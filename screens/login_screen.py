"""
App 登录页对象 (示例)
- 定位器集中管理，App 改版只改这里
"""

import allure

from screens.base_screen import BaseScreen


class LoginScreen(BaseScreen):
    # ---- 定位器 (优先 resource-id / accessibility id) ----
    INPUT_USERNAME = (BaseScreen.ID, "com.example.app:id/et_username")
    INPUT_PASSWORD = (BaseScreen.ID, "com.example.app:id/et_password")
    BTN_LOGIN = (BaseScreen.ID, "com.example.app:id/btn_login")
    MSG_ERROR = (BaseScreen.ID, "com.example.app:id/tv_error")
    HOME_TAB = (BaseScreen.ACCESSIBILITY_ID, "home_tab")

    @allure.step("App 登录: {username}")
    def login(self, username: str, password: str):
        self.input(*self.INPUT_USERNAME, username)
        self.input(*self.INPUT_PASSWORD, password)
        self.click(*self.BTN_LOGIN)

    def get_error(self) -> str:
        return self.text(*self.MSG_ERROR)

    def is_login_success(self) -> bool:
        """登录成功标志：首页 tab 出现"""
        return self.is_displayed(*self.HOME_TAB)
