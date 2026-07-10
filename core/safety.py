"""生产环境测试的强制保护规则。"""

import os

import pytest


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
