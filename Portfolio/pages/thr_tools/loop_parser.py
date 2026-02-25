"""
PTC Loop Parser
================
Parse logs from PTC experiment data and generate DPMB report format files.
Calls THRTools/parsers/PPVLoopsParser.py backend.
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
    path='/thr-tools/loop-parser',
    name='PTC Loop Parser',
    title='PTC Loop Parser'
)

ACCENT = "#00d4ff"

layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="lp-toast"),
    dcc.Download(id="lp-download"),

    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-file-earmark-code me-2", style={"color": ACCENT}),
            html.Span("PTC Loop Parser", style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P("Parse logs from PTC experiment data and generate DPMB report format files.",
               style={"color": "#a0a0a0", "fontSize": "0.9rem"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        dbc.Col(md=4, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Parser Configuration", className="mb-3", style={"color": ACCENT}),

                html.Label("Bucket", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Input(id="lp-bucket", placeholder="e.g. 3STRIKE", type="text",
                          className="mb-3",
                          style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                 "border": "1px solid rgba(255,255,255,0.1)"}),

                html.Label("Lots Seq Key", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Input(id="lp-lots-key", placeholder="e.g. 74BJ", type="text",
                          className="mb-3",
                          style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                 "border": "1px solid rgba(255,255,255,0.1)"}),

                dbc.Row([
                    dbc.Col([
                        html.Label("Start WW", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                        dbc.Input(id="lp-start-ww", placeholder="2026WW01", type="text",
                                  className="mb-3",
                                  style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                         "border": "1px solid rgba(255,255,255,0.1)"}),
                    ], width=6),
                    dbc.Col([
                        html.Label("Output Name", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                        dbc.Input(id="lp-output-name", placeholder="output.xlsx", type="text",
                                  className="mb-3",
                                  style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                         "border": "1px solid rgba(255,255,255,0.1)"}),
                    ], width=6),
                ]),

                dbc.Checklist(
                    id="lp-options",
                    options=[
                        {"label": "ZIP input", "value": "zip"},
                        {"label": "DPMB format output", "value": "dpmb"},
                    ],
                    value=["dpmb"],
                    inputStyle={"marginRight": "6px"},
                    labelStyle={"color": "#e0e0e0", "fontSize": "0.88rem"},
                    className="mb-3"
                ),

                html.Label("Upload Log Folder (ZIP) or log files",
                           style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Upload(
                    id="lp-upload",
                    children=html.Div([
                        html.I(className="bi bi-upload me-2", style={"color": ACCENT}),
                        "Drop files or ", html.A("browse", style={"color": ACCENT})
                    ]),
                    multiple=True, className="mt-2 mb-3",
                    style={
                        "border": f"1px dashed {ACCENT}", "borderRadius": "8px",
                        "padding": "16px", "textAlign": "center",
                        "color": "#a0a0a0", "fontSize": "0.85rem",
                        "backgroundColor": "rgba(0,212,255,0.04)", "cursor": "pointer"
                    }
                ),

                dbc.Button(
                    [html.I(className="bi bi-play-circle me-2"), "Parse Logs"],
                    id="lp-run-btn",
                    color="primary", outline=True, className="w-100",
                    style={"borderColor": ACCENT, "color": ACCENT}
                ),
            ]), className="card-premium border-0"),
        ]),

        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Parse Results", style={"color": ACCENT}, className="mb-3"),
                html.Div(id="lp-status", children=[
                    dbc.Alert("Configure parser and upload log files.",
                              color="secondary", className="card-premium border-0 text-white")
                ])
            ]), className="card-premium border-0"),
        ]),
    ]),
])


@callback(
    Output("lp-status", "children"),
    Output("lp-download", "data"),
    Output("lp-toast", "children"),
    Input("lp-run-btn", "n_clicks"),
    State("lp-upload", "contents"),
    State("lp-upload", "filename"),
    State("lp-bucket", "value"),
    State("lp-lots-key", "value"),
    State("lp-start-ww", "value"),
    State("lp-output-name", "value"),
    State("lp-options", "value"),
    prevent_initial_call=True
)
def run_parser(n_clicks, contents_list, filenames, bucket, lots_key, start_ww, output_name, options):
    if not contents_list:
        return no_update, no_update, dbc.Toast("Upload log files first.", icon="warning", duration=3000,
                                                is_open=True, style={"position": "fixed", "top": 20,
                                                                     "right": 20, "zIndex": 9999},
                                                className="toast-custom")
    try:
        import tempfile
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from THRTools.parsers.PPVLoopsParser import LogsPTC

        # Write uploaded files to a temp dir
        with tempfile.TemporaryDirectory() as tmpdir:
            for content, fname in zip(contents_list, filenames):
                _, data = content.split(',')
                fpath = os.path.join(tmpdir, fname)
                with open(fpath, 'wb') as f:
                    f.write(base64.b64decode(data))

            out_name = output_name or "parsed_output.xlsx"
            out_path = os.path.join(tmpdir, out_name)
            use_zip = "zip" in (options or [])
            use_dpmb = "dpmb" in (options or [])

            parser = LogsPTC(
                StartWW=start_ww or "",
                bucket=bucket or "",
                LotsSeqKey=lots_key or "",
                folder_path=tmpdir,
                output_file=out_path,
                zipfile=use_zip,
                dpmbformat=use_dpmb
            )
            parser.run()

            if os.path.exists(out_path):
                with open(out_path, 'rb') as f:
                    data_bytes = f.read()

                summary = html.Div([
                    html.P(f"✓ Parsed {len(filenames)} file(s)", style={"color": "#00ff9d"}),
                    html.P(f"Output: {out_name}", style={"color": "#a0a0a0"}),
                ])
                return (summary,
                        dcc.send_bytes(data_bytes, out_name),
                        dbc.Toast("Parse complete. Downloading...", icon="success", duration=4000,
                                  is_open=True, style={"position": "fixed", "top": 20, "right": 20,
                                                       "zIndex": 9999}, className="toast-custom"))

            return (dbc.Alert("Parser completed but no output file found.", color="warning",
                              className="card-premium border-0 text-white"),
                    no_update,
                    dbc.Toast("Warning: No output generated.", icon="warning", duration=4000, is_open=True,
                              style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                              className="toast-custom"))

    except Exception as e:
        logger.exception("Loop parser error")
        return (no_update, no_update,
                dbc.Toast(f"Error: {str(e)}", icon="danger", duration=5000, is_open=True,
                          style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                          className="toast-custom"))
