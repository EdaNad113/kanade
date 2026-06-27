/**
 * mcp-1panel — OpenResty / Process 模块工具（7 个）
 */
import { tool, toolWithParams, fmtObj, fmtList } from "./helpers.js";
import { api } from "../api-proxy.js";

export const OPENRESTY_TOOLS = {

  panel_openresty: tool("OpenResty 状态 — 活动连接、请求数", async () => {
    const d = await api.get("/openresty/status");
    return fmtObj("OpenResty 状态", d);
  }),

  panel_openresty_config: tool("OpenResty 配置概览 — 主配置路径、状态", async () => {
    const d = await api.get("/openresty");
    return fmtObj("OpenResty 配置", d);
  }),

  panel_openresty_modules: tool("OpenResty 已加载模块列表", async () => {
    const d = await api.get("/openresty/modules");
    const lines = ["= OpenResty 模块 ="];
    if (d && typeof d === "object") {
      for (const [k, v] of Object.entries(d)) {
        if (Array.isArray(v)) {
          lines.push(`  ${k}:`);
          for (const m of v) lines.push(`    ${m.enable ? "✅" : "⬜"} ${m.name ?? "?"}  ${m.packages ?? ""}`);
        } else {
          lines.push(`  ${k}: ${String(v).slice(0, 80)}`);
        }
      }
    }
    if (!d) lines.push("  (空)");
    return lines.join("\n");
  }),

  panel_openresty_https: tool("默认 HTTPS 配置状态", async () => {
    const d = await api.get("/openresty/https");
    return fmtObj("OpenResty HTTPS", d);
  }),

  panel_openresty_scope: toolWithParams("OpenResty 局部配置 — 按范围查询", async (args) => {
    const d = await api.post("/openresty/scope", { scope: args.scope ?? "http" });
    return fmtObj(`OpenResty ${args.scope ?? "http"} 配置`, d, 200);
  }, { scope: { type: "string", default: "http" } }),

};

export const PROCESS_TOOLS = {

  panel_process_listening: tool("监听端口列表 — 全部进程端口", async () => {
    const d = await api.post("/process/listening", {});
    return fmtList("监听端口", Array.isArray(d) ? d.slice(0, 50) : [], (p) =>
      `${p.protocol ?? "?"} ${p.port ?? "?"}  ${p.processName ?? "?"}  PID ${p.pid ?? "?"}  ${p.user ?? ""}`
    );
  }),

  panel_process_info: toolWithParams("进程详情 — 按 PID 查询", async (args) => {
    const d = await api.get(`/process/${args.pid}`);
    return fmtObj(`进程 ${args.pid}`, d);
  }, { pid: { type: "number", default: 1 } }),

};
