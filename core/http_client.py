"""统一 HTTP 客户端，提供日志、报告、脱敏和资源管理。"""

import json
from urllib.parse import urlsplit, urlunsplit

import allure
import requests

from config.settings import settings
from core.safety import ensure_http_request_allowed
from utils.logger import log
from utils.redaction import redact, redact_text, redact_url


class HttpClient:
    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        session: requests.Session | None = None,
        timeout: float | None = None,
    ):
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout if timeout is not None else settings.timeout
        # None 沿用环境配置；空字符串明确表示匿名，不能回退到 API_TOKEN。
        selected_token = settings.api_token if token is None else token
        if selected_token:
            self.set_token(selected_token)
        elif token == "":
            self.session.headers.pop("Authorization", None)
            self.session.auth = None
            if hasattr(self.session, "cookies"):
                self.session.cookies.clear()

    def set_token(self, token: str) -> None:
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _build_url(self, path: str) -> str:
        parsed = urlsplit(path)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return path
        base = urlsplit(self.base_url)
        base_path = base.path.rstrip("/")
        relative_path = parsed.path.lstrip("/")
        joined_path = "/".join(part for part in (base_path, relative_path) if part)
        if not joined_path.startswith("/"):
            joined_path = f"/{joined_path}"
        return urlunsplit((base.scheme, base.netloc, joined_path, parsed.query, parsed.fragment))

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = self._build_url(path)
        ensure_http_request_allowed(settings.env, method, url, self.base_url)
        kwargs.setdefault("timeout", self.timeout)
        safe_url = redact_url(url)
        safe_request = self._request_detail(method, url, kwargs)

        log.info(f"HTTP 请求 | {method.upper()} {safe_url}")
        if kwargs.get("params"):
            log.debug(f"请求参数: {redact(kwargs['params'])}")
        if kwargs.get("json") is not None:
            log.debug(f"请求体: {redact(kwargs['json'])}")

        try:
            response = self.session.request(method, url, **kwargs)
        except requests.RequestException as exc:
            detail = {"request": safe_request, "error": redact_text(str(exc))}
            self._attach_json(detail, f"{method.upper()} {safe_url} 请求异常")
            log.error(f"HTTP 请求异常 | {method.upper()} {safe_url} | {redact_text(str(exc))}")
            raise

        safe_body = self._response_body(response)
        log.info(
            f"HTTP 响应 | {response.status_code} | 耗时 {response.elapsed.total_seconds():.2f}s"
        )
        if settings.log_response:
            log.info(f"响应: {self._limit_text(self._display_text(safe_body))}")
        self._attach_json(
            {
                "request": safe_request,
                "response": {
                    "status_code": response.status_code,
                    "body": self._limit_value(safe_body),
                },
            },
            f"{method.upper()} {safe_url}",
        )
        return response

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def patch(self, path, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _request_detail(self, method: str, url: str, kwargs: dict) -> dict:
        headers = dict(getattr(self.session, "headers", {}))
        headers.update(kwargs.get("headers") or {})
        return {
            "method": method.upper(),
            "url": redact_url(url),
            "headers": redact(headers),
            "params": redact(kwargs.get("params")),
            "body": redact(kwargs.get("json", kwargs.get("data"))),
        }

    @staticmethod
    def _response_body(response):
        content_type = response.headers.get("Content-Type", "").lower()
        if "application/json" in content_type:
            try:
                return redact(response.json())
            except ValueError:
                pass
        return redact_text(response.text or "")

    @staticmethod
    def _display_text(value) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _limit_text(text: str) -> str:
        maximum = max(int(settings.log_response_max), 1)
        if len(text) <= maximum:
            return text
        return f"{text[:maximum]}...(共{len(text)}字符，已截断)"

    @classmethod
    def _limit_value(cls, value):
        text = cls._display_text(value)
        return value if len(text) <= int(settings.log_response_max) else cls._limit_text(text)

    @staticmethod
    def _attach_json(detail: dict, name: str) -> None:
        try:
            allure.attach(
                json.dumps(detail, ensure_ascii=False, indent=2),
                name=name,
                attachment_type=allure.attachment_type.JSON,
            )
        except Exception as exc:
            log.warning(f"Allure 附加失败: {redact_text(str(exc))}")
