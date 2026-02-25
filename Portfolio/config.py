"""
Portfolio App Configuration
============================
All settings read from environment variables with local dev fallbacks.
CaaS deployment: set env vars in container manifest.
Local dev: defaults work out of the box.
"""
import os

# Base directory = Portfolio/ folder (this file's location)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Data & Paths ---
# CaaS: mount a persistent volume and set DATA_PATH to its mount point
PRODUCTS_DIR = os.environ.get('DATA_PATH', os.path.join(BASE_DIR, 'data'))

# CaaS: set FRAMEWORK_PATH to the UNC path accessible from the container
# (requires CIFS/SMB sidecar or init container — see CAAS_TODO.md)
FRAMEWORK_PATH = os.environ.get(
    'FRAMEWORK_PATH',
    r'\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\DebugFramework'
)

# Settings directory (scripts config, templates)
SETTINGS_DIR = os.path.join(BASE_DIR, 'settings')

# THRTools backend root
THRTOOLS_DIR = os.path.join(BASE_DIR, 'THRTools')

# --- Server ---
PORT = int(os.environ.get('PORT', 8050))
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
HOST = os.environ.get('HOST', '0.0.0.0')

# --- Logging ---
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# --- Application Constants ---
OPCIONES_ESTADO = [
    "Pass", "Fail", "Pending", "Running", "Fail - Setup", "Not_Done"
]

# Product list (driven by data folder; this is used as fallback/validation)
SUPPORTED_PRODUCTS = ['GNR', 'CWF', 'DMR']

# Framework disk structure: {FRAMEWORK_PATH}/{Product}/{VID}/{RVP}/{Date}/{Experiments}
FRAMEWORK_EXPERIMENT_PATTERN = r'^(\d{8})_(\d{6})_T(\d+)_(.+)$'
