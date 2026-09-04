"""
Appium 驱动工厂
- 根据配置创建 Android / iOS driver
- 统一管理 capabilities 与 server 地址
- 可选自动启动和关闭本机 Appium Server
"""

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from appium.webdriver.appium_service import AppiumService

from config.settings import settings
from utils.logger import log

LOCAL_APPIUM_HOSTS = {"127.0.0.1", "localhost", "::1"}


def appium_server_ready(server_url: str, timeout: float = 1.0) -> bool:
    """检查 Appium `/status`，避免重复启动或错误占用本机端口。"""
    status_url = f"{server_url.rstrip('/')}/status"
    try:
        with urlopen(status_url, timeout=timeout) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
        return False
    return response.status < 400 and bool(payload.get("value", {}).get("ready"))


def build_appium_service_args(server_url: str, log_file: str | Path | None = None) -> list[str]:
    """把本机 Appium URL 转换为 Server 启动参数。"""
    parsed = urlparse(server_url)
    host = parsed.hostname or "127.0.0.1"
    if host not in LOCAL_APPIUM_HOSTS:
        raise ValueError(f"自动管理仅支持本机 Appium Server，实际地址: {server_url}")

    args = ["--address", host, "--port", str(parsed.port or 4723)]
    base_path = parsed.path.rstrip("/")
    if base_path:
        args.extend(["--base-path", base_path])
    if log_file is not None:
        args.extend(["--log", str(log_file), "--log-timestamp"])
    return args


def start_managed_appium_service() -> AppiumService | None:
    """按配置启动本机 Appium；复用已运行的 Server，且不接管外部进程。"""
    app_cfg = settings.app
    if not app_cfg.get("manage_server", False):
        return None

    server_url = app_cfg.get("appium_server", "http://127.0.0.1:4723")
    if appium_server_ready(server_url):
        log.info(f"复用已运行的 Appium Server | server={server_url}")
        return None

    log_file = settings.root_dir / "logs" / "appium-server.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    service = AppiumService()
    service.start(
        args=build_appium_service_args(server_url, log_file),
        timeout_ms=int(app_cfg.get("server_start_timeout", 60000)),
    )
    log.info(f"已自动启动 Appium Server | server={server_url} | log={log_file}")
    return service


def create_app_driver():
    """根据配置创建对应平台的 Appium driver。"""
    app_cfg = settings.app
    platform = app_cfg.get("platform", "Android").lower()
    server = app_cfg.get("appium_server", "http://127.0.0.1:4723")
    caps = settings.app_caps()

    log.info(f"启动 App driver | 平台={platform} | server={server}")

    if platform == "android":
        options = UiAutomator2Options().load_capabilities(caps)
    elif platform == "ios":
        options = XCUITestOptions().load_capabilities(caps)
    else:
        raise ValueError(f"不支持的平台: {platform}")

    driver = webdriver.Remote(command_executor=server, options=options)
    return driver
