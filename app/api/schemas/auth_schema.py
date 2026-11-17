"""
认证接口数据结构

定义注册 登录 当前用户和 Token 响应的请求与响应结构
"""

from pydantic import BaseModel, Field


class RegisterSchema(BaseModel):
    """注册请求体"""

    username: str = Field(
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9_\-一-龥]+$",
        description="3-64 位用户名，允许中英文、数字、下划线和短横线",
    )
    password: str = Field(min_length=6, max_length=128)
    display_name: str | None = Field(default=None, max_length=64)


class LoginSchema(BaseModel):
    """登录请求体"""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class UserSchema(BaseModel):
    """返回给前端的用户信息"""

    id: str
    username: str
    display_name: str
    role: str
    created_at: str


class TokenSchema(BaseModel):
    """登录成功后的 Token 与用户信息"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSchema
