"""
MDT Tools - Debug Module Wrapper

This module provides a convenient wrapper class for accessing debug.mdt_tools components.
All debug components (asf, cache, cms, ccf, cpm, etc.) are dynamically initialized
and available as instance attributes.

Note: The debug module is imported lazily - only when MDT_Tools is instantiated.
      This allows you to import debugtools without requiring debug to be available.

Usage Example:
--------------
from Tools.debugtools import MDT_Tools  # debug is NOT imported here

# Initialize with ALL components (slower, loads everything)
mdt = MDT_Tools()

# Initialize with ONLY specific components (faster, recommended for targeted tasks)
mdt = MDT_Tools(components='ccf')  # Only CCF for TOR dumps
mdt = MDT_Tools(components=['ccf', 'cache'])  # Only CCF and cache

# Or pass your own debug module
import debug
mdt = MDT_Tools(debug, components='ccf')

# Access any debug component directly
if mdt.ccf:
    ccf_data = mdt.ccf.get_cbos_tor_dump()

# Check which components are available
mdt.print_available_components()

# Use built-in helper functions
mdt.dpm_tor_dump(destination_path=r"C:\\Temp", visual_id="test_run_001")

Note: Initializing only needed components significantly improves initialization time.
      For TOR dumps, use: MDT_Tools(components='ccf')
"""


from datetime import datetime
import os
import pandas as pd


class MDT_Tools():
	"""
	MDT Tools wrapper class for debug module components.
	Dynamically initializes all available debug components (asf, cache, cms, ccf, etc.)
	as self attributes for easy access.

	Note: The debug module is imported only when the class is instantiated, not when
	      the module is imported. This allows the module to be imported without requiring
	      the debug module to be available.
	"""

	# List of all debug components that get initialized
	DEBUG_COMPONENTS = [
		'ccf', 'pm', 'xbar', 'xncu', 'santa'
 	#	'asf', 'cache', 'cms', 'ccf', 'cpm', 'cxlcm', 'dda', 'dsa',
	#	'fivr', 'hamvf', 'hap', 'hiop', 'hwrs', 'iaa', 'iommu',
	#	'iosfsb2ucie', 'iosf2sfi', 'isa', 'lcpll', 'ljpll', 'mc_subch',
	#	'mse', 'oobmsm', 'pcie', 'punit', 'rasip', 'resctrl',
	#	'rsrc_adapt', 'dts', 'rstw', 's3m', 'sca', 'ubox', 'ubr',
	#	'uciephy', 'ula', 'cxl', 'fsa'
	]

	def __init__(self, debug_module=None, components='all'):
		"""
		Initialize MDT_Tools with specified debug components.

		Args:
			debug_module: The debug module (default: None, will import debug automatically)
			components: Components to initialize. Options:
				- 'all': Initialize all components (default)
				- list: Initialize only specific components, e.g., ['ccf', 'cache']
				- str: Initialize a single component, e.g., 'ccf'

		Examples:
			mdt = MDT_Tools()  # Initialize all components
			mdt = MDT_Tools(components='ccf')  # Only CCF
			mdt = MDT_Tools(components=['ccf', 'cache'])  # Only CCF and cache
		"""
		# Lazy import of debug module - only import when class is instantiated
		if debug_module is None:
			print("Importing 'debug.mdt_tools' module...")
			import debug
			debug_module = debug

		self.debug_module = debug_module.mdt_tools

		# Dynamically set all available debug components as self attributes
		self._initialize_debug_components(components)

	def _initialize_debug_components(self, components='all'):
		"""
		Dynamically initialize debug components from debug.mdt_tools
		and set them as instance attributes (e.g., self.ccf, self.asf, etc.)

		Args:
			components: 'all', a single component name (str), or list of component names
		"""
		# Determine which components to initialize
		if components == 'all':
			components_to_init = self.DEBUG_COMPONENTS
		elif isinstance(components, str):
			components_to_init = [components]
		elif isinstance(components, list):
			components_to_init = components
		else:
			raise ValueError(f"Invalid components parameter: {components}. Must be 'all', string, or list.")

		# Initialize only requested components
		for component_name in components_to_init:
			if component_name not in self.DEBUG_COMPONENTS:
				print(f"Warning: '{component_name}' is not a valid component name")
				setattr(self, component_name, None)
				continue

			if hasattr(self.debug_module, component_name):
				setattr(self, component_name, getattr(self.debug_module, component_name))
				print(f"Initialized {component_name}")
			else:
				# Set to None if component is not available
				setattr(self, component_name, None)
				print(f"Warning: {component_name} not available in debug.mdt_tools")

		# Set all non-initialized components to None for safety
		for component_name in self.DEBUG_COMPONENTS:
			if not hasattr(self, component_name):
				setattr(self, component_name, None)


	def get_available_components(self):
		"""
		Return a dictionary of all initialized debug components and their availability status.

		Returns:
			dict: Component name -> availability (True/False)
		"""
		return {comp: getattr(self, comp) is not None for comp in self.DEBUG_COMPONENTS}

	def print_available_components(self):
		"""
		Print a formatted list of all available debug components.
		"""
		print("\n" + "="*60)
		print("DEBUG COMPONENTS STATUS")
		print("="*60)

		available = []
		unavailable = []

		for comp in self.DEBUG_COMPONENTS:
			if getattr(self, comp) is not None:
				available.append(comp)
			else:
				unavailable.append(comp)

		print(f"\nAvailable ({len(available)}):")
		for comp in available:
			print(f"  ✓ {comp}")

		if unavailable:
			print(f"\nUnavailable ({len(unavailable)}):")
			for comp in unavailable:
				print(f"  ✗ {comp}")

		print("="*60 + "\n")

	def dpm_tor_dump(self, destination_path=None, visual_id=None):
		"""
		Generate TOR dump from CCF component.

		Args:
			destination_path: Path to save the Excel file (default: C:\\Temp)
			visual_id: Optional identifier to include in filename
		"""
		if not self.ccf:
			print("Error: CCF component not available")
			return

		print("Generating TOR dump from CCF...")
		# Get TOR trackers from CCF
		tor_trk_valid = self.ccf.get_cbos_tor_trk_valid()
		get_cbos_tor_dump = self.ccf.get_cbos_tor_dump()

		print("TOR dump operations completed, saving to Excel...")
		# Save both trackers to the same Excel file with separate tabs
		self.dpm_save_excel_data([tor_trk_valid, get_cbos_tor_dump], destination_path=destination_path, visual_id=visual_id)

	def dpm_save_excel_data(self, trk, destination_path=None, visual_id=None):
		# Handle single tracker or list of trackers
		if not isinstance(trk, list):
			trk_list = [trk]
		else:
			trk_list = trk

		# Validate and prepare tracker data
		tracker_data = []
		for tracker in trk_list:
			if tracker and tracker.trk_table and isinstance(tracker.trk_table, (list, tuple)):
				try:
					title = tracker.trk_name
					ip_name = tracker.ip_name
					headers = list(tracker.trk_table[0].keys())
					table, text = tracker.prepare_table(title=title, table=tracker.trk_table, headers=headers)
					tracker_data.append({'title': title, 'data': tracker.trk_table})
				except AttributeError:
					continue
				except IndexError:
					# WA for https://hsdes.intel.com/appstore/article/#/18032905805
					print(f"something went wrong for tracker {title}")
					continue
			else:
				if tracker and tracker.trk_table:
					print(f"empty tracker: {tracker.trk_name}")

		if not tracker_data:
			print("No valid tracker data to save")
			return

		# Save to Excel file
		try:
			# Generate timestamp
			timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

			# Build filename
			if visual_id:
				filename = f"{timestamp}_{visual_id}_Tordump.xlsx"
			else:
				filename = f"{timestamp}_Tordump.xlsx"

			# Set destination path
			if destination_path is None:
				destination_path = r"C:\Temp"

			# Ensure destination directory exists
			os.makedirs(destination_path, exist_ok=True)

			# Create full file path
			full_path = os.path.join(destination_path, filename)

			# Create Excel writer object to write multiple sheets
			with pd.ExcelWriter(full_path, engine='openpyxl') as writer:
				for tracker_info in tracker_data:
					df = pd.DataFrame(tracker_info['data'])
					# Clean sheet name (Excel has 31 char limit and doesn't allow certain characters)
					sheet_name = tracker_info['title'][:31].replace('/', '_').replace('\\', '_').replace('[', '').replace(']', '')
					df.to_excel(writer, index=False, sheet_name=sheet_name)

			print(f"Data saved to: {full_path}")
			print(f"Sheets created: {', '.join([t['title'] for t in tracker_data])}")
		except Exception as e:
			print(f"Error saving to Excel: {e}")
