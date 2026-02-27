"""
Loop parser REST endpoints.
  POST /api/loops/parse — run PTC loop parser
"""
from __future__ import annotations
import io
import os
import sys
import tempfile
import traceback
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()


def _backend():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, here)
    from THRTools.parsers.PPVLoopsParser import LogsPTC  # type: ignore
    return LogsPTC


@router.post("/parse")
async def loops_parse(
    files: List[UploadFile] = File(..., description="Loop log files (.txt, .log) or a single ZIP containing them"),
    start_ww: str = Form("WW1", description="Work week (e.g. WW9)"),
    bucket: str = Form("PPV", description="Bucket / experiment identifier"),
    seq_key: int = Form(100, description="Lots sequence key"),
    pysv_format: bool = Form(False, description="Use PySV format instead of DPMB"),
    zipfile_mode: bool = Form(False, description="Look for ZIP files inside the folder"),
    output_name: str = Form("LoopReport"),
):
    """Parse PTC loop files and return an Excel report (.xlsx)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save uploaded files into a temp folder so LogsPTC can scan the folder
        input_dir = os.path.join(tmpdir, "input")
        os.makedirs(input_dir, exist_ok=True)
        for f in files:
            raw = await f.read()
            dst = os.path.join(input_dir, f.filename or "loop.txt")
            with open(dst, "wb") as fh:
                fh.write(raw)

        out = os.path.join(tmpdir, f"{output_name}.xlsx")
        try:
            LogsPTC = _backend()
            parser = LogsPTC(
                StartWW     = start_ww,
                bucket      = bucket,
                LotsSeqKey  = seq_key,
                folder_path = input_dir,
                output_file = out,
                zipfile     = zipfile_mode,
                dpmbformat  = not pysv_format,
            )
            parser.run()
            with open(out, "rb") as fh:
                result = fh.read()
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())

    return StreamingResponse(
        io.BytesIO(result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{output_name}.xlsx"'},
    )
