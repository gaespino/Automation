"""
PPV Tools GUI Package
Contains all graphical user interface modules for PPV analysis tools.
These modules require tkinter and are only available in desktop environments.
"""

try:
    from .PPVTools import Tools
    from .PPVLoopChecks import PTCReportGUI
    from .PPVDataChecks import PPVReportGUI
    from .PPVFileHandler import FileHandlerGUI
    from .PPVFrameworkReport import FrameworkReportBuilder
except ImportError:
    # tkinter or other desktop dependency not available (e.g. CaaS/headless)
    Tools = None
    PTCReportGUI = None
    PPVReportGUI = None
    FileHandlerGUI = None
    FrameworkReportBuilder = None

__all__ = [
    'Tools',
    'PTCReportGUI',
    'PPVReportGUI',
    'FileHandlerGUI',
    'FrameworkReportBuilder',
]
