# Getting Started

## Installation

```bash
cd c:\Git\Automation\Portfolio
pip install -r requirements.txt
python app.py
```

Navigate to **http://localhost:8050**.

## Home Page

The home page (`/`) shows two tiles:
- **Unit Portfolio** → navigates to the Dashboard (`/portfolio`)
- **THR Tools** → navigates to the tools hub (`/thr-tools`)

## Navigation

The top navbar provides:
- **THR Tools** brand link → home
- **Unit Portfolio** → Dashboard
- **THR Tools** dropdown → all 9 tool pages

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DATA_PATH` | `Portfolio/data/` | Unit JSON directory |
| `FRAMEWORK_PATH` | UNC production path | DebugFramework files |
| `PORT` | `8050` | HTTP port |
| `DEBUG` | `false` | Dash debug mode |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `HOST` | `0.0.0.0` | Bind address |
