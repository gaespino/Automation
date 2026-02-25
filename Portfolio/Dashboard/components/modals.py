from dash import html, dcc
import dash_bootstrap_components as dbc

def create_recipe_viewer_modal():
    return dbc.Modal([
        dbc.ModalHeader("Recipe Content", className="bg-dark text-white border-bottom border-secondary"),
        dbc.ModalBody([
            html.Pre(id="recipe-viewer-content", className="text-info small bg-black p-3 rounded border border-secondary")
        ], className="bg-dark"),
        dbc.ModalFooter(
            dbc.Button("Close", id="btn-close-viewer", className="ms-auto", outline=True, color="secondary"),
            className="bg-dark border-top border-secondary"
        )
    ], id="modal-recipe-viewer", size="lg")

def create_unit_creation_modal():
    return dbc.Modal([
        dbc.ModalHeader("Add New Unit", className="bg-dark text-white border-bottom border-secondary"),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    dbc.Row([
                        dbc.Col(dbc.Label("Product"), width="auto"),
                        dbc.Col(dbc.Button(html.I(className="bi bi-plus-circle"), id="btn-open-prod-modal-2", size="sm", color="link", className="text-info p-0 ms-1"), width="auto")
                    ], className="align-items-center mb-1"),
                    dcc.Dropdown(id="new-unit-product", options=["GNR", "SRF"], value="GNR", className="dash-dropdown mb-2"),
                    
                    dbc.Row([
                        dbc.Col(dbc.Label("Bucket"), width="auto"),
                        dbc.Col(dbc.Button(html.I(className="bi bi-plus-circle"), id="btn-open-buck-modal-2", size="sm", color="link", className="text-info p-0 ms-1"), width="auto")
                    ], className="align-items-center mb-1"),
                    dbc.Input(id="new-unit-bucket", placeholder="e.g. Imunch", className="bg-dark text-white mb-2"),
                    
                    dbc.Label("Visual ID"),
                    dbc.Input(id="new-unit-vid", placeholder="e.g. 75Q...", className="bg-dark text-white mb-2"),
                ]),
                dbc.Col([
                    dbc.Label("Platform"),
                     dcc.Dropdown(id="new-unit-platform", options=["AP", "SP"], value="AP", className="dash-dropdown mb-2"),
                     dbc.Label("QDF"),
                     dbc.Input(id="new-unit-qdf", placeholder="e.g. RPKY", className="bg-dark text-white mb-2"),
                ])
            ])
        ], className="bg-dark text-white"),
        dbc.ModalFooter([
             dbc.Button("Cancel", id="btn-cancel-unit", className="me-auto", outline=True, color="secondary"),
             dbc.Button("Create Unit", id="btn-create-unit", color="success")
        ], className="bg-dark border-top border-secondary")
    ], id="modal-unit-creator")
def create_product_modal():
    return dbc.Modal([
        dbc.ModalHeader(html.H5("Add New Product", className="text-info m-0"), close_button=True, className="bg-dark border-secondary"),
        dbc.ModalBody([
            dbc.Label("Product Name (e.g. GNR, SRF)", className="small text-secondary"),
            dbc.Input(id="new-prod-name", className="bg-dark text-white border-secondary mb-3"),
            html.Div(id="prod-modal-msg", className="small text-warning")
        ], className="bg-dark text-white"),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="btn-cancel-prod", size="sm", outline=True, color="secondary"),
            dbc.Button("Create", id="btn-create-prod", size="sm", color="info")
        ], className="bg-dark border-secondary")
    ], id="modal-product-creator", size="sm")

def create_bucket_modal():
    return dbc.Modal([
        dbc.ModalHeader(html.H5("Add New Bucket", className="text-info m-0"), close_button=True, className="bg-dark border-secondary"),
        dbc.ModalBody([
            dbc.Label("Parent Product", className="small text-secondary"),
            dcc.Dropdown(id="new-buck-parent", className="dash-dropdown mb-3"),
            dbc.Label("Bucket Name (e.g. Imunch)", className="small text-secondary"),
            dbc.Input(id="new-buck-name", className="bg-dark text-white border-secondary mb-3"),
            html.Div(id="buck-modal-msg", className="small text-warning")
        ], className="bg-dark text-white"),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="btn-cancel-buck", size="sm", outline=True, color="secondary"),
            dbc.Button("Create", id="btn-create-buck", size="sm", color="info")
        ], className="bg-dark border-secondary")
    ], id="modal-bucket-creator", size="sm")

def create_save_recipe_modal():
    return dbc.Modal([
        dbc.ModalHeader(html.H5("Save as Recipe", className="text-info m-0"), close_button=True, className="bg-dark border-secondary"),
        dbc.ModalBody([
            dbc.Label("Recipe Name", className="text-white"),
            dbc.Input(id="new-recipe-name", placeholder="e.g. Standard_Flow_AP", className="bg-dark text-white border-secondary mb-3"),
            html.Div(id="save-recipe-msg", className="small text-warning")
        ], className="bg-dark text-white"),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="btn-cancel-save-recipe", size="sm", outline=True, color="secondary"),
            dbc.Button("Save Recipe", id="btn-confirm-save-recipe", size="sm", color="success")
        ], className="bg-dark border-secondary")
    ], id="modal-save-recipe", size="sm", backdrop="static")

def create_load_recipe_modal():
    return dbc.Modal([
        dbc.ModalHeader(html.H5("Load Recipe Template", className="text-info m-0"), close_button=True, className="bg-dark border-secondary"),
        dbc.ModalBody([
            dbc.Label("Select Recipe", className="text-white"),
            dcc.Dropdown(id="select-recipe-dropdown", className="dash-dropdown mb-3"),
            html.Div(id="load-recipe-msg", className="small text-warning")
        ], className="bg-dark text-white"),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="btn-cancel-load-recipe", size="sm", outline=True, color="secondary"),
            dbc.Button("Load Experiments", id="btn-confirm-load-recipe", size="sm", color="primary")
        ], className="bg-dark border-secondary")
    ], id="modal-load-recipe", size="sm", backdrop="static")
