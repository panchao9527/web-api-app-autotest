# 全栈自动化测试框架 (API + Web + App)

基于 **Python + Pytest** 的统一自动化测试框架，三端共用核心层，一套工程同时管理 **接口测试、Web UI 测试、App 测试**。

---

## ✨ 特性

- **三端统一**：接口(requests) / Web(Playwright) / App(Appium) 共用配置、日志、报告
- **分层架构**：核心层与业务层解耦，UI/接口改动只改一处
- **PO 模式**：Web 用 Page Object，App 用 Screen Object，用例只写业务语义
- **数据驱动**：yaml / json / excel 驱动，一套逻辑跑多组数据
- **多环境**：sit / uat / prod 一键切换，敏感信息走 `.env`
- **Allure 报告**：失败自动截图、请求/响应详情自动附加
- **CI/CD**：GitHub Actions 自动跑 + 每日定时回归 + 报告发布
- **失败重试**：过滤偶发抖动，提升稳定性

---

## 📁 目录结构

```
.
├── config/              # 配置层
│   ├── config.yaml      #   多环境 + 三端配置
│   └── settings.py      #   配置加载器(单例 settings)
├── core/                # 核心层(与业务无关，最稳定)
│   ├── http_client.py   #   HTTP 客户端封装
│   ├── assertions.py    #   自定义断言库
│   ├── web_driver.py    #   Playwright 启动参数
│   └── app_driver.py    #   Appium driver 工厂
├── api/                 # 接口业务层(按模块封装)
│   ├── base_api.py
│   └── user_api.py
├── pages/               # Web 页面对象(PO 模式)
│   ├── base_page.py
│   └── login_page.py
├── screens/             # App 页面对象(移动端 PO 模式)
│   ├── base_screen.py
│   └── login_screen.py
├── clients/             # 测试基础设施客户端(DB/Redis/通知)
│   ├── db_client.py     #   MySQL 查库断言/数据准备清理
│   ├── redis_client.py  #   Redis 缓存校验
│   └── notify.py        #   钉钉/企微 机器人通知
├── testcases/           # 测试用例(只写业务逻辑)
│   ├── api/
│   ├── web/
│   └── app/
├── data/                # 测试数据(数据驱动)
│   └── login_data.yaml
├── fixtures/            # 共享 fixture(登录态复用、数据准备清理)
│   └── api_fixtures.py
├── utils/               # 工具(日志、数据加载、随机数据)
├── docs/                # 使用文档(api/web/appium/infra-clients 指南)
├── reports/             # Allure 报告输出
├── conftest.py          # 全局 hook + fixture(失败自动截图)
├── pytest.ini           # pytest 配置 + 用例标记
├── requirements.txt          # 核心依赖(轻量)
├── requirements-optional.txt # 可选依赖(ES/Kafka/MQ 等，用到再装)
├── Makefile             # 常用命令快捷方式
└── .github/workflows/   # CI/CD
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium        # Web 测试需要
# App 测试另需: 安装 Appium server + Android SDK / Xcode
#   详细步骤见 docs/appium-setup.md
```

> 也可直接 `make install`
>
> 💡 建议用虚拟环境隔离依赖，避免与本机其它包(如 httprunner)冲突：
> ```bash
> python -m venv .venv
> source .venv/Scripts/activate    # Git Bash;  PowerShell 用 .venv\Scripts\activate
> pip install -r requirements.txt
> ```

### 2. 配置环境

```bash
cp .env.example .env               # 填入真实账号/token
```

编辑 `config/config.yaml` 把 `example.com` 换成你的真实地址。

### 3. 运行用例

```bash
make test          # 全部用例
make api           # 只跑接口
make web           # 只跑 Web
make smoke         # 只跑冒烟(P0核心链路)
make parallel      # 4 进程并发加速

# 或直接用 pytest
ENV=uat pytest -m api                     # 指定环境跑接口
pytest -m "smoke and api"                 # 组合标记
pytest testcases/api/test_login_api.py    # 跑单个文件
```

### 4. 查看报告

```bash
make report        # 本地生成并打开 Allure 报告
```

---

## 🏷️ 用例标记(markers)

| 标记 | 含义 | 示例 |
|------|------|------|
| `smoke` | 冒烟用例(P0核心链路) | `pytest -m smoke` |
| `regression` | 回归用例 | `pytest -m regression` |
| `api` / `web` / `app` | 按端筛选 | `pytest -m web` |
| `p0` / `p1` / `p2` | 优先级 | `pytest -m p0` |

---

## 🧩 如何新增用例

> 📘 **小白手把手教程**（强烈推荐先看）：
> - 接口测试：**[docs/api-guide.md](docs/api-guide.md)**
> - Web 测试：**[docs/web-guide.md](docs/web-guide.md)**
> - App 测试：**[docs/appium-setup.md](docs/appium-setup.md)**
> - 基础设施客户端(DB/Redis/通知)：**[docs/infra-clients.md](docs/infra-clients.md)**
> - 工具与 Fixture 速查：**[docs/utils-fixtures.md](docs/utils-fixtures.md)**
> - 团队代码规范：**[docs/coding-standards.md](docs/coding-standards.md)**
> - UI vs 接口 测试分工策略：**[docs/ui-api-strategy.md](docs/ui-api-strategy.md)**
> - CI/CD 集成(GitHub/GitLab/Jenkins)：**[docs/ci.md](docs/ci.md)**
> - 新公司落地指南(改哪里/要什么权限)：**[docs/onboarding.md](docs/onboarding.md)**

### 新增接口测试
1. 在 `api/` 下封装接口调用(继承 `BaseApi`)
2. 在 `data/` 下准备数据(可选，数据驱动)
3. 在 `testcases/api/` 下写用例，调用 api 方法 + `Assert` 断言

### 新增 Web 测试
1. 在 `pages/` 下新建页面对象(继承 `BasePage`)，定位器集中在类顶部
2. 在 `testcases/web/` 下写用例，只调页面的业务方法

### 新增 App 测试
1. 在 `screens/` 下新建页面对象(继承 `BaseScreen`)
2. 在 `testcases/app/` 下写用例，用 `app_driver` fixture

> 📱 **App 自动化首次上手**：完整的 Appium 环境搭建、获取包名/Activity、用 Appium Inspector 抓元素定位、写 Screen 对象与用例的详细步骤，见 **[docs/appium-setup.md](docs/appium-setup.md)**。

> **定位原则**：Web 优先 `data-testid`，App 优先 `resource-id`/`accessibility-id`，避免脆弱的绝对 xpath。

---

## 🤖 结合 AI 工具写用例(提效)

1. **用例设计**：把需求/接口文档丢给 AI，让它用等价类/边界值列出测试场景 → 填进 `data/*.yaml`
2. **生成接口封装**：把 Swagger/OpenAPI 给 AI，自动生成 `api/` 下的封装类
3. **重构录制脚本**：Playwright `codegen` 录制后，让 AI 重构成 PO 模式
4. **造数据**：`utils/random_data.py` 已集成 Faker，配合 AI 设计数据规则

> ⚠️ AI 生成的代码必须 review，框架原理要自己懂，否则会产出难维护的用例。

### 🛠️ Skill：把"录制/定义"一键变成规范用例

仓库内置了 Kiro Skill（`.kiro/skills/`），在 Kiro 里把素材交给 AI、说一句话即可按框架规范生成用例并提交：

| Skill | 输入 | 产出 |
|-------|------|------|
| **recording-to-po** | codegen / Appium Inspector 录制的裸代码 | Web/App 的 `pages`或`screens` + 用例 |
| **api-test-from-spec** | Swagger / Controller 代码 / 接口文档 | `api/` 封装 + 单接口用例(正常/必填/边界/异常) |
| **api-scenario-test** | 业务流程描述 / 接口调用序列 | 接口场景级用例(共享登录态+传参+查库核对) |

用法示例：
> "用 api-scenario-test 写一条流程：登录 → 创建订单 → 支付 → 查订单=PAID → 查库核对"

AI 会自动判断归属模块、按规范生成对应 `api/`、`testcases/`，校验语法后提交推送。详见各 skill 的 `SKILL.md`。

---

## 🔧 后期维护建议

| 方面 | 做法 |
|------|------|
| **降低脆弱** | 稳定定位器 + Playwright/显式等待，杜绝 `sleep` |
| **失败治理** | 自动重试过滤抖动；区分真 bug 与用例问题；看 Allure 截图/trace |
| **用例分级** | smoke(每次合并) / regression(每日) / 全量 |
| **资产管理** | 定期清理重复无效用例，用例不是越多越好 |
| **持续集成** | push/PR 跑冒烟，每日定时跑全量，失败自动通知 |
| **监控指标** | 通过率、执行时长、缺陷拦截率、维护频率 |

---

## 📊 CI/CD

`.github/workflows/automation-test.yml` 已配置：
- **触发**：push/PR 到 main、每日 02:00 定时、手动触发
- **并行**：api-test 与 web-test 分 job 跑
- **报告**：自动合并 Allure 结果并发布到 GitHub Pages
- **密钥**：账号通过 GitHub Secrets(`TEST_USERNAME`/`TEST_PASSWORD`)注入

> 在仓库 Settings → Secrets 配置账号；启用 Pages(Source 选 gh-pages 分支)查看报告。

---

## 📝 说明

示例用例中的 URL/接口路径/定位器均为占位符(`example.com` / `data-testid` 等)，
替换成你项目的真实信息即可运行。App 用例默认 `@skip`，连接真机/模拟器并启动 Appium 后放开。
