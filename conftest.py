"""
全局 conftest.py
- 提供跨三端(API/Web/App)共享的 fixture 和 pytest hook
- setup/call/teardown 失败时自动保留 Web/App 截图和安全上下文
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import allure
import pytest

from config.settings import settings
from core.safety import ensure_environment_allowed
from utils.logger import log
from utils.redaction import redact, redact_text, redact_url

# 注册 fixtures 包下的共享 fixture
pytest_plugins = [
    "fixtures.api_fixtures",
]

# 不同测试端的合理耗时差异较大。这里统一设置测试级超时，防止接口、
# 浏览器或设备异常后无限等待；用例上的显式 timeout 标记始终优先。
DEFAULT_TIMEOUTS_BY_MARKER = {
    "api": 60,
    "web": 180,
    "app": 300,
}


class _ExecutionGate:
    """统计实际执行结果；不依赖终端插件，xdist 主进程也会收到 worker 报告。"""

    def __init__(self):
        self.executed = 0

    def pytest_runtest_logreport(self, report):
        if (
            report.when == "call"
            and report.outcome in {"passed", "failed"}
            and not hasattr(report, "wasxfail")
        ):
            self.executed += 1


# ---------------------------------------------------------------------------
# pytest hook
# ---------------------------------------------------------------------------
def pytest_addoption(parser):
    group = parser.getgroup("automation", "自动化框架")
    group.addoption("--env", action="store", default=None, help="运行环境，如 sit/uat/prod")
    group.addoption(
        "--require-executed",
        action="store_true",
        default=False,
        help="业务门禁：全部跳过视为失败，不把未执行当作测试通过",
    )
    group.addoption(
        "--allow-prod",
        action="store_true",
        default=False,
        help="允许生产环境只读测试，仍需 ALLOW_PROD_TESTS=1",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """运行开始前打印环境信息"""
    selected_env = config.getoption("--env") or settings.env
    if selected_env != settings.env:
        settings.reload(selected_env)
    ensure_environment_allowed(settings.env, config.getoption("--allow-prod"))
    if config.getoption("--require-executed"):
        config.pluginmanager.register(_ExecutionGate(), "business-execution-gate")
    # 显式 --alluredir（例如 CI 的分端目录）优先，否则每次生成唯一目录。
    if not getattr(config.option, "allure_report_dir", None):
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
        config.option.allure_report_dir = str(settings.root_dir / "reports" / "runs" / run_id)
    log.info(f"Allure 结果目录: {config.option.allure_report_dir}")
    if hasattr(config.option, "browser"):
        from core.web_driver import configured_browsers, configured_tracing

        config.option.browser = configured_browsers(
            config.getoption("--browser"), settings.web.get("browser", "chromium")
        )
        config.option.tracing = configured_tracing(
            config.getoption("--tracing"),
            sys.argv,
            bool(settings.web.get("trace", False)),
        )
        config._trace_retention = config.option.tracing
        # 插件在 teardown 报告产生前清理文件；延迟保留决策以覆盖清理失败。
        if config._trace_retention == "retain-on-failure":
            config.option.tracing = "on"
        output_base = Path(config.option.output)
        if str(output_base) == "test-results":
            output_base = settings.root_dir / "reports" / "web-evidence"
        config.option.output = str(output_base / uuid4().hex[:12])
    log.info("=" * 60)
    log.info(f"测试启动 | 环境: {settings.env} | base_url: {settings.api_base_url}")
    log.info("=" * 60)


def pytest_report_header(config):
    """在 pytest 标准头部显示报告位置，不依赖日志捕获设置。"""
    return f"Allure results: {config.option.allure_report_dir}"


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    """应用三端默认超时，并在生产环境只保留 prod_safe 用例。"""
    _apply_default_timeouts(items)

    if any(item.get_closest_marker("app") for item in items) and (
        config.getoption("numprocesses", default=0) or hasattr(config, "workerinput")
    ):
        raise pytest.UsageError("当前 App 使用单设备配置，请移除 -n；多设备需先隔离 udid 和端口")

    if settings.env != "prod":
        return
    selected = [item for item in items if item.get_closest_marker("prod_safe")]
    deselected = [item for item in items if item not in selected]
    items[:] = selected
    if deselected:
        config.hook.pytest_deselected(items=deselected)


def pytest_sessionfinish(session, exitstatus):
    """保留原有失败码；只阻止业务范围全部 skip 的假绿色，兼容 xdist 主进程。"""
    if exitstatus != 0 or not session.config.getoption("--require-executed"):
        return
    if getattr(session.config, "workerinput", None) is not None:
        return  # worker 不单独判定整个业务范围，交由主进程汇总。
    gate = session.config.pluginmanager.getplugin("business-execution-gate")
    reporter = session.config.pluginmanager.getplugin("terminalreporter")
    if gate is None or gate.executed == 0:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
        message = "业务门禁失败：没有实际通过或失败的用例（可能全部跳过/预期失败）"
        if reporter is not None:
            reporter.write_sep("!", message)
        else:
            log.error(message)


def _apply_default_timeouts(items) -> None:
    """按端类型设置超时；显式覆盖优先，多端标记取最长时间。"""
    for item in items:
        if item.get_closest_marker("timeout") is not None:
            continue

        matched_timeouts = [
            seconds
            for marker, seconds in DEFAULT_TIMEOUTS_BY_MARKER.items()
            if item.get_closest_marker(marker) is not None
        ]
        if matched_timeouts:
            item.add_marker(pytest.mark.timeout(max(matched_timeouts)))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    钩子：捕获每个用例的执行结果。
    用例失败时，从 fixture 里拿到 page/driver 自动截图并附加到 Allure。
    """
    outcome = yield
    report = outcome.get_result()

    if report.failed:
        _attach_failure_evidence(item, report.when)
        item._web_failed = True
    if report.when == "teardown":
        _finish_web_traces(item)


def _finish_web_traces(item):
    """插件已导出所有 Context 的 Trace，此时 Allure 用例尚未关闭。"""
    output = getattr(item, "_web_output", None)
    if output is None:
        return
    mode = getattr(item.config, "_trace_retention", "off")
    for trace in Path(output).glob("trace*.zip"):
        try:
            if mode == "retain-on-failure" and not getattr(item, "_web_failed", False):
                trace.unlink()
            elif mode != "off":
                allure.attach.file(
                    str(trace),
                    name=f"Playwright {trace.name}",
                    attachment_type="application/zip",
                    extension="zip",
                )
        except Exception as exc:
            log.warning(f"Trace 证据处理失败: {redact_text(str(exc))}")


def _attach_json(data: dict, name: str) -> None:
    allure.attach(
        json.dumps(redact(data), ensure_ascii=False, indent=2),
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )


def _attach_failure_evidence(item, stage: str) -> None:
    """为 setup/call/teardown 任一阶段的失败尽量保留现场。"""
    page = item.funcargs.get("page")
    if page is not None:
        try:
            allure.attach(
                page.screenshot(),
                name=f"Web失败截图-{stage}",
                attachment_type=allure.attachment_type.PNG,
            )
            _attach_json(
                {
                    "stage": stage,
                    "url": redact_url(page.url),
                    "title": redact_text(page.title()),
                },
                f"Web失败上下文-{stage}",
            )
        except Exception as exc:  # noqa: BLE001
            log.warning(f"Web 失败证据收集失败: {redact_text(str(exc))}")

    driver = item.funcargs.get("app_driver")
    if driver is not None:
        try:
            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"App失败截图-{stage}",
                attachment_type=allure.attachment_type.PNG,
            )
            _attach_json(
                {
                    "stage": stage,
                    "package": getattr(driver, "current_package", ""),
                    "activity": getattr(driver, "current_activity", ""),
                },
                f"App失败上下文-{stage}",
            )
        except Exception as exc:  # noqa: BLE001
            log.warning(f"App 失败证据收集失败: {redact_text(str(exc))}")


# ---------------------------------------------------------------------------
# 共享 fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def env_settings():
    """暴露全局配置对象给用例使用"""
    return settings


# ---------------------------------------------------------------------------
# Web (Playwright) 配置注入
# 覆盖 pytest-playwright 内置 fixture，让浏览器读 config.yaml 的设置
# ---------------------------------------------------------------------------
@pytest.fixture
def output_path(output_path, request):
    # UUID 隔离重试；上层运行目录隔离并发 worker 和独立运行。
    path = str(Path(output_path) / uuid4().hex[:8])
    request.node._web_output = path
    request.node._web_failed = False
    return path


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    from core.web_driver import browser_launch_args, merge_launch_args

    return merge_launch_args(browser_launch_args(), browser_type_launch_args)


@pytest.fixture
def browser_context_args(browser_context_args):
    from core.web_driver import browser_context_args as configured_context_args

    return {**browser_context_args, **configured_context_args()}


# ---------------------------------------------------------------------------
# App (Appium) driver fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def appium_service():
    """按配置自动管理本机 Appium Server；已有 Server 不会被关闭。"""
    from core.app_driver import start_managed_appium_service

    service = start_managed_appium_service()
    try:
        yield service
    finally:
        if service is not None:
            service.stop()


@pytest.fixture
def app_driver(appium_service):
    """App 测试用：确保 Server 就绪，创建 driver，并在用例结束后退出。"""
    from core.app_driver import create_app_driver

    driver = None
    try:
        driver = create_app_driver()
        yield driver
    finally:
        if driver is not None:
            driver.quit()


@pytest.fixture
def network_recorder(page):
    """
    网络录制器：跑 UI 流程时自动捕获接口调用序列。
    用于"UI 操作 → 抓接口序列 → 反推接口场景用例"。
    """
    from core.network_recorder import NetworkRecorder

    return NetworkRecorder(page)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    测试全部跑完后：若开启 send_on_finish，自动把结果摘要推送到
    已配置的钉钉/企微/邮件渠道。
    - 开关：config.yaml 的 notify.send_on_finish 或环境变量 NOTIFY_ON_FINISH=1
    - 本地默认不发(避免打扰)；CI 里打开即可
    """
    if not settings.notify.get("send_on_finish"):
        return

    import time

    stats = terminalreporter.stats
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", [])) + len(stats.get("error", []))
    skipped = len(stats.get("skipped", []))
    total = passed + failed + skipped
    try:
        duration = f"{time.time() - terminalreporter._sessionstarttime:.1f}s"
    except Exception:  # noqa
        duration = ""
    report_url = settings.notify.get("report_url", "")

    try:
        from clients.notify import Notifier

        Notifier().send_test_result(
            total=total, passed=passed, failed=failed, duration=duration, report_url=report_url
        )
    except Exception as e:  # noqa
        log.warning(f"钉钉/企微通知失败: {e}")

    if settings.email.get("host") and settings.email.get("to"):
        try:
            from clients.email_client import EmailSender

            EmailSender().send_report(
                total=total, passed=passed, failed=failed, duration=duration, report_url=report_url
            )
        except Exception as e:  # noqa
            log.warning(f"邮件通知失败: {e}")
