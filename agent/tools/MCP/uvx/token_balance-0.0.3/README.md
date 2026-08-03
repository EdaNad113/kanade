# token_balance — 多厂商 Token 余额查询工具

一个独立的 Python 工具，用于查询各 AI 厂商/中转站的 Token 余额。
支持 CLI 与 **MCP Server**（Codex / Claude Desktop / Cursor / 1Panel 等
任意 MCP 客户端对话中直接查询）。已发布 PyPI：<https://pypi.org/project/token-balance/>

## 核心特性

- 内置 17 个平台预设，只需填 `api_key`（部分需 `base_url`）
- 任意自定义站点：`url` + `headers` + `result_template`（支持取值与公式）
- 并发查询、失败隔离、密钥自动脱敏
- 首次启动**自动生成**含全部平台的配置文件模板（粘贴即用）
- MCP：3 个工具 + 3 个 `token://` 资源，stdio / SSE / Streamable HTTP 三种传输

## 快速开始（CLI）

```bash
# 安装（或 uvx token-balance 免安装）
pip install token-balance

# 首次运行自动生成 config.yaml（含全部平台模板）→ 填密钥 → 再运行
token-balance

# 临时查询（不写配置文件）
token-balance query deepseek sk-xxxx
token-balance query https://api.example.com/v1 sk-xxxx
token-balance --json
```

## 内置平台

| 类型 | 平台 | 需要 | 余额单位 |
|---|---|---|---|
| `deepseek` | DeepSeek 深度求索 | api_key | CNY |
| `siliconflow` | 硅基流动 | api_key | CNY |
| `kimi` / `kimi-full` / `moonshot` | Kimi / Moonshot 月之暗面 | api_key | CNY |
| `openai` | OpenAI | api_key | USD |
| `chatanywhere` | ChatAnywhere | api_key | USD |
| `openrouter` | OpenRouter | api_key | USD |
| `onething` | 网心云 OneThing | api_key | CNY |
| `minimax` | MiniMax 海螺 | api_key | 套餐额度 |
| `aihubmix` | AIHubMix | api_key | CNY |
| `apimart` 系列 | APIMart | api_key | CNY / 积分 |
| `newapi` | NEW API 中转站 | base_url + api_key | 额度 |
| `oneapi` | One-API 自建 | base_url + api_key | 元 |

默认别名：`ds`=deepseek，`sc`/`硅基`=siliconflow，`ca`=chatanywhere，`new`/`中转`=newapi。
可用 `platform_aliases` 追加自定义别名。

## 配置文件

首次启动若找不到配置，会自动在目标位置生成模板（**包含全部平台**），
把 `在这里填你的密钥` 替换为真实 key 后重启即可。文件已存在时不会覆盖。

查找顺序：`--config` 参数 > `TOKEN_BALANCE_CONFIG` 环境变量 > 当前目录 `config.yaml`。

⚠️ MCP 部署时**必须**用 `TOKEN_BALANCE_CONFIG` 指定绝对路径（server 的
"当前目录"由客户端拉起时决定，不可依赖）。

### 如何添加更多厂商

三步，无需改代码：

```yaml
# 1. 编辑 config.yaml，在 services 下新增一项（内置平台见上方表格）
services:
  openrouter:                    # 服务名任意
    type: openrouter             # 平台类型
    api_key: "sk-or-xxxx"        # 或 env:OPENROUTER_API_KEY

  # 中转站类需要 base_url：
  newapi:
    type: newapi
    base_url: "http://172.17.0.1:3000"
    api_key: "sk-xxxx"
```

```bash
# 2. 保存；3. 重启 MCP 实例（或重新运行命令）
```

- 没有内置的平台：用 `type: custom` + `url`/`headers`/`result_template`，见下方「自定义站点」
- 临时试一个 key 不想写配置：`token-balance query <平台名|URL> <key>`

## MCP Server

### 工具与资源

| 工具 | 说明 |
|---|---|
| `list_services` | 列出配置中的服务与内置平台（无网络请求） |
| `query_balances` | 查询全部或指定服务的余额 |
| `query_endpoint` | 临时查询：平台名 / API 地址 / NewAPI 连接 JSON |

| 资源 | 说明 |
|---|---|
| `token://services` | 配置服务与平台列表 |
| `token://balances` | 全部服务余额快照 |
| `token://balance/{name}` | 单个服务余额 |

### 客户端注册（本机）

任意 JSON 格式客户端（Claude Desktop / Cursor / Windsurf / Hermes 等）
用同一段配置，放到各自配置入口：

```json
{
  "mcpServers": {
    "token-balance": {
      "command": "uvx",
      "args": ["--from", "token-balance", "token-balance-mcp"],
      "env": {
        "TOKEN_BALANCE_CONFIG": "/opt/1panel/mcp/token-balance/config.yaml"
      }
    }
  }
}
```

- ⚠️ `--from token-balance` 不能省（命令名 ≠ 包名，直接写 `token-balance-mcp` 会报 `No solution found`）
- 本机 Windows 示例：`TOKEN_BALANCE_CONFIG` 改为 `D:\...\config.yaml`，`env` 可加 `UV_DEFAULT_INDEX` 镜像

Codex（`~/.codex/config.toml`，TOML 格式）：

```toml
[mcp_servers.token-balance]
command = "uvx"
args = ["--from", "token-balance", "token-balance-mcp"]
env = { TOKEN_BALANCE_CONFIG = "D:\\tools\\small\\Codex\\codex\\work\\mcp\\config.yaml" }
```

### 1Panel 部署

1Panel 内置 MCP 管理用 **Supergateway（Node 容器）** 桥接 stdio → SSE。

⚠️ **导入配置后请确认「类型」为 `uvx`**：1Panel 导入 mcpServers JSON 时可能把
类型默认识别为 `npx`，而容器里没有 npm 包会导致启动失败（日志出现
`Child stderr: /bin/sh: uvx: not found` 即为此问题）。

**步骤：**

1. **宿主机建挂载目录**：
   ```bash
   mkdir -p /opt/1panel/mcp/token-balance
   ```

2. **创建实例**（1Panel → AI → MCP），按下面填：

   | 字段 | 值 |
   |---|---|
   | 名称 | `token-balance` |
   | 类型 | **`uvx`**（导入 JSON 后务必检查此项） |
   | 运行命令 | `uvx --from token-balance token-balance-mcp` |
   | 输出类型 | `sse`（或 `streamableHttp`） |
   | 环境变量 | `TOKEN_BALANCE_CONFIG=/opt/1panel/mcp/token-balance/config.yaml` |
   | 挂载 | 宿主机 `/opt/1panel/mcp/token-balance` → 容器 `/opt/1panel/mcp/token-balance` |
   | 端口 | 如 `10005`，开启外部访问 |

   或直接粘贴上方「客户端注册」的 JSON，**然后检查类型是否为 uvx**。

3. **首次启动自动生成模板**：server 会在挂载目录生成
   `/opt/1panel/mcp/token-balance/config.yaml`（宿主机同路径可见），
   用 1Panel「文件」打开填密钥。

4. **重启实例**，用面板给出的 SSE 地址连接：
   ```json
   { "mcpServers": { "token-balance": { "url": "http://你的IP:端口/token-balance" } } }
   ```

> 升级版本：改运行命令为 `uvx --from token-balance==X.Y.Z token-balance-mcp`
> （锁版本绕开 uvx 缓存），或容器内 `uv cache clean` 后重启。
> 容器内访问宿主机中转站用 `172.17.0.1` / `host.docker.internal`，不要用 `localhost`。

### 远程传输（SSE / HTTP）

```bash
token-balance-mcp --transport sse --host 0.0.0.0 --port 10003 --mount-path token-balance
# 客户端 url: http://你的IP:10003/token-balance/sse
```

`--transport http` 同理，url 为 `http://你的IP:端口/mcp`。

## 自定义站点

任意服务商都能接入：

```yaml
services:
  my_site:
    type: custom
    url: "https://api.example.com/v1/user/balance"
    method: GET
    headers:
      Authorization: "Bearer sk-xxxx"
    result_template: "我的站: {{data.balance}} 元"
    # 可选结构化字段（用于表格/JSON 输出）：
    currency: "CNY"
    total_template: "{{data.balance}}"
    remaining_template: "{{data.balance}}"
    raw_info_template: "备注: {{data.note}}"
```

模板语法：`{{data.balance}}` 取值（支持数组下标）；`{{round({data.quota}/500000*7.1, 2)}}`
公式计算；支持函数 abs/round/min/max/pow/sqrt/floor/ceil/log/exp 等与 `+ - * / %`。

## 安全提醒

- 密钥建议用 `env:环境变量名` 引用；输出与错误信息自动脱敏
- 配置文件在 `.gitignore` 中，避免密钥入库
- MCP server 查询只读；仅首次启动生成配置文件模板（已存在不覆盖）
- 远程暴露建议内网或反向代理鉴权

## 开发与发布

```bash
python -m unittest discover -s tests    # 80 个测试（本地 Mock，不访问外网）
uv build && uv publish                  # 发版（需 PyPI API Token）
```