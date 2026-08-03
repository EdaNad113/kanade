"""配置加载：读取 YAML 配置文件，合并内置平台预设。

配置文件格式（config.yaml）：

    timeout: 10          # 单个请求超时（秒）
    concurrency: 10      # 并发数

    platform_aliases:    # 可选：自定义平台别名（用于 query 命令匹配）
      deepseek: "ds,深度求索"
      siliconflow: "sc,硅基"

    # 可选：自定义输出模板（配置任一即启用模板输出模式）
    success_template: "🟢 **{{source_name}}**\n  💵 {{balance}} {{currency}}"
    error_template: "🔴 **{{source_name}}**\n  ❌ {{error}}"

    services:
      deepseek:
        type: deepseek
        api_key: "sk-xxx"             # 或 env:环境变量名
      my_site:
        type: custom
        url: "https://api.example.com/v1/user/balance"
        method: GET
        headers:
          Authorization: "Bearer sk-xxx"
        result_template: "我的站: {{data.balance}} 元"
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

import yaml

from .fetchers import BUILTIN_PLATFORMS, Service

DEFAULT_CONFIG_FILE = os.environ.get("TOKEN_BALANCE_CONFIG", "config.yaml")

# 首次启动自动生成的引导模板（包含全部内置平台）
CONFIG_TEMPLATE = """# ============================================================
# token-balance 配置文件（首次启动自动生成）
# 使用方法：
#   1. 保留你需要的平台，删掉不需要的
#   2. 把 "在这里填你的密钥" 替换为真实 API Key（或改成 env:环境变量名）
#   3. 保存后重启 MCP 实例 / 重新运行命令即可生效
# 平台类型与别名说明见 README「内置平台」
# ============================================================

timeout: 10
concurrency: 10

services:
  # ---- DeepSeek 深度求索（CNY） ----
  deepseek:
    type: deepseek
    api_key: "在这里填你的密钥"          # 或 env:DEEPSEEK_API_KEY

  # ---- 硅基流动（CNY，totalBalance 总余额含赠送） ----
  siliconflow:
    type: siliconflow
    api_key: "在这里填你的密钥"

  # ---- Kimi / Moonshot 月之暗面（CNY；kimi-full 显示现金+代金券明细） ----
  kimi:
    type: kimi-full
    api_key: "在这里填你的密钥"

  # ---- OpenAI（USD） ----
  openai:
    type: openai
    api_key: "在这里填你的密钥"

  # ---- ChatAnywhere（USD） ----
  chatanywhere:
    type: chatanywhere
    api_key: "在这里填你的密钥"

  # ---- OpenRouter（USD） ----
  openrouter:
    type: openrouter
    api_key: "在这里填你的密钥"

  # ---- 网心云 OneThing（CNY） ----
  onething:
    type: onething
    api_key: "在这里填你的密钥"

  # ---- MiniMax 海螺（编码套餐额度） ----
  minimax:
    type: minimax
    api_key: "在这里填你的密钥"

  # ---- AIHubMix（CNY，按 quota/500000*7.1 换算） ----
  aihubmix:
    type: aihubmix
    api_key: "在这里填你的密钥"

  # ---- APIMart（元；另有 apimart-full / apimart-credits / apimart-credits-full） ----
  apimart:
    type: apimart
    api_key: "在这里填你的密钥"

  # ---- NEW API 中转站（需 base_url；容器内访问宿主机用 172.17.0.1 或 host.docker.internal） ----
  # newapi:
  #   type: newapi
  #   base_url: "http://172.17.0.1:3000"
  #   api_key: "在这里填你的密钥"

  # ---- One-API 自建（需 base_url） ----
  # oneapi:
  #   type: oneapi
  #   base_url: "http://172.17.0.1:3000"
  #   api_key: "在这里填你的密钥"
"""


def ensure_config_file(path: str) -> bool:
    """配置文件不存在时自动生成引导模板（含占位密钥）。

    返回 True 表示本次创建了文件。文件已存在时不会覆盖（幂等）。
    """
    if os.path.exists(path):
        return False
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(CONFIG_TEMPLATE)
    return True


@dataclass
class AppConfig:
    timeout: float = 10.0
    concurrency: int = 10
    platform_aliases: Dict[str, str] = field(default_factory=dict)
    # 可选输出模板（配置任一即启用模板输出模式；与参考插件同名）
    success_template: str = ""
    error_template: str = ""
    header_template: str = ""
    separator_template: str = ""
    item_separator_template: str = ""
    section_separator_template: str = ""
    services: List[Service] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)   # 配置解析失败项
    path: str = ""


def resolve_secret(value: Any) -> str:
    """密钥解析：支持 env:VAR 语法从环境变量读取，避免明文写在配置文件里。"""
    s = str(value or "")
    if s.startswith("env:"):
        return os.environ.get(s[4:].strip(), "")
    return s


def service_from_dict(name: str, info: dict) -> Service:
    """从 YAML 配置项构造 Service（合并内置预设、解析 {api_key}/{base_url} 占位符）。"""
    svc_type = str(info.get("type") or "custom").lower()
    display_name = str(info.get("display_name") or "")
    api_key = resolve_secret(info.get("api_key"))
    base_url = str(info.get("base_url") or "")

    def fill_placeholders(text: str) -> str:
        return text.replace("{base_url}", base_url).replace("{api_key}", api_key)

    if svc_type == "custom":
        url = str(info.get("url") or "")
        if not url:
            raise ValueError(f"[{name}] custom 类型必须提供 url")
        headers = {str(k): fill_placeholders(str(v)) for k, v in (info.get("headers") or {}).items()}
        return Service(
            name=name,
            type="custom",
            api_key=api_key,
            base_url=base_url,
            url=fill_placeholders(url),
            method=str(info.get("method") or "GET").upper(),
            headers=headers,
            result_template=str(info.get("result_template") or "{{data}}"),
            display_name=display_name,
            currency=str(info.get("currency") or ""),
            currency_template=str(info.get("currency_template") or ""),
            total_template=str(info.get("total_template") or ""),
            remaining_template=str(info.get("remaining_template") or ""),
            used_template=str(info.get("used_template") or ""),
            raw_info_template=str(info.get("raw_info_template") or ""),
        )

    if svc_type not in BUILTIN_PLATFORMS:
        raise ValueError(
            f"[{name}] 未知类型 '{svc_type}'，可选: {', '.join(sorted(BUILTIN_PLATFORMS.keys()))}"
        )

    preset = BUILTIN_PLATFORMS[svc_type]
    if preset.get("requires_base_url") and not base_url:
        raise ValueError(f"[{name}] 类型 {svc_type} 需要填写 base_url（自建实例地址）")
    if not api_key:
        raise ValueError(f"[{name}] 缺少 api_key（可用 env:环境变量名 引用）")

    url = fill_placeholders(str(info.get("url") or preset["url"]))
    headers: Dict[str, str] = {}
    for k, v in (preset.get("headers") or {}).items():
        headers[str(k)] = fill_placeholders(str(v))
    for k, v in (info.get("headers") or {}).items():
        headers[str(k)] = fill_placeholders(str(v))

    template_keys = [
        "result_template",
        "currency_template",
        "total_template",
        "remaining_template",
        "used_template",
        "raw_info_template",
    ]
    fields: Dict[str, str] = {k: str(info.get(k) or preset.get(k) or "") for k in template_keys}
    if not fields["result_template"]:
        fields["result_template"] = "{{data}}"

    return Service(
        name=name,
        type=svc_type,
        api_key=api_key,
        base_url=base_url,
        url=url,
        method=str(info.get("method") or preset.get("method") or "GET").upper(),
        headers=headers,
        display_name=display_name or preset.get("display_name") or name,
        currency=str(info.get("currency") or preset.get("currency") or ""),
        currency_template=fields["currency_template"],
        result_template=fields["result_template"],
        total_template=fields["total_template"],
        remaining_template=fields["remaining_template"],
        used_template=fields["used_template"],
        raw_info_template=fields["raw_info_template"],
    )


def load_config(path: str) -> AppConfig:
    """加载配置文件；某一行配置失败不会影响其他行（记录到 errors）。"""
    with open(path, "r", encoding="utf-8-sig") as f:
        raw = yaml.safe_load(f) or {}

    cfg = AppConfig(
        timeout=float(raw.get("timeout", 10.0)),
        concurrency=int(raw.get("concurrency", 10)),
        path=path,
    )

    aliases = raw.get("platform_aliases") or {}
    if isinstance(aliases, dict):
        cfg.platform_aliases = {str(k): str(v) for k, v in aliases.items()}

    for key in (
        "success_template", "error_template", "header_template",
        "separator_template", "item_separator_template", "section_separator_template",
    ):
        value = raw.get(key)
        if value is not None:
            setattr(cfg, key, str(value))

    services = raw.get("services") or {}
    if not isinstance(services, dict):
        raise ValueError("services 必须是键值对（YAML 映射）")

    for name, info in services.items():
        if not isinstance(info, dict):
            cfg.errors.append(f"[{name}] 配置必须是映射（含 type/url 等字段）")
            continue
        try:
            cfg.services.append(service_from_dict(name, info))
        except Exception as e:  # noqa: BLE001
            cfg.errors.append(str(e))
    return cfg