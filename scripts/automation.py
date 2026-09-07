"""自动化框架跨平台命令入口。"""

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import CONFIG_FILE, Settings  # noqa: E402
from core.safety import ensure_environment_allowed  # noqa: E402

TEST_PATHS = {
    "api": "testcases/api",
    "web": "testcases/web",
    "app": "testcases/app",
    "all": "testcases",
}


def build_pytest_command(
    *,
    test_type: str,
    environment: str,
    marker: str | None,
    headed: bool,
    browser: str | None,
    slowmo: int,
    tracing: str | None,
    allow_prod: bool,
) -> tuple[list[str], dict[str, str]]:
    """构造可直接交给当前 Python 解释器的 pytest 参数。"""
    command = ["-m", "pytest", TEST_PATHS[test_type]]
    marker_parts = [] if test_type == "all" else [test_type]
    if marker:
        marker_parts.append(f"({marker})")
    if marker_parts:
        command.extend(["-m", " and ".join(marker_parts)])
    command.extend(["--env", environment])
    command.append("--require-executed")
    if allow_prod:
        command.append("--allow-prod")
    if headed:
        command.append("--headed")
    if browser:
        command.extend(["--browser", browser])
    if slowmo:
        command.extend(["--slowmo", str(slowmo)])
    if tracing:
        command.extend(["--tracing", tracing])

    child_env = os.environ.copy()
    child_env["ENV"] = environment
    child_env["PYTHONUTF8"] = "1"
    child_env["PYTHONIOENCODING"] = "utf-8"
    return command, child_env


def run_pytest(arguments: list[str], child_env: dict[str, str] | None = None) -> int:
    return subprocess.run(
        [sys.executable, *arguments],
        cwd=ROOT,
        env=child_env,
        check=False,
    ).returncode


def normalize_pytest_exit_code(exit_code: int, allow_empty: bool = False) -> int:
    """无业务用例默认失败；仅初始化模板时允许显式放行。"""
    if exit_code == 5 and allow_empty:
        print("[提醒] 当前范围没有业务用例；添加 test_*.py 后会自动执行。")
        return 0
    if exit_code == 5:
        print("[失败] 当前范围没有收集到业务用例；如处于模板初始化阶段可传 --allow-empty。")
    return exit_code


def _print_check(level: str, message: str) -> None:
    print(f"[{level}] {message}")


def _check_python() -> bool:
    supported = (3, 10) <= sys.version_info[:2] < (3, 13)
    level = "通过" if supported else "失败"
    _print_check(level, f"Python {sys.version.split()[0]}，要求 3.10-3.12")
    return supported


def _check_virtual_environment() -> None:
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv:
        _print_check("通过", f"已启用虚拟环境: {sys.prefix}")
    else:
        _print_check(
            "提醒",
            "当前未启用虚拟环境。请运行 python -m venv .venv，"
            "然后在 PowerShell 执行 .\\.venv\\Scripts\\Activate.ps1",
        )


def _check_imports() -> bool:
    required = {
        "pytest": "pytest",
        "pytest_timeout": "pytest-timeout",
        "requests": "requests",
        "yaml": "PyYAML",
        "dotenv": "python-dotenv",
        "allure": "allure-pytest",
    }
    missing = [
        package for module, package in required.items() if not importlib.util.find_spec(module)
    ]
    if missing:
        _print_check(
            "失败", f"缺少核心依赖: {', '.join(missing)}。运行 pip install -r requirements.txt"
        )
        return False
    _print_check("通过", "核心 Python 依赖已安装")
    return True


def _check_config(environment: str) -> bool:
    try:
        loaded = Settings(config_file=CONFIG_FILE, env=environment)
    except ValueError as exc:
        _print_check("失败", str(exc))
        return False
    _print_check("通过", f"配置可读取，当前环境: {loaded.env}")
    if "example.com" in loaded.api_base_url or "example.com" in loaded.web_base_url:
        _print_check("提醒", "当前仍是示例地址；运行真实业务测试前请修改 config/config.yaml")
    env_file = ROOT / ".env"
    if env_file.exists():
        _print_check("通过", ".env 已存在")
    else:
        _print_check("提醒", "未找到 .env。请复制 .env.example 为 .env 并填写测试账号")
    return True


def playwright_browser_installed(cache_roots: list[Path], browser: str = "chromium") -> bool:
    """通过 Playwright 浏览器缓存判断是否安装，避免启动 Node driver。"""
    for root in cache_roots:
        try:
            if root.is_dir() and any(
                item.is_dir() and item.name.lower().startswith(f"{browser.lower()}-")
                for item in root.iterdir()
            ):
                return True
        except OSError:
            continue
    return False


def _playwright_cache_roots() -> list[Path]:
    roots = []
    configured = os.getenv("PLAYWRIGHT_BROWSERS_PATH")
    if configured and configured != "0":
        roots.append(Path(configured))
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        roots.append(Path(local_app_data) / "ms-playwright")
    home = os.getenv("USERPROFILE") or os.getenv("HOME")
    if home:
        roots.append(Path(home) / ".cache" / "ms-playwright")
    return roots


def _check_optional_tools(loaded: Settings) -> None:
    if importlib.util.find_spec("playwright"):
        if playwright_browser_installed(_playwright_cache_roots()):
            _print_check("通过", "Playwright Chromium 已安装")
        else:
            _print_check("提醒", "未发现 Chromium 缓存。运行 playwright install chromium")
    else:
        _print_check("提醒", "未安装 Web 测试依赖。运行 pip install -r requirements.txt")

    if importlib.util.find_spec("appium"):
        _print_check("通过", "Appium Python 客户端已安装")
    else:
        _print_check("提醒", "未安装 App 测试依赖。运行 pip install -r requirements.txt")
    if shutil.which("appium"):
        _print_check("通过", "已找到 Appium Server 命令")
    else:
        _print_check("提醒", "未找到 Appium Server；仅做 API/Web 测试可忽略")

    platform = loaded.app.get("platform", "Android").lower()
    if platform == "android":
        if shutil.which("adb"):
            _print_check("通过", "已找到 Android adb 命令")
        else:
            _print_check("提醒", "未找到 adb；运行 Android App 测试前请安装 Android SDK")
        if shutil.which("java"):
            _print_check("通过", "已找到 Java 命令")
        else:
            _print_check("提醒", "未找到 Java；Appium Android 驱动通常需要 JDK")
    elif sys.platform != "darwin":
        _print_check("提醒", "iOS 真机/模拟器自动化需要在 macOS + Xcode 环境运行")


def _command_output(executable: str, *arguments: str) -> tuple[int, str]:
    """执行环境诊断命令并返回合并输出，避免异常中断全部检查。"""
    try:
        result = subprocess.run(
            [executable, *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return result.returncode, f"{result.stdout}\n{result.stderr}".strip()


def _check_app_tools(loaded: Settings) -> bool:
    """执行 App 专项阻断检查；普通 API/Web doctor 不受设备状态影响。"""
    checks: list[bool] = []
    platform = str(loaded.app.get("platform", "Android")).lower()
    driver_name = "uiautomator2" if platform == "android" else "xcuitest"
    appium_command = shutil.which("appium.cmd") or shutil.which("appium")
    if appium_command:
        _print_check("通过", f"Appium Server: {appium_command}")
        code, output = _command_output(appium_command, "driver", "doctor", driver_name)
        driver_ready = code == 0
        _print_check(
            "通过" if driver_ready else "失败",
            f"{driver_name} doctor 通过"
            if driver_ready
            else f"{driver_name} doctor 失败，请执行 appium driver doctor {driver_name} 查看详情",
        )
        checks.append(driver_ready)
    else:
        _print_check("失败", "未找到 Appium Server；运行 npm install -g appium")
        checks.append(False)

    if platform != "android":
        supported = sys.platform == "darwin"
        _print_check("通过" if supported else "失败", "iOS 自动化运行主机必须是 macOS")
        checks.append(supported)
        return all(checks)

    android_home = os.getenv("ANDROID_HOME") or os.getenv("ANDROID_SDK_ROOT")
    android_home_ready = bool(android_home and Path(android_home).is_dir())
    _print_check(
        "通过" if android_home_ready else "失败",
        f"ANDROID_HOME: {android_home}"
        if android_home_ready
        else "ANDROID_HOME 未设置或目录不存在",
    )
    checks.append(android_home_ready)

    java_home = os.getenv("JAVA_HOME")
    java_binary = "java.exe" if sys.platform == "win32" else "java"
    java_home_ready = bool(java_home and (Path(java_home) / "bin" / java_binary).is_file())
    _print_check(
        "通过" if java_home_ready else "失败",
        f"JAVA_HOME: {java_home}" if java_home_ready else "JAVA_HOME 未设置或 JDK 不完整",
    )
    checks.append(java_home_ready)

    adb_command = shutil.which("adb")
    emulator_command = shutil.which("emulator")
    caps = loaded.app_caps()
    required_commands = [("adb", adb_command)]
    if caps.get("avd"):
        required_commands.append(("emulator", emulator_command))
    for label, command in required_commands:
        _print_check(
            "通过" if command else "失败",
            f"{label}: {command}" if command else f"未找到 {label} 命令",
        )
        checks.append(bool(command))

    app_path = caps.get("app")
    installed_app_ready = bool(caps.get("appPackage") and caps.get("appActivity"))
    if app_path:
        app_ready = Path(str(app_path)).is_file()
        message = f"安装包存在: {app_path}" if app_ready else f"安装包不存在: {app_path}"
    else:
        app_ready = installed_app_ready
        message = (
            "已配置已安装 App 的 appPackage/appActivity"
            if app_ready
            else "请在 .env 设置 APP_PATH，或配置 appPackage/appActivity"
        )
    _print_check("通过" if app_ready else "失败", message)
    checks.append(app_ready)

    if caps.get("avd") and emulator_command:
        code, output = _command_output(emulator_command, "-list-avds")
        avd_ready = code == 0 and str(caps["avd"]) in output.splitlines()
        _print_check(
            "通过" if avd_ready else "失败",
            f"模拟器已创建: {caps['avd']}" if avd_ready else f"未找到模拟器: {caps['avd']}",
        )
        checks.append(avd_ready)
    elif caps.get("udid") and adb_command:
        code, output = _command_output(adb_command, "devices")
        device_ready = code == 0 and any(
            line.split()[:2] == [str(caps["udid"]), "device"] for line in output.splitlines()
        )
        _print_check(
            "通过" if device_ready else "失败",
            f"真机/设备在线: {caps['udid']}" if device_ready else f"设备未在线: {caps['udid']}",
        )
        checks.append(device_ready)
    else:
        _print_check("失败", "未配置 APPIUM_AVD 或 APPIUM_UDID")
        checks.append(False)

    return all(checks)


def doctor(environment: str, test_type: str | None = None) -> int:
    print("自动化测试框架环境检查")
    print("=" * 40)
    checks = [_check_python(), _check_imports(), _check_config(environment)]
    _check_virtual_environment()
    if checks[-1]:
        try:
            loaded = Settings(config_file=CONFIG_FILE, env=environment)
            _check_optional_tools(loaded)
            if test_type in {"app", "all"}:
                checks.append(_check_app_tools(loaded))
        except ValueError as exc:
            _print_check("失败", str(exc))
            checks.append(False)
    return 0 if all(checks) else 1


def run_app_smoke(environment: str, allow_prod: bool = False) -> int:
    """创建一次真实 Appium Session，验证 Server、设备和安装包完整链路。"""
    # 会启动/安装 App，不能因为传了只读生产授权就放行。
    if environment.lower() == "prod":
        _print_check("失败", "App 连接验收可能安装或重置应用，禁止在生产环境执行")
        return 2
    try:
        ensure_environment_allowed(environment, allow_prod)
    except pytest.UsageError as exc:
        _print_check("失败", str(exc))
        return 2

    from config.settings import settings as project_settings
    from core.app_driver import create_app_driver, start_managed_appium_service

    project_settings.reload(environment)
    service = None
    driver = None
    exit_code = 0
    try:
        service = start_managed_appium_service()
        driver = create_app_driver()
        _print_check("通过", f"Appium Session: {driver.session_id}")
        if str(project_settings.app.get("platform", "Android")).lower() == "android":
            _print_check(
                "通过", f"当前 package/activity: {driver.current_package}/{driver.current_activity}"
            )
    except Exception as exc:  # noqa: BLE001
        _print_check("失败", f"Appium 冒烟连接失败: {exc}")
        exit_code = 1
    finally:
        # 两项独立清理；driver 断连不能阻止关闭本次创建的 Server。
        for resource, method in ((driver, "quit"), (service, "stop")):
            if resource is not None:
                try:
                    getattr(resource, method)()
                except Exception:  # noqa: BLE001
                    _print_check("失败", f"App 资源清理失败: {method}，请检查设备/进程状态")
                    exit_code = 1
    return exit_code


def clean_generated_files() -> int:
    for relative in ["reports", "logs", "screenshots", "traces", ".pytest_cache"]:
        target = (ROOT / relative).resolve()
        if ROOT not in target.parents:
            raise RuntimeError(f"拒绝清理项目目录之外的路径: {target}")
        if target.exists():
            shutil.rmtree(target)
            print(f"已清理: {target.relative_to(ROOT)}")
    return 0


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="API/Web/App 自动化测试统一命令")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="检查本机环境和项目配置")
    doctor_parser.add_argument("--env", default=os.getenv("ENV", "uat"))
    doctor_parser.add_argument("--type", choices=TEST_PATHS, default=None)

    app_smoke_parser = subparsers.add_parser("app-smoke", help="创建真实 Appium Session")
    app_smoke_parser.add_argument("--env", default=os.getenv("ENV", "uat"))
    app_smoke_parser.add_argument("--allow-prod", action="store_true")

    subparsers.add_parser("self-test", help="运行完全离线的框架自测")
    subparsers.add_parser("clean", help="清理报告、日志和缓存")

    test_parser = subparsers.add_parser("test", help="运行真实业务测试")
    test_parser.add_argument("--type", choices=TEST_PATHS, default="all")
    test_parser.add_argument("--env", default=os.getenv("ENV", "uat"))
    test_parser.add_argument("--marker", help="额外 pytest marker 表达式")
    test_parser.add_argument("--headed", action="store_true")
    test_parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"])
    test_parser.add_argument("--slowmo", type=int, default=0)
    test_parser.add_argument("--tracing", choices=["on", "off", "retain-on-failure"])
    test_parser.add_argument("--allow-prod", action="store_true")
    test_parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="模板初始化阶段允许没有业务用例；CI 不应使用",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    if args.command == "doctor":
        return doctor(args.env, args.type)
    if args.command == "app-smoke":
        return run_app_smoke(args.env, args.allow_prod)
    if args.command == "self-test":
        return run_pytest(["-m", "pytest", "tests/framework"])
    if args.command == "clean":
        return clean_generated_files()

    try:
        ensure_environment_allowed(args.env, args.allow_prod)
    except pytest.UsageError as exc:
        _print_check("失败", str(exc))
        return 2
    command, child_env = build_pytest_command(
        test_type=args.type,
        environment=args.env,
        marker=args.marker,
        headed=args.headed,
        browser=args.browser,
        slowmo=args.slowmo,
        tracing=args.tracing,
        allow_prod=args.allow_prod,
    )
    return normalize_pytest_exit_code(run_pytest(command, child_env), allow_empty=args.allow_empty)


if __name__ == "__main__":
    raise SystemExit(main())
