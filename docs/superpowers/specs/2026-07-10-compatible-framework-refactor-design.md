# 自动化测试框架兼容式重构设计

## 1. 背景

当前仓库已经具备 API、Web、App 三端自动化测试的基本分层，但默认执行依赖外部示例站点，配置和文档存在不一致，请求日志可能记录敏感信息，生产环境缺少强制保护，框架自身也没有离线自测。

本次重构面向第一次接触自动化测试的使用者。目标是在保留现有目录结构和主要用例写法的前提下，让框架默认安全、首次运行稳定、错误提示清晰，并具备持续维护所需的自动化质量保障。

## 2. 目标

- 保留 `api/`、`pages/`、`screens/`、`testcases/` 等现有目录和主要导入方式。
- 保留 `UserApi()`、`LoginPage(page)`、`LoginScreen(driver)` 等现有调用方式。
- 提供跨平台中文命令入口，覆盖环境检查、框架自测和真实业务测试。
- 默认测试不访问公网、数据库、Redis、Appium 或占位业务地址。
- 对请求日志和 Allure 附件中的敏感数据强制脱敏。
- 默认禁止生产环境测试，显式授权后仍只允许运行 `prod_safe` 用例。
- 统一配置优先级和校验逻辑，错误信息直接给出修复方法。
- 为核心框架代码建立离线单元测试和 CI 质量门禁。
- 提供一份从新项目零基础落地到 CI 的完整中文指南。

## 3. 非目标

- 不拆分为独立发布的 Python 框架包和业务测试仓库。
- 不引入数据库迁移系统、测试管理平台或分布式设备农场。
- 不强制启用严格 mypy，不要求新人先理解复杂类型系统。
- 不改变现有 Page Object、Screen Object 和 API 业务封装的核心模式。
- 不自动操作真实生产环境，也不提供绕过生产保护的隐式入口。

## 4. 目录设计

保留现有业务目录，新增以下内容：

```text
examples/                         外部站点和占位业务示例，默认不收集
tests/framework/                  完全离线的框架单元测试
scripts/automation.py             跨平台统一命令入口
docs/新项目从0开始.md              零基础落地指南
docs/superpowers/specs/           设计文档
docs/superpowers/plans/           实施计划
pyproject.toml                    Python、pytest、ruff 等工程配置
```

`testcases/` 只保留真实项目业务用例。当前依赖 `example.com`、百度或占位 App 的演示用例迁移到 `examples/`，从而保证默认测试入口不访问外部系统。

## 5. 配置设计

配置优先级固定为：

```text
命令行参数 > 环境变量 > config/config.yaml > 代码默认值
```

配置加载继续兼容全局 `settings`，同时提供可独立实例化的设置对象，便于单元测试。启动时校验：

- 环境名称必须存在。
- API 和 Web 地址必须是合法的 HTTP/HTTPS URL。
- timeout 必须是正数。
- Web 浏览器只能是 Chromium、Firefox 或 WebKit。
- App 平台只能是 Android 或 iOS。
- 运行需要登录的用例时，必须提供对应账号。

命令行提供 `--env`，避免用户在 PowerShell、CMD 和 Bash 中分别学习不同的环境变量语法。

## 6. 统一命令入口

提供以下命令：

```bash
python scripts/automation.py doctor
python scripts/automation.py self-test
python scripts/automation.py test --type api --env uat
python scripts/automation.py test --type web --env uat --headed
python scripts/automation.py test --marker smoke --env uat
```

行为约定：

- `doctor` 检查 Python 版本、虚拟环境、依赖、配置文件、Playwright 和 Appium 基础条件，输出中文修复建议。
- `self-test` 只运行 `tests/framework/`，不得访问任何外部系统。
- `test` 运行 `testcases/` 下的真实业务测试。
- 命令返回 pytest 的退出码，CI 可以直接判断成功或失败。
- `--headed`、`--browser`、`--slowmo`、`--tracing` 等命令行选项优先于 YAML。

## 7. 安全设计

### 7.1 敏感数据脱敏

新增统一脱敏模块，递归处理字典、列表、字符串、请求头、查询参数和 URL。默认敏感键包括：

```text
password, passwd, pwd, token, access_token, refresh_token,
authorization, cookie, secret, mobile, phone, id_card
```

日志和 Allure 附件必须复用同一个脱敏入口。JSON 响应附件设置最大长度，避免大报文拖垮报告。脱敏不可通过普通配置关闭。

### 7.2 生产环境保护

- 发现 `ENV=prod` 或 `--env prod` 时默认终止测试。
- 只有同时传入 `--allow-prod` 并设置 `ALLOW_PROD_TESTS=1` 才进入生产测试模式。
- 生产测试模式自动追加 `-m prod_safe`，其他用例不收集。
- 写接口、数据库清理和缓存写入的通用 fixture 在生产模式下拒绝执行。
- 文档明确要求生产环境使用只读账号。

## 8. HTTP 与资源生命周期

`HttpClient` 增加：

- `close()`、`__enter__()`、`__exit__()`。
- 请求异常日志和 Allure 诊断附件。
- headers、params、JSON body 和响应数据的统一脱敏。
- 明确的 URL 拼接规则。
- 可注入 Session，方便离线测试。

框架不默认重试所有 HTTP 请求。业务方需要重试时，只允许对明确幂等的调用配置重试策略。

所有 fixture 使用 `yield` 或上下文管理器释放 HttpClient、DB、Redis 和 Appium driver。清理任务失败时汇总错误并让 teardown 失败，避免数据污染被忽略。

## 9. Web 与 App 行为

### 9.1 Web

- pytest 的 browser fixture 读取 YAML 浏览器配置。
- 命令行 Playwright 参数优先于 YAML。
- `trace: true` 映射为失败保留 trace。
- 失败截图由 pytest-playwright 负责时不重复截图，否则使用现有 Allure 截图兜底。
- 保持现有 BasePage 方法兼容，本次不大规模重写业务 Page Object。

### 9.2 App

- 关闭 Appium 隐式等待，只保留 BaseScreen 的显式等待。
- driver fixture 无论用例成功、失败或 setup 异常都尽力释放资源。
- App 示例继续默认不执行，只有设备和配置就绪后显式运行。

## 10. 测试设计

新增 `tests/framework/`，至少覆盖：

- 配置优先级、无效环境、无效 URL 和缺少必需配置。
- 嵌套数据、headers、URL 和字符串脱敏。
- HttpClient URL 拼接、超时、附件脱敏、异常处理和资源关闭。
- 生产环境默认阻断及双重授权。
- 清理任务逆序执行和失败汇总。
- 数据文件加载和空 Excel 的可理解错误。
- retry 参数校验、函数元数据保留和最终失败行为。
- JUnit 汇总逻辑。
- Web 启动参数的命令行优先级。

每个行为修改遵循测试先行：先写失败测试并确认失败原因，再写最小实现使其通过。

## 11. 依赖与质量门禁

使用 `pyproject.toml` 声明 Python 3.10 至 3.12，并集中配置 pytest 和 ruff。依赖按用途拆分为 API、Web、App、基础设施和开发工具，同时保留一次安装全部依赖的路径。

CI 至少执行：

```text
ruff format --check
ruff check
pytest tests/framework
pytest --collect-only testcases
```

PR 默认执行框架自测和业务 smoke；定时流水线执行 regression。全局 `--reruns 1` 删除，只有显式 `flaky` 用例允许重试。

## 12. 文档设计

新增 `docs/新项目从0开始.md`，按实际操作顺序覆盖：

1. 安装 Python、Git 和编辑器。
2. 创建并激活虚拟环境。
3. 按 API、Web、App 场景安装依赖。
4. 运行 doctor 和 self-test。
5. 复制环境配置和填写 `.env`。
6. 根据 Swagger 编写第一个 API 封装和测试。
7. 根据真实页面编写第一个 Page Object 和 Web 测试。
8. Appium 环境、Screen Object 和 App 测试入口。
9. 测试数据、fixture、清理、marker 和报告。
10. 常见错误定位。
11. GitHub、GitLab、Jenkins 接入。
12. 新项目上线前检查清单。

所有示例命令同时给出 Windows PowerShell 和通用 Python 入口，避免依赖 Make。

## 13. 兼容性

- 现有业务模块和 Page/Screen 类无需迁移目录。
- `from config.settings import settings` 继续可用。
- 现有 `pytest -m api` 等命令仍可用，但推荐统一命令入口。
- 删除默认全局重试属于有意行为变化。
- 默认 pytest 只运行框架自测属于有意行为变化，真实业务测试通过统一命令或显式目录运行。

## 14. 验收标准

- 全新虚拟环境按文档操作后，`doctor` 能给出准确检查结果。
- `self-test` 在断网情况下全部通过。
- 默认 pytest 不访问外部系统。
- 敏感字段不会以明文出现在日志或 Allure 附件中。
- 未双重授权时无法运行生产测试。
- `--headed` 和 `--browser` 能覆盖 YAML 配置。
- API、DB、Redis 和 Appium 资源均有确定的释放路径。
- Jenkins 并行任务使用独立 Allure 结果目录。
- README 与从零指南中的命令可直接执行。
- Python 3.10、3.11、3.12 的框架自测均通过。
