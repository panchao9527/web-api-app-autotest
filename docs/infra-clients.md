# 测试基础设施客户端（DB / Redis / 通知）

框架在 `clients/` 下封装了一批**测试基础设施工具**，用于：
- **数据校验**：接口/UI 操作后查库、查缓存，断言数据真的对
- **数据准备/清理**：用例前后预置或清理测试数据
- **结果通知**：CI 跑完把测试报告摘要推送到钉钉/企微群

> 设计原则：**按需使用 + 依赖可选 + 懒加载**。核心框架保持轻量；较重的中间件（ES/Kafka/MQ）放 `requirements-optional.txt`，用到再装。

---

## 第 1 期已封装

| 客户端 | 文件 | 依赖 |
|--------|------|------|
| MySQL | `clients/db_client.py` | PyMySQL（核心） |
| Redis | `clients/redis_client.py` | redis（核心） |
| 钉钉/企微通知 | `clients/notify.py` | requests（核心） |

---

## 配置

连接信息放 `config/config.yaml`（非敏感），账号密码/webhook 放 `.env`（敏感，不入库）。

`config/config.yaml`（已为每个环境预留）：
```yaml
uat:
  db:    { host: "uat-db.example.com",    port: 3306, name: "app_db" }
  redis: { host: "uat-redis.example.com", port: 6379, db: 0 }
```

`.env`：
```bash
DB_USER=xxx
DB_PASSWORD=xxx
REDIS_PASSWORD=
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
WECOM_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
```

---

## 1. MySQL：查库断言

```python
from clients.db_client import DBClient

with DBClient() as db:                       # 用完自动关连接
    # 查多行
    rows = db.query("SELECT * FROM users WHERE status=%s", ["active"])
    # 查单行
    row  = db.query_one("SELECT count(*) AS c FROM orders WHERE user_id=%s", [1])
    # 写入(返回受影响行数，自动提交)
    db.execute("DELETE FROM orders WHERE id=%s", [order_id])
```

**典型场景**：接口下单后，查库确认订单真的写进去了：
```python
def test_create_order(self):
    resp = OrderApi().create_order(product_id=1, qty=2)
    order_id = resp.json()["order_id"]
    with DBClient() as db:
        row = db.query_one("SELECT status FROM orders WHERE id=%s", [order_id])
    assert row["status"] == "CREATED"        # 不只看接口返回，还查库验证
```

> 用参数化 `%s` 传参（防注入），不要用字符串拼接。

---

## 2. Redis：验证缓存 / 清理数据

```python
from clients.redis_client import RedisClient

with RedisClient() as r:
    r.set("verify_code:13800138000", "1234", ex=300)   # ex=过期秒数
    code = r.get("verify_code:13800138000")
    assert code == "1234"
    r.delete("verify_code:13800138000")                # 用例后清理
```

常用方法：`get / set / delete / exists / expire / keys / hgetall`。

---

## 1bis. 数据库典型用法：入参查库 + 断言查库 + DB数据驱动

接口测试里很常见：**请求入参要先查库拿合法数据**，**断言时也要查库核对**。框架提供 `db` fixture（用例里直接用，自动关连接）。

### 场景 A：入参依赖查库（先查 DB 拿合法数据，再发请求）
```python
def test_create_order(db):
    # ① 从库里取一个"在售"商品作为入参(避免硬编码不存在的ID)
    product = db.query_one("SELECT id, price FROM products WHERE status='on' LIMIT 1")
    assert product, "库里没有在售商品，无法下单"

    # ② 用查到的数据发请求
    resp = OrderApi().create_order(product_id=product["id"], qty=2)
    Assert.status_code(resp, 200)
```

### 场景 B：断言查库（不只信接口返回，查库二次核对）
```python
def test_create_order_db_check(db):
    resp = OrderApi().create_order(product_id=1001, qty=2)
    order_id = extract(resp.json(), "$.data.order_id")

    # 查库确认订单真的落库、状态/金额对
    row = db.query_one("SELECT status, amount FROM orders WHERE order_id=%s", [order_id])
    Assert.not_none(row, "订单应已写入数据库")
    Assert.equal(row["status"], "CREATED")
    Assert.approx(row["amount"], 199.00)        # 金额用近似断言
```

### 场景 C：DB 数据驱动（用查询结果生成参数化用例）
> 注意：parametrize 在**收集阶段**执行，早于 fixture，所以这里用**模块级函数**直接查库，不能用 `db` fixture。

```python
from clients.db_client import DBClient

def load_active_stores():
    """从库里查出所有在营门店，作为用例参数（替代手维护 txt 文件）"""
    with DBClient() as db:
        rows = db.query("SELECT store_code FROM stores WHERE status='active'")
    return [r["store_code"] for r in rows]

@pytest.mark.parametrize("store_code", load_active_stores())
def test_store(store_code):
    ...
```
> 这样门店列表**实时来自数据库**，不用手动维护 `data/sales/*.txt`。

> ⚠️ 提醒：入参/断言查库用 `SELECT`；如需造数据用 `db.execute(...)`，并记得用例后清理(teardown)。

### 场景 D：自动清理脏数据（`clean_data` fixture）
写数据的用例跑完会留下脏数据。用 `clean_data` fixture **注册清理任务**，用例结束（**即使失败**）自动按逆序清掉：

```python
def test_create_order(clean_data):
    resp = OrderApi().create_order(product_id=1001, qty=2)
    order_id = extract(resp.json(), "$.data.order_id")

    # 创建后立刻注册清理(两种方式任选)
    clean_data.add_table("orders", "order_id=%s", [order_id])      # ① 删库
    # clean_data.add_callback(lambda: OrderApi().delete_order(order_id))  # ② 调删除接口

    Assert.status_code(resp, 200)
    # 用例结束 → 自动执行: DELETE FROM orders WHERE order_id=...
```

特点：
- **逆序清理**（后注册先清，符合"先清子表再清主表"的依赖）
- **单条失败不影响其它**清理
- 用例**断言失败也会清**（注册在 teardown 执行）
- 支持删库 SQL、删多表、调删除接口任意组合

---

## 3. 通知：推送测试结果到钉钉/企微

```python
from clients.notify import Notifier

n = Notifier()

# 简单文本/markdown
n.dingtalk_text("冒烟测试通过 ✅")
n.wecom_markdown("## 测试报告\n- 通过: 50\n- 失败: 2")

# 高层封装：一行推送结果摘要(钉钉+企微都发)
n.send_test_result(total=52, passed=50, failed=2,
                   duration="3m20s",
                   report_url="https://你的报告地址")
```

> 未配置的 webhook 会自动跳过，不报错。

### 在 CI 里跑完自动推送

可在流水线测试步骤后加一步，调用一个小脚本读取 pytest 结果并发送，例如：
```python
# scripts/notify_result.py (示例思路)
from clients.notify import Notifier
Notifier().send_test_result(total=..., passed=..., failed=...,
                            report_url="${{ 报告地址 }}")
```
（具体数字可从 pytest 的 `--junitxml` 结果或 Allure 汇总里解析。）

---

## 第 2 期（按需扩展）

ES / Kafka / RabbitMQ / MongoDB / PostgreSQL 的客户端尚未封装，依赖已在
`requirements-optional.txt` 里列好（注释状态）。需要时：
1. 取消对应依赖的注释，`pip install -r requirements-optional.txt`
2. 在 `clients/` 下按相同风格（懒加载 + 上下文管理器 + 日志）新增对应客户端

> 或者直接告诉 AI 你用的中间件，让它按本框架规范帮你补封装。
