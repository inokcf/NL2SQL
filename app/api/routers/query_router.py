"""
问数查询接口路由

负责定义前端访问的 `/api/query` 接口，把 HTTP 请求交给 QueryService，
并把问数智能体执行过程以 SSE 形式持续返回给客户端。
路由层只处理请求体、依赖声明和响应类型，不直接创建 Repository 或执行图节点。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import StreamingResponse

from app.api.dependencies import (
    get_current_user,
    get_query_service,
    get_session_service,
)
from app.api.schemas.query_schema import QuerySchema
from app.entities.user_info import UserInfo
from app.services.query_service import QueryService
from app.services.session_service import SessionService

# 当前模块只维护查询相关接口，避免后续所有 API 都挤在 main.py 中
query_router = APIRouter()


@query_router.post("/api/query")
async def query_handler(
    # 请求体参数：FastAPI 会把前端 JSON 自动解析成 QuerySchema
    query: QuerySchema,
    # 当前登录用户，服务端据此隔离会话和长期记忆
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    # 服务依赖：FastAPI 会调用 get_query_service，递归组装它所需的仓储和客户端
    query_service: Annotated[QueryService, Depends(get_query_service)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
):
    """接收用户自然语言问题，并流式返回 LangGraph 工作流输出"""

    # 在建立 SSE 连接前校验会话归属，避免 SSE 开始后才暴露权限错误
    if query.session_id:
        session = await session_service.get_session_for_user(
            query.session_id, current_user.id
        )
        if session is None:
            raise HTTPException(status_code=404, detail="会话不存在或已过期")

    return StreamingResponse(
        # 用户身份只来自 Token，不接受客户端传入的 user_id
        query_service.query(
            query=query.query,
            user_id=current_user.id,
            session_id=query.session_id,
        ),
        media_type="text/event-stream",
    )
