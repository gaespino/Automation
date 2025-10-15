"""
Debug Framework - Main Entry Point
Maintains backward compatibility while providing modular architecture
"""

# Core S2T and utils imports (maintain original functionality)
import users.gaespino.dev.S2T.CoreManipulation as gcm
import users.gaespino.dev.S2T.dpmChecks as dpm
import users.gaespino.dev.S2T.SetTesterRegs as s2t
import users.gaespino.dev.DebugFramework.SerialConnection as ser
import users.gaespino.dev.DebugFramework.MaskEditor as gme
import users.gaespino.dev.DebugFramework.FileHandler as fh
import users.gaespino.dev.DebugFramework.UI.ControlPanel as fcp
import users.gaespino.dev.S2T.Tools.utils as s2tutils
import importlib

# Reload modules for development
importlib.reload(ser)
importlib.reload(gme)
importlib.reload(fh)
importlib.reload(fcp)
importlib.reload(s2tutils)

# Framework imports
from framework.main_framework import Framework
from framework.external_api import FrameworkExternalAPI
from utils.misc_utils import initscript, replace_files, currentTime, DebugMask

# Initialize framework
initscript()

#######################################################
########## Quick Access Framework Functions
#######################################################

def Recipes(path=r'C:\Temp\DebugFrameworkTemplate.xlsx'):
    """Load recipes from file"""
    return Framework.Recipes(path)

def RecipeLoader(data, extmask=None, summary=True, skip=[], upload_to_database=True):
    """Load and execute multiple recipes"""
    Framework.RecipeLoader(data, extmask, summary, skip, upload_to_database)

#######################################################
########## User Interface Calls
#######################################################

def ControlPanel():
    """Launch control panel UI"""
    fcp.run(Framework)

def TTLMacroTest():
    """Launch TTL macro test UI"""
    Framework.Test_Macros_UI()

#######################################################
########## Masking Script 
#######################################################

def DebugMask(basemask=None, root=None, callback=None):
    """Create debug mask interface"""
    die = dpm.product_str()
    masks = dpm.fuses(rdFuses=True, sktnum=[0], printFuse=False) if basemask is None else basemask

    # Check for all configurations
    compute0_core_hex = str(masks["ia_compute_0"]) if masks["ia_compute_0"] is not None else None
    compute0_cha_hex = str(masks["llc_compute_0"]) if masks["llc_compute_0"] is not None else None
    compute1_core_hex = str(masks["ia_compute_1"]) if masks["ia_compute_1"] is not None else None
    compute1_cha_hex = str(masks["llc_compute_1"]) if masks["llc_compute_1"] is not None else None
    compute2_core_hex = str(masks["ia_compute_2"]) if masks["ia_compute_2"] is not None else None
    compute2_cha_hex = str(masks["llc_compute_2"]) if masks["llc_compute_2"] is not None else None

    newmask = gme.Masking(root, compute0_core_hex, compute0_cha_hex, compute1_core_hex, 
                         compute1_cha_hex, compute2_core_hex, compute2_cha_hex, 
                         product=die.upper(), callback=callback)

    return newmask

# Export main classes for external use
__all__ = [
    'Framework',
    'FrameworkExternalAPI', 
    'Recipes',
    'RecipeLoader',
    'ControlPanel',
    'TTLMacroTest',
    'DebugMask',
    'currentTime',
    'initscript',
    'replace_files'
]