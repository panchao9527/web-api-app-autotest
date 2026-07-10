"""
可运行的 UI 示例页面对象 —— 百度搜索（国内可直接访问，无需梯子）
- 用来快速体验 UI 自动化：打开百度 → 输入关键词 → 点搜索 → 断言出结果
- 用的是绝对 URL，不依赖 config 里的 web_base_url，开箱即跑
"""

import allure

from pages.base_page import BasePage


class BaiduSearchPage(BasePage):
    # 定位器（百度的稳定 id）
    URL = "https://www.baidu.com"
    INPUT_KW = "#kw"  # 搜索输入框
    BTN_SU = "#su"  # "百度一下"按钮
    RESULTS = "#content_left"  # 搜索结果区域

    @allure.step("百度搜索: {keyword}")
    def search(self, keyword: str):
        self.open(self.URL)
        self.fill(self.INPUT_KW, keyword)
        self.click(self.BTN_SU)
