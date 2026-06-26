# Appium 环境搭建指南（App 自动化）

App 自动化的链路：

```
测试用例 → app_driver(fixture) → Appium Server → 手机/模拟器上的 App
```

框架代码（`screens/`、`core/app_driver.py`、`app_driver` fixture）已写好，你需要做的是：
**① 搭好 Appium 环境 → ② 用 Appium Inspector 抓定位器 → ③ 写 Screen 对象和用例**。

本指南以 **Windows + Android** 为主线（iOS 见文末，仅 macOS 支持）。

---

## 一、Android 环境搭建（Windows）

### 1. 安装 JDK (11+)

1. 下载安装 [Temurin / Oracle JDK 11+](https://adoptium.net/)
2. 配置环境变量：
   - 新建系统变量 `JAVA_HOME` = JDK 安装目录（如 `C:\Program Files\Eclipse Adoptium\jdk-17`）
   - 在 `Path` 中追加 `%JAVA_HOME%\bin`
3. 验证：
   ```bash
   java -version
   ```

### 2. 安装 Android SDK（推荐装 Android Studio）

1. 下载安装 [Android Studio](https://developer.android.com/studio)
2. 首次启动按引导安装 SDK（默认目录如 `C:\Users\你\AppData\Local\Android\Sdk`）
3. 配置环境变量：
   - 新建 `ANDROID_HOME` = SDK 目录
   - 在 `Path` 中追加：
     - `%ANDROID_HOME%\platform-tools`（提供 adb）
     - `%ANDROID_HOME%\emulator`
     - `%ANDROID_HOME%\tools` 和 `%ANDROID_HOME%\tools\bin`
4. 验证：
   ```bash
   adb version
   ```

### 3. 准备一台设备（二选一）

**A. 模拟器（无真机时用）**
- Android Studio → Device Manager → Create Device → 选机型 + 系统镜像 → 启动
- 或命令行：
  ```bash
  emulator -list-avds        # 查看已创建的模拟器
  emulator -avd <名称>        # 启动
  ```

**B. 真机**
- 手机「设置 → 关于手机」连点 7 次版本号开启「开发者选项」
- 开启「USB 调试」，USB 连接电脑，手机上点「允许调试」

**验证设备连通：**
```bash
adb devices
# 出现 emulator-5554  device  或  你的设备序列号  device 即成功
```

### 4. 安装 Node.js + Appium Server

1. 安装 [Node.js LTS](https://nodejs.org/)（18+）
2. 安装 Appium 与 UiAutomator2 驱动：
   ```bash
   npm install -g appium
   appium driver install uiautomator2
   ```
3. （可选）安装体检工具，自动检查环境是否齐全：
   ```bash
   npm install -g appium-doctor
   appium-doctor --android
   ```
4. 启动 Appium Server：
   ```bash
   appium
   # 默认监听 http://127.0.0.1:4723 —— 与 config.yaml 的 appium_server 对应
   ```

### 5. 安装 Appium Inspector（抓元素定位的关键工具）

- 下载 [Appium Inspector](https://github.com/appium/appium-inspector/releases)（图形界面）

---

## 二、获取 App 的 appPackage / appActivity

启动目标 App 后，在命令行执行：

```bash
adb shell dumpsys window | findstr mCurrentFocus     # Windows
# 输出形如:  mCurrentFocus=...{ ... com.example.app/com.example.app.MainActivity}
```

`/` 前是 **appPackage**，`/` 后是 **appActivity**。

---

## 三、配置 `config/config.yaml`

把上一步拿到的信息填进 app 段：

```yaml
app:
  appium_server: "http://127.0.0.1:4723"
  platform: "Android"
  android:
    platformName: "Android"
    automationName: "UiAutomator2"
    deviceName: "emulator-5554"        # adb devices 看到的名字
    appPackage: "com.example.app"      # 你的包名
    appActivity: ".MainActivity"       # 你的启动 Activity
    noReset: true                      # 不重装 App，提速
    # 常用可选项(按需开启):
    # autoGrantPermissions: true       # 自动授予权限，避免权限弹窗打断
    # appWaitActivity: "*"             # 启动页 Activity 不固定时用
    # newCommandTimeout: 120           # 空闲超时(秒)
```

---

## 四、用 Appium Inspector 抓定位器

1. 确保 Appium Server 已启动、`adb devices` 能看到设备
2. 打开 Appium Inspector，填入 capabilities（和 config.yaml 一致），点 **Start Session**
3. 它会镜像手机画面，**点任意控件**，右侧面板显示该控件的 `resource-id` / `content-desc` / `xpath`
4. 把这些值写进你的 Screen 对象

**定位优先级（稳定性从高到低）：**

```
resource-id  >  accessibility id(content-desc)  >  xpath(尽量避免)
```

---

## 五、写 Screen 对象与用例

### Screen 对象（参考 `screens/login_screen.py`）

```python
# screens/mine_screen.py
import allure
from screens.base_screen import BaseScreen

class MineScreen(BaseScreen):
    # 定位器集中放顶部，App 改版只改这里
    BTN_PROFILE  = (BaseScreen.ID, "com.example.app:id/btn_profile")
    TXT_NICKNAME = (BaseScreen.ID, "com.example.app:id/tv_nickname")
    BTN_LOGOUT   = (BaseScreen.ACCESSIBILITY_ID, "logout")

    @allure.step("进入个人资料")
    def open_profile(self):
        self.click(*self.BTN_PROFILE)

    def get_nickname(self) -> str:
        return self.text(*self.TXT_NICKNAME)
```

> `BaseScreen` 已封装 `find / click / input / text / is_displayed / swipe_up`，
> 其中 `find()` 用**显式等待**，所以**不要写 `sleep`**——这是 App 稳定性的关键。

### 用例（参考 `testcases/app/test_login_app.py`）

```python
# testcases/app/test_mine_app.py
import allure, pytest
from screens.login_screen import LoginScreen
from screens.mine_screen import MineScreen

@allure.feature("App 个人中心")
@pytest.mark.app
class TestMineApp:

    @pytest.mark.smoke
    def test_view_nickname(self, app_driver, env_settings):
        # app_driver fixture 已自动创建/退出 driver、失败自动截图
        LoginScreen(app_driver).login(env_settings.username, env_settings.password)
        mine = MineScreen(app_driver)
        mine.open_profile()
        assert mine.get_nickname() != ""
```

---

## 六、运行

```bash
# 前置: Appium Server 已启动 + adb devices 能看到设备
pytest -m app                                # 跑所有 App 用例
pytest testcases/app/test_login_app.py       # 跑单个文件
```

> `testcases/app/test_login_app.py` 顶部有 `@pytest.mark.skip`，
> 环境就绪、定位器填好后，**删掉那行 skip** 即可运行。

---

## 七、常见问题排查

| 问题 | 原因 / 应对 |
|------|------------|
| `adb devices` 看不到设备 | 真机未开 USB 调试 / 驱动未装 / 数据线问题；模拟器未启动 |
| Session 启动失败 | capabilities 写错（包名/Activity/deviceName）；Appium Server 未启动 |
| 找不到元素 / 超时 | 定位器失效，用 Inspector 重新抓；元素在屏幕外用 `swipe_up()` 滚动 |
| 权限/广告弹窗打断 | capabilities 加 `autoGrantPermissions: true` |
| 启动页 Activity 报错 | 加 `appWaitActivity: "*"` |
| 每次都重装 App 很慢 | 确认 `noReset: true` |
| 定位器频繁失效 | 优先用 `resource-id`，推动开发给关键控件加稳定 id |

---

## 八、iOS 说明（仅 macOS）

iOS 需要 **Mac + Xcode**，驱动用 XCUITest：

```bash
appium driver install xcuitest
```

`config/config.yaml` 把 `platform` 改为 `iOS`，填 `ios` 段的 `bundleId` / `deviceName` / `platformVersion`。
其余用例写法与 Android 一致（框架已自动按 platform 选择驱动，见 `core/app_driver.py`）。

---

## 链路回顾

> 框架的 App 部分（driver 管理、PO 基类、自动截图、`app_driver` fixture）**已经现成**；
> 你的核心工作 = **搭 Appium 环境** + **用 Inspector 抓定位器写进 Screen 对象**。
