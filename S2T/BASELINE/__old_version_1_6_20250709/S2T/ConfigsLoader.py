import ipccli
import namednodes
import sys
import os
import importlib

verbose = False

ipc = ipccli.baseaccess()
itp = ipc
sv = namednodes.sv #shortcut
sv.initialize()
product_functions = None

# Product Data Collection needed to init variables on script --
PRODUCT_CONFIG = sv.socket0.target_info["segment"].upper()
PRODUCT_CHOP = sv.socket0.target_info["chop"].upper()
PRODUCT_VARIANT = sv.socket0.target_info["variant"].upper()

SELECTED_PRODUCT = PRODUCT_CONFIG.strip(PRODUCT_VARIANT)
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
PRODUCT_PATH = os.path.join(ROOT_PATH, 'product_specific', SELECTED_PRODUCT.lower())

sys.path.append(PRODUCT_PATH)

# Imports the configuration arrays from ROOT_PATH\product_specific\{PRODUCT}\
import configs as pe
import registers as regs
import functions as pf

importlib.reload(pe)
importlib.reload(regs)
importlib.reload(pf)

_configs = pe.configurations(SELECTED_PRODUCT)

CONFIG = _configs.init_product_specific()

# Configuration Variables Init
ConfigFile = CONFIG['CONFIGFILE']
CORESTRING = CONFIG['CORESTRING']
CORETYPES = CONFIG['CORETYPES']
CHIPCONFIG = CONFIG['CORETYPES'][PRODUCT_CONFIG]['config']
MAXCORESCHIP = CONFIG['CORETYPES'][PRODUCT_CONFIG]['maxcores']
MAXLOGICAL = CONFIG['MAXLOGICAL']
MAXPHYSICAL = CONFIG['MAXPHYSICAL']
classLogical2Physical = CONFIG['LOG2PHY']
physical2ClassLogical = CONFIG['PHY2LOG']
Physical2apicIDAssignmentOrder10x5 = CONFIG['PHY2APICID']
phys2colrow = CONFIG['PHY2COLROW']
skip_cores_10x5 =CONFIG['SKIPPHYSICAL']


# Product Fuses Init
FUSES = _configs.init_product_fuses()

DEBUGMASK = FUSES['DebugMasks']
PSEUDOCONDFIGS = FUSES['pseudoConfigs']
BURINFUSES = FUSES['BurnInFuses']
FUSE_INSTANCE = FUSES['fuse_instance']
CFC_RATIO_CURVES = FUSES['cfc_ratio_curves']
CFC_VOLTAGE_CURVES = FUSES['cfc_voltage_curves']
IA_RATIO_CURVES = FUSES['ia_ratio_curves']
IA_RATIO_CONFIG = FUSES['ia_ratios_config']
IA_VOLTAGE_CURVES = FUSES['ia_voltage_curves']
FUSES_600W_COMP = FUSES['fuses_600w_comp']
FUSES_600W_IO = FUSES['fuses_600w_io']
HIDIS_COMP = FUSES['htdis_comp']
HTDIS_IO = FUSES['htdis_io']
VP2INTERSECT = FUSES['vp2intersect']

# Framework Variables Init
FRAMEWORKVARS = _configs.init_framework_vars()

LICENSE_DICT = FRAMEWORKVARS['core_license_dict']
LICENSE_S2T_MENU = FRAMEWORKVARS['license_dict']
LICENSE_LEVELS = FRAMEWORKVARS['core_license_levels']
SPECIAL_QDF = FRAMEWORKVARS['qdf600']
VALIDCLASS = FRAMEWORKVARS['ValidClass']
CUSTOMS = FRAMEWORKVARS['customs']
VALIDROWS = FRAMEWORKVARS['ValidRows']
VALIDCOLS = FRAMEWORKVARS['ValidCols']
BOOTSCRIPT_DATA = FRAMEWORKVARS['bootscript_data']
ATE_MASKS = FRAMEWORKVARS['ate_masks']
ATE_CONFIG = FRAMEWORKVARS['ate_config']
DIS2CPM_MENU = FRAMEWORKVARS['dis2cpm_menu']
DIS2CPM_DICT = FRAMEWORKVARS['dis2cpm_dict']
RIGHT_HEMISPHERE = FRAMEWORKVARS['righthemisphere']
LEFT_HEMISPHERE = FRAMEWORKVARS['lefthemisphere']

# Framework Features Init
FRAMEWORK_FEATURES = _configs.init_framework_features()

def LoadFunctions():
    #module_name = 'functions'
    #f  = importlib.import_module(module_name)  
    f = pf.functions()
    return f

def LoadRegisters():
    r = regs.registers()
    return r