"""
Voltage Manager Module
Handles all voltage-related operations for System 2 Tester framework.

This module provides a centralized way to manage voltage configurations across different products,
including fixed voltages, voltage bumps, PPVC fuses, and domain-specific settings.

REV 0.1 -- Initial implementation
"""

from typing import Dict, Optional, List, Any, Callable
from tabulate import tabulate


class VoltageManager:
	"""
	Manages voltage configurations for S2T framework.
	
	Responsibilities:
	- Voltage initialization and validation
	- Fixed voltage configuration
	- Voltage bump (vbump) configuration and validation
	- PPVC fuses configuration
	- Uncore voltage management
	- ATE voltage configuration
	"""
	
	def __init__(self, product_strategy, dpm_module, menus: Dict, features: Dict):
		"""
		Initialize VoltageManager.
		
		Args:
			product_strategy: Product-specific strategy implementation
			dpm_module: DPM module for voltage operations
			menus: Menu strings for user prompts
			features: Feature flags dict to check what's enabled
		"""
		self.strategy = product_strategy
		self.dpm = dpm_module
		self.menus = menus
		self.features = features
		
		# Voltage configuration state
		self.core_volt: Optional[float] = None
		self.mesh_cfc_volt: Optional[Dict[str, float]] = None
		self.mesh_hdc_volt: Optional[Dict[str, float]] = None
		self.io_cfc_volt: Optional[float] = None
		self.ddrd_volt: Optional[float] = None
		self.ddra_volt: Optional[float] = None
		
		# Configuration flags
		self.use_ate_volt: bool = False
		self.custom_volt: bool = False
		self.vbumps_volt: bool = False
		self.ppvc_fuses: bool = False
		
		# Voltage configuration list (for bootscript)
		self.volt_config: List = []
		
		# Safe voltage tables
		self.safevolts_PKG: List = []
		self.safevolts_CDIE: List = []
		self.voltstable: str = ""
		
	def init_voltage_tables(self, mode: str = 'mesh', safe_volts_pkg: Dict = None, safe_volts_cdie: Dict = None):
		"""
		Initialize voltage reference tables.
		
		Args:
			mode: Operating mode ('mesh' or 'slice')
			safe_volts_pkg: Package-level safe voltages
			safe_volts_cdie: Compute DIE safe voltages
		"""
		self.safevolts_PKG = [['Domain', 'Value']]
		self.safevolts_CDIE = [['Domain', 'Value']]
		
		# Initialize domain voltage tracking using product strategy
		domains = self.strategy.get_voltage_domains()
		self.mesh_cfc_volt = {d: None for d in domains}
		self.mesh_hdc_volt = {d: None for d in domains}
		
		# Populate safe voltage tables
		if safe_volts_pkg:
			for k, v in safe_volts_pkg.items():
				self.safevolts_PKG.append([k, v])
		
		if safe_volts_cdie:
			for k, v in safe_volts_cdie.items():
				self.safevolts_CDIE.append([k, v])
		
		# Set table based on mode
		safevalues = self.safevolts_CDIE if mode == 'slice' else self.safevolts_PKG
		self.voltstable = tabulate(safevalues, headers="firstrow", tablefmt="grid")
		
		# Initialize volt_config using strategy
		self.volt_config = self.strategy.init_voltage_config()
	
	def check_vbumps(self, value: Optional[float], prompt_func: Callable = None) -> Optional[float]:
		"""
		Validate voltage bump values are within acceptable range.
		
		Args:
			value: Voltage bump value to validate
			prompt_func: Function to prompt for new value if invalid
			
		Returns:
			Validated voltage bump value or None
		"""
		if value is None:
			return None
			
		while value > 0.2 or value < -0.2:
			if prompt_func:
				try:
					value = float(prompt_func(self.menus['vbumpfix']))
				except (ValueError, KeyError):
					pass
			else:
				# If no prompt function, return None for invalid values
				return None
		
		return value
	
	def configure_voltage(self, 
						  use_ate_volt: bool,
						  external: bool = False,
						  volt_select: Optional[int] = None,
						  fastboot: bool = False,
						  qvbumps_core: Optional[float] = None,
						  qvbumps_mesh: Optional[float] = None,
						  core_string: str = 'Core',
						  input_func: Callable = None) -> bool:
		"""
		Main voltage configuration workflow.
		
		Args:
			use_ate_volt: Whether to use ATE voltage configuration
			external: Whether this is called from external tool
			volt_select: Pre-selected voltage option (1-4)
			fastboot: Whether fastboot is enabled
			qvbumps_core: Quick vbumps for core (external mode)
			qvbumps_mesh: Quick vbumps for mesh (external mode)
			core_string: Display string for core type
			input_func: Function to get user input
			
		Returns:
			True if voltage was configured, False otherwise
		"""
		self.use_ate_volt = use_ate_volt
		
		if use_ate_volt:
			return self._configure_ate_voltage(fastboot)
		
		if not self.features.get('use_ate_volt', {}).get('enabled', True):
			return False
		
		# Get voltage configuration option from user if not provided
		if not external and volt_select is None:
			volt_select = self._prompt_voltage_option(input_func)
		
		# Option 1: No voltage configuration
		if volt_select == 1:
			return False
		
		# Option 2: Fixed Voltage
		elif volt_select == 2:
			return self._configure_fixed_voltage(external, qvbumps_core, core_string, fastboot, input_func)
		
		# Option 3: Voltage Bumps
		elif volt_select == 3:
			return self._configure_vbumps(external, qvbumps_core, qvbumps_mesh, core_string, fastboot, input_func)
		
		# Option 4: PPVC Fuses
		elif volt_select == 4:
			return self._configure_ppvc_fuses(fastboot)
		
		return False
	
	def _prompt_voltage_option(self, input_func: Callable) -> int:
		"""Prompt user to select voltage configuration option."""
		print(f"\n{'*' * 80}")
		print(f"> Set System Voltage?")
		print("\t> 1. No")
		print("\t> 2. Fixed Voltage")
		print("\t> 3. Voltage Bumps")
		print("\t> 4. PPVC Conditions")
		
		volt_select = None
		while volt_select not in range(1, 5):
			try:
				user_input = input_func("\n--> Enter 1-4: (enter for [1]) ")
				if user_input == "":
					volt_select = 1
				else:
					volt_select = int(user_input)
			except (ValueError, TypeError):
				pass
		
		return volt_select
	
	def _configure_ate_voltage(self, fastboot: bool) -> bool:
		"""Configure voltage using ATE settings."""
		voltdict = {
			'core': self.core_volt,
			'cfc_die': self.mesh_cfc_volt,
			'hdc_die': self.mesh_hdc_volt,
			'cfc_io': self.io_cfc_volt,
			'ddrd': self.ddrd_volt,
			'ddra': self.ddra_volt
		}
		self.volt_config = self.dpm.tester_voltage(
			bsformat=(not fastboot),
			volt_dict=voltdict,
			volt_fuses=[],
			fixed=True,
			vbump=False
		)
		return True
	
	def _configure_fixed_voltage(self, 
								 external: bool,
								 qvbumps_core: Optional[float],
								 core_string: str,
								 fastboot: bool,
								 input_func: Callable) -> bool:
		"""Configure fixed voltage values."""
		if not external:
			print(f"\n> Fixed Voltage Configuration Selected\n")
			print(f"\n> Tester Safe values for reference:\n")
			print(self.voltstable)
			
			# Prompt for core voltage
			self.core_volt = self._prompt_float_voltage(
				f"--> Enter {core_string} Voltage: ",
				self.menus.get('CoreVolt', 'Set Core Voltage?'),
				input_func
			)
		else:
			self.core_volt = qvbumps_core
		
		# Configure uncore voltages (CFC/HDC)
		self.configure_uncore_voltages(fixed=True, external=external, 
									   qvbumps_mesh=None, input_func=input_func)
		
		if not external:
			# IO and DDR voltages
			self.io_cfc_volt = self._prompt_float_voltage(
				"--> Enter CFC IO DIE Voltage: ",
				self.menus.get('CFCIOVolt', 'Set IO CFC Voltage?'),
				input_func
			)
			self.ddrd_volt = self._prompt_float_voltage(
				"--> Enter DDRD Voltage: ",
				self.menus.get('DDRDVolt', 'Set DDRD Voltage?'),
				input_func
			)
		
		# Build voltage configuration
		voltdict = {
			'core': self.core_volt,
			'cfc_die': self.mesh_cfc_volt,
			'hdc_die': self.mesh_hdc_volt,
			'cfc_io': self.io_cfc_volt,
			'ddrd': self.ddrd_volt,
			'ddra': self.ddra_volt
		}
		
		self.volt_config = self.dpm.tester_voltage(
			bsformat=(not fastboot),
			volt_dict=voltdict,
			volt_fuses=[],
			fixed=True,
			vbump=False
		)
		self.custom_volt = True
		return True
	
	def _configure_vbumps(self,
						  external: bool,
						  qvbumps_core: Optional[float],
						  qvbumps_mesh: Optional[float],
						  core_string: str,
						  fastboot: bool,
						  input_func: Callable) -> bool:
		"""Configure voltage bumps."""
		if not external:
			print(f"\n> Vbumps Configuration selected, use values in volts range of -0.2V to 0.2V:")
			
			# Prompt for core vbump
			core_vbump = self._prompt_float_voltage(
				f"--> Enter {core_string} vBump: ",
				self.menus.get('CoreBump', 'Set Core vBump?'),
				input_func
			)
			self.core_volt = self.check_vbumps(core_vbump, input_func)
		else:
			self.core_volt = qvbumps_core
		
		# Configure uncore voltage bumps
		self.configure_uncore_voltages(vbumps=True, external=external,
									   qvbumps_mesh=qvbumps_mesh, input_func=input_func)
		
		if not external:
			# IO and DDR vbumps
			io_vbump = self._prompt_float_voltage(
				"--> Enter CFC IO DIE vBump: ",
				self.menus.get('CFCIOBump', 'Set IO CFC vBump?'),
				input_func
			)
			self.io_cfc_volt = self.check_vbumps(io_vbump, input_func)
			
			ddrd_vbump = self._prompt_float_voltage(
				"--> Enter DDRD vBump: ",
				self.menus.get('DDRDBump', 'Set DDRD vBump?'),
				input_func
			)
			self.ddrd_volt = self.check_vbumps(ddrd_vbump, input_func)
		
		# Build voltage configuration
		voltdict = {
			'core': self.core_volt,
			'cfc_die': self.mesh_cfc_volt,
			'hdc_die': self.mesh_hdc_volt,
			'cfc_io': self.io_cfc_volt,
			'ddrd': self.ddrd_volt,
			'ddra': self.ddra_volt
		}
		
		self.volt_config = self.dpm.tester_voltage(
			bsformat=(not fastboot),
			volt_dict=voltdict,
			volt_fuses=[],
			fixed=False,
			vbump=True
		)
		self.vbumps_volt = True
		return True
	
	def _configure_ppvc_fuses(self, fastboot: bool) -> bool:
		"""Configure PPVC fuses."""
		self.volt_config = self.dpm.ppvc(bsformat=(not fastboot), ppvc_fuses=[])
		self.ppvc_fuses = True
		return True
	
	def configure_uncore_voltages(self,
								   vbumps: bool = False,
								   fixed: bool = False,
								   external: bool = False,
								   qvbumps_mesh: Optional[float] = None,
								   input_func: Callable = None):
		"""
		Configure uncore (CFC/HDC) voltages.
		
		Args:
			vbumps: Configure as voltage bumps
			fixed: Configure as fixed voltages
			external: External tool mode
			qvbumps_mesh: Quick vbumps for mesh (external mode)
			input_func: Function to get user input
		"""
		domains = self.strategy.get_voltage_domains()
		core_type = self.strategy.get_core_type()
		
		# Determine configuration mode
		if external:
			uncore_mode = 3  # External mode
		else:
			uncore_mode = self._prompt_uncore_option(input_func)
		
		# Mode 1: Same for all domains
		if uncore_mode == 1:
			if fixed:
				cfc_value = self._prompt_float_voltage(
					"--> Enter CFC Voltage: ",
					self.menus.get('CFCVolt', 'Set CFC Voltage?'),
					input_func
				)
				hdc_value = self._prompt_float_voltage(
					"--> Enter HDC Voltage: ",
					self.menus.get('HDCVolt', 'Set HDC Voltage?'),
					input_func
				)
				for domain in domains:
					self.mesh_cfc_volt[domain] = cfc_value
					self.mesh_hdc_volt[domain] = hdc_value
			
			if vbumps:
				cfc_vbump = self._prompt_float_voltage(
					"--> Enter CFC vBump: ",
					self.menus.get('CFCBump', 'Set CFC vBump?'),
					input_func
				)
				hdc_vbump = self._prompt_float_voltage(
					"--> Enter HDC vBump: ",
					self.menus.get('HDCBump', 'Set HDC vBump?'),
					input_func
				)
				cfc_value = self.check_vbumps(cfc_vbump, input_func)
				hdc_value = self.check_vbumps(hdc_vbump, input_func)
				
				for domain in domains:
					self.mesh_cfc_volt[domain] = cfc_value
					self.mesh_hdc_volt[domain] = hdc_value
		
		# Mode 2: Per domain configuration
		elif uncore_mode == 2:
			for domain in domains:
				domain_display = self.strategy.format_domain_name(domain)
				
				if fixed:
					cfc_prompt = self.menus.get('CFCVolt', 'Set CFC Voltage?').replace(
						'Uncore CFC Voltage', f'{domain_display} Uncore CFC Voltage'
					)
					hdc_prompt = self.menus.get('HDCVolt', 'Set HDC Voltage?').replace(
						'Uncore HDC Voltage', f'{domain_display} Uncore HDC Voltage'
					)
					
					self.mesh_cfc_volt[domain] = self._prompt_float_voltage(
						f"--> Enter CFC {domain_display} Voltage: ",
						cfc_prompt,
						input_func
					)
					self.mesh_hdc_volt[domain] = self._prompt_float_voltage(
						f"--> Enter HDC {domain_display} Voltage: ",
						hdc_prompt,
						input_func
					)
				
				if vbumps:
					cfc_prompt = self.menus.get('CFCBump', 'Set CFC vBump?').replace(
						'Uncore CFC vBump', f'{domain_display} Uncore CFC vBump'
					)
					hdc_prompt = self.menus.get('HDCBump', 'Set HDC vBump?').replace(
						'Uncore HDC vBump', f'{domain_display} Uncore HDC vBump'
					)
					
					cfc_vbump = self._prompt_float_voltage(
						f"--> Enter CFC {domain_display} vBump: ",
						cfc_prompt,
						input_func
					)
					hdc_vbump = self._prompt_float_voltage(
						f"--> Enter HDC {domain_display} vBump: ",
						hdc_prompt,
						input_func
					)
					
					self.mesh_cfc_volt[domain] = self.check_vbumps(cfc_vbump, input_func)
					self.mesh_hdc_volt[domain] = self.check_vbumps(hdc_vbump, input_func)
		
		# Mode 3: External mode
		elif uncore_mode == 3:
			for domain in domains:
				self.mesh_cfc_volt[domain] = qvbumps_mesh
				# HDC voltage depends on core type
				if core_type == 'bigcore':
					self.mesh_hdc_volt[domain] = qvbumps_mesh
				else:
					# For atomcore, HDC is at core level
					self.mesh_hdc_volt[domain] = self.core_volt if hasattr(self, 'core_volt') else qvbumps_mesh
	
	def _prompt_uncore_option(self, input_func: Callable) -> int:
		"""Prompt user for uncore voltage configuration option."""
		print(f"\n> Uncore Voltage Options?")
		print("\t> 1. Same for all " + self.strategy.get_domain_display_name() + "s")
		print("\t> 2. Set per " + self.strategy.get_domain_display_name())
		
		uncore = None
		while uncore not in range(1, 3):
			try:
				user_input = input_func("\n--> Enter 1-2: (enter for [1]) ")
				if user_input == "":
					uncore = 1
				else:
					uncore = int(user_input)
			except (ValueError, TypeError):
				pass
		
		return uncore
	
	def _prompt_float_voltage(self, prompt: str, menu_str: str, input_func: Callable) -> Optional[float]:
		"""Helper to prompt for float voltage value."""
		if input_func is None:
			return None
		
		print(f"\n{menu_str}")
		try:
			value = input_func(prompt)
			return float(value) if value else None
		except (ValueError, TypeError):
			return None
	
	def get_voltage_dict(self) -> Dict[str, Any]:
		"""
		Get current voltage configuration as dictionary.
		
		Returns:
			Dictionary with all voltage settings
		"""
		return {
			'core_volt': self.core_volt,
			'mesh_cfc_volt': self.mesh_cfc_volt,
			'mesh_hdc_volt': self.mesh_hdc_volt,
			'io_cfc_volt': self.io_cfc_volt,
			'ddrd_volt': self.ddrd_volt,
			'ddra_volt': self.ddra_volt,
			'use_ate_volt': self.use_ate_volt,
			'custom_volt': self.custom_volt,
			'vbumps_volt': self.vbumps_volt,
			'ppvc_fuses': self.ppvc_fuses,
			'volt_config': self.volt_config
		}
	
	def set_from_dict(self, volt_dict: Dict[str, Any]):
		"""
		Set voltage configuration from dictionary.
		
		Args:
			volt_dict: Dictionary with voltage settings
		"""
		self.core_volt = volt_dict.get('core_volt')
		self.mesh_cfc_volt = volt_dict.get('mesh_cfc_volt')
		self.mesh_hdc_volt = volt_dict.get('mesh_hdc_volt')
		self.io_cfc_volt = volt_dict.get('io_cfc_volt')
		self.ddrd_volt = volt_dict.get('ddrd_volt')
		self.ddra_volt = volt_dict.get('ddra_volt')
		self.use_ate_volt = volt_dict.get('use_ate_volt', False)
		self.custom_volt = volt_dict.get('custom_volt', False)
		self.vbumps_volt = volt_dict.get('vbumps_volt', False)
		self.ppvc_fuses = volt_dict.get('ppvc_fuses', False)
		self.volt_config = volt_dict.get('volt_config', [])
