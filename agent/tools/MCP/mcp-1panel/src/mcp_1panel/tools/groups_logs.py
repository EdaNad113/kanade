"""MCP tools for 1Panel groups and logs endpoints."""

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
    """Register all group and log related MCP tools."""

    # ------------------------------------------------------------------ #
    # Groups
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_groups() -> str:
        """分组列表 — 所有资源的分组"""
        p = get_client()
        data = p.post("/groups/search", {
            "page": 1, "pageSize": 50,
        })
        lines, items = fmt_search(data, "分组列表")
        for g in items:
            name = g.get("name", "?")
            gtype = g.get("type", g.get("groupType", "?"))
            lines.append(f"  {fmt_val(name)}  [{gtype}]")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Logs
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_system_log_files() -> str:
        """系统日志文件列表"""
        p = get_client()
        data = p.get("/core/logs/system/files")
        lines = [header("系统日志文件")]
        if isinstance(data, list):
            for f in data:
                name = f if isinstance(f, str) else f.get("name", f.get("file", "?"))
                lines.append(f"  {fmt_val(name)}")
        elif isinstance(data, dict):
            for k, v in data.items():
                lines.append(f"  {k}: {fmt_val(v)}")
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_executing_tasks() -> str:
        """正在执行的任务数"""
        p = get_client()
        data = p.get("/core/tasks/executing")
        return fmt_generic(data, "正在执行的任务")

    # ------------------------------------------------------------------ #
    # Paginated log endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_login_logs(rows: int = 20) -> str:
        """登录日志 — 最近登录记录"""
        p = get_client()
        data = p.post("/core/logs/login", {
            "page": 1, "pageSize": rows,
            "orderBy": "createdAt", "order": "descending",
        })
        lines, items = fmt_search(data, "登录日志")
        for log in items[:rows]:
            ip = log.get("ip", log.get("sourceIP", "?"))
            ua = log.get("agent", log.get("userAgent", ""))
            created = log.get("createdAt", log.get("time", "?"))
            status_icon = icon_green() if log.get("status") == "success" else icon_red()
            lines.append(f"  {status_icon} {created}  IP: {ip}")
            if ua:
                lines.append(f"    UA: {fmt_val(ua, 80)}")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_task_logs(rows: int = 20) -> str:
        """任务执行日志 — 系统任务记录"""
        p = get_client()
        data = p.post("/core/logs/tasks", {
            "page": 1, "pageSize": rows,
            "orderBy": "createdAt", "order": "descending",
        })
        lines, items = fmt_search(data, "任务执行日志")
        for log in items[:rows]:
            task = log.get("task", log.get("name", "?"))
            status = log.get("status", "?")
            created = log.get("createdAt", log.get("time", "?"))
            s_icon = icon_green() if status in ("success", "done", "completed") else icon_red()
            lines.append(f"  {s_icon} {created}  {fmt_val(task)}  [{status}]")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    # -- 收集 handler 供 resources 复用 --
    if handlers is not None:
        for _name, _fn in list(locals().items()):
            if _name.startswith("panel_") and callable(_fn):
                handlers[_name] = _fn
