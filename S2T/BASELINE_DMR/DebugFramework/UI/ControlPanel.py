import asyncio.events
import tkinter as tk
from tkinter import filedialog, messagebox,ttk
import sys
import os
import pandas as pd
import time
import threading
import queue
import multiprocessing
from contextlib import contextmanager
from colorama import Fore, Style, Back
from datetime import datetime
import socket
import json
import weakref
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
import importlib

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

print(' -- Debug Framework Control Panel -- rev 1.7')

sys.path.append(parent_dir)

import DebugFramework.FileHandler as fh
import DebugFramework.MaskEditor as gme
import DebugFramework.UI.StatusHandler as fs

from DebugFramework.UI.StatusPanel import StatusExecutionPanel

import DebugFramework.ExecutionHandler.utils.ThreadsHandler as th

importlib.reload(th)

ExecutionCommand = th.ExecutionCommand
execution_state = th.execution_state

#importlib.reload(fh)
#importlib.reload(gme)
importlib.reload(fs)

#from .. import FileHandler as fh
#from .. import MaskEditor  as gme

# Default configuration dictionary
S2T_CONFIGURATION = {
	'AFTER_MRC_POST': 0xbf000000,
	'EFI_POST': 0xef0000ff,
	'LINUX_POST': 0x58000000,
	'BOOTSCRIPT_RETRY_TIMES': 3,
	'BOOTSCRIPT_RETRY_DELAY': 60,
	'MRC_POSTCODE_WT': 30,
	'EFI_POSTCODE_WT': 60,
	'MRC_POSTCODE_CHECK_COUNT': 5,
	'EFI_POSTCODE_CHECK_COUNT': 10,
	'BOOT_STOP_POSTCODE' : 0x0,
	'BOOT_POSTCODE_WT' : 30,
	'BOOT_POSTCODE_CHECK_COUNT' : 1
}

# Default configuration dictionary
PLATFORM_CONFIGURATION = {
	'COM_PORT': 8,
	'IP_ADDRESS': '192.168.0.2',
}

# Mapping of labels to configuration keys
CONFIG_LABELS = {
	'Bootscript retries': 'BOOTSCRIPT_RETRY_TIMES',
	'Bootscript retry PC delay': 'BOOTSCRIPT_RETRY_DELAY',
	'EFI Postcode': 'EFI_POST',
	'EFI Postcode Waittime': 'EFI_POSTCODE_WT',
	'EFI Postcode checks count': 'EFI_POSTCODE_CHECK_COUNT',
	'OTHER Postcode': 'LINUX_POST',
	'MRC Postcode': 'AFTER_MRC_POST',
	'MRC Postcode Waittime': 'MRC_POSTCODE_WT',
	'MRC Postcode checks count': 'MRC_POSTCODE_CHECK_COUNT',
	'Boot Break Postcode': 'BOOT_STOP_POSTCODE',
	'Boot Break Waittimet': 'BOOT_POSTCODE_WT',
	'Boot Break checks count': 'BOOT_POSTCODE_CHECK_COUNT'
}

# Select Execution Type Process or Threads ---
use_process = False
debug = False

#########################################################
######		Configuration Classes
#########################################################

@dataclass
class UICommand:
	command_type: str
	data: Dict[str, Any]

class UICommandType(Enum):
	START_EXPERIMENT = "start_experiment"
	CANCEL_EXPERIMENT = "cancel_experiment"
	END_EXPERIMENT = "end_experiment"
	HOLD_EXPERIMENT = "hold_experiment"

#########################################################
######		Control Panel Code
#########################################################

class TaskCancelledException(Exception):
	"""Execution Cancelled by User"""
	pass

class ThreadHandler(threading.Thread):
	def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
		super().__init__(group, target, name, args, kwargs, daemon=daemon)
		self._stop_event = threading.Event()
		self.exception_queue = queue.Queue()
		# Store references but don't access them from this thread
		self._target_func = target
		self._target_args = args
		self._target_kwargs = kwargs or {}

	def run(self):
		try:
			print(f"({self.name}) --> Started\n")
			if self._target_func:
				# Don't pass any Tkinter objects to the target function
				self._target_func(*self._target_args, **self._target_kwargs)
				print(f"({self.name}) --> Ended")
		except Exception as e:
			print(f'({self.name}) --> Exception:', e)
			self.exception_queue.put(e)

	def stop(self):
		print(f"\n({self.name}) --> Stop order received")
		self._stop_event.set()

	def get_exception(self):
		"""Retrieve any exception raised during thread execution."""
		if not self.exception_queue.empty():
			return self.exception_queue.get()
		return None

class EditExperimentWindow(tk.Toplevel):

	_open_windows = []

	def __init__(self, parent, data, update_callback, add_new_callback=None, mode="edit", config_file='GNRControlPanelConfig.json'):

		# Check for existing windows
		if EditExperimentWindow._open_windows:
			existing_window = EditExperimentWindow._open_windows[0]
			if existing_window.winfo_exists():
				existing_window.lift()  # Bring existing window to front
				existing_window.focus_force()
				messagebox.showinfo("Window Already Open",
								"An experiment editor window is already open. Please close it first.")
				return
			else:
				# Clean up dead reference
				EditExperimentWindow._open_windows.clear()

		super().__init__(parent)

		# Register this window
		EditExperimentWindow._open_windows.append(self)

		self.parent = parent
		self.data = data
		self.update_callback = update_callback
		self.add_new_experiment_callback = add_new_callback
		self.mode = mode  # "edit" or "add_new"
		self.config_file = config_file

		# Extract product from config filename (e.g., 'GNRControlPanelConfig.json' -> 'GNR')
		self.current_product = config_file.replace('ControlPanelConfig.json', '') if 'ControlPanelConfig.json' in config_file else 'GNR'
		print(f"[EDIT WINDOW] Initializing with config_file='{config_file}', extracted product='{self.current_product}'")

		# Add validation debouncing
		self.validation_timer = None
		self.pending_validations = set()

		# Load configuration
		self.load_configuration()

		# Initialize all possible fields with default values if they don't exist
		self._initialize_missing_fields()

		self.input_vars = {
			key: tk.StringVar(value=str(value) if value is not None else '')
			for key, value in self.data.items()
		}
		
		# Now that input_vars exist, populate MASK_OPTIONS based on current Test Mode
		self.MASK_OPTIONS = self._get_field_options('Configuration (Mask)')
		print(f"[EDIT WINDOW INIT] Initial MASK_OPTIONS based on Test Mode '{self.data.get('Test Mode', '')}': {self.MASK_OPTIONS}")

		if 'Type' in self.input_vars:
			self.input_vars['Type'].trace('w', self.on_type_change)
		
		# Bind Test Mode changes to update Configuration (Mask) field
		if 'Test Mode' in self.input_vars:
			self.input_vars['Test Mode'].trace('w', self.on_test_mode_change)

		# Initialize widgets and frames
		self.widgets = {}
		self.tab_frames = {}
		self.validation_indicators = {}
		self.field_dependencies = {}

		# Set window title based on mode
		if mode == "add_new":
			title = "Add New Experiment"
		else:
			title = f"Edit - {self.data.get('Test Name', 'Experiment')}"
		self.title(title)

		# Create main container
		container = tk.Frame(self)
		container.pack(fill="both", expand=True, padx=5, pady=5)

		# Create status bar for validation feedback
		self.status_frame = tk.Frame(container)
		self.status_frame.pack(fill="x", pady=(0, 5))

		self.status_label = tk.Label(self.status_frame, text="Ready",
								   relief=tk.SUNKEN, anchor="w")
		self.status_label.pack(side="left", fill="x", expand=True)

		self.validation_count_label = tk.Label(self.status_frame, text="",
											 foreground="red")
		self.validation_count_label.pack(side="right")

		# Create notebook for tabs
		self.notebook = ttk.Notebook(container)
		self.notebook.pack(fill="both", expand=True)

		# Create tabs
		self.create_tabs()

		# Create button frame with mode-specific buttons
		self.create_button_frame(container)

		# Set window size and make it resizable
		self.geometry("600x800")
		self.minsize(600, 600)
		self.protocol("WM_DELETE_WINDOW", self.on_closing)

		# Bind content change to update field visibility
		if 'Content' in self.input_vars:
			self.input_vars['Content'].trace('w', self.on_content_change)

		# Bind test type change
		if 'Test Type' in self.input_vars:
			self.input_vars['Test Type'].trace('w', self.on_test_type_change)

		# Initial validation
		self.after(500, self.validate_all_fields)

	def create_button_frame(self, container):
		"""Create button frame with mode-specific buttons"""
		button_frame = tk.Frame(container)
		button_frame.pack(fill="x", pady=(10, 0))

		# Left side buttons
		left_buttons = tk.Frame(button_frame)
		left_buttons.pack(side="left")

		ttk.Button(left_buttons, text=" Validate ",
				  command=self.validate_all_fields).pack(side="left")
		ttk.Button(left_buttons, text=" Reset ",
				  command=self.reset_to_defaults).pack(side="left", padx=(5, 0))
		ttk.Button(left_buttons, text=" Import ",
				  command=self.import_from_file).pack(side="left", padx=(5, 0))
		ttk.Button(left_buttons, text=" Export ",
				  command=self.export_to_file).pack(side="left", padx=(5, 0))

		# Mode-specific buttons
		if self.mode == "edit":
			# Edit mode: Save changes + Save as New
			ttk.Button(left_buttons, text=" Save as New ",
					  command=self.save_as_new_experiment).pack(side="left", padx=(5, 0))

		# Right side buttons
		right_buttons = tk.Frame(button_frame)
		right_buttons.pack(side="right")

		ttk.Button(right_buttons, text="Cancel",
				  command=self.on_closing).pack(side="right")

		if self.mode == "add_new":
			# Add mode: Create Experiment button
			ttk.Button(right_buttons, text="Create Experiment",
					  command=self.create_new_experiment).pack(side="right", padx=(0, 5))
		else:
			# Edit mode: Save Changes button
			ttk.Button(right_buttons, text=" Save Changes ",
					  command=self.save_changes).pack(side="right", padx=(0, 5))

	def create_new_experiment(self):
		"""Create a new experiment (for add_new mode)"""
		try:
			# Check if we have existing experiments to use as templates
			available_experiments = self.get_available_experiments()

			if available_experiments:
				# Show template selection dialog
				template_choice = self.show_template_selection_dialog(available_experiments)
				if template_choice is None:  # User cancelled
					return
			else:
				template_choice = "current"  # Use current form values

			# Get new experiment name
			new_name = self.get_new_experiment_name()
			if not new_name:
				return

			# Create new experiment data based on template choice
			if template_choice == "empty":
				new_experiment_data = self.create_empty_experiment()
			elif template_choice == "current":
				current_values = self.get_values()
				new_experiment_data = self._convert_values_to_proper_types(current_values)
			else:
				new_experiment_data = self.create_from_template(template_choice)

			# Set the experiment name and enable it
			new_experiment_data['Test Name'] = new_name
			new_experiment_data['Experiment'] = 'Enabled'

			# Log creation to console
			self._log_configuration_changes({}, new_experiment_data, "CREATE_NEW", new_name)

			# Call the callback to add the new experiment
			if self.add_new_experiment_callback:
				self.add_new_experiment_callback(new_name, new_experiment_data)
				messagebox.showinfo("Success", f"New experiment '{new_name}' created successfully!")
				self.destroy()
			else:
				messagebox.showwarning("Error", "Cannot add new experiment - callback not available")

		except Exception as e:
			error_msg = f"Failed to create new experiment: {str(e)}"
			print(f"ERROR: {error_msg}")
			messagebox.showerror("Error", error_msg)

	def save_as_new_experiment(self):
		"""Save current configuration as a new experiment with change logging"""
		try:
			# Get new experiment name
			new_name = self.get_new_experiment_name()
			if not new_name:
				return

			# Create new experiment data from current values
			current_values = self.get_values()
			new_experiment_data = self._convert_values_to_proper_types(current_values)

			# Set the experiment name and enable it
			new_experiment_data['Test Name'] = new_name
			new_experiment_data['Experiment'] = 'Enabled'

			# Log creation to console
			self._log_configuration_changes({}, new_experiment_data, "SAVE_AS_NEW", new_name)

			# Call the callback to add the new experiment
			if self.add_new_experiment_callback:
				self.add_new_experiment_callback(new_name, new_experiment_data)
				messagebox.showinfo("Success", f"New experiment '{new_name}' created successfully!")
			else:
				messagebox.showwarning("Error", "Cannot add new experiment - callback not available")

		except Exception as e:
			error_msg = f"Failed to create new experiment: {str(e)}"
			print(f"ERROR: {error_msg}")
			messagebox.showerror("Error", error_msg)

	def _convert_values_to_proper_types(self, current_values):
		"""Convert string values to proper types based on field configuration"""
		converted_data = {}

		for field, value_str in current_values.items():
			if field not in self.data_types:
				converted_data[field] = value_str
				continue

			field_types = self.data_types[field]
			converted_value = None

			# Handle empty/None values
			if not value_str or value_str.strip() == '' or value_str == 'None':
				if field in self.mandatory_fields:
					converted_value = self.data.get(field, '')  # Keep original if mandatory
				else:
					converted_value = None
			else:
				# Try to convert to appropriate type
				for field_type in field_types:
					try:
						if field_type == bool:
							converted_value = value_str.lower() in ['true', '1', 'yes', 'on']
							break
						elif field_type == int:
							# Special handling for Start, End, Steps based on Type
							if field in ['Start', 'End', 'Steps']:
								type_value = current_values.get('Type', '')
								if type_value.lower() == 'frequency':
									converted_value = int(float(value_str))  # Allow float input, convert to int
								else:
									converted_value = int(value_str)
							else:
								converted_value = int(value_str)
							break
						elif field_type == float:
							converted_value = float(value_str)
							break
						elif field_type == str:
							converted_value = str(value_str).strip()
							break
					except (ValueError, TypeError):
						continue

				# If no conversion worked, keep as string
				if converted_value is None:
					converted_value = str(value_str).strip()

			converted_data[field] = converted_value

		return converted_data

	def _initialize_missing_fields(self):
		"""Initialize any missing fields with default values from config"""
		all_fields = set()

		# Collect all possible fields from field_configs
		for field in self.field_configs.keys():
			all_fields.add(field)

		# Add missing fields with default values from config
		for field in all_fields:
			if field not in self.data:
				field_config = self.field_configs.get(field, {})
				default_value = field_config.get('default', '')

				# Use configured default if it exists and is not empty string
				if default_value != '' and default_value is not None:
					self.data[field] = default_value
				else:
					# Use empty string for fields without defaults
					self.data[field] = ''

	def load_configuration(self):
		"""Load configuration from PPV/configs folder using new field_configs format"""
		# Try to load from DebugFramework's PPV/configs folder
		current_dir = os.path.dirname(__file__)
		# Navigate to PPV/configs: UI -> DebugFramework -> PPV -> configs
		ppv_config_dir = os.path.join(current_dir, '..', 'PPV', 'configs')
		ppv_config_path = os.path.join(ppv_config_dir, self.config_file)

		# Fallback to old location if PPV config doesn't exist
		old_config_path = os.path.join(current_dir, self.config_file)

		config_path = ppv_config_path if os.path.exists(ppv_config_path) else old_config_path

		# Log which config file is being loaded
		config_location = "PPV/configs" if config_path == ppv_config_path else "UI folder"
		print(f"[EDIT WINDOW] Loading config from {config_location}: {config_path}")

		try:
			with open(config_path) as config_file:
				config_data = json.load(config_file)
				# Migrate old format to new format if needed
				config_data = self.migrate_config_format(config_data)
		except FileNotFoundError:
			messagebox.showerror("Configuration Error",
						   f"Configuration file '{self.config_file}' not found in PPV/configs or UI folder.")
			self.destroy()
			return
		except json.JSONDecodeError as e:
			messagebox.showerror("Configuration Error",
						   f"Invalid JSON in configuration file: {e}")
			self.destroy()
			return

		# Store the full configuration
		self.config_template = config_data
		self.field_configs = config_data.get('field_configs', {})
		self.field_enable_config = config_data.get('field_enable_config', {})
		self.config_product = config_data.get('PRODUCT', 'GNR')
		print(f"[EDIT WINDOW] Config loaded successfully. PRODUCT from config: '{self.config_product}', current_product: '{self.current_product}'")

		# Build data_types from field_configs for backward compatibility
		type_mapping = {
			"str": str,
			"int": int,
			"float": float,
			"bool": bool,
			"dict": dict
		}

		data_types_with_objects = {}
		for field_name, field_config in self.field_configs.items():
			field_type = field_config.get('type', 'str')
			data_types_with_objects[field_name] = [type_mapping.get(field_type, str)]

		self.data_types = data_types_with_objects

		# Extract options and metadata from field_configs
		self.TEST_MODES = config_data.get('TEST_MODES', [])
		self.TEST_TYPES = config_data.get('TEST_TYPES', [])
		self.VOLTAGE_TYPES = config_data.get('VOLTAGE_TYPES', [])
		self.TYPES = config_data.get('TYPES', [])
		self.DOMAINS = config_data.get('DOMAINS', [])
		self.CONTENT_OPTIONS = config_data.get('CONTENT_OPTIONS', [])

		# Note: MASK_OPTIONS will be populated after input_vars are initialized
		# because it depends on the current Test Mode value
		self.MASK_OPTIONS = []
		self.CORE_LICENSE_OPTIONS = self._get_field_options('Core License')
		self.DISABLE_2_CORES_OPTIONS = self._get_field_options('Disable 2 Cores')
		self.DISABLE_1_CORE_OPTIONS = self._get_field_options('Disable 1 Core')

		# Build field descriptions and mandatory fields from field_configs
		self.field_descriptions = {}
		self.mandatory_fields = []
		for field_name, field_config in self.field_configs.items():
			if field_config.get('description'):
				self.field_descriptions[field_name] = field_config['description']
			if field_config.get('required', False):
				self.mandatory_fields.append(field_name)

		# Build field groups by section
		self.FIELD_GROUPS = self._build_field_groups_from_sections()

		# Build fields to hide based on conditions
		self.fields_to_hide = self._build_conditional_fields()

	def migrate_config_format(self, config):
		"""Migrate old data_types format to new field_configs format"""
		if 'field_configs' in config:
			# Already in new format
			return config

		if 'data_types' not in config:
			# No data types, return as-is
			return config

		# Convert old format to new format
		new_config = config.copy()
		new_config['field_configs'] = {}

		for field_name, type_list in config['data_types'].items():
			field_type = type_list[0] if type_list else 'str'
			# Determine section based on field name patterns
			section = self._guess_section_for_field(field_name)
			new_config['field_configs'][field_name] = {
				'section': section,
				'type': field_type if isinstance(field_type, str) else field_type.__name__,
				'default': self._get_default_for_type(field_type if isinstance(field_type, str) else field_type.__name__),
				'description': config.get('field_descriptions', {}).get(field_name, f'{field_name} field'),
				'required': field_name in config.get('mandatory_fields', [])
			}

		# Remove old data_types
		if 'data_types' in new_config:
			del new_config['data_types']

		return new_config

	def _get_default_for_type(self, field_type):
		"""Get default value for a field type"""
		defaults = {
			'str': '',
			'int': 0,
			'float': 0.0,
			'bool': False
		}
		return defaults.get(field_type, '')

	def _guess_section_for_field(self, field_name):
		"""Guess section for a field based on its name"""
		if any(x in field_name.lower() for x in ['linux', 'dragon', 'merlin', 'ulx', 'vvar']):
			if 'linux' in field_name.lower():
				return 'Linux'
			if 'dragon' in field_name.lower() or 'ulx' in field_name.lower() or 'vvar' in field_name.lower():
				return 'Dragon'
			if 'merlin' in field_name.lower():
				return 'Merlin'
		if any(x in field_name.lower() for x in ['voltage', 'frequency']):
			return 'Voltage & Frequency'
		if any(x in field_name.lower() for x in ['loop']):
			return 'Loops'
		if any(x in field_name.lower() for x in ['sweep', 'start', 'end', 'step', 'domain']):
			return 'Sweep'
		if any(x in field_name.lower() for x in ['shmoo']):
			return 'Shmoo'
		if any(x in field_name.lower() for x in ['ttl', 'script', 'pass', 'fail']):
			return 'Advanced Configuration'
		if field_name in ['Visual ID', 'Bucket', 'COM Port', 'IP Address']:
			return 'Unit Data'
		if field_name in ['Test Name', 'Test Mode', 'Test Type', 'Experiment']:
			return 'Basic Information'
		return 'Test Configuration'

	def _get_field_options(self, field_name):
		"""Get options for a field from field_configs"""
		if field_name not in self.field_configs:
			return []
		
		field_config = self.field_configs[field_name]
		
		# Check for conditional_options (e.g., Configuration (Mask) depends on Test Mode)
		if 'conditional_options' in field_config:
			conditional = field_config['conditional_options']
			dependent_field = conditional.get('field')
			
			if dependent_field:
				# Get current value of the dependent field
				current_value = self.data.get(dependent_field, '')
				
				# If dependent field is in input_vars, get the current UI value
				if hasattr(self, 'input_vars') and dependent_field in self.input_vars:
					current_value = self.input_vars[dependent_field].get()
				
				# Get options for the current value
				if current_value in conditional:
					option_config = conditional[current_value]
					return option_config.get('options', [])
		
		# Fall back to regular options
		return field_config.get('options', [])

	def _build_field_groups_from_sections(self):
		"""Build FIELD_GROUPS structure from field_configs sections"""
		groups = {
			'Config': {},
			'Linux': {},
			'EFI/Dragon': {}
		}

		# Map sections to tabs
		section_to_tab = {
			'Basic Information': 'Config',
			'Test Configuration': 'Config',
			'Unit Data': 'Config',
			'Voltage & Frequency': 'Config',
			'Loops': 'Config',
			'Sweep': 'Config',
			'Shmoo': 'Config',
			'Advanced Configuration': 'Config',
			'Linux': 'Linux',
			'Dragon': 'EFI/Dragon',
			'Merlin': 'EFI/Dragon'
		}

		# Group fields by section within tabs
		for field_name, field_config in self.field_configs.items():
			section = field_config.get('section', 'Test Configuration')
			tab_name = section_to_tab.get(section, 'Config')

			if section not in groups[tab_name]:
				groups[tab_name][section] = []

			groups[tab_name][section].append(field_name)

		return groups

	def _build_conditional_fields(self):
		"""Build fields_to_hide based on conditions in field_configs"""
		fields_to_hide = {
			'Loops': [],
			'Sweep': [],
			'Shmoo': []
		}

		# Find fields with Test Type conditions
		for field_name, field_config in self.field_configs.items():
			condition = field_config.get('condition', {})
			if condition.get('field') == 'Test Type':
				required_value = condition.get('value')
				# Hide this field for other test types
				for test_type in ['Loops', 'Sweep', 'Shmoo']:
					if test_type != required_value:
						fields_to_hide[test_type].append(field_name)

		return fields_to_hide

	def create_tabs(self):
		"""Create tabs for different categories"""
		tab_names = ["Config", "Linux", "EFI/Dragon"]

		for tab_name in tab_names:
			# Create tab frame
			tab_frame = ttk.Frame(self.notebook)
			self.notebook.add(tab_frame, text=tab_name)

			# Create scrollable content for each tab
			canvas = tk.Canvas(tab_frame)
			scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
			scrollable_frame = ttk.Frame(canvas)

			scrollable_frame.bind(
				"<Configure>",
				lambda e, c=canvas: c.configure(scrollregion=c.bbox("all"))
			)

			canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
			canvas.configure(yscrollcommand=scrollbar.set)

			# Bind mousewheel to canvas
			def _on_mousewheel(event, canvas=canvas):
				canvas.yview_scroll(int(-1*(event.delta/120)), "units")

			canvas.bind("<MouseWheel>", _on_mousewheel)

			scrollbar.pack(side="right", fill="y")
			canvas.pack(side="left", fill="both", expand=True)

			# Store references
			self.tab_frames[tab_name] = {
				'canvas': canvas,
				'scrollable_frame': scrollable_frame,
				'scrollbar': scrollbar
			}

			# Populate tab content
			self.populate_tab_fields(tab_name, scrollable_frame)

	def populate_tab_fields(self, tab_name, parent_frame):
		"""Populate fields for a specific tab"""
		if tab_name not in self.FIELD_GROUPS:
			return

		selected_type = self.input_vars.get('Test Type', tk.StringVar()).get()
		hide_fields = self.fields_to_hide.get(selected_type, [])

		row = 0

		for group_name, fields in self.FIELD_GROUPS[tab_name].items():
			# Check if group has any visible fields
			visible_fields = [field for field in fields if field not in hide_fields and field in self.data_types]

			if not visible_fields:
				continue

			# Create group frame with reduced padding
			group_frame = ttk.LabelFrame(parent_frame, text=group_name, padding=(8, 4))
			group_frame.grid(row=row, column=0, sticky='EW', padx=8, pady=3)
			parent_frame.grid_columnconfigure(0, weight=1)

			field_row = 0
			for field in visible_fields:
				self.create_field_widget(group_frame, field, field_row, tab_name)
				field_row += 1

			row += 1

	def create_field_widget(self, parent, field, row, tab_name):
		"""Optimized widget creation with reduced validation calls - uses field_configs"""
		if field not in self.data_types and field not in self.field_configs:
			return

		# Get field configuration
		field_config = self.field_configs.get(field, {})
		field_types = self.data_types.get(field, [str])
		field_type = field_config.get('type', 'str')
		entry_widget = None

		# Create label with mandatory indicator - optimized width
		label_text = field
		if field in self.mandatory_fields or field_config.get('required', False):
			label_text += " *"

		label = ttk.Label(parent, text=label_text, width=20)
		label.grid(row=row, column=0, sticky='W', padx=5, pady=2)

		# Add validation indicator
		validation_indicator = tk.Label(parent, text="", width=1,
									relief="flat")
		validation_indicator.grid(row=row, column=1, padx=(2, 5))
		self.validation_indicators[field] = validation_indicator

		# Get options from field_config if available
		field_options = field_config.get('options', [])

		# Check if field should be disabled based on product (field_enable_config)
		field_enabled = True
		if hasattr(self, 'field_enable_config') and field in self.field_enable_config:
			enabled_products = self.field_enable_config[field]
			field_enabled = self.current_product in enabled_products

		# Special handling for Product field - always read-only and matches config
		if field == 'Product':
			field_enabled = False  # Make it read-only
			# Ensure it matches the current product from config
			self.input_vars[field].set(self.current_product)

		# Create appropriate widget based on field type
		if field_type == 'bool' or bool in field_types:
			entry_widget = ttk.Checkbutton(parent, variable=self.input_vars[field],
									onvalue='True', offvalue='False')
		elif field_options or field in ['Test Type', 'Test Mode', 'Configuration (Mask)', 'Type', 'Domain', 'Core License', 'Content', 'Voltage Type', 'Disable 2 Cores', 'Disable 1 Core']:
			# Use options from field_config first, then fall back to legacy options
			if not field_options:
				options_dict = {
					'Test Mode': self.TEST_MODES,
					'Test Type': self.TEST_TYPES,
					'Voltage Type': self.VOLTAGE_TYPES,
					'Configuration (Mask)': self.MASK_OPTIONS,
					'Type': self.TYPES,
					'Domain': self.DOMAINS,
					'Core License': self.CORE_LICENSE_OPTIONS,
					'Content': self.CONTENT_OPTIONS,
					'Disable 2 Cores': self.DISABLE_2_CORES_OPTIONS,
					'Disable 1 Core': self.DISABLE_1_CORE_OPTIONS
				}
				field_options = options_dict.get(field, [])

			entry_widget = ttk.Combobox(parent, textvariable=self.input_vars[field],
							values=field_options, width=35)
			entry_widget.set(self.input_vars[field].get() or (field_options[0] if field_options else ""))
			if not field_enabled:
				entry_widget.configure(state='disabled')
				label.configure(foreground='#cccccc')
			else:
				entry_widget.configure(state='readonly')

		elif field in ['TTL Folder', 'Scripts File', 'Post Process', 'Linux Path', 'ULX Path', 'Dragon Content Path', 'ShmooFile', 'Merlin Path', 'Fuse File', 'Bios File']:
			# File/folder selection fields
			frame = tk.Frame(parent)
			frame.grid(row=row, column=2, sticky='EW', padx=5, pady=2)

			entry_widget = ttk.Entry(frame, textvariable=self.input_vars[field], width=25)
			entry_widget.pack(side="left", fill="x", expand=True)

			browse_button = ttk.Button(frame, text="...", width=3,
								command=lambda f=field: self.browse_file_folder(f))
			browse_button.pack(side="right", padx=(3, 0))

		else:
			# Regular entry widget
			entry_widget = ttk.Entry(parent, textvariable=self.input_vars[field], width=35)
			if not field_enabled:
				entry_widget.configure(state='disabled')
				label.configure(foreground='#cccccc')

			# Optimized validation binding - only for critical fields
			if field in self.mandatory_fields or field in ['Start', 'End', 'Steps', 'IP Address'] or field_config.get('required', False):
				self.input_vars[field].trace('w', lambda *args, f=field: self.validate_field(f))

		if entry_widget and field not in ['TTL Folder', 'Scripts File', 'Post Process', 'Linux Path', 'ULX Path', 'Dragon Content Path', 'ShmooFile', 'Merlin Path', 'Fuse File', 'Bios File']:
			entry_widget.grid(row=row, column=2, sticky='EW', padx=5, pady=2)

		# Configure grid weights
		parent.grid_columnconfigure(0, weight=0, minsize=150)
		parent.grid_columnconfigure(1, weight=0, minsize=20)
		parent.grid_columnconfigure(2, weight=1, minsize=250)

		# Create tooltip from field_config description
		tooltip_text = field_config.get('description', self.field_descriptions.get(field, "No description available"))
		if field in self.mandatory_fields or field_config.get('required', False):
			tooltip_text += "\n\n* This field is mandatory"

		self.create_tooltip(label, tooltip_text)

		# Store widget reference
		if field not in self.widgets:
			self.widgets[field] = []
			self.widgets[field].append((label, entry_widget, validation_indicator))

	def browse_file_folder(self, field):
		"""Handle file/folder browsing"""
		current_value = self.input_vars[field].get()

		if 'Folder' in field or 'Path' in field:
			# Folder selection
			folder_path = filedialog.askdirectory(
				title=f"Select {field}",
				initialdir=current_value if current_value and os.path.exists(current_value) else "/"
			)
			if folder_path:
				self.input_vars[field].set(folder_path)
		else:
			# File selection
			file_extensions = {
				'Scripts File': [("Script files", "*.py *.bat *.sh"), ("All files", "*.*")],
				'Post Process': [("Script files", "*.py *.bat *.sh"), ("All files", "*.*")],
				'ShmooFile': [("Shmoo files", "*.shmoo *.txt"), ("All files", "*.*")],
			}

			filetypes = file_extensions.get(field, [("All files", "*.*")])

			file_path = filedialog.askopenfilename(
				title=f"Select {field}",
				filetypes=filetypes,
				initialdir=os.path.dirname(current_value) if current_value and os.path.exists(os.path.dirname(current_value)) else "/"
			)
			if file_path:
				self.input_vars[field].set(file_path)

	def on_test_mode_change(self, *args):
		"""Handle Test Mode change to update Configuration (Mask) options"""
		if 'Configuration (Mask)' in self.widgets:
			# Update MASK_OPTIONS based on current Test Mode
			self.MASK_OPTIONS = self._get_field_options('Configuration (Mask)')
			
			# Update the combobox widget with new options
			for label, widget, indicator in self.widgets['Configuration (Mask)']:
				if isinstance(widget, ttk.Combobox):
					current_value = self.input_vars['Configuration (Mask)'].get()
					widget['values'] = self.MASK_OPTIONS
					
					# Clear the field if the current value is not in the new options
					if current_value and current_value not in self.MASK_OPTIONS and self.MASK_OPTIONS:
						self.input_vars['Configuration (Mask)'].set('')
						
					# Set to first option if empty and options are available
					if not current_value and self.MASK_OPTIONS:
						self.input_vars['Configuration (Mask)'].set(self.MASK_OPTIONS[0] if self.MASK_OPTIONS[0] != '' else '')
						
					print(f"[TEST MODE CHANGE] Updated Configuration (Mask) options: {self.MASK_OPTIONS}")
					break
		
		# Validate the field with new options
		self.validate_field('Configuration (Mask)')
	
	def on_test_type_change(self, *args):
		"""Handle test type change to show/hide relevant fields"""
		self.refresh_all_tabs()
		self.validate_all_fields()

	def on_content_change(self, *args):
		"""Handle content type change to show/hide content-specific fields"""
		content_type = self.input_vars.get('Content', tk.StringVar()).get().lower()

		# Update tab highlighting based on content type
		for i, tab_name in enumerate(["Config", "Linux", "EFI/Dragon"]):
			tab_text = tab_name

			if content_type == "linux" and tab_name == "Linux":
				tab_text = "★ Linux"
				self.notebook.tab(i, text=tab_text)
			elif content_type == "dragon" and tab_name == "EFI/Dragon":
				tab_text = "★ EFI/Dragon"
				self.notebook.tab(i, text=tab_text)
			else:
				self.notebook.tab(i, text=tab_name)

		# Update field visibility and validation
		self.update_content_dependent_fields(content_type)
		self.validate_all_fields()

	def update_content_dependent_fields(self, content_type):
		"""Update field visibility and requirements based on content type"""
		# Dynamically build content-specific field lists from field_configs
		linux_fields = []
		dragon_fields = []

		for field_name, field_config in self.field_configs.items():
			condition = field_config.get('condition', {})
			if condition and condition.get('field') == 'Content':
				condition_value = condition.get('value', '').lower()
				if condition_value == 'linux':
					linux_fields.append(field_name)
				elif condition_value in ['dragon', 'efi']:
					dragon_fields.append(field_name)

		# Update field states based on content type
		for field in linux_fields + dragon_fields:
			if field in self.widgets:
				for label, widget, indicator in self.widgets[field]:
					if content_type == "linux" and field in linux_fields:
						# Enable Linux fields
						if hasattr(widget, 'configure'):
							widget.configure(state='normal')
						label.configure(foreground='black')
					elif content_type in ["dragon", "efi"] and field in dragon_fields:
						# Enable Dragon fields
						if hasattr(widget, 'configure'):
							widget.configure(state='normal')
						label.configure(foreground='black')
					else:
						# Disable irrelevant fields
						if hasattr(widget, 'configure'):
							try:
								widget.configure(state='disabled')
							except:
								pass
						label.configure(foreground='gray')

	def validate_field(self, field):
		"""Optimized field validation with debouncing"""
		if field not in self.input_vars or field not in self.validation_indicators:
			return True

		# Add to pending validations
		self.pending_validations.add(field)

		# Cancel existing timer
		if self.validation_timer:
			self.after_cancel(self.validation_timer)

		# Set new timer for batch validation
		self.validation_timer = self.after(300, self._process_pending_validations)

		return True

	def _validate_single_field(self, field):
		"""Actual field validation logic with comprehensive checks"""
		if field not in self.input_vars or field not in self.validation_indicators:
			return True

		value = self.input_vars[field].get().strip()
		indicator = self.validation_indicators[field]
		is_valid = True
		error_message = ""

		try:
			# Skip validation for disabled fields
			content_type = self.input_vars.get('Content', tk.StringVar()).get().lower()
			if self._is_field_disabled(field, content_type):
				indicator.configure(text="", fg="gray")
				return True

			# Define remote/unavailable path fields that shouldn't be validated for existence
			remote_path_fields = ['ULX Path', 'Linux Path', 'Dragon Content Path', 'Linux Content Path',
								'Merlin Path', 'Dragon Content Line']

			# Check if field is mandatory
			if field in self.mandatory_fields and (not value or value == 'None'):
				is_valid = False
				error_message = "Required field"

			# Type-specific validation for non-empty values
			elif value and value != 'None':
				field_types = self.data_types.get(field, [str])

				# Context-aware validation for Start, End, Steps based on Type field
				if field in ['Start', 'End', 'Steps']:
					type_value = self.input_vars.get('Type', tk.StringVar()).get()
					is_valid, error_message = self._validate_numeric_field_by_type(field, value, type_value)

				# Integer validation
				elif int in field_types:
					try:
						int_val = int(float(value))  # Allow float input but convert to int

						# Field-specific integer validation
						if field == 'COM Port' and not (0 <= int_val <= 256):
							is_valid = False
							error_message = "COM Port must be 0-256"
						elif field in ['Test Number', 'Test Time', 'Linux Content Wait Time'] and int_val <= 0:
							is_valid = False
							error_message = "Must be positive"
						elif field == 'Loops' and int_val <= 0:
							is_valid = False
							error_message = "Loops must be positive"
						elif field == 'Check Core' and not (0 <= int_val <= 255):
							is_valid = False
							error_message = "Check Core must be 0-255"
						elif field in ['Frequency IA', 'Frequency CFC'] and int_val < 0:
							is_valid = False
							error_message = "Frequency must be non-negative"
						elif field in ['Frequency IA', 'Frequency CFC'] and int_val > 10000:
							is_valid = False
							error_message = "Frequency seems too high (max 10000 MHz)"

					except ValueError:
						is_valid = False
						error_message = "Must be a valid integer"

				# Float validation
				elif float in field_types:
					try:
						float_val = float(value)

						# Field-specific float validation
						if field in ['Voltage IA', 'Voltage CFC']:
							if not (-2.0 <= float_val <= 2.0):
								is_valid = False
								error_message = "Voltage must be between -2.0V and 2.0V"
						elif field in ['Start', 'End'] and field in self.data_types:
							# Additional range checks for sweep parameters
							type_value = self.input_vars.get('Type', tk.StringVar()).get()
							if type_value.lower() == 'voltage' and not (-2.0 <= float_val <= 2.0):
								is_valid = False
								error_message = f"{field} voltage must be between -2.0V and 2.0V"

					except ValueError:
						is_valid = False
						error_message = "Must be a valid number"

				# Boolean validation (usually handled by checkboxes, but validate string input)
				elif bool in field_types and isinstance(value, str):
					if value.lower() not in ['true', 'false', '1', '0', 'yes', 'no', 'on', 'off']:
						is_valid = False
						error_message = "Must be true/false"

				# String validation with specific field checks
				elif str in field_types:
					# IP Address validation
					if field == 'IP Address':
						if not self._is_valid_ip(value):
							is_valid = False
							error_message = "Invalid IP address format"

					# Path validation for local files/folders
					elif field in ['TTL Folder', 'Scripts File', 'Post Process', 'ShmooFile'] and value:
						is_valid, error_message = self._validate_path_format(field, value)

					# Remote path validation - just check format, not existence
					elif field in remote_path_fields and value:
						if len(value.strip()) < 3:
							is_valid = False
							error_message = "Path too short"
						elif any(char in value for char in ['<', '>', '|', '"', '*', '?']):
							is_valid = False
							error_message = "Path contains invalid characters"

					# Visual ID validation (should be alphanumeric)
					elif field == 'Visual ID':
						if not value.replace('_', '').replace('-', '').isalnum():
							is_valid = False
							error_message = "Visual ID should be alphanumeric (with _ or - allowed)"

					# Bucket validation
					elif field == 'Bucket':
						if not value.isalnum():
							is_valid = False
							error_message = "Bucket should be alphanumeric"

					# Test Name validation
					elif field == 'Test Name':
						if len(value) < 3:
							is_valid = False
							error_message = "Test Name too short (minimum 3 characters)"
						elif any(char in value for char in ['<', '>', '|', '"', '*', '?', '/', '\\']):
							is_valid = False
							error_message = "Test Name contains invalid characters"

					# Pass/Fail String validation
					elif field in ['Pass String', 'Fail String', 'Linux Pass String', 'Linux Fail String']:
						if len(value) < 2:
							is_valid = False
							error_message = "String too short (minimum 2 characters)"

					# Content validation
					elif field == 'Content':
						valid_content = ['Linux', 'Dragon', 'PYSVConsole']
						if value not in valid_content:
							is_valid = False
							error_message = f"Content must be one of: {', '.join(valid_content)}"

					# Voltage Type validation
					elif field == 'Voltage Type':
						valid_voltage_types = ['vbump', 'fixed', 'ppvc']
						if value not in valid_voltage_types:
							is_valid = False
							error_message = f"Voltage Type must be one of: {', '.join(valid_voltage_types)}"

					# Test Mode validation
					elif field == 'Test Mode':
						valid_test_modes = ['Mesh', 'Slice']
						if value not in valid_test_modes:
							is_valid = False
							error_message = f"Test Mode must be one of: {', '.join(valid_test_modes)}"

					# Test Type validation
					elif field == 'Test Type':
						valid_test_types = ['Loops', 'Sweep', 'Shmoo']
						if value not in valid_test_types:
							is_valid = False
							error_message = f"Test Type must be one of: {', '.join(valid_test_types)}"

					# Type validation (for sweep)
					elif field == 'Type':
						valid_types = ['Voltage', 'Frequency']
						if value not in valid_types:
							is_valid = False
							error_message = f"Type must be one of: {', '.join(valid_types)}"

					# Domain validation
					elif field == 'Domain':
						valid_domains = ['CFC', 'IA']
						if value not in valid_domains:
							is_valid = False
							error_message = f"Domain must be one of: {', '.join(valid_domains)}"

					# Hex value validation for Disable 2 Cores
					elif field == 'Disable 2 Cores' and value:
						if not value.startswith('0x'):
							is_valid = False
							error_message = "Must be hex value starting with 0x"
						else:
							try:
								int(value, 16)
							except ValueError:
								is_valid = False
								error_message = "Invalid hex value"

					# VVAR validation (should be hex values)
					elif field.startswith('VVAR') and value:
						if not value.startswith('0x'):
							is_valid = False
							error_message = "VVAR should be hex value starting with 0x"
						else:
							try:
								int(value, 16)
							except ValueError:
								is_valid = False
								error_message = "Invalid hex value"

					# General string length validation
					elif len(value) > 500:  # Reasonable max length
						is_valid = False
						error_message = "Value too long (max 500 characters)"

			# Cross-field validation
			if is_valid and field in ['Start', 'End']:
				is_valid, cross_error = self._validate_start_end_relationship()
				if not is_valid:
					error_message = cross_error

			# Special validation for sweep parameters
			if is_valid and field == 'Steps' and value:
				is_valid, steps_error = self._validate_steps_logic()
				if not is_valid:
					error_message = steps_error

		except Exception as e:
			is_valid = False
			error_message = f"Validation error: {str(e)}"

		# Update indicator efficiently
		try:
			if is_valid:
				indicator.configure(text="✓", fg="green")
			else:
				indicator.configure(text="✗", fg="red")
		except tk.TclError:
			# Fallback for systems that don't support certain configurations
			if is_valid:
				indicator.configure(text="✓", fg="green")
			else:
				indicator.configure(text="✗", fg="red")

		# Update tooltip with error message
		if hasattr(indicator, 'tooltip'):
			try:
				indicator.tooltip.destroy()
			except:
				pass

		if error_message:
			self.create_tooltip(indicator, error_message)

		return is_valid

	def _validate_start_end_relationship(self):
		"""Validate that Start and End values make sense together"""
		try:
			start_str = self.input_vars.get('Start', tk.StringVar()).get().strip()
			end_str = self.input_vars.get('End', tk.StringVar()).get().strip()

			if not start_str or not end_str:
				return True, ""

			type_value = self.input_vars.get('Type', tk.StringVar()).get()

			try:
				if type_value.lower() == 'frequency':
					start_val = int(float(start_str))
					end_val = int(float(end_str))
				else:
					start_val = float(start_str)
					end_val = float(end_str)

				if start_val >= end_val:
					return False, "Start value must be less than End value"

			except ValueError:
				# Individual field validation will catch invalid numbers
				return True, ""

			return True, ""

		except Exception:
			return True, ""  # Don't fail cross-validation on errors

	def _validate_steps_logic(self):
		"""Validate that Steps value makes sense with Start and End"""
		try:
			start_str = self.input_vars.get('Start', tk.StringVar()).get().strip()
			end_str = self.input_vars.get('End', tk.StringVar()).get().strip()
			steps_str = self.input_vars.get('Steps', tk.StringVar()).get().strip()

			if not all([start_str, end_str, steps_str]):
				return True, ""

			type_value = self.input_vars.get('Type', tk.StringVar()).get()

			try:
				if type_value.lower() == 'frequency':
					start_val = int(float(start_str))
					end_val = int(float(end_str))
					steps_val = int(float(steps_str))
				else:
					start_val = float(start_str)
					end_val = float(end_str)
					steps_val = float(steps_str)

				# Check if step size makes sense
				range_val = end_val - start_val
				if steps_val > range_val:
					return False, "Step size larger than total range"

				# Check for reasonable number of iterations
				num_iterations = int(range_val / steps_val) + 1
				if num_iterations > 1000:
					return False, f"Too many iterations ({num_iterations}). Consider larger step size."
				elif num_iterations < 2:
					return False, "Step size too large. Would result in less than 2 iterations."

			except (ValueError, ZeroDivisionError):
				# Individual field validation will catch these
				return True, ""

			return True, ""

		except Exception:
			return True, ""  # Don't fail on errors

	def _process_pending_validations(self):
		"""Process all pending validations in batch"""
		try:
			fields_to_validate = list(self.pending_validations)
			self.pending_validations.clear()
			self.validation_timer = None

			for field in fields_to_validate:
				self._validate_single_field(field)

			# Update overall validation status
			self._update_validation_summary()

		except Exception as e:
			print(f"Validation processing error: {e}")

	def _validate_numeric_field_by_type(self, field, value, type_value):
		"""Enhanced validation for Start, End, Steps fields based on Type field value"""
		is_valid = True
		error_message = ""

		try:
			# Determine expected data type based on Type field
			if type_value.lower() == 'frequency':
				# Frequency type expects integers
				try:
					int_val = int(float(value))  # Allow float input but convert to int
					if field in ['Start', 'End'] and int_val < 0:
						is_valid = False
						error_message = f"{field} must be non-negative integer for Frequency"
					elif field == 'Steps' and int_val <= 0:
						is_valid = False
						error_message = "Steps must be positive integer for Frequency"
					# Additional frequency-specific validation
					elif field in ['Start', 'End'] and int_val > 50:  # Example max frequency
						is_valid = False
						error_message = f"{field} frequency seems too high (max 50 GHz)"
				except ValueError:
					is_valid = False
					error_message = f"{field} must be a valid number for Frequency type"

			elif type_value.lower() == 'voltage':
				# Voltage type expects floats
				try:
					float_val = float(value)
					if field == 'Steps' and float_val <= 0:
						is_valid = False
						error_message = "Steps must be positive number for Voltage"
					# Voltage range validation
					elif field in ['Start', 'End'] and not (-2.0 <= float_val <= 2.0):
						is_valid = False
						error_message = f"{field} voltage must be between -2.0V and 2.0V"
					elif field == 'Steps' and float_val > 1.0:
						is_valid = False
						error_message = "Voltage step size seems too large (max 1.0V)"
				except ValueError:
					is_valid = False
					error_message = f"{field} must be a valid decimal number for Voltage type"

			else:
				# Default validation when Type is not set or unknown
				try:
					float_val = float(value)
					if field == 'Steps' and float_val <= 0:
						is_valid = False
						error_message = "Steps must be positive number"
				except ValueError:
					is_valid = False
					error_message = f"{field} must be a valid number"

		except Exception as e:
			is_valid = False
			error_message = f"Validation error: {str(e)}"

		return is_valid, error_message

	def _validate_path_format(self, field, path):
		"""Simple path format validation - just check for reasonable string format"""
		is_valid = True
		error_message = ""

		try:
			# Basic checks
			if not path or not path.strip():
				return False, "Path cannot be empty"

			path = path.strip()

			# Check minimum length
			if len(path) < 3:
				return False, "Path too short"

			# Check for invalid characters (basic check)
			invalid_chars = ['<', '>', '|', '"', '*', '?']
			for char in invalid_chars:
				if char in path:
					return False, f"Path contains invalid character: {char}"

			# Check for reasonable path format (has some path-like structure)
			if field in ['TTL Folder']:
				# For folders, just check it looks like a path
				if not ('/' in path or '\\' in path or ':' in path):
					return False, "Path should contain path separators (/ or \\)"

			elif field in ['Scripts File', 'Post Process', 'ShmooFile']:
				# For files, check it has some extension or looks like a file
				if not ('.' in path or '/' in path or '\\' in path):
					return False, "File path should contain an extension or path separators"

			# If we get here, it's probably a valid path format
			return True, ""

		except Exception as e:
			return False, f"Path format validation error: {str(e)}"

	def _is_field_disabled(self, field, content_type):
		"""Check if a field should be disabled based on content type"""
		linux_fields = [f for f in self.data_types.keys() if f.startswith('Linux')]
		dragon_fields = [f for f in self.data_types.keys() if f.startswith('Dragon') or f.startswith('ULX') or f.startswith('VVAR') or f.startswith('Merlin')]

		if content_type != "linux" and field in linux_fields:
			return True
		if content_type != "dragon" and field in dragon_fields:
			return True
		return False

	def _is_valid_ip(self, ip):
		"""Validate IP address format"""
		try:
			socket.inet_aton(ip)
			return True
		except socket.error:
			return False

	def on_type_change(self, *args):
		"""Handle Type field change to re-validate Start, End, Steps fields"""
		# Re-validate the numeric fields that depend on Type
		fields_to_revalidate = ['Start', 'End', 'Steps']
		for field in fields_to_revalidate:
			if field in self.input_vars:
				self.validate_field(field)

	def validate_all_fields(self):
		"""Validate all fields and update status - now uses enhanced validation"""
		return self.validate_all_fields_enhanced()

	def _update_validation_summary(self):
		"""Update the overall validation summary and status display"""
		try:
			total_fields = 0
			valid_fields = 0
			error_count = 0
			warning_count = 0
			error_fields = []
			warning_fields = []

			# Count validation results
			for field, indicator in self.validation_indicators.items():
				# Skip disabled fields
				content_type = self.input_vars.get('Content', tk.StringVar()).get().lower()
				if self._is_field_disabled(field, content_type):
					continue

				total_fields += 1
				indicator_text = indicator.cget('text')

				if indicator_text == "✓":
					valid_fields += 1
				elif indicator_text == "✗":
					error_count += 1
					error_fields.append(field)
				elif indicator_text == "⚠":  # Warning indicator (if you want to add warnings)
					warning_count += 1
					warning_fields.append(field)

			# Update status label
			if error_count == 0 and warning_count == 0:
				status_text = f"All fields valid ({valid_fields}/{total_fields})"
				status_color = "green"
				self.status_label.configure(text=status_text, fg=status_color)
				self.validation_count_label.configure(text="", fg="black")
			else:
				if error_count > 0:
					status_text = "Validation errors found"
					status_color = "red"
					count_text = f"{error_count} error{'s' if error_count != 1 else ''}"
					if warning_count > 0:
						count_text += f", {warning_count} warning{'s' if warning_count != 1 else ''}"
				else:
					status_text = "Validation warnings found"
					status_color = "orange"
					count_text = f"{warning_count} warning{'s' if warning_count != 1 else ''}"

				self.status_label.configure(text=status_text, fg=status_color)
				self.validation_count_label.configure(text=count_text, fg=status_color)

			# Update validation progress (optional visual indicator)
			if hasattr(self, 'validation_progress_var'):
				if total_fields > 0:
					progress = (valid_fields / total_fields) * 100
					self.validation_progress_var.set(progress)

			# Store validation state for save operations
			self._validation_state = {
				'total_fields': total_fields,
				'valid_fields': valid_fields,
				'error_count': error_count,
				'warning_count': warning_count,
				'error_fields': error_fields,
				'warning_fields': warning_fields,
				'is_valid': error_count == 0
			}

			# Update save button state based on validation
			self._update_save_button_state()

			# Log validation summary if in debug mode
			if hasattr(self, 'debug') and self.debug:
				self._log_validation_summary()

		except Exception as e:
			print(f"Error updating validation summary: {e}")
			# Fallback to basic status
			self.status_label.configure(text="Validation check failed", fg="red")
			self.validation_count_label.configure(text="Error", fg="red")

	def _update_save_button_state(self):
		"""Update save button states based on validation results"""
		try:
			if not hasattr(self, '_validation_state'):
				return

			validation_state = self._validation_state
			has_errors = validation_state['error_count'] > 0
			has_warnings = validation_state['warning_count'] > 0

			# Find save buttons (they might be in button frames)
			save_buttons = []

			# Look for save-related buttons in the window
			for widget in self.winfo_children():
				if isinstance(widget, tk.Frame):
					for child in widget.winfo_children():
						if isinstance(child, (ttk.Button, tk.Button)):
							button_text = child.cget('text').lower()
							if any(keyword in button_text for keyword in ['save', 'create', 'update']):
								save_buttons.append(child)

			# Update button states and styles
			for button in save_buttons:
				if button.winfo_exists():
					button_text = button.cget('text').lower()

					if has_errors:
						# Enable but warn about errors
						button.configure(state='normal')
						if hasattr(button, 'configure_style'):
							button.configure(style='Warning.TButton')
					elif has_warnings:
						# Enable with warning style
						button.configure(state='normal')
						if hasattr(button, 'configure_style'):
							button.configure(style='Caution.TButton')
					else:
						# Enable with normal style
						button.configure(state='normal')
						if hasattr(button, 'configure_style'):
							button.configure(style='TButton')

		except Exception as e:
			print(f"Error updating save button state: {e}")

	def _log_validation_summary(self):
		"""Log detailed validation summary for debugging"""
		try:
			if not hasattr(self, '_validation_state'):
				return

			state = self._validation_state

			print(f"\n{'='*50}")
			print("VALIDATION SUMMARY")
			print(f"{'='*50}")
			print(f"Total Fields: {state['total_fields']}")
			print(f"Valid Fields: {state['valid_fields']}")
			print(f"Error Count: {state['error_count']}")
			print(f"Warning Count: {state['warning_count']}")
			print(f"Overall Valid: {state['is_valid']}")

			if state['error_fields']:
				print("\nFields with Errors:")
				for field in state['error_fields']:
					indicator = self.validation_indicators.get(field)
					if indicator and hasattr(indicator, 'tooltip_text'):
						print(f"  - {field}: {getattr(indicator, 'tooltip_text', 'Unknown error')}")
					else:
						print(f"  - {field}")

			if state['warning_fields']:
				print("\nFields with Warnings:")
				for field in state['warning_fields']:
					print(f"  - {field}")

			print(f"{'='*50}\n")

		except Exception as e:
			print(f"Error logging validation summary: {e}")

	def get_validation_state(self):
		"""Get current validation state for external use"""
		if hasattr(self, '_validation_state'):
			return self._validation_state.copy()
		else:
			return {
				'total_fields': 0,
				'valid_fields': 0,
				'error_count': 0,
				'warning_count': 0,
				'error_fields': [],
				'warning_fields': [],
				'is_valid': False
			}

	def validate_all_fields_enhanced(self):
		"""Enhanced version of validate_all_fields that uses the summary system"""
		try:
			# Clear pending validations and process all fields
			self.pending_validations.clear()
			if self.validation_timer:
				self.after_cancel(self.validation_timer)
				self.validation_timer = None

			# Validate all fields
			for field in self.input_vars.keys():
				if field in self.validation_indicators:
					self._validate_single_field(field)

			# Update summary
			self._update_validation_summary()

			# Return validation state
			return self.get_validation_state()

		except Exception as e:
			print(f"Error in enhanced validation: {e}")
			return self.get_validation_state()

	def show_validation_report(self):
		"""Show a detailed validation report in a popup window"""
		try:
			validation_state = self.get_validation_state()

			# Create report window
			report_window = tk.Toplevel(self)
			report_window.title("Validation Report")
			report_window.geometry("500x400")
			report_window.transient(self)
			report_window.grab_set()

			# Create main frame
			main_frame = ttk.Frame(report_window)
			main_frame.pack(fill="both", expand=True, padx=10, pady=10)

			# Title
			title_label = ttk.Label(main_frame, text="Field Validation Report",
								font=("Arial", 14, "bold"))
			title_label.pack(pady=(0, 10))

			# Summary frame
			summary_frame = ttk.LabelFrame(main_frame, text="Summary", padding=10)
			summary_frame.pack(fill="x", pady=(0, 10))

			ttk.Label(summary_frame, text=f"Total Fields: {validation_state['total_fields']}").pack(anchor="w")
			ttk.Label(summary_frame, text=f"Valid Fields: {validation_state['valid_fields']}",
					foreground="green").pack(anchor="w")

			if validation_state['error_count'] > 0:
				ttk.Label(summary_frame, text=f"Fields with Errors: {validation_state['error_count']}",
						foreground="red").pack(anchor="w")

			if validation_state['warning_count'] > 0:
				ttk.Label(summary_frame, text=f"Fields with Warnings: {validation_state['warning_count']}",
						foreground="orange").pack(anchor="w")

			# Details frame with scrollbar
			details_frame = ttk.LabelFrame(main_frame, text="Details", padding=5)
			details_frame.pack(fill="both", expand=True)

			# Create text widget with scrollbar
			text_frame = ttk.Frame(details_frame)
			text_frame.pack(fill="both", expand=True)

			text_widget = tk.Text(text_frame, wrap=tk.WORD, width=60, height=15)
			scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
			text_widget.configure(yscrollcommand=scrollbar.set)

			text_widget.pack(side="left", fill="both", expand=True)
			scrollbar.pack(side="right", fill="y")

			# Populate details
			if validation_state['error_fields']:
				text_widget.insert(tk.END, "FIELDS WITH ERRORS:\n", "error_header")
				for field in validation_state['error_fields']:
					indicator = self.validation_indicators.get(field)
					error_msg = "Unknown error"
					if indicator and hasattr(indicator, 'tooltip_text'):
						error_msg = getattr(indicator, 'tooltip_text', 'Unknown error')
					text_widget.insert(tk.END, f"• {field}: {error_msg}\n", "error")
				text_widget.insert(tk.END, "\n")

			if validation_state['warning_fields']:
				text_widget.insert(tk.END, "FIELDS WITH WARNINGS:\n", "warning_header")
				for field in validation_state['warning_fields']:
					text_widget.insert(tk.END, f"• {field}\n", "warning")
				text_widget.insert(tk.END, "\n")

			if validation_state['valid_fields'] > 0:
				text_widget.insert(tk.END, f"VALID FIELDS: {validation_state['valid_fields']} fields passed validation\n", "success")

			# Configure text tags for colors
			text_widget.tag_configure("error_header", foreground="red", font=("Arial", 10, "bold"))
			text_widget.tag_configure("error", foreground="red")
			text_widget.tag_configure("warning_header", foreground="orange", font=("Arial", 10, "bold"))
			text_widget.tag_configure("warning", foreground="orange")
			text_widget.tag_configure("success", foreground="green")

			text_widget.configure(state=tk.DISABLED)

			# Close button
			ttk.Button(main_frame, text="Close",
					command=report_window.destroy).pack(pady=(10, 0))

		except Exception as e:
			print(f"Error showing validation report: {e}")
			messagebox.showerror("Error", f"Failed to show validation report: {e}")

	def refresh_all_tabs(self):
		"""Refresh all tabs to show/hide fields based on current selections"""
		# Clear existing widgets
		for field_widgets in self.widgets.values():
			for widgets_tuple in field_widgets:
				for widget in widgets_tuple:
					if hasattr(widget, 'destroy'):
						widget.destroy()
		self.widgets.clear()
		self.validation_indicators.clear()

		# Recreate all tabs
		for tab_name, tab_data in self.tab_frames.items():
			# Clear the scrollable frame
			for widget in tab_data['scrollable_frame'].winfo_children():
				widget.destroy()

			# Repopulate
			self.populate_tab_fields(tab_name, tab_data['scrollable_frame'])

	def get_available_experiments(self):
		"""Get list of available experiments from parent"""
		try:
			if hasattr(self.parent, 'experiments') and self.parent.experiments:
				return list(self.parent.experiments.keys())
			return []
		except:
			return []

	def show_template_selection_dialog(self, available_experiments):
		"""Show dialog to select template for new experiment"""
		dialog = tk.Toplevel(self)
		dialog.title("Select Template")
		dialog.geometry("500x400")
		dialog.transient(self)
		dialog.grab_set()

		# Center the dialog
		dialog.geometry("+%d+%d" % (self.winfo_rootx() + 50, self.winfo_rooty() + 50))

		result = {"choice": None}

		# Create main frame
		main_frame = tk.Frame(dialog)
		main_frame.pack(fill="both", expand=True, padx=20, pady=20)

		# Title
		title_label = tk.Label(main_frame, text="Choose Template for New Experiment",
							  font=("Arial", 12, "bold"))
		title_label.pack(pady=(0, 15))

		# Selection variable
		selection_var = tk.StringVar(value="current")

		# Option 1: Use current values
		current_frame = tk.Frame(main_frame, relief="ridge", bd=1)
		current_frame.pack(fill="x", pady=5)

		tk.Radiobutton(current_frame, text="Use Current Form Values",
					  variable=selection_var, value="current",
					  font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=5)
		tk.Label(current_frame, text="Create new experiment with the values currently in this form",
				font=("Arial", 9), fg="gray").pack(anchor="w", padx=30, pady=(0, 5))

		# Option 2: Empty experiment
		empty_frame = tk.Frame(main_frame, relief="ridge", bd=1)
		empty_frame.pack(fill="x", pady=5)

		tk.Radiobutton(empty_frame, text="Create Empty Experiment",
					  variable=selection_var, value="empty",
					  font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=5)
		tk.Label(empty_frame, text="Create new experiment with default/empty values",
				font=("Arial", 9), fg="gray").pack(anchor="w", padx=30, pady=(0, 5))

		# Option 3: Use existing experiment as template
		if available_experiments:
			template_frame = tk.Frame(main_frame, relief="ridge", bd=1)
			template_frame.pack(fill="x", pady=5)

			tk.Radiobutton(template_frame, text="Use Existing Experiment as Template",
						  variable=selection_var, value="template",
						  font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=5)
			tk.Label(template_frame, text="Select an existing experiment to copy its configuration",
					font=("Arial", 9), fg="gray").pack(anchor="w", padx=30, pady=(0, 5))

			# Listbox for experiment selection
			listbox_frame = tk.Frame(template_frame)
			listbox_frame.pack(fill="x", padx=30, pady=(0, 10))

			tk.Label(listbox_frame, text="Select experiment:", font=("Arial", 9)).pack(anchor="w")

			listbox = tk.Listbox(listbox_frame, height=6, font=("Arial", 9))
			scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
			listbox.configure(yscrollcommand=scrollbar.set)

			for exp_name in available_experiments:
				listbox.insert(tk.END, exp_name)

			if available_experiments:
				listbox.selection_set(0)  # Select first item by default

			listbox.pack(side="left", fill="both", expand=True)
			scrollbar.pack(side="right", fill="y")

			# Enable/disable listbox based on radio selection
			def on_selection_change():
				if selection_var.get() == "template":
					listbox.configure(state="normal", bg="white")
				else:
					listbox.configure(state="disabled", bg="lightgray")

			selection_var.trace('w', lambda *args: on_selection_change())
			on_selection_change()  # Initial state

		def on_ok():
			choice = selection_var.get()
			if choice == "template" and available_experiments:
				selected_indices = listbox.curselection()
				if selected_indices:
					selected_experiment = available_experiments[selected_indices[0]]
					result["choice"] = selected_experiment
				else:
					messagebox.showwarning("No Selection", "Please select an experiment to use as template.")
					return
			else:
				result["choice"] = choice
			dialog.destroy()

		def on_cancel():
			result["choice"] = None
			dialog.destroy()

		# Buttons
		button_frame = tk.Frame(main_frame)
		button_frame.pack(pady=(20, 0))

		tk.Button(button_frame, text="OK", command=on_ok, width=10,
				 font=("Arial", 10)).pack(side="left", padx=5)
		tk.Button(button_frame, text="Cancel", command=on_cancel, width=10,
				 font=("Arial", 10)).pack(side="left", padx=5)

		# Bind Enter and Escape keys
		dialog.bind('<Return>', lambda e: on_ok())
		dialog.bind('<Escape>', lambda e: on_cancel())

		# Wait for dialog to close
		dialog.wait_window()

		return result["choice"]

	def create_empty_experiment(self):
		"""Create an experiment with default/empty values"""
		new_experiment_data = {}

		for field, field_types in self.data_types.items():
			if field == 'Experiment':
				new_experiment_data[field] = 'Enabled'
			elif field == 'Test Name':
				new_experiment_data[field] = 'New_Experiment'  # Will be overridden
			elif bool in field_types:
				new_experiment_data[field] = False
			elif int in field_types:
				# Set reasonable defaults for some fields
				if field in ['Test Number']:
					new_experiment_data[field] = 1
				elif field in ['Test Time']:
					new_experiment_data[field] = 30
				elif field in ['COM Port']:
					new_experiment_data[field] = 1
				elif field in ['Linux Content Wait Time']:
					new_experiment_data[field] = 10
				else:
					new_experiment_data[field] = 0
			elif float in field_types:
				new_experiment_data[field] = 0.0
			else:
				# Set some reasonable defaults for string fields
				if field in ['Test Mode']:
					new_experiment_data[field] = self.TEST_MODES[0] if self.TEST_MODES else ''
				elif field in ['Test Type']:
					new_experiment_data[field] = self.TEST_TYPES[0] if self.TEST_TYPES else ''
				elif field in ['Content']:
					new_experiment_data[field] = self.CONTENT_OPTIONS[0] if self.CONTENT_OPTIONS else ''
				elif field in ['Voltage Type']:
					new_experiment_data[field] = self.VOLTAGE_TYPES[0] if self.VOLTAGE_TYPES else ''
				elif field in ['Pass String']:
					new_experiment_data[field] = 'Test Complete'
				elif field in ['Fail String']:
					new_experiment_data[field] = 'Test Failed'
				else:
					new_experiment_data[field] = ''

		return new_experiment_data

	def create_from_current_values(self):
		"""Create experiment from current form values"""
		current_values = self.get_values()
		new_experiment_data = {}

		for field, value in current_values.items():
			if value and value != 'None':
				# Convert to appropriate type
				field_types = self.data_types.get(field, [str])
				if bool in field_types:
					new_experiment_data[field] = value.lower() == 'true'
				elif int in field_types:
					try:
						new_experiment_data[field] = int(value)
					except ValueError:
						new_experiment_data[field] = value
				elif float in field_types:
					try:
						new_experiment_data[field] = float(value)
					except ValueError:
						new_experiment_data[field] = value
				else:
					new_experiment_data[field] = value
			else:
				new_experiment_data[field] = None

		return new_experiment_data

	def create_from_template(self, template_name):
		"""Create experiment from existing experiment template"""
		try:
			if hasattr(self.parent, 'experiments') and template_name in self.parent.experiments:
				template_data = self.parent.experiments[template_name].copy()

				# Reset some fields that should be unique for new experiment
				template_data['Test Name'] = 'New_Experiment'  # Will be overridden
				template_data['Experiment'] = 'Enabled'

				# Optionally reset test number to avoid conflicts
				if 'Test Number' in template_data:
					template_data['Test Number'] = template_data.get('Test Number', 1)

				return template_data
			else:
				# Fallback to empty if template not found
				return self.create_empty_experiment()

		except Exception as e:
			print(f"Error creating from template: {e}")
			return self.create_empty_experiment()

	def get_new_experiment_name(self):
		"""Get new experiment name from user with better suggestions"""
		dialog = tk.Toplevel(self)
		dialog.title("New Experiment Name")
		dialog.geometry("450x180")
		dialog.transient(self)
		dialog.grab_set()

		# Center the dialog
		dialog.geometry("+%d+%d" % (self.winfo_rootx() + 50, self.winfo_rooty() + 50))

		result = {"name": None}

		# Create widgets
		main_frame = tk.Frame(dialog)
		main_frame.pack(fill="both", expand=True, padx=20, pady=20)

		tk.Label(main_frame, text="Enter name for new experiment:",
				font=("Arial", 11, "bold")).pack(pady=(0, 10))

		name_var = tk.StringVar()
		entry = tk.Entry(main_frame, textvariable=name_var, width=40, font=("Arial", 10))
		entry.pack(pady=5)
		entry.focus()

		# Generate a smart default name
		base_name = self.data.get('Test Name', 'New_Experiment')
		existing_experiments = self.get_available_experiments()

		# Find a unique name
		counter = 1
		suggested_name = f"{base_name}_Copy"
		while suggested_name in existing_experiments:
			counter += 1
			suggested_name = f"{base_name}_Copy_{counter}"

		name_var.set(suggested_name)
		entry.select_range(0, tk.END)

		# Add validation label
		validation_label = tk.Label(main_frame, text="", font=("Arial", 9))
		validation_label.pack(pady=(5, 0))

		def validate_name():
			name = name_var.get().strip()
			if not name:
				validation_label.configure(text="Name cannot be empty", fg="red")
				return False
			elif name in existing_experiments:
				validation_label.configure(text="Name already exists", fg="red")
				return False
			else:
				validation_label.configure(text="✓ Name is available", fg="green")
				return True

		def on_name_change(*args):
			validate_name()

		name_var.trace('w', on_name_change)
		validate_name()  # Initial validation

		def on_ok():
			if validate_name():
				result["name"] = name_var.get().strip()
				dialog.destroy()

		def on_cancel():
			dialog.destroy()

		# Buttons
		button_frame = tk.Frame(main_frame)
		button_frame.pack(pady=(15, 0))

		tk.Button(button_frame, text="Create", command=on_ok, width=10,
				 font=("Arial", 10)).pack(side="left", padx=5)
		tk.Button(button_frame, text="Cancel", command=on_cancel, width=10,
				 font=("Arial", 10)).pack(side="left", padx=5)

		# Bind Enter key
		entry.bind('<Return>', lambda e: on_ok())
		dialog.bind('<Escape>', lambda e: on_cancel())

		# Wait for dialog to close
		dialog.wait_window()

		return result["name"]

	def reset_to_defaults(self):
		"""Reset fields to default values for new experiment"""
		if messagebox.askyesno("Reset to Defaults", "Are you sure you want to reset all fields to default values?"):
			for field, field_types in self.data_types.items():
				if field == 'Experiment':
					self.input_vars[field].set('Enabled')  # New experiments should be enabled
				elif field == 'Test Name':
					self.input_vars[field].set('New_Experiment')  # Default name
				elif bool in field_types:
					self.input_vars[field].set('False')
				elif int in field_types or float in field_types:
					# Set reasonable defaults for some fields
					if field in ['Test Number']:
						self.input_vars[field].set('1')
					elif field in ['Test Time']:
						self.input_vars[field].set('30')
					elif field in ['COM Port']:
						self.input_vars[field].set('1')
					else:
						self.input_vars[field].set('0')
				else:
					self.input_vars[field].set('')

			self.validate_all_fields()

	def import_from_file(self):
		"""Import configuration from JSON file"""
		file_path = filedialog.askopenfilename(
			title="Import Configuration",
			filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
		)

		if file_path:
			try:
				with open(file_path, 'r') as f:
					imported_data = json.load(f)

				# Update fields with imported data
				for field, value in imported_data.items():
					if field in self.input_vars:
						self.input_vars[field].set(str(value) if value is not None else '')

				self.validate_all_fields()
				messagebox.showinfo("Import Successful", "Configuration imported successfully!")

			except Exception as e:
				messagebox.showerror("Import Error", f"Failed to import configuration: {str(e)}")

	def export_to_file(self):
		"""Export current configuration to JSON file"""
		file_path = filedialog.asksaveasfilename(
			title="Export Configuration",
			defaultextension=".json",
			filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
		)

		if file_path:
			try:
				export_data = {}
				for field, var in self.input_vars.items():
					value = var.get()
					if value and value != 'None':
						# Convert to appropriate type
						field_types = self.data_types.get(field, [str])
						if bool in field_types:
							export_data[field] = value.lower() == 'true'
						elif int in field_types:
							try:
								export_data[field] = int(value)
							except ValueError:
								export_data[field] = value
						elif float in field_types:
							try:
								export_data[field] = float(value)
							except ValueError:
								export_data[field] = value
						else:
							export_data[field] = value

				with open(file_path, 'w') as f:
					json.dump(export_data, f, indent=4)

				messagebox.showinfo("Export Successful", "Configuration exported successfully!")

			except Exception as e:
				messagebox.showerror("Export Error", f"Failed to export configuration: {str(e)}")

	def create_tooltip(self, widget, text):
		"""Create enhanced tooltip with word wrapping"""
		def on_enter(event):
			x = event.x_root + 10
			y = event.y_root + 10

			# Create tooltip with better formatting
			tooltip = tk.Toplevel(self)
			tooltip.wm_overrideredirect(True)
			tooltip.wm_geometry(f"+{x}+{y}")

			label = tk.Label(tooltip, text=text, background="lightyellow",
						   relief="solid", borderwidth=1, wraplength=400,
						   justify="left", padx=5, pady=3)
			label.pack()

			widget.tooltip = tooltip

		def on_leave(event):
			if hasattr(widget, 'tooltip'):
				widget.tooltip.destroy()
				del widget.tooltip

		widget.bind("<Enter>", on_enter)
		widget.bind("<Leave>", on_leave)

	def save_changes(self):
		"""Save changes with comprehensive validation and change logging"""
		try:
			# Store original data for comparison
			original_data = dict(self.data)

			# Validate all fields first
			self.validate_all_fields()

			# Check for validation errors
			error_count = sum(1 for field in self.validation_indicators
							if self.validation_indicators[field].cget('text') == '✗')

			if error_count > 0:
				if not messagebox.askyesno("Validation Errors",
										f"There are {error_count} validation errors. Do you want to save anyway?"):
					return

			# Get current values and convert types
			current_values = self.get_values()
			updated_data = self._convert_values_to_proper_types(current_values)

			# Find experiment name for logging
			experiment_name = updated_data.get('Test Name', self.data.get('Test Name', 'Unknown'))

			# Log changes to console
			self._log_configuration_changes(original_data, updated_data, "SAVE_CHANGES", experiment_name)

			# Update the data
			self.data.update(updated_data)

			# Call update callback
			self.update_callback(self.data)

			# Show success message
			messagebox.showinfo("Success", f"Changes saved successfully for '{experiment_name}'")

			self.destroy()

		except Exception as e:
			error_msg = f"Failed to save changes: {str(e)}"
			print(f"ERROR: {error_msg}")
			messagebox.showerror("Error", error_msg)

	def get_values(self):
		"""Get all current values from input variables"""
		return {field: (var.get().strip() if var.get() else None)
			for field, var in self.input_vars.items()}

	def _log_configuration_changes(self, original_data, new_data, operation_type, experiment_name):
		"""Log configuration changes to console with detailed comparison"""
		print(f"\n{'='*60}")
		print(f"CONFIGURATION CHANGES - {operation_type.upper()}")
		print(f"Experiment: {experiment_name}")
		print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
		print(f"{'='*60}")

		if operation_type == "CREATE_NEW":
			print("NEW EXPERIMENT CREATED:")
			for key, value in new_data.items():
				if value not in [None, "", "None"]:
					print(f"  + {key}: {value}")
		else:
			# Compare original vs new data
			changes_found = False

			# Check for modified fields
			for key in set(list(original_data.keys()) + list(new_data.keys())):
				old_value = original_data.get(key)
				new_value = new_data.get(key)

				# Normalize values for comparison
				old_normalized = self._normalize_value_for_comparison(old_value)
				new_normalized = self._normalize_value_for_comparison(new_value)

				if old_normalized != new_normalized:
					changes_found = True
					if key not in original_data:
						print(f"  + ADDED {key}: {new_value}")
					elif key not in new_data:
						print(f"  - REMOVED {key}: {old_value}")
					else:
						print(f"  ~ CHANGED {key}: '{old_value}' → '{new_value}'")

			if not changes_found:
				print("  No changes detected")

		print(f"{'='*60}\n")

	def _normalize_value_for_comparison(self, value):
		"""Normalize values for consistent comparison"""
		if value is None:
			return ""
		if isinstance(value, bool):
			return str(value).lower()
		if isinstance(value, (int, float)):
			return str(value)
		return str(value).strip()

	def on_closing(self):
		"""Handle window closing event with unsaved changes check"""
		try:

			# Remove from tracking
			if self in EditExperimentWindow._open_windows:
				EditExperimentWindow._open_windows.remove(self)

			if self.mode == "edit":
				# Check if there are unsaved changes
				current_values = self.get_values()
				has_changes = False

				for field, current_value in current_values.items():
					original_value = str(self.data.get(field, '')) if self.data.get(field) is not None else ''
					if current_value != original_value:
						has_changes = True
						break

				if has_changes:
					result = messagebox.askyesnocancel("Unsaved Changes",
													 "You have unsaved changes. Do you want to save before closing?")
					if result is True:  # Yes, save
						self.save_changes()
						return
					elif result is None:  # Cancel
						return
					# If No, continue with closing

			# Clean up resources
			for var in self.input_vars.values():
				try:
					var.set("")
				except:
					pass

			self.widgets.clear()
			self.tab_frames.clear()
			self.validation_indicators.clear()
			self.destroy()

		except Exception as e:
			print(f"Error during EditExperimentWindow cleanup: {e}")
			try:
				self.destroy()
			except:
				pass

class DebugFrameworkControlPanel:

	# ==================== CORE INITIALIZATION ====================

	def __init__(self, root, Framework, utils, manager):
		self.root = root
		self.root.title("Debug Framework Control Panel")

		# Configure grid for header (matching AutomationDesigner)
		self.root.rowconfigure(0, weight=0)
		self.root.rowconfigure(1, weight=1)
		self.root.columnconfigure(0, weight=1)

		# Initialize MainThreadHandler and ThreadIntegration
		self.main_thread_handler = fs.MainThreadHandler(self.root, self)
		#self.thread_integration = ControlPanelThreadIntegration(self)

		# Remove self.Framework completely!
		# Instead, use instance manager
		self.framework_manager = None
		self.framework_api = None
		self.Framework_utils = None
		self.execution_state = execution_state

		# CRITICAL: Initialize Framework with queue-based reporter
		self.Framework = Framework
		if Framework:
			self.framework_manager = manager(Framework)
			self.Framework_utils = utils
			# Extract product from FrameworkUtils (which reads from dpm.product_str())
			try:
				self.product = utils.get_selected_product().upper()
				print(f"[CONTROL PANEL] Product from FrameworkUtils: {self.product}")
			except Exception as e:
				print(f"[CONTROL PANEL] Failed to get product from utils: {e}")
				self.product = 'GNR'  # Default to GNR if call fails
		else:
			self.product = 'GNR'  # Default to GNR if no Framework

		# Log Framework and Product status
		framework_status = "loaded" if Framework else "NOT loaded"
		print(f"[CONTROL PANEL] Framework: {framework_status} | Product: {self.product}")

		# CRITICAL: Store only primitive data, no Tkinter variables in threads
		self.experiments_data = {}  # Use dict instead of Tkinter variables
		self.experiment_states = {}  # Track enabled/disabled state

		# ADD: Thread-safe data storage
		self.thread_safe_experiment_states = {}  # Primitive data only for threads
		self.current_framework_instance_id = None
		self.registered_tkinter_variables = []  # Track variables for cleanup

		# Command queue for thread communication
		self.command_queue = queue.Queue()
		self.status_queue = queue.Queue()

		# Thread management
		self.framework_thread = None
		self.thread_active = False

		# Set minimum window size and make it resizable
		self.root.minsize(800, 600)  # Minimum size to accommodate both panels
		#self.root.geometry("1400x800")  # Default size

		# Configure ttk styles for better appearance
		self.setup_styles()

		self.experiments = {}
		self.experiment_frames = []
		self.hold_active = False
		self.cancel_requested = threading.Event()
		self.exception_queue = queue.Queue()

		self.S2T_CONFIG = self.Framework_utils.system_2_tester_default() if Framework != None else S2T_CONFIGURATION
		self.mask_dict = {}
		self.mask_dict['Default'] = None


		# Enables Cancellation Check on S2T side
		self.s2t_cancel_enabled = True
		self._cleanup_in_progress = False
		# Framework execution state tracking
		self.framework_execution_active = False
		self.current_framework_thread = None
		self.current_experiment_data = {}
		self.upload_unit_data = False

		# Progress tracking variables
		self.current_experiment_name = None
		self.current_experiment_index = 0
		self.total_experiments = 0
		self.current_iteration = 0
		self.total_iterations_in_experiment = 0
		self.current_iteration_progress = 0.0
		self.strategy_progress = 0.0

		# Initialize timing estimates
		self.avg_iterations_per_experiment = 10  # Default
		self.start_time = None
		self.last_iteration_time = None


		self.create_widgets()

		# Auto-size after widgets are created
		self.root.after(100, self.auto_size_window)

		# Log Framework and Product status after widgets are created
		framework_status = "loaded" if Framework else "NOT loaded"
		self.log_status(f"Framework: {framework_status} | Product: {self.product}", level="info")

		# Keep track of active threads
		self.active_threads = []		# Enhanced status management
		#self._status_callback_enabled = True
		#self._original_framework_callback = None

		#else:
		#	self.framework_manager = None
		#	self.Framework = None
			#self.execution_state = execution_state

		# Cleanup handling
		self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

	def setup_styles(self):
		"""Configure ttk styles matching PPV AutomationDesigner theme"""
		style = ttk.Style()

		# Use clam theme for modern flat design (matching AutomationDesigner)
		style.theme_use('clam')

		# Overall progress bar style
		style.configure("Overall.Horizontal.TProgressbar",
					troughcolor='#404040',
					background='#2196F3',  # Blue for overall
					lightcolor='#2196F3',
					darkcolor='#1976D2',
					borderwidth=1,
					relief='flat')

		# Current iteration progress bar style
		style.configure("Iteration.Horizontal.TProgressbar",
					troughcolor='#404040',
					background='#4CAF50',  # Green for current iteration
					lightcolor='#4CAF50',
					darkcolor='#388E3C',
					borderwidth=1,
					relief='flat')

		# Style variations for different states
		style.configure("Overall.Running.Horizontal.TProgressbar",
					background='#2196F3',
					lightcolor='#2196F3',
					darkcolor='#1976D2')

		style.configure("Overall.Warning.Horizontal.TProgressbar",
					background='#FF9800',
					lightcolor='#FF9800',
					darkcolor='#F57C00')

		style.configure("Overall.Error.Horizontal.TProgressbar",
					background='#F44336',
					lightcolor='#F44336',
					darkcolor='#D32F2F')

		style.configure("Iteration.Running.Horizontal.TProgressbar",
					background='#4CAF50',
					lightcolor='#4CAF50',
					darkcolor='#388E3C')

		style.configure("Iteration.Boot.Horizontal.TProgressbar",
					background='#FF9800',
					lightcolor='#FF9800',
					darkcolor='#F57C00')

		style.configure("Iteration.Error.Horizontal.TProgressbar",
					background='#F44336',
					lightcolor='#F44336',
					darkcolor='#D32F2F')

		# Custom button styles
		style.configure("Hold.TButton", foreground="black")
		style.configure("HoldActive.TButton", foreground="orange", font=("Arial", 9, "bold"))
		style.configure("Continue.TButton", foreground="blue", font=("Arial", 9, "bold"))
		style.configure("End.TButton", foreground="red", font=("Arial", 9, "bold"))
		style.configure("EndActive.TButton", foreground="white", background="red", font=("Arial", 9, "bold"))

	def create_widgets(self):
		# Header frame with teal color accent (matching AutomationDesigner)
		header_frame = tk.Frame(self.root, bg='#1abc9c', height=12)
		header_frame.grid(row=0, column=0, sticky="ew")
		header_frame.grid_propagate(False)

		# Create main horizontal container using ttk.PanedWindow (placed at row=1)
		self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
		self.main_paned.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

		# Left side - Main UI (experiments, controls, etc.)
		self.left_frame = ttk.Frame(self.main_paned)
		self.main_paned.add(self.left_frame, weight=3)  # Gets 75% of space

		# Right side - Status panel
		self.right_frame = ttk.Frame(self.main_paned)
		self.main_paned.add(self.right_frame, weight=1)  # Gets 25% of space

		# Create left side content
		self.create_left_panel()

		# Create right side status panel
		self.create_right_status_panel()

	def create_left_panel(self):
		"""Create the main UI elements on the left side"""
		# Main Title
		title_frame = ttk.Frame(self.left_frame)
		title_frame.pack(fill=tk.X, padx=10, pady=5)

		# Product badge - modern framed design on the left
		product_frame = tk.Frame(title_frame, bg="#1abc9c", relief=tk.FLAT, borderwidth=0)
		product_frame.pack(side=tk.LEFT, padx=(0, 15))

		# Inner frame for padding
		product_inner = tk.Frame(product_frame, bg="#1abc9c")
		product_inner.pack(padx=8, pady=4)

		product_label = tk.Label(product_inner, text=self.product,
							   font=("Arial", 14, "bold"),
							   bg="#1abc9c", fg="white")
		product_label.pack()

		# Main title
		ttk.Label(title_frame, text="Debug Framework Control Panel", font=("Arial", 16)).pack(side=tk.LEFT)

		# Status Label
		self.status_label = tk.Label(title_frame, padx=5, width=15, text=" Ready ",
								   bg="white", fg="black", font=("Arial", 12),
								   relief=tk.GROOVE, borderwidth=2)
		self.status_label.pack(side=tk.RIGHT)

		# Control buttons frame
		buttons_frame = ttk.Frame(title_frame)
		buttons_frame.pack(side=tk.RIGHT, padx=5)

		# Power Control Button
		self.power_control_button = ttk.Button(buttons_frame, text="Power",
											 command=self.open_power_control_window)
		self.power_control_button.pack(side=tk.RIGHT, padx=2)

		# IPC Control Button
		self.ipc_control_button = ttk.Button(buttons_frame, text="IPC",
										   command=self.check_ipc)
		self.ipc_control_button.pack(side=tk.RIGHT, padx=2)

		# Settings Button
		self.settings_button = ttk.Button(buttons_frame, text="⚙",
										command=self.open_settings_window)
		self.settings_button.pack(side=tk.RIGHT, padx=2)

		# Add test button for animation verification (remove in production)
		if debug:
			if hasattr(self, 'settings_button'):  # Add next to settings button
				test_button = ttk.Button(buttons_frame, text="Test",
									command=self.verify_animations)
				test_button.pack(side=tk.RIGHT, padx=2)

		# Add emergency cleanup button (optional)
		#self.emergency_button = ttk.Button(
		#	buttons_frame,
		#	text="[CRIT] Emergency",
		#	command=self.thread_integration.emergency_cleanup
		#)
		#self.emergency_button.pack(side=tk.RIGHT, padx=2)

		# File selection frame
		self.file_frame = ttk.Frame(self.left_frame)
		self.file_frame.pack(fill=tk.X, padx=10, pady=5)

		ttk.Label(self.file_frame, text="Experiments:", width=12).pack(side=tk.LEFT)
		self.file_entry = ttk.Entry(self.file_frame)
		self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
		ttk.Button(self.file_frame, text="Browse",
				  command=self.load_experiments_file).pack(side=tk.LEFT)

		# Separator
		ttk.Separator(self.left_frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)

		# Experiment container with scrollbar
		self.create_experiment_container()

		# Options frame
		self.create_options_frame()

		# Control buttons frame
		self.create_control_buttons()

	def create_right_status_panel(self):
		"""Create the right-side status panel with enhanced progress bar"""
		# Create the shared status panel
		self.status_panel = StatusExecutionPanel(
			parent_frame=self.right_frame,
			dual_progress=True,
			show_experiment_stats=True,
			logger_callback=self._external_log_callback
		)

		# Store references to important components for backward compatibility
		self.status_log = self.status_panel.status_log
		self.overall_progress_var = self.status_panel.overall_progress_var
		self.iteration_progress_var = self.status_panel.iteration_progress_var
		self.overall_progress_bar = self.status_panel.overall_progress_bar
		self.iteration_progress_bar = self.status_panel.iteration_progress_bar

		# Store label references
		self.overall_percentage_label = self.status_panel.overall_percentage_label
		self.iteration_percentage_label = self.status_panel.iteration_percentage_label
		self.overall_experiment_label = self.status_panel.overall_experiment_label
		self.iteration_progress_label = self.status_panel.iteration_progress_label
		self.overall_eta_label = self.status_panel.overall_eta_label
		self.iteration_speed_label = self.status_panel.iteration_speed_label
		self.iteration_status_label = self.status_panel.iteration_status_label
		self.phase_label = self.status_panel.phase_label
		self.strategy_label = self.status_panel.strategy_label
		self.test_name_label = self.status_panel.test_name_label
		self.pass_count_label = self.status_panel.pass_count_label
		self.fail_count_label = self.status_panel.fail_count_label
		self.skip_count_label = self.status_panel.skip_count_label
		self.elapsed_time_label = self.status_panel.elapsed_time_label
		self.auto_scroll_var = self.status_panel.auto_scroll_var

		self.start_time = self.status_panel.start_time
		self.last_iteration_time =  self.status_panel.last_iteration_time
		self.pass_count =  self.status_panel.pass_count
		self.fail_count =  self.status_panel.fail_count
		self.skip_count =  self.status_panel.skip_count

	#Remove once validated
	def old_right_side(self):
		# Main container for right panel
		main_container = ttk.Frame(self.right_frame)
		main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

		# Title
		title_label = ttk.Label(main_container, text="Execution Status",
							   font=("Arial", 12, "bold"))
		title_label.pack(pady=(0, 10))

		# Progress section
		progress_frame = ttk.LabelFrame(main_container, text="Execution Progress", padding=10)
		progress_frame.pack(fill=tk.X, pady=(0, 10))

		# Strategy and test info
		self.strategy_label = ttk.Label(progress_frame, text="Strategy: Ready")
		self.strategy_label.pack(anchor="w")

		self.test_name_label = ttk.Label(progress_frame, text="Test: None",
										foreground="blue")
		self.test_name_label.pack(anchor="w")

		# === OVERALL PROGRESS BAR ===
		overall_frame = ttk.Frame(progress_frame)
		overall_frame.pack(fill=tk.X, pady=(10, 5))

		# Overall progress info
		overall_info = ttk.Frame(overall_frame)
		overall_info.pack(fill=tk.X, pady=(0, 2))

		ttk.Label(overall_info, text="Overall Progress:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)

		self.overall_percentage_label = ttk.Label(overall_info, text="0%",
												font=("Arial", 10, "bold"))
		self.overall_percentage_label.pack(side=tk.LEFT, padx=(10, 0))

		self.overall_experiment_label = ttk.Label(overall_info, text="(0/0 experiments)")
		self.overall_experiment_label.pack(side=tk.LEFT, padx=(5, 0))

		self.overall_eta_label = ttk.Label(overall_info, text="")
		self.overall_eta_label.pack(side=tk.RIGHT)

		# Overall progress bar
		self.overall_progress_var = tk.DoubleVar()
		self.overall_progress_bar = ttk.Progressbar(overall_frame, variable=self.overall_progress_var,
												maximum=100, style="Overall.Horizontal.TProgressbar")
		self.overall_progress_bar.pack(fill=tk.X, pady=(0, 5))

		# === CURRENT ITERATION PROGRESS BAR ===
		iteration_frame = ttk.Frame(progress_frame)
		iteration_frame.pack(fill=tk.X, pady=(5, 5))

		# Current iteration info
		iteration_info = ttk.Frame(iteration_frame)
		iteration_info.pack(fill=tk.X, pady=(0, 2))

		ttk.Label(iteration_info, text="Current Iteration:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)

		self.iteration_percentage_label = ttk.Label(iteration_info, text="0%",
												font=("Arial", 10, "bold"))
		self.iteration_percentage_label.pack(side=tk.LEFT, padx=(10, 0))

		self.iteration_progress_label = ttk.Label(iteration_info, text="(0/0)")
		self.iteration_progress_label.pack(side=tk.LEFT, padx=(5, 0))

		self.iteration_speed_label = ttk.Label(iteration_info, text="")
		self.iteration_speed_label.pack(side=tk.RIGHT)

		# Current iteration progress bar
		self.iteration_progress_var = tk.DoubleVar()
		self.iteration_progress_bar = ttk.Progressbar(iteration_frame, variable=self.iteration_progress_var,
													maximum=100, style="Iteration.Horizontal.TProgressbar")
		self.iteration_progress_bar.pack(fill=tk.X, pady=(0, 5))

		# Status and phase info
		status_info = ttk.Frame(progress_frame)
		status_info.pack(fill=tk.X)

		self.iteration_status_label = ttk.Label(status_info, text="Status: Idle")
		self.iteration_status_label.pack(side=tk.LEFT)

		self.phase_label = ttk.Label(status_info, text="", foreground="orange")
		self.phase_label.pack(side=tk.RIGHT)

		# Statistics section (rest remains the same)
		stats_frame = ttk.LabelFrame(main_container, text="Statistics", padding=10)
		stats_frame.pack(fill=tk.X, pady=(0, 10))

		# Counters
		counters = ttk.Frame(stats_frame)
		counters.pack(fill=tk.X)

		self.pass_count_label = ttk.Label(counters, text="✓ Pass: 0", foreground="green")
		self.pass_count_label.pack(side=tk.LEFT)

		self.fail_count_label = ttk.Label(counters, text="✗ Fail: 0", foreground="red")
		self.fail_count_label.pack(side=tk.LEFT, padx=(10, 0))

		self.skip_count_label = ttk.Label(counters, text="⊘ Skip: 0", foreground="orange")
		self.skip_count_label.pack(side=tk.LEFT, padx=(10, 0))

		self.elapsed_time_label = ttk.Label(counters, text="Time: 00:00")
		self.elapsed_time_label.pack(side=tk.RIGHT)

		# Status Log section
		log_frame = ttk.LabelFrame(main_container, text="Status Log", padding=5)
		log_frame.pack(fill=tk.BOTH, expand=True)

		# Log container
		log_container = ttk.Frame(log_frame)
		log_container.pack(fill=tk.BOTH, expand=True)

		# Text widget with scrollbar
		self.status_log = tk.Text(log_container, bg="black", fg="white",
								 font=("Consolas", 10), wrap=tk.WORD,
								 state=tk.DISABLED, width=45, height=15,
								 insertbackground="white",  # Cursor color
							 	 selectbackground="darkblue",  # Selection background
							 	 selectforeground="white")  # Selection text color)

		log_scrollbar = ttk.Scrollbar(log_container, orient="vertical",
									 command=self.status_log.yview)
		self.status_log.configure(yscrollcommand=log_scrollbar.set)

		self.status_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

		# Log controls
		log_controls = ttk.Frame(log_frame)
		log_controls.pack(fill=tk.X, pady=(5, 0))

		ttk.Button(log_controls, text="Clear",
				  command=self.clear_status_log).pack(side=tk.LEFT)
		ttk.Button(log_controls, text="Save",
				  command=self.save_status_log).pack(side=tk.LEFT, padx=(5, 0))

		self.auto_scroll_var = tk.BooleanVar(value=True)
		ttk.Checkbutton(log_controls, text="Auto-scroll",
					   variable=self.auto_scroll_var).pack(side=tk.RIGHT)

		# Initialize tracking variables
		self.start_time = None
		self.last_iteration_time = None
		self.pass_count = 0
		self.fail_count = 0
		self.skip_count = 0

		# Add initial messages
		self.log_status("Framework Control Panel initialized")
		self.log_status("Ready to load experiments...")

	def create_experiment_container(self):
		"""Create scrollable container for experiments"""
		# Container frame - remove white background
		container_frame = ttk.Frame(self.left_frame)
		container_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

		# Create canvas and scrollbar - remove highlightthickness and set proper background
		canvas = tk.Canvas(container_frame, highlightthickness=0,
						bg=self.root.cget('bg'))  # Match root background
		v_scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
		h_scrollbar = ttk.Scrollbar(container_frame, orient="horizontal", command=canvas.xview)

		# Scrollable frame - use ttk.Frame for consistent theming
		self.experiment_container = ttk.Frame(canvas)

		# Configure scrolling
		self.experiment_container.bind(
			"<Configure>",
			lambda e: self._update_scroll_region(canvas)
		)

		# Bind canvas resize to update scroll region
		canvas.bind(
			"<Configure>",
			lambda e: self._update_canvas_scroll_region(canvas)
		)

		canvas_window = canvas.create_window((0, 0), window=self.experiment_container, anchor="nw")
		canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

		# Pack scrollbars and canvas
		canvas.pack(side="left", fill="both", expand=True)
		v_scrollbar.pack(side="right", fill="y")
		# Only show horizontal scrollbar if needed

		# Bind mousewheel to canvas
		def _on_mousewheel(event):
			canvas.yview_scroll(int(-1*(event.delta/120)), "units")

		def _bind_mousewheel(event):
			canvas.bind_all("<MouseWheel>", _on_mousewheel)

		def _unbind_mousewheel(event):
			canvas.unbind_all("<MouseWheel>")

		#canvas.bind('<Enter>', _bind_mousewheel)
		#canvas.bind('<Leave>', _unbind_mousewheel)

		# Store references for later use
		self.experiment_canvas = canvas
		self.experiment_canvas_window = canvas_window

	def create_options_frame(self):
		"""Create options checkboxes"""
		self.options_frame = ttk.Frame(self.left_frame)
		self.options_frame.pack(fill=tk.X, padx=10, pady=5)

		# Right side buttons
		buttons_right = ttk.Frame(self.options_frame)
		buttons_right.pack(side=tk.RIGHT)

		ttk.Button(buttons_right, text="Test TTL",
				  command=self.test_ttl).pack(side=tk.RIGHT, padx=5)
		ttk.Button(buttons_right, text="Mask",
				  command=self.open_mask_management).pack(side=tk.RIGHT, padx=5)

		# Left side checkboxes
		self.stop_on_fail_var = tk.BooleanVar(value=False)
		ttk.Checkbutton(self.options_frame, text="Stop on Fail",
					   variable=self.stop_on_fail_var).pack(side=tk.LEFT, padx=5)

		self.check_unit_data_var = tk.BooleanVar(value=False)
		ttk.Checkbutton(self.options_frame, text="Check Unit Data",
					   variable=self.check_unit_data_var).pack(side=tk.LEFT, padx=5)

		self.upload_unit_data_var = tk.BooleanVar(value=True)
		ttk.Checkbutton(self.options_frame, text="Upload Data (DB)",
					   variable=self.upload_unit_data_var).pack(side=tk.LEFT, padx=5)

	def create_control_buttons(self):
		"""Create main control buttons"""
		self.control_frame = ttk.Frame(self.left_frame)
		self.control_frame.pack(fill=tk.X, padx=10, pady=10)

		# Left side
		self.saveas_button = ttk.Button(self.control_frame, text="Save JSON",
									   command=self.save_config, state=tk.DISABLED)
		self.saveas_button.pack(side=tk.LEFT)

		# Add Experiment button
		self.add_experiment_button = ttk.Button(self.control_frame, text="Add Experiment",
											command=self.add_new_experiment)
		self.add_experiment_button.pack(side=tk.LEFT)

		# Right side
		button_frame = ttk.Frame(self.control_frame)
		button_frame.pack(side=tk.RIGHT)

		self.run_button = ttk.Button(button_frame, text="Run",
								   command=self.start_tests_thread)
		self.run_button.pack(side=tk.RIGHT, padx=2)

		self.hold_button = ttk.Button(button_frame, text="Hold",
									command=self.toggle_framework_hold,
									state=tk.DISABLED)
		self.hold_button.pack(side=tk.RIGHT, padx=2)

		self.end_button = ttk.Button(button_frame, text="End",
								command=self.end_current_experiment,
								state=tk.DISABLED)
		self.end_button.pack(side=tk.RIGHT, padx=2)

		self.cancel_button = ttk.Button(button_frame, text="Cancel",
									  command=self.cancel_tests,
									  state=tk.DISABLED)
		self.cancel_button.pack(side=tk.RIGHT, padx=2)

	# ==================== THREAD MANAGEMENT & EXECUTION ====================

	def start_tests_thread(self):
		"""Start tests with proper thread isolation and command system"""
		if self.thread_active:
			self.log_status("Tests already running")
			return

		# Debug button states before start
		self.debug_button_states("BEFORE START")

		# CRITICAL: Reset button states FIRST before any other operations
		self._reset_all_button_states()

		# Small delay to ensure button reset is processed
		self.root.update_idletasks()

		# EDIT: Add framework cleanup before starting
		self._cleanup_previous_framework()

		# Clean up previous run statuses
		self._cleanup_experiment_statuses()

		# CRITICAL: Reset ALL counters and progress tracking
		self._reset_execution_counters()

		# Reset progress bars
		self.overall_progress_var.set(0)
		self.iteration_progress_var.set(0)
		self.overall_percentage_label.configure(text="0%")
		self.iteration_percentage_label.configure(text="0%")

		self.execution_state.clear_all_commands()

		# EDIT: Create fresh Framework instance with ID tracking
		framework_instance_id = f"framework_{int(time.time() * 1000)}"

		# Create fresh Framework instance for this execution
		if self.framework_manager:
			self.framework_api = self.framework_manager.create_framework_instance(
				status_reporter=self.main_thread_handler,
				execution_state=self.execution_state
			)
			self.current_framework_instance_id = framework_instance_id
			self.log_status(f"Created fresh framework instance: {framework_instance_id}")

		# Prepare through API instead of direct Framework call
		if not self._prepare_framework_for_execution():
			self.log_status("Failed to prepare framework for execution")
			return

		# Prepare primitive data for thread
		enabled_experiments = []

		for experiment_name, enabled in self.experiment_states.items():
			if enabled and experiment_name in self.experiments:
				exp_data = self._create_primitive_experiment_data(experiment_name)
				enabled_experiments.append(exp_data)
				# Store Experiment indication in safe structure
				self.thread_safe_experiment_states[experiment_name] = True

		if not enabled_experiments:
			self.log_status("No experiments enabled")
			return

		# Set total_experiments BEFORE starting thread
		self.total_experiments = len(enabled_experiments)
		self.current_experiment_index = 0

		# Log the setup
		self.log_status(f"[RUN] Setup: {self.total_experiments} experiments to execute")

		# Prepare configuration data (primitives only)
		s2t_config_copy = dict(self.S2T_CONFIG) if self.S2T_CONFIG else {}

		# Get option states (convert Tkinter vars to primitives)
		options = {
			'stop_on_fail': self.stop_on_fail_var.get(),
			'check_unit_data': self.check_unit_data_var.get(),
			'upload_to_db': self.upload_unit_data_var.get()
		}

		# Clear any previous thread state
		self.thread_active = True

		# Update UI for start
		self._update_ui_for_start()

		# Debug button states after UI update for start
		self.debug_button_states("AFTER UI UPDATE FOR START")


		# Start thread with primitive data only
		self.framework_thread = threading.Thread(
			target=self._run_experiments_thread,
			args=(enabled_experiments, s2t_config_copy, options, framework_instance_id),
			daemon=True,
			name=f"FrameworkExecution_{framework_instance_id}"
		)
		self.framework_thread.start()

		self.log_status(f"Started execution thread for {len(enabled_experiments)} experiments")

	def _prepare_framework_for_execution(self):
		"""Prepare framework for execution through API"""
		if not self.framework_api:
			return True  # No framework to prepare

		try:
			# Get current state to verify preparation
			state = self.framework_api.get_current_state()
			return True  # Framework API handles preparation internally
		except Exception as e:
			self.log_status(f"Framework preparation error: {e}")
			return False

	def _run_experiments_thread(self, experiments_list, s2t_config, options, framework_instance_id):
		"""Enhanced thread execution with command system"""
		try:

			# Verify framework instance at start
			if framework_instance_id != self.current_framework_instance_id:
				self.log_status("[ERROR] Framework instance mismatch - aborting thread")
				return

			total_experiments = len(experiments_list)

			# Initialize execution state
			self.execution_state.update_state(
				execution_active=True,
				current_experiment=None,
				current_iteration=0,
				total_iterations=0
			)

			# Send setup notification
			self.main_thread_handler.queue_status_update({
				'type': 'execution_setup',
				'data': {
					'total_experiments': total_experiments,
					'experiment_names': [exp['experiment_name'] for exp in experiments_list],
					'framework_instance_id': framework_instance_id
				}
			})

			# Update framework options
			if self.framework_api:
				self.framework_api._set_upload_to_db(options['upload_to_db'])
				if options['check_unit_data']: self.framework_api._update_unit_data()

			for index, exp_data in enumerate(experiments_list):
				# Verify framework instance during execution
				if framework_instance_id != self.current_framework_instance_id:
					self.log_status("[ERROR] Framework instance changed during execution - aborting")
					break

				self.execution_state.update_state(experiment_index=index)

				#'experiment_index_update'
				# Send setup notification
				self.main_thread_handler.queue_status_update({
					'type': 'experiment_index_update',
					'data': {
						'current_experiment_index': index,
						'total_experiments': total_experiments,
						'experiment_name': exp_data['experiment_name'],
						'framework_instance_id': framework_instance_id
					}
				})

				# Check for END command BEFORE starting each experiment
				if self.execution_state.is_ended():
					self.log_status(f"[END] END command received - stopping before experiment {index + 1}")
					self._send_end_status(exp_data, index, len(experiments_list))
					break

				# Check for cancellation BEFORE starting each experiment
				if self.execution_state.should_stop() or self.execution_state.is_cancelled():
					self.log_status(f"[CANCEL] Execution stopped before experiment {index + 1}")
					self._send_cancellation_status(exp_data, index, len(experiments_list))
					break  # CRITICAL: Break immediately

				experiment_name = exp_data['experiment_name']

				# UPDATE: Make sure this status update is being sent
				self.main_thread_handler.queue_status_update({
					'type': 'experiment_status_update',
					'data': {
						'experiment_name': experiment_name,
						'status': 'In Progress',
						'bg_color': '#00008B',
						'fg_color': 'white'
					}
				})

				# Update experiment state
				self.execution_state.update_state(
					current_experiment=experiment_name,
					current_iteration=0
				)


				time.sleep(0.1)  # Ensure state update is processed

				self.main_thread_handler.queue_status_update({
					'type': 'experiment_status_update',
					'data': {
						'experiment_name': experiment_name,
						'status': 'In Progress',
						'bg_color': '#00008B',
						'fg_color': 'white'
					}
				})

				success = False

				try:


					# Use API instead of direct Framework access
					if self.framework_api is None:
						success = self._simulate_test_execution(exp_data)
					else:
						success = self._execute_framework_test(exp_data, s2t_config, experiment_name, framework_instance_id)

					# Check for END command after each experiment
					if self.execution_state.is_ended():
						self.log_status(f"[END] END command received after experiment '{experiment_name}' - stopping execution")
						self._send_end_status(exp_data, index + 1, len(experiments_list))

						# Update this experiment's status to show it completed
						status_text = "Done" if success else "Fail"
						bg_color = "#006400" if success else "yellow"
						fg_color = "white" if success else "black"

						self.main_thread_handler.queue_status_update({
							'type': 'experiment_status_update',
							'data': {
								'experiment_name': experiment_name,
								'status': status_text,
								'bg_color': bg_color,
								'fg_color': fg_color
							}
						})
						break

					# CRITICAL: Check for cancellation after each experiment
					if self.execution_state.is_cancelled():
						self.log_status(f"Execution cancelled after experiment '{experiment_name}'")
						if self.execution_state.is_cancelled():
							self._send_cancellation_status(exp_data, index, len(experiments_list))
						break

					# CRITICAL: Check for end after each experiment
					if self.execution_state.is_ended():
						self.log_status(f"[CANCEL] Execution cancelled after experiment '{experiment_name}'")
						if self.execution_state.is_ended():
							self._send_end_status(exp_data, index, len(experiments_list))
						break

				except InterruptedError:
					self.log_status(f"[CANCEL] Experiment '{experiment_name}' was cancelled")
					success = False
					self._send_cancellation_status(exp_data, index + 1, len(experiments_list))
					break
				except Exception as e:
					self.log_status(f"[ERROR] Experiment '{experiment_name}' failed: {str(e)}")
					success = False

					# Check for commands after exception
					if self.execution_state.is_ended():
						self._send_end_status(exp_data, index + 1, len(experiments_list))
						break
					# Send cancellation status and break immediately
					if self.execution_state.is_cancelled():
						self._send_cancellation_status(exp_data, index + 1, len(experiments_list))
						break

				# CRITICAL: Check for cancellation IMMEDIATELY after experiment execution
				if self.execution_state.is_cancelled():
					self.log_status(f"[CANCEL] Execution cancelled after experiment '{experiment_name}'")

					# Update this experiment's status to cancelled
					self.main_thread_handler.queue_status_update({
						'type': 'experiment_status_update',
						'data': {
							'experiment_name': experiment_name,
							'status': 'Cancelled',
							'bg_color': 'gray',
							'fg_color': 'white'
						}
					})

					self._send_cancellation_status(exp_data, index + 1, len(experiments_list))
					break  #  CRITICAL: Break immediately

				# Update experiment status
				status_text = "Done" if success else "Fail"
				bg_color = "#006400" if success else "yellow"
				fg_color = "white" if success else "black"

				self.main_thread_handler.queue_status_update({
					'type': 'experiment_status_update',
					'data': {
						'experiment_name': experiment_name,
						'status': status_text,
						'bg_color': bg_color,
						'fg_color': fg_color
					}
				})

				# Break if cancelled
				if self.execution_state.is_cancelled():
					break

				# Break if ended
				if self.execution_state.is_ended():
					break

				if not success and options['stop_on_fail']:
					break

				if index < len(experiments_list) - 1:
					time.sleep(2)

			# CRITICAL: Send proper completion status
			if not self.execution_state.is_cancelled() and not self.execution_state.is_ended():
				# All experiments completed successfully
				self.main_thread_handler.queue_status_update({
					'type': 'all_experiments_complete',
					'data': {
						'total_executed': len(experiments_list),
						'framework_instance_id': framework_instance_id
					}
				})

		except Exception as e:
			self.log_status(f"[ERROR] Thread execution error: {e}")

			# Send appropriate status on exception
			if self.execution_state.is_ended():
				self.main_thread_handler.queue_status_update({
					'type': 'execution_ended',
					'data': {
						'reason': f'Execution ended during error: {str(e)}',
						'error': str(e)
					}
				})

			# Send cancellation status on exception if cancelled
			if self.execution_state.is_cancelled():
				self.main_thread_handler.queue_status_update({
					'type': 'execution_cancelled',
					'data': {
						'reason': f'Execution error during cancellation: {str(e)}',
						'error': str(e)
					}
				})
		finally:
			# Proper cleanup using command system
			try:
				self.thread_active = False

				# Finalize framework execution
				self.thread_safe_experiment_states.clear()

				# Clear primitive data
				experiments_list.clear()
				s2t_config.clear()
				options.clear()
				self.log_status(f"[INFO] Execution completed for FID: {framework_instance_id}")

				# Queue completion
				if self.execution_state.is_ended():
					self.main_thread_handler.queue_status_update({
						'type': 'execution_ended_complete',
						'data': {
							'total_executed': len(experiments_list) if experiments_list else 0,
							'framework_instance_id':framework_instance_id}
					})
				# Queue completion
				#else:
				#	self.main_thread_handler.queue_status_update({
				#	'type': 'all_experiments_complete',
				#	'data': {
				#			'total_executed': len(experiments_list) if experiments_list else 0,
				#			'framework_instance_id':framework_instance_id}
				#	})

			except Exception as cleanup_error:
				self.log_status(f"[ERROR] Thread cleanup error: {cleanup_error}")

	def _execute_framework_test(self, exp_data, s2t_config, experiment_name, framework_instance_id):
		"""Execute framework test with proper error handling"""
		try:

			# Framework instance verification
			if framework_instance_id and framework_instance_id != self.current_framework_instance_id:
				self.log_status("[ERROR] Framework instance mismatch during execution")
				return False

			if not self.framework_api:
				self.log_status("No Framework API available")
				return False

			# Check global execution state before starting
			if execution_state.is_cancelled():
				self.log_status(f"[CANCEL] Execution already cancelled before starting '{experiment_name}'")
				return False

			if execution_state.is_ended():
				self.log_status(f"[CANCEL] Execution already ended before starting '{experiment_name}'")
				return False

			# Debug Logs
			#self.log_status(f"DEBUG: Starting Framework execution for '{experiment_name}'")
			#self.log_status(f"DEBUG: Control Panel cancellation state: {self.execution_state.is_cancelled()}")
			#self.log_status(f"DEBUG: Control Panel END state: {self.execution_state.is_ended()}")
			# Set up progress tracking
			estimated_iterations = self._estimate_experiment_iterations(exp_data)
			self.total_iterations_in_experiment = estimated_iterations
			self.current_iteration = 1
			self.strategy_progress = 0.0
			self.current_iteration_progress = 0.0

			# Update experiment name for progress tracking
			self.current_experiment_name = experiment_name
			extmask = exp_data.get('External Mask')
			print(f' External Option Mask selected: {extmask}')

			# Safe handling without problematic 'in' operation
			if isinstance(extmask, dict):
				external_masking = extmask if extmask else None  # Use dict if not empty
			elif extmask is None:
				external_masking = None
			elif str(extmask) in ["None", 'Default', '', ' ']:
				external_masking = None
			else:
				external_masking = None

			print( f' External Mask : "type{type(external_masking)}:{external_masking}"')
			# Execute through API
			result = self.framework_api.execute_experiment(
				experiment_data=exp_data,
				s2t_config=s2t_config,
				extmask=external_masking,
				experiment_name=experiment_name
			)

			# Check for cancellation through API
			state = self.framework_api.get_current_state()
			if state.get('end_requested') or 'CANCELLED' in result:
				return False

			# Process results
			if isinstance(result, list):
				failure_statuses = ['FAILED', 'CANCELLED', 'ExecutionFAIL']
				has_cancelled = any(status == 'CANCELLED' for status in result)
				if has_cancelled:
					self.log_status(f"[CANCEL] Framework execution cancelled for '{experiment_name}' (detected in results)")
					# Propagate cancellation to Control Panel's execution state
					self.execution_state.cancel(reason="Framework execution returned CANCELLED status")
					return False

				return not any(status in failure_statuses for status in result)

			# Check global execution state after Framework execution
			if execution_state.is_cancelled():
				self.log_status(f"[CANCEL] Execution was cancelled during Framework execution of '{experiment_name}'")
				return False

			return True

		except InterruptedError:
			self.log_status(f"[CANCEL] Experiment '{experiment_name}' was cancelled")
			# Propagate cancellation to Control Panel's execution state
			self.execution_state.cancel(reason="Framework execution interrupted")
			return False
		except Exception as e:
			self.log_status(f"[ERROR] Framework execution error for '{experiment_name}': {str(e)}")
			return False

	def _create_primitive_experiment_data(self, experiment_name):
		"""Create primitive data copy for thread safety"""
		original_data = self.experiments[experiment_name]
		exp_data = {}

		# Copy all primitive data
		for key, value in original_data.items():
			if isinstance(value, (str, int, float, bool, list, dict, type(None))):
				exp_data[key] = value
			else:
				if key == 'External Mask': # This will be passed throug the Other Variables
					continue
				exp_data[key] = str(value)

		# Add experiment name for identification
		exp_data['experiment_name'] = experiment_name

		# Add mask data if available
		external_mask = original_data.get('External Mask')
		if external_mask not in [None, "None", 'Default', '', ' ']:
			exp_data['External Mask'] = external_mask
		else:
			exp_data['External Mask'] = None

		return exp_data

	def _send_cancellation_status(self, exp_data, completed_count, total_count):
		"""Helper method to send cancellation status"""
		self.main_thread_handler.queue_status_update({
			'type': 'execution_cancelled',
			'data': {
				'experiment_name': exp_data.get('experiment_name', 'Unknown'),
				'completed_experiments': completed_count,
				'total_experiments': total_count,
				'reason': 'User cancellation'
			}
		})

	def _send_end_status(self, exp_data, completed_count, total_count):
		"""Helper method to send end command status"""
		self.main_thread_handler.queue_status_update({
			'type': 'execution_ended',
			'data': {
				'experiment_name': exp_data.get('experiment_name', 'Unknown'),
				'completed_experiments': completed_count,
				'total_experiments': total_count,
				'reason': 'END command - execution stopped gracefully'
			}
		})

	# ==================== COMMAND SYSTEM & CONTROL ====================

	def toggle_framework_hold(self):
		"""Toggle framework halt/continue functionality using command system"""

		if not self.framework_api:
			self.log_status("No Framework API available")
			return

		state = self.framework_api.get_current_state()

		if not state.get('is_running'):
			self.log_status("No active execution to control")
			return

		# Check if currently paused
		if state.get('is_halted', False):
			# Continue execution
			result = self.framework_api.resume_execution_with_ack()
			if result['success']:
				self.hold_button.configure(text="Hold", style="Hold.TButton")
				self.log_status(result['reason'])
				self.status_label.configure(text=" Resuming... ", bg="#BF0000", fg="white")
			else:
				self.log_status(result['error'])
		else:
			# Halt execution
			result = self.framework_api.pause_execution_with_ack()
			if result['success']:
				self.hold_button.configure(text="Continue", style="Continue.TButton")
				self.log_status(result['reason'])
				self.status_label.configure(text=" Halting... ", bg="orange", fg="black")
			else:
				self.log_status(result['error'])
	def end_current_experiment(self):
		"""End experiment through API"""
		if not self.framework_api:
			self.log_status("No Framework API available")
			return

		result = self.framework_api.end_current_experiment_with_ack()
		if result['success']:
			self.log_status(result['reason'])
			self.end_button.configure(text="Ending...", state=tk.DISABLED, style="EndActive.TButton")
		else:
			self.log_status(result['error'])

	def cancel_tests(self):

		"""Cancel through API"""
		if not self.framework_api:
			self.log_status("No Framework API available")
			return

		result = self.framework_api.cancel_experiment_with_ack()
		if result['success']:
			self.log_status(result['reason'])
		else:
			self.log_status(result['error'])

		# Update UI immediately
		self.thread_active = False
		self.cancel_button.configure(state=tk.DISABLED)
		self.end_button.configure(state=tk.DISABLED)

		# Schedule cleanup
		self.root.after(2000, self._cleanup_after_cancel)

	def _cleanup_after_cancel(self):
		"""Cleanup after cancellation with command system"""
		try:

			# Check if cancellation was processed or force cleanup after timeout
			if (not self.execution_state.has_command(ExecutionCommand.CANCEL) or
				not self.thread_active):
				self.log_status("Cancellation completed successfully")
				self.status_label.configure(text=" Cancelled ", bg="gray", fg="white")
				self._reset_buttons_after_cancel()
			else:
				# Still processing, check again but with limit
				if not hasattr(self, '_cancel_retry_count'):
					self._cancel_retry_count = 0

				self._cancel_retry_count += 1
				if self._cancel_retry_count < 10:  # Max 5 seconds (10 * 500ms)
					self.root.after(500, self._cleanup_after_cancel)
				else:
					# Force cleanup after timeout
					self.log_status("Force cleanup after cancel timeout")
					self._reset_buttons_after_cancel()
					self._cancel_retry_count = 0

		except Exception as e:
			self.log_status(f"Error in cancel cleanup: {e}")

	def _cleanup_experiment_statuses(self):
		"""Clean up experiment statuses when starting new run"""

		try:
			for frame_data in self.experiment_frames:
				run_label = frame_data['run_label']

				if run_label.winfo_exists():
					# Cancel any ongoing animations
					run_label.configure(text="Idle", bg="lightgray", fg="black")

					# Reset to clean idle state - simple color change
					run_label.configure(text="Idle", bg="lightgray", fg="black")

					# Clear status tracking
					frame_data['current_status'] = 'Idle'
					frame_data['status_timestamp'] = time.time()

		except Exception as e:
			self.log_status(f"[ERROR] Status cleanup failed: {e}")

	def _reset_buttons_after_cancel(self):
		"""Reset buttons after cancellation is complete"""
		try:
			self.thread_active = False

			self.run_button.configure(state=tk.NORMAL)
			self.cancel_button.configure(state=tk.DISABLED)
			self.hold_button.configure(state=tk.DISABLED, text=" Hold ")
			self.end_button.configure(state=tk.DISABLED, text="End", style="End.TButton")
			self.power_control_button.configure(state=tk.NORMAL)
			self.ipc_control_button.configure(state=tk.NORMAL)

			# Final status update
			self.root.after(2000, lambda: self.status_label.configure(text=" Ready ", bg="white", fg="black"))
			# Reset cancel retry
			if hasattr(self, '_cancel_retry_count'):
				self._cancel_retry_count = 0
		except Exception as e:
			self.log_status(f"Error resetting buttons: {e}")

	def _reset_all_button_states(self):
		"""Reset all button states to initial ready state"""
		try:
			# Reset to initial ready state
			if hasattr(self, 'run_button') and self.run_button.winfo_exists():
				self.run_button.configure(state='normal', text="Run")

			if hasattr(self, 'cancel_button') and self.cancel_button.winfo_exists():
				self.cancel_button.configure(state='disabled', text="Cancel")

			if hasattr(self, 'hold_button') and self.hold_button.winfo_exists():
				self.hold_button.configure(state='disabled', text="Hold", style="Hold.TButton")

			if hasattr(self, 'end_button') and self.end_button.winfo_exists():
				self.end_button.configure(state='disabled', text="End", style="End.TButton")

			if hasattr(self, 'power_control_button') and self.power_control_button.winfo_exists():
				self.power_control_button.configure(state='normal')

			if hasattr(self, 'ipc_control_button') and self.ipc_control_button.winfo_exists():
				self.ipc_control_button.configure(state='normal')

			# Reset any button priority tracking
			self._current_button_priority = 40

			if debug:
				self.log_status("[DEBUG] All button states reset to ready state")

		except Exception as e:
			self.log_status(f"[ERROR] Button state reset failed: {e}")

	def _reset_execution_counters(self):
		"""Reset all execution counters and tracking variables"""
		try:
			# Reset counters in status panel
			if hasattr(self, 'status_panel'):
				self.status_panel.reset_counters()

			# Reset counters in control panel (backward compatibility)
			self.pass_count = 0
			self.fail_count = 0
			self.skip_count = 0

			# Update counter labels
			if hasattr(self, 'pass_count_label'):
				self.pass_count_label.configure(text="✓ Pass: 0")
			if hasattr(self, 'fail_count_label'):
				self.fail_count_label.configure(text="✗ Fail: 0")
			if hasattr(self, 'skip_count_label'):
				self.skip_count_label.configure(text="⊘ Skip: 0")

			# Reset timing
			self.start_time = None
			self.last_iteration_time = None

			# Reset progress tracking
			self.current_experiment_name = None
			self.current_experiment_index = 0
			self.total_experiments = 0
			self.current_iteration = 0
			self.total_iterations_in_experiment = 0
			self.current_iteration_progress = 0.0
			self.strategy_progress = 0.0

			# Reset elapsed time display
			if hasattr(self, 'elapsed_time_label'):
				self.elapsed_time_label.configure(text="Time: 00:00")

			self.log_status("[RESET] All counters and progress tracking reset")

		except Exception as e:
			self.log_status(f"[ERROR] Counter reset failed: {e}")

	# ==================== UI COORDINATION & ANIMATION ====================

	def _coordinate_progress_updates(self, source_type: str, progress_data: Dict[str, Any]):
		"""Coordinate progress updates for dual progress bar system - ENHANCED"""

		try:
			if source_type == 'strategy_progress':
				# Strategy progress updates the ITERATION progress bar
				strategy_progress = progress_data['progress_percent']
				self.strategy_progress = strategy_progress
				#print(f'Strategy Progress: {strategy_progress}')
				# Update iteration tracking variables
				self.current_iteration = progress_data['current_iteration']
				self.total_iterations_in_experiment = progress_data['total_iterations']

				# Update ITERATION progress bar
				if hasattr(self, 'iteration_progress_var'):
					self.iteration_progress_var.set(min(100, max(0, strategy_progress)))
				if hasattr(self, 'iteration_percentage_label'):
					self.iteration_percentage_label.configure(text=f"{int(strategy_progress)}%")
				if hasattr(self, 'iteration_progress_label'):
					self.iteration_progress_label.configure(
						text=f"({progress_data['current_iteration']}/{progress_data['total_iterations']})")

				# Calculate iteration progress weight for overall calculation
				if progress_data['total_iterations'] > 0:
					self.current_iteration_progress = int((strategy_progress / 100.0))
				##print(f'strategy_progress - {progress_data["total_iterations"]}')
				# Update OVERALL progress bar
				self._update_overall_progress()

				# Update timing and speed
				self._update_timing_display()

				# Mark strategy progress as active
				self._strategy_progress_active = True

				# Update iteration progress bar style based on progress
				if hasattr(self, 'iteration_progress_bar'):
					if strategy_progress < 30:
						self.iteration_progress_bar.configure(style="Iteration.Running.Horizontal.TProgressbar")
					elif strategy_progress < 70:
						self.iteration_progress_bar.configure(style="Iteration.Horizontal.TProgressbar")
					else:
						self.iteration_progress_bar.configure(style="Iteration.Running.Horizontal.TProgressbar")

			elif source_type == 'iteration_progress':
				# Direct iteration progress update
				iteration_progress = progress_data.get('progress_weight', 0.0) * 100

				if hasattr(self, 'iteration_progress_var'):
					self.iteration_progress_var.set(min(100, max(0, iteration_progress)))
				if hasattr(self, 'iteration_percentage_label'):
					self.iteration_percentage_label.configure(text=f"{int(iteration_progress)}%")

				# Update overall progress
				self.current_iteration_progress = progress_data.get('progress_weight', 0.0)
				print('iteration_progress')
				self._update_overall_progress()

				# Update timing
				self._update_timing_display()

			elif source_type == 'overall_calculation':
				# Only update overall when no strategy progress is active
				if not hasattr(self, '_strategy_progress_active') or not self._strategy_progress_active:
					self._update_overall_progress()
					print('overall_calculation')
					self._update_timing_display()

			elif source_type == 'experiment_start':
				# Reset iteration progress for new experiment
				if hasattr(self, 'iteration_progress_var'):
					self.iteration_progress_var.set(0)
				if hasattr(self, 'iteration_percentage_label'):
					self.iteration_percentage_label.configure(text="0%")
				self.current_iteration = 0
				self.current_iteration_progress = 0.0
				self.strategy_progress - 0.0
				print('experiment_start')
				# Update overall progress
				self._update_overall_progress()

			elif source_type == 'experiment_complete':
				# Set iteration progress to 100% for completed experiment
				if hasattr(self, 'iteration_progress_var'):
					self.iteration_progress_var.set(100)
				if hasattr(self, 'iteration_percentage_label'):
					self.iteration_percentage_label.configure(text="100%")
				self.current_iteration_progress = 1.0

				print('experiment_start')
				# Update overall progress
				self._update_overall_progress()

				# Update timing
				self._update_timing_display()

		except Exception as e:
			self.log_status(f"[ERROR] Progress coordination error: {e}")

	def _coordinate_button_states(self, update_type: str, button_data: Dict[str, Any] = None):
		"""Coordinate button state changes to prevent conflicts - ENHANCED DEBUG"""

		print(f"_coordinate_button_states called: update_type='{update_type}'")
		if button_data:
			print(f"  button_data: {button_data}")

		# Define button state priorities (higher number = higher priority)
		state_priorities = {
			'disabled_during_execution': 100,
			'specific_button_update': 80,
			'enable_after_completion': 60,
			'default_state': 40
		}

		current_priority = getattr(self, '_current_button_priority', 0)
		new_priority = state_priorities.get(update_type, 40)

		print(f"  current_priority: {current_priority}, new_priority: {new_priority}")

		# Only update if new priority is higher or equal
		if new_priority >= current_priority:
			self._current_button_priority = new_priority
			print(f"  Updating buttons with priority {new_priority}")

			if update_type == 'specific_button_update' and button_data:
				for button_name, config in button_data.items():
					if hasattr(self, button_name):
						try:
							button = getattr(self, button_name)
							if button.winfo_exists():
								button.configure(**config)
								print(f"    Updated {button_name}: {config}")
						except Exception as e:
							self.log_status(f"[ERROR] Button update failed for {button_name}: {e}")

			elif update_type == 'enable_after_completion':
				print("  Calling _enable_ui_buttons_safe")
				self._enable_ui_buttons_safe()

			elif update_type == 'disabled_during_execution':
				print("  Calling _disable_ui_buttons_safe")
				self._disable_ui_buttons_safe()

			# Schedule priority reset after delay
			self.root.after(2000, lambda: setattr(self, '_current_button_priority', 40))
		else:
			print("  Skipping update due to lower priority")

	def _coordinate_status_updates(self, update_data: Dict[str, Any]):
		"""Coordinate status label updates to prevent conflicts"""

		# Priority system for status updates
		status_priorities = {
		'error': 100,
		'failed': 95,
		'cancelled': 90,
		'ended': 85,
		'completed': 80,
		'halted': 70,
		'resuming': 65,
		'running': 60,
		'starting': 50,
		'ready': 40
	}

	# Determine priority from status text
		status_text = update_data.get('text', '').lower()
		current_priority = 40  # default

		for status_type, priority in status_priorities.items():
			if status_type in status_text:
				current_priority = priority
				break

		# Check if we should update (higher or equal priority)
		last_priority = getattr(self, '_last_status_priority', 0)

		if current_priority >= last_priority:
			self._last_status_priority = current_priority

			try:
				if hasattr(self, 'status_label') and self.status_label.winfo_exists():
					self.status_label.configure(**update_data)
			except Exception as e:
				self.log_status(f"[ERROR] Status label update failed: {e}")

			# Reset priority after delay for high priority statuses
			if current_priority > 60:
				reset_delay = 4000 if current_priority >= 80 else 3000
				self.root.after(reset_delay, lambda: setattr(self, '_last_status_priority', 40))

	def _coordinate_progress_bar_styles(self, style_name: str, duration: int = None, bar_type: str = 'iteration'):
		"""Coordinate progress bar style changes with proper timing - UPDATED for dual bars"""

		try:
			if bar_type == 'overall' and hasattr(self, 'overall_progress_bar'):
				if self.overall_progress_bar.winfo_exists():
					self.overall_progress_bar.configure(style=style_name)

					# Handle automatic reset
					if duration and not style_name.startswith("Overall."):
						self.root.after(duration,
							lambda: self._coordinate_progress_bar_styles("Overall.Horizontal.TProgressbar", None, 'overall'))

			elif bar_type == 'iteration' and hasattr(self, 'iteration_progress_bar'):
				if self.iteration_progress_bar.winfo_exists():
					self.iteration_progress_bar.configure(style=style_name)

					# Handle automatic reset
					if duration and not style_name.startswith("Iteration."):
						self.root.after(duration,
							lambda: self._coordinate_progress_bar_styles("Iteration.Horizontal.TProgressbar", None, 'iteration'))

		except Exception as e:
			self.log_status(f"[ERROR] Progress bar style update failed: {e}")

	def _update_experiment_status_safe(self, experiment_name: str, status: str,
									bg_color: str, fg_color: str):
		"""Safely update experiment status with animation support"""

		try:
			for frame_data in self.experiment_frames:
				if frame_data['experiment_name'] == experiment_name:
					run_label = frame_data['run_label']

					if run_label.winfo_exists():
						# Optional: Simple flash effect for important status changes
						if status in ['Done', 'Fail', 'Cancelled']:
							# Brief white flash, then final color
							run_label.configure(text=status, bg='white', fg='black')
							self.root.after(100, lambda: run_label.configure(bg=bg_color, fg=fg_color))
						else:
							# Direct update for other statuses
							run_label.configure(text=status, bg=bg_color, fg=fg_color)
						# Store the current status for cleanup tracking
						frame_data['current_status'] = status
						frame_data['status_timestamp'] = time.time()
					break

		except Exception as e:
			self.log_status(f"[ERROR] Experiment status update failed: {e}")

	def _enable_ui_buttons_safe(self):
		"""Safely enable UI buttons with error handling"""
		try:
			if hasattr(self, 'run_button') and self.run_button.winfo_exists():
				self.run_button.configure(state='normal')
			if hasattr(self, 'cancel_button') and self.cancel_button.winfo_exists():
				self.cancel_button.configure(state='disabled')
			if hasattr(self, 'hold_button') and self.hold_button.winfo_exists():
				self.hold_button.configure(state='disabled', text=" Hold ")
			if hasattr(self, 'end_button') and self.end_button.winfo_exists():
				self.end_button.configure(state='disabled', text="End")
			if hasattr(self, 'power_control_button') and self.power_control_button.winfo_exists():
				self.power_control_button.configure(state='normal')
			if hasattr(self, 'ipc_control_button') and self.ipc_control_button.winfo_exists():
				self.ipc_control_button.configure(state='normal')
		except Exception as e:
			self.log_status(f"[ERROR] Button enable error: {e}")

	def _disable_ui_buttons_safe(self):
		"""Safely disable UI buttons during execution - WITH DEBUG"""
		try:
			print("_disable_ui_buttons_safe called")

			if hasattr(self, 'run_button') and self.run_button.winfo_exists():
				self.run_button.configure(state='disabled')
				print("  run_button disabled")
			if hasattr(self, 'cancel_button') and self.cancel_button.winfo_exists():
				self.cancel_button.configure(state='normal')
				print("  cancel_button enabled")
			if hasattr(self, 'hold_button') and self.hold_button.winfo_exists():
				self.hold_button.configure(state='normal')
				print("  hold_button enabled")
			if hasattr(self, 'end_button') and self.end_button.winfo_exists():
				self.end_button.configure(state='normal')
				print("  end_button enabled")
			if hasattr(self, 'power_control_button') and self.power_control_button.winfo_exists():
				self.power_control_button.configure(state='disabled')
				print("  power_control_button disabled")
			if hasattr(self, 'ipc_control_button') and self.ipc_control_button.winfo_exists():
				self.ipc_control_button.configure(state='disabled')
				print("  ipc_control_button disabled")

		except Exception as e:
			self.log_status(f"[ERROR] Button disable error: {e}")
	# ==================== PROGRESS TRACKING & DISPLAY ====================

	def _update_ui_for_start(self):
		"""Update UI elements for execution start - FIXED with debugging"""
		try:
			self.debug_button_states("INSIDE _update_ui_for_start - BEFORE")

			# Update status label
			self.status_label.configure(text=" Starting ", bg="#4CAF50", fg="white")
			self.log_status("Starting test execution")

			# Reset run labels to clean state
			for frame_data in self.experiment_frames:
				if frame_data['run_label'].winfo_exists():
					frame_data['run_label'].configure(text="Idle", bg="lightgray", fg="black")

			# CRITICAL: Set button states for RUNNING execution
			print("Setting buttons to RUNNING state...")

			if hasattr(self, 'run_button') and self.run_button.winfo_exists():
				self.run_button.configure(state='disabled', text="Run")
				print("  run_button set to disabled")

			if hasattr(self, 'cancel_button') and self.cancel_button.winfo_exists():
				self.cancel_button.configure(state='normal', text="Cancel")
				print("  cancel_button set to normal")

			if hasattr(self, 'hold_button') and self.hold_button.winfo_exists():
				self.hold_button.configure(state='normal', text="Hold", style="Hold.TButton")
				print("  hold_button set to normal")

			if hasattr(self, 'end_button') and self.end_button.winfo_exists():
				self.end_button.configure(state='normal', text="End", style="End.TButton")
				print("  end_button set to normal")

			if hasattr(self, 'power_control_button') and self.power_control_button.winfo_exists():
				self.power_control_button.configure(state='disabled')
				print("  power_control_button set to disabled")

			if hasattr(self, 'ipc_control_button') and self.ipc_control_button.winfo_exists():
				self.ipc_control_button.configure(state='disabled')
				print("  ipc_control_button set to disabled")

			# Force UI update
			self.root.update_idletasks()

			self.debug_button_states("INSIDE _update_ui_for_start - AFTER")

			# Update status after a brief delay to show "Starting" then "Running"
			self.root.after(500, lambda: self.status_label.configure(text=" Running ", bg="#BF0000", fg="white"))

		except Exception as e:
			print(f"Error updating UI for start: {e}")
			import traceback
			traceback.print_exc()

	def update_progress_display(self, experiment_name="", strategy_type="", test_name="",
							  status="Idle", result_status=None):
		"""Update the enhanced progress display - FIXED for dual progress bars"""
		try:
			# Update basic labels only if provided
			if experiment_name is not None and hasattr(self, 'strategy_label'):
				self.strategy_label.configure(text=f"Experiment: {experiment_name}")

			if strategy_type and hasattr(self, 'test_name_label'):
				self.test_name_label.configure(text=f"Strategy: {strategy_type} - {test_name}")

			if status and hasattr(self, 'iteration_status_label'):
				self.iteration_status_label.configure(text=f"Status: {status}")


			# Update counters if result status is provided
			if result_status:
				# Use status panel counters if available, otherwise use control panel counters
				if hasattr(self, 'status_panel') and hasattr(self.status_panel, 'pass_count'):
					self._update_status_panel_counters(result_status)
				else:
					self._update_control_panel_counters(result_status)

			# Update timing and speed calculations
			self._update_timing_display()

		except Exception as e:
			self.log_status(f"[ERROR] Progress display update failed: {e}")

	def _update_status_panel_counters(self, result_status):
		"""Update counters in status panel"""
		try:
			if result_status.upper() in ["PASS", "SUCCESS", "*"]:
				self.status_panel.pass_count += 1
			elif result_status.upper() in ["FAIL", "FAILED", "ERROR"]:
				self.status_panel.fail_count += 1
			else:
				self.status_panel.skip_count += 1

			# Update counter labels
			if hasattr(self.status_panel, 'pass_count_label'):
				self.status_panel.pass_count_label.configure(text=f"✓ Pass: {self.status_panel.pass_count}")
			if hasattr(self.status_panel, 'fail_count_label'):
				self.status_panel.fail_count_label.configure(text=f"✗ Fail: {self.status_panel.fail_count}")
			if hasattr(self.status_panel, 'skip_count_label'):
				self.status_panel.skip_count_label.configure(text=f"⊘ Skip: {self.status_panel.skip_count}")

		except Exception as e:
			print(f"Status panel counter update error: {e}")

	def _update_control_panel_counters(self, result_status):
		"""Update counters in control panel (backward compatibility)"""
		try:
			if result_status.upper() in ["PASS", "SUCCESS", "*"]:
				self.pass_count += 1
			elif result_status.upper() in ["FAIL", "FAILED", "ERROR"]:
				self.fail_count += 1
			else:
				self.skip_count += 1

			# Update counter labels
			if hasattr(self, 'pass_count_label'):
				self.pass_count_label.configure(text=f"✓ Pass: {self.pass_count}")
			if hasattr(self, 'fail_count_label'):
				self.fail_count_label.configure(text=f"✗ Fail: {self.fail_count}")
			if hasattr(self, 'skip_count_label'):
				self.skip_count_label.configure(text=f"⊘ Skip: {self.skip_count}")

		except Exception as e:
			print(f"Control panel counter update error: {e}")

	def _update_overall_progress(self):
		"""Calculate and update OVERALL progress across all experiments"""
		try:
			if self.total_experiments == 0:
				self.overall_progress_var.set(0)
				self.overall_percentage_label.configure(text="0%")
				self.overall_experiment_label.configure(text="(0/0 experiments)")
				return

			# Calculate overall progress
			completed_experiments = max(self.current_experiment_index, 0)
			current_experiment_progress = min(self.current_iteration_progress, 1.0)

			# FIXED: Calculate current experiment's contribution to overall progress
			if self.total_iterations_in_experiment > 0:
				# Current experiment progress = (completed iterations + current iteration progress) / total iterations
				current_exp_progress = (self.current_iteration - 1 + current_experiment_progress) / self.total_iterations_in_experiment
				current_exp_progress = min(1.0, max(0.0, current_exp_progress))  # Clamp between 0 and 1
			else:
				current_exp_progress = 0.0

			# FIXED: Overall progress = (completed experiments + current experiment progress) / total experiments
			overall_progress = ((completed_experiments + current_exp_progress) / self.total_experiments) * 100

			# Update overall progress bar
			self.overall_progress_var.set(max(0, min(100, overall_progress)))
			self.overall_percentage_label.configure(text=f"{int(overall_progress)}%")
			self.overall_experiment_label.configure(
			text=f"({completed_experiments + 1 }/{self.total_experiments} experiments)") #(1 if current_experiment_progress > 0 else 1)

			# Update overall progress bar style based on progress
			if overall_progress < 25:
				self.overall_progress_bar.configure(style="Overall.Running.Horizontal.TProgressbar")
			elif overall_progress >= 100:
				self.overall_progress_bar.configure(style="Overall.Horizontal.TProgressbar")
			else:
				self.overall_progress_bar.configure(style="Overall.Running.Horizontal.TProgressbar")

		except Exception as e:
			self.log_status(f"[ERROR] Overall progress calculation error: {e}")

		# Calculate progress within current experiment
		#if self.total_iterations_in_experiment > 0:
		#	# Progress from completed iterations
		#	completed_iterations_progress = (self.current_iteration - 1) / self.total_iterations_in_experiment
		#
		#	# Progress from current iteration
		#	current_iteration_progress = self.current_iteration_progress / self.total_iterations_in_experiment
		#
		#	# Total progress within current experiment (0.0 to 1.0)
		#	experiment_progress = min(1.0, completed_iterations_progress + current_iteration_progress)
		#else:
		#	experiment_progress = 0.0
		#
		# Calculate overall progress across all experiments
		#if self.total_experiments > 0:
		#	# Progress from completed experiments
		#	completed_experiments_progress = self.current_experiment_index / self.total_experiments
		#
		#	# Progress from current experiment
		#	current_experiment_contribution = experiment_progress / self.total_experiments
		#
		#	# Total overall progress
		#	overall_progress = (completed_experiments_progress + current_experiment_contribution) * 100
		#else:
		#	overall_progress = 0.0

		## Update progress bar
		#self.progress_var.set(min(100, max(0, overall_progress)))

		## Update progress labels
		#self.progress_percentage_label.configure(text=f"{int(overall_progress)}%")

		## Update iteration info
		#if self.current_experiment_name:
		#	iteration_text = f"Exp {self.current_experiment_index + 1}/{self.total_experiments} - Iter {self.current_iteration}/{self.total_iterations_in_experiment}"
		#else:
		#	iteration_text = f"Exp {self.current_experiment_index}/{self.total_experiments}"

		#self.progress_iteration_label.configure(text=iteration_text)


		# Debug logging
		#print(f"DEBUG Progress: {overall_progress:.1f}% (Exp: {self.current_experiment_index+1}/{self.total_experiments}, Iter: {self.current_iteration}/{self.total_iterations_in_experiment}, Weight: {self.current_iteration_progress:.2f})")

	def _update_timing_display(self):
		"""Update timing display including elapsed time, ETA, and speed - FIXED"""
		current_time = time.time()

		# Initialize start time if not set
		if self.start_time is None:
			self.start_time = current_time

		# Calculate elapsed time
		elapsed_seconds = current_time - self.start_time
		elapsed_str = self._format_time(elapsed_seconds)

		# Update elapsed time label
		if hasattr(self, 'elapsed_time_label'):
			self.elapsed_time_label.configure(text=f"Time: {elapsed_str}")

		# Calculate and display speed/ETA if we have progress data
		if hasattr(self, 'current_iteration') and hasattr(self, 'total_iterations_in_experiment'):
			self._update_speed_and_eta(current_time, elapsed_seconds)

	def _update_speed_and_eta(self, current_time, elapsed_seconds):
		"""Update speed and ETA calculations - FIXED for dual progress bar system"""
		try:
			# Calculate total completed iterations across all experiments
			total_completed = (self.current_experiment_index *
							getattr(self, 'avg_iterations_per_experiment', 10) +
							max(0, self.current_iteration - 1))

			# Calculate total expected iterations
			total_expected = (self.total_experiments *
							getattr(self, 'avg_iterations_per_experiment', 10))

			if total_completed > 0 and elapsed_seconds > 0:
				# Calculate iterations per second
				iterations_per_second = total_completed / elapsed_seconds

				# Update speed display - use iteration_speed_label instead of speed_label
				if iterations_per_second >= 1:
					speed_text = f"{iterations_per_second:.1f} iter/s"
				else:
					seconds_per_iteration = elapsed_seconds / total_completed
					speed_text = f"{seconds_per_iteration:.1f} s/iter"

				# Update the correct speed label
				if hasattr(self, 'iteration_speed_label'):
					self.iteration_speed_label.configure(text=speed_text)

				# Calculate ETA
				remaining_iterations = total_expected - total_completed
				if remaining_iterations > 0 and iterations_per_second > 0:
					eta_seconds = remaining_iterations / iterations_per_second
					eta_str = self._format_time(eta_seconds)

					# Update the correct ETA label
					if hasattr(self, 'overall_eta_label'):
						self.overall_eta_label.configure(text=f"ETA: {eta_str}")
				else:
					if hasattr(self, 'overall_eta_label'):
						self.overall_eta_label.configure(text="ETA: --:--")
			else:
				# Clear speed and ETA when no data available
				if hasattr(self, 'iteration_speed_label'):
					self.iteration_speed_label.configure(text="")
				if hasattr(self, 'overall_eta_label'):
					self.overall_eta_label.configure(text="")

		except Exception as e:
			# Don't let timing calculations break the UI
			print(f"Error updating speed/ETA: {e}")
			# Clear labels on error
			if hasattr(self, 'iteration_speed_label'):
				self.iteration_speed_label.configure(text="")
			if hasattr(self, 'overall_eta_label'):
				self.overall_eta_label.configure(text="")

	def _format_time(self, seconds):
		"""Format seconds into HH:MM:SS or MM:SS format"""
		if seconds < 0:
			return "00:00"

		hours = int(seconds // 3600)
		minutes = int((seconds % 3600) // 60)
		seconds = int(seconds % 60)

		if hours > 0:
			return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
		else:
			return f"{minutes:02d}:{seconds:02d}"

	def _estimate_iterations_per_experiment(self):
		"""Estimate average iterations per experiment for timing calculations"""
		if not self.experiments:
			return 10  # Default estimate

		total_iterations = 0
		experiment_count = 0

		for experiment_data in self.experiments.values():
			test_type = experiment_data.get('Test Type', '')

			if test_type == 'Loops':
				iterations = experiment_data.get('Loops', 5)
			elif test_type == 'Sweep':
				# Calculate sweep iterations
				start = experiment_data.get('Start', 0)
				end = experiment_data.get('End', 10)
				step = experiment_data.get('Steps', 1)
				iterations = max(1, int((end - start) / step) + 1)
			elif test_type == 'Shmoo':
				# Estimate shmoo iterations (this would need more complex calculation)
				iterations = 25  # Default estimate for shmoo
			else:
				iterations = 5  # Default

			total_iterations += iterations
			experiment_count += 1

		avg_iterations = total_iterations / experiment_count if experiment_count > 0 else 10
		self.avg_iterations_per_experiment = avg_iterations

		return avg_iterations

	def _estimate_experiment_iterations(self, exp_data):
		"""Estimate number of iterations for an experiment"""
		test_type = exp_data.get('Test Type', '')

		if test_type == 'Loops':
			return exp_data.get('Loops', 5)
		elif test_type == 'Sweep':
			start = exp_data.get('Start', 0)
			end = exp_data.get('End', 10)
			step = exp_data.get('Steps', 1)
			return max(1, int((end - start) / step) + 1)
		elif test_type == 'Shmoo':
			return 25  # Default estimate
		else:
			return 5

	def reset_timing(self):
		"""Reset timing calculations for new test run"""
		self.start_time = None
		self.last_iteration_time = None

	def reset_progress_tracking(self):
		"""Reset progress tracking variables"""
		self.status_panel.reset_progress_tracking()

	def _external_log_callback(self, message: str, level: str):
		"""Callback for external logging integration."""
		# You can add any additional logging logic here
		pass

	# ==================== EXPERIMENT MANAGEMENT ====================

	def load_experiments_file(self):
		file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("JSON files", "*.json")])
		if file_path:
			self.file_entry.delete(0, tk.END)
			self.file_entry.insert(0, file_path)
			self.load_experiments(file_path)

	def load_experiments(self, file_path):
		"""Load experiments with improved error handling"""
		try:
			# Suppress openpyxl warnings if needed
			import warnings
			with warnings.catch_warnings():
				warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

				self.experiments = OpenExperiment(file_path) if self.Framework_utils == None else self.Framework_utils.Recipes(file_path)

			if not self.experiments:
				messagebox.showwarning("Load Warning", "No experiments found in the selected file.")
				return

			self.saveas_button.configure(state=tk.NORMAL)

			# Estimate iterations per experiment for timing calculations
			self._estimate_iterations_per_experiment()

			self.create_experiment_rows()

			self.log_status(f"Loaded {len(self.experiments)} experiments from {os.path.basename(file_path)}")

		except Exception as e:
			self.log_status(f"[ERROR] Failed to load experiments: {e}")
			messagebox.showerror("Error", f"Failed to load experiments: {e}")

	def create_experiment_header(self):
		"""Create header row for experiment columns"""
		if hasattr(self, 'header_frame'):
			self.header_frame.destroy()

		# Header frame
		self.header_frame = ttk.Frame(self.experiment_container, style="Header.TFrame")
		self.header_frame.pack(fill=tk.X, pady=(0, 5), padx=2)

		# Configure grid weights
		self.header_frame.grid_columnconfigure(2, weight=1)

		# Header labels
		headers = [
			("", 0, 3),  # Checkbox column
			("Experiment", 1, 15),
			("Test Name", 2, 20),
			("Mode", 3, 8),
			("Type", 4, 8),
			("Edit", 5, 6),  # Edit button
			("Mask", 6, 10),
			("Status", 7, 12)
		]

		for text, col, width in headers:
			if text:  # Only create label if there's text
				label = ttk.Label(self.header_frame, text=text, font=("Arial", 9, "bold"))
				if col == 2:  # Test name column
					label.grid(row=0, column=col, sticky="ew", padx=(0, 8))
				else:
					label.grid(row=0, column=col, sticky="w", padx=(0, 8))

		# Add separator line
		separator = ttk.Separator(self.experiment_container, orient='horizontal')
		separator.pack(fill=tk.X, pady=(0, 5))

	def create_experiment_rows(self):
		"""Create experiment rows with thread-safe data storage"""
		# Clear existing frames
		for frame_data in getattr(self, 'experiment_frames', []):
			try:
				if isinstance(frame_data, dict) and 'frame' in frame_data:
					if 'enabled_var' in frame_data:
						frame_data['enabled_var'] = None
					if 'mask_var' in frame_data:
						frame_data['mask_var'] = None
					frame_data['frame'].destroy()
				elif hasattr(frame_data, '__len__') and len(frame_data) > 0:
					# Handle old tuple format
					frame_data[0].destroy()
			except Exception as e:
				print(f"Error destroying frame: {e}")

		self.experiment_frames = []

		if not self.experiments:
			return

		# Initialize experiment states if not exists
		if not hasattr(self, 'experiment_states'):
			self.experiment_states = {}
		if not hasattr(self, 'thread_safe_experiment_states'):
			self.thread_safe_experiment_states = {}

		# Calculate column widths based on content
		max_exp_name_width = max(len(name) for name in self.experiments.keys()) + 2
		max_test_name_width = max(len(data.get('Test Name', '')) for data in self.experiments.values()) + 2

		# Ensure minimum widths
		exp_name_width = max(15, min(25, max_exp_name_width))
		test_name_width = max(20, min(40, max_test_name_width))

		for experiment_name, experiment_data in self.experiments.items():
			data = experiment_data

			# Store state as primitive data, not Tkinter variables
			enabled_status = data.get('Experiment', "Disabled").lower() == 'enabled'
			self.experiment_states[experiment_name] = enabled_status

			# Main experiment frame - use ttk.Frame for consistent theming
			frame = ttk.Frame(self.experiment_container, padding=(5, 2))
			frame.pack(fill=tk.X, pady=1, padx=2)

			# Configure grid weights for proper expansion
			frame.grid_columnconfigure(2, weight=1)  # Test name column expands

			# Create Tkinter variable for UI only (not passed to threads)
			enabled_var = tk.BooleanVar(value=enabled_status)

			# Checkbox with lambda that captures experiment_name
			checkbox = ttk.Checkbutton(frame, variable=enabled_var,
									command=lambda name=experiment_name, var=enabled_var:
									self._update_experiment_state(name, var.get()))
			checkbox.grid(row=0, column=0, sticky="w", padx=(0, 8))

			# Experiment name - fixed width based on content
			name_label = ttk.Label(frame, text=experiment_name, width=exp_name_width,
								font=("Arial", 9))
			name_label.grid(row=0, column=1, sticky="w", padx=(0, 8))

			# Test name (expandable) - minimum width based on content
			test_name_text = data.get('Test Name', '')
			test_name_label = ttk.Label(frame, text=test_name_text, width=test_name_width,
									font=("Arial", 9), foreground="blue")
			test_name_label.grid(row=0, column=2, sticky="ew", padx=(0, 8))

			# Test mode
			mode_label = ttk.Label(frame, text=data.get('Test Mode', ''), width=8,
								font=("Arial", 9))
			mode_label.grid(row=0, column=3, sticky="w", padx=(0, 8))

			# Test type
			type_label = ttk.Label(frame, text=data.get('Test Type', ''), width=8,
								font=("Arial", 9))
			type_label.grid(row=0, column=4, sticky="w", padx=(0, 8))

			# Edit button
			edit_button = ttk.Button(frame, text="Edit", width=6,
								command=lambda d=data: self.edit_experiment(d))
			edit_button.grid(row=0, column=5, sticky="w", padx=(0, 8))

			# Mask dropdown - store mask selection in experiment_states
			mask_var = tk.StringVar()

			current_mask_selection = "Default"
			external_mask = data.get('External Mask')

			if external_mask is not None:
				# Look for the mask name that corresponds to this mask data
				for mask_name, mask_data in self.mask_dict.items():
					if mask_data == external_mask:
						current_mask_selection = mask_name
						break

			mask_var.set(current_mask_selection)

			mask_dropdown = ttk.Combobox(frame, textvariable=mask_var,
									values=list(self.mask_dict.keys()),
									width=10, state="readonly", font=("Arial", 8))
			mask_dropdown.grid(row=0, column=6, sticky="w", padx=(0, 8))
			mask_dropdown.bind('<<ComboboxSelected>>',
							lambda e, d=data, mv=mask_var, en=experiment_name:
							self.update_mask(mv.get(), d, mv, en))

			# Status label - Use tk.Label for color support
			run_label = tk.Label(frame, text="Idle", bg="lightgray", fg="black",
							width=12, relief=tk.GROOVE, borderwidth=1,
							font=("Arial", 8))
			run_label.grid(row=0, column=7, sticky="ew", padx=(8, 0))

			# Store frame data in new format (dict instead of tuple)
			frame_data = {
				'frame': frame,
				'run_label': run_label,
				'enabled_var': enabled_var,  # Keep for UI updates only
				'data': data,
				'mask_var': mask_var,
				'experiment_name': experiment_name,
				'checkbox': checkbox,
				'name_label': name_label,
				'test_name_label': test_name_label,
				'mode_label': mode_label,
				'type_label': type_label,
				'edit_button': edit_button,
				'mask_dropdown': mask_dropdown
			}

			self.experiment_frames.append(frame_data)

			# Register tkinter variables
			self.registered_tkinter_variables.append(enabled_var)
			self.registered_tkinter_variables.append(mask_var)

			# Update widget states based on enabled status
			self.toggle_experiment(frame_data, enabled_status)

		# Update scroll region after adding all experiments
		self.root.after(10, lambda: self._update_scroll_region(self.experiment_canvas))

		# Auto-size window after loading experiments
		self.root.after(100, self.auto_size_window)

	# Method for thread-safe state updates
	def _update_experiment_state(self, experiment_name: str, enabled: bool):
		"""Update experiment state thread-safely"""
		self.experiment_states[experiment_name] = enabled
		self.thread_safe_experiment_states[experiment_name] = enabled

		# Update the data
		if experiment_name in self.experiments:
			self.experiments[experiment_name]['Experiment'] = 'Enabled' if enabled else 'Disabled'

		# Find the frame_data for this experiment and update its visual state
		for frame_data in self.experiment_frames:
			if isinstance(frame_data, dict) and frame_data.get('experiment_name') == experiment_name:
				self.toggle_experiment(frame_data, enabled)
				break

		# Log the change
		status = "enabled" if enabled else "disabled"
		self.log_status(f"Experiment '{experiment_name}' {status}")

	def toggle_experiment(self, frame_data, enabled_status):
		"""Toggle experiment widgets based on enabled status"""
		try:
			# Determine the state based on enabled_status
			state = tk.NORMAL if enabled_status else tk.DISABLED

			# Update all widgets except checkbox and run_label
			widgets_to_update = ['name_label', 'test_name_label', 'mode_label',
							'type_label', 'edit_button', 'mask_dropdown']

			for widget_name in widgets_to_update:
				if widget_name in frame_data:
					widget = frame_data[widget_name]
					try:
						if widget and widget.winfo_exists():
							# Special handling for different widget types
							if widget_name == 'mask_dropdown':
								# For combobox, use 'readonly' when enabled, 'disabled' when disabled
								widget.configure(state='readonly' if enabled_status else 'disabled')
							else:
								# For labels and buttons
								widget.configure(state=state)

							# Update visual appearance for labels
							if 'label' in widget_name:
								if enabled_status:
									# Restore normal colors
									if widget_name == 'test_name_label':
										widget.configure(foreground="blue")
									else:
										widget.configure(foreground="black")
								else:
									# Gray out disabled labels
									widget.configure(foreground="gray")

					except Exception as e:
						print(f"Error updating {widget_name}: {e}")

		except Exception as e:
			print(f"Error in toggle_experiment: {e}")

	def edit_experiment(self, data):
		"""Open experiment editor with improved data handling"""
		try:
			# Find the experiment name for this data
			experiment_name = None
			for name, exp_data in self.experiments.items():
				if exp_data == data:
					experiment_name = name
					break

			if not experiment_name:
				experiment_name = data.get('Test Name', 'Unknown')

			# Create a callback that includes the experiment name
			def update_callback(updated_data):
				# Update the main experiments dictionary
				if experiment_name in self.experiments:
					self.experiments[experiment_name] = updated_data

				# Update the display
				self.update_experiment(updated_data)

				# Update experiment states
				enabled_status = updated_data.get('Experiment', "Disabled").lower() == 'enabled'
				self.experiment_states[experiment_name] = enabled_status
				self.thread_safe_experiment_states[experiment_name] = enabled_status

			# Callback for adding new experiments
			def add_new_experiment_callback(new_name, new_data):
				# Add to experiments dictionary
				self.experiments[new_name] = new_data

				# Update experiment states
				enabled_status = new_data.get('Experiment', "Disabled").lower() == 'enabled'
				self.experiment_states[new_name] = enabled_status
				self.thread_safe_experiment_states[new_name] = enabled_status

				# Refresh the experiment rows to show the new experiment
				self.create_experiment_rows()

				self.log_status(f"New experiment added: {new_name}")

			# Determine config file based on Framework product
			config_file = f"{self.product}ControlPanelConfig.json"
			print(f"[CONTROL PANEL] Opening edit window with product='{self.product}', config_file='{config_file}'")

			# Open in edit mode
			EditExperimentWindow(self.root, data, update_callback, add_new_experiment_callback, mode="edit", config_file=config_file)
		except Exception as e:
			self.log_status(f"[ERROR] Failed to open experiment editor: {e}")
			messagebox.showerror("Error", f"Failed to open experiment editor: {e}")

	def add_new_experiment(self):
		"""Add a new experiment using the edit window"""
		try:
			# Create empty experiment data with reasonable defaults
			new_experiment_data = self.create_default_experiment_data()

			# Create callbacks for the edit window
			def update_callback(updated_data):
				# This won't be used for new experiments, but needed for compatibility
				pass

			def add_new_experiment_callback(new_name, new_data):
				# Add to experiments dictionary
				self.experiments[new_name] = new_data

				# Update experiment states
				enabled_status = new_data.get('Experiment', "Disabled").lower() == 'enabled'
				self.experiment_states[new_name] = enabled_status
				self.thread_safe_experiment_states[new_name] = enabled_status

				# Enable save button since we now have experiments
				self.saveas_button.configure(state=tk.NORMAL)

				# Refresh the experiment rows to show the new experiment
				self.create_experiment_rows()

				self.log_status(f"New experiment added: {new_name}")

			# Determine config file based on Framework product
			config_file = f"{self.product}ControlPanelConfig.json"
			print(f"[CONTROL PANEL] Opening add new window with product='{self.product}', config_file='{config_file}'")

			# Open edit window in "add new" mode
			EditExperimentWindow(self.root, new_experiment_data, update_callback,
								add_new_experiment_callback, mode="add_new", config_file=config_file)

		except Exception as e:
			self.log_status(f"[ERROR] Failed to open add experiment window: {e}")
			messagebox.showerror("Error", f"Failed to open add experiment window: {e}")

	def create_default_experiment_data(self):
		"""Create default experiment data for new experiments"""
		# Get the config to know what fields exist
		current_dir = os.path.dirname(__file__)
		# Load from DebugFramework's PPV/configs folder using product
		ppv_config_dir = os.path.join(current_dir, '..', 'PPV', 'configs')
		config_file = f"{self.product}ControlPanelConfig.json"
		config_path = os.path.join(ppv_config_dir, config_file)
		# Fallback to old location
		if not os.path.exists(config_path):
			config_path = os.path.join(current_dir, config_file)

		try:
			with open(config_path) as f:
				config_data = json.load(f)
			# Support both old data_types and new field_configs formats
			if 'field_configs' in config_data:
				field_configs = config_data['field_configs']
			else:
				# Old format - convert to new format
				field_configs = {}
				for field, types in config_data.get('data_types', {}).items():
					field_type = 'str'
					if 'int' in types:
						field_type = 'int'
					elif 'float' in types:
						field_type = 'float'
					elif 'bool' in types:
						field_type = 'bool'
					field_configs[field] = {'type': field_type, 'default': ''}
		except:
			# Fallback if config not available
			field_configs = {}

		new_experiment_data = {}

		for field, field_config in field_configs.items():
			field_type = field_config.get('type', 'str')
			# Use config default if available
			default_value = field_config.get('default', '')

			if field == 'Experiment':
				new_experiment_data[field] = 'Enabled'
			elif field == 'Test Name':
				new_experiment_data[field] = 'New_Experiment'
			elif default_value:
				# Use the default from config
				new_experiment_data[field] = default_value
			elif field_type == 'bool':
				new_experiment_data[field] = False
			elif field_type == 'int':
				# Set reasonable defaults for some fields
				if field in ['Test Number']:
					new_experiment_data[field] = 1
				elif field in ['Test Time']:
					new_experiment_data[field] = 30
				elif field in ['COM Port']:
					new_experiment_data[field] = 1
				elif field in ['Linux Content Wait Time']:
					new_experiment_data[field] = 10
				else:
					new_experiment_data[field] = ''
			elif field_type == 'float':
				new_experiment_data[field] = ''
			elif field in ['Pass String']:
				new_experiment_data[field] = 'Test Complete'
			elif field in ['Fail String']:
				new_experiment_data[field] = 'Test Failed'
			else:
				new_experiment_data[field] = ''

		return new_experiment_data

	def update_experiment(self, updated_data):
		"""Update the experiment data and refresh the display - FIXED for new dict format"""
		try:
			for frame_data in self.experiment_frames:
				# Handle new dict format
				if isinstance(frame_data, dict):
					data = frame_data.get('data')
					experiment_name = frame_data.get('experiment_name')
					enabled_var = frame_data.get('enabled_var')

					# Check if this is the experiment we're updating
					if data == updated_data or experiment_name == updated_data.get('Test Name'):
						# Update the stored data reference
						frame_data['data'] = updated_data

						# Update the display with new data
						enabled_status = updated_data.get('Experiment', "Disabled").lower() == 'enabled'
						if enabled_var:
							enabled_var.set(enabled_status)

						# Update experiment state
						if experiment_name:
							self.experiment_states[experiment_name] = enabled_status

						# Update the labels in the frame
						frame = frame_data.get('frame')
						if frame and frame.winfo_exists():
							# Update test name label (column 2)
							test_name_label = frame_data.get('test_name_label')
							if test_name_label and test_name_label.winfo_exists():
								test_name_label.configure(text=updated_data.get('Test Name', ''))

							# Update mode label (column 3)
							mode_label = frame_data.get('mode_label')
							if mode_label and mode_label.winfo_exists():
								mode_label.configure(text=updated_data.get('Test Mode', ''))

							# Update type label (column 4)
							type_label = frame_data.get('type_label')
							if type_label and type_label.winfo_exists():
								type_label.configure(text=updated_data.get('Test Type', ''))

						# Update widget states based on enabled status
						self.toggle_experiment(frame_data, enabled_status)

						self.log_status(f"Updated experiment: {updated_data.get('Test Name', 'Unknown')}")
						break

				# Handle old tuple format (for backward compatibility)
				elif hasattr(frame_data, '__len__') and len(frame_data) >= 6:
					try:
						frame, run_label, enabled_var, data, mask_var, experiment_name = frame_data[:6]

						if data == updated_data:
							# Update the display with new data
							enabled_status = updated_data.get('Experiment', "Disabled").lower() == 'enabled'
							enabled_var.set(enabled_status)

							# Update labels using grid info to find the right widgets
							children = frame.winfo_children()
							if len(children) >= 5:
								# Test name label (index 2)
								if len(children) > 2:
									children[2].configure(text=updated_data.get('Test Name', ''))
								# Mode label (index 3)
								if len(children) > 3:
									children[3].configure(text=updated_data.get('Test Mode', ''))
								# Type label (index 4)
								if len(children) > 4:
									children[4].configure(text=updated_data.get('Test Type', ''))
							break

					except ValueError as e:
						print(f"Error updating old format frame: {e}")
						continue

		except Exception as e:
			self.log_status(f"[ERROR] Failed to update experiment display: {e}")
			print(f"Error in update_experiment: {e}")

	def save_config(self):
		# Open a dialog to select the save location
		file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
		if file_path:
			Convert_xlsx_to_json(file_path, self.experiments)

	# ==================== LOGGING & STATUS MANAGEMENT ====================

	def log_status(self, message, level: str = "info"):
		"""Add message to status log with timestamp"""
		self.status_panel.log_status(message, level)

	def clear_status_log(self):
		"""Clear the status log"""
		self.status_panel.clear_status_log()

	def save_status_log(self):
		"""Save status log to file"""
		self.status_panel.save_status_log()

	def _display_experiment_summary(self, summary_data):
		"""Display experiment summary in status log"""
		self.log_status("=" * 40)
		self.log_status(f"SUMMARY: {summary_data['test_name']}")
		self.log_status("=" * 40)
		self.log_status(f"Strategy: {summary_data['strategy_type']}")
		self.log_status(f"Total Tests: {summary_data['total_tests']}")
		self.log_status(f"Success Rate: {summary_data['success_rate']}%")

		# Display status breakdown
		self.log_status("Status Breakdown:")
		for status, count in summary_data['status_counts'].items():
			percentage = (count / summary_data['total_tests'] * 100) if summary_data['total_tests'] > 0 else 0
			self.log_status(f"  {status}: {count} ({percentage:.1f}%)")

		# Display failure patterns if any
		if summary_data['failure_patterns']:
			self.log_status("Top Failure Patterns:")
			for pattern, count in list(summary_data['failure_patterns'].items())[:3]:
				self.log_status(f"  {pattern}: {count} occurrences")

		if summary_data['first_fail_iteration']:
			self.log_status(f"First Failure: Iteration {summary_data['first_fail_iteration']}")

		execution_time = summary_data.get('execution_time', 0)
		if execution_time > 0:
			self.log_status(f"Execution Time: {execution_time:.1f} seconds")

		self.log_status("=" * 40)

	# ==================== WINDOW & UI MANAGEMENT ====================

	def auto_size_window(self):
		"""Automatically size window based on content"""
		# Update all widgets to get their required sizes
		self.root.update_idletasks()

		# Calculate required width based on content
		left_width = max(800, self.left_frame.winfo_reqwidth())  # Minimum width for left panel
		right_width = max(400, self.right_frame.winfo_reqwidth())  # Minimum 400px for right panel

		# Add some padding
		total_width = left_width + right_width + 50

		# Calculate height based on content, but don't make it too tall
		content_height = self.root.winfo_reqheight()
		screen_height = self.root.winfo_screenheight()
		max_height = int(screen_height * 0.9)  # Max 90% of screen height
		total_height = min(max_height, max(700, content_height + 50))

		# Set window size
		self.root.geometry(f"{total_width}x{total_height}")

		# Position the sash to give right panel the space it needs
		self.root.after(50, lambda: self.main_paned.sashpos(0, total_width - right_width - 20))

	def _update_scroll_region(self, canvas):
		"""Update canvas scroll region"""
		canvas.configure(scrollregion=canvas.bbox("all"))

	def _update_canvas_scroll_region(self, canvas):
		"""Update canvas window width to match canvas width"""
		canvas_width = canvas.winfo_width()
		canvas.itemconfig(self.experiment_canvas_window, width=canvas_width)

	def on_closing(self):
		"""Enhanced cleanup to prevent Tkinter variable errors"""
		try:
			print("Starting cleanup process...")
			self._cleanup_in_progress = True

			# CRITICAL: Stop the MainThreadHandler first
			if hasattr(self, 'main_thread_handler'):
				print("Cleaning up MainThreadHandler...")
				self.main_thread_handler.cleanup()
				# Give it a moment to cleanup
				time.sleep(0.1)

			# Stop status updates first
			if hasattr(self, 'main_thread_handler'):
				print("Disabling status updates...")
				self.main_thread_handler.disable_callbacks()

			# Cancel any running operations
			if hasattr(self, 'cancel_requested'):
				self.cancel_requested.set()

			# Stop thread first
			self.thread_active = False

			# Wait for thread to finish with timeout
			if self.framework_thread and self.framework_thread.is_alive():
				self.framework_thread.join(timeout=5.0)
				if self.framework_thread.is_alive():
					print("Warning: Thread did not stop gracefully")

			# Clear all queues
			self._clear_queue(self.command_queue)
			self._clear_queue(self.status_queue)

			# EDIT: Add framework cleanup
			self._cleanup_previous_framework()

			# Clean up Framework instance through manager
			#if hasattr(self, 'framework_manager') and self.framework_manager:
			#	self.framework_manager.cleanup_current_instance()
			#	self.framework_manager = None

			#self.framework_api = None
			#self.framework_utils = None

			# CRITICAL: Schedule Tkinter variable cleanup in main thread
			self.root.after_idle(self._cleanup_tkinter_variables)

			# Destroy widgets properly
			self._cleanup_widgets()

		except Exception as e:
			print(f"Cleanup error: {e}")
		finally:
			try:
				# Force garbage collection before destroying
				import gc
				gc.collect()

				# Small delay to let cleanup complete
				time.sleep(0.1)

				#self.root.quit()
				#self.root.destroy()
				self.root.after_idle(self._final_destroy)
			except:
				pass

	def _cleanup_previous_framework(self):
		"""Clean up previous framework instance"""
		try:
			if self.current_framework_instance_id:
				self.log_status(f"Cleaning up framework instance: {self.current_framework_instance_id}")

				if self.framework_api:
					try:
						state = self.framework_api.get_current_state()
						if state.get('is_running'):
							self.framework_api.cancel_experiment()
						time.sleep(0.1)
					except:
						pass

				if self.framework_manager:
					try:
						self.framework_manager.cleanup_current_instance("cleanup_before_new_run")
					except:
						pass

				self.framework_api = None
				self.current_framework_instance_id = None

				import gc
				gc.collect()

		except Exception as e:
			self.log_status(f"Framework cleanup error: {e}")

	def _cleanup_tkinter_variables(self):
		"""Clean up Tkinter variables safely in main thread"""
		try:
			print("Cleaning up Tkinter variables...")

			# Clear registered variables
			if hasattr(self, 'registered_tkinter_variables'):
				for var in self.registered_tkinter_variables:
					var = None
				self.registered_tkinter_variables.clear()

			# Clear experiment frame variables
			for frame_data in getattr(self, 'experiment_frames', []):
				if isinstance(frame_data, dict):
					frame_data['enabled_var'] = None
					frame_data['mask_var'] = None

			# Clear main variables
			vars_to_clear = ['stop_on_fail_var', 'check_unit_data_var', 'upload_unit_data_var',
							'auto_scroll_var', 'overall_progress_var', 'iteration_progress_var']

			for var_name in vars_to_clear:
				if hasattr(self, var_name):
					setattr(self, var_name, None)

			# Clear thread-safe data
			if hasattr(self, 'thread_safe_experiment_states'):
				self.thread_safe_experiment_states.clear()

			print("Variables cleaned up successfully")

		except Exception as e:
			print(f"Variable cleanup error: {e}")

	def _clear_queue(self, q):
		"""Clear a queue safely"""
		try:
			while True:
				q.get_nowait()
		except queue.Empty:
			pass

	def _cleanup_widgets(self):
		"""Clean up widgets to prevent variable errors"""
		try:
			# Clear experiment frames
			for frame_data in getattr(self, 'experiment_frames', []):
				try:
					if 'checkbox_var' in frame_data:
						del frame_data['checkbox_var']
					if 'frame' in frame_data:
						frame_data['frame'].destroy()
				except:
					pass

			self.experiment_frames = []

		except Exception as e:
			print(f"Widget cleanup error: {e}")

	# Deprecated -- Check and remove
	def cleanup_variables(self):
		"""Clean up Tkinter variables safely"""
		try:
			# Clear variable references
			if hasattr(self, 'input_vars'):
				self.input_vars.clear()

			# Clear other variable collections
			for frame, run_label, enabled_var, data, mask_var, experiment_name in self.experiment_frames:
				try:
					del enabled_var
					del mask_var
				except:
					pass

		except Exception as e:
			print(f"Error cleaning up variables: {e}")

	# Deprecated
	def _cleanup_tkinter_variables_old(self):
		"""Clean up Tkinter variables safely in main thread"""
		try:
			print("Cleaning up Tkinter variables in main thread...")

			# Clear experiment frame variables
			for frame_data in getattr(self, 'experiment_frames', []):
				try:
					if isinstance(frame_data, dict):
						# Clear variables without accessing them
						if 'enabled_var' in frame_data:
							frame_data['enabled_var'] = None
						if 'mask_var' in frame_data:
							frame_data['mask_var'] = None
				except Exception as e:
					print(f"Error cleaning frame variables: {e}")

			# Clear other Tkinter variables by setting to None
			vars_to_clear = [
				'stop_on_fail_var', 'check_unit_data_var', 'upload_unit_data_var',
				'auto_scroll_var', 'overall_progress_var', 'iteration_progress_var'
			]

			for var_name in vars_to_clear:
				if hasattr(self, var_name):
					try:
						setattr(self, var_name, None)
					except Exception as e:
						print(f"Error clearing {var_name}: {e}")

			print("Tkinter variables cleaned up successfully")

		except Exception as e:
			print(f"Error in Tkinter variable cleanup: {e}")

	def _final_destroy(self):
		"""Final destruction in main thread"""
		try:
			self.root.quit()
			self.root.destroy()
		except Exception as e:
			print(f"Final destroy error: {e}")

	# ==================== EXTERNAL INTEGRATIONS ====================

	def open_settings_window(self):
		SettingsWindow(self.root, self.S2T_CONFIG, self.update_configuration)

	def open_power_control_window(self):
		PowerControlWindow(self.root, self.Framework_utils)

	def open_mask_management(self):
		MaskManagementWindow(self.root, self.mask_dict, self.update_mask_dict, self.Framework_utils)

	def update_mask_dict(self, updated_mask_dict):

		print('Updating Masking Data with new Entry:')
		print(f'Old: {self.mask_dict.keys()}')
		self.mask_dict = updated_mask_dict
		print(f'New: {self.mask_dict.keys()}')
		self.refresh_experiment_rows()

	def refresh_experiment_rows(self):
		"""Refresh experiment rows with updated mask options"""
		try:
			for frame_data in self.experiment_frames:
				# Handle new dict format
				if isinstance(frame_data, dict):
					mask_dropdown = frame_data.get('mask_dropdown')
					data = frame_data.get('data')
					mask_var = frame_data.get('mask_var')
					experiment_name = frame_data.get('experiment_name')

					if mask_dropdown and mask_dropdown.winfo_exists():
						# Update the combobox values
						mask_dropdown['values'] = list(self.mask_dict.keys())

						# Reset to default if current selection is no longer valid
						current_selection = mask_var.get() if mask_var else ''
						if current_selection not in self.mask_dict.keys():
							mask_var.set('Default')
							if data:
								data['External Mask'] = None

				# Handle old tuple format (if any still exist)
				elif hasattr(frame_data, '__len__') and len(frame_data) >= 6:
					try:
						frame, run_label, enabled_var, data, mask_var, experiment_name = frame_data[:6]
						# Find the mask dropdown widget (should be at column 6)
						for child in frame.winfo_children():
							if isinstance(child, ttk.Combobox) and child.grid_info().get('column') == 6:
								child['values'] = list(self.mask_dict.keys())
								current_selection = mask_var.get() if mask_var else ''
								if current_selection not in self.mask_dict.keys():
									mask_var.set('Default')
									if data:
										data['External Mask'] = None
								break
					except ValueError as e:
						print(f"Error updating old format frame: {e}")
						continue

		except Exception as e:
			self.log_status(f"[ERROR] Failed to refresh experiment rows: {e}")
			print(f"Error in refresh_experiment_rows: {e}")

	def check_ipc(self):
		if self.Framework_utils:
			self.Framework_utils.refresh_ipc()
		else:
			print('Refreshing SV and Unlocking IPC')

	def update_configuration(self, updated_config):

		self.S2T_CONFIG = updated_config
		print("Configuration updated:", self.S2T_CONFIG)

	def update_mask(self, selected_mask, data, mask_var, experiment_name):
		"""Update mask for a specific experiment"""
		try:
			if selected_mask == "Default" or not selected_mask or not selected_mask.strip():
				data['External Mask'] = None
				self.log_status(f"[MASK] Removed external mask from '{experiment_name}'")
			else:
				if selected_mask in self.mask_dict:
					mask_value = self.mask_dict[selected_mask]
					# Ensure mask_value is not empty
					if mask_value and str(mask_value).strip():
						data['External Mask'] = mask_value
						self.log_status(f"[MASK] Applied mask '{selected_mask}' to '{experiment_name}'")
					else:
						data['External Mask'] = None
						self.log_status(f"[MASK] Warning: Mask '{selected_mask}' not found")

				else:
					data['External Mask'] = None
					self.log_status(f"[MASK] Warning: Mask '{selected_mask}' not found")


			# Update the mask_var for this specific experiment
			mask_var.set(selected_mask if selected_mask and selected_mask != "Default" else "Default")

			# Update the experiment in the main experiments dictionary
			if experiment_name in self.experiments:
				self.experiments[experiment_name] = data

			print(f"Experiment '{experiment_name}' External Mask --> {selected_mask}")
			print(f"\tValue --> {data.get('External Mask')}")

		except Exception as e:
			self.log_status(f"[ERROR] Failed to update mask for '{experiment_name}': {e}")

	def test_ttl(self, ):

		TestTTLWindow(self.root, self.experiments, self.Framework_utils)
		#EditExperimentWindow(self.root, data)
		#pass

	# ==================== TESTING & DEBUG ====================

	def verify_animations(self):
		"""Comprehensive animation verification for dual progress bar system and enhanced status animations"""

		self.log_status("[TEST] Starting comprehensive animation verification...")

		# Store original values to restore later
		original_total_experiments = getattr(self, 'total_experiments', 0)
		original_current_experiment_index = getattr(self, 'current_experiment_index', 0)
		original_current_iteration = getattr(self, 'current_iteration', 0)
		original_total_iterations = getattr(self, 'total_iterations_in_experiment', 0)

		# Set up test values
		self.total_experiments = 5
		self.current_experiment_index = 0
		self.total_iterations_in_experiment = 10
		self.current_iteration = 0
		self.current_iteration_progress = 0.0
		self.strategy_progress = 0

		# Test sequence timing
		test_delays = {
			'dual_progress': 0,
			'status_labels': 8000,
			'button_states': 16000,
			'experiment_status': 24000,
			'progress_bar_styles': 32000,
			'continuous_animations': 40000,
			'cleanup': 50000
		}

		# === TEST 1: DUAL PROGRESS BAR SYSTEM ===
		def test_dual_progress():
			self.log_status("[TEST] Testing dual progress bar system...")

			# Test overall progress (simulating 5 experiments)
			def simulate_overall_progress():
				for exp_idx in range(5):
					self.current_experiment_index = exp_idx

					# Simulate iterations within each experiment
					for iter_idx in range(1, 11):  # 10 iterations per experiment
						self.current_iteration = iter_idx

						# Test iteration progress
						iteration_progress = (iter_idx / 10) * 100
						self.root.after(
							(exp_idx * 10 + iter_idx) * 200,
							lambda prog=iteration_progress, it=iter_idx: _test_iteration_progress(prog, it)
						)

					# Complete experiment
					self.root.after(
						(exp_idx * 10 + 10) * 200 + 100,
						lambda idx=exp_idx: _test_experiment_complete(idx)
					)

			simulate_overall_progress()

		def _test_iteration_progress(progress, iteration):
			"""Test iteration progress updates"""
			try:
				progress_data = {
					'progress_percent': progress,
					'current_iteration': iteration,
					'total_iterations': 10
				}
				self._coordinate_progress_updates('strategy_progress', progress_data)

				# Update phase label for visual feedback
				if progress < 30:
					self.phase_label.configure(text="[BOOT] Initializing", foreground="orange")
					self.iteration_progress_bar.configure(style="Iteration.Boot.Horizontal.TProgressbar")
				elif progress < 70:
					self.phase_label.configure(text="[TEST] Executing", foreground="green")
					self.iteration_progress_bar.configure(style="Iteration.Running.Horizontal.TProgressbar")
				else:
					self.phase_label.configure(text="[COMPLETE] Finishing", foreground="blue")
					self.iteration_progress_bar.configure(style="Iteration.Horizontal.TProgressbar")

			except Exception as e:
				self.log_status(f"[ERROR] Iteration progress test failed: {e}")

		def _test_experiment_complete(exp_index):
			"""Test experiment completion"""
			try:
				self.current_experiment_index = exp_index + 1
				self.current_iteration_progress = 1.0
				self._coordinate_progress_updates('experiment_complete', {})
				self.log_status(f"[TEST] Completed experiment {exp_index + 1}/5")
			except Exception as e:
				self.log_status(f"[ERROR] Experiment complete test failed: {e}")

		# === TEST 2: STATUS LABEL ANIMATIONS ===
		def test_status_labels():
			self.log_status("[TEST] Testing enhanced status label animations...")

			status_sequence = [
				({'text': ' Starting ', 'bg': '#4CAF50', 'fg': 'white'}, 0),
				({'text': ' Running ', 'bg': '#BF0000', 'fg': 'white'}, 1500),
				({'text': ' Halted ', 'bg': 'orange', 'fg': 'black'}, 3000),
				({'text': ' Resumed ', 'bg': '#BF0000', 'fg': 'white'}, 4500),
				({'text': ' Completed ', 'bg': '#006400', 'fg': 'white'}, 6000),
				({'text': ' Ready ', 'bg': 'white', 'fg': 'black'}, 7500)
			]

			for status_config, delay in status_sequence:
				self.root.after(delay, lambda s=status_config: self._coordinate_status_updates(s))

		# === TEST 3: BUTTON STATE ANIMATIONS ===
		def test_button_states():
			self.log_status("[TEST] Testing button state animations...")

			button_sequence = [
				('disabled_during_execution', 0),
				('specific_button_update', 2000),
				('enable_after_completion', 4000),
				('default_state', 6000)
			]

			# Test specific button updates
			specific_updates = {
				'hold_button': {'text': 'Continue', 'style': 'Continue.TButton', 'state': 'normal'},
				'end_button': {'text': 'Ending...', 'style': 'EndActive.TButton', 'state': 'disabled'},
				'cancel_button': {'text': 'Cancelling...', 'state': 'disabled'}
			}

			for update_type, delay in button_sequence:
				if update_type == 'specific_button_update':
					self.root.after(delay, lambda: self._coordinate_button_states(update_type, specific_updates))
				else:
					self.root.after(delay, lambda ut=update_type: self._coordinate_button_states(ut))

		# === TEST 4: EXPERIMENT STATUS ANIMATIONS ===
		def test_experiment_status():
			self.log_status("[TEST] Testing enhanced experiment status animations...")

			if not self.experiment_frames:
				self.log_status("[WARN] No experiment frames available for testing")
				return

			# Test with first 3 experiments (or all if less than 3)
			test_experiments = self.experiment_frames[:min(3, len(self.experiment_frames))]

			status_animations = [
				('Idle', 'lightgray', 'black', 'reset_clean', 0),
				('In Progress', '#00008B', 'white', 'pulse_continuous', 1000),
				('Running', '#00008B', 'white', 'pulse_continuous', 3000),
				('Done', '#006400', 'white', 'success_flash', 5000),
				('Fail', 'yellow', 'black', 'error_flash', 7000),
				('Cancelled', 'gray', 'white', 'cancel_fade', 9000),
				('Halted', 'orange', 'black', 'warning_pulse', 11000),
				('Idle', 'lightgray', 'black', 'reset_clean', 13000)
			]

			for i, frame_data in enumerate(test_experiments):
				exp_name = frame_data['experiment_name']

				for status, bg_color, fg_color, animation_type, base_delay in status_animations:
					delay = base_delay + (i * 200)  # Stagger animations for multiple experiments
					self.root.after(
						delay,
						lambda n=exp_name, s=status, bg=bg_color, fg=fg_color:
						self._update_experiment_status_safe(n, s, bg, fg)
					)

		# === TEST 5: PROGRESS BAR STYLE ANIMATIONS ===
		def test_progress_bar_styles():
			self.log_status("[TEST] Testing progress bar style animations...")

			style_sequence = [
				# Overall progress bar styles
				('overall', "Overall.Running.Horizontal.TProgressbar", 0),
				('overall', "Overall.Warning.Horizontal.TProgressbar", 1500),
				('overall', "Overall.Error.Horizontal.TProgressbar", 3000),
				('overall', "Overall.Horizontal.TProgressbar", 4500),

				# Iteration progress bar styles
				('iteration', "Iteration.Boot.Horizontal.TProgressbar", 1000),
				('iteration', "Iteration.Running.Horizontal.TProgressbar", 2500),
				('iteration', "Iteration.Error.Horizontal.TProgressbar", 4000),
				('iteration', "Iteration.Horizontal.TProgressbar", 5500)
			]

			for bar_type, style_name, delay in style_sequence:
				if bar_type == 'overall':
					self.root.after(delay, lambda s=style_name: self.overall_progress_bar.configure(style=s))
				else:
					self.root.after(delay, lambda s=style_name: self.iteration_progress_bar.configure(style=s))

		# === TEST 6: CONTINUOUS ANIMATIONS ===
		def test_continuous_animations():
			self.log_status("[TEST] Testing continuous animations (pulse, fade, etc.)...")

			# Test continuous pulse on first experiment
			if self.experiment_frames:
				exp_name = self.experiment_frames[0]['experiment_name']

				# Start continuous pulse
				self.root.after(0, lambda: self._update_experiment_status_safe(exp_name, "Running", "#00008B", "white"))

				# Test interrupting continuous animation
				self.root.after(3000, lambda: self._update_experiment_status_safe(exp_name, "Done", "#006400", "white"))

				# Test fade animation
				self.root.after(5000, lambda: self._update_experiment_status_safe(exp_name, "Cancelled", "gray", "white"))

			# Test progress bar continuous updates
			def continuous_progress_test():
				for i in range(101):
					# Update both progress bars simultaneously
					self.root.after(i * 50, lambda p=i: _test_continuous_progress(p))

			continuous_progress_test()

		def _test_continuous_progress(progress):
			"""Test continuous progress updates - FIXED"""
			try:
				# Update iteration progress
				if hasattr(self, 'iteration_progress_var'):
					self.iteration_progress_var.set(progress)
				if hasattr(self, 'iteration_percentage_label'):
					self.iteration_percentage_label.configure(text=f"{progress}%")

				# Update overall progress (simulate being on experiment 3 of 5)
				overall_progress = (2 + (progress / 100)) / 5 * 100  # 2 complete + current progress
				if hasattr(self, 'overall_progress_var'):
					self.overall_progress_var.set(overall_progress)
				if hasattr(self, 'overall_percentage_label'):
					self.overall_percentage_label.configure(text=f"{int(overall_progress)}%")

				# Update speed display
				if hasattr(self, 'iteration_speed_label'):
					speed = f"{progress/10:.1f} iter/s" if progress > 0 else ""
					self.iteration_speed_label.configure(text=speed)

				# Update ETA display
				if hasattr(self, 'overall_eta_label'):
					remaining_time = max(0, (100 - overall_progress) * 0.5)  # Simulate ETA
					eta = self._format_time(remaining_time) if remaining_time > 0 else ""
					self.overall_eta_label.configure(text=f"ETA: {eta}" if eta else "")

				# Update colors based on progress
				if hasattr(self, 'iteration_progress_bar'):
					if progress < 30:
						self.iteration_progress_bar.configure(style="Iteration.Boot.Horizontal.TProgressbar")
					elif progress < 70:
						self.iteration_progress_bar.configure(style="Iteration.Running.Horizontal.TProgressbar")
					else:
						self.iteration_progress_bar.configure(style="Iteration.Horizontal.TProgressbar")

			except Exception as e:
				self.log_status(f"[ERROR] Continuous progress test failed: {e}")

		# === TEST 7: CLEANUP AND RESTORATION ===
		def cleanup_and_restore():
			self.log_status("[TEST] Cleaning up and restoring original values...")

			try:
				# Stop any continuous animations
				for frame_data in self.experiment_frames:
					run_label = frame_data['run_label']
					if hasattr(run_label, '_animation_after_id'):
						self.root.after_cancel(run_label._animation_after_id)

				# Restore original values
				self.total_experiments = original_total_experiments
				self.current_experiment_index = original_current_experiment_index
				self.current_iteration = original_current_iteration
				self.total_iterations_in_experiment = original_total_iterations

				# Reset progress bars
				self.overall_progress_var.set(0)
				self.iteration_progress_var.set(0)
				self.overall_percentage_label.configure(text="0%")
				self.iteration_percentage_label.configure(text="0%")
				self.overall_experiment_label.configure(text="(0/0 experiments)")
				self.iteration_progress_label.configure(text="(0/0)")

				# Reset styles
				self.overall_progress_bar.configure(style="Overall.Horizontal.TProgressbar")
				self.iteration_progress_bar.configure(style="Iteration.Horizontal.TProgressbar")

				# Reset status labels
				self._coordinate_status_updates({'text': ' Ready ', 'bg': 'white', 'fg': 'black'})
				self.phase_label.configure(text="", foreground="black")

				# Reset experiment statuses
				self._cleanup_experiment_statuses()

				# Reset buttons
				self._coordinate_button_states('default_state')

				self.log_status("[TEST] Animation verification completed successfully!")

			except Exception as e:
				self.log_status(f"[ERROR] Cleanup failed: {e}")

		# === EXECUTE ALL TESTS ===
		try:
			# Run tests in sequence
			self.root.after(test_delays['dual_progress'], test_dual_progress)
			self.root.after(test_delays['status_labels'], test_status_labels)
			self.root.after(test_delays['button_states'], test_button_states)
			self.root.after(test_delays['experiment_status'], test_experiment_status)
			self.root.after(test_delays['progress_bar_styles'], test_progress_bar_styles)
			self.root.after(test_delays['continuous_animations'], test_continuous_animations)
			self.root.after(test_delays['cleanup'], cleanup_and_restore)

			# Log test schedule
			self.log_status("[TEST] Animation test schedule:")
			self.log_status("[TEST] 0-8s: Dual progress bar system")
			self.log_status("[TEST] 8-16s: Status label animations")
			self.log_status("[TEST] 16-24s: Button state animations")
			self.log_status("[TEST] 24-32s: Experiment status animations")
			self.log_status("[TEST] 32-40s: Progress bar style animations")
			self.log_status("[TEST] 40-50s: Continuous animations")
			self.log_status("[TEST] 50s: Cleanup and restoration")

		except Exception as e:
			self.log_status(f"[ERROR] Animation verification setup failed: {e}")

	# === ADDITIONAL HELPER METHODS FOR TESTING ===

	def _test_animation_coordination(self):
		"""Test animation coordination and conflict resolution"""

		self.log_status("[TEST] Testing animation coordination...")

		try:
			# Test conflicting progress updates
			progress_data_1 = {'progress_percent': 30, 'current_iteration': 3, 'total_iterations': 10}
			progress_data_2 = {'progress_percent': 60, 'current_iteration': 6, 'total_iterations': 10}

			# Send conflicting updates rapidly
			self._coordinate_progress_updates('strategy_progress', progress_data_1)
			self.root.after(100, lambda: self._coordinate_progress_updates('strategy_progress', progress_data_2))

			# Test conflicting status updates
			status_1 = {'text': ' Running ', 'bg': '#BF0000', 'fg': 'white'}
			status_2 = {'text': ' Halted ', 'bg': 'orange', 'fg': 'black'}

			self._coordinate_status_updates(status_1)
			self.root.after(50, lambda: self._coordinate_status_updates(status_2))

			# Test conflicting button updates
			button_data_1 = {'hold_button': {'text': 'Hold', 'state': 'normal'}}
			button_data_2 = {'hold_button': {'text': 'Continue', 'state': 'normal'}}

			self._coordinate_button_states('specific_button_update', button_data_1)
			self.root.after(75, lambda: self._coordinate_button_states('specific_button_update', button_data_2))

			self.log_status("[TEST] Animation coordination test completed")

		except Exception as e:
			self.log_status(f"[ERROR] Animation coordination test failed: {e}")

	def _test_error_recovery(self):
		"""Test animation error recovery"""

		self.log_status("[TEST] Testing animation error recovery...")

		try:
			# Test with invalid progress data
			invalid_progress = {'invalid_key': 'invalid_value'}
			self._coordinate_progress_updates('strategy_progress', invalid_progress)

			# Test with invalid status data
			invalid_status = {'invalid_key': 'invalid_value'}
			self._coordinate_status_updates(invalid_status)

			# Test with non-existent experiment
			self._update_experiment_status_safe('NonExistentExperiment', 'Test', 'red', 'white')

			self.log_status("[TEST] Error recovery test completed")

		except Exception as e:
			self.log_status(f"[ERROR] Error recovery test failed: {e}")

	def debug_progress_state(self):
		"""Enhanced debug method to track experiment counting"""

		if not debug:
			return

		try:
			print("=== PROGRESS DEBUG ===")
			print(f"Progress Bar Value: {self.overall_progress_bar.get()}")
			print(f"Current Experiment Index: {self.current_experiment_index}")
			print(f"Total Experiments: {self.total_experiments}")
			print(f"Current Experiment: {self.current_experiment_index + 1}/{self.total_experiments}")
			print(f"Current Iteration: {self.current_iteration}/{self.total_iterations_in_experiment}")
			print(f"Iteration Progress Weight: {self.current_iteration_progress}")
			print(f"Experiment Name: {self.current_experiment_name}")

			# Calculate what progress should be
			if self.total_experiments > 0:
				exp_progress = self.current_experiment_index / self.total_experiments
				iter_progress = 0
				if self.total_iterations_in_experiment > 0:
					iter_progress = ((self.current_iteration - 1) + self.current_iteration_progress) / self.total_iterations_in_experiment

				overall_progress = (exp_progress + (iter_progress / self.total_experiments)) * 100
				print(f"CALCULATED Progress: {overall_progress:.1f}%")
				print(f"  Exp Progress: {exp_progress:.3f}")
				print(f"  Iter Progress: {iter_progress:.3f}")

			print("======================")
		except Exception as e:
			print(f"Debug error: {e}")

	def _simulate_test_execution(self, exp_data):
		"""Simulate test execution for testing purposes"""
		import random
		time.sleep(random.uniform(2, 5))  # Simulate work
		return random.choice([True, True, True, False])  # 75% success rate

	def debug_button_states(self, context=""):
		"""Debug method to check current button states"""
		if not debug:
			return

		try:
			print(f"=== BUTTON STATES DEBUG {context} ===")

			buttons = ['run_button', 'cancel_button', 'hold_button', 'end_button',
					'power_control_button', 'ipc_control_button']

			for button_name in buttons:
				if hasattr(self, button_name):
					button = getattr(self, button_name)
					if button and button.winfo_exists():
						state = button.cget('state')
						text = button.cget('text')
						print(f"  {button_name}: state='{state}', text='{text}'")
					else:
						print(f"  {button_name}: NOT EXISTS")
				else:
					print(f"  {button_name}: NOT FOUND")

			print(f"  thread_active: {self.thread_active}")
			print("=" * 40)

		except Exception as e:
			print(f"Button state debug error: {e}")
	# ==================== DEPRECATED -- REMOVE ====================
	## Cleaned up

class SettingsWindow:
	def __init__(self, parent, config, update_callback):
		self.top = tk.Toplevel(parent)
		self.top.title("Settings")

		self.config = config
		self.entries = {}
		self.update_callback = update_callback

		self.create_widgets()

	def create_widgets(self):
		row = 0
		for label, key in CONFIG_LABELS.items():
			tk.Label(self.top, text=label).grid(row=row, column=0, padx=10, pady=5, sticky=tk.W)
			entry = tk.Entry(self.top, width=20)
			entry.grid(row=row, column=1, padx=10, pady=5)
			# Display hex values for specific keys
			if key in ['AFTER_MRC_POST', 'EFI_POST', 'LINUX_POST']:
				entry.insert(0, f"{self.config[key]:#0x}")
			else:
				entry.insert(0, str(self.config[key]))
			self.entries[key] = entry
			row += 1
		tk.Button(self.top, text="Save", command=self.save_changes).grid(row=row, column=0, columnspan=2, pady=10)

	def save_changes(self):
		for key, entry in self.entries.items():
			try:
				# Convert hex input for specific keys
				if key in ['AFTER_MRC_POST', 'EFI_POST', 'LINUX_POST']:
					self.config[key] = int(entry.get(), 16)
				else:
					self.config[key] = int(entry.get())
			except ValueError:
				messagebox.showerror("Invalid Input", f"Invalid value for {key}. Please enter a valid integer.")
				return
		self.update_callback(self.config)
		self.top.destroy()

class TestTTLWindow:
	def __init__(self, parent, experiments, test_function=None):
		self.top = tk.Toplevel(parent)
		self.top.title("Teraterm Macros Tester (TTL)")
		self.experiments = experiments
		self.test_function = test_function
		self.stop_event = threading.Event()
		self.test_thread = None
		self.exception_queue = queue.Queue()
		self.selected_experiment_name = tk.StringVar()
		self.selected_experiment_name.set(next(iter(experiments)))  # Set default to the first experiment

		self.create_widgets()
		self.update_experiment_info()

		# Bind the window close event
		self.top.protocol("WM_DELETE_WINDOW", self.on_close)

	def create_widgets(self):
		# Row 1: Select Experiment, Experiment Menu, and Test Button
		tk.Label(self.top, text="Select Experiment", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky=tk.EW)

		self.experiment_menu = tk.OptionMenu(self.top, self.selected_experiment_name, *self.experiments.keys(), command=self.update_experiment_info)
		self.experiment_menu.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

		tk.Button(self.top, text=" Test Macro ", command=self.start_test_thread).grid(row=0, column=2, padx=5, pady=5, sticky=tk.EW)
		tk.Button(self.top, text=" Cancel", command=self.cancel_test).grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)

		# Row 2: Separator Line
		separator = tk.Frame(self.top, height=2, bd=1, relief=tk.SUNKEN)
		separator.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

		# Row 3: Visual and Content
		self.visual_label = tk.Label(self.top, text="Visual: ")
		self.visual_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

		self.content_label = tk.Label(self.top, text="Content: ")
		self.content_label.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

		tk.Button(self.top, text=" Warm Reset ", command=self.warm_reset).grid(row=2, column=3, padx=5, pady=5, sticky=tk.EW)
		#tk.Button(self.top, text=" Cold Reset ", command=self.reboot_unit).grid(row=2, column=3, padx=5, pady=5, sticky=tk.EW)

		# Row 4: TTL Path
		self.ttl_path_label = tk.Label(self.top, text="TTL Folder: ")
		self.ttl_path_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

		# Row 5: Commands List and Open/Edit TTL Button
		self.ttl_files_listbox = tk.Listbox(self.top)
		self.ttl_files_listbox.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)

		tk.Button(self.top, text=" Open TTL ", command=self.open_edit_ttl_file).grid(row=4, column=2, padx=5, pady=5, sticky=tk.EW)

	def update_experiment_info(self, *args):
		selected_experiment = self.experiments[self.selected_experiment_name.get()]

		self.visual = selected_experiment.get('Visual ID', None)
		self.content = selected_experiment.get('Content', None)
		self.ttl_path = selected_experiment.get('TTL Folder', None)
		self.tnumber = selected_experiment.get('Test Number', 1)
		self.ttime = selected_experiment.get('Test Time', 30)
		self.chkcore = selected_experiment.get('Check Core', None)
		self.bucket = selected_experiment.get('Bucket', 'dummy')
		self.passstring = selected_experiment.get('Pass String', 'Test Complete')
		self.failstring = selected_experiment.get('Fail String', 'Test Failed')
		self.target = selected_experiment.get('Test Mode', None)

		# Update labels with selected values
		self.visual_label.config(text=f"Visual: {self.visual}")
		self.content_label.config(text=f"Content: {self.content}")
		self.ttl_path_label.config(text=f"TTL Folder: {self.ttl_path}")

		# List .ttl files in the TTL Path
		self.ttl_files_listbox.delete(0, tk.END)  # Clear previous entries
		if self.ttl_path and os.path.isdir(self.ttl_path):
			ttl_files = [f for f in os.listdir(self.ttl_path) if f.endswith('.ttl')]
			for ttl_file in ttl_files:
				self.ttl_files_listbox.insert(tk.END, ttl_file)

	def start_test_thread(self):
		# Stop any existing thread
		self.stop_event.set()
		task_name = 'TTL_Check'
		if self.test_thread and self.test_thread.is_alive():
			self.test_thread.stop()
			self.test_thread.join()

		# Clear the stop event and start a new thread
		self.stop_event.clear()
		self.test_thread = ThreadHandler(target=self.run_test, name=f'Thread-{task_name}', args=())
		self.test_thread.start()

	def run_test(self, *args):
		visual = self.visual
		cmds = self.ttl_path
		ttime = self.ttime
		tnumber = self.tnumber
		bucket = self.bucket
		chkcore = self.chkcore if self.chkcore != '' else None

		try:

			execute(task_name = 'TTL Test',target_func = TTL_testing, exceptions=self.exception_queue, cancel_flag = self.stop_event, args=(self.test_function, visual, cmds, chkcore, bucket, ttime, tnumber), use_process = use_process )

		except TaskCancelledException as e:
			print('TTL Test Cancelled by User')
		except Exception as e:
			print('Exception raised: ', e)  # Remove this break if you want the test to run continuously

	def rev_2_check(self, cmds):
		current_datetime = datetime.now().strftime('%Y%m%d_%H%M%S')
		ini_path = os.path.join(self.ttl_path, 'config.ini')
		temp_path = os.path.join(r'C:\Temp', f'TTL_{current_datetime}')
		if not os.path.exists(ini_path):
			print(' TTL Macro is a 1.0 version')
		else:
			print(' TTL Macro is a 2.0 version. Moving to Temp Folder and updating')
			fh.create_folder_if_not_exists(temp_path)
			fh.copy_files(cmds, temp_path, uinput='Y')

			# Starts the compiler
			converter = fh.FrameworkConfigConverter(ini_path, logger=self.test_func.FrameworkPrint)

			# WIP
			dragon_config = None
			linux_config = None
			custom_config = None




	def reboot_unit(self):
		self.test_function.reboot_unit(waittime=60, u600w=False)

	def warm_reset(self):
		self.test_function.warm_reset(waittime=60)

	def open_edit_ttl_file(self):
		selected_index = self.ttl_files_listbox.curselection()
		if selected_index:
			selected_file = self.ttl_files_listbox.get(selected_index)
			ttl_path = self.ttl_path#_label.cget("text").replace("TTL Path: ", "")
			file_path = os.path.join(ttl_path, selected_file)
			if os.path.isfile(file_path):
				os.startfile(file_path)  # Open the file with the default text editor

	def on_close(self):
		# Stop the thread and close the window
		self.stop_event.set()
		self.top.destroy()

	def cancel_test(self):
		self.stop_event.set()
		if self.test_thread and self.test_thread.is_alive():
			self.test_thread.stop()
			self.test_thread.join()
	#def test_function(self):#self, visual, bucket, ttl_path, test='Dummy', ttime=30, tnum=1):
	#	print('add test function')
		#print(f"Running test with visual={visual}, bucket={bucket}, ttl_path={ttl_path}, test={test}, ttime={ttime}, tnum={tnum}")
		# Implement the actual test logic here

class PowerControlWindow:

	def __init__(self, parent, utils):
		self.top = tk.Toplevel(parent)
		self.top.title("Power Control")
		self.Framework_utils = utils

		self.create_widgets()

	def create_widgets(self):
		tk.Button(self.top, width= 12, text=" Power ON ", command=lambda: self.control_power("on")).pack(side=tk.LEFT, padx=10, pady=5)
		tk.Button(self.top, width= 12, text=" Power OFF ", command=lambda: self.control_power("off")).pack(side=tk.LEFT, padx=10, pady=5)
		tk.Button(self.top, width= 12, text=" Power CYCLE ", command=lambda: self.control_power("cycle")).pack(side=tk.LEFT, padx=10, pady=5)

	def control_power(self, state):
		if self.Framework_utils:
			self.Framework_utils.power_control(state=state)
		else:
			print(f"Power control: {state}")

class MaskManagementWindow:

	def __init__(self, parent, mask_dict, update_callback, utils=None):
		self.top = tk.Toplevel(parent)
		self.parent = parent
		self.top.title("Mask Management")
		self.mask_dict = mask_dict
		self.update_callback = update_callback
		self.Framework_utils = utils
		self.create_widgets()

	def create_widgets(self):
		# List to display existing masks
		self.mask_listbox = tk.Listbox(self.top)
		self.mask_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

		# Populate listbox with existing masks
		for mask_name in self.mask_dict.keys():
			self.mask_listbox.insert(tk.END, mask_name)

		# Populate listbox with existing masks
		self.refresh_listbox()

		# Entry to set a new mask name
		self.mask_name_entry = tk.Entry(self.top, width=50)
		self.mask_name_entry.pack(fill=tk.X, padx=10, pady=5)

		# Button to open MaskEditor
		mask_editor_button = tk.Button(self.top, text="Open Mask Editor", command=self.open_mask_editor)
		mask_editor_button.pack(pady=5)

		# Button to save mask
		save_button = tk.Button(self.top, text="Save Mask", command=self.save_mask)
		save_button.pack(pady=5)

	def refresh_listbox(self):
		self.mask_listbox.delete(0, tk.END)
		for mask_name in self.mask_dict.keys():
			self.mask_listbox.insert(tk.END, mask_name)

	# Save the mask with the entered name
	def receive_masks(self, masks):
		print("New/updated masks:", masks)  # Debugging statement
		mask_name = self.mask_name_entry.get().strip()
		if mask_name:
			self.mask_dict[mask_name] = masks
			self.mask_listbox.insert(tk.END, mask_name)
			self.mask_name_entry.delete(0, tk.END)

	def open_mask_editor(self):
		# DMR CBB-based mask editor
		idx = self.mask_listbox.curselection()
		mask_selected = self.mask_listbox.get(idx) if idx else None

		root_mask = tk.Toplevel(self.top)
		clean_mask = self.clean_mask()
		# Create an instance of SystemMaskEditor
		if self.Framework_utils == None:
			self.mask_dict['Default'] = clean_mask
			test_mask = clean_mask if mask_selected == None else self.mask_dict[mask_selected]

			# DMR uses CBB-based configuration (cbb0-3 instead of compute0-2)
			cbb0_core_hex = test_mask.get('ia_cbb0', None)
			cbb0_llc_hex = test_mask.get('llc_cbb0', None)
			cbb1_core_hex = test_mask.get('ia_cbb1', None)
			cbb1_llc_hex = test_mask.get('llc_cbb1', None)
			cbb2_core_hex = test_mask.get('ia_cbb2', None)
			cbb2_llc_hex = test_mask.get('llc_cbb2', None)
			cbb3_core_hex = test_mask.get('ia_cbb3', None)
			cbb3_llc_hex = test_mask.get('llc_cbb3', None)

			gme.Masking(
				root_mask,
				cbb0_core_hex, cbb0_llc_hex,
				cbb1_core_hex, cbb1_llc_hex,
				cbb2_core_hex, cbb2_llc_hex,
				cbb3_core_hex, cbb3_llc_hex,
				product='DMR',
				callback=self.receive_masks
			)
		else:
			sysmask = self.Framework_utils.read_current_mask()
			self.Framework_utils.Masks(basemask=sysmask, root=root_mask, callback=self.receive_masks)
		# Start the UI and get the updated masks

	def clean_mask(self):
		"""Generate clean DMR CBB-based mask (32-bit masks per CBB)"""
		CBB_String = "0x00000000"  # 32-bit mask (8 hex chars)
		masks = {
			'ia_cbb0': CBB_String,
			'ia_cbb1': CBB_String,
			'ia_cbb2': CBB_String,
			'ia_cbb3': CBB_String,
			'llc_cbb0': CBB_String,
			'llc_cbb1': CBB_String,
			'llc_cbb2': CBB_String,
			'llc_cbb3': CBB_String,
		}

		return masks

	def save_mask(self):
		self.update_callback(self.mask_dict)
		self.top.destroy()

## Placeholder for a context manager, not being used for now
@contextmanager
def managed_thread(target, args=(), kwargs=None):
	thread = ThreadHandler(target=target, args=args, kwargs=kwargs)
	try:
		thread.start()
		yield thread
	finally:
		thread.stop()
		thread.join()

def check_exceptions(exception_queue):
	while not exception_queue.empty():
		exception = exception_queue.get()
		if isinstance(exception, TaskCancelledException):
			print("Task cancelled, stopping all executions.")
			return True
	return False

# Function to monitor execution variables -- yet to be enabled, code is not final...
def monitor_task(cancel_flag, task_name,exception_queue):

	try:
		while not cancel_flag.is_set():
			time.sleep(1)

		print('Cancelling now betch!!')

		raise TaskCancelledException(f"{task_name} cancelled")
			# Check periodically

	except:
		exception_queue.put(TaskCancelledException(f"{task_name} cancelled"))

def monitor(cancel_flag, task_name, execution_thread):

	while execution_thread.is_alive():
		if cancel_flag.is_set():
			time.sleep(1)  # Check periodically
		if not execution_thread.is_alive():
			return

	print('Cancelling now')
	execution_thread.join()
	print('Cancelling now')
	#exception_queue.put(TaskCancelledException(f"{task_name} cancelled"))
	raise TaskCancelledException(f"{task_name} cancelled")

# Offline UI Test functions
def TestLogic(txt, cancel_flag, exception_queue):
	try:
		for i in range(10):
			if cancel_flag.is_set():
				print('Cancelling TestLogic')
				exception_queue.put(TaskCancelledException(f"{txt} logic cancelled"))
				raise TaskCancelledException(f"{txt} logic cancelled")
			print(f'Testing {txt} Logic count:{i}')
			time.sleep(1)
		print('Done')
	except TaskCancelledException as e:
		exception_queue.put(e)

def TestLogic2(txt, simulate_fail, exception_queue, cancel_flag):


	try:
		for i in range(10):
			cancel = cancel_flag.is_set() if cancel_flag != None else False
			print(f'Testing {txt} Logic count:{i} -- {cancel} :: {cancel_flag}')
			if cancel or (i == 5 and simulate_fail):
				raise InterruptedError('SimulatedFailure')
			time.sleep(1)
		print('Done')
	except InterruptedError as e:
		print(f"Logic Interrupted by user: {e}")
		exception_queue.put(e)  # Put the exception into the queue

	except TaskCancelledException as e:
		print(f"Exception in TestLogic2: {e}")
		exception_queue.put(e)  # Put the exception into the queue

def TTL_testing(test_function, visual, cmds, chkcore, bucket, ttime, tnumber, exception_queue, cancel_flag):
	#cancel = cancel_flag.is_set() if cancel_flag != None else False

	try:
		cancel = True
		if test_function == None:
			print('add test function')
			for i in range(1,5):
				print(i)
				time.sleep(1)
			if i > 5 and cancel: raise InterruptedError('User SimulatedError')
			for i in range(5,10):
				print(i)
				time.sleep(1)

		else:
			test_function.TTL_Test(visual=visual, cmds=cmds, chkcore = chkcore, bucket = bucket, test = 'TTL_Macro_Validation', ttime=ttime, tnum=tnumber, cancel_flag=cancel_flag)

	except InterruptedError as e:
		print(Fore.YELLOW + f"Framework Iteration Interrupted: {e}" + Fore.WHITE)
		exception_queue.put(e)
	except TaskCancelledException as e:
		print(Fore.YELLOW + f"User Interruption in TTL_testing: {e}"+ Fore.WHITE)
		exception_queue.put(e)
	except Exception as e:
		print(Fore.RED + f"Exception in TTL_testing: {e}"+ Fore.WHITE)
		exception_queue.put(e)  # Put the exception into the queue

def Framework_call(Framework, data, S2TCONFIG, experiment_name, exception_queue, cancel_flag):
	try:
		# Don't access any Tkinter variables here
		# Pass primitive values only, not Tkinter variables

		#Framework.cancel_flag = cancel_flag
		Framework.RecipeExecutor(data=data, S2T_BOOT_CONFIG=S2TCONFIG,
								cancel_flag=cancel_flag, experiment_name=experiment_name)

		if cancel_flag and cancel_flag.is_set():
			raise InterruptedError("Framework execution cancelled by user")
		return True

	except InterruptedError as e:
		print(Fore.YELLOW + f"Framework Iteration Interrupted: {e}" + Fore.WHITE)
		if exception_queue:
			exception_queue.put(e)
		return False
	except Exception as e:
		print(Fore.RED + f"Exception during Framework Execution: {e}" + Fore.WHITE)
		if exception_queue:
			exception_queue.put(e)
		return False

# Deprecated
# Executes threads or process for Framework Flow
def execute(task_name, target_func, exceptions, cancel_flag, args, use_process=True):
	handler = None
	try:
		if use_process:
			exception_queue = multiprocessing.Queue()
			handler = multiprocessing.Process(target=target_func,
											args=args + (exception_queue, None))
		else:
			exception_queue = exceptions
			handler = ThreadHandler(target=target_func, name=f'Thread-{task_name}',
								  args=args + (exception_queue, cancel_flag))

		handler.start()
		print(Fore.RED + f"Framework Control -- Starting new task: {task_name} -- " + Fore.WHITE)

		# Monitor execution
		#while not cancel_flag.is_set():
		#	time.sleep(0.1)
		#	if not handler.is_alive():
		#		break

		#if cancel_flag.is_set():
		#	if use_process and handler:
		#		handler.terminate()
		#	elif handler:
		#		handler.stop()
		#	raise TaskCancelledException(f"{task_name} cancelled by User")

		if handler:
			handler.join(timeout=5.0)

		# Check for exceptions
		try:
			if not exception_queue.empty():
				exception = exception_queue.get_nowait()
				print(f"Exception occurred during {task_name}: {exception}")
				return False
		except:
			pass

		return True

	except Exception as e:
		print(Fore.RED + f"Exception occurred during {task_name}: {e}" + Fore.WHITE)
		try:
			if handler:
				if use_process:
					handler.terminate()
				else:
					handler.stop()
				handler.join(timeout=2.0)
		except:
			pass

		if exceptions:
			try:
				exceptions.put(e)
			except:
				pass
		return False

def OpenExperiment(path):
	# Placeholder for the actual implementation
	# Assume fh.process_excel_file and fh.create_tabulated_format are defined elsewhere

	if path.endswith('.json'):
		data_from_sheets = fh.load_json_file(path)
		#tabulated_df = data_from_sheets
	elif path.endswith('.xlsx'):
		data_from_sheets = fh.process_excel_file(path)
		# Create the tabulated format
	else: return None

	return data_from_sheets

def Convert_xlsx_to_json(file_path, experiments):
	data_from_json = fh.save_excel_to_json(file_path, experiments)
	return data_from_json

def run(Framework, utils, manager):
	try:
		root = tk.Tk()

		# Ensure we're in the main thread
		if threading.current_thread() != threading.main_thread():
			raise RuntimeError("GUI must be started from main thread")

		app = DebugFrameworkControlPanel(root, Framework, utils, manager)
		root.mainloop()

	except Exception as e:
		print(f"Error starting GUI: {e}")
	finally:
		# Ensure cleanup
		try:
			root.quit()
			root.destroy()
		except:
			pass

if __name__ == "__main__":
	Framework = None
	utils = None
	manager = None

	root = tk.Tk()
	app = DebugFrameworkControlPanel(root, Framework, manager, utils)
	root.mainloop()
