/**
 * mcp-1panel — Runtimes 模块工具（12 个）
 */
import { tool, toolWithParams, fmtObj, fmtList } from "./helpers.js";
import { api } from "../api-proxy.js";

export const RUNTIMES_TOOLS = {

  panel_runtimes: tool("运行环境列表 — PHP/Node 等", async () => {
    const d = await api.post("/runtimes/search", { page: 1, pageSize: 50 });
    const items = d.items ?? [];
    const lines = [`= 运行环境 (共${d.total ?? items.length}个) =`];
    for (const r of items) lines.push(`  ${r.name ?? "?"}  ${r.type ?? "?"}  v${r.version ?? "?"}  [${r.status ?? "?"}]`);
    if (!items.length) lines.push("  (空)");
    return lines.join("\n");
  }),

  panel_runtime_detail: toolWithParams("运行环境详情", async (args) => {
    const d = await api.get(`/runtimes/${args.id}`);
    return fmtObj("运行环境详情", d);
  }, { id: { type: "number", default: 1 } }),

  panel_php_extensions: toolWithParams("PHP 扩展列表", async (args) => {
    const d = await api.get(`/runtimes/php/${args.id}/extensions`);
    return fmtList("PHP 扩展", Array.isArray(d) ? d : [], (e) => `${e.name ?? "?"}  ${e.version ?? ""}  ${e.enable ? "✅" : "⬜"}`);
  }, { id: { type: "number", default: 1 } }),

  panel_php_config: toolWithParams("PHP 运行配置", async (args) => {
    const d = await api.get(`/runtimes/php/config/${args.id}`);
    return fmtObj("PHP 配置", d);
  }, { id: { type: "number", default: 1 } }),

  panel_php_container: toolWithParams("PHP 容器配置", async (args) => {
    const d = await api.get(`/runtimes/php/container/${args.id}`);
    return fmtObj("PHP 容器配置", d);
  }, { id: { type: "number", default: 1 } }),

  panel_php_fpm_config: toolWithParams("PHP-FPM 配置", async (args) => {
    const d = await api.get(`/runtimes/php/fpm/config/${args.id}`);
    return fmtObj("PHP-FPM 配置", d);
  }, { id: { type: "number", default: 1 } }),

  panel_php_fpm_status: toolWithParams("PHP-FPM 运行状态", async (args) => {
    const d = await api.get(`/runtimes/php/fpm/status/${args.id}`);
    return fmtObj("PHP-FPM 状态", d);
  }, { id: { type: "number", default: 1 } }),

  panel_php_file: toolWithParams("PHP 配置文件内容", async (args) => {
    const d = await api.post("/runtimes/php/file", { id: args.id });
    return typeof d === "string" ? `= PHP 配置文件 =\n${d.slice(0, 2000)}` : fmtObj("PHP 配置文件", d, 200);
  }, { id: { type: "number", default: 1 } }),

  panel_node_modules: toolWithParams("Node.js 模块列表", async (args) => {
    const d = await api.post("/runtimes/node/modules", { id: args.id });
    return fmtList("Node 模块", Array.isArray(d) ? d.slice(0, 50) : [], (m) => `${m.name ?? "?"}  v${m.version ?? "?"}`);
  }, { id: { type: "number", default: 1 } }),

  panel_node_package: toolWithParams("Node.js 包脚本", async (args) => {
    const d = await api.post("/runtimes/node/package", { id: args.id });
    return fmtObj("Node 包脚本", d);
  }, { id: { type: "number", default: 1 } }),

  panel_supervisor_process_detail: toolWithParams("Supervisor 进程详情", async (args) => {
    const d = await api.get(`/runtimes/supervisor/process/${args.id}`);
    return fmtObj("Supervisor 进程", d);
  }, { id: { type: "number", default: 1 } }),

  panel_runtime_php_extensions_list: toolWithParams("PHP 可用扩展列表", async (args) => {
    const d = await api.post("/runtimes/php/extensions/search", { page: 1, pageSize: 50, runtimeId: args.id });
    const items = d.items ?? d ?? [];
    return fmtList("PHP 可用扩展", Array.isArray(items) ? items : [], (e) => `${e.name ?? "?"}  ${e.version ?? ""}  ${e.installed ? "✅" : "⬜"}`);
  }, { id: { type: "number", default: 1 } }),

};
