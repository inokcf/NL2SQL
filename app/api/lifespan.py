"""
FastAPI 应用生命周期管理

负责在服务启动时初始化外部客户端，在服务关闭时释放连接资源。
这些客户端是应用级资源，适合在 lifespan 中创建一次并复用，而不是每个请求
重复初始化。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import (
    dw_mysql_client_manager,
    meta_mysql_client_manager,
)
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.clients.redis_client_manager import redis_client_manager
from app.core.log import logger
from app.repositories.mysql.meta.user_mysql_repository import UserMySQLRepository
from app.repositories.qdrant.conversation_memory_qdrant_repository import (
    ConversationMemoryQdrantRepository,
)
from app.services.auth_service import AuthService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理应用启动和关闭两个阶段的外部资源"""

    # 启动阶段：先建立各类外部服务客户端，后续依赖函数会从 manager 中取已初始化对象
    qdrant_client_manager.init()
    embedding_client_manager.init()
    es_client_manager.init()
    meta_mysql_client_manager.init()
    dw_mysql_client_manager.init()
    redis_client_manager.init()

    # 提前探测 Redis 和创建长期记忆集合；失败只告警，不阻止应用启动
    try:
        await redis_client_manager.client.ping()
    except Exception as e:
        logger.warning(f"Redis 暂不可用，会话记忆将降级：{e}")

    try:
        memory_repository = ConversationMemoryQdrantRepository(
            qdrant_client_manager.client
        )
        await memory_repository.ensure_collection()
    except Exception as e:
        logger.warning(f"长期记忆集合初始化失败，首次使用时将重试：{e}")

    # 为已有数据库补建用户表，并在空库中创建体验账号
    try:
        async with meta_mysql_client_manager.session_factory() as meta_session:
            auth_service = AuthService(UserMySQLRepository(meta_session))
            await auth_service.ensure_default_user()
    except Exception as e:
        logger.warning(f"用户表初始化失败，登录功能可能不可用：{e}")

    # yield 之前是启动逻辑，yield 之后是关闭逻辑；中间阶段由 FastAPI 正常处理请求
    yield

    # 关闭阶段：按应用级资源统一释放连接，避免进程退出前留下未关闭的网络连接
    await qdrant_client_manager.close()
    await es_client_manager.close()
    await meta_mysql_client_manager.close()
    await dw_mysql_client_manager.close()
    await redis_client_manager.close()
