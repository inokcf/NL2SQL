"""
短期会话记忆 Redis 仓储

负责会话元信息 消息列表和用户会话索引的读写
消息使用 Redis List 保存，并通过 LTRIM 只保留最近 N 条；元信息和消息列表
都会在每次追加时刷新 TTL，从而实现“最近 N 条 + 自动过期”的短期记忆
"""

import asyncio
import json
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from redis.asyncio import Redis

from app.conf.app_config import RedisConfig
from app.entities.chat_message import ChatMessage
from app.entities.session_info import SessionInfo


class SessionRedisRepository:
    """负责会话元信息 消息窗口和用户会话索引的 Redis 读写"""

    def __init__(self, client: Redis, redis_config: RedisConfig):
        self.client = client
        self.config = redis_config

    # ------------------------------------------------------------------
    # key 约定
    # ------------------------------------------------------------------
    def _meta_key(self, session_id: str) -> str:
        return f"{self.config.key_prefix}:session:{session_id}:meta"

    def _messages_key(self, session_id: str) -> str:
        return f"{self.config.key_prefix}:session:{session_id}:messages"

    def _user_sessions_key(self, user_id: str) -> str:
        return f"{self.config.key_prefix}:user:{user_id}:sessions"

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _make_title(text: str, limit: int = 30) -> str:
        """用首轮问题生成会话标题，过长时截断"""
        title = " ".join((text or "").split())
        return title[:limit] if title else "新会话"

    # ------------------------------------------------------------------
    # 会话生命周期
    # ------------------------------------------------------------------
    async def create_session(
        self,
        user_id: str,
        title: str = "新会话",
        session_id: str | None = None,
    ) -> SessionInfo:
        """创建会话元信息，并把会话 id 写入用户会话索引"""
        session_id = session_id or str(uuid.uuid4())
        now = self._now_iso()
        title = self._make_title(title)

        pipe = self.client.pipeline()
        pipe.hset(
            self._meta_key(session_id),
            mapping={
                "session_id": session_id,
                "user_id": user_id,
                "title": title,
                "created_at": now,
                "updated_at": now,
            },
        )
        pipe.expire(self._meta_key(session_id), self.config.session_ttl_seconds)
        # 使用时间戳作为 score，会话列表可以按最近活跃时间倒序展示
        pipe.zadd(self._user_sessions_key(user_id), {session_id: time.time()})
        pipe.expire(self._user_sessions_key(user_id), self.config.session_ttl_seconds)
        await pipe.execute()

        return SessionInfo(
            session_id=session_id,
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=now,
            message_count=0,
        )

    async def get_session(self, session_id: str) -> SessionInfo | None:
        """读取会话元信息，并补充当前保留的消息条数"""
        # 元信息和消息长度放在同一个 pipeline 中读取，减少一次网络往返
        pipe = self.client.pipeline()
        pipe.hgetall(self._meta_key(session_id))
        pipe.llen(self._messages_key(session_id))
        meta, message_count = await pipe.execute()
        if not meta:
            return None

        return SessionInfo(
            session_id=meta.get("session_id", session_id),
            user_id=meta.get("user_id", "default"),
            title=meta.get("title", "新会话"),
            created_at=meta.get("created_at", ""),
            updated_at=meta.get("updated_at", ""),
            message_count=message_count,
        )

    async def list_sessions(self, user_id: str, limit: int = 50) -> list[SessionInfo]:
        """按最近活跃时间倒序返回用户的会话列表"""
        sessions_key = self._user_sessions_key(user_id)
        session_ids = await self.client.zrevrange(sessions_key, 0, limit - 1)

        # 会话较多时逐个读取会产生串行往返，这里并发读取并保留 zset 的排序结果
        results = await asyncio.gather(
            *(self.get_session(session_id) for session_id in session_ids)
        )
        sessions: list[SessionInfo] = []
        stale_session_ids: list[str] = []
        for session_id, session in zip(session_ids, results):
            if session is None:
                # 会话已经过期但索引还在时，顺手清理掉，避免列表出现空壳会话
                stale_session_ids.append(session_id)
                continue
            sessions.append(session)

        if stale_session_ids:
            await self.client.zrem(sessions_key, *stale_session_ids)
        return sessions

    async def delete_session(self, session_id: str, user_id: str | None = None) -> bool:
        """删除会话元信息 消息窗口和用户会话索引"""
        session = await self.get_session(session_id)
        if session is None:
            return False

        owner = user_id or session.user_id
        pipe = self.client.pipeline()
        pipe.delete(self._meta_key(session_id))
        pipe.delete(self._messages_key(session_id))
        pipe.zrem(self._user_sessions_key(owner), session_id)
        await pipe.execute()
        return True

    # ------------------------------------------------------------------
    # 消息窗口
    # ------------------------------------------------------------------
    async def append_turn(
        self,
        session_id: str,
        user_id: str,
        user_message: ChatMessage,
        assistant_message: ChatMessage,
    ) -> None:
        """追加一轮问答，并裁剪到最近 N 条消息"""
        meta_key = self._meta_key(session_id)
        messages_key = self._messages_key(session_id)

        # Redis 过期后同一 session_id 可能被再次使用，这里自动补建元信息
        if not await self.client.exists(meta_key):
            await self.create_session(
                user_id=user_id,
                title=user_message.content,
                session_id=session_id,
            )

        # 由 API 创建的空会话标题通常是“新会话”，首轮问数后替换成真实问题
        current_title = await self.client.hget(meta_key, "title")
        now = self._now_iso()

        pipe = self.client.pipeline()
        pipe.rpush(
            messages_key,
            json.dumps(asdict(user_message), ensure_ascii=False),
            json.dumps(asdict(assistant_message), ensure_ascii=False),
        )
        # 负索引表示从末尾计数，只保留最近 max_messages 条
        pipe.ltrim(messages_key, -self.config.max_messages, -1)
        pipe.expire(messages_key, self.config.session_ttl_seconds)
        pipe.hset(meta_key, mapping={"updated_at": now})
        pipe.expire(meta_key, self.config.session_ttl_seconds)
        if not current_title or current_title == "新会话":
            pipe.hset(meta_key, "title", self._make_title(user_message.content))
        pipe.zadd(self._user_sessions_key(user_id), {session_id: time.time()})
        pipe.expire(self._user_sessions_key(user_id), self.config.session_ttl_seconds)
        await pipe.execute()

    async def get_messages(self, session_id: str) -> list[ChatMessage]:
        """按时间顺序读取当前会话保留的最近消息"""
        raw_messages = await self.client.lrange(self._messages_key(session_id), 0, -1)
        messages: list[ChatMessage] = []
        for raw_message in raw_messages:
            try:
                payload = json.loads(raw_message)
                messages.append(ChatMessage(**payload))
            except json.JSONDecodeError, TypeError:
                # 单条脏数据不应影响整段会话加载，跳过并继续读取
                continue
        return messages
