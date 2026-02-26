"""
MCA REST endpoints.
  POST /api/mca/report   — generate MCA report from uploaded Excel
  POST /api/mca/decode   — decode raw MCA register values
"""
from __future__ import annotations
import io
import os
import sys
import tempfile
import traceback
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _backend():
    """Lazily import MCAparser — avoids import-time errors on CaaS."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, here)
    from THRTools.parsers.MCAparser import PPVMCAReport  # type: ignore
    return PPVMCAReport


def _decoder(product: str = "GNR"):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, here)
    from THRTools.Decoder.decoder import decoder  # type: ignore
    return decoder(product=product)


# ---------------------------------------------------------------------------
# /api/mca/report
# ---------------------------------------------------------------------------
@router.post("/report")
async def mca_report(
    file: UploadFile = File(..., description="Bucketer / S2T Logger Excel file"),
    mode: str = Form("Bucketer"),
    product: str = Form("GNR"),
    work_week: str = Form("WW1"),
    label: str = Form(""),
    options: str = Form(""),   # comma-separated: REDUCED,DECODE,OVERVIEW,MCCHECKER
):
    """Generate MCA report and return the output Excel file."""
    raw = await file.read()
    options_list = [o.strip().upper() for o in options.split(",") if o.strip()]

    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, file.filename or "input.xlsx")
        with open(src, "wb") as fh:
            fh.write(raw)

        out = os.path.join(tmpdir, "MCAReport.xlsx")
        try:
            PPVMCAReport = _backend()
            report = PPVMCAReport(
                data_file=src,
                product=product,
                work_week=work_week,
                label=label,
                mode=mode,
            )
            report.run(options=options_list)
            with open(out, "rb") as fh:
                result = fh.read()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Report error: {traceback.format_exc()}")

    return StreamingResponse(
        io.BytesIO(result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="MCAReport_{label or work_week}.xlsx"'},
    )


# ---------------------------------------------------------------------------
# /api/mca/decode
# ---------------------------------------------------------------------------
class DecodeRequest(BaseModel):
    product: str = "GNR"
    bank: str = "CHA"          # CHA | CORE | MEM | IO | PORTIDS
    instance: Optional[str] = None   # e.g. ML2, DCU, B2CMI, UBOX, ...
    mc_status: Optional[str] = None
    mc_addr: Optional[str] = None
    mc_misc: Optional[str] = None
    mc_misc2: Optional[str] = None
    mc_misc3: Optional[str] = None
    mc_misc4: Optional[str] = None


@router.post("/decode")
async def mca_decode(req: DecodeRequest):
    """Decode raw MCA register hex values."""
    try:
        dec = _decoder(req.product)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Decoder init error: {exc}")

    results: dict = {}
    bank = (req.bank or "CHA").upper()

    def _hex(v):
        if not v:
            return None
        try:
            return int(v, 16)
        except ValueError:
            return None

    try:
        if bank == "CHA":
            for field, val in [
                ("MC_STATUS",  req.mc_status),
                ("MC_MISC",    req.mc_misc),
                ("MC_MISC3",   req.mc_misc3),
            ]:
                h = _hex(val)
                if h is not None:
                    results[field] = dec.cha_decoder(h, "MC DECODE")

        elif bank == "CORE":
            instance = (req.instance or "ML2").upper()
            for field, val in [
                ("MC_STATUS",  req.mc_status),
                ("MC_MISC",    req.mc_misc),
            ]:
                h = _hex(val)
                if h is not None:
                    results[field] = dec.core_decoder(h, instance)

        elif bank == "MEM":
            instance = (req.instance or "B2CMI").upper()
            h = _hex(req.mc_status)
            if h is not None:
                results["MC_STATUS"] = dec.mem_decoder(h, instance)

        elif bank == "IO":
            instance = (req.instance or "UBOX").upper()
            h = _hex(req.mc_status)
            if h is not None:
                results["MC_STATUS"] = dec.io_decoder(h, instance)

        elif bank == "PORTIDS":
            h = _hex(req.mc_status)
            if h is not None:
                results["MC_STATUS"] = dec.portids_decoder(h, [], "FirstError")

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Decode error: {traceback.format_exc()}")

    return {"product": req.product, "bank": bank, "results": results}
