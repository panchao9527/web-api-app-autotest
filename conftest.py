"""
全局 conftest.py
- 提供跨三端(API/Web/App)共享的 fixture 和 pytest hook
- 失败时自动截图(Web/App) + 附加到 Allure 报告
"""
import allure
import pytest

from config.settings import settings
from core.web_driver import browser_context_args as _web_context_args
from core.web_driver import browser_launch_args as _web_launch_args
from utils.logger import log

# 注册 fixtures 包下的共享 fixture
pytest_plugins = [
    "fixtures.api_fixtures",
]


# ---------------------------------------------------------------------------
# pytest hook
# ---------------------------------------------------------------------------
def pytest_configure(config):
    """运行开始前打印环境信息"""
    log.info("=" * 60)
    log.info(f"测试启动 | 环境: {settings.env} | base_url: {settings.api_base_url}")
    log.info("=" * 60)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    钩子：捕获每个用例的执行结果。
    用例失败时，从 fixture 里拿到 page/driver 自动截图并附加到 Allure。
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        # Web (Playwright)
        page = item.funcargs.get("page", None)
        if page is not None:
            try:
                allure.attach(
                    page.screenshot(),
                    name="失败截图",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception as e:  # noqa
                log.warning(f"Web 截图失败: {e}")

        # App (Appium)
        driver = item.funcargs.get("app_driver", None)
        if driver is not None:
            try:
                allure.attach(
                    driver.get_screenshot_as_png(),
                    name="失败截图",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception as e:  # noqa
                log.warning(f"App 截图失败: {e}")


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
@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {**browser_type_launch_args, **_web_launch_args()}


@pytest.fixture
def browser_context_args(browser_context_args):
    return {**browser_context_args, **_web_context_args()}


# ---------------------------------------------------------------------------
# App (Appium) driver fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def app_driver():
    """App 测试用：创建 driver，用例结束自动退出"""
    from core.app_driver import create_app_driver

    driver = create_app_driver()
    yield driver
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
        Notifier().send_test_result(total=total, passed=passed, failed=failed,
                                    duration=duration, report_url=report_url)
    except Exception as e:  # noqa
        log.warning(f"钉钉/企微通知失败: {e}")

    if settings.email.get("host") and settings.email.get("to"):
        try:
            from clients.email_client import EmailSender
            EmailSender().send_report(total=total, passed=passed, failed=failed,
                                      duration=duration, report_url=report_url)
        except Exception as e:  # noqa
            log.warning(f"邮件通知失败: {e}")
