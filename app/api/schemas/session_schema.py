"""
会话管理接口数据结构

定义会话创建 会话列表 会话详情和长期记忆查询的请求与响应结构
"""

from pydantic import BaseModel, Field


class SessionCreateSchema(BaseModel):
    """创建会话请求体"""

    title: str = "新会话"


class ChatMessageSchema(BaseModel):
    """短期会话消息"""

    id: str
    role: str
    content: str
    created_at: str
    sql: str = ""
    resolved_query: str = ""
    metadata: dict = Field(default_factory=dict)


class SessionSchema(BaseModel):
    """会话概要信息"""

    session_id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class SessionDetailSchema(SessionSchema):
    """会话详情，包含最近消息窗口"""

    messages: list[ChatMessageSchema] = Field(default_factory=list)


class MemorySchema(BaseModel):
    """长期向量记忆"""

    id: str
    user_id: str
    session_id: str
    memory_type: str
    content: str
    question: str = ""
    resolved_query: str = ""
    sql: str = ""
    created_at: str = ""
    score: float | None = None
