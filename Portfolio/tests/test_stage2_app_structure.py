"""
test_stage2_app_structure.py
Stage 2: App structure — page registry, expected routes, layout elements
"""
import os
import sys
import pytest

PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)

EXPECTED_PATHS = [
    "/",
    "/portfolio",
    "/thr-tools",
    "/thr-tools/mca-decoder",
    "/thr-tools/mca-report",
    "/thr-tools/loop-parser",
    "/thr-tools/dpmb",
    "/thr-tools/file-handler",
    "/thr-tools/fuse-generator",
    "/thr-tools/framework-report",
    "/thr-tools/experiment-builder",
    "/thr-tools/automation-designer",
]


class TestPageRegistry:
    @pytest.fixture(autouse=True)
    def load_app(self):
        import importlib
        import app as app_module
        importlib.reload(app_module)
        self.app = app_module.app

    def test_dash_app_has_use_pages(self):
        assert self.app.config.get("pages_folder") == "pages"

    def test_all_expected_pages_registered(self):
        import dash
        registered = {p["path"] for p in dash.page_registry.values()}
        for path in EXPECTED_PATHS:
            assert path in registered, f"Missing page: {path}"

    def test_app_layout_has_page_container(self):
        from dash import page_container
        layout_str = str(self.app.layout)
        assert "page-content" in layout_str or "pages" in layout_str.lower()


class TestAppFiles:
    def test_app_py_exists(self):
        assert os.path.exists(os.path.join(PORTFOLIO_ROOT, "app.py"))

    def test_config_py_exists(self):
        assert os.path.exists(os.path.join(PORTFOLIO_ROOT, "config.py"))

    def test_requirements_txt_has_gunicorn(self):
        req_path = os.path.join(PORTFOLIO_ROOT, "requirements.txt")
        content = open(req_path).read()
        assert "gunicorn" in content

    def test_requirements_txt_has_dash(self):
        req_path = os.path.join(PORTFOLIO_ROOT, "requirements.txt")
        content = open(req_path).read()
        assert "dash" in content
