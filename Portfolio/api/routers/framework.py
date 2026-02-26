"""
Framework Report REST endpoints.
  POST /api/framework/parse     — parse experiment ZIP, return experiment list
  POST /api/framework/generate  — generate framework report Excel
"""
from __future__ import annotations
import io
import json
import os
import sys
import tempfile
import traceback
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


def _backend():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, here)
    from THRTools.parsers.FrameworkParser import FrameworkParser  # type: ignore
    return FrameworkParser


@router.post("/parse")
async def framework_parse(
    zip_file: UploadFile = File(..., description="ZIP of experiment folder tree"),
):
    """Parse experiment ZIP, return list of discovered experiments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import zipfile
        raw = await zip_file.read()
        zp = os.path.join(tmpdir, "upload.zip")
        with open(zp, "wb") as fh:
            fh.write(raw)

        extract_dir = os.path.join(tmpdir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(zp, "r") as z:
                z.extractall(extract_dir)
        except Exception:
            raise HTTPException(status_code=400, detail="Could not extract ZIP file")

        try:
            fpa = _backend()(root=extract_dir)
            experiments = fpa.find_files()
            return {"experiments": experiments, "root": extract_dir}
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())


class GenerateRequest(BaseModel):
    experiments_json: str   # JSON string of experiment config list
    options: dict = {}


@router.post("/generate")
async def framework_generate(
    zip_file: UploadFile = File(..., description="ZIP of experiment folder tree"),
    experiments_json: str = Form(..., description="JSON array of experiment configs"),
    merge: bool = Form(False),
    merge_tag: str = Form(""),
    generate: bool = Form(True),
    report_tag: str = Form(""),
    check_logging: bool = Form(False),
    skip_strings: str = Form(""),
    dragon_data: bool = Form(False),
    core_data: bool = Form(False),
    summary_tab: bool = Form(False),
    overview: bool = Form(False),
    output_name: str = Form("FrameworkReport"),
):
    """Run full framework report pipeline and return Excel file."""
    experiments = json.loads(experiments_json)
    skip = [s.strip() for s in skip_strings.split(",") if s.strip()]

    with tempfile.TemporaryDirectory() as tmpdir:
        import zipfile
        raw = await zip_file.read()
        zp = os.path.join(tmpdir, "upload.zip")
        with open(zp, "wb") as fh:
            fh.write(raw)

        extract_dir = os.path.join(tmpdir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(zp, "r") as z:
                z.extractall(extract_dir)
        except Exception:
            raise HTTPException(status_code=400, detail="Could not extract ZIP")

        out = os.path.join(tmpdir, f"{output_name}.xlsx")
        try:
            fpa = _backend()(root=extract_dir)
            fpa.parse_log_files(experiments)
            fpa.save_to_excel(
                out,
                dragon_data=dragon_data,
                core_data=core_data,
                summary_tab=summary_tab,
                overview=overview,
            )
            if merge:
                fpa.framework_merge(out, tag=merge_tag)
            with open(out, "rb") as fh:
                result = fh.read()
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())

    return StreamingResponse(
        io.BytesIO(result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{output_name}.xlsx"'},
    )
