"""
销售数据接口封装
- 上送门店销售数据；报文由 data/sales/sales_payload.py 构造
- URL 走 config.yaml 的 api_base_url（占位，本地换成真实地址）
"""

import allure

from api.base_api import BaseApi
from data.sales.sales_payload import build_sales_payload

# 接口相对路径（base_url 在 config.yaml）
SALES_PATH = "/fctdata/sales/master/salesAccessConsumer"


class SalesApi(BaseApi):
    @allure.step("上送销售数据: store={store_code} ownership={ownership}")
    def push_sales(self, store_code: str, ownership: str, business_date: str):
        payload = build_sales_payload(store_code, ownership, business_date)
        return self.client.post(SALES_PATH, json=payload)
