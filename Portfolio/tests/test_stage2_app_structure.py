"""
test_stage2_app_structure.py
Stage 2: App structure — page registry, expected routes, layout elements.
THR Tools pages are now served by React at /thr/ — only Dashboard pages remain in Dash.
"""
import os
import sys
import pytest

PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)

# Dashboard Dash pages only — THR Tools are now React pages at /thr/
EXPECTED_DASH_PATHS = [
    "/",
    "/portfolio",
]


class TestPageRegistry:
    @pytest.fixture(autouse=True)
    def load_app(self):
        import importlib
        import app as app_module
        importlib.reload(app_module)
        self.app = app_module.app

    def test_dash_app_has_use_pages(self):
        pages_folder = self.app.config.get("pages_folder") or ""
        assert str(pages_folder).endswith("pages"), (
            f"Expected pages_folder to end with 'pages', got: {pages_folder!r}"
        )

    def test_dashboard_pages_registered(self):
        import dash
        registered = {p["path"] for p in dash.page_registry.values()}
        for path in EXPECTED_DASH_PATHS:
            assert path in registered, f"Missing dashboard page: {path}"

    def test_no_thr_tools_in_dash_registry(self):
        """THR Tools are now React pages -- must not appear in the Dash page registry."""
        import dash
        registered = {p["path"] for p in dash.page_registry.values()}
        thr_paths = [p for p in registered if p.startswith("/thr-tools")]
        assert thr_paths == [], f"Old thr-tools pages still in Dash registry: {thr_paths}"

    def test_app_layout_has_page_container(self):
        layout_str = str(self.app.layout)
        assert "page-content" in layout_str or "pages" in layout_str.lower()


class TestAppFiles:
    def test_app_py_exists(self):
        assert os.path.exists(os.path.join(PORTFOLIO_ROOT, "app.py"))

    def test_config_py_exists(self):
        assert os.path.exists(os.path.join(PORTFOLIO_ROOT, "config.py"))

    def test_api_main_exists(self):
        """FastAPI entry point must exist."""
        assert os.path.exists(os.path.join(PORTFOLIO_ROOT, "api", "main.py"))

    def test_thr_ui_package_json_exists(self):
        """React frontend must have a package.json."""
        assert os.path.exists(os.path.join(PORTFOLIO_ROOT, "thr_ui", "package.json"))

    def test_requirements_txt_has_fastapi(self):
        req_path = os.path.join(PORTFOLIO_ROOT, "requirements.txt")
        content = open(req_path).read()
        assert "fastapi" in content

    def test_requirements_txt_has_uvicorn(self):
        req_path = os.path.join(PORTFOLIO_ROOT, "requirements.txt")
        content = open(req_path).read()
        assert "uvicorn" in content

    def test_requirements_txt_has_dash(self):
        req_path = os.path.join(PORTFOLIO_ROOT, "requirements.txt")
        content = open(req_path).read()
        assert "dash" in content

    def test_run_app_bat_uses_uvicorn(self):
        """run_app.bat must launch uvicorn, not the old python app.py."""
        bat_path = os.path.join(PORTFOLIO_ROOT, "run_app.bat")
        content = open(bat_path).read()
        assert "uvicorn" in content
        assert "python app.py" not in content
