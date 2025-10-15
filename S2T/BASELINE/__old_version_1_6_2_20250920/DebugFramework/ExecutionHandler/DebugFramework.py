
import time
import pandas as pd
import os
import shutil


import users.gaespino.dev.S2T.CoreManipulation as gcm
import users.gaespino.dev.S2T.dpmChecks as dpm
import users.gaespino.dev.S2T.SetTesterRegs as s2t

import users.gaespino.dev.DebugFramework.SerialConnection as ser
import users.gaespino.dev.DebugFramework.MaskEditor as gme
import users.gaespino.dev.DebugFramework.FileHandler as fh
import users.gaespino.dev.DebugFramework.UI.ControlPanel as fcp

import importlib

importlib.reload(ser)
importlib.reload(gme)
importlib.reload(fh)
importlib.reload(fcp)


## Folders
script_dir = os.path.dirname(os.path.abspath(__file__))
base_folder = 'C:\\SystemDebug'
ttl_source = os.path.join(script_dir, 'TTL')
shmoos_source = os.path.join(script_dir, 'Shmoos')
ttl_dest = os.path.join(base_folder, 'TTL')
shmoos_dest = os.path.join(base_folder, 'Shmoos')
logs_dest = os.path.join(base_folder, 'Logs')

PYTHONSV_CONSOLE_LOG = r"C:\Temp\PythonSVLog.log"


# Usage Examples:
if __name__ == "__main__":
    # Create framework instance
    framework = Framework()
    
    # Example 1: Simple loop test
    results = framework.Loops(
        loops=5,
        name="My Loop Test",
        volt_type="vbump",
        volt_IA=1.2,
        freq_ia=2400
    )
    
    # Example 2: Sweep test
    results = framework.Sweep(
        ttype='frequency',
        domain='ia',
        start=1600,
        end=3200,
        step=200,
        name="Frequency Sweep",
        volt_IA=1.1
    )
    
    # Example 3: Using static methods (for interfaces)
    Framework.platform_check("8", "192.168.0.2")
    recipes = Framework.Recipes("test_config.xlsx")
    Framework.RecipeLoader(recipes)