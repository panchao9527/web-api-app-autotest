---
name: api-scenario-test
description: 生成本框架规范的【接口场景级用例】—— 把一条业务流程(如 登录→下单→支付→查询→查库)编排成多接口串联的端到端用例，自动用共享 HttpClient 贯穿登录态、用 extract 接口间传参、wait_until 等异步、DBClient 查库核对，遵循框架规范并提交推送。当用户描述业务流程、或提供接口调用序列(含 NetworkRecorder 抓取结果)并希望写场景用例时使用。
---

# 业务流程 → 接口场景级用例 生成工作流

把一条业务流程编排成多接口串联的端到端用例。

## 触发场景
- 用户描述业务流程，如"登录 → 创建订单 → 支付 → 查订单状态=PAID → 查库核对"
- 或用户提供接口调用序列（F12 抓包 / `NetworkRecorder` 导出的 captured_apis.json）
- 典型说法："用 api-scenario-test 写一条下单流程""把这串接口写成场景用例"

## 第 1 步：拆解流程
把流程拆成有序步骤，识别每步属于哪个模块、调哪个接口。缺少的接口封装先按 `BaseApi` 规范补到 `api/`。

## 第 2 步：编排用例（核心套路）
1. **共用一个 client**：用 `api_client` fixture(框架提供的共享 HttpClient)，各模块 `XxxApi(client=api_client)`，使登录态(token/cookie)贯穿全程
2. **逐步执行**，每步用 `with allure.step("步骤N：...")` 包裹
3. 每步断言：`Assert.status_code` + 业务码
4. **接口间传参**：用 `utils.extractor.extract(resp.json(), "$.data.xxx")` 取上一步结果传给下一步
5. **异步状态**：用 `utils.retry.wait_until(...)` 轮询直到状态就绪
6. **数据核对**：关键数据用 `clients.db_client.DBClient` 查库二次确认（不只信接口返回）
7. **数据清理**：写数据的流程，在 teardown(或 finally)清理产生的测试数据

## 第 3 步：留 TODO 给用户
- 业务成功标志字段(如 `code==0`、`status=="PAID"`)
- 环境内有效的真实数据(商品ID、门店码等)
- 各步的具体断言点

## 第 4 步：组织与标记
- 放 `testcases/api/<module>/test_<flow>_flow.py`（场景用例单独文件，文件名含 flow）
- 标记：`api` + 主模块名 + `scenario` + `p0`
- `@allure.epic/feature/story` + 每步 `@allure.step`

## 第 5 步：规范校验 + 提交
- 用例只调封装方法；账号密码用 `env_settings`
- `python -m py_compile` 校验语法
- commit：`test(api): 新增 <flow> 场景级用例`；用 push_to_remote 推送；给链接

## 参考模板（标准结构）
```python
def test_order_e2e(self, api_client, env_settings):
    user, order = UserApi(client=api_client), OrderApi(client=api_client)  # 共享client,登录态贯穿

    with allure.step("登录"):
        Assert.status_code(user.login(env_settings.username, env_settings.password), 200)
    with allure.step("创建订单"):
        resp = order.create_order(product_id=1001, qty=2)
        order_id = extract(resp.json(), "$.data.order_id")   # 传参
    with allure.step("支付"):
        Assert.status_code(order.pay(order_id), 200)
    with allure.step("轮询状态=PAID"):
        wait_until(lambda: extract(order.get_order(order_id).json(), "$.data.status") == "PAID",
                   timeout=10, desc="等待支付完成")
    with allure.step("查库核对"):
        with DBClient() as db:
            row = db.query_one("SELECT status FROM orders WHERE order_id=%s", [order_id])
        Assert.equal(row["status"], "PAID")
```

## 框架约定速查
- 共享客户端 `core/http_client.py` `HttpClient`；接口基类 `api/base_api.py`
- 取值 `utils/extractor.py` `extract/extract_all`
- 轮询 `utils/retry.py` `wait_until`
- 查库 `clients/db_client.py` `DBClient`
- 断言 `core/assertions.py` `Assert`
- fixture：`env_settings`、`logged_in_client`
- 详见 `docs/自动化测试框架操作手册.md` 的“API 自动化操作步骤”章节
