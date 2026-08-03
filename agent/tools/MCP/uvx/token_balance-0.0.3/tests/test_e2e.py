"""端到端测试：用本地 Mock 服务模拟各厂商接口，验证完整查询流程。"""

import unittest

import aiohttp
from aiohttp import web

from token_balance.config import service_from_dict
from token_balance.fetchers import query_all, query_by_url


class MockVendorServer:
    """本地 Mock 服务，模拟 DeepSeek / 硅基流动 / Kimi / OpenAI / NEW API / 自定义站点。"""

    def __init__(self) -> None:
        app = web.Application()

        async def deepseek(request):
            return web.json_response({
                "is_available": True,
                "balance_infos": [{
                    "currency": "CNY",
                    "total_balance": "12.34",
                    "granted_balance": "10.00",
                    "topped_up_balance": "2.34",
                }],
            })

        async def siliconflow(request):
            return web.json_response({
                "code": 20000,
                "message": "",
                "data": {"totalBalance": 5.0, "chargeBalance": 3.0},
            })

        async def moonshot(request):
            return web.json_response({
                "data": {
                    "available_balance": 25.0,
                    "cash_balance": 10.0,
                    "voucher_balance": 15.0,
                },
            })

        async def openai_sub(request):
            return web.json_response({
                "hard_limit_usd": 10.0,
                "soft_limit_usd": 10.0,
                "has_payment_method": True,
                "access_until": "2030-01-01",
            })

        async def openai_usage(request):
            return web.json_response({"total_usage": 250})  # 2.50 USD

        async def newapi_token(request):
            return web.json_response({
                "code": 0,
                "success": True,
                "message": "",
                "data": {
                    "name": "测试中转站",
                    "total_granted": 100,
                    "total_used": 30,
                    "total_available": 70,
                    "unlimited_quota": False,
                    "expires_at": 0,
                },
            })

        async def oneapi_self(request):
            return web.json_response({
                "success": True,
                "message": "",
                "data": {"email": "user@example.com", "balance": 88.8},
            })

        async def custom_balance(request):
            return web.json_response({"data": {"balance": 88.5, "note": "充值赠送"}})

        async def apimart(request):
            return web.json_response({
                "remain_balance": 10.0,
                "used_balance": 4.0,
                "remain_credits": 50.0,
                "used_credits": 20.0,
            })

        async def bad_json(request):
            # 返回非 JSON，且响应体里回显 Authorization 密钥（用于验证脱敏）
            return web.Response(text=f"Bearer {request.headers.get('Authorization', '')} error page")

        async def missing_field(request):
            return web.json_response({"data": {}})

        app.router.add_get("/user/balance", deepseek)
        app.router.add_get("/v1/user/info", siliconflow)
        app.router.add_get("/v1/users/me/balance", moonshot)
        app.router.add_get("/v1/dashboard/billing/subscription", openai_sub)
        app.router.add_get("/v1/dashboard/billing/usage", openai_usage)
        app.router.add_get("/api/usage/token", newapi_token)
        app.router.add_get("/api/user/self", oneapi_self)
        app.router.add_get("/custom/balance", custom_balance)
        app.router.add_get("/v1/user/balance", apimart)
        app.router.add_get("/badjson", bad_json)
        app.router.add_get("/missing", missing_field)

        self.app = app
        self.runner = None
        self.site = None
        self._sock = None
        self.port = None

    async def start(self) -> None:
        # 用公开 API runner.addresses 获取端口，避免访问私有属性
        self.runner = web.AppRunner(self.app, access_log=None)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await self.site.start()
        self.port = self.runner.addresses[0][1]

    async def stop(self) -> None:
        await self.site.stop()
        await self.runner.cleanup()

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.port}"


class E2ETests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server = MockVendorServer()
        await self.server.start()

    async def asyncTearDown(self):
        await self.server.stop()

    async def test_deepseek(self):
        svc = service_from_dict("ds", {"type": "deepseek", "api_key": "sk-test", "url": f"{self.server.base}/user/balance"})
        results = await query_all([svc], timeout=5)
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.name, "DeepSeek")
        self.assertEqual(r.currency, "CNY")
        self.assertEqual(r.total, "12.34")
        self.assertEqual(r.remaining, "12.34")
        self.assertIn("赠送: 10.00", r.raw_info)
        self.assertEqual(r.rendered, "DeepSeek: 12.34 元")

    async def test_siliconflow(self):
        svc = service_from_dict("sc", {"type": "siliconflow", "api_key": "sk-test", "url": f"{self.server.base}/v1/user/info"})
        r = (await query_all([svc], timeout=5))[0]
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.currency, "CNY")
        self.assertEqual(r.total, "5.0")
        self.assertIn("3.0", r.raw_info)

    async def test_kimi(self):
        svc = service_from_dict("kimi", {"type": "kimi-full", "api_key": "sk-test", "url": f"{self.server.base}/v1/users/me/balance"})
        r = (await query_all([svc], timeout=5))[0]
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.currency, "CNY")
        self.assertEqual(r.total, "25.0")
        self.assertIn("现金: 10.0", r.raw_info)
        self.assertIn("代金券: 15.0", r.raw_info)

    async def test_openai_billing(self):
        svc = service_from_dict("oa", {"type": "openai", "api_key": "sk-test", "url": f"{self.server.base}/v1"})
        r = (await query_all([svc], timeout=5))[0]
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.currency, "USD")
        self.assertEqual(r.total, "10.00")
        self.assertEqual(r.used, "2.50")
        self.assertEqual(r.remaining, "7.50")
        self.assertIn("支付: 是", r.raw_info)

    async def test_newapi_token(self):
        svc = service_from_dict("na", {"type": "newapi", "api_key": "sk-test", "base_url": self.server.base})
        r = (await query_all([svc], timeout=5))[0]
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.name, "测试中转站")
        self.assertEqual(r.total, "100")
        self.assertEqual(r.used, "30")
        self.assertEqual(r.remaining, "70")
        self.assertIn("永不过期", r.raw_info)

    async def test_oneapi_self(self):
        svc = service_from_dict("oa", {"type": "oneapi", "api_key": "sk-test", "base_url": self.server.base})
        r = (await query_all([svc], timeout=5))[0]
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.name, "One-API")
        self.assertEqual(r.remaining, "88.80")
        self.assertIn("user@example.com", r.rendered)

    async def test_custom_template(self):
        svc = service_from_dict(
            "custom",
            {
                "type": "custom",
                "api_key": "sk-test",
                "url": f"{self.server.base}/custom/balance",
                "headers": {"Authorization": "Bearer sk-test"},
                "result_template": "我的站: {{data.balance}} 元",
                "currency": "CNY",
                "total_template": "{{data.balance}}",
                "raw_info_template": "备注: {{data.note}}",
            },
        )
        r = (await query_all([svc], timeout=5))[0]
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.rendered, "我的站: 88.50 元")
        self.assertEqual(r.currency, "CNY")
        self.assertEqual(r.total, "88.50")
        self.assertEqual(r.raw_info, "备注: 充值赠送")

    async def test_apimart_formula(self):
        svc = service_from_dict("ap", {"type": "apimart", "api_key": "sk-test", "url": f"{self.server.base}/v1/user/balance"})
        r = (await query_all([svc], timeout=5))[0]
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.total, "70")
        self.assertEqual(r.used, "28")
        self.assertEqual(r.remaining, "42")
        self.assertEqual(r.currency, "CNY")

    async def test_query_by_url_openai(self):
        async with aiohttp.ClientSession() as session:
            r = await query_by_url(session, f"{self.server.base}/v1", "sk-test", timeout=5)
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.remaining, "7.50")
        self.assertIn("127.0.0.1", r.raw_info)

    async def test_query_by_url_newapi(self):
        # 服务器同时提供 OpenAI 路由时自动识别会优先走 OpenAI Billing，
        # 因此这里用只含 /api/usage/token 的独立服务器验证降级逻辑
        app = web.Application()

        async def token_handler(request):
            return web.json_response({
                "code": 0, "success": True, "message": "",
                "data": {"name": "测试中转站", "total_granted": 100,
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
            async with aiohttp.ClientSession() as session:
                r = await query_by_url(session, f"http://127.0.0.1:{port}", "sk-test", timeout=5)
        finally:
            await site.stop()
            await runner.cleanup()
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.remaining, "70")
        self.assertEqual(r.name, "测试中转站")

    async def test_query_by_url_newapi_with_v1_suffix(self):
        # P0 修复：以 /v1 结尾的地址降级到 New API 时不能拼出 /v1/api/usage/token
        app = web.Application()

        async def token_handler(request):
            self.assertEqual(request.path, "/api/usage/token")
            return web.json_response({
                "code": 0, "success": True, "message": "",
                "data": {"name": "中转站", "total_granted": 100,
                         "total_used": 0, "total_available": 100,
                         "unlimited_quota": False, "expires_at": 0},
            })

        app.router.add_get("/api/usage/token", token_handler)
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = runner.addresses[0][1]
        try:
            async with aiohttp.ClientSession() as session:
                r = await query_by_url(session, f"http://127.0.0.1:{port}/v1", "sk-test", timeout=5)
        finally:
            await site.stop()
            await runner.cleanup()
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.remaining, "100")

    async def test_query_by_url_fallback_error_contains_reasons(self):
        # 两种格式都失败时，错误信息应包含两段失败原因（不再吞异常）
        app = web.Application()

        async def not_found(request):
            raise web.HTTPNotFound()

        app.router.add_get("/v1/dashboard/billing/subscription", not_found)
        app.router.add_get("/api/usage/token", not_found)
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = runner.addresses[0][1]
        try:
            async with aiohttp.ClientSession() as session:
                r = await query_by_url(session, f"http://127.0.0.1:{port}", "sk-test", timeout=5)
        finally:
            await site.stop()
            await runner.cleanup()
        self.assertFalse(r.ok)
        self.assertIn("OpenAI Billing", r.error)
        self.assertIn("New API", r.error)

    async def test_empty_key_rejected(self):
        # P0：空 key 不发请求，直接报错（配置层已拦截，这里直接构造 Service 验证 Fetcher 层）
        from token_balance.fetchers import Service
        svc = Service(name="ds", type="deepseek", api_key="", url=f"{self.server.base}/user/balance", display_name="DeepSeek")
        r = (await query_all([svc], timeout=5))[0]
        self.assertFalse(r.ok)
        self.assertIn("未提供 API Key", r.error)

    async def test_response_body_sanitized(self):
        # P0：错误信息中的响应体回显必须脱敏，不能泄露 Authorization
        secret = "sk-very-secret-123456"
        svc = service_from_dict("bad", {"type": "deepseek", "api_key": secret, "url": f"{self.server.base}/badjson"})
        r = (await query_all([svc], timeout=5))[0]
        self.assertFalse(r.ok)
        self.assertNotIn(secret, r.error)
        self.assertIn("****", r.error)

    async def test_missing_field_reports_path(self):
        # P1：未找到字段的错误信息要带上字段路径
        svc = service_from_dict(
            "miss",
            {
                "type": "custom",
                "api_key": "sk-test",
                "url": f"{self.server.base}/missing",
                "result_template": "余额: {{data.balance}} 元",
            },
        )
        r = (await query_all([svc], timeout=5))[0]
        self.assertFalse(r.ok)
        self.assertIn("未找到字段", r.error)
        self.assertIn("{{data.balance}}", r.error)

    async def test_failure_isolated(self):
        svc1 = service_from_dict("ds", {"type": "deepseek", "api_key": "sk-test", "url": f"{self.server.base}/user/balance"})
        svc2 = service_from_dict("bad", {"type": "deepseek", "api_key": "sk-test", "url": f"{self.server.base}/not-exist"})
        results = await query_all([svc1, svc2], timeout=5)
        self.assertTrue(results[0].ok)
        self.assertFalse(results[1].ok)
        self.assertIn("404", results[1].error)


if __name__ == "__main__":
    unittest.main()