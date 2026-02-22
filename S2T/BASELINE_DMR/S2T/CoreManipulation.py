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
import itpii
import sys
import re
from colorama import Fore, Style, Back
import importlib
import os
from tabulate import tabulate
from typing import Dict, List, Optional, Union
from importlib import import_module

## Custom Modulesimport

import toolext.bootscript.boot as b

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== DIRECT CONFIG ACCESS (Single Source of Truth) ==========================================#
#========================================================================================================#

# All configuration accessed directly via config object - no redundant declarations
# This provides a true single source of truth for all product configuration

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
	config.reload()
else:
	dpm = import_module(f'{BASE_PATH}.S2T.dpmChecks{LEGACY_NAMING}')

pf = config.get_functions()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=================================== IPC AND SV SETUP ===================================================#
#========================================================================================================#

from ipccli import BitData

ipc = None
api = None

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
global_boot_postcode=None
global_ht_dis=None
global_2CPM_dis=None
global_1CPM_dis=None
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
global_fixed_mlc_volt=None
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
	global global_fixed_mlc_volt
	global global_fixed_cfcio_volt
	global global_fixed_ddrd_volt
	global global_fixed_ddra_volt
	global global_vbumps_configuration
	global global_u600w
	global global_boot_extra
	global global_dry_run

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
	global_dry_run=False
	global_ia_vf=None
	global_ia_turbo=None

	# Voltage Resets
	global_fixed_core_volt=None
	global_fixed_cfc_volt=None
	global_fixed_hdc_volt=None
	global_fixed_mlc_volt=None
	global_fixed_cfcio_volt=None
	global_fixed_ddrd_volt=None
	global_fixed_ddra_volt=None
	global_vbumps_configuration=None
	global_u600w=None
	global_boot_extra=""

	print("Global variables reset.")

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== MAIN CODE STARTS HERE ==================================================================#
#========================================================================================================#

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#=============== BOOT CONFIGURATION CLASSES ==============================================================#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class BootConfiguration:
	"""Stores all configuration parameters for a boot operation"""

	def __init__(self):
		# Core frequencies
		self.ia_fw_p1: Optional[int] = None
		self.ia_fw_pn: Optional[int] = None
		self.ia_fw_pm: Optional[int] = None
		self.ia_fw_pboot: Optional[int] = None
		self.ia_fw_pturbo: Optional[int] = None
		self.ia_vf_curves: Optional[int] = None

		# IMH frequencies
		self.ia_imh_p1: Optional[int] = None
		self.ia_imh_pn: Optional[int] = None
		self.ia_imh_pm: Optional[int] = None
		self.ia_imh_pturbo: Optional[int] = None

		# CFC Mesh frequencies (FW)
		self.cfc_fw_p0: Optional[int] = None
		self.cfc_fw_p1: Optional[int] = None
		self.cfc_fw_pm: Optional[int] = None

		# CFC Mesh frequencies (CBB)
		self.cfc_cbb_p0: Optional[int] = None
		self.cfc_cbb_p1: Optional[int] = None
		self.cfc_cbb_pm: Optional[int] = None

		# CFC Mesh frequencies (IO)
		self.cfc_io_p0: Optional[int] = None
		self.cfc_io_p1: Optional[int] = None
		self.cfc_io_pm: Optional[int] = None

		# CFC Mesh frequencies (MEM)
		self.cfc_mem_p0: Optional[int] = None
		self.cfc_mem_p1: Optional[int] = None
		self.cfc_mem_pm: Optional[int] = None

		# Boot control flags
		self.boot_postcode: bool = False
		self.stop_after_mrc: bool = False
		self.ht_dis: Optional[bool] = None
		self.dis_2CPM: Optional[int] = None
		self.dis_1CPM: Optional[int] = None
		self.acode_dis: Optional[bool] = None
		self.vp2intersect_en: bool = True
		self.u600w: Optional[bool] = None
		self.pm_enable_no_vf: bool = False

		# License mode
		self.avx_mode: Optional[Union[str, int]] = None

		# Fixed frequency modes
		self.fixed_core_freq: Optional[int] = None
		self.fixed_mesh_freq: Optional[int] = None
		self.fixed_iocbb_freq: Optional[int] = None
		self.fixed_io_freq: Optional[int] = None
		self.fixed_mem_freq: Optional[int] = None
		self.fixed_io_freq: Optional[int] = None

		# Voltage configuration
		self.fixed_core_volt: Optional[float] = None
		self.fixed_cfc_volt: Optional[float] = None
		self.fixed_hdc_volt: Optional[float] = None
		self.fixed_mlc_volt: Optional[float] = None
		self.fixed_cfcio_volt: Optional[float] = None
		self.fixed_ddrd_volt: Optional[float] = None
		self.fixed_ddra_volt: Optional[float] = None
		self.vbumps_configuration: Optional[bool] = None

		# Extra boot options
		self.boot_extra: str = ""

	def _apply_global_boot_config(self):
		"""Apply global boot configuration to the booter"""
		global_config = {
			'ia_fw_p1': global_ia_fw_p1,
			'ia_fw_pn': global_ia_fw_pn,
			'ia_fw_pm': global_ia_fw_pm,
			'ia_fw_pboot': global_ia_fw_pboot,
			'ia_fw_pturbo': global_ia_fw_pturbo,
			'ia_vf_curves': global_ia_vf_curves,
			'ia_imh_p1': global_ia_imh_p1,
			'ia_imh_pn': global_ia_imh_pn,
			'ia_imh_pm': global_ia_imh_pm,
			'ia_imh_pturbo': global_ia_imh_pturbo,
			'cfc_fw_p0': global_cfc_fw_p0,
			'cfc_fw_p1': global_cfc_fw_p1,
			'cfc_fw_pm': global_cfc_fw_pm,
			'cfc_cbb_p0': global_cfc_cbb_p0,
			'cfc_cbb_p1': global_cfc_cbb_p1,
			'cfc_cbb_pm': global_cfc_cbb_pm,
			'cfc_io_p0': global_cfc_io_p0,
			'cfc_io_p1': global_cfc_io_p1,
			'cfc_io_pm': global_cfc_io_pm,
			'cfc_mem_p0': global_cfc_mem_p0,
			'cfc_mem_p1': global_cfc_mem_p1,
			'cfc_mem_pm': global_cfc_mem_pm,
			'boot_postcode': global_boot_postcode,
			'stop_after_mrc': global_boot_stop_after_mrc,
			'ht_dis': global_ht_dis,
			'dis_2CPM': global_2CPM_dis,
			'dis_1CPM': global_1CPM_dis,
			'acode_dis': global_acode_dis,
			'fixed_core_freq': global_fixed_core_freq,
			'fixed_mesh_freq': global_fixed_mesh_freq,
			'fixed_io_freq': global_fixed_io_freq,
			'avx_mode': global_avx_mode,
			'u600w': global_u600w,
			'boot_extra': global_boot_extra,
			'fixed_core_volt': global_fixed_core_volt,
			'fixed_cfc_volt': global_fixed_cfc_volt,
			'fixed_hdc_volt': global_fixed_hdc_volt,
			'fixed_mlc_volt': global_fixed_mlc_volt,
			'fixed_cfcio_volt': global_fixed_cfcio_volt,
			'fixed_ddrd_volt': global_fixed_ddrd_volt,
			'fixed_ddra_volt': global_fixed_ddra_volt,
			'vbumps_configuration': global_vbumps_configuration
		}
		#print('Boot params -->', global_config)
		self.apply_global_overrides(global_config)

	def apply_global_overrides(self, global_config: Dict):
		"""Apply global configuration overrides from a dictionary"""
		for key, value in global_config.items():
			if hasattr(self, key) and value is not None:
				setattr(self, key, value)
				print('Boot Configuration after applying global overrides: ', key, ' : ', value)

	def apply_fixed_frequencies(self):
		"""Apply fixed frequency settings across all related parameters"""
		if self.fixed_core_freq is not None: # Core frequency
			self.ia_fw_p1 = self.fixed_core_freq
			self.ia_fw_pn = self.fixed_core_freq
			self.ia_fw_pm = self.fixed_core_freq
			self.ia_fw_pboot = self.fixed_core_freq
			self.ia_fw_pturbo = self.fixed_core_freq

		if self.fixed_mesh_freq is not None:
			self.cfc_fw_p0 = self.fixed_mesh_freq
			self.cfc_fw_p1 = self.fixed_mesh_freq
			self.cfc_fw_pm = self.fixed_mesh_freq

		if self.fixed_iocbb_freq is not None: # IO CBB frequency
			self.cfc_cbb_p0 = self.fixed_iocbb_freq
			self.cfc_cbb_p1 = self.fixed_iocbb_freq
			self.cfc_cbb_pm = self.fixed_iocbb_freq

		if self.fixed_io_freq is not None: # IO frequency
			self.cfc_io_p0 = self.fixed_io_freq
			self.cfc_io_p1 = self.fixed_io_freq
			self.cfc_io_pm = self.fixed_io_freq

		if self.fixed_mem_freq is not None: # Memory frequency
			self.cfc_mem_p0 = self.fixed_mem_freq
			self.cfc_mem_p1 = self.fixed_mem_freq
			self.cfc_mem_pm = self.fixed_mem_freq

	def print_configuration(self):
		"""Print the current boot configuration"""
		print('\nUsing the following configuration for unit boot: ')

		if self.acode_dis:
			print('\tAcode disabled')
		if self.stop_after_mrc:
			print('\tStop after MRC')
		if self.boot_postcode:
			print('\tBoot will be stopped at Break')

		print(f'\tConfigured License Mode: {self.avx_mode}')

		# Core frequencies
		print('\tCore Frequencies:')
		print(f'\t\tIA p1: {self.ia_fw_p1}')
		print(f'\t\tIA pn: {self.ia_fw_pn}')
		print(f'\t\tIA pm: {self.ia_fw_pm}')
		print(f'\t\tIA fw boot: {self.ia_fw_pboot}')
		print(f'\t\tIA fw turbo: {self.ia_fw_pturbo}')
		print(f'\t\tIA fw vf curves: {self.ia_vf_curves}')
		print(f'\t\tIA imh p1: {self.ia_imh_p1}')
		print(f'\t\tIA imh pn: {self.ia_imh_pn}')
		print(f'\t\tIA imh pm: {self.ia_imh_pm}')
		print(f'\t\tIA imh turbo: {self.ia_imh_pturbo}')

		# Mesh frequencies
		print('\tCompute Mesh Frequencies:')
		print(f'\t\tCFC MESH fw p0: {self.cfc_fw_p0}')
		print(f'\t\tCFC MESH fw p1: {self.cfc_fw_p1}')
		print(f'\t\tCFC MESH fw pn: {self.cfc_fw_pm}')
		print(f'\t\tCFC MESH cbb p0: {self.cfc_cbb_p0}')
		print(f'\t\tCFC MESH cbb p1: {self.cfc_cbb_p1}')
		print(f'\t\tCFC MESH cbb pn: {self.cfc_cbb_pm}')
		print(f'\t\tCFC MESH io p0: {self.cfc_io_p0}')
		print(f'\t\tCFC MESH io p1: {self.cfc_io_p1}')
		print(f'\t\tCFC MESH io pn: {self.cfc_io_pm}')
		print(f'\t\tCFC MESH mem p0: {self.cfc_mem_p0}')
		print(f'\t\tCFC MESH mem p1: {self.cfc_mem_p1}')
		print(f'\t\tCFC MESH mem pn: {self.cfc_mem_pm}')

		# Voltages
		voltage_word = 'vBump' if self.vbumps_configuration else 'Volt'
		print('\tVoltage Bumps Configurations:' if self.vbumps_configuration else '\tFixed Voltage Configurations:')
		print(f'\t\tCore {voltage_word}: {self.fixed_core_volt}{"V" if self.fixed_core_volt is not None else ""}')
		print(f'\t\tCFC CBB {voltage_word}: {self.fixed_cfc_volt}{"V" if self.fixed_cfc_volt is not None else ""}')
		print(f'\t\tHDC CBB {voltage_word}: {self.fixed_hdc_volt}{"V" if self.fixed_hdc_volt is not None else ""}')
		print(f'\t\tMLC CBB {voltage_word}: {self.fixed_mlc_volt}{"V" if self.fixed_mlc_volt is not None else ""}')
		print(f'\t\tCFC IO {voltage_word}: {self.fixed_cfcio_volt}{"V" if self.fixed_cfcio_volt is not None else ""}')
		print(f'\t\tDDRD {voltage_word}: {self.fixed_ddrd_volt}{"V" if self.fixed_ddrd_volt is not None else ""}')

class SystemBooter:
	"""
	Handles all system boot operations with clean separation of concerns.

	This class encapsulates:
	- Boot configuration management
	- Bootscript and fastboot execution
	- Fuse management and verification
	- Boot retry logic
	"""

	def __init__(self, sv, ipc, system_config: Dict):
		"""
		Initialize the SystemBooter

		Args:
			sv: Python SV object
			ipc: IPC interface object
			system_config: Dictionary containing system-specific configuration
		"""
		self.sv = sv
		self.ipc = ipc
		self.system_config = system_config

		# Extract system configuration
		self.cbbs = system_config.get('cbbs', [])
		self.imhs = system_config.get('imhs', [])
		self.masks = system_config.get('masks', {})
		self.coremask = system_config.get('coremask', None)
		self.slicemask = system_config.get('slicemask', None)
		self.boot_fuses = system_config.get('boot_fuses', {})
		self.ppvc_fuses = system_config.get('ppvc_fuses', None)
		self.external_fuses = system_config.get('external_fuses', None)
		self.execution_state = system_config.get('execution_state', None)
		self.fuse_2CPM = system_config.get('fuse_2CPM', [])
		self.fuse_1CPM = system_config.get('fuse_1CPM', [])
		self.fastboot = system_config.get('fastboot', False)
		# Boot configuration
		self.config = BootConfiguration()

		# Fuse strings storage
		self.fuse_str = []
		self.fuse_str_cbb = []
		self.fuse_str_cbb_0 = {'base': [], 'top0': [], 'top1': [], 'top2': [], 'top3': []}
		self.fuse_str_cbb_1 = {'base': [], 'top0': [], 'top1': [], 'top2': [], 'top3': []}
		self.fuse_str_cbb_2 = {'base': [], 'top0': [], 'top1': [], 'top2': [], 'top3': []}
		self.fuse_str_cbb_3 = {'base': [], 'top0': [], 'top1': [], 'top2': [], 'top3': []}
		self.fuse_str_imh = []
		self.fuse_str_imh_0 = []
		self.fuse_str_imh_1 = []

		# Boot string for execution
		self.boot_string = ""

	def boot(self, use_fastboot: bool = False, **boot_params):
		"""
		Main entry point for boot operations

		Args:
			use_fastboot: Use fastboot method if True, otherwise use bootscript
			global_config: Global configuration overrides
			**boot_params: Boot parameters to override defaults
		"""
		# Update configuration with provided parameters
		for key, value in boot_params.items():
			if hasattr(self.config, key):
				setattr(self.config, key, value)
				print('Boot Configuration Parameters: ', key, ' : ', value)

		# Apply global boot configuration
		self.config._apply_global_boot_config()
		print('Applied Global Boot Configuration Overrides.')

		# Apply fixed frequency settings
		self.config.apply_fixed_frequencies()

		# Print configuration
		self.config.print_configuration()

		# Execute boot
		if use_fastboot:
			self._execute_fastboot()
		else:
			self._execute_bootscript()

	def _execute_bootscript(self):
		"""Execute boot using bootscript method"""
		# Build fuse strings
		self._build_fuse_strings()

		# Build boot disable strings
		boot_disable_ia, boot_disable_llc = self._build_mask_strings()

		# Build fuse string for bootscript
		fuse_string = self._build_bootscript_fuse_string()

		# Build fuse files string
		fuse_files_str = self._build_fuse_files_string()

		# Generate boot string
		compute_config = f'X{len(self.cbbs)}'
		bootopt = 'b.go'

		self.boot_string = gen_product_bootstring(
			bootopt=bootopt,
			compute_config=compute_config,
			b_extra=self.config.boot_extra,
			_boot_disable_ia=boot_disable_ia,
			_boot_disable_llc=boot_disable_llc,
			fuse_string=fuse_string,
			fuse_files=fuse_files_str
		)

		# Check for user cancel
		if check_user_cancel(self.execution_state):
			return

		# Print boot string
		print(Fore.CYAN + '\n' + "+" * 90)
		print(Fore.CYAN + "import toolext.bootscript.boot as b")
		print(Fore.CYAN + self.boot_string)
		print(Fore.CYAN + "+" * 90 + '\n')

		# Execute boot
		print(Fore.YELLOW + "*" * 90)
		print(Fore.YELLOW + "***   Starting Unit using Bootscript   ***".center(90))
		print(Fore.YELLOW + "*" * 90)

		# Execute with retry logic
		bootcont = 'b.cont'
		if not debug:
			boot_pass = self._retry_boot(
				boot_string=self.boot_string,
				bootcont=bootcont,
				n=BOOTSCRIPT_RETRY_TIMES,
				delay=BOOTSCRIPT_RETRY_DELAY
			)
		else:
			print(Fore.MAGENTA + 'Debug mode - skipping bootscript execution')
			boot_pass = True

		if not boot_pass:
			raise ValueError("!!!FAIL -- Max number of bootscript retries reached")
		elif boot_pass == 'Cancel':
			raise InterruptedError('Boot Interrupted by user')

	def _execute_fastboot(self):
		"""Execute boot using fastboot method with itp.resettarget()"""
		print(Fore.YELLOW + "*" * 90)
		print(Fore.YELLOW + f"{'>' * 3}   Using FastBoot with itp.resettarget() and ram flush ")

		# Build fuse strings
		self._build_fuse_strings()

		# Add mask fuses
		if self.slicemask is not None:
			self.fuse_str += mask_fuse_llc_array(self.slicemask)

		if self.coremask is not None:
			self.fuse_str += mask_fuse_module_array(self.coremask)

		# Set postcode if needed
		if self.config.stop_after_mrc:
			print(f'Setting biosscratchpad6_cfg for desired PostCode = {AFTER_MRC_POST:#x}')
			self.sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6] = AFTER_MRC_POST

		if self.config.boot_postcode:
			print(f'Setting biosscratchpad6_cfg for desired PostCode = {BOOT_STOP_POSTCODE:#x}')
			self.sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6] = BOOT_STOP_POSTCODE

		# Execute fuse override and reset
		print(Fore.YELLOW + "*" * 90)
		print(Fore.YELLOW + "*** Starting Unit Fast Boot Fuse Override ***".center(90))
		print(Fore.YELLOW + "*" * 90)

		if not debug:
			fuse_cmd_override_reset(
				fuse_cmd_array=self.fuse_str,
				s2t=True,
				execution_state=self.execution_state
			)

		# Wait for appropriate postcode
		if self.config.stop_after_mrc:
			_wait_for_post(
				AFTER_MRC_POST,
				sleeptime=MRC_POSTCODE_WT,
				timeout=MRC_POSTCODE_CHECK_COUNT,
				execution_state=self.execution_state
			)
		elif self.config.boot_postcode:
			_wait_for_post(
				BOOT_STOP_POSTCODE,
				sleeptime=BOOT_POSTCODE_WT,
				timeout=BOOT_POSTCODE_CHECK_COUNT,
				additional_postcode=LINUX_POST,
				execution_state=self.execution_state
			)
		else:
			_wait_for_post(
				EFI_POST,
				sleeptime=EFI_POSTCODE_WT,
				timeout=EFI_POSTCODE_CHECK_COUNT,
				additional_postcode=LINUX_POST,
				execution_state=self.execution_state
			)

	def _build_fuse_strings(self):
		"""Build all fuse configuration strings"""
		_fuse_str_cbb = []
		_fuse_str_imh = []

		# HT disable
		if self.config.ht_dis is not None:
			_fuse_str_cbb += config.HIDIS_COMP
			_fuse_str_imh += config.HTDIS_IO

		# 2CPM disable
		if self.config.dis_2CPM is not None:
			_fuse_str_cbb += self.fuse_2CPM

		# 1CPM disable
		if self.config.dis_1CPM is not None:
			_fuse_str_cbb += self.fuse_1CPM

		# 600W configuration
		if self.config.u600w:
			_fuse_str_cbb += config.FUSES_600W_COMP
			_fuse_str_imh += config.FUSES_600W_IO

		# config.VP2INTERSECT enable
		if self.config.vp2intersect_en:
			_fuse_str_cbb += config.VP2INTERSECT.get('bs', [])

		# Frequency configurations -- Full Path
		_fuse_str_cbb, _fuse_str_imh = self._apply_frequency_fuses(_fuse_str_cbb, _fuse_str_imh)

		# License mode configuration -- Full Path
		_fuse_str_cbb = self._apply_license_mode(_fuse_str_cbb)

		# If not fastboot, extend common fuses for bootscript usage
		if not self.fastboot:
			self._extend_common_fuses(_fuse_str_cbb, _fuse_str_imh)

		# Apply PPVC fuses if configured - This comes in format from S2T
		self._apply_external_fuses(self.ppvc_fuses)

		# Apply External fuses if configured - This comes in format from S2T
		self._apply_external_fuses(self.external_fuses)

		# Store fuse strings
		#print('Fuse Strings CBB:', _fuse_str_cbb)
		print('Fuse Strings IMH:', _fuse_str_imh)
		if _fuse_str_cbb: self.fuse_str_cbb.extend(_fuse_str_cbb)
		if _fuse_str_imh: self.fuse_str_imh.extend(_fuse_str_imh)

		# Add to Fastboot Fuse String
		self.fuse_str += self.fuse_str_cbb
		self.fuse_str += self.fuse_str_imh

	def _apply_frequency_fuses(self, fuse_str_cbb: List[str], fuse_str_imh: List[str]):
		"""Apply frequency configuration to fuse strings"""
		# CFC frequencies
		if self.config.cfc_fw_p0:
			fuse_str_cbb.extend(self._assign_values_to_regs(
				self.boot_fuses['CFC']['fwFreq']['p0'], self.config.cfc_fw_p0))
		if self.config.cfc_fw_p1:
			fuse_str_cbb.extend(self._assign_values_to_regs(
				self.boot_fuses['CFC']['fwFreq']['p1'], self.config.cfc_fw_p1))
		if self.config.cfc_fw_pm:
			fuse_str_cbb.extend(self._assign_values_to_regs(
				self.boot_fuses['CFC']['fwFreq']['min'], self.config.cfc_fw_pm))

		if self.config.cfc_cbb_p0:
			fuse_str_imh.extend(self._assign_values_to_regs(
				self.boot_fuses['CFC']['cbbFreq']['p0'], self.config.cfc_cbb_p0))
		if self.config.cfc_cbb_p1:
			fuse_str_imh.extend(self._assign_values_to_regs(
				self.boot_fuses['CFC']['cbbFreq']['p1'], self.config.cfc_cbb_p1))
		if self.config.cfc_cbb_pm:
			fuse_str_imh.extend(self._assign_values_to_regs(
				self.boot_fuses['CFC']['cbbFreq']['min'], self.config.cfc_cbb_pm))

		if self.config.cfc_io_p0:
			fuse_str_imh.extend(self._assign_values_to_regs(
				self.boot_fuses['CFC']['ioFreq']['p0'], self.config.cfc_io_p0))
		if self.config.cfc_io_p1:
			fuse_str_imh.extend(self._assign_values_to_regs(
				self.boot_fuses['CFC']['ioFreq']['p1'], self.config.cfc_io_p1))
		if self.config.cfc_io_pm:
			fuse_str_imh.extend(self._assign_values_to_regs(
				self.boot_fuses['CFC']['ioFreq']['min'], self.config.cfc_io_pm))

		if self.config.cfc_mem_p0:
			fuse_str_imh.extend(self._assign_values_to_regs(
				self.boot_fuses['CFC']['memFreq']['p0'], self.config.cfc_mem_p0))
		if self.config.cfc_mem_p1:
			fuse_str_imh.extend(self._assign_values_to_regs(
				self.boot_fuses['CFC']['memFreq']['p1'], self.config.cfc_mem_p1))
		if self.config.cfc_mem_pm:
			fuse_str_imh.extend(self._assign_values_to_regs(
				self.boot_fuses['CFC']['memFreq']['min'], self.config.cfc_mem_pm))

		# IA frequencies
		if self.config.ia_fw_p1:
			fuse_str_cbb.extend(self._assign_values_to_regs(
				self.boot_fuses['IA']['fwFreq']['p1'], self.config.ia_fw_p1))
			#fuse_str_imh.extend(self._assign_values_to_regs(
			#	self.boot_fuses['IA']['imhFreq']['p1'], self.config.ia_fw_p1))

		if self.config.ia_fw_pn:
			fuse_str_cbb.extend(self._assign_values_to_regs(
				self.boot_fuses['IA']['fwFreq']['pn'], self.config.ia_fw_pn))
			#fuse_str_imh.extend(self._assign_values_to_regs(
			#	self.boot_fuses['IA']['imhFreq']['pn'], self.config.ia_fw_p1))

		# Removing Min and Boot fuses as they are causing boot issues
		#if self.config.ia_fw_pm:
		#	fuse_str_cbb.extend(self._assign_values_to_regs(
		#		self.boot_fuses['IA']['fwFreq']['min'], self.config.ia_fw_pm))
		#	#fuse_str_imh.extend(self._assign_values_to_regs(
		#	#	self.boot_fuses['IA']['imhFreq']['min'], self.config.ia_fw_p1))

			#Including the top DIE fuses as well
			#fuse_str_cbb.extend(self._assign_values_to_regs(
			#	self.boot_fuses['IA']['fwFreq']['top_min'], self.config.ia_fw_pturbo))

		#if self.config.ia_fw_pboot:
		#	fuse_str_cbb.extend(self._assign_values_to_regs(
		#		self.boot_fuses['IA']['fwFreq']['boot'], self.config.ia_fw_pboot))
		#	#fuse_str_imh.extend(self._assign_values_to_regs(
		#	#	self.boot_fuses['IA']['imhFreq']['boot'], self.config.ia_fw_p1))

		if self.config.ia_fw_pturbo:
			fuse_str_cbb.extend(self._assign_values_to_regs(
				self.boot_fuses['IA']['fwFreq']['turbo'], self.config.ia_fw_pturbo))

			#Including the top DIE fuses as well
			#fuse_str_cbb.extend(self._assign_values_to_regs(
			#	self.boot_fuses['IA']['fwFreq']['top_p0'], self.config.ia_fw_pturbo))
			#fuse_str_imh.extend(self._assign_values_to_regs(
			#	self.boot_fuses['IA']['imhFreq']['turbo'], self.config.ia_fw_p1))

		return fuse_str_cbb, fuse_str_imh

	def _apply_license_mode(self, fuse_str_cbb: List[str]):
		"""Apply AVX license mode configuration"""
		if self.config.avx_mode is None:
			return fuse_str_cbb

		if self.config.avx_mode in range(0, 5):
			int_mode = self.config.avx_mode
		elif self.config.avx_mode == "128":
			int_mode = 0
		elif self.config.avx_mode == "256":
			int_mode = 1
		elif self.config.avx_mode == "512":
			int_mode = 2
		elif self.config.avx_mode == "TMUL":
			int_mode = 3
		else:
			raise ValueError("Invalid AVX Mode")

		ia_min_lic = self.boot_fuses['IA_license']['cbb']['min']
		ia_max_lic = self.boot_fuses['IA_license']['cbb']['max']

		fuse_str_cbb.append(f'{ia_min_lic}=0x{int_mode:x}')
		fuse_str_cbb.append(f'{ia_max_lic}=0x{int_mode:x}')

		return fuse_str_cbb

	def _apply_external_fuses(self, external_fuses: Optional[Dict[str, List[str]]]):
		"""Apply PPVC fuse configurations"""
		if not external_fuses:
			return

		# Updates Main Fuses with all PPVC fuses data

		if self.fastboot:
			# Fastboot use complete register name

			self.fuse_str_cbb.extend(external_fuses.get('cbb0',[]))
			self.fuse_str_cbb.extend(external_fuses.get('cbb1',[]))
			self.fuse_str_cbb.extend(external_fuses.get('cbb2',[]))
			self.fuse_str_cbb.extend(external_fuses.get('cbb3',[]))
			self.fuse_str_imh.extend(external_fuses.get('imh0',[]))
			self.fuse_str_imh.extend(external_fuses.get('imh1',[]))
			return

		# Split fuse strings by CBB/IMH
		for cbb in self.cbbs:
			cbb_name = cbb.name.lower() if hasattr(cbb, 'name') else str(cbb).lower()
			if 'cbb0' in cbb_name:
				self._extend_cbb_fuses('fuse_str_cbb_0', external_fuses.get('cbb0', {}))

			if 'cbb1' in cbb_name:
				self._extend_cbb_fuses('fuse_str_cbb_1', external_fuses.get('cbb1', {}))

			if 'cbb2' in cbb_name:
				self._extend_cbb_fuses('fuse_str_cbb_2', external_fuses.get('cbb2', {}))

			if 'cbb3' in cbb_name:
				self._extend_cbb_fuses('fuse_str_cbb_3', external_fuses.get('cbb3', {}))

		for imh in self.imhs:
			imh_name = imh.name.lower() if hasattr(imh, 'name') else str(imh).lower()
			if 'imh0' in imh_name or 'io0' in imh_name:
				self._extend_imh_fuses('fuse_str_imh_0', external_fuses.get('imh0', []))

			if 'imh1' in imh_name or 'io1' in imh_name:
				self._extend_imh_fuses('fuse_str_imh_1', external_fuses.get('imh1', []))

	def _build_mask_strings(self) -> tuple:
		"""Build core and LLC mask disable strings for bootscript"""
		_ia = []
		_llc = []

		print(f"Generating Bootscript string with CoreMask: {self.coremask}")
		print(f"Generating Bootscript string with SliceMask: {self.slicemask}")

		if self.coremask is None:
			boot_disable_ia = ''
		else:
			for key, value in self.coremask.items():
				_ia.append(f'"cbb_base{key[-1]}":{hex(value)}')
			disable_ia = ','.join(_ia)
			boot_disable_ia = f' ia_core_disable = {{{disable_ia}}},'

		if self.slicemask is None:
			boot_disable_llc = ''
		else:
			for key, value in self.slicemask.items():
				_llc.append(f'"cbb_base{key[-1]}":{hex(value)}')
			disable_llc = ','.join(_llc)
			boot_disable_llc = f' llc_slice_disable = {{{disable_llc}}},'

		print(f'Boot Disable IA String: {boot_disable_ia}')
		print(f'Boot Disable LLC String: {boot_disable_llc}')

		return boot_disable_ia, boot_disable_llc

	def _build_bootscript_fuse_string(self) -> str:
		"""Build the fuse string for bootscript format"""
		cbbs_number = len(self.cbbs)
		imhs_number = len(self.imhs)

		fuse_string = ''

		if cbbs_number >= 1:
			fuse_string += f"'cbb_base0': {self.fuse_str_cbb_0['base']},"
			fuse_string += f"'cbb0_top0': {self.fuse_str_cbb_0['top0']},"
			fuse_string += f"'cbb0_top1': {self.fuse_str_cbb_0['top1']},"
			fuse_string += f"'cbb0_top2': {self.fuse_str_cbb_0['top2']},"
			fuse_string += f"'cbb0_top3': {self.fuse_str_cbb_0['top3']},"
		if cbbs_number >= 2:
			fuse_string += f"'cbb_base1': {self.fuse_str_cbb_1['base']},"
			fuse_string += f"'cbb1_top0': {self.fuse_str_cbb_1['top0']},"
			fuse_string += f"'cbb1_top1': {self.fuse_str_cbb_1['top1']},"
			fuse_string += f"'cbb1_top2': {self.fuse_str_cbb_1['top2']},"
			fuse_string += f"'cbb1_top3': {self.fuse_str_cbb_1['top3']},"
		if cbbs_number >= 3:
			fuse_string += f"'cbb_base2': {self.fuse_str_cbb_2['base']},"
			fuse_string += f"'cbb2_top0': {self.fuse_str_cbb_2['top0']},"
			fuse_string += f"'cbb2_top1': {self.fuse_str_cbb_2['top1']},"
			fuse_string += f"'cbb2_top2': {self.fuse_str_cbb_2['top2']},"
			fuse_string += f"'cbb2_top3': {self.fuse_str_cbb_2['top3']},"
		if cbbs_number >= 4:
			fuse_string += f"'cbb_base3': {self.fuse_str_cbb_3['base']},"
			fuse_string += f"'cbb3_top0': {self.fuse_str_cbb_3['top0']},"
			fuse_string += f"'cbb3_top1': {self.fuse_str_cbb_3['top1']},"
			fuse_string += f"'cbb3_top2': {self.fuse_str_cbb_3['top2']},"
			fuse_string += f"'cbb3_top3': {self.fuse_str_cbb_3['top3']},"

		if imhs_number >= 1:
			fuse_string += f"'imh0': {self.fuse_str_imh_0},"
		if imhs_number >= 2:
			fuse_string += f"'imh1': {self.fuse_str_imh_1},"

		if fuse_string.endswith(','):
			fuse_string = f' fuse_str={{{fuse_string[:-1]}}},'
		print(fuse_string)
		return fuse_string

	def _ready_fuses_for_bootscript(self, fuses: List[str], base: List[str]) -> List[str]:
		"""Remove base fuses from CBB fuse list"""
		return dpm.bs_fuse_fix(fuses, base)

	# Holder not sure if using yet
	def _check_cbb_fuse_location(self, fuses: List[str]) -> tuple:
		"""Check and return top and bottom fuse locations based on system configuration"""
		top_fuses = []
		base_fuses = []

		for fuse in fuses:
			if '.base.' in fuse:
				base_fuses.append(fuse)
			else:
				top_fuses.append(fuse)

		return base_fuses, top_fuses

	def _build_fuse_files_string(self) -> str:
		"""Build fuse files string for bootscript"""
		_fuse_files_cbb = []
		_fuse_files_imh = []

		if self.config.pm_enable_no_vf:
			parent_dir = os.path.dirname(os.path.realpath(__file__))
			fuses_dir = os.path.join(parent_dir, 'Fuse')
			_fuse_files_cbb = [f'{fuses_dir}\\pm_enable_no_vf_computes.cfg']
			_fuse_files_imh = [f'{fuses_dir}\\pm_enable_no_vf_ios.cfg']

		fuse_files_str = ''
		if _fuse_files_cbb:
			fuse_files_cbb_str = ','.join([f'"{file}"' for file in _fuse_files_cbb])
			fuse_files_str += f'cbb=[{fuse_files_cbb_str}],'
		if _fuse_files_imh:
			fuse_files_imh_str = ','.join([f'"{file}"' for file in _fuse_files_imh])
			fuse_files_str += f'imh=[{fuse_files_imh_str}],'

		if fuse_files_str.endswith(','):
			fuse_files_str = f' fuse_files_str={{{fuse_files_str[:-1]}}},'

		return fuse_files_str

	def _extend_common_fuses(self, fuse_str_cbb, fuse_str_imh):

		cbbs_common_string = '.cbbs.'
		imhs_common_string = '.imhs.'

		_base_cbb_fuses = []
		_base_imh_fuses = []

		_top_cbb_fuses = []

		print(fuse_str_cbb)
		if fuse_str_cbb:
			for fuse in fuse_str_cbb:
				if cbbs_common_string in fuse and 'computes' in fuse:
					#print('Top Fuse Found: ', fuse)
					_top_cbb_fuses.append(re.sub(r'sv\.socket(s|\d+)\.cbbs\.computes\.fuses\.', '', fuse))
				elif cbbs_common_string in fuse and 'base' in fuse:
					#print('Bae Fuse Found: ', fuse)
					_base_cbb_fuses.append(re.sub(r'sv\.socket(s|\d+)\.cbbs\.base\.fuses\.', '', fuse))
				else:
					continue

		print(fuse_str_imh)
		if fuse_str_imh:
			for fuse in fuse_str_imh:
				if imhs_common_string in fuse:
					_base_imh_fuses.append(re.sub(r'sv\.socket(s|\d+)\.imhs\.fuses\.', '', fuse))


		for cbb in self.cbbs:
			cbb_name = cbb.name.lower() if hasattr(cbb, 'name') else str(cbb).lower()
			if 'cbb0' in cbb_name:
				self._extend_cbb_fuses('fuse_str_cbb_0', _base_cbb_fuses, fuse_keys = ['base'])
				self._extend_cbb_fuses('fuse_str_cbb_0', _top_cbb_fuses, fuse_keys = ['top0', 'top1', 'top2', 'top3'])

			if 'cbb1' in cbb_name:
				self._extend_cbb_fuses('fuse_str_cbb_1', _base_cbb_fuses, fuse_keys = ['base'])
				self._extend_cbb_fuses('fuse_str_cbb_1', _top_cbb_fuses, fuse_keys = ['top0', 'top1', 'top2', 'top3'])

			if 'cbb2' in cbb_name:
				self._extend_cbb_fuses('fuse_str_cbb_2', _base_cbb_fuses, fuse_keys = ['base'])
				self._extend_cbb_fuses('fuse_str_cbb_2', _top_cbb_fuses, fuse_keys = ['top0', 'top1', 'top2', 'top3'])

			if 'cbb3' in cbb_name:
				self._extend_cbb_fuses('fuse_str_cbb_3', _base_cbb_fuses, fuse_keys = ['base'])
				self._extend_cbb_fuses('fuse_str_cbb_3', _top_cbb_fuses, fuse_keys = ['top0', 'top1', 'top2', 'top3'])

		for imh in self.imhs:
			imh_name = imh.name.lower() if hasattr(imh, 'name') else str(imh).lower()
			if 'imh0' in imh_name or 'io0' in imh_name:
				self._extend_imh_fuses('fuse_str_imh_0', _base_imh_fuses)

			if 'imh1' in imh_name or 'io1' in imh_name:
				self._extend_imh_fuses('fuse_str_imh_1', _base_imh_fuses)

	def _extend_cbb_fuses(self, target_attr_name, source_fuses_dict, fuse_keys = ['base', 'top0', 'top1', 'top2', 'top3']):
		"""
		Helper method to extend CBB fuse strings for all locations (base, top0-3)

		Args:
			target_attr_name: Name of the target attribute (e.g., 'fuse_str_cbb_0')
			source_fuses_dict: Dictionary with keys like 'base', 'top0', 'top1', 'top2', 'top3', or a list
		"""
		if not hasattr(self, target_attr_name):
			print(f'Warning: No attribute configured with name: {target_attr_name}')
			return

		dict_source = isinstance(source_fuses_dict, dict)
		target_attr = getattr(self, target_attr_name)

		for key in fuse_keys:
			if key in target_attr:
				# If source is a dict, get the specific key; if it's a list, use the list directly
				data = source_fuses_dict.get(key, []) if dict_source else source_fuses_dict
				target_attr[key].extend(data)
				print('DEBUG: ', target_attr_name, key, target_attr[key])
			else:
				print(f'Warning: {target_attr_name} dictionary does not have key: {key}')

	def _extend_imh_fuses(self, target_attr_name, source_fuses_list):
		"""
		Helper method to extend IMH fuse strings

		Args:
			target_attr_name: Name of the target attribute (e.g., 'fuse_str_imh_0')
			source_fuses_list: List of fuses to extend
		"""
		if not hasattr(self, target_attr_name):
			print(f'Warning: No attribute configured with name: {target_attr_name}')
			return

		getattr(self, target_attr_name).extend(source_fuses_list)

	def _assign_values_to_regs(self, list_regs: List[str], new_value: int) -> List[str]:
		"""
		Assign a value to a list of register strings

		Args:
			list_regs: List of register names
			new_value: Value to assign

		Returns:
			List of register assignment strings
		"""
		print(f'DEBUG: Assigning value 0x{new_value:x} to registers: {list_regs[0:3]}...')
		return [f'{reg}=0x{new_value:x}' for reg in list_regs]

	def _retry_boot(self, boot_string: str, bootcont: str, n: int, delay: int = 60) -> Union[bool, str]:
		"""
		Retry boot with error handling

		Args:
			boot_string: Boot command string to execute
			bootcont: Boot continue command
			n: Number of retry attempts
			delay: Delay between retries in seconds

		Returns:
			True if successful, False if failed, 'Cancel' if user cancelled
		"""
		attempt = 0

		while attempt < n:
			print(Fore.BLACK + Back.LIGHTGREEN_EX + f"Performing Bootstript Attempt {attempt + 1}" + Back.RESET + Fore.RESET)
			try:
				# Execute boot string
				eval(boot_string)
				self._check_boot_completion(bootcont)
				print(Fore.BLACK + Back.LIGHTGREEN_EX + "Boot string executed successfully..." + Back.RESET + Fore.RESET)
				return True
			except KeyboardInterrupt:
				print(Back.RED + "Boot interrupted by user. Exiting..." + Back.RESET)
				return 'Cancel'
			except InterruptedError:
				print(Back.RED + "Boot interrupted by user. Exiting..." + Back.RESET)
				return 'Cancel'
			except SyntaxError as se:
				print(f"Syntax error occurred: {se}")
			except Exception as e:
				print(Back.RED + f"Attempt {attempt + 1} failed: {e}" + Back.RESET)
				print(Fore.LIGHTGREEN_EX + Back.YELLOW + "Performing power cycle..." + Back.RESET + Fore.RESET)

				if 'RSP 11 - Multicast Mixed stats' in str(e):
					print(Back.RED + "Performing IPC Reconnect.. Trying to fix RSP 11 issue" + Back.RESET)
					dpm.powercycle()
					time.sleep(120)

					if check_user_cancel(self.execution_state):
						return 'Cancel'

					svStatus(checkipc=True, checksvcores=False, refresh=False, reconnect=False)

				elif attempt <= n - 1:
					dpm.powercycle()
					time.sleep(delay)

			attempt += 1

		print(f"Failed to execute boot string after {n} attempts.")
		return False

	def _check_boot_completion(self, bootcont: str):
		"""Check boot completion and wait for appropriate postcode"""
		if self.config.stop_after_mrc:
			self.sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6] = AFTER_MRC_POST
			print("*" * 90)
			print(f"sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6]={AFTER_MRC_POST:#x}")
			print(f"{bootcont}(curr_state='phase6_cpu_reset_break')")
			print("*" * 90)
			self.ipc.go()
			_wait_for_post(
				AFTER_MRC_POST,
				sleeptime=MRC_POSTCODE_WT,
				timeout=MRC_POSTCODE_CHECK_COUNT,
				execution_state=self.execution_state
			)
		elif self.config.boot_postcode:
			self.sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6] = BOOT_STOP_POSTCODE
			print("*" * 90)
			print(f"sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6]={BOOT_STOP_POSTCODE:#x}")
			print(f"{bootcont}(curr_state='phase6_cpu_reset_break')")
			print("*" * 90)
			self.ipc.go()
			_wait_for_post(
				BOOT_STOP_POSTCODE,
				sleeptime=BOOT_POSTCODE_WT,
				timeout=BOOT_POSTCODE_CHECK_COUNT,
				additional_postcode=LINUX_POST,
				execution_state=self.execution_state
			)
		else:
			_wait_for_post(
				EFI_POST,
				sleeptime=EFI_POSTCODE_WT,
				timeout=EFI_POSTCODE_CHECK_COUNT,
				additional_postcode=LINUX_POST,
				execution_state=self.execution_state
			)

	def verify_fuses(self, use_fastboot: bool = False):
		"""
		Verify that fuses were applied correctly after boot

		Args:
			use_fastboot: Whether fastboot method was used
		"""

		def fuse_top_base_check(fuse_dict: dict, showresults:bool, skip_init:bool, cbb_name: str):
			"""Helper function to check fuse top and base values"""

			dict_keys = fuse_dict.keys() if fuse_dict else []

			for dict_key in dict_keys:
				top_fuse = 'top' in dict_key
				top_not_available = not(check_compute_fuses(f'compute{dict_key[-1]}'))

				if top_fuse and top_not_available:
					continue
				print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking {dict_key.upper()} Fuse for {cbb_name.upper()}: total of {len(fuse_dict[dict_key])} entries	---")
				fuse_cmd_override_check(fuse_dict[dict_key], showresults=showresults, skip_init=skip_init, bsFuses=f'{cbb_name}{dict_key if "base" not in dict_key else ""}')


		print(Fore.LIGHTCYAN_EX + "*" * 90)
		print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuse application after boot")

		dpm.fuseRAM(refresh=True)
		skip_init = True
		len_cbbs = len(self.cbbs)
		len_imhs = len(self.imhs)

		if use_fastboot:
			if self.fuse_str:
				fuse_cmd_override_check(self.fuse_str, showresults=False, skip_init=skip_init, bsFuses=None)
		else:
			if self.fuse_str_cbb_0 and len_cbbs >= 1:
				print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuses for CBB0 ---")
				fuse_top_base_check(self.fuse_str_cbb_0, showresults=False, skip_init=skip_init, cbb_name='cbb0')

			if self.fuse_str_cbb_1 and len_cbbs >= 2:
				print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuses for CBB1 ---")
				fuse_top_base_check(self.fuse_str_cbb_1, showresults=False, skip_init=skip_init, cbb_name='cbb1')

			if self.fuse_str_cbb_2 and len_cbbs >= 3:
				print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuses for CBB2 ---")
				fuse_top_base_check(self.fuse_str_cbb_2, showresults=False, skip_init=skip_init, cbb_name='cbb2')

			if self.fuse_str_cbb_3 and len_cbbs >= 4:
				print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuses for CBB3 ---")
				fuse_top_base_check(self.fuse_str_cbb_3, showresults=False, skip_init=skip_init, cbb_name='cbb3')
			if self.fuse_str_imh_0 and len_imhs >= 1:
				print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuses for imh0 ---")
				fuse_cmd_override_check(self.fuse_str_imh_0, showresults=False, skip_init=skip_init, bsFuses='imh0')

			if self.fuse_str_imh_1 and len_imhs >= 2:
				print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuses for imh1 ---")
				fuse_cmd_override_check(self.fuse_str_imh_1, showresults=False, skip_init=skip_init, bsFuses='imh1')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#=============== SYSTEM TO TESTER CLASS =================================================================#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class System2Tester():

	def __init__(self, target, masks = None, coremask=None, slicemask=None, boot = True, ht_dis = False, dis_1CPM = None, dis_2CPM = None, fresh_state = True, readFuse = False, clusterCheck = True , fastboot = True, ppvc_fuses = None, external_fuses = None, execution_state = None):

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

		self.instances = sv.socket0.cbbs.instance
		self.sktnum = [0]
		self.die = config.PRODUCT_CONFIG
		self.BootFuses = dpm.FuseFileConfigs
		self.Fastboot = fastboot
		self.boot_params = {}
		self.fuse_str = []
		self.fuse_str_imh = []
		self.fuse_str_cbb = []
		## Added split fuse to apply PPVC
		self.fuse_str_cbb_0 = {'base': [], 'top0': [], 'top1': [], 'top2': [], 'top3': []}
		self.fuse_str_cbb_1 = {'base': [], 'top0': [], 'top1': [], 'top2': [], 'top3': []}
		self.fuse_str_cbb_2 = {'base': [], 'top0': [], 'top1': [], 'top2': [], 'top3': []}
		self.fuse_str_cbb_3 = {'base': [], 'top0': [], 'top1': [], 'top2': [], 'top3': []}
		self.fuse_str_imh_0 = []
		self.fuse_str_imh_1 = []

		# We will convert the fuse on code as there is a top / base differentiation already in place
		self.fuse_2CPM = dpm.fuses_dis_2CPM(dis_2CPM, bsformat = False) if dis_2CPM != None else []
		self.fuse_1CPM = dpm.fuses_dis_1CPM(dis_1CPM, bsformat = False) if dis_1CPM != None else []

		self.ppvc_fuses = ppvc_fuses
		self.external_fuses = external_fuses

		## Option to bring preconfigured Mask
		if masks == None: self.masks = dpm.fuses(rdFuses = self.readFuse, sktnum =self.sktnum, printFuse=False)
		else: self.masks = masks

		# Debug Mode -- User can enable/disable debug mode during execution
		self.debug = debug

		# Initialize SystemBooter for boot operations
		self._init_system_booter()

#=============== DEBUG MODE SET / RESET ==================================================================#

	def set_debug_mode(self) -> None:
		self.debug = True

	def disable_debug_mode(self) -> None:
		self.debug = False

#=============== SYSTEM BOOTER INITIALIZATION ============================================================#

	def _init_system_booter(self):
		"""Initialize the SystemBooter instance with system configuration"""
		system_config = {
			'cbbs': self.cbbs,
			'imhs': self.imhs,
			'masks': self.masks,
			'coremask': self.coremask,
			'slicemask': self.slicemask,
			'boot_fuses': self.BootFuses,
			'ppvc_fuses': self.ppvc_fuses,
			'external_fuses': self.external_fuses,
			'execution_state': self.execution_state,
			'fuse_2CPM': self.fuse_2CPM,
			'fuse_1CPM': self.fuse_1CPM,
			'fastboot': self.Fastboot,
		}
		self.booter = SystemBooter(self.sv, self.ipc, system_config)

	def _apply_global_boot_config(self):
		"""Apply global boot configuration to the booter"""
		global_config = {
			'ia_fw_p1': global_ia_fw_p1,
			'ia_fw_pn': global_ia_fw_pn,
			'ia_fw_pm': global_ia_fw_pm,
			'ia_fw_pboot': global_ia_fw_pboot,
			'ia_fw_pturbo': global_ia_fw_pturbo,
			'ia_vf_curves': global_ia_vf_curves,
			'ia_imh_p1': global_ia_imh_p1,
			'ia_imh_pn': global_ia_imh_pn,
			'ia_imh_pm': global_ia_imh_pm,
			'ia_imh_pturbo': global_ia_imh_pturbo,
			'cfc_fw_p0': global_cfc_fw_p0,
			'cfc_fw_p1': global_cfc_fw_p1,
			'cfc_fw_pm': global_cfc_fw_pm,
			'cfc_cbb_p0': global_cfc_cbb_p0,
			'cfc_cbb_p1': global_cfc_cbb_p1,
			'cfc_cbb_pm': global_cfc_cbb_pm,
			'cfc_io_p0': global_cfc_io_p0,
			'cfc_io_p1': global_cfc_io_p1,
			'cfc_io_pm': global_cfc_io_pm,
			'cfc_mem_p0': global_cfc_mem_p0,
			'cfc_mem_p1': global_cfc_mem_p1,
			'cfc_mem_pm': global_cfc_mem_pm,
			'boot_postcode': global_boot_postcode,
			'stop_after_mrc': global_boot_stop_after_mrc,
			'ht_dis': global_ht_dis,
			'dis_2CPM': global_2CPM_dis,
			'dis_1CPM': global_1CPM_dis,
			'acode_dis': global_acode_dis,
			'fixed_core_freq': global_fixed_core_freq,
			'fixed_mesh_freq': global_fixed_mesh_freq,
			'fixed_io_freq': global_fixed_io_freq,
			'avx_mode': global_avx_mode,
			'u600w': global_u600w,
			'boot_extra': global_boot_extra,
			'fixed_core_volt': global_fixed_core_volt,
			'fixed_cfc_volt': global_fixed_cfc_volt,
			'fixed_hdc_volt': global_fixed_hdc_volt,
			'fixed_mlc_volt': global_fixed_mlc_volt,
			'fixed_cfcio_volt': global_fixed_cfcio_volt,
			'fixed_ddrd_volt': global_fixed_ddrd_volt,
			'fixed_ddra_volt': global_fixed_ddra_volt,
			'vbumps_configuration': global_vbumps_configuration
		}
		#print('Boot params -->', global_config)
		self.apply_global_overrides(global_config)

	def apply_global_overrides(self, global_config: Dict) -> None:
		"""Apply global configuration overrides from a dictionary"""
		for key, value in global_config.items():
			print('Global key:', key, 'Value:', value)
			if key in self.boot_params and value is not None:
				self.boot_params[key] = value

#=============== CONFIGURATION CHECKS ==================================================================#

	def check_for_start_fresh(self) -> None:
		if self.fresh_state: reset_globals()

	def check_product_validity(self) -> bool:
		if (self.die not in config.CORETYPES.keys()):
			print (f"sorry.  This method still needs updating for {self.die}.  ")
			return False

		return True

#=============== STRUCTURE GENERATION ==================================================================#

	def generate_base_dict(self) -> dict[str, int]:
		base_value = 0xffffffff
		cbb_base_dict = {cbb.name: base_value for cbb in self.cbbs}

		return cbb_base_dict

	def generate_module_mask(self) -> tuple[int, int]:
		target_cbb = int(self.target/config.MODS_PER_CBB) # Target CBB based on logical module
		modulemask = ~(1 << (self.target % config.MODS_PER_CBB)) & ((1 << config.MODS_PER_CBB) - 1)

		print("\n"+"-"*62)
		print("| A single module will be enabled for each available cbb |")
		print("-"*62+"\n")

		return target_cbb, modulemask

	def generate_mesh_masking(self, masks: dict) -> tuple[dict, dict]:
		modules = {}
		llcs = {}

		_moduleMasks= {cbb.name: masks[f'ia_cbb{cbb.instance}'] for cbb in self.cbbs}
		_llcMasks= {cbb.name: masks[f'llc_cbb{cbb.instance}'] for cbb in self.cbbs}

		for __cbb in self.cbbs:
			cbb_name = __cbb.name
			# Checking if str or int for modulemask / llcmask
			if isinstance(_moduleMasks[cbb_name], str):
				_moduleMasks[cbb_name] = int(_moduleMasks[cbb_name], 16)

			if isinstance(_llcMasks[cbb_name], str):
				_llcMasks[cbb_name] = int(_llcMasks[cbb_name], 16)

			modules[cbb_name] =  _moduleMasks[cbb_name]
			llcs[cbb_name] =  _llcMasks[cbb_name]

			print  (f"\n{cbb_name.upper()}: Module disabled mask: {hex(modules[cbb_name])}")
			print  (f"{cbb_name.upper()}: CBO disabled mask:  {hex(llcs[cbb_name])}")

		return modules, llcs

	def generate_first_enabled_mask(self, masks: dict, cbb_name: str) -> int:
		combineMask = masks[f'llc_{cbb_name}'] | masks[f'ia_{cbb_name}']
		binMask = bin(combineMask)
		first_zero = binMask[::-1].find('0')
		disMask = ~(1 << (first_zero)) & ((1 << config.MODS_PER_CBB)-1)

		return disMask, first_zero

	def generate_compute_first_slice_mask(self, cbb, target_core) -> dict:
		new_compute_mask = 0
		computes = cbb.computes
		target_compute = int((target_core % config.MODS_PER_CBB) / config.MODS_PER_COMPUTE) # Target Compute based on CBB
		for compute in computes:
			#compute_name = compute.name
			computeN = compute.instance
			if computeN == target_compute:
				new_compute_mask |= (0 << (computeN * config.MODS_PER_COMPUTE))
			else:
				new_compute_mask |= (0xFF << (computeN * config.MODS_PER_COMPUTE))
		print(f"{cbb.name.upper()}: Generated new compute mask:  {hex(new_compute_mask)}")

		return new_compute_mask

	def _get_alternative_compute_if_target_disabled(self, cbb_name, cbb_computes, target_compute, masks_per_compute):
		'''
		Helper method: checks if target compute is disabled and finds first available alternative.
		Returns: (is_disabled: bool, alternative_compute: str or None)
		'''
		if target_compute not in cbb_computes:
			return False, None

		target_mask = masks_per_compute[cbb_name][f'ia_{target_compute}']
		if target_mask != 0xFF:
			return False, None

		# Target is disabled, find first available compute
		print(f"[{cbb_name.upper()}] Target {target_compute.upper()} is already disabled (mask=0xFF)")
		print(f"[{cbb_name.upper()}] Applying special handling: keeping target disabled, using first available compute")

		for comp_name in cbb_computes:
			if masks_per_compute[cbb_name][f'ia_{comp_name}'] != 0xFF:
				print(f"[{cbb_name.upper()}] First available compute: {comp_name.upper()}")
				return True, comp_name

		print(f"[{cbb_name.upper()}] WARNING: No available compute found with enabled cores")
		return True, None

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
				shift_amount = computeN * config.MODS_PER_COMPUTE
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
				new_ia_cbb_mask |= (compute_ia_mask << (computeN * config.MODS_PER_COMPUTE))
				compute_llc_mask = compute_masks[cbb_name][f'llc_{compute_name}']
				new_llc_cbb_mask |= (compute_llc_mask << (computeN * config.MODS_PER_COMPUTE))
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

	# Sets up system to run with 1 enabled module per cbb -- Name is legacy from previous versions
	def setCore(self) -> None:
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
				new_llc_mask = self.generate_compute_first_slice_mask(cbb, self.target)
				_llcMasks[cbb_name] = new_llc_mask | masks[f'llc_{cbb_name}']
				#_llcMasks[cbb_name] = masks[f'llc_{cbb_name}']
			else:
				disMask, first_zero = self.generate_first_enabled_mask(masks=masks, cbb_name=cbb_name)
				_moduleMasks[cbb_name] = disMask | masks[f'ia_{cbb_name}']

				new_llc_mask = self.generate_compute_first_slice_mask(cbb, first_zero)
				_llcMasks[cbb_name] = new_llc_mask | masks[f'llc_{cbb_name}']

		for cbb_name in cbbs.name:
			# Print masks
			print  (f"\n{cbb_name.upper()}: MODULE disabled mask: {hex(_moduleMasks[cbb_name])}")
			print  (f"{cbb_name.upper()}: CBO disabled mask:  {hex(_llcMasks[cbb_name])}")

		# Setting the Class masks
		self.coremask = _moduleMasks
		self.slicemask = _llcMasks

		if self.boot and not debug:
			self._call_boot(boot_postcode=False,stop_after_mrc=False, pm_enable_no_vf=False)
		else:
			print("Debug Mode - No Boot Performed")

	## Enables/Disables each compute based on selected target
	def setCompute(self, boot_postcode=False,stop_after_mrc=False, pm_enable_no_vf=False, extMasks = None) -> None:
		'''
		Selects which computes to enable/disable. Based on Selected Target
		'''
		## Local variables -- Just defining them for shorter lines and usage

		targetComputes = self.target
		cbbs = self.cbbs

		if extMasks != None:
			masks = {k:int(v,16) for k, v in extMasks.items()}
		else:
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

		# CBBs requiring at least one compute with 1 core alive
		cbbs_requiring_one_compute = ['cbb0','cbb1','cbb2','cbb3']  # Extend this list as needed

		print("\n"+"-"*62)
		print(f"| Computes: {targetComputes} ==> selection requested for each available cbb |")
		print("-"*62+"\n")

		for cbb in cbbs: # For each cbb
			cbb_name = cbb.name
			cbb_computes = cbb.computes.name
			new_masks_per_compute[cbb_name] = {}

			# Check if this CBB requires special handling
			use_special_handling = cbb_name.lower() in cbbs_requiring_one_compute
			target_disabled = False
			alternative_compute = None

			if use_special_handling and len(targetComputeList) > 0:
				target_disabled, alternative_compute = self._get_alternative_compute_if_target_disabled(
					cbb_name, cbb_computes, targetComputeList[0], masks_per_compute)

			for compute_name in cbb_computes:
				if use_special_handling and target_disabled:
					# Special handling: target is already disabled
					if compute_name in targetComputeList:
						print(f"{compute_name.upper()} (target) keeping disabled for {cbb_name}")
						new_masks_per_compute[cbb_name][f'ia_{compute_name}'] = 0xFF
						new_masks_per_compute[cbb_name][f'llc_{compute_name}'] = masks_per_compute[cbb_name][f'llc_{compute_name}']
					elif compute_name == alternative_compute:
						print(f"{compute_name.upper()} enabled for {cbb_name} (alternative), maintaining original Masks")
						new_masks_per_compute[cbb_name][f'ia_{compute_name}'] = masks_per_compute[cbb_name][f'ia_{compute_name}']
						new_masks_per_compute[cbb_name][f'llc_{compute_name}'] = masks_per_compute[cbb_name][f'llc_{compute_name}']
					else:
						print(f"{compute_name.upper()} disabled for {cbb_name} (removing other computes)")
						new_masks_per_compute[cbb_name][f'ia_{compute_name}'] = 0xFF
						new_masks_per_compute[cbb_name][f'llc_{compute_name}'] = 0xFF #masks_per_compute[cbb_name][f'llc_{compute_name}']
				elif compute_name in targetComputeList:
					# Normal handling: Compute remains enabled
					print(f"{compute_name.upper()} enabled for {cbb_name}, mantaining original Masks")
					new_masks_per_compute[cbb_name][f'ia_{compute_name}'] = masks_per_compute[cbb_name][f'ia_{compute_name}']
					new_masks_per_compute[cbb_name][f'llc_{compute_name}'] = masks_per_compute[cbb_name][f'llc_{compute_name}']
				else:
					# Normal handling: Compute disabled
					print(f"{compute_name.upper()} disabled for {cbb_name}, updating Masks")
					new_masks_per_compute[cbb_name][f'ia_{compute_name}'] = 0xFF
					new_masks_per_compute[cbb_name][f'llc_{compute_name}'] = 0xFF #masks_per_compute[cbb_name][f'llc_{compute_name}']

		_moduleMasks, _llcMasks = self.convert_compute_mask_to_cbb_mask(new_masks_per_compute)

		for cbb_name in cbbs.name:
			# Print masks
			print  (f"\n{cbb_name.upper()}: MODULE disabled mask: {hex(_moduleMasks[f'{cbb_name}'])}")
			print  (f"{cbb_name.upper()}: CBO disabled mask:  {hex(_llcMasks[f'{cbb_name}'])}")

		# Setting the Class masks
		self.coremask = _moduleMasks
		self.slicemask = _llcMasks

		if self.boot and not debug:
			self._call_boot(boot_postcode=boot_postcode,stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)
		else:
			print("Debug Mode - No Boot Performed")

	## Needs at least one core enabled per COMPUTE, we are limited here, as WA we are leaving the selected compute alive plus the first full slice on the other COMPUTES.
	def setTile(self, boot_postcode=False,stop_after_mrc=False, pm_enable_no_vf=False, extMasks = None) -> None:
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

		if extMasks != None:
			masks = {k:int(v,16) for k, v in extMasks.items()}
		else:
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
		print(f"| CBB: {self.target} ==> selection requested for availables cbb |")
		print("-"*62+"\n")

		target_cbb = targetTileList

		#coremask = ~(1 << (targetLogicalCore - (60 * target_compute))) & ((1 << 60) - 1)

		for cbb in cbbs:
			cbb_name = cbb.name
			cbbN = cbb.target_info.instance

			if cbb_name not in target_cbb:
				disMask, first_zero = self.generate_first_enabled_mask(masks=masks, cbb_name=cbb_name)
				new_llc_mask = self.generate_compute_first_slice_mask(cbb, first_zero)

				print(f"\n\t{cbb_name.upper()} not selected, enabling only the first available slice")
				_moduleMasks[cbb_name] = disMask |  masks[f'ia_{cbb_name}']
				_llcMasks[cbb_name] = new_llc_mask |  masks[f'llc_{cbb_name}']

			## If compute is not being disabled keep original Mask
			else:
				print(f"\n\t{cbb_name.upper()} selected, mantaining original Masks")
				_moduleMasks[cbb_name] = masks[f'ia_{cbb_name}']
				_llcMasks[cbb_name] = masks[f'llc_{cbb_name}']


		for cbb_name in cbbs.name:
			# Print masks
			print  (f"\n{cbb_name.upper()}: module disabled mask: {hex(_moduleMasks[cbb_name])}")
			print  (f"{cbb_name.upper()}: CBO disabled mask:  {hex(_llcMasks[cbb_name])}")

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
		targetConfig = self.target
		ht_dis = self.ht_dis
		dis_2CPM = self.dis_2CPM
		dis_1CPM = self.dis_1CPM

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
		core_count, llc_count, Masks_test = dpm.pseudo_bs(	ClassMask = targetConfig,
															Custom = CustomConfig,
															boot = False, use_core = False,
															htdis = ht_dis,
															dis_2CPM = dis_2CPM,
															dis_1CPM = dis_1CPM,
															fuse_read = readFuse,
															s2t = True, masks = masks,
															clusterCheck = clusterCheck,
															lsb = lsb, skip_init = True)

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

			print('\nSetting New Mask Based on External Masks Configuration:\n')
			modules, llcs = self.generate_mesh_masking(masks=extMasks)

			# Setting the Class masks in script arrays
			self.coremask = modules
			self.slicemask = llcs

		if self.boot and not debug:
			self._call_boot(boot_postcode=boot_postcode,stop_after_mrc=stop_after_mrc, pm_enable_no_vf=pm_enable_no_vf)
		else:
			print("Debug Mode - No Boot Performed")

#=============== BOOT CONFIGURATION =========================================================#

	## Wrapper to call boot or fastboot depending on class variable self.Fastboot
	def _call_boot(self, boot_postcode=False, stop_after_mrc=False, fixed_core_freq=None, fixed_mesh_freq=None,
				   fixed_io_freq=None, avx_mode=None, acode_dis=None, vp2intersect_en=True, pm_enable_no_vf=False, u600w=None,
				   ia_fw_p1=None, ia_fw_pn=None, ia_fw_pm=None, ia_fw_pboot=None, ia_fw_pturbo=None, ia_vf_curves=None,
				   ia_imh_p1=None, ia_imh_pn=None, ia_imh_pm=None, ia_imh_pturbo=None,
				   cfc_fw_p0=None, cfc_fw_p1=None, cfc_fw_pm=None,
				   cfc_cbb_p0=None, cfc_cbb_p1=None, cfc_cbb_pm=None,
				   cfc_io_p0=None, cfc_io_p1=None, cfc_io_pm=None,
				   cfc_mem_p0=None, cfc_mem_p1=None, cfc_mem_pm=None, **kwargs):
		'''
		Wrapper to call boot or fastboot depending on class variable self.Fastboot.
		Now uses the SystemBooter class for cleaner boot management.
		'''
		# Prepare boot parameters
		self.boot_params = {
			'boot_postcode': boot_postcode,
			'stop_after_mrc': stop_after_mrc,
			'fixed_core_freq': fixed_core_freq,
			'fixed_mesh_freq': fixed_mesh_freq,
			'fixed_io_freq': fixed_io_freq,
			'avx_mode': avx_mode,
			'acode_dis': acode_dis,
			'vp2intersect_en': vp2intersect_en,
			'pm_enable_no_v': pm_enable_no_vf,
			'u600w': u600w,
			'ia_fw_p1': ia_fw_p1,
			'ia_fw_pn': ia_fw_pn,
			'ia_fw_pm': ia_fw_pm,
			'ia_fw_pboot': ia_fw_pboot,
			'ia_fw_pturbo': ia_fw_pturbo,
			'ia_vf_curves': ia_vf_curves,
			'ia_imh_p1': ia_imh_p1,
			'ia_imh_pn': ia_imh_pn,
			'ia_imh_pm': ia_imh_pm,
			'ia_imh_pturbo': ia_imh_pturbo,
			'cfc_fw_p0': cfc_fw_p0,
			'cfc_fw_p1': cfc_fw_p1,
			'cfc_fw_pm': cfc_fw_pm,
			'cfc_cbb_p0': cfc_cbb_p0,
			'cfc_cbb_p1': cfc_cbb_p1,
			'cfc_cbb_pm': cfc_cbb_pm,
			'cfc_io_p0': cfc_io_p0,
			'cfc_io_p1': cfc_io_p1,
			'cfc_io_pm': cfc_io_pm,
			'cfc_mem_p0': cfc_mem_p0,
			'cfc_mem_p1': cfc_mem_p1,
			'cfc_mem_pm': cfc_mem_pm
		}

		# Re-initialize SystemBooter to ensure it has the latest configuration - Might only need it here check later
		self._init_system_booter()

		# Apply global configuration
		#self._apply_global_boot_config()
		#print('Boot params -->', self.boot_params)
		# Execute boot using SystemBooter
		self.booter.boot(use_fastboot=self.Fastboot, **self.boot_params)

		# Copy fuse strings back for backward compatibility
		self.fuse_str = self.booter.fuse_str
		self.fuse_str_cbb = self.booter.fuse_str_cbb
		self.fuse_str_imh = self.booter.fuse_str_imh
		self.fuse_str_cbb_0 = self.booter.fuse_str_cbb_0
		self.fuse_str_cbb_1 = self.booter.fuse_str_cbb_1
		self.fuse_str_cbb_2 = self.booter.fuse_str_cbb_2
		self.fuse_str_cbb_3 = self.booter.fuse_str_cbb_3
		self.fuse_str_imh_0 = self.booter.fuse_str_imh_0
		self.fuse_str_imh_1 = self.booter.fuse_str_imh_1

	def fuse_checks(self):
		use_fastboot = self.Fastboot
		self.booter.verify_fuses(use_fastboot)

def gen_product_bootstring(bootopt = '', compute_config = 'X1', b_extra = '', _boot_disable_ia = '', _boot_disable_llc ='',fuse_string ='', fuse_files = '') -> str:

	# Future Releases will call a product_specific function here,
	chip = config.CHIPCONFIG.upper()

	if chip == 'SP':
		#_boot_string = f'{bootopt}(fused_unit=True, enable_strap_checks=False, compute_config="{compute_cofig}", segment="{segment}", enable_pm=True {b_extra}, {_boot_disable_ia} {_boot_disable_llc} {fuse_string} fuse_files_compute=[{_fuse_files_compute}], fuse_files_io=[{_fuse_files_io}])'
		_boot_string = f'{bootopt}(fused_unit=True, enable_strap_checks=False, compute_config="{compute_config}", enable_pm=True {b_extra},{_boot_disable_ia}{_boot_disable_llc}{fuse_string}{fuse_files})'

		#_boot_string = ('%s(fused_unit=False, pwrgoodmethod="usb", compute_config="%s", ia_core_disable={%s}, llc_slice_disable={%s}, fuse_str={"cbb_base":%s, "imh":%s})') % (bootopt, product[die]['compute_config'], _boot_disable_ia, _boot_disable_llc, _fuse_str_cbb, _fuse_str_imh)

		#_boot_string = ('%s(fused_unit=True, enable_strap_checks=False,enable_pm=True %s, %s %s %s fuse_files_compute=[%s], fuse_files_io=[%s])') % (bootopt, b_extra, _boot_disable_ia, _boot_disable_llc, fuse_string,_fuse_files_compute, _fuse_files_io)

	else:
		#_boot_string = f'{bootopt}(fused_unit=True, enable_strap_checks=False, compute_config="{compute_cofig}", segment="{segment}", enable_pm=True {b_extra}, {_boot_disable_ia} {_boot_disable_llc} {fuse_string} fuse_files_compute=[{_fuse_files_compute}], fuse_files_io=[{_fuse_files_io}])'
		_boot_string = f'{bootopt}(fused_unit=True, enable_strap_checks=False, compute_config="{compute_config}", enable_pm=True {b_extra},{_boot_disable_ia}{_boot_disable_llc}{fuse_string}{fuse_files})'
		#_boot_string = ('%s(fused_unit=True, enable_strap_checks=False,compute_config="%s",enable_pm=True,segment="%s" %s, %s %s %s fuse_files_compute=[%s], fuse_files_io=[%s])') % (bootopt, compute_cofig, segment, b_extra, _boot_disable_ia, _boot_disable_llc,fuse_string,_fuse_files_compute, _fuse_files_io)

	return _boot_string

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

		module_count = config.MODS_PER_CBB - _bitsoncount(module_mask) # enabled modules
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

		module_count = config.MODS_PER_CBB - _bitsoncount(LLC_mask) # Enabled Modules
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

## Helper: extract integer mask value from hardware register object or hex string
def _extract_mask_value(val):
	'''Return integer mask value from a register object, hex string, or integer.'''
	if hasattr(val, 'value'):
		return val.value
	if isinstance(val, str):
		return int(val, 16)
	return int(val)

## Helper: apply disable bits into an integer mask for a given CBB unit
def _apply_disable_bits(mask, unit_index, core_list, unit_size, disable_llc=False, llc_mask=None):
	'''
	Set disable bits in an IA (and optionally LLC) mask for all modules in core_list
	that belong to the given CBB unit.

	Input:
		mask: (int) Current IA disable mask for this CBB
		unit_index: (int) CBB index
		core_list: (List[int]) Global physical module numbers
		unit_size: (int) Number of physical modules per CBB (config.MODS_PER_CBB)
		disable_llc: (bool) If True, also apply bits to llc_mask
		llc_mask: (int) Current LLC disable mask (required if disable_llc is True)

	Output:
		Tuple (ia_mask, llc_mask) with updated values
	'''
	for core in core_list:
		if core // unit_size == unit_index:
			bit_pos = core % unit_size
			mask |= (1 << bit_pos)
			if disable_llc and llc_mask is not None:
				llc_mask |= (1 << bit_pos)
	return mask, llc_mask

## Generates external mask for Core Disable experiment (disables IA only, LLC unchanged)
def gen_core_disable_mask(core_list, current_masks=None):
	'''
	Generate an external mask with the specified modules disabled in the IA domain.
	The LLC mask is preserved from the current system mask.

	Input:
		core_list: (List[int]) List of global physical module numbers to disable (e.g. [62, 70])
		current_masks: (Dict, optional) Current system masks; if None, reads from hardware

	Output:
		result: (Dict) External mask dict with hex strings for ia_cbbX and llc_cbbX
	'''
	if current_masks is None:
		current_masks = dpm.fuses(rdFuses=True, sktnum=[0], printFuse=False)

	sv = _get_global_sv()
	result = {}

	for cbb in sv.socket0.cbbs:
		cbbN = cbb.instance
		cbb_name = cbb.name
		ia_mask = _extract_mask_value(current_masks[f'ia_{cbb_name}'])
		llc_mask = _extract_mask_value(current_masks[f'llc_{cbb_name}'])
		ia_mask, _ = _apply_disable_bits(ia_mask, cbbN, core_list, config.MODS_PER_CBB)
		result[f'ia_{cbb_name}'] = hex(ia_mask)
		result[f'llc_{cbb_name}'] = hex(llc_mask)

	print(Fore.CYAN + f'> Core Disable mask generated for modules: {core_list}' + Fore.WHITE)
	for key, val in result.items():
		print(Fore.CYAN + f'  {key}: {val}' + Fore.WHITE)

	return result

## Generates external mask for Slice Disable experiment (disables both IA and LLC)
def gen_slice_disable_mask(core_list, current_masks=None):
	'''
	Generate an external mask with the specified modules and their LLC slices disabled.

	Input:
		core_list: (List[int]) List of global physical module numbers to disable (e.g. [60, 72])
		current_masks: (Dict, optional) Current system masks; if None, reads from hardware

	Output:
		result: (Dict) External mask dict with hex strings for ia_cbbX and llc_cbbX
	'''
	if current_masks is None:
		current_masks = dpm.fuses(rdFuses=True, sktnum=[0], printFuse=False)

	sv = _get_global_sv()
	result = {}

	for cbb in sv.socket0.cbbs:
		cbbN = cbb.instance
		cbb_name = cbb.name
		ia_mask = _extract_mask_value(current_masks[f'ia_{cbb_name}'])
		llc_mask = _extract_mask_value(current_masks[f'llc_{cbb_name}'])
		ia_mask, llc_mask = _apply_disable_bits(ia_mask, cbbN, core_list, config.MODS_PER_CBB, disable_llc=True, llc_mask=llc_mask)
		result[f'ia_{cbb_name}'] = hex(ia_mask)
		result[f'llc_{cbb_name}'] = hex(llc_mask)

	print(Fore.CYAN + f'> Slice Disable mask generated for modules: {core_list}' + Fore.WHITE)
	for key, val in result.items():
		print(Fore.CYAN + f'  {key}: {val}' + Fore.WHITE)

	return result

## FastBoot Fuse Override
def fuse_cmd_override_reset(fuse_cmd_array, skip_init=False, boot = True, s2t=False, execution_state=None):
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
		#ipc.forcereconfig()
		#ipc.unlock()
		#sv.refresh()

		svStatus(refresh = (False if s2t else True))
		sv.sockets.imhs.fuses.load_fuse_ram() # Load IOs fuses
		sv.sockets.cbbs.base.fuses.load_fuse_ram() # Load computes fuses
		sv.sockets.cbbs.computes.fuses.load_fuse_ram() # Load computes fuses
		sv.sockets.imhs.fuses.go_offline() # Computes go offline
		sv.sockets.cbbs.base.fuses.go_offline() # IOs go offline
		sv.sockets.cbbs.computes.fuses.go_offline() # IOs go offline

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
	sv.sockets.cbbs.computes.fuses.flush_fuse_ram() # Load computes fuses
	sv.sockets.imhs.fuses.go_online() # Computes go online
	sv.sockets.cbbs.base.fuses.go_online() # IOs go online
	sv.sockets.cbbs.computes.fuses.go_online() # IOs go online

	try: ipc.go() # Restart threads
	except: print('Not able to restart threads... skipping...')
	if boot: # Reboot
		print(Fore.YELLOW + 'Rebooting unit with ipc.resettarget()')
		ipc.resettarget()

		if not s2t:
			print(Fore.YELLOW + '>>> Waiting for EFI... ')
			_wait_for_post(EFI_POST, sleeptime=EFI_POSTCODE_WT, timeout=EFI_POSTCODE_CHECK_COUNT, additional_postcode= LINUX_POST, execution_state=execution_state)
			fuse_cmd_override_check(fuse_cmd_array)

## Fuse Read --- Added to validate fuse application after bootscript is completed - either Fast or normal
def fuse_cmd_override_check(fuse_cmd_array, showresults = False, skip_init= False, bsFuses = None):

	sv = _get_global_sv()
	ipc = ipccli.baseaccess()
	## This part is just to complete the fuses in case they are coming from a Bootscript String


	bsf = 	{		'cbbs'	:'sv.sockets.cbbs.base.fuses.',
					'imhs'	:'sv.sockets.imhs.fuses.',
					'cbb0'	:'sv.sockets.cbb0.base.fuses.',
					'cbb1'	:'sv.sockets.cbb1.base.fuses.',
					'cbb2'	:'sv.sockets.cbb2.base.fuses.',
					'cbb3'	:'sv.sockets.cbb3.base.fuses.',
					'imh0'	:'sv.sockets.imh0.fuses.',
					'imh1'	:'sv.sockets.imh1.fuses.',
					'cbbstops':'sv.sockets.cbbs.computes.fuses.',
					'cbb0tops':'sv.sockets.cbb0.computes.fuses.',
					'cbb1tops':'sv.sockets.cbb1.computes.fuses.',
					'cbb2tops':'sv.sockets.cbb2.computes.fuses.',
					'cbb3tops':'sv.sockets.cbb3.computes.fuses.',
					'cbb0top0':'sv.sockets.cbb0.compute0.fuses.',
					'cbb0top1':'sv.sockets.cbb0.compute1.fuses.',
					'cbb0top2':'sv.sockets.cbb0.compute2.fuses.',
					'cbb0top3':'sv.sockets.cbb0.compute3.fuses.',
					'cbb1top0':'sv.sockets.cbb1.compute0.fuses.',
					'cbb1top1':'sv.sockets.cbb1.compute1.fuses.',
					'cbb1top2':'sv.sockets.cbb1.compute2.fuses.',
					'cbb1top3':'sv.sockets.cbb1.compute3.fuses.',
					'cbb2top0':'sv.sockets.cbb2.compute0.fuses.',
					'cbb2top1':'sv.sockets.cbb2.compute1.fuses.',
					'cbb2top2':'sv.sockets.cbb2.compute2.fuses.',
					'cbb2top3':'sv.sockets.cbb2.compute3.fuses.',
					'cbb3top0':'sv.sockets.cbb3.compute0.fuses.',
					'cbb3top1':'sv.sockets.cbb3.compute1.fuses.',
					'cbb3top2':'sv.sockets.cbb3.compute2.fuses.',
					'cbb3top3':'sv.sockets.cbb3.compute3.fuses.',
				}

	fuse_table = []
	All_true = True
	bserror = False
	if skip_init==False:

		svStatus(refresh = True)
		dpm.fuseRAM()

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

	if bserror:
		print(f"\n{Fore.RED}{'>'*3} Fuse data not checked some error during fuse read, check fuses array{Fore.WHITE}")
	elif All_true:
		print(f"\n{Fore.GREEN}{'>'*3} All fuses changed correctly{Fore.WHITE}")
	else:
		print(f"\n{Fore.RED}{'>'*3} Some fuses did not change correctly{Fore.WHITE}")

	# Print the table
	if (not All_true or showresults) and not bserror:
		print(tabulate(fuse_table, headers=["Fuse", "Requested", "System Value", "Changed"], tablefmt="grid"))

def check_compute_fuses(compute):
	'''
	Checks if the fuses in the compute match the requested values.

	Inputs:
		compute: (Compute Node) Compute to check fuses.
		fuse_cmd_array: (String Array) Input fuses to be checked.
	'''
	return compute in sv.sockets.cbbs.computes.name

def check_cbb_fuses(cbb):
	'''
	Checks if the fuses in the cbb match the requested values.

	Inputs:
		cbb: (CBB Node) CBB to check fuses.
		fuse_cmd_array: (String Array) Input fuses to be checked.
	'''
	return cbb in sv.sockets.cbbs.name

def check_imh_fuses(imh):
	'''
	Checks if the fuses in the cbb match the requested values.

	Inputs:
		cbb: (CBB Node) CBB to check fuses.
		fuse_cmd_array: (String Array) Input fuses to be checked.
	'''
	return imh in sv.sockets.imhs.name

#========================================================================================================#
#=============== DEBUG SCRIPTS ==========================================================================#
#========================================================================================================#

def svStatus(checkipc: bool = True, checksvcores: bool = True, refresh: bool = False, reconnect: bool = False) -> None:
	"""
	Check and display system status for IPC and SV components.

	Args:
		checkipc: Check IPC thread status
		checksvcores: Check SV core data availability
		refresh: Force refresh of IPC and SV data
		reconnect: Reconnect IPC before checking
	"""
	from namednodes import sv

	# Constants for better performance (avoid repeated attribute lookups)
	ipc = ipccli.baseaccess()

	# Simple ASCII symbols (log-friendly)
	OK = "[OK]"
	FAIL = "[FAIL]"
	WARN = "[WARN]"
	INFO = "[>>]"

	# Pre-compute separator lines
	HEADER_LINE = f"{Fore.CYAN}{'=' * 70}{Fore.WHITE}"
	SEPARATOR = f"{Fore.CYAN}{'-' * 70}{Fore.WHITE}"

	# State tracking
	ipcBad = svBad = False
	ipcthreads = svcoredara = None
	svcores = 0

	# Print header
	print(f"\n{HEADER_LINE}")
	print(f"{Fore.CYAN}  SYSTEM STATUS CHECK{Fore.WHITE}")
	print(f"{HEADER_LINE}\n")

	# Reconnect if requested
	if reconnect:
		print(f"{Fore.YELLOW}{INFO}{Fore.WHITE} IPC Reconnect: Reconnecting to target...")
		ipc.reconnect()
		print(f"      {Fore.GREEN}{OK}{Fore.WHITE} Reconnection complete\n")

	# Force refresh if requested
	if refresh:
		print(f"{Fore.YELLOW}{INFO}{Fore.WHITE} Force Refresh: Refreshing IPC and SV data...")
		ipc.unlock()
		ipc.forcereconfig()
		sv.refresh()
		print(f"      {Fore.GREEN}{OK}{Fore.WHITE} Refresh complete\n")

	# Initialize checks
	print(f"{Fore.LIGHTCYAN_EX}[1/4]{Fore.WHITE} Initializing system checks...")
	ipclocked = ipc.islocked()
	sv_status = not sv.sockets

	# Check IPC status
	if checkipc:
		print(f"{Fore.LIGHTCYAN_EX}[2/4]{Fore.WHITE} Checking IPC status...", end=" ", flush=True)
		try:
			ipcstatus = ipc.isrunning()
			ipcthreads = f'{Fore.GREEN}{OK} Running{Fore.WHITE}' if ipcstatus else f'{Fore.YELLOW}{WARN} Halted{Fore.WHITE}'
			print(f"{Fore.GREEN}{OK}{Fore.WHITE}" if ipcstatus else f"{Fore.YELLOW}{WARN}{Fore.WHITE}")
		except Exception:
			ipcthreads = f'{Fore.RED}{FAIL} Down{Fore.WHITE}'
			ipcBad = True
			print(f"{Fore.RED}{FAIL}{Fore.WHITE}")

	# Check SV Core data
	if checksvcores:
		print(f"{Fore.LIGHTCYAN_EX}[3/4]{Fore.WHITE} Checking SV core data...", end=" ", flush=True)
		try:
			svcores = len(sv.sockets.cpu.modules)
			svcoredara = f'{Fore.GREEN}{OK} Up ({svcores} cores){Fore.WHITE}'
			print(f"{Fore.GREEN}{OK}{Fore.WHITE}")
		except Exception:
			svcoredara = f'{Fore.RED}{FAIL} Down{Fore.WHITE}'
			svBad = True
			print(f"{Fore.RED}{FAIL}{Fore.WHITE}")

	print(f"{Fore.LIGHTCYAN_EX}[4/4]{Fore.WHITE} Compiling results...\n")

	# Build status table with simple ASCII
	SysStatus = [
		[f"{Fore.CYAN}Feature{Fore.WHITE}", f"{Fore.CYAN}Status{Fore.WHITE}"],
		["IPC Lock State", f'{Fore.RED}{FAIL} Locked{Fore.WHITE}' if ipclocked else f'{Fore.GREEN}{OK} Unlocked{Fore.WHITE}']
	]

	# Conditionally add rows
	if checkipc and ipcthreads:
		SysStatus.append(["IPC Threads", ipcthreads])

	SysStatus.append([
		"SV Initialization",
		f'{Fore.RED}{FAIL} Not Ready{Fore.WHITE}' if sv_status else f'{Fore.GREEN}{OK} Ready{Fore.WHITE}'
	])

	if checksvcores and svcoredara:
		SysStatus.append(["SV Core Data", svcoredara])

	# Print table with simple grid
	print(tabulate(SysStatus, headers="firstrow", tablefmt="simple_grid"))
	print()

	# Recovery actions
	recovery_needed = False

	if ipclocked or ipcBad:
		recovery_needed = True
		print(f"{Fore.YELLOW}{INFO}{Fore.WHITE} Recovery Action: IPC not ready, performing unlock and reconfig...")
		ipc.unlock()
		ipc.forcereconfig()
		print(f"      {Fore.GREEN}{OK}{Fore.WHITE} IPC recovery complete")

	if not sv.sockets or svBad:
		recovery_needed = True
		print(f"{Fore.YELLOW}{INFO}{Fore.WHITE} Recovery Action: SV not initialized, refreshing...")
		sv.refresh()
		print(f"      {Fore.GREEN}{OK}{Fore.WHITE} SV refresh complete")

	# Final status summary
	print(f"\n{SEPARATOR}")
	system_ready = sv.sockets and ipc.isunlocked()

	if system_ready:
		print(f"{Fore.GREEN}{OK} SYSTEM READY{Fore.WHITE} - SV unlocked with updated nodes")
	elif recovery_needed:
		print(f"{Fore.YELLOW}{WARN} RECOVERY APPLIED{Fore.WHITE} - System may require verification")
	else:
		print(f"{Fore.RED}{FAIL} SYSTEM NOT READY{Fore.WHITE} - Manual intervention required")

	print(f"{SEPARATOR}\n")


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

def CheckModule(global_physical_module, masks):
	'''
	Checks if input Module is enabled in the system

	Inputs:
		global_physical_module: (Int) Module to check.

	Output:
		module_status: (Boolean) True if enabled, False if disabled.
	'''
	target_cbb = int(global_physical_module / config.MODS_PER_CBB) # Target compute
	# masks = dpm.fuses(system = sv.socket0.target_info["device_name"], rdFuses = True, sktnum =[0]) # Get LLC and Module masks

	compute_mask = masks[f'ia_cbb{target_cbb}'].value # Target mask
	local_physical = global_physical_module - config.MODS_PER_CBB*target_cbb # Local module
	module_status = _bit_check(compute_mask, local_physical) # Check if mask contains local module

	return module_status

def CheckMasks(readfuse = True, extMasks=None):
	'''
	Returns unit Module and LLC masks, and a dictionary containing all the global physcial enabled Modules and LLCs

	Input:
		readfuse: (Boolean, Default=True) read fuses to get masks.

	Outputs:
		masks: (Dictionary) contains all Modules and LLC masks for every compute.
		array: (Dictionary) contains all enabled Modules and LLCs for every mask.
	'''
	sv = _get_global_sv() # init SV
	if extMasks in [None, "None", 'Default', '', ' ']:
		masks = dpm.fuses(rdFuses = readfuse, sktnum =[0], printFuse=False)

	else:
		print(Fore.YELLOW +' !!! Using External masking as base instead of system values' + Fore.WHITE)
		print(Fore.YELLOW +f' !!! ({type(extMasks)} : {extMasks})' + Fore.WHITE)
		masks = extMasks

	array = {'CORES':{},
				'LLC':{}} # Dictionary to save both masks

	for cbb in sv.socket0.cbbs: # For each Compute
		cbb_name = cbb.name
		cbbN = int(cbb.target_info.instance)
		_ia = masks[f'ia_{cbb_name}'].value if extMasks == None else int(masks[f'ia_{cbb_name}'],16)# module mask
		_slices = masks[f'llc_{cbb_name}'].value if extMasks == None else int(masks[f'llc_{cbb_name}'],16) # LLC mask

		ia = _enabled_bit_array(_ia) # get physical indexes of enabled modules
		ia_array = [x + ((cbbN)*config.MODS_PER_CBB) for x in ia] # Put previous indexes as global physical indexes in an array

		llcs = _enabled_bit_array(_slices) # get physical indexes of enabled LLCs
		llc_array = [x + ((cbbN)*config.MODS_PER_CBB) for x in llcs] # Put previous indexes as global physical indexes in an array

		array['CORES'][cbb_name] = ia_array # Add module indexes array into the return dictionary
		array['LLC'][cbb_name] = llc_array # Add LLC indexes array into the return dictionary

	return masks, array

def modulesEnabled(moduleslicemask=None, logical=False, skip = False, print_modules = True, print_llcs = True, rdfuses=True):
	'''
	Prints a  mini-tileview table of enabled modules

	Input:
		moduleslicemask: (Dictionary, Default=None) module mask override.
		logical: (Boolean, Default=False) if moduleslicemask should be treated as logical or physical.
		skip: (Boolean, Default=False) Skip tileview print. Module and LLC masks are still printed.
		print_modules: (Boolean, Default=True) display modules in tileview
		print_llcs: (Boolean, Default=True) display LLCs in tileview
	'''

	def _build_table_cbb(cbb, module_name, c0, c1, r0,r1, cols, mask):

		cbbN = int(cbb.target_info.instance)
		cbb_name = cbb.name
		return_array = []

		for row in range(r0,r1):
			row_string = []

			for col in range(c0,c1):
				data = cols[f'C{col}'][row]
				if type(data) == str:
					if 'MDF' in data: color = Fore.YELLOW
					elif 'XB' in data: color = Fore.YELLOW
					else: color = Fore.LIGHTWHITE_EX
					row_string.append(color + data + Fore.WHITE)
				else:

					module_data = _module_string(data, mask[cbb_name], cbbN)
					tabledata = f'{module_name}\n{module_data}'

					row_string.append(tabledata)

			return_array.append(row_string)

		return return_array

	def _build_table_imh(imh: str, rows_data: dict ):
		tile_io = []
		headers_io = []
		headers_io.append("R/C")
		for c in range (0,9): headers_io.append(f'COL{c}')

		if imh not in rows_data.keys():
			return

		print(F'\nDIE: {imh.upper()}\n')

		# Get Data for current imh
		rows_imh = rows_data[imh]

		for key in rows_imh.keys():
			row_string = []
			for row in rows_imh[key]:
				if 'MDF' in row:
					color = Fore.YELLOW
					width = cellwith
				else:
					color = Fore.LIGHTWHITE_EX
					width = 4
				row_string.append(color + f"{row.center(width)}"+ Fore.WHITE)
			tile_io.append(row_string)
		table = tabulate(tile_io, headers=headers_io, tablefmt="grid")
		print(table)

	def _gen_cbb_tiledata(tile_cbss, cbb_name, row_string):
		"""
		Merges row_string data from modules, xbar/shaft, and llcs into complete rows in tile_cbss.
		Each complete row will have 13 columns: [ROW label, 4 module cols, 4 shaft cols, 4 llc cols]

		Args:
			tile_cbss: Dictionary where merged rows will be appended
			cbb_name: CBB identifier key for tile_cbss
			row_string: Dictionary with keys 'modules', 'xbar', 'llcs', each containing row arrays
		"""
		# Get the number of rows (should be same across all sections)
		num_rows = len(row_string['modules']) if row_string['modules'] else 0

		# Merge each row horizontally across the three sections
		for row_idx in range(num_rows):
			merged_row = []

			# Add the ROW# index as the first column
			merged_row.append(f'ROW{row_idx}')

			# Add module columns (all columns from modules section)
			if row_string['modules'] and len(row_string['modules'][row_idx]) > 0:
				merged_row.extend(row_string['modules'][row_idx])

			# Add xbar/shaft columns (all columns from xbar section)
			if row_string['xbar'] and len(row_string['xbar'][row_idx]) > 0:
				merged_row.extend(row_string['xbar'][row_idx])

			# Add LLC columns (all columns from llcs section)
			if row_string['llcs'] and len(row_string['llcs'][row_idx]) > 0:
				merged_row.extend(row_string['llcs'][row_idx])

			# Append the complete merged row to tile_cbss
			tile_cbss[cbb_name].append(merged_row)

	sv = _get_global_sv() # init sv
	die = sv.socket0.target_info["device_name"] # Get die name

	max_modules_cbb = config.MODS_PER_CBB # Modules per compute

	masks = dpm.fuses(rdFuses = rdfuses, sktnum =[0]) # Get Module and LLC masks

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
		ios_tile = socket.imhs.name # IO Name
		cbbs_tile = socket.cbbs # Compute names
		logicalStringCore = 0x0 # Logical core string
		logicalStringLLC = 0x0 # Logical LLC string

		if skip: # Skip tileview
			print('Tileview option skipped .... ')
		else:   #Build Tileview
			print  ("Building Tileview for : %s" % (socket.name))
			for cbb in cbbs_tile: # For each compute name
				cbb_name = cbb.name
				cbb_number = cbb.instance
				# cbb_name = cbb.name
				# cbbN = int(cbb.target_info.instance) # Compute id
				if logical == False: # Get Module and LLC info through physical into logical conversions
					log_module_dis_mask[cbb_name] = _module_mask_phy_to_log(moduleslicemask[f'ia_{cbb_name}'])
					phy_module_dis_mask[cbb_name] = moduleslicemask[f'ia_{cbb_name}']
					log_llc_dis_mask[cbb_name] = _module_mask_phy_to_log(moduleslicemask[f'llc_{cbb_name}'])
					phy_llc_dis_mask[cbb_name] = moduleslicemask[f'llc_{cbb_name}']
					logicalStringCore +=  log_module_dis_mask[cbb_name] << (config.MAXLOGICAL*cbb_number)
					logicalStringLLC += log_llc_dis_mask[cbb_name] << (config.MAXLOGICAL*cbb_number)
				else: # Get Module and LLC info through logical into physical conversions
					phy_module_dis_mask[cbb_name] = _module_mask_log_to_phy(moduleslicemask[f'ia_{cbb_name}'])
					log_module_dis_mask[cbb_name] = moduleslicemask[f'ia_{cbb_name}']
					phy_llc_dis_mask[cbb_name] = _module_mask_log_to_phy(moduleslicemask[f'llc_{cbb_name}'])
					log_llc_dis_mask[cbb_name] = moduleslicemask[f'llc_{cbb_name}']

			headers = [] # Table headers
			headers.append("R/C") # Row Column header
			# 4 module columns + 4 xbar/shaft columns + 4 LLC columns = 12 total (with R/C = 13)

			if print_modules:
				for c in range(0, 4): headers.append(f'DCM{c}')  # Module columns

			headers.append('TOP')  # Shaft/XBar columns
			#headers.append(f'SHAFT')  # Shaft/XBar columns
			headers.append('BASE')  # Shaft/XBar columns

			if print_llcs:
				for c in range(0, 4): headers.append(f'CL{c}')  # LLC columns

			MDFlabel = '---- MDF ----' # MDF
			cellwith = len(MDFlabel) # size of MDF string to keep everything in line
			tile_io0 =[] # io0 tile
			tile_io1 =[] # io1 tile
			MDF_string  = [] # MDF string

			tile_cbss = {} # compute names
			for cbb_name in sv.socket0.cbbs.name: # For each compute name
				tile_cbss[cbb_name] = [] # Assign empty array to each compute name

			# Leaving this one here for now, not used for the moment

			cols = {'C0':[0,4,8,12,16,20,24,28], #DCM0 column
					'C1':[1,5,9,13,17,21,25,29], #DCM1 column
					'C2':[2,6,10,14,18,22,26,30], #DCM2 column
					'C3':[3,7,11,15,19,23,27,31], #DCM3 column
					'C4':['XB','XB','XB','XB','XB','XB','XB','XB'], # TOP column
					#'C5':[' ','','','','','','',''], # SHAFT column
					'C5':['XB','XB','XB','XB','XB','XB','XB','XB'], # BASE column
					'C6':[0,4,8,12,16,20,24,28], #CL0 column
					'C7':[1,5,9,13,17,21,25,29], #CL1 column
					'C8':[2,6,10,14,18,22,26,30], #CL2 column
					'C9':[3,7,11,15,19,23,27,31], #CL3 column
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

			rows_io = {	'imh0':{'R0':['ROW0','MC0','D2D\nCBB0','','','','','','D2D\nCBB2','MC4'],
				 				'R1':['ROW1','MC1','','SCA','UBOX\nHIOP','HIOP','HIOP','SCA','','MC5'],
				 				'R2':['ROW2','MC2','D2D\nD2D0','SCA','UBOX\nHIOP','HIOP','HIOP','SCA','D2D\nD2D1','MC6'],
								'R3':['ROW2','MC2','D2D\nCBB1','','','','','','D2D\nCBB3','MC7']},

						'imh1' : {	'R0':['ROW0','MC0','D2D\nCBB0','','','','','','D2D\nCBB2','MC4'],
				 				'R1':['ROW1','MC1','','SCA','UBOX\nHIOP','HIOP','HIOP','SCA','','MC5'],
				 				'R2':['ROW2','MC2','D2D\nD2D0','SCA','UBOX\nHIOP','HIOP','HIOP','SCA','D2D\nD2D1','MC6'],
								'R3':['ROW2','MC2','D2D\nCBB1','','','','','','D2D\nCBB3','MC7']}
					} # IO rows


			rows_num = len(rows.keys()) # number of rows

			# Generate IO Table -- Static
			for imh in ios_tile:
				_build_table_imh(imh.lower(), rows_io)

			# Generate CBB Table -- Dynamic
			for cbb in cbbs_tile:
				cbb_name = cbb.name
				modulesmask = moduleslicemask[f'ia_{cbb_name}']# & 0x7fff

				modules_per_cbb = config.MODS_PER_CBB - _bitsoncount(modulesmask)

				print  (f"{cbb_name}: %d modules enabled: 0x%x" % (modules_per_cbb, modulesmask))
				print  (f"Input module disables mask ->    {cbb_name}: 0x%x" % moduleslicemask[f'ia_{cbb_name}'])
				print  (f"Logical module disables mask ->    {cbb_name}: 0x%x" % log_module_dis_mask[f'{cbb_name}'])
				print  (f"Physical module disables mask ->    {cbb_name}: 0x%x" % phy_module_dis_mask[f'{cbb_name}'])
				print("\n\nCore Tileview Map ---> physical:logical")

				# for cbb in sv.socket0.cbbs:
					# cbb_name = cbb.name
				print (f'\nDIE: {cbb_name.upper()}\n')
				row_string = {'modules':[], 'xbar':[], 'llcs':[]}

				if print_modules:
					print('--- MODULES ENABLED VIEW ---')
					row_string['modules'] = _build_table_cbb(cbb, module_name= 'MOD', c0=0, c1=4, r0=0, r1=rows_num, cols=cols, mask=phy_module_dis_mask)

				# Generate CrossBar and Shaft
				row_string['xbar'] = _build_table_cbb(cbb, module_name= '', c0=4, c1=6, r0=0, r1=rows_num, cols=cols, mask=None)

				if print_llcs:
					print('--- LLCs ENABLED VIEW ---')
					row_string['llcs'] = _build_table_cbb(cbb, module_name= 'CBO', c0=6, c1=10, r0=0, r1=rows_num, cols=cols, mask=phy_llc_dis_mask)

				# Merge the modules, xbar, and llcs data into complete rows in tile_cbss
				_gen_cbb_tiledata(tile_cbss, cbb_name, row_string)

				# Display the complete tileview table
				table = tabulate(tile_cbss[cbb_name], headers=headers, tablefmt="grid")

				print(table)

			if not logical:
				bitstringlen = len(tile_cbss)*config.MAXLOGICAL
				print('\n>>> CLASS Masking Bitstrings\n')
				print(f'>>> CLASS {config.CORESTRING}s Mask Bitstring: 0b{bin(logicalStringCore)[2:].zfill(bitstringlen)}')
				print(f'>>> CLASS LLCs Mask Bitstring:  0b{bin(logicalStringLLC)[2:].zfill(bitstringlen)}\n')

def read_postcode():
	'''
	reads register
		sv.socket0.imh0.ubox.ncdecs.biosnonstickyscratchpad_mem[7]
	'''
	try:
		pc = sv.socket0.imh0.ubox.ncdecs.biosnonstickyscratchpad_mem[7]
	except Exception as e:
		pc = None
		print(Fore.RED + f"Error reading BIOS POST code: {e}" + Fore.WHITE)

	return pc

def clear_biosbreak():
	'''
	Sets register
		sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg = 0
	'''
	# sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg=0 # Set register to 0
	sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6]=0

def go_to_efi(execution_state = None):
	'''
	Execute clear_biosbreak(), then waits for the unit to read EFI postcode (0x57000000).
	Maximum wait time: 10 minutes
	'''
	print(Fore.YELLOW +'\n>>> Reenabling boot going to EFI ---\n')
	if check_user_cancel(execution_state):
		return
	svStatus()
	if (itp.ishalted() == False): itp.halt()
	clear_biosbreak() # Set register to 0
	if (itp.ishalted() == True): itp.go()

	_wait_for_post(EFI_POST, sleeptime=EFI_POSTCODE_WT, timeout = EFI_POSTCODE_CHECK_COUNT, additional_postcode = LINUX_POST,execution_state=execution_state)

def _wait_for_post(postcode, sleeptime = 3, timeout = 10, additional_postcode = None, execution_state=None):
	'''
	Waits for the unit to reach a desired postcode.
	If timeout is exceeded, print a message stating the postcode was not reached.

	Inputs:
		postcode: (Hex) desired postcode to reach.
		sleeptime: (Int, Default=3) seconds to wait for each sleep cycle.
		timeout: (Int, Default=10) timeout counter reduced by 1 at the end of every sleep cycle. If timeout is exceeded, print a message stating the postcode was not reached.
	'''
	done=False
	# current_post = sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg # Current postcode
	current_post = read_postcode()
	PC = f'{postcode:#x}' if additional_postcode == None else f'{postcode:#x} or {additional_postcode:#x}'
	print (Fore.YELLOW + ">>> WAITING for postcode: %s <---> Current Postcode: 0x%x" % (PC, current_post)+ Fore.RESET)
	while(not done): # While target post has not been reached
		time.sleep(sleeptime) # Sleep for N seconds
		if check_user_cancel(execution_state=execution_state):
			return
		prev_post = current_post
		current_post = read_postcode() # New current postcode
		print (Fore.YELLOW + ">>> WAITING for postcode: %s <---> Current Postcode: 0x%x" % (PC, current_post)+ Fore.RESET)

		if (prev_post == current_post): # Same postcode as N seconds earlier
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

def _logical_to_physical(logModule, cbb_instance=None):
	'''
	Given a logical module (local or global), return the corresponding global physical module.

	Input:
		logModule: (Int) logical module, this can be local or global value.
		compute_instance: (Int, Default=None) if given, return corresponding global physical module for that compute.

	Outputs:
		physicalModule: (Int) corresponding global physical value.
	'''

	if cbb_instance == None: cbb_instance = int(logModule/config.MODS_ACTIVE_PER_CBB) # If no compute was given, calculate it from given global logical module

	local_logical = logModule % config.MODS_ACTIVE_PER_CBB # If a global logical was given, reduce it to local logical
	local_offset = cbb_instance* config.MODS_PER_CBB # Add physical offset based on desired (or calculated) compute. If compute=0, offset=0

	physicalModule = config.classLogical2Physical[local_logical] + local_offset # Extract local physical from dictionary, then add offset if compute>0
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
	if cbb_instance == None: cbb_instance = int(physModule/config.MODS_PER_CBB) # If no compute was given, calculate it from given global physical module

	local_physical = physModule % config.MODS_PER_CBB # If a global physical was given, reduce it to local physical
	local_offset = cbb_instance * config.MODS_ACTIVE_PER_CBB # Add logical offset based on desired (or calculated) compute. If compute=0, offset=0

	if local_physical in config.physical2ClassLogical: # If physical value has an associated logical value
		logicalModule = config.physical2ClassLogical[local_physical] + local_offset # Extract local logical from dictionary, then add offset if compute>0
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
	phys_module = phys_module%config.MODS_PER_CBB # Local module if global value was given
	if phys_module in config.phys2colrow: # If physical module is present in 'coretile' (moduletile?)
		row = config.phys2colrow[phys_module][1] # Get row value from dictionary
		column = config.phys2colrow[phys_module][0] # Get column value from dictionary
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

	for physical_mod in range(0,config.MODS_PER_CBB): # for each possible physical module position
		if ((phy_module_mask >> physical_mod) & 1 == 1) and physical_mod not in config.skip_physical_modules: # If current module is disabled, and this module is not part of the skip list
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

	for logical_mod in range(0,config.MODS_ACTIVE_PER_CBB): # For each possible logical module position
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
	maxphysical = config.MODS_PER_CBB # MAX physical modules per compute

	if phys_module in config.skip_physical_modules: # If physical module not enabled in CWF
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
	ipc = _get_global_ipc()
	print (Fore.YELLOW + f"Checking APIC IDs for {config.CORESTRING}: [ {phys_module} ]... Please Wait..." + Fore.RESET )
	try:
		if ipc.isrunning: ipc.halt()
	except Exception as e:
		print(Fore.RED  +f'IPC Failed with Exception {e}'+ Fore.RESET)
		print(Fore.RED  + 'Unable Halt the unit, script will continue, assure there is no issue with IPC.' + Fore.RESET )

	if phys_module == None: phys_module = global_slice_core
	cbb_index = int(phys_module/config.MODS_PER_CBB)
	compute_index =  int((phys_module % config.MODS_PER_CBB) / config.MODS_PER_COMPUTE)
	product = config.SELECTED_PRODUCT
	id0 = None
	id1 = None

	# Product Specific APIC ID Logic -- Checks for each Thread Value
	try:

		id0, id1 = pf.core_apic_id(phys_module, cbb_index, compute_index, sv, id0, id1)
	except:
		print(Fore.RED  + 'Not able to collect APIC IDs Data'+ Fore.RESET)

	try:
		if ipc.ishalted: ipc.go()
	except Exception as e:
		print(Fore.RED  + f'IPC Failed with Exception {e}'+ Fore.RESET)
		print(Fore.RED  + 'Not able to take the unit out of Halt state'+ Fore.RESET)

	print (Fore.YELLOW + f"{config.CORESTRING}{phys_module}: LOWER APIC: {id0} HIGHER APIC: {id1}" + Fore.RESET )

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

def _enabled_bit_array(value, max_bit = config.MODS_PER_CBB):
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

