"""
用户 MySQL 仓储

负责用户表的初始化 查询和创建
当前用户的 id 会继续作为 Redis 会话和 Qdrant 长期记忆的隔离键
"""

import uuid

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.user_info import UserAuthRecord, UserInfo
from app.models.user_info import UserInfoMySQL
from app.repositories.mysql.meta.mappers.user_info_mapper import UserInfoMapper


class UserMySQLRepository:
    """负责用户信息的持久化与查询"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def ensure_table(self):
        """为已有数据库补建用户表，避免必须重建 MySQL 容器"""
        exists = await self.session.execute(text("SHOW TABLES LIKE 'user_info'"))
        if exists.first():
            return

        sql = """
        CREATE TABLE IF NOT EXISTS user_info (
            id VARCHAR(36) PRIMARY KEY COMMENT '用户编号',
            username VARCHAR(64) NOT NULL UNIQUE COMMENT '登录用户名',
            password_hash VARCHAR(255) NOT NULL COMMENT 'scrypt 密码哈希',
            display_name VARCHAR(64) NOT NULL DEFAULT '' COMMENT '展示名称',
            role VARCHAR(32) NOT NULL DEFAULT 'user' COMMENT '用户角色',
            is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
        await self.session.execute(text(sql))
        await self.session.commit()

    async def count_users(self) -> int:
        """统计用户数量，用于首次启动时创建体验账号"""
        result = await self.session.execute(
            select(func.count()).select_from(UserInfoMySQL)
        )
        return int(result.scalar_one())

    async def get_auth_by_username(self, username: str) -> UserAuthRecord | None:
        """按用户名查询包含密码哈希的认证记录"""
        result = await self.session.execute(
            select(UserInfoMySQL).where(UserInfoMySQL.username == username).limit(1)
        )
        model = result.scalar_one_or_none()
        return UserInfoMapper.to_auth_record(model) if model else None

    async def get_by_id(self, user_id: str) -> UserInfo | None:
        """按用户 id 查询用户信息"""
        model = await self.session.get(UserInfoMySQL, user_id)
        return UserInfoMapper.to_entity(model) if model else None

    async def create_user(
        self,
        username: str,
        password_hash: str,
        display_name: str,
        role: str = "user",
    ) -> UserInfo:
        """创建用户；用户名冲突时转换为业务层可识别的 ValueError"""
        model = UserInfoMapper.to_model(
            user_id=str(uuid.uuid4()),
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
        )
        try:
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
        except IntegrityError as error:
            await self.session.rollback()
            raise ValueError("用户名已存在") from error

        return UserInfoMapper.to_entity(model)
