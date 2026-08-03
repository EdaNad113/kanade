"""模板渲染单元测试。"""

import unittest

from token_balance.renderer import eval_expr, get_by_path, render_template


class GetByPathTests(unittest.TestCase):
    def test_dict_path(self):
        data = {"data": {"balance": 12.5}}
        self.assertEqual(get_by_path(data, "data.balance"), 12.5)

    def test_list_index(self):
        data = {"balance_infos": [{"total_balance": "12.34"}]}
        self.assertEqual(get_by_path(data, "balance_infos.0.total_balance"), "12.34")

    def test_missing(self):
        data = {"a": {"b": 1}}
        self.assertIsNone(get_by_path(data, "a.c"))
        self.assertIsNone(get_by_path(data, "x.y.z"))
        self.assertIsNone(get_by_path(data, "a.b.c"))


class EvalExprTests(unittest.TestCase):
    def test_round(self):
        # round 是用户显式调用的函数，保留其精度
        self.assertEqual(eval_expr("round(1.23456, 2)"), 1.23)

    def test_percent(self):
        self.assertEqual(eval_expr("50%"), 0.5)

    def test_formula(self):
        self.assertEqual(eval_expr("10/4"), 2.5)

    def test_small_number_rounded_to_2(self):
        # 与参考插件一致：公式结果保留两位小数
        self.assertEqual(eval_expr("0.00142"), 0.0)

    def test_safe_no_builtins(self):
        self.assertEqual(eval_expr("__import__('os')"), "N/A")


class RenderTemplateTests(unittest.TestCase):
    def test_simple_path(self):
        out = render_template("余额: {{data.balance}} 元", {"data": {"balance": 12.5}})
        self.assertEqual(out, "余额: 12.50 元")

    def test_int_no_decimal(self):
        out = render_template("余额: {{data.balance}}", {"data": {"balance": 12}})
        self.assertEqual(out, "余额: 12")

    def test_string_number(self):
        out = render_template("余额: {{balance_infos.0.total_balance}} 元", {"balance_infos": [{"total_balance": "12.34"}]})
        self.assertEqual(out, "余额: 12.34 元")

    def test_formula_round(self):
        out = render_template(
            "{{round({data.quota}/500000*7.1, 2)}} 元",
            {"data": {"quota": 1000000}},
        )
        self.assertEqual(out, "14.2 元")

    def test_formula_usage_percent(self):
        out = render_template(
            "{{round({data.usage}/{data.limit}*100, 1)}}%",
            {"data": {"usage": 30, "limit": 100}},
        )
        self.assertEqual(out, "30%")  # 30.0 是整数，参考插件会整数化

    def test_missing_value_na(self):
        out = render_template("余额: {{data.nope}}", {"data": {}})
        self.assertEqual(out, "余额: N/A")

    def test_nested_expr(self):
        out = render_template(
            "剩余 {{round({model_remains.0.current_interval_total_count}-{model_remains.0.current_interval_usage_count})}}",
            {"model_remains": [{"current_interval_total_count": 100, "current_interval_usage_count": 30}]},
        )
        self.assertEqual(out, "剩余 70")


if __name__ == "__main__":
    unittest.main()