"""
PPV MCA Report
===============
Generate MCA failure analysis reports from Bucketer/S2T Logger Excel files.
Calls THRTools/parsers/MCAparser.ppv_report backend.

Replicates all functionality from PPV/gui/PPVDataChecks.PPVReportGUI:
- Mode: Framework / Bucketer / Data
- Product: GNR / CWF / DMR
- Week: 1-52 (auto-detects current week)
- Custom label
- Processing options: Reduced report, MCA decode, Overview sheet, MCA Checker file
- Disables Reduced/Decode options when mode == Data
"""
import logging
import base64
import io
import os
import datetime
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
PRODUCTS = ['GNR', 'CWF', 'DMR']
MODES = ['Bucketer', 'Framework', 'Data']
CURRENT_WEEK = str(datetime.datetime.now().isocalendar()[1])
WEEKS = [str(i) for i in range(1, 53)]

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

                dbc.Row([
                    dbc.Col([
                        html.Label("Mode", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                        dbc.Select(
                            id="mr-mode",
                            options=[{"label": m, "value": m} for m in MODES],
                            value="Bucketer",
                            style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                   "border": "1px solid rgba(255,255,255,0.1)"}
                        ),
                    ], width=6),
                    dbc.Col([
                        html.Label("Product", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                        dbc.Select(
                            id="mr-product",
                            options=[{"label": p, "value": p} for p in PRODUCTS],
                            value="GNR",
                            style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                   "border": "1px solid rgba(255,255,255,0.1)"}
                        ),
                    ], width=6),
                ], className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        html.Label("Work Week", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                        dbc.Select(
                            id="mr-week",
                            options=[{"label": f"WW{w}", "value": w} for w in WEEKS],
                            value=CURRENT_WEEK,
                            style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                   "border": "1px solid rgba(255,255,255,0.1)"}
                        ),
                    ], width=6),
                    dbc.Col([
                        html.Label("Label", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                        dbc.Input(
                            id="mr-label",
                            placeholder="e.g. PPV_Batch_001",
                            type="text",
                            style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                   "border": "1px solid rgba(255,255,255,0.1)",
                                   "fontSize": "0.85rem"}
                        ),
                    ], width=6),
                ], className="mb-3"),

                html.Label("Processing Options", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Checklist(
                    id="mr-options",
                    options=[
                        {"label": "Reduced report", "value": "reduced"},
                        {"label": "MCA decode",     "value": "decode"},
                        {"label": "Overview sheet", "value": "overview"},
                        {"label": "MCA Checker file", "value": "mcfile"},
                    ],
                    value=["reduced", "decode", "overview"],
                    inputStyle={"marginRight": "6px"},
                    labelStyle={"color": "#e0e0e0", "fontSize": "0.88rem"},
                    className="mt-1 mb-3"
                ),

                html.Label(id="mr-source-label",
                           children="Upload Bucketer / S2T Excel File",
                           style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Upload(
                    id="mr-upload",
                    children=html.Div([
                        html.I(className="bi bi-file-earmark-spreadsheet me-2",
                               style={"color": ACCENT}),
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
                    "The report is appended as a new sheet to a copy of the uploaded workbook.",
                ], color="secondary", className="card-premium border-0 text-white mt-2",
                   style={"fontSize": "0.8rem"})
            ]), className="card-premium border-0"),
        ]),

        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Report Status", style={"color": ACCENT}, className="mb-3"),
                html.Div(id="mr-status", children=[
                    dbc.Alert("Upload an Excel file and configure options to generate a report.",
                              color="secondary", className="card-premium border-0 text-white")
                ])
            ]), className="card-premium border-0"),
        ]),
    ]),
])


@callback(
    Output("mr-upload-label", "children"),
    Output("mr-source-label", "children"),
    Output("mr-options", "options"),
    Input("mr-upload", "filename"),
    Input("mr-mode", "value"),
    prevent_initial_call=False
)
def update_upload_area(fname, mode):
    file_label = f"Selected: {fname}" if fname else ""
    source_label = "Upload Data File" if mode == "Data" else "Upload Bucketer / S2T Excel File"

    # In Data mode, Reduced and MCA decode are not applicable
    opts = [
        {"label": "Reduced report",    "value": "reduced",  "disabled": mode == "Data"},
        {"label": "MCA decode",        "value": "decode",   "disabled": mode == "Data"},
        {"label": "Overview sheet",    "value": "overview"},
        {"label": "MCA Checker file",  "value": "mcfile"},
    ]
    return file_label, source_label, opts


@callback(
    Output("mr-status", "children"),
    Output("mr-download", "data"),
    Output("mr-toast", "children"),
    Input("mr-run-btn", "n_clicks"),
    State("mr-upload", "contents"),
    State("mr-upload", "filename"),
    State("mr-mode", "value"),
    State("mr-product", "value"),
    State("mr-week", "value"),
    State("mr-label", "value"),
    State("mr-options", "value"),
    prevent_initial_call=True
)
def generate_report(n_clicks, content, filename, mode, product, week, label, options):
    if not content:
        return (no_update, no_update,
                dbc.Toast("Upload a source file first.", icon="warning", duration=3000,
                          is_open=True, style={"position": "fixed", "top": 20, "right": 20,
                                               "zIndex": 9999}, className="toast-custom"))
    try:
        import tempfile
        import shutil
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from THRTools.parsers.MCAparser import ppv_report

        options = options or []
        reduced   = "reduced"  in options
        decode    = "decode"   in options
        overview  = "overview" in options
        mcfile    = "mcfile"   in options

        _, data = content.split(',')
        file_bytes = base64.b64decode(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, filename)
            out_path = os.path.join(tmpdir, f"report_{filename}")
            with open(in_path, 'wb') as f:
                f.write(file_bytes)
            shutil.copy(in_path, out_path)

            report = ppv_report(
                name=product or "GNR",
                week=week or CURRENT_WEEK,
                label=label or "",
                source_file=in_path,
                report=tmpdir,
                reduced=reduced,
                mcdetail=mcfile,
                overview=overview,
                decode=decode,
                mode=mode or "Bucketer",
                product=product or "GNR",
            )

            if mode in ("Bucketer", "Framework"):
                report.run(options=['MESH', 'CORE'])
            elif mode == "Data":
                report.gen_auxfiles(
                    data_file=in_path,
                    mca_file=report.mca_file if hasattr(report, 'mca_file') else out_path,
                    ovw_file=report.ovw_file if hasattr(report, 'ovw_file') else out_path,
                    mcfile_on=mcfile,
                    ovw_on=overview,
                    options=['MESH', 'CORE', 'PPV']
                )

            # Find the generated output file
            generated = [f for f in os.listdir(tmpdir)
                         if f.endswith('.xlsx') and f != os.path.basename(in_path)]
            if generated:
                result_file = os.path.join(tmpdir, generated[0])
                with open(result_file, 'rb') as f:
                    out_bytes = f.read()
                dl_name = generated[0]
            else:
                # Fall back to original file (report written in-place)
                with open(in_path, 'rb') as f:
                    out_bytes = f.read()
                dl_name = f"report_{filename}"

        status = html.Div([
            html.P(f"✓ Report generated for: {filename}", style={"color": "#00ff9d"}),
            html.P(f"Product: {product} | WW: {week} | Mode: {mode}",
                   style={"color": "#a0a0a0", "fontSize": "0.88rem"}),
            html.P(f"Options: {', '.join(options) or 'none'}",
                   style={"color": "#a0a0a0", "fontSize": "0.88rem"}),
        ])
        return (status,
                dcc.send_bytes(out_bytes, dl_name),
                dbc.Toast("Report generated. Downloading...", icon="success", duration=4000,
                          is_open=True, style={"position": "fixed", "top": 20, "right": 20,
                                               "zIndex": 9999}, className="toast-custom"))

    except Exception as e:
        logger.exception("MCA Report error")
        return (no_update, no_update,
                dbc.Toast(f"Error: {str(e)}", icon="danger", duration=5000, is_open=True,
                          style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                          className="toast-custom"))
