/**
 * mcp-1panel — Tool module aggregator
 *
 * Imports all per-module tool definitions and merges them into one map.
 */
import { AI_TOOLS } from "./ai.js";
import { APPS_TOOLS } from "./apps.js";
import { BACKUPS_TOOLS } from "./backups.js";
import { CONTAINERS_TOOLS } from "./containers.js";
import { CORE_TOOLS } from "./core.js";
import { CRONJOBS_TOOLS } from "./cronjobs.js";
import { DASHBOARD_TOOLS } from "./dashboard.js";
import { DATABASES_TOOLS } from "./databases.js";
import { FILES_TOOLS } from "./files.js";
import { GROUPS_TOOLS, LOGS_TOOLS } from "./groups-logs.js";
import { HOSTS_TOOLS } from "./hosts.js";
import { OPENRESTY_TOOLS, PROCESS_TOOLS } from "./openresty-process.js";
import { RUNTIMES_TOOLS } from "./runtimes.js";
import { SETTINGS_TOOLS } from "./settings.js";
import { TOOLBOX_TOOLS } from "./toolbox.js";
import { WEBSITES_TOOLS } from "./websites.js";

export const ALL_TOOLS = {
  ...AI_TOOLS,
  ...APPS_TOOLS,
  ...BACKUPS_TOOLS,
  ...CONTAINERS_TOOLS,
  ...CORE_TOOLS,
  ...CRONJOBS_TOOLS,
  ...DASHBOARD_TOOLS,
  ...DATABASES_TOOLS,
  ...FILES_TOOLS,
  ...GROUPS_TOOLS,
  ...HOSTS_TOOLS,
  ...LOGS_TOOLS,
  ...OPENRESTY_TOOLS,
  ...PROCESS_TOOLS,
  ...RUNTIMES_TOOLS,
  ...SETTINGS_TOOLS,
  ...TOOLBOX_TOOLS,
  ...WEBSITES_TOOLS,
};
