"""
登录页 Page Object (示例)
- 定位器集中在类顶部，UI 改版只改这里
- 业务方法对外暴露语义化操作 (login)，用例无需关心元素
"""
import allure

from pages.base_page import BasePage


class LoginPage(BasePage):
    # ---- 定位器 (优先 data-testid，最稳定) ----
    URL = "/login"
    INPUT_USERNAME = "[data-testid='username']"
    INPUT_PASSWORD = "[data-testid='password']"
    BTN_SUBMIT = "[data-testid='login-btn']"
    MSG_ERROR = "[data-testid='error-msg']"
    USER_AVATAR = "[data-testid='user-avatar']"

    @allure.step("执行登录: {username}")
    def login(self, username: str, password: str):
        """业务方法：完整登录流程"""
        self.open(self.URL)
        self.fill(self.INPUT_USERNAME, username)
        self.fill(self.INPUT_PASSWORD, password)
        self.click(self.BTN_SUBMIT)

    def get_error_message(self) -> str:
        return self.text(self.MSG_ERROR)

    def is_logged_in(self) -> bool:
        """登录成功的标志：头像出现"""
        return self.is_visible(self.USER_AVATAR)
