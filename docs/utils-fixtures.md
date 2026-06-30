# 工具(utils) 与 Fixture 速查

框架提供的通用工具和 fixture 一览。每个都附一句用法，详细看对应源码的 docstring。

---

## 一、通用工具 utils/

### 日志 `utils/logger.py`
```python
from utils.logger import log
log.info("...")   # 控制台彩色 + logs/ 按天文件，自动用
```

### 数据加载 `utils/data_loader.py`
```python
from utils.data_loader import load_yaml, load_json, load_excel, read_lines
load_yaml("login_data.yaml")        # 读 data/ 下 yaml -> list/dict
load_excel("cases.xlsx")            # 读 excel -> [{列:值}]
read_lines("sales/m餐厅.txt")        # 读文本每行(忽略空行/#注释)
```

### 随机数据 `utils/random_data.py`
```python
from utils.random_data import random_name, random_phone, uuid_str, unique_id, random_digits
random_name(); random_phone(); random_email()      # Faker 造数据(中文)
uuid_str()                          # 无横线uuid
unique_id("ORD")                    # ORD+毫秒时间戳,唯一编号
random_digits(6)                    # 6位随机数字(验证码)
```

### 日期时间 `utils/date_util.py`
```python
from utils.date_util import now_str, today_str, yesterday_str, days_offset
yesterday_str()        # '2026-06-28'
days_offset(-7)        # 7天前
now_str()              # '2026-06-29 17:40:00'
```

### 响应取值(JSONPath) `utils/extractor.py`
```python
from utils.extractor import extract, extract_all
extract(resp.json(), "$.data.order_id")          # 取第一个匹配
extract_all(resp.json(), "$.data.list[*].name")  # 取所有匹配
```

### 加密/签名 `utils/crypto_util.py`
```python
from utils.crypto_util import md5, sha256, hmac_sha256, base64_encode, sign_params
md5("abc"); hmac_sha256(key, msg)
sign_params({"a":1,"b":2}, "secret")   # 按key排序+拼密钥签名
```

### 轮询/重试 `utils/retry.py`
```python
from utils.retry import wait_until, retry
wait_until(lambda: 条件(), timeout=10, interval=1)   # 等异步结果(DB/MQ/状态)
@retry(times=3, delay=2)                              # 失败自动重试装饰器
```

### 文件操作 `utils/file_util.py`
```python
from utils.file_util import read_json, write_json, read_text, write_text, ensure_dir, project_path
write_json("reports/x.json", data)     # 写json(中文不转义)
project_path("data", "x.yaml")         # 拼项目根路径
```

### 字典/响应对比 `utils/dict_util.py`
```python
from utils.dict_util import deep_get, contains_subset, dict_diff, pick, omit
deep_get(resp, "data.list.0.name")                    # 深层取值(支持下标)
contains_subset(resp.json(), {"code":0})              # 只校验关心的字段
dict_diff(预期, 实际)                                  # 返回差异 {路径:(期望,实际)}
```

### Schema 生成 `utils/schema_util.py`
```python
from utils.schema_util import generate_schema
schema = generate_schema(resp.json())   # 从真实返回生成 JSON Schema
# 配合 Assert.match_schema(resp, schema) 做契约测试
```

---

## 二、断言 `core/assertions.py`
```python
from core.assertions import Assert
Assert.status_code(resp, 200)
Assert.jsonpath(resp, "$.data.status", "PAID")   # 嵌套字段
Assert.approx(95.58, 95.580000)                  # 浮点近似(金额)
# 还有 equal/not_equal/greater/less/between/not_empty/length/match_regex/match_schema...
```
> 完整列表见 `docs/api-guide.md` 断言速查表。

---

## 三、Fixture（用例参数里直接用）

| fixture | 位置 | 作用域 | 用途 |
|---------|------|--------|------|
| `env_settings` | conftest | session | 全局配置对象 |
| `page` | pytest-playwright内置 | function | Playwright 页面(Web测试) |
| `app_driver` | conftest | function | Appium driver(App测试,自动退出) |
| `network_recorder` | conftest | function | 跑UI流程抓接口序列 |
| `logged_in_client` | api_fixtures | session | 会话级登录态复用 |
| `api_client` | api_fixtures | function | 共享干净HttpClient(场景级多模块共用) |
| `db` | api_fixtures | function | 数据库查询(入参/断言查库,自动关连接) |
| `created_user` | api_fixtures | function | 数据准备+自动清理示例 |
| `clean_data` | api_fixtures | function | 注册式自动清理脏数据 |

### 常用 fixture 示例
```python
def test_api(api_client, db, clean_data):
    user = UserApi(client=api_client)          # 共享client
    product = db.query_one("SELECT id FROM products WHERE status='on' LIMIT 1")  # 查库取入参
    resp = OrderApi(client=api_client).create_order(product_id=product["id"], qty=1)
    oid = extract(resp.json(), "$.data.order_id")
    clean_data.add_table("orders", "order_id=%s", [oid])   # 注册清理,用例后自动删
    Assert.status_code(resp, 200)

def test_web(page):
    BaiduSearchPage(page).search("自动化测试")

def test_app(app_driver):
    LoginScreen(app_driver).login("user", "pwd")
```

---

## 四、客户端 clients/
```python
from clients.db_client import DBClient
from clients.redis_client import RedisClient
from clients.notify import Notifier

with DBClient() as db: db.query("...")          # MySQL
with RedisClient() as r: r.get("k")             # Redis
Notifier().send_test_result(total=50, passed=48, failed=2)   # 钉钉/企微推送
```
> 详见 `docs/infra-clients.md`。
