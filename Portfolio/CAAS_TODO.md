# CaaS Deployment — Deferred Action Items

This file tracks items that are architecturally prepared in the codebase
but require the CaaS environment to be finalized before they can be completed.

---

## 1. Persistent Volume for `data/`

**Status:** Code-ready. `PRODUCTS_DIR` reads from `DATA_PATH` env var (see `config.py`).

**Action needed:**
- Create a CaaS persistent volume claim (PVC) for the data directory
- Configure the container manifest to mount the PVC at the path set in `DATA_PATH`
- Ensure the volume is shared across replicas if horizontal scaling is used

**Manifest snippet (example):**
```yaml
env:
  - name: DATA_PATH
    value: /mnt/portfolio-data
volumeMounts:
  - name: portfolio-data
    mountPath: /mnt/portfolio-data
```

---

## 2. Framework Path — SMB/CIFS Network Mount

**Status:** Code-ready. `FRAMEWORK_PATH` reads from env var; defaults to `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\DebugFramework`.

**Action needed:**
- Configure a CIFS/SMB sidecar or init container to mount the network share
- Set `FRAMEWORK_PATH` env var to the container-local mount point
- Verify network policies allow the container to reach the CIFS server

---

## 3. Production Secrets (API Keys, Credentials)

**Status:** No secrets in codebase currently. Pattern is env-var injection.

**Action needed:**
- Store any required credentials in the CaaS secret store (Vault / k8s Secrets)
- Inject as env vars at runtime — do NOT bake into container image

---

## 4. Horizontal Scaling / Session Affinity

**Status:** `dcc.Store` is client-side — safe for multi-replica out of the box.

**Action needed (if caching is added later):**
- If server-side caching (`flask_caching`, `diskcache`) is introduced, load balancer must enable sticky sessions
- Consider Redis as a shared cache layer if multi-worker is needed

---

## 5. CI/CD Pipeline

**Status:** Not started.

**Action needed:**
- Dockerfile: see template below
- CI: build image on push to `main`, push to CaaS container registry
- CD: rolling update via CaaS manifest

**Dockerfile template:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY Portfolio/ .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8050
CMD ["gunicorn", "app:server", "-b", "0.0.0.0:8050", "--workers=2", "--timeout=120"]
```

**`.dockerignore`:**
```
__pycache__/
*.pyc
*.pyo
venv/
.venv/
.env
Dashboard/
```

---

## 6. TLS / HTTPS

**Status:** Not app-level. Handled by CaaS ingress controller.

**Action needed:**
- Configure ingress with TLS termination
- App can remain plain HTTP internally

---

## 7. Automation Flow Designer — Visual Canvas

**Status:** Current web implementation is an ordered step-list editor (add/remove/reorder steps).

**Action needed:**
- Implement drag-and-drop canvas using `dash-cytoscape` or a React-based graph library
- The backend logic (`AutomationDesigner.py` flow JSON format) is already in `THRTools/gui/`

---

## 8. xlwings Dependency

**Status:** Commented out in `requirements.txt`. Some THRTools backends used xlwings for Excel manipulation.

**Action needed:**
- Audit which functions in `THRTools/` use `xlwings`
- Replace with `openpyxl` equivalents for CaaS compatibility
- `xlwings` requires a local Excel installation — not available in headless containers

---

## 9. Live Experiment Monitoring

**Status:** Dashboard shows static data (last known state). `btn-load-data` is a manual refresh.

**Action needed (future integration stage):**
- Poll or subscribe to Framework server for live experiment status
- WebSocket or SSE endpoint for real-time updates
