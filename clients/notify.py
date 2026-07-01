"""
消息通知客户端（钉钉 / 企业微信 机器人）
- 典型用途：CI 跑完把测试报告摘要推送到群里
- 只依赖 requests（核心依赖，无需额外安装）
- webhook 地址含密钥，放 .env 的 DINGTALK_WEBHOOK / WECOM_WEBHOOK

用法:
    from clients.notify import Notifier

    n = Notifier()
    n.dingtalk_text("冒烟测试通过 ✅")
    n.wecom_markdown("## 测试报告\n- 通过: 50\n- 失败: 2")
    n.send_test_result(total=52, passed=50, failed=2, duration="3m20s",
                       report_url="https://...")
"""
import base64
import hashlib
import hmac
import time
import urllib.parse

import requests

from config.settings import settings
from utils.logger import log

TIMEOUT = 10


class Notifier:
    def __init__(self, dingtalk_webhook: str = None, wecom_webhook: str = None,
                 dingtalk_secret: str = None):
        notify = settings.notify
        self.dingtalk_webhook = dingtalk_webhook or notify.get("dingtalk_webhook", "")
        self.wecom_webhook = wecom_webhook or notify.get("wecom_webhook", "")
        # 钉钉"加签"安全设置的密钥(SEC开头)；配了就自动算签名，没配走关键词模式
        self.dingtalk_secret = dingtalk_secret or notify.get("dingtalk_secret", "")

    def _dingtalk_url(self) -> str:
        """钉钉 webhook：若配了加签密钥，自动追加 timestamp + sign"""
        if not self.dingtalk_secret:
            return self.dingtalk_webhook   # 未加签(用自定义关键词模式)
        ts = str(round(time.time() * 1000))
        string_to_sign = f"{ts}\n{self.dingtalk_secret}"
        hmac_code = hmac.new(
            self.dingtalk_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        sep = "&" if "?" in self.dingtalk_webhook else "?"
        return f"{self.dingtalk_webhook}{sep}timestamp={ts}&sign={sign}"

    # ---------------- 钉钉 ----------------
    def dingtalk_text(self, content: str):
        if not self.dingtalk_webhook:
            log.warning("未配置钉钉 webhook，跳过通知")
            return
        payload = {"msgtype": "text", "text": {"content": content}}
        return self._post(self._dingtalk_url(), payload, "钉钉")

    def dingtalk_markdown(self, title: str, text: str):
        if not self.dingtalk_webhook:
            log.warning("未配置钉钉 webhook，跳过通知")
            return
        payload = {"msgtype": "markdown", "markdown": {"title": title, "text": text}}
        return self._post(self._dingtalk_url(), payload, "钉钉")

    # ---------------- 企业微信 ----------------
    def wecom_text(self, content: str):
        if not self.wecom_webhook:
            log.warning("未配置企微 webhook，跳过通知")
            return
        payload = {"msgtype": "text", "text": {"content": content}}
        return self._post(self.wecom_webhook, payload, "企微")

    def wecom_markdown(self, content: str):
        if not self.wecom_webhook:
            log.warning("未配置企微 webhook，跳过通知")
            return
        payload = {"msgtype": "markdown", "markdown": {"content": content}}
        return self._post(self.wecom_webhook, payload, "企微")

    # ---------------- 高层封装：推送测试结果摘要 ----------------
    def send_test_result(self, total: int, passed: int, failed: int,
                         duration: str = "", report_url: str = "",
                         title: str = "自动化测试报告"):
        """构造一份测试结果摘要，同时推送到已配置的钉钉/企微"""
        pass_rate = f"{(passed / total * 100):.1f}%" if total else "N/A"
        emoji = "✅" if failed == 0 else "⚠️"
        md = (
            f"## {emoji} {title}\n"
            f"- 环境：{settings.env}\n"
            f"- 总计：**{total}**　通过：**{passed}**　失败：**{failed}**\n"
            f"- 通过率：**{pass_rate}**\n"
            f"- 耗时：{duration or '-'}\n"
        )
        if report_url:
            md += f"- [查看完整报告]({report_url})\n"

        if self.dingtalk_webhook:
            self.dingtalk_markdown(title, md)
        if self.wecom_webhook:
            self.wecom_markdown(md)
        if not (self.dingtalk_webhook or self.wecom_webhook):
            log.warning("钉钉/企微 webhook 都未配置，未发送测试结果")

    # ---------------- 内部 ----------------
    @staticmethod
    def _post(webhook: str, payload: dict, name: str):
        try:
            resp = requests.post(webhook, json=payload, timeout=TIMEOUT)
            ok = resp.status_code == 200 and resp.json().get("errcode", 0) == 0
            log.info(f"{name}通知发送{'成功' if ok else '失败'} | {resp.text[:200]}")
            return resp
        except Exception as e:  # noqa
            log.error(f"{name}通知异常: {e}")
            return None
