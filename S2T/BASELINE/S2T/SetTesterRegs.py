## GNR Set Tester Registers
revision = 2.0
date = '28/10/2025'
engineer ='gaespino'
##
## Version: 2.0
## MAJOR REFACTORING:
## - Introduced VoltageManager for all voltage operations
## - Introduced FrequencyManager for all frequency operations
## - Introduced ProductStrategy pattern for product-specific logic
## - Supports GNR, CWF, and DMR products seamlessly
## - DMR uses CBB structure (cbb0/1/2/3) instead of computes
## - Cleaner separation of concerns
## - Easier to extend for new products
##
## Based on SetTesterRegs.py v1.7
# Update: 27/6/2025
# Version: 1.6
# Last Update notes: Added the following features:
# - Fixed an issue with L2 voltages being applied at the same time with CFC in CWF products
# - Added DR reading to DPM logger
#
# Update: 3/6/2025
# Version: 1.5
# Last Update notes: Added the following features:
# - Code Modularity to include BASELINE of multiproducts
#
## Version: 1.4
## Last Update notes: Added the following features:
## - Voltage Configurations for mesh and slice
## 		- Vbumps (NEW)
## 		- Fixed Voltages (NEW)
## 		- ATE Configuration for Slice/Mesh -- Uses DFF Data based on VID (NEW)
##		- PPVC (Existent)
##
## - Moved Code a new Class, goal is to be able to easily use the code into Automation Tasks with NGA
## - New Features:
## 		> Configuration Save, Load and Run: Every S2T run will save configuration by default into C:\Temp folder, this configuration can be used
##			to rerun previous configurations/experiments, with no need to pass through system configuration menu of the s2t.
##			The tool comes with a gui which can be called using, s2t.Configs(), use this to load and run previous configurations.
##		> Mesh Quick Defeature Tool: Added a new UI with most common Defeature options for Mesh, it can be used by UI or by code, the usage with
## 			switches is intended for future NGA automation loops, such as Frequency defeature, voltage defeature, ...
##		> Slice Quick Defeature Tool: Same as Mesh, but with the option to select a Core to run slice content, same as above one, this is intended
##			for future inclusion of NGA Automated loops.
##
#  Update: 30/10/2024
## Version: 1.30
## Last Update notes: Added the following features:
## - Interface improvements
## - Bios knobs check option
## - PPVC Fuses option
## - Removed the user option for PCU Halt and Clear UCODE as those modes are not valid for GNR
## - APIC ID change Bug fix
## - Minor text errors in UI
## - Core registers removed as they were causing console freeze
##		91: !!!! skipping thread0.ms_cr_mbb_pppe_exe_ctl
##		92: !!!! skipping thread0.ms_cr_mbb_ucode_state
##		129: !!!! skipping thread1.ms_cr_mbb_pppe_exe_ctl
##		130: !!!! skipping thread1.ms_cr_mbb_ucode_state
## - Core registers can now be applied even if HT is disabled
## - MESH Row Masks added
## - Fuses self-check added at the end of the flow
##
## Revision: 1.2
## Date: 20/06/2024
## Edit: gabriel.espinoza.ballestero@intel.com
## update Notes: Added MLC ways selection for MESH s2t and updated the APIC id ordering script to properly work with GNR UCC.
##
## Revision: 1.1
## Date: 16/04/2024
## Edit: gabriel.espinoza.ballestero@intel.com
##
## System 2 Tester main script, contains all the necessary logic to start the system to tester loop.
## To start the script from system use.
## import users.THR.PythonScripts.thr.S2T.GNRSetTesterRegs as s2t
## s2t.setupSystemAsTester()


import namednodes
import math
import ipccli
import sys
import os
from ipccli import BitData
import json
import importlib
import os
import time
from tabulate import tabulate
from importlib import import_module

ipc = ipccli.baseaccess()
itp = ipc

sv = namednodes.sv.get_manager(["socket"])
#from common import baseaccess
sv.refresh()
verbose = False
debug = False


# Append the Main Scripts Path
MAIN_PATH = os.path.abspath(os.path.dirname(__file__))
ROOT_PATH = os.path.abspath(os.path.join(MAIN_PATH, '..'))

#MANAGERS_PATH = os.path.join(MAIN_PATH, 'managers')

## Imports from S2T Folder  -- ADD Product on Module Name for Production
sys.path.append(ROOT_PATH)

import S2T.ConfigsLoader as cfl
config = cfl.config

# Set Used product Variable -- Called by Framework
SELECTED_PRODUCT = config.SELECTED_PRODUCT
BASE_PATH = config.BASE_PATH
LEGACY_NAMING = SELECTED_PRODUCT.upper() if SELECTED_PRODUCT.upper() in ['GNR', 'CWF'] else ''
THR_NAMING = SELECTED_PRODUCT.upper() if SELECTED_PRODUCT.upper() in ['GNR', 'CWF', 'DMR'] else ''

if cfl.DEV_MODE:
	import S2T.CoreManipulation as scm
	import S2T.GetTesterCurves as stc
	import S2T.dpmChecks as dpm

	print("=" * 80)
	print(" " * 27 + "DEVELOPER MODE")
	print("=" * 80)
else:
	scm = import_module(f'{BASE_PATH}.S2T.{LEGACY_NAMING}CoreManipulation')
	stc = import_module(f'{BASE_PATH}.S2T.{LEGACY_NAMING}GetTesterCurves')
	dpm = import_module(f'{BASE_PATH}.S2T.dpmChecks{LEGACY_NAMING}')
	print("=" * 80)
	print(" " * 27 + "PRODUCTION MODE")
	print("=" * 80)


## UI Calls
import S2T.UI.System2TesterUI as UI

## Imports from THR folder - These are external scripts, always use same path
CoreDebugUtils = None
try:
	CoreDebugUtils = import_module(f'{BASE_PATH}.{THR_NAMING}CoreDebugUtils')
	print(' [+] CoreDebugUtils imported successfully')
except Exception as e:
	print(f' [x] Could not import CoreDebugUtils, some features may be limited: {e}')

## Import Managers and Strategy
import S2T.managers.voltage_manager as vmgr
import S2T.managers.frequency_manager as fmgr

## Reload of all imported scripts
if cfl.DEV_MODE:
	importlib.reload(scm)
	if CoreDebugUtils is not None:
		importlib.reload(CoreDebugUtils)
	importlib.reload(stc)
	importlib.reload(dpm)
	importlib.reload(UI)
	importlib.reload(vmgr)
	importlib.reload(fmgr)
	config.reload()

bullets = '>>>'
s2tflow = None

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== DIRECT CONFIG ACCESS (No redundant declarations) =======================================#
#========================================================================================================#

# All configuration data accessible via config.ATTRIBUTE (single source of truth from ConfigsLoader.py)
# Use config.get_functions() and config.get_registers() locally where needed

## Change Banner display based on product -- fixed for now
pf = config.get_functions()
reg = config.get_registers()
strategy = config.get_strategy()

VoltageManager = vmgr.VoltageManager
FrequencyManager = fmgr.FrequencyManager

if strategy is None:
	raise ValueError("Could not load product strategy. Check product configuration.")

pf.display_banner(revision, date, engineer)

#========================================================================================================#

## Initializes Menus based on type of product used
def init_menus(product):
	"""Initialize menus using product strategy for proper terminology."""
	menustring = strategy.get_core_string()
	domain_name = strategy.get_domain_display_name()


	Menus = {'Reset': f'\n{bullets} Reset system before starting S2T flow? Enter for [N]: ',
			'TargetCore':f'\n{bullets} Enter Target {menustring} (Physical): ',
			'CoreFreq':f'\n{bullets} Want to set {menustring} Frequency?',
			'MeshFreq':f'\n{bullets} Want to set Uncore CFC Frequency?',
			'IOFreq':f'\n{bullets} Want to set Uncore IO Frequency?',
			'DCF':f'\n{bullets} Want to set DCF Ratio?',
			'UCODE':f'\n{bullets} Clear Ucode? Y / N (enter for [N]): ',
			'PCU':f'\n{bullets} Halt PCU? Y / N (enter for [N]): ',
			'FASTBOOT':f'\n{bullets} Use FastBoot for unit restart? Y / N (enter for [Y]): ',
			'PPVC':f'\n{bullets} Do you want to set system with PPV Conditions? Y / N (enter for [N]) ',
			'MLC': f'\n{bullets} Set MLC ways? Y / N (enter for [N]): ',
			'HTDIS': f'\n{bullets} Disable Hyper Threading? Y / N (enter for [Y]): ',
			'DIS2CPM': f'\n{bullets} Disable 2 Cores Per Module? Y / N (enter for [Y]): ',
			'DIS1CPM': f'\n{bullets} Disable 1 Core Per Module? Y / N (enter for [Y]): ',
			'CLUSTER': f'\n{bullets} Fix Clustering on new mask? Y / N (enter for [Y]): ',
			'CLUSTERLSB': f'\n{bullets} Select: Fix disabling lowest slice (Y) / Fix disabling highest slice (N)? (enter for [N]): ',
			'APICS': f'\n{bullets} FIXUP APIC IDs to match tester? Y / N( enter for [N]): ',
			'BIOS': f'\n{bullets} Check BIOS knobs configuration before starting? Y / N ( enter for [N]): ',
			'ATE_Change': f'\n{bullets} Do you want to change any ATE value before moving forward? Y / N ( enter for [N]): ',
			'CoreVolt': f'\n{bullets} Do you want to set {menustring} Voltage Configuration? Y / N ( enter for [N]): ',
			'CFCVolt': f'\n{bullets} Do you want to set Uncore CFC Voltage Configuration? Y / N ( enter for [N]): ',
			'HDCVolt': f'\n{bullets} Do you want to set Uncore HDC Voltage Configuration? Y / N ( enter for [N]): ',
			'MLCVolt': f'\n{bullets} Do you want to set Core MLC Voltage Configuration? Y / N ( enter for [N]): ',
			'CFCIOVolt': f'\n{bullets} Do you want to set IO CFC Voltage Configuration? Y / N ( enter for [N]): ',
			'DDRDVolt': f'\n{bullets} Do you want to set DDRD Voltage Configuration? Y / N ( enter for [N]): ',
			'DDRAVolt': f'\n{bullets} Do you want to set DDRA Voltage Configuration? Y / N ( enter for [N]): ',
			'CoreBump': f'\n{bullets} Do you want to set {menustring} vBump Configuration? Y / N ( enter for [N]): ',
			'CFCBump': f'\n{bullets} Do you want to set Uncore CFC vBump Configuration? Y / N ( enter for [N]): ',
			'HDCBump': f'\n{bullets} Do you want to set Uncore HDC vBump Configuration? Y / N ( enter for [N]): ',
			'MLCBump': f'\n{bullets} Do you want to set Core MLC vBump Configuration? Y / N ( enter for [N]): ',
			'CFCIOBump': f'\n{bullets} Do you want to set IO CFC vBump Configuration? Y / N ( enter for [N]): ',
			'DDRDBump': f'\n{bullets} Do you want to set DDRD vBump Configuration? Y / N ( enter for [N]): ',
			'DDRABump': f'\n{bullets} Do you want to set DDRA vBump Configuration? Y / N ( enter for [N]): ',
			'vbumpfix': f'\n{bullets} Value outside of range, select a valid range (0.2V to -0.2V): ',
			'UnitVID': f'\n{bullets} Enter Unit Visual ID to get DFF Data: ',
			'u600w': f'\n{bullets} 600W QDF unit do you want to apply fuses to run in lower Power platforms? Y / N ( enter for [Y])',
			'BOOT_BREAK': f'\n{bullets} Do you want to stop the unit at a BIOS Breakdpoint? Y / N ( enter for [Y])',
			}

	return Menus, menustring

## On screen selection for System to Tester, Initial script run this to start the tool -- Newer version
def setupSystemAsTester(debug = False):
	'''
	Sets up system to be like tester using new manager architecture.
	Will ask questions on details.
	'''

	global s2tflow
	tester_mode = 0
	s2tflow = S2TFlow(debug=debug)

	print(f"\n{'='*80}")
	print(f"System 2 Tester - Product Configuration v{revision}")
	print(f"Product: {strategy.get_product_name()}")
	print(f"Core Type: {strategy.get_core_type()}")
	print(f"Domain Type: {strategy.get_domain_display_name()}")
	print(f"{'='*80}\n")

	print("Select Tester Mode:")
	print("\t1. SLICE")
	print("\t2. MESH")

	while tester_mode not in range (1,3):
		tester_mode = int(input("Enter 1-2: "))

	if tester_mode == 1:
		s2tflow.setupSliceMode()

	if tester_mode == 2:
		s2tflow.setupMeshMode()

def MeshQuickTest(core_freq = None, mesh_freq = None, vbump_core = None, vbump_mesh = None,
				  Reset = False, Mask = None, pseudo = False, dis_2CPM = None, dis_1CPM = None, GUI = True,
				  fastboot = True, corelic = None, volttype='vbump', debug= False,
				  boot_postcode = False, extMask = None, u600w=None, execution_state=None):
	"""
	Quick mesh test using new manager architecture.
	"""
	s2tTest = S2TFlow(debug=debug, execution_state=execution_state)
	product = config.SELECTED_PRODUCT
	qdf = dpm.qdf_str()

	voltage_recipes = ['ppvc']
	special_qdf = ['RVF5']

	vtype = 3 if volttype == 'vbump' else 2 if volttype == 'fixed' else 4 if volttype == 'ppvc' else 1

	# Set Default Values of non used variables
	s2tTest.check_bios = False
	s2tTest.use_ate_freq = False
	s2tTest.use_ate_volt= False
	s2tTest.dcf_ratio=None
	s2tTest.stop_after_mrc=False
	s2tTest.clear_ucode=False
	s2tTest.halt_pcu=False
	s2tTest.dis_acode=False
	s2tTest.postBootS2T=True
	s2tTest.clusterCheck = False
	s2tTest.lsb = False
	s2tTest.fix_apic=False
	s2tTest.mlcways = False
	s2tTest.reg_select = 1
	s2tTest.voltselect = 1

	# Set other variables based on input
	s2tTest.reset_start = Reset
	s2tTest.boot_postcode = boot_postcode
	s2tTest.license_level = corelic
	s2tTest.extMasks = extMask
	s2tTest.u600w = u600w if qdf in special_qdf else False
	s2tTest.fastboot = False if s2tTest.u600w == True else fastboot

	# Set quickconfig variables
	s2tTest.quick()
	s2tTest.qvbumps_core = vbump_core
	s2tTest.qvbumps_mesh = vbump_mesh

	# Init System
	s2tTest.mesh_init()

	# Build valid configs for targetTile logic
	valid_configs = {v:k for k,v in s2tTest.ate_masks.items()}
	customs = {'LeftSide': s2tTest.right_hemispthere, 'RightSide': s2tTest.left_hemispthere}
	# Get domains from strategy (computes for GNR/CWF, cbbs for DMR)
	domain_names = s2tTest.strategy.get_voltage_domains()

	# Check for Target Masking - skip configuration menus if provided
	if Mask == None:
		s2tTest.targetTile = 4
	elif Mask in valid_configs.keys():
		s2tTest.targetTile = 1
		s2tTest.target = Mask
		s2tTest.fastboot = False

	elif Mask.lower() in domain_names.keys():
		s2tTest.targetTile = 2
		s2tTest.target = Mask.lower()
		s2tTest.fastboot = False

	elif Mask in customs.keys():
		s2tTest.targetTile = 3
		s2tTest.target = 'Custom'
		s2tTest.custom_list = customs[Mask]
		s2tTest.fastboot = False

	else:
		s2tTest.targetTile = 4

	# 1CPM Configuration
	if pseudo != None:
		s2tTest.dis_ht = pseudo

	# 1CPM Configuration
	if dis_1CPM != None:
		s2tTest.dis_1CPM = dis_1CPM

	# 2CPM Configuration
	if dis_2CPM != None:
		s2tTest.dis_2CPM = dis_2CPM

	## UI Part here
	if GUI:
		UI.mesh_ui(s2tTest, product=product)
	else:
		# Frequency Conditions using FrequencyManager
		if core_freq != None:
			s2tTest.core_freq = core_freq
		if mesh_freq != None:
			s2tTest.mesh_freq = mesh_freq

		# Voltage Conditions using VoltageManager
		if vtype > 1:
			s2tTest.voltselect = vtype

		if vbump_core != None and volttype not in voltage_recipes:
			s2tTest.qvbumps_core = vbump_core

		if vbump_mesh != None and volttype not in voltage_recipes:
			s2tTest.qvbumps_mesh = vbump_mesh
		# Set voltage using manager
		s2tTest.set_voltage()

		# Run Mesh
		if not s2tTest.debug:
			s2tTest.mesh_run()

		# Save Configuration
		s2tTest.save_config(file_path=s2tTest.defaultSave)

def SliceQuickTest(Target_core = None, core_freq = None, mesh_freq = None, vbump_core = None, vbump_mesh = None, Reset = False, pseudo = False, dis_1CPM = None, dis_2CPM = None, GUI = True, fastboot = True, corelic = None,  volttype = 'fixed', debug= False, boot_postcode = False, u600w=None, execution_state=None):
	"""
	Quick slice test using new manager architecture.
	"""
	s2tTest = S2TFlow(debug=debug, execution_state=execution_state)
	product = config.SELECTED_PRODUCT
	qdf = dpm.qdf_str()

	voltage_recipes = ['ppvc']
	special_qdf = ['RVF5']

	vtype = 3 if volttype == 'vbump' else 2 if volttype == 'fixed' else 4 if volttype == 'ppvc' else 1

	# Set Default Values of non used variables
	s2tTest.check_bios = False
	s2tTest.use_ate_freq = False
	s2tTest.use_ate_volt= False
	s2tTest.dcf_ratio=None
	s2tTest.stop_after_mrc=False
	s2tTest.clear_ucode=False
	s2tTest.halt_pcu=False
	s2tTest.dis_acode=False
	s2tTest.postBootS2T=True
	s2tTest.clusterCheck = False
	s2tTest.lsb = False
	s2tTest.fix_apic=False
	s2tTest.mlcways = False
	s2tTest.reg_select = 1
	s2tTest.voltselect = 1

	# Set other variables based on input
	s2tTest.reset_start = Reset
	s2tTest.boot_postcode = boot_postcode
	s2tTest.targetLogicalCore = Target_core
	s2tTest.license_level = corelic
	s2tTest.u600w = u600w if qdf in special_qdf else False
	s2tTest.fastboot =  False if s2tTest.u600w == True else fastboot

	# Set quickconfig variables
	s2tTest.quick()


	# Init System
	s2tTest.slice_init()

	## UI Part here
	if GUI:
		UI.slice_ui(s2tTest, product=product)
	else:
		# Frequency Conditions using FrequencyManager
		if core_freq != None:
			s2tTest.core_freq = core_freq
		if mesh_freq != None:
			s2tTest.mesh_freq = mesh_freq

		# Voltage Conditions using VoltageManager
		if vtype > 1:
			s2tTest.voltselect = vtype

		if vbump_core != None and volttype not in voltage_recipes:
			s2tTest.qvbumps_core = vbump_core

		if vbump_mesh != None and volttype not in voltage_recipes:
			s2tTest.qvbumps_mesh = vbump_mesh

		# Check for Target Core
		if Target_core == None:
			s2tTest.slice_core(s2tTest.array, s2tTest.core_dict)

		# Set voltage using manager
		s2tTest.set_voltage()

		# Run Slice
		if not s2tTest.debug:
			s2tTest.slice_run()

		# Save Configuration
		s2tTest.save_config(file_path=s2tTest.defaultSave)

## Calls a User Interface to Interact with saved config files
def Configs():
	S2T = S2TFlow()
	UI.config_ui(S2T)

## Placeholders to group some of the variables, not used for the moment, but will migrate some data here later on
class VoltageSettings:
	def __init__(self, mesh_cfc_volt=None, mesh_hdc_volt=None, io_cfc_volt=None,
					ddrd_volt=None, ddra_volt=None, core_volt=None,
					ppvc_fuses = None, custom_volt = None, vbumps_volt = None, ):

		## Voltage Settings
		self.mesh_cfc = mesh_cfc_volt
		self.mesh_hdc = mesh_hdc_volt
		self.io_cfc = io_cfc_volt
		self.ddrd= ddrd_volt
		self.ddra = ddra_volt
		self.core = core_volt
		self.ppvc = ppvc_fuses
		self.custom = custom_volt
		self.vbumps = vbumps_volt
		#self.init_voltage()

class FrequencySettings():
	def __init__(self, core_freq=None, mesh_freq=None, io_freq=None):

		## Frequency Settings
		self.core = core_freq
		self.mesh = mesh_freq
		self.io = io_freq
		#self.volt_config = volt_config

## System 2 Tester Main Class -- Newer version
class S2TFlow():

	def __init__(self, 	debug = False,
						  targetLogicalCore=None,
						  targetTile=None,
						use_ate_freq = True,
						use_ate_volt= False,
						flowid=1,
						  core_freq=None,
						mesh_freq=None,
						io_freq=None,
						license_level=None,
						dcf_ratio=None,
						stop_after_mrc=False,
						boot_postcode=False,
						clear_ucode=None,
						halt_pcu=None,
						dis_acode=False,
						dis_ht = None,
						dis_2CPM = None,
						dis_1CPM = None,
						postBootS2T=True,
						clusterCheck = None,
						lsb = False,
						fix_apic=None,
						dryrun=False,
						fastboot = False,
						mlcways = None,
						ppvc_fuses = None,
						custom_volt = None,
						vbumps_volt = None,
						reset_start = None,
						check_bios = None,
						mesh_cfc_volt=None,
						mesh_hdc_volt=None,
						io_cfc_volt=None,
						ddrd_volt=None,
						ddra_volt=None,
						core_volt=None,
						core_mlc_volt=None,
						u600w=None,
						extMasks=None,
						execution_state = None):

		# Framework Execution Status
		self.execution_state = execution_state

		# Get product strategy
		self.strategy = config.get_strategy()
		if self.strategy is None:
			raise ValueError("Could not load product strategy")

		# Product information from strategy
		self.product = config.PRODUCT_CONFIG
		self.core_type = self.strategy.get_core_type()
		self.core_string = self.strategy.get_core_string()
		self.HDC_AT_CORE = self.strategy.has_hdc_at_core()
		self.MLC_AT_CORE = self.strategy.has_mlc_at_core()

		# Get voltage domains from strategy (computes or cbbs)
		self.domains = self.strategy.get_voltage_domains()
		self.domain_type = self.strategy.get_domain_display_name()

		# Initialize menus with product-specific terminology
		self.Menus, self.coremenustring = init_menus(self.product)

		# Initialize Voltage Manager
		self.voltage_mgr = VoltageManager(
			product_strategy=self.strategy,
			dpm_module=dpm,
			menus=self.Menus,
			features=config.FRAMEWORK_FEATURES
		)

		# Initialize Frequency Manager
		self.frequency_mgr = FrequencyManager(
			product_strategy=self.strategy,
			stc_module=stc,
			menus=self.Menus,
			features=config.FRAMEWORK_FEATURES
		)

		# Defined Voltage and Frequency Settings
		## Frequency Settings
		self.flowid = flowid
		self.core_freq = core_freq
		self.mesh_freq = mesh_freq
		self.io_freq = io_freq
		self.use_ate_freq = use_ate_freq

		## Voltage Settings
		self.core_volt = core_volt
		self.core_mlc_volt = core_mlc_volt
		self.mesh_cfc_volt = mesh_cfc_volt
		self.mesh_hdc_volt = mesh_hdc_volt
		self.io_cfc_volt = io_cfc_volt
		self.ddrd_volt = ddrd_volt
		self.ddra_volt = ddra_volt
		self.use_ate_volt = use_ate_volt
		self.volt_config = None

		## Script Flow
		self.mode = None
		self.external = False
		self.debug = debug

		## Common Settings
		self.dcf_ratio = dcf_ratio
		self.stop_after_mrc = stop_after_mrc
		self.boot_postcode = boot_postcode
		self.boot_postcode_break = scm.BOOT_STOP_POSTCODE
		self.clear_ucode = clear_ucode
		self.halt_pcu = halt_pcu
		self.dis_acode = dis_acode
		self.postBootS2T = postBootS2T
		self.fastboot = fastboot
		self.reset_start = reset_start
		self.check_bios = check_bios
		self.cr_array_start = 0xffff
		self.cr_array_end = 0xffff
		self.reg_select = None
		self.defaultSave = r'C:\\Temp\\System2TesterRun.json'
		self.configfile = None

		## License level
		self.license_level = license_level

		## External Base Masks
		self.extMasks = extMasks

		## Voltage Settings (maintained for compatibility, but delegated to manager)
		self.ppvc_fuses = ppvc_fuses
		self.custom_volt = custom_volt
		self.vbumps_volt = vbumps_volt
		self.voltselect = None

		# Initialize voltage dictionaries (allow float values)
		self.cfc_volt = {}  # type: dict[str, float | None]
		self.hdc_volt = {}  # type: dict[str, float | None]
		for d in self.domains:
			self.cfc_volt[d] = None
			self.hdc_volt[d] = None

		## Mesh Settings
		self.targetTile = targetTile
		self.clusterCheck = clusterCheck
		self.dis_ht = dis_ht
		self.dis_2CPM = dis_2CPM
		self.dis_1CPM = dis_1CPM
		self.lsb = lsb
		self.mlcways = mlcways

		self.custom_list = []
		self.target = ''
		self.fix_apic = fix_apic
		self.dryrun = dryrun

		self.u600w = u600w
		self.ATE_CORE_FREQ = self.frequency_mgr.ATE_CORE_FREQ
		self.ATE_MESH_FREQ = self.frequency_mgr.ATE_MESH_FREQ


		## Slice Settings
		self.targetLogicalCore = targetLogicalCore

		# Framework Features
		self.__FRAMEWORK_FEATURES = config.FRAMEWORK_FEATURES
		self.__FRAMEWORKVARS = config.FRAMEWORKVARS
		self.specific_product_features()

		# Initialize Managers with current settings
		self.init_managers()

		print(f"\n{bullets} S2TFlow initialized for {self.strategy.get_product_name()}")
		print(f"{bullets} Using {self.domain_type}s: {', '.join(self.domains)}")
		print(f"{bullets} Core terminology: {self.core_string}\n")

	# This will check based on product to disable S2T features, not all products require the same features, implemented to keep code structure
	# as similar as possible to facilitaate future updates of S2T, enabled for GNR and CWF

	def features(self):
		return self.__FRAMEWORK_FEATURES

	def variables(self):
		return self.__FRAMEWORKVARS

	def features_check(self):
		print(f'{"+"*80}')
		print(f'{bullets} System 2 Tester Notes: ')
		for F in self.__FRAMEWORK_FEATURES.keys():
			FEATURE = self.__FRAMEWORK_FEATURES[F]
			if FEATURE['enabled'] == False:
				FEATURE_VALUE = getattr(self, F)
				if FEATURE_VALUE != FEATURE['disabled_value']:
					print(f'\t> Feature: {F} not enabled for this product ({config.SELECTED_PRODUCT}).')
					setattr(self, F, FEATURE['disabled_value'])
		print(f'{"+"*80}\n')

	def specific_product_features(self):
		"""Initialize product-specific features using strategy."""

		_exit_condition(self.product, config.CORETYPES.keys(),
					   f"\n{bullets} Product not available, select a valid product...\n")

		# Check for each Feature Status
		self.features_check()

				# Populate internal variables based on product selected
		self.license_dict = config.LICENSE_S2T_MENU
		self.core_license_dict = config.LICENSE_DICT
		self.core_license_levels = config.LICENSE_LEVELS
		self.qdf600 = config.SPECIAL_QDF
		self.ate_masks = config.ATE_MASKS[config.PRODUCT_CONFIG.upper()]
		self.customs = config.CUSTOMS
		self.ate_config_main = config.ATE_CONFIG['main']
		self.ate_config_product = config.ATE_CONFIG[config.PRODUCT_CONFIG.upper()]
		self.left_hemispthere = config.LEFT_HEMISPHERE
		self.right_hemispthere = config.RIGHT_HEMISPHERE
		self.validclass = config.VALIDCLASS[config.PRODUCT_CONFIG.upper()]
		self.dis2cpm_dict = config.DIS2CPM_DICT
		self.dis1cpm_dict = config.DIS1CPM_DICT

	# Prints Menus from a dictionary, each key should be of the format l# or line# to be used
	def print_menu(self, menu):
		for l in menu.keys():
			if 'l' == l[0] or 'line' in l:
				print(menu[l])

	## Quick Defeature Tool Init
	def quick(self):
		self.qvbumps_core = None
		self.qvbumps_mesh = None
		self.external = True

	def init_managers(self):
		"""Initialize voltage and frequency managers."""

		# Pass initial frequency values to manager
		self.frequency_mgr.core_freq = self.core_freq
		self.frequency_mgr.mesh_freq = self.mesh_freq
		self.frequency_mgr.io_freq = self.io_freq
		self.frequency_mgr.use_ate_freq = self.use_ate_freq
		self.frequency_mgr.flowid = self.flowid

		# Pass initial voltage values to manager
		self.voltage_mgr.core_volt = self.core_volt
		self.voltage_mgr.mesh_cfc_volt = self.mesh_cfc_volt if self.mesh_cfc_volt else {d: None for d in self.domains}
		self.voltage_mgr.volt_config = self.volt_config

		# mesh_hdc_volt: only initialize if product supports it
		if self.voltage_mgr.voltage_ips['mesh_hdc_volt']:
			self.voltage_mgr.mesh_hdc_volt = self.mesh_hdc_volt if self.mesh_hdc_volt else {d: None for d in self.domains}
		else:
			self.voltage_mgr.mesh_hdc_volt = None  # DMR/CWF don't use mesh_hdc_volt

		# core_mlc_volt: only initialize if product supports it (DMR only)
		if self.voltage_mgr.voltage_ips['core_mlc_volt']:
			self.voltage_mgr.core_mlc_volt = None  # Will be set via voltage configuration

		self.voltage_mgr.io_cfc_volt = self.io_cfc_volt
		self.voltage_mgr.ddrd_volt = self.ddrd_volt
		self.voltage_mgr.ddra_volt = self.ddra_volt
		self.voltage_mgr.use_ate_volt = self.use_ate_volt

	#========================================================================================================#
	#=============== INITIALIZATION AND FLOW CONTROL =======================================================#
	#========================================================================================================#

	def init_flow(self):

		if self.check_bios == None and self.__FRAMEWORK_FEATURES['check_bios']['enabled']:
			self.check_bios = _yorn_bool(default_yorn='N', prompt = self.Menus['BIOS'])

		if self.check_bios:
			print (f"\n{bullets} Checking bios knobs...\n")
			dpm.bsknobs(readonly = False, skipinit = True)

		## CHecks QDF Data
		print (f"\n{bullets} Checking Unit QDF...\n")
		self.uqdf = dpm.qdf_str()
		print (f"\n{bullets} Unit QDF : {self.uqdf}...\n")

		if self.uqdf in self.qdf600:
			self.qdf600w = True
			print (f"\n{bullets} Unit QDF ({self.uqdf}) is for 600W Units, if motherboard doesn't support configuration apply fuses to boot.\n")
		else:
			self.qdf600w = False

		if self.u600w == None and self.qdf600w and self.__FRAMEWORK_FEATURES['u600w']['enabled']:
			self.u600w = _yorn_bool(default_yorn='Y', prompt = self.Menus['u600w'])
			if self.fastboot and self.u600w:
				print(f'{bullets} Fuses for 600W Unit applied, removing FastBoot option, unit will use bootscript to apply the fuses...')
				self.fastboot= False

		# Request for a clean run, this will wipe any previous configuration with a cold restart
		if self.reset_start == None and self.__FRAMEWORK_FEATURES['reset_start']['enabled']:
			self.reset_start = _yorn_bool(default_yorn='N', prompt = self.Menus['Reset'])

		if self.reset_start:
			print (f"\n{bullets} Rebooting unit please wait... \n")
			self.powercycle()

	def powercycle(self):

		if not self.u600w:
			dpm.powercycle(ports=[1,2])
		else:
			dpm.reset_600w()
			time.sleep(scm.EFI_POSTCODE_WT)

		time.sleep(scm.EFI_POSTCODE_WT)
		scm._wait_for_post(scm.EFI_POST, sleeptime=scm.EFI_POSTCODE_WT,
						   additional_postcode=scm.LINUX_POST, execution_state=self.execution_state)

		if scm.check_user_cancel(self.execution_state):
			return True

		scm.svStatus(refresh=True)

	def ate_data(self, mode='mesh'):
		"""Display ATE frequency configuration data"""
		self.frequency_mgr.display_ate_frequencies(mode=mode, core_string=self.core_string)

	#========================================================================================================#
	#=============== VOLTAGE CONFIGURATION USING VOLTAGEMANAGER ============================================#
	#========================================================================================================#

	def set_voltage(self):
		"""
		Configure voltage using VoltageManager.
		Handles all voltage options: ATE, fixed, vbumps, PPVC.
		"""

		# Configure voltage
		configured = self.voltage_mgr.configure_voltage(
			use_ate_volt=self.use_ate_volt,
			external=self.external,
			volt_select=self.voltselect,
			fastboot=self.fastboot,
			qvbumps_core=getattr(self, 'qvbumps_core', None),
			qvbumps_mesh=getattr(self, 'qvbumps_mesh', None),
			core_string=self.core_string,
			input_func=input
		)

		# Get configured values back from manager
		if configured or self.use_ate_volt:
			volt_dict = self.voltage_mgr.get_voltage_dict()
			self.volt_config = volt_dict['volt_config']
			self.custom_volt = volt_dict['custom_volt']
			self.vbumps_volt = volt_dict['vbumps_volt']
			self.ppvc_fuses = volt_dict['ppvc_fuses']

			# Update manager frequency values for use in other parts
			self.core_volt = volt_dict['core_volt']
			self.core_mlc_volt = volt_dict['core_mlc_volt']
			self.mesh_cfc_volt = volt_dict['mesh_cfc_volt']
			self.mesh_hdc_volt = volt_dict['mesh_hdc_volt']
			self.io_cfc_volt = volt_dict['io_cfc_volt']
			self.ddrd_volt = volt_dict['ddrd_volt']
			self.ddra_volt = volt_dict['ddra_volt']

			print(f"\n{bullets} Voltage configured successfully")

	#========================================================================================================#
	#=============== FREQUENCY CONFIGURATION USING FREQUENCYMANAGER ========================================#
	#========================================================================================================#

	def set_frequency(self):
		"""
		Configure frequency using FrequencyManager.
		Handles both ATE and manual frequency configuration.
		"""
		# Try ATE frequency first
		#ate_configured = self.frequency_mgr.configure_ate_frequency(
		#	mode=self.mode,
		#	core_string=self.core_string,
		#	input_func=input
		#)

		# Fall back to manual if ATE not used
		#if not ate_configured:
		self.frequency_mgr.configure_manual_frequency(input_func=input)

		# Get configured values back from manager
		freq_dict = self.frequency_mgr.get_frequency_dict()
		self.core_freq = freq_dict['core_freq']
		self.mesh_freq = freq_dict['mesh_freq']
		self.io_freq = freq_dict['io_freq']
		self.flowid = freq_dict['flowid']
		self.use_ate_freq = freq_dict['use_ate_freq']

		print(f"\n{bullets} Frequency configured:")
		print(f"  {self.core_string}: {self.core_freq}")
		print(f"  Mesh: {self.mesh_freq}")
		print(f"  IO: {self.io_freq}")

	#========================================================================================================#
	#=============== CONFIGURATION SAVE/LOAD USING MANAGERS ================================================#
	#========================================================================================================#

	def save_config(self, file_path = r'C:\\Temp\\System2TesterRun.json'):
		"""
		Save configuration including manager states.
		Now includes voltage and frequency manager dictionaries.
		"""
		config = {
			'product': self.strategy.get_product_name(),
			'mode': self.mode,
			'targetLogicalCore': self.targetLogicalCore,
			'targetTile': self.targetTile,
			'target': self.target,
			'custom_list': self.custom_list,

			# Frequency configuration from manager
			'frequency': self.frequency_mgr.get_frequency_dict(),

			# Voltage configuration from manager
			'voltage': self.voltage_mgr.get_voltage_dict(),

			# Other settings
			'license_level': self.license_level,
			'dcf_ratio': self.dcf_ratio,
			'stop_after_mrc': self.stop_after_mrc,
			'boot_postcode': self.boot_postcode,
			'clear_ucode': self.clear_ucode,
			'halt_pcu': self.halt_pcu,
			'dis_acode': self.dis_acode,
			'dis_ht': self.dis_ht,
			'dis_2CPM': self.dis_2CPM,
			'dis_1CPM': self.dis_1CPM,
			'postBootS2T': self.postBootS2T,
			'clusterCheck': self.clusterCheck,
			'lsb': self.lsb,
			'fix_apic': self.fix_apic,
			'dryrun': self.dryrun,
			'fastboot': self.fastboot,
			'mlcways': self.mlcways,
			'u600w': self.u600w,
			'masks': {k:str(v) for k,v in self.masks.items()} if hasattr(self, 'masks') and self.masks != None else None,
			'extMasks': self.extMasks
		}

		print(f'\n{bullets} Saving Configuration file to: {file_path}')
		with open(file_path, 'w') as f:
			json.dump(config, f, indent=4)

	def load_config(self, file_path = r'C:\\Temp\\System2TesterRun.json'):
		"""
		Load configuration and restore manager states.
		"""
		with open(file_path, 'r') as f:
			config_data = json.load(f)

		# Validate product matches
		if config_data.get('product') != self.strategy.get_product_name():
			print(f"\n{bullets} Warning: Config was for {config_data.get('product')}, current product is {self.strategy.get_product_name()}")

		# Restore basic settings
		self.mode = config_data.get('mode')
		self.targetLogicalCore = config_data.get('targetLogicalCore')
		self.targetTile = config_data.get('targetTile')
		self.target = config_data.get('target')
		self.custom_list = config_data.get('custom_list')

		# Restore frequency manager state
		if 'frequency' in config_data:
			self.frequency_mgr.set_from_dict(config_data['frequency'])
			freq_dict = self.frequency_mgr.get_frequency_dict()
			self.core_freq = freq_dict['core_freq']
			self.mesh_freq = freq_dict['mesh_freq']
			self.io_freq = freq_dict['io_freq']
			self.flowid = freq_dict['flowid']
			self.use_ate_freq = freq_dict['use_ate_freq']

		# Restore voltage manager state
		if 'voltage' in config_data:
			self.voltage_mgr.set_from_dict(config_data['voltage'])
			volt_dict = self.voltage_mgr.get_voltage_dict()
			self.volt_config = volt_dict['volt_config']
			self.custom_volt = volt_dict['custom_volt']
			self.vbumps_volt = volt_dict['vbumps_volt']
			self.ppvc_fuses = volt_dict['ppvc_fuses']

			# Sync voltage values to SetTesterRegs_2 attributes for set_globals()
			self.core_volt = volt_dict['core_volt']
			self.mesh_cfc_volt = volt_dict['mesh_cfc_volt']
			self.mesh_hdc_volt = volt_dict['mesh_hdc_volt']
			self.io_cfc_volt = volt_dict['io_cfc_volt']
			self.ddrd_volt = volt_dict['ddrd_volt']
			self.ddra_volt = volt_dict['ddra_volt']
			self.use_ate_volt = volt_dict['use_ate_volt']

		# Restore other settings
		self.license_level = config_data.get('license_level')
		self.dcf_ratio = config_data.get('dcf_ratio')
		self.stop_after_mrc = config_data.get('stop_after_mrc', False)
		self.boot_postcode = config_data.get('boot_postcode', False)
		self.clear_ucode = config_data.get('clear_ucode')
		self.halt_pcu = config_data.get('halt_pcu')
		self.dis_acode = config_data.get('dis_acode')
		self.dis_ht = config_data.get('dis_ht',None)
		self.dis_2CPM = config_data.get('dis_2CPM',None)
		self.dis_1CPM = config_data.get('dis_1CPM',None)
		self.postBootS2T = config_data.get('postBootS2T')
		self.clusterCheck = config_data.get('clusterCheck')
		self.lsb = config_data.get('lsb')
		self.fix_apic = config_data.get('fix_apic')
		self.dryrun = config_data.get('dryrun')
		self.fastboot = config_data.get('fastboot')
		self.mlcways = config_data.get('mlcways')
		self.u600w = config_data.get('u600w')
		self.extMasks = config_data.get('extMasks')

		masks = config_data.get('masks')
		if masks == None:
			self.masks = masks
		else:
			self.masks = {k: (lambda v: None if v == "None" else int(v, 16))(v) for k, v in masks.items()}

		self.configfile = file_path
		print(f'\n{bullets} S2T Configuration loaded from: {file_path}\n')

		# Display loaded configuration
		configtable = [["Setting", "Value"]]
		for k,v in config_data.items():
			if isinstance(v,dict):
				for d,c in v.items():
					if c != None:
						if isinstance(c,list):
							if len(c) > 5:
								str_arr = '\n'.join(map(str,c[:3]+['...']))
							else:
								str_arr = '\n'.join(map(str,c))
							configtable.append([f"{k}:{d}",str_arr])
						else:
							configtable.append([f"{k}:{d}",c])
					else:
						configtable.append([f"{k}:{d}",'N/A'])
			else:
				configtable.append([k,v if v != None else 'N/A'])

		print(f'{bullets} S2T Settings loaded:\n')
		print(f'{bullets} S2T Configuration loaded from: {self.configfile}\n')

		print(tabulate(configtable, headers="firstrow", tablefmt="grid"))

	def run_config(self, dryrun= True, file_path = r'C:\\Temp\\System2TesterRun.json'):
		"""Run configuration from file"""
		if self.u600w:
			print(f'{bullets} Unit set for 600w Configuration, removing Fastboot option...')
			self.fastboot = False

		if self.configfile == None:
			self.load_config(file_path = file_path)

		print(f'{bullets} Running System 2 Tester with Configuration loaded from: {self.configfile}\n')

		if dryrun:
			self.reset_start = True

		self.check_bios = False

		self.init_flow()

		if self.mode == 'slice':
			print(f'{bullets} Running System 2 Tester {self.mode.upper()} with Configuration loaded from: {self.configfile}\n')
			self.slice_run()
		elif self.mode == 'mesh':
			print(f'{bullets} Running System 2 Tester {self.mode.upper()} with Configuration loaded from: {self.configfile}\n')
			self.mesh_run()
		else:
			print(f'{bullets} Not a valid System 2 Tester Flow found in the configuration please check your file')

	#========================================================================================================#
	#=============== COMMON AND MISCELLANEOUS FUNCTIONS ====================================================#
	#========================================================================================================#

	def set_license(self):
		if self.license_level == None and self.__FRAMEWORK_FEATURES['license_level']['enabled']:
			print(f"\n{bullets} Select Core License Level:")
			print("\t> 0. Don't set license")
			print("\t> 1. SSE/128")
			print("\t> 2. AVX2/256 Light")
			print("\t> 3. AVX2/256 Heavy")
			print("\t> 4. AVX3/512 Light")
			print("\t> 5. AVX3/512 Heavy")
			print("\t> 6. TMUL Light")
			print("\t> 7. TMUL Heavy")

			while self.license_level not in range (0,8):
				self.license_level = int(input("--> Enter 0-7 : "))
			if self.license_level == 0: self.license_level = None

	def set_misc(self):
		print(f'\n{bullets} Clear Ucode S2T option is defaulted to [N]. This portion is not available to use.')
		print(f'\n{bullets} Halt PCU S2T option is defaulted to [N]. This portion is not available to use.')
		self.clear_ucode = False
		self.halt_pcu = False

		if self.dcf_ratio == None and self.__FRAMEWORK_FEATURES['dcf_ratio']['enabled']:
			self.dcf_ratio = _yorn_int(default_yorn ='N', prompt = self.Menus['DCF'], userin = "--> Enter DCF Ratio: ")

		if self.clear_ucode == None and self.__FRAMEWORK_FEATURES['clear_ucode']['enabled']:
			self.clear_ucode = _yorn_bool(default_yorn='N', prompt = self.Menus['UCODE'])

		if self.halt_pcu == None and self.__FRAMEWORK_FEATURES['halt_pcu']['enabled']:
			self.halt_pcu = _yorn_bool(default_yorn='N', prompt = self.Menus['PCU'])

	def set_globals(self, flow = 'core'):
		"""Set global variables for SCM module"""
		scm.reset_globals()
		scm.global_slice_core=self.targetLogicalCore
		scm.global_fixed_core_freq=self.core_freq
		scm.global_ia_turbo=self.core_freq
		scm.global_fixed_mesh_freq=self.mesh_freq
		scm.global_fixed_io_freq=self.io_freq

		# Voltages
		scm.global_fixed_core_volt=self.core_volt
		scm.global_fixed_cfc_volt=self.mesh_cfc_volt

		# mesh_hdc_volt: only set if product supports it
		if self.voltage_mgr.voltage_ips.get('mesh_hdc_volt', False):
			scm.global_fixed_hdc_volt=self.mesh_hdc_volt
		else:
			scm.global_fixed_hdc_volt=None  # DMR/CWF don't use mesh_hdc_volt

		scm.global_fixed_cfcio_volt=self.io_cfc_volt
		scm.global_fixed_ddrd_volt=self.ddrd_volt
		scm.global_fixed_ddra_volt=self.ddra_volt

		# DMR-specific: core_mlc_volt
		if self.voltage_mgr.voltage_ips.get('core_mlc_volt', False):
			scm.global_fixed_mlc_volt = self.voltage_mgr.core_mlc_volt
		else:
			scm.global_fixed_mlc_volt = None  # GNR/CWF don't use core_mlc_volt

		scm.global_avx_mode = self.license_level
		scm.global_vbumps_configuration=self.vbumps_volt
		scm.global_u600w=self.u600w
		scm.global_boot_extra=",pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=45 "

		# Flow specific
		if flow =='mesh':
			scm.global_ht_dis = self.dis_ht

		scm.global_2CPM_dis = self.dis_2CPM
		scm.global_1CPM_dis = self.dis_1CPM

		if flow =='mesh':
			scm.global_acode_dis=False
		if flow =='mesh':
			scm.global_dry_run = self.dryrun

		scm.global_acode_dis=self.dis_acode

		if self.stop_after_mrc:
			print (f"{bullets} SETTING GLOBAL STOP_AFTER_MRC")
			scm.global_boot_stop_after_mrc=True
		else:
			scm.global_boot_stop_after_mrc=False

		if self.boot_postcode:
			print (f"{bullets} SETTING GLOBAL BOOT STOP BREAKPOINT")
			scm.global_boot_postcode=True
			scm.BOOT_STOP_POSTCODE = self.boot_postcode_break
		else:
			scm.global_boot_postcode=False

	#========================================================================================================#
	#=============== SLICE MODE IMPLEMENTATION ==============================================================#
	#========================================================================================================#

	def setupSliceMode(self):
		"""Setup Slice Mode - Main entry point"""
		# Slice Mode init
		self.slice_init()

		# Core Selection Menu
		self.slice_core(array=self.array, core_dict=self.core_dict)

		# ATE Selection -- Frequency and Voltages, uses DFF for voltage, other IPS will go to safe mode
		self.slice_ate()

		# Fastboot option selection -- Moved to the start of the flow, as we need this to properly set some fuses
		if not self.u600w and self.__FRAMEWORK_FEATURES['fastboot']['enabled']:
			self.fastboot = _yorn_bool(self.Menus['FASTBOOT'],"Y")

		# Asks for license configuration
		self.set_license()

		# Asks for DCF, PCU Halt, Clear Ucode -- Clear Ucode and PCU Halt, disabled by default
		self.set_misc()

		## Registers Selection Menu
		self.slice_registers()

		# Asks for frequency changes if not configured during ATE
		self.set_frequency()

		# Asks for Voltage changes if not configured during ATE
		self.set_voltage()

		# Reboots the unit with Configuration -- In debug the script won't boot, this is mainly to check any core addition to the script
		if not self.debug:
			self.slice_run()

		# Save Configuration to Temp Folder
		self.save_config(file_path=self.defaultSave)

	def slice_init(self):
		self.mode = 'slice'

		# Initialize voltage tables with safe voltages
		self.voltage_mgr.init_voltage_tables(
			mode=self.mode,
			safe_volts_pkg=stc.All_Safe_RST_PKG,
			safe_volts_cdie=stc.All_Safe_RST_CDIE
		)

		# Expose voltstable for UI compatibility
		self.voltstable = self.voltage_mgr.voltstable

		if scm.check_user_cancel(self.execution_state):
			return

		scm.svStatus(refresh=False)

		self.init_flow()
		self.masks, self.array = scm.CheckMasks(extMasks=self.extMasks)
		self.core_dict = {f'{key}':{key: value} for key,value in self.array['CORES'].items()}

	def slice_core(self, array, core_dict):
		"""Select core for slice mode using strategy"""

		if self.targetLogicalCore == None and self.__FRAMEWORK_FEATURES['targetLogicalCore']['enabled']:
			enabledCores = []

			# Use strategy to format core table
			print(f"\n{bullets} Available {self.core_string}s:")
			printTable (core_dict, header = ['Type', 'Physical ID'],
					   label = f'Each array shows the available physical {self.core_string}s for each {self.domain_type}')

			# Build list of all available cores
			for listkeys in array['CORES'].keys():
				enabledCores.extend(array['CORES'][listkeys])

			# Loop until valid core selected
			while self.targetLogicalCore not in enabledCores:
				try:
					# Checks for Core Status in current System
					self.targetLogicalCore = int(input(self.Menus['TargetCore']))

					if self.targetLogicalCore not in enabledCores:
						print (f"\n{bullets} Selected {self.core_string} is disabled for this unit please enter a different one as per below table: \n")
						printTable (core_dict, header = ['Type', 'Physical ID'], label = f'Each array shows the available physical {self.core_string}s for each compute')
				except:
					pass

			print(f"\n{bullets} Selected {self.core_string}: {self.targetLogicalCore}")

	def slice_ate(self):
		"""
		ATE configuration for slice mode - handles both frequency and voltage.
		Uses managers for voltage and frequency configuration.
		"""

		if (self.use_ate_freq and self.__FRAMEWORK_FEATURES['use_ate_freq']['enabled']):
			yorn = ""
			yornv = ""

			print (f"\n{bullets} Want to set {self.coremenustring} Frequency via ATE frequency method?: i.e.  {self.ATE_CORE_FREQ}?")

			while "N" not in yorn and "Y" not in yorn:
				yorn = input('--> Y / N (enter for [Y]): ').upper()
				if yorn == "": yorn = "Y"

			if yorn == "Y":
				# Display ATE data using frequency manager
				self.frequency_mgr.display_ate_frequencies(mode='slice', core_string=self.core_string)

				print(f"\n{bullets} Enter Frequency:  {self.ATE_CORE_FREQ}:  ")
				ate_freq=0

				core_range = len(stc.CORE_FREQ.keys())

				while ate_freq not in range (1,(core_range + 1)):
					try:
						ate_freq = int(input(f"--> Enter 1-{core_range}: F"))
					except:
						pass

				if ate_freq > 4:
					tmp = input('--> enter FlowID (enter for [1]): ')
					if tmp == '':
						self.flowid = 1
					else:
						self.flowid = int(tmp)

				print(f'\n{bullets} ' + "FLOWID %d ate_freq %d" % ( self.flowid, ate_freq))

				# Use FrequencyManager to configure ATE frequencies
				self.frequency_mgr.configure_ate_frequency(
					mode = 'slice',
					core_string = self.core_string,
					ate_freq=ate_freq,
				)

				# Sync frequencies from manager
				self.core_freq = self.frequency_mgr.core_freq
				self.mesh_freq = self.frequency_mgr.mesh_freq
				self.io_freq = self.frequency_mgr.io_freq

				# More variability in testing conditions after selecting ATE
				print(f"\n{bullets} Setting system with ATE configuration: {self.coremenustring.upper()}: { self.core_freq}, CFCCOMP: { self.mesh_freq}, CFCIO:{ self.io_freq}")

				# ATE Voltage Selection
				print (f"\n{bullets} Want to set Voltage based on ATE Frequency selection F{ate_freq}?")

				while "N" not in yornv and "Y" not in yornv:
					yornv = input('--> Y / N (enter for [N]): ').upper()
					if yornv == "": yornv = "N"

				if yornv == "Y":

					VID = str(input(f"{self.Menus['UnitVID']}"))

					# Use VoltageManager to configure ATE voltages
					self.voltage_mgr.configure_ate_voltage_slice(
						VID=VID,
						ate_freq=ate_freq,
						target_core=self.targetLogicalCore,
						license_dict=self.core_license_dict,
						license_levels=self.core_license_levels,
						stc_module=stc,
						input_func=input,
						core_string=self.coremenustring
					)

					# Sync voltages from manager
					self.core_volt = self.voltage_mgr.core_volt
					self.core_mlc_volt = self.voltage_mgr.core_mlc_volt
					self.mesh_cfc_volt = self.voltage_mgr.mesh_cfc_volt
					self.mesh_hdc_volt = self.voltage_mgr.mesh_hdc_volt
					self.io_cfc_volt = self.voltage_mgr.io_cfc_volt
					self.ddrd_volt = self.voltage_mgr.ddrd_volt
					self.ddra_volt = self.voltage_mgr.ddra_volt
					self.use_ate_volt = self.voltage_mgr.use_ate_volt

				else:
					print(f'\n{bullets} Using System Default voltage configuration --')

				if self.core_volt:
					self.use_ate_volt = True

				ATEChange = _yorn_bool(self.Menus['ATE_Change'],"N")

				if ATEChange:

					if self.HDC_AT_CORE:
						meshf = _yorn_int(default_yorn ='N', prompt = self.Menus['MeshFreq'], userin = "--> Enter CFC Mesh Frequency: ")
					else:
						meshf = _yorn_int(default_yorn ='N', prompt = self.Menus['MeshFreq'], userin = "--> Enter CFC/HDC Mesh Frequency: ")

					#coref = _yorn_int(default_yorn ='N', prompt = self.Menus['CoreFreq'], userin = "--> Enter Core Frequency: ")
					iof = _yorn_int(default_yorn ='N', prompt = self.Menus['IOFreq'], userin = "--> Enter IO Mesh Frequency: ")

					# Update frequency manager
					self.frequency_mgr.configure_from_user_input(mesh=meshf, io=iof)

					# Sync frequencies
					self.mesh_freq = self.frequency_mgr.mesh_freq
					self.io_freq = self.frequency_mgr.io_freq

					print(f"\n{bullets} Updated configuration: {self.coremenustring.upper()}: {self.core_freq}, CFCCOMP: {self.mesh_freq}, CFCIO:{self.io_freq}")

			#return core_freq, mesh_freq, io_freq, mesh_cfc_volt, mesh_hdc_volt, io_cfc_volt, ddrd_volt, use_ate_volt

	def slice_registers(self):
		"""Register selection for slice mode"""
		if self.reg_select == None and self.__FRAMEWORK_FEATURES['use_ate_freq']['enabled']:
			print(f"\n{bullets} Set tester registers? ")
			print("\t> 1. No")
			print("\t> 2. Yes - Set all the regs")
			print("\t> 3. Yes - Set a subset of the regs")
			while self.reg_select not in range (1,4):
				reg_select = input("\n--> Enter 1-3: (enter for [2]) ")
				if reg_select == "":
					reg_select = 2
				self.reg_select = int(reg_select)

		if self.reg_select == 1:
			self.cr_array_start = 0xffff

		if self.reg_select == 2:
			self.cr_array_start = 0
			self.cr_array_end = 0xffff

		elif self.reg_select == 3:
			cr_array_start = input("\n--> start_array # (enter for [0]): ")
			if cr_array_start == "":
				cr_array_start = 0
			self.cr_array_start = int(cr_array_start)
			cr_array_end = input("--> end index # (enter for [max]): ")
			if cr_array_end == "":
				cr_array_end = 0xffff
			self.cr_array_end = int(cr_array_end)

	def slice_run(self):
		"""Run slice configuration"""
		# Global Variables configuration
		self.set_globals(flow='core')

		slice_mode = scm.System2Tester(target = self.targetLogicalCore, masks = self.masks,
									   boot=True, ht_dis=False, dis_2CPM = self.dis_2CPM,
									   dis_1CPM = self.dis_1CPM,fresh_state= False,
									   fastboot = self.fastboot, ppvc_fuses=self.volt_config,
									   execution_state = self.execution_state)

		slice_mode.setCore()

		# Will force refresh after boot to properly load all the nodes after mask changes
		if scm.check_user_cancel(self.execution_state):
			return
		scm.svStatus(refresh=True) #ipc.unlock(); ipc.forcereconfig(); sv.refresh()

		#scm.setCore(targetLogicalCore, boot=True, ht_dis=False, fresh_state= False)
		if (itp.ishalted() == False):
			try:
				itp.halt()
			except:
				print("--> Unit Can't be halted, problems with ipc...")

		if self.postBootS2T:
			try:
				set_slice(self.cr_array_start, self.cr_array_end, license_level=self.license_level,
						 core_ratio=None, mesh_ratio=None, clear_ucode=self.clear_ucode,
						 dcf_ratio=self.dcf_ratio, halt_pcu=self.halt_pcu)
			except:
				print('--> Errors ocurred applying slice configuration, skipping...')

		if (itp.ishalted() == True):
			try:
				itp.go()
			except:
				print("--> Unit go can't be issued, problems with ipc...")

		## Apply Fuse Checks for SLICE Content
		slice_mode.fuse_checks()

		# Calls overview and last refresh
		self.slice_end()

	def slice_end(self):
		print(f"\n{'='*80}")
		print(f"{bullets} Slice Mode Configuration Complete")
		print(f"{'='*80}\n")

		print (f"\n{'='*80}")
		print ("\tUnit Tileview")
		print (f"{'='*80}\n")
		scm.coresEnabled(rdfuses=False)
		print (f"\n{'='*80}")
		print ("\tConfiguration Summary")
		print (f"{'='*80}\n")
		print ("\t> Booted to physical %s: %d" % (self.coremenustring, self.targetLogicalCore))
		if self.core_freq != None: print ("\t> %s Freq = %d" % (self.coremenustring,self.core_freq))
		if self.mesh_freq != None: print ("\t> Mesh Freq = %d" % self.mesh_freq)
		if self.io_freq != None: print ("\t> IO Freq = %d" % self.io_freq)
		if self.dis_acode: print("\t> ACODE disabled")
		if self.dis_2CPM: print(f"\t> Booted with 2 Cores per Module -> Fuse Config: {self.dis_2CPM}")
		if self.dis_1CPM: print(f"\t> Booted with 1 Core per Module -> Fuse Config: {self.dis_1CPM}")
		if self.ppvc_fuses: print("\t> PPV Condition fuses set")
		if self.custom_volt: print("\t> Custom Fixed Voltage fuses set")
		if self.vbumps_volt: print("\t> Voltage Bumps fuses set")
		if self.use_ate_volt: print("\t> ATE Fixed Voltage fuses set")
		if self.core_volt != None: print ("\t> %s Volt = %f" % (self.coremenustring, self.core_volt))
		if self.core_mlc_volt != None: print (f"\t> {self.coremenustring} MLC Volt = {self.core_mlc_volt}" )
		if self.mesh_cfc_volt != None: print (f"\t> Mesh CFC Volt = {self.mesh_cfc_volt}" )
		if self.mesh_hdc_volt != None: print (f"\t> Mesh HDC Volt = {self.mesh_hdc_volt}" )
		if self.io_cfc_volt != None: print ("\t> IO CFC Volt = %f" % self.io_cfc_volt)
		if self.ddrd_volt != None: print ("\t> DDRD Volt = %f" % self.ddrd_volt)
		if self.postBootS2T:
			if self.license_level != None: print (f"\t> License level= {self.license_level} : {self.license_dict[self.license_level]}")
			if self.clear_ucode: print ("\t> Ucode patch matches were cleared")
			if self.dcf_ratio != None: print ("\t> Fixed DCF RATIO %d" % self.dcf_ratio)
			if self.halt_pcu : print ("\t> PCU halted")
			if self.cr_array_start!=0xffff:
				print ("\t> CR_ARRAY_START = %d" % self.cr_array_start)
				print ("\t> CR_ARRAY_END = %d" % self.cr_array_end)
			print(r"Rerun this config without prompt: s2t.Configs(), default save path: C:\Temp\System2TesterRun.json")
			print(f"Configuration File located at {self.defaultSave}")
			# Removing it for now
			#print("Build this configuration without prompt using: s2tconfig = s2t.S2TFlow(targetLogicalCore=%d, use_ate_freq=False, core_freq=%d, mesh_freq=%d, license_level=%d, dcf_ratio=%d, mesh_cfc_volt = %d, mesh_hdc_volt = %d, io_cfc_volt = %d, ddrd_volt = %d, core_volt = %d,)"  % (self.targetLogicalCore, self.core_freq, self.mesh_freq, self.license_level, self.dcf_ratio, self.mesh_cfc_volt, self.mesh_hdc_volt, self.io_cfc_volt, self.ddrd_volt, self.core_volt))
			#print("Run command: s2tconfig.setupSliceMode()")

		## Displays on console VVAR Configuration for selected mode
		vvars_call(slice = True, logCore=self.targetLogicalCore, corestring=self.coremenustring)
		if scm.check_user_cancel(self.execution_state):
			return
		scm.svStatus()

	#========================================================================================================#
	#=============== MESH MODE IMPLEMENTATION ==============================================================#
	#========================================================================================================#

	def setupMeshMode(self):
		"""Setup Mesh Mode - Main entry point"""
		# Mesh Mode init
		self.mesh_init()

		# ATE Selection - Frequency and Voltage (includes DFF data collection)
		self.mesh_ate()

		# Asks for mesh configuration selection: ATE Masks, Custom, Tiles
		self.mesh_configuration()

		# Fastboot option selection (To be used only in Full Chip mode to apply configuration fuses)
		if self.targetTile == 4:
			if not self.u600w and self.__FRAMEWORK_FEATURES['fastboot']['enabled']:
				self.fastboot = _yorn_bool(self.Menus['FASTBOOT'],"Y")

		# Asks for DCF, PCU Halt, Clear Ucode -- Clear Ucode and PCU Halt, disabled by default
		self.set_misc()

		## Setting of Core License, Cluster Checks, MLC Ways
		self.mesh_misc()

		## Registers Selection Menu
		self.mesh_registers()

		# Asks for frequency changes if not configured during ATE
		self.set_frequency()

		# Asks for Voltage changes if not configured during ATE
		self.set_voltage()

		# Reboots the unit with Configuration -- In debug the script won't boot, this is mainly to check any core addition to the script
		if not self.debug:
			self.mesh_run()

		# Save Configuration to Temp Folder
		self.save_config(file_path=self.defaultSave)

	def mesh_init(self):
		self.mode = 'mesh'

		# Initialize voltage tables with safe voltages
		self.voltage_mgr.init_voltage_tables(
			mode=self.mode,
			safe_volts_pkg=stc.All_Safe_RST_PKG,
			safe_volts_cdie=stc.All_Safe_RST_CDIE
		)

		# Expose voltstable for UI compatibility
		self.voltstable = self.voltage_mgr.voltstable

		if scm.check_user_cancel(self.execution_state):
			return
		scm.svStatus(refresh=False)

		self.init_flow()
		self.masks, self.array = scm.CheckMasks(extMasks=self.extMasks)

	def mesh_ate(self):
		"""
		ATE configuration for mesh mode - handles both frequency and voltage.
		Uses managers for voltage and frequency configuration.
		"""

		if (self.use_ate_freq):
			yorn = ""
			yornv = ""

			print (f"\n{bullets} Want to set CFC Frequency via ATE frequency method?: i.e. {self.ATE_MESH_FREQ}?")
			while "N" not in yorn and "Y" not in yorn:
				yorn = input('--> Y / N (enter for [Y]): ').upper()
				if yorn == "": yorn = "Y"
			if yorn == "Y":
				self.frequency_mgr.display_ate_frequencies(mode='mesh', core_string=self.core_string)

				print(f"\n{bullets} Enter Frequency: {self.ATE_MESH_FREQ} :  ")
				ate_freq=0
				mesh_range = len(stc.CFC_FREQ.keys())

				while ate_freq not in range (1,(mesh_range + 1)):
					try:
						ate_freq = int(input(f"--> Enter 1-{mesh_range}: F"))
					except:
						pass

				if ate_freq == 4:
					tmp = input('--> Enter FlowID (enter for [1]): ')
					if tmp == '':
						self.flowid = 1
					else:
						self.flowid = int(tmp)


				print(f"\n{bullets} FLOWID %d ate_freq %d" % ( self.flowid, ate_freq))

				# Use FrequencyManager to configure ATE frequencies
				self.frequency_mgr.configure_ate_frequency(
					mode = 'mesh',
					core_string = self.core_string,
					ate_freq=ate_freq,
				)

				# Sync frequencies from manager
				self.core_freq = self.frequency_mgr.core_freq
				self.mesh_freq = self.frequency_mgr.mesh_freq
				self.io_freq = self.frequency_mgr.io_freq

				print(f"\n{bullets} Setting system with ATE configuration: {self.coremenustring}: { self.core_freq}, CFCCOMP: { self.mesh_freq}, CFCIO:{ self.io_freq}")

				#if (use_ate_volt):
				print (f"\n{bullets} Want to set Voltage based on ATE Frequency selection F{ate_freq}?")

				while "N" not in yornv and "Y" not in yornv:
					yornv = input('--> Y / N (enter for [N]): ').upper()
					if yornv == "": yornv = "N"

				if yornv == "Y":

					VID = str(input(f"{self.Menus['UnitVID']}"))

					# Use VoltageManager to configure ATE voltages
					self.voltage_mgr.configure_ate_voltage_mesh(
						VID=VID,
						ate_freq=ate_freq,
						stc_module=stc,
						input_func=input,
						core_string=self.coremenustring
					)

					# Sync voltages from manager
					self.core_volt = self.voltage_mgr.core_volt
					self.mesh_cfc_volt = self.voltage_mgr.mesh_cfc_volt
					self.mesh_hdc_volt = self.voltage_mgr.mesh_hdc_volt
					self.io_cfc_volt = self.voltage_mgr.io_cfc_volt
					self.ddrd_volt = self.voltage_mgr.ddrd_volt
					self.ddra_volt = self.voltage_mgr.ddra_volt
					self.use_ate_volt = self.voltage_mgr.use_ate_volt

				else:
					print(f'\n{bullets} Using System Default voltage configuration --')

				if self.mesh_cfc_volt:
					self.use_ate_volt = True

				# Allow changes after ATE selection
				ATEChange = _yorn_bool(self.Menus['ATE_Change'],"N")

				if ATEChange:

					coref = _yorn_int(default_yorn ='N', prompt = self.Menus['CoreFreq'], userin = f"--> Enter {self.coremenustring} Frequency: ")
					iof = _yorn_int(default_yorn ='N', prompt = self.Menus['IOFreq'], userin = "--> Enter IO Mesh Frequency: ")

					# Update frequency manager
					self.frequency_mgr.configure_from_user_input(core=coref, io=iof)

					# Update frequency manager
					self.core_freq = self.frequency_mgr.core_freq
					self.io_freq = self.frequency_mgr.io_freq

					print(f"\n{bullets} Updated configuration: {self.coremenustring.upper()}: { self.core_freq}, CFCCOMP: { self.mesh_freq}, CFCIO:{ self.io_freq}")

	def mesh_configuration(self):
		"""Mask selection for mesh mode"""
		ate_mask = 0

		# Get Available Domains (Compute / CBB) --
		domains = self.strategy.get_voltage_domains()

		print(f'\n{bullets} System 2 Tester MESH Available Configurations: ')
		self.print_menu(menu=self.ate_config_main)

		# Get user selection
		maxrng = self.ate_config_product['maxrng']

		if self.targetTile == None:
			self.targetTile = int(input("--> Enter Configuration: "))

			while self.targetTile not in range(1, maxrng):
				try:
					self.targetTile = int(input(f"--> Enter 1-{maxrng-1}: "))
				except:
					pass

		if self.targetTile == 1:
			print(f'\n{bullets} Enter ATE Class mask configuration:')
			self.print_menu(menu=self.ate_config_product)
			maxrng = self.ate_config_product['maxrng']

			while ate_mask not in range (1,maxrng):
				ate_config = ''
				try:
					ate_mask = int(input("--> ATE Pass mask to be used: "))
					ate_config = self.ate_masks[ate_mask]
				except:
					pass
				print(f'--> System 2 Tester Configured in ATE Mode: {ate_config.upper()}')
				self.target = ate_config

		# Need to check how to user input a list
		elif self.targetTile == 2:
			# Tile Isolation
			invalid = True
			domain_list = []
			print(f"\n{bullets} {self.domain_type} Isolation:")
			for idx, domain in enumerate(domains, 1):
				print(f"\t> {idx}. {domain.upper()}")

			while invalid:
				input_str = str(input(f"--> Enter {self.domain_type.upper()}(s) name splitted by comma: "))
				domain_list = input_str.lower().strip(' ').split(',')
				invalid = [val for val in domain_list if val not in domains]
				if invalid:
					print(f'--> Not valid values entered please check: {invalid}')
			print(f'--> System 2 Tester Configured in {self.domain_type} Isolation Mode: {domain_list}')
			self.target = domain_list


		## Check for the Custom configuration in X2
		elif self.targetTile == 3:
			invalid = True
			self.target = 'Custom'
			print(f'\n{bullets} Valid input values for Custom mode are: {self.customs}')
			while invalid:
				input_str = str(input("--> Enter Column(s)/Row(s) name splitted by comma:"))
				self.custom_list = input_str.upper().strip(' ').split(',')

				invalid = [val for val in self.custom_list if val not in self.customs]
				if invalid:
					print(f'--> Not valid values entered please check: {invalid}')

			print(f'--> System 2 Tester Configured in Custom Mode: {self.custom_list}')

		elif self.targetTile == 4:
			# Full Chip
			print(f'--> System 2 Tester Configured in Full Chip Mode')
			self.target = 'FULLCHIP'

	def mesh_misc(self):
		"""
		Mesh miscellaneous settings.
		Handles mlcways, dis_ht, dis_2CPM, fix_apic, boot_postcode, clusterCheck, and license_level.
		Uses targetTile to determine appropriate defaults.
		"""
		if self.mlcways == None and self.__FRAMEWORK_FEATURES['mlcways']['enabled']:
			self.mlcways = _yorn_bool(self.Menus['MLC'],"N")

		if self.dis_ht == None and self.__FRAMEWORK_FEATURES['dis_ht']['enabled']:
			default_ht = "Y" if self.targetTile != 4 else "N"
			self.dis_ht = _yorn_bool(self.Menus['HTDIS'],default_ht)

		if self.dis_2CPM == None and self.__FRAMEWORK_FEATURES['dis_2CPM']['enabled']:
			default_2cpm = "Y" if self.targetTile != 4 else "N"
			_dis_2cpm = _yorn_bool(self.Menus['DIS2CPM'],default_2cpm)
			if _dis_2cpm:
				self.dis2CPM()

		if self.dis_1CPM == None and self.__FRAMEWORK_FEATURES['dis_1CPM']['enabled']:
			default_1cpm = "Y" if self.targetTile != 4 else "N"
			_dis_1cpm = _yorn_bool(self.Menus['DIS1CPM'],default_1cpm)
			if _dis_1cpm:
				self.dis1CPM()

		if self.fix_apic == None and self.__FRAMEWORK_FEATURES['fix_apic']['enabled']:
			self.fix_apic = _yorn_bool(self.Menus['APICS'],"N")
			if self.fix_apic:
				self.stop_after_mrc = True

		if self.boot_postcode == None and self.__FRAMEWORK_FEATURES['boot_postcode']['enabled']:
			self.boot_postcode_break = _yorn_int(default_yorn ='N',
										prompt = self.Menus['BOOT_BREAK'],
										userin = "--> Enter Hex Value of Breakpoint: ")
			if self.boot_postcode_break != None:
				self.boot_postcode = True

		# Cluster check only for ATE configuration (targetTile == 1)
		if self.clusterCheck == None and self.targetTile == 1 and self.__FRAMEWORK_FEATURES['clusterCheck']['enabled']:
			self.clusterCheck = _yorn_bool(self.Menus['CLUSTER'],"Y")
			if self.clusterCheck:
				self.lsb = _yorn_bool(self.Menus['CLUSTERLSB'],"N")

		## Check License level
		if self.license_level == None and self.__FRAMEWORK_FEATURES['license_level']['enabled']:
			LicenseCheck = _yorn_bool(f'\n{bullets} Select {self.coremenustring} License level Y / N (enter for [N]): ',"N")
			if LicenseCheck:
				self.set_license()

	def dis2CPM(self):
		_2cpm = 0
		print(f'\n{bullets} Select Cores to disabled:')
		self.print_menu(menu=config.DIS2CPM_MENU['main'])
		maxrng = config.DIS2CPM_MENU['main']['maxrng']

		while _2cpm not in range (1,maxrng):
			_2cpm = ''
			try:
				_2cpm = int(input("--> Core disable selection to be used: "))
				self.dis_2CPM = self.dis2cpm_dict[_2cpm]
			except:
				pass

	def dis1CPM(self):
		_1cpm = 0
		print(f'\n{bullets} Select Cores to disabled:')
		self.print_menu(menu=config.DIS1CPM_MENU['main'])
		maxrng = config.DIS1CPM_MENU['main']['maxrng']

		while _1cpm not in range (1,maxrng):
			_1cpm = ''
			try:
				_1cpm = int(input("--> Core disable selection to be used: "))
				self.dis_1CPM = self.dis1cpm_dict[_1cpm]
			except:
				pass

	def mesh_registers(self):
		"""
		Register selection for mesh mode.
		Allows setting all registers, subset, or none.
		"""
		if self.reg_select == None and self.__FRAMEWORK_FEATURES['reg_select']['enabled']:

			print(f"\n{bullets} Set tester registers? ")
			print("\t> 1. No")
			print("\t> 2. Yes - Set all the regs")
			print("\t> 3. Yes - Set a subset of the regs")

			# Disabled by default
			print(f'\n{bullets} Mesh registers disabled by default, option not availble for now.')
			self.reg_select = 1

			while self.reg_select not in range (1,3):
				reg_select = input("\n--> Enter 1-3: (enter for [1]) \n Select default of [1], do not use press enter to continue.")
				if reg_select == "":
					reg_select = 1
				self.reg_select = int(reg_select)

		if self.reg_select == 1:
			self.cr_array_start = 0xffff

		if self.reg_select == 2:
			self.cr_array_start = 0
			self.cr_array_end = 0xffff

		elif self.reg_select == 3:
			cr_array_start = input("\n--> Start_array # (enter for [0]): ")
			if cr_array_start == "":
				self.cr_array_start = 0
			self.cr_array_start = int(cr_array_start)

			cr_array_end = input("--> End index # (enter for [max]): ")
			if cr_array_end == "":
				self.cr_array_end = 0xffff
			self.cr_array_end = int(cr_array_end)

	def mesh_run(self):

		#Set Globals before calling the S2T Script flow
		self.set_globals(flow='mesh')

		# Call the appropriate script based on the selected mode
		mesh = scm.System2Tester(target=self.target, masks=self.masks, boot=True,
						   				ht_dis=self.dis_ht, dis_2CPM=self.dis_2CPM,
										dis_1CPM=self.dis_1CPM, fresh_state=False, readFuse=True,
										fastboot=self.fastboot, ppvc_fuses=self.volt_config,
										execution_state=self.execution_state)

		# Call different methods based on targetTile
		# ATE Configuration
		if self.targetTile == 1:
			mesh.setmesh(boot_postcode=self.boot_postcode,stop_after_mrc=self.stop_after_mrc, lsb = self.lsb, extMasks=self.extMasks)

		 # Tile Isolation
		elif self.targetTile == 2:
			mesh.setTile(boot_postcode=self.boot_postcode,stop_after_mrc=self.stop_after_mrc)

		# Custom Configuration
		elif self.targetTile == 3:
			mesh.setmesh(CustomConfig = self.custom_list, boot_postcode=self.boot_postcode,stop_after_mrc=self.stop_after_mrc, lsb = self.lsb, extMasks=self.extMasks)

		# Full Chip
		elif self.targetTile == 4:
			mesh.setfc(extMasks = self.extMasks, boot_postcode=self.boot_postcode,stop_after_mrc=self.stop_after_mrc)

		# Force refresh after boot
		if scm.check_user_cancel(self.execution_state):
			return
		scm.svStatus(refresh=True) # ipc.unlock(); ipc.forcereconfig(); sv.refresh()

		if (itp.ishalted() == False):
			try:
				itp.halt()
			except:
				print("--> Unit Can't be halted, problems with ipc...")

		if self.fix_apic:
			#print('\n --- Continuing boot moving EFI ---\n')
			tester_apic_id()
			scm.go_to_efi(self.execution_state)

		# Post-boot S2T configuration
		if self.postBootS2T:
			try:
				set_mesh(self.cr_array_start, self.cr_array_end,
			 					license_level=self.license_level, core_ratio=None, mesh_ratio=None,
								reorder_apic=False, clear_ucode=self.clear_ucode,
								dcf_ratio=self.dcf_ratio, halt_pcu=self.halt_pcu,
								mlcways=self.mlcways)
			except:
				print('--> Errors ocurred applying mesh configuration, skipping...')

		if (itp.ishalted() == True):
			try:
				itp.go()
			except:
				print("--> Unit go can't be issued, problems with ipc...")

		## Apply Fuse Checks for MESH Content
		mesh.fuse_checks()

		self.mesh_end()

	def mesh_end(self):
		"""Finalize mesh mode"""
		print(f"\n{'='*80}")
		print(f"{bullets} Mesh Mode Configuration Complete")
		print(f"{'='*80}\n")

		print (f"\n{'='*80}")
		print ("\tUnit Tileview")
		print (f"{'='*80}\n")
		scm.coresEnabled(rdfuses=False)
		print (f"\n{'='*80}")
		print ("\tConfiguration Summary")
		print (f"{'='*80}\n")
		print ("\t> Unit Booted using pseudo configuration: %s" % self.target)
		if self.core_freq != None: print ("\t> %s Freq = %d" % (self.coremenustring, self.core_freq))
		if self.mesh_freq != None: print ("\t> Mesh Freq = %d" % self.mesh_freq)
		if self.io_freq != None: print ("\t> IO Freq = %d" % self.io_freq)
		if self.dis_acode: print("\t> ACODE disabled")
		if self.dis_ht: print("\t> Hyper Threading disabled")
		if self.dis_2CPM: print(f"\t> Booted with 2 Cores per Module -> Fuse Config: {self.dis_2CPM}")
		if self.dis_1CPM: print(f"\t> Booted with 1 Core per Module -> Fuse Config: {self.dis_1CPM}")
		if self.ppvc_fuses: print("\t> PPV Condition fuses set")
		if self.custom_volt: print("\t> Custom Fixed Voltage fuses set")
		if self.vbumps_volt: print("\t> Voltage Bumps fuses set")
		if self.use_ate_volt: print("\t> ATE Fixed Voltage fuses set")
		if self.core_volt != None: print ("\t> %s Volt = %f" % (self.coremenustring,self.core_volt))
		if self.mesh_cfc_volt != None: print (f"\t> Mesh CFC Volt = {self.mesh_cfc_volt}" )
		if self.mesh_hdc_volt != None: print (f"\t> Mesh HDC Volt = {self.mesh_hdc_volt}" )
		if self.io_cfc_volt != None: print ("\t> IO CFC Volt = %f" % self.io_cfc_volt)
		if self.ddrd_volt != None: print ("\t> DDRD Volt = %f" % self.ddrd_volt)
		if self.postBootS2T:
			if self.license_level != None: print (f"\t> License level= {self.license_level} : {self.license_dict[self.license_level]}")
			if self.clear_ucode: print ("\t> Ucode patch matches were cleared")
			if self.dcf_ratio != None: print ("\t> Fixed DCF RATIO %d" % self.dcf_ratio)
			if self.halt_pcu : print ("\t> PCU halted")
			if self.cr_array_start!=0xffff:
				print ("\t> CR_ARRAY_START = %d" % self.cr_array_start)
				print ("\t> CR_ARRAY_END = %d" % self.cr_array_end)
			print(r"Rerun this config without prompt: s2t.Configs(), default save path: C:\Temp\System2TesterRun.json")
			print(f"Configuration File located at {self.defaultSave}")
			#print("Rerun this config without prompt: s2t.setupSliceMode(targetLogicalCore=%d, use_ate_freq=False, core_freq=%d, mesh_freq=%d, license_level=%d, dcf_ratio=%d)"  % (targetLogicalCore, core_freq, mesh_freq, license_level, dcf_ratio))

		vvars_call(slice = False, logCore=None, corestring=self.coremenustring)
		if scm.check_user_cancel(self.execution_state):
			return
		scm.svStatus()


#========================================================================================================#
#=============== HELPER FUNCTIONS ======================================================================#
#========================================================================================================#

## PM Mode need to revisit at some point -- Will add this to the Class once implemented
def setupMeshPMMode(target_tile = None, pm_default=None):
	if target_tile == None: target_tile = int(input("Enter Tile: "))
	if pm_default == None:
		print("  Do you want PM defaults? ")
		print("\t1. Default: IA_P0=32, IA_P1=32, IA_PN=8, IA_PN=8,  CFC_P0=20, CFC_P1=20, CFC_PN=8, CFC_MIN=8")
		print("\tHT_ENABLED,  UCODE CLEARED, APIC ID FIXED , MLC WAYMASK=2")
		print("\t2. NO_VF")
		#pm_default = _yorn("PM DEFAULTS? Y or N (enter for Y)? ","Y")
		while pm_default not in range (1,3):
			pm_default = input("Enter 1-2: (enter for 1) ")
			if pm_default == "":
				pm_default = 1
			pm_default = int(pm_default)
	if pm_default == 1:
		scm.global_ia_p0=32
		scm.global_ia_p1=32
		scm.global_ia_pn=8
		scm.global_ia_pm=8
		scm.global_cfc_p0=20
		scm.global_cfc_p1=20
		scm.global_cfc_pn=8
		scm.global_cfc_pm=8
		scm.global_boot_stop_after_mrc=True
		scm.setTile(target_tile, ht_dis=False, stop_after_mrc=True, fresh_state=False)

		# should be waiting after MRC
		scm.read_biospost()
		tester_apic_id()
		scm.go_to_efi()
		scm.read_biospost()
		# CoreDebugUtils.set_mlc_waymask(mesh_tester = True )
		# TODO: Add tester regs?
	elif pm_default == 2:
		scm.setTile(target_tile, ht_dis=False, stop_after_mrc=True, fresh_state=False,pm_enable_no_vf=True)
		# should be waiting after MRC
		scm.read_biospost()
		tester_apic_id()
		scm.go_to_efi()
		scm.read_biospost()
	else:
		setupMeshMode(targetTile=target_tile, clear_ucode=False, halt_pcu=False)

def reboot_pm():
	sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=scm.AFTER_MRC_POST
	itp.resettarget()
	scm._wait_for_post(scm.AFTER_MRC_POST)
	tester_apic_id()
	scm.go_to_efi()
	#CoreDebugUtils.set_mlc_waymask(mesh_tester = True)

## Prints VVAR default configuration
def vvars_call(slice = True, logCore=None, corestring = 'CORE'):
	# GNR / CWF
	VVAR2_DEFAULT = 0x1000002 if corestring == 'CORE' else 0x1000004 # 2 Threads

	if slice:
		targetLogicalCore = logCore
		try:
			apic_0, apic_1 = scm._core_apic_id(core = logCore)
		except:
			print('!!! Error Collecting APIC IDs Data --')
			apic_0 = None
			apic_1 = None

		vvars = {	0:0x04C4B40,
					1:0x80064000,
					2:VVAR2_DEFAULT,
					3:0x10000,
					4:apic_0,
					5:apic_1}

		print ("\n----------------------------------------------------------------")
		print(f'\n{bullets} To run slice content for selected {corestring}{targetLogicalCore}')
		print(f'{bullets} Use the following VVARs:')
		print(f'\t> VVAR0 = {vvars[0]:#x}  ---> Runtime Execution default = 5s (x timing)')
		print(f'\t> VVAR1 = {vvars[1]:#x}  ---> Optional Base timing / multiplying factor of VVAR0')
		print(f'\t> VVAR2 = {vvars[2]:#x}  ---> Running Threads = 2')
		print(f'\t> VVAR3 = {vvars[3]:#x}  ---> PM option disabled')
		if vvars[4] != None: print(f'\t> VVAR4 = {vvars[4]:#x}  ---> APIC ID for {corestring}{targetLogicalCore} thread0')
		if vvars[5] != None: print(f'\t> VVAR5 = {vvars[5]:#x}  ---> APIC ID for {corestring}{targetLogicalCore} thread1')
		else: "\t> VVAR5 = HTDisabled Error"
		print(f'{bullets} Use Merlin version 8.15 ---> Individual seed cmd example:')
		print(f'{bullets} MerlinX.efi -otl -a <path to seed> -d 0 989680 1 0x80064000 2 1000002 3 0x10000 4 {apic_0} 5 {apic_1} ')
		print ("----------------------------------------------------------------\n")
		print(f'{bullets} If using slice_regression.nsh, set the following variables in console:\n')
		print(f'set SEEDS_PATH <path to slice content>')
		print(f'set SEEDS_PATH')
		print(f'set MERLIN_DIR <path to Merlin 8.15>')
		print(f'set MERLIN_DIR')
		print(f'set MERLIN_DRIVE <Merlin 8.15 drive>')
		print(f'set MERLIN_DRIVE')
		print(f'set DRG_START_FRESH 1')
		print(f'set DRG_START_FRESH')
		print(f'set DRG_STOP_ON_FAIL 0')
		print(f'set DRG_STOP_ON_FAIL')
		print(f'set VVAR3 "{vvars[3]:#x}"')
		print(f'set VVAR3')
		print(f'set VVAR2 "{vvars[2]:#x}"')
		print(f'set VVAR2')
		if vvars[4] != None: print(f'set VVAR4 "{vvars[4]:#x}"')
		else: print(f'set VVAR4 "None - Error Collecting Data"')
		print(f'set VVAR4')
		if vvars[5] != None: print(f'set VVAR5 "{vvars[5]:#x}"')
		else: print(f'set VVAR5 "None - HT Disabled"')
		print(f'set VVAR5')
		print(f'set VVAR_EXTRA "0 {vvars[0]:#x}"')
		print(f'set VVAR_EXTRA')
		print(f'set MERLIN "MerlinX"')
		print(f'set MERLIN')
		print('\nOnce set run: ../slice_regression.nsh %SEEDS_PATH% <Optional seeds filter>')
		print ("----------------------------------------------------------------\n")
	# MESH
	else:
		vvars = {	0:0x04C4B40,
					1:0x80064000,
					2:0x1000000,
					3:0x4000000,
					4:'apic_0',
					5:'apic_1'}

		print ("\n----------------------------------------------------------------")
		print(f'\n{bullets} To run MESH content for selected Pseudo Configuration')
		print(f'{bullets} Use the following VVARs:')
		print(f'\t> VVAR0 = {vvars[0]:#x}  ---> Runtime Execution default = 5s (x timing)')
		print(f'\t> VVAR1 = {vvars[1]:#x}  ---> Optional Base timing / multiplying factor of VVAR0')
		print(f'\t> VVAR2 = {vvars[2]:#x}  ---> Running Threads = Default(all)')
		print(f'\t> VVAR3 = {vvars[3]:#x}  ---> PM enabled seeds will skip the end of test PState restore verification.')
		#print(f'\tVVAR4 = {vvars[4]:#x}  ---> APIC ID for {corestring}{targetLogicalCore} thread0')
		#print(f'\tVVAR5 = {vvars[5]:#x}  ---> APIC ID for {corestring}{targetLogicalCore} thread1')
		print(f'{bullets} Use Merlin version 8.15 ---> Individual seed cmd example:')
		print(f'{bullets} MerlinX.efi -otl -a <path to seed> -d 0 989680 1 0x80064000 2 1000000 3 0x4000000 ')
		print ("----------------------------------------------------------------\n")
		print(f'{bullets} If using runregression.nsh, set the following variables in console:\n')
		print(f'set SEEDS_PATH <path to slice content>')
		print(f'set SEEDS_PATH')
		print(f'set MERLIN_DIR <path to Merlin 8.15>')
		print(f'set MERLIN_DIR')
		print(f'set MERLIN_DRIVE <Merlin 8.15 drive>')
		print(f'set MERLIN_DRIVE')
		print(f'set DRG_START_FRESH 1')
		print(f'set DRG_START_FRESH')
		print(f'set DRG_STOP_ON_FAIL 0')
		print(f'set DRG_STOP_ON_FAIL')
		print(f'set VVAR3 "{vvars[3]:#x}"')
		print(f'set VVAR3')
		#print(f'set VVAR2 "{vvars[2]:#x}"')
		#print(f'set VVAR2')
		#print(f'set VVAR4 "{vvars[4]:#x}"')
		#print(f'set VVAR4')
		#print(f'set VVAR5 "{vvars[5]:#x}"')
		#print(f'set VVAR5')
		print(f'set VVAR_EXTRA "0 {vvars[0]:#x}"')
		print(f'set VVAR_EXTRA')
		print(f'set MERLIN "MerlinX"')
		print(f'set MERLIN')
		print('\nOnce set run: ../runregression.nsh %SEEDS_PATH% <Optional seeds filter>')
		print ("----------------------------------------------------------------\n")

def print_apic_ids():
	'''
	Prints compare table of APIC IDs vs CLASS APIC IDs in order of PHYSICAL IDs.
	'''

	scm.svStatus() #sv.refresh()

	die = sv.socket0.target_info["segment"].lower()

	phys2cindex = {}
	ht_enabled = len(sv.socket0.cpu.cores[0].threads) == 2
	#phys2cindex = scm._log2phy()
	for i in range (len(sv.socket0.cpu.cores)):
		PID = sv.socket0.cpu.cores[i].target_info["instance"] #.target_info["physical_id"] # This is really logical id...
		cinst = sv.socket0.cpu.cores[i].target_info["compute_instance"]
		phys2cindex.update({scm._physical_to_logical(PID,cinst):i})

	new_apic_id = {'compute0':0, 'compute1':128, 'compute2':256}
	## Legacy ID compute2 Starts from 0

	data = [['Compute', 'Core', 'Thread', 'Physical ID', 'Logical ID', 'APIC ID SYSTEM', 'APIC ID CLASS']]

	print('Building APIC IDs table.... \n')
	print(phys2cindex)
	for LID in sorted(phys2cindex.keys()):
		core_index = phys2cindex[LID]
		compute_instance = sv.socket0.cpu.cores[core_index].target_info['compute_instance']
		_new_apic_id = new_apic_id[f'compute{compute_instance}']

		old_apic_id = sv.socket0.cpu.cores[core_index].thread0.ml3_cr_pic_extended_local_apic_id
		physical_id = sv.socket0.cpu.cores[core_index].target_info['instance']
		logical_id = sv.socket0.cpu.cores[core_index].target_info['global_logical_inst']

		#print("%d\t%d\t%d\t%d\t%d" % (physical_id,logical_id, LID, old_apic_id, _new_apic_id))
		thread_index = '0x0'
		old_apic_index = f'{old_apic_id:#x}'
		new_apic_index = f'{_new_apic_id:#x}'
		if (ht_enabled):
			thread_index = '0x0, 0x1'
			new_apic_index = f'{_new_apic_id:#x},{_new_apic_id+1:#x}'
			old_apic_index = f'{old_apic_id:#x},{old_apic_id+1:#x}'

		new_apic_id[f'compute{compute_instance}'] = _new_apic_id + 2

		data.append([compute_instance, core_index, thread_index, physical_id, logical_id, old_apic_index, new_apic_index])
	#data_dict = {f'F{key}':{key: value} for key,value in data.items()}
	table = tabulate(data, headers='firstrow', tablefmt="grid")
	print(table)

## APIC ID Configurations  -- Revisit for CWF
def tester_apic_id(die=None, SVrefresh = True):
	'''
	Puts APIC IDs in order of PHYSICAL IDs.
	'''
	scm.svStatus(refresh=SVrefresh) #sv.refresh()
	if die == None:
		die = sv.socket0.target_info["segment"].lower()

	phys2cindex = {}
	ht_enabled = len(sv.socket0.cpu.cores[0].threads) == 2
	#phys2cindex = scm._log2phy()
	for i in range (len(sv.socket0.cpu.cores)):
		PID = sv.socket0.cpu.cores[i].target_info["instance"] #.target_info["physical_id"] # This is really logical id...
		cinst = sv.socket0.cpu.cores[i].target_info["compute_instance"]
		phys2cindex.update({scm._physical_to_logical(PID,cinst):i})
	new_apic_id = {'compute0':0, 'compute1':128, 'compute2':256}
	## Legacy ID compute2 Starts from 0
	new_legacy_id = {'compute0':0, 'compute1':128, 'compute2':0}
	data = {'Core':[],
			'Thread #':[],
			 'Physical ID':[],
			 'Logical ID':[],
#			'CLASS Logical ID':[],
			'Old APIC ID (SYS)':[],
			'New APIC ID (CLASS)':[]}
	print('Changing System APIC IDs to match CLASS assignment.... \n')
	#print("FIXING UP APIC IDS TO MATCH TESTER")
	#print(f"PID\tSLID\tCLID\tOLD AID\tNEW AID")


	for LID in sorted(phys2cindex.keys()):
		core_index = phys2cindex[LID]
		compute_instance = sv.socket0.cpu.cores[core_index].target_info['compute_instance']
		_new_apic_id = new_apic_id[f'compute{compute_instance}']
		_new_legacy_id = new_legacy_id[f'compute{compute_instance}']
		old_apic_id = sv.socket0.cpu.cores[core_index].thread0.ml3_cr_pic_extended_local_apic_id.get_value()
		physical_id = sv.socket0.cpu.cores[core_index].target_info['instance']
		logical_id = sv.socket0.cpu.cores[core_index].target_info['global_logical_inst']

		#print("%d\t%d\t%d\t%d\t%d" % (physical_id,logical_id, LID, old_apic_id, _new_apic_id))
		sv.socket0.cpu.cores[core_index].thread0.ml3_cr_pic_extended_local_apic_id=_new_apic_id
		sv.socket0.cpu.cores[core_index].thread0.ml3_cr_pic_legacy_local_apic_id.legacy_apic_id=_new_legacy_id
		data = apic_id_table(data=data, phy=physical_id, slog=logical_id, clog=LID, thread=0, old_aid=old_apic_id, new_aid=_new_apic_id)
#		data['Core'].append(F'CORE{physical_id}')
#		data['Physical ID'].append(hex(physical_id))
#		data['Logical ID'].append(f'SYS: {hex(logical_id)}, CLASS: {hex(LID)}')
##		data['CLASS Logical ID'].append()
#		data['Thread #'].append(hex(0))
#		data['Old APIC ID (SYS)'].append(hex(old_apic_id))
#		data['New APIC ID (CLASS)'].append(hex(_new_apic_id))

		if (ht_enabled):
			old_apic_id_t1 = sv.socket0.cpu.cores[core_index].thread1.ml3_cr_pic_extended_local_apic_id.get_value()
			#print("%d\t%d\t%d\t%d\t%d" % (physical_id,logical_id, LID, old_apic_id_t1, _new_apic_id+1))
			sv.socket0.cpu.cores[core_index].thread1.ml3_cr_pic_extended_local_apic_id=(_new_apic_id+1)
			sv.socket0.cpu.cores[core_index].thread1.ml3_cr_pic_legacy_local_apic_id.legacy_apic_id=(_new_legacy_id+1)
			data = apic_id_table(data=data, phy=physical_id, slog=logical_id, clog=LID, thread=1, old_aid=old_apic_id_t1, new_aid=_new_apic_id +1)
#			data['Core'].append(F'CORE{physical_id}')
#			data['Physical ID'].append(hex(physical_id))
#			#data['System Logical ID'].append(hex(logical_id))
#			data['Logical ID'].append(f'SYS: {hex(logical_id)}, CLASS: {hex(LID)}')
#			data['Thread #'].append(hex(1))
#			data['Old APIC ID (SYS)'].append(hex(old_apic_id_t1))
#			data['New APIC ID (CLASS)'].append(hex(_new_apic_id +1))
		#_new_apic_id+=2
		new_apic_id[f'compute{compute_instance}'] = _new_apic_id + 2
		new_legacy_id[f'compute{compute_instance}'] = _new_legacy_id + 2

	#data_dict = {f'F{key}':{key: value} for key,value in data.items()}
	table = tabulate(data, headers=data.keys(), tablefmt="grid")
	print(table)
	#printTable (data, header = data.keys(), label = 'APIC ID Summary of changes')

def apic_id_table(data, phy, slog, clog, thread, old_aid, new_aid):

	data['Core'].append(F'CORE{phy}')
	data['Physical ID'].append(hex(phy))
	data['Logical ID'].append(f'SYS: {hex(slog)}, CLASS: {hex(clog)}')
#	data['CLASS Logical ID'].append()
	data['Thread #'].append(hex(thread))
	data['Old APIC ID (SYS)'].append(hex(old_aid))
	data['New APIC ID (CLASS)'].append(hex(new_aid))

	return data

## S2T Setup --- Slice / MESH
def set_slice(
		cr_array_start=0, cr_array_end=0xffff, skip_index_array=[],
		core_ratio=0, mesh_ratio=0, license_level="128", dcf_ratio=0,
		clear_ucode = True, halt_pcu = True,
		all_crs = False, skip_wbinvd=False,
		):
	sbft_type ="SLICE"
	set_tester( cr_array_start, cr_array_end, skip_index_array,
		sbft_type, core_ratio, mesh_ratio, license_level, dcf_ratio,
		clear_ucode, halt_pcu, all_crs, skip_wbinvd)

def set_mesh(
		cr_array_start=0, cr_array_end=0xffff, skip_index_array=[],
		core_ratio=0, mesh_ratio=0, license_level="128", dcf_ratio=0,
		clear_ucode = True, halt_pcu = True, reorder_apic=True,
		all_crs = False, skip_wbinvd=False, mlcways = True):
	sbft_type ="MESH"


	set_tester( cr_array_start, cr_array_end, skip_index_array,
		sbft_type, core_ratio, mesh_ratio, license_level, dcf_ratio,
		clear_ucode, halt_pcu, all_crs, skip_wbinvd, mlcways)
	#if reorder_apic: tester_apic_id()

def set_tester(
		cr_array_start=0, cr_array_end=0xffff, skip_index_array=[],
		sbft_type = "SLICE",
		core_ratio=0, mesh_ratio=0, license_level="128", dcf_ratio=None,
		clear_ucode = True, halt_pcu = True,
		all_crs = False, skip_wbinvd=False, mlcways = True
		):

	"""
	:cr_array_start: Index to start on in cr_array -- for minimization
	:cr_array_end: Index to end on in cr_end -- for minimization
	:skip_index_array: array of indexes to skip -- for minimizatio
	:sbft_type = "SLICE" or "MESH"
	:core_ratio: Set cores/mpdules to fixed ratio, 'None' will skip override.  0 will set to P1( default )
	:mesh_ratio: Set mesh to fixed ratio,  'None' will skip override.  0 will set to uncor max ratio ( default )
	:license_level: Set license level. 1=sse, 3=AVX2, 5=AVX3. (default = 1) 'None' will skip override
	:dcf_ratio: Set DCF ratio ( default = 0 )  'None' will skip override
	:clear_ucode (default = True): If set, will clear out micro_patch_valids regs
	:halt_pcu (default = True): If set, will halt pcu
	:all_crs -- will write all CR deltas, not just minimized tests. Will cause EFI to hang. Good for ITP loader
	 skip_wbinvd -- skip WBINVD
	"""
	crarray = None
	product = config.SELECTED_PRODUCT
	dcf_allowed = ['GNR']
	lic_allowed = ['GNR']
	pstates_allowed = ['GNR']

	if (sbft_type =="SLICE"):
		crarray = _s2t_reg ##_slice_crs_min
	elif(sbft_type =="MESH"):
		crarray = _mesh_dict #_mesh_crs_min ## Need to check the registers
	else:
		print ("INCORRECT SBFT TYPE %s" % sbft_type)
		return

	if (core_ratio != None):
		if(core_ratio == 0):
			core_ratio=CoreDebugUtils.read_core_p1()
		print (f"Setting flat IA Ratio to {core_ratio}")
		CoreDebugUtils.set_core_freq(core_ratio)
	if (mesh_ratio != None):
		if (mesh_ratio == 0 ):
			mesh_ratio = CoreDebugUtils.read_uncore_p1()
		print (f"Setting flat IA Ratio to {mesh_ratio}")
		CoreDebugUtils.set_mesh_freq(mesh_ratio)

	## DCF Ratio is not available for AtomCores
	if (dcf_ratio != None and product in dcf_allowed): CoreDebugUtils.dcf_set_ratio(dcf_ratio=dcf_ratio)
	if (all_crs): crarray = _s2t_reg ##_slice_crs_all ## Nothing here, might want to check defaulting to _s2t_reg dict
	if (sbft_type == "MESH" and mlcways):
		CoreDebugUtils.set_mlc_waymask(mesh_tester = True )
	# Check if there is any register to set if not just dont go here
	#if cr_array_end != cr_array_start:
	if (cr_array_start < 0xffff): _set_crs(crarray, cr_array_start, cr_array_end, skip_index_array, clear_ucode,  halt_pcu, skip_wbinvd, SVrefresh = False)
	else: print (f" Skipping Registers Configuration...")
	if (license_level != None and product in lic_allowed):
		print (f"Setting AVX license : {license_level}")
		CoreDebugUtils.set_license(lic=license_level)

## Revisit for CWF
def _set_crs(crarray, cr_array_start=0, cr_array_end=0xffff, skip_index_array=[], clear_ucode = False, halt_pcu = False, skip_wbinvd = False, SVrefresh = True):
	#sv = namednodes.sv.get_manager(["socket"])
	scm.svStatus(refresh=SVrefresh)#itp.unlock()
	func_wr_ipc = cr_write_ipc

	start_halted = True
	if (itp.isrunning() == True):
		print ("itp.halt()")
		itp.halt()
		start_halted = False
	if (skip_wbinvd == False):
		itp.threads[CoreDebugUtils.find_bsp_thread()].wbinvd()

	print ("\nSetting CRs to tester values ( at least as close as we can get)")
	num_crs = len(crarray)
	# TODO: Check that cr_array_end, cr_array_start and all elements within skip_index_array are within the bounds of the crarray
	if ((cr_array_start !=0) or (cr_array_end != 0xffff)):
		num_crs = cr_array_end - cr_array_start  # Blind calc.  Doesn't check against number of items in array

	# Product specific to set CRS using IPC
	pf._set_crs(sv, num_crs, crarray, cr_array_start, cr_array_end, skip_index_array, _s2t_dict, func_wr_ipc)

#	print ("\nSetting %d CRs " % num_crs)
#	index = 0
#	for n in sorted(crarray):
#	# for n in (crarray):
#
#		if (index not in skip_index_array) and (index >= cr_array_start) and (index<=cr_array_end):
#
#			if 'thread' in n:
#
#
#				threads = len(sv.sockets.cpu.cores[0].threads)
#				if threads == 1 and 'thread1' in n:
#					print ("%d: !!!! skipping %s, single thread is configured" % (index, n)  )
#					continue
#				value = sv.sockets.cpu.cores[0].get_by_path(n).read()
#				sv.socket0.computes.cpu.cores.get_by_path(n).write(crarray[n])
#
#				print("TAP -- | {}:{} Changed from :{}: -> :{}: ".format(index, n, value, hex(crarray[n])))
#			else:
#				cr_write_ipc(index, n, crarray)
#				print("IPC -- | {}:{}({})={}".format(index, n,hex(_s2t_dict[n]['cr_offset']),hex(crarray[n])))
#		else:
#			print ("%d: !!!! skipping %s" % (index, n)  )
#		index +=1

	print ("Done setting CRs ")
	if clear_ucode: CoreDebugUtils.do_clear_ucode()
	if halt_pcu: CoreDebugUtils.pcu_halt()
	if start_halted == False:
		print ("itp.go()")
		itp.go()

def _set_crs_tap(crarray = None , cr_array_start=0, cr_array_end=0xffff, skip_index_array=[], clear_ucode = False, halt_pcu = False, skip_wbinvd = False, SVrefresh = True):

	sv = namednodes.sv

	if crarray == None: crarray = _s2t_reg

	scm.svStatus(refresh=SVrefresh)#itp.unlock()
	start_halted = True
	if (itp.ishalted() == False):
		print ("itp.halt()")
		itp.halt()
		start_halted = False
	if (skip_wbinvd == False):
		itp.threads[CoreDebugUtils.find_bsp_thread()].wbinvd()
	print ("Setting CRs to tester values ( at least as close as we can get)")
	num_crs = len(crarray)
	# TODO: Check that cr_array_end, cr_array_start and all elements within skip_index_array are within the bounds of the crarray
	if ((cr_array_start !=0) or (cr_array_end != 0xffff)):
		num_crs = cr_array_end - cr_array_start  # Blind calc.  Doesn't check against number of items in array

	# Product specific to set CRS using TAP
	pf._set_crs_tap(sv, num_crs, crarray, cr_array_start, cr_array_end, skip_index_array)

#	for n in sorted(crarray):
#	# for n in (crarray):
#
#		if (index not in skip_index_array) and (index >= cr_array_start) and (index<=cr_array_end):
#			# print ("%d:%s: itp.crb64(0x%x, 0x%x)" % (index, n, _s2t_dict[n], crarray[n]))
#
#
#			threads = len(sv.sockets.cpu.cores[0].threads)
#			if threads == 1 and 'thread1' in n:
#				print ("%d: !!!! skipping %s, single thread is configured" % (index, n)  )
#				continue
#
#			value = sv.socket0.compute0.cpu.cores[0].get_by_path(n)
#			sv.socket0.computes.cpu.cores.get_by_path(n).write(crarray[n])
#			time.sleep(0.5)
#			mcchk = sv.socket0.compute0.cpu.cores[0].ml2_cr_mc3_status
#
#			if mcchk != 0:
#				print(f'sv.socket0.cpu.core0.ml2_cr_mc3_status = {mcchk}')
#				print(f"{index}: {n} - Failing the unit add to skip --")
#				break
#			print("{}:{} Changed from :{}: -> :{}: ".format(index, n, value, hex(crarray[n])))
#
#		else:
#			print ("%d: !!!! skipping %s" % (index, n)  )
#		index +=1

	print ("Done setting CRs ")
	if clear_ucode: CoreDebugUtils.do_clear_ucode()
	if halt_pcu: CoreDebugUtils.pcu_halt()
	if start_halted == False:
		print ("itp.go()")
		itp.go()

def cr_write(crarray=None, cr_array_start=0, cr_array_end=0xffff):

	if crarray == None: crarray = _s2t_reg
	_set_crs(crarray=crarray, cr_array_start=cr_array_start, cr_array_end=cr_array_end)

def cr_write_ipc(index, n, crarray = None):

	sv = namednodes.sv
	if _s2t_dict[n]['numbits']==0x20:
		#print("{}:{}({})={}".format(index, n,hex(_s2t_dict[n]['cr_offset']),hex(crarray[n])))
		ipc.crb(_s2t_dict[n]['cr_offset'],crarray[n])
	elif _s2t_dict[n]['numbits']==0x40:
		#print("{}:{}({})={}".format(index, n,hex(_s2t_dict[n]['cr_offset']),hex(crarray[n])))
		ipc.crb64(_s2t_dict[n]['cr_offset'],crarray[n])

def _get_bool(prompt):
	while True:
		try:
			return {"true":True,"false":False}[input(prompt).lower()]
		except KeyError:
			print("Invalid input please enter True or False!")

def _yorn_bool(prompt, default_yorn="Y"):
	yorn = ""
	ret_val=False
	while "N" not in yorn and "Y" not in yorn:
		yorn = input(prompt).upper()
		if yorn == "":
			yorn = default_yorn
		if yorn == "Y": ret_val = True
	print (f"{ret_val}")
	return ret_val

def _yorn_int(default_yorn = 'Y', prompt = 'Answer Y or N', userin = 'Enter Value'):
	yorn = ""
	response = None
	print (f"{prompt}")
	while "N" not in yorn and "Y" not in yorn:
		yorn = input(f'Y / N (enter for [{default_yorn}]): ').upper()
		if yorn == "": yorn = default_yorn
	if yorn == "Y":
		response = int(input(f"\n{userin}"))

	return response

def _yorn_float(default_yorn = 'Y', prompt = 'Answer Y or N', userin = 'Enter Value'):
	yorn = ""
	response = None
	print (f"\n{prompt}")
	while "N" not in yorn and "Y" not in yorn:
		yorn = input(f'Y / N (enter for [{default_yorn}]): ').upper()
		if yorn == "": yorn = default_yorn
	if yorn == "Y":
		response = float(input(f"\n{userin}"))

	return response

def _yorn_string(default_yorn = 'N', prompt = 'Answer Y or N', userin = 'Enter Value'):
	yorn = ""
	response = None
	print (f"\n{prompt}")
	while "N" not in yorn and "Y" not in yorn:
		yorn = input(f'Y / N (enter for [{default_yorn}]): ').upper()
		if yorn == "": yorn = default_yorn
	if yorn == "Y":
		response = str(input(f"\n{userin}"))

	return response

def _exit_condition(condition, list, fail_text):
	def condition_check(c, l):
		if c not in l:
			raise ValueError(fail_text)

	## Checks for a Condition if not in the list exits
	try:
		condition_check(condition, list)
	except ValueError as e:
		print(e)
		exit(1)  # Exit the code with a status of 1 indicating an error

def cr_reg_dump(core = 0,  seldict = 3, wjson = True):
	mesh_crs = _mesh_crs_min
	slice_crs_min = _slice_crs_min
	crdict = _crdict
	s2t_reg = _s2t_reg
	_seldict =[mesh_crs,slice_crs_min,crdict, s2t_reg]
	regsname =['mesh_crs','slice_crs_min','crdict', 's2t_reg']
	_crd = {regsname[seldict]: {}}

	# Product Specific function to dump register values
	_crd = pf._cr_reg_dump(_seldict, seldict, sv, core, regsname, _crd)
#	for key in _seldict[seldict].keys():
#		regfound = sv.socket0.cpu.get_by_path(f'core{core}').thread0.search(key)
#		#print(regfound)
#		if key in regfound:
#			data = sv.socket0.cpu.get_by_path(f'core{core}').thread0.get_by_path(key).info
#			value = sv.socket0.cpu.get_by_path(f'core{core}').thread0.get_by_path(key).read()
#			#print(f'{key} : cr_offset = {data['cr_offset']}, numbits = {data['numbits']}')
#			#for keydata, value in data.items():
#			#    _crd[key][keydata] = value
#			#    print(f'thread0.{key} : {value}')
#		else:
#			data = sv.socket0.cpu.get_by_path(f'core{core}').get_by_path(key).info
#			value = sv.socket0.cpu.get_by_path(f'core{core}').get_by_path(key).read()
#			#print(data)
#		_crd[regsname[seldict]][key] = {'description':data['description'],
#										'cr_offset':data['cr_offset'],
#										'numbits':data['numbits'],} # Use below entries to build initial s2tregs main file, not needed for the rest.
#										#'desired_value':hex(_seldict[seldict][key]),
#										#'ref_value': hex(value)}
#		print(f"{key} : cr_offset = {data['cr_offset']}, numbits = {data['numbits']}, desired_value = {_seldict[seldict][key]} -- {value}")
#			#for keydata, value in data.items():
#			#    _crd[key][keydata] = value
#			#    print(f'{key} : {value}')
	if wjson:
		# Write to JSON file
		jfile = r'C:\\Temp\\s2tregdata.json'
		print(f"Saving dump creg data in file: {jfile}")
		with open(jfile, 'w') as json_file:
			json.dump(_crd, json_file, indent = 6)

def cr_reg_check(core = 0,  seldict = 3):
	mesh_crs = _mesh_crs_min
	slice_crs_min = _slice_crs_min
	crdict = _crdict
	s2t_reg = _s2t_reg
	_seldict =[mesh_crs,slice_crs_min,crdict, s2t_reg]
	regsname =['mesh_crs','slice_crs_min','crdict', 's2t_reg']

	# Product Specific function to check register values
	pf._cr_reg_check(sv, _seldict, seldict, core)
#	for key in _seldict[seldict].keys():
#		regfound = sv.socket0.cpu.get_by_path(f'core{core}').thread0.search(key)
#		#print(regfound)
#		if key in regfound:
#
#			value = sv.socket0.cpu.get_by_path(f'core{core}').thread0.get_by_path(key).read()
#			#print(f'{key} : cr_offset = {data['cr_offset']}, numbits = {data['numbits']}')
#			#for keydata, value in data.items():
#			#    _crd[key][keydata] = value
#			#    print(f'thread0.{key} : {value}')
#		else:
#
#			value = sv.socket0.cpu.get_by_path(f'core{core}').get_by_path(key).read()
#			#print(data)
#
#		print(f"{key} : desired_value = {hex(_seldict[seldict][key])} -- {value}")

## Data tabulate - Display data in a organized table format
def printTable(data, header = ['Frequency', 'Value(s)'], label = ''):
	#print(data)
	tblkeys = list(data.keys())
	tblvalues = list(data.values())

	# Converting the dictionary values to a list of lists
	table_data = [[k] + [v for v in tblvalues[i].values()] for i, k in enumerate(tblkeys)]

	# Printing the table
	table = tabulate(table_data, headers=header, tablefmt="grid")
	if label !='':
		print ('\n{}'.format(label))
	print(table)

_mesh_crs_min = reg.mesh_crs_min()

# Old Register Data from SPR/EMR
_slice_crs_min = reg.slice_crs_min()

# Old Dict from SPR/EMR new one will be loaded from json file
_crdict  = reg.cr_dict()

# Dict will be loaded from json file in in s2t\Regfiles folder
# Below is all the new values, all keys should be available in json data, if something needs to be added, please run again
# cr_reg_dump(core = 0,  seldict = 3, wjson = True) # To rebuild the json file, copy and replace, new file will be placed in C:\Temps
_s2t_reg = reg.s2t_reg()

_s2t_dict = reg.slice_dict()

_mesh_dict = reg.mesh_dict()
