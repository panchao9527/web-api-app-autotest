from pathlib import Path

import pytest

from config.settings import Settings


def write_config(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_settings_rejects_non_http_url(tmp_path):
    config = write_config(
        tmp_path / "config.yaml",
        "common: {timeout: 30}\nuat: {api_base_url: 'bad', web_base_url: 'https://web.example'}\n",
    )

    with pytest.raises(ValueError, match="api_base_url"):
        Settings(config_file=config, env="uat", load_env_file=False)


def test_explicit_environment_overrides_environment_variable(monkeypatch, tmp_path):
    monkeypatch.setenv("ENV", "sit")
    config = write_config(
        tmp_path / "config.yaml",
        "common: {}\n"
        "sit: {api_base_url: 'https://sit.example', web_base_url: 'https://sit-web.example'}\n"
        "uat: {api_base_url: 'https://uat.example', web_base_url: 'https://uat-web.example'}\n",
    )

    loaded = Settings(config_file=config, env="uat", load_env_file=False)

    assert loaded.env == "uat"
    assert loaded.api_base_url == "https://uat.example"


def test_settings_rejects_non_positive_timeout(tmp_path):
    config = write_config(
        tmp_path / "config.yaml",
        "common: {timeout: 0}\n"
        "uat: {api_base_url: 'https://api.example', web_base_url: 'https://web.example'}\n",
    )

    with pytest.raises(ValueError, match="timeout"):
        Settings(config_file=config, env="uat", load_env_file=False)


def test_app_environment_overrides_select_real_device(monkeypatch, tmp_path):
    apk = tmp_path / "demo.apk"
    apk.touch()
    monkeypatch.setenv("APP_PATH", str(apk))
    monkeypatch.setenv("APPIUM_UDID", "device-001")
    monkeypatch.setenv("APPIUM_SERVER", "http://localhost:4725/")
    monkeypatch.setenv("APPIUM_MANAGE_SERVER", "false")
    config = write_config(
        tmp_path / "config.yaml",
        "common: {}\n"
        "uat: {api_base_url: 'https://api.example', web_base_url: 'https://web.example'}\n"
        "app:\n"
        "  platform: Android\n"
        "  manage_server: true\n"
        "  android: {platformName: Android, automationName: UiAutomator2, avd: Demo_AVD}\n",
    )

    loaded = Settings(config_file=config, env="uat", load_env_file=False)

    assert loaded.app["appium_server"] == "http://localhost:4725"
    assert loaded.app["manage_server"] is False
    assert loaded.app_caps()["app"] == str(apk.absolute())
    assert loaded.app_caps()["udid"] == "device-001"
    assert "avd" not in loaded.app_caps()


def test_app_caps_omit_empty_values(monkeypatch, tmp_path):
    for name in (
        "APP_PATH",
        "APPIUM_AVD",
        "APPIUM_UDID",
        "APP_PACKAGE",
        "APP_ACTIVITY",
        "APPIUM_PLATFORM_VERSION",
    ):
        monkeypatch.delenv(name, raising=False)
    config = write_config(
        tmp_path / "config.yaml",
        "common: {}\n"
        "uat: {api_base_url: 'https://api.example', web_base_url: 'https://web.example'}\n"
        "app:\n"
        "  platform: Android\n"
        "  android: {platformName: Android, app: '', appPackage: null, noReset: false}\n",
    )

    caps = Settings(config_file=config, env="uat", load_env_file=False).app_caps()

    assert caps == {"platformName": "Android", "noReset": False}
