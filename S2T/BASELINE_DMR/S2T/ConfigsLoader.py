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
DEVICE_NAME = sv.socket0.target_info["device_name"].upper()

if 'DMR' in DEVICE_NAME:
	PRODUCT_CONFIG = DEVICE_NAME
	PRODUCT_CHOP = None
	PRODUCT_VARIANT = None
	SELECTED_PRODUCT = PRODUCT_CONFIG.strip('_CLTAP')
else:
	PRODUCT_CONFIG = sv.socket0.target_info["segment"].upper()
	PRODUCT_CHOP = sv.socket0.target_info["chop"].upper()
	PRODUCT_VARIANT = sv.socket0.target_info["variant"].upper()
	SELECTED_PRODUCT = PRODUCT_CONFIG.strip(PRODUCT_VARIANT)

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
PRODUCT_PATH = os.path.join(ROOT_PATH, 'product_specific', SELECTED_PRODUCT.lower())
MANAGERS_PATH = os.path.join(ROOT_PATH, 'managers')

sys.path.append(PRODUCT_PATH)
sys.path.append(MANAGERS_PATH)

# Imports the configuration arrays from ROOT_PATH\product_specific\{PRODUCT}\
import configs as pe
import registers as regs
import functions as pf
import strategy as strat

importlib.reload(pe)
importlib.reload(regs)
importlib.reload(pf)
importlib.reload(module=strat)

_configs = pe.configurations(SELECTED_PRODUCT)

CONFIG = _configs.init_product_specific()

# This an optional INIT Method for products such as DMR

if PRODUCT_CHOP == None:
	PRODUCT_CHOP = _configs.get_chop(sv)

if PRODUCT_VARIANT == None:
	PRODUCT_VARIANT = _configs.get_variant(sv)

class ProductConfiguration:
	"""
	Centralized product configuration manager.
	Provides clean access to all product-specific settings through a single object.
	
	Usage:
		from ConfigsLoader import config
		
		# Access product info
		product_name = config.PRODUCT_CONFIG
		
		# Access configuration
		max_cores = config.MAXCORESCHIP
		
		# Access fuses
		fuses = config.FUSES
		
		# Access functions and registers
		functions = config.get_functions()
		registers = config.get_registers()
	"""
	
	def __init__(self, config_dict, fuses_dict, framework_dict, features_dict):
		"""Initialize product configuration with all settings"""
		# Product identification
		self.PRODUCT_CONFIG = PRODUCT_CONFIG
		self.PRODUCT_CHOP = PRODUCT_CHOP
		self.PRODUCT_VARIANT = PRODUCT_VARIANT
		self.SELECTED_PRODUCT = SELECTED_PRODUCT
		self.ROOT_PATH = ROOT_PATH
		self.PRODUCT_PATH = PRODUCT_PATH
		
		# Core configuration dictionary
		self.CONFIG = config_dict
		
		# Configuration variables
		self.ConfigFile = config_dict['CONFIGFILE']
		self.CORESTRING = config_dict['CORESTRING']
		self.CORETYPES = config_dict['CORETYPES']
		self.CHIPCONFIG = config_dict['CORETYPES'][PRODUCT_CONFIG]['config']
		self.MAXCORESCHIP = config_dict['CORETYPES'][PRODUCT_CONFIG]['maxcores']
		self.MAXLOGICAL = config_dict['MAXLOGICAL']
		self.MAXPHYSICAL = config_dict['MAXPHYSICAL']
		self.classLogical2Physical = config_dict['LOG2PHY']
		self.physical2ClassLogical = config_dict['PHY2LOG']
		self.Physical2apicIDAssignmentOrder10x5 = config_dict['PHY2APICID']
		self.phys2colrow = config_dict['PHY2COLROW']
		self.skip_physical_modules = config_dict['SKIPPHYSICAL']
		self.skip_cores_10x5 = self.skip_physical_modules
		# DMR specific configurations
		if 'DMR' in DEVICE_NAME:
			self.MODS_PER_CBB = self.CORETYPES[PRODUCT_CONFIG]['mods_per_cbb']
			self.MODS_PER_COMPUTE = self.CORETYPES[PRODUCT_CONFIG]['mods_per_compute']
			self.MODS_ACTIVE_PER_CBB = self.CORETYPES[PRODUCT_CONFIG]['active_per_cbb']
			self.MAX_CBBS = self.CORETYPES[PRODUCT_CONFIG]['max_cbbs']
			self.MAX_IMHS = self.CORETYPES[PRODUCT_CONFIG]['max_imhs']
		else:
			self.MODS_PER_CBB = None
			self.MODS_PER_COMPUTE = None
			self.MODS_ACTIVE_PER_CBB = None
			self.MAX_CBBS = None
			self.MAX_IMHS = None
			
		# Product fuses
		self.FUSES = fuses_dict
		self.DEBUGMASK = fuses_dict['DebugMasks']
		self.PSEUDOCONDFIGS = fuses_dict['pseudoConfigs']
		self.BURINFUSES = fuses_dict['BurnInFuses']
		self.FUSE_INSTANCE = fuses_dict['fuse_instance']
		self.CFC_RATIO_CURVES = fuses_dict['cfc_ratio_curves']
		self.CFC_VOLTAGE_CURVES = fuses_dict['cfc_voltage_curves']
		self.IA_RATIO_CURVES = fuses_dict['ia_ratio_curves']
		self.IA_RATIO_CONFIG = fuses_dict['ia_ratios_config']
		self.IA_VOLTAGE_CURVES = fuses_dict['ia_voltage_curves']
		self.FUSES_600W_COMP = fuses_dict['fuses_600w_comp']
		self.FUSES_600W_IO = fuses_dict['fuses_600w_io']
		self.HIDIS_COMP = fuses_dict['htdis_comp']
		self.HTDIS_IO = fuses_dict['htdis_io']
		self.VP2INTERSECT = fuses_dict['vp2intersect']
		
		# Framework variables
		self.FRAMEWORKVARS = framework_dict
		self.LICENSE_DICT = framework_dict['core_license_dict']
		self.LICENSE_S2T_MENU = framework_dict['license_dict']
		self.LICENSE_LEVELS = framework_dict['core_license_levels']
		self.SPECIAL_QDF = framework_dict['qdf600']
		self.VALIDCLASS = framework_dict['ValidClass']
		self.CUSTOMS = framework_dict['customs']
		self.VALIDROWS = framework_dict['ValidRows']
		self.VALIDCOLS = framework_dict['ValidCols']
		self.BOOTSCRIPT_DATA = framework_dict['bootscript_data']
		self.ATE_MASKS = framework_dict['ate_masks']
		self.ATE_CONFIG = framework_dict['ate_config']
		self.DIS2CPM_MENU = framework_dict['dis2cpm_menu']
		self.DIS1CPM_MENU = framework_dict['dis1cpm_menu']
		self.DIS2CPM_DICT = framework_dict['dis2cpm_dict']
		self.DIS1CPM_DICT = framework_dict['dis1cpm_dict']
		self.RIGHT_HEMISPHERE = framework_dict['righthemisphere']
		self.LEFT_HEMISPHERE = framework_dict['lefthemisphere']
		
		# Framework features
		self.FRAMEWORK_FEATURES = features_dict
		
		# Cache for functions and registers
		self._functions = None
		self._registers = None
		self._strategy = None
	
	def get_functions(self):
		"""Get product-specific functions (lazy loaded)"""
		if self._functions is None:
			self._functions = pf.functions()
		return self._functions
	
	def get_registers(self):
		"""Get product-specific registers (lazy loaded)"""
		if self._registers is None:
			self._registers = regs.registers()
		return self._registers
	
	def get_strategy(self):
		"""
		Get product-specific strategy (lazy loaded).
		
		Returns:
			ProductStrategy implementation for the current product
		"""
		if self._strategy is None:
			# Import the appropriate strategy based on product
			try:
				if 'GNR' in SELECTED_PRODUCT.upper():
					
					self._strategy = strat.GNRStrategy(self)
				
				elif 'CWF' in SELECTED_PRODUCT.upper():
					
					self._strategy = strat.CWFStrategy(self)
				
				elif 'DMR' in SELECTED_PRODUCT.upper():
					
					self._strategy = strat.DMRStrategy(self)
				else:
					raise ValueError(f"No strategy implementation found for product: {SELECTED_PRODUCT}")
			except Exception as e:
				print(f"Warning: Could not load product strategy: {e}")
				# Return None or a default strategy
				self._strategy = None
		return self._strategy
	
	def reload(self):
		"""Reload all product-specific modules"""
		importlib.reload(pe)
		importlib.reload(regs)
		importlib.reload(pf)
		self._functions = None
		self._registers = None
		self._strategy = None


# Initialize the global configuration object
FUSES = _configs.init_product_fuses()
FRAMEWORKVARS = _configs.init_framework_vars()
FRAMEWORK_FEATURES = _configs.init_framework_features()

config = ProductConfiguration(CONFIG, FUSES, FRAMEWORKVARS, FRAMEWORK_FEATURES)


# ============================================================================
# BACKWARD COMPATIBILITY LAYER (for existing code)
# ============================================================================
# These can be gradually removed as code is updated to use config object

ConfigFile = config.ConfigFile
CORESTRING = config.CORESTRING
CORETYPES = config.CORETYPES
CHIPCONFIG = config.CHIPCONFIG
MAXCORESCHIP = config.MAXCORESCHIP
MAXLOGICAL = config.MAXLOGICAL
MAXPHYSICAL = config.MAXPHYSICAL
classLogical2Physical = config.classLogical2Physical
physical2ClassLogical = config.physical2ClassLogical
Physical2apicIDAssignmentOrder10x5 = config.Physical2apicIDAssignmentOrder10x5
phys2colrow = config.phys2colrow
skip_physical_modules = config.skip_physical_modules
skip_cores_10x5 = skip_physical_modules # Duplicate for old product variable name

# DMR specific configurations
if 'DMR' in DEVICE_NAME:
	MODS_PER_CBB = config.MODS_PER_CBB
	MODS_PER_COMPUTE = config.MODS_PER_COMPUTE
	MODS_ACTIVE_PER_CBB = config.MODS_ACTIVE_PER_CBB
	MAX_CBBS = config.MAX_CBBS
	MAX_IMHS = config.MAX_IMHS
else:
	MODS_PER_CBB = None
	MODS_PER_COMPUTE = None
	MODS_ACTIVE_PER_CBB = None
	MAX_CBBS = None
	MAX_IMHS = None

DEBUGMASK = config.DEBUGMASK
PSEUDOCONDFIGS = config.PSEUDOCONDFIGS
BURINFUSES = config.BURINFUSES
FUSE_INSTANCE = config.FUSE_INSTANCE
CFC_RATIO_CURVES = config.CFC_RATIO_CURVES
CFC_VOLTAGE_CURVES = config.CFC_VOLTAGE_CURVES
IA_RATIO_CURVES = config.IA_RATIO_CURVES
IA_RATIO_CONFIG = config.IA_RATIO_CONFIG
IA_VOLTAGE_CURVES = config.IA_VOLTAGE_CURVES
FUSES_600W_COMP = config.FUSES_600W_COMP
FUSES_600W_IO = config.FUSES_600W_IO
HIDIS_COMP = config.HIDIS_COMP
HTDIS_IO = config.HTDIS_IO
VP2INTERSECT = config.VP2INTERSECT

LICENSE_DICT = config.LICENSE_DICT
LICENSE_S2T_MENU = config.LICENSE_S2T_MENU
LICENSE_LEVELS = config.LICENSE_LEVELS
SPECIAL_QDF = config.SPECIAL_QDF
VALIDCLASS = config.VALIDCLASS
CUSTOMS = config.CUSTOMS
VALIDROWS = config.VALIDROWS
VALIDCOLS = config.VALIDCOLS
BOOTSCRIPT_DATA = config.BOOTSCRIPT_DATA
ATE_MASKS = config.ATE_MASKS
ATE_CONFIG = config.ATE_CONFIG
DIS2CPM_MENU = config.DIS2CPM_MENU
DIS2CPM_DICT = config.DIS2CPM_DICT
DIS1CPM_MENU = config.DIS1CPM_MENU
DIS1CPM_DICT = config.DIS1CPM_DICT
RIGHT_HEMISPHERE = config.RIGHT_HEMISPHERE
LEFT_HEMISPHERE = config.LEFT_HEMISPHERE


def LoadFunctions():
	"""Legacy function - use config.get_functions() instead"""
	return config.get_functions()


def LoadRegisters():
	"""Legacy function - use config.get_registers() instead"""
	return config.get_registers()