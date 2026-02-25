"""
Fuse File Generator
====================
Generate fuse configuration files from CSV fuse definitions.
Calls THRTools/utils/fusefilegenerator.py backend.
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
    path='/thr-tools/fuse-generator',
    name='Fuse File Generator',
    title='Fuse File Generator'
)

ACCENT = "#ff9f45"

_PRODUCTS = ["GNR", "CWF", "DMR", "SRF"]

layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="fg-toast"),
    dcc.Download(id="fg-download"),

    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-cpu me-2", style={"color": ACCENT}),
            html.Span("Fuse File Generator", style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P("Generate fuse configuration files from CSV fuse definitions.",
               style={"color": "#a0a0a0", "fontSize": "0.9rem"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        dbc.Col(md=4, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Generator Configuration", className="mb-3", style={"color": ACCENT}),

                html.Label("Product", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Select(
                    id="fg-product",
                    options=[{"label": p, "value": p} for p in _PRODUCTS],
                    value="GNR",
                    className="mb-3",
                    style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                           "border": "1px solid rgba(255,255,255,0.1)"}
                ),

                html.Label("Upload compute.csv", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Upload(
                    id="fg-upload-compute",
                    children=html.Div([
                        html.I(className="bi bi-upload me-2", style={"color": ACCENT}),
                        "compute.csv or ", html.A("browse", style={"color": ACCENT})
                    ]),
                    multiple=False, className="mt-1 mb-2",
                    style={
                        "border": f"1px dashed {ACCENT}", "borderRadius": "8px",
                        "padding": "12px", "textAlign": "center",
                        "color": "#a0a0a0", "fontSize": "0.85rem",
                        "backgroundColor": "rgba(255,159,69,0.04)", "cursor": "pointer"
                    }
                ),
                html.Div(id="fg-compute-label",
                         style={"color": "#a0a0a0", "fontSize": "0.8rem", "marginBottom": "8px"}),

                html.Label("Upload io.csv", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Upload(
                    id="fg-upload-io",
                    children=html.Div([
                        html.I(className="bi bi-upload me-2", style={"color": ACCENT}),
                        "io.csv or ", html.A("browse", style={"color": ACCENT})
                    ]),
                    multiple=False, className="mt-1 mb-3",
                    style={
                        "border": f"1px dashed {ACCENT}", "borderRadius": "8px",
                        "padding": "12px", "textAlign": "center",
                        "color": "#a0a0a0", "fontSize": "0.85rem",
                        "backgroundColor": "rgba(255,159,69,0.04)", "cursor": "pointer"
                    }
                ),
                html.Div(id="fg-io-label",
                         style={"color": "#a0a0a0", "fontSize": "0.8rem", "marginBottom": "8px"}),

                html.Label("Output Filename", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Input(id="fg-output-name", placeholder="output.fuse", type="text",
                          className="mb-3",
                          style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                 "border": "1px solid rgba(255,255,255,0.1)"}),

                dbc.Button(
                    [html.I(className="bi bi-gear-wide-connected me-2"), "Load CSV Files"],
                    id="fg-load-btn",
                    color="warning", outline=True, className="w-100 mb-2",
                    style={"borderColor": ACCENT, "color": ACCENT}
                ),

                dbc.Button(
                    [html.I(className="bi bi-download me-2"), "Generate Fuse File"],
                    id="fg-gen-btn",
                    color="warning", outline=True, className="w-100",
                    style={"borderColor": ACCENT, "color": ACCENT}, disabled=True
                ),
            ]), className="card-premium border-0"),
        ]),

        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Fuse Selection", style={"color": ACCENT}, className="mb-3"),
                html.Div(id="fg-fuse-area", children=[
                    dbc.Alert("Load CSV files to view available fuses.",
                              color="secondary", className="card-premium border-0 text-white")
                ]),
                html.Div(id="fg-status", className="mt-3")
            ]), className="card-premium border-0"),
        ]),
    ]),

    # Hidden store for loaded fuse data
    dcc.Store(id="fg-fuse-store"),
])


@callback(
    Output("fg-compute-label", "children"),
    Input("fg-upload-compute", "filename"),
    prevent_initial_call=True
)
def show_compute(fname):
    return f"Selected: {fname}" if fname else ""


@callback(
    Output("fg-io-label", "children"),
    Input("fg-upload-io", "filename"),
    prevent_initial_call=True
)
def show_io(fname):
    return f"Selected: {fname}" if fname else ""


@callback(
    Output("fg-fuse-area", "children"),
    Output("fg-fuse-store", "data"),
    Output("fg-gen-btn", "disabled"),
    Output("fg-toast", "children"),
    Input("fg-load-btn", "n_clicks"),
    State("fg-upload-compute", "contents"),
    State("fg-upload-compute", "filename"),
    State("fg-upload-io", "contents"),
    State("fg-upload-io", "filename"),
    State("fg-product", "value"),
    prevent_initial_call=True
)
def load_fuses(n_clicks, compute_content, compute_fname, io_content, io_fname, product):
    if not compute_content or not io_content:
        return no_update, no_update, True, dbc.Toast(
            "Upload both compute.csv and io.csv first.", icon="warning", duration=3000,
            is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
            className="toast-custom")

    try:
        import tempfile
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from THRTools.utils.fusefilegenerator import FuseFileGenerator

        with tempfile.TemporaryDirectory() as tmpdir:
            for content, fname in [(compute_content, compute_fname), (io_content, io_fname)]:
                _, data = content.split(',')
                with open(os.path.join(tmpdir, fname), 'wb') as f:
                    f.write(base64.b64decode(data))

            gen = FuseFileGenerator(product=product)
            gen.load_csv_files(tmpdir)

            fuses = getattr(gen, 'available_fuses', []) or getattr(gen, 'fuses', []) or []
            ips = getattr(gen, 'ip_assignments', {}) or {}

        store_data = {"product": product, "fuses": fuses, "ips": ips,
                      "compute_content": compute_content, "compute_fname": compute_fname,
                      "io_content": io_content, "io_fname": io_fname}

        fuse_options = [{"label": f, "value": f} for f in fuses] if fuses else []
        ip_options = list(ips.keys()) if isinstance(ips, dict) else []

        fuse_area = html.Div([
            html.H6(f"Available Fuses ({product})", style={"color": "#a0a0a0"}, className="mb-2"),
            dbc.Checklist(
                id="fg-selected-fuses",
                options=fuse_options,
                value=[f["value"] for f in fuse_options],
                inputStyle={"marginRight": "6px"},
                labelStyle={"color": "#e0e0e0", "fontSize": "0.88rem"},
            ) if fuse_options else dbc.Alert("No fuses found in CSVs.", color="secondary",
                                             className="card-premium border-0 text-white"),
            html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),
            html.H6("IP Assignments", style={"color": "#a0a0a0"}, className="mb-2"),
            html.P(", ".join(ip_options) if ip_options else "None found",
                   style={"color": "#e0e0e0", "fontSize": "0.85rem"}),
        ])

        return fuse_area, store_data, False, dbc.Toast(
            f"Loaded {len(fuses)} fuses.", icon="success", duration=3000,
            is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
            className="toast-custom")

    except Exception as e:
        logger.exception("Fuse load error")
        return no_update, no_update, True, dbc.Toast(
            f"Error loading fuses: {str(e)}", icon="danger", duration=5000,
            is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
            className="toast-custom")


@callback(
    Output("fg-status", "children"),
    Output("fg-download", "data"),
    Output("fg-toast", "children", allow_duplicate=True),
    Input("fg-gen-btn", "n_clicks"),
    State("fg-fuse-store", "data"),
    State("fg-selected-fuses", "value"),
    State("fg-output-name", "value"),
    prevent_initial_call=True
)
def generate_fuse_file(n_clicks, store_data, selected_fuses, output_name):
    if not store_data:
        return no_update, no_update, dbc.Toast("Load CSV files first.", icon="warning",
                                                duration=3000, is_open=True,
                                                style={"position": "fixed", "top": 20, "right": 20,
                                                       "zIndex": 9999}, className="toast-custom")
    try:
        import tempfile
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from THRTools.utils.fusefilegenerator import FuseFileGenerator

        out_fname = output_name or "output.fuse"

        with tempfile.TemporaryDirectory() as tmpdir:
            for content, fname in [
                (store_data["compute_content"], store_data["compute_fname"]),
                (store_data["io_content"], store_data["io_fname"])
            ]:
                _, data = content.split(',')
                with open(os.path.join(tmpdir, fname), 'wb') as f:
                    f.write(base64.b64decode(data))

            gen = FuseFileGenerator(product=store_data["product"])
            gen.load_csv_files(tmpdir)
            out_path = os.path.join(tmpdir, out_fname)
            gen.generate_fuse_file(
                selected_fuses=selected_fuses or [],
                ip_assignments=store_data.get("ips", {}),
                output_file=out_path
            )

            if os.path.exists(out_path):
                with open(out_path, 'rb') as f:
                    out_bytes = f.read()
            else:
                out_bytes = b""

        status = html.P(f"✓ Fuse file generated: {out_fname}", style={"color": "#00ff9d"})
        return (status,
                dcc.send_bytes(out_bytes, out_fname),
                dbc.Toast("Fuse file generated. Downloading...", icon="success", duration=4000,
                          is_open=True, style={"position": "fixed", "top": 20, "right": 20,
                                               "zIndex": 9999}, className="toast-custom"))

    except Exception as e:
        logger.exception("Fuse generation error")
        return (no_update, no_update,
                dbc.Toast(f"Error: {str(e)}", icon="danger", duration=5000, is_open=True,
                          style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                          className="toast-custom"))
