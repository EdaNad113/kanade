#!/usr/bin/env node
/**
 * mcp-1panel — MCP Server for 1Panel
 *
 * Modular architecture. Tool definitions live in src/tools/*.js.
 * This file only handles MCP protocol wiring and startup.
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import { ALL_TOOLS } from "./tools/index.js";
import { getResources, readResource } from "./resources.js";

const server = new Server(
  { name: "mcp-1panel", version: "0.1.0" },
  { capabilities: { tools: {}, resources: {} } }
);

// ── Tool Handlers ────────────────────────────────────────────

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: Object.entries(ALL_TOOLS).map(([name, t]) => ({
    name,
    description: t.description,
    inputSchema: t.inputSchema,
  })),
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const tool = ALL_TOOLS[request.params.name];
  if (!tool) {
    throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
  }
  try {
    const text = await tool.handler(request.params.arguments ?? {});
    return { content: [{ type: "text", text }] };
  } catch (e) {
    return { content: [{ type: "text", text: `ERR: ${e.message}` }], isError: true };
  }
});

// ── Resource Handlers ────────────────────────────────────────

server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: getResources(),
}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  try {
    return await readResource(request.params.uri);
  } catch (e) {
    if (e.message.startsWith("Unknown resource")) {
      throw new McpError(ErrorCode.NotFound, e.message);
    }
    throw new McpError(ErrorCode.InternalError, `Resource error: ${e.message}`);
  }
});

// ── Startup ──────────────────────────────────────────────────

async function main() {
  const toolCount = Object.keys(ALL_TOOLS).length;
  const resourceCount = getResources().length;
  console.error(`[mcp-1panel] Starting... (${toolCount} tools, ${resourceCount} resources)`);
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(`[mcp-1panel] Running on stdio (${toolCount} tools, ${resourceCount} resources)`);
}

main().catch((e) => {
  console.error("[mcp-1panel] Fatal:", e);
  process.exit(1);
});
