"""
统一日志 (基于 loguru)
- 控制台彩色输出 + 文件按天滚动
- 全局导入: from utils.logger import log
"""

import sys
from pathlib import Path

from loguru import logger

ROOT_DIR = Path(__file__).parent.parent
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 移除默认 handler，自定义格式
logger.remove()

# 控制台输出
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}:{line}</cyan> | <level>{message}</level>",
)

# 文件输出：按天切分，保留 15 天，自动压缩
logger.add(
    LOG_DIR / "test_{time:YYYY-MM-DD}.log",
    level="DEBUG",
    rotation="00:00",
    retention="15 days",
    compression="zip",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
)

log = logger
