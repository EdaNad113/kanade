# 1Panel API Client — 使用 API Key 认证
# 配置方式：环境变量 PANEL_HOST + PANEL_API_KEY
import os, time, hashlib, requests


class PanelClient:
    def __init__(self, host=None, api_key=None):
        self.base = (
            host or os.getenv("PANEL_HOST")
        )
        if not self.base:
            raise ValueError("PANEL_HOST 未设置（环境变量或构造参数）")
        self.base = self.base.rstrip("/") + "/api/v2"

        self.api_key = api_key or os.getenv("PANEL_API_KEY")
        if not self.api_key:
            raise ValueError("PANEL_API_KEY 未设置（环境变量或构造参数）")

    def _auth_headers(self):
        ts = str(int(time.time()))
        raw = "1panel" + self.api_key + ts
        token = hashlib.md5(raw.encode()).hexdigest()
        return {
            "Content-Type": "application/json",
            "1Panel-Token": token,
            "1Panel-Timestamp": ts,
        }

    def _request(self, method, path, **kwargs):
        url = self.base + path
        headers = self._auth_headers()
        resp = requests.request(method, url, headers=headers, timeout=15, **kwargs)
        data = resp.json()
        if data.get("code") != 200:
            msg = data.get("message", resp.text)
            raise RuntimeError(f"API 错误 [{resp.status_code}]: {msg}")
        return data.get("data")

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, body=None):
        return self._request("POST", path, json=body or {})

    def delete(self, path, body=None):
        return self._request("DELETE", path, json=body or {})

    def put(self, path, body=None):
        return self._request("PUT", path, json=body or {})