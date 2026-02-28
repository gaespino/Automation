"""
Fuse Generator REST endpoints.
  GET  /api/fuses/{product}  — return fuse list for a product
  POST /api/fuses/generate   — generate .fuse file from selected fuses
"""
from __future__ import annotations
import csv
import io
import os
import sys
import traceback
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

# Set CSV field size limit once at module level
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2 ** 31 - 1)

# Product-specific IP targets for .fuse file generation
_IP_TARGETS: dict = {
    "GNR": [
        {"label": "All Computes",    "value": "computes"},
        {"label": "Compute 0",       "value": "compute0"},
        {"label": "Compute 1",       "value": "compute1"},
        {"label": "All IOs",         "value": "ios"},
        {"label": "IO 0",            "value": "io0"},
        {"label": "IO 1",            "value": "io1"},
    ],
    "CWF": [
        {"label": "All Computes",    "value": "computes"},
        {"label": "Compute 0",       "value": "compute0"},
        {"label": "Compute 1",       "value": "compute1"},
        {"label": "All IOs",         "value": "ios"},
        {"label": "IO 0",            "value": "io0"},
        {"label": "IO 1",            "value": "io1"},
    ],
    "DMR": [
        {"label": "All CBBs (Base)",           "value": "cbbs_base"},
        {"label": "CBB 0 – Base",              "value": "cbb0"},
        {"label": "All CBBs (Top/Compute)",    "value": "cbbs_top"},
        {"label": "CBB 0 – Top (Compute 0)",   "value": "cbb0_compute0"},
        {"label": "All IMHs",                  "value": "imhs"},
        {"label": "IMH 0",                     "value": "imh0"},
    ],
}

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

    return {"Name": name, "IP": ip, "Description": desc,
            "Bits": bits, "Default": default, "Group": group}


def _load_product_fuses(product: str) -> list:
    if product in _FUSE_CACHE:
        return _FUSE_CACHE[product]

    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Directories are stored lowercase (gnr/, cwf/, dmr/)
    fuse_dir = os.path.join(here, "THRTools", "configs", "fuses", product.lower())
    if not os.path.isdir(fuse_dir):
        return []

    import csv
    import sys as _sys

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


@router.get("/{product}/ip-targets")
async def get_ip_targets(product: str):
    """Return available IP targets for .fuse file section generation."""
    targets = _IP_TARGETS.get(product.upper(), [])
    return {"product": product.upper(), "targets": targets}


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
    fuse_values: Optional[Dict[str, str]] = None   # {fuse_name: value}; defaults used when absent
    ip_targets: Optional[List[str]] = None          # ip_instance strings, e.g. ["computes","ios"]
    filename: str = "fuses.fuse"


@router.post("/generate")
async def generate_fuse_file(req: FuseGenerateRequest):
    """Generate a .fuse file from selected fuses.

    When ip_targets is provided the file is structured as
    [sv.sockets.computes.fuses] / [sv.socket0.compute0.fuses] sections (etc.)
    matching the fusefilegen.py input format.
    """
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, here)

    fuses = _load_product_fuses(req.product.upper())
    selected = [f for f in fuses if f.get("Name") in set(req.selected_names)]

    # Build the fuse_name → value mapping; req.fuse_values overrides defaults
    fuse_values: dict = req.fuse_values if req.fuse_values else {
        f["Name"]: f.get("Default", "0") for f in selected
    }

    if req.ip_targets:
        try:
            from THRTools.utils.fusefilegenerator import FuseFileGenerator  # type: ignore
            gen = FuseFileGenerator(product=req.product.upper())
            buf: list = [
                f"# Fuse configuration for {req.product.upper()}",
                "# Generated by PPV Engineering Tools",
                f"# Fuses: {len(fuse_values)}",
                "",
            ]
            for target in req.ip_targets:
                section = gen._get_section_header(target.lower())
                if section:
                    buf.append(f"[{section}]")
                    for fname, val in fuse_values.items():
                        buf.append(f"{fname} = {val}")
                    buf.append("")
            fuse_bytes = "\n".join(buf).encode()
        except Exception:
            # Fallback: simple key=value without sections
            lines = [f"{n} = {v}" for n, v in fuse_values.items()]
            fuse_bytes = "\n".join(lines).encode()
    else:
        lines = [f"{n}={v}" for n, v in fuse_values.items()]
        fuse_bytes = "\n".join(lines).encode()

    out_fname = req.filename if req.filename.endswith(".fuse") else f"{req.filename}.fuse"
    return StreamingResponse(
        io.BytesIO(fuse_bytes),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{out_fname}"'},
    )
