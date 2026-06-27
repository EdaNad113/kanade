"""MCP tools for 1Panel file management — browse, inspect, and manage files."""

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
    """Register all file-management MCP tools."""

    # ------------------------------------------------------------------ #
    # 1. panel_files — browse directory
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_files(path: str = "/") -> str:
        """浏览服务器文件目录 — 列出路径下的文件和文件夹"""
        p = get_client()
        data = p.post("/files/search", {
            "page": 1, "pageSize": 50,
            "path": path, "expand": False,
            "sortBy": "name", "asc": True,
        })
        items = data.get("items", []) if isinstance(data, dict) else (data or [])
        lines = [header(f"文件: {path}", len(items))]
        for f in items[:50]:
            icon = "\U0001f4c1" if f.get("isDir") else "\U0001f4c4"
            name = f.get("name", "?")
            size = f.get("size", "")
            mod = f.get("modTime", f.get("modifyTime", ""))
            lines.append(f"  {icon} {fmt_val(name)}  {fmt_val(size)}  {fmt_val(mod)}")
        if not items:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # 2. panel_file_content — read file content
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_file_content(path: str = "/") -> str:
        """文件内容预览 — 查看文本文件内容"""
        p = get_client()
        data = p.post("/files/content", {"path": path})
        lines = [header(f"文件内容: {path}")]
        if isinstance(data, dict):
            content = data.get("content", data.get("text", ""))
            if content:
                for line in str(content).split("\n")[:200]:
                    lines.append(f"  {line}")
            else:
                lines.extend(fmt_obj(data))
        elif isinstance(data, str):
            for line in data.split("\n")[:200]:
                lines.append(f"  {line}")
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # 3. panel_file_size — file/dir size
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_file_size(path: str = "/") -> str:
        """文件/目录大小 — 查询路径所占用的磁盘空间"""
        p = get_client()
        data = p.post("/files/tree/size", {"path": path})
        lines = [header(f"文件大小: {path}")]
        if isinstance(data, dict):
            size = data.get("size", data.get("total", "?"))
            count = data.get("count", data.get("fileCount", ""))
            lines.append(f"  大小: {fmt_val(size)}")
            if count:
                lines.append(f"  文件数: {count}")
        elif isinstance(data, (int, float)):
            lines.append(f"  大小: {data}")
        else:
            lines.append(f"  {fmt_val(data)}")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # 4. panel_file_check — check existence
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_file_check(path: str = "/") -> str:
        """检查文件是否存在 — 验证路径有效性"""
        p = get_client()
        data = p.post("/files/tree/check", {"path": path})
        lines = [header(f"检查路径: {path}")]
        if isinstance(data, dict):
            ok = data.get("exist", data.get("exists", False))
            icon = icon_green() if ok else icon_red()
            lines.append(f"  {icon} {'存在' if ok else '不存在'}")
            for k, v in data.items():
                if k not in ("exist", "exists"):
                    lines.append(f"  {k}: {fmt_val(v)}")
        else:
            st = icon_green() if data else icon_red()
            lines.append(f"  {st} {data}")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # 5. panel_favorites — list favorites
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_favorites() -> str:
        """文件收藏夹列表 — 已收藏的文件/目录"""
        p = get_client()
        data = p.get("/files/favorites")
        lines = [header("文件收藏夹")]
        if isinstance(data, list):
            for fav in data:
                name = fav.get("name", fav.get("path", "?"))
                fpath = fav.get("path", "")
                lines.append(f"  \u2b50 {fmt_val(name)}  [{fmt_val(fpath)}]")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # 6. panel_recycle_bin — list recycle bin
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_recycle_bin() -> str:
        """回收站文件列表 — 已删除但可恢复的文件"""
        p = get_client()
        data = p.get("/files/recycle/bin")
        lines = [header("回收站")]
        if isinstance(data, list):
            for item in data:
                name = item.get("name", item.get("fileName", "?"))
                old = item.get("oldName", item.get("originalPath", ""))
                deleted_at = item.get("deleteAt", item.get("deleteTime", ""))
                lines.append(f"  \U0001f5d1 {fmt_val(name)}  \u2190 {fmt_val(old)}  {fmt_val(deleted_at)}")
        elif isinstance(data, dict):
            lines.extend(fmt_obj(data))
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # 7. panel_recycle_status — recycle bin status
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_recycle_status() -> str:
        """回收站状态 — 是否启用回收站功能"""
        p = get_client()
        data = p.get("/files/recycle/status")
        lines = [header("回收站状态")]
        if isinstance(data, dict):
            enabled = data.get("enable", data.get("enabled", data.get("status", False)))
            lines.append(f"  {'\U0001f7e2 已启用' if enabled else '\U0001f534 已禁用'}")
            for k, v in data.items():
                if k not in ("enable", "enabled", "status"):
                    lines.append(f"  {k}: {fmt_val(v)}")
        elif isinstance(data, bool):
            lines.append(f"  {icon_green() if data else icon_red()} {'已启用' if data else '已禁用'}")
        else:
            lines.append(f"  {fmt_val(data)}")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # 8. panel_file_tree — directory tree
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_file_tree(path: str = "/") -> str:
        """文件目录树 — 显示目录层级结构"""
        p = get_client()
        data = p.post("/files/tree", {"path": path, "expand": True})
        lines = [header(f"目录树: {path}")]
        def walk(node, depth=0):
            prefix = "  " * depth
            name = node.get("name", node.get("path", "?"))
            is_dir = node.get("isDir", node.get("isDirectory", False))
            icon = "\U0001f4c1" if is_dir else "\U0001f4c4"
            lines.append(f"  {prefix}{icon} {fmt_val(name)}")
            children = node.get("children", node.get("items", []))
            if children:
                for child in children[:30]:
                    walk(child, depth + 1)
        if isinstance(data, list):
            for node in data[:20]:
                walk(node)
        elif isinstance(data, dict):
            walk(data)
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # 9. panel_file_remarks — file remarks
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_file_remarks(path: str = "/") -> str:
        """文件备注信息 — 查看或获取文件备注"""
        p = get_client()
        data = p.post("/files/remarks", {"path": path})
        lines = [header(f"文件备注: {path}")]
        if isinstance(data, dict):
            remark = data.get("remark", data.get("remarks", data.get("content", "")))
            if remark:
                lines.append(f"  {fmt_val(remark)}")
            else:
                lines.extend(fmt_obj(data))
        elif isinstance(data, str):
            lines.append(f"  {data}")
        else:
            lines.append(f"  {fmt_val(data)}")
        if not data:
            lines.append("  (空)")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # 10. panel_file_batch_check — batch file existence check
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def panel_file_batch_check(paths: str) -> str:
        """批量检查文件是否存在 — paths 为逗号分隔的路径字符串"""
        p = get_client()
        path_list = [p.strip() for p in paths.split(",") if p.strip()]
        data = p.post("/files/tree/batch/check", {"paths": path_list})
        lines = [header("批量文件检查", len(path_list))]
        if isinstance(data, dict):
            results = data.get("results", data.get("items", data.get("data", [])))
            if isinstance(results, list):
                for r in results:
                    rpath = r.get("path", "?")
                    ok = r.get("exist", r.get("exists", False))
                    icon = icon_green() if ok else icon_red()
                    lines.append(f"  {icon} {fmt_val(rpath)}")
            else:
                for k, v in data.items():
                    ok = bool(v)
                    icon = icon_green() if ok else icon_red()
                    lines.append(f"  {icon} {fmt_val(k)}: {v}")
        elif isinstance(data, list):
            for r in data:
                rpath = r.get("path", "?")
                ok = r.get("exist", r.get("exists", False))
                icon = icon_green() if ok else icon_red()
                lines.append(f"  {icon} {fmt_val(rpath)}")
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
