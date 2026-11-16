"""
长期会话记忆 Qdrant 仓储

长期记忆和字段 指标向量分开存放在独立集合中
仓储只负责集合初始化 向量写入 按用户语义检索以及按会话删除
记忆如何生成 何时写入由上层 ConversationMemoryService 决定
"""

from dataclasses import asdict

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from app.conf.app_config import app_config
from app.entities.conversation_memory import ConversationMemory


class ConversationMemoryQdrantRepository:
    """负责长期会话记忆向量集合的读写"""

    collection_name = "conversation_memory_collection"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client
        # 同一仓储实例在一次请求内可能多次写入，初始化一次集合即可
        self._ensured = False

    async def ensure_collection(self):
        """确保记忆集合和常用过滤字段索引存在"""
        if self._ensured:
            return

        if not await self.client.collection_exists(self.collection_name):
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=app_config.qdrant.embedding_size,
                    distance=Distance.COSINE,
                ),
            )

        # 读取集合信息后按需补建索引，既能避免重复创建，也能修复历史集合缺少索引的情况
        collection_info = await self.client.get_collection(self.collection_name)
        payload_schema = collection_info.payload_schema or {}
        if "user_id" not in payload_schema:
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="user_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
        if "session_id" not in payload_schema:
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="session_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
        self._ensured = True

    async def upsert(
        self,
        memories: list[ConversationMemory],
        embeddings: list[list[float]],
        batch_size: int = 10,
    ):
        """批量写入长期记忆向量点"""
        if not memories:
            return

        await self.ensure_collection()
        points: list[PointStruct] = []
        for memory, embedding in zip(memories, embeddings):
            payload = asdict(memory)
            # score 只在检索结果中出现，不属于持久化字段
            payload.pop("score", None)
            points.append(PointStruct(id=memory.id, vector=embedding, payload=payload))

        for i in range(0, len(points), batch_size):
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points[i : i + batch_size],
            )

    async def search(
        self,
        embedding: list[float],
        user_id: str,
        limit: int = 5,
        score_threshold: float = 0.55,
    ) -> list[ConversationMemory]:
        """按用户维度做语义检索，避免把其他用户的历史记忆注入当前会话"""
        await self.ensure_collection()

        filters = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id),
                )
            ]
        )
        result = await self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            query_filter=filters,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )
        return [
            ConversationMemory(**point.payload, score=point.score)
            for point in result.points
        ]

    async def scroll_by_session(
        self, session_id: str, limit: int = 100
    ) -> list[ConversationMemory]:
        """按会话读取长期记忆，主要用于会话详情和调试查看"""
        await self.ensure_collection()

        points, _ = await self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id),
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return [ConversationMemory(**point.payload) for point in points]

    async def delete_by_session(self, session_id: str):
        """删除某个会话产生的全部长期记忆，用于会话清理和隐私删除"""
        await self.ensure_collection()
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="session_id",
                            match=MatchValue(value=session_id),
                        )
                    ]
                )
            ),
        )
