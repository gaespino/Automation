"""
FlowProgressInterface.py
Main interface for the automation flow progress monitoring.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
from datetime import datetime
import queue
import importlib

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

print(' Framework Automation Panel -- rev 1.7')
# Note: parent_dir path not printed to avoid console clutter

sys.path.append(parent_dir)


# Import all the builder classes
from Automation_Flow.AutomationBuilder import (
	FlowConfiguration,
	NodeDrawer,
	ConnectionDrawer,
	LayoutManager,
	NodeDragHandler,
	CanvasInteractionHandler,
	StatusDisplayPanel
)

# Import all the flow/executor classes
from Automation_Flow.AutomationFlows import (
	FlowTestBuilder,
)
# Optional: Import shared status panel if it exists
try:
	from UI.StatusPanel import StatusExecutionPanel
	HAS_STATUS_PANEL = True
except ImportError:
	print("Warning: StatusExecutionPanel not found. Using basic status display.")
	HAS_STATUS_PANEL = False

import UI.StatusHandler as fs
import ExecutionHandler.utils.ThreadsHandler as th
importlib.reload(th)

ExecutionCommand = th.ExecutionCommand
execution_state = th.execution_state

# ==================== NEW INTERFACE FUNCTIONS ====================

class FlowProgressInterface:
	"""
	Enhanced Automation Flow Interface with proper command handling and cleanup.
	Matches ControlPanel's robustness for Framework API interaction.
	"""
	
	def __init__(self, framework=None, utils=None, manager=None):
		self.framework = framework
		
		# Framework integration (matching ControlPanel pattern)
		self.framework_manager = manager(framework) if manager and framework else None
		self.Framework_utils = utils
		self.execution_state = execution_state  # Global ThreadsHandler - ONLY state manager
		
		# REMOVED: FlowExecutionManager, FlowExecutionState
		# SIMPLIFIED: Direct Framework API management
		self.shared_framework_api = None
		self.framework_instance_id = None
		
		# Flow configuration
		self.builder = None
		self.executor = None
		self.root_node = None
		
		# File paths (unchanged)
		self.flow_folder = None
		self.structure_path = None
		self.flows_path = None
		self.ini_path = None
		self.default_files = {
			'structure': 'FrameworkAutomationStructure.json',
			'flows': 'FrameworkAutomationFlows.json',
			'ini': 'FrameworkAutomationInit.ini'
		}
		
		# UI State (unchanged)
		self.current_node = None
		self.completed_nodes = set()
		self.failed_nodes = set()
		self.node_widgets = {}
		self.connection_lines = {}
		
		# Statistics tracking - SIMPLIFIED
		self.start_time = None
		self.total_nodes = 0
		self.completed_count = 0
		self.failed_count = 0
		
		# Threading - SIMPLIFIED
		self.main_thread_handler = None
		self.execution_thread = None
		self.is_running = False
		self._cleanup_in_progress = False
		self._scheduled_after_ids = []
		
		# REMOVED: Complex queue management, cancellation events, etc.
		
		# Initialize SIMPLIFIED components
		self.flow_config = FlowConfiguration(framework_api=None, framework_utils=self.Framework_utils, execution_state=self.execution_state)
		
		# UI components (unchanged)
		self.node_drawer = None
		self.connection_drawer = None
		self.layout_manager = None
		self.drag_handler = None
		self.interaction_handler = None
		
		# Dragging state variables (unchanged)
		self.current_positions = {}
		
		# Create main window (unchanged)
		self.setup_main_window()
		self.create_widgets()

		# Initialize MainThreadHandler
		self.main_thread_handler = fs.SecondThreadHandler(self.root, self)		

		# Start update loop
		#self.root.after(100, self.process_updates)
		
		# Cleanup handling
		self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
		
		#after_id = self.root.after(100, self.process_updates)
		#self._scheduled_after_ids.append(after_id)

	def setup_main_window(self):
		"""Setup the main window with proper styling."""
		self.root = tk.Tk()
		self.root.title("Automation Flow Execution Monitor")
		self.root.geometry("1600x900")
		self.root.minsize(1200, 700)
		
		# Configure styles to match ControlPanel
		self.setup_styles()

	def setup_styles(self):
		"""Configure ttk styles for consistent appearance with ControlPanel."""
		self.style = ttk.Style()
		
		# Use same theme as ControlPanel
		try:
			self.style.theme_use('alt')
		except:
			self.style.theme_use('clam')
		
		# Node status colors
		self.node_colors = {
			'idle': '#E8E8E8',           # Light gray - waiting
			'current': '#2196F3',        # Blue - currently executing
			'running': '#FF5722',        # Red - experiment running
			'completed': '#4CAF50',      # Green - completed successfully
			'failed': '#F44336',         # Red - execution failed
			'execution_fail': '#FFC107', # Yellow - execution failed
			'skipped': '#FF9800',        # Orange - skipped
			'cancelled': '#9E9E9E'       # Gray - cancelled
		}
		
		# Text colors for better contrast
		self.node_text_colors = {
			'idle': 'black',
			'current': 'white',
			'running': 'white',
			'completed': 'white',
			'failed': 'white',
			'execution_fail': 'black',
			'skipped': 'white',
			'cancelled': 'white'
		}
		
		# Connection colors
		self.connection_colors = {
			0: '#F44336',  # Red for failure path
			1: '#4CAF50',  # Green for success path
			2: '#FF9800',  # Orange for alternative path
			3: '#9C27B0'   # Purple for special path
		}
		
		# Button styles (matching ControlPanel)
		self.style.configure("Hold.TButton", foreground="black")
		self.style.configure("HoldActive.TButton", foreground="orange", font=("Arial", 9, "bold"))
		self.style.configure("Continue.TButton", foreground="blue", font=("Arial", 9, "bold"))
		self.style.configure("End.TButton", foreground="red", font=("Arial", 9, "bold"))
		self.style.configure("EndActive.TButton", foreground="white", background="red", font=("Arial", 9, "bold"))

	def create_widgets(self):
		"""Create the main UI layout."""
		# Main horizontal container
		self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
		self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
		
		# Left side - Flow diagram
		self.left_frame = ttk.Frame(self.main_paned)
		self.main_paned.add(self.left_frame, weight=3)
		
		# Right side - Status panel (using shared component)
		self.right_frame = ttk.Frame(self.main_paned)
		self.main_paned.add(self.right_frame, weight=1)
		
		self.create_left_panel()
		self.create_right_panel()

	def create_left_panel(self):
		"""Create the flow diagram panel."""
		# Title and controls
		title_frame = ttk.Frame(self.left_frame)
		title_frame.pack(fill=tk.X, padx=10, pady=5)
		
		ttk.Label(title_frame, text="Automation Flow Execution", 
				 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
		
		# Status label (matching ControlPanel)
		self.status_label = tk.Label(title_frame, padx=5, width=15, text=" Ready ", 
								   bg="white", fg="black", font=("Arial", 12), 
								   relief=tk.GROOVE, borderwidth=2)
		self.status_label.pack(side=tk.RIGHT)
		
		# Control buttons frame
		controls_frame = ttk.Frame(title_frame)
		controls_frame.pack(side=tk.RIGHT, padx=5)
		
		# Control buttons (matching ControlPanel functionality)
		self.run_button = ttk.Button(controls_frame, text="Start Flow", 
									 command=self.start_execution, state=tk.DISABLED)
		self.run_button.pack(side=tk.RIGHT, padx=2)
		
		self.hold_button = ttk.Button(controls_frame, text="Hold", 
									command=self.toggle_framework_hold, 
									state=tk.DISABLED, style="Hold.TButton")
		self.hold_button.pack(side=tk.RIGHT, padx=2)
		
		self.end_button = ttk.Button(controls_frame, text="End", 
								   command=self.end_current_experiment, 
								   state=tk.DISABLED, style="End.TButton")
		self.end_button.pack(side=tk.RIGHT, padx=2)
		
		self.cancel_button = ttk.Button(controls_frame, text="Cancel", 
									  command=self.cancel_execution, 
									  state=tk.DISABLED)
		self.cancel_button.pack(side=tk.RIGHT, padx=2)
		
		# Dragging controls frame (NEW - restored from modular version)
		drag_controls_frame = ttk.Frame(controls_frame)
		drag_controls_frame.pack(side=tk.RIGHT, padx=(20, 5))
		
		self.drag_enabled_var = tk.BooleanVar(value=True)
		self.drag_checkbox = ttk.Checkbutton(
			drag_controls_frame, text="Enable Dragging",
			variable=self.drag_enabled_var,
			command=self.toggle_dragging
		)
		self.drag_checkbox.pack(side=tk.RIGHT, padx=2)
		
		self.snap_grid_var = tk.BooleanVar(value=True)
		self.snap_checkbox = ttk.Checkbutton(
			drag_controls_frame, text="Snap to Grid",
			variable=self.snap_grid_var,
			command=self.toggle_grid_snap
		)
		self.snap_checkbox.pack(side=tk.RIGHT, padx=2)
		
		self.reset_positions_button = ttk.Button(
			drag_controls_frame, text="Reset Layout",
			command=self.reset_node_positions
		)
		self.reset_positions_button.pack(side=tk.RIGHT, padx=2)

		self.refresh_button = ttk.Button(
			drag_controls_frame, text="Refresh Display",
			command=self.force_complete_redraw
		)
		self.refresh_button.pack(side=tk.RIGHT, padx=2)   

		# File selection frame
		file_frame = ttk.Frame(self.left_frame)
		file_frame.pack(fill=tk.X, padx=10, pady=5)
		
		ttk.Label(file_frame, text="Flow Folder:", width=12).pack(side=tk.LEFT)
		
		self.folder_entry = ttk.Entry(file_frame, state='readonly')
		self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
		
		self.browse_button = ttk.Button(file_frame, text="Browse", 
									  command=self.browse_flow_folder)
		self.browse_button.pack(side=tk.RIGHT)
		
		# File status frame
		self.file_status_frame = ttk.Frame(self.left_frame)
		self.file_status_frame.pack(fill=tk.X, padx=10, pady=5)
		
		# Initially hidden, will be shown after folder selection
		self.create_file_status_widgets()

		# Progress bar (FIXED: Better labeling)
		progress_frame = ttk.Frame(self.left_frame)
		progress_frame.pack(fill=tk.X, padx=10, pady=5)
		
		ttk.Label(progress_frame, text="Flow Progress:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
		
		self.progress_var = tk.DoubleVar()
		self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
										maximum=100, length=300)
		self.progress_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
		
		self.progress_label = ttk.Label(progress_frame, text="0%", font=("Arial", 9, "bold"))
		self.progress_label.pack(side=tk.RIGHT)
		
		# Separator
		ttk.Separator(self.left_frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)
		
		# Canvas for flow diagram
		canvas_frame = ttk.Frame(self.left_frame)
		canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
		
		# Canvas with scrollbars
		self.canvas = tk.Canvas(canvas_frame, bg='white', highlightthickness=0)
		
		v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
		h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
		
		self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
		
		# Pack scrollbars and canvas
		self.canvas.pack(side="left", fill="both", expand=True)
		v_scrollbar.pack(side="right", fill="y")
		h_scrollbar.pack(side="bottom", fill="x")
		
		# Initialize drawing components after canvas is created
		self.setup_drawing_components()
		
		# Bind mouse events for canvas interaction (including dragging)
		self.canvas.bind("<Button-1>", self.on_canvas_click)
		self.canvas.bind("<Button-3>", self.on_right_click)  # Right-click context menu
		self.canvas.bind("<MouseWheel>", self.on_mousewheel)
		
		# Dragging bindings (NEW - restored)
		self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
		self.canvas.bind("<B1-Motion>", self.on_drag_motion)
		self.canvas.bind("<ButtonRelease-1>", self.on_drag_end)
		
		# Initial message on canvas
		self.show_canvas_message("Please select a flow folder to begin")

	def setup_drawing_components(self):
		"""Initialize the drawing and interaction components."""
		# Initialize drawing components
		self.node_drawer = NodeDrawer(self.canvas, self.node_colors, self.connection_colors)
		self.connection_drawer = ConnectionDrawer(self.canvas, self.connection_colors)
		self.layout_manager = LayoutManager()
		
		# Initialize interaction handlers
		self.drag_handler = NodeDragHandler(
			self.canvas, self.layout_manager, 
			self.node_drawer, self.connection_drawer
		)
		self.interaction_handler = CanvasInteractionHandler(
			self.canvas, self.flow_config, 
			self.execution_state, self.drag_handler
									)


	def create_right_panel(self):
		"""Create the status and logging panel using shared component."""

		# Create the shared status panel (single progress bar for automation)
		if HAS_STATUS_PANEL:
			self.status_panel = StatusExecutionPanel(
				parent_frame=self.right_frame,
				dual_progress=False,  # Use single progress for automation flow
				create_on_start=False,
				show_experiment_stats=True,
				logger_callback=self._external_log_callback
			)
			
			# Store references for compatibility and command handling
			self.create_automation_specific_sections()
			self.status_panel.generate_panel()
			self.status_log = self.status_panel.status_log
			self.auto_scroll_var = self.status_panel.auto_scroll_var
			self.elapsed_time_label = self.status_panel.elapsed_time_label
		else:
			# Fallback to basic status panel
			self.status_panel = StatusDisplayPanel(self.right_frame, self.execution_state)

			# Add automation-specific sections after the progress section
			self.create_automation_specific_sections()

	def create_automation_specific_sections(self):
		"""Add automation-specific UI sections."""
		# Get the main container from status panel
		main_container = self.status_panel.main_container if HAS_STATUS_PANEL else self.right_frame
		
		# Current node info (insert after progress section)
		current_node_frame = ttk.LabelFrame(main_container, text="Current Node", padding=10)
		current_node_frame.pack(fill=tk.X, pady=(0, 10))
		
		self.current_node_label = ttk.Label(current_node_frame, text="Node: Ready to start")
		self.current_node_label.pack(anchor="w")
		
		self.current_experiment_label = ttk.Label(current_node_frame, text="Experiment: None")
		self.current_experiment_label.pack(anchor="w")
		
		self.current_status_label = ttk.Label(current_node_frame, text="Status: Idle")
		self.current_status_label.pack(anchor="w")
		
		# Flow statistics (insert after statistics section)
		flow_stats_frame = ttk.LabelFrame(self.status_panel.main_container if HAS_STATUS_PANEL else self.right_frame, 
										text="Flow Statistics", padding=10)
		flow_stats_frame.pack(fill=tk.X, pady=(0, 10))
		
		counters_frame = ttk.Frame(flow_stats_frame)
		counters_frame.pack(fill=tk.X)
		
		self.completed_nodes_label = ttk.Label(counters_frame, text="✓ Completed: 0", foreground="green")
		self.completed_nodes_label.pack(side=tk.LEFT)
		
		self.failed_nodes_label = ttk.Label(counters_frame, text="✗ Failed: 0", foreground="red")
		self.failed_nodes_label.pack(side=tk.LEFT, padx=(10, 0))
		
		self.total_nodes_label = ttk.Label(counters_frame, text="Total: 0")
		self.total_nodes_label.pack(side=tk.RIGHT)

	def _external_log_callback(self, message: str, level: str):
		"""Callback for external logging integration."""
		# Add any automation-specific logging logic here
		pass

	def log_status(self, message: str, level: str = "info"):
		"""Log status message - delegate to shared status panel or print."""
		if HAS_STATUS_PANEL and hasattr(self.status_panel, 'log_status'):
			self.status_panel.log_status(message, level)
		else:
			timestamp = datetime.now().strftime("%H:%M:%S")
			print(f"[{timestamp}] {level.upper()}: {message}")

	def _coordinate_status_updates(self, status_data):
		"""Coordinate status label updates."""
		try:
			if isinstance(status_data, dict):
				text = status_data.get('text', '')
				bg = status_data.get('bg', 'white')
				fg = status_data.get('fg', 'black')
				
				self.status_label.configure(text=text, bg=bg, fg=fg)
			else:
				self.status_label.configure(text=str(status_data))
		except Exception as e:
			self.log_status(f"Status update error: {e}", "error")

	def _coordinate_button_states(self, action_type, button_data=None):
		"""Coordinate button state updates."""
		try:
			if action_type == 'enable_after_completion':
				self._enable_ui_buttons_safe()
			elif action_type == 'specific_button_update' and button_data:
				self._update_specific_buttons(button_data)
			elif action_type == 'disable_for_execution':
				self._disable_ui_buttons_safe()
		except Exception as e:
			self.log_status(f"Button state update error: {e}", "error")

	def _enable_ui_buttons_safe(self):
		"""Safely enable UI buttons with error handling."""
		try:
			self.run_button.configure(state=tk.NORMAL)
			self.cancel_button.configure(state=tk.DISABLED)
			self.hold_button.configure(state=tk.DISABLED, text="Hold", style="Hold.TButton")
			self.end_button.configure(state=tk.DISABLED, text="End", style="End.TButton")
			self.browse_button.configure(state=tk.NORMAL)
			
			# Re-enable dragging controls
			self.drag_checkbox.configure(state=tk.NORMAL)
			self.snap_checkbox.configure(state=tk.NORMAL)
			self.reset_positions_button.configure(state=tk.NORMAL)
			self.refresh_button.configure(state=tk.NORMAL)
			self.drag_handler.enable_dragging(self.drag_enabled_var.get())
			
		except Exception as e:
			self.log_status(f"Error enabling buttons: {e}", "error")

	def _disable_ui_buttons_safe(self):
		"""Safely disable UI buttons during execution."""
		try:
			self.run_button.configure(state=tk.DISABLED)
			self.cancel_button.configure(state=tk.NORMAL)
			self.hold_button.configure(state=tk.NORMAL, text="Hold", style="Hold.TButton")
			self.end_button.configure(state=tk.NORMAL, text="End", style="End.TButton")
			self.browse_button.configure(state=tk.DISABLED)
			
			# Disable dragging controls during execution
			self.drag_checkbox.configure(state=tk.DISABLED)
			self.snap_checkbox.configure(state=tk.DISABLED)
			self.reset_positions_button.configure(state=tk.DISABLED)
			self.refresh_button.configure(state=tk.DISABLED)
			self.drag_handler.enable_dragging(False)
			
		except Exception as e:
			self.log_status(f"Error disabling buttons: {e}", "error")

	def _update_specific_buttons(self, button_data):
		"""Update specific buttons based on data."""
		try:
			for button_name, config in button_data.items():
				button = getattr(self, button_name, None)
				if button:
					if 'text' in config:
						button.configure(text=config['text'])
					if 'state' in config:
						button.configure(state=config['state'])
					if 'style' in config:
						button.configure(style=config['style'])
		except Exception as e:
			self.log_status(f"Specific button update error: {e}", "error")

	def _coordinate_progress_updates(self, update_type, data):
		"""Coordinate progress updates - automation flow uses single progress."""
		try:
			if update_type == 'overall_calculation':
				self.update_progress()
			elif update_type == 'iteration_progress':
				# For automation, iteration progress contributes to overall progress
				self.update_progress()
			elif update_type == 'strategy_progress':
				# For automation, strategy progress is the overall progress
				self.update_progress()
			elif update_type == 'experiment_start':
				# FIXED: Don't reset progress for new experiment/node in automation
				# Each node is a separate experiment, so we track cumulative progress
				pass  # Don't reset progress
			elif update_type == 'flow_start':
				# FIXED: Only reset at flow start
				self.reset_progress_tracking()
		except Exception as e:
			self.log_status(f"Progress update error: {e}", "error")

	def _coordinate_progress_bar_styles(self, style_name, duration=None, bar_type='single'):
		"""Coordinate progress bar style updates - automation has single progress bar."""
		if self._cleanup_in_progress:
			return
		try:
			# Map styles to appropriate automation styles
			style_mapping = {
				"Iteration.Error.Horizontal.TProgressbar": "TProgressbar",  # Use default for errors
				"Iteration.Boot.Horizontal.TProgressbar": "TProgressbar",   # Use default for boot
				"Warning.Horizontal.TProgressbar": "TProgressbar",          # Use default for warnings
				"Custom.Horizontal.TProgressbar": "TProgressbar"            # Use default
			}
			
			mapped_style = style_mapping.get(style_name, "TProgressbar")
			self.progress_bar.configure(style=mapped_style)
			
			# Reset style after duration if specified
			if duration and not self._cleanup_in_progress:
				after_id = self.root.after(duration, lambda: self.progress_bar.configure(style="TProgressbar"))
				self._scheduled_after_ids.append(after_id)	

		except Exception as e:
			self.log_status(f"Progress bar style error: {e}", "error")

	def update_progress_display(self, **kwargs):
		"""Update progress display with various parameters - ENHANCED for Framework integration."""
		try:
			# Handle experiment name updates
			if 'experiment_name' in kwargs and hasattr(self, 'current_experiment_label'):
				exp_name = kwargs['experiment_name']
				if exp_name:
					self.current_experiment_label.configure(text=f"Experiment: {exp_name}")
			
			# Handle strategy type updates
			if 'strategy_type' in kwargs:
				strategy_type = kwargs['strategy_type']
				test_name = kwargs.get('test_name', '')
				
				# Update status panel strategy info
				if hasattr(self, 'status_panel'):
					self.status_panel.update_strategy_info(
						strategy_type=strategy_type,
						test_name=test_name
					)
			
			# Handle status updates
			if 'status' in kwargs and hasattr(self, 'current_status_label'):
				status = kwargs['status']
				self.current_status_label.configure(text=f"Status: {status}")
			
			# Handle result status (for coloring and statistics)
			if 'result_status' in kwargs:
				result = kwargs['result_status']
				
				# Update statistics in status panel
				#if hasattr(self, 'status_panel'):
				#	self.status_panel.update_statistics(result_status=result)
				
				# Update current status color
				if hasattr(self, 'current_status_label'):
					color = 'green' if result == 'PASS' else 'red' if result == 'FAIL' else 'black'
					self.current_status_label.configure(foreground=color)
			
			# Update timing display
			if hasattr(self, 'status_panel'):
				self.status_panel.update_timing_display()
				
		except Exception as e:
			self.log_status(f"Progress display update error: {e}", "error")

	def reset_progress_tracking(self):
		"""Reset progress tracking for new execution - ENHANCED."""
		try:
			# FIXED: Reset progress bar
			self.progress_var.set(0)
			self.progress_label.configure(text="0%")
			
			# FIXED: Reset counters
			self.completed_count = 0
			self.failed_count = 0
			self.completed_nodes.clear()
			self.failed_nodes.clear()
			
			# FIXED: Reset status panel if available
			if hasattr(self, 'status_panel'):
				self.status_panel.reset_progress_tracking()
			
			# FIXED: Update execution_state
			if self.execution_state:
				self.execution_state.update_state(
					current_iteration=0,
					total_iterations=self.total_nodes
				)
			
			# Update statistics display
			if hasattr(self, 'completed_nodes_label'):
				self.completed_nodes_label.configure(text="✓ Completed: 0")
			if hasattr(self, 'failed_nodes_label'):
				self.failed_nodes_label.configure(text="✗ Failed: 0")
			
			# Reset current status
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(text="Status: Ready", foreground='black')
				
		except Exception as e:
			self.log_status(f"Progress reset error: {e}", "error")

	def debug_progress_state(self):
		"""Debug method for progress state - automation specific."""
		if hasattr(self, 'progress_var'):
			print(f"[DEBUG] Automation Progress: {self.progress_var.get():.1f}%")
		if hasattr(self, 'completed_count'):
			print(f"[DEBUG] Completed Nodes: {self.completed_count}")
		if hasattr(self, 'failed_count'):
			print(f"[DEBUG] Failed Nodes: {self.failed_count}")
		if hasattr(self, 'total_nodes'):
			print(f"[DEBUG] Total Nodes: {self.total_nodes}")
		
		# FIXED: Check execution_state values
		if hasattr(self, 'execution_state') and self.execution_state:
			current_iter = self.execution_state.get_state('current_iteration', 0)
			total_iter = self.execution_state.get_state('total_iterations', 0)
			print(f"[DEBUG] ExecutionState - Current: {current_iter}, Total: {total_iter}")
	# ==================== AUTOMATION SPECIFIC METHODS ====================
	
	def _update_experiment_status_safe(self, experiment_name, status, bg_color, fg_color):
		"""Update experiment status safely - automation specific."""
		try:
			# For automation, this updates the current node status
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(
					text=f"Status: {status}",
					foreground=fg_color if fg_color != 'white' else 'black'
				)
		except Exception as e:
			self.log_status(f"Experiment status update error: {e}", "error")

	def _handle_flow_specific_updates(self, update_type, data):
		"""Handle flow-specific updates that don't exist in other interfaces."""
		try:
			if update_type == 'current_node_update':
				self._handle_current_node_update_safe(data)
			elif update_type == 'node_status_update':
				self._handle_node_status_update_safe(data)
			elif update_type == 'flow_progress_update':
				self._handle_flow_progress_update_safe()
			elif update_type == 'flow_setup':
				self._handle_flow_setup_safe(data)
		except Exception as e:
			self.log_status(f"Flow-specific update error: {e}", "error")
				
	def _handle_current_node_update_safe(self, node_data):
		"""Handle current node update safely."""
		try:
			if hasattr(self, 'current_node_label'):
				self.current_node_label.configure(
					text=f"Node: {node_data['node_name']} ({node_data['node_id']})"
				)
			
			if hasattr(self, 'current_experiment_label'):
				self.current_experiment_label.configure(
					text=f"Experiment: {node_data['experiment_name']}"
				)
			
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(
					text="Status: Preparing", foreground='blue'
				)
			
			# Update node visual status
			if hasattr(self, 'builder') and self.builder and hasattr(self, 'node_drawer'):
				node = self.builder.builtNodes.get(node_data['node_id'])
				if node and self.node_drawer:
					self.node_drawer.redraw_node(node, 'current')
					
		except Exception as e:
			self.log_status(f"Current node update error: {e}", "error")

	def _handle_node_status_update_safe(self, status_data):
		"""Handle node status update safely."""
		try:
			node_id = status_data['node_id']
			status = status_data['status']
			
			# Update node visual status
			if hasattr(self, 'node_drawer') and self.node_drawer:
				if hasattr(self, 'builder') and self.builder:
					node = self.builder.builtNodes.get(node_id)
					if node:
						self.node_drawer.redraw_node(node, status)
			
			# Update current status if this is the current node
			if (hasattr(self, 'current_node') and self.current_node and 
				self.current_node.ID == node_id):
				
				status_text_map = {
					'running': 'Status: Running Experiment',
					'completed': 'Status: Completed',
					'failed': 'Status: Test Failed',
					'execution_fail': 'Status: Execution Failed'
				}
				
				status_color_map = {
					'running': 'red',
					'completed': 'green',
					'failed': 'red',
					'execution_fail': 'orange'
				}
				
				if hasattr(self, 'current_status_label'):
					self.current_status_label.configure(
						text=status_text_map.get(status, f"Status: {status}"),
						foreground=status_color_map.get(status, 'black')
					)
		except Exception as e:
			self.log_status(f"Node status update error: {e}", "error")

	def _handle_flow_progress_update_safe(self):
		"""Handle flow progress update safely."""
		try:
			self.update_progress()
			
			# Update statistics
			if hasattr(self, 'completed_nodes_label'):
				self.completed_nodes_label.configure(
					text=f"✓ Completed: {self.completed_count}"
				)
			if hasattr(self, 'failed_nodes_label'):
				self.failed_nodes_label.configure(
					text=f"✗ Failed: {self.failed_count}"
				)
		except Exception as e:
			self.log_status(f"Flow progress update error: {e}", "error")


	def _handle_flow_setup_safe(self, setup_data):
		"""Handle flow setup safely."""
		try:
			if hasattr(self, 'total_nodes_label'):
				self.total_nodes_label.configure(text=f"Total: {setup_data['total_nodes']}")
			
			# Update execution_state
			if self.execution_state:
				self.execution_state.update_state(
					total_iterations=setup_data['total_nodes'],
					current_iteration=0
				)
		except Exception as e:
			self.log_status(f"Flow setup update error: {e}", "error")
				
	# ==================== DRAGGING FUNCTIONALITY (RESTORED) ====================
	
	def toggle_dragging(self):
		"""Toggle dragging capability."""
		enabled = self.drag_enabled_var.get()
		if self.drag_handler:
			self.drag_handler.enable_dragging(enabled)
		
		# Update cursor
		if enabled and not self.is_running:
			self.canvas.configure(cursor="hand2")
		else:
			self.canvas.configure(cursor="")
	
	def toggle_grid_snap(self):
		"""Toggle grid snapping."""
		if self.drag_handler:
			self.drag_handler.snap_to_grid = self.snap_grid_var.get()
	
	def reset_node_positions(self):
		"""Reset node positions to calculated layout."""
		if not self.drag_handler or not self.layout_manager:
			return
		
		if self.layout_manager.position_modified:
			if messagebox.askyesno("Reset Positions", 
								 "This will reset all manually positioned nodes to the calculated layout. Continue?"):
				self.layout_manager.reset_positions()
				# Redraw the flow with reset positions
				if self.builder:
					self.draw_flow_diagram()
				self.log_status("Node positions reset to calculated layout")
				return True
		else:
			self.log_status("No custom positions to reset")
		return False

	def force_complete_redraw(self):
		"""Force a complete redraw of the entire flow diagram."""
		# FIXED: Check if we have a valid builder after cleanup
		if not hasattr(self, 'builder') or not self.builder:
			self.show_canvas_message("No flow configuration loaded")
			return
		
		try:
			# Clear everything
			self.canvas.delete("all")
			
			# FIXED: Safe clearing of tracking dictionaries
			if hasattr(self, 'node_widgets'):
				self.node_widgets.clear()
			if hasattr(self, 'connection_lines'):
				self.connection_lines.clear()
			
			# FIXED: Safe connection drawer clearing
			if hasattr(self, 'connection_drawer') and self.connection_drawer:
				self.connection_drawer.clear_all_connections()
			
			# FIXED: Safe node drawer clearing
			if hasattr(self, 'node_drawer') and self.node_drawer:
				if hasattr(self.node_drawer, 'node_widgets'):
					self.node_drawer.node_widgets.clear()
			
			# Force canvas update
			self.canvas.update_idletasks()
			
			# FIXED: Ensure we have current_positions
			if not hasattr(self, 'current_positions') or not self.current_positions:
				self._recalculate_positions()
			
			# Redraw everything
			nodes = list(self.builder.builtNodes.values())
			
			# FIXED: Safe drag handler update
			if hasattr(self, 'drag_handler') and self.drag_handler:
				self.drag_handler.set_nodes_and_positions(nodes, self.current_positions)
			
			# Draw connections first
			if hasattr(self, 'connection_drawer') and self.connection_drawer:
				self.connection_drawer.draw_connections(nodes, self.current_positions)
			
			# Draw nodes
			if hasattr(self, 'node_drawer') and self.node_drawer:
				for node in nodes:
					if node.ID in self.current_positions:
						pos = self.current_positions[node.ID]
						status = self.get_node_status_color(node)
						self.node_drawer.draw_single_node(node, pos, status)
			
			# Update canvas scroll region
			self.update_canvas_scroll_region(self.current_positions)
			
			self.log_status("Display refreshed successfully")
			
		except Exception as e:
			self.log_status(f"Error during refresh: {e}", "error")
			# FIXED: Better error recovery
			self.show_canvas_message("Error refreshing display. Please reload configuration.")

	def _recalculate_positions(self):
		"""Recalculate node positions if they're missing."""
		try:
			if hasattr(self, 'layout_manager') and self.layout_manager and hasattr(self, 'builder') and self.builder:
				calculated_positions = self.layout_manager.calculate_hierarchical_layout(self.builder)
				self.current_positions = {}
				for node_id, calc_pos in calculated_positions.items():
					self.current_positions[node_id] = self.layout_manager.get_node_position(node_id, {node_id: calc_pos})
			else:
				self.current_positions = {}
		except Exception as e:
			self.log_status(f"Error recalculating positions: {e}", "error")
			self.current_positions = {}

	def on_drag_start(self, event):
		"""Handle start of node dragging."""
		if not self.drag_handler or self.is_running:
			return
		
		# Only handle dragging if dragging is enabled
		if self.drag_enabled_var.get():
			self.drag_handler.on_drag_start(event)

	def on_drag_motion(self, event):
		"""Handle dragging motion."""
		if not self.drag_handler or self.is_running:
			return
		
		if self.drag_enabled_var.get():
			self.drag_handler.on_drag_motion(event)
		
	def on_drag_end(self, event):
		"""Handle end of dragging."""
		if not self.drag_handler or self.is_running:
			return
		
		if self.drag_enabled_var.get():
			self.drag_handler.on_drag_end(event)
			# Update current positions after drag
			if hasattr(self.drag_handler, 'current_positions'):
				self.current_positions = self.drag_handler.current_positions

	def on_right_click(self, event):
		"""Handle right-click context menu."""
		if not self.drag_handler or self.is_running:
			return
		
		# Only show context menu if dragging is enabled
		if self.drag_enabled_var.get():
			self.show_context_menu(event)
	
	def show_context_menu(self, event):
		"""Show context menu for node operations."""
		canvas_x = self.canvas.canvasx(event.x)
		canvas_y = self.canvas.canvasy(event.y)
		
		# Find node under cursor
		item = self.canvas.find_closest(canvas_x, canvas_y)[0]
		tags = self.canvas.gettags(item)
		
		node_id = None
		for tag in tags:
			if tag.startswith("node_"):
				node_id = tag.split("_", 1)[1]
				break
		
		if node_id:
			context_menu = tk.Menu(self.root, tearoff=0)
			
			context_menu.add_command(
				label=f"Node Details: {node_id}",
				command=lambda: self.show_node_details(node_id)
			)
			
			context_menu.add_separator()
			
			context_menu.add_command(
				label=f"Reset Position: {node_id}",
				command=lambda: self._reset_single_node_position(node_id)
			)
			
			try:
				context_menu.tk_popup(event.x_root, event.y_root)
			finally:
				context_menu.grab_release()
		
	def _reset_single_node_position(self, node_id):
		"""Reset a single node to its calculated position."""
		if self.layout_manager:
			self.layout_manager.reset_single_position(node_id)
			# Redraw the flow to show the reset position
			if self.builder:
				self.draw_flow_diagram()
			self.log_status(f"Reset position for node: {node_id}")
		
	# ==================== FILE HANDLING & FLOW LOADING ====================
	
	def create_file_status_widgets(self):
		"""Create file status indicators."""
		# File status labels (initially hidden)
		self.file_labels = {}
		
		for file_type, filename in self.default_files.items():
			frame = ttk.Frame(self.file_status_frame)
			
			# Status indicator
			status_label = ttk.Label(frame, text="●", foreground="red", font=("Arial", 12))
			status_label.pack(side=tk.LEFT)
			
			# File name
			name_label = ttk.Label(frame, text=filename, width=35)
			name_label.pack(side=tk.LEFT, padx=(5, 0))
			
			# Browse individual file button (initially hidden)
			browse_btn = ttk.Button(frame, text="Browse", 
								  command=lambda ft=file_type: self.browse_individual_file(ft),
								  state=tk.DISABLED)
			browse_btn.pack(side=tk.RIGHT)
			
			self.file_labels[file_type] = {
				'frame': frame,
				'status': status_label,
				'name': name_label,
				'browse': browse_btn
			}

	def browse_flow_folder(self):
		"""Browse for flow folder containing configuration files."""
		folder_path = filedialog.askdirectory(title="Select Flow Configuration Folder")
		
		if not folder_path:
			return
		
		self.flow_folder = folder_path
		self.flow_config.flow_folder = folder_path
		self.folder_entry.configure(state='normal')
		self.folder_entry.delete(0, tk.END)
		self.folder_entry.insert(0, folder_path)
		self.folder_entry.configure(state='readonly')
		
		self.log_status(f"Selected flow folder: {folder_path}")
		
		# Check for default files
		self.check_default_files()

	def check_default_files(self):
		"""Check for default configuration files in the selected folder."""
		if not self.flow_folder:
			return
		
		found_files = {}
		missing_files = []
		
		# Show file status frame
		self.file_status_frame.pack(fill=tk.X, padx=10, pady=5)
		
		for file_type, filename in self.default_files.items():
			file_path = os.path.join(self.flow_folder, filename)
			frame_info = self.file_labels[file_type]
			
			# Show the frame
			frame_info['frame'].pack(fill=tk.X, pady=2)
			
			if os.path.exists(file_path):
				# File found
				found_files[file_type] = file_path
				frame_info['status'].configure(foreground="green")
				frame_info['browse'].configure(state=tk.DISABLED)
				self.log_status(f"Found {filename}")
			else:
				# File not found
				missing_files.append(file_type)
				frame_info['status'].configure(foreground="red")
				frame_info['browse'].configure(state=tk.NORMAL)
				self.log_status(f"Missing {filename}", "warning")
		
		# Store found file paths
		self.structure_path = found_files.get('structure')
		self.flows_path = found_files.get('flows')
		self.ini_path = found_files.get('ini')
		
		# Update flow config
		self.flow_config.structure_path = self.structure_path
		self.flow_config.flows_path = self.flows_path
		self.flow_config.ini_path = self.ini_path
		
		if missing_files:
			# Show message about missing files
			missing_list = [self.default_files[ft] for ft in missing_files]
			message = f"Missing files:\n" + "\n".join(f"• {f}" for f in missing_list)
			message += "\n\nPlease use the Browse buttons to select these files individually."
			
			messagebox.showwarning("Missing Configuration Files", message)
			self.log_status("Some configuration files are missing. Please browse for them individually.", "warning")
		else:
			# All files found, try to load the flow
			self.log_status("All configuration files found. Loading flow...")
			self.load_flow_configuration()

	def browse_individual_file(self, file_type):
		"""Browse for individual configuration file."""
		filename = self.default_files[file_type]
		
		# Determine file type for dialog
		if file_type in ['structure', 'flows']:
			filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
		else:  # ini
			filetypes = [("INI files", "*.ini"), ("All files", "*.*")]
		
		file_path = filedialog.askopenfilename(
			title=f"Select {filename}",
			filetypes=filetypes
		)
		
		if not file_path:
			return
		
		# Update the corresponding path
		if file_type == 'structure':
			self.structure_path = file_path
			self.flow_config.structure_path = file_path
		elif file_type == 'flows':
			self.flows_path = file_path
			self.flow_config.flows_path = file_path
		elif file_type == 'ini':
			self.ini_path = file_path
			self.flow_config.ini_path = file_path
		
		# Update UI
		frame_info = self.file_labels[file_type]
		frame_info['status'].configure(foreground="green")
		frame_info['name'].configure(text=os.path.basename(file_path))
		frame_info['browse'].configure(state=tk.DISABLED)
		
		self.log_status(f"Selected {file_type} file: {os.path.basename(file_path)}")
		
		# Check if all files are now available
		if all([self.structure_path, self.flows_path, self.ini_path]):
			self.log_status("All configuration files selected. Loading flow...")
			self.load_flow_configuration()

	def load_flow_configuration(self):
		"""Load the flow configuration from selected files with enhanced validation."""
		try:
			# FIXED: Ensure all required attributes exist after cleanup
			self._ensure_required_attributes()
		
			# Load using flow config - PASS execution_state here
			success, error = self.flow_config.load_configuration(
				self.structure_path, self.flows_path, self.ini_path,
				framework=self.framework, 
				logger=self.log_status,
				execution_state=self.execution_state  # Pass ThreadsHandler
			)
			
			if not success:
				raise ValueError(error)
			
			# Update references for compatibility
			self.builder = self.flow_config.builder
			self.executor = self.flow_config.executor  # Executor created by builder
			self.root_node = self.flow_config.root_node
			
			# Update total nodes count
			self.total_nodes = len(self.builder.builtNodes)

			# FIXED: Reset execution tracking after new load
			self._reset_execution_tracking()
					
			# Log flow summary
			self.log_flow_summary()
			
			# Draw the flow diagram
			self.draw_flow_diagram()
			
			# Enable start button
			self.run_button.configure(state=tk.NORMAL)
			
			self.log_status(f"Flow loaded successfully with {self.total_nodes} nodes", "success")
			self.log_status(f"Start node: {self.root_node.ID} ({self.root_node.Name})")
			self.log_status("Ready to start execution")
			
		except Exception as e:
			error_msg = f"Error loading flow configuration: {str(e)}"
			self.log_status(error_msg, "error")
			messagebox.showerror("Configuration Error", error_msg)
			
			# Reset UI state
			self.builder = None
			self.executor = None
			self.root_node = None
			self.run_button.configure(state=tk.DISABLED)
			self.show_canvas_message("Error loading configuration. Please check files and try again.")

	def _ensure_required_attributes(self):
		"""Ensure all required attributes exist after cleanup."""
		# Initialize attributes that might be missing after cleanup
		if not hasattr(self, 'completed_nodes'):
			self.completed_nodes = set()
		if not hasattr(self, 'failed_nodes'):
			self.failed_nodes = set()
		if not hasattr(self, 'node_widgets'):
			self.node_widgets = {}
		if not hasattr(self, 'connection_lines'):
			self.connection_lines = {}
		if not hasattr(self, 'current_positions'):
			self.current_positions = {}
		if not hasattr(self, 'completed_count'):
			self.completed_count = 0
		if not hasattr(self, 'failed_count'):
			self.failed_count = 0

	def _reset_execution_tracking(self):
		"""Reset execution tracking for new configuration."""
		self.completed_nodes.clear()
		self.failed_nodes.clear()
		self.completed_count = 0
		self.failed_count = 0
		self.current_node = None
		
		# Reset progress
		if hasattr(self, 'progress_var'):
			self.progress_var.set(0)
		if hasattr(self, 'progress_label'):
			self.progress_label.configure(text="0%")
				
	def show_canvas_message(self, message):
		"""Show a message on the canvas when no flow is loaded."""
		self.canvas.delete("all")
		self.canvas.create_text(
			400, 300, text=message, 
			font=("Arial", 14), 
			fill="gray",
			width=600
		)

	def draw_flow_diagram(self):
		"""Draw the complete flow diagram with nodes and connections."""
		if not self.builder:
			self.show_canvas_message("No flow configuration loaded")
			return
		
		# Calculate positions using layout manager
		calculated_positions = self.layout_manager.calculate_hierarchical_layout(self.builder)
		
		# Merge with custom positions
		self.current_positions = {}
		for node_id, calc_pos in calculated_positions.items():
			self.current_positions[node_id] = self.layout_manager.get_node_position(node_id, {node_id: calc_pos})
		
		# Update drag handler with nodes and positions
		nodes = list(self.builder.builtNodes.values())
		self.drag_handler.set_nodes_and_positions(nodes, self.current_positions)
		
		# Clear canvas
		self.canvas.delete("all")
		self.node_widgets.clear()
		self.connection_lines.clear()
		
		# Update total nodes label
		self.total_nodes_label.configure(text=f"Total: {self.total_nodes}")
		
		# Draw connections first
		self.connection_drawer.draw_connections(nodes, self.current_positions)
		
		# Draw nodes
		for node in nodes:
			if node.ID in self.current_positions:
				pos = self.current_positions[node.ID]
				status = self.get_node_status_color(node)
				self.node_drawer.draw_single_node(node, pos, status)
		
		# Update canvas scroll region
		self.update_canvas_scroll_region(self.current_positions)

	def update_canvas_scroll_region(self, positions):
		"""Update canvas scroll region based on node positions."""
		if not positions:
			return
		
		# Calculate bounds
		min_x = min_y = float('inf')
		max_x = max_y = float('-inf')
		
		for pos in positions.values():
			min_x = min(min_x, pos['x'])
			min_y = min(min_y, pos['y'])
			max_x = max(max_x, pos['x'] + pos['width'])
			max_y = max(max_y, pos['y'] + pos['height'])
		
		# Add margin
		margin = 100
		self.canvas.configure(scrollregion=(
			min_x - margin, min_y - margin,
			max_x + margin, max_y + margin
		))

	def get_node_status_color(self, node):
		"""Determine node color based on current execution status."""
		node_id = node.ID
		
		# Check if this is the currently executing node
		if hasattr(self, 'current_node') and self.current_node and node_id == self.current_node.ID:
			# Check if experiment is actually running
			if self.is_experiment_running(node):
				return 'running'  # Red - experiment is running
			else:
				return 'current'  # Blue - node selected but not running yet
		
		# Check completion status
		if hasattr(self, 'completed_nodes') and node_id in self.completed_nodes:
			return 'completed'  # Green - done successfully
		
		if hasattr(self, 'failed_nodes') and node_id in self.failed_nodes:
			# Check if it's execution failure vs other failure
			if self.is_execution_failure(node):
				return 'execution_fail'  # Yellow - execution failed
			else:
				return 'failed'  # Red - other failure
		
		# Default state
		return 'idle'  # Gray - waiting

	def is_experiment_running(self, node):
		"""Check if the experiment is currently running for this node."""
		if hasattr(self, 'shared_framework_api') and self.shared_framework_api is not None:
			return self.shared_framework_api.is_experiment_running()
		return False

	def is_execution_failure(self, node):
		"""Determine if the failure was due to execution issues (yellow) vs test failures (red)."""
		# Check the run status history for execution vs test failures
		if hasattr(node, 'runStatusHistory') and node.runStatusHistory:
			# If we have detailed execution stats, use them
			if hasattr(node, 'execution_stats') and node.execution_stats:
				# Execution failure indicators
				if 'execution_error' in str(node.execution_stats).lower():
					return True
				if 'timeout' in str(node.execution_stats).lower():
					return True
			
			# Check for specific failure patterns
			if 'FAILED' in node.runStatusHistory:  # Framework execution failure
				return True
			if len(node.runStatusHistory) == 1 and 'FAIL' in node.runStatusHistory:
				# Single failure might be execution issue
				return True
		
		return False  # Regular test failure

	def log_flow_summary(self):
		"""Log a summary of the loaded flow."""
		summary = self.get_flow_summary()
		
		if not summary:
			return
		
		self.log_status("=== FLOW SUMMARY ===")
		self.log_status(f"Total Nodes: {summary['total_nodes']}")
		self.log_status(f"Start Node: {summary['start_node']} ({summary['start_node_name']})")
		self.log_status(f"Total Connections: {summary['total_connections']}")
		
		if summary['node_types']:
			self.log_status("Node Types:")
			for node_type, count in summary['node_types'].items():
				self.log_status(f"  {node_type}: {count}")
		
		if summary['experiments_used']:
			self.log_status(f"Experiments Used: {len(summary['experiments_used'])}")
			for exp in summary['experiments_used']:
				self.log_status(f"  - {exp}")
		
		self.log_status("==================")

	def get_flow_summary(self):
		"""Get a summary of the loaded flow."""
		if not self.builder:
			return {}
		
		try:
			summary = {
				'total_nodes': len(self.builder.structureFile),
				'start_node': self.root_node.ID if self.root_node else None,
				'start_node_name': self.root_node.Name if self.root_node else None,
				'node_types': {},
				'experiments_used': set(),
				'total_connections': 0
			}
			
			# Analyze node types and connections
			for node_id, node_config in self.builder.structureFile.items():
				node_type = node_config.get("instanceType", "Unknown")
				summary['node_types'][node_type] = summary['node_types'].get(node_type, 0) + 1
				
				# Count connections
				output_map = node_config.get("outputNodeMap", {})
				summary['total_connections'] += len(output_map)
				
				# Track experiments
				flow_name = node_config.get("flow")
				if flow_name and flow_name in self.builder.flowsFile:
					summary['experiments_used'].add(flow_name)
			
			summary['experiments_used'] = list(summary['experiments_used'])
			
			return summary
			
		except Exception as e:
			self.log_status(f"Error generating flow summary: {str(e)}", "error")
			return {}

	# ==================== EXECUTION CONTROL ====================

	# SIMPLIFIED: Direct execution start
	def start_execution(self):
		"""SIMPLIFIED: Start flow execution using builder-created executor."""
		if self.execution_state.get_state('execution_active'):
			self.log_status("Flow execution already running", "warning")
			return

		if not self.flow_config.root_node:
			self.log_status("No flow loaded - please load a flow configuration first", "error")
			return

		# Clear any previous commands
		self.execution_state.clear_all_commands()
		
		# Create shared Framework API
		success, api_or_error = self._create_shared_framework_api()
		if not success:
			self.log_status(f"Failed to create Framework API: {api_or_error}", "error")
			return

		# SIMPLIFIED: Use executor from flow_config (created by builder)
		self.executor = self.flow_config.executor
		if not self.executor:
			self.log_status("No executor available from flow configuration", "error")
			return
			
		# Set Framework API and callback on existing executor
		self.executor.set_framework_api(self.shared_framework_api)
		self.executor.set_status_callback(self._handle_executor_status)
		
		# Set execution state
		self.execution_state.update_state(
			execution_active=True,
			current_experiment=None,
			current_iteration=0,
			total_iterations=self.total_nodes
		)
		
		# Update UI
		self.is_running = True
		self.start_time = time.time()
		self._update_ui_for_start()
		
		# Start execution thread
		self.execution_thread = threading.Thread(
			target=self._simple_execution_thread,
			daemon=True,
			name=f"FlowExecution_{self.framework_instance_id}"
		)
		self.execution_thread.start()
		
		self.log_status("Started automation flow execution", "success")
		
	def _create_shared_framework_api(self):
		"""Create shared Framework API for entire flow execution."""
		try:
			if not self.framework_manager:
				return False, "No Framework manager available"

			self.framework_instance_id = f"flow_framework_{int(time.time() * 1000)}"
			
			self.shared_framework_api = self.framework_manager.create_framework_instance(
				status_reporter=self.main_thread_handler,
				execution_state=self.execution_state  # Pass ThreadsHandler directly
			)
			
			if not self.shared_framework_api:
				return False, "Framework manager returned None"

			print(f"Created shared Framework API: {self.framework_instance_id}")
			return True, self.shared_framework_api
			
		except Exception as e:
			return False, str(e)

	def _simple_execution_thread(self):
		"""SIMPLIFIED: Execute flow using FlowTestExecutor with ThreadsHandler."""
		try:
			# Notify start
			if self.main_thread_handler:
				self.main_thread_handler.queue_status_update({
					'type': 'flow_execution_setup',
					'data': {'total_nodes': self.total_nodes}
				})

			# Execute flow using FlowTestExecutor - it will handle command checking
			self.executor.execute()
			
			# Check final state
			if self.execution_state.is_cancelled():
				if self.main_thread_handler:
					self.main_thread_handler.queue_status_update({
						'type': 'flow_execution_cancelled',
						'data': {'reason':'Final Check'}
					})
			elif self.execution_state.is_ended():
				if self.main_thread_handler:
					self.main_thread_handler.queue_status_update({
						'type': 'flow_execution_ended_complete',
						'data': {'framework_instance_id':self.framework_instance_id}
					})
			else:
				# Normal completion
				if self.main_thread_handler:
					self.main_thread_handler.queue_status_update({
						'type': 'flow_execution_complete',
						'data': {'framework_instance_id':self.framework_instance_id}
					})
			
		except Exception as e:
			if self.main_thread_handler:
				self.main_thread_handler.queue_status_update({
					'type': 'flow_execution_error',
					'data': str(e)
				})
		finally:
			# SIMPLIFIED: Safe cleanup
			self._safe_cleanup()

	def _get_experiment_name(self, node):
		"""Get experiment name for display."""
		if hasattr(node, 'Experiment') and node.Experiment:
			return node.Experiment.get('Test Name', f"Node: {node.Name}")
		return f"Node: {node.Name}"

	def _has_system_failure(self, node):
		"""Check for system-level failures."""
		if not hasattr(node, 'runStatusHistory') or not node.runStatusHistory:
			return False
		
		system_failure_statuses = ['FAILED', 'ExecutionFAIL', 'CANCELLED', 'PythonFail']
		return any(status in system_failure_statuses for status in node.runStatusHistory)

	def _determine_node_success(self, node):
		"""Determine if node execution was successful (PASS/FAIL only)."""
		if not hasattr(node, 'runStatusHistory') or not node.runStatusHistory:
			return True
		
		# Only consider PASS/FAIL for flow routing
		test_results = [status for status in node.runStatusHistory if status in ['PASS', 'FAIL']]
		
		if not test_results:
			return not self._has_system_failure(node)
		
		return test_results.count('FAIL') == 0

	def _handle_executor_status(self, status_type, data):
		"""Handle status updates from executor."""
		if self.main_thread_handler:
			self.main_thread_handler.queue_status_update({
				'type': status_type,
				'data': data
			})

	def _safe_cleanup(self):
		"""SIMPLIFIED: Safe cleanup without issuing commands."""
		try:
			# Update ThreadsHandler state
			self.execution_state.update_state(execution_active=False)
			
			# Clean up Framework API - NO COMMANDS ISSUED
			if self.shared_framework_api and self.framework_manager:
				try:
					# Direct cleanup through manager
					self.framework_manager.cleanup_current_instance("execution_complete")
				except Exception as e:
					print(f"Framework cleanup error: {e}")
			
			# Clear references
			self.shared_framework_api = None
			self.framework_instance_id = None
			self.executor = None
			
			print("Safe cleanup completed")
			
		except Exception as e:
			print(f"Safe cleanup error: {e}")

	# SIMPLIFIED: Direct command methods using ThreadsHandler
	def cancel_execution(self):
		"""Cancel execution using ThreadsHandler directly."""
		success = self.execution_state.cancel("User requested cancellation")
		
		if success:
			self.status_label.configure(text=" Cancelling... ", bg="orange", fg="black")
			self.cancel_button.configure(state=tk.DISABLED)
			self.log_status("Cancellation requested")
		
		return success

	def toggle_framework_hold(self):
		"""Toggle framework halt/continue using shared API directly."""
		if not self.shared_framework_api:
			self.log_status("No Framework API available", "warning")
			return

		try:
			state = self.shared_framework_api.get_current_state()

			if state.get('is_halted', False):
				result = self.shared_framework_api.continue_execution()
				if result['success']:
					self.hold_button.configure(text="Hold", style="Hold.TButton")
					self.log_status(result['message'])
			else:
				result = self.shared_framework_api.halt_execution()
				if result['success']:
					self.hold_button.configure(text="Continue", style="Continue.TButton")
					self.log_status(result['message'])
					
		except Exception as e:
			self.log_status(f"Framework control error: {e}", "error")

	def end_current_experiment(self):
		"""End current experiment using ThreadsHandler."""
		success = self.execution_state.end_experiment("User requested end")
		
		if success:
			self.log_status("End experiment requested")
			self.end_button.configure(text="Ending...", state=tk.DISABLED)
		
		return success
				
	def _update_ui_for_start(self):
		"""Update UI elements for execution start (matching ControlPanel)."""
		try:
			self.status_label.configure(text=" Running ", bg="#BF0000", fg="white")
			self.log_status("Starting flow execution", "success")
			
			# FIXED: Reset progress tracking at start
			self.reset_progress_tracking()
			
			# Reset node statuses
			for node_id in self.node_widgets.keys():
				self._update_node_status_safe(node_id, "Idle", self.node_colors['idle'], 'black')
			
			# Update button states
			self.run_button.configure(state=tk.DISABLED)
			self.cancel_button.configure(state=tk.NORMAL)
			self.end_button.configure(state=tk.NORMAL, text="End", style="End.TButton")
			self.hold_button.configure(state=tk.NORMAL, text="Hold", style="Hold.TButton")
			self.browse_button.configure(state=tk.DISABLED)
			
			# Disable dragging controls during execution
			self.drag_checkbox.configure(state=tk.DISABLED)
			self.snap_checkbox.configure(state=tk.DISABLED)
			self.reset_positions_button.configure(state=tk.DISABLED)
			self.refresh_button.configure(state=tk.DISABLED)
			self.drag_handler.enable_dragging(False)
			
		except Exception as e:
			self.log_status(f"Error updating UI for start: {e}", "error")

	def _cleanup_after_cancel(self):
		"""Cleanup after cancellation with command system (matching ControlPanel)."""
		if self._cleanup_in_progress:
			return
		try:
			# Check if cancellation was processed
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
				if self._cancel_retry_count < 10:  # Max 5 seconds
					self.root.after(500, self._cleanup_after_cancel)
				else:
					# Force cleanup after timeout
					self.log_status("Force cleanup after cancel timeout")
					self._reset_buttons_after_cancel()
					self._cancel_retry_count = 0
				
		except Exception as e:
			self.log_status(f"Error in cancel cleanup: {e}")

	# **ADD** cleanup method matching ControlPanel:
	def _cleanup_previous_framework(self):
		"""Clean up previous framework instance (matching ControlPanel)."""
		try:
			if hasattr(self, 'current_framework_instance_id') and self.current_framework_instance_id:
				self.log_status(f"Cleaning up framework instance: {self.current_framework_instance_id}")
				
				if self.framework_api:
					try:
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

	def _cleanup_previous_execution(self):
		"""Clean up previous execution state."""
		# Clear Framework API reference (will be recreated by execution manager)
		self.framework_api = None
		
		# Reset execution state
		self.is_running = False
		self.thread_active = False
		
		# Clear node statuses
		self._cleanup_node_statuses()

		# Reset progress bars
		self.progress_var.set(0)
		self.progress_label.configure(text="0%")

	# **ADD** node status cleanup:
	def _cleanup_node_statuses(self):
		"""Clean up node statuses when starting new run."""
		try:
			if self.node_drawer and hasattr(self.node_drawer, 'node_widgets'):
				for node_id, widget_info in self.node_drawer.node_widgets.items():
					# Reset to idle state
					if self.builder and node_id in self.builder.builtNodes:
						node = self.builder.builtNodes[node_id]
						self.node_drawer.redraw_node(node, 'idle')
						
		except Exception as e:
			self.log_status(f"[ERROR] Node status cleanup failed: {e}")

	def _reset_buttons_after_cancel(self):
		"""Reset buttons after cancellation is complete (matching ControlPanel)."""
		try:
			self.thread_active = False
			self.is_running = False

			self.run_button.configure(state=tk.NORMAL)
			self.cancel_button.configure(state=tk.DISABLED)
			self.hold_button.configure(state=tk.DISABLED, text="Hold", style="Hold.TButton")
			self.end_button.configure(state=tk.DISABLED, text="End", style="End.TButton")
			self.browse_button.configure(state=tk.NORMAL)
			
			# Re-enable dragging controls after execution
			if hasattr(self, 'drag_checkbox'):
				self.drag_checkbox.configure(state=tk.NORMAL)
				self.snap_checkbox.configure(state=tk.NORMAL)
				self.reset_positions_button.configure(state=tk.NORMAL)
				self.drag_handler.enable_dragging(self.drag_enabled_var.get())
			
			# Final status update
			self.root.after(2000, lambda: self.status_label.configure(text=" Ready ", bg="white", fg="black"))
			
			# Reset cancel retry
			if hasattr(self, '_cancel_retry_count'):
				self._cancel_retry_count = 0
				
		except Exception as e:
			self.log_status(f"Error resetting buttons: {e}")

	def _update_node_status_safe(self, node_id: str, status: str, bg_color: str, fg_color: str):
		"""Safely update node status with error handling."""
		try:
			if node_id in self.node_widgets:
				# Find the node object
				node_obj = None
				if self.builder:
					node_obj = self.builder.builtNodes.get(node_id)
				
				if node_obj:
					# Use node drawer to redraw with new status
					status_map = {
						'Idle': 'idle',
						'Running': 'running',
						'Completed': 'completed',
						'Failed': 'failed'
					}
					new_status = status_map.get(status, 'idle')
					self.node_drawer.redraw_node(node_obj, new_status)
		except Exception as e:
			self.log_status(f"[ERROR] Node status update failed for {node_id}: {e}", "error")

	# ==================== UPDATE PROCESSING & UI COORDINATION ====================

	# SIMPLIFIED: Handle updates from ThreadsHandler
	def handle_main_thread_update(self, update):
		"""ENHANCED: Handle updates from ThreadsHandler with Framework execution support."""
		update_type = update.get('type')
		data = update.get('data', {})
		
		# Flow-specific updates
		if update_type == 'flow_execution_complete':
			self.execution_completed()
		elif update_type == 'flow_execution_error':
			self.execution_error(data)
		elif update_type == 'current_node':
			self.update_current_node(data)
		elif update_type == 'node_completed':
			self.update_node_completed(data)
		elif update_type == 'node_failed':
			self.update_node_failed(data)
		elif update_type == 'flow_execution_setup':
			self.log_status(f"Flow setup: {data.get('total_nodes', 0)} nodes")
		elif update_type == 'flow_execution_ended_complete':
			self.execution_ended()
		elif update_type == 'flow_execution_cancelled':
			self.execution_cancelled()
		elif update_type == 'node_running':
			node_data = data if isinstance(data, dict) else {'node_id': getattr(data, 'ID', 'Unknown')}
			self.update_node_running(node_data)
		elif update_type == 'node_execution_fail':
			node_data = data if isinstance(data, dict) else {'node_id': getattr(data, 'ID', 'Unknown')}
			self.update_node_execution_fail(node_data)
		elif update_type == 'node_error':
			node_data = data if isinstance(data, dict) else {'node_id': getattr(data, 'ID', 'Unknown')}
			self.update_node_error(node_data)
		elif update_type == 'status_update':
			message = data.get('message', '') if isinstance(data, dict) else str(data)
			if message:
				self.log_status(message)
		
		# ADDED: Framework execution updates for automation
		elif update_type == 'experiment_start':
			self._handle_framework_experiment_start(data)
		elif update_type == 'strategy_progress':
			self._handle_framework_strategy_progress(data)
		elif update_type == 'iteration_start':
			self._handle_framework_iteration_start(data)
		elif update_type == 'iteration_progress':
			self._handle_framework_iteration_progress(data)
		elif update_type == 'iteration_complete':
			self._handle_framework_iteration_complete(data)
		elif update_type == 'strategy_complete':
			self._handle_framework_strategy_complete(data)
		elif update_type == 'experiment_complete':
			self._handle_framework_experiment_complete(data)
		elif update_type == 'experiment_end_requested':
			self._handle_framework_experiment_end_requested(data)
		elif update_type == 'experiment_ended_by_command':
			self._handle_framework_experiment_ended_by_command(data)
		elif update_type == 'strategy_execution_complete':
			self._handle_framework_strategy_execution_complete(data)
		elif update_type == 'execution_prepared':
			self._handle_framework_execution_prepared(data)
		elif update_type == 'step_mode_enabled':
			self._handle_framework_step_mode_enabled(data)
		elif update_type == 'step_continue_issued':
			self._handle_framework_step_continue_issued(data)
		elif update_type == 'execution_finalized':
			self._handle_framework_execution_finalized(data)
		
		# Node completion handlers
		elif update_type == 'node_complete':
			# This is different from 'node_completed' - just logs completion
			node_data = data if isinstance(data, dict) else {'node_id': getattr(data, 'ID', 'Unknown')}
			node_id = node_data.get('node_id', 'Unknown')
			self.log_status(f"Node {node_id} execution finished")
		
		else:
			# Log unknown update types for debugging (but don't spam with DEBUG level)
			if update_type not in ['log_message', 'node_start']:  # Skip common ones
				self.log_status(f"Unhandled update type: {update_type}", "debug")

		# FIXED: Always update progress after any node-related update
		if update_type in ['node_completed', 'node_failed', 'node_execution_fail', 'current_node', 
						'iteration_complete', 'strategy_progress']:
			self.update_progress()

	def update_current_node(self, node_data):
		"""Update the current executing node with enhanced status tracking."""
		# Handle both node object and dict data
		if isinstance(node_data, dict):
			node_id = node_data.get('node_id')
			node_name = node_data.get('node_name', 'Unknown')
			experiment_name = node_data.get('experiment_name', 'Unknown')
			# Find actual node object
			node = None
			if self.builder and node_id:
				node = self.builder.builtNodes.get(node_id)
		else:
			# Legacy node object
			node = node_data
			node_id = node.ID
			node_name = node.Name
			experiment_name = self._get_experiment_name(node)
		
		if not node:
			self.log_status(f"Warning: Could not find node {node_id} in built nodes", "warning")
			return
		
		self.current_node = node
		self.execution_state.update_state(current_experiment=f"Node: {node.Name}")
		
		# Update UI labels
		self.current_node_label.configure(text=f"Node: {node_name} ({node_id})")
		self.current_experiment_label.configure(text=f"Experiment: {experiment_name}")
		self.current_status_label.configure(text="Status: Preparing", foreground='blue')
		
		# FIXED: Update node visual status immediately to blue (current)
		if self.node_drawer:
			self.node_drawer.redraw_node(node, 'current')
			self.log_status(f"Updated node {node_id} to 'current' status", "debug")
		
		# Update progress
		self.update_progress()
		
		self.log_status(f"Executing node: {node_name} ({node_id})")

	def update_node_running(self, node_data):
		"""Update node as running (red)."""
		# Handle both dict and object data
		if isinstance(node_data, dict):
			node_id = node_data.get('node_id')
			node_name = node_data.get('node_name', 'Unknown')
			if self.builder and node_id:
				node = self.builder.builtNodes.get(node_id)
			else:
				node = None
		else:
			node = node_data
			node_id = node.ID
			node_name = node.Name
		
		if node and self.node_drawer:
			self.node_drawer.redraw_node(node, 'running')
			self.log_status(f"Updated node {node_id} to 'running' status", "debug")
		
		self.current_status_label.configure(text="Status: Running Experiment", foreground='red')

	def update_node_completed(self, node_data):
		"""Update node as completed (Green)."""
		if isinstance(node_data, dict):
			node_id = node_data.get('node_id', 'Unknown')
			node_name = node_data.get('node_name', 'Unknown')
			if self.builder and node_id:
				node = self.builder.builtNodes.get(node_id)
			else:
				node = None
		else:
			node = node_data
			node_id = getattr(node_data, 'ID', 'Unknown')
			node_name = getattr(node_data, 'Name', 'Unknown')
		
		# Only increment if not already counted
		if node_id not in self.completed_nodes:
			self.completed_nodes.add(node_id)
			self.completed_count += 1
			
			# Update execution_state with correct progress
			self.execution_state.update_state(
				current_experiment=f"Completed: {node_id}",
				current_iteration=self.completed_count + self.failed_count
			)
		
		# Update statistics display
		self.completed_nodes_label.configure(text=f"✓ Completed: {self.completed_count}")
		
		# FIXED: Update node visual status to green (completed)
		if node and self.node_drawer:
			self.node_drawer.redraw_node(node, 'completed')
			self.log_status(f"Updated node {node_id} to 'completed' status", "debug")
		
		# Update progress
		self.update_progress()
		
		self.log_status(f"Experiment completed: {node_name}", "success")
		
	def update_node_failed(self, node_data):
		"""Update node as failed (red)."""
		if isinstance(node_data, dict):
			node_id = node_data.get('node_id', 'Unknown')
			node_name = node_data.get('node_name', 'Unknown')
			if self.builder and node_id:
				node = self.builder.builtNodes.get(node_id)
			else:
				node = None
		else:
			node = node_data
			node_id = getattr(node_data, 'ID', 'Unknown')
			node_name = getattr(node_data, 'Name', 'Unknown')
		
		# Only increment if not already counted
		if node_id not in self.failed_nodes:
			self.failed_nodes.add(node_id)
			self.failed_count += 1
			
			# Update execution_state with correct progress
			self.execution_state.update_state(
				current_experiment=f"Failed: {node_id}",
				current_iteration=self.completed_count + self.failed_count
			)
		
		# Update statistics
		self.failed_nodes_label.configure(text=f"✗ Failed: {self.failed_count}")
		
		# FIXED: Update node visual status to red (failed)
		if node and self.node_drawer:
			self.node_drawer.redraw_node(node, 'failed')
			self.log_status(f"Updated node {node_id} to 'failed' status", "debug")
		
		# Update progress
		self.update_progress()
		
		self.log_status(f"Node test failed: {node_name}", "error")

	def update_node_error(self, node_data):
		"""Handle node error."""
		if isinstance(node_data, dict):
			node_id = node_data.get('node_id', 'Unknown')
			error = node_data.get('error', 'Unknown error')
		else:
			node_id = getattr(node_data, 'ID', 'Unknown')
			error = str(node_data)
		
		# Treat node errors as execution failures (yellow)
		self.failed_nodes.add(node_id)
		self.failed_count += 1
		self.execution_state.update_state(current_node_status='failed')
		
		# Update statistics
		self.failed_nodes_label.configure(text=f"✗ Failed: {self.failed_count}")
		
		# Update node visual status as execution failure
		if self.builder:
			node = self.builder.builtNodes.get(node_id)
			if node:
				self.node_drawer.redraw_node(node, 'execution_fail')
		
		# Update progress
		self.update_progress()
		
		self.log_status(f"Node error: {node_id} - {error}", "error")

	def update_node_execution_fail(self, node_data):
		"""Update node as execution failed (Yellow)."""
		if isinstance(node_data, dict):
			node_id = node_data.get('node_id', 'Unknown')
			node_name = node_data.get('node_name', 'Unknown')
			if self.builder and node_id:
				node = self.builder.builtNodes.get(node_id)
			else:
				node = None
		else:
			node = node_data
			node_id = getattr(node_data, 'ID', 'Unknown')
			node_name = getattr(node_data, 'Name', 'Unknown')
		
		# Only increment if not already counted
		if node_id not in self.failed_nodes:
			self.failed_nodes.add(node_id)
			self.failed_count += 1
		
		# Update statistics
		self.failed_nodes_label.configure(text=f"✗ Failed: {self.failed_count}")
		
		# FIXED: Update node visual status to yellow (execution_fail)
		if node and self.node_drawer:
			self.node_drawer.redraw_node(node, 'execution_fail')
			self.log_status(f"Updated node {node_id} to 'execution_fail' status", "debug")
		
		# Update progress
		self.update_progress()
		
		self.log_status(f"Node execution failed: {node_name}", "warning")

	def update_progress(self):
		"""Update overall progress based on EXPERIMENTS (nodes), not iterations."""
		if self.total_nodes > 0:
			# Progress based on completed experiments (nodes)
			completed_total = self.completed_count + self.failed_count
			progress = (completed_total / self.total_nodes) * 100
			
			# Ensure progress doesn't exceed 100%
			progress = min(progress, 100.0)
			
			self.progress_var.set(progress)
			self.progress_label.configure(text=f"{int(progress)}%")

			# Update execution_state with correct values
			if self.execution_state:
				self.execution_state.update_state(
					current_iteration=completed_total,
					total_iterations=self.total_nodes
				)
							
			# Update shared status panel if available with correct values
			if HAS_STATUS_PANEL and hasattr(self.status_panel, 'update_overall_progress'):
				# Use 0-based indexing for current experiment
				current_experiment_index = max(0, completed_total - 1) if completed_total > 0 else 0
				
				self.status_panel.update_overall_progress(
					current_experiment_index,  # Current experiment index (0-based)
					self.total_nodes,         # Total experiments
					1.0 if completed_total > 0 else 0.0  # Current experiment progress (completed = 1.0)
				)
				
			# FIXED: Debug logging to track progress updates
			self.log_status(f"Flow Progress: {completed_total}/{self.total_nodes} = {progress:.1f}%", "debug")
		
		# Update timing
		if self.start_time:
			elapsed = time.time() - self.start_time
			if hasattr(self, 'status_panel') and hasattr(self.status_panel, 'elapsed_time_label'):
				self.status_panel.elapsed_time_label.configure(text=f"Time: {self._format_time(elapsed)}")
	
	# SIMPLIFIED: Execution completion handlers
	def execution_completed(self):
		"""Handle normal execution completion."""
		self.is_running = False
		self._enable_ui_buttons_safe()
		self.execution_state.update_state(execution_active=False)

		total_time = time.time() - self.start_time if self.start_time else 0
		self.log_status(f"Flow execution completed in {self._format_time(total_time)}", "success")
		self.status_label.configure(text=" Completed ", bg="#006400", fg="white")

	def execution_ended(self):
		"""Handle execution ended by END command."""
		self.is_running = False
		self.execution_state.update_state(execution_active=False)
		
		# Update UI
		self._enable_ui_buttons_safe()
		self.current_status_label.configure(text="Status: Ended")
		
		total_time = time.time() - self.start_time if self.start_time else 0
		self.log_status(f"Flow execution ended by command in {self._format_time(total_time)}", "warning")
		self.log_status(f"Results: {self.completed_count} completed, {self.failed_count} failed")
		
		self.status_label.configure(text=" Ended ", bg="orange", fg="black")

	def execution_cancelled(self):
		"""Handle execution cancellation."""
		self.is_running = False
		self.execution_state.update_state(execution_active=False)
		
		self.current_status_label.configure(text="Status: Cancelled")
		self.log_status("Flow execution cancelled", "warning")
		
		self.status_label.configure(text=" Cancelled ", bg="gray", fg="white")
		self._enable_ui_buttons_safe()

	def execution_error(self, error_msg):
		"""Handle execution error."""
		self.is_running = False
		self.execution_state.update_state(execution_active=False)
		self._enable_ui_buttons_safe()
		self.log_status(f"Execution error: {error_msg}", "error")
		self.status_label.configure(text=" Error ", bg="red", fg="white")

	def _enable_ui_buttons_safe(self):
		"""Safely enable UI buttons with error handling (matching ControlPanel)."""
		try:
			self.run_button.configure(state=tk.NORMAL)
			self.cancel_button.configure(state=tk.DISABLED)
			self.hold_button.configure(state=tk.DISABLED, text="Hold", style="Hold.TButton")
			self.end_button.configure(state=tk.DISABLED, text="End", style="End.TButton")
			self.browse_button.configure(state=tk.NORMAL)
			
			# Re-enable dragging controls
			self.drag_checkbox.configure(state=tk.NORMAL)
			self.snap_checkbox.configure(state=tk.NORMAL)
			self.reset_positions_button.configure(state=tk.NORMAL)
			self.drag_handler.enable_dragging(self.drag_enabled_var.get())
			
		except Exception as e:
			self.log_status(f"Error enabling buttons: {e}", "error")

	def _format_time(self, seconds: float) -> str:
		"""Format seconds to MM:SS format."""
		minutes = int(seconds // 60)
		seconds = int(seconds % 60)
		return f"{minutes:02d}:{seconds:02d}"

# ==================== FRAMEWORK EXECUTION HANDLERS ====================

	def _handle_framework_experiment_start(self, data):
		"""Handle Framework experiment start for current node."""
		try:
			experiment_name = data.get('experiment_name', 'Unknown')
			strategy_type = data.get('strategy_type', 'Unknown')
			total_iterations = data.get('total_iterations', 0)
			
			# Update current experiment info
			if hasattr(self, 'current_experiment_label'):
				self.current_experiment_label.configure(text=f"Experiment: {experiment_name}")
			
			# Update strategy info in status panel
			if hasattr(self, 'status_panel'):
				self.status_panel.update_strategy_info(
					experiment_name=experiment_name,
					strategy_type=strategy_type,
					status="Starting"
				)
			
			# Update current status
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(text="Status: Starting Experiment", foreground='blue')
			
			self.log_status(f"[EXPERIMENT] Started: {experiment_name} ({strategy_type})")
			
		except Exception as e:
			self.log_status(f"Error handling experiment start: {e}", "error")

	def _handle_framework_strategy_progress(self, data):
		"""Handle Framework strategy progress updates."""
		try:
			progress_percent = data.get('progress_percent', 0)
			current_iteration = data.get('current_iteration', 0)
			total_iterations = data.get('total_iterations', 0)
			test_name = data.get('test_name', 'Unknown')
			
			# Update status panel if available
			if hasattr(self, 'status_panel'):
				self.status_panel.update_iteration_progress(
					current_iteration, total_iterations, progress_percent
				)
			
			# Update current status
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(
					text=f"Status: Running ({progress_percent:.1f}%)", 
					foreground='red'
				)
			
			# Update execution_state for progress tracking
			if self.execution_state:
				self.execution_state.update_state(
					current_iteration=current_iteration,
					total_iterations=total_iterations
				)
			
			self.log_status(f"[PROGRESS] {test_name}: {progress_percent:.1f}% ({current_iteration}/{total_iterations})")
			
		except Exception as e:
			self.log_status(f"Error handling strategy progress: {e}", "error")

	def _handle_framework_iteration_start(self, data):
		"""Handle Framework iteration start."""
		try:
			iteration = data.get('iteration', 0)
			status = data.get('status', 'Starting')
			
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(
					text=f"Status: Iteration {iteration} - {status}", 
					foreground='orange'
				)
			
			self.log_status(f"[ITERATION] Starting iteration {iteration}: {status}")
			
		except Exception as e:
			self.log_status(f"Error handling iteration start: {e}", "error")

	def _handle_framework_iteration_progress(self, data):
		"""Handle Framework iteration progress."""
		try:
			iteration = data.get('iteration', 0)
			status = data.get('status', 'Running')
			progress_weight = data.get('progress_weight', 0.0)
			
			# Update current status with progress
			if hasattr(self, 'current_status_label'):
				progress_percent = int(progress_weight * 100)
				self.current_status_label.configure(
					text=f"Status: Iter {iteration} - {status} ({progress_percent}%)", 
					foreground='red'
				)
			
			# Don't log every progress update to avoid spam
			if progress_weight in [0.25, 0.5, 0.75, 1.0]:  # Log at 25% intervals
				self.log_status(f"[PROGRESS] Iteration {iteration}: {int(progress_weight * 100)}%")
			
		except Exception as e:
			self.log_status(f"Error handling iteration progress: {e}", "error")

	def _handle_framework_iteration_complete(self, data):
		"""Handle Framework iteration completion."""
		try:
			iteration = data.get('iteration', 0)
			status = data.get('status', 'Complete')
			scratchpad = data.get('scratchpad', '')
			
			# Update statistics in status panel
			if hasattr(self, 'status_panel'):
				self.status_panel.update_statistics(result_status=status)
			
			# Update current status
			if hasattr(self, 'current_status_label'):
				color = 'green' if status == 'PASS' else 'red' if status == 'FAIL' else 'black'
				self.current_status_label.configure(
					text=f"Status: Iter {iteration} Complete - {status}", 
					foreground=color
				)
			
			# Log with details
			log_msg = f"[COMPLETE] Iteration {iteration}: {status}"
			if scratchpad:
				log_msg += f" ({scratchpad})"
			self.log_status(log_msg)
			
		except Exception as e:
			self.log_status(f"Error handling iteration complete: {e}", "error")

	def _handle_framework_strategy_complete(self, data):
		"""Handle Framework strategy completion."""
		try:
			test_name = data.get('test_name', 'Unknown')
			total_tests = data.get('total_tests', 0)
			success_rate = data.get('success_rate', 0)
			
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(
					text=f"Status: Strategy Complete ({success_rate}%)", 
					foreground='blue'
				)
			
			self.log_status(f"[STRATEGY] Complete: {test_name} - {total_tests} tests, {success_rate}% success")
			
		except Exception as e:
			self.log_status(f"Error handling strategy complete: {e}", "error")

	def _handle_framework_experiment_complete(self, data):
		"""Handle Framework experiment completion."""
		try:
			test_name = data.get('test_name', 'Unknown')
			
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(
					text="Status: Experiment Complete", 
					foreground='green'
				)
			
			self.log_status(f"[EXPERIMENT] Complete: {test_name}")
			
		except Exception as e:
			self.log_status(f"Error handling experiment complete: {e}", "error")

	def _handle_framework_experiment_end_requested(self, data):
		"""Handle Framework experiment end request."""
		try:
			message = data.get('message', 'End requested')
			
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(
					text="Status: Ending Experiment", 
					foreground='orange'
				)
			
			self.log_status(f"[END] {message}")
			
		except Exception as e:
			self.log_status(f"Error handling experiment end request: {e}", "error")

	def _handle_framework_experiment_ended_by_command(self, data):
		"""Handle Framework experiment ended by command."""
		try:
			completed = data.get('completed_iterations', 0)
			total = data.get('total_iterations', 0)
			reason = data.get('reason', 'Command')
			
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(
					text="Status: Ended by Command", 
					foreground='orange'
				)
			
			self.log_status(f"[ENDED] Experiment ended by {reason} after {completed}/{total} iterations")
			
		except Exception as e:
			self.log_status(f"Error handling experiment ended by command: {e}", "error")

	def _handle_framework_strategy_execution_complete(self, data):
		"""Handle Framework strategy execution completion."""
		try:
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(
					text="Status: Strategy Execution Complete", 
					foreground='blue'
				)
			
			self.log_status("[STRATEGY] Execution phase complete")
			
		except Exception as e:
			self.log_status(f"Error handling strategy execution complete: {e}", "error")

	def _handle_framework_execution_prepared(self, data):
		"""Handle Framework execution preparation."""
		try:
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(
					text="Status: Framework Prepared", 
					foreground='blue'
				)
			
			self.log_status("[FRAMEWORK] Execution prepared")
			
		except Exception as e:
			self.log_status(f"Error handling execution prepared: {e}", "error")

	def _handle_framework_step_mode_enabled(self, data):
		"""Handle Framework step mode enabled."""
		try:
			self.log_status("[STEP] Step-by-step mode enabled")
			
		except Exception as e:
			self.log_status(f"Error handling step mode enabled: {e}", "error")

	def _handle_framework_step_continue_issued(self, data):
		"""Handle Framework step continue command."""
		try:
			message = data.get('message', 'Step continue processed')
			
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(
					text="Status: Step Continue", 
					foreground='blue'
				)
			
			self.log_status(f"[STEP] {message}")
			
		except Exception as e:
			self.log_status(f"Error handling step continue: {e}", "error")

	def _handle_framework_execution_finalized(self, data):
		"""Handle Framework execution finalization."""
		try:
			reason = data.get('reason', 'completed')
			
			if hasattr(self, 'current_status_label'):
				self.current_status_label.configure(
					text=f"Status: Finalized ({reason})", 
					foreground='green'
				)
			
			self.log_status(f"[FRAMEWORK] Execution finalized: {reason}")
			
		except Exception as e:
			self.log_status(f"Error handling execution finalized: {e}", "error")
			
	# ==================== EVENT HANDLERS ====================
		
	def on_canvas_click(self, event):
		"""Handle canvas click events - delegate to interaction handler."""
		# Always delegate to interaction handler - let it decide what to do
		if hasattr(self, 'interaction_handler') and self.interaction_handler:
			self.interaction_handler.on_canvas_click(event)

	def show_node_details(self, node_id):
		"""Show detailed information about a node - delegate to interaction handler."""
		if self.interaction_handler:
			self.interaction_handler.show_node_details(node_id)

	def on_mousewheel(self, event):
		"""Handle mouse wheel scrolling on canvas."""
		self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

	# ==================== CLEANUP & SHUTDOWN ====================
				
	def on_closing(self):
		"""Enhanced cleanup to prevent errors (matching ControlPanel exactly)."""
		try:
			print("Starting automation interface cleanup...")
			self._cleanup_in_progress = True

			# CRITICAL: Cancel all scheduled callbacks FIRST
			print("Cancelling scheduled callbacks...")
			for after_id in self._scheduled_after_ids:
				try:
					self.root.after_cancel(after_id)
				except:
					pass
			self._scheduled_after_ids.clear()

			# CRITICAL: Stop the MainThreadHandler first (matching ControlPanel)
			if hasattr(self, 'main_thread_handler') and self.main_thread_handler:
				print("Cleaning up MainThreadHandler...")
				self.main_thread_handler.cleanup()
				time.sleep(0.1)
				
			# Stop status updates first
			if hasattr(self, 'main_thread_handler'):
				print("Disabling status updates...")
				self.main_thread_handler.disable_callbacks()

			# Cancel any running operations
			if self.execution_state:
				self.execution_state.cancel("Interface closing")

			# Stop execution (matching ControlPanel)
			self.is_running = False
			
			# Wait for execution thread to finish with timeout
			if hasattr(self, 'execution_thread') and self.execution_thread:
				if self.execution_thread.is_alive():
					self.execution_thread.join(timeout=5.0)
					if self.execution_thread.is_alive():
						print("Warning: Execution thread did not stop gracefully")

			# Clean up Framework instance through manager (matching ControlPanel)
			if hasattr(self, 'framework_manager') and self.framework_manager:
				self.framework_manager.cleanup_current_instance("automation_interface_closing")
				self.framework_manager = None
			
			# Clean up shared Framework API
			if hasattr(self, 'shared_framework_api'):
				self.shared_framework_api = None
			
			self.Framework_utils = None

			# Clean up flow components
			self.builder = None
			self.executor = None
			self.root_node = None
			
			# Schedule final cleanup (matching ControlPanel)
			self.root.after_idle(self._final_destroy)
			
		except Exception as e:
			print(f"Automation interface cleanup error: {e}")
		finally:
			try:
				import gc
				gc.collect()
				time.sleep(0.1)
			except:
				pass

	def _clear_queue(self, q):
		"""Clear a queue safely."""
		try:
			while True:
				q.get_nowait()
		except queue.Empty:
			pass

	def _final_destroy(self):
		"""Final destruction in main thread."""
		try:
			self.root.quit()
			self.root.destroy()
		except Exception as e:
			print(f"Final destroy error: {e}")

	def run(self):
		"""Start the automation interface main loop."""
		self.root.mainloop()

# ====================STATUS HANDLER COMPATIBILITY ====================
	# Add these properties to FlowProgressInterface for compatibility
	@property
	def thread_active(self):
		"""Thread active property for compatibility."""
		return self.execution_state.get_state('execution_active', False)

	@thread_active.setter
	def thread_active(self, value):
		"""Thread active setter for compatibility."""
		self.execution_state.update_state(execution_active=value)

	@property
	def current_experiment_name(self):
		"""Current experiment name for compatibility."""
		return self.execution_state.get_state('current_experiment', None)

	@current_experiment_name.setter
	def current_experiment_name(self, value):
		"""Current experiment name setter."""
		self.execution_state.update_state(current_experiment=value)

	@property
	def total_experiments(self):
		"""Total experiments for compatibility."""
		return self.total_nodes

	@property
	def current_experiment_index(self):
		"""Current experiment index for compatibility."""
		return self.completed_count + self.failed_count

# ==================== STANDALONE FUNCTIONS ====================

def run(framework=None, utils=None, manager=None):
	start_automation_flow_ui(framework, utils, manager)

def start_automation_flow_ui(framework=None, utils=None, manager=None):
	"""
	Start the automation flow UI with proper Framework integration.
	
	Args:
		framework: Framework instance (optional)
		framework_manager: FrameworkInstanceManager instance
		main_thread_handler: MainThreadHandler instance  
		execution_state: ExecutionState instance
	"""
	interface = FlowProgressInterface(framework=framework, utils=utils, manager=manager)

	
	interface.run()

def start_automation_flow(structure_path, flows_path, ini_file_path, framework):
	"""
	Start the automation flow with enhanced Framework integration (command line version).
	"""
	try:
		print("Starting Automation Flow...")
		print(f"Structure: {structure_path}")
		print(f"Flows: {flows_path}")
		print(f"Config: {ini_file_path}")
		
		# Build the flow
		builder = FlowTestBuilder(structure_path, flows_path, ini_file_path, Framework=framework)
		executor = builder.build_flow(rootID='BASELINE')
		
		# Execute the flow
		print("Executing flow...")
		executor.execute()
		
		# Generate report
		report = executor.get_execution_report()
		print(f"\nFlow completed in {report['total_time']:.1f} seconds")
		print("Execution log:")
		for log_entry in report['execution_log']:
			print(f"  {log_entry}")
			
	except Exception as e:
		print(f"Error in automation flow: {e}")
		raise

# Main execution
if __name__ == '__main__':
	# Start the UI without pre-loading any files
	framework = None
	utils = None
	manager = None
	start_automation_flow_ui(framework, utils, manager)
