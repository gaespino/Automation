"""
Unified Navigation Bar
=======================
Shared across all Portfolio pages (Unit Portfolio + THR Tools).
Dark-themed, consistent with existing Dashboard style.
"""
from dash import html
import dash_bootstrap_components as dbc

TOOLS = [
    {"name": "PTC Loop Parser",          "href": "/thr-tools/loop-parser"},
    {"name": "PPV MCA Report",           "href": "/thr-tools/mca-report"},
    {"name": "MCA Single Decoder",       "href": "/thr-tools/mca-decoder"},
    {"name": "DPMB Requests",            "href": "/thr-tools/dpmb"},
    {"name": "File Handler",             "href": "/thr-tools/file-handler"},
    {"name": "Framework Report Builder", "href": "/thr-tools/framework-report"},
    {"name": "Automation Flow Designer", "href": "/thr-tools/automation-designer"},
    {"name": "Experiment Builder",       "href": "/thr-tools/experiment-builder"},
    {"name": "Fuse File Generator",      "href": "/thr-tools/fuse-generator"},
]


def build_navbar() -> dbc.Navbar:
    """Build and return the unified top navigation bar."""
    thr_menu_items = [
        dbc.DropdownMenuItem(tool["name"], href=tool["href"])
        for tool in TOOLS
    ]

    return dbc.Navbar(
        dbc.Container(
            fluid=True,
            children=[
                # Brand
                dbc.NavbarBrand(
                    [
                        html.Span("●", style={"color": "#00d4ff", "marginRight": "8px", "fontSize": "1.1rem"}),
                        "THR Tools"
                    ],
                    href="/",
                    style={"color": "#e0e0e0", "fontWeight": "600", "fontFamily": "Inter, sans-serif"}
                ),

                dbc.NavbarToggler(id="navbar-toggler"),

                dbc.Collapse(
                    dbc.Nav(
                        [
                            dbc.NavItem(
                                dbc.NavLink(
                                    "Unit Portfolio",
                                    href="/portfolio",
                                    style={"color": "#a0a0a0"},
                                    active="partial",
                                    className="nav-link-custom"
                                )
                            ),
                            dbc.DropdownMenu(
                                label="THR Tools",
                                nav=True,
                                in_navbar=True,
                                children=thr_menu_items,
                                toggle_style={"color": "#a0a0a0"},
                                menu_variant="dark",
                                style={"color": "#a0a0a0"},
                            ),
                        ],
                        className="ms-auto",
                        navbar=True,
                    ),
                    id="navbar-collapse",
                    navbar=True,
                    is_open=False,
                ),
            ]
        ),
        color="dark",
        dark=True,
        className="mb-4 shadow-sm border-bottom border-secondary",
        style={"backgroundColor": "#15171e", "fontFamily": "Inter, sans-serif"}
    )
