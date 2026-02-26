"""
Portfolio Dashboard — Dash app
===============================
Serves the Unit Portfolio / Dashboard pages.
Mounted at /dashboard/ by FastAPI (api/main.py).

Entry points:
  Development:  uvicorn api.main:app --reload --port 8000
  CaaS:         uvicorn api.main:app --host 0.0.0.0 --port 8000

THR Tools are served separately at /thr/ (React SPA) with a REST backend at /api/.
"""
import logging
import sys
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from config import PORT, DEBUG, HOST, LOG_LEVEL
from components.navbar import build_navbar

# --- Logging ---
logging.basicConfig(
    stream=sys.stdout,
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- App Initialization ---
app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder='pages',
    assets_folder='assets',
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap",
        "https://cdn.jsdelivr.net/npm/ag-grid-community/styles/ag-grid.css",
        "https://cdn.jsdelivr.net/npm/ag-grid-community/styles/ag-theme-alpine-dark.css"
    ],
    suppress_callback_exceptions=True
)

# Expose Flask server — FastAPI mounts this via starlette.middleware.wsgi
server = app.server

# --- Health check endpoint ---
@server.route('/health')
def health():
    return 'OK', 200

# --- App Layout ---
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    build_navbar(),
    html.Div(
        dash.page_container,
        style={'minHeight': 'calc(100vh - 56px)'}
    )
], style={'backgroundColor': 'var(--bg-body, #0a0b10)', 'minHeight': '100vh'})


# --- Dev server launch ---
if __name__ == '__main__':
    import socket
    import webbrowser
    import threading
    import os

    def find_free_port(start=8050, retries=100):
        for p in range(start, start + retries):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', p)) != 0:
                    return p
        raise RuntimeError("No free ports found.")

    def open_browser(port):
        if "WERKZEUG_RUN_MAIN" not in os.environ:
            webbrowser.open_new(f"http://127.0.0.1:{port}/")

    port = find_free_port(PORT)
    threading.Timer(1.5, open_browser, args=[port]).start()
    logger.info(f"Starting Portfolio server on port {port}...")
    app.run(debug=DEBUG, host=HOST, port=port)
