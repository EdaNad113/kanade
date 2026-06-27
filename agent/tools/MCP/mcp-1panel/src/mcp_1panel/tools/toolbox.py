"""MCP tools for 1Panel toolbox — fail2ban, FTP, ClamAV, device, timezones."""

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
    """Register all toolbox MCP tools (fail2ban, FTP, ClamAV, device, timezones)."""

    # ------------------------------------------------------------------ #
    # Fail2ban
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_fail2ban() -> str:
        """Fail2ban 状态 — 启用、SSH 保护"""
        p = get_client()
        data = p.get("/toolbox/fail2ban/base")
        lines = [header("Fail2ban 状态")]
        if isinstance(data, dict):
            enabled = data.get("enable", data.get("enabled", False))
            sshd = data.get("sshdStatus", data.get("sshd_status", ""))
            st = icon_green() if enabled else icon_red()
            lines.append(f"  {st} Fail2ban: {'已启用' if enabled else '已禁用'}")
            if sshd:
                mode_icon = icon_green() if "active" in str(sshd).lower() else icon_red()
                lines.append(f"  {mode_icon} SSHd: {sshd}")
            for k, v in data.items():
                if k not in ("enable", "enabled", "sshdStatus", "sshd_status"):
                    lines.append(f"  {k}: {fmt_val(v)}")
        elif isinstance(data, list):
            lines.extend(fmt_list(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_fail2ban_conf() -> str:
        """Fail2ban 配置详情 — 封禁规则、时间"""
        p = get_client()
        data = p.get("/toolbox/fail2ban/config")
        return fmt_generic(data, "Fail2ban 配置")

    @mcp.tool()
    def panel_fail2ban_list() -> str:
        """Fail2ban 封禁 IP 列表"""
        p = get_client()
        data = p.get("/toolbox/fail2ban/list")
        lines = [header("Fail2ban 封禁 IP")]
        if isinstance(data, list):
            for entry in data:
                ip = entry.get("ip", entry.get("address", "?"))
                ban_type = entry.get("type", entry.get("banType", ""))
                location = entry.get("location", entry.get("country", ""))
                time = entry.get("time", entry.get("bannedAt", ""))
                detail = f"  🔒 {ip}"
                if ban_type:
                    detail += f"  [{ban_type}]"
                if location:
                    detail += f"  🌍 {location}"
                if time:
                    detail += f"  (封禁时间: {time})"
                lines.append(detail)
        elif isinstance(data, dict):
            # Might be paginated: {"items": [...], "total": N}
            sub, items = fmt_search(data, "")
            for entry in items:
                ip = entry.get("ip", entry.get("address", "?"))
                ban_type = entry.get("type", entry.get("banType", ""))
                location = entry.get("location", entry.get("country", ""))
                time = entry.get("time", entry.get("bannedAt", ""))
                detail = f"  🔒 {ip}"
                if ban_type:
                    detail += f"  [{ban_type}]"
                if location:
                    detail += f"  🌍 {location}"
                if time:
                    detail += f"  (封禁时间: {time})"
                lines.append(detail)
            if not items:
                lines.append("  (空)")
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # FTP
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_ftp() -> str:
        """FTP 账号列表 — 用户名、状态"""
        p = get_client()
        data = p.post("/toolbox/ftp/search", {"page": 1, "pageSize": 20})
        lines, items = fmt_search(data, "FTP 账号")
        for acct in items:
            user = acct.get("user", acct.get("username", "?"))
            status = acct.get("status", acct.get("enable", True))
            path = acct.get("path", acct.get("dir", ""))
            st = icon_green() if status else icon_red()
            detail = f"  {st} {fmt_val(user)}"
            if path:
                detail += f"  📁 {fmt_val(path)}"
            lines.append(detail)
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ftp_base() -> str:
        """FTP 基础配置 — 状态、端口"""
        p = get_client()
        data = p.get("/toolbox/ftp/base")
        lines = [header("FTP 基础配置")]
        if isinstance(data, dict):
            enabled = data.get("enable", data.get("enabled", False))
            port = data.get("port", data.get("listenPort", ""))
            st = icon_green() if enabled else icon_red()
            lines.append(f"  {st} FTP: {'已启用' if enabled else '已禁用'}")
            if port:
                lines.append(f"  端口: {port}")
            for k, v in data.items():
                if k not in ("enable", "enabled", "port", "listenPort"):
                    lines.append(f"  {k}: {fmt_val(v)}")
        elif isinstance(data, list):
            lines.extend(fmt_list(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ftp_logs() -> str:
        """FTP 操作日志"""
        p = get_client()
        data = p.post("/toolbox/ftp/log/search", {"page": 1, "pageSize": 20})
        lines, items = fmt_search(data, "FTP 日志")
        for log in items:
            time = log.get("time", log.get("createdAt", "?"))
            user = log.get("user", log.get("username", "?"))
            operation = log.get("operation", log.get("action", "?"))
            ip = log.get("ip", log.get("address", ""))
            detail = f"  {time}  {fmt_val(user)}  [{operation}]"
            if ip:
                detail += f"  {ip}"
            lines.append(detail)
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # ClamAV
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_clamav() -> str:
        """ClamAV 杀毒状态 — 版本、活跃状态"""
        p = get_client()
        data = p.post("/toolbox/clam/base", {})
        lines = [header("ClamAV 状态")]
        if isinstance(data, dict):
            enabled = data.get("enable", data.get("enabled", False))
            version = data.get("version", data.get("virusVersion", ""))
            running = data.get("status", data.get("running", enabled))
            st = icon_green() if running else icon_red()
            lines.append(f"  {st} ClamAV: {'运行中' if running else '已停止'}")
            if version:
                lines.append(f"  版本: {version}")
            if isinstance(enabled, bool):
                lines.append(f"  启用: {'是' if enabled else '否'}")
            for k, v in data.items():
                if k not in ("enable", "enabled", "version", "virusVersion", "status", "running"):
                    lines.append(f"  {k}: {fmt_val(v)}")
        elif isinstance(data, list):
            lines.extend(fmt_list(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_clamav_records() -> str:
        """ClamAV 查杀记录"""
        p = get_client()
        data = p.get("/toolbox/clam/records")
        lines = [header("ClamAV 查杀记录")]
        if isinstance(data, list):
            for rec in data:
                time = rec.get("time", rec.get("createdAt", "?"))
                path = rec.get("path", rec.get("file", "?"))
                result = rec.get("result", rec.get("status", "?"))
                virus = rec.get("virus", rec.get("virusName", ""))
                st = icon_red() if result.lower() in ("infected", "found", "病毒") else icon_green()
                detail = f"  {st} {time}  {fmt_val(path)}  [{result}]"
                if virus:
                    detail += f"  🦠 {virus}"
                lines.append(detail)
        elif isinstance(data, dict):
            sub, items = fmt_search(data, "")
            for rec in items:
                time = rec.get("time", rec.get("createdAt", "?"))
                path = rec.get("path", rec.get("file", "?"))
                result = rec.get("result", rec.get("status", "?"))
                virus = rec.get("virus", rec.get("virusName", ""))
                st = icon_red() if result.lower() in ("infected", "found", "病毒") else icon_green()
                detail = f"  {st} {time}  {fmt_val(path)}  [{result}]"
                if virus:
                    detail += f"  🦠 {virus}"
                lines.append(detail)
            if not items:
                lines.append("  (空)")
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_clamav_files() -> str:
        """ClamAV 扫描文件配置"""
        p = get_client()
        data = p.get("/toolbox/clam/files")
        lines = [header("ClamAV 扫描文件")]
        if isinstance(data, list):
            for entry in data:
                path = entry.get("path", entry.get("file", "?"))
                typ = entry.get("type", entry.get("scanType", ""))
                detail = f"  📄 {fmt_val(path)}"
                if typ:
                    detail += f"  [{typ}]"
                lines.append(detail)
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Device
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_device_base() -> str:
        """设备基础信息 — 主机名、系统信息"""
        p = get_client()
        data = p.get("/toolbox/device/base")
        return fmt_generic(data, "设备基础信息")

    @mcp.tool()
    def panel_device_dns() -> str:
        """设备 DNS 配置检查"""
        p = get_client()
        data = p.get("/toolbox/device/dns")
        return fmt_generic(data, "DNS 配置")

    # ------------------------------------------------------------------ #
    # Timezones
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_timezones() -> str:
        """时区选项列表"""
        p = get_client()
        data = p.get("/toolbox/timezones")
        lines = [header("时区列表")]
        if isinstance(data, list):
            for tz in data:
                name = tz.get("name", tz.get("zone", tz.get("value", "")))
                if not name:
                    name = str(tz)
                lines.append(f"  🕐 {name}")
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
