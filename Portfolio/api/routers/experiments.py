"""
Experiment Builder REST endpoints.
  GET  /api/experiments/config/{product}  — ControlPanelConfig.json
  GET  /api/experiments/products          — available products
  POST /api/experiments/build             — build/export experiment list as .tpl
"""
from __future__ import annotations
import io
import json
import os
import sys
import traceback
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter()

_CONFIGS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "THRTools", "configs"
)


@router.get("/products")
async def get_products():
    """Return list of products that have a ControlPanelConfig.json."""
    products = []
    for fname in sorted(os.listdir(_CONFIGS_DIR)):
        if fname.endswith("ControlPanelConfig.json"):
            products.append(fname.replace("ControlPanelConfig.json", ""))
    return {"products": products}


@router.get("/config/{product}")
async def get_config(product: str):
    """Return the ControlPanelConfig.json for a product (drives the dynamic form)."""
    fname = os.path.join(_CONFIGS_DIR, f"{product.upper()}ControlPanelConfig.json")
    if not os.path.isfile(fname):
        # Fall back to generic
        fname = os.path.join(_CONFIGS_DIR, "ControlPanelConfig.json")
    if not os.path.isfile(fname):
        raise HTTPException(status_code=404, detail=f"Config not found for product '{product}'")
    with open(fname, encoding="utf-8") as f:
        config = json.load(f)
    return {"product": product.upper(), "config": config}


class ExperimentBuildRequest(BaseModel):
    experiments: List[dict] = Field(..., description="List of experiment parameter dicts")
    filename: str = "experiments.tpl"


@router.post("/build")
async def build_experiments(req: ExperimentBuildRequest):
    """Export experiment list as a .tpl (JSON) file."""
    content = json.dumps(req.experiments, indent=2).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{req.filename}"'},
    )
