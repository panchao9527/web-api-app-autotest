"""
响应字段提取工具（基于 JSONPath）
- 从接口返回的 JSON / dict 里按路径取值
- 场景级测试常用：从上一步响应取 id 传给下一步
- 用法:
    from utils.extractor import extract, extract_all
    order_id = extract(resp.json(), "$.data.order_id")
    names    = extract_all(resp.json(), "$.data.list[*].name")
"""
from jsonpath_ng.ext import parse

from utils.logger import log


def extract(data: dict | list, expr: str, default=None):
    """
    提取第一个匹配值；无匹配返回 default。
    expr 为 JSONPath，如 "$.data.id"、"$.list[0].name"
    """
    matches = [m.value for m in parse(expr).find(data)]
    if not matches:
        log.warning(f"JSONPath 无匹配: {expr}")
        return default
    return matches[0]


def extract_all(data: dict | list, expr: str) -> list:
    """提取所有匹配值，返回列表"""
    return [m.value for m in parse(expr).find(data)]
