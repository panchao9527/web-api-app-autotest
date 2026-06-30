"""
自定义断言库
- 统一断言风格，失败信息清晰，自动记录日志 + Allure step
- 覆盖：通用断言 / 数值比较 / 空值长度 / 文本正则 / 浮点近似 / 接口响应 / JSONPath 嵌套取值 / Schema 契约
- 用法: from core.assertions import Assert
"""
import re

import allure
from jsonschema import ValidationError, validate

from utils.logger import log


def _to_data(resp):
    """兼容 requests.Response 或已是 dict/list 的数据"""
    return resp.json() if hasattr(resp, "json") else resp


class Assert:
    # ---------------- 通用 ----------------
    @staticmethod
    @allure.step("断言相等: {msg}")
    def equal(actual, expected, msg=""):
        log.info(f"断言相等 | 实际={actual} 期望={expected} | {msg}")
        assert actual == expected, f"{msg} | 期望 {expected}，实际 {actual}"

    @staticmethod
    @allure.step("断言不相等: {msg}")
    def not_equal(actual, expected, msg=""):
        log.info(f"断言不等 | 实际={actual} 不应={expected} | {msg}")
        assert actual != expected, f"{msg} | 不应等于 {expected}，实际 {actual}"

    @staticmethod
    @allure.step("断言为真: {msg}")
    def is_true(condition, msg=""):
        log.info(f"断言为真 | {msg}")
        assert condition, f"断言失败(应为真) | {msg}"

    @staticmethod
    @allure.step("断言为假: {msg}")
    def is_false(condition, msg=""):
        log.info(f"断言为假 | {msg}")
        assert not condition, f"断言失败(应为假) | {msg}"

    @staticmethod
    @allure.step("断言包含: {msg}")
    def contains(container, member, msg=""):
        log.info(f"断言包含 | {member} in {container} | {msg}")
        assert member in container, f"{msg} | {container} 中不包含 {member}"

    @staticmethod
    @allure.step("断言不包含: {msg}")
    def not_contains(container, member, msg=""):
        log.info(f"断言不包含 | {member} not in ... | {msg}")
        assert member not in container, f"{msg} | 不应包含 {member}"

    # ---------------- 空值 / 长度 ----------------
    @staticmethod
    @allure.step("断言为 None: {msg}")
    def is_none(actual, msg=""):
        assert actual is None, f"{msg} | 期望 None，实际 {actual}"

    @staticmethod
    @allure.step("断言非 None: {msg}")
    def not_none(actual, msg=""):
        assert actual is not None, f"{msg} | 不应为 None"

    @staticmethod
    @allure.step("断言非空: {msg}")
    def not_empty(actual, msg=""):
        """非空：字符串/列表/字典等长度 > 0"""
        log.info(f"断言非空 | 实际={actual} | {msg}")
        assert actual, f"{msg} | 期望非空，实际为空: {actual!r}"

    @staticmethod
    @allure.step("断言长度 == {expected}")
    def length(obj, expected, msg=""):
        actual = len(obj)
        log.info(f"断言长度 | 实际={actual} 期望={expected} | {msg}")
        assert actual == expected, f"{msg} | 长度期望 {expected}，实际 {actual}"

    # ---------------- 数值比较 ----------------
    @staticmethod
    @allure.step("断言 {actual} > {expected}")
    def greater(actual, expected, msg=""):
        assert actual > expected, f"{msg} | 期望 >{expected}，实际 {actual}"

    @staticmethod
    @allure.step("断言 {actual} < {expected}")
    def less(actual, expected, msg=""):
        assert actual < expected, f"{msg} | 期望 <{expected}，实际 {actual}"

    @staticmethod
    @allure.step("断言 {low} <= {actual} <= {high}")
    def between(actual, low, high, msg=""):
        """范围断言(闭区间)"""
        assert low <= actual <= high, f"{msg} | 期望 [{low},{high}]，实际 {actual}"

    @staticmethod
    @allure.step("断言近似相等(容差 {tol})")
    def approx(actual, expected, tol=0.01, msg=""):
        """浮点近似相等(金额/税率常用，避免精度问题)"""
        log.info(f"断言近似 | 实际={actual} 期望={expected} 容差={tol} | {msg}")
        assert abs(float(actual) - float(expected)) <= tol, (
            f"{msg} | 期望≈{expected}(±{tol})，实际 {actual}"
        )

    # ---------------- 文本 / 正则 ----------------
    @staticmethod
    @allure.step("断言匹配正则: {pattern}")
    def match_regex(text, pattern, msg=""):
        log.info(f"断言正则 | {pattern} ~ {text} | {msg}")
        assert re.search(pattern, str(text)), f"{msg} | {text} 不匹配 /{pattern}/"

    # ---------------- 接口响应 ----------------
    @staticmethod
    @allure.step("断言状态码 == {expected}")
    def status_code(resp, expected=200):
        actual = resp.status_code
        log.info(f"断言状态码 | 实际={actual} 期望={expected}")
        assert actual == expected, (
            f"状态码不符 | 期望 {expected}，实际 {actual} | 响应: {resp.text[:300]}"
        )

    @staticmethod
    @allure.step("断言响应顶层字段 {key} == {expected}")
    def json_value(resp, key, expected):
        """断言响应【顶层】字段；嵌套字段请用 jsonpath()"""
        actual = _to_data(resp).get(key)
        log.info(f"断言响应字段 | {key}: 实际={actual} 期望={expected}")
        assert actual == expected, f"字段 {key} 不符 | 期望 {expected}，实际 {actual}"

    @staticmethod
    @allure.step("断言 JSONPath {expr} == {expected}")
    def jsonpath(resp, expr, expected):
        """
        断言【嵌套】字段，用 JSONPath 定位，如 "$.data.order.status"。
        解决 json_value 只能取顶层的局限。
        """
        from utils.extractor import extract
        actual = extract(_to_data(resp), expr)
        log.info(f"断言JSONPath | {expr}: 实际={actual} 期望={expected}")
        assert actual == expected, f"{expr} 不符 | 期望 {expected}，实际 {actual}"

    @staticmethod
    @allure.step("断言 JSONPath {expr} 存在且非空")
    def jsonpath_exists(resp, expr):
        """断言某嵌套字段存在且非空(如返回里必须有 token/order_id)"""
        from utils.extractor import extract
        actual = extract(_to_data(resp), expr)
        log.info(f"断言JSONPath存在 | {expr}: {actual}")
        assert actual is not None and actual != "", f"{expr} 不存在或为空"

    @staticmethod
    @allure.step("断言响应符合 JSON Schema")
    def match_schema(resp, schema: dict):
        """校验响应结构是否符合预期 schema (契约测试常用)"""
        try:
            validate(instance=_to_data(resp), schema=schema)
            log.info("JSON Schema 校验通过")
        except ValidationError as e:
            raise AssertionError(f"响应结构不符合 schema: {e.message}")
