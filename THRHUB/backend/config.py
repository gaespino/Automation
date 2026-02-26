"""
THRHUB Backend — Configuration
================================
Environment-variable-driven config for CaaS compatibility.
"""
import os

# --- Server ---
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5050"))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# --- Data paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.environ.get("DATA_PATH", os.path.join(BASE_DIR, "data"))
CONFIGS_PATH = os.environ.get("CONFIGS_PATH", os.path.join(BASE_DIR, "configs"))

# --- Products ---
PRODUCTS = ["GNR", "CWF", "DMR"]
