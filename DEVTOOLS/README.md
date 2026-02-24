# DEVTOOLS - Development and Release Management Tools

All deployment, validation, and release tooling for the Debug Framework projects lives here.

---

## Tools at a Glance

| File | Purpose |
|---|---|
| `deploy_universal.py` | Main GUI — Deploy / Reports & Changelog / Release Notes |
| `deploy_agent.py` | CLI validation agent: syntax, lint, tests, draft PR |
| `generate_release_notes.py` | Release notes engine (also callable from Tab 3) |
| `analyze_imports.py` | Import analysis utility for BASELINE directories |
| `launch_deploy_universal.bat` | Windows shortcut to open the main tool |

---

## Universal Deployment Tool (`deploy_universal.py`)

Launch with:

```batch
launch_deploy_universal.bat
```
or
```bash
python deploy_universal.py
```

### Tab 1 — Deploy

Configure source (BASELINE / BASELINE_DMR / PPV), deployment type (DebugFramework / S2T), product (GNR / CWF / DMR), and target directory. Load optional CSVs for import replacement and file renaming. Scan, review diffs, then deploy selected files. Backups are created automatically before every deployment.

### Tab 2 — Reports & Changelog

Scrollable history of all deployments. Click any entry to open its CSV report. Every deployment also appends an entry to:
- `deployment_changelog.json` — machine-readable per-entry log
- `CHANGELOG.md` — human-readable Markdown history

### Tab 3 — Release Notes

Generate formatted release notes from the deployment history, save drafts, export to HTML, or create a draft PR via the `gh` CLI.

### Validation Agent (button in Tab 1)

Opens a log window and streams output from `deploy_agent.py` — syntax validation, lint, quick test run, and draft PR creation.

For full feature details, see [UNIVERSAL_DEPLOY_GUIDE.md](UNIVERSAL_DEPLOY_GUIDE.md) and [UNIVERSAL_DEPLOY_QUICKREF.md](UNIVERSAL_DEPLOY_QUICKREF.md).

---

## Validation Agent (`deploy_agent.py`)

Standalone CLI tool for pre-release checks.

```bash
# Syntax-check all Python files under a target path
python deploy_agent.py --validate --product GNR --target DEVTOOLS

# Lint (auto-detects flake8 / pyflakes / pylint)
python deploy_agent.py --lint --product GNR --target DEVTOOLS

# Quick test run (pytest -x -q)
python deploy_agent.py --test --quick

# Create a draft PR (requires gh CLI)
python deploy_agent.py --pr --draft --title "Release v1.8.0"

# Full check in one pass
python deploy_agent.py --validate --lint --test --quick --product GNR --target DEVTOOLS
```

Each run saves a `check_report_YYYYMMDD_HHMMSS.json` with full results.

For AI/Copilot usage, see [.github/agents/deploy_validator.agent.md](../.github/agents/deploy_validator.agent.md).

---

## Release Notes Generator (`generate_release_notes.py`)

Automates creation of release notes, email drafts, and HTML versions. Can be run standalone or from Tab 3.

```bash
python generate_release_notes.py --start-date 2026-01-22 --version 1.8.0 --html
```

For AI/Copilot: See [deploys/QUICKSTART_RELEASE.md](deploys/QUICKSTART_RELEASE.md)

---

## Configuration Files

| File | Purpose |
|---|---|
| `deploy_config.json` | Source/target paths and similarity threshold |
| `deployment_manifest_debugframework.json` | Filter rules for DebugFramework deployments |
| `deployment_manifest_ppv.json` | Filter rules for PPV deployments |
| `deployment_manifest_s2t.json` | Filter rules for S2T deployments |

### CSV Data Files

| File | Purpose |
|---|---|
| `import_replacement_gnr.csv` | Import rewrite rules for GNR product |
| `import_replacement_cwf.csv` | Import rewrite rules for CWF product |
| `import_replacement_dmr.csv` | Import rewrite rules for DMR product |
| `file_rename_gnr.csv` | File rename rules for GNR product |
| `file_rename_cwf.csv` | File rename rules for CWF product |
| `file_rename_dmr.csv` | File rename rules for DMR product |

---

## Documentation

| Doc | Contents |
|---|---|
| [UNIVERSAL_DEPLOY_GUIDE.md](UNIVERSAL_DEPLOY_GUIDE.md) | Full feature reference for `deploy_universal.py` |
| [UNIVERSAL_DEPLOY_QUICKREF.md](UNIVERSAL_DEPLOY_QUICKREF.md) | Quick-reference workflow card |
| [VISUAL_GUIDE_UNIVERSAL.md](VISUAL_GUIDE_UNIVERSAL.md) | ASCII UI layout diagram |
| [DEPLOYMENT_MANIFEST_GUIDE.md](DEPLOYMENT_MANIFEST_GUIDE.md) | How to use deployment manifests |
| [MANIFEST_QUICKSTART.md](MANIFEST_QUICKSTART.md) | 3-step manifest quick start |
| [DEPLOYMENT_FILE_LISTS.md](DEPLOYMENT_FILE_LISTS.md) | What files go to production per product |
| [CHANGELOG.md](CHANGELOG.md) | Auto-generated deployment history |
