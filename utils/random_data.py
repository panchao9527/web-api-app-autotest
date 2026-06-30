"""
随机测试数据生成 (基于 Faker)
- 造唯一用户名/邮箱/手机号等，避免用例间数据冲突
- 中文场景用 zh_CN
"""
from faker import Faker

fake = Faker("zh_CN")


def random_username(prefix: str = "auto") -> str:
    """生成唯一用户名，带时间戳避免重复"""
    return f"{prefix}_{fake.user_name()}_{fake.random_int(1000, 9999)}"


def random_email() -> str:
    return fake.email()


def random_phone() -> str:
    return fake.phone_number()


def random_name() -> str:
    return fake.name()


def random_password(length: int = 12) -> str:
    return fake.password(length=length)


def random_address() -> str:
    return fake.address()



import time
import uuid


def uuid_str() -> str:
    """无横线的 uuid，适合做唯一标识"""
    return uuid.uuid4().hex


def unique_id(prefix: str = "T") -> str:
    """带前缀的唯一ID(毫秒时间戳)，造不重复的订单号/编码等"""
    return f"{prefix}{int(time.time() * 1000)}"


def random_digits(n: int = 6) -> str:
    """n 位随机数字串(验证码/编号)"""
    return "".join(str(fake.random_digit()) for _ in range(n))


def random_int(minimum: int = 1, maximum: int = 100) -> int:
    return fake.random_int(minimum, maximum)
