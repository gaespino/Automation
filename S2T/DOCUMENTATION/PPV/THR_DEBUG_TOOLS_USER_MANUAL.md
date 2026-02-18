# THR Debug Tools - User Manual

**Version:** 2.0
**Release Date:** January 15, 2026
**Organization:** Intel Corporation - Test & Validation
**Classification:** Intel Confidential
**Maintainer:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)
**Repository:** `c:\Git\Automation\PPV\`
**Documentation:** `c:\Git\Automation\S2T\DOCUMENTATION\`
**Python Requirements:** Python 3.7+, tkinter, pandas, openpyxl, tabulate

---

## Overview

The **THR Debug Tools** (Test Hole Resolution Debug Tools) suite is a comprehensive Python GUI application designed for unit characterization, post-silicon validation, and debug workflows. The tools integrate seamlessly with Intel's Debug Framework, providing engineers with powerful capabilities for MCA (Machine Check Architecture) analysis, experiment configuration, data collection automation, and comprehensive report generation.

**Main Entry Point:** `run.py`

---

## Installation

### Prerequisites
```bash
# Required Python packages
pip install pandas openpyxl tabulate requests
```

### Launch the Tools Hub
```bash
cd c:\Git\Automation\PPV
python run.py
```

The Tools Hub will display a product selector (GNR/CWF/DMR) and launch the main interface with access to all 9 tools.

---

## Tools Hub Architecture

The THR Debug Tools Hub provides a centralized launcher with modern card-based UI:

- **Product Selector**: Choose target product (GNR, CWF, DMR) for tool configuration
- **Tool Cards**: Visual cards for each tool with color-coded headers
- **Context Preservation**: Selected product persists across all launched tools

---

## Tool 1: PTC Loop Parser

**Purpose:** Parse PTC (Post-Test Check) loop data from Framework execution folders, extracting key metrics and generating consolidated Excel reports.

**Color:** Blue (#3498db)
**Location:** `gui/PPVLoopChecks.py`
**Parser:** `parsers/PPVLoopsParser.py`

### Features
- Parse loop folders with structured experiment data
- Extract sequence-based loop metrics
- Generate Excel reports with loop summaries
- Support for ZIP file processing
- Configurable sequence keys for data organization

### Usage

#### GUI Launch
1. From Tools Hub → Click **PTC Loop Parser**
2. Configure experiment parameters:
   - **Bucket**: Experiment bucket identifier (e.g., `PPV_Loops_WW45`)
   - **Week**: Work week number (e.g., `45`)
   - **Sequence Key**: Sequence identifier (default: `100`)
3. Select paths:
   - **Output File**: Excel report destination
   - **Loops Folder**: Source folder containing loop data
4. Enable **Process ZIP files** if data is compressed
5. Click **Run** to generate report

#### Parameters
- **Bucket** (str): Experiment bucket name for tracking
- **Week** (int): Work week for temporal organization
- **Sequence Key** (str): Sequence identifier for loop grouping
- **Output File** (str): Path to output Excel file
- **Loops Folder** (str): Directory containing loop experiments
- **Zipfile** (bool): Enable ZIP file processing

#### Output Format
Excel file with columns:
- Experiment metadata (bucket, week, sequence)
- Loop iteration counts
- Pass/Fail statistics
- PostCode analysis
- Timing information

---

## Tool 2: PPV MCA Report Builder

**Purpose:** Generate comprehensive Machine Check Architecture (MCA) reports from Framework logs, Bucketer data, or raw data files with detailed error analysis.

**Color:** Red (#e74c3c)
**Location:** `gui/PPVDataChecks.py`
**Parser:** `parsers/MCAparser.py`

### Features
- Multiple data source modes (Framework, Bucketer, Data)
- Product-specific MCA decoding (GNR/CWF/DMR)
- Week-based organization
- Custom report labeling
- Automated MCA error extraction and categorization
- Support for multiple decoders (CHA, LLC, CORE, MEMORY, IO)

### Usage

#### GUI Launch
1. From Tools Hub → Click **PPV MCA Report Builder**
2. Configure report settings:
   - **Mode**: Select data source
     - `Framework`: Parse Framework execution logs
     - `Bucketer`: Load from DPMB Bucketer exports
     - `Data`: Process raw data files
   - **Product**: Target product (GNR/CWF/DMR)
   - **Week**: Current work week (auto-populated)
   - **Label**: Custom report identifier
3. Select files:
   - **Source File**: Input data file (changes by mode)
   - **Report Output**: Excel report destination
4. Click **Generate Report**

#### Parameters
- **Mode** (str): Data source type [`Framework`, `Bucketer`, `Data`]
- **Product** (str): Product family [`GNR`, `CWF`, `DMR`]
- **Week** (int): Work week (1-52)
- **Label** (str): Report custom label
- **Source File** (str): Input data file path
- **Report Output** (str): Excel report output path

#### MCA Report Sections
1. **Summary**: Overall MCA error statistics
2. **Decoder Analysis**: Per-decoder MCA breakdown
3. **Bank Distribution**: MCA errors by bank
4. **Error Patterns**: Common error signatures
5. **Timeline**: MCA occurrences over time

---

## Tool 3: DPMB Bucketer Requests

**Purpose:** Query Intel's DPMB (Data Platform Management Backend) API for bucket data, enabling offline analysis and experiment planning based on historical unit data.

**Color:** Purple (#9b59b6)
**Location:** `api/dpmb.py`
**GUI:** `api/dpmb.py` (dpmbGUI class)

### Features
- Query multiple Visual IDs simultaneously
- Time range filtering (work week based)
- Operation filtering (test types: 8749, 8748, 8657, 7682, etc.)
- Product-specific queries (GNR, GNR3, CWF)
- Export results to JSON/Excel
- Credential-based authentication

### Usage

#### GUI Launch
1. From Tools Hub → Click **DPMB Bucketer Requests**
2. Enter Visual IDs (one per line):
   ```
   D491916S00148
   D491916S00149
   D491916S00150
   ```
3. Configure user credentials:
   - **User**: Intel username (auto-populated with current user)
4. Set time range:
   - **Start Year/WW**: Beginning of data range
   - **End Year/WW**: End of data range
5. Select product: `GNR`, `GNR3`, or `CWF`
6. Choose operations: Multi-select from operation list
7. Click **Submit Request**

#### Parameters
- **VID List** (list): Visual IDs to query
- **User** (str): Intel username for authentication
- **Start Year** (int): Starting year for data range
- **Start WW** (int): Starting work week (1-52)
- **End Year** (int): Ending year for data range
- **End WW** (int): Ending work week (1-52)
- **Product** (str): Product type [`GNR`, `GNR3`, `CWF`]
- **Operations** (list): Operation codes to include

#### API Response Format
```json
{
  "visual_id": "D491916S00148",
  "buckets": [
    {
      "bucket_id": "PPV_WW45_001",
      "operation": "8749",
      "week": 45,
      "year": 2025,
      "status": "PASS",
      "data": {...}
    }
  ]
}
```

#### Programmatic Usage
```python
from PPV.api.dpmb import get_dpmb_data

# Query DPMB for bucket data
results = get_dpmb_data(
    vid_list=['D491916S00148'],
    user='username',
    start_ww=40,
    end_ww=45,
    year=2025,
    product='GNR',
    operations=['8749', '8748']
)
```

---

## Tool 4: File Handler

**Purpose:** Merge or append multiple Excel report files, consolidating data from multiple experiments into unified reports.

**Color:** Orange (#f39c12)
**Location:** `gui/PPVFileHandler.py`
**Utility:** `utils/PPVReportMerger.py`

### Features
- **Merge Mode**: Combine multiple files from folder into single report
- **Append Mode**: Add data from one file to another
- File prefix filtering for targeted merges
- Maintains data integrity and formatting
- Progress tracking with detailed logs

### Usage

#### GUI Launch
1. From Tools Hub → Click **File Handler**
2. Select operation mode:
   - **Merge**: Combine all matching files in folder
   - **Append**: Add one file's data to another
3. Configure based on mode:

**Merge Mode:**
- **Source Folder**: Directory containing files to merge
- **Target File**: Output merged report path
- **File Prefix**: (Optional) Filter files by prefix (e.g., `Summary_`, `Report_`)

**Append Mode:**
- **Source File**: File to append from
- **Target File**: File to append to

4. Click **Execute** to process files

#### Parameters
- **Operation Mode** (str): [`Merge`, `Append`]
- **Source** (str): Folder path (Merge) or File path (Append)
- **Target** (str): Output file path
- **File Prefix** (str): Optional filter for Merge mode

#### Use Cases
- Consolidate weekly experiment reports into monthly summaries
- Merge individual unit reports into fleet-level analysis
- Append new experiment data to ongoing tracking reports
- Combine reports from multiple engineers into unified deliverable

---

## Tool 5: Framework Report Builder

**Purpose:** Generate comprehensive experiment reports from Debug Framework execution logs, providing detailed analysis of test results, VVAR patterns, core data, and failure characterization.

**Color:** Turquoise (#1abc9c)
**Location:** `gui/PPVFrameworkReport.py`
**Parsers:** `parsers/Frameworkparser.py`, `parsers/FrameworkAnalyzer.py`

### Features
- Parse Framework execution folders from network storage
- Multi-experiment analysis with configurable experiment types
- VVAR (Voltage/Ratio Analysis) integration
- Core data extraction (voltage, ratios, physical cores)
- Failing content categorization (EFI/Linux/Python)
- MCA integration for error correlation
- Excel report generation with multiple worksheets
- Experiment summary with key metrics

### Report Worksheets
1. **FrameworkData**: Raw experiment iteration data
2. **ExperimentReport**: Polished summary with key metrics
3. **DragonData**: VVAR analysis for Dragon content (DBM, Pseudo Mesh/Slice)
4. **CoreData**: Core voltage, ratio, and VVAR per core
5. **FrameworkFails**: Detailed failing content categorization
6. **UniqueFails**: Unique failing patterns identified
7. **MCA**: Machine Check Architecture error integration
8. **Summary**: Experiment-level comprehensive summary

### Usage

#### GUI Launch
1. From Tools Hub → Click **Framework Report Builder**
2. Select data source:
   - **Product**: GNR or CWF
   - **Visual ID**: Select from available experiments (auto-populated)
3. Choose save location:
   - **Save Folder**: Output directory for report
4. Configure experiments (middle panel):
   - Each experiment shows: Date, Experiment Name, Type, Status
   - **Type**: Categorize experiment (`Baseline`, `Loops`, `Voltage`, `Frequency`, `Shmoo`, `Invalid`, `Others`)
   - **Content**: Select test content used (`DBM`, `Pseudo Slice`, `Pseudo Mesh`, `TSL`, `Sandstone`, `Imunch`, `EFI`, `Python`, `Linux`, `Other`)
   - **Include**: Enable/disable experiment in report
   - **Custom**: Add custom notes/identifiers
   - **Comments**: Additional commentary
5. Configure options (right panel):
   - **Skip Invalid**: Automatically exclude Invalid experiments
   - **VVAR Options**: Enable VVAR parsing for Dragon content
   - **Core Data**: Enable per-core voltage/ratio extraction
   - **MCA Integration**: Include MCA error analysis
6. Click **Generate Report**

#### Parameters
- **Product** (str): [`GNR`, `CWF`]
- **Visual ID** (str): Framework execution folder identifier
- **Save Folder** (str): Output directory path
- **Experiment Types** (dict): Type assignments per experiment
- **Content Types** (dict): Content assignments per experiment
- **Include Flags** (dict): Experiment inclusion flags
- **Skip Invalid** (bool): Auto-exclude Invalid experiments
- **VVAR Parsing** (bool): Enable VVAR extraction
- **Core Data** (bool): Enable core voltage/ratio parsing
- **MCA Integration** (bool): Include MCA error data

#### Data Source
Framework logs are stored on network server:
```
\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\DebugFramework\{Product}\{Visual_ID}\
```

#### Example Experiment Configuration
| Date | Experiment Name | Type | Content | Include | Custom | Comments |
|------|----------------|------|---------|---------|--------|----------|
| 01/13 | PPV_Loops_WW02 | Loops | Sandstone | ✓ | Loop_v1 | Initial loops |
| 01/14 | Voltage_Sweep_1 | Voltage | DBM | ✓ | V_Sweep | 0.8-1.2V sweep |
| 01/15 | Invalid_Test | Invalid | N/A | ✗ | Skip | Corrupted data |

#### Output Report Structure
```
Report_GNR_D491916S00148_20250115.xlsx
├── FrameworkData (detailed iterations)
├── ExperimentReport (summary metrics)
├── DragonData (VVAR analysis)
├── CoreData (per-core data)
├── FrameworkFails (failing content)
├── UniqueFails (unique patterns)
├── MCA (error integration)
└── Summary (experiment-level overview)
```

---

## Tool 6: Automation Flow Designer

**Purpose:** Visual flow designer for creating test automation sequences, enabling engineers to design complex decision-tree based automation flows with multiple experiments, conditions, and outcomes.

**Color:** Teal (#1abc9c)
**Location:** `gui/AutomationDesigner.py`

### Features
- Visual drag-and-drop flow canvas
- Multiple flow node types:
  - **SingleFailFlowInstance**: Execute until single failure
  - **AllFailFlowInstance**: Execute until all iterations fail
  - **MajorityFailFlowInstance**: Execute until majority fail
  - **AdaptiveFlowInstance**: Adaptive execution based on results
  - **CharacterizationFlowInstance**: Full characterization flow
  - **DataCollectionFlowInstance**: Data collection automation
  - **AnalysisFlowInstance**: Automated analysis flow
- Load experiments from Excel or JSON
- Connection-based flow logic (Pass/Fail branches)
- Unit configuration override
- Export to JSON for Control Panel integration
- INI-style configuration generation

### Flow Node Types

#### SingleFailFlowInstance
Execute experiments iteratively until a single failure is detected.

**Use Case:** Quick failure identification in stable configurations

**Parameters:**
- Experiment selection
- Max iterations
- Pass/Fail branches

#### AllFailFlowInstance
Execute until all iterations of an experiment fail.

**Use Case:** Confirming systematic failures across iterations

**Parameters:**
- Experiment selection
- Iteration count
- Consecutive fail threshold

#### MajorityFailFlowInstance
Execute until majority of iterations fail.

**Use Case:** Statistical characterization with threshold-based decisions

**Parameters:**
- Experiment selection
- Iteration count
- Majority threshold (percentage)

#### AdaptiveFlowInstance
Adaptive execution adjusting parameters based on real-time results.

**Use Case:** Intelligent characterization adapting to unit behavior

**Parameters:**
- Base experiment
- Adaptation rules
- Parameter ranges

#### CharacterizationFlowInstance
Full characterization flow with multiple test phases.

**Use Case:** Comprehensive unit characterization workflows

**Parameters:**
- Test phases
- Phase ordering
- Failure handling

#### DataCollectionFlowInstance
Automated data collection across test configurations.

**Use Case:** Systematic data gathering for analysis

**Parameters:**
- Collection parameters
- Data points
- Storage configuration

#### AnalysisFlowInstance
Automated analysis and decision making.

**Use Case:** Real-time analysis with flow adjustments

**Parameters:**
- Analysis types
- Decision rules
- Branching logic

### Usage

#### GUI Launch
1. From Tools Hub → Click **Automation Flow Designer**
2. Load experiments:
   - Click **Load Experiments**
   - Select Excel or JSON file with experiment definitions
   - File format: Must contain experiment configurations compatible with Control Panel
3. Design flow:
   - Click **Add Node** to create flow nodes
   - Select node type from dropdown
   - Assign experiments to nodes via properties panel
   - Click **Connection Mode** to link nodes
   - Click start node, then end node to create connection
   - Label connections as `Pass` or `Fail`
4. Configure unit settings (optional):
   - **Visual ID**: Override unit identifier
   - **Bucket**: Override bucket assignment
   - **COM Port**: Override serial port
   - **IP Address**: Override network address
   - **600W Unit**: Flag for high-power units
   - **Check Core**: Specify cores to monitor
5. Export flow:
   - Click **Export Flow** to save as JSON
   - Flow file compatible with Control Panel automation

#### Experiment File Format (Excel)
```
| Experiment | Test Name    | Test Mode | Test Type | Product | Loops | ... |
|------------|--------------|-----------|-----------|---------|-------|-----|
| TRUE       | PPV_Loop_001 | Mesh      | Loops     | GNR     | 100   | ... |
| TRUE       | Voltage_001  | Mesh      | Sweep     | GNR     | 50    | ... |
```

#### Experiment File Format (JSON)
```json
[
  {
    "Experiment": true,
    "Test Name": "PPV_Loop_001",
    "Test Mode": "Mesh",
    "Test Type": "Loops",
    "Product": "GNR",
    "Loops": 100
  }
]
```

#### Flow Export Format
```json
{
  "flow_nodes": {
    "node_1": {
      "type": "SingleFailFlowInstance",
      "experiment": "PPV_Loop_001",
      "max_iterations": 100
    },
    "node_2": {
      "type": "CharacterizationFlowInstance",
      "experiments": ["Voltage_001", "Frequency_001"]
    }
  },
  "flow_structure": {
    "node_1": {
      "Pass": "node_2",
      "Fail": "END"
    }
  },
  "unit_config": {
    "Visual ID": "D491916S00148",
    "Bucket": "PPV_WW45",
    "COM Port": 5
  }
}
```

---

## Tool 7: Experiment Builder

**Purpose:** Excel-like interface for creating and editing Control Panel JSON configuration files, providing template-based experiment creation with validation and bulk operations.

**Color:** Teal (#1abc9c)
**Location:** `gui/ExperimentBuilder.py`

### Features
- Excel-like grid interface for experiment editing
- Template-based configuration with product-specific defaults
- Section-organized fields (Status, Basic Info, Unit Data, Test Config, Advanced)
- Data type validation (str, int, float, bool)
- Required field enforcement
- Bulk operations (add/delete multiple experiments)
- Real-time JSON preview
- Import/Export Excel support
- Dropdown options for constrained fields
- Color-coded sections for visual organization

### Field Sections

#### Status
- **Experiment** (bool): Enable/disable experiment

#### Basic Information
- **Test Name** (str): Unique test identifier (required)
- **Test Mode** (str): Execution mode [`Mesh`, `Slice`]
- **Test Type** (str): Test type [`Loops`, `Sweep`, `Shmoo`]

#### Unit Data
- **Product** (str): Product family [`GNR`, `CWF`, `DMR`]
- **Visual ID** (str): Unit identifier
- **Bucket** (str): Assigned bucket
- **COM Port** (int): Serial communication port
- **IP Address** (str): Network address

#### Test Configuration
- **Content** (str): Test content type [`Linux`, `Dragon`, `PYSVConsole`]
- **Test Number** (int): Sequence number
- **Test Time** (int): Timeout in seconds
- **Reset** (bool): Reset before test
- **Loops** (int): Loop iteration count
- **Boot Timeout** (int): Boot timeout in seconds
- **OS Timeout** (int): OS load timeout

#### Advanced Configuration
- **TTL Folder** (str): TTL scripts directory
- **Scripts File** (str): Test scripts file
- **Pass String** (str): Pass detection string
- **Fail String** (str): Fail detection string
- **Postcodes** (str): Expected postcodes
- **Expected Failing Content** (str): Known failures
- **Mask** (str): Configuration mask
- **Defeature** (str): Feature disablement

### Usage

#### GUI Launch
1. From Tools Hub → Click **Experiment Builder**
2. Product selection:
   - Choose product (GNR/CWF/DMR)
   - Template loads with product-specific defaults
3. Add experiments:
   - Click **+ Add Experiment** to create new row
   - Grid displays with sections:
     - Status (yellow)
     - Basic Information (cyan)
     - Unit Data (green)
     - Test Configuration (light blue)
     - Advanced Configuration (pink)
4. Edit experiments:
   - Click cells to edit values
   - Dropdown fields show available options
   - Required fields marked with visual indicators
   - Data validation prevents invalid entries
5. Bulk operations:
   - Select multiple rows (Shift+Click, Ctrl+Click)
   - Click **Delete Selected** to remove
   - Click **Duplicate** to clone experiments
6. Import/Export:
   - **Import Excel**: Load experiments from Excel file
   - **Export Excel**: Save current configuration to Excel
   - **Save JSON**: Generate Control Panel config file
7. Preview:
   - JSON preview pane shows real-time configuration
   - Validation errors highlighted

#### Template Configuration Files
Located in: `PPV/configs/`
- `GNRControlPanelConfig.json`
- `CWFControlPanelConfig.json`
- `DMRControlPanelConfig.json`

#### Keyboard Shortcuts
- **Tab**: Move to next field
- **Shift+Tab**: Move to previous field
- **Enter**: Confirm edit and move down
- **Escape**: Cancel edit
- **Ctrl+C**: Copy selected cells
- **Ctrl+V**: Paste to selected cells
- **Delete**: Clear selected cells

#### Example Workflow
1. Load GNR template
2. Add 10 experiments (bulk add)
3. Set common fields:
   - Product: GNR (all experiments)
   - Visual ID: D491916S00148 (all experiments)
   - Bucket: PPV_WW45 (all experiments)
4. Configure individual tests:
   - Test Names: PPV_Loop_001 through PPV_Loop_010
   - Test Types: Loops (all)
   - Loop counts: 100, 200, 300, ... (varying)
5. Set advanced config for specific tests:
   - Mask: 0x1234 (experiments 5-7)
   - Defeature: Feature_X (experiment 8)
6. Export to JSON for Control Panel

#### Output JSON Format
```json
[
  {
    "Experiment": true,
    "Test Name": "PPV_Loop_001",
    "Test Mode": "Mesh",
    "Test Type": "Loops",
    "Product": "GNR",
    "Visual ID": "D491916S00148",
    "Bucket": "PPV_WW45",
    "COM Port": 5,
    "IP Address": "10.10.10.100",
    "Content": "Linux",
    "Loops": 100,
    "Reset": false
  }
]
```

---

## Tool 8: MCA Single Line Decoder

**Purpose:** Interactive decoder for individual MCA (Machine Check Architecture) register values, supporting multiple decoder types (CHA, LLC, CORE, MEMORY, IO) across GNR/CWF/DMR products.

**Color:** Red (#e74c3c)
**Location:** `gui/MCADecoder.py`
**Decoder Engine:** `Decoder/decoder.py`

### Supported Decoders

#### CHA/CCF Decoder
**Caching Agent / CCF (Coherent Control Fabric)**

Registers:
- MC_STATUS
- MC_ADDR
- MC_MISC
- MC_MISC3

Decoded Fields:
- Error type and severity
- Transaction type
- Address information
- Cache line state
- Core/thread association

#### LLC Decoder
**Last Level Cache**

Registers:
- MC_STATUS
- MC_ADDR
- MC_MISC

Decoded Fields:
- Cache way information
- Set/index
- Error syndrome
- Victim information
- Tag data

#### CORE Decoder
**CPU Core Errors (ML2, DCU, IFU, DTLB, etc.)**

Subtypes:
- **ML2**: Mid-Level Cache (L2)
- **DCU**: Data Cache Unit (L1 Data)
- **IFU**: Instruction Fetch Unit (L1 Instruction)
- **DTLB**: Data Translation Lookaside Buffer
- **L2**: Level 2 Cache
- **BBL**: Bus Block (Front Side Bus)
- **BUS**: System Bus Interface
- **MEC**: Memory Controller Errors
- **AGU**: Address Generation Unit
- **IC**: Instruction Cache

Registers:
- MC_STATUS
- MC_ADDR
- MC_MISC

Decoded Fields (vary by subtype):
- Core ID
- Thread ID
- Error type
- Address information
- Microarchitectural details

#### MEMORY Decoder
**Memory Subsystem (B2CMI, MSE, MCCHAN)**

Subtypes:
- **B2CMI**: B2C Memory Interface
- **MSE**: Memory Scalability Engine
- **MCCHAN**: Memory Controller Channel

Registers:
- MC_STATUS
- MC_ADDR
- MC_MISC

Decoded Fields:
- Channel information
- DIMM/rank/bank
- Memory address
- ECC information
- Transaction type

#### IO Decoder
**IO Subsystem (UBOX, UPI, ULA)**

Subtypes:
- **UBOX**: Uncore Box (System Interface)
- **UPI**: Ultra Path Interconnect
- **ULA**: UPI Link Agent

Registers:
- MC_STATUS
- MC_ADDR
- MC_MISC

Decoded Fields:
- Link information
- IO address
- Error type
- Transaction details

#### FIRST ERROR Decoder
**First Error Logger (UBOX MCERR/IERR)**

Registers:
- MCERRLOGGINGREG
- IERRLOGGINGREG

Decoded Fields:
- First error timestamp
- Error source
- Machine check vs. internal error
- Logging status

### Usage

#### GUI Launch
1. From Tools Hub → Click **MCA Single Line Decoder**
2. Select product: GNR, CWF, or DMR
3. Choose decoder type:
   - CHA/CCF
   - LLC
   - CORE (with subtype)
   - MEMORY (with subtype)
   - IO (with subtype)
   - FIRST ERROR
4. Enter register values:
   - Paste hex values from logs
   - Format: `0x1234567890ABCDEF`
   - Registers displayed based on decoder type
5. Click **Decode** to analyze
6. Review decoded output:
   - Field-by-field breakdown
   - Bit position references
   - Human-readable descriptions
7. Click **Copy Output** to copy results
8. Click **Clear** to reset for next decode

#### Example Decode Session

**Input:**
- Decoder: CHA/CCF
- Product: GNR
- MC_STATUS: `0xBEA00000000C0151`
- MC_ADDR: `0x000000FF12345678`
- MC_MISC: `0x0000000000000086`
- MC_MISC3: `0x0000000000000000`

**Output:**
```
CHA/CCF Decode Results (GNR)
═══════════════════════════════════════

MC_STATUS: 0xBEA00000000C0151
  [63:62] MCACOD: 0b10 - Corrected Error
  [61:57] MSCOD: 0b01111 - Read from remote socket
  [56:53] Error Type: 0b1010 - Data Read Error
  [52:48] Request: 0b10100 - RFO (Read For Ownership)
  [47:40] Channel: 0x00
  [15:0] Model Specific: 0x0151

MC_ADDR: 0x000000FF12345678
  Physical Address: 0x00FF12345678
  Page: 0x00FF12345
  Offset: 0x678

MC_MISC: 0x0000000000000086
  [15:8] Address Mode: Valid
  [7:0] LSB: 0x86

Interpretation:
  Corrected data read error from remote socket
  RFO request to address 0x00FF12345678
  Cache line in Modified state
```

#### Batch Decoding
For multiple MCA entries, use PPV MCA Report Builder (Tool 2) instead of single-line decoder.

---

## Tool 9: Fuse File Generator

**Purpose:** Interactive GUI for selecting, filtering, and generating fuse configuration files from product-specific CSV data sources. Provides comprehensive fuse management with advanced filtering, search capabilities, and product-specific hierarchy generation.

**Color:** Orange (#e67e22)
**Location:** `gui/fusefileui.py`
**Generator Engine:** `utils/fusefilegenerator.py`
**Status Bar Component:** `utils/status_bar.py`

### Supported Products

- **GNR (Granite Rapids)**: Compute and IO fuse hierarchies
- **CWF (Clearwater Forest)**: Compute and IO fuse hierarchies
- **DMR (Diamond Rapids)**: CBB (Base/Top) and IMH fuse hierarchies

### Features

- Load fuse data from product-specific CSV files
- Multi-level filtering system:
  - Pre-filters (Instance, Description, IP)
  - Column-specific filters with wildcard support
  - Quick search across displayed data
- Column selection for customized data views
- Excel-like table interface with sortable columns
- Fuse selection management with viewer window
- Product-specific fuse file generation with IP assignments
- Configuration import/export for reusable setups
- CSV export of filtered/selected fuses
- Real-time fuse value validation

### Fuse Data Structure

#### GNR/CWF CSV Files
Product folders should contain:
- `compute.csv`: Compute fuse definitions
- `io.csv`: IO fuse definitions

#### DMR CSV Files
Product folders should contain:
- `cbbsbase.csv`: CBB base fuse definitions
- `cbbstop.csv`: CBB top/compute fuse definitions
- `imhs.csv`: IMH fuse definitions

### CSV File Location
Default location: `PPV/configs/fuses/<product>/`

Example structure:
```
PPV/
└── configs/
    └── fuses/
        ├── gnr/
        │   ├── compute.csv
        │   └── io.csv
        ├── cwf/
        │   ├── compute.csv
        │   └── io.csv
        └── dmr/
            ├── cbbsbase.csv
            ├── cbbstop.csv
            └── imhs.csv
```

### Product-Specific Hierarchies

#### GNR/CWF Hierarchy Patterns
```
sv.socket{socket}.compute{compute}.fuses   # Individual compute
sv.socket{socket}.io{io}.fuses              # Individual IO
sv.sockets.computes.fuses                   # All computes
sv.sockets.ios.fuses                        # All IOs
```

#### DMR Hierarchy Patterns
```
sv.socket{socket}.cbb{cbb}.base.fuses           # CBB base
sv.socket{socket}.cbb{cbb}.compute{compute}.fuses  # CBB top
sv.socket{socket}.imh{imh}.fuses                # IMH
sv.sockets.cbbs.base.fuses                      # All CBBs base
sv.sockets.cbbs.computes.fuses                  # All CBBs top
sv.sockets.imhs.fuses                           # All IMHs
```

### Usage

#### GUI Launch
1. From Tools Hub → Click **Fuse File Generator**
2. Select product from dropdown (GNR, CWF, or DMR)
3. Configure fuse file location (auto-detected: `configs/fuses/`)
4. Click **📁** to browse custom location if needed

#### Data Loading and Filtering
1. Click **⚙️ Configure Filters** to set pre-filters:
   - **Instance**: Filter by fuse instance name
   - **Description**: Filter by fuse description
   - **IP**: Filter by IP origin (COMPUTE, IO, CBB, IMH)
   - Supports wildcards: `*text*` (contains), `text*` (starts with), `*text` (ends with)

2. Click **📋 Select Columns** to choose display columns:
   - Default columns: `original_name`, `Instance`, `description`, `VF_Name`, `IP_Origin`
   - Additional columns from CSV: `fuse_width`, `numbits`, `reset_value`, etc.
   - Select/deselect checkboxes and click **Apply**

3. Click **🔄 Apply & Show Data** to load and display filtered fuses

#### Column-Specific Filtering
1. **Click on any column header** to open column filter dialog
2. Filter options:
   - **Contains**: Text matching
   - **Starts With**: Prefix matching
   - **Ends With**: Suffix matching
   - **Exact Match**: Precise value matching
3. Sort ascending/descending
4. Active filters show **🔽** indicator in column header

#### Selection Management
1. **Select fuses** in table (click rows, Ctrl+Click, Shift+Click)
2. Click **Add Highlighted to Selection** (Ctrl+A) to add to selection pool
3. Click **View Selection** (Ctrl+S) to open Selection Viewer window
4. In Selection Viewer:
   - **Select All**: Select all fuses
   - **Clear All**: Clear all selections
   - **Select Filtered**: Select only filtered fuses
   - **Clear Filtered**: Clear filtered fuses
   - **Remove from Selection**: Remove selected items from pool

#### Fuse File Generation
1. Click **Generate Fuse File** with selected fuses
2. Configure IP assignments:
   - **GNR/CWF**: Select sockets, computes, IOs
   - **DMR**: Select sockets, CBBs, CBB-computes, IMHs
3. Click **Generate List** to create socket+IP+fuse combinations
4. Configure fuse values:
   - **Double-click** cells to edit values inline
   - **Apply to All**: Set value for all rows
   - **Apply to Selected**: Set value for selected rows
   - Validation checks fuse width and bit limits
5. Click **Generate Fuse File** and select output location

#### Configuration Management

**Export Configuration:**
1. Click **Export Config** after setting up filters and selections
2. Save as `.json` file with:
   - Active filters (pre-filters and column filters)
   - Display columns
   - Selected fuse IDs
3. Use for repeatable workflows

**Import Configuration:**
1. Click **Import Config** to load saved `.json`
2. Validates configuration structure
3. Verifies fuse IDs exist in current dataset
4. Shows validation errors if issues found
5. Applies filters and restores selections

#### CSV Export
1. Apply desired filters
2. Click **Export to CSV**
3. Choose output location
4. Exports currently filtered data with selected columns

### Parameters

**Configuration:**
- **Product** (str): Target product [`GNR`, `CWF`, `DMR`]
- **Fuse Location** (str): Path to fuses folder (default: auto-detected)

**Pre-Filters:**
- **Instance** (str): Filter by instance name with wildcard support
- **Description** (str): Filter by description with wildcard support
- **IP** (str): Filter by IP origin [`COMPUTE`, `IO`, `CBB`, `IMH`]

**Display Configuration:**
- **Columns** (list): Selected columns to display
- **Column Filters** (dict): Per-column filter values

**Fuse Values:**
- Supported formats: Hexadecimal (`0x1A`), Decimal (`26`), Binary (`0b11010`)
- Validation against fuse width and numbits

### Output Format

Generated `.fuse` file structure:
```
# Fuse configuration file for GNR
# Generated by PPV Engineering Tools - Fuse File Generator
# Total fuses: 25
#
# This file is compatible with fusefilegen.py

[sv.socket0.compute0.fuses]
fuse_name_1 = 0x1
fuse_name_2 = 0xFF
fuse_name_3 = 0x0

[sv.socket0.io0.fuses]
fuse_name_4 = 0x2A
fuse_name_5 = 0x1F

[sv.sockets.computes.fuses]
fuse_name_global = 0xAB
```

### Programmatic Usage

```python
from PPV.utils.fusefilegenerator import FuseFileGenerator, load_product_fuses

# Load fuses for a product
generator = load_product_fuses('GNR')

# Get statistics
stats = generator.get_statistics()
print(f"Total fuses: {stats['total_fuses']}")
print(f"IP Origins: {stats['ip_origins']}")

# Search fuses
results = generator.search_fuses('voltage', ['description', 'original_name'])
print(f"Found {len(results)} matching fuses")

# Filter fuses with wildcards
filtered = generator.filter_fuses({
    'IP_Origin': 'COMPUTE',
    'description': '*voltage*'
})

# Get unique values for a column
unique_ips = generator.get_column_unique_values('IP_Origin')

# Export filtered results
generator.export_to_csv(filtered, 'output/filtered_fuses.csv')

# Generate fuse file
ip_assignments = {
    'compute0': {'fuse_name_1': '0x1', 'fuse_name_2': '0xFF'},
    'io0': {'fuse_name_4': '0x2A'}
}
generator.generate_fuse_file(filtered, ip_assignments, 'output/fuses.fuse')
```

### Validation Functions

**Fuse Value Validation:**
```python
from PPV.utils.fusefilegenerator import validate_fuse_value

# Validate value fits within bit width
is_valid = validate_fuse_value('0xFF', fuse_width=8, numbits=8)  # True
is_valid = validate_fuse_value('0x1FF', fuse_width=8, numbits=8)  # False (exceeds 8 bits)
is_valid = validate_fuse_value('256', fuse_width=8)  # False (256 requires 9 bits)
```

### Use Cases

1. **Fuse Configuration Generation**: Create product-specific fuse files for silicon bring-up
2. **Fuse Analysis**: Search and filter fuses by description, instance, or IP
3. **Documentation**: Export filtered fuse lists as CSV for reference
4. **Configuration Reuse**: Save/load filter configurations for repeatable workflows
5. **Multi-IP Assignment**: Configure same fuses across multiple IPs (compute, IO, CBB, IMH)
6. **Validation**: Verify fuse values fit within specified bit widths before generation

### Tips and Best Practices

- **Start with Pre-Filters**: Use Instance/Description/IP pre-filters to reduce dataset before column filtering
- **Column Filters for Precision**: Use column-specific filters for exact value matching
- **Save Configurations**: Export configurations for frequently-used filter combinations
- **Validate Before Generate**: Tool validates fuse values against bit widths automatically
- **Use Wildcards**: Leverage `*` wildcards for flexible text matching
- **Selection Viewer**: Use dedicated Selection Viewer for managing large fuse selections
- **Export Intermediate Results**: Export filtered CSVs for review before generating .fuse files

---

## Integration Workflows

### Workflow 1: Complete Debug Cycle

1. **DPMB Request** → Query historical bucket data for unit
2. **MCA Report Builder** → Generate MCA analysis from Bucketer data
3. **MCA Decoder** → Deep-dive decode specific MCA errors
4. **Experiment Builder** → Create targeted experiments based on findings
5. **Automation Designer** → Design characterization flow
6. **Control Panel** → Execute automation flow (external tool)
7. **Framework Report Builder** → Analyze execution results
8. **File Handler** → Consolidate reports across multiple runs

### Workflow 2: Loop Analysis

1. **Control Panel** → Execute loop experiments (external)
2. **PTC Loop Parser** → Parse loop data
3. **Framework Report Builder** → Detailed experiment analysis
4. **File Handler** → Merge weekly loop reports

### Workflow 3: Offline Characterization Planning

1. **DPMB Request** → Download historical data
2. **MCA Report Builder** → Identify failure patterns
3. **Experiment Builder** → Configure targeted tests
4. **Export JSON** → Load to Control Panel for execution

### Workflow 4: Fuse Configuration Generation

1. **Fuse File Generator** → Load product-specific fuse CSVs
2. **Apply Filters** → Filter by instance, description, or IP origin
3. **Select Fuses** → Choose relevant fuses for configuration
4. **Configure IP Assignments** → Set socket and IP mappings (compute, IO, CBB, IMH)
5. **Assign Values** → Set fuse values with validation
6. **Generate .fuse File** → Export for fusefilegen.py tool
7. **Export Configuration** → Save filter/selection setup for reuse

---

## Best Practices

### Report Organization
- Use consistent naming: `{Product}_{Type}_{VisualID}_{Date}.xlsx`
- Archive reports by work week
- Maintain separate folders for raw data and processed reports

### Experiment Configuration
- Start with template configurations
- Validate JSON before Control Panel import
- Document custom configurations in Comments field
- Use version control for experiment files

### MCA Analysis
- Cross-reference MCA Report with Single Line Decoder for deep analysis
- Track MCA patterns across weeks
- Correlate MCA with experiment types

### Automation Design
- Test individual experiments before adding to flows
- Document flow logic in node descriptions
- Export flows as JSON backups
- Version control automation flows

### Data Management
- Use File Handler for regular consolidation
- Maintain source data separately from merged reports
- Document merge operations in report metadata

---

## Troubleshooting

### Issue: Tools don't launch from Hub
**Solution:** Verify Python environment and package dependencies
```bash
pip install --upgrade pandas openpyxl tabulate requests tkinter
```

### Issue: DPMB authentication fails
**Solution:** Verify network connectivity and Intel credentials
- Ensure access to `dpmb-api.intel.com`
- Check credentials with SSO

### Issue: Framework Report Builder can't find Visual ID
**Solution:** Verify network path access
```
\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\DebugFramework\
```
Check VPN connection and network permissions

### Issue: MCA Decoder returns "Unknown Register"
**Solution:** Verify register format
- Use hex format: `0x1234567890ABCDEF`
- No spaces or special characters
- 16-character hex value (excluding 0x prefix)

### Issue: Experiment Builder JSON invalid
**Solution:** Check required fields
- Test Name (required)
- Product (required)
- Experiment status (required)
- Validate with JSON linter before export

### Issue: File Handler merge fails
**Solution:** Verify file formats match
- All files must be Excel (.xlsx)
- Column headers must match
- Check for corrupted files

### Issue: Fuse File Generator CSV files not found
**Solution:** Verify fuse folder structure and location
- Check product folder exists: `PPV/configs/fuses/<product>/`
- GNR/CWF: Ensure `compute.csv` and `io.csv` exist
- DMR: Ensure `cbbsbase.csv`, `cbbstop.csv`, `imhs.csv` exist
- Browse to custom location if using non-standard paths

### Issue: Fuse value validation fails
**Solution:** Check value format and bit width
- Use proper format: `0x1A` (hex), `26` (decimal), or `0b11010` (binary)
- Verify value fits within fuse's bit width
- Example: For 8-bit fuse, max value is 0xFF (255)

---

## Advanced Topics

### Custom MCA Decoders
Extend decoder support by editing `Decoder/decoder.py`:
```python
def decode_custom_mca(status, addr, misc):
    """Custom decoder implementation"""
    fields = extract_bits(status, [(63, 62), (61, 57)])
    return format_decode_output(fields)
```

### Batch Processing
Automate report generation:
```python
from PPV.parsers.MCAparser import ppv_report

# Batch process multiple buckets
buckets = ['PPV_WW45_001', 'PPV_WW45_002', 'PPV_WW45_003']
for bucket in buckets:
    ppv_report(
        mode='Bucketer',
        product='GNR',
        bucket_file=f'data/{bucket}.xlsx',
        output=f'reports/{bucket}_report.xlsx'
    )
```

### API Integration
Use DPMB API programmatically:
```python
from PPV.api.dpmb import dpmbAPI

# Initialize API client
client = dpmbAPI(user='username')

# Query data
results = client.query(
    vids=['D491916S00148'],
    start_ww=40,
    end_ww=45,
    product='GNR'
)

# Process results
for vid_data in results:
    print(f"VID: {vid_data['visual_id']}")
    print(f"Buckets: {len(vid_data['buckets'])}")
```

---

## Appendix A: File Locations

### GUI Modules
```
PPV/gui/
├── PPVTools.py              # Main Tools Hub
├── PPVLoopChecks.py         # PTC Loop Parser
├── PPVDataChecks.py         # MCA Report Builder
├── PPVFileHandler.py        # File Handler
├── PPVFrameworkReport.py    # Framework Report Builder
├── AutomationDesigner.py    # Automation Flow Designer
├── ExperimentBuilder.py     # Experiment Builder
├── MCADecoder.py            # MCA Single Line Decoder
├── fusefileui.py            # Fuse File Generator
└── ProductSelector.py       # Product Selection Dialog
```

### Parsers
```
PPV/parsers/
├── MCAparser.py             # MCA parsing engine
├── PPVLoopsParser.py        # Loop data parser
├── Frameworkparser.py       # Framework log parser
├── FrameworkAnalyzer.py     # Experiment analysis
└── OverviewAnalyzer.py      # Summary generation
```

### Decoders
```
PPV/Decoder/
├── decoder.py               # Main decoder engine
├── GNR_decoders.py          # GNR-specific decoders
├── CWF_decoders.py          # CWF-specific decoders
└── DMR_decoders.py          # DMR-specific decoders
```

### API
```
PPV/api/
└── dpmb.py                  # DPMB API client
```

### Utilities
```
PPV/utils/
├── PPVReportMerger.py       # Report merge/append
├── ExcelReports.py          # Excel generation
├── fusefilegenerator.py     # Fuse file generator engine
├── status_bar.py            # Status bar component
└── FileFixes.py             # File repair utilities
```

---

## Appendix B: Configuration Templates

### GNR Control Panel Config
```json
{
  "field_configs": {
    "Experiment": {"section": "Status", "type": "bool", "default": true},
    "Test Name": {"section": "Basic Information", "type": "str", "required": true},
    "Product": {"section": "Unit Data", "type": "str", "default": "GNR"}
  }
}
```

### Automation Flow Template
```json
{
  "flow_nodes": {
    "START": {"type": "StartNode"},
    "node_1": {"type": "SingleFailFlowInstance", "experiment": "test_001"},
    "END": {"type": "EndNode"}
  },
  "flow_structure": {
    "START": {"next": "node_1"},
    "node_1": {"Pass": "END", "Fail": "END"}
  }
}
```

### Fuse File Generator Configuration Template
```json
{
  "product": "GNR",
  "pre_filters": {
    "instance": "*voltage*",
    "description": "*ratio*",
    "ip": "COMPUTE"
  },
  "display_columns": [
    "original_name",
    "Instance",
    "description",
    "VF_Name",
    "IP_Origin",
    "fuse_width",
    "numbits"
  ],
  "column_filters": {
    "IP_Origin": "COMPUTE"
  },
  "selected_fuses": [
    "fuse_id_1",
    "fuse_id_2",
    "fuse_id_3"
  ]
}
```

---

## 📧 Support and Contact

**Maintainer:** Gabriel Espinoza
**Email:** gabriel.espinoza.ballestero@intel.com
**Organization:** Intel Corporation - Test & Validation
**Framework:** THR Debug Tools v2.0
**Release Date:** January 15, 2026

**For Technical Support:**
- Questions, issues, or clarifications: Contact maintainer via email
- Bug reports: Include framework version, product (GNR/CWF/DMR), tool used, and full error logs
- Feature requests: Provide detailed use case description and business justification
- Documentation feedback: Report errors, suggest improvements, or request additional examples

**Related Documentation:**
- Quick Start Guide: [THR_DEBUG_TOOLS_QUICK_START.md](THR_DEBUG_TOOLS_QUICK_START.md)
- Workflow Integration: [THR_DEBUG_TOOLS_FLOWS.md](THR_DEBUG_TOOLS_FLOWS.md)
- Interactive Examples: [THR_DEBUG_TOOLS_EXAMPLES.ipynb](THR_DEBUG_TOOLS_EXAMPLES.ipynb)
- Main Documentation Index: [../README.md](THR_DOCUMENTATION_README.md)

**Repository Location:** `c:\Git\Automation\PPV\`
**Documentation Location:** `c:\Git\Automation\S2T\DOCUMENTATION\`

---

**© 2026 Intel Corporation. Intel Confidential.**
- **Repository:** `c:\Git\Automation\PPV\`
- **Documentation:** `c:\Git\Automation\S2T\DOCUMENTATION\`
- **Internal Wiki:** [THR Debug Tools Confluence](https://confluence.intel.com/thr-debug-tools)

**Version:** 2.0
**Last Updated:** January 2025
**Maintainer:** THR Characterization Team
