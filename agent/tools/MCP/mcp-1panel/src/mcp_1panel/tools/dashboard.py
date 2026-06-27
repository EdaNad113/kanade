"""MCP tools for the 1Panel dashboard — overview, monitoring, system info."""

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
    """Register all dashboard-related MCP tools."""

    # ------------------------------------------------------------------ #
    # Multi-call overview
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_overview() -> str:
        """面板总览 — 系统版本、CPU、内存、磁盘、应用/网站/数据库数量"""
        p = get_client()

        # Fetch all data sources in parallel where possible
        os_info = p.get("/dashboard/base/os")
        monitor = p.get("/dashboard/current/0/0")
        apps_resp = p.get("/apps/installed/list", {"page": 1, "pageSize": 1})
        websites_resp = p.post(
            "/websites/search", {"page": 1, "pageSize": 1}
        )
        mysql_list = p.get("/databases/db/list/mysql")
        pg_list = p.get("/databases/db/list/postgresql")

        lines: List[str] = []

        # -- System info --
        lines.append(header("系统信息"))
        if isinstance(os_info, dict):
            for k, v in os_info.items():
                lines.append(f"  {k}: {fmt_val(v)}")

        # -- Resource usage --
        lines.append("")
        lines.append(header("资源使用"))
        if isinstance(monitor, dict):
            cpu = monitor.get("cpuPercent", monitor.get("cpu", "?"))
            mem = monitor.get("memoryPercent", monitor.get("memory", "?"))
            disk = monitor.get("diskPercent", monitor.get("disk", "?"))
            load = monitor.get("load", monitor.get("loadAvg", "?"))
            lines.append(f"  CPU:    {cpu}%")
            lines.append(f"  内存:   {mem}%")
            lines.append(f"  磁盘:   {disk}%")
            lines.append(f"  负载:   {fmt_val(load)}")

        # -- Counts --
        lines.append("")
        lines.append(header("数量统计"))

        # Apps count
        app_total = 0
        if isinstance(apps_resp, dict):
            app_total = apps_resp.get("total", apps_resp.get("count", 0))
        lines.append(f"  应用:     {app_total}")

        # Websites count
        site_total = 0
        if isinstance(websites_resp, dict):
            site_total = websites_resp.get("total", websites_resp.get("count", 0))
        lines.append(f"  网站:     {site_total}")

        # Databases count (MySQL + PostgreSQL)
        mysql_count = len(mysql_list) if isinstance(mysql_list, list) else 0
        pg_count = len(pg_list) if isinstance(pg_list, list) else 0
        lines.append(f"  数据库:   {mysql_count + pg_count}")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Single-call endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_monitor() -> str:
        """实时监控 — CPU/内存/磁盘百分比、负载"""
        p = get_client()
        data = p.get("/dashboard/current/0/0")
        lines = [header("实时监控")]
        if isinstance(data, dict):
            cpu = data.get("cpuPercent", data.get("cpu", "?"))
            mem = data.get("memoryPercent", data.get("memory", "?"))
            disk = data.get("diskPercent", data.get("disk", "?"))
            load = data.get("load", data.get("loadAvg", "?"))
            lines.append(f"  CPU%:   {cpu}%")
            lines.append(f"  内存%:  {mem}%")
            lines.append(f"  磁盘%:  {disk}%")
            lines.append(f"  负载:   {fmt_val(load)}")
        elif isinstance(data, list):
            lines.extend(fmt_list(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_top_cpu() -> str:
        """CPU 占用最高的进程 Top10"""
        p = get_client()
        data = p.get("/dashboard/top/cpu")
        lines = [header("CPU 占用 Top10")]
        if isinstance(data, list):
            for i, proc in enumerate(data, 1):
                name = proc.get("name", proc.get("command", "?"))
                pid = proc.get("pid", "?")
                cpu_pct = proc.get("cpuPercent", proc.get("cpu", "?"))
                lines.append(f"  {i}. PID {pid}  {fmt_val(name)}  ({cpu_pct}%)")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_top_memory() -> str:
        """内存占用最高的进程 Top10"""
        p = get_client()
        data = p.get("/dashboard/top/memory")
        lines = [header("内存占用 Top10")]
        if isinstance(data, list):
            for i, proc in enumerate(data, 1):
                name = proc.get("name", proc.get("command", "?"))
                pid = proc.get("pid", "?")
                mem_pct = proc.get("memoryPercent", proc.get("memory", "?"))
                mem_usage = proc.get("memoryUsage", proc.get("rss", ""))
                detail = f"({mem_pct}%)" if mem_pct != "?" else ""
                if mem_usage:
                    detail += f" [{fmt_val(mem_usage)}]"
                lines.append(f"  {i}. PID {pid}  {fmt_val(name)}  {detail}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_base_info() -> str:
        """面板基本信息 — 系统、内核、运行时间"""
        p = get_client()
        data = p.get("/dashboard/base/os")
        return fmt_generic(data, "系统基础信息")

    @mcp.tool()
    def panel_node_info() -> str:
        """节点信息 — 当前节点运行状态"""
        p = get_client()
        data = p.get("/dashboard/node")
        return fmt_generic(data, "节点信息")

    @mcp.tool()
    def panel_app_launcher() -> str:
        """应用启动器 — 快捷启动的应用列表"""
        p = get_client()
        data = p.get("/dashboard/launcher")
        lines = [header("应用启动器")]
        if isinstance(data, list):
            for app in data:
                name = app.get("name", app.get("label", "?"))
                icon = app.get("icon", "")
                key = app.get("key", "?")
                line = f"  {fmt_val(name)}"
                if icon:
                    line += f"  [{fmt_val(icon)}]"
                line += f"  ({key})"
                lines.append(line)
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_launcher_options() -> str:
        """启动器选项 — 自定义快捷方式"""
        p = get_client()
        data = p.get("/dashboard/launcher/options")
        lines = [header("启动器选项")]
        if isinstance(data, list):
            for opt in data:
                name = opt.get("name", opt.get("label", "?"))
                params = opt.get("params", opt.get("value", ""))
                lines.append(f"  {fmt_val(name)}  {fmt_val(params)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_quick_jump() -> str:
        """快速跳转选项 — 常用导航"""
        p = get_client()
        data = p.get("/dashboard/quick/jump")
        lines = [header("快速跳转")]
        if isinstance(data, list):
            for item in data:
                title = item.get("title", item.get("name", "?"))
                url = item.get("url", item.get("link", ""))
                lines.append(f"  {fmt_val(title)}  ->  {fmt_val(url)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # -- 收集 handler 供 resources 复用 --
    if handlers is not None:
        for _name, _fn in list(locals().items()):
            if _name.startswith("panel_") and callable(_fn):
                handlers[_name] = _fn
