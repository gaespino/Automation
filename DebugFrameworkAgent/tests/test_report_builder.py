"""
tests/test_report_builder.py — Tests for _core/report_builder.py and exporter.write_report().
"""
from __future__ import annotations
import json
import pathlib
import sys
import tempfile

import pytest

# Make scripts/ importable
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from _core import report_builder, exporter


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def minimal_exp():
    return {
        "Test Name":  "Baseline Test",
        "Test Mode":  "mesh",
        "Test Type":  "Standard",
        "Content":    "PYSVConsole",
        "COM Port":   "COM3",
        "IP Address": "192.168.1.10",
        "Loops":      5,
        "Reset":      True,
        "Scripts File": "run_test.py",
    }


@pytest.fixture
def dragon_exp():
    return {
        "Test Name":            "Dragon Run",
        "Test Mode":            "mesh",
        "Test Type":            "Standard",
        "Content":              "Dragon",
        "COM Port":             "COM4",
        "Loops":                3,
        "ULX Path":             "C:\\ulx\\test.ulx",
        "Dragon Content Path":  "C:\\dragon\\content.py",
        "Dragon Content Line":  "run_dragon()",
        "Startup Dragon":       True,
        "Product Chop":         "GNR",
        "VVAR0":                "0.85",
    }


@pytest.fixture
def linux_exp():
    return {
        "Test Name":        "Linux Boot",
        "Test Mode":        "boot",
        "Test Type":        "Standard",
        "Content":          "Linux",
        "Linux Path":       "/home/user/test.sh",
        "Linux Pass String": "TEST PASSED",
        "Linux Fail String": "FAIL",
        "Startup Linux":    True,
    }


@pytest.fixture
def shmoo_exp():
    return {
        "Test Name":   "Voltage Shmoo",
        "Test Mode":   "mesh",
        "Test Type":   "Shmoo",
        "Content":     "Dragon",
        "ShmooFile":   "v_shmoo.json",
        "ShmooLabel":  "VCC_0",
    }


@pytest.fixture
def validation_pass():
    return (True, [], [])


@pytest.fixture
def validation_fail():
    return (False, ["COM Port is required", "Test Name is empty"], ["IP Address not set"])


@pytest.fixture
def validation_warn():
    return (True, [], ["IP Address not set"])


# --------------------------------------------------------------------------
# build_markdown tests
# --------------------------------------------------------------------------

class TestBuildMarkdown:

    def test_returns_string(self, minimal_exp):
        result = report_builder.build_markdown(minimal_exp)
        assert isinstance(result, str)

    def test_contains_test_name(self, minimal_exp):
        md = report_builder.build_markdown(minimal_exp)
        assert "Baseline Test" in md

    def test_contains_product(self, minimal_exp):
        md = report_builder.build_markdown(minimal_exp, product="GNR")
        assert "GNR" in md

    def test_contains_generated_header(self, minimal_exp):
        md = report_builder.build_markdown(minimal_exp)
        assert "Experiment Report" in md

    def test_basic_settings_section(self, minimal_exp):
        md = report_builder.build_markdown(minimal_exp)
        assert "## Basic Settings" in md

    def test_connection_section(self, minimal_exp):
        md = report_builder.build_markdown(minimal_exp)
        assert "## Connection & Unit" in md
        assert "COM3" in md

    def test_dragon_section_shown_when_dragon(self, dragon_exp):
        md = report_builder.build_markdown(dragon_exp)
        assert "## Dragon Content" in md
        assert "Dragon Content Path" in md

    def test_dragon_section_hidden_when_pysv(self, minimal_exp):
        md = report_builder.build_markdown(minimal_exp)
        assert "## Dragon Content" not in md

    def test_linux_section_shown_when_linux(self, linux_exp):
        md = report_builder.build_markdown(linux_exp)
        assert "## Linux Content" in md
        assert "Linux Pass String" in md

    def test_linux_section_hidden_when_dragon(self, dragon_exp):
        md = report_builder.build_markdown(dragon_exp)
        assert "## Linux Content" not in md

    def test_shmoo_section_shown(self, shmoo_exp):
        md = report_builder.build_markdown(shmoo_exp)
        assert "## Shmoo" in md
        assert "ShmooFile" in md

    def test_pysv_section_shown(self, minimal_exp):
        md = report_builder.build_markdown(minimal_exp)
        assert "## PYSVConsole Content" in md
        assert "Scripts File" in md

    def test_validation_pass_shown(self, minimal_exp, validation_pass):
        md = report_builder.build_markdown(minimal_exp, validation_result=validation_pass)
        assert "Validation Results" in md
        assert "PASS" in md

    def test_validation_fail_shown(self, minimal_exp, validation_fail):
        md = report_builder.build_markdown(minimal_exp, validation_result=validation_fail)
        assert "Validation Results" in md
        assert "COM Port is required" in md
        assert "FAIL" in md

    def test_validation_warn_shown(self, minimal_exp, validation_warn):
        md = report_builder.build_markdown(minimal_exp, validation_result=validation_warn)
        assert "IP Address not set" in md

    def test_validation_none_skipped(self, minimal_exp):
        md = report_builder.build_markdown(minimal_exp, validation_result=None)
        assert "## Validation Results" not in md

    def test_none_values_rendered_as_dash(self):
        exp = {"Test Name": "X", "COM Port": None}
        md = report_builder.build_markdown(exp)
        assert "—" in md

    def test_bool_true_rendered_as_yes(self, dragon_exp):
        md = report_builder.build_markdown(dragon_exp)
        assert "Yes" in md

    def test_generated_by_default(self, minimal_exp):
        md = report_builder.build_markdown(minimal_exp)
        assert "DebugFrameworkAgent" in md

    def test_custom_generated_by(self, minimal_exp):
        md = report_builder.build_markdown(minimal_exp, generated_by="TestAgent v2")
        assert "TestAgent v2" in md


# --------------------------------------------------------------------------
# build_html tests
# --------------------------------------------------------------------------

class TestBuildHtml:

    def test_returns_string(self, minimal_exp):
        result = report_builder.build_html(minimal_exp)
        assert isinstance(result, str)

    def test_is_html(self, minimal_exp):
        html = report_builder.build_html(minimal_exp)
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html

    def test_contains_test_name(self, minimal_exp):
        html = report_builder.build_html(minimal_exp)
        assert "Baseline Test" in html

    def test_contains_product(self, minimal_exp):
        html = report_builder.build_html(minimal_exp, product="CWF")
        assert "CWF" in html

    def test_has_embedded_css(self, minimal_exp):
        html = report_builder.build_html(minimal_exp)
        assert "<style>" in html

    def test_print_hint_present(self, minimal_exp):
        html = report_builder.build_html(minimal_exp)
        assert "Print" in html or "print" in html

    def test_dragon_section_shown(self, dragon_exp):
        html = report_builder.build_html(dragon_exp)
        assert "Dragon Content" in html
        assert "ULX Path" in html

    def test_validation_pass_badge(self, minimal_exp, validation_pass):
        html = report_builder.build_html(minimal_exp, validation_result=validation_pass)
        assert "badge-pass" in html

    def test_validation_fail_badge(self, minimal_exp, validation_fail):
        html = report_builder.build_html(minimal_exp, validation_result=validation_fail)
        assert "badge-fail" in html

    def test_validation_warn_badge(self, minimal_exp, validation_warn):
        html = report_builder.build_html(minimal_exp, validation_result=validation_warn)
        assert "badge-warn" in html

    def test_no_validation_section_when_none(self, minimal_exp):
        html = report_builder.build_html(minimal_exp, validation_result=None)
        assert "Validation Results" not in html

    def test_table_headers_present(self, minimal_exp):
        html = report_builder.build_html(minimal_exp)
        assert "<th" in html

    def test_utf8_content(self, minimal_exp):
        """Report should handle non-ASCII safely."""
        exp = dict(minimal_exp)
        exp["Test Name"] = "Prueba de señal voltaje"
        html = report_builder.build_html(exp)
        assert "Prueba" in html


# --------------------------------------------------------------------------
# write_pdf tests (optional dep)
# --------------------------------------------------------------------------

class TestWritePdf:

    def test_raises_import_error_without_fpdf2(self, minimal_exp):
        """If fpdf2 is not installed, write_pdf should raise ImportError with hint."""
        if report_builder.PDF_AVAILABLE:
            pytest.skip("fpdf2 is installed; skipping missing-dep test.")
        with pytest.raises(ImportError, match="fpdf2"):
            report_builder.write_pdf(minimal_exp, "/tmp/dummy.pdf")

    def test_writes_pdf_when_fpdf2_available(self, minimal_exp):
        if not report_builder.PDF_AVAILABLE:
            pytest.skip("fpdf2 not installed.")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = pathlib.Path(tmpdir) / "test.pdf"
            result = report_builder.write_pdf(minimal_exp, out)
            assert result.exists()
            assert result.stat().st_size > 0


# --------------------------------------------------------------------------
# exporter.write_report tests
# --------------------------------------------------------------------------

class TestExporterWriteReport:

    def test_writes_md_and_html_by_default(self, minimal_exp):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = exporter.write_report(minimal_exp, tmpdir)
            assert "md" in written
            assert "html" in written
            assert written["md"].exists()
            assert written["html"].exists()

    def test_md_file_contains_test_name(self, minimal_exp):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = exporter.write_report(minimal_exp, tmpdir)
            content = written["md"].read_text(encoding="utf-8")
            assert "Baseline Test" in content

    def test_html_file_is_valid_html(self, minimal_exp):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = exporter.write_report(minimal_exp, tmpdir)
            content = written["html"].read_text(encoding="utf-8")
            assert "<!DOCTYPE html>" in content

    def test_custom_name_used_in_filename(self, minimal_exp):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = exporter.write_report(minimal_exp, tmpdir, name="CustomName")
            assert "CustomName_report" in written["md"].name

    def test_default_name_from_test_name(self, minimal_exp):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = exporter.write_report(minimal_exp, tmpdir)
            assert "Baseline Test_report" in written["md"].name or "Baseline" in written["md"].name

    def test_md_only_format(self, minimal_exp):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = exporter.write_report(minimal_exp, tmpdir, formats=("md",))
            assert "md" in written
            assert "html" not in written

    def test_html_only_format(self, minimal_exp):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = exporter.write_report(minimal_exp, tmpdir, formats=("html",))
            assert "html" in written
            assert "md" not in written

    def test_invalid_format_raises_value_error(self, minimal_exp):
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Unknown report format"):
                exporter.write_report(minimal_exp, tmpdir, formats=("txt",))

    def test_returns_dict_of_paths(self, minimal_exp):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = exporter.write_report(minimal_exp, tmpdir)
            assert isinstance(written, dict)
            for fmt, path in written.items():
                assert isinstance(path, pathlib.Path)

    def test_validation_result_included_in_md(self, minimal_exp, validation_fail):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = exporter.write_report(
                minimal_exp, tmpdir, validation_result=validation_fail
            )
            content = written["md"].read_text(encoding="utf-8")
            assert "COM Port is required" in content

    def test_product_shown_in_report(self, minimal_exp):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = exporter.write_report(minimal_exp, tmpdir, product="DMR")
            content = written["md"].read_text(encoding="utf-8")
            assert "DMR" in content

    def test_output_dir_created_if_absent(self, minimal_exp):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_subdir = pathlib.Path(tmpdir) / "new" / "subdir"
            written = exporter.write_report(minimal_exp, new_subdir)
            assert new_subdir.exists()
            assert written["md"].exists()

    def test_pdf_raises_import_error_without_fpdf2(self, minimal_exp):
        if report_builder.PDF_AVAILABLE:
            pytest.skip("fpdf2 is installed.")
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ImportError, match="fpdf2"):
                exporter.write_report(minimal_exp, tmpdir, formats=("pdf",))


# --------------------------------------------------------------------------
# Field grouping helpers
# --------------------------------------------------------------------------

class TestFieldGrouping:

    def test_section_fields_is_dict(self):
        assert isinstance(report_builder._SECTION_FIELDS, dict)

    def test_all_section_field_lists_are_nonempty(self):
        for section, fields in report_builder._SECTION_FIELDS.items():
            assert len(fields) > 0, f"Section {section!r} has no fields"

    def test_iter_sections_yields_tuples(self, minimal_exp):
        results = list(report_builder._iter_sections(minimal_exp))
        for section, rows in results:
            assert isinstance(section, str)
            assert isinstance(rows, list)

    def test_fmt_value_none_returns_dash(self):
        assert report_builder._fmt_value(None) == "—"

    def test_fmt_value_true_returns_yes(self):
        assert report_builder._fmt_value(True) == "Yes"

    def test_fmt_value_false_returns_no(self):
        assert report_builder._fmt_value(False) == "No"

    def test_fmt_value_int_returns_str(self):
        assert report_builder._fmt_value(42) == "42"

    def test_fmt_value_string_passthrough(self):
        assert report_builder._fmt_value("hello") == "hello"

    def test_section_has_data_detects_set_field(self):
        exp = {"ShmooFile": "test.json"}
        fields = ["ShmooFile", "ShmooLabel"]
        assert report_builder._section_has_data(exp, fields) is True

    def test_section_has_data_empty_returns_false(self):
        exp = {"ShmooFile": None, "ShmooLabel": ""}
        fields = ["ShmooFile", "ShmooLabel"]
        assert report_builder._section_has_data(exp, fields) is False
