"""MCP tools for 1Panel settings & snapshot endpoints."""

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
    """Register all settings & snapshot MCP tools."""

    # ------------------------------------------------------------------ #
    # Settings
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_setting_by_key(key: str = "PanelName") -> str:
        """按 Key 查询系统设置"""
        p = get_client()
        data = p.post("/core/settings/by", {"key": key})
        lines = [header(f"系统设置: {key}")]
        if isinstance(data, dict):
            # Format as key: value
            val = data.get("value", data.get(key, ""))
            lines.append(f"  {key}: {fmt_val(val)}")
        elif isinstance(data, list):
            lines.extend(fmt_list(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ssh_conn() -> str:
        """本地 SSH 连接配置"""
        p = get_client()
        data = p.get("/core/ssh/conn")
        return fmt_generic(data, "SSH 连接配置")

    @mcp.tool()
    def panel_ssh_check() -> str:
        """本地连接信息检查"""
        p = get_client()
        data = p.get("/core/ssh/check")
        return fmt_generic(data, "SSH 连接检查")

    @mcp.tool()
    def panel_backup_dir() -> str:
        """本地备份目录路径"""
        p = get_client()
        data = p.get("/core/backup/dir")
        return fmt_generic(data, "备份目录")

    @mcp.tool()
    def panel_system_available() -> str:
        """系统可用状态 — 各模块健康检查"""
        p = get_client()
        data = p.get("/core/system/available")
        lines = [header("系统可用状态")]
        if isinstance(data, dict):
            for service, status in data.items():
                ok = status in (True, "true", "ok", "running", "正常")
                icon = icon_green() if ok else icon_red()
                lines.append(f"  {icon} {service}: {fmt_val(status)}")
        elif isinstance(data, list):
            lines.extend(fmt_list(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Snapshots
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_snapshot_list() -> str:
        """系统快照列表 — 可用的回滚点"""
        p = get_client()
        data = p.get("/core/snapshots")
        lines = [header("系统快照列表")]
        if isinstance(data, list):
            for snap in data:
                snap_id = snap.get("id", "?")
                name = snap.get("name", snap.get("description", "?"))
                created = snap.get("createdAt", snap.get("time", ""))
                size = snap.get("size", "")
                lines.append(f"  ID {snap_id}: {fmt_val(name)}")
                if created:
                    lines.append(f"    创建时间: {fmt_val(created)}")
                if size:
                    lines.append(f"    大小: {fmt_val(size)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_snapshot_info() -> str:
        """系统快照信息 — 状态、时间"""
        p = get_client()
        data = p.get("/core/snapshot/info")
        return fmt_generic(data, "快照信息")

    @mcp.tool()
    def panel_snapshot_recover(id: int) -> str:
        """快照恢复信息查询"""
        p = get_client()
        data = p.get(f"/core/snapshot/recover?id={id}")
        return fmt_generic(data, f"快照恢复 (ID: {id})")

    # -- 收集 handler 供 resources 复用 --
    if handlers is not None:
        for _name, _fn in list(locals().items()):
            if _name.startswith("panel_") and callable(_fn):
                handlers[_name] = _fn
