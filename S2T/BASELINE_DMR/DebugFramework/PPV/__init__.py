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
    Run 'python run_ppv_tools.py' to start the PPV Tools Hub
"""

__version__ = "2.0.0"
__author__ = "PPV Tools Team"

# Import main components for easy access
from .gui import (
    Tools,
    PTCReportGUI,
    PPVReportGUI,
    FileHandlerGUI,
    FrameworkReportBuilder
)

from .api import dpmbGUI

__all__ = [
    'Tools',
    'PTCReportGUI',
    'PPVReportGUI',
    'FileHandlerGUI',
    'FrameworkReportBuilder',
    'dpmbGUI'
]
