"""BOSS 手工登录和登录态保存 Page Object。"""

from pathlib import Path
from time import monotonic

import allure
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

from pages.base_page import BasePage


class BossLoginPage(BasePage):
    """封装 BOSS 登录入口、登录完成判断和 storage_state 保存。"""

    HOME_PATH = "/mcd-boss/home"
    AUTH_COOKIE_NAME = "authorization"

    @property
    def home_url(self) -> str:
        return f"{self.base_url}{self.HOME_PATH}"

    @allure.step("打开 BOSS 登录入口")
    def open_login(self) -> None:
        self.page.goto(self.home_url, wait_until="domcontentloaded")

    @allure.step("等待用户完成 BOSS 手工登录")
    def wait_for_manual_login(self, timeout_ms: int = 300_000) -> None:
        """只判断认证 Cookie 名称，不读取或打印账号、密码和 Cookie 值。"""
        deadline = monotonic() + timeout_ms / 1_000
        while monotonic() < deadline:
            cookie_names = {
                cookie["name"].lower() for cookie in self.page.context.cookies(self.base_url)
            }
            if self.AUTH_COOKIE_NAME in cookie_names:
                break
            self.page.wait_for_timeout(1_000)
        else:
            raise PlaywrightTimeoutError("等待 BOSS 认证 Cookie 超时")

        self.page.wait_for_url(f"{self.home_url}**", timeout=60_000)
        self.page.wait_for_load_state("domcontentloaded")
        expect(self.page.get_by_role("tab", name="首页", exact=True)).to_be_visible(timeout=60_000)

    @allure.step("保存 BOSS 登录态")
    def save_storage_state(self, path: str | Path) -> Path:
        state_path = Path(path)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        self.page.context.storage_state(path=str(state_path))
        return state_path
