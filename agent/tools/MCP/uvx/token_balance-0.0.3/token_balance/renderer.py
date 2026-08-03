"""结果模板渲染：{{path}} 取值、{{expr({path})}} 公式计算。

语法与 astrbot_plugin_balance 保持一致：
- {{data.balance}}                         取 JSON 路径
- {{round({data.quota}/500000*7.1, 2)}}    公式计算（内层 {path} 先替换成实际值）
- 支持函数：abs / round / min / max / pow / sqrt / floor / ceil / log / log10
             / exp / sin / cos / tan / pi / e
- 支持运算符：+ - * / %（如 50% 等价于 50/100）
"""

from __future__ import annotations

import math
import re
from typing import Any, Match

_EXPR_PATTERN = re.compile(r"\{\{(.*?)\}\}")     # 双层大括号 {{...}}
_PATH_PATTERN = re.compile(r"\{([^{}]+)\}")      # 单层大括号 {path}

SAFE_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "pow": pow,
    "sqrt": math.sqrt,
    "floor": math.floor,
    "ceil": math.ceil,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
}


def get_by_path(data: Any, path: str) -> Any:
    """按点分路径取值，支持列表下标，如 balance_infos.0.total_balance。"""
    current = data
    for part in str(path).split("."):
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError, TypeError):
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def eval_expr(expr: str) -> Any:
    """安全计算数学表达式（不暴露内置函数，无属性访问）。"""
    try:
        expr = expr.replace("%", "/100")
        value = eval(expr, {"__builtins__": {}}, dict(SAFE_FUNCS))
    except Exception:
        return "N/A"
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return round(value, 2)
    return value


def _to_number(value: Any) -> Any:
    """字符串数字转为 int/float，方便参与公式计算。"""
    if isinstance(value, str):
        cleaned = re.sub(r"[^\d.\-]", "", value)
        if cleaned:
            return float(cleaned) if "." in cleaned else int(cleaned)
    return value


def render_template(template: str, data: Any) -> str:
    """渲染模板，只处理双层大括号 {{...}}，内层单层大括号 {path} 表示 JSON 路径。"""

    def replace_path(match: Match) -> str:
        value = _to_number(get_by_path(data, match.group(1)))
        return "N/A" if value is None else str(value)

    def process(match: Match) -> str:
        inner = match.group(1)
        if _PATH_PATTERN.search(inner):
            # 含内层 {path}：先取值再计算表达式
            expr = _PATH_PATTERN.sub(replace_path, inner)
            return str(eval_expr(expr))
        # 简单取值
        value = get_by_path(data, inner)
        if value is None:
            return "N/A"
        if isinstance(value, float) and not value.is_integer():
            return f"{value:.2f}"
        return str(value)

    return _EXPR_PATTERN.sub(process, template)