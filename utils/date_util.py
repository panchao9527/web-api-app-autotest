"""
日期/时间工具
- 测试里高频：取今天/昨天、按偏移取日期、时间戳、格式转换
- 用法: from utils.date_util import yesterday_str, days_offset
"""

import datetime
import time

DATE_FMT = "%Y-%m-%d"
DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def now_str(fmt: str = DATETIME_FMT) -> str:
    """当前时间字符串，默认 'YYYY-MM-DD HH:MM:SS'"""
    return datetime.datetime.now().strftime(fmt)


def today_str(fmt: str = DATE_FMT) -> str:
    """今天，默认 'YYYY-MM-DD'"""
    return datetime.date.today().strftime(fmt)


def yesterday_str(fmt: str = DATE_FMT) -> str:
    """昨天"""
    return days_offset(-1, fmt)


def tomorrow_str(fmt: str = DATE_FMT) -> str:
    """明天"""
    return days_offset(1, fmt)


def days_offset(days: int, fmt: str = DATE_FMT, base: datetime.date = None) -> str:
    """
    相对某天偏移 N 天的日期字符串。
    days 为负表示过去，为正表示未来。
    例: days_offset(-7) 取 7 天前
    """
    base = base or datetime.date.today()
    return (base + datetime.timedelta(days=days)).strftime(fmt)


def timestamp(ms: bool = False) -> int:
    """当前时间戳，秒级；ms=True 返回毫秒级"""
    return int(time.time() * 1000) if ms else int(time.time())


def str_to_date(date_str: str, fmt: str = DATE_FMT) -> datetime.date:
    """字符串转 date 对象"""
    return datetime.datetime.strptime(date_str, fmt).date()


def to_str(d: datetime.date, fmt: str = DATE_FMT) -> str:
    """date/datetime 转字符串"""
    return d.strftime(fmt)
