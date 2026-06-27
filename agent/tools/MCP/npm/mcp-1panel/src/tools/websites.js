/**
 * mcp-1panel — Websites 模块工具（25 个）
 */
import { tool, toolWithParams, fmtObj, fmtList, fmtSearch, statusIcon } from "./helpers.js";
import { api } from "../api-proxy.js";

export const WEBSITES_TOOLS = {

  panel_websites: tool("网站列表 — 域名、SSL 状态、别名", async (args) => {
    const d = await api.post("/websites/search", {
      page: args.page ?? 1, pageSize: args.size ?? 20,
      orderBy: "createdAt", order: "descending",
    });
    const items = d.items ?? [];
    const lines = [`= 网站 (共${d.total ?? 0}个) =`];
    for (const w of items) {
      const s = w.status === "Running" ? "🟢" : "🔴";
      const h = w.https ? "🔒" : "🔓";
      lines.push(`  ${s} ${h} ${w.primaryDomain ?? "?"} [${w.alias ?? "?"}]`);
    }
    if (!items.length) lines.push("  (空)");
    return lines.join("\n");
  }, { page: { type: "number", default: 1 }, size: { type: "number", default: 20 } }),

  panel_website_detail: toolWithParams("网站详情 — 配置、状态、域名", async (args) => {
    const d = await api.get(`/websites/${args.id}`);
    return fmtObj("网站详情", d);
  }, { id: { type: "number", default: 1 } }),

  panel_website_nginx: toolWithParams("网站 Nginx 配置", async (args) => {
    const d = await api.get(`/websites/${args.id}/config/${args.type ?? "nginx"}`);
    return typeof d === "string" ? `= Nginx 配置 =\n${d.slice(0, 3000)}` : fmtObj("Nginx 配置", d, 200);
  }, { id: { type: "number", default: 1 }, type: { type: "string", default: "nginx" } }),

  panel_website_https: toolWithParams("网站 HTTPS 配置", async (args) => {
    const d = await api.get(`/websites/${args.id}/https`);
    return fmtObj("HTTPS 配置", d);
  }, { id: { type: "number", default: 1 } }),

  panel_website_domains: toolWithParams("网站域名列表", async (args) => {
    const d = await api.get(`/websites/domains/${args.id}`);
    return fmtList("网站域名", Array.isArray(d) ? d : [], (dm) => `${dm.domain ?? "?"}  ${dm.port ?? "?"}  ${dm.https ? "🔒" : "🔓"}`);
  }, { id: { type: "number", default: 1 } }),

  panel_website_ssl: toolWithParams("网站 SSL 证书", async (args) => {
    const d = await api.get(`/websites/ssl/${args.id}`);
    return fmtObj("SSL 证书", d);
  }, { id: { type: "number", default: 1 } }),

  panel_website_ssl_by_site: toolWithParams("按网站 ID 查询 SSL 证书", async (args) => {
    const d = await api.get(`/websites/ssl/website/${args.id}`);
    return fmtObj("网站 SSL", d);
  }, { id: { type: "number", default: 1 } }),

  panel_ssl_list: tool("SSL 证书列表", async () => {
    const d = await api.post("/websites/ssl/search", { page: 1, pageSize: 50 });
    return fmtSearch("SSL 证书", d, (s) => `${s.domains ?? "?"}  到期: ${s.expireDate ?? "?"}  颁发者: ${s.issuer ?? "?"}`);
  }),

  panel_acme_accounts: tool("ACME 账户列表 — Let's Encrypt 等", async () => {
    const d = await api.post("/websites/acme/search", { page: 1, pageSize: 50 });
    return fmtSearch("ACME 账户", d, (a) => `${a.email ?? "?"}  ${a.type ?? "?"}  ${a.status ?? "?"}`);
  }),

  panel_dns_accounts: tool("DNS 账户列表 — 域名解析服务商", async () => {
    const d = await api.post("/websites/dns/search", { page: 1, pageSize: 50 });
    return fmtSearch("DNS 账户", d, (dns) => `${dns.name ?? "?"}  ${dns.type ?? "?"}  ${dns.status ?? "?"}`);
  }),

  panel_ca_certificates: tool("CA 证书列表 — 自定义证书颁发机构", async () => {
    const d = await api.post("/websites/ca/search", { page: 1, pageSize: 50 });
    return fmtSearch("CA 证书", d, (ca) => `${ca.name ?? "?"}  ${ca.commonName ?? "?"}  到期: ${ca.expireDate ?? "?"}`);
  }),

  panel_ca_detail: toolWithParams("CA 证书详情", async (args) => {
    const d = await api.get(`/websites/ca/${args.id}`);
    return fmtObj("CA 证书", d);
  }, { id: { type: "number", default: 1 } }),

  panel_website_db: tool("网站关联数据库", async () => {
    const d = await api.get(`/websites/databases`);
    return fmtList("网站数据库", Array.isArray(d) ? d : [], (db) => `${db.name ?? "?"}  ${db.type ?? "?"}  ${db.status ?? "?"}`);
  }),

  panel_website_config: toolWithParams("网站 Nginx 配置详情", async (args) => {
    const d = await api.post("/websites/config", { websiteId: args.id });
    return fmtObj("网站 Nginx 配置", d, 200);
  }, { id: { type: "number", default: 1 } }),

  panel_website_dir: toolWithParams("网站目录信息", async (args) => {
    const d = await api.post("/websites/dir", { websiteId: args.id });
    return fmtObj("网站目录", d);
  }, { id: { type: "number", default: 1 } }),

  panel_website_cors: toolWithParams("网站 CORS 配置", async (args) => {
    const d = await api.get(`/websites/cors/${args.id}`);
    return fmtObj("CORS 配置", d);
  }, { id: { type: "number", default: 1 } }),

  panel_website_realip: toolWithParams("网站 RealIP 配置", async (args) => {
    const d = await api.get(`/websites/realip/config/${args.id}`);
    return fmtObj("RealIP 配置", d);
  }, { id: { type: "number", default: 1 } }),

  panel_website_upstreams: tool("负载均衡上游列表", async () => {
    const d = await api.get("/websites/lbs");
    return fmtList("负载均衡上游", Array.isArray(d) ? d : [], (lb) => `${lb.name ?? "?"}  ${lb.type ?? "?"}  ${lb.status ?? "?"}`);
  }),

  panel_website_proxy: toolWithParams("网站反向代理配置", async (args) => {
    const d = await api.post("/websites/proxies", { websiteId: args.id });
    return fmtObj("反向代理", d);
  }, { id: { type: "number", default: 1 } }),

  panel_website_rewrite: toolWithParams("网站重写规则", async (args) => {
    const d = await api.post("/websites/rewrite", { websiteId: args.id });
    return fmtObj("重写规则", d);
  }, { id: { type: "number", default: 1 } }),

  panel_website_redirect: toolWithParams("网站重定向配置", async (args) => {
    const d = await api.post("/websites/redirect", { websiteId: args.id });
    return fmtObj("重定向", d);
  }, { id: { type: "number", default: 1 } }),

  panel_website_antileech: toolWithParams("网站防盗链配置", async (args) => {
    const d = await api.post("/websites/leech", { websiteId: args.id });
    return fmtObj("防盗链", d);
  }, { id: { type: "number", default: 1 } }),

  panel_website_auth: toolWithParams("网站 BasicAuth 认证配置", async (args) => {
    const d = await api.post("/websites/auths", { websiteId: args.id });
    return fmtObj("BasicAuth", d);
  }, { id: { type: "number", default: 1 } }),

  panel_website_log: toolWithParams("网站访问日志", async (args) => {
    const d = await api.post("/websites/log", { websiteId: args.id, page: 1, pageSize: args.rows ?? 50 });
    return fmtObj("网站日志", d, 200);
  }, { id: { type: "number", default: 1 }, rows: { type: "number", default: 50 } }),

  panel_website_list_simple: tool("网站简要列表", async () => {
    const d = await api.get("/websites/list");
    return fmtList("网站列表", Array.isArray(d) ? d : [], (w) => `${w.domain ?? w.primaryDomain ?? "?"}  ${statusIcon(w.status)} ${w.status ?? "?"}`);
  }),

};
