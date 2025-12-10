================================================================================
BASELINE IMPORT ANALYSIS - DETAILED REPORT
================================================================================
Generated: 2025-12-09
Total unique import statements: 343

================================================================================
SUMMARY BY CATEGORY
================================================================================

EXTERNAL         10 packages,   88 file references
INTEL             8 packages,   41 file references
STANDARD         40 packages,  473 file references
PROJECT          18 packages,   59 file references
RELATIVE          1 packages,   15 file references
OTHER            39 packages,  118 file references

================================================================================
EXTERNAL PACKAGES (pip/conda)
================================================================================

📦 colorama
   Used in 11 file(s):
   - DebugFramework\ExecutionHandler\utils\FrameworkUtils.py
   - DebugFramework\FileHandler.py
   - DebugFramework\PPV\parsers\Frameworkparser.py
   - DebugFramework\SystemDebug.py
   - DebugFramework\UI\ControlPanel.py
   - DebugFramework\UI\ProcessPanel.py
   - S2T\CoreManipulation.py
   - S2T\product_specific\cwf\functions.py
   - S2T\product_specific\dmr\functions.py
   - S2T\product_specific\gnr\functions.py
   ... and 1 more files

📦 lxml
   Used in 2 file(s):
   - S2T\GetTesterCurves.py
   - test_dependencies.py

📦 numpy
   Used in 3 file(s):
   - DebugFramework\PPV\parsers\FrameworkAnalyzer.py
   - S2T\Tools\portid2ip.py
   - test_dependencies.py

📦 openpyxl
   Used in 17 file(s):
   - DebugFramework\Automation_Flow\AutomationDesigner.py
   - DebugFramework\FileHandler.py
   - DebugFramework\Misc.py
   - DebugFramework\PPV\gui\AutomationDesigner.py
   - DebugFramework\PPV\gui\ExperimentBuilder.py
   - DebugFramework\PPV\parsers\Frameworkparser.py
   - DebugFramework\PPV\parsers\MCAparser.py
   - DebugFramework\PPV\utils\ExcelReportBuilder.py
   - DebugFramework\PPV\utils\FrameworkFileFix.py
   - DebugFramework\Storage_Handler\ReportUtils.py
   ... and 7 more files

📦 pandas
   Used in 27 file(s):
   - DebugFramework\EFI\patternfinder.py
   - DebugFramework\FileHandler.py
   - DebugFramework\Misc.py
   - DebugFramework\PPV\Decoder\TransformJson.py
   - DebugFramework\PPV\Decoder\decoder.py
   - DebugFramework\PPV\Decoder\decoder_dmr.py
   - DebugFramework\PPV\Decoder\faildetection.py
   - DebugFramework\PPV\parsers\FrameworkAnalyzer.py
   - DebugFramework\PPV\parsers\Frameworkparser.py
   - DebugFramework\PPV\parsers\MCAparser.py
   ... and 17 more files

📦 psutil
   Used in 3 file(s):
   - DebugFramework\ExecutionHandler\utils\EmergencyCleanup.py
   - DebugFramework\ExecutionHandler\utils\ThreadsManager.py
   - test_dependencies.py

📦 pymongo
   Used in 2 file(s):
   - DebugFramework\Storage_Handler\DBClient.py
   - test_dependencies.py

📦 pytz
   Used in 3 file(s):
   - DebugFramework\ExecutionHandler\utils\misc_utils.py
   - DebugFramework\SystemDebug.py
   - test_dependencies.py

📦 tabulate
   Used in 17 file(s):
   - DebugFramework\ExecutionHandler\utils\FrameworkUtils.py
   - DebugFramework\Misc.py
   - DebugFramework\PPV\gui\PPVFrameworkReport.py
   - DebugFramework\PPV\parsers\Frameworkparser.py
   - DebugFramework\SystemDebug.py
   - S2T\CoreManipulation.py
   - S2T\GetTesterCurves.py
   - S2T\SetTesterRegs.py
   - S2T\Tools\requests_unit_info.py
   - S2T\UI\System2TesterUI.py
   ... and 7 more files

📦 xlwings
   Used in 3 file(s):
   - DebugFramework\PPV\gui\PPVTools.py
   - DebugFramework\PPV\parsers\MCAparser.py
   - test_dependencies.py

================================================================================
INTEL-SPECIFIC PACKAGES
================================================================================

🏢 configs
   Used in 2 file(s):
   - S2T\ConfigsLoader.py
   - S2T\GetTesterCurves.py

🏢 ipccli
   Used in 13 file(s):
   - DebugFramework\S2TMocks.py
   - DebugFramework\S2TTestFramework.py
   - DebugFramework\SystemDebug.py
   - S2T\ConfigsLoader.py
   - S2T\CoreManipulation.py
   - S2T\Logger\ErrorReport.py
   - S2T\Logger\ErrorReportClass.py
   - S2T\Logger\ErrorReport_legacy.py
   - S2T\Logger\ErrorReport_original_backup.py
   - S2T\SetTesterRegs.py
   ... and 3 more files

🏢 namednodes
   Used in 14 file(s):
   - DebugFramework\S2TTestFramework.py
   - DebugFramework\SystemDebug.py
   - S2T\ConfigsLoader.py
   - S2T\CoreManipulation.py
   - S2T\Logger\ErrorReport.py
   - S2T\Logger\ErrorReportClass.py
   - S2T\Logger\ErrorReport_legacy.py
   - S2T\Logger\ErrorReport_original_backup.py
   - S2T\SetTesterRegs.py
   - S2T\Tools\portid2ip.py
   ... and 4 more files

🏢 pm
   Used in 1 file(s):
   - S2T\dpmChecks.py

🏢 registers
   Used in 1 file(s):
   - S2T\ConfigsLoader.py

🏢 strategy
   Used in 1 file(s):
   - S2T\ConfigsLoader.py

🏢 svtools
   Used in 2 file(s):
   - S2T\Logger\ErrorReportClass.py
   - test_dependencies.py

🏢 toolext
   Used in 7 file(s):
   - DebugFramework\S2TMocks.py
   - DebugFramework\S2TTestFramework.py
   - S2T\CoreManipulation.py
   - S2T\Logger\ErrorReport_legacy.py
   - S2T\Logger\ErrorReport_original_backup.py
   - S2T\dpmChecks.py
   - test_dependencies.py

================================================================================
MOST USED STANDARD LIBRARY MODULES (Top 15)
================================================================================

📚 os                   - Used in  77 files
📚 sys                  - Used in  66 files
📚 time                 - Used in  36 files
📚 typing               - Used in  35 files
📚 datetime             - Used in  33 files
📚 json                 - Used in  29 files
📚 threading            - Used in  22 files
📚 dataclasses          - Used in  20 files
📚 re                   - Used in  16 files
📚 enum                 - Used in  14 files
📚 queue                - Used in  12 files
📚 traceback            - Used in  11 files
📚 shutil               - Used in  11 files
📚 zipfile              - Used in   8 files
📚 random               - Used in   7 files

================================================================================
PROJECT MODULES (Top 15 Most Used)
================================================================================

🔧 DebugFramework            - Used in  11 files
🔧 UI                        - Used in   7 files
🔧 ExecutionHandler          - Used in   7 files
🔧 FileHandler               - Used in   6 files
🔧 ConfigsLoader             - Used in   6 files
🔧 S2T                       - Used in   3 files
🔧 TestMocks                 - Used in   3 files
🔧 HardwareMocks             - Used in   2 files
🔧 Logger                    - Used in   2 files
🔧 Automation_Flow           - Used in   2 files
🔧 MaskEditor                - Used in   2 files
🔧 Decoder                   - Used in   2 files
🔧 Storage_Handler           - Used in   1 files
🔧 PPV                       - Used in   1 files
🔧 SystemDebug               - Used in   1 files

================================================================================
DETAILED IMPORT STATEMENTS BY PACKAGE
================================================================================


================================================================================
Package: colorama
================================================================================

Import: from colorama import Fore, Style, Back
Used in 10 file(s):
  - DebugFramework\ExecutionHandler\utils\FrameworkUtils.py:7
  - DebugFramework\FileHandler.py:15
  - DebugFramework\PPV\parsers\Frameworkparser.py:6
  - DebugFramework\SystemDebug.py:14
  - DebugFramework\UI\ControlPanel.py:12
  ... and 5 more files

Import: import colorama
Used in 6 file(s):
  - DebugFramework\PPV\parsers\Frameworkparser.py:4
  - DebugFramework\SystemDebug.py:11
  - S2T\product_specific\cwf\functions.py:9
  - S2T\product_specific\dmr\functions.py:9
  - S2T\product_specific\gnr\functions.py:9
  ... and 1 more files


================================================================================
Package: configs
================================================================================

Import: import configs as pe
Used in 2 file(s):
  - S2T\ConfigsLoader.py:43
  - S2T\GetTesterCurves.py:112


================================================================================
Package: ipccli
================================================================================

Import: from ipccli import BitData
Used in 2 file(s):
  - S2T\CoreManipulation.py:72
  - S2T\SetTesterRegs.py:84

Import: from ipccli import ipc
Used in 1 file(s):
  - DebugFramework\S2TTestFramework.py:133

Import: from ipccli.bitdata import BitData as _BitData
Used in 1 file(s):
  - S2T\Tools\requests_unit_info.py:24

Import: from ipccli.stdiolog import log
Used in 4 file(s):
  - DebugFramework\SystemDebug.py:15
  - S2T\Logger\ErrorReportClass.py:29
  - S2T\Logger\ErrorReport_legacy.py:20
  - S2T\Logger\ErrorReport_original_backup.py:16

Import: from ipccli.stdiolog import nolog
Used in 4 file(s):
  - DebugFramework\SystemDebug.py:16
  - S2T\Logger\ErrorReportClass.py:30
  - S2T\Logger\ErrorReport_legacy.py:21
  - S2T\Logger\ErrorReport_original_backup.py:17

Import: import ipccli
Used in 11 file(s):
  - DebugFramework\S2TMocks.py:254
  - DebugFramework\SystemDebug.py:3
  - S2T\ConfigsLoader.py:1
  - S2T\CoreManipulation.py (lines: 32, 114)
  - S2T\Logger\ErrorReport.py (lines: 49, 190)
  ... and 6 more files


================================================================================
Package: lxml
================================================================================

Import: from lxml import etree
Used in 1 file(s):
  - S2T\GetTesterCurves.py:52

Import: import lxml
Used in 1 file(s):
  - test_dependencies.py:85


================================================================================
Package: namednodes
================================================================================

Import: from namednodes import sv
Used in 5 file(s):
  - DebugFramework\S2TTestFramework.py:111
  - S2T\CoreManipulation.py (lines: 71, 94, 309, 1764)
  - S2T\Logger\ErrorReport_legacy.py:19
  - S2T\Logger\ErrorReport_original_backup.py:15
  - S2T\dpmChecks.py (lines: 165, 2717)

Import: import namednodes
Used in 11 file(s):
  - DebugFramework\SystemDebug.py:4
  - S2T\ConfigsLoader.py:2
  - S2T\CoreManipulation.py:29
  - S2T\Logger\ErrorReport.py (lines: 50, 183)
  - S2T\Logger\ErrorReportClass.py:27
  ... and 6 more files


================================================================================
Package: numpy
================================================================================

Import: import numpy
Used in 1 file(s):
  - test_dependencies.py:29

Import: import numpy as np
Used in 2 file(s):
  - DebugFramework\PPV\parsers\FrameworkAnalyzer.py:7
  - S2T\Tools\portid2ip.py:285


================================================================================
Package: openpyxl
================================================================================

Import: from openpyxl import Workbook
Used in 2 file(s):
  - DebugFramework\PPV\parsers\Frameworkparser.py:7
  - DebugFramework\PPV\utils\ExcelReportBuilder.py:6

Import: from openpyxl import load_workbook
Used in 6 file(s):
  - DebugFramework\PPV\parsers\MCAparser.py:4
  - DebugFramework\PPV\utils\FrameworkFileFix.py:6
  - DebugFramework\Storage_Handler\ReportUtils.py:1
  - DebugFramework\UI\ExperimentsForm.py:5
  - S2T\UI\ExperimentsForm.py:5
  ... and 1 more files

Import: from openpyxl.cell.rich_text import TextBlock, CellRichText
Used in 1 file(s):
  - DebugFramework\PPV\utils\ExcelReportBuilder.py:12

Import: from openpyxl.cell.text import InlineFont
Used in 1 file(s):
  - DebugFramework\PPV\utils\ExcelReportBuilder.py:11

Import: from openpyxl.styles import Border, Side
Used in 1 file(s):
  - DebugFramework\PPV\utils\ExcelReportBuilder.py:136

Import: from openpyxl.styles import PatternFill
Used in 3 file(s):
  - S2T\Logger\ErrorReportClass.py:17
  - S2T\Logger\ErrorReport_legacy.py:14
  - S2T\Logger\ErrorReport_original_backup.py:10

Import: from openpyxl.styles import PatternFill, Font, Alignment
Used in 2 file(s):
  - DebugFramework\PPV\parsers\Frameworkparser.py:8
  - DebugFramework\PPV\utils\ExcelReportBuilder.py:8

Import: from openpyxl.styles.colors import Color
Used in 4 file(s):
  - DebugFramework\PPV\utils\ExcelReportBuilder.py:377
  - S2T\Logger\ErrorReportClass.py:18
  - S2T\Logger\ErrorReport_legacy.py:15
  - S2T\Logger\ErrorReport_original_backup.py:11

Import: from openpyxl.utils import get_column_letter
Used in 3 file(s):
  - S2T\Logger\ErrorReportClass.py:19
  - S2T\Logger\ErrorReport_legacy.py:16
  - S2T\Logger\ErrorReport_original_backup.py:12

Import: from openpyxl.worksheet.datavalidation import DataValidation
Used in 2 file(s):
  - DebugFramework\UI\ExperimentsForm.py:7
  - S2T\UI\ExperimentsForm.py:7

Import: from openpyxl.worksheet.table import Table
Used in 2 file(s):
  - DebugFramework\UI\ExperimentsForm.py:6
  - S2T\UI\ExperimentsForm.py:6

Import: from openpyxl.worksheet.table import Table, TableStyleInfo
Used in 3 file(s):
  - DebugFramework\PPV\parsers\Frameworkparser.py:9
  - DebugFramework\PPV\parsers\MCAparser.py:5
  - DebugFramework\PPV\utils\ExcelReportBuilder.py:7

Import: import openpyxl
Used in 9 file(s):
  - DebugFramework\Automation_Flow\AutomationDesigner.py:20
  - DebugFramework\FileHandler.py:8
  - DebugFramework\Misc.py:6
  - DebugFramework\PPV\gui\AutomationDesigner.py:20
  - DebugFramework\PPV\gui\ExperimentBuilder.py:19
  ... and 4 more files


================================================================================
Package: pandas
================================================================================

Import: import pandas
Used in 1 file(s):
  - test_dependencies.py:22

Import: import pandas as pd
Used in 26 file(s):
  - DebugFramework\EFI\patternfinder.py:3
  - DebugFramework\FileHandler.py:7
  - DebugFramework\Misc.py:5
  - DebugFramework\PPV\Decoder\TransformJson.py:1
  - DebugFramework\PPV\Decoder\decoder.py:8
  ... and 21 more files


================================================================================
Package: pm
================================================================================

Import: import pm.pmutils.tools as cvt
Used in 1 file(s):
  - S2T\dpmChecks.py:62


================================================================================
Package: psutil
================================================================================

Import: import psutil
Used in 3 file(s):
  - DebugFramework\ExecutionHandler\utils\EmergencyCleanup.py:8
  - DebugFramework\ExecutionHandler\utils\ThreadsManager.py:9
  - test_dependencies.py:78


================================================================================
Package: pymongo
================================================================================

Import: from pymongo import MongoClient
Used in 1 file(s):
  - DebugFramework\Storage_Handler\DBClient.py:1

Import: import pymongo
Used in 1 file(s):
  - test_dependencies.py:50


================================================================================
Package: pytz
================================================================================

Import: import pytz
Used in 3 file(s):
  - DebugFramework\ExecutionHandler\utils\misc_utils.py:4
  - DebugFramework\SystemDebug.py:10
  - test_dependencies.py:71


================================================================================
Package: registers
================================================================================

Import: import registers as regs
Used in 1 file(s):
  - S2T\ConfigsLoader.py:44


================================================================================
Package: strategy
================================================================================

Import: import strategy as strat
Used in 1 file(s):
  - S2T\ConfigsLoader.py:46


================================================================================
Package: svtools
================================================================================

Import: from svtools.common import baseaccess
Used in 1 file(s):
  - S2T\Logger\ErrorReportClass.py:26

Import: import svtools
Used in 1 file(s):
  - test_dependencies.py:109


================================================================================
Package: tabulate
================================================================================

Import: from tabulate import tabulate
Used in 16 file(s):
  - DebugFramework\ExecutionHandler\utils\FrameworkUtils.py:2
  - DebugFramework\Misc.py:7
  - DebugFramework\PPV\gui\PPVFrameworkReport.py:7
  - DebugFramework\PPV\parsers\Frameworkparser.py:5
  - DebugFramework\SystemDebug.py:8
  ... and 11 more files

Import: import tabulate
Used in 1 file(s):
  - test_dependencies.py:64


================================================================================
Package: toolext
================================================================================

Import: from toolext.server_ip_debug.ccf import ccf
Used in 2 file(s):
  - S2T\Logger\ErrorReport_legacy.py:79
  - S2T\Logger\ErrorReport_original_backup.py:72

Import: from toolext.server_ip_debug.llc import llc ## Not available for CWF at the moment
Used in 2 file(s):
  - S2T\Logger\ErrorReport_legacy.py:88
  - S2T\Logger\ErrorReport_original_backup.py:81

Import: from toolext.server_ip_debug.punit import punit
Used in 2 file(s):
  - S2T\Logger\ErrorReport_legacy.py (lines: 74, 81)
  - S2T\Logger\ErrorReport_original_backup.py (lines: 67, 74)

Import: from toolext.server_ip_debug.ula import ula
Used in 2 file(s):
  - S2T\Logger\ErrorReport_legacy.py:83
  - S2T\Logger\ErrorReport_original_backup.py:76

Import: import toolext
Used in 1 file(s):
  - test_dependencies.py:116

Import: import toolext.bootscript.boot as b
Used in 4 file(s):
  - DebugFramework\S2TMocks.py:341
  - DebugFramework\S2TTestFramework.py:98
  - S2T\CoreManipulation.py:42
  - S2T\dpmChecks.py:60

Import: import toolext.bootscript.toolbox.fuse_utility as fu
Used in 1 file(s):
  - S2T\dpmChecks.py:61

Import: import toolext.bootscript.toolbox.power_control.USBPowerSplitterFullControl as pwsc
Used in 1 file(s):
  - S2T\dpmChecks.py (lines: 1984, 1991, 1998)


================================================================================
Package: xlwings
================================================================================

Import: import xlwings
Used in 1 file(s):
  - test_dependencies.py:43

Import: import xlwings as xw
Used in 2 file(s):
  - DebugFramework\PPV\gui\PPVTools.py:9
  - DebugFramework\PPV\parsers\MCAparser.py:8
