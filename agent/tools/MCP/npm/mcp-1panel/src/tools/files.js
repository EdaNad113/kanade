/**
 * mcp-1panel — Files 模块工具（10 个）
 */
import { tool, toolWithParams, fmtObj, fmtList } from "./helpers.js";
import { api } from "../api-proxy.js";

export const FILES_TOOLS = {

  panel_files: tool("浏览服务器文件目录", async (args) => {
    const path = args.path ?? "/";
    let d;
    try {
      d = await api.post("/files/search", { page: 1, pageSize: 50, path, expand: false, sortBy: "name", asc: true });
    } catch (e) {
      // expand/sortBy might not be supported on older API versions — retry without them
      d = await api.post("/files/search", { page: 1, pageSize: 50, path });
    }
    const items = d.items ?? [];
    return fmtList(`文件: ${path}`, items.slice(0, 50), (f) =>
      `${f.isDir ? "📁" : "📄"} ${f.name ?? "?"}  ${f.size ?? "?"}  ${f.mode ?? ""}`
    );
  }, { path: { type: "string", default: "/" } }),

  panel_file_content: toolWithParams("文件内容预览", async (args) => {
    const d = await api.post("/files/content", { path: args.path });
    return typeof d === "string" ? `= ${args.path} =\n${d.slice(0, 3000)}` : fmtObj("文件内容", d, 200);
  }, { path: { type: "string", default: "/" } }),

  panel_file_size: toolWithParams("文件/目录大小", async (args) => {
    const d = await api.post("/files/size", { path: args.path });
    return `= 文件大小 =\n  ${args.path}: ${String(d ?? "?").slice(0, 40)}`;
  }, { path: { type: "string", default: "/" } }),

  panel_file_check: toolWithParams("检查文件是否存在", async (args) => {
    const d = await api.post("/files/check", { path: args.path });
    return `= 文件检查 =\n  ${args.path}: ${d?.exist ?? d?.exists ?? d ? "存在 ✅" : "不存在 ❌"}`;
  }, { path: { type: "string", default: "/" } }),

  panel_favorites: tool("文件收藏夹列表", async () => {
    const d = await api.post("/files/favorite/search", { page: 1, pageSize: 50 });
    const items = d.items ?? d ?? [];
    return fmtList("收藏夹", Array.isArray(items) ? items : [], (f) => `${f.name ?? "?"}  ${f.path ?? ""}`);
  }),

  panel_recycle_bin: tool("回收站文件列表", async () => {
    const d = await api.post("/files/recycle/search", { page: 1, pageSize: 50 });
    const items = d.items ?? [];
    return fmtList("回收站", items, (f) => `${f.name ?? "?"}  删除时间: ${f.deleteTime ?? "?"}  大小: ${f.size ?? "?"}`);
  }),

  panel_recycle_status: tool("回收站状态 — 是否启用", async () => {
    const d = await api.get("/files/recycle/status");
    return fmtObj("回收站状态", d);
  }),

  panel_file_tree: toolWithParams("文件目录树", async (args) => {
    const d = await api.post("/files/tree", { path: args.path });
    return fmtList("文件树", Array.isArray(d) ? d.slice(0, 50) : [], (f) => {
      const name = f.name ?? f.path ?? "?";
      return `${f.isDir ? "📁" : "📄"} ${name}`;
    });
  }, { path: { type: "string", default: "/" } }),

  panel_file_remarks: toolWithParams("文件备注信息", async (args) => {
    const d = await api.post("/files/remarks", { paths: [args.path] });
    return fmtObj("文件备注", d);
  }, { path: { type: "string", default: "/" } }),

  panel_file_batch_check: toolWithParams("批量检查文件是否存在", async (args) => {
    const d = await api.post("/files/batch/check", { paths: Array.isArray(args.paths) ? args.paths : [args.paths] });
    return fmtObj("批量检查结果", d);
  }, { paths: { type: "string", default: "" } }),

};
