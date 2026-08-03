"""各平台余额查询 Fetcher。

- 内置平台预设：只需提供 api_key（部分需要 base_url）
- 自定义站点：url + method + headers + result_template 完全由配置决定
- OpenAI / ChatAnywhere 走计费接口（subscription + usage）
- NEW API / One-API 走 /api/usage/token 或 /api/user/self
- 临时端点查询 query_by_url：OpenAI Billing → New API 自动降级
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

from .renderer import render_template

log = logging.getLogger("token_balance")


# ==================== 数据模型 ====================

@dataclass
class Service:
    """一个待查询的服务（已合并预设并解析占位符）。"""

    name: str
    type: str                      # 内置平台类型 或 custom
    api_key: str = ""
    base_url: str = ""
    url: str = ""
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    result_template: str = "{{data}}"
    display_name: str = ""
    currency: str = ""
    currency_template: str = ""
    total_template: str = ""
    remaining_template: str = ""
    used_template: str = ""
    raw_info_template: str = ""

    @property
    def label(self) -> str:
        return self.display_name or self.name


@dataclass
class BalanceResult:
    """统一的余额查询结果。"""

    name: str                      # 平台显示名
    currency: str = ""             # 币种：CNY / USD / 元 / 积分 / "" 等
    total: str = ""                # 总额
    used: str = ""                 # 已用
    remaining: str = ""            # 剩余（为空时视为与 total 相同）
    raw_info: str = ""             # 附加信息（赠送/充值/到期等）
    rendered: str = ""             # 模板渲染后的原始一行
    api_key_masked: str = ""       # 脱敏后的密钥（用于展示）
    ok: bool = True
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "currency": self.currency,
            "total": self.total,
            "remaining": self.remaining,
            "used": self.used,
            "raw_info": self.raw_info,
            "rendered": self.rendered,
            "api_key_masked": self.api_key_masked,
            "error": self.error,
        }

    # ---------- 可自定义输出模板（P2） ----------

    def render_success(self, template: str, api_key_masked: str = "") -> str:
        """按成功模板渲染；template 为空时使用内置默认块。"""
        if not template:
            return self._default_block()
        replacements = {
            "{{api_key}}": api_key_masked,
            "{{source_name}}": self.name,
            "{{currency}}": self.currency,
            "{{balance}}": self.remaining if str(self.remaining) != str(self.total) else self.total,
            "{{total_balance}}": self.total,
            "{{remaining_balance}}": self.remaining,
            "{{used_balance}}": self.used,
            "{{raw_info}}": self.raw_info,
            "{{smart_balance}}": self._smart_balance_lines(),
        }
        return _apply_template(template, replacements)

    def render_error(self, template: str, api_key_masked: str = "") -> str:
        """按失败模板渲染；template 为空时使用内置默认块。"""
        if not template:
            return f"🔴 **{self.name}**\n  ❌ {self.error}"
        replacements = {
            "{{api_key}}": api_key_masked,
            "{{source_name}}": self.name,
            "{{error}}": self.error,
        }
        return _apply_template(template, replacements)

    def _smart_balance_lines(self) -> str:
        """智能附加信息：总额/已用/备注，自动跳过无意义行。"""
        parts = []
        if self.remaining and str(self.remaining) != str(self.total):
            parts.append(f"  📈 总额: {self.total} {self.currency}".rstrip())
            if self.used and str(self.used) not in ("0", "0.0", "0.00", ""):
                parts.append(f"  📊 已用: {self.used} {self.currency}".rstrip())
        if self.raw_info:
            parts.append(f"  📝 {self.raw_info}")
        return "\n".join(parts)

    def _default_block(self) -> str:
        indent = "  "
        msg = f"🟢 **{self.name}**\n"
        if not self.remaining or str(self.remaining) == str(self.total):
            msg += f"{indent}💵 {self.total} {self.currency}".rstrip()
        else:
            msg += f"{indent}💵 余额: {self.remaining} {self.currency}".rstrip()
            msg += f"\n{indent}📈 总额: {self.total} {self.currency}".rstrip()
            if self.used and str(self.used) not in ("0", "0.0", "0.00", ""):
                msg += f"\n{indent}📊 已用: {self.used} {self.currency}".rstrip()
        if self.raw_info:
            msg += f"\n{indent}📝 {self.raw_info}"
        return msg


def _apply_template(template: str, replacements: Dict[str, str]) -> str:
    """模板变量替换：{{?变量}} 条件行（值为空/0 时删除整行）、\\n 转义。"""
    for key, value in replacements.items():
        cond_key = key.replace("{{", "{{?")
        if cond_key in template:
            if not str(value).strip() or str(value).strip() in ("0", "0.0", "0.00"):
                template = "\n".join(line for line in template.split("\n") if cond_key not in line)
    result = template
    for key, value in replacements.items():
        result = result.replace(key, str(value))
        result = result.replace(key.replace("{{", "{{?"), str(value))
    return result.replace("\\n", "\n")


# ==================== 通用工具 ====================

def mask_key(key: str) -> str:
    """脱敏 API Key：只保留前后几位；太短无法安全脱敏时全部隐藏。"""
    if not key:
        return ""
    if len(key) < 10:
        return "****"
    return f"{key[:6]}...{key[-4:]}"


def _sanitize(text: str, secret: str) -> str:
    """把文本中出现的密钥替换为掩码，避免错误信息泄露 token。"""
    if secret and secret in text:
        text = text.replace(secret, "****")
    return text


OPENAI_USAGE_DAYS = 1          # OpenAI 用量查询窗口（今天）
CHATANYWHERE_USAGE_DAYS = 99   # ChatAnywhere 用量查询窗口（99 天）


# ==================== 内置平台预设 ====================

def _moonshot_preset(result_template: str, raw_info_template: str) -> dict:
    return {
        "display_name": "Kimi/Moonshot",
        "aliases": ["moonshot", "moonshot.cn", "kimi", "月之暗面"],
        "url": "https://api.moonshot.cn/v1/users/me/balance",
        "headers": {"Accept": "application/json", "Authorization": "Bearer {api_key}"},
        "result_template": result_template,
        "currency": "CNY",
        "total_template": "{{data.available_balance}}",
        "remaining_template": "{{data.available_balance}}",
        "raw_info_template": raw_info_template,
    }


def _apimart_preset(key: str, *, full: bool = False, credits: bool = False) -> dict:
    """APIMart 四个变体共用一个工厂，仅余额字段/单位不同。"""
    if credits:
        total_t = "{{round({remain_credits}, 2)}}"
        used_t = "{{round({used_credits}, 2)}}"
        remaining_t = "{{round({remain_credits}, 2) - round({used_credits}, 2)}}"
        unit = "积分"
    else:
        total_t = "{{round({remain_balance}*7, 2)}}"
        used_t = "{{round({used_balance}*7, 2)}}"
        remaining_t = "{{round({remain_balance}*7, 2) - round({used_balance}*7, 2)}}"
        unit = "元"
    if full:
        result_template = f"APIMart: {total_t} {unit} (已用: {used_t} {unit})"
    else:
        result_template = f"APIMart: {remaining_t} {unit}"
    return {
        "display_name": "APIMart",
        "aliases": [key],
        "url": "https://aishuch.com/v1/user/balance",
        "headers": {"Accept": "application/json", "Authorization": "Bearer {api_key}"},
        "result_template": result_template,
        "currency": "积分" if credits else "CNY",
        "total_template": total_t,
        "used_template": used_t,
        "remaining_template": remaining_t,
    }


BUILTIN_PLATFORMS: Dict[str, dict] = {
    "deepseek": {
        "display_name": "DeepSeek",
        "aliases": ["deepseek", "ds", "深度求索"],
        "url": "https://api.deepseek.com/user/balance",
        "headers": {"Accept": "application/json", "Authorization": "Bearer {api_key}"},
        "result_template": "DeepSeek: {{balance_infos.0.total_balance}} 元",
        "currency": "CNY",
        "total_template": "{{balance_infos.0.total_balance}}",
        "remaining_template": "{{balance_infos.0.total_balance}}",
        "raw_info_template": "赠送: {{balance_infos.0.granted_balance}} 元 | 充值: {{balance_infos.0.topped_up_balance}} 元",
    },
    "siliconflow": {
        "display_name": "硅基流动",
        "aliases": ["siliconflow", "siliconcloud", "硅基", "硅基流动", "sc"],
        "url": "https://api.siliconflow.cn/v1/user/info",
        "headers": {"Authorization": "Bearer {api_key}", "Content-Type": "application/json"},
        # 硅基流动余额单位为人民币（元）：totalBalance 为总余额（含赠送），chargeBalance 为充值余额
        "result_template": "硅基流动: {{data.totalBalance}} 元",
        "currency": "CNY",
        "total_template": "{{data.totalBalance}}",
        "remaining_template": "{{data.totalBalance}}",
        "raw_info_template": "充值: {{data.chargeBalance}} 元（差额为赠送/活动额度）",
    },
    "moonshot": _moonshot_preset(
        "Kimi: {{data.available_balance}} 元",
        "现金: {{data.cash_balance}} 元 | 代金券: {{data.voucher_balance}} 元",
    ),
    "kimi": _moonshot_preset(  # 兼容旧配置的别名类型
        "Kimi: {{data.available_balance}} 元",
        "现金: {{data.cash_balance}} 元 | 代金券: {{data.voucher_balance}} 元",
    ),
    "kimi-full": _moonshot_preset(  # 更详细的显示
        "Kimi: {{data.available_balance}} 元 (现金: {{data.cash_balance}} 元, 代金券: {{data.voucher_balance}} 元)",
        "现金: {{data.cash_balance}} 元 | 代金券: {{data.voucher_balance}} 元",
    ),
    "openrouter": {
        "display_name": "OpenRouter",
        "aliases": ["openrouter", "or"],
        "url": "https://openrouter.ai/api/v1/credits",
        "headers": {"Authorization": "Bearer {api_key}"},
        "result_template": "OpenRouter: ${{data.total_credits}}",
        "currency": "USD",
        "total_template": "{{data.total_credits}}",
        "remaining_template": "{{data.total_credits}}",
        "raw_info_template": "已用: ${{data.total_usage}}",
    },
    "onething": {
        "display_name": "网心云 OneThing",
        "aliases": ["onething", "onethingai", "网心云", "网心"],
        "url": "https://api-lab.onethingai.com/api/v1/account/wallet/detail",
        "headers": {"Authorization": "Bearer {api_key}"},
        "result_template": "网心云: {{data.availableBalance}} 元",
        "currency": "CNY",
        "total_template": "{{data.availableBalance}}",
        "remaining_template": "{{data.availableBalance}}",
        "raw_info_template": "可用代金券: {{data.availableVoucherCash}} 元 | 累计消费: {{data.consumeCashTotal}} 元",
    },
    "minimax": {
        "display_name": "MiniMax",
        "aliases": ["minimax", "minimaxi", "海螺"],
        "url": "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains",
        "headers": {"Authorization": "Bearer {api_key}", "Content-Type": "application/json"},
        "result_template": "MiniMax: 剩余 {{round({model_remains.0.current_interval_total_count}-{model_remains.0.current_interval_usage_count})}}/{{model_remains.0.current_interval_total_count}} ({{round(({model_remains.0.current_interval_total_count}-{model_remains.0.current_interval_usage_count})/{model_remains.0.current_interval_total_count}*100, 1)}}%), 本周 {{round({model_remains.0.current_weekly_total_count}-{model_remains.0.current_weekly_usage_count})}}/{{model_remains.0.current_weekly_total_count}}",
    },
    "aihubmix": {
        "display_name": "AIHubMix",
        "aliases": ["aihubmix", "hubmix"],
        "url": "https://aihubmix.com/api/user/self",
        "headers": {"Accept": "application/json", "Authorization": "Bearer {api_key}"},
        "result_template": "AIHubMix: {{round({data.quota}/500000*7.1, 2)}} 元",
        "currency": "CNY",
        "total_template": "{{round({data.quota}/500000*7.1, 2)}}",
        "remaining_template": "{{round({data.quota}/500000*7.1, 2)}}",
    },
    "apimart": _apimart_preset("apimart"),
    "apimart-full": _apimart_preset("apimart-full", full=True),
    "apimart-credits": _apimart_preset("apimart-credits", credits=True),
    "apimart-credits-full": _apimart_preset("apimart-credits-full", full=True, credits=True),
    "openai": {
        "display_name": "OpenAI",
        "aliases": ["openai", "openai.com", "gpt", "chatgpt"],
        "url": "https://api.openai.com/v1",  # 特殊 Fetcher：subscription + usage
        "headers": {"Authorization": "Bearer {api_key}"},
        "result_template": "OpenAI: ${{hard_limit_usd}}",
    },
    "chatanywhere": {
        "display_name": "ChatAnywhere",
        "aliases": ["chatanywhere", "ca"],
        "url": "https://api.chatanywhere.com.cn/v1",  # 特殊 Fetcher：subscription + usage
        "headers": {"Authorization": "Bearer {api_key}"},
        "result_template": "ChatAnywhere: ${{hard_limit_usd}}",
    },
    "newapi": {
        "display_name": "NEW API",
        "aliases": ["newapi", "new", "new_api", "中转"],
        "url": "{base_url}/api/usage/token",  # 特殊 Fetcher，需 base_url
        "headers": {"Authorization": "Bearer {api_key}", "Accept": "application/json"},
        "result_template": "NEW API: 剩余 {{data.total_available}} (总额 {{data.total_granted}}, 已用 {{data.total_used}})",
        "requires_base_url": True,
    },
    "oneapi": {
        "display_name": "One-API",
        "aliases": ["oneapi", "one-api"],
        "url": "{base_url}/api/user/self",  # 需 base_url
        "headers": {"Authorization": "Bearer {api_key}"},
        "result_template": "{{data.email}}: {{data.balance}} 元",
        "currency": "元",
        "total_template": "{{data.balance}}",
        "remaining_template": "{{data.balance}}",
        "requires_base_url": True,
    },
}


# ==================== Fetcher 基类 ====================

class Fetcher:
    """单个服务查询器（模板型，适用于绝大多数平台）。"""

    def __init__(self, svc: Service) -> None:
        self.svc = svc

    async def fetch(self, session: aiohttp.ClientSession, timeout: float) -> BalanceResult:
        svc = self.svc
        if not svc.api_key:
            return BalanceResult(svc.label, error="未提供 API Key", ok=False)
        try:
            async with session.request(
                svc.method, svc.url, headers=svc.headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status != 200:
                    return BalanceResult(svc.label, error=f"HTTP {resp.status} {resp.reason or ''}".strip(), ok=False)
                try:
                    data = await resp.json()
                except Exception:
                    text = await resp.text()
                    return BalanceResult(
                        svc.label,
                        error=f"返回非 JSON(HTTP {resp.status}): {_sanitize(text, svc.api_key)[:200]}",
                        ok=False,
                    )
            return self._build_result(data)
        except asyncio.TimeoutError:
            return BalanceResult(svc.label, error="请求超时", ok=False)
        except aiohttp.ClientError as e:
            return BalanceResult(svc.label, error=f"网络错误: {e}", ok=False)
        except Exception as e:  # noqa: BLE001
            return BalanceResult(svc.label, error=f"异常: {type(e).__name__}: {e}", ok=False)

    def _build_result(self, data: Any) -> BalanceResult:
        svc = self.svc
        missing: List[str] = []

        def field_val(tmpl: str) -> str:
            if not tmpl:
                return ""
            v = render_template(tmpl, data)
            if v == "N/A":
                missing.append(tmpl)
                return ""
            return v

        rendered = render_template(svc.result_template or "{{data}}", data)
        currency = svc.currency or field_val(svc.currency_template)
        total = field_val(svc.total_template)
        remaining = field_val(svc.remaining_template)
        used = field_val(svc.used_template)
        raw_info = field_val(svc.raw_info_template)

        if not total and not remaining:
            detail = missing[0] if missing else (svc.result_template or "无")
            return BalanceResult(svc.label, error=f"未找到字段: {detail}", ok=False)

        return BalanceResult(
            name=svc.label,
            currency=currency,
            total=total,
            remaining=remaining or total,
            used=used,
            raw_info=raw_info,
            rendered=rendered,
        )


# ==================== 特殊平台 Fetcher ====================

class OpenAIBillingFetcher(Fetcher):
    """OpenAI / ChatAnywhere 计费接口：subscription + usage。"""

    def __init__(self, svc: Service, *, usage_days: int) -> None:
        super().__init__(svc)
        self.usage_days = usage_days

    async def fetch(self, session: aiohttp.ClientSession, timeout: float) -> BalanceResult:
        svc = self.svc
        if not svc.api_key:
            return BalanceResult(svc.label, error="未提供 API Key", ok=False)
        base = (svc.base_url or svc.url).rstrip("/")
        if "/v1" in base:
            base = base.split("/v1")[0]
        headers = {"Authorization": f"Bearer {svc.api_key}"}
        to = aiohttp.ClientTimeout(total=timeout)

        today = datetime.today()
        start = (today - timedelta(days=self.usage_days - 1)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        sub_url = f"{base}/v1/dashboard/billing/subscription"
        usage_url = f"{base}/v1/dashboard/billing/usage?start_date={start}&end_date={end}"

        try:
            async with session.get(sub_url, headers=headers, timeout=to) as resp:
                if resp.status != 200:
                    return BalanceResult(svc.label, error=f"HTTP {resp.status}（subscription 接口不可用）", ok=False)
                sub = await resp.json()
        except asyncio.TimeoutError:
            return BalanceResult(svc.label, error="请求超时", ok=False)
        except aiohttp.ClientError as e:
            return BalanceResult(svc.label, error=f"网络错误: {e}", ok=False)
        except Exception as e:  # noqa: BLE001
            return BalanceResult(svc.label, error=f"异常: {type(e).__name__}: {e}", ok=False)

        if isinstance(sub, list):
            sub = sub[0] if sub else {}
        if not isinstance(sub, dict):
            sub = {}

        total = float(sub.get("hard_limit_usd") or sub.get("soft_limit_usd") or 0)
        used = 0.0
        try:
            async with session.get(usage_url, headers=headers, timeout=to) as resp:
                if resp.status == 200:
                    usage = await resp.json()
                    used = float(usage.get("total_usage") or 0) / 100
        except Exception:  # noqa: BLE001
            pass

        remaining = total - used
        if total == 0 and used == 0:
            return BalanceResult(svc.label, error="无法获取余额信息 (API 不支持或返回为空)", ok=False)

        return BalanceResult(
            name=svc.label,
            currency="USD",
            total=f"{total:.2f}",
            used=f"{used:.2f}",
            remaining=f"{remaining:.2f}",
            raw_info=f"支付: {'是' if sub.get('has_payment_method') else '否'} | 到期: {sub.get('access_until', '无限制')}",
        )


class NewApiTokenFetcher(Fetcher):
    """NEW API / one-api 的 /api/usage/token 接口。"""

    async def fetch(self, session: aiohttp.ClientSession, timeout: float) -> BalanceResult:
        svc = self.svc
        if not svc.api_key:
            return BalanceResult(svc.label, error="未提供 API Key", ok=False)
        base = (svc.base_url or svc.url).rstrip("/")
        if not base:
            return BalanceResult(svc.label, error="缺少 base_url（NEW API 需要填写中转站地址）", ok=False)
        url = f"{base}/api/usage/token"
        headers = {"Authorization": f"Bearer {svc.api_key}", "Accept": "application/json"}
        to = aiohttp.ClientTimeout(total=timeout)

        try:
            async with session.get(url, headers=headers, timeout=to) as resp:
                try:
                    data = await resp.json()
                except Exception:
                    text = await resp.text()
                    return BalanceResult(
                        svc.label,
                        error=f"非 JSON 数据(HTTP {resp.status}): {_sanitize(text, svc.api_key)[:200]}",
                        ok=False,
                    )
        except asyncio.TimeoutError:
            return BalanceResult(svc.label, error="请求超时", ok=False)
        except aiohttp.ClientError as e:
            return BalanceResult(svc.label, error=f"网络错误: {e}", ok=False)
        except Exception as e:  # noqa: BLE001
            return BalanceResult(svc.label, error=f"异常: {type(e).__name__}: {e}", ok=False)

        code = data.get("code")
        ok = bool(data.get("success")) or code in (0, 200) or code is True
        if not ok or "data" not in data:
            msg = data.get("message") or data.get("error") or "接口返回错误"
            return BalanceResult(svc.label, error=str(msg), ok=False)

        d = data.get("data") or {}
        name = d.get("name") or svc.label
        expires_at = d.get("expires_at") or 0
        expires = "永不过期" if not expires_at else datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S")

        return BalanceResult(
            name=name,
            total=str(d.get("total_granted", 0)),
            used=str(d.get("total_used", 0)),
            remaining=str(d.get("total_available", 0)),
            raw_info=f"无限额度: {'是' if d.get('unlimited_quota') else '否'} | 到期: {expires}",
        )


# ==================== Fetcher 构建 ====================

_SPECIAL_BUILDERS: Dict[str, Any] = {
    "openai": lambda svc: OpenAIBillingFetcher(svc, usage_days=OPENAI_USAGE_DAYS),
    "chatanywhere": lambda svc: OpenAIBillingFetcher(svc, usage_days=CHATANYWHERE_USAGE_DAYS),
    "newapi": NewApiTokenFetcher,
}


def build_fetcher(svc: Service) -> Fetcher:
    """根据服务类型构建 Fetcher（特殊类型走映射表，其余走模板型）。"""
    builder = _SPECIAL_BUILDERS.get(svc.type)
    return builder(svc) if builder else Fetcher(svc)


# ==================== 查询入口 ====================

async def query_all(
    services: List[Service],
    timeout: float = 10.0,
    concurrency: int = 10,
    session: Optional[aiohttp.ClientSession] = None,
) -> List[BalanceResult]:
    """并发查询多个服务，单个失败不影响其他。

    session 为空时自建（每次调用新建连接）；MCP server 等常驻进程可传入
    复用的长连接 session 以减少握手开销。
    """
    sem = asyncio.Semaphore(max(1, int(concurrency)))

    async def run(svc: Service) -> BalanceResult:
        async with sem:
            try:
                result = await build_fetcher(svc).fetch(session, timeout)
            except Exception as e:  # noqa: BLE001
                result = BalanceResult(svc.label, error=f"异常: {type(e).__name__}: {e}", ok=False)
            result.api_key_masked = mask_key(svc.api_key)
            return result

    async def run_all():
        return await asyncio.gather(*(run(s) for s in services), return_exceptions=True)

    if session is not None:
        responses = await run_all()
    else:
        async with aiohttp.ClientSession() as session:
            responses = await run_all()

    results: List[BalanceResult] = []
    for r in responses:
        if isinstance(r, BalanceResult):
            results.append(r)
        elif isinstance(r, Exception):
            results.append(BalanceResult("未知服务", error=f"异常: {r}", ok=False))
    return results


async def query_by_url(
    session: aiohttp.ClientSession,
    url: str,
    api_key: str,
    timeout: float = 10.0,
) -> BalanceResult:
    """临时查询：自动识别端点格式。

    优先尝试 OpenAI Billing API（/v1/dashboard/billing/subscription + /usage），
    失败后降级尝试 New API 格式（/api/usage/token）。
    传入地址以 /v1 结尾时，两条路径都会去掉 /v1 再拼接，避免拼出 /v1/api/usage/token。
    """
    if not api_key:
        return BalanceResult("自定义端点", error="未提供 API Key", ok=False)

    base = url.rstrip("/")
    prefix = base.split("/v1")[0] if "/v1" in base else base

    # 1) OpenAI Billing
    openai_svc = Service(
        name="自定义端点", type="openai", api_key=api_key,
        url=prefix, display_name="OpenAI 兼容端点",
    )
    openai_result = await OpenAIBillingFetcher(openai_svc, usage_days=OPENAI_USAGE_DAYS).fetch(session, timeout)
    if openai_result.ok:
        openai_result.raw_info = f"{base} | {openai_result.raw_info}"
        openai_result.api_key_masked = mask_key(api_key)
        return openai_result

    # 2) New API /api/usage/token
    newapi_svc = Service(
        name="自定义端点", type="newapi", api_key=api_key,
        base_url=prefix, display_name="NEW API",
    )
    newapi_result = await NewApiTokenFetcher(newapi_svc).fetch(session, timeout)
    if newapi_result.ok:
        newapi_result.raw_info = f"{base} | {newapi_result.raw_info}"
        newapi_result.api_key_masked = mask_key(api_key)
        return newapi_result

    return BalanceResult(
        "自定义端点",
        error=f"无法识别端点格式: {base}（OpenAI Billing: {openai_result.error}；New API: {newapi_result.error}）",
        ok=False,
    )