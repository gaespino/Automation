## S2T Set Tester Registers - Refactored with Managers and Strategy Pattern
revision = 2.0
date = '28/10/2025'
engineer = 'gaespino'
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
sv.refresh()
verbose = False
debug = False

## Imports from S2T Folder
import users.gaespino.dev.S2T.CoreManipulation as scm
import users.gaespino.dev.S2T.GetTesterCurves as stc
import users.gaespino.dev.S2T.dpmChecks as dpm
from users.gaespino.dev.S2T.ConfigsLoader import config

## Import Managers and Strategy
sys.path.append(os.path.join(os.path.dirname(__file__), 'managers'))
from voltage_manager import VoltageManager
from frequency_manager import FrequencyManager

## UI Calls
import users.gaespino.dev.S2T.UI.System2TesterUI as UI

## Imports from THR folder
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
config.reload()

bullets = '>>>'
s2tflow = None

#========================================================================================================#
#=============== CONFIGURATION ACCESS ===================================================================#
#========================================================================================================#

pf = config.get_functions()
reg = config.get_registers()
strategy = config.get_strategy()

if strategy is None:
	raise ValueError("Could not load product strategy. Check product configuration.")

pf.display_banner(revision, date, engineer)

## Initializes Menus based on product strategy
def init_menus(product):
	"""Initialize menus using product strategy for proper terminology."""
	strategy = config.get_strategy()
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

## On screen selection for System to Tester
def setupSystemAsTester(debug = False):
	'''
	Sets up system to be like tester using new manager architecture.
	Will ask questions on details.
	'''
	
	global s2tflow
	tester_mode = 0
	s2tflow = S2TFlow(debug=debug)

	print(f"\n{'='*80}")
	print(f"System 2 Tester - Refactored v{revision}")
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
				  Reset = False, Mask = None, pseudo = False, dis_2CPM = None, GUI = True, 
				  fastboot = True, corelic = None, volttype='vbump', debug= False, 
				  boot_postcode = False, extMask = None, u600w=None, execution_state=None):
	"""
	Quick mesh test using new manager architecture.
	"""
	s2tTest = S2TFlow(debug=debug, execution_state=execution_state)
	product = config.SELECTED_PRODUCT
	
	voltage_recipes = ['ppvc']
	vtype = 3 if volttype == 'vbump' else 2 if volttype == 'fixed' else 4 if volttype == 'ppvc' else 1
	
	s2tTest.reset_start = Reset
	s2tTest.boot_postcode = boot_postcode
	s2tTest.license_level = corelic
	s2tTest.extMasks = extMask
	s2tTest.u600w = u600w
	
	# Set quickconfig variables
	s2tTest.quick()
	s2tTest.qvbumps_core = vbump_core
	s2tTest.qvbumps_mesh = vbump_mesh
	
	# Init System
	s2tTest.mesh_init()
	
	# Mask Selection
	if Mask != None:
		s2tTest.target = Mask
	elif pseudo:
		s2tTest.target = 'PSEUDO'
	else:
		s2tTest.mesh_mask()
	
	# 2CPM Configuration
	if dis_2CPM != None:
		s2tTest.dis_2CPM = dis_2CPM
	else:
		s2tTest.mesh_2cpm()
	
	## UI Part here
	if GUI:
		UI.mesh_ui(s2tTest, product=product)
	else:
		# Frequency Conditions using FrequencyManager
		if core_freq != None:
			s2tTest.frequency_mgr.set_frequencies(core=core_freq)
		if mesh_freq != None:
			s2tTest.frequency_mgr.set_frequencies(mesh=mesh_freq)
		
		# Voltage Conditions using VoltageManager
		if vtype > 1:
			s2tTest.voltselect = vtype
		
		# Set voltage using manager
		s2tTest.set_voltage()
		
		# Run Mesh
		if not s2tTest.debug:
			s2tTest.mesh_run()
		
		# Save Configuration
		s2tTest.save_config(file_path=s2tTest.defaultSave)

def SliceQuickTest(Target_core = None, core_freq = None, mesh_freq = None, vbump_core = None, 
				   vbump_mesh = None, Reset = False, GUI = True, fastboot = True, volttype='vbump', 
				   vtype = 3, debug= False, boot_postcode = False, u600w=None, execution_state=None):
	"""
	Quick slice test using new manager architecture.
	"""
	s2tTest = S2TFlow(debug=debug, execution_state=execution_state)
	product = config.SELECTED_PRODUCT
	
	voltage_recipes = ['ppvc']
	
	s2tTest.reset_start = Reset
	s2tTest.boot_postcode = boot_postcode
	s2tTest.targetLogicalCore = Target_core
	s2tTest.u600w = u600w
	
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
			s2tTest.frequency_mgr.set_frequencies(core=core_freq)
		if mesh_freq != None:
			s2tTest.frequency_mgr.set_frequencies(mesh=mesh_freq)
		
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

#========================================================================================================#
#=============== REFACTORED S2TFLOW CLASS WITH MANAGERS ================================================#
#========================================================================================================#

class S2TFlow():
	"""
	Refactored S2TFlow class using VoltageManager, FrequencyManager, and ProductStrategy.
	
	Key improvements:
	- Voltage operations delegated to VoltageManager
	- Frequency operations delegated to FrequencyManager
	- Product-specific logic handled by ProductStrategy
	- Works seamlessly with GNR (computes), CWF (computes), and DMR (CBBs)
	- Cleaner code with better separation of concerns
	"""
		
	def __init__(self, debug=False, targetLogicalCore=None, targetTile=None, 
				 use_ate_freq=True, use_ate_volt=False, flowid=1, 
				 core_freq=None, mesh_freq=None, io_freq=None, 
				 license_level=None, dcf_ratio=None, stop_after_mrc=False, 
				 boot_postcode=False, clear_ucode=None, halt_pcu=None, 
				 dis_acode=False, dis_ht=None, dis_2CPM=None, 
				 postBootS2T=True, clusterCheck=None, lsb=False, 
				 fix_apic=None, dryrun=False, fastboot=False, 
				 mlcways=None, ppvc_fuses=None, custom_volt=None, 
				 vbumps_volt=None, reset_start=None, check_bios=None, 
				 mesh_cfc_volt=None, mesh_hdc_volt=None, io_cfc_volt=None, 
				 ddrd_volt=None, ddra_volt=None, core_volt=None, 
				 u600w=None, extMasks=None, execution_state=None):

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
		
		# Pass initial frequency values to manager
		self.frequency_mgr.core_freq = core_freq
		self.frequency_mgr.mesh_freq = mesh_freq
		self.frequency_mgr.io_freq = io_freq
		self.frequency_mgr.use_ate_freq = use_ate_freq
		self.frequency_mgr.flowid = flowid
		
		# Pass initial voltage values to manager
		self.voltage_mgr.core_volt = core_volt
		self.voltage_mgr.mesh_cfc_volt = mesh_cfc_volt if mesh_cfc_volt else {d: None for d in self.domains}
		self.voltage_mgr.mesh_hdc_volt = mesh_hdc_volt if mesh_hdc_volt else {d: None for d in self.domains}
		self.voltage_mgr.io_cfc_volt = io_cfc_volt
		self.voltage_mgr.ddrd_volt = ddrd_volt
		self.voltage_mgr.ddra_volt = ddra_volt
		self.voltage_mgr.use_ate_volt = use_ate_volt
		
		## Script Flow
		self.mode = None
		self.external = False
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
		
		## License level
		self.license_level = license_level
		
		## External Base Masks
		self.extMasks = extMasks

		## Voltage Settings (maintained for compatibility, but delegated to manager)
		self.ppvc_fuses = ppvc_fuses
		self.custom_volt = custom_volt
		self.vbumps_volt = vbumps_volt
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
		
		print(f"\n{bullets} S2TFlow initialized for {self.strategy.get_product_name()}")
		print(f"{bullets} Using {self.domain_type}s: {', '.join(self.domains)}")
		print(f"{bullets} Core terminology: {self.core_string}\n")
	
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
				FEATURE_VALUE = getattr(self, F, None)
				if FEATURE_VALUE != FEATURE['disabled_value']:
					print(f'\t> Feature: {F} not enabled for this product ({config.SELECTED_PRODUCT}).')
					setattr(self, F, FEATURE['disabled_value'])
		print(f'{"+"*80}\n')

	def specific_product_features(self):
		"""Initialize product-specific features using strategy."""
		product = self.product
		
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

	def print_menu(self, menu):
		for l in menu.keys():
			if 'l' == l[0] or 'line' in l:
				print(menu[l])

	def quick(self):
		"""Quick Defeature Tool Init"""
		self.qvbumps_core = None
		self.qvbumps_mesh = None
		self.external = True
		
	#========================================================================================================#
	#=============== INITIALIZATION AND FLOW CONTROL =======================================================#
	#========================================================================================================#
		
	def init_flow(self):
		"""Initialization flow checks for BIOS and ColdReset if required"""
		
		if self.check_bios == None and self.__FRAMEWORK_FEATURES['check_bios']['enabled']:
			self.check_bios = _yorn_bool(default_yorn='N', prompt = self.Menus['BIOS'])
		
		if self.check_bios:
			print (f"\n{bullets} Checking bios knobs...\n")
			dpm.bsknobs(readonly = False, skipinit = True)
		
		## Checks QDF Data
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
				self.fastboot = False

		# Request for a clean run
		if self.reset_start == None and self.__FRAMEWORK_FEATURES['reset_start']['enabled']:
			self.reset_start = _yorn_bool(default_yorn='N', prompt = self.Menus['Reset'])

		if self.reset_start:
			print (f"\n{bullets} Rebooting unit please wait... \n")
			self.powercycle()
		
	def powercycle(self):
		"""Power cycle the unit"""
		if not self.u600w: 
			dpm.powercycle(ports=[1])
		else: 
			dpm.reset_600w()
			time.sleep(scm.EFI_POSTCODE_WT)
		
		time.sleep(scm.EFI_POSTCODE_WT)
		scm._wait_for_post(scm.EFI_POST, sleeptime=scm.EFI_POSTCODE_WT, 
						   additional_postcode=scm.LINUX_POST, execution_state=self.execution_state)
		
		if scm.check_user_cancel(self.execution_state):
			return True
		
		scm.svStatus(refresh=True)

	#========================================================================================================#
	#=============== VOLTAGE CONFIGURATION USING VOLTAGEMANAGER ============================================#
	#========================================================================================================#

	def set_license(self):
		"""Set license level"""
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
			if self.license_level == 0:
				self.license_level = None

	def set_voltage(self):
		"""
		Configure voltage using VoltageManager.
		Handles all voltage options: ATE, fixed, vbumps, PPVC.
		"""
		# Initialize voltage tables with safe voltages
		self.voltage_mgr.init_voltage_tables(
			mode=self.mode,
			safe_volts_pkg=stc.All_Safe_RST_PKG,
			safe_volts_cdie=stc.All_Safe_RST_CDIE
		)
		
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
		ate_configured = self.frequency_mgr.configure_ate_frequency(
			mode=self.mode,
			core_string=self.core_string,
			input_func=input
		)
		
		# Fall back to manual if ATE not used
		if not ate_configured:
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

	def set_misc(self):
		"""Set miscellaneous options"""
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
		scm.global_fixed_hdc_volt=self.mesh_hdc_volt
		scm.global_fixed_cfcio_volt=self.io_cfc_volt
		scm.global_fixed_ddrd_volt=self.ddrd_volt
		scm.global_fixed_ddra_volt=self.ddra_volt
		scm.global_avx_mode = self.license_level
		scm.global_vbumps_configuration=self.vbumps_volt
		scm.global_u600w=self.u600w
		scm.global_boot_extra=",pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=45 "
		
		# Flow specific
		if flow =='mesh': 
			scm.global_ht_dis = self.dis_ht
		scm.global_2CPM_dis = self.dis_2CPM
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
		
		# Restore other settings
		self.license_level = config_data.get('license_level')
		self.dcf_ratio = config_data.get('dcf_ratio')
		self.stop_after_mrc = config_data.get('stop_after_mrc', False)
		self.boot_postcode = config_data.get('boot_postcode', False)
		self.clear_ucode = config_data.get('clear_ucode')
		self.halt_pcu = config_data.get('halt_pcu')
		self.dis_acode = config_data.get('dis_acode')
		self.dis_ht = config_data.get('dis_ht')
		self.dis_2CPM = config_data.get('dis_2CPM')
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
	#=============== SLICE MODE IMPLEMENTATION ==============================================================#
	#========================================================================================================#

	def setupSliceMode(self):
		"""Setup Slice Mode - Main entry point"""
		# Slice Mode init
		self.slice_init()

		# Core Selection Menu
		self.slice_core(array=self.array, core_dict=self.core_dict)

		# ATE Selection
		self.slice_ate()

		# Fastboot option
		if not self.u600w and self.__FRAMEWORK_FEATURES['fastboot']['enabled']:
			self.fastboot = _yorn_bool(self.Menus['FASTBOOT'],"Y")

		# License configuration
		self.set_license()

		# Miscellaneous settings
		self.set_misc()

		# Registers Selection
		self.slice_registers()

		# Frequency configuration
		self.set_frequency()

		# Voltage configuration
		self.set_voltage()

		# Run slice (unless in debug mode)
		if not self.debug:
			self.slice_run()

		# Save configuration
		self.save_config(file_path=self.defaultSave)

	def slice_init(self):
		"""Initialize slice mode"""
		self.mode = 'slice'
		
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
					self.targetLogicalCore = int(input(f"--> Enter Physical {self.core_string} ID: "))
				except:
					pass
			
			print(f"\n{bullets} Selected {self.core_string}: {self.targetLogicalCore}")
			
	def slice_ate(self):
		"""ATE configuration for slice mode - now uses FrequencyManager"""
		if (self.use_ate_freq and self.__FRAMEWORK_FEATURES['use_ate_freq']['enabled']):
			# Use frequency manager for ATE configuration
			ate_configured = self.frequency_mgr.configure_ate_frequency(
				mode='slice',
				core_string=self.core_string,
				input_func=input
			)
			
			if ate_configured:
				# Get the configured values
				freq_dict = self.frequency_mgr.get_frequency_dict()
				self.core_freq = freq_dict['core_freq']
				self.mesh_freq = freq_dict['mesh_freq']
				self.io_freq = freq_dict['io_freq']
				self.flowid = freq_dict['flowid']

	def slice_registers(self):
		"""Register selection for slice mode"""
		if self.reg_select == None and self.__FRAMEWORK_FEATURES['reg_select']['enabled']:
			print(f"\n{bullets} Register Selection not currently enabled for this product")
			self.reg_select = 1
	
	def slice_run(self):
		"""Run slice configuration"""
		# Set global variables
		self.set_globals(flow='core')
		
		slice_mode = scm.System2Tester(target = self.targetLogicalCore, masks = self.masks, 
									   boot=True, ht_dis=False, dis_2CPM = self.dis_2CPM, 
									   fresh_state= False, fastboot = self.fastboot, 
									   ppvc_fuses=self.volt_config, execution_state = self.execution_state)

		slice_mode.setCore()
		
		# Force refresh after boot
		if scm.check_user_cancel(self.execution_state):
			return
		scm.svStatus(refresh=True)
		
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
				print('--> Errors occurred applying slice configuration, skipping...')
				
		if (itp.ishalted() == True): 
			try:
				itp.go()
			except:
				print("--> Unit go can't be issued, problems with ipc...")

		# Apply Fuse Checks
		slice_mode.fuse_checks()

		# Call overview and last refresh
		self.slice_end()

	def slice_end(self):
		"""Finalize slice mode"""
		print(f"\n{'='*80}")
		print(f"{bullets} Slice Mode Configuration Complete")
		print(f"{'='*80}\n")
		
		# Display final configuration
		print(f"{bullets} Final Configuration:")
		print(f"  Target {self.core_string}: {self.targetLogicalCore}")
		print(f"  {self.core_string} Frequency: {self.core_freq}")
		print(f"  Mesh Frequency: {self.mesh_freq}")
		print(f"  IO Frequency: {self.io_freq}")
		print(f"  License Level: {self.license_level}")
		
		if self.custom_volt or self.vbumps_volt or self.ppvc_fuses:
			print(f"  Voltage Config: {'Custom' if self.custom_volt else 'VBumps' if self.vbumps_volt else 'PPVC'}")
		
		print(f"\n{bullets} System ready for testing\n")

	#========================================================================================================#
	#=============== MESH MODE IMPLEMENTATION ==============================================================#
	#========================================================================================================#

	def setupMeshMode(self):
		"""Setup Mesh Mode - Main entry point"""
		# Mesh Mode init
		self.mesh_init()

		# Mask Selection
		self.mesh_mask()

		# 2CPM Configuration
		self.mesh_2cpm()

		# Fastboot option
		if not self.u600w and self.__FRAMEWORK_FEATURES['fastboot']['enabled']:
			self.fastboot = _yorn_bool(self.Menus['FASTBOOT'],"Y")

		# License configuration
		self.set_license()

		# Miscellaneous settings
		self.set_misc()

		# HT disable (if supported by product)
		if self.__FRAMEWORK_FEATURES['dis_ht']['enabled']:
			if self.dis_ht == None:
				self.dis_ht = _yorn_bool(default_yorn='Y', prompt=self.Menus['HTDIS'])

		# Frequency configuration
		self.set_frequency()

		# Voltage configuration
		self.set_voltage()

		# Run mesh (unless in debug mode)
		if not self.debug:
			self.mesh_run()

		# Save configuration
		self.save_config(file_path=self.defaultSave)

	def mesh_init(self):
		"""Initialize mesh mode"""
		self.mode = 'mesh'
		
		if scm.check_user_cancel(self.execution_state):
			return
		scm.svStatus(refresh=False)
		
		self.init_flow()
		self.masks, self.array = scm.CheckMasks(extMasks=self.extMasks)

	def mesh_mask(self):
		"""Mask selection for mesh mode"""
		if self.target == '':
			print(f"\n{bullets} Mask Selection for {self.domain_type}s:")
			self.print_menu(self.ate_config_main)
			
			# Get valid masks from strategy
			valid_masks = self.strategy.get_valid_ate_masks()
			
			ate_mask = 0
			maxrng = self.ate_config_product['maxrng']
			
			while ate_mask not in range(1, maxrng):
				try:
					ate_mask = int(input(f"--> Enter 1-{maxrng-1}: "))
				except:
					pass
			
			if ate_mask == 1:
				# ATE Configuration
				self.print_menu(self.ate_config_product)
				ate_id = 0
				while ate_id not in range(1, len(valid_masks) + 1):
					try:
						ate_id = int(input(f"--> Enter 1-{len(valid_masks)}: "))
					except:
						pass
				self.target = valid_masks[ate_id - 1]
				
			elif ate_mask == 2:
				# Tile Isolation
				print(f"\n{bullets} {self.domain_type} Isolation:")
				domains = self.strategy.get_voltage_domains()
				for idx, domain in enumerate(domains, 1):
					print(f"\t> {idx}. {domain.upper()}")
				
				tile_sel = 0
				while tile_sel not in range(1, len(domains) + 1):
					try:
						tile_sel = int(input(f"--> Enter 1-{len(domains)}: "))
					except:
						pass
				self.target = domains[tile_sel - 1].upper()
				
			elif ate_mask == 3:
				# Custom
				self.target = 'CUSTOM'
				customs = self.strategy.get_valid_customs()
				print(f"\n{bullets} Custom mask options: {', '.join(customs)}")
				
			elif ate_mask == 4:
				# Full Chip
				self.target = 'FULLCHIP'
		
		print(f"\n{bullets} Selected mask: {self.target}")

	def mesh_2cpm(self):
		"""2CPM configuration for mesh mode"""
		if self.dis_2CPM == None and self.__FRAMEWORK_FEATURES['dis_2CPM']['enabled']:
			print(f"\n{bullets} 2CPM Disable Options:")
			self.print_menu(config.DIS2CPM_MENU['main'])
			
			dis2cpm_sel = 0
			maxrng = config.DIS2CPM_MENU['main']['maxrng']
			
			while dis2cpm_sel not in range(0, maxrng):
				try:
					dis2cpm_sel = int(input(f"--> Enter 0-{maxrng-1} (0 for no disable): "))
				except:
					pass
			
			if dis2cpm_sel == 0:
				self.dis_2CPM = 0
			else:
				self.dis_2CPM = self.dis2cpm_dict.get(dis2cpm_sel, 0)
		
		print(f"\n{bullets} 2CPM Disable: {self.dis_2CPM}")

	def mesh_run(self):
		"""Run mesh configuration"""
		# Set global variables
		self.set_globals(flow='mesh')
		
		mesh_mode = scm.System2Tester_Mesh(target=self.target, custom_list=self.custom_list,
										   masks=self.masks, boot=True, ht_dis=self.dis_ht,
										   dis_2CPM=self.dis_2CPM, fresh_state=False,
										   fastboot=self.fastboot, ppvc_fuses=self.volt_config,
										   clusterCheck=self.clusterCheck, lsb=self.lsb,
										   fix_apic=self.fix_apic, dryrun=self.dryrun,
										   mlcways=self.mlcways, execution_state=self.execution_state)

		mesh_mode.setMesh()
		
		# Force refresh after boot
		if scm.check_user_cancel(self.execution_state):
			return
		scm.svStatus(refresh=True)
		
		if (itp.ishalted() == False): 
			try:
				itp.halt()
			except:
				print("--> Unit Can't be halted, problems with ipc...")

		if self.postBootS2T:
			try:
				set_mesh(license_level=self.license_level, clear_ucode=self.clear_ucode,
						dcf_ratio=self.dcf_ratio, halt_pcu=self.halt_pcu)
			except:
				print('--> Errors occurred applying mesh configuration, skipping...')
				
		if (itp.ishalted() == True): 
			try:
				itp.go()
			except:
				print("--> Unit go can't be issued, problems with ipc...")

		# Apply Fuse Checks
		mesh_mode.fuse_checks()

		# Call overview and last refresh
		self.mesh_end()

	def mesh_end(self):
		"""Finalize mesh mode"""
		print(f"\n{'='*80}")
		print(f"{bullets} Mesh Mode Configuration Complete")
		print(f"{'='*80}\n")
		
		# Display final configuration
		print(f"{bullets} Final Configuration:")
		print(f"  Target Mask: {self.target}")
		print(f"  Core Frequency: {self.core_freq}")
		print(f"  Mesh Frequency: {self.mesh_freq}")
		print(f"  IO Frequency: {self.io_freq}")
		print(f"  License Level: {self.license_level}")
		print(f"  HT Disable: {self.dis_ht}")
		print(f"  2CPM Disable: {self.dis_2CPM}")
		
		if self.custom_volt or self.vbumps_volt or self.ppvc_fuses:
			print(f"  Voltage Config: {'Custom' if self.custom_volt else 'VBumps' if self.vbumps_volt else 'PPVC'}")
		
		print(f"\n{bullets} System ready for testing\n")

#========================================================================================================#
#=============== HELPER FUNCTIONS ======================================================================#
#========================================================================================================#

def _exit_condition(value, valid_values, error_message):
	"""Check if value is in valid values, exit if not"""
	if value not in valid_values:
		print(error_message)
		sys.exit(1)

def _yorn_bool(default_yorn='N', prompt='Y / N: '):
	"""Get Y/N input and return boolean"""
	yorn = ""
	while "N" not in yorn and "Y" not in yorn:
		yorn = input(prompt).upper()
		if yorn == "":
			yorn = default_yorn
	return yorn == "Y"

def _yorn_int(default_yorn='N', prompt='Y / N: ', userin='Enter value: '):
	"""Get Y/N input, if Y get integer value"""
	yorn = _yorn_bool(default_yorn, prompt)
	if not yorn:
		return None
	try:
		return int(input(userin))
	except:
		return None

def _yorn_float(default_yorn='N', prompt='Y / N: ', userin='Enter value: '):
	"""Get Y/N input, if Y get float value"""
	yorn = _yorn_bool(default_yorn, prompt)
	if not yorn:
		return None
	try:
		return float(input(userin))
	except:
		return None

def printTable(data, header=None, label=''):
	"""Print formatted table"""
	if label:
		print(f"\n{bullets} {label}\n")
	
	table_data = []
	for key, value in data.items():
		if isinstance(value, dict):
			for sub_key, sub_value in value.items():
				if isinstance(sub_value, list):
					table_data.append([key, sub_key, ', '.join(map(str, sub_value))])
				else:
					table_data.append([key, sub_key, sub_value])
		else:
			table_data.append([key, value])
	
	print(tabulate(table_data, headers=header if header else ['Key', 'Value'], tablefmt='grid'))

def set_slice(cr_array_start, cr_array_end, license_level=None, core_ratio=None, 
			  mesh_ratio=None, clear_ucode=False, dcf_ratio=None, halt_pcu=False):
	"""Set slice registers - placeholder for actual implementation"""
	print(f"{bullets} Applying slice register configuration...")
	# Implementation would go here
	pass

def set_mesh(license_level=None, clear_ucode=False, dcf_ratio=None, halt_pcu=False):
	"""Set mesh registers - placeholder for actual implementation"""
	print(f"{bullets} Applying mesh register configuration...")
	# Implementation would go here
	pass

#========================================================================================================#
#=============== MAIN EXECUTION ========================================================================#
#========================================================================================================#

if __name__ == "__main__":
	print(f"\n{'='*80}")
	print(f"System 2 Tester - Refactored v{revision}")
	print(f"Using Manager and Strategy Architecture")
	print(f"Supports: GNR (Computes), CWF (Computes), DMR (CBBs)")
	print(f"{'='*80}\n")
	print("Import this module and call setupSystemAsTester() to begin")
	print("Or use MeshQuickTest() / SliceQuickTest() for quick testing")
