#!/usr/bin/env node

/**
 * mcp-1panel — Bootstrapper
 *
 * Automatically installs missing dependencies, then loads the real server.
 * This allows "node src/index.js" to work even without node_modules/.
 */

import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { existsSync } from "node:fs";

const pkgDir = dirname(fileURLToPath(import.meta.url)) + "/..";

// Walk up the node_modules chain like Node's own resolution, so this
// works in every install layout (npm project, npx cache, global) where
// dependencies are hoisted to a parent node_modules directory.
function findSdk(startDir) {
  let dir = startDir;
  for (;;) {
    const candidate = resolve(dir, "node_modules", "@modelcontextprotocol", "sdk");
    if (existsSync(candidate)) return candidate;
    const parent = dirname(dir);
    if (parent === dir) return null;
    dir = parent;
  }
}

let sdkReady = true;
if (!findSdk(pkgDir)) {
  sdkReady = false;
}

if (!sdkReady) {
  console.error("[mcp-1panel] node_modules/@modelcontextprotocol/sdk not found — running npm install...");
  try {
    execSync("npm install", {
      cwd: pkgDir,
      stdio: "inherit",
      env: { ...process.env, npm_config_fund: "false", npm_config_audit: "false" },
    });
    console.error("[mcp-1panel] Dependencies installed successfully");
  } catch (e) {
    console.error("[mcp-1panel] Failed to install dependencies:", e.message);
    process.exit(1);
  }
}

// Load and run the real MCP server
await import("./server.js");
