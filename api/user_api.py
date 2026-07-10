"""
用户模块 API 封装 (示例)
- 把"接口调用细节"封装在这里，用例只关心业务语义
- 接口路径变了只改这里一处，所有用例不受影响
"""

import allure

from api.base_api import BaseApi


class UserApi(BaseApi):
    @allure.step("登录: {username}")
    def login(self, username: str, password: str):
        """登录并自动回填 token，实现登录态复用"""
        resp = self.client.post("/api/login", json={"username": username, "password": password})
        # 登录成功则把 token 写回 client，后续请求自动带上
        if resp.status_code == 200:
            token = resp.json().get("token")
            if token:
                self.client.set_token(token)
        return resp

    @allure.step("查询用户: id={user_id}")
    def get_user(self, user_id: int):
        return self.client.get(f"/api/users/{user_id}")

    @allure.step("创建用户")
    def create_user(self, name: str, job: str):
        return self.client.post("/api/users", json={"name": name, "job": job})

    @allure.step("更新用户: id={user_id}")
    def update_user(self, user_id: int, **fields):
        return self.client.put(f"/api/users/{user_id}", json=fields)

    @allure.step("删除用户: id={user_id}")
    def delete_user(self, user_id: int):
        return self.client.delete(f"/api/users/{user_id}")

    @allure.step("用户列表: page={page}")
    def list_users(self, page: int = 1):
        return self.client.get("/api/users", params={"page": page})
