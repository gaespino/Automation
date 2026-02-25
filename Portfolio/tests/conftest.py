"""
conftest.py — shared pytest fixtures for Portfolio tests
"""
import json
import os
import pytest
import sys

# Ensure Portfolio root is on the path
PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)


@pytest.fixture
def mock_config(monkeypatch):
    """Override config with test values."""
    monkeypatch.setenv("DATA_PATH", os.path.join(PORTFOLIO_ROOT, "data"))
    monkeypatch.setenv("FRAMEWORK_PATH", "/tmp/framework")
    monkeypatch.setenv("PORT", "8888")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("HOST", "127.0.0.1")
    # Re-import config after env patching
    import importlib
    import config
    importlib.reload(config)
    return config


@pytest.fixture
def sample_unit_json():
    """Minimal unit JSON matching Dashboard data model."""
    return {
        "unit_id": "TEST_UNIT_001",
        "product": "GNR",
        "created": "2026-01-01T00:00:00",
        "experiments": [
            {
                "id": "exp-001",
                "name": "GNR_SLT_Test",
                "ww": "2026WW01",
                "score": 95,
                "status": "pass",
                "notes": "pytest sample",
            }
        ]
    }


@pytest.fixture
def app_client():
    """Flask test client for HTTP-level tests."""
    import importlib
    import app as app_module
    importlib.reload(app_module)
    server = app_module.server
    server.config["TESTING"] = True
    with server.test_client() as client:
        yield client
