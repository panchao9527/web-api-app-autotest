"""
Page Object 基类 (Playwright)
- 封装通用页面操作：导航/点击/输入/选择/等待/断言/截图...
- 子页面只声明定位器 + 业务方法，不重复写底层操作
- 优先用 data-testid / role 等稳定定位；Playwright 自带智能等待，禁止写 sleep
"""
import allure
from playwright.sync_api import Page, expect

from config.settings import settings
from utils.logger import log


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = settings.web_base_url

    # ================= 导航 / 页面 =================
    @allure.step("打开页面: {path}")
    def open(self, path: str = ""):
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        log.info(f"打开页面: {url}")
        self.page.goto(url)

    @allure.step("刷新页面")
    def reload(self):
        self.page.reload()

    @allure.step("返回上一页")
    def go_back(self):
        self.page.go_back()

    def current_url(self) -> str:
        return self.page.url

    def title(self) -> str:
        return self.page.title()

    @allure.step("等待 URL 包含: {url_part}")
    def wait_for_url(self, url_part: str):
        self.page.wait_for_url(f"**{url_part}**")

    # ================= 元素操作 =================
    @allure.step("点击: {selector}")
    def click(self, selector: str):
        log.info(f"点击: {selector}")
        self.page.click(selector)

    @allure.step("双击: {selector}")
    def double_click(self, selector: str):
        self.page.dblclick(selector)

    @allure.step("输入 [{text}] 到 {selector}")
    def fill(self, selector: str, text: str):
        log.info(f"输入: {selector} <- {text}")
        self.page.fill(selector, text)

    @allure.step("逐字输入 [{text}] 到 {selector}")
    def type_text(self, selector: str, text: str, delay: int = 50):
        """模拟逐字输入(触发联想/校验等场景)"""
        self.page.type(selector, text, delay=delay)

    @allure.step("清空: {selector}")
    def clear(self, selector: str):
        self.page.fill(selector, "")

    @allure.step("悬停: {selector}")
    def hover(self, selector: str):
        self.page.hover(selector)

    @allure.step("勾选: {selector}")
    def check(self, selector: str):
        self.page.check(selector)

    @allure.step("取消勾选: {selector}")
    def uncheck(self, selector: str):
        self.page.uncheck(selector)

    @allure.step("下拉选择 {selector}: value={value} label={label}")
    def select(self, selector: str, value: str = None, label: str = None):
        """下拉框选择，按 value 或显示文本 label 二选一"""
        if label is not None:
            self.page.select_option(selector, label=label)
        else:
            self.page.select_option(selector, value=value)

    @allure.step("按键 {key} on {selector}")
    def press(self, selector: str, key: str):
        """按键，如 'Enter' / 'Escape' / 'Control+A'"""
        self.page.press(selector, key)

    @allure.step("上传文件到 {selector}")
    def upload(self, selector: str, files):
        """上传文件，files 为路径或路径列表"""
        self.page.set_input_files(selector, files)

    @allure.step("滚动到元素: {selector}")
    def scroll_into_view(self, selector: str):
        self.page.locator(selector).scroll_into_view_if_needed()

    # ================= 元素查询 =================
    def text(self, selector: str) -> str:
        """取单个元素文本"""
        return self.page.text_content(selector)

    def texts(self, selector: str) -> list:
        """取所有匹配元素的文本(列表页常用)"""
        return self.page.locator(selector).all_text_contents()

    def get_attribute(self, selector: str, name: str) -> str:
        return self.page.get_attribute(selector, name)

    def count(self, selector: str) -> int:
        """匹配元素个数"""
        return self.page.locator(selector).count()

    def is_visible(self, selector: str) -> bool:
        return self.page.is_visible(selector)

    def is_enabled(self, selector: str) -> bool:
        return self.page.is_enabled(selector)

    def is_checked(self, selector: str) -> bool:
        return self.page.is_checked(selector)

    # ================= 等待 =================
    @allure.step("等待元素 {selector} 状态={state}")
    def wait_for(self, selector: str, state: str = "visible", timeout: int = None):
        """等待元素到指定状态: visible/hidden/attached/detached"""
        self.page.locator(selector).wait_for(state=state, timeout=timeout)

    # ================= 弹窗 / 截图 =================
    def auto_accept_dialog(self, accept: bool = True):
        """自动处理浏览器原生弹窗(alert/confirm)：accept=True 确定，False 取消"""
        self.page.on("dialog", lambda d: d.accept() if accept else d.dismiss())

    @allure.step("截图: {name}")
    def screenshot(self, name: str = "screenshot"):
        """手动截图并附加到 Allure(失败时框架已自动截图)"""
        allure.attach(self.page.screenshot(), name=name,
                      attachment_type=allure.attachment_type.PNG)

    # ================= 断言 (Playwright 自动等待) =================
    @allure.step("断言元素可见: {selector}")
    def expect_visible(self, selector: str):
        expect(self.page.locator(selector)).to_be_visible()

    @allure.step("断言元素隐藏/不存在: {selector}")
    def expect_hidden(self, selector: str):
        expect(self.page.locator(selector)).to_be_hidden()

    @allure.step("断言文本包含: {expected}")
    def expect_text(self, selector: str, expected: str):
        expect(self.page.locator(selector)).to_contain_text(expected)

    @allure.step("断言输入框值 == {expected}")
    def expect_value(self, selector: str, expected: str):
        expect(self.page.locator(selector)).to_have_value(expected)

    @allure.step("断言元素数量 == {expected}")
    def expect_count(self, selector: str, expected: int):
        expect(self.page.locator(selector)).to_have_count(expected)

    @allure.step("断言 URL 包含: {url_part}")
    def expect_url(self, url_part: str):
        expect(self.page).to_have_url(f"**{url_part}**")

    @allure.step("断言标题包含: {text}")
    def expect_title(self, text: str):
        expect(self.page).to_have_title(text)
