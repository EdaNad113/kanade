"""mcp-1panel: 199 MCP tools + 18 resources for 1Panel (18 API modules).

Usage:
    export PANEL_HOST=http://your-panel:port
    export PANEL_API_KEY=***
    mcp-1panel
"""
import os

from mcp.server.fastmcp import FastMCP

from mcp_1panel.panel_client import PanelClient


# ---------------------------------------------------------------------------
# 注册期间收集所有工具 handler 用于 resources 复用
# ---------------------------------------------------------------------------
_tool_handlers: dict = {}


def _store_handler(fn):
    """Store a tool function in the global handler registry by its __name__."""
    _tool_handlers[fn.__name__] = fn
    return fn


# ---------------------------------------------------------------------------
# 工具注册
# ---------------------------------------------------------------------------
def _register_tools(mcp):
    """Register all tool modules and resources."""

    # -- 工具注册（传入 handlers dict 用于后续 resources 复用） --

    from mcp_1panel.tools.ai import register_tools as r_ai
    from mcp_1panel.tools.apps import register_tools as r_apps
    from mcp_1panel.tools.backups import register_tools as r_backups
    from mcp_1panel.tools.containers import register_tools as r_containers
    from mcp_1panel.tools.core import register_tools as r_core
    from mcp_1panel.tools.cronjobs import register_tools as r_cronjobs
    from mcp_1panel.tools.dashboard import register_tools as r_dashboard
    from mcp_1panel.tools.databases import register_tools as r_databases
    from mcp_1panel.tools.files import register_tools as r_files
    from mcp_1panel.tools.groups_logs import register_tools as r_groups_logs
    from mcp_1panel.tools.hosts import register_tools as r_hosts
    from mcp_1panel.tools.openresty_process import register_tools as r_openresty
    from mcp_1panel.tools.runtimes import register_tools as r_runtimes
    from mcp_1panel.tools.settings import register_tools as r_settings
    from mcp_1panel.tools.toolbox import register_tools as r_toolbox
    from mcp_1panel.tools.websites import register_tools as r_websites

    # get_client 闭包：延迟求值，允许测试时替换
    def _get_client():
        return PanelClient(
            host=os.getenv("PANEL_HOST", ""),
            api_key=os.getenv("PANEL_API_KEY", ""),
        )

    r_ai(mcp, _get_client, _tool_handlers)
    r_apps(mcp, _get_client, _tool_handlers)
    r_backups(mcp, _get_client, _tool_handlers)
    r_containers(mcp, _get_client, _tool_handlers)
    r_core(mcp, _get_client, _tool_handlers)
    r_cronjobs(mcp, _get_client, _tool_handlers)
    r_dashboard(mcp, _get_client, _tool_handlers)
    r_databases(mcp, _get_client, _tool_handlers)
    r_files(mcp, _get_client, _tool_handlers)
    r_groups_logs(mcp, _get_client, _tool_handlers)
    r_hosts(mcp, _get_client, _tool_handlers)
    r_openresty(mcp, _get_client, _tool_handlers)
    r_runtimes(mcp, _get_client, _tool_handlers)
    r_settings(mcp, _get_client, _tool_handlers)
    r_toolbox(mcp, _get_client, _tool_handlers)
    r_websites(mcp, _get_client, _tool_handlers)

    # -- Resources（复用工具 handler） --

    from mcp_1panel.resources import register_resources

    register_resources(mcp, _tool_handlers)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def main():
    mcp = FastMCP("1Panel Manager", log_level="INFO")
    _register_tools(mcp)
    mcp.run()


if __name__ == "__main__":
    main()
