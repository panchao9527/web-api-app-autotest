"""
配置加载器
- 读取 config.yaml + .env，按当前 ENV 合并成一个全局 settings 对象
- 用例中通过 `from config.settings import settings` 使用
"""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
CONFIG_FILE = ROOT_DIR / "config" / "config.yaml"

# 加载 .env (敏感信息)
load_dotenv(ROOT_DIR / ".env")


class Settings:
    """全局配置对象，集中管理所有环境/三端配置"""

    def __init__(self):
        # 当前环境，优先取环境变量，默认 uat
        self.env = os.getenv("ENV", "uat").lower()

        # 读取 yaml
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            self._raw = yaml.safe_load(f)

        if self.env not in self._raw:
            raise ValueError(f"未知环境: {self.env}，请检查 config.yaml")

        # 合并 common + 当前环境
        self.common = self._raw.get("common", {})
        self._env_cfg = self._raw[self.env]

        # ---- API ----
        self.api_base_url = self._env_cfg["api_base_url"]
        self.web_base_url = self._env_cfg["web_base_url"]

        # ---- DB (host/port/name 来自 config.yaml; user/password 来自 .env) ----
        db_cfg = dict(self._env_cfg.get("db", {}))
        db_cfg["user"] = os.getenv("DB_USER", db_cfg.get("user", ""))
        db_cfg["password"] = os.getenv("DB_PASSWORD", db_cfg.get("password", ""))
        self.db = db_cfg

        # ---- Redis (host/port/db 来自 config.yaml; password 来自 .env) ----
        redis_cfg = dict(self._env_cfg.get("redis", {}))
        redis_cfg["password"] = os.getenv("REDIS_PASSWORD", redis_cfg.get("password", ""))
        self.redis = redis_cfg

        # ---- 公共 ----
        self.timeout = self.common.get("timeout", 30)
        self.retry = self.common.get("retry", 1)
        self.log_level = self.common.get("log_level", "INFO")
        # 是否在日志打印接口返回报文 + 最大长度(超出截断)
        self.log_response = self.common.get("log_response", True)
        self.log_response_max = self.common.get("log_response_max", 1000)

        # ---- Web / App ----
        self.web = self._raw.get("web", {})
        self.app = self._raw.get("app", {})

        # ---- 敏感信息 (来自 .env) ----
        self.username = os.getenv("TEST_USERNAME", "")
        self.password = os.getenv("TEST_PASSWORD", "")
        self.api_token = os.getenv("API_TOKEN", "")

        # ---- 通知 (webhook 含密钥，来自 .env) ----
        self.notify = {
            "dingtalk_webhook": os.getenv("DINGTALK_WEBHOOK", ""),
            "wecom_webhook": os.getenv("WECOM_WEBHOOK", ""),
        }

    @property
    def root_dir(self) -> Path:
        return ROOT_DIR

    def app_caps(self) -> dict:
        """根据 platform 返回对应的 Appium capabilities"""
        platform = self.app.get("platform", "Android").lower()
        return self.app.get(platform, {})


# 单例，全局共用
settings = Settings()
