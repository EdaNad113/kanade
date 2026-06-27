/**
 * 1Panel API Client — uses API Key authentication (MD5 token signing)
 * Configuration: env vars PANEL_HOST + PANEL_API_KEY
 */
import crypto from "node:crypto";

export class PanelClient {
  constructor(host, apiKey) {
    this.base = (host || process.env.PANEL_HOST || "").replace(/\/+$/, "");
    if (!this.base) {
      throw new Error("PANEL_HOST not set (env var or constructor param)");
    }
    this.base += "/api/v2";

    this.apiKey = apiKey || process.env.PANEL_API_KEY || process.env.PANEL_ACCESS_TOKEN || "";
    if (!this.apiKey) {
      throw new Error("PANEL_API_KEY or PANEL_ACCESS_TOKEN not set (env var or constructor param)");
    }
  }

  _authHeaders() {
    const ts = String(Math.floor(Date.now() / 1000));
    const raw = "1panel" + this.apiKey + ts;
    const token = crypto.createHash("md5").update(raw).digest("hex");
    return {
      "Content-Type": "application/json",
      "1Panel-Token": token,
      "1Panel-Timestamp": ts,
    };
  }

  async _request(method, path, body) {
    const url = this.base + path;
    const headers = this._authHeaders();
    const opts = {
      method,
      headers,
    };
    if (body !== undefined) {
      opts.body = JSON.stringify(body);
    }
    const resp = await fetch(url, opts);
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
    }
    const data = await resp.json();
    if (data.code !== 200) {
      const msg = data.message || resp.statusText;
      throw new Error(`API error [${resp.status}]: ${msg}`);
    }
    return data.data;
  }

  async get(path, params) {
    let url = path;
    if (params) {
      const qs = new URLSearchParams(params).toString();
      url = path + "?" + qs;
    }
    return this._request("GET", url);
  }

  async post(path, body) {
    return this._request("POST", path, body || {});
  }

  async delete(path, body) {
    return this._request("DELETE", path, body || {});
  }

  async put(path, body) {
    return this._request("PUT", path, body || {});
  }
}
