"""MCP Server：把 token_balance 暴露为标准 MCP 工具。

供 AI 客户端（Codex / Claude Desktop / Cursor 等）在对话中直接查询
各厂商 Token 余额。共 3 个工具：

- list_services   列出配置中的服务与支持的内置平台（无网络请求）
- query_balances  查询 config.yaml 中全部或指定服务的余额
- query_endpoint  临时查询平台 / API 地址 / NewAPI 连接 JSON

运行方式：
    uvx --from . token-balance-mcp          # 或安装后直接: token-balance-mcp
    python -m token_balance.mcp_server      # 本地开发
    token-balance-mcp --config D:\\path\\config.yaml
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp

from . import __version__
from .cli import find_services, match_platform, parse_newapi_conn
from .config import DEFAULT_CONFIG_FILE, AppConfig, ensure_config_file, load_config, resolve_secret, service_from_dict
from .fetchers import (
    BUILTIN_PLATFORMS,
    BalanceResult,
    NewApiTokenFetcher,
    Service,
    mask_key,
    query_all,
    query_by_url,
)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    raise SystemExit(
        "缺少 mcp 依赖，请先安装: pip install -e \".[mcp]\" 或 pip install mcp"
    )

CACHE_TTL_SECONDS = 30  # 结果缓存时长，防止 LLM 对同一批服务反复调用

# 模块级资源：长连接 session + TTL 缓存
_session: Optional[aiohttp.ClientSession] = None
_cache: Dict[tuple, tuple] = {}


def _get_session() -> aiohttp.ClientSession:
    """惰性创建复用的 aiohttp 长连接 session（在调用方的事件循环中创建）。"""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session


async def _close_session() -> None:
    global _session
    if _session is not None and not _session.closed:
        await _session.close()
    _session = None


async def _cached_async(key: tuple, producer, *args) -> dict:
    """TTL 缓存包装：命中时返回缓存副本并标记 cached=true。"""
    now = time.time()
    hit = _cache.get(key)
    if hit is not None and now - hit[0] < CACHE_TTL_SECONDS:
        result = copy.deepcopy(hit[1])
        result["cached"] = True
        return result
    result = await producer(*args)
    result["cached"] = False
    _cache[key] = (now, result)
    return result


# ==================== 内部处理函数（纯逻辑，便于测试） ====================

def _config_path(override: Optional[str]) -> str:
    return override or os.environ.get("TOKEN_BALANCE_CONFIG") or DEFAULT_CONFIG_FILE


def _try_load_config(path: str) -> Optional[AppConfig]:
    try:
        return load_config(path)
    except Exception:  # noqa: BLE001
        return None


def _build_response(results: List[BalanceResult], config_errors: List[str]) -> dict:
    ok_count = sum(1 for r in results if r.ok)
    return {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total": len(results) + len(config_errors),
            "success": ok_count,
            "failed": len(results) - ok_count + len(config_errors),
        },
        "results": [r.to_dict() for r in results],
        "config_errors": config_errors,
    }


def _error_response(message: str) -> dict:
    return {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {"total": 0, "success": 0, "failed": 1},
        "results": [],
        "config_errors": [message],
    }


def _handle_list_services(config_path: Optional[str] = None) -> dict:
    """列出配置中的服务与内置平台（无网络请求）。"""
    path = _config_path(config_path)
    cfg = _try_load_config(path)
    services = []
    config_errors = []
    if cfg is not None:
        config_errors = cfg.errors
        services = [
            {
                "name": s.name,
                "type": s.type,
                "label": s.label,
                "base_url": s.base_url or "",
                "needs_api_key": bool(s.api_key),
            }
            for s in cfg.services
        ]
    platforms = [
        {
            "type": pkey,
            "display_name": preset.get("display_name", pkey),
            "aliases": preset.get("aliases", []),
            "requires_base_url": bool(preset.get("requires_base_url")),
        }
        for pkey, preset in sorted(BUILTIN_PLATFORMS.items())
    ]
    return {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config_path": path,
        "config_exists": os.path.exists(path),
        "services": services,
        "platforms": platforms,
        "config_errors": config_errors,
    }


async def _handle_query_balances(
    service_names: Optional[List[str]] = None,
    timeout: Optional[float] = None,
    config_path: Optional[str] = None,
) -> dict:
    """查询配置文件中的全部或指定服务余额。"""
    path = _config_path(config_path)
    if not os.path.exists(path):
        return _error_response(
            f"未找到配置文件: {path}。请用 TOKEN_BALANCE_CONFIG 环境变量或 --config 指定，或先创建 config.yaml"
        )
    try:
        cfg = load_config(path)
    except Exception as e:  # noqa: BLE001
        return _error_response(f"配置文件解析失败: {e}")

    if timeout:
        cfg.timeout = timeout

    services = cfg.services
    if service_names:
        services = find_services(cfg, service_names, cfg.platform_aliases)
        if not services:
            available = ", ".join(s.name for s in cfg.services) or "（无）"
            return _error_response(
                f"未匹配到任何服务: {', '.join(service_names)}。可用服务: {available}（可先调用 list_services）"
            )

    results = await query_all(
        services, timeout=cfg.timeout, concurrency=cfg.concurrency, session=_get_session()
    )
    return _build_response(results, cfg.errors)


async def _handle_query_endpoint(
    target: str,
    api_keys: List[str],
    timeout: float = 10.0,
    config_path: Optional[str] = None,
) -> dict:
    """临时查询平台 / API 地址 / NewAPI 连接 JSON 的余额。"""
    keys = [resolve_secret(k) for k in (api_keys or [])]
    session = _get_session()

    if target.startswith("{"):
        # NewAPI 连接信息 JSON 粘贴：key 可从 JSON 内取，命令行 keys 可省略
        conn = parse_newapi_conn(target)
        if not conn:
            return _error_response(f"无法解析 NewAPI 连接 JSON: {target[:120]}")
        url, conn_key, name = conn
        keys_to_query = [conn_key] + [k for k in keys if k and k != conn_key]
        if not keys_to_query:
            return _error_response("未提供 API Key")
        display = name or "NEW API"
        results: List[BalanceResult] = []
        for key in keys_to_query:
            svc = Service(name=display, type="newapi", api_key=key, base_url=url, display_name=display)
            r = await NewApiTokenFetcher(svc).fetch(session, timeout)
            r.api_key_masked = mask_key(key)
            results.append(r)
        return _build_response(results, [])

    if not keys:
        return _error_response("未提供 API Key")

    if target.startswith(("http://", "https://")):
        # API 地址：自动识别 OpenAI Billing / New API（多 key 并发）
        results = list(
            await asyncio.gather(*(query_by_url(session, target, k, timeout=timeout) for k in keys))
        )
        return _build_response(results, [])

    # 平台名 / 别名
    extra_aliases = {}
    cfg = _try_load_config(_config_path(config_path))
    if cfg is not None:
        extra_aliases = cfg.platform_aliases
    pkey = match_platform(target, extra_aliases)
    if not pkey:
        platforms = ", ".join(sorted(BUILTIN_PLATFORMS.keys()))
        return _error_response(f"无法识别 '{target}'。支持的内置平台: {platforms}（或传 API 地址 / NewAPI JSON）")
    preset = BUILTIN_PLATFORMS[pkey]
    if preset.get("requires_base_url"):
        return _error_response(f"平台 {pkey} 需要 base_url，请改用 API 地址或 NewAPI 连接 JSON 形式查询")
    services = [
        service_from_dict(
            f"临时-{pkey}-{i + 1}",
            {"type": pkey, "api_key": key, "display_name": preset.get("display_name", pkey)},
        )
        for i, key in enumerate(keys)
    ]
    results = await query_all(services, timeout=timeout, concurrency=10, session=session)
    return _build_response(results, [])


# ==================== MCP 工具定义 ====================

mcp = FastMCP(
    "token-balance",
    instructions=(
        "查询各 AI 厂商/中转站的 Token 余额（只读工具，密钥自动脱敏）。\n"
        "1. 先调用 list_services 查看配置中的服务与支持的内置平台（含别名）。\n"
        "2. query_balances 查询 config.yaml 中配置的服务。\n"
        "3. query_endpoint 临时查询：平台名/别名、http(s) API 地址（自动识别 OpenAI Billing / New API）、"
        "或 NewAPI 面板复制的连接 JSON。\n"
        "返回的 api_key_masked 是脱敏后的密钥，不要向用户展示完整密钥。"
    ),
)


@mcp.tool()
async def list_services() -> dict:
    """列出配置中的服务与支持的内置平台（含别名）。无网络请求，用于查询前发现可用目标。"""
    return _handle_list_services()


@mcp.tool()
async def query_balances(
    service_names: Optional[List[str]] = None,
    timeout: Optional[float] = None,
) -> dict:
    """查询 config.yaml 中配置的全部或指定服务的 Token 余额（并行、失败隔离）。

    Args:
        service_names: 服务名 / 平台类型 / 别名的过滤列表，省略则查询全部。
        timeout: 覆盖单个请求超时（秒），默认取配置。
    """
    key = (
        "query_balances",
        _config_path(None),
        json.dumps({"names": service_names, "timeout": timeout}, sort_keys=True, ensure_ascii=False),
    )
    return await _cached_async(key, _handle_query_balances, service_names, timeout)


@mcp.tool()
async def query_endpoint(
    target: str,
    api_keys: List[str],
    timeout: float = 10.0,
) -> dict:
    """临时查询平台 / API 端点余额，不依赖配置文件。

    Args:
        target: 平台名或别名（如 ds、硅基）；或 http(s):// 地址（自动识别
            OpenAI Billing → New API 降级）；或 NewAPI 面板复制的连接 JSON
            （形如 {"_type":"newapi_channel_conn","key":"sk-xxx","url":"https://..."}）。
        api_keys: 一个或多个 API Key（也支持 env:环境变量名）。
        timeout: 单个请求超时（秒），默认 10。
    """
    key = (
        "query_endpoint",
        _config_path(None),
        json.dumps({"target": target, "keys": api_keys, "timeout": timeout}, sort_keys=True, ensure_ascii=False),
    )
    return await _cached_async(key, _handle_query_endpoint, target, api_keys, timeout)


# ==================== 只读资源（token://） ====================

@mcp.resource(
    "token://services",
    title="配置的服务列表",
    description="config.yaml 中配置的服务与支持的内置平台（含别名）。无网络请求。",
    mime_type="application/json",
)
async def services_resource() -> str:
    """token://services — 配置的服务与内置平台列表。"""
    return json.dumps(_handle_list_services(), ensure_ascii=False, indent=2)


@mcp.resource(
    "token://balances",
    title="全部余额快照",
    description="实时查询所有配置服务的 Token 余额（并行、失败隔离、密钥脱敏）。",
    mime_type="application/json",
)
async def balances_resource() -> str:
    """token://balances — 所有配置服务的余额快照。"""
    return json.dumps(await _handle_query_balances(None, None), ensure_ascii=False, indent=2)


@mcp.resource(
    "token://balance/{name}",
    title="单个服务余额",
    description="按服务名 / 平台类型 / 别名查询单个服务的余额。",
    mime_type="application/json",
)
async def balance_resource(name: str) -> str:
    """token://balance/{name} — 单个服务的余额。"""
    return json.dumps(await _handle_query_balances([name], None), ensure_ascii=False, indent=2)


# ==================== 入口 ====================

def _ensure_config_and_notify() -> None:
    """首次启动时在目标位置自动生成配置文件模板。

    MCP stdio 协议下 stdout 是协议通道，提示必须走 stderr，避免破坏协议。
    """
    path = _config_path(None)
    if ensure_config_file(path):
        print(
            f"[token-balance] 已自动生成配置文件模板: {path}\n"
            f"[token-balance] 请填写密钥后重启 MCP 实例。",
            file=sys.stderr,
        )


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="token_balance MCP server")
    parser.add_argument(
        "--config", default=None,
        help="配置文件路径（默认 $TOKEN_BALANCE_CONFIG 或当前目录 config.yaml）",
    )
    parser.add_argument(
        "--transport", choices=["stdio", "sse", "http"], default="stdio",
        help="传输方式：stdio（默认，本机 MCP 客户端）/ sse / http（streamable-http，远程访问）",
    )
    parser.add_argument("--host", default="127.0.0.1", help="sse/http 监听地址（默认 127.0.0.1；远程访问需 0.0.0.0）")
    parser.add_argument("--port", type=int, default=8000, help="sse/http 监听端口（默认 8000）")
    parser.add_argument(
        "--mount-path", default=None,
        help="sse 挂载路径（默认 /sse；传 mcp 则端点为 /mcp/sse）",
    )
    parser.add_argument("--version", action="version", version=f"token_balance {__version__}")
    args = parser.parse_args(argv)
    if args.config:
        os.environ["TOKEN_BALANCE_CONFIG"] = args.config
    _ensure_config_and_notify()
    try:
        if args.transport == "stdio":
            mcp.run()
        else:
            _run_remote(args)
    finally:
        try:
            asyncio.run(_close_session())
        except RuntimeError:
            pass


def _run_remote(args: argparse.Namespace) -> None:
    """以 SSE / Streamable HTTP 方式启动（uvicorn 托管 Starlette app）。"""
    import uvicorn

    if args.transport == "sse":
        app = mcp.sse_app(args.mount_path)
        endpoint = f"/{args.mount_path}/sse" if args.mount_path else "/sse"
    else:  # http = streamable-http
        app = mcp.streamable_http_app()
        endpoint = "/mcp"
    print(
        f"[token-balance] MCP server listening: http://{args.host}:{args.port}{endpoint}",
        file=sys.stderr,
    )
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()