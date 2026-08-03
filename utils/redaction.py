"""日志和报告使用的强制敏感数据脱敏。"""

import re
from collections.abc import Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

MASK = "***"
SENSITIVE_KEYS = frozenset(
    {
        "password",
        "passwd",
        "pwd",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "secret",
        "mobile",
        "phone",
        "id_card",
        "passcode",
        "otp",
    }
)


def _normalized_keys(sensitive_keys) -> frozenset[str]:
    return frozenset(str(key).lower() for key in sensitive_keys)


def is_sensitive_field(field: str, sensitive_keys=SENSITIVE_KEYS) -> bool:
    """根据字段名、定位器或标签判断输入内容是否应隐藏。"""
    normalized = re.sub(r"[^a-z0-9]+", "_", str(field).lower())
    return any(key in normalized for key in _normalized_keys(sensitive_keys))


def safe_input_value(value, field: str = "", sensitive: bool = False) -> str:
    """返回可安全写入日志的输入值，不改变真正发送给页面或设备的值。"""
    if sensitive or is_sensitive_field(field):
        return MASK
    return redact_text(str(value))


def redact(value, sensitive_keys=SENSITIVE_KEYS):
    """递归复制数据并隐藏敏感键对应的值。"""
    keys = _normalized_keys(sensitive_keys)
    if isinstance(value, Mapping):
        return {
            key: MASK if str(key).lower() in keys else redact(item, keys)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item, keys) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item, keys) for item in value)
    if isinstance(value, set):
        return {redact(item, keys) for item in value}
    if isinstance(value, str):
        return redact_text(value, keys)
    return value


def redact_url(url: str, sensitive_keys=SENSITIVE_KEYS) -> str:
    """隐藏 URL 查询参数中的敏感值。"""
    keys = _normalized_keys(sensitive_keys)
    parts = urlsplit(url)
    query = [
        (key, MASK if key.lower() in keys else value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def redact_text(text: str, sensitive_keys=SENSITIVE_KEYS) -> str:
    """隐藏文本中常见的 key=value 和 key: value 形式。"""
    keys = sorted(_normalized_keys(sensitive_keys), key=len, reverse=True)
    if not keys:
        return text
    alternation = "|".join(re.escape(key) for key in keys)
    quoted = re.compile(rf"(?i)\b({alternation})\b(\s*[:=]\s*)(['\"])(.*?)\3")
    unquoted = re.compile(rf"(?i)\b({alternation})\b(\s*[:=]\s*)([^\s,;&}}]+)")
    result = quoted.sub(lambda match: f"{match.group(1)}{match.group(2)}{MASK}", text)
    return unquoted.sub(lambda match: f"{match.group(1)}{match.group(2)}{MASK}", result)
