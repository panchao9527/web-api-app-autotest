"""
门店销售数据上送 - 接口测试（数据驱动）
- 原来 3 个近 2000 行、只差 ownership(M/L/J) 的方法 → 合并为 1 个数据驱动用例
- 门店编码从 data/sales/*.txt 读取（真实文件不入库，见 *.txt.example）
"""
import datetime

import allure
import pytest

from api.sales_api import SalesApi
from core.assertions import Assert
from utils.data_loader import read_lines

# 业务日期：默认取前一天
BUSINESS_DATE = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

# 门店列表文件 → ownership 映射（要加一类餐厅只需在这里加一行）
STORE_FILE_OWNERSHIP = [
    ("sales/m餐厅.txt", "M"),
    ("sales/L餐厅.txt", "L"),
    ("sales/j餐厅.txt", "J"),
]


def load_store_cases():
    """展开成 (store_code, ownership) 参数对"""
    cases = []
    for filename, ownership in STORE_FILE_OWNERSHIP:
        for store_code in read_lines(filename):
            cases.append((store_code, ownership))
    return cases


_CASES = load_store_cases()


@allure.epic("销售数据")
@allure.feature("门店销售数据上送")
@pytest.mark.api
class TestSalesData:

    @allure.story("上送各类餐厅销售数据")
    @pytest.mark.skipif(
        not _CASES,
        reason="未找到门店列表 data/sales/*.txt（参考同目录 *.txt.example 创建）",
    )
    @pytest.mark.parametrize(
        "store_code,ownership",
        _CASES or [("PLACEHOLDER", "M")],
        ids=[f"{c}-{o}" for c, o in _CASES] or ["placeholder"],
    )
    def test_push_store_sales(self, store_code, ownership):
        resp = SalesApi().push_sales(store_code, ownership, BUSINESS_DATE)
        Assert.status_code(resp, 200)
        # TODO: 按接口实际返回补强业务断言，例如:
        # Assert.json_value(resp, "code", 0)
