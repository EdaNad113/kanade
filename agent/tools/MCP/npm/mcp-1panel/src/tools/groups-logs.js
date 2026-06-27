/**
 * mcp-1panel — Groups & Logs 模块工具（5 个）
 */
import { tool, toolWithParams, fmtObj, fmtList } from "./helpers.js";
import { api } from "../api-proxy.js";

export const GROUPS_TOOLS = {

  panel_groups: tool("分组列表 — 所有资源的分组", async () => {
    const d = await api.post("/groups/search", { page: 1, pageSize: 50 });
    const items = d.items ?? [];
    return fmtList("分组", items, (g) => `${g.name ?? "?"}  [${g.type ?? "?"}]  ${g.isDefault ? "⭐默认" : ""}`);
  }),

};

export const LOGS_TOOLS = {

  panel_system_log_files: tool("系统日志文件列表", async () => {
    const d = await api.get("/logs/system/files");
    return fmtList("系统日志文件", Array.isArray(d) ? d : [], (f) => `${f.name ?? "?"}  ${f.size ?? ""}`);
  }),

  panel_executing_tasks: tool("正在执行的任务数", async () => {
    const d = await api.get("/logs/tasks/executing/count");
    return `= 执行中的任务 =\n  当前: ${d ?? 0} 个任务正在执行`;
  }),

  panel_login_logs: tool("登录日志 — 最近登录记录", async (args) => {
    const d = await api.post("/core/logs/login", { page: 1, pageSize: args.rows ?? 20, orderBy: "createdAt", order: "descending" });
    const items = d.items ?? [];
    const lines = [`= 登录日志 (共${d.total ?? 0}条) =`];
    for (const log of items) lines.push(`  ${log.createdAt ?? "?"}  ${log.ip ?? "?"}  ${log.authResult ?? "?"}  ${(log.userAgent ?? "").slice(0, 40)}`);
    if (!items.length) lines.push("  (空)");
    return lines.join("\n");
  }, { rows: { type: "number", default: 20 } }),

  panel_task_logs: tool("任务执行日志 — 系统任务记录", async (args) => {
    const d = await api.post("/logs/tasks/search", { page: 1, pageSize: args.rows ?? 20 });
    return fmtObj("任务日志", d);
  }, { rows: { type: "number", default: 20 } }),

};
