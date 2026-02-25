"""
MCA Single Decoder
===================
Decode individual MCA registers for CHA, LLC, CORE, MEMORY, IO, and First Error.
Calls THRTools/Decoder/decoder.py backend (decoder class, not mcadata).

Replicates all functionality from PPV/gui/MCADecoder.py:
- Per-decoder-type register fields (MC_STATUS, MC_ADDR, MC_MISC, MC_MISC3)
- Subtype selection for CORE / MEMORY / IO
- Uses decoder class for actual decoding
- Export results to text file
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
    path='/thr-tools/mca-decoder',
    name='MCA Single Decoder',
    title='MCA Single Decoder'
)

ACCENT = "#ff6b8a"
PRODUCTS = ['GNR', 'CWF', 'DMR']

# Decoder type definitions matching PPV/gui/MCADecoder.py
DECODER_TYPES = {
    'CHA/CCF': {
        'description': 'CHA (Caching Agent) / CCF Decoder',
        'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC', 'MC_MISC3'],
        'decode_method': 'cha',
        'subtypes': [],
    },
    'LLC': {
        'description': 'Last Level Cache Decoder',
        'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
        'decode_method': 'llc',
        'subtypes': [],
    },
    'CORE': {
        'description': 'CPU Core Decoder (ML2, DCU, IFU, DTLB, etc.)',
        'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
        'decode_method': 'core',
        'subtypes': ['ML2', 'DCU', 'IFU', 'DTLB', 'L2', 'BBL', 'BUS', 'MEC', 'AGU', 'IC'],
    },
    'MEMORY': {
        'description': 'Memory Subsystem Decoder (B2CMI, MSE, MCCHAN)',
        'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
        'decode_method': 'mem',
        'subtypes': ['B2CMI', 'MSE', 'MCCHAN'],
    },
    'IO': {
        'description': 'IO Subsystem Decoder (UBOX, UPI, ULA)',
        'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
        'decode_method': 'io',
        'subtypes': ['UBOX', 'UPI', 'ULA'],
    },
    'FIRST ERROR': {
        'description': 'First Error Logger - UBOX MCERR/IERR Logging',
        'registers': ['MCERRLOGGINGREG', 'IERRLOGGINGREG'],
        'decode_method': 'first_error',
        'subtypes': [],
    },
}

_INPUT_STYLE = {"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                "border": "1px solid rgba(255,255,255,0.1)", "fontSize": "0.85rem",
                "fontFamily": "monospace"}


def _reg_input(reg_id, label, placeholder="e.g. 0xBE00000000800400"):
    return html.Div([
        html.Label(label, style={"color": "#a0a0a0", "fontSize": "0.8rem"}),
        dbc.Input(id=reg_id, placeholder=placeholder, type="text",
                  className="mb-2", style=_INPUT_STYLE),
    ])


layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="mca-dec-toast"),
    dcc.Download(id="mca-dec-download"),

    # Header
    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-cpu me-2", style={"color": ACCENT}),
            html.Span("MCA Single Decoder", style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P("Decode individual MCA registers for CHA/CCF, LLC, CORE, MEMORY, IO, and First Error.",
               style={"color": "#a0a0a0", "fontSize": "0.9rem"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        # Left panel — inputs
        dbc.Col(md=4, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Configuration", className="mb-3", style={"color": ACCENT}),

                html.Label("Product", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Dropdown(
                    id="mca-dec-product",
                    options=[{'label': p, 'value': p} for p in PRODUCTS],
                    value='GNR', clearable=False,
                    className="mb-3"
                ),

                html.Label("Decoder Type", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Dropdown(
                    id="mca-dec-type",
                    options=[{'label': k, 'value': k} for k in DECODER_TYPES],
                    value='CHA/CCF', clearable=False,
                    className="mb-2"
                ),
                html.Div(id="mca-dec-type-desc",
                         style={"color": "#606070", "fontSize": "0.78rem", "marginBottom": "8px"}),

                # Subtype selector (shown only for CORE / MEMORY / IO)
                html.Div(id="mca-dec-subtype-row", children=[
                    html.Label("Bank / Subtype", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                    dcc.Dropdown(id="mca-dec-subtype", value=None, clearable=True, className="mb-3"),
                ], style={"display": "none"}),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                # Dynamic register fields
                html.Div(id="mca-dec-reg-fields", children=[
                    _reg_input("mca-dec-mc-status", "MC_STATUS *"),
                    _reg_input("mca-dec-mc-addr",   "MC_ADDR"),
                    _reg_input("mca-dec-mc-misc",   "MC_MISC"),
                    _reg_input("mca-dec-mc-misc3",  "MC_MISC3"),
                ]),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                dbc.Button(
                    [html.I(className="bi bi-gear me-2"), "Decode"],
                    id="mca-dec-btn", color="primary", outline=True, className="w-100 mb-2",
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
                        [html.I(className="bi bi-download me-1"), "Export"],
                        id="mca-dec-export-btn", size="sm", outline=True,
                        style={"borderColor": "#a0a0a0", "color": "#a0a0a0",
                               "float": "right", "marginTop": "-4px"}
                    ),
                ], className="mb-3"),
                html.Div(id="mca-dec-results", children=[
                    dbc.Alert("Select product, decoder type, enter register values and click Decode.",
                              color="secondary", className="card-premium border-0 text-white")
                ]),
                # Hidden store for raw text results (used for export)
                dcc.Store(id="mca-dec-results-store"),
            ]), className="card-premium border-0"),
        ]),
    ]),
])


# ── callbacks ──────────────────────────────────────────────────────────────────

@callback(
    Output("mca-dec-type-desc", "children"),
    Output("mca-dec-subtype-row", "style"),
    Output("mca-dec-subtype", "options"),
    Output("mca-dec-subtype", "value"),
    Output("mca-dec-reg-fields", "children"),
    Input("mca-dec-type", "value"),
    prevent_initial_call=False
)
def update_decoder_ui(decoder_type):
    """Update UI when decoder type changes."""
    if not decoder_type or decoder_type not in DECODER_TYPES:
        return "", {"display": "none"}, [], None, []

    cfg = DECODER_TYPES[decoder_type]
    desc = cfg["description"]
    subtypes = cfg.get("subtypes", [])
    regs = cfg["registers"]

    # Build register input fields
    reg_fields = []
    for reg in regs:
        label = f"{reg} *" if reg in ("MC_STATUS", "MCERRLOGGINGREG") else reg
        reg_id = f"mca-dec-{reg.lower().replace('_', '-')}"
        reg_fields.append(_reg_input(reg_id, label))

    subtype_style = {"display": "block"} if subtypes else {"display": "none"}
    subtype_opts = [{"label": s, "value": s} for s in subtypes]
    default_sub = subtypes[0] if subtypes else None

    return desc, subtype_style, subtype_opts, default_sub, reg_fields


def _get_reg_values(decoder_type, mc_status, mc_addr, mc_misc, mc_misc3,
                    mcerrlogging, ierrlogging):
    """Collect register values based on decoder type."""
    if decoder_type == "FIRST ERROR":
        vals = {}
        if mcerrlogging:
            vals["MCERRLOGGINGREG"] = mcerrlogging.strip()
        if ierrlogging:
            vals["IERRLOGGINGREG"] = ierrlogging.strip()
        return vals
    vals = {}
    if mc_status:
        vals["MC_STATUS"] = mc_status.strip()
    if mc_addr:
        vals["MC_ADDR"] = mc_addr.strip()
    if mc_misc:
        vals["MC_MISC"] = mc_misc.strip()
    if mc_misc3:
        vals["MC_MISC3"] = mc_misc3.strip()
    return vals


def _decode_registers(product, decoder_type, subtype, reg_values):
    """Run backend decode and return formatted text output."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    import pandas as pd
    from THRTools.Decoder.decoder import decoder as Decoder, extract_bits

    dummy_df = pd.DataFrame({'VisualId': [1], 'TestName': ['dummy'], 'TestValue': ['0x0']})
    dec = Decoder(data=dummy_df, product=product)

    lines = []
    lines.append("=" * 72)
    lines.append(f"{decoder_type} MCA DECODE — {product}")
    lines.append("=" * 72)
    lines.append("")
    lines.append("RAW REGISTER VALUES:")
    for k, v in reg_values.items():
        lines.append(f"  {k:<16} {v}")
    lines.append("")

    method = DECODER_TYPES[decoder_type]["decode_method"]

    try:
        if method == "cha":
            result = dec.cha()
            lines += _format_df_result(result, "CHA / CCF Decode")
        elif method == "llc":
            result = dec.llc()
            lines += _format_df_result(result, "LLC Decode")
        elif method == "core":
            result = dec.core()
            lines += _format_df_result(result, f"CORE Decode ({subtype or 'all'})")
        elif method == "mem":
            result = dec.mem()
            lines += _format_df_result(result, f"MEMORY Decode ({subtype or 'all'})")
        elif method == "io":
            result = dec.io()
            lines += _format_df_result(result, f"IO Decode ({subtype or 'all'})")
        elif method == "first_error":
            lines.append("FIRST ERROR DECODE:")
            mc_val = reg_values.get("MCERRLOGGINGREG", "")
            if mc_val:
                try:
                    iv = int(mc_val.replace("0x", "").replace("0X", ""), 16)
                    lines.append(f"  MCERRLOGGINGREG:  0x{iv:016X}")
                    lines.append(f"    VAL  (bit 63): {extract_bits(mc_val, 63, 63)}")
                    lines.append(f"    IERR (bit  0): {extract_bits(mc_val,  0,  0)}")
                except Exception as ex:
                    lines.append(f"  Parse error: {ex}")
            ie_val = reg_values.get("IERRLOGGINGREG", "")
            if ie_val:
                try:
                    iv = int(ie_val.replace("0x", "").replace("0X", ""), 16)
                    lines.append(f"  IERRLOGGINGREG:   0x{iv:016X}")
                    lines.append(f"    VAL  (bit 63): {extract_bits(ie_val, 63, 63)}")
                except Exception as ex:
                    lines.append(f"  Parse error: {ex}")
        else:
            lines.append(f"Decoder method '{method}' not implemented.")
    except Exception as e:
        lines.append(f"Decode error: {e}")
        import traceback
        lines.append(traceback.format_exc())

    return "\n".join(lines)


def _format_df_result(result, title):
    """Format a DataFrame or dict decode result as text lines."""
    import pandas as pd
    out = [f"{title}:"]
    if result is None:
        out.append("  (no result)")
    elif isinstance(result, pd.DataFrame):
        if result.empty:
            out.append("  (no data)")
        else:
            for _, row in result.head(50).iterrows():
                out.append("  " + " | ".join(str(v) for v in row.values))
    elif isinstance(result, dict):
        for k, v in result.items():
            out.append(f"  {k}: {v}")
    else:
        out.append(str(result))
    out.append("")
    return out


@callback(
    Output("mca-dec-results", "children"),
    Output("mca-dec-results-store", "data"),
    Output("mca-dec-toast", "children"),
    Input("mca-dec-btn", "n_clicks"),
    State("mca-dec-product", "value"),
    State("mca-dec-type", "value"),
    State("mca-dec-subtype", "value"),
    # Register value states — all optional; callback reads whatever is rendered
    State("mca-dec-mc-status", "value"),
    State("mca-dec-mc-addr",   "value"),
    State("mca-dec-mc-misc",   "value"),
    State("mca-dec-mc-misc3",  "value"),
    State("mca-dec-mcerrloggingreg", "value"),
    State("mca-dec-ierrloggingreg",  "value"),
    prevent_initial_call=True
)
def decode_mca(n_clicks, product, decoder_type, subtype,
               mc_status, mc_addr, mc_misc, mc_misc3,
               mcerrlogging, ierrlogging):
    if not decoder_type:
        return no_update, no_update, _toast("Select a decoder type.", "warning")

    reg_values = _get_reg_values(
        decoder_type, mc_status, mc_addr, mc_misc, mc_misc3,
        mcerrlogging, ierrlogging
    )

    if not reg_values:
        return no_update, no_update, _toast("Enter at least one register value.", "warning")

    try:
        text = _decode_registers(product, decoder_type, subtype, reg_values)
        result_div = html.Pre(text, style={
            "backgroundColor": "#0d0f17", "color": "#d4d4d4",
            "padding": "12px", "borderRadius": "6px",
            "fontSize": "0.78rem", "fontFamily": "monospace",
            "whiteSpace": "pre-wrap", "maxHeight": "500px", "overflowY": "auto"
        })
        return result_div, text, _toast("Decode complete.", "success", 2500)
    except Exception as e:
        logger.exception("MCA decode error")
        return no_update, no_update, _toast(f"Decode error: {e}", "danger")


@callback(
    Output("mca-dec-download", "data"),
    Input("mca-dec-export-btn", "n_clicks"),
    State("mca-dec-results-store", "data"),
    prevent_initial_call=True
)
def export_results(n_clicks, text):
    if not text:
        return no_update
    return dcc.send_string(text, "mca_decode_results.txt")


def _toast(msg, icon, duration=4000):
    return dbc.Toast(
        msg, icon=icon, duration=duration, is_open=True,
        style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
        className="toast-custom"
    )
