"""
FastAPI 依赖组装

集中声明 API 层需要的依赖函数，把 Session、Repository、Client 和 Service
按职责组装起来。路由层只通过 Depends 声明自己需要什么对象，具体创建细节
都收敛在这里，避免 HTTP 处理函数直接感知底层基础设施。
"""

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm import llm
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import (
    dw_mysql_client_manager,
    meta_mysql_client_manager,
)
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.clients.redis_client_manager import redis_client_manager
from app.conf.app_config import app_config
from app.core.security import decode_access_token
from app.entities.user_info import UserInfo
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.mysql.meta.user_mysql_repository import UserMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.conversation_memory_qdrant_repository import (
    ConversationMemoryQdrantRepository,
)
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.repositories.redis.session_redis_repository import SessionRedisRepository
from app.services.auth_service import AuthService
from app.services.conversation_memory_service import ConversationMemoryService
from app.services.query_service import QueryService
from app.services.session_service import SessionService

# auto_error=False 让缺少 Authorization 头时由依赖函数统一返回 401
bearer_scheme = HTTPBearer(auto_error=False)


async def get_meta_session():
    """创建一次请求内使用的元数据库 Session"""

    # yield 之后的清理逻辑由 async with 负责，FastAPI 会在请求结束后继续执行退出流程
    async with meta_mysql_client_manager.session_factory() as meta_session:
        yield meta_session


async def get_meta_mysql_repository(
    session: Annotated[AsyncSession, Depends(get_meta_session)],
) -> MetaMySQLRepository:
    """基于请求级 Session 创建元数据仓储"""

    return MetaMySQLRepository(session)


async def get_embedding_client() -> HuggingFaceEndpointEmbeddings:
    """获取应用启动阶段初始化好的 Embedding 客户端"""

    return embedding_client_manager.client


async def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_meta_session)],
) -> UserMySQLRepository:
    """创建用户信息仓储"""
    return UserMySQLRepository(session)


async def get_auth_service(
    user_repository: Annotated[UserMySQLRepository, Depends(get_user_repository)],
) -> AuthService:
    """组装注册登录服务"""
    return AuthService(user_repository)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    user_repository: Annotated[UserMySQLRepository, Depends(get_user_repository)],
) -> UserInfo:
    """解析 Bearer Token 并加载当前登录用户"""

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub") if payload else None
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(
            status_code=401,
            detail="登录凭证无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="用户不存在或已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_dw_session():
    """创建一次请求内使用的数仓 Session"""

    async with dw_mysql_client_manager.session_factory() as dw_session:
        yield dw_session


async def get_dw_mysql_repository(
    session: Annotated[AsyncSession, Depends(get_dw_session)],
) -> DWMySQLRepository:
    """基于请求级 Session 创建数仓仓储"""

    return DWMySQLRepository(session)


async def get_column_qdrant_repository() -> ColumnQdrantRepository:
    """创建字段向量检索仓储"""

    return ColumnQdrantRepository(qdrant_client_manager.client)


async def get_metric_qdrant_repository() -> MetricQdrantRepository:
    """创建指标向量检索仓储"""

    return MetricQdrantRepository(qdrant_client_manager.client)


async def get_value_es_repository() -> ValueESRepository:
    """创建字段取值全文检索仓储"""

    return ValueESRepository(es_client_manager.client)


async def get_session_redis_repository() -> SessionRedisRepository:
    """创建短期会话记忆 Redis 仓储"""

    return SessionRedisRepository(redis_client_manager.client, app_config.redis)


async def get_conversation_memory_repository() -> ConversationMemoryQdrantRepository:
    """创建长期会话记忆 Qdrant 仓储"""

    return ConversationMemoryQdrantRepository(qdrant_client_manager.client)


async def get_session_service(
    session_repository: Annotated[
        SessionRedisRepository, Depends(get_session_redis_repository)
    ],
    memory_repository: Annotated[
        ConversationMemoryQdrantRepository,
        Depends(get_conversation_memory_repository),
    ],
) -> SessionService:
    """组装会话管理服务"""

    return SessionService(
        session_repository=session_repository,
        memory_repository=memory_repository,
    )


async def get_conversation_memory_service(
    session_repository: Annotated[
        SessionRedisRepository, Depends(get_session_redis_repository)
    ],
    memory_repository: Annotated[
        ConversationMemoryQdrantRepository,
        Depends(get_conversation_memory_repository),
    ],
    embedding_client: Annotated[
        HuggingFaceEndpointEmbeddings, Depends(get_embedding_client)
    ],
) -> ConversationMemoryService:
    """组装短期会话与长期向量记忆服务"""

    return ConversationMemoryService(
        session_repository=session_repository,
        memory_repository=memory_repository,
        embedding_client=embedding_client,
        llm=llm,
    )


async def get_query_service(
    meta_mysql_repository: Annotated[
        MetaMySQLRepository, Depends(get_meta_mysql_repository)
    ],
    embedding_client: Annotated[
        HuggingFaceEndpointEmbeddings, Depends(get_embedding_client)
    ],
    dw_mysql_repository: Annotated[DWMySQLRepository, Depends(get_dw_mysql_repository)],
    column_qdrant_repository: Annotated[
        ColumnQdrantRepository, Depends(get_column_qdrant_repository)
    ],
    metric_qdrant_repository: Annotated[
        MetricQdrantRepository, Depends(get_metric_qdrant_repository)
    ],
    value_es_repository: Annotated[ValueESRepository, Depends(get_value_es_repository)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    conversation_memory_service: Annotated[
        ConversationMemoryService, Depends(get_conversation_memory_service)
    ],
) -> QueryService:
    """组装一次查询所需的业务服务"""

    # QueryService 只接收已经创建好的依赖对象，本身不关心这些对象来自 MySQL、Qdrant 还是 ES
    return QueryService(
        meta_mysql_repository=meta_mysql_repository,
        embedding_client=embedding_client,
        dw_mysql_repository=dw_mysql_repository,
        column_qdrant_repository=column_qdrant_repository,
        metric_qdrant_repository=metric_qdrant_repository,
        value_es_repository=value_es_repository,
        session_service=session_service,
        conversation_memory_service=conversation_memory_service,
    )
