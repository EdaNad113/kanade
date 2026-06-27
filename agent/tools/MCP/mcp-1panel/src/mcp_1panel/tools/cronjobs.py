"""MCP tools for cronjob-related 1Panel API endpoints."""

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
    """Register all cronjob-related MCP tools."""

    # ------------------------------------------------------------------ #
    # Search / paginated endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_cronjobs() -> str:
        """计划任务列表 — 名称、类型、Cron 表达式"""
        p = get_client()
        data = p.post("/cronjobs/search", {
            "page": 1, "pageSize": 20,
            "orderBy": "createdAt", "order": "descending",
        })
        lines, items = fmt_search(data, "计划任务")
        for c in items:
            name = c.get("name", "?")
            ctype = c.get("type", "?")
            spec = c.get("cronSpec", c.get("spec", ""))
            status = icon_green() if c.get("status") == "Enabled" else icon_red()
            lines.append(f"  {status} {fmt_val(name)}  [{ctype}]  {fmt_val(spec)}")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_cronjob_records(id: int) -> str:
        """计划任务执行记录 — 历史执行日志"""
        p = get_client()
        data = p.post("/cronjobs/records/search", {
            "page": 1, "pageSize": 20, "cronjobID": id,
        })
        lines, items = fmt_search(data, f"任务执行记录 (ID: {id})")
        for r in items:
            rid = r.get("id", "?")
            start = r.get("startTime", r.get("startedAt", "?"))
            status = icon_green() if r.get("status") == "success" else icon_red()
            lines.append(f"  #{rid} {status} {fmt_val(start)}")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # GET / single-object endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_cronjob_info(id: int) -> str:
        """计划任务详情 — 配置信息"""
        p = get_client()
        data = p.get("/cronjobs/info", {"id": id})
        return fmt_generic(data, f"计划任务详情 (ID: {id})")

    @mcp.tool()
    def panel_cronjob_record_log(id: int) -> str:
        """计划任务执行日志详情"""
        p = get_client()
        data = p.get("/cronjobs/records/log", {"id": id})
        return fmt_generic(data, f"执行日志 (ID: {id})")

    @mcp.tool()
    def panel_script_options() -> str:
        """脚本选项 — 可用的脚本参数"""
        p = get_client()
        data = p.get("/cronjobs/script/options")
        return fmt_generic(data, "脚本选项")

    # ------------------------------------------------------------------ #
    # POST endpoints with payload
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_cronjob_next(id: int, cronSpec: str) -> str:
        """计划任务下次执行时间"""
        p = get_client()
        data = p.post("/cronjobs/next", {"id": id, "cronSpec": cronSpec})
        return fmt_generic(data, f"下次执行 (ID: {id})")

    # -- 收集 handler 供 resources 复用 --
    if handlers is not None:
        for _name, _fn in list(locals().items()):
            if _name.startswith("panel_") and callable(_fn):
                handlers[_name] = _fn
