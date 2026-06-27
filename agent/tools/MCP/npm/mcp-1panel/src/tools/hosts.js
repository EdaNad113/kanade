/**
 * mcp-1panel — Hosts 模块工具（17 个）
 */
import { tool, toolWithParams, fmtObj, fmtList, fmtSearch, fmtBool, statusIcon } from "./helpers.js";
import { api } from "../api-proxy.js";

export const HOSTS_TOOLS = {

  panel_disks: tool("磁盘分区详情 — 路径、用量（含进度条）", async () => {
    const d = await api.get("/hosts/disks");
    const lines = ["= 磁盘分区 ="];
    for (const disk of d ?? []) {
      const pct = disk.usedPercent ?? 0;
      const full = "█".repeat(Math.floor(pct / 10));
      const empty = "░".repeat(10 - Math.floor(pct / 10));
      lines.push(`  ${disk.path ?? "?"} [${full}${empty}] ${disk.used ?? "?"}/${disk.total ?? "?"} (${pct}%)`);
    }
    if (!d?.length) lines.push("  (空)");
    return lines.join("\n");
  }),

  panel_firewall: tool("防火墙规则 — 协议、端口、策略", async () => {
    const d = await api.post("/hosts/firewall/search", { page: 1, pageSize: 50, type: "port" });
    return fmtSearch("防火墙规则", d, (r) => `${r.protocol ?? "?"} 端口${r.port ?? "?"} ${r.address ?? "?"} -> ${r.strategy ?? "?"}`);
  }),

  panel_ssh: tool("SSH 配置列表 — 名称、地址、端口", async () => {
    const d = await api.post("/hosts/ssh/search", { page: 1, pageSize: 50 });
    return fmtSearch("SSH 配置", d, (s) => `${s.name ?? "?"} @ ${s.addr ?? "?"}:${s.port ?? "?"}`);
  }),

  panel_system_component: toolWithParams("检查系统组件是否存在", async (args) => {
    const d = await api.get(`/hosts/components/${args.name}`);
    return `= 系统组件 =\n  ${args.name}: ${d?.exists ?? d?.exist ?? d ? "已安装 ✅" : "未安装 ❌"}`;
  }, { name: { type: "string", default: "docker" } }),

  panel_firewall_base: tool("防火墙基础配置 — 默认策略、状态", async () => {
    const d = await api.post("/hosts/firewall/base", {});
    return fmtObj("防火墙基础配置", d);
  }),

  panel_firewall_filter: tool("防火墙过滤规则 — iptables 规则列表", async () => {
    const d = await api.post("/hosts/firewall/filter/search", {});
    return fmtList("过滤规则", Array.isArray(d) ? d : d?.items ?? [], (r) =>
      `${r.chain ?? "?"} ${r.protocol ?? "?"} ${r.source ?? "?"} ${r.target ?? "?"}`
    );
  }),

  panel_firewall_forward: tool("防火墙端口转发规则", async () => {
    const d = await api.post("/hosts/firewall/forward", {});
    return fmtList("端口转发", Array.isArray(d) ? d : [], (r) =>
      `${r.protocol ?? "?"} ${r.srcPort ?? "?"} -> ${r.destIp ?? "?"}:${r.destPort ?? "?"}`
    );
  }),

  panel_firewall_ip: tool("防火墙 IP 黑/白名单", async () => {
    const d = await api.post("/hosts/firewall/ip", { page: 1, pageSize: 50 });
    const items = d.items ?? d ?? [];
    return fmtList("IP 规则", Array.isArray(items) ? items : [], (r) =>
      `${r.address ?? "?"}  ${r.strategy ?? "?"}  ${(r.desc ?? "").slice(0, 40)}`
    );
  }),

  panel_monitor_history: toolWithParams("历史监控数据查询", async (args) => {
    const d = await api.post("/hosts/monitor/search", { page: 1, pageSize: args.rows ?? 20, type: args.type ?? "cpu" });
    return fmtObj(`监控历史 (${args.type ?? "cpu"})`, d);
  }, { type: { type: "string", default: "cpu" }, rows: { type: "number", default: 20 } }),

  panel_monitor_setting: tool("监控设置 — 采集间隔、保留天数", async () => {
    const d = await api.get("/hosts/monitor/setting");
    return fmtObj("监控设置", d);
  }),

  panel_ssh_certs: tool("SSH 证书列表 — 密钥对", async () => {
    const d = await api.post("/hosts/ssh/cert/search", { page: 1, pageSize: 50 });
    return fmtSearch("SSH 证书", d, (c) => `${c.name ?? "?"}  ${c.type ?? "?"}  ${c.fingerprint ?? ""}`);
  }),

  panel_ssh_conf: toolWithParams("SSH 配置文件内容", async (args) => {
    const d = await api.post("/hosts/ssh/file", { id: args.id });
    return typeof d === "string" ? `= SSH 配置 =\n${d.slice(0, 2000)}` : fmtObj("SSH 配置", d, 200);
  }, { id: { type: "number", default: 0 } }),

  panel_ssh_logs: toolWithParams("SSH 登录日志", async (args) => {
    const d = await api.post("/hosts/ssh/log", { page: 1, pageSize: args.rows ?? 20 });
    return fmtSearch("SSH 登录日志", d, (l) => `${l.time ?? "?"}  ${l.ip ?? "?"}  ${l.status ?? "?"}  ${l.user ?? ""}`);
  }, { rows: { type: "number", default: 20 } }),

  panel_tool_status: toolWithParams("系统工具状态查询", async (args) => {
    const d = await api.post("/hosts/tool", { name: args.name });
    return fmtObj(`工具状态: ${args.name}`, d);
  }, { name: { type: "string", default: "supervisor" } }),

  panel_tool_config: toolWithParams("系统工具配置", async (args) => {
    const d = await api.post("/hosts/tool/config", { name: args.name });
    return fmtObj(`工具配置: ${args.name}`, d);
  }, { name: { type: "string", default: "supervisor" } }),

  panel_supervisor_processes: tool("Supervisor 进程列表", async () => {
    const d = await api.get("/hosts/tool/supervisor/process");
    return fmtList("Supervisor 进程", Array.isArray(d) ? d : [], (p) =>
      `${statusIcon(p.status)} ${p.name ?? "?"}  ${p.status ?? "?"}  PID ${p.pid ?? "?"}`
    );
  }),

  panel_gpu_monitor: tool("GPU 监控历史数据", async () => {
    const d = await api.post("/hosts/monitor/gpu/search", { page: 1, pageSize: 20 });
    return fmtObj("GPU 监控", d);
  }),

};
