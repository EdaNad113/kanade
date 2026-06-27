/**
 * mcp-1panel — Tool helpers & formatters
 *
 * Shared utilities that keep each tool definition to 1-3 lines.
 */

/**
 * Safely wrap an async handler so every tool catches its own errors.
 */
export function safe(handler) {
  return async (...args) => {
    try {
      const r = await handler(...args);
      return r;
    } catch (e) {
      return `ERR: ${e.message}`;
    }
  };
}

/**
 * Create a tool definition object with error-safe handler.
 */
export function tool(desc, handler, schema = {}) {
  return {
    description: desc,
    inputSchema: { type: "object", properties: schema, required: [] },
    handler: safe(handler),
  };
}

/**
 * Create a tool that requires 1+ string params.
 */
export function toolWithParams(desc, handler, schema) {
  if (!schema || !Object.keys(schema).length) {
    // No params needed — treat as regular tool
    return tool(desc, handler);
  }
  // Only mark params without a 'default' as required
  const required = Object.entries(schema)
    .filter(([_, v]) => !("default" in v))
    .map(([k]) => k);
  return {
    description: desc,
    inputSchema: { type: "object", properties: schema, required },
    handler: safe(handler),
  };
}

/**
 * Format an object as a titled key:value block.
 */
export function fmtObj(title, obj, maxLen = 60) {
  if (obj == null || typeof obj !== "object") {
    return `= ${title} =\n  ${String(obj ?? "?")}`;
  }
  const lines = [`= ${title} =`];
  for (const [k, v] of Object.entries(obj)) {
    lines.push(`  ${k}: ${String(v ?? "?").slice(0, maxLen)}`);
  }
  return lines.join("\n");
}

/**
 * Format an array of items using a per-item formatter.
 */
export function fmtList(title, items, fn) {
  const lines = [`= ${title} =`];
  for (const item of items ?? []) lines.push(`  ${fn(item)}`);
  if (!items?.length) lines.push("  (空)");
  return lines.join("\n");
}

/**
 * Format a paginated search result.
 */
export function fmtSearch(title, result, fn) {
  const items = result?.items ?? [];
  const total = result?.total ?? 0;
  const lines = [`= ${title} (共${total}个) =`];
  for (const item of items) lines.push(`  ${fn(item)}`);
  if (!items.length) lines.push("  (空)");
  return lines.join("\n");
}

/**
 * Format a generic object response (fallback: list all keys).
 */
export function fmtGeneric(title, data, maxLen = 80) {
  if (data == null) return `= ${title} =\n  (空)`;
  if (typeof data === "string") return `= ${title} =\n  ${data}`;
  if (typeof data === "number" || typeof data === "boolean")
    return `= ${title} =\n  ${String(data)}`;
  if (Array.isArray(data)) {
    return fmtList(
      title,
      data,
      (item) =>
        typeof item === "object" && item !== null
          ? Object.entries(item)
              .map(([k, v]) => `${k}=${String(v ?? "").slice(0, 40)}`)
              .join(" | ")
          : String(item).slice(0, maxLen)
    );
  }
  return fmtObj(title, data, maxLen);
}

/** Boolean to 是/否 */
export function fmtBool(v) {
  return v ? "是" : "否";
}

/** Status icon */
export function statusIcon(status) {
  if (status === "Running" || status === "running" || status === "Enabled" || status === "enabled")
    return "🟢";
  if (status === "Stopped" || status === "stopped" || status === "Disabled" || status === "disabled")
    return "🔴";
  if (status === "Paused" || status === "paused") return "⏸️";
  if (status === "Error" || status === "error") return "⚠️";
  return "⚪";
}
