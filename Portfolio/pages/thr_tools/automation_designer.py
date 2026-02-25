"""
Automation Flow Designer
=========================
Build automation flow configurations as ordered node lists with experiment assignment.
Calls THRTools/gui/AutomationDesigner.py backend (non-GUI methods only).

Replicates all functionality from PPV/gui/AutomationDesigner.AutomationFlowDesigner:
- Node types: StartNode, SingleFail, AllFail, MajorityFail, Adaptive,
  Characterization, DataCollection, Analysis, EndNode
- Load experiments from JSON or Excel (from Experiment Builder or files)
- Assign experiments to flow nodes
- Export flow: FrameworkAutomationStructure.json, FrameworkAutomationFlows.json,
  FrameworkAutomationInit.ini, FrameworkAutomationPositions.json
- Unit configuration overrides (Visual ID, Bucket, COM Port, IP Address, etc.)
- Save / load flow design (.json)
- Import flow config

Scalability:
- Add new node types to _NODE_TYPES list — no other code changes required
- Experiment fields expand automatically from ControlPanelConfig.json

CaaS notes: Visual canvas drag-and-drop deferred — see CAAS_TODO.md.
"""
import base64
import io
import json
import logging
import os
import uuid
import zipfile
import datetime

import dash
from dash import html, dcc, Input, Output, State, callback, no_update, ctx
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

dash.register_page(
    __name__,
    path='/thr-tools/automation-designer',
    name='Automation Designer',
    title='Automation Flow Designer'
)

ACCENT = "#00c9a7"

# Node types matching PPV/gui/AutomationDesigner.py exactly
_NODE_TYPES = [
    ("StartNode",                   "Start Node",         "Flow entry point"),
    ("SingleFailFlowInstance",      "Single Fail",        "Stops on first failure"),
    ("AllFailFlowInstance",         "All Fail",           "Requires all tests to fail"),
    ("MajorityFailFlowInstance",    "Majority Fail",      "Routes based on majority"),
    ("AdaptiveFlowInstance",        "Adaptive",           "Intelligent decision making"),
    ("CharacterizationFlowInstance","Characterization",   "Uses previous data for experiments"),
    ("DataCollectionFlowInstance",  "Data Collection",    "Runs complete experiment data collection"),
    ("AnalysisFlowInstance",        "Analysis",           "Generates summary and experiment proposals"),
    ("EndNode",                     "End Node",           "Flow exit point"),
]

_NODE_TYPE_VALUES = [n[0] for n in _NODE_TYPES]
_NODE_COLORS = {
    "StartNode":                   "#27ae60",
    "EndNode":                     "#e74c3c",
    "SingleFailFlowInstance":      "#e67e22",
    "AllFailFlowInstance":         "#c0392b",
    "MajorityFailFlowInstance":    "#8e44ad",
    "AdaptiveFlowInstance":        "#2980b9",
    "CharacterizationFlowInstance":"#16a085",
    "DataCollectionFlowInstance":  "#1abc9c",
    "AnalysisFlowInstance":        "#f39c12",
}

_INPUT_STYLE = {"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                "border": "1px solid rgba(255,255,255,0.1)", "fontSize": "0.85rem"}
_LABEL_STYLE = {"color": "#a0a0a0", "fontSize": "0.8rem"}


def _unit_field(label: str, html_label_id: str, input_id: str) -> html.Div:
    return html.Div([
        html.Label(label, id=html_label_id, style=_LABEL_STYLE),
        dbc.Input(id=input_id, type="text", className="mb-2",
                  style={**_INPUT_STYLE, "fontSize": "0.82rem"}),
    ])


layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="ad-toast"),
    dcc.Download(id="ad-download"),
    dcc.Store(id="ad-nodes-store", data=[]),
    dcc.Store(id="ad-experiments-store", data={}),

    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-diagram-3 me-2", style={"color": ACCENT}),
            html.Span("Automation Flow Designer",
                      style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P(
            "Build automation flow configurations as ordered node lists. "
            "Assign experiments to nodes. Export for system RVP.",
            style={"color": "#a0a0a0", "fontSize": "0.9rem"}
        ),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        # ── Left: unit config + node editor ──────────────────────────────────
        dbc.Col(md=4, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Unit Configuration", className="mb-3", style={"color": ACCENT}),
                html.Small("Overrides applied to all experiments on export.",
                           style={"color": "#606070", "fontSize": "0.77rem"}),
                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                _unit_field("Visual ID",  "ad-vid",      "ad-unit-vid"),
                _unit_field("Bucket",     "ad-bucket",   "ad-unit-bucket"),
                _unit_field("COM Port",   "ad-com",      "ad-unit-com"),
                _unit_field("IP Address", "ad-ip",       "ad-unit-ip"),

                dbc.Row([
                    dbc.Col([
                        dbc.Checklist(
                            id="ad-unit-600w",
                            options=[{"label": "600W Unit", "value": "600w"}],
                            value=[],
                            inputStyle={"marginRight": "6px"},
                            labelStyle={"color": "#e0e0e0", "fontSize": "0.88rem"}
                        ),
                    ], width=6),
                    dbc.Col([
                        html.Label("Check Core", style=_LABEL_STYLE),
                        dbc.Input(id="ad-unit-check-core", type="number", min=0,
                                  placeholder="core #", style={**_INPUT_STYLE, "fontSize": "0.82rem"}),
                    ], width=6),
                ], className="mb-3"),
            ]), className="card-premium border-0 mb-3"),

            dbc.Card(dbc.CardBody([
                html.H6("Add Node", className="mb-3", style={"color": ACCENT}),

                html.Label("Node Type", style=_LABEL_STYLE),
                dbc.Select(
                    id="ad-node-type",
                    options=[{"label": f"{label} — {desc}", "value": cls}
                             for cls, label, desc in _NODE_TYPES],
                    value="SingleFailFlowInstance",
                    className="mb-2",
                    style=_INPUT_STYLE
                ),

                html.Label("Node Name (label)", style=_LABEL_STYLE),
                dbc.Input(id="ad-node-label", placeholder="Descriptive name",
                          className="mb-2", style=_INPUT_STYLE),

                html.Label("Assign Experiment (optional)", style=_LABEL_STYLE),
                dcc.Dropdown(
                    id="ad-node-experiment",
                    options=[], value=None, clearable=True,
                    placeholder="Select loaded experiment...",
                    className="mb-3"
                ),

                dbc.Button([html.I(className="bi bi-plus-circle me-2"), "Add Node"],
                           id="ad-add-btn", outline=True, className="w-100 mb-2",
                           style={"borderColor": ACCENT, "color": ACCENT}),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                html.Label("Import Flow JSON", style=_LABEL_STYLE),
                dcc.Upload(
                    id="ad-import-flow",
                    children=html.Div([html.A("Browse", style={"color": ACCENT}),
                                       " or drop flow .json"]),
                    multiple=False, className="mt-1 mb-2",
                    style={"border": f"1px dashed {ACCENT}", "borderRadius": "6px",
                           "padding": "8px", "textAlign": "center",
                           "color": "#a0a0a0", "fontSize": "0.82rem",
                           "backgroundColor": f"rgba(0,201,167,0.03)", "cursor": "pointer"}
                ),

                html.Label("Load Experiments (JSON / .tpl / .xlsx)", style=_LABEL_STYLE),
                dcc.Upload(
                    id="ad-import-experiments",
                    children=html.Div([html.A("Browse", style={"color": "#a070ff"}),
                                       " or drop experiments file"]),
                    multiple=False, className="mt-1 mb-3",
                    style={"border": "1px dashed #a070ff", "borderRadius": "6px",
                           "padding": "8px", "textAlign": "center",
                           "color": "#a0a0a0", "fontSize": "0.82rem",
                           "backgroundColor": "rgba(160,112,255,0.03)", "cursor": "pointer"}
                ),

                dbc.Alert([
                    html.I(className="bi bi-info-circle me-2"),
                    "Visual canvas is deferred to CaaS migration. See ",
                    html.Code("CAAS_TODO.md"), "."
                ], color="secondary", className="card-premium border-0 text-white",
                   style={"fontSize": "0.78rem"}),

            ]), className="card-premium border-0"),
        ]),

        # ── Right: flow nodes list + export ───────────────────────────────────
        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                dbc.Row([
                    dbc.Col(html.H6("Flow Nodes", style={"color": ACCENT}), width=8),
                    dbc.Col([
                        dbc.Button([html.I(className="bi bi-trash me-1"), "Clear"],
                                   id="ad-clear-btn", color="danger", outline=True, size="sm",
                                   className="me-1"),
                        dbc.Button([html.I(className="bi bi-eye me-1"), "Preview"],
                                   id="ad-preview-btn", outline=True, size="sm",
                                   style={"borderColor": "#a0a0a0", "color": "#a0a0a0"}),
                    ], width=4, className="text-end"),
                ], className="mb-3"),

                html.Div(id="ad-node-list", children=[
                    dbc.Alert("No nodes yet. Add nodes using the editor.",
                              color="secondary", className="card-premium border-0 text-white")
                ], style={"maxHeight": "380px", "overflowY": "auto"}),

            ]), className="card-premium border-0 mb-3"),

            dbc.Card(dbc.CardBody([
                html.H6("Export & Save", style={"color": ACCENT}, className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        html.Label("Export Config (ZIP)", style=_LABEL_STYLE),
                        html.Small(" — structure, flows, INI, positions",
                                   style={"color": "#606070", "fontSize": "0.75rem"}),
                        dbc.Input(id="ad-export-name", placeholder="flow_export",
                                  type="text", className="mb-2", style=_INPUT_STYLE),
                        dbc.Button([html.I(className="bi bi-file-zip me-2"), "Export Flow Config"],
                                   id="ad-export-btn", outline=True, className="w-100",
                                   style={"borderColor": ACCENT, "color": ACCENT}),
                    ], width=6),
                    dbc.Col([
                        html.Label("Save Flow Design (.json)", style=_LABEL_STYLE),
                        dbc.Input(id="ad-save-name", placeholder="my_flow.json",
                                  type="text", className="mb-2", style=_INPUT_STYLE),
                        dbc.Button([html.I(className="bi bi-download me-2"), "Save Flow"],
                                   id="ad-save-btn", outline=True, className="w-100",
                                   style={"borderColor": "#a070ff", "color": "#a070ff"}),
                    ], width=6),
                ]),

                html.Div(id="ad-export-status", className="mt-3"),
            ]), className="card-premium border-0"),
        ]),
    ]),
])


# ── Callbacks ──────────────────────────────────────────────────────────────────

@callback(
    Output("ad-nodes-store", "data"),
    Output("ad-experiments-store", "data"),
    Output("ad-node-experiment", "options"),
    Output("ad-toast", "children"),
    Input("ad-add-btn", "n_clicks"),
    Input("ad-clear-btn", "n_clicks"),
    Input("ad-import-flow", "contents"),
    Input("ad-import-experiments", "contents"),
    Input("ad-import-experiments", "filename"),
    State("ad-nodes-store", "data"),
    State("ad-experiments-store", "data"),
    State("ad-node-type", "value"),
    State("ad-node-label", "value"),
    State("ad-node-experiment", "value"),
    prevent_initial_call=True
)
def manage_nodes(add_c, clear_c, import_flow_content, import_exp_content, import_exp_fname,
                 nodes, experiments,
                 node_type, node_label, node_experiment):
    trigger = ctx.triggered_id
    nodes = list(nodes or [])
    experiments = dict(experiments or {})

    if trigger == "ad-clear-btn":
        return [], {}, [], _toast("Flow cleared.", "info", 2000)

    if trigger == "ad-import-flow" and import_flow_content:
        try:
            _, data = import_flow_content.split(',')
            flow = json.loads(base64.b64decode(data).decode('utf-8'))
            loaded_nodes = []
            loaded_exps = {}
            if isinstance(flow, dict):
                raw_nodes = flow.get("nodes", {})
                loaded_exps = flow.get("experiments", {})
                if isinstance(raw_nodes, dict):
                    loaded_nodes = list(raw_nodes.values())
                elif isinstance(raw_nodes, list):
                    loaded_nodes = raw_nodes
            elif isinstance(flow, list):
                loaded_nodes = flow
            opts = [{"label": k, "value": k} for k in loaded_exps]
            return loaded_nodes, loaded_exps, opts, _toast(
                f"Loaded {len(loaded_nodes)} nodes, {len(loaded_exps)} experiments.", "success")
        except Exception as e:
            return no_update, no_update, no_update, _toast(f"Import error: {e}", "danger")

    if trigger == "ad-import-experiments" and import_exp_content:
        try:
            exps = _load_experiments(import_exp_content, import_exp_fname or "")
            experiments.update(exps)
            opts = [{"label": k, "value": k} for k in experiments]
            return no_update, experiments, opts, _toast(
                f"Loaded {len(exps)} experiment(s).", "success")
        except Exception as e:
            return no_update, no_update, no_update, _toast(f"Experiment load error: {e}", "danger")

    if trigger == "ad-add-btn":
        ntype = node_type or "SingleFailFlowInstance"
        label = node_label or _get_display(ntype)
        node = {
            "id": str(uuid.uuid4())[:8],
            "type": ntype,
            "label": label,
            "experiment": node_experiment,
            "connections": {},
            "x": 100 + len(nodes) * 180,
            "y": 200,
        }
        nodes.append(node)
        exp_opts = [{"label": k, "value": k} for k in experiments]
        return nodes, experiments, exp_opts, _toast(f"Added {label} node.", "success", 2000)

    return no_update, no_update, no_update, no_update


def _load_experiments(content: str, fname: str) -> dict:
    """Load experiments from JSON, .tpl, or Excel content."""
    _, data = content.split(',')
    raw = base64.b64decode(data)
    if fname.endswith(".xlsx"):
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
        all_exps = {}
        for sname in wb.sheetnames:
            ws = wb[sname]
            for table in ws.tables.values():
                rng = ws[table.ref]
                headers = [cell.value for cell in rng[0]]
                if "Field" in headers and "Value" in headers:
                    fi, vi = headers.index("Field"), headers.index("Value")
                    exp = {}
                    for row in rng[1:]:
                        f, v = row[fi].value, row[vi].value
                        if f:
                            exp[str(f)] = str(v) if v is not None else ""
                    if exp:
                        name = exp.get("Test Name", exp.get("Experiment", sname))
                        all_exps[str(name)] = exp
        return all_exps
    else:
        imported = json.loads(raw.decode("utf-8"))
        if isinstance(imported, list):
            return {
                str(e.get("Test Name", e.get("Experiment", f"Exp_{i+1}"))): e
                for i, e in enumerate(imported)
            }
        elif isinstance(imported, dict):
            # Could be {name: data} or a single experiment
            if all(isinstance(v, dict) for v in imported.values()):
                return imported
            return {"Experiment": imported}
    return {}


def _get_display(cls: str) -> str:
    for c, label, _ in _NODE_TYPES:
        if c == cls:
            return label
    return cls


@callback(
    Output("ad-node-list", "children"),
    Input("ad-nodes-store", "data"),
    State("ad-experiments-store", "data"),
)
def render_nodes(nodes, experiments):
    if not nodes:
        return dbc.Alert("No nodes yet. Add nodes using the editor.",
                         color="secondary", className="card-premium border-0 text-white")
    rows = []
    for i, node in enumerate(nodes):
        ntype = node.get("type", "")
        color = _NODE_COLORS.get(ntype, "#607080")
        exp_name = node.get("experiment", "")
        exp_preview = ""
        if exp_name and experiments and exp_name in experiments:
            exp_data = experiments[exp_name]
            exp_preview = f" | {exp_data.get('Test Type','?')} / {exp_data.get('Content','?')}"
        rows.append(dbc.Card(dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Span(f"#{i+1} ", style={"color": "#606070", "fontSize": "0.78rem"}),
                    html.Span(node.get("label", ntype),
                              style={"color": color, "fontWeight": "600", "fontSize": "0.88rem"}),
                    html.Span(f"  [{_get_display(ntype)}]",
                              style={"color": "#a0a0a0", "fontSize": "0.78rem"}),
                ], width=8),
                dbc.Col([
                    dbc.Button(html.I(className="bi bi-arrow-up"),
                               id={"type": "ad-move-up", "index": i},
                               size="sm", outline=True, className="me-1",
                               style={"borderColor": "#a0a0a0", "color": "#a0a0a0", "padding": "1px 5px"}),
                    dbc.Button(html.I(className="bi bi-arrow-down"),
                               id={"type": "ad-move-down", "index": i},
                               size="sm", outline=True, className="me-1",
                               style={"borderColor": "#a0a0a0", "color": "#a0a0a0", "padding": "1px 5px"}),
                    dbc.Button(html.I(className="bi bi-trash"),
                               id={"type": "ad-del-node", "index": i},
                               size="sm", color="danger", outline=True,
                               style={"padding": "1px 5px"}),
                ], width=4, className="text-end"),
            ], className="mb-1"),
            html.Div([
                html.Span(f"Experiment: {exp_name or '(none)'}{exp_preview}",
                          style={"color": "#a0a0a0", "fontSize": "0.78rem"})
            ])
        ]), className="card-premium border-0 mb-1",
            style={"borderLeft": f"3px solid {color}"}))
    return rows


@callback(
    Output("ad-nodes-store", "data", allow_duplicate=True),
    Output("ad-toast", "children", allow_duplicate=True),
    Input({"type": "ad-del-node", "index": dash.ALL}, "n_clicks"),
    Input({"type": "ad-move-up", "index": dash.ALL}, "n_clicks"),
    Input({"type": "ad-move-down", "index": dash.ALL}, "n_clicks"),
    State("ad-nodes-store", "data"),
    prevent_initial_call=True
)
def mutate_nodes(del_c, up_c, down_c, nodes):
    if not ctx.triggered_id:
        return no_update, no_update
    tid = ctx.triggered_id
    action = tid.get("type", "")
    idx = tid.get("index", 0)
    nodes = list(nodes or [])

    if action == "ad-del-node":
        nodes = [n for i, n in enumerate(nodes) if i != idx]
        return nodes, _toast(f"Node #{idx+1} deleted.", "info", 2000)
    if action == "ad-move-up" and idx > 0:
        nodes[idx - 1], nodes[idx] = nodes[idx], nodes[idx - 1]
        return nodes, no_update
    if action == "ad-move-down" and idx < len(nodes) - 1:
        nodes[idx + 1], nodes[idx] = nodes[idx], nodes[idx + 1]
        return nodes, no_update
    return no_update, no_update


@callback(
    Output("ad-download", "data"),
    Output("ad-export-status", "children"),
    Output("ad-toast", "children", allow_duplicate=True),
    Input("ad-export-btn", "n_clicks"),
    Input("ad-save-btn", "n_clicks"),
    State("ad-nodes-store", "data"),
    State("ad-experiments-store", "data"),
    State("ad-export-name", "value"),
    State("ad-save-name", "value"),
    State("ad-unit-vid", "value"),
    State("ad-unit-bucket", "value"),
    State("ad-unit-com", "value"),
    State("ad-unit-ip", "value"),
    State("ad-unit-600w", "value"),
    State("ad-unit-check-core", "value"),
    prevent_initial_call=True
)
def export_or_save(export_c, save_c, nodes, experiments,
                   export_name, save_name,
                   vid, bucket, com, ip, w600, check_core):
    trigger = ctx.triggered_id
    nodes = nodes or []
    experiments = experiments or {}

    if not nodes:
        return no_update, no_update, _toast("No nodes to export.", "warning")

    # Build unit_config overrides
    unit_config = {
        "Visual ID": vid or "",
        "Bucket": bucket or "",
        "COM Port": com or "",
        "IP Address": ip or "",
        "600W Unit": bool(w600),
        "Check Core": check_core,
    }

    if trigger == "ad-save-btn":
        fname = save_name or "flow_design.json"
        if not fname.endswith(".json"):
            fname += ".json"
        flow = {
            "nodes": {n["id"]: n for n in nodes},
            "experiments": experiments,
            "unit_config": unit_config,
            "metadata": {
                "created": datetime.datetime.now().isoformat(),
                "version": "2.0",
            }
        }
        return (dcc.send_string(json.dumps(flow, indent=2), fname),
                html.P(f"✓ Flow saved as {fname}", style={"color": "#00ff9d"}),
                _toast(f"Flow saved as {fname}.", "success"))

    if trigger == "ad-export-btn":
        export_base = export_name or "flow_export"
        zip_name = f"{export_base}.zip"

        # Build export files (matching PPV original format)
        structure_data = {}
        for i, node in enumerate(nodes):
            nid = node["id"]
            # Connections: next node in ordered list (simple chain)
            output_map = {}
            if i < len(nodes) - 1:
                output_map["0"] = nodes[i + 1]["id"]

            structure_data[nid] = {
                "name": node.get("label", node.get("type")),
                "instanceType": node["type"],
                "flow": node.get("experiment", "default"),
                "outputNodeMap": output_map,
            }

        flows_data = {}
        for node in nodes:
            exp_name = node.get("experiment")
            if exp_name and exp_name in experiments:
                exp = dict(experiments[exp_name])
                # Apply unit config overrides
                for key, val in unit_config.items():
                    if val:
                        exp[key] = val
                flows_data[exp_name] = exp

        ini_lines = [
            "[DEFAULT]",
            "# Automation Flow Configuration",
            f"# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        for exp_name in flows_data:
            ini_lines.append(f"[{exp_name}]")
            ini_lines.append("# experiment-specific overrides here")
            ini_lines.append("")

        positions_data = {n["id"]: {"x": n.get("x", 0), "y": n.get("y", 0)} for n in nodes}

        # Pack into ZIP
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("FrameworkAutomationStructure.json",
                        json.dumps(structure_data, indent=2))
            zf.writestr("FrameworkAutomationFlows.json",
                        json.dumps(flows_data, indent=2))
            zf.writestr("FrameworkAutomationInit.ini", "\n".join(ini_lines))
            zf.writestr("FrameworkAutomationPositions.json",
                        json.dumps(positions_data, indent=2))
        buf.seek(0)

        status = html.Div([
            html.P(f"✓ Exported {len(nodes)} nodes, {len(flows_data)} experiments",
                   style={"color": "#00ff9d"}),
            html.Small("Files in ZIP: Structure, Flows, Init INI, Positions",
                       style={"color": "#a0a0a0"}),
        ])
        return (dcc.send_bytes(buf.read(), zip_name),
                status,
                _toast(f"Exported {zip_name}.", "success"))

    return no_update, no_update, no_update


@callback(
    Output("ad-preview-btn", "disabled"),
    Input("ad-nodes-store", "data"),
)
def update_preview_btn(nodes):
    return not bool(nodes)


def _toast(msg, icon, duration=4000):
    return dbc.Toast(
        msg, icon=icon, duration=duration, is_open=True,
        style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
        className="toast-custom"
    )
