"""
Product Strategy Module
Defines the abstract interface for product-specific implementations.

This module uses the Strategy pattern to handle differences between products
(GNR/CWF use 'computes', DMR uses 'cbbs', etc.) in a clean, extensible way.

REV 0.1 -- Initial implementation
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class ProductStrategy(ABC):
	"""
	Abstract base class defining the interface for product-specific strategies.
	
	Each product (GNR, CWF, DMR) implements this interface to provide
	product-specific behavior for:
	- Domain structure (computes vs CBBs)
	- Naming conventions
	- Voltage/frequency domains
	- Core/module identification
	- Product-specific validations
	"""
	
	def __init__(self, config):
		"""
		Initialize strategy with product configuration.
		
		Args:
			config: ProductConfiguration object from ConfigsLoader
		"""
		self.config = config
	
	# ========================================================================
	# Product Identification
	# ========================================================================
	
	@abstractmethod
	def get_product_name(self) -> str:
		"""Get the product name (e.g., 'GNR', 'CWF', 'DMR')."""
		pass
	
	@abstractmethod
	def get_core_type(self) -> str:
		"""Get the core type ('bigcore' or 'atomcore')."""
		pass
	
	@abstractmethod
	def get_core_string(self) -> str:
		"""Get the display string for cores (e.g., 'CORE', 'MODULE')."""
		pass
	
	# ========================================================================
	# Domain Structure (Computes vs CBBs)
	# ========================================================================
	
	@abstractmethod
	def get_voltage_domains(self) -> List[str]:
		"""
		Get list of voltage domains for this product.
		
		Returns:
			List of domain names (e.g., ['compute0', 'compute1', ...] or ['cbb0', 'cbb1', ...])
		"""
		pass
	
	@abstractmethod
	def get_domain_display_name(self) -> str:
		"""
		Get singular display name for domain type.
		
		Returns:
			'Compute' for GNR/CWF, 'CBB' for DMR
		"""
		pass
	
	@abstractmethod
	def format_domain_name(self, domain: str) -> str:
		"""
		Format a domain name for display (e.g., 'compute0' -> 'COMPUTE0').
		
		Args:
			domain: Raw domain name
			
		Returns:
			Formatted display name
		"""
		pass
	
	@abstractmethod
	def get_total_domains(self) -> int:
		"""Get total number of voltage domains."""
		pass
	
	# ========================================================================
	# Core/Module Management
	# ========================================================================
	
	@abstractmethod
	def get_max_cores(self) -> int:
		"""Get maximum number of cores/modules for this product."""
		pass
	
	@abstractmethod
	def get_max_logical_cores(self) -> int:
		"""Get maximum number of logical cores."""
		pass
	
	@abstractmethod
	def logical_to_physical(self, logical_id: int) -> int:
		"""
		Convert logical core ID to physical core ID.
		
		Args:
			logical_id: Logical core ID
			
		Returns:
			Physical core ID
		"""
		pass
	
	@abstractmethod
	def physical_to_logical(self, physical_id: int) -> int:
		"""
		Convert physical core ID to logical core ID.
		
		Args:
			physical_id: Physical core ID
			
		Returns:
			Logical core ID
		"""
		pass
	
	@abstractmethod
	def physical_to_colrow(self, physical_id: int) -> List[int]:
		"""
		Convert physical core ID to [column, row] coordinates.
		
		Args:
			physical_id: Physical core ID
			
		Returns:
			[column, row] list
		"""
		pass
	
	# ========================================================================
	# Product-Specific Features
	# ========================================================================
	
	@abstractmethod
	def has_hdc_at_core(self) -> bool:
		"""
		Check if HDC voltage is at core level (atomcore) or uncore level (bigcore).
		
		Returns:
			True if HDC is at core level, False if at uncore level
		"""
		pass
	
	@abstractmethod
	def supports_600w_config(self) -> bool:
		"""Check if product supports 600W configuration."""
		pass
	
	@abstractmethod
	def supports_hyperthreading(self) -> bool:
		"""Check if product supports hyperthreading disable."""
		pass
	
	@abstractmethod
	def supports_2cpm(self) -> bool:
		"""Check if product supports 2CPM disable."""
		pass
	
	@abstractmethod
	def get_bootscript_config(self) -> Dict[str, Any]:
		"""
		Get bootscript configuration for this product.
		
		Returns:
			Dictionary with segment, config, compute_config keys
		"""
		pass
	
	# ========================================================================
	# Mask and Configuration Management
	# ========================================================================
	
	@abstractmethod
	def get_valid_ate_masks(self) -> List[str]:
		"""
		Get list of valid ATE mask names for this product.
		
		Returns:
			List of mask names (e.g., ['FirstPass', 'SecondPass', ...])
		"""
		pass
	
	@abstractmethod
	def get_valid_customs(self) -> List[str]:
		"""
		Get list of valid custom mask options.
		
		Returns:
			List of custom options (e.g., ['ROW5', 'COL1', ...])
		"""
		pass
	
	@abstractmethod
	def init_voltage_config(self) -> Dict[str, List]:
		"""
		Initialize empty voltage configuration structure.
		
		Returns:
			Dictionary with voltage config structure for each domain
		"""
		pass
	
	# ========================================================================
	# DMR-Specific Methods (default implementations for non-DMR products)
	# ========================================================================
	
	def get_modules_per_cbb(self) -> Optional[int]:
		"""
		Get number of modules per CBB (DMR-specific).
		
		Returns:
			Number of modules per CBB, or None if not applicable
		"""
		return None
	
	def get_modules_per_compute(self) -> Optional[int]:
		"""
		Get number of modules per compute (DMR-specific).
		
		Returns:
			Number of modules per compute, or None if not applicable
		"""
		return None
	
	def get_active_modules_per_cbb(self) -> Optional[int]:
		"""
		Get number of active modules per CBB (DMR-specific).
		
		Returns:
			Number of active modules, or None if not applicable
		"""
		return None
	
	def get_max_cbbs(self) -> Optional[int]:
		"""
		Get maximum number of CBBs (DMR-specific).
		
		Returns:
			Max CBBs, or None if not applicable
		"""
		return None
	
	def get_max_imhs(self) -> Optional[int]:
		"""
		Get maximum number of IMHS (DMR-specific).
		
		Returns:
			Max IMHS, or None if not applicable
		"""
		return None
	
	# ========================================================================
	# Validation Methods
	# ========================================================================
	
	@abstractmethod
	def validate_core_id(self, core_id: int, id_type: str = 'logical') -> bool:
		"""
		Validate a core/module ID.
		
		Args:
			core_id: Core ID to validate
			id_type: 'logical' or 'physical'
			
		Returns:
			True if valid, False otherwise
		"""
		pass
	
	@abstractmethod
	def validate_domain(self, domain: str) -> bool:
		"""
		Validate a voltage domain name.
		
		Args:
			domain: Domain name to validate
			
		Returns:
			True if valid, False otherwise
		"""
		pass
	
	# ========================================================================
	# Display and Formatting
	# ========================================================================
	
	@abstractmethod
	def format_core_table(self, core_dict: Dict) -> str:
		"""
		Format a core dictionary for table display.
		
		Args:
			core_dict: Dictionary of core information
			
		Returns:
			Formatted table string
		"""
		pass
	
	def get_strategy_info(self) -> Dict[str, Any]:
		"""
		Get summary information about this strategy.
		
		Returns:
			Dictionary with strategy configuration details
		"""
		return {
			'product': self.get_product_name(),
			'core_type': self.get_core_type(),
			'core_string': self.get_core_string(),
			'domain_type': self.get_domain_display_name(),
			'total_domains': self.get_total_domains(),
			'max_cores': self.get_max_cores(),
			'max_logical': self.get_max_logical_cores(),
			'features': {
				'hdc_at_core': self.has_hdc_at_core(),
				'supports_600w': self.supports_600w_config(),
				'supports_ht': self.supports_hyperthreading(),
				'supports_2cpm': self.supports_2cpm(),
			}
		}
