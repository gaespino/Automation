"""
MCA REST endpoints.
  POST /api/mca/report   — generate MCA report from uploaded Excel (returns ZIP)
  POST /api/mca/decode   — decode raw MCA register values
"""
from __future__ import annotations
import io
import os
import sys
import tempfile
import traceback
import zipfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _backend():
    """Lazily import PPVMCAReport — avoids import-time errors on CaaS."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, here)
    from THRTools.parsers.MCAparser import PPVMCAReport  # type: ignore
    return PPVMCAReport


def _decoder(product: str = "GNR"):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, here)
    import pandas as pd  # type: ignore
    from THRTools.Decoder.decoder import decoder  # type: ignore
    # decoder requires a data DataFrame — pass a minimal dummy for standalone register decoding
    dummy_df = pd.DataFrame({'VisualId': [1], 'TestName': ['dummy'], 'TestValue': ['0x0']})
    return decoder(data=dummy_df, product=product)


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
    options: str = Form("REDUCED,DECODE,OVERVIEW"),  # default: all three enabled
):
    """Generate MCA report and return a ZIP containing the output file(s).

    Options (comma-separated):
      REDUCED  — reduced data mode (filters noise rows)
      DECODE   — MCA decode tab
      OVERVIEW — unit overview Excel file
    """
    raw = await file.read()
    options_list = [o.strip().upper() for o in options.split(",") if o.strip()]

    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, file.filename or "input.xlsx")
        with open(src, "wb") as fh:
            fh.write(raw)

        try:
            PPVMCAReport = _backend()
            report = PPVMCAReport(
                data_file   = src,
                product     = product,
                work_week   = work_week,
                label       = label,
                mode        = mode,
                output_dir  = tmpdir,
            )
            report.run(options=options_list)
            output_files = report.get_output_files()
        except Exception:
            raise HTTPException(status_code=500, detail=f"Report error: {traceback.format_exc()}")

        if not output_files:
            raise HTTPException(status_code=500, detail="No output files were generated.")

        tag = label or work_week
        if len(output_files) == 1:
            # Single file — return directly
            path, fname = output_files[0]
            with open(path, "rb") as fh:
                result = fh.read()
            return StreamingResponse(
                io.BytesIO(result),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="{fname}"'},
            )

        # Multiple files — pack into ZIP
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, fname in output_files:
                zf.write(path, fname)
        zip_buf.seek(0)
        return StreamingResponse(
            zip_buf,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="MCAReport_{tag}.zip"'},
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
        """Normalize to lowercase hex string with 0x prefix, or None if invalid."""
        if not v:
            return None
        v = v.strip()
        try:
            n = int(v, 16)
            return hex(n)  # e.g. '0x12345678'
        except ValueError:
            return None

    try:
        if bank == "CHA":
            # MC_STATUS: MSCOD decode
            h_status = _hex(req.mc_status)
            if h_status is not None:
                results["MC_STATUS (MSCOD)"] = dec.cha_decoder(h_status, "MC DECODE")

            # MC_MISC: TOR/cache details
            h_misc = _hex(req.mc_misc)
            if h_misc is not None:
                for subfield, stype in [
                    ("MC_MISC (Orig Req)", "Orig Req"),
                    ("MC_MISC (Opcode)",   "Opcode"),
                    ("MC_MISC (CacheState)", "cachestate"),
                    ("MC_MISC (TorID)",    "TorID"),
                    ("MC_MISC (TorFSM)",   "TorFSM"),
                ]:
                    results[subfield] = dec.cha_decoder(h_misc, stype)

            # MC_MISC3: routing details
            h_misc3 = _hex(req.mc_misc3)
            if h_misc3 is not None:
                for subfield, stype in [
                    ("MC_MISC3 (SrcID)",     "SrcID"),
                    ("MC_MISC3 (ISMQ)",      "ISMQ"),
                    ("MC_MISC3 (Attribute)", "Attribute"),
                    ("MC_MISC3 (Result)",    "Result"),
                    ("MC_MISC3 (Local Port)","Local Port"),
                ]:
                    results[subfield] = dec.cha_decoder(h_misc3, stype)

        elif bank == "LLC":
            h_status = _hex(req.mc_status)
            if h_status is not None:
                results["MC_STATUS (MSCOD)"] = dec.llc_decoder(h_status, "MC DECODE")

            h_misc = _hex(req.mc_misc)
            if h_misc is not None:
                for subfield, stype in [
                    ("MC_MISC (RSF)",  "RSF"),
                    ("MC_MISC (LSF)",  "LSF"),
                    ("MC_MISC (MiscV)","MiscV"),
                ]:
                    results[subfield] = dec.llc_decoder(h_misc, stype)

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
