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
