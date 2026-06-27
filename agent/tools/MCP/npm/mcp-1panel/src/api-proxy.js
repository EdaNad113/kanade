/**
 * mcp-1panel — API Proxy (shared lazy client)
 *
 * Imported by all tool modules.
 * The first call to any method creates the PanelClient from env vars.
 */
import { PanelClient } from "./panel-client.js";

let _client = null;

function getClient() {
  if (_client) return _client;
  // Don't cache errors — retry on every call so
  // a fixed env var doesn't require a server restart.
  _client = new PanelClient();
  return _client;
}

/**
 * api is a lazy proxy — tool modules can import it safely;
 * it only fails when a tool actually calls a 1Panel API without
 * PANEL_HOST / PANEL_API_KEY being set.
 */
export const api = new Proxy(
  {},
  {
    get(_, method) {
      return (...args) => getClient()[method](...args);
    },
  }
);
