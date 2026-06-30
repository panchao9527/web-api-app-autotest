"""
字典 / 响应数据工具
- 深取值、字典对比、子集校验、字段筛选
- 用法: from utils.dict_util import deep_get, dict_diff, contains_subset
"""


def deep_get(data, path: str, default=None):
    """
    按点路径深取值，支持列表下标。
    例: deep_get(resp, "data.list.0.name")
    """
    cur = data
    for part in path.split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return default
        elif isinstance(cur, dict):
            if part in cur:
                cur = cur[part]
            else:
                return default
        else:
            return default
    return cur


def pick(d: dict, keys: list) -> dict:
    """只保留指定字段"""
    return {k: d[k] for k in keys if k in d}


def omit(d: dict, keys: list) -> dict:
    """排除指定字段(如对比响应时忽略 时间戳/id 等动态字段)"""
    return {k: v for k, v in d.items() if k not in keys}


def contains_subset(full, subset) -> bool:
    """
    判断 full 是否"包含" subset(深层)。
    断言响应只关心部分字段时很有用：只校验你关心的字段，不管多余字段。
    """
    if isinstance(subset, dict):
        if not isinstance(full, dict):
            return False
        return all(k in full and contains_subset(full[k], v) for k, v in subset.items())
    if isinstance(subset, list):
        if not isinstance(full, list) or len(full) < len(subset):
            return False
        return all(contains_subset(full[i], subset[i]) for i in range(len(subset)))
    return full == subset


def dict_diff(expected, actual, _path: str = "") -> dict:
    """
    递归对比两个字典/值，返回不一致的路径 -> (期望, 实际)。
    排查"响应和预期对不上"时直接定位差异。
    """
    diffs = {}
    if isinstance(expected, dict) and isinstance(actual, dict):
        for k in expected:
            p = f"{_path}.{k}" if _path else k
            if k not in actual:
                diffs[p] = (expected[k], "<缺失>")
            else:
                diffs.update(dict_diff(expected[k], actual[k], p))
    elif expected != actual:
        diffs[_path or "."] = (expected, actual)
    return diffs
