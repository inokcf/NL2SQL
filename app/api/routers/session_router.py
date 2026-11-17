"""
会话管理接口路由

提供会话创建 列表 详情 删除和长期记忆查看接口
路由层只负责 HTTP 参数与响应结构，具体 Redis 和 Qdrant 操作由 SessionService 完成
"""

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user, get_session_service
from app.api.schemas.session_schema import (
    ChatMessageSchema,
    MemorySchema,
    SessionCreateSchema,
    SessionDetailSchema,
    SessionSchema,
)
from app.entities.user_info import UserInfo
from app.services.session_service import SessionService

session_router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@session_router.post("", response_model=SessionSchema)
async def create_session_handler(
    payload: SessionCreateSchema,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
):
    """为当前用户显式创建一个空会话"""
    session = await session_service.create_session(
        user_id=current_user.id, title=payload.title
    )
    return SessionSchema(**asdict(session))


@session_router.get("", response_model=list[SessionSchema])
async def list_sessions_handler(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    limit: int = 50,
):
    """按最近活跃时间倒序返回当前用户的会话列表"""
    sessions = await session_service.list_sessions(user_id=current_user.id, limit=limit)
    return [SessionSchema(**asdict(session)) for session in sessions]


@session_router.get("/{session_id}", response_model=SessionDetailSchema)
async def get_session_handler(
    session_id: str,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
):
    """读取当前用户的会话元信息和 Redis 中最近 N 条短期消息"""
    detail = await session_service.get_session_detail(session_id, current_user.id)
    if detail is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session, messages = detail
    return SessionDetailSchema(
        **asdict(session),
        messages=[ChatMessageSchema(**asdict(message)) for message in messages],
    )


@session_router.delete("/{session_id}")
async def delete_session_handler(
    session_id: str,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
):
    """删除当前用户的会话短期消息和该会话产生的长期记忆"""
    deleted = await session_service.delete_session(session_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    return {"deleted": True, "session_id": session_id}


@session_router.get("/{session_id}/memories", response_model=list[MemorySchema])
async def list_session_memories_handler(
    session_id: str,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    limit: int = 100,
):
    """查看当前用户某个会话写入 Qdrant 的长期记忆"""
    memories = await session_service.list_memories(
        session_id=session_id, user_id=current_user.id, limit=limit
    )
    if memories is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    return [MemorySchema(**asdict(memory)) for memory in memories]
