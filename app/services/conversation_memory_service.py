"""
会话记忆服务

负责协调短期记忆和长期记忆：
- 短期记忆从 Redis 读取最近消息窗口，供问题改写和提示词使用
- 长期记忆把每轮问数信息 Embedding 后写入 Qdrant，并在新问题到来时做语义检索
- 每轮结束后同时更新 Redis 消息窗口和 Qdrant 长期记忆

任何记忆读写失败都不应该阻断主问数流程，因此这里统一做降级处理并记录告警
"""

import asyncio
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.conf.app_config import app_config
from app.core.log import logger
from app.entities.chat_message import ChatMessage
from app.entities.conversation_memory import ConversationMemory
from app.prompt.prompt_loader import load_prompt
from app.repositories.qdrant.conversation_memory_qdrant_repository import (
    ConversationMemoryQdrantRepository,
)
from app.repositories.redis.session_redis_repository import SessionRedisRepository


@dataclass
class LoadedConversationContext:
    """一次问数开始前加载到的历史上下文"""

    history: list[ChatMessage]
    memories: list[ConversationMemory]
    resolved_query: str


class ConversationMemoryService:
    """短期会话记忆和长期向量记忆的统一编排服务"""

    def __init__(
        self,
        session_repository: SessionRedisRepository,
        memory_repository: ConversationMemoryQdrantRepository,
        embedding_client: HuggingFaceEndpointEmbeddings,
        llm: BaseChatModel,
    ):
        self.session_repository = session_repository
        self.memory_repository = memory_repository
        self.embedding_client = embedding_client
        self.llm = llm
        self.config = app_config.memory

    # ------------------------------------------------------------------
    # 读取上下文
    # ------------------------------------------------------------------
    async def load_context(
        self, user_id: str, session_id: str, query: str
    ) -> LoadedConversationContext:
        """加载短期消息和长期记忆，并把追问改写成独立问题"""
        history = await self._load_history(session_id)
        memories = await self._retrieve_memories(user_id=user_id, query=query)
        resolved_query = await self._rewrite_query(
            query=query, history=history, memories=memories
        )

        # 追问被改写成独立问题后，再用改写结果检索一次长期记忆，提升语义命中率
        if resolved_query.strip() != query.strip():
            resolved_memories = await self._retrieve_memories(
                user_id=user_id, query=resolved_query
            )
            memories = self._dedupe_memories(memories + resolved_memories)
            # 两路检索合并后按相似度保留 top_k，避免提示词无限膨胀
            memories.sort(key=lambda memory: memory.score or 0, reverse=True)
            memories = memories[: self.config.long_term_top_k]

        return LoadedConversationContext(
            history=history,
            memories=memories,
            resolved_query=resolved_query,
        )

    async def _load_history(self, session_id: str) -> list[ChatMessage]:
        if not session_id:
            return []
        try:
            return await self.session_repository.get_messages(session_id)
        except Exception as e:
            logger.warning(f"读取短期会话记忆失败，将按无历史会话处理：{e}")
            return []

    async def _retrieve_memories(
        self, user_id: str, query: str
    ) -> list[ConversationMemory]:
        if not self.config.long_term_enabled or not query.strip():
            return []

        try:
            embedding = await self.embedding_client.aembed_query(query)
            memories = await self.memory_repository.search(
                embedding=embedding,
                user_id=user_id,
                limit=self.config.long_term_top_k,
                score_threshold=self.config.long_term_score_threshold,
            )
        except Exception as e:
            logger.warning(f"长期记忆语义检索失败，将跳过长期记忆注入：{e}")
            return []

        return self._dedupe_memories(memories)

    @staticmethod
    def _dedupe_memories(
        memories: list[ConversationMemory],
    ) -> list[ConversationMemory]:
        """同一个事实可能被多轮对话重复抽取，注入前按文本去重"""
        unique_memories: list[ConversationMemory] = []
        seen_contents: set[str] = set()
        for memory in memories:
            content = memory.content.strip()
            if not content or content in seen_contents:
                continue
            seen_contents.add(content)
            unique_memories.append(memory)
        return unique_memories

    async def _rewrite_query(
        self,
        query: str,
        history: list[ChatMessage],
        memories: list[ConversationMemory],
    ) -> str:
        """存在历史会话时，把“那上个月呢”这类追问改写为独立问题"""
        if not history:
            return query

        prompt = PromptTemplate(
            template=load_prompt("rewrite_query"),
            input_variables=["history", "memory", "query"],
        )
        chain = prompt | self.llm | StrOutputParser()
        try:
            result = await chain.ainvoke(
                {
                    "history": self.format_history(history),
                    "memory": self.format_memories(memories),
                    "query": query,
                }
            )
        except Exception as e:
            logger.warning(f"多轮问题改写失败，将使用原始问题：{e}")
            return query

        resolved_query = (result or "").strip()
        # 模型偶尔会带出“改写后的问题：”前缀或反引号，这里做一次轻量清洗
        for prefix in ("改写后的问题：", "改写后问题：", "独立问题：", "改写后："):
            if resolved_query.startswith(prefix):
                resolved_query = resolved_query[len(prefix) :].strip()
        resolved_query = resolved_query.strip("`").strip()

        # 改写结果异常时回退到原始问题，避免把错误内容带进后续召回
        if not resolved_query or len(resolved_query) > 500:
            return query
        return resolved_query

    # ------------------------------------------------------------------
    # 写入本轮记忆
    # ------------------------------------------------------------------
    async def save_turn(
        self,
        user_id: str,
        session_id: str,
        query: str,
        resolved_query: str,
        sql: str,
        sql_result: list[dict] | None,
        history: list[dict] | None = None,
    ) -> None:
        """保存一轮问答到 Redis 短期记忆，并把可复用信息写入 Qdrant 长期记忆"""
        if not session_id:
            logger.warning("缺少 session_id，跳过本轮会话记忆保存")
            return

        created_at = self._now_iso()
        row_count = len(sql_result) if isinstance(sql_result, list) else 0

        assistant_content = f"已生成并执行 SQL，返回 {row_count} 行。"
        if sql:
            assistant_content += f"\nSQL：{self._truncate(sql, 1500)}"

        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            role="user",
            content=query,
            created_at=created_at,
            resolved_query=resolved_query,
        )
        assistant_message = ChatMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content=assistant_content,
            created_at=created_at,
            sql=sql,
            resolved_query=resolved_query,
            metadata={"row_count": row_count},
        )

        try:
            await self.session_repository.append_turn(
                session_id=session_id,
                user_id=user_id,
                user_message=user_message,
                assistant_message=assistant_message,
            )
        except Exception as e:
            logger.warning(f"写入短期会话记忆失败：{e}")

        if not self.config.long_term_enabled or not sql:
            return

        try:
            await self._save_long_term(
                user_id=user_id,
                session_id=session_id,
                query=query,
                resolved_query=resolved_query,
                sql=sql,
                history=history or [],
                created_at=created_at,
            )
        except Exception as e:
            # 长期记忆属于增强能力，写入失败只记录日志，不影响已经返回的问数结果
            logger.warning(f"写入长期向量记忆失败：{e}")

    async def _save_long_term(
        self,
        user_id: str,
        session_id: str,
        query: str,
        resolved_query: str,
        sql: str,
        history: list[dict],
        created_at: str,
    ) -> None:
        """把本轮问数记录和抽取出的稳定偏好写入 Qdrant"""
        episode_content = self._truncate(
            "历史问数记录\n"
            f"用户问题：{query}\n"
            f"独立问题：{resolved_query}\n"
            f"生成 SQL：{sql}",
            self.config.max_memory_chars * 4,
        )

        # Embedding 和 LLM 记忆抽取互不依赖，可以并发执行，降低记忆保存耗时
        episode_embedding, extracted = await asyncio.gather(
            self.embedding_client.aembed_query(episode_content),
            self._extract_memories(
                query=query,
                resolved_query=resolved_query,
                sql=sql,
                history=history,
            ),
        )

        episode_memory = ConversationMemory(
            id=self._memory_id("episodic", user_id, session_id, query, sql),
            user_id=user_id,
            session_id=session_id,
            memory_type="episodic",
            content=episode_content,
            question=query,
            resolved_query=resolved_query,
            sql=sql,
            created_at=created_at,
        )
        await self.memory_repository.upsert(
            memories=[episode_memory], embeddings=[episode_embedding]
        )

        facts = self._normalize_facts(extracted.get("facts", []))
        if not facts:
            return

        fact_embeddings = await self.embedding_client.aembed_documents(facts)
        fact_memories = [
            ConversationMemory(
                id=self._memory_id("semantic", user_id, fact),
                user_id=user_id,
                session_id=session_id,
                memory_type="semantic",
                content=fact,
                question=query,
                resolved_query=resolved_query,
                created_at=created_at,
            )
            for fact in facts
        ]
        await self.memory_repository.upsert(
            memories=fact_memories, embeddings=fact_embeddings
        )
        logger.info(f"写入长期记忆：episodic=1, semantic={len(fact_memories)}")

    async def _extract_memories(
        self,
        query: str,
        resolved_query: str,
        sql: str,
        history: list[dict],
    ) -> dict:
        """调用 LLM 从本轮问数中抽取稳定偏好和业务口径"""
        if not self.config.extraction_enabled:
            return {}

        prompt = PromptTemplate(
            template=load_prompt("extract_memory"),
            input_variables=["history", "query", "resolved_query", "sql"],
        )
        chain = prompt | self.llm | JsonOutputParser()
        try:
            result = await chain.ainvoke(
                {
                    "history": self._format_history_dicts(history),
                    "query": query,
                    "resolved_query": resolved_query,
                    "sql": self._truncate(sql, 2000),
                }
            )
        except Exception as e:
            logger.warning(f"长期记忆抽取失败，将只保存问数记录：{e}")
            return {}

        if not isinstance(result, dict):
            return {}

        summary = self._truncate(str(result.get("summary") or "").strip(), 100)
        facts = result.get("facts") or []
        if not isinstance(facts, list):
            facts = []
        return {"summary": summary, "facts": facts}

    # ------------------------------------------------------------------
    # 提示词格式化
    # ------------------------------------------------------------------
    def format_history(self, history: list[ChatMessage]) -> str:
        """把最近消息格式化成提示词中的对话片段"""
        limit = self.config.history_prompt_messages
        selected = history[-limit:] if limit > 0 else history
        lines: list[str] = []
        for message in selected:
            role = "用户" if message.role == "user" else "助手"
            content = self._truncate(message.content.strip(), 500)
            if content:
                lines.append(f"{role}：{content}")
        return "\n".join(lines) if lines else "无"

    def _format_history_dicts(self, history: list[dict]) -> str:
        """把状态中的历史消息字典格式化成提示词片段"""
        limit = self.config.history_prompt_messages
        selected = history[-limit:] if limit > 0 else history
        lines: list[str] = []
        for message in selected:
            role = "用户" if message.get("role") == "user" else "助手"
            content = self._truncate(str(message.get("content") or "").strip(), 500)
            if content:
                lines.append(f"{role}：{content}")
        return "\n".join(lines) if lines else "无"

    def format_memories(self, memories: list[ConversationMemory]) -> str:
        """把长期记忆格式化成提示词中的参考片段"""
        type_labels = {
            "episodic": "历史问数",
            "semantic": "长期偏好",
        }
        lines: list[str] = []
        for memory in memories:
            content = self._truncate(
                memory.content.strip(), self.config.max_memory_chars
            )
            if not content:
                continue
            label = type_labels.get(memory.memory_type, "长期记忆")
            lines.append(f"- [{label}] {content}")
        return "\n".join(lines) if lines else "无"

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _truncate(text: str, max_chars: int) -> str:
        text = text or ""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."

    @staticmethod
    def _memory_id(*parts: str) -> str:
        """用稳定内容生成 UUID，重复保存同一记忆时会覆盖而不是新增向量点"""
        raw = json.dumps(parts, ensure_ascii=False, sort_keys=True)
        return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))

    def _normalize_facts(self, facts) -> list[str]:
        """清洗 LLM 返回的 facts，限制条数和长度并去重"""
        if not isinstance(facts, list):
            return []

        normalized: list[str] = []
        for fact in facts:
            if not isinstance(fact, str):
                continue
            fact = fact.strip()
            if not fact or fact in normalized:
                continue
            normalized.append(self._truncate(fact, self.config.max_memory_chars))
            if len(normalized) >= 3:
                break
        return normalized
