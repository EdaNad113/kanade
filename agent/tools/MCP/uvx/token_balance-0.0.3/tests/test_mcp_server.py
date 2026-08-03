"""MCP server 测试：内部处理函数 + 缓存 + 错误路径（复用本地 Mock 服务）。"""

import asyncio
import json
import os
import socket
import tempfile
import unittest

from aiohttp import web

from mcp import ClientSession
from tests.test_e2e import MockVendorServer
from token_balance.mcp_server import (
    _handle_list_services,
    _handle_query_balances,
    _handle_query_endpoint,
    mcp,
)
from token_balance.mcp_server import _cache as mcp_cache
from token_balance.mcp_server import _close_session


class McpServerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server = MockVendorServer()
        await self.server.start()
        await _close_session()
        mcp_cache.clear()

    async def asyncTearDown(self):
        await self.server.stop()
        await _close_session()
        mcp_cache.clear()

    def _write_config(self, tmp: str) -> str:
        base = self.server.base
        cfg = f"""
timeout: 5
concurrency: 5
platform_aliases:
  deepseek: "我的深度求索"
services:
  deepseek:
    type: deepseek
    api_key: sk-smoke-12345678
    url: "{base}/user/balance"
  kimi:
    type: kimi-full
    api_key: sk-test
    url: "{base}/v1/users/me/balance"
  newapi:
    type: newapi
    api_key: sk-test
    base_url: "{base}"
  bad_line:
    type: not-exist
"""
        path = os.path.join(tmp, "config.yaml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(cfg)
        return path

    # ---------- list_services ----------

    async def test_list_services(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(tmp)
            out = _handle_list_services(path)
        self.assertTrue(out["config_exists"])
        self.assertEqual(len(out["platforms"]), 17)
        names = [s["name"] for s in out["services"]]
        self.assertIn("deepseek", names)
        self.assertIn("kimi", names)
        # 配置错误项也上报
        self.assertEqual(len(out["config_errors"]), 1)

    async def test_list_services_missing_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = _handle_list_services(os.path.join(tmp, "nope.yaml"))
        self.assertFalse(out["config_exists"])
        self.assertEqual(out["services"], [])
        # 平台列表仍然可用
        self.assertEqual(len(out["platforms"]), 17)

    # ---------- query_balances ----------

    async def test_query_balances_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(tmp)
            out = await _handle_query_balances(None, None, path)
        self.assertEqual(out["summary"]["success"], 3)
        self.assertEqual(out["summary"]["failed"], 1)  # bad_line 配置错误
        results = {r["name"]: r for r in out["results"]}
        self.assertEqual(results["DeepSeek"]["total"], "12.34")
        self.assertEqual(results["测试中转站"]["remaining"], "70")

    async def test_query_balances_filter_by_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(tmp)
            out = await _handle_query_balances(["我的深度求索"], None, path)
        self.assertEqual(len(out["results"]), 1)
        self.assertEqual(out["results"][0]["name"], "DeepSeek")

    async def test_query_balances_no_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(tmp)
            out = await _handle_query_balances(["不存在的服务"], None, path)
        self.assertEqual(out["summary"]["failed"], 1)
        self.assertIn("未匹配到任何服务", out["config_errors"][0])

    async def test_query_balances_missing_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = await _handle_query_balances(None, None, os.path.join(tmp, "nope.yaml"))
        self.assertIn("未找到配置文件", out["config_errors"][0])

    async def test_query_balances_cache_hit(self):
        # 缓存包装在 FastMCP 工具层：通过工具函数调用验证 TTL 缓存
        from token_balance.mcp_server import query_balances
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(tmp)
            old = os.environ.get("TOKEN_BALANCE_CONFIG")
            os.environ["TOKEN_BALANCE_CONFIG"] = path
            try:
                out1 = await query_balances(["deepseek"])
                out2 = await query_balances(["deepseek"])
            finally:
                if old is None:
                    os.environ.pop("TOKEN_BALANCE_CONFIG", None)
                else:
                    os.environ["TOKEN_BALANCE_CONFIG"] = old
        self.assertFalse(out1["cached"])
        self.assertTrue(out2["cached"])
        # 缓存是副本，修改返回结果不会污染缓存
        out2["results"][0]["total"] = "999"
        with tempfile.TemporaryDirectory() as tmp2:
            path2 = self._write_config(tmp2)
            old = os.environ.get("TOKEN_BALANCE_CONFIG")
            os.environ["TOKEN_BALANCE_CONFIG"] = path2
            try:
                out3 = await query_balances(["deepseek"])
            finally:
                if old is None:
                    os.environ.pop("TOKEN_BALANCE_CONFIG", None)
                else:
                    os.environ["TOKEN_BALANCE_CONFIG"] = old
        self.assertEqual(out3["results"][0]["total"], "12.34")

    # ---------- query_endpoint ----------

    async def test_query_endpoint_url_openai(self):
        out = await _handle_query_endpoint(f"{self.server.base}/v1", ["sk-test"], 5)
        self.assertEqual(out["summary"]["success"], 1)
        r = out["results"][0]
        self.assertEqual(r["name"], "OpenAI 兼容端点")
        self.assertEqual(r["remaining"], "7.50")

    async def test_query_endpoint_url_newapi(self):
        # 独立服务器（无 OpenAI 路由）验证降级
        app = web.Application()

        async def token_handler(request):
            return web.json_response({
                "code": 0, "success": True, "message": "",
                "data": {"name": "中转站", "total_granted": 100,
                         "total_used": 30, "total_available": 70,
                         "unlimited_quota": False, "expires_at": 0},
            })

        app.router.add_get("/api/usage/token", token_handler)
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = runner.addresses[0][1]
        try:
            out = await _handle_query_endpoint(f"http://127.0.0.1:{port}", ["sk-test"], 5)
        finally:
            await site.stop()
            await runner.cleanup()
        self.assertEqual(out["summary"]["success"], 1)
        self.assertEqual(out["results"][0]["remaining"], "70")

    async def test_query_endpoint_json_conn(self):
        conn = '{"_type":"newapi_channel_conn","key":"sk-test","url":"%s"}' % self.server.base
        out = await _handle_query_endpoint(conn, [], 5)
        self.assertEqual(out["summary"]["success"], 1)
        self.assertEqual(out["results"][0]["name"], "测试中转站")

    async def test_query_endpoint_platform_alias_no_network(self):
        # 平台别名走真实端点（沙箱无外网），应返回结构化失败而非崩溃
        out = await _handle_query_endpoint("ds", ["sk-test"], 5)
        self.assertEqual(len(out["results"]), 1)
        self.assertFalse(out["results"][0]["ok"])
        self.assertEqual(out["results"][0]["name"], "DeepSeek")

    async def test_query_endpoint_unknown_target(self):
        out = await _handle_query_endpoint("不存在的平台", ["sk-test"], 5)
        self.assertIn("无法识别", out["config_errors"][0])

    async def test_query_endpoint_no_keys(self):
        out = await _handle_query_endpoint("ds", [], 5)
        self.assertIn("未提供 API Key", out["config_errors"][0])

    async def test_query_endpoint_requires_base_url(self):
        out = await _handle_query_endpoint("newapi", ["sk-test"], 5)
        self.assertIn("需要 base_url", out["config_errors"][0])


# ==================== 资源与远程传输测试 ====================

class ResourceTests(unittest.IsolatedAsyncioTestCase):
    """token:// 资源：通过真实 stdio 客户端读取。"""

    async def asyncSetUp(self):
        self.server = MockVendorServer()
        await self.server.start()
        await _close_session()
        mcp_cache.clear()

    async def asyncTearDown(self):
        await self.server.stop()
        await _close_session()
        mcp_cache.clear()

    async def test_resources_readable_via_stdio(self):
        # 用 stdio 客户端验证 list_resources / list_resource_templates / read_resource
        from mcp import StdioServerParameters
        from mcp.client.stdio import stdio_client
        import sys

        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = os.path.join(tmp, "config.yaml")
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write(f"""
timeout: 5
services:
  deepseek:
    type: deepseek
    api_key: sk-smoke-12345678
    url: "{self.server.base}/user/balance"
""")
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            env["TOKEN_BALANCE_CONFIG"] = cfg_path
            params = StdioServerParameters(command=sys.executable, args=["-m", "token_balance.mcp_server"], env=env)
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    resources_result = await session.list_resources()
                    uris = [str(r.uri) for r in resources_result.resources]
                    self.assertIn("token://services", uris)
                    self.assertIn("token://balances", uris)

                    templates_result = await session.list_resource_templates()
                    tpl_uris = [str(t.uriTemplate) for t in templates_result.resourceTemplates]
                    self.assertIn("token://balance/{name}", tpl_uris)

                    # 读取静态资源
                    res = await session.read_resource("token://services")
                    data = json.loads(res.contents[0].text)
                    self.assertIn("platforms", data)
                    self.assertEqual(len(data["platforms"]), 17)

                    # 读取模板资源（单个服务）
                    res = await session.read_resource("token://balance/deepseek")
                    data = json.loads(res.contents[0].text)
                    self.assertEqual(data["summary"]["success"], 1)
                    self.assertEqual(data["results"][0]["total"], "12.34")

                    # 读取余额快照（全部服务）
                    res = await session.read_resource("token://balances")
                    data = json.loads(res.contents[0].text)
                    self.assertEqual(data["summary"]["success"], 1)


def _free_port() -> int:
    """取一个空闲端口（bind 0 后释放；uvicorn 无公开 API 获取随机端口，测试用）。"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


async def _start_uvicorn(app):
    """进程内启动 uvicorn，返回 (port, task, server)。"""
    import uvicorn

    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    # 本版本 uvicorn 的 started 是 bool 而非 Event，轮询等待就绪
    while not server.started:
        await asyncio.sleep(0.05)
    return port, task, server


async def _stop_uvicorn(task, server):
    server.should_exit = True
    try:
        await asyncio.wait_for(task, timeout=5)
    except asyncio.TimeoutError:
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass


class RemoteTransportTests(unittest.IsolatedAsyncioTestCase):
    """SSE / Streamable HTTP 传输全链路。"""

    async def asyncSetUp(self):
        self.server = MockVendorServer()
        await self.server.start()
        await _close_session()
        mcp_cache.clear()

    async def asyncTearDown(self):
        await self.server.stop()
        await _close_session()
        mcp_cache.clear()

    def _write_config(self, tmp: str) -> str:
        path = os.path.join(tmp, "config.yaml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"""
timeout: 5
services:
  deepseek:
    type: deepseek
    api_key: sk-smoke-12345678
    url: "{self.server.base}/user/balance"
""")
        return path

    async def test_sse_transport_full(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = self._write_config(tmp)
            os.environ["TOKEN_BALANCE_CONFIG"] = cfg_path
            try:
                port, task, server = await _start_uvicorn(mcp.sse_app())
                try:
                    from mcp.client.sse import sse_client
                    url = f"http://127.0.0.1:{port}/sse"
                    async with sse_client(url) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            tools = await session.list_tools()
                            names = [t.name for t in tools.tools]
                            self.assertIn("query_balances", names)
                            res = await session.read_resource("token://services")
                            data = json.loads(res.contents[0].text)
                            self.assertEqual(len(data["platforms"]), 17)
                            res = await session.call_tool("query_balances", {"service_names": ["deepseek"]})
                            data = json.loads(res.content[0].text)
                            self.assertEqual(data["results"][0]["total"], "12.34")
                finally:
                    await _stop_uvicorn(task, server)
            finally:
                os.environ.pop("TOKEN_BALANCE_CONFIG", None)

    async def test_streamable_http_transport_full(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = self._write_config(tmp)
            os.environ["TOKEN_BALANCE_CONFIG"] = cfg_path
            try:
                port, task, server = await _start_uvicorn(mcp.streamable_http_app())
                try:
                    from mcp.client.streamable_http import streamable_http_client
                    url = f"http://127.0.0.1:{port}/mcp"
                    # 该版本 streamable_http_client 返回 (read, write, get_session_id) 三元组
                    async with streamable_http_client(url) as (read, write, _get_session_id):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            tools = await session.list_tools()
                            names = [t.name for t in tools.tools]
                            self.assertIn("list_services", names)
                            res = await session.read_resource("token://balance/deepseek")
                            data = json.loads(res.contents[0].text)
                            self.assertEqual(data["results"][0]["total"], "12.34")
                            res = await session.call_tool("query_endpoint",
                                                          {"target": self.server.base, "api_keys": ["sk-test"]})
                            data = json.loads(res.content[0].text)
                            self.assertEqual(data["summary"]["success"], 1)
                finally:
                    await _stop_uvicorn(task, server)
            finally:
                os.environ.pop("TOKEN_BALANCE_CONFIG", None)


if __name__ == "__main__":
    unittest.main()