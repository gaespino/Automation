"""
test_stage4_home_page.py
Stage 4: Home landing page — layout structure, tile hrefs
"""
import os
import sys
import pytest

PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)


class TestHomePage:
    @pytest.fixture(autouse=True)
    def load_home(self):
        import importlib
        from pages import home
        importlib.reload(home)
        self.home = home

    def test_layout_defined(self):
        assert self.home.layout is not None

    def test_layout_is_not_none(self):
        assert self.home.layout is not None

    def test_layout_has_portfolio_href(self):
        layout_str = str(self.home.layout)
        assert "/portfolio" in layout_str

    def test_layout_has_thr_tools_href(self):
        layout_str = str(self.home.layout)
        assert "/thr-tools" in layout_str

    def test_layout_mentions_unit_portfolio(self):
        layout_str = str(self.home.layout)
        assert "Unit Portfolio" in layout_str or "portfolio" in layout_str.lower()

    def test_layout_mentions_thr_tools(self):
        layout_str = str(self.home.layout)
        assert "THR" in layout_str or "thr" in layout_str.lower()

    def test_page_registered_at_root(self):
        import importlib
        import app as app_module
        importlib.reload(app_module)
        import dash
        paths = [p["path"] for p in dash.page_registry.values()]
        assert "/" in paths
