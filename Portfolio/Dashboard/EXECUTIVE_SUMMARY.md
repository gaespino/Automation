# Executive Summary: Bucket Dashboard (Light Version)

## 1. Project Overview
The **Bucket Dashboard (Light Version)** is a specialized, modular development environment designed to replicate the core functionality of the main production dashboard—specifically **Experiment Creation and Unit Management**—without the dependencies of the onsite execution runner.

**Goal**: Provide a lightweight, "Premium" UI for engineers to create, edit, and manage test recipes (JSON) locally, ensuring high data integrity and a superior user experience.

## 2. Key Features
- **Experiment Builder**: A complete, faithful replication of the complex "Recipe Builder" modal, ported to an agnostic component structure. It supports all legacy fields (Linux/Dragon flavors) plus dynamic logic (Sweeps, Loops).
- **Unit Management**: Ability to create new Unit Data Structures directly from the UI, enforcing correct folder hierarchy (`Product > Bucket > Type > Unit`).
- **Premium UI**: high-contrast "Dark Mode" design with glassmorphism elements, ensuring readability in lab environments.
- **Logic Enhancements**:
    -   **Auto-Population**: Automatically fills contextual data (VID, Cores) to reduce human error.
    -   **Sweep Generation**: Automatically expands a single "Sweep" definition into multiple discrete experiment steps.
    -   **Interactive Grid**: Edit statuses, duplicate experiments, and activate batches directly from the table.

## 3. Technical Architecture
The project follows a component-based architecture using **Plotly Dash**:

### A. Directory Hierarchy
- **`app.py`**: Entry point. Handles routing and server initialization.
- **`config.py`**: Centralized configuration (paths, constants).
- **`services/`**:
    -   `data_handler.py`: The "Brain" of the data layer. Abstraction for reading/writing JSON files. Can be refactored in the future to talk to an API (Phase 4).
- **`components/`**: Reusable UI blocks.
    -   `unit_selector.py`: Navigation menu.
    -   `recipe_builder.py`: The complex form logic.
    -   `experiments_grid.py`: AgGrid interactive table.
- **`pages/`**:
    -   `dashboard.py`: Controller that wires components together using Callbacks.

### B. Data Flow
1.  **Read**: `unit_selector` calls `DataHandler.get_units()`.
2.  **Context**: Selection is stored in `dcc.Store(id='store-unit-data')`.
3.  **Render**: `dashboard.py` updates the Grid and Stats Card based on the Store.
4.  **Write**: User Actions (Save/Create) trigger callbacks that pass data back to `DataHandler` to write to JSON files.

## 4. Future Considerations (Handover Notes)
- **Backend Integration**: The current `DataHandler` reads local files. To move to production, this class should be updated to make HTTP requests to the CAS API (Phase 4). The architecture is ready for this switch (Strategy Pattern recommended).
- **Monitoring**: The "Unit Monitoring" view from the legacy app was not ported to this Light Version, as the focus was on *Creation* workflow. If needed, a `pages/monitoring.py` can be added following the existing patterns.
- **Validation**: Current validation is frontend-based. For production, backend schema validation `(json.validate)` is recommended before saving.

## 5. Conclusion
This "Light Version" stands as a robust, standalone tool. It has rectified previous UI/UX issues (contrast, usability) and implemented critical missing logic (Sweeps expansion). It is ready for deployment as a local editor tool or for integration into the larger ecosystem.
