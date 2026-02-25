"""
PPV (Pre-Production Validation) Tools Package

A comprehensive suite of tools for PPV data analysis and management.

Package Structure:
- gui: Graphical user interface modules
- parsers: Data parsing and analysis modules
- utils: Utility functions and helper modules
- api: API integration modules
- Decoder: MCA decoder modules
- MCChecker: MCA checker tools
- DebugScripts: Debugging and utility scripts

Main Entry Point:
    Run 'python run.py' to start the PPV Tools Hub
"""

__version__ = "2.0.0"
__author__ = "Gaespino"

# GUI imports are optional — tkinter is not available in CaaS/headless environments.
# The web app uses the parsers/utils/api backends directly; GUI classes are only
# needed when running the standalone Tkinter app (python run.py).
try:
    from .gui import (
        Tools,
        PTCReportGUI,
        PPVReportGUI,
        FileHandlerGUI,
        FrameworkReportBuilder,
    )
    from .api import dpmbGUI
    _GUI_AVAILABLE = True
except ImportError:
    _GUI_AVAILABLE = False
    Tools = None
    PTCReportGUI = None
    PPVReportGUI = None
    FileHandlerGUI = None
    FrameworkReportBuilder = None
    dpmbGUI = None

__all__ = [
    'Tools',
    'PTCReportGUI',
    'PPVReportGUI',
    'FileHandlerGUI',
    'FrameworkReportBuilder',
    'dpmbGUI',
    '_GUI_AVAILABLE',
]
