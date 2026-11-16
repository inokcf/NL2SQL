"""
Redis 客户端管理器

负责按配置初始化 Redis 异步客户端，供短期会话记忆仓储复用
客户端采用懒连接，应用启动时不会因为 Redis 暂时不可用而直接失败
"""

from typing import Optional

from redis.asyncio import Redis

from app.conf.app_config import RedisConfig, app_config


class RedisClientManager:
    """管理 Redis 客户端生命周期"""

    def __init__(self, redis_config: RedisConfig):
        self.redis_config = redis_config
        # 真正初始化放到 init() 中，和项目其他客户端管理器保持一致
        self.client: Optional[Redis] = None

    def init(self):
        """创建 Redis 异步客户端；decode_responses 让读写都直接使用字符串"""
        self.client = Redis(
            host=self.redis_config.host,
            port=self.redis_config.port,
            password=self.redis_config.password or None,
            db=self.redis_config.db,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            health_check_interval=30,
        )

    async def close(self):
        """释放 Redis 连接池"""
        if self.client is not None:
            await self.client.aclose()
            self.client = None


# 模块级单例，供服务层和仓储层共享同一个连接池
redis_client_manager = RedisClientManager(app_config.redis)


if __name__ == "__main__":
    import asyncio

    redis_client_manager.init()

    async def test():
        """执行一次最小化读写，验证 Redis 服务是否可用"""
        client = redis_client_manager.client
        await client.set("nl2sql:test", "ok", ex=10)
        print(await client.get("nl2sql:test"))
        await redis_client_manager.close()

    asyncio.run(test())
