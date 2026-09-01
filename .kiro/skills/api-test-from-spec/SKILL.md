---
name: api-test-from-spec
description: 根据接口定义(Swagger/OpenAPI、Controller 代码、接口文档)生成本框架规范的【单接口测试用例】—— 自动产出 api/ 接口封装 + testcases/api/ 用例(正常/必填/边界/异常)+ 数据驱动，遵循分层与 PO 规范，并提交推送。当用户提供接口定义/Swagger/Controller 并希望生成接口用例时使用。
---

# 接口定义 → 单接口用例 生成工作流

把用户提供的接口定义，按本框架规范生成接口封装 + 单接口用例。

## 触发场景
用户贴出 Swagger/OpenAPI 片段、Controller 代码、或接口文档，希望生成接口测试用例。典型说法："帮我根据这个接口写用例""用 api-test-from-spec 生成"。

## 第 0 步：解析接口信息
从输入提取：所属**模块**、每个接口的 **method / 路径 / 入参(名/类型/是否必填) / 返回结构**。信息不足时向用户确认（尤其鉴权方式、成功标志字段）。

## 第 1 步：生成接口封装 `api/<module>_api.py`
- 继承 `BaseApi`，通过 `self.client`(HttpClient) 发请求
- 一个业务模块一个文件；方法名表达业务语义
- 路径用相对路径（base_url 由 config 拼接）
- 每个方法加 `@allure.step(...)`
- 参考已有 `api/user_api.py`

## 第 2 步：生成单接口用例 `testcases/api/<module>/test_<feature>.py`
按字段类型自动设计场景，**覆盖以下维度**：
- **正向**：合法参数 → 期望状态码 + 业务成功
- **必填校验**：缺必填字段 → 4xx / 业务错误
- **边界值**：数值取最小/最大/越界；字符串取空/超长；枚举取非法值
- **类型错误**：传错类型
- 多组数据用**数据驱动**：放 `data/<module>/*.yaml` + `@pytest.mark.parametrize` + `load_yaml`

## 第 3 步：断言
- `Assert.status_code(resp, 期望)`
- `Assert.json_value(resp, 字段, 期望值)` 校验业务返回
- 关键接口加 `Assert.match_schema(resp, schema)` 做**契约校验**(防后端改字段)

## 第 4 步：留 TODO 给用户
AI 猜不到的，明确标 TODO：
- 业务成功标志(如 `code==0`)
- 环境内有效的真实数据(商品ID/门店码等)
- 鉴权 token 获取方式

## 第 5 步：规范校验 + 提交
- 用例只调封装方法，不出现裸 `requests.`/拼 URL
- 账号密码用 `env_settings`(来自 .env)
- 打标记：`api` + 模块名 + 优先级(`p0/p1`) + `single`
- 加 `@allure.epic/feature/story`
- `python -m py_compile` 校验语法
- commit：`test(api): 新增 <module> 单接口用例`；用 push_to_remote 推送；给分支/PR 链接

## 框架约定速查
- 接口基类 `api/base_api.py` `BaseApi`；HTTP 客户端 `core/http_client.py`
- 断言 `core/assertions.py` `Assert`
- 数据加载 `utils/data_loader.py` `load_yaml`
- 提取响应字段 `utils/extractor.py` `extract`
- 配置 `config/config.yaml`(多环境)；敏感信息 `.env`
- fixture：`env_settings`、`logged_in_client`(会话级登录态复用)
