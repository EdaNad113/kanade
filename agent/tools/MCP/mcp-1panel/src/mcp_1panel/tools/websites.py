"""MCP tools for website, SSL, and DNS management via 1Panel API."""

from typing import Any, Callable, Dict, List
from mcp_1panel.tools.helpers import (
    icon_green,
    icon_red,
    icon_lock,
    icon_unlock,
    icon_status,
    header,
    fmt_val,
    fmt_obj,
    fmt_list,
    fmt_search,
    fmt_generic,
)


def register_tools(mcp, get_client, handlers=None):
    """Register all website/SSL/DNS management MCP tools."""

    # ------------------------------------------------------------------ #
    # Website list and detail
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_websites(page: int = 1, size: int = 20) -> str:
        """网站列表 — 域名、别名、运行状态、SSL"""
        p = get_client()
        data = p.post("/websites/search", {
            "page": page, "pageSize": size,
            "orderBy": "createdAt", "order": "descending",
        })
        lines, items = fmt_search(data, "网站列表")
        for w in items:
            domain = w.get("primaryDomain", w.get("domain", "?"))
            alias = w.get("alias", "")
            running = w.get("status", w.get("running", 0))
            run_icon = icon_green() if running else "\u23f9"  # 🟢 / ⏹
            https = w.get("https", w.get("hasSSL", False))
            https_icon = icon_lock() if https else icon_unlock()
            label = f"{run_icon} {https_icon} {domain}"
            if alias:
                label += f"  ({alias})"
            lines.append(f"  {label}")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_website_detail(id: int) -> str:
        """网站详情 — 配置、状态、域名"""
        p = get_client()
        data = p.get(f"/websites/detail?id={id}")
        return fmt_generic(data, f"网站详情 (ID: {id})")

    @mcp.tool()
    def panel_website_nginx(id: int, type: str = "nginx") -> str:
        """网站 Nginx 配置"""
        p = get_client()
        data = p.get(f"/websites/nginx?id={id}&type={type}")
        return fmt_generic(data, f"Nginx 配置 (ID: {id})")

    @mcp.tool()
    def panel_website_https(id: int) -> str:
        """网站 HTTPS 配置"""
        p = get_client()
        data = p.get(f"/websites/https?id={id}")
        return fmt_generic(data, f"HTTPS 配置 (ID: {id})")

    @mcp.tool()
    def panel_website_domains(id: int) -> str:
        """网站域名列表"""
        p = get_client()
        data = p.get(f"/websites/domains?id={id}")
        lines = [header(f"域名列表 (ID: {id})")]
        if isinstance(data, list):
            for d in data:
                domain = d.get("domain", d.get("name", fmt_val(d)))
                port = d.get("port", "")
                lines.append(f"  {domain}  {f':{port}' if port else ''}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_website_ssl(id: int) -> str:
        """网站 SSL 证书"""
        p = get_client()
        data = p.get(f"/websites/ssl?id={id}")
        return fmt_generic(data, f"SSL 证书 (ID: {id})")

    @mcp.tool()
    def panel_website_ssl_by_site(id: int) -> str:
        """按网站 ID 查询 SSL 证书"""
        p = get_client()
        data = p.get(f"/websites/ssl/bysite?id={id}")
        return fmt_generic(data, f"站点 SSL 证书 (ID: {id})")

    # ------------------------------------------------------------------ #
    # SSL, ACME, DNS, CA lists
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_ssl_list() -> str:
        """SSL 证书列表"""
        p = get_client()
        data = p.get("/websites/ssl/list")
        lines = [header("SSL 证书列表", len(data) if isinstance(data, list) else None)]
        if isinstance(data, list):
            for cert in data:
                domain = cert.get("primaryDomain", cert.get("domain", "?"))
                issuer = cert.get("issuer", cert.get("organization", ""))
                expire = cert.get("expireDate", cert.get("expireAt", "?"))
                lines.append(f"  {domain}  {fmt_val(issuer)}  expires: {expire}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_acme_accounts() -> str:
        """ACME 账户列表 — Let's Encrypt 等"""
        p = get_client()
        data = p.get("/websites/acme/accounts")
        lines = [header("ACME 账户", len(data) if isinstance(data, list) else None)]
        if isinstance(data, list):
            for acc in data:
                email = acc.get("email", "?")
                provider = acc.get("ca", acc.get("provider", "?"))
                status = acc.get("status", "?")
                st = icon_green() if status in ("valid", "active", "ok") else icon_red()
                lines.append(f"  {st} {email}  [{provider}]")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_dns_accounts() -> str:
        """DNS 账户列表 — 域名解析服务商"""
        p = get_client()
        data = p.get("/websites/dns/accounts")
        lines = [header("DNS 账户", len(data) if isinstance(data, list) else None)]
        if isinstance(data, list):
            for acc in data:
                name = acc.get("name", acc.get("provider", "?"))
                vendor = acc.get("type", acc.get("vendor", "?"))
                status = acc.get("status", "")
                st = icon_green() if status in ("valid", "active", "ok") else icon_red() if status else ""
                label = f"  {name}  [{vendor}]"
                if st:
                    label = f"  {st} {name}  [{vendor}]"
                lines.append(label)
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ca_certificates() -> str:
        """CA 证书列表 — 自定义证书颁发机构"""
        p = get_client()
        data = p.get("/websites/ca")
        lines = [header("CA 证书", len(data) if isinstance(data, list) else None)]
        if isinstance(data, list):
            for ca in data:
                name = ca.get("name", ca.get("commonName", "?"))
                org = ca.get("organization", "")
                expire = ca.get("expireDate", ca.get("expireAt", ""))
                ln = f"  {name}"
                if org:
                    ln += f"  [{org}]"
                if expire:
                    ln += f"  expires: {expire}"
                lines.append(ln)
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_ca_detail(id: int) -> str:
        """CA 证书详情"""
        p = get_client()
        data = p.get(f"/websites/ca/detail?id={id}")
        return fmt_generic(data, f"CA 证书详情 (ID: {id})")

    # ------------------------------------------------------------------ #
    # Database and config
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_website_db() -> str:
        """网站关联数据库"""
        p = get_client()
        data = p.get("/websites/db")
        lines = [header("网站关联数据库", len(data) if isinstance(data, list) else None)]
        if isinstance(data, list):
            for db in data:
                name = db.get("name", db.get("database", "?"))
                wname = db.get("website", db.get("siteName", ""))
                lines.append(f"  {name}  {f'({wname})' if wname else ''}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_website_config(id: int) -> str:
        """网站 Nginx 配置详情"""
        p = get_client()
        data = p.post("/websites/config", {"id": id})
        return fmt_generic(data, f"Nginx 配置详情 (ID: {id})")

    # ------------------------------------------------------------------ #
    # Directory, CORS, RealIP
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_website_dir(id: int) -> str:
        """网站目录信息"""
        p = get_client()
        data = p.get(f"/websites/dir?id={id}")
        return fmt_generic(data, f"网站目录 (ID: {id})")

    @mcp.tool()
    def panel_website_cors(id: int) -> str:
        """网站 CORS 配置"""
        p = get_client()
        data = p.get(f"/websites/cors?id={id}")
        return fmt_generic(data, f"CORS 配置 (ID: {id})")

    @mcp.tool()
    def panel_website_realip(id: int) -> str:
        """网站 RealIP 配置"""
        p = get_client()
        data = p.get(f"/websites/realip?id={id}")
        return fmt_generic(data, f"RealIP 配置 (ID: {id})")

    # ------------------------------------------------------------------ #
    # Upstreams, Proxy, Rewrite, Redirect
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_website_upstreams() -> str:
        """负载均衡上游列表"""
        p = get_client()
        data = p.get("/websites/upstreams")
        lines = [header("上游列表", len(data) if isinstance(data, list) else None)]
        if isinstance(data, list):
            for up in data:
                name = up.get("name", up.get("upstream", "?"))
                servers = up.get("servers", [])
                ln = f"  {name}"
                if isinstance(servers, list):
                    for s in servers:
                        addr = s.get("address", fmt_val(s))
                        ln += f"  -> {addr}"
                lines.append(ln)
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    @mcp.tool()
    def panel_website_proxy(id: int) -> str:
        """网站反向代理配置"""
        p = get_client()
        data = p.get(f"/websites/proxy?id={id}")
        return fmt_generic(data, f"反向代理 (ID: {id})")

    @mcp.tool()
    def panel_website_rewrite(id: int) -> str:
        """网站重写规则"""
        p = get_client()
        data = p.get(f"/websites/rewrite?id={id}")
        return fmt_generic(data, f"重写规则 (ID: {id})")

    @mcp.tool()
    def panel_website_redirect(id: int) -> str:
        """网站重定向配置"""
        p = get_client()
        data = p.get(f"/websites/redirect?id={id}")
        return fmt_generic(data, f"重定向 (ID: {id})")

    # ------------------------------------------------------------------ #
    # Anti-leech, Auth, Log
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_website_antileech(id: int) -> str:
        """网站防盗链配置"""
        p = get_client()
        data = p.get(f"/websites/antileech?id={id}")
        return fmt_generic(data, f"防盗链 (ID: {id})")

    @mcp.tool()
    def panel_website_auth(id: int) -> str:
        """网站 BasicAuth 认证配置"""
        p = get_client()
        data = p.get(f"/websites/auth?id={id}")
        return fmt_generic(data, f"BasicAuth (ID: {id})")

    @mcp.tool()
    def panel_website_log(id: int, rows: int = 50) -> str:
        """网站访问日志"""
        p = get_client()
        data = p.get(f"/websites/log?id={id}&rows={rows}")
        lines = [header(f"访问日志 (ID: {id})")]
        if isinstance(data, list):
            for log in data[:rows]:
                ts = log.get("time", log.get("createdAt", log.get("timestamp", "?")))
                ip = log.get("ip", log.get("remoteAddr", ""))
                method = log.get("method", log.get("requestMethod", ""))
                url = log.get("url", log.get("requestUri", ""))
                status = log.get("status", log.get("httpCode", ""))
                ln = f"  {ts}"
                if ip:
                    ln += f"  {ip}"
                if method:
                    ln += f"  {method}"
                if url:
                    ln += f"  {url}"
                if status:
                    ln += f"  [{status}]"
                lines.append(ln)
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Simple list
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_website_list_simple() -> str:
        """网站简要列表"""
        p = get_client()
        data = p.get("/websites/list")
        lines = [header("网站简要列表", len(data) if isinstance(data, list) else None)]
        if isinstance(data, list):
            for w in data:
                domain = w.get("primaryDomain", w.get("domain", w.get("name", "?")))
                alias = w.get("alias", "")
                ln = f"  {domain}"
                if alias:
                    ln += f"  ({alias})"
                lines.append(ln)
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # -- 收集 handler 供 resources 复用 --
    if handlers is not None:
        for _name, _fn in list(locals().items()):
            if _name.startswith("panel_") and callable(_fn):
                handlers[_name] = _fn
