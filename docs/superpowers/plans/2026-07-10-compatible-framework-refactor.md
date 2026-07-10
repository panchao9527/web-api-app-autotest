# Compatible Automation Framework Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing API/Web/App automation scaffold into a safe, deterministic, beginner-friendly framework while preserving its public directory structure and common test-writing APIs.

**Architecture:** Keep business-facing modules in `api/`, `pages/`, `screens/`, and `testcases/`. Add independently testable configuration, safety, redaction, CLI, and lifecycle components, then make pytest and CI call those components through a stable cross-platform entry point. External demonstration tests move to `examples/`; `tests/framework/` becomes the offline health suite.

**Tech Stack:** Python 3.10-3.12, pytest, requests, pytest-playwright, Appium, Allure, PyYAML, python-dotenv, ruff.

---

### Task 1: Establish deterministic framework test entry

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/framework/__init__.py`
- Create: `tests/framework/test_test_entry.py`
- Create: `pyproject.toml`
- Modify: `pytest.ini`
- Move: `testcases/api/test_login_api.py` to `examples/api/test_login_api.py`
- Move: `testcases/api/test_sales.py` to `examples/api/test_sales.py`
- Move: `testcases/web/test_login_web.py` to `examples/web/test_login_web.py`
- Move: `testcases/web/test_demo_search.py` to `examples/web/test_demo_search.py`
- Move: `testcases/app/test_login_app.py` to `examples/app/test_login_app.py`

- [ ] **Step 1: Write the failing test-entry test**

```python
from pathlib import Path


def test_default_pytest_entry_only_targets_framework_tests():
    config = Path("pytest.ini").read_text(encoding="utf-8")
    assert "testpaths = tests/framework" in config
    assert "--reruns" not in config
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `python -m pytest tests/framework/test_test_entry.py -q -o addopts=""`

Expected: FAIL because `pytest.ini` still targets `testcases` and contains `--reruns 1`.

- [ ] **Step 3: Move external examples and update pytest configuration**

Set `testpaths = tests/framework`, remove global reruns and `-s`, register `prod_safe` and `flaky`, and keep Allure output. Add `pyproject.toml` with Python version and ruff configuration:

```toml
[project]
name = "web-api-app-autotest"
version = "1.0.0"
requires-python = ">=3.10,<3.13"

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
```

- [ ] **Step 4: Verify the focused test and default collection**

Run: `python -m pytest tests/framework/test_test_entry.py -q -o addopts=""`

Expected: PASS.

Run: `python -m pytest --collect-only -q`

Expected: only tests under `tests/framework/` are collected.

### Task 2: Add validated settings and production safety

**Files:**
- Create: `core/safety.py`
- Create: `tests/framework/test_settings.py`
- Create: `tests/framework/test_safety.py`
- Modify: `config/settings.py`
- Modify: `conftest.py`

- [ ] **Step 1: Write failing settings tests**

```python
import pytest

from config.settings import Settings


def test_settings_rejects_non_http_url(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(
        "common: {timeout: 30}\n"
        "uat: {api_base_url: 'bad', web_base_url: 'https://web.example'}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="api_base_url"):
        Settings(config_file=config, env="uat", load_env_file=False)


def test_explicit_environment_overrides_environment_variable(monkeypatch, tmp_path):
    monkeypatch.setenv("ENV", "sit")
    config = tmp_path / "config.yaml"
    config.write_text(
        "common: {}\n"
        "sit: {api_base_url: 'https://sit.example', web_base_url: 'https://sit-web.example'}\n"
        "uat: {api_base_url: 'https://uat.example', web_base_url: 'https://uat-web.example'}\n",
        encoding="utf-8",
    )
    assert Settings(config_file=config, env="uat", load_env_file=False).env == "uat"
```

- [ ] **Step 2: Run and verify expected failure**

Run: `python -m pytest tests/framework/test_settings.py -q -o addopts=""`

Expected: FAIL because `Settings` does not accept injectable config or environment values.

- [ ] **Step 3: Implement injectable validated Settings**

Use the exact constructor signature `Settings(config_file: str | Path = CONFIG_FILE, env: str | None = None, load_env_file: bool = True)`. Store the resolved `Path`, optionally load the root `.env`, select the explicit `env` before `ENV`, parse YAML with `yaml.safe_load`, and perform all validations before exposing public fields.

Validate environment existence, HTTP URLs, positive timeout, browser name, and App platform. Preserve the global `settings = Settings()` API.

- [ ] **Step 4: Write failing production-safety tests**

```python
import pytest

from core.safety import ensure_environment_allowed


def test_prod_is_blocked_by_default(monkeypatch):
    monkeypatch.delenv("ALLOW_PROD_TESTS", raising=False)
    with pytest.raises(pytest.UsageError, match="生产环境"):
        ensure_environment_allowed("prod", allow_prod_flag=False)


def test_prod_requires_flag_and_environment_variable(monkeypatch):
    monkeypatch.setenv("ALLOW_PROD_TESTS", "1")
    ensure_environment_allowed("prod", allow_prod_flag=True)
```

- [ ] **Step 5: Run and verify production-safety failure**

Run: `python -m pytest tests/framework/test_safety.py -q -o addopts=""`

Expected: FAIL because `core.safety` does not exist.

- [ ] **Step 6: Implement production safety and pytest options**

Add `--env` and `--allow-prod`. During `pytest_configure`, validate the selected environment. During `pytest_collection_modifyitems`, when production is authorized, deselect tests without `prod_safe`.

- [ ] **Step 7: Run settings and safety tests**

Run: `python -m pytest tests/framework/test_settings.py tests/framework/test_safety.py -q -o addopts=""`

Expected: PASS.

### Task 3: Add mandatory recursive redaction

**Files:**
- Create: `utils/redaction.py`
- Create: `tests/framework/test_redaction.py`

- [ ] **Step 1: Write failing redaction tests**

```python
from utils.redaction import redact, redact_url


def test_redact_masks_nested_sensitive_values():
    value = {
        "username": "tester",
        "password": "plain-password",
        "nested": {"access_token": "secret-token"},
        "items": [{"phone": "13800138000"}],
    }
    result = redact(value)
    assert result["username"] == "tester"
    assert result["password"] == "***"
    assert result["nested"]["access_token"] == "***"
    assert result["items"][0]["phone"] == "***"


def test_redact_url_masks_sensitive_query_parameters():
    result = redact_url("https://example.test/login?token=abc&page=1")
    assert "token=%2A%2A%2A" in result
    assert "page=1" in result
    assert "abc" not in result
```

- [ ] **Step 2: Run and verify expected import failure**

Run: `python -m pytest tests/framework/test_redaction.py -q -o addopts=""`

Expected: ERROR because `utils.redaction` does not exist.

- [ ] **Step 3: Implement recursive redaction**

Expose `SENSITIVE_KEYS` containing the keys listed in the design, `redact(value, sensitive_keys=SENSITIVE_KEYS)`, `redact_url(url, sensitive_keys=SENSITIVE_KEYS)`, and `redact_text(text)`. `redact_text` must mask JSON-like `key=value` and `key: value` fragments for the same sensitive keys.

Preserve non-sensitive types, avoid mutating input data, and match keys case-insensitively.

- [ ] **Step 4: Run redaction tests**

Run: `python -m pytest tests/framework/test_redaction.py -q -o addopts=""`

Expected: PASS.

### Task 4: Refactor HttpClient with TDD

**Files:**
- Create: `tests/framework/test_http_client.py`
- Modify: `core/http_client.py`
- Modify: `api/base_api.py`
- Modify: `fixtures/api_fixtures.py`

- [ ] **Step 1: Write failing lifecycle and URL tests**

```python
from core.http_client import HttpClient


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.closed = False
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return FakeResponse()

    def close(self):
        self.closed = True


def test_client_joins_relative_paths_and_closes():
    session = FakeSession()
    client = HttpClient(base_url="https://api.example/root/", session=session, timeout=9)
    client.get("users")
    assert session.calls[0][1] == "https://api.example/root/users"
    assert session.calls[0][2]["timeout"] == 9
    client.close()
    assert session.closed is True
```

- [ ] **Step 2: Run and verify expected constructor failure**

Run: `python -m pytest tests/framework/test_http_client.py -q -o addopts=""`

Expected: FAIL because `HttpClient` does not accept `session` or `timeout` and joins paths incorrectly.

- [ ] **Step 3: Implement session injection and lifecycle**

Use the exact constructor signature `HttpClient(base_url: str | None = None, token: str | None = None, session: requests.Session | None = None, timeout: float | None = None)`. Track whether the session is internally created, but close either injected or internal sessions when `close()` is called because the fixture owns the client lifecycle.

Add `close`, `__enter__`, and `__exit__`. Use a URL join helper that retains a base path and handles absolute URLs.

- [ ] **Step 4: Write failing redacted-report test**

```python
def test_request_details_are_redacted(monkeypatch):
    attached = []
    monkeypatch.setattr("allure.attach", lambda body, **kwargs: attached.append(body))
    client = HttpClient(base_url="https://api.example", session=FakeSession())
    client.post("/login", json={"password": "plain-password"})
    assert attached
    assert "plain-password" not in attached[0]
    assert "***" in attached[0]
```

- [ ] **Step 5: Implement redacted request, response, headers, URL and exception attachments**

Limit serialized attachment length using `settings.log_response_max`. Catch `requests.RequestException`, attach redacted request context, log the exception, then re-raise it.

- [ ] **Step 6: Convert client fixtures to yield and close**

`api_client` and `logged_in_client` must use `yield` and close their session in `finally`.

- [ ] **Step 7: Run HTTP and redaction tests**

Run: `python -m pytest tests/framework/test_http_client.py tests/framework/test_redaction.py -q -o addopts=""`

Expected: PASS.

### Task 5: Make cleanup and App resource handling reliable

**Files:**
- Create: `tests/framework/test_cleanup.py`
- Modify: `fixtures/api_fixtures.py`
- Modify: `conftest.py`
- Modify: `core/app_driver.py`

- [ ] **Step 1: Write failing cleanup aggregation test**

```python
import pytest

from fixtures.api_fixtures import CleanupRegistry


def test_cleanup_runs_in_reverse_and_reports_failures():
    calls = []
    registry = CleanupRegistry()
    registry.add_callback(lambda: calls.append("first"))
    registry.add_callback(lambda: (_ for _ in ()).throw(RuntimeError("cleanup failed")))
    registry.add_callback(lambda: calls.append("last"))
    with pytest.raises(ExceptionGroup, match="cleanup failed"):
        registry.run()
    assert calls == ["last", "first"]
```

- [ ] **Step 2: Run and verify test fails**

Run: `python -m pytest tests/framework/test_cleanup.py -q -o addopts=""`

Expected: FAIL because cleanup failures are ignored.

- [ ] **Step 3: Aggregate cleanup errors**

Run every registered cleanup in reverse order, collect exceptions, close DB resources in `finally`, then raise `ExceptionGroup("测试数据清理失败", errors)` on Python 3.11+ and a framework `CleanupError` containing all messages on Python 3.10.

- [ ] **Step 4: Remove App implicit wait and harden fixture teardown**

Delete `driver.implicitly_wait(settings.timeout)`. In `app_driver`, initialize `driver = None`, create it inside `try`, yield, and quit in `finally` when created.

- [ ] **Step 5: Run cleanup tests and compile App modules**

Run: `python -m pytest tests/framework/test_cleanup.py -q -o addopts=""`

Expected: PASS.

Run: `python -m py_compile core/app_driver.py conftest.py fixtures/api_fixtures.py`

Expected: exit 0.

### Task 6: Fix Web option precedence and trace behavior

**Files:**
- Create: `tests/framework/test_web_config.py`
- Modify: `core/web_driver.py`
- Modify: `conftest.py`

- [ ] **Step 1: Write failing precedence tests**

```python
from core.web_driver import merge_launch_args


def test_cli_launch_options_override_yaml_options():
    yaml_args = {"headless": True, "slow_mo": 0}
    cli_args = {"headless": False, "slow_mo": 800}
    assert merge_launch_args(yaml_args, cli_args) == cli_args
```

- [ ] **Step 2: Run and verify missing helper failure**

Run: `python -m pytest tests/framework/test_web_config.py -q -o addopts=""`

Expected: ERROR because `merge_launch_args` does not exist.

- [ ] **Step 3: Implement browser and launch option fixtures**

Add pure helpers for merge behavior. Add `browser_name` fixture that uses the command-line browser when explicitly supplied, otherwise YAML. Merge YAML first and plugin-provided CLI args second.

Add `pytest_load_initial_conftests` or command-builder behavior so YAML `trace: true` supplies `--tracing=retain-on-failure` only when the user has not explicitly selected a tracing mode.

- [ ] **Step 4: Run Web configuration tests**

Run: `python -m pytest tests/framework/test_web_config.py -q -o addopts=""`

Expected: PASS.

### Task 7: Add cross-platform CLI and doctor command

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/automation.py`
- Create: `tests/framework/test_automation_cli.py`
- Modify: `Makefile`

- [ ] **Step 1: Write failing command-builder tests**

```python
from scripts.automation import build_pytest_command


def test_build_web_command_preserves_cli_options():
    command, env = build_pytest_command(
        test_type="web",
        environment="uat",
        marker="smoke",
        headed=True,
        browser="firefox",
        slowmo=500,
        tracing="retain-on-failure",
        allow_prod=False,
    )
    assert command[:3] == ["-m", "pytest", "testcases/web"]
    assert "web and smoke" in command
    assert "--headed" in command
    assert command[-2:] == ["--tracing", "retain-on-failure"]
    assert env["ENV"] == "uat"
```

- [ ] **Step 2: Run and verify import failure**

Run: `python -m pytest tests/framework/test_automation_cli.py -q -o addopts=""`

Expected: ERROR because the CLI module does not exist.

- [ ] **Step 3: Implement argparse CLI**

Subcommands:

```text
doctor
self-test
test --type {api,web,app,all} --env ENV --marker EXPR
     --headed --browser {chromium,firefox,webkit} --slowmo N
     --tracing {on,off,retain-on-failure} --allow-prod
```

Run pytest through `subprocess.run([sys.executable, *command], env=env).returncode`; never build a shell string.

- [ ] **Step 4: Implement doctor checks**

Check Python version, virtual environment, `config/config.yaml`, importable core packages, Playwright browser availability, and optional Appium command. Print `[通过]`, `[提醒]`, or `[失败]` plus the exact remediation command.

- [ ] **Step 5: Update Makefile to delegate to Python CLI**

Every target should call one of the documented `python scripts/automation.py doctor`, `self-test`, `test`, or `clean` commands; clean must use the Python CLI and not `rm -rf`.

- [ ] **Step 6: Run CLI tests and help output**

Run: `python -m pytest tests/framework/test_automation_cli.py -q -o addopts=""`

Expected: PASS.

Run: `python scripts/automation.py --help`

Expected: exit 0 and list `doctor`, `self-test`, and `test`.

### Task 8: Harden utilities and JUnit aggregation

**Files:**
- Create: `tests/framework/test_retry.py`
- Create: `tests/framework/test_data_loader.py`
- Create: `tests/framework/test_junit_summary.py`
- Modify: `utils/retry.py`
- Modify: `utils/data_loader.py`
- Modify: `scripts/notify_from_junit.py`

- [ ] **Step 1: Write failing retry tests**

```python
import pytest

from utils.retry import retry


def test_retry_preserves_function_metadata():
    @retry(times=1, delay=0)
    def operation():
        """operation docs"""
        return "ok"

    assert operation.__name__ == "operation"
    assert operation.__doc__ == "operation docs"


def test_retry_rejects_zero_attempts():
    with pytest.raises(ValueError, match="times"):
        retry(times=0)
```

- [ ] **Step 2: Write failing data-loader and JUnit tests**

```python
import pytest

from utils.data_loader import load_excel


def test_empty_excel_has_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr("utils.data_loader.DATA_DIR", tmp_path)
    create_empty_workbook(tmp_path / "empty.xlsx")
    with pytest.raises(ValueError, match="没有表头"):
        load_excel("empty.xlsx")
```

JUnit tests must cover a root `<testsuite>` and nested `<testsuites>` without double-counting parent aggregates.

- [ ] **Step 3: Run utility tests and verify failures**

Run: `python -m pytest tests/framework/test_retry.py tests/framework/test_data_loader.py tests/framework/test_junit_summary.py -q -o addopts=""`

Expected: FAIL for missing validation, metadata preservation, empty workbook handling, or double-count behavior.

- [ ] **Step 4: Implement minimal fixes**

Use `functools.wraps`, validate `times >= 1`, avoid sleeping after the final failed attempt, close workbooks in `finally`, raise a Chinese empty-sheet error, and count only leaf JUnit suites.

- [ ] **Step 5: Run utility tests**

Run: `python -m pytest tests/framework/test_retry.py tests/framework/test_data_loader.py tests/framework/test_junit_summary.py -q -o addopts=""`

Expected: PASS.

### Task 9: Split dependencies and repair CI behavior

**Files:**
- Create: `requirements-api.txt`
- Create: `requirements-web.txt`
- Create: `requirements-app.txt`
- Create: `requirements-infra.txt`
- Create: `requirements-dev.txt`
- Modify: `requirements.txt`
- Modify: `.github/workflows/automation-test.yml`
- Modify: `.gitlab-ci.yml`
- Modify: `Jenkinsfile`

- [ ] **Step 1: Add a repository-policy test**

```python
from pathlib import Path


def test_jenkins_parallel_jobs_use_separate_allure_directories():
    text = Path("Jenkinsfile").read_text(encoding="utf-8")
    assert "reports/allure-api" in text
    assert "reports/allure-web" in text
```

- [ ] **Step 2: Run and verify CI policy failure**

Run: `python -m pytest tests/framework/test_ci_policy.py -q -o addopts=""`

Expected: FAIL because Jenkins writes both jobs to one Allure directory.

- [ ] **Step 3: Split dependency files**

`requirements.txt` remains the beginner-friendly all-in install and includes the four runtime requirement files with `-r`. `requirements-dev.txt` adds ruff and test-only packages.

- [ ] **Step 4: Update CI flows**

- Framework job: ruff plus `python scripts/automation.py self-test`.
- PR/push business jobs: `test --marker smoke`.
- Scheduled jobs: `test --marker regression`.
- Jenkins API and Web jobs write to `reports/allure-api` and `reports/allure-web`, then report both paths.
- GitHub report publishing declares the required `contents: write` permission.

- [ ] **Step 5: Run CI policy tests and YAML parse checks**

Run: `python -m pytest tests/framework/test_ci_policy.py -q -o addopts=""`

Expected: PASS.

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/automation-test.yml', encoding='utf-8')); yaml.safe_load(open('.gitlab-ci.yml', encoding='utf-8')); print('yaml ok')"`

Expected: `yaml ok`.

### Task 10: Write the beginner guide and align README

**Files:**
- Create: `docs/新项目从0开始.md`
- Modify: `README.md`
- Modify: `docs/ci.md`
- Modify: `docs/web-guide.md`
- Modify: `docs/coding-standards.md`

- [ ] **Step 1: Write the guide from the verified commands**

The guide must contain complete Windows PowerShell commands for virtual environment creation, dependency installation, doctor, self-test, `.env` setup, first API test, first Web test, first App test, reports, markers, data cleanup, CI, and troubleshooting.

- [ ] **Step 2: Replace obsolete README commands**

Make `python scripts/automation.py doctor`, `python scripts/automation.py self-test`, and `python scripts/automation.py test` the primary interfaces. Clearly distinguish framework self-tests, real business tests, and examples. Document production blocking and redaction.

- [ ] **Step 3: Align specialized docs**

Remove claims that all CI platforms have identical scheduling configuration, document actual Playwright trace behavior, and update coding standards to require framework tests for core changes.

- [ ] **Step 4: Check documentation references**

Run: `python -c "from pathlib import Path; assert Path('docs/新项目从0开始.md').exists(); assert 'automation.py self-test' in Path('README.md').read_text(encoding='utf-8'); print('docs ok')"`

Expected: `docs ok`.

### Task 11: Final verification

**Files:**
- Modify only files required by verification failures.

- [ ] **Step 1: Run formatting and lint checks**

Run: `python -m ruff format --check .`

Expected: exit 0.

Run: `python -m ruff check .`

Expected: exit 0.

- [ ] **Step 2: Run offline framework tests**

Run: `python scripts/automation.py self-test`

Expected: all framework tests pass with no network access.

- [ ] **Step 3: Verify default pytest behavior**

Run: `python -m pytest --collect-only -q`

Expected: only `tests/framework/` tests are collected.

- [ ] **Step 4: Verify business and example collection explicitly**

Run: `python -m pytest testcases --collect-only -q -o addopts=""`

Expected: collection succeeds even if the project currently has no real business tests.

Run: `python -m pytest examples --collect-only -q -o addopts=""`

Expected: example tests collect without executing external calls.

- [ ] **Step 5: Verify production blocking**

Run: `python scripts/automation.py test --type api --env prod`

Expected: non-zero exit with a Chinese message explaining the two required production authorizations.

- [ ] **Step 6: Verify syntax and working tree**

Run: `python -m compileall -q .`

Expected: exit 0.

Run: `git diff --check`

Expected: exit 0.
