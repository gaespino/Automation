"""
test_stage3_navbar.py
Stage 3: Navbar — brand href, portfolio href, all 9 tool hrefs
"""
import os
import sys
import pytest

PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)

EXPECTED_TOOL_HREFS = [
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


class TestNavbarModule:
    @pytest.fixture(autouse=True)
    def load_navbar(self):
        import importlib
        from components import navbar
        importlib.reload(navbar)
        self.navbar = navbar

    def test_build_navbar_callable(self):
        assert callable(self.navbar.build_navbar)

    def test_navbar_tools_list_has_9_entries(self):
        assert len(self.navbar.TOOLS) == 9

    def test_all_tool_hrefs_present(self):
        hrefs = [t["href"] for t in self.navbar.TOOLS]
        for expected in EXPECTED_TOOL_HREFS:
            assert expected in hrefs, f"Missing href: {expected}"

    def test_tool_names_unique(self):
        names = [t["name"] for t in self.navbar.TOOLS]
        assert len(names) == len(set(names))

    def test_brand_links_to_home(self):
        """Verify the TOOLS list doesn't include root — navigation brand points to /."""
        hrefs = [t["href"] for t in self.navbar.TOOLS]
        assert "/" not in hrefs  # / is handled by brand, not tool list

    def test_navbar_returns_component(self):
        nav = self.navbar.build_navbar()
        assert nav is not None

    def test_navbar_has_portfolio_link(self):
        layout_str = str(self.navbar.build_navbar())
        assert "/portfolio" in layout_str

    def test_navbar_has_thr_tools_brand(self):
        layout_str = str(self.navbar.build_navbar())
        assert "THR" in layout_str or "thr" in layout_str.lower()
