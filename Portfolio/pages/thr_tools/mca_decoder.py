"""
MCA Single Decoder
==================
Interactive interface for decoding individual MCA register values.
Faithfully replicates PPV/gui/MCADecoder.MCADecoderGUI.

Decoder types (product-specific):
  CHA/CCF — registers: MC_STATUS, MC_ADDR, MC_MISC, MC_MISC3
  LLC      — registers: MC_STATUS, MC_ADDR, MC_MISC
  CORE     — registers: MC_STATUS, MC_ADDR, MC_MISC  (subtypes: ML2/DCU/IFU/DTLB/L2)
  MEMORY   — registers: MC_STATUS, MC_ADDR, MC_MISC  (subtypes: B2CMI/MSE/MCCHAN)
  IO       — registers: MC_STATUS, MC_ADDR, MC_MISC  (subtypes: UBOX/UPI/ULA)
  FIRST ERROR — registers: MCERRLOGGINGREG, IERRLOGGINGREG

Note: DMR uses a separate decoder (decoder_dmr) for CCF/CORE.
"""
import logging
import sys
import os
import datetime
import pandas as pd
import dash
from dash import html, dcc, Input, Output, State, callback, no_update, ctx
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

dash.register_page(
    __name__,
    path='/thr-tools/mca-decoder',
    name='MCA Decoder',
    title='MCA Single Decoder'
)

ACCENT = "#e879f9"

# Decoder type definitions — must match original MCADecoder.py exactly
_DECODER_TYPES = {
    "CHA/CCF": {
        "registers": ["MC_STATUS", "MC_ADDR", "MC_MISC", "MC_MISC3"],
        "decode_method": "cha",
        "subtypes": [],
        "tooltip": "Cache Home Agent (GNR/CWF) or CCF (DMR)"
    },
    "LLC": {
        "registers": ["MC_STATUS", "MC_ADDR", "MC_MISC"],
        "decode_method": "llc",
        "subtypes": [],
        "tooltip": "Last Level Cache (empty for DMR, LLC is in CCF)"
    },
    "CORE": {
        "registers": ["MC_STATUS", "MC_ADDR", "MC_MISC"],
        "decode_method": "core",
        "subtypes": ["ML2", "DCU", "IFU", "DTLB", "L2"],
        "tooltip": "Core MCA — ML2/DCU/IFU/DTLB/L2 banks"
    },
    "MEMORY": {
        "registers": ["MC_STATUS", "MC_ADDR", "MC_MISC"],
        "decode_method": "mem",
        "subtypes": ["B2CMI", "MSE", "MCCHAN"],
        "tooltip": "Memory Controller — B2CMI/MSE/MCCHAN"
    },
    "IO": {
        "registers": ["MC_STATUS", "MC_ADDR", "MC_MISC"],
        "decode_method": "io",
        "subtypes": ["UBOX", "UPI", "ULA"],
        "tooltip": "IO Subsystem — UBOX/UPI/ULA"
    },
    "FIRST ERROR": {
        "registers": ["MCERRLOGGINGREG", "IERRLOGGINGREG"],
        "decode_method": "first_error",
        "subtypes": [],
        "tooltip": "UBOX First/Second Error Logging registers"
    },
}

_PRODUCTS = ["GNR", "CWF", "DMR"]

_INPUT_STYLE = {
    "backgroundColor": "#1a1d26", "color": "#e0e0e0",
    "border": "1px solid rgba(255,255,255,0.1)", "fontSize": "0.9rem",
    "fontFamily": "monospace"
}
_LABEL_STYLE = {"color": "#a0a0a0", "fontSize": "0.8rem"}


def _register_inputs(decoder_type: str):
    """Build register input rows for a given decoder type."""
    regs = _DECODER_TYPES.get(decoder_type, {}).get("registers", [])
    rows = []
    for reg in regs:
        fid = f"mcd-reg-{reg.lower()}"
        rows.append(html.Div([
            html.Label(reg, style=_LABEL_STYLE),
            dbc.Input(
                id={"type": "mcd-register", "index": reg},
                placeholder=f"e.g. 0xFE000000000C1136",
                type="text",
                className="mb-2",
                style=_INPUT_STYLE
            ),
        ]))
    return rows


layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="mcd-toast"),
    dcc.Download(id="mcd-download"),
    dcc.Store(id="mcd-result-store", data=""),

    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-cpu me-2", style={"color": ACCENT}),
            html.Span("MCA Single Decoder",
                      style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P("Decode individual MCA register values. Product-specific decoder (DMR uses separate decoder_dmr).",
               style={"color": "#a0a0a0", "fontSize": "0.9rem"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        # ── Left: configuration + register inputs ──
        dbc.Col(md=4, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Decoder Configuration", className="mb-3", style={"color": ACCENT}),

                html.Label("Product", style=_LABEL_STYLE),
                dbc.Select(
                    id="mcd-product",
                    options=[{"label": p, "value": p} for p in _PRODUCTS],
                    value="GNR",
                    className="mb-3",
                    style={**_INPUT_STYLE, "fontFamily": "inherit"}
                ),

                html.Label("Decoder Type", style=_LABEL_STYLE),
                dbc.Select(
                    id="mcd-decoder-type",
                    options=[{"label": f"{k} — {v['tooltip']}", "value": k}
                             for k, v in _DECODER_TYPES.items()],
                    value="CHA/CCF",
                    className="mb-2",
                    style={**_INPUT_STYLE, "fontFamily": "inherit"}
                ),

                # Subtype (shown for CORE / MEMORY / IO)
                html.Div(id="mcd-subtype-row", children=[
                    html.Label("Bank / Subtype", style=_LABEL_STYLE),
                    dbc.Select(
                        id="mcd-subtype",
                        options=[{"label": s, "value": s} for s in ["ML2", "DCU", "IFU", "DTLB", "L2"]],
                        value="ML2",
                        className="mb-2",
                        style={**_INPUT_STYLE, "fontFamily": "inherit"}
                    ),
                ], style={"display": "none"}),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                html.H6("Register Values", style={"color": "#c0c0c0", "fontSize": "0.88rem"}, className="mb-2"),
                html.Div(id="mcd-register-inputs", children=_register_inputs("CHA/CCF")),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                dbc.Row([
                    dbc.Col(dbc.Button(
                        [html.I(className="bi bi-play-fill me-1"), "Decode"],
                        id="mcd-decode-btn", outline=True, className="w-100",
                        style={"borderColor": ACCENT, "color": ACCENT}
                    ), width=6),
                    dbc.Col(dbc.Button(
                        [html.I(className="bi bi-x-circle me-1"), "Clear"],
                        id="mcd-clear-btn", color="secondary", outline=True, className="w-100",
                    ), width=3),
                    dbc.Col(dbc.Button(
                        [html.I(className="bi bi-download me-1"), "Export"],
                        id="mcd-export-btn", outline=True, className="w-100",
                        style={"borderColor": "#a0a0a0", "color": "#a0a0a0"}, disabled=True
                    ), width=3),
                ], className="g-2"),
            ]), className="card-premium border-0"),
        ]),

        # ── Right: results ──
        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Decode Output", style={"color": ACCENT}, className="mb-3"),
                dbc.Textarea(
                    id="mcd-results",
                    value="",
                    readOnly=True,
                    style={
                        "backgroundColor": "#0d0f17",
                        "color": "#e0f0e0",
                        "fontFamily": "Courier New, monospace",
                        "fontSize": "0.82rem",
                        "border": "1px solid rgba(255,255,255,0.08)",
                        "height": "500px",
                        "resize": "vertical"
                    }
                ),
            ]), className="card-premium border-0"),
        ]),
    ]),
])


# ── Callbacks ──────────────────────────────────────────────────────────────────

@callback(
    Output("mcd-register-inputs", "children"),
    Output("mcd-subtype-row", "style"),
    Output("mcd-subtype", "options"),
    Output("mcd-subtype", "value"),
    Input("mcd-decoder-type", "value"),
)
def update_register_fields(decoder_type):
    cfg = _DECODER_TYPES.get(decoder_type or "CHA/CCF", _DECODER_TYPES["CHA/CCF"])
    subtypes = cfg.get("subtypes", [])
    subtype_style = {} if subtypes else {"display": "none"}
    subtype_opts = [{"label": s, "value": s} for s in subtypes]
    subtype_val = subtypes[0] if subtypes else ""
    return _register_inputs(decoder_type), subtype_style, subtype_opts, subtype_val


@callback(
    Output("mcd-results", "value"),
    Output("mcd-result-store", "data"),
    Output("mcd-export-btn", "disabled"),
    Output("mcd-toast", "children"),
    Input("mcd-decode-btn", "n_clicks"),
    Input("mcd-clear-btn", "n_clicks"),
    State("mcd-product", "value"),
    State("mcd-decoder-type", "value"),
    State("mcd-subtype", "value"),
    State({"type": "mcd-register", "index": dash.ALL}, "value"),
    State({"type": "mcd-register", "index": dash.ALL}, "id"),
    prevent_initial_call=True
)
def run_decode(decode_c, clear_c, product, decoder_type, subtype,
               reg_values, reg_ids):
    trigger = ctx.triggered_id

    if trigger == "mcd-clear-btn":
        return "", "", True, no_update

    if trigger != "mcd-decode-btn":
        return no_update, no_update, no_update, no_update

    # Collect register values
    registers = {}
    for rid, rval in zip(reg_ids, reg_values):
        if rval and str(rval).strip():
            registers[rid["index"]] = str(rval).strip()

    cfg = _DECODER_TYPES.get(decoder_type or "CHA/CCF", _DECODER_TYPES["CHA/CCF"])
    method = cfg["decode_method"]

    # Validate required fields
    if method == "first_error":
        if not registers.get("MCERRLOGGINGREG") and not registers.get("IERRLOGGINGREG"):
            return no_update, no_update, True, _toast(
                "Enter at least one of MCERRLOGGINGREG or IERRLOGGINGREG.", "warning")
    else:
        if not registers.get("MC_STATUS"):
            return no_update, no_update, True, _toast("MC_STATUS is required.", "warning")

    try:
        # Validate hex format
        for name, val in list(registers.items()):
            registers[name] = _parse_hex(val)

        output = _do_decode(method, registers, product or "GNR", subtype or "")
        return output, output, False, _toast("Decode complete.", "success", 2000)

    except Exception as e:
        logger.exception("MCA decode error")
        err = f"ERROR: {e}\n"
        return err, err, False, _toast(f"Decode error: {e}", "danger")


def _parse_hex(val: str) -> str:
    """Normalize hex value to 0x... format."""
    val = val.strip().replace(" ", "")
    if not val.startswith("0x") and not val.startswith("0X"):
        val = "0x" + val
    int(val, 16)  # validate — raises ValueError if invalid
    return val.upper().replace("0X", "0x")


def _do_decode(method: str, registers: dict, product: str, subtype: str) -> str:
    """Perform actual decoding using THRTools decoder backend."""
    sys.path.insert(0, os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..'))
    )
    from THRTools.Decoder.decoder import decoder, extract_bits

    # Create a minimal dummy DataFrame to instantiate the decoder
    dummy_df = pd.DataFrame({
        'VisualId': [1], 'TestName': ['dummy'], 'TestValue': ['0x0'],
        'LotsSeqKey': [1], 'UnitTestingSeqKey': [1], 'Operation': ['RD']
    })
    dec = decoder(data=dummy_df, product=product)

    lines = []

    def sep(): lines.append("=" * 72)
    def sub(): lines.append("-" * 40)

    if method == "cha":
        sep()
        lines.append(f"CHA/CCF MCA DECODE — {product}")
        sep()
        lines.append("")
        mc_status = registers.get("MC_STATUS", "")
        mc_addr   = registers.get("MC_ADDR", "")
        mc_misc   = registers.get("MC_MISC", "")
        mc_misc3  = registers.get("MC_MISC3", "")

        lines.append("RAW REGISTER VALUES:")
        lines.append(f"  MC_STATUS:  {mc_status}")
        if mc_addr:  lines.append(f"  MC_ADDR:    {mc_addr}")
        if mc_misc:  lines.append(f"  MC_MISC:    {mc_misc}")
        if mc_misc3: lines.append(f"  MC_MISC3:   {mc_misc3}")
        lines.append("")

        lines.append("MC_STATUS DECODE:")
        try:
            lines.append(f"  MSCOD (Error Type):  {dec.cha_decoder(mc_status, 'MC DECODE')}")
            lines.append(f"  VAL  (bit 63):       {extract_bits(mc_status, 63, 63)}")
            lines.append(f"  UC   (bit 61):       {extract_bits(mc_status, 61, 61)}")
            lines.append(f"  PCC  (bit 57):       {extract_bits(mc_status, 57, 57)}")
            lines.append(f"  ADDRV(bit 58):       {extract_bits(mc_status, 58, 58)}")
            lines.append(f"  MISCV(bit 59):       {extract_bits(mc_status, 59, 59)}")
        except Exception as e:
            lines.append(f"  Error: {e}")
        lines.append("")

        if mc_misc:
            lines.append("MC_MISC DECODE:")
            try:
                lines.append(f"  Original Request:  {dec.cha_decoder(mc_misc, 'Orig Req')}")
                lines.append(f"  Opcode:            {dec.cha_decoder(mc_misc, 'Opcode')}")
                lines.append(f"  Cache State:       {dec.cha_decoder(mc_misc, 'cachestate')}")
                lines.append(f"  TOR ID:            {dec.cha_decoder(mc_misc, 'TorID')}")
                lines.append(f"  TOR FSM:           {dec.cha_decoder(mc_misc, 'TorFSM')}")
            except Exception as e:
                lines.append(f"  Error: {e}")
            lines.append("")

        if mc_misc3:
            lines.append("MC_MISC3 DECODE:")
            try:
                lines.append(f"  Source ID:         {dec.cha_decoder(mc_misc3, 'SrcID')}")
                lines.append(f"  ISMQ FSM:          {dec.cha_decoder(mc_misc3, 'ISMQ')}")
                lines.append(f"  SAD Attribute:     {dec.cha_decoder(mc_misc3, 'Attribute')}")
                lines.append(f"  SAD Result:        {dec.cha_decoder(mc_misc3, 'Result')}")
                lines.append(f"  Local Port:        {dec.cha_decoder(mc_misc3, 'Local Port')}")
            except Exception as e:
                lines.append(f"  Error: {e}")
            lines.append("")

    elif method == "llc":
        if product == "DMR":
            lines.append("Note: DMR uses CCF decoder (LLC is in CCF). Use CHA/CCF decoder.")
            return "\n".join(lines)
        sep()
        lines.append(f"LLC MCA DECODE — {product}")
        sep()
        lines.append("")
        mc_status = registers.get("MC_STATUS", "")
        mc_addr   = registers.get("MC_ADDR", "")
        mc_misc   = registers.get("MC_MISC", "")

        lines.append("RAW REGISTER VALUES:")
        lines.append(f"  MC_STATUS:  {mc_status}")
        if mc_addr: lines.append(f"  MC_ADDR:    {mc_addr}")
        if mc_misc: lines.append(f"  MC_MISC:    {mc_misc}")
        lines.append("")

        lines.append("MC_STATUS DECODE:")
        try:
            lines.append(f"  MSCOD (Error Type):  {dec.llc_decoder(mc_status, 'MC DECODE')}")
            lines.append(f"  MISCV:               {dec.llc_decoder(mc_status, 'MiscV')}")
            lines.append(f"  VAL (bit 63):        {extract_bits(mc_status, 63, 63)}")
            lines.append(f"  UC  (bit 61):        {extract_bits(mc_status, 61, 61)}")
            lines.append(f"  PCC (bit 57):        {extract_bits(mc_status, 57, 57)}")
        except Exception as e:
            lines.append(f"  Error: {e}")
        lines.append("")

        if mc_misc:
            lines.append("MC_MISC DECODE:")
            try:
                lines.append(f"  RSF:       {dec.llc_decoder(mc_misc, 'RSF')}")
                lines.append(f"  LSF:       {dec.llc_decoder(mc_misc, 'LSF')}")
                lines.append(f"  LLC_MISC:  {dec.llc_decoder(mc_misc, 'LLC_misc')}")
            except Exception as e:
                lines.append(f"  Error: {e}")
            lines.append("")

    elif method == "core":
        sep()
        lines.append(f"CORE MCA DECODE — {product} — {subtype}")
        sep()
        lines.append("")
        mc_status = registers.get("MC_STATUS", "")
        mc_addr   = registers.get("MC_ADDR", "")
        mc_misc   = registers.get("MC_MISC", "")

        lines.append("RAW REGISTER VALUES:")
        lines.append(f"  MC_STATUS:  {mc_status}")
        if mc_addr: lines.append(f"  MC_ADDR:    {mc_addr}")
        if mc_misc: lines.append(f"  MC_MISC:    {mc_misc}")
        lines.append("")

        lines.append(f"MC_STATUS DECODE ({subtype}):")
        try:
            mcacod, mscod = dec.core_decoder(value=mc_status, type=subtype)
            lines.append(f"  Bank Type:              {subtype}")
            lines.append(f"  MCACOD (Error Decode):  {mcacod}")
            lines.append(f"  MSCOD:                  {mscod}")
            lines.append(f"  VAL (bit 63):           {extract_bits(mc_status, 63, 63)}")
            lines.append(f"  UC  (bit 61):           {extract_bits(mc_status, 61, 61)}")
            lines.append(f"  PCC (bit 57):           {extract_bits(mc_status, 57, 57)}")
        except Exception as e:
            lines.append(f"  Error: {e}")
            # Fallback generic decode
            try:
                mscod = extract_bits(mc_status, 16, 31)
                mcacod = extract_bits(mc_status, 0, 15)
                lines.append(f"  MSCOD  (bits 16-31): 0x{mscod:04X}")
                lines.append(f"  MCACOD (bits  0-15): 0x{mcacod:04X}")
            except:
                pass
        lines.append("")

    elif method == "mem":
        sep()
        lines.append(f"MEMORY MCA DECODE — {product} — {subtype}")
        sep()
        lines.append("")
        mc_status = registers.get("MC_STATUS", "")
        mc_addr   = registers.get("MC_ADDR", "")
        mc_misc   = registers.get("MC_MISC", "")

        lines.append("RAW REGISTER VALUES:")
        lines.append(f"  MC_STATUS:  {mc_status}")
        if mc_addr: lines.append(f"  MC_ADDR:    {mc_addr}")
        if mc_misc: lines.append(f"  MC_MISC:    {mc_misc}")
        lines.append("")

        lines.append(f"MC_STATUS DECODE ({subtype}):")
        try:
            decoded = dec.mem_decoder(value=mc_status, instance_type=subtype)
            lines.append(f"  Decoded Value:       {decoded}")
            lines.append(f"  VAL (bit 63):        {extract_bits(mc_status, 63, 63)}")
            lines.append(f"  UC  (bit 61):        {extract_bits(mc_status, 61, 61)}")
            lines.append(f"  PCC (bit 57):        {extract_bits(mc_status, 57, 57)}")
        except Exception as e:
            lines.append(f"  Error: {e}")
            try:
                lines.append(f"  MSCOD  (bits 16-31): 0x{extract_bits(mc_status, 16, 31):04X}")
                lines.append(f"  MCACOD (bits  0-15): 0x{extract_bits(mc_status, 0, 15):04X}")
            except:
                pass
        lines.append("")

    elif method == "io":
        sep()
        lines.append(f"IO MCA DECODE — {product} — {subtype}")
        sep()
        lines.append("")
        mc_status = registers.get("MC_STATUS", "")
        mc_addr   = registers.get("MC_ADDR", "")
        mc_misc   = registers.get("MC_MISC", "")

        lines.append("RAW REGISTER VALUES:")
        lines.append(f"  MC_STATUS:  {mc_status}")
        if mc_addr: lines.append(f"  MC_ADDR:    {mc_addr}")
        if mc_misc: lines.append(f"  MC_MISC:    {mc_misc}")
        lines.append("")

        lines.append(f"MC_STATUS DECODE ({subtype}):")
        try:
            mcacod_decoded, mscod_decoded = dec.io_decoder(value=mc_status, instance_type=subtype)
            lines.append(f"  MCACOD:  {mcacod_decoded}")
            lines.append(f"  MSCOD:   {mscod_decoded}")
            lines.append(f"  VAL (bit 63):  {extract_bits(mc_status, 63, 63)}")
            lines.append(f"  UC  (bit 61):  {extract_bits(mc_status, 61, 61)}")
            lines.append(f"  PCC (bit 57):  {extract_bits(mc_status, 57, 57)}")
        except Exception as e:
            lines.append(f"  Error: {e}")
        lines.append("")

    elif method == "first_error":
        sep()
        lines.append(f"FIRST ERROR DECODE — {product}")
        sep()
        lines.append("")
        mcerr_reg = registers.get("MCERRLOGGINGREG", "")
        ierr_reg  = registers.get("IERRLOGGINGREG", "")

        lines.append("RAW REGISTER VALUES:")
        if mcerr_reg: lines.append(f"  MCERRLOGGINGREG:  {mcerr_reg}")
        if ierr_reg:  lines.append(f"  IERRLOGGINGREG:   {ierr_reg}")
        lines.append("")

        portid_fields = [
            'FirstError - DIEID', 'FirstError - PortID', 'FirstError - Location', 'FirstError - FromCore',
            'SecondError - DIEID', 'SecondError - PortID', 'SecondError - Location', 'SecondError - FromCore'
        ]

        if mcerr_reg:
            lines.append("MCERRLOGGINGREG DECODE:")
            try:
                pv = dec.portids_decoder(value=mcerr_reg, portid_data=portid_fields, event='mcerr')
                lines.append(f"  First Error:")
                lines.append(f"    DIE ID:    {pv.get('FirstError - DIEID', 'N/A')}")
                lines.append(f"    Port ID:   {pv.get('FirstError - PortID', 'N/A')}")
                lines.append(f"    Location:  {pv.get('FirstError - Location', 'N/A')}")
                lines.append(f"    From Core: {pv.get('FirstError - FromCore', 'N/A')}")
                lines.append(f"  Second Error:")
                lines.append(f"    DIE ID:    {pv.get('SecondError - DIEID', 'N/A')}")
                lines.append(f"    Port ID:   {pv.get('SecondError - PortID', 'N/A')}")
                lines.append(f"    Location:  {pv.get('SecondError - Location', 'N/A')}")
                lines.append(f"    From Core: {pv.get('SecondError - FromCore', 'N/A')}")
            except Exception as e:
                lines.append(f"  Error decoding MCERRLOGGINGREG: {e}")
            lines.append("")

        if ierr_reg:
            lines.append("IERRLOGGINGREG DECODE:")
            try:
                pv = dec.portids_decoder(value=ierr_reg, portid_data=portid_fields, event='ierr')
                lines.append(f"  First Error:")
                lines.append(f"    DIE ID:    {pv.get('FirstError - DIEID', 'N/A')}")
                lines.append(f"    Port ID:   {pv.get('FirstError - PortID', 'N/A')}")
                lines.append(f"    Location:  {pv.get('FirstError - Location', 'N/A')}")
                lines.append(f"    From Core: {pv.get('FirstError - FromCore', 'N/A')}")
                lines.append(f"  Second Error:")
                lines.append(f"    DIE ID:    {pv.get('SecondError - DIEID', 'N/A')}")
                lines.append(f"    Port ID:   {pv.get('SecondError - PortID', 'N/A')}")
                lines.append(f"    Location:  {pv.get('SecondError - Location', 'N/A')}")
                lines.append(f"    From Core: {pv.get('SecondError - FromCore', 'N/A')}")
            except Exception as e:
                lines.append(f"  Error decoding IERRLOGGINGREG: {e}")
            lines.append("")

    sep()
    lines.append("Decode Complete")
    return "\n".join(lines)


@callback(
    Output("mcd-download", "data"),
    Output("mcd-toast", "children", allow_duplicate=True),
    Input("mcd-export-btn", "n_clicks"),
    State("mcd-result-store", "data"),
    State("mcd-product", "value"),
    State("mcd-decoder-type", "value"),
    prevent_initial_call=True
)
def export_results(n_clicks, result_text, product, decoder_type):
    if not result_text:
        return no_update, _toast("No results to export.", "warning")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"MCA_Decode_{product}_{(decoder_type or 'unknown').replace('/','-')}_{ts}.txt"
    return dcc.send_string(result_text, fname), _toast(f"Exported {fname}.", "success", 2500)


def _toast(msg, icon, duration=4000):
    return dbc.Toast(
        msg, icon=icon, duration=duration, is_open=True,
        style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
        className="toast-custom"
    )
