"""Appium Server 生命周期辅助函数的离线测试。"""

from unittest.mock import Mock

import pytest

from core import app_driver
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


@pytest.mark.parametrize(
    "payload, ready",
    [
        (b'{"value":{"ready":true}}', True),
        (b'{"value":{"ready":"false"}}', False),
        (b'{"value":null}', False),
        (b"[]", False),
        (b"not-json", False),
    ],
)
def test_status_probe_handles_invalid_payload(monkeypatch, payload, ready):
    response = Mock(status=200)
    response.read.return_value = payload
    context = Mock()
    context.__enter__ = Mock(return_value=response)
    context.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(app_driver, "urlopen", lambda *args, **kwargs: context)
    assert app_driver.appium_server_ready("http://127.0.0.1:4723") is ready


def test_status_probe_handles_invalid_url(monkeypatch):
    monkeypatch.setattr(app_driver, "urlopen", Mock(side_effect=ValueError("invalid URL")))
    assert not app_driver.appium_server_ready("invalid")


def test_missing_local_app_is_rejected_before_server_or_session(monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_driver.settings,
        "app",
        {"platform": "Android", "appium_server": "http://127.0.0.1:4723", "manage_server": True},
    )
    monkeypatch.setattr(
        app_driver.settings, "app_caps", lambda: {"app": str(tmp_path / "missing.apk")}
    )
    server = Mock()
    remote = Mock()
    monkeypatch.setattr(app_driver, "AppiumService", server)
    monkeypatch.setattr(app_driver.webdriver, "Remote", remote)
    with pytest.raises(ValueError, match="安装包不存在"):
        app_driver.start_managed_appium_service()
    with pytest.raises(ValueError, match="安装包不存在"):
        app_driver.create_app_driver()
    server.assert_not_called()
    remote.assert_not_called()


def test_remote_app_path_is_not_checked_on_client_machine():
    app_driver.validate_app_target(
        {"platform": "Android", "appium_server": "http://device-host:4723"},
        {"app": "/server-only/company.apk"},
    )


@pytest.mark.parametrize(
    "platform, caps",
    [
        ("Android", {"appPackage": "company.app", "appActivity": ".Main"}),
        ("iOS", {"bundleId": "company.app"}),
    ],
)
def test_installed_app_target_is_supported(platform, caps):
    app_driver.validate_app_target({"platform": platform}, caps)
    with pytest.raises(ValueError, match="未指定测试 App"):
        app_driver.validate_app_target({"platform": platform}, {})
