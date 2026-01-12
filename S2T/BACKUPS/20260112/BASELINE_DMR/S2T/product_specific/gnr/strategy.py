"""
GNR Product Strategy Implementation
Concrete strategy for GNR (Granite Rapids) product.

REV 0.1 -- Initial implementation
"""

import sys
import os
from typing import List, Dict, Any

# Add parent managers directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'managers'))
from product_strategy import ProductStrategy
from tabulate import tabulate


class GNRStrategy(ProductStrategy):
	"""
	Product strategy implementation for GNR.
	
	GNR uses:
	- 'computes' for voltage domains
	- 'bigcore' architecture
	- Standard compute-based structure
	"""
	
	def __init__(self, config):
		super().__init__(config)
		self.product_config = config.CORETYPES[config.PRODUCT_CONFIG]
	
	# ========================================================================
	# Product Identification
	# ========================================================================
	
	def get_product_name(self) -> str:
		return 'GNR'
	
	def get_core_type(self) -> str:
		return self.product_config['core']
	
	def get_core_string(self) -> str:
		return self.config.CORESTRING
	
	# ========================================================================
	# Domain Structure
	# ========================================================================
	
	def get_voltage_domains(self) -> List[str]:
		"""GNR uses compute0, compute1, compute2 structure."""
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
		return self.config.classLogical2Physical.get(logical_id, logical_id)
	
	def physical_to_logical(self, physical_id: int) -> int:
		return self.config.physical2ClassLogical.get(physical_id, physical_id)
	
	def physical_to_colrow(self, physical_id: int) -> List[int]:
		return self.config.phys2colrow.get(physical_id, [0, 0])
	
	# ========================================================================
	# Product-Specific Features
	# ========================================================================
	
	def has_hdc_at_core(self) -> bool:
		"""GNR has HDC at uncore level."""
		return False

	def has_mlc_at_core(self) -> bool:
		"""GNR has HDC at uncore level."""
		return False
		
	def supports_600w_config(self) -> bool:
		"""GNR supports 600W configuration."""
		return True
	
	def supports_hyperthreading(self) -> bool:
		"""GNR supports HT disable."""
		return True
	
	def supports_2cpm(self) -> bool:
		"""GNR supports 2CPM disable."""
		return False

	def supports_1cpm(self) -> bool:
		"""GNR supports 1CPM disable."""
		return False
		
	def get_bootscript_config(self) -> Dict[str, Any]:
		"""Get GNR bootscript configuration."""
		product_key = self.config.PRODUCT_CONFIG
		if product_key in self.config.BOOTSCRIPT_DATA:
			return self.config.BOOTSCRIPT_DATA[product_key]
		# Default for GNR
		return {
			'segment': 'GNRXDCC' if 'AP' in product_key else 'GNRHDCC',
			'config': ['compute0', 'compute1', 'compute2'],
			'compute_config': 'x3'
		}
	
	# ========================================================================
	# Mask and Configuration Management
	# ========================================================================
	
	def get_valid_ate_masks(self) -> List[str]:
		"""Get valid ATE masks for GNR."""
		product_key = self.config.PRODUCT_CONFIG
		if product_key in self.config.VALIDCLASS:
			return self.config.VALIDCLASS[product_key]
		return []
	
	def get_valid_customs(self) -> List[str]:
		"""Get valid custom options for GNR."""
		return self.config.CUSTOMS
	
	def init_voltage_config(self) -> Dict[str, List]:
		"""Initialize voltage config with compute structure."""
		domains = self.get_voltage_domains()
		return {domain: [] for domain in domains}
	
	def get_voltage_ips(self) -> Dict[str, bool]:
		"""
		Get which voltage IPs are used by GNR.
		GNR uses: core, CFC/HDC per compute, IO CFC, DDRD, DDRA
		GNR does NOT use: core_mlc_volt (DMR-specific)
		"""
		return {
			'core_volt': True,
			'mesh_cfc_volt': True,   # Per compute
			'mesh_hdc_volt': True,   # Per compute (bigcore)
			'core_mlc_volt': False,  # Not used in GNR
			'io_cfc_volt': True,
			'ddrd_volt': True,
			'ddra_volt': True
		}
	
	# ========================================================================
	# Validation Methods
	# ========================================================================
	
	def validate_core_id(self, core_id: int, id_type: str = 'logical') -> bool:
		"""Validate GNR core ID."""
		if id_type == 'logical':
			return 0 <= core_id < self.config.MAXLOGICAL
		elif id_type == 'physical':
			return core_id in self.config.physical2ClassLogical
		return False
	
	def validate_domain(self, domain: str) -> bool:
		"""Validate compute domain name."""
		return domain in self.get_voltage_domains()
	
	# ========================================================================
	# Display and Formatting
	# ========================================================================
	
	def format_core_table(self, core_dict: Dict) -> str:
		"""Format core dictionary for GNR display."""
		table_data = []
		for compute_key, cores in core_dict.items():
			if isinstance(cores, dict):
				for core_type, core_list in cores.items():
					if isinstance(core_list, list):
						core_str = ', '.join(map(str, core_list))
						table_data.append([compute_key, core_type, core_str])
		
		if table_data:
			return tabulate(table_data, 
						   headers=['Compute', 'Type', 'Physical Cores'],
						   tablefmt='grid')
		return "No cores available"
