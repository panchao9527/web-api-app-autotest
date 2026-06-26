---
name: recording-to-po
description: 把录制工具(Playwright codegen / Appium Inspector Recorder)产出的裸代码，重构成本框架的 Page Object(PO) 模式 —— 自动判断 Web/App，生成 pages/ 或 screens/ 页面对象 + testcases/ 用例，遵循项目分层规范，并提交推送。当用户提供"录制的裸代码""codegen 生成的代码""Appium 录制结果"并希望整理成规范用例时使用。
---

# Recording → PO 重构工作流

把用户提供的**录制裸代码**重构成本框架规范的 PO 模式用例。

## 触发场景

用户粘贴了 Playwright codegen 或 Appium Inspector 录制出来的裸代码，并希望整理成框架规范的用例。典型说法："帮我把这段录制重构成 PO""用 recording-to-po 整理这个"。

## 第 0 步：判断是 Web 还是 App

根据裸代码特征自动识别：

- **Web (Playwright)**：出现 `page.goto` / `page.click` / `page.fill` / `page.get_by_*` / `locator(...)`
- **App (Appium)**：出现 `driver.find_element` / `AppiumBy.*` / `send_keys` / `resource-id` / `content-desc`

如无法确定，向用户确认一次。

## 第 1 步：提取定位器与操作

从裸代码里拆出两类信息：
1. **定位器**（选择器 / resource-id / accessibility id / xpath）
2. **操作序列**（打开、输入、点击、断言等）

并为这段流程归纳一个**业务语义名**（如 login、search、createOrder）。

## 第 2 步：生成 Page Object / Screen Object

### Web → `pages/<name>_page.py`（继承 `BasePage`）

- 定位器集中声明在类顶部，命名用大写常量（如 `INPUT_USERNAME`、`BTN_SUBMIT`）
- 选择器优先级：`data-testid` / `id` > role/text > css > xpath（尽量不用 xpath）
- 操作封装成**语义化业务方法**，方法加 `@allure.step(...)`
- 只调用 `BasePage` 已有方法：`open / click / fill / text / is_visible / expect_visible / expect_text`
- **不要写 sleep**（Playwright 自带等待）

参考已有 `pages/login_page.py` 的写法保持一致。

### App → `screens/<name>_screen.py`（继承 `BaseScreen`）

- 定位器写成元组：`(BaseScreen.ID, "包名:id/xxx")`
- 定位别名映射：`BaseScreen.ID`=resource-id，`BaseScreen.ACCESSIBILITY_ID`=content-desc，`BaseScreen.XPATH`=xpath，`BaseScreen.ANDROID_UIAUTOMATOR`=UiAutomator
- 定位优先级：resource-id > accessibility id > xpath
- 操作封装成业务方法，加 `@allure.step(...)`
- 只调用 `BaseScreen` 已有方法：`find / click / input / text / is_displayed / swipe_up`（已含显式等待，不要写 sleep）

参考已有 `screens/login_screen.py`。

## 第 3 步：生成用例

### Web → `testcases/web/test_<name>_web.py`

```python
import allure, pytest
from playwright.sync_api import Page
from pages.<name>_page import <Name>Page

@allure.feature("...")
@pytest.mark.web
class Test<Name>Web:
    @pytest.mark.smoke           # 核心链路标 smoke
    def test_<action>(self, page: Page):
        po = <Name>Page(page)
        po.<业务方法>(...)
        po.expect_visible(<Name>Page.<关键元素>)   # 用可断言的"成功标志"收尾
```

### App → `testcases/app/test_<name>_app.py`

```python
import allure, pytest
from screens.<name>_screen import <Name>Screen

@allure.feature("...")
@pytest.mark.app
class Test<Name>App:
    @pytest.mark.smoke
    def test_<action>(self, app_driver, env_settings):
        screen = <Name>Screen(app_driver)
        screen.<业务方法>(...)
        assert screen.is_displayed(*<Name>Screen.<关键元素>)
```

> App 用例若环境未就绪，可在类上加 `@pytest.mark.skip(reason="需连接设备")`，并提示用户就绪后移除。

## 第 4 步：规范校验

- 用例**只调业务方法**，不出现裸 `page.`/`driver.` 调用（细节都在 PO 里）
- 写死的账号密码等改用 `env_settings`（来自 `.env`）
- 合理打标记：`smoke`/`regression` + `web`/`app` + 可选 `p0/p1/p2`
- 用 `python -m py_compile` 校验新文件语法通过

## 第 5 步：提交并推送

- 在已克隆的仓库目录内操作（如 `/projects/sandbox/web-api-app-autotest`）
- 新建语义化分支或复用当前工作分支（不要直接推 main，除非用户要求）
- commit message 用约定式：`test(web|app): 新增 <name> PO 用例`
- 用平台的 `push_to_remote` 工具推送（不要用裸 `git push`）
- 推送后给用户分支链接和 PR 创建链接

## 输出给用户

- 列出新增/修改的文件
- 说明哪些是"成功标志"断言、用了哪些标记
- 提醒：示例中占位的 URL/选择器需替换成真实值；语法已校验，真实运行需对应环境

## 框架约定速查

- 配置：`config/config.yaml`（多环境 + web/app 段）；敏感信息 `.env`
- 断言（API 用）：`core/assertions.py` 的 `Assert`
- Web 基类：`pages/base_page.py` `BasePage`
- App 基类：`screens/base_screen.py` `BaseScreen`
- 全局 fixture：`page`(pytest-playwright)、`app_driver`、`env_settings`、`logged_in_client`
- 失败自动截图已在 `conftest.py` 配好，无需在用例里处理
