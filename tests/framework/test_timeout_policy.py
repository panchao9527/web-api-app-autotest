"""验证 API、Web、App 的用例级超时策略。"""

import pytest

from conftest import _apply_default_timeouts


class FakeItem:
    """只实现超时策略所需的最小 pytest Item 接口。"""

    def __init__(self, *markers: str):
        self.markers = set(markers)
        self.added_markers = []

    def get_closest_marker(self, name: str):
        return object() if name in self.markers else None

    def add_marker(self, marker) -> None:
        self.added_markers.append(marker)


def test_timeout_plugin_and_global_fallback_are_enabled(pytestconfig):
    """依赖未安装或 pytest.ini 兜底值被误删时立即失败。"""
    assert pytestconfig.pluginmanager.hasplugin("timeout")
    assert float(pytestconfig.getini("timeout")) == 300


@pytest.mark.parametrize(
    ("markers", "expected_seconds"),
    [
        (("api",), 60),
        (("web",), 180),
        (("app",), 300),
        (("api", "web"), 180),
        (("api", "app"), 300),
    ],
)
def test_default_timeout_matches_test_type(markers, expected_seconds):
    item = FakeItem(*markers)

    _apply_default_timeouts([item])

    assert len(item.added_markers) == 1
    assert item.added_markers[0].mark.name == "timeout"
    assert item.added_markers[0].mark.args == (expected_seconds,)


def test_explicit_timeout_is_not_overwritten():
    item = FakeItem("api", "timeout")

    _apply_default_timeouts([item])

    assert item.added_markers == []


def test_untyped_framework_test_uses_pytest_ini_fallback():
    item = FakeItem()

    _apply_default_timeouts([item])

    assert item.added_markers == []
