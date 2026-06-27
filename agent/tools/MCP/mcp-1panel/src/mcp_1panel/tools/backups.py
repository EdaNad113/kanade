"""MCP tools for backup-related 1Panel API endpoints."""

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
    """Register all backup-related MCP tools."""

    # ------------------------------------------------------------------ #
    # Search / paginated endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_backups() -> str:
        """备份记录列表 — 类型、文件"""
        p = get_client()
        data = p.post("/backups/record/search", {
            "page": 1, "pageSize": 20, "type": "all",
        })
        lines, items = fmt_search(data, "备份记录")
        for b in items:
            name = b.get("name", b.get("file", "?"))
            bt = b.get("type", "?")
            lines.append(f"  {bt}: {fmt_val(name)}")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_backup_accounts() -> str:
        """备份账号列表 — 存储类型、配置"""
        p = get_client()
        data = p.post("/backups/account/search", {"page": 1, "pageSize": 20})
        lines, items = fmt_search(data, "备份账号")
        for a in items:
            st = icon_green() if a.get("status") == "Enabled" else icon_red()
            lines.append(f"  {st} {a.get('type', '?')}  [{a.get('bucket', '?')}]  {a.get('accessKey', '?')}")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # GET / single-object endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_backup_options() -> str:
        """备份账号选项 — 本地/远程存储类型、配置"""
        p = get_client()
        data = p.get("/backups/account/options")
        lines = [header("备份账号选项")]
        if isinstance(data, list):
            for opt in data:
                lines.append(f"  {fmt_val(opt.get('type', opt.get('key', '?')))}  {opt.get('value', opt.get('label', ''))}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_backup_local() -> str:
        """本地备份目录信息"""
        p = get_client()
        data = p.get("/backups/local")
        return fmt_generic(data, "本地备份目录")

    # ------------------------------------------------------------------ #
    # POST endpoints with type parameter
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_backup_buckets(type: str = "LOCAL") -> str:
        """列出存储桶 — 按账号类型"""
        p = get_client()
        data = p.post("/backups/buckets", {"type": type})
        lines = [header(f"存储桶 ({type})")]
        if isinstance(data, list):
            for bucket in data:
                name = bucket.get("name", bucket.get("bucket", "?"))
                lines.append(f"  {fmt_val(name)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_backup_check(type: str = "LOCAL") -> str:
        """检查备份账号连通性"""
        p = get_client()
        data = p.post("/backups/check", {"type": type})
        return fmt_generic(data, f"连通性检查 ({type})")

    @mcp.tool()
    def panel_backup_files(type: str = "LOCAL") -> str:
        """备份目录文件列表"""
        p = get_client()
        data = p.post("/backups/search/files", {"type": type})
        lines = [header(f"备份文件 ({type})")]
        if isinstance(data, list):
            for f in data:
                name = f.get("name", f.get("file", "?"))
                size = f.get("size", "")
                lines.append(f"  {fmt_val(name)}  {fmt_val(size)}")
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
