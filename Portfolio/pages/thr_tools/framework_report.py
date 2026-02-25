"""
Framework Report Builder
=========================
Build experiment summary reports from DebugFramework output files.
Calls THRTools/parsers/FrameworkAnalyzer.py backend.
"""
import logging
import base64
import os
import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

dash.register_page(
    __name__,
    path='/thr-tools/framework-report',
    name='Framework Report',
    title='Framework Report Builder'
)

ACCENT = "#00ff9d"

_FILE_SPECS = [
    ("fr-upload-test",    "fr-test-label",    "Test DataFrame (test.xlsx / .csv)",        "test"),
    ("fr-upload-summary", "fr-summary-label", "Summary DataFrame (summary.xlsx / .csv)",  "summary"),
    ("fr-upload-fail",    "fr-fail-label",    "Fail Info DataFrame (failinfo.xlsx / .csv)", "fail"),
    ("fr-upload-vvar",    "fr-vvar-label",    "VVAR DataFrame (vvar.xlsx / .csv)",         "vvar"),
    ("fr-upload-mca",     "fr-mca-label",     "MCA DataFrame (mca.xlsx / .csv)",           "mca"),
    ("fr-upload-core",    "fr-core-label",    "Core Data DataFrame (core.xlsx / .csv)",    "core"),
    ("fr-upload-dragon",  "fr-dragon-label",  "Dragon Data DataFrame (dragon.xlsx / .csv)", "dragon"),
]


def _upload_card(upload_id, label_id, label_text, key):
    return html.Div([
        html.Label(label_text, style={"color": "#a0a0a0", "fontSize": "0.8rem"}),
        dcc.Upload(
            id=upload_id,
            children=html.Div([
                html.A("Browse", style={"color": ACCENT}), " or drop file"
            ]),
            multiple=False,
            style={
                "border": f"1px dashed {ACCENT}", "borderRadius": "6px",
                "padding": "8px", "textAlign": "center",
                "color": "#a0a0a0", "fontSize": "0.8rem",
                "backgroundColor": "rgba(0,255,157,0.03)", "cursor": "pointer"
            }
        ),
        html.Div(id=label_id, style={"color": "#a0a0a0", "fontSize": "0.75rem", "marginTop": "3px"})
    ], className="mb-2")


layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="fr-toast"),
    dcc.Download(id="fr-download"),
    dcc.Store(id="fr-store"),

    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-clipboard-data me-2", style={"color": ACCENT}),
            html.Span("Framework Report Builder",
                      style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P("Build multi-sheet experiment summary reports using DebugFramework output DataFrames.",
               style={"color": "#a0a0a0", "fontSize": "0.9rem"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        dbc.Col(md=4, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Input DataFrames", className="mb-3", style={"color": ACCENT}),

                _upload_card("fr-upload-test", "fr-test-label",
                             "Test DataFrame (test.xlsx / .csv)", "test"),
                _upload_card("fr-upload-summary", "fr-summary-label",
                             "Summary DataFrame (summary.xlsx / .csv)", "summary"),
                _upload_card("fr-upload-fail", "fr-fail-label",
                             "Fail Info DataFrame (failinfo.xlsx / .csv)", "fail"),
                _upload_card("fr-upload-vvar", "fr-vvar-label",
                             "VVAR DataFrame (vvar.xlsx / .csv)", "vvar"),
                _upload_card("fr-upload-mca", "fr-mca-label",
                             "MCA DataFrame (mca.xlsx / .csv)", "mca"),
                _upload_card("fr-upload-core", "fr-core-label",
                             "Core Data DataFrame (core.xlsx / .csv)", "core"),
                _upload_card("fr-upload-dragon", "fr-dragon-label",
                             "Dragon Data DataFrame (dragon.xlsx / .csv)", "dragon"),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                html.Label("Output Report Name", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Input(id="fr-output-name", placeholder="framework_report.xlsx", type="text",
                          className="mb-3",
                          style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                 "border": "1px solid rgba(255,255,255,0.1)"}),

                dbc.Button(
                    [html.I(className="bi bi-file-earmark-excel me-2"), "Build Report"],
                    id="fr-run-btn",
                    outline=True, className="w-100",
                    style={"borderColor": ACCENT, "color": ACCENT}
                ),
            ]), className="card-premium border-0"),
        ]),

        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Report Output", style={"color": ACCENT}, className="mb-3"),
                html.Div(id="fr-status", children=[
                    dbc.Alert("Upload DataFrames and click Build Report.",
                              color="secondary", className="card-premium border-0 text-white")
                ])
            ]), className="card-premium border-0"),
        ]),
    ]),
])


def _register_label_callbacks():
    for upload_id, label_id, _, _ in _FILE_SPECS:
        @callback(
            Output(label_id, "children"),
            Input(upload_id, "filename"),
            prevent_initial_call=True
        )
        def _cb(fname):
            return f"✓ {fname}" if fname else ""


_register_label_callbacks()


@callback(
    Output("fr-status", "children"),
    Output("fr-download", "data"),
    Output("fr-toast", "children"),
    Input("fr-run-btn", "n_clicks"),
    State("fr-upload-test", "contents"),    State("fr-upload-test", "filename"),
    State("fr-upload-summary", "contents"), State("fr-upload-summary", "filename"),
    State("fr-upload-fail", "contents"),    State("fr-upload-fail", "filename"),
    State("fr-upload-vvar", "contents"),    State("fr-upload-vvar", "filename"),
    State("fr-upload-mca", "contents"),     State("fr-upload-mca", "filename"),
    State("fr-upload-core", "contents"),    State("fr-upload-core", "filename"),
    State("fr-upload-dragon", "contents"),  State("fr-upload-dragon", "filename"),
    State("fr-output-name", "value"),
    prevent_initial_call=True
)
def build_report(n_clicks,
                 test_c, test_f, sum_c, sum_f, fail_c, fail_f,
                 vvar_c, vvar_f, mca_c, mca_f, core_c, core_f,
                 dragon_c, dragon_f, output_name):
    import tempfile
    import pandas as pd
    import sys

    def _df_from_upload(content, fname):
        if not content:
            return None
        _, data = content.split(',')
        raw = base64.b64decode(data)
        bio = __import__('io').BytesIO(raw)
        if fname and fname.endswith('.csv'):
            return pd.read_csv(bio)
        return pd.read_excel(bio)

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from THRTools.parsers.FrameworkAnalyzer import ExperimentSummaryAnalyzer

        dfs = {
            "test":   _df_from_upload(test_c, test_f),
            "summary": _df_from_upload(sum_c, sum_f),
            "fail":   _df_from_upload(fail_c, fail_f),
            "vvar":   _df_from_upload(vvar_c, vvar_f),
            "mca":    _df_from_upload(mca_c, mca_f),
            "core":   _df_from_upload(core_c, core_f),
            "dragon": _df_from_upload(dragon_c, dragon_f),
        }

        missing = [k for k, v in dfs.items() if v is None]
        if missing:
            warn = dbc.Alert(
                [html.I(className="bi bi-exclamation-triangle me-2"),
                 f"Missing DataFrames: {', '.join(missing)}. Proceeding with available data."],
                color="warning", className="card-premium border-0 text-white mb-3")
        else:
            warn = None

        def _safe(key):
            return dfs[key] if dfs[key] is not None else pd.DataFrame()

        analyzer = ExperimentSummaryAnalyzer(
            test_df=_safe("test"),
            summary_df=_safe("summary"),
            fail_info_df=_safe("fail"),
            vvar_df=_safe("vvar"),
            mca_df=_safe("mca"),
            core_data_df=_safe("core"),
            dragon_data_df=_safe("dragon"),
        )
        result_df = analyzer.analyze_all_experiments()

        with tempfile.TemporaryDirectory() as tmpdir:
            out_name = output_name or "framework_report.xlsx"
            out_path = os.path.join(tmpdir, out_name)
            result_df.to_excel(out_path, index=False)
            with open(out_path, 'rb') as f:
                out_bytes = f.read()

        rows, cols = result_df.shape
        status_rows = [
            warn,
            html.P(f"✓ Analysis complete: {rows} experiments, {cols} columns",
                   style={"color": "#00ff9d"}),
            html.P(f"Columns: {', '.join(str(c) for c in result_df.columns[:8])}...",
                   style={"color": "#a0a0a0", "fontSize": "0.85rem"}),
        ]
        status = html.Div([r for r in status_rows if r])

        return (status,
                dcc.send_bytes(out_bytes, out_name),
                dbc.Toast("Report built. Downloading...", icon="success", duration=4000,
                          is_open=True, style={"position": "fixed", "top": 20, "right": 20,
                                               "zIndex": 9999}, className="toast-custom"))

    except Exception as e:
        logger.exception("Framework report error")
        return (no_update, no_update,
                dbc.Toast(f"Error: {str(e)}", icon="danger", duration=5000, is_open=True,
                          style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                          className="toast-custom"))
