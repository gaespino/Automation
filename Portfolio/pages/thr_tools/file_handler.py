"""
File Handler
=============
Merge and manage multiple data files efficiently.
Calls THRTools/utils/PPVReportMerger.py backend.
"""
import logging
import base64
import io
import os
import dash
from dash import html, dcc, Input, Output, State, callback, no_update, ctx
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

dash.register_page(
    __name__,
    path='/thr-tools/file-handler',
    name='File Handler',
    title='File Handler'
)

ACCENT = "#ffbd2e"

layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="fh-toast"),
    dcc.Download(id="fh-download"),

    # Header
    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-files me-2", style={"color": ACCENT}),
            html.Span("File Handler", style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P("Merge and manage multiple DPMB-format data files efficiently.",
               style={"color": "#a0a0a0", "fontSize": "0.9rem"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        # Left panel
        dbc.Col(md=4, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Operation", className="mb-3", style={"color": ACCENT}),

                dbc.RadioItems(
                    id="fh-mode",
                    options=[
                        {"label": "Merge — combine multiple files into one", "value": "merge"},
                        {"label": "Append — add rows to existing file", "value": "append"},
                    ],
                    value="merge",
                    className="mb-3",
                    inputStyle={"marginRight": "8px"},
                    labelStyle={"color": "#e0e0e0", "fontSize": "0.88rem"}
                ),

                html.Label("Upload Files (.xlsx)", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Upload(
                    id="fh-upload",
                    children=html.Div([
                        html.I(className="bi bi-upload me-2", style={"color": ACCENT}),
                        "Drop files or ", html.A("browse", style={"color": ACCENT})
                    ]),
                    multiple=True,
                    className="mt-2 mb-3",
                    style={
                        "border": f"1px dashed {ACCENT}", "borderRadius": "8px",
                        "padding": "16px", "textAlign": "center",
                        "color": "#a0a0a0", "fontSize": "0.85rem",
                        "backgroundColor": "rgba(255,189,46,0.04)", "cursor": "pointer"
                    }
                ),

                html.Div(id="fh-file-list", className="mb-3"),

                html.Label("Output Filename", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Input(
                    id="fh-output-name",
                    placeholder="output_merged.xlsx",
                    type="text",
                    className="mb-3",
                    style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                           "border": "1px solid rgba(255,255,255,0.1)"}
                ),

                dbc.Button(
                    [html.I(className="bi bi-gear me-2"), "Process Files"],
                    id="fh-run-btn",
                    color="primary",
                    outline=True,
                    className="w-100",
                    style={"borderColor": ACCENT, "color": ACCENT}
                ),
            ]), className="card-premium border-0"),
        ]),

        # Right panel
        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Status", style={"color": ACCENT}, className="mb-3"),
                html.Div(id="fh-status", children=[
                    dbc.Alert("Upload files and click Process.",
                              color="secondary", className="card-premium border-0 text-white")
                ])
            ]), className="card-premium border-0"),
        ]),
    ]),
])


@callback(
    Output("fh-file-list", "children"),
    Input("fh-upload", "filename"),
    prevent_initial_call=True
)
def show_file_list(filenames):
    if not filenames:
        return ""
    items = [html.Li(f, style={"color": "#a0a0a0", "fontSize": "0.82rem"}) for f in filenames]
    return html.Ul(items, style={"paddingLeft": "1.2rem", "marginBottom": 0})


@callback(
    Output("fh-status", "children"),
    Output("fh-download", "data"),
    Output("fh-toast", "children"),
    Input("fh-run-btn", "n_clicks"),
    State("fh-upload", "contents"),
    State("fh-upload", "filename"),
    State("fh-mode", "value"),
    State("fh-output-name", "value"),
    prevent_initial_call=True
)
def process_files(n_clicks, contents_list, filenames, mode, output_name):
    if not contents_list:
        return no_update, no_update, dbc.Toast("Upload at least one file.", icon="warning", duration=3000,
                                                is_open=True, style={"position": "fixed", "top": 20, "right": 20,
                                                                     "zIndex": 9999}, className="toast-custom")
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from THRTools.utils.PPVReportMerger import PPVReportMerger

        import pandas as pd

        dfs = []
        for content, fname in zip(contents_list, filenames):
            _, data = content.split(',')
            decoded = base64.b64decode(data)
            try:
                df = pd.read_excel(io.BytesIO(decoded))
                dfs.append(df)
            except Exception as ex:
                logger.warning(f"Could not read {fname}: {ex}")

        if not dfs:
            return (dbc.Alert("No valid Excel files could be read.", color="danger",
                              className="card-premium border-0 text-white"),
                    no_update,
                    dbc.Toast("No valid files.", icon="danger", duration=3000, is_open=True,
                              style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                              className="toast-custom"))

        if mode == "merge":
            merged = pd.concat(dfs, ignore_index=True)
        else:
            merged = dfs[0]
            for df in dfs[1:]:
                merged = pd.concat([merged, df], ignore_index=True)

        out_name = output_name or "output_merged.xlsx"
        buf = io.BytesIO()
        merged.to_excel(buf, index=False)
        buf.seek(0)

        summary = [
            html.P(f"✓ {len(filenames)} file(s) processed", style={"color": "#00ff9d"}),
            html.P(f"Total rows: {len(merged)}", style={"color": "#e0e0e0"}),
            dbc.Button([html.I(className="bi bi-download me-2"), f"Download {out_name}"],
                       id="fh-dl-btn", outline=True,
                       style={"borderColor": ACCENT, "color": ACCENT})
        ]

        return (html.Div(summary),
                dcc.send_bytes(buf.read(), out_name),
                dbc.Toast(f"Processed {len(filenames)} file(s). Downloading...", icon="success",
                          duration=4000, is_open=True,
                          style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                          className="toast-custom"))
    except Exception as e:
        logger.exception("File handler error")
        return (no_update, no_update,
                dbc.Toast(f"Error: {str(e)}", icon="danger", duration=5000, is_open=True,
                          style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                          className="toast-custom"))
