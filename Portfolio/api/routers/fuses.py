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


def _load_product_fuses(product: str) -> list:
    if product in _FUSE_CACHE:
        return _FUSE_CACHE[product]

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fuse_dir = os.path.join(here, "THRTools", "configs", "fuses", product)
    if not os.path.isdir(fuse_dir):
        return []

    import csv
    rows = []
    for fname in sorted(os.listdir(fuse_dir)):
        if not fname.endswith(".csv"):
            continue
        fpath = os.path.join(fuse_dir, fname)
        with open(fpath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(dict(r))

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
    ips = sorted({f.get("IP", f.get("ip", "")) for f in fuses if f.get("IP", f.get("ip", ""))})
    groups = sorted({f.get("Group", f.get("group", "")) for f in fuses if f.get("Group", f.get("group", ""))})
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
        fuse_bytes = gen.generate(selected_names=req.selected_names)
    except Exception:
        # Fallback: write simple text format
        fuses = _load_product_fuses(req.product.upper())
        selected = {f["Name"]: f for f in fuses if f.get("Name") in req.selected_names}
        lines = [f"{name}={info.get('Default','')}" for name, info in selected.items()]
        fuse_bytes = "\n".join(lines).encode()

    return StreamingResponse(
        io.BytesIO(fuse_bytes),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{req.filename}"'},
    )
