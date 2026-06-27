/**
 * mcp-1panel — Containers 模块工具（22 个）
 */
import { tool, toolWithParams, fmtObj, fmtList, fmtSearch, statusIcon, fmtBool } from "./helpers.js";
import { api } from "../api-proxy.js";

export const CONTAINERS_TOOLS = {

  panel_containers: tool("Docker 容器列表 — 名称、镜像、状态", async () => {
    const d = await api.post("/containers/list", {});
    return fmtList("Docker 容器", d, (c) => `${statusIcon(c.state)} ${c.name ?? "?"}  ${c.image ?? "?"}  [${c.state ?? "?"}]`);
  }),

  panel_images: tool("Docker 镜像列表 — 仓库标签、大小", async () => {
    const d = await api.get("/containers/image/all");
    return fmtList("Docker 镜像", d, (img) => `${img.repoTag ?? "?"}  ${img.size ?? "?"}`);
  }),

  panel_compose: tool("Docker Compose 项目列表", async () => {
    const d = await api.post("/containers/compose/search", { page: 1, pageSize: 50 });
    return fmtSearch("Compose 项目", d, (c) => `${c.name ?? "?"}  ${c.status ?? "?"}`);
  }),

  panel_networks: tool("Docker 网络列表", async () => {
    const d = await api.get("/containers/network");
    return fmtList("Docker 网络", d, (n) => `${n.name ?? n.option ?? "?"}  ${n.driver ?? ""}  ${n.attachable ? "🔗" : ""}`);
  }),

  panel_volumes: tool("Docker 存储卷列表 — 名称、驱动、挂载点", async () => {
    const d = await api.get("/containers/volume");
    return fmtList("Docker 存储卷", d, (v) => `${v.name ?? "?"}  ${v.driver ?? "?"}  ${v.mountPoint ?? ""}`);
  }),

  panel_image_repos: tool("Docker 镜像仓库列表", async () => {
    const d = await api.get("/containers/repo");
    return fmtList("Docker 镜像仓库", d, (r) => `${r.name ?? "?"}  ${r.protocol ?? "?"}  ${r.downloadUrl ?? ""}`);
  }),

  panel_docker_status: tool("Docker 守护进程状态 — 运行状态、版本", async () => {
    const d = await api.get("/containers/docker/status");
    return fmtObj("Docker 状态", d);
  }),

  panel_compose_templates: tool("Docker Compose 模板列表", async () => {
    const d = await api.get("/containers/template");
    return fmtList("Compose 模板", d, (t) => `${t.name ?? "?"}  ${t.description ?? ""}`);
  }),

  panel_processes: tool("端口监听列表 — 协议、端口、进程名、PID", async () => {
    const d = await api.get("/containers/list/stats");
    return fmtList("监听端口", d?.slice(0, 50) ?? [], (p) => `${p.protocol ?? "?"} ${p.port ?? "?"} -> ${p.processName ?? "?"} (PID ${p.pid ?? "?"})`);
  }),

  panel_docker_daemon: tool("Docker 守护进程配置 (daemon.json)", async () => {
    const d = await api.get("/containers/daemonjson");
    return fmtObj("Docker daemon.json", d);
  }),

  panel_docker_daemon_file: tool("Docker daemon.json 文件内容", async () => {
    const d = await api.get("/containers/daemonjson/file");
    return typeof d === "string" ? `= daemon.json =\n${d}` : fmtObj("daemon.json", d);
  }),

  panel_container_info: toolWithParams("容器详情 — 名称、配置、挂载", async (args) => {
    const d = await api.post("/containers/info", { id: args.id, name: args.name });
    return fmtObj("容器详情", d);
  }, { id: { type: "string", default: "" }, name: { type: "string", default: "" } }),

  panel_container_inspect: toolWithParams("容器 Inspect 信息 — 完整的 JSON 配置", async (args) => {
    const d = await api.post("/containers/inspect", { id: args.id });
    return fmtObj("容器 Inspect", d);
  }, { id: { type: "string", default: "" } }),

  panel_container_stats: toolWithParams("容器资源统计 — CPU/内存/网络", async (args) => {
    const d = await api.post("/containers/item/stats", { id: args.id });
    return fmtObj("容器统计", d);
  }, { id: { type: "string", default: "" } }),

  panel_container_limits: tool("Docker 容器资源限制配置", async () => {
    const d = await api.get("/containers/limit");
    return fmtObj("容器限制", d);
  }),

  panel_container_status: tool("Docker 容器状态概览 — 运行/停止计数", async () => {
    const d = await api.get("/containers/status");
    return fmtObj("容器状态", d);
  }),

  panel_containers_by_image: toolWithParams("按镜像查找容器", async (args) => {
    const d = await api.post("/containers/list/byimage", { imageName: args.image });
    return fmtList("匹配容器", d, (c) => `${c.name ?? "?"}  ${c.state ?? "?"}  ${c.image ?? "?"}`);
  }, { image: { type: "string", default: "" } }),

  panel_compose_env: toolWithParams("Compose 项目环境变量", async (args) => {
    const d = await api.post("/containers/compose/env", { id: args.id });
    return fmtObj("Compose 环境变量", d);
  }, { id: { type: "number", default: 0 } }),

  panel_repo_status: toolWithParams("镜像仓库连通性检查", async (args) => {
    const d = await api.post("/containers/repo/status", { id: args.id });
    return fmtObj("仓库状态", d);
  }, { id: { type: "number", default: 0 } }),

  panel_container_logs: tool("Docker 容器日志概览", async () => {
    try {
      const d = await api.get("/containers/search/log");
      return typeof d === "string" ? `= 容器日志 =\n${d.slice(0, 3000)}` : fmtObj("容器日志", d);
    } catch (e) {
      return `= 容器日志 =\n  无法获取日志: ${e.message}`;
    }
  }),

  panel_container_users: tool("容器用户列表 — UID/GID 映射", async () => {
    const d = await api.post("/containers/users", {});
    return fmtList("容器用户", d, (u) => `${u.name ?? "?"}  UID=${u.uid ?? "?"}  GID=${u.gid ?? "?"}`);
  }),

  panel_image_options: tool("Docker 镜像仓库选项 — 支持的加速器", async () => {
    const d = await api.get("/containers/image");
    return fmtObj("镜像选项", d);
  }),

};
