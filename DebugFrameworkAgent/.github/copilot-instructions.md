# Debug Framework Agent — Copilot Instructions

This workspace contains the **Debug Framework Agent** (`DebugFrameworkAgent/`), a self-contained
package for generating, validating, and exporting silicon debug experiment configurations.

---

## Package Layout

```
DebugFrameworkAgent/
├── agents/          ← Orchestrator, ExperimentAgent, FlowAgent
├── prompts/         ← Per-content and per-test-type prompt files
├── skills/          ← experiment_generator and automation_flow_designer skill docs
├── defaults/presets/ ← split per-product preset files: common.json, GNR.json, CWF.json, DMR.json (73 presets, v2.0)
├── scripts/
│   ├── _core/       ← preset_loader, experiment_builder, flow_builder, exporter
│   ├── list_presets.py
│   ├── apply_preset.py
│   ├── generate_experiment.py
│   ├── validate_experiment.py
│   ├── generate_flow.py
│   └── mcp_server.py   (Phase 2 — requires mcp[cli])
├── .vscode/
│   ├── tasks.json   ← VS Code tasks for all CLI scripts
│   └── mcp.json     ← MCP server config (disabled until Phase 2)
├── docs/
│   ├── SETUP.md
│   └── WORKFLOWS.md
└── tests/
```

---

## Target Products

| Code | Product | Notes |
|------|---------|-------|
| GNR  | Granite Rapids | COM 11, IP 192.168.0.2, Merlin 8.15, FastBoot=True |
| CWF  | Clearwater Forest | COM 11, IP 10.250.0.2, Merlin 8.15, FastBoot=True |
| DMR  | Diamond Rapids | COM 9, IP 192.168.0.2, Merlin 8.23, FastBoot=False |

---

## Agent Entry Points

- **Orchestrator**: `agents/orchestrator.agent.md` — intake, classify, delegate
- **ExperimentAgent**: `agents/experiment.agent.md` — create/validate single experiments
- **FlowAgent**: `agents/flow.agent.md` — build multi-node automation flows

## Quick CLI Reference

```powershell
# List all GNR presets
python DebugFrameworkAgent/scripts/list_presets.py --product GNR

# Generate a blank CWF mesh experiment
python DebugFrameworkAgent/scripts/generate_experiment.py --product CWF --mode mesh --name "CWF_Test"

# Apply a preset
python DebugFrameworkAgent/scripts/apply_preset.py --product GNR --preset gnr_baseline --name "Run1"

# Validate an experiment
python DebugFrameworkAgent/scripts/validate_experiment.py ./output/Run1.json

# Build flow files
python DebugFrameworkAgent/scripts/generate_flow.py --experiments ./output/exps.json --out ./flow/
```

## VS Code Tasks (Ctrl+Shift+P → Tasks: Run Task)

- `DFA: List Presets`
- `DFA: Generate Experiment (interactive)`
- `DFA: Apply Preset (interactive)`
- `DFA: Validate Experiment`
- `DFA: Generate Flow`
- `DFA: Run Tests`

---

## Zero External Dependencies

The core package uses only Python stdlib (`json`, `pathlib`, `argparse`, `re`, `copy`).
The MCP server requires `pip install "mcp[cli]>=1.0"` but is disabled by default.
