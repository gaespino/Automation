"""
Automation Designer
====================
Visual interface to build DebugFramework automation flows using a drag-and-drop
node canvas. Faithfully replicates PPV/gui/AutomationDesigner.AutomationFlowDesigner.

Features:
  - Interactive node canvas (dash-cytoscape): add, move, connect, delete nodes
  - All 9 node types (StartNode, EndNode, SingleFail/AllFail/MajorityFail/Adaptive,
    Characterization/DataCollection/Analysis)
  - Load experiments from JSON/.tpl/Excel; assign to nodes
  - Unit Configuration overrides (Visual ID, Bucket, COM Port, IP, 600W, Check Core)
  - Export Flow Config as ZIP (FrameworkAutomation*.json + *.ini, matching original)
  - Save / Load flow design JSON (compatible with original save_flow() format)
  - Scalable: add new node types via _NODE_TYPES list; new exp fields via ControlPanelConfig

CaaS note: full drag-and-drop canvas requires dash-cytoscape (bundled in requirements.txt).
  For native drag-and-drop position persistence, save/load flow design preserves coordinates.
"""
import base64
import json
import io
import logging
import os
import sys
import zipfile
import datetime
import tempfile
import re

import dash
from dash import html, dcc, Input, Output, State, callback, no_update, ctx
import dash_bootstrap_components as dbc
try:
    import dash_cytoscape as cyto
    _CYTO_AVAILABLE = True
except ImportError:
    cyto = None  # type: ignore[assignment]
    _CYTO_AVAILABLE = False

logger = logging.getLogger(__name__)

dash.register_page(
    __name__,
    path='/thr-tools/automation-designer',
    name='Automation Designer',
    title='Automation Designer'
)

ACCENT = "#1abc9c"
_PRODUCTS = ["GNR", "CWF", "DMR"]

# Node type definitions — add new types here to make them available in the designer
_NODE_TYPES = [
    {"type": "StartNode",                  "label": "Start",            "color": "#1abc9c", "text": "white"},
    {"type": "EndNode",                    "label": "End",              "color": "#e74c3c", "text": "white"},
    {"type": "SingleFailFlowInstance",     "label": "SingleFail",       "color": "#3498db", "text": "white"},
    {"type": "AllFailFlowInstance",        "label": "AllFail",          "color": "#2980b9", "text": "white"},
    {"type": "MajorityFailFlowInstance",   "label": "MajorityFail",     "color": "#8e44ad", "text": "white"},
    {"type": "AdaptiveFlowInstance",       "label": "Adaptive",         "color": "#f39c12", "text": "white"},
    {"type": "CharacterizationFlowInstance","label": "Characterization","color": "#16a085", "text": "white"},
    {"type": "DataCollectionFlowInstance", "label": "DataCollection",   "color": "#27ae60", "text": "white"},
    {"type": "AnalysisFlowInstance",       "label": "Analysis",         "color": "#c0392b", "text": "white"},
]
_TYPE_MAP = {n["type"]: n for n in _NODE_TYPES}
_NODE_TYPE_OPTIONS = [{"label": n["label"], "value": n["type"]} for n in _NODE_TYPES]

_INPUT_STYLE = {
    "backgroundColor": "#1a1d26", "color": "#e0e0e0",
    "border": "1px solid rgba(255,255,255,0.1)", "fontSize": "0.85rem"
}
_LABEL_STYLE = {"color": "#a0a0a0", "fontSize": "0.8rem"}

# Cytoscape stylesheet
_CY_STYLESHEET = [
    {
        "selector": "node",
        "style": {
            "label": "data(label)",
            "background-color": "data(color)",
            "color": "data(textColor)",
            "text-valign": "center",
            "text-halign": "center",
            "font-size": "11px",
            "font-family": "Inter, Segoe UI, sans-serif",
            "font-weight": "600",
            "width": 140,
            "height": 70,
            "shape": "roundrectangle",
            "border-width": 2,
            "border-color": "data(borderColor)",
            "text-wrap": "wrap",
            "text-max-width": 120,
        }
    },
    {
        "selector": "node:selected",
        "style": {
            "border-color": "#f1c40f",
            "border-width": 3,
            "overlay-color": "#f1c40f",
            "overlay-padding": 3,
            "overlay-opacity": 0.15,
        }
    },
    {
        "selector": "edge",
        "style": {
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
            "arrow-scale": 1.5,
            "line-color": "#aaa",
            "target-arrow-color": "#aaa",
            "label": "data(label)",
            "font-size": "9px",
            "color": "#ccc",
            "text-background-color": "#1a1d26",
            "text-background-opacity": 0.85,
            "text-background-padding": "2px",
        }
    },
    {
        "selector": "edge:selected",
        "style": {
            "line-color": "#f1c40f",
            "target-arrow-color": "#f1c40f",
        }
    },
]


def _make_node_element(node_id, node_type, label, exp_name, x, y):
    info = _TYPE_MAP.get(node_type, {"color": "#555", "text": "white"})
    display = label or f"{info.get('label', node_type)}"
    if exp_name:
        display += f"\n[{exp_name[:12]}]"
    return {
        "data": {
            "id": node_id,
            "label": display,
            "type": node_type,
            "experiment": exp_name or "",
            "color": info["color"],
            "textColor": info["text"],
            "borderColor": info["color"],
        },
        "position": {"x": x, "y": y},
        "grabbable": True,
    }


def _cyto_fallback_layout():
    return dbc.Container(fluid=True, className="pb-5", children=[
        dbc.Alert([
            html.Strong("dash-cytoscape is not installed. "),
            "Run: ", html.Code("pip install dash-cytoscape"),
            " then restart the server.",
        ], color="warning", className="mt-4"),
    ])


def layout():
    if not _CYTO_AVAILABLE:
        return _cyto_fallback_layout()
    return dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="ad-toast"),
    dcc.Download(id="ad-download"),
    dcc.Store(id="ad-nodes-store",       data={}),   # node_id -> node_data
    dcc.Store(id="ad-edges-store",       data=[]),   # list of {source, target, port, label}
    dcc.Store(id="ad-experiments-store", data={}),   # exp_name -> exp_config
    dcc.Store(id="ad-counter-store",     data=1),    # node counter
    dcc.Store(id="ad-result-store",      data=None), # last export bytes (b64)
    dcc.Store(id="ad-selected-node",     data=None), # currently selected node id

    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-diagram-3 me-2", style={"color": ACCENT}),
            html.Span("Automation Designer",
                      style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P(
            "Build DebugFramework automation flows visually. "
            "Drag nodes, draw connections, assign experiments, then export the flow config ZIP.",
            style={"color": "#a0a0a0", "fontSize": "0.9rem"}
        ),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        # ── Left panel: controls ─────────────────────────────────────────────
        dbc.Col(md=3, children=[

            # Node toolbox
            dbc.Card(dbc.CardBody([
                html.H6("Add Node", className="mb-2", style={"color": ACCENT}),
                dbc.Select(
                    id="ad-node-type-sel",
                    options=_NODE_TYPE_OPTIONS,
                    value="SingleFailFlowInstance",
                    className="mb-2",
                    style=_INPUT_STYLE
                ),
                dbc.Button([html.I(className="bi bi-plus-circle me-1"), "Add Node"],
                           id="ad-add-node-btn", outline=True, className="w-100 mb-1",
                           style={"borderColor": ACCENT, "color": ACCENT}),
                dbc.Button([html.I(className="bi bi-arrow-left-right me-1"), "Auto Layout"],
                           id="ad-layout-btn", color="secondary", outline=True,
                           className="w-100 mb-1", size="sm"),
                dbc.Button([html.I(className="bi bi-trash me-1"), "Delete Selected"],
                           id="ad-del-node-btn", color="danger", outline=True,
                           className="w-100", size="sm"),
            ]), className="card-premium border-0 mb-3"),

            # Load experiments
            dbc.Card(dbc.CardBody([
                html.H6("Load Experiments", className="mb-2", style={"color": ACCENT}),
                html.Label("Product", style=_LABEL_STYLE),
                dbc.Select(id="ad-product", options=[{"label": p, "value": p} for p in _PRODUCTS],
                           value="GNR", className="mb-2", style=_INPUT_STYLE),
                dcc.Upload(
                    id="ad-exp-upload",
                    children=html.Div([html.A("Browse", style={"color": ACCENT}),
                                       " .json / .tpl / .xlsx"]),
                    multiple=False,
                    style={"border": f"1px dashed {ACCENT}", "borderRadius": "6px",
                           "padding": "8px", "textAlign": "center",
                           "color": "#a0a0a0", "fontSize": "0.8rem",
                           "backgroundColor": "rgba(26,188,156,0.03)", "cursor": "pointer"}
                ),
                html.Div(id="ad-exp-label",
                         style={"color": "#a0a0a0", "fontSize": "0.75rem", "marginTop": "4px"}),
            ]), className="card-premium border-0 mb-3"),

            # Node editor (shown when node is selected)
            dbc.Card(dbc.CardBody([
                html.H6("Node Editor", className="mb-2", style={"color": ACCENT}),
                html.Div(id="ad-node-editor", children=[
                    html.P("Select a node on the canvas to edit it.",
                           style={"color": "#a0a0a0", "fontSize": "0.82rem"})
                ]),
            ]), className="card-premium border-0 mb-3"),

            # Unit configuration
            dbc.Card(dbc.CardBody([
                html.H6("Unit Configuration", className="mb-2", style={"color": ACCENT}),
                html.Label("Visual ID", style=_LABEL_STYLE),
                dbc.Input(id="ad-vid", type="text", placeholder="75EH348100130",
                          className="mb-1", style=_INPUT_STYLE),
                html.Label("Bucket", style=_LABEL_STYLE),
                dbc.Input(id="ad-bucket", type="text", placeholder="N/A",
                          className="mb-1", style=_INPUT_STYLE),
                html.Label("COM Port", style=_LABEL_STYLE),
                dbc.Input(id="ad-com", type="text", placeholder="COM3",
                          className="mb-1", style=_INPUT_STYLE),
                html.Label("IP Address", style=_LABEL_STYLE),
                dbc.Input(id="ad-ip", type="text", placeholder="192.168.1.100",
                          className="mb-1", style=_INPUT_STYLE),
                dbc.Checklist(
                    id="ad-unit-flags",
                    options=[{"label": "600W Unit", "value": "600w"},
                             {"label": "Check Core",  "value": "check_core"}],
                    value=[],
                    inputStyle={"marginRight": "6px"},
                    labelStyle={"color": "#e0e0e0", "fontSize": "0.85rem"},
                    className="mt-2"
                ),
            ]), className="card-premium border-0 mb-3"),

            # Connection builder
            dbc.Card(dbc.CardBody([
                html.H6("Add Connection", className="mb-2", style={"color": ACCENT}),
                dbc.Row([
                    dbc.Col([html.Label("From", style=_LABEL_STYLE),
                             dbc.Input(id="ad-conn-from", placeholder="NODE_001",
                                       type="text", style=_INPUT_STYLE)], width=6),
                    dbc.Col([html.Label("To",   style=_LABEL_STYLE),
                             dbc.Input(id="ad-conn-to", placeholder="NODE_002",
                                       type="text", style=_INPUT_STYLE)], width=6),
                ], className="mb-1 g-1"),
                dbc.Row([
                    dbc.Col([html.Label("Port", style=_LABEL_STYLE),
                             dbc.Select(id="ad-conn-port",
                                        options=[{"label": f"Port {i} ({l})", "value": str(i)}
                                                 for i, l in enumerate(["Success","Fail","Alt","Err"])],
                                        value="0", style=_INPUT_STYLE)], width=12),
                ], className="mb-2 g-1"),
                dbc.Button([html.I(className="bi bi-arrow-right me-1"), "Connect"],
                           id="ad-conn-btn", outline=True, className="w-100",
                           style={"borderColor": ACCENT, "color": ACCENT}, size="sm"),
                dbc.Button([html.I(className="bi bi-x me-1"), "Remove Edge"],
                           id="ad-del-edge-btn", color="danger", outline=True,
                           className="w-100 mt-1", size="sm"),
            ]), className="card-premium border-0"),
        ]),

        # ── Centre: canvas ───────────────────────────────────────────────────
        dbc.Col(md=6, children=[
            dbc.Card(dbc.CardBody([
                dbc.Row([
                    dbc.Col(html.H6("Flow Canvas", style={"color": ACCENT}), width=6),
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button(html.I(className="bi bi-zoom-in"),  id="ad-zoom-in",  size="sm",
                                       outline=True, style={"borderColor": ACCENT, "color": ACCENT}),
                            dbc.Button(html.I(className="bi bi-zoom-out"), id="ad-zoom-out", size="sm",
                                       outline=True, style={"borderColor": ACCENT, "color": ACCENT}),
                            dbc.Button(html.I(className="bi bi-fullscreen"), id="ad-fit-btn", size="sm",
                                       outline=True, style={"borderColor": ACCENT, "color": ACCENT}),
                        ], className="float-end"),
                    ], width=6),
                ], className="mb-2 align-items-center"),

                cyto.Cytoscape(
                    id="ad-canvas",
                    elements=[],
                    layout={"name": "preset"},
                    style={"width": "100%", "height": "540px",
                           "backgroundColor": "#0d0f17",
                           "border": "1px solid rgba(26,188,156,0.2)",
                           "borderRadius": "6px"},
                    stylesheet=_CY_STYLESHEET,
                    boxSelectionEnabled=True,
                    autoRefreshLayout=False,
                    userPanningEnabled=True,
                    userZoomingEnabled=True,
                    minZoom=0.2,
                    maxZoom=3,
                    responsive=True,
                ),

                html.Small(
                    "Click node to select. Drag to move. Use Add Connection to wire nodes.",
                    style={"color": "#666", "fontSize": "0.75rem", "marginTop": "4px",
                           "display": "block"}
                ),
            ]), className="card-premium border-0"),
        ]),

        # ── Right: flow list + I/O ───────────────────────────────────────────
        dbc.Col(md=3, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Flow Nodes", className="mb-2", style={"color": ACCENT}),
                html.Div(id="ad-node-list", style={"maxHeight": "300px", "overflowY": "auto"},
                         children=[html.P("No nodes yet.", style={"color": "#a0a0a0",
                                                                   "fontSize": "0.82rem"})]),
            ]), className="card-premium border-0 mb-3"),

            dbc.Card(dbc.CardBody([
                html.H6("Loaded Experiments", className="mb-2", style={"color": ACCENT}),
                html.Div(id="ad-exp-list", style={"maxHeight": "150px", "overflowY": "auto"},
                         children=[html.P("No experiments loaded.",
                                          style={"color": "#a0a0a0", "fontSize": "0.82rem"})]),
            ]), className="card-premium border-0 mb-3"),

            dbc.Card(dbc.CardBody([
                html.H6("Save / Load / Export", className="mb-2", style={"color": ACCENT}),

                dbc.Input(id="ad-save-name", placeholder="flow_design.json", type="text",
                          className="mb-2", style=_INPUT_STYLE),
                dbc.Button([html.I(className="bi bi-save me-1"), "Save Flow Design"],
                           id="ad-save-btn", outline=True, className="w-100 mb-1",
                           style={"borderColor": ACCENT, "color": ACCENT}),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),
                html.Label("Load Flow Design (.json)", style=_LABEL_STYLE),
                dcc.Upload(
                    id="ad-load-upload",
                    children=html.Div([html.A("Browse", style={"color": ACCENT}),
                                       " or drop .json"]),
                    multiple=False, className="mt-1 mb-2",
                    style={"border": f"1px dashed {ACCENT}", "borderRadius": "6px",
                           "padding": "6px", "textAlign": "center",
                           "color": "#a0a0a0", "fontSize": "0.78rem", "cursor": "pointer"}
                ),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),
                dbc.Button([html.I(className="bi bi-check-circle me-1"), "Validate Flow"],
                           id="ad-validate-btn", color="secondary", outline=True,
                           className="w-100 mb-1", size="sm"),
                dbc.Button([html.I(className="bi bi-file-zip me-1"), "Export Flow Config ZIP"],
                           id="ad-export-btn", outline=True, className="w-100",
                           style={"borderColor": "#f39c12", "color": "#f39c12"}),

                html.Div(id="ad-export-status", className="mt-2",
                         style={"color": "#a0a0a0", "fontSize": "0.78rem"}),
            ]), className="card-premium border-0 mb-3"),

            # Log
            dbc.Card(dbc.CardBody([
                html.H6("Log", className="mb-2", style={"color": ACCENT}),
                dbc.Textarea(
                    id="ad-log",
                    value="Automation Designer ready.\n",
                    readOnly=True,
                    style={
                        "backgroundColor": "#0d0f17", "color": "#c0d0c0",
                        "fontFamily": "Courier New, monospace", "fontSize": "0.75rem",
                        "border": "1px solid rgba(255,255,255,0.08)",
                        "height": "140px", "resize": "vertical"
                    }
                ),
            ]), className="card-premium border-0"),
        ]),
    ]),
    ])


# ── Helper: rebuild cytoscape elements from stores ─────────────────────────────
def _build_elements(nodes_store: dict, edges_store: list) -> list:
    elements = []
    for node_id, nd in nodes_store.items():
        elements.append(_make_node_element(
            node_id,
            nd["type"],
            nd.get("name", ""),
            nd.get("experiment", ""),
            nd.get("x", 300),
            nd.get("y", 200),
        ))
    for edge in edges_store:
        port = edge.get("port", 0)
        port_labels = {0: "OK", 1: "Fail", 2: "Alt", 3: "Err"}
        elements.append({
            "data": {
                "source": edge["source"],
                "target": edge["target"],
                "label": f"P{port} {port_labels.get(port,'')}",
                "port": port,
            }
        })
    return elements


# ── Load experiments ──────────────────────────────────────────────────────────

@callback(
    Output("ad-experiments-store", "data"),
    Output("ad-exp-label", "children"),
    Output("ad-exp-list", "children"),
    Output("ad-toast", "children"),
    Input("ad-exp-upload", "contents"),
    State("ad-exp-upload", "filename"),
    prevent_initial_call=True
)
def load_experiments(content, fname):
    if not content:
        return no_update, no_update, no_update, no_update
    try:
        _, data = content.split(',')
        raw = base64.b64decode(data)

        experiments = {}
        if fname and fname.endswith('.xlsx'):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
            for ws in wb.worksheets:
                for table in ws.tables.values():
                    rng = ws[table.ref]
                    headers = [c.value for c in rng[0]]
                    if headers:
                        for row in rng[1:]:
                            entry = {str(headers[i]): (r.value or "") for i, r in enumerate(row)}
                            exp_name = entry.get("Experiment", entry.get("Test Name",
                                       entry.get("Name", f"Exp_{len(experiments)+1}")))
                            experiments[str(exp_name)] = entry
        else:
            loaded = json.loads(raw.decode('utf-8'))
            if isinstance(loaded, list):
                for e in loaded:
                    n = e.get("Experiment", e.get("Test Name", e.get("Name",
                              f"Exp_{len(experiments)+1}")))
                    experiments[str(n)] = e
            elif isinstance(loaded, dict):
                # Could be {exp_name: data} or a flow_design file
                if "nodes" in loaded:
                    return no_update, "Use Load Flow Design to load a flow JSON.", no_update, \
                           _toast("That looks like a flow design, not experiments. Use Load Flow Design.", "warning")
                for k, v in loaded.items():
                    if isinstance(v, dict):
                        experiments[k] = v
                    else:
                        experiments[k] = {"value": v}

        if not experiments:
            return no_update, "No experiments found.", no_update, _toast("No experiments found.", "warning")

        items = [
            html.Div(f"• {name}", style={"color": "#e0e0e0", "fontSize": "0.8rem", "marginBottom": "2px"})
            for name in list(experiments.keys())[:30]
        ]
        if len(experiments) > 30:
            items.append(html.Div(f"...and {len(experiments)-30} more",
                                  style={"color": "#a0a0a0", "fontSize": "0.78rem"}))

        return experiments, f"✓ {fname} ({len(experiments)} experiments)", items, \
               _toast(f"Loaded {len(experiments)} experiments.", "success", 2500)

    except Exception as e:
        logger.exception("Exp load error")
        return no_update, f"Error: {e}", no_update, _toast(f"Error: {e}", "danger")


# ── Add node ──────────────────────────────────────────────────────────────────

@callback(
    Output("ad-nodes-store", "data"),
    Output("ad-counter-store", "data"),
    Output("ad-canvas", "elements"),
    Output("ad-node-list", "children"),
    Output("ad-log", "value"),
    Output("ad-toast", "children", allow_duplicate=True),
    Input("ad-add-node-btn", "n_clicks"),
    Input("ad-del-node-btn", "n_clicks"),
    Input("ad-conn-btn", "n_clicks"),
    Input("ad-del-edge-btn", "n_clicks"),
    Input("ad-layout-btn", "n_clicks"),
    Input("ad-load-upload", "contents"),
    Input("ad-canvas", "tapNodeData"),
    Input("ad-canvas", "elements"),  # position updates from drag
    State("ad-node-type-sel", "value"),
    State("ad-nodes-store", "data"),
    State("ad-edges-store", "data"),
    State("ad-counter-store", "data"),
    State("ad-canvas", "selectedNodeData"),
    State("ad-conn-from", "value"),
    State("ad-conn-to", "value"),
    State("ad-conn-port", "value"),
    State("ad-load-upload", "filename"),
    State("ad-log", "value"),
    prevent_initial_call=True
)
def manage_canvas(add_c, del_c, conn_c, del_edge_c, layout_c, load_content,
                  tap_node, canvas_elements,
                  node_type, nodes_store, edges_store, counter,
                  selected_nodes, conn_from, conn_to, conn_port,
                  load_fname, log_val):
    trigger = ctx.triggered_id
    log = log_val or ""

    def _log(msg):
        nonlocal log
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        log = f"[{ts}] {msg}\n" + log  # prepend newest

    # Update positions from canvas drag
    if trigger == "ad-canvas" and canvas_elements:
        for el in canvas_elements:
            if "position" in el and "data" in el:
                nid = el["data"].get("id")
                if nid and nid in nodes_store:
                    nodes_store[nid]["x"] = el["position"]["x"]
                    nodes_store[nid]["y"] = el["position"]["y"]
        return (nodes_store, counter,
                no_update,  # don't rebuild — cytoscape handles it
                no_update, log, no_update)

    if trigger == "ad-add-node-btn":
        node_id = f"NODE_{counter:03d}"
        counter += 1
        # Stagger position
        n = len(nodes_store)
        x = 150 + (n % 4) * 180
        y = 150 + (n // 4) * 140
        nodes_store[node_id] = {
            "id": node_id, "name": node_id,
            "type": node_type,
            "x": x, "y": y,
            "experiment": "",
            "connections": {}
        }
        _log(f"Added {node_type}: {node_id}")
        elements = _build_elements(nodes_store, edges_store)
        return nodes_store, counter, elements, _node_list(nodes_store), log, \
               _toast(f"Added {node_type}: {node_id}", "success", 1500)

    if trigger == "ad-del-node-btn":
        if not selected_nodes:
            return no_update, no_update, no_update, no_update, log, _toast("Select a node first.", "warning")
        for nd in selected_nodes:
            nid = nd.get("id")
            if nid in nodes_store:
                del nodes_store[nid]
                edges_store = [e for e in edges_store
                               if e.get("source") != nid and e.get("target") != nid]
                _log(f"Deleted node: {nid}")
        elements = _build_elements(nodes_store, edges_store)
        return nodes_store, counter, elements, _node_list(nodes_store), log, \
               _toast("Node(s) deleted.", "info", 1500)

    if trigger == "ad-conn-btn":
        if not conn_from or not conn_to:
            return no_update, no_update, no_update, no_update, log, _toast("Enter From and To node IDs.", "warning")
        if conn_from not in nodes_store:
            return no_update, no_update, no_update, no_update, log, _toast(f"Node '{conn_from}' not found.", "warning")
        if conn_to not in nodes_store:
            return no_update, no_update, no_update, no_update, log, _toast(f"Node '{conn_to}' not found.", "warning")
        edge = {"source": conn_from, "target": conn_to, "port": int(conn_port or 0)}
        # Remove duplicate
        edges_store = [e for e in edges_store
                       if not (e["source"] == conn_from and e["target"] == conn_to
                               and e["port"] == edge["port"])]
        edges_store.append(edge)
        nodes_store[conn_from].setdefault("connections", {})[str(conn_port)] = conn_to
        _log(f"Connected {conn_from} → {conn_to} port {conn_port}")
        elements = _build_elements(nodes_store, edges_store)
        return nodes_store, counter, elements, _node_list(nodes_store), log, \
               _toast(f"Connected {conn_from} → {conn_to}.", "success", 1500)

    if trigger == "ad-del-edge-btn":
        if not selected_nodes:
            return no_update, no_update, no_update, no_update, log, _toast("Select source node first.", "warning")
        nid = selected_nodes[0].get("id")
        edges_store = [e for e in edges_store if e.get("source") != nid]
        if nid in nodes_store:
            nodes_store[nid]["connections"] = {}
        _log(f"Removed all edges from {nid}")
        elements = _build_elements(nodes_store, edges_store)
        return nodes_store, counter, elements, _node_list(nodes_store), log, \
               _toast(f"Removed edges from {nid}.", "info", 1500)

    if trigger == "ad-layout-btn":
        # Simple hierarchical layout
        nodes_store = _auto_layout(nodes_store, edges_store)
        _log("Applied auto layout")
        elements = _build_elements(nodes_store, edges_store)
        return nodes_store, counter, elements, _node_list(nodes_store), log, no_update

    if trigger == "ad-load-upload" and load_content:
        try:
            _, data = load_content.split(',')
            design = json.loads(base64.b64decode(data).decode('utf-8'))
            new_nodes = {}
            new_edges = []
            new_counter = 1
            for nid, nd in design.get("nodes", {}).items():
                new_nodes[nid] = nd
                m = re.search(r'(\d+)', nid)
                if m:
                    new_counter = max(new_counter, int(m.group(1)) + 1)
                for port, tgt in nd.get("connections", {}).items():
                    new_edges.append({"source": nid, "target": tgt, "port": int(port)})
            elements = _build_elements(new_nodes, new_edges)
            _log(f"Loaded flow design: {load_fname} ({len(new_nodes)} nodes)")
            return new_nodes, new_counter, elements, _node_list(new_nodes), log, \
                   _toast(f"Flow loaded: {load_fname}", "success")
        except Exception as e:
            _log(f"Load error: {e}")
            return no_update, no_update, no_update, no_update, log, _toast(f"Load error: {e}", "danger")

    return no_update, no_update, no_update, no_update, log, no_update


# ── Update edges store in a separate store (needed since manage_canvas doesn't output it) ──

@callback(
    Output("ad-edges-store", "data"),
    Input("ad-conn-btn", "n_clicks"),
    Input("ad-del-edge-btn", "n_clicks"),
    Input("ad-load-upload", "contents"),
    State("ad-nodes-store", "data"),
    State("ad-edges-store", "data"),
    State("ad-conn-from", "value"),
    State("ad-conn-to", "value"),
    State("ad-conn-port", "value"),
    State("ad-canvas", "selectedNodeData"),
    prevent_initial_call=True
)
def update_edges_store(conn_c, del_edge_c, load_content,
                       nodes_store, edges_store, conn_from, conn_to, conn_port,
                       selected_nodes):
    trigger = ctx.triggered_id
    if trigger == "ad-conn-btn":
        if conn_from and conn_to and conn_from in nodes_store and conn_to in nodes_store:
            edge = {"source": conn_from, "target": conn_to, "port": int(conn_port or 0)}
            edges_store = [e for e in edges_store
                           if not (e["source"] == conn_from and e["target"] == conn_to
                                   and e["port"] == edge["port"])]
            edges_store.append(edge)
            return edges_store
    if trigger == "ad-del-edge-btn":
        if selected_nodes:
            nid = selected_nodes[0].get("id")
            return [e for e in edges_store if e.get("source") != nid]
    if trigger == "ad-load-upload" and load_content:
        try:
            _, data = load_content.split(',')
            design = json.loads(base64.b64decode(data).decode('utf-8'))
            new_edges = []
            for nid, nd in design.get("nodes", {}).items():
                for port, tgt in nd.get("connections", {}).items():
                    new_edges.append({"source": nid, "target": tgt, "port": int(port)})
            return new_edges
        except:
            pass
    return no_update


# ── Node editor (when node selected) ──────────────────────────────────────────

@callback(
    Output("ad-node-editor", "children"),
    Output("ad-selected-node", "data"),
    Input("ad-canvas", "tapNodeData"),
    State("ad-nodes-store", "data"),
    State("ad-experiments-store", "data"),
    prevent_initial_call=True
)
def show_node_editor(tap_data, nodes_store, experiments):
    if not tap_data:
        return no_update, no_update
    nid = tap_data.get("id")
    nd = nodes_store.get(nid)
    if not nd:
        return no_update, no_update
    exp_options = [{"label": "— none —", "value": ""}] + \
                  [{"label": k, "value": k} for k in experiments.keys()]
    editor = html.Div([
        html.P(f"Node: {nid}", style={"color": ACCENT, "fontWeight": "600", "marginBottom": "6px"}),
        html.Label("Name", style=_LABEL_STYLE),
        dbc.Input(id="ad-editor-name", value=nd.get("name", ""), type="text",
                  className="mb-1", style=_INPUT_STYLE),
        html.Label("Experiment", style=_LABEL_STYLE),
        dbc.Select(id="ad-editor-exp",
                   options=exp_options,
                   value=nd.get("experiment", ""),
                   className="mb-2", style=_INPUT_STYLE),
        dbc.Button([html.I(className="bi bi-check me-1"), "Apply"],
                   id="ad-editor-apply", outline=True, className="w-100",
                   style={"borderColor": ACCENT, "color": ACCENT}, size="sm"),
    ])
    return editor, nid


@callback(
    Output("ad-nodes-store", "data", allow_duplicate=True),
    Output("ad-canvas", "elements", allow_duplicate=True),
    Output("ad-node-list", "children", allow_duplicate=True),
    Output("ad-toast", "children", allow_duplicate=True),
    Input("ad-editor-apply", "n_clicks"),
    State("ad-selected-node", "data"),
    State("ad-editor-name", "value"),
    State("ad-editor-exp", "value"),
    State("ad-nodes-store", "data"),
    State("ad-edges-store", "data"),
    prevent_initial_call=True
)
def apply_node_edit(n_clicks, node_id, name, exp, nodes_store, edges_store):
    if not node_id or node_id not in nodes_store:
        return no_update, no_update, no_update, _toast("No node selected.", "warning")
    nodes_store[node_id]["name"] = name or node_id
    nodes_store[node_id]["experiment"] = exp or ""
    elements = _build_elements(nodes_store, edges_store)
    return nodes_store, elements, _node_list(nodes_store), _toast(f"Node {node_id} updated.", "success", 1500)


# ── Save / Validate / Export ───────────────────────────────────────────────────

@callback(
    Output("ad-download", "data"),
    Output("ad-export-status", "children"),
    Output("ad-toast", "children", allow_duplicate=True),
    Output("ad-result-store", "data"),
    Input("ad-save-btn", "n_clicks"),
    Input("ad-export-btn", "n_clicks"),
    Input("ad-validate-btn", "n_clicks"),
    State("ad-nodes-store", "data"),
    State("ad-edges-store", "data"),
    State("ad-experiments-store", "data"),
    State("ad-vid", "value"),
    State("ad-bucket", "value"),
    State("ad-com", "value"),
    State("ad-ip", "value"),
    State("ad-unit-flags", "value"),
    State("ad-save-name", "value"),
    prevent_initial_call=True
)
def save_or_export(save_c, export_c, validate_c,
                   nodes_store, edges_store, experiments,
                   vid, bucket, com_port, ip_addr, unit_flags, save_name):
    trigger = ctx.triggered_id

    if trigger == "ad-validate-btn":
        errors, warnings = _validate(nodes_store, edges_store, experiments)
        if errors:
            return no_update, html.Div([
                html.P("❌ Errors:", style={"color": "#e74c3c", "fontSize": "0.82rem", "marginBottom": "4px"}),
                *[html.P(f"• {e}", style={"color": "#e74c3c", "fontSize": "0.8rem"}) for e in errors]
            ]), _toast(f"{len(errors)} validation error(s).", "danger"), no_update
        else:
            return no_update, html.P("✓ Flow valid!", style={"color": "#1abc9c"}), \
                   _toast("Flow is valid.", "success", 2000), no_update

    if trigger == "ad-save-btn":
        if not nodes_store:
            return no_update, no_update, _toast("Nothing to save.", "warning"), no_update
        design = {
            "nodes": nodes_store,
            "edges": edges_store,
            "unit_config": {
                "Visual ID": vid or "",
                "Bucket": bucket or "",
                "COM Port": com_port or "",
                "IP Address": ip_addr or "",
                "600W Unit": "600w" in (unit_flags or []),
                "Check Core": "check_core" in (unit_flags or []),
            }
        }
        fname = save_name or "flow_design.json"
        if not fname.endswith(".json"):
            fname += ".json"
        return dcc.send_string(json.dumps(design, indent=2), fname), \
               f"✓ Saved: {fname}", _toast(f"Flow saved: {fname}", "success"), no_update

    if trigger == "ad-export-btn":
        errors, _ = _validate(nodes_store, edges_store, experiments)
        if errors:
            return no_update, no_update, \
                   _toast(f"Validation errors: {'; '.join(errors[:2])}", "danger"), no_update

        # Apply unit config overrides to experiments
        unit_config = {
            "Visual ID": vid or "",
            "Bucket": bucket or "",
            "COM Port": com_port or "",
            "IP Address": ip_addr or "",
            "600W Unit": "600w" in (unit_flags or []),
            "Check Core": "check_core" in (unit_flags or []),
        }
        enriched_exps = {}
        for node_id, nd in nodes_store.items():
            exp_name = nd.get("experiment")
            if exp_name and exp_name in experiments:
                entry = dict(experiments[exp_name])
                entry.update({k: v for k, v in unit_config.items() if v not in ("", False, None)})
                enriched_exps[exp_name] = entry

        zip_bytes = _build_export_zip(nodes_store, edges_store, enriched_exps, unit_config)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_fname = f"FrameworkAutomation_{ts}.zip"
        b64_zip = base64.b64encode(zip_bytes).decode()
        return (dcc.send_bytes(zip_bytes, zip_fname),
                f"✓ Exported: {zip_fname}",
                _toast(f"Exported {zip_fname}", "success"),
                b64_zip)

    return no_update, no_update, no_update, no_update


# ── Helpers ───────────────────────────────────────────────────────────────────

def _node_list(nodes_store):
    if not nodes_store:
        return html.P("No nodes.", style={"color": "#a0a0a0", "fontSize": "0.82rem"})
    rows = []
    for nid, nd in nodes_store.items():
        info = _TYPE_MAP.get(nd["type"], {"label": nd["type"], "color": "#555"})
        exp_tag = f" [{nd.get('experiment', '')[:10]}]" if nd.get("experiment") else ""
        rows.append(html.Div([
            html.Span("● ", style={"color": info["color"], "fontSize": "0.9rem"}),
            html.Span(f"{nid}: {info['label']}{exp_tag}",
                      style={"color": "#e0e0e0", "fontSize": "0.8rem"})
        ], style={"marginBottom": "3px"}))
    return rows


def _validate(nodes_store, edges_store, experiments):
    errors, warnings = [], []
    start_nodes = [n for n in nodes_store.values() if n["type"] == "StartNode"]
    end_nodes   = [n for n in nodes_store.values() if n["type"] == "EndNode"]
    if not start_nodes:
        errors.append("Flow must have a StartNode")
    if not end_nodes:
        warnings.append("Flow has no EndNode")
    no_exp = [nid for nid, nd in nodes_store.items()
              if nd["type"] not in ("StartNode", "EndNode") and not nd.get("experiment")]
    if no_exp:
        warnings.append(f"Nodes without experiments: {', '.join(no_exp[:3])}")
    return errors, warnings


def _auto_layout(nodes_store, edges_store):
    """Simple top-down hierarchical layout."""
    if not nodes_store:
        return nodes_store
    # Find root (StartNode or first node)
    roots = [nid for nid, nd in nodes_store.items() if nd["type"] == "StartNode"]
    if not roots:
        roots = [next(iter(nodes_store))]
    # BFS
    visited = {}
    queue = [(roots[0], 0, 0)]
    level_x = {}
    while queue:
        nid, level, idx = queue.pop(0)
        if nid in visited:
            continue
        visited[nid] = level
        level_x.setdefault(level, 0)
        nodes_store[nid]["x"] = 200 + level * 220
        nodes_store[nid]["y"] = 150 + level_x[level] * 160
        level_x[level] += 1
        for edge in edges_store:
            if edge["source"] == nid:
                queue.append((edge["target"], level + 1, level_x.get(level + 1, 0)))
    return nodes_store


def _build_export_zip(nodes_store, edges_store, experiments, unit_config):
    """Build the 4-file ZIP matching original export_flow() format."""
    # Structure file
    structure_data = {}
    for nid, nd in nodes_store.items():
        output_map = {}
        for port, tgt in nd.get("connections", {}).items():
            output_map[str(port)] = tgt
        structure_data[nid] = {
            "name": nd["name"],
            "instanceType": nd["type"],
            "flow": nd.get("experiment", "default"),
            "outputNodeMap": output_map,
        }

    # Flows file
    flows_data = {n: d for n, d in experiments.items()}

    # INI file
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ini_lines = [
        "[DEFAULT]",
        "# Automation Flow Configuration",
        f"# Generated on {ts}",
        f"# Visual ID: {unit_config.get('Visual ID', '')}",
        f"# Product: {unit_config.get('Product', 'GNR')}",
        "",
    ]
    for exp_name in flows_data:
        ini_lines.append(f"[{exp_name}]")
        ini_lines.append("# Experiment-specific configuration")
        ini_lines.append("")
    ini_content = "\n".join(ini_lines)

    # Positions file
    positions_data = {nid: {"x": nd["x"], "y": nd["y"]}
                      for nid, nd in nodes_store.items()}

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("FrameworkAutomationStructure.json", json.dumps(structure_data, indent=2))
        zf.writestr("FrameworkAutomationFlows.json",    json.dumps(flows_data, indent=2))
        zf.writestr("FrameworkAutomationInit.ini",       ini_content)
        zf.writestr("FrameworkAutomationPositions.json", json.dumps(positions_data, indent=2))
    return buf.getvalue()


def _toast(msg, icon, duration=4000):
    return dbc.Toast(
        msg, icon=icon, duration=duration, is_open=True,
        style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
        className="toast-custom"
    )
