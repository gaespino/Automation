# THRHUB — Test Hole Resolution Hub

A unified post-silicon engineering platform for **failing unit root-cause analysis** and experiment management, designed for engineers responsible for GNR, CWF, and DMR product debug.

**Stack:** Flask REST API + React + React Flow + AG Grid

---

## Architecture

```
THRHUB/
├── backend/                    # Flask REST API (Python, no tkinter, no xlwings)
│   ├── app.py                  # Entry point — serves API + React SPA
│   ├── config.py               # Env-var-driven config (CaaS ready)
│   ├── requirements.txt        # Python deps
│   ├── api/
│   │   ├── config.py           # GET /api/config/<product>
│   │   ├── dashboard.py        # /api/dashboard/* (units, stats)
│   │   └── tools.py            # /api/tools/* (experiments, flows, mca, etc.)
│   ├── services/
│   │   ├── data_handler.py     # JSON file storage (no Excel/xlwings)
│   │   ├── unit_service.py     # Unit CRUD + stats
│   │   └── thr_service.py      # MCA decode, loop parser, fuse generator
│   ├── configs/
│   │   ├── GNRControlPanelConfig.json
│   │   ├── CWFControlPanelConfig.json
│   │   └── DMRControlPanelConfig.json
│   └── data/                   # Runtime JSON storage
│
├── frontend/                   # React + Vite frontend
│   ├── package.json
│   ├── vite.config.js          # Proxy /api → :5050, build → backend/static/
│   ├── index.html
│   └── src/
│       ├── App.jsx             # React Router routes
│       ├── main.jsx
│       ├── components/
│       │   ├── Layout.jsx
│       │   └── Navbar.jsx
│       ├── pages/
│       │   ├── Home.jsx        # Landing page
│       │   ├── Dashboard.jsx   # Unit tracking hub (failing units, experiments)
│       │   └── thr-tools/
│       │       ├── ThrToolsHub.jsx      # Tool cards grid
│       │       ├── AutomationDesigner.jsx  ← React Flow canvas
│       │       ├── ExperimentBuilder.jsx   ← Excel-like tab notebook
│       │       ├── MCADecoder.jsx
│       │       ├── MCAReport.jsx
│       │       ├── LoopParser.jsx
│       │       ├── DPMB.jsx
│       │       ├── FileHandler.jsx
│       │       ├── FrameworkReport.jsx
│       │       └── FuseGenerator.jsx
│       ├── services/api.js     # Fetch wrapper for Flask endpoints
│       └── styles/index.css    # Dark premium theme (matching Portfolio)
│
├── run_app.bat                 # Windows launcher
├── run_app.sh                  # Linux/macOS launcher
└── README.md
```

---

## Quick Start

### Local Dev (recommended: separate terminal per service)

**Backend:**
```bash
cd THRHUB/backend
pip install -r requirements.txt
python app.py          # → http://localhost:5050
```

**Frontend (hot-reload dev server):**
```bash
cd THRHUB/frontend
npm install
npm run dev            # → http://localhost:3000  (proxies /api to :5050)
```

### Production / CaaS

```bash
# Build React
cd THRHUB/frontend && npm run build   # → ../backend/static/

# Run Flask (serves API + SPA)
cd THRHUB/backend
gunicorn app:app -b 0.0.0.0:5050 --workers 2
```

Or simply:
```bash
# Windows
THRHUB/run_app.bat

# Linux/macOS
THRHUB/run_app.sh
```

---

## Environment Variables

| Variable       | Default        | Description                          |
|----------------|----------------|--------------------------------------|
| `HOST`         | `0.0.0.0`      | Flask bind host                      |
| `PORT`         | `5050`         | Flask bind port                      |
| `DEBUG`        | `false`        | Flask debug mode                     |
| `LOG_LEVEL`    | `INFO`         | Python log level                     |
| `DATA_PATH`    | `backend/data` | Persistent data root (CaaS: PV mount)|
| `CONFIGS_PATH` | `backend/configs` | Product config JSON directory     |

---

## Tools

| Tool | Route | Description |
|------|-------|-------------|
| Dashboard | `/dashboard` | Unit tracking hub — failing units, experiments, next steps |
| Automation Designer | `/thr-tools/automation-designer` | **React Flow** engineering diagramming — drag-and-drop nodes |
| Experiment Builder | `/thr-tools/experiment-builder` | **Excel-notebook** tab UI — per-product field config (GNR/CWF/DMR) |
| MCA Single Decoder | `/thr-tools/mca-decoder` | Decode MCA register hex values |
| PPV MCA Report | `/thr-tools/mca-report` | Batch MCA decode from bucketer/S2T data |
| PTC Loop Parser | `/thr-tools/loop-parser` | Parse loop logs — pass/fail summary + MCA entries |
| DPMB Requests | `/thr-tools/dpmb` | Build and queue DPMB data requests |
| File Handler | `/thr-tools/file-handler` | Merge DPMB format files, append MCA reports |
| Framework Report | `/thr-tools/framework-report` | Create debug framework reports from unit data |
| Fuse File Generator | `/thr-tools/fuse-generator` | Parse CSV fuse data, filter by product/IP |

---

## Per-Product Configuration

The Experiment Builder and backend services load product-specific field configs from:

- `backend/configs/GNRControlPanelConfig.json`
- `backend/configs/CWFControlPanelConfig.json`
- `backend/configs/DMRControlPanelConfig.json`

Fields can be enabled/disabled per product via `field_enable_config` in each JSON. GNR-specific fields (Pseudo Config, Core License tiers), CWF-specific (Disable 2 Cores), and DMR-specific (Disable 1 Core) are handled automatically.

---

## CaaS Deployment

- **Gunicorn:** `gunicorn app:app -b 0.0.0.0:$PORT --workers 2`
- **Health probe:** `GET /health` → `{"status": "ok"}`
- **DATA_PATH** → persistent volume mount for unit JSON files
- **No xlwings, no tkinter** — all Excel parsing uses `openpyxl`; no GUI dependencies

---

## Key Design Decisions

### React Flow for Automation Designer
The Automation Designer uses [React Flow](https://reactflow.dev/) to provide a true canvas-based node editor, replacing the placeholder list editor in the Dash Portfolio. Engineers can drag nodes, connect them with edges, and export/import flows as JSON.

### Experiment Builder — Excel-notebook UX
Each experiment gets its own tab (matching the original tkinter `ttk.Notebook` tab-per-experiment design). Fields are dynamically enabled/disabled based on the selected product's `ControlPanelConfig.json`. A live JSON preview panel shows the current experiment queue.

### No tkinter / xlwings
All GUI code has been eliminated. `openpyxl` handles Excel files where needed. The Flask + React stack runs cleanly in headless CaaS containers.

### Dark Premium Theme
CSS design system in `src/styles/index.css` mirrors the Portfolio dark palette:
- Background body: `#0a0b10`
- Card background: `#15171e`
- Primary accent (cyan): `#00d4ff`
- Each tool has its own accent color
