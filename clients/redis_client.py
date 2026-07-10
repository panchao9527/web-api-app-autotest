"""
Redis 客户端（验证缓存 / 清理测试数据）
- 连接信息来自 config.yaml 的 redis 段 + .env 的 REDIS_PASSWORD
- decode_responses=True，取出来直接是 str

用法:
    from clients.redis_client import RedisClient

    with RedisClient() as r:
        r.set("k", "v", ex=60)
        v = r.get("k")
        r.delete("k")
"""

from config.settings import settings
from utils.logger import log


class RedisClient:
    def __init__(self, redis_config: dict = None):
        import redis  # 延迟导入

        cfg = redis_config or settings.redis
        if not cfg.get("host"):
            raise ValueError("Redis 未配置：请在 config.yaml 的 redis 段填好连接信息")

        self.client = redis.Redis(
            host=cfg["host"],
            port=int(cfg.get("port", 6379)),
            db=int(cfg.get("db", 0)),
            password=cfg.get("password") or None,
            decode_responses=True,
            socket_timeout=settings.timeout,
        )
        log.info(f"Redis 连接 | {cfg['host']}:{cfg.get('port', 6379)} db={cfg.get('db', 0)}")

    def get(self, key: str):
        val = self.client.get(key)
        log.info(f"Redis GET {key} -> {val}")
        return val

    def set(self, key: str, value, ex: int = None):
        """ex: 过期秒数"""
        log.info(f"Redis SET {key}={value} ex={ex}")
        return self.client.set(key, value, ex=ex)

    def delete(self, *keys):
        log.info(f"Redis DEL {keys}")
        return self.client.delete(*keys)

    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))

    def expire(self, key: str, seconds: int):
        return self.client.expire(key, seconds)

    def keys(self, pattern: str = "*") -> list:
        return self.client.keys(pattern)

    def hgetall(self, key: str) -> dict:
        return self.client.hgetall(key)

    def close(self):
        try:
            self.client.close()
            log.info("Redis 连接已关闭")
        except Exception:  # noqa
            pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
