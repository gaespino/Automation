# GitHub Actions Integration

DebugFrameworkAgent ships with three GitHub Actions workflows that let you
generate, validate, and catalog experiments directly from your repository —
no local Python environment required.

---

## Prerequisites

1. The `DebugFrameworkAgent/` folder must be at the root of your GitHub repository
   (or adjust the `working-directory` paths in the workflow files to match your layout).
2. The `.github/workflows/` directory must sit at the **repository root** (one level above
   `DebugFrameworkAgent/`).
3. No additional Python packages are needed — the agent uses only stdlib.

### Optional: PPV Integration

If PPV is installed on your self-hosted runner, set the `PPV_ROOT` **repository secret**
to the absolute path of the PPV directory:

```
Settings → Secrets and variables → Actions → New repository secret
Name:  PPV_ROOT
Value: /path/to/PPV
```

When `PPV_ROOT` is set, enum values are validated against the live PPV config; otherwise
the bundled fallback lists are used.

---

## Workflows

### 1. `generate-experiments.yml` — Generate a New Experiment

**Trigger:** Manual (`workflow_dispatch`)

Generates an experiment JSON from a preset or blank template, runs validation,
and uploads the JSON + reports as a workflow artifact.

**Inputs:**

| Input | Default | Description |
|---|---|---|
| `product` | `GNR` | Target product: `GNR`, `CWF`, or `DMR` |
| `preset` | _(blank)_ | Preset key from `defaults/presets/`; leave blank for a blank template |
| `mode` | `mesh` | Test mode for blank experiments: `mesh`, `slice`, `boot`, `linux` |
| `unit_id` | _(blank)_ | Unit identifier — used to name the output folder |
| `overrides` | _(blank)_ | Extra field overrides, one `KEY=VALUE` per line |
| `report_format` | `md,html` | Comma-separated report formats: `md`, `html` |

**Artifact:** `experiment-<PRODUCT>-<run_number>.zip` containing the JSON and reports.

**Example — GNR Dragon run with 50 loops:**
```
product:   GNR
preset:    gnr_dragon_base
overrides: |
  Loops=50
  Test Name=My CI Dragon Run
unit_id:   SND01234567
```

---

### 2. `validate-experiments.yml` — Validate Experiment Files

**Triggers:** Push to `main`/`master`, pull requests, manual dispatch

Scans `DebugFrameworkAgent/output/**/*.json` for experiment files and validates
each one against all constraint rules.

**Features:**
- Posts a **validation summary comment** on pull requests (requires `pull-requests: write` permission)
- Writes a step summary visible in the Actions run UI
- Fails the workflow if any experiment has validation errors
- Warns but continues for advisory issues

**Permissions required** (for PR commenting):
```yaml
permissions:
  contents:      read
  pull-requests: write
```

---

### 3. `list-presets.yml` — List Available Presets

**Trigger:** Manual (`workflow_dispatch`)

Builds a catalog of all presets loaded from `defaults/presets/` and uploads it
as a downloadable artifact.

**Inputs:**

| Input | Default | Description |
|---|---|---|
| `product` | _(all)_ | Filter by product; blank = include all |
| `format` | `json` | Output format: `json` or `markdown` |

**Artifact:** `presets-catalog-<run_number>.zip` containing `presets_catalog.json`
or `presets_catalog.md`.

---

## GitHub Models Client (`github_model_client.py`)

For AI-assisted experiment generation, use the `github_model_client.py` CLI
(or import `GitHubModelClient` in your scripts).

### Setup

Export your GitHub token with Models access:
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

Or in Windows PowerShell:
```powershell
$env:GITHUB_TOKEN = "ghp_your_token_here"
```

### CLI Usage

```bash
# Ask a question with agent context
python scripts/github_model_client.py \
    --agent experiment \
    --message "GNR Dragon experiment, 100 loops, ULX Path FS1:\\EFI\\Release"

# Translate plain English to field overrides (JSON output)
python scripts/github_model_client.py \
    --translate \
    --product GNR \
    --message "dragon content with 50 loops and voltage bump of 0.1 on IA"

# Use a specific model
python scripts/github_model_client.py \
    --model gpt-4o \
    --message "Explain the difference between Mesh and Slice test modes"

# List available GitHub Models
python scripts/github_model_client.py --list-models
```

### Python API

```python
from scripts.github_model_client import GitHubModelClient

client = GitHubModelClient()  # reads GITHUB_TOKEN from env

# One-shot question
answer = client.ask("What is Check Core used for?")

# Question with agent + skill context loaded from .md files
answer = client.ask_with_agent_context(
    "Generate a CWF Dragon experiment with 50 loops",
    agent="experiment",
    extra_skills=["experiment_constraints"],
)

# Translate to field overrides dict  →  pass straight to update_fields()
overrides = client.translate_to_overrides(
    "50 loops, IA voltage bump 0.1, dragon content",
    product="GNR",
)
# overrides == {"Loops": 50, "IA Voltage Bump": 0.1, "Content": "Dragon"}
```

---

## Models

The default model is `gpt-4o-mini` (fast, cheap, good for structured extraction).

Available models include:
- `gpt-4o-mini` (default)
- `gpt-4o`
- `Meta-Llama-3.1-70B-Instruct`
- `Phi-3-medium-128k-instruct`

Run `--list-models` to see the full current catalog from the GitHub Models API.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `GITHUB_TOKEN is not set` | Export `GITHUB_TOKEN` or pass `token=` to the client |
| `GitHub Models API error 401` | Token lacks Models access; generate a new PAT with `read:models` scope |
| Workflow fails on `working-directory: DebugFrameworkAgent` | Ensure this directory exists at repo root |
| PPV enum warnings in CI | Either install PPV on the runner or leave `PPV_ROOT` unset to use bundled fallbacks |
| PR comment not posted | Add `permissions: pull-requests: write` to the workflow job |
