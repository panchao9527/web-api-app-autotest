# API + Web + App 自动化测试框架

一套基于 Python + pytest 的三端自动化测试框架：

- API：requests
- Web：Playwright
- App：Appium
- 报告：Allure
- 数据校验：MySQL / Redis
- CI：GitHub Actions / GitLab CI / Jenkins

项目只保留一个依赖文件和一份操作手册，适合由同一名测试工程师同时维护 API、Web、App 自动化。

## 最快开始

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
python scripts/automation.py doctor --env uat
python scripts/automation.py self-test
```

首次在 Windows 配置 Android 模拟器和 Appium：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_android_emulator.ps1
python scripts/automation.py doctor --env uat --type app
python scripts/automation.py app-smoke --env uat
```

运行三端业务测试：

```powershell
python scripts/automation.py test --type api --env uat
python scripts/automation.py test --type web --env uat --headed
python scripts/automation.py test --type app --env uat
python scripts/automation.py test --type all --env uat --marker smoke
```

> 业务目录尚无用例时命令会失败，避免 CI 假绿色。仅初始化模板时可临时增加 `--allow-empty`。

## 唯一操作手册

安装、配置、API/Web/App 用例编写、数据准备、报告、CI、安全规则、新公司落地和常见问题全部集中在：

[自动化测试框架操作手册](docs/自动化测试框架操作手册.md)

## 提交前检查

```powershell
python -m ruff format .
python -m ruff check .
python scripts/automation.py self-test
```
