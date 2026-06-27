# kanade

个人 AI Agent 工具集仓库，存放各类 Agent 相关的工具组件。

## 目录结构

```
agent/
└── tools/
    ├── MCP/                  # MCP Server 工具
    │   ├── docs/             # 1Panel API 开发文档（swagger + HTML）
    │   ├── mcp-1panel/       # 1Panel 面板管理 MCP Server（Python 版, v0.2.0）
    │   └── npm/
    │       └── mcp-1panel/   # 1Panel 面板管理 MCP Server（Node.js 版, v0.1.0）
    ├── skills/               # Hermes Agent Skill 文件
    │   ├── qiuzhi-skill-creator/
    │   └── skill 模板/
    │
    └── 插件/                 # AstrBot 适配插件
        └── conversation_logs/   # 对话记录器 v2.6
```

| 组件 | 版本 | 语言 | 说明 |
|------|------|------|------|
| `mcp-1panel` (Python) | **v0.2.0** | Python | 199 工具 / 18 资源 / 16 领域模块 |
| `mcp-1panel` (Node.js) | v0.1.0 | Node.js | 199 工具 / 18 资源 / 18 模块 |
| `conversation_logger` | v2.6.0 | Python | AstrBot 对话记录插件 |

### mcp-1panel（Python 版）v0.2.0

- 199 个 MCP 工具 + 18 个 `panel://` 资源（资源复用工具 handler）
- 覆盖 18 个 1Panel API 模块，16 个领域模块
- 架构：`FastMCP` + 16 个 `register_tools(mcp, get_client, handlers)` 模块
- 资源通过 `resources.py` 映射复用工具 handler，不重复调用逻辑
- 测试覆盖：PanelClient 认证、HTTP 调用、错误处理（14 个用例）
- 安装：`pip install .` 或 `pip install -e .`
- 环境变量：`PANEL_HOST` + `PANEL_API_KEY`

### mcp-1panel（Node.js 版）v0.1.0

- 199 个 MCP 工具 + 18 个 `panel://` 资源（映射复用工具 handler）
- npm package `@kanade/mcp-1panel`
- 支持 stdio / SSE 双传输协议
- `api-proxy.js` 使用 Proxy 实现惰性初始化，错误不缓存（环境变量修复后即刻生效）
- `toolWithParams` 只标记无默认值的参数为 required
- 测试覆盖：12 个用例，无需 1Panel 环境即可运行

### skills/

Hermes Agent 的 Skill 定义（`.md` + 配套脚本/引用文件）：
- `qiuzhi-skill-creator/` — 个人 Skill 创建工具箱
- `skill 模板/` — 新建 Skill 的起点模板

### 插件/

基于 AstrBot Star API 开发的插件（Python），适用于 AstrBot >= 4.0.0：
- `conversation_logs/` — 对话记录器，全量捕获对话日志，附带日记生成 WebUI

## 版本管理约定

- `mcp-1panel` 双版本保持**功能同步**，版本号各自独立管理
- 功能模块按 `agent/tools/MCP/mcp-1panel/tools/` 下模块划分
- 新增工具后同步更新 README 和版本号
- 双版本改动需同步更新对应的测试文件
