"""MCP tools for 1Panel App Store management."""

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
    """Register all app-store-related MCP tools."""

    # ------------------------------------------------------------------ #
    # Paginated list endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_apps() -> str:
        """已安装的应用商店应用 — 名称、版本、状态"""
        p = get_client()
        data = p.get("/apps/installed/list", {"page": 1, "pageSize": 50})
        lines, items = fmt_search(data, "已安装应用")
        for app in items:
            st = icon_green() if app.get("status") == "Running" else icon_red()
            lines.append(f"  {st} {app.get('name', '?')}  v{app.get('version', '?')}  [{app.get('status', '?')}]")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_app_store_list() -> str:
        """应用商店应用列表 — 所有可用应用"""
        p = get_client()
        data = p.get("/apps/store/list", {"page": 1, "pageSize": 50})
        lines, items = fmt_search(data, "应用商店")
        for app in items:
            lines.append(f"  {app.get('name', '?')}  v{app.get('version', '?')}  [{app.get('description', '?')}]")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # POST / single-object endpoints (by key)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_app_detail(key: str) -> str:
        """应用详情 — 按 key 查询"""
        p = get_client()
        data = p.post("/apps/store/detail/bykey", {"key": key})
        return fmt_generic(data, f"应用详情: {key}")

    @mcp.tool()
    def panel_app_installed_conf(key: str) -> str:
        """应用默认配置 — 按 key 查询"""
        p = get_client()
        data = p.post("/apps/installed/conf", {"key": key})
        return fmt_generic(data, f"应用默认配置: {key}")

    @mcp.tool()
    def panel_app_conninfo(key: str) -> str:
        """应用连接信息 — 账号/密码/端口"""
        p = get_client()
        data = p.post("/apps/installed/conninfo", {"key": key})
        return fmt_generic(data, f"应用连接信息: {key}")

    @mcp.tool()
    def panel_app_installed_loadport(key: str) -> str:
        """应用端口信息 — 按 key 查询"""
        p = get_client()
        data = p.post("/apps/installed/loadport", {"key": key})
        return fmt_generic(data, f"应用端口: {key}")

    @mcp.tool()
    def panel_app_service(key: str) -> str:
        """应用服务详情 — 按 key 查询"""
        p = get_client()
        data = p.post("/apps/installed/service", {"key": key})
        return fmt_generic(data, f"应用服务: {key}")

    # ------------------------------------------------------------------ #
    # POST / single-object endpoints (by id)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_app_detail_by_id(id: int) -> str:
        """应用详情（按 ID）"""
        p = get_client()
        data = p.post("/apps/store/detail/byid", {"id": id})
        return fmt_generic(data, f"应用详情 (ID: {id})")

    # ------------------------------------------------------------------ #
    # GET / single-object endpoints (with query params)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_app_installed_detail(id: int) -> str:
        """已安装应用详情 — 安装信息"""
        p = get_client()
        data = p.get("/apps/installed/detail", {"id": id})
        return fmt_generic(data, f"已安装应用详情 (ID: {id})")

    @mcp.tool()
    def panel_app_installed_params(id: int) -> str:
        """已安装应用参数 — 安装时的配置参数"""
        p = get_client()
        data = p.get("/apps/installed/param", {"id": id})
        return fmt_generic(data, f"已安装应用参数 (ID: {id})")

    # ------------------------------------------------------------------ #
    # Simple GET / single-object endpoints (no params)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_app_check_updates() -> str:
        """应用更新检查 — 有更新的应用列表"""
        p = get_client()
        data = p.get("/apps/installed/checkupdates")
        lines = [header("应用更新检查")]
        if isinstance(data, list):
            for upd in data:
                name = upd.get("name", upd.get("app", "?"))
                old_ver = upd.get("oldVersion", upd.get("currentVersion", "?"))
                new_ver = upd.get("newVersion", upd.get("latestVersion", "?"))
                lines.append(f"  {name}  {old_ver} -> {new_ver}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (无可用更新)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_app_ignored_upgrades() -> str:
        """已忽略升级的应用列表"""
        p = get_client()
        data = p.get("/apps/ignored/upgrade")
        lines = [header("已忽略升级的应用")]
        if isinstance(data, list):
            for app in data:
                name = app.get("name", app.get("app", "?"))
                version = app.get("version", app.get("ignoredVersion", "?"))
                lines.append(f"  {name}  v{version}")
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
