"""统一配置加载与校验。"""

import os
from pathlib import Path
from urllib.parse import urlparse

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
CONFIG_FILE = ROOT_DIR / "config" / "config.yaml"
SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}
SUPPORTED_APP_PLATFORMS = {"android", "ios"}


def _require_http_url(name: str, value: str) -> str:
    parsed = urlparse(str(value))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"配置 {name} 必须是有效的 http/https URL，实际值: {value!r}")
    return str(value).rstrip("/")


class Settings:
    """读取 YAML 和环境变量，并暴露兼容的属性接口。"""

    def __init__(
        self,
        config_file: str | Path = CONFIG_FILE,
        env: str | None = None,
        load_env_file: bool = True,
    ):
        self.config_file = Path(config_file)
        self._load(env=env, load_env_file=load_env_file)

    def _load(self, env: str | None, load_env_file: bool) -> None:
        if load_env_file:
            load_dotenv(ROOT_DIR / ".env", override=False)

        self.env = (env or os.getenv("ENV", "uat")).lower()
        try:
            raw = yaml.safe_load(self.config_file.read_text(encoding="utf-8")) or {}
        except FileNotFoundError as exc:
            raise ValueError(f"配置文件不存在: {self.config_file}") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"配置文件顶层必须是对象: {self.config_file}")
        if self.env not in raw:
            available = ", ".join(k for k, v in raw.items() if isinstance(v, dict))
            raise ValueError(f"未知环境: {self.env}，可用环境: {available or '无'}")

        self._raw = raw
        self.common = dict(raw.get("common", {}))
        self._env_cfg = dict(raw[self.env])
        self.api_base_url = _require_http_url("api_base_url", self._env_cfg.get("api_base_url", ""))
        self.web_base_url = _require_http_url("web_base_url", self._env_cfg.get("web_base_url", ""))

        timeout = self.common.get("timeout", 30)
        if not isinstance(timeout, int | float) or isinstance(timeout, bool) or timeout <= 0:
            raise ValueError(f"配置 timeout 必须是正数，实际值: {timeout!r}")
        self.timeout = timeout
        self.retry = self.common.get("retry", 0)
        self.log_level = str(self.common.get("log_level", "INFO")).upper()
        self.log_response = bool(self.common.get("log_response", True))
        self.log_response_max = int(self.common.get("log_response_max", 1000))

        self.web = dict(raw.get("web", {}))
        browser = str(self.web.get("browser", "chromium")).lower()
        if browser not in SUPPORTED_BROWSERS:
            raise ValueError(
                f"配置 web.browser 仅支持 {sorted(SUPPORTED_BROWSERS)}，实际值: {browser!r}"
            )
        self.web["browser"] = browser

        self.app = dict(raw.get("app", {}))
        platform = str(self.app.get("platform", "Android")).lower()
        if platform not in SUPPORTED_APP_PLATFORMS:
            raise ValueError(f"配置 app.platform 仅支持 Android/iOS，实际值: {platform!r}")

        db_cfg = dict(self._env_cfg.get("db", {}))
        db_cfg["user"] = os.getenv("DB_USER", db_cfg.get("user", ""))
        db_cfg["password"] = os.getenv("DB_PASSWORD", db_cfg.get("password", ""))
        self.db = db_cfg

        redis_cfg = dict(self._env_cfg.get("redis", {}))
        redis_cfg["password"] = os.getenv("REDIS_PASSWORD", redis_cfg.get("password", ""))
        self.redis = redis_cfg

        self.username = os.getenv("TEST_USERNAME", "")
        self.password = os.getenv("TEST_PASSWORD", "")
        self.api_token = os.getenv("API_TOKEN", "")

        notify_cfg = dict(raw.get("notify", {}))
        self.notify = {
            "dingtalk_webhook": os.getenv("DINGTALK_WEBHOOK", ""),
            "dingtalk_secret": os.getenv("DINGTALK_SECRET", ""),
            "wecom_webhook": os.getenv("WECOM_WEBHOOK", ""),
            "send_on_finish": os.getenv("NOTIFY_ON_FINISH", "").lower() in {"1", "true"}
            or bool(notify_cfg.get("send_on_finish", False)),
            "report_url": os.getenv("REPORT_URL", "") or notify_cfg.get("report_url", ""),
        }
        self.email = {
            "host": os.getenv("SMTP_HOST", ""),
            "port": os.getenv("SMTP_PORT", "465"),
            "user": os.getenv("SMTP_USER", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
            "to": os.getenv("EMAIL_TO", ""),
        }

    def reload(self, env: str | None = None) -> "Settings":
        """在保持对象引用不变的情况下重新加载环境配置。"""
        self._load(env=env, load_env_file=False)
        return self

    @property
    def root_dir(self) -> Path:
        return ROOT_DIR

    def app_caps(self) -> dict:
        platform = str(self.app.get("platform", "Android")).lower()
        return dict(self.app.get(platform, {}))


settings = Settings()
