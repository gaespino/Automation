"""
Frequency Manager Module
Handles all frequency-related operations for System 2 Tester framework.

This module provides a centralized way to manage frequency configurations across different products,
including ATE frequency settings, ratio calculations, and frequency validation.

REV 0.1 -- Initial implementation
"""

from typing import Dict, Optional, Tuple, Callable, Any
from tabulate import tabulate


class FrequencyManager:
	"""
	Manages frequency configurations for S2T framework.
	
	Responsibilities:
	- Frequency initialization and validation
	- ATE frequency configuration
	- Frequency ratio calculations
	- Flow ID management for multiple frequencies
	"""
	
	def __init__(self, product_strategy, stc_module, menus: Dict, features: Dict):
		"""
		Initialize FrequencyManager.
		
		Args:
			product_strategy: Product-specific strategy implementation
			stc_module: STC module with frequency/ratio data
			menus: Menu strings for user prompts
			features: Feature flags dict to check what's enabled
		"""
		self.strategy = product_strategy
		self.stc = stc_module
		self.menus = menus
		self.features = features
		
		# Frequency configuration state
		self.core_freq: Optional[int] = None
		self.mesh_freq: Optional[int] = None
		self.io_freq: Optional[int] = None
		self.use_ate_freq: bool = True
		self.flowid: int = 1
		
		# ATE frequency options
		self.ATE_CORE_FREQ = [f'F{k}' for k in stc_module.CORE_FREQ.keys()]
		self.ATE_MESH_FREQ = [f'F{k}' for k in stc_module.CFC_FREQ.keys()]
	
	def display_ate_frequencies(self, mode: str = 'mesh', core_string: str = 'Core'):
		"""
		Display available ATE frequencies for the product.
		
		Args:
			mode: Operating mode ('mesh' or 'slice')
			core_string: Display string for core type
		"""
		if mode == 'slice':
			print(f"\n{'*' * 80}")
			print(f"> {self.strategy.get_product_name()} {core_string} frequencies are:")
			
			table = [[f'{core_string} Frequency', 'IA Value', 'CFC Value']]
			for k, v in self.stc.CORE_FREQ.items():
				cfc_val = self.stc.CORE_CFC_FREQ.get(k, 'N/A')
				table.append([f'F{k}', v, cfc_val])
			
			print(tabulate(table, headers="firstrow", tablefmt="grid"))
			print(f'--> Multiple freqs are FLOWID 1-4')
		
		elif mode == 'mesh':
			print(f"\n{'*' * 80}")
			print(f"> {self.strategy.get_product_name()} CFC frequencies are:")
			
			table = [['UnCore Frequency', 'CFC Value', 'IA Value']]
			for k, v in self.stc.CFC_FREQ.items():
				ia_val = self.stc.CFC_CORE_FREQ.get(k, 'N/A')
				table.append([f'F{k}', v, ia_val])
			
			print(tabulate(table, headers="firstrow", tablefmt="grid"))
			print(f'--> Multiple freqs are FLOWID 1-4')
	
	def configure_ate_frequency(self, 
								mode: str = 'mesh',
								core_string: str = 'Core',
								input_func: Callable = None) -> bool:
		"""
		Configure frequencies using ATE method.
		
		Args:
			mode: Operating mode ('mesh' or 'slice')
			core_string: Display string for core type
			input_func: Function to get user input
			
		Returns:
			True if ATE frequency was configured, False otherwise
		"""
		if not self.use_ate_freq or not self.features.get('use_ate_freq', {}).get('enabled', True):
			return False
		
		if input_func is None:
			return False
		
		# Prompt user if they want to use ATE frequency
		print(f"\n{'*' * 80}")
		if mode == 'slice':
			print(f"> Want to set {core_string} Frequency via ATE frequency method?: i.e. {self.ATE_CORE_FREQ}?")
		else:
			print(f"> Want to set UnCore Frequency via ATE frequency method?: i.e. {self.ATE_MESH_FREQ}?")
		
		yorn = ""
		while "N" not in yorn and "Y" not in yorn:
			yorn = input_func('--> Y / N (enter for [Y]): ').upper()
			if yorn == "":
				yorn = "Y"
		
		if yorn != "Y":
			self.use_ate_freq = False
			return False
		
		# Display frequency tables
		self.display_ate_frequencies(mode=mode, core_string=core_string)
		
		# Get frequency selection
		freq_range = self._get_frequency_range(mode)
		ate_freq = self._prompt_ate_frequency(freq_range, mode, core_string, input_func)
		
		if ate_freq is None:
			return False
		
		# Handle multi-frequency configurations (F5, F6, F7...)
		if ate_freq > 4:
			self.flowid = self._prompt_flowid(input_func)
		
		# Get ratios based on mode
		if mode == 'slice':
			self.core_freq, self.mesh_freq, self.io_freq = self.stc.get_ratios_core(ate_freq, self.flowid)
		else:
			self.mesh_freq, self.io_freq, self.core_freq = self.stc.get_ratios_mesh(ate_freq, self.flowid)
		
		print(f"\n{'*' * 80}")
		print(f"> FLOWID {self.flowid} ate_freq F{ate_freq}")
		print(f"> Setting system with ATE configuration:")
		print(f"  - {core_string.upper()}: {self.core_freq}")
		print(f"  - CFCCOMP: {self.mesh_freq}")
		print(f"  - CFCIO: {self.io_freq}")
		
		return True
	
	def _get_frequency_range(self, mode: str) -> int:
		"""Get the valid frequency range for the given mode."""
		if mode == 'slice':
			return len(self.stc.CORE_FREQ.keys())
		else:
			return len(self.stc.CFC_FREQ.keys())
	
	def _prompt_ate_frequency(self, 
							  freq_range: int, 
							  mode: str,
							  core_string: str,
							  input_func: Callable) -> Optional[int]:
		"""Prompt user to select ATE frequency."""
		freq_type = core_string if mode == 'slice' else 'UnCore'
		freq_list = self.ATE_CORE_FREQ if mode == 'slice' else self.ATE_MESH_FREQ
		
		print(f"\n> Enter {freq_type} Frequency: {freq_list}:")
		
		ate_freq = 0
		while ate_freq not in range(1, freq_range + 1):
			try:
				ate_freq = int(input_func(f"--> Enter 1-{freq_range}: "))
			except (ValueError, TypeError):
				pass
		
		return ate_freq
	
	def _prompt_flowid(self, input_func: Callable) -> int:
		"""Prompt user to select flow ID for multi-frequency configurations."""
		print(f"\n> Multiple frequencies available, select FLOWID:")
		print("\t> 1. Highest frequency")
		print("\t> 2. Second highest")
		print("\t> 3. Third highest")
		print("\t> 4. Lowest frequency")
		
		flowid = 0
		while flowid not in range(1, 5):
			try:
				flowid = int(input_func("--> Enter 1-4 (enter for [1]): ") or "1")
			except (ValueError, TypeError):
				flowid = 1
		
		return flowid
	
	def configure_manual_frequency(self, input_func: Callable = None) -> bool:
		"""
		Configure frequencies manually (not using ATE).
		
		Args:
			input_func: Function to get user input
			
		Returns:
			True if frequencies were configured
		"""
		configured = False
		
		# Core frequency
		if self.core_freq is None and self.features.get('core_freq', {}).get('enabled', True):
			if input_func:
				self.core_freq = self._prompt_int_frequency(
					self.menus.get('CoreFreq', 'Set Core Frequency?'),
					"--> Enter Core Frequency: ",
					input_func
				)
				configured = True
		
		# Mesh frequency
		if self.mesh_freq is None and self.features.get('mesh_freq', {}).get('enabled', True):
			if input_func:
				self.mesh_freq = self._prompt_int_frequency(
					self.menus.get('MeshFreq', 'Set Mesh Frequency?'),
					"--> Enter CFC/HDC Mesh Frequency: ",
					input_func
				)
				configured = True
		
		# IO frequency
		if self.io_freq is None and self.features.get('io_freq', {}).get('enabled', True):
			if input_func:
				self.io_freq = self._prompt_int_frequency(
					self.menus.get('IOFreq', 'Set IO Frequency?'),
					"--> Enter IO Mesh Frequency: ",
					input_func
				)
				configured = True
		
		return configured
	
	def _prompt_int_frequency(self, menu_str: str, prompt: str, input_func: Callable) -> Optional[int]:
		"""Helper to prompt for integer frequency value."""
		print(f"\n{menu_str}")
		
		# Prompt for yes/no first
		yorn = ""
		while "N" not in yorn and "Y" not in yorn:
			yorn = input_func('--> Y / N (enter for [Y]): ').upper()
			if yorn == "":
				yorn = "Y"
		
		if yorn != "Y":
			return None
		
		# Get frequency value
		try:
			value = input_func(prompt)
			return int(value) if value else None
		except (ValueError, TypeError):
			return None
	
	def validate_frequency(self, freq: Optional[int], freq_type: str, max_val: int = None) -> bool:
		"""
		Validate a frequency value.
		
		Args:
			freq: Frequency value to validate
			freq_type: Type of frequency ('core', 'mesh', 'io')
			max_val: Maximum allowed value
			
		Returns:
			True if valid, False otherwise
		"""
		if freq is None:
			return True  # None is valid (means not set)
		
		if not isinstance(freq, (int, list)):
			return False
		
		if isinstance(freq, list):
			# Handle multiple frequencies
			return all(isinstance(f, int) and f > 0 for f in freq)
		
		if freq <= 0:
			return False
		
		if max_val and freq > max_val:
			return False
		
		return True
	
	def get_frequency_dict(self) -> Dict[str, Any]:
		"""
		Get current frequency configuration as dictionary.
		
		Returns:
			Dictionary with all frequency settings
		"""
		return {
			'core_freq': self.core_freq,
			'mesh_freq': self.mesh_freq,
			'io_freq': self.io_freq,
			'use_ate_freq': self.use_ate_freq,
			'flowid': self.flowid
		}
	
	def set_from_dict(self, freq_dict: Dict[str, Any]):
		"""
		Set frequency configuration from dictionary.
		
		Args:
			freq_dict: Dictionary with frequency settings
		"""
		self.core_freq = freq_dict.get('core_freq')
		self.mesh_freq = freq_dict.get('mesh_freq')
		self.io_freq = freq_dict.get('io_freq')
		self.use_ate_freq = freq_dict.get('use_ate_freq', True)
		self.flowid = freq_dict.get('flowid', 1)
	
	def get_ratios_for_ate(self, ate_freq: int, flowid: int = 1, mode: str = 'mesh') -> Tuple[int, int, int]:
		"""
		Get frequency ratios for a given ATE frequency and flow ID.
		
		Args:
			ate_freq: ATE frequency index (1-N)
			flowid: Flow ID for multi-frequency configs (1-4)
			mode: Operating mode ('mesh' or 'slice')
			
		Returns:
			Tuple of (primary_freq, secondary_freq, tertiary_freq)
			For slice mode: (core_freq, mesh_freq, io_freq)
			For mesh mode: (mesh_freq, io_freq, core_freq)
		"""
		if mode == 'slice':
			return self.stc.get_ratios_core(ate_freq, flowid)
		else:
			return self.stc.get_ratios_mesh(ate_freq, flowid)
	
	def set_frequencies(self, core: Optional[int] = None, 
						mesh: Optional[int] = None, 
						io: Optional[int] = None):
		"""
		Directly set frequency values.
		
		Args:
			core: Core frequency
			mesh: Mesh/CFC frequency
			io: IO frequency
		"""
		if core is not None:
			self.core_freq = core
		if mesh is not None:
			self.mesh_freq = mesh
		if io is not None:
			self.io_freq = io
