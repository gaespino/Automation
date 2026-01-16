# THR Testing & Validation Framework - Documentation Index

**Version:** 2.0
**Release Date:** January 15, 2026
**Organization:** Intel Corporation - Test & Validation
**Classification:** Intel Confidential
**Maintainer:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)
**Location:** `c:\Git\Automation\S2T\DOCUMENTATION\`

---

## 📚 Documentation Structure

This folder contains comprehensive documentation for Intel's THR (Test Hole Resolution) Testing & Validation frameworks, organized into two main categories:

### 1. Debug Framework & S2T (`DEBUG_FRAMEWORK_S2T/`)
**BASELINE Framework** - DebugFramework and System-to-Tester (S2T) modules for **GNR** (Granite Rapids), **CWF** (Clearwater Forest), and **DMR** (Diamond Rapids)

### 2. PPV Debug Tools (`PPV/`)
**THR Debug Tools Suite** - 8 integrated GUI tools for unit characterization, MCA analysis, and post-silicon validation workflows

---

## 📂 Folder Contents

### DEBUG_FRAMEWORK_S2T/

#### Core Documentation
| File | Description |
|------|-------------|
| [THR_DEBUG_FRAMEWORK_USER_MANUAL.md](DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_USER_MANUAL.md) | Complete BASELINE framework manual covering ControlPanel, AutomationPanel, MeshQuickTest, SliceQuickTest, and setupSystemAsTester interfaces |
| [THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md](DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md) | Import paths, file naming conventions, and deployment guide for GNR/CWF/DMR products |

#### Interactive Examples
| File | Description |
|------|-------------|
| [THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb](DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb) | Jupyter notebook with DebugFramework interface examples (ControlPanel, AutomationPanel, MeshQuickTest, SliceQuickTest) |
| [THR_S2T_EXAMPLES.ipynb](DEBUG_FRAMEWORK_S2T/THR_S2T_EXAMPLES.ipynb) | Jupyter notebook with S2T/dpmChecks examples (logger, pseudo_bs, unit info, voltage sweeps) |

**Key Topics:**
- System requirements & installation
- Product-specific import paths (GNR/CWF/DMR)
- GUI interfaces for test execution
- MCA logging and error reporting
- S2T configuration and testing
- Core manipulation and masking
- BIOS knob configuration
- Voltage sweep automation

---

### PPV/

#### Core Documentation
| File | Description |
|------|-------------|
| [THR_DEBUG_TOOLS_QUICK_START.md](PPV/THR_DEBUG_TOOLS_QUICK_START.md) | Quick start guide with launch instructions, tool overview, and common workflows |
| [THR_DEBUG_TOOLS_USER_MANUAL.md](PPV/THR_DEBUG_TOOLS_USER_MANUAL.md) | Complete manual for all 8 THR Debug Tools with parameters, examples, and troubleshooting |
| [THR_DEBUG_TOOLS_FLOWS.md](PPV/THR_DEBUG_TOOLS_FLOWS.md) | Workflow documentation showing tool integration, data flows, and best practices |

#### Interactive Examples
| File | Description |
|------|-------------|
| [THR_DEBUG_TOOLS_EXAMPLES.ipynb](PPV/THR_DEBUG_TOOLS_EXAMPLES.ipynb) | Jupyter notebook with GUI usage examples and programmatic API demonstrations |

**8 Integrated Tools:**
1. **PTC Loop Parser** - Experiment configuration and loop data analysis
2. **PPV MCA Report Builder** - MCA analysis and comprehensive reporting
3. **DPMB Bucketer Requests** - Historical bucket data queries
4. **File Handler** - Merge and consolidate reports
5. **Framework Report Builder** - Execution analysis and statistics
6. **Automation Flow Designer** - Visual automation workflow design
7. **Experiment Builder** - Excel-like config creator
8. **MCA Single Line Decoder** - Register-level MCA decoding

---

## 🚀 Quick Start Guide

### Debug Framework & S2T

**Choose your product and import:**

```python
# GNR (Granite Rapids)
import users.gaespino.DebugFramework.GNRSystemDebug as sd
import users.THR.PythonScripts.thr.S2T.GNRSetTesterRegs as s2t
import users.THR.PythonScripts.thr.S2T.dpmChecksGNR as dpm

# CWF (Clearwater Forest)
import users.gaespino.DebugFramework.CWFSystemDebug as sd
import users.THR.PythonScripts.thr.S2T.CWFSetTesterRegs as s2t
import users.THR.PythonScripts.thr.S2T.dpmChecksCWF as dpm

# DMR (Diamond Rapids)
import users.THR.dmr_debug_utilities.DebugFramework.SystemDebug as sd
import users.THR.dmr_debug_utilities.S2T.SetTesterRegs as s2t
import users.THR.dmr_debug_utilities.S2T.dpmChecks as dpm
```

**Launch interfaces:**
```python
sd.ControlPanel()        # Manual test execution
sd.AutomationPanel()     # Automation flows
s2t.MeshQuickTest()      # Full chip testing
s2t.SliceQuickTest()     # Core-specific testing
```

---

### THR Debug Tools (PPV)

**Launch Tools Hub:**
```bash
cd c:\Git\Automation\PPV
python run.py
```

The Tools Hub will:
1. Display THR Debug Tools banner
2. Prompt for product selection (GNR/CWF/DMR)
3. Launch main interface with all 8 tools

**Primary Usage:** GUI interface via Tools Hub
**Secondary Usage:** Programmatic API for automation

---

## 🎯 Documentation Purpose Guide

| I want to... | Navigate to |
|--------------|-------------|
| **Debug Framework & S2T** | |
| Understand the BASELINE framework | [DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_USER_MANUAL.md](DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_USER_MANUAL.md) |
| Set up imports for my product | [DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md](DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md) |
| See DebugFramework examples | [DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb](DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb) |
| Learn S2T/dpmChecks usage | [DEBUG_FRAMEWORK_S2T/THR_S2T_EXAMPLES.ipynb](DEBUG_FRAMEWORK_S2T/THR_S2T_EXAMPLES.ipynb) |
| **THR Debug Tools (PPV)** | |
| Get started quickly | [PPV/THR_DEBUG_TOOLS_QUICK_START.md](PPV/THR_DEBUG_TOOLS_QUICK_START.md) |
| Learn all 8 tools | [PPV/THR_DEBUG_TOOLS_USER_MANUAL.md](PPV/THR_DEBUG_TOOLS_USER_MANUAL.md) |
| Understand debug workflows | [PPV/THR_DEBUG_TOOLS_FLOWS.md](PPV/THR_DEBUG_TOOLS_FLOWS.md) |
| See tool usage examples | [PPV/THR_DEBUG_TOOLS_EXAMPLES.ipynb](PPV/THR_DEBUG_TOOLS_EXAMPLES.ipynb) |

---

## 🔗 Source Code Repositories

### Debug Framework & S2T
| Product | Repository |
|---------|-----------|
| **GNR** | https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.graniterapids |
| **CWF** | https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.clearwaterforest |
| **DMR** | https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.diamondrapids |

### THR Debug Tools (PPV)
| Component | Location |
|-----------|----------|
| **Main Repository** | `c:\Git\Automation\PPV\` |
| **Tools Hub** | `PPV/run.py` |
| **GUI Modules** | `PPV/gui/` |
| **Parsers** | `PPV/parsers/` |
| **Decoders** | `PPV/Decoder/` |

---

## 📧 Support & Contact

**Maintainer:** Gabriel Espinoza
**Email:** gabriel.espinoza.ballestero@intel.com
**Organization:** Intel Corporation - Test & Validation

**For Technical Support:**
- Questions or issues: Contact maintainer via email
- Bug reports: Include version, product, and full error logs
- Feature requests: Provide detailed use case description
- Documentation feedback: Report errors or suggest improvements

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| **2.0** | January 15, 2026 | **Major reorganization**: Split documentation into DEBUG_FRAMEWORK_S2T/ and PPV/ subfolders; renamed all files with THR_ prefix for consistency; added comprehensive cross-references; professional formatting for official release |
| 1.5 | January 15, 2026 | Updated to full import paths; added repository links; centralized all documentation in S2T/DOCUMENTATION/ |
| 1.0 | January 15, 2026 | Initial unified documentation for BASELINE framework and THR Debug Tools |

---

## 💡 Key Features

### Debug Framework & S2T
✅ **Multi-Product Support** - Works identically across GNR, CWF, and DMR
✅ **GUI Interfaces** - ControlPanel, AutomationPanel, MeshQuickTest, SliceQuickTest
✅ **S2T Capabilities** - ATE-style testing in system environment
✅ **MCA Logging** - Comprehensive error capture and reporting
✅ **Configuration Management** - BIOS knobs, fuses, pseudo boot scripts

### THR Debug Tools (PPV)
✅ **8 Integrated Tools** - Complete debug workflow coverage
✅ **GUI-First Design** - Tools Hub with unified interface
✅ **Product Support** - GNR, CWF, DMR with automatic selection
✅ **DPMB Integration** - Historical data queries and analysis
✅ **MCA Analysis** - Multi-source reporting and register decoding
✅ **Automation Support** - Programmatic API for batch processing

---

## 📝 Documentation Standards

All documentation follows Intel professional standards:
- ✅ Consistent THR_ prefix naming convention
- ✅ UPPERCASE_WITH_UNDERSCORES file naming
- ✅ Version control and release dates
- ✅ Intel confidential classification
- ✅ Complete metadata headers
- ✅ Professional support sections
- ✅ Cross-referenced navigation
- ✅ Copyright and legal notices

---

**© 2026 Intel Corporation. Intel Confidential.**
