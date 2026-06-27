/**
 * mcp-1panel — Cronjobs 模块工具（6 个）
 */
import { tool, toolWithParams, fmtObj, fmtList, fmtSearch } from "./helpers.js";
import { api } from "../api-proxy.js";

export const CRONJOBS_TOOLS = {

  panel_cronjobs: tool("计划任务列表 — 名称、类型、Cron 表达式", async () => {
    const d = await api.post("/cronjobs/search", { page: 1, pageSize: 50, orderBy: "createdAt", order: "descending" });
    return fmtSearch("计划任务", d, (c) => `${c.name ?? "?"}  [${c.type ?? "?"}]  ${c.cronSpec ?? "?"}`);
  }),

  panel_cronjob_info: toolWithParams("计划任务详情 — 配置信息", async (args) => {
    const d = await api.post("/cronjobs/load/info", { id: args.id });
    return fmtObj("任务详情", d);
  }, { id: { type: "number", default: 0 } }),

  panel_cronjob_next: toolWithParams("计划任务下次执行时间", async (args) => {
    const d = await api.post("/cronjobs/next", { id: args.id, cronSpec: args.cronSpec ?? "" });
    return fmtObj("下次执行", d);
  }, { id: { type: "number", default: 0 }, cronSpec: { type: "string", default: "" } }),

  panel_cronjob_records: toolWithParams("计划任务执行记录 — 历史执行日志", async (args) => {
    const d = await api.post("/cronjobs/search/records", { page: 1, pageSize: 20, cronjobID: args.id });
    return fmtSearch("执行记录", d, (r) => `${r.startTime ?? "?"}  ${r.status ?? "?"}  ${(r.result ?? "").slice(0, 40)}`);
  }, { id: { type: "number", default: 0 } }),

  panel_cronjob_record_log: toolWithParams("计划任务执行日志详情", async (args) => {
    const d = await api.post("/cronjobs/records/log", { recordID: args.id });
    return typeof d === "string" ? `= 任务日志 =\n${d.slice(0, 3000)}` : fmtObj("任务日志", d, 200);
  }, { id: { type: "number", default: 0 } }),

  panel_script_options: tool("脚本选项 — 可用的脚本参数", async () => {
    const d = await api.get("/cronjobs/script/options");
    return fmtObj("脚本选项", d);
  }),

};
