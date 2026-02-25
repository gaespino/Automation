"""
Automation Flow Designer
=========================
Ordered step-list editor for automation flow JSON files.
Canvas drag-and-drop deferred — see CAAS_TODO.md.
Calls THRTools/gui/AutomationDesigner.py backend (non-GUI methods only).
"""
import logging
import json
import base64
import uuid
import dash
from dash import html, dcc, Input, Output, State, callback, no_update, ctx
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

dash.register_page(
    __name__,
    path='/thr-tools/automation-designer',
    name='Automation Designer',
    title='Automation Flow Designer'
)

ACCENT = "#00c9a7"

_STEP_TYPES = [
    "set_vid", "set_ww", "set_bucket", "run_script",
    "copy_files", "parse_logs", "generate_report",
    "send_notification", "conditional_branch", "custom"
]

# ── layout ────────────────────────────────────────────────────────────────────

layout = dbc.Container(fluid=True, className="pb-5", children=[
    html.Div(id="ad-toast"),
    dcc.Download(id="ad-download"),
    dcc.Store(id="ad-steps-store", data=[]),

    dbc.Row(dbc.Col(html.Div([
        html.H4([
            html.I(className="bi bi-diagram-3 me-2", style={"color": ACCENT}),
            html.Span("Automation Flow Designer",
                      style={"color": ACCENT, "fontFamily": "Inter, sans-serif"})
        ], className="mb-1"),
        html.P("Build automation flow configurations as ordered step lists. Import/export as JSON.",
               style={"color": "#a0a0a0", "fontSize": "0.9rem"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"})
    ], className="pt-3 pb-1"), width=12)),

    dbc.Row([
        # ── Left: step editor ─────────────────────────────────────────────────
        dbc.Col(md=4, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Add Step", className="mb-3", style={"color": ACCENT}),

                html.Label("Step Type", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Select(
                    id="ad-step-type",
                    options=[{"label": t.replace("_", " ").title(), "value": t} for t in _STEP_TYPES],
                    value="run_script",
                    className="mb-3",
                    style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                           "border": "1px solid rgba(255,255,255,0.1)"}
                ),

                html.Label("Step Label", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Input(id="ad-step-label", placeholder="Descriptive name",
                          className="mb-3",
                          style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                                 "border": "1px solid rgba(255,255,255,0.1)"}),

                html.Label("Parameters (JSON)", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dbc.Textarea(
                    id="ad-step-params",
                    placeholder='{"key": "value"}',
                    rows=4,
                    className="mb-3",
                    style={"backgroundColor": "#1a1d26", "color": "#e0e0e0",
                           "border": "1px solid rgba(255,255,255,0.1)",
                           "fontFamily": "monospace", "fontSize": "0.82rem"}
                ),

                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-2"), "Add Step"],
                    id="ad-add-btn", outline=True, className="w-100 mb-2",
                    style={"borderColor": ACCENT, "color": ACCENT}
                ),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                dbc.Row([
                    dbc.Col(dbc.Button(
                        [html.I(className="bi bi-download me-2"), "Export"],
                        id="ad-export-btn", outline=True, className="w-100",
                        style={"borderColor": ACCENT, "color": ACCENT}
                    ), width=6),
                    dbc.Col(dbc.Button(
                        [html.I(className="bi bi-trash me-2"), "Clear"],
                        id="ad-clear-btn", color="danger", outline=True, className="w-100",
                    ), width=6),
                ], className="mb-2"),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),

                html.Label("Import Flow JSON", style={"color": "#a0a0a0", "fontSize": "0.83rem"}),
                dcc.Upload(
                    id="ad-import",
                    children=html.Div([
                        html.A("Browse", style={"color": ACCENT}), " or drop JSON"
                    ]),
                    multiple=False,
                    style={
                        "border": f"1px dashed {ACCENT}", "borderRadius": "6px",
                        "padding": "8px", "textAlign": "center",
                        "color": "#a0a0a0", "fontSize": "0.82rem",
                        "backgroundColor": "rgba(0,201,167,0.03)", "cursor": "pointer"
                    }
                ),

                dbc.Alert([
                    html.I(className="bi bi-info-circle me-2"),
                    "Visual canvas drag-and-drop is planned. See ",
                    html.Code("CAAS_TODO.md"), "."
                ], color="secondary", className="card-premium border-0 text-white mt-3",
                   style={"fontSize": "0.78rem"}),

            ]), className="card-premium border-0"),
        ]),

        # ── Right: step list ──────────────────────────────────────────────────
        dbc.Col(md=8, children=[
            dbc.Card(dbc.CardBody([
                html.H6("Flow Steps", style={"color": ACCENT}, className="mb-3"),
                html.Div(id="ad-step-list", children=[
                    dbc.Alert("No steps yet. Add steps using the editor.",
                              color="secondary", className="card-premium border-0 text-white")
                ])
            ]), className="card-premium border-0"),
        ]),
    ]),
])


# ── callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output("ad-steps-store", "data"),
    Output("ad-toast", "children"),
    Input("ad-add-btn", "n_clicks"),
    Input("ad-clear-btn", "n_clicks"),
    Input("ad-import", "contents"),
    State("ad-steps-store", "data"),
    State("ad-step-type", "value"),
    State("ad-step-label", "value"),
    State("ad-step-params", "value"),
    prevent_initial_call=True
)
def manage_steps(add_clicks, clear_clicks, import_content,
                 current, step_type, step_label, step_params):
    trigger = ctx.triggered_id

    if trigger == "ad-clear-btn":
        return [], dbc.Toast("Steps cleared.", icon="info", duration=2500, is_open=True,
                             style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                             className="toast-custom")

    if trigger == "ad-import" and import_content:
        try:
            _, data = import_content.split(',')
            flow = json.loads(base64.b64decode(data).decode('utf-8'))
            steps = flow.get("steps", flow) if isinstance(flow, dict) else flow
            if not isinstance(steps, list):
                steps = [steps]
            return steps, dbc.Toast(f"Imported {len(steps)} step(s).", icon="success",
                                    duration=3000, is_open=True,
                                    style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                                    className="toast-custom")
        except Exception as e:
            return no_update, dbc.Toast(f"Import error: {e}", icon="danger", duration=4000,
                                        is_open=True,
                                        style={"position": "fixed", "top": 20, "right": 20,
                                               "zIndex": 9999}, className="toast-custom")

    # Add step
    params = {}
    if step_params and step_params.strip():
        try:
            params = json.loads(step_params)
        except json.JSONDecodeError:
            return no_update, dbc.Toast("Invalid JSON in parameters.", icon="warning",
                                        duration=3000, is_open=True,
                                        style={"position": "fixed", "top": 20, "right": 20,
                                               "zIndex": 9999}, className="toast-custom")

    step = {
        "id": str(uuid.uuid4())[:8],
        "type": step_type or "custom",
        "label": step_label or step_type or "step",
        "params": params,
    }
    updated = list(current or []) + [step]
    return updated, dbc.Toast(f"Step added. Total: {len(updated)}.", icon="success",
                              duration=2000, is_open=True,
                              style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                              className="toast-custom")


@callback(
    Output("ad-steps-store", "data", allow_duplicate=True),
    Output("ad-toast", "children", allow_duplicate=True),
    Input({"type": "ad-move-up", "index": dash.ALL}, "n_clicks"),
    Input({"type": "ad-move-down", "index": dash.ALL}, "n_clicks"),
    Input({"type": "ad-delete", "index": dash.ALL}, "n_clicks"),
    State("ad-steps-store", "data"),
    prevent_initial_call=True
)
def reorder_steps(up_clicks, down_clicks, del_clicks, steps):
    if not steps:
        return no_update, no_update

    trigger = ctx.triggered_id
    if not trigger or not isinstance(trigger, dict):
        return no_update, no_update

    op = trigger["type"]
    idx = trigger["index"]
    steps = list(steps)

    if op == "ad-delete":
        if 0 <= idx < len(steps):
            steps.pop(idx)
        return steps, dbc.Toast("Step removed.", icon="info", duration=2000, is_open=True,
                                style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
                                className="toast-custom")

    if op == "ad-move-up" and idx > 0:
        steps[idx - 1], steps[idx] = steps[idx], steps[idx - 1]
    elif op == "ad-move-down" and idx < len(steps) - 1:
        steps[idx + 1], steps[idx] = steps[idx], steps[idx + 1]

    return steps, no_update


@callback(
    Output("ad-step-list", "children"),
    Input("ad-steps-store", "data"),
)
def render_steps(steps):
    if not steps:
        return dbc.Alert("No steps yet. Add steps using the editor.",
                         color="secondary", className="card-premium border-0 text-white")

    items = []
    for i, step in enumerate(steps):
        items.append(
            dbc.Card(dbc.CardBody([
                dbc.Row([
                    dbc.Col(html.Div([
                        html.Span(f"{i + 1}. ", style={"color": "#666", "fontSize": "0.85rem"}),
                        html.Span(step.get("label", "?"),
                                  style={"color": ACCENT, "fontWeight": "600", "fontSize": "0.9rem"}),
                        html.Span(f"  [{step.get('type', '?')}]",
                                  style={"color": "#666", "fontSize": "0.78rem"}),
                    ]), width=7),
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button(html.I(className="bi bi-arrow-up"),
                                       id={"type": "ad-move-up", "index": i},
                                       size="sm", color="secondary", outline=True,
                                       disabled=(i == 0)),
                            dbc.Button(html.I(className="bi bi-arrow-down"),
                                       id={"type": "ad-move-down", "index": i},
                                       size="sm", color="secondary", outline=True,
                                       disabled=(i == len(steps) - 1)),
                            dbc.Button(html.I(className="bi bi-trash"),
                                       id={"type": "ad-delete", "index": i},
                                       size="sm", color="danger", outline=True),
                        ], size="sm"),
                    ], width=5, className="text-end"),
                ], align="center"),
                html.Div(
                    json.dumps(step.get("params", {}), indent=2) if step.get("params") else "",
                    style={"color": "#a0a0a0", "fontSize": "0.78rem", "fontFamily": "monospace",
                           "marginTop": "4px", "whiteSpace": "pre-wrap"}
                )
            ]), className="card-premium border-0 mb-2",
                style={"borderLeft": f"3px solid {ACCENT}"})
        )

    return items


@callback(
    Output("ad-download", "data"),
    Input("ad-export-btn", "n_clicks"),
    State("ad-steps-store", "data"),
    prevent_initial_call=True
)
def export_flow(n_clicks, steps):
    if not steps:
        return no_update
    flow = {"version": "1.0", "steps": steps}
    return dcc.send_string(json.dumps(flow, indent=2), "automation_flow.json")
