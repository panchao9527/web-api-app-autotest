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
