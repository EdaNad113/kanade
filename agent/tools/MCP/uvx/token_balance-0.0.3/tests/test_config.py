"""配置加载与内置预设合并测试。"""

import os
import tempfile
import unittest
from pathlib import Path

from token_balance.config import ensure_config_file, load_config, resolve_secret, service_from_dict
from token_balance.fetchers import BUILTIN_PLATFORMS


class ResolveSecretTests(unittest.TestCase):
    def test_env_var(self):
        os.environ["TB_TEST_KEY"] = "sk-test-123"
        self.assertEqual(resolve_secret("env:TB_TEST_KEY"), "sk-test-123")
        del os.environ["TB_TEST_KEY"]

    def test_plain(self):
        self.assertEqual(resolve_secret("sk-plain"), "sk-plain")

    def test_missing_env(self):
        self.assertEqual(resolve_secret("env:TB_NOT_EXIST_XYZ"), "")


class ServiceFromDictTests(unittest.TestCase):
    def test_builtin_deepseek(self):
        svc = service_from_dict("ds", {"type": "deepseek", "api_key": "sk-x"})
        self.assertEqual(svc.type, "deepseek")
        self.assertEqual(svc.url, BUILTIN_PLATFORMS["deepseek"]["url"])
        self.assertEqual(svc.headers["Authorization"], "Bearer sk-x")
        self.assertEqual(svc.currency, "CNY")

    def test_builtin_requires_base_url(self):
        with self.assertRaises(ValueError):
            service_from_dict("n", {"type": "newapi", "api_key": "sk-x"})
        svc = service_from_dict("n", {"type": "newapi", "api_key": "sk-x", "base_url": "https://x.com"})
        self.assertIn("https://x.com/api/usage/token", svc.url)

    def test_custom_requires_url(self):
        with self.assertRaises(ValueError):
            service_from_dict("c", {"type": "custom"})

    def test_custom_placeholders(self):
        svc = service_from_dict(
            "c",
            {
                "type": "custom",
                "api_key": "sk-1",
                "url": "https://x.com/api?key={api_key}",
                "headers": {"Authorization": "Bearer {api_key}"},
                "result_template": "{{data.balance}} 元",
            },
        )
        self.assertEqual(svc.url, "https://x.com/api?key=sk-1")
        self.assertEqual(svc.headers["Authorization"], "Bearer sk-1")

    def test_unknown_type(self):
        with self.assertRaises(ValueError):
            service_from_dict("x", {"type": "not-exist"})

    def test_builtin_missing_api_key(self):
        with self.assertRaises(ValueError):
            service_from_dict("ds", {"type": "deepseek"})
        with self.assertRaises(ValueError):
            service_from_dict("ds", {"type": "deepseek", "api_key": "env:TB_NO_SUCH_KEY_XYZ"})


class EnsureConfigFileTests(unittest.TestCase):
    def test_creates_template(self):
        # 首次启动自动生成：文件不存在时创建引导模板
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sub", "config.yaml")  # 目录也不存在
            self.assertTrue(ensure_config_file(path))
            self.assertTrue(os.path.exists(path))
            content = Path(path).read_text(encoding="utf-8")
            self.assertIn("在这里填你的密钥", content)
            self.assertIn("deepseek", content)
            # 生成的模板必须能被正常解析（全部内置平台，newapi/oneapi 注释不加载）
            cfg = load_config(path)
            self.assertEqual(len(cfg.services), 10)
            self.assertIn("deepseek", [s.name for s in cfg.services])
            self.assertIn("apimart", [s.name for s in cfg.services])

    def test_idempotent_no_overwrite(self):
        # 已存在的文件不会被覆盖（幂等）
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# 用户已填写的配置\nservices: {}\n")
            self.assertFalse(ensure_config_file(path))
            content = Path(path).read_text(encoding="utf-8")
            self.assertNotIn("在这里填你的密钥", content)
            self.assertIn("用户已填写", content)

    def test_template_parses_as_yaml(self):
        # 模板本身是合法 YAML（防手误破坏模板）
        import yaml
        from token_balance.config import CONFIG_TEMPLATE
        data = yaml.safe_load(CONFIG_TEMPLATE)
        self.assertIn("services", data)
        self.assertIn("deepseek", data["services"])


class LoadConfigTests(unittest.TestCase):
    def test_load_yaml(self):
        content = """
timeout: 5
concurrency: 3
services:
  ds:
    type: deepseek
    api_key: env:TB_TEST_DS_KEY
  bad:
    type: not-exist
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            os.environ["TB_TEST_DS_KEY"] = "sk-abc"
            cfg = load_config(path)
            del os.environ["TB_TEST_DS_KEY"]
        self.assertEqual(cfg.timeout, 5)
        self.assertEqual(cfg.concurrency, 3)
        self.assertEqual(len(cfg.services), 1)
        self.assertEqual(cfg.services[0].api_key, "sk-abc")
        self.assertEqual(len(cfg.errors), 1)
        self.assertIn("未知类型", cfg.errors[0])


if __name__ == "__main__":
    unittest.main()