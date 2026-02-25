"""
DPMB Requests
==============
Interface for Bucketer data requests through DPMB API.
Calls THRTools/api/dpmb.py backend (dpmb class, not GUI).
"""
import logging
import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

logger = logging.getLogger(__name__)

dash.register_page(
    __name__,
    path='/thr-tools/dpmb',
    name='DPMB Requests',
    title='DPMB Requests'
)

ACCENT = "#7000ff"
PRODUCTS = ['GNR', 'CWF', 'DMR']
OPERATIONS = ['Bucketing', 'UoD Bucketing', 'Final Bucketing', 'Final UoD Bucketing']

layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="dpmb-toast"),

    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-diagram-3 me-2", style={"color": ACCENT}),
            html.Span("DPMB Requests", style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P("Submit Visual ID bucketing jobs through the DPMB API.",
               style={"color": "#a0a0a0", "fontSize": "0.9rem"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        dbc.Col(md=4, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Request Configuration", className="mb-3", style={"color": ACCENT}),

                html.Label("Product", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Dropdown(id="dpmb-product",
                             options=[{'label': p, 'value': p} for p in PRODUCTS],
                             value='GNR', clearable=False, className="mb-3"),

                html.Label("Visual ID(s) — one per line", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Textarea(id="dpmb-vids", placeholder="74BJ554200224\n74WX726800134",
                             rows=5, className="mb-3",
                             style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                    "border": "1px solid rgba(255,255,255,0.1)"}),

                dbc.Row([
                    dbc.Col([
                        html.Label("Start WW", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                        dbc.Input(id="dpmb-start-ww", placeholder="2026WW01", type="text",
                                  className="mb-3",
                                  style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                         "border": "1px solid rgba(255,255,255,0.1)"}),
                    ], width=6),
                    dbc.Col([
                        html.Label("End WW", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                        dbc.Input(id="dpmb-end-ww", placeholder="2026WW06", type="text",
                                  className="mb-3",
                                  style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                         "border": "1px solid rgba(255,255,255,0.1)"}),
                    ], width=6),
                ]),

                html.Label("Operations", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Dropdown(id="dpmb-ops",
                             options=[{'label': o, 'value': o} for o in OPERATIONS],
                             value=['Bucketing'], multi=True, className="mb-3"),

                html.Label("Username", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Input(id="dpmb-user", placeholder="intel_username", type="text",
                          className="mb-3",
                          style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                 "border": "1px solid rgba(255,255,255,0.1)"}),

                dbc.Button(
                    [html.I(className="bi bi-send me-2"), "Submit Request"],
                    id="dpmb-submit-btn",
                    color="primary", outline=True, className="w-100",
                    style={"borderColor": ACCENT, "color": ACCENT}
                ),
                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),
                dbc.Button(
                    [html.I(className="bi bi-arrow-clockwise me-2"), "Check Status"],
                    id="dpmb-status-btn",
                    color="secondary", outline=True, className="w-100",
                    style={"borderColor": "#a0a0a0", "color": "#a0a0a0"}
                ),
            ]), className="card-premium border-0"),
        ]),

        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Response", style={"color": ACCENT}, className="mb-3"),
                html.Div(id="dpmb-results", children=[
                    dbc.Alert("Fill in the form and submit a request.",
                              color="secondary", className="card-premium border-0 text-white")
                ])
            ]), className="card-premium border-0"),
        ]),
    ]),
])


@callback(
    Output("dpmb-results", "children"),
    Output("dpmb-toast", "children"),
    Input("dpmb-submit-btn", "n_clicks"),
    Input("dpmb-status-btn", "n_clicks"),
    State("dpmb-vids", "value"),
    State("dpmb-user", "value"),
    State("dpmb-start-ww", "value"),
    State("dpmb-end-ww", "value"),
    State("dpmb-product", "value"),
    State("dpmb-ops", "value"),
    prevent_initial_call=True
)
def submit_dpmb(n_sub, n_stat, vids_raw, user, start_ww, end_ww, product, ops):
    from dash import ctx as dash_ctx
    trigger = dash_ctx.triggered_id

    if not vids_raw:
        return no_update, dbc.Toast("Enter Visual ID(s).", icon="warning", duration=3000, is_open=True,
                                     style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                                     className="toast-custom")
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from THRTools.api.dpmb import dpmb

        vid_list = [v.strip() for v in vids_raw.strip().splitlines() if v.strip()]
        delta = False

        client = dpmb(
            vidlist=vid_list,
            user=user or "",
            startWW=start_ww or "",
            endWW=end_ww or "",
            product=product,
            operations=ops or ['Bucketing'],
            delta=delta
        )

        if trigger == "dpmb-submit-btn":
            client.request()
            msg = f"Request submitted for {len(vid_list)} VID(s)."
            result_content = html.Div([
                html.P(f"✓ {msg}", style={"color": "#00ff9d"}),
                html.P(f"Product: {product} | WW: {start_ww} → {end_ww}",
                       style={"color": "#a0a0a0", "fontSize": "0.88rem"}),
                html.P(f"VIDs: {', '.join(vid_list[:5])}{'...' if len(vid_list) > 5 else ''}",
                       style={"color": "#a0a0a0", "fontSize": "0.88rem"})
            ])
        else:
            client.status()
            msg = "Status checked."
            result_content = html.P("Status request sent — check server logs.", style={"color": "#a0a0a0"})

        toast = dbc.Toast(msg, icon="success", duration=4000, is_open=True,
                          style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                          className="toast-custom")
        return result_content, toast

    except Exception as e:
        logger.exception("DPMB error")
        return no_update, dbc.Toast(f"Error: {str(e)}", icon="danger", duration=5000, is_open=True,
                                     style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                                     className="toast-custom")
