# 新公司落地指南（含要改的地方 + 所需账号权限）

带这套框架到新项目落地时，照本清单逐项处理即可。分三部分：**① 要申请的账号/权限 ② 框架里要改的地方 ③ 落地步骤与检查清单**。

---

## 一、先理解 CI/CD（一分钟）

- **CI（持续集成）**：代码一提交 → 自动构建 + **跑自动化测试** + 出报告。**你的框架就干这一环。**
- **CD（持续交付/部署）**：测试通过 → 自动打包 → 部署到测试/生产（通常开发/运维负责）。
- 你作为测试的核心任务：**把自动化测试接进公司的 CI 流水线**，让"提交代码就自动跑、出报告、发通知"。

---

## 二、需要向公司申请的账号 / 权限

| 类别 | 需要什么 | 找谁要 | 用在哪 |
|------|---------|--------|--------|
| 代码仓库 | 项目仓库的读写权限 | 团队负责人/配置管理 | clone、提交用例 |
| 测试环境 | SIT/UAT 环境的**接口地址**、可访问网络 | 开发/运维 | `config.yaml` |
| 测试账号 | 业务系统的测试用户名/密码 | 业务/测试负责人 | `.env` |
| 数据库 | 测试库的 host/账号/密码（**只读或测试库**） | DBA/运维 | `config.yaml` + `.env` |
| 缓存 | Redis 地址/密码（如需） | 运维 | `config.yaml` + `.env` |
| CI 平台 | GitLab/Jenkins 的项目权限、能配流水线 | DevOps/运维 | 配 CI |
| CI 密钥配置权 | 能在 CI 里配 Variables/Credentials | DevOps | 存账号/webhook |
| 通知机器人 | 钉钉/企微群机器人 webhook | 团队群主 | `.env`/CI 密钥 |
| 邮件 | SMTP 服务器/发件账号授权码 | IT/运维 | `.env`/CI 密钥 |
| App测试(如需) | 测试包(apk)、真机/模拟器、Appium 环境 | 移动开发 | Appium |

> 原则：**数据库尽量要测试库/只读账号**，别直连生产；测试账号用专门的测试用户。

---

## 三、框架里要改的地方（逐文件清单）⭐

### 1. `config/config.yaml` —— 各环境地址（非敏感）
```yaml
sit:
  api_base_url: "http://公司SIT接口地址"     # ← 改
  web_base_url: "http://公司SIT前端地址"     # ← 改
  db:    { host: "公司测试库地址", port: 3306, name: "库名" }   # ← 改
  redis: { host: "公司redis地址", port: 6379, db: 0 }          # ← 改
uat:
  ...同上改成 UAT 地址
```
> 环境名 sit/uat/prod 也可按公司习惯改（改这里 + settings 默认值）。

### 2. `.env` —— 敏感信息（复制 `.env.example` 生成，**不入库**）
```bash
ENV=uat
TEST_USERNAME=测试账号
TEST_PASSWORD=密码
DB_USER=库账号
DB_PASSWORD=库密码
REDIS_PASSWORD=
DINGTALK_WEBHOOK=钉钉机器人地址
WECOM_WEBHOOK=企微机器人地址
SMTP_HOST=... SMTP_USER=... SMTP_PASSWORD=... EMAIL_TO=...
```

### 3. `data/` —— 测试数据
- 替换成公司真实的测试数据（如门店编码、商品ID）
- 真实数据文件记得加 `.gitignore`，别提交（参考 `data/sales/*.txt` 的做法）

### 4. App 配置（如做 App，改 `config.yaml` 的 app 段）
```yaml
app:
  android:
    appPackage: "com.公司.app"       # ← 改成真实包名
    appActivity: ".启动Activity"      # ← 改
    deviceName: "你的设备名"          # ← adb devices 看
```

### 5. CI 配置 —— 选公司用的平台，改地址和触发分支
| 平台 | 改这个文件 | 主要改什么 |
|------|-----------|-----------|
| GitLab | `.gitlab-ci.yml` | `REPORT_URL`（或用 `$CI_PAGES_URL`）、镜像源 |
| Jenkins | `Jenkinsfile` | `REPORT_URL`、凭据 ID、agent |
| GitHub | `.github/workflows/automation-test.yml` | 触发分支、`REPORT_URL` |
- **触发分支**：确认公司主分支叫 main/master/release，改 workflow 里的分支名
- **报告地址 `REPORT_URL`**：改成公司报告地址（GitLab Pages / 内网 Nginx / Jenkins Allure）

### 6. CI 密钥 —— 在 CI 平台配置（不是写代码里）
| 平台 | 配在哪 |
|------|--------|
| GitLab | Settings → CI/CD → Variables |
| Jenkins | 凭据 Credentials（ID 与 Jenkinsfile 一致） |
| GitHub | Settings → Secrets |

要配的：`TEST_USERNAME/PASSWORD`、`DINGTALK_WEBHOOK`、`WECOM_WEBHOOK`、`SMTP_*`、`EMAIL_TO`、`DB_*` 等。

### 7. 业务断言 —— 补 TODO
用例里 `Assert.status_code(resp, 200)` 后面，按公司接口实际返回补业务断言：
```python
Assert.jsonpath(resp, "$.code", 0)     # 按公司成功码改(可能是 code=0 / success=true 等)
```

---

## 四、落地步骤（从小到大，别一步到位）

```
1. 摸清现状：公司用啥CI平台?仓库/环境/账号怎么给?现有CI长啥样?
2. 本地跑通：改好 config.yaml + .env，本地把几条用例跑稳
3. 接冒烟：先把 3-5 条核心用例接进CI，跑通、出报告
4. 接回归：扩到每日定时全量回归
5. 接触发：每次提交/MR 自动触发冒烟
6. 配通知：报告推送到钉钉/企微/邮件群，让团队看见
7. 定规则：推动"冒烟不过不许合并"等团队规范
```

---

## 五、落地检查清单（Checklist）

- [ ] 拿到仓库读写权限，能 clone
- [ ] 拿到 SIT/UAT 接口地址，改进 `config.yaml`
- [ ] 拿到测试账号，填进 `.env`
- [ ] 拿到测试库/Redis 连接信息（如需）
- [ ] 本地 `pip install -r requirements.txt` + `playwright install chromium`
- [ ] 本地跑通冒烟：`pytest -m smoke`
- [ ] 确认公司 CI 平台，选用对应配置文件
- [ ] 改 `REPORT_URL` 和触发分支名
- [ ] 在 CI 平台配好密钥（账号/webhook/SMTP）
- [ ] 建好钉钉/企微群机器人，拿到 webhook
- [ ] CI 上跑通一次，群里/邮箱收到报告
- [ ] 补齐用例的业务断言
- [ ] 推动团队用起来

---

## 六、常见坑

| 坑 | 应对 |
|----|------|
| 直接连生产库/生产环境 | 坚持用测试环境、测试库、只读账号 |
| 敏感信息提交到仓库 | 一律放 `.env`/CI密钥，`.env` 加 gitignore |
| 一上来接全量用例 | 先冒烟跑通，再逐步扩 |
| CI 里跑失败因缺依赖 | 用 `requirements.txt` 锁版本；Web 用 Playwright 镜像 |
| 用例不稳定(偶发失败) | 用显式等待、失败重试、查库核对，别用 sleep |
| 报告没人看 | 一定要配通知推到群里 |

---

> 带着这套框架 + 三平台 CI 配置落地，通常 **1-2 天**就能让"提交代码→自动跑测试→群里收报告"跑起来。核心就是上面三件事：**要账号权限、改配置、接 CI**。
