"""
Automation Flow Designer REST endpoints.
  POST /api/flow/validate  — validate a flow JSON
  POST /api/flow/export    — export flow as ZIP (4 PPV config files)
  POST /api/flow/layout    — compute auto-layout positions (BFS from StartNode)
"""
from __future__ import annotations
import io
import json
import os
import zipfile
import configparser
import traceback
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class NodeModel(BaseModel):
    id: str
    name: str
    type: str
    x: float = 0
    y: float = 0
    experiment: Optional[str] = None
    connections: Dict[str, str] = {}


class FlowModel(BaseModel):
    nodes: Dict[str, NodeModel]
    unit_config: Dict[str, Any] = {}
    experiments: Dict[str, Any] = {}
    _format: str = "web"


# Terminal node types (no outputs)
_TERMINAL = {"EndNode", "EndFlowInstance"}
_STARTERS = {"StartNode", "StartFlowInstance"}

# ---------------------------------------------------------------------------
# /api/flow/validate
# ---------------------------------------------------------------------------
@router.post("/validate")
async def validate_flow(flow: FlowModel):
    errors: List[str] = []
    warnings: List[str] = []

    start_nodes = [n for n in flow.nodes.values() if n.type in _STARTERS]
    end_nodes   = [n for n in flow.nodes.values() if n.type in _TERMINAL]

    if not start_nodes:
        errors.append("No StartNode found in flow.")
    if len(start_nodes) > 1:
        warnings.append(f"Multiple StartNodes detected: {[n.id for n in start_nodes]}")
    if not end_nodes:
        warnings.append("No EndNode found — flow may never terminate.")

    for node in flow.nodes.values():
        if node.type not in _STARTERS | _TERMINAL:
            if not node.experiment:
                warnings.append(f"{node.id} ({node.name}): no experiment assigned.")
        if not node.connections and node.type not in _TERMINAL:
            warnings.append(f"{node.id} ({node.name}): no output connections.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# /api/flow/export
# ---------------------------------------------------------------------------
@router.post("/export")
async def export_flow(flow: FlowModel):
    """Export flow as a ZIP containing 4 PPV-compatible config files."""
    nodes = flow.nodes
    uc = flow.unit_config

    # FrameworkAutomationStructure.json
    structure = {
        nid: {
            "NodeName": n.name,
            "NodeType": n.type,
            "Experiment": n.experiment or "",
        }
        for nid, n in nodes.items()
    }

    # FrameworkAutomationFlows.json  (connections, port = key)
    flows: Dict[str, Any] = {}
    for nid, n in nodes.items():
        flows[nid] = {f"Port{k}": v for k, v in n.connections.items()}

    # FrameworkAutomationInit.ini
    cfg = configparser.ConfigParser()
    cfg["UnitConfig"] = {
        "VisualID":   uc.get("visual_id", ""),
        "Bucket":     uc.get("bucket", ""),
        "COMPort":    uc.get("com_port", ""),
        "IPAddress":  uc.get("ip", ""),
        "600W":       str(uc.get("flag_600w", False)),
        "CheckCore":  str(uc.get("check_core", 5)),
    }
    ini_buf = io.StringIO()
    cfg.write(ini_buf)

    # FrameworkAutomationPositions.json (PPV top-left: subtract 75/50 offset)
    positions = {
        nid: {"x": int(n.x - 75), "y": int(n.y - 50)}
        for nid, n in nodes.items()
    }

    # Build ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("FrameworkAutomationStructure.json",  json.dumps(structure,  indent=2))
        zf.writestr("FrameworkAutomationFlows.json",      json.dumps(flows,      indent=2))
        zf.writestr("FrameworkAutomationInit.ini",        ini_buf.getvalue())
        zf.writestr("FrameworkAutomationPositions.json",  json.dumps(positions,  indent=2))
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="FlowConfig.zip"'},
    )


# ---------------------------------------------------------------------------
# /api/flow/layout
# ---------------------------------------------------------------------------
@router.post("/layout")
async def auto_layout(flow: FlowModel):
    """Compute hierarchical BFS layout positions from StartNode."""
    nodes = flow.nodes
    if not nodes:
        return {"positions": {}}

    # Build adjacency
    children: Dict[str, List[str]] = {nid: [] for nid in nodes}
    for nid, n in nodes.items():
        for target in n.connections.values():
            if target in children:
                children[nid].append(target)

    start = next((n.id for n in nodes.values() if n.type in _STARTERS), list(nodes.keys())[0])

    from collections import deque
    visited: Dict[str, int] = {}  # node_id → column
    col_rows: Dict[int, int] = {}  # column → row count
    queue = deque([(start, 0)])
    while queue:
        nid, depth = queue.popleft()
        if nid in visited:
            continue
        visited[nid] = depth
        row = col_rows.get(depth, 0)
        col_rows[depth] = row + 1
        for ch in children.get(nid, []):
            if ch not in visited:
                queue.append((ch, depth + 1))

    # Place orphans
    max_depth = max(visited.values(), default=0) + 1
    orphan_row = 0
    for nid in nodes:
        if nid not in visited:
            visited[nid] = max_depth
            orphan_row += 1

    row_idx: Dict[int, int] = {}
    positions: Dict[str, Dict[str, float]] = {}
    HGAP, VGAP = 230, 180
    for nid, depth in sorted(visited.items(), key=lambda x: x[1]):
        r = row_idx.get(depth, 0)
        row_idx[depth] = r + 1
        positions[nid] = {
            "x": round((160 + depth * HGAP) / 20) * 20,
            "y": round((160 + r * VGAP) / 20) * 20,
        }

    return {"positions": positions}
