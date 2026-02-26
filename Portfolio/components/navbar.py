"""
Dashboard Navigation Bar
=========================
Navigation for the Dash Dashboard pages (Unit Portfolio).
THR Tools are served as a separate React SPA at /thr/ — linked from here.
"""
from dash import html
import dash_bootstrap_components as dbc


def build_navbar() -> dbc.Navbar:
    """Build and return the unified top navigation bar."""
    return dbc.Navbar(
        dbc.Container(
            fluid=True,
            children=[
                dbc.NavbarBrand(
                    [
                        html.Span("●", style={"color": "#00d4ff", "marginRight": "8px", "fontSize": "1.1rem"}),
                        "Portfolio"
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
                            dbc.NavItem(
                                dbc.NavLink(
                                    "THR Tools",
                                    href="/thr/",
                                    style={"color": "#a0a0a0"},
                                    external_link=True,
                                    className="nav-link-custom"
                                )
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

