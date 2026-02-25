# Bucket Dashboard - Light Version

**Version**: 2.5 (Handover Ready)
**Status**: Production Ready

## 📖 Executive Summary
The **Bucket Dashboard (Light Version)** is a specialized tool designed to manage, monitor, and execute validation experiments. It replaces legacy, monolithic scripts with a modern, modular web application built on **Python Dash**.

This system allows engineers to:
1.  **Manage Units**: Track Units, Buckets, and Products hierarchically.
2.  **Visual Interaction**: View real-time status, MRS expiration, and core logs via an interactive UI.
3.  **Experiment Suite**: Create individual tests or complex parameter sweeps (Voltage/Frequency) with a standardized Recipe Builder.
4.  **Recipe Standardization**: Automatically generate JSON configuration files ("Recipes") that are strictly compliant with the validation framework (FrameworkV2).

---

## 🚀 Quick Start (One-Click Setup)

We have streamlined the setup process for a **Zero Friction Handover**.

### 1. Prerequisites
- **Python 3.10+**: Ensure Python is installed and added to your **PATH**. 
    - [Download Python](https://www.python.org/downloads/)

### 2. Run the Application
Simply double-click the `run_app.bat` file in the project root.

The script will automatically:
1.  **Check** if Python is available.
2.  **Create** a safe, isolated virtual environment (`venv/`).
3.  **Install** all necessary dependencies from `requirements.txt`.
4.  **Launch** the dashboard in your default browser.

> **Note**: The first run may take a minute to create the environment and download libraries. Subsequent runs will be instant.

---

## 🏗 Architecture Overview

The project follows a **Service-Oriented Architecture (SOA)** with a clean separation of concerns:

-   **`app.py`**: Entry point. Initializes the Dash app and layout.
-   **`pages/`**: Contains the view logic (Controllers).
    -   `dashboard.py`: Main interactive dashboard.
-   **`components/`**: Reusable UI elements (modals, cards, grids).
-   **`services/`**: Business Logic Layer (The "Brain").
    -   **`UnitService`**: Handles file system I/O for Products/Buckets/Units.
    -   **`ExperimentService`**: Core logic for validating, creating, and ACTIVATING experiments. Generates the standard JSON recipes.
    -   **`TemplateService`**: Manages the "Save/Load Recipe" feature for templating.
    -   **`DataHandler`**: Low-level JSON read/write operations.

---

## 📂 File Structure
```
Light_Version_Dev/
├── run_app.bat            # <--- START HERE (Launcher)
├── app.py                 # Main Application
├── config.py              # Configuration constants
├── requirements.txt       # Python dependencies
├── .gitignore             # Git configuration
├── components/            # UI Components
├── pages/                 # View Controllers
├── services/              # Business Logic
├── settings/              # Configuration files
└── data/                  # Data Storage (JSONs)
```

---
**Handover Date**: Feb 2026
