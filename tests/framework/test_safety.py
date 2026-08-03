import pytest

from core.safety import (
    ensure_environment_allowed,
    ensure_http_request_allowed,
    ensure_write_allowed,
    is_production_authorized,
)


def test_prod_is_blocked_by_default(monkeypatch):
    monkeypatch.delenv("ALLOW_PROD_TESTS", raising=False)

    with pytest.raises(pytest.UsageError, match="生产环境"):
        ensure_environment_allowed("prod", allow_prod_flag=False)


def test_prod_requires_flag_and_environment_variable(monkeypatch):
    monkeypatch.setenv("ALLOW_PROD_TESTS", "1")

    ensure_environment_allowed("prod", allow_prod_flag=True)
    assert is_production_authorized("prod", allow_prod_flag=True) is True


@pytest.mark.parametrize(
    ("flag", "env_value"),
    [(True, ""), (False, "1"), (True, "true")],
)
def test_prod_rejects_incomplete_or_invalid_authorization(monkeypatch, flag, env_value):
    monkeypatch.setenv("ALLOW_PROD_TESTS", env_value)

    with pytest.raises(pytest.UsageError, match="--allow-prod"):
        ensure_environment_allowed("prod", allow_prod_flag=flag)


def test_non_prod_environment_needs_no_authorization(monkeypatch):
    monkeypatch.delenv("ALLOW_PROD_TESTS", raising=False)

    ensure_environment_allowed("uat", allow_prod_flag=False)


def test_write_helpers_are_forbidden_in_prod():
    with pytest.raises(pytest.UsageError, match="写操作"):
        ensure_write_allowed("prod", "clean_data")


def test_prod_http_only_allows_read_requests_to_configured_origin():
    ensure_http_request_allowed(
        "prod",
        "GET",
        "https://api.example.com:443/users?page=1",
        "https://api.example.com",
    )

    with pytest.raises(pytest.UsageError, match="只读"):
        ensure_http_request_allowed(
            "prod", "POST", "https://api.example.com/users", "https://api.example.com"
        )

    with pytest.raises(pytest.UsageError, match="跨域"):
        ensure_http_request_allowed(
            "prod", "GET", "https://other.example.com/users", "https://api.example.com"
        )


def test_direct_db_and_redis_writes_are_also_blocked_in_prod(monkeypatch):
    from clients.db_client import DBClient
    from clients.redis_client import RedisClient

    monkeypatch.setattr("clients.db_client.settings.env", "prod")
    monkeypatch.setattr("clients.redis_client.settings.env", "prod")

    with pytest.raises(pytest.UsageError, match="写操作"):
        DBClient.__new__(DBClient).execute("DELETE FROM users")
    with pytest.raises(pytest.UsageError, match="写操作"):
        RedisClient.__new__(RedisClient).set("key", "value")
