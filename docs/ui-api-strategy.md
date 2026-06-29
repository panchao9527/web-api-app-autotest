# UI 测试 vs 接口测试：怎么分工 + UI 流程转接口场景

一句话：**UI 一个业务流程，背后就是页面按顺序调了一串接口——这串接口序列天然就是一条接口场景级用例。** 本文讲清两者怎么分工、怎么互相转化。

---

## 一、核心认知

```
用户在页面操作:   登录    →    加入购物车   →    提交订单    →    支付
页面背后调接口:  /login  →  /cart/add    →  /order/create  →  /pay
                          ↑ 这串接口序列 = 一条接口场景级用例
```

---

## 二、两者怎么分工（测试金字塔）

| | 接口场景用例 | UI 测试 |
|---|------------|---------|
| 测什么 | 后端业务逻辑、接口协作、数据流转 | 前端渲染、交互、前后端集成 |
| 速度 | 快 | 慢 |
| 稳定性 | 稳 | 脆（UI 一变就挂） |
| 数量 | **多**（主力） | **少**（只核心链路） |

**正确策略：**
```
业务逻辑（各种分支/边界/异常）  → 用「接口场景用例」大量覆盖（便宜稳定，常跑）
关键用户流（能不能正常用）      → 用「UI 测试」少量覆盖（每个核心流程 1 条冒烟）
```

> 例：下单。用接口场景覆盖满减/库存不足/超时等各种组合；UI 只测一条"正常下单页面能走通"。
> **别用 UI 去测一堆业务分支**——又慢又容易挂。

### 决策速查

| 你要验证的东西 | 用哪种 |
|---------------|--------|
| 某接口参数/边界/异常 | 单接口用例 |
| 一条业务链的后端逻辑与数据 | 接口场景用例 |
| 页面能否正常操作、渲染对不对 | UI 测试（少量） |
| 前后端联调是否打通 | UI 测试 + `expect_response` 混合验证 |

---

## 三、用法一：UI 操作 → 抓接口序列 → 反推接口场景用例（推荐）

框架提供了 `NetworkRecorder`（见 `core/network_recorder.py`）+ `network_recorder` fixture。
跑一遍 UI 流程，自动导出页面调了哪些接口：

```python
import pytest
from pages.login_page import LoginPage

@pytest.mark.web
def test_capture_checkout_apis(page, network_recorder):
    # 手动走一遍 UI 业务流
    LoginPage(page).login("user", "pwd")
    # ... 加购、下单等 UI 操作 ...

    network_recorder.print_summary()          # 日志打印接口调用序列
    network_recorder.save("captured_apis.json")  # 导出成 json
```

日志会输出类似：
```
===== 捕获到 4 个接口调用 =====
  1. POST   200 https://.../api/login
  2. POST   200 https://.../api/cart/add
  3. POST   201 https://.../api/order/create
  4. POST   200 https://.../api/order/pay
```

**拿到这串序列，就能照着写接口场景用例**（参考 `docs/api-guide.md` 的场景级写法）。
> 也可以把 `captured_apis.json` 交给 AI，让它按框架规范生成接口场景用例。

---

## 四、用法二：UI 测试里顺带校验接口（混合验证）

跑 UI 测试的同时，断言关键接口确实被调用且返回正常，用 Playwright 的 `expect_response`：

```python
@pytest.mark.web
def test_checkout_ui(page):
    # 点"提交订单"的同时，断言下单接口返回正常
    with page.expect_response("**/api/order/create") as resp_info:
        CheckoutPage(page).submit_order()
    resp = resp_info.value
    assert resp.status == 200
    assert resp.json()["code"] == 0      # UI 操作 + 接口结果 一起验
```

这样一条 UI 用例同时覆盖了"前端交互"和"后端接口结果"。

---

## 五、小结

> - UI 流程背后的接口序列 = 一条接口场景用例，**可以这么转**。
> - 推荐：**接口层大量覆盖业务逻辑（稳/快），UI 层只留核心冒烟（验证真能用）。**
> - 用 `NetworkRecorder` 把 UI 流程的接口序列录下来，是**发现/编写接口场景用例**的高效途径。
