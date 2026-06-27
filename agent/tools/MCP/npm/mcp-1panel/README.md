# mcp-1panel

> **MCP Server for 1Panel** — 通过 MCP 协议查询 1Panel 服务器状态（只读）。

基于原始 [Python 版](https://github.com/EdaNad113/kanade/tree/main/agent/tools/MCP/mcp-1panel) 的 Node.js 移植版。  
设计用于 **1Panel 内置 MCP 管理**，也支持任何 MCP 客户端（Cursor、Claude Desktop、Windsurf 等）。

---

## 目录

- [快速开始](#快速开始)
- [客户端连接配置](#客户端连接配置)
- [1Panel MCP Server 配置](#1panel-mcp-server-配置)
- [工具列表](#工具列表)
- [资源列表](#资源列表)
- [环境变量](#环境变量)
- [项目结构](#项目结构)
- [开发](#开发)
- [与 Python 版的区别](#与-python-版的区别)

---

## 快速开始

### 前置条件

- 1Panel 面板 v2.x
- 1Panel API 密钥（面板设置 → API 接口 → 创建密钥）

### 方式一：本地运行

```bash
cd agent/tools/MCP/npm/mcp-1panel
PANEL_HOST=http://localhost:8080 PANEL_API_KEY=your_api_key node src/index.js
```

### 方式二：npm link（全局注册）

```bash
npm install
npm link
PANEL_HOST=http://localhost:8080 PANEL_API_KEY=your_api_key mcp-1panel
```

### 方式三：npx（需先发布到 npm）

```bash
PANEL_HOST=http://localhost:8080 PANEL_API_KEY=your_api_key npx @kanade/mcp-1panel
```

---

## 客户端连接配置

### stdio 模式（本地）

```json
{
  "mcpServers": {
    "mcp-1panel": {
      "command": "node",
      "args": ["/opt/1panel/mcp/mcp-1panel/src/index.js"],
      "env": {
        "PANEL_HOST": "http://localhost:8080",
        "PANEL_API_KEY": "<your API key>"
      }
    }
  }
}
```

> 环境变量支持 `PANEL_API_KEY` 或 `PANEL_ACCESS_TOKEN` 两种写法。

### SSE 模式（远程）

```json
{
  "mcpServers": {
    "mcp-1panel": {
      "url": "http://your-server:10002/mcp-1panel",
      "transport": "sse"
    }
  }
}
```

---

## 1Panel MCP Server 配置

在 1Panel → AI → MCP 中创建：

| 字段 | 值 |
|------|-----|
| 名称 | `mcp-1panel` |
| 类型 | `npx` 或 `node` |
| 启动命令 | `npx -y @kanade/mcp-1panel` 或 `node /opt/1panel/mcp/mcp-1panel/src/index.js` |
| 环境变量 | `PANEL_HOST=http://localhost:8080` + `PANEL_API_KEY=...` |
| 端口 | `10002` |

> ⚠️ 部署为 node 类型时，需要手动在 docker-compose.yml 中添加 `volumes` 挂载源码目录。

---

## 工具列表

> **共 199 个工具**，覆盖 18 个模块。所有工具均为**只读查询**，不会修改任何 1Panel 配置。

### 🤖 AI（18 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_mcp_servers` | MCP Server 列表 | — |
| `panel_ai_agents` | AI 智能体列表 | — |
| `panel_ai_providers` | AI 供应商列表 | — |
| `panel_ai_overview` | AI 全局概览 | — |
| `panel_ai_agent_roles` | 智能体角色列表 | — |
| `panel_ai_agent_channels` | 角色渠道配置 | — |
| `panel_ai_agent_md` | Agent MD 文件列表 | — |
| `panel_ai_model_config` | 模型配置详情 | — |
| `panel_ai_config_file` | Agent 配置文件 | — |
| `panel_ai_security` | AI 安全配置 | — |
| `panel_ai_channels` | 渠道配置概览 | — |
| `panel_ai_skills_list` | 技能列表 | — |
| `panel_ai_skills_search` | 搜索技能 | `keywords` |
| `panel_ai_other_config` | 其他配置 | — |
| `panel_mcp_domain` | MCP 域名绑定 | — |
| `panel_ollama` | Ollama 模型列表 | — |
| `panel_ollama_config` | Ollama 运行状态 | — |
| `panel_gpu_load` | GPU 负载信息 | — |

### 📦 应用商店（12 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_apps` | 已安装应用列表 | — |
| `panel_app_store_list` | 应用商店列表 | — |
| `panel_app_detail` | 应用详情 | `key` |
| `panel_app_detail_by_id` | 应用详情（按 ID） | `id` |
| `panel_app_check_updates` | 应用更新检查 | — |
| `panel_app_installed_detail` | 安装详情 | `id` |
| `panel_app_installed_params` | 安装参数 | `id` |
| `panel_app_installed_conf` | 默认配置 | `key` |
| `panel_app_conninfo` | 连接信息 | `key` |
| `panel_app_ignored_upgrades` | 已忽略升级 | — |
| `panel_app_installed_loadport` | 端口信息 | `key` |
| `panel_app_service` | 服务详情 | `key` |

### 🗄️ 备份（7 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_backups` | 备份记录列表 | — |
| `panel_backup_options` | 备份账号选项 | — |
| `panel_backup_local` | 本地备份目录 | — |
| `panel_backup_accounts` | 备份账号列表 | — |
| `panel_backup_buckets` | 列出存储桶 | `type` |
| `panel_backup_check` | 检查备份账号 | `type` |
| `panel_backup_files` | 备份文件列表 | `type` |

### 🐳 容器（22 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_containers` | 容器列表 | — |
| `panel_containers_by_image` | 按镜像查找容器 | `image` |
| `panel_container_info` | 容器详情 | `id`, `name` |
| `panel_container_inspect` | Inspect 信息 | `id` |
| `panel_container_stats` | 资源统计 | `id` |
| `panel_container_limits` | 资源限制 | — |
| `panel_container_status` | 状态概览 | — |
| `panel_container_logs` | 日志概览 | — |
| `panel_container_users` | 用户列表 | — |
| `panel_images` | 镜像列表 | — |
| `panel_image_options` | 镜像仓库选项 | — |
| `panel_image_repos` | 镜像仓库列表 | — |
| `panel_repo_status` | 仓库连通性 | `id` |
| `panel_compose` | Compose 项目列表 | — |
| `panel_compose_templates` | 模板列表 | — |
| `panel_compose_env` | 环境变量 | `id` |
| `panel_networks` | 网络列表 | — |
| `panel_volumes` | 存储卷列表 | — |
| `panel_docker_status` | Docker 守护进程状态 | — |
| `panel_docker_daemon` | daemon.json 配置 | — |
| `panel_docker_daemon_file` | daemon.json 文件 | — |
| `panel_processes` | 端口监听列表 | — |

### ⚙️ 核心设置（15 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_settings` | 面板基础设置 | — |
| `panel_setting_by_key` | 按 Key 查询设置 | `key` |
| `panel_setting_by_key_post` | 按 Key 查询设置(POST) | `key` |
| `panel_login_setting` | 登录认证设置 | — |
| `panel_commands_tree` | 命令树 | — |
| `panel_commands_list` | 命令列表 | — |
| `panel_system_address` | 系统地址信息 | — |
| `panel_available_status` | 系统可用状态 | — |
| `panel_terminal_setting` | 终端设置 | — |
| `panel_upgrade_info` | 升级信息 | — |
| `panel_upgrade_releases` | 版本发布日志 | — |
| `panel_release_notes` | 版本说明 | `version` |
| `panel_ssl_cert_info` | SSL 证书信息 | — |
| `panel_dashboard_memo` | 仪表盘备忘录 | — |
| `panel_backup_client_info` | 备份账号信息 | `type` |

### ⏰ 计划任务（6 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_cronjobs` | 任务列表 | — |
| `panel_cronjob_info` | 任务详情 | `id` |
| `panel_cronjob_next` | 下次执行时间 | `id`, `cronSpec` |
| `panel_cronjob_records` | 执行记录 | `id` |
| `panel_cronjob_record_log` | 执行日志 | `id` |
| `panel_script_options` | 脚本选项 | — |

### 📊 仪表盘（9 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_overview` | 面板总览 | — |
| `panel_base_info` | 系统信息 | — |
| `panel_monitor` | 实时监控 | — |
| `panel_node_info` | 节点信息 | — |
| `panel_top_cpu` | CPU Top10 进程 | — |
| `panel_top_memory` | 内存 Top10 进程 | — |
| `panel_app_launcher` | 应用启动器 | — |
| `panel_launcher_options` | 启动器选项 | — |
| `panel_quick_jump` | 快速跳转 | — |

### 🗃️ 数据库（14 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_databases` | 数据库列表 | — |
| `panel_db_list_by_type` | 按类型列数据库 | `type` |
| `panel_db_detail_by_name` | 数据库详情 | `name` |
| `panel_db_check` | 检查可连接性 | `name`, `type` |
| `panel_db_base_info` | 基础信息 | `name`, `type` |
| `panel_db_conf_file` | 配置文件 | `type` |
| `panel_db_item` | 数据库项列表 | `type` |
| `panel_mysql_status` | MySQL 运行状态 | — |
| `panel_mysql_variables` | MySQL 变量 | — |
| `panel_mysql_collation` | 排序规则选项 | — |
| `panel_mysql_remote` | 远程访问配置 | — |
| `panel_redis_status` | Redis 运行状态 | — |
| `panel_redis_conf` | Redis 配置 | — |
| `panel_redis_persistence` | Redis 持久化配置 | — |

### 📂 文件管理（10 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_files` | 浏览目录 | `path` |
| `panel_file_content` | 文件内容预览 | `path` |
| `panel_file_size` | 文件/目录大小 | `path` |
| `panel_file_check` | 检查文件存在 | `path` |
| `panel_file_tree` | 目录树 | `path` |
| `panel_file_remarks` | 文件备注 | `path` |
| `panel_file_batch_check` | 批量检查 | `paths` |
| `panel_favorites` | 收藏夹列表 | — |
| `panel_recycle_bin` | 回收站文件 | — |
| `panel_recycle_status` | 回收站状态 | — |

### 🏷️ 分组（1 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_groups` | 分组列表 | — |

### 🖥️ 主机管理（17 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_disks` | 磁盘分区 | — |
| `panel_firewall` | 防火墙规则 | — |
| `panel_firewall_base` | 防火墙基础配置 | — |
| `panel_firewall_filter` | iptables 过滤规则 | — |
| `panel_firewall_forward` | 端口转发规则 | — |
| `panel_firewall_ip` | IP 黑/白名单 | — |
| `panel_ssh` | SSH 配置列表 | — |
| `panel_ssh_certs` | SSH 证书列表 | — |
| `panel_ssh_conf` | SSH 配置文件 | `id` |
| `panel_ssh_logs` | SSH 登录日志 | `rows` |
| `panel_monitor_history` | 历史监控数据 | `type`, `rows` |
| `panel_monitor_setting` | 监控设置 | — |
| `panel_gpu_monitor` | GPU 监控 | — |
| `panel_system_component` | 检查系统组件 | `name` |
| `panel_tool_status` | 工具状态 | `name` |
| `panel_tool_config` | 工具配置 | `name` |
| `panel_supervisor_processes` | Supervisor 进程列表 | — |

### 📋 日志（5 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_logs` | 操作日志 | `rows` |
| `panel_login_logs` | 登录日志 | `rows` |
| `panel_system_log_files` | 系统日志文件 | — |
| `panel_executing_tasks` | 执行中的任务数 | — |
| `panel_task_logs` | 任务执行日志 | `rows` |

### 🔌 OpenResty（5 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_openresty` | 运行状态 | — |
| `panel_openresty_config` | 配置概览 | — |
| `panel_openresty_modules` | 已加载模块 | — |
| `panel_openresty_https` | HTTPS 配置 | — |
| `panel_openresty_scope` | 局部配置 | `scope` |

### 🔄 进程（3 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_process_listening` | 监听端口列表 | — |
| `panel_process_info` | 进程详情 | `pid` |
| `panel_processes` | 端口监听（容器） | — |

### 🏗️ 运行环境（12 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_runtimes` | 环境列表 | — |
| `panel_runtime_detail` | 环境详情 | `id` |
| `panel_php_extensions` | PHP 扩展列表 | `id` |
| `panel_php_config` | PHP 运行配置 | `id` |
| `panel_php_container` | PHP 容器配置 | `id` |
| `panel_php_fpm_config` | PHP-FPM 配置 | `id` |
| `panel_php_fpm_status` | PHP-FPM 状态 | `id` |
| `panel_php_file` | PHP 配置文件 | `id` |
| `panel_runtime_php_extensions_list` | PHP 可用扩展 | `id` |
| `panel_node_modules` | Node 模块列表 | `id` |
| `panel_node_package` | Node 包脚本 | `id` |
| `panel_supervisor_process_detail` | Supervisor 进程详情 | `id` |

### ⚡ 系统设置（8 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_snapshot_list` | 快照列表 | — |
| `panel_snapshot_info` | 快照信息 | — |
| `panel_snapshot_recover` | 快照恢复信息 | `id` |
| `panel_setting_by_key` | 按 Key 查设置 | `key` |
| `panel_backup_dir` | 备份目录路径 | — |
| `panel_ssh_conn` | SSH 连接配置 | — |
| `panel_ssh_check` | 连接信息检查 | — |
| `panel_system_available` | 系统可用状态 | — |

### 🛠️ 工具箱（12 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_fail2ban` | Fail2ban 状态 | — |
| `panel_fail2ban_conf` | Fail2ban 配置 | — |
| `panel_fail2ban_list` | 封禁 IP 列表 | — |
| `panel_ftp` | FTP 账号列表 | — |
| `panel_ftp_base` | FTP 基础配置 | — |
| `panel_ftp_logs` | FTP 操作日志 | — |
| `panel_clamav` | ClamAV 状态 | — |
| `panel_clamav_records` | 查杀记录 | — |
| `panel_clamav_files` | 扫描文件配置 | — |
| `panel_device_base` | 设备信息 | — |
| `panel_device_dns` | DNS 检查 | — |
| `panel_timezones` | 时区选项 | — |

### 🌐 网站（25 个）

| 工具 | 说明 | 参数 |
|------|------|------|
| `panel_websites` | 网站列表 | `page`, `size` |
| `panel_website_list_simple` | 网站简要列表 | — |
| `panel_website_detail` | 网站详情 | `id` |
| `panel_website_nginx` | Nginx 配置 | `id`, `type` |
| `panel_website_https` | HTTPS 配置 | `id` |
| `panel_website_domains` | 域名列表 | `id` |
| `panel_website_ssl` | SSL 证书 | `id` |
| `panel_website_ssl_by_site` | 按网站查 SSL | `id` |
| `panel_website_config` | Nginx 配置详情 | `id` |
| `panel_website_dir` | 目录信息 | `id` |
| `panel_website_db` | 关联数据库 | — |
| `panel_website_cors` | CORS 配置 | `id` |
| `panel_website_realip` | RealIP 配置 | `id` |
| `panel_website_proxy` | 反向代理 | `id` |
| `panel_website_rewrite` | 重写规则 | `id` |
| `panel_website_redirect` | 重定向 | `id` |
| `panel_website_antileech` | 防盗链 | `id` |
| `panel_website_auth` | BasicAuth | `id` |
| `panel_website_log` | 访问日志 | `id`, `rows` |
| `panel_website_upstreams` | 负载均衡上游 | — |
| `panel_ssl_list` | SSL 证书列表 | — |
| `panel_acme_accounts` | ACME 账户 | — |
| `panel_dns_accounts` | DNS 账户 | — |
| `panel_ca_certificates` | CA 证书列表 | — |
| `panel_ca_detail` | CA 证书详情 | `id` |

---

## 资源列表

| URI | 对应工具 | 说明 |
|-----|---------|------|
| `panel://overview` | `panel_overview` | 面板总览 |
| `panel://websites` | `panel_websites` | 网站列表 |
| `panel://containers` | `panel_containers` | 容器列表 |
| `panel://databases` | `panel_databases` | 数据库列表 |
| `panel://disks` | `panel_disks` | 磁盘分区 |
| `panel://mcp` | `panel_mcp_servers` | MCP Server |
| `panel://monitor` | `panel_monitor` | 实时监控 |
| `panel://settings` | `panel_settings` | 面板设置 |
| `panel://docker-status` | `panel_docker_status` | Docker 状态 |
| `panel://firewall` | `panel_firewall` | 防火墙 |
| `panel://ssh` | `panel_ssh` | SSH 配置 |
| `panel://cronjobs` | `panel_cronjobs` | 计划任务 |
| `panel://backups` | `panel_backups` | 备份记录 |
| `panel://logs` | `panel_logs` | 操作日志 |
| `panel://fail2ban` | `panel_fail2ban` | Fail2ban 状态 |
| `panel://gpu` | `panel_gpu_load` | GPU 负载 |
| `panel://ai-agents` | `panel_ai_agents` | AI 智能体 |
| `panel://ollama` | `panel_ollama` | Ollama 模型 |

---

## 环境变量

| 变量 | 别名 | 必填 | 说明 |
|------|------|------|------|
| `PANEL_HOST` | — | ✅ | 1Panel 面板地址 |
| `PANEL_API_KEY` | `PANEL_ACCESS_TOKEN` | ✅ | API 密钥（面板设置 → API 接口） |

---

## 项目结构

```
mcp-1panel/
├── package.json              # 包配置
├── README.md                 # 本文件
├── .gitignore
├── .env.example              # 环境变量模板
├── src/
│   ├── index.js              # 主入口（自动安装依赖 + 启动）
│   ├── server.js             # MCP Server 启动 + 协议处理
│   ├── api-proxy.js          # API 懒代理（错误不缓存，自动重试）
│   ├── panel-client.js       # 1Panel API 客户端（MD5 签名认证）
│   ├── resources.js          # 资源端点定义（18 个 → 复用工具 handler）
│   ├── panel-client.test.js  # PanelClient 测试（12 个用例）
│   └── tools/
│       ├── index.js          # 聚合所有模块
│       ├── helpers.js        # 工具辅助函数（tool/toolWithParams/fmtObj/...）
│       ├── ai.js             # AI 模块（18 个工具）
│       ├── apps.js           # 应用商店模块（12 个工具）
│       ├── backups.js        # 备份模块（7 个工具）
│       ├── containers.js     # 容器模块（22 个工具）
│       ├── core.js           # 核心设置模块（15 个工具）
│       ├── cronjobs.js       # 计划任务模块（6 个工具）
│       ├── dashboard.js      # 仪表盘模块（9 个工具）
│       ├── databases.js      # 数据库模块（14 个工具）
│       ├── files.js          # 文件管理模块（10 个工具）
│       ├── groups-logs.js    # 分组 + 日志模块（5 个工具）
│       ├── hosts.js          # 主机管理模块（17 个工具）
│       ├── openresty-process.js # OpenResty + 进程模块（7 个工具）
│       ├── runtimes.js       # 运行环境模块（12 个工具）
│       ├── settings.js       # 系统设置模块（8 个工具）
│       ├── toolbox.js        # 工具箱模块（12 个工具）
│       └── websites.js       # 网站管理模块（25 个工具）
```

---

## 测试

本机测试（无需 1Panel 环境，使用 mock）：

```bash
node --test src/panel-client.test.js
```

覆盖：客户端初始化、MD5 认证签名、fetch 调用、HTTP/API 错误处理（共 12 个用例）。

---

## 开发

### 本地调试

```bash
npm install
PANEL_HOST=http://localhost:8080 PANEL_API_KEY=your_key node src/index.js
```

### 使用 MCP Inspector

```bash
npx @modelcontextprotocol/inspector node src/index.js
```

### 添加新工具

1. 在 `src/tools/` 下找到对应模块文件（或新建），导入 `tool` / `toolWithParams` 等辅助函数
2. 使用 `tool("描述", handler)` 或 `toolWithParams("描述", handler, { param: { type: "string" } })` 定义工具
3. 在 `src/tools/index.js` 中导入并合并进 `ALL_TOOLS`

### 发布到 npm

```bash
npm version patch
npm publish --access public
```

---

## v0.2.0 更新

- **api-proxy.js**：初始化失败不再永久缓存错误 — 环境变量修复后即刻生效，无需重启
- **helpers.js**：`toolWithParams` 仅将有默认值的参数标记为可选，`required` 数组只含无 `default` 的参数
- **panel-client.test.js**：新增 12 个测试用例，覆盖认证、HTTP 调用、错误处理

---

## 与 Python 版的区别

| 特性 | Python 版 | npm 版 |
|------|-----------|--------|
| 运行环境 | Python 3.10+ | Node.js 18+ |
| 部署方式 | Docker 容器 | **npx**（1Panel 原生支持） |
| 依赖 | `mcp>=1.0.0`, `requests` | `@modelcontextprotocol/sdk` |
| MCP 框架 | FastMCP | `@modelcontextprotocol/sdk` |
| 工具数量 | 44 | **199** |
| 资源数量 | 6 | **18** |
| 架构 | 单文件 | **模块化（16 个模块文件）** |

---

## 许可证

MIT

## 相关链接

- [1Panel 官方文档](https://1panel.cn/docs/)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [原始 Python 版](https://github.com/EdaNad113/kanade/tree/main/agent/tools/MCP/mcp-1panel)
