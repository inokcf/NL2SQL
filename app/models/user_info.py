"""
`user_info` ORM 模型

保存系统登录用户的基本信息和密码哈希
用户 id 会继续用作 Redis 会话隔离键和 Qdrant 长期记忆的 user_id 过滤条件
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserInfoMySQL(Base):
    """用户信息表对应的 ORM 模型"""

    __tablename__ = "user_info"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment="用户编号")
    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True, comment="登录用户名"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="scrypt 密码哈希"
    )
    display_name: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", comment="展示名称"
    )
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, default="user", comment="用户角色"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否启用"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
