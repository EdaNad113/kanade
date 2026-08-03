"""MCP Resources for 1Panel — mapping panel:// URIs to tool handlers.

Mirrors the Node.js resources.js pattern: each URI maps to an existing tool name.
Resources reuse tool handlers directly, avoiding duplication.
"""

# Mapping: panel:// URI → tool function name
# Resources reuse the tool handlers registered in mcp_server.py
RESOURCE_TO_TOOL = {
    "panel://overview": "panel_overview",
    "panel://websites": "panel_websites",
    "panel://containers": "panel_containers",
    "panel://databases": "panel_databases",
    "panel://disks": "panel_disks",
    "panel://mcp": "panel_mcp_servers",
    "panel://monitor": "panel_monitor",
    "panel://settings": "panel_settings",
    "panel://docker-status": "panel_docker_status",
    "panel://firewall": "panel_firewall",
    "panel://ssh": "panel_ssh",
    "panel://cronjobs": "panel_cronjobs",
    "panel://backups": "panel_backups",
    "panel://logs": "panel_logs",
    "panel://fail2ban": "panel_fail2ban",
    "panel://gpu": "panel_gpu_load",
    "panel://ai-agents": "panel_ai_agents",
    "panel://ollama": "panel_ollama",
}


def register_resources(mcp, handler_registry):
    """Register all resource endpoints using tool handlers from the registry.

    Args:
        mcp: FastMCP instance
        handler_registry: dict mapping tool name → callable, populated during tool registration.
    """
    for uri, tool_name in RESOURCE_TO_TOOL.items():
        # Get a human-readable description from the handler's docstring
        fn = handler_registry.get(tool_name)
        description = (fn.__doc__ or tool_name).strip() if fn else tool_name

        # Note: we capture tool_name and uri by value in the closure
        _register_resource(mcp, uri, description, handler_registry, tool_name)


def _register_resource(mcp, uri, description, handler_registry, tool_name):
    """Register a single resource endpoint that delegates to a tool handler."""

    @mcp.resource(uri)
    def resource_handler() -> str:
        fn = handler_registry.get(tool_name)
        if fn is None:
            return f"ERR: handler '{tool_name}' not found"
        try:
            result = fn()
            return str(result) if result is not None else "(空)"
        except Exception as e:
            return f"ERR: {e}"

    resource_handler.__doc__ = description
    resource_handler.__name__ = f"r_{tool_name}"


def get_resource_list():
    """Return list of (uri, tool_name) pairs for startup logging."""
    return list(RESOURCE_TO_TOOL.items())
