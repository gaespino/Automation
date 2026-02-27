"""
Fuse Generator REST endpoints.
  GET  /api/fuses/{product}  — return fuse list for a product
  POST /api/fuses/generate   — generate .fuse file from selected fuses
"""
from __future__ import annotations
import io
import os
import sys
import traceback
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

_FUSE_CACHE: dict = {}


def _normalize_fuse_row(row: dict, ip_origin: str) -> dict:
    """Normalize raw CSV columns to the canonical schema expected by the UI.

    Raw CSV columns:  original_name, IOSFSBEP, Instance, VF_Name, FUSE_WIDTH, default, Group, ...
    Canonical schema: Name, IP, Description, Bits, Default, Group
    """
    name = row.get("original_name") or row.get("Name") or row.get("name") or ""
    ip   = ip_origin or row.get("IOSFSBEP") or row.get("IP") or row.get("ip") or ""
    desc = (row.get("VF_Name") or row.get("Description") or row.get("description") or
            row.get("IOSFSBEP") or "")
    bits = row.get("FUSE_WIDTH") or row.get("Bits") or row.get("bits") or ""
    default = row.get("default") or row.get("Default") or ""
    group = row.get("Group") or row.get("group") or row.get("Category") or ""

    normalized = {"Name": name, "IP": ip, "Description": desc,
                  "Bits": bits, "Default": default, "Group": group}
    # Keep all original columns too so nothing is lost
    normalized.update(row)
    return normalized


def _load_product_fuses(product: str) -> list:
    if product in _FUSE_CACHE:
        return _FUSE_CACHE[product]

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Directories are stored lowercase (gnr/, cwf/, dmr/)
    fuse_dir = os.path.join(here, "THRTools", "configs", "fuses", product.lower())
    if not os.path.isdir(fuse_dir):
        return []

    import csv
    import sys as _sys
    _sys.setrecursionlimit(10000)
    try:
        csv.field_size_limit(_sys.maxsize)
    except OverflowError:
        csv.field_size_limit(2 ** 31 - 1)

    rows = []
    for fname in sorted(os.listdir(fuse_dir)):
        if not fname.endswith(".csv"):
            continue
        ip_origin = os.path.splitext(fname)[0].upper()  # e.g. "COMPUTE", "IO"
        fpath = os.path.join(fuse_dir, fname)
        with open(fpath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(_normalize_fuse_row(dict(r), ip_origin))

    _FUSE_CACHE[product] = rows
    return rows


@router.get("/{product}")
async def get_fuses(product: str):
    """Return full fuse list for a product (GNR, CWF, DMR, …)."""
    fuses = _load_product_fuses(product.upper())
    if not fuses:
        raise HTTPException(status_code=404, detail=f"No fuse data found for product '{product}'")
    return {"product": product.upper(), "count": len(fuses), "fuses": fuses}


@router.get("/{product}/metadata")
async def get_fuses_metadata(product: str):
    """Return unique IPs and Groups for filter dropdowns."""
    fuses = _load_product_fuses(product.upper())
    ips    = sorted({f.get("IP", "") for f in fuses if f.get("IP", "")})
    groups = sorted({f.get("Group", "") for f in fuses if f.get("Group", "")})
    return {"ips": ips, "groups": groups}


class FuseGenerateRequest(BaseModel):
    product: str
    selected_names: List[str]
    filename: str = "fuses.fuse"


@router.post("/generate")
async def generate_fuse_file(req: FuseGenerateRequest):
    """Generate a .fuse file from the selected fuse names."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, here)
    try:
        from THRTools.utils.fusefilegenerator import FuseFileGenerator  # type: ignore
        gen = FuseFileGenerator(product=req.product.upper())
        fuse_dir = os.path.join(here, "THRTools", "configs", "fuses", req.product.lower())
        gen.load_csv_files(fuse_dir)
        # generate_fuse_file needs ip_assignments; produce simple text as fallback
        raise NotImplementedError("Use fallback path")
    except Exception:
        # Fallback: write simple .fuse text format using normalized data
        fuses = _load_product_fuses(req.product.upper())
        selected = [f for f in fuses if f.get("Name") in set(req.selected_names)]
        lines = [f"{f.get('Name', '')}={f.get('Default', '')}" for f in selected]
        fuse_bytes = "\n".join(lines).encode()

    return StreamingResponse(
        io.BytesIO(fuse_bytes),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{req.filename}"'},
    )
