"""统一断言：比较原始值，日志/异常仅输出脱敏副本，不自动向 Allure 传入原始参数。"""

import re
from functools import wraps

import allure
from jsonschema import ValidationError, validate

from utils.logger import log
from utils.redaction import MASK, redact, redact_text, safe_input_value


def _step(title):
    """固定步骤标题，避免 allure.step 装饰器自动采集 actual/expected。"""

    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with allure.step(title):
                return function(*args, **kwargs)

        return wrapped

    return decorate


def _safe(value, sensitive=False):
    return MASK if sensitive else str(redact(value))


def _check(condition, message):
    safe_message = redact_text(message)
    log.info(safe_message)
    if not condition:
        raise AssertionError(safe_message)


def _to_data(resp):
    return resp.json() if hasattr(resp, "json") else resp


class Assert:
    @staticmethod
    @_step("断言相等")
    def equal(actual, expected, msg="", sensitive=False):
        """无字段名的秘密标量请显式传 sensitive=True。"""
        _check(
            actual == expected,
            f"{msg} | 期望 {_safe(expected, sensitive)}，实际 {_safe(actual, sensitive)}",
        )

    @staticmethod
    @_step("断言不相等")
    def not_equal(actual, expected, msg="", sensitive=False):
        _check(
            actual != expected,
            f"{msg} | 实际 {_safe(actual, sensitive)}，不应为 {_safe(expected, sensitive)}",
        )

    @staticmethod
    @_step("断言为真")
    def is_true(condition, msg=""):
        _check(condition, f"{msg} | 断言应为真")

    @staticmethod
    @_step("断言为假")
    def is_false(condition, msg=""):
        _check(not condition, f"{msg} | 断言应为假")

    @staticmethod
    @_step("断言包含")
    def contains(container, member, msg=""):
        _check(member in container, f"{msg} | {_safe(container)} 应包含 {_safe(member)}")

    @staticmethod
    @_step("断言不包含")
    def not_contains(container, member, msg=""):
        _check(member not in container, f"{msg} | {_safe(container)} 不应包含 {_safe(member)}")

    @staticmethod
    @_step("断言为 None")
    def is_none(actual, msg=""):
        _check(actual is None, f"{msg} | 期望 None，实际 {_safe(actual)}")

    @staticmethod
    @_step("断言非 None")
    def not_none(actual, msg=""):
        _check(actual is not None, f"{msg} | 不应为 None")

    @staticmethod
    @_step("断言非空")
    def not_empty(actual, msg=""):
        _check(bool(actual), f"{msg} | 期望非空，实际 {_safe(actual)}")

    @staticmethod
    @_step("断言长度")
    def length(obj, expected, msg=""):
        _check(len(obj) == expected, f"{msg} | 长度期望 {expected}，实际 {len(obj)}")

    @staticmethod
    @_step("断言大于")
    def greater(actual, expected, msg=""):
        _check(actual > expected, f"{msg} | 期望 >{_safe(expected)}，实际 {_safe(actual)}")

    @staticmethod
    @_step("断言小于")
    def less(actual, expected, msg=""):
        _check(actual < expected, f"{msg} | 期望 <{_safe(expected)}，实际 {_safe(actual)}")

    @staticmethod
    @_step("断言闭区间")
    def between(actual, low, high, msg=""):
        _check(
            low <= actual <= high,
            f"{msg} | 期望 [{_safe(low)},{_safe(high)}]，实际 {_safe(actual)}",
        )

    @staticmethod
    @_step("断言近似相等")
    def approx(actual, expected, tol=0.01, msg=""):
        _check(
            abs(float(actual) - float(expected)) <= tol,
            f"{msg} | 期望≈{_safe(expected)}(±{tol})，实际 {_safe(actual)}",
        )

    @staticmethod
    @_step("断言正则匹配")
    def match_regex(text, pattern, msg=""):
        _check(
            re.search(pattern, str(text)) is not None,
            f"{msg} | {_safe(text)} 应匹配 {_safe(pattern)}",
        )

    @staticmethod
    @_step("断言 HTTP 状态码")
    def status_code(resp, expected=200):
        # 正文已由 HttpClient 脱敏附加，不在异常消息里再次输出原文。
        _check(resp.status_code == expected, f"状态码期望 {expected}，实际 {resp.status_code}")

    @staticmethod
    @_step("断言响应字段")
    def json_value(resp, key, expected):
        actual = _to_data(resp).get(key)
        _check(
            actual == expected,
            f"字段 {key} | 期望 {safe_input_value(redact(expected), key)}，实际 {safe_input_value(redact(actual), key)}",
        )

    @staticmethod
    @_step("断言 JSONPath 字段")
    def jsonpath(resp, expr, expected):
        from utils.extractor import extract

        actual = extract(_to_data(resp), expr)
        _check(
            actual == expected,
            f"{expr} | 期望 {safe_input_value(redact(expected), expr)}，实际 {safe_input_value(redact(actual), expr)}",
        )

    @staticmethod
    @_step("断言 JSONPath 存在且非空")
    def jsonpath_exists(resp, expr):
        from utils.extractor import extract

        actual = extract(_to_data(resp), expr)
        _check(actual is not None and actual != "", f"{expr} 应存在且非空")

    @staticmethod
    @_step("断言 JSON Schema")
    def match_schema(resp, schema: dict):
        try:
            validate(instance=_to_data(resp), schema=schema)
        except ValidationError as exc:
            # jsonschema.message 携带失败原值，因此只报告字段路径和校验规则。
            path = ".".join(str(part) for part in exc.absolute_path) or "$"
            raise AssertionError(
                f"响应结构不符合 schema: 字段 {path}，规则 {exc.validator}"
            ) from None
        log.info("JSON Schema 校验通过")
