"""
THRHUB Backend — Flask Application
====================================
REST API server for the THRHUB React frontend.
Entrypoint for both local dev and CaaS (gunicorn app:app).
"""
import logging
import sys
import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from config import HOST, PORT, DEBUG, LOG_LEVEL

# --- Logging ---
logging.basicConfig(
    stream=sys.stdout,
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_BASE = os.path.dirname(os.path.abspath(__file__))
_STATIC = os.path.join(_BASE, "static")


def create_app() -> Flask:
    # Disable built-in static file serving; we handle it manually below
    app = Flask(__name__, static_folder=None)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Blueprints
    from api.dashboard import bp as dashboard_bp
    from api.tools import bp as tools_bp
    from api.config import bp as config_bp

    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(tools_bp, url_prefix="/api/tools")
    app.register_blueprint(config_bp, url_prefix="/api/config")

    # Health probe
    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # Serve React SPA (built output in backend/static/)
    if os.path.isdir(_STATIC):
        @app.route("/assets/<path:filename>")
        def serve_assets(filename):
            return send_from_directory(os.path.join(_STATIC, "assets"), filename)

        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_spa(path):
            # If it's a real static file (favicon etc.), serve it
            candidate = os.path.join(_STATIC, path)
            if path and os.path.isfile(candidate):
                return send_from_directory(_STATIC, path)
            # Otherwise fall back to index.html for React Router
            return send_from_directory(_STATIC, "index.html")
    else:
        logger.warning("No static/ folder found — frontend not built. Run: cd frontend && npm run build")

    return app


app = create_app()

if __name__ == "__main__":
    import socket

    def find_free_port(start=PORT, retries=100):
        for p in range(start, start + retries):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", p)) != 0:
                    return p
        raise RuntimeError("No free port found.")

    port = find_free_port()
    logger.info(f"Starting THRHUB backend on http://127.0.0.1:{port}")
    app.run(debug=DEBUG, host=HOST, port=port)
