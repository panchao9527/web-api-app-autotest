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


def _environment_bool(name: str, default: bool) -> bool:
    """读取布尔环境变量，避免把任意非空字符串都误判为 True。"""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"环境变量 {name} 仅支持 1/0、true/false、yes/no 或 on/off")


def _application_path(value: str) -> str:
    """把安装包路径规范为绝对路径；文件是否存在由 doctor 在运行前检查。"""
    path = Path(os.path.expandvars(value)).expanduser()
    if not path.is_absolute():
        path = ROOT_DIR / path
    # 不调用 resolve()，避免 Windows 商店应用环境把 AppData 路径改写到 LocalCache。
    return str(path.absolute())


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
        self.boss = dict(self._env_cfg.get("boss", {}))
        self.boss["storage_state"] = (
            os.getenv("BOSS_STORAGE_STATE")
            or self.boss.get("storage_state")
            or f".auth/boss-{self.env}.json"
        )

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
        self.app["platform"] = os.getenv("APPIUM_PLATFORM") or self.app.get(
            "platform", "Android"
        )
        self.app["appium_server"] = _require_http_url(
            "app.appium_server",
            os.getenv("APPIUM_SERVER") or self.app.get("appium_server", "http://127.0.0.1:4723"),
        )
        self.app["manage_server"] = _environment_bool(
            "APPIUM_MANAGE_SERVER", bool(self.app.get("manage_server", False))
        )

        platform = str(self.app["platform"]).lower()
        if platform not in SUPPORTED_APP_PLATFORMS:
            raise ValueError(f"配置 app.platform 仅支持 Android/iOS，实际值: {platform!r}")
        platform_config = dict(self.app.get(platform, {}))
        overrides = {
            "app": os.getenv("APP_PATH"),
            "avd": os.getenv("APPIUM_AVD"),
            "udid": os.getenv("APPIUM_UDID"),
            "appPackage": os.getenv("APP_PACKAGE"),
            "appActivity": os.getenv("APP_ACTIVITY"),
            "platformVersion": os.getenv("APPIUM_PLATFORM_VERSION"),
        }
        for key, value in overrides.items():
            if value and value.strip():
                platform_config[key] = _application_path(value) if key == "app" else value.strip()
        if os.getenv("APPIUM_UDID"):
            platform_config.pop("avd", None)
        elif os.getenv("APPIUM_AVD"):
            platform_config.pop("udid", None)
        self.app[platform] = platform_config

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
        return {
            key: value
            for key, value in dict(self.app.get(platform, {})).items()
            if value is not None and value != ""
        }


settings = Settings()
