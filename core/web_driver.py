"""
Playwright 启动参数辅助
- pytest-playwright 已内置 page/browser fixture，
  这里集中提供启动参数(headless/viewport/slow_mo)，由 conftest 注入。
- 也可用于非 pytest-playwright 场景手动启动浏览器。
"""
from playwright.sync_api import sync_playwright

from config.settings import settings
from utils.logger import log


def browser_launch_args() -> dict:
    """供 pytest-playwright 的 browser_type_launch_args fixture 使用"""
    web = settings.web
    return {
        "headless": web.get("headless", True),
        "slow_mo": web.get("slow_mo", 0),
    }


def browser_context_args() -> dict:
    """供 pytest-playwright 的 browser_context_args fixture 使用"""
    web = settings.web
    vp = web.get("viewport", {"width": 1920, "height": 1080})
    return {
        "viewport": {"width": vp["width"], "height": vp["height"]},
        "base_url": settings.web_base_url,
    }


class WebBrowser:
    """手动启动浏览器的上下文管理器(脱离 pytest 时使用)"""

    def __enter__(self):
        web = settings.web
        self._pw = sync_playwright().start()
        browser_type = getattr(self._pw, web.get("browser", "chromium"))
        self.browser = browser_type.launch(**browser_launch_args())
        self.context = self.browser.new_context(**browser_context_args())
        self.page = self.context.new_page()
        log.info(f"启动浏览器 | {web.get('browser')} | headless={web.get('headless')}")
        return self.page

    def __exit__(self, *args):
        self.context.close()
        self.browser.close()
        self._pw.stop()
