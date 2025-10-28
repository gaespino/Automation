"""
CWF Product Strategy Implementation
Concrete strategy for CWF (Clearwater Forest) product.

REV 0.1 -- Initial implementation
"""

import sys
import os
from typing import List, Dict, Any

# Add parent managers directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'managers'))
from product_strategy import ProductStrategy
from tabulate import tabulate


class CWFStrategy(ProductStrategy):
	"""
	Product strategy implementation for CWF.
	
	CWF uses:
	- 'computes' for voltage domains  
	- 'atomcore' architecture (HDC at core level)
	- Standard compute-based structure
	"""
	
	def __init__(self, config):
		super().__init__(config)
		self.product_config = config.CORETYPES[config.PRODUCT_CONFIG]
	
	# ========================================================================
	# Product Identification
	# ========================================================================
	
	def get_product_name(self) -> str:
		return 'CWF'
	
	def get_core_type(self) -> str:
		return self.product_config['core']
	
	def get_core_string(self) -> str:
		return self.config.CORESTRING
	
	# ========================================================================
	# Domain Structure
	# ========================================================================
	
	def get_voltage_domains(self) -> List[str]:
		"""CWF uses compute0, compute1, compute2 structure."""
		import namednodes
		sv = namednodes.sv
		return [c for c in sv.socket0.computes.name]
	
	def get_domain_display_name(self) -> str:
		return 'Compute'
	
	def format_domain_name(self, domain: str) -> str:
		return domain.upper()
	
	def get_total_domains(self) -> int:
		return len(self.get_voltage_domains())
	
	# ========================================================================
	# Core/Module Management
	# ========================================================================
	
	def get_max_cores(self) -> int:
		return self.product_config['maxcores']
	
	def get_max_logical_cores(self) -> int:
		return self.product_config['maxlogcores']
	
	def logical_to_physical(self, logical_id: int) -> int:
		# CWF may use AtomID mapping
		if self.config.CONFIG.get('LOG2ATOMID'):
			return self.config.CONFIG['LOG2ATOMID'].get(logical_id, logical_id)
		return self.config.classLogical2Physical.get(logical_id, logical_id)
	
	def physical_to_logical(self, physical_id: int) -> int:
		# CWF may use AtomID mapping
		if self.config.CONFIG.get('ATOMID2LOG'):
			return self.config.CONFIG['ATOMID2LOG'].get(physical_id, physical_id)
		return self.config.physical2ClassLogical.get(physical_id, physical_id)
	
	def physical_to_colrow(self, physical_id: int) -> List[int]:
		return self.config.phys2colrow.get(physical_id, [0, 0])
	
	# ========================================================================
	# Product-Specific Features
	# ========================================================================
	
	def has_hdc_at_core(self) -> bool:
		"""CWF is atomcore, so HDC is at core level (L2)."""
		return True
	
	def supports_600w_config(self) -> bool:
		"""CWF supports 600W configuration."""
		return False
	
	def supports_hyperthreading(self) -> bool:
		"""CWF supports HT disable."""
		return True
	
	def supports_2cpm(self) -> bool:
		"""CWF supports 2CPM disable."""
		return True
	
	def get_bootscript_config(self) -> Dict[str, Any]:
		"""Get CWF bootscript configuration."""
		product_key = self.config.PRODUCT_CONFIG
		if product_key in self.config.BOOTSCRIPT_DATA:
			return self.config.BOOTSCRIPT_DATA[product_key]
		# Default for CWF
		return {
			'segment': 'CWFXDCC' if 'AP' in product_key else 'CWFHDCC',
			'config': ['compute0', 'compute1', 'compute2'],
			'compute_config': 'x3'
		}
	
	# ========================================================================
	# Mask and Configuration Management
	# ========================================================================
	
	def get_valid_ate_masks(self) -> List[str]:
		"""Get valid ATE masks for CWF."""
		product_key = self.config.PRODUCT_CONFIG
		if product_key in self.config.VALIDCLASS:
			return self.config.VALIDCLASS[product_key]
		return []
	
	def get_valid_customs(self) -> List[str]:
		"""Get valid custom options for CWF."""
		return self.config.CUSTOMS
	
	def init_voltage_config(self) -> Dict[str, List]:
		"""Initialize voltage config with compute structure."""
		domains = self.get_voltage_domains()
		return {domain: [] for domain in domains}
	
	# ========================================================================
	# Validation Methods
	# ========================================================================
	
	def validate_core_id(self, core_id: int, id_type: str = 'logical') -> bool:
		"""Validate CWF module ID."""
		if id_type == 'logical':
			return 0 <= core_id < self.config.MAXLOGICAL
		elif id_type == 'physical':
			# Check both standard physical and AtomID mappings
			if core_id in self.config.physical2ClassLogical:
				return True
			if self.config.CONFIG.get('ATOMID2LOG'):
				return core_id in self.config.CONFIG['ATOMID2LOG']
		return False
	
	def validate_domain(self, domain: str) -> bool:
		"""Validate compute domain name."""
		return domain in self.get_voltage_domains()
	
	# ========================================================================
	# Display and Formatting
	# ========================================================================
	
	def format_core_table(self, core_dict: Dict) -> str:
		"""Format core dictionary for CWF display."""
		table_data = []
		for compute_key, modules in core_dict.items():
			if isinstance(modules, dict):
				for module_type, module_list in modules.items():
					if isinstance(module_list, list):
						module_str = ', '.join(map(str, module_list))
						table_data.append([compute_key, module_type, module_str])
		
		if table_data:
			return tabulate(table_data,
						   headers=['Compute', 'Type', 'Physical Modules'],
						   tablefmt='grid')
		return "No modules available"
