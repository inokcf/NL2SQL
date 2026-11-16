"""
会话元信息业务实体

用于描述一次多轮问数会话的标识 标题 归属用户和更新时间
API 层返回会话列表和会话详情时都会复用这份结构
"""

from dataclasses import dataclass


@dataclass
class SessionInfo:
    """多轮问数会话的元信息"""

    session_id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0
