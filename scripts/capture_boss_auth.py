"""按环境手工登录 BOSS，并安全保存 Playwright storage_state。"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env", override=False)

from config.settings import settings  # noqa: E402
from core.safety import ensure_environment_allowed  # noqa: E402
from pages.boss.login_page import BossLoginPage  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="采集指定环境的 BOSS Playwright 登录态")
    parser.add_argument(
        "--env",
        choices=("sit", "uat", "prod"),
        default=os.getenv("ENV", "uat").lower(),
        help="目标环境，默认读取 ENV，未配置时为 uat",
    )
    parser.add_argument(
        "--allow-prod",
        action="store_true",
        help="生产环境显式授权标志；还必须设置 ALLOW_PROD_TESTS=1",
    )
    return parser.parse_args()


def _storage_state_path(configured: str) -> Path:
    path = Path(configured)
    return path if path.is_absolute() else ROOT / path


def main() -> int:
    args = _parse_args()
    settings.reload(args.env)
    ensure_environment_allowed(settings.env, args.allow_prod)
    storage_state = _storage_state_path(settings.boss["storage_state"])

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        login_page = BossLoginPage(page)
        login_page.open_login()
        print(f"当前环境: {settings.env}，登录地址: {settings.web_base_url}")
        print("请在打开的浏览器中手工输入 BOSS 账号和密码并完成登录。")
        print("脚本不会读取或打印账号密码，等待时间最多 5 分钟。")

        try:
            login_page.wait_for_manual_login()
        except PlaywrightTimeoutError:
            print("登录等待超时或未进入 BOSS 首页，未保存登录态。")
            context.close()
            browser.close()
            return 1

        saved_path = login_page.save_storage_state(storage_state)
        print(f"登录态已保存到: {saved_path}")
        context.close()
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
