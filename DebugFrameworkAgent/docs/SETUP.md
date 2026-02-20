# Debug Framework Agent — Setup Guide

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ (3.14.x tested) |
| OS | Windows 10/11 or Linux |
| VS Code | 1.96+ (for MCP Agent Mode) |

No third-party Python packages are required for normal use.
All CLI scripts run on Python stdlib only.

---

## Quick Setup

### 1. Clone / copy this folder

The entire `DebugFrameworkAgent/` folder is self-contained.
You can drop it into any repository or file share.

```
YourRepo/
└── DebugFrameworkAgent/   ← copy here
```

### 2. Verify Python

```powershell
python --version          # should be 3.10+
python scripts/list_presets.py --product GNR
```

If using a venv (recommended):

```powershell
# Windows
.venv\Scripts\activate
python scripts/list_presets.py
```

### 3. Run the test suite

```powershell
# From workspace root
python -m pytest DebugFrameworkAgent/tests/ -v
```

All tests should pass with no additional dependencies.

---

## VS Code Integration

### Tasks

Open the Command Palette (`Ctrl+Shift+P`) → **Tasks: Run Task**
All `DFA:` prefixed tasks are available in `DebugFrameworkAgent/.vscode/tasks.json`.

> These tasks use the `.venv` at the workspace root.
> Update `.vscode/tasks.json` → `"command"` paths if your venv is elsewhere.

### GitHub Copilot Agent Mode (Phase 2 — Optional)

To enable the MCP server for GitHub Copilot:

```powershell
pip install "mcp[cli]>=1.0"
```

Then edit `DebugFrameworkAgent/.vscode/mcp.json`, change:
```json
"disabled": true   →   "disabled": false
```

Restart VS Code and confirm the server appears in
**Copilot Chat → Agent icon → debug-framework-agent**.

---

## Preset File Location

The default preset file is:

```
DebugFrameworkAgent/defaults/experiment_presets.json
```

To override (e.g. for a team-specific preset file):

```powershell
python scripts/list_presets.py --presets-file /path/to/custom_presets.json
```

---

## Output Directory

All generated files are written to `./output/` relative to the working directory unless
`--out` is specified. The directory is created automatically.

---

## Updating Presets

To regenerate `experiment_presets.json` from the generator script
(if you have the full repo):

```powershell
python DEVTOOLS/_generate_presets.py
```

Or edit `defaults/experiment_presets.json` directly — it's plain JSON.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named '_core'` | Run scripts from `DebugFrameworkAgent/scripts/` or the workspace root |
| `FileNotFoundError: experiment_presets.json` | Confirm `defaults/experiment_presets.json` exists in the package |
| MCP server crashes on start | Run `pip install "mcp[cli]>=1.0"` first |
| Tests fail on import | Confirm Python version ≥ 3.10 |
