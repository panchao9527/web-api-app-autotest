"""BOSS 发票查询页 Page Object。"""

import re

import allure
from playwright.sync_api import Response, expect

from pages.base_page import BasePage


class InvoiceQueryPage(BasePage):
    """封装发票精确查询、结果读取和进入详情的只读流程。"""

    LIST_PATH = "/recon/electronicInvoice"
    DETAIL_PATH_PATTERN = re.compile(r"/recon/electronicInvoice/form\?id=\d+")
    QUERY_API = "/api/inner/fct/fct/invoice/queryList"
    DETAIL_API = "/api/inner/fct/fct/invoice/queryInvoiceById"

    INPUT_INVOICE_CODE = "#invoiceCode"
    INPUT_INVOICE_NO = "#invoiceNo"
    TABLE_ROWS = "tbody tr"

    @staticmethod
    def _is_query_response(response: Response) -> bool:
        return response.request.method == "POST" and InvoiceQueryPage.QUERY_API in response.url

    @staticmethod
    def _is_detail_response(response: Response) -> bool:
        return response.request.method == "POST" and InvoiceQueryPage.DETAIL_API in response.url

    def _first_data_row(self):
        return (
            self.page.locator(self.TABLE_ROWS)
            .filter(has=self.page.get_by_text("查看", exact=True))
            .first
        )

    @allure.step("打开 BOSS 发票查询页")
    def open_list(self) -> Response:
        """进入列表并返回页面首次自动查询对应的响应。"""
        with self.page.expect_response(self._is_query_response) as response_info:
            self.page.goto(
                f"{self.base_url}{self.LIST_PATH}",
                wait_until="domcontentloaded",
            )
        response = response_info.value
        expect(self.page.get_by_role("tab", name="发票查询", exact=True)).to_be_visible()
        expect(self.page.get_by_text("发票号码", exact=True).last).to_be_visible()
        expect(self._first_data_row()).to_be_visible()
        return response

    def first_invoice_no(self) -> str:
        """读取第一条数据的发票号码，避免依赖固定 UAT 数据。"""
        invoice_no = self._first_data_row().locator("td").nth(3).inner_text().strip()
        if not invoice_no:
            raise AssertionError("首条发票记录缺少发票号码")
        return invoice_no

    @allure.step("按发票号码精确查询: {invoice_no}")
    def query_by_invoice_no(self, invoice_no: str) -> Response:
        self.page.locator(self.INPUT_INVOICE_NO).fill(invoice_no)
        with self.page.expect_response(self._is_query_response) as response_info:
            self.page.get_by_role("button", name="查询", exact=True).click()
        response = response_info.value
        expect(self.page.get_by_text(invoice_no, exact=True)).to_be_visible()
        expect(self._first_data_row()).to_have_count(1)
        return response

    @allure.step("进入首条发票详情")
    def open_first_detail(self) -> tuple[str, Response]:
        row = self._first_data_row()
        invoice_no = row.locator("td").nth(3).inner_text().strip()
        with self.page.expect_response(self._is_detail_response) as response_info:
            row.get_by_text("查看", exact=True).click()
        response = response_info.value
        expect(self.page).to_have_url(self.DETAIL_PATH_PATTERN)
        expect(self.page.get_by_role("tab", name="发票查询详情", exact=True)).to_be_visible()
        return invoice_no, response

    @allure.step("校验发票详情关键字段")
    def expect_detail(self, invoice_no: str, detail: dict) -> None:
        """校验稳定字段；任一失败都会触发框架的失败截图和 Allure 附件。"""
        for label in ("发票类型", "发票号码", "开票日期", "合计金额", "购方名称", "销售方名称"):
            expect(self.page.get_by_text(label, exact=True)).to_be_visible()

        expect(self.page.get_by_text(invoice_no, exact=True)).to_be_visible()
        expect(self.page.get_by_text(str(detail["invoiceDate"]), exact=True)).to_be_visible()
        expect(self.page.get_by_text(str(detail["totalAmount"]), exact=True)).to_be_visible()
        expect(self.page.get_by_text(str(detail["purchaserName"]), exact=True)).to_be_visible()
        expect(self.page.get_by_text(str(detail["sellerName"]), exact=True)).to_be_visible()
        expect(self.page.get_by_role("button", name="发票预览", exact=True)).to_be_visible()
        expect(self.page.get_by_role("button", name="关闭", exact=True)).to_be_visible()
