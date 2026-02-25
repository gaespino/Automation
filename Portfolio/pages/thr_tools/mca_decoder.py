"""
MCA Single Decoder
===================
Decode individual MCA registers for CHA, LLC, CORE, MEMORY, IO, and First Error.
Calls THRTools/Decoder/decoder.py backend.
"""
import logging
import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

logger = logging.getLogger(__name__)

dash.register_page(
    __name__,
    path='/thr-tools/mca-decoder',
    name='MCA Single Decoder',
    title='MCA Single Decoder'
)

ACCENT = "#ff6b8a"
PRODUCTS = ['GNR', 'CWF', 'DMR']
ERROR_TYPES = ['CHA', 'LLC', 'CORE', 'MEMORY', 'IO', 'First Error', 'Port ID']

layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="mca-dec-toast"),

    # Header
    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-cpu me-2", style={"color": ACCENT}),
            html.Span("MCA Single Decoder", style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P("Decode individual MCA registers for CHA, LLC, CORE, MEMORY, IO, and First Error.",
               style={"color": "#a0a0a0", "fontSize": "0.9rem"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        # Left panel — inputs
        dbc.Col(md=4, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Configuration", className="card-header-text mb-3",
                        style={"color": ACCENT}),

                html.Label("Product", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Dropdown(
                    id="mca-dec-product",
                    options=[{'label': p, 'value': p} for p in PRODUCTS],
                    value='GNR', clearable=False,
                    className="mb-3"
                ),

                html.Label("Error Type", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Dropdown(
                    id="mca-dec-type",
                    options=[{'label': e, 'value': e} for e in ERROR_TYPES],
                    value='CHA', clearable=False,
                    className="mb-3"
                ),

                html.Label("MCA Register Value (hex)", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Input(
                    id="mca-dec-hex",
                    placeholder="e.g. 0xBE00000000800400",
                    type="text",
                    className="mb-1",
                    style={"backgroundColor": "#1a1d26", "color": "#e0e0e0", "border": "1px solid rgba(255,255,255,0.1)"}
                ),
                html.Small("Enter a single hex value or paste multiple on separate lines.",
                           style={"color": "#606070", "fontSize": "0.78rem"}),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)", "marginTop": "1rem"}),

                dbc.Button(
                    [html.I(className="bi bi-gear me-2"), "Decode"],
                    id="mca-dec-btn",
                    color="primary",
                    outline=True,
                    className="w-100",
                    style={"borderColor": ACCENT, "color": ACCENT}
                ),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                html.Label("Or upload a register file (.txt / .csv)",
                           style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Upload(
                    id="mca-dec-upload",
                    children=html.Div([
                        html.I(className="bi bi-upload me-2", style={"color": ACCENT}),
                        "Drop file or ", html.A("browse", style={"color": ACCENT})
                    ]),
                    className="mt-2",
                    style={
                        "border": f"1px dashed {ACCENT}", "borderRadius": "8px",
                        "padding": "12px", "textAlign": "center",
                        "color": "#a0a0a0", "fontSize": "0.85rem",
                        "backgroundColor": "rgba(255,107,138,0.04)", "cursor": "pointer"
                    }
                ),
            ]), className="card-premium border-0"),
        ]),

        # Right panel — results
        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                html.Div([
                    html.H6("Decode Results", style={"color": ACCENT, "display": "inline-block"}),
                    dbc.Button(
                        [html.I(className="bi bi-clipboard me-1"), "Copy"],
                        id="mca-dec-copy-btn", size="sm", outline=True,
                        style={"borderColor": "#a0a0a0", "color": "#a0a0a0", "float": "right", "marginTop": "-4px"}
                    ),
                ], className="mb-3"),

                html.Div(id="mca-dec-results", children=[
                    dbc.Alert("Enter a hex value and click Decode.",
                              color="secondary", className="card-premium border-0 text-white")
                ])
            ]), className="card-premium border-0"),
        ]),
    ]),
])


@callback(
    Output("mca-dec-results", "children"),
    Output("mca-dec-toast", "children"),
    Input("mca-dec-btn", "n_clicks"),
    State("mca-dec-hex", "value"),
    State("mca-dec-product", "value"),
    State("mca-dec-type", "value"),
    prevent_initial_call=True
)
def decode_mca(n_clicks, hex_val, product, error_type):
    if not hex_val:
        return no_update, dbc.Toast("Enter a hex value.", icon="warning", duration=3000, is_open=True,
                                     style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                                     className="toast-custom")
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from THRTools.Decoder.decoder import mcadata

        lines = [h.strip() for h in hex_val.strip().splitlines() if h.strip()]
        rows = []
        mca = mcadata(product)

        for raw in lines:
            # Normalize hex value
            val_str = raw.strip().lower().replace('0x', '')
            try:
                int_val = int(val_str, 16)
            except ValueError:
                rows.append({"Register": raw, "Field": "ERROR", "Value": "Invalid hex"})
                continue

            # Get decoded fields based on error type
            decode_map = {
                'CHA': getattr(mca, 'cha', None),
                'LLC': getattr(mca, 'llc', None),
                'CORE': getattr(mca, 'core', None),
                'MEMORY': getattr(mca, 'memory', None),
                'IO': getattr(mca, 'portid', None),
            }
            decoder_fn = decode_map.get(error_type)
            if decoder_fn:
                try:
                    result = decoder_fn()
                    if isinstance(result, dict):
                        for field, desc in result.items():
                            rows.append({"Register": raw, "Field": field, "Value": str(desc)})
                    else:
                        rows.append({"Register": raw, "Field": error_type, "Value": str(result)})
                except Exception as ex:
                    rows.append({"Register": raw, "Field": "ERROR", "Value": str(ex)})
            else:
                rows.append({"Register": raw, "Field": error_type, "Value": "Decoder not available for this type"})

        if not rows:
            return dbc.Alert("No results.", color="secondary", className="card-premium border-0 text-white"), no_update

        grid = dag.AgGrid(
            id="mca-dec-grid",
            rowData=rows,
            columnDefs=[
                {"field": "Register", "headerName": "Register", "width": 220},
                {"field": "Field", "headerName": "Field", "flex": 1},
                {"field": "Value", "headerName": "Value", "flex": 2},
            ],
            defaultColDef={"sortable": True, "filter": True, "resizable": True},
            className="ag-theme-alpine-dark",
            style={"height": "420px"},
        )
        return grid, no_update

    except Exception as e:
        logger.exception("MCA decode error")
        toast = dbc.Toast(f"Decode error: {str(e)}", icon="danger", duration=5000, is_open=True,
                          style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                          className="toast-custom")
        return no_update, toast
