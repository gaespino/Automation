"""
test_experiment_builder.py — Tests for scripts/_core/experiment_builder.py

Run with:
    pytest DebugFrameworkAgent/tests/test_experiment_builder.py -v
"""

import copy
import json
import pathlib
import pytest
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from _core import experiment_builder


# ---------------------------------------------------------------------------
# PRODUCT_DEFAULTS
# ---------------------------------------------------------------------------

class TestProductDefaults:
    def test_all_products_present(self):
        for product in ("GNR", "CWF", "DMR"):
            assert product in experiment_builder.PRODUCT_DEFAULTS

    def test_gnr_com_port(self):
        assert experiment_builder.PRODUCT_DEFAULTS["GNR"]["COM Port"] == 11

    def test_cwf_com_port(self):
        assert experiment_builder.PRODUCT_DEFAULTS["CWF"]["COM Port"] == 11

    def test_dmr_com_port(self):
        assert experiment_builder.PRODUCT_DEFAULTS["DMR"]["COM Port"] == 9

    def test_gnr_ip(self):
        assert experiment_builder.PRODUCT_DEFAULTS["GNR"]["IP Address"] == "192.168.0.2"

    def test_cwf_ip(self):
        assert experiment_builder.PRODUCT_DEFAULTS["CWF"]["IP Address"] == "10.250.0.2"

    def test_dmr_ip(self):
        assert experiment_builder.PRODUCT_DEFAULTS["DMR"]["IP Address"] == "192.168.0.2"

    def test_gnr_check_core(self):
        assert experiment_builder.PRODUCT_DEFAULTS["GNR"]["Check Core"] == 36

    def test_cwf_check_core(self):
        assert experiment_builder.PRODUCT_DEFAULTS["CWF"]["Check Core"] == 7

    def test_dmr_check_core(self):
        assert experiment_builder.PRODUCT_DEFAULTS["DMR"]["Check Core"] == 24

    def test_gnr_fastboot_true(self):
        assert experiment_builder.PRODUCT_DEFAULTS["GNR"]["FastBoot"] is True

    def test_dmr_fastboot_false(self):
        assert experiment_builder.PRODUCT_DEFAULTS["DMR"]["FastBoot"] is False


# ---------------------------------------------------------------------------
# new_blank
# ---------------------------------------------------------------------------

class TestNewBlank:
    def test_returns_dict(self):
        exp = experiment_builder.new_blank("GNR")
        assert isinstance(exp, dict)

    def test_test_name_empty(self):
        exp = experiment_builder.new_blank("GNR")
        assert exp["Test Name"] == ""

    def test_gnr_defaults_applied(self):
        exp = experiment_builder.new_blank("GNR")
        assert exp["COM Port"] == 11
        assert exp["IP Address"] == "192.168.0.2"
        assert exp["ULX CPU"] == "GNR_B0"

    def test_cwf_defaults_applied(self):
        exp = experiment_builder.new_blank("CWF")
        assert exp["COM Port"] == 11
        assert exp["IP Address"] == "10.250.0.2"
        assert exp["ULX CPU"] == "CWF_B0"

    def test_dmr_defaults_applied(self):
        exp = experiment_builder.new_blank("DMR")
        assert exp["COM Port"] == 9
        assert exp["ULX CPU"] == "DMR"
        assert exp["FastBoot"] is False

    def test_slice_mode_sets_test_mode(self):
        exp = experiment_builder.new_blank("GNR", mode="slice")
        assert exp["Test Mode"] == "Slice"

    def test_mesh_mode_default(self):
        exp = experiment_builder.new_blank("GNR")
        assert exp["Test Mode"] == "Mesh"

    def test_boot_mode_disables_fastboot(self):
        exp = experiment_builder.new_blank("GNR", mode="boot")
        assert exp["FastBoot"] is False

    def test_does_not_mutate_blank_template(self):
        exp1 = experiment_builder.new_blank("GNR")
        exp2 = experiment_builder.new_blank("CWF")
        exp1["Test Name"] = "Modified"
        exp2["Test Name"] = "Also Modified"
        exp3 = experiment_builder.new_blank("GNR")
        assert exp3["Test Name"] == ""

    def test_invalid_product_raises(self):
        with pytest.raises(ValueError):
            experiment_builder.new_blank("XYZ")

    def test_case_insensitive_product(self):
        exp = experiment_builder.new_blank("gnr")
        assert exp["ULX CPU"] == "GNR_B0"

    def test_has_all_required_fields(self):
        exp = experiment_builder.new_blank("GNR")
        for field in ("Experiment", "Test Name", "Test Mode", "Test Type", "COM Port", "IP Address"):
            assert field in exp, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# apply_preset
# ---------------------------------------------------------------------------

class TestApplyPreset:
    def _make_preset(self, **exp_overrides):
        exp = {"Test Name": "Base", "Loops": 5, "Test Mode": "Mesh"}
        exp.update(exp_overrides)
        return {"description": "Test", "ask_user": [], "experiment": exp}

    def test_returns_dict(self):
        preset = self._make_preset()
        result = experiment_builder.apply_preset(preset)
        assert isinstance(result, dict)

    def test_overrides_applied(self):
        preset = self._make_preset()
        result = experiment_builder.apply_preset(preset, {"Loops": 20})
        assert result["Loops"] == 20

    def test_original_preset_not_mutated(self):
        preset = self._make_preset()
        experiment_builder.apply_preset(preset, {"Loops": 99})
        assert preset["experiment"]["Loops"] == 5

    def test_no_overrides_copies_cleanly(self):
        preset = self._make_preset(Test_Name="Run1")
        result = experiment_builder.apply_preset(preset)
        assert result == preset["experiment"]

    def test_preset_missing_experiment_key_raises(self):
        with pytest.raises(ValueError):
            experiment_builder.apply_preset({"description": "bad"})

    def test_new_fields_can_be_injected(self):
        preset = self._make_preset()
        result = experiment_builder.apply_preset(preset, {"Extra_Field": "value"})
        assert result.get("Extra_Field") == "value"


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

class TestValidate:
    def _valid_exp(self, **overrides):
        exp = {
            "Experiment": "Enabled",
            "Test Name": "MyTest",
            "Test Mode": "Mesh",
            "Test Type": "Loops",
            "IP Address": "192.168.0.2",
            "COM Port": 11,
            "TTL Folder": "S:\\GNR\\TTL",
        }
        exp.update(overrides)
        return exp

    def test_valid_exp_passes(self):
        ok, errors, warnings = experiment_builder.validate(self._valid_exp())
        assert ok
        assert errors == []

    def test_missing_test_name_fails(self):
        ok, errors, _ = experiment_builder.validate(self._valid_exp(**{"Test Name": ""}))
        assert not ok
        assert any("Test Name" in e for e in errors)

    def test_invalid_ip_fails(self):
        ok, errors, _ = experiment_builder.validate(self._valid_exp(**{"IP Address": "999.999.999"}))
        assert not ok
        assert any("IP Address" in e for e in errors)

    def test_valid_ip_passes(self):
        ok, errors, _ = experiment_builder.validate(self._valid_exp(**{"IP Address": "10.250.0.2"}))
        assert ok

    def test_sweep_missing_start_fails(self):
        ok, errors, _ = experiment_builder.validate(
            self._valid_exp(**{"Test Type": "Sweep", "Start": None, "End": 1100, "Steps": 5,
                               "Domain": "IA", "Type": "Voltage"})
        )
        assert not ok

    def test_sweep_end_less_than_start_fails(self):
        ok, errors, _ = experiment_builder.validate(
            self._valid_exp(**{"Test Type": "Sweep", "Start": 1100, "End": 900, "Steps": 5,
                               "Domain": "IA", "Type": "Voltage"})
        )
        assert not ok
        assert any("End" in e for e in errors)

    def test_sweep_valid(self):
        ok, errors, _ = experiment_builder.validate(
            self._valid_exp(**{"Test Type": "Sweep", "Start": 900, "End": 1100, "Steps": 5,
                               "Domain": "IA", "Type": "Voltage"})
        )
        assert ok

    def test_shmoo_missing_file_fails(self):
        ok, errors, _ = experiment_builder.validate(
            self._valid_exp(**{"Test Type": "Shmoo", "ShmooFile": None})
        )
        assert not ok
        assert any("ShmooFile" in e for e in errors)

    def test_empty_ttl_folder_warns(self):
        exp = self._valid_exp()
        exp["TTL Folder"] = None
        _, _, warnings = experiment_builder.validate(exp)
        assert any("TTL" in w for w in warnings)

    def test_returns_tuple_of_three(self):
        result = experiment_builder.validate(self._valid_exp())
        assert len(result) == 3

    def test_linux_missing_path_warns(self):
        exp = self._valid_exp(**{"Content": "Linux", "Linux Path": None, "Startup Linux": None})
        _, _, warnings = experiment_builder.validate(exp)
        assert any("Linux Path" in w for w in warnings)


# ---------------------------------------------------------------------------
# list_all_fields
# ---------------------------------------------------------------------------

class TestListAllFields:
    def test_returns_list(self):
        fields = experiment_builder.list_all_fields()
        assert isinstance(fields, list)

    def test_required_fields_present(self):
        fields = experiment_builder.list_all_fields()
        for f in ("Experiment", "Test Name", "COM Port", "IP Address", "Loops"):
            assert f in fields, f"Missing field: {f}"

    def test_field_count_reasonable(self):
        fields = experiment_builder.list_all_fields()
        assert len(fields) >= 10


# ---------------------------------------------------------------------------
# load_from_file
# ---------------------------------------------------------------------------

class TestLoadFromFile:
    def _write_exp(self, tmp_path, data) -> pathlib.Path:
        p = tmp_path / "exp.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_loads_single_experiment_dict(self, tmp_path):
        exp = {"Test Name": "MyTest", "Loops": 5}
        p = self._write_exp(tmp_path, exp)
        result = experiment_builder.load_from_file(p)
        assert result["Test Name"] == "MyTest"
        assert result["Loops"] == 5

    def test_loads_first_element_when_list(self, tmp_path):
        exp = [{"Test Name": "ListTest", "Loops": 3}]
        p = self._write_exp(tmp_path, exp)
        result = experiment_builder.load_from_file(p)
        assert result["Test Name"] == "ListTest"

    def test_returns_a_copy_not_same_object(self, tmp_path):
        exp = {"Test Name": "CopyTest", "Loops": 1}
        p = self._write_exp(tmp_path, exp)
        result = experiment_builder.load_from_file(p)
        result["Loops"] = 99
        result2 = experiment_builder.load_from_file(p)
        assert result2["Loops"] == 1  # original file unchanged

    def test_accepts_string_path(self, tmp_path):
        exp = {"Test Name": "StringPath", "Loops": 2}
        p = self._write_exp(tmp_path, exp)
        result = experiment_builder.load_from_file(str(p))
        assert result["Test Name"] == "StringPath"

    def test_raises_for_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            experiment_builder.load_from_file(tmp_path / "nonexistent.json")

    def test_raises_for_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{ not valid json ", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            experiment_builder.load_from_file(p)

    def test_raises_for_empty_list(self, tmp_path):
        p = self._write_exp(tmp_path, [])
        with pytest.raises(ValueError, match="empty"):
            experiment_builder.load_from_file(p)

    def test_raises_for_wrong_type(self, tmp_path):
        p = self._write_exp(tmp_path, "just a string")
        with pytest.raises(ValueError):
            experiment_builder.load_from_file(p)

    # .tpl format
    def test_loads_tpl_single_row(self, tmp_path):
        p = tmp_path / "exp.tpl"
        p.write_text("Test Name\tLoops\tExperiment\nTplTest\t7\tEnabled\n", encoding="utf-8")
        result = experiment_builder.load_from_file(p)
        assert result["Test Name"] == "TplTest"
        assert result["Loops"] == 7
        assert result["Experiment"] == "Enabled"

    def test_loads_tpl_multi_row_returns_first(self, tmp_path):
        p = tmp_path / "multi.tpl"
        p.write_text(
            "Test Name\tLoops\nFirst\t1\nSecond\t2\n",
            encoding="utf-8",
        )
        result = experiment_builder.load_from_file(p)
        assert result["Test Name"] == "First"

    def test_raises_for_tpl_missing_data_row(self, tmp_path):
        p = tmp_path / "bad.tpl"
        p.write_text("Test Name\tLoops\n", encoding="utf-8")
        with pytest.raises(ValueError, match="valid .tpl"):
            experiment_builder.load_from_file(p)

    def test_tpl_coerces_empty_to_none(self, tmp_path):
        p = tmp_path / "empty.tpl"
        p.write_text("Test Name\tLoops\nMyTest\t\n", encoding="utf-8")
        result = experiment_builder.load_from_file(p)
        assert result["Loops"] is None

    def test_tpl_coerces_bool_true(self, tmp_path):
        p = tmp_path / "bool.tpl"
        p.write_text("Test Name\tFastBoot\nMyTest\tTrue\n", encoding="utf-8")
        result = experiment_builder.load_from_file(p)
        assert result["FastBoot"] is True

    def test_tpl_coerces_bool_false(self, tmp_path):
        p = tmp_path / "bool2.tpl"
        p.write_text("Test Name\tFastBoot\nMyTest\tFalse\n", encoding="utf-8")
        result = experiment_builder.load_from_file(p)
        assert result["FastBoot"] is False

    def test_tpl_coerces_int(self, tmp_path):
        p = tmp_path / "int.tpl"
        p.write_text("Test Name\tLoops\nMyTest\t5\n", encoding="utf-8")
        result = experiment_builder.load_from_file(p)
        assert result["Loops"] == 5
        assert isinstance(result["Loops"], int)

    def test_tpl_coerces_float(self, tmp_path):
        p = tmp_path / "flt.tpl"
        p.write_text("Test Name\tVoltage IA\nMyTest\t0.05\n", encoding="utf-8")
        result = experiment_builder.load_from_file(p)
        assert abs(result["Voltage IA"] - 0.05) < 1e-9


# ---------------------------------------------------------------------------
# load_batch_from_file
# ---------------------------------------------------------------------------

class TestLoadBatchFromFile:
    """load_batch_from_file handles all file structures and returns list[dict]."""

    def test_json_list(self, tmp_path):
        data = [{"Test Name": "A"}, {"Test Name": "B"}]
        p = tmp_path / "batch.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        result = experiment_builder.load_batch_from_file(p)
        assert len(result) == 2
        assert result[0]["Test Name"] == "A"
        assert result[1]["Test Name"] == "B"

    def test_json_single_dict(self, tmp_path):
        data = {"Test Name": "Single", "Experiment": "Enabled"}
        p = tmp_path / "single.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        result = experiment_builder.load_batch_from_file(p)
        assert len(result) == 1
        assert result[0]["Test Name"] == "Single"

    def test_json_dict_of_dicts(self, tmp_path):
        data = {
            "exp1": {"Test Name": "X"},
            "exp2": {"Test Name": "Y"},
        }
        p = tmp_path / "dod.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        result = experiment_builder.load_batch_from_file(p)
        assert len(result) == 2
        names = {r["Test Name"] for r in result}
        assert names == {"X", "Y"}

    def test_tpl_single_row(self, tmp_path):
        p = tmp_path / "s.tpl"
        p.write_text("Test Name\tLoops\nOne\t3\n", encoding="utf-8")
        result = experiment_builder.load_batch_from_file(p)
        assert len(result) == 1
        assert result[0]["Test Name"] == "One"
        assert result[0]["Loops"] == 3

    def test_tpl_multi_row(self, tmp_path):
        p = tmp_path / "m.tpl"
        p.write_text("Test Name\tLoops\nFirst\t1\nSecond\t2\nThird\t3\n", encoding="utf-8")
        result = experiment_builder.load_batch_from_file(p)
        assert len(result) == 3
        assert [r["Test Name"] for r in result] == ["First", "Second", "Third"]

    def test_raises_for_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            experiment_builder.load_batch_from_file(tmp_path / "no.json")

    def test_raises_for_empty_json_list(self, tmp_path):
        p = tmp_path / "empty.json"
        p.write_text("[]", encoding="utf-8")
        with pytest.raises(ValueError, match="empty"):
            experiment_builder.load_batch_from_file(p)

    def test_returns_independent_copies(self, tmp_path):
        data = [{"Test Name": "Copy", "Loops": 1}]
        p = tmp_path / "c.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        r1 = experiment_builder.load_batch_from_file(p)
        r1[0]["Loops"] = 999
        r2 = experiment_builder.load_batch_from_file(p)
        assert r2[0]["Loops"] == 1


# ---------------------------------------------------------------------------
# update_fields
# ---------------------------------------------------------------------------

class TestUpdateFields:
    def test_updates_existing_field(self):
        exp = {"Test Name": "Old", "Loops": 5}
        result = experiment_builder.update_fields(exp, {"Loops": 20})
        assert result["Loops"] == 20

    def test_does_not_mutate_original(self):
        exp = {"Test Name": "Orig", "Loops": 5}
        experiment_builder.update_fields(exp, {"Loops": 99})
        assert exp["Loops"] == 5

    def test_adds_new_key(self):
        exp = {"Test Name": "Orig"}
        result = experiment_builder.update_fields(exp, {"NewField": "value"})
        assert result["NewField"] == "value"

    def test_preserves_unchanged_fields(self):
        exp = {"Test Name": "KeepMe", "Loops": 5, "Content": "Dragon"}
        result = experiment_builder.update_fields(exp, {"Loops": 10})
        assert result["Test Name"] == "KeepMe"
        assert result["Content"] == "Dragon"

    def test_empty_changes_returns_copy(self):
        exp = {"Test Name": "Same", "Loops": 5}
        result = experiment_builder.update_fields(exp, {})
        assert result == exp
        assert result is not exp

    def test_null_value_clears_field(self):
        exp = {"Dragon Content Line": "func_a"}
        result = experiment_builder.update_fields(exp, {"Dragon Content Line": None})
        assert result["Dragon Content Line"] is None

    def test_multiple_fields_updated_at_once(self):
        exp = {"Loops": 5, "Bucket": "OLD", "Check Core": 0}
        result = experiment_builder.update_fields(exp, {"Loops": 10, "Bucket": "MARGIN", "Check Core": 36})
        assert result["Loops"] == 10
        assert result["Bucket"] == "MARGIN"
        assert result["Check Core"] == 36


# ---------------------------------------------------------------------------
# Disabled experiment handling
# ---------------------------------------------------------------------------

class TestDisabledExperiment:
    """validate() and validate_batch() behaviour for Experiment == 'Disabled'."""

    def _disabled_exp(self, name="Skip Me"):
        """Minimal experiment marked Disabled (missing required fields on purpose)."""
        return {"Experiment": "Disabled", "Test Name": name}

    def _enabled_exp(self, name="Active Test", **overrides):
        exp = {
            "Experiment": "Enabled",
            "Test Name": name,
            "Test Mode": "Mesh",
            "Test Type": "Loops",
            "IP Address": "192.168.0.1",
            "COM Port": 11,
            "TTL Folder": "S:\\GNR\\TTL",
        }
        exp.update(overrides)
        return exp

    # ── validate() ──────────────────────────────────────────────────────────

    def test_disabled_is_valid(self):
        ok, errors, warnings = experiment_builder.validate(self._disabled_exp())
        assert ok

    def test_disabled_has_no_errors(self):
        _, errors, _ = experiment_builder.validate(self._disabled_exp())
        assert errors == []

    def test_disabled_produces_experiment_disabled_warning(self):
        _, _, warnings = experiment_builder.validate(self._disabled_exp())
        assert len(warnings) == 1
        assert warnings[0].startswith("EXPERIMENT_DISABLED:")

    def test_disabled_skips_other_validation(self):
        # A disabled experiment with missing required fields (IP, Mode, etc.)
        # must NOT produce errors for those fields.
        exp = self._disabled_exp()
        ok, errors, _ = experiment_builder.validate(exp)
        assert ok
        assert errors == []

    def test_empty_experiment_field_still_errors(self):
        exp = self._enabled_exp()
        exp["Experiment"] = ""
        ok, errors, _ = experiment_builder.validate(exp)
        assert not ok
        assert any("Experiment" in e for e in errors)

    def test_none_experiment_field_errors(self):
        exp = self._enabled_exp()
        exp["Experiment"] = None
        ok, errors, _ = experiment_builder.validate(exp)
        assert not ok
        assert any("Experiment" in e for e in errors)

    def test_enabled_exp_not_flagged_as_disabled(self):
        _, _, warnings = experiment_builder.validate(self._enabled_exp())
        assert not any(w.startswith("EXPERIMENT_DISABLED:") for w in warnings)

    # ── validate_batch() ────────────────────────────────────────────────────

    def test_validate_batch_returns_four_values(self):
        result = experiment_builder.validate_batch([self._enabled_exp()])
        assert len(result) == 4

    def test_validate_batch_disabled_names(self):
        exps = [self._enabled_exp("A"), self._disabled_exp("B"), self._enabled_exp("C")]
        _, _, _, disabled = experiment_builder.validate_batch(exps)
        assert disabled == ["B"]

    def test_validate_batch_all_disabled(self):
        exps = [self._disabled_exp("D1"), self._disabled_exp("D2")]
        ok, errors, _, disabled = experiment_builder.validate_batch(exps)
        assert ok
        assert errors == []
        assert set(disabled) == {"D1", "D2"}

    def test_validate_batch_no_disabled(self):
        exps = [self._enabled_exp("X"), self._enabled_exp("Y")]
        _, _, _, disabled = experiment_builder.validate_batch(exps)
        assert disabled == []

    def test_validate_batch_disabled_not_in_errors(self):
        exps = [self._enabled_exp("Good"), self._disabled_exp()]
        _, errors, _, _ = experiment_builder.validate_batch(exps)
        assert not any("Skip Me" in e for e in errors)

    # ── filter_disabled() ───────────────────────────────────────────────────

    def test_filter_disabled_removes_disabled(self):
        exps = [self._enabled_exp("Keep"), self._disabled_exp()]
        result = experiment_builder.filter_disabled(exps)
        names = [e.get("Test Name") for e in result]
        assert "Keep" in names
        assert "Skip Me" not in names

    def test_filter_disabled_keeps_enabled(self):
        exps = [self._enabled_exp("A"), self._enabled_exp("B")]
        result = experiment_builder.filter_disabled(exps)
        assert len(result) == 2

    def test_filter_disabled_all_disabled_returns_empty(self):
        exps = [self._disabled_exp(), self._disabled_exp()]
        result = experiment_builder.filter_disabled(exps)
        assert result == []

    def test_filter_disabled_does_not_mutate_input(self):
        exps = [self._enabled_exp("K"), self._disabled_exp()]
        original_len = len(exps)
        experiment_builder.filter_disabled(exps)
        assert len(exps) == original_len

    def test_filter_disabled_case_insensitive(self):
        exp = self._enabled_exp("CaseTest")
        exp["Experiment"] = "DISABLED"
        result = experiment_builder.filter_disabled([exp])
        assert result == []
