# DMR Testing & Validation Framework
## Focused 1-Hour Presentation

**Target Audience:** Validation Engineers, Test Development Teams
**Duration:** 60 minutes
**Presenter:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)
**Date:** January 2026
**Classification:** Intel Confidential

---

## Slide 1: Title Slide

**Title:** DMR Testing & Validation Framework
**Subtitle:** Key Tools for Characterization & Debug

**Focus Areas:**
- DebugFramework: 5 Core GUI Tools
- THR Debug Tools: 3 Essential Builders
- Practical Workflows & Live Demo

**Visual:** Intel logo, DMR chip diagram

---

## Slide 2: Agenda

**60-Minute Session:**

1. **Framework Overview** (5 min) - Architecture & entry point
2. **System2Tester Setup** (5 min) - S2T configuration
3. **ControlPanel & AutomationPanel** (10 min) - Test execution interfaces
4. **MeshQuickTest & SliceQuickTest** (8 min) - Core/slice manipulation
5. **THR Debug Tools** (12 min) - Experiments, Automation, Framework Report
6. **Live Demonstrations** (15 min) - Tool walkthroughs
7. **Q&A & Wrap-up** (5 min)

---

## Slide 3: Framework Entry Point

**Getting Started**

```python
# DebugFramework - Test execution interfaces
import users.THR.dmr_debug_utilities.DebugFramework.SystemDebug as sd

# System-to-Tester - S2T configuration
import users.THR.dmr_debug_utilities.S2T.SetTesterRegs as s2t

# Launch interfaces:
sd.ControlPanel()         # Manual test execution
sd.AutomationPanel()      # Automated test execution

# S2T Tools:
s2t.setupSystemAsTester() # S2T configuration
s2t.MeshQuickTest()       # Full chip testing
s2t.SliceQuickTest()      # Targeted core testing
```

**Repository:** `c:\Git\Automation\S2T\BASELINE_DMR\`

---

## Slide 4: System2Tester Overview

**What is System-to-Tester (S2T)?**

S2T brings ATE-style testing to system environment:
- 🎯 Precise voltage/frequency control per core
- 📊 Real-time MCA logging and error capture
- 🔄 Automated sweep capabilities
- ⚡ Sub-boot and sub-OS testing

**Key Benefits:**
- Early silicon characterization before OS boot
- Isolated core/slice testing
- Production-like test patterns in system
- Rapid failure isolation

---

## Slide 5: setupSystemAsTester() - S2T Configuration

**Launch S2T Setup GUI:**

```python
import users.THR.dmr_debug_utilities.S2T.SetTesterRegs as s2t
s2t.setupSystemAsTester()
```

**Configuration Steps:**
1. **BIOS Settings** - Set required knobs for S2T mode
2. **Tester Configuration** - Socket, core masks, voltage limits
3. **Serial Connection** - Configure debug serial port
4. **Safety Limits** - Max voltage, temperature thresholds
5. **Test Environment** - Initialize hardware and validate

**Output:** System ready for characterization with S2T enabled

---

## Slide 6: ControlPanel - Manual Test Execution

**Purpose:** Interactive test execution and configuration

**Launch:**
```python
import users.THR.dmr_debug_utilities.DebugFramework.SystemDebug as sd
sd.ControlPanel()
```

**Key Features:**
- 📝 Test configuration form (voltage, frequency, duration)
- 🎯 Core/slice selection dropdown
- ⚙️ Real-time parameter adjustment
- ▶️ Execute button for single test runs
- 📊 Live status updates (pass/fail/running)
- 📁 Result saving and export

**Common Use Cases:**
- Quick unit validation
- Interactive debug sessions
- Ad-hoc test execution
- Parameter tuning

**Visual:** Screenshot showing test configuration panel

---

## Slide 7: AutomationPanel - Automated Test Flows

**Purpose:** Multi-test sequencing and batch execution

**Launch:**
```python
import users.THR.dmr_debug_utilities.DebugFramework.SystemDebug as sd
sd.AutomationPanel()
```

**Key Features:**
- 🔄 Test sequence builder (drag & drop)
- 📋 Pre-configured test templates
- ⏱️ Scheduling and loop controls
- 📊 Batch execution across cores/sockets
- 📈 Aggregate reporting
- 💾 Flow save/load

**Workflow Examples:**
- Overnight voltage sweeps on all cores
- Multi-socket characterization
- Stress test campaigns (1000s of iterations)
- Automated regression testing

**Visual:** AutomationPanel with flow diagram

---

---

## Slide 8: MeshQuickTest - Full Chip Testing

**Purpose:** Rapid full-chip S2T validation

**Launch:**
```python
import users.THR.dmr_debug_utilities.S2T.SetTesterRegs as s2t
s2t.MeshQuickTest()
```

**Key Features:**
- ✅ All cores enabled by default
- 🎯 Socket selection (0, 1, or both)
- ⚙️ Mesh test pattern configuration
- 🔌 One-click S2T enable/disable
- 📊 Quick health check validation

**Use Cases:**
- Initial unit bring-up
- Full-chip health check after BIOS update
- Production validation
- Quick verification after hardware fix

**Visual:** MeshQuickTest interface with "Enable All Cores" button

---

## Slide 9: SliceQuickTest - Targeted Core Testing

**Purpose:** Granular core/slice-level control

**Launch:**
```python
import users.THR.dmr_debug_utilities.S2T.SetTesterRegs as s2t
s2t.SliceQuickTest()
```

**Key Features:**
- 🎯 Individual core selection (visual grid)
- 📊 Slice-level enable/disable
- ⚡ Reduced power consumption
- 🔍 Isolated failure debug
- 💾 Mask save/load templates

**Configuration:**
- Select specific cores for testing
- Enable/disable slices within cores
- Apply saved masks from characterization data
- Set per-core voltage/frequency

**Use Cases:**
- Debug specific failing cores
- Characterize individual slices
- Power optimization testing
- Targeted stress testing

**Visual:** SliceQuickTest with core grid and selection controls

---

## Slide 10: THR Debug Tools Overview

**Integrated Test Automation Tools**

**What are THR Debug Tools?**
- Suite of 8 GUI tools for unit characterization
- Built on DebugFramework foundation
- Focus on automation, experiments, and reporting

**Today's Focus - 3 Essential Tools:**

| Tool | Purpose | Key Benefit |
|------|---------|-------------|
| **Experiments Builder** | Design test matrices | Systematic coverage |
| **Automation Flow Designer** | Build complex workflows | Unattended execution |
| **Framework Report Builder** | Generate analysis reports | Data insights |

**Launch:** `python c:\Git\Automation\PPV\run.py`

---

## Slide 11: Experiments Builder

**Purpose:** Design comprehensive test matrices

**Launch from Tools Hub:**
```python
from PPV.run import launch_experiments_builder
launch_experiments_builder()
```

**Key Features:**
- 📊 Multi-dimensional experiment design
- 🎯 Voltage/frequency/core matrix builder
- 📋 CSV export for automation
- 🔄 Template save/load
- 📈 Coverage analysis

**Example Experiment:**
- **Variables:** Voltage (0.60-0.85V), Frequency (1.8-2.6 GHz), Cores (0-15)
- **Matrix:** 13 voltages × 9 frequencies × 16 cores = 1,872 test points
- **Output:** experiment_matrix.csv

**Visual:** Experiments Builder showing matrix configuration

---

## Slide 12: Automation Flow Designer

**Purpose:** Build complex multi-stage test workflows

**Launch from Tools Hub:**
```python
from PPV.run import launch_automation_designer
launch_automation_designer()
```

**Key Features:**
- 🎨 Visual flow builder (drag & drop nodes)
- 🔄 Loops, conditionals, error handling
- 📊 CSV input integration
- ⏱️ Scheduling and timing controls
- 💾 Flow save/load (JSON format)
- 📁 Result aggregation

**Node Types:**
- Test execution nodes
- Data collection nodes
- Analysis nodes
- Conditional branching
- Email/notification nodes

**Visual:** Automation Flow Designer with sample flow

---

## Slide 13: Framework Report Builder

**Purpose:** Generate comprehensive analysis reports

**Launch from Tools Hub:**
```python
from PPV.run import launch_framework_report
launch_framework_report()
```

**Key Features:**
- 📊 Multi-source data aggregation
- 📈 Automated chart generation (pass/fail, Shmoo plots)
- 📋 Customizable report templates
- 🔍 Failure analysis summaries
- 📁 HTML/PDF export
- 📧 Email distribution

**Report Sections:**
1. Executive Summary (pass rates, key findings)
2. Test Configuration Details
3. Per-Core Results Tables
4. Shmoo Plots (voltage vs frequency)
5. MCA Error Analysis
6. Failure Mode Distribution
7. Recommendations

**Visual:** Framework Report Builder showing template selection

---

## Slide 14: Key Takeaways

**What You Learned:**

**DebugFramework (5 Tools):**
- ✅ `setupSystemAsTester()` - S2T configuration
- ✅ `ControlPanel()` - Interactive test execution
- ✅ `AutomationPanel()` - Multi-test sequencing
- ✅ `MeshQuickTest()` - Full-chip validation
- ✅ `SliceQuickTest()` - Targeted core testing

**THR Debug Tools (3 Builders):**
- ✅ **Experiments Builder** - Design test matrices
- ✅ **Automation Flow Designer** - Complex workflows
- ✅ **Framework Report Builder** - Analysis reports

**Power Combo:** Design → Automate → Analyze

---

## Slide 15: Live Demonstrations

**Demo 1: ControlPanel - Quick Test Execution (3 min)**
- Open ControlPanel GUI
- Configure voltage sweep (0.65V - 0.80V on Core 4)
- Execute and view real-time results
- Export to CSV

**Demo 2: Experiments Builder - Matrix Design (3 min)**
- Open Experiments Builder
- Create multi-variable experiment (voltage × cores)
- Preview matrix (64 test points)
- Export CSV for automation

**Demo 3: Automation Flow Designer - Build Workflow (4 min)**
- Open Automation Flow Designer
- Load CSV from Experiments Builder
- Add error handling and reporting nodes
- Save and schedule overnight run

**Demo 4: Framework Report Builder - Generate Report (3 min)**
- Open Framework Report Builder
- Load test results from previous runs
- Generate Shmoo plots and summary
- Export HTML report

**Demo 5: End-to-End Workflow Overview (2 min)**
- Quick walkthrough: Design → Automate → Analyze
- Show overnight characterization setup
- Review morning results and reports

---

## Slide 16: Documentation & Resources

**Getting Started:**

1. **User Manuals:**
   - `S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_USER_MANUAL.md`
   - `S2T/DOCUMENTATION/PPV/THR_DEBUG_TOOLS_USER_MANUAL.md`

2. **Interactive Examples:**
   - `THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb`
   - `THR_DEBUG_TOOLS_EXAMPLES.ipynb`

3. **Quick Reference:**
   - `THR_DEBUG_TOOLS_QUICK_START.md`
   - `THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md`

**Support Contact:**
- Gabriel Espinoza: gabriel.espinoza.ballestero@intel.com

---

## Slide 17: Q&A

**Questions?**

**Common Topics:**
- How do I get access to the tools?
- Can I run this on GNR/CWF platforms?
- How do I debug specific failure modes?
- Can I customize the automation flows?
- Integration with existing test infrastructure?

**Thank you!**

**Next Steps:**
- Hands-on training sessions available
- One-on-one tool walkthroughs
- Custom workflow development support

---

## Appendix: Quick Command Reference

**Essential Commands:**

```python
# DebugFramework - Test execution
import users.THR.dmr_debug_utilities.DebugFramework.SystemDebug as sd

# System-to-Tester - S2T configuration
import users.THR.dmr_debug_utilities.S2T.SetTesterRegs as s2t

# S2T Tools
s2t.setupSystemAsTester()
s2t.MeshQuickTest()
s2t.SliceQuickTest()

# DebugFramework Tools
sd.ControlPanel()
sd.AutomationPanel()

# THR Debug Tools
python c:\Git\Automation\PPV\run.py

# Experiments Builder
from PPV.run import launch_experiments_builder
launch_experiments_builder()

# Automation Flow Designer
from PPV.run import launch_automation_designer
launch_automation_designer()

# Framework Report Builder
from PPV.run import launch_framework_report
launch_framework_report()
```

**Documentation Paths:**
- User Manuals: `S2T/DOCUMENTATION/`
- Examples: `THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb`
- Quick Start: `THR_DEBUG_TOOLS_QUICK_START.md`

---

**End of Presentation**
**© 2026 Intel Corporation - Intel Confidential**
cm.getCoreCount()
cm.getSliceCount()
```

**Use Cases:**
- Isolating failing cores
- Power optimization studies
- Thermal characterization
- Yield analysis

---

## Slide 12: S2T - dpmChecks (MCA Logging)

**dpmChecks.py - Error Reporting & Configuration**

**MCA Logger:**
```python
import users.THR.dmr_debug_utilities.S2T.dpmChecks as dpm

# Initialize logger
dpm.logger(
    test_name="Voltage_Sweep",
    description="1.0V to 0.8V characterization"
)

# Run test with automatic MCA capture
runTest()

# Logger generates reports automatically
```

**Report Output:**
- MCA error counts by bank
- Error signatures and patterns
- Timestamp correlation
- Core/socket mapping
- Excel report generation

---

## Slide 13: S2T - Configuration Management

**dpmChecks.py - BIOS & System Configuration**

**Pseudo Boot Script (pseudo_bs):**
```python
# Change configuration WITHOUT reboot
dpm.pseudo_bs(
    vcc_core="1.05V",
    frequency="3.0GHz",
    HT_enable=False
)
```

**BIOS Knob Management:**
```python
# Query current settings
current_knobs = dpm.biosknobs()

# Modify knobs
dpm.bsknobs(ProcessorHyperThreadingDisable=1)
```

**Benefits:**
- Rapid configuration changes
- No reboot delays
- Sweep automation
- Consistent settings

---

## Slide 14: S2T - DFF Data Collection

**GetTesterCurves.py & DffDataCollector.py**

**Purpose:** Automated DFF (Design For Failure) data retrieval

**Single Collection:**
```python
import users.THR.dmr_debug_utilities.S2T.GetTesterCurves as gtc

gtc.GetTesterCurves(
    socket=0,
    core=0,
    output_dir="C:/DFF_Data"
)
```

**Batch Collection:**
```python
import users.THR.dmr_debug_utilities.S2T.DffDataCollector as dfc

dfc.collectAllCores(
    socket=0,
    parallel=True
)
```

**Output:** Voltage/frequency curves, guardband data, yield predictions

---

## Slide 15: Test Execution Framework

**TestFramework.py & S2TTestFramework.py**

**Test Execution Pipeline:**

1. **Initialization**
   - Hardware setup
   - Configuration loading
   - Logger initialization

2. **Execution**
   - Test pattern generation
   - Real-time monitoring
   - Error capture

3. **Post-Processing**
   - Result aggregation
   - Report generation
   - Data archival

**Supported Test Types:**
- Loop tests (repeated iterations)
- Sweep tests (parameter ranges)
- Shmoo tests (2D parameter space)

---

## Slide 16: Automation Flow Builder

**Automation_Flow/ - Visual Flow Designer**

**Components:**
- **AutomationBuilder.py** - Flow construction
- **AutomationFlows.py** - Flow execution
- **AutomationHandler.py** - Flow management
- **AutomationTracker.py** - Progress tracking

**Flow Example:**
```
START → Configure Voltage (1.0V)
      → Run Test (100 iterations)
      → Check Pass/Fail
      → [Pass] → Decrease Voltage (0.05V)
      → [Fail] → Log Results → END
```

**Benefits:**
- No coding required
- Reusable flows
- Version control
- Team collaboration

**Visual Suggestion:** Flow diagram with decision nodes

---

## Slide 17: Storage & Reporting

**Storage_Handler/ - Database Integration**

**Features:**
- MongoDB integration for result storage
- Automated report generation
- Historical data queries
- Trend analysis
- Multi-unit comparison

**Report Types:**
1. **Test Summary** - Pass/fail statistics
2. **Error Report** - MCA analysis
3. **Performance Report** - Voltage/frequency curves
4. **Comparison Report** - Multi-unit analysis

**ReportUtils.py Functions:**
- Excel report generation
- PDF export
- Chart/graph creation
- Data visualization

---

## Slide 18: PPV Debug Tools Integration

**PPV/ - 8 Integrated Tools**

Located in: `BASELINE_DMR/DebugFramework/PPV/`

**Tools Suite:**
1. **PTC Loop Parser** - Loop experiment analysis
2. **PPV MCA Report Builder** - MCA consolidation
3. **DPMB Bucketer Requests** - Historical data queries
4. **File Handler** - Report merging
5. **Framework Report Builder** - Execution statistics
6. **Automation Flow Designer** - Visual automation
7. **Experiment Builder** - Config generation
8. **MCA Decoder** - Register-level decoding

**Launch:**
```bash
cd c:\Git\Automation\PPV
python run.py
# Select DMR product
```

**Visual Suggestion:** PPV Tools Hub screenshot

---

## Slide 19: PPV Tool Highlight - PTC Loop Parser

**Purpose:** Parse and analyze loop experiment data

**Input:** PTC loop experiment results (CSV/TXT)

**Features:**
- Automatic data extraction
- Configuration identification
- Pass/fail analysis
- Voltage/frequency mapping
- Statistical analysis

**Output:**
- Parsed Excel report
- Summary statistics
- Failure patterns
- Configuration recommendations

**Use Case:** Post-characterization analysis for large loop experiments

---

## Slide 20: PPV Tool Highlight - MCA Report Builder

**Purpose:** Consolidate MCA data from multiple sources

**Input Sources:**
- Framework execution logs
- Manual MCA captures
- Historical database records
- Multi-unit test data

**Features:**
- Multi-source aggregation
- Error signature matching
- Core/socket correlation
- Temporal analysis
- Trend identification

**Output:**
- Consolidated Excel report
- Error frequency charts
- Core mapping diagrams
- Failure predictions

---

## Slide 21: PPV Tool Highlight - DPMB Integration

**DPMB Bucketer Requests - Historical Data Access**

**Purpose:** Query Intel DPMB (Data Platform Management Bucketer) for historical test data

**API Integration:**
```python
from PPV.api.dpmb import DPMBClient

client = DPMBClient()
data = client.getBucketData(
    product="DMR",
    test_type="voltage_sweep",
    date_range="last_30_days"
)
```

**Use Cases:**
- Historical trend analysis
- Unit comparison
- Baseline establishment
- Failure prediction
- Yield correlation

---

## Slide 22: Advanced Features - Serial Connection

**SerialConnection.py - Hardware Communication**

**Features:**
- Multi-port serial management
- Auto-detection and connection
- Command execution
- Log capture
- Timeout handling

**Supported Interfaces:**
- EFI Shell
- Linux shell
- BMC console
- Custom protocols

**Integration:**
- Automatic hardware initialization
- Test execution synchronization
- Real-time monitoring
- Error recovery

---

## Slide 23: Advanced Features - Hardware Mocks

**HardwareMocks.py & TestMocks.py**

**Purpose:** Enable framework development without hardware

**Mock Capabilities:**
- Simulated hardware responses
- Configurable test outcomes
- Timing simulation
- Error injection
- Edge case testing

**Benefits:**
- Framework development without silicon
- Unit testing
- Training environments
- Demo capabilities
- CI/CD integration

**Use Cases:**
- New feature development
- Test validation
- User training
- Presentation demos

---

## Slide 24: EFI Tools & Scripts

**EFI/ - Extensive EFI Shell Tooling**

**Key Scripts:**
- **startup_efi.nsh** - Automated EFI initialization
- **runregression.nsh** - Regression test execution
- **SetupMesh.nsh** - Mesh test configuration
- **SetupSlice.nsh** - Slice test setup
- **dbmvars.nsh** - Variable management

**Pattern Finder:**
- Custom test pattern generation
- Pattern validation
- Performance optimization
- Coverage analysis

**Integration:** Seamless EFI/Framework coordination for sub-boot testing

---

## Slide 25: Linux Tools & Support

**TTL/TTL_Linux/ - Linux Test Environment**

**Capabilities:**
- Boot to Linux from framework
- Execute Linux-based tests
- System-level validation
- Performance benchmarking
- Driver testing

**Startup Scripts:**
- **startup_linux.nsh** - Automated Linux boot
- Custom test harness
- Result collection
- Log aggregation

**Use Cases:**
- OS-level validation
- Driver characterization
- System integration testing
- Performance analysis

---

## Slide 26: Product-Specific Modules

**S2T/product_specific/ - DMR Customization**

**Product-Specific Features:**
- DMR register definitions
- Memory map configurations
- Voltage/frequency tables
- Fuse configurations
- SKU-specific settings

**Fuse Management:**
```
S2T/Fuse/
├── disable_acode.cfg
├── disable_amx.cfg
├── disable_HT.cfg
└── pm_enable_no_vf.cfg
```

**Benefits:**
- Product-optimized testing
- Accurate hardware modeling
- SKU-specific validation

---

## Slide 27: Common Workflow #1 - Initial Unit Bring-Up

**Workflow Steps:**

1. **Hardware Setup**
   - Connect serial ports
   - Initialize BMC
   - Verify power

2. **Framework Launch**
   ```python
   import users.THR.dmr_debug_utilities.DebugFramework.SystemDebug as sd
   sd.ControlPanel()
   ```

3. **First Boot**
   - Run MeshQuickTest
   - All cores enabled
   - Nominal voltage/frequency

4. **Health Check**
   - Verify boot success
   - Check MCA errors
   - Validate core count

5. **Initial Characterization**
   - Simple loop test (10 iterations)
   - Document baseline

**Time:** ~30 minutes

---

## Slide 28: Common Workflow #2 - Voltage Characterization

**Workflow Steps:**

1. **Setup Automation Flow**
   - Launch AutomationPanel
   - Create voltage sweep flow
   - Range: 1.0V to 0.7V, step 0.05V

2. **Configure Logger**
   ```python
   dpm.logger("Voltage_Characterization", "Finding min voltage")
   ```

3. **Execute Sweep**
   - Automated voltage changes (pseudo_bs)
   - 100 iterations per voltage
   - MCA logging enabled

4. **Analysis**
   - Review MCA reports
   - Identify failure voltage
   - Calculate guardband

5. **Documentation**
   - Generate summary report
   - Store in database
   - Update unit profile

**Time:** ~2-4 hours (automated)

---

## Slide 29: Common Workflow #3 - Core Isolation Debug

**Workflow Steps:**

1. **Identify Failure**
   - Test fails with all cores
   - MCA report shows errors

2. **Binary Search**
   ```python
   import users.THR.dmr_debug_utilities.S2T.CoreManipulation as cm

   # Test with half cores
   cm.createCoreMask(cores=range(0, core_count//2))
   runTest()
   ```

3. **Isolate Failing Core**
   - Continue binary search
   - Narrow down to single core

4. **Detailed Analysis**
   - Run targeted tests
   - Collect DFF data
   - MCA deep dive

5. **Resolution**
   - Document failing core
   - Create workaround mask
   - Generate failure report

**Time:** ~1-2 hours

---

## Slide 30: Common Workflow #4 - Regression Validation

**Workflow Steps:**

1. **Load Regression Suite**
   - Launch AutomationPanel
   - Select regression flow
   - Configure test parameters

2. **Execution**
   - Automated overnight run
   - Multiple test configurations
   - Comprehensive coverage

3. **Monitoring**
   - Real-time status dashboard
   - Error notifications
   - Progress tracking

4. **Result Analysis**
   - Automated report generation
   - Pass/fail summary
   - Historical comparison

5. **Sign-off**
   - Review results
   - Document exceptions
   - Archive data

**Time:** 8-12 hours (overnight)

---

## Slide 31: Best Practices

**Framework Usage Recommendations:**

**DO:**
- ✅ Use logger() for all characterization
- ✅ Document test configurations
- ✅ Archive important results
- ✅ Leverage automation for repetitive tasks
- ✅ Use pseudo_bs for rapid sweeps
- ✅ Monitor MCA logs regularly

**DON'T:**
- ❌ Skip logger initialization
- ❌ Run tests without error capture
- ❌ Ignore MCA warnings
- ❌ Manually repeat identical tests
- ❌ Modify core masks during execution
- ❌ Delete test data prematurely

---

## Slide 32: Troubleshooting Guide

**Common Issues & Solutions:**

| Issue | Cause | Solution |
|-------|-------|----------|
| Import errors | Wrong path | Use `users.THR.dmr_debug_utilities.DebugFramework` |
| Serial timeout | Connection lost | Check cables, restart BMC |
| MCA not captured | Logger not initialized | Call `dpm.logger()` before test |
| Test hangs | Hardware unresponsive | Check serial console, power cycle |
| Config not applied | Reboot required | Use `pseudo_bs()` for no-reboot changes |

**Support:**
- Documentation: `c:\Git\Automation\S2T\DOCUMENTATION\`
- Contact: gabriel.espinoza.ballestero@intel.com

---

## Slide 33: Documentation Resources

**Available Documentation:**

**Location:** `c:\Git\Automation\S2T\DOCUMENTATION\`

**DEBUG_FRAMEWORK_S2T/**
- THR_DEBUG_FRAMEWORK_USER_MANUAL.md (1052 lines)
- THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md (326 lines)
- THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb
- THR_S2T_EXAMPLES.ipynb

**PPV/**
- THR_DEBUG_TOOLS_QUICK_START.md
- THR_DEBUG_TOOLS_USER_MANUAL.md (1110 lines)
- THR_DEBUG_TOOLS_FLOWS.md (961 lines)
- THR_DEBUG_TOOLS_EXAMPLES.ipynb

**All Documentation:** Professional, comprehensive, with examples

---

## Slide 34: Training Resources

**Getting Started:**

1. **Read Quick Start Guide**
   - `DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_USER_MANUAL.md`

2. **Review Import Paths**
   - `DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md`

3. **Try Interactive Examples**
   - Open Jupyter notebooks
   - Run example code
   - Experiment with configurations

4. **Practice with Mocks**
   - Use HardwareMocks for training
   - No hardware required
   - Safe environment for learning

5. **Contact Support**
   - gabriel.espinoza.ballestero@intel.com
   - Documentation feedback welcome

---

## Slide 35: Roadmap & Future Enhancements

**Planned Features:**

**Q1 2026:**
- Enhanced automation flow designer
- Machine learning failure prediction
- Expanded PPV tool integration

**Q2 2026:**
- Cloud data storage integration
- Real-time collaboration features
- Mobile monitoring app

**Q3 2026:**
- Advanced analytics dashboard
- Automated report distribution
- Cross-product comparison tools

**Feedback Welcome:**
- Feature requests to maintainer
- Bug reports and improvements
- Documentation enhancements

---

## Slide 36: Demo - Live Framework Walkthrough

**Demo Agenda (10 minutes):**

1. **Launch ControlPanel** (2 min)
   - Show GUI interface
   - Configure simple test
   - Execute and monitor

2. **MeshQuickTest** (2 min)
   - Launch interface
   - Configure S2T
   - Show test execution

3. **MCA Logger** (2 min)
   - Initialize logger
   - Run test with MCA capture
   - Review generated report

4. **PPV Tools Hub** (2 min)
   - Launch Tools Hub
   - Show 8 integrated tools
   - Quick parser demonstration

5. **Q&A** (2 min)

---

## Slide 37: Key Takeaways

**What We Learned:**

✅ **Comprehensive Framework**
   - DebugFramework + S2T = Complete validation solution
   - GUI and API interfaces available
   - Extensive automation capabilities

✅ **DMR-Optimized**
   - Product-specific configurations
   - Fuse management
   - SKU support

✅ **8 PPV Debug Tools**
   - Integrated analysis suite
   - Historical data access
   - Advanced workflows

✅ **Production-Ready**
   - Professional documentation
   - Training resources
   - Active support

---

## Slide 38: Q&A

**Questions?**

**Contact Information:**
- **Maintainer:** Gabriel Espinoza
- **Email:** gabriel.espinoza.ballestero@intel.com
- **Documentation:** `c:\Git\Automation\S2T\DOCUMENTATION\`
- **Repository:** `c:\Git\Automation\S2T\BASELINE_DMR\`

**Resources:**
- User manuals with complete API reference
- Jupyter notebooks with executable examples
- Quick start guides
- Workflow documentation
- Troubleshooting guides

**Support:** Email maintainer for technical questions, bug reports, or feature requests

---

## Slide 39: Thank You

**DMR S2T & DebugFramework**

**Version 2.0** - Ready for Production

**Get Started Today:**
1. Review documentation in `S2T/DOCUMENTATION/`
2. Try interactive Jupyter examples
3. Contact for training or support

**Intel Corporation - Test & Validation**
**© 2026 Intel Corporation. Intel Confidential.**

---

## Appendix: Technical Specifications

**System Requirements:**
- Windows 10/11 or Linux
- Python 3.7+
- Required packages: pandas, openpyxl, tabulate, requests, tkinter

**Hardware Requirements:**
- DMR validation platform
- Serial connection capability
- Network access (for DPMB queries)

**Repository Structure:**
- Main: `c:\Git\Automation\S2T\BASELINE_DMR\`
- Docs: `c:\Git\Automation\S2T\DOCUMENTATION\`
- PPV: `c:\Git\Automation\PPV\`

**Version Control:**
- Framework: v2.0 (January 2026)
- Documentation: v2.0 (January 2026)

---

## Appendix: Import Reference

**DMR Import Paths:**

```python
# DebugFramework
import users.THR.dmr_debug_utilities.DebugFramework.SystemDebug as sd

# S2T Modules
import users.THR.dmr_debug_utilities.S2T.SetTesterRegs as s2t
import users.THR.dmr_debug_utilities.S2T.CoreManipulation as cm
import users.THR.dmr_debug_utilities.S2T.dpmChecks as dpm
import users.THR.dmr_debug_utilities.S2T.GetTesterCurves as gtc
import users.THR.dmr_debug_utilities.S2T.DffDataCollector as dfc
```

**Note:** DMR uses no product prefix in filenames (unlike GNR/CWF)

---

## Appendix: Quick Command Reference

**Essential Commands:**

```python
# Launch GUIs
sd.ControlPanel()
sd.AutomationPanel()
s2t.MeshQuickTest()
s2t.SliceQuickTest()

# MCA Logging
dpm.logger("test_name", "description")

# Configuration
dpm.pseudo_bs(vcc="1.0V", freq="3.0GHz")

# Core Control
cm.createCoreMask(cores=[0,1,2])
cm.bootToEFI()

# DFF Collection
gtc.GetTesterCurves(socket=0, core=0)
```

---

**END OF PRESENTATION OUTLINE**

**Total Slides:** 39 + Appendix (3 slides) = 42 slides
**Estimated Presentation Time:** 45-60 minutes
**Format Recommendation:** 16:9 widescreen, Intel corporate template
