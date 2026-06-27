/**
 * mcp-1panel — AI 模块工具（18 个）
 */
import { tool, toolWithParams, fmtObj, fmtList, fmtSearch, fmtBool } from "./helpers.js";
import { api } from "../api-proxy.js";

export const AI_TOOLS = {

  // ── 已有工具 ──────────────────────────────────────────────

  panel_mcp_servers: tool("1Panel 中注册的 MCP Server 列表", async () => {
    const d = await api.post("/ai/mcp/search", { page: 1, pageSize: 50 });
    return fmtSearch("MCP Server", d, (m) => `${statusIcon(m.status)} ${m.name ?? "?"}  [${m.type ?? "?"}]  ${m.host ?? "?"}`);
  }),

  panel_ai_agents: tool("AI 智能体列表 — 名称、模型、状态", async () => {
    const d = await api.post("/ai/agents/search", { page: 1, pageSize: 50 });
    return fmtSearch("AI 智能体", d, (a) => `${a.name ?? "?"}  [${a.model ?? "?"}]  ${a.status ?? "?"}`);
  }),

  panel_ai_providers: tool("AI 供应商列表 — 名称、模型支持", async () => {
    const d = await api.get("/ai/agents/providers");
    if (!Array.isArray(d)) return fmtObj("AI 供应商", d);
    const lines = ["= AI 供应商 ="];
    for (const p of d) {
      const models = Array.isArray(p.models) ? p.models.map((m) => m.model ?? m.name ?? "?").join(", ") : "";
      lines.push(`  ${p.displayName ?? p.provider ?? "?"}  [${p.baseUrl ?? ""}]`);
      if (models) lines.push(`    模型: ${models.slice(0, 80)}`);
    }
    if (!d.length) lines.push("  (空)");
    return lines.join("\n");
  }),

  panel_ollama: tool("Ollama 模型列表 — 名称、大小", async () => {
    const d = await api.post("/ai/ollama/model/search", { page: 1, pageSize: 50 });
    return fmtSearch("Ollama 模型", d, (m) => `${m.name ?? "?"}  ${m.size ?? "?"}`);
  }),

  panel_gpu_load: tool("GPU 负载信息 — GPU 型号、显存使用率", async () => {
    const d = await api.get("/ai/gpu/load");
    if (!Array.isArray(d)) return fmtObj("GPU 负载", d);
    return fmtList("GPU 负载", d, (g) => `${g.name ?? "?"}  显存: ${g.memoryUsed ?? "?"}/${g.memoryTotal ?? "?"}  利用率: ${g.gpuUtil ?? "?"}%`);
  }),

  // ── 新增工具 ──────────────────────────────────────────────

  panel_ai_overview: tool("AI 全局概览 — 智能体总数、运行状态、渠道概览", async () => {
    const d = await api.post("/ai/agents/overview", {});
    return fmtObj("AI 概览", d);
  }),

  panel_ai_agent_roles: tool("AI 智能体角色列表 — 已配置的角色", async () => {
    const d = await api.post("/ai/agents/agent/list", {});
    return fmtList("AI 智能体角色", d, (r) => `${r.name ?? "?"}  [${r.model ?? "?"}]  ${r.status ?? "?"}`);
  }),

  panel_ai_model_config: tool("AI 模型配置详情 — 当前模型参数", async () => {
    const d = await api.post("/ai/agents/model/get", {});
    return fmtObj("AI 模型配置", d);
  }),

  panel_ai_config_file: tool("AI Agent 配置文件内容", async () => {
    const d = await api.post("/ai/agents/config-file/get", {});
    return fmtObj("AI 配置文件", d, 120);
  }),

  panel_ai_security: tool("AI 安全配置 — 访问控制、权限设置", async () => {
    const d = await api.post("/ai/agents/security/get", {});
    return fmtObj("AI 安全配置", d);
  }),

  panel_ai_channels: tool("AI 渠道配置概览 — 各平台渠道状态", async () => {
    const channels = [
      { name: "钉钉", ep: "/ai/agents/channel/dingtalk/get" },
      { name: "Discord", ep: "/ai/agents/channel/discord/get" },
      { name: "飞书", ep: "/ai/agents/channel/feishu/get" },
      { name: "QQ 机器人", ep: "/ai/agents/channel/qqbot/get" },
      { name: "Telegram", ep: "/ai/agents/channel/telegram/get" },
      { name: "企业微信", ep: "/ai/agents/channel/wecom/get" },
    ];
    const lines = ["= AI 渠道配置 ="];
    for (const ch of channels) {
      try {
        const d = await api.post(ch.ep, {});
        lines.push(`  ${ch.name}: ${fmtBool(d?.enable ?? d?.enabled ?? false)}  ${d?.botToken ? "🟢已配置" : "⚪未配置"}`);
      } catch {
        lines.push(`  ${ch.name}: 查询失败`);
      }
    }
    return lines.join("\n");
  }),

  panel_ai_skills_list: tool("AI 技能列表 — 已安装的技能", async () => {
    const d = await api.post("/ai/agents/skills/list", {});
    return fmtList("AI 技能", d, (s) => `${s.name ?? "?"}  v${s.version ?? "?"}  ${s.description?.slice(0, 40) ?? ""}`);
  }),

  panel_ai_skills_search: toolWithParams("搜索 AI 技能 — 按关键词查询", async (args) => {
    const d = await api.post("/ai/agents/skills/search", { page: 1, pageSize: 20, ...args });
    return fmtSearch("AI 技能搜索结果", d, (s) => `${s.name ?? "?"}  ${(s.description ?? "").slice(0, 50)}`);
  }, { keywords: { type: "string", default: "" } }),

  panel_mcp_domain: tool("MCP Server 域名绑定信息", async () => {
    const d = await api.get("/ai/mcp/domain/get");
    return fmtObj("MCP 域名绑定", d);
  }),

  panel_ai_other_config: tool("AI 其他配置 — 杂项设置", async () => {
    const d = await api.post("/ai/agents/other/get", {});
    return fmtObj("AI 其他配置", d);
  }),

  panel_ai_agent_md: tool("AI 智能体 Markdown 文件列表", async () => {
    const d = await api.post("/ai/agents/agent/md/list", {});
    return fmtList("AI Agent MD 文件", d, (m) => m.name ?? m.path ?? "?");
  }),

  panel_ai_agent_channels: tool("AI 智能体角色渠道配置", async () => {
    const d = await api.post("/ai/agents/agent/channels", {});
    return fmtList("Agent 角色渠道", d, (c) => `${c.channel ?? "?"}  ${c.enable ? "🟢" : "🔴"}  ${c.remark ?? ""}`);
  }),

  panel_ollama_config: tool("Ollama 运行配置状态", async () => {
    try {
      const d = await api.post("/ai/ollama/model", {});
      return fmtObj("Ollama 配置", d);
    } catch {
      return "= Ollama =\n  Ollama 未安装或未运行";
    }
  }),

};

function statusIcon(s) {
  if (s === "Running" || s === "running" || s === "Enabled") return "🟢";
  if (s === "Stopped" || s === "stopped" || s === "Disabled") return "🔴";
  if (s === "Error" || s === "error") return "⚠️";
  return "⚪";
}
