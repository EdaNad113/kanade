"""MCP tools for database management via 1Panel API."""

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
    """Register all database-related MCP tools."""

    # ------------------------------------------------------------------ #
    # Combined database listing
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_databases() -> str:
        """数据库列表 — 类型、版本"""
        p = get_client()
        mysql_data = p.get("/databases/db/list/mysql")
        pg_data = p.get("/databases/db/list/postgresql")
        lines = [header("数据库列表")]
        for item in mysql_data or []:
            name = item.get("name", "?")
            version = item.get("version", item.get("v", "?"))
            lines.append(f"  MySQL: {fmt_val(name)} v{version}")
        for item in pg_data or []:
            name = item.get("name", "?")
            version = item.get("version", item.get("v", "?"))
            lines.append(f"  PostgreSQL: {fmt_val(name)} v{version}")
        if not mysql_data and not pg_data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # MySQL status / config endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_mysql_status() -> str:
        """MySQL 运行状态 — 连接数、运行时间"""
        p = get_client()
        data = p.get("/databases/mysql/status")
        return fmt_generic(data, "MySQL 运行状态")

    @mcp.tool()
    def panel_mysql_variables() -> str:
        """MySQL 变量列表 — 重要配置参数"""
        p = get_client()
        data = p.get("/databases/mysql/variables")
        lines = [header("MySQL 变量")]
        if isinstance(data, list):
            for var in data:
                name = var.get("name", var.get("variable_name", "?"))
                value = var.get("value", "")
                lines.append(f"  {name}: {fmt_val(value)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_mysql_collation() -> str:
        """MySQL 排序规则选项"""
        p = get_client()
        data = p.get("/databases/mysql/collation")
        lines = [header("MySQL 排序规则")]
        if isinstance(data, list):
            for coll in data:
                name = coll.get("name", coll.get("collation", str(coll)))
                lines.append(f"  {fmt_val(name)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_mysql_remote() -> str:
        """MySQL 远程访问配置"""
        p = get_client()
        data = p.get("/databases/mysql/remote")
        return fmt_generic(data, "MySQL 远程访问配置")

    # ------------------------------------------------------------------ #
    # Redis status / config endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_redis_status() -> str:
        """Redis 运行状态 — 内存、连接数、命中率"""
        p = get_client()
        data = p.get("/databases/redis/status")
        return fmt_generic(data, "Redis 运行状态")

    @mcp.tool()
    def panel_redis_conf() -> str:
        """Redis 配置 — 当前配置参数"""
        p = get_client()
        data = p.get("/databases/redis/conf")
        return fmt_generic(data, "Redis 配置")

    @mcp.tool()
    def panel_redis_persistence() -> str:
        """Redis 持久化配置 — RDB/AOF 设置"""
        p = get_client()
        data = p.get("/databases/redis/persistence")
        return fmt_generic(data, "Redis 持久化配置")

    # ------------------------------------------------------------------ #
    # Database list / detail endpoints (with parameters)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_db_list_by_type(type: str = "mysql") -> str:
        """按类型列出数据库"""
        p = get_client()
        data = p.get(f"/databases/db/list/{type}")
        lines = [header(f"数据库列表 ({type})")]
        if isinstance(data, list):
            for item in data:
                name = item.get("name", "?")
                version = item.get("version", item.get("v", "?"))
                lines.append(f"  {fmt_val(name)} v{version}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_db_detail_by_name(name: str) -> str:
        """数据库详情 — 按名称查询"""
        p = get_client()
        data = p.get("/databases/db/detail", {"name": name})
        return fmt_generic(data, f"数据库详情: {name}")

    @mcp.tool()
    def panel_db_check(name: str, type: str = "mysql") -> str:
        """检查数据库是否可连接"""
        p = get_client()
        data = p.get("/databases/db/check", {"name": name, "type": type})
        lines = [header(f"数据库连接检查 ({type}:{name})")]
        if isinstance(data, dict):
            ok = data.get("status", data.get("ok", data.get("success", True)))
            st = icon_green() if ok else icon_red()
            lines.append(f"  {st} {fmt_val(data)}")
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_db_base_info(name: str, type: str = "mysql") -> str:
        """数据库基础信息 — 版本、大小"""
        p = get_client()
        data = p.get("/databases/db/baseinfo", {"name": name, "type": type})
        return fmt_generic(data, f"数据库基础信息 ({type}:{name})")

    @mcp.tool()
    def panel_db_conf_file(type: str = "mysql") -> str:
        """数据库配置文件内容"""
        p = get_client()
        data = p.get(f"/databases/db/config/{type}")
        return fmt_generic(data, f"数据库配置文件 ({type})")

    @mcp.tool()
    def panel_db_item(type: str = "mysql") -> str:
        """按类型获取数据库项列表"""
        p = get_client()
        data = p.get(f"/databases/db/item/{type}")
        lines = [header(f"数据库项 ({type})")]
        if isinstance(data, list):
            for item in data:
                name = item.get("name", "?")
                lines.append(f"  {fmt_val(name)}")
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
