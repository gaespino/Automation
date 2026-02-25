"""
test_stage6_tool_pages.py
Stage 6: Tool page smoke tests — each page has a layout and is registered
"""
import os
import sys
import importlib
import pytest

PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)

TOOL_PAGES = [
    ("pages.thr_tools.mca_decoder",      "/thr-tools/mca-decoder",        "MCA"),
    ("pages.thr_tools.mca_report",       "/thr-tools/mca-report",         "MCA Report"),
    ("pages.thr_tools.loop_parser",      "/thr-tools/loop-parser",        "Loop"),
    ("pages.thr_tools.dpmb",             "/thr-tools/dpmb",               "DPMB"),
    ("pages.thr_tools.file_handler",     "/thr-tools/file-handler",       "File"),
    ("pages.thr_tools.fuse_generator",   "/thr-tools/fuse-generator",     "Fuse"),
    ("pages.thr_tools.framework_report", "/thr-tools/framework-report",   "Framework"),
    ("pages.thr_tools.experiment_builder","/thr-tools/experiment-builder","Experiment"),
    ("pages.thr_tools.automation_designer","/thr-tools/automation-designer","Automation"),
]


@pytest.mark.parametrize("module_path,expected_path,name_hint", TOOL_PAGES)
class TestToolPageSmoke:
    def test_module_importable(self, module_path, expected_path, name_hint):
        mod = importlib.import_module(module_path)
        assert mod is not None

    def test_layout_exists(self, module_path, expected_path, name_hint):
        mod = importlib.import_module(module_path)
        assert hasattr(mod, "layout"), f"{module_path} missing 'layout'"

    def test_layout_is_not_none(self, module_path, expected_path, name_hint):
        mod = importlib.import_module(module_path)
        assert mod.layout is not None

    def test_layout_has_download_component(self, module_path, expected_path, name_hint):
        mod = importlib.import_module(module_path)
        # layout may be a Dash component or a callable (function) — handle both
        layout_val = mod.layout() if callable(mod.layout) else mod.layout
        layout_str = str(layout_val)
        assert "Download" in layout_str or "download" in layout_str

    def test_page_path_registered(self, module_path, expected_path, name_hint):
        # Load all pages via app
        import app as app_module
        importlib.reload(app_module)
        import dash
        paths = [p["path"] for p in dash.page_registry.values()]
        assert expected_path in paths, f"Path not registered: {expected_path}"

    def test_title_contains_hint(self, module_path, expected_path, name_hint):
        import dash
        page = next(
            (p for p in dash.page_registry.values() if p["path"] == expected_path),
            None
        )
        if page:
            assert (name_hint.lower() in page.get("title", "").lower() or
                    name_hint.lower() in page.get("name", "").lower())
