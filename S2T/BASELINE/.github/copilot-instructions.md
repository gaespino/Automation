# System-to-Tester (S2T) Debug Framework AI Coding Guide

## Architecture Overview

This is a hardware testing and debugging framework for semiconductor validation with two main components:
- **S2T/**: Core system-to-tester communication, hardware control, and test execution
- **DebugFramework/**: UI, automation, file handling, and test orchestration

### Key Components
- `SystemDebug.py`: Main framework entry point, hardware interface manager
- `CoreManipulation.py`: Core/slice masking, boot control, fuse management  
- `AutomationFlows.py`: Test orchestration and experiment management
- `FileHandler.py`: Logging, file operations, Excel template processing
- `TestMocks.py`: Mock system for safe testing without hardware

## Critical Development Workflows

### Running the System
```python
# Production mode (requires hardware)
import SystemDebug as gdf
gdf.ControlPanel()  # Main UI
gdf.AutomationPanel()  # Automation interface

# Test mode (no hardware required)
import TestFramework
TestFramework.run_control_panel_test()  # Mock environment
TestFramework.run_automation_panel_test()  # Framework UI testing

# NEW: S2T Functions Direct Testing (no UI)
TestFramework.run_s2t_function_test("GNR")  # Direct S2T capability testing
```

### Mock-First Development
**Always import mocks BEFORE framework modules** to avoid hardware dependencies:
```python
import TestMocks  # Must be first
TestMocks.setup_all_mocks()  # Essential for testing
# Then import framework modules
```

## Project-Specific Patterns

### Configuration System
- JSON files in root: `mock_s2t_config.json`, `test_experiments.json`, `mock_masks.json`
- Excel templates: `ExperimentsTemplate*.xlsx` for test definitions
- S2T_CONFIGURATION dict in `AutomationFlows.py` for hardware timing parameters

### Threading Architecture
- `ExecutionHandler/utils/ThreadsHandler.py`: Central thread management
- `ExecutionCommand` enum for thread communication
- `execution_state` global for status tracking
- UI components use `ThreadHandler` classes for non-blocking operations

### Status Management
- `StatusUpdateManager`: Real-time status broadcasts
- `IStatusReporter` interface: Standardized status reporting
- `TestStatus` enum in `ExecutionHandler/Enums.py` for test states

### File Organization
- Version-controlled backups: `__old_version_*` directories (ignore for active development)
- Active code: `DebugFramework/` and `S2T/` only
- Logs: `debug_logs/` and `C:\SystemDebug\Logs\`
- Templates: `TTL/` (Tera Term macros), `Shmoos/` (test patterns)

## Integration Points

### Hardware Communication
- `ipccli`: Primary hardware interface (Intel Platform Controller)
- `namednodes`: Hardware node access
- `toolext.bootscript.boot`: Boot sequence control
- Serial connections via `SerialConnection.py`

### External Dependencies
- Excel: `openpyxl`, `pandas` for template processing
- UI: Custom tkinter-based panels (not standard frameworks)
- Database: `Storage_Handler.DBHandler` (active, with optional disable for testing)
- Intel Hardware: `ipccli`, `namednodes` (require mocking for development)

## Testing Strategy

### Mock System Architecture
`TestMocks.py` provides comprehensive mocking:
- `MockFrameworkLogger`: Replaces hardware logging
- `MockFileHandler`: Safe file operations
- Hardware interfaces mocked to prevent actual hardware calls
- **Intel Hardware Mocking**: `ipccli` and `namednodes` require register-level mocking for development without hardware access
- Database operations can be disabled via configuration for testing scenarios

### Test Types & Execution
The framework supports three main test categories:
- **Loops**: Repetitive test execution for stability validation
- **Sweep**: Parameter sweeps (voltage, frequency, etc.) for characterization
- **Shmoo**: 2D parameter mapping for operational boundaries

```python
# Framework UI tests (safe)
python DebugFramework/UI/TestRunControlPanel.py

# Framework integration tests (requires setup)
python TestRun.py

# NEW: S2T Function tests (direct S2T capability testing)
python DebugFramework/S2TTestFramework.py
import S2TTestFramework
S2TTestFramework.test_gnr_s2t()  # Test GNR S2T functions
S2TTestFramework.test_cwf_s2t()  # Test CWF S2T functions

# Test type definitions in ExecutionHandler/Enums.py:
# TestType.LOOPS, TestType.SWEEP, TestType.SHMOO
```

## Critical Conventions

### Error Handling
- Use `xformat(e)` from `s2tutils.formatException()` for consistent error formatting
- `ExecutionHandler/Exceptions.py` defines framework-specific exceptions
- Always log to both console and file via `FrameworkLogger`

### Configuration Loading
- Use `ConfigsLoader.py` for product-specific configurations  
- `FileHandler.load_configuration()` for JSON configs
- Excel templates loaded via pandas with specific sheet structures

### Path Management
- Absolute paths required for file operations
- `script_dir = os.path.dirname(os.path.abspath(__file__))` pattern
- Base folder typically `C:\SystemDebug` for logs and outputs

## Development Guidelines

1. **Always use test mode** for initial development and debugging
2. **Import mocks first** in any new modules that interact with hardware
3. **Use interfaces** (`Interfaces/IFramework.py`) for new components requiring dependency injection
4. **Follow enum patterns** from `ExecutionHandler/Enums.py` for type safety
5. **Implement `IStatusReporter`** for components that need UI updates
6. **Version naming**: Use `__old_version_*` pattern for backups, not git branches

## Deployment Considerations

### Suggested Deployment Patterns
Based on the current architecture, consider these deployment approaches:

1. **Containerized Development Environment**
   - Docker containers with mocked Intel hardware interfaces
   - Pre-configured Python environment with all dependencies
   - Shared volume mounts for logs and test results

2. **Staged Deployment Pipeline**
   - **Dev Stage**: Full mocking, no hardware dependencies
   - **Integration Stage**: Limited hardware access for validation
   - **Production Stage**: Full hardware integration

3. **Configuration Management**
   - Environment-specific JSON configs (`dev_config.json`, `prod_config.json`)
   - Hardware availability detection and automatic mock switching
   - Database connection pooling for production environments

### Hardware Register Mocking Strategy
For `ipccli` and `namednodes` emulation, implement:
- Register read/write simulation with realistic timing delays  
- State persistence across mock sessions
- Configurable register maps for different hardware variants
- Error injection capabilities for robustness testing

#### Key Register Patterns Discovered:
- **SV Structure**: `sv.socket0.computes.name`, `sv.socket0.ios.name`, `sv.socket0.target_info`
- **IPC Commands**: `ipc.resettarget()`, `ipc.unlock()`, `ipc.forcereconfig()`, `ipc.go()`, `ipc.islocked()`
- **Critical Registers**: 
  - `sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg` (boot control)
  - `sv.socket0.pcudata.fused_ia_core_disable_*` (core masking)
  - `sv.socket0.computes.fuses.*_core_disable` (fuse settings)
  - VP2INTERSECT fuse controls for instruction set features

#### Comprehensive Register Categories Found in JSON configs:
- **Frequency Control**: SST performance profiles, CFC/IA/IO ratios, turbo limits
- **Power Management**: Burn-in voltages, power-down overrides, C-state counters  
- **Core Configuration**: Architecture fuses, test modes, debug registers
- **Instruction Sets**: AVX2/AVX512/SSE ratios, VP2INTERSECT controls
- **Debug/Test**: TAP registers, state dump devices, allocation controls
- **Product-Specific**: Different register sets for GNR vs CWF architectures

#### Mock Dictionary Structure:
```python
REGISTER_MAPS = {
    'GNR': {...},   # 80+ registers from JSON configs
    'CWF': {...},   # CWF-specific variants
    'DMR': {...}    # New product (to be added)
}
```

#### JSON Configuration Files:
- `S2T/product_specific/{product}/RegFiles/s2tregdata.json` - Core register definitions
- `S2T/product_specific/{product}/RegFiles/s2tmeshdata.json` - Mesh/cache registers  
- `S2T/product_specific/{product}/ConfigFiles/*FuseFileConfigs.json` - Frequency/fuse mappings
- `S2T/product_specific/{product}/ConfigFiles/*BurnInFuses.json` - Voltage test levels

## Entry Points for New Development

- **UI Extensions**: Extend classes in `UI/ControlPanel.py`
- **New Test Types**: Add to `ExecutionHandler/Enums.py`, implement in automation flows
- **Hardware Interfaces**: Implement `ISystemController` from interfaces
- **File Processing**: Extend `FileHandler.py` methods
- **Mock Extensions**: Add to `TestMocks.py` for new hardware interactions