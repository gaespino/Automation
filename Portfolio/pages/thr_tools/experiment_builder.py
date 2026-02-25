"""
Experiment Builder
==================
Build experiment configuration files with per-product field enabling.
Reads product-specific config from THRTools/configs/{product}ControlPanelConfig.json
"""
import logging
import json
import os
import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

dash.register_page(
    __name__,
    path='/thr-tools/experiment-builder',
    name='Experiment Builder',
    title='Experiment Builder'
)

ACCENT = "#36d7b7"

_PRODUCTS = ["GNR", "CWF", "DMR", "SRF"]
_CONFIGS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'THRTools', 'configs')

# ── helpers ────────────────────────────────────────────────────────────────────

def _load_product_config(product: str) -> dict:
    """Load ControlPanelConfig for a product, returns {} on failure."""
    path = os.path.join(_CONFIGS_DIR, f"{product}ControlPanelConfig.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _field_row(label: str, field_id: str, value="", placeholder="", disabled=False, options=None):
    """Render a single form row: label + input or select."""
    if options:
        return dbc.Row([
            dbc.Col(html.Label(label, style={"color": "#a0a0a0", "fontSize": "0.83rem"}), width=4),
            dbc.Col(
                dbc.Select(
                    id=field_id,
                    options=[{"label": o, "value": o} for o in options],
                    value=value,
                    disabled=disabled,
                    style={"backgroundColor": "#1a1d26", "color": "#e0e0e0" if not disabled else "#555",
                           "border": "1px solid rgba(255,255,255,0.1)", "fontSize": "0.85rem"}
                ), width=8
            )
        ], className="mb-2")
    return dbc.Row([
        dbc.Col(html.Label(label, style={"color": "#a0a0a0", "fontSize": "0.83rem"}), width=4),
        dbc.Col(
            dbc.Input(
                id=field_id, type="text", value=value, placeholder=placeholder,
                disabled=disabled,
                style={"backgroundColor": "#1a1d26", "color": "#e0e0e0" if not disabled else "#555",
                       "border": "1px solid rgba(255,255,255,0.1)", "fontSize": "0.85rem"}
            ), width=8
        )
    ], className="mb-2")


# ── layout ─────────────────────────────────────────────────────────────────────

layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="eb-toast"),
    dcc.Download(id="eb-download"),
    dcc.Store(id="eb-experiments-store", data=[]),

    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-beaker me-2", style={"color": ACCENT}),
            html.Span("Experiment Builder",
                      style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P("Build multi-experiment JSON configurations with per-product field enabling.",
               style={"color": "#a0a0a0", "fontSize": "0.9rem"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        # ── Left: configuration form ─────────────────────────────────────────
        dbc.Col(md=5, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Experiment Parameters", className="mb-3", style={"color": ACCENT}),

                dbc.Row([
                    dbc.Col([
                        html.Label("Product", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                        dbc.Select(
                            id="eb-product",
                            options=[{"label": p, "value": p} for p in _PRODUCTS],
                            value="GNR",
                            style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                   "border": "1px solid rgba(255,255,255,0.1)"}
                        ),
                    ], width=6),
                    dbc.Col([
                        html.Label("Environment", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                        dbc.Select(
                            id="eb-environment",
                            options=[{"label": e, "value": e}
                                     for e in ["SLT", "CHx", "SORT", "CLASS", "FINAL"]],
                            value="SLT",
                            style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                   "border": "1px solid rgba(255,255,255,0.1)"}
                        ),
                    ], width=6),
                ], className="mb-3"),

                html.Div(id="eb-dynamic-fields", children=[
                    _field_row("Experiment Name", "eb-name", placeholder="e.g. GNR_SLT_Mesh"),
                    _field_row("VID", "eb-vid", placeholder="0x1234"),
                    _field_row("WW", "eb-ww", placeholder="2026WW01"),
                    _field_row("Bucket", "eb-bucket", placeholder="3STRIKE"),
                    _field_row("Site", "eb-site", placeholder="SRF1"),
                    _field_row("Lots", "eb-lots", placeholder="AABBCC"),
                    _field_row("Script Version", "eb-script-ver", placeholder="1.0.0"),
                    _field_row("Notes", "eb-notes", placeholder="Optional"),
                ]),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                dbc.Row([
                    dbc.Col(dbc.Button(
                        [html.I(className="bi bi-plus-circle me-2"), "Add Experiment"],
                        id="eb-add-btn", outline=True, className="w-100",
                        style={"borderColor": ACCENT, "color": ACCENT}
                    ), width=6),
                    dbc.Col(dbc.Button(
                        [html.I(className="bi bi-trash me-2"), "Clear All"],
                        id="eb-clear-btn", color="danger", outline=True, className="w-100",
                    ), width=6),
                ]),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                dbc.Button(
                    [html.I(className="bi bi-download me-2"), "Export JSON"],
                    id="eb-export-btn", outline=True, className="w-100",
                    style={"borderColor": ACCENT, "color": ACCENT}
                ),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                html.Label("Import JSON", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Upload(
                    id="eb-import",
                    children=html.Div(["Drop JSON or ", html.A("browse", style={"color": ACCENT})]),
                    multiple=False,
                    style={
                        "border": f"1px dashed {ACCENT}", "borderRadius": "6px",
                        "padding": "8px", "textAlign": "center",
                        "color": "#a0a0a0", "fontSize": "0.82rem",
                        "backgroundColor": "rgba(54,215,183,0.03)", "cursor": "pointer"
                    }
                ),
            ]), className="card-premium border-0"),
        ]),

        # ── Right: experiment list ────────────────────────────────────────────
        dbc.Col(md=7, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Experiment Queue", style={"color": ACCENT}, className="mb-3"),
                html.Div(id="eb-exp-list", children=[
                    dbc.Alert("No experiments yet. Fill the form and click Add Experiment.",
                              color="secondary", className="card-premium border-0 text-white")
                ])
            ]), className="card-premium border-0"),
        ]),
    ]),
])


# ── callbacks ──────────────────────────────────────────────────────────────────

@callback(
    Output("eb-dynamic-fields", "children"),
    Input("eb-product", "value"),
    prevent_initial_call=False
)
def update_fields(product):
    """Enable/disable fields based on product config."""
    cfg = _load_product_config(product or "GNR")
    enabled = set(cfg.get("enabled_fields", []) or [])

    def _disabled(key):
        return bool(enabled) and key not in enabled

    return [
        _field_row("Experiment Name", "eb-name", placeholder="e.g. GNR_SLT_Mesh",
                   disabled=_disabled("name")),
        _field_row("VID", "eb-vid", placeholder="0x1234", disabled=_disabled("vid")),
        _field_row("WW", "eb-ww", placeholder="2026WW01", disabled=_disabled("ww")),
        _field_row("Bucket", "eb-bucket", placeholder="3STRIKE", disabled=_disabled("bucket")),
        _field_row("Site", "eb-site", placeholder="SRF1", disabled=_disabled("site")),
        _field_row("Lots", "eb-lots", placeholder="AABBCC", disabled=_disabled("lots")),
        _field_row("Script Version", "eb-script-ver", placeholder="1.0.0",
                   disabled=_disabled("script_version")),
        _field_row("Notes", "eb-notes", placeholder="Optional", disabled=_disabled("notes")),
    ]


@callback(
    Output("eb-experiments-store", "data"),
    Output("eb-toast", "children"),
    Input("eb-add-btn", "n_clicks"),
    Input("eb-clear-btn", "n_clicks"),
    Input("eb-import", "contents"),
    State("eb-experiments-store", "data"),
    State("eb-product", "value"),
    State("eb-environment", "value"),
    State("eb-name", "value"),
    State("eb-vid", "value"),
    State("eb-ww", "value"),
    State("eb-bucket", "value"),
    State("eb-site", "value"),
    State("eb-lots", "value"),
    State("eb-script-ver", "value"),
    State("eb-notes", "value"),
    prevent_initial_call=True
)
def manage_experiments(add_clicks, clear_clicks, import_content,
                       current, product, environment,
                       name, vid, ww, bucket, site, lots, script_ver, notes):
    from dash import ctx
    trigger = ctx.triggered_id

    if trigger == "eb-clear-btn":
        return [], dbc.Toast("Experiments cleared.", icon="info", duration=2500, is_open=True,
                             style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                             className="toast-custom")

    if trigger == "eb-import" and import_content:
        try:
            import base64
            _, data = import_content.split(',')
            imported = json.loads(base64.b64decode(data).decode('utf-8'))
            exps = imported if isinstance(imported, list) else [imported]
            return exps, dbc.Toast(f"Imported {len(exps)} experiment(s).", icon="success",
                                   duration=3000, is_open=True,
                                   style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                                   className="toast-custom")
        except Exception as e:
            return no_update, dbc.Toast(f"Import error: {e}", icon="danger", duration=4000,
                                        is_open=True,
                                        style={"position": "fixed", "top": 20, "right": 20,
                                               "zIndex": 9999}, className="toast-custom")

    # Add experiment
    entry = {k: v for k, v in {
        "product": product, "environment": environment,
        "name": name, "vid": vid, "ww": ww, "bucket": bucket,
        "site": site, "lots": lots, "script_version": script_ver, "notes": notes
    }.items() if v}

    updated = list(current or []) + [entry]
    return updated, dbc.Toast(f"Added experiment #{len(updated)}.", icon="success", duration=2500,
                              is_open=True,
                              style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                              className="toast-custom")


@callback(
    Output("eb-exp-list", "children"),
    Input("eb-experiments-store", "data"),
)
def render_list(experiments):
    if not experiments:
        return dbc.Alert("No experiments yet. Fill the form and click Add Experiment.",
                         color="secondary", className="card-premium border-0 text-white")

    rows = []
    for i, exp in enumerate(experiments, 1):
        rows.append(dbc.Card(dbc.CardBody([
            dbc.Row([
                dbc.Col(html.Span(f"#{i} — {exp.get('product', '?')} / {exp.get('environment', '?')}",
                                  style={"color": ACCENT, "fontWeight": "600",
                                         "fontSize": "0.9rem"}), width=10),
            ], className="mb-1"),
            html.Div([
                html.Span(f"{k}: ", style={"color": "#a0a0a0", "fontSize": "0.8rem"}),
                html.Span(str(v), style={"color": "#e0e0e0", "fontSize": "0.8rem"}),
                html.Span("  "),
            ] for k, v in exp.items() if k not in ("product", "environment") and v)
        ]), className="card-premium border-0 mb-2",
            style={"borderLeft": f"3px solid {ACCENT}"}))

    return rows


@callback(
    Output("eb-download", "data"),
    Input("eb-export-btn", "n_clicks"),
    State("eb-experiments-store", "data"),
    prevent_initial_call=True
)
def export_json(n_clicks, experiments):
    if not experiments:
        return no_update
    payload = json.dumps(experiments, indent=2)
    return dcc.send_string(payload, "experiments.json")
