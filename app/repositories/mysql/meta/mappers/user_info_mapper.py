"""
用户信息映射器

负责在用户 ORM 模型与业务实体之间转换
密码哈希只在 UserAuthRecord 中保留，普通 UserInfo 不携带敏感字段
"""

from dataclasses import asdict

from app.entities.user_info import UserAuthRecord, UserInfo
from app.models.user_info import UserInfoMySQL


class UserInfoMapper:
    """负责 `UserInfo` / `UserAuthRecord` 与 `UserInfoMySQL` 的转换"""

    @staticmethod
    def _format_time(value) -> str:
        return value.isoformat(timespec="seconds") if value else ""

    @classmethod
    def to_entity(cls, model: UserInfoMySQL) -> UserInfo:
        """把 ORM 模型转换为不包含密码哈希的用户实体"""
        return UserInfo(
            id=model.id,
            username=model.username,
            display_name=model.display_name or "",
            role=model.role,
            is_active=bool(model.is_active),
            created_at=cls._format_time(model.created_at),
            updated_at=cls._format_time(model.updated_at),
        )

    @classmethod
    def to_auth_record(cls, model: UserInfoMySQL) -> UserAuthRecord:
        """把 ORM 模型转换为认证流程使用的用户实体"""
        return UserAuthRecord(
            **asdict(cls.to_entity(model)),
            password_hash=model.password_hash,
        )

    @staticmethod
    def to_model(
        user_id: str,
        username: str,
        password_hash: str,
        display_name: str,
        role: str = "user",
    ) -> UserInfoMySQL:
        """构建待写入数据库的用户 ORM 模型"""
        return UserInfoMySQL(
            id=user_id,
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
            is_active=True,
        )
