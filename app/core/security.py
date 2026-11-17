"""
密码哈希与登录 Token 工具

密码使用标准库 hashlib.scrypt 加盐哈希，避免引入额外的密码学依赖
登录 Token 使用 HMAC-SHA256 签名的 JWT，载荷中包含用户 id 和过期时间
"""

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.conf.app_config import app_config

# scrypt 参数兼顾安全性和本地开发时的计算耗时
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 64


def hash_password(password: str) -> str:
    """生成带随机盐的 scrypt 密码哈希"""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    return "$".join(
        [
            "scrypt",
            str(_SCRYPT_N),
            str(_SCRYPT_R),
            str(_SCRYPT_P),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(digest).decode("ascii"),
        ]
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """校验明文密码与数据库中的 scrypt 哈希是否匹配"""
    try:
        scheme, n, r, p, salt_b64, digest_b64 = stored_hash.split("$")
        if scheme != "scrypt":
            return False

        n_value = int(n)
        # 对数据库中的参数做基本边界检查，避免异常参数导致计算资源被耗尽
        if n_value < 2**10 or n_value > 2**16:
            return False

        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        candidate = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n_value,
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
        return hmac.compare_digest(candidate, expected)
    except ValueError, TypeError:
        return False


def create_access_token(user_id: str, username: str, role: str) -> str:
    """签发带用户身份和过期时间的 JWT"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=app_config.auth.token_expire_minutes),
    }
    return jwt.encode(
        payload,
        app_config.auth.secret_key,
        algorithm=app_config.auth.algorithm,
    )


def decode_access_token(token: str) -> dict | None:
    """校验并解析 JWT，签名错误或过期时返回 None"""
    try:
        return jwt.decode(
            token,
            app_config.auth.secret_key,
            algorithms=[app_config.auth.algorithm],
        )
    except jwt.InvalidTokenError:
        return None
