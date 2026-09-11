"""快捷入口和诊断命令回归；不连接业务、不启动浏览器或设备。"""

import os
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import yaml

from scripts import automation


def test_report_selects_latest_nonempty_run_without_deleting_history(monkeypatch, tmp_path):
    runs = tmp_path / "reports" / "runs"
    for name in ("old", "new", "empty"):
        (runs / name).mkdir(parents=True)
    for name in ("old", "new"):
        (runs / name / "sample-result.json").write_text("{}", encoding="utf-8")
    os.utime(runs / "old", (10, 10))
    os.utime(runs / "new", (20, 20))
    monkeypatch.setattr(automation, "ROOT", tmp_path)
    monkeypatch.setattr(automation.shutil, "which", lambda name: "allure")
    run = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(automation.subprocess, "run", run)
    assert automation.main(["report"]) == 0
    assert run.call_args.args[0] == ["allure", "serve", str(runs / "new")]
    assert (runs / "old" / "sample-result.json").exists()


def test_report_honors_explicit_path(monkeypatch, tmp_path):
    (tmp_path / "case-result.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(automation.shutil, "which", lambda name: "allure")
    run = Mock(return_value=SimpleNamespace(returncode=7))
    monkeypatch.setattr(automation.subprocess, "run", run)
    assert automation.main(["report", "--path", str(tmp_path)]) == 7
    assert str(tmp_path.resolve()) in run.call_args.args[0]


def test_report_empty_directory_does_not_start_allure(monkeypatch, tmp_path):
    monkeypatch.setattr(automation, "ROOT", tmp_path)
    run = Mock()
    monkeypatch.setattr(automation.subprocess, "run", run)
    assert automation.main(["report"]) == 1
    assert automation.main(["report", "--path", str(tmp_path)]) == 1
    run.assert_not_called()


@pytest.mark.parametrize(
    "kind, missing",
    [("web", "playwright"), ("app", "appium"), ("app", "selenium"), ("all", "pytest_playwright")],
)
def test_doctor_selected_dependencies_are_required(monkeypatch, kind, missing):
    monkeypatch.setattr(
        automation.importlib.util, "find_spec", lambda name: None if name == missing else object()
    )
    assert not automation._check_imports(kind)
    assert automation._check_imports("api")


def test_doctor_runs_without_site_packages():
    # -S 禁用第三方 site-packages，验证诊断入口自身不依赖 pytest/YAML。
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            str(automation.ROOT / "scripts" / "automation.py"),
            "doctor",
            "--type",
            "web",
        ],
        capture_output=True,
        encoding="utf-8",
        timeout=15,
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 1
    assert "缺少核心依赖" in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("code", [0, 1])
def test_web_doctor_checks_configured_browser(monkeypatch, code):
    probe = Mock(return_value=(code, ""))
    monkeypatch.setattr(automation, "_command_output", probe)
    assert automation._check_web_tools(SimpleNamespace(web={"browser": "firefox"})) is (code == 0)
    assert probe.call_args.args[-1] == "firefox"
    assert ".launch(" in probe.call_args.args[2]


def test_make_targets_and_ci_time_limits():
    root = automation.ROOT
    makefile = (root / "Makefile").read_text(encoding="utf-8")
    assert "scripts/automation.py report" in makefile
    assert 'testcases/api testcases/web -m "not app" -n 4 --require-executed' in makefile
    workflow = yaml.safe_load(
        (root / ".github/workflows/automation-test.yml").read_text(encoding="utf-8")
    )
    assert all(job["timeout-minutes"] > 0 for job in workflow["jobs"].values())
    gitlab = yaml.safe_load((root / ".gitlab-ci.yml").read_text(encoding="utf-8"))
    assert all(
        "timeout" in gitlab[name]
        for name in ("framework-test", "api-test", "web-test", "pages", "notify")
    )
    assert "timeout(time: 60, unit: 'MINUTES')" in (root / "Jenkinsfile").read_text(
        encoding="utf-8"
    )


def test_unused_retry_setting_is_removed():
    settings = (automation.ROOT / "config/settings.py").read_text(encoding="utf-8")
    config = yaml.safe_load((automation.ROOT / "config/config.yaml").read_text(encoding="utf-8"))
    assert "self.retry" not in settings
    assert "retry" not in config["common"]
