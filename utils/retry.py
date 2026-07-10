"""
轮询/重试工具
- 异步场景必备：等数据库落库、等 MQ 消费完、等状态变更
- 用法:
    from utils.retry import wait_until

    # 轮询直到查到订单，最多等 10 秒，每 1 秒查一次
    order = wait_until(lambda: query_order(oid), timeout=10, interval=1)
"""

import time
from functools import wraps

from utils.logger import log


def wait_until(func, timeout: float = 10, interval: float = 1, desc: str = ""):
    """
    每隔 interval 秒调用一次 func，直到其返回值为"真"则返回该值。
    超过 timeout 秒仍为假则抛 TimeoutError。
    适合：等异步结果(DB/MQ/状态)就绪。
    """
    deadline = time.time() + timeout
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        result = func()
        if result:
            log.info(f"wait_until 成功 | {desc or func} | 第{attempt}次")
            return result
        time.sleep(interval)
    raise TimeoutError(f"wait_until 超时({timeout}s) | {desc or func}")


def retry(times: int = 3, delay: float = 1, exceptions=(Exception,)):
    """
    装饰器：函数抛指定异常时自动重试。
    @retry(times=3, delay=2)
    def call_flaky_api(): ...
    """
    if not isinstance(times, int) or isinstance(times, bool) or times < 1:
        raise ValueError(f"times 必须是大于等于 1 的整数，实际值: {times!r}")
    if delay < 0:
        raise ValueError(f"delay 不能小于 0，实际值: {delay!r}")

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for i in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if i < times:
                        log.warning(f"{func.__name__} 第{i}次失败: {e}，{delay}s 后重试")
                        time.sleep(delay)
                    else:
                        log.error(f"{func.__name__} 重试 {times} 次后仍失败: {e}")
            raise last_exc

        return wrapper

    return decorator
