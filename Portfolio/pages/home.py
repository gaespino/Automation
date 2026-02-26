"""
Landing Page — THR Tools Portfolio
====================================
Main entry point. Links to Unit Portfolio and THR Tools.
"""
import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/', name='Home', title='THR Tools Portfolio')

layout = dbc.Container(
    fluid=True,
    className="pb-5",
    style={"backgroundColor": "var(--bg-body, #0a0b10)"},
    children=[
        # Hero Section
        dbc.Row(
            dbc.Col(
                html.Div([
                    html.H1(
                        "THR Tools Portfolio",
                        className="display-5 fw-bold mb-2",
                        style={"color": "#e0e0e0", "fontFamily": "Inter, sans-serif"}
                    ),
                    html.P(
                        "Unified debug & analysis platform for GNR, CWF, and DMR products.",
                        style={"color": "#a0a0a0", "fontSize": "1.1rem", "fontFamily": "Inter, sans-serif"}
                    ),
                    html.Hr(style={"borderColor": "rgba(255,255,255,0.08)", "marginBottom": "2rem"})
                ], className="pt-4 pb-2"),
                width=12
            )
        ),

        # Entry Tiles
        dbc.Row([
            # Unit Portfolio Tile
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-grid-3x3-gap-fill",
                                   style={"fontSize": "2.5rem", "color": "#00d4ff", "marginBottom": "1rem"}),
                            html.H4("Unit Portfolio", className="card-title mb-2",
                                    style={"color": "#e0e0e0", "fontFamily": "Inter, sans-serif"}),
                            html.P(
                                "Track and manage test units. View experiment status, debug data, "
                                "build recipes, and manage configurations for GNR, CWF and DMR units.",
                                style={"color": "#a0a0a0", "fontSize": "0.9rem", "minHeight": "60px"}
                            ),
                            html.Hr(style={"borderColor": "rgba(0,212,255,0.2)"}),
                            dbc.Button(
                                [html.I(className="bi bi-arrow-right-circle me-2"), "Open Portfolio"],
                                href="/dashboard/portfolio",
                                color="primary",
                                outline=True,
                                className="mt-2 btn-primary-custom",
                                style={"borderColor": "#00d4ff", "color": "#00d4ff"}
                            )
                        ], className="text-center py-2")
                    ]),
                    className="card-premium border-0 h-100",
                    style={"borderLeft": "3px solid #00d4ff !important",
                           "borderRadius": "12px"}
                ),
                md=6, className="mb-4"
            ),

            # THR Tools Tile
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-tools",
                                   style={"fontSize": "2.5rem", "color": "#7000ff", "marginBottom": "1rem"}),
                            html.H4("THR Tools", className="card-title mb-2",
                                    style={"color": "#e0e0e0", "fontFamily": "Inter, sans-serif"}),
                            html.P(
                                "Debug and analysis tools: parse logs, decode MCA registers, build "
                                "Framework reports, design automation flows, generate fuse files and more.",
                                style={"color": "#a0a0a0", "fontSize": "0.9rem", "minHeight": "60px"}
                            ),
                            html.Hr(style={"borderColor": "rgba(112,0,255,0.2)"}),
                            dbc.Button(
                                [html.I(className="bi bi-arrow-right-circle me-2"), "Open Tools"],
                                href="/thr/",
                                color="primary",
                                outline=True,
                                className="mt-2",
                                style={"borderColor": "#7000ff", "color": "#7000ff"}
                            )
                        ], className="text-center py-2")
                    ]),
                    className="card-premium border-0 h-100",
                    style={"borderLeft": "3px solid #7000ff !important",
                           "borderRadius": "12px"}
                ),
                md=6, className="mb-4"
            ),
        ])
    ]
)
