"""BOSS Web 用例专用的登录态配置。"""

import json
import os
from pathlib import Path

import pytest

from config.settings import settings


def _storage_state_path() -> Path:
    configured = settings.boss["storage_state"]
    path = Path(configured)
    return path if path.is_absolute() else settings.root_dir / path


@pytest.fixture
def browser_context_args(browser_context_args, request):
    """仅为 BOSS 用例加载手工登录态，不影响其他 Web 项目。"""
    # CI 从 Secret 注入，不把登录态写入仓库、报告或临时文件。
    state_json = os.getenv("BOSS_STORAGE_STATE_JSON")
    if state_json:
        try:
            state = json.loads(state_json)
        except ValueError:
            pytest.fail("BOSS_STORAGE_STATE_JSON 不是合法 JSON，请更新 CI Secret", pytrace=False)
        if not isinstance(state, dict) or not all(
            isinstance(state.get(key), list) for key in ("cookies", "origins")
        ):
            pytest.fail("BOSS_STORAGE_STATE_JSON 必须包含 cookies/origins 数组", pytrace=False)
        return {**browser_context_args, "base_url": settings.web_base_url, "storage_state": state}
    storage_state = _storage_state_path()
    if not storage_state.is_file():
        message = (
            "缺少当前环境的 BOSS 登录态。请先运行: "
            f"python scripts/capture_boss_auth.py --env {settings.env}"
        )
        if request.config.getoption("--require-executed"):
            pytest.fail(message, pytrace=False)
        pytest.skip(message)
    return {
        **browser_context_args,
        "base_url": settings.web_base_url,
        "storage_state": str(storage_state),
    }
