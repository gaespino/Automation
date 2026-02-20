"""
test_constraints.py — Tests for scripts/_core/constraints.py

Run with:
    pytest DebugFrameworkAgent/tests/test_constraints.py -v
"""

import pathlib
import sys
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from _core import constraints as c


# ---------------------------------------------------------------------------
# Constants / data structure smoke tests
# ---------------------------------------------------------------------------

class TestConstants:
    def test_mesh_mask_products(self):
        for p in ("GNR", "CWF", "DMR"):
            assert p in c.MESH_MASK_OPTIONS

    def test_gnr_cwf_mesh_masks_identical(self):
        assert c.MESH_MASK_OPTIONS["GNR"] == c.MESH_MASK_OPTIONS["CWF"]

    def test_dmr_mesh_masks(self):
        masks = c.MESH_MASK_OPTIONS["DMR"]
        assert "Compute0" in masks
        assert "Cbb3" in masks
        assert "RowPass1" not in masks

    def test_gnr_slice_range(self):
        assert c.SLICE_CORE_RANGE["GNR"] == (0, 179)

    def test_dmr_slice_range(self):
        assert c.SLICE_CORE_RANGE["DMR"] == (0, 128)

    def test_vvar_defaults_keys(self):
        for p in ("GNR", "CWF", "DMR"):
            assert "mesh"  in c.VVAR_DEFAULTS[p]
            assert "slice" in c.VVAR_DEFAULTS[p]

    def test_dmr_mesh_vvar3_differs_from_gnr(self):
        assert c.VVAR_DEFAULTS["DMR"]["mesh"]["VVAR3"] != c.VVAR_DEFAULTS["GNR"]["mesh"]["VVAR3"]

    def test_dmr_slice_vvar3_differs_from_gnr(self):
        assert c.VVAR_DEFAULTS["DMR"]["slice"]["VVAR3"] != c.VVAR_DEFAULTS["GNR"]["slice"]["VVAR3"]

    def test_slice_blocked_fields_contains_pseudo(self):
        assert "Pseudo Config"  in c.SLICE_BLOCKED_FIELDS
        assert "Disable 2 Cores" in c.SLICE_BLOCKED_FIELDS
        assert "Disable 1 Core"  in c.SLICE_BLOCKED_FIELDS

    def test_disable_2_core_options_cwf(self):
        for opt in ("0x3", "0xc", "0x9", "0xa", "0x5"):
            assert opt in c.DISABLE_2_CORE_OPTIONS

    def test_disable_1_core_options_dmr(self):
        assert "0x1" in c.DISABLE_1_CORE_OPTIONS
        assert "0x2" in c.DISABLE_1_CORE_OPTIONS

    def test_default_test_time(self):
        assert c.DEFAULT_TEST_TIME == 30

    def test_test_number_priority_ordering(self):
        assert c.TEST_NUMBER_PRIORITY["Loops"] < c.TEST_NUMBER_PRIORITY["Sweep"]
        assert c.TEST_NUMBER_PRIORITY["Sweep"] < c.TEST_NUMBER_PRIORITY["Shmoo"]

    def test_pysvconsole_required_scripts_file(self):
        assert "Scripts File" in c.CONTENT_REQUIRED_FIELDS["PYSVConsole"]


# ---------------------------------------------------------------------------
# check_slice_restrictions
# ---------------------------------------------------------------------------

class TestCheckSliceRestrictions:
    def _exp(self, mode, **kwargs):
        return {"Test Mode": mode, **kwargs}

    def test_mesh_with_pseudo_config_ok(self):
        exp = self._exp("Mesh", **{"Pseudo Config": True})
        errors, warnings = c.check_slice_restrictions(exp)
        assert errors == []

    def test_slice_with_pseudo_config_error(self):
        exp = self._exp("Slice", **{"Pseudo Config": True})
        errors, _ = c.check_slice_restrictions(exp)
        assert any("Pseudo Config" in e for e in errors)

    def test_slice_with_disable_2_cores_error(self):
        exp = self._exp("Slice", **{"Disable 2 Cores": "0x3"})
        errors, _ = c.check_slice_restrictions(exp)
        assert any("Disable 2 Cores" in e for e in errors)

    def test_slice_with_disable_1_core_error(self):
        exp = self._exp("Slice", **{"Disable 1 Core": "0x1"})
        errors, _ = c.check_slice_restrictions(exp)
        assert any("Disable 1 Core" in e for e in errors)

    def test_slice_empty_blocked_fields_ok(self):
        exp = self._exp("Slice", **{"Pseudo Config": False, "Disable 2 Cores": "", "Disable 1 Core": ""})
        errors, _ = c.check_slice_restrictions(exp)
        assert errors == []

    def test_non_slice_returns_clean(self):
        exp = self._exp("Mesh", **{"Pseudo Config": True, "Disable 2 Cores": "0x3"})
        errors, warnings = c.check_slice_restrictions(exp)
        assert errors == [] and warnings == []


# ---------------------------------------------------------------------------
# check_mesh_mask
# ---------------------------------------------------------------------------

class TestCheckMeshMask:
    def _exp(self, mode, mask):
        return {"Test Mode": mode, "Configuration (Mask)": mask}

    def test_gnr_valid_mesh_mask(self):
        errors, _ = c.check_mesh_mask(self._exp("Mesh", "RowPass1"), "GNR")
        assert errors == []

    def test_gnr_invalid_mesh_mask(self):
        errors, _ = c.check_mesh_mask(self._exp("Mesh", "Compute0"), "GNR")
        assert errors  # Compute0 is DMR only

    def test_dmr_valid_mesh_mask_compute(self):
        errors, _ = c.check_mesh_mask(self._exp("Mesh", "Compute2"), "DMR")
        assert errors == []

    def test_dmr_valid_mesh_mask_cbb(self):
        errors, _ = c.check_mesh_mask(self._exp("Mesh", "Cbb3"), "DMR")
        assert errors == []

    def test_dmr_invalid_mesh_mask_rowpass(self):
        errors, _ = c.check_mesh_mask(self._exp("Mesh", "RowPass1"), "DMR")
        assert errors

    def test_gnr_slice_valid_core_number(self):
        errors, _ = c.check_mesh_mask(self._exp("Slice", "50"), "GNR")
        assert errors == []

    def test_gnr_slice_invalid_core_out_of_range(self):
        errors, _ = c.check_mesh_mask(self._exp("Slice", "200"), "GNR")
        assert errors  # max is 179

    def test_dmr_slice_invalid_core_out_of_range(self):
        errors, _ = c.check_mesh_mask(self._exp("Slice", "130"), "DMR")
        assert errors  # max is 128

    def test_dmr_slice_valid_core_max(self):
        errors, _ = c.check_mesh_mask(self._exp("Slice", "128"), "DMR")
        assert errors == []

    def test_slice_non_integer_mask_error(self):
        errors, _ = c.check_mesh_mask(self._exp("Slice", "RowPass1"), "GNR")
        assert errors  # must be integer in Slice

    def test_empty_mask_returns_clean(self):
        errors, _ = c.check_mesh_mask(self._exp("Mesh", ""), "GNR")
        assert errors == []

    def test_none_mask_returns_clean(self):
        errors, _ = c.check_mesh_mask({"Test Mode": "Mesh"}, "GNR")
        assert errors == []


# ---------------------------------------------------------------------------
# check_vvar_mode_consistency
# ---------------------------------------------------------------------------

class TestCheckVvarModeConsistency:
    def _exp(self, mode, vvar2=None, vvar3=None):
        e = {"Test Mode": mode}
        if vvar2 is not None:
            e["VVAR2"] = vvar2
        if vvar3 is not None:
            e["VVAR3"] = vvar3
        return e

    def test_gnr_mesh_correct_vvar2_no_warning(self):
        _, warnings = c.check_vvar_mode_consistency(self._exp("Mesh", "0x1000000"), "GNR")
        assert warnings == []

    def test_gnr_slice_correct_vvar2_no_warning(self):
        _, warnings = c.check_vvar_mode_consistency(self._exp("Slice", "0x1000002"), "GNR")
        assert warnings == []

    def test_gnr_mesh_with_slice_vvar2_warns(self):
        _, warnings = c.check_vvar_mode_consistency(self._exp("Mesh", "0x1000002"), "GNR")
        assert any("2 threads" in w or "Slice" in w for w in warnings)

    def test_gnr_slice_with_mesh_vvar2_warns(self):
        _, warnings = c.check_vvar_mode_consistency(self._exp("Slice", "0x1000000"), "GNR")
        assert any("Mesh" in w for w in warnings)

    def test_dmr_mesh_correct_vvar3_no_warning(self):
        _, warnings = c.check_vvar_mode_consistency(
            self._exp("Mesh", "0x1000000", "0x4200000"), "DMR"
        )
        assert warnings == []

    def test_dmr_slice_wrong_vvar3_warns(self):
        _, warnings = c.check_vvar_mode_consistency(
            self._exp("Slice", "0x1000002", "0x4200000"), "DMR"
        )
        # 0x4200000 is the mesh value; slice expects 0x4210000
        assert warnings

    def test_no_vvar_set_no_warning(self):
        _, warnings = c.check_vvar_mode_consistency({"Test Mode": "Mesh"}, "GNR")
        assert warnings == []


# ---------------------------------------------------------------------------
# check_pseudo_core_configuration
# ---------------------------------------------------------------------------

class TestCheckPseudoCoreConfiguration:
    def test_cwf_valid_disable_2_cores(self):
        exp = {"Test Mode": "Mesh", "Disable 2 Cores": "0x3"}
        errors, _ = c.check_pseudo_core_configuration(exp, "CWF")
        assert errors == []

    def test_cwf_invalid_disable_2_cores(self):
        exp = {"Test Mode": "Mesh", "Disable 2 Cores": "0xff"}
        errors, _ = c.check_pseudo_core_configuration(exp, "CWF")
        assert errors

    def test_dmr_valid_disable_1_core(self):
        exp = {"Test Mode": "Mesh", "Disable 1 Core": "0x1"}
        errors, _ = c.check_pseudo_core_configuration(exp, "DMR")
        assert errors == []

    def test_dmr_invalid_disable_1_core(self):
        exp = {"Test Mode": "Mesh", "Disable 1 Core": "0x4"}
        errors, _ = c.check_pseudo_core_configuration(exp, "DMR")
        assert errors

    def test_gnr_no_enumerated_validation(self):
        # GNR pseudo config is bool — no error for any bool value
        exp = {"Pseudo Config": True}
        errors, _ = c.check_pseudo_core_configuration(exp, "GNR")
        assert errors == []

    def test_cwf_empty_disable_ok(self):
        exp = {"Disable 2 Cores": ""}
        errors, _ = c.check_pseudo_core_configuration(exp, "CWF")
        assert errors == []


# ---------------------------------------------------------------------------
# check_pysvconsole_requirements
# ---------------------------------------------------------------------------

class TestCheckPysvConsoleRequirements:
    def test_pysv_missing_scripts_file_is_error(self):
        exp = {"Content": "PYSVConsole", "Scripts File": ""}
        errors, _ = c.check_pysvconsole_requirements(exp)
        assert errors

    def test_pysv_with_scripts_file_ok(self):
        exp = {"Content": "PYSVConsole", "Scripts File": "my_script.py"}
        errors, _ = c.check_pysvconsole_requirements(exp)
        assert errors == []

    def test_pysv_boot_breakpoint_without_bios_warns(self):
        exp = {"Content": "PYSVConsole", "Scripts File": "s.py", "Boot Breakpoint": True}
        _, warnings = c.check_pysvconsole_requirements(exp)
        assert warnings

    def test_pysv_boot_breakpoint_with_bios_ok(self):
        exp = {"Content": "PYSVConsole", "Scripts File": "s.py",
               "Boot Breakpoint": True, "Bios File": "bios.bin"}
        _, warnings = c.check_pysvconsole_requirements(exp)
        assert warnings == []

    def test_dragon_content_not_affected(self):
        exp = {"Content": "Dragon", "Scripts File": ""}
        errors, _ = c.check_pysvconsole_requirements(exp)
        assert errors == []


# ---------------------------------------------------------------------------
# check_dragon_content_requirements
# ---------------------------------------------------------------------------

class TestCheckDragonContentRequirements:
    def test_dragon_missing_paths_warns(self):
        exp = {"Content": "Dragon"}
        _, warnings = c.check_dragon_content_requirements(exp)
        assert len(warnings) >= 2
        assert any("ULX" in w for w in warnings)
        assert any("Dragon Content Path" in w for w in warnings)

    def test_dragon_with_paths_no_warnings(self):
        exp = {
            "Content": "Dragon",
            "ULX Path": "path/to/ulx",
            "Dragon Content Path": "path/to/content",
            "Dragon Content Line": "line args",
        }
        _, warnings = c.check_dragon_content_requirements(exp)
        assert warnings == []

    def test_non_dragon_content_skipped(self):
        exp = {"Content": "Linux"}
        _, warnings = c.check_dragon_content_requirements(exp)
        assert warnings == []


# ---------------------------------------------------------------------------
# check_linux_content_requirements
# ---------------------------------------------------------------------------

class TestCheckLinuxContentRequirements:
    def test_linux_missing_fields_warns(self):
        exp = {"Content": "Linux"}
        _, warnings = c.check_linux_content_requirements(exp)
        assert any("Linux Path" in w for w in warnings)

    def test_linux_with_required_fields_clean(self):
        exp = {
            "Content": "Linux",
            "Linux Path": "/path",
            "Startup Linux": "startup",
            "Linux Pass String": "PASS",
        }
        _, warnings = c.check_linux_content_requirements(exp)
        assert warnings == []

    def test_non_linux_skipped(self):
        exp = {"Content": "Dragon"}
        _, warnings = c.check_linux_content_requirements(exp)
        assert warnings == []


# ---------------------------------------------------------------------------
# check_check_core_set
# ---------------------------------------------------------------------------

class TestCheckCheckCoreSet:
    def test_pysv_skips_check_core_requirement(self):
        exp = {"Content": "PYSVConsole", "Check Core": 0}
        _, warnings = c.check_check_core_set(exp)
        assert warnings == []

    def test_zero_check_core_warns(self):
        exp = {"Content": "Dragon", "Check Core": 0}
        _, warnings = c.check_check_core_set(exp)
        assert warnings

    def test_none_check_core_warns(self):
        exp = {"Content": "Dragon"}
        _, warnings = c.check_check_core_set(exp)
        assert warnings

    def test_valid_check_core_no_warning(self):
        exp = {"Content": "Dragon", "Check Core": 36}
        _, warnings = c.check_check_core_set(exp)
        assert warnings == []


# ---------------------------------------------------------------------------
# check_batch_check_core
# ---------------------------------------------------------------------------

class TestCheckBatchCheckCore:
    def test_consistent_check_core_no_warning(self):
        exps = [
            {"Test Name": "exp1", "Content": "Dragon", "Check Core": 36},
            {"Test Name": "exp2", "Content": "Linux",  "Check Core": 36},
        ]
        _, warnings = c.check_batch_check_core(exps)
        assert warnings == []

    def test_inconsistent_check_core_warns(self):
        exps = [
            {"Test Name": "exp1", "Content": "Dragon", "Check Core": 36},
            {"Test Name": "exp2", "Content": "Dragon", "Check Core": 7},
        ]
        _, warnings = c.check_batch_check_core(exps)
        assert warnings

    def test_pysvconsole_excluded_from_batch_check(self):
        # PYSVConsole experiments are excluded, so different values don't matter
        exps = [
            {"Test Name": "exp1", "Content": "Dragon",     "Check Core": 36},
            {"Test Name": "exp2", "Content": "PYSVConsole", "Check Core": 0},
        ]
        _, warnings = c.check_batch_check_core(exps)
        assert warnings == []

    def test_single_exp_no_warning(self):
        exps = [{"Test Name": "exp1", "Content": "Dragon", "Check Core": 36}]
        _, warnings = c.check_batch_check_core(exps)
        assert warnings == []


# ---------------------------------------------------------------------------
# assign_test_numbers
# ---------------------------------------------------------------------------

class TestAssignTestNumbers:
    def test_loops_gets_lowest_number(self):
        exps = [
            {"Test Type": "Shmoo",  "Test Name": "s"},
            {"Test Type": "Loops",  "Test Name": "l"},
            {"Test Type": "Sweep",  "Test Name": "sw"},
        ]
        result = c.assign_test_numbers(exps)
        nums = {e["Test Name"]: e["Test Number"] for e in result}
        assert nums["l"] < nums["sw"] < nums["s"]

    def test_sequential_numbering_starts_at_one(self):
        exps = [{"Test Type": "Loops"}, {"Test Type": "Sweep"}, {"Test Type": "Shmoo"}]
        result = c.assign_test_numbers(exps)
        test_nums = [e["Test Number"] for e in result]
        assert sorted(test_nums) == [1, 2, 3]

    def test_original_list_not_mutated(self):
        exps = [{"Test Type": "Loops", "Test Number": 99}]
        c.assign_test_numbers(exps)
        assert exps[0]["Test Number"] == 99  # not mutated

    def test_multiple_loops_all_before_sweep(self):
        exps = [
            {"Test Type": "Sweep", "Test Name": "sweep1"},
            {"Test Type": "Loops", "Test Name": "loop1"},
            {"Test Type": "Loops", "Test Name": "loop2"},
        ]
        result = c.assign_test_numbers(exps)
        loop_nums  = [e["Test Number"] for e in result if e["Test Name"].startswith("loop")]
        sweep_nums = [e["Test Number"] for e in result if e["Test Name"].startswith("sweep")]
        assert max(loop_nums) < min(sweep_nums)

    def test_empty_list_returns_empty(self):
        assert c.assign_test_numbers([]) == []


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

class TestHelperFunctions:
    def test_get_unit_chop_options_gnr(self):
        opts = c.get_unit_chop_options("GNR")
        assert "AP" in opts and "SP" in opts

    def test_get_unit_chop_options_dmr(self):
        opts = c.get_unit_chop_options("DMR")
        assert "X1" in opts and "X4" in opts

    def test_get_pseudo_core_field_gnr(self):
        field, options = c.get_pseudo_core_field_and_options("GNR")
        assert field == "Pseudo Config"
        assert options == ["True"]  # bool toggle — only "True" is an enable value

    def test_get_pseudo_core_field_cwf(self):
        field, options = c.get_pseudo_core_field_and_options("CWF")
        assert field == "Disable 2 Cores"
        assert len(options) > 0

    def test_get_pseudo_core_field_dmr(self):
        field, options = c.get_pseudo_core_field_and_options("DMR")
        assert field == "Disable 1 Core"
        assert "0x1" in options


# ---------------------------------------------------------------------------
# check_voltage_bumps
# ---------------------------------------------------------------------------

class TestCheckVoltageBumps:
    def test_none_values_ignored(self):
        exp = {"Voltage IA": None, "Voltage CFC": None}
        errors, warnings = c.check_voltage_bumps(exp)
        assert errors == [] and warnings == []

    def test_missing_fields_ignored(self):
        exp = {}
        errors, warnings = c.check_voltage_bumps(exp)
        assert errors == [] and warnings == []

    def test_zero_produces_informational_warning(self):
        exp = {"Voltage IA": 0}
        errors, warnings = c.check_voltage_bumps(exp)
        assert errors == []
        assert len(warnings) == 1
        assert "0" in warnings[0] and "Voltage IA" in warnings[0]

    def test_zero_float_string_produces_warning(self):
        exp = {"Voltage IA": "0.0"}
        errors, warnings = c.check_voltage_bumps(exp)
        assert errors == []
        assert warnings

    def test_valid_positive_no_warning(self):
        exp = {"Voltage IA": 0.1, "Voltage CFC": 0.05}
        errors, warnings = c.check_voltage_bumps(exp)
        assert errors == [] and warnings == []

    def test_at_max_no_warning(self):
        exp = {"Voltage IA": 0.3}
        errors, warnings = c.check_voltage_bumps(exp)
        assert errors == [] and warnings == []

    def test_exceeds_max_warns(self):
        exp = {"Voltage IA": 0.31}
        errors, warnings = c.check_voltage_bumps(exp)
        assert errors == []
        assert len(warnings) == 1
        assert "0.31" in warnings[0] or "Voltage IA" in warnings[0]

    def test_both_fields_exceeding_produces_two_warnings(self):
        exp = {"Voltage IA": 0.4, "Voltage CFC": 0.5}
        errors, warnings = c.check_voltage_bumps(exp)
        assert errors == []
        assert len(warnings) == 2

    def test_negative_value_is_error(self):
        exp = {"Voltage IA": -0.1}
        errors, warnings = c.check_voltage_bumps(exp)
        assert len(errors) == 1
        assert "negative" in errors[0].lower() or "Voltage IA" in errors[0]
        assert warnings == []

    def test_non_numeric_string_is_error(self):
        exp = {"Voltage CFC": "high"}
        errors, warnings = c.check_voltage_bumps(exp)
        assert len(errors) == 1

    def test_empty_string_ignored(self):
        exp = {"Voltage IA": "", "Voltage CFC": ""}
        errors, warnings = c.check_voltage_bumps(exp)
        assert errors == [] and warnings == []
