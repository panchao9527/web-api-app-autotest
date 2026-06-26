"""
API 业务基类
- 所有业务 API 类继承它，共享同一个 HttpClient 实例
- 在这里放跨模块通用的方法
"""
from core.http_client import HttpClient


class BaseApi:
    def __init__(self, client: HttpClient = None):
        # 允许外部传入已登录的 client，实现登录态复用
        self.client = client or HttpClient()
