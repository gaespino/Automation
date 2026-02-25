"""
PPV MCA Report
===============
Generate MCA failure analysis reports from Bucketer/S2T Logger Excel files.
Calls THRTools/parsers/MCAparser.py backend.
"""
import logging
import base64
import io
import os
import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

dash.register_page(
    __name__,
    path='/thr-tools/mca-report',
    name='PPV MCA Report',
    title='PPV MCA Report'
)

ACCENT = "#ff4d4d"

layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="mr-toast"),
    dcc.Download(id="mr-download"),

    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-file-earmark-bar-graph me-2", style={"color": ACCENT}),
            html.Span("PPV MCA Report", style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P("Generate MCA failure analysis reports from Bucketer or S2T Logger Excel files.",
               style={"color": "#a0a0a0", "fontSize": "0.9rem"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        dbc.Col(md=4, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Report Configuration", className="mb-3", style={"color": ACCENT}),

                html.Label("Analysis Options", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Checklist(
                    id="mr-options",
                    options=[
                        {"label": "MESH Analysis", "value": "MESH"},
                        {"label": "CORE Analysis", "value": "CORE"},
                        {"label": "IO Analysis", "value": "IO"},
                        {"label": "SA Analysis", "value": "SA"},
                    ],
                    value=["MESH", "CORE"],
                    inputStyle={"marginRight": "6px"},
                    labelStyle={"color": "#e0e0e0", "fontSize": "0.88rem"},
                    className="mt-1 mb-3"
                ),

                html.Label("Upload Bucketer/S2T Excel File",
                           style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Upload(
                    id="mr-upload",
                    children=html.Div([
                        html.I(className="bi bi-file-earmark-spreadsheet me-2", style={"color": ACCENT}),
                        "Drop Excel file or ", html.A("browse", style={"color": ACCENT})
                    ]),
                    multiple=False, className="mt-2 mb-3",
                    style={
                        "border": f"1px dashed {ACCENT}", "borderRadius": "8px",
                        "padding": "16px", "textAlign": "center",
                        "color": "#a0a0a0", "fontSize": "0.85rem",
                        "backgroundColor": "rgba(255,77,77,0.04)", "cursor": "pointer"
                    }
                ),

                html.Div(id="mr-upload-label",
                         style={"color": "#a0a0a0", "fontSize": "0.8rem", "marginBottom": "12px"}),

                dbc.Button(
                    [html.I(className="bi bi-bar-chart-line me-2"), "Generate Report"],
                    id="mr-run-btn",
                    color="danger", outline=True, className="w-100",
                    style={"borderColor": ACCENT, "color": ACCENT}
                ),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)", "marginTop": "20px"}),
                dbc.Alert([
                    html.I(className="bi bi-info-circle me-2"),
                    "The report is appended as a new sheet to the uploaded Excel workbook.",
                ], color="secondary", className="card-premium border-0 text-white mt-2",
                   style={"fontSize": "0.8rem"})
            ]), className="card-premium border-0"),
        ]),

        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Report Status", style={"color": ACCENT}, className="mb-3"),
                html.Div(id="mr-status", children=[
                    dbc.Alert("Upload an Excel file and select analysis options to generate a report.",
                              color="secondary", className="card-premium border-0 text-white")
                ])
            ]), className="card-premium border-0"),
        ]),
    ]),
])


@callback(
    Output("mr-upload-label", "children"),
    Input("mr-upload", "filename"),
    prevent_initial_call=True
)
def show_filename(fname):
    if fname:
        return f"Selected: {fname}"
    return ""


@callback(
    Output("mr-status", "children"),
    Output("mr-download", "data"),
    Output("mr-toast", "children"),
    Input("mr-run-btn", "n_clicks"),
    State("mr-upload", "contents"),
    State("mr-upload", "filename"),
    State("mr-options", "value"),
    prevent_initial_call=True
)
def generate_report(n_clicks, content, filename, options):
    if not content:
        return no_update, no_update, dbc.Toast("Upload an Excel file first.", icon="warning",
                                                duration=3000, is_open=True,
                                                style={"position": "fixed", "top": 20, "right": 20,
                                                       "zIndex": 9999}, className="toast-custom")
    try:
        import tempfile
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from THRTools.parsers.MCAparser import ppv_report

        _, data = content.split(',')
        file_bytes = base64.b64decode(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, filename)
            with open(in_path, 'wb') as f:
                f.write(file_bytes)

            report = ppv_report(in_path)
            report.run(options=options or ["MESH", "CORE"])

            with open(in_path, 'rb') as f:
                out_bytes = f.read()

        status = html.Div([
            html.P(f"✓ Report generated for: {filename}", style={"color": "#00ff9d"}),
            html.P(f"Analysis sections: {', '.join(options or [])}", style={"color": "#a0a0a0"}),
        ])
        return (status,
                dcc.send_bytes(out_bytes, f"report_{filename}"),
                dbc.Toast("Report generated. Downloading...", icon="success", duration=4000,
                          is_open=True, style={"position": "fixed", "top": 20, "right": 20,
                                               "zIndex": 9999}, className="toast-custom"))

    except Exception as e:
        logger.exception("MCA Report error")
        return (no_update, no_update,
                dbc.Toast(f"Error: {str(e)}", icon="danger", duration=5000, is_open=True,
                          style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                          className="toast-custom"))
