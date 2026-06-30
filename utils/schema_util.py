"""
JSON Schema 工具
- 从一份样例响应自动生成 JSON Schema，省去手写
- 配合 Assert.match_schema 做契约测试(防后端悄悄改字段/类型)
- 用法:
    from utils.schema_util import generate_schema
    schema = generate_schema(resp.json())   # 拿真实返回生成 schema
    # 人工微调后存起来，之后用 Assert.match_schema(resp, schema) 校验
"""


def generate_schema(sample) -> dict:
    """根据样例数据递归生成 JSON Schema(对象的所有字段默认 required)"""
    # 注意: bool 是 int 的子类，要先判断 bool
    if isinstance(sample, bool):
        return {"type": "boolean"}
    if isinstance(sample, int):
        return {"type": "integer"}
    if isinstance(sample, float):
        return {"type": "number"}
    if sample is None:
        return {"type": "null"}
    if isinstance(sample, dict):
        return {
            "type": "object",
            "properties": {k: generate_schema(v) for k, v in sample.items()},
            "required": list(sample.keys()),
        }
    if isinstance(sample, list):
        return {
            "type": "array",
            "items": generate_schema(sample[0]) if sample else {},
        }
    return {"type": "string"}
