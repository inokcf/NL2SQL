"""
认证服务

负责用户注册 登录和首次启动时的体验账号初始化
密码校验和 Token 签发统一收敛在这里，路由层只负责 HTTP 语义映射
"""

from app.core.log import logger
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.entities.user_info import UserInfo
from app.repositories.mysql.meta.user_mysql_repository import UserMySQLRepository


class AuthService:
    """封装注册、登录和默认用户初始化逻辑"""

    def __init__(self, user_repository: UserMySQLRepository):
        self.user_repository = user_repository

    async def register(
        self,
        username: str,
        password: str,
        display_name: str | None = None,
    ) -> tuple[UserInfo, str]:
        """注册新用户并直接签发登录 Token"""
        username = username.strip()
        if await self.user_repository.get_auth_by_username(username):
            raise ValueError("用户名已存在")

        display_name = (display_name or username).strip() or username
        user = await self.user_repository.create_user(
            username=username,
            password_hash=hash_password(password),
            display_name=display_name,
        )
        token = create_access_token(user.id, user.username, user.role)
        return user, token

    async def login(self, username: str, password: str) -> tuple[UserInfo, str]:
        """校验用户名密码并签发登录 Token"""
        record = await self.user_repository.get_auth_by_username(username.strip())
        if (
            record is None
            or not record.is_active
            or not verify_password(password, record.password_hash)
        ):
            # 不区分“用户不存在”和“密码错误”，避免泄露账号是否存在
            raise PermissionError("用户名或密码错误")

        user = UserInfo(
            id=record.id,
            username=record.username,
            display_name=record.display_name,
            role=record.role,
            is_active=record.is_active,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        token = create_access_token(user.id, user.username, user.role)
        return user, token

    async def ensure_default_user(self):
        """确保用户表存在，并在空库中创建体验账号"""
        await self.user_repository.ensure_table()
        if await self.user_repository.count_users() > 0:
            return

        # 体验账号只用于本地演示，前端登录页会展示这组凭据
        await self.user_repository.create_user(
            username="admin",
            password_hash=hash_password("admin123"),
            display_name="管理员",
            role="admin",
        )
        logger.info("已创建默认体验账号：admin")
