"""
test_stage1_thr_tools_copy.py
Stage 1: THRTools — backend modules exist, no tkinter at package level,
no hardcoded production paths.

All tkinter/desktop GUI code has been removed from Portfolio/THRTools/.
The Dash pages in Portfolio/pages/thr_tools/ are the only UI layer.
"""
import os
import sys
import importlib
import pytest

PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)

THRTOOLS = os.path.join(PORTFOLIO_ROOT, "THRTools")


class TestTHRToolsExists:
    def test_thrtools_dir_exists(self):
        assert os.path.isdir(THRTOOLS)

    def test_decoder_module_exists(self):
        assert os.path.exists(os.path.join(THRTOOLS, "Decoder", "decoder.py"))

    def test_mca_parser_exists(self):
        assert os.path.exists(os.path.join(THRTOOLS, "parsers", "MCAparser.py"))

    def test_loops_parser_exists(self):
        assert os.path.exists(os.path.join(THRTOOLS, "parsers", "PPVLoopsParser.py"))

    def test_fuse_generator_exists(self):
        assert os.path.exists(os.path.join(THRTOOLS, "utils", "fusefilegenerator.py"))

    def test_framework_analyzer_exists(self):
        assert os.path.exists(os.path.join(THRTOOLS, "parsers", "FrameworkAnalyzer.py"))

    def test_dpmb_module_exists(self):
        assert os.path.exists(os.path.join(THRTOOLS, "api", "dpmb.py"))

    def test_gui_folder_removed(self):
        """Verify the tkinter GUI folder has been fully removed (no desktop GUI in CaaS)."""
        assert not os.path.exists(os.path.join(THRTOOLS, "gui")), (
            "THRTools/gui/ should be removed — Dash pages replace desktop GUIs"
        )


class TestNoTkinterAtPackageLevel:
    """THRTools __init__.py must not import tkinter-dependent code."""

    def test_thrtools_imports_without_crash(self):
        import importlib
        # Reload to ensure fresh import
        if "THRTools" in sys.modules:
            del sys.modules["THRTools"]
        mod = importlib.import_module("THRTools")
        assert mod is not None

    def test_dpmb_has_tkinter_guard(self):
        path = os.path.join(THRTOOLS, "api", "dpmb.py")
        content = open(path, encoding="utf-8").read()
        assert "TKINTER_AVAILABLE" in content or "ImportError" in content


class TestNoHardcodedPaths:
    """Non-config Python files in THRTools should not have the production UNC path hardcoded."""

    PRODUCTION_PATH_FRAGMENT = "crcv03a-cifs"

    def test_decoder_no_hardcoded_path(self):
        path = os.path.join(THRTOOLS, "Decoder", "decoder.py")
        if os.path.exists(path):
            assert self.PRODUCTION_PATH_FRAGMENT not in open(path, encoding="utf-8").read()

    def test_mca_parser_no_hardcoded_path(self):
        path = os.path.join(THRTOOLS, "parsers", "MCAparser.py")
        if os.path.exists(path):
            assert self.PRODUCTION_PATH_FRAGMENT not in open(path, encoding="utf-8").read()
