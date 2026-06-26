"""
Web 登录 UI 测试 (Playwright + PO 模式 示例)
- 用例只调 LoginPage 的业务方法，不碰元素定位
- page fixture 由 pytest-playwright 提供，失败自动截图(见 conftest)
- UI 自动化原则：少而精，只覆盖核心链路
"""
import allure
import pytest
from playwright.sync_api import Page

from pages.login_page import LoginPage


@allure.epic("用户中心")
@allure.feature("登录页面")
@pytest.mark.web
class TestLoginWeb:

    @allure.story("登录成功")
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_login_success(self, page: Page, env_settings):
        login_page = LoginPage(page)
        login_page.login(env_settings.username, env_settings.password)
        # 登录成功标志：头像出现 (Playwright 自动等待)
        login_page.expect_visible(LoginPage.USER_AVATAR)

    @allure.story("密码错误提示")
    @pytest.mark.regression
    def test_login_wrong_password(self, page: Page):
        login_page = LoginPage(page)
        login_page.login("valid_user", "wrong_pwd")
        login_page.expect_text(LoginPage.MSG_ERROR, "用户名或密码错误")
