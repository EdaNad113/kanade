"""Regression test: every API path used by mcp-1panel tools must exist in the
bundled 1Panel swagger (agent/tools/MCP/docs/api-swagger.json).

Run: pytest tests/ -v
"""
import glob
import json
import os
import re

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SWAGGER = os.path.normpath(os.path.join(TESTS_DIR, "..", "..", "docs", "api-swagger.json"))
TOOLS_DIR = os.path.normpath(os.path.join(TESTS_DIR, "..", "src", "mcp_1panel", "tools"))


def _norm(path):
    """Normalize a path: drop query string, convert {param} / :param to :p."""
    path = path.split("?")[0]
    path = re.sub(r"\{[^}]*\}", ":p", path)
    path = re.sub(r":[a-zA-Z_]+", ":p", path)
    return path


def _loose_match(path, swagger_path):
    """Match path against a swagger path where ':p' segments accept any value."""
    a, b = path.split("/"), swagger_path.split("/")
    if len(a) != len(b):
        return False
    return all(x == y or y == ":p" for x, y in zip(a, b))


@pytest.fixture(scope="module")
def swagger_paths():
    if not os.path.exists(SWAGGER):
        pytest.skip("api-swagger.json not found; skipping endpoint alignment test")
    with open(SWAGGER, encoding="utf-8") as f:
        data = json.load(f)
    return {_norm(p) for p in data.get("paths", {})}


@pytest.fixture(scope="module")
def tool_paths():
    """tool_name -> list of normalized API paths used in its body."""
    result = {}
    call_re = re.compile(r"\bp\.(get|post|put|delete)\(\s*f?([\"'])(.*?)\2", re.S)
    name_re = re.compile(r"def (panel_\w+)\(")
    for f in sorted(glob.glob(os.path.join(TOOLS_DIR, "*.py"))):
        text = open(f, encoding="utf-8").read()
        # assign each API call to the tool function that contains it
        chunks = []  # (tool_name_or_None, start, end)
        for m in name_re.finditer(text):
            chunks.append((m.group(1), m.start(), m.end()))
        chunks.append((None, len(text), len(text)))
        for i in range(len(chunks) - 1):
            tool_name = chunks[i][0]
            body = text[chunks[i][2]:chunks[i + 1][1]]
            paths = result.setdefault(tool_name, [])
            for m in call_re.finditer(body):
                p = _norm(m.group(3))
                if p.startswith("/"):
                    paths.append(p)
    return result


def test_all_tool_paths_exist_in_swagger(swagger_paths, tool_paths):
    missing = []
    for tool_name, paths in tool_paths.items():
        for p in sorted(set(paths)):
            if not any(_loose_match(p, s) for s in swagger_paths):
                missing.append(f"{tool_name}: {p}")
    assert not missing, "工具端点不在 Swagger 中:\n" + "\n".join(missing)


def test_tool_count():
    """Sanity: still 199 tools."""
    names = set()
    for f in glob.glob(os.path.join(TOOLS_DIR, "*.py")):
        text = open(f, encoding="utf-8").read()
        names.update(re.findall(r"def (panel_\w+)\(", text))
    assert len(names) == 199
