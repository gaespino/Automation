"""
Run PPV Experiment Builder as a standalone application

This script launches the Experiment Builder tool independently
from the main PPV Tools Hub.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.ExperimentBuilder import ExperimentBuilderGUI

if __name__ == "__main__":
    print("="*70)
    print("  PPV Experiment Builder")
    print("  Create JSON configurations for Debug Framework Control Panel")
    print("="*70)
    print()
    
    app = ExperimentBuilderGUI()
    app.run()
