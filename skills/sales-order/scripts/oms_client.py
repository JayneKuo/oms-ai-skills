"""
OMS 共享客户端 — auth + HTTP 请求
所有脚本通过 import oms_client 使用

配置优先级（高到低）：
1. 运行时参数 init(config=...) — 上游 agent 通过 --config JSON 传入
2. 环境变量 OMS_BASE_URL 等
3. 别名环境变量 BASE_URL、TENANT_ID 等
"""
import os
import json
import sys
import urllib.request
import urllib.parse

_token_cache = {}
_runtime_config = {}  # 由 init() 注入

# 支持的环境变量别名映射
_ALIASES = {
    "OMS_BASE_URL":     ["OMS_BASE_URL", "OMS_HOST", "OMS_SERVER_URL", "BASE_URL"],
    "OMS_IAM_BASE_URL": ["OMS_IAM_BASE_URL", "OMS_AUTH_URL"],
    "OMS_TENANT_ID":    ["OMS_TENANT_ID", "TENANT_ID", "OMS_TENANT"],
    "OMS_MERCHANT_NO":  ["OMS_MERCHANT_NO", "MERCHANT_NO", "OMS_MERCHANT"],
    "OMS_USERNAME":     ["OMS_USERNAME", "OMS_USER", "USERNAME"],
    "OMS_PASSWORD":     ["OMS_PASSWORD", "OMS_PASS", "PASSWORD"],
    "OMS_ACCESS_TOKEN": ["OMS_ACCESS_TOKEN", "ACCESS_TOKEN"],
}

_PARAM_KEYS = {
    "OMS_BASE_URL":     ["baseUrl", "base_url", "OMS_BASE_URL"],
    "OMS_IAM_BASE_URL": ["iamBaseUrl", "iam_base_url", "OMS_IAM_BASE_URL"],
    "OMS_TENANT_ID":    ["tenantId", "tenant_id", "OMS_TENANT_ID"],
    "OMS_MERCHANT_NO":  ["merchantNo", "merchant_no", "OMS_MERCHANT_NO"],
    "OMS_USERNAME":     ["username", "OMS_USERNAME"],
    "OMS_PASSWORD":     ["password", "OMS_PASSWORD"],
    "OMS_ACCESS_TOKEN": ["token", "accessToken", "access_token", "OMS_ACCESS_TOKEN"],
    "OMS_ENV":          ["env", "OMS_ENV"],
}

def _iam_base_url():
    """IAM token URL，默认和 OMS_BASE_URL 相同（omsv2/omsv3 共用同一 IAM）"""
    return _env("OMS_BASE_URL")
    for param_key in _PARAM_KEYS.get("OMS_IAM_BASE_URL", []):
        val = _runtime_config.get(param_key)
        if val:
            return str(val)
    for alias in _ALIASES.get("OMS_IAM_BASE_URL", []):
        val = os.environ.get(alias)
        if val:
            return val
    # 默认：把 omsv3 替换回 omsv2 获取 token
    base = _env("OMS_BASE_URL")
    return base.replace("omsv3", "omsv2")

def get_env_label():
    """返回当前环境标识，用于在响应中标注"""
    for alias in ["OMS_ENV", "env"]:
        val = _runtime_config.get(alias) or os.environ.get(alias)
        if val:
            return val.lower()
    try:
        base_url = _env("OMS_BASE_URL")
        if "staging" in base_url:
            return "staging"
        return "production"
    except SystemExit:
        return "unknown"

def init(config: dict):
    """由脚本在解析 --config 参数后调用，注入运行时配置"""
    global _runtime_config, _token_cache
    _runtime_config = config or {}
    _token_cache = {}

def _env(key):
    # 1. 运行时参数优先
    for param_key in _PARAM_KEYS.get(key, [key]):
        val = _runtime_config.get(param_key)
        if val:
            return str(val)

    # 2. 环境变量（含别名）
    for alias in _ALIASES.get(key, [key]):
        val = os.environ.get(alias)
        if val:
            return val

    # 3. 缺失，输出友好提示
    missing = {
        "error": "missing_config",
        "key": key,
        "accepted_params": _PARAM_KEYS.get(key, [key]),
        "accepted_env": _ALIASES.get(key, [key]),
        "message": (
            f"'{key}' is not set. Provide it via --config JSON or environment variable. "
            f"Accepted param names: {', '.join(_PARAM_KEYS.get(key, []))}. "
            f"Accepted env names: {', '.join(_ALIASES.get(key, []))}."
        )
    }
    print(json.dumps(missing, ensure_ascii=False), file=sys.stderr)
    sys.exit(2)

def get_token():
    # 如果上游直接传入浏览器/agent token，优先使用
    for key in _PARAM_KEYS.get("OMS_ACCESS_TOKEN", []):
        val = _runtime_config.get(key)
        if val:
            return str(val).replace("Bearer ", "")
    for key in _ALIASES.get("OMS_ACCESS_TOKEN", []):
        val = os.environ.get(key)
        if val:
            return val.replace("Bearer ", "")

    base_url = _env("OMS_BASE_URL")
    iam_url = _iam_base_url()
    cache_key = base_url + _env("OMS_USERNAME")
    if cache_key in _token_cache:
        return _token_cache[cache_key]

    payload = json.dumps({
        "grantType": "password",
        "username": _env("OMS_USERNAME"),
        "password": _env("OMS_PASSWORD")
    }).encode()

    req = urllib.request.Request(
        f"{iam_url}/api/linker-oms/opc/iam/token",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-tenant-id": _env("OMS_TENANT_ID")
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(json.dumps({"error": "auth_failed", "message": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)

    token = data.get("data", {}).get("accessToken") or data.get("data", {}).get("access_token")
    if not token:
        print(json.dumps({"error": "auth_failed", "message": f"Token response missing access token: {data}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)

    _token_cache[cache_key] = token
    return token

def _headers():
    base_url = _env("OMS_BASE_URL")
    return {
        "Authorization": f"Bearer {get_token()}",
        "x-tenant-id": _env("OMS_TENANT_ID"),
        "USER": _env("OMS_USERNAME"),
        "Content-Type": "application/json",
        "accept": "application/json, text/plain, */*",
        "locale": _runtime_config.get("locale") or os.environ.get("OMS_LOCALE") or "en-US",
        "origin": base_url,
        "referer": f"{base_url}/sales-orders/add"
    }

def get(path, params=None):
    base_url = _env("OMS_BASE_URL")
    if params:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
        url = f"{base_url}{path}?{qs}"
    else:
        url = f"{base_url}{path}"

    req = urllib.request.Request(url, headers=_headers(), method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def post(path, body=None, base_url=None, extra_headers=None):
    base_url = base_url or _env("OMS_BASE_URL")
    payload = json.dumps(body).encode() if body is not None else b""
    headers = _headers()
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=payload,
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def add_config_arg(parser):
    """给 argparse 添加标准 --config 参数"""
    parser.add_argument(
        "--config",
        default=None,
        help='JSON 配置，如 \'{"baseUrl":"https://...","tenantId":"LT","merchantNo":"LAN0000002","username":"x@item.com","password":"xxx"}\''
    )

def load_config_arg(args):
    """解析 --config 并注入到 oms_client"""
    if hasattr(args, "config") and args.config:
        init(json.loads(args.config))
