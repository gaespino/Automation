# Portfolio THR Tools — Changelog

## [2.1.0] — 2026-02-25

### Summary
Migration of THR Tools from PPV Tkinter desktop GUIs to web (Dash) interface,
restoring full functional parity with the originals. All 128 tests pass.

### Critical Fixes

#### THRTools Package — Import Chain (`THRTools/__init__.py`, `gui/__init__.py`)
- **Root cause**: `THRTools/__init__.py` imported GUI modules (`PPVTools`, `PPVLoopChecks`,
  `PPVDataChecks`, `PPVFileHandler`, `PPVFrameworkReport`) at module level. These modules
  depend on `tkinter`, which is unavailable in headless/CaaS environments.
- **Fix**: Wrapped all GUI imports in `try/except ImportError` in both `__init__.py` files.
  `_GUI_AVAILABLE` flag exported so callers can check availability.
- **Impact**: All backend tests that previously crashed with
  `ModuleNotFoundError: No module named 'tkinter'` now pass.

#### xlwings Removal (`THRTools/parsers/MCAparser.py`, `THRTools/gui/PPVTools.py`)
- **Root cause**: `MCAparser.py` imported `xlwings as xw` and used it in `file_open()`.
  `PPVTools.py` also imported `xlwings`. xlwings requires a local Microsoft Excel
  installation — unavailable in CaaS containers.
- **Fix**: Replaced `xw.Book(file)` in `file_open()` with `load_workbook(file)` (openpyxl,
  already imported). Removed unused `xlwings` import from `PPVTools.py`.
- **Learning**: Use `openpyxl` for all Excel read/write operations.

#### PPVFileHandler.py — Fallback Import
- **Fix**: The fallback `from utils import PPVReportMerger` was failing in isolated
  test contexts. Added `sys.path` manipulation before the fallback and an ultimate
  `prm = None` guard.

### Functional Restorations

#### PPV MCA Report (`pages/thr_tools/mca_report.py`)
- Added **Mode** dropdown (Framework / Bucketer / Data) — was hardcoded to Bucketer.
- Added **Product** dropdown (GNR / CWF / DMR).
- Added **Work Week** dropdown (WW1–WW52, auto-selects current week).
- Added **Label** text field.
- Added **Processing Options** checklist: Reduced report, MCA decode, Overview sheet,
  MCA Checker file — matching `PPVDataChecks.PPVReportGUI` exactly.
- Options "Reduced report" and "MCA decode" are disabled when Mode == Data.
- Backend call now passes all params to `ppv_report(name, week, label, source_file,
  report, reduced, mcdetail, overview, decode, mode, product)`.

#### PTC Loop Parser (`pages/thr_tools/loop_parser.py`)
- Renamed field "Lots Seq Key" → **"Sequence Key"** (matches PPV original).
- Default value for Sequence Key is now 100 (cast to int) matching original.
- Renamed checkbox from "DPMB format output" → **"PySV logging format"**.
  - Original logic: `dpmbformat = not self.dpmb_var.get()` → unchecked → dpmbformat=True.
  - Web now: "pysv" checked → dpmbformat=False (PySV), unchecked → dpmbformat=True (DPMB).

#### File Handler (`pages/thr_tools/file_handler.py`)
- Rewrote to use `PPVReportMerger` backend properly:
  - **Merge mode**: saves uploads to tmpdir, calls
    `merge_excel_files(input_folder, output_file, prefix)`.
  - **Append mode**: two separate file uploads (source + target); calls
    `append_excel_tables(source_file, target_file, sheet_names)`.
- Added **File Prefix Filter** field for Merge mode (matches PPV original).
- Added `dbc.RadioItems` for mode selection (Merge / Append).

#### MCA Single Decoder (`pages/thr_tools/mca_decoder.py`)
- Rewrote to match `PPV/gui/MCADecoder.MCADecoderGUI` fully:
  - **Multiple register fields** per decoder type:
    - CHA/CCF: MC_STATUS, MC_ADDR, MC_MISC, MC_MISC3
    - LLC: MC_STATUS, MC_ADDR, MC_MISC
    - CORE/MEMORY/IO: MC_STATUS, MC_ADDR, MC_MISC
    - First Error: MCERRLOGGINGREG, IERRLOGGINGREG
  - **Subtype dropdown** for CORE (ML2/DCU/IFU/…), MEMORY (B2CMI/MSE/MCCHAN),
    IO (UBOX/UPI/ULA).
  - Uses **`decoder` class** (not `mcadata`) for actual decoding.
  - Added **Export to text file** (`dcc.Download`).

#### DPMB Requests (`pages/thr_tools/dpmb.py`)
- Added `dcc.Download` component (required by test + useful for response export).

### New / Enhanced Tools

#### Experiment Builder (`pages/thr_tools/experiment_builder.py`)
- Rebuilt from scratch to replicate `PPV/gui/ExperimentBuilder.ExperimentBuilderGUI`:
  - **Dynamic form** built from `{Product}ControlPanelConfig.json` — all sections:
    Basic Information, Unit Data, Test Configuration, Voltage & Frequency, Loops,
    Sweep, Shmoo, Linux, Dragon, Merlin, Advanced Configuration.
  - **Conditional sections**: Loops/Sweep/Shmoo sections show only when Test Type matches;
    Linux/Dragon sections show only when Content matches.
  - **Multi-experiment queue**: add, edit (click ✏ on row), delete, clear all.
  - **Template management**: save/load `.tpl` files (JSON with `.tpl` extension).
  - **Import from JSON / .tpl** via file upload.
  - **Import from Excel** (openpyxl named-table format matching PPV's Excel format).
  - **Export to JSON** with custom filename.
  - **Scalable**: add new experiment fields by editing `ControlPanelConfig.json` only.

#### Automation Designer (`pages/thr_tools/automation_designer.py`)
- Rebuilt to replicate `PPV/gui/AutomationDesigner.AutomationFlowDesigner`:
  - **All 9 node types** from original: StartNode, SingleFail, AllFail, MajorityFail,
    Adaptive, Characterization, DataCollection, Analysis, EndNode.
  - **Load experiments** from JSON, .tpl, or Excel (assigned to nodes).
  - **Reorder nodes** (up/down arrows), delete individual nodes.
  - **Unit Configuration** overrides panel (Visual ID, Bucket, COM Port, IP Address,
    600W Unit, Check Core) — applied to experiments on export.
  - **Export Flow Config** as ZIP containing:
    - `FrameworkAutomationStructure.json` — node definitions and connections
    - `FrameworkAutomationFlows.json` — experiment data with unit overrides applied
    - `FrameworkAutomationInit.ini` — INI configuration skeleton
    - `FrameworkAutomationPositions.json` — node position metadata
  - **Save Flow Design** as `.json` (compatible with original `save_flow()` format).
  - **Import flow JSON** to reload a saved design.
  - **Scalable**: add new node types by appending to `_NODE_TYPES` list.

### Test Fixes

- `test_stage2_app_structure::test_dash_app_has_use_pages`: Dash resolves relative
  path to absolute; updated assertion to check `endswith("pages")`.
- `test_stage6_backends::test_mcadata_has_decode_method`: `mcadata` is a data-loader
  class; actual decode class is `decoder`. Updated test to check `decoder` class.

### Learnings (for future stages)

1. **Never import tkinter-dependent modules at package `__init__.py` level** — use
   lazy/optional imports with `try/except` so backends work in headless environments.
2. **xlwings → openpyxl**: xlwings requires a local Excel install; always use openpyxl
   for read/write in CaaS-compatible code. `load_workbook()` is the direct replacement
   for `xw.Book()`.
3. **`decoder` vs `mcadata`**: `mcadata` loads JSON parameter files; `decoder(data, product)`
   wraps it and provides the decode methods (`.cha()`, `.llc()`, `.core()`, `.mem()`,
   `.io()`). Always instantiate `decoder` for actual decoding.
4. **PPVReportMerger functions are module-level**, not class methods. Import the functions
   directly: `merge_excel_files`, `append_excel_tables`, `sheet_names`.
5. **Conditional form sections**: use `style={"display": "none"}` / `{}` toggled by
   callbacks on `Test Type` and `Content` dropdowns.
6. **Scalable config pattern**: `{Product}ControlPanelConfig.json` drives all field
   definitions (type, section, options, conditional). Adding new fields requires only
   a JSON edit — no Python changes.
7. **Flow export format**: the original AutomationDesigner produces 4 files
   (Structure, Flows, Init INI, Positions). The web version replicates this exactly
   and wraps them in a ZIP for browser download.
8. **`.tpl` files**: JSON files with `.tpl` extension. The Experiment Builder can
   save/load them. The Automation Designer can also load them as experiment sources.
