"""
HTTP 客户端封装 (基于 requests.Session)
- 统一 base_url、超时、请求头、鉴权
- 自动记录请求/响应日志，并附加到 Allure 报告
- 所有 API 业务类都基于它，便于统一维护
"""
import json

import allure
import requests

from config.settings import settings
from utils.logger import log


class HttpClient:
    def __init__(self, base_url: str = None, token: str = None):
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.session = requests.Session()
        self.timeout = settings.timeout

        # 默认请求头
        self.session.headers.update({"Content-Type": "application/json"})
        token = token or settings.api_token
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def set_token(self, token: str):
        """登录后回填 token"""
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)

        # 记录请求
        log.info(f"➡️  {method.upper()} {url}")
        if kwargs.get("params"):
            log.debug(f"   params: {kwargs['params']}")
        if kwargs.get("json"):
            log.debug(f"   body: {kwargs['json']}")

        resp = self.session.request(method, url, **kwargs)

        # 记录响应
        log.info(f"⬅️  {resp.status_code} | 耗时 {resp.elapsed.total_seconds():.2f}s")
        # 全局开关：是否打印返回报文(config.yaml 的 log_response)
        if settings.log_response:
            body = resp.text or ""
            max_len = settings.log_response_max
            if len(body) > max_len:
                body = body[:max_len] + f"...(共{len(resp.text)}字符,已截断)"
            log.info(f"   响应: {body}")
        self._attach_to_allure(method, url, kwargs, resp)
        return resp

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

    @staticmethod
    def _attach_to_allure(method, url, kwargs, resp):
        """把请求/响应详情附加到 Allure，失败时方便排查"""
        try:
            detail = {
                "request": {
                    "method": method.upper(),
                    "url": url,
                    "params": kwargs.get("params"),
                    "body": kwargs.get("json"),
                },
                "response": {
                    "status_code": resp.status_code,
                    "body": resp.json() if "application/json"
                    in resp.headers.get("Content-Type", "") else resp.text[:500],
                },
            }
            allure.attach(
                json.dumps(detail, ensure_ascii=False, indent=2),
                name=f"{method.upper()} {url}",
                attachment_type=allure.attachment_type.JSON,
            )
        except Exception as e:  # noqa
            log.warning(f"Allure 附加失败: {e}")
