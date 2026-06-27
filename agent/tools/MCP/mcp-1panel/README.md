# mcp-1panel

通过 MCP 协议管理 1Panel 面板。**199 个工具 + 18 个资源**，覆盖 18 个 1Panel API 模块。

> 另有 [Node.js 版](../npm/mcp-1panel/) 功能一致。

## 安装

### 从 GitHub 安装

```bash
git clone https://github.com/EdaNad113/kanade.git
cd kanade/agent/tools/MCP/mcp-1panel
pip install .
```

### 可编辑安装（开发用，改代码即时生效）

```bash
pip install -e .
```

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `PANEL_HOST` | 1Panel 面板地址（如 `http://localhost:9999`） | ✅ |
| `PANEL_API_KEY` | API 接口密钥 | ✅ |

## 使用

```bash
export PANEL_HOST=http://your-panel:port
export PANEL_API_KEY=***
mcp-1panel
```

## MCP Host 配置

### Hermes Agent

```bash
hermes config set mcp_servers.panel-manager.command "mcp-1panel"
hermes config set mcp_servers.panel-manager.transport stdio
```

### Claude Desktop / Cursor

```json
{
  "mcpServers": {
    "panel-manager": {
      "command": "mcp-1panel",
      "env": {
        "PANEL_HOST": "http://your-panel:port",
        "PANEL_API_KEY": "your-api-key"
      }
    }
  }
}
```

## 认证原理

```
Token = md5("1panel" + API-Key + UnixTimestamp)
```

请求头: `1Panel-Token` + `1Panel-Timestamp`

对应代码见 `panel_client.py`。

## 功能模块

| 模块 | 工具数 | 说明 |
|------|--------|------|
| 网站 | 25 | 网站列表/详情、SSL/ACME/DNS、CA 证书、CORS、反代、防盗链 |
| 容器 | 22 | Docker 容器、镜像、Compose、网络、存储卷、仓库 |
| AI | 18 | MCP Server、AI 智能体、Ollama、GPU、渠道、安全、技能 |
| 主机 | 17 | 磁盘、防火墙、SSH、监控、Supervisor、GPU 监控 |
| 核心 | 15 | 操作日志、面板设置、升级、命令、证书 |
| 数据库 | 14 | MySQL、PostgreSQL、Redis、配置、状态 |
| 应用商店 | 12 | 已安装/商店应用、更新检查、连接信息 |
| 运行环境 | 12 | PHP、Node.js、扩展、FPM 状态 |
| 工具箱 | 12 | Fail2ban、FTP、ClamAV、设备信息、时区 |
| 文件 | 10 | 文件浏览/内容/大小/检查、收藏夹、回收站 |
| 仪表盘 | 9 | 总览、监控、Top CPU/内存、快捷跳转 |
| 设置 | 8 | 快照、系统设置、SSH 连接、备份目录 |
| 备份 | 7 | 备份记录、账号、存储桶、连通性 |
| 计划任务 | 6 | 任务列表、详情、执行记录、日志 |
| 日志 | 4 | 登录日志、任务日志、系统日志 |
| OpenResty | 5 | 状态、配置、模块、HTTPS |
| 进程 | 2 | 监听端口、进程详情 |
| 分组 | 1 | 资源分组列表 |

### 资源（18 个 `panel://` URI）

所有资源复用对应的工具 handler，不重复调用逻辑。

| URI | 复用工具 | 说明 |
|-----|---------|------|
| `panel://overview` | `panel_overview` | 面板总览 |
| `panel://websites` | `panel_websites` | 网站列表 |
| `panel://containers` | `panel_containers` | Docker 容器列表 |
| `panel://databases` | `panel_databases` | 数据库列表 |
| `panel://disks` | `panel_disks` | 磁盘分区详情 |
| `panel://mcp` | `panel_mcp_servers` | MCP Server 列表 |
| `panel://monitor` | `panel_monitor` | 实时监控 |
| `panel://settings` | `panel_settings` | 面板设置 |
| `panel://docker-status` | `panel_docker_status` | Docker 守护进程状态 |
| `panel://firewall` | `panel_firewall` | 防火墙规则 |
| `panel://ssh` | `panel_ssh` | SSH 配置 |
| `panel://cronjobs` | `panel_cronjobs` | 计划任务列表 |
| `panel://backups` | `panel_backups` | 备份记录列表 |
| `panel://logs` | `panel_logs` | 操作日志 |
| `panel://fail2ban` | `panel_fail2ban` | Fail2ban 状态 |
| `panel://gpu` | `panel_gpu_load` | GPU 负载 |
| `panel://ai-agents` | `panel_ai_agents` | AI 智能体列表 |
| `panel://ollama` | `panel_ollama` | Ollama 模型列表 |

## 测试

```bash
cd kanade/agent/tools/MCP/mcp-1panel
pip install pytest          # 首次需要
pytest tests/ -v
```

覆盖：客户端初始化、MD5 认证签名、HTTP 调用（GET/POST/DELETE/PUT）、API 错误处理。

## 项目结构

```
mcp-1panel/
├── pyproject.toml              # 包定义 v0.2.0
├── src/mcp_1panel/
│   ├── __init__.py             # 导出 PanelClient + __version__
│   ├── __main__.py             # 快捷入口
│   ├── mcp_server.py           # 主入口，注册 199 工具 + 18 资源
│   ├── panel_client.py         # API 客户端（MD5 签名）
│   ├── resources.py            # 资源映射（复用工具 handler）
│   └── tools/                  # 16 个领域模块
│       ├── __init__.py
│       ├── helpers.py          # 格式化工具函数
│       ├── ai.py               # 18 个 AI 工具
│       ├── apps.py             # 12 个应用工具
│       ├── backups.py          # 7 个备份工具
│       ├── containers.py       # 22 个容器工具
│       ├── core.py             # 15 个核心工具
│       ├── cronjobs.py         # 6 个计划任务工具
│       ├── dashboard.py        # 9 个仪表盘工具
│       ├── databases.py        # 14 个数据库工具
│       ├── files.py            # 10 个文件工具
│       ├── groups_logs.py      # 5 个分组/日志工具
│       ├── hosts.py            # 17 个主机工具
│       ├── openresty_process.py# 7 个 OpenResty/进程工具
│       ├── runtimes.py         # 12 个运行环境工具
│       ├── settings.py         # 8 个设置工具
│       ├── toolbox.py          # 12 个工具箱工具
│       └── websites.py         # 25 个网站工具
├── tests/
│   └── test_panel_client.py    # PanelClient 测试（14 个用例）
├── docs/
│   ├── INDEX.md                # 开发文档索引
│   ├── api-manual.html         # 1Panel 官方 API 文档
│   └── api-swagger.json        # 完整 Swagger（603 端点）
├── README.md
├── LICENSE
├── .gitignore
└── .env.example
```

## 许可

MIT
