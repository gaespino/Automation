import dash_ag_grid as dag
from dash import html
import dash_bootstrap_components as dbc
from config import OPCIONES_ESTADO

def create_experiments_grid():
    columnDefs = [
        {"field": "Experiment", "headerName": "Experiment Name", "checkboxSelection": True, "headerCheckboxSelection": True, "pinned": "left", "width": 300},
        {
            "field": "Estado", 
            "headerName": "Status", 
            "width": 140, 
            "editable": True,
            "cellEditor": "agSelectCellEditor",
            "cellEditorParams": {"values": OPCIONES_ESTADO},
            "singleClickEdit": True,
            "cellStyle": {'textAlign': 'center'} 
        },
        {"field": "FailRate", "headerName": "Fail Rate"},
        {"field": "Test Type", "headerName": "Type"},
        {"field": "Link", "headerName": "Recipe Path"}
    ]

    return dbc.Card(className="card-premium", children=[
        dbc.CardHeader(
            dbc.Row([
                dbc.Col(html.Div([html.I(className="bi bi-table me-2"), "Experiments"], className="card-header-custom p-0"), width="auto"),
               
                # Action Buttons
                dbc.Col([
                    dbc.Button(html.I(className="bi bi-plus-lg"), id="btn-add-exp", size="sm", color="success", className="me-1", outline=True, title="Add Experiment"),
                    dbc.Button(html.I(className="bi bi-cloud-download"), id="btn-open-load-recipe", size="sm", color="primary", className="me-1", outline=True, title="Load Recipe Template"),
                    dbc.Button(html.I(className="bi bi-pencil-square"), id="btn-edit-exp", size="sm", color="info", className="me-1", outline=True, title="Edit Selected"),
                    dbc.Button(html.I(className="bi bi-files"), id="btn-dup-exp", size="sm", color="primary", className="me-1", outline=True, title="Duplicate Selected"),
                    dbc.Button(html.I(className="bi bi-trash"), id="btn-del-exp", size="sm", color="danger", className="me-1", outline=True, title="Delete Selected"),
                    dbc.Button(html.I(className="bi bi-code-slash"), id="btn-view-recipe", size="sm", color="secondary", className="me-1", outline=True, title="View Recipe JSON"),
                    dbc.Button(html.I(className="bi bi-cloud-upload"), id="btn-open-save-recipe", size="sm", color="success", className="me-1", outline=True, title="Save as Recipe Template"),
                    dbc.Button([html.I(className="bi bi-lightning-fill me-1"), "Activate"], id="btn-activate", size="sm", color="warning", className="me-1 fw-bold", title="Activate Pending"),
                    dbc.Button([html.I(className="bi bi-save me-1"), "Save"], id="btn-save", size="sm", color="info", className="fw-bold", disabled=True),
                ], width="auto", className="d-flex align-items-center"),

                dbc.Col(dbc.Input(id="grid-search", placeholder="Search...", size="sm", className="bg-dark text-white border-secondary"), width=3, className="ms-auto"),
            ], align="center"),
            className="border-bottom border-secondary px-4 py-3"
        ),
        dbc.CardBody([
            dag.AgGrid(
                id="experiments-grid",
                columnDefs=columnDefs,
                dashGridOptions={
                    "rowSelection": "multiple",
                    "pagination": True,
                    "paginationPageSize": 15,
                    "suppressRowClickSelection": True,
                    "animateRows": True
                },
                defaultColDef={"sortable": True, "filter": True, "resizable": True},
                className="ag-theme-alpine-dark",
                style={"height": "500px", "width": "100%"},
            )
        ], className="p-0")
    ])
