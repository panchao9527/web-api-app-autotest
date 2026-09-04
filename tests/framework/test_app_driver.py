"""Appium Server 生命周期辅助函数的离线测试。"""

import pytest

from core.app_driver import build_appium_service_args


def test_build_appium_service_args_keeps_base_path_and_log(tmp_path):
    log_file = tmp_path / "appium.log"

    arguments = build_appium_service_args("http://127.0.0.1:4725/wd/hub", log_file)

    assert arguments[:4] == ["--address", "127.0.0.1", "--port", "4725"]
    assert arguments[arguments.index("--base-path") + 1] == "/wd/hub"
    assert arguments[arguments.index("--log") + 1] == str(log_file)
    assert "--log-timestamp" in arguments


def test_managed_appium_rejects_remote_server():
    with pytest.raises(ValueError, match="仅支持本机"):
        build_appium_service_args("https://grid.example.com:4723")
