"""
S2TFlow Refactoring Example
Demonstrates how to use the new managers and product strategy in S2TFlow class.

This is an example/template showing the refactored approach. The actual SetTesterRegs.py
would need to be gradually migrated to use these patterns.

REV 0.1 -- Initial example implementation
"""

import sys
import os

# Add managers to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'managers'))

from voltage_manager import VoltageManager
from frequency_manager import FrequencyManager
from product_strategy import ProductStrategy


class S2TFlowRefactored:
	"""
	Refactored S2TFlow class using managers and strategy pattern.
	
	Key improvements:
	1. Voltage logic delegated to VoltageManager
	2. Frequency logic delegated to FrequencyManager  
	3. Product-specific logic handled by ProductStrategy
	4. Cleaner separation of concerns
	5. Easier to add new products
	"""
	
	def __init__(self,
				 config,  # ProductConfiguration from ConfigsLoader
				 dpm_module,  # DPM module for voltage/power operations
				 stc_module,  # STC module with frequency data
				 scm_module,  # SCM module
				 debug=False,
				 targetLogicalCore=None,
				 targetTile=None,
				 use_ate_freq=True,
				 use_ate_volt=False,
				 flowid=1,
				 execution_state=None,
				 **kwargs):  # Other parameters
		
		# Get product strategy from config
		self.strategy = config.get_strategy()
		if self.strategy is None:
			raise ValueError("Could not load product strategy")
		
		# Initialize managers
		self.voltage_mgr = VoltageManager(
			product_strategy=self.strategy,
			dpm_module=dpm_module,
			menus=self._init_menus(),
			features=config.FRAMEWORK_FEATURES
		)
		
		self.frequency_mgr = FrequencyManager(
			product_strategy=self.strategy,
			stc_module=stc_module,
			menus=self._init_menus(),
			features=config.FRAMEWORK_FEATURES
		)
		
		# Store references
		self.config = config
		self.dpm = dpm_module
		self.stc = stc_module
		self.scm = scm_module
		self.execution_state = execution_state
		
		# Basic settings
		self.debug = debug
		self.mode = None
		self.external = False
		self.product = config.PRODUCT_CONFIG
		
		# Core/Module selection
		self.targetLogicalCore = targetLogicalCore
		self.targetTile = targetTile
		
		# Pass through other kwargs
		for key, value in kwargs.items():
			setattr(self, key, value)
		
		# Product-specific initialization
		self._init_product_specific()
	
	def _init_product_specific(self):
		"""Initialize product-specific settings using strategy."""
		# Get product-specific data from strategy
		self.core_string = self.strategy.get_core_string()
		self.core_type = self.strategy.get_core_type()
		self.HDC_AT_CORE = self.strategy.has_hdc_at_core()
		
		# Domain names (computes vs cbbs)
		self.domains = self.strategy.get_voltage_domains()
		self.domain_type = self.strategy.get_domain_display_name()
		
		# Product capabilities
		self.supports_600w = self.strategy.supports_600w_config()
		self.supports_ht = self.strategy.supports_hyperthreading()
		self.supports_2cpm = self.strategy.supports_2cpm()
		
		print(f"\n{'='*80}")
		print(f"Initialized S2TFlow for {self.strategy.get_product_name()}")
		print(f"  Core Type: {self.core_type}")
		print(f"  Core String: {self.core_string}")
		print(f"  Domain Type: {self.domain_type}")
		print(f"  Domains: {', '.join(self.domains)}")
		print(f"={'='*80}\n")
	
	def _init_menus(self):
		"""Initialize menu strings - would come from config."""
		return {
			'CoreVolt': '> Set Core Voltage?',
			'CoreBump': '> Set Core vBump?',
			'CFCVolt': '> Set Uncore CFC Voltage?',
			'CFCBump': '> Set Uncore CFC vBump?',
			'HDCVolt': '> Set Uncore HDC Voltage?',
			'HDCBump': '> Set Uncore HDC vBump?',
			'CFCIOVolt': '> Set CFC IO DIE Voltage?',
			'CFCIOBump': '> Set CFC IO DIE vBump?',
			'DDRDVolt': '> Set DDRD Voltage?',
			'DDRDBump': '> Set DDRD vBump?',
			'CoreFreq': '> Set Core Frequency?',
			'MeshFreq': '> Set Mesh Frequency?',
			'IOFreq': '> Set IO Frequency?',
			'vbumpfix': '--> Value out of range (-0.2V to 0.2V). Enter valid vBump: ',
			# ... more menus
		}
	
	# ========================================================================
	# REFACTORED VOLTAGE CONFIGURATION
	# ========================================================================
	
	def set_voltage(self, input_func=input):
		"""
		Configure voltage using VoltageManager.
		
		OLD CODE:
			- 200+ lines of inline voltage configuration logic
			- Product-specific conditionals scattered throughout
			- Hard to maintain and extend
		
		NEW CODE:
			- Single call to voltage manager
			- Product differences handled by strategy
			- Clean and maintainable
		"""
		# Initialize voltage tables with safe voltages
		self.voltage_mgr.init_voltage_tables(
			mode=self.mode,
			safe_volts_pkg=self.stc.All_Safe_RST_PKG,
			safe_volts_cdie=self.stc.All_Safe_RST_CDIE
		)
		
		# Configure voltage (handles all options: ATE, fixed, vbumps, PPVC)
		configured = self.voltage_mgr.configure_voltage(
			use_ate_volt=self.voltage_mgr.use_ate_volt,
			external=self.external,
			fastboot=getattr(self, 'fastboot', False),
			core_string=self.core_string,
			input_func=input_func
		)
		
		if configured:
			print(f"\n> Voltage configured successfully")
			# Get configured values back
			volt_dict = self.voltage_mgr.get_voltage_dict()
			self.volt_config = volt_dict['volt_config']
			self.custom_volt = volt_dict['custom_volt']
			self.vbumps_volt = volt_dict['vbumps_volt']
			self.ppvc_fuses = volt_dict['ppvc_fuses']
	
	def set_voltage_quick(self, core_vbump, mesh_vbump):
		"""
		Quick voltage configuration for external tools.
		
		OLD CODE:
			- Duplicated logic from main voltage configuration
			- Different code paths for different products
		
		NEW CODE:
			- Reuses same voltage manager
			- Consistency guaranteed
		"""
		self.external = True
		self.voltage_mgr.init_voltage_tables(mode=self.mode)
		
		self.voltage_mgr.configure_voltage(
			use_ate_volt=False,
			external=True,
			volt_select=3,  # Vbumps
			qvbumps_core=core_vbump,
			qvbumps_mesh=mesh_vbump,
			fastboot=False
		)
	
	# ========================================================================
	# REFACTORED FREQUENCY CONFIGURATION
	# ========================================================================
	
	def set_frequency(self, input_func=input):
		"""
		Configure frequency using FrequencyManager.
		
		OLD CODE:
			- Mixed ATE and manual frequency logic
			- Product-specific frequency tables embedded
			- Difficult to add new frequency options
		
		NEW CODE:
			- Delegated to frequency manager
			- Product data from STC module
			- Clean separation
		"""
		# Try ATE frequency first
		ate_configured = self.frequency_mgr.configure_ate_frequency(
			mode=self.mode,
			core_string=self.core_string,
			input_func=input_func
		)
		
		if not ate_configured:
			# Fall back to manual frequency configuration
			self.frequency_mgr.configure_manual_frequency(input_func=input_func)
		
		# Get configured values
		freq_dict = self.frequency_mgr.get_frequency_dict()
		self.core_freq = freq_dict['core_freq']
		self.mesh_freq = freq_dict['mesh_freq']
		self.io_freq = freq_dict['io_freq']
		self.flowid = freq_dict['flowid']
		
		print(f"\n> Frequency configured:")
		print(f"  {self.core_string}: {self.core_freq}")
		print(f"  Mesh: {self.mesh_freq}")
		print(f"  IO: {self.io_freq}")
	
	# ========================================================================
	# PRODUCT-SPECIFIC OPERATIONS USING STRATEGY
	# ========================================================================
	
	def display_available_cores(self, array):
		"""
		Display available cores using product strategy.
		
		OLD CODE:
			- Different display logic for each product
			- Hard-coded "CORE" vs "MODULE" strings
			- Manual table formatting
		
		NEW CODE:
			- Strategy handles product differences
			- Consistent display across products
		"""
		print(f"\n{'='*80}")
		print(f"Available {self.core_string}s for {self.strategy.get_product_name()}")
		print(f"{'='*80}\n")
		
		# Let strategy format the core table
		table = self.strategy.format_core_table(array['CORES'])
		print(table)
	
	def validate_core_selection(self, core_id):
		"""
		Validate core selection using product strategy.
		
		OLD CODE:
			- Manual range checks
			- Product-specific validation logic
		
		NEW CODE:
			- Strategy handles validation
			- Accounts for product differences
		"""
		if not self.strategy.validate_core_id(core_id, id_type='physical'):
			print(f"Error: Invalid {self.core_string} ID: {core_id}")
			return False
		return True
	
	def get_bootscript_config(self):
		"""
		Get bootscript configuration using product strategy.
		
		OLD CODE:
			- Hardcoded compute0/compute1/compute2 vs cbb0/cbb1/cbb2
			- Different segment names per product
		
		NEW CODE:
			- Strategy provides correct configuration
			- Works for computes or CBBs automatically
		"""
		return self.strategy.get_bootscript_config()
	
	# ========================================================================
	# CONFIGURATION SAVE/LOAD WITH MANAGERS
	# ========================================================================
	
	def save_config(self, file_path):
		"""
		Save configuration including manager states.
		
		Enhancement: Now saves voltage and frequency manager states
		"""
		import json
		
		config = {
			'product': self.strategy.get_product_name(),
			'mode': self.mode,
			'targetLogicalCore': self.targetLogicalCore,
			'targetTile': self.targetTile,
			
			# Voltage configuration from manager
			'voltage': self.voltage_mgr.get_voltage_dict(),
			
			# Frequency configuration from manager
			'frequency': self.frequency_mgr.get_frequency_dict(),
			
			# Other settings...
			'flowid': self.flowid,
			'fastboot': getattr(self, 'fastboot', False),
			# ... more settings
		}
		
		with open(file_path, 'w') as f:
			json.dump(config, f, indent=4)
		
		print(f"\n> Configuration saved to: {file_path}")
	
	def load_config(self, file_path):
		"""
		Load configuration and restore manager states.
		"""
		import json
		
		with open(file_path, 'r') as f:
			config = json.load(f)
		
		# Validate product matches
		if config.get('product') != self.strategy.get_product_name():
			print(f"Warning: Config was for {config.get('product')}, current product is {self.strategy.get_product_name()}")
		
		# Restore basic settings
		self.mode = config.get('mode')
		self.targetLogicalCore = config.get('targetLogicalCore')
		self.targetTile = config.get('targetTile')
		
		# Restore voltage manager state
		if 'voltage' in config:
			self.voltage_mgr.set_from_dict(config['voltage'])
		
		# Restore frequency manager state
		if 'frequency' in config:
			self.frequency_mgr.set_from_dict(config['frequency'])
		
		print(f"\n> Configuration loaded from: {file_path}")


# ========================================================================
# EXAMPLE USAGE
# ========================================================================

def example_usage():
	"""
	Example showing how to use the refactored S2TFlow.
	"""
	
	# This would normally come from ConfigsLoader
	# from ConfigsLoader import config, dpm, stc, scm
	
	# Create S2TFlow instance
	# flow = S2TFlowRefactored(
	#     config=config,
	#     dpm_module=dpm,
	#     stc_module=stc,
	#     scm_module=scm,
	#     debug=False,
	#     use_ate_freq=True,
	#     use_ate_volt=False
	# )
	
	# Configure voltages
	# flow.set_voltage()
	
	# Configure frequencies
	# flow.set_frequency()
	
	# Product automatically adapts:
	# - GNR/CWF use compute0/compute1/compute2
	# - DMR uses cbb0/cbb1/cbb2/cbb3
	# - Core vs Module terminology automatic
	# - HDC at core vs uncore handled automatically
	
	pass


if __name__ == "__main__":
	print(__doc__)
	print("\nThis is an example/template file.")
	print("See the code for refactoring patterns to apply to SetTesterRegs.py")
