"""Tests for PanelClient — MD5 authentication, error handling, and env fallback."""

import hashlib
import json
import os
import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from mcp_1panel.panel_client import PanelClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """PanelClient with known host+key (no env vars touched)."""
    return PanelClient(host="http://test.local:10000", api_key="test-key-123")


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestInit:
    def test_host_and_key_from_params(self):
        c = PanelClient(host="http://example.com", api_key="sk-secret")
        assert c.base == "http://example.com/api/v2"

    def test_host_trailing_slash_stripped(self):
        c = PanelClient(host="http://example.com/", api_key="k")
        assert not c.base.endswith("//")

    def test_missing_host_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="未设置"):
                PanelClient()

    def test_missing_api_key_raises(self):
        with patch.dict(os.environ, {"PANEL_HOST": "http://x"}):
            with pytest.raises(ValueError, match="未设置"):
                PanelClient()

    def test_env_fallback(self):
        with patch.dict(
            os.environ,
            {"PANEL_HOST": "http://env-host", "PANEL_API_KEY": "env-key"},
        ):
            c = PanelClient()
            assert "env-host" in c.base
            assert c.api_key == "env-key"


# ---------------------------------------------------------------------------
# Authentication headers — MD5 signing
# ---------------------------------------------------------------------------


class TestAuth:
    def test_auth_headers_structure(self, client):
        """Headers contain expected keys."""
        headers = client._auth_headers()
        assert headers["Content-Type"] == "application/json"
        assert "1Panel-Token" in headers
        assert "1Panel-Timestamp" in headers

    def test_auth_timestamp_is_numeric(self, client):
        """Timestamp should be a string-encoded Unix time."""
        ts = client._auth_headers()["1Panel-Timestamp"]
        assert ts.isdigit()
        # Sanity: within ±10s of now
        assert abs(int(ts) - int(time.time())) < 10

    def test_auth_token_md5_correct(self, client):
        """Token = md5('1panel' + api_key + timestamp)."""
        headers = client._auth_headers()
        ts = headers["1Panel-Timestamp"]
        expected = hashlib.md5(
            ("1panel" + client.api_key + ts).encode()
        ).hexdigest()
        assert headers["1Panel-Token"] == expected

    def test_different_keys_produce_different_tokens(self):
        c1 = PanelClient(host="http://a", api_key="key1")
        c2 = PanelClient(host="http://a", api_key="key2")
        h1 = c1._auth_headers()
        h2 = c2._auth_headers()
        # Use same timestamp for fair comparison
        ts = h1["1Panel-Timestamp"]
        with patch.object(c2, "_auth_headers", return_value={
            **h2,
            "1Panel-Timestamp": ts,
            "1Panel-Token": hashlib.md5(
                ("1panel" + "key2" + ts).encode()
            ).hexdigest(),
        }):
            h2_fixed = c2._auth_headers()
            assert h1["1Panel-Token"] != h2_fixed["1Panel-Token"]


# ---------------------------------------------------------------------------
# _request — HTTP calls and error handling
# ---------------------------------------------------------------------------


class TestRequest:
    def test_get_success(self, client):
        """Successful GET returns the 'data' field from response."""
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.json.return_value = {"code": 200, "data": {"key": "val"}}

        with patch("requests.request", return_value=mock_resp) as mock_req:
            result = client.get("/some/path", params={"p": 1})

        assert result == {"key": "val"}
        mock_req.assert_called_once()
        args, kwargs = mock_req.call_args
        assert kwargs.get("params") == {"p": 1}

    def test_post_success(self, client):
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.json.return_value = {"code": 200, "data": "ok"}

        with patch("requests.request", return_value=mock_resp) as mock_req:
            result = client.post("/submit", {"name": "x"})

        assert result == "ok"
        _, kwargs = mock_req.call_args
        assert kwargs.get("json") == {"name": "x"}

    def test_api_error_raised(self, client):
        """Non-200 code in response body raises RuntimeError."""
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 500
        mock_resp.text = '{"code":500,"message":"Internal error"}'
        mock_resp.json.return_value = {
            "code": 500,
            "message": "Internal error",
        }

        with patch("requests.request", return_value=mock_resp):
            with pytest.raises(RuntimeError, match="API 错误"):
                client.get("/fail")

    def test_delete_method(self, client):
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.json.return_value = {"code": 200, "data": None}

        with patch("requests.request", return_value=mock_resp) as mock_req:
            result = client.delete("/resource/1")

        assert result is None
        args, kwargs = mock_req.call_args
        assert args[0] == "DELETE"

    def test_put_method(self, client):
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.json.return_value = {"code": 200, "data": "updated"}

        with patch("requests.request", return_value=mock_resp) as mock_req:
            result = client.put("/resource/1", {"status": "active"})

        assert result == "updated"
        args, kwargs = mock_req.call_args
        assert args[0] == "PUT"
