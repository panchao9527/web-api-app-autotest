"""
门店销售数据上送 - 报文构造器
- 把原本内联在用例里的几百行 JSON 抽成一个函数
- 差异项作参数：store_code(门店编码) / ownership(M/L/J) / business_date(业务日期)
- 各列表用"数据表 + 循环"生成，消除重复
- 注意：beName 等为脱敏占位值，本地按真实情况替换即可
"""

# 固定的 createTime（与原报文一致）
_CT = "2025-09-29 00:55:36"  # itemStatList / statList
_PT = "2025-09-29 00:55:46"  # paymentList / salesList


def build_sales_payload(store_code: str, ownership: str, business_date: str) -> dict:
    be = {"01": f"{store_code}01", "02": f"{store_code}02"}

    # ---- itemStatList：(beKey, itemCode, desc, qty, netSales, salesAmount, statCode, taxAmount, taxRate) ----
    item_rows = [
        ("01", "521196", "示例商品-居家服", 1, 95.58, 108.00, "SLP", 12.42, "13"),
        ("02", "901609", "随机玩具", 2, 10.15, 10.76, "HM", 0.61, "6"),
        ("02", "513817", "示例-月卡(30天)", 2, 34.11, 36.16, "EquityCard", 2.05, "6"),
        ("01", "7001", "随机玩具1个", 1, 5.66, 6.00, "HM", 0.34, "6"),
        ("01", "514696", "示例-早餐卡", 1, 11.23, 11.90, "EquityCard", 0.67, "6"),
        ("01", "520815", "示例-季卡(90天)", 1, 32.61, 34.57, "EquityCard", 1.96, "6"),
        ("01", "513817", "示例-月卡(30天)", 4, 64.13, 67.98, "EquityCard", 3.85, "6"),
    ]
    item_stat_list = [
        {
            "balanceFlag": 1,
            "beCode": be[k],
            "businessDate": business_date,
            "createBy": "system",
            "createTime": _CT,
            "itemCode": code,
            "itemDescription": desc,
            "itemQty": qty,
            "netSales": net,
            "salesAmount": amt,
            "settlementType": 0,
            "statCode": sc,
            "statType": "FctNonProduct",
            "storeCode": store_code,
            "subStatType": "",
            "taxAmount": tax,
            "taxRate": rate,
            "versionNo": 1,
        }
        for k, code, desc, qty, net, amt, sc, tax, rate in item_rows
    ]

    # ---- paymentList：(amount, tenderId, tenderName) ----
    payment_rows = [
        (255.00, "12", "手机支付"),
        (4120.30, "29", "MDS美团外卖"),
        (12.30, "180", "微信小程序-麦钱包支付"),
        (407.30, "182", "支付宝小程序-支付宝支付"),
        (613.60, "154", "App微信支付"),
        (826.87, "155", "App支付宝支付"),
        (601.50, "210", "自助点餐微信支付"),
        (191.00, "156", "App麦钱包支付"),
        (268.65, "211", "自助点餐支付宝支付"),
        (2412.30, "179", "微信小程序-微信支付"),
        (33.50, "223", "抖音支付"),
        (983.59, "202", "优惠券A"),
        (60.90, "204", "APP云闪付支付"),
        (23.90, "228", "京东外卖"),
        (360.70, "218", "优惠券B"),
        (2700.80, "30", "MDS饿了么外卖"),
    ]
    payment_list = [
        {
            "amount": amt,
            "balanceFlag": 1,
            "businessDate": business_date,
            "chequePayment": "",
            "createBy": "system",
            "createTime": _PT,
            "currency": "CNY",
            "dataType": "3",
            "settlementType": 0,
            "storeCode": store_code,
            "tenderId": tid,
            "tenderName": name,
            "tenderType": 1,
            "versionNo": 1,
        }
        for amt, tid, name in payment_rows
    ]

    # ---- salesList：(beKey, beName, beType, gc, mainItem, netSales, salesType, subItem, taxRate, totalSales, totalTax) ----
    # beName 为脱敏占位
    sales_rows = [
        (
            "02",
            "示例餐厅-MDS",
            "MDS",
            173,
            "0",
            7353.66,
            "Product Sales",
            "1",
            "6",
            7795.08,
            441.42,
        ),
        ("02", "示例餐厅-MDS", "MDS", 173, "1", 44.26, "Non Product Sales", "1", "6", 46.92, 2.66),
        ("02", "示例餐厅-MDS", "MDS", 173, "1", 642.29, "MDS", "2", "6", 680.80, 38.51),
        (
            "01",
            "Front Counter",
            "FC",
            160,
            "0",
            4130.17,
            "Product Sales",
            "1",
            "6",
            4378.04,
            247.87,
        ),
        (
            "01",
            "Front Counter",
            "FC",
            160,
            "1",
            113.63,
            "Non Product Sales",
            "1",
            "6",
            120.45,
            6.82,
        ),
        ("01", "Front Counter", "FC", 160, "1", 0.00, "MDS", "2", "6", 0.00, 0.00),
        ("01", "Front Counter", "FC", 160, "0", 0.00, "Product Sales", "1", "13", 0.00, 0.00),
        (
            "01",
            "Front Counter",
            "FC",
            160,
            "1",
            95.58,
            "Non Product Sales",
            "1",
            "13",
            108.00,
            12.42,
        ),
        ("01", "Front Counter", "FC", 160, "1", 0.00, "MDS", "2", "13", 0.00, 0.00),
        ("01", "示例餐厅-DT", "DT", 32, "0", 700.88, "Product Sales", "1", "6", 742.92, 42.04),
        ("01", "示例餐厅-DT", "DT", 32, "1", 0.00, "Non Product Sales", "1", "6", 0.00, 0.00),
        ("01", "示例餐厅-DT", "DT", 32, "1", 0.00, "MDS", "2", "6", 0.00, 0.00),
    ]
    sales_list = [
        {
            "balanceFlag": 1,
            "beCode": be[k],
            "beName": name,
            "beType": btype,
            "businessDate": business_date,
            "createBy": "system",
            "createTime": _PT,
            "currency": "CNY",
            "gc": gc,
            "mainItem": main,
            "netSales": net,
            "ownership": ownership,
            "salesType": stype,
            "settlementType": 0,
            "storeCode": store_code,
            "subItem": sub,
            "taxId": "",
            "taxRate": rate,
            "totalSales": total,
            "totalTax": ttax,
            "versionNo": 1,
        }
        for k, name, btype, gc, main, net, stype, sub, rate, total, ttax in sales_rows
    ]

    # ---- statList：(beKey, gc, netSales, salesAmount, statCode, statType, taxAmount, taxRate) ----
    stat_rows = [
        ("02", 173, 261.35, 277.20, "PackagingFee", "FctProduct", 15.85, "6"),
        ("01", 8, 95.58, 108.00, "SLP", "FctNonProduct", 12.42, "13"),
        ("02", 2, 10.15, 10.76, "HM", "FctNonProduct", 0.61, "6"),
        ("02", 2, 34.11, 36.16, "EquityCard", "FctNonProduct", 2.05, "6"),
        ("01", 8, 5.66, 6.00, "HM", "FctNonProduct", 0.34, "6"),
        ("01", 8, 107.97, 114.45, "EquityCard", "FctNonProduct", 6.48, "6"),
    ]
    stat_list = [
        {
            "balanceFlag": 1,
            "beCode": be[k],
            "businessDate": business_date,
            "createBy": "system",
            "createTime": _CT,
            "gc": gc,
            "netSales": net,
            "ownership": ownership,
            "salesAmount": amt,
            "settlementType": 0,
            "statCode": sc,
            "statType": st,
            "storeCode": store_code,
            "subStatType": "",
            "taxAmount": tax,
            "taxRate": rate,
            "versionNo": 1,
        }
        for k, gc, net, amt, sc, st, tax, rate in stat_rows
    ]

    return {
        "businessDate": business_date,
        "itemStatList": item_stat_list,
        "overshortList": [],
        "paymentList": payment_list,
        "salesList": sales_list,
        "settlementType": 0,
        "statList": stat_list,
        "storeCode": store_code,
    }
