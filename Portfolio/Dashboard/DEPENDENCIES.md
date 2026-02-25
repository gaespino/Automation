# Project Dependencies & Installation Guide

This document lists all requirements necessary to run the **Bucket Dashboard (Light Version)**.

## 1. System Requirements
- **OS**: Windows 10/11 (Preferred) or Linux.
- **Python**: Version 3.8 or higher.
- **Browser**: Chrome, Edge, or Firefox (Latest versions recommended for CSS Grid/Flexbox support).

## 2. Python Libraries
Install the following packages using pip:

```bash
pip install dash dash-bootstrap-components pandas numpy
```

### Library Details:
| Library | Version Tested | Purpose |
| :--- | :--- | :--- |
| `dash` | 2.14.0+ | Core framework for the web application. |
| `dash-bootstrap-components` | 1.5.0+ | UI components (grid, cards, modals, buttons). |
| `pandas` | 2.0.0+ | Data manipulation (optional for grid, but recommended). |
| `numpy` | 1.24.0+ | Used for generating Sweep values (numeric ranges). |

## 3. Project Structure Requirements
The application expects the following directory structure to function correctly. Ensure these exist relative to `app.py`:

```
Light_Version_Dev/
├── assets/             # CSS, Images, JS
│   ├── style.css       # Premium Theme
│   └── script.js       # Clientside callbacks
├── components/         # UI Modules
│   ├── recipe_builder.py
│   ├── unit_selector.py
│   └── ...
├── pages/              # Page Layouts
│   └── dashboard.py
├── services/           # Backend Logic
│   └── data_handler.py
├── data/               # Local Data Store (Mocking Production)
│   └── [Product]/Buckets/...
├── config.py           # Configuration constants
└── app.py              # Entry Point
```

## 4. Running the Application
To start the dashboard, navigate to the project folder and run:

```bash
python app.py
```

The application will be accessible at `http://127.0.0.1:8050/`.
