"""
DPMB Bucketer Requests REST endpoints.
  POST /api/dpmb/request  — submit a new DPMB job
  GET  /api/dpmb/status   — get last job status for a user/product
"""
from __future__ import annotations
import getpass
import http.client
import json
import traceback

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()

DPMB_HOST = "dpmb-api.intel.com"


class DPMBRequest(BaseModel):
    vidlist: List[str] = Field(..., description="List of Visual IDs")
    user: str = Field(default="", description="Intel username (defaults to OS user)")
    start_year: int = Field(..., description="Start year (e.g. 2025)")
    start_ww: int = Field(..., ge=1, le=52, description="Start work week (1–52)")
    end_year: int = Field(..., description="End year (e.g. 2025)")
    end_ww: int = Field(..., ge=1, le=52, description="End work week (1–52)")
    product: str = Field("GNR3", description="Product code (GNR, GNR3, CWF, DMR)")
    operations: List[str] = Field(default_factory=list, description="Operation codes")


@router.post("/request")
async def dpmb_request(body: DPMBRequest):
    """Submit a new DPMB bucketer job request."""
    user = body.user or _get_user()
    start_ww = f"{body.start_year}{body.start_ww:02d}"
    end_ww = f"{body.end_year}{body.end_ww:02d}"
    delta = str(abs(int(start_ww) - int(end_ww)))
    vid_csv = ",".join(v.strip() for v in body.vidlist if v.strip())
    ops_csv = ",".join(body.operations)

    payload = json.dumps({
        "createdBy": user,
        "endWW": end_ww,
        "operationCsv": ops_csv,
        "product": body.product,
        "scriptId": 1,
        "startWW": start_ww,
        "status": "Pending",
        "updatedBy": user,
        "visualIdCsv": vid_csv,
        "wwDelta": delta,
    })
    headers = {"Content-Type": "application/json"}

    try:
        conn = http.client.HTTPSConnection(DPMB_HOST, timeout=15)
        conn.request("POST", "/api/job/create", payload, headers)
        res = conn.getresponse()
        raw = res.read().decode("utf-8", errors="replace")
        conn.close()
        try:
            return JSONResponse(content=json.loads(raw), status_code=res.status)
        except Exception:
            return JSONResponse(content={"raw": raw}, status_code=res.status)
    except Exception:
        raise HTTPException(status_code=502, detail=traceback.format_exc())


@router.get("/status")
async def dpmb_status(user: str = "", product: str = "GNR3"):
    """Get last DPMB job status for a user/product pair."""
    user = user or _get_user()
    try:
        conn = http.client.HTTPSConnection(DPMB_HOST, timeout=15)
        conn.request("GET", f"/api/job/users/{user}/products/{product}/last", "", {})
        res = conn.getresponse()
        raw = res.read().decode("utf-8", errors="replace")
        conn.close()
        try:
            return JSONResponse(content=json.loads(raw), status_code=res.status)
        except Exception:
            return JSONResponse(content={"raw": raw}, status_code=res.status)
    except Exception:
        raise HTTPException(status_code=502, detail=traceback.format_exc())


@router.get("/current-user")
async def current_user():
    """Return the OS username for pre-filling the user field."""
    return {"user": _get_user()}


def _get_user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return ""
