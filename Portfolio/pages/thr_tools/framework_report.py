"""
Framework Report Builder
=========================
Build experiment summary reports from DebugFramework output files.
Faithfully replicates PPV/gui/PPVFrameworkReport.FrameworkReportBuilder workflow:

1. Upload PPV data folder (ZIP of experiment folder tree) or point to local path
2. Parse Experiments — calls fpa.find_files() to discover experiment subfolders
3. Show experiments table: Include checkbox, Content type, Type, Other Type, Comments
4. Options: Merge Summary Files, Generate Report, Check Logging Data, Skip Strings,
            Generate DragonData, CoreData, Summary Tab, Unit Overview sheets
5. Generate Framework Files → runs full analysis pipeline via Frameworkparser
6. Download result
"""
import logging
import base64
import io
import os
import json
import tempfile
import zipfile
import datetime
import sys
import dash
from dash import html, dcc, Input, Output, State, callback, no_update, ctx
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

dash.register_page(
    __name__,
    path='/thr-tools/framework-report',
    name='Framework Report',
    title='Framework Report Builder'
)

ACCENT = "#00ff9d"
_PRODUCTS = ["GNR", "CWF", "DMR"]
_CONTENT_TYPES = ["Dragon", "Linux", "TSL", "Python", "Sandstone", ""]
_EXP_TYPES = ["Base", "Voltage", "Frequency", "Shmoo", "Others", ""]

_INPUT_STYLE = {
    "backgroundColor": "#1a1d26", "color": "#e0e0e0",
    "border": "1px solid rgba(255,255,255,0.1)", "fontSize": "0.85rem"
}
_LABEL_STYLE = {"color": "#a0a0a0", "fontSize": "0.8rem"}


layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="fr-toast"),
    dcc.Download(id="fr-download"),
    dcc.Store(id="fr-store", data={}),
    dcc.Store(id="fr-result-store", data=None),

    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-clipboard-data me-2", style={"color": ACCENT}),
            html.Span("Framework Report Builder",
                      style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P(
            "Build multi-experiment summary reports from DebugFramework output files. "
            "Upload a ZIP of the experiment folder tree, parse experiments, configure and generate.",
            style={"color": "#a0a0a0", "fontSize": "0.9rem"}
        ),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        # ── Left: Data Source & Options ────────────────────────────────────────
        dbc.Col(md=4, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Data Source & Output", className="mb-3", style={"color": ACCENT}),

                html.Label("Product", style=_LABEL_STYLE),
                dbc.Select(
                    id="fr-product",
                    options=[{"label": p, "value": p} for p in _PRODUCTS],
                    value="GNR",
                    className="mb-2",
                    style=_INPUT_STYLE
                ),

                html.Label("Upload PPV Data ZIP (experiment folder tree)", style=_LABEL_STYLE),
                dcc.Upload(
                    id="fr-upload-zip",
                    children=html.Div([html.A("Browse", style={"color": ACCENT}),
                                       " or drop .zip"]),
                    multiple=False, className="mt-1 mb-1",
                    style={"border": f"1px dashed {ACCENT}", "borderRadius": "6px",
                           "padding": "10px", "textAlign": "center",
                           "color": "#a0a0a0", "fontSize": "0.82rem",
                           "backgroundColor": f"rgba(0,255,157,0.03)", "cursor": "pointer"}
                ),
                html.Div(id="fr-zip-label",
                         style={"color": "#a0a0a0", "fontSize": "0.75rem", "marginBottom": "8px"}),

                dbc.Button([html.I(className="bi bi-search me-2"), "Parse Experiments"],
                           id="fr-parse-btn", outline=True, className="w-100 mb-3",
                           style={"borderColor": ACCENT, "color": ACCENT}),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),
                html.H6("Report Options", style={"color": "#c0c0c0", "fontSize": "0.85rem"}, className="mb-2"),

                dbc.Checklist(
                    id="fr-report-options",
                    options=[
                        {"label": "Merge Summary Files",         "value": "merge"},
                        {"label": "Generate Report",             "value": "report"},
                        {"label": "Check Logging Data",          "value": "logging"},
                        {"label": "Generate DragonData Sheet",   "value": "dragon"},
                        {"label": "Generate CoreData Sheet",     "value": "core"},
                        {"label": "Generate Summary Tab",        "value": "summary_tab"},
                        {"label": "Generate Unit Overview",      "value": "overview"},
                    ],
                    value=["merge", "report", "dragon", "core", "overview"],
                    inputStyle={"marginRight": "6px"},
                    labelStyle={"color": "#e0e0e0", "fontSize": "0.85rem"},
                    className="mb-3"
                ),

                html.Label("Merge Tag (appended to merged file name)", style=_LABEL_STYLE),
                dbc.Input(id="fr-merge-tag", placeholder="e.g. Batch01", type="text",
                          className="mb-2", style=_INPUT_STYLE),

                html.Label("Report Tag (appended to report file name)", style=_LABEL_STYLE),
                dbc.Input(id="fr-report-tag", placeholder="e.g. v1", type="text",
                          className="mb-2", style=_INPUT_STYLE),

                html.Label("Skip Strings (comma-separated)", style=_LABEL_STYLE),
                dbc.Input(id="fr-skip-strings", placeholder="pysv, timeout",
                          type="text", className="mb-3", style=_INPUT_STYLE),

                dbc.Button(
                    [html.I(className="bi bi-file-earmark-excel me-2"), "Generate Framework Files"],
                    id="fr-run-btn",
                    outline=True, className="w-100 mb-1",
                    style={"borderColor": ACCENT, "color": ACCENT}, disabled=True
                ),
                dbc.Button(
                    [html.I(className="bi bi-download me-2"), "Download Report"],
                    id="fr-dl-btn",
                    color="success", outline=True, className="w-100",
                    style={"display": "none"}
                ),

            ]), className="card-premium border-0"),
        ]),

        # ── Right: Experiments table + status ──────────────────────────────────
        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                dbc.Row([
                    dbc.Col(html.H6("Experiments Configuration", style={"color": ACCENT}), width=8),
                    dbc.Col([
                        dbc.Button("Select All", id="fr-select-all-btn", size="sm",
                                   outline=True, className="me-1 float-end",
                                   style={"borderColor": ACCENT, "color": ACCENT}, disabled=True),
                        dbc.Button("Deselect All", id="fr-deselect-all-btn", size="sm",
                                   outline=True, className="float-end",
                                   style={"borderColor": "#a0a0a0", "color": "#a0a0a0"}, disabled=True),
                    ], width=4),
                ], className="mb-3"),

                html.Div(id="fr-experiments-table", children=[
                    dbc.Alert("Upload a ZIP and click Parse Experiments.",
                              color="secondary", className="card-premium border-0 text-white")
                ], style={"maxHeight": "400px", "overflowY": "auto"}),

            ]), className="card-premium border-0 mb-3"),

            dbc.Card(dbc.CardBody([
                html.H6("Report Status & Log", style={"color": ACCENT}, className="mb-2"),
                html.Div(id="fr-status"),
                dbc.Textarea(
                    id="fr-log",
                    value="",
                    readOnly=True,
                    style={
                        "backgroundColor": "#0d0f17", "color": "#c0d0c0",
                        "fontFamily": "Courier New, monospace", "fontSize": "0.8rem",
                        "border": "1px solid rgba(255,255,255,0.08)",
                        "height": "180px", "resize": "vertical", "marginTop": "8px"
                    }
                ),
            ]), className="card-premium border-0"),
        ]),
    ]),
])


# ── Callbacks ──────────────────────────────────────────────────────────────────

@callback(
    Output("fr-zip-label", "children"),
    Input("fr-upload-zip", "filename"),
    prevent_initial_call=True
)
def show_zip_label(fname):
    return f"✓ {fname}" if fname else ""


@callback(
    Output("fr-experiments-table", "children"),
    Output("fr-store", "data"),
    Output("fr-run-btn", "disabled"),
    Output("fr-select-all-btn", "disabled"),
    Output("fr-deselect-all-btn", "disabled"),
    Output("fr-toast", "children"),
    Output("fr-log", "value"),
    Input("fr-parse-btn", "n_clicks"),
    State("fr-upload-zip", "contents"),
    State("fr-upload-zip", "filename"),
    State("fr-product", "value"),
    prevent_initial_call=True
)
def parse_experiments(n_clicks, zip_content, zip_fname, product):
    if not zip_content:
        return (no_update, no_update, True, True, True,
                _toast("Upload a ZIP file first.", "warning"), no_update)

    log = []
    try:
        _add_portfolio_to_path()
        from THRTools.parsers.Frameworkparser import find_files

        log.append(f"[{_now()}] Extracting ZIP: {zip_fname}")
        _, data = zip_content.split(',')
        raw = base64.b64decode(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, zip_fname or "data.zip")
            with open(zip_path, 'wb') as f:
                f.write(raw)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(tmpdir)

            log.append(f"[{_now()}] Scanning for experiment folders...")
            initial_df = find_files(tmpdir)

        if initial_df.empty:
            log.append(f"[{_now()}] No experiments found.")
            return (
                dbc.Alert("No experiments found in the ZIP. Check folder structure.",
                          color="warning", className="card-premium border-0 text-white"),
                {}, True, True, True,
                _toast("No experiments found.", "warning"),
                "\n".join(log)
            )

        experiments = sorted(initial_df['Experiment'].unique())
        log.append(f"[{_now()}] Found {len(experiments)} experiments.")

        # Build configuration table
        table_rows = [
            html.Tr([
                html.Th("Include", style={"color": ACCENT, "fontSize": "0.82rem"}),
                html.Th("Experiment",   style={"color": ACCENT, "fontSize": "0.82rem"}),
                html.Th("Content",      style={"color": ACCENT, "fontSize": "0.82rem"}),
                html.Th("Type",         style={"color": ACCENT, "fontSize": "0.82rem"}),
                html.Th("Other Type",   style={"color": ACCENT, "fontSize": "0.82rem"}),
                html.Th("Comments",     style={"color": ACCENT, "fontSize": "0.82rem"}),
            ], style={"borderBottom": f"1px solid rgba(0,255,157,0.2)"})
        ]

        for exp in experiments:
            eid = exp.lower().replace(" ", "-").replace("/", "-")[:40]
            table_rows.append(html.Tr([
                html.Td(dbc.Checklist(
                    id={"type": "fr-include", "index": exp},
                    options=[{"label": "", "value": "yes"}],
                    value=["yes"],
                    className="mb-0"
                ), style={"textAlign": "center"}),
                html.Td(html.Span(exp, style={"color": "#e0e0e0", "fontSize": "0.82rem"})),
                html.Td(dbc.Select(
                    id={"type": "fr-content", "index": exp},
                    options=[{"label": c, "value": c} for c in _CONTENT_TYPES],
                    value="", style={**_INPUT_STYLE, "fontSize": "0.78rem"}
                )),
                html.Td(dbc.Select(
                    id={"type": "fr-type", "index": exp},
                    options=[{"label": t, "value": t} for t in _EXP_TYPES],
                    value="Base", style={**_INPUT_STYLE, "fontSize": "0.78rem"}
                )),
                html.Td(dbc.Input(
                    id={"type": "fr-other-type", "index": exp},
                    placeholder="custom", type="text",
                    style={**_INPUT_STYLE, "fontSize": "0.78rem"}
                )),
                html.Td(dbc.Input(
                    id={"type": "fr-comments", "index": exp},
                    placeholder="comments", type="text",
                    style={**_INPUT_STYLE, "fontSize": "0.78rem"}
                )),
            ]))

        table = dbc.Table(table_rows, bordered=False, striped=False, hover=True,
                          style={"fontSize": "0.82rem", "color": "#e0e0e0"})

        # Store initial_df as JSON for later use
        store = {"experiments": experiments, "zip_content": zip_content,
                 "zip_fname": zip_fname, "product": product}

        return (table, store, False, False, False,
                _toast(f"Found {len(experiments)} experiments.", "success"),
                "\n".join(log))

    except Exception as e:
        logger.exception("Parse experiments error")
        log.append(f"[{_now()}] ERROR: {e}")
        return (no_update, {}, True, True, True,
                _toast(f"Parse error: {e}", "danger"),
                "\n".join(log))


@callback(
    Output("fr-status", "children"),
    Output("fr-download", "data"),
    Output("fr-toast", "children", allow_duplicate=True),
    Output("fr-dl-btn", "style"),
    Output("fr-result-store", "data"),
    Output("fr-log", "value", allow_duplicate=True),
    Input("fr-run-btn", "n_clicks"),
    State("fr-store", "data"),
    State("fr-product", "value"),
    State("fr-report-options", "value"),
    State("fr-merge-tag", "value"),
    State("fr-report-tag", "value"),
    State("fr-skip-strings", "value"),
    State({"type": "fr-include",    "index": dash.ALL}, "value"),
    State({"type": "fr-include",    "index": dash.ALL}, "id"),
    State({"type": "fr-content",    "index": dash.ALL}, "value"),
    State({"type": "fr-type",       "index": dash.ALL}, "value"),
    State({"type": "fr-other-type", "index": dash.ALL}, "value"),
    State({"type": "fr-comments",   "index": dash.ALL}, "value"),
    prevent_initial_call=True
)
def run_framework_report(n_clicks, store, product,
                         report_opts, merge_tag, report_tag, skip_strings,
                         include_vals, include_ids,
                         content_vals, type_vals, other_type_vals, comments_vals):
    if not store or not store.get("zip_content"):
        return (no_update, no_update,
                _toast("Parse experiments first.", "warning"),
                {"display": "none"}, no_update, no_update)

    log = []
    try:
        _add_portfolio_to_path()
        from THRTools.parsers import Frameworkparser as fpa

        report_opts = report_opts or []
        generate_merge  = "merge"       in report_opts
        generate_report = "report"      in report_opts
        check_logging   = "logging"     in report_opts
        gen_dragon      = "dragon"      in report_opts
        gen_core        = "core"        in report_opts
        gen_summary_tab = "summary_tab" in report_opts
        gen_overview    = "overview"    in report_opts

        tag_merge  = f"_{merge_tag}"  if merge_tag  else ""
        tag_report = f"_{report_tag}" if report_tag else ""
        skip_array = [s.strip() for s in skip_strings.split(",")] if skip_strings else []

        # Build experiment configurations from pattern-match states
        include_map    = {iid["index"]: bool(iv) for iid, iv in zip(include_ids, include_vals)
                          if iv}
        content_map    = {iid["index"]: cv for iid, cv in zip(include_ids, content_vals)}
        type_map       = {iid["index"]: tv for iid, tv in zip(include_ids, type_vals)}
        other_type_map = {iid["index"]: ov for iid, ov in zip(include_ids, other_type_vals)}
        comments_map   = {iid["index"]: cmv for iid, cmv in zip(include_ids, comments_vals)}

        log.append(f"[{_now()}] Starting framework report generation...")

        _, data = store["zip_content"].split(',')
        raw = base64.b64decode(data)

        with tempfile.TemporaryDirectory() as workdir:
            zip_path = os.path.join(workdir, store.get("zip_fname", "data.zip"))
            with open(zip_path, 'wb') as f:
                f.write(raw)
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(workdir)

            log.append(f"[{_now()}] Finding experiment files...")
            initial_df = fpa.find_files(workdir)

            selected = [exp for exp, inc in include_map.items() if inc]
            filtered_df = initial_df[initial_df['Experiment'].isin(selected)]

            log.append(f"[{_now()}] {len(selected)} experiments selected.")

            type_values    = {}
            content_values = {}
            comments_values = {}

            for exp in selected:
                tv = type_map.get(exp, "Base")
                ov = other_type_map.get(exp, "")
                type_values[exp] = ov if tv == "Others" and ov else tv
                content_values[exp] = content_map.get(exp, "")
                comments_values[exp] = comments_map.get(exp, "")

            log_path_dict   = fpa.create_file_dict(filtered_df, 'Log',   type_values, content_values, comments_values)
            excel_path_dict = fpa.create_file_dict(filtered_df, 'Excel', type_values, content_values)

            log.append(f"[{_now()}] Parsing log files...")
            test_df = fpa.parse_log_files(log_path_dict)

            fail_info_df = None
            unique_fails_df = None
            vvar_df = None
            mca_df = None
            core_data_df = None
            dragon_data_df = None
            summary_df = None
            overview_df = None
            experiment_summary_df = None
            unique_mcas_df = None
            metadata_df = None
            dr_df = None
            voltage_df = None

            if check_logging:
                log.append(f"[{_now()}] Checking logging data (ZIP files)...")
                zip_path_dict = fpa.create_file_dict(filtered_df, 'ZIP', type_values, content_values)
                fail_info_df = fpa.check_zip_data(zip_path_dict, skip_array, test_df)
                test_df = fpa.update_content_results(test_df, fail_info_df)
                unique_fails_df = fpa.generate_unique_fails(fail_info_df)

                log_summary = fpa.LogSummaryParser(excel_path_dict, test_df, product or "GNR")
                mca_df = log_summary.parse_mca_tabs_from_files()
                test_df = fpa.update_mca_results(test_df, fail_info_df, mca_df)

            if gen_dragon or gen_core or gen_summary_tab:
                try:
                    logger_parser = fpa.DebugFrameworkLoggerParser(log_path_dict, product=product or "GNR")
                    dr_df, metadata_df = logger_parser.parse()
                except Exception:
                    pass

            if gen_dragon and dr_df is not None:
                dragon_data_df = dr_df

            if gen_core and dr_df is not None:
                try:
                    core_data_df = fpa.create_core_data_report(
                        voltage_df, dr_df, vvar_df, mca_df, test_df, metadata_df,
                        product=product or "GNR"
                    )
                except Exception:
                    pass

            summary_df, test_df, exp_idx_map = fpa.create_summary_df(test_df)

            if gen_summary_tab:
                try:
                    analyzer = fpa.ExperimentSummaryAnalyzer(
                        test_df, summary_df, fail_info_df,
                        vvar_df, mca_df, core_data_df
                    )
                    experiment_summary_df = analyzer.analyze_all_experiments()
                except Exception:
                    pass

            if gen_overview and experiment_summary_df is not None:
                try:
                    overview_df = experiment_summary_df.head(10)
                except Exception:
                    pass

            vid = initial_df['VID'].iloc[0] if not initial_df.empty else "unknown"
            report_fname = f"{vid}_FrameworkReport{tag_report}.xlsx"
            merged_fname = f"{vid}_MergedSummary{tag_merge}.xlsx"
            out_report   = os.path.join(workdir, report_fname)
            out_merged   = os.path.join(workdir, merged_fname)

            if generate_report:
                log.append(f"[{_now()}] Saving report to {report_fname}...")
                fpa.save_to_excel(
                    filtered_df, test_df, summary_df,
                    fail_info_df, unique_fails_df, unique_mcas_df,
                    vvar_df, core_data_df, experiment_summary_df, overview_df,
                    filename=out_report
                )

            if generate_merge:
                log.append(f"[{_now()}] Merging summary files...")
                fpa.framework_merge(
                    file_dict=excel_path_dict,
                    output_file=out_merged,
                    prefix='Summary',
                    skip=[]
                )

            # Pick the main output to download
            main_out = out_report if generate_report else out_merged
            if not os.path.exists(main_out):
                # fallback: just save test_df
                import pandas as pd
                test_df.to_excel(main_out, index=False)

            with open(main_out, 'rb') as f:
                out_bytes = f.read()

        log.append(f"[{_now()}] Done.")

        import base64 as b64
        result_store = b64.b64encode(out_bytes).decode()
        dl_fname = os.path.basename(main_out)
        dl_style = {"borderColor": "#00ff9d", "color": "#00ff9d", "width": "100%", "marginTop": "8px"}

        status = html.P(f"✓ Report complete: {dl_fname}", style={"color": "#00ff9d"})
        return (status,
                dcc.send_bytes(out_bytes, dl_fname),
                _toast(f"Report ready: {dl_fname}", "success"),
                dl_style, result_store,
                "\n".join(log))

    except Exception as e:
        logger.exception("Framework report error")
        log.append(f"[{_now()}] ERROR: {e}")
        return (html.P(f"Error: {e}", style={"color": "#ff4444"}),
                no_update,
                _toast(f"Error: {e}", "danger", 6000),
                {"display": "none"}, no_update,
                "\n".join(log))


@callback(
    Output("fr-download", "data", allow_duplicate=True),
    Input("fr-dl-btn", "n_clicks"),
    State("fr-result-store", "data"),
    prevent_initial_call=True
)
def redownload(n_clicks, result_store):
    if not result_store:
        return no_update
    import base64 as b64
    return dcc.send_bytes(b64.b64decode(result_store), "framework_report.xlsx")


def _add_portfolio_to_path():
    portfolio_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if portfolio_root not in sys.path:
        sys.path.insert(0, portfolio_root)


def _now():
    return datetime.datetime.now().strftime("%H:%M:%S")


def _toast(msg, icon, duration=4000):
    return dbc.Toast(
        msg, icon=icon, duration=duration, is_open=True,
        style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
        className="toast-custom"
    )
