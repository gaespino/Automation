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
# Helpers
# ---------------------------------------------------------------------------

# web snake_case → PPV display-name field keys
_UC_MAP: Dict[str, str] = {
    "visual_id":  "Visual ID",
    "bucket":     "Bucket",
    "com_port":   "COM Port",
    "ip":         "IP Address",
    "flag_600w":  "600W Unit",
    "check_core": "Check Core",
}


def _translate_unit_config(uc: Dict[str, Any]) -> Dict[str, Any]:
    """Translate web unit_config keys to PPV display names, skipping empty/falsy values."""
    out: Dict[str, Any] = {}
    for web_key, ppv_key in _UC_MAP.items():
        val = uc.get(web_key)
        if val is None or val == "" or val is False:
            continue
        out[ppv_key] = val
    return out


def _build_ppv_files(flow: "FlowModel") -> Dict[str, str]:
    """Build the 4 PPV config file contents from a FlowModel."""
    from datetime import datetime
    nodes = flow.nodes
    uc_overrides = _translate_unit_config(flow.unit_config)

    # Apply unit config overrides to every experiment in the flow
    experiments_out: Dict[str, Any] = {}
    for exp_name, exp_data in flow.experiments.items():
        merged = dict(exp_data)
        merged.update(uc_overrides)
        experiments_out[exp_name] = merged

    # FrameworkAutomationStructure.json — matches PPV import_flow_config() expectations
    structure: Dict[str, Any] = {}
    for nid, n in nodes.items():
        output_map = {str(port): target for port, target in n.connections.items()}
        structure[nid] = {
            "name":          n.name,
            "instanceType":  n.type,
            "flow":          n.experiment if n.experiment else "default",
            "outputNodeMap": output_map,
        }

    # FrameworkAutomationFlows.json — experiment name → full experiment data dict
    # (not a connection map; PPV reads this as the experiment library)

    # FrameworkAutomationInit.ini — [DEFAULT] header + one section per experiment
    ini_lines: List[str] = [
        "[DEFAULT]",
        "# Automation Flow Configuration",
        f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    for exp_name in experiments_out:
        ini_lines.append(f"[{exp_name}]")
        ini_lines.append("# Add experiment-specific configuration here")
        ini_lines.append("")
    ini_content = "\n".join(ini_lines)

    # FrameworkAutomationPositions.json — raw coords, no offset (PPV applies display offset itself)
    positions = {nid: {"x": int(n.x), "y": int(n.y)} for nid, n in nodes.items()}

    return {
        "FrameworkAutomationStructure.json": json.dumps(structure, indent=2),
        "FrameworkAutomationFlows.json":     json.dumps(experiments_out, indent=2),
        "FrameworkAutomationInit.ini":       ini_content,
        "FrameworkAutomationPositions.json": json.dumps(positions, indent=2),
    }


class SaveToFolderRequest(BaseModel):
    folder_path: str
    filename: str = "flow_design"
    flow: "FlowModel"


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
    ppv_files = _build_ppv_files(flow)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, content in ppv_files.items():
            zf.writestr(fname, content)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="FlowConfig.zip"'},
    )


# ---------------------------------------------------------------------------
# /api/flow/save_to_folder
# ---------------------------------------------------------------------------
@router.post("/save_to_folder")
async def save_flow_to_folder(req: SaveToFolderRequest):
    """Save flow project JSON + 4 PPV config files to a server-side folder path."""
    folder = req.folder_path
    if not os.path.isdir(folder):
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Cannot create folder: {exc}")

    from datetime import datetime
    saved: List[str] = []
    try:
        # Write 4 PPV config files
        for fname, content in _build_ppv_files(req.flow).items():
            path = os.path.join(folder, fname)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            saved.append(path)

        # Write project JSON (web format — can be reloaded in the browser UI)
        nodes_dict = {
            nid: {
                "id": n.id, "name": n.name, "type": n.type,
                "x": n.x, "y": n.y, "experiment": n.experiment,
                "connections": n.connections,
            }
            for nid, n in req.flow.nodes.items()
        }
        project = {
            "nodes":       nodes_dict,
            "unit_config": req.flow.unit_config,
            "experiments": req.flow.experiments,
            "_format":     "web",
            "metadata": {
                "saved":        datetime.now().isoformat(),
                "version":      "2.0",
                "node_counter": len(req.flow.nodes),
            },
        }
        proj_path = os.path.join(folder, f"{req.filename}.json")
        with open(proj_path, "w", encoding="utf-8") as fh:
            json.dump(project, fh, indent=2)
        saved.append(proj_path)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())

    return {"success": True, "saved_files": saved, "folder": folder}


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
