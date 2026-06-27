/**
 * mcp-1panel — Databases 模块工具（14 个）
 */
import { tool, toolWithParams, fmtObj, fmtList } from "./helpers.js";
import { api } from "../api-proxy.js";

export const DATABASES_TOOLS = {

  panel_databases: tool("数据库列表 — 类型、版本", async () => {
    const [mysql, pg] = await Promise.all([
      api.get("/databases/db/list/mysql"),
      api.get("/databases/db/list/postgresql"),
    ]);
    const d = [...(mysql ?? []), ...(pg ?? [])];
    return fmtList("数据库", d, (db) => `${db.type ?? "?"}: ${db.name ?? "?"}  v${db.version ?? "?"}`);
  }),

  panel_mysql_status: tool("MySQL 运行状态 — 连接数、运行时间", async () => {
    const d = await api.post("/databases/status", {});
    return fmtObj("MySQL 状态", d);
  }),

  panel_mysql_variables: tool("MySQL 变量列表 — 重要配置参数", async () => {
    const d = await api.post("/databases/variables", {});
    return fmtObj("MySQL 变量", d);
  }),

  panel_redis_status: tool("Redis 运行状态 — 内存、连接数、命中率", async () => {
    const d = await api.post("/databases/redis/status", {});
    return fmtObj("Redis 状态", d);
  }),

  panel_redis_conf: tool("Redis 配置 — 当前配置参数", async () => {
    const d = await api.post("/databases/redis/conf", {});
    return fmtObj("Redis 配置", d);
  }),

  panel_redis_persistence: tool("Redis 持久化配置 — RDB/AOF 设置", async () => {
    const d = await api.post("/databases/redis/persistence/conf", {});
    return fmtObj("Redis 持久化", d);
  }),

  panel_db_list_by_type: toolWithParams("按类型列出数据库", async (args) => {
    const d = await api.get(`/databases/db/list/${args.type}`);
    return fmtList(`数据库 (${args.type})`, d, (db) => `${db.name ?? "?"}  v${db.version ?? "?"}  ${db.status ?? "?"}`);
  }, { type: { type: "string", default: "mysql" } }),

  panel_db_detail_by_name: toolWithParams("数据库详情 — 按名称查询", async (args) => {
    const d = await api.get(`/databases/db/${encodeURIComponent(args.name)}`);
    return fmtObj("数据库详情", d);
  }, { name: { type: "string", default: "" } }),

  panel_db_check: toolWithParams("检查数据库是否可连接", async (args) => {
    const d = await api.post("/databases/db/check", args);
    return fmtObj("数据库检查", d);
  }, { name: { type: "string", default: "" }, type: { type: "string", default: "mysql" } }),

  panel_db_base_info: toolWithParams("数据库基础信息 — 版本、大小", async (args) => {
    const d = await api.post("/databases/common/info", args);
    return fmtObj("数据库基础信息", d);
  }, { name: { type: "string", default: "" }, type: { type: "string", default: "mysql" } }),

  panel_db_conf_file: toolWithParams("数据库配置文件内容", async (args) => {
    const d = await api.post("/databases/common/load/file", args);
    return fmtObj("数据库配置", d, 200);
  }, { type: { type: "string", default: "mysql" } }),

  panel_mysql_collation: tool("MySQL 排序规则选项", async () => {
    const d = await api.post("/databases/format/options", {});
    return fmtList("排序规则选项", d, (o) => `${o.collation ?? "?"}  ${o.charset ?? ""}`);
  }),

  panel_mysql_remote: tool("MySQL 远程访问配置", async () => {
    const d = await api.post("/databases/remote", {});
    return fmtObj("MySQL 远程访问", d);
  }),

  panel_db_item: toolWithParams("按类型获取数据库项列表", async (args) => {
    const d = await api.get(`/databases/db/item/${args.type}`);
    return fmtList(`数据库项 (${args.type})`, d, (db) => `${db.name ?? "?"}  ${db.status ?? "?"}`);
  }, { type: { type: "string", default: "mysql" } }),

};
