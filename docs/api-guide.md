# 接口(API)自动化测试 手把手指南（小白版）

本指南假设你**从零开始**，跟着一步步做就能跑起来。API 测试是这套框架里**最容易上手、最稳定**的一块，建议先从它练手。

---

## 0. 先理解：API 测试在测什么？

API（接口）测试 = 不打开页面，直接给后端服务**发请求、看返回**对不对。比如：

> 发一个"登录"请求，带上用户名密码 → 期望返回状态码 `200` 且响应里有 `token`。

它比点页面快得多、也稳定得多，所以是自动化的**主力**。

整个链路：

```
你的测试用例 → UserApi(封装的接口) → HttpClient(发请求) → 后端服务 → 返回 → 用 Assert 断言
```

框架里 `core/http_client.py`、`api/`、`core/assertions.py` 都已经写好，你主要写**用例**和**数据**。

---

## 1. 装环境（只需一次）

### 1.1 安装 Python
- 装 [Python 3.11+](https://www.python.org/downloads/)，安装时**勾选 "Add Python to PATH"**
- 验证：
  ```bash
  python --version
  ```

### 1.2 拉代码 + 建虚拟环境 + 装依赖

```bash
# 拉代码
git clone https://github.com/panchao9527/web-api-app-autotest.git
cd web-api-app-autotest

# 建虚拟环境(隔离依赖，避免和电脑里其它库冲突)
python -m venv .venv
source .venv/Scripts/activate     # Git Bash
# PowerShell 用:  .venv\Scripts\activate

# 装依赖
pip install -r requirements.txt
```

> 激活成功后，命令行最前面会出现 `(.venv)`。以后每次进项目都要先激活一次。

---

## 2. 配置：告诉框架你的后端地址在哪

打开 `config/config.yaml`，找到 `test` 环境，把 `api_base_url` 改成**你要测的后端地址**：

```yaml
test:
  api_base_url: "https://你的后端地址.com"   # ← 改这里
```

如果接口需要账号密码，复制 `.env.example` 为 `.env` 填进去（`.env` 不会上传到 git）：

```bash
# .env 文件内容
TEST_USERNAME=你的用户名
TEST_PASSWORD=你的密码
```

---

## 3. 看懂已有的示例（照葫芦画瓢）

### 3.1 接口封装：`api/user_api.py`

把"怎么发请求"封装成方法，用例里就不用写细节了：

```python
class UserApi(BaseApi):
    @allure.step("查询用户: id={user_id}")
    def get_user(self, user_id: int):
        return self.client.get(f"/api/users/{user_id}")   # GET 请求
```

> `self.client` 就是框架封装的 `HttpClient`，支持 `get / post / put / delete / patch`，
> 会自动带上 base_url、超时、日志，并把请求/响应记录到 Allure 报告。

### 3.2 用例：`testcases/api/test_login_api.py`

```python
@pytest.mark.api
class TestUserApi:

    @pytest.mark.smoke         # 标记为冒烟用例
    def test_get_user(self):
        resp = UserApi().get_user(user_id=2)   # 调接口
        Assert.status_code(resp, 200)          # 断言状态码=200
```

### 3.3 断言：`core/assertions.py` 提供这些

| 方法 | 作用 |
|------|------|
| `Assert.status_code(resp, 200)` | 断言响应状态码 |
| `Assert.json_value(resp, "name", "kiro")` | 断言响应里某字段的值 |
| `Assert.contains(resp.json(), "token")` | 断言响应里包含某字段 |
| `Assert.equal(a, b, "说明")` | 断言两个值相等 |
| `Assert.match_schema(resp, schema)` | 断言响应结构符合预期(契约测试) |

---

## 4. 动手写你的第一个接口用例

假设你要测一个"获取商品详情"的接口 `GET /api/products/{id}`：

### 第 1 步：在 `api/` 下封装接口

```python
# api/product_api.py
import allure
from api.base_api import BaseApi

class ProductApi(BaseApi):
    @allure.step("获取商品详情: id={product_id}")
    def get_product(self, product_id: int):
        return self.client.get(f"/api/products/{product_id}")
```

### 第 2 步：在 `testcases/api/` 下写用例

```python
# testcases/api/test_product_api.py
import allure, pytest
from api.product_api import ProductApi
from core.assertions import Assert

@allure.feature("商品接口")
@pytest.mark.api
class TestProductApi:

    @pytest.mark.smoke
    def test_get_product(self):
        resp = ProductApi().get_product(product_id=1)
        Assert.status_code(resp, 200)                # 状态码对不对
        Assert.contains(resp.json(), "price", "应返回价格字段")
```

### 第 3 步：运行

```bash
pytest testcases/api/test_product_api.py
```

就这么简单——**封装接口 → 写用例调它 → 断言返回**。

---

## 5. 数据驱动：一套用例跑多组数据

不想为每组数据写一个用例？用数据驱动。看 `data/login_data.yaml`：

```yaml
- case_id: login_001
  desc: 正确账号密码登录成功
  username: "valid_user"
  password: "correct_pwd"
  expected_status: 200
```

用例里用 `parametrize` 把数据"喂"进去（见 `test_login_api.py` 的 `TestLoginApi`）：

```python
login_data = load_yaml("login_data.yaml")

@pytest.mark.parametrize("case", login_data, ids=[c["case_id"] for c in login_data])
def test_login(self, case):
    resp = UserApi().login(case["username"], case["password"])
    Assert.status_code(resp, case["expected_status"])
```

> 加测试场景时，**只需往 yaml 里加几行**，不用改代码。

---

## 6. 运行 & 筛选用例

```bash
pytest                       # 跑全部
pytest -m api                # 只跑接口用例
pytest -m smoke              # 只跑冒烟用例
pytest -m "api and smoke"    # 组合
pytest testcases/api/test_login_api.py            # 跑单个文件
pytest testcases/api/test_login_api.py::TestUserApi::test_get_user   # 跑单个用例
pytest -n 4                  # 4 进程并发加速
```

---

## 7. 看测试报告（Allure）

```bash
# 跑完用例后(结果在 reports/allure-results)
allure serve reports/allure-results
```

> 需要先装 [Allure 命令行](https://allurereport.org/docs/install/)。
> 报告里能看到每个用例的**请求详情、响应内容、断言步骤**，失败时一目了然。

如果暂时不想装 Allure，直接看命令行输出也行——框架已经把每个请求的方法、URL、状态码、耗时打到控制台和 `logs/` 目录了。

---

## 8. 常见问题

| 问题 | 应对 |
|------|------|
| `ModuleNotFoundError` | 没激活虚拟环境，或没 `pip install -r requirements.txt` |
| 连接超时/拒绝 | `config.yaml` 的 `api_base_url` 写错，或后端没启动 |
| 401/403 | 接口需要登录态，先调 `login()`(会自动回填 token)，或在 `.env` 配账号 |
| 断言失败 | 看报告里实际返回值 vs 期望值，确认是 bug 还是用例写错 |
| 想看发了什么请求 | 看控制台日志(➡️ 请求 / ⬅️ 响应)或 `logs/` 目录 |

---

## 一句话总结

> 框架已封装好 **发请求(HttpClient) + 断言(Assert) + 报告**；
> 你的工作 = 在 `api/` 封装接口、在 `testcases/api/` 写用例、（可选）在 `data/` 加数据。
