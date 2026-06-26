"""
API 相关共享 fixture
- logged_in_client: 登录态复用，避免每个用例重复登录
- 通过 pytest_plugins 在 conftest 注册
"""
import pytest

from api.user_api import UserApi
from config.settings import settings
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
    yield user_api.client
    log.info("会话结束，清理登录态")


@pytest.fixture
def created_user(logged_in_client):
    """
    数据准备 + 自动清理示例：
    用例前创建一个用户，用例后自动删除，保证环境干净。
    """
    from api.user_api import UserApi
    from utils.random_data import random_name

    api = UserApi(client=logged_in_client)
    resp = api.create_user(name=random_name(), job="auto-test")
    user_id = resp.json().get("id")
    log.info(f"预置测试用户: id={user_id}")

    yield resp.json()

    # teardown：清理
    if user_id:
        api.delete_user(user_id)
        log.info(f"清理测试用户: id={user_id}")
