"""
THR Tools Hub Page
===================
Grid of tool cards matching the Tkinter PPVTools.py layout,
adapted to the dark web theme.
"""
import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/thr-tools', name='THR Tools', title='THR Tools')

# Tool definitions — name/description/accent from PPVTools.py, re-mapped to dark palette
TOOLS = [
    {
        "title": "PTC Loop Parser",
        "description": "Parse logs from PTC experiment data and generate DPMB report format files.",
        "features": ["Automated log parsing", "DPMB format output", "Batch processing support"],
        "accent": "#00d4ff",
        "icon": "bi-file-earmark-code",
        "href": "/thr-tools/loop-parser",
    },
    {
        "title": "PPV MCA Report",
        "description": "Generate comprehensive MCA reports from Bucketer files or S2T Logger data.",
        "features": ["Bucketer file analysis", "S2T Logger integration", "MCA decoding & visualization"],
        "accent": "#ff4d4d",
        "icon": "bi-file-earmark-bar-graph",
        "href": "/thr-tools/mca-report",
    },
    {
        "title": "MCA Single Decoder",
        "description": "Decode individual MCA registers for CHA, LLC, CORE, MEMORY, IO, and First Error.",
        "features": ["Single register decode", "Multi-product support", "Easy copy/paste results"],
        "accent": "#ff6b8a",
        "icon": "bi-cpu",
        "href": "/thr-tools/mca-decoder",
    },
    {
        "title": "DPMB Requests",
        "description": "Interface for Bucketer data requests through DPMB API.",
        "features": ["Direct API connection", "Automated data retrieval", "Custom query builder"],
        "accent": "#7000ff",
        "icon": "bi-diagram-3",
        "href": "/thr-tools/dpmb",
    },
    {
        "title": "File Handler",
        "description": "Merge and manage multiple data files efficiently.",
        "features": ["Merge DPMB format files", "Append MCA reports", "Batch file operations"],
        "accent": "#ffbd2e",
        "icon": "bi-files",
        "href": "/thr-tools/file-handler",
    },
    {
        "title": "Framework Report Builder",
        "description": "Create comprehensive reports from Debug Framework experiment data.",
        "features": ["Unit overview generation", "Summary file merging", "Multi-experiment analysis"],
        "accent": "#00ff9d",
        "icon": "bi-bar-chart-steps",
        "href": "/thr-tools/framework-report",
    },
    {
        "title": "Automation Flow Designer",
        "description": "Visual tool for designing and managing automation test flows.",
        "features": ["Drag-and-drop flow design", "Experiment sequencing", "Export automation configs"],
        "accent": "#00c9a7",
        "icon": "bi-bezier2",
        "href": "/thr-tools/automation-designer",
    },
    {
        "title": "Experiment Builder",
        "description": "Create and edit JSON configurations for Debug Framework Control Panel.",
        "features": ["Build experiments from scratch", "Import from Excel/JSON", "Export Control Panel configs"],
        "accent": "#36d7b7",
        "icon": "bi-sliders",
        "href": "/thr-tools/experiment-builder",
    },
]

FULL_WIDTH_TOOL = {
    "title": "Fuse File Generator",
    "description": "Engineering tool for managing and generating fuse configuration files from CSV data.",
    "features": ["Parse and filter fuse CSV files", "Product-specific IP configuration", "Generate .fuse files for fusefilegen"],
    "accent": "#ff9f45",
    "icon": "bi-lightning-charge",
    "href": "/thr-tools/fuse-generator",
}


def _tool_card(tool: dict, full_width: bool = False) -> dbc.Col:
    """Render a single tool card column."""
    features = html.Ul(
        [html.Li(f, style={"color": "#a0a0a0", "fontSize": "0.82rem"}) for f in tool["features"]],
        style={"paddingLeft": "1.2rem", "marginBottom": "0", "lineHeight": "1.8"}
    )

    card = dbc.Card(
        dbc.CardBody([
            html.Div([
                html.I(
                    className=f"bi {tool['icon']} me-2",
                    style={"color": tool["accent"], "fontSize": "1.2rem"}
                ),
                html.Span(
                    tool["title"],
                    style={"color": tool["accent"], "fontWeight": "600",
                           "fontSize": "1rem", "fontFamily": "Inter, sans-serif"}
                )
            ], className="mb-2"),
            html.P(tool["description"],
                   style={"color": "#e0e0e0", "fontSize": "0.88rem", "marginBottom": "0.75rem"}),
            features,
            html.Div(
                dbc.Button(
                    [html.I(className="bi bi-arrow-right-circle me-1"), "Open Tool"],
                    href=tool["href"],
                    size="sm",
                    outline=True,
                    className="mt-3",
                    style={"borderColor": tool["accent"], "color": tool["accent"]}
                ),
                className="mt-2"
            )
        ]),
        className="card-premium border-0 h-100",
        style={"borderLeft": f"3px solid {tool['accent']}", "borderRadius": "12px"}
    )

    return dbc.Col(card, md=12 if full_width else 4, className="mb-4")


layout = dbc.Container(
    fluid=True,
    className="pb-5",
    style={"backgroundColor": "var(--bg-body, #0a0b10)"},
    children=[
        dbc.Row(
            dbc.Col(html.Div([
                html.H2("THR Tools", className="fw-bold mb-1",
                        style={"color": "#e0e0e0", "fontFamily": "Inter, sans-serif"}),
                html.P("Debug & analysis tools for GNR, CWF, and DMR products.",
                       style={"color": "#a0a0a0", "fontFamily": "Inter, sans-serif"}),
                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)", "marginBottom": "1.5rem"})
            ], className="pt-4 pb-1"), width=12)
        ),

        # 3-column grid of 8 tools
        dbc.Row([_tool_card(t) for t in TOOLS]),

        # Full-width Fuse Generator
        dbc.Row([_tool_card(FULL_WIDTH_TOOL, full_width=True)]),
    ]
)
