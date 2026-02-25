import os

# Base Directory: Current Light_Version_Dev folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data Directory (Mock Data)
PRODUCTS_DIR = os.path.join(BASE_DIR, 'data')

# Constants
OPCIONES_ESTADO = [
    "Pass", "Fail", "Pending", "Running", "Fail - Setup", "Not_Done"
]
