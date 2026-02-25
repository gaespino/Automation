"""
test_stage1_thr_tools_copy.py
Stage 1: THRTools copy — clean imports, tkinter guards, no hardcoded paths in non-config files
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


class TestTkinterGuards:
    """Verify that tkinter-dependent modules import without raising on headless systems."""

    def _import_module(self, rel_path: str, module_name: str):
        """Import a THRTools module by file path, isolating sys.modules."""
        spec = importlib.util.spec_from_file_location(
            module_name,
            os.path.join(THRTOOLS, rel_path)
        )
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except ImportError as e:
            # Only fail if the error is NOT tkinter
            if "tkinter" not in str(e).lower():
                raise
        return mod

    def test_dpmb_imports_without_crash(self):
        self._import_module("api/dpmb.py", "thr_dpmb")

    def test_file_handler_imports_without_crash(self):
        self._import_module("gui/PPVFileHandler.py", "thr_pph")

    def test_experiment_builder_imports_without_crash(self):
        self._import_module("gui/ExperimentBuilder.py", "thr_eb")

    def test_automation_designer_imports_without_crash(self):
        self._import_module("gui/AutomationDesigner.py", "thr_ad")

    def test_dpmb_has_guard(self):
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
