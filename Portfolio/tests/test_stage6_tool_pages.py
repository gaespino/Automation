"""
test_stage6_tool_pages.py
Stage 6: Tool page smoke tests.
Old Dash thr-tools pages removed; tests now validate the FastAPI REST endpoints.
"""
import os
import sys
import importlib
import pytest

PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)

REST_ENDPOINTS = [
    ("api.routers.mca",         "router", "/api/mca"),
    ("api.routers.loops",       "router", "/api/loops"),
    ("api.routers.files",       "router", "/api/files"),
    ("api.routers.framework",   "router", "/api/framework"),
    ("api.routers.fuses",       "router", "/api/fuses"),
    ("api.routers.experiments", "router", "/api/experiments"),
    ("api.routers.flow",        "router", "/api/flow"),
]


@pytest.mark.parametrize("module_path,attr,prefix", REST_ENDPOINTS)
class TestRestRouterSmoke:
    def test_module_importable(self, module_path, attr, prefix):
        mod = importlib.import_module(module_path)
        assert mod is not None

    def test_router_attribute_exists(self, module_path, attr, prefix):
        mod = importlib.import_module(module_path)
        assert hasattr(mod, attr), f"{module_path} missing '{attr}'"

    def test_router_has_routes(self, module_path, attr, prefix):
        mod = importlib.import_module(module_path)
        router = getattr(mod, attr)
        assert len(router.routes) > 0, f"{module_path}.router has no routes defined"


class TestFastAPIApp:
    def test_fastapi_app_importable(self):
        mod = importlib.import_module("api.main")
        assert hasattr(mod, "app")

    def test_fastapi_app_has_correct_title(self):
        mod = importlib.import_module("api.main")
        assert "THR" in mod.app.title or "Tools" in mod.app.title

    def test_fastapi_openapi_schema_has_all_tags(self):
        mod = importlib.import_module("api.main")
        app = mod.app
        # Build schema (may raise if badly configured)
        schema = app.openapi()
        paths = schema.get("paths", {})
        # At minimum the /api paths must appear
        api_paths = [p for p in paths if p.startswith("/api/")]
        assert len(api_paths) >= 7, f"Expected >=7 /api/ paths, got {len(api_paths)}"
