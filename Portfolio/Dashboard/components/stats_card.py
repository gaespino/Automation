from dash import html
import dash_bootstrap_components as dbc

def create_stats_card():
    return html.Div(id='stats-container', className="fade-in")

def generate_stats_view(unit_data):
    if not unit_data: return html.Div()

    config = unit_data.get("Config", {})
    exps = unit_data.get("experiments", [])
    
    total = len(exps)
    passed = sum(1 for e in exps if e.get("Estado") == "Pass")
    failed = sum(1 for e in exps if e.get("Estado") in ["Fail", "Fail - Setup"])
    pending = sum(1 for e in exps if e.get("Estado") == "Pending")
    
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    # Extra Details
    mrs = config.get("MRS", "N/A")
    qdf = config.get("QDF", "N/A")
    mrs_days = config.get("MRS_Days_Remaining", "N/A")
    phy_core = str(config.get("Victim_Phy_Core", ["N/A"])[0]) if isinstance(config.get("Victim_Phy_Core"), list) else str(config.get("Victim_Phy_Core", "N/A"))
    
    # Extended Core Info
    os_core = str(config.get("Victim_OS_Core", "N/A"))
    
    log_core_val = config.get("Victim_Log_Core", "N/A")
    log_core = str(log_core_val[0]) if isinstance(log_core_val, list) and log_core_val else str(log_core_val)
    
    instr = config.get("Failing Instructions", [])
    instr_text = "\n".join(instr) if isinstance(instr, list) else str(instr)

    return dbc.Card(className="card-premium mb-4", children=[
        dbc.CardBody([
            dbc.Row([
                # Visual ID Section
                dbc.Col([
                    html.Div([
                        html.Div("Visual ID", className="stat-label"),
                        html.Div(config.get("Visual ID", unit_data.get("_context", {}).get("unit", "N/A")), className="stat-value text-white"),
                        html.Div([
                            html.I(className="bi bi-tag-fill me-1 text-info"),
                            dbc.Input(id="edit-mrs-value", value=mrs, size="sm", className="bg-transparent text-light border-0 p-0 d-inline-block", style={"width": "80px", "fontSize": "inherit"}),
                            dbc.Button(html.I(className="bi bi-save"), id="btn-save-mrs", size="sm", color="link", className="text-info p-0 ms-1")
                        ], className="small text-light mt-2 d-flex align-items-center")
                    ], className="d-flex flex-column h-100 justify-content-center border-end border-secondary border-opacity-25 pe-3")
                ], width=3),

                # Pass Rate Section
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.Div("Pass Rate", className="stat-label"),
                            html.Div(f"{pass_rate:.1f}%", className="stat-value"),
                        ]),
                        html.Div(html.I(className="bi bi-pie-chart-fill"), className="stat-icon-wrapper")
                    ], className="d-flex justify-content-between align-items-center px-3 border-end border-secondary border-opacity-25")
                ], width=3),

                # Total Tests Section
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.Div("Total Tests", className="stat-label"),
                            html.Div(str(total), className="stat-value", style={"color": "#b0b0b0"}),
                        ]),
                        html.Div(html.I(className="bi bi-list-check"), className="stat-icon-wrapper")
                    ], className="d-flex justify-content-between align-items-center px-3")
                ], width=2),

                # Progress Bar Section
                dbc.Col([
                    html.Div("Progress Overview", className="stat-label mb-2"),
                    dbc.Progress([
                        dbc.Progress(value=passed, max=total, color="success", bar=True, className="opacity-75"),
                        dbc.Progress(value=failed, max=total, color="danger", bar=True, className="opacity-75"),
                        dbc.Progress(value=pending, max=total, color="warning", bar=True, className="opacity-75")
                    ], style={"height": "12px", "backgroundColor": "rgba(255,255,255,0.05)"}),
                    html.Div([
                        html.Span([html.I(className="bi bi-circle-fill text-success me-1"), f"{passed} Pass"], className="me-3"),
                        html.Span([html.I(className="bi bi-circle-fill text-danger me-1"), f"{failed} Fail"], className="me-3"),
                        html.Span([html.I(className="bi bi-circle-fill text-warning me-1"), f"{pending} Pend"])
                    ], className="d-flex small text-light mt-2")
                ], width=4)
            ]),
            
            html.Hr(className="border-secondary opacity-10 my-3"),
            
            # Collapsible Details
            dbc.Accordion([
                dbc.AccordionItem([
                    dbc.Row([
                        dbc.Col([
                            html.Div([html.I(className="bi bi-upc-scan me-2 text-info"), "QDF: ", html.Span(qdf, className="text-white fw-bold")], className="mb-2"),
                            html.Div([html.I(className="bi bi-calendar-event me-2 text-warning"), "Days Left: ", html.Span(mrs_days, className="text-white fw-bold")], className="mb-2"),
                            html.Div([html.I(className="bi bi-cpu me-2 text-primary"), "Phy Core: ", html.Span(phy_core, className="text-white fw-bold")], className="mb-2"),
                            html.Div([html.I(className="bi bi-terminal me-2 text-success"), "OS Core: ", html.Span(os_core, className="text-white fw-bold")], className="mb-2"),
                            html.Div([html.I(className="bi bi-card-text me-2 text-info"), "Log Core: ", html.Span(log_core, className="text-white fw-bold")])
                        ], width=4, className="font-monospace small"),
                        
                        dbc.Col([
                            html.Div([html.I(className="bi bi-bug-fill me-2 text-danger"), "Failing Instructions:"], className="mb-1 text-secondary small"),
                            html.Pre(instr_text, className="bg-black p-2 rounded small text-danger border border-secondary border-opacity-25 m-0", style={"maxHeight": "80px", "overflowY": "auto"})
                        ], width=8)
                    ])
                ], title="🔧 Technical Details & Config")
            ], start_collapsed=True, flush=True, className="accordion-custom")
        ])
    ])
