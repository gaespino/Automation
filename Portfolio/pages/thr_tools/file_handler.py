"""
File Handler
=============
Merge and manage multiple data files efficiently.
Calls THRTools/utils/PPVReportMerger.py backend.

Replicates PPV/gui/PPVFileHandler.FileHandlerGUI:
- Merge mode: combine multiple Excel files from a folder into one output file
  (upload multiple files as the "folder contents", optional file prefix filter)
- Append mode: add data from one source file to an existing target file
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
        html.P("Merge or append multiple DPMB-format Excel data files.",
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
                        {"label": "Append — add rows from source to target", "value": "append"},
                    ],
                    value="merge",
                    className="mb-3",
                    inputStyle={"marginRight": "8px"},
                    labelStyle={"color": "#e0e0e0", "fontSize": "0.88rem"}
                ),

                html.Div(id="fh-mode-desc",
                         style={"color": "#7f8c8d", "fontSize": "0.8rem", "marginBottom": "12px"}),

                # Merge mode: multiple source files
                html.Div(id="fh-merge-area", children=[
                    html.Label("Source Files (.xlsx)", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                    dcc.Upload(
                        id="fh-upload-source",
                        children=html.Div([
                            html.I(className="bi bi-upload me-2", style={"color": ACCENT}),
                            "Drop files or ", html.A("browse", style={"color": ACCENT})
                        ]),
                        multiple=True, className="mt-1 mb-2",
                        style={
                            "border": f"1px dashed {ACCENT}", "borderRadius": "8px",
                            "padding": "12px", "textAlign": "center",
                            "color": "#a0a0a0", "fontSize": "0.85rem",
                            "backgroundColor": "rgba(255,189,46,0.04)", "cursor": "pointer"
                        }
                    ),
                    html.Div(id="fh-source-list", className="mb-2"),

                    html.Label("File Prefix Filter (optional)",
                               style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                    dbc.Input(
                        id="fh-prefix",
                        placeholder="e.g. Summary_ or Report_",
                        type="text", className="mb-3",
                        style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                               "border": "1px solid rgba(255,255,255,0.1)"}
                    ),
                ]),

                # Append mode: two separate file uploads
                html.Div(id="fh-append-area", style={"display": "none"}, children=[
                    html.Label("Source File (.xlsx)", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                    dcc.Upload(
                        id="fh-upload-append-src",
                        children=html.Div([html.A("Browse", style={"color": ACCENT}),
                                           " or drop source file"]),
                        multiple=False, className="mt-1 mb-2",
                        style={"border": f"1px dashed {ACCENT}", "borderRadius": "6px",
                               "padding": "10px", "textAlign": "center",
                               "color": "#a0a0a0", "fontSize": "0.85rem",
                               "backgroundColor": "rgba(255,189,46,0.04)", "cursor": "pointer"}
                    ),
                    html.Div(id="fh-append-src-label",
                             style={"color": "#a0a0a0", "fontSize": "0.8rem", "marginBottom": "8px"}),

                    html.Label("Target File (.xlsx)", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                    dcc.Upload(
                        id="fh-upload-append-tgt",
                        children=html.Div([html.A("Browse", style={"color": ACCENT}),
                                           " or drop target file"]),
                        multiple=False, className="mt-1 mb-2",
                        style={"border": f"1px dashed {ACCENT}", "borderRadius": "6px",
                               "padding": "10px", "textAlign": "center",
                               "color": "#a0a0a0", "fontSize": "0.85rem",
                               "backgroundColor": "rgba(255,189,46,0.04)", "cursor": "pointer"}
                    ),
                    html.Div(id="fh-append-tgt-label",
                             style={"color": "#a0a0a0", "fontSize": "0.8rem", "marginBottom": "8px"}),
                ]),

                html.Label("Output Filename", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Input(
                    id="fh-output-name",
                    placeholder="output_merged.xlsx",
                    type="text", className="mb-3",
                    style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                           "border": "1px solid rgba(255,255,255,0.1)"}
                ),

                dbc.Button(
                    [html.I(className="bi bi-gear me-2"), "Process Files"],
                    id="fh-run-btn", color="primary", outline=True, className="w-100",
                    style={"borderColor": ACCENT, "color": ACCENT}
                ),
            ]), className="card-premium border-0"),
        ]),

        # Right panel
        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Status", style={"color": ACCENT}, className="mb-3"),
                html.Div(id="fh-status", children=[
                    dbc.Alert("Select operation, upload files, and click Process.",
                              color="secondary", className="card-premium border-0 text-white")
                ])
            ]), className="card-premium border-0"),
        ]),
    ]),
])


@callback(
    Output("fh-mode-desc", "children"),
    Output("fh-merge-area", "style"),
    Output("fh-append-area", "style"),
    Input("fh-mode", "value"),
    prevent_initial_call=False
)
def toggle_mode(mode):
    if mode == "append":
        desc = "Append mode: add rows from source file into existing target file (matched by sheet name)."
        return desc, {"display": "none"}, {"display": "block"}
    desc = "Merge mode: combine multiple Excel files from the same folder into one output file."
    return desc, {"display": "block"}, {"display": "none"}


@callback(
    Output("fh-source-list", "children"),
    Input("fh-upload-source", "filename"),
    prevent_initial_call=True
)
def show_source_list(filenames):
    if not filenames:
        return ""
    return html.Ul([html.Li(f, style={"color": "#a0a0a0", "fontSize": "0.82rem"})
                    for f in filenames],
                   style={"paddingLeft": "1.2rem", "marginBottom": 0})


@callback(
    Output("fh-append-src-label", "children"),
    Input("fh-upload-append-src", "filename"),
    prevent_initial_call=True
)
def show_append_src(fname):
    return f"Source: {fname}" if fname else ""


@callback(
    Output("fh-append-tgt-label", "children"),
    Input("fh-upload-append-tgt", "filename"),
    prevent_initial_call=True
)
def show_append_tgt(fname):
    return f"Target: {fname}" if fname else ""


@callback(
    Output("fh-status", "children"),
    Output("fh-download", "data"),
    Output("fh-toast", "children"),
    Input("fh-run-btn", "n_clicks"),
    State("fh-mode", "value"),
    # Merge states
    State("fh-upload-source", "contents"),
    State("fh-upload-source", "filename"),
    State("fh-prefix", "value"),
    # Append states
    State("fh-upload-append-src", "contents"),
    State("fh-upload-append-src", "filename"),
    State("fh-upload-append-tgt", "contents"),
    State("fh-upload-append-tgt", "filename"),
    # Common
    State("fh-output-name", "value"),
    prevent_initial_call=True
)
def process_files(n_clicks, mode,
                  merge_contents, merge_filenames, prefix,
                  append_src_content, append_src_fname,
                  append_tgt_content, append_tgt_fname,
                  output_name):
    try:
        import tempfile
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from THRTools.utils.PPVReportMerger import (
            merge_excel_files, append_excel_tables, sheet_names
        )

        out_name = output_name or "output_merged.xlsx"

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, out_name)

            if mode == "merge":
                if not merge_contents:
                    return (no_update, no_update,
                            _toast("Upload at least one source file.", "warning"))

                # Save all uploaded files to tmpdir
                for content, fname in zip(merge_contents, merge_filenames):
                    _, data = content.split(',')
                    with open(os.path.join(tmpdir, fname), 'wb') as f:
                        f.write(base64.b64decode(data))

                merge_excel_files(
                    input_folder=tmpdir,
                    output_file=out_path,
                    prefix=prefix if prefix and prefix.strip() else None
                )

                if not os.path.exists(out_path):
                    return (dbc.Alert("Merge produced no output. Check that files match the prefix.",
                                      color="warning", className="card-premium border-0 text-white"),
                            no_update, _toast("No output file created.", "warning"))

                n = len(merge_filenames)
                status = html.P(f"✓ Merged {n} file(s) → {out_name}", style={"color": "#00ff9d"})

            else:  # append
                if not append_src_content or not append_tgt_content:
                    return (no_update, no_update,
                            _toast("Upload both source and target files for Append mode.", "warning"))

                # Save source and target to tmpdir
                _, src_data = append_src_content.split(',')
                src_path = os.path.join(tmpdir, append_src_fname)
                with open(src_path, 'wb') as f:
                    f.write(base64.b64decode(src_data))

                _, tgt_data = append_tgt_content.split(',')
                tgt_path = os.path.join(tmpdir, append_tgt_fname)
                with open(tgt_path, 'wb') as f:
                    f.write(base64.b64decode(tgt_data))

                append_excel_tables(
                    source_file=src_path,
                    target_file=tgt_path,
                    sheet_names=sheet_names
                )

                # Output is the modified target file
                out_path = tgt_path
                out_name = output_name or f"appended_{append_tgt_fname}"
                status = html.P(f"✓ Appended {append_src_fname} → {append_tgt_fname}",
                                style={"color": "#00ff9d"})

            with open(out_path, 'rb') as f:
                out_bytes = f.read()

        return (status,
                dcc.send_bytes(out_bytes, out_name),
                _toast(f"Processing complete. Downloading {out_name}…", "success"))

    except Exception as e:
        logger.exception("File handler error")
        return (no_update, no_update, _toast(f"Error: {str(e)}", "danger", 5000))


def _toast(msg, icon, duration=3000):
    return dbc.Toast(
        msg, icon=icon, duration=duration, is_open=True,
        style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
        className="toast-custom"
    )
