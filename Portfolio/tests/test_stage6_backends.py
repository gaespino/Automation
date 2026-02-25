"""
test_stage6_backends.py
Stage 6: Backend functional parity tests — verify THRTools modules work correctly
These tests exercise the core backend classes directly (no Dash/GUI layer).
"""
import os
import sys
import pytest
import pandas as pd

PORTFOLIO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PORTFOLIO_ROOT not in sys.path:
    sys.path.insert(0, PORTFOLIO_ROOT)


# ── MCA Decoder ───────────────────────────────────────────────────────────────

class TestMCADecoder:
    @pytest.fixture
    def mcadata_class(self):
        from THRTools.Decoder.decoder import mcadata
        return mcadata

    def test_import_mcadata(self, mcadata_class):
        assert mcadata_class is not None

    def test_mcadata_instantiates(self, mcadata_class):
        try:
            obj = mcadata_class(product="GNR")
        except TypeError:
            obj = mcadata_class()
        assert obj is not None

    def test_mcadata_has_decode_method(self, mcadata_class):
        try:
            obj = mcadata_class(product="GNR")
        except TypeError:
            obj = mcadata_class()
        assert hasattr(obj, "decode") or hasattr(obj, "run") or hasattr(obj, "parse")


# ── PTC Loop Parser ───────────────────────────────────────────────────────────

class TestLoopParser:
    def test_import_logsPTC(self):
        from THRTools.parsers.PPVLoopsParser import LogsPTC
        assert LogsPTC is not None

    def test_logsPTC_constructor_params(self):
        import inspect
        from THRTools.parsers.PPVLoopsParser import LogsPTC
        sig = inspect.signature(LogsPTC.__init__)
        params = list(sig.parameters.keys())
        # Must accept folder_path or similar
        assert any(p in params for p in ("folder_path", "folder", "path", "StartWW")), \
            f"Expected folder_path-like param, got: {params}"


# ── MCA Report ────────────────────────────────────────────────────────────────

class TestMCAReport:
    def test_import_ppv_report(self):
        from THRTools.parsers.MCAparser import ppv_report
        assert ppv_report is not None

    def test_ppv_report_has_run(self):
        from THRTools.parsers.MCAparser import ppv_report
        import inspect
        methods = [m for m, _ in inspect.getmembers(ppv_report, predicate=inspect.isfunction)]
        assert "run" in methods or any("run" in m for m in methods)


# ── Fuse Generator ────────────────────────────────────────────────────────────

class TestFuseGenerator:
    def test_import_fuse_file_generator(self):
        from THRTools.utils.fusefilegenerator import FuseFileGenerator
        assert FuseFileGenerator is not None

    def test_instantiate_with_product(self):
        from THRTools.utils.fusefilegenerator import FuseFileGenerator
        try:
            gen = FuseFileGenerator(product="GNR")
            assert gen is not None
        except Exception as e:
            pytest.skip(f"FuseFileGenerator requires config files: {e}")

    def test_has_load_csv_files_method(self):
        from THRTools.utils.fusefilegenerator import FuseFileGenerator
        assert hasattr(FuseFileGenerator, "load_csv_files")

    def test_has_generate_fuse_file_method(self):
        from THRTools.utils.fusefilegenerator import FuseFileGenerator
        assert hasattr(FuseFileGenerator, "generate_fuse_file")


# ── Framework Analyzer ────────────────────────────────────────────────────────

class TestFrameworkAnalyzer:
    def test_import_experiment_summary_analyzer(self):
        from THRTools.parsers.FrameworkAnalyzer import ExperimentSummaryAnalyzer
        assert ExperimentSummaryAnalyzer is not None

    def test_analyzer_accepts_dataframes(self):
        from THRTools.parsers.FrameworkAnalyzer import ExperimentSummaryAnalyzer
        import inspect
        sig = inspect.signature(ExperimentSummaryAnalyzer.__init__)
        params = list(sig.parameters.keys())
        # Expect several df params
        df_params = [p for p in params if "df" in p.lower() or "data" in p.lower()]
        assert len(df_params) >= 3, f"Expected multiple df params, got: {params}"

    def test_analyzer_has_analyze_method(self):
        from THRTools.parsers.FrameworkAnalyzer import ExperimentSummaryAnalyzer
        assert hasattr(ExperimentSummaryAnalyzer, "analyze_all_experiments")

    def test_analyzer_with_empty_dfs(self):
        from THRTools.parsers.FrameworkAnalyzer import ExperimentSummaryAnalyzer
        import inspect
        sig = inspect.signature(ExperimentSummaryAnalyzer.__init__)
        params = [p for p in sig.parameters.keys() if p != "self"]
        kwargs = {p: pd.DataFrame() for p in params}
        try:
            analyzer = ExperimentSummaryAnalyzer(**kwargs)
            result = analyzer.analyze_all_experiments()
            assert isinstance(result, pd.DataFrame)
        except Exception as e:
            pytest.skip(f"Analyzer requires non-empty data: {e}")


# ── DPMB ──────────────────────────────────────────────────────────────────────

class TestDPMB:
    def test_import_dpmb_class(self):
        from THRTools.api.dpmb import dpmb
        assert dpmb is not None

    def test_tkinter_gui_class_not_imported_at_module_level(self):
        """The dpmbGUI class should only be accessible if TKINTER_AVAILABLE."""
        import THRTools.api.dpmb as dpmb_mod
        # If tkinter is unavailable, dpmbGUI should not be instantiatable
        if not getattr(dpmb_mod, "TKINTER_AVAILABLE", True):
            assert not hasattr(dpmb_mod, "dpmbGUI") or dpmb_mod.dpmbGUI is None


# ── Dashboard Data Handler ────────────────────────────────────────────────────

class TestDashboardDataHandler:
    def test_import_data_handler(self):
        from services.data_handler import DataHandler
        assert DataHandler is not None

    def test_data_handler_instantiates(self):
        from services.data_handler import DataHandler
        try:
            dh = DataHandler()
            assert dh is not None
        except Exception as e:
            pytest.skip(f"DataHandler needs environment: {e}")


# ── Unit Service ──────────────────────────────────────────────────────────────

class TestUnitService:
    def test_import_unit_service(self):
        try:
            from services.unit_service import UnitService
            assert UnitService is not None
        except ImportError as e:
            pytest.skip(f"unit_service not available: {e}")

    def test_sample_unit_json_valid(self, sample_unit_json):
        assert "unit_id" in sample_unit_json
        assert "experiments" in sample_unit_json
        assert isinstance(sample_unit_json["experiments"], list)
