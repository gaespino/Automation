"""
Framework Report REST endpoints.
  GET  /api/framework/vids              — list available VIDs from network server
  POST /api/framework/scan              — scan a folder path, return experiment list
  POST /api/framework/parse             — parse experiment ZIP, return experiment list (upload fallback)
  POST /api/framework/generate          — generate framework report Excel
  POST /api/framework/generate_from_path — generate report from server folder path
  POST /api/framework/save_to_folder    — save report files directly to disk
  GET  /api/framework/sheets            — list sheet names for a cached report
  GET  /api/framework/sheet_data        — return JSON data for a specific sheet
"""
from __future__ import annotations
import io
import json
import os
import sys
import tempfile
import traceback
import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

router = APIRouter()

# Network server path (from map_network_drives.ps1 — R: drive)
DATA_SERVER = r"\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\DebugFramework"

# In-memory report cache: {token: {filename: bytes}}
_fw_report_cache: dict[str, dict[str, bytes]] = {}

# Type keywords to infer test type from experiment or date folder name
_TYPE_KEYWORDS = ['Loops', 'Voltage', 'Frequency', 'Shmoo', 'Sweep', 'Invalid']


def _infer_type(name: str) -> str:
    """Try to infer test type from experiment or date folder name."""
    name_lower = name.lower()
    for kw in _TYPE_KEYWORDS:
        if kw.lower() in name_lower:
            return kw
    return ''


def _fpa():
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
@router.post("/debug_scan")
async def framework_debug_scan(folder_path: str = Form(...)):
    """Return full diagnostic breakdown of what the scan sees for a VID folder.
    Shows: discovered experiments, all JSON files parsed, all config keys found,
    how each experiment name matches (or fails to match) a PPV config key."""
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder_path}")
    try:
        fp = _fpa()
        df = fp.find_files(base_folder=folder_path)
        records = df.to_dict('records') if hasattr(df, 'to_dict') else list(df)

        _SKIP_META = frozenset(['_meta', 'unit_data', 'templates', 'saved_date', 'tool', 'file_type'])
        json_files_parsed: list[dict] = []
        json_config: dict[str, dict] = {}

        for fname in sorted(os.listdir(folder_path)):
            if not fname.lower().endswith('.json'):
                continue
            fpath = os.path.join(folder_path, fname)
            try:
                with open(fpath, encoding='utf-8') as fh:
                    cfg = json.load(fh)
                non_meta = {k: v for k, v in cfg.items()
                            if k not in _SKIP_META and not k.startswith('_')} if isinstance(cfg, dict) else {}
                is_multi = bool(non_meta) and all(isinstance(v, dict) for v in non_meta.values())

                keys_added: list[str] = []
                if isinstance(cfg, dict):
                    if fname.lower() == 'framework_report_config.json':
                        json_files_parsed.append({
                            "file": fname, "format": "framework_report_config",
                            "keys": list(cfg.get("experiments", {}).keys()),
                            "opts": cfg.get("opts", {}),
                            "last_updated": cfg.get("last_updated", ""),
                        })
                        continue
                    if is_multi:
                        for exp_key, exp_data in non_meta.items():
                            json_config[exp_key] = {
                                "content":   exp_data.get("Content") or "",
                                "type":      exp_data.get("Type") or exp_data.get("Test Type") or "",
                                "otherType": exp_data.get("CustomType") or "",
                                "comments":  exp_data.get("Comments") or exp_data.get("Notes") or "",
                                "include":   bool(exp_data["Include"]) if "Include" in exp_data else exp_data.get("Experiment", "Enabled") != "Disabled",
                            }
                            keys_added.append(exp_key)
                            inner = exp_data.get("Test Name") or ""
                            if inner and inner != exp_key:
                                json_config.setdefault(inner, json_config[exp_key])
                                keys_added.append(f"(alias) {inner}")
                    else:
                        key = cfg.get("Test Name") or fname[:-5]
                        if key:
                            json_config[key] = {
                                "content":   cfg.get("Content") or "",
                                "type":      cfg.get("Type") or cfg.get("Test Type") or "",
                                "otherType": cfg.get("CustomType") or "",
                                "comments":  cfg.get("Comments") or cfg.get("Notes") or "",
                                "include":   bool(cfg["Include"]) if "Include" in cfg else cfg.get("Experiment", "Enabled") != "Disabled",
                            }
                            keys_added.append(key)
                json_files_parsed.append({
                    "file": fname, "format": "multi" if is_multi else "single",
                    "keys_added": keys_added, "top_level_keys": list(non_meta.keys())[:20],
                })
            except Exception as exc:
                json_files_parsed.append({"file": fname, "error": str(exc)})

        # fw config
        fw_config: dict[str, dict] = {}
        fw_config_path = os.path.join(folder_path, "framework_report_config.json")
        fw_info: dict = {}
        if os.path.isfile(fw_config_path):
            try:
                with open(fw_config_path, encoding='utf-8') as fh:
                    fw_saved = json.load(fh)
                fw_config = fw_saved.get("experiments", {})
                fw_info = {"last_updated": fw_saved.get("last_updated", ""),
                           "experiment_count": len(fw_config),
                           "experiment_keys": list(fw_config.keys()),
                           "opts": fw_saved.get("opts", {})}
            except Exception as exc:
                fw_info = {"error": str(exc)}

        json_config_ci = {k.lower(): v for k, v in json_config.items()}

        def _ppv_lookup_debug(exp_name: str) -> tuple[dict, str]:
            if exp_name in json_config:
                return json_config[exp_name], f"exact match '{exp_name}'"
            el = exp_name.lower()
            if el in json_config_ci:
                return json_config_ci[el], f"case-insensitive match '{el}'"
            parts = el.split('_')
            for start in range(1, len(parts)):
                suffix = '_'.join(parts[start:])
                if len(suffix) > 4 and suffix in json_config_ci:
                    return json_config_ci[suffix], f"suffix match '{suffix}'"
            return {}, "NO MATCH"

        seen: set = set()
        experiment_resolution: list[dict] = []
        for d in records:
            exp = d.get("Experiment", "")
            if not exp or exp in seen:
                continue
            seen.add(exp)
            ppv, match_method = _ppv_lookup_debug(exp)
            fw = fw_config.get(exp, {})
            resolved = {
                "experiment": exp,
                "ppv_match": match_method,
                "ppv_content":  ppv.get("content", ""),
                "ppv_type":     ppv.get("type", ""),
                "ppv_include":  ppv.get("include", True),
                "fw_content":   fw.get("content", ""),
                "fw_type":      fw.get("type", ""),
                "fw_include":   fw.get("include", None),
                "resolved_content": fw.get("content") or ppv.get("content") or d.get("Platform") or "Dragon",
                "resolved_type":    fw.get("type") or ppv.get("type") or _infer_type(exp) or "Baseline",
                "resolved_include": fw.get("include", ppv.get("include", True)),
            }
            experiment_resolution.append(resolved)

        return {
            "folder": folder_path,
            "experiments_discovered": len(experiment_resolution),
            "json_files_parsed": json_files_parsed,
            "ppv_config_keys": list(json_config.keys()),
            "framework_report_config": fw_info,
            "experiment_resolution": experiment_resolution,
        }
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.post("/scan")
async def framework_scan(folder_path: str = Form(..., description="Local or network folder path")):
    """Scan a local / network folder and return discovered experiments."""
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder_path}")
    try:
        fp = _fpa()
        df = fp.find_files(base_folder=folder_path)
        records = df.to_dict('records') if hasattr(df, 'to_dict') else list(df)

        # Load JSON config files from the VID root folder (PPV experiment configs).
        # Supports two formats produced by PPV ExperimentBuilder:
        #   Multi-experiment:  { "ExpKey": { "Experiment": "Enabled", "Content": ..., ... }, ... }
        #   Single-experiment: { "Test Name": "X", "Content": ..., ... }
        _SKIP_META = frozenset(['_meta', 'unit_data', 'templates', 'saved_date', 'tool', 'file_type'])
        json_config: dict[str, dict] = {}
        try:
            for fname in os.listdir(folder_path):
                if not fname.lower().endswith('.json'):
                    continue
                if fname.lower() == 'framework_report_config.json':
                    continue  # handled separately below
                fpath = os.path.join(folder_path, fname)
                try:
                    with open(fpath, encoding='utf-8') as fh:
                        cfg = json.load(fh)
                    if not isinstance(cfg, dict):
                        continue
                    # Detect multi-experiment format: all values (excluding meta keys) are dicts
                    non_meta = {k: v for k, v in cfg.items()
                                if k not in _SKIP_META and not k.startswith('_')}
                    is_multi = bool(non_meta) and all(isinstance(v, dict) for v in non_meta.values())
                    if is_multi:
                        # Multi-experiment export: outer key is the experiment folder name
                        for exp_key, exp_data in non_meta.items():
                            entry = {
                                "content":   exp_data.get("Content") or "",
                                "type":      exp_data.get("Type") or exp_data.get("Test Type") or "",
                                "otherType": exp_data.get("CustomType") or "",
                                "comments":  exp_data.get("Comments") or exp_data.get("Notes") or "",
                                "include":   bool(exp_data["Include"]) if "Include" in exp_data else exp_data.get("Experiment", "Enabled") != "Disabled",
                            }
                            json_config[exp_key] = entry
                            # Also register inner "Test Name" as an alternative lookup key
                            inner = exp_data.get("Test Name") or ""
                            if inner and inner != exp_key:
                                json_config.setdefault(inner, entry)
                    else:
                        # Single-experiment flat format
                        key = cfg.get("Test Name") or fname[:-5]
                        if key:
                            json_config[key] = {
                                "content":   cfg.get("Content") or "",
                                "type":      cfg.get("Type") or cfg.get("Test Type") or "",
                                "otherType": cfg.get("CustomType") or "",
                                "comments":  cfg.get("Comments") or cfg.get("Notes") or "",
                                "include":   bool(cfg["Include"]) if "Include" in cfg else cfg.get("Experiment", "Enabled") != "Disabled",
                            }
                except Exception:
                    pass
        except Exception:
            pass

        # Load include overrides from Config.json (_last_updated / _opts stored inline)
        # Falls back to legacy framework_report_config.json for backward compat.
        fw_config: dict[str, dict] = {}
        fw_config_timestamp = ""
        fw_opts: dict = {}
        config_json_path = os.path.join(folder_path, "Config.json")
        try:
            if os.path.isfile(config_json_path):
                with open(config_json_path, encoding='utf-8') as fh:
                    cfg_raw = json.load(fh)
                fw_config_timestamp = cfg_raw.get("_last_updated", "")
                fw_opts = cfg_raw.get("_opts", {})
        except Exception:
            pass
        # Backward-compat fallback: read legacy framework_report_config.json if
        # Config.json has no _opts yet (i.e. save_config hasn't been used yet).
        if not fw_opts:
            legacy_path = os.path.join(folder_path, "framework_report_config.json")
            try:
                if os.path.isfile(legacy_path):
                    with open(legacy_path, encoding='utf-8') as fh:
                        fw_saved = json.load(fh)
                    if not fw_config_timestamp:
                        fw_config_timestamp = fw_saved.get("last_updated", "")
                    fw_opts = fw_saved.get("opts", {})
            except Exception:
                pass

        # Precompute case-insensitive PPV lookup to handle minor naming differences
        json_config_ci = {k.lower(): v for k, v in json_config.items()}

        def _ppv_lookup(exp_name: str) -> dict:
            """Exact → case-insensitive exact → underscore-boundary suffix match."""
            result = json_config.get(exp_name)
            if result:
                return result
            el = exp_name.lower()
            result = json_config_ci.get(el)
            if result:
                return result
            # Handles date-prefixed folders: "2025_01_15_LoopName" → match "LoopName"
            parts = el.split('_')
            for start in range(1, len(parts)):
                suffix = '_'.join(parts[start:])
                if len(suffix) > 4 and suffix in json_config_ci:
                    return json_config_ci[suffix]
            return {}

        # Build one clean detail entry per unique experiment
        seen: set = set()
        details = []
        for d in records:
            exp = d.get("Experiment", "")
            if not exp or exp in seen:
                continue
            seen.add(exp)
            platform = str(d.get("Platform") or "Dragon")
            date_str  = str(d.get("Date") or "")
            ppv = _ppv_lookup(exp)
            # PPV Config.json is the single source of truth for content/type/include.
            # If it has an entry (even blank fields), respect them as-is.
            # Only infer defaults when the experiment isn't in Config.json at all.
            if ppv:
                resolved_content = ppv.get("content", "")
                resolved_type    = ppv.get("type", "")
            else:
                resolved_content = ""
                resolved_type    = _infer_type(exp) or _infer_type(date_str) or ""
            details.append({
                "name":     exp,
                "content":  resolved_content,
                "type":     resolved_type,
                "comments": ppv.get("comments", ""),
                "include":  ppv.get("include", True),
                "otherType": ppv.get("otherType", ""),
            })

        experiments = [d["name"] for d in details]
        return {"experiments": experiments, "details": details,
                "config_timestamp": fw_config_timestamp, "opts": fw_opts}
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
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
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
            records = data.to_dict('records') if hasattr(data, 'to_dict') else list(data)
            seen: set = set()
            details = []
            for d in records:
                exp = d.get("Experiment", "")
                if not exp or exp in seen:
                    continue
                seen.add(exp)
                platform = str(d.get("Platform") or "Dragon")
                date_str  = str(d.get("Date") or "")
                details.append({
                    "name": exp,
                    "content": platform or "Dragon",
                    "type": _infer_type(exp) or _infer_type(date_str) or "Baseline",
                    "comments": "",
                })
            experiments = [d["name"] for d in details]
            return {"experiments": experiments, "details": details}
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())


# ---------------------------------------------------------------------------
# Save experiment config back to network / local folder
# ---------------------------------------------------------------------------
@router.post("/save_config")
async def framework_save_config(
    folder_path: str = Form(..., description="VID root folder path (local or network)"),
    experiments_json: str = Form(..., description="JSON array of experiment config objects"),
    opts_json: str = Form("{}", description="JSON object of global report options to persist"),
    expected_timestamp: str = Form("", description="Timestamp from when config was loaded; empty = skip conflict check"),
    force: bool = Form(False, description="Overwrite even if a concurrent edit is detected"),
):
    """Save experiment configuration back to Config.json (PPV format) in the VID folder.

    Experiment fields are written in PPV format (Type / CustomType / Include / Content / Comments).
    Report options (merge, generate, etc.) are stored under the reserved '_opts' key, which PPV
    ignores because keys starting with '_' are excluded from experiment detection.
    """
    import datetime
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder_path}")
    config_json_path = os.path.join(folder_path, "Config.json")
    # Concurrent-edit guard via _last_updated stored inside Config.json.
    if expected_timestamp and not force and os.path.isfile(config_json_path):
        try:
            with open(config_json_path, encoding='utf-8') as fh:
                existing = json.load(fh)
            existing_ts = existing.get("_last_updated", "")
            if existing_ts and existing_ts != expected_timestamp:
                return JSONResponse(
                    status_code=409,
                    content={"conflict_timestamp": existing_ts},
                )
        except Exception:
            pass  # unreadable → proceed
    try:
        experiments = json.loads(experiments_json)
        saved_opts = json.loads(opts_json) if opts_json and opts_json != '{}' else {}
        new_timestamp = datetime.datetime.now().isoformat(timespec='seconds')

        # Read existing Config.json so we preserve any keys we don't manage
        existing_cfg: dict = {}
        if os.path.isfile(config_json_path):
            try:
                with open(config_json_path, encoding='utf-8') as fh:
                    existing_cfg = json.load(fh)
            except Exception:
                pass

        # Build updated Config.json: preserve existing entries (and _ / meta keys),
        # then overwrite only the experiments we received from the UI.
        new_cfg: dict = {}
        # Carry over _ keys and meta keys first (preserves PPV tool metadata)
        _SKIP_META = frozenset(['_meta', 'unit_data', 'templates', 'saved_date', 'tool', 'file_type'])
        for k, v in existing_cfg.items():
            if k.startswith('_') or k in _SKIP_META:
                new_cfg[k] = v
        # Write experiment entries in PPV format
        for e in experiments:
            name = e.get("name")
            if not name:
                continue
            existing_entry = existing_cfg.get(name, {})
            new_cfg[name] = {
                "Type":       e.get("type", "") if e.get("type") is not None else existing_entry.get("Type", ""),
                "CustomType": e.get("otherType", "") or existing_entry.get("CustomType", ""),
                "Include":    bool(e.get("include", existing_entry.get("Include", False))),
                "Content":    e.get("content", "") if e.get("content") is not None else existing_entry.get("Content", ""),
                "Comments":   e.get("comments", "") or existing_entry.get("Comments", ""),
            }
        # Store web-UI opts and timestamp under reserved _ keys
        new_cfg["_opts"] = saved_opts
        new_cfg["_last_updated"] = new_timestamp

        with open(config_json_path, 'w', encoding='utf-8') as fh:
            json.dump(new_cfg, fh, indent=4)
        return {"saved": config_json_path, "count": len(experiments), "timestamp": new_timestamp}
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
    merge_tag: str = Form("Summary"),
    merge_output_name: str = Form("MergedSummary"),
    generate: bool = Form(False),
    report_tag: str = Form(""),
    check_logging: bool = Form(False),
    skip_strings: str = Form(""),
    dragon_data: bool = Form(False),
    core_data: bool = Form(False),
    summary_tab: bool = Form(False),
    overview: bool = Form(False),
    output_name: str = Form("FrameworkReport"),
):
    """Generate framework report from a folder path (network or local)."""
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder_path}")
    if not merge and not generate:
        raise HTTPException(status_code=400, detail="No action selected (enable Generate Report and/or Merge Summary).")

    experiments = json.loads(experiments_json)
    skip = [s.strip() for s in skip_strings.split(",") if s.strip()]

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        try:
            fp = _fpa()
            all_files = fp.find_files(base_folder=folder_path)
            log_dict = _build_log_dict(all_files, experiments)

            if log_dict:
                test_df = fp.parse_log_files(log_dict)
            else:
                import pandas as pd
                test_df = pd.DataFrame()

            generated_files = []  # list of (filename, bytes)

            if generate and not test_df.empty:
                report_out = os.path.join(tmpdir, f"{output_name}.xlsx")
                _write_framework_excel(
                    fp, test_df, report_out, folder_path,
                    log_dict=log_dict, skip=skip,
                    dragon_data=dragon_data, core_data=core_data,
                    summary_tab=summary_tab, overview=overview,
                )
                with open(report_out, "rb") as fh:
                    generated_files.append((f"{output_name}.xlsx", fh.read()))

            if merge:
                # framework_merge requires excel_path_dict (Summary Excel files)
                find_df = all_files
                selected_exps = list(log_dict.keys())
                import pandas as pd
                filtered_df = find_df[find_df["Experiment"].isin(selected_exps)] if hasattr(find_df, '__len__') and len(find_df) else find_df
                try:
                    type_values    = {k: v.get("test_type", "Baseline") for k, v in log_dict.items()}
                    content_values = {k: v.get("content",   "Dragon")   for k, v in log_dict.items()}
                    excel_path_dict = fp.create_file_dict(filtered_df, "Excel", type_values, content_values)
                except Exception:
                    excel_path_dict = {}
                # Pre-flight: ensure at least one Excel file exists to merge
                excel_files_exist = any(
                    isinstance(v, dict)
                    and os.path.isfile(str(v.get('path', '')))
                    and str(v.get('path', '')).lower().endswith(('.xlsx', '.xls'))
                    for v in excel_path_dict.values()
                )
                if not excel_files_exist:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Merge Summary requires existing Excel summary files in the experiment "
                            "folders. Run 'Generate Report' first to produce per-experiment Excel "
                            "outputs, or ensure the framework has already written Excel files into "
                            "this VID folder."
                        ),
                    )
                merge_out = os.path.join(tmpdir, f"{merge_output_name}.xlsx")
                fp.framework_merge(file_dict=excel_path_dict, output_file=merge_out, prefix=merge_tag, skip=skip)
                with open(merge_out, "rb") as fh:
                    generated_files.append((f"{merge_output_name}.xlsx", fh.read()))

            if not generated_files:
                raise HTTPException(status_code=400, detail="No files generated — check log files and folder structure.")

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())

    # Cache for sheet preview
    report_token = str(uuid.uuid4())
    _fw_report_cache[report_token] = {fname: data for fname, data in generated_files}
    expose = "X-Report-Token, X-Report-Sheets"

    # If both files, return a ZIP; otherwise stream single file
    if len(generated_files) == 2:
        import zipfile as zflib
        buf = io.BytesIO()
        with zflib.ZipFile(buf, "w", zflib.ZIP_DEFLATED) as zf:
            for fname, data in generated_files:
                zf.writestr(fname, data)
        buf.seek(0)
        zip_name = f"{output_name}_files.zip"
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_name}"',
                "X-Report-Token": report_token,
                "Access-Control-Expose-Headers": expose,
            },
        )
    else:
        fname, data = generated_files[0]
        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{fname}"',
                "X-Report-Token": report_token,
                "Access-Control-Expose-Headers": expose,
            },
        )


# ---------------------------------------------------------------------------
# Generate report from ZIP upload
# ---------------------------------------------------------------------------
@router.post("/generate")
async def framework_generate(
    zip_file: UploadFile = File(..., description="ZIP of experiment folder tree"),
    experiments_json: str = Form(..., description="JSON array of experiment configs"),
    merge: bool = Form(False),
    merge_tag: str = Form("Summary"),
    merge_output_name: str = Form("MergedSummary"),
    generate: bool = Form(False),
    report_tag: str = Form(""),
    check_logging: bool = Form(False),
    skip_strings: str = Form(""),
    dragon_data: bool = Form(False),
    core_data: bool = Form(False),
    summary_tab: bool = Form(False),
    overview: bool = Form(False),
    output_name: str = Form("FrameworkReport"),
):
    """Run full framework report pipeline and return Excel file(s)."""
    if not merge and not generate:
        raise HTTPException(status_code=400, detail="No action selected (enable Generate Report and/or Merge Summary).")
    experiments = json.loads(experiments_json)
    skip = [s.strip() for s in skip_strings.split(",") if s.strip()]

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
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

        try:
            fp = _fpa()
            all_files = fp.find_files(base_folder=extract_dir)
            log_dict = _build_log_dict(all_files, experiments)

            if log_dict:
                test_df = fp.parse_log_files(log_dict)
            else:
                import pandas as pd
                test_df = pd.DataFrame()

            generated_files = []  # list of (filename, bytes)

            if generate and not test_df.empty:
                report_out = os.path.join(tmpdir, f"{output_name}.xlsx")
                _write_framework_excel(
                    fp, test_df, report_out, extract_dir,
                    log_dict=log_dict, skip=skip,
                    dragon_data=dragon_data, core_data=core_data,
                    summary_tab=summary_tab, overview=overview,
                )
                with open(report_out, "rb") as fh:
                    generated_files.append((f"{output_name}.xlsx", fh.read()))

            if merge:
                find_df = all_files
                selected_exps = list(log_dict.keys())
                import pandas as pd
                filtered_df = find_df[find_df["Experiment"].isin(selected_exps)] if hasattr(find_df, '__len__') and len(find_df) else find_df
                try:
                    type_values    = {k: v.get("test_type", "Baseline") for k, v in log_dict.items()}
                    content_values = {k: v.get("content",   "Dragon")   for k, v in log_dict.items()}
                    excel_path_dict = fp.create_file_dict(filtered_df, "Excel", type_values, content_values)
                except Exception:
                    excel_path_dict = {}
                # Pre-flight: ensure at least one Excel file exists to merge
                excel_files_exist = any(
                    isinstance(v, dict)
                    and os.path.isfile(str(v.get('path', '')))
                    and str(v.get('path', '')).lower().endswith(('.xlsx', '.xls'))
                    for v in excel_path_dict.values()
                )
                if not excel_files_exist:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Merge Summary requires existing Excel summary files in the experiment "
                            "folders. Run 'Generate Report' first to produce per-experiment Excel "
                            "outputs, or ensure the framework has already written Excel files into "
                            "this VID folder."
                        ),
                    )
                merge_out = os.path.join(tmpdir, f"{merge_output_name}.xlsx")
                fp.framework_merge(file_dict=excel_path_dict, output_file=merge_out, prefix=merge_tag, skip=skip)
                with open(merge_out, "rb") as fh:
                    generated_files.append((f"{merge_output_name}.xlsx", fh.read()))

            if not generated_files:
                raise HTTPException(status_code=400, detail="No files generated — check log files and folder structure.")

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())

    # Cache for sheet preview
    report_token = str(uuid.uuid4())
    _fw_report_cache[report_token] = {fname: data for fname, data in generated_files}
    expose = "X-Report-Token, X-Report-Sheets"

    if len(generated_files) == 2:
        buf = io.BytesIO()
        with zflib.ZipFile(buf, "w", zflib.ZIP_DEFLATED) as zf:
            for fname, data in generated_files:
                zf.writestr(fname, data)
        buf.seek(0)
        zip_name = f"{output_name}_files.zip"
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_name}"',
                "X-Report-Token": report_token,
                "Access-Control-Expose-Headers": expose,
            },
        )
    else:
        fname, data = generated_files[0]
        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{fname}"',
                "X-Report-Token": report_token,
                "Access-Control-Expose-Headers": expose,
            },
        )


# ---------------------------------------------------------------------------
# Sheet preview endpoints — serve cached report data as JSON for UI viewer
# ---------------------------------------------------------------------------
@router.get("/sheets")
async def framework_list_sheets(token: str):
    """Return {filename: [sheet_names]} for a cached report."""
    if token not in _fw_report_cache:
        raise HTTPException(status_code=404, detail="Report token not found or expired.")
    import pandas as pd
    result = {}
    for fname, data in _fw_report_cache[token].items():
        if not fname.endswith(".xlsx"):
            continue
        try:
            result[fname] = pd.ExcelFile(io.BytesIO(data)).sheet_names
        except Exception:
            result[fname] = []
    return result


@router.get("/sheet_data")
async def framework_sheet_data(token: str, sheet: str, max_rows: int = 2000):
    """Return column headers + row data for a specific sheet as JSON."""
    if token not in _fw_report_cache:
        raise HTTPException(status_code=404, detail="Report token not found or expired.")
    import pandas as pd
    for fname, data in _fw_report_cache[token].items():
        if not fname.endswith(".xlsx"):
            continue
        try:
            xl = pd.ExcelFile(io.BytesIO(data))
            if sheet not in xl.sheet_names:
                continue
            df = pd.read_excel(io.BytesIO(data), sheet_name=sheet, nrows=max_rows)
            columns = [
                ' / '.join(str(x) for x in c) if isinstance(c, tuple) else str(c)
                for c in df.columns
            ]
            rows = json.loads(df.to_json(orient='values', date_format='iso', default_handler=str))
            return {
                "sheet": sheet,
                "columns": columns,
                "rows": rows,
                "total_rows": len(df),
            }
        except Exception:
            continue
    raise HTTPException(status_code=404, detail=f"Sheet '{sheet}' not found in cached report.")


# ---------------------------------------------------------------------------
# Save to folder (path mode only)
# ---------------------------------------------------------------------------
class SaveFolderRequest(BaseModel):
    folder_path: str
    experiments: list
    merge: bool = False
    merge_tag: str = "Summary"
    merge_output_name: str = "MergedSummary"
    generate: bool = False
    report_tag: str = ""
    check_logging: bool = False
    skip_strings: str = ""
    dragon_data: bool = False
    core_data: bool = False
    summary_tab: bool = False
    overview: bool = False
    output_name: str = "FrameworkReport"
    save_folder: str = ""


@router.post("/save_to_folder")
async def framework_save_to_folder(req: SaveFolderRequest):
    """Generate report file(s) and save directly to a folder on disk."""
    if not req.save_folder:
        raise HTTPException(status_code=400, detail="save_folder is required.")
    if not os.path.isdir(req.folder_path):
        raise HTTPException(status_code=400, detail=f"Data folder not found: {req.folder_path}")
    if not req.merge and not req.generate:
        raise HTTPException(status_code=400, detail="No action selected (enable Generate Report and/or Merge Summary).")

    os.makedirs(req.save_folder, exist_ok=True)
    skip = [s.strip() for s in req.skip_strings.split(",") if s.strip()]

    try:
        fp = _fpa()
        all_files = fp.find_files(base_folder=req.folder_path)
        log_dict = _build_log_dict(all_files, req.experiments)

        if log_dict:
            test_df = fp.parse_log_files(log_dict)
        else:
            import pandas as pd
            test_df = pd.DataFrame()

        saved_files = []

        if req.generate and not test_df.empty:
            report_path = os.path.join(req.save_folder, f"{req.output_name}.xlsx")
            _write_framework_excel(
                fp, test_df, report_path, req.folder_path,
                log_dict=log_dict, skip=skip,
                dragon_data=req.dragon_data, core_data=req.core_data,
                summary_tab=req.summary_tab, overview=req.overview,
            )
            saved_files.append(f"{req.output_name}.xlsx")

        if req.merge:
            selected_exps = list(log_dict.keys())
            import pandas as pd
            find_df = all_files
            filtered_df = find_df[find_df["Experiment"].isin(selected_exps)] if hasattr(find_df, '__len__') and len(find_df) else find_df
            try:
                type_values    = {k: v.get("test_type", "Baseline") for k, v in log_dict.items()}
                content_values = {k: v.get("content",   "Dragon")   for k, v in log_dict.items()}
                excel_path_dict = fp.create_file_dict(filtered_df, "Excel", type_values, content_values)
            except Exception:
                excel_path_dict = log_dict
            merge_path = os.path.join(req.save_folder, f"{req.merge_output_name}.xlsx")
            fp.framework_merge(file_dict=excel_path_dict, output_file=merge_path, prefix=req.merge_tag, skip=skip)
            saved_files.append(f"{req.merge_output_name}.xlsx")

        if not saved_files:
            raise HTTPException(status_code=400, detail="No files generated — check log files and folder structure.")

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())

    return JSONResponse({"success": True, "saved_files": saved_files, "folder": req.save_folder})


# ---------------------------------------------------------------------------
# Rebuild MCA tabs on a cached merged/summary file
# ---------------------------------------------------------------------------
@router.post("/rebuild_mca")
async def framework_rebuild_mca(
    token:    str  = Form(..., description="Cache token from a previous generate response"),
    filename: str  = Form(..., description="Filename inside the cached report (e.g. VID_MergedSummary.xlsx)"),
    product:  str  = Form("GNR"),
    decode:   bool = Form(True,  description="Run decoder to produce _MCAS tabs"),
    analysis: bool = Form(True,  description="Run MCAAnalyzer to append Analysis sheet"),
):
    """
    Add decoded MCA tabs (CHA_MCAS, LLC_MCAS, CORE_MCAS, MEM_MCAS, IO_MCAS,
    UBOX) and an MCA_Analysis sheet to a previously generated/cached merged file.

    The file must already have CHA and CORE tabs (produced by Merge Summary).
    Returns the updated file as a streaming download and also caches it
    under a new token (returned in the X-Report-Token header).
    """
    cached = _fw_report_cache.get(token, {})
    file_bytes = cached.get(filename)
    if not file_bytes:
        raise HTTPException(
            status_code=404,
            detail=f"Cached file '{filename}' not found for token '{token}'. "
                   "Generate / merge a report first.",
        )

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        data_path = os.path.join(tmpdir, filename)
        with open(data_path, "wb") as fh:
            fh.write(file_bytes)

        try:
            here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            sys.path.insert(0, here)
            from THRTools.parsers.PPVMCAReportAPI import rebuild_mca_tabs  # type: ignore
            rebuild_mca_tabs(data_path, product=product, decode=decode, analysis=analysis)
        except Exception:
            raise HTTPException(status_code=500, detail=traceback.format_exc())

        with open(data_path, "rb") as fh:
            updated_bytes = fh.read()

    new_token = str(uuid.uuid4())
    _fw_report_cache[new_token] = {filename: updated_bytes}

    return StreamingResponse(
        io.BytesIO(updated_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Report-Token": new_token,
        },
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _build_log_dict(all_files, experiments: list) -> dict:
    """Build log_dict from find_files() output and user-selected experiment configs."""
    # find_files() returns a pandas DataFrame — convert to records
    if hasattr(all_files, "to_dict"):
        all_files = all_files.to_dict("records")

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
    """Write framework report Excel using the correct PPV pipeline."""
    import pandas as pd

    # --- 1. Build file dicts from find_files DataFrame (needed for zip/excel/logger parsing) ---
    find_df = fp.find_files(base_folder=base_folder)

    # Build name→config lookup from log_dict so create_file_dict can carry type/content/comments
    type_values    = {k: v.get("test_type", "Baseline") for k, v in log_dict.items()}
    content_values = {k: v.get("content",   "Dragon")   for k, v in log_dict.items()}
    comments_values= {k: v.get("comments",  "")         for k, v in log_dict.items()}

    selected_exps   = list(log_dict.keys())
    filtered_df     = find_df[find_df["Experiment"].isin(selected_exps)] if not find_df.empty else find_df

    try:
        zip_path_dict  = fp.create_file_dict(filtered_df, "ZIP",   type_values, content_values)
        excel_path_dict= fp.create_file_dict(filtered_df, "Excel", type_values, content_values)
        log_path_dict  = fp.create_file_dict(filtered_df, "Log",   type_values, content_values, comments_values)
    except Exception:
        zip_path_dict   = {}
        excel_path_dict = {}
        log_path_dict   = log_dict   # fall back to what _build_log_dict gave us

    # Re-parse log files using the proper log_path_dict (original log_dict is equivalent)
    if not log_path_dict:
        log_path_dict = log_dict

    # --- 2. parse_log_files already done upstream (test_df passed in), but if empty try again ---
    if test_df is None or test_df.empty:
        try:
            test_df = fp.parse_log_files(log_path_dict)
        except Exception:
            test_df = pd.DataFrame()

    if test_df.empty:
        raise ValueError("No test data found — check log files and folder structure.")

    # --- 3. Optional: check ZIP data (fail/pass strings) ---
    fail_info_df      = None
    unique_fails_df   = None
    unique_mcas_df    = None
    mca_df            = None
    vvar_df           = None
    core_data_df      = None
    experiment_summary_df = None
    dr_df             = None
    voltage_df        = None
    metadata_df       = None

    if zip_path_dict:
        try:
            fail_info_df  = fp.check_zip_data(zip_path_dict, skip, test_df)
            test_df       = fp.update_content_results(test_df, fail_info_df)
            unique_fails_df = fp.generate_unique_fails(fail_info_df)
        except Exception:
            pass

    # --- 4. MCA parsing via LogSummaryParser ---
    if excel_path_dict:
        try:
            lsp = fp.LogSummaryParser(excel_path_dict, test_df)
            unique_mcas_df, mca_df = lsp.parse_mca_tabs_from_files()
            if mca_df is not None and not mca_df.empty and fail_info_df is not None:
                test_df = fp.update_mca_results(test_df, fail_info_df, mca_df)
        except Exception:
            pass

    # --- 5. DebugFrameworkLogger parsing (DragonData / CoreData) ---
    if (dragon_data or core_data) and log_path_dict:
        try:
            logger_parser = fp.DebugFrameworkLoggerParser(log_path_dict)
            dr_df       = logger_parser.parse_dr_data()
            voltage_df  = logger_parser.parse_core_voltage_data()
            metadata_df = logger_parser.parse_experiment_metadata()
        except Exception:
            pass

    # --- 6. Summary DataFrame ---
    try:
        summary_df, test_df, experiment_index_map = fp.create_summary_df(test_df)
    except Exception:
        summary_df = pd.DataFrame()
        experiment_index_map = {}

    # --- 7. VVAR data (DragonData sheet) ---
    if dragon_data and zip_path_dict and dr_df is not None and metadata_df is not None:
        try:
            vvar_df = fp.parse_vvars_from_zip(
                zip_path_dict, test_df, vvar_filter=["0x600D600D"],
                skip_array=skip, dr_df=dr_df, metadata_df=metadata_df,
                experiment_index_map=experiment_index_map,
            )
        except Exception:
            vvar_df = None

    # --- 8. Core data report ---
    if core_data and voltage_df is not None:
        try:
            core_data_df = fp.create_core_data_report(
                voltage_df, dr_df, vvar_df, mca_df, test_df, metadata_df
            )
        except Exception:
            core_data_df = None

    # --- 9. Experiment summary tab ---
    if summary_tab:
        try:
            analyzer = fp.ExperimentSummaryAnalyzer(
                test_df, summary_df, fail_info_df, vvar_df, mca_df, core_data_df
            )
            experiment_summary_df = analyzer.analyze_all_experiments()
        except Exception:
            experiment_summary_df = None

    # --- 10. Overview ---
    overview_df = None
    if overview and experiment_summary_df is not None:
        try:
            from THRTools.utils.OverviewAnalyzer import OverviewAnalyzer  # type: ignore
            ov = OverviewAnalyzer(test_df, summary_df, experiment_summary_df, fail_info_df)
            overview_df = ov.create_overview()
        except Exception:
            overview_df = None

    # --- 11. Save to Excel ---
    fp.save_to_excel(
        filtered_df, test_df, summary_df,
        fail_info_df, unique_fails_df, unique_mcas_df,
        vvar_df, core_data_df, experiment_summary_df, overview_df,
        filename=out_path,
    )
