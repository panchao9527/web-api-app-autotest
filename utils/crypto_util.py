"""
加密/签名工具
- 接口测试常见：参数 md5/sha256 签名、base64、HMAC 签名
- 用法:
    from utils.crypto_util import md5, sha256, hmac_sha256, base64_encode
    sign = md5("a=1&b=2&key=secret")
"""
import base64
import hashlib
import hmac


def md5(text: str, upper: bool = False) -> str:
    """MD5，默认小写十六进制"""
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    return h.upper() if upper else h


def sha256(text: str, upper: bool = False) -> str:
    """SHA256"""
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return h.upper() if upper else h


def hmac_sha256(key: str, message: str, upper: bool = False) -> str:
    """HMAC-SHA256 签名（很多开放接口用）"""
    h = hmac.new(key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return h.upper() if upper else h


def base64_encode(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def base64_decode(b64: str) -> str:
    return base64.b64decode(b64).decode("utf-8")


def sign_params(params: dict, secret: str = "", algo: str = "md5") -> str:
    """
    通用参数签名：按 key 升序拼成 a=1&b=2 后拼 secret 再做摘要。
    很多接口的签名规则就是这种，具体按你接口调整。
    """
    items = sorted(params.items())
    raw = "&".join(f"{k}={v}" for k, v in items)
    if secret:
        raw += f"&key={secret}"
    return md5(raw) if algo == "md5" else sha256(raw)
