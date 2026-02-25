import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from pages.dashboard import layout as dashboard_layout

# Initialize App with Bootstrap and Custom Theme
# (Reload Triggered v4)
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap",
        "https://cdn.jsdelivr.net/npm/ag-grid-community/styles/ag-grid.css",
        "https://cdn.jsdelivr.net/npm/ag-grid-community/styles/ag-theme-alpine-dark.css"
    ],
    suppress_callback_exceptions=True
)
server = app.server

# Basic App Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    # Navbar (Simplified)
    dbc.NavbarSimple(
        brand="Bucket Dashboard Light",
        brand_href="#",
        color="dark",
        dark=True,
        className="mb-4 shadow-sm border-bottom border-secondary",
        style={"backgroundColor": "#15171e"}
    ),
    
    # Main Content Area
    html.Div(id='page-content', children=dashboard_layout)
])

import socket
import webbrowser
import threading
import os

def find_free_port(start_port=8050, max_retries=100):
    """Finds the first available port starting from start_port."""
    for port in range(start_port, start_port + max_retries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    raise RuntimeError("No free ports found.")

def open_browser(port):
    """Opens browser only once (avoids reloader double-open)."""
    if "WERKZEUG_RUN_MAIN" not in os.environ:
        webbrowser.open_new(f"http://127.0.0.1:{port}/")

if __name__ == '__main__':
    port = find_free_port(8050) # Start searching from 8050 (default Dash port)
    
    # Schedule browser open
    threading.Timer(1.5, open_browser, args=[port]).start()
    
    # Run App
    print(f"Starting server on port {port}...")
    app.run(debug=True, port=port)
