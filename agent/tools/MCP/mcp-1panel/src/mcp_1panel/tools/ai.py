"""MCP tools for AI-related 1Panel API endpoints."""

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
    """Register all AI-related MCP tools."""

    # ------------------------------------------------------------------ #
    # Search / paginated endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_mcp_servers() -> str:
        """1Panel 中注册的 MCP Server 列表"""
        p = get_client()
        data = p.post("/ai/mcp/search", {"page": 1, "pageSize": 20})
        lines, items = fmt_search(data, "MCP Servers")
        for m in items:
            st = icon_green() if m.get("status") == "Running" else icon_red()
            lines.append(f"  {st} {m.get('name', '?')}  [{m.get('type', '?')}]  {m.get('host', '?')}")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ai_agents() -> str:
        """AI 智能体列表 — 名称、模型、状态"""
        p = get_client()
        data = p.post("/ai/agents/search", {"page": 1, "pageSize": 20})
        lines, items = fmt_search(data, "AI 智能体")
        for a in items:
            st = icon_green() if a.get("status") == "Running" else icon_red()
            lines.append(f"  {st} {a.get('name', '?')}  [{a.get('model', '?')}]  {a.get('status', '?')}")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ai_providers() -> str:
        """AI 供应商列表 — 名称、模型支持"""
        p = get_client()
        data = p.post("/ai/providers/search", {"page": 1, "pageSize": 20})
        lines, items = fmt_search(data, "AI 供应商")
        for prov in items:
            lines.append(f"  {prov.get('name', '?')}  [{prov.get('models', '?')}]")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ollama() -> str:
        """Ollama 模型列表 — 名称、大小"""
        p = get_client()
        data = p.post("/ai/ollama/model/search", {"page": 1, "pageSize": 20})
        lines, items = fmt_search(data, "Ollama 模型")
        for m in items:
            lines.append(f"  {m.get('name', '?')}  {m.get('size', '?')}")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # GET / single-object endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_gpu_load() -> str:
        """GPU 负载信息 — GPU 型号、显存使用率"""
        p = get_client()
        data = p.get("/ai/gpu")
        return fmt_generic(data, "GPU 负载")

    @mcp.tool()
    def panel_ai_overview() -> str:
        """AI 全局概览 — 智能体总数、运行状态、渠道概览"""
        p = get_client()
        data = p.get("/ai/overview")
        return fmt_generic(data, "AI 全局概览")

    @mcp.tool()
    def panel_ai_agent_roles() -> str:
        """AI 智能体角色列表 — 已配置的角色"""
        p = get_client()
        data = p.get("/ai/agents/roles")
        lines = [header("AI 智能体角色")]
        if isinstance(data, list):
            for role in data:
                name = role.get("name", role.get("role", "?"))
                lines.append(f"  {fmt_val(name)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ai_model_config() -> str:
        """AI 模型配置详情 — 当前模型参数"""
        p = get_client()
        data = p.get("/ai/model/config")
        return fmt_generic(data, "AI 模型配置")

    @mcp.tool()
    def panel_ai_config_file() -> str:
        """AI Agent 配置文件内容"""
        p = get_client()
        data = p.get("/ai/config/file")
        return fmt_generic(data, "AI 配置文件")

    @mcp.tool()
    def panel_ai_security() -> str:
        """AI 安全配置 — 访问控制、权限设置"""
        p = get_client()
        data = p.get("/ai/security")
        return fmt_generic(data, "AI 安全配置")

    @mcp.tool()
    def panel_ai_channels() -> str:
        """AI 渠道配置概览 — 各平台渠道状态"""
        p = get_client()
        data = p.get("/ai/channels")
        lines = [header("AI 渠道配置")]
        if isinstance(data, list):
            for ch in data:
                st = icon_green() if ch.get("status") == "Enabled" else icon_red()
                lines.append(f"  {st} {ch.get('name', '?')}  [{ch.get('type', '?')}]  {ch.get('status', '?')}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ai_skills_list() -> str:
        """AI 技能列表 — 已安装的技能"""
        p = get_client()
        data = p.get("/ai/skills/list")
        lines = [header("AI 技能")]
        if isinstance(data, list):
            for skill in data:
                name = skill.get("name", "?")
                desc = skill.get("description", "")
                lines.append(f"  {name}  {fmt_val(desc)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Search with keyword parameter
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_ai_skills_search(keywords: str) -> str:
        """搜索 AI 技能 — 按关键词查询"""
        p = get_client()
        data = p.post("/ai/skills/search", {
            "page": 1,
            "pageSize": 20,
            "keywords": keywords,
        })
        lines, items = fmt_search(data, f"AI 技能搜索: {keywords}")
        for skill in items:
            name = skill.get("name", "?")
            desc = skill.get("description", "")
            lines.append(f"  {name}  {fmt_val(desc)}")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # More GET / single-object endpoints
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_mcp_domain() -> str:
        """MCP Server 域名绑定信息"""
        p = get_client()
        data = p.get("/ai/mcp/domain")
        return fmt_generic(data, "MCP 域名绑定")

    @mcp.tool()
    def panel_ai_other_config() -> str:
        """AI 其他配置 — 杂项设置"""
        p = get_client()
        data = p.get("/ai/other/config")
        return fmt_generic(data, "AI 其他配置")

    @mcp.tool()
    def panel_ai_agent_md() -> str:
        """AI 智能体 Markdown 文件列表"""
        p = get_client()
        data = p.get("/ai/agents/md")
        lines = [header("AI 智能体 Markdown 文件")]
        if isinstance(data, list):
            for md in data:
                name = md.get("name", md.get("file", "?"))
                lines.append(f"  {fmt_val(name)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ai_agent_channels() -> str:
        """AI 智能体角色渠道配置"""
        p = get_client()
        data = p.get("/ai/agents/channels")
        lines = [header("AI 智能体角色渠道")]
        if isinstance(data, list):
            for ch in data:
                name = ch.get("name", ch.get("role", "?"))
                st = icon_green() if ch.get("status") == "Enabled" else icon_red()
                lines.append(f"  {st} {fmt_val(name)}  [{ch.get('type', '?')}]  {ch.get('status', '?')}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ollama_config() -> str:
        """Ollama 运行配置状态"""
        p = get_client()
        data = p.get("/ai/ollama/config")
        return fmt_generic(data, "Ollama 配置")


    # -- 收集 handler 供 resources 复用 --
    if handlers is not None:
        for _name, _fn in list(locals().items()):
            if _name.startswith("panel_") and callable(_fn):
                handlers[_name] = _fn
