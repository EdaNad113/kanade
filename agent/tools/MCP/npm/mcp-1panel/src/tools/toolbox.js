/**
 * mcp-1panel — Toolbox 模块工具（12 个）
 */
import { tool, toolWithParams, fmtObj, fmtList, fmtSearch } from "./helpers.js";
import { api } from "../api-proxy.js";

export const TOOLBOX_TOOLS = {

  panel_fail2ban: tool("Fail2ban 状态 — 启用、SSH 保护", async () => {
    const d = await api.get("/toolbox/fail2ban/base");
    return [
      "= Fail2ban =",
      `启用: ${d.isEnabled ? "✅ 是" : "❌ 否"}`,
      `SSH 保护: ${d.sshdStatus ? "✅ 是" : "❌ 否"}`,
      `封禁数: ${d.banCount ?? "?"}`,
    ].join("\n");
  }),

  panel_fail2ban_conf: tool("Fail2ban 配置详情 — 封禁规则、时间", async () => {
    const d = await api.get("/toolbox/fail2ban/load/conf");
    return fmtObj("Fail2ban 配置", d);
  }),

  panel_fail2ban_list: tool("Fail2ban 封禁 IP 列表", async () => {
    const d = await api.post("/toolbox/fail2ban/search", { page: 1, pageSize: 50 });
    return fmtSearch("Fail2ban 封禁列表", d, (ip) => `${ip.ip ?? "?"}  封禁时间: ${ip["ban_time"] ?? ip.time ?? "?"}  原因: ${ip.reason ?? ""}`);
  }),

  panel_ftp: tool("FTP 账号列表 — 用户名、状态", async () => {
    const d = await api.post("/toolbox/ftp/search", { page: 1, pageSize: 50 });
    return fmtSearch("FTP 账号", d, (f) => `${f.user ?? "?"}  ${f.status ?? "?"}`);
  }),

  panel_ftp_base: tool("FTP 基础配置 — 状态、端口", async () => {
    const d = await api.get("/toolbox/ftp/base");
    return fmtObj("FTP 基础配置", d);
  }),

  panel_ftp_logs: tool("FTP 操作日志", async () => {
    const d = await api.post("/toolbox/ftp/log/search", { page: 1, pageSize: 20 });
    return fmtSearch("FTP 日志", d, (l) => `${l.time ?? "?"}  ${l.user ?? "?"}  ${l.operation ?? "?"}  ${l.ip ?? ""}`);
  }),

  panel_clamav: tool("ClamAV 杀毒状态 — 版本、活跃状态", async () => {
    const d = await api.post("/toolbox/clam/base", {});
    return fmtObj("ClamAV", d);
  }),

  panel_clamav_records: tool("ClamAV 查杀记录", async () => {
    const d = await api.post("/toolbox/clam/record/search", { page: 1, pageSize: 20 });
    return fmtSearch("ClamAV 查杀记录", d, (r) => `${r.time ?? "?"}  ${r.filePath ?? "?"}  ${r.status ?? "?"}  ${r.description ?? ""}`);
  }),

  panel_clamav_files: tool("ClamAV 扫描文件配置", async () => {
    const d = await api.post("/toolbox/clam/file/search", { page: 1, pageSize: 50 });
    return fmtSearch("ClamAV 扫描文件", d, (f) => `${f.path ?? "?"}  ${f.status ?? "?"}`);
  }),

  panel_device_base: tool("设备基础信息 — 主机名、系统信息", async () => {
    const d = await api.post("/toolbox/device/base", {});
    return fmtObj("设备信息", d);
  }),

  panel_device_dns: tool("设备 DNS 配置检查", async () => {
    const d = await api.post("/toolbox/device/check/dns", {});
    return fmtObj("DNS 检查", d);
  }),

  panel_timezones: tool("时区选项列表", async () => {
    const d = await api.get("/toolbox/device/zone/options");
    return fmtList("时区选项", Array.isArray(d) ? d : [], (z) => z.zone ?? z.value ?? z ?? "?");
  }),

};
