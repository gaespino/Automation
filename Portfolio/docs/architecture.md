# Portfolio — Architecture

## Overview

The Portfolio app is a unified single-server Dash/Flask web application that consolidates:
- **Unit Portfolio Dashboard** — experiment tracking and unit data visualization
- **THR Tools** — 9 web-migrated debugging and analysis tools

```
Portfolio/
├── app.py                  # Entry point: Dash app + Flask server + /health route
├── config.py               # All env-var-driven configuration
├── requirements.txt        # Merged dependencies (includes gunicorn)
├── run_app.bat             # Dev launcher
├── CAAS_TODO.md            # Deferred CaaS items
│
├── pages/                  # Dash multi-page routing (use_pages=True)
│   ├── home.py             # / — landing page
│   ├── dashboard.py        # /portfolio — Unit Portfolio Dashboard
│   └── thr_tools/
│       ├── index.py        # /thr-tools — tool hub
│       ├── mca_decoder.py  # /thr-tools/mca-decoder
│       ├── mca_report.py   # /thr-tools/mca-report
│       ├── loop_parser.py  # /thr-tools/loop-parser
│       ├── dpmb.py         # /thr-tools/dpmb
│       ├── file_handler.py # /thr-tools/file-handler
│       ├── fuse_generator.py      # /thr-tools/fuse-generator
│       ├── framework_report.py    # /thr-tools/framework-report
│       ├── experiment_builder.py  # /thr-tools/experiment-builder
│       └── automation_designer.py # /thr-tools/automation-designer
│
├── components/
│   ├── navbar.py           # build_navbar() — shared top nav
│   └── ...                 # (other Dashboard components)
│
├── services/               # Data access layer (from Dashboard)
│   ├── data_handler.py
│   ├── unit_service.py
│   ├── experiment_service.py
│   └── template_service.py
│
├── THRTools/               # Backend logic (copy of PPV — no Tkinter at module level)
│   ├── Decoder/decoder.py
│   ├── parsers/
│   ├── utils/
│   ├── api/dpmb.py         # tkinter-guarded
│   ├── gui/                # tkinter-guarded (4 files)
│   └── configs/            # per-product JSON configs
│
├── assets/                 # CSS + JS (dark theme)
├── data/                   # Unit JSON files (GNR/, SRF/, ...)
├── settings/               # scripts_config.json, templates/
├── docs/                   # This documentation
├── changelog/              # Version history
└── tests/                  # pytest suite
```

---

## Request Flow

```
Browser → Flask (app.server)
           ├── /health           → 200 OK  (CaaS readiness probe)
           └── /                 → Dash routing
                                   ├── layout: Navbar + dcc.Location + page_container
                                   └── pages/{route}.py handles rendering + callbacks
```

---

## Key Design Decisions

### Single Server
All pages run in a single Dash `use_pages=True` app. The Flask `server` object is exposed as
`app.server` for gunicorn (`gunicorn app:server`).

### env-var Configuration
All paths and secrets are read from environment variables in `config.py`. No hardcoded
production paths exist in application logic.

### Tkinter Guards
The 4 THRTools GUI modules that import tkinter at module level have been wrapped:
```python
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
```
This allows the module to be imported cleanly in a headless CaaS environment.

### CSS Design System
Dark theme defined in `assets/style.css`:
- Background body: `#0a0b10`
- Card background: `#15171e`
- Primary accent (cyan): `#00d4ff`
- Secondary accent (purple): `#7000ff`
- Success: `#00ff9d`
- Danger: `#ff4d4d`

Each THR tool has its own accent color for visual identity.

### Per-Product Configuration
`THRTools/configs/{product}ControlPanelConfig.json` files drive which fields are
enabled in the Experiment Builder. Loading is graceful — missing config = all fields enabled.

---

## CaaS Deployment

See [../CAAS_TODO.md](../CAAS_TODO.md) for full list of remaining items.

Quick summary:
- `gunicorn app:server -b 0.0.0.0:$PORT --workers 2`
- `DATA_PATH` → persistent volume mount
- `FRAMEWORK_PATH` → CIFS/SMB sidecar or init container mount
- `/health` → readiness/liveness probe target
- stdout logging → captured by container runtime log aggregator

---

## Adding a New Tool Page

1. Create `pages/thr_tools/{tool_name}.py`
2. Add `dash.register_page(__name__, path='/thr-tools/{slug}', name='...', title='...')`
3. Define `layout` + callbacks with unique ID prefix (e.g. `tn-`)
4. Add entry to `components/navbar.py` `TOOLS` list
5. Add card to `pages/thr_tools/index.py` `TOOLS` list
6. Add test in `tests/test_stage6_tool_pages.py`
