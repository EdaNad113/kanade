"""MCP tools for 1Panel hosts management — disks, firewall, SSH, monitor, supervisor."""

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


def _progress_bar(used: float, total: float, width: int = 20) -> str:
    """Render a text progress bar with █ and ░ characters."""
    if total <= 0:
        return "░" * width
    pct = used / total
    filled = int(pct * width)
    if filled > width:
        filled = width
    bar = "█" * filled + "░" * (width - filled)
    return bar


def register_tools(mcp, get_client, handlers=None):
    """Register all hosts-management MCP tools."""

    # ------------------------------------------------------------------ #
    # Disks
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_disks() -> str:
        """磁盘分区详情 — 路径、用量（含进度条）"""
        p = get_client()
        data = p.get("/hosts/disks")
        lines = [header("磁盘分区")]
        if isinstance(data, list):
            for disk in data:
                path = disk.get("path", disk.get("mount", "?"))
                total = disk.get("total", disk.get("size", 0))
                used = disk.get("used", 0)
                free = disk.get("free", total - used if total else 0)
                pct = disk.get("percent", disk.get("usage", 0))
                if isinstance(pct, str) and "%" in pct:
                    pct = pct.replace("%", "")
                try:
                    pct_val = float(pct)
                except (TypeError, ValueError):
                    pct_val = round((used / total) * 100, 1) if total else 0.0
                bar = _progress_bar(used, total)
                lines.append(f"  {path}")
                lines.append(f"    [{bar}] {pct_val:.1f}%")
                lines.append(f"    总: {fmt_val(total)}  |  已用: {fmt_val(used)}  |  剩余: {fmt_val(free)}")
        elif isinstance(data, dict):
            path = data.get("path", data.get("mount", "?"))
            total = data.get("total", data.get("size", 0))
            used = data.get("used", 0)
            free = data.get("free", total - used if total else 0)
            pct = data.get("percent", data.get("usage", 0))
            if isinstance(pct, str) and "%" in pct:
                pct = pct.replace("%", "")
            try:
                pct_val = float(pct)
            except (TypeError, ValueError):
                pct_val = round((used / total) * 100, 1) if total else 0.0
            bar = _progress_bar(used, total)
            lines.append(f"  {path}")
            lines.append(f"    [{bar}] {pct_val:.1f}%")
            lines.append(f"    总: {fmt_val(total)}  |  已用: {fmt_val(used)}  |  剩余: {fmt_val(free)}")
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Firewall
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_firewall() -> str:
        """防火墙规则 — 协议、端口、策略"""
        p = get_client()
        data = p.post("/hosts/firewall/search", {
            "page": 1, "pageSize": 50, "type": "port",
        })
        lines, items = fmt_search(data, "防火墙规则")
        for rule in items:
            protocol = rule.get("protocol", rule.get("proto", "?"))
            port = rule.get("port", rule.get("ports", "?"))
            strategy = rule.get("strategy", rule.get("action", "?"))
            addr = rule.get("address", rule.get("source", ""))
            st = icon_green() if strategy == "accept" else icon_red()
            detail = f"  {st} {protocol}/{port}  [{strategy}]"
            if addr:
                detail += f"  {addr}"
            lines.append(detail)
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_firewall_base() -> str:
        """防火墙基础配置 — 默认策略、状态"""
        p = get_client()
        data = p.get("/hosts/firewall/base")
        return fmt_generic(data, "防火墙基础配置")

    @mcp.tool()
    def panel_firewall_filter() -> str:
        """防火墙过滤规则 — iptables 规则列表"""
        p = get_client()
        data = p.get("/hosts/firewall/filter")
        lines = [header("防火墙过滤规则")]
        if isinstance(data, list):
            for rule in data:
                chain = rule.get("chain", rule.get("table", "?"))
                target = rule.get("target", rule.get("action", "?"))
                proto = rule.get("protocol", rule.get("proto", ""))
                dport = rule.get("dport", rule.get("port", ""))
                source = rule.get("source", rule.get("src", ""))
                detail = f"  {chain} -> {target}"
                if proto:
                    detail += f"  {proto}"
                if dport:
                    detail += f"  dport={dport}"
                if source:
                    detail += f"  from={source}"
                lines.append(detail)
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_firewall_forward() -> str:
        """防火墙端口转发规则"""
        p = get_client()
        data = p.get("/hosts/firewall/forward")
        lines = [header("防火墙端口转发")]
        if isinstance(data, list):
            for fwd in data:
                proto = fwd.get("protocol", fwd.get("proto", "?"))
                src = fwd.get("source", fwd.get("srcPort", "?"))
                dest = fwd.get("dest", fwd.get("destPort", "?"))
                target = fwd.get("target", fwd.get("destIp", ""))
                enable = fwd.get("enable", fwd.get("enabled", True))
                st = icon_green() if enable else icon_red()
                detail = f"  {st} {proto}  {src} -> {dest}"
                if target:
                    detail += f"  (目标: {target})"
                lines.append(detail)
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_firewall_ip() -> str:
        """防火墙 IP 黑/白名单"""
        p = get_client()
        data = p.get("/hosts/firewall/ip")
        lines = [header("防火墙 IP 名单")]
        if isinstance(data, list):
            for entry in data:
                addr = entry.get("address", entry.get("ip", "?"))
                typ = entry.get("type", entry.get("list", "black"))
                enable = entry.get("enable", entry.get("enabled", True))
                st = icon_green() if enable else icon_red()
                icon = icon_red() if typ == "black" else icon_green()
                lines.append(f"  {st} {icon} {addr}  [{typ}]")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # SSH
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_ssh() -> str:
        """SSH 配置列表 — 名称、地址、端口"""
        p = get_client()
        data = p.post("/hosts/ssh/search", {
            "page": 1, "pageSize": 20,
        })
        lines, items = fmt_search(data, "SSH 配置")
        for s in items:
            name = s.get("name", s.get("title", "?"))
            addr = s.get("address", s.get("host", ""))
            port = s.get("port", "")
            user = s.get("user", s.get("username", ""))
            status = s.get("status", s.get("connected", False))
            st = icon_green() if status else icon_red()
            detail = f"  {st} {fmt_val(name)}"
            if addr:
                detail += f"  {addr}"
            if port:
                detail += f":{port}"
            if user:
                detail += f"  [{user}]"
            lines.append(detail)
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ssh_certs() -> str:
        """SSH 证书列表 — 密钥对"""
        p = get_client()
        data = p.get("/hosts/ssh/certs")
        lines = [header("SSH 证书")]
        if isinstance(data, list):
            for cert in data:
                name = cert.get("name", cert.get("key", "?"))
                typ = cert.get("type", cert.get("algorithm", ""))
                fingerprint = cert.get("fingerprint", cert.get("fp", ""))
                detail = f"  {fmt_val(name)}"
                if typ:
                    detail += f"  [{typ}]"
                if fingerprint:
                    detail += f"  {fingerprint}"
                lines.append(detail)
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ssh_conf(id: int) -> str:
        """SSH 配置文件内容"""
        p = get_client()
        data = p.get("/hosts/ssh/conf", {"id": id})
        return fmt_generic(data, f"SSH 配置 (ID: {id})")

    @mcp.tool()
    def panel_ssh_logs(rows: int = 20) -> str:
        """SSH 登录日志"""
        p = get_client()
        data = p.post("/hosts/ssh/log/search", {
            "page": 1, "pageSize": rows,
        })
        lines, items = fmt_search(data, "SSH 登录日志")
        for log in items[:rows]:
            time = log.get("time", log.get("createdAt", "?"))
            user = log.get("user", log.get("username", "?"))
            addr = log.get("address", log.get("ip", "?"))
            auth = log.get("auth", log.get("authMethod", ""))
            result = log.get("result", log.get("status", ""))
            st = icon_green() if result in ("success", "Success", "accepted") else icon_red()
            detail = f"  {st} {time}  {user}@{addr}"
            if auth:
                detail += f"  [{auth}]"
            lines.append(detail)
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Monitor
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_monitor_history(type: str = "cpu", rows: int = 20) -> str:
        """历史监控数据查询"""
        p = get_client()
        data = p.post("/hosts/monitor/history", {
            "type": type, "count": rows,
        })
        lines = [header(f"监控历史: {type}")]
        if isinstance(data, list):
            for rec in data[:rows]:
                time = rec.get("time", rec.get("createdAt", "?"))
                val = rec.get("value", rec.get(type, "?"))
                lines.append(f"  {time}  {val}")
        elif isinstance(data, dict):
            lines, items = fmt_search(data, f"监控历史: {type}")
            for rec in items[:rows]:
                time = rec.get("time", rec.get("createdAt", "?"))
                val = rec.get("value", rec.get(type, "?"))
                lines.append(f"  {time}  {val}")
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_monitor_setting() -> str:
        """监控设置 — 采集间隔、保留天数"""
        p = get_client()
        data = p.get("/hosts/monitor/setting")
        return fmt_generic(data, "监控设置")

    # ------------------------------------------------------------------ #
    # System components & tools
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_system_component(name: str = "docker") -> str:
        """检查系统组件是否存在"""
        p = get_client()
        data = p.get("/hosts/component/check", {"name": name})
        lines = [header(f"系统组件: {name}")]
        if isinstance(data, dict):
            exists = data.get("exists", data.get("isExist", data.get("status", False)))
            version = data.get("version", data.get("versionInfo", ""))
            if isinstance(exists, bool):
                lines.append(f"  {'✓ 存在' if exists else '✗ 不存在'}")
            else:
                lines.append(f"  状态: {exists}")
            if version:
                lines.append(f"  版本: {version}")
            for k, v in data.items():
                if k not in ("exists", "isExist", "version", "versionInfo"):
                    lines.append(f"  {k}: {fmt_val(v)}")
        elif isinstance(data, list):
            lines.extend(fmt_list(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_tool_status(name: str = "supervisor") -> str:
        """系统工具状态查询"""
        p = get_client()
        data = p.get("/hosts/tools/status", {"name": name})
        return fmt_generic(data, f"工具状态: {name}")

    @mcp.tool()
    def panel_tool_config(name: str = "supervisor") -> str:
        """系统工具配置"""
        p = get_client()
        data = p.get("/hosts/tools/config", {"name": name})
        return fmt_generic(data, f"工具配置: {name}")

    # ------------------------------------------------------------------ #
    # Supervisor
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_supervisor_processes() -> str:
        """Supervisor 进程列表"""
        p = get_client()
        data = p.get("/hosts/supervisor/processes")
        lines = [header("Supervisor 进程")]
        if isinstance(data, list):
            for proc in data:
                name = proc.get("name", proc.get("process", "?"))
                st = proc.get("status", proc.get("state", "?"))
                uptime = proc.get("uptime", proc.get("time", ""))
                pid = proc.get("pid", "")
                running = st.lower() in ("running", "up", "started") if isinstance(st, str) else bool(st)
                icon = icon_green() if running else icon_red()
                detail = f"  {icon} {fmt_val(name)}  [{st}]"
                if pid:
                    detail += f"  PID {pid}"
                if uptime:
                    detail += f"  (运行: {uptime})"
                lines.append(detail)
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # GPU
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_gpu_monitor() -> str:
        """GPU 监控历史数据"""
        p = get_client()
        data = p.get("/hosts/gpu/monitor")
        lines = [header("GPU 监控")]
        if isinstance(data, list):
            for entry in data:
                gpu_name = entry.get("name", entry.get("gpu", entry.get("model", "?")))
                usage = entry.get("usage", entry.get("utilization", ""))
                mem_used = entry.get("memoryUsed", entry.get("memUsed", ""))
                mem_total = entry.get("memoryTotal", entry.get("memTotal", ""))
                temp = entry.get("temperature", entry.get("temp", ""))
                detail = f"  {fmt_val(gpu_name)}"
                if usage:
                    detail += f"  使用率: {usage}"
                if mem_used and mem_total:
                    detail += f"  显存: {mem_used}/{mem_total}"
                elif mem_used:
                    detail += f"  显存: {mem_used}"
                if temp:
                    detail += f"  温度: {temp}"
                lines.append(detail)
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
