/**
 * mcp-1panel — Backups 模块工具（7 个）
 */
import { tool, toolWithParams, fmtObj, fmtList, fmtSearch, fmtGeneric } from "./helpers.js";
import { api } from "../api-proxy.js";

export const BACKUPS_TOOLS = {

  panel_backups: tool("备份记录列表 — 类型、文件", async () => {
    const d = await api.post("/backups/record/search", { page: 1, pageSize: 20, type: "all" });
    return fmtSearch("备份记录", d, (b) => `${b.type ?? "?"}: ${b.bucket ?? "?"}  ${b.filePath ?? ""}`);
  }),

  panel_backup_options: tool("备份账号选项 — 本地/远程存储类型、配置", async () => {
    const d = await api.get("/backups/options");
    return fmtGeneric("备份账号选项", d);
  }),

  panel_backup_local: tool("本地备份目录信息", async () => {
    const d = await api.get("/backups/local");
    return fmtObj("本地备份目录", d);
  }),

  panel_backup_accounts: tool("备份账号列表 — 存储类型、配置", async () => {
    const d = await api.post("/backups/search", { page: 1, pageSize: 50 });
    return fmtSearch("备份账号", d, (b) => `${b.type ?? "?"}  ${b.bucket ?? ""}  ${(b.endpoint ?? "").slice(0, 40)}`);
  }),

  panel_backup_buckets: toolWithParams("列出存储桶 — 按账号类型", async (args) => {
    const d = await api.post("/backups/buckets", args);
    return fmtList("存储桶", d, (b) => b.bucket ?? b.name ?? "?");
  }, { type: { type: "string", default: "LOCAL" } }),

  panel_backup_check: toolWithParams("检查备份账号连通性", async (args) => {
    const d = await api.post("/backups/check", args);
    return fmtObj("备份检查结果", d);
  }, { type: { type: "string", default: "LOCAL" } }),

  panel_backup_files: toolWithParams("备份目录文件列表", async (args) => {
    const d = await api.post("/backups/search/files", args);
    return fmtList("备份文件", Array.isArray(d) ? d : d?.items ?? [], (f) => `${f.name ?? "?"}  ${f.size ?? ""}`);
  }, { type: { type: "string", default: "LOCAL" } }),

};
