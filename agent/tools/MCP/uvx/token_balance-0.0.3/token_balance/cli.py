"""命令行入口：python -m token_balance [check|query] ..."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import List, Optional

import aiohttp

from . import __version__
from .config import (
    AppConfig,
    Service,
    ensure_config_file,
    load_config,
    resolve_secret,
    service_from_dict,
    DEFAULT_CONFIG_FILE,
)
from .fetchers import (
    BUILTIN_PLATFORMS,
    BalanceResult,
    NewApiTokenFetcher,
    mask_key,
    query_all,
    query_by_url,
)


# ==================== 工具函数 ====================

def find_services(cfg: AppConfig, keywords: List[str], extra_aliases: Optional[dict] = None) -> List[Service]:
    """按关键字（服务名/显示名/平台类型/base_url/平台别名）筛选服务。"""
    hits: List[Service] = []
    seen = set()
    for kw in keywords:
        k = kw.lower()
        for svc in cfg.services:
            if svc.name in seen:
                continue
            aliases = set(a.lower() for a in BUILTIN_PLATFORMS.get(svc.type, {}).get("aliases", []))
            if extra_aliases:
                aliases.update(
                    a.lower().strip()
                    for a in str(extra_aliases.get(svc.type, "")).split(",")
                    if a.strip()
                )
            if (
                k in svc.name.lower()
                or k in svc.label.lower()
                or k in svc.type.lower()
                or k in svc.base_url.lower()
                or k in aliases
            ):
                hits.append(svc)
                seen.add(svc.name)
    return hits


def match_platform(keyword: str, extra_aliases: Optional[dict] = None) -> Optional[str]:
    """按名称/别名匹配内置平台，返回平台 key。extra_aliases 来自配置 platform_aliases。"""
    k = keyword.lower().strip()
    for pkey, preset in BUILTIN_PLATFORMS.items():
        aliases = set(a.lower() for a in preset.get("aliases", []))
        if extra_aliases:
            extra = extra_aliases.get(pkey, "")
            aliases.update(a.lower().strip() for a in str(extra).split(",") if a.strip())
        if k == pkey or k in aliases:
            return pkey
    return None


def parse_newapi_conn(target: str) -> Optional[tuple]:
    """解析 NewAPI 面板复制的连接 JSON。

    形如：{"_type":"newapi_channel_conn","key":"sk-xxx","url":"https://..."}
    返回 (url, key, name)，解析失败或字段缺失返回 None。
    """
    try:
        data = json.loads(target)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    url = str(data.get("url") or "").strip()
    key = str(data.get("key") or "").strip()
    if not (url and key):
        return None
    return (url, key, str(data.get("name") or ""))


# ==================== 输出 ====================

def _disp_width(text: str) -> int:
    """估算显示宽度：CJK 等全角字符占 2 列。"""
    return sum(2 if ord(ch) > 0x2E7F else 1 for ch in text)


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _disp_width(text))


def _balance_text(r: BalanceResult) -> str:
    if r.remaining or r.total:
        parts = [f"剩余 {r.remaining}"]
        if r.total and str(r.total) != str(r.remaining):
            parts.append(f"总额 {r.total}")
        if r.used and str(r.used) not in ("0", "0.0", "0.00", ""):
            parts.append(f"已用 {r.used}")
        return " | ".join(parts)
    return r.rendered or ""


def format_text(results: List[BalanceResult], config_errors: List[str], title: str) -> str:
    """默认文本输出：成功项与失败项分组展示。"""
    ok_items = [r for r in results if r.ok]
    fail_items = [r for r in results if not r.ok]
    lines = [f"🔍 {title}", "-" * 72]

    for r in ok_items:
        key = f" [{r.api_key_masked}]" if r.api_key_masked else ""
        lines.append(f"✅ {_pad(r.name, 20)}{key}  {_pad(r.currency or '', 6)}{_balance_text(r)}")
        if r.raw_info:
            lines.append(f"{'':<26}└ {r.raw_info}")

    if fail_items:
        lines.append("-" * 72)
        lines.append(f"❌ 失败 ({len(fail_items)}):")
        for r in fail_items:
            lines.append(f"❌ {_pad(r.name, 20)}  {r.error}")

    for err in config_errors:
        lines.append(f"❌ {err}")

    lines.append("-" * 72)
    failed = len(fail_items) + len(config_errors)
    lines.append(f"共 {len(results) + len(config_errors)} 项，成功 {len(ok_items)}，失败 {failed}")
    return "\n".join(lines)


def format_templated(results: List[BalanceResult], config_errors: List[str], title: str, cfg: AppConfig) -> str:
    """可自定义模板输出：成功/失败分组，各块用配置模板渲染。"""
    header = cfg.header_template.replace("{{title}}", title) if cfg.header_template else f"💰 **{title}**"
    sep = cfg.separator_template or "═" * 40
    item_sep = cfg.item_separator_template
    section_sep = cfg.section_separator_template or sep
    success_t = cfg.success_template or "🟢 **{{source_name}}**\n  💵 {{balance}} {{currency}}\n{{smart_balance}}"
    error_t = cfg.error_template or "🔴 **{{source_name}}**\n  ❌ {{error}}"

    lines = [header, sep]
    ok_items = [r for r in results if r.ok]
    fail_items = [r for r in results if not r.ok]

    for i, r in enumerate(ok_items):
        lines.append(r.render_success(success_t, r.api_key_masked))
        if i < len(ok_items) - 1 and item_sep:
            lines.append(item_sep)

    if ok_items and (fail_items or config_errors):
        lines.append(section_sep)

    for i, r in enumerate(fail_items):
        lines.append(r.render_error(error_t, r.api_key_masked))
        if i < len(fail_items) - 1 and item_sep:
            lines.append(item_sep)

    for err in config_errors:
        lines.append(f"❌ {err}")

    lines.append(sep)
    lines.append(f"共 {len(results) + len(config_errors)} 项，成功 {len(ok_items)}，失败 {len(fail_items) + len(config_errors)}")
    return "\n".join(lines)


def format_json(results: List[BalanceResult], config_errors: List[str], title: str) -> str:
    ok_count = sum(1 for r in results if r.ok)
    return json.dumps(
        {
            "title": title,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total": len(results) + len(config_errors),
                "success": ok_count,
                "failed": len(results) - ok_count + len(config_errors),
            },
            "results": [r.to_dict() for r in results],
            "config_errors": config_errors,
        },
        ensure_ascii=False,
        indent=2,
    )


# ==================== 子命令 ====================

def _load_cfg_optional(path: str) -> Optional[AppConfig]:
    if os.path.exists(path):
        return load_config(path)
    return None


async def _run_check(args: argparse.Namespace) -> int:
    path = args.config or DEFAULT_CONFIG_FILE
    if not os.path.exists(path):
        if ensure_config_file(path):
            print(
                f"已自动生成配置文件模板: {path}\n"
                f"请填写密钥后重新运行。",
                file=sys.stderr,
            )
        else:
            print(f"未找到配置文件: {path}", file=sys.stderr)
        return 2

    cfg = load_config(path)
    if args.timeout:
        cfg.timeout = args.timeout

    services = cfg.services
    names = getattr(args, "name", None) or []
    if names:
        services = find_services(cfg, names, cfg.platform_aliases)
        if not services:
            available = ", ".join(s.name for s in cfg.services) or "（无）"
            print(f"未匹配到任何服务: {' '.join(names)}。可用服务: {available}")
            return 1

    title = "余额查询结果"
    if services:
        title += "（" + ", ".join(s.name for s in services) + "）"

    results = await query_all(services, timeout=cfg.timeout, concurrency=cfg.concurrency)

    use_templates = any([cfg.success_template, cfg.error_template, cfg.header_template])
    if args.json:
        output = format_json(results, cfg.errors, title)
    elif use_templates:
        output = format_templated(results, cfg.errors, title, cfg)
    else:
        output = format_text(results, cfg.errors, title)
    print(output)
    return 0


async def _run_query(args: argparse.Namespace) -> int:
    target = args.target.strip()
    keys = [resolve_secret(k) for k in args.keys]
    timeout = args.timeout or 10.0
    cfg_path = args.config or DEFAULT_CONFIG_FILE
    cfg = _load_cfg_optional(cfg_path)
    extra_aliases = cfg.platform_aliases if cfg else {}

    results: List[BalanceResult] = []

    # 1) NewAPI 连接信息 JSON 粘贴：{"_type":"newapi_channel_conn","key":"sk-xxx","url":"https://..."}
    if target.startswith("{"):
        conn = parse_newapi_conn(target)
        if not conn:
            print(f"无法解析 NewAPI 连接 JSON: {target[:120]}")
            return 1
        url, conn_key, name = conn
        keys_to_query = [conn_key] + [k for k in keys if k and k != conn_key]
        display = name or "NEW API"
        async with aiohttp.ClientSession() as session:
            for key in keys_to_query:
                svc = Service(name=display, type="newapi", api_key=key, base_url=url, display_name=display)
                r = await NewApiTokenFetcher(svc).fetch(session, timeout)
                r.api_key_masked = mask_key(key)
                results.append(r)

    # 2) 自定义 API 地址：自动识别 OpenAI Billing / New API 格式（多 key 并发）
    elif target.startswith(("http://", "https://")):
        async with aiohttp.ClientSession() as session:
            results = list(
                await asyncio.gather(
                    *(query_by_url(session, target, k, timeout=timeout) for k in keys)
                )
            )

    else:
        # 3) 内置平台（支持配置的自定义别名）
        pkey = match_platform(target, extra_aliases)
        if pkey:
            preset = BUILTIN_PLATFORMS[pkey]
            if preset.get("requires_base_url"):
                print(
                    f"平台 {pkey} 需要 base_url。\n"
                    f"用法: python -m token_balance query https://你的中转站地址 <key>"
                )
                return 1
            services = [
                service_from_dict(
                    f"临时-{pkey}-{i + 1}",
                    {"type": pkey, "api_key": key, "display_name": preset.get("display_name", pkey)},
                )
                for i, key in enumerate(keys)
            ]
            results = await query_all(services, timeout=timeout, concurrency=10)
        else:
            # 4) 配置文件中已有的服务名
            if cfg:
                matched = find_services(cfg, [target])
                if matched:
                    services = []
                    for svc in matched:
                        for key in keys:
                            base = {"base_url": svc.base_url} if svc.base_url else {}
                            services.append(service_from_dict(svc.name, {"type": svc.type, "api_key": key, **base}))
                    results = await query_all(services, timeout=timeout, concurrency=10)

            if not results:
                platforms = ", ".join(sorted(BUILTIN_PLATFORMS.keys()))
                print(
                    f"无法识别 '{target}'。\n"
                    f"支持的内置平台: {platforms}\n"
                    f"或直接传入 API 地址，例如: python -m token_balance query https://api.example.com/v1 sk-xxx"
                )
                return 1

    title = f"余额查询：{target}"
    output = format_json(results, [], title) if args.json else format_text(results, [], title)
    print(output)
    return 0


# ==================== 入口 ====================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="token_balance",
        description="多厂商 Token 余额查询工具",
        epilog="示例:\n"
        "  python -m token_balance                        # 查询 config.yaml 中所有服务\n"
        "  python -m token_balance check deepseek         # 只查询 deepseek\n"
        "  python -m token_balance query ds sk-xxx        # 临时查询 DeepSeek\n"
        "  python -m token_balance query https://api.example.com/v1 sk-xxx\n"
        "  python -m token_balance query '{\"key\":\"sk-xxx\",\"url\":\"https://newapi.example.com\"}'\n"
        "  python -m token_balance --json                 # JSON 输出",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-c", "--config", default=None, help=f"配置文件路径（默认 {DEFAULT_CONFIG_FILE} 或 $TOKEN_BALANCE_CONFIG）")
    parser.add_argument("-t", "--timeout", type=float, default=None, help="请求超时秒数（默认取配置中的 timeout）")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    parser.add_argument("-V", "--version", action="version", version=f"token_balance {__version__}")

    sub = parser.add_subparsers(dest="cmd")
    p_check = sub.add_parser("check", help="查询配置文件中的服务")
    p_check.add_argument("name", nargs="*", help="服务名/平台类型关键字，留空查询全部")
    p_query = sub.add_parser("query", help="临时查询: query <平台名/API地址/NewAPI-JSON> <key1> [key2 ...]")
    p_query.add_argument("target", help="平台名/别名、http(s):// 地址，或 NewAPI 连接 JSON")
    p_query.add_argument("keys", nargs="*", help="一个或多个 API Key（也支持 env:变量名）")
    return parser


def _force_utf8_stdio() -> None:
    """Windows 下管道/重定向时 Python 默认用本地代码页（如 GBK），强制 UTF-8 保证中文不乱码。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError, OSError):
            pass


def main(argv: Optional[List[str]] = None) -> int:
    _force_utf8_stdio()
    args = build_parser().parse_args(argv)
    if args.cmd == "query":
        return asyncio.run(_run_query(args))
    return asyncio.run(_run_check(args))


if __name__ == "__main__":
    sys.exit(main())