"""
App 页面对象基类 (Appium / 移动端 PO 模式)
- 封装通用控件操作：查找、点击、输入、显式等待、滑动
- 定位优先用 accessibility id / resource-id，避免脆弱定位
"""
import allure
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.settings import settings
from utils.logger import log


class BaseScreen:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, settings.timeout)

    @allure.step("查找并等待元素: {value}")
    def find(self, by, value):
        """显式等待元素可点击，杜绝 sleep"""
        return self.wait.until(EC.element_to_be_clickable((by, value)))

    @allure.step("点击: {value}")
    def click(self, by, value):
        log.info(f"点击控件: {value}")
        self.find(by, value).click()

    @allure.step("输入 [{text}]: {value}")
    def input(self, by, value, text):
        log.info(f"输入: {value} <- {text}")
        el = self.find(by, value)
        el.clear()
        el.send_keys(text)

    def text(self, by, value) -> str:
        return self.find(by, value).text

    def is_displayed(self, by, value) -> bool:
        try:
            return self.driver.find_element(by, value).is_displayed()
        except Exception:  # noqa
            return False

    @allure.step("滑动屏幕")
    def swipe_up(self, duration=800):
        """从屏幕下方往上滑(常用于上拉加载)"""
        size = self.driver.get_window_size()
        x = size["width"] // 2
        start_y = int(size["height"] * 0.8)
        end_y = int(size["height"] * 0.2)
        self.driver.swipe(x, start_y, x, end_y, duration)

    # 常用定位方式快捷别名
    ID = AppiumBy.ID
    ACCESSIBILITY_ID = AppiumBy.ACCESSIBILITY_ID
    XPATH = AppiumBy.XPATH
    ANDROID_UIAUTOMATOR = AppiumBy.ANDROID_UIAUTOMATOR
