"""在独立 pytest 进程中验证业务门禁和实际生成的 Allure 内容。"""

from pathlib import Path

import pytest

pytest_plugins = ["pytester"]


@pytest.fixture(autouse=True)
def isolated_subprocess_environment(monkeypatch):
    """pytester 按 UTF-8 读取输出；不继承 CI 的报告目录和其它 pytest 参数。"""
    monkeypatch.setenv("PYTHONUTF8", "1")
    monkeypatch.setenv("PYTHONIOENCODING", "utf-8")
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)


def _load_hooks(pytester):
    root = Path(__file__).resolve().parents[2]
    pytester.makeconftest(f"""
import sys
import importlib.util
sys.path.insert(0, {str(root)!r})
spec = importlib.util.spec_from_file_location("framework_hooks", {str(root / "conftest.py")!r})
hooks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hooks)
pytest_addoption = hooks.pytest_addoption
pytest_configure = hooks.pytest_configure
pytest_report_header = hooks.pytest_report_header
pytest_sessionfinish = hooks.pytest_sessionfinish
""")


@pytest.mark.parametrize("workers", [0, 2])
def test_all_skipped_business_run_fails(pytester, workers):
    _load_hooks(pytester)
    pytester.makepyfile("import pytest\ndef test_missing_environment(): pytest.skip('not ready')")
    result = pytester.runpytest_subprocess(
        "--require-executed", "--alluredir=results", "-n", str(workers), timeout=60
    )
    result.assert_outcomes(skipped=1)
    assert result.ret == pytest.ExitCode.TESTS_FAILED


def test_passed_business_run_and_report_do_not_capture_secret_parameters(pytester):
    _load_hooks(pytester)
    pytester.makepyfile("""
from unittest.mock import Mock
import pytest
from core.assertions import Assert
from pages.base_page import BasePage
from screens.base_screen import BaseScreen
from api.user_api import UserApi

def test_safe_outputs():
    with pytest.raises(AssertionError):
        Assert.equal({"password": "secret-actual"}, {"password": "secret-expected"})
    with pytest.raises(AssertionError):
        Assert.json_value({"token": "secret-token"}, "token", "secret-other-token")
    with pytest.raises(AssertionError):
        Assert.equal("secret-scalar", "other", sensitive=True)
    with pytest.raises(AssertionError):
        Assert.match_schema({"password": "secret-schema"}, {"type": "object", "properties": {"password": {"type": "integer"}}})
    BasePage(Mock()).fill("#password", "secret-web")
    BasePage(Mock()).type_text("#password", "secret-type")
    screen = BaseScreen(Mock())
    screen.find = Mock()
    screen.input("id", "password", "secret-app")
    client = Mock()
    client.post.return_value.status_code = 401
    UserApi(client).login("user", "secret-login")
""")
    result = pytester.runpytest_subprocess("--require-executed", "--alluredir=results", timeout=60)
    result.assert_outcomes(passed=1)
    assert result.ret == 0
    files = list((pytester.path / "results").glob("*-result.json"))
    assert files, "必须验证真实 Allure 结果，而不只是日志 Mock"
    for path in files:
        assert "secret-" not in path.read_text(encoding="utf-8")
