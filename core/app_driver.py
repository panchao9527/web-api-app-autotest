"""
Appium 驱动工厂
- 根据配置创建 Android / iOS driver
- 统一管理 capabilities 与 server 地址
"""
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions

from config.settings import settings
from utils.logger import log


def create_app_driver():
    """根据 config.yaml 的 app.platform 创建对应平台的 Appium driver"""
    app_cfg = settings.app
    platform = app_cfg.get("platform", "Android").lower()
    server = app_cfg.get("appium_server", "http://127.0.0.1:4723")
    caps = settings.app_caps()

    log.info(f"启动 App driver | 平台={platform} | server={server}")

    if platform == "android":
        options = UiAutomator2Options().load_capabilities(caps)
    elif platform == "ios":
        options = XCUITestOptions().load_capabilities(caps)
    else:
        raise ValueError(f"不支持的平台: {platform}")

    driver = webdriver.Remote(command_executor=server, options=options)
    driver.implicitly_wait(settings.timeout)
    return driver
