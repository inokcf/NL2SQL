"""
用户业务实体

用于在认证服务 仓储和 API 层之间传递用户信息
UserInfo 不包含密码哈希，避免业务层和响应层意外泄露敏感字段
"""

from dataclasses import dataclass


@dataclass
class UserInfo:
    """对外使用的用户信息"""

    id: str
    username: str
    display_name: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str


@dataclass
class UserAuthRecord(UserInfo):
    """认证流程内部使用的用户信息，包含密码哈希"""

    password_hash: str = ""
