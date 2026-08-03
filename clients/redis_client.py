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
from core.safety import ensure_write_allowed
from utils.logger import log
from utils.redaction import safe_input_value


def _safe_key(key: str) -> str:
    return safe_input_value(key, key)


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
        log.info(f"Redis GET {_safe_key(key)} -> {'命中' if val is not None else '未命中'}")
        return val

    def set(self, key: str, value, ex: int = None):
        """ex: 过期秒数"""
        ensure_write_allowed(settings.env, "RedisClient.set")
        log.info(f"Redis SET {_safe_key(key)} ex={ex}（值不写入日志）")
        return self.client.set(key, value, ex=ex)

    def delete(self, *keys):
        ensure_write_allowed(settings.env, "RedisClient.delete")
        safe_keys = tuple(_safe_key(key) for key in keys)
        log.info(f"Redis DEL {safe_keys}")
        return self.client.delete(*keys)

    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))

    def expire(self, key: str, seconds: int):
        ensure_write_allowed(settings.env, "RedisClient.expire")
        return self.client.expire(key, seconds)

    def keys(self, pattern: str = "*") -> list:
        """使用渐进式 SCAN，避免 KEYS 阻塞 Redis。"""
        return list(self.client.scan_iter(match=pattern, count=100))

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
