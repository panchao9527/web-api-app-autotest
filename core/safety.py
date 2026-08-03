"""生产环境测试的强制保护规则。"""

import os
from urllib.parse import urlsplit

import pytest

PROD_READ_ONLY_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def is_production_authorized(env: str, allow_prod_flag: bool) -> bool:
    """只有命令行标志和严格环境变量同时满足时才授权生产测试。"""
    if env.lower() != "prod":
        return True
    return allow_prod_flag and os.getenv("ALLOW_PROD_TESTS") == "1"


def ensure_environment_allowed(env: str, allow_prod_flag: bool) -> None:
    """阻止未经双重授权的生产环境测试。"""
    if env.lower() == "prod" and not is_production_authorized(env, allow_prod_flag):
        raise pytest.UsageError(
            "生产环境测试默认禁止。确需执行只读用例时，必须同时传入 "
            "--allow-prod 并设置 ALLOW_PROD_TESTS=1；框架随后只收集 prod_safe 用例。"
        )


def ensure_write_allowed(env: str, operation: str) -> None:
    """生产环境禁止使用框架提供的数据写入和清理能力。"""
    if env.lower() == "prod":
        raise pytest.UsageError(f"生产环境禁止执行写操作: {operation}。请改用只读 prod_safe 用例。")


def _origin(url: str) -> tuple[str, str, int | None]:
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    default_port = 443 if scheme == "https" else 80 if scheme == "http" else None
    return scheme, (parsed.hostname or "").lower(), parsed.port or default_port


def ensure_http_request_allowed(env: str, method: str, url: str, base_url: str) -> None:
    """生产环境仅允许向已配置 API 同源地址发送只读 HTTP 请求。"""
    if env.lower() != "prod":
        return
    normalized_method = method.upper()
    if normalized_method not in PROD_READ_ONLY_METHODS:
        raise pytest.UsageError(f"生产环境仅允许只读 HTTP 请求，已阻止 {normalized_method} {url}。")
    if _origin(url) != _origin(base_url):
        raise pytest.UsageError(f"生产环境禁止跨域请求，目标 {url} 与配置地址 {base_url} 不同源。")
