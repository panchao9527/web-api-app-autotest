"""
Page Object 基类 (Playwright)
- 封装通用页面操作：打开、点击、输入、获取文本、等待
- 子页面只声明定位器 + 业务方法，不重复写底层操作
- 优先用 data-testid / role 等稳定定位，避免脆弱的绝对 xpath
"""
import allure
from playwright.sync_api import Page, expect

from config.settings import settings
from utils.logger import log


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = settings.web_base_url

    @allure.step("打开页面: {path}")
    def open(self, path: str = ""):
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        log.info(f"打开页面: {url}")
        self.page.goto(url)

    @allure.step("点击: {selector}")
    def click(self, selector: str):
        log.info(f"点击: {selector}")
        self.page.click(selector)

    @allure.step("输入 [{text}] 到 {selector}")
    def fill(self, selector: str, text: str):
        log.info(f"输入: {selector} <- {text}")
        self.page.fill(selector, text)

    def text(self, selector: str) -> str:
        return self.page.text_content(selector)

    def is_visible(self, selector: str) -> bool:
        return self.page.is_visible(selector)

    @allure.step("断言元素可见: {selector}")
    def expect_visible(self, selector: str):
        """Playwright 自带智能等待，无需手动 sleep"""
        expect(self.page.locator(selector)).to_be_visible()

    @allure.step("断言文本包含: {expected}")
    def expect_text(self, selector: str, expected: str):
        expect(self.page.locator(selector)).to_contain_text(expected)
