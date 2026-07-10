"""
API 相关共享 fixture
- logged_in_client: 登录态复用，避免每个用例重复登录
- 通过 pytest_plugins 在 conftest 注册
"""

import pytest

from api.user_api import UserApi
from config.settings import settings
from core.safety import ensure_write_allowed
from utils.logger import log


@pytest.fixture(scope="session")
def logged_in_client():
    """
    会话级登录态复用：整个测试会话只登录一次，
    返回已带 token 的 HttpClient，需要鉴权的用例直接用。
    """
    user_api = UserApi()
    resp = user_api.login(settings.username, settings.password)
    if resp.status_code != 200:
        log.warning("登录态预置失败，需要鉴权的用例可能失败")
    try:
        yield user_api.client
    finally:
        user_api.client.close()
        log.info("会话结束，登录客户端已关闭")


@pytest.fixture
def created_user(logged_in_client):
    """
    数据准备 + 自动清理示例：
    用例前创建一个用户，用例后自动删除，保证环境干净。
    """
    from api.user_api import UserApi
    from utils.random_data import random_name

    ensure_write_allowed(settings.env, "created_user")
    api = UserApi(client=logged_in_client)
    resp = api.create_user(name=random_name(), job="auto-test")
    user_id = resp.json().get("id")
    log.info(f"预置测试用户: id={user_id}")

    yield resp.json()

    # teardown：清理
    if user_id:
        api.delete_user(user_id)
        log.info(f"清理测试用户: id={user_id}")


@pytest.fixture
def db():
    """
    数据库 fixture：用例里直接 db.query/query_one/execute，结束自动关连接。
    用途：①取入参依赖的数据 ②断言时查库核对。
    用法:
        def test_xxx(db):
            row = db.query_one("SELECT id FROM products WHERE status='on' LIMIT 1")
            ...
    """
    from clients.db_client import DBClient

    ensure_write_allowed(settings.env, "db fixture")
    client = DBClient()
    try:
        yield client
    finally:
        client.close()


class CleanupError(RuntimeError):
    """一项或多项测试数据清理失败。"""

    def __init__(self, errors: list[Exception]):
        self.errors = errors
        detail = "; ".join(str(error) for error in errors)
        super().__init__(f"测试数据清理失败: {detail}")


class CleanupRegistry:
    """
    清理任务登记器：用例里注册"要清什么"，用例结束后统一执行。
    支持两种清理方式：①删库 SQL ②任意回调(如调删除接口)。
    逆序执行(后注册的先清，符合数据依赖顺序)；单条失败不影响其它。
    """

    def __init__(self):
        self._tasks = []  # [(kind, a, b)]

    def add_sql(self, sql: str, args=None):
        """注册一条清理 SQL(通常是 DELETE)"""
        self._tasks.append(("sql", sql, args))

    def add_table(self, table: str, where: str, args=None):
        """便捷：删除某表满足条件的数据。例: add_table('orders', 'order_id=%s', [oid])"""
        self._tasks.append(("sql", f"DELETE FROM {table} WHERE {where}", args))

    def add_callback(self, func):
        """注册任意清理回调，例: add_callback(lambda: OrderApi().delete_order(oid))"""
        self._tasks.append(("call", func, None))

    def run(self):
        if not self._tasks:
            return
        from clients.db_client import DBClient

        db = None
        errors = []
        try:
            for kind, a, b in reversed(self._tasks):  # 逆序清理
                try:
                    if kind == "sql":
                        if db is None:
                            db = DBClient()
                        n = db.execute(a, b)
                        log.info(f"清理数据 | {a} | 删除 {n} 行")
                    else:
                        a()
                        log.info("清理回调已执行")
                except Exception as e:  # noqa 单条失败不影响其它清理
                    errors.append(e)
                    log.error(f"清理失败: {e}")
        finally:
            if db:
                db.close()
        if errors:
            raise CleanupError(errors)


@pytest.fixture
def clean_data():
    """
    自动清理 fixture：用例里注册要清的数据，用例结束(含失败)自动清理。
    用法:
        def test_create_order(clean_data):
            resp = OrderApi().create_order(product_id=1, qty=1)
            oid = resp.json()["data"]["order_id"]
            clean_data.add_table("orders", "order_id=%s", [oid])   # 注册清理(创建后立刻注册)
            Assert.status_code(resp, 200)
        # 用例结束 → 自动 DELETE FROM orders WHERE order_id=oid
    """
    ensure_write_allowed(settings.env, "clean_data")
    registry = CleanupRegistry()
    yield registry
    registry.run()


@pytest.fixture
def api_client():
    """
    提供一条用例内【共享的干净 HttpClient】(未登录)。
    用途：场景级用例里多个接口模块共用同一个 client，让登录态(token/cookie)贯穿。
    用法:
        def test_flow(api_client):
            user  = UserApi(client=api_client)
            order = OrderApi(client=api_client)
            user.login(...)          # set_token 后，order 的请求自动带上同一 token
            order.create_order(...)
    """
    from core.http_client import HttpClient

    client = HttpClient()
    try:
        yield client
    finally:
        client.close()
