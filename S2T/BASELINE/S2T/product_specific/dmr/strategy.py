"""
DMR Product Strategy Implementation
Concrete strategy for DMR (Diamond Rapids) product.

REV 0.1 -- Initial implementation
"""

import sys
import os
from typing import List, Dict, Any, Optional

# Add parent managers directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'managers'))
from product_strategy import ProductStrategy
from tabulate import tabulate


class DMRStrategy(ProductStrategy):
	"""
	Product strategy implementation for DMR.
	
	DMR uses:
	- 'cbbs' (Compute Building Blocks) instead of 'computes'
	- 'MODULE' terminology instead of 'CORE'
	- Different structural organization
	"""
	
	def __init__(self, config):
		super().__init__(config)
		self.product_config = config.CORETYPES[config.PRODUCT_CONFIG]
	
	# ========================================================================
	# Product Identification
	# ========================================================================
	
	def get_product_name(self) -> str:
		return 'DMR'
	
	def get_core_type(self) -> str:
		return self.product_config['core']
	
	def get_core_string(self) -> str:
		return self.config.CORESTRING  # 'MODULE' for DMR
	
	# ========================================================================
	# Domain Structure (CBBs instead of Computes)
	# ========================================================================
	
	def get_voltage_domains(self) -> List[str]:
		"""
		DMR uses cbb0, cbb1, cbb2, cbb3 structure (AP) or cbb0, cbb1 (SP).
		"""
		max_cbbs = self.product_config.get('max_cbbs', 4)
		return [f'cbb{i}' for i in range(max_cbbs)]
	
	def get_domain_display_name(self) -> str:
		return 'CBB'
	
	def format_domain_name(self, domain: str) -> str:
		return domain.upper()
	
	def get_total_domains(self) -> int:
		return self.product_config.get('max_cbbs', 4)
	
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
		"""
		DMR does NOT have HDC at core level.
		DMR uses MLC at core level instead, which is handled separately via core_mlc_volt.
		
		Returns False because DMR doesn't have mesh_hdc_volt (no HDC voltage domain).
		"""
		return False  # DMR doesn't have HDC, it has MLC instead
	
	def supports_600w_config(self) -> bool:
		"""DMR does not support 600W configuration."""
		return False
	
	def supports_hyperthreading(self) -> bool:
		"""DMR supports HT disable."""
		return False
	
	def supports_2cpm(self) -> bool:
		"""DMR supports 2CPM disable."""
		return False

	def supports_1cpm(self) -> bool:
		"""DMR supports 1CPM enabled."""
		return False
		
	def get_bootscript_config(self) -> Dict[str, Any]:
		"""Get DMR bootscript configuration."""
		product_key = self.config.PRODUCT_CONFIG
		if product_key in self.config.BOOTSCRIPT_DATA:
			return self.config.BOOTSCRIPT_DATA[product_key]
		
		# Default based on AP/SP
		if 'AP' in product_key:
			return {
				'segment': 'CWFXDCC',
				'config': ['cbb0', 'cbb1', 'cbb2', 'cbb3'],
				'compute_config': 'x4'
			}
		else:  # SP
			return {
				'segment': 'CWFHDCC',
				'config': ['cbb0'],
				'compute_config': 'x1'
			}
	
	# ========================================================================
	# Mask and Configuration Management
	# ========================================================================
	
	def get_valid_ate_masks(self) -> List[str]:
		"""Get valid ATE masks for DMR."""
		product_key = self.config.PRODUCT_CONFIG
		if product_key in self.config.VALIDCLASS:
			return self.config.VALIDCLASS[product_key]
		return []
	
	def get_valid_customs(self) -> List[str]:
		"""Get valid custom options for DMR."""
		return self.config.CUSTOMS
	
	def init_voltage_config(self) -> Dict[str, List]:
		"""Initialize voltage config with CBB structure."""
		domains = self.get_voltage_domains()
		# Also include io domains if needed
		volt_config = {domain: [] for domain in domains}
		# DMR may have io0, io1 domains as well
		if self.product_config.get('max_imhs', 0) > 0:
			for i in range(self.product_config['max_imhs']):
				volt_config[f'io{i}'] = []
		return volt_config
	
	def get_voltage_ips(self) -> Dict[str, bool]:
		"""
		Get which voltage IPs are used by DMR.
		DMR uses: core, CFC per CBB, core MLC, IO CFC, DDRD, DDRA
		DMR does NOT use: mesh_hdc_volt (only CFC is used for uncore)
		"""
		return {
			'core_volt': True,
			'mesh_cfc_volt': True,   # Per CBB
			'mesh_hdc_volt': False,  # DMR does NOT use HDC voltage
			'core_mlc_volt': True,   # DMR-specific: MLC voltage
			'io_cfc_volt': True,
			'ddrd_volt': True,
			'ddra_volt': True
		}
	
	# ========================================================================
	# DMR-Specific Methods
	# ========================================================================
	
	def get_modules_per_cbb(self) -> Optional[int]:
		"""Get number of modules per CBB for DMR."""
		return self.product_config.get('mods_per_cbb', 32)
	
	def get_modules_per_compute(self) -> Optional[int]:
		"""Get number of modules per compute for DMR."""
		return self.product_config.get('mods_per_compute', 8)
	
	def get_active_modules_per_cbb(self) -> Optional[int]:
		"""Get number of active modules per CBB for DMR."""
		return self.product_config.get('active_per_cbb', 32)
	
	def get_max_cbbs(self) -> Optional[int]:
		"""Get maximum number of CBBs for DMR."""
		return self.product_config.get('max_cbbs', 4)
	
	def get_max_imhs(self) -> Optional[int]:
		"""Get maximum number of IMHS for DMR."""
		return self.product_config.get('max_imhs', 2)
	
	# ========================================================================
	# Validation Methods
	# ========================================================================
	
	def validate_core_id(self, core_id: int, id_type: str = 'logical') -> bool:
		"""Validate DMR module ID."""
		if id_type == 'logical':
			return 0 <= core_id < self.config.MAXLOGICAL
		elif id_type == 'physical':
			return core_id in self.config.physical2ClassLogical
		return False
	
	def validate_domain(self, domain: str) -> bool:
		"""Validate CBB or IO domain name."""
		valid_domains = self.get_voltage_domains()
		# Also check for io domains
		if self.product_config.get('max_imhs', 0) > 0:
			valid_domains.extend([f'io{i}' for i in range(self.product_config['max_imhs'])])
		return domain in valid_domains
	
	# ========================================================================
	# Display and Formatting
	# ========================================================================
	
	def format_core_table(self, core_dict: Dict) -> str:
		"""Format core dictionary for DMR display with CBB structure."""
		table_data = []
		for cbb_key, modules in core_dict.items():
			if isinstance(modules, dict):
				for module_type, module_list in modules.items():
					if isinstance(module_list, list):
						module_str = ', '.join(map(str, module_list))
						table_data.append([cbb_key, module_type, module_str])
		
		if table_data:
			return tabulate(table_data,
						   headers=['CBB', 'Type', 'Physical Modules'],
						   tablefmt='grid')
		return "No modules available"
	
	def get_cbb_info(self) -> Dict[str, Any]:
		"""
		Get detailed CBB configuration information.
		
		Returns:
			Dictionary with CBB-specific configuration
		"""
		return {
			'total_cbbs': self.get_max_cbbs(),
			'modules_per_cbb': self.get_modules_per_cbb(),
			'modules_per_compute': self.get_modules_per_compute(),
			'active_per_cbb': self.get_active_modules_per_cbb(),
			'max_imhs': self.get_max_imhs(),
			'total_modules': self.get_max_cores(),
			'config_type': self.product_config.get('config', 'Unknown')
		}
