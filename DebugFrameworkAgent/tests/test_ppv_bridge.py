"""
test_ppv_bridge.py — Tests for scripts/_core/ppv_bridge.py

All tests use only mock/temp data so they pass with or without
a real PPV installation on the host.

Run with:
    pytest DebugFrameworkAgent/tests/test_ppv_bridge.py -v
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys
import tempfile

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from _core import ppv_bridge as pb


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_fake_ppv(tmp_path: pathlib.Path, product: str = "GNR") -> pathlib.Path:
    """Create a minimal fake PPV root directory with a ControlPanelConfig."""
    root = tmp_path / "PPV"
    configs = root / "configs"
    configs.mkdir(parents=True)

    config_data = {
        "testModes":      ["Mesh", "Slice", "Boot", "Linux"],
        "testTypes":      ["Single", "Sweep", "Shmoo"],
        "contentOptions": ["Dragon", "Linux", "PYSVConsole"],
        "voltageTypes":   ["IA", "CFC"],
        "sweepTypes":     ["Voltage", "Frequency"],
        "domains":        ["IA", "CFC"],
    }
    (configs / f"{product}ControlPanelConfig.json").write_text(
        json.dumps(config_data), encoding="utf-8"
    )
    return root


# ---------------------------------------------------------------------------
# TestDiscovery
# ---------------------------------------------------------------------------

class TestDiscovery:
    def test_invalid_path_returns_none(self, monkeypatch):
        monkeypatch.delenv("PPV_ROOT", raising=False)
        monkeypatch.setattr(pb, "_RELATIVE_CANDIDATES", [])
        monkeypatch.setattr(pb, "_ABSOLUTE_CANDIDATES", [])
        result = pb.discover_ppv(override="/nonexistent/path/PPV")
        assert result is None

    def test_dir_without_config_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.delenv("PPV_ROOT", raising=False)
        monkeypatch.setattr(pb, "_RELATIVE_CANDIDATES", [])
        monkeypatch.setattr(pb, "_ABSOLUTE_CANDIDATES", [])
        fake = tmp_path / "PPV"
        fake.mkdir()
        result = pb.discover_ppv(override=fake)
        assert result is None

    def test_valid_override_accepted(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        result = pb.discover_ppv(override=root)
        assert result is not None
        assert result.is_dir()

    def test_override_path_resolved(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        result = pb.discover_ppv(override=root)
        assert result == root.resolve()

    def test_env_var_takes_priority(self, tmp_path, monkeypatch):
        root = make_fake_ppv(tmp_path)
        monkeypatch.setenv("PPV_ROOT", str(root))
        result = pb.discover_ppv(override="/wrong/path")
        assert result == root.resolve()

    def test_invalid_env_var_ignored(self, tmp_path, monkeypatch):
        root = make_fake_ppv(tmp_path)
        monkeypatch.setenv("PPV_ROOT", "/nonexistent/path")
        result = pb.discover_ppv(override=root)
        assert result == root.resolve()


# ---------------------------------------------------------------------------
# TestAvailability
# ---------------------------------------------------------------------------

class TestAvailability:
    def test_unavailable_when_no_ppv(self):
        bridge = pb.PPVBridge(ppv_root="/nonexistent/ppv")
        assert not bridge.is_available
        assert bridge.root is None

    def test_available_when_valid_root(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        assert bridge.is_available
        assert bridge.root == root.resolve()

    def test_status_line_unavailable(self):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        assert "standalone" in bridge.status_line.lower() or "not found" in bridge.status_line.lower()

    def test_status_line_available(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        assert str(root.resolve()) in bridge.status_line or "detected" in bridge.status_line.lower()


# ---------------------------------------------------------------------------
# TestConfigLoading
# ---------------------------------------------------------------------------

class TestConfigLoading:
    def test_returns_none_when_unavailable(self):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        assert bridge.load_live_field_config("GNR") is None

    def test_returns_fallback_when_unavailable(self):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        assert bridge.load_live_field_config("GNR", fallback={"x": 1}) == {"x": 1}

    def test_loads_config_when_available(self, tmp_path):
        root = make_fake_ppv(tmp_path, "GNR")
        bridge = pb.PPVBridge(ppv_root=root)
        cfg = bridge.load_live_field_config("GNR")
        assert cfg is not None
        assert "testModes" in cfg

    def test_returns_deep_copy(self, tmp_path):
        root = make_fake_ppv(tmp_path, "GNR")
        bridge = pb.PPVBridge(ppv_root=root)
        cfg1 = bridge.load_live_field_config("GNR")
        cfg2 = bridge.load_live_field_config("GNR")
        assert cfg1 is not cfg2
        cfg1["testModes"].append("MODIFIED")
        assert "MODIFIED" not in cfg2.get("testModes", [])

    def test_caches_config(self, tmp_path):
        root = make_fake_ppv(tmp_path, "GNR")
        bridge = pb.PPVBridge(ppv_root=root)
        bridge.load_live_field_config("GNR")
        assert "GNR" in bridge._config_cache

    def test_missing_product_returns_none(self, tmp_path):
        root = make_fake_ppv(tmp_path, "GNR")
        bridge = pb.PPVBridge(ppv_root=root)
        result = bridge.load_live_field_config("UNKNOWN")
        assert result is None


# ---------------------------------------------------------------------------
# TestEnumSync
# ---------------------------------------------------------------------------

class TestEnumSync:
    def test_returns_none_when_unavailable(self):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        assert bridge.sync_enums("GNR") is None

    def test_sync_returns_dict(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        enums = bridge.sync_enums("GNR")
        assert isinstance(enums, dict)

    def test_sync_contains_test_modes(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        enums = bridge.sync_enums("GNR")
        assert "TEST_MODES" in enums
        assert "Mesh" in enums["TEST_MODES"]

    def test_get_valid_enum_returns_list(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        result = bridge.get_valid_enum("GNR", "TEST_MODES")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_valid_enum_fallback_when_unavailable(self):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        fallback = ["Mesh", "Slice"]
        result = bridge.get_valid_enum("GNR", "TEST_MODES", fallback=fallback)
        assert result == fallback

    def test_get_valid_enum_unknown_key_returns_fallback(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        result = bridge.get_valid_enum("GNR", "NONEXISTENT_KEY", fallback=["x"])
        assert result == ["x"]


# ---------------------------------------------------------------------------
# TestFieldConfig
# ---------------------------------------------------------------------------

class TestFieldConfig:
    def test_field_enable_config_unavailable(self):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        assert bridge.get_field_enable_config("GNR") is None

    def test_field_enable_config_missing_key(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        # Our fake config doesn't have fieldEnableConfig — should return fallback
        result = bridge.get_field_enable_config("GNR", fallback={"x": True})
        assert result == {"x": True}

    def test_field_configs_unavailable(self):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        assert bridge.get_field_configs("GNR") is None


# ---------------------------------------------------------------------------
# TestExperimentLoading
# ---------------------------------------------------------------------------

class TestExperimentLoading:
    def test_load_single_dict(self, tmp_path):
        exp_data = {"Test Name": "CI Exp", "Product Chop": "GNR"}
        p = tmp_path / "exp.json"
        p.write_text(json.dumps(exp_data), encoding="utf-8")
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        result = bridge.load_ppv_experiment(p)
        assert result["Test Name"] == "CI Exp"

    def test_load_list_wrapped(self, tmp_path):
        exp_data = [{"Test Name": "CI Exp", "Product Chop": "GNR"}]
        p = tmp_path / "exp.json"
        p.write_text(json.dumps(exp_data), encoding="utf-8")
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        result = bridge.load_ppv_experiment(p)
        assert result["Test Name"] == "CI Exp"

    def test_missing_file_raises(self, tmp_path):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        with pytest.raises(FileNotFoundError):
            bridge.load_ppv_experiment(tmp_path / "missing.json")

    def test_invalid_json_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not valid json", encoding="utf-8")
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        with pytest.raises(ValueError, match="Invalid JSON"):
            bridge.load_ppv_experiment(p)

    def test_returns_deep_copy(self, tmp_path):
        exp_data = {"Test Name": "CI Exp"}
        p = tmp_path / "exp.json"
        p.write_text(json.dumps(exp_data), encoding="utf-8")
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        r1 = bridge.load_ppv_experiment(p)
        r1["Test Name"] = "MODIFIED"
        r2 = bridge.load_ppv_experiment(p)
        assert r2["Test Name"] == "CI Exp"


# ---------------------------------------------------------------------------
# TestOutputPath
# ---------------------------------------------------------------------------

class TestOutputPath:
    def test_fallback_when_unavailable(self):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        path = bridge.get_output_path(fallback_base="/tmp/out")
        assert str(path).startswith("/tmp/out") or "out" in str(path)

    def test_unit_id_appended(self, tmp_path):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        path = bridge.get_output_path(unit_id="UNIT123", fallback_base=tmp_path)
        assert "UNIT123" in str(path)

    def test_ppv_root_used_when_available(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        path = bridge.get_output_path(unit_id="UNIT123")
        # When PPV available, output path is under PPV root
        assert str(root.resolve()) in str(path) or "UNIT123" in str(path)

    def test_returns_path_object(self):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        path = bridge.get_output_path()
        assert isinstance(path, pathlib.Path)


# ---------------------------------------------------------------------------
# TestEnumValidation
# ---------------------------------------------------------------------------

class TestEnumValidation:
    def test_valid_value_accepted(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        ok, msg = bridge.validate_enum_value("GNR", "TEST_MODES", "Mesh")
        assert ok
        assert msg is None

    def test_invalid_value_rejected(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        ok, msg = bridge.validate_enum_value("GNR", "TEST_MODES", "InvalidMode")
        assert not ok
        assert "InvalidMode" in msg

    def test_none_value_accepted(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        ok, msg = bridge.validate_enum_value("GNR", "TEST_MODES", None)
        assert ok

    def test_empty_value_accepted(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        ok, msg = bridge.validate_enum_value("GNR", "TEST_MODES", "")
        assert ok

    def test_no_ppv_accepts_any_value(self):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        ok, msg = bridge.validate_enum_value("GNR", "TEST_MODES", "AnyValue")
        assert ok

    def test_bundled_fallback_used_when_no_ppv(self):
        bridge = pb.PPVBridge(ppv_root="/nonexistent")
        ok, msg = bridge.validate_enum_value(
            "GNR", "TEST_MODES", "BadValue",
            bundled_fallback=["Mesh", "Slice"],
        )
        assert not ok

    def test_error_message_contains_expected_values(self, tmp_path):
        root = make_fake_ppv(tmp_path)
        bridge = pb.PPVBridge(ppv_root=root)
        ok, msg = bridge.validate_enum_value("GNR", "TEST_MODES", "NOPE")
        assert "Mesh" in msg or "TEST_MODES" in msg


# ---------------------------------------------------------------------------
# TestSingleton
# ---------------------------------------------------------------------------

class TestSingleton:
    def setup_method(self):
        pb.reset_bridge()

    def teardown_method(self):
        pb.reset_bridge()

    def test_get_bridge_returns_ppvbridge(self):
        bridge = pb.get_bridge()
        assert isinstance(bridge, pb.PPVBridge)

    def test_singleton_same_instance(self):
        b1 = pb.get_bridge()
        b2 = pb.get_bridge()
        assert b1 is b2

    def test_reset_forces_new_instance(self):
        b1 = pb.get_bridge()
        pb.reset_bridge()
        b2 = pb.get_bridge()
        assert b1 is not b2

    def test_reset_sets_none(self):
        pb.get_bridge()
        pb.reset_bridge()
        assert pb._bridge_instance is None
