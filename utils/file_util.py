"""
文件工具
- 读写文本/JSON、目录操作、拼项目路径
- 用法: from utils.file_util import read_json, write_json, ensure_dir
"""

import json
from pathlib import Path

from config.settings import settings


def project_path(*parts) -> Path:
    """拼项目根目录下的路径，如 project_path('data', 'x.json')"""
    return settings.root_dir.joinpath(*parts)


def read_text(path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    """写 JSON(中文不转义、缩进美化)"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_dir(path) -> Path:
    """确保目录存在(不存在则创建)"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def exists(path) -> bool:
    return Path(path).exists()


def list_files(directory, pattern: str = "*") -> list:
    """列出目录下匹配的文件(如 *.json)"""
    return [str(p) for p in Path(directory).glob(pattern) if p.is_file()]
