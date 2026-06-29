# 代码规范（团队协作约定）

本文件固化本框架的编码约定。**新增用例/客户端时请遵循**，AI 生成代码也按此规范执行（见 `.kiro/skills/recording-to-po`）。

---

## 1. 注释规范

| 层次 | 要求 | 示例 |
|------|------|------|
| 文件头 docstring | 每个模块顶部必须有，说明**职责 + 配置来源 + 用法示例** | 见 `clients/db_client.py` 顶部 |
| 方法 docstring | 公开方法说明**作用 + 返回值** | `"""查询多行，返回 [{列: 值}, ...]"""` |
| 行内注释 | 解释**为什么**这么写（设计意图），而非复述代码 | `# 延迟导入，未装 PyMySQL 也不影响其它用例` |
| 区块分隔 | 用 `# ---- xxx ----` 给方法分组 | `# ---- 查询 ----` |

- **统一用中文注释**，让团队成员（含新手）易懂。
- 重点注释"为什么"：安全考量、等待策略、懒加载意图等。
- 配置文件（`config.yaml`/`pytest.ini`/`requirements.txt`）也要逐行注释。

---

## 2. 命名规范

| 对象 | 规范 | 示例 |
|------|------|------|
| 文件/模块 | 小写 + 下划线 | `user_api.py`、`login_page.py` |
| 类 | 大驼峰 | `UserApi`、`LoginPage`、`DBClient` |
| 方法/函数/变量 | 小写 + 下划线 | `get_user`、`order_id` |
| 常量/定位器 | 全大写 + 下划线 | `INPUT_USERNAME`、`BTN_SUBMIT` |
| 测试文件 | `test_<模块>_<端>.py` | `test_login_api.py`、`test_search_web.py` |
| 测试类 | `Test<功能><端>` | `TestLoginApi`、`TestSearchWeb` |
| 测试方法 | `test_<场景>` | `test_login_success` |

---

## 3. 分层规范（东西放哪）

| 放什么 | 目录 |
|--------|------|
| 接口封装（继承 `BaseApi`） | `api/` |
| Web 页面对象（继承 `BasePage`） | `pages/` |
| App 页面对象（继承 `BaseScreen`） | `screens/` |
| 测试用例 | `testcases/{api,web,app}/` |
| 测试数据（数据驱动） | `data/` |
| 共享 fixture | `fixtures/` |
| 基础设施客户端（DB/Redis/通知…） | `clients/` |
| 与业务无关的核心封装 | `core/` |
| 工具（日志/数据加载/随机数据） | `utils/` |

> 原则：**核心层(core)与业务层分离**；用例只写业务逻辑，细节封装进对应层。

---

## 4. PO 模式规范

### Web（`pages/`，继承 `BasePage`）
- 定位器集中声明在**类顶部**，用大写常量。
- 选择器优先级：`data-testid` / `id` > role/text > css > **xpath（尽量不用）**。
- 操作封装成**语义化业务方法**，加 `@allure.step(...)`。
- 只调用 `BasePage` 已有方法（`open/click/fill/text/is_visible/expect_visible/expect_text`）。
- **禁止写 `sleep`**（Playwright 自带等待）。

### App（`screens/`，继承 `BaseScreen`）
- 定位器写成元组：`(BaseScreen.ID, "包名:id/xxx")`。
- 定位优先级：resource-id > accessibility id > xpath。
- 只调用 `BaseScreen` 已有方法（`find/click/input/text/is_displayed/swipe_up`，已含显式等待）。
- **禁止写 `sleep`**。

---

## 5. 接口封装规范（`api/`）
- 继承 `BaseApi`，通过 `self.client`（`HttpClient`）发请求。
- 一个业务模块一个文件（`user_api.py`、`order_api.py`）。
- 方法名表达业务语义（`create_order` 而非 `post_order`）。
- 方法加 `@allure.step(...)`。
- 路径只写相对路径（`/api/users`），base_url 由框架拼接。

---

## 6. 用例规范（`testcases/`）
- **用例只调业务方法**，不出现裸 `page.` / `driver.` / 直接拼 URL。
- 账号密码等用 `env_settings`（来自 `.env`），**不要硬编码**。
- 必打标记：`@pytest.mark.{api|web|app}` + 优先级（`smoke`/`regression`/`p0`~`p2`）。
- 加 `@allure.feature/story`，便于报告归类。
- 断言用 `core/assertions.py` 的 `Assert`（API），UI 用 PO 的 `expect_*`。
- 失败截图已在 `conftest.py` 自动处理，**用例里不用管**。

---

## 7. 断言规范
- API：`Assert.status_code / json_value / contains / equal / match_schema / is_true`。
- 关键接口建议加 `match_schema` 做**契约校验**，防后端悄悄改字段。
- 场景级测试：除接口返回外，**用 `DBClient` 查库二次确认**数据真的对。

---

## 8. 数据 / 配置规范
- **非敏感配置**（地址、端口、超时）→ `config/config.yaml`，分环境。
- **敏感信息**（账号、密码、token、webhook）→ `.env`（不入库），示例放 `.env.example`。
- 多组数据用**数据驱动**：放 `data/*.yaml`，用 `parametrize` + `load_yaml`。
- 切环境用 `ENV=dev/test/prod`，不要在代码里写死。

---

## 9. 基础设施客户端规范（`clients/`）
- 第三方库**懒加载**（在 `__init__`/方法内 import），未安装不影响其它用例。
- 提供**上下文管理器**（`__enter__/__exit__`），用完自动关闭连接。
- 统一用 `utils.logger` 打日志。
- 连接信息从 `settings` 读，敏感部分来自 `.env`。
- 较重依赖（ES/Kafka/MQ）放 `requirements-optional.txt`，用到再装。

---

## 10. 提交规范（Git）
- 分支：从 `main` 切功能分支，**不直推 main**。
- commit message 用约定式前缀：
  - `feat:` 新功能　`fix:` 修复　`docs:` 文档　`test:` 用例　`refactor:` 重构　`chore:` 杂项
  - 示例：`test(web): 新增搜索页 PO 用例`
- 提交前确保新增 `.py` 通过 `python -m py_compile` 语法校验。

---

## 11. 依赖管理
- 核心、轻量依赖 → `requirements.txt`。
- 可选、较重依赖（中间件）→ `requirements-optional.txt`，注释状态，用到再开。
- 建议用虚拟环境 `.venv` 隔离，避免与本机其它库冲突。

---

> 这些规范已内置到 `recording-to-po` Skill：把录制裸代码交给 AI 时，会自动按本规范产出 PO 用例。
