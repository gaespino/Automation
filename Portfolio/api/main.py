"""
FastAPI entry point for Portfolio THR Tools.
==============================================
Entry point for both local dev and CaaS:
  uvicorn api.main:app --reload          (dev)
  uvicorn api.main:app --host 0.0.0.0    (CaaS)

Routes:
  /api/...        — REST endpoints for all THR Tools
  /thr/           — React SPA (static build from thr_ui/dist)
  /dashboard/     — Dash app (WSGI mounted via starlette)
  /health         — liveness/readiness probe
"""
import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from api.routers import mca, loops, files, framework, fuses, experiments, flow, dpmb

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="THR Tools API",
    description="REST backend for THR Tools – MCA, Experiments, Framework, Fuses, Flow Designer",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# REST routers
# ---------------------------------------------------------------------------
app.include_router(mca.router,          prefix="/api/mca",          tags=["MCA"])
app.include_router(loops.router,        prefix="/api/loops",        tags=["Loops"])
app.include_router(files.router,        prefix="/api/files",        tags=["Files"])
app.include_router(framework.router,    prefix="/api/framework",    tags=["Framework"])
app.include_router(fuses.router,        prefix="/api/fuses",        tags=["Fuses"])
app.include_router(experiments.router,  prefix="/api/experiments",  tags=["Experiments"])
app.include_router(flow.router,         prefix="/api/flow",         tags=["Flow"])
app.include_router(dpmb.router,         prefix="/api/dpmb",         tags=["DPMB"])

# ---------------------------------------------------------------------------
# Mount Dash dashboard (WSGI → ASGI wrapper)
# ---------------------------------------------------------------------------
try:
    from starlette.middleware.wsgi import WSGIMiddleware
    import sys, os
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app import server as dash_flask_server  # noqa: E402
    app.mount("/dashboard", WSGIMiddleware(dash_flask_server))
    logger.info("Dash dashboard mounted at /dashboard/")
except Exception as exc:  # pragma: no cover
    logger.warning("Could not mount Dash dashboard: %s", exc)

# ---------------------------------------------------------------------------
# Serve React SPA
# ---------------------------------------------------------------------------
_DIST = Path(__file__).parent.parent / "thr_ui" / "dist"

if _DIST.exists():
    app.mount("/thr/assets", StaticFiles(directory=str(_DIST / "assets")), name="thr_assets")

    @app.get("/thr/{full_path:path}", include_in_schema=False)
    async def serve_react(full_path: str):
        index = _DIST / "index.html"
        return FileResponse(str(index))

    @app.get("/thr", include_in_schema=False)
    async def serve_react_root():
        return FileResponse(str(_DIST / "index.html"))
else:
    logger.warning(
        "React build not found at %s — run `npm run build` inside thr_ui/ to enable the UI", _DIST
    )

    @app.get("/thr/{full_path:path}", include_in_schema=False)
    @app.get("/thr", include_in_schema=False)
    async def react_not_built(full_path: str = ""):
        return JSONResponse(
            {"error": "React UI not built. Run: cd thr_ui && npm install && npm run build"},
            status_code=503,
        )


# ---------------------------------------------------------------------------
# Health / root
# ---------------------------------------------------------------------------
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def root():
    return {"thr_tools": "/thr/", "dashboard": "/dashboard/", "api_docs": "/docs"}
