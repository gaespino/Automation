# Changelog

All notable changes to Portfolio will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-02-24

### Added

**Portfolio Unified App**
- Unified Dash `use_pages=True` multi-page application (`app.py`)
- Single Flask server exposed as `app.server` for gunicorn CaaS deployment
- `/health` endpoint returning `200 OK` for CaaS readiness/liveness probes
- Env-var-driven configuration (`config.py`): `DATA_PATH`, `FRAMEWORK_PATH`, `PORT`, `DEBUG`, `LOG_LEVEL`, `HOST`
- Stdout logging setup at startup suitable for container log aggregation
- `run_app.bat` development launcher
- `requirements.txt` merged from Dashboard and PPV with `gunicorn>=21.2.0`
- `CAAS_TODO.md` documenting deferred CaaS items with Dockerfile template

**THRTools Backend**
- Copied PPV project to `THRTools/` as versioned backend
- Tkinter `try/except ImportError` guards added to 4 GUI modules:
  - `THRTools/api/dpmb.py`
  - `THRTools/gui/PPVFileHandler.py`
  - `THRTools/gui/ExperimentBuilder.py`
  - `THRTools/gui/AutomationDesigner.py`
- Replaced module-level `print()` in `AutomationDesigner.py` with `logging.debug()`

**Navigation & Layout**
- Shared `build_navbar()` in `components/navbar.py` with brand, Portfolio link, and THR Tools dropdown
- Landing page (`pages/home.py`, path `/`) with Unit Portfolio and THR Tools tiles

**Unit Portfolio Dashboard**
- Migrated `Dashboard/pages/dashboard.py` to `pages/dashboard.py`
- Registered at `path='/portfolio'` via `dash.register_page()`
- Added missing `import datetime` (used in callbacks 14 and 16)
- All 17 original callbacks preserved intact

**THR Tools Hub**
- Tools hub page (`pages/thr_tools/index.py`, path `/thr-tools`) with 9 tool cards

**THR Tool Pages (9 total)**
- MCA Single Decoder (`/thr-tools/mca-decoder`) — hex decode via `decoder.mcadata`
- PPV MCA Report (`/thr-tools/mca-report`) — analysis report via `MCAparser.ppv_report`
- PTC Loop Parser (`/thr-tools/loop-parser`) — log parsing via `PPVLoopsParser.LogsPTC`
- DPMB Requests (`/thr-tools/dpmb`) — requests via `dpmb.dpmb` (non-GUI class)
- File Handler (`/thr-tools/file-handler`) — merge/append via `PPVReportMerger`
- Fuse File Generator (`/thr-tools/fuse-generator`) — fuse files via `FuseFileGenerator`
- Framework Report Builder (`/thr-tools/framework-report`) — analysis via `ExperimentSummaryAnalyzer`
- Experiment Builder (`/thr-tools/experiment-builder`) — per-product JSON configs
- Automation Flow Designer (`/thr-tools/automation-designer`) — step-list JSON flows

**Documentation**
- `docs/quick_start.md` — 5-minute setup guide
- `docs/architecture.md` — structure, design decisions, CaaS deployment notes
- `docs/user_guide/01-12` — per-tool user guides
- `docs/flows/debug_workflows.md` — end-to-end debug workflows with Mermaid diagrams

**Tests**
- `tests/conftest.py` — pytest fixtures: `app_client`, `mock_config`, `sample_unit_json`
- `tests/test_stage0_caas_config.py` — env vars, /health route, server instance
- `tests/test_stage1_thr_tools_copy.py` — import clean checks, no tkinter at module load
- `tests/test_stage2_app_structure.py` — page registry, expected routes
- `tests/test_stage3_navbar.py` — all 9 tool hrefs, brand/portfolio hrefs
- `tests/test_stage4_home_page.py` — layout validity, tile hrefs
- `tests/test_stage5_thr_hub.py` — all 9 card titles and accent colors
- `tests/test_stage6_tool_pages.py` — layout smoke tests per tool page
- `tests/test_stage6_backends.py` — backend functional parity tests

### Changed

- Dashboard `app.py` replaced by Portfolio `app.py` (superset with CaaS additions)
- Portfolio `config.py` replaces inline path definitions across Dashboard components
- `xlwings` dependency commented out in `requirements.txt` (not CaaS-compatible; see CAAS_TODO.md)

---

## [0.3.0] - 2026-02-20 (Dashboard baseline)

### Added
- Unit Portfolio Dashboard with 17 callbacks
- AG Grid experiment table
- Template and recipe management
- Services layer: data_handler, unit_service, experiment_service, template_service

---

## [0.2.0] - 2026-01-15 (PPV / THR Tools baseline)

### Added
- PPV Tkinter GUI suite (9 tools)
- DPMB API integration
- MCA Decoder with GNR/CWF/DMR support
- Framework Analyzer
- Fuse File Generator
- PTC Loop Parser
- MCA Report generator
- Experiment Builder Tkinter GUI
- Automation Designer Tkinter GUI

---

## [0.1.0] - 2025-11-01

### Added
- Initial PPV project scaffold
- Basic MCA decode functionality
