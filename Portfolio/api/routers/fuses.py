"""
Fuse Generator REST endpoints.
  GET  /api/fuses/{product}  — return fuse list for a product
  POST /api/fuses/generate   — generate .fuse file from selected fuses
"""
from __future__ import annotations
import csv
import io
import os
import re
import sys
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
        {"label": "All Computes",  "value": "computes"},
        {"label": "Compute 0",     "value": "compute0"},
        {"label": "Compute 1",     "value": "compute1"},
        {"label": "Compute 2",     "value": "compute2"},
        {"label": "All IOs",       "value": "ios"},
        {"label": "IO 0",          "value": "io0"},
        {"label": "IO 1",          "value": "io1"},
    ],
    "CWF": [
        {"label": "All Computes",  "value": "computes"},
        {"label": "Compute 0",     "value": "compute0"},
        {"label": "Compute 1",     "value": "compute1"},
        {"label": "Compute 2",     "value": "compute2"},
        {"label": "All IOs",       "value": "ios"},
        {"label": "IO 0",          "value": "io0"},
        {"label": "IO 1",          "value": "io1"},
    ],
    "DMR": [
        {"label": "All CBBs",      "value": "cbbs"},
        {"label": "CBB 0",         "value": "cbb0"},
        {"label": "CBB 1",         "value": "cbb1"},
        {"label": "CBB 2",         "value": "cbb2"},
        {"label": "CBB 3",         "value": "cbb3"},
        {"label": "All Computes",  "value": "computes"},
        {"label": "Compute 0",     "value": "compute0"},
        {"label": "Compute 1",     "value": "compute1"},
        {"label": "Compute 2",     "value": "compute2"},
        {"label": "Compute 3",     "value": "compute3"},
        {"label": "All IMHs",      "value": "imhs"},
        {"label": "IMH 0",         "value": "imh0"},
        {"label": "IMH 1",         "value": "imh1"},
    ],
}

_FUSE_CACHE: dict = {}


def _normalize_fuse_row(row: dict, ip_origin: str) -> dict:
    """Normalize raw CSV columns to the canonical schema expected by the UI.

    Raw CSV columns:  original_name, ip_name, Instance, description, numbits/FUSE_WIDTH, default, Group, ...
    Canonical schema: Name (unique key), IP_Origin, ip_name, Instance, description, Bits, Default, Group
    """
    name     = row.get("original_name") or row.get("Name") or row.get("name") or ""
    ip_nm    = row.get("ip_name") or row.get("IPName") or ""
    instance = row.get("Instance") or row.get("instance") or ""
    desc     = row.get("description") or row.get("Description") or row.get("VF_Name") or ""
    bits     = row.get("numbits") or row.get("FUSE_WIDTH") or row.get("Bits") or ""
    default  = row.get("default") or row.get("Default") or ""
    group    = row.get("Group") or row.get("group") or row.get("Category") or ""

    return {
        "Name": name,
        "IP_Origin": ip_origin,
        "ip_name": ip_nm,
        "Instance": instance,
        "description": desc,
        "Bits": bits,
        "Default": default,
        "Group": group,
    }


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
    """Return unique IP_Origins and Groups for filter dropdowns."""
    fuses = _load_product_fuses(product.upper())
    ips    = sorted({f.get("IP_Origin", "") for f in fuses if f.get("IP_Origin", "")})
    groups = sorted({f.get("Group", "") for f in fuses if f.get("Group", "")})
    return {"ips": ips, "groups": groups}


class FuseGenerateRequest(BaseModel):
    product: str
    selected_names: List[str]
    fuse_values: Optional[Dict[str, str]] = None   # {Name: value}; defaults used when absent
    ip_targets: Optional[List[str]] = None          # ip_instance strings, e.g. ["computes","ios"]
    sockets: Optional[List[str]] = None             # socket strings, e.g. ["sockets","socket0"]
    filename: str = "fuses.fuse"


def _build_section_header(socket: str, ip_target: str, product: str) -> str:
    """Build sv.*.fuses section header matching original PPV conventions."""
    product = product.upper()
    if product == "DMR":
        if ip_target in ("cbbs", "all_cbbs"):
            return f"sv.{socket}.cbbs.base.fuses"
        if re.match(r"^cbb\d+$", ip_target):
            return f"sv.{socket}.{ip_target}.base.fuses"
        if ip_target in ("imhs", "all_imhs"):
            return f"sv.{socket}.imhs.fuses"
    # GNR/CWF and remaining DMR targets (compute*, imh*)
    return f"sv.{socket}.{ip_target}.fuses"


@router.post("/generate")
async def generate_fuse_file(req: FuseGenerateRequest):
    """Generate a .fuse file from selected fuses.

    The file is structured as [sv.{socket}.{ip}.fuses] sections (socket × ip_target),
    with fuse keys as ip_name.instance matching the original PPV fusefilegen.py format.
    """
    fuses_all = _load_product_fuses(req.product.upper())
    selected_map = {f["Name"]: f for f in fuses_all if f.get("Name") in set(req.selected_names)}

    # Build fuse key → value mapping using ip_name.instance format (original PPV convention)
    fuse_kv: dict = {}
    for name, f in selected_map.items():
        ip_nm  = str(f.get("ip_name", "")).lower()
        inst   = str(f.get("Instance", "")).lower()
        fuse_key = f"{ip_nm}.{inst}" if ip_nm else inst
        val = (req.fuse_values or {}).get(name, f.get("Default", "0") or "0")
        fuse_kv[fuse_key] = val

    sockets    = req.sockets    or ["sockets"]
    ip_targets = req.ip_targets or []

    if ip_targets:
        buf: list = [
            f"# Fuse configuration for {req.product.upper()}",
            "# Generated by PPV Engineering Tools",
            f"# Fuses: {len(fuse_kv)}",
            "",
        ]
        for socket in sockets:
            for target in ip_targets:
                section = _build_section_header(socket, target, req.product)
                buf.append(f"[{section}]")
                for fname, val in fuse_kv.items():
                    buf.append(f"{fname} = {val}")
                buf.append("")
        fuse_bytes = "\n".join(buf).encode()
    else:
        lines = [f"{n} = {v}" for n, v in fuse_kv.items()]
        fuse_bytes = "\n".join(lines).encode()

    out_fname = req.filename if req.filename.endswith(".fuse") else f"{req.filename}.fuse"
    return StreamingResponse(
        io.BytesIO(fuse_bytes),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{out_fname}"'},
    )
