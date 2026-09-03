"""BOSS 发票查询和详情只读冒烟测试。"""

import allure
import pytest

from pages.boss.invoice_query_page import InvoiceQueryPage


def _assert_success_response(response, *, api_name: str) -> dict:
    assert response.status == 200, f"{api_name} HTTP 状态异常: {response.status}"
    payload = response.json()
    assert payload.get("code") == 1, f"{api_name}业务码异常: {payload}"
    assert payload.get("data") is not None, f"{api_name}缺少 data: {payload}"
    return payload


@allure.feature("BOSS 发票管理")
@allure.story("发票查询与详情")
@pytest.mark.web
@pytest.mark.smoke
@pytest.mark.p0
def test_query_invoice_and_open_detail(page):
    """动态取首条发票精确查询，并校验列表、接口和详情字段。"""
    invoice_page = InvoiceQueryPage(page)

    initial_response = invoice_page.open_list()
    initial_payload = _assert_success_response(initial_response, api_name="发票列表初始化")
    assert initial_payload["data"]["list"], "最近 30 天没有可用于验证的发票数据"

    invoice_no = invoice_page.first_invoice_no()
    query_response = invoice_page.query_by_invoice_no(invoice_no)
    query_payload = _assert_success_response(query_response, api_name="发票精确查询")
    result_list = query_payload["data"]["list"]
    assert len(result_list) == 1, f"精确查询预期返回 1 条，实际为 {len(result_list)} 条"
    assert result_list[0]["invoiceNo"] == invoice_no

    detail_invoice_no, detail_response = invoice_page.open_first_detail()
    detail_payload = _assert_success_response(detail_response, api_name="发票详情查询")
    detail = detail_payload["data"]
    assert detail_invoice_no == invoice_no
    assert detail["invoiceNo"] == invoice_no

    invoice_page.expect_detail(invoice_no, detail)
