"""
File handler REST endpoints.
  POST /api/files/merge   — merge Excel files
  POST /api/files/append  — append tables from source into target
"""
from __future__ import annotations
import io
import os
import sys
import tempfile
import traceback
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()


def _backend():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, here)
    from THRTools.utils.PPVReportMerger import PPVReportMerger  # type: ignore
    return PPVReportMerger


@router.post("/merge")
async def files_merge(
    files: List[UploadFile] = File(..., description="Excel files to merge"),
    prefix: str = Form("", description="File name prefix filter"),
    output_name: str = Form("MergedReport"),
):
    """Merge multiple Excel files into one."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for f in files:
            raw = await f.read()
            dst = os.path.join(tmpdir, f.filename or "file.xlsx")
            with open(dst, "wb") as fh:
                fh.write(raw)

        out = os.path.join(tmpdir, f"{output_name}.xlsx")
        try:
            merger = _backend()()
            merger.merge_excel_files(tmpdir, out, prefix=prefix or None)
            with open(out, "rb") as fh:
                result = fh.read()
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())

    return StreamingResponse(
        io.BytesIO(result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{output_name}.xlsx"'},
    )


@router.post("/append")
async def files_append(
    source: UploadFile = File(..., description="Source Excel (tables to copy from)"),
    target: UploadFile = File(..., description="Target Excel (tables to append into)"),
    sheets: str = Form("", description="Comma-separated sheet names to append"),
):
    """Append tables from source Excel into target Excel."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, source.filename or "source.xlsx")
        tgt_path = os.path.join(tmpdir, target.filename or "target.xlsx")
        with open(src_path, "wb") as fh:
            fh.write(await source.read())
        with open(tgt_path, "wb") as fh:
            fh.write(await target.read())

        sheet_list = [s.strip() for s in sheets.split(",") if s.strip()] or None
        try:
            merger = _backend()()
            merger.append_excel_tables(src_path, tgt_path, sheet_names=sheet_list)
            with open(tgt_path, "rb") as fh:
                result = fh.read()
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())

    return StreamingResponse(
        io.BytesIO(result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{target.filename or "appended.xlsx"}"'},
    )
