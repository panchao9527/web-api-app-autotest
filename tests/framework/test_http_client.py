import json
from datetime import timedelta

import pytest
import requests

from core.http_client import HttpClient


class FakeResponse:
    status_code = 200
    text = '{"token": "response-secret", "name": "tester"}'
    headers = {"Content-Type": "application/json"}
    elapsed = timedelta(milliseconds=25)

    def json(self):
        return {"token": "response-secret", "name": "tester"}


class FakeSession:
    def __init__(self, error=None):
        self.headers = {}
        self.closed = False
        self.calls = []
        self.error = error

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if self.error:
            raise self.error
        return FakeResponse()

    def close(self):
        self.closed = True


def test_client_joins_relative_paths_and_closes():
    session = FakeSession()
    client = HttpClient(base_url="https://api.example/root/", session=session, timeout=9)

    client.get("users")

    assert session.calls[0][1] == "https://api.example/root/users"
    assert session.calls[0][2]["timeout"] == 9
    client.close()
    assert session.closed is True


def test_client_keeps_absolute_url():
    session = FakeSession()
    client = HttpClient(base_url="https://api.example", session=session)

    client.get("https://other.example/health")

    assert session.calls[0][1] == "https://other.example/health"


def test_request_details_are_redacted(monkeypatch):
    attached = []
    monkeypatch.setattr("allure.attach", lambda body, **kwargs: attached.append(json.loads(body)))
    client = HttpClient(base_url="https://api.example", session=FakeSession())

    client.post(
        "/login?token=query-secret",
        headers={"Authorization": "Bearer header-secret"},
        json={"password": "plain-password"},
    )

    serialized = json.dumps(attached, ensure_ascii=False)
    assert "plain-password" not in serialized
    assert "query-secret" not in serialized
    assert "header-secret" not in serialized
    assert "response-secret" not in serialized
    assert "***" in serialized


def test_request_exception_is_attached_and_reraised(monkeypatch):
    attached = []
    monkeypatch.setattr("allure.attach", lambda body, **kwargs: attached.append(body))
    error = requests.ConnectionError("connection failed")
    client = HttpClient(base_url="https://api.example", session=FakeSession(error=error))

    try:
        client.get("/users", params={"token": "query-secret"})
    except requests.ConnectionError as exc:
        assert exc is error
    else:
        raise AssertionError("请求异常必须继续抛给用例")

    assert attached
    assert "query-secret" not in attached[0]


def test_prod_client_blocks_write_and_cross_origin_requests(monkeypatch):
    monkeypatch.setattr("core.http_client.settings.env", "prod")
    session = FakeSession()
    client = HttpClient(base_url="https://api.example.com", session=session)

    with pytest.raises(pytest.UsageError, match="只读"):
        client.post("/users", json={"name": "tester"})
    with pytest.raises(pytest.UsageError, match="跨域"):
        client.get("https://other.example.com/users")

    assert session.calls == []


@pytest.mark.parametrize(
    "token, expected", [(None, "Bearer configured"), ("", None), ("role", "Bearer role")]
)
def test_explicit_anonymous_token_does_not_fall_back_to_environment(monkeypatch, token, expected):
    monkeypatch.setattr("core.http_client.settings.api_token", "configured")
    session = requests.Session()
    session.headers["Authorization"] = "Bearer previous"
    session.auth = ("old-user", "old-password")
    session.cookies.set("session", "old-cookie")
    with HttpClient(session=session, token=token):
        assert session.headers.get("Authorization") == expected
        if token == "":
            assert session.auth is None
            assert not session.cookies
