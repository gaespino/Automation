"""
SystemBooter Module
===================

This module provides a clean, reusable interface for system boot operations.
It encapsulates all boot-related functionality including:
- Boot configuration (frequencies, voltages, fuses)
- Boot execution (bootscript and fastboot)
- Fuse verification and validation
- Retry logic for robust boot operations

Changelog:
- Version 1.0 (January 2025): Initial extraction from DMRCoreManipulation

"""

import time
import os
from typing import Dict, List, Optional, Union
from colorama import Fore, Back, Style
import ipccli
from tabulate import tabulate


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
	
	def apply_global_overrides(self, global_config: Dict):
		"""Apply global configuration overrides from a dictionary"""
		for key, value in global_config.items():
			if hasattr(self, key) and value is not None:
				setattr(self, key, value)
	
	def apply_fixed_frequencies(self):
		"""Apply fixed frequency settings across all related parameters"""
		if self.fixed_core_freq is not None:
			self.ia_fw_p1 = self.fixed_core_freq
			self.ia_fw_pn = self.fixed_core_freq
			self.ia_fw_pm = self.fixed_core_freq
			self.ia_fw_pboot = self.fixed_core_freq
			self.ia_fw_pturbo = self.fixed_core_freq
		
		if self.fixed_mesh_freq is not None:
			self.cfc_fw_p0 = self.fixed_mesh_freq
			self.cfc_fw_p1 = self.fixed_mesh_freq
			self.cfc_fw_pm = self.fixed_mesh_freq
			self.cfc_cbb_p0 = self.fixed_mesh_freq
			self.cfc_cbb_p1 = self.fixed_mesh_freq
			self.cfc_cbb_pm = self.fixed_mesh_freq
			self.cfc_io_p0 = self.fixed_mesh_freq
			self.cfc_io_p1 = self.fixed_mesh_freq
			self.cfc_io_pm = self.fixed_mesh_freq
			self.cfc_mem_p0 = self.fixed_mesh_freq
			self.cfc_mem_p1 = self.fixed_mesh_freq
			self.cfc_mem_pm = self.fixed_mesh_freq
	
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
		print(f'\tCore Frequencies:')
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
		print(f'\tCompute Mesh Frequencies:')
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
		print(f'\tVoltage Bumps Configurations:' if self.vbumps_configuration else f'\tFixed Voltage Configurations:')
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
		self.execution_state = system_config.get('execution_state', None)
		self.fuse_2CPM = system_config.get('fuse_2CPM', [])
		self.fuse_1CPM = system_config.get('fuse_1CPM', [])
		
		# Boot configuration
		self.config = BootConfiguration()
		
		# Fuse strings storage
		self.fuse_str = []
		self.fuse_str_cbb = []
		self.fuse_str_cbb_0 = []
		self.fuse_str_cbb_1 = []
		self.fuse_str_cbb_2 = []
		self.fuse_str_cbb_3 = []
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
			**boot_params: Boot parameters to override defaults
		"""
		# Update configuration with provided parameters
		for key, value in boot_params.items():
			if hasattr(self.config, key):
				setattr(self.config, key, value)
		
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
		# Import functions from DMRCoreManipulation in the same directory
		from DMRCoreManipulation import (
			gen_product_bootstring, 
			AFTER_MRC_POST,
			_wait_for_post,
			MRC_POSTCODE_WT,
			MRC_POSTCODE_CHECK_COUNT,
			BOOT_STOP_POSTCODE,
			BOOT_POSTCODE_WT,
			BOOT_POSTCODE_CHECK_COUNT,
			EFI_POST,
			EFI_POSTCODE_WT,
			EFI_POSTCODE_CHECK_COUNT,
			LINUX_POST,
			check_user_cancel,
			BOOTSCRIPT_RETRY_TIMES,
			BOOTSCRIPT_RETRY_DELAY
		)
		
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
		boot_pass = self._retry_boot(
			boot_string=self.boot_string,
			bootcont=bootcont,
			n=BOOTSCRIPT_RETRY_TIMES,
			delay=BOOTSCRIPT_RETRY_DELAY
		)
		
		if not boot_pass:
			raise ValueError("!!!FAIL -- Max number of bootscript retries reached")
		elif boot_pass == 'Cancel':
			raise InterruptedError('Boot Interrupted by user')
	
	def _execute_fastboot(self):
		"""Execute boot using fastboot method with itp.resettarget()"""
		from DMRCoreManipulation import (
			fuse_cmd_override_reset,
			_wait_for_post,
			AFTER_MRC_POST,
			MRC_POSTCODE_WT,
			MRC_POSTCODE_CHECK_COUNT,
			BOOT_STOP_POSTCODE,
			BOOT_POSTCODE_WT,
			BOOT_POSTCODE_CHECK_COUNT,
			EFI_POST,
			EFI_POSTCODE_WT,
			EFI_POSTCODE_CHECK_COUNT,
			LINUX_POST,
			mask_fuse_module_array,
			mask_fuse_llc_array
		)
		
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
		_fuse_str_io = []
		
		# Get fuse configurations from system config
		from DMRCoreManipulation import (
			HIDIS_COMP,
			HTDIS_IO,
			VP2INTERSECT,
			FUSES_600W_COMP,
			FUSES_600W_IO
		)
		
		# HT disable
		if self.config.ht_dis:
			_fuse_str_cbb += HIDIS_COMP
			_fuse_str_imh += HTDIS_IO
		
		# 2CPM disable
		if self.config.dis_2CPM is not None:
			_fuse_str_cbb += self.fuse_2CPM
		
		# 1CPM disable
		if self.config.dis_1CPM is not None:
			_fuse_str_cbb += self.fuse_1CPM
		
		# 600W configuration
		if self.config.u600w:
			_fuse_str_cbb += FUSES_600W_COMP
			_fuse_str_imh += FUSES_600W_IO
		
		# VP2INTERSECT enable
		if self.config.vp2intersect_en:
			_fuse_str_cbb += VP2INTERSECT.get('bs', [])
		
		# Frequency configurations
		self._apply_frequency_fuses(_fuse_str_cbb, _fuse_str_imh)
		
		# License mode configuration
		self._apply_license_mode(_fuse_str_cbb)
		
		# Clean up fuse strings
		if _fuse_str_cbb:
			_fuse_str_cbb = [val.replace("sv.sockets.cbbs.base.", "") for val in _fuse_str_cbb]
		
		if _fuse_str_imh:
			_fuse_str_imh = [val.replace("sv.sockets.imhs.", "") for val in _fuse_str_imh]
		
		# Apply PPVC fuses if configured
		self._apply_ppvc_fuses(_fuse_str_cbb, _fuse_str_imh)
		
		# Store fuse strings
		self.fuse_str_cbb = _fuse_str_cbb
		self.fuse_str_imh = _fuse_str_imh
	
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
		if self.config.ia_fw_pn:
			fuse_str_cbb.extend(self._assign_values_to_regs(
				self.boot_fuses['IA']['fwFreq']['pn'], self.config.ia_fw_pn))
		if self.config.ia_fw_pm:
			fuse_str_cbb.extend(self._assign_values_to_regs(
				self.boot_fuses['IA']['fwFreq']['min'], self.config.ia_fw_pm))
		if self.config.ia_fw_pboot:
			fuse_str_cbb.extend(self._assign_values_to_regs(
				self.boot_fuses['IA']['fwFreq']['boot'], self.config.ia_fw_pboot))
		if self.config.ia_fw_pturbo:
			fuse_str_cbb.extend(self._assign_values_to_regs(
				self.boot_fuses['IA']['fwFreq']['turbo'], self.config.ia_fw_pturbo))
	
	def _apply_license_mode(self, fuse_str_cbb: List[str]):
		"""Apply AVX license mode configuration"""
		if self.config.avx_mode is None:
			return
		
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
	
	def _apply_ppvc_fuses(self, fuse_str_cbb: List[str], fuse_str_imh: List[str]):
		"""Apply PPVC fuse configurations"""
		if not self.ppvc_fuses:
			return
		
		# Split fuse strings by CBB/IMH
		for cbb in self.cbbs:
			cbb_name = cbb.name.lower() if hasattr(cbb, 'name') else str(cbb).lower()
			if 'cbb0' in cbb_name:
				self.fuse_str_cbb_0.extend(self.ppvc_fuses.get('cbb0', []))
			if 'cbb1' in cbb_name:
				self.fuse_str_cbb_1.extend(self.ppvc_fuses.get('cbb1', []))
			if 'cbb2' in cbb_name:
				self.fuse_str_cbb_2.extend(self.ppvc_fuses.get('cbb2', []))
			if 'cbb3' in cbb_name:
				self.fuse_str_cbb_3.extend(self.ppvc_fuses.get('cbb3', []))
		
		for imh in self.imhs:
			imh_name = imh.name.lower() if hasattr(imh, 'name') else str(imh).lower()
			if 'imh0' in imh_name or 'io0' in imh_name:
				self.fuse_str_imh_0.extend(self.ppvc_fuses.get('imh0', []))
			if 'imh1' in imh_name or 'io1' in imh_name:
				self.fuse_str_imh_1.extend(self.ppvc_fuses.get('imh1', []))
		
		# Append base fuse strings
		self.fuse_str_cbb_0.extend(fuse_str_cbb)
		self.fuse_str_cbb_1.extend(fuse_str_cbb)
		self.fuse_str_cbb_2.extend(fuse_str_cbb)
		self.fuse_str_cbb_3.extend(fuse_str_cbb)
		self.fuse_str_imh_0.extend(fuse_str_imh)
		self.fuse_str_imh_1.extend(fuse_str_imh)
	
	def _build_mask_strings(self) -> tuple:
		"""Build core and LLC mask disable strings for bootscript"""
		_ia = []
		_llc = []
		
		if self.coremask is None:
			boot_disable_ia = ''
		else:
			for key, value in self.coremask.items():
				_ia.append(f'"{key}":{hex(value)}')
			disable_ia = ','.join(_ia)
			boot_disable_ia = f' ia_core_disable={{{disable_ia}}},'
		
		if self.slicemask is None:
			boot_disable_llc = ''
		else:
			for key, value in self.slicemask.items():
				_llc.append(f'"{key}":{hex(value)}')
			disable_llc = ','.join(_llc)
			boot_disable_llc = f' llc_slice_disable={{{disable_llc}}},'
		
		return boot_disable_ia, boot_disable_llc
	
	def _build_bootscript_fuse_string(self) -> str:
		"""Build the fuse string for bootscript format"""
		cbbs_number = len(self.cbbs)
		imhs_number = len(self.imhs)
		
		fuse_string = ''
		
		if cbbs_number >= 1:
			fuse_string += f"'cbb_base0': {self.fuse_str_cbb_0},"
		if cbbs_number >= 2:
			fuse_string += f"'cbb_base1': {self.fuse_str_cbb_1},"
		if cbbs_number >= 3:
			fuse_string += f"'cbb_base2': {self.fuse_str_cbb_2},"
		if cbbs_number >= 4:
			fuse_string += f"'cbb_base3': {self.fuse_str_cbb_3},"
		
		if imhs_number >= 1:
			fuse_string += f"'imh0': {self.fuse_str_imh_0},"
		if imhs_number >= 2:
			fuse_string += f"'imh1': {self.fuse_str_imh_1},"
		
		if fuse_string.endswith(','):
			fuse_string = f' fuse_str={{{fuse_string[:-1]}}},'
		
		return fuse_string
	
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
	
	def _assign_values_to_regs(self, list_regs: List[str], new_value: int) -> List[str]:
		"""
		Assign a value to a list of register strings
		
		Args:
			list_regs: List of register names
			new_value: Value to assign
		
		Returns:
			List of register assignment strings
		"""
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
		from DMRCoreManipulation import (
			_wait_for_post,
			AFTER_MRC_POST,
			MRC_POSTCODE_WT,
			MRC_POSTCODE_CHECK_COUNT,
			BOOT_STOP_POSTCODE,
			BOOT_POSTCODE_WT,
			BOOT_POSTCODE_CHECK_COUNT,
			EFI_POST,
			EFI_POSTCODE_WT,
			EFI_POSTCODE_CHECK_COUNT,
			LINUX_POST,
			check_user_cancel,
			svStatus,
			dpm
		)
		
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
					print(Back.RED + f"Performing IPC Reconnect.. Trying to fix RSP 11 issue" + Back.RESET)
					dpm.powercycle()
					time.sleep(120)
					
					if check_user_cancel(self.execution_state):
						return 'Cancel'
					
					svStatus(checkipc=True, checksvcores=False, refresh=False, reconnect=False)
				
				if attempt <= n - 1:
					dpm.powercycle()
					time.sleep(delay)
			
			attempt += 1
		
		print(f"Failed to execute boot string after {n} attempts.")
		return False
	
	def _check_boot_completion(self, bootcont: str):
		"""Check boot completion and wait for appropriate postcode"""
		from DMRCoreManipulation import (
			_wait_for_post,
			AFTER_MRC_POST,
			MRC_POSTCODE_WT,
			MRC_POSTCODE_CHECK_COUNT,
			BOOT_STOP_POSTCODE,
			BOOT_POSTCODE_WT,
			BOOT_POSTCODE_CHECK_COUNT,
			EFI_POST,
			EFI_POSTCODE_WT,
			EFI_POSTCODE_CHECK_COUNT,
			LINUX_POST
		)
		
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
		from DMRCoreManipulation import fuse_cmd_override_check, dpm
		
		print(Fore.LIGHTCYAN_EX + "*" * 90)
		print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuse application after boot")
		
		dpm.fuseRAM(refresh=True)
		skip_init = True
		
		if use_fastboot:
			if self.fuse_str:
				fuse_cmd_override_check(self.fuse_str, showresults=False, skip_init=skip_init, bsFuses=None)
		else:
			if self.fuse_str_cbb_0:
				print(f"{'>' * 3} Checking fuses for CBB0 ---")
				fuse_cmd_override_check(self.fuse_str_cbb_0, showresults=False, skip_init=skip_init, bsFuses='cbb0')
			
			if self.fuse_str_cbb_1:
				print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuses for CBB1 ---")
				fuse_cmd_override_check(self.fuse_str_cbb_1, showresults=False, skip_init=skip_init, bsFuses='cbb1')
			
			if self.fuse_str_cbb_2:
				print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuses for CBB2 ---")
				fuse_cmd_override_check(self.fuse_str_cbb_2, showresults=False, skip_init=skip_init, bsFuses='cbb2')
			
			if self.fuse_str_cbb_3:
				print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuses for CBB3 ---")
				fuse_cmd_override_check(self.fuse_str_cbb_3, showresults=False, skip_init=skip_init, bsFuses='cbb3')
			
			if self.fuse_str_imh_0:
				print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuses for imh0 ---")
				fuse_cmd_override_check(self.fuse_str_imh_0, showresults=False, skip_init=skip_init, bsFuses='imh0')
			
			if self.fuse_str_imh_1:
				print(Fore.LIGHTCYAN_EX + f"{'>' * 3} Checking fuses for imh1 ---")
				fuse_cmd_override_check(self.fuse_str_imh_1, showresults=False, skip_init=skip_init, bsFuses='imh1')
