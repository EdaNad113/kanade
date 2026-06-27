/**
 * mcp-1panel — Settings 模块工具（8 个）
 */
import { tool, toolWithParams, fmtObj, fmtList } from "./helpers.js";
import { api } from "../api-proxy.js";

export const SETTINGS_TOOLS = {

  panel_snapshot_list: tool("系统快照列表 — 可用的回滚点", async () => {
    const d = await api.post("/settings/snapshot/search", { page: 1, pageSize: 50, orderBy: "createdAt", order: "descending" });
    const items = d.items ?? [];
    return fmtList("系统快照", items, (s) => `${s.name ?? "?"}  ${s.createdAt ?? "?"}  ${s.size ?? "?"}  ${s.description ?? ""}`);
  }),

  panel_snapshot_info: tool("系统快照信息 — 状态、时间", async () => {
    const d = await api.get("/settings/snapshot/load");
    return fmtObj("快照信息", d);
  }),

  panel_setting_by_key: toolWithParams("按 Key 查询系统设置", async (args) => {
    const d = await api.get(`/settings/get/${args.key}`);
    return `= ${args.key} =\n  ${String(d ?? "?").slice(0, 200)}`;
  }, { key: { type: "string", default: "PanelName" } }),

  panel_ssh_conn: tool("本地 SSH 连接配置", async () => {
    const d = await api.get("/settings/ssh/conn");
    return fmtObj("SSH 连接", d);
  }),

  panel_ssh_check: tool("本地连接信息检查", async () => {
    const d = await api.post("/settings/ssh/check/info", {});
    return fmtObj("SSH 连接检查", d);
  }),

  panel_backup_dir: tool("本地备份目录路径", async () => {
    const d = await api.get("/settings/basedir");
    return `= 备份目录 =\n  ${String(d ?? "?")}`;
  }),

  panel_system_available: tool("系统可用状态 — 各模块健康检查", async () => {
    const d = await api.get("/settings/search/available");
    return fmtObj("系统可用状态", d);
  }),

  panel_snapshot_recover: toolWithParams("快照恢复信息查询", async (args) => {
    const d = await api.post("/settings/snapshot/recover", { id: args.id });
    return fmtObj("快照恢复信息", d);
  }, { id: { type: "number", default: 0 } }),

};
