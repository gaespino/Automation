# Portfolio — Quick Start Guide

> Get the unified THR Tools + Unit Portfolio web app running in under 5 minutes.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| pip | 23+ |

---

## 1. Install dependencies

```bash
cd c:\Git\Automation\Portfolio
pip install -r requirements.txt
```

---

## 2. Configure environment (optional)

The app uses sensible defaults but you can override any setting via environment variable:

```bash
# Windows PowerShell
$env:DATA_PATH      = "C:\path\to\your\data"       # default: Portfolio/data/
$env:FRAMEWORK_PATH = "\\server\share\DebugFramework"  # default: production UNC path
$env:PORT           = "8050"
$env:DEBUG          = "false"
$env:LOG_LEVEL      = "INFO"
```

---

## 3. Run the app

```bash
# Development
python app.py

# Or use the launcher script
run_app.bat
```

Open your browser at **http://localhost:8050**

---

## 4. Production (CaaS / gunicorn)

```bash
gunicorn app:server -b 0.0.0.0:8050 --workers 2
```

Health check endpoint: `GET /health` → `200 OK`

---

## 5. App structure at a glance

| URL | Page |
|---|---|
| `/` | Home — landing page with tool tiles |
| `/portfolio` | Unit Portfolio Dashboard |
| `/thr-tools` | THR Tools hub |
| `/thr-tools/mca-decoder` | MCA Single Decoder |
| `/thr-tools/mca-report` | PPV MCA Report |
| `/thr-tools/loop-parser` | PTC Loop Parser |
| `/thr-tools/dpmb` | DPMB Requests |
| `/thr-tools/file-handler` | File Handler |
| `/thr-tools/fuse-generator` | Fuse File Generator |
| `/thr-tools/framework-report` | Framework Report Builder |
| `/thr-tools/experiment-builder` | Experiment Builder |
| `/thr-tools/automation-designer` | Automation Flow Designer |

---

## 6. Adding a new unit to the Dashboard

Place a properly structured JSON file in `data/{product}/` — see [user_guide/01_getting_started.md](user_guide/01_getting_started.md).

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: tkinter` | Normal — tkinter is guarded; verify no new tkinter import outside a guard |
| `FRAMEWORK_PATH not found` | Set `FRAMEWORK_PATH` env var or use local data |
| `Port 8050 in use` | Set `PORT=8051` env var |
| App shows blank page | Check browser console; usually a missing Dash callback dependency |

---

*For full details see [user_guide/01_getting_started.md](user_guide/01_getting_started.md)*
