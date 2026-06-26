"""
自定义断言库
- 统一断言风格，失败信息更清晰，自动记录日志 + Allure step
- API 响应校验 / JSON 结构校验 / 通用断言
"""
import allure
from jsonschema import ValidationError, validate

from utils.logger import log


class Assert:
    @staticmethod
    @allure.step("断言: {msg}")
    def equal(actual, expected, msg=""):
        log.info(f"断言相等 | 实际={actual} 期望={expected} | {msg}")
        assert actual == expected, f"{msg} | 期望 {expected}，实际 {actual}"

    @staticmethod
    @allure.step("断言: {msg}")
    def contains(container, member, msg=""):
        log.info(f"断言包含 | {member} in {container} | {msg}")
        assert member in container, f"{msg} | {container} 中不包含 {member}"

    @staticmethod
    @allure.step("断言状态码 == {expected}")
    def status_code(resp, expected=200):
        actual = resp.status_code
        log.info(f"断言状态码 | 实际={actual} 期望={expected}")
        assert actual == expected, (
            f"状态码不符 | 期望 {expected}，实际 {actual} | 响应: {resp.text[:300]}"
        )

    @staticmethod
    @allure.step("断言响应字段 {key} == {expected}")
    def json_value(resp, key, expected):
        data = resp.json()
        actual = data.get(key)
        log.info(f"断言响应字段 | {key}: 实际={actual} 期望={expected}")
        assert actual == expected, f"字段 {key} 不符 | 期望 {expected}，实际 {actual}"

    @staticmethod
    @allure.step("断言响应符合 JSON Schema")
    def match_schema(resp, schema: dict):
        """校验响应结构是否符合预期 schema (契约测试常用)"""
        try:
            validate(instance=resp.json(), schema=schema)
            log.info("JSON Schema 校验通过")
        except ValidationError as e:
            raise AssertionError(f"响应结构不符合 schema: {e.message}")

    @staticmethod
    @allure.step("断言: {msg}")
    def is_true(condition, msg=""):
        log.info(f"断言为真 | {msg}")
        assert condition, f"断言失败 | {msg}"
