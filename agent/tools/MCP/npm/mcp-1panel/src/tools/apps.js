/**
 * mcp-1panel — Apps 模块工具（12 个）
 */
import { tool, toolWithParams, fmtObj, fmtList, fmtSearch, statusIcon } from "./helpers.js";
import { api } from "../api-proxy.js";

export const APPS_TOOLS = {

  panel_apps: tool("已安装的应用商店应用 — 名称、版本、状态", async () => {
    const d = await api.get("/apps/installed/list", { page: 1, pageSize: 50 });
    const items = d.items ?? [];
    const lines = [`= 已安装应用 (共${d.total ?? items.length}个) =`];
    for (const a of items) lines.push(`  ${statusIcon(a.status)} ${a.appKey ?? "?"}  v${a.version ?? "?"}`);
    if (!items.length) lines.push("  (空)");
    return lines.join("\n");
  }),

  panel_app_store_list: tool("应用商店应用列表 — 所有可用应用", async () => {
    const d = await api.post("/apps/search", { page: 1, pageSize: 50 });
    return fmtSearch("应用商店", d, (a) => `${a.name ?? "?"}  v${(a.versions ?? [])[0] ?? "?"}  ${a.shortDesc ?? ""}`);
  }),

  panel_app_detail: toolWithParams("应用详情 — 按 key 查询", async (args) => {
    const d = await api.get(`/apps/${encodeURIComponent(args.key)}`);
    return fmtObj("应用详情", d);
  }, { key: { type: "string", default: "" } }),

  panel_app_check_updates: tool("应用更新检查 — 有更新的应用列表", async () => {
    const d = await api.get("/apps/checkupdate");
    return fmtList("应用更新", d, (a) => `${a.name ?? "?"}  当前: v${a.currentVersion ?? "?"} → 最新: v${a.latestVersion ?? "?"}`);
  }),

  panel_app_installed_detail: toolWithParams("已安装应用详情 — 安装信息", async (args) => {
    const d = await api.get(`/apps/installed/info/${args.id}`);
    return fmtObj("安装详情", d);
  }, { id: { type: "number", default: 1 } }),

  panel_app_installed_params: toolWithParams("已安装应用参数 — 安装时的配置参数", async (args) => {
    const d = await api.get(`/apps/installed/params/${args.id}`);
    return fmtObj("应用参数", d);
  }, { id: { type: "number", default: 1 } }),

  panel_app_installed_conf: toolWithParams("应用默认配置 — 按 key 查询", async (args) => {
    const d = await api.post("/apps/installed/conf", { key: args.key });
    return fmtObj("应用默认配置", d);
  }, { key: { type: "string", default: "" } }),

  panel_app_conninfo: toolWithParams("应用连接信息 — 账号/密码/端口", async (args) => {
    const d = await api.post("/apps/installed/conninfo", { key: args.key });
    return fmtObj("连接信息", d);
  }, { key: { type: "string", default: "" } }),

  panel_app_ignored_upgrades: tool("已忽略升级的应用列表", async () => {
    const d = await api.get("/apps/ignored/detail");
    return fmtList("已忽略升级", d, (a) => `${a.name ?? "?"}  v${a.version ?? "?"}`);
  }),

  panel_app_installed_loadport: toolWithParams("应用端口信息 — 按 key 查询", async (args) => {
    const d = await api.post("/apps/installed/loadport", { key: args.key });
    return fmtObj("应用端口", d);
  }, { key: { type: "string", default: "" } }),

  panel_app_service: toolWithParams("应用服务详情 — 按 key 查询", async (args) => {
    const d = await api.get(`/apps/services/${encodeURIComponent(args.key)}`);
    return fmtObj("应用服务", d);
  }, { key: { type: "string", default: "" } }),

  panel_app_detail_by_id: toolWithParams("应用详情（按 ID）", async (args) => {
    const d = await api.get(`/apps/details/${args.id}`);
    return fmtObj("应用详情", d);
  }, { id: { type: "number", default: 1 } }),

};
