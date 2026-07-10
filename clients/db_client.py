"""
MySQL 数据库客户端（数据校验/数据准备用）
- 典型用途：接口/UI 操作后，查库断言数据是否正确；或预置/清理测试数据
- 连接信息来自 config.yaml 的 db 段 + .env 的 DB_USER/DB_PASSWORD
- 支持上下文管理器，用完自动关闭连接

用法:
    from clients.db_client import DBClient

    with DBClient() as db:
        rows = db.query("SELECT * FROM users WHERE id=%s", [1])
        one  = db.query_one("SELECT count(*) AS c FROM orders")
        n    = db.execute("DELETE FROM orders WHERE id=%s", [order_id])
"""

from config.settings import settings
from utils.logger import log


class DBClient:
    def __init__(self, db_config: dict = None):
        # 延迟导入，未装 PyMySQL 也不影响其它用例
        import pymysql
        from pymysql.cursors import DictCursor

        cfg = db_config or settings.db
        if not cfg.get("host"):
            raise ValueError("数据库未配置：请在 config.yaml 的 db 段和 .env 里填好连接信息")

        self.conn = pymysql.connect(
            host=cfg["host"],
            port=int(cfg.get("port", 3306)),
            user=cfg.get("user", ""),
            password=cfg.get("password", ""),
            database=cfg.get("name", ""),
            charset="utf8mb4",
            cursorclass=DictCursor,
            connect_timeout=settings.timeout,
        )
        log.info(f"DB 连接成功 | {cfg['host']}:{cfg.get('port', 3306)}/{cfg.get('name')}")

    # ---- 查询 ----
    def query(self, sql: str, args=None) -> list[dict]:
        """查询多行，返回 [{列: 值}, ...]"""
        log.info(f"SQL查询: {sql} | 参数: {args}")
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
            rows = cur.fetchall()
        log.info(f"查询返回 {len(rows)} 行")
        return rows

    def query_one(self, sql: str, args=None) -> dict | None:
        """查询单行，返回 {列: 值} 或 None"""
        log.info(f"SQL查询(单行): {sql} | 参数: {args}")
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()

    # ---- 写入 ----
    def execute(self, sql: str, args=None) -> int:
        """执行 insert/update/delete，返回受影响行数（自动提交）"""
        log.info(f"SQL执行: {sql} | 参数: {args}")
        with self.conn.cursor() as cur:
            affected = cur.execute(sql, args)
        self.conn.commit()
        log.info(f"受影响行数: {affected}")
        return affected

    def close(self):
        try:
            self.conn.close()
            log.info("DB 连接已关闭")
        except Exception:  # noqa
            pass

    # ---- 上下文管理器 ----
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
