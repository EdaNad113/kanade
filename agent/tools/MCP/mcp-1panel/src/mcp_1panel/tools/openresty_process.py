"""MCP tools for 1Panel OpenResty (5) and Process (2) modules."""

from typing import Any, Callable, Dict, List
from mcp_1panel.tools.helpers import (
    icon_green,
    icon_red,
    icon_lock,
    icon_unlock,
    icon_status,
    header,
    fmt_val,
    fmt_obj,
    fmt_list,
    fmt_search,
    fmt_generic,
)


def register_tools(mcp, get_client, handlers=None):
    """Register all OpenResty and Process MCP tools."""

    # ------------------------------------------------------------------ #
    # OpenResty (5 tools)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_openresty() -> str:
        """OpenResty 状态 — 活动连接、请求数"""
        p = get_client()
        data = p.get("/openresty/status")
        return fmt_generic(data, "OpenResty 状态")

    @mcp.tool()
    def panel_openresty_config() -> str:
        """OpenResty 配置概览 — 主配置路径、状态"""
        p = get_client()
        data = p.get("/openresty/config")
        return fmt_generic(data, "OpenResty 配置")

    @mcp.tool()
    def panel_openresty_modules() -> str:
        """OpenResty 已加载模块列表"""
        p = get_client()
        data = p.get("/openresty/modules")
        lines = [header("OpenResty 模块")]
        if isinstance(data, list):
            for mod in data:
                if isinstance(mod, dict):
                    name = mod.get("name", mod.get("module", str(mod)))
                    lines.append(f"  {fmt_val(name)}")
                else:
                    lines.append(f"  {fmt_val(mod)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_openresty_https() -> str:
        """默认 HTTPS 配置状态"""
        p = get_client()
        data = p.get("/openresty/https")
        return fmt_generic(data, "OpenResty HTTPS 配置")

    @mcp.tool()
    def panel_openresty_scope(scope: str = "http") -> str:
        """OpenResty 局部配置 — 按范围查询 (http/server/location/upstream)"""
        p = get_client()
        data = p.get("/openresty/scope", {"scope": scope})
        return fmt_generic(data, f"OpenResty 配置 ({scope})")

    # ------------------------------------------------------------------ #
    # Process (2 tools)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_process_listening() -> str:
        """监听端口列表 — 全部进程端口"""
        p = get_client()
        data = p.get("/process/listening")
        lines = [header("监听端口")]
        if isinstance(data, list):
            for proc in data:
                if isinstance(proc, dict):
                    pid = proc.get("PID", proc.get("pid", "?"))
                    port = proc.get("Port", proc.get("port", "?"))
                    proto = proc.get("Protocol", proc.get("protocol", "?"))
                    prog = proc.get("Program", proc.get("program", proc.get("name", "?")))
                    lines.append(f"  [{proto}] 端口 {port}  PID {pid}  {fmt_val(prog)}")
                else:
                    lines.append(f"  {fmt_val(proc)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_process_info(pid: int) -> str:
        """进程详情 — 按 PID 查询"""
        p = get_client()
        data = p.get("/process/info", {"pid": pid})
        return fmt_generic(data, f"进程详情 (PID {pid})")

    # -- 收集 handler 供 resources 复用 --
    if handlers is not None:
        for _name, _fn in list(locals().items()):
            if _name.startswith("panel_") and callable(_fn):
                handlers[_name] = _fn
