"""
Automation Designer
====================
Modern visual flow editor for DebugFramework automation flows.
Faithfully replicates PPV/gui/AutomationDesigner.AutomationFlowDesigner with a
full web-native UI.

Layout
------
  TOP TOOLBAR (always visible, compact)
    [+Add][type] | [Connect][port] | [Del Node][Del Edge][Layout] | [Validate][Save][Load][Export] | [◧][◨]

  MAIN AREA (fills viewport)
    LEFT  : dbc.Offcanvas  — Unit Configuration + Load Experiments
    CENTER: cyto canvas    — fills all remaining space
    RIGHT : collapsible panel — Experiments · Flow Nodes · Node Editor · Log

Connect Mode (click-based port wiring)
  1. Click [Connect]          → toolbar shows port selector + "Click source node →"
  2. Click SOURCE node        → node glows orange; hint → "Source: X → Click target"
  3. Click TARGET node        → edge drawn with selected port colour/label
  4. Click [Connect] again    → cancel / deactivate

Edge deletion
  Click an edge on canvas → it highlights gold and status bar shows info
  Click [Del Edge]        → removes it

Port colour ring on nodes (pie-chart sectors, not shown on Start/End terminals):
  P0=OK  (teal) · P1=Fail (red) · P2=Alt (orange) · P3=Err (purple)

All 9 original node types. Add more via _NODE_TYPES list — no other changes needed.

CaaS note: requires dash-cytoscape (pip install dash-cytoscape).
"""
import base64
import json
import io
import logging
import zipfile
import datetime
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
    path="/thr-tools/automation-designer",
    name="Automation Designer",
    title="Automation Flow Designer",
)

# ── Constants ──────────────────────────────────────────────────────────────────
ACCENT    = "#1abc9c"
_PRODUCTS = ["GNR", "CWF", "DMR"]
_PORT_LABELS = {0: "OK", 1: "Fail", 2: "Alt", 3: "Err"}
_PORT_COLORS  = {0: "#1abc9c", 1: "#e74c3c", 2: "#f39c12", 3: "#9b59b6"}
_PORT_OPTIONS = [{"label": f"P{i}:{l}", "value": str(i)} for i, l in _PORT_LABELS.items()]

# Node type registry — add new types here to expose them in the designer
_NODE_TYPES = [
    {"type": "StartNode",                    "label": "Start",           "color": "#1abc9c", "colorL": "#4ecdc4", "colorD": "#0a7a65"},
    {"type": "EndNode",                      "label": "End",             "color": "#e74c3c", "colorL": "#ff7675", "colorD": "#922b21"},
    {"type": "SingleFailFlowInstance",       "label": "SingleFail",      "color": "#3498db", "colorL": "#74b9ff", "colorD": "#1a6fa8"},
    {"type": "AllFailFlowInstance",          "label": "AllFail",         "color": "#2471a3", "colorL": "#5dade2", "colorD": "#1a4a75"},
    {"type": "MajorityFailFlowInstance",     "label": "MajorityFail",    "color": "#8e44ad", "colorL": "#bb8fce", "colorD": "#5b2c6f"},
    {"type": "AdaptiveFlowInstance",         "label": "Adaptive",        "color": "#e67e22", "colorL": "#f0a500", "colorD": "#9c5e0a"},
    {"type": "CharacterizationFlowInstance", "label": "Characterization","color": "#16a085", "colorL": "#48c9b0", "colorD": "#0a5d4d"},
    {"type": "DataCollectionFlowInstance",   "label": "DataCollection",  "color": "#27ae60", "colorL": "#6bcf7f", "colorD": "#1a6e38"},
    {"type": "AnalysisFlowInstance",         "label": "Analysis",        "color": "#c0392b", "colorL": "#ec7063", "colorD": "#7b241c"},
]
_TYPE_MAP = {n["type"]: n for n in _NODE_TYPES}
_NODE_TYPE_OPTIONS = [{"label": n["label"], "value": n["type"]} for n in _NODE_TYPES]

# Convenience styles
_IS = {
    "backgroundColor": "#0a0d14", "color": "#dde4ee",
    "border": "1px solid rgba(255,255,255,0.1)", "fontSize": "0.8rem",
}
_LS = {"color": "#6a7a8a", "fontSize": "0.73rem", "marginBottom": "2px"}


# ── Cytoscape stylesheet ───────────────────────────────────────────────────────
_STYLESHEET = [
    # Base node — gradient + shadow + port-colour ring (pie chart)
    {"selector": "node", "style": {
        "label":              "data(label)",
        "background-color":   "data(colorD)",
        "background-gradient-stop-colors":    "data(grad)",
        "background-gradient-stop-positions": "0 45 100",
        "background-gradient-direction":      "to-bottom",
        "width": 160, "height": 80,
        "shape": "roundrectangle",
        "border-width": 2, "border-color": "data(colorL)",
        "shadow-blur": 14, "shadow-color": "data(color)",
        "shadow-opacity": 0.40, "shadow-offset-x": 0, "shadow-offset-y": 5,
        "color": "#ffffff",
        "text-valign": "center", "text-halign": "center",
        "font-size": "11px",
        "font-family": "'Segoe UI', Inter, Arial, sans-serif",
        "font-weight": "600",
        "text-wrap": "wrap", "text-max-width": 148,
        # Pie-chart port indicators (small colour ring)
        "pie-size": "16%",
        "pie-1-background-color": "#1abc9c", "pie-1-background-size": 25,
        "pie-2-background-color": "#e74c3c", "pie-2-background-size": 25,
        "pie-3-background-color": "#f39c12", "pie-3-background-size": 25,
        "pie-4-background-color": "#9b59b6", "pie-4-background-size": 25,
    }},
    # Start / End — no port ring, thicker border
    {"selector": "node[type='StartNode'], node[type='EndNode']", "style": {
        "pie-size": "0%",
        "border-width": 3,
    }},
    # Selected
    {"selector": "node:selected", "style": {
        "border-color": "#f1c40f", "border-width": 4,
        "overlay-color": "#f1c40f", "overlay-padding": 5, "overlay-opacity": 0.1,
    }},
    # Pending source in connect-mode (orange glow)
    {"selector": "node.source-pending", "style": {
        "border-color": "#f39c12", "border-width": 4,
        "shadow-color": "#f39c12", "shadow-blur": 32, "shadow-opacity": 0.9,
    }},
    # Edge
    {"selector": "edge", "style": {
        "curve-style": "unbundled-bezier",
        "target-arrow-shape": "triangle",
        "arrow-scale": 1.5,
        "line-color": "data(edgeColor)",
        "target-arrow-color": "data(edgeColor)",
        "width": 2.5,
        "label": "data(portLabel)",
        "font-size": "9px", "color": "#dde4ee",
        "text-background-color": "#06080f", "text-background-opacity": 0.88,
        "text-background-padding": "3px", "text-background-shape": "roundrectangle",
        "edge-text-rotation": "autorotate",
    }},
    # Selected edge — gold highlight
    {"selector": "edge:selected", "style": {
        "line-color": "#f1c40f", "target-arrow-color": "#f1c40f",
        "width": 4,
        "overlay-color": "#f1c40f", "overlay-opacity": 0.22, "overlay-padding": 4,
    }},
]


# ── Element builders ───────────────────────────────────────────────────────────
def _node_elem(node_id, node_type, name, exp_name, x, y, pending=False):
    info = _TYPE_MAP.get(node_type,
                         {"label": node_type, "color": "#555", "colorL": "#777", "colorD": "#333"})
    lines = [name or info["label"]]
    if exp_name:
        short = exp_name[:18] + ("\u2026" if len(exp_name) > 18 else "")
        lines.append(f"[{short}]")
    return {
        "data": {
            "id":    node_id,
            "label": "\n".join(lines),
            "type":  node_type,
            "name":  name or node_id,
            "experiment": exp_name or "",
            "color":  info["color"],
            "colorD": info.get("colorD", info["color"]),
            "colorL": info.get("colorL", info["color"]),
            "grad":   (f"{info.get('colorL', info['color'])} "
                       f"{info['color']} "
                       f"{info.get('colorD', info['color'])}"),
        },
        "position": {"x": x, "y": y},
        "classes":  "source-pending" if pending else "",
        "grabbable": True,
    }


def _build_elements(nodes_store, edges_store, pending_source=None):
    elems = []
    for nid, nd in (nodes_store or {}).items():
        elems.append(_node_elem(
            nid, nd["type"], nd.get("name", ""), nd.get("experiment", ""),
            nd.get("x", 200), nd.get("y", 200),
            pending=(nid == pending_source),
        ))
    for edge in (edges_store or []):
        port = int(edge.get("port", 0))
        elems.append({"data": {
            "id":        f"e_{edge['source']}_{edge['target']}_{port}",
            "source":    edge["source"],
            "target":    edge["target"],
            "port":      port,
            "portLabel": f"P{port}:{_PORT_LABELS.get(port, '')}",
            "edgeColor": _PORT_COLORS.get(port, "#aaa"),
        }})
    return elems


# ── Layout helpers ─────────────────────────────────────────────────────────────
def _btn(children, bid, **kw):
    extra = kw.pop("extra_style", {})
    return dbc.Button(children, id=bid, size="sm",
                      style={"height": "30px", "padding": "0 9px",
                             "fontSize": "0.77rem", **extra},
                      **kw)


def _sep():
    return html.Span(style={"width": "1px", "height": "22px", "alignSelf": "center",
                             "backgroundColor": "rgba(255,255,255,0.13)",
                             "margin": "0 3px"})


def _toolbar():
    return html.Div(id="ad-toolbar", style={
        "display": "flex", "alignItems": "center", "gap": "3px",
        "padding": "5px 8px", "flexShrink": 0,
        "backgroundColor": "#10131c",
        "borderBottom": "1px solid rgba(26,188,156,0.25)",
    }, children=[
        # Title
        html.Span([
            html.I(className="bi bi-diagram-3 me-1", style={"color": ACCENT}),
            html.Span("Automation Designer",
                      style={"color": ACCENT, "fontWeight": "700", "fontSize": "0.85rem"}),
        ], style={"marginRight": "5px", "whiteSpace": "nowrap"}),
        _sep(),
        # Add node
        dbc.Select(id="ad-node-type-sel", options=_NODE_TYPE_OPTIONS,
                   value="SingleFailFlowInstance",
                   style={**_IS, "width": "140px", "height": "30px", "padding": "1px 4px"}),
        _btn([html.I(className="bi bi-plus-lg")], "ad-add-node-btn",
             extra_style={"borderColor": ACCENT, "color": ACCENT,
                     "backgroundColor": "transparent", "width": "30px"}),
        _sep(),
        # Connect mode
        _btn([html.I(className="bi bi-share-fill me-1"), "Connect"],
             "ad-connect-toggle-btn",
             extra_style={"borderColor": "#3498db", "color": "#3498db",
                     "backgroundColor": "transparent"}),
        dbc.Select(id="ad-conn-port", options=_PORT_OPTIONS, value="0",
                   style={**_IS, "width": "102px", "height": "30px",
                          "padding": "1px 4px", "display": "none"}),
        html.Span(id="ad-connect-hint",
                  style={"color": "#5a6a7a", "fontSize": "0.72rem",
                         "whiteSpace": "nowrap", "lineHeight": "30px"}),
        _sep(),
        # Actions
        _btn([html.I(className="bi bi-trash3 me-1"), "Del Node"],
             "ad-del-node-btn", color="danger", outline=True),
        _btn([html.I(className="bi bi-x-circle me-1"), "Del Edge"],
             "ad-del-edge-btn",
             extra_style={"borderColor": "#c0392b", "color": "#c0392b",
                     "backgroundColor": "transparent"}),
        _sep(),
        _btn([html.I(className="bi bi-grid-1x2 me-1"), "Layout"],
             "ad-layout-btn", color="secondary", outline=True),
        html.Div(style={"flex": "1"}),  # spacer
        # I/O
        _btn([html.I(className="bi bi-check-circle me-1"), "Validate"],
             "ad-validate-btn", color="secondary", outline=True),
        _btn([html.I(className="bi bi-floppy me-1"), "Save"],
             "ad-save-btn",
             extra_style={"borderColor": ACCENT, "color": ACCENT,
                     "backgroundColor": "transparent"}),
        dcc.Upload(id="ad-load-upload", multiple=False, children=dbc.Button(
            [html.I(className="bi bi-folder2-open me-1"), "Load"],
            size="sm",
            style={"height": "30px", "padding": "0 9px", "fontSize": "0.77rem",
                   "borderColor": "#7a8a9a", "color": "#7a8a9a",
                   "backgroundColor": "transparent"},
            outline=True,
        )),
        _btn([html.I(className="bi bi-file-zip me-1"), "Export ZIP"],
             "ad-export-btn",
             extra_style={"borderColor": "#f39c12", "color": "#f39c12",
                     "backgroundColor": "transparent"}),
        _sep(),
        # Panel toggles
        dbc.Button(html.I(className="bi bi-layout-sidebar-inset"),
                   id="ad-toggle-left-btn", size="sm", color="secondary", outline=True,
                   title="Unit Config / Load Experiments",
                   style={"height": "30px", "width": "30px", "padding": "0"}),
        dbc.Button(html.I(className="bi bi-layout-sidebar-inset-reverse"),
                   id="ad-toggle-right-btn", size="sm", color="secondary", outline=True,
                   title="Toggle right panel",
                   style={"height": "30px", "width": "30px", "padding": "0"}),
    ])


def _left_offcanvas():
    def _fld(lbl, fid, ph):
        return html.Div([
            html.Label(lbl, style=_LS),
            dbc.Input(id=fid, type="text", placeholder=ph, className="mb-2",
                      style={**_IS, "height": "28px"}),
        ])
    return dbc.Offcanvas(
        id="ad-left-offcanvas",
        title=html.Span([
            html.I(className="bi bi-cpu me-2", style={"color": ACCENT}),
            "Unit Configuration",
        ], style={"color": ACCENT, "fontWeight": "700"}),
        is_open=False, placement="start", backdrop=False, scrollable=True,
        style={"backgroundColor": "#10131c", "color": "#dde4ee",
               "width": "270px", "borderRight": "1px solid rgba(26,188,156,0.2)"},
        children=[
            html.Div(style={"padding": "8px 12px"}, children=[
                _fld("Visual ID",  "ad-vid",    "75EH348100130"),
                _fld("Bucket",     "ad-bucket", "N/A"),
                _fld("COM Port",   "ad-com",    "COM3"),
                _fld("IP Address", "ad-ip",     "192.168.1.100"),
                dbc.Checklist(
                    id="ad-unit-flags",
                    options=[{"label": "600W Unit",  "value": "600w"},
                             {"label": "Check Core", "value": "check_core"}],
                    value=[],
                    inputStyle={"marginRight": "6px"},
                    labelStyle={"color": "#dde4ee", "fontSize": "0.82rem"},
                ),
            ]),
            html.Hr(style={"borderColor": "rgba(255,255,255,0.1)", "margin": "4px 0"}),
            html.Div(style={"padding": "4px 12px 12px"}, children=[
                html.Div("Load Experiments",
                         style={"color": ACCENT, "fontWeight": "700",
                                "fontSize": "0.84rem", "marginBottom": "8px"}),
                html.Label("Product", style=_LS),
                dbc.Select(id="ad-product",
                           options=[{"label": p, "value": p} for p in _PRODUCTS],
                           value="GNR", className="mb-2",
                           style={**_IS, "height": "28px"}),
                dcc.Upload(
                    id="ad-exp-upload", multiple=False,
                    children=html.Div([
                        html.I(className="bi bi-cloud-upload",
                               style={"color": ACCENT, "fontSize": "1.3rem",
                                      "display": "block", "marginBottom": "3px"}),
                        html.Span("Browse or drop file", style={"color": ACCENT}),
                        html.Br(),
                        html.Small(".json \xb7 .tpl \xb7 .xlsx",
                                   style={"color": "#4a5a6a"}),
                    ], style={"textAlign": "center", "padding": "10px 0"}),
                    style={"border": f"1px dashed {ACCENT}", "borderRadius": "6px",
                           "cursor": "pointer",
                           "backgroundColor": "rgba(26,188,156,0.03)"},
                ),
                html.Div(id="ad-exp-label",
                         style={"color": "#5a6a7a", "fontSize": "0.72rem",
                                "marginTop": "4px"}),
            ]),
        ],
    )


def _canvas_area():
    return html.Div(style={
        "flex": "1", "minWidth": 0,
        "display": "flex", "flexDirection": "column", "overflow": "hidden",
    }, children=[
        # Mini info-bar
        html.Div(style={
            "display": "flex", "alignItems": "center", "gap": "8px",
            "padding": "2px 10px", "flexShrink": 0,
            "backgroundColor": "#0a0d15",
            "borderBottom": "1px solid rgba(255,255,255,0.05)",
        }, children=[
            html.Span(id="ad-canvas-stats", children="0 nodes \xb7 0 edges",
                      style={"color": "#3a4a5a", "fontSize": "0.7rem"}),
            html.Span("\xb7", style={"color": "#1a2a3a", "fontSize": "0.7rem"}),
            html.Span(id="ad-canvas-hint2",
                      children="Click to select \xb7 Drag to move \xb7 Connect Mode to wire",
                      style={"color": "#3a4a5a", "fontSize": "0.7rem"}),
            html.Div(style={"flex": "1"}),
            dbc.ButtonGroup([
                dbc.Button(html.I(className="bi bi-zoom-in"),   id="ad-zoom-in",  size="sm",
                           outline=True,
                           style={"border": "1px solid #1a2a3a", "color": "#4a5a6a",
                                  "padding": "1px 5px", "backgroundColor": "transparent"}),
                dbc.Button(html.I(className="bi bi-zoom-out"),  id="ad-zoom-out", size="sm",
                           outline=True,
                           style={"border": "1px solid #1a2a3a", "color": "#4a5a6a",
                                  "padding": "1px 5px", "backgroundColor": "transparent"}),
                dbc.Button(html.I(className="bi bi-fullscreen"), id="ad-fit-btn",  size="sm",
                           outline=True,
                           style={"border": "1px solid #1a2a3a", "color": "#4a5a6a",
                                  "padding": "1px 5px", "backgroundColor": "transparent"}),
            ]),
        ]),
        cyto.Cytoscape(
            id="ad-canvas",
            elements=[],
            layout={"name": "preset"},
            style={"flex": "1", "width": "100%", "minHeight": 0,
                   "backgroundColor": "#06080f"},
            stylesheet=_STYLESHEET,
            boxSelectionEnabled=True,
            autoRefreshLayout=False,
            userPanningEnabled=True,
            userZoomingEnabled=True,
            minZoom=0.15, maxZoom=4,
            responsive=True,
        ),
        html.Div(id="ad-statusbar",
                 style={"backgroundColor": "#08090f",
                        "borderTop": "1px solid rgba(255,255,255,0.04)",
                        "padding": "2px 10px", "fontSize": "0.69rem",
                        "color": "#3a4a5a", "flexShrink": 0},
                 children="Ready."),
    ])


def _right_panel_content():
    def _card(title, body_id, body_children, max_h=None):
        return html.Div([
            html.Div(title, style={
                "color": ACCENT, "fontSize": "0.77rem", "fontWeight": "700",
                "padding": "6px 10px 4px",
                "borderBottom": "1px solid rgba(255,255,255,0.07)",
            }),
            html.Div(id=body_id,
                     style={"padding": "6px 10px",
                            **({"maxHeight": max_h, "overflowY": "auto"}
                               if max_h else {})},
                     children=body_children),
        ], style={"borderBottom": "1px solid rgba(255,255,255,0.08)"})

    return [
        _card("Experiments", "ad-exp-list",
              [html.Span("No experiments loaded.",
                         style={"color": "#3a4a5a", "fontSize": "0.74rem"})],
              max_h="90px"),
        _card("Flow Nodes", "ad-node-list",
              [html.Span("No nodes.",
                         style={"color": "#3a4a5a", "fontSize": "0.74rem"})],
              max_h="210px"),
        _card("Node Editor", "ad-node-editor",
              [html.Span("Select a node on the canvas.",
                         style={"color": "#3a4a5a", "fontSize": "0.74rem"})]),
        # Flow file
        html.Div(style={"padding": "6px 10px",
                        "borderBottom": "1px solid rgba(255,255,255,0.08)"}, children=[
            html.Div("Flow File", style={"color": ACCENT, "fontSize": "0.77rem",
                                          "fontWeight": "700", "marginBottom": "5px"}),
            dbc.Input(id="ad-save-name", placeholder="flow_design.json", type="text",
                      className="mb-1",
                      style={**_IS, "fontSize": "0.75rem", "height": "26px"}),
            html.Div(id="ad-export-status",
                     style={"color": "#5a6a7a", "fontSize": "0.7rem", "marginTop": "2px"}),
        ]),
        # Log
        html.Div(style={"display": "flex", "flexDirection": "column", "flex": "1"}, children=[
            html.Div("Log", style={"color": ACCENT, "fontSize": "0.77rem",
                                   "fontWeight": "700", "padding": "6px 10px 4px",
                                   "borderBottom": "1px solid rgba(255,255,255,0.07)"}),
            dbc.Textarea(
                id="ad-log", value="Automation Designer ready.\n", readOnly=True,
                style={"backgroundColor": "#04050a", "color": "#7a9a88",
                       "fontFamily": "Consolas, 'Courier New', monospace",
                       "fontSize": "0.69rem", "border": "none", "resize": "none",
                       "flex": "1", "padding": "6px 10px", "minHeight": "100px"},
            ),
        ]),
    ]


# ── Main layout ────────────────────────────────────────────────────────────────
def _cyto_fallback():
    return dbc.Container(fluid=True, className="pb-4", children=[
        dbc.Alert([
            html.Strong("dash-cytoscape is not installed. "),
            "Run: ", html.Code("pip install dash-cytoscape"), " then restart.",
        ], color="warning", className="mt-4"),
    ])


def layout():
    if not _CYTO_AVAILABLE:
        return _cyto_fallback()

    return html.Div(style={
        "display": "flex", "flexDirection": "column",
        "height": "calc(100vh - 58px)",
        "overflow": "hidden",
        "backgroundColor": "#06080f",
    }, children=[
        dcc.Download(id="ad-download"),
        dcc.Store(id="ad-nodes-store",         data={}),
        dcc.Store(id="ad-edges-store",         data=[]),
        dcc.Store(id="ad-experiments-store",   data={}),
        dcc.Store(id="ad-counter-store",       data=1),
        dcc.Store(id="ad-result-store",        data=None),
        dcc.Store(id="ad-selected-node",       data=None),
        dcc.Store(id="ad-selected-edge-store", data=None),
        # connect-mode dict: {active, pending, port}
        dcc.Store(id="ad-connect-mode",
                  data={"active": False, "pending": None, "port": "0"}),
        dcc.Store(id="ad-right-open", data=True),

        _toolbar(),

        html.Div(style={"display": "flex", "flex": "1",
                        "overflow": "hidden", "minHeight": 0}, children=[
            _left_offcanvas(),
            _canvas_area(),
            html.Div(id="ad-right-panel",
                     style={"width": "252px", "minWidth": "252px",
                            "display": "flex", "flexDirection": "column",
                            "overflow": "hidden",
                            "backgroundColor": "#0c0f18",
                            "borderLeft": "1px solid rgba(26,188,156,0.15)"},
                     children=_right_panel_content()),
        ]),

        html.Div(id="ad-toast"),
    ])


# ══════════════════════════════════════════════════════════════════════════════
#  Callbacks
# ══════════════════════════════════════════════════════════════════════════════

@callback(
    Output("ad-left-offcanvas", "is_open"),
    Input("ad-toggle-left-btn", "n_clicks"),
    State("ad-left-offcanvas", "is_open"),
    prevent_initial_call=True,
)
def toggle_left(n, is_open):
    return not is_open


@callback(
    Output("ad-right-panel", "style"),
    Output("ad-right-open", "data"),
    Input("ad-toggle-right-btn", "n_clicks"),
    State("ad-right-open", "data"),
    prevent_initial_call=True,
)
def toggle_right(n, is_open):
    now = not is_open
    return ({
        "width": "252px", "minWidth": "252px",
        "display": "flex" if now else "none",
        "flexDirection": "column", "overflow": "hidden",
        "backgroundColor": "#0c0f18",
        "borderLeft": "1px solid rgba(26,188,156,0.15)",
    }, now)


@callback(
    Output("ad-connect-mode",        "data"),
    Output("ad-connect-toggle-btn",  "style"),
    Output("ad-conn-port",           "style"),
    Output("ad-connect-hint",        "children"),
    Input("ad-connect-toggle-btn",   "n_clicks"),
    State("ad-connect-mode",         "data"),
    prevent_initial_call=True,
)
def toggle_connect(n, mode):
    active = mode.get("active", False)
    if active:
        new_mode   = {**mode, "active": False, "pending": None}
        btn_style  = {"height": "30px", "padding": "0 9px", "fontSize": "0.77rem",
                      "borderColor": "#3498db", "color": "#3498db",
                      "backgroundColor": "transparent"}
        port_style = {**_IS, "width": "102px", "height": "30px",
                      "padding": "1px 4px", "display": "none"}
        hint = ""
    else:
        new_mode   = {**mode, "active": True, "pending": None}
        btn_style  = {"height": "30px", "padding": "0 9px", "fontSize": "0.77rem",
                      "borderColor": "#f39c12", "color": "#f39c12",
                      "backgroundColor": "rgba(243,156,18,0.12)"}
        port_style = {**_IS, "width": "102px", "height": "30px", "padding": "1px 4px"}
        hint = "Click source node \u2192"
    return new_mode, btn_style, port_style, hint


@callback(
    Output("ad-connect-mode", "data", allow_duplicate=True),
    Input("ad-conn-port", "value"),
    State("ad-connect-mode", "data"),
    prevent_initial_call=True,
)
def sync_port(val, mode):
    return {**mode, "port": val or "0"}


@callback(
    Output("ad-experiments-store", "data"),
    Output("ad-exp-label",         "children"),
    Output("ad-exp-list",          "children"),
    Output("ad-toast",             "children"),
    Input("ad-exp-upload",         "contents"),
    State("ad-exp-upload",         "filename"),
    prevent_initial_call=True,
)
def load_experiments(content, fname):
    if not content:
        return no_update, no_update, no_update, no_update
    try:
        if "," not in content:
            return no_update, "Invalid file format.", no_update, _toast("Invalid file.", "danger")
        _, data = content.split(",", 1)
        raw = base64.b64decode(data)
        experiments = {}
        if fname and fname.endswith(".xlsx"):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
            for ws in wb.worksheets:
                for tbl in ws.tables.values():
                    rng = ws[tbl.ref]
                    headers = [c.value for c in rng[0]]
                    for row in rng[1:]:
                        entry = {str(headers[i]): (r.value or "")
                                 for i, r in enumerate(row)}
                        k = entry.get("Experiment",
                            entry.get("Test Name",
                            entry.get("Name", f"Exp_{len(experiments)+1}")))
                        experiments[str(k)] = entry
        else:
            loaded = json.loads(raw.decode("utf-8"))
            if isinstance(loaded, list):
                for e in loaded:
                    k = e.get("Experiment",
                        e.get("Test Name",
                        e.get("Name", f"Exp_{len(experiments)+1}")))
                    experiments[str(k)] = e
            elif isinstance(loaded, dict):
                if "nodes" in loaded:
                    return (no_update, "\u26a0 Looks like a flow file \u2014 use Load.",
                            no_update,
                            _toast("That's a flow file. Use 'Load' button.", "warning"))
                for k, v in loaded.items():
                    experiments[k] = v if isinstance(v, dict) else {"value": v}
        if not experiments:
            return (no_update, "No experiments found.", no_update,
                    _toast("No experiments found.", "warning"))
        items = [
            html.Div(f"\u2022 {n}",
                     style={"color": "#c0d0e0", "fontSize": "0.74rem",
                            "marginBottom": "1px"})
            for n in list(experiments.keys())[:40]
        ]
        if len(experiments) > 40:
            items.append(html.Div(f"\u2026{len(experiments)-40} more",
                                  style={"color": "#4a5a6a", "fontSize": "0.7rem"}))
        return (experiments,
                f"\u2713 {fname} ({len(experiments)} experiments)",
                items,
                _toast(f"Loaded {len(experiments)} experiments.", "success", 2000))
    except Exception as exc:
        logger.exception("Exp load error")
        return no_update, f"Error: {exc}", no_update, _toast(str(exc), "danger")


@callback(
    Output("ad-selected-edge-store", "data"),
    Output("ad-statusbar",           "children"),
    Input("ad-canvas",               "tapEdgeData"),
    prevent_initial_call=True,
)
def select_edge(edge_data):
    if not edge_data:
        return no_update, no_update
    port  = int(edge_data.get("port", 0))
    label = _PORT_LABELS.get(port, "?")
    status = (f"Edge: {edge_data.get('source')} \u2192 {edge_data.get('target')}  "
              f"(P{port}:{label})  \u2014  click \u2018Del Edge\u2019 to remove")
    return edge_data, status


@callback(
    Output("ad-nodes-store",   "data"),
    Output("ad-edges-store",   "data"),
    Output("ad-counter-store", "data"),
    Output("ad-canvas",        "elements"),
    Output("ad-node-list",     "children"),
    Output("ad-connect-mode",  "data",     allow_duplicate=True),
    Output("ad-connect-hint",  "children", allow_duplicate=True),
    Output("ad-canvas-stats",  "children"),
    Output("ad-log",           "value"),
    Output("ad-statusbar",     "children", allow_duplicate=True),
    Output("ad-toast",         "children", allow_duplicate=True),
    Input("ad-add-node-btn",   "n_clicks"),
    Input("ad-del-node-btn",   "n_clicks"),
    Input("ad-del-edge-btn",   "n_clicks"),
    Input("ad-layout-btn",     "n_clicks"),
    Input("ad-load-upload",    "contents"),
    Input("ad-canvas",         "tapNodeData"),
    Input("ad-canvas",         "elements"),
    State("ad-node-type-sel",  "value"),
    State("ad-nodes-store",    "data"),
    State("ad-edges-store",    "data"),
    State("ad-counter-store",  "data"),
    State("ad-canvas",         "selectedNodeData"),
    State("ad-connect-mode",   "data"),
    State("ad-selected-edge-store", "data"),
    State("ad-load-upload",    "filename"),
    State("ad-log",            "value"),
    prevent_initial_call=True,
)
def manage_canvas(add_c, del_c, del_edge_c, layout_c, load_content,
                  tap_node, canvas_elements,
                  node_type, nodes, edges, counter,
                  selected_nodes, connect_mode, sel_edge,
                  load_fname, log_val):
    trigger = ctx.triggered_id
    nodes   = dict(nodes   or {})
    edges   = list(edges   or [])
    log     = log_val or ""
    cmode   = dict(connect_mode or {"active": False, "pending": None, "port": "0"})
    hint    = no_update
    status  = no_update

    def _log(msg):
        nonlocal log
        ts  = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
        log = f"[{ts}] {msg}\n" + log

    def _stats():
        return f"{len(nodes)} nodes \xb7 {len(edges)} edges"

    # ── Position update from drag — never rebuild elements ──
    if trigger == "ad-canvas" and canvas_elements and tap_node is None:
        for el in canvas_elements:
            if "position" in el and "data" in el:
                nid = el["data"].get("id")
                if nid and nid in nodes:
                    nodes[nid]["x"] = el["position"]["x"]
                    nodes[nid]["y"] = el["position"]["y"]
        return (nodes, edges, counter, no_update, no_update,
                cmode, hint, _stats(), log, status, no_update)

    # ── Add node ──
    if trigger == "ad-add-node-btn":
        nid  = f"NODE_{counter:03d}"
        counter += 1
        n    = len(nodes)
        x, y = 160 + (n % 4) * 190, 160 + (n // 4) * 150
        nodes[nid] = {"id": nid, "name": nid, "type": node_type,
                      "x": x, "y": y, "experiment": "", "connections": {}}
        _log(f"Added {_TYPE_MAP.get(node_type, {}).get('label', node_type)}: {nid}")
        elems = _build_elements(nodes, edges, cmode.get("pending"))
        return (nodes, edges, counter, elems, _node_list_html(nodes),
                cmode, hint, _stats(), log, f"Added {nid}.",
                _toast(f"Added {nid}", "success", 1500))

    # ── Delete node ──
    if trigger == "ad-del-node-btn":
        if not selected_nodes:
            return (no_update, no_update, no_update, no_update, no_update,
                    cmode, hint, no_update, log, "Select a node first.",
                    _toast("Select a node first.", "warning"))
        for nd in selected_nodes:
            nid = nd.get("id")
            if nid in nodes:
                del nodes[nid]
                edges = [e for e in edges
                         if e.get("source") != nid and e.get("target") != nid]
                _log(f"Deleted {nid}")
        elems = _build_elements(nodes, edges, cmode.get("pending"))
        return (nodes, edges, counter, elems, _node_list_html(nodes),
                cmode, hint, _stats(), log, "Node(s) deleted.",
                _toast("Deleted.", "info", 1500))

    # ── Delete selected edge ──
    if trigger == "ad-del-edge-btn":
        if not sel_edge:
            return (no_update, no_update, no_update, no_update, no_update,
                    cmode, hint, no_update, log, "Click an edge first.",
                    _toast("Click an edge on the canvas first.", "warning"))
        src  = sel_edge.get("source")
        tgt  = sel_edge.get("target")
        port = int(sel_edge.get("port", -1))
        before = len(edges)
        edges  = [e for e in edges
                  if not (e["source"] == src and e["target"] == tgt
                          and int(e.get("port", -1)) == port)]
        if src in nodes and len(edges) < before:
            nodes[src].get("connections", {}).pop(str(port), None)
            _log(f"Removed edge {src}\u2192{tgt} P{port}")
        elems = _build_elements(nodes, edges, cmode.get("pending"))
        return (nodes, edges, counter, elems, _node_list_html(nodes),
                cmode, hint, _stats(), log, "Edge removed.",
                _toast("Edge removed.", "info", 1500))

    # ── Auto layout ──
    if trigger == "ad-layout-btn":
        nodes = _auto_layout(nodes, edges)
        _log("Applied auto layout")
        elems = _build_elements(nodes, edges, cmode.get("pending"))
        return (nodes, edges, counter, elems, _node_list_html(nodes),
                cmode, hint, _stats(), log, "Auto layout applied.", no_update)

    # ── Load flow design ──
    if trigger == "ad-load-upload" and load_content:
        try:
            if "," not in load_content:
                return (no_update, no_update, no_update, no_update, no_update,
                        cmode, hint, no_update, log, "Invalid file format.",
                        _toast("Invalid file format.", "danger"))
            _, data  = load_content.split(",", 1)
            design   = json.loads(base64.b64decode(data).decode("utf-8"))
            new_nodes, new_edges, new_ctr = {}, [], 1
            for nid, nd in design.get("nodes", {}).items():
                new_nodes[nid] = nd
                m = re.search(r"(\d+)", nid)
                if m:
                    new_ctr = max(new_ctr, int(m.group(1)) + 1)
                for prt, tgt in nd.get("connections", {}).items():
                    new_edges.append({"source": nid, "target": tgt, "port": int(prt)})
            elems = _build_elements(new_nodes, new_edges)
            _log(f"Loaded: {load_fname} ({len(new_nodes)} nodes)")
            return (new_nodes, new_edges, new_ctr, elems, _node_list_html(new_nodes),
                    cmode, hint,
                    f"{len(new_nodes)} nodes \xb7 {len(new_edges)} edges",
                    log, f"Flow loaded: {load_fname}",
                    _toast(f"Loaded: {load_fname}", "success"))
        except Exception as exc:
            _log(f"Load error: {exc}")
            return (no_update, no_update, no_update, no_update, no_update,
                    cmode, hint, no_update, log, f"Load error: {exc}",
                    _toast(str(exc), "danger"))

    # ── Node tap ──
    if trigger == "ad-canvas" and tap_node:
        nid = tap_node.get("id")
        # If connect mode is not active — plain selection info
        if not cmode.get("active"):
            return (no_update, no_update, no_update, no_update, no_update,
                    cmode, hint, no_update, log,
                    f"Selected: {nid}  ({tap_node.get('type', '')})",
                    no_update)

        # Connect mode — first click sets source
        if cmode.get("pending") is None:
            new_cmode = {**cmode, "pending": nid}
            hint      = f"Source: {nid} \u2192 Click target"
            elems     = _build_elements(nodes, edges, pending_source=nid)
            _log(f"Connect source: {nid}")
            return (nodes, edges, counter, elems, no_update,
                    new_cmode, hint, _stats(), log,
                    f"Connect mode: source = {nid}. Now click target.",
                    _toast(f"Source: {nid}. Click target node.", "info", 3000))

        # Connect mode — second click creates edge
        src_id   = cmode["pending"]
        port_num = int(cmode.get("port", "0"))
        if nid == src_id:
            new_cmode = {**cmode, "pending": None}
            hint      = "Click source node \u2192"
            elems     = _build_elements(nodes, edges)
            return (nodes, edges, counter, elems, no_update,
                    new_cmode, hint, _stats(), log, "Cancelled (same node).",
                    no_update)
        # Deduplicate then add
        edges = [e for e in edges
                 if not (e["source"] == src_id and e["target"] == nid
                         and int(e.get("port", -1)) == port_num)]
        edges.append({"source": src_id, "target": nid, "port": port_num})
        nodes[src_id].setdefault("connections", {})[str(port_num)] = nid
        new_cmode = {**cmode, "pending": None}
        hint      = "Click source node \u2192"
        elems     = _build_elements(nodes, edges)
        lbl       = _PORT_LABELS.get(port_num, "")
        _log(f"Connected {src_id}\u2192{nid} P{port_num}:{lbl}")
        return (nodes, edges, counter, elems, _node_list_html(nodes),
                new_cmode, hint, _stats(), log,
                f"Connected {src_id} \u2192 {nid} (P{port_num}:{lbl})",
                _toast(f"{src_id} \u2192 {nid}", "success", 1500))

    return (no_update, no_update, no_update, no_update, no_update,
            cmode, hint, no_update, log, status, no_update)


@callback(
    Output("ad-node-editor",   "children"),
    Output("ad-selected-node", "data"),
    Input("ad-canvas",         "tapNodeData"),
    State("ad-nodes-store",    "data"),
    State("ad-experiments-store","data"),
    prevent_initial_call=True,
)
def show_node_editor(tap, nodes, experiments):
    if not tap:
        return no_update, no_update
    nid  = tap.get("id")
    nd   = (nodes or {}).get(nid)
    if not nd:
        return no_update, no_update
    info     = _TYPE_MAP.get(nd["type"], {"label": nd["type"], "color": "#555"})
    exp_opts = [{"label": "\u2014 none \u2014", "value": ""}] + \
               [{"label": k, "value": k} for k in (experiments or {}).keys()]
    conn_rows = []
    for p, t in nd.get("connections", {}).items():
        p = int(p)
        conn_rows.append(html.Span(
            f"P{p}:{_PORT_LABELS.get(p,'?')} \u2192 {t}  ",
            style={"color": _PORT_COLORS.get(p, "#aaa"),
                   "fontSize": "0.7rem", "marginRight": "4px"},
        ))
    return html.Div([
        html.Span(nid, style={"color": info["color"], "fontWeight": "700",
                               "fontSize": "0.8rem"}),
        html.Span(f"  {info['label']}",
                  style={"color": "#4a5a6a", "fontSize": "0.74rem"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)", "margin": "4px 0"}),
        html.Label("Name", style=_LS),
        dbc.Input(id="ad-editor-name", value=nd.get("name", ""), type="text",
                  className="mb-1",
                  style={**_IS, "height": "26px", "fontSize": "0.78rem"}),
        html.Label("Experiment", style=_LS),
        dbc.Select(id="ad-editor-exp", options=exp_opts,
                   value=nd.get("experiment", ""), className="mb-1",
                   style={**_IS, "height": "26px", "fontSize": "0.78rem"}),
        html.Div(conn_rows or [html.Span("No connections.",
                                          style={"color": "#3a4a5a",
                                                 "fontSize": "0.7rem"})],
                 style={"marginBottom": "4px"}),
        dbc.Button([html.I(className="bi bi-check me-1"), "Apply"],
                   id="ad-editor-apply", size="sm", outline=True,
                   style={"borderColor": ACCENT, "color": ACCENT,
                          "backgroundColor": "transparent",
                          "width": "100%", "height": "26px",
                          "fontSize": "0.77rem"}),
    ]), nid


@callback(
    Output("ad-nodes-store",  "data",     allow_duplicate=True),
    Output("ad-canvas",       "elements", allow_duplicate=True),
    Output("ad-node-list",    "children", allow_duplicate=True),
    Output("ad-toast",        "children", allow_duplicate=True),
    Input("ad-editor-apply",  "n_clicks"),
    State("ad-selected-node", "data"),
    State("ad-editor-name",   "value"),
    State("ad-editor-exp",    "value"),
    State("ad-nodes-store",   "data"),
    State("ad-edges-store",   "data"),
    State("ad-connect-mode",  "data"),
    prevent_initial_call=True,
)
def apply_edit(n, node_id, name, exp, nodes, edges, cmode):
    if not node_id or node_id not in (nodes or {}):
        return no_update, no_update, no_update, _toast("No node selected.", "warning")
    nodes[node_id]["name"]       = name or node_id
    nodes[node_id]["experiment"] = exp or ""
    elems = _build_elements(nodes, edges or [], (cmode or {}).get("pending"))
    return nodes, elems, _node_list_html(nodes), _toast(f"{node_id} updated.", "success", 1500)


@callback(
    Output("ad-download",      "data"),
    Output("ad-export-status", "children"),
    Output("ad-toast",         "children", allow_duplicate=True),
    Output("ad-result-store",  "data"),
    Input("ad-save-btn",       "n_clicks"),
    Input("ad-export-btn",     "n_clicks"),
    Input("ad-validate-btn",   "n_clicks"),
    State("ad-nodes-store",    "data"),
    State("ad-edges-store",    "data"),
    State("ad-experiments-store","data"),
    State("ad-vid",            "value"),
    State("ad-bucket",         "value"),
    State("ad-com",            "value"),
    State("ad-ip",             "value"),
    State("ad-unit-flags",     "value"),
    State("ad-save-name",      "value"),
    prevent_initial_call=True,
)
def save_or_export(save_c, export_c, validate_c,
                   nodes, edges, experiments,
                   vid, bucket, com, ip, flags, save_name):
    trigger = ctx.triggered_id
    nodes   = nodes   or {}
    edges   = edges   or []

    if trigger == "ad-validate-btn":
        errs, _ = _validate(nodes, edges, experiments or {})
        if errs:
            msg = html.Div([html.P(f"\u274c {e}",
                                   style={"color": "#e74c3c",
                                          "fontSize": "0.74rem", "margin": "1px 0"})
                            for e in errs])
            return no_update, msg, _toast(f"{len(errs)} error(s).", "danger"), no_update
        return (no_update,
                html.P("\u2713 Flow is valid!", style={"color": ACCENT, "fontSize": "0.74rem"}),
                _toast("Flow valid.", "success", 2000), no_update)

    if trigger == "ad-save-btn":
        if not nodes:
            return no_update, no_update, _toast("Nothing to save.", "warning"), no_update
        design = {
            "nodes": nodes, "edges": edges,
            "unit_config": {
                "Visual ID":  vid or "",
                "Bucket":     bucket or "",
                "COM Port":   com or "",
                "IP Address": ip or "",
                "600W Unit":  "600w"       in (flags or []),
                "Check Core": "check_core" in (flags or []),
            },
        }
        fname = (save_name or "flow_design.json")
        if not fname.endswith(".json"):
            fname += ".json"
        return (dcc.send_string(json.dumps(design, indent=2), fname),
                f"\u2713 Saved: {fname}",
                _toast(f"Saved: {fname}", "success"), None)

    if trigger == "ad-export-btn":
        errs, _ = _validate(nodes, edges, experiments or {})
        if errs:
            return (no_update, no_update,
                    _toast("Fix validation errors first.", "danger"), no_update)
        unit_cfg = {
            "Visual ID":  vid or "",
            "Bucket":     bucket or "",
            "COM Port":   com or "",
            "IP Address": ip or "",
            "600W Unit":  "600w"       in (flags or []),
            "Check Core": "check_core" in (flags or []),
        }
        enriched = {}
        for nid, nd in nodes.items():
            en = nd.get("experiment")
            if en and en in (experiments or {}):
                entry = dict(experiments[en])
                entry.update({k: v for k, v in unit_cfg.items()
                              if v not in ("", False, None)})
                enriched[en] = entry
        zb  = _build_export_zip(nodes, edges, enriched, unit_cfg)
        ts  = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        fn  = f"FrameworkAutomation_{ts}.zip"
        b64 = base64.b64encode(zb).decode()
        return (dcc.send_bytes(zb, fn),
                f"\u2713 Exported: {fn}",
                _toast(f"Exported {fn}", "success"), b64)

    return no_update, no_update, no_update, no_update


# ══════════════════════════════════════════════════════════════════════════════
#  Pure helpers
# ══════════════════════════════════════════════════════════════════════════════
def _node_list_html(nodes):
    if not nodes:
        return html.Span("No nodes.",
                         style={"color": "#3a4a5a", "fontSize": "0.74rem"})
    rows = []
    for nid, nd in nodes.items():
        info    = _TYPE_MAP.get(nd["type"], {"label": nd["type"], "color": "#555"})
        exp_tag = f" [{nd['experiment'][:12]}]" if nd.get("experiment") else ""
        nc      = len(nd.get("connections", {}))
        rows.append(html.Div([
            html.Span("\u25cf ", style={"color": info["color"]}),
            html.Span(f"{nid}: {info['label']}{exp_tag}" +
                      (f" \xb7{nc}" if nc else ""),
                      style={"color": "#c0d0e0", "fontSize": "0.73rem"}),
        ], style={"marginBottom": "1px", "lineHeight": "1.3"}))
    return rows


def _validate(nodes, edges, experiments):
    errs, warns = [], []
    if not any(n["type"] == "StartNode" for n in nodes.values()):
        errs.append("Flow must have a StartNode")
    if not any(n["type"] == "EndNode" for n in nodes.values()):
        warns.append("No EndNode found")
    no_exp = [nid for nid, nd in nodes.items()
              if nd["type"] not in ("StartNode", "EndNode")
              and not nd.get("experiment")]
    if no_exp:
        errs.append(f"No experiment assigned: {', '.join(no_exp[:3])}")
    return errs, warns


def _auto_layout(nodes, edges):
    if not nodes:
        return nodes
    roots = [nid for nid, nd in nodes.items() if nd["type"] == "StartNode"] \
            or [next(iter(nodes))]
    visited, queue, level_x = {}, [(roots[0], 0)], {}
    while queue:
        nid, lvl = queue.pop(0)
        if nid in visited:
            continue
        visited[nid] = lvl
        level_x.setdefault(lvl, 0)
        nodes[nid]["x"] = 180 + lvl * 210
        nodes[nid]["y"] = 120 + level_x[lvl] * 160
        level_x[lvl]   += 1
        for e in edges:
            if e["source"] == nid:
                queue.append((e["target"], lvl + 1))
    for nid in nodes:
        if nid not in visited:
            lvl = max(visited.values(), default=0) + 1
            level_x.setdefault(lvl, 0)
            nodes[nid]["x"] = 180 + lvl * 210
            nodes[nid]["y"] = 120 + level_x[lvl] * 160
            level_x[lvl]   += 1
    return nodes


def _build_export_zip(nodes, edges, experiments, unit_config):
    structure = {
        nid: {"name": nd["name"], "instanceType": nd["type"],
              "flow": nd.get("experiment", "default"),
              "outputNodeMap": nd.get("connections", {})}
        for nid, nd in nodes.items()
    }
    ts  = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    ini = ["[DEFAULT]", f"# FrameworkAutomation generated {ts}",
           f"# Visual ID: {unit_config.get('Visual ID', '')}", ""]
    ini += [f"[{n}]\n" for n in experiments]
    pos = {nid: {"x": nd["x"], "y": nd["y"]} for nid, nd in nodes.items()}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("FrameworkAutomationStructure.json",
                    json.dumps(structure,   indent=2))
        zf.writestr("FrameworkAutomationFlows.json",
                    json.dumps(experiments, indent=2))
        zf.writestr("FrameworkAutomationInit.ini",     "\n".join(ini))
        zf.writestr("FrameworkAutomationPositions.json",
                    json.dumps(pos,         indent=2))
    return buf.getvalue()


def _toast(msg, icon, duration=4000):
    return dbc.Toast(
        msg, icon=icon, duration=duration, is_open=True,
        style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
        className="toast-custom",
    )
