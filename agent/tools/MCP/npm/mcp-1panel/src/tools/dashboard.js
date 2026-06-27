/**
 * mcp-1panel — Dashboard 模块工具（9 个）
 */
import { tool, toolWithParams, fmtObj, fmtList } from "./helpers.js";
import { api } from "../api-proxy.js";

export const DASHBOARD_TOOLS = {

  panel_overview: tool("面板总览 — 系统版本、CPU、内存、磁盘、应用/网站/数据库数量", async () => {
    const [o, c, a, w, mysql, pg] = await Promise.all([
      api.get("/dashboard/base/os"),
      api.get("/dashboard/current/0/0"),
      api.get("/apps/installed/list", { page: 1, pageSize: 1 }),
      api.post("/websites/search", { page: 1, pageSize: 1, orderBy: "createdAt", order: "descending" }),
      api.get("/databases/db/list/mysql"),
      api.get("/databases/db/list/postgresql"),
    ]);
    const dbCount = (mysql || []).length + (pg || []).length;
    return [
      "= 面板总览 =", "",
      `系统: ${o.prettyDistro ?? "?"} / ${o.kernelVersion ?? "?"}`,
      `CPU: ${c.cpuPercent ?? "?"}% (${c.cpuCore ?? "?"} 核)`,
      `内存: ${c.memoryUsed ?? "?"} / ${c.memoryTotal ?? "?"}`,
      `磁盘: ${c.diskUsed ?? "?"} / ${c.diskTotal ?? "?"}`,
      `负载: ${c.loadAvg ?? "?"}`, "",
      `应用: ${a?.total ?? 0} | 网站: ${w?.total ?? 0} | 数据库: ${dbCount}`,
    ].join("\n");
  }),

  panel_monitor: tool("实时监控 — CPU/内存/磁盘百分比、负载", async () => {
    const c = await api.get("/dashboard/current/0/0");
    return [
      "= 实时监控 =",
      `CPU: ${c.cpuPercent ?? "?"}% | 内存: ${c.memoryPercent ?? "?"}% | 磁盘: ${c.diskPercent ?? "?"}%`,
      `负载: ${c.loadAvg ?? "?"}`,
    ].join("\n");
  }),

  panel_top_cpu: tool("CPU 占用最高的进程 Top10", async () => {
    const d = await api.get("/dashboard/current/top/cpu");
    return fmtList("CPU Top 进程", d?.slice(0, 10), (p) => {
      const cpu = p.percent != null ? Number(p.percent).toFixed(1) : "?";
      return `PID ${p.pid ?? "?"}  ${(p.name ?? "?").slice(0, 25)}  CPU ${cpu}%  用户 ${p.user ?? "?"}`;
    });
  }),

  panel_top_memory: tool("内存占用最高的进程 Top10", async () => {
    const d = await api.get("/dashboard/current/top/mem");
    return fmtList("内存 Top 进程", d?.slice(0, 10), (p) => {
      const memMB = p.memory != null ? Number(p.memory / 1024 / 1024).toFixed(1) : "?";
      const pct = p.percent != null ? Number(p.percent).toFixed(1) : "?";
      return `PID ${p.pid ?? "?"}  ${(p.name ?? "?").slice(0, 25)}  MEM ${memMB}MB (${pct}%)  用户 ${p.user ?? "?"}`;
    });
  }),

  panel_base_info: tool("面板基本信息 — 系统、内核、运行时间", async () => {
    const o = await api.get("/dashboard/base/os");
    return fmtObj("系统信息", o);
  }),

  panel_node_info: tool("节点信息 — 当前节点运行状态", async () => {
    const d = await api.get("/dashboard/current/node");
    return fmtObj("节点信息", d);
  }),

  panel_app_launcher: tool("应用启动器 — 快捷启动的应用列表", async () => {
    const d = await api.get("/dashboard/app/launcher");
    return fmtList("应用启动器", Array.isArray(d) ? d : [], (a) => `${a.name ?? "?"}  ${a.url ?? ""}`);
  }),

  panel_launcher_options: tool("启动器选项 — 自定义快捷方式", async () => {
    const d = await api.post("/dashboard/app/launcher/option", {});
    return fmtObj("启动器选项", d);
  }),

  panel_quick_jump: tool("快速跳转选项 — 常用导航", async () => {
    const d = await api.get("/dashboard/quick/option");
    return fmtObj("快速跳转", d);
  }),

};
