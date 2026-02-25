"""
Fuse File Generator
====================
Generate fuse configuration files from CSV fuse definitions.
Faithfully replicates PPV/gui/fusefileui.FuseFileUI.

Key difference from original: the fuse CSV files are already bundled in
THRTools/configs/fuses/{product}/ — no file upload required.
Workflow:
  1. Select Product → auto-loads configs/fuses/{product}/ CSVs
  2. Search/filter by description, instance, IP
  3. Select fuses using the checkbox table (Select All / Clear All / Select Filtered)
  4. Generate Fuse File → download .fuse output
"""
import logging
import os
import sys
import json
import datetime
import dash
from dash import html, dcc, Input, Output, State, callback, no_update, ctx
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

dash.register_page(
    __name__,
    path='/thr-tools/fuse-generator',
    name='Fuse File Generator',
    title='Fuse File Generator'
)

ACCENT = "#ff9f45"
_PRODUCTS = ["GNR", "CWF", "DMR"]

# Key columns to display in the table (matching original FuseFileUI)
_DISPLAY_COLS = ["original_name", "ip_name", "description", "numbits", "default",
                 "Group", "Category", "IP_Origin"]

_INPUT_STYLE = {
    "backgroundColor": "#1a1d26", "color": "#e0e0e0",
    "border": "1px solid rgba(255,255,255,0.1)", "fontSize": "0.85rem"
}
_LABEL_STYLE = {"color": "#a0a0a0", "fontSize": "0.8rem"}


layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="fg-toast"),
    dcc.Download(id="fg-download"),
    dcc.Store(id="fg-fuse-store", data={}),
    dcc.Store(id="fg-selected-store", data=[]),

    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-cpu me-2", style={"color": ACCENT}),
            html.Span("Fuse File Generator",
                      style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P(
            "Generate fuse configuration files from product CSV definitions. "
            "Fuse data is auto-loaded from configs/fuses/{product}/.",
            style={"color": "#a0a0a0", "fontSize": "0.9rem"}
        ),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        # ── Left: configuration ───────────────────────────────────────────────
        dbc.Col(md=3, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Configuration", className="mb-3", style={"color": ACCENT}),

                html.Label("Product", style=_LABEL_STYLE),
                dbc.Select(
                    id="fg-product",
                    options=[{"label": p, "value": p} for p in _PRODUCTS],
                    value="GNR",
                    className="mb-2",
                    style=_INPUT_STYLE
                ),

                html.Div(id="fg-config-info",
                         style={"color": "#a0a0a0", "fontSize": "0.75rem", "marginBottom": "8px"}),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),
                html.H6("Search & Filter", style={"color": "#c0c0c0", "fontSize": "0.85rem"}, className="mb-2"),

                html.Label("Search (name/description)", style=_LABEL_STYLE),
                dbc.Input(id="fg-search", placeholder="e.g. bgr, trim, enable",
                          type="text", className="mb-2", style=_INPUT_STYLE),

                html.Label("Filter by IP", style=_LABEL_STYLE),
                dbc.Select(id="fg-filter-ip", options=[{"label": "All", "value": ""}],
                           value="", className="mb-2", style=_INPUT_STYLE),

                html.Label("Filter by Group", style=_LABEL_STYLE),
                dbc.Select(id="fg-filter-group", options=[{"label": "All", "value": ""}],
                           value="", className="mb-3", style=_INPUT_STYLE),

                dbc.Row([
                    dbc.Col(dbc.Button("Apply Filters", id="fg-filter-btn",
                                       outline=True, className="w-100",
                                       style={"borderColor": ACCENT, "color": ACCENT}), width=12),
                ], className="mb-2"),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),
                html.H6("Output", style={"color": "#c0c0c0", "fontSize": "0.85rem"}, className="mb-2"),

                html.Label("Output Filename", style=_LABEL_STYLE),
                dbc.Input(id="fg-output-name", placeholder="output.fuse", type="text",
                          className="mb-3", style=_INPUT_STYLE),

                dbc.Button(
                    [html.I(className="bi bi-gear-wide-connected me-2"), "Generate Fuse File"],
                    id="fg-gen-btn",
                    color="warning", outline=True, className="w-100",
                    style={"borderColor": ACCENT, "color": ACCENT}, disabled=True
                ),
                html.Div(id="fg-gen-status", className="mt-2",
                         style={"color": "#a0a0a0", "fontSize": "0.8rem"}),

            ]), className="card-premium border-0"),
        ]),

        # ── Right: fuse table ─────────────────────────────────────────────────
        dbc.Col(md=9, children=[
            dbc.Card(dbc.CardBody([
                dbc.Row([
                    dbc.Col(html.H6("Fuse Selection", style={"color": ACCENT}), width=6),
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button("Select All",      id="fg-sel-all",     size="sm",
                                       outline=True, style={"borderColor": ACCENT, "color": ACCENT}),
                            dbc.Button("Clear All",       id="fg-clr-all",     size="sm",
                                       color="secondary", outline=True),
                            dbc.Button("Select Filtered", id="fg-sel-filtered",size="sm",
                                       outline=True, style={"borderColor": ACCENT, "color": ACCENT}),
                            dbc.Button("Clear Filtered",  id="fg-clr-filtered",size="sm",
                                       color="secondary", outline=True),
                        ], className="float-end"),
                    ], width=6),
                ], className="mb-2 align-items-center"),

                html.Div(id="fg-selection-info",
                         style={"color": "#a0a0a0", "fontSize": "0.78rem", "marginBottom": "6px"}),

                html.Div(id="fg-fuse-table", children=[
                    dbc.Alert("Select a product to load fuse data.",
                              color="secondary", className="card-premium border-0 text-white")
                ], style={"maxHeight": "550px", "overflowY": "auto"}),
            ]), className="card-premium border-0"),
        ]),
    ]),
])


# ── Callbacks ──────────────────────────────────────────────────────────────────

@callback(
    Output("fg-fuse-store", "data"),
    Output("fg-filter-ip", "options"),
    Output("fg-filter-group", "options"),
    Output("fg-config-info", "children"),
    Output("fg-gen-btn", "disabled"),
    Output("fg-toast", "children"),
    Input("fg-product", "value"),
    prevent_initial_call=True
)
def load_product(product):
    """Auto-load fuse data from configs/fuses/{product}/ when product changes."""
    try:
        _add_path()
        from THRTools.utils.fusefilegenerator import load_product_fuses

        gen = load_product_fuses(product)
        if gen is None or not gen.fuse_data:
            return ({}, [], [], f"No data loaded for {product}.", True,
                    _toast(f"No fuse data found for {product}.", "warning"))

        fuses = gen.fuse_data  # list of dicts
        n = len(fuses)

        # Build IP and Group filter options
        ips    = sorted({f.get("IP_Origin", "") for f in fuses if f.get("IP_Origin")})
        groups = sorted({f.get("Group", "")     for f in fuses if f.get("Group")})
        ip_opts    = [{"label": "All", "value": ""}] + [{"label": i, "value": i} for i in ips]
        group_opts = [{"label": "All", "value": ""}] + [{"label": g, "value": g} for g in groups]

        store = {"product": product, "fuses": fuses, "filtered_fuses": fuses}
        info = f"Loaded {n} fuses from {', '.join(gen.csv_files_loaded)}"

        return store, ip_opts, group_opts, info, False, _toast(f"Loaded {n} fuses.", "success", 2500)

    except Exception as e:
        logger.exception("Fuse load error")
        return ({}, [], [], str(e), True, _toast(f"Error loading fuses: {e}", "danger"))


@callback(
    Output("fg-fuse-store", "data", allow_duplicate=True),
    Output("fg-fuse-table", "children"),
    Output("fg-selection-info", "children"),
    Output("fg-selected-store", "data"),
    Input("fg-filter-btn",   "n_clicks"),
    Input("fg-sel-all",      "n_clicks"),
    Input("fg-clr-all",      "n_clicks"),
    Input("fg-sel-filtered", "n_clicks"),
    Input("fg-clr-filtered", "n_clicks"),
    Input({"type": "fg-fuse-check", "index": dash.ALL}, "value"),
    State("fg-fuse-store", "data"),
    State("fg-selected-store", "data"),
    State("fg-search", "value"),
    State("fg-filter-ip", "value"),
    State("fg-filter-group", "value"),
    prevent_initial_call=True
)
def update_table(filter_c, sel_all_c, clr_all_c, sel_filt_c, clr_filt_c,
                 check_vals, store, selected_ids,
                 search, ip_filter, group_filter):
    if not store or not store.get("fuses"):
        return no_update, no_update, no_update, no_update

    trigger = ctx.triggered_id
    all_fuses = store["fuses"]
    selected_set = set(selected_ids or [])

    # Apply filters
    filtered = all_fuses
    if search:
        sl = search.lower()
        filtered = [f for f in filtered if
                    sl in str(f.get("original_name", "")).lower() or
                    sl in str(f.get("description", "")).lower() or
                    sl in str(f.get("ip_name", "")).lower()]
    if ip_filter:
        filtered = [f for f in filtered if f.get("IP_Origin") == ip_filter]
    if group_filter:
        filtered = [f for f in filtered if f.get("Group") == group_filter]

    filtered_ids = [f["original_name"] for f in filtered]
    store["filtered_fuses"] = filtered

    # Handle selection actions
    if trigger == "fg-sel-all":
        selected_set = {f["original_name"] for f in all_fuses}
    elif trigger == "fg-clr-all":
        selected_set = set()
    elif trigger == "fg-sel-filtered":
        selected_set |= set(filtered_ids)
    elif trigger == "fg-clr-filtered":
        selected_set -= set(filtered_ids)
    elif isinstance(trigger, dict) and trigger.get("type") == "fg-fuse-check":
        # Individual checkbox toggled — rebuild from all checkbox states
        fuse_ids = [f["original_name"] for f in filtered]
        for fid, cv in zip(fuse_ids, check_vals):
            if cv:
                selected_set.add(fid)
            else:
                selected_set.discard(fid)

    table = _build_table(filtered, selected_set)
    info = f"Showing {len(filtered)} / {len(all_fuses)} fuses — {len(selected_set)} selected"
    return store, table, info, list(selected_set)


def _build_table(fuses, selected_ids):
    if not fuses:
        return dbc.Alert("No fuses match the current filter.",
                         color="secondary", className="card-premium border-0 text-white")

    selected_set = set(selected_ids)
    headers = ["✓", "Name", "IP", "Description", "Bits", "Default", "Group"]
    header_row = html.Tr([html.Th(h, style={"color": ACCENT, "fontSize": "0.8rem",
                                             "whiteSpace": "nowrap"}) for h in headers])
    rows = []
    for f in fuses[:500]:  # cap at 500 for performance
        fid = f.get("original_name", "")
        is_checked = fid in selected_set
        rows.append(html.Tr([
            html.Td(dbc.Checklist(
                id={"type": "fg-fuse-check", "index": fid},
                options=[{"label": "", "value": True}],
                value=[True] if is_checked else [],
                className="mb-0"
            ), style={"width": "40px"}),
            html.Td(html.Span(fid[:60], title=fid, style={"fontSize": "0.78rem", "color": "#e0e0e0",
                                                            "fontFamily": "monospace"})),
            html.Td(html.Span(str(f.get("ip_name", ""))[:20],
                              style={"fontSize": "0.78rem", "color": "#a0a0a0"})),
            html.Td(html.Span(str(f.get("description", ""))[:60],
                              title=str(f.get("description", "")),
                              style={"fontSize": "0.78rem", "color": "#c0c0c0"})),
            html.Td(html.Span(str(f.get("numbits", "")),
                              style={"fontSize": "0.78rem", "color": "#a0c0ff"})),
            html.Td(html.Span(str(f.get("default", "")),
                              style={"fontSize": "0.78rem", "color": "#a0c0a0"})),
            html.Td(html.Span(str(f.get("Group", ""))[:20],
                              style={"fontSize": "0.78rem", "color": "#a0a0a0"})),
        ]))
    return dbc.Table([html.Thead(header_row), html.Tbody(rows)],
                     bordered=False, hover=True,
                     style={"fontSize": "0.82rem", "color": "#e0e0e0"})


@callback(
    Output("fg-download", "data"),
    Output("fg-gen-status", "children"),
    Output("fg-toast", "children", allow_duplicate=True),
    Input("fg-gen-btn", "n_clicks"),
    State("fg-fuse-store", "data"),
    State("fg-selected-store", "data"),
    State("fg-output-name", "value"),
    prevent_initial_call=True
)
def generate_fuse_file(n_clicks, store, selected_ids, output_name):
    if not store or not store.get("fuses"):
        return no_update, no_update, _toast("Load fuse data first.", "warning")
    if not selected_ids:
        return no_update, no_update, _toast("Select at least one fuse.", "warning")

    try:
        _add_path()
        from THRTools.utils.fusefilegenerator import FuseFileGenerator
        import tempfile

        product = store.get("product", "GNR")
        all_fuses = store["fuses"]
        selected_set = set(selected_ids)
        selected_fuses = [f for f in all_fuses if f.get("original_name") in selected_set]

        gen = FuseFileGenerator(product=product)
        gen.fuse_data = all_fuses
        gen.product = product

        out_fname = output_name or f"{product}_fuses.fuse"
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, out_fname)
            gen.generate_fuse_file(
                selected_fuses=selected_fuses,
                ip_assignments={},
                output_file=out_path
            )
            with open(out_path, 'rb') as f:
                out_bytes = f.read()

        info = f"✓ Generated {len(selected_fuses)} fuses → {out_fname}"
        return (dcc.send_bytes(out_bytes, out_fname),
                info,
                _toast(f"Fuse file generated: {out_fname}", "success"))

    except Exception as e:
        logger.exception("Fuse generation error")
        return no_update, f"Error: {e}", _toast(f"Error: {e}", "danger", 6000)


def _add_path():
    root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if root not in sys.path:
        sys.path.insert(0, root)


def _toast(msg, icon, duration=4000):
    return dbc.Toast(
        msg, icon=icon, duration=duration, is_open=True,
        style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
        className="toast-custom"
    )
