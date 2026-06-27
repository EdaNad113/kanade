"""MCP tools for Docker container management via 1Panel API."""

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
    """Register all Docker-container-related MCP tools."""

    # ------------------------------------------------------------------ #
    # List / paginated endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_containers() -> str:
        """Docker 容器列表 — 名称、镜像、状态"""
        p = get_client()
        data = p.post("/containers/list", {})
        lines = [header("Docker 容器", len(data) if isinstance(data, list) else None)]
        for c in data or []:
            running = c.get("state") == "running"
            st = icon_status(running)
            lines.append(f"  {st} {c.get('name', '?')}  {c.get('image', '?')}  [{c.get('state', '?')}]")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_images() -> str:
        """Docker 镜像列表 — 仓库标签、大小"""
        p = get_client()
        data = p.get("/containers/image/all")
        lines = [header("Docker 镜像", len(data) if isinstance(data, list) else None)]
        for img in data or []:
            lines.append(f"  {img.get('repoTag', '?')}  {img.get('size', '?')}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_compose() -> str:
        """Docker Compose 项目列表"""
        p = get_client()
        data = p.post("/containers/compose/search", {"page": 1, "pageSize": 20})
        lines, items = fmt_search(data, "Compose 项目")
        for c in items:
            st = icon_status(c.get("status") == "Running") if c.get("status") else ""
            lines.append(f"  {st} {c.get('name', '?')}  [{c.get('status', '?')}]")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_networks() -> str:
        """Docker 网络列表"""
        p = get_client()
        data = p.get("/containers/network")
        lines = [header("Docker 网络", len(data) if isinstance(data, list) else None)]
        for net in data or []:
            name = net.get("name", net.get("Name", "?"))
            driver = net.get("driver", net.get("Driver", "?"))
            scope = net.get("scope", net.get("Scope", "?"))
            subnet = net.get("subnet", net.get("Subnet", ""))
            lines.append(f"  {name}  [{driver}]  {subnet}  ({scope})")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_volumes() -> str:
        """Docker 存储卷列表 — 名称、驱动、挂载点"""
        p = get_client()
        data = p.get("/containers/volume")
        lines = [header("Docker 存储卷", len(data) if isinstance(data, list) else None)]
        for vol in data or []:
            name = vol.get("name", vol.get("Name", "?"))
            driver = vol.get("driver", vol.get("Driver", "?"))
            mount = vol.get("mountpoint", vol.get("Mountpoint", "?"))
            lines.append(f"  {name}  [{driver}]  {mount}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_image_repos() -> str:
        """Docker 镜像仓库列表"""
        p = get_client()
        data = p.get("/containers/repo")
        lines = [header("镜像仓库", len(data) if isinstance(data, list) else None)]
        for repo in data or []:
            protocol = repo.get("protocol", "?")
            host = repo.get("host", repo.get("hostname", "?"))
            port = repo.get("port", "")
            auth = icon_lock() if repo.get("auth") else icon_unlock()
            lines.append(f"  {auth} {protocol}://{host}:{port}  [{repo.get('status', '?')}]")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_docker_status() -> str:
        """Docker 守护进程状态 — 运行状态、版本"""
        p = get_client()
        data = p.get("/containers/daemon/status")
        lines = [header("Docker 守护进程状态")]
        if isinstance(data, dict):
            running = data.get("status", data.get("State", "")) == "running"
            st = icon_status(running)
            lines.append(f"  {st} 状态: {data.get('status', data.get('State', '?'))}")
            for k, v in data.items():
                if k not in ("status", "State"):
                    lines.append(f"  {k}: {fmt_val(v)}")
        elif isinstance(data, str):
            lines.append(f"  {fmt_val(data)}")
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_compose_templates() -> str:
        """Docker Compose 模板列表"""
        p = get_client()
        data = p.get("/containers/compose/template")
        lines = [header("Compose 模板", len(data) if isinstance(data, list) else None)]
        for tpl in data or []:
            name = tpl.get("name", tpl.get("title", "?"))
            desc = tpl.get("description", "")
            if desc and len(str(desc)) > 60:
                desc = str(desc)[:60] + "..."
            lines.append(f"  {name}")
            if desc:
                lines.append(f"    {desc}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_processes() -> str:
        """容器进程状态（来自 Docker stats）"""
        p = get_client()
        data = p.post("/containers/stats/list", {})
        lines = [header("容器进程 / Stats")]
        for proc in (data or [])[:30]:
            name = proc.get("name", proc.get("Name", "?"))
            cpu = proc.get("cpuPercent", proc.get("cpu", "?"))
            mem = proc.get("memoryPercent", proc.get("memory", "?"))
            mem_used = proc.get("memoryUsed", proc.get("memUsage", ""))
            lines.append(f"  {name}  CPU: {cpu}%  MEM: {mem}%  ({mem_used})")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # GET / single-config endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_docker_daemon() -> str:
        """Docker 守护进程配置 (daemon.json)"""
        p = get_client()
        data = p.get("/containers/daemon")
        return fmt_generic(data, "Docker 守护进程配置")

    @mcp.tool()
    def panel_docker_daemon_file() -> str:
        """Docker daemon.json 文件内容"""
        p = get_client()
        data = p.get("/containers/daemon/file")
        return fmt_generic(data, "daemon.json")

    @mcp.tool()
    def panel_container_limits() -> str:
        """Docker 容器资源限制配置"""
        p = get_client()
        data = p.get("/containers/limits")
        return fmt_generic(data, "容器资源限制")

    @mcp.tool()
    def panel_container_status() -> str:
        """Docker 容器状态概览 — 运行/停止计数"""
        p = get_client()
        data = p.get("/containers/status")
        if isinstance(data, dict):
            running = data.get("running", data.get("Running", 0))
            stopped = data.get("stopped", data.get("Stopped", 0))
            total = data.get("total", data.get("Total", 0))
            lines = [header("容器状态概览")]
            lines.append(f"  {icon_status(True)} 运行中: {running}")
            lines.append(f"  {icon_status(False)} 已停止: {stopped}")
            if total:
                lines.append(f"  总计: {total}")
            for k, v in data.items():
                if k.lower() not in ("running", "stopped", "total"):
                    lines.append(f"  {k}: {fmt_val(v)}")
            return "\n".join(lines)
        return fmt_generic(data, "容器状态概览")

    @mcp.tool()
    def panel_container_logs() -> str:
        """Docker 容器日志概览"""
        p = get_client()
        data = p.get("/containers/logs")
        return fmt_generic(data, "容器日志")

    @mcp.tool()
    def panel_container_users() -> str:
        """容器用户列表 — UID/GID 映射"""
        p = get_client()
        data = p.get("/containers/users")
        return fmt_generic(data, "容器用户")

    @mcp.tool()
    def panel_image_options() -> str:
        """Docker 镜像仓库选项 — 支持的加速器"""
        p = get_client()
        data = p.get("/containers/image/options")
        return fmt_generic(data, "镜像仓库选项")

    # ------------------------------------------------------------------ #
    # GET / single-object endpoints (with query params)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_container_inspect(id: str) -> str:
        """容器 Inspect 信息 — 完整的 JSON 配置"""
        p = get_client()
        data = p.get("/containers/inspect", {"id": id})
        return fmt_generic(data, f"容器 Inspect: {id}")

    @mcp.tool()
    def panel_container_stats(id: str) -> str:
        """容器资源统计 — CPU/内存/网络"""
        p = get_client()
        data = p.get("/containers/stats", {"id": id})
        lines = [header(f"容器 Stats: {id}")]
        if isinstance(data, dict):
            for k, v in data.items():
                lines.append(f"  {k}: {fmt_val(v)}")
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # POST / single-object endpoints (by id / name / image)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_container_info(id: str, name: str) -> str:
        """容器详情 — 名称、配置、挂载"""
        p = get_client()
        data = p.post("/containers/info", {"id": id, "name": name})
        return fmt_generic(data, f"容器详情: {name}")

    @mcp.tool()
    def panel_containers_by_image(image: str) -> str:
        """按镜像查找容器"""
        p = get_client()
        data = p.post("/containers/listbyimage", {"image": image})
        lines = [header(f"镜像: {image} 的容器", len(data) if isinstance(data, list) else None)]
        for c in data or []:
            running = c.get("state") == "running"
            st = icon_status(running)
            lines.append(f"  {st} {c.get('name', '?')}  [{c.get('state', '?')}]")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_compose_env(id: int) -> str:
        """Compose 项目环境变量"""
        p = get_client()
        data = p.post("/containers/compose/env", {"id": id})
        return fmt_generic(data, f"Compose 环境变量 (ID: {id})")

    @mcp.tool()
    def panel_repo_status(id: int) -> str:
        """镜像仓库连通性检查"""
        p = get_client()
        data = p.post("/containers/repo/status", {"id": id})
        lines = [header(f"镜像仓库连通性 (ID: {id})")]
        if isinstance(data, dict):
            ok = data.get("status", data.get("message", "")) == "ok"
            st = icon_status(ok)
            lines.append(f"  {st} {fmt_val(data)}")
        else:
            lines.append(f"  {fmt_val(data)}")
        return "\n".join(lines)


    # -- 收集 handler 供 resources 复用 --
    if handlers is not None:
        for _name, _fn in list(locals().items()):
            if _name.startswith("panel_") and callable(_fn):
                handlers[_name] = _fn
