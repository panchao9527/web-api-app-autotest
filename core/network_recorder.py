"""
网络请求录制器（Playwright）
- 跑 UI 业务流时，自动捕获页面调用的接口序列（方法/URL/状态码/请求体）
- 用途：把"UI 流程背后的接口序列"导出，据此编写【接口场景级用例】
- 用法:
    def test_flow(page, network_recorder):   # network_recorder 见 conftest
        LoginPage(page).login("user", "pwd")
        # ...继续 UI 操作...
        network_recorder.print_summary()       # 打印接口调用序列
        network_recorder.save("captured_apis.json")
"""

import json

from utils.logger import log
from utils.redaction import redact, redact_text, redact_url


def _safe_body(body):
    """优先按 JSON 脱敏，非 JSON 文本使用通用键值脱敏。"""
    if body is None:
        return None
    try:
        parsed = json.loads(body)
    except (TypeError, ValueError):
        return redact_text(str(body))
    return json.dumps(redact(parsed), ensure_ascii=False)


class NetworkRecorder:
    def __init__(self, page, url_keyword: str = "/api", capture_body: bool = False):
        """
        :param page: Playwright page 对象
        :param url_keyword: 只记录 URL 含该关键字的请求(默认 /api，过滤掉静态资源)
        :param capture_body: 是否抓响应体(默认 False，避免大响应/异常)
        """
        self.page = page
        self.url_keyword = url_keyword
        self.capture_body = capture_body
        self.calls: list[dict] = []
        page.on("response", self._on_response)

    def _on_response(self, response):
        try:
            req = response.request
            if self.url_keyword and self.url_keyword not in req.url:
                return
            record = {
                "method": req.method,
                "url": redact_url(req.url),
                "status": response.status,
                "request_body": _safe_body(req.post_data),
            }
            if self.capture_body:
                try:
                    record["response_body"] = _safe_body(response.text())[:1000]
                except Exception:  # noqa
                    record["response_body"] = None
            self.calls.append(record)
        except Exception as e:  # noqa
            log.warning(f"录制网络请求失败: {e}")

    def print_summary(self):
        """在日志里打印捕获到的接口调用序列"""
        log.info(f"===== 捕获到 {len(self.calls)} 个接口调用 =====")
        for i, c in enumerate(self.calls, 1):
            log.info(f"  {i}. {c['method']:6} {c['status']} {c['url']}")

    def save(self, filename: str = "captured_apis.json") -> list[dict]:
        """把接口序列保存成 json，方便据此写接口场景用例"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.calls, f, ensure_ascii=False, indent=2)
        log.info(f"接口调用序列已保存: {filename}（共 {len(self.calls)} 条）")
        return self.calls

    def clear(self):
        """清空已记录(分段录制时用)"""
        self.calls.clear()
