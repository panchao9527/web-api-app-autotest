"""
App 页面对象基类 (Appium / 移动端 PO 模式)
- 封装通用控件操作：查找/点击/输入/等待/各方向滑动/长按/滚动找元素/toast/返回...
- 定位优先用 accessibility id / resource-id，避免脆弱定位
- 显式等待已内置，禁止写 sleep
"""

import allure
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.settings import settings
from utils.logger import log
from utils.redaction import safe_input_value


class BaseScreen:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, settings.timeout)

    # ================= 查找 / 等待 =================
    @allure.step("查找并等待可点击: {value}")
    def find(self, by, value):
        """显式等待元素可点击"""
        return self.wait.until(EC.element_to_be_clickable((by, value)))

    @allure.step("等待元素出现: {value}")
    def wait_for(self, by, value):
        """显式等待元素存在(出现即可，不要求可点击)"""
        return self.wait.until(EC.presence_of_element_located((by, value)))

    # ================= 基础操作 =================
    @allure.step("点击: {value}")
    def click(self, by, value):
        log.info(f"点击控件: {value}")
        self.find(by, value).click()

    @allure.step("输入内容到: {value}")
    def input(self, by, value, text, sensitive: bool = False):
        safe_text = safe_input_value(text, value, sensitive)
        log.info(f"输入: {value} <- {safe_text}")
        el = self.find(by, value)
        el.clear()
        el.send_keys(text)

    @allure.step("清空: {value}")
    def clear(self, by, value):
        self.find(by, value).clear()

    def text(self, by, value) -> str:
        return self.find(by, value).text

    def get_attribute(self, by, value, name: str) -> str:
        return self.find(by, value).get_attribute(name)

    def is_displayed(self, by, value) -> bool:
        """元素是否可见(不等待，立即判断)"""
        try:
            return self.driver.find_element(by, value).is_displayed()
        except Exception:  # noqa
            return False

    # ================= 滑动(四方向) =================
    def _swipe(self, start_x, start_y, end_x, end_y, duration=800):
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)

    @allure.step("上滑")
    def swipe_up(self, duration=800):
        s = self.driver.get_window_size()
        self._swipe(
            s["width"] // 2,
            int(s["height"] * 0.8),
            s["width"] // 2,
            int(s["height"] * 0.2),
            duration,
        )

    @allure.step("下滑")
    def swipe_down(self, duration=800):
        s = self.driver.get_window_size()
        self._swipe(
            s["width"] // 2,
            int(s["height"] * 0.2),
            s["width"] // 2,
            int(s["height"] * 0.8),
            duration,
        )

    @allure.step("左滑")
    def swipe_left(self, duration=800):
        s = self.driver.get_window_size()
        self._swipe(
            int(s["width"] * 0.8),
            s["height"] // 2,
            int(s["width"] * 0.2),
            s["height"] // 2,
            duration,
        )

    @allure.step("右滑")
    def swipe_right(self, duration=800):
        s = self.driver.get_window_size()
        self._swipe(
            int(s["width"] * 0.2),
            s["height"] // 2,
            int(s["width"] * 0.8),
            s["height"] // 2,
            duration,
        )

    def pull_to_refresh(self):
        """下拉刷新"""
        self.swipe_down()

    @allure.step("滑动查找元素: {value}")
    def scroll_to_find(self, by, value, max_swipes: int = 8):
        """反复上滑直到元素出现(列表里找下方元素)，找不到抛异常"""
        for i in range(max_swipes):
            if self.is_displayed(by, value):
                log.info(f"第{i}次滑动后找到: {value}")
                return self.driver.find_element(by, value)
            self.swipe_up()
        raise AssertionError(f"滑动 {max_swipes} 次仍未找到元素: {value}")

    # ================= 手势 =================
    @allure.step("长按: {value}")
    def long_press(self, by, value, duration=2000):
        """长按元素(默认2秒)"""
        el = self.find(by, value)
        rect = el.rect
        cx = rect["x"] + rect["width"] // 2
        cy = rect["y"] + rect["height"] // 2
        self.driver.tap([(cx, cy)], duration)

    @allure.step("坐标点击 ({x},{y})")
    def tap(self, x: int, y: int):
        self.driver.tap([(x, y)])

    # ================= toast / 系统 =================
    @allure.step("获取 Toast 文本")
    def get_toast(self) -> str:
        """获取 Android Toast 文本(需 UiAutomator2)"""
        try:
            el = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((AppiumBy.XPATH, "//android.widget.Toast"))
            )
            return el.get_attribute("name") or el.text
        except Exception:  # noqa
            return ""

    @allure.step("断言 Toast 包含: {expected}")
    def assert_toast(self, expected: str):
        toast = self.get_toast()
        log.info(f"Toast: {toast}")
        assert expected in toast, f"Toast 不含 [{expected}]，实际: {toast}"

    @allure.step("隐藏键盘")
    def hide_keyboard(self):
        try:
            self.driver.hide_keyboard()
        except Exception:  # noqa
            pass

    @allure.step("返回上一页")
    def back(self):
        self.driver.back()

    @allure.step("截图: {name}")
    def screenshot(self, name: str = "screenshot"):
        allure.attach(
            self.driver.get_screenshot_as_png(),
            name=name,
            attachment_type=allure.attachment_type.PNG,
        )

    # 常用定位方式快捷别名
    ID = AppiumBy.ID
    ACCESSIBILITY_ID = AppiumBy.ACCESSIBILITY_ID
    XPATH = AppiumBy.XPATH
    ANDROID_UIAUTOMATOR = AppiumBy.ANDROID_UIAUTOMATOR
    CLASS_NAME = AppiumBy.CLASS_NAME
