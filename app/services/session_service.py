"""
会话管理服务

在 Redis 会话仓储和长期记忆仓储之上提供会话创建 查询 列表和删除能力
API 层只依赖这层服务，不直接感知 Redis key 结构或 Qdrant 过滤条件
"""

from app.core.log import logger
from app.entities.chat_message import ChatMessage
from app.entities.conversation_memory import ConversationMemory
from app.entities.session_info import SessionInfo
from app.repositories.qdrant.conversation_memory_qdrant_repository import (
    ConversationMemoryQdrantRepository,
)
from app.repositories.redis.session_redis_repository import SessionRedisRepository


class SessionService:
    """封装多轮会话的生命周期管理逻辑"""

    def __init__(
        self,
        session_repository: SessionRedisRepository,
        memory_repository: ConversationMemoryQdrantRepository,
    ):
        self.session_repository = session_repository
        self.memory_repository = memory_repository

    async def create_session(self, user_id: str, title: str = "新会话") -> SessionInfo:
        """显式创建一个空会话"""
        return await self.session_repository.create_session(
            user_id=user_id, title=title
        )

    async def ensure_session(
        self,
        user_id: str,
        session_id: str | None = None,
        title: str = "新会话",
    ) -> SessionInfo:
        """存在且属于当前用户则复用，否则创建一个新会话"""
        if session_id:
            session = await self.session_repository.get_session(session_id)
            if session is not None:
                if session.user_id == user_id:
                    return session
                # 不允许复用其他用户的 session_id，直接降级为全新会话
                logger.warning(f"会话 {session_id} 不属于用户 {user_id}，将创建新会话")
                session_id = None

        return await self.session_repository.create_session(
            user_id=user_id,
            title=title,
            session_id=session_id,
        )

    async def list_sessions(self, user_id: str, limit: int = 50) -> list[SessionInfo]:
        """返回用户最近的会话列表"""
        return await self.session_repository.list_sessions(user_id=user_id, limit=limit)

    async def get_session_for_user(
        self, session_id: str, user_id: str
    ) -> SessionInfo | None:
        """读取会话元信息，并校验会话归属"""
        try:
            session = await self.session_repository.get_session(session_id)
        except Exception as e:
            # Redis 不可用时无法确认会话归属，按不存在处理，避免越权访问
            logger.warning(f"读取会话归属失败：{e}")
            return None

        if session is None or session.user_id != user_id:
            return None
        return session

    async def get_session_detail(
        self, session_id: str, user_id: str
    ) -> tuple[SessionInfo, list[ChatMessage]] | None:
        """读取属于当前用户的会话元信息和短期消息窗口"""
        session = await self.get_session_for_user(session_id, user_id)
        if session is None:
            return None

        messages = await self.session_repository.get_messages(session_id)
        return session, messages

    async def list_memories(
        self, session_id: str, user_id: str, limit: int = 100
    ) -> list[ConversationMemory] | None:
        """读取某个会话写入的长期记忆，并校验会话归属"""
        session = await self.get_session_for_user(session_id, user_id)
        if session is None:
            return None

        try:
            return await self.memory_repository.scroll_by_session(
                session_id=session_id, limit=limit
            )
        except Exception as e:
            logger.warning(f"读取会话长期记忆失败：{e}")
            return []

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """删除属于当前用户的会话及其长期记忆"""
        session = await self.get_session_for_user(session_id, user_id)
        if session is None:
            return False

        # 先删除长期记忆，再清理 Redis，避免留下无法通过会话定位的孤立记忆
        try:
            await self.memory_repository.delete_by_session(session_id)
        except Exception as e:
            # 向量库暂时不可用时仍然允许删除短期会话，长期记忆留待后续人工清理
            logger.warning(f"删除会话长期记忆失败：{e}")

        return await self.session_repository.delete_session(
            session_id=session_id, user_id=session.user_id
        )
