"""
test_stage0_caas_config.py
Stage 0: CaaS foundations — env-var config, /health endpoint, server instance
"""
import os
import sys
import pytest

PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)


class TestEnvVarConfig:
    def test_data_path_default_exists(self):
        import config
        assert config.PRODUCTS_DIR is not None

    def test_port_is_integer(self):
        import config
        assert isinstance(config.PORT, int)

    def test_port_env_override(self, monkeypatch):
        monkeypatch.setenv("PORT", "9999")
        import importlib
        import config
        importlib.reload(config)
        assert config.PORT == 9999

    def test_debug_is_bool(self):
        import config
        assert isinstance(config.DEBUG, bool)

    def test_host_has_value(self):
        import config
        assert config.HOST

    def test_framework_path_set(self):
        import config
        assert config.FRAMEWORK_PATH is not None

    def test_log_level_valid(self):
        import config
        assert config.LOG_LEVEL in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    def test_thrtools_dir_defined(self):
        import config
        assert hasattr(config, "THRTOOLS_DIR")


class TestHealthEndpoint:
    def test_health_returns_200(self, app_client):
        resp = app_client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_ok_body(self, app_client):
        resp = app_client.get("/health")
        assert b"OK" in resp.data or b"ok" in resp.data.lower()


class TestServerInstance:
    def test_server_is_flask_app(self):
        import app as app_module
        from flask import Flask
        assert isinstance(app_module.server, Flask)

    def test_dash_app_has_server(self):
        import app as app_module
        assert app_module.server is app_module.app.server
