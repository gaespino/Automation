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
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()


def _backend():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, here)
    from THRTools.parsers.LoopParser import LoopParser  # type: ignore
    return LoopParser


@router.post("/parse")
async def loops_parse(
    files: List[UploadFile] = File(..., description="Loop log files"),
    seq_key: int = Form(100),
    pysv_format: bool = Form(False),
    output_name: str = Form("LoopReport"),
):
    """Parse PTC loop files and return an Excel report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        saved = []
        for f in files:
            raw = await f.read()
            dst = os.path.join(tmpdir, f.filename or "loop.txt")
            with open(dst, "wb") as fh:
                fh.write(raw)
            saved.append(dst)

        out = os.path.join(tmpdir, f"{output_name}.xlsx")
        try:
            LoopParser = _backend()
            parser = LoopParser(files=saved, seq_key=seq_key, dpmbformat=not pysv_format)
            parser.run(output=out)
            with open(out, "rb") as fh:
                result = fh.read()
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())

    return StreamingResponse(
        io.BytesIO(result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{output_name}.xlsx"'},
    )
