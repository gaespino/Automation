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
- Version 1.6 (3/7/2025): Added EFI, MRC, and BIOS break variables, custom BIOS break point option, and Cancel flag for Framework Mode.
- Version 1.5 (3/6/2025): Introduced code modularity for multiproducts baseline.
- Version 1.30: Enhanced self-check code for bootscript and fastboot, improved fuses assignment, fixed bootscript issue, and interface improvements.
- Revision 1.2 (20/06/2024): Code cleanup and UI improvements.
- Revision 1.1 (16/04/2024): Initial version.

"""

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== Modules/Libraries Imports =========================================================================#
#========================================================================================================#

import namednodes
import math
import time
import ipccli
import sys
from colorama import Fore, Style, Back
import importlib
import os
from tabulate import tabulate
from importlib import import_module

## Custom Modules

import toolext.bootscript.boot as b

# Append the Main Scripts Path
MAIN_PATH = os.path.abspath(os.path.dirname(__file__))

## Imports from S2T Folder  -- ADD Product on Module Name for Production
sys.path.append(MAIN_PATH)
import ConfigsLoader as LoadConfig
config = LoadConfig.config

# Set Used product Variable -- Called by Framework
SELECTED_PRODUCT = config.SELECTED_PRODUCT
BASE_PATH = config.BASE_PATH
LEGACY_NAMING = SELECTED_PRODUCT.upper() if SELECTED_PRODUCT.upper() in ['GNR', 'CWF'] else ''
THR_NAMING = SELECTED_PRODUCT.upper() if SELECTED_PRODUCT.upper() in ['GNR', 'CWF', 'DMR'] else ''

if LoadConfig.DEV_MODE:
	import dpmChecks as dpm
else:
	dpm = import_module(f'{BASE_PATH}.S2T.dpmChecks{LEGACY_NAMING}')

importlib.reload(LoadConfig)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== IPC and SV Initialization ==============================================================#
#========================================================================================================#

from namednodes import sv
from ipccli import BitData

ipc = ipccli.baseaccess()
itp = ipc

sv_refreshed = True
verbose = False
debug = False


def _get_global_sv():
	'''
	Lazy initialize for the sapphirerapids sv 'socket' instance

	Return
	------
	sv: class 'components.ComponentManager'
	'''
	global sv
	global ipc

	if sv is None:
		from namednodes import sv
		sv.initialize()
	if not sv.sockets:
		print("No socketlist detected. Restarting baseaccess and sv.refresh")
		ipc = _get_global_ipc()
		ipc.forcereconfig()
		if ipc.islocked():
			ipc.unlock()
		#ipc.unlock()
		#ipc.uncores.unlock()
		sv.initialize()
		sv.refresh()    #determined this was needed in manual testing
	return sv

def _get_global_ipc():
	'''
	Lazy initialize for the global IPC instance
	'''
	global ipc
	if ipc is None:
		import ipccli
		ipc = ipccli.baseaccess()
		ipc.forcereconfig()
		ipc.unlock()
		ipc.uncores.unlock()
	return ipc

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

global_boot_stop_after_mrc=None
global_boot_postcode=None
global_ht_dis=None
global_2CPM_dis=None
global_1CPM_dis=None
global_acode_dis=None
global_fixed_core_freq=None
global_ia_p0=None
global_ia_vf=None
global_ia_turbo=None
global_ia_p1=None
global_ia_pn=None
global_ia_pm=None
global_cfc_p0=None
global_cfc_p1=None
global_cfc_pn=None
global_cfc_pm=None
global_slice_core = None
# Including IO mesh frequencies separate
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
global_fixed_mlc_volt=None # Holder not used
global_fixed_cfcio_volt=None
global_fixed_ddrd_volt=None
global_fixed_ddra_volt=None
global_vbumps_configuration=None
global_u600w = None
#global_system = ''
_boot_string=""
AFTER_MRC_POST = 0xbf000000
#EFI_POST = 0x57000000
EFI_POST = 0xef0000ff
LINUX_POST = 0x58000000
#EFI_POST_old = 0x57000000
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
	global global_boot_stop_after_mrc
	global global_boot_postcode
	global global_ht_dis
	global global_2CPM_dis
	global global_1CPM_dis
	global global_acode_dis
	global global_fixed_core_freq
	global global_fixed_mesh_freq
	global global_fixed_io_freq
	global global_avx_mode
	global global_ia_vf
	global global_ia_turbo
	global global_fixed_core_volt
	global global_fixed_cfc_volt
	global global_fixed_hdc_volt
	global global_fixed_cfcio_volt
	global global_fixed_ddrd_volt
	global global_fixed_ddra_volt
	global global_vbumps_configuration
	global global_u600w
	global global_boot_extra
	#global global_dry_run
	global_boot_stop_after_mrc=None
	global_boot_postcode=None
	global_ht_dis=None
	global_2CPM_dis=None
	global_1CPM_dis=None
	global_acode_dis=None
	global_fixed_core_freq=None
	global_fixed_mesh_freq=None
	global_fixed_io_freq=None
	global_avx_mode=None
	global_slice_core = None
	#global_dry_run=False
	global_ia_vf=None
	global_ia_turbo=None
	# Voltage Resets
	global_fixed_core_volt=None
	global_fixed_cfc_volt=None
	global_fixed_hdc_volt=None
	global_fixed_cfcio_volt=None
	global_fixed_ddrd_volt=None
	global_fixed_ddra_volt=None
	global_vbumps_configuration=None
	global_u600w=None
	global_boot_extra=""


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== MAIN CODE STARTS HERE ==================================================================#
#========================================================================================================#


## S2T main Class, includes the different masking mode and boot options
class System2Tester():

	def __init__(self, target, masks = None, coremask=None, slicemask=None, boot = True, ht_dis = False, dis_2CPM = None, dis_1CPM = None, fresh_state = True, readFuse = False, clusterCheck = False , fastboot = True, ppvc_fuses = None, external_fuses = None, execution_state = None):

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
		self.dis_2CPM = dis_2CPM
		self.fresh_state = fresh_state
		self.read_Fuse = False
		self.readFuse = readFuse
		self.sv = sv #_get_global_sv()
		self.ipc = ipc #_get_global_ipc()
		self.clusterCheck = clusterCheck
		self.computes = sv.socket0.computes.name
		self.ios = sv.socket0.ios.name
		self.instances = sv.socket0.computes.instance
		self.sktnum = [0]
		self.die = PRODUCT_CONFIG
		self.BootFuses = dpm.FuseFileConfigs
		self.Fastboot = fastboot
		self.fuse_str = []
		self.fuse_str_io = []
		self.fuse_str_compute = []
		## Added split fuse to apply PPVC
		self.fuse_str_compute_0 = []
		self.fuse_str_compute_1 = []
		self.fuse_str_compute_2 = []
		self.fuse_str_io_0 = []
		self.fuse_str_io_1 = []
		self.fuse_2CPM = dpm.fuses_dis_2CPM(dis_2CPM, bsformat = (not fastboot)) if dis_2CPM != None else []
		self.fuse_1CPM = [] ## Not available for versions on GNR / CWF -- Placeholder for DMR compatbibility on S2T

		#self.fuse_str_compute_0 = []
		self.ppvc_fuses = ppvc_fuses
		self.external_fuses = external_fuses

		## Option to bring preconfigured Mask
		if masks == None: self.masks = dpm.fuses(rdFuses = self.readFuse, sktnum =self.sktnum, printFuse=False)
		else: self.masks = masks

	## Needs at least one core enabled per COMPUTE, we are limited here, as WA we are leaving the selected CORE alive plus the first full slice on the other COMPUTES.
	def setCore(self):

		'''
		Sets up system to run 1 core per compute
		targetTile: disables all tiles but targetTile
		targetLogicalCore: disables all cores but targetLogicalCore. All tiles other than targetLogicalCore tile will be disabled
		boot: (True)/False Will call bootscript with new setting
		We need at least one Core per compute, best we can do for the moment is left first core available in
		ht_dis : (True_/False
		'''

		#sv = _get_global_sv()

		## Variables Init
		sv = self.sv
		targetLogicalCore = self.target
		boot = self.boot
		fresh_state = self.fresh_state
		computes = self.computes
		die = self.die
		masks = self.masks

		if (die not in CORETYPES.keys()):
			print (f"sorry.  This method still needs updating for {die}.  ")
			return

		if fresh_state: reset_globals()
		#computes = sv.socket0.computes.name

		# Building arrays based on system structure
		_coreMasks= {die: {comp: 0xfffffffffffffff for comp in computes}}
		_llcMasks= {die: {comp: 0xfffffffffffffff for comp in computes}}

		## Read Mask enable for this part, no need for fuse ram need in Slice mode as we already read those at the beggining
		#masks = dpm.fuses(system = die, rdFuses = readFuse, sktnum =[0])
		target_compute = int(targetLogicalCore/60)

		coremask = ~(1 << (targetLogicalCore - (60 * target_compute))) & ((1 << 60) - 1)

		for compute in _coreMasks[die].keys():
			computeN = sv.socket0.get_by_path(compute).target_info.instance

			if int(computeN) == target_compute:
				_coreMasks[die][compute] = coremask | masks[f'ia_compute_{computeN}']
				_llcMasks[die][compute] = masks[f'llc_compute_{computeN}']
			else:
				combineMask = masks[f'llc_compute_{computeN}'] | masks[f'ia_compute_{computeN}']
				## We will check for the first enabled slice and enable it

				binMask = bin(combineMask)
				first_zero = binMask[::-1].find('0')
				disMask = ~(1 << (first_zero)) & ((1 << 60)-1)
				#print(first_zero)
				#print(hex(disMask))
				_coreMasks[die][compute] = disMask | masks[f'ia_compute_{computeN}']
				#_llcMasks[die][compute] = disMask | masks[f'llc_compute_{computeN}']
				_llcMasks[die][compute] = masks[f'llc_compute_{computeN}']

			print  (f'{compute}:'+ "core disabled mask:  0x%x" % (_coreMasks[die][compute]))
			print  (f'{compute}:'+ "slice disabled mask: 0x%x" % (_llcMasks[die][compute]))

		# Setting the Class masks
		self.coremask = _coreMasks[die]
		self.slicemask = _llcMasks[die]

		if boot:
			if self.Fastboot:
				self._fastboot()
			else:
				self._doboot()

	## Needs at least one core enabled per COMPUTE, we are limited here, as WA we are leaving the selected compute alive plus the first full slice on the other COMPUTES.
	def setTile(self, boot_postcode=False,stop_after_mrc=False, pm_enable_no_vf=False):
		'''
		Will disable all cores but targetTile
		targetTiles: disables all tiles but targetTiles.  Can be single tile or list of tiles
		ht_dis : True/(False)
		boot: (True)/False Will call bootscript with new settings
		coresliceMask: Override with desired coreslicemask.  Default: None
		'''
		#sv = _get_global_sv()

		## Variables Init
		sv = self.sv
		targetTiles = self.target
		boot = self.boot
		fresh_state = self.fresh_state
		computes = self.computes
		die = self.die
		masks = self.masks

		#if die == None: die = sv.socket0.target_info["segment"]
		if (die not in CORETYPES.keys()):
			print (f"sorry.  This method still needs updating for {die}.  ")
			return

		if fresh_state: reset_globals()
		#computes = sv.socket0.computes.name

		# Building arrays based on system structure
		_coreMasks= {die: {comp: 0xfffffffffffffff for comp in computes}}
		_llcMasks= {die: {comp: 0xfffffffffffffff for comp in computes}}

		## Read Mask enable for this part, no need for fuse ram need in Slice mode as we already read those at the beggining
		#masks = dpm.fuses(system = die, rdFuses = readFuse, sktnum =[0])

		## Checking if multiple instances are selected

		if not isinstance(targetTiles,list):
			#print (f"Single Compute Requested for: {targetTiles}")
			targetTileList = [targetTiles]
		else:

			targetTileList = targetTiles
		print (f"****"*20)
		print (f"\tMulti Compute Requested for: {targetTiles}\n")
		print (f"****"*20 +"\n")
		target_compute = targetTileList

		#coremask = ~(1 << (targetLogicalCore - (60 * target_compute))) & ((1 << 60) - 1)

		for compute in _coreMasks[die].keys():
			computeN = sv.socket0.get_by_path(compute).target_info.instance

			if compute not in target_compute:


				combineMask = masks[f'llc_compute_{computeN}'] | masks[f'ia_compute_{computeN}']
				## We will check for the first enabled slice and enable it

				binMask = bin(combineMask)
				first_zero = binMask[::-1].find('0')
				disMask = ~(1 << (first_zero)) & ((1 << 60)-1)

				print(f"\n\t{compute.upper()} not selected, enabling only the first available slice -> {first_zero}")
				_coreMasks[die][compute] = disMask | masks[f'ia_compute_{computeN}']
				#_llcMasks[die][compute] = disMask | masks[f'llc_compute_{computeN}']
				_llcMasks[die][compute] = disMask | masks[f'llc_compute_{computeN}']

			## If compute is not being disabled keep original Mask
			else:
				print(f"\n\t{compute.upper()} selected, mantaining original Masks")
				_coreMasks[die][compute] = masks[f'ia_compute_{computeN}']
				_llcMasks[die][compute] = masks[f'llc_compute_{computeN}']

			print  (f'{compute}:'+ "core disabled mask:  0x%x" % (_coreMasks[die][compute]))
			print  (f'{compute}:'+ "slice disabled mask: 0x%x" % (_llcMasks[die][compute]))


		# Setting the Class masks
		self.coremask = _coreMasks[die]
		self.slicemask = _llcMasks[die]

		if boot:
			if self.Fastboot:
				self._fastboot(boot_postcode=boot_postcode,stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)
			else:
				self._doboot(boot_postcode=boot_postcode,stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)

	## GNR needs at least one core enabled per COMPUTE, we are limited here, as WA we are leaving the selected compute alive plus the first full slice on the other COMPUTES.
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
		computes = self.computes
		die = self.die

		readFuse = self.readFuse
		clusterCheck = self.clusterCheck

		if extMasks != None:
			masks = {k:int(v,16) for k, v in extMasks.items()}
		else:
			masks = self.masks

		if (die not in CORETYPES.keys()):
			print (f"sorry.  This method still needs updating for {die}.  ")
			return

		if fresh_state: reset_globals()
		#computes = sv.socket0.computes.name

		# Call DPMChecks Mesh script for mask change, we are not booting here
		core_count, llc_count, Masks_test = dpm.pseudo_bs(ClassMask = targetConfig, Custom = CustomConfig, boot = False, use_core = False, htdis = ht_dis, dis_2CPM = dis_2CPM, fuse_read = readFuse, s2t = True, masks = masks, clusterCheck = clusterCheck, lsb = lsb, skip_init = True)

		# Building arrays based on system structure
		_coreMasks= {die: {comp: Masks_test[targetConfig][f'core_comp_{comp[-1]}'] for comp in self.computes}}
		_llcMasks= {die: {comp: Masks_test[targetConfig][f'llc_comp_{comp[-1]}'] for comp in self.computes}}

		# Below dicts are only for converting of variables str to int
		cores = {}
		llcs = {}

		print(f'\nSetting new Masks for {targetConfig} configuration:\n')
		for compute in _coreMasks[die].keys():

			cores[compute] =  int(_coreMasks[die][compute],16)
			llcs[compute] =  int(_llcMasks[die][compute],16)
			print  (f'\t{compute}:'+ "core disabled mask:  0x%x" % (cores[compute]))
			print  (f'\t{compute}:'+ "slice disabled mask: 0x%x" % (llcs[compute]))

		# Setting the Class masks in script arrays
		self.coremask = cores
		self.slicemask = llcs

		if boot:
			if self.Fastboot:
				self._fastboot(boot_postcode=boot_postcode,stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)
			else:
				self._doboot(boot_postcode=boot_postcode,stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)

	## GNR needs at least one core enabled per COMPUTE, we are limited here, as WA we are leaving the selected compute alive plus the first full slice on the other COMPUTES.
	def setfc(self, extMasks = None, boot_postcode=False, stop_after_mrc=False, pm_enable_no_vf=False):
		'''
		Will Boot Unit with full chip configuration, extMasks option to input a custom masking for slice defeature

		'''
		## Variables Init

		boot = self.boot
		fresh_state = self.fresh_state
		die = self.die

		if (die not in CORETYPES.keys()):
			print (f"sorry.  This method still needs updating for {die}.  ")
			return

		if fresh_state: reset_globals()
		#computes = sv.socket0.computes.name

		# Building arrays based on system structure
		if extMasks != None:
			_coreMasks= {die: {comp: extMasks[f'ia_compute_{comp[-1]}'] for comp in self.computes}}
			_llcMasks= {die: {comp: extMasks[f'llc_compute_{comp[-1]}'] for comp in self.computes}}

			# Below dicts are only for converting of variables str to int
			cores = {}
			llcs = {}

			print(f'\nSetting New Mask Based on External Masks Configuration:\n')
			for compute in _coreMasks[die].keys():

				cores[compute] =  int(_coreMasks[die][compute],16)
				llcs[compute] =  int(_llcMasks[die][compute],16)
				print  (f'\t{compute}:'+ "core disabled mask:  0x%x" % (cores[compute]))
				print  (f'\t{compute}:'+ "slice disabled mask: 0x%x" % (llcs[compute]))

			# Setting the Class masks in script arrays
			self.coremask = cores
			self.slicemask = llcs

		if boot:
			if self.Fastboot:
				self._fastboot(boot_postcode=boot_postcode,stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)
			else:
				self._doboot(boot_postcode=boot_postcode,stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)

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

		#{	'limits': [f'pcode_sst_pp_##profile##_turbo_ratio_limit_ratios_cdyn_index##idx##_ratio##ratio##'],
		#			'p1': [f'pcode_sst_pp_##profile##_sse_p1_ratio',f'pcode_sst_pp_##profile##_avx2_p1_ratio',f'pcode_sst_pp_##profile##_avx512_p1_ratio',f'pcode_sst_pp_##profile##_amx_p1_ratio'],
		#			'pstates' : {	'p0':'pcode_ia_p0_ratio',
		#							'pn':'pcode_ia_pn_ratio',
		#							'min':'pcode_ia_min_ratio',
		#						},
		#			'vf_curve' : [f'pcode_ia_vf_ratio_voltage_index##idx##_ratio_point##point##']
		#		}
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
			_fuse_dict = self._external_fuses(self.ppvc_fuses, False)
			# Collect data into the different fuse strings if PPVC fuses are defined and configured
			_fuse_str_compute_0 += _fuse_dict.get('compute0', [])
			_fuse_str_compute_1 += _fuse_dict.get('compute1', [])
			_fuse_str_compute_2 += _fuse_dict.get('compute2', [])
			#_fuse_str_compute_3 += _fuse_dict.get('compute3', [])
			_fuse_str_io_0 += _fuse_dict.get('io0', [])
			_fuse_str_io_1 += _fuse_dict.get('io1', [])

		if self.external_fuses:
			_fuse_dict = self._external_fuses(self.external_fuses, False)
			# Collect data into the different fuse strings if external fuses are defined and configured
			_fuse_str_compute_0 += _fuse_dict.get('compute0', [])
			_fuse_str_compute_1 += _fuse_dict.get('compute1', [])
			_fuse_str_compute_2 += _fuse_dict.get('compute2', [])
			#_fuse_str_compute_3 += _fuse_dict.get('compute3', [])
			_fuse_str_io_0 += _fuse_dict.get('io0', [])
			_fuse_str_io_1 += _fuse_dict.get('io1', [])
		#	ppvc_fuses = self.ppvc_fuses
		#	for comp in self.computes:
		#		if 'compute0' in comp.lower(): _fuse_str_compute_0 += ppvc_fuses['compute0']
		#		if 'compute1' in comp.lower(): _fuse_str_compute_1 += ppvc_fuses['compute1']
		#		if 'compute2' in comp.lower(): _fuse_str_compute_2 += ppvc_fuses['compute2']
		#	for iodie in self.ios:
		#		if 'io0' in iodie.lower(): _fuse_str_io_0 += ppvc_fuses['io0']
		#		if 'io1' in iodie.lower(): _fuse_str_io_1 += ppvc_fuses['io1']


		_fuse_str_compute_0 += _fuse_str_compute
		_fuse_str_compute_1 += _fuse_str_compute
		_fuse_str_compute_2 += _fuse_str_compute
		_fuse_str_io_0 += _fuse_str_io
		_fuse_str_io_1 += _fuse_str_io

		## Adds additional fuses to properly boot the unit in GNRSP
		if die == 'GNRSP':
			#_fuse_str_compute_0 += ["pcu.pcode_loadline_res=5"]
			#_fuse_str_compute_1 += ["pcu.pcode_loadline_res=5"]
			#_fuse_str_compute_2 += ["pcu.pcode_loadline_res=5"]
			#_fuse_str_io_0 += ["punit_iosf_sb.pcode_loadline_res=5"]
			#_fuse_str_io_1 += ["punit_iosf_sb.pcode_loadline_res=5"]
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
				#sys.exit()
			#print("********************************************************************************")
			#print (_boot_string)
			#print("********************************************************************************")
			#if (stop_after_mrc):
			#	sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=AFTER_MRC_POST
			#	print("***********************************v********************************************")
			#	print(f"sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg={AFTER_MRC_POST:#x}")
			#	print ("%s(curr_state='phase6_cpu_reset_break')" % bootcont)
			#	print("***********************************v********************************************")
			#	ipc.go()
			#	#if FastBoot: ipc.go()#bs.cont(curr_state='phase6_cpu_reset_break')
			#	#else:	ipc.go() #b.cont(curr_state='phase6_cpu_reset_break')
			#	_wait_for_post(AFTER_MRC_POST,sleeptime=20, timeout = 5)
			#else:
			#	_wait_for_post(EFI_POST, sleeptime=60)
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
			_fuse_str += self._external_fuses(self.ppvc_fuses, fast=True)
  		#	ppvc_fuses = self.ppvc_fuses
		#	for comp in self.computes:
		#		if 'compute0' in comp.lower(): _fuse_str += ppvc_fuses['compute0']
		#		if 'compute1' in comp.lower(): _fuse_str += ppvc_fuses['compute1']
		#		if 'compute2' in comp.lower(): _fuse_str += ppvc_fuses['compute2']
		#	for iodie in self.ios:
		#		if 'io0' in iodie.lower(): _fuse_str += ppvc_fuses['io0']
		#		if 'io1' in iodie.lower(): _fuse_str += ppvc_fuses['io1']

		if self.external_fuses:
			_fuse_str += self._external_fuses(self.external_fuses, fast=True)
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

	def _external_fuses(self, external_fuses, fast=True):
		_fuse_str = []
		_fuse_array = []

		_fuse_array.extend({c:[] for c in self.computes})
		_fuse_array.extend({i:[] for i in self.ios})

		_fuse_dict = {f: [] for f in _fuse_array}

		for comp in self.computes:
			if 'compute0' in comp.lower():
				_fuse_str += external_fuses['compute0']
				_fuse_dict['compute0'] += external_fuses['compute0']
			if 'compute1' in comp.lower():
				_fuse_str += external_fuses['compute1']
				_fuse_dict['compute1'] += external_fuses['compute1']
			if 'compute2' in comp.lower():
				_fuse_str += external_fuses['compute2']
				_fuse_dict['compute2'] += external_fuses['compute2']
		for iodie in self.ios:
			if 'io0' in iodie.lower():
				_fuse_str += external_fuses['io0']
				_fuse_dict['io0'] += external_fuses['io0']
			if 'io1' in iodie.lower():
				_fuse_str += external_fuses['io1']
				_fuse_dict['io1'] += external_fuses['io1']

		if fast:
			return _fuse_str
		else:
			return _fuse_dict

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

	# Prints and Checks External Fuses after unit is booted
	def external_fuses_print(self):

		if self.external_fuses:
			print(Fore.LIGHTCYAN_EX + "***********************************v********************************************")
			print(Fore.LIGHTCYAN_EX + f"{'>'*3} Checking External Fuses configured after boot")

			for key in self.external_fuses.keys():
				bsFuses =  None if self.Fastboot else key.lower()
				print(Fore.LIGHTCYAN_EX + f"{'>'*3} Checking fuses for {key.upper()} ---")
				fuse_cmd_override_check(self.external_fuses[key], showresults = True, skip_init= True, bsFuses = bsFuses)

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

## Builds the necessary arrays for Core disable Masks used in FastBoot option
def mask_fuse_core_array(coremask = {'compute0':0x0, 'compute1':0x0, 'compute2':0x0}, init = False):

	ia_masks = coremask
	ret_array=[]
	fuse_instance = FUSE_INSTANCE[0]
	base = 0xf000000000000000
	dis = 0xffffffffffffffff
	pp_num = 0
	if init: dpm.fuseRAM()
	for compute in ia_masks.keys():

		C_mask = ia_masks[compute]
		C_mask_reg=f"sv.socket0.{compute}.fuses.{fuse_instance}.ip_disable_fuses_dword6_core_disable"
		## Need to eval this
		C_mask_reg_pp0=f"sv.socket0.{compute}.fuses.pcu.pcode_sst_pp_0_core_disable_mask"
		if eval(C_mask_reg_pp0) != dis: pp_num = 1
		C_mask_reg_pp1=f"sv.socket0.{compute}.fuses.pcu.pcode_sst_pp_1_core_disable_mask"
		if eval(C_mask_reg_pp1) != dis: pp_num = 2
		C_mask_reg_pp2=f"sv.socket0.{compute}.fuses.pcu.pcode_sst_pp_2_core_disable_mask"
		if eval(C_mask_reg_pp2) != dis: pp_num = 3
		C_mask_reg_pp3=f"sv.socket0.{compute}.fuses.pcu.pcode_sst_pp_3_core_disable_mask"
		if eval(C_mask_reg_pp3) != dis: pp_num = 4
		C_mask_reg_pp4=f"sv.socket0.{compute}.fuses.pcu.pcode_sst_pp_4_core_disable_mask"
		if eval(C_mask_reg_pp4) != dis: pp_num = 5
		C_mask_reg_dts=f"sv.socket0.{compute}.fuses.pcu.pcode_disabled_module_dts_mask"
		#C0_mask=self._clear_bit(mask,compute0_core)
		ret_array.append(C_mask_reg+ "= 0x%x" % C_mask)
		#C0_mask2=self._clear_bit(mask2,compute0_core)
		if pp_num > 0: ret_array.append(C_mask_reg_pp0+ "= 0x%x" % (C_mask | base))
		if pp_num > 1: ret_array.append(C_mask_reg_pp1+ "= 0x%x" % (C_mask | base))
		if pp_num > 2: ret_array.append(C_mask_reg_pp2+ "= 0x%x" % (C_mask | base))
		if pp_num > 3: ret_array.append(C_mask_reg_pp3+ "= 0x%x" % (C_mask | base))
		if pp_num > 4: ret_array.append(C_mask_reg_pp4+ "= 0x%x" % (C_mask | base))
		ret_array.append(C_mask_reg_dts+ "= 0x%x" % C_mask)

		C_count = MAXPHYSICAL - _bitsoncount(C_mask)

		print(Fore.CYAN + f'> {compute.upper()} enabled {CORESTRING}s = {C_count}, modifying slice_en_low and high to match')


		if C_count >= 32:
			lowval = 0xffffffff
			highval = _enable_bits(C_count-32)
		else:
			lowval = _enable_bits(C_count)
			highval = 0x0

		ret_array.append(f"sv.socket0.{compute}.fuses.pcu.capid_capid8_llc_ia_core_en_low={lowval:#x}")
		ret_array.append(f"sv.socket0.{compute}.fuses.pcu.capid_capid9_llc_ia_core_en_high={highval:#x}")
		#ret_array.append(f"sv.socket0.{compute}.fuses.pcu.pcode_sst_pp_level_en_mask=0x1f")

	return(ret_array)

## Builds the necessary arrays for LLC disable Masks used in FastBoot option
def mask_fuse_llc_array(slicemask = {'compute0':0x0, 'compute1':0x0, 'compute2':0x0}):

	llc_masks = slicemask
	ret_array=[]
	fuse_instance = FUSE_INSTANCE[0]
	base = 0xf000000000000000

	for compute in llc_masks.keys():
		C_mask = llc_masks[compute]
		C_mask_reg0=f"sv.socket0.{compute}.fuses.{fuse_instance}.ip_disable_fuses_dword2_llc_disable"
		C_mask_reg1=f"sv.socket0.{compute}.fuses.{fuse_instance}.ip_disable_fuses_dword1_cha_disable"
		C_mask_reg2=f"sv.socket0.{compute}.fuses.pcu.pcode_llc_slice_disable"

		ret_array.append(C_mask_reg0+ "= 0x%x" % C_mask)
		ret_array.append(C_mask_reg1+ "= 0x%x" % C_mask)
		ret_array.append(C_mask_reg2+ "= 0x%x" % (C_mask | base))
		C_count = MAXPHYSICAL - _bitsoncount(C_mask)

		print(Fore.CYAN + f'> {compute.upper()} enabled LLC slices = {C_count}, modifying slice_en_low and high to match')

		if C_count >= 32:
			lowval = 0xffffffff
			highval = _enable_bits(C_count-32)
		else:
			lowval = _enable_bits(C_count)
			highval = 0x0

		ret_array.append(f"sv.socket0.{compute}.fuses.pcu.capid_capid6_llc_slice_en_low={lowval:#x}")
		ret_array.append(f"sv.socket0.{compute}.fuses.pcu.capid_capid7_llc_slice_en_high={highval:#x}")
		#ret_array.append(f"sv.socket0.{compute}.fuses.pcu.pcode_sst_pp_level_en_mask=0x1f")

	return(ret_array)

## FastBoot Fuse Override
def fuse_cmd_override_reset(fuse_cmd_array, skip_init=False, boot = True, s2t=False, execution_state=None):
	sv = _get_global_sv()
	ipc = ipccli.baseaccess()

	try: ipc.halt()
	except: print('>>> Not able to halt threads... skipping...')

	fuses = []
	fval = []
	# Check User Cancel Before Starting
	if check_user_cancel(execution_state):
		return

	if skip_init==False:
		#ipc.forcereconfig()
		#ipc.unlock()
		#sv.refresh()
		#cd.refresh()

		svStatus(refresh = (False if s2t else True))
		sv.sockets.ios.fuses.load_fuse_ram()
		sv.sockets.computes.fuses.load_fuse_ram()
		sv.sockets.computes.fuses.go_offline()
		sv.sockets.ios.fuses.go_offline()
	for f in (fuse_cmd_array):
		#print (f)
		base = f.split('=')[0]
		newval = f.split('=')[1]
		fuses.append(base)
		fval.append(newval)

		val=eval(base + ".get_value()")
		if isinstance(val,int):
			print(Fore.LIGHTCYAN_EX + f"> Changing --- {base} from {val:#x} --> {newval}")

		else:
			print(Fore.LIGHTCYAN_EX + f"> Changing --- {base} from {val} --> {newval}")
		exec(f)
	#sv.socket0.computes.fuses.reserved.socfusegen_reserved_lockoutid_intelhvm_row_1_bit_0 = 0x0
	#sv.socket0.ios.fuses.reserved.socfusegen_reserved_lockoutid_intelhvm_row_1_bit_0 = 0x0
	sv.sockets.ios.fuses.flush_fuse_ram()
	sv.sockets.computes.fuses.flush_fuse_ram()
	sv.sockets.computes.fuses.go_online()
	sv.sockets.ios.fuses.go_online()

	#sv.socket0.computes.fuses.reserved.socfusegen_reserved_lockoutid_intelhvm_row_1_bit_0 = 0xffffffff
	#sv.socket0.ios.fuses.reserved.socfusegen_reserved_lockoutid_intelhvm_row_1_bit_0 = 0xffffffff
	#sv.sockets.ios.fuses.flush_fuse_ram()
	#sv.sockets.computes.fuses.flush_fuse_ram()
	#sv.sockets.computes.fuses.go_online()
	#sv.sockets.ios.fuses.go_online()
	try: ipc.go()
	except: print('>>> Not able to restart threads... skipping...')
	if boot:
		print(Fore.YELLOW + '>>> Rebooting unit with ipc.resettarget()')
		ipc.resettarget()

		if not s2t:
			print(Fore.YELLOW + f'>>> Waiting for EFI... ')
			_wait_for_post(EFI_POST, sleeptime=EFI_POSTCODE_WT, timeout=EFI_POSTCODE_CHECK_COUNT, additional_postcode= LINUX_POST, execution_state=execution_state)
			fuse_cmd_override_check(fuse_cmd_array)

## Fuse Read --- Added to validate fuse application after bootscript is completed - either Fast or normal
def fuse_cmd_override_check(fuse_cmd_array, showresults = False, skip_init= False, bsFuses = None):
	sv = _get_global_sv()
	ipc = ipccli.baseaccess()
	## This part is just to complete the fuses in case they are coming from a Bootscript String


	bsf = 	{		'computes'	:'sv.sockets.computes.fuses.',
					'ios'		:'sv.sockets.ios.fuses.',
					'compute0'	:'sv.sockets.compute0.fuses.',
					'compute1'	:'sv.sockets.compute1.fuses.',
					'compute2'	:'sv.sockets.compute2.fuses.',
					'io0'		:'sv.sockets.io0.fuses.',
					'io1'		:'sv.sockets.io1.fuses.',

				}

	fuse_table = []
	All_true = True
	bserror = False
	if skip_init==False:
		#ipc.forcereconfig()
		#ipc.unlock()
		#sv.refresh()
		#cd.refresh()
		svStatus(refresh = True)
		dpm.fuseRAM()
		#sv.sockets.ios.fuses.load_fuse_ram()
		#sv.sockets.computes.fuses.load_fuse_ram()
		#sv.sockets.computes.fuses.go_offline()
		#sv.sockets.ios.fuses.go_offline()
	#if bsFuses != None:
	#	if bsFuses not in bsf.keys():
	#		#f = fuse_cmd_array
	#		print(Fore.RED +f'Die selected for bootscript not correct, use {bsf.keys()}')
	#		print(Fore.RED +'Will not perform the Fuse check invalid selection.')
	#			bserror = True
	#	else:
	#		fuse_cmd_array = [bsf[bsFuses] + _f for _f in fuse_cmd_array]
	#print(fuse_cmd_array)
	for f in (fuse_cmd_array):
		# Adds the base to each fuse to be read in system
		if bsFuses != None:
			if bsFuses not in bsf.keys():
				print(Fore.RED +f'{">"*3} Die selected for bootscript not correct, use {bsf.keys()}')
				print(Fore.RED +F'{">"*3} Will not perform the Fuse check invalid selection.')
				break
			else:
				f = bsf[bsFuses] + f

		base = f.split('=')[0]
		newval = int(f.split('=')[1],16)
		#print(f)
		#print(f, base, newval)
		val=eval(base + ".get_value()")

		if val == newval:
			check = f"{Fore.GREEN}True{Fore.WHITE}"
		else:
			check = f"{Fore.RED}False{Fore.WHITE}"
			All_true = False
			print(Fore.LIGHTMAGENTA_EX + f"> {base} -- Expected value mismatch check below table for details.")

		if isinstance(val,int):
			val = hex(val)

		fuse_table.append([base, hex(newval), val, check])

		#if isinstance(val,int):
		#	print(Fore.LIGHTCYAN_EX + f"Changing --- {base} from {val:#x} --> {newval}")

		#else:
		#	print(Fore.LIGHTCYAN_EX + f"Changing --- {base} from {val} --> {newval}")
	if bserror:
		print(f"\n{Fore.RED}{'>'*3} Fuse data not checked some error during fuse read, check fuses array{Fore.WHITE}")
	elif All_true:
		print(f"\n{Fore.GREEN}{'>'*3} All fuses changed correctly{Fore.WHITE}")
	else:
		print(f"\n{Fore.RED}{'>'*3} Some fuses did not change correctly{Fore.WHITE}")

	# Print the table
	if (not All_true or showresults) and not bserror:
		print(tabulate(fuse_table, headers=["Fuse", "Requested", "System Value", "Changed"], tablefmt="grid"))

## Bootscript Selector based on Product (AP or SP)

def gen_product_bootstring(bootopt = '', compute_cofig = 'GNRUCC', segment = 'X3' , b_extra = '', _boot_disable_ia = '', _boot_disable_llc ='',fuse_string ='',_fuse_files_compute = '', _fuse_files_io =''):

	# Future Releases will call a product_specific function here,
	chip = CHIPCONFIG.upper()

	if chip == 'SP':
		_boot_string = f'{bootopt}(fused_unit=True, enable_strap_checks=False, compute_config="{compute_cofig}", segment="{segment}", enable_pm=True {b_extra}, {_boot_disable_ia} {_boot_disable_llc} {fuse_string} fuse_files_compute=[{_fuse_files_compute}], fuse_files_io=[{_fuse_files_io}])'
		#_boot_string = ('%s(fused_unit=True, enable_strap_checks=False,enable_pm=True %s, %s %s %s fuse_files_compute=[%s], fuse_files_io=[%s])') % (bootopt, b_extra, _boot_disable_ia, _boot_disable_llc, fuse_string,_fuse_files_compute, _fuse_files_io)

	else:
		_boot_string = f'{bootopt}(fused_unit=True, enable_strap_checks=False, compute_config="{compute_cofig}", segment="{segment}", enable_pm=True {b_extra}, {_boot_disable_ia} {_boot_disable_llc} {fuse_string} fuse_files_compute=[{_fuse_files_compute}], fuse_files_io=[{_fuse_files_io}])'
		#_boot_string = ('%s(fused_unit=True, enable_strap_checks=False,compute_config="%s",enable_pm=True,segment="%s" %s, %s %s %s fuse_files_compute=[%s], fuse_files_io=[%s])') % (bootopt, compute_cofig, segment, b_extra, _boot_disable_ia, _boot_disable_llc,fuse_string,_fuse_files_compute, _fuse_files_io)

	return _boot_string

## Checks if system is unlocked and sv is updated
## The intention of this is to reduce time of execution, avoiding excessive sv refresh
def svStatus(checkipc = True, checksvcores = True, refresh = False, reconnect = False):
	from namednodes import sv
	ipc = ipccli.baseaccess()
	SysStatus = []
	ipcBad = False
	svBad = False
	svcoredara = None

	# Removing Causing Issues with threads
	#check_user_cancel(execution_state)

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
			svcores = len(sv.sockets.cpu.modules) if SELECTED_PRODUCT == 'CWF' else len(sv.sockets.cpu.cores)
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

## Checks if a Core is enabled in the system
def CheckCore(enabledCore, masks):

	target_comp = int(enabledCore / MAXPHYSICAL)

	IAC = masks[F'ia_compute_{target_comp}'].value
	updatedCore = enabledCore - MAXPHYSICAL*target_comp
	CoreStatus = _bit_check(IAC, updatedCore)

	return CoreStatus

## Checks for current system mask configuration
def CheckMasks(readfuse = True, extMasks=None):
	sv = _get_global_sv()
	die = sv.socket0.target_info["segment"].lower()

	if extMasks in [None, "None", 'Default', '', ' ']:
		masks = dpm.fuses(rdFuses = readfuse, sktnum =[0], printFuse=False)

	else:
		print(Fore.YELLOW +f' !!! Using External masking as base instead of system values' + Fore.WHITE)
		print(Fore.YELLOW +f' !!! ({type(extMasks)} : {extMasks})' + Fore.WHITE)
		masks = extMasks
	array = {	'CORES':{},
				  'LLC':{}}

	for compute in sv.socket0.computes:
		computeN = compute.instance
		_cores = masks[f'ia_compute_{computeN}'].value if extMasks == None else int(masks[f'ia_compute_{computeN}'],16)
		_slices = masks[f'llc_compute_{computeN}'].value if extMasks == None else int(masks[f'llc_compute_{computeN}'],16)

		cores = _bit_array(_cores)
		core_array = [x + ((computeN)*MAXPHYSICAL) for x in cores]

		llcs = _bit_array(_slices)
		llc_array = [x + ((computeN)*MAXPHYSICAL) for x in llcs]

		array['CORES'][compute.name] = core_array
		array['LLC'][compute.name] = llc_array

	return masks, array

## Done an improvement will be to add the IO Dies fuse config - Later - Working for single socket masks only
def coresEnabled(coreslicemask=None, logical=False, die = None, skip = False, print_cores = True, print_llcs = True, rdfuses = True):
	'''
	prints a pretty mini-tileview picture of enabled cores
	coreslicemask:core mask override
	logical: if coreslicemask should be treated as logical(default) or physical
	'''
	sv = _get_global_sv()
	if die == None:
		die = PRODUCT_CONFIG
	log_core_dis_mask = 0
	phy_core_dis_mask = 0
	max_cores = MAXCORESCHIP # Cores total
	max_cores_compute = MAXPHYSICAL # Cores per compute
	chip_config = CHIPCONFIG.upper()
	supported_dies = [k.upper() for k in CORETYPES.keys()]

	if (die not in supported_dies):

		print(f'>>> {die.upper()} not supported, please select a different one from the list: {supported_dies}')
		return

	slicemask = {}
	masks = dpm.fuses(rdFuses = rdfuses, sktnum =[0], printFuse=False)


	# Reducing this portion of Code
	#for skt in sv.sockets:

	#	sktnum = skt.name[-1]
	#	computes = skt.computes

	if coreslicemask==None:
		coreslicemask = {}
		coreslicemask = {k : v for k, v in masks.items() if v != None}

	log_core_dis_mask = {}
	phy_core_dis_mask = {}
	log_llc_dis_mask = {}
	phy_llc_dis_mask = {}
	ios_tile = sv.socket0.ios.name
	computes_tile = sv.socket0.computes.name
	skt = sv.socket0
	logicalStringCore = 0
	logicalStringLLC = 0

	chop_size = len(computes_tile)

	# use this matrix -> sv.socket._core_phy2log_matrixes['socket0'][0].cha_list[1].get_details()
	# Use as base the GNR phy2log, this can be checked later -- Need to fix this to also show current system logical if wanted, either class or system
	if skip:
		print('>>> Tileview option skipped .... ')
	else:
		print  (">>> Building Tileview for : %s" % (skt.name))
		for compute in computes_tile:
			computeN = sv.socket0.get_by_path(compute).target_info.instance
			if logical == False:
				log_core_dis_mask[compute] = (_core_dis_phy_to_log(coreslicemask[f'ia_compute_{computeN}'],computeN)) >> (MAXLOGICAL*computeN)
				phy_core_dis_mask[compute] = coreslicemask[f'ia_compute_{computeN}']
				log_llc_dis_mask[compute] = (_core_dis_phy_to_log(coreslicemask[f'llc_compute_{computeN}'],computeN)) >> (MAXLOGICAL*computeN)
				phy_llc_dis_mask[compute] = coreslicemask[f'llc_compute_{computeN}']
				logicalStringCore +=  log_core_dis_mask[compute] << (MAXLOGICAL*computeN)
				logicalStringLLC += log_llc_dis_mask[compute] << (MAXLOGICAL*computeN)
			else:
				phy_core_dis_mask[compute] = _core_dis_log_to_phy(coreslicemask[f'ia_compute_{computeN}'], computeN)
				log_core_dis_mask[compute] = coreslicemask[f'ia_compute_{computeN}']
				phy_llc_dis_mask[compute] = _core_dis_log_to_phy(coreslicemask[f'llc_compute_{computeN}'], computeN)
				log_llc_dis_mask[compute] = coreslicemask[f'llc_compute_{computeN}']

			#print  ("core disables mask: 0x%x" % (coreslicemask[f'ia_compute_{computeN}']))

		headers = []
		headers.append("R/C")
		for c in range (0,10): headers.append(f'COL{c}')
		#headers = [str(item).center(11) for item in headers]

		MDFlabel = '---- MDF ----'
		cellwith = len(MDFlabel)
		tile_io0 =[]
		tile_io1 =[]
		MDF_string  = []
		tile_computes ={'compute0':[], 'compute1':[],'compute2':[]}

		# Leaving this one here for now, not used for the moment

		cols = {'C0':[MDFlabel,0,1,'','','MC2','MC3','SPK0',MDFlabel],
				'C1':[MDFlabel,2,3,4,5,6,7,8,MDFlabel],
				'C2':[MDFlabel,9,10,11,12,13,14,15,MDFlabel],
				'C3':[MDFlabel,16,17,18,19,20,21,22,MDFlabel],
				'C4':[MDFlabel,23,24,25,26,27,28,29,MDFlabel],
				'C5':[MDFlabel,30,31,32,33,34,35,36,MDFlabel],
				'C6':[MDFlabel,37,38,39,40,41,42,43,MDFlabel],
				'C7':[MDFlabel,44,45,46,47,48,49,50,MDFlabel],
				'C8':[MDFlabel,51,52,53,54,55,56,57,MDFlabel],
				'C9':[MDFlabel,58,59,'','','MC6','MC7','SPK1',MDFlabel],
				}
		cols_num = len(cols.keys())

		for col in range(0,cols_num):
			MDF_string.append(MDFlabel)

		rows = {'R0':['ROW0'] + MDF_string,
				'R1':['ROW1'],
				'R2':['ROW2'],
				'R3':['ROW3','','4:','11:','18:','25:','32:','39:','46:','53:',''],
				'R4':['ROW4','','5:','12:','19:','26:','33:','40:','47:','54:',''],
				'R5':['ROW5','MC2','MC6'],
				'R6':['ROW6','MC3','MC7'],
				'R7':['ROW8','SPK0','SPK1'],
				'R8':['ROW8']+ MDF_string
				}
		mcs = {	'compute0':{	'C0':['CH8','CH9'] if chip_config == 'AP' else ['CH6','CH7'],
					 			'C9':['CH2','CH3']},
				'compute1':{	'C0':['CH6','CH7'] if chip_config == 'AP' else ['CH4','CH5'],
					 			'C9':['CH0','CH1']},
				'compute2':{	'C0':['CH10','CH11'],
					 			'C9':['CH4','CH5']},}
		# Config for 10x5 DIE split
		rows_num = len(rows.keys())

		cores_en_c0 = 0
		cores_en_c1 = 0
		cores_en_c2 = 0
		llc_en_c0 = 0
		llc_en_c1 = 0
		llc_en_c2 = 0
		#tile_compute1 =[]
		#tile_compute2 =[]

		t0 = coreslicemask[f'ia_compute_{0}']# & 0x7fff
		l0 = coreslicemask[f'llc_compute_{0}']
		cores_en_c0 = MAXPHYSICAL - _bitsoncount(t0)
		llc_en_c0 = MAXPHYSICAL - _bitsoncount(l0)

		if chop_size > 1:
			t1 = coreslicemask[f'ia_compute_{1}']# & 0x7fff
			l1 = coreslicemask[f'llc_compute_{1}']
			cores_en_c1 = MAXPHYSICAL - _bitsoncount(t1)
			llc_en_c1 = MAXPHYSICAL - _bitsoncount(l1)
			cores_en_c1 = MAXPHYSICAL - _bitsoncount(t1)

		if chop_size > 2:
			t2 = coreslicemask[f'ia_compute_{2}']# & 0x7fff
			l2 = coreslicemask[f'llc_compute_{2}']
			cores_en_c2 = MAXPHYSICAL - _bitsoncount(t2)
			llc_en_c2 = MAXPHYSICAL - _bitsoncount(l2)

		print  (f">>> COMPUTE0: {CORESTRING}s {cores_en_c0} enabled: 0x{t0:#x}" )
		print  (f">>> COMPUTE0: {llc_en_c0} LLCs enabled:  0x{l0:#x}")

		if chop_size > 1:
			print  (f">>> COMPUTE1: {CORESTRING}s {cores_en_c1} enabled: 0x{t1:#x}")
			print  (f">>> COMPUTE1: {llc_en_c1} LLCs enabled:  0x{l1:#x}")

		if chop_size > 2:
			print  (f">>> COMPUTE2: {CORESTRING}s {cores_en_c2} enabled: 0x{t2:#x}")
			print  (f">>> COMPUTE2: {llc_en_c2} LLCs enabled:  0x{l2:#x}")

		print  (f"\n>>> Total of {(cores_en_c0 + cores_en_c1+ cores_en_c2)} {CORESTRING} enabled on the System")
		print  (f">>> Total of {(llc_en_c0 + llc_en_c1+ llc_en_c2)} LLcs enabled on the System\n")

		ConfigTable = [['Configuration'] + [c.upper() for c in computes_tile]]
		ConfigTable.append([f'Input {CORESTRING} disabled mask'] + [('0x%x' % coreslicemask[f'ia_compute_{c.target_info.instance}'])  for c in skt.computes])
		ConfigTable.append([f'Class {CORESTRING} disabled mask' if logical== False else f'Logical {CORESTRING.lower()} disabled mask'] + [('0x%x' % log_core_dis_mask[f'{c.lower()}'])  for c in computes_tile])
		ConfigTable.append([f'Physical {CORESTRING} disabled mask'] + [('0x%x' % phy_core_dis_mask[f'{c.lower()}'])  for c in computes_tile])
		print(tabulate(ConfigTable, headers='firstrow', tablefmt='grid'))

		print  (f"\n\n>>> {CORESTRING} Tileview Map ---> physical:logical")

		if 'io0' in ios_tile:
			rows_io0 = {'R0':['ROW0','UPI0','','','PE2','','PE1','','UBOX','','UPI1'],
					'R1':['ROW1','','HC0','','','PE0','','PE3','','HC1',''],
					'R2':['ROW2'] + MDF_string}

			print('\nDIE: IO0\n')
			for key in rows_io0.keys():
				row_string = []
				for row in rows_io0[key]:
					if 'MDF' in row:
						color = Fore.YELLOW
						width = cellwith
					else:
						color = Fore.LIGHTWHITE_EX
						width = 4

					row_string.append(color + f"{row.center(width)}"+ Fore.WHITE)
				tile_io0.append(row_string)
			table = tabulate(tile_io0, headers=headers, tablefmt="grid")
			print(table)

		for compute in computes_tile:
			print (f'\nDIE: {compute.upper()}\n')
			computeN = sv.socket0.get_by_path(compute).target_info.instance
			for row in range(0,rows_num):
				row_string = [F'ROW{row}']

				for col in range(0,cols_num):
					data = cols[f'C{col}'][row]
					if type(data) == str:
						if 'MC' in data:
							if col == 0 or col == 9:
								mcdata = mcs[compute][f'C{col}']
								data = f'{data}:{(mcdata[0] if row == 5 else mcdata[1])}'
								color = Fore.LIGHTCYAN_EX
						elif 'MDF' in data: color = Fore.YELLOW
						else: color = Fore.LIGHTWHITE_EX
						row_string.append(color + data + Fore.WHITE)
					else:
						if print_cores:
							core_data = _core_string(data, phy_core_dis_mask[compute], computeN)
							tabledata = f'CORE{core_data}' if "CORE" in CORESTRING else f'MOD{core_data}'
						if print_llcs:
							llc_data = _core_string(data, phy_llc_dis_mask[compute], computeN)
							tabledata = f'CHA{llc_data}'
						if print_cores and print_llcs:
							tabledata = f'CORE {core_data}\nCHA  {llc_data}' if "CORE" in CORESTRING else f'MODULE {core_data}\nCHA    {llc_data}'
						row_string.append(tabledata)
				tile_computes[compute].append(row_string)
			table = tabulate(tile_computes[compute], headers=headers, tablefmt="grid")
			print(table)

		if 'io1' in ios_tile:
			rows_io1 = {'R0':['ROW0']+ MDF_string,
					'R1':['ROW1','','HC2','','','PE5','UPI4','','','HC3',''],
					'R2':['ROW2','UPI3','','','','UPI5','PE4','','','','UPI2']}

			print('\nDIE: IO1\n')
			#print(header)
			for key in rows_io1.keys():
				row_string = []
				for row in rows_io1[key]:
					if 'MDF' in row:
						color = Fore.YELLOW
					else: color = Fore.LIGHTWHITE_EX

					row_string.append(color + f"{row}"+ Fore.WHITE)
				tile_io1.append(row_string)
			table = tabulate(tile_io1, headers=headers, tablefmt="grid")
			print(table)

		## Prints CLASS bitstring for reference
		if not logical:
			bitstringlen = len(computes_tile)*MAXLOGICAL
			print(f'\n>>> CLASS Masking Bitstrings\n')
			print(f'>>> CLASS {CORESTRING}s Mask Bitstring: 0b{bin(logicalStringCore)[2:].zfill(bitstringlen)}')
			print(f'>>> CLASS LLCs Mask Bitstring:  0b{bin(logicalStringLLC)[2:].zfill(bitstringlen)}\n')

# We are passing Execution State to Check For Cancellations
def check_user_cancel(execution_state=None):

	if execution_state is not None:
		if execution_state.is_cancelled():
			print("S2T: Execution stopped by command", 2)
			return True
			#raise InterruptedError("SERIAL: Execution stopped")
		#time.sleep(0.5)
	return False

# Need to revisit this as we are not able to cancel during S2T
def clear_cancel_flag(logger=None,cancel_flag=False):
	pass
'''
	def check_user_cancel():
		global cancel_flag
		try:
			cancel_check = cancel_flag is not None
			if cancel_check and hasattr(cancel_flag, 'is_set'):
				if cancel_flag.is_set():
					print("S2T: Framework Execution interrupted by user...")
					raise InterruptedError('Execution Interrupted by User')
		except Exception as e:
			# Don't let cancel check break the execution
			print(f"Error checking cancel flag: {e}")

	def clear_cancel_flag(logger=None):
		global cancel_flag

		try:
			if cancel_flag is not None:
				text = "S2T: Framework Cancel Flag was set, clearing it..."
				if hasattr(cancel_flag, 'clear'):
					cancel_flag.clear()  # Clear the flag instead of setting to None
				else:
					cancel_flag = None  # Fallback if it's not a threading.Event
			else:
				text = "S2T: Framework Cancel flag not set."

			if logger:
				logger(text)
			else:
				print(text)

		except Exception as e:
			error_msg = f"Error clearing cancel flag: {e}"
			if logger:
				logger(error_msg)
			else:
				print(error_msg)
'''
###############################################################################################################################
###									Auxiliay scripts/Tools can be used indepenent of S2T flow								###
###############################################################################################################################

def read_biospost():
	print ("POST = 0x%x" % sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg)

def clear_biosbreak():
	sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=0

def go_to_efi(execution_state = None):
	print(Fore.YELLOW +'\n>>> Reenabling boot going to EFI ---\n')
	if check_user_cancel(execution_state):
		return
	svStatus()
	if (itp.ishalted() == False): itp.halt()
	clear_biosbreak() #sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=0
	if (itp.ishalted() == True): itp.go()

	_wait_for_post(EFI_POST, sleeptime=EFI_POSTCODE_WT, timeout = EFI_POSTCODE_CHECK_COUNT, additional_postcode = LINUX_POST,execution_state=execution_state)

def _wait_for_post(postcode, sleeptime = 3, timeout = 10, additional_postcode = None, execution_state=None):
	done=False
	#current_post = sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg
	current_post = read_postcode()
	PC = f'{postcode:#x}' if additional_postcode == None else f'{postcode:#x} or {additional_postcode:#x}'
	print (Fore.YELLOW + ">>> WAITING for postcode: %s <---> Current Postcode: 0x%x" % (PC, current_post)+ Fore.RESET)
	while(not done):
		time.sleep(sleeptime)
		if check_user_cancel(execution_state=execution_state):
			return
		prev_post = current_post
		current_post = read_postcode()
		#current_post = sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg

		print (Fore.YELLOW + ">>> WAITING for postcode: %s <---> Current Postcode: 0x%x" % (PC, current_post)+ Fore.RESET)
		if (prev_post == current_post):
			print (Fore.YELLOW + ">>> Executing go command: itp.go"+ Fore.RESET)
			try:
				itp.go() # Sometimes breakpoints are occurring with boot script that need a kick
			except:
				pass

		done_condition = (current_post == postcode) if additional_postcode == None else (current_post == postcode or current_post == additional_postcode)
		if (done_condition):
			done=True
		else:
			timeout-=1
			if (timeout ==0):
				print(Fore.BLACK + Back.RED + "!!!! COULD NOT REACH POSTCODE %s !!!!" % (PC) + Fore.RESET + Back.RESET )
				done=True

def read_postcode():

	try:
		pc = sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg
	except Exception as e:
		pc = None
		print(Fore.YELLOW + f">>> Unable to read PostCode with Exception: {e}"+ Fore.RESET)

	return pc

def _phy2log():
	sv = _get_global_sv()
	physical_to_logical = physical2ClassLogical

	for socket in sv.sockets:
		physical_to_logical_array = {}
		apicid_t0_to_physical_array = {}
		phy2logfullchip = {}
		for compute in socket.computes:
			skt = compute.parent.path
			compute_instance = compute.target_info.instance
			core_matrix = sv.socket._core_phy2log_matrixes[skt][compute_instance]
			for core in core_matrix.cha_list:
				if core.is_enabled:
					pid = core.global_physical
					apic_id_t0 = compute.cpu.get_by_path(f'core{pid}').thread0.ml3_cr_pic_extended_local_apic_id
					apic_id_t1 = apic_id_t0 + 1
					apicid_t0_to_physical_array[apic_id_t0] = pid
					physical_to_logical_array[pid] = core.global_logical
					phy2logfullchip[pid] = physical_to_logical[pid % 60] + (compute_instance*44)
	return physical_to_logical_array, apicid_t0_to_physical_array, phy2logfullchip

def _log2phy():
	physical_to_logical_array, apicid_t0_to_physical_array, phy2logfullchip = _phy2log()
	log2phyfullchip = {v:k for k, v in phy2logfullchip.items()}
	return log2phyfullchip

def _logical_to_physical(logCore, cinst=0):
	#print('compute instance = ',cinst)
	#physical_to_logical = classLogical2Physical
	maxlogical = MAXLOGICAL  # MAX logical cores/slices per compute
	maxphysical = MAXPHYSICAL # MAX physical cores/slices per compute
	log_to_phys = classLogical2Physical

	return int(log_to_phys[logCore % maxlogical] + cinst*maxphysical)

def _physical_to_logical(physCore, cinst=0):
	physical_to_logical = physical2ClassLogical
	maxlogical = MAXLOGICAL  # MAX logical cores/slices per compute
	maxphysical = MAXPHYSICAL # MAX physical cores/slices per compute

	return int(physical_to_logical[physCore % maxphysical] + cinst*maxlogical)

def _core_dis_phy_to_log(phy_core_dis_mask, cinst=0):
	log_core_dis = 0
	max_cores = MAXPHYSICAL # Physical MAX
	#skip = [4,5,11,12,18,19,25,26,32,33,39,40,46,47,53,54]
	for i in range(0,max_cores):
		if ((phy_core_dis_mask >> i) & 1 == 1) and i not in skip_cores_10x5:
			log_core_dis |= 1 << _physical_to_logical(i, cinst)
	return(log_core_dis)

def _core_dis_log_to_phy(log_core_dis_mask, cinst=0):
	phy_core_dis = 0
	max_cores = MAXLOGICAL # Logical MAX
	#skip = [4,5,11,12,18,19,25,26,32,33,39,40,46,47,53,54]
	#print('compute instance = ',cinst)
	for i in range(0,max_cores):
		if ((log_core_dis_mask >> i) & 1 == 1) and i not in skip_cores_10x5:
			phy_core_dis |= 1<< _logical_to_physical(i, cinst)
	return(phy_core_dis)

def _core_string(phys_core, coreslicemask, cinst):
	ret_string = ""
	maxlogical = MAXLOGICAL  # MAX logical cores/slices per compute
	maxphysical = MAXPHYSICAL # MAX physical cores/slices per compute
	if phys_core in skip_cores_10x5:
		ret_string = Fore.LIGHTBLACK_EX + "%d:-" % (phys_core + (maxphysical*cinst)) + Fore.WHITE
		#return ret_string
	else:
		log_core = _physical_to_logical(phys_core, cinst)

		if ((coreslicemask & 1<<phys_core) != 0 ): color = Fore.RED #ret_string += Fore.RED + "%d:%d" % (phys_core, log_core) + Fore.WHITE
		else: color = Fore.GREEN
		#ret_string = color + "%d:%d" % (phys_core + (maxphysical*cinst), log_core + (maxlogical*cinst)) + Fore.WHITE
		ret_string = color + "%d:%d" % (phys_core + (maxphysical*cinst), log_core ) + Fore.WHITE
	return ret_string

def _core_apic_id(core=None):
	sv = _get_global_sv()
	ipc = _get_global_ipc()
	print (Fore.YELLOW + f"Checking APIC IDs for {CORESTRING}: [ {core} ]... Please Wait..." + Fore.RESET )
	try:
		if ipc.isrunning: ipc.halt()
	except Exception as e:
		print(Fore.RED  +f'IPC Failed with Exception {e}'+ Fore.RESET)
		print(Fore.RED  + f'Unable Halt the unit, script will continue, assure there is no issue with IPC.' + Fore.RESET )

	print()
	if core == None: core = global_slice_core
	compute_index = int(core/MAXPHYSICAL)
	product = SELECTED_PRODUCT
	id0 = None
	id1 = None

	# Product Specific APIC ID Logic -- Checks for each Thread Value
	try:
		id0, id1 = pf.core_apic_id(core, compute_index, sv, id0, id1)
	except:
		print(Fore.RED  + 'Not able to collect APIC IDs Data'+ Fore.RESET)

	try:
		if ipc.ishalted: ipc.go()
	except Exception as e:
		print(Fore.RED  + f'IPC Failed with Exception {e}'+ Fore.RESET)
		print(Fore.RED  + 'Not able to take the unit out of Halt state'+ Fore.RESET)

	print (Fore.YELLOW + f"{CORESTRING}{core}: LOWER APIC: {id0} HIGHER APIC: {id1}" + Fore.RESET )

	return id0, id1

def _core_dr_registers(logger=None, mcadata = None, table = False):
	sv = _get_global_sv()
	ipc = _get_global_ipc()

	if logger == None: logger = print
	try:
		if ipc.isrunning: ipc.halt()
	except:
		logger('Fail halting Unit... Continuing..')

	try:
		logger('Reading Unit Debug Breakpoint Registers')
		dr_data, mcadata = pf.read_dr_registers(sv, ipc, logger, mcadata, table)
	except Exception as e:
		logger(f'Failed to read DR data with Exception {e}')

	if ipc.ishalted: ipc.go()

	if table: logger(tabulate(dr_data, headers="firstrow", tablefmt="grid"))

def _bitsoncount(x):
	return bin(x).count('1')

def _bitsoffcount(x, max_bit):
	return bin((x&(1<<max_bit)-1)|1<<max_bit).count('0')-1

def _set_bit(value, bit):
	if verbose: print ("_set_bit(0x%x, %d)" %(value, bit))
	return value | (1<<bit)

def _bit_check(value, bit):
	#bin_string = bin(value)
	# Convert data to be usable by script
	if isinstance(value, int):
		bin_string = (value)
	elif isinstance(value, str):
		bin_string = (int(value,16))
	else:
		raise ValueError ("Invalid input used for binary checks")
	# Check if the nth bit is set to 1
	if bin_string & (1 << bit):
		binStatus = True
	else:
		binStatus = False
	return binStatus

def _bit_array(value, bitlen = 60):
	#bin_string = value
	## Convert data to be usable by script
	if isinstance(value, int):
		bin_string = (value)
	elif isinstance(value, str):
		bin_string = (int(value,16))
	else:
		raise ValueError ("Invalid input used for binary array build")

	# Initialize an empty list to store the positions of the disabled bits
	disabled_bits = []

	 # Check each bit in the bitstring
	for n in range(bitlen):
		# If the nth bit is not set to 1, add n to the list
		if not bin_string & (1 << n):
			disabled_bits.append(n)

	return (disabled_bits)

def _set_bits(value, bits_to_set, max_bit=59):
	if verbose: print ("_set_bits(0x%x, %d, %d)" %(value, bits_to_set, max_bit))
	if (bits_to_set > max_bit):
		print ("BAD VALUE" )
		raise ValueError ("Bits higher than max limit")
	while (_bitsoncount(value) < bits_to_set):
		if verbose: print ("max_bit %d" % max_bit )
		if (((value >> max_bit) & 1) == 0):
			value = _set_bit(value,max_bit)
		max_bit -=1
	return value

def _enable_bits(n):
	# Calculate the bitmask by setting the first n bits to 1
	bitmask = (1 << n) - 1
	return bitmask

###############################################################################################################################
###									Debugging code for another option of Fastboot - Not completed							###
###############################################################################################################################

## Debugging code, to be implemented for fast boot in MESH, not available at the moment...
## FastBoot Fuse Override
def fuse_cmd_override_reset_test(fuse_cmd_array, skip_init=False, io = 0x5d, compute = 0x63, nextio = 0, nextcomp = 0, boot = True):
	_go = False
	try: itp.halt()
	except: pass
	fuse_break_nobs(io=io, compute=compute, boot = boot)
	sv = _get_global_sv()
	if skip_init==False:
		itp.forcereconfig()
		itp.unlock()
		sv.refresh()
		#cd.refresh()
		sv.sockets.ios.fuses.load_fuse_ram()
		sv.sockets.computes.fuses.load_fuse_ram()
		sv.sockets.computes.fuses.go_offline()
		sv.sockets.ios.fuses.go_offline()
	for f in (fuse_cmd_array):
		#print (f)
		base = f.split('=')[0]
		newval = f.split('=')[1]
		val=eval(base + ".get_value()")
		if isinstance(val,int):
			print(Fore.LIGHTCYAN_EX + f"Changing --- {base} from {val:#x} --> {newval}")

		else:
			print(Fore.LIGHTCYAN_EX + f"Changing --- {base} from {val} --> {newval}")
		exec(f)
	#sv.socket0.computes.fuses.reserved.socfusegen_reserved_lockoutid_intelhvm_row_1_bit_0 = 0x0
	#sv.socket0.ios.fuses.reserved.socfusegen_reserved_lockoutid_intelhvm_row_1_bit_0 = 0x0
	sv.sockets.ios.fuses.flush_fuse_ram()
	sv.sockets.computes.fuses.flush_fuse_ram()
	sv.sockets.computes.fuses.go_online()
	sv.sockets.ios.fuses.go_online()

	#sv.socket0.computes.fuses.reserved.socfusegen_reserved_lockoutid_intelhvm_row_1_bit_0 = 0xffffffff
	#sv.socket0.ios.fuses.reserved.socfusegen_reserved_lockoutid_intelhvm_row_1_bit_0 = 0xffffffff
	#sv.sockets.ios.fuses.flush_fuse_ram()
	#sv.sockets.computes.fuses.flush_fuse_ram()
	#sv.sockets.computes.fuses.go_online()
	#sv.sockets.ios.fuses.go_online()
	if nextcomp !=0 or nextio != 0:
		_go = True
	fuse_release_nobs(io = nextio, compute = nextcomp, go = _go)
	itp.go()
	#if boot: itp.resettarget()

def fuse_break(fusebreak = 'phase3_d2d_config_part1_hwrs_break'):


	#break2 = 'phase3_infra_compute_die_s3m_break'
	print(f'Starting Bootscript moving to fuse break - {fusebreak}')
	compute_config = 'x2'
	segment = 'GNRXCC'

	b.go(gotil=fusebreak, fused_unit=True, enable_strap_checks=False,compute_config=compute_config,enable_pm=True,segment=segment)

def fuse_break_nobs(io = 0x5d, compute = 0x63, boot = True):

	#import toolext.bootscript.toolbox.HWRS_utility_GNR as hwrs
	sv = _get_global_sv()
	#hwrs.set_break_point(value,die)
	#hwrs.check_breakpoint(value, die)

	fuse_override_break_io = io
	fuse_override_break_compute = compute

	itp.forcereconfig()
	itp.unlock()
	sv.refresh()

	print(Fore.YELLOW + f'\nSetting breakpoint for fuse override in break: phase3_d2d_config_part1_hwrs_break\n')

	print(Fore.YELLOW + f'Setting break for IO dies     	=== >	uncore.hwrs.gpsb.hwrs_cmd_break_on_index = {fuse_override_break_io}')
	print(Fore.YELLOW + f'Setting break for Compute dies	=== >	uncore.hwrs.gpsb.hwrs_cmd_break_on_index = {fuse_override_break_compute}')

	sv.sockets.ios.uncore.hwrs.gpsb.hwrs_cmd_break_on_index = fuse_override_break_io
	sv.sockets.computes.uncore.hwrs.gpsb.hwrs_cmd_break_on_index = fuse_override_break_compute
	sv.sockets.ios.uncore.hwrs.gpsb.hwrs_seq_control.break_on_index_valid =0x1
	sv.sockets.computes.uncore.hwrs.gpsb.hwrs_seq_control.break_on_index_valid =0x1

	if boot: itp.resettarget()

	fuse_break_check_nobs(fuse_override_break_io, fuse_override_break_compute)

def fuse_release(current = 'phase3_d2d_config_part1_hwrs_break' , next = None):

	fuse_break = current
	#_gotil = next
	if next != None:
		gotil = f',gotil = {next}'

	iofuse = sv.sockets.ios.uncore.hwrs.gpsb.hwrs_cmd_current_index.index_address.read()
	compfuse = sv.sockets.computes.uncore.hwrs.gpsb.hwrs_cmd_current_index.index_address.read()

	for io in iofuse:
		print(f'IO HWRS Break {io}')

	for comp in compfuse:
		print(f'IO HWRS Break {comp}')

	print('Continuing Bootscript ---')
	b.cont(curr_state=fuse_break)

def fuse_release_nobs(io = 0, compute = 0, go = True):
	valids = 0
	fuse_override_break_io = io
	fuse_override_break_compute = compute
	if go: valids = 1
	sv.sockets.ios.uncore.hwrs.gpsb.hwrs_cmd_break_on_index = fuse_override_break_io
	sv.sockets.computes.uncore.hwrs.gpsb.hwrs_cmd_break_on_index = fuse_override_break_compute
	sv.sockets.ios.uncore.hwrs.gpsb.hwrs_seq_control.break_on_index_valid =valids
	sv.sockets.computes.uncore.hwrs.gpsb.hwrs_seq_control.break_on_index_valid =valids

def fuse_break_check_nobs(io = 0x5d, comp = 0x63):
	print(Fore.YELLOW + 'Waiting to reach desired break for io and compute')
	fuse_override_break_io = io
	fuse_override_break_compute = comp


	#Only checking first compute and die
	io_break = sv.socket0.io0.uncore.hwrs.gpsb.hwrs_cmd_current_index.index_address.read()
	comp_break = sv.socket0.compute0.uncore.hwrs.gpsb.hwrs_cmd_current_index.index_address.read()

	print(Fore.YELLOW + f'Expected IO Breakpoint      = {fuse_override_break_io:#x}')
	print(Fore.YELLOW + f'Expected Compute Breakpoint = {fuse_override_break_compute:#x}')

	counter = 0
	retries = 10
	while (fuse_override_break_io != io_break) and (fuse_override_break_compute != comp_break):

		time.sleep(30)
		io_break = sv.sockets.ios.uncore.hwrs.gpsb.hwrs_cmd_current_index.index_address.read()
		comp_break = sv.sockets.computes.uncore.hwrs.gpsb.hwrs_cmd_current_index.index_address.read()
		counter += 1
		if counter == retries:
			print('Break not reached --- boot failed')
			break

	if counter < 10:
		print(Fore.YELLOW + f'Current IO Breakpoint reached      = {io_break}')
		print(Fore.YELLOW + f'Current Compute Breakpoint reached = {comp_break}')
	else:
		sys.exit()

