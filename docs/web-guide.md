# Web UI 自动化测试 手把手指南（小白版）

本指南假设你**从零开始**。Web 测试 = 用代码自动操作浏览器（打开页面、输入、点击、断言），就像把你手点页面的过程录下来重放。框架用的是 **Playwright**（比 Selenium 更快更稳、自带等待）。

---

## 0. 先理解：Web 测试在测什么？

> 打开登录页 → 输入用户名密码 → 点登录按钮 → 断言"头像出现"（即登录成功）。

链路：

```
你的测试用例 → LoginPage(页面对象) → Playwright 操作浏览器 → 真实页面 → 用 expect 断言
```

框架里 `pages/base_page.py`（页面操作封装）、`conftest.py`（浏览器配置）都已写好，你主要写**页面对象**和**用例**。

> ⚠️ Web 自动化原则：**少而精**。UI 容易变，只测核心链路（登录、下单等），细节交给接口测试。

---

## 1. 装环境（只需一次）

```bash
# 拉代码
git clone https://github.com/panchao9527/web-api-app-autotest.git
cd web-api-app-autotest

# 虚拟环境 + 依赖
python -m venv .venv
source .venv/Scripts/activate      # Git Bash; PowerShell 用 .venv\Scripts\activate
pip install -r requirements.txt

# 关键: 装浏览器内核(Playwright 自带浏览器)
playwright install chromium
```

> `playwright install chromium` 会下载一个测试专用的 Chromium，**必须执行**，否则跑不起来。

---

## 2. 配置：网址 + 浏览器行为

### 2.1 改网址 `config/config.yaml`

```yaml
test:
  web_base_url: "https://你的网站.com"    # ← 改这里
```

### 2.2 浏览器行为（同文件的 web 段）

```yaml
web:
  browser: "chromium"     # chromium / firefox / webkit
  headless: true          # true=后台不显示窗口(CI用); 调试时改 false 能看到浏览器操作
  slow_mo: 0              # 调试时改 500，每步放慢500毫秒，看清在干嘛
  viewport:
    width: 1920
    height: 1080
  trace: true             # 失败时保留操作轨迹，可回放
```

> **新手调试建议**：先把 `headless: false`、`slow_mo: 500`，这样能**亲眼看到**浏览器自动操作，方便排查。调通后再改回 `headless: true`。

---

## 3. 核心概念：PO 模式（页面对象）

把"页面上的元素"和"操作"封装进一个类，用例只调方法、不碰元素。**好处：页面改版只改一处。**

看 `pages/login_page.py`：

```python
class LoginPage(BasePage):
    # ① 定位器集中放顶部(优先用 data-testid 这种稳定属性)
    URL = "/login"
    INPUT_USERNAME = "[data-testid='username']"
    INPUT_PASSWORD = "[data-testid='password']"
    BTN_SUBMIT     = "[data-testid='login-btn']"
    USER_AVATAR    = "[data-testid='user-avatar']"

    # ② 业务方法对外暴露语义化操作
    @allure.step("执行登录: {username}")
    def login(self, username, password):
        self.open(self.URL)
        self.fill(self.INPUT_USERNAME, username)
        self.fill(self.INPUT_PASSWORD, password)
        self.click(self.BTN_SUBMIT)
```

`BasePage`（基类）已封装这些常用操作：

| 方法 | 作用 |
|------|------|
| `self.open(path)` | 打开页面 |
| `self.click(选择器)` | 点击 |
| `self.fill(选择器, 文本)` | 输入 |
| `self.text(选择器)` | 取文本 |
| `self.expect_visible(选择器)` | 断言元素可见(自动等待) |
| `self.expect_text(选择器, 文本)` | 断言文本包含 |

> Playwright **自带智能等待**——元素没出现会自动等，所以**不要写 `sleep`**。

---

## 4. 怎么获取元素选择器（最关键）

不用记复杂语法，浏览器帮你生成：

### 方法 A：浏览器开发者工具（简单）
1. 在页面上**右键要操作的元素 → 检查**
2. 在 Elements 面板看它的属性，优先找 `data-testid`、`id`
3. 写成选择器：
   - 有 id：`#login-btn`
   - 有 data-testid：`[data-testid='login-btn']`
   - 按文字找按钮：`text=登录`

### 方法 B：Playwright 录制（强烈推荐，自动生成代码）
```bash
playwright codegen https://你的网站.com
```
会打开浏览器，**你手点操作，它自动生成对应代码和选择器**！把生成的选择器和操作整理进页面对象即可。

**选择器稳定性优先级：**
```
data-testid / id  >  role/text  >  css class  >  xpath(尽量避免)
```

---

## 5. 动手写你的第一个 Web 用例

假设测"搜索功能"：打开首页 → 搜索框输入"手机" → 点搜索 → 断言出现结果。

### 第 1 步：写页面对象

```python
# pages/search_page.py
import allure
from pages.base_page import BasePage

class SearchPage(BasePage):
    URL          = "/"
    INPUT_SEARCH = "[data-testid='search-input']"
    BTN_SEARCH   = "[data-testid='search-btn']"
    RESULT_LIST  = "[data-testid='result-list']"

    @allure.step("搜索: {keyword}")
    def search(self, keyword):
        self.open(self.URL)
        self.fill(self.INPUT_SEARCH, keyword)
        self.click(self.BTN_SEARCH)
```

### 第 2 步：写用例

```python
# testcases/web/test_search_web.py
import allure, pytest
from playwright.sync_api import Page
from pages.search_page import SearchPage

@allure.feature("搜索页面")
@pytest.mark.web
class TestSearchWeb:

    @pytest.mark.smoke
    def test_search(self, page: Page):       # page 由框架自动提供
        sp = SearchPage(page)
        sp.search("手机")
        sp.expect_visible(SearchPage.RESULT_LIST)   # 断言结果列表出现
```

> `page` 这个参数是 Playwright 的浏览器页面对象，**框架已自动创建/关闭、失败自动截图**，你直接用就行。

### 第 3 步：运行

```bash
pytest testcases/web/test_search_web.py
```

---

## 6. 运行 & 筛选

```bash
pytest -m web                 # 只跑 Web 用例
pytest -m "web and smoke"     # Web 冒烟
pytest testcases/web/test_login_web.py    # 单个文件
pytest -m web --headed        # 显示浏览器窗口跑(临时调试，覆盖 headless)
```

---

## 7. 看报告 & 调试

### Allure 报告（含失败截图）
```bash
allure serve reports/allure-results
```
Web 用例**失败时框架会自动截图**附到报告里，一眼看出卡在哪。

### Playwright Trace（强力调试）
`config.yaml` 里 `trace: true` 时，失败会留下轨迹文件，可逐帧回放：
```bash
playwright show-trace 轨迹文件路径.zip
```

### 调试三板斧
1. `headless: false` + `slow_mo: 500` → 亲眼看操作
2. `pytest --headed` → 临时显示窗口
3. 看 Allure 里的失败截图 / trace

---

## 8. 常见问题

| 问题 | 应对 |
|------|------|
| `playwright install` 没做 | 跑前必须 `playwright install chromium` |
| 元素找不到/超时 | 选择器写错；用 `codegen` 或开发者工具重新取；确认元素真的会出现 |
| 跑得太快看不清 | `headless: false` + `slow_mo: 500` |
| 登录态每个用例都重来 | 把登录抽成 fixture 复用(进阶) |
| 选择器经常失效 | 优先用 `data-testid`，推动开发给关键元素加这个属性 |
| 页面加载慢导致失败 | Playwright 自带等待；必要时用 `expect_visible` 等关键元素 |

---

## 一句话总结

> 框架已封装好 **浏览器管理 + 页面操作(BasePage) + 自动截图/trace + 报告**；
> 你的工作 = 在 `pages/` 写页面对象（用 `codegen` 取选择器）、在 `testcases/web/` 写用例。
> 记住：**UI 测试少而精，只测核心链路。**
