"""
App 登录测试 (Appium + PO 模式 示例)
- 需要先启动 Appium server + 连接真机/模拟器
- app_driver fixture 由 conftest 提供，失败自动截图
- 默认 skip，去掉 skip 并准备好设备后即可运行
"""
import allure
import pytest

from screens.login_screen import LoginScreen


@allure.epic("用户中心")
@allure.feature("App 登录")
@pytest.mark.app
@pytest.mark.skip(reason="需连接真机/模拟器并启动 Appium server 后再放开")
class TestLoginApp:

    @allure.story("App 登录成功")
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_login_success(self, app_driver, env_settings):
        screen = LoginScreen(app_driver)
        screen.login(env_settings.username, env_settings.password)
        assert screen.is_login_success(), "登录后未进入首页"

    @allure.story("App 密码错误")
    @pytest.mark.regression
    def test_login_wrong_password(self, app_driver):
        screen = LoginScreen(app_driver)
        screen.login("valid_user", "wrong_pwd")
        assert "密码错误" in screen.get_error()
