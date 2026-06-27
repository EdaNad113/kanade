"""Formatting helpers for mcp-1panel tools (mirrors Node.js tools/helpers.js)."""

from typing import Any, Callable, Dict, List, Optional, TypeVar

F = TypeVar("F", bound=Callable)


def safe(handler: F) -> F:
    """Wrap a handler so that exceptions become 'ERR: ...' strings."""
    import functools

    @functools.wraps(handler)
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except Exception as e:
            return f"ERR: {e}"

    return wrapper  # type: ignore


# ---------------------------------------------------------------------------
# Icons
# ---------------------------------------------------------------------------
def icon_green() -> str:
    return "\U0001f7e2"  # 🟢


def icon_red() -> str:
    return "\U0001f534"  # 🔴


def icon_lock() -> str:
    return "\U0001f512"  # 🔒


def icon_unlock() -> str:
    return "\U0001f513"  # 🔓


def icon_status(running: bool) -> str:
    return icon_green() if running else icon_red()


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------
def header(label: str, count: Optional[int] = None) -> str:
    if count is not None:
        return f"= {label} (共{count}个) ="
    return f"= {label} ="


def fmt_bool(v: Any) -> str:
    return icon_green() if v else icon_red()


def fmt_val(val: Any, max_len: int = 60) -> str:
    s = str(val)
    return s[:max_len] + "..." if len(s) > max_len else s


def fmt_obj(obj: Any, indent: str = "  ") -> List[str]:
    """Format a dict as key:value lines."""
    if not isinstance(obj, dict):
        return [f"{indent}{fmt_val(obj)}"]
    lines: List[str] = []
    for k, v in obj.items():
        lines.append(f"{indent}{k}: {fmt_val(v)}")
    return lines


def fmt_list(items: List[Any], template: str = "  {}", max_items: int = 50) -> List[str]:
    """Format a list with a template string per item."""
    lines: List[str] = []
    for item in (items or [])[:max_items]:
        if isinstance(template, str):
            lines.append(template.format(item))
        else:
            lines.append(str(item))
    if not items:
        lines.append("  (空)")
    return lines


def fmt_search(data: Dict[str, Any], label: str = "") -> tuple:
    """Parse a paginated search response into (header_lines, items)."""
    items = data.get("items", []) if isinstance(data, dict) else (data or [])
    total = data.get("total", 0) if isinstance(data, dict) else len(items)
    lines = [header(label, total)] if label else []
    return lines, items


def fmt_generic(data: Any, label: str = "") -> str:
    """Format any API response (dict, list, or scalar) into a string."""
    lines = [header(label)] if label else []
    if isinstance(data, dict):
        lines.extend(fmt_obj(data))
    elif isinstance(data, list):
        lines.extend(fmt_list(data))
    else:
        lines.append(f"  {fmt_val(data)}")
    return "\n".join(lines) if lines else "(空)"
