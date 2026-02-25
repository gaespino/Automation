"""
test_stage5_thr_hub.py
Stage 5: THR Tools hub — all 9 cards present, accent colors, hrefs
"""
import os
import sys
import pytest

PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)

EXPECTED_TOOLS = [
    {"name_fragment": "MCA",          "href": "/thr-tools/mca-decoder",        "accent": "#ff6b8a"},
    {"name_fragment": "MCA Report",   "href": "/thr-tools/mca-report",         "accent": "#ff4d4d"},
    {"name_fragment": "Loop",         "href": "/thr-tools/loop-parser",        "accent": "#00d4ff"},
    {"name_fragment": "DPMB",         "href": "/thr-tools/dpmb",               "accent": "#7000ff"},
    {"name_fragment": "File",         "href": "/thr-tools/file-handler",       "accent": "#ffbd2e"},
    {"name_fragment": "Fuse",         "href": "/thr-tools/fuse-generator",     "accent": "#ff9f45"},
    {"name_fragment": "Framework",    "href": "/thr-tools/framework-report",   "accent": "#00ff9d"},
    {"name_fragment": "Experiment",   "href": "/thr-tools/experiment-builder", "accent": "#36d7b7"},
    {"name_fragment": "Automation",   "href": "/thr-tools/automation-designer","accent": "#00c9a7"},
]


class TestTHRHub:
    @pytest.fixture(autouse=True)
    def load_index(self):
        import importlib
        from pages.thr_tools import index
        importlib.reload(index)
        self.index = index
        self.layout_str = str(index.layout)

    def test_layout_defined(self):
        assert self.index.layout is not None

    def test_all_9_hrefs_present(self):
        for tool in EXPECTED_TOOLS:
            assert tool["href"] in self.layout_str, f"Missing href: {tool['href']}"

    def test_all_9_accent_colors_present(self):
        for tool in EXPECTED_TOOLS:
            assert tool["accent"] in self.layout_str, f"Missing accent color: {tool['accent']}"

    def test_thr_tools_list_length(self):
        total = len(self.index.TOOLS) + (1 if hasattr(self.index, "FULL_WIDTH_TOOL") else 0)
        assert total == 9

    def test_page_registered_at_thr_tools(self):
        import importlib
        import app as app_module
        importlib.reload(app_module)
        import dash
        paths = [p["path"] for p in dash.page_registry.values()]
        assert "/thr-tools" in paths
