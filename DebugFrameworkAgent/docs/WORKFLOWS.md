# Debug Framework Agent — Workflow Guide

This guide describes end-to-end workflows for the three most common use cases.

---

## Workflow A — Single Experiment from Preset

**Goal:** Create one experiment from an existing preset and export as JSON.

### Steps

```
1. List available presets
   python scripts/list_presets.py --product GNR --category content

2. Apply preset with overrides
   python scripts/apply_preset.py \
     --product GNR \
     --preset gnr_dragon_base_h \
     --name "GNR_Mesh_Run_001" \
     --set Loops=10 "TTL Folder=S:\GNR\RVP\TTLs\TTL_DragonMesh"

3. Validate output (auto-runs as part of apply_preset)
   python scripts/validate_experiment.py output/GNR_Mesh_Run_001.json
```

### Via VS Code
- Run **DFA: List GNR Presets**
- Run **DFA: Apply Preset (interactive)** → choose GNR, enter preset key, enter test name

---

## Workflow B — Blank Experiment with Manual Fields

**Goal:** Build an experiment from scratch for a new test type.

### Steps

```
1. Generate blank template with product defaults
   python scripts/generate_experiment.py \
     --product CWF \
     --mode mesh \
     --name "CWF_Stability_001" \
     --set Loops=50 "Test Time=120" "TTL Folder=R:\Templates\CWF\version_2_0\TTL_DragonMesh"

2. Review and edit output JSON if needed
   code output/CWF_Stability_001.json

3. Validate
   python scripts/validate_experiment.py output/CWF_Stability_001.json
```

---

## Workflow C — Multi-Experiment Automation Flow

**Goal:** Generate TestStructure.json + TestFlows.json for a multi-step automation run.

### Steps

```
1. Create each experiment (repeat for each step)
   python scripts/generate_experiment.py --product GNR --preset gnr_baseline --name "Boot_Step"   --out output/
   python scripts/generate_experiment.py --product GNR --preset gnr_dragon_base_h --name "Stress_Step" --out output/

2. Combine experiments into a batch file (manually or via jq)
   # Windows PowerShell:
   Get-Content output\Boot_Step.json, output\Stress_Step.json |
     ConvertFrom-Json | ConvertTo-Json -Depth 10 > output\flow_experiments.json

3. Generate flow files
   python scripts/generate_flow.py \
     --experiments output/flow_experiments.json \
     --unit-ip 192.168.0.2 \
     --unit-com 11 \
     --out output/flow/

4. Review generated files
   output/flow/TestStructure.json   ← node graph
   output/flow/TestFlows.json       ← experiment bindings
   output/flow/unit_config.ini      ← DUT connection settings
   output/flow/positions.json       ← UI layout hints
```

---

## Workflow D — GitHub Copilot Agent Mode (Phase 2)

**Goal:** Use natural language in Copilot Chat to generate experiments.

### Prerequisites
```
pip install "mcp[cli]>=1.0"
# Edit .vscode/mcp.json — set "disabled": false
# Restart VS Code
```

### Example prompts

```
@debug-framework-agent List all GNR presets in the content category

@debug-framework-agent Generate a DMR Dragon mesh experiment with 10 loops, TTL folder S:\DMR\Tests\TTL_Mesh

@debug-framework-agent Validate this experiment: { ... }

@debug-framework-agent What are the default field values for CWF?
```

### Alternative: Copilot with Agent Files

Without MCP, use GitHub Copilot Chat in Agent Mode pointing at:
- `agents/orchestrator.agent.md` — start here, will route to other agents
- `agents/experiment.agent.md`   — direct experiment creation
- `agents/flow.agent.md`         — direct flow generation

---

## Workflow E — Adding Custom Presets

**Goal:** Share team-specific presets without modifying the main preset file.

### Create a custom presets file

```json
{
  "version": "2.0",
  "common": {
    "my_team_baseline": {
      "description": "Our team's standard baseline",
      "ask_user": ["TTL Folder"],
      "experiment": {
        "Test Name": "TeamBaseline",
        "Loops": 20,
        "Test Time": 90
      }
    }
  }
}
```

### Use it

```
python scripts/list_presets.py --presets-file ./team_presets.json
python scripts/apply_preset.py --preset my_team_baseline --presets-file ./team_presets.json
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| List all presets | `python scripts/list_presets.py` |
| List GNR content presets | `python scripts/list_presets.py --product GNR --category content` |
| Apply preset | `python scripts/apply_preset.py --product GNR --preset KEY --name NAME` |
| Blank experiment | `python scripts/generate_experiment.py --product CWF --mode mesh --name NAME` |
| Validate | `python scripts/validate_experiment.py FILE.json` |
| Build flow | `python scripts/generate_flow.py --experiments FILE.json --out ./flow/` |
| Run tests | `python -m pytest DebugFrameworkAgent/tests/ -v` |
