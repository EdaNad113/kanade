/**
 * Tests for panel-client.js — MD5 authentication, error handling, env fallback.
 *
 * Run with: node --test src/panel-client.test.js
 * (Node.js >= 18 built-in test runner)
 */
import { describe, it, mock } from "node:test";
import assert from "node:assert/strict";
import crypto from "node:crypto";

// Dynamic import with env setup
async function createClient(host, apiKey) {
  const { PanelClient } = await import("./panel-client.js");
  return new PanelClient(host, apiKey);
}

// -----------------------------------------------------------------------
// Initialization
// -----------------------------------------------------------------------

describe("PanelClient (Node.js)", () => {
  describe("init", () => {
    it("accepts host and key from constructor", async () => {
      const c = await createClient("http://example.com", "test-key");
      assert.ok(c.base.endsWith("/api/v2"));
      assert.equal(c.apiKey, "test-key");
    });

    it("strips trailing slash from host", async () => {
      const c = await createClient("http://example.com/", "k");
      assert.ok(!c.base.endsWith("//"));
    });

    it("throws when host is missing", async () => {
      const oldHost = process.env.PANEL_HOST;
      const oldKey = process.env.PANEL_API_KEY;
      delete process.env.PANEL_HOST;
      delete process.env.PANEL_API_KEY;

      const { PanelClient } = await import("./panel-client.js");
      assert.throws(() => new PanelClient(), /PANEL_HOST/);

      if (oldHost) process.env.PANEL_HOST = oldHost;
      if (oldKey) process.env.PANEL_API_KEY = oldKey;
    });

    it("reads env vars as fallback", async () => {
      process.env.PANEL_HOST = "http://env-host";
      process.env.PANEL_API_KEY = "env-key";

      const { PanelClient } = await import("./panel-client.js");
      const c = new PanelClient();
      assert.ok(c.base.includes("env-host"));
      assert.equal(c.apiKey, "env-key");

      delete process.env.PANEL_HOST;
      delete process.env.PANEL_API_KEY;
    });

    it("supports PANEL_ACCESS_TOKEN as key alias", async () => {
      process.env.PANEL_HOST = "http://host";
      delete process.env.PANEL_API_KEY;
      process.env.PANEL_ACCESS_TOKEN = "alt-key";

      const { PanelClient } = await import("./panel-client.js");
      const c = new PanelClient();
      assert.equal(c.apiKey, "alt-key");

      delete process.env.PANEL_HOST;
      delete process.env.PANEL_ACCESS_TOKEN;
    });
  });

  // -----------------------------------------------------------------------
  // Authentication headers — MD5 signing
  // -----------------------------------------------------------------------

  describe("auth", () => {
    it("produces correct content-type header", async () => {
      const c = await createClient("http://a", "key");
      const h = c._authHeaders();
      assert.equal(h["Content-Type"], "application/json");
    });

    it("produces a numeric timestamp", async () => {
      const c = await createClient("http://a", "key");
      const ts = c._authHeaders()["1Panel-Timestamp"];
      assert.match(ts, /^\d+$/);
      assert.ok(Math.abs(Number(ts) - Math.floor(Date.now() / 1000)) < 10);
    });

    it("computes correct MD5 token", async () => {
      const c = await createClient("http://a", "my-api-key");
      const h = c._authHeaders();
      const expected = crypto
        .createHash("md5")
        .update("1panel" + "my-api-key" + h["1Panel-Timestamp"])
        .digest("hex");
      assert.equal(h["1Panel-Token"], expected);
    });
  });

  // -----------------------------------------------------------------------
  // HTTP calls via fetch
  // -----------------------------------------------------------------------

  describe("http calls", () => {
    it("_request sends correct method and headers", async () => {
      const c = await createClient("http://test", "k");

      // Mock fetch
      mock.method(global, "fetch", async (url, opts) => {
        assert.ok(url.includes("/api/v2/test-path"));
        assert.equal(opts.method, "GET");
        assert.equal(opts.headers["Content-Type"], "application/json");
        assert.ok(opts.headers["1Panel-Token"]);
        return {
          ok: true,
          json: async () => ({ code: 200, data: { status: "ok" } }),
        };
      });

      const result = await c.get("/test-path");
      assert.deepEqual(result, { status: "ok" });

      mock.restoreAll();
    });

    it("throws on non-200 API response", async () => {
      const c = await createClient("http://test", "k");

      mock.method(global, "fetch", async () => ({
        ok: true,
        json: async () => ({ code: 500, message: "Server error" }),
      }));

      await assert.rejects(() => c.get("/fail"), /API error/);
      mock.restoreAll();
    });

    it("throws on HTTP error", async () => {
      const c = await createClient("http://test", "k");

      mock.method(global, "fetch", async () => ({
        ok: false,
        status: 403,
        statusText: "Forbidden",
        text: async () => "Forbidden",
      }));

      await assert.rejects(() => c.get("/secret"), /HTTP 403/);
      mock.restoreAll();
    });

    it("handles POST with body", async () => {
      const c = await createClient("http://test", "k");

      mock.method(global, "fetch", async (url, opts) => {
        const body = JSON.parse(opts.body);
        assert.equal(body.name, "test");
        return {
          ok: true,
          json: async () => ({ code: 200, data: "created" }),
        };
      });

      const result = await c.post("/create", { name: "test" });
      assert.equal(result, "created");
      mock.restoreAll();
    });
  });
});
