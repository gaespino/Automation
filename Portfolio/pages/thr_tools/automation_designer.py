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
from dash import html, dcc, Input, Output, State, callback, no_update, ctx, ALL
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
    {"type": "StartNode",                    "label": "Start",           "color": "#1abc9c", "colorL": "#4ecdc4", "colorD": "#0a7a65", "symbol": "\u25b6", "sym_bg": "#0a5c50"},
    {"type": "EndNode",                      "label": "End",             "color": "#e74c3c", "colorL": "#ff7675", "colorD": "#922b21", "symbol": "\u25a0", "sym_bg": "#7b2410"},
    {"type": "SingleFailFlowInstance",       "label": "SingleFail",      "color": "#3498db", "colorL": "#74b9ff", "colorD": "#1a6fa8", "symbol": "\u2717",  "sym_bg": "#1a4a6f"},
    {"type": "AllFailFlowInstance",          "label": "AllFail",         "color": "#2471a3", "colorL": "#5dade2", "colorD": "#1a4a75", "symbol": "\u2756",  "sym_bg": "#12304e"},
    {"type": "MajorityFailFlowInstance",     "label": "MajorityFail",    "color": "#8e44ad", "colorL": "#bb8fce", "colorD": "#5b2c6f", "symbol": "\u00bd",  "sym_bg": "#3d1a5a"},
    {"type": "AdaptiveFlowInstance",         "label": "Adaptive",        "color": "#e67e22", "colorL": "#f0a500", "colorD": "#9c5e0a", "symbol": "\u25c6",  "sym_bg": "#7a4000"},
    {"type": "CharacterizationFlowInstance", "label": "Characterization","color": "#16a085", "colorL": "#48c9b0", "colorD": "#0a5d4d", "symbol": "\u25ce",  "sym_bg": "#073d33"},
    {"type": "DataCollectionFlowInstance",   "label": "DataCollection",  "color": "#27ae60", "colorL": "#6bcf7f", "colorD": "#1a6e38", "symbol": "\u2295",  "sym_bg": "#0e4a20"},
    {"type": "AnalysisFlowInstance",         "label": "Analysis",        "color": "#c0392b", "colorL": "#ec7063", "colorD": "#7b241c", "symbol": "\u2299",  "sym_bg": "#5a1610"},
]
_TYPE_MAP = {n["type"]: n for n in _NODE_TYPES}
_NODE_TYPE_OPTIONS = [{"label": n["label"], "value": n["type"]} for n in _NODE_TYPES]

# Port sets per node type — matches original draw_connection_ports logic:
#   StartNode              → P0 only (success path)
#   EndNode                → no outputs
#   Characterization/Data/Analysis/Adaptive → P0 + P3 (OK + Error)
#   SingleFail/AllFail/MajorityFail         → P0–P3 (all four ports)
_NODE_PORTS: dict[str, list[int]] = {
    "StartNode":                    [0],
    "EndNode":                      [],
    "SingleFailFlowInstance":       [0, 1, 2, 3],
    "AllFailFlowInstance":          [0, 1, 2, 3],
    "MajorityFailFlowInstance":     [0, 1, 2, 3],
    "AdaptiveFlowInstance":         [0, 3],
    "CharacterizationFlowInstance": [0, 3],
    "DataCollectionFlowInstance":   [0, 3],
    "AnalysisFlowInstance":         [0, 3],
}

# Convenience styles
_IS = {
    "backgroundColor": "#0a0d14", "color": "#dde4ee",
    "border": "1px solid rgba(255,255,255,0.1)", "fontSize": "0.8rem",
}
_LS = {"color": "#6a7a8a", "fontSize": "0.73rem", "marginBottom": "2px"}


# ── Cytoscape stylesheet ───────────────────────────────────────────────────────
# Nodes use SVG data-URL backgrounds (generated per-node in _node_svg) so that
# we can draw rich content: type header, name, experiment, IN port at top and
# OUT port dots at bottom.  Cytoscape only applies shadow + selection overlay.
_STYLESHEET = [
    {"selector": "node", "style": {
        "label": "",                           # all text is inside the SVG
        "background-image": "data(svgBg)",
        "background-fit":   "cover",
        "background-color": "data(color)",     # solid fallback if SVG fails to load
        "background-opacity": 1,
        "background-image-opacity": 1,
        "width": 190, "height": 130,
        "shape": "roundrectangle",
        "border-width": 0,                     # border is drawn inside the SVG
        "shadow-blur": 22,
        "shadow-color": "data(color)",
        "shadow-opacity": 0.50,
        "shadow-offset-x": 0, "shadow-offset-y": 5,
    }},
    # Selected — gold outline overlay
    {"selector": "node:selected", "style": {
        "border-width": 3, "border-color": "#f1c40f",
        "shadow-color": "#f1c40f", "shadow-blur": 30, "shadow-opacity": 0.75,
        "overlay-color": "#f1c40f", "overlay-padding": 4, "overlay-opacity": 0.10,
    }},
    # Pending source in connect-mode — orange glow
    {"selector": "node.source-pending", "style": {
        "border-width": 3, "border-color": "#f39c12",
        "shadow-color": "#f39c12", "shadow-blur": 36, "shadow-opacity": 0.95,
    }},
    # Edge — bezier curves with port-accurate source endpoint
    {"selector": "edge", "style": {
        "curve-style":        "bezier",
        "target-arrow-shape": "triangle",
        "arrow-scale": 1.6,
        "line-color": "data(edgeColor)",
        "target-arrow-color": "data(edgeColor)",
        "width": 2.5,
        "label": "data(portLabel)",
        "font-size": "9px", "color": "#dde4ee",
        "text-background-color": "#06080f", "text-background-opacity": 0.88,
        "text-background-padding": "3px", "text-background-shape": "roundrectangle",
        "edge-text-rotation": "autorotate",
        "source-endpoint": "data(sourceEp)",   # port-dot x%, bottom-strip y%
        "target-endpoint": "50% 9%",           # ▲IN strip top-centre
    }},
    # Selected edge — gold highlight
    {"selector": "edge:selected", "style": {
        "line-color": "#f1c40f", "target-arrow-color": "#f1c40f",
        "width": 4,
        "overlay-color": "#f1c40f", "overlay-opacity": 0.22, "overlay-padding": 4,
    }},
]


# ── Element builders ───────────────────────────────────────────────────────────
_PORT_COLORS_LIST = ["#1abc9c", "#e74c3c", "#f39c12", "#9b59b6"]


def _node_svg(type_label: str, name: str, exp_name: str,
              color: str, colorL: str, colorD: str, node_type: str,
              ports: "list[int] | None" = None,
              symbol: str = "\u25c9", sym_bg: str = "#1a2a3a",
              uid: str = "n") -> str:
    """SVG background for a cytoscape node.

    Layout (top → bottom):
      HEADER strip: [symbol badge left] [type label center] [▲IN right on non-Start]
      NAME   (large, bold, white)        ← most prominent
      [exp]  (small, italic teal — only when assigned)
      ▼ OUT strip with coloured port dots (hidden on EndNode)

    *uid* is used to make linearGradient IDs unique per node so that different
    browsers don't share gradient definitions across multiple SVG data-URIs.
    """
    W, H, R = 190, 130, 9
    STRIP = 24
    if ports is None:
        ports = _NODE_PORTS.get(node_type, [0, 1, 2, 3])
    is_start = node_type == "StartNode"
    # Unique IDs to avoid cross-SVG gradient pollution in some browsers
    gid = re.sub(r"[^a-z0-9]", "", uid.lower())[:8] or "n"

    def esc(s: str) -> str:
        return (str(s)
                .replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    sname = (name[:20] + "\u2026") if len(name) > 20 else name
    sexp  = (exp_name[:22] + "\u2026") if len(exp_name) > 22 else exp_name

    p: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'style="font-family:Segoe UI,Inter,Arial,sans-serif">',
        '<defs>',
        f'<linearGradient id="bg{gid}" x1="0" y1="0" x2="0" y2="1">',
        f'  <stop offset="0%"   stop-color="{colorL}"/>',
        f'  <stop offset="45%"  stop-color="{color}"/>',
        f'  <stop offset="100%" stop-color="{colorD}"/>',
        '</linearGradient>',
        f'<linearGradient id="ts{gid}" x1="0" y1="0" x2="0" y2="1">',
        f'  <stop offset="0%"   stop-color="#000" stop-opacity="0.55"/>',
        f'  <stop offset="100%" stop-color="#000" stop-opacity="0.18"/>',
        '</linearGradient>',
        f'<linearGradient id="bs{gid}" x1="0" y1="0" x2="0" y2="1">',
        f'  <stop offset="0%"   stop-color="#000" stop-opacity="0.18"/>',
        f'  <stop offset="100%" stop-color="#000" stop-opacity="0.60"/>',
        '</linearGradient>',
        '</defs>',
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="{R}" ry="{R}" '
        f'fill="url(#bg{gid})" stroke="{colorL}" stroke-width="2"/>',
        # Header strip (always visible)
        f'<rect x="1" y="1" width="{W-2}" height="{STRIP}" '
        f'rx="{R}" ry="{R}" fill="url(#ts{gid})"/>',
        f'<rect x="1" y="{1+R}" width="{W-2}" height="{STRIP-R}" fill="url(#ts{gid})"/>',
        f'<line x1="1" y1="{STRIP+1}" x2="{W-1}" y2="{STRIP+1}" '
        f'stroke="{colorL}" stroke-opacity="0.35" stroke-width="0.5"/>',
        # Symbol badge (left)
        f'<circle cx="15" cy="{STRIP//2+1}" r="9" fill="{sym_bg}" opacity="0.92"/>',
        f'<text x="15" y="{STRIP//2+1}" text-anchor="middle" '
        f'dominant-baseline="middle" fill="white" font-size="10" '
        f'font-weight="700">{esc(symbol)}</text>',
        # Type label (centre)
        f'<text x="{W//2}" y="{STRIP//2+1}" text-anchor="middle" '
        f'dominant-baseline="middle" fill="#d0e8f8" font-size="9" '
        f'font-weight="600" letter-spacing="0.5">{esc(type_label)}</text>',
    ]
    # ▲IN on non-Start nodes (right side of header)
    if not is_start:
        p.append(
            f'<text x="{W-6}" y="{STRIP//2+1}" text-anchor="end" '
            f'dominant-baseline="middle" fill="#9ab4c8" font-size="8" '
            f'font-weight="600">\u25b2IN</text>'
        )

    # ── content area ─────────────────────────────────────────────────────────
    top_off = STRIP + 2
    bot_off = STRIP if ports else 4
    avail_h = H - top_off - bot_off

    rows: list[tuple[str, int, str, str]] = [
        (esc(sname), 13, "#ffffff", "700"),   # node name — big + bold
    ]
    if sexp:
        rows.append((f"[ {esc(sexp)} ]", 8, "#1abc9c", "300"))  # experiment — teal

    total_h = sum(sz + 5 for _, sz, _, _ in rows)
    y_cur   = top_off + max(0, (avail_h - total_h) // 2)

    for txt, sz, fill, weight in rows:
        y_cur += sz
        p.append(
            f'<text x="{W//2}" y="{y_cur}" text-anchor="middle" '
            f'fill="{fill}" font-size="{sz}" font-weight="{weight}">'
            f'{txt}</text>'
        )
        y_cur += 5

    # ── BOTTOM strip: OUTPUT ports ────────────────────────────────────────────
    if ports:
        ys = H - STRIP
        p += [
            f'<line x1="1" y1="{ys}" x2="{W-1}" y2="{ys}" '
            f'stroke="{colorL}" stroke-opacity="0.35" stroke-width="0.5"/>',
            f'<rect x="1" y="{ys}" width="{W-2}" height="{STRIP}" '
            f'rx="0" ry="0" fill="url(#bs{gid})"/>',
            f'<rect x="1" y="{H-1-R}" width="{W-2}" height="{R+1}" '
            f'rx="{R}" ry="{R}" fill="url(#bs{gid})"/>',
            f'<text x="11" y="{H - STRIP//2}" dominant-baseline="middle" '
            f'fill="#6a8a9a" font-size="7" font-weight="600" letter-spacing="1">'
            f'\u25bc OUT</text>',
        ]
        n_p = len(ports)
        dot_start_x = W - n_p * 22 - 4
        for i, pi in enumerate(sorted(ports)):
            pc = _PORT_COLORS.get(pi, "#888")
            cx = dot_start_x + i * 22 + 11
            cy = H - STRIP // 2
            p += [
                f'<circle cx="{cx}" cy="{cy}" r="8" fill="{pc}" opacity="0.92"/>',
                f'<text x="{cx}" y="{cy}" text-anchor="middle" '
                f'dominant-baseline="middle" fill="white" '
                f'font-size="7" font-weight="700">P{pi}</text>',
            ]

    p.append('</svg>')
    svg_bytes = "\n".join(p).encode("utf-8")
    return "data:image/svg+xml;base64," + base64.b64encode(svg_bytes).decode("ascii")


def _node_elem(node_id, node_type, name, exp_name, x, y, pending=False):
    info = _TYPE_MAP.get(
        node_type,
        {"label": node_type, "color": "#555", "colorL": "#777", "colorD": "#333",
         "symbol": "\u25c9", "sym_bg": "#1a2a3a"},
    )
    ports = _NODE_PORTS.get(node_type, [0, 1, 2, 3])
    svg_bg = _node_svg(
        info["label"], name or node_id, exp_name or "",
        info["color"], info.get("colorL", info["color"]), info.get("colorD", info["color"]),
        node_type, ports,
        symbol=info.get("symbol", "\u25c9"),
        sym_bg=info.get("sym_bg", "#1a2a3a"),
        uid=node_id,
    )
    return {
        "data": {
            "id":         node_id,
            "label":      "",
            "type":       node_type,
            "name":       name or node_id,
            "experiment": exp_name or "",
            "color":      info["color"],
            "colorD":     info.get("colorD", info["color"]),
            "colorL":     info.get("colorL", info["color"]),
            "svgBg":      svg_bg,
        },
        "position": {"x": x, "y": y},
        "classes":  "source-pending" if pending else "",
        "grabbable": True,
    }


def _source_ep(source_id: str, port_num: int, nodes_store: dict) -> str:
    """Compute the 'N% M%' cytoscape source-endpoint for this port on source_id.

    This positions the edge tail exactly at the coloured port dot in the OUT strip,
    matching the visual indicator drawn by _node_svg.
    """
    W    = 190          # node width
    node_type = (nodes_store or {}).get(source_id, {}).get("type", "")
    ports = sorted(_NODE_PORTS.get(node_type, [0, 1, 2, 3]))
    n_p   = len(ports)
    if n_p == 0:
        return "50% 100%"
    try:
        idx = ports.index(port_num)
    except ValueError:
        idx = 0
    # Mirror the dot_start_x formula from _node_svg
    dot_start_x = W - n_p * 22 - 4
    cx = dot_start_x + idx * 22 + 11
    x_pct = round(cx / W * 100, 1)
    return f"{x_pct}% 91%"   # 91% ≈ centre of OUT strip (H-STRIP//2 = 118/130)



    """Build a {node_id: {x, y}} map from the current Cytoscape elements list.
    This preserves user-dragged positions when we rebuild elements."""
    pos = {}
    for el in (canvas_elements or []):
        if "position" in el and "data" in el and "source" not in el.get("data", {}):
            nid = el["data"].get("id")
            if nid:
                pos[nid] = el["position"]
    return pos


def _build_elements(nodes_store, edges_store, pending_source=None, canvas_pos=None):
    """Build cytoscape elements list.

    *canvas_pos* is the position map from _canvas_pos_map().  When provided,
    existing nodes use their current canvas positions (preserving user drags)
    instead of the stored initial positions.
    """
    pos_map = canvas_pos or {}
    elems = []
    for nid, nd in (nodes_store or {}).items():
        # Prefer canvas position (preserves drag) over stored position
        cp  = pos_map.get(nid)
        x   = cp["x"] if cp else nd.get("x", 200)
        y   = cp["y"] if cp else nd.get("y", 200)
        elems.append(_node_elem(
            nid, nd["type"], nd.get("name", ""), nd.get("experiment", ""),
            x, y,
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
            "sourceEp":  _source_ep(edge["source"], port, nodes_store),
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


def _left_sidebar():
    """Fixed-width left sidebar (no Offcanvas overlay — part of the flex layout)."""
    def _fld(lbl, fid, ph, t="text"):
        return html.Div([
            html.Label(lbl, style=_LS),
            dbc.Input(id=fid, type=t, placeholder=ph, className="mb-2",
                      style={**_IS, "height": "28px"}),
        ])
    return html.Div(
        id="ad-left-panel",
        style={
            "width": "265px", "minWidth": "265px",
            "display": "flex", "flexDirection": "column",
            "overflowY": "auto", "overflowX": "hidden",
            "backgroundColor": "#10131c",
            "borderRight": "1px solid rgba(26,188,156,0.2)",
        },
        children=[
            # ── Product selector — most visible, at the very top ──────────────
            html.Div(style={"padding": "8px 12px",
                            "borderBottom": "1px solid rgba(26,188,156,0.2)",
                            "backgroundColor": "rgba(26,188,156,0.06)"}, children=[
                html.Div([
                    html.I(className="bi bi-cpu-fill me-2", style={"color": ACCENT}),
                    html.Span("Product",
                              style={"color": ACCENT, "fontWeight": "700",
                                     "fontSize": "0.88rem"}),
                ], style={"marginBottom": "5px"}),
                dbc.Select(id="ad-product",
                           options=[{"label": p, "value": p} for p in _PRODUCTS],
                           value="GNR",
                           style={**_IS, "height": "30px", "fontWeight": "600",
                                  "fontSize": "0.84rem"}),
            ]),
            # ── Unit Configuration ────────────────────────────────────────────
            html.Div(style={"padding": "8px 12px",
                            "borderBottom": "1px solid rgba(255,255,255,0.07)"}, children=[
                html.Div([
                    html.I(className="bi bi-cpu me-2", style={"color": ACCENT}),
                    html.Span("Unit Configuration",
                              style={"color": ACCENT, "fontWeight": "700",
                                     "fontSize": "0.84rem"}),
                ], style={"marginBottom": "8px"}),
                _fld("Visual ID",  "ad-vid",    "75EH348100130"),
                _fld("Bucket",     "ad-bucket", "N/A"),
                _fld("COM Port",   "ad-com",    "COM3"),
                _fld("IP Address", "ad-ip",     "192.168.1.100"),
                html.Div([
                    dbc.Checklist(
                        id="ad-unit-flags",
                        options=[{"label": "600W Unit", "value": "600w"}],
                        value=[],
                        inputStyle={"marginRight": "6px"},
                        labelStyle={"color": "#dde4ee", "fontSize": "0.82rem"},
                    ),
                ], className="mb-1"),
                html.Div([
                    html.Label("Check Core (int)", style=_LS),
                    dbc.Input(id="ad-check-core", type="number", placeholder="e.g. 7",
                              min=0, step=1,
                              style={**_IS, "height": "26px", "fontSize": "0.8rem"}),
                ]),
            ]),
            # ── Load Experiments ──────────────────────────────────────────────
            html.Div(style={"padding": "8px 12px"}, children=[
                html.Div([
                    html.I(className="bi bi-collection me-2", style={"color": ACCENT}),
                    html.Span("Load Experiments",
                              style={"color": ACCENT, "fontWeight": "700",
                                     "fontSize": "0.84rem", "marginBottom": "8px"}),
                ], style={"marginBottom": "8px"}),
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
        # 20px grid canvas background (matches original PPV canvas grid spacing)
        html.Div(id="ad-canvas-wrap", style={
            "flex": "1", "position": "relative", "overflow": "hidden",
            "backgroundImage": (
                "linear-gradient(rgba(26,188,156,0.07) 1px, transparent 1px),"
                "linear-gradient(90deg, rgba(26,188,156,0.07) 1px, transparent 1px)"
            ),
            "backgroundSize": "20px 20px",
            "backgroundColor": "#06080f",
        }, children=[
        cyto.Cytoscape(
            id="ad-canvas",
            elements=[],
            layout={"name": "preset"},
            style={"position": "absolute", "top": 0, "left": 0,
                   "width": "100%", "height": "100%",
                   "backgroundColor": "transparent"},
            stylesheet=_STYLESHEET,
            boxSelectionEnabled=True,
            autoRefreshLayout=False,
            userPanningEnabled=True,
            userZoomingEnabled=True,
            minZoom=0.15, maxZoom=4,
            responsive=True,
        )]),
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

    # Node Palette — colored buttons, one per type, clicking adds that node
    palette_btns = []
    for nt in _NODE_TYPES:
        palette_btns.append(
            dbc.Button(
                [html.Span(nt["symbol"], style={"marginRight": "4px"}), nt["label"]],
                id={"type": "ad-palette-btn", "index": nt["type"]},
                n_clicks=0, size="sm",
                style={
                    "backgroundColor": nt["colorD"],
                    "borderColor": nt["colorL"],
                    "color": "#fff",
                    "fontSize": "0.72rem",
                    "padding": "2px 6px",
                    "height": "24px",
                    "width": "100%",
                    "textAlign": "left",
                    "marginBottom": "2px",
                    "overflow": "hidden", "textOverflow": "ellipsis",
                    "whiteSpace": "nowrap",
                },
            )
        )

    return [
        # ── Node Palette — add nodes by clicking type buttons ─────────────────
        html.Div([
            html.Div("Node Palette", style={
                "color": ACCENT, "fontSize": "0.77rem", "fontWeight": "700",
                "padding": "6px 10px 4px",
                "borderBottom": "1px solid rgba(255,255,255,0.07)",
            }),
            html.Div(palette_btns, style={"padding": "6px 10px"}),
        ], style={"borderBottom": "1px solid rgba(255,255,255,0.08)"}),
        # ── Node Editor FIRST — most important panel ──────────────────────────
        _card("Node Editor", "ad-node-editor",
              [html.Span("Click a node or press Edit ✏ in the list below.",
                         style={"color": "#3a4a5a", "fontSize": "0.74rem"})]),
        # ── Experiments (with Edit ✏ per entry) ──────────────────────────────
        _card("Experiments", "ad-exp-list",
              [html.Span("No experiments loaded.",
                         style={"color": "#3a4a5a", "fontSize": "0.74rem"})],
              max_h="120px"),
        # ── Flow Nodes (with Edit buttons) ────────────────────────────────────
        _card("Flow Nodes", "ad-node-list",
              [html.Span("No nodes.",
                         style={"color": "#3a4a5a", "fontSize": "0.74rem"})],
              max_h="260px"),
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
        html.Div(style={"padding": "6px 10px 6px", "flex": "1"}, children=[
            html.Div("Log", style={"color": ACCENT, "fontSize": "0.77rem",
                                   "fontWeight": "700", "marginBottom": "4px"}),
            dbc.Textarea(
                id="ad-log", value="Automation Designer ready.\n", readOnly=True,
                style={"backgroundColor": "#04050a", "color": "#7a9a88",
                       "fontFamily": "Consolas, 'Courier New', monospace",
                       "fontSize": "0.69rem", "border": "none", "resize": "none",
                       "width": "100%", "minHeight": "120px", "padding": "6px 10px"},
            ),
        ]),
    ]


def _edit_modal():
    """Floating modal for editing a node — triggered by Edit ✏ button in node list."""
    exp_placeholder = [{"label": "— none —", "value": ""}]
    return dbc.Modal(
        id="ad-edit-modal",
        is_open=False,
        size="md",
        backdrop=True,
        className="modal-dark",
        children=[
            dbc.ModalHeader(
                html.Span(id="ad-modal-title",
                          style={"color": ACCENT, "fontWeight": "700"}),
                close_button=True,
                style={"backgroundColor": "#10131c",
                       "borderBottom": "1px solid rgba(255,255,255,0.1)"},
            ),
            dbc.ModalBody(style={"backgroundColor": "#10131c"}, children=[
                html.Label("Name", style=_LS),
                dbc.Input(id="ad-modal-name", type="text", className="mb-2",
                          style={**_IS, "height": "28px"}),
                html.Label("Experiment", style=_LS),
                dbc.Select(id="ad-modal-exp", options=exp_placeholder, value="",
                           className="mb-2",
                           style={**_IS, "height": "28px"}),
                html.Div(id="ad-modal-connections",
                         style={"color": "#7a9a88", "fontSize": "0.73rem",
                                "marginBottom": "4px"}),
            ]),
            dbc.ModalFooter(style={"backgroundColor": "#10131c",
                                   "borderTop": "1px solid rgba(255,255,255,0.1)"}, children=[
                dbc.Button([html.I(className="bi bi-check me-1"), "Apply"],
                           id="ad-modal-apply", n_clicks=0,
                           style={"borderColor": ACCENT, "color": ACCENT,
                                  "backgroundColor": "transparent",
                                  "fontSize": "0.8rem"},
                           outline=True),
                dbc.Button("Close", id="ad-modal-close", n_clicks=0,
                           color="secondary", outline=True,
                           style={"fontSize": "0.8rem", "marginLeft": "6px"}),
            ]),
        ],
    )


def _exp_editor_modal():
    """Full experiment editor modal — opened via Edit ✏ on an experiment in the list."""
    return dbc.Modal(
        id="ad-exp-editor-modal",
        is_open=False,
        size="lg",
        scrollable=True,
        backdrop=True,
        className="modal-dark",
        children=[
            dbc.ModalHeader(
                html.Span(id="ad-exp-editor-title",
                          style={"color": ACCENT, "fontWeight": "700"}),
                close_button=True,
                style={"backgroundColor": "#10131c",
                       "borderBottom": "1px solid rgba(255,255,255,0.1)"},
            ),
            dbc.ModalBody(style={"backgroundColor": "#10131c"}, children=[
                html.Label("Experiment Name", style=_LS),
                dbc.Input(id="ad-exp-editor-name", type="text", className="mb-3",
                          style={**_IS, "height": "30px"}),
                html.Div(id="ad-exp-editor-fields",
                         style={"maxHeight": "60vh", "overflowY": "auto"}),
            ]),
            dbc.ModalFooter(style={"backgroundColor": "#10131c",
                                   "borderTop": "1px solid rgba(255,255,255,0.1)"}, children=[
                dbc.Button([html.I(className="bi bi-floppy me-1"), "Save (overwrite)"],
                           id="ad-exp-editor-save", n_clicks=0,
                           style={"borderColor": ACCENT, "color": ACCENT,
                                  "backgroundColor": "transparent", "fontSize": "0.8rem"},
                           outline=True),
                dbc.Button([html.I(className="bi bi-plus me-1"), "Save as New"],
                           id="ad-exp-editor-save-new", n_clicks=0,
                           style={"borderColor": "#7a9a88", "color": "#7a9a88",
                                  "backgroundColor": "transparent", "fontSize": "0.8rem",
                                  "marginLeft": "6px"},
                           outline=True),
                dbc.Button("Close", id="ad-exp-editor-close", n_clicks=0,
                           color="secondary", outline=True,
                           style={"fontSize": "0.8rem", "marginLeft": "6px"}),
            ]),
        ],
    )


def _ctx_menu_modal():
    """Context menu modal — opens on right-click on a node (via ad-ctx-node-store)."""
    return dbc.Modal(
        id="ad-ctx-modal",
        is_open=False,
        size="sm",
        backdrop=True,
        className="modal-dark",
        children=[
            dbc.ModalHeader(
                html.Span(id="ad-ctx-modal-title",
                          style={"color": ACCENT, "fontWeight": "700", "fontSize": "0.85rem"}),
                close_button=True,
                style={"backgroundColor": "#10131c",
                       "borderBottom": "1px solid rgba(255,255,255,0.1)"},
            ),
            dbc.ModalBody(style={"backgroundColor": "#10131c", "padding": "10px 16px"},
                          children=[
                html.Div(id="ad-ctx-modal-body"),
            ]),
        ],
    )



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
        dcc.Store(id="ad-connect-mode",
                  data={"active": False, "pending": None, "port": "0"}),
        dcc.Store(id="ad-right-open",  data=True),
        dcc.Store(id="ad-left-open",   data=True),
        dcc.Store(id="ad-modal-node",  data=None),   # node ID currently open in edit modal
        dcc.Store(id="ad-exp-editor-orig-name", data=None),  # original exp name being edited
        dcc.Store(id="ad-ctx-node-store", data=None),        # right-clicked node id
        dcc.Interval(id="ad-ctx-poll", interval=200, max_intervals=-1),

        _toolbar(),
        _edit_modal(),
        _exp_editor_modal(),
        _ctx_menu_modal(),
        # Validation banner — shown below toolbar after Validate is clicked
        html.Div(id="ad-validate-banner", style={"padding": "0", "flexShrink": 0}),

        html.Div(style={"display": "flex", "flex": "1",
                        "overflow": "hidden", "minHeight": 0}, children=[
            _left_sidebar(),
            _canvas_area(),
            html.Div(id="ad-right-panel",
                     style={"width": "260px", "minWidth": "260px",
                            "display": "flex", "flexDirection": "column",
                            "overflowY": "auto",
                            "backgroundColor": "#0c0f18",
                            "borderLeft": "1px solid rgba(26,188,156,0.15)"},
                     children=_right_panel_content()),
        ]),

        html.Div(id="ad-toast"),
    ])


# ══════════════════════════════════════════════════════════════════════════════
#  Callbacks
# ══════════════════════════════════════════════════════════════════════════════

# ── Clientside: capture right-click on canvas wrapper ─────────────────────────
# Sets window._adCtxNodeId via mouseoverNodeData tracking, then stores the
# right-clicked node id via the polling interval.
dash.get_app().clientside_callback(
    """
    function(n) {
        if (window._adCtxSetup) return window.dash_clientside.no_update;
        window._adCtxSetup = true;
        window._adCtxPending = null;
        window._adCtxHoveredId = null;
        setTimeout(function() {
            var wrap = document.getElementById('ad-canvas-wrap');
            if (!wrap) wrap = document.getElementById('ad-canvas');
            if (wrap) {
                wrap.addEventListener('contextmenu', function(e) {
                    e.preventDefault();
                    window._adCtxPending = {
                        nodeId: window._adCtxHoveredId,
                        t: Date.now()
                    };
                });
            }
        }, 800);
        return window.dash_clientside.no_update;
    }
    """,
    Output("ad-ctx-node-store", "data", allow_duplicate=True),
    Input("ad-canvas", "id"),
    prevent_initial_call=True,
)

dash.get_app().clientside_callback(
    """
    function(nodeData) {
        if (nodeData && nodeData.id) window._adCtxHoveredId = nodeData.id;
        return window.dash_clientside.no_update;
    }
    """,
    Output("ad-ctx-node-store", "data", allow_duplicate=True),
    Input("ad-canvas", "mouseoverNodeData"),
    prevent_initial_call=True,
)

dash.get_app().clientside_callback(
    """
    function(n) {
        if (!window._adCtxPending) return window.dash_clientside.no_update;
        var d = window._adCtxPending;
        window._adCtxPending = null;
        return d.nodeId || '__canvas__';
    }
    """,
    Output("ad-ctx-node-store", "data"),
    Input("ad-ctx-poll", "n_intervals"),
    prevent_initial_call=True,
)


@callback(
    Output("ad-ctx-modal",       "is_open"),
    Output("ad-ctx-modal-title", "children"),
    Output("ad-ctx-modal-body",  "children"),
    Input("ad-ctx-node-store",   "data"),
    State("ad-nodes-store",      "data"),
    State("ad-experiments-store","data"),
    State("ad-ctx-modal",        "is_open"),
    prevent_initial_call=True,
)
def show_ctx_menu(node_id, nodes, experiments, is_open):
    """Show the right-click context modal for a node."""
    if not node_id or node_id == "__canvas__":
        return False, no_update, no_update
    nd = (nodes or {}).get(node_id)
    if not nd:
        return False, no_update, no_update
    info      = _TYPE_MAP.get(nd["type"], {"label": nd["type"], "color": "#555"})
    title     = [
        html.Span(nd.get("name", node_id),
                  style={"color": info["color"], "marginRight": "6px"}),
        html.Span(f"({info['label']})", style={"color": "#5a7a8a", "fontSize": "0.78rem"}),
    ]
    # Connections summary
    conn_rows = []
    for p, t in nd.get("connections", {}).items():
        pi = int(p)
        conn_rows.append(html.Div(
            f"P{pi}:{_PORT_LABELS.get(pi,'?')} \u2192 {t}",
            style={"color": _PORT_COLORS.get(pi, "#aaa"), "fontSize": "0.75rem",
                   "marginBottom": "2px"},
        ))
    exp_name = nd.get("experiment") or "—"
    body = html.Div([
        html.Div([
            html.Span("Experiment: ", style={"color": "#5a7a8a", "fontSize": "0.8rem"}),
            html.Span(exp_name, style={"color": "#1abc9c", "fontSize": "0.8rem"}),
        ], style={"marginBottom": "8px"}),
        html.Div(conn_rows, style={"marginBottom": "10px"}) if conn_rows else html.Div(),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.1)", "margin": "6px 0"}),
        dbc.Button(
            [html.I(className="bi bi-pencil me-2"), "Edit Node"],
            id={"type": "ad-ctx-edit-node-btn", "index": node_id},
            n_clicks=0, size="sm",
            style={"width": "100%", "backgroundColor": "transparent",
                   "borderColor": ACCENT, "color": ACCENT,
                   "fontSize": "0.8rem", "marginBottom": "6px"},
            outline=True,
        ),
        dbc.Button(
            [html.I(className="bi bi-trash3 me-2"), "Delete Node"],
            id={"type": "ad-ctx-del-node-btn", "index": node_id},
            n_clicks=0, size="sm",
            style={"width": "100%", "backgroundColor": "transparent",
                   "borderColor": "#e74c3c", "color": "#e74c3c",
                   "fontSize": "0.8rem"},
            outline=True,
        ),
    ])
    return True, title, body


@callback(
    Output("ad-edit-modal",  "is_open", allow_duplicate=True),
    Output("ad-modal-node",  "data",    allow_duplicate=True),
    Output("ad-modal-title", "children",allow_duplicate=True),
    Output("ad-modal-name",  "value",   allow_duplicate=True),
    Output("ad-modal-exp",   "options", allow_duplicate=True),
    Output("ad-modal-exp",   "value",   allow_duplicate=True),
    Output("ad-modal-connections","children",allow_duplicate=True),
    Output("ad-ctx-modal",   "is_open", allow_duplicate=True),
    Input({"type": "ad-ctx-edit-node-btn", "index": ALL}, "n_clicks"),
    State("ad-nodes-store",       "data"),
    State("ad-experiments-store", "data"),
    prevent_initial_call=True,
)
def ctx_open_edit(clicks, nodes, experiments):
    if not any((c or 0) > 0 for c in (clicks or [])):
        return (no_update,) * 8
    nid = ctx.triggered_id["index"]
    nd  = (nodes or {}).get(nid)
    if not nd:
        return (no_update,) * 8
    info      = _TYPE_MAP.get(nd["type"], {"label": nd["type"], "color": "#555"})
    exp_opts  = [{"label": "\u2014 none \u2014", "value": ""}] + \
                [{"label": k, "value": k} for k in (experiments or {}).keys()]
    conn_rows = []
    for p, t in nd.get("connections", {}).items():
        pi = int(p)
        conn_rows.append(html.Span(
            f"P{pi}:{_PORT_LABELS.get(pi,'?')} \u2192 {t}  ",
            style={"color": _PORT_COLORS.get(pi, "#aaa"), "fontSize": "0.7rem"},
        ))
    title = [html.Span(f"Edit: {nid}", style={"color": info["color"]}),
             html.Span(f" ({info['label']})",
                       style={"color": "#5a7a8a", "fontSize": "0.8rem"})]
    return (True, nid, title, nd.get("name", nid), exp_opts,
            nd.get("experiment") or "", html.Div(conn_rows), False)


@callback(
    Output("ad-nodes-store",     "data",    allow_duplicate=True),
    Output("ad-edges-store",     "data",    allow_duplicate=True),
    Output("ad-canvas",          "elements",allow_duplicate=True),
    Output("ad-node-list",       "children",allow_duplicate=True),
    Output("ad-ctx-modal",       "is_open", allow_duplicate=True),
    Output("ad-log",             "value",   allow_duplicate=True),
    Output("ad-statusbar",       "children",allow_duplicate=True),
    Output("ad-toast",           "children",allow_duplicate=True),
    Input({"type": "ad-ctx-del-node-btn", "index": ALL}, "n_clicks"),
    State("ad-nodes-store",     "data"),
    State("ad-edges-store",     "data"),
    State("ad-canvas",          "elements"),
    State("ad-log",             "value"),
    prevent_initial_call=True,
)
def ctx_delete_node(clicks, nodes, edges, cur_elements, log_val):
    if not any((c or 0) > 0 for c in (clicks or [])):
        return (no_update,) * 8
    nid   = ctx.triggered_id["index"]
    nodes = dict(nodes or {})
    edges = list(edges or [])
    log   = log_val or ""
    ts    = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
    if nid not in nodes:
        return (no_update,) * 8
    del nodes[nid]
    edges = [e for e in edges if e["source"] != nid and e["target"] != nid]
    for nd in nodes.values():
        nd.get("connections", {}).pop(str(nid), None)
        nd["connections"] = {p: t for p, t in nd.get("connections", {}).items() if t != nid}
    cpos  = _canvas_pos_map(cur_elements)
    elems = _build_elements(nodes, edges, canvas_pos=cpos)
    log   = f"[{ts}] Deleted node: {nid}\n" + log
    return (nodes, edges, elems, _node_list_html(nodes), False, log,
            f"Deleted {nid}.",
            _toast(f"Deleted {nid}", "warning", 2000))


@callback(
    Output("ad-left-panel", "style"),
    Output("ad-left-open",  "data"),
    Input("ad-toggle-left-btn", "n_clicks"),
    State("ad-left-open", "data"),
    prevent_initial_call=True,
)
def toggle_left(n, is_open):
    now = not (is_open if is_open is not None else True)
    return ({
        "width": "265px" if now else "0px",
        "minWidth": "265px" if now else "0px",
        "display": "flex" if now else "none",
        "flexDirection": "column",
        "overflowY": "auto", "overflowX": "hidden",
        "backgroundColor": "#10131c",
        "borderRight": "1px solid rgba(26,188,156,0.2)",
    }, now)


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
        return (experiments,
                f"\u2713 {fname} ({len(experiments)} experiments)",
                _exp_list_html(experiments),
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
    Output("ad-nodes-store",       "data"),
    Output("ad-edges-store",       "data"),
    Output("ad-counter-store",     "data"),
    Output("ad-canvas",            "elements"),
    Output("ad-node-list",         "children"),
    Output("ad-connect-mode",      "data",     allow_duplicate=True),
    Output("ad-connect-hint",      "children", allow_duplicate=True),
    Output("ad-canvas-stats",      "children"),
    Output("ad-log",               "value"),
    Output("ad-statusbar",         "children", allow_duplicate=True),
    Output("ad-toast",             "children", allow_duplicate=True),
    Output("ad-experiments-store", "data",     allow_duplicate=True),
    Output("ad-exp-list",          "children", allow_duplicate=True),
    Input("ad-add-node-btn",       "n_clicks"),
    Input("ad-del-node-btn",       "n_clicks"),
    Input("ad-del-edge-btn",       "n_clicks"),
    Input("ad-layout-btn",         "n_clicks"),
    Input("ad-load-upload",        "contents"),
    Input("ad-canvas",             "tapNodeData"),
    Input({"type": "ad-palette-btn", "index": ALL}, "n_clicks"),
    State("ad-node-type-sel",      "value"),
    State("ad-nodes-store",        "data"),
    State("ad-edges-store",        "data"),
    State("ad-counter-store",      "data"),
    State("ad-canvas",             "selectedNodeData"),
    State("ad-connect-mode",       "data"),
    State("ad-selected-edge-store","data"),
    State("ad-load-upload",        "filename"),
    State("ad-log",                "value"),
    State("ad-canvas",             "elements"),   # State (not Input!) — avoids feedback loop
    prevent_initial_call=True,
)
def manage_canvas(add_c, del_c, del_edge_c, layout_c, load_content,
                  tap_node, palette_clicks,
                  node_type, nodes, edges, counter,
                  selected_nodes, connect_mode, sel_edge,
                  load_fname, log_val,
                  cur_elements):
    trigger = ctx.triggered_id
    nodes   = dict(nodes   or {})
    edges   = list(edges   or [])
    log     = log_val or ""
    cmode   = dict(connect_mode or {"active": False, "pending": None, "port": "0"})
    hint    = no_update
    status  = no_update
    # canvas_pos preserves user-dragged positions when rebuilding elements
    cpos    = _canvas_pos_map(cur_elements)

    def _log(msg):
        nonlocal log
        ts  = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
        log = f"[{ts}] {msg}\n" + log

    def _stats():
        return f"{len(nodes)} nodes \xb7 {len(edges)} edges"

    def _no_change():
        return (no_update, no_update, no_update, no_update, no_update,
                cmode, hint, no_update, log, status, no_update,
                no_update, no_update)

    # ── Add node (toolbar button) ─────────────────────────────────────────────
    if trigger == "ad-add-node-btn":
        nid  = f"NODE_{counter:03d}"
        counter += 1
        n    = len(nodes)
        # Snap to 20px grid (matches original PPV canvas grid)
        x = round((160 + (n % 4) * 220) / 20) * 20
        y = round((160 + (n // 4) * 180) / 20) * 20
        nodes[nid] = {"id": nid, "name": nid, "type": node_type,
                      "x": x, "y": y, "experiment": "", "connections": {}}
        _log(f"Added {_TYPE_MAP.get(node_type, {}).get('label', node_type)}: {nid}")
        elems = _build_elements(nodes, edges, cmode.get("pending"), cpos)
        return (nodes, edges, counter, elems, _node_list_html(nodes),
                cmode, hint, _stats(), log, f"Added {nid}.",
                _toast(f"Added {nid}", "success", 1500),
                no_update, no_update)

    # ── Add node via palette button ───────────────────────────────────────────
    if isinstance(trigger, dict) and trigger.get("type") == "ad-palette-btn":
        if not any((c or 0) > 0 for c in (palette_clicks or [])):
            return _no_change()
        ptype = trigger["index"]
        nid   = f"NODE_{counter:03d}"
        counter += 1
        n     = len(nodes)
        # Snap to 20px grid
        x = round((160 + (n % 4) * 220) / 20) * 20
        y = round((160 + (n // 4) * 180) / 20) * 20
        nodes[nid] = {"id": nid, "name": nid, "type": ptype,
                      "x": x, "y": y, "experiment": "", "connections": {}}
        _log(f"Added {_TYPE_MAP.get(ptype, {}).get('label', ptype)}: {nid}")
        elems = _build_elements(nodes, edges, cmode.get("pending"), cpos)
        return (nodes, edges, counter, elems, _node_list_html(nodes),
                cmode, hint, _stats(), log, f"Added {nid}.",
                _toast(f"Added {nid}", "success", 1500),
                no_update, no_update)

    # ── Delete node ───────────────────────────────────────────────────────────
    if trigger == "ad-del-node-btn":
        if not selected_nodes:
            return (no_update, no_update, no_update, no_update, no_update,
                    cmode, hint, no_update, log, "Select a node first.",
                    _toast("Select a node first.", "warning"),
                    no_update, no_update)
        for nd in selected_nodes:
            nid = nd.get("id")
            if nid in nodes:
                del nodes[nid]
                edges = [e for e in edges
                         if e.get("source") != nid and e.get("target") != nid]
                _log(f"Deleted {nid}")
        elems = _build_elements(nodes, edges, cmode.get("pending"), cpos)
        return (nodes, edges, counter, elems, _node_list_html(nodes),
                cmode, hint, _stats(), log, "Node(s) deleted.",
                _toast("Deleted.", "info", 1500),
                no_update, no_update)

    # ── Delete selected edge ──────────────────────────────────────────────────
    if trigger == "ad-del-edge-btn":
        if not sel_edge:
            return (no_update, no_update, no_update, no_update, no_update,
                    cmode, hint, no_update, log, "Click an edge first.",
                    _toast("Click an edge on the canvas first.", "warning"),
                    no_update, no_update)
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
        elems = _build_elements(nodes, edges, cmode.get("pending"), cpos)
        return (nodes, edges, counter, elems, _node_list_html(nodes),
                cmode, hint, _stats(), log, "Edge removed.",
                _toast("Edge removed.", "info", 1500),
                no_update, no_update)

    # ── Auto layout ───────────────────────────────────────────────────────────
    if trigger == "ad-layout-btn":
        nodes = _auto_layout(nodes, edges)
        _log("Applied auto layout")
        elems = _build_elements(nodes, edges, cmode.get("pending"))
        return (nodes, edges, counter, elems, _node_list_html(nodes),
                cmode, hint, _stats(), log, "Auto layout applied.", no_update,
                no_update, no_update)

    # ── Load flow design ──────────────────────────────────────────────────────
    if trigger == "ad-load-upload" and load_content:
        try:
            if "," not in load_content:
                return (no_update, no_update, no_update, no_update, no_update,
                        cmode, hint, no_update, log, "Invalid file format.",
                        _toast("Invalid file format.", "danger"),
                        no_update, no_update)
            _, data  = load_content.split(",", 1)
            design   = json.loads(base64.b64decode(data).decode("utf-8"))
            new_nodes, new_edges, new_ctr = {}, [], 1
            # Detect PPV format (no "_format" key) — PPV saves x,y as tkinter
            # top-left (150×100 node).  Cytoscape needs center → add half-node offset.
            _PPV_OFFSET_X, _PPV_OFFSET_Y = 75, 50
            is_ppv_format = "_format" not in design
            for nid, nd in design.get("nodes", {}).items():
                nd = dict(nd)
                if is_ppv_format:
                    nd["x"] = nd.get("x", 200) + _PPV_OFFSET_X
                    nd["y"] = nd.get("y", 200) + _PPV_OFFSET_Y
                new_nodes[nid] = nd
                m = re.search(r"(\d+)", nid)
                if m:
                    new_ctr = max(new_ctr, int(m.group(1)) + 1)
                for prt, tgt in nd.get("connections", {}).items():
                    new_edges.append({"source": nid, "target": tgt, "port": int(prt)})
            # Restore edges list if present (web format)
            if not is_ppv_format:
                for e in design.get("edges", []):
                    src, tgt, prt = e.get("source"), e.get("target"), int(e.get("port", 0))
                    if src and tgt:
                        new_edges.append({"source": src, "target": tgt, "port": prt})
                # Deduplicate
                seen = set()
                deduped = []
                for e in new_edges:
                    k = (e["source"], e["target"], e["port"])
                    if k not in seen:
                        seen.add(k); deduped.append(e)
                new_edges = deduped
            # Restore experiments embedded in the flow file
            loaded_exps = design.get("experiments", {})
            exp_items = _exp_list_html(loaded_exps)
            elems = _build_elements(new_nodes, new_edges)
            ppv_note = " [PPV format — positions converted]" if is_ppv_format else ""
            _log(f"Loaded: {load_fname} ({len(new_nodes)} nodes, "
                 f"{len(loaded_exps)} experiments){ppv_note}")
            return (new_nodes, new_edges, new_ctr, elems, _node_list_html(new_nodes),
                    cmode, hint,
                    f"{len(new_nodes)} nodes \xb7 {len(new_edges)} edges",
                    log, f"Flow loaded: {load_fname}",
                    _toast(f"Loaded: {load_fname}", "success"),
                    loaded_exps if loaded_exps else no_update,
                    exp_items if loaded_exps else no_update)
        except Exception as exc:
            _log(f"Load error: {exc}")
            return (no_update, no_update, no_update, no_update, no_update,
                    cmode, hint, no_update, log, f"Load error: {exc}",
                    _toast(str(exc), "danger"),
                    no_update, no_update)

    # ── Node tap ──────────────────────────────────────────────────────────────
    if trigger == "ad-canvas" and tap_node:
        nid = tap_node.get("id")
        if not cmode.get("active"):
            return (no_update, no_update, no_update, no_update, no_update,
                    cmode, hint, no_update, log,
                    f"Selected: {nid}  ({tap_node.get('type', '')})",
                    no_update, no_update, no_update)

        # Connect mode — first click sets source
        if cmode.get("pending") is None:
            new_cmode = {**cmode, "pending": nid}
            hint      = f"Source: {nid} \u2192 Click target"
            elems     = _build_elements(nodes, edges, pending_source=nid, canvas_pos=cpos)
            _log(f"Connect source: {nid}")
            return (nodes, edges, counter, elems, no_update,
                    new_cmode, hint, _stats(), log,
                    f"Connect mode: source = {nid}. Now click target.",
                    _toast(f"Source: {nid}. Click target node.", "info", 3000),
                    no_update, no_update)

        # Connect mode — second click creates edge
        src_id   = cmode["pending"]
        port_num = int(cmode.get("port", "0"))
        if nid == src_id:
            new_cmode = {**cmode, "pending": None}
            hint      = "Click source node \u2192"
            elems     = _build_elements(nodes, edges, canvas_pos=cpos)
            return (nodes, edges, counter, elems, no_update,
                    new_cmode, hint, _stats(), log, "Cancelled (same node).",
                    no_update, no_update, no_update)
        # Port uniqueness: each (source, port) can only connect to ONE target
        existing = [e for e in edges
                    if e["source"] == src_id and int(e.get("port", -1)) == port_num]
        if existing and existing[0]["target"] != nid:
            existing_tgt = existing[0]["target"]
            new_cmode = {**cmode, "pending": None}
            hint      = "Click source node \u2192"
            elems     = _build_elements(nodes, edges, canvas_pos=cpos)
            _log(f"Port P{port_num} of {src_id} already connected to {existing_tgt}")
            return (nodes, edges, counter, elems, no_update,
                    new_cmode, hint, _stats(), log,
                    f"P{port_num} of {src_id} already wired to {existing_tgt}. Remove it first.",
                    _toast(f"Port P{port_num} already used on {src_id}.", "warning"),
                    no_update, no_update)
        # Remove any exact duplicate then add
        edges = [e for e in edges
                 if not (e["source"] == src_id and e["target"] == nid
                         and int(e.get("port", -1)) == port_num)]
        edges.append({"source": src_id, "target": nid, "port": port_num})
        nodes[src_id].setdefault("connections", {})[str(port_num)] = nid
        new_cmode = {**cmode, "pending": None}
        hint      = "Click source node \u2192"
        elems     = _build_elements(nodes, edges, canvas_pos=cpos)
        lbl       = _PORT_LABELS.get(port_num, "")
        _log(f"Connected {src_id}\u2192{nid} P{port_num}:{lbl}")
        return (nodes, edges, counter, elems, _node_list_html(nodes),
                new_cmode, hint, _stats(), log,
                f"Connected {src_id} \u2192 {nid} (P{port_num}:{lbl})",
                _toast(f"{src_id} \u2192 {nid}", "success", 1500),
                no_update, no_update)

    return _no_change()


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
    State("ad-canvas",        "elements"),
    prevent_initial_call=True,
)
def apply_edit(n, node_id, name, exp, nodes, edges, cmode, cur_elements):
    if not node_id or node_id not in (nodes or {}):
        return no_update, no_update, no_update, _toast("No node selected.", "warning")
    nodes[node_id]["name"]       = name or node_id
    nodes[node_id]["experiment"] = exp or ""
    cpos  = _canvas_pos_map(cur_elements)
    elems = _build_elements(nodes, edges or [], (cmode or {}).get("pending"), cpos)
    return nodes, elems, _node_list_html(nodes), _toast(f"{node_id} updated.", "success", 1500)


@callback(
    Output("ad-download",        "data"),
    Output("ad-export-status",   "children"),
    Output("ad-toast",           "children", allow_duplicate=True),
    Output("ad-result-store",    "data"),
    Output("ad-validate-banner", "children"),
    Input("ad-save-btn",         "n_clicks"),
    Input("ad-export-btn",       "n_clicks"),
    Input("ad-validate-btn",     "n_clicks"),
    State("ad-nodes-store",      "data"),
    State("ad-edges-store",      "data"),
    State("ad-experiments-store","data"),
    State("ad-vid",              "value"),
    State("ad-bucket",           "value"),
    State("ad-com",              "value"),
    State("ad-ip",               "value"),
    State("ad-unit-flags",       "value"),
    State("ad-check-core",       "value"),
    State("ad-save-name",        "value"),
    State("ad-canvas",           "elements"),
    prevent_initial_call=True,
)
def save_or_export(save_c, export_c, validate_c,
                   nodes, edges, experiments,
                   vid, bucket, com, ip, flags, check_core, save_name,
                   cur_elements):
    trigger = ctx.triggered_id
    nodes   = nodes   or {}
    edges   = edges   or []
    # Capture latest drag positions from cytoscape before saving
    cpos = _canvas_pos_map(cur_elements)
    nodes_with_pos = {}
    for nid, nd in nodes.items():
        cp = cpos.get(nid)
        nodes_with_pos[nid] = {**nd,
                               "x": cp["x"] if cp else nd.get("x", 200),
                               "y": cp["y"] if cp else nd.get("y", 200)}

    def _unit_cfg():
        return {
            "Visual ID":  vid or "",
            "Bucket":     bucket or "",
            "COM Port":   com or "",
            "IP Address": ip or "",
            "600W Unit":  "600w" in (flags or []),
            "Check Core": int(check_core) if check_core not in (None, "", " ") else 0,
        }

    if trigger == "ad-validate-btn":
        errs, warns = _validate(nodes, edges, experiments or {})
        if errs:
            banner = dbc.Alert(
                [html.Strong("Validation Errors: "), html.Br()] +
                [html.Span(["\u274c ", e, html.Br()], style={"fontSize": "0.8rem"})
                 for e in errs] +
                ([html.Span(["\u26a0 ", w, html.Br()],
                             style={"fontSize": "0.8rem", "color": "#f39c12"})
                  for w in warns] if warns else []),
                color="danger", dismissable=True, is_open=True,
                style={"margin": "4px 8px", "padding": "6px 12px"},
            )
            return no_update, no_update, _toast(f"{len(errs)} error(s).", "danger"), no_update, banner
        banner = dbc.Alert(
            ["\u2713 Flow is valid!"] + (
                [html.Span([html.Br(), "\u26a0 " + w]) for w in warns]
                if warns else []
            ),
            color="success", dismissable=True, is_open=True,
            style={"margin": "4px 8px", "padding": "6px 12px"},
        )
        return (no_update, no_update, _toast("Flow valid.", "success", 2000),
                no_update, banner)

    if trigger == "ad-save-btn":
        if not nodes:
            return no_update, no_update, _toast("Nothing to save.", "warning"), no_update, no_update
        design = {
            "_format": "web",
            "nodes": nodes_with_pos, "edges": edges,
            "experiments": experiments or {},
            "unit_config": _unit_cfg(),
        }
        fname = (save_name or "flow_design.json")
        if not fname.endswith(".json"):
            fname += ".json"
        return (dcc.send_string(json.dumps(design, indent=2), fname),
                f"\u2713 Saved: {fname}",
                _toast(f"Saved: {fname}", "success"), None, no_update)

    if trigger == "ad-export-btn":
        errs, _ = _validate(nodes_with_pos, edges, experiments or {})
        if errs:
            return (no_update, no_update,
                    _toast("Fix validation errors first.", "danger"), no_update, no_update)
        unit_cfg = _unit_cfg()
        enriched = {}
        for nid, nd in nodes_with_pos.items():
            en = nd.get("experiment")
            if en and en in (experiments or {}):
                entry = dict(experiments[en])
                entry.update({k: v for k, v in unit_cfg.items()
                              if v not in ("", False, None)})
                enriched[en] = entry
        zb  = _build_export_zip(nodes_with_pos, edges, enriched, unit_cfg)
        ts  = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        fn  = f"FrameworkAutomation_{ts}.zip"
        b64 = base64.b64encode(zb).decode()
        return (dcc.send_bytes(zb, fn),
                f"\u2713 Exported: {fn}",
                _toast(f"Exported {fn}", "success"), b64, no_update)

    return no_update, no_update, no_update, no_update, no_update


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
            html.Span(info.get("symbol", "\u25cf"),
                      style={"color": info["color"], "marginRight": "4px",
                             "fontSize": "0.85rem"}),
            html.Span(f"{nid}: {info['label']}{exp_tag}" +
                      (f" \xb7{nc}" if nc else ""),
                      style={"color": "#c0d0e0", "fontSize": "0.73rem", "flex": "1"}),
            dbc.Button("\u270f", id={"type": "ad-edit-node-btn", "index": nid},
                       size="sm", n_clicks=0,
                       style={"width": "22px", "height": "20px", "padding": "0",
                              "fontSize": "0.7rem", "lineHeight": "1",
                              "borderColor": ACCENT, "color": ACCENT,
                              "backgroundColor": "transparent",
                              "flexShrink": 0},
                       outline=True),
        ], style={"display": "flex", "alignItems": "center", "gap": "2px",
                  "marginBottom": "2px", "lineHeight": "1.3"}))
    return rows


def _exp_list_html(experiments):
    """Build the Experiments panel content — bullet list with Edit ✏ button per entry."""
    if not experiments:
        return [html.Span("No experiments loaded.",
                          style={"color": "#3a4a5a", "fontSize": "0.74rem"})]
    rows = []
    for name in list(experiments.keys())[:50]:
        rows.append(html.Div([
            html.Span("\u2022", style={"color": ACCENT, "marginRight": "4px",
                                       "fontSize": "0.8rem"}),
            html.Span(name, style={"color": "#c0d0e0", "fontSize": "0.73rem", "flex": "1",
                                   "overflow": "hidden", "textOverflow": "ellipsis",
                                   "whiteSpace": "nowrap"}),
            dbc.Button("\u270f",
                       id={"type": "ad-edit-exp-btn", "index": name},
                       size="sm", n_clicks=0,
                       style={"width": "22px", "height": "20px", "padding": "0",
                              "fontSize": "0.7rem", "lineHeight": "1",
                              "borderColor": "#7a9a88", "color": "#7a9a88",
                              "backgroundColor": "transparent", "flexShrink": 0},
                       outline=True),
        ], style={"display": "flex", "alignItems": "center", "gap": "2px",
                  "marginBottom": "2px", "lineHeight": "1.3"}))
    if len(experiments) > 50:
        rows.append(html.Div(f"\u2026{len(experiments)-50} more",
                             style={"color": "#4a5a6a", "fontSize": "0.7rem"}))
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
        nodes[nid]["x"] = 200 + lvl * 230
        nodes[nid]["y"] = 130 + level_x[lvl] * 175
        level_x[lvl]   += 1
        for e in edges:
            if e["source"] == nid:
                queue.append((e["target"], lvl + 1))
    for nid in nodes:
        if nid not in visited:
            lvl = max(visited.values(), default=0) + 1
            level_x.setdefault(lvl, 0)
            nodes[nid]["x"] = 200 + lvl * 230
            nodes[nid]["y"] = 130 + level_x[lvl] * 175
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
    # Save positions in PPV-compatible format (top-left, 150×100 node size)
    # cytoscape center → ppv top-left: subtract half of original PPV node size
    pos = {nid: {"x": nd["x"] - 75, "y": nd["y"] - 50} for nid, nd in nodes.items()}
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


# ── Edit Modal callbacks ───────────────────────────────────────────────────────

@callback(
    Output("ad-edit-modal",        "is_open"),
    Output("ad-modal-title",       "children"),
    Output("ad-modal-name",        "value"),
    Output("ad-modal-exp",         "options"),
    Output("ad-modal-exp",         "value"),
    Output("ad-modal-connections", "children"),
    Output("ad-modal-node",        "data"),
    Input({"type": "ad-edit-node-btn", "index": ALL}, "n_clicks"),
    Input("ad-modal-close",        "n_clicks"),
    Input("ad-modal-apply",        "n_clicks"),
    State("ad-nodes-store",        "data"),
    State("ad-experiments-store",  "data"),
    prevent_initial_call=True,
)
def toggle_edit_modal(edit_clicks, close_n, apply_n,
                      nodes, experiments):
    trigger = ctx.triggered_id
    # Close button or Apply button closes modal
    if trigger in ("ad-modal-close", "ad-modal-apply"):
        return False, no_update, no_update, no_update, no_update, no_update, no_update
    # Pattern-match edit button — guard: ignore if all clicks are 0 (initial render)
    if isinstance(trigger, dict) and trigger.get("type") == "ad-edit-node-btn":
        if not any((c or 0) > 0 for c in (edit_clicks or [])):
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update
        nid = trigger["index"]
        nd  = (nodes or {}).get(nid)
        if not nd:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update
        info     = _TYPE_MAP.get(nd["type"], {"label": nd["type"], "color": ACCENT})
        exp_opts = [{"label": "\u2014 none \u2014", "value": ""}] + \
                   [{"label": k, "value": k} for k in (experiments or {}).keys()]
        conn_rows = []
        for p, t in nd.get("connections", {}).items():
            pi = int(p)
            conn_rows.append(html.Span(
                f"P{pi}:{_PORT_LABELS.get(pi,'?')} \u2192 {t}  ",
                style={"color": _PORT_COLORS.get(pi, "#aaa"), "fontSize": "0.72rem",
                       "marginRight": "4px"},
            ))
        conn_info = conn_rows or html.Span("No connections.",
                                           style={"color": "#3a4a5a", "fontSize": "0.72rem"})
        title = [
            html.Span(f"{nid} ", style={"color": info.get("color", ACCENT), "fontWeight": "700"}),
            html.Span(f"— {info['label']}",
                      style={"color": "#7a9a88", "fontSize": "0.84rem"}),
        ]
        return True, title, nd.get("name", nid), exp_opts, nd.get("experiment", ""), conn_info, nid
    return no_update, no_update, no_update, no_update, no_update, no_update, no_update


@callback(
    Output("ad-nodes-store",  "data",     allow_duplicate=True),
    Output("ad-canvas",       "elements", allow_duplicate=True),
    Output("ad-node-list",    "children", allow_duplicate=True),
    Output("ad-node-editor",  "children", allow_duplicate=True),
    Output("ad-toast",        "children", allow_duplicate=True),
    Input("ad-modal-apply",   "n_clicks"),
    State("ad-modal-node",    "data"),
    State("ad-modal-name",    "value"),
    State("ad-modal-exp",     "value"),
    State("ad-nodes-store",   "data"),
    State("ad-edges-store",   "data"),
    State("ad-connect-mode",  "data"),
    State("ad-canvas",        "elements"),
    State("ad-experiments-store", "data"),
    prevent_initial_call=True,
)
def apply_modal_edit(n, node_id, name, exp, nodes, edges, cmode,
                     cur_elements, experiments):
    if not n or not node_id or node_id not in (nodes or {}):
        return no_update, no_update, no_update, no_update, no_update
    nodes[node_id]["name"]       = name or node_id
    nodes[node_id]["experiment"] = exp or ""
    cpos  = _canvas_pos_map(cur_elements)
    elems = _build_elements(nodes, edges or [], (cmode or {}).get("pending"), cpos)
    # Refresh inline Node Editor panel too
    nd   = nodes[node_id]
    info = _TYPE_MAP.get(nd["type"], {"label": nd["type"], "color": "#555"})
    exp_opts = [{"label": "\u2014 none \u2014", "value": ""}] + \
               [{"label": k, "value": k} for k in (experiments or {}).keys()]
    conn_rows = []
    for p, t in nd.get("connections", {}).items():
        pi = int(p)
        conn_rows.append(html.Span(
            f"P{pi}:{_PORT_LABELS.get(pi,'?')} \u2192 {t}  ",
            style={"color": _PORT_COLORS.get(pi, "#aaa"),
                   "fontSize": "0.7rem", "marginRight": "4px"},
        ))
    editor_body = html.Div([
        html.Span(node_id, style={"color": info.get("color", ACCENT), "fontWeight": "700",
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
    ])
    return (nodes, elems, _node_list_html(nodes), editor_body,
            _toast(f"{node_id} updated.", "success", 1500))


# ── Experiment Editor Modal callbacks ─────────────────────────────────────────

@callback(
    Output("ad-exp-editor-modal",     "is_open"),
    Output("ad-exp-editor-title",     "children"),
    Output("ad-exp-editor-name",      "value"),
    Output("ad-exp-editor-fields",    "children"),
    Output("ad-exp-editor-orig-name", "data"),
    Input({"type": "ad-edit-exp-btn", "index": ALL}, "n_clicks"),
    Input("ad-exp-editor-close",      "n_clicks"),
    Input("ad-exp-editor-save",       "n_clicks"),
    Input("ad-exp-editor-save-new",   "n_clicks"),
    State("ad-experiments-store",     "data"),
    prevent_initial_call=True,
)
def toggle_exp_editor(edit_clicks, close_n, save_n, save_new_n, experiments):
    trigger = ctx.triggered_id
    if trigger in ("ad-exp-editor-close", "ad-exp-editor-save",
                   "ad-exp-editor-save-new"):
        return False, no_update, no_update, no_update, no_update
    if isinstance(trigger, dict) and trigger.get("type") == "ad-edit-exp-btn":
        if not any((c or 0) > 0 for c in (edit_clicks or [])):
            return no_update, no_update, no_update, no_update, no_update
        exp_name = trigger["index"]
        exp_data = (experiments or {}).get(exp_name, {})
        # Build field rows (key-value editable form)
        rows = []
        for i, (k, v) in enumerate(exp_data.items()):
            rows.append(html.Div([
                html.Label(str(k), style={**_LS, "width": "200px", "minWidth": "200px"}),
                dbc.Input(
                    id={"type": "ad-exp-field", "index": str(k)},
                    value=str(v) if v is not None else "",
                    type="text", className="mb-1",
                    style={**_IS, "height": "26px", "fontSize": "0.75rem"},
                ),
            ], style={"display": "flex", "alignItems": "center", "gap": "8px",
                      "marginBottom": "3px"}))
        if not rows:
            rows = [html.Span("No fields in this experiment.",
                              style={"color": "#3a4a5a", "fontSize": "0.74rem"})]
        title = [
            html.Span(exp_name, style={"color": ACCENT, "fontWeight": "700"}),
            html.Span(" — Experiment Editor",
                      style={"color": "#7a9a88", "fontSize": "0.84rem"}),
        ]
        return True, title, exp_name, rows, exp_name
    return no_update, no_update, no_update, no_update, no_update


@callback(
    Output("ad-experiments-store", "data",     allow_duplicate=True),
    Output("ad-exp-list",          "children", allow_duplicate=True),
    Output("ad-toast",             "children", allow_duplicate=True),
    Output("ad-exp-editor-modal",  "is_open",  allow_duplicate=True),
    Input("ad-exp-editor-save",     "n_clicks"),
    Input("ad-exp-editor-save-new", "n_clicks"),
    State("ad-exp-editor-orig-name",   "data"),
    State("ad-exp-editor-name",        "value"),
    State({"type": "ad-exp-field", "index": ALL}, "value"),
    State({"type": "ad-exp-field", "index": ALL}, "id"),
    State("ad-experiments-store",      "data"),
    prevent_initial_call=True,
)
def save_exp_edit(save_n, save_new_n, orig_name, new_name, field_values,
                  field_ids, experiments):
    trigger = ctx.triggered_id
    if trigger not in ("ad-exp-editor-save", "ad-exp-editor-save-new"):
        return no_update, no_update, no_update, no_update
    if not orig_name:
        return no_update, no_update, _toast("No experiment selected.", "warning"), False
    experiments = dict(experiments or {})
    # Build updated experiment data
    updated = {}
    for fid, fval in zip(field_ids or [], field_values or []):
        updated[fid["index"]] = fval or ""
    save_name = (new_name or orig_name).strip() or orig_name
    if trigger == "ad-exp-editor-save":
        # Overwrite original (possibly with renamed key)
        if save_name != orig_name and orig_name in experiments:
            del experiments[orig_name]
        experiments[save_name] = updated
        msg = f"Saved experiment: {save_name}"
    else:
        # Save as new — generate unique name
        base = save_name
        suffix = 1
        while save_name in experiments:
            save_name = f"{base}_Copy{suffix}"
            suffix += 1
        experiments[save_name] = updated
        msg = f"Saved new experiment: {save_name}"
    return (experiments, _exp_list_html(experiments),
            _toast(msg, "success", 2500), False)
