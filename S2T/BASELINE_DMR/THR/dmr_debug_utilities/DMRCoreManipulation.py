"""
Overview:
This script is designed to facilitate the configuration and booting of systems with specific core and slice masking requirements. 
It provides tools for manipulating system configurations, executing bootscripts, and verifying fuse settings. The script supports 
various configurations for different product types and includes options for fast booting and fuse overrides.

Key Features:
- Core and slice masking for system configuration
- Bootscripts execution with retry logic
- Fuse override and verification
- Support for multiple product types and configurations
- Detailed logging and error handling

Changelog:
- Version 1.7 (3/7/2025): DMR Initial Release -- Matches CWF Functionality

"""


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== Modules/Libraries Imports =========================================================================#
#========================================================================================================#

import math
import namednodes
import time
import ipccli
import sys
import itpii
from tabulate import tabulate
from colorama import Fore, Back, Style
import toolext.bootscript.boot as b
import os
import importtlib

print ("DMR Core Manipulation")


## Custom Modules -- Lets move them first to Dev then back to DMR folder

import users.gaespino.dev.S2T.dpmChecks as dpm # Need to port it to DMR
import users.gaespino.dev.S2T.ConfigsLoader as LoadConfig ## Need to port it to DMR

importlib.reload(LoadConfig)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=================================== IPC AND SV SETUP ===================================================#
#========================================================================================================#

from namednodes import sv
from ipccli import BitData

ipc = None
api = None

sv = None
sv = namednodes.sv #shortcut
sv.initialize()

def _get_global_sv():
  # Lazy initialize for the global SV instance  
  global sv
  if sv is None:
    from namednodes import sv
    sv.initialize()
    #import components.socket as skt
    #skts = skt.getAll()
  if not sv.sockets:
    print("No socketlist detected. Restarting baseaccess and sv.refresh")
    sv.initialize()
    sv.refresh()
  return sv

def _get_global_ipc():
  # Lazy initialize for the global IPC instance
  global ipc
  if ipc is None:
    import ipccli
    ipc = ipccli.baseaccess()
  return ipc

ipc = _get_global_ipc()
sv = _get_global_sv()
itp = itpii.baseaccess()
ipc = ipccli.baseaccess()
base = ipccli.baseaccess()

sv_refreshed = True
verbose = False
debug = False

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== SELECTED PRODUCT INITIALIZATION ========================================================#
#========================================================================================================#

# Product Data Collection needed to init variables on script --
PRODUCT_CONFIG = LoadConfig.PRODUCT_CONFIG
PRODUCT_CHOP  = LoadConfig.PRODUCT_CHOP
PRODUCT_VARIANT = LoadConfig.PRODUCT_VARIANT
SELECTED_PRODUCT = LoadConfig.SELECTED_PRODUCT

CONFIG = LoadConfig.CONFIG

# Configuration Variables Init
ConfigFile = LoadConfig.ConfigFile
CORESTRING = LoadConfig.CORESTRING
CORETYPES = LoadConfig.CORETYPES
CHIPCONFIG = LoadConfig.CHIPCONFIG
MAXCORESCHIP = LoadConfig.MAXCORESCHIP
MAXLOGICAL = LoadConfig.MAXLOGICAL
MAXPHYSICAL = LoadConfig.MAXPHYSICAL
classLogical2Physical = LoadConfig.classLogical2Physical
physical2ClassLogical = LoadConfig.physical2ClassLogical
Physical2apicIDAssignmentOrder10x5 = LoadConfig.Physical2apicIDAssignmentOrder10x5
phys2colrow = LoadConfig.phys2colrow
skip_cores_10x5 = LoadConfig.skip_cores_10x5

# DMR Architecture Constants - 
TOTAL_MODULES_PER_CBB = LoadConfig.MODS_PER_CBB
TOTAL_MODULES_PER_COMPUTE = LoadConfig.MODS_PER_COMPUTE
TOTAL_ACTIVE_MODULES_PER_CBB = LoadConfig.MODS_ACTIVE_PER_CBB
TOTAL_CBBS = LoadConfig.MAX_CBBS
TOTAL_IMHS = LoadConfig.MAX_IMHS

# Product Fuses Init
FUSES = LoadConfig.FUSES

DEBUGMASK = LoadConfig.DEBUGMASK
PSEUDOCONDFIGS = LoadConfig.PSEUDOCONDFIGS
BURINFUSES = LoadConfig.BURINFUSES
FUSE_INSTANCE = LoadConfig.FUSE_INSTANCE
CFC_RATIO_CURVES = LoadConfig.CFC_RATIO_CURVES
CFC_VOLTAGE_CURVES = LoadConfig.CFC_VOLTAGE_CURVES
IA_RATIO_CURVES = LoadConfig.IA_RATIO_CURVES
IA_RATIO_CONFIG = LoadConfig.IA_RATIO_CONFIG
IA_VOLTAGE_CURVES = LoadConfig.IA_VOLTAGE_CURVES
FUSES_600W_COMP = LoadConfig.FUSES_600W_COMP
FUSES_600W_IO = LoadConfig.FUSES_600W_IO
HIDIS_COMP = LoadConfig.HIDIS_COMP
HTDIS_IO = LoadConfig.HTDIS_IO
VP2INTERSECT = LoadConfig.VP2INTERSECT

# Framework Variables Init
FRAMEWORKVARS = LoadConfig.FRAMEWORKVARS
LICENSE_DICT = LoadConfig.LICENSE_DICT
LICENSE_S2T_MENU = LoadConfig.LICENSE_S2T_MENU
LICENSE_LEVELS = LoadConfig.LICENSE_LEVELS
SPECIAL_QDF = LoadConfig.SPECIAL_QDF
VALIDCLASS = LoadConfig.VALIDCLASS
CUSTOMS = LoadConfig.CUSTOMS
VALIDROWS = LoadConfig.VALIDROWS
VALIDCOLS = LoadConfig.VALIDCOLS
BOOTSCRIPT_DATA = LoadConfig.BOOTSCRIPT_DATA

# Framework Features Init
FRAMEWORK_FEATURES = LoadConfig.FRAMEWORK_FEATURES

# Product Specific Functions Load
pf = LoadConfig.LoadFunctions()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== CONSTANTS AND GLOBAL VARIABLES =========================================================#
#========================================================================================================#

#DMR globals
global_ia_fw_p1=None
global_ia_fw_pn=None
global_ia_fw_pm=None
global_ia_fw_pboot=None
global_ia_fw_pturbo=None
global_ia_vf_curves=None
global_ia_imh_p1=None
global_ia_imh_pn=None
global_ia_imh_pm=None
global_ia_imh_pturbo=None
global_cfc_fw_p0=None
global_cfc_fw_p1=None
global_cfc_fw_pm=None
global_cfc_cbb_p0=None
global_cfc_cbb_p1=None
global_cfc_cbb_pm=None
global_cfc_io_p0=None
global_cfc_io_p1=None
global_cfc_io_pm=None
global_cfc_mem_p0=None
global_cfc_mem_p1=None
global_cfc_mem_pm=None

global_boot_stop_after_mrc=None
# global_ht_dis=None
global_acode_dis=None
global_fixed_core_freq=None
global_ia_p0=None
global_ia_p1=None
global_ia_pn=None
global_ia_pm=None
global_cfc_p0=None
global_cfc_p1=None
global_cfc_pn=None
global_cfc_pm=None
global_slice_core = None
global_io_p0=None
global_io_p1=None
global_io_pn=None
global_io_pm=None
global_fixed_mesh_freq=None
global_fixed_io_freq=None
global_avx_mode=None
global_dry_run=False
global_boot_extra=""

# Including Voltages
global_fixed_core_volt=None
global_fixed_cfc_volt=None
global_fixed_hdc_volt=None
global_fixed_cfcio_volt=None
global_fixed_ddrd_volt=None
global_fixed_ddra_volt=None
global_vbumps_configuration=None
global_u600w = None
_boot_string=""

# Boot Breaks option
AFTER_MRC_POST = 0xbf000000
#EFI_POST = 0x57000000
#EFI_POST = 0xef0000ff

EFI_POST = 0x57000000
LINUX_POST = 0x58000000
BOOTSCRIPT_RETRY_TIMES = 3
BOOTSCRIPT_RETRY_DELAY = 60
MRC_POSTCODE_WT = 30
EFI_POSTCODE_WT = 60
MRC_POSTCODE_CHECK_COUNT = 5
EFI_POSTCODE_CHECK_COUNT = 10

# Boot Breaks option
BOOT_STOP_POSTCODE = 0x0
BOOT_POSTCODE_WT = 30
BOOT_POSTCODE_CHECK_COUNT = 10


def reset_globals():
	'''
	Resets global variables used in _boot and _fastboot
	'''
	global global_boot_stop_after_mrc
	# global global_ht_dis
	global global_acode_dis
	global global_fixed_core_freq
	global global_fixed_mesh_freq
	global global_fixed_io_freq
	global global_avx_mode
	global global_dry_run
	global_boot_stop_after_mrc=None
	# global_ht_dis=None
	global_acode_dis=None
	global_fixed_core_freq=None
	global_fixed_mesh_freq=None
	global_fixed_io_freq=None
	global_avx_mode=None
	global_dry_run=False
	print("Global variables reset.")



#---------------------------------------

#classLogical2Physical = {0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,11:11,12:12,13:13,14:14,15:15,16:16,17:17,18:18,19:19,20:20,21:21,22:22,23:23,24:24,25:25,26:26,27:27,28:28,29:29,30:30,31:31}
#physical2ClassLogical = {value: key for key, value in classLogical2Physical.items()}
#phys2colrow= {0: [0, 0], 1: [1, 0], 2: [2, 0], 3: [3, 0], 4: [0, 1], 5: [1, 1], 6: [2, 1], 7: [3, 1], 8: [0, 2], 9: [1, 2], 10: [2, 2], 11: [3, 2], 12: [0, 3], 13: [1, 3], 14: [2, 3], 15: [3, 3], 16: [0, 4], 17: [1, 4], 18: [2, 4], 19: [3, 4], 20: [0, 5], 21: [1, 5], 22: [2, 5], 23: [3, 5], 24: [0, 6], 25: [1, 6], 26: [2, 6], 27: [3, 6], 28: [0, 7], 29: [1, 7], 30: [2, 7], 31: [3, 7]}
#skip_physical_modules = []


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== MAIN CODE STARTS HERE ==================================================================#
#========================================================================================================#


#========================================================================================================#
#=============== System to Tester Class and Scripts =====================================================#
#========================================================================================================#

class System2Tester():

	def __init__(self, target, masks = None, coremask=None, slicemask=None, boot = True, ht_dis = False, dis_1CPM = None, dis_2CPM = None, fresh_state = True, readFuse = False, clusterCheck = True , fastboot = True, ppvc_fuses = None, execution_state = None):
		
		# Python SV Variables
		from namednodes import sv
		#sv = _get_global_sv()
		ipc = ipccli.baseaccess() #_get_global_ipc()

		# Framework Cancel Flag -- Checks Cancel orders during execution
		self.execution_state = execution_state
				
		# Check for Status of PythonSV

		svStatus()
		
		## Class Variables initialization
		self.target = target
		self.coremask = coremask
		self.slicemask = slicemask
		self.boot = boot
		self.ht_dis = ht_dis
		self.dis_1CPM = dis_1CPM
		self.dis_2CPM = dis_2CPM
		self.fresh_state = fresh_state
		self.read_Fuse = False
		self.readFuse = readFuse
		self.sv = sv #_get_global_sv()
		self.ipc = ipc #_get_global_ipc()
		self.clusterCheck = clusterCheck
		
		# DMR Specific Variables
		self.cbbs = sv.socket0.cbbs
		self.imhs = sv.socket0.imhs
		
		self.instances = sv.socket0.computes.instance
		self.sktnum = [0]
		self.die = PRODUCT_CONFIG
		self.BootFuses = dpm.FuseFileConfigs
		self.Fastboot = fastboot
		self.fuse_str = []
		self.fuse_str_imh = []
		self.fuse_str_cbb = []
		## Added split fuse to apply PPVC
		self.fuse_str_cbb_0 = []
		self.fuse_str_cbb_1 = []
		self.fuse_str_cbb_2 = []
		self.fuse_str_cbb_3 = []
		self.fuse_str_imh_0 = []
		self.fuse_str_imh_1 = []
		self.fuse_2CPM = dpm.fuses_dis_2CPM(dis_2CPM, bsformat = (not fastboot)) if dis_2CPM != None else []
		self.fuse_1CPM = dpm.fuses_dis_1CPM(dis_1CPM, bsformat = (not fastboot)) if dis_1CPM != None else []
		
		self.ppvc_fuses = ppvc_fuses
		## Option to bring preconfigured Mask
		if masks == None: self.masks = dpm.fuses(rdFuses = self.readFuse, sktnum =self.sktnum, printFuse=False)
		else: self.masks = masks

		# Debug Mode -- User can enable/disable debug mode during execution
		self.debug = False

#=============== DEBUG MODE SET / RESET ==================================================================#

	def set_debug_mode(self) -> None:
		self.debug = True

	def disable_debug_mode(self) -> None:
		self.debug = False

#=============== CONFIGURATION CHECKS ==================================================================#

	def check_for_start_fresh(self) -> None:
		if self.fresh_state: reset_globals()

	def check_product_validity(self) -> bool:
		if (self.die not in CORETYPES.keys()):
			print (f"sorry.  This method still needs updating for {self.die}.  ")
			return False

		return True

#=============== STRUCTURE GENERATION ==================================================================#

	def generate_base_dict(self) -> dict[str, int]:
		base_value = 0xffffffff
		cbb_base_dict = {cbb.name: base_value for cbb in self.cbbs}
		
		return cbb_base_dict

	def generate_module_mask(self) -> tuple[int, int]:
		target_cbb = int(self.target/TOTAL_MODULES_PER_CBB) # Target CBB based on logical module
		modulemask = ~(1 << (self.target % TOTAL_MODULES_PER_CBB)) & ((1 << TOTAL_MODULES_PER_CBB) - 1)
		
		print("\n"+"-"*62)
		print("| A single module will be enabled for each available cbb |")
		print("-"*62+"\n")
		
		return target_cbb, modulemask

	def generate_mesh_masking(self, masks: dict) -> tuple[dict, dict]:
		modules = {}
		llcs = {}

		_moduleMasks= {cbb.name: masks[f'ia_{cbb.name}'] for cbb in self.cbbs}
		_llcMasks= {cbb.name: masks[f'llc_{cbb.name}'] for cbb in self.cbbs}

		for cbb_name in masks.keys():
			# Checking if str or int for modulemask / llcmask
			if isinstance(_moduleMasks[cbb_name], str):
				_moduleMasks[cbb_name] = int(_moduleMasks[cbb_name], 16)

			if isinstance(_llcMasks[cbb_name], str):
				_llcMasks[cbb_name] = int(_llcMasks[cbb_name], 16)

			modules[cbb_name] =  _moduleMasks[cbb_name]
			llcs[cbb_name] =  _llcMasks[cbb_name]

			print  (f"\n{cbb_name.upper()}: module disabled mask: {hex(modules[cbb_name])}") 
			print  (f"{cbb_name.upper()}: llc disabled mask:  {hex(llcs[cbb_name])}") 
		
		return modules, llcs

	def generate_first_enabled_mask(self, masks: dict, cbb_name: str) -> int:
		combineMask = masks[f'llc_{cbb_name}'] | masks[f'ia_{cbb_name}']
		binMask = bin(combineMask)
		first_zero = binMask[::-1].find('0')
		disMask = ~(1 << (first_zero)) & ((1 << TOTAL_MODULES_PER_CBB)-1) 

		return disMask

	def convert_cbb_mask_to_compute_mask(self, cbb_masks: dict) -> dict:
		cbbs = self.cbbs
		compute_masks = {}
		for cbb in cbbs:
			cbb_name = cbb.name
			cbb_computes = cbb.computes
			compute_masks[cbb_name] = {}
			for compute in cbb_computes:
				compute_name = compute.name
				computeN = compute.target_info.instance
				shift_amount = computeN * TOTAL_MODULES_PER_COMPUTE
				compute_masks[cbb_name][f'ia_{compute_name}'] = (cbb_masks[f'ia_{cbb_name}'] >> shift_amount) & 0xFF
				compute_masks[cbb_name][f'llc_{compute_name}'] = (cbb_masks[f'llc_{cbb_name}'] >> shift_amount) & 0xFF

		return compute_masks

	def convert_compute_mask_to_cbb_mask(self, compute_masks: dict) -> tuple[dict, dict]:
		cbbs = self.cbbs
		
		_moduleMasks = {}
		_llcMasks = {}

		for cbb in cbbs:
			cbb_name = cbb.name
			cbb_computes = cbb.computes
			new_ia_cbb_mask = 0
			new_llc_cbb_mask = 0
			for compute in cbb_computes:
				computeN = int(compute.target_info.instance)
				compute_name = compute.name
				compute_ia_mask = compute_masks[cbb_name][f'ia_{compute_name}']
				new_ia_cbb_mask |= (compute_ia_mask << (computeN * TOTAL_MODULES_PER_COMPUTE))
				compute_llc_mask = compute_masks[cbb_name][f'llc_{compute_name}']
				new_llc_cbb_mask |= (compute_llc_mask << (computeN * TOTAL_MODULES_PER_COMPUTE))
			_moduleMasks[f'{cbb_name}'] = new_ia_cbb_mask
			_llcMasks[f'{cbb_name}'] = new_llc_cbb_mask
		return _moduleMasks, _llcMasks

	def get_compute_config(self) -> tuple[list, str]:
		
		return self.cbbs, f'x{len(self.cbbs)}'

	def assign_values_to_regs(self, list_regs: list[str], new_value: int) -> list[str]:
		regs_with_values = []
		
		for reg_string in list_regs:
			regs_with_values += [f'{reg_string}=' + '0x%x' % new_value]

		return regs_with_values

#=============== MAIN SYSTEM 2 TESTER FUNCTIONS =========================================================#
	
	# Sets up system to run with 1 enabled module per cbb
	def setModule(self) -> None:
		'''
		Sets up system to run with 1 enabled module per cbb.

		Inputs:
			boot: (Boolean, Default=True) Will call bootscript with new setting
			fastboot: (Boolean, Default=False) Will call bootscript with faster setting
			load_fuses: (Boolean, Default=True) Calls fuse load for dpm.fuses
			resetGlobals: (Boolean, Default=False) Resets globals for bootscript call
		'''
		## Local variables -- Just defining them for shorter lines and usage

		cbbs = self.cbbs
		masks = self.masks

		# Check Product Validity
		if not self.check_product_validity(): return

		# Check Fresh State
		self.check_for_start_fresh()
		
		# Building arrays based on system structure
		_moduleMasks = self.generate_base_dict() # Module mask filled with 1 for every compute
		_llcMasks= self.generate_base_dict() # LLC mask filled with 1 for every compute

		target_cbb, modulemask = self.generate_module_mask()

		for cbb in cbbs: # For each compute
			cbb_name = cbb.name
			cbbN = cbb.target_info.instance
			
			if int(cbbN) == target_cbb:
				_moduleMasks[cbb_name] = modulemask | masks[f'ia_{cbb_name}']
				_llcMasks[cbb_name] = masks[f'llc_{cbb_name}']
			else:
				disMask = self.generate_first_enabled_mask(masks=masks, cbb_name=cbb_name)
				_moduleMasks[cbb_name] = disMask | masks[f'ia_{cbb_name}']
				_llcMasks[cbb_name] = masks[f'llc_{cbb_name}']

		for cbb_name in cbbs.name:
			# Print masks
			print  (f"\n{cbb_name.upper()}: module disabled mask: {hex(_moduleMasks[cbb_name])}") 
			print  (f"{cbb_name.upper()}: llc disabled mask:  {hex(_llcMasks[cbb_name])}") 

		# Setting the Class masks
		self.coremask = _moduleMasks
		self.slicemask = _llcMasks
				
		if self.boot and not debug:
			self._call_boot(boot_postcode=False,stop_after_mrc=False, pm_enable_no_vf=False)
		else:
			print("Debug Mode - No Boot Performed")

	## Enables/Disables each compute based on selected target
	def setCompute(self) -> None:
		'''
		Selects which computes to enable/disable. Based on Selected Target
		'''
		## Local variables -- Just defining them for shorter lines and usage
		
		targetComputes = self.target
		cbbs = self.cbbs
		masks = self.masks		

		# Check Product Validity
		if not self.check_product_validity(): return

		# Check Fresh State
		self.check_for_start_fresh()

		## Checking if multiple instances are selected -- If single, convert to list
		if not isinstance(targetComputes,list):
			#print (f"Single Compute Requested for: {targetTiles}")
			targetComputeList = [targetComputes]
		else:		
			targetComputeList = targetComputes

		masks_per_compute =  self.convert_cbb_mask_to_compute_mask(masks)
		new_masks_per_compute = {}

		print("\n"+"-"*62)
		print("| Compute(s) selection requested for each available cbb |")
		print("-"*62+"\n")

		
		for cbb in cbbs: # For each cbb
			cbb_name = cbb.name
			cbb_computes = cbb.computes.name
			new_masks_per_compute[cbb_name] = {}

			for compute_name in cbb_computes:
				if compute_name in targetComputeList: # Compute remains enabled
					print(f"\n{compute_name.upper()} enabled for {cbb_name}, mantaining original Masks")
					new_masks_per_compute[cbb_name][f'ia_{compute_name}'] = masks_per_compute[cbb_name][f'ia_{compute_name}']
					new_masks_per_compute[cbb_name][f'llc_{compute_name}'] = masks_per_compute[cbb_name][f'llc_{compute_name}']
				else:
					print(f"\n{compute_name.upper()} disabled for {cbb_name}, updating Masks")
					new_masks_per_compute[cbb_name][f'ia_{compute_name}'] = 0xFF
					new_masks_per_compute[cbb_name][f'llc_{compute_name}'] = masks_per_compute[cbb_name][f'llc_{compute_name}']
		
		_moduleMasks, _llcMasks = self.convert_compute_mask_to_cbb_mask(new_masks_per_compute)		

		for cbb_name in cbbs:
			# Print masks
			print  (f"\n{cbb_name.upper()}: module disables mask: {hex(_moduleMasks[f'{cbb_name}'])}") 
			print  (f"{cbb_name.upper()}: llc disables mask:  {hex(_llcMasks[f'{cbb_name}'])}") 

		# Setting the Class masks
		self.coremask = _moduleMasks
		self.slicemask = _llcMasks
				
		if self.boot and not debug:
			self._call_boot(boot_postcode=False,stop_after_mrc=False, pm_enable_no_vf=False)
		else:
			print("Debug Mode - No Boot Performed")
			
	## Needs at least one core enabled per COMPUTE, we are limited here, as WA we are leaving the selected compute alive plus the first full slice on the other COMPUTES.
	def setTile(self, boot_postcode=False,stop_after_mrc=False, pm_enable_no_vf=False):
		'''
		Will disable all cores but targetTile / Target CBB
		targetTiles: disables all tiles but targetTiles.  Can be single tile or list of tiles
		ht_dis : True/(False)
		boot: (True)/False Will call bootscript with new settings
		coresliceMask: Override with desired coreslicemask.  Default: None
		'''
		## Variables Init
		targetTiles = self.target
		cbbs = self.cbbs
		masks = self.masks

		# Check Product Validity
		if not self.check_product_validity(): return

		# Check Fresh State
		self.check_for_start_fresh()
		
		
		# Building arrays based on system structure
		_moduleMasks = self.generate_base_dict() # Module mask filled with 1 for every compute
		_llcMasks= self.generate_base_dict() # LLC mask filled with 1 for every compute

		## Read Mask enable for this part, no need for fuse ram need in Slice mode as we already read those at the beggining
		#masks = dpm.fuses(system = die, rdFuses = readFuse, sktnum =[0])
		
		## Checking if multiple instances are selected

		if not isinstance(targetTiles,list):
			#print (f"Single Compute Requested for: {targetTiles}")
			targetTileList = [targetTiles]
		else:
			
			targetTileList = targetTiles	
			
		print("\n"+"-"*62)
		print("| CBB(s) selection requested for availables cbb |")
		print("-"*62+"\n")
		
		target_cbb = targetTileList

		#coremask = ~(1 << (targetLogicalCore - (60 * target_compute))) & ((1 << 60) - 1)

		for cbb in cbbs:
			cbb_name = cbb.name
			cbbN = cbb.target_info.instance

			if cbb not in target_cbb:
				disMask = self.generate_first_enabled_mask(masks=masks, cbb_name=cbb_name)

				print(f"\n\t{cbb_name.upper()} not selected, enabling only the first available slice")
				_moduleMasks[cbb_name] = disMask |  masks[f'llc_{cbb_name}']
				_llcMasks[cbb_name] = disMask |  masks[f'llc_{cbb_name}']
			
			## If compute is not being disabled keep original Mask
			else:
				print(f"\n\t{cbb_name.upper()} selected, mantaining original Masks")
				_moduleMasks[cbb_name] = masks[f'llc_{cbb_name}']
				_llcMasks[cbb_name] = masks[f'llc_{cbb_name}']


		for cbb_name in cbbs.name:
			# Print masks
			print  (f"\n{cbb_name.upper()}: module disabled mask: {hex(_moduleMasks[cbb_name])}") 
			print  (f"{cbb_name.upper()}: llc disabled mask:  {hex(_llcMasks[cbb_name])}") 

		# Setting the Class masks
		self.coremask = _moduleMasks
		self.slicemask = _llcMasks

		if self.boot and not debug:
			self._call_boot(boot_postcode=boot_postcode,stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)
		else:
			print("Debug Mode - No Boot Performed")

	## Mesh Mode: Applies Class mask configurations or some predfined Custom Masking for Debug Experiments
	def setmesh(self, CustomConfig = [], boot_postcode=False, stop_after_mrc=False, pm_enable_no_vf=False, lsb = False, extMasks = None):
		'''
		Will disable all cores but targetTile
		targetTiles: disables all tiles but targetTiles.  Can be single tile or list of tiles
		ht_dis : True/(False)
		boot: (True)/False Will call bootscript with new settings
		coresliceMask: Override with desired coreslicemask.  Default: None

		'''
		## Variables Init
		sv = self.sv
		targetConfig = self.target
		boot = self.boot
		ht_dis = self.ht_dis
		dis_2CPM = self.dis_2CPM
		fresh_state = self.fresh_state
		cbbs = self.cbbs
		die = self.die
		
		readFuse = self.readFuse
		clusterCheck = self.clusterCheck

		if extMasks != None:
			masks = {k:int(v,16) for k, v in extMasks.items()}
		else:
			masks = self.masks

		# Check Product Validity
		if not self.check_product_validity(): return

		# Check Fresh State
		self.check_for_start_fresh()
	
		# Call DPMChecks Mesh script for mask change, we are not booting here
		core_count, llc_count, Masks_test = dpm.pseudo_bs(ClassMask = targetConfig, Custom = CustomConfig, boot = False, use_core = False, htdis = ht_dis, dis_2CPM = dis_2CPM, fuse_read = readFuse, s2t = True, masks = masks, clusterCheck = clusterCheck, lsb = lsb, skip_init = True)

		# Below dicts are only for converting of variables str to int
		
		print(f'\nSetting new Masks for {targetConfig} configuration:\n')

		modules, llcs = self.generate_mesh_masking(Masks_test[targetConfig])

		# Setting the Class masks in script arrays
		self.coremask = modules
		self.slicemask = llcs

		if self.boot and not debug:
			self._call_boot(boot_postcode=boot_postcode,stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)
		else:
			print("Debug Mode - No Boot Performed")

	## Full Chip Mode: The script passes current System Masking or an External provided Mask 
	def setfc(self, extMasks = None, boot_postcode=False, stop_after_mrc=False, pm_enable_no_vf=False):
		'''
		Will Boot Unit with full chip configuration, extMasks option to input a custom masking for slice defeature

		'''

		# Check Product Validity
		if not self.check_product_validity(): return

		# Check Fresh State
		self.check_for_start_fresh()

		# Building arrays based on system structure
		if extMasks != None:
			
			#_moduleMasks= {cbb.name: extMasks[f'ia_{cbb.name}'] for cbb in cbbs}
			#_llcMasks= {cbb.name: extMasks[f'llc_{cbb.name}'] for cbb in cbbs}

			print(f'\nSetting New Mask Based on External Masks Configuration:\n')
			modules, llcs = self.generate_mesh_masking(masks=extMasks)
							
			# Setting the Class masks in script arrays
			self.coremask = modules
			self.slicemask = llcs

		if self.boot and not debug:
			self._call_boot(boot_postcode=boot_postcode,stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)
		else:
			print("Debug Mode - No Boot Performed")

	## Wrapper to call boot or fastboot depending on class variable self.Fastboot
	def _call_boot(self, boot_postcode=False, stop_after_mrc=False, fixed_core_freq = None, fixed_mesh_freq=None, fixed_io_freq=None, avx_mode = None, acode_dis=None, vp2intersect_en=True, ia_p0=None, ia_turbo=None, ia_vf=None, ia_p1=None, ia_pn=None, ia_pm=None, cfc_p0=None, cfc_p1=None, cfc_pn=None, cfc_pm=None, io_p0=None, io_p1=None, io_pn=None, io_pm=None, pm_enable_no_vf=False, u600w=None):
		'''
		Wrapper to call boot or fastboot depending on class variable self.Fastboot
		'''
		if self.Fastboot:
			self._fastboot(boot_postcode=boot_postcode, stop_after_mrc=stop_after_mrc, fixed_core_freq=fixed_core_freq, fixed_mesh_freq=fixed_mesh_freq, fixed_io_freq=fixed_io_freq, avx_mode=avx_mode, acode_dis=acode_dis, vp2intersect_en=vp2intersect_en, ia_p0=ia_p0, ia_turbo=ia_turbo, ia_vf=ia_vf, ia_p1=ia_p1, ia_pn=ia_pn, ia_pm=ia_pm, cfc_p0=cfc_p0, cfc_p1=cfc_p1, cfc_pn=cfc_pn, cfc_pm=cfc_pm, io_p0=io_p0, io_p1=io_p1, io_pn=io_pn, io_pm=io_pm, pm_enable_no_vf=pm_enable_no_vf, u600w=u600w)
		else:
			self._doboot(boot_postcode=boot_postcode, stop_after_mrc=stop_after_mrc, fixed_core_freq=fixed_core_freq, fixed_mesh_freq=fixed_mesh_freq, fixed_io_freq=fixed_io_freq, avx_mode=avx_mode, acode_dis=acode_dis, vp2intersect_en=vp2intersect_en, ia_p0=ia_p0, ia_turbo=ia_turbo, ia_vf=ia_vf, ia_p1=ia_p1, ia_pn=ia_pn, ia_pm=ia_pm, cfc_p0=cfc_p0, cfc_p1=cfc_p1, cfc_pn=cfc_pn, cfc_pm=cfc_pm, io_p0=io_p0, io_p1=io_p1, io_pn=io_pn, io_pm=io_pm, pm_enable_no_vf=pm_enable_no_vf, u600w=u600w)


	## Boots the unit using the bootscript with fuse_strings.
	def _doboot(self, masks=None, modulemask=None, llcmask=None, stop_after_mrc=False, fixed_core_freq = None, fixed_mesh_freq=None, avx_mode = None, acode_dis=None, vp2intersect_en=True, pm_enable_no_vf=False, ia_fw_p1=None, ia_fw_pn=None, ia_fw_pm=None, ia_fw_pboot=None, ia_fw_pturbo=None, ia_vf_curves=None, ia_imh_p1=None, ia_imh_pn=None, ia_imh_pm=None, ia_imh_pturbo=None, cfc_fw_p0=None, cfc_fw_p1=None, cfc_fw_pm=None, cfc_cbb_p0=None, cfc_cbb_p1=None, cfc_cbb_pm=None, cfc_io_p0=None, cfc_io_p1=None, cfc_io_pm=None, cfc_mem_p0=None, cfc_mem_p1=None, cfc_mem_pm=None):
		'''
		Calls bootscript, if modulemask and llcmask is not set, then both llc_slice_disable and ia_core_disable get masks value

		Inputs:
			masks: (Dictionary, Default=None) module and LLC masks.
			modulemask: (Dictionary, Default=None) override module mask.
			llcmask: (Dictionary, Default=None) override LLC mask.
			stop_after_mrc: (Boolean, Default=False) If set, will stop after MRC is complete
			fixed_core_freq: (Boolean, Default=None) if set, set core P0,P1,Pn and pmin 
			fixed_mesh_freq: (Boolean, Default=None) if set, set mesh P0,P1,Pn and pmin
			fixed_io_freq: (Boolean, Default=None) if set, set io P0,P1,Pn and pmin
			avx_mode: (String, Default=None)  Set AVX mode
			acode_dis: (Boolean, Default=None) Disable acode 
			vp2intersect_en: (Boolean, Default=None) If set, will enable VPINTERSECT instruction ( needed for some Dragon Content )
			ia_p0: (Int, Default=None) CORE P0
			ia_p1: (Int, Default=None) CORE P1
			ia_pn: (Int, Default=None) CORE Pn
			ia_pm: (Int, Default=None) CORE Pm
			cfc_p0: (Int, Default=None) CFC P0
			cfc_p1: (Int, Default=None) CFC P1
			cfc_pn: (Int, Default=None) CFC Pn
			cfc_pm: (Int, Default=None) CFC Pm
			io_p0: (Int, Default=None) IO P0
			io_p1: (Int, Default=None) IO P1
			io_pn: (Int, Default=None) IO Pn
			io_pm: (Int, Default=None) IO Pm
			pm_enable_no_vf: (Boolean, Default=False) if True, will use fuse file pm_enable_no_vf.cfg to configure fuses (cfc/ia ratios and ia volt=1V) as tester	
	'''

		## Core and LLC slice disable masks we are going to move to a dict with all the values, this dict is going to change depending on the type of system we use
		# GNR has different flavours and topologies
		# On this version we have X3 and X2, code is left with some spaces for the rest of them.
		global _boot_string
		sv = self.sv #_get_global_sv()
		ipc = self.ipc
		die = self.die
		masks = self.masks
		ht_dis = self.ht_dis
		dis_2CPM = self.dis_2CPM
		coreslicemask= self.coremask
		slicemask = self.slicemask
		
		product_bs = BOOTSCRIPT_DATA
				
						
		# Retrieve local path
		parent_dir = os.path.dirname(os.path.realpath(__file__))
		fuses_dir = os.path.join(parent_dir, 'Fuse')
		
		
		b_extra = global_boot_extra
		_fuse_str = []
		_fuse_str_cbb = []
		_fuse_str_cbb_0 = []
		_fuse_str_cbb_1 = []
		_fuse_str_cbb_2 = []
		_fuse_str_cbb_3 = []
		_fuse_str_imh = []
		_fuse_str_imh_0 = []
		_fuse_str_imh_1 = []
		
		_fuse_str_io = []
		_fuse_files = []
		_fuse_files_cbb = []
		_fuse_files_imh = []
		_llc = []
		_ia = []

		htdis_comp = HIDIS_COMP # Based on Product
		htdis_io = HTDIS_IO # Based on Product
		vp2i_en_comp = VP2INTERSECT['bs'] # Based on Product
		U600W_comp = FUSES_600W_COMP # Based on Product
		W600W_io = FUSES_600W_IO # Based on Product
		
		if ht_dis == None and global_ht_dis !=None: ht_dis = global_ht_dis
		#if dis_2CPM == None and global_2CPM_dis !=None: dis_2CPM = global_2CPM_dis
		if u600w == None and global_u600w !=None: u600w = global_u600w
		if acode_dis == None and global_acode_dis !=None: acode_dis = global_acode_dis
		if global_boot_stop_after_mrc: stop_after_mrc = True
		if global_boot_postcode: boot_postcode = True
		if avx_mode == None and global_avx_mode !=None: avx_mode = global_avx_mode
		if fixed_core_freq == None and global_fixed_core_freq !=None: fixed_core_freq = global_fixed_core_freq
		if ia_fw_p1 == None and global_ia_fw_p1 !=None: ia_fw_p1 = global_ia_fw_p1
		if ia_fw_pn == None and global_ia_fw_pn !=None: ia_fw_pn = global_ia_fw_pn
		if ia_fw_pm == None and global_ia_fw_pm !=None: ia_fw_pm = global_ia_fw_pm
		if ia_fw_pboot == None and global_ia_fw_pboot !=None: ia_fw_pboot = global_ia_fw_pboot
		if ia_fw_pturbo == None and global_ia_fw_pturbo !=None: ia_fw_pturbo = global_ia_fw_pturbo
		if ia_vf_curves == None and global_ia_vf_curves !=None: ia_vf_curves = global_ia_vf_curves

		if ia_imh_p1 == None and global_ia_imh_p1 !=None: ia_imh_p1 = global_ia_imh_p1
		if ia_imh_pn == None and global_ia_imh_pn !=None: ia_imh_pn = global_ia_imh_pn
		if ia_imh_pm == None and global_ia_imh_pm !=None: ia_imh_pm = global_ia_imh_pm
		if ia_imh_pturbo == None and global_ia_imh_pturbo !=None: ia_imh_pturbo = global_ia_imh_pturbo

		if fixed_mesh_freq == None and global_fixed_mesh_freq !=None: fixed_mesh_freq = global_fixed_mesh_freq
		if cfc_fw_p0 == None and global_cfc_fw_p0 !=None: cfc_fw_p0 = global_cfc_fw_p0
		if cfc_fw_p1 == None and global_cfc_fw_p1 !=None: cfc_fw_p1 = global_cfc_fw_p1
		if cfc_fw_pm == None and global_cfc_fw_pm  !=None: cfc_fw_pm = global_cfc_fw_pm
		if cfc_cbb_p0 == None and global_cfc_cbb_p0 !=None: cfc_cbb_p0 = global_cfc_cbb_p0
		if cfc_cbb_p1 == None and global_cfc_cbb_p1 !=None: cfc_cbb_p0 = global_cfc_cbb_p1
		if cfc_cbb_pm == None and global_cfc_cbb_pm !=None: cfc_cbb_p0 = global_cfc_cbb_pm

		# if fixed_io_freq == None and global_fixed_io_freq !=None: fixed_io_freq = global_fixed_io_freq
		# if io_p0 == None and global_io_p0 !=None: io_p0 = global_io_p0
		if cfc_io_p0 == None and global_cfc_io_p0 !=None: cfc_io_p0 = global_cfc_io_p0
		if cfc_io_p1 == None and global_cfc_io_p1 !=None: cfc_io_p1 = global_cfc_io_p1
		if cfc_io_pm == None and global_cfc_io_pm !=None: cfc_io_pm = global_cfc_io_pm
		if cfc_mem_p0 == None and global_cfc_mem_p0 !=None: cfc_mem_p0 = global_cfc_mem_p0
		if cfc_mem_p1 == None and global_cfc_mem_p1 !=None: cfc_mem_p1 = global_cfc_mem_p1
		if cfc_mem_pm == None and global_cfc_mem_pm !=None: cfc_mem_pm = global_cfc_mem_pm

		if (fixed_core_freq != None):	
			ia_fw_p1 = fixed_core_freq
			ia_fw_pn = fixed_core_freq
			ia_fw_pm = fixed_core_freq
			ia_fw_pboot = fixed_core_freq
			ia_fw_pturbo = fixed_core_freq
			#ia_vf_curves = fixed_core_freq # We dont Modify VF curves

			ia_imh_p1 = fixed_core_freq
			ia_imh_pn = fixed_core_freq
			ia_imh_pm = fixed_core_freq
			ia_imh_pturbo = fixed_core_freq

		if (fixed_mesh_freq != None):
			cfc_fw_p0 = fixed_mesh_freq
			cfc_fw_p1 = fixed_mesh_freq
			cfc_fw_pm = fixed_mesh_freq

			cfc_cbb_p0 = fixed_mesh_freq
			cfc_cbb_p1 = fixed_mesh_freq
			cfc_cbb_pm = fixed_mesh_freq

			cfc_io_p0 = fixed_mesh_freq
			cfc_io_p1 = fixed_mesh_freq
			cfc_io_pm = fixed_mesh_freq

			cfc_mem_p0 = fixed_mesh_freq
			cfc_mem_p1 = fixed_mesh_freq
			cfc_mem_pm = fixed_mesh_freq


		print('\nUsing the following configuration for unit boot: ')
		# if ht_dis: print('\tHyper Threading disabled')
		if acode_dis: print('\tAcode disabled')
		if stop_after_mrc: print('\tStop after MRC')
		print(f'\tConfigured License Mode: {avx_mode}')
		print(f'\tCore Frequencies:')
		print(f'\t\tIA p1: {ia_fw_p1}')
		print(f'\t\tIA pn: {ia_fw_pn}')
		print(f'\t\tIA pm: {ia_fw_pm}')
		print(f'\t\tIA fw boot: {ia_fw_pboot}')
		print(f'\t\tIA fw turbo: {ia_fw_pturbo}')
		print(f'\t\tIA fw vf curves: {ia_vf_curves}')
		print(f'\t\tIA imh p1: {ia_imh_p1}')
		print(f'\t\tIA imh pn: {ia_imh_pn}')
		print(f'\t\tIA imh pm: {ia_imh_pm}')
		print(f'\t\tIA imh turbo: {ia_imh_pturbo}')
		print(f'\tCompute Mesh Frequencies:')
		print(f'\t\tCFC MESH fw p0: {cfc_fw_p0}')
		print(f'\t\tCFC MESH fw p1: {cfc_fw_p1}')
		print(f'\t\tCFC MESH fw pn: {cfc_fw_pm}')
		print(f'\t\tCFC MESH cbb p0: {cfc_cbb_p0}')
		print(f'\t\tCFC MESH cbb p1: {cfc_cbb_p1}')
		print(f'\t\tCFC MESH cbb pn: {cfc_cbb_pm}')
		print(f'\t\tCFC MESH io p0: {cfc_io_p0}')
		print(f'\t\tCFC MESH io p1: {cfc_io_p1}')
		print(f'\t\tCFC MESH io pn: {cfc_io_pm}')
		print(f'\t\tCFC MESH mem p0: {cfc_mem_p0}')
		print(f'\t\tCFC MESH mem p1: {cfc_mem_p1}')
		print(f'\t\tCFC MESH mem pn: {cfc_mem_pm}')
		

		try:
			temp = sv.sockets.imhs.fuses.hwrs_top_late.ip_disable_fuses_dword6_core_disable.get_value()[0] 
		except:
			itp.forcereconfig()
			itp.unlock()
			sv.refresh()
		
		if (pm_enable_no_vf == True): 
			_fuse_files_compute=[f'{fuses_dir}\\pm_enable_no_vf_computes.cfg']
			_fuse_files_io = [f'{fuses_dir}\\pm_enable_no_vf_ios.cfg'] 


		if (stop_after_mrc): b_extra+=', gotil=\"phase6_cpu_reset_break\"'
		
		
		if cfc_fw_p0: _fuse_str_cbb += assign_values_to_regs(bootFuses['CFC']['fwFreq']['p0'], cfc_fw_p0)
		if cfc_fw_p1: _fuse_str_cbb += assign_values_to_regs(bootFuses['CFC']['fwFreq']['p1'], cfc_fw_p1)
		if cfc_fw_pm: _fuse_str_cbb += assign_values_to_regs(bootFuses['CFC']['fwFreq']['min'], cfc_fw_pm)

		if cfc_cbb_p0: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['cbbFreq']['p0'], cfc_cbb_p0)
		if cfc_cbb_p1: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['cbbFreq']['p1'], cfc_cbb_p1)
		if cfc_cbb_pm: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['cbbFreq']['min'], cfc_cbb_pm)

		if cfc_io_p0: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['ioFreq']['p0'], cfc_io_p0)
		if cfc_io_p1: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['ioFreq']['p1'], cfc_io_p1)
		if cfc_io_pm: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['ioFreq']['min'], cfc_io_pm)

		if cfc_mem_p0: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['memFreq']['p0'], cfc_mem_p0)
		if cfc_mem_p1: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['memFreq']['p1'], cfc_mem_p1)
		if cfc_mem_pm: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['memFreq']['min'], cfc_mem_pm)

		if ia_fw_p1: _fuse_str_cbb += assign_values_to_regs(bootFuses['IA']['fwFreq']['p1'], ia_fw_p1)
		if ia_fw_pn: _fuse_str_cbb += assign_values_to_regs(bootFuses['IA']['fwFreq']['pn'], ia_fw_pn)
		if ia_fw_pm: _fuse_str_cbb += assign_values_to_regs(bootFuses['IA']['fwFreq']['min'], ia_fw_pm)
		if ia_fw_pboot: _fuse_str_cbb += assign_values_to_regs(bootFuses['IA']['fwFreq']['boot'], ia_fw_pboot)
		if ia_fw_pturbo: _fuse_str_cbb += assign_values_to_regs(bootFuses['IA']['fwFreq']['turbo'], ia_fw_pturbo)
		if ia_vf_curves: _fuse_str_cbb += assign_values_to_regs(bootFuses['IA']['fwFreq']['vf_curves'], ia_vf_curves)
			
		if ia_imh_p1: _fuse_str_imh += assign_values_to_regs(bootFuses['IA']['imhFreq']['p1'], ia_imh_p1)
		if ia_imh_pn: _fuse_str_imh += assign_values_to_regs(bootFuses['IA']['imhFreq']['pn'], ia_imh_pn)
		if ia_imh_pm: _fuse_str_imh += assign_values_to_regs(bootFuses['IA']['imhFreq']['min'], ia_imh_pm)
		if ia_imh_pturbo: _fuse_str_imh += assign_values_to_regs(bootFuses['IA']['imhFreq']['turbo'], ia_imh_pturbo)

		if (avx_mode != None):
			if (avx_mode) in range (0,8):
				int_mode = avx_mode
			elif avx_mode == "128":
				int_mode = 1        
			elif avx_mode == "256":
				int_mode = 3
			elif avx_mode == "512":
				int_mode=5
			elif avx_mode == "TMUL":
				int_mode=7
			else:
				raise ValueError("Invalid AVX Mode")
			ia_min_lic = bootFuses['IA_license']['cbb']['min']
			ia_max_lic = bootFuses['IA_license']['cbb']['max']
			# ia_def_lic = IA_license['default']
			# _fuse_str += [f'{ia_min_lic}=0x%x' % int_mode,f'{ia_def_lic}=0x%x' % int_mode]
			_fuse_str_cbb += [f'{ia_min_lic}=0x%x' % int_mode]
			_fuse_str_cbb += [f'{ia_max_lic}=0x%x' % int_mode]
		# print(f'fuse_str {_fuse_str_compute}')

		if _fuse_str_cbb:
			updated_fuse_str_cbb = [value.replace("sv.sockets.cbbs.base.", "") for value in _fuse_str_cbb]
			_fuse_str_cbb = updated_fuse_str_cbb

		if _fuse_str_imh:
			updated_fuse_str_imh = [value.replace("sv.sockets.imhs.", "") for value in _fuse_str_imh]
			_fuse_str_imh = updated_fuse_str_imh

		# _modulemask ={}
		# _llcmask = {}
		
		# for key, value in masks.items():
		# 	newkey = f'cbb{key[-1]}'
		# 	if key.startswith('ia_'):
		# 		_modulemask[newkey] = value
		# 	if key.startswith('llc_'):
		# 		_llcmask[newkey] = value
		
		if (modulemask == None): 
			_boot_disable_ia = ''
		else:
			for key, value in modulemask.items():
				_ia +=  [('"cbb_base%s":%s')  % (key[-1],hex(value))]
				_boot_disable_ia = ','.join(_ia)

		if (llcmask == None): 
			_boot_disable_llc = ''
		else:
			for key, value in llcmask.items():
				_llc +=  [('"cbb_base%s":%s')  % (key[-1],hex(value))]
			_boot_disable_llc = ','.join(_llc)

		FastBoot = False
		if FastBoot:
			bootopt = 'bs.fast_boot'
			bootcont = 'bs.cont'
		else:
			bootopt = 'b.go'
			bootcont = 'b.cont'

		# _boot_string = ('%s(fused_unit=True, enable_strap_checks=False,compute_config="%s",enable_pm=True,segment="%s" %s, %s, %s fuse_str_compute = %s,fuse_str_io = %s, fuse_files_compute=[%s], fuse_files_io=[%s],AXON_UPLOAD_ENABLED = False)') % (bootopt, product[die]['compute_config'], product[die]['segment'], b_extra, _boot_disable_ia, _boot_disable_llc,_fuse_str_compute,_fuse_str_io,_fuse_files_compute, _fuse_files_io)
		_boot_string = ('%s(fused_unit=False, pwrgoodmethod="usb", compute_config="%s", ia_core_disable={%s}, llc_slice_disable={%s}, fuse_str={"cbb_base":%s, "imh":%s})') % (bootopt, product[die]['compute_config'], _boot_disable_ia, _boot_disable_llc, _fuse_str_cbb, _fuse_str_imh)

		print("*"*20)
		if FastBoot: print('import users.THR.PythonScripts.thr.GnrBootscriptOverrider as bs') # CHECK THIS FOR IMPLEMENTATION
		else:	print("import toolext.bootscript.boot as b")
		print (_boot_string)
		print("***********************************v********************************************")
		if global_dry_run == False:
			eval(_boot_string)
			#print("********************************************************************************")
			#print (_boot_string)
			#print("********************************************************************************")
			if (stop_after_mrc):
				# sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=AFTER_MRC_POST
				sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6]=AFTER_MRC_POST
				print("***********************************v********************************************")
				print(f"sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg={AFTER_MRC_POST}")
				print ("%s(curr_state='phase6_cpu_reset_break')" % bootcont)
				print("***********************************v********************************************")
				if FastBoot: bs.cont(curr_state='phase6_cpu_reset_break')
				else:	b.cont(curr_state='phase6_cpu_reset_break')
				_wait_for_post(AFTER_MRC_POST)
			else:
				_wait_for_post(EFI_POST, sleeptime=120)
			sv_refreshed = False


	## Boots the unit using the bootscript with fuse_strings.
	def _doboot(self, boot_postcode=False, stop_after_mrc=False, fixed_core_freq = None, fixed_mesh_freq=None, fixed_io_freq=None, avx_mode = None, acode_dis=None, vp2intersect_en=True, ia_p0=None, ia_turbo=None, ia_vf=None, ia_p1=None, ia_pn=None, ia_pm=None, cfc_p0=None, cfc_p1=None, cfc_pn=None, cfc_pm=None, io_p0=None, io_p1=None, io_pn=None, io_pm=None, pm_enable_no_vf=False, u600w=None):
		'''
		calls bootscript
		if coreslicemask and slicemask is not set, then both llc_slice_disable and ia_core_disable get coreslice mask
		ht_dis: Disable HT or not
		slicemask: override llc_slice_disable
		stop_after_mrc:  If set, will stop after MRC is complete
		fixed_core_freq : if set, set core P0,P1,Pn and pmin 
		fixed_mesh_freq : if set, set mesh P0,P1,Pn and pmin
		fixed_io_freq : if set, set mesh P0,P1,Pn and pmin
		pm_enable_no_vf : if True, will use fuse file pm_enable_no_vf.cfg to configure fuses (cfc/ia ratios and ia volt=1V) as tester	
		avx_mode:  Set AVX mode
		vptintersect_en: If set, will enable VPINTERSECT instruction ( needed for some Dragon Content )
		ia_p0:CORE P0 
		ia_p1:CORE P1
		ia_pn:CORE Pn
		ia_pm:CORE Pm
		cfc_p0:CFC P0
		cfc_p1:CFC P1
		cfc_pn:CFC Pn
		cfc_pm:CFC Pm
	'''
		## Core and LLC slice disable masks we are going to move to a dict with all the values, this dict is going to change depending on the type of system we use
		# GNR has different flavours and topologies
		# On this version we have X3 and X2, code is left with some spaces for the rest of them.
		global _boot_string
		sv = self.sv #_get_global_sv()
		ipc = self.ipc
		die = self.die
		masks = self.masks
		ht_dis = self.ht_dis
		dis_2CPM = self.dis_2CPM
		coreslicemask= self.coremask
		slicemask = self.slicemask
		
		product_bs = BOOTSCRIPT_DATA
				
		# Retrieve local path
		parent_dir = os.path.dirname(os.path.realpath(__file__))
		fuses_dir = os.path.join(parent_dir, 'Fuse')
		
		
		b_extra = global_boot_extra
		_fuse_str = []
		_fuse_str_compute = []
		_fuse_str_compute_0 = []
		_fuse_str_compute_1 = []
		_fuse_str_compute_2 = []
		_fuse_str_io = []
		_fuse_str_io_0 = []
		_fuse_str_io_1 = []
		_fuse_files = []
		_fuse_files_compute = []
		_fuse_files_io = []
		_llc = []
		_ia = []

		htdis_comp = HIDIS_COMP # No HT dis in Atomcore
		htdis_io = HTDIS_IO # No HT dis in Atomcore
		vp2i_en_comp = VP2INTERSECT['bs'] #['scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_vp2intersect_dis=0x0']
		U600W_comp = FUSES_600W_COMP # Nothing defined for HiPower required units
		W600W_io = FUSES_600W_IO # Nothing defined for HiPower required units
		
		
		

		if ht_dis == None and global_ht_dis !=None: ht_dis = global_ht_dis
		#if dis_2CPM == None and global_2CPM_dis !=None: dis_2CPM = global_2CPM_dis
		if u600w == None and global_u600w !=None: u600w = global_u600w
		if acode_dis == None and global_acode_dis !=None: acode_dis = global_acode_dis
		if global_boot_stop_after_mrc: stop_after_mrc = True
		if global_boot_postcode: boot_postcode = True
		if avx_mode == None and global_avx_mode !=None: avx_mode = global_avx_mode
		if fixed_core_freq == None and global_fixed_core_freq !=None: fixed_core_freq = global_fixed_core_freq
		if ia_p0 == None and global_ia_p0 !=None: ia_p0 = global_ia_p0
		## Turbo and limit conditions for IA Frequency
		if ia_turbo == None and global_ia_turbo !=None: ia_turbo = global_ia_turbo
		if ia_vf == None and global_ia_vf !=None: ia_vf = global_ia_vf
		##
		if ia_p1 == None and global_ia_p1 !=None: ia_p1 = global_ia_p1
		if ia_pn == None and global_ia_pn !=None: ia_pn = global_ia_pn
		if ia_pm == None and global_ia_pm !=None: ia_pm = global_ia_pm
		if fixed_mesh_freq == None and global_fixed_mesh_freq !=None: fixed_mesh_freq = global_fixed_mesh_freq
		if cfc_p0 == None and global_cfc_p0 !=None: cfc_p0 = global_cfc_p0
		if cfc_p1 == None and global_cfc_p1 !=None: cfc_p1 = global_cfc_p1
		if cfc_pn == None and global_cfc_pn !=None: cfc_pn = global_cfc_pn
		if cfc_pm == None and global_cfc_pm !=None: cfc_pm = global_cfc_pm
		if fixed_io_freq == None and global_fixed_io_freq !=None: fixed_io_freq = global_fixed_io_freq
		if io_p0 == None and global_io_p0 !=None: io_p0 = global_io_p0
		if io_p1 == None and global_io_p1 !=None: io_p1 = global_io_p1
		if io_pn == None and global_io_pn !=None: io_pn = global_io_pn
		if io_pm == None and global_io_pm !=None: io_pm = global_io_pm

		if (fixed_core_freq != None):
			ia_p0 = fixed_core_freq
			ia_p1 = fixed_core_freq
			ia_pn = fixed_core_freq
			ia_pm = fixed_core_freq
		if (fixed_mesh_freq != None):
			cfc_p0 = fixed_mesh_freq
			cfc_p1 = fixed_mesh_freq
			cfc_pn = fixed_mesh_freq
			cfc_pm = fixed_mesh_freq
		if (fixed_mesh_freq != None):
			io_p0 = fixed_io_freq
			io_p1 = fixed_io_freq
			io_pn = fixed_io_freq
			io_pm = fixed_io_freq

		## Cores per Module disable Fuses (Atom)
		dis_2CPM_comp = self.fuse_2CPM
		dis_2CPM_value = f'{dis_2CPM:#x}' if isinstance(dis_2CPM,int) else dis_2CPM
		print('\nUsing the following configuration for unit boot: ')
		if ht_dis: print('\tHyper Threading disabled')
		if dis_2CPM != None: print(f'\tRunning with 2 Cores per Module Configuration : {dis_2CPM_value}')
		if acode_dis: print('\tAcode disabled')
		if stop_after_mrc: print('\tStop after MRC')
		if boot_postcode: print('\tBoot Will be stopped at Break')

		print(f'\tConfigured License Mode: {avx_mode}')
		print(f'\tCore Frequencies:')
		print(f'\t\tIA P0: {ia_p0}')
		print(f'\t\tIA P1: {ia_p1}')
		print(f'\t\tIA PN: {ia_pn}')
		print(f'\t\tIA MIN: {ia_pm}')
		print(f'\t\tIA TURBO: {ia_turbo}')
		print(f'\t\tIA VF: {ia_vf}')

		print(f'\tCompute Mesh Frequencies:')
		print(f'\t\tCFC MESH P0: {cfc_p0}')
		print(f'\t\tCFC MESH P1: {cfc_p1}')
		print(f'\t\tCFC MESH PN: {cfc_pn}')
		print(f'\t\tCFC MESH MIN: {cfc_pm}')
		print(f'\tIO Mesh Frequencies:')
		print(f'\t\tCFC IO P0: {io_p0}')
		print(f'\t\tCFC IO P1: {io_p1}')
		print(f'\t\tCFC IO PN: {io_pn}')
		print(f'\t\tCFC IO MIN: {io_pm}')

		#Voltages
		fixed_core_volt = global_fixed_core_volt
		fixed_cfc_volt = global_fixed_cfc_volt
		fixed_hdc_volt = global_fixed_hdc_volt
		fixed_cfcio_volt = global_fixed_cfcio_volt
		fixed_ddrd_volt = global_fixed_ddrd_volt
		fixed_ddra_volt = global_fixed_ddra_volt
		vbumps_config = global_vbumps_configuration

		voltageWord = 'vBump' if vbumps_config else 'Volt'
		print(f'\tVoltage Bumps Configurations:' if vbumps_config else f'\tFixed Voltage Configurations:')
		print(f'\t\tCore {voltageWord}: {fixed_core_volt}{"V" if fixed_core_volt != None else ""}')
		print(f'\t\tCFC Compute {voltageWord}: {fixed_cfc_volt}{"V" if fixed_cfc_volt != None else ""}')
		print(f'\t\tHDC Compute {voltageWord}: {fixed_hdc_volt}{"V" if fixed_hdc_volt != None else ""}')
		print(f'\t\tCFC IO {voltageWord}: {fixed_cfcio_volt}{"V" if fixed_cfcio_volt != None else ""}')		
		print(f'\t\tDDRD {voltageWord}: {fixed_ddrd_volt}{"V" if fixed_ddrd_volt != None else ""}')	
		#print(f'\t\tDDRA {voltageWord}: {fixed_ddra_volt}{"V" if fixed_ddra_volt != None else ""}')	
		#try:
		#	temp = sv.socket0.compute0.fuses.hwrs_top_rom.ip_disable_fuses_dword6_core_disable ## Need to change this
		#except:
		#	itp.forcereconfig()
		#	itp.unlock()
		#	sv.refresh()
		
		##PM enable no vf not enabled yet, do not use... WIP
		if (pm_enable_no_vf == True): 
			_fuse_files_compute=[f'{fuses_dir}\\pm_enable_no_vf_computes.cfg'] ## Fix the file for GNR
			_fuse_files_io = [f'{fuses_dir}\\pm_enable_no_vf_ios.cfg'] ## Fix the file for GNR


		if (stop_after_mrc or boot_postcode): b_extra+=', gotil=\"phase6_cpu_reset_break\"'
		
		#masks = dpm.fuses(system = die, rdFuses = False, sktnum =[0])


		_coreslicemask ={}
		_slicemask = {}
		print(coreslicemask)
		print(slicemask)
		for key, value in masks.items():
			newkey = f'compute{key[-1]}'
			if key.startswith('ia_compute_'):
				_coreslicemask[newkey] = value
			if key.startswith('llc_compute_'):
				_slicemask[newkey] = value
		
		
		if (coreslicemask == None): 
			#coreslicemask = _coreslicemask
			_boot_disable_ia = ''
		else:
			for key, value in coreslicemask.items():
					_ia +=  [('ia_core_disable_compute_%s = %s')  % (key[-1],hex(value))]

			_boot_disable_ia = ','.join(_ia) + ','
			

			#coreslicemask = {value: {die:None} for value in product[die]}

			#coreslicemask = int(sv.socket0.pcudata.fused_ia_core_disable_1) << 32 | int(sv.socket0.pcudata.fused_ia_core_disable_0) # double check this works

		if (slicemask == None): 
			#slicemask = coreslicemask
			_boot_disable_llc = ''
		else:
			for key, value in slicemask.items():
				_llc +=  [('llc_slice_disable_compute_%s = %s')  % (key[-1],hex(value))]
			_boot_disable_llc = ','.join(_llc) + ','

		if (ht_dis): 
			_fuse_str_compute+=htdis_comp
			_fuse_str_io+=htdis_io

		if (dis_2CPM != None): 
			_fuse_str_compute+=dis_2CPM_comp

		if (u600w): 
			_fuse_str_compute+=U600W_comp
			_fuse_str_io+=W600W_io

		#if (acode_dis): _fuse_str+=['pcu.pcode_acp_enable=0x0'] # Not used for GNR we can't disable acode
		
		if (vp2intersect_en): 
			#_fuse_str+=[ 'cfs_core_c0_r2.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c0_r4.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c0_r5.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c1_r2.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c1_r3.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c1_r4.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c1_r5.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c2_r2.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c2_r3.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c2_r4.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c2_r5.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c3_r2.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c3_r3.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c3_r4.core_core_fuse_misc_vp2intersect_dis=0x0']
			_fuse_str_compute += vp2i_en_comp

		# Are we including the IO ratios?? 

		curves = IA_RATIO_CURVES 
		
		# Enumarate all the variables needed for power curves	
		ppfs = IA_RATIO_CONFIG['ppfs']#[0,1,2,3,4]
		idxs = IA_RATIO_CONFIG['idxs']#[0,1,2,3,4,5]
		ratios = IA_RATIO_CONFIG['ratios']#[0,1,2,3,4,5,6,7]
		vfidx =  IA_RATIO_CONFIG['vfidx']#[0,1,2,3]
		vfpnt =  IA_RATIO_CONFIG['vfpnt']#[0,1,2,3,4,5]

		# IA P0 frequencies flat
		if (ia_p0 != None): 
			_fuse_str_compute += ['pcu.pcode_ia_p0_ratio=0x%x' % ia_p0]
			#ia_turbo = ia_p0 ## Will have it disabled for now, need to check if needed, maybe add a new switch
			#ia_vf = ia_p0 ## Setting VF curves same as ratio for IA
		# IA P0 Turbo Limits
		# Limit fuses (RATIO)
		if ia_turbo != None:
			for curve in curves['limits']:
				for pp in ppfs:
					for idx in idxs:
						for ratio in ratios:
							turbo_string = curve
										
							#for _search in search_string:
							turbo_string = turbo_string.replace(f'##profile##',str(pp))
							turbo_string = turbo_string.replace(f'##idx##',str(idx))
							turbo_string = turbo_string.replace(f'##ratio##',str(ratio))
							#print(turbo_string)
							_fuse_str_compute += [f'pcu.{turbo_string}=' + '0x%x' % ia_turbo]

		if ia_vf != None:
			for curve in curves['vf_curve']:
				for vfid in vfidx:
					for pnt in vfpnt:
						vf_string = curve
										
						#for _search in search_string:
						vf_string = vf_string.replace(f'##idx##',str(vfid))
						vf_string = vf_string.replace(f'##point##',str(pnt))
						#print(vf_string)
						_fuse_str_compute += [f'pcu.{vf_string}=' + '0x%x' % ia_vf]

		# IA P1 frequencies flat
		if (ia_p1 != None): 
			for curve in curves['p1']:
				for pp in ppfs:
					p1_string = curve
					p1_string = p1_string.replace(f'##profile##',str(pp))
					_fuse_str_compute += [f'pcu.{p1_string}=' + '0x%x' % ia_p1]

		# IA PN frequencies flat

		if (ia_pn != None): 
			_fuse_str_compute += ['pcu.pcode_ia_pn_ratio=0x%x' % ia_pn]
		if (ia_pm != None): 
			_fuse_str_compute += ['pcu.pcode_ia_min_ratio=0x%x' % ia_pm]
		
		## CFC is modifying IOs as well, can we make them separate?
		if (cfc_p0 != None): 
			_fuse_str_compute += ['pcu.pcode_sst_pp_0_cfc_p0_ratio=0x%x' % cfc_p0]
		if (cfc_p1 != None): 
			_fuse_str_compute += ['pcu.pcode_sst_pp_0_cfc_p1_ratio=0x%x' % cfc_p1]
		if (cfc_pn != None): 
			_fuse_str_compute += ['pcu.pcode_cfc_pn_ratio=0x%x' % cfc_pn]
		if (cfc_pm != None): 
			_fuse_str_compute += ['pcu.pcode_cfc_min_ratio=0x%x' % cfc_pm]
		
		## CFC is modifying IOs as well, can we make them separate?
		if (io_p0 != None): 
			_fuse_str_io += ['punit_iosf_sb.pcode_sst_pp_0_cfc_p0_ratio=0x%x' % io_p0]
		if (io_p1 != None): 
			_fuse_str_io += ['punit_iosf_sb.pcode_sst_pp_0_cfc_p1_ratio=0x%x' % io_p1]
		if (io_pn != None): 
			_fuse_str_io += ['punit_iosf_sb.pcode_cfc_pn_ratio=0x%x' % io_pn]
		if (io_pm != None): 
			_fuse_str_io += ['punit_iosf_sb.pcode_cfc_min_ratio=0x%x' % io_pm]   

		if (avx_mode != None):
			#print(avx_mode)
			if (avx_mode) in range (0,8):
				int_mode = avx_mode
			elif avx_mode == "128":
				int_mode = 1        
			elif avx_mode == "256":
				int_mode = 3
			elif avx_mode == "512":
				int_mode=5
			elif avx_mode == "TMUL":
				int_mode=7
			else:
				raise ValueError(f"Invalid AVX Mode",avx_mode)
			_fuse_str_compute += ['pcu.pcode_iccp_min_license=0x%x' % int_mode,'pcu.pcode_iccp_default=0x%x' % int_mode]

		FastBoot = False
		if FastBoot:
			bootopt = 'bs.fast_boot'
			bootcont = 'bs.cont'
		else:
			bootopt = 'b.go'
			bootcont = 'b.cont'


		## Add PPVC Data if configured
		if self.ppvc_fuses:
			ppvc_fuses = self.ppvc_fuses
			for comp in self.computes:
				if 'compute0' in comp.lower(): _fuse_str_compute_0 += ppvc_fuses['compute0']
				if 'compute1' in comp.lower(): _fuse_str_compute_1 += ppvc_fuses['compute1']
				if 'compute2' in comp.lower(): _fuse_str_compute_2 += ppvc_fuses['compute2']
			for iodie in self.ios:
				if 'io0' in iodie.lower(): _fuse_str += ppvc_fuses['io0']
				if 'io1' in iodie.lower(): _fuse_str += ppvc_fuses['io1']

		
		_fuse_str_compute_0 += _fuse_str_compute
		_fuse_str_compute_1 += _fuse_str_compute
		_fuse_str_compute_2 += _fuse_str_compute
		_fuse_str_io_0 += _fuse_str_io
		_fuse_str_io_1 += _fuse_str_io
		
		## Adds additional fuses to properly boot the unit in GNRSP
		if die == 'GNRSP':
			print(Fore.CYAN + "GNRSP System Configuration")
		
		## Adding the fuse_str to the Class variable here before the Masks addition this variable is for checking purposes only, Masking will be checked with the CoresEnabled script
		self.fuse_str_io = _fuse_str_io
		self.fuse_str_io_0 = _fuse_str_io_0
		self.fuse_str_io_1 = _fuse_str_io_1
		self.fuse_str_compute = _fuse_str_compute
		self.fuse_str_compute_0 = _fuse_str_compute_0
		self.fuse_str_compute_1 = _fuse_str_compute_1
		self.fuse_str_compute_2 = _fuse_str_compute_2

		# Building a new splitted fuse string for the bootscript
		fuse_string = ''
		computeNumber = len(self.computes)
		ioNumber = 2
		if computeNumber >= 1:
			fuse_string = fuse_string + f'fuse_str_compute_0 = {_fuse_str_compute_0},'
		if computeNumber >= 2:
			fuse_string = fuse_string + f'fuse_str_compute_1 = {_fuse_str_compute_1},'			
		if computeNumber >= 3:
			fuse_string = fuse_string + f'fuse_str_compute_2 = {_fuse_str_compute_2},'

		if ioNumber >= 1:
			fuse_string = fuse_string + f'fuse_str_io_0 = {_fuse_str_io_0},'
		if ioNumber >= 2:
			fuse_string = fuse_string + f'fuse_str_io_1 = {_fuse_str_io_1},'
	

		_boot_string = gen_product_bootstring(bootopt, product_bs[die]['compute_config'], product_bs[die]['segment'], b_extra, _boot_disable_ia, _boot_disable_llc, fuse_string,_fuse_files_compute, _fuse_files_io)
		if check_user_cancel():
			return
		print(Fore.CYAN+ '\n' + "+"*90)
		#if FastBoot: print('import users.THR.PythonScripts.thr.GnrBootscriptOverrider as bs')
		#else:	print("import toolext.bootscript.boot as b")
		print(Fore.CYAN + "import toolext.bootscript.boot as b")
		print(Fore.CYAN + _boot_string)
		print(Fore.CYAN + "+"*90 + '\n')
		
		## Might remove this if condition, and run code inside only there is no need for this condition global_dry condition
		if global_dry_run == False:
			# ADded below only for checking some configs, can be removed later
			Test = False
			if Test: 
				print("Testing, not booting for now")
				return

			print(Fore.YELLOW + "********************************************v********************************************")
			print(Fore.YELLOW + "***************************   Starting Unit using Bootscript   **************************")
			print(Fore.YELLOW + "********************************************v********************************************")			


			bsPASS = self.bsRetry(boot_postcode=boot_postcode, stop_after_mrc=stop_after_mrc, bootcont=bootcont, sv=sv, ipc=ipc, boot_string=_boot_string ,n=BOOTSCRIPT_RETRY_TIMES,delay=BOOTSCRIPT_RETRY_DELAY) #Changed this to retry bootscript eval(_boot_string)
			if not bsPASS: 
				raise ValueError("!!!FAIL --  Max number of bootscript retries reached, fails occurred during unit boot, please check your configuration and try again.")
			elif bsPASS == 'Cancel':
				raise InterruptedError('Boot Interrupted by user')

			sv_refreshed = False

	## Fastboot option to boot the unit using itp.resettarget, works with SLICE MODE only
	def _fastboot(self, boot_postcode = False, stop_after_mrc=False, fixed_core_freq = None, fixed_mesh_freq=None, fixed_io_freq=None, avx_mode = None, acode_dis=None, vp2intersect_en=True, ia_p0=None, ia_turbo=None, ia_vf=None, ia_p1=None, ia_pn=None, ia_pm=None, cfc_p0=None, cfc_p1=None, cfc_pn=None, cfc_pm=None, io_p0=None, io_p1=None, io_pn=None, io_pm=None, pm_enable_no_vf=False):
		'''
		calls bootscript
		if coreslicemask and slicemask is not set, then both llc_slice_disable and ia_core_disable get coreslice mask
		ht_dis: Disable HT or not
		slicemask: override llc_slice_disable
		stop_after_mrc:  If set, will stop after MRC is complete
		fixed_core_freq : if set, set core P0,P1,Pn and pmin 
		fixed_mesh_freq : if set, set mesh P0,P1,Pn and pmin
		fixed_io_freq : if set, set mesh P0,P1,Pn and pmin
		pm_enable_no_vf : if True, will use fuse file pm_enable_no_vf.cfg to configure fuses (cfc/ia ratios and ia volt=1V) as tester	
		avx_mode:  Set AVX mode
		vptintersect_en: If set, will enable VPINTERSECT instruction ( needed for some Dragon Content )
		ia_p0:CORE P0 
		ia_p1:CORE P1
		ia_pn:CORE Pn
		ia_pm:CORE Pm
		cfc_p0:CFC P0
		cfc_p1:CFC P1
		cfc_pn:CFC Pn
		cfc_pm:CFC Pm
	'''
		## Core and LLC slice disable masks we are going to move to a dict with all the values, this dict is going to change depending on the type of system we use
		# GNR has different flavours and topologies
		# On this version we have X3 and X2, code is left with some spaces for the rest of them.
		global _boot_string
		sv = self.sv #_get_global_sv()
		ipc = self.ipc
		die = self.die
		masks = self.masks
		ht_dis = self.ht_dis
		dis_2CPM = self.dis_2CPM
		coreslicemask= self.coremask
		slicemask = self.slicemask
		BootFuses = self.BootFuses
		
		# Retrieve local path
		parent_dir = os.path.dirname(os.path.realpath(__file__))
		fuses_dir = os.path.join(parent_dir, 'Fuse')
		
		
		b_extra = global_boot_extra
		_fuse_str = []
		_fuse_str_compute = []
		_fuse_str_io = []
		_fuse_files = []
		_fuse_files_compute = []
		_fuse_files_io = []
		_llc = []
		_ia = []


		## Declare all the fuse arrays to be used
		htdis_comp = BootFuses['ht']['compHT']['htdis']#['scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_fused_ht_dis=0x1', 'pcu.capid_capid0_ht_dis_fuse=0x1','fuses.pcu.pcode_lp_disable=0x2','pcu.capid_capid0_max_lp_en=0x1']
		htdis_io = BootFuses['ht']['ioHT']['htdis']#['punit_iosf_sb.soc_capid_capid0_max_lp_en=0x1','punit_iosf_sb.soc_capid_capid0_ht_dis_fuse=0x1']
		
		## Need to include in configFile, will move later
		vp2i_en_comp = VP2INTERSECT['fast']#['sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_vp2intersect_dis=0x0']
		
		##Frequency fuses
		CFC_freq_fuses = BootFuses['CFC']['compFreq']
		CFCIO_freq_fuses = BootFuses['CFC']['ioFreq']
		IA_freq_fuses = BootFuses['IA']['compFreq']
		IA_license = BootFuses['IA_license']['compute']

		if ht_dis == None and global_ht_dis !=None: ht_dis = global_ht_dis
		#if dis_2CPM == None and global_2CPM_dis !=None: dis_2CPM = global_2CPM_dis
		if acode_dis == None and global_acode_dis !=None: acode_dis = global_acode_dis
		if global_boot_stop_after_mrc: stop_after_mrc = True
		if global_boot_postcode: boot_postcode = True
		
		if avx_mode == None and global_avx_mode !=None: avx_mode = global_avx_mode
		if fixed_core_freq == None and global_fixed_core_freq !=None: fixed_core_freq = global_fixed_core_freq
		if ia_p0 == None and global_ia_p0 !=None: ia_p0 = global_ia_p0
		## Turbo and limit conditions for IA Frequency
		if ia_turbo == None and global_ia_turbo !=None: ia_turbo = global_ia_turbo
		if ia_vf == None and global_ia_vf !=None: ia_vf = global_ia_vf
		##
		if ia_p1 == None and global_ia_p1 !=None: ia_p1 = global_ia_p1
		if ia_pn == None and global_ia_pn !=None: ia_pn = global_ia_pn
		if ia_pm == None and global_ia_pm !=None: ia_pm = global_ia_pm
		if fixed_mesh_freq == None and global_fixed_mesh_freq !=None: fixed_mesh_freq = global_fixed_mesh_freq
		if cfc_p0 == None and global_cfc_p0 !=None: cfc_p0 = global_cfc_p0
		if cfc_p1 == None and global_cfc_p1 !=None: cfc_p1 = global_cfc_p1
		if cfc_pn == None and global_cfc_pn !=None: cfc_pn = global_cfc_pn
		if cfc_pm == None and global_cfc_pm !=None: cfc_pm = global_cfc_pm
		if fixed_io_freq == None and global_fixed_io_freq !=None: fixed_io_freq = global_fixed_io_freq
		if io_p0 == None and global_io_p0 !=None: io_p0 = global_io_p0
		if io_p1 == None and global_io_p1 !=None: io_p1 = global_io_p1
		if io_pn == None and global_io_pn !=None: io_pn = global_io_pn
		if io_pm == None and global_io_pm !=None: io_pm = global_io_pm

		## Cores per Module disable Fuses (Atom)
		dis_2CPM_comp = self.fuse_2CPM
		dis_2CPM_value = f'{dis_2CPM:#x}' if isinstance(dis_2CPM,int) else dis_2CPM

		if (fixed_core_freq != None):
			ia_p0 = fixed_core_freq
			ia_p1 = fixed_core_freq
			ia_pn = fixed_core_freq
			ia_pm = fixed_core_freq

		if (fixed_mesh_freq != None):
			cfc_p0 = fixed_mesh_freq
			cfc_p1 = fixed_mesh_freq
			cfc_pn = fixed_mesh_freq
			cfc_pm = fixed_mesh_freq
		if (fixed_mesh_freq != None):
			io_p0 = fixed_io_freq
			io_p1 = fixed_io_freq
			io_pn = fixed_io_freq
			io_pm = fixed_io_freq

		print('\nUsing the following configuration for unit boot: ')
		if ht_dis: print('\tHyper Threading disabled')
		if dis_2CPM != None: print(f'\tRunning with 2 Cores per Module Configuration: {dis_2CPM_value}')
		if acode_dis: print('\tAcode disabled')
		if stop_after_mrc: print('\tStop after MRC')
		if boot_postcode: print('\tBoot Will be stopped at Break')
		print(f'\tConfigured License Mode: {avx_mode}')
		print(f'\tCore Frequencies:')
		print(f'\t\tIA P0: {ia_p0}')
		print(f'\t\tIA P1: {ia_p1}')
		print(f'\t\tIA PN: {ia_pn}')
		print(f'\t\tIA MIN: {ia_pm}')
		print(f'\t\tIA TURBO: {ia_turbo}')
		print(f'\t\tIA VF: {ia_vf}')
		print(f'\tCompute Mesh Frequencies:')
		print(f'\t\tCFC MESH P0: {cfc_p0}')
		print(f'\t\tCFC MESH P1: {cfc_p1}')
		print(f'\t\tCFC MESH PN: {cfc_pn}')
		print(f'\t\tCFC MESH MIN: {cfc_pm}')
		print(f'\tIO Mesh Frequencies:')
		print(f'\t\tCFC IO P0: {io_p0}')
		print(f'\t\tCFC IO P1: {io_p1}')
		print(f'\t\tCFC IO PN: {io_pn}')
		print(f'\t\tCFC IO MIN: {io_pm}')
		
		#Voltages
		fixed_core_volt = global_fixed_core_volt
		fixed_cfc_volt = global_fixed_cfc_volt
		fixed_hdc_volt = global_fixed_hdc_volt
		fixed_cfcio_volt = global_fixed_cfcio_volt
		fixed_ddrd_volt = global_fixed_ddrd_volt
		fixed_ddra_volt = global_fixed_ddra_volt
		vbumps_config = global_vbumps_configuration

		voltageWord = 'vBump' if vbumps_config else 'Volt'
		print(f'\tVoltage Bumps Configurations:' if vbumps_config else f'\tFixed Voltage Configurations:')
		print(f'\t\tCore {voltageWord}: {fixed_core_volt}{"V" if fixed_core_volt != None else ""}')
		print(f'\t\tCFC Compute {voltageWord}: {fixed_cfc_volt}{"V" if fixed_cfc_volt != None else ""}')
		print(f'\t\tHDC Compute {voltageWord}: {fixed_hdc_volt}{"V" if fixed_hdc_volt != None else ""}')
		print(f'\t\tCFC IO {voltageWord}: {fixed_cfcio_volt}{"V" if fixed_cfcio_volt != None else ""}')		
		print(f'\t\tDDRD {voltageWord}: {fixed_ddrd_volt}{"V" if fixed_ddrd_volt != None else ""}')	
		#print(f'\t\tDDRA {voltageWord}: {fixed_ddra_volt}{"V" if fixed_ddra_volt != None else ""}')	
		#try:
		#try:
		#	temp = sv.socket0.compute0.fuses.hwrs_top_rom.ip_disable_fuses_dword6_core_disable ## Need to change this
		#except:
		#	itp.forcereconfig()
		#	itp.unlock()
		#	sv.refresh()
		
		##PM enable no vf not enabled yet, do not use... WIP
		#if (pm_enable_no_vf == True): 
		#	_fuse_files_compute=[f'{fuses_dir}\\pm_enable_no_vf_computes.cfg'] ## Fix the file for GNR
		#	_fuse_files_io = [f'{fuses_dir}\\pm_enable_no_vf_ios.cfg'] ## Fix the file for GNR


		#if (stop_after_mrc): b_extra+=', gotil=\"phase6_cpu_reset_break\"'
		
		#masks = dpm.fuses(system = die, rdFuses = False, sktnum =[0])


		_coreslicemask ={}
		_slicemask = {}
		
		for key, value in masks.items():
			newkey = f'compute{key[-1]}'
			if key.startswith('ia_compute_'):
				_coreslicemask[newkey] = value
			if key.startswith('llc_compute_'):
				_slicemask[newkey] = value
		
		
		if (coreslicemask == None): 
			coreslicemask = _coreslicemask

		if (ht_dis): 
			_fuse_str+= htdis_comp
			_fuse_str+= htdis_io

		if (dis_2CPM != None): 
			_fuse_str+=dis_2CPM_comp

		if (vp2intersect_en): 
			_fuse_str += vp2i_en_comp

		## Defining new values for IA Frequencies
		# IA P0 frequencies flat
		if (ia_p0 != None): 
			for fuse in IA_freq_fuses['p0']:
				_fuse_str += [fuse + '=0x%x' % ia_p0]
		if (ia_turbo != None): 
			for fuse in IA_freq_fuses['limits']:
				_fuse_str += [fuse + '=0x%x' % ia_turbo]
		if (ia_vf != None): 
			for fuse in IA_freq_fuses['vf_curves']:
				_fuse_str += [fuse + '=0x%x' % ia_vf]							
		# IA P1 frequencies flat
		if (ia_p1 != None): 
			for fuse in IA_freq_fuses['p1']:
				_fuse_str += [fuse + '=0x%x' % ia_p1]
	
		# IA PN frequencies flat
		if (ia_pn != None): 
			for fuse in IA_freq_fuses['pn']:
				_fuse_str += [fuse + '=0x%x' % ia_pn]

		# IA MIN frequencies flat
		if (ia_pm != None): 
			for fuse in IA_freq_fuses['min']:
				_fuse_str += [fuse + '=0x%x' % ia_pm]

		## Defining new values for MESH CFC Frequencies
		# MESH CFC P0 frequencies flat
		if (cfc_p0 != None): 
			for fuse in CFC_freq_fuses['p0']:
				_fuse_str += [fuse + '=0x%x' % cfc_p0]
			
		# MESH CFC P1 frequencies flat
		if (cfc_p1 != None): 
			for fuse in CFC_freq_fuses['p1']:
				_fuse_str += [fuse + '=0x%x' % cfc_p1]
	
		# MESH CFC PN frequencies flat
		if (cfc_pn != None): 
			for fuse in CFC_freq_fuses['pn']:
				_fuse_str += [fuse + '=0x%x' % cfc_pn]

		# MESH CFC MIN frequencies flat
		if (cfc_pm != None): 
			for fuse in CFC_freq_fuses['min']:
				_fuse_str += [fuse + '=0x%x' % cfc_pm]

		## Defining new values for IO CFC Frequencies
		# CFCIO P0 frequencies flat
		if (io_p0 != None): 
			for fuse in CFCIO_freq_fuses['p0']:
				_fuse_str += [fuse + '=0x%x' % io_p0]
			
		# CFCIO P1 frequencies flat
		if (io_p1 != None): 
			for fuse in CFCIO_freq_fuses['p1']:
				_fuse_str += [fuse + '=0x%x' % io_p1]
	
		# CFCIO PN frequencies flat
		if (io_pn != None): 
			for fuse in CFCIO_freq_fuses['pn']:
				_fuse_str += [fuse + '=0x%x' % io_pn]

		# CFCIO MIN frequencies flat
		if (io_pm != None): 
			for fuse in CFCIO_freq_fuses['min']:
				_fuse_str += [fuse + '=0x%x' % io_pm]

		if (avx_mode != None):
			if (avx_mode) in range (0,8):
				int_mode = avx_mode
			elif avx_mode == "128":
				int_mode = 1        
			elif avx_mode == "256":
				int_mode = 3
			elif avx_mode == "512":
				int_mode=5
			elif avx_mode == "TMUL":
				int_mode=7
			else:
				raise ValueError("Invalid AVX Mode")
			ia_min_lic = IA_license['min']
			ia_def_lic = IA_license['default']
			_fuse_str += [f'{ia_min_lic}=0x%x' % int_mode,f'{ia_def_lic}=0x%x' % int_mode]

		## Add PPVC Data if configured
		if self.ppvc_fuses:
			ppvc_fuses = self.ppvc_fuses
			for comp in self.computes:
				if 'compute0' in comp.lower(): _fuse_str += ppvc_fuses['compute0']
				if 'compute1' in comp.lower(): _fuse_str += ppvc_fuses['compute1']
				if 'compute2' in comp.lower(): _fuse_str += ppvc_fuses['compute2']
			for iodie in self.ios:
				if 'io0' in iodie.lower(): _fuse_str += ppvc_fuses['io0']
				if 'io1' in iodie.lower(): _fuse_str += ppvc_fuses['io1']

		## Adding the fuse_str to the Class variable here before the Masks addition this variable is for checking purposes only
		self.fuse_str = _fuse_str

		## Continue adding the Core/llc Masks
		if (self.slicemask != None): 
			#slicemask = coreslicemask
			_fuse_str+= mask_fuse_llc_array(self.slicemask)

		if (self.coremask != None): 
			_fuse_str+= mask_fuse_core_array(self.coremask)

		if check_user_cancel():
			return
		
		print(Fore.YELLOW + "********************************************v********************************************")
		print(Fore.YELLOW +  f"{'>'*3}   Using FastBoot with itp.resettarget() and ram flush ")

		
		if global_dry_run == False:
			if (stop_after_mrc):
				print(f'Setting biosscratchpad6_cfg for desired PostCode = {AFTER_MRC_POST}')
				sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=AFTER_MRC_POST

			if (boot_postcode):
				print(f'Setting biosscratchpad6_cfg for desired PostCode = {BOOT_STOP_POSTCODE}')
				sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=BOOT_STOP_POSTCODE
			
			print(Fore.YELLOW + "********************************************v********************************************")
			print(Fore.YELLOW + "***********************   Starting Unit Fast Boot Fuse Override   ***********************")
			print(Fore.YELLOW + "********************************************v********************************************")			

			fuse_cmd_override_reset(fuse_cmd_array=_fuse_str, s2t=True, execution_state=self.execution_state)

			if (stop_after_mrc):

				_wait_for_post(AFTER_MRC_POST, sleeptime=MRC_POSTCODE_WT, timeout = MRC_POSTCODE_CHECK_COUNT, execution_state=self.execution_state)
			if (boot_postcode):

				_wait_for_post(BOOT_STOP_POSTCODE, sleeptime=BOOT_POSTCODE_WT, timeout = BOOT_POSTCODE_CHECK_COUNT, additional_postcode=LINUX_POST, execution_state=self.execution_state)
						
			else:
				_wait_for_post(EFI_POST, sleeptime=EFI_POSTCODE_WT, timeout = EFI_POSTCODE_CHECK_COUNT, additional_postcode=LINUX_POST, execution_state=self.execution_state)
			sv_refreshed = False

	## Boot checking for s2t
	def fuse_checks(self):
		product_variant = PRODUCT_VARIANT
		#svStatus()
		dpm.fuseRAM(refresh=True)
		skipinit = True
		if self.Fastboot:
			print(Fore.LIGHTCYAN_EX + "***********************************v********************************************")
			print(Fore.LIGHTCYAN_EX + f"{'>'*3} Checking fuse application after boot")
			
			if self.fuse_str: fuse_cmd_override_check(self.fuse_str, showresults = False,skip_init= skipinit, bsFuses = None)
		
		else:
			print(Fore.LIGHTCYAN_EX + "***********************************v********************************************")
			print(Fore.LIGHTCYAN_EX + f"{'>'*3} Checking fuse application after boot")
			if self.fuse_str_compute_0: 
				print(f"{'>'*3} Checking fuses for Compute0 ---")
				fuse_cmd_override_check(self.fuse_str_compute_0, showresults = False, skip_init= skipinit, bsFuses = 'compute0')
				#skipinit = True
			if self.fuse_str_compute_1: 
				print(Fore.LIGHTCYAN_EX + f"{'>'*3} Checking fuses for Compute1 ---")
				fuse_cmd_override_check(self.fuse_str_compute_1, showresults = False, skip_init= skipinit, bsFuses = 'compute1')
				#skipinit = True
			if self.fuse_str_compute_2 and product_variant == 'AP': 
				print(Fore.LIGHTCYAN_EX + f"{'>'*3} Checking fuses for Compute2 ---")
				fuse_cmd_override_check(self.fuse_str_compute_2, showresults = False, skip_init= skipinit, bsFuses = 'compute2')
				#skipinit = True
			if self.fuse_str_io_0: 
				print(Fore.LIGHTCYAN_EX + f"{'>'*3} Checking fuses for io0 ---")
				fuse_cmd_override_check(self.fuse_str_io_0, showresults = False, skip_init= skipinit, bsFuses = 'io0')
			if self.fuse_str_io_1: 
				print(Fore.LIGHTCYAN_EX + f"{'>'*3} Checking fuses for io1 ---")
				fuse_cmd_override_check(self.fuse_str_io_1, showresults = False, skip_init= skipinit, bsFuses = 'io1')

	## Logic for bootscript retry
	def bsRetry(self,boot_postcode, stop_after_mrc, bootcont, sv, ipc, boot_string, n, delay = 60):
		attempt = 0
		_boot_string = boot_string

		while attempt < n:
			print(Fore.BLACK + Back.LIGHTGREEN_EX + f"Performing Bootstript Attempt {attempt + 1}" + Back.RESET + Fore.RESET )
			try:
				# Attempt to evaluate _boot_string
				eval(_boot_string)
				self.bsCheck(boot_postcode, stop_after_mrc, bootcont, sv, ipc)
				print(Fore.BLACK + Back.LIGHTGREEN_EX +"Boot string executed successfully..." + Back.RESET + Fore.RESET)
				return True
			except KeyboardInterrupt:
				print(Back.RED + "Boot interrupted by user. Exiting..."+ Back.RESET )
				return 'Cancel'				
			except InterruptedError:
				print(Back.RED + "Boot interrupted by user. Exiting..."+ Back.RESET )
				return 'Cancel'	
			except SyntaxError as se:
				print(f"Syntax error occurred: {se}")
				
			except Exception as e:
				print(Back.RED + f"Attempt {attempt + 1} failed: {e}"+ Back.RESET )
				print(Fore.LIGHTGREEN_EX + Back.YELLOW +"Performing power cycle..." + Back.RESET+ Fore.RESET)
				if 'RSP 11 - Multicast Mixed stats' in str(e):
					print(Back.RED + f"Performing IPC Reconnect.. Trying to fix RSP 11 issue"+ Back.RESET )
					dpm.powercycle()#time.sleep(120)
					time.sleep(120)#ipc.reconnect()
					
					if check_user_cancel(self.execution_state):
						return
					svStatus(checkipc=True, checksvcores=False, refresh=False, reconnect=False)

				if attempt <= n-1: 
					dpm.powercycle()
					time.sleep(delay)  # Wait for a few seconds before retrying

			attempt += 1

		print("Failed to execute boot string after", n, "attempts.")
		return False    		

	def bsCheck(self, boot_postcode, stop_after_mrc, bootcont, sv, ipc):

		if (stop_after_mrc):
			sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=AFTER_MRC_POST
			print("***********************************v********************************************")
			print(f"sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg={AFTER_MRC_POST:#x}")
			print ("%s(curr_state='phase6_cpu_reset_break')" % bootcont)
			print("***********************************v********************************************")
			ipc.go()
			#if FastBoot: ipc.go()#bs.cont(curr_state='phase6_cpu_reset_break')
			#else:	ipc.go() #b.cont(curr_state='phase6_cpu_reset_break')
			_wait_for_post(AFTER_MRC_POST, sleeptime=MRC_POSTCODE_WT, timeout = MRC_POSTCODE_CHECK_COUNT, execution_state=self.execution_state)
			#else:_wait_for_post(BOOT_STOP_POSTCODE, sleeptime=BOOT_POSTCODE_WT, timeout = BOOT_POSTCODE_CHECK_COUNT, additional_postcode=LINUX_POST)
		elif (boot_postcode):
			sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=BOOT_STOP_POSTCODE
			print("***********************************v********************************************")
			print(f"sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg={BOOT_STOP_POSTCODE:#x}")
			print ("%s(curr_state='phase6_cpu_reset_break')" % bootcont)
			print("***********************************v********************************************")
			ipc.go()
			#if FastBoot: ipc.go()#bs.cont(curr_state='phase6_cpu_reset_break')
			#else:	ipc.go() #b.cont(curr_state='phase6_cpu_reset_break')
			#if stop_after_mrc: _wait_for_post(AFTER_MRC_POST, sleeptime=MRC_POSTCODE_WT, timeout = MRC_POSTCODE_CHECK_COUNT)
			_wait_for_post(BOOT_STOP_POSTCODE, sleeptime=BOOT_POSTCODE_WT, timeout = BOOT_POSTCODE_CHECK_COUNT, additional_postcode=LINUX_POST, execution_state=self.execution_state)

		else:
			_wait_for_post(EFI_POST, sleeptime=EFI_POSTCODE_WT, timeout = EFI_POSTCODE_CHECK_COUNT, additional_postcode=LINUX_POST, execution_state=self.execution_state)


#========================================================================================================#
#=============== DEBUG SCRIPTS ==========================================================================#
#========================================================================================================#

def svStatus(checkipc = True, checksvcores = True, refresh = False, reconnect = False):
	ipc = ipccli.baseaccess()
	SysStatus = []
	ipcBad = False
	svBad = False
	svcoredara = None
	ipcthreads = None
	
	if reconnect:
		print(Fore.RED + f'{">"*3} IPC reconnect command requested... '+ Fore.WHITE)
		ipc.reconnect()
		
	# Forcefully rerefsh sv and reconfig ipc, this is used mostly after boot that sv is not properly updated but no error is shown.
	if refresh:
		print(Fore.RED + f'{">"*3} IPC and SV data refresh requested... '+ Fore.WHITE)
		ipc.unlock()
		ipc.forcereconfig()
		sv.refresh()

	## Start Checking flow
	print(Fore.LIGHTGREEN_EX + f'{">"*3} Checking for System readiness... '+ Fore.WHITE)
	ipclocked = ipc.islocked()
	sv_status = not sv.sockets	

	# Trying to check SV and IPC, if any read fails marks them as bad and will request the refresh
	if checkipc:
		try:
			print(Fore.LIGHTGREEN_EX + f'{">"*3} Checking IPC Status... '+ Fore.WHITE)
			ipcstatus = ipc.isrunning()
			ipcthreads = f'{Fore.BLACK}{(Back.LIGHTGREEN_EX + " Running " + Back.RESET) if ipcstatus else (Back.YELLOW +" Halted "+ Back.RESET)}{Fore.WHITE}'
		except:
			ipcthreads = f'{Fore.BLACK}{(Back.RED + " Down " + Back.RESET)}{Fore.WHITE}'
			ipcBad = True

	if checksvcores:
		try:
			print(Fore.LIGHTGREEN_EX + f'{">"*3} Checking SV Status... '+ Fore.WHITE)
			svcores = len(sv.sockets.cpu.modules)
			svcoredara = f'{Fore.BLACK}{Back.LIGHTGREEN_EX}{" Up "}{Back.RESET}{Fore.WHITE}'

		except:
			svcoredara = f'{Fore.BLACK}{Back.RED}{" Down "}{Back.RESET}{Fore.WHITE}'

			svBad = True

	## Fancy Table for showing System Status
	SysStatus.append(["Feature", "Status"])
	SysStatus.append(["IPC Status",f'{Fore.BLACK}{(Back.RED + " Locked " + Back.RESET) if ipclocked else (Back.LIGHTGREEN_EX +" Unlocked "+ Back.RESET)}{Fore.WHITE}'])
	SysStatus.append(["IPC Threads",f'{ipcthreads}'])
	SysStatus.append(["SV Status",f'{Fore.BLACK}{(Back.RED + " Not Ready " + Back.RESET) if sv_status else (Back.LIGHTGREEN_EX +" Ready "+ Back.RESET)}{Fore.WHITE}'])
	SysStatus.append(["SV CORE Data",f'{svcoredara}'])
	

	table = tabulate(SysStatus, headers="firstrow", tablefmt="grid")

	print(table)
	
	if (ipclocked or ipcBad):
		print(Fore.RED + f'{">"*3} IPC is not ready, performing unlock and reconfig'+ Fore.WHITE)
		ipc.unlock()
		ipc.forcereconfig()

	if (not sv.sockets or svBad):
		print(Fore.RED + f'{">"*3} SV not initialized refreshing '+ Fore.WHITE)
		sv.refresh()
		
	if (sv.sockets and ipc.isunlocked()):
		print(Fore.LIGHTGREEN_EX + f'{">"*3} SV is unlocked with updated nodes, ready to use '+ Fore.WHITE)
	

# def setCBB(boot = True, fastboot = False, load_fuses = True, resetGlobals = False):
# 	'''
# 	Sets up system to run with 1 enabled module per compute.
	
# 	Inputs:
# 		boot: (Boolean, Default=True) Will call bootscript with new setting
# 		fastboot: (Boolean, Default=False) Will call bootscript with faster setting
# 		load_fuses: (Boolean, Default=True) Calls fuse load for dpm.fuses
# 		resetGlobals: (Boolean, Default=False) Resets globals for bootscript call
# 	'''

# 	# Variables Init
# 	sv = _get_global_sv()
# 	die = sv.socket0.target_info["device_name"] # Get Die name
# 	cbbs = sv.socket0.cbbs.name # Get compute names array	

# 	if (not die.startswith("DMR")):
# 		print (f"Sorry. This method is not available for {die}.")
# 		return
	
# 	if resetGlobals: reset_globals()
	
# 	# Building arrays based on system structure
# 	_moduleMasks= {cbb: 0xffffffff for cbb in cbbs} # Module mask filled with 1 for every compute
# 	_llcMasks= {cbb: 0xffffffff for cbb in cbbs} # LLC mask filled with 1 for every compute
# 	masks = dpm.fuses(rdFuses = load_fuses, sktnum =[0]) # Read module and LLC masks from fuses
# 	print(masks)

# 	print("\n"+"-"*62)
# 	print("| A single cbb  will be enabled |")
# 	print("-"*62+"\n")
# 	for cbb_name in cbbs:
# 		accepted_input = False
# 		while(not accepted_input): # Keep asking for input, if an invalid value was given
# 			disable_cbb = input(f"\n Disable {cbb_name}? Y/[N]: ").upper()
# 			if(disable_cbb == "N" or disable_cbb == ""): # Compute remains enabled
# 				_moduleMasks[cbb_name] = masks[f'ia_{cbb_name}']
# 				_llcMasks[cbb_name] = masks[f'llc_{cbb_name}']
# 			else:
# 				new_cbbMask = 0xFFFFFFFF # Mask filled with 1 except the desired target physical module
# 				_moduleMasks[cbb_name] = new_cbbMask # Combine calculated modulemask and the mask given by dpm.fuses
# 				_llcMasks[cbb_name] = masks[f'llc_{cbb_name}'] # Assign LLC mask given by dpm.fuses (stays the same, this script does not modify LLCs)
# 			accepted_input = True

# 	for cbb_name in cbbs:
# 		# Print masks
# 		print  (f"\n{cbb_name}: module disables mask: {hex(_moduleMasks[cbb_name])}") 
# 		print  (f"{cbb_name}: llc disables mask:  {hex(_llcMasks[cbb_name])}") 
	
# 	if boot:
# 		if fastboot:
# 			_fastboot(masks=masks)
# 		else:
# 			_doboot(masks=masks, modulemask=_moduleMasks, llcmask=_llcMasks)


# ## GNR needs at least one module enabled per COMPUTE, we are limited here, as WA we are leaving the selected compute alive plus the first full slice on the other COMPUTES.
# def setMesh(stop_after_mrc=False, pm_enable_no_vf=False, lsb = False, boot = True, fastboot = False, load_fuses = True, resetGlobals = False, clusterCheck = False):
# 	'''
# 	Sets modules and LLCs to run a specific or custom configuration. 
	
# 	Inputs:
# 		stop_after_mrc: (Boolean, Default=False) Input used in _boot and _fastboot. Flag to stop after mrc.
# 		pm_enable_no_vf: (Boolean, Default=False) Input used in _boot and _fastboot. pm enable.
# 		boot: (Boolean, Default=True) Will call bootscript with new setting
# 		fastboot: (Boolean, Default=False) Will call bootscript with faster setting
# 		load_fuses: (Boolean, Default=True) Calls fuse load for dpm.fuses
# 		resetGlobals: (Boolean, Default=False) Resets globals for bootscript call
# 		clusterCheck: (Boolean, Default=False) Input for dpm.pseudo_bs.
# 		lsb: (Boolean, Default=False) Input for dpm.pseudo_bs.	
# 	'''
# 	## Variables Init
# 	ht_dis = False
# 	sv = _get_global_sv()
# 	die = sv.socket0.target_info["segment"] # Get Die name
# 	computes = sv.socket0.computes.name # Get compute names array	
	 
# 	if (not die.startswith("CWF")):
# 		print (f"Sorry.  This method is not available for {die}.")
# 		return
	
# 	if resetGlobals: reset_globals()

# 	accepted_input = False
# 	while(not accepted_input):
# 		print("\n"+"-"*38)
# 		print("| Select a module mask configuration |")
# 		print("-"*38+"\n")

# 		print("1) FirstPass: Booting only with the first half of the 1st compute")
# 		print("2) SecondPass: Booting only with the second half of the 1st compute")
# 		print("3) ThirdPass: Booting only with the first half of the 2nd compute")
# 		print("4) FourthPass: Booting only with the second half of the 2nd compute")
# 		print("5) FifthPass: Booting only with the first half of the 3rd compute")
# 		print("6) SixthPass: Booting only with the second half of the 3rd compute")
# 		print("7) Custom: Booting with user mix & match configuration, Cols or Rows")
# 		print("8) External: Use configuration from file .\\ConfigFiles\\CWFMasksDebug.json")

# 		inputConfig = input("\nPlease input the number for desired target configuration: ")
# 		accepted_input = True
# 		CustomConfig = []
# 		if inputConfig == "1":
# 			targetConfig = 'FirstPass'
# 		elif inputConfig == "2":
# 			targetConfig = 'SecondPass'
# 		elif inputConfig == "3":
# 			targetConfig = 'ThirdPass'
# 		elif inputConfig == "4":
# 			targetConfig = 'FourthPass'
# 		elif inputConfig == "5":
# 			targetConfig = 'FifthPass'
# 		elif inputConfig == "6":
# 			targetConfig = 'SixthPass'
# 		elif inputConfig == "7":
# 			targetConfig = 'Custom'
# 			CustomConfig = input("Please input the desired custom configuration: ")
# 		elif inputConfig == "8":
# 			targetConfig = 'External'
# 		else:
# 			print("INPUT ERROR.\nTry again.")
# 			accepted_input = False

# 	masks = dpm.fuses(rdFuses = load_fuses, sktnum =[0]) # Read module and LLC masks from fuses

# 	# Call DPMChecks Mesh script for mask change, we are not booting here
# 	module_count, llc_count, Masks_test = dpm.pseudo_bs(ClassMask = targetConfig, Custom = CustomConfig, boot = False, use_core = False, htdis = ht_dis, fuse_read = load_fuses, s2t = True, masks = masks, clusterCheck = clusterCheck, lsb = lsb)

# 	# Building arrays based on system structure
# 	_moduleMasks= {die: {comp: Masks_test[targetConfig][f'core_comp_{comp[-1]}'] for comp in computes}}
# 	_llcMasks= {die: {comp: Masks_test[targetConfig][f'llc_comp_{comp[-1]}'] for comp in computes}}

	

# 	# Below dicts are only for converting of variables str to int
# 	modules = {}
# 	llcs = {}
	
# 	print(f'\nSetting new Masks for {targetConfig} configuration:\n')
# 	for compute in _moduleMasks[die].keys():
		
# 		modules[compute] =  int(_moduleMasks[die][compute],16)
# 		llcs[compute] =  int(_llcMasks[die][compute],16)
# 		print  (f'\t{compute}:'+ "module disables mask:  0x%x" % (modules[compute])) 
# 		print  (f'\t{compute}:'+ "slice disables mask: 0x%x" % (llcs[compute])) 			

# 	if boot:
# 		if fastboot:
# 			_fastboot(stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)
# 		else:
# 			_doboot(masks=masks, modulemask=modules, llcmask=llcs, stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)


## Boots the unit using the bootscript with fuse_strings.
def _doboot(masks=None, modulemask=None, llcmask=None, stop_after_mrc=False, fixed_core_freq = None, fixed_mesh_freq=None, avx_mode = None, acode_dis=None, vp2intersect_en=True, pm_enable_no_vf=False, ia_fw_p1=None, ia_fw_pn=None, ia_fw_pm=None, ia_fw_pboot=None, ia_fw_pturbo=None, ia_vf_curves=None, ia_imh_p1=None, ia_imh_pn=None, ia_imh_pm=None, ia_imh_pturbo=None, cfc_fw_p0=None, cfc_fw_p1=None, cfc_fw_pm=None, cfc_cbb_p0=None, cfc_cbb_p1=None, cfc_cbb_pm=None, cfc_io_p0=None, cfc_io_p1=None, cfc_io_pm=None, cfc_mem_p0=None, cfc_mem_p1=None, cfc_mem_pm=None):
	'''
	Calls bootscript, if modulemask and llcmask is not set, then both llc_slice_disable and ia_core_disable get masks value

	Inputs:
		masks: (Dictionary, Default=None) module and LLC masks.
		modulemask: (Dictionary, Default=None) override module mask.
		llcmask: (Dictionary, Default=None) override LLC mask.
		stop_after_mrc: (Boolean, Default=False) If set, will stop after MRC is complete
		fixed_core_freq: (Boolean, Default=None) if set, set core P0,P1,Pn and pmin 
		fixed_mesh_freq: (Boolean, Default=None) if set, set mesh P0,P1,Pn and pmin
		fixed_io_freq: (Boolean, Default=None) if set, set io P0,P1,Pn and pmin
		avx_mode: (String, Default=None)  Set AVX mode
		acode_dis: (Boolean, Default=None) Disable acode 
		vp2intersect_en: (Boolean, Default=None) If set, will enable VPINTERSECT instruction ( needed for some Dragon Content )
		ia_p0: (Int, Default=None) CORE P0
		ia_p1: (Int, Default=None) CORE P1
		ia_pn: (Int, Default=None) CORE Pn
		ia_pm: (Int, Default=None) CORE Pm
		cfc_p0: (Int, Default=None) CFC P0
		cfc_p1: (Int, Default=None) CFC P1
		cfc_pn: (Int, Default=None) CFC Pn
		cfc_pm: (Int, Default=None) CFC Pm
		io_p0: (Int, Default=None) IO P0
		io_p1: (Int, Default=None) IO P1
		io_pn: (Int, Default=None) IO Pn
		io_pm: (Int, Default=None) IO Pm
		pm_enable_no_vf: (Boolean, Default=False) if True, will use fuse file pm_enable_no_vf.cfg to configure fuses (cfc/ia ratios and ia volt=1V) as tester	
'''

	global _boot_string
	sv = _get_global_sv()
	ipc = _get_global_ipc()
	die = sv.socket0.target_info["device_name"]
	# ht_dis = sv.socket0.compute0.fuses.pcu.capid_capid0_ht_dis_fuse
	bootFuses = dpm.dev_dict('DMRFuseFileConfigs.json') # Fuses for booting

	cbb_names, config = get_compute_config()

	# Need to move this to a better implementation
	product = {	'DMR_CLTAP':
				{   
					'config': cbb_names,
					'segment': 'DMRUCC',
					'compute_config': config}
				}
	
	# Retrieve local path
	parent_dir = os.path.dirname(os.path.realpath(__file__))
	fuses_dir = os.path.join(parent_dir, 'Fuse')
	
	
	b_extra = global_boot_extra
	_fuse_str = []
	_fuse_str_cbb = []
	_fuse_str_imh = []
	_fuse_str_io = []
	_fuse_files = []
	_fuse_files_compute = []
	_fuse_files_io = []
	_llc = []
	_ia = []

	# htdis_comp = [#'scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_fused_ht_dis=0x1', 
	# 		'pcu.capid_capid0_ht_dis_fuse=0x1']
	# htdis_io = ['punit_iosf_sb.soc_capid_capid0_max_lp_en=0x1','punit_iosf_sb.soc_capid_capid0_ht_dis_fuse=0x1']
	#vp2i_en_comp = ['scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_vp2intersect_dis=0x0']

	# if ht_dis == None and global_ht_dis !=None: ht_dis = global_ht_dis
	# if acode_dis == None and global_acode_dis !=None: acode_dis = global_acode_dis
	if global_boot_stop_after_mrc: stop_after_mrc = True
	if avx_mode == None and global_avx_mode !=None: avx_mode = global_avx_mode
	if fixed_core_freq == None and global_fixed_core_freq !=None: fixed_core_freq = global_fixed_core_freq
	if ia_fw_p1 == None and global_ia_fw_p1 !=None: ia_fw_p1 = global_ia_fw_p1
	if ia_fw_pn == None and global_ia_fw_pn !=None: ia_fw_pn = global_ia_fw_pn
	if ia_fw_pm == None and global_ia_fw_pm !=None: ia_fw_pm = global_ia_fw_pm
	if ia_fw_pboot == None and global_ia_fw_pboot !=None: ia_fw_pboot = global_ia_fw_pboot
	if ia_fw_pturbo == None and global_ia_fw_pturbo !=None: ia_fw_pturbo = global_ia_fw_pturbo
	if ia_vf_curves == None and global_ia_vf_curves !=None: ia_vf_curves = global_ia_vf_curves

	if ia_imh_p1 == None and global_ia_imh_p1 !=None: ia_imh_p1 = global_ia_imh_p1
	if ia_imh_pn == None and global_ia_imh_pn !=None: ia_imh_pn = global_ia_imh_pn
	if ia_imh_pm == None and global_ia_imh_pm !=None: ia_imh_pm = global_ia_imh_pm
	if ia_imh_pturbo == None and global_ia_imh_pturbo !=None: ia_imh_pturbo = global_ia_imh_pturbo

	if fixed_mesh_freq == None and global_fixed_mesh_freq !=None: fixed_mesh_freq = global_fixed_mesh_freq
	if cfc_fw_p0 == None and global_cfc_fw_p0 !=None: cfc_fw_p0 = global_cfc_fw_p0
	if cfc_fw_p1 == None and global_cfc_fw_p1 !=None: cfc_fw_p1 = global_cfc_fw_p1
	if cfc_fw_pm == None and global_cfc_fw_pm  !=None: cfc_fw_pm = global_cfc_fw_pm
	if cfc_cbb_p0 == None and global_cfc_cbb_p0 !=None: cfc_cbb_p0 = global_cfc_cbb_p0
	if cfc_cbb_p1 == None and global_cfc_cbb_p1 !=None: cfc_cbb_p0 = global_cfc_cbb_p1
	if cfc_cbb_pm == None and global_cfc_cbb_pm !=None: cfc_cbb_p0 = global_cfc_cbb_pm

	# if fixed_io_freq == None and global_fixed_io_freq !=None: fixed_io_freq = global_fixed_io_freq
	# if io_p0 == None and global_io_p0 !=None: io_p0 = global_io_p0
	if cfc_io_p0 == None and global_cfc_io_p0 !=None: cfc_io_p0 = global_cfc_io_p0
	if cfc_io_p1 == None and global_cfc_io_p1 !=None: cfc_io_p1 = global_cfc_io_p1
	if cfc_io_pm == None and global_cfc_io_pm !=None: cfc_io_pm = global_cfc_io_pm
	if cfc_mem_p0 == None and global_cfc_mem_p0 !=None: cfc_mem_p0 = global_cfc_mem_p0
	if cfc_mem_p1 == None and global_cfc_mem_p1 !=None: cfc_mem_p1 = global_cfc_mem_p1
	if cfc_mem_pm == None and global_cfc_mem_pm !=None: cfc_mem_pm = global_cfc_mem_pm

	if (fixed_core_freq != None):	
		ia_fw_p1 = fixed_core_freq
		ia_fw_pn = fixed_core_freq
		ia_fw_pm = fixed_core_freq
		ia_fw_pboot = fixed_core_freq
		ia_fw_pturbo = fixed_core_freq
		ia_vf_curves = fixed_core_freq

		ia_imh_p1 = fixed_core_freq
		ia_imh_pn = fixed_core_freq
		ia_imh_pm = fixed_core_freq
		ia_imh_pturbo = fixed_core_freq
	if (fixed_mesh_freq != None):
		cfc_fw_p0 = fixed_mesh_freq
		cfc_fw_p1 = fixed_mesh_freq
		cfc_fw_pm = fixed_mesh_freq

		cfc_cbb_p0 = fixed_mesh_freq
		cfc_cbb_p1 = fixed_mesh_freq
		cfc_cbb_pm = fixed_mesh_freq

		cfc_io_p0 = fixed_mesh_freq
		cfc_io_p1 = fixed_mesh_freq
		cfc_io_pm = fixed_mesh_freq

		cfc_mem_p0 = fixed_mesh_freq
		cfc_mem_p1 = fixed_mesh_freq
		cfc_mem_pm = fixed_mesh_freq


	print('\nUsing the following configuration for unit boot: ')
	# if ht_dis: print('\tHyper Threading disabled')
	if acode_dis: print('\tAcode disabled')
	if stop_after_mrc: print('\tStop after MRC')
	print(f'\tConfigured License Mode: {avx_mode}')
	print(f'\tCore Frequencies:')
	print(f'\t\tIA p1: {ia_fw_p1}')
	print(f'\t\tIA pn: {ia_fw_pn}')
	print(f'\t\tIA pm: {ia_fw_pm}')
	print(f'\t\tIA fw boot: {ia_fw_pboot}')
	print(f'\t\tIA fw turbo: {ia_fw_pturbo}')
	print(f'\t\tIA fw vf curves: {ia_vf_curves}')
	print(f'\t\tIA imh p1: {ia_imh_p1}')
	print(f'\t\tIA imh pn: {ia_imh_pn}')
	print(f'\t\tIA imh pm: {ia_imh_pm}')
	print(f'\t\tIA imh turbo: {ia_imh_pturbo}')
	print(f'\tCompute Mesh Frequencies:')
	print(f'\t\tCFC MESH fw p0: {cfc_fw_p0}')
	print(f'\t\tCFC MESH fw p1: {cfc_fw_p1}')
	print(f'\t\tCFC MESH fw pn: {cfc_fw_pm}')
	print(f'\t\tCFC MESH cbb p0: {cfc_cbb_p0}')
	print(f'\t\tCFC MESH cbb p1: {cfc_cbb_p1}')
	print(f'\t\tCFC MESH cbb pn: {cfc_cbb_pm}')
	print(f'\t\tCFC MESH io p0: {cfc_io_p0}')
	print(f'\t\tCFC MESH io p1: {cfc_io_p1}')
	print(f'\t\tCFC MESH io pn: {cfc_io_pm}')
	print(f'\t\tCFC MESH mem p0: {cfc_mem_p0}')
	print(f'\t\tCFC MESH mem p1: {cfc_mem_p1}')
	print(f'\t\tCFC MESH mem pn: {cfc_mem_pm}')
	

	try:
		temp = sv.sockets.imhs.fuses.hwrs_top_late.ip_disable_fuses_dword6_core_disable.get_value()[0] 
	except:
		itp.forcereconfig()
		itp.unlock()
		sv.refresh()
	
	if (pm_enable_no_vf == True): 
		_fuse_files_compute=[f'{fuses_dir}\\pm_enable_no_vf_computes.cfg']
		_fuse_files_io = [f'{fuses_dir}\\pm_enable_no_vf_ios.cfg'] 


	if (stop_after_mrc): b_extra+=', gotil=\"phase6_cpu_reset_break\"'
	
	
	if cfc_fw_p0: _fuse_str_cbb += assign_values_to_regs(bootFuses['CFC']['fwFreq']['p0'], cfc_fw_p0)
	if cfc_fw_p1: _fuse_str_cbb += assign_values_to_regs(bootFuses['CFC']['fwFreq']['p1'], cfc_fw_p1)
	if cfc_fw_pm: _fuse_str_cbb += assign_values_to_regs(bootFuses['CFC']['fwFreq']['min'], cfc_fw_pm)

	if cfc_cbb_p0: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['cbbFreq']['p0'], cfc_cbb_p0)
	if cfc_cbb_p1: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['cbbFreq']['p1'], cfc_cbb_p1)
	if cfc_cbb_pm: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['cbbFreq']['min'], cfc_cbb_pm)

	if cfc_io_p0: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['ioFreq']['p0'], cfc_io_p0)
	if cfc_io_p1: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['ioFreq']['p1'], cfc_io_p1)
	if cfc_io_pm: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['ioFreq']['min'], cfc_io_pm)

	if cfc_mem_p0: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['memFreq']['p0'], cfc_mem_p0)
	if cfc_mem_p1: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['memFreq']['p1'], cfc_mem_p1)
	if cfc_mem_pm: _fuse_str_imh += assign_values_to_regs(bootFuses['CFC']['memFreq']['min'], cfc_mem_pm)

	if ia_fw_p1: _fuse_str_cbb += assign_values_to_regs(bootFuses['IA']['fwFreq']['p1'], ia_fw_p1)
	if ia_fw_pn: _fuse_str_cbb += assign_values_to_regs(bootFuses['IA']['fwFreq']['pn'], ia_fw_pn)
	if ia_fw_pm: _fuse_str_cbb += assign_values_to_regs(bootFuses['IA']['fwFreq']['min'], ia_fw_pm)
	if ia_fw_pboot: _fuse_str_cbb += assign_values_to_regs(bootFuses['IA']['fwFreq']['boot'], ia_fw_pboot)
	if ia_fw_pturbo: _fuse_str_cbb += assign_values_to_regs(bootFuses['IA']['fwFreq']['turbo'], ia_fw_pturbo)
	if ia_vf_curves: _fuse_str_cbb += assign_values_to_regs(bootFuses['IA']['fwFreq']['vf_curves'], ia_vf_curves)
		
	if ia_imh_p1: _fuse_str_imh += assign_values_to_regs(bootFuses['IA']['imhFreq']['p1'], ia_imh_p1)
	if ia_imh_pn: _fuse_str_imh += assign_values_to_regs(bootFuses['IA']['imhFreq']['pn'], ia_imh_pn)
	if ia_imh_pm: _fuse_str_imh += assign_values_to_regs(bootFuses['IA']['imhFreq']['min'], ia_imh_pm)
	if ia_imh_pturbo: _fuse_str_imh += assign_values_to_regs(bootFuses['IA']['imhFreq']['turbo'], ia_imh_pturbo)

	if (avx_mode != None):
		if (avx_mode) in range (0,8):
			int_mode = avx_mode
		elif avx_mode == "128":
			int_mode = 1        
		elif avx_mode == "256":
			int_mode = 3
		elif avx_mode == "512":
			int_mode=5
		elif avx_mode == "TMUL":
			int_mode=7
		else:
			raise ValueError("Invalid AVX Mode")
		ia_min_lic = bootFuses['IA_license']['cbb']['min']
		ia_max_lic = bootFuses['IA_license']['cbb']['max']
		# ia_def_lic = IA_license['default']
		# _fuse_str += [f'{ia_min_lic}=0x%x' % int_mode,f'{ia_def_lic}=0x%x' % int_mode]
		_fuse_str_cbb += [f'{ia_min_lic}=0x%x' % int_mode]
		_fuse_str_cbb += [f'{ia_max_lic}=0x%x' % int_mode]
	# print(f'fuse_str {_fuse_str_compute}')

	if _fuse_str_cbb:
		updated_fuse_str_cbb = [value.replace("sv.sockets.cbbs.base.", "") for value in _fuse_str_cbb]
		_fuse_str_cbb = updated_fuse_str_cbb

	if _fuse_str_imh:
		updated_fuse_str_imh = [value.replace("sv.sockets.imhs.", "") for value in _fuse_str_imh]
		_fuse_str_imh = updated_fuse_str_imh

	# _modulemask ={}
	# _llcmask = {}
	
	# for key, value in masks.items():
	# 	newkey = f'cbb{key[-1]}'
	# 	if key.startswith('ia_'):
	# 		_modulemask[newkey] = value
	# 	if key.startswith('llc_'):
	# 		_llcmask[newkey] = value
	
	if (modulemask == None): 
		_boot_disable_ia = ''
	else:
		for key, value in modulemask.items():
			_ia +=  [('"cbb_base%s":%s')  % (key[-1],hex(value))]
			_boot_disable_ia = ','.join(_ia)

	if (llcmask == None): 
		_boot_disable_llc = ''
	else:
		for key, value in llcmask.items():
			_llc +=  [('"cbb_base%s":%s')  % (key[-1],hex(value))]
		_boot_disable_llc = ','.join(_llc)

	FastBoot = False
	if FastBoot:
		bootopt = 'bs.fast_boot'
		bootcont = 'bs.cont'
	else:
		bootopt = 'b.go'
		bootcont = 'b.cont'

	# _boot_string = ('%s(fused_unit=True, enable_strap_checks=False,compute_config="%s",enable_pm=True,segment="%s" %s, %s, %s fuse_str_compute = %s,fuse_str_io = %s, fuse_files_compute=[%s], fuse_files_io=[%s],AXON_UPLOAD_ENABLED = False)') % (bootopt, product[die]['compute_config'], product[die]['segment'], b_extra, _boot_disable_ia, _boot_disable_llc,_fuse_str_compute,_fuse_str_io,_fuse_files_compute, _fuse_files_io)
	_boot_string = ('%s(fused_unit=False, pwrgoodmethod="usb", compute_config="%s", ia_core_disable={%s}, llc_slice_disable={%s}, fuse_str={"cbb_base":%s, "imh":%s})') % (bootopt, product[die]['compute_config'], _boot_disable_ia, _boot_disable_llc, _fuse_str_cbb, _fuse_str_imh)

	print("*"*20)
	if FastBoot: print('import users.THR.PythonScripts.thr.GnrBootscriptOverrider as bs') # CHECK THIS FOR IMPLEMENTATION
	else:	print("import toolext.bootscript.boot as b")
	print (_boot_string)
	print("***********************************v********************************************")
	if global_dry_run == False:
		eval(_boot_string)
		#print("********************************************************************************")
		#print (_boot_string)
		#print("********************************************************************************")
		if (stop_after_mrc):
			# sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=AFTER_MRC_POST
			sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6]=AFTER_MRC_POST
			print("***********************************v********************************************")
			print(f"sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg={AFTER_MRC_POST}")
			print ("%s(curr_state='phase6_cpu_reset_break')" % bootcont)
			print("***********************************v********************************************")
			if FastBoot: bs.cont(curr_state='phase6_cpu_reset_break')
			else:	b.cont(curr_state='phase6_cpu_reset_break')
			_wait_for_post(AFTER_MRC_POST)
		else:
			_wait_for_post(EFI_POST, sleeptime=120)
		sv_refreshed = False

def my_method(socket: str, die: str, fuse_override_iteration=None)->int:
    sv = namednodes.sv.get_manager(['socket'])
    sv.get_all()
    print(f"Testing")
    sv.sockets.cbbs.computes.fuses.core0_fuse.core_fuse_core_fuse_acode_ia_base_vf_ratio_0=0x8
    return 0 

b.go(dynamic_fuse_inject={"imh":my_method})

## Fastboot option to boot the unit using itp.resettarget, works with SLICE MODE only
def _fastboot(masks=None, modulemask=None, llcmask=None, stop_after_mrc=False, fixed_core_freq = None, fixed_mesh_freq=None, fixed_io_freq=None, avx_mode = None, acode_dis=None,  vp2intersect_en=True, pm_enable_no_vf=False, ia_fw_p1=None, ia_fw_pn=None, ia_fw_pm=None, ia_fw_pboot=None, ia_fw_pturbo=None, ia_vf_curves=None, ia_imh_p1=None, ia_imh_pn=None, ia_imh_pm=None, ia_imh_pturbo=None, cfc_fw_p0=None, cfc_fw_p1=None, cfc_fw_pm=None, cfc_cbb_p0=None, cfc_cbb_p1=None, cfc_cbb_pm=None, cfc_io_p0=None, cfc_io_p1=None, cfc_io_pm=None, cfc_mem_p0=None, cfc_mem_p1=None, cfc_mem_pm=None):
	'''
	Calls bootscript with a faster configuration, if modulemask and llcmask is not set, then both llc_slice_disable and ia_core_disable get masks value

	Inputs:
		masks: (Dictionary, Default=None) module and LLC masks.
		modulemask: (Dictionary, Default=None) override module mask.
		llcmask: (Dictionary, Default=None) override LLC mask.
		stop_after_mrc: (Boolean, Default=False) If set, will stop after MRC is complete
		fixed_core_freq: (Boolean, Default=None) if set, set core P0,P1,Pn and pmin 
		fixed_mesh_freq: (Boolean, Default=None) if set, set mesh P0,P1,Pn and pmin
		fixed_io_freq: (Boolean, Default=None) if set, set io P0,P1,Pn and pmin
		avx_mode: (String, Default=None)  Set AVX mode
		acode_dis: (Boolean, Default=None) Disable acode 
		vp2intersect_en: (Boolean, Default=None) If set, will enable VPINTERSECT instruction ( needed for some Dragon Content )
		ia_p0: (Int, Default=None) CORE P0
		ia_p1: (Int, Default=None) CORE P1
		ia_pn: (Int, Default=None) CORE Pn
		ia_pm: (Int, Default=None) CORE Pm
		cfc_p0: (Int, Default=None) CFC P0
		cfc_p1: (Int, Default=None) CFC P1
		cfc_pn: (Int, Default=None) CFC Pn
		cfc_pm: (Int, Default=None) CFC Pm
		io_p0: (Int, Default=None) IO P0
		io_p1: (Int, Default=None) IO P1
		io_pn: (Int, Default=None) IO Pn
		io_pm: (Int, Default=None) IO Pm
		pm_enable_no_vf: (Boolean, Default=False) if True, will use fuse file pm_enable_no_vf.cfg to configure fuses (cfc/ia ratios and ia volt=1V) as tester	
'''

	global _boot_string
	sv = _get_global_sv()
	ipc = _get_global_ipc()
	die = sv.socket0.target_info["device_name"]
	# ht_dis = ( sv.socket0.compute0.fuses.pcu.capid_capid0_ht_dis_fuse == True )
	bootFuses = dpm.dev_dict('DMRFuseFileConfigs.json') # Fuses for booting
	
	cbb_names, config = get_compute_config()

	product = {	'DMR_CLTAP':
				{   
					'config': cbb_names,
					'segment': 'DMRUCC',
					'compute_config': config}
				}
	
	# Retrieve local path
	parent_dir = os.path.dirname(os.path.realpath(__file__))
	fuses_dir = os.path.join(parent_dir, 'Fuse')
	
	
	b_extra = global_boot_extra
	_fuse_str = []
	_fuse_str_compute = []
	_fuse_str_io = []
	_fuse_files = []
	_fuse_files_compute = []
	_fuse_files_io = []
	_llc = []
	_ia = []


	## Need to include in configFile, will move later
	#vp2i_en_comp = ['sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_vp2intersect_dis=0x0']
	
	##Frequency fuses
	if global_boot_stop_after_mrc: stop_after_mrc = True
	if avx_mode == None and global_avx_mode !=None: avx_mode = global_avx_mode
	if fixed_core_freq == None and global_fixed_core_freq !=None: fixed_core_freq = global_fixed_core_freq
	if ia_fw_p1 == None and global_ia_fw_p1 !=None: ia_fw_p1 = global_ia_fw_p1
	if ia_fw_pn == None and global_ia_fw_pn !=None: ia_fw_pn = global_ia_fw_pn
	if ia_fw_pm == None and global_ia_fw_pm !=None: ia_fw_pm = global_ia_fw_pm
	if ia_fw_pboot == None and global_ia_fw_pboot !=None: ia_fw_pboot = global_ia_fw_pboot
	if ia_fw_pturbo == None and global_ia_fw_pturbo !=None: ia_fw_pturbo = global_ia_fw_pturbo
	if ia_vf_curves == None and global_ia_vf_curves !=None: ia_vf_curves = global_ia_vf_curves

	if ia_imh_p1 == None and global_ia_imh_p1 !=None: ia_imh_p1 = global_ia_imh_p1
	if ia_imh_pn == None and global_ia_imh_pn !=None: ia_imh_pn = global_ia_imh_pn
	if ia_imh_pm == None and global_ia_imh_pm !=None: ia_imh_pm = global_ia_imh_pm
	if ia_imh_pturbo == None and global_ia_imh_pturbo !=None: ia_imh_pturbo = global_ia_imh_pturbo

	if fixed_mesh_freq == None and global_fixed_mesh_freq !=None: fixed_mesh_freq = global_fixed_mesh_freq
	if cfc_fw_p0 == None and global_cfc_fw_p0 !=None: cfc_fw_p0 = global_cfc_fw_p0
	if cfc_fw_p1 == None and global_cfc_fw_p1 !=None: cfc_fw_p1 = global_cfc_fw_p1
	if cfc_fw_pm == None and global_cfc_fw_pm  !=None: cfc_fw_pm = global_cfc_fw_pm
	if cfc_cbb_p0 == None and global_cfc_cbb_p0 !=None: cfc_cbb_p0 = global_cfc_cbb_p0
	if cfc_cbb_p1 == None and global_cfc_cbb_p1 !=None: cfc_cbb_p0 = global_cfc_cbb_p1
	if cfc_cbb_pm == None and global_cfc_cbb_pm !=None: cfc_cbb_p0 = global_cfc_cbb_pm

	# if fixed_io_freq == None and global_fixed_io_freq !=None: fixed_io_freq = global_fixed_io_freq
	# if io_p0 == None and global_io_p0 !=None: io_p0 = global_io_p0
	if cfc_io_p0 == None and global_cfc_io_p0 !=None: cfc_io_p0 = global_cfc_io_p0
	if cfc_io_p1 == None and global_cfc_io_p1 !=None: cfc_io_p1 = global_cfc_io_p1
	if cfc_io_pm == None and global_cfc_io_pm !=None: cfc_io_pm = global_cfc_io_pm
	if cfc_mem_p0 == None and global_cfc_mem_p0 !=None: cfc_mem_p0 = global_cfc_mem_p0
	if cfc_mem_p1 == None and global_cfc_mem_p1 !=None: cfc_mem_p1 = global_cfc_mem_p1
	if cfc_mem_pm == None and global_cfc_mem_pm !=None: cfc_mem_pm = global_cfc_mem_pm

	if (fixed_core_freq != None):	
		ia_fw_p1 = fixed_core_freq
		ia_fw_pn = fixed_core_freq
		ia_fw_pm = fixed_core_freq
		ia_fw_pboot = fixed_core_freq
		ia_fw_pturbo = fixed_core_freq
		ia_vf_curves = fixed_core_freq

		ia_imh_p1 = fixed_core_freq
		ia_imh_pn = fixed_core_freq
		ia_imh_pm = fixed_core_freq
		ia_imh_pturbo = fixed_core_freq
	if (fixed_mesh_freq != None):
		cfc_fw_p0 = fixed_mesh_freq
		cfc_fw_p1 = fixed_mesh_freq
		cfc_fw_pm = fixed_mesh_freq

		cfc_cbb_p0 = fixed_mesh_freq
		cfc_cbb_p1 = fixed_mesh_freq
		cfc_cbb_pm = fixed_mesh_freq

		cfc_io_p0 = fixed_mesh_freq
		cfc_io_p1 = fixed_mesh_freq
		cfc_io_pm = fixed_mesh_freq

		cfc_mem_p0 = fixed_mesh_freq
		cfc_mem_p1 = fixed_mesh_freq
		cfc_mem_pm = fixed_mesh_freq

	print('\nUsing the following configuration for unit boot: ')
	# if ht_dis: print('\tHyper Threading disabled')
	if acode_dis: print('\tAcode disabled')
	if stop_after_mrc: print('\tStop after MRC')
	print(f'\tConfigured License Mode: {avx_mode}')
	print(f'\tCore Frequencies:')
	print(f'\t\tIA p1: {ia_fw_p1}')
	print(f'\t\tIA pn: {ia_fw_pn}')
	print(f'\t\tIA pm: {ia_fw_pm}')
	print(f'\t\tIA fw boot: {ia_fw_pboot}')
	print(f'\t\tIA fw turbo: {ia_fw_pturbo}')
	print(f'\t\tIA fw vf curves: {ia_vf_curves}')
	print(f'\t\tIA imh p1: {ia_imh_p1}')
	print(f'\t\tIA imh pn: {ia_imh_pn}')
	print(f'\t\tIA imh pm: {ia_imh_pm}')
	print(f'\t\tIA imh turbo: {ia_imh_pturbo}')
	print(f'\tCompute Mesh Frequencies:')
	print(f'\t\tCFC MESH fw p0: {cfc_fw_p0}')
	print(f'\t\tCFC MESH fw p1: {cfc_fw_p1}')
	print(f'\t\tCFC MESH fw pn: {cfc_fw_pm}')
	print(f'\t\tCFC MESH cbb p0: {cfc_cbb_p0}')
	print(f'\t\tCFC MESH cbb p1: {cfc_cbb_p1}')
	print(f'\t\tCFC MESH cbb pn: {cfc_cbb_pm}')
	print(f'\t\tCFC MESH io p0: {cfc_io_p0}')
	print(f'\t\tCFC MESH io p1: {cfc_io_p1}')
	print(f'\t\tCFC MESH io pn: {cfc_io_pm}')
	print(f'\t\tCFC MESH mem p0: {cfc_mem_p0}')
	print(f'\t\tCFC MESH mem p1: {cfc_mem_p1}')
	print(f'\t\tCFC MESH mem pn: {cfc_mem_pm}')

	try:
		temp = sv.sockets.imhs.fuses.hwrs_top_late.ip_disable_fuses_dword6_core_disable.get_value()[0] 
	except:
		itp.forcereconfig()
		itp.unlock()
		sv.refresh()
	
	##PM enable no vf not enabled yet, do not use... WIP
	#if (pm_enable_no_vf == True): 
	#	_fuse_files_compute=[f'{fuses_dir}\\pm_enable_no_vf_computes.cfg'] ## Fix the file for CWF
	#	_fuse_files_io = [f'{fuses_dir}\\pm_enable_no_vf_ios.cfg'] ## Fix the file for CWF


	#if (stop_after_mrc): b_extra+=', gotil=\"phase6_cpu_reset_break\"'
	
	#masks = dpm.fuses(rdFuses = False, sktnum =[0])

	# if (ht_dis): 
	# 	_fuse_str+= htdis_comp
	# 	_fuse_str+= htdis_io
	
	#if (vp2intersect_en): 
	#	_fuse_str += vp2i_en_comp

	## Defining new values for IA Frequencies
	# IA P0 frequencies flat
	if ia_fw_p1: _fuse_str += assign_values_to_regs(bootFuses['IA']['fwFreq']['p1'], ia_fw_p1)
	if ia_fw_pn: _fuse_str += assign_values_to_regs(bootFuses['IA']['fwFreq']['pn'], ia_fw_pn)
	if ia_fw_pm: _fuse_str += assign_values_to_regs(bootFuses['IA']['fwFreq']['min'], ia_fw_pm)
	if ia_fw_pboot: _fuse_str += assign_values_to_regs(bootFuses['IA']['fwFreq']['boot'], ia_fw_pboot)
	if ia_fw_pturbo: _fuse_str += assign_values_to_regs(bootFuses['IA']['fwFreq']['turbo'], ia_fw_pturbo)
	if ia_vf_curves: _fuse_str += assign_values_to_regs(bootFuses['IA']['fwFreq']['vf_curves'], ia_vf_curves)
		
	if ia_imh_p1: _fuse_str += assign_values_to_regs(bootFuses['IA']['imhFreq']['p1'], ia_imh_p1)
	if ia_imh_pn: _fuse_str += assign_values_to_regs(bootFuses['IA']['imhFreq']['pn'], ia_imh_pn)
	if ia_imh_pm: _fuse_str += assign_values_to_regs(bootFuses['IA']['imhFreq']['min'], ia_imh_pm)

	if cfc_fw_p0: _fuse_str += assign_values_to_regs(bootFuses['CFC']['fwFreq']['p0'], cfc_fw_p0)
	if cfc_fw_p1: _fuse_str += assign_values_to_regs(bootFuses['CFC']['fwFreq']['p1'], cfc_fw_p1)
	if cfc_fw_pm: _fuse_str += assign_values_to_regs(bootFuses['CFC']['fwFreq']['min'], cfc_fw_pm)

	if cfc_cbb_p0: _fuse_str += assign_values_to_regs(bootFuses['CFC']['cbbFreq']['p0'], cfc_cbb_p0)
	if cfc_cbb_p1: _fuse_str += assign_values_to_regs(bootFuses['CFC']['cbbFreq']['p1'], cfc_cbb_p1)
	if cfc_cbb_pm: _fuse_str += assign_values_to_regs(bootFuses['CFC']['cbbFreq']['min'], cfc_cbb_pm)

	if cfc_io_p0: _fuse_str += assign_values_to_regs(bootFuses['CFC']['ioFreq']['p0'], cfc_io_p0)
	if cfc_io_p1: _fuse_str += assign_values_to_regs(bootFuses['CFC']['ioFreq']['p1'], cfc_io_p1)
	if cfc_io_pm: _fuse_str += assign_values_to_regs(bootFuses['CFC']['ioFreq']['min'], cfc_io_pm)

	if cfc_mem_p0: _fuse_str += assign_values_to_regs(bootFuses['CFC']['memFreq']['p0'], cfc_mem_p0)
	if cfc_mem_p1: _fuse_str += assign_values_to_regs(bootFuses['CFC']['memFreq']['p1'], cfc_mem_p1)
	if cfc_mem_pm: _fuse_str += assign_values_to_regs(bootFuses['CFC']['memFreq']['min'], cfc_mem_pm)

	if (avx_mode != None):
		if (avx_mode) in range (0,8):
			int_mode = avx_mode
		elif avx_mode == "128":
			int_mode = 1        
		elif avx_mode == "256":
			int_mode = 3
		elif avx_mode == "512":
			int_mode=5
		elif avx_mode == "TMUL":
			int_mode=7
		else:
			raise ValueError("Invalid AVX Mode")
		ia_min_lic = bootFuses['IA_license']['cbb']['min']
		ia_max_lic = bootFuses['IA_license']['cbb']['max']
		_fuse_str += [f'{ia_min_lic}=0x%x' % int_mode]
		_fuse_str += [f'{ia_max_lic}=0x%x' % int_mode]
	
	_modulemask ={}
	_llcmask = {}
	
	for key, value in masks.items():
		newkey = f'cbb{key[-1]}'
		if key.startswith('ia_'):
			_modulemask[newkey] = value
		if key.startswith('llc_'):
			_llcmask[newkey] = value

	if (modulemask == None): 
		modulemask = _modulemask
	_fuse_str+= mask_fuse_module_array(modulemask)

	if (llcmask != None):
		_fuse_str+= mask_fuse_llc_array(llcmask)

	print("*"*20)
	print('Using FastBoot with itp.resettarget() and ram flush')
	
	if global_dry_run == False:
		if (stop_after_mrc):
			print(f'Setting biosscratchpad6_cfg for desired PostCode = {AFTER_MRC_POST}')
			sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6]=AFTER_MRC_POST
			# sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=AFTER_MRC_POST

		
		print(Fore.YELLOW + "***********************************v********************************************")
		print(Fore.YELLOW + "******************** Starting Unit Fast Boot Fuse Override *********************")
		print(Fore.YELLOW + "***********************************v********************************************")			

		fuse_cmd_override_reset(_fuse_str)

		if (stop_after_mrc):

			_wait_for_post(AFTER_MRC_POST)
		else:
			_wait_for_post(EFI_POST, sleeptime=120)
		#sv_refreshed = False


def mask_fuse_module_array(ia_masks = {'cbb0':0x0, 'cbb1':0x0, 'cbb2':0x0, 'cbb3':0x0}):
	'''
	Builds the necessary arrays for Module disable Masks used in FastBoot option.

	Input:
		ia_masks: (Mask Dictionary, Default={'compute0':0x0, 'compute1':0x0, 'compute2':0x0}): mask of all Modules to be disabled

	Output:
		ret_array: (Register Array) Module Masks disable registers.
	'''
	ret_array=[] # Return array
	
	sv = _get_global_sv()
	cbbs = sv.socket0.cbbs.name

	for cbb_name in cbbs: # For each compute name
		module_mask = ia_masks[cbb_name] # Current mask
		module_mask_hex = hex(module_mask)
		# reg0=f"sv.socket0.{imh_name}.fuses.hwrs_top_late.ip_disable_fuses_dword6_core_disable"
		reg_pp0=f"sv.socket0.{cbb_name}.base.fuses.punit_fuses.fw_fuses_sst_pp_0_module_disable_mask"
		reg_pp1=f"sv.socket0.{cbb_name}.base.fuses.punit_fuses.fw_fuses_sst_pp_1_module_disable_mask"
		reg_pp2=f"sv.socket0.{cbb_name}.base.fuses.punit_fuses.fw_fuses_sst_pp_2_module_disable_mask"
		reg_pp3=f"sv.socket0.{cbb_name}.base.fuses.punit_fuses.fw_fuses_sst_pp_3_module_disable_mask"
		reg_pp4=f"sv.socket0.{cbb_name}.base.fuses.punit_fuses.fw_fuses_sst_pp_4_module_disable_mask"
		# reg_dts=f"sv.socket0.{cbb_name}.fuses.pcu.pcode_disabled_module_dts_mask"
		
		# Module disable registers
		# ret_array.append(f"{reg0}={module_mask_hex}")
		ret_array.append(f"{reg_pp0}={module_mask_hex}")
		ret_array.append(f"{reg_pp1}={module_mask_hex}")
		ret_array.append(f"{reg_pp2}={module_mask_hex}")
		ret_array.append(f"{reg_pp3}={module_mask_hex}")
		ret_array.append(f"{reg_pp4}={module_mask_hex}")
		# ret_array.append(f"{reg_dts}={module_mask_hex}")
			
		module_count = DMR_TOTAL_MODULES_PER_CBB - _bitsoncount(module_mask) # enabled modules
		print(Fore.CYAN + f'{cbb_name.upper()} enabled Cores = {module_count}')

		# if module_count >= 32:
		# 	lowval = 0xffffffff
		# 	highval = _enable_bits(module_count-32)
		# else:
		# 	lowval = _enable_bits(module_count)
		# 	highval = 0x0
			
		
		# ret_array.append(f"sv.socket0.{cbb_name}.fuses.pcu.capid_capid8_llc_ia_core_en_low={lowval:#x}")
		# ret_array.append(f"sv.socket0.{cbb_name}.fuses.pcu.capid_capid9_llc_ia_core_en_high={highval:#x}")
		
	return(ret_array)
	

def mask_fuse_llc_array(llc_masks = {'cbb0':0x0, 'cbb1':0x0, 'cbb2':0x0, 'cbb3':0x0}):
	'''
	Builds the necessary arrays for LLC disable Masks used in FastBoot option.

	Input:
		llc_masks: (Mask Dictionary, Default={'compute0':0x0, 'compute1':0x0, 'compute2':0x0}): mask of all LLCs to be disabled

	Output:
		ret_array: (Register Array) LLC Masks disable registers.
	'''
	ret_array=[] # Retrun array
	sv = _get_global_sv()
	cbbs = sv.socket0.cbbs.name

	for cbb_name in cbbs: # For each compute name
		LLC_mask = llc_masks[cbb_name] # Current LLC Mask
		LLC_mask_hex = hex(LLC_mask)
		# reg0=f"sv.socket0.{compute}.fuses.hwrs_top_late.ip_disable_fuses_dword2_llc_disable" 
		# reg1=f"sv.socket0.{compute}.fuses.hwrs_top_ram.ip_disable_fuses_dword1_cha_disable"
		# reg2=f"sv.socket0.{cbb_name}.fuses.pcu.pcode_llc_slice_disable"
		reg0 = f"sv.socket0.{cbb_name}.base.fuses.punit_fuses.fw_fuses_llc_slice_ia_ccp_dis"

		# Add LLC Mask as register values
		ret_array.append(f"{reg0}={LLC_mask_hex}")
		# ret_array.append(f"{reg1}={LLC_mask_hex}")
		# ret_array.append(f"{reg2}={LLC_mask_hex}")	

		module_count = DMR_TOTAL_MODULES_PER_CBB - _bitsoncount(LLC_mask) # Enabled Modules
		print(Fore.CYAN + f'{cbb_name.upper()} enabled LLC slices = {module_count}')
			
		# if module_count >= 32:
		# 	lowval = 0xffffffff
		# 	highval = _enable_bits(module_count-32)
		# else:
		# 	lowval = _enable_bits(module_count)
		# 	highval = 0x0
			
		# ret_array.append(f"sv.socket0.{compute}.fuses.pcu.capid_capid6_llc_slice_en_low={lowval:#x}")
		# ret_array.append(f"sv.socket0.{compute}.fuses.pcu.capid_capid7_llc_slice_en_high={highval:#x}")
		
	return(ret_array)


def fuse_cmd_override_reset(fuse_cmd_array, skip_init=False, boot = True):
	'''
	Overrides each fuse given as input array with its specified values.
	Full fuse names and values are required.
	This stops and later resets the unit.

	Input:
		fuse_cmd_array: (String Array) Input fuses to be overwritten.
		skip_init: (Boolean, Default=False) Skip loading fuses and go_offline functions for computes and ios.
		boot: (Boolean, Default=True) Reboot after execution.
	'''
	sv = _get_global_sv() # Get sv
	ipc = ipccli.baseaccess()

	try: ipc.halt() # Try to halt threads
	except: print('Not able to halt threads... skipping...')
	
	if skip_init==False:
		ipc.forcereconfig()
		ipc.unlock()
		sv.refresh()

		sv.sockets.imhs.fuses.load_fuse_ram() # Load IOs fuses
		sv.sockets.cbbs.base.fuses.load_fuse_ram() # Load computes fuses
		sv.sockets.imhs.fuses.go_offline() # Computes go offline
		sv.sockets.cbbs.base.fuses.go_offline() # IOs go offline

	for f in (fuse_cmd_array): # For each input fuse
		base = f.split('=')[0] # Fuse name
		newval = f.split('=')[1] # Fuse new value
		val=eval(base + ".get_value()") # Fuse current value
		if isinstance(val,int):
			print(Fore.LIGHTCYAN_EX + f"Changing --- {base} from {val:#x} --> {newval}")		
		else:
			print(Fore.LIGHTCYAN_EX + f"Changing --- {base} from {val} --> {newval}")
		exec(f) # Override fuse

	sv.sockets.imhs.fuses.flush_fuse_ram() # Load IOs fuses
	sv.sockets.cbbs.base.fuses.flush_fuse_ram() # Load computes fuses
	sv.sockets.imhs.fuses.go_online() # Computes go online
	sv.sockets.cbbs.base.fuses.go_online() # IOs go online

	try: ipc.go() # Restart threads
	except: print('Not able to restart threads... skipping...')
	if boot: # Reboot
		print(Fore.YELLOW + 'Rebooting unit with ipc.resettarget()')
		ipc.resettarget()

def CheckModule(global_physical_module):
	'''
	Checks if input Module is enabled in the system 
	
	Inputs:
		global_physical_module: (Int) Module to check.
	
	Output:
		module_status: (Boolean) True if enabled, False if disabled.
	'''
	target_cbb = int(global_physical_module / DMR_TOTAL_MODULES_PER_CBB) # Target compute
	# masks = dpm.fuses(system = sv.socket0.target_info["device_name"], rdFuses = True, sktnum =[0]) # Get LLC and Module masks
	masks = dpm.fuses(rdFuses = True, sktnum =[0])
	compute_mask = int(masks[f'ia_cbb{target_cbb}']) # Target mask
	local_physical = global_physical_module - DMR_TOTAL_MODULES_PER_CBB*target_cbb # Local module
	module_status = not (_bit_check(compute_mask, local_physical)) # Check if mask contains local module
	return module_status


def CheckMasks(readfuse = True):
	'''
	Returns unit Module and LLC masks, and a dictionary containing all the global physcial enabled Modules and LLCs

	Input:
		readfuse: (Boolean, Default=True) read fuses to get masks.

	Outputs:
		masks: (Dictionary) contains all Modules and LLC masks for every compute.
		array: (Dictionary) contains all enabled Modules and LLCs for every mask.
	'''
	sv = _get_global_sv() # init SV
	
	masks = dpm.fuses(rdFuses = readfuse, sktnum =[0]) # Get LLC and Module masks
	array = {'MODULES':{},
				'LLC':{}} # Dictionary to save both masks
	
	for cbb in sv.socket0.cbbs: # For each Compute
		cbb_name = cbb.name
		cbbN = int(cbb.target_info.instance)
		_modules = masks[f'ia_{cbb_name}'].value # module mask
		_slices = masks[f'llc_{cbb_name}'].value # LLC mask
		
		modules = _enabled_bit_array(_modules) # get physical indexes of enabled modules
		module_array = [x + ((cbbN)*DMR_TOTAL_MODULES_PER_CBB) for x in modules] # Put previous indexes as global physical indexes in an array

		llcs = _enabled_bit_array(_slices) # get physical indexes of enabled LLCs
		llc_array = [x + ((cbbN)*DMR_TOTAL_MODULES_PER_CBB) for x in llcs] # Put previous indexes as global physical indexes in an array

		array['MODULES'][cbb_name] = module_array # Add module indexes array into the return dictionary
		array['LLC'][cbb_name] = llc_array # Add LLC indexes array into the return dictionary
		
	return masks, array


def modulesEnabled(moduleslicemask=None, logical=False, skip = False, print_modules = True, print_llcs = True):
	'''
	Prints a  mini-tileview table of enabled modules
	
	Input:
		moduleslicemask: (Dictionary, Default=None) module mask override.
		logical: (Boolean, Default=False) if moduleslicemask should be treated as logical or physical.
		skip: (Boolean, Default=False) Skip tileview print. Module and LLC masks are still printed.
		print_modules: (Boolean, Default=True) display modules in tileview
		print_llcs: (Boolean, Default=True) display LLCs in tileview 
	'''
	sv = _get_global_sv() # init sv
	die = sv.socket0.target_info["device_name"] # Get die name
	
	max_modules_cbb = DMR_TOTAL_MODULES_PER_CBB # Modules per compute
	
	masks = dpm.fuses(rdFuses = True, sktnum =[0]) # Get Module and LLC masks

	for socket in sv.sockets: # For each socket
		
		
		# Get all available Modules and LLCs
		if moduleslicemask==None: # If no given masks from user
			moduleslicemask = {}
			for cbb_name in socket.cbbs.name: # for each compute
				# compute = cbb_name # Compute name
				# computeN = _compute.target_info.instance # Compute Id
				_modules = masks[f'ia_{cbb_name}'] # Extract module mask
				_slices = masks[f'llc_{cbb_name}'] # Extract LLC mask
				moduleslicemask[f'ia_{cbb_name}'] = _modules # Add Module mask to moduleslicemask
				moduleslicemask[f'llc_{cbb_name}'] = _slices # Add LLC mask to moduleslicemask

				if (_modules!=_slices): # LLC and Module masks are different
					#Print info
					print  ("\tmodule disables mask: 0x%x" % (_modules)) 
					print  ("%d modules enabled" % ( _bitsoffcount(_modules, max_modules_cbb)))
					print  ("\tslice disables mask: 0x%x" % (_slices)) 
					print  ("%d slices enabled" % ( _bitsoffcount(_slices, max_modules_cbb)))

	log_module_dis_mask = {} # Logical module Mask
	phy_module_dis_mask = {} # Physical module Mask
	log_llc_dis_mask = {} # Logical LLC Mask
	phy_llc_dis_mask = {} # Physical LLC Mask
	ios_tile = sv.socket0.imhs.name # IO Name
	cbbs_tile = sv.socket0.cbbs # Compute names	

	if skip: # Skip tileview
		print('Tileview option skipped .... ')
	else:   #Build Tileview
		print  ("Building Tileview for : %s" % (socket.name)) 
		for cbb in cbbs_tile: # For each compute name
			cbb_name = cbb.name
			# cbb_name = cbb.name
			# cbbN = int(cbb.target_info.instance) # Compute id 
			if logical == False: # Get Module and LLC info through physical into logical conversions
				log_module_dis_mask[cbb_name] = _module_mask_phy_to_log(moduleslicemask[f'ia_{cbb_name}'])
				phy_module_dis_mask[cbb_name] = moduleslicemask[f'ia_{cbb_name}']
				log_llc_dis_mask[cbb_name] = _module_mask_phy_to_log(moduleslicemask[f'llc_{cbb_name}'])
				phy_llc_dis_mask[cbb_name] = moduleslicemask[f'llc_{cbb_name}']
			else: # Get Module and LLC info through logical into physical conversions
				phy_module_dis_mask[cbb_name] = _module_mask_log_to_phy(moduleslicemask[f'ia_{cbb_name}'])
				log_module_dis_mask[cbb_name] = moduleslicemask[f'ia_{cbb_name}']
				phy_llc_dis_mask[cbb_name] = _module_mask_log_to_phy(moduleslicemask[f'llc_{cbb_name}'])
				log_llc_dis_mask[cbb_name] = moduleslicemask[f'llc_{cbb_name}']

		headers = [] # Table headers
		headers.append("R/C") # Row Column header			
		for c in range (0,10): headers.append(f'COL{c}') # Column headers
	
		MDFlabel = '---- MDF ----' # MDF
		cellwith = len(MDFlabel) # size of MDF string to keep everything in line
		tile_io0 =[] # io0 tile
		tile_io1 =[] # io1 tile
		MDF_string  = [] # MDF string

		tile_cbss = {} # compute names
		for cbb_name in sv.socket0.cbbs.name: # For each compute name
			tile_cbss[cbb_name] = [] # Assign empty array to each compute name
		
		# Leaving this one here for now, not used for the moment

		cols = {'C0':[0,4,8,12,16,20,24,28],
				'C1':[1,5,9,13,17,21,25,29],
				'C2':[2,6,10,14,18,22,26,30],
				'C3':[3,7,11,15,19,23,27,31]
				# 'C7':[MDFlabel,44,45,46,47,48,49,50,MDFlabel],
				# 'C8':[MDFlabel,51,52,53,54,55,56,57,MDFlabel],
				# 'C9':[MDFlabel,58,59,'','','MC6','MC7','SPK1',MDFlabel],
				} # CBB columns
		
		cols_num = len(cols.keys()) # Number of columns

		# for col in range(0,cols_num): # For each column
		# 	MDF_string.append(MDFlabel) # Add MDF label

		rows = {'R0':['ROW0','0:','1:','2:','3:'],
				'R1':['ROW1','4:','5:','6:','7:'],
				'R2':['ROW2','8:','9:','10:','11:'],
				'R3':['ROW3','12:','13','14','15:'],
				'R4':['ROW4','16','17','18','19'],
				'R5':['ROW5','20','21','22','23'],
				'R6':['ROW6','24','25','26','27'],
				'R7':['ROW8','28','29','30','31']
				}	# Compute rows

		rows_num = len(rows.keys()) # number of rows


		# Corregir todo esto hacia abajo, es muy estático, si cambia la cantidad de computes, hay que cambiar todo



		# if (die =="DMR_CLTAP"):
		for cbb in cbbs_tile:
			cbb_name = cbb.name
			modulesmask = moduleslicemask[f'ia_{cbb_name}']# & 0x7fff
			# t1 = moduleslicemask[f'ia_{cbb_name}']# & 0x7fff
			# if (die =="gnrap"): t2 = moduleslicemask[f'ia_compute_{2}']# & 0x7fff
			#t1 = (moduleslicemask >> 15) & 0x7fff
			#t2 = (moduleslicemask >> 30) & 0x7fff
			#t3 = (moduleslicemask >> 45) & 0x7fff
			modules_per_cbb = DMR_TOTAL_MODULES_PER_CBB - _bitsoncount(modulesmask)
			# modules_en_c1 = DMR_TOTAL_MODULES_PER_CBB - _bitsoncount(t1)
			# if (die =="gnrap"): modules_en_c2 = DMR_TOTAL_MODULES_PER_CBB - _bitsoncount(t2)

			print  (f"{cbb_name}: %d modules enabled: 0x%x" % (modules_per_cbb, modulesmask))
			# print  ("COMPUTE1: %d modules enabled: 0x%x" % (modules_en_c1, t1))
			# if (die =="gnrap"): print  ("COMPUTE2: %d modules enabled: 0x%x" % (modules_en_c2, t2))#print  ("t2: %d modules enabled: 0x%x" % ( 15 - _bitsoncount(t2), t2))
			#print  ("t3: %d modules enabled: 0x%x" % ( 15 - _bitsoncount(t3), t3))
			
			# print  ("%d modules enabled" % (modules_en_c0 + modules_en_c1+ modules_en_c2))
			# if (die =="gnrap"): 
			print  (f"Input module disables mask ->    {cbb_name}: 0x%x" % moduleslicemask[f'ia_{cbb_name}']) 
			print  (f"Logical module disables mask ->    {cbb_name}: 0x%x" % log_module_dis_mask[f'{cbb_name}']) 
			print  (f"Physical module disables mask ->    {cbb_name}: 0x%x" % phy_module_dis_mask[f'{cbb_name}']) 
				# print  (f"Logical module disables mask:  {cbb_name}: 0x%x - Compute1: 0x%x - Compute2: 0x%x" % (log_module_dis_mask['compute0'], log_module_dis_mask['compute1'], log_module_dis_mask['compute2'])) 
				# print  (f"Physical module disables mask: {cbb_name}: 0x%x - Compute1: 0x%x - Compute2: 0x%x" % (phy_module_dis_mask['compute0'], phy_module_dis_mask['compute1'], phy_module_dis_mask['compute2'])) 
			# else:
				# print  ("Input module disables mask:    Compute0: 0x%x - Compute1: 0x%x" % (moduleslicemask[f'ia_compute_{0}'],moduleslicemask[f'ia_compute_{1}'])) 
				# print  ("Logical module disables mask:  Compute0: 0x%x - Compute1: 0x%x" % (log_module_dis_mask['compute0'], log_module_dis_mask['compute1'])) 
				# print  ("Physical module disables mask: Compute0: 0x%x - Compute1: 0x%x" % (phy_module_dis_mask['compute0'], phy_module_dis_mask['compute1'])) 
			print("\n\nCore Tileview Map ---> physical:logical")


			# if 'io0' in ios_tile:
			# 	rows_io0 = {'R0':['ROW0','UPI0','','','PE2','','PE1','','UBOX','','UPI1'],
			# 			'R1':['ROW1','','HC0','','','PE0','','PE3','','HC1',''],
			# 			'R2':['ROW2'] + MDF_string}

			# 	print('\nDIE: IO0\n')
			# 	for key in rows_io0.keys():
			# 		row_string = []
			# 		for row in rows_io0[key]:
			# 			if 'MDF' in row:
			# 				color = Fore.YELLOW
			# 				width = cellwith
			# 			else: 
			# 				color = Fore.LIGHTWHITE_EX
			# 				width = 4
						
			# 			row_string.append(color + f"{row.center(width)}"+ Fore.WHITE)
			# 		tile_io0.append(row_string)
			# 	table = tabulate(tile_io0, headers=headers, tablefmt="grid")
			# 	print(table)

			# for cbb in sv.socket0.cbbs:
				# cbb_name = cbb.name
			print (f'\nDIE: {cbb_name.upper()}\n')
			cbbN = int(cbb.target_info.instance)
			for row in range(0,rows_num):
				row_string = [F'ROW{row}']
					
				for col in range(0,cols_num):
					data = cols[f'C{col}'][row]
					if type(data) == str:
						if 'MDF' in data: color = Fore.YELLOW
						else: color = Fore.LIGHTWHITE_EX
						row_string.append(color + data + Fore.WHITE)
					else:
						if print_modules: 
							module_data = _module_string(data, phy_module_dis_mask[cbb_name], cbbN)
							tabledata = f'MOD{module_data}'
						if print_llcs: 
							llc_data = _module_string(data, phy_llc_dis_mask[cbb_name], cbbN)
							tabledata = f'LLC{llc_data}'
						if print_modules and print_llcs:
							tabledata = f'MOD {module_data}\nLLC {llc_data}'
						row_string.append(tabledata)
				tile_cbss[cbb_name].append(row_string)
			table = tabulate(tile_cbss[cbb_name], headers=headers, tablefmt="grid")
			print(table)

			# if 'io1' in ios_tile:
			# 	rows_io1 = {'R0':['ROW0']+ MDF_string,
			# 			'R1':['ROW1','','HC2','','','PE5','UPI4','','','HC3',''],
			# 			'R2':['ROW2','UPI3','','','','UPI5','PE4','','','','UPI2']}

			# 	print('\nDIE: IO1\n')
			# 	#print(header)
			# 	for key in rows_io1.keys():
			# 		row_string = []
			# 		for row in rows_io1[key]:
			# 			if 'MDF' in row:
			# 				color = Fore.YELLOW
			# 			else: color = Fore.LIGHTWHITE_EX
						
			# 			row_string.append(color + f"{row}"+ Fore.WHITE)
			# 		tile_io1.append(row_string)
			# 	table = tabulate(tile_io1, headers=headers, tablefmt="grid")
			# 	print(table)


def read_biospost(): 
	'''
	reads register
		sv.socket0.imh0.ubox.ncdecs.biosnonstickyscratchpad_mem[7]
	'''
	# print ("POST = 0x%x" % sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg) # Read current postcode
	print ("POST = %x" % sv.socket0.imh0.ubox.ncdecs.biosnonstickyscratchpad_mem[7])

def clear_biosbreak(): 
	'''
	Sets register
		sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg = 0
	'''
	# sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=0 # Set register to 0
	sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6]=0

def go_to_efi(): 
	'''
	Execute clear_biosbreak(), then waits for the unit to read EFI postcode (0x57000000).
	Maximum wait time: 10 minutes
	'''
	clear_biosbreak() # Set register to 0
	_wait_for_post(EFI_POST, sleeptime=60) # wait for EFI postcode

def _wait_for_post(postcode, sleeptime = 3, timeout = 10):
	'''
	Waits for the unit to reach a desired postcode.
	If timeout is exceeded, print a message stating the postcode was not reached.

	Inputs:
		postcode: (Hex) desired postcode to reach.
		sleeptime: (Int, Default=3) seconds to wait for each sleep cycle.
		timeout: (Int, Default=10) timeout counter reduced by 1 at the end of every sleep cycle. If timeout is exceeded, print a message stating the postcode was not reached.
	'''
	# current_post = sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg # Current postcode
	current_post = sv.socket0.imh0.ubox.ncdecs.biosnonstickyscratchpad_mem[7]
	print (Fore.YELLOW + "WAITING FOR postcode 0x%x. Sleeptime %d" % (postcode,sleeptime))
	while(current_post < postcode): # While target post has not been reached
		time.sleep(sleeptime) # Sleep for N seconds
		prev_post = current_post
		current_post = sv.socket0.imh0.ubox.ncdecs.biosnonstickyscratchpad_mem[7] # New current postcode
		if (prev_post == current_post): # Same postcode as N seconds earlier
			print ("itp.go")
			try:
				
				itp.go() # Sometimes breakpoints are occurring with boot script that need a kick
			except:
				pass
		timeout-=1 # Reduce timeout
		print(f"Timeout: {timeout}")
		if (timeout ==0):
			print(f"!!!! COULD NOT REACH POSTCODE {postcode} !!!!")
			return
	print ("Successfully reached postcode 0x%x" % postcode)
   
def _logical_to_physical(logModule, cbb_instance=None):
	'''
	Given a logical module (local or global), return the corresponding global physical module.
	
	Input:
		logModule: (Int) logical module, this can be local or global value.
		compute_instance: (Int, Default=None) if given, return corresponding global physical module for that compute.
	
	Outputs:
		physicalModule: (Int) corresponding global physical value.
	'''

	if cbb_instance == None: cbb_instance = int(logModule/DMR_TOTAL_ACTIVE_MODULES_PER_CBB) # If no compute was given, calculate it from given global logical module

	local_logical = logModule % DMR_TOTAL_ACTIVE_MODULES_PER_CBB # If a global logical was given, reduce it to local logical
	local_offset = cbb_instance*DMR_TOTAL_MODULES_PER_CBB # Add physical offset based on desired (or calculated) compute. If compute=0, offset=0

	physicalModule = classLogical2Physical[local_logical] + local_offset # Extract local physical from dictionary, then add offset if compute>0
	return physicalModule
	
def _physical_to_logical(physModule, cbb_instance=None):
	'''
	Given a physical module (local or global), return the corresponding global logical module.
	Returns None if phys_module is not present in CWF.
	
	Input:
		physModule: (Int) physical module, this can be local or global value.
		compute_instance: (Int, Default=None) if given, return corresponding global logical module for that compute.
	
	Outputs:
		logicalModule: (Int) corresponding global logical value, returns None if phys_module is not present in CWF.
	'''
	if cbb_instance == None: cbb_instance = int(physModule/DMR_TOTAL_MODULES_PER_CBB) # If no compute was given, calculate it from given global physical module

	local_physical = physModule % DMR_TOTAL_MODULES_PER_CBB # If a global physical was given, reduce it to local physical
	local_offset = cbb_instance * DMR_TOTAL_ACTIVE_MODULES_PER_CBB # Add logical offset based on desired (or calculated) compute. If compute=0, offset=0

	if local_physical in physical2ClassLogical: # If physical value has an associated logical value
		logicalModule = physical2ClassLogical[local_physical] + local_offset # Extract local logical from dictionary, then add offset if compute>0
		return logicalModule
	else:
		print(f"Physical module {physModule} is not present in CWF")
		return None # Return error value
    
def _physical_to_col_row(phys_module):
	'''
	Given a physical module, return the corresponding row and column positions in the compute die, respectively.
	
	Input:
		phys_module: (Int) physical module.
	
	Outputs:
		row: (Int) row position in compute die.
		column: (Int) column position in compute die.
	'''
	phys_module = phys_module%DMR_TOTAL_MODULES_PER_CBB # Local module if global value was given
	if phys_module in phys2colrow: # If physical module is present in 'coretile' (moduletile?)
		row = phys2colrow[phys_module][1] # Get row value from dictionary
		column = phys2colrow[phys_module][0] # Get column value from dictionary
		return row, column
	else: print(f"Physical module {phys_module} is not present in DMR")
	return None, None

def _module_mask_phy_to_log(phy_module_mask, verbose=False):
	'''
	Given a physical mask (60 bits), return corresponding logical mask (24 bits).

	Input:
		phys_module_mask: (Hex or Int) physical module mask.
		verbose: (Boolean, Default=True) More information on script execution.
	
	Output:
		log_module_mask: logical module mask.
	'''
	log_module_mask = 0 # Disabled logical module mask

	for physical_mod in range(0,DMR_TOTAL_MODULES_PER_CBB): # for each possible physical module position
		if ((phy_module_mask >> physical_mod) & 1 == 1) and physical_mod not in skip_physical_modules: # If current module is disabled, and this module is not part of the skip list
			logical_mod = _physical_to_logical(physical_mod) # Get respective logical module
			log_module_mask |= 1 <<  logical_mod # Add logical module to the disabled logical mask
			if verbose: print(f"Physical: {physical_mod} -> Logical: {logical_mod}") # Print more info
	
	return(log_module_mask) # Return disabled logical module mask

def _module_mask_log_to_phy(log_module_mask, verbose=False):
	'''
	Given a logical mask (24 bits), return corresponding physical mask (60 bits).

	Input:
		log_module_mask: (Hex or Int) logical module mask.
		verbose: (Boolean, Default=True) More information on script execution.
	
	Output:
		phys_module_mask: physical module mask.
	'''
	phy_module_mask = 0 # Disabled physical module mask
	
	for logical_mod in range(0,DMR_TOTAL_ACTIVE_MODULES_PER_CBB): # For each possible logical module position
		if ((log_module_mask >> logical_mod) & 1 == 1): # If current module is disabled in input mask (is 1)
			physical_mod = _logical_to_physical(logical_mod) # Get respective physical module
			phy_module_mask |= 1 <<  physical_mod # Add physical module to the disabled physical mask
			if verbose: print(f"Logical: {logical_mod} -> Physical: {physical_mod}") # Print more info
	
	return(phy_module_mask) # Return disabled physical module mask

def _module_string(phys_module, moduleslicemask, cbbinst):
	'''
	Returns a string containing module information, this includes Physical, Logical (if aplicable) and a Python color that represents enabled/disabled (GREEN/RED) state.
	This function is called by modulesEnabled() to get the information for every module.

	Inputs:
		phys_module: (Int) physical module to check.
		moduleslicemask: (Hex or Int) compute mask to determine the current state of the module.
		cinst: (Int) compute instance.
	
	Outputs:
		ret_string: (String) contains module information such as Physical, Logical (if aplicable) and a Python color that represents enabled/disabled (GREEN/RED) state.
	'''
	ret_string = "" # Return string
	maxphysical = DMR_TOTAL_MODULES_PER_CBB # MAX physical modules per compute

	if phys_module in skip_physical_modules: # If physical module not enabled in CWF
		ret_string = Fore.LIGHTBLACK_EX + "%d:-" % (phys_module + (maxphysical*cbbinst)) + Fore.WHITE	# Only add physical module to return string
	
	else: # Else: module is enabled in CWF
		log_module = _physical_to_logical(phys_module, cbbinst) # Get respective logical module value
		if ((moduleslicemask & 1<<phys_module) != 0 ): color = Fore.RED # If module is not active (1), color it RED
		else: color = Fore.GREEN # Else, module is active (0), color it GREEN
		ret_string = color + "%d:%d" % (phys_module + (maxphysical*cbbinst), log_module ) + Fore.WHITE # Add both physical and logical values to return string

	return ret_string

def _module_apic_id(phys_module, verbose=False):
	'''
	Read and return all 4 core APIC IDs for selected physical module.

	Input:
		phys_module: (Int) physical module to read from. Can be either global or local value.
		verbose: (Boolean, Default=False) Additional prints for debug.
		
	Outputs:
		id0: (Int) value read from core0.thread0.ml3_cr_pic_extended_local_apic_id
		Id1: (Int) value read from core1.thread0.ml3_cr_pic_extended_local_apic_id

	'''
	sv = _get_global_sv()
	cbb_index = int(phys_module/DMR_TOTAL_MODULES_PER_CBB) # Compute id
	compute_index =  int((phys_module % DMR_TOTAL_MODULES_PER_CBB) / DMR_TOTAL_MODULES_PER_COMPUTE)
	# phys_module = phys_module%DMR_TOTAL_MODULES_PER_CBB # Local module if global value was given
	
	id0 = f"sv.socket0.cbb{cbb_index}.compute{compute_index}.module{phys_module}.core0.ml3_cr_pic_extended_local_apic_id"
	id1 = f"sv.socket0.cbb{cbb_index}.compute{compute_index}.module{phys_module}.core1.ml3_cr_pic_extended_local_apic_id"
	
	id0 = eval(id0) # Read id0
	id1 = eval(id1) # Read id1

	if verbose:
			print(f'CBB: {cbb_index}. Compute: {compute_index}. Module: {phys_module}')
			print(f'Core0 APIC ID: {id0}')
			print(f'Core1 APIC ID: {id1}')

	return id0, id1

def _bitsoncount(number):
	'''
	Given an input number, counts all its bits set to 1.

	Input:
		number: (Int) number to analyze.
		
	Output:
		ones: (Int) amount of bits set to 1 in number.
	'''
	return bin(number).count('1')

def _bitsoffcount(number, bit_size): 
	'''
	Given an input number, counts all its bits set to 0.

	Input:
		number: (Int) number to analyze.
		bit_size: (Int) bit size of the input number. 
		
	Output:
		zeros: (Int) amount of bits set to 0 in number.
	'''
	zeros = bin((number&(1<<bit_size)-1)|1<<bit_size).count('0')-1
	return zeros

def _bit_check(value, bit_n):
	'''
	Check if the input value contains a 1 in the selected bit_n position.

	Inputs:
		value: (Int) number to analyze.
		bit_n: (Int) bit position to check.
		
	Output:
		binStatus: (Boolean) returns true if the input value contains a 1 in the selected bit_n position.
	'''
	# Verify input value data type
	if isinstance(value, int): # Value is an int
		bin_string = (value) # Keep as int
	elif isinstance(value, str): # Value is a string
		bin_string = (int(value,16)) # Convert to int
	else:
		raise ValueError ("Invalid input used for binary checks")
	
	if bin_string & (1 << bit_n): # Check if the bit_n is set to 1
		binStatus = True
	else:
		binStatus = False
	return binStatus

def _enabled_bit_array(value, max_bit = DMR_TOTAL_MODULES_PER_CBB):
	'''
	Given an input number value, return an array with all bit indexes that are set to 0 (enabled).

	Inputs:
		value: (Int) initial number value.
		max_bit: (Int, Default=DMR_TOTAL_MODULES_PER_CBB) maximum bit index for value.
		
	Output:
		disabled_bits: (Int Array) contains every bit index that is set to 0.
	'''
	# Validate value data type
	if isinstance(value, int): # Value is an int
		bin_string = (value) # Assign value into bin_string as an Int
	elif isinstance(value, str): # Value is a string
		bin_string = (int(value,16)) # Cast value as a 16 bit Int and assign it to bin_string
	else:
		raise ValueError ("Invalid input used for binary array build")
	
	disabled_bits = [] # Initialize an empty list to store the positions of the disabled bits
	
	 
	for n in range(max_bit): # Check each bit in the total number
		if not bin_string & (1 << n): # If the nth bit is not set to 1
			disabled_bits.append(n) # Add n to the list
	return (disabled_bits)

def _set_bit(value, bit_x, verbose = False):
	'''
	Given an initial value input, set bit x to 1.
	
	Inputs: 
		value: (Int) initial value to modify.
		bit_x: (Int) bit index to be set to 1.
		verbose: (Boolean, Default=False) additional information.
	
	Output:
		value: (Int) modified value.
	'''
	if verbose: print ("_set_bit(0x%x, %d)" %(value, bit_x))
	return value | (1<<bit_x)

def _set_bits(value, bits_to_enable, max_bit=31, verbose=False):
	'''
	Modifies input value, enabling the amount of bits specified, starting from its max bit.

	Inputs:
		value: (Int) initial number to modify.
		bits_to_enable: (Int) total number of bits set to 1. This considers initial values.
		max_bit: (Int, Default=59) maximum bit index for value. Bit enabling starts with this index towards bit 0.
		verbose: (Boolean, Default=False) additional information.
		
	Output:
		value: modified value.
	'''
	if verbose: print ("_set_bits(0x%x, %d, %d)" %(value, bits_to_enable, max_bit))
	if (bits_to_enable > max_bit):
		print ("BAD VALUE. The number of bits to enable must be equal or lower than the maximum possible bit." )
		raise
	while (_bitsoncount(value) < bits_to_enable): # While the amount of 1 bits in value is lower than bits_to_enable
		if verbose: print ("max_bit %d" % max_bit )
		if (((value >> max_bit) & 1) == 0): # If max_bit is 0
			value = _set_bit(value,max_bit) # Set max_bit to 1
		max_bit -=1 # Reduce current max_bit and continue loop until desired bits_to_enable are reached
	return value

def _enable_bits(n_bits):
	'''
	Returns the equivalent number of setting the first n bits to 1.

	Input:
		n_bits: (Int) first n bits to turn into 1.

	Output:
		bitmask: (Int) result as decimal value.
	''' 
	bitmask = (1 << n_bits) - 1
	return bitmask

class System2Tester():

	def __init__(self, target, masks = None, modulemask=None, slicemask=None, boot = False, fastboot = False, ht_dis = False, readFuse = True, clusterCheck = True, resetGlobals = False):
		'''
		Creates an instance of the System2Tester class. An instance of this class is needed to execute its internal methods, these are setModule, setTile, setMesh, _doboot and _fastboot.

		Inputs:
			target: (Int) target module for other scripts usage.
			Masks: (Dictionary, Default=None) dictionary containing both llc and module masks for every compute. Example:
				masks={'ia_compute_0': 0x0, 'ia_compute_1': 0x0, 'ia_compute_2': 0x0, 'llc_compute_0': 0x0, 'llc_compute_1': 0x0, 'llc_compute_2': 0x0}
			modulemask: (Dictionary, Default=None) dictionary containing module masks for every compute. These are used for booting. Example:
				modulemask= {'compute0': 0x0, 'compute1': 0x0, 'compute2': 0x0}
			slicemask: (Dictionary, Default=None) dictionary containing llc masks for every compute. These are used for booting. Example:
				slicemask= {'compute0': 0x0, 'compute1': 0x0, 'compute2': 0x0}
			boot: (Boolean, Default=False) This flag indicates the unit to boot after every System2Tester class function.
			fastboot: (Boolean, Default=False) This flag indicates the unit to fastboot after every System2Tester class function.
			ht_dis: (Boolean, Default=False) indicates HT disable on boot. HT is supposed to be disabled in CWF.
			readFuse: (Boolean, Default=False) read fused mask values using.
			clusterCheck: (Boolean, Default=True) used for dpm.pseudo_bs call in setMesh.
			resetGlobals: (Boolean, Default=False) execute reset_globals function on executing any System2Tester class function.
			
		Output:
			System2Tester instance
		'''

		# Check for Status of PythonSV
		svStatus()

		sv = _get_global_sv()
		self.sv = sv #_get_global_sv()
		ipc = _get_global_ipc()
		#self.ipc = ipc #_get_global_ipc()
		self.target = target # Target Module
		self.masks = masks # Input Module and LLC masks for every compute.
		self.modulemask = modulemask # Module Masks
		self.slicemask = slicemask # LLC Masks
		self.boot = boot # Enable Boot
		self.Fastboot = fastboot # Enable Fastboot 
		# self.ht_dis = ht_dis # Enable Ht
		self.readFuse = readFuse # Flag for dpm.fuses to execute fuse load
		self.clusterCheck = clusterCheck # Flag for dmp.pseudo_bs
		#self.BootFuses = dpm.dev_dict('GNRFuseFileConfigs.json') # Fuses for booting
		self.resetGlobals = resetGlobals # Execute global_reset on script executions
		
		self.die = sv.socket0.target_info["segment"] # Product name ('CWFAP')
		self.computes = sv.socket0.computes.name # Array containing compute names (['compute0', 'compute1', ...])
		self.instances = sv.socket0.computes.instance # Array containing compute instance value in hex ([0x0, 0x1, ...])
		self.sktnum = [0] # Used for dpm.fuses
		## Option to bring preconfigured Mask
		if masks == None: self.masks = dpm.fuses(system = self.die, rdFuses = self.readFuse, sktnum =self.sktnum)
	

	def setModule(self):
		
		'''
		Sets up system to run with 1 enabled module on a desired compute, other computes remain enabled.

		Input:
			self: (System2Tester instance) class instance uses self.target as the targetPhysicalModule to remain enabled.
		'''

		
		## Variables Init
		die = self.die
		computes = self.computes
		sv = self.sv
		targetPhysicalModule = self.target # Global physical value
		boot = self.boot
		ht_dis = self.ht_dis
		resetGlobals = self.resetGlobals
		readFuse = self.readFuse
		masks = self.masks

		if (not die.startswith("CWF")):
			print (f"Sorry.  This method is not available for {die}.")
			return
		
		if resetGlobals: reset_globals()
		
		# Building arrays based on system structure
		_moduleMasks= {die: {comp: 0xfffffffffffffff for comp in computes}} # Module mask filled with 1 for every compute
		_llcMasks= {die: {comp: 0xfffffffffffffff for comp in computes}} # LLC mask filled with 1 for every compute

		## Read Mask enable for this part, no need for fuse ram need in Slice mode as we already read those at the beggining
		masks = dpm.fuses(rdFuses = readFuse, sktnum =[0])
		target_compute = int(targetPhysicalModule/DMR_TOTAL_MODULES_PER_CBB) # Target compute

		modulemask = ~(1 << (targetPhysicalModule - (DMR_TOTAL_MODULES_PER_CBB * target_compute))) & ((1 << DMR_TOTAL_MODULES_PER_CBB) - 1) # Mask filled with 1 except the desired target physical module

		for compute in _moduleMasks[die].keys(): # For each compute
			computeN = sv.socket0.get_by_path(compute).target_info.instance # Compute Id 

			if int(computeN) == target_compute: # If current compute is target compute
				_moduleMasks[die][compute] = modulemask | masks[f'ia_compute_{computeN}']
				_llcMasks[die][compute] = masks[f'llc_compute_{computeN}']
			else:
				combineMask = masks[f'llc_compute_{computeN}'] | masks[f'ia_compute_{computeN}'] # combine both LLC and Module masks
				## We will check for the first enabled slice and enable it				
				binMask = bin(combineMask) # 
				first_zero = binMask[::-1].find('0') # Find first enabled module
				disMask = ~(1 << (first_zero)) & ((1 << DMR_TOTAL_MODULES_PER_CBB)-1) # Build a new mask filled with 1, except for the first enabled module found in first_zero

				_moduleMasks[die][compute] = disMask | masks[f'ia_compute_{computeN}'] # Combine previous module mask with new mask (overwrites everything except target module)
				_llcMasks[die][compute] = masks[f'llc_compute_{computeN}'] # LLC Mask is the one read in fuses
	
			# Print masks
			print  (f"{compute}: module disables mask:  0x{_moduleMasks[die][compute]}") 
			print  (f"{compute}: slice disables mask: 0x{_llcMasks[die][compute]}") 
		
		# Set as new mask for the Class
		self.modulemask = _moduleMasks[die]
		self.slicemask = _llcMasks[die]
		for i in range(len(sv.socket0.computes)):
			self.masks[f'llc_compute_{i}'] = self.modulemask[f'compute{i}']
			self.masks[f'ia_compute_{i}'] = self.slicemask[f'compute{i}']
	
		if boot:
			if self.Fastboot:
				self._fastboot()
			else:
				self._doboot(ht_dis)

	def setTile(self, stop_after_mrc=False, pm_enable_no_vf=False):
		'''
		Sets up system to run with target computes enabled. If a compute is to be disabled, the first available module remains enabled for the compute.

		Inputs:
			self: (System2Tester instance) class instance uses self.target as the target computes to remain enabled. target can be a String (Ex: target='compute0') or String Array (Ex: target=['compute0','compute1']).
			stop_after_mrc: (Boolean, Default=False) used for _boot and _fastboot. If set, will stop after MRC is complete.
			pm_enable_no_vf: (Boolean, Default=False) used for _boot and _fastboot. If True, will use fuse file pm_enable_no_vf.cfg to configure fuses (cfc/ia ratios and ia volt=1V) as tester.
		'''
		sv = _get_global_sv()

		## Variables Init
		sv = self.sv
		targetTiles = self.target
		boot = self.boot
		resetGlobals = self.resetGlobals
		computes = self.computes
		die = self.die
		masks = self.masks

		if (not die.startswith("CWF")):
			print (f"Sorry.  This method is not available for {die}.")
			return
		
		if resetGlobals: reset_globals()
		
		# Module and LLC masks for editing, they start with 0xfff...
		_moduleMasks= {die: {comp: 0xfffffffffffffff for comp in computes}}
		_llcMasks= {die: {comp: 0xfffffffffffffff for comp in computes}}

		if not isinstance(targetTiles,list): # Single target
			targetTileList = [targetTiles] # Convert to Array
		else: # Target is already an array
			targetTileList = targetTiles	
		
		print (f"****"*20)
		print (f"\tMulti Compute Requested for: {targetTiles}\n")
		print (f"****"*20 +"\n")

		target_compute = targetTileList
		for compute in _moduleMasks[die].keys(): # For each compute
			computeN = sv.socket0.get_by_path(compute).target_info.instance # Compute Id 
			
			if compute not in target_compute: # Compute will be disabled

				combineMask = masks[f'llc_compute_{computeN}'] | masks[f'ia_compute_{computeN}']
				
				# Check for the first enabled module or LLC and enable it
				binMask = bin(combineMask)
				first_zero = binMask[::-1].find('0')
				disMask = ~(1 << (first_zero)) & ((1 << DMR_TOTAL_MODULES_PER_CBB)-1) 

				print(f"\n\t{compute.upper()} not selected, enabling only the first available slice -> {first_zero}")
				_moduleMasks[die][compute] = disMask | masks[f'ia_compute_{computeN}'] # Enable this module
				_llcMasks[die][compute] = disMask | masks[f'llc_compute_{computeN}'] # Enable this LLC
			
			else: # If compute is not being disabled, keep original Mask
				print(f"\n\t{compute.upper()} selected, mantaining original Masks")
				_moduleMasks[die][compute] = masks[f'ia_compute_{computeN}']
				_llcMasks[die][compute] = masks[f'llc_compute_{computeN}']
							
			print  (f'{compute}:'+ "module disables mask:  0x%x" % (_moduleMasks[die][compute])) 
			print  (f'{compute}:'+ "slice disables mask: 0x%x" % (_llcMasks[die][compute])) 
			
		# Set new masks as the Class masks
		self.modulemask = _moduleMasks[die]
		self.slicemask = _llcMasks[die]

		if boot:
			if self.Fastboot:
				self._fastboot(stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)
			else:
				self._doboot(stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)

	## GNR needs at least one module enabled per COMPUTE, we are limited here, as WA we are leaving the selected compute alive plus the first full slice on the other COMPUTES.
	def setMesh(self, CustomConfig = [], stop_after_mrc=False, pm_enable_no_vf=False, lsb = False):
		'''
		Sets modules and LLCs to run a specific or custom configuration. 

		Inputs:
			self: (System2Tester instance) class instance uses self.target as the desired configuration String. This must be one of the following:
				'FirstPass': Booting only with Columns 0, 3, 6 and 9")
				'SecondPass': Booting only with Columns 1, 4, and 7")
				'ThirdPass': Booting only with Columns 2, 5, and 8 (Applies to X3)")
				'Custom': Booting with user mix & match configuration, Cols or Rows")
				'External': Use configuration from file .\\ConfigFiles\\GNRMasksDebug.json"
		
			CustomConfig: (Array, Default=[]) Array for 'Custom' mode to set desired configuration.
			stop_after_mrc: (Boolean, Default=False) used for _boot and _fastboot. If set, will stop after MRC is complete.
			pm_enable_no_vf: (Boolean, Default=False) used for _boot and _fastboot. If True, will use fuse file pm_enable_no_vf.cfg to configure fuses (cfc/ia ratios and ia volt=1V) as tester.
			lsb: (Boolean, Default=False) Input for dpm.pseudo_bs.
		'''
		## Variables Init
		sv = self.sv
		targetConfig = self.target
		boot = self.boot
		ht_dis = self.ht_dis
		resetGlobals = self.resetGlobals
		computes = self.computes
		die = self.die
		masks = self.masks
		readFuse = self.readFuse
		clusterCheck = self.clusterCheck


		if (not die.startswith("CWF")):
			print (f"Sorry.  This method is not available for {die}.")
			return
		
		if resetGlobals: reset_globals()
	
		# Call DPMChecks Mesh script for mask change, we are not booting here
		module_count, llc_count, Masks_test = dpm.pseudo_bs(ClassMask = targetConfig, Custom = CustomConfig, boot = False, use_core = False, htdis = ht_dis, fuse_read = readFuse, s2t = True, masks = masks, clusterCheck = clusterCheck, lsb = lsb)

		# Building arrays based on system structure
		_moduleMasks= {die: {comp: Masks_test[targetConfig][f'core_comp_{comp[-1]}'] for comp in self.computes}}
		_llcMasks= {die: {comp: Masks_test[targetConfig][f'llc_comp_{comp[-1]}'] for comp in self.computes}}

		# Below dicts are only for converting of variables str to int
		modules = {}
		llcs = {}
		
		print(f'\nSetting new Masks for {targetConfig} configuration:\n')
		for compute in _moduleMasks[die].keys(): # For each compute

			modules[compute] =  int(_moduleMasks[die][compute],16)
			llcs[compute] =  int(_llcMasks[die][compute],16)
			print  (f'\t{compute}:'+ "module disables mask:  0x%x" % (modules[compute])) 
			print  (f'\t{compute}:'+ "slice disables mask: 0x%x" % (llcs[compute])) 			

		# Setting the Class masks in script arrays
		self.modulemask = modules
		self.slicemask = llcs

		if boot:
			if self.Fastboot:
				self._fastboot(stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)
			else:
				self._doboot(stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)

	## Boots the unit using the bootscript with fuse_strings.
	def _doboot(self, stop_after_mrc=False, fixed_core_freq = None, fixed_mesh_freq=None, fixed_io_freq=None, avx_mode = None, acode_dis=None, vp2intersect_en=True, ia_p0=None, ia_p1=None, ia_pn=None, ia_pm=None, cfc_p0=None, cfc_p1=None, cfc_pn=None, cfc_pm=None, io_p0=None, io_p1=None, io_pn=None, io_pm=None, pm_enable_no_vf=False):
		'''
		Calls bootscript, if modulemask and llcmask is not set, then both llc_slice_disable and ia_core_disable get masks value

		Inputs:
			self: (System2Tester instance) class instance uses saved info such as original masks and new masks.
			stop_after_mrc: (Boolean, Default=False) If set, will stop after MRC is complete.
			fixed_core_freq: (Boolean, Default=None) if set, set core P0,P1,Pn and pmin.
			fixed_mesh_freq: (Boolean, Default=None) if set, set mesh P0,P1,Pn and pmin.
			fixed_io_freq: (Boolean, Default=None) if set, set io P0,P1,Pn and pmin.
			avx_mode: (String, Default=None)  Set AVX mode.
			acode_dis: (Boolean, Default=None) Disable acode.
			vp2intersect_en: (Boolean, Default=None) If set, will enable VPINTERSECT instruction ( needed for some Dragon Content )
			ia_p0: (Int, Default=None) CORE P0.
			ia_p1: (Int, Default=None) CORE P1.
			ia_pn: (Int, Default=None) CORE Pn.
			ia_pm: (Int, Default=None) CORE Pm.
			cfc_p0: (Int, Default=None) CFC P0.
			cfc_p1: (Int, Default=None) CFC P1.
			cfc_pn: (Int, Default=None) CFC Pn.
			cfc_pm: (Int, Default=None) CFC Pm.
			io_p0: (Int, Default=None) IO P0.
			io_p1: (Int, Default=None) IO P1.
			io_pn: (Int, Default=None) IO Pn.
			io_pm: (Int, Default=None) IO Pm.
			pm_enable_no_vf: (Boolean, Default=False) if True, will use fuse file pm_enable_no_vf.cfg to configure fuses (cfc/ia ratios and ia volt=1V) as tester	
		'''

		global _boot_string
		sv = self.sv
		ipc = self.ipc
		die = self.die
		masks = self.masks
		# ht_dis = self.ht_dis
		moduleslicemask= self.modulemask
		slicemask = self.slicemask
		print(f"die: {die}")
		# Need to move this to a better implementation
		product = {	'DMRSP': 	{   'config':['cbb0', 'cbb1'],
									'segment': 'DMRSP',
									'compute_config': 'x2'},
					'DMRAP':	{   'config':['cbb0', 'cbb1', 'cbb2', 'cbb3'],
									'segment': 'DMRAP',
									'compute_config': 'x4'},}
		
		# Retrieve local path
		parent_dir = os.path.dirname(os.path.realpath(__file__))
		fuses_dir = os.path.join(parent_dir, 'Fuse')
		
		
		b_extra = global_boot_extra
		_fuse_str = []
		_fuse_str_compute = []
		_fuse_str_io = []
		_fuse_files = []
		_fuse_files_compute = []
		_fuse_files_io = []
		_llc = []
		_ia = []

		# htdis_comp = [#'scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_fused_ht_dis=0x1', 
		# 		'pcu.capid_capid0_ht_dis_fuse=0x1']
		# htdis_io = ['punit_iosf_sb.soc_capid_capid0_max_lp_en=0x1','punit_iosf_sb.soc_capid_capid0_ht_dis_fuse=0x1']
		#vp2i_en_comp = ['scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_vp2intersect_dis=0x0']

		# if ht_dis == None and global_ht_dis !=None: ht_dis = global_ht_dis
		if acode_dis == None and global_acode_dis !=None: acode_dis = global_acode_dis
		if global_boot_stop_after_mrc: stop_after_mrc = True
		if avx_mode == None and global_avx_mode !=None: avx_mode = global_avx_mode
		if fixed_core_freq == None and global_fixed_core_freq !=None: fixed_core_freq = global_fixed_core_freq
		if ia_p0 == None and global_ia_p0 !=None: ia_p0 = global_ia_p0
		if ia_p1 == None and global_ia_p1 !=None: ia_p1 = global_ia_p1
		if ia_pn == None and global_ia_pn !=None: ia_pn = global_ia_pn
		if ia_pm == None and global_ia_pm !=None: ia_pm = global_ia_pm
		if fixed_mesh_freq == None and global_fixed_mesh_freq !=None: fixed_mesh_freq = global_fixed_mesh_freq
		if cfc_p0 == None and global_cfc_p0 !=None: cfc_p0 = global_cfc_p0
		if cfc_p1 == None and global_cfc_p1 !=None: cfc_p1 = global_cfc_p1
		if cfc_pn == None and global_cfc_pn !=None: cfc_pn = global_cfc_pn
		if cfc_pm == None and global_cfc_pm !=None: cfc_pm = global_cfc_pm
		if fixed_io_freq == None and global_fixed_io_freq !=None: fixed_io_freq = global_fixed_io_freq
		if io_p0 == None and global_io_p0 !=None: io_p0 = global_io_p0
		if io_p1 == None and global_io_p1 !=None: io_p1 = global_io_p1
		if io_pn == None and global_io_pn !=None: io_pn = global_io_pn
		if io_pm == None and global_io_pm !=None: io_pm = global_io_pm

		if (fixed_core_freq != None):
			ia_p0 = fixed_core_freq
			ia_p1 = fixed_core_freq
			ia_pn = fixed_core_freq
			ia_pm = fixed_core_freq
		if (fixed_mesh_freq != None):
			cfc_p0 = fixed_mesh_freq
			cfc_p1 = fixed_mesh_freq
			cfc_pn = fixed_mesh_freq
			cfc_pm = fixed_mesh_freq
		if (fixed_mesh_freq != None):
			io_p0 = fixed_io_freq
			io_p1 = fixed_io_freq
			io_pn = fixed_io_freq
			io_pm = fixed_io_freq

		print('\nUsing the following configuration for unit boot: ')
		if ht_dis: print('\tHyper Threading disabled')
		if acode_dis: print('\tAcode disabled')
		if stop_after_mrc: print('\tStop after MRC')
		print(f'\tConfigured License Mode: {avx_mode}')
		print(f'\tCore Frequencies:')
		print(f'\t\tIA P0: {ia_p0}')
		print(f'\t\tIA P1: {ia_p1}')
		print(f'\t\tIA PN: {ia_pn}')
		print(f'\t\tIA MIN: {ia_pm}')
		print(f'\tCompute Mesh Frequencies:')
		print(f'\t\tCFC MESH P0: {cfc_p0}')
		print(f'\t\tCFC MESH P1: {cfc_p1}')
		print(f'\t\tCFC MESH PN: {cfc_pn}')
		print(f'\t\tCFC MESH MIN: {cfc_pm}')
		print(f'\tIO Mesh Frequencies:')
		print(f'\t\tCFC IO P0: {io_p0}')
		print(f'\t\tCFC IO P1: {io_p1}')
		print(f'\t\tCFC IO PN: {io_pn}')
		print(f'\t\tCFC IO MIN: {io_pm}')

		try:
			temp = sv.socket0.compute0.fuses.hwrs_top_rom.ip_disable_fuses_dword6_core_disable ## Need to change this
		except:
			itp.forcereconfig()
			itp.unlock()
			sv.refresh()
		
		##PM enable no vf not enabled yet, do not use... WIP
		if (pm_enable_no_vf == True): 
			_fuse_files_compute=[f'{fuses_dir}\\pm_enable_no_vf_computes.cfg'] ## Fix the file for GNR
			_fuse_files_io = [f'{fuses_dir}\\pm_enable_no_vf_ios.cfg'] ## Fix the file for GNR


		if (stop_after_mrc): b_extra+=', gotil=\"phase6_cpu_reset_break\"'
		
		#masks = dpm.fuses(rdFuses = False, sktnum =[0])


		_moduleslicemask ={}
		_slicemask = {}
		
		for key, value in masks.items():
			newkey = f'cbb{key[-1]}'
			if key.startswith('ia_'):
				_modulemask[newkey] = value
			if key.startswith('llc_'):
				_llcmask[newkey] = value
		
		
		if (moduleslicemask == None): 
			moduleslicemask = _moduleslicemask
			

		if (slicemask == None): 
			#slicemask = moduleslicemask
			_boot_disable_llc = ''
		else:
			for key, value in slicemask.items():
				_llc +=  [('llc_slice_disable_cbb_%s = %s')  % (key[-1],hex(value))]
			_boot_disable_llc = ','.join(_llc) + ','

		# if (ht_dis): 
		# 	_fuse_str_compute+=htdis_comp
		# 	_fuse_str_io+=htdis_io
		#if (acode_dis): _fuse_str+=['pcu.pcode_acp_enable=0x0'] # Not used for CWF
		"""
		if (vp2intersect_en): 
			#_fuse_str+=[ 'cfs_core_c0_r2.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c0_r4.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c0_r5.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c1_r2.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c1_r3.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c1_r4.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c1_r5.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c2_r2.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c2_r3.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c2_r4.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c2_r5.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c3_r2.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c3_r3.core_core_fuse_misc_vp2intersect_dis=0x0', 'cfs_core_c3_r4.core_core_fuse_misc_vp2intersect_dis=0x0']
			_fuse_str_compute += vp2i_en_comp"""

		curves = {	'turbo': [f'pcode_sst_pp_##profile##_turbo_ratio_limit_ratios_cdyn_index##idx##_ratio##ratio##'],
					'p1': [f'pcode_sst_pp_##profile##_sse_p1_ratio',f'pcode_sst_pp_##profile##_avx2_p1_ratio',f'pcode_sst_pp_##profile##_avx512_p1_ratio',f'pcode_sst_pp_##profile##_amx_p1_ratio'],
					'pstates' : {	#'p0':'pcode_ia_p0_ratio', 
									'pn':'pcode_ia_pn_ratio', 
									'min':'pcode_ia_min_ratio',
								}
				}
		
		# Enumarate all the variables needed for power curves	
		ppfs = [0,1,2,3,4]
		idxs = [0,1,2,3,4,5]
		ratios = [0,1,2,3,4,5,6,7]
		

		# IA P0 frequencies flat
		if (ia_p0 != None): 
			# _fuse_str_compute += ['pcu.pcode_ia_p0_ratio=0x%x' % ia_p0]
			ia_turbo = None ## Will have it disabled for now, need to check if needed, maybe add a new switch
			# IA P0 Turbo Limits
			# Limit fuses (RATIO)
			if ia_turbo != None:
				for curve in curves['turbo']:
					for pp in ppfs:
						for idx in idxs:
							for ratio in ratios:
								turbo_string = curve
										
								#for _search in search_string:
								turbo_string = turbo_string.replace(f'##profile##',str(pp))
								turbo_string = turbo_string.replace(f'##idx##',str(idx))
								turbo_string = turbo_string.replace(f'##ratio##',str(ratio))

								_fuse_str_compute += [f'punit.{turbo_string}=' + '0x%x' % ia_p0]

		# IA P1 frequencies flat
		if (ia_p1 != None): 
			for curve in curves['p1']:
				for pp in ppfs:
					p1_string = curve
					p1_string = p1_string.replace(f'##profile##',str(pp))
					_fuse_str_compute += [f'punit.{p1_string}=' + '0x%x' % ia_p1]

		# IA PN frequencies flat

		if (ia_pn != None): 
			_fuse_str_compute += ['punit.pcode_ia_pn_ratio=0x%x' % ia_pn]
		if (ia_pm != None): 
			_fuse_str_compute += ['punit.pcode_ia_min_ratio=0x%x' % ia_pm]
	
		## CFC is modifying IOs as well, can we make them separate?
		if (cfc_p0 != None): 
			_fuse_str_compute += ['punit.pcode_sst_pp_0_cfccbb_p0_ratio=0x%x' % cfc_p0]
		if (cfc_p1 != None): 
			_fuse_str_compute += ['punit.pcode_sst_pp_0_cfccbb_p1_ratio=0x%x' % cfc_p1]
		# if (cfc_pn != None): 
		# 	_fuse_str_compute += ['punit.pcode_cfc_pn_ratio=0x%x' % cfc_pn]
		if (cfc_pm != None): 
			_fuse_str_compute += ['punit.pcode_cfccbb_min_ratio=0x%x' % cfc_pm]

		if (io_p0 != None): 
			_fuse_str_io += ['punit.pcode_sst_pp_0_cfcio_p0_ratio=0x%x' % io_p0]
		if (io_p1 != None): 
			_fuse_str_io += ['punit.pcode_sst_pp_0_cfcio_p1_ratio=0x%x' % io_p1]
		# if (io_pn != None): 
		# 	_fuse_str_io += ['punit_iosf_sb.pcode_cfc_pn_ratio=0x%x' % io_pn]
		if (io_pm != None): 
			_fuse_str_io += ['punit.pcode_cfcio_min_ratio=0x%x' % io_pm]   

		if (avx_mode != None):
			if (avx_mode) in range (0,8):
				int_mode = avx_mode
			elif avx_mode == "128":
				int_mode = 1        
			elif avx_mode == "256":
				int_mode = 3
			elif avx_mode == "512":
				int_mode=5
			elif avx_mode == "TMUL":
				int_mode=7
			else:
				raise ValueError("Invalid AVX Mode")
			_fuse_str_compute += ['punit_fuses.fw_fuses_iccp_min_license=0x%x' % int_mode]
			# _fuse_str_compute += ['pcu.pcode_iccp_min_license=0x%x' % int_mode,'pcu.pcode_iccp_default=0x%x' % int_mode]

		for key, value in moduleslicemask.items():
			_ia +=  [('ia_core_disable_cbb_%s = %s')  % (key[-1],hex(value))]

		_boot_disable_ia = ','.join(_ia)

		FastBoot = False
		if FastBoot:
			bootopt = 'bs.fast_boot'
			bootcont = 'bs.cont'
		else:
			bootopt = 'b.go'
			bootcont = 'b.cont'

		_boot_string = ('%s(fused_unit=True, enable_strap_checks=False,compute_config="%s",enable_pm=True,segment="%s" %s, %s, %s fuse_str_compute = %s,fuse_str_io = %s, fuse_files_compute=[%s], fuse_files_io=[%s],AXON_UPLOAD_ENABLED = False)') % (bootopt, product[die]['compute_config'], product[die]['segment'], b_extra, _boot_disable_ia, _boot_disable_llc,_fuse_str_compute,_fuse_str_io,_fuse_files_compute, _fuse_files_io)
		
		print("*"*20)
		if FastBoot: print('import users.THR.PythonScripts.thr.GnrBootscriptOverrider as bs')
		else:	print("import toolext.bootscript.boot as b")
		print (_boot_string)
		print("***********************************v********************************************")
		if global_dry_run == False:
			eval(_boot_string)
			#print("********************************************************************************")
			#print (_boot_string)
			#print("********************************************************************************")
			if (stop_after_mrc):
				sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=AFTER_MRC_POST
				print("***********************************v********************************************")
				print(f"sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg={AFTER_MRC_POST}")
				print ("%s(curr_state='phase6_cpu_reset_break')" % bootcont)
				print("***********************************v********************************************")
				if FastBoot: bs.cont(curr_state='phase6_cpu_reset_break')
				else:	b.cont(curr_state='phase6_cpu_reset_break')
				_wait_for_post(AFTER_MRC_POST)
			else:
				_wait_for_post(EFI_POST, sleeptime=120)
			sv_refreshed = False

	
	## Fastboot option to boot the unit using itp.resettarget, works with SLICE MODE only
	def _fastboot(self, stop_after_mrc=False, fixed_core_freq = None, fixed_mesh_freq=None, fixed_io_freq=None, avx_mode = None, acode_dis=None, vp2intersect_en=True, ia_p0=None, ia_p1=None, ia_pn=None, ia_pm=None, cfc_p0=None, cfc_p1=None, cfc_pn=None, cfc_pm=None, io_p0=None, io_p1=None, io_pn=None, io_pm=None, pm_enable_no_vf=False):
		'''
		Calls bootscript with a faster configuration, if modulemask and llcmask is not set, then both llc_slice_disable and ia_core_disable get masks value

		Inputs:
			self: (System2Tester instance) class instance uses saved info such as original masks and new masks.
			stop_after_mrc: (Boolean, Default=False) If set, will stop after MRC is complete
			fixed_core_freq: (Boolean, Default=None) if set, set core P0,P1,Pn and pmin 
			fixed_mesh_freq: (Boolean, Default=None) if set, set mesh P0,P1,Pn and pmin
			fixed_io_freq: (Boolean, Default=None) if set, set io P0,P1,Pn and pmin
			avx_mode: (String, Default=None)  Set AVX mode
			acode_dis: (Boolean, Default=None) Disable acode 
			vp2intersect_en: (Boolean, Default=None) If set, will enable VPINTERSECT instruction ( needed for some Dragon Content )
			ia_p0: (Int, Default=None) CORE P0
			ia_p1: (Int, Default=None) CORE P1
			ia_pn: (Int, Default=None) CORE Pn
			ia_pm: (Int, Default=None) CORE Pm
			cfc_p0: (Int, Default=None) CFC P0
			cfc_p1: (Int, Default=None) CFC P1
			cfc_pn: (Int, Default=None) CFC Pn
			cfc_pm: (Int, Default=None) CFC Pm
			io_p0: (Int, Default=None) IO P0
			io_p1: (Int, Default=None) IO P1
			io_pn: (Int, Default=None) IO Pn
			io_pm: (Int, Default=None) IO Pm
			pm_enable_no_vf: (Boolean, Default=False) if True, will use fuse file pm_enable_no_vf.cfg to configure fuses (cfc/ia ratios and ia volt=1V) as tester
		'''
		global _boot_string
		sv = self.sv 
		ipc = self.ipc
		die = self.die
		masks = self.masks
		# ht_dis = self.ht_dis
		moduleslicemask= self.modulemask
		slicemask = self.slicemask
		BootFuses = self.BootFuses
		
		# Need to move this to a better implementation
		product = {	'DMRSP': 	{   'config':['cbb0', 'cbb1'],
									'segment': 'DMRSP',
									'compute_config': 'x2'},
					'DMRAP':	{   'config':['cbb0', 'cbb1', 'cbb2', 'cbb3'],
									'segment': 'DMRAP',
									'compute_config': 'x4'},}
		
		# Retrieve local path
		parent_dir = os.path.dirname(os.path.realpath(__file__))
		fuses_dir = os.path.join(parent_dir, 'Fuse')
		
		
		b_extra = global_boot_extra
		_fuse_str = []
		_fuse_str_compute = []
		_fuse_str_io = []
		_fuse_files = []
		_fuse_files_compute = []
		_fuse_files_io = []
		_llc = []
		_ia = []


		## Declare all the fuse arrays to be used
		htdis_comp = BootFuses['ht']['compHT']['htdis']#['scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_fused_ht_dis=0x1', 'pcu.capid_capid0_ht_dis_fuse=0x1','fuses.pcu.pcode_lp_disable=0x2','pcu.capid_capid0_max_lp_en=0x1']
		htdis_io = BootFuses['ht']['ioHT']['htdis']#['punit_iosf_sb.soc_capid_capid0_max_lp_en=0x1','punit_iosf_sb.soc_capid_capid0_ht_dis_fuse=0x1']
		
		##Frequency fuses
		CFC_freq_fuses = BootFuses['CFC']['compFreq']
		CFCIO_freq_fuses = BootFuses['CFC']['ioFreq']
		IA_freq_fuses = BootFuses['IA']['compFreq']
		IA_license = BootFuses['IA_license']['compute']

		# if ht_dis == None and global_ht_dis !=None: ht_dis = global_ht_dis
		if acode_dis == None and global_acode_dis !=None: acode_dis = global_acode_dis
		if global_boot_stop_after_mrc: stop_after_mrc = True
		if avx_mode == None and global_avx_mode !=None: avx_mode = global_avx_mode
		if fixed_core_freq == None and global_fixed_core_freq !=None: fixed_core_freq = global_fixed_core_freq
		if ia_p0 == None and global_ia_p0 !=None: ia_p0 = global_ia_p0
		if ia_p1 == None and global_ia_p1 !=None: ia_p1 = global_ia_p1
		if ia_pn == None and global_ia_pn !=None: ia_pn = global_ia_pn
		if ia_pm == None and global_ia_pm !=None: ia_pm = global_ia_pm
		if fixed_mesh_freq == None and global_fixed_mesh_freq !=None: fixed_mesh_freq = global_fixed_mesh_freq
		if cfc_p0 == None and global_cfc_p0 !=None: cfc_p0 = global_cfc_p0
		if cfc_p1 == None and global_cfc_p1 !=None: cfc_p1 = global_cfc_p1
		if cfc_pn == None and global_cfc_pn !=None: cfc_pn = global_cfc_pn
		if cfc_pm == None and global_cfc_pm !=None: cfc_pm = global_cfc_pm
		if fixed_io_freq == None and global_fixed_io_freq !=None: fixed_io_freq = global_fixed_io_freq
		if io_p0 == None and global_io_p0 !=None: io_p0 = global_io_p0
		if io_p1 == None and global_io_p1 !=None: io_p1 = global_io_p1
		if io_pn == None and global_io_pn !=None: io_pn = global_io_pn
		if io_pm == None and global_io_pm !=None: io_pm = global_io_pm

		if (fixed_core_freq != None):
			ia_p0 = fixed_core_freq
			ia_p1 = fixed_core_freq
			ia_pn = fixed_core_freq
			ia_pm = fixed_core_freq
		if (fixed_mesh_freq != None):
			cfc_p0 = fixed_mesh_freq
			cfc_p1 = fixed_mesh_freq
			cfc_pn = fixed_mesh_freq
			cfc_pm = fixed_mesh_freq
		if (fixed_mesh_freq != None):
			io_p0 = fixed_io_freq
			io_p1 = fixed_io_freq
			io_pn = fixed_io_freq
			io_pm = fixed_io_freq

		print('\nUsing the following configuration for unit boot: ')
		if ht_dis: print('\tHyper Threading disabled')
		if acode_dis: print('\tAcode disabled')
		if stop_after_mrc: print('\tStop after MRC')
		print(f'\tConfigured License Mode: {avx_mode}')
		print(f'\tCore Frequencies:')
		print(f'\t\tIA P0: {ia_p0}')
		print(f'\t\tIA P1: {ia_p1}')
		print(f'\t\tIA PN: {ia_pn}')
		print(f'\t\tIA MIN: {ia_pm}')
		print(f'\tCompute Mesh Frequencies:')
		print(f'\t\tCFC MESH P0: {cfc_p0}')
		print(f'\t\tCFC MESH P1: {cfc_p1}')
		print(f'\t\tCFC MESH PN: {cfc_pn}')
		print(f'\t\tCFC MESH MIN: {cfc_pm}')
		print(f'\tIO Mesh Frequencies:')
		print(f'\t\tCFC IO P0: {io_p0}')
		print(f'\t\tCFC IO P1: {io_p1}')
		print(f'\t\tCFC IO PN: {io_pn}')
		print(f'\t\tCFC IO MIN: {io_pm}')

		try:
			temp = sv.socket0.compute0.fuses.hwrs_top_rom.ip_disable_fuses_dword6_core_disable ## Need to change this
		except:
			itp.forcereconfig()
			itp.unlock()
			sv.refresh()

		_moduleslicemask ={}
		_slicemask = {}
		
		for key, value in masks.items():
			newkey = f'compute{key[-1]}'
			if key.startswith('ia_compute_'):
				_moduleslicemask[newkey] = value
			if key.startswith('llc_compute_'):
				_slicemask[newkey] = value
		
		
		if (moduleslicemask == None): 
			moduleslicemask = _moduleslicemask

		# if (ht_dis): 
		# 	_fuse_str+= htdis_comp
		# 	_fuse_str+= htdis_io
		
		#if (vp2intersect_en): 
		#	_fuse_str += vp2i_en_comp

		## Defining new values for IA Frequencies
		# IA P0 frequencies flat
		if (ia_p0 != None): 
			for fuse in IA_freq_fuses['p0']:
				_fuse_str += [fuse + '=0x%x' % ia_p0]
			
		# IA P1 frequencies flat
		if (ia_p1 != None): 
			for fuse in IA_freq_fuses['p1']:
				_fuse_str += [fuse + '=0x%x' % ia_p1]
	
		# IA PN frequencies flat
		if (ia_pn != None): 
			for fuse in IA_freq_fuses['pn']:
				_fuse_str += [fuse + '=0x%x' % ia_pn]

		# IA MIN frequencies flat
		if (ia_pm != None): 
			for fuse in IA_freq_fuses['min']:
				_fuse_str += [fuse + '=0x%x' % ia_pm]

		## Defining new values for MESH CFC Frequencies
		# MESH CFC P0 frequencies flat
		if (cfc_p0 != None): 
			for fuse in CFC_freq_fuses['p0']:
				_fuse_str += [fuse + '=0x%x' % cfc_p0]
			
		# MESH CFC P1 frequencies flat
		if (cfc_p1 != None): 
			for fuse in CFC_freq_fuses['p1']:
				_fuse_str += [fuse + '=0x%x' % cfc_p1]
	
		# MESH CFC PN frequencies flat
		if (cfc_pn != None): 
			for fuse in CFC_freq_fuses['pn']:
				_fuse_str += [fuse + '=0x%x' % cfc_pn]

		# MESH CFC MIN frequencies flat
		if (cfc_pm != None): 
			for fuse in CFC_freq_fuses['min']:
				_fuse_str += [fuse + '=0x%x' % cfc_pm]

		## Defining new values for IO CFC Frequencies
		# CFCIO P0 frequencies flat
		if (io_p0 != None): 
			for fuse in CFCIO_freq_fuses['p0']:
				_fuse_str += [fuse + '=0x%x' % io_p0]
			
		# CFCIO P1 frequencies flat
		if (io_p1 != None): 
			for fuse in CFCIO_freq_fuses['p1']:
				_fuse_str += [fuse + '=0x%x' % io_p1]
	
		# CFCIO PN frequencies flat
		if (io_pn != None): 
			for fuse in CFCIO_freq_fuses['pn']:
				_fuse_str += [fuse + '=0x%x' % io_pn]

		# CFCIO MIN frequencies flat
		if (io_pm != None): 
			for fuse in CFCIO_freq_fuses['min']:
				_fuse_str += [fuse + '=0x%x' % io_pm]

		if (avx_mode != None):
			if (avx_mode) in range (0,8):
				int_mode = avx_mode
			elif avx_mode == "128":
				int_mode = 1        
			elif avx_mode == "256":
				int_mode = 3
			elif avx_mode == "512":
				int_mode=5
			elif avx_mode == "TMUL":
				int_mode=7
			else:
				raise ValueError("Invalid AVX Mode")
			ia_min_lic = IA_license['min']
			ia_def_lic = IA_license['default']
			_fuse_str += [f'{ia_min_lic}=0x%x' % int_mode,f'{ia_def_lic}=0x%x' % int_mode]

		if (slicemask != None): 
			_fuse_str+= mask_fuse_llc_array(self.slicemask)

		if (moduleslicemask != None): 
			_fuse_str+= mask_fuse_module_array(self.modulemask)

		print("*"*20)
		print('Using FastBoot with itp.resettarget() and ram flush')
		
		if global_dry_run == False:
			if (stop_after_mrc):
				print(f'Setting biosscratchpad6_cfg for desired PostCode = {AFTER_MRC_POST}')
				sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=AFTER_MRC_POST

			
			print(Fore.YELLOW + "***********************************v********************************************")
			print(Fore.YELLOW + "******************** Starting Unit Fast Boot Fuse Override *********************")
			print(Fore.YELLOW + "***********************************v********************************************")			

			fuse_cmd_override_reset(_fuse_str)

			if (stop_after_mrc):

				_wait_for_post(AFTER_MRC_POST)
			else:
				_wait_for_post(EFI_POST, sleeptime=120)
			sv_refreshed = False

