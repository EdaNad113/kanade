/**
 * mcp-1panel — Core 模块工具（15 个）
 */
import { tool, toolWithParams, fmtObj, fmtList, fmtSearch } from "./helpers.js";
import { api } from "../api-proxy.js";

export const CORE_TOOLS = {

  panel_logs: tool("操作日志 — 时间、操作内容", async (args) => {
    const d = await api.post("/core/logs/operation", {
      page: 1, pageSize: args.rows ?? 20, orderBy: "createdAt", order: "descending",
    });
    return fmtSearch("操作日志", d, (log) => `${log.createdAt ?? "?"}  ${(log.operation ?? "?").slice(0, 60)}`);
  }, { rows: { type: "number", default: 20 } }),

  panel_settings: tool("面板基础设置 — 名称、端口、版本等", async () => {
    const d = await api.post("/core/settings/search", { page: 1, pageSize: 50 });
    const info = {};
    if (Array.isArray(d)) for (const s of d) info[s.key] = s.value;
    const keys = ["PanelName", "ServerPort", "Language", "Theme", "SessionTimeout", "SystemVersion", "Edition"];
    const lines = ["= 面板设置 ="];
    for (const k of keys) {
      let v = info[k] ?? "?";
      if (String(v).length > 60) v = String(v).slice(0, 60) + "...";
      lines.push(`  ${k}: ${v}`);
    }
    return lines.join("\n");
  }),

  panel_upgrade_info: tool("面板升级信息 — 当前版本、最新版本", async () => {
    const d = await api.get("/core/settings/upgrade");
    return fmtObj("面板升级", d);
  }),

  panel_ssl_cert_info: tool("面板 SSL 证书信息 — 域名、到期时间、颁发者", async () => {
    const d = await api.get("/core/settings/ssl/info");
    return fmtObj("面板 SSL 证书", d);
  }),

  panel_dashboard_memo: tool("仪表盘备忘录 — 自定义备忘内容", async () => {
    const d = await api.get("/core/settings/memo");
    return `= 仪表盘备忘录 =\n  ${String(d ?? "(空)").slice(0, 200)}`;
  }),

  panel_login_setting: tool("登录认证设置 — 登录方式、安全策略", async () => {
    const d = await api.get("/core/auth/setting");
    return fmtObj("登录设置", d);
  }),

  panel_commands_tree: tool("命令树 — 可用的系统命令分类", async () => {
    const d = await api.get("/core/commands/tree");
    return fmtObj("命令树", d);
  }),

  panel_commands_list: tool("命令列表 — 所有已注册命令", async () => {
    const d = await api.get("/core/commands/command");
    return fmtList("命令列表", d, (c) => `${c.name ?? "?"}  ${(c.description ?? "").slice(0, 50)}`);
  }),

  panel_system_address: tool("系统地址信息 — 面板访问地址、IP", async () => {
    const d = await api.get("/core/settings/interface");
    return fmtObj("系统地址", d);
  }),

  panel_upgrade_releases: tool("面板升级发布日志 — 版本历史", async () => {
    const d = await api.get("/core/settings/upgrade/releases");
    return fmtList("版本发布", Array.isArray(d) ? d : [], (r) => `v${r.version ?? "?"}  ${(r.description ?? "").slice(0, 60)}`);
  }),

  panel_setting_by_key_post: toolWithParams("按 Key 查询系统设置 (POST /core/settings/by)", async (args) => {
    const d = await api.post("/core/settings/by", { key: args.key });
    return `= ${args.key} =\n  ${String(d ?? "?").slice(0, 200)}`;
  }, { key: { type: "string", default: "" } }),

  panel_terminal_setting: tool("终端设置 — 字体、样式、安全配置", async () => {
    const d = await api.post("/core/settings/terminal/search", {});
    return fmtObj("终端设置", d);
  }),

  panel_release_notes: toolWithParams("版本发布说明 — 按版本查询", async (args) => {
    const d = await api.post("/core/settings/upgrade/notes", { version: args.version });
    return fmtObj(`v${args.version} 发布说明`, d, 200);
  }, { version: { type: "string", default: "" } }),

  panel_backup_client_info: toolWithParams("备份账号基础信息", async (args) => {
    const d = await api.get(`/core/backups/client/${args.type}`);
    return fmtObj("备份账号信息", d);
  }, { type: { type: "string", default: "LOCAL" } }),

  panel_available_status: tool("系统可用状态 — 各服务健康检查", async () => {
    const d = await api.get("/core/settings/search/available");
    return fmtObj("系统可用状态", d);
  }),

};
