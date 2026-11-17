"""
问数查询服务

负责把 API 层传入的自然语言问题转换成一次 LangGraph 工作流执行：
创建初始 State、组装 Runtime Context、消费 graph.astream 的流式输出，
并统一包装成 SSE 文本返回给路由层。
"""

import json
import uuid

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.session_info import SessionInfo
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.conversation_memory_service import ConversationMemoryService
from app.services.session_service import SessionService


class QueryService:
    """封装一次问数查询所需的业务编排逻辑"""

    def __init__(
        self,
        meta_mysql_repository: MetaMySQLRepository,
        embedding_client: HuggingFaceEndpointEmbeddings,
        dw_mysql_repository: DWMySQLRepository,
        column_qdrant_repository: ColumnQdrantRepository,
        metric_qdrant_repository: MetricQdrantRepository,
        value_es_repository: ValueESRepository,
        session_service: SessionService,
        conversation_memory_service: ConversationMemoryService,
    ):
        # MySQL 仓储分别负责元数据补全和真实数仓环境信息读取
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository

        # 召回链路依赖的向量检索、Embedding 和全文检索能力由依赖层注入
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.value_es_repository = value_es_repository

        # 会话管理负责保证 session_id 存在，记忆服务负责图执行前后的记忆读写
        self.session_service = session_service
        self.conversation_memory_service = conversation_memory_service

    async def _ensure_session(
        self, user_id: str, session_id: str | None, query: str
    ) -> SessionInfo:
        """确保本次请求有可用的会话；Redis 不可用时也返回值用于单轮降级"""
        try:
            return await self.session_service.ensure_session(
                user_id=user_id,
                session_id=session_id,
                title=query,
            )
        except Exception as e:
            logger.warning(f"会话初始化失败，将按无状态单轮问数继续：{e}")
            return SessionInfo(
                session_id=session_id or str(uuid.uuid4()),
                user_id=user_id,
                title=(query or "新会话")[:30],
                created_at="",
                updated_at="",
            )

    async def query(
        self,
        query: str,
        user_id: str,
        session_id: str | None = None,
    ):
        """执行一次问数工作流，并逐段产出 SSE 消息"""

        # 先确定会话，前端没有传 session_id 时由后端创建并在首条事件中返回
        session = await self._ensure_session(
            user_id=user_id, session_id=session_id, query=query
        )

        # session 事件让前端记住会话 id，后续追问会自动携带，实现多轮上下文
        session_event = {
            "type": "session",
            "session_id": session.session_id,
            "user_id": session.user_id,
        }
        yield f"data: {json.dumps(session_event, ensure_ascii=False)}\n\n"

        # State 只放会被图节点读写和合并的业务数据，外部工具对象不塞进 State
        state = DataAgentState(
            query=query,
            session_id=session.session_id,
            user_id=session.user_id,
        )
        # Context 保存本次图执行需要复用的外部依赖，节点通过 runtime.context 读取
        context = DataAgentContext(
            conversation_memory_service=self.conversation_memory_service,
            column_qdrant_repository=self.column_qdrant_repository,
            embedding_client=self.embedding_client,
            metric_qdrant_repository=self.metric_qdrant_repository,
            value_es_repository=self.value_es_repository,
            meta_mysql_repository=self.meta_mysql_repository,
            dw_mysql_repository=self.dw_mysql_repository,
        )
        try:
            # stream_mode="custom" 对应节点内部 writer(...) 写出的进度消息
            async for chunk in graph.astream(
                input=state, context=context, stream_mode="custom"
            ):
                # SSE 要求每条消息以 data: 开头，并以两个换行符结束
                # ensure_ascii=False 保留中文进度文案，default=str 兜底处理日期等非 JSON 类型
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:
            # 流式接口已经开始返回后不能再改 HTTP 状态码，因此把异常也包装成一条 SSE 消息
            error = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error, ensure_ascii=False, default=str)}\n\n"
