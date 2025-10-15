## GNR Set Tester Registers
revision = 1.61
date = '23/07/2025'
engineer ='gaespino'
## Update: 05/02/2025
#
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
from ipccli import BitData
import json
import importlib
import os 
import time
from tabulate import tabulate

ipc = ipccli.baseaccess()
itp = ipc

sv = namednodes.sv.get_manager(["socket"])
#from common import baseaccess
sv.refresh()
verbose = False
debug = False

## Imports from S2T Folder
import users.gaespino.dev.S2T.CoreManipulation as scm
import users.gaespino.dev.S2T.GetTesterCurves as stc
import users.gaespino.dev.S2T.dpmChecks as dpm
import users.gaespino.dev.S2T.ConfigsLoader as LoadConfig

## UI Calls
import users.gaespino.dev.S2T.UI.System2TesterUI as UI

## Imports from THR folder -
try:
	import users.THR.PythonScripts.thr.GNRCoreDebugUtils as CoreDebugUtils 
except:
	import users.THR.PythonScripts.thr.CWFCoreDebugUtils as CoreDebugUtils 
## Reload of all imported scripts
importlib.reload(scm)
importlib.reload(CoreDebugUtils)
importlib.reload(stc)
importlib.reload(dpm)
importlib.reload(UI)
importlib.reload(LoadConfig)

bullets = '>>>'
s2tflow = None

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
ATE_MASKS = LoadConfig.ATE_MASKS
ATE_CONFIG = LoadConfig.ATE_CONFIG
DIS2CPM_MENU = LoadConfig.DIS2CPM_MENU
DIS2CPM_DICT = LoadConfig.DIS2CPM_DICT
RIGHT_HEMISPHERE = LoadConfig.RIGHT_HEMISPHERE
LEFT_HEMISPHERE = LoadConfig.LEFT_HEMISPHERE

# Framework Features Init
FRAMEWORK_FEATURES = LoadConfig.FRAMEWORK_FEATURES

# Registers Load
reg = LoadConfig.LoadRegisters()

# Product Specific Functions Load
pf = LoadConfig.LoadFunctions()

## Change Banner display based on product -- fixed for now
pf.display_banner(revision, date, engineer)

## Initializes Menus based on type of product used
def init_menus(product):
	if CORETYPES[product]['core'] == 'atomcore':
		menustring = 'Module'
	else:
		menustring = 'Core'

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
			'CLUSTER': f'\n{bullets} Fix Clustering on new mask? Y / N (enter for [Y]): ',
			'CLUSTERLSB': f'\n{bullets} Select: Fix disabling lowest slice (Y) / Fix disabling highest slice (N)? (enter for [N]): ',
			'APICS': f'\n{bullets} FIXUP APIC IDs to match tester? Y / N( enter for [N]): ',
			'BIOS': f'\n{bullets} Check BIOS knobs configuration before starting? Y / N ( enter for [N]): ',
			'ATE_Change': f'\n{bullets} Do you want to change any ATE value before moving forward? Y / N ( enter for [N]): ',
			'CoreVolt': f'\n{bullets} Do you want to set {menustring} Voltage Configuration? Y / N ( enter for [N]): ',
			'CFCVolt': f'\n{bullets} Do you want to set Uncore CFC Voltage Configuration? Y / N ( enter for [N]): ',
			'HDCVolt': f'\n{bullets} Do you want to set Uncore HDC Voltage Configuration? Y / N ( enter for [N]): ',
			'CFCIOVolt': f'\n{bullets} Do you want to set IO CFC Voltage Configuration? Y / N ( enter for [N]): ',
			'DDRDVolt': f'\n{bullets} Do you want to set DDRD Voltage Configuration? Y / N ( enter for [N]): ',
			'DDRAVolt': f'\n{bullets} Do you want to set DDRA Voltage Configuration? Y / N ( enter for [N]): ',
			'CoreBump': f'\n{bullets} Do you want to set {menustring} vBump Configuration? Y / N ( enter for [N]): ',
			'CFCBump': f'\n{bullets} Do you want to set Uncore CFC vBump Configuration? Y / N ( enter for [N]): ',
			'HDCBump': f'\n{bullets} Do you want to set Uncore HDC vBump Configuration? Y / N ( enter for [N]): ',
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
	Sets up system to be like tester.  
	Will ask questions on details
	'''
	
	global s2tflow
	tester_mode = 0
	s2tflow = S2TFlow(debug=debug)

	print("Select Tester Mode:")
	print("\t1. SLICE")
	print("\t2. MESH")
#	print("\t2. MESH_PM")
#	print("\t3. MESH_NOPM")
	while tester_mode not in range (1,3): 
		tester_mode = int(input("Enter 1-2: "))

	if tester_mode == 1:
		s2tflow.setupSliceMode()

	if tester_mode == 2:
		s2tflow.setupMeshMode()

def MeshQuickTest(core_freq = None, mesh_freq = None, vbump_core = None, vbump_mesh = None, Reset = False, Mask = None, pseudo = False, dis_2CPM = None, GUI = True, fastboot = True, corelic = None, volttype='vbump', debug= False, boot_postcode = False, extMask = None, u600w=None):
	s2tTest = S2TFlow(debug=debug)
	product = SELECTED_PRODUCT
	qdf = dpm.qdf_str()
	
	if qdf == 'RVF5' and u600w == None:
		u600w = True
		print(' --- Unit QDF is for 600W disabling FastBoot option')
	else:
		u600w = False
	

	if volttype == 'fixed':
		vtype = 2
	elif volttype == 'vbump':
		vtype = 3
	elif volttype == 'ppvc':
		vtype = 4
	else:
		vtype = 1

	voltage_recipes = ['ppvc']

	## Variables preconfig
	#s2tTest.targetLogicalCore=None, 
	#s2tTest.targetTile=None, 
	s2tTest.use_ate_freq = False
	s2tTest.use_ate_volt= False 
	#s2tTest.flowid=1, 
	#s2tTest.core_freq=None, 
	#s2tTest.mesh_freq=None, 
	#s2tTest.io_freq=None, 
	s2tTest.license_level=corelic 
	s2tTest.dcf_ratio=None
	s2tTest.stop_after_mrc=False 
	s2tTest.boot_postcode=boot_postcode 
	s2tTest.clear_ucode=False
	s2tTest.halt_pcu=False
	s2tTest.dis_acode=False 
	s2tTest.dis_ht = pseudo 
	s2tTest.dis_2CPM = dis_2CPM
	s2tTest.postBootS2T=True 
	s2tTest.clusterCheck = False 
	s2tTest.lsb = False
	s2tTest.fix_apic=False
	#s2tTest.dryrun=False,
	s2tTest.fastboot = fastboot if u600w == False else False
	s2tTest.mlcways = False
	#s2tTest.ppvc_fuses = None,
	#s2tTest.custom_volt = None, 
	#s2tTest.vbumps_volt = None, 
	s2tTest.reset_start = Reset 
	s2tTest.check_bios = False
	#s2tTest.mesh_cfc_volt=None, 
	#s2tTest.mesh_hdc_volt=None, 
	#s2tTest.io_cfc_volt=None, 
	#s2tTest.ddrd_volt=None,
	#s2tTest.ddra_volt=None, 
	#s2tTest.core_volt=None):
	s2tTest.reg_select = 1
	#s2tTest.license_level = None
	s2tTest.voltselect = 1
	valid_configs = {v:k for k,v in s2tTest.ate_masks.items()}
	s2tTest.extMasks = extMask  # Dict with system Masks to be used as base
	s2tTest.u600w = u600w

	customs = {'LeftSide':RIGHT_HEMISPHERE,'RightSide':LEFT_HEMISPHERE}
	computes = s2tTest.computes #['compute0', 'compute1', 'compute2']

	# Set quickconfig variables
	s2tTest.quick()
	
	## Option to replace system mask with an edited one
	#customMask = False
	
	# Init System
	s2tTest.mesh_init()
	
	## UI Part here
	if GUI:
		UI.mesh_ui(s2tTest, product=product)
	else:
		# Frequency Conditions
		if core_freq != None:
			s2tTest.core_freq = core_freq
		if mesh_freq != None:
			s2tTest.mesh_freq = mesh_freq
		
		## Voltage Conditions 
		# 1 No Change
		# 2 Fixed Voltage
		# 3 Vbumps 
		# PPVC Fuse recipe (RGB Reduction)

		if vtype > 1:
			s2tTest.voltselect = vtype
		
		if vbump_core != None and volttype not in voltage_recipes:	
			s2tTest.qvbumps_core = vbump_core
		
		if vbump_mesh != None and volttype not in voltage_recipes:
			s2tTest.qvbumps_mesh = vbump_mesh
		
		# Check for Target Masking
		if Mask == None:
			s2tTest.targetTile = 4
		elif Mask in valid_configs.keys():
			s2tTest.targetTile = 1
			s2tTest.target = Mask
			s2tTest.fastboot = False
		elif Mask.lower() in computes:
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
		
		# Run Mesh
		#s2tTest.setupMeshMode()
		# Asks for Voltage changes if not configured during ATE
		s2tTest.set_voltage()

		# Reboots the unit with Configuration -- In debug the script won't boot, this is mainly to check any core addition to the script
		if not s2tTest.debug: s2tTest.mesh_run()

		# Save Configuration to Temp Folder
		s2tTest.save_config(file_path=s2tTest.defaultSave)

def SliceQuickTest(Target_core = None, core_freq = None, mesh_freq = None, vbump_core = None, vbump_mesh = None, Reset = False, pseudo = False, dis_2CPM = None, GUI = True, fastboot = True, corelic = None,  volttype = 'fixed', debug= False, boot_postcode = False, u600w=None):
	s2tTest = S2TFlow(debug=debug)
	product = SELECTED_PRODUCT
	qdf = dpm.qdf_str()

	if qdf == 'RVF5' and u600w == None:
		u600w = True
		print(' --- Unit QDF is for 600W disabling FastBoot option')
	else:
		u600w = False
	
	
	if volttype == 'fixed':
		vtype = 2
	elif volttype == 'vbump':
		vtype = 3
	elif volttype == 'ppvc':
		vtype = 4
	else:
		vtype = 1

	voltage_recipes = ['ppvc']

	## Variables preconfig
	s2tTest.targetLogicalCore=Target_core 
	#s2tTest.targetTile=None, 
	s2tTest.use_ate_freq = False
	s2tTest.use_ate_volt= False 
	#s2tTest.flowid=1, 
	#s2tTest.core_freq=None, 
	#s2tTest.mesh_freq=None, 
	#s2tTest.io_freq=None, 
	s2tTest.license_level=corelic 
	s2tTest.dcf_ratio=None
	s2tTest.stop_after_mrc=False 
	s2tTest.boot_postcode=boot_postcode 
	s2tTest.clear_ucode=False
	s2tTest.halt_pcu=False
	s2tTest.dis_acode=False 
	s2tTest.dis_ht = pseudo 
	s2tTest.dis_2CPM = dis_2CPM
	s2tTest.postBootS2T=True 
	s2tTest.clusterCheck = False 
	s2tTest.lsb = False
	s2tTest.fix_apic=False
	#s2tTest.dryrun=False,
	s2tTest.fastboot = fastboot if u600w == False else False
	s2tTest.mlcways = False
	#s2tTest.ppvc_fuses = None,
	#s2tTest.custom_volt = None, 
	#s2tTest.vbumps_volt = None, 
	s2tTest.reset_start = Reset 
	s2tTest.check_bios = False
	#s2tTest.mesh_cfc_volt=None, 
	#s2tTest.mesh_hdc_volt=None, 
	#s2tTest.io_cfc_volt=None, 
	#s2tTest.ddrd_volt=None,
	#s2tTest.ddra_volt=None, 
	#s2tTest.core_volt=None):
	s2tTest.reg_select = 1
	#s2tTest.license_level = None
	s2tTest.voltselect = 1
	s2tTest.u600w = u600w

	# Set quickconfig variables
	s2tTest.quick()
	
	# Init System
	s2tTest.slice_init()
	
	## UI Part here
	if GUI:
		UI.slice_ui(s2tTest, product=product)
	else:
		# Frequency Conditions
		if core_freq != None:
			s2tTest.core_freq = core_freq
		if mesh_freq != None:
			s2tTest.mesh_freq = mesh_freq
		
		## Voltage Conditions 
		# 1 No Change
		# 2 Fixed Voltage
		# 3 Vbumps 
		# PPVC Fuse recipe (RGB Reduction)

		if vtype > 1:
			s2tTest.voltselect = vtype
		
		if vbump_core != None and volttype not in voltage_recipes:	
			s2tTest.qvbumps_core = vbump_core
		
		if vbump_mesh != None and volttype not in voltage_recipes:
			s2tTest.qvbumps_mesh = vbump_mesh
		
		# Check for Target Core
		if Target_core == None:
			s2tTest.slice_core()

		
		# Run Mesh
		#s2tTest.setupMeshMode()
		# Asks for Voltage changes if not configured during ATE
		s2tTest.set_voltage()
		#print(s2tTest.targetLogicalCore, type(s2tTest.targetLogicalCore))
		# Reboots the unit with Configuration -- In debug the script won't boot, this is mainly to check any core addition to the script
		if not s2tTest.debug: s2tTest.slice_run()

		# Save Configuration to Temp Folder
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
						u600w=None,
						extMasks=None):

		## Script Flow
		self.mode = None
		self.external = False
		self.product = PRODUCT_CONFIG
		## Testing and debug Variable
		self.debug = debug
		## Common Settings
		self.use_ate_freq = use_ate_freq
		self.flowid = flowid
		self.use_ate_volt = use_ate_volt
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
		## Frequency Settings
		self.core_freq = core_freq
		self.mesh_freq = mesh_freq
		self.io_freq = io_freq
		self.license_level = license_level
		## External Base Masks
		self.extMasks = extMasks

		## Voltage Settings
		self.mesh_cfc_volt = mesh_cfc_volt
		self.mesh_hdc_volt = mesh_hdc_volt
		self.io_cfc_volt = io_cfc_volt
		self.ddrd_volt = ddrd_volt
		self.ddra_volt = ddra_volt
		self.core_volt = core_volt
		self.ppvc_fuses = ppvc_fuses
		self.custom_volt = custom_volt
		self.vbumps_volt = vbumps_volt
		#self.init_voltage()

		self.voltselect = None

		## Mesh Settings
		self.targetTile = targetTile
		self.clusterCheck = clusterCheck
		self.dis_ht = dis_ht
		self.dis_2CPM = dis_2CPM
		self.lsb = lsb
		self.mlcways = mlcways

		self.custom_list = []
		self.target = ''
		self.fix_apic = fix_apic
		self.dryrun= dryrun

		self.u600w = u600w
		self.ATE_CORE_FREQ = [f'F{k}' for k in stc.CORE_FREQ.keys()]
		self.ATE_MESH_FREQ = [f'F{k}' for k in stc.CFC_FREQ.keys()]
		## Slice Settings
		self.targetLogicalCore = targetLogicalCore

		# Init Menus and disable checks product specific features
		self.__FRAMEWORK_FEATURES = FRAMEWORK_FEATURES
		self.__FRAMEWORKVARS = FRAMEWORK_FEATURES
		self.specific_product_features()
	
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
					print(f'\t> Feature: {F} not enabled for this product ({SELECTED_PRODUCT}).')
					setattr(self, F, FEATURE['disabled_value'])
		print(f'{"+"*80}\n')

	def specific_product_features(self):
		
		_exit_condition(self.product, CORETYPES.keys(), f"\n{bullets} Product not available, select a valid product...\n")
		
		# Will move this configuration to a config json file to avoid product specifics 
		self.Menus, self.coremenustring = init_menus(self.product)
		self.computes = sv.socket0.computes.name
		self.core_type = CORETYPES[self.product]['core']
		
		## Specific HDC condition atomcore is located at L2
		if self.core_type == 'atomcore': 
			self.HDC_AT_CORE = True
		else: 
			self.HDC_AT_CORE = False
		# Check for each Feature Status
		self.features_check()

		# Populate internal variables based on product selected
		self.license_dict = LICENSE_S2T_MENU
		self.core_license_dict = LICENSE_DICT
		self.core_license_levels = LICENSE_LEVELS
		self.qdf600 = SPECIAL_QDF
		self.ate_masks = ATE_MASKS[PRODUCT_CONFIG.upper()]
		self.customs = CUSTOMS
		self.ate_config_main = ATE_CONFIG['main']
		self.ate_config_product = ATE_CONFIG[PRODUCT_CONFIG.upper()]
		self.left_hemispthere = LEFT_HEMISPHERE
		self.right_hemispthere = RIGHT_HEMISPHERE
		self.validclass = VALIDCLASS[PRODUCT_CONFIG.upper()]
		self.dis2cpm_dict = DIS2CPM_DICT

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
		
	## Initialization flow checks for BIOS and ColdReset if required
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
			dpm.powercycle(ports=[1])
		else: 
			#dpm.powercycle(ports=[1])
			dpm.reset_600w()
			time.sleep(scm.EFI_POSTCODE_WT)
			#dpm.reset_600w()
		# Wait time to start reading PythonSV again
		time.sleep(scm.EFI_POSTCODE_WT)
		scm._wait_for_post(scm.EFI_POST, sleeptime=scm.EFI_POSTCODE_WT, additional_postcode=scm.LINUX_POST)
		scm.svStatus(refresh=True)

	def init_voltage(self, mode = 'mesh'):
		#self.safevolts = [['Domain', 'Value']]
		self.safevolts_PKG = [['Domain', 'Value']]
		self.safevolts_CDIE = [['Domain', 'Value']]
		
		self.cfc_volt = {c:None for c in self.computes}
		self.hdc_volt = {c:None for c in self.computes}					
		
		# Variables used in CORE are different than the ones used in mesh, but values are the same
		for k,v in stc.All_Safe_RST_PKG.items():
			self.safevolts_PKG.append([k,v])
		for k,v in stc.All_Safe_RST_CDIE.items():
			self.safevolts_CDIE.append([k,v])
		
		# Setting safevalues depending on selection, slice or mesh
		safevalues = self.safevolts_CDIE if mode == 'slice' else self.safevolts_PKG
		self.voltstable = tabulate(safevalues, headers="firstrow", tablefmt="grid")
		self.v_confg = None
		self.volt_config = {	'compute0':[],
						'compute1':[],
						'compute2':[],
						'io0':[],
						'io1':[],}
	
	def ate_data(self, mode = 'mesh'):
		if mode == 'slice':
			print(f"\n{bullets} {self.product} {self.coremenustring} frequencies are:")

			table = [[f'{self.coremenustring} Frequency', 'IA Value', 'CFC Value']]
			for k, v in stc.CORE_FREQ.items():
				table.append([f'F{k}',v,stc.CORE_CFC_FREQ[k]])

			print(tabulate(table, headers="firstrow", tablefmt="grid"))
			print(f'--> Multiple freqs are FLOWID 1-4')
		
		elif mode == 'mesh':
			print(f"\n{bullets} {self.product} CFC frequencies are:")
			table = [['UnCore Frequency', 'CFC Value', 'IA Value']]
			for k, v in stc.CFC_FREQ.items():
				table.append([f'F{k}',v,stc.CFC_CORE_FREQ[k]])

			print(tabulate(table, headers="firstrow", tablefmt="grid"))
			print(f'--> Multiple freqs are FLOWID 1-4')

	## Confguration Save / Load / Run
	def save_config(self, file_path = r'C:\\Temp\\System2TesterRun.json'):
		
		config = {
			'mode': self.mode,
			'targetLogicalCore': self.targetLogicalCore,
			'targetTile': self.targetTile,
			'target': self.target,
			'custom_list': self.custom_list,
			'use_ate_freq': self.use_ate_freq,
			'use_ate_volt': self.use_ate_volt,
			'flowid': self.flowid,
			'core_freq': self.core_freq,
			'mesh_freq': self.mesh_freq,               
			'io_freq': self.io_freq,
			'license_level': self.license_level,
			'dcf_ratio': self.dcf_ratio,
			'stop_after_mrc': self.stop_after_mrc,
			'boot_postcode': self.boot_postcode,
			'clear_ucode': self.clear_ucode,
			'halt_pcu': self.halt_pcu,
			'dis_acode': self.dis_acode,
			'dis_ht': self.dis_ht,
			'dis_2CPM': self.dis_2CPM,
			'postBootS2T': self.postBootS2T,
			'clusterCheck': self.clusterCheck,
			'lsb': self.lsb,
			'fix_apic': self.fix_apic,
			'dryrun': self.dryrun,
			'fastboot': self.fastboot,
			'mlcways': self.mlcways,
			'ppvc_fuses': self.ppvc_fuses,
			'custom_volt': self.custom_volt,
			'vbumps_volt': self.vbumps_volt,
			'volt_config': self.volt_config,
			'u600w': self.u600w,
			#'reset_start': self.reset_start,
			#'check_bios': self.check_bios,
			'mesh_cfc_volt': self.mesh_cfc_volt,
			'mesh_hdc_volt': self.mesh_hdc_volt,
			'io_cfc_volt': self.io_cfc_volt,
			'ddrd_volt': self.ddrd_volt,
			'ddra_volt': self.ddra_volt,
			'core_volt': self.core_volt,
			'masks': {k:str(v) for k,v in self.masks.items()} if self.masks != None else self.masks,
			'extMasks': self.extMasks}
		
		print(f' ---> Saving Configuration file to: {file_path}')
		#print(config['masks'])
		#print('---------------')
		#print(config['volt_config'])
		with open(file_path, 'w') as f:
			json.dump(config, f, indent=4)

	def load_config(self, file_path = r'C:\\Temp\\System2TesterRun.json'):
		with open(file_path, 'r') as f:
			config = json.load(f)
			self.mode = config.get('mode')
			self.targetLogicalCore = config.get('targetLogicalCore')
			self.targetTile = config.get('targetTile')
			self.target = config.get('target')
			self.custom_list = config.get('custom_list')
			self.use_ate_freq = config.get('use_ate_freq')
			self.use_ate_volt = config.get('use_ate_volt')
			self.flowid = config.get('flowid')
			self.core_freq = config.get('core_freq')
			self.mesh_freq = config.get('mesh_freq')
			self.io_freq = config.get('io_freq')
			self.license_level = config.get('license_level')
			self.dcf_ratio = config.get('dcf_ratio')
			self.stop_after_mrc = config.get('stop_after_mrc', False)
			self.boot_postcode = config.get('boot_postcode', False)
			self.clear_ucode = config.get('clear_ucode')
			self.halt_pcu = config.get('halt_pcu')
			self.dis_acode = config.get('dis_acode')
			self.dis_ht = config.get('dis_ht')
			self.dis_2CPM = config.get('dis_2CPM')
			self.postBootS2T = config.get('postBootS2T')
			self.clusterCheck = config.get('clusterCheck')
			self.lsb = config.get('lsb')
			self.fix_apic = config.get('fix_apic')
			self.dryrun = config.get('dryrun')
			self.fastboot = config.get('fastboot')
			self.mlcways = config.get('mlcways')
			self.ppvc_fuses = config.get('ppvc_fuses')
			self.custom_volt = config.get('custom_volt')
			self.vbumps_volt = config.get('vbumps_volt')
			self.reset_start = config.get('reset_start')
			self.check_bios = config.get('check_bios')
			self.mesh_cfc_volt = config.get('mesh_cfc_volt')
			self.mesh_hdc_volt = config.get('mesh_hdc_volt')
			self.io_cfc_volt = config.get('io_cfc_volt')
			self.ddrd_volt = config.get('ddrd_volt')
			self.ddra_volt = config.get('ddra_volt')
			self.core_volt = config.get('core_volt')
			masks = config.get('masks')
			self.extMasks = config.get('extMasks')
			
			if masks == None:
				self.masks = masks
			else:
				self.masks = {k: (lambda v: None if v == "None" else int(v, 16))(v) for k, v in masks.items()}
				#for k,v in masks.items():
				#	self.masks[k] = None if v == "None" else int(v,16)
			#print(self.masks)
			#self.masks = {k: (lambda v: None if v == "None" else int(v, 16))(v) for k, v in masks.items()}
			self.volt_config = config.get('volt_config')
			self.u600w = config.get('u600w')
			#print(self.masks)
		configtable = [["Setting", "Value"]]
		for k,v in config.items():
			if isinstance(v,dict):
				for d,c in v.items():
					#print(c)
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
		print(tabulate(configtable, headers="firstrow", tablefmt="grid"))

		self.configfile = file_path		
		print(f'{bullets} S2T Configuration loaded from: {file_path}\n')

	def run_config(self, dryrun= True, file_path = r'C:\\Temp\\System2TesterRun.json'):
		if self.u600w: 
			print(f'{bullets} Unit set for 600w Configuration, removing Fastboot option...')
			self.fastboot == False
		if self.configfile == None: 
			#print(f'{bullets} S2T Configuration loaded from: {file_path}\n')
			self.load_config(file_path = file_path)
		
		print(f'{bullets} Running System 2 Tester with Configuration loaded from: {self.configfile}\n')

		if dryrun: 
			
			self.reset_start = True
		
		self.check_bios = False
		# Will ask for system Restart
		#if self.reset_start == False:
		#	self.reset_start = _yorn_bool(default_yorn='Y', prompt = self.Menus['Reset'].replace('Enter for [N]','Enter for [Y]'))
		
		self.init_flow()
		if self.mode == 'slice':
			# Starts the Run Sequence
			print(f'{bullets} Running System 2 Tester {self.mode.upper()} with Configuration loaded from: {self.configfile}\n')
			self.slice_run()
		elif self.mode == 'mesh':
			print(f'{bullets} Running System 2 Tester {self.mode.upper()} with Configuration loaded from: {self.configfile}\n')
			self.mesh_run()
		else:
			print(f'{bullets} Not a valid System 2 Tester Flow found in the configuration please check your file')

	## Common Settings for Slice and Mesh
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

	def set_voltage(self):
		computes = self.computes
		external = self.external
		volt_select = self.voltselect
		
		if self.use_ate_volt == False and self.__FRAMEWORK_FEATURES['use_ate_volt']['enabled']:
			
			## Skips self.Menus if data is coming from an external source
			if not external: 
				print(f"\n{bullets} Set System Voltage?") 
				print("\t> 1. No")
				print("\t> 2. Fixed Voltage")
				print("\t> 3. Voltage Bumps")
				print("\t> 4. PPVC Conditions")
				while volt_select not in range (1,5): 
					volt_select = input("\n--> Enter 1-4: (enter for [1]) ")
					if volt_select == "":
						volt_select = 1
					volt_select = int(volt_select)
			
			## Fixed Voltage Configuration
			if volt_select == 2:
				
				if not external: 
					print(f"\n{bullets} Fixed Voltage Configuration Selected\n")
					print(f"\n{bullets} Tester Safe values for reference:\n")
					print(self.voltstable)
					self.core_volt = _yorn_float(default_yorn ='N', prompt = self.Menus['CoreVolt'], userin = f"--> Enter {self.coremenustring} Voltage: ")
				else: 
					self.core_volt = self.qvbumps_core

				# Calls the Uncore Voltages options
				self.uncore_voltages(fixed=True)

				if not external: 
					self.io_cfc_volt = _yorn_float(default_yorn ='N', prompt = self.Menus['CFCIOVolt'], userin = "--> Enter CFC IO DIE Voltage: ")
					self.ddrd_volt = _yorn_float(default_yorn ='N', prompt = self.Menus['DDRDVolt'], userin = "--> Enter DDRD Voltage: ")
				
				# DDRA option will be included later, only digital side is available for now
				#self.ddrd_volt = _yorn_float(default_yorn ='N', prompt = self.Menus['DDRAVolt'], userin = "--> Enter DDRA Voltage: ")
				voltdict = {'core':self.core_volt, 'cfc_die':self.mesh_cfc_volt, 'hdc_die':self.mesh_hdc_volt, 'cfc_io':self.io_cfc_volt, 'ddrd':self.ddrd_volt, 'ddra':self.ddra_volt}
				self.volt_config = dpm.tester_voltage(bsformat = (not self.fastboot), volt_dict = voltdict, volt_fuses = [], fixed=True, vbump = False)
				self.custom_volt = True
				#self.v_confg = [['Domain', 'FixedValue']]
			
			## Voltage Vbumps
			elif volt_select == 3:

				if not external: 
					print(f"\n{bullets} Vbumps Configuration selected, use values in volts range of -0.2V to 0.2V:")
					self.core_volt = self.check_vbumps(_yorn_float(default_yorn ='N', prompt = self.Menus['CoreBump'], userin = f"--> Enter {self.coremenustring} vBump: "))
				else: 
					self.core_volt = self.qvbumps_core
				# Adding a bit of Change for MESH as this can be applied to each Compute individually
				# Calls the Uncore Voltages options
				self.uncore_voltages(vbumps=True)

				if not external: 
					self.io_cfc_volt =  self.check_vbumps(_yorn_float(default_yorn ='N', prompt = self.Menus['CFCIOBump'], userin = "--> Enter CFC IO DIE vBump: "))
					self.ddrd_volt =  self.check_vbumps(_yorn_float(default_yorn ='N', prompt = self.Menus['DDRDBump'], userin = "--> Enter DDRD vBump: "))
				# DDRA option will be included later, only digital side is available for now
				#self.ddrd_volt = self.check_vbumps(_yorn_float(default_yorn ='N', prompt = self.Menus['DDRABump'], userin = "--> Enter DDRD vBump: "))
				voltdict = {'core':self.core_volt, 'cfc_die':self.mesh_cfc_volt, 'hdc_die':self.mesh_hdc_volt, 'cfc_io':self.io_cfc_volt, 'ddrd':self.ddrd_volt, 'ddra':self.ddra_volt}
				self.volt_config = dpm.tester_voltage(bsformat = (not self.fastboot), volt_dict = voltdict, volt_fuses = [], fixed=False, vbump = True)
				self.vbumps_volt = True
				#self.v_confg = [['Domain', 'Vbump']]
			
			## PPVC fuses Configuration -- For an external use, need to modify a few more scripts... WIP
			elif volt_select == 4:

				self.volt_config = dpm.ppvc(bsformat=(not self.fastboot), ppvc_fuses = [])
				self.ppvc_fuses = True			
		
		elif self.use_ate_volt:
			voltdict = {'core':self.core_volt, 'cfc_die':self.mesh_cfc_volt, 'hdc_die':self.mesh_hdc_volt, 'cfc_io':self.io_cfc_volt, 'ddrd':self.ddrd_volt, 'ddrd':self.ddra_volt}
			self.volt_config = dpm.tester_voltage(bsformat = (not self.fastboot), volt_dict = voltdict, volt_fuses = [], fixed=True, vbump = False)

	def uncore_voltages(self, vbumps= False, fixed= False):
		if self.external:
			uncore = 3
			
		else:
			uncore = None
			print(f"\n{bullets} Uncore Voltage Options?") 
			print("\t> 1. Same for all Computes")
			print("\t> 2. Set per Compute")
		
			while uncore not in range (1,3): 
					uncore = input("\n--> Enter 1-2: (enter for [1]) ")
					if uncore == "":
						uncore = 1
					uncore = int(uncore)
		
		# Same for all computes
		if uncore == 1:
			if fixed:
				cfcvalue = _yorn_float(default_yorn ='N', prompt = self.Menus['CFCVolt'], userin = f"--> Enter CFC Voltage: ")	
				hdcvalue = _yorn_float(default_yorn ='N', prompt = self.Menus['HDCVolt'], userin = f"--> Enter HDC Voltage: ")
				for c in self.computes:
					self.cfc_volt[c] = 	cfcvalue			
					self.hdc_volt[c] =  hdcvalue

			if vbumps:			
				cfcvalue = self.check_vbumps(_yorn_float(default_yorn ='N', prompt = self.Menus['CFCBump'], userin = f"--> Enter CFC vBump: "))
				hdcvalue = self.check_vbumps(_yorn_float(default_yorn ='N', prompt = self.Menus['HDCBump'], userin = f"--> Enter HDC vBump: "))
				for c in self.computes:
					self.cfc_volt[c] =  cfcvalue
					self.hdc_volt[c] =  hdcvalue

		# Selection per compute	
		elif uncore== 2:		
			if fixed:
				for c in self.computes:
					self.cfc_volt[c] = _yorn_float(default_yorn ='N', prompt = self.Menus['CFCVolt'].replace('Uncore CFC Voltage',f'{c.upper()} Uncore CFC Voltage'), userin = f"--> Enter CFC {c.upper()} Voltage: ")					
					self.hdc_volt[c] = _yorn_float(default_yorn ='N', prompt = self.Menus['HDCVolt'].replace('Uncore HDC Voltage',f'{c.upper()} Uncore HDC Voltage'), userin = f"--> Enter HDC {c.upper()} Voltage: ")

			if vbumps:			
				for c in self.computes:
					self.cfc_volt[c] =  self.check_vbumps(_yorn_float(default_yorn ='N', prompt = self.Menus['CFCBump'].replace('Uncore CFC vBump',f'{c.upper()} Uncore CFC vBump'), userin = f"--> Enter CFC {c.upper()} vBump: "))
					self.hdc_volt[c] =  self.check_vbumps(_yorn_float(default_yorn ='N', prompt = self.Menus['HDCBump'].replace('Uncore HDC vBump',f'{c.upper()} Uncore HDC vBump'), userin = f"--> Enter HDC {c.upper()} vBump: "))
		
		## External option 
		elif uncore== 3:	
			for c in self.computes:
				self.cfc_volt[c] =  self.qvbumps_mesh
				self.hdc_volt[c] =  self.qvbumps_mesh if self.core_type == 'bigcore' else self.qvbumps_core

		self.mesh_cfc_volt = self.cfc_volt
		self.mesh_hdc_volt = self.hdc_volt

	def check_vbumps(self, value):
		if value != None:
			while value > 0.2 or value <-0.2:
				try:
					value = float(input(self.Menus['vbumpfix']))	
				except:
					pass
		return value

	def set_frequency(self):

		if self.core_freq == None and self.__FRAMEWORK_FEATURES['core_freq']['enabled']:
			self.core_freq = _yorn_int(default_yorn ='Y', prompt = self.Menus['CoreFreq'], userin = f"--> Enter {self.coremenustring} Frequency: ")
		
		if self.mesh_freq == None and self.__FRAMEWORK_FEATURES['mesh_freq']['enabled']:
			self.mesh_freq = _yorn_int(default_yorn ='Y', prompt = self.Menus['MeshFreq'], userin = "--> Enter CFC/HDC Mesh Frequency: ")
		
		if self.io_freq == None and self.__FRAMEWORK_FEATURES['io_freq']['enabled']:
			self.io_freq = _yorn_int(default_yorn ='Y', prompt = self.Menus['IOFreq'], userin = "--> Enter IO Mesh Frequency: ")

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
		scm.reset_globals()
		scm.global_slice_core=self.targetLogicalCore
		scm.global_fixed_core_freq=self.core_freq
		scm.global_ia_turbo=self.core_freq
		#if flow =='core': scm.global_ia_vf=self.core_freq # Removing this affecting voltage as vf is being flatten on one of the pairs...
		scm.global_fixed_mesh_freq=self.mesh_freq
		scm.global_fixed_io_freq=self.io_freq
		# Voltages Setting the variables but, there is no need for them as how we implemented this
		scm.global_fixed_core_volt=self.core_volt
		scm.global_fixed_cfc_volt=self.mesh_cfc_volt
		scm.global_fixed_hdc_volt=self.mesh_hdc_volt
		scm.global_fixed_cfcio_volt=self.io_cfc_volt
		scm.global_fixed_ddrd_volt=self.ddrd_volt
		scm.global_fixed_ddra_volt=self.ddra_volt
		scm.global_avx_mode = self.license_level
		scm.global_vbumps_configuration=self.vbumps_volt
		scm.global_u600w=self.u600w
		scm.global_boot_extra=",pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=45 "
		# Mesh Specific
		if flow =='mesh': scm.global_ht_dis = self.dis_ht
		scm.global_2CPM_dis = self.dis_2CPM
		if flow =='mesh': scm.global_acode_dis=False # Acode cant be disabled
		if flow =='mesh': scm.global_dry_run = self.dryrun
		# scm.global_avx_mode=license_level   Do this via register method below
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
		
	##Slice Flow Settings
	## TargetLogicalCore: Selected Core to be used in the Slice test
	def setupSliceMode(self):
		# Slice Mode init
		self.slice_init()

		# Core Selection Menu
		self.slice_core(array=self.array, core_dict=self.core_dict)

		# ATE Selection -- Frequency and Voltages, uses DFF for voltage, other IPS will go to safe mode
		self.slice_ate()

		# Fastboot option selection -- Moved to the start of the flow, as we need this to properly set some fuses
		if not self.u600w and self.__FRAMEWORK_FEATURES['fastboot']['enabled']: self.fastboot = _yorn_bool(self.Menus['FASTBOOT'],"Y")

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
		if not self.debug: self.slice_run()

		# Save Configuration to Temp Folder
		self.save_config(file_path=self.defaultSave)

	def slice_run(self):

		# Global Variables configuration
		self.set_globals(flow='core')
		
		slice_mode = scm.System2Tester(target = self.targetLogicalCore, masks = self.masks, boot=True, ht_dis=False, dis_2CPM = self.dis_2CPM, fresh_state= False,fastboot = self.fastboot, ppvc_fuses=self.volt_config)

		slice_mode.setCore()
		
		# Will force refresh after boot to properly load all the nodes after mask changes
		scm.svStatus(refresh=True) #ipc.unlock(); ipc.forcereconfig(); sv.refresh()
		#scm.setCore(targetLogicalCore, boot=True, ht_dis=False, fresh_state= False)
		if (itp.ishalted() == False): 
			try:
				itp.halt()
			except:
				print("--> Unit Can't be halted, problems with ipc...")

		if self.postBootS2T:
			try:
				set_slice(self.cr_array_start, self.cr_array_end, license_level=self.license_level, core_ratio=None, mesh_ratio=None, clear_ucode=self.clear_ucode, dcf_ratio=self.dcf_ratio, halt_pcu=self.halt_pcu)
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

	def slice_init(self):
		self.mode = 'slice'
		self.init_voltage(mode=self.mode)
		scm.svStatus(refresh=False)
		self.init_flow()
		self.masks, self.array = scm.CheckMasks(extMasks=self.extMasks)
		self.core_dict = {f'{key}':{key: value} for key,value in self.array['CORES'].items()}
		
	def slice_core(self, array, core_dict):
		
		
		if self.targetLogicalCore == None and self.__FRAMEWORK_FEATURES['targetLogicalCore']['enabled']:		
			enabledCores = []
				
			# Checks for current System Masks and prints a table with all the availables CORES
			# Mask is also used for 

			printTable (core_dict, header = ['Type', 'Physical ID'], label = f'Each array shows the available physical {self.coremenustring}s for each compute')
				
			# Build a list of all available Cores (Physical)
			for listkeys in array['CORES'].keys():
				enabledCores.extend(array['CORES'][listkeys])
			# Loops the Target Physical Core to be used in Slice MODE: If CORE is disabled in current Mask will not continue.
			while self.targetLogicalCore not in enabledCores:
				try:
					# Checks for Core Status in current System
					self.targetLogicalCore = int(input(self.Menus['TargetCore']))
					#CoreStatus = scm.CheckCore(targetLogicalCore, masks)
					#if CoreStatus == True:
					if self.targetLogicalCore not in enabledCores:
						print (f"\n{bullets} Selected {self.coremenustring} is disabled for this unit please enter a different one as per below table: \n")
						printTable (core_dict, header = ['Type', 'Physical ID'], label = f'Each array shows the available physical {self.coremenustring}s for each compute')
				except:
					pass

			#return self.targetLogicalCore
			
	def slice_ate(self):
		computes = self.computes
		if (self.use_ate_freq and self.__FRAMEWORK_FEATURES['use_ate_freq']['enabled']):		
			yorn = ""
			yornv = ""
			vdata = []
			print (f"\n{bullets} Want to set {self.coremenustring} Frequency via ATE frequency method?: i.e.  {self.ATE_CORE_FREQ}?")
			while "N" not in yorn and "Y" not in yorn:
				yorn = input('--> Y / N (enter for [Y]): ').upper()
				if yorn == "": yorn = "Y"
			if yorn == "Y":
				self.ate_data(mode= 'slice')
				#print(f"\n{bullets} GNR Core frequencies are:")
				#freq_dict = {f'F{key}':{key: value} for key,value in stc.CORE_FREQ.items()}
				#printTable (freq_dict, header = ['Core Frequency', 'Value'], label = 'Multiple freqs are FLOWID 1-4')
				#print ("F1 == 8 F2 == 17 F3 == 24 F4 = 32 F5 == 38-36-34-32 F6: 40-38-36-34 F7:42-40-38-36 ( Multiple freqs are FLOWID 1-4 )")
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
				self.core_freq, self.mesh_freq, self.io_freq = stc.get_ratios_core(ate_freq, self.flowid)
				# More variability in testing conditions after selecting ATE
				print(f"\n{bullets} Setting system with ATE configuration: {self.coremenustring.upper()}: { self.core_freq}, CFCCOMP: { self.mesh_freq}, CFCIO:{ self.io_freq}")

				#if (use_ate_volt):
				print (f"\n{bullets} Want to set Voltage based on ATE Frequency selection F{ate_freq}?")
				while "N" not in yornv and "Y" not in yornv:
					yornv = input('--> Y / N (enter for [N]): ').upper()
					if yornv == "": yornv = "N"
				if yornv == "Y":

					VID = str(input(f"{self.Menus['UnitVID']}"))
					
					# Function to collect DFF Data -- CORE
					self.slice_ate_type(VID, ate_freq)
					
					#try:
					#	vdata = stc.get_voltages_core(visual=VID, core = self.targetLogicalCore, ate_freq=f'F{ate_freq}', hot=True)
					#	if self.core_type == 'atomcore': vdata_l2 = stc.get_voltages_uncore(visual=VID, ate_freq=f'F{ate_freq}', hot=True)

					#	voltlic = None
					#	#vdatalen = len(vdata)
					#	while voltlic not in self.core_license_levels:
					#		if not vdata: break
					#		voltlic = str(input(f"Select License from {self.core_license_levels} :"))
					#		if voltlic not in self.core_license_levels:
					#			print(f'--> Selected License Value not valid, use: {self.core_license_levels}')
					#		else: 
					#			
					#			self.license_level = self.core_license_dict[voltlic]
					#			print(f'--> Setting {self.coremenustring} License to: {self.license_dict[self.license_level]}')

					#	self.core_volt = stc.filter_core_voltage(data=vdata, lic=voltlic, core = self.targetLogicalCore, ate_freq=f'F{ate_freq}')
					#	if self.core_type == 'atomcore': 
					#		hdc_volt = {c:stc.filter_uncore_voltage(data=vdata_l2, ip='HDC', die= c.upper(), ate_freq=f'F{ate_freq}') for c in computes}
						
					#except:
					#	print(f'!!! Failed collecting DFF Data for {VID}, enter value manually or use system default')
					#	self.core_volt = _yorn_float(default_yorn ='Y', prompt = self.Menus['CoreVolt'], userin = f"--> Enter {self.coremenustring} Voltage: ")
					#	if self.core_type == 'atomcore':
					#		for c in computes:
					#			self.hdc_volt[c] =  _yorn_float(default_yorn ='Y', prompt = self.Menus['HDCVolt'].replace('Uncore HDC Voltage',f'{c.upper()} Uncore HDC Voltage'), userin = f"--> Enter HDC {c.upper()} voltage: ")
					    						
					#if not vdata:
					#	print(f'!!! Empty DFF Data for {VID}, check if data is at your site, enter value manually or use system default')
					#	self.core_volt = _yorn_float(default_yorn ='Y', prompt = self.Menus['CoreVolt'], userin = f"--> Enter {self.coremenustring} Voltage: ")
					#	if self.core_type == 'atomcore':
					#		for c in computes:
					#			self.hdc_volt[c] =  _yorn_float(default_yorn ='Y', prompt = self.Menus['HDCVolt'].replace('Uncore HDC Voltage',f'{c.upper()} Uncore HDC Voltage'), userin = f"--> Enter HDC {c.upper()} voltage: ")
					#
					#cfc_volt = {c:stc.All_Safe_RST_CDIE['VCFC_CDIE_RST'] for c in computes}
					#if self.core_type == 'bigocre': hdc_volt = {c:stc.All_Safe_RST_CDIE['VHDC_RST'] for c in computes}					

					#self.mesh_cfc_volt = cfc_volt
					#self.mesh_hdc_volt = hdc_volt
					##self.io_cfc_volt = stc.All_Safe_RST_PKG['VCFC_IO_RST']
					#self.ddrd_volt = stc.All_Safe_RST_CDIE['VDDRD_RST']
					#self.ddra_volt = stc.All_Safe_RST_CDIE['VDDRA_RST']
					
					#if self.core_type == 'atomcore':
					#	print(f'\n{bullets} Using Safe Voltages for CFC:{self.mesh_cfc_volt}, CFC_IO: {self.io_cfc_volt}, DDRD: {self.ddrd_volt} --')
					#	print(f'\n{bullets} Using ATE MESH CFC Voltage --- {self.mesh_cfc_volt} --')		
					#	print(f'\n{bullets} Setting {self.coremenustring} Voltage to {self.core_volt if self.core_volt != None else "System Value"} --')
	
					#else:
					#	print(f'\n{bullets} Using Safe Voltages for CFC:{self.mesh_cfc_volt}, HDC: {self.mesh_hdc_volt}, CFC_IO: {self.io_cfc_volt}, DDRD: {self.ddrd_volt} --')
					#	print(f'\n{bullets} Setting {self.coremenustring} Voltage to {self.core_volt if self.core_volt != None else "System Value"} --')
				else:
					print(f'\n{bullets} Using System Default voltage configuration --')
					
				if self.core_volt: self.use_ate_volt = True
				
				ATEChange = _yorn_bool(self.Menus['ATE_Change'],"N")
				if ATEChange:
    				
					if self.HDC_AT_CORE: meshf = _yorn_int(default_yorn ='N', prompt = self.Menus['MeshFreq'], userin = "--> Enter CFC Mesh Frequency: ")
					else: meshf = _yorn_int(default_yorn ='N', prompt = self.Menus['MeshFreq'], userin = "--> Enter CFC/HDC Mesh Frequency: ")
					
					#coref = _yorn_int(default_yorn ='N', prompt = self.Menus['CoreFreq'], userin = "--> Enter Core Frequency: ")
					iof = _yorn_int(default_yorn ='N', prompt = self.Menus['IOFreq'], userin = "--> Enter IO Mesh Frequency: ")
					#if meshf != None:  mesh_freq = meshf
					if meshf != None:  self.mesh_freq = meshf
					if iof != None:  self.io_freq = iof
					print(f"\n{bullets} Updated configuration: {self.coremenustring.upper()}: {self.core_freq}, CFCCOMP: {self.mesh_freq}, CFCIO:{self.io_freq}")

			#return core_freq, mesh_freq, io_freq, mesh_cfc_volt, mesh_hdc_volt, io_cfc_volt, ddrd_volt, use_ate_volt

	def slice_ate_type(self, VID, ate_freq):
		computes = self.computes

		# Will start collecting Data based on VID info, if fails will ask for manual inputs
		try:
			vdata = stc.get_voltages_core(visual=VID, core = self.targetLogicalCore, ate_freq=f'F{ate_freq}', hot=True)
			if self.HDC_AT_CORE: vdata_l2 = stc.get_voltages_uncore(visual=VID, ate_freq=f'F{ate_freq}', hot=True)

			voltlic = None
			#vdatalen = len(vdata)
			while voltlic not in self.core_license_levels:
				if not vdata: break
				voltlic = str(input(f"Select License from {self.core_license_levels} :"))
				if voltlic not in self.core_license_levels:
					print(f'--> Selected License Value not valid, use: {self.core_license_levels}')
				else: 
							
					self.license_level = self.core_license_dict[voltlic]
					print(f'--> Setting {self.coremenustring} License to: {self.license_dict[self.license_level]}')

			self.core_volt = stc.filter_core_voltage(data=vdata, lic=voltlic, core = self.targetLogicalCore, ate_freq=f'F{ate_freq}')
			
			## Modifies 
			if self.HDC_AT_CORE: 
				hdc_volt = {c:stc.filter_uncore_voltage(data=vdata_l2, ip='HDC', die= c.upper(), ate_freq=f'F{ate_freq}') for c in computes}
						
		except Exception as e:
			print(f'!!! Failed collecting DFF Data for {VID}, enter value manually or use system default')
			print(f'Execption -- {e}')
			self.core_volt = _yorn_float(default_yorn ='Y', prompt = self.Menus['CoreVolt'], userin = f"--> Enter {self.coremenustring} Voltage: ")
			if self.HDC_AT_CORE:
				for c in computes:
					self.hdc_volt[c] =  _yorn_float(default_yorn ='Y', prompt = self.Menus['HDCVolt'].replace('Uncore HDC Voltage',f'{c.upper()} Uncore HDC Voltage'), userin = f"--> Enter HDC {c.upper()} voltage: ")
					    						
		if not vdata:
			print(f'!!! Empty DFF Data for {VID}, check if data is at your site, enter value manually or use system default')
			self.core_volt = _yorn_float(default_yorn ='Y', prompt = self.Menus['CoreVolt'], userin = f"--> Enter {self.coremenustring} Voltage: ")
				
			if self.HDC_AT_CORE:
				for c in computes:
					self.hdc_volt[c] =  _yorn_float(default_yorn ='Y', prompt = self.Menus['HDCVolt'].replace('Uncore HDC Voltage',f'{c.upper()} Uncore HDC Voltage'), userin = f"--> Enter HDC {c.upper()} voltage: ")

				
		
		cfc_volt = {c:stc.All_Safe_RST_CDIE['VCFC_CDIE_RST'] for c in computes}
		if not self.HDC_AT_CORE: hdc_volt = {c:stc.All_Safe_RST_CDIE['VHDC_RST'] for c in computes}

		self.mesh_cfc_volt = cfc_volt
		self.mesh_hdc_volt = hdc_volt
		#self.io_cfc_volt = stc.All_Safe_RST_PKG['VCFC_IO_RST']
		self.ddrd_volt = stc.All_Safe_RST_CDIE['VDDRD_RST']
		self.ddra_volt = stc.All_Safe_RST_CDIE['VDDRA_RST']
					
		if self.HDC_AT_CORE:
			print(f'\n{bullets} Using Safe Voltages for CFC:{self.mesh_cfc_volt}, CFC_IO: {self.io_cfc_volt}, DDRD: {self.ddrd_volt} --')
			print(f'\n{bullets} Using ATE MESH HDC Voltage --- {self.mesh_hdc_volt} --')		
			print(f'\n{bullets} Setting {self.coremenustring} Voltage to {self.core_volt if self.core_volt != None else "System Value"} --')
	
		else:
			print(f'\n{bullets} Using Safe Voltages for CFC:{self.mesh_cfc_volt}, HDC: {self.mesh_hdc_volt}, CFC_IO: {self.io_cfc_volt}, DDRD: {self.ddrd_volt} --')
			print(f'\n{bullets} Setting {self.coremenustring} Voltage to {self.core_volt if self.core_volt != None else "System Value"} --')
	    	
	def slice_registers(self):
		#reg_select = None
		#cr_array_start=0 
		#cr_array_end=0xffff
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

	def slice_end(self):
		print ("\n----------------------------------------------------------------")
		print ("\tUnit Tileview")
		print ("----------------------------------------------------------------\n")
		scm.coresEnabled(rdfuses=False)
		print ("\n----------------------------------------------------------------")
		print ("\tConfiguration Summary")
		print ("----------------------------------------------------------------\n")
		print ("\t> Booted to physical %s: %d" % (self.coremenustring, self.targetLogicalCore))
		if self.core_freq != None: print ("\t> %s Freq = %d" % (self.coremenustring,self.core_freq))
		if self.mesh_freq != None: print ("\t> Mesh Freq = %d" % self.mesh_freq)
		if self.io_freq != None: print ("\t> IO Freq = %d" % self.io_freq)
		if self.dis_acode: print("\t> ACODE disabled")
		if self.dis_2CPM: print(f"\t> Booted with 2 Cores per Module -> Fuse Config: {self.dis_2CPM}")
		if self.ppvc_fuses: print("\t> PPV Condition fuses set")
		if self.custom_volt: print("\t> Custom Fixed Voltage fuses set")
		if self.vbumps_volt: print("\t> Voltage Bumps fuses set")
		if self.use_ate_volt: print("\t> ATE Fixed Voltage fuses set")
		if self.core_volt != None: print ("\t> %s Volt = %f" % (self.coremenustring, self.core_volt))		
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
			print("Rerun this config without prompt: s2t.Configs(), default save path: C:\Temp\System2TesterRun.json")
			print(f"Configuration File located at {self.defaultSave}")
			# Removing it for now
			#print("Build this configuration without prompt using: s2tconfig = s2t.S2TFlow(targetLogicalCore=%d, use_ate_freq=False, core_freq=%d, mesh_freq=%d, license_level=%d, dcf_ratio=%d, mesh_cfc_volt = %d, mesh_hdc_volt = %d, io_cfc_volt = %d, ddrd_volt = %d, core_volt = %d,)"  % (self.targetLogicalCore, self.core_freq, self.mesh_freq, self.license_level, self.dcf_ratio, self.mesh_cfc_volt, self.mesh_hdc_volt, self.io_cfc_volt, self.ddrd_volt, self.core_volt))
			#print("Run command: s2tconfig.setupSliceMode()")
		
		## Displays on console VVAR Configuration for selected mode
		vvars_call(slice = True, logCore=self.targetLogicalCore, corestring=self.coremenustring)
		scm.svStatus()

	##Mesh Flow Settings
	## Target: Selected Mesh Configuration mode
	def setupMeshMode(self):
		self.mesh_init()
		
		# Asks for ATE Mesh configuration, frequency and voltage
		self.mesh_ate()

		# Asks for mesh configuration selection: ATE Masks, Custom, Tiles
		self.mesh_configuration()

		# Fastboot option selection (To be used only in Full Chip mode to apply configuration fuses)
		if self.targetTile == 4: 
			if not self.u600w: 
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
		if not self.debug: self.mesh_run()

		# Save Configuration to Temp Folder
		self.save_config(file_path=self.defaultSave)

	def mesh_run(self):
		
		#Set Globals before calling the S2T Script flow
		self.set_globals(flow='mesh')

		## Call the appropita script based on the selected mode
		mesh = scm.System2Tester(target= self.target, masks = self.masks, boot = True, ht_dis = self.dis_ht, dis_2CPM = self.dis_2CPM, fresh_state = False, readFuse = True, clusterCheck = self.clusterCheck,fastboot = self.fastboot, ppvc_fuses=self.volt_config)
		
		if self.targetTile == 1:
			mesh.setmesh(boot_postcode=self.boot_postcode,stop_after_mrc=self.stop_after_mrc, lsb = self.lsb, extMasks=self.extMasks)
			#scm.System2Tester(targetConfig= ate_config, ht_dis=dis_ht, stop_after_mrc=stop_after_mrc, fresh_state=False)
			
		elif self.targetTile == 2:
			mesh.setTile(boot_postcode=self.boot_postcode,stop_after_mrc=self.stop_after_mrc)
			#scm.setTile(targetTile = compute_list, ht_dis=dis_ht, stop_after_mrc=stop_after_mrc, fresh_state=False)
		
		elif self.targetTile == 3:
			mesh.setmesh(CustomConfig = self.custom_list, boot_postcode=self.boot_postcode,stop_after_mrc=self.stop_after_mrc, lsb = self.lsb, extMasks=self.extMasks)

		elif self.targetTile == 4:
			mesh.setfc(extMasks = self.extMasks, boot_postcode=self.boot_postcode,stop_after_mrc=self.stop_after_mrc)
			#if self.fastboot:
				#mesh._fastboot(stop_after_mrc=self.stop_after_mrc, pm_enable_no_vf=False)
			#else:
				#mesh._doboot(stop_after_mrc=self.stop_after_mrc, pm_enable_no_vf=False)

		# Will force refresh after boot to properly load all the nodes after mask changes
		scm.svStatus(refresh=True) # ipc.unlock(); ipc.forcereconfig(); sv.refresh()
		
		if (itp.ishalted() == False): 
			try:
				itp.halt()
			except:
				print("--> Unit Can't be halted, problems with ipc...")

		if self.fix_apic:
			#print('\n --- Continuing boot moving EFI ---\n')
			tester_apic_id()
			scm.go_to_efi()

		## Reorder APIC to be applied on MRC Postcode, removing it from below set mesh
		if self.postBootS2T:
			try:
				set_mesh(self.cr_array_start, self.cr_array_end, license_level=self.license_level, core_ratio=None, mesh_ratio=None, reorder_apic=False, clear_ucode=self.clear_ucode,dcf_ratio=self.dcf_ratio, halt_pcu=self.halt_pcu, mlcways=self.mlcways)
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

	def mesh_init(self):
		self.mode = 'mesh'
		self.init_voltage(mode=self.mode)
		scm.svStatus(refresh=False)
		self.init_flow()
		self.masks, self.array = scm.CheckMasks(extMasks=self.extMasks)
		#print(self.masks)
					
	def mesh_ate(self):
		computes = self.computes
		if (self.use_ate_freq):
			yorn = ""
			yornv = ""
			vdata = []
			print (f"\n{bullets} Want to set CFC Frequency via ATE frequency method?: i.e. {self.ATE_MESH_FREQ}?")
			while "N" not in yorn and "Y" not in yorn:
				yorn = input('--> Y / N (enter for [Y]): ').upper()
				if yorn == "": yorn = "Y"
			if yorn == "Y":
				self.ate_data(mode = 'mesh')

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
				self.core_freq, self.mesh_freq, self.io_freq = stc.get_ratios_uncore(ate_freq, self.flowid)
				print(f"\n{bullets} Setting system with ATE configuration: {self.coremenustring}: { self.core_freq}, CFCCOMP: { self.mesh_freq}, CFCIO:{ self.io_freq}")

				#if (use_ate_volt):
				print (f"\n{bullets} Want to set Voltage based on ATE Frequency selection F{ate_freq}?")
				while "N" not in yornv and "Y" not in yornv:
					yornv = input('--> Y / N (enter for [N]): ').upper()
					if yornv == "": yornv = "N"
				if yornv == "Y":

					VID = str(input(f"{self.Menus['UnitVID']}"))
					self.mesh_ate_type(VID, ate_freq)	
				#	try:
				#		vdata = stc.get_voltages_uncore(visual=VID, ate_freq=f'F{ate_freq}', hot=True)
				#		#vdatalen = len(vdata)
				#		self.cfc_volt = {c:stc.filter_uncore_voltage(data=vdata, ip='CFC', die=c.upper(), ate_freq=f'F{ate_freq}') for c in computes}
				#		if self.core_type == 'bigcore': 
				#			self.hdc_volt = {c:stc.filter_uncore_voltage(data=vdata, ip='HDC', die=c.upper(), ate_freq=f'F{ate_freq}') for c in computes}
				#		else:
				#			self.hdc_volt = stc.All_Safe_RST_PKG['VHDC_RST']

				#	except:
				#		print(f'!!! Failed collecting DFF Data for {VID}, enter value manually or use system default')
				#		for c in computes:
				#			self.cfc_volt[c] =  _yorn_float(default_yorn ='Y', prompt = self.Menus['CFCVolt'].replace('Uncore CFC Voltage',f'{c.upper()} Uncore CFC Voltage'), userin = f"--> Enter CFC {c.upper()} voltage: ")
				#			if self.core_type == 'bigcore': self.hdc_volt[c] =  _yorn_float(default_yorn ='Y', prompt = self.Menus['HDCVolt'].replace('Uncore HDC Voltage',f'{c.upper()} Uncore HDC Voltage'), userin = f"--> Enter HDC {c.upper()} voltage: ")

				
				#	if not vdata:
				#		print(f'!!! Empty DFF Data for {VID}, check if data is at your site, enter value manually or use system default')
				#		for c in computes:
				#			self.cfc_volt[c] =  _yorn_float(default_yorn ='Y', prompt = self.Menus['CFCVolt'].replace('Uncore CFC Voltage',f'{c.upper()} Uncore CFC Voltage'), userin = f"--> Enter CFC {c.upper()} voltage: ")
				#			if self.core_type == 'bigcore': self.hdc_volt[c] =  _yorn_float(default_yorn ='Y', prompt = self.Menus['HDCVolt'].replace('Uncore HDC Voltage',f'{c.upper()} Uncore HDC Voltage'), userin = f"--> Enter HDC {c.upper()} voltage: ")
					
				#	self.core_volt = stc.All_Safe_RST_PKG['VCORE_RST']
				#	#self.mesh_hdc_volt = stc.All_Safe_RST_PKG['VHDC_RST']
				#	self.io_cfc_volt = stc.All_Safe_RST_PKG['VCFC_IO_RST']
				#	self.ddrd_volt = stc.All_Safe_RST_PKG['VDDRD_RST']
				#	self.ddra_volt = stc.All_Safe_RST_PKG['VDDRA_RST']

				#	self.mesh_cfc_volt = self.cfc_volt
				#	self.mesh_hdc_volt = self.hdc_volt

				#	if self.core_type == 'bigcore':
				#		print(f'\n{bullets} Using ATE Safe Voltages    --- {self.coremenustring.upper()}:{self.core_volt}, CFC_IO: {self.io_cfc_volt}, DDRD: {self.ddrd_volt} --')
				#		print(f'\n{bullets} Using ATE MESH CFC Voltage --- {self.mesh_cfc_volt} --')
				#		print(f'\n{bullets} Using ATE MESH HDC Voltage --- {self.mesh_hdc_volt} --')
				#	else:
				#		print(f'\n{bullets} Using ATE Safe Voltages    --- {self.coremenustring.upper()}:{self.core_volt},HDC(L2):{self.mesh_hdc_volt}, CFC_IO: {self.io_cfc_volt}, DDRD: {self.ddrd_volt} --')
				#		print(f'\n{bullets} Using ATE MESH CFC Voltage --- {self.mesh_cfc_volt} --')
						
				else:
					print(f'\n{bullets} Using System Default voltage configuration --')
					
				if self.mesh_cfc_volt: self.use_ate_volt = True

				# More variability in testing conditions after selecting ATE
				ATEChange = _yorn_bool(self.Menus['ATE_Change'],"N")
				if ATEChange:
					#meshf = _yorn_int(default_yorn ='N', prompt = self.Menus['MeshFreq'], userin = "--> Enter CFC/HDC Mesh Frequency: ")
					coref = _yorn_int(default_yorn ='N', prompt = self.Menus['CoreFreq'], userin = f"--> Enter {self.coremenustring} Frequency: ")
					iof = _yorn_int(default_yorn ='N', prompt = self.Menus['IOFreq'], userin = "--> Enter IO Mesh Frequency: ")
					#if meshf != None:  mesh_freq = meshf
					if coref != None:  self.core_freq = coref
					if iof != None:   self.io_freq = iof
					print(f"\n{bullets} Updated configuration: {self.coremenustring.upper()}: { self.core_freq}, CFCCOMP: { self.mesh_freq}, CFCIO:{ self.io_freq}")

	def mesh_ate_type(self, VID, ate_freq):
		computes = self.computes
					
		try:
			vdata = stc.get_voltages_uncore(visual=VID, ate_freq=f'F{ate_freq}', hot=True)
			#vdatalen = len(vdata)
			self.cfc_volt = {c:stc.filter_uncore_voltage(data=vdata, ip='CFC', die=c.upper(), ate_freq=f'F{ate_freq}') for c in computes}
			
			if not self.HDC_AT_CORE: 
				self.hdc_volt = {c:stc.filter_uncore_voltage(data=vdata, ip='HDC', die=c.upper(), ate_freq=f'F{ate_freq}') for c in computes}
			

		except:
			print(f'!!! Failed collecting DFF Data for {VID}, enter value manually or use system default')
			for c in computes:
				
				self.cfc_volt[c] =  _yorn_float(default_yorn ='Y', prompt = self.Menus['CFCVolt'].replace('Uncore CFC Voltage',f'{c.upper()} Uncore CFC Voltage'), userin = f"--> Enter CFC {c.upper()} voltage: ")
				
				if not self.HDC_AT_CORE: 
					self.hdc_volt[c] =  _yorn_float(default_yorn ='Y', prompt = self.Menus['HDCVolt'].replace('Uncore HDC Voltage',f'{c.upper()} Uncore HDC Voltage'), userin = f"--> Enter HDC {c.upper()} voltage: ")

		if not vdata:
			print(f'!!! Empty DFF Data for {VID}, check if data is at your site, enter value manually or use system default')
			for c in computes:
				self.cfc_volt[c] =  _yorn_float(default_yorn ='Y', prompt = self.Menus['CFCVolt'].replace('Uncore CFC Voltage',f'{c.upper()} Uncore CFC Voltage'), userin = f"--> Enter CFC {c.upper()} voltage: ")
				
				if not self.HDC_AT_CORE: 
					self.hdc_volt[c] =  _yorn_float(default_yorn ='Y', prompt = self.Menus['HDCVolt'].replace('Uncore HDC Voltage',f'{c.upper()} Uncore HDC Voltage'), userin = f"--> Enter HDC {c.upper()} voltage: ")
					
		self.core_volt = stc.All_Safe_RST_PKG['VCORE_RST']
		if self.HDC_AT_CORE: self.mesh_hdc_volt = stc.All_Safe_RST_PKG['VHDC_RST']
		self.io_cfc_volt = stc.All_Safe_RST_PKG['VCFC_IO_RST']
		self.ddrd_volt = stc.All_Safe_RST_PKG['VDDRD_RST']
		self.ddra_volt = stc.All_Safe_RST_PKG['VDDRA_RST']

		self.mesh_cfc_volt = self.cfc_volt
		self.mesh_hdc_volt = self.hdc_volt

		if self.core_type == 'bigcore':
			print(f'\n{bullets} Using ATE Safe Voltages    --- {self.coremenustring.upper()}:{self.core_volt}, CFC_IO: {self.io_cfc_volt}, DDRD: {self.ddrd_volt} --')
			print(f'\n{bullets} Using ATE MESH CFC Voltage --- {self.mesh_cfc_volt} --')
			print(f'\n{bullets} Using ATE MESH HDC Voltage --- {self.mesh_hdc_volt} --')
		else:
			print(f'\n{bullets} Using ATE Safe Voltages    --- {self.coremenustring.upper()}:{self.core_volt},HDC(L2):{self.mesh_hdc_volt}, CFC_IO: {self.io_cfc_volt}, DDRD: {self.ddrd_volt} --')
			print(f'\n{bullets} Using ATE MESH CFC Voltage --- {self.mesh_cfc_volt} --')
						
	def mesh_configuration(self):
		
		# Init Variables
		ate_mask = 0
		computes =self.computes
		#compute = ''
		#custom = ''
		#flowid = 1
		print(f'\n{bullets} System 2 Tester MESH Available Configurations: ')
		self.print_menu(menu=self.ate_config_main)
		
		if self.targetTile == None:
			self.targetTile = int(input("--> Enter Configuration: "))

		if self.targetTile == 1:
			print(f'\n{bullets} Enter ATE Class mask configuration:')
			self.print_menu(menu=self.ate_config_product)
			maxrng = self.ate_config_product['maxrng']

		
			
			while ate_mask not in range (1,maxrng):
				ate_config = ''
				try:
					ate_mask = int(input("--> ATE Pass mask to be used: "))
					ate_config = self.ate_masks[ate_mask]
		#				
		#			if XCC and ate_mask > 2:	
		#				ate_maskxcc = ate_mask + 1
		#			else: 
		#				ate_maskxcc = ate_mask
		#			
		#			if ate_maskxcc in self.ate_masks.keys():
		#				ate_config = self.ate_masks[ate_maskxcc]
		#			#target = ate_config
				except:
					pass
				
				self.target = ate_config
		

		# Need to check how to user input a list
		elif self.targetTile == 2:
			invalid = True
			print(f'\n{bullets} Valid input values for Compute mode are: {computes}')
			while invalid:
				input_str = str(input("--> Enter Compute(s) name splitted by comma: "))
				compute_list = input_str.lower().strip(' ').split(',')
				invalid = [val for val in compute_list if val not in computes]
				if invalid:
					print(f'--> Not valid values entered please check: {invalid}')
			self.target = compute_list
		

		## Check for the Custom configuration in X2
		elif self.targetTile == 3:
			invalid = True
			self.target = 'Custom'
			print(f'\n{bullets} Valid input values for Custom mode are: {self.customs}')
			while invalid:
				input_str = str(input("--> Enter Column(s)/Row(s) name splitted by comma:"))
				self.custom_list = input_str.upper().strip(' ').split(',')
				#USE Lower for the string no need to match cases
				#customs_upper = [s.upper() for s in customs]
				invalid = [val for val in self.custom_list if val not in self.customs]
				if invalid:
					print(f'--> Not valid values entered please check: {invalid}')

	def mesh_misc(self):

		if self.mlcways == None and self.__FRAMEWORK_FEATURES['mlcways']['enabled']:
			self.mlcways = _yorn_bool(self.Menus['MLC'],"N")
		if self.dis_ht == None and self.__FRAMEWORK_FEATURES['dis_ht']['enabled']:
			self.dis_ht = _yorn_bool(self.Menus['HTDIS'],"Y" if self.targetTile != 4 else "N")
		if self.dis_2CPM == None and self.__FRAMEWORK_FEATURES['dis_2CPM']['enabled']:
			_dis_2cpm = _yorn_bool(self.Menus['DIS2CPM'],"Y" if self.targetTile != 4 else "N")
			
			if _dis_2cpm:
				self.dis2CPM()
				
		if self.fix_apic == None and self.__FRAMEWORK_FEATURES['fix_apic']['enabled']:
			self.fix_apic = _yorn_bool(self.Menus['APICS'],"N")
			if self.fix_apic: self.stop_after_mrc = True

		if self.boot_postcode == None and self.__FRAMEWORK_FEATURES['boot_postcode']['enabled']:
			self.boot_postcode_break = _yorn_int(default_yorn ='N', prompt = self.Menus['BOOT_BREAK'], userin = "--> Enter Hex Value of Breakpoint: ")
			if self.boot_postcode_break != None:
				self.boot_postcode = True

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
		self.print_menu(menu=DIS2CPM_MENU['main'])
		maxrng = DIS2CPM_MENU['main']['maxrng']
			
		while _2cpm not in range (1,maxrng):
			_2cpm = ''
			try:
				_2cpm = int(input("--> Core disable selection to be used: "))
				self.dis_2CPM = self.dis2cpm_dict[_2cpm]  
			except:
				pass  

	def mesh_registers(self):
		#reg_select = None
		#cr_array_start=0 
		#cr_array_end=0xffff
		if self.reg_select == None and self.__FRAMEWORK_FEATURES['reg_select']['enabled']:
    
			print(f"\n{bullets} Set tester registers? ") 
			print("\t> 1. No")
			print("\t> 2. Yes - Set all the regs")
			print("\t> 3. Yes - Set a subset of the regs")
			#print("\t> 3. Yes - Set a subset of the regs")
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
		
	def mesh_end(self):
		print ("\n----------------------------------------------------------------")
		print ("\tUnit Tileview")
		print ("----------------------------------------------------------------\n")
		scm.coresEnabled(rdfuses=False)
		print ("\n----------------------------------------------------------------")
		print ("\tConfiguration Summary")
		print ("----------------------------------------------------------------\n")
		print ("\t> Unit Booted using pseudo configuration: %s" % self.target)
		if self.core_freq != None: print ("\t> %s Freq = %d" % (self.coremenustring, self.core_freq))
		if self.mesh_freq != None: print ("\t> Mesh Freq = %d" % self.mesh_freq)
		if self.io_freq != None: print ("\t> IO Freq = %d" % self.io_freq)
		if self.dis_acode: print("\t> ACODE disabled")
		if self.dis_ht: print("\t> Hyper Threading disabled")
		if self.dis_2CPM: print(f"\t> Booted with 2 Cores per Module -> Fuse Config: {self.dis_2CPM}")
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
			print("Rerun this config without prompt: s2t.Configs(), default save path: C:\Temp\System2TesterRun.json")
			print(f"Configuration File located at {self.defaultSave}")
			#print("Rerun this config without prompt: s2t.setupSliceMode(targetLogicalCore=%d, use_ate_freq=False, core_freq=%d, mesh_freq=%d, license_level=%d, dcf_ratio=%d)"  % (targetLogicalCore, core_freq, mesh_freq, license_level, dcf_ratio))
		
		vvars_call(slice = False, logCore=None, corestring=self.coremenustring)
		scm.svStatus()

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
					2:0x1000002,
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
	product = SELECTED_PRODUCT
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
	#sv.refresh()
	
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

	print ("\nSetting %d CRs " % num_crs)
	index = 0
	for n in sorted(crarray):
	# for n in (crarray):
		
		if (index not in skip_index_array) and (index >= cr_array_start) and (index<=cr_array_end):

			if 'thread' in n:

				
				threads = len(sv.sockets.cpu.cores[0].threads)
				if threads == 1 and 'thread1' in n:
					print ("%d: !!!! skipping %s, single thread is configured" % (index, n)  )
					continue
				value = sv.sockets.cpu.cores[0].get_by_path(n).read()
				sv.socket0.computes.cpu.cores.get_by_path(n).write(crarray[n])

				print("TAP -- | {}:{} Changed from :{}: -> :{}: ".format(index, n, value, hex(crarray[n])))
			else:
				cr_write_ipc(index, n, crarray)
				print("IPC -- | {}:{}({})={}".format(index, n,hex(_s2t_dict[n]['cr_offset']),hex(crarray[n])))
		else:
			print ("%d: !!!! skipping %s" % (index, n)  )
		index +=1

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

	print ("Setting %d CRs " % num_crs)
	index = 0
	for n in sorted(crarray):
	# for n in (crarray):
		
		if (index not in skip_index_array) and (index >= cr_array_start) and (index<=cr_array_end):
			# print ("%d:%s: itp.crb64(0x%x, 0x%x)" % (index, n, _s2t_dict[n], crarray[n]))
			
			
			threads = len(sv.sockets.cpu.cores[0].threads)
			if threads == 1 and 'thread1' in n:
				print ("%d: !!!! skipping %s, single thread is configured" % (index, n)  )
				continue
			
			value = sv.socket0.compute0.cpu.cores[0].get_by_path(n)
			sv.socket0.computes.cpu.cores.get_by_path(n).write(crarray[n])
			time.sleep(0.5)	
			mcchk = sv.socket0.compute0.cpu.cores[0].ml2_cr_mc3_status
		
			if mcchk != 0:
				print(f'sv.socket0.cpu.core0.ml2_cr_mc3_status = {mcchk}')
				print(f"{index}: {n} - Failing the unit add to skip --")
				break
			print("{}:{} Changed from :{}: -> :{}: ".format(index, n, value, hex(crarray[n])))

		else:
			print ("%d: !!!! skipping %s" % (index, n)  )
		index +=1

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
	for key in _seldict[seldict].keys():
		regfound = sv.socket0.cpu.get_by_path(f'core{core}').thread0.search(key)
		#print(regfound)
		if key in regfound:
			data = sv.socket0.cpu.get_by_path(f'core{core}').thread0.get_by_path(key).info
			value = sv.socket0.cpu.get_by_path(f'core{core}').thread0.get_by_path(key).read()
			#print(f'{key} : cr_offset = {data['cr_offset']}, numbits = {data['numbits']}')
			#for keydata, value in data.items():
			#    _crd[key][keydata] = value
			#    print(f'thread0.{key} : {value}')
		else:
			data = sv.socket0.cpu.get_by_path(f'core{core}').get_by_path(key).info
			value = sv.socket0.cpu.get_by_path(f'core{core}').get_by_path(key).read()
			#print(data)
		_crd[regsname[seldict]][key] = {'description':data['description'],
										'cr_offset':data['cr_offset'], 
										'numbits':data['numbits'],} # Use below entries to build initial s2tregs main file, not needed for the rest.
										#'desired_value':hex(_seldict[seldict][key]),
										#'ref_value': hex(value)}
		print(f"{key} : cr_offset = {data['cr_offset']}, numbits = {data['numbits']}, desired_value = {_seldict[seldict][key]} -- {value}")
			#for keydata, value in data.items():
			#    _crd[key][keydata] = value
			#    print(f'{key} : {value}')
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
	for key in _seldict[seldict].keys():
		regfound = sv.socket0.cpu.get_by_path(f'core{core}').thread0.search(key)
		#print(regfound)
		if key in regfound:

			value = sv.socket0.cpu.get_by_path(f'core{core}').thread0.get_by_path(key).read()
			#print(f'{key} : cr_offset = {data['cr_offset']}, numbits = {data['numbits']}')
			#for keydata, value in data.items():
			#    _crd[key][keydata] = value
			#    print(f'thread0.{key} : {value}')
		else:

			value = sv.socket0.cpu.get_by_path(f'core{core}').get_by_path(key).read()
			#print(data)

		print(f"{key} : desired_value = {hex(_seldict[seldict][key])} -- {value}")

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
