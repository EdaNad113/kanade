/**
 * mcp-1panel — Resource endpoint definitions
 *
 * Maps panel:// URIs to tool handlers.
 */
import { ALL_TOOLS } from "./tools/index.js";

const RESOURCE_MAP = {
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
};

export function getResources() {
  return Object.entries(RESOURCE_MAP).map(([uri, toolName]) => ({
    uri,
    name: uri,
    description: `1Panel resource: ${uri} — ${ALL_TOOLS[toolName]?.description ?? ""}`,
    mimeType: "text/plain",
  }));
}

export async function readResource(uri) {
  const toolName = RESOURCE_MAP[uri];
  if (!toolName) throw new Error(`Unknown resource: ${uri}`);
  const tool = ALL_TOOLS[toolName];
  if (!tool) throw new Error(`No handler for resource: ${uri}`);
  const text = await tool.handler({});
  return { contents: [{ uri, mimeType: "text/plain", text }] };
}
