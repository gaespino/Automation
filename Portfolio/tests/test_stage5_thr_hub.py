"""
test_stage5_thr_hub.py
Stage 5: THR Tools hub — React SPA structure and REST API routers registered.
Old Dash thr-tools pages have been removed; all tools are now served by React at /thr/.
"""
import os
import sys
import pytest

PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)

EXPECTED_REACT_PAGES = [
    "AutomationDesigner",
    "ExperimentBuilder",
    "MCAReport",
    "MCADecoder",
    "LoopParser",
    "FileHandler",
    "FrameworkReport",
    "FuseGenerator",
]

EXPECTED_REST_ROUTERS = [
    "mca",
    "loops",
    "files",
    "framework",
    "fuses",
    "experiments",
    "flow",
]


class TestReactUIStructure:
    def test_thr_ui_src_exists(self):
        assert os.path.isdir(os.path.join(PORTFOLIO_ROOT, "thr_ui", "src"))

    def test_all_react_page_folders_exist(self):
        pages_dir = os.path.join(PORTFOLIO_ROOT, "thr_ui", "src", "pages")
        for page in EXPECTED_REACT_PAGES:
            page_path = os.path.join(pages_dir, page)
            assert os.path.isdir(page_path), f"React page folder missing: {page}"

    def test_app_tsx_exists(self):
        assert os.path.exists(os.path.join(PORTFOLIO_ROOT, "thr_ui", "src", "App.tsx"))

    def test_theme_css_exists(self):
        assert os.path.exists(os.path.join(PORTFOLIO_ROOT, "thr_ui", "src", "theme.css"))

    def test_api_client_exists(self):
        assert os.path.exists(
            os.path.join(PORTFOLIO_ROOT, "thr_ui", "src", "api", "client.ts")
        )


class TestRestApiRouters:
    def test_all_rest_router_files_exist(self):
        routers_dir = os.path.join(PORTFOLIO_ROOT, "api", "routers")
        for router in EXPECTED_REST_ROUTERS:
            path = os.path.join(routers_dir, f"{router}.py")
            assert os.path.exists(path), f"REST router missing: {router}.py"

    def test_all_routers_importable(self):
        import importlib
        for router in EXPECTED_REST_ROUTERS:
            mod = importlib.import_module(f"api.routers.{router}")
            assert hasattr(mod, "router"), f"api.routers.{router} has no 'router' attribute"

    def test_api_main_includes_all_routers(self):
        main_path = os.path.join(PORTFOLIO_ROOT, "api", "main.py")
        content = open(main_path).read()
        for router in EXPECTED_REST_ROUTERS:
            assert router in content, f"api/main.py does not include router: {router}"


class TestOldDashPagesRemoved:
    def test_thr_tools_dash_folder_removed(self):
        """pages/thr_tools/ must not exist -- those Dash pages are replaced by React."""
        thr_tools_path = os.path.join(PORTFOLIO_ROOT, "pages", "thr_tools")
        assert not os.path.exists(thr_tools_path), (
            "pages/thr_tools/ still exists -- old Dash THR Tools pages must be removed"
        )
