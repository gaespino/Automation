"""
test_debugframework_agent.py — Migrated & updated core framework tests.

This is the migrated version of DEVTOOLS/test_debugframework_agent.py,
updated to use paths relative to the DebugFrameworkAgent package root.

Run with:
    pytest DebugFrameworkAgent/tests/test_debugframework_agent.py -v
"""

import json
import configparser
import io
import copy
import re
import pathlib
import pytest
import sys

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from _core import preset_loader, experiment_builder

DEFAULTS_DIR = pathlib.Path(__file__).parent.parent / "defaults"
PRESETS_FILE = DEFAULTS_DIR / "experiment_presets.json"


# ---------------------------------------------------------------------------
# Constants (matching original test file)
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = ["Experiment", "Test Name", "Test Mode", "Test Type"]

LOOP_ONLY_FIELDS   = ["Loops"]
SWEEP_ONLY_FIELDS  = ["Type", "Domain", "Start", "End", "Steps"]
SHMOO_ONLY_FIELDS  = ["ShmooFile", "ShmooLabel"]
LINUX_ONLY_FIELDS  = [
    "Linux Path", "Linux Pre Command", "Linux Post Command",
    "Linux Pass String", "Linux Fail String", "Linux Content Wait Time",
    "Startup Linux",
    *[f"Linux Content Line {i}" for i in range(10)],
]
DRAGON_ONLY_FIELDS = [
    "ULX Path", "ULX CPU", "Product Chop",
    "Dragon Pre Command", "Dragon Post Command", "Startup Dragon",
    "Dragon Content Path", "Dragon Content Line",
    "VVAR0", "VVAR1", "VVAR2", "VVAR3", "VVAR_EXTRA",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_base_experiment(**overrides):
    base = {
        "Experiment": "Enabled",
        "Test Name": "Test_Loops_001",
        "Test Mode": "Mesh",
        "Test Type": "Loops",
        "Visual ID": "",
        "Bucket": "BASELINE",
        "COM Port": 8,
        "IP Address": "192.168.1.100",
        "Content": "Dragon",
        "Test Number": 1,
        "Test Time": 45,
        "Reset": True,
        "Reset on PASS": True,
        "FastBoot": True,
        "Core License": "",
        "600W Unit": False,
        "Pseudo Config": False,
        "Post Process": "",
        "Configuration (Mask)": "",
        "Boot Breakpoint": "",
        "Check Core": 36,
        "Voltage Type": "vbump",
        "Voltage IA": "",
        "Voltage CFC": "",
        "Frequency IA": "",
        "Frequency CFC": "",
        "Loops": 5,
        "Type": "",
        "Domain": "",
        "Start": "",
        "End": "",
        "Steps": "",
        "ShmooFile": "",
        "ShmooLabel": "",
        "ULX Path": r"S:\GNR\RVP\ULX\xlnk_cpu.exe",
        "ULX CPU": "GNR_B0",
        "Product Chop": "GNR",
        "Dragon Pre Command": "",
        "Dragon Post Command": "",
        "Startup Dragon": True,
        "Dragon Content Path": r"S:\GNR\RVP\Content\Mesh\\",
        "Dragon Content Line": 0,
        "VVAR0": "",
        "VVAR1": "",
        "VVAR2": "0x1000000",
        "VVAR3": "0x4000000",
        "VVAR_EXTRA": "",
        "TTL Folder": r"S:\GNR\RVP\TTLs\TTL_DragonMesh",
        "Scripts File": "",
        "Pass String": "Test Complete",
        "Fail String": "Test Failed",
        "Stop on Fail": True,
        "Fuse File": "",
        "Bios File": "",
        "Merlin Name": "MerlinX.efi",
        "Merlin Drive": "FS1:",
        "Merlin Path": r"FS1:\EFI\Version8.15\BinFiles\Release",
        "Disable 2 Cores": "",
        "Disable 1 Core": "",
        "Linux Pre Command": "",
        "Linux Post Command": "",
        "Linux Pass String": "",
        "Linux Fail String": "",
        "Startup Linux": False,
        "Linux Path": "",
        "Linux Content Wait Time": 120,
        **{f"Linux Content Line {i}": "" for i in range(10)},
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

class TestRequiredFields:
    def test_all_required_fields_present(self):
        exp = make_base_experiment()
        for field in REQUIRED_FIELDS:
            assert field in exp, f"Missing required field: {field}"

    def test_experiment_field_is_enabled(self):
        exp = make_base_experiment()
        assert exp["Experiment"] == "Enabled"

    def test_test_name_not_empty(self):
        exp = make_base_experiment()
        assert exp["Test Name"] != ""

    def test_test_mode_valid(self):
        exp = make_base_experiment()
        assert exp["Test Mode"] in ("Mesh", "Slice")

    def test_test_type_valid(self):
        exp = make_base_experiment()
        assert exp["Test Type"] in ("Loops", "Sweep", "Shmoo", "Stability")


# ---------------------------------------------------------------------------
# IP address validation
# ---------------------------------------------------------------------------

IP_PATTERN = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

class TestIPAddress:
    def test_valid_ip_192(self):
        assert IP_PATTERN.match("192.168.0.2")

    def test_valid_ip_10(self):
        assert IP_PATTERN.match("10.250.0.2")

    def test_invalid_ip_no_match(self):
        assert not IP_PATTERN.match("999.999.999")
        assert not IP_PATTERN.match("not-an-ip")

    def test_experiment_ip_valid(self):
        exp = make_base_experiment()
        assert IP_PATTERN.match(exp["IP Address"])


# ---------------------------------------------------------------------------
# Content-specific fields
# ---------------------------------------------------------------------------

class TestDragonFields:
    def test_dragon_fields_present(self):
        exp = make_base_experiment()
        for field in DRAGON_ONLY_FIELDS:
            assert field in exp, f"Missing Dragon field: {field}"

    def test_ulx_cpu_gnr(self):
        exp = make_base_experiment()
        assert exp["ULX CPU"] == "GNR_B0"

    def test_vvar3_gnr_mesh(self):
        exp = make_base_experiment()
        assert exp["VVAR3"] == "0x4000000"

    def test_vvar2_gnr_mesh(self):
        exp = make_base_experiment()
        assert exp["VVAR2"] == "0x1000000"


class TestLinuxFields:
    def test_linux_fields_present(self):
        exp = make_base_experiment(Content="Linux")
        for field in LINUX_ONLY_FIELDS:
            assert field in exp, f"Missing Linux field: {field}"

    def test_linux_content_lines_count(self):
        exp = make_base_experiment(Content="Linux")
        lines = [f"Linux Content Line {i}" for i in range(10)]
        for f in lines:
            assert f in exp


# ---------------------------------------------------------------------------
# Sweep-specific
# ---------------------------------------------------------------------------

class TestSweepFields:
    def test_sweep_fields_present(self):
        exp = make_base_experiment(**{"Test Type": "Sweep"})
        for field in SWEEP_ONLY_FIELDS:
            assert field in exp, f"Missing Sweep field: {field}"

    def test_sweep_end_greater_than_start(self):
        exp = make_base_experiment(**{"Test Type": "Sweep", "Start": 900, "End": 1100, "Steps": 5})
        assert exp["End"] > exp["Start"]


# ---------------------------------------------------------------------------
# Preset file integrity
# ---------------------------------------------------------------------------

class TestPresetFile:
    @pytest.fixture(scope="class")
    def data(self):
        return preset_loader.load_all(PRESETS_FILE)

    def test_presets_file_exists(self):
        assert PRESETS_FILE.exists()

    def test_version_is_2(self, data):
        assert data.get("_meta", {}).get("version") == "2.0"

    def test_common_section_exists(self, data):
        assert "common" in data

    def test_product_sections_exist(self, data):
        for p in ("GNR", "CWF", "DMR"):
            assert p in data

    def test_schema_valid(self, data):
        ok, errors = preset_loader.validate_schema(data)
        assert ok, f"Schema errors: {errors}"

    def test_preset_count_atleast_9_common(self, data):
        assert len(data.get("common", {})) >= 9

    def test_all_presets_have_experiment_key(self, data):
        # common is a flat {key: preset_dict} — iterate directly
        for preset_key, preset in data.get("common", {}).items():
            if isinstance(preset, dict):
                assert "experiment" in preset, \
                    f"Preset '{preset_key}' in common missing 'experiment'"
        # product sections are nested: {boot_cases: {key: preset}, content_cases: ...}
        for product_key in ("GNR", "CWF", "DMR"):
            section = data.get(product_key, {})
            for cat_name, cat_dict in section.items():
                if isinstance(cat_dict, dict):
                    for preset_key, preset in cat_dict.items():
                        if isinstance(preset, dict):
                            assert "experiment" in preset, \
                                f"Preset '{preset_key}' in {product_key}/{cat_name} missing 'experiment'"


# ---------------------------------------------------------------------------
# Exporter round-trip
# ---------------------------------------------------------------------------

class TestExporterRoundTrip:
    def test_write_and_read_experiment_json(self, tmp_path):
        sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
        from _core import exporter

        exp = make_base_experiment()
        out = exporter.write_experiment_json(exp, tmp_path, "TestRoundTrip")
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["Test Name"] == "Test_Loops_001"

    def test_write_tpl_creates_file(self, tmp_path):
        from _core import exporter

        exp = make_base_experiment()
        out = exporter.write_tpl(exp, tmp_path, "TestTpl")
        assert out.exists()
        text = out.read_text()
        assert "Test Name" in text


# ---------------------------------------------------------------------------
# Flow builder
# ---------------------------------------------------------------------------

class TestFlowBuilder:
    def test_build_structure_basic(self):
        from _core import flow_builder

        nodes = [
            {"name": "Boot",     "type": flow_builder.NODE_BOOT},
            {"name": "Test1",    "type": flow_builder.NODE_TEST},
            {"name": "End_PASS", "type": flow_builder.NODE_END_PASS},
        ]
        result = flow_builder.build_structure(nodes)
        assert "nodes" in result
        assert "connections" in result
        assert len(result["nodes"]) == 3

    def test_build_ini_contains_sections(self):
        from _core import flow_builder

        ini = flow_builder.build_ini({"com_port": 11, "ip_address": "192.168.0.2"})
        assert "[Connection]" in ini
        assert "192.168.0.2" in ini

    def test_build_positions_all_nodes(self):
        from _core import flow_builder

        nodes = [
            {"name": "A", "type": flow_builder.NODE_TEST},
            {"name": "B", "type": flow_builder.NODE_TEST},
        ]
        pos = flow_builder.build_positions(nodes)
        assert len(pos) == 2
        for nid, coords in pos.items():
            assert "x" in coords and "y" in coords
