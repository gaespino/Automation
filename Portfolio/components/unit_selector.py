from dash import html, dcc
import dash_bootstrap_components as dbc

def create_unit_selector():
    return dbc.Card(className="card-premium h-100", children=[
        dbc.CardHeader(
            html.Div([
                html.Div([html.I(className="bi bi-cpu-fill me-2"), "Unit Selection"]),
                dbc.Button(html.I(className="bi bi-plus-lg"), id="btn-open-unit-modal", size="sm", color="link", className="text-white p-0")
            ], className="card-header-custom d-flex justify-content-between align-items-center")
        ),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.Label("Product", className="small text-secondary text-uppercase fw-bold"), width="auto"),
                dbc.Col(dbc.Button(html.I(className="bi bi-plus-circle"), id="btn-open-prod-modal", size="sm", color="link", className="text-info p-0 ms-1"), width="auto")
            ], className="mb-1 align-items-center"),
            dcc.Dropdown(id='sel-product', className="dash-dropdown mb-3", placeholder="Select Product..."),
            
            dbc.Row([
                dbc.Col(dbc.Label("Bucket", className="small text-secondary text-uppercase fw-bold"), width="auto"),
                dbc.Col(dbc.Button(html.I(className="bi bi-plus-circle"), id="btn-open-buck-modal", size="sm", color="link", className="text-info p-0 ms-1"), width="auto")
            ], className="mb-1 align-items-center"),
            dcc.Dropdown(id='sel-bucket', className="dash-dropdown mb-3", placeholder="Select Bucket...", disabled=True),
            
            dbc.Label("Platform", className="small text-secondary text-uppercase fw-bold"),
            dbc.RadioItems(
                id='sel-platform',
                options=[{'label': 'AP', 'value': 'AP'}, {'label': 'SP', 'value': 'SP'}],
                value='AP',
                inline=True,
                className="mb-3",
                inputClassName="btn-check",
                labelClassName="btn btn-outline-custom btn-sm me-2",
                labelCheckedClassName="active"
            ),
            
            dbc.Label("Unit", className="small text-secondary text-uppercase fw-bold"),
            dcc.Dropdown(id='sel-unit', className="dash-dropdown mb-3", placeholder="Select Unit...", disabled=True),

            html.Hr(className="border-secondary"),

            dbc.Button(
                [html.I(className="bi bi-arrow-clockwise me-2"), "Load Data (API)"],
                id='btn-load-data',
                color="primary",
                className="btn-primary-custom w-100",
                disabled=True
            )
        ])
    ])
