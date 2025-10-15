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

sys.path.append(parent_dir)


# Import all the builder classes
from Automation_Flow.AutomationBuilder import (
	FlowExecutionState,
	FlowConfiguration,
	NodeDrawer,
	ConnectionDrawer,
	LayoutManager,
	NodeDragHandler,
	CanvasInteractionHandler,
	FlowExecutionManager,
	FlowControlPanel,
	FileManagementPanel,
	StatusDisplayPanel
)

# Import all the flow/executor classes
from Automation_Flow.AutomationFlows import (
	FlowTestExecutor,
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
		self.framework_manager = None
		self.framework_api = None
		self.Framework_utils = None
		self.execution_state = execution_state  # Global

		# Initialize Framework with queue-based reporter if available
		if framework:
			print('Manager Set')
			self.framework_manager = manager(framework)
			self.Framework_utils = utils
		
		print(self.framework_manager)
		# Flow configuration
		self.builder = None
		self.executor = None
		self.root_node = None
		
		# File paths
		self.flow_folder = None
		self.structure_path = None
		self.flows_path = None
		self.ini_path = None
		
		# Default file names
		self.default_files = {
			'structure': 'FrameworkAutomationStructure.json',
			'flows': 'FrameworkAutomationFlows.json',
			'ini': 'FrameworkAutomationInit.ini'
		}
		
		# UI State
		self.current_node = None
		self.completed_nodes = set()
		self.failed_nodes = set()
		self.node_widgets = {}
		self.connection_lines = {}
		
		# Statistics tracking
		self.start_time = None
		self.total_nodes = 0
		self.completed_count = 0
		self.failed_count = 0
		
		# Threading and command handling (matching ControlPanel)
		self.main_thread_handler = None  # Will be set externally
		self.command_queue = queue.Queue()
		self.status_queue = queue.Queue()
		self.update_queue = queue.Queue()
		
		# Thread management
		self.execution_thread = None
		self.thread_active = False
		self.is_running = False
		self._cleanup_in_progress = False
		self._scheduled_after_ids = []  # Track scheduled callbacks
		
		# Cancellation and cleanup
		self.cancel_requested = threading.Event()
		self.exception_queue = queue.Queue()
		
		# Initialize modular components -- Framework API will be set later
		self.flow_execution_state = FlowExecutionState(execution_state)
		self.flow_config = FlowConfiguration(framework_api=None, framework_utils= self.Framework_utils)
		
		# UI components (will be initialized in setup)
		self.node_drawer = None
		self.connection_drawer = None
		self.layout_manager = None
		self.drag_handler = None
		self.interaction_handler = None

		# Execution manager initialization  -- Framework API will be set later
		#self.execution_manager = FlowExecutionManager(
		#	self.flow_config, self.flow_execution_state, self.framework_manager
		#)
		
		# Dragging state variables
		self.current_positions = {}
		
		# Create main window
		self.setup_main_window()
		self.create_widgets()

		# Initialize MainThreadHandler and ThreadIntegration
		self.main_thread_handler = fs.SecondThreadHandler(self.root, self)		

		# Start update loop (matching ControlPanel pattern)
		self.root.after(100, self.process_updates)
		
		# Cleanup handling
		self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
		
		# Start update loop (matching ControlPanel pattern)
		after_id = self.root.after(100, self.process_updates)
		self._scheduled_after_ids.append(after_id)

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
		self.start_button = ttk.Button(controls_frame, text="Start Flow", 
									 command=self.start_execution, state=tk.DISABLED)
		self.start_button.pack(side=tk.RIGHT, padx=2)
		
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
		
		# Progress bar (single progress for automation flow)
		progress_frame = ttk.Frame(self.left_frame)
		progress_frame.pack(fill=tk.X, padx=10, pady=5)
		
		ttk.Label(progress_frame, text="Flow Progress:").pack(side=tk.LEFT)
		
		self.progress_var = tk.DoubleVar()
		self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
										  maximum=100, length=300)
		self.progress_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
		
		self.progress_label = ttk.Label(progress_frame, text="0%")
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
			self.canvas, self.flow_config, self.flow_execution_state, self.drag_handler
		)
		
		# Initialize execution manager
		self.execution_manager = FlowExecutionManager(
			self.flow_config, self.flow_execution_state, self.framework_manager
		)

	def create_right_panel(self):
		"""Create the status and logging panel using shared component."""
		# Create the shared status panel (single progress bar for automation)
		if HAS_STATUS_PANEL:
			self.status_panel = StatusExecutionPanel(
				parent_frame=self.right_frame,
				dual_progress=False,  # Use single progress for automation flow
				show_experiment_stats=True,
				logger_callback=self._external_log_callback
			)
			
			# Store references for compatibility and command handling
			self.status_log = self.status_panel.status_log
			self.auto_scroll_var = self.status_panel.auto_scroll_var
			self.elapsed_time_label = self.status_panel.elapsed_time_label
		else:
			# Fallback to basic status panel
			self.status_panel = StatusDisplayPanel(self.right_frame, self.flow_execution_state)
			
		# Add automation-specific sections after the progress section
		self.create_automation_specific_sections()

	def create_automation_specific_sections(self):
		"""Add automation-specific UI sections."""
		# Current node info (insert after progress section)
		current_node_frame = ttk.LabelFrame(self.status_panel.main_container if HAS_STATUS_PANEL else self.right_frame, 
										  text="Current Node", padding=10)
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
			self.start_button.configure(state=tk.NORMAL)
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

	def _disable_ui_buttons_safe(self):
		"""Safely disable UI buttons during execution."""
		try:
			self.start_button.configure(state=tk.DISABLED)
			self.cancel_button.configure(state=tk.NORMAL)
			self.hold_button.configure(state=tk.NORMAL, text="Hold", style="Hold.TButton")
			self.end_button.configure(state=tk.NORMAL, text="End", style="End.TButton")
			self.browse_button.configure(state=tk.DISABLED)
			
			# Disable dragging controls during execution
			self.drag_checkbox.configure(state=tk.DISABLED)
			self.snap_checkbox.configure(state=tk.DISABLED)
			self.reset_positions_button.configure(state=tk.DISABLED)
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
				# Reset progress for new experiment/node
				self.progress_var.set(0)
				self.progress_label.configure(text="0%")
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
		"""Update progress display with various parameters."""
		try:
			# Handle experiment name updates
			if 'experiment_name' in kwargs and hasattr(self, 'current_experiment_label'):
				exp_name = kwargs['experiment_name']
				if exp_name:
					self.current_experiment_label.configure(text=f"Experiment: {exp_name}")
			
			# Handle status updates
			if 'status' in kwargs and hasattr(self, 'current_status_label'):
				status = kwargs['status']
				self.current_status_label.configure(text=f"Status: {status}")
			
			# Handle result status (for coloring)
			if 'result_status' in kwargs:
				result = kwargs['result_status']
				if hasattr(self, 'current_status_label'):
					color = 'green' if result == 'PASS' else 'red' if result == 'FAIL' else 'black'
					self.current_status_label.configure(foreground=color)
					
		except Exception as e:
			self.log_status(f"Progress display update error: {e}", "error")

	def reset_progress_tracking(self):
		"""Reset progress tracking for new execution."""
		try:
			self.progress_var.set(0)
			self.progress_label.configure(text="0%")
			
			# Reset counters
			self.completed_count = 0
			self.failed_count = 0
			self.completed_nodes.clear()
			self.failed_nodes.clear()
			
			# Update statistics display
			if hasattr(self, 'completed_nodes_label'):
				self.completed_nodes_label.configure(text="✓ Completed: 0")
			if hasattr(self, 'failed_nodes_label'):
				self.failed_nodes_label.configure(text="✗ Failed: 0")
				
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
		if not self.builder:
			return
		
		# Clear everything
		self.canvas.delete("all")
		self.node_widgets.clear()
		self.connection_lines.clear()
		
		# Clear connection drawer tracking
		if self.connection_drawer:
			self.connection_drawer.clear_all_connections()
		
		# Force canvas update
		self.canvas.update_idletasks()
		
		# Redraw everything
		nodes = list(self.builder.builtNodes.values())
		
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
			# Load using flow config
			success, error = self.flow_config.load_configuration(
				self.structure_path, self.flows_path, self.ini_path,
				framework=self.framework, logger=self.log_status
			)
			
			if not success:
				raise ValueError(error)
			
			# Update references for compatibility
			self.builder = self.flow_config.builder
			self.executor = self.flow_config.executor
			self.root_node = self.flow_config.root_node
			
			# Update total nodes count
			self.total_nodes = len(self.builder.builtNodes)
			self.flow_execution_state.total_nodes = self.total_nodes
			
			# Log flow summary
			self.log_flow_summary()
			
			# Draw the flow diagram
			self.draw_flow_diagram()
			
			# Enable start button
			self.start_button.configure(state=tk.NORMAL)
			
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
			self.start_button.configure(state=tk.DISABLED)
			self.show_canvas_message("Error loading configuration. Please check files and try again.")

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
		if self.current_node and node_id == self.current_node.ID:
			# Check if experiment is actually running
			if self.is_experiment_running(node):
				return 'running'  # Red - experiment is running
			else:
				return 'current'  # Blue - node selected but not running yet
		
		# Check completion status
		if node_id in self.completed_nodes:
			return 'completed'  # Green - done successfully
		
		if node_id in self.failed_nodes:
			# Check if it's execution failure vs other failure
			if self.is_execution_failure(node):
				return 'execution_fail'  # Yellow - execution failed
			else:
				return 'failed'  # Red - other failure
		
		# Default state
		return 'idle'  # Gray - waiting

	def is_experiment_running(self, node):
		"""Check if the experiment is currently running for this node."""
		if self.framework_api:
			return self.framework_api.is_experiment_running()
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
	
	# **MODIFY** start_execution to use proper thread safety:
	def start_execution(self):
		"""Start the flow execution with proper thread isolation and command system."""
		if self.thread_active or self.is_running:
			self.log_status("Flow execution already running", "warning")
			return

		if not self.builder or not self.root_node:
			self.log_status("No flow loaded - please load a flow configuration first", "error")
			return

		# **ADD** Framework cleanup before starting (matching ControlPanel)
		#self._cleanup_previous_framework()

		# Clean up any previous state
		self._cleanup_previous_execution()

		# Clean up previous run statuses
		# self._cleanup_node_statuses()

		# **ADD** Clear execution state commands (matching ControlPanel)
		if self.execution_state:
			self.execution_state.clear_all_commands()


		print('=== FRAMEWORK API FLOW DEBUG ===')
		print(f'Framework Manager: {self.framework_manager}')
		print(f'Execution Manager: {self.execution_manager}')
		print(f'Builder: {self.builder}')
		print(f'Root Node: {self.root_node}')
		print(f'Status Handler: {self.main_thread_handler}')

		print('Execution Started 1')
		# Use execution manager to start

		# Set the Main Thread Handler
		self.execution_manager.set_main_thread_handler = self.main_thread_handler

		# Start execution (this will create shared Framework API)
		success, message = self.execution_manager.start_execution(self.executor)
		
		if success:
			# Get the shared Framework API from execution manager
			self.framework_api = self.execution_manager.shared_framework_api
			
			if self.framework_api:
				self.log_status("UI now has access to shared Framework API", "success")
			else:
				self.log_status("Warning: No Framework API available from execution manager", "warning")

			# Update UI state
			self.is_running = True
			self.thread_active = True
			self.start_time = time.time()
			self._update_ui_for_start()
			
			self.log_status("Started automation flow execution with shared Framework API", "success")
		else:
			self.log_status(f"Failed to start execution: {message}", "error")

	def cancel_execution(self):
		"""Cancel execution using shared API directly."""
		success, message = self.execution_manager.cancel_execution()
		
		if success:
			self.status_label.configure(text=" Cancelling... ", bg="orange", fg="black")
			self.cancel_button.configure(state=tk.DISABLED)
		
		self.log_status(message)
		
	# **ADD** Command system methods (matching ControlPanel):
	def toggle_framework_hold(self):
		"""Toggle framework halt/continue using shared API directly."""
		# Get Framework API directly from execution manager
		framework_api = (self.framework_api or 
						getattr(self.execution_manager, 'shared_framework_api', None))
		
		if not framework_api:
			self.log_status("No Framework API available - execution may not be running", "warning")
			return

		try:
			state = framework_api.get_current_state()

			if not state.get('is_running'):
				self.log_status("No active execution to control", "warning")
				return

			if state.get('is_halted', False):
				# Continue execution
				result = framework_api.continue_execution()
				if result['success']:
					self.hold_button.configure(text="Hold", style="Hold.TButton")
					self.log_status(result['message'])
					self.status_label.configure(text=" Resuming... ", bg="#BF0000", fg="white")
			else:
				# Halt execution
				result = framework_api.halt_execution()
				if result['success']:
					self.hold_button.configure(text="Continue", style="Continue.TButton")
					self.log_status(result['message'])
					self.status_label.configure(text=" Halting... ", bg="orange", fg="black")
					
		except Exception as e:
			self.log_status(f"Framework control error: {e}", "error")

	def end_current_experiment(self):
		"""End current experiment using shared API directly."""
		# Get Framework API directly from execution manager
		framework_api = (self.framework_api or 
						getattr(self.execution_manager, 'shared_framework_api', None))
		
		if not framework_api:
			self.log_status("No Framework API available", "warning")
			return
		
		try:
			result = framework_api.end_experiment()
			if result['success']:
				self.log_status(result['message'])
				self.end_button.configure(text="Ending...", state=tk.DISABLED)
				self.status_label.configure(text=" Ending... ", bg="red", fg="white")
			else:
				self.log_status(result['message'], "error")
		except Exception as e:
			self.log_status(f"End experiment error: {e}", "error")
			
	def _update_ui_for_start(self):
		"""Update UI elements for execution start (matching ControlPanel)."""
		try:
			self.status_label.configure(text=" Running ", bg="#BF0000", fg="white")
			self.log_status("Starting flow execution", "success")
			
			# Reset node statuses
			for node_id in self.node_widgets.keys():
				self._update_node_status_safe(node_id, "Idle", self.node_colors['idle'], 'black')
			
			# Update button states
			self.start_button.configure(state=tk.DISABLED)
			self.cancel_button.configure(state=tk.NORMAL)
			self.end_button.configure(state=tk.NORMAL, text="End", style="End.TButton")
			self.hold_button.configure(state=tk.NORMAL, text="Hold", style="Hold.TButton")
			self.browse_button.configure(state=tk.DISABLED)
			
			# Disable dragging controls during execution
			self.drag_checkbox.configure(state=tk.DISABLED)
			self.snap_checkbox.configure(state=tk.DISABLED)
			self.reset_positions_button.configure(state=tk.DISABLED)
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

			self.start_button.configure(state=tk.NORMAL)
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
	
	def process_updates(self):
		"""Process updates from the execution thread (matching ControlPanel pattern)."""
		# Check if cleanup is in progress
		if self._cleanup_in_progress:
			return

		try:
			# Process main update queue
			while True:
				update_type, data = self.update_queue.get_nowait()
				self.handle_update(update_type, data)
		except queue.Empty:
			pass
		
		# Process execution manager updates
		try:
			while True:
				update_type, data = self.execution_manager.update_queue.get_nowait()
				self.handle_update(update_type, data)
		except queue.Empty:
			pass
		
		# Process MainThreadHandler updates (matching ControlPanel)
		if hasattr(self, 'main_thread_handler') and self.main_thread_handler:
			try:
				while True:
					update = self.main_thread_handler.get_next_update()
					if update:
						self.handle_main_thread_update(update)
					else:
						break
			except:
				pass
		
		# Schedule next update
		if (self.is_running or 
			not self.update_queue.empty() or 
			not self.execution_manager.update_queue.empty()):
			self.root.after(100, self.process_updates)
		else:
			# Continue processing at slower rate when not running
			self.root.after(500, self.process_updates)

	# New method to handle MainThreadHandler updates:
	def handle_main_thread_update(self, update):
		"""Handle updates from MainThreadHandler (matching ControlPanel)."""
		update_type = update.get('type')
		data = update.get('data', {})
		
		if update_type == 'flow_execution_setup':
			self.log_status(f"Flow setup: {data.get('total_nodes', 0)} nodes")
		elif update_type == 'flow_execution_complete':
			self.execution_completed()
		elif update_type == 'flow_execution_ended_complete':
			self.execution_ended()  # Now properly handled
		elif update_type == 'flow_execution_cancelled':
			self.execution_cancelled()
		elif update_type == 'flow_execution_error':
			error_msg = data.get('error', 'Unknown error')
			self.execution_error(error_msg)
		elif update_type == 'current_node':
			self.update_current_node(data)
		elif update_type == 'node_running':
			node_data = data if isinstance(data, dict) else {'node_id': getattr(data, 'ID', 'Unknown')}
			self.update_node_running(node_data)
		elif update_type == 'node_completed':
			node_data = data if isinstance(data, dict) else {'node_id': getattr(data, 'ID', 'Unknown')}
			self.update_node_completed(node_data)
		elif update_type == 'node_failed':
			node_data = data if isinstance(data, dict) else {'node_id': getattr(data, 'ID', 'Unknown')}
			self.update_node_failed(node_data)
		elif update_type == 'node_execution_fail':
			node_data = data if isinstance(data, dict) else {'node_id': getattr(data, 'ID', 'Unknown')}
			self.update_node_execution_fail(node_data)
		elif update_type == 'node_error':
			node_data = data if isinstance(data, dict) else {'node_id': getattr(data, 'ID', 'Unknown')}
			self.update_node_error(node_data)
		elif update_type == 'status_update':
			# Handle Framework status updates
			message = data.get('message', '')
			if message:
				self.log_status(message)
		else:
			# Log unknown update types for debugging
			self.log_status(f"Unknown update type: {update_type}", "debug")

	def handle_update(self, update_type, data):
		"""Handle different types of updates - delegate to MainThreadHandler."""
		# All updates now go through MainThreadHandler for consistency
		if self.main_thread_handler:
			self.main_thread_handler.queue_status_update({
				'type': update_type,
				'data': data
			})
		else:
			# Fallback for direct handling (legacy) - should rarely be used
			print(f"Warning: Direct update handling for {update_type}")
			self._handle_update_direct(update_type, data)

	def _handle_update_direct(self, update_type, data):
		"""Handle different types of updates."""
		if update_type == 'current_node':
			self.update_current_node(data)
		elif update_type == 'node_running':
			self.update_node_running(data)
		elif update_type == 'node_completed':
			self.update_node_completed(data)
		elif update_type == 'node_failed':
			self.update_node_failed(data)
		elif update_type == 'node_execution_fail':
			self.update_node_execution_fail(data)
		elif update_type == 'execution_complete':
			self.execution_completed()
		elif update_type == 'execution_cancelled':
			self.execution_cancelled()
		elif update_type == 'execution_error':
			self.execution_error(data)

	def update_current_node(self, node_data):
		"""Update the current executing node with enhanced status tracking."""
		# Handle both node object and dict data
		if isinstance(node_data, dict):
			node_id = node_data.get('node_id')
			node_name = node_data.get('node_name', 'Unknown')
			# Find actual node object
			node = None
			if self.builder and node_id:
				node = self.builder.builtNodes.get(node_id)
		else:
			# Legacy node object
			node = node_data
			node_id = node.ID
			node_name = node.Name
		
		if not node:
			return
		
		self.current_node = node
		self.flow_execution_state.current_node = node
		
		# Update UI labels
		self.current_node_label.configure(text=f"Node: {node.Name} ({node.ID})")
		
		exp_name = "None"
		if hasattr(node, 'Experiment') and node.Experiment:
			exp_name = node.Experiment.get('Test Name', 'Unknown')
		self.current_experiment_label.configure(text=f"Experiment: {exp_name}")
		
		# Determine detailed status
		if self.is_experiment_running(node):
			status_text = "Status: Running Experiment"
			self.current_status_label.configure(text=status_text, foreground='red')
		else:
			status_text = "Status: Preparing"
			self.current_status_label.configure(text=status_text, foreground='blue')
		
		# Update node visual status
		self.node_drawer.redraw_node(node, 'current')
		
		# Update progress
		self.update_progress()
		
		self.log_status(f"Executing node: {node.Name} ({node.ID})")

	def update_node_running(self, node):
		"""Update node as running."""
		self.current_status_label.configure(text="Status: Running Experiment", foreground='red')
		self.node_drawer.redraw_node(node, 'running')

	def update_node_completed(self, node_data):
		"""Update node as completed (Green)."""
		if isinstance(node_data, dict):
			node_id = node_data.get('node_id', 'Unknown')
		else:
			node_id = getattr(node_data, 'ID', 'Unknown')
		
		self.completed_nodes.add(node_id)
		self.completed_count += 1
		
		# Update FlowExecutionState with experiment completion
		self.flow_execution_state.update_node_status(node_id, 'completed')
		
		# Update statistics display
		self.completed_nodes_label.configure(text=f"✓ Completed: {self.completed_count}")
		
		# Update node visual status
		if isinstance(node_data, dict):
			if self.builder:
				node = self.builder.builtNodes.get(node_id)
				if node:
					self.node_drawer.redraw_node(node, 'completed')
		else:
			self.node_drawer.redraw_node(node_data, 'completed')
		
		# Update progress
		self.update_progress()
		
		self.log_status(f"Experiment completed: {node_id}", "success")

	def update_node_failed(self, node):
		"""Update node as failed with proper color coding."""
		self.failed_nodes.add(node.ID)
		self.failed_count += 1
		self.flow_execution_state.update_node_status(node.ID, 'failed')
		
		# Update statistics
		self.failed_nodes_label.configure(text=f"✗ Failed: {self.failed_count}")
		
		# Update node visual status
		self.node_drawer.redraw_node(node, 'failed')
		
		# Update progress
		self.update_progress()
		
		self.log_status(f"Node test failed: {node.Name}", "error")

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
		self.flow_execution_state.update_node_status(node_id, 'failed')
		
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

	def update_node_execution_fail(self, node):
		"""Update node as execution failed (Yellow)."""
		self.failed_nodes.add(node.ID)
		self.failed_count += 1
		self.flow_execution_state.update_node_status(node.ID, 'failed')
		
		# Update statistics
		self.failed_nodes_label.configure(text=f"✗ Failed: {self.failed_count}")
		
		# Update node visual status
		self.node_drawer.redraw_node(node, 'execution_fail')
		
		# Update progress
		self.update_progress()
		
		self.log_status(f"Node execution failed: {node.Name}", "warning")

	def update_progress(self):
		"""Update overall progress based on EXPERIMENTS (nodes), not iterations."""
		if self.flow_execution_state.total_experiments > 0:
			# Progress based on completed experiments (nodes)
			progress = (self.flow_execution_state.current_experiment_index / self.flow_execution_state.total_experiments) * 100
			self.progress_var.set(progress)
			self.progress_label.configure(text=f"{int(progress)}%")
			
			# Update shared status panel if available
			if HAS_STATUS_PANEL and hasattr(self.status_panel, 'update_overall_progress'):
				self.status_panel.update_overall_progress(
					self.flow_execution_state.current_experiment_index - 1,  # Current experiment index
					self.flow_execution_state.total_experiments,
					1.0  # Current experiment progress (completed)
				)
		
		# Update timing
		if self.start_time:
			elapsed = time.time() - self.start_time
			if hasattr(self.status_panel, 'elapsed_time_label'):
				self.status_panel.elapsed_time_label.configure(text=f"Time: {self._format_time(elapsed)}")

	def execution_completed(self):
		"""Handle normal execution completion."""
		self.is_running = False
		self.flow_execution_state.is_running = False
		
		# Update UI
		self._enable_ui_buttons_safe()
		self.current_status_label.configure(text="Status: Completed")
		
		total_time = time.time() - self.start_time if self.start_time else 0
		self.log_status(f"Flow execution completed in {self._format_time(total_time)}", "success")
		self.log_status(f"Results: {self.completed_count} completed, {self.failed_count} failed")
		
		self.status_label.configure(text=" Completed ", bg="#006400", fg="white")

	def execution_ended(self):
		"""Handle execution ended by END command."""
		self.is_running = False
		self.flow_execution_state.is_running = False
		
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
		self.flow_execution_state.is_running = False
		
		self.current_status_label.configure(text="Status: Cancelled")
		self.log_status("Flow execution cancelled", "warning")
		
		self.status_label.configure(text=" Cancelled ", bg="gray", fg="white")
		self._enable_ui_buttons_safe()

	def execution_error(self, error_msg):
		"""Handle execution error."""
		self.is_running = False
		self.flow_execution_state.is_running = False
		
		# Update UI
		self._enable_ui_buttons_safe()
		self.current_status_label.configure(text="Status: Error")
		self.log_status(f"Execution error: {error_msg}", "error")
		
		self.status_label.configure(text=" Error ", bg="red", fg="white")

	def _enable_ui_buttons_safe(self):
		"""Safely enable UI buttons with error handling (matching ControlPanel)."""
		try:
			self.start_button.configure(state=tk.NORMAL)
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

	# ==================== EVENT HANDLERS ====================
	
	def on_canvas_click(self, event):
		"""Handle canvas click events."""
		# Check if we're dragging first - use the drag_handler's state
		if (self.drag_handler and 
			hasattr(self.drag_handler, 'dragging_node') and 
			self.drag_handler.dragging_node):
			return  # Don't process clicks during dragging
		
		# Delegate to interaction handler, which will handle drag vs click logic
		if self.interaction_handler:
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
			if hasattr(self, 'cancel_requested'):
				self.cancel_requested.set()

			# Stop execution (matching ControlPanel)
			self.thread_active = False
			self.is_running = False
			
			# Wait for thread to finish with timeout (matching ControlPanel)
			if hasattr(self.execution_manager, 'execution_thread') and self.execution_manager.execution_thread:
				if self.execution_manager.execution_thread.is_alive():
					self.execution_manager.execution_thread.join(timeout=5.0)
					if self.execution_manager.execution_thread.is_alive():
						print("Warning: Execution thread did not stop gracefully")

			# Clear all queues (matching ControlPanel)
			self._clear_queue(self.command_queue)
			self._clear_queue(self.status_queue)
			self._clear_queue(self.update_queue)
			if hasattr(self.execution_manager, 'update_queue'):
				self._clear_queue(self.execution_manager.update_queue)
			
			# Clean up Framework instance through manager (matching ControlPanel)
			if hasattr(self, 'framework_manager') and self.framework_manager:
				self.framework_manager.cleanup_current_instance("automation_interface_closing")
				self.framework_manager = None
			
			self.framework_api = None
			self.Framework_utils = None

			# Clean up flow components
			self.builder = None
			self.executor = None
			self.root_node = None
			
			# Clean up execution manager
			if hasattr(self, 'execution_manager'):
				self.execution_manager.executor = None
				self.execution_manager.framework_api = None
			
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
		return self.is_running

	@thread_active.setter
	def thread_active(self, value):
		"""Thread active setter for compatibility."""
		self.is_running = value

	@property
	def current_experiment_name(self):
		"""Current experiment name for compatibility."""
		return getattr(self, '_current_experiment_name', None)

	@current_experiment_name.setter
	def current_experiment_name(self, value):
		"""Current experiment name setter."""
		self._current_experiment_name = value

	@property
	def total_experiments(self):
		"""Total experiments for compatibility."""
		return self.total_nodes

	@total_experiments.setter
	def total_experiments(self, value):
		"""Total experiments setter."""
		self.total_nodes = value

	@property
	def current_experiment_index(self):
		"""Current experiment index for compatibility."""
		return self.completed_count + self.failed_count

	@current_experiment_index.setter
	def current_experiment_index(self, value):
		"""Current experiment index setter."""
		pass  # Calculated property, ignore setter

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
