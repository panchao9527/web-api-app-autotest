"""
UI 自动化 体验示例（百度搜索）
- 目的：让你第一次就能看到浏览器自动操作并跑出绿色通过
- 运行(加 --headed 能看到浏览器):
    playwright install chromium
    pytest testcases/web/test_demo_search.py --headed --slowmo 800 -s
"""

import allure
import pytest
from playwright.sync_api import Page

from pages.demo_search_page import BaiduSearchPage


@allure.epic("UI 体验示例")
@allure.feature("百度搜索")
@pytest.mark.web
class TestDemoSearch:
    @allure.story("搜索后出现结果")
    @pytest.mark.smoke
    def test_baidu_search(self, page: Page):
        search_page = BaiduSearchPage(page)
        search_page.search("自动化测试")
        # 断言结果区域出现（Playwright 自动等待）
        search_page.expect_visible(BaiduSearchPage.RESULTS)
