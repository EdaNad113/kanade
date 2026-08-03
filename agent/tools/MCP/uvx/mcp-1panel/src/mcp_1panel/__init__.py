"""mcp-1panel: MCP Server for 1Panel"""

from mcp_1panel.panel_client import PanelClient
from mcp_1panel.mcp_server import main

__version__ = "0.2.0"
__all__ = ["PanelClient", "main"]
