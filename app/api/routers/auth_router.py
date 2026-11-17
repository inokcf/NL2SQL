"""
认证接口路由

提供注册 登录和当前用户查询接口
认证成功后返回 Bearer Token，前端后续请求统一通过 Authorization 头携带
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_auth_service, get_current_user
from app.api.schemas.auth_schema import (
    LoginSchema,
    RegisterSchema,
    TokenSchema,
    UserSchema,
)
from app.conf.app_config import app_config
from app.entities.user_info import UserInfo
from app.services.auth_service import AuthService

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_schema(user: UserInfo) -> UserSchema:
    """把用户实体转换为 API 响应结构"""
    return UserSchema(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        created_at=user.created_at,
    )


def _token_schema(user: UserInfo, token: str) -> TokenSchema:
    return TokenSchema(
        access_token=token,
        expires_in=app_config.auth.token_expire_minutes * 60,
        user=_user_schema(user),
    )


@auth_router.post("/register", response_model=TokenSchema, status_code=201)
async def register_handler(
    payload: RegisterSchema,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """注册新用户并直接返回登录 Token"""
    try:
        user, token = await auth_service.register(
            username=payload.username,
            password=payload.password,
            display_name=payload.display_name,
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return _token_schema(user, token)


@auth_router.post("/login", response_model=TokenSchema)
async def login_handler(
    payload: LoginSchema,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """校验用户名密码并返回登录 Token"""
    try:
        user, token = await auth_service.login(
            username=payload.username,
            password=payload.password,
        )
    except PermissionError as error:
        raise HTTPException(
            status_code=401,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return _token_schema(user, token)


@auth_router.get("/me", response_model=UserSchema)
async def me_handler(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
):
    """返回当前登录用户信息"""
    return _user_schema(current_user)
