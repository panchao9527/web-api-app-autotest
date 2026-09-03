"""BOSS Web 用例专用的登录态配置。"""

from pathlib import Path

import pytest

from config.settings import settings


def _storage_state_path() -> Path:
    configured = settings.boss["storage_state"]
    path = Path(configured)
    return path if path.is_absolute() else settings.root_dir / path


@pytest.fixture
def browser_context_args(browser_context_args):
    """仅为 BOSS 用例加载手工登录态，不影响其他 Web 项目。"""
    storage_state = _storage_state_path()
    if not storage_state.is_file():
        pytest.skip(
            "缺少当前环境的 BOSS 登录态。请先运行: "
            f"python scripts/capture_boss_auth.py --env {settings.env}"
        )
    return {
        **browser_context_args,
        "base_url": settings.web_base_url,
        "storage_state": str(storage_state),
    }
