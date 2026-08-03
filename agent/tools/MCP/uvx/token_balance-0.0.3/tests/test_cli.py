"""CLI 层单元测试：脱敏、NewAPI JSON 解析、别名匹配、分组输出、可配置模板。"""

import unittest

from token_balance.cli import (
    find_services,
    format_templated,
    format_text,
    match_platform,
    parse_newapi_conn,
)
from token_balance.config import AppConfig, Service
from token_balance.fetchers import BalanceResult, mask_key


class MaskKeyTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(mask_key(""), "")

    def test_long_key(self):
        self.assertEqual(mask_key("sk-123456789012"), "sk-123...9012")

    def test_short_key_fully_hidden(self):
        # P0 修复：太短的 key 不再显示可能重叠/更长的掩码
        for key in ("a", "ab", "abc", "sk-x", "sk-test1"):
            self.assertEqual(mask_key(key), "****")

    def test_exactly_10(self):
        self.assertEqual(mask_key("1234567890"), "123456...7890")


class ParseNewapiConnTests(unittest.TestCase):
    def test_valid(self):
        target = '{"_type":"newapi_channel_conn","key":"sk-xxx","url":"https://new.xinjianya.top"}'
        url, key, name = parse_newapi_conn(target)
        self.assertEqual(url, "https://new.xinjianya.top")
        self.assertEqual(key, "sk-xxx")
        self.assertEqual(name, "")

    def test_with_name(self):
        target = '{"_type":"newapi_channel_conn","key":"sk-xxx","url":"https://x.com","name":"我的站"}'
        url, key, name = parse_newapi_conn(target)
        self.assertEqual(name, "我的站")

    def test_invalid_json(self):
        self.assertIsNone(parse_newapi_conn("not json at all"))
        self.assertIsNone(parse_newapi_conn(""))
        self.assertIsNone(parse_newapi_conn('{"key":"sk-xxx"}'))           # 缺 url
        self.assertIsNone(parse_newapi_conn('{"url":"https://x.com"}'))    # 缺 key
        self.assertIsNone(parse_newapi_conn("[1,2,3]"))


class MatchPlatformTests(unittest.TestCase):
    def test_builtin_alias(self):
        self.assertEqual(match_platform("ds"), "deepseek")
        self.assertEqual(match_platform("深度求索"), "deepseek")
        self.assertEqual(match_platform("硅基"), "siliconflow")

    def test_extra_aliases(self):
        # P1：platform_aliases 配置的别名参与匹配
        extra = {"deepseek": "我自己的名字, 别名2"}
        self.assertEqual(match_platform("我自己的名字", extra), "deepseek")
        self.assertEqual(match_platform("别名2", extra), "deepseek")
        # 原有别名仍然可用
        self.assertEqual(match_platform("ds", extra), "deepseek")

    def test_no_match(self):
        self.assertIsNone(match_platform("不存在", {"deepseek": "ds"}))


class FindServicesTests(unittest.TestCase):
    def test_match_by_alias(self):
        # check 命令支持用平台别名过滤（含配置的自定义别名）
        cfg = AppConfig(path="test")
        cfg.services = [
            Service(name="ds", type="deepseek", api_key="sk-x", display_name="DeepSeek"),
            Service(name="sc", type="siliconflow", api_key="sk-x", display_name="硅基流动"),
        ]
        cfg.platform_aliases = {"deepseek": "我的ds"}
        hits = find_services(cfg, ["我的ds"], cfg.platform_aliases)
        self.assertEqual([s.name for s in hits], ["ds"])
        hits = find_services(cfg, ["深度求索"], cfg.platform_aliases)
        self.assertEqual([s.name for s in hits], ["ds"])


class FormatTextTests(unittest.TestCase):
    def _results(self):
        ok = BalanceResult(name="DeepSeek", currency="CNY", total="12.34", remaining="12.34",
                           raw_info="赠送: 10.00", api_key_masked="sk-a...b")
        fail = BalanceResult(name="硅基流动", error="HTTP 401", ok=False)
        return [ok, fail]

    def test_success_fail_grouped(self):
        # P2：成功项与失败项分组展示
        out = format_text(self._results(), [], "测试")
        self.assertIn("✅ DeepSeek", out)
        self.assertIn("❌ 失败 (1):", out)
        self.assertIn("❌ 硅基流动", out)
        # 成功项在失败分区之前
        self.assertLess(out.index("✅ DeepSeek"), out.index("❌ 失败"))
        self.assertIn("共 2 项，成功 1，失败 1", out)

    def test_config_errors_appended(self):
        out = format_text([], ["[x] 未知类型"], "测试")
        self.assertIn("[x] 未知类型", out)


class FormatTemplatedTests(unittest.TestCase):
    def _cfg(self):
        from token_balance.config import AppConfig
        cfg = AppConfig(path="test")
        cfg.success_template = "🟢 **{{source_name}}**\n  🔑 密钥: {{api_key}}\n  💵 {{balance}} {{currency}}\n{{smart_balance}}"
        cfg.error_template = "🔴 **{{source_name}}**\n  ❌ {{error}}"
        cfg.header_template = "💰 **{{title}}**"
        cfg.separator_template = "══"
        return cfg

    def _results(self):
        ok = BalanceResult(name="DeepSeek", currency="CNY", total="12.34", remaining="12.34",
                           raw_info="赠送: 10.00", api_key_masked="sk-a...b")
        ok2 = BalanceResult(name="OpenAI", currency="USD", total="10.00", remaining="7.50",
                            used="2.50", api_key_masked="sk-c...d")
        fail = BalanceResult(name="硅基流动", error="HTTP 401", ok=False)
        return [ok, ok2, fail]

    def test_templated_output(self):
        cfg = self._cfg()
        out = format_templated(self._results(), [], "余额查询", cfg)
        self.assertIn("💰 **余额查询**", out)
        self.assertIn("🟢 **DeepSeek**", out)
        self.assertIn("🔑 密钥: sk-a...b", out)
        # smart_balance 应包含 raw_info 与"总额"行（OpenAI 剩余≠总额）
        self.assertIn("📈 总额: 10.00 USD", out)
        self.assertIn("📊 已用: 2.50 USD", out)
        self.assertIn("🔴 **硅基流动**", out)

    def test_conditional_line_hidden(self):
        # {{?变量}} 条件行：值为空/0 时隐藏整行
        cfg = self._cfg()
        cfg.success_template = "第一行\n{{?used_balance}}已用: {{used_balance}} 元\n{{?raw_info}}{{raw_info}}"
        ok = BalanceResult(name="DeepSeek", currency="CNY", total="12.34", remaining="12.34", used="")
        out = format_templated([ok], [], "余额查询", cfg)
        self.assertIn("第一行", out)
        self.assertNotIn("已用:", out)
        self.assertNotIn("{{raw_info}}", out)

    def test_header_title_placeholder(self):
        # header_template 中的 {{title}} 占位符应被替换
        cfg = self._cfg()
        out = format_templated([], [], "我的标题", cfg)
        self.assertIn("**我的标题**", out)
        self.assertNotIn("{{title}}", out)


class RenderMethodsTests(unittest.TestCase):
    def test_render_success_smart_balance(self):
        r = BalanceResult(name="OpenAI", currency="USD", total="10.00", remaining="7.50", used="2.50",
                          raw_info="支付: 是")
        out = r.render_success("{{source_name}}|{{balance}}|{{remaining_balance}}|{{total_balance}}|{{used_balance}}|{{raw_info}}", "sk-a...b")
        self.assertEqual(out, "OpenAI|7.50|7.50|10.00|2.50|支付: 是")

    def test_render_error(self):
        r = BalanceResult(name="X", error="网络错误", ok=False)
        self.assertEqual(r.render_error("{{source_name}}: {{error}}", "k"), "X: 网络错误")
        self.assertEqual(r.render_error("", "k"), "🔴 **X**\n  ❌ 网络错误")

    def test_newline_escape(self):
        r = BalanceResult(name="X", currency="CNY", total="1", remaining="1")
        out = r.render_success("{{source_name}}\\n第二行", "")
        self.assertIn("\n", out)


if __name__ == "__main__":
    unittest.main()