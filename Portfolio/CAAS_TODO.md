# CaaS Deployment — Deferred Action Items

This file tracks items that are architecturally prepared in the codebase
but require the CaaS environment to be finalized before they can be completed.

---

## Architecture Overview

```
Portfolio/
├── app.py              # Dash server — Dashboard only (mounted at /dashboard/)
├── api/main.py         # FastAPI — main entry point  (uvicorn api.main:app)
│   └── routers/        # REST endpoints for all 7 THR Tools
├── thr_ui/             # React + TypeScript SPA (built to thr_ui/dist/)
│   └── src/pages/      # 8 tool pages + Automation Designer (React Flow)
├── pages/              # Dash pages — Home + Unit Portfolio only
├── components/         # Dash components for Dashboard navbar
├── services/           # Dashboard data services
├── THRTools/           # Pure Python backend logic (no GUI)
│   ├── parsers/        # MCAparser, FrameworkAnalyzer, PPVLoopsParser
│   ├── utils/          # PPVReportMerger, fusefilegenerator, ExcelReportBuilder
│   ├── Decoder/        # MCA decoder (GNR/CWF/DMR)
│   └── configs/        # Fuse configs, product configs
└── tests/              # All tests (pytest)
```

**Entry points:**
- **Dev backend**: `uvicorn api.main:app --reload --port 8000`
- **Dev frontend**: `cd thr_ui && npm run dev` (proxies /api/* to :8000)
- **Production**: `uvicorn api.main:app --host 0.0.0.0 --port 8000`
- **CaaS**: `uvicorn api.main:app` (Dockerfile CMD)
- **Windows launcher**: `run_app.bat` (handles venv, npm build, uvicorn)

---

## 1. Persistent Volume for `data/`

**Status:** Code-ready. `PRODUCTS_DIR` reads from `DATA_PATH` env var.

**Action needed:**
- Create a CaaS PVC for the data directory
- Set `DATA_PATH` env var to the PVC mount point

---

## 2. Framework Path — SMB/CIFS Network Mount

**Status:** Code-ready. `FRAMEWORK_PATH` reads from env var.

**Action needed:**
- Configure CIFS sidecar/init container
- Set `FRAMEWORK_PATH` env var to the container-local mount point

---

## 3. Production Secrets

**Status:** No secrets in codebase. Pattern is env-var injection.

**Action needed:**
- Store credentials in CaaS secret store (Vault / k8s Secrets)
- Inject as env vars at runtime

---

## 4. Containerise

**Status:** Not started. App is ready for containerisation.

**Dockerfile template:**
```dockerfile
FROM node:20-slim AS react-build
WORKDIR /app/thr_ui
COPY Portfolio/thr_ui/package*.json ./
RUN npm ci
COPY Portfolio/thr_ui/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY Portfolio/ .
COPY --from=react-build /app/thr_ui/dist ./thr_ui/dist
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

---

## 5. SSE Streaming for Long-Running Jobs

**Status:** Not implemented. MCA Report and Framework Report may take minutes.

**Action needed:**
- Add `fastapi` `StreamingResponse` or `EventSourceResponse` endpoints
- Client-side: EventSource API in React pages (MCAReport, FrameworkReport)
- Replace the current polling pattern with server-sent events

---

## 6. Auth Middleware

**Status:** Not implemented. All `/api/*` endpoints are currently open.

**Action needed:**
- Add JWT or API-key middleware to FastAPI
- Configure the React SPA to pass auth token in `Authorization: Bearer` header
- Dash dashboard auth via Flask session middleware

---

## 7. TLS / HTTPS

**Status:** Not app-level. Handled by CaaS ingress controller.

---

## 8. React UI — Remaining Pages to Complete

**Status:** Scaffolded. Need full implementation:
- [ ] ExperimentBuilder — dynamic form from ControlPanelConfig.json (product-driven)
- [ ] MCAReport — file upload + SSE progress log stream
- [ ] MCADecoder — register inputs + product-routing (GNR/CWF/DMR)
- [ ] LoopParser — full form implementation
- [ ] FileHandler — merge/append with preview
- [ ] FrameworkReport — ZIP upload + experiment table + SSE progress
- [ ] FuseGenerator — product fuse table with checkboxes + generate

---

## 9. xlwings

**Status:** ✅ RESOLVED in v2.1.0. All Excel I/O uses openpyxl.

---

## 10. Starlette WSGI Middleware

**Status:** ⚠️ `starlette.middleware.wsgi.WSGIMiddleware` is deprecated.

**Action needed:**
- Replace with `a2wsgi.WSGIMiddleware` (`pip install a2wsgi`)
- Change `api/main.py`: `from a2wsgi import WSGIMiddleware`

---

## 11. OpenAPI Schema Validation

**Action needed:**
- Add Pydantic request/response models to all 7 REST routers
- Enables auto-generated docs at `/docs` with proper validation

---

## 12. CI/CD Pipeline

**Status:** Not started.

**Action needed:**
- GitHub Actions workflow: lint → test → build React → build Docker → push image
