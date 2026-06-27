"""MCP tools for 1Panel core panel management."""

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
    """Register all core-panel-management MCP tools."""

    # ------------------------------------------------------------------ #
    # Paginated list endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_logs(rows: int = 20) -> str:
        """操作日志 — 时间、操作内容"""
        p = get_client()
        data = p.post("/core/logs/operation", {
            "page": 1, "pageSize": rows,
            "orderBy": "createdAt", "order": "descending",
        })
        lines, items = fmt_search(data, "操作日志")
        for log in items[:rows]:
            lines.append(
                f"  {log.get('createdAt', '?')}  {str(log.get('operation', '?'))[:60]}"
            )
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_settings() -> str:
        """面板基础设置 — 名称、端口、版本等"""
        p = get_client()
        data = p.post("/settings/search", {"page": 1, "pageSize": 50})
        info = {}
        if isinstance(data, list):
            for s in data:
                info[s.get("key", "")] = s.get("value", "")
        lines = [header("面板设置")]
        for k, v in info.items():
            lines.append(f"  {k}: {fmt_val(v)}")
        if not info:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # GET / single-object endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_upgrade_info() -> str:
        """面板升级信息 — 当前版本、最新版本"""
        p = get_client()
        data = p.get("/core/upgrade/info")
        return fmt_generic(data, "面板升级信息")

    @mcp.tool()
    def panel_ssl_cert_info() -> str:
        """面板 SSL 证书信息 — 域名、到期时间、颁发者"""
        p = get_client()
        data = p.get("/core/ssl/info")
        return fmt_generic(data, "面板 SSL 证书")

    @mcp.tool()
    def panel_dashboard_memo() -> str:
        """仪表盘备忘录 — 自定义备忘内容"""
        p = get_client()
        data = p.get("/core/dashboard/memo")
        return fmt_generic(data, "仪表盘备忘录")

    @mcp.tool()
    def panel_login_setting() -> str:
        """登录认证设置 — 登录方式、安全策略"""
        p = get_client()
        data = p.get("/core/login/setting")
        return fmt_generic(data, "登录设置")

    @mcp.tool()
    def panel_commands_tree() -> str:
        """命令树 — 可用的系统命令分类"""
        p = get_client()
        data = p.get("/core/commands/tree")
        lines = [header("命令树")]
        if isinstance(data, list):
            for node in data:
                name = node.get("name", node.get("title", "?"))
                children = node.get("children", node.get("items", []))
                lines.append(f"  {fmt_val(name)}")
                for child in (children or [])[:20]:
                    child_name = child.get("name", child.get("title", "?"))
                    lines.append(f"    - {fmt_val(child_name)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_commands_list() -> str:
        """命令列表 — 所有已注册命令"""
        p = get_client()
        data = p.get("/core/commands/list")
        lines = [header("命令列表")]
        if isinstance(data, list):
            for cmd in data:
                name = cmd.get("name", cmd.get("command", "?"))
                desc = cmd.get("description", cmd.get("desc", ""))
                lines.append(f"  {fmt_val(name)}  {fmt_val(desc)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_system_address() -> str:
        """系统地址信息 — 面板访问地址、IP"""
        p = get_client()
        data = p.get("/core/system/address")
        return fmt_generic(data, "系统地址")

    @mcp.tool()
    def panel_upgrade_releases() -> str:
        """面板升级发布日志 — 版本历史"""
        p = get_client()
        data = p.get("/core/upgrade/releases")
        lines = [header("版本发布历史")]
        if isinstance(data, list):
            for release in data:
                version = release.get("version", release.get("tag", "?"))
                notes = release.get("notes", release.get("description", ""))
                date = release.get("createdAt", release.get("date", ""))
                lines.append(f"  v{version}  ({fmt_val(date)})")
                if notes:
                    lines.append(f"    {fmt_val(notes, 120)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_terminal_setting() -> str:
        """终端设置 — 字体、样式、安全配置"""
        p = get_client()
        data = p.get("/core/terminal/setting")
        return fmt_generic(data, "终端设置")

    @mcp.tool()
    def panel_available_status() -> str:
        """系统可用状态 — 各服务健康检查"""
        p = get_client()
        data = p.get("/core/available/status")
        lines = [header("系统可用状态")]
        if isinstance(data, dict):
            for k, v in data.items():
                st = icon_green() if v else icon_red()
                lines.append(f"  {st} {k}: {v}")
        elif isinstance(data, list):
            for item in data:
                name = item.get("name", item.get("service", "?"))
                ok = item.get("status", item.get("available", False))
                st = icon_green() if ok else icon_red()
                lines.append(f"  {st} {fmt_val(name)}: {ok}")
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # POST endpoints with parameters
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_setting_by_key_post(key: str) -> str:
        """按 Key 查询系统设置 (POST /core/settings/by)"""
        p = get_client()
        data = p.post("/core/settings/by", {"key": key})
        return fmt_generic(data, f"系统设置: {key}")

    @mcp.tool()
    def panel_release_notes(version: str) -> str:
        """版本发布说明 — 按版本查询"""
        p = get_client()
        data = p.post("/core/upgrade/release", {"version": version})
        return fmt_generic(data, f"版本发布说明: {version}")

    @mcp.tool()
    def panel_backup_client_info(type: str = "LOCAL") -> str:
        """备份账号基础信息"""
        p = get_client()
        data = p.post("/core/backup/client/info", {"type": type})
        return fmt_generic(data, f"备份账号信息 ({type})")

    # -- 收集 handler 供 resources 复用 --
    if handlers is not None:
        for _name, _fn in list(locals().items()):
            if _name.startswith("panel_") and callable(_fn):
                handlers[_name] = _fn
