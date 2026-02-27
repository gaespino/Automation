"""
Framework Report REST endpoints.
  GET  /api/framework/vids              — list available VIDs from network server
  POST /api/framework/scan              — scan a folder path, return experiment list
  POST /api/framework/parse             — parse experiment ZIP, return experiment list (upload fallback)
  POST /api/framework/generate          — generate framework report Excel
  POST /api/framework/generate_from_path — generate report from server folder path
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
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

router = APIRouter()

# Network server path (from map_network_drives.ps1 — R: drive)
DATA_SERVER = r"\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\DebugFramework"


def _fpa():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, here)
    import THRTools.parsers.Frameworkparser as fp  # type: ignore
    return fp


# ---------------------------------------------------------------------------
# VID listing from network server
# ---------------------------------------------------------------------------
@router.get("/vids")
async def list_vids(product: str = "GNR"):
    """List Visual IDs (VID folders) available on the network server for a product."""
    product_path = os.path.join(DATA_SERVER, product)
    try:
        vids = sorted([
            e for e in os.listdir(product_path)
            if os.path.isdir(os.path.join(product_path, e))
        ])
        return {"product": product, "vids": vids, "server": DATA_SERVER}
    except Exception as exc:
        return JSONResponse(
            {"product": product, "vids": [], "server": DATA_SERVER,
             "warning": f"Cannot list VIDs: {exc}"},
            status_code=200,
        )


# ---------------------------------------------------------------------------
# Scan a folder path
# ---------------------------------------------------------------------------
@router.post("/scan")
async def framework_scan(folder_path: str = Form(..., description="Local or network folder path")):
    """Scan a local / network folder and return discovered experiments."""
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder_path}")
    try:
        fp = _fpa()
        df = fp.find_files(base_folder=folder_path)
        # df is a list of dicts
        experiments = [d.get("Experiment", "") for d in df if d.get("Experiment")]
        return {"experiments": experiments, "details": df}
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())


# ---------------------------------------------------------------------------
# Parse ZIP upload (browser fallback)
# ---------------------------------------------------------------------------
@router.post("/parse")
async def framework_parse(
    zip_file: UploadFile = File(..., description="ZIP of experiment folder tree"),
):
    """Parse experiment ZIP, return list of discovered experiments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import zipfile as zflib
        raw = await zip_file.read()
        zp = os.path.join(tmpdir, "upload.zip")
        with open(zp, "wb") as fh:
            fh.write(raw)

        extract_dir = os.path.join(tmpdir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with zflib.ZipFile(zp, "r") as z:
                z.extractall(extract_dir)
        except Exception:
            raise HTTPException(status_code=400, detail="Could not extract ZIP file")

        try:
            fp = _fpa()
            data = fp.find_files(base_folder=extract_dir)
            experiments = [d.get("Experiment", "") for d in data if d.get("Experiment")]
            return {"experiments": experiments}
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())


# ---------------------------------------------------------------------------
# Generate report from server / local folder path
# ---------------------------------------------------------------------------
@router.post("/generate_from_path")
async def framework_generate_from_path(
    folder_path: str = Form(..., description="Local or network folder containing VID experiments"),
    experiments_json: str = Form("[]", description="JSON array of experiment config objects"),
    merge: bool = Form(False),
    merge_tag: str = Form(""),
    generate: bool = Form(True),
    report_tag: str = Form(""),
    check_logging: bool = Form(False),
    skip_strings: str = Form(""),
    dragon_data: bool = Form(True),
    core_data: bool = Form(True),
    summary_tab: bool = Form(False),
    overview: bool = Form(True),
    output_name: str = Form("FrameworkReport"),
):
    """Generate framework report from a folder path (network or local)."""
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder_path}")

    experiments = json.loads(experiments_json)
    skip = [s.strip() for s in skip_strings.split(",") if s.strip()]

    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, f"{output_name}.xlsx")
        try:
            fp = _fpa()
            # Build log_dict from experiments
            all_files = fp.find_files(base_folder=folder_path)
            log_dict = _build_log_dict(all_files, experiments)

            if log_dict:
                test_df = fp.parse_log_files(log_dict)
            else:
                import pandas as pd
                test_df = pd.DataFrame()

            if generate and not test_df.empty:
                _write_framework_excel(
                    fp, test_df, out, folder_path,
                    log_dict=log_dict, skip=skip,
                    dragon_data=dragon_data, core_data=core_data,
                    summary_tab=summary_tab, overview=overview,
                )
            elif merge:
                merge_dict = {k: v for k, v in log_dict.items() if v.get("test_type") not in skip}
                fp.framework_merge(merge_dict, out, prefix=merge_tag, skip=skip)
            else:
                raise HTTPException(status_code=400, detail="No action selected (generate or merge).")

            with open(out, "rb") as fh:
                result = fh.read()
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())

    return StreamingResponse(
        io.BytesIO(result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{output_name}.xlsx"'},
    )


# ---------------------------------------------------------------------------
# Generate report from ZIP upload
# ---------------------------------------------------------------------------
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
    dragon_data: bool = Form(True),
    core_data: bool = Form(True),
    summary_tab: bool = Form(False),
    overview: bool = Form(True),
    output_name: str = Form("FrameworkReport"),
):
    """Run full framework report pipeline and return Excel file."""
    experiments = json.loads(experiments_json)
    skip = [s.strip() for s in skip_strings.split(",") if s.strip()]

    with tempfile.TemporaryDirectory() as tmpdir:
        import zipfile as zflib
        raw = await zip_file.read()
        zp = os.path.join(tmpdir, "upload.zip")
        with open(zp, "wb") as fh:
            fh.write(raw)

        extract_dir = os.path.join(tmpdir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with zflib.ZipFile(zp, "r") as z:
                z.extractall(extract_dir)
        except Exception:
            raise HTTPException(status_code=400, detail="Could not extract ZIP")

        out = os.path.join(tmpdir, f"{output_name}.xlsx")
        try:
            fp = _fpa()
            all_files = fp.find_files(base_folder=extract_dir)
            log_dict = _build_log_dict(all_files, experiments)

            if log_dict:
                test_df = fp.parse_log_files(log_dict)
            else:
                import pandas as pd
                test_df = pd.DataFrame()

            if generate and not test_df.empty:
                _write_framework_excel(
                    fp, test_df, out, extract_dir,
                    log_dict=log_dict, skip=skip,
                    dragon_data=dragon_data, core_data=core_data,
                    summary_tab=summary_tab, overview=overview,
                )
            elif merge:
                merge_dict = {k: v for k, v in log_dict.items() if v.get("test_type") not in skip}
                fp.framework_merge(merge_dict, out, prefix=merge_tag, skip=skip)
            else:
                test_df.to_excel(out, index=False)

            with open(out, "rb") as fh:
                result = fh.read()
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())

    return StreamingResponse(
        io.BytesIO(result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{output_name}.xlsx"'},
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _build_log_dict(all_files: list, experiments: list) -> dict:
    """Build log_dict from find_files() output and user-selected experiment configs."""
    # Build name→config lookup from experiments list
    exp_config = {e.get("name", ""): e for e in experiments if e.get("include", True)}

    log_dict = {}
    for entry in all_files:
        exp_name = entry.get("Experiment", "")
        if exp_name not in exp_config:
            continue
        cfg = exp_config[exp_name]
        log_path = entry.get("Log") or entry.get("Excel")
        if not log_path or not os.path.isfile(str(log_path)):
            continue
        log_dict[exp_name] = {
            "path": log_path,
            "test_type": cfg.get("type", "Baseline"),
            "content": cfg.get("content", "Dragon"),
            "comments": cfg.get("comments", ""),
        }
    return log_dict


def _write_framework_excel(fp, test_df, out_path, base_folder, log_dict,
                            skip, dragon_data, core_data, summary_tab, overview):
    """Write test_df and optional extra sheets to out_path."""
    import pandas as pd
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows

    # Use LogSummaryParser if available for richer output
    try:
        lsp = fp.LogSummaryParser({}, test_df)
    except Exception:
        lsp = None

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        test_df.to_excel(writer, sheet_name="Framework Data", index=False)

        if dragon_data and lsp:
            try:
                dragon_df = lsp.get_dragon_data() if hasattr(lsp, "get_dragon_data") else pd.DataFrame()
                if not dragon_df.empty:
                    dragon_df.to_excel(writer, sheet_name="DragonData", index=False)
            except Exception:
                pass

        if core_data and lsp:
            try:
                core_df = lsp.get_core_data() if hasattr(lsp, "get_core_data") else pd.DataFrame()
                if not core_df.empty:
                    core_df.to_excel(writer, sheet_name="CoreData", index=False)
            except Exception:
                pass
