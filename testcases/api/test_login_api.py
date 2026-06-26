"""
登录接口测试 (数据驱动示例)
- 一套逻辑跑 login_data.yaml 里的多组数据
- 演示：parametrize 数据驱动 + 自定义断言 + Allure 标记
"""
import allure
import pytest

from api.user_api import UserApi
from core.assertions import Assert
from utils.data_loader import load_yaml

login_data = load_yaml("login_data.yaml")


@allure.epic("用户中心")
@allure.feature("登录接口")
@pytest.mark.api
class TestLoginApi:

    @allure.story("登录场景覆盖")
    @pytest.mark.parametrize("case", login_data, ids=[c["case_id"] for c in login_data])
    def test_login(self, case):
        allure.dynamic.title(case["desc"])
        user_api = UserApi()
        resp = user_api.login(case["username"], case["password"])

        # 断言状态码
        Assert.status_code(resp, case["expected_status"])

        # 成功场景应返回 token
        if case["expect_success"]:
            Assert.contains(resp.json(), "token", "登录成功应返回 token")


@allure.epic("用户中心")
@allure.feature("用户管理接口")
@pytest.mark.api
class TestUserApi:

    @allure.story("查询用户")
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_get_user(self):
        resp = UserApi().get_user(user_id=2)
        Assert.status_code(resp, 200)

    @allure.story("创建用户")
    @pytest.mark.regression
    def test_create_user(self):
        resp = UserApi().create_user(name="kiro", job="tester")
        Assert.status_code(resp, 201)
        Assert.json_value(resp, "name", "kiro")

    @allure.story("响应结构契约校验")
    def test_user_schema(self):
        """演示 JSON Schema 契约测试：防止后端悄悄改字段"""
        resp = UserApi().get_user(user_id=2)
        schema = {
            "type": "object",
            "required": ["data"],
            "properties": {
                "data": {
                    "type": "object",
                    "required": ["id", "email"],
                    "properties": {
                        "id": {"type": "integer"},
                        "email": {"type": "string"},
                    },
                }
            },
        }
        Assert.status_code(resp, 200)
        Assert.match_schema(resp, schema)
