"""三端稳定性回归：全部使用模拟对象，不访问业务服务或设备。"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from selenium.common.exceptions import NoSuchElementException, WebDriverException

import conftest as hooks
from fixtures import api_fixtures
from screens.base_screen import BaseScreen
from scripts import automation


@pytest.mark.parametrize("login_error", [None, RuntimeError("network unavailable")])
def test_login_fixture_closes_client_on_setup_failure(monkeypatch, login_error):
    client = Mock()
    api = Mock(client=client)
    api.login.side_effect = login_error
    api.login.return_value = SimpleNamespace(status_code=401)
    monkeypatch.setattr(api_fixtures, "HttpClient", lambda **kwargs: client)
    monkeypatch.setattr(api_fixtures, "UserApi", lambda **kwargs: api)
    with pytest.raises(RuntimeError):
        next(api_fixtures.logged_in_client.__wrapped__())
    client.close.assert_called_once()


@pytest.mark.parametrize("body", [{}, {"token": ""}, {"token": " "}, {"token": 42}, []])
def test_login_fixture_rejects_missing_or_invalid_token(monkeypatch, body):
    client = Mock()
    api = Mock(client=client)
    api.login.return_value = Mock(status_code=200)
    api.login.return_value.json.return_value = body
    monkeypatch.setattr(api_fixtures, "HttpClient", lambda **kwargs: client)
    monkeypatch.setattr(api_fixtures, "UserApi", lambda **kwargs: api)
    with pytest.raises(RuntimeError, match="token"):
        next(api_fixtures.logged_in_client.__wrapped__())
    client.close.assert_called_once()


def test_login_fixture_yields_and_closes_valid_client(monkeypatch):
    client = Mock()
    api = Mock(client=client)
    api.login.return_value = Mock(status_code=200)
    api.login.return_value.json.return_value = {"token": "valid"}
    monkeypatch.setattr(api_fixtures, "HttpClient", lambda **kwargs: client)
    monkeypatch.setattr(api_fixtures, "UserApi", lambda **kwargs: api)
    fixture = api_fixtures.logged_in_client.__wrapped__()
    assert next(fixture) is client
    fixture.close()
    client.close.assert_called_once()


@pytest.mark.parametrize("swipes", [0, 1, 3])
def test_scroll_checks_initial_screen_and_last_swipe(swipes):
    driver = Mock()
    driver.find_element.return_value.is_displayed.side_effect = [False] * swipes + [True]
    screen = BaseScreen(driver)
    screen.swipe_up = Mock()
    assert (
        screen.scroll_to_find("id", "target", max_swipes=swipes) is driver.find_element.return_value
    )
    assert screen.swipe_up.call_count == swipes


def test_scroll_stops_at_limit_and_device_errors_are_not_hidden():
    driver = Mock()
    driver.find_element.side_effect = NoSuchElementException()
    screen = BaseScreen(driver)
    screen.swipe_up = Mock()
    with pytest.raises(AssertionError):
        screen.scroll_to_find("id", "missing", max_swipes=2)
    assert screen.swipe_up.call_count == 2
    driver.find_element.side_effect = WebDriverException("device disconnected")
    with pytest.raises(WebDriverException):
        screen.is_displayed("id", "missing")


def test_reading_disabled_element_does_not_require_clickability():
    driver = Mock()
    element = driver.find_element.return_value
    element.is_displayed.return_value = True
    element.is_enabled.return_value = False
    element.text = "只读值"
    assert BaseScreen(driver).text("id", "readonly") == "只读值"
    element.is_enabled.assert_not_called()


@pytest.mark.parametrize(
    "create_failure, quit_failure", [(False, True), (True, False), (False, False)]
)
def test_app_smoke_always_stops_owned_server(monkeypatch, create_failure, quit_failure):
    service = Mock()
    driver = Mock()
    if quit_failure:
        driver.quit.side_effect = RuntimeError("disconnected")
    monkeypatch.setattr(automation.Settings, "reload", lambda self, env: self)
    monkeypatch.setattr("core.app_driver.start_managed_appium_service", lambda: service)
    factory = (
        Mock(side_effect=RuntimeError("create failed"))
        if create_failure
        else Mock(return_value=driver)
    )
    monkeypatch.setattr("core.app_driver.create_app_driver", factory)
    assert automation.run_app_smoke("uat") == (1 if create_failure or quit_failure else 0)
    service.stop.assert_called_once()


def test_marker_or_expression_is_grouped():
    command, _ = automation.build_pytest_command(
        test_type="api",
        environment="uat",
        marker="smoke or regression",
        headed=False,
        browser=None,
        slowmo=0,
        tracing=None,
        allow_prod=False,
    )
    assert "api and (smoke or regression)" in command


@pytest.mark.parametrize(
    "stats, original, expected",
    [
        ({"skipped": [object()]}, 0, 1),
        ({"passed": [object()]}, 0, 0),
        ({"skipped": [object()]}, 5, 5),
        ({"error": [object()]}, 1, 1),
    ],
)
def test_execution_gate_preserves_errors_and_rejects_all_skipped(stats, original, expected):
    reporter = Mock(stats=stats)
    config = SimpleNamespace(getoption=Mock(), pluginmanager=Mock())
    config.getoption.return_value = True
    gate = SimpleNamespace(executed=len(stats.get("passed", [])) + len(stats.get("failed", [])))
    config.pluginmanager.getplugin.side_effect = (
        lambda name: gate if name == "business-execution-gate" else reporter
    )
    session = SimpleNamespace(config=config, exitstatus=original)
    hooks.pytest_sessionfinish(session, original)
    assert session.exitstatus == expected


def test_report_paths_are_unique_and_explicit_path_is_preserved(monkeypatch, tmp_path):
    monkeypatch.setattr(hooks.settings, "env", "uat")
    paths = []
    for explicit in (None, None, str(tmp_path / "custom")):
        config = Mock(option=SimpleNamespace(allure_report_dir=explicit))
        config.getoption.side_effect = lambda name: "uat" if name == "--env" else False
        hooks.pytest_configure(config)
        paths.append(config.option.allure_report_dir)
    assert paths[0] != paths[1]
    assert paths[2] == str(tmp_path / "custom")


def test_app_parallel_is_rejected(monkeypatch):
    config = Mock()
    config.getoption.return_value = 2
    item = Mock()
    item.get_closest_marker.side_effect = lambda name: object() if name == "app" else None
    with pytest.raises(pytest.UsageError, match="单设备"):
        hooks.pytest_collection_modifyitems(config, [item])


def test_doctor_real_device_does_not_require_emulator(monkeypatch, tmp_path):
    java = tmp_path / "jdk" / "bin"
    java.mkdir(parents=True)
    (java / ("java.exe" if automation.sys.platform == "win32" else "java")).touch()
    monkeypatch.setenv("JAVA_HOME", str(java.parent))
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path))
    monkeypatch.setattr(
        automation.shutil, "which", lambda name: None if name == "emulator" else name
    )
    calls = []

    def output(executable, *args):
        calls.append((executable, args))
        return 0, "List of devices attached\nphone-1\tdevice\n"

    monkeypatch.setattr(automation, "_command_output", output)
    loaded = SimpleNamespace(
        app={"platform": "Android"},
        app_caps=lambda: {
            "udid": "phone-1",
            "appPackage": "company.app",
            "appActivity": ".Main",
        },
    )
    assert automation._check_app_tools(loaded)
    assert ("appium.cmd", ("driver", "doctor", "uiautomator2")) in calls


def test_doctor_ios_uses_xcuitest(monkeypatch):
    monkeypatch.setattr(automation.sys, "platform", "darwin")
    monkeypatch.setattr(automation.shutil, "which", lambda name: name)
    output = Mock(return_value=(0, "ok"))
    monkeypatch.setattr(automation, "_command_output", output)
    assert automation._check_app_tools(SimpleNamespace(app={"platform": "iOS"}))
    output.assert_called_once_with("appium.cmd", "driver", "doctor", "xcuitest")
