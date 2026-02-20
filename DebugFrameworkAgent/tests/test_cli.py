"""
test_cli.py — Smoke tests for CLI scripts (subprocess execution).

Tests that each CLI script runs without error for basic invocations.

Run with:
    pytest DebugFrameworkAgent/tests/test_cli.py -v
"""

import json
import pathlib
import subprocess
import sys
import pytest

SCRIPTS_DIR = pathlib.Path(__file__).parent.parent / "scripts"
PYTHON      = sys.executable


def run_script(script_name: str, *args) -> subprocess.CompletedProcess:
    """Run a CLI script and return the completed process."""
    cmd = [PYTHON, str(SCRIPTS_DIR / script_name)] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True)


# ---------------------------------------------------------------------------
# list_presets.py
# ---------------------------------------------------------------------------

class TestListPresets:
    def test_runs_without_args(self):
        result = run_script("list_presets.py")
        assert result.returncode == 0, result.stderr

    def test_runs_with_gnr_filter(self):
        result = run_script("list_presets.py", "--product", "GNR")
        assert result.returncode == 0, result.stderr

    def test_outputs_at_least_one_preset(self):
        result = run_script("list_presets.py", "--product", "GNR")
        assert "GNR" in result.stdout or len(result.stdout) > 10

    def test_json_output(self):
        result = run_script("list_presets.py", "--json")
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_json_output_has_expected_keys(self):
        result = run_script("list_presets.py", "--product", "GNR", "--json")
        data = json.loads(result.stdout)
        for item in data[:3]:
            assert "_key" in item or "key" in item or "description" in item

    def test_invalid_product_returns_error(self):
        result = run_script("list_presets.py", "--product", "XYZ")
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# generate_experiment.py
# ---------------------------------------------------------------------------

class TestGenerateExperiment:
    def test_generates_gnr_mesh(self, tmp_path):
        out = tmp_path / "exp.json"
        result = run_script(
            "generate_experiment.py",
            "--product", "GNR",
            "--mode", "mesh",
            "--name", "TestRun",
            "--out", str(out),
            "--no-validate",
        )
        assert result.returncode == 0, result.stderr
        assert out.exists()

    def test_generated_json_is_valid(self, tmp_path):
        out = tmp_path / "exp.json"
        run_script(
            "generate_experiment.py",
            "--product", "CWF",
            "--mode", "mesh",
            "--name", "CWFTest",
            "--out", str(out),
            "--no-validate",
        )
        assert out.exists()
        data = json.loads(out.read_text())
        assert isinstance(data, dict)
        assert data.get("Test Name") == "CWFTest"

    def test_product_defaults_applied(self, tmp_path):
        out = tmp_path / "dmr.json"
        run_script(
            "generate_experiment.py",
            "--product", "DMR",
            "--name", "DMRTest",
            "--out", str(out),
            "--no-validate",
        )
        data = json.loads(out.read_text())
        assert data["COM Port"] == 9
        assert data["ULX CPU"] == "DMR"

    def test_missing_product_exits_nonzero(self):
        result = run_script("generate_experiment.py", "--name", "Test")
        assert result.returncode != 0

    def test_set_override_applied(self, tmp_path):
        out = tmp_path / "override.json"
        run_script(
            "generate_experiment.py",
            "--product", "GNR",
            "--name", "Override",
            "--out", str(out),
            "--no-validate",
            "--set", "Loops=42",
        )
        data = json.loads(out.read_text())
        assert data["Loops"] == 42


# ---------------------------------------------------------------------------
# validate_experiment.py
# ---------------------------------------------------------------------------

class TestValidateExperiment:
    def _write_valid_exp(self, tmp_path) -> pathlib.Path:
        exp = {
            "Experiment": "Enabled",
            "Test Name": "ValidTest",
            "Test Mode": "Mesh",
            "Test Type": "Loops",
            "IP Address": "192.168.0.2",
            "COM Port": 11,
            "TTL Folder": "S:\\GNR\\TTL",
        }
        p = tmp_path / "valid.json"
        p.write_text(json.dumps(exp))
        return p

    def _write_invalid_exp(self, tmp_path) -> pathlib.Path:
        exp = {"Experiment": "Enabled", "Test Name": ""}
        p = tmp_path / "invalid.json"
        p.write_text(json.dumps(exp))
        return p

    def test_valid_experiment_exits_zero(self, tmp_path):
        path = self._write_valid_exp(tmp_path)
        result = run_script("validate_experiment.py", str(path))
        assert result.returncode == 0, result.stdout + result.stderr

    def test_invalid_experiment_exits_nonzero(self, tmp_path):
        path = self._write_invalid_exp(tmp_path)
        result = run_script("validate_experiment.py", str(path))
        assert result.returncode != 0

    def test_missing_file_exits_nonzero(self):
        result = run_script("validate_experiment.py", "/nonexistent/file.json")
        assert result.returncode != 0

    def test_json_flag_outputs_valid_json(self, tmp_path):
        path = self._write_valid_exp(tmp_path)
        result = run_script("validate_experiment.py", "--json", str(path))
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert data[0]["valid"] is True


# ---------------------------------------------------------------------------
# generate_flow.py
# ---------------------------------------------------------------------------

class TestGenerateFlow:
    def _write_experiments(self, tmp_path) -> pathlib.Path:
        exps = [
            {"Experiment": "Enabled", "Test Name": "Step1", "Test Mode": "Mesh",
             "Test Type": "Loops", "COM Port": 11, "IP Address": "192.168.0.2"},
            {"Experiment": "Enabled", "Test Name": "Step2", "Test Mode": "Mesh",
             "Test Type": "Loops", "COM Port": 11, "IP Address": "192.168.0.2"},
        ]
        p = tmp_path / "exps.json"
        p.write_text(json.dumps(exps))
        return p

    def test_generates_flow_files(self, tmp_path):
        exps = self._write_experiments(tmp_path)
        out_dir = tmp_path / "flow"
        result = run_script(
            "generate_flow.py",
            "--experiments", str(exps),
            "--out", str(out_dir),
        )
        assert result.returncode == 0, result.stderr
        assert (out_dir / "TestStructure.json").exists()
        assert (out_dir / "TestFlows.json").exists()
        assert (out_dir / "unit_config.ini").exists()
        assert (out_dir / "positions.json").exists()

    def test_structure_json_valid(self, tmp_path):
        exps = self._write_experiments(tmp_path)
        out_dir = tmp_path / "flow"
        run_script("generate_flow.py", "--experiments", str(exps), "--out", str(out_dir))
        structure = json.loads((out_dir / "TestStructure.json").read_text())
        assert "nodes" in structure
        assert "connections" in structure

    def test_node_count_correct(self, tmp_path):
        exps = self._write_experiments(tmp_path)
        out_dir = tmp_path / "flow"
        run_script("generate_flow.py", "--experiments", str(exps), "--out", str(out_dir))
        structure = json.loads((out_dir / "TestStructure.json").read_text())
        # Boot + Step1 + Step2 + End_PASS + End_FAIL = 5
        assert len(structure["nodes"]) == 5
