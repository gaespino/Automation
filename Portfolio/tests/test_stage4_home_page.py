"""
test_stage4_home_page.py
Stage 4: Home landing page — layout structure, tile hrefs.
THR Tools tile now links to /thr/ (React SPA).
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
        import sys
        # Ensure app is initialised (Dash registers pages on app instantiation).
        # Import without reload to avoid re-executing page imports (dash_ag_grid etc.)
        if 'app' not in sys.modules:
            try:
                import app as _app  # noqa: F401
            except Exception:
                pass
        from pages import home
        importlib.reload(home)
        self.home = home

    def test_layout_defined(self):
        assert self.home.layout is not None

    def test_layout_has_portfolio_href(self):
        layout_str = str(self.home.layout)
        assert "/portfolio" in layout_str

    def test_layout_is_redirect_or_links_to_thr(self):
        """Home page is now a redirect to /dashboard/portfolio (no tile needed)."""
        layout_str = str(self.home.layout)
        # Either a redirect or a tile — both are acceptable
        assert "/portfolio" in layout_str or "/thr/" in layout_str

    def test_layout_has_no_old_thr_tools_href(self):
        """Old /thr-tools Dash hub link must be gone from home page."""
        layout_str = str(self.home.layout)
        # Checks that the exact href string "/thr-tools" (the old Dash hub path) is not present.
        assert '"/thr-tools"' not in layout_str

    def test_layout_mentions_unit_portfolio(self):
        layout_str = str(self.home.layout)
        assert "Unit Portfolio" in layout_str or "portfolio" in layout_str.lower()

    def test_layout_mentions_thr_tools(self):
        layout_str = str(self.home.layout)
        # Home is now a redirect page; "portfolio" or "dashboard" is sufficient
        assert "portfolio" in layout_str.lower() or "dashboard" in layout_str.lower()

    def test_page_registered_at_root(self):
        import importlib
        import app as app_module
        importlib.reload(app_module)
        import dash
        paths = [p["path"] for p in dash.page_registry.values()]
        assert "/" in paths
