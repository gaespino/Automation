"""
test_github_integration.py — Tests for GitHub Actions workflows and
the github_model_client.py helper.

These tests exercise the structure of the workflow YAML files and the
client logic without making real API calls (all network calls are
mocked/patched).

Run with:
    pytest DebugFrameworkAgent/tests/test_github_integration.py -v
"""

from __future__ import annotations

import json
import pathlib
import sys
import types
import unittest.mock as mock

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_TESTS_DIR   = pathlib.Path(__file__).parent
_AGENT_ROOT  = _TESTS_DIR.parent
_SCRIPTS_DIR = _AGENT_ROOT / "scripts"
_WORKFLOWS   = _AGENT_ROOT / ".github" / "workflows"

sys.path.insert(0, str(_SCRIPTS_DIR))
import github_model_client as gmc


# ---------------------------------------------------------------------------
# TestWorkflowFiles — basic existence and YAML structure
# ---------------------------------------------------------------------------

class TestWorkflowFiles:
    def test_generate_workflow_exists(self):
        assert (_WORKFLOWS / "generate-experiments.yml").exists()

    def test_validate_workflow_exists(self):
        assert (_WORKFLOWS / "validate-experiments.yml").exists()

    def test_list_presets_workflow_exists(self):
        assert (_WORKFLOWS / "list-presets.yml").exists()

    def test_workflow_files_are_valid_yaml(self):
        """Each workflow file must be parseable as YAML (or at minimum not empty)."""
        for wf in _WORKFLOWS.glob("*.yml"):
            content = wf.read_text(encoding="utf-8")
            assert len(content) > 100, f"{wf.name} appears empty"
            assert "on:" in content or "name:" in content, f"{wf.name} missing YAML structure"


# ---------------------------------------------------------------------------
# TestGenerateWorkflow
# ---------------------------------------------------------------------------

class TestGenerateWorkflow:
    @pytest.fixture(autouse=True)
    def load(self):
        self.text = (_WORKFLOWS / "generate-experiments.yml").read_text(encoding="utf-8")

    def test_has_workflow_dispatch(self):
        assert "workflow_dispatch" in self.text

    def test_has_product_input(self):
        assert "product:" in self.text

    def test_has_preset_input(self):
        assert "preset:" in self.text

    def test_has_upload_artifact_step(self):
        assert "upload-artifact" in self.text

    def test_references_generate_script(self):
        assert "generate_experiment.py" in self.text

    def test_checkout_step_present(self):
        assert "actions/checkout" in self.text


# ---------------------------------------------------------------------------
# TestValidateWorkflow
# ---------------------------------------------------------------------------

class TestValidateWorkflow:
    @pytest.fixture(autouse=True)
    def load(self):
        self.text = (_WORKFLOWS / "validate-experiments.yml").read_text(encoding="utf-8")

    def test_has_push_trigger(self):
        assert "push:" in self.text

    def test_has_pull_request_trigger(self):
        assert "pull_request:" in self.text

    def test_has_workflow_dispatch(self):
        assert "workflow_dispatch" in self.text

    def test_references_experiment_builder(self):
        assert "experiment_builder" in self.text

    def test_comments_on_pr(self):
        assert "createComment" in self.text or "github-script" in self.text


# ---------------------------------------------------------------------------
# TestListPresetsWorkflow
# ---------------------------------------------------------------------------

class TestListPresetsWorkflow:
    @pytest.fixture(autouse=True)
    def load(self):
        self.text = (_WORKFLOWS / "list-presets.yml").read_text(encoding="utf-8")

    def test_has_workflow_dispatch(self):
        assert "workflow_dispatch" in self.text

    def test_has_product_input(self):
        assert "product:" in self.text

    def test_has_format_input(self):
        assert "format:" in self.text

    def test_references_preset_loader(self):
        assert "preset_loader" in self.text

    def test_uploads_catalog_artifact(self):
        assert "presets_catalog" in self.text or "catalog" in self.text


# ---------------------------------------------------------------------------
# TestGitHubModelClientInit
# ---------------------------------------------------------------------------

class TestGitHubModelClientInit:
    def test_raises_without_token(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(ValueError, match="GITHUB_TOKEN"):
            gmc.GitHubModelClient(token="")

    def test_accepts_explicit_token(self):
        client = gmc.GitHubModelClient(token="ghp_test123")
        assert client.token == "ghp_test123"

    def test_uses_env_var_token(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_env_token")
        client = gmc.GitHubModelClient()
        assert client.token == "ghp_env_token"

    def test_default_model(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        client = gmc.GitHubModelClient()
        assert client.model == gmc.DEFAULT_MODEL

    def test_custom_model(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        client = gmc.GitHubModelClient(model="gpt-4o")
        assert client.model == "gpt-4o"


# ---------------------------------------------------------------------------
# TestGitHubModelClientAsk
# ---------------------------------------------------------------------------

class TestGitHubModelClientAsk:
    @pytest.fixture
    def client(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        return gmc.GitHubModelClient()

    def _mock_response(self, text: str) -> dict:
        return {"choices": [{"message": {"content": text}}]}

    def test_ask_returns_string(self, client):
        with mock.patch.object(client, "_post", return_value=self._mock_response("Hello")):
            result = client.ask("Hi")
        assert result == "Hello"

    def test_ask_includes_system_prompt(self, client):
        captured = {}
        def fake_post(url, payload):
            captured["payload"] = payload
            return self._mock_response("ok")
        with mock.patch.object(client, "_post", side_effect=fake_post):
            client.ask("User msg", system_prompt="System msg")
        messages = captured["payload"]["messages"]
        assert any(m["role"] == "system" and "System msg" in m["content"] for m in messages)

    def test_ask_includes_history(self, client):
        captured = {}
        def fake_post(url, payload):
            captured["payload"] = payload
            return self._mock_response("ok")
        history = [{"role": "assistant", "content": "Prior reply"}]
        with mock.patch.object(client, "_post", side_effect=fake_post):
            client.ask("Follow-up", history=history)
        messages = captured["payload"]["messages"]
        assert any(m["role"] == "assistant" for m in messages)

    def test_ask_raises_on_bad_response(self, client):
        with mock.patch.object(client, "_post", return_value={"bad": "structure"}):
            with pytest.raises(RuntimeError):
                client.ask("Hi")


# ---------------------------------------------------------------------------
# TestTranslateToOverrides
# ---------------------------------------------------------------------------

class TestTranslateToOverrides:
    @pytest.fixture
    def client(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        return gmc.GitHubModelClient()

    def test_returns_dict(self, client):
        mock_reply = '{"Loops": 50, "Test Name": "CI Run"}'
        with mock.patch.object(client, "ask", return_value=mock_reply):
            result = client.translate_to_overrides("50 loops, name CI Run")
        assert isinstance(result, dict)
        assert result.get("Loops") == 50

    def test_strips_code_fences(self, client):
        mock_reply = '```json\n{"Loops": 10}\n```'
        with mock.patch.object(client, "ask", return_value=mock_reply):
            result = client.translate_to_overrides("10 loops")
        assert result.get("Loops") == 10

    def test_returns_empty_on_unparseable(self, client):
        with mock.patch.object(client, "ask", return_value="not valid json at all"):
            result = client.translate_to_overrides("gibberish")
        assert result == {}

    def test_product_in_system_prompt(self, client):
        captured = {}
        def fake_ask(msg, system_prompt=None, **kwargs):
            captured["system"] = system_prompt
            return "{}"
        with mock.patch.object(client, "ask", side_effect=fake_ask):
            client.translate_to_overrides("anything", product="DMR")
        assert "DMR" in (captured.get("system") or "")


# ---------------------------------------------------------------------------
# TestLoadPromptFile
# ---------------------------------------------------------------------------

class TestLoadPromptFile:
    def test_returns_string(self):
        # Even if prompts/ doesn't exist, must return a string (possibly empty)
        result = gmc.load_prompt_file("nonexistent_prompt_xyz")
        assert isinstance(result, str)

    def test_returns_empty_for_missing(self):
        result = gmc.load_prompt_file("__definitely_does_not_exist__")
        assert result == ""

    def test_returns_empty_for_missing_agent(self):
        result = gmc.load_agent_file("__definitely_does_not_exist__")
        assert result == ""

    def test_loads_existing_agent(self):
        # experiment.agent.md should exist
        result = gmc.load_agent_file("experiment")
        assert isinstance(result, str)
        # If it exists it should have some content
        if result:
            assert len(result) > 50
