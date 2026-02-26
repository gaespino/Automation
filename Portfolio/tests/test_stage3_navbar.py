"""
test_stage3_navbar.py
Stage 3: Navbar — brand href, portfolio href, THR Tools link to React SPA.
The old per-tool dropdown links have been replaced with a single /thr/ link.
"""
import os
import sys
import pytest

PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)


class TestNavbarModule:
    @pytest.fixture(autouse=True)
    def load_navbar(self):
        import importlib
        from components import navbar
        importlib.reload(navbar)
        self.navbar = navbar

    def test_build_navbar_callable(self):
        assert callable(self.navbar.build_navbar)

    def test_navbar_returns_component(self):
        nav = self.navbar.build_navbar()
        assert nav is not None

    def test_navbar_has_portfolio_link(self):
        layout_str = str(self.navbar.build_navbar())
        assert "/portfolio" in layout_str

    def test_navbar_links_to_thr_react_spa(self):
        """Navbar must link to /thr/ (React SPA), not the old /thr-tools/ Dash pages."""
        layout_str = str(self.navbar.build_navbar())
        assert "/thr/" in layout_str

    def test_navbar_has_no_old_thr_tools_links(self):
        """Individual /thr-tools/* Dash links must not appear in the navbar."""
        layout_str = str(self.navbar.build_navbar())
        assert "/thr-tools/" not in layout_str

    def test_navbar_has_brand(self):
        layout_str = str(self.navbar.build_navbar())
        assert "Portfolio" in layout_str or "THR" in layout_str
