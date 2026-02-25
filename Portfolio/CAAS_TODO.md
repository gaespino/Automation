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

**Status:** ✅ RESOLVED in v2.1.0.
`file_open()` in `MCAparser.py` was the only usage — replaced with `openpyxl.load_workbook()`.
`PPVTools.py` import removed (was unused).

---

## 9. Live Experiment Monitoring

**Status:** Dashboard shows static data (last known state). `btn-load-data` is a manual refresh.

**Action needed (future integration stage):**
- Poll or subscribe to Framework server for live experiment status
- WebSocket or SSE endpoint for real-time updates

---

## 10. Automation Designer — Visual Canvas (Drag-and-Drop)

**Status:** Current web implementation is an ordered step-list editor (add/remove/reorder nodes).
The backend logic and export format (`FrameworkAutomationStructure.json`, `FrameworkAutomationFlows.json`,
`FrameworkAutomationInit.ini`, `FrameworkAutomationPositions.json`) is already in
`pages/thr_tools/automation_designer.py` and matches the original PPV designer's output exactly.

**Action needed:**
- Implement drag-and-drop visual canvas using `dash-cytoscape` or a React-based graph library
- The node position metadata (`FrameworkAutomationPositions.json`) is already tracked
  so layout can be preserved when the canvas is implemented
- Connection lines between nodes (currently chain connections) should be customizable
  per port (multi-output: success/fail/majority branches)

**Implementation steps:**
1. `pip install dash-cytoscape` (add to `requirements.txt`)
2. Create cytoscape graph from `ad-nodes-store` and `ad-experiments-store`
3. Map node types to cytoscape node styles using `_NODE_COLORS`
4. Handle drag events to update node x/y in store
5. Add edge drawing for connections (per-port output mapping)

---

## 11. Experiment Builder — Conditional Section Toggle via Callbacks

**Status:** Conditional sections (Loops/Sweep/Shmoo, Linux/Dragon) are pre-rendered
with `display:none` based on initial product config. Dynamic toggling requires a callback
that reads Test Type and Content from the PATTERN-MATCH field store and hides/shows sections.

**Action needed:**
- Add a callback that listens to `eb-field` pattern-match inputs for "Test Type" and "Content"
- On change, toggle visibility of section divs
  (e.g., `eb-section-loops`, `eb-section-sweep`, `eb-section-linux`, `eb-section-dragon`)
- This requires using `dash.ALL` inputs with a section-visibility Output list

---

## 12. MCA Decoder — Register File Upload Parsing

**Status:** Upload field exists in layout but upload content is not yet parsed.

**Action needed:**
- Parse uploaded `.txt` or `.csv` register file (line format: `REGISTER: 0xVALUE`)
- Populate the register input fields from the parsed values
- Run decode automatically after upload

---

## 13. THRTools GUI — Remove Old Deprecated Code (Stage 5)

**Status:** Per the migration plan, the final stage is removing old deprecated code
inside the `Portfolio/` folder (PPV Tkinter GUIs that have been fully replaced by Dash pages).

**Files to remove after verification:**
- `Portfolio/THRTools/gui/PPVTools.py`
- `Portfolio/THRTools/gui/PPVLoopChecks.py`
- `Portfolio/THRTools/gui/PPVDataChecks.py`
- `Portfolio/THRTools/gui/PPVFileHandler.py`
- `Portfolio/THRTools/gui/PPVFrameworkReport.py`
- `Portfolio/THRTools/gui/MCADecoder.py`
- `Portfolio/THRTools/gui/ExperimentBuilder.py`
- `Portfolio/THRTools/gui/AutomationDesigner.py`
- `Portfolio/THRTools/gui/fusefileui.py`
- `Portfolio/THRTools/MCAparser_bkup.py`

**Prerequisite:** All web tool pages must be fully verified before removing desktop GUIs.
