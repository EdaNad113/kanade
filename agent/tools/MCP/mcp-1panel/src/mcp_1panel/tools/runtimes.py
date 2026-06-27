"""MCP tools for runtimes (PHP/Node/Supervisor) via 1Panel API."""

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
    """Register all runtime-related MCP tools."""

    # ------------------------------------------------------------------ #
    # Runtime list (paginated search)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_runtimes() -> str:
        """运行环境列表 — PHP/Node 等"""
        p = get_client()
        data = p.post("/runtimes/search", {"page": 1, "pageSize": 20})
        lines, items = fmt_search(data, "运行环境")
        for r in items:
            name = r.get("name", "?")
            rtype = r.get("type", "?")
            ver = r.get("version", "?")
            st_val = r.get("status", "")
            st = icon_status(st_val == "running" or st_val == "1") if st_val else ""
            lines.append(f"  {st} {name}  {rtype}  v{ver}  [{st_val}]")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Runtime detail
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_runtime_detail(id: int) -> str:
        """运行环境详情"""
        p = get_client()
        data = p.get("/runtimes/detail", {"id": id})
        return fmt_generic(data, f"运行环境详情 (ID: {id})")

    # ------------------------------------------------------------------ #
    # PHP extensions (status)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_php_extensions(id: int) -> str:
        """PHP 扩展列表"""
        p = get_client()
        data = p.get("/runtimes/php/extensions", {"id": id})
        lines = [header(f"PHP 扩展 (ID: {id})")]
        if isinstance(data, list):
            for ext in data:
                name = ext.get("name", ext.get("extension", str(ext)))
                loaded = ext.get("loaded", ext.get("status", ""))
                if loaded:
                    st = icon_green() if str(loaded).lower() in ("1", "true", "yes", "enabled") else icon_red()
                    lines.append(f"  {st} {name}")
                else:
                    lines.append(f"  {name}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # PHP config
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_php_config(id: int) -> str:
        """PHP 运行配置"""
        p = get_client()
        data = p.get("/runtimes/php/config", {"id": id})
        return fmt_generic(data, f"PHP 运行配置 (ID: {id})")

    # ------------------------------------------------------------------ #
    # PHP container
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_php_container(id: int) -> str:
        """PHP 容器配置"""
        p = get_client()
        data = p.get("/runtimes/php/container", {"id": id})
        return fmt_generic(data, f"PHP 容器配置 (ID: {id})")

    # ------------------------------------------------------------------ #
    # PHP-FPM config
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_php_fpm_config(id: int) -> str:
        """PHP-FPM 配置"""
        p = get_client()
        data = p.get("/runtimes/php/fpm/config", {"id": id})
        return fmt_generic(data, f"PHP-FPM 配置 (ID: {id})")

    # ------------------------------------------------------------------ #
    # PHP-FPM status
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_php_fpm_status(id: int) -> str:
        """PHP-FPM 运行状态"""
        p = get_client()
        data = p.get("/runtimes/php/fpm/status", {"id": id})
        return fmt_generic(data, f"PHP-FPM 状态 (ID: {id})")

    # ------------------------------------------------------------------ #
    # PHP file (config file content)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_php_file(id: int) -> str:
        """PHP 配置文件内容"""
        p = get_client()
        data = p.get("/runtimes/php/file", {"id": id})
        return fmt_generic(data, f"PHP 配置文件 (ID: {id})")

    # ------------------------------------------------------------------ #
    # Node modules
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_node_modules(id: int) -> str:
        """Node.js 模块列表"""
        p = get_client()
        data = p.get("/runtimes/node/modules", {"id": id})
        lines = [header(f"Node.js 模块 (ID: {id})")]
        if isinstance(data, list):
            for mod in data:
                name = mod.get("name", mod.get("module", str(mod)))
                ver = mod.get("version", "")
                if ver:
                    lines.append(f"  {name}  v{ver}")
                else:
                    lines.append(f"  {name}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Node package (package.json scripts)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_node_package(id: int) -> str:
        """Node.js 包脚本 (package.json)"""
        p = get_client()
        data = p.get("/runtimes/node/package", {"id": id})
        return fmt_generic(data, f"Node.js package.json (ID: {id})")

    # ------------------------------------------------------------------ #
    # Supervisor process detail
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_supervisor_process_detail(id: int) -> str:
        """Supervisor 进程详情"""
        p = get_client()
        data = p.get("/runtimes/supervisor/process/detail", {"id": id})
        return fmt_generic(data, f"Supervisor 进程详情 (ID: {id})")

    # ------------------------------------------------------------------ #
    # PHP available extensions list
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_runtime_php_extensions_list(id: int) -> str:
        """PHP 可用扩展列表"""
        p = get_client()
        data = p.get("/runtimes/php/extensions/list", {"id": id})
        lines = [header(f"PHP 可用扩展 (ID: {id})")]
        if isinstance(data, list):
            for ext in data:
                name = ext.get("name", ext.get("extension", str(ext)))
                installed = ext.get("installed", ext.get("loaded", ""))
                if installed and str(installed).lower() in ("1", "true", "yes", "installed"):
                    st = icon_green()
                    lines.append(f"  {st} {name} (已安装)")
                else:
                    lines.append(f"  {name}")
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
