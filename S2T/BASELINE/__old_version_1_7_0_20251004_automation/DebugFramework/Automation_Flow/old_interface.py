
# ==================== OLD INTERFACE FUNCTIONS ====================

class FlowProgressInterface_old:
	"""
	Enhanced Automation Flow Interface with proper command handling and cleanup.
	Matches ControlPanel's robustness for Framework API interaction.
	"""
	
	def __init__(self, framework=None):
		self.framework = framework
		
		# Framework integration (matching ControlPanel pattern)
		self.framework_manager = None
		self.framework_api = None
		self.Framework_utils = None
		self.execution_state = None  # Will be set by external execution state
		
		# Initialize Framework with queue-based reporter if available
		if framework:
			# This should be set by the caller, similar to ControlPanel
			pass
		
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
		
		# Cancellation and cleanup
		self.cancel_requested = threading.Event()
		self.exception_queue = queue.Queue()
		
		# Create main window
		self.setup_main_window()
		self.create_widgets()
		
		# Start update loop (matching ControlPanel pattern)
		self.root.after(100, self.process_updates)
		
		# Cleanup handling
		self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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
		
		# Bind mouse events for canvas interaction
		self.canvas.bind("<Button-1>", self.on_canvas_click)
		self.canvas.bind("<MouseWheel>", self.on_mousewheel)
		
		# Initial message on canvas
		self.show_canvas_message("Please select a flow folder to begin")

	def create_right_panel(self):
		"""Create the status and logging panel using shared component."""
		# Create the shared status panel (single progress bar for automation)
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
				
		# Add automation-specific sections after the progress section
		self.create_automation_specific_sections()

	def create_automation_specific_sections(self):
		"""Add automation-specific UI sections."""
		# Current node info (insert after progress section)
		current_node_frame = ttk.LabelFrame(self.status_panel.main_container, text="Current Node", padding=10)
		# Insert after the progress section (index 1)
		current_node_frame.pack(fill=tk.X, pady=(0, 10))
		
		# Move it to the correct position
		children = list(self.status_panel.main_container.winfo_children())
		if len(children) >= 2:
			current_node_frame.pack_forget()
			current_node_frame.pack(fill=tk.X, pady=(0, 10), after=children[1])
		
		self.current_node_label = ttk.Label(current_node_frame, text="Node: Ready to start")
		self.current_node_label.pack(anchor="w")
		
		self.current_experiment_label = ttk.Label(current_node_frame, text="Experiment: None")
		self.current_experiment_label.pack(anchor="w")
		
		self.current_status_label = ttk.Label(current_node_frame, text="Status: Idle")
		self.current_status_label.pack(anchor="w")
		
		# Flow statistics (insert after statistics section)
		flow_stats_frame = ttk.LabelFrame(self.status_panel.main_container, text="Flow Statistics", padding=10)
		# Insert after current node frame
		flow_stats_frame.pack(fill=tk.X, pady=(0, 10))
		
		# Move it to correct position
		children = list(self.status_panel.main_container.winfo_children())
		if len(children) >= 4:
			flow_stats_frame.pack_forget()
			flow_stats_frame.pack(fill=tk.X, pady=(0, 10), after=children[3])
		
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

	def log_message(self, message: str, level: str = "info"):
		"""Delegate to shared status panel."""
		self.status_panel.log_status(message, level)

	# ==================== FRAMEWORK INTEGRATION & COMMAND HANDLING ====================
	
	def set_framework_integration(self, framework_manager, main_thread_handler, execution_state):
		"""Set Framework integration components (called externally like ControlPanel)."""
		self.framework_manager = framework_manager
		self.main_thread_handler = main_thread_handler
		self.execution_state = execution_state
		
		# Create Framework API if manager is available
		if self.framework_manager:
			self.framework_api = self.framework_manager.create_framework_instance(
				status_reporter=self.main_thread_handler,
				execution_state=self.execution_state
			)

	def start_execution(self):
		"""Start the flow execution with proper thread isolation and command system."""
		if self.thread_active or self.is_running:
			self.log_message("Flow execution already running", "warning")
			return
		
		if not self.builder or not self.root_node:
			self.log_message("No flow loaded - please load a flow configuration first", "error")
			return
		
		# Clean up previous run statuses
		self._cleanup_node_statuses()
		
		# Reset progress tracking
		self.status_panel.reset_progress_tracking()
		
		# Clear execution state commands
		if self.execution_state:
			self.execution_state.clear_all_commands()
		
		# Create fresh Framework instance for this execution
		if self.framework_manager:
			self.framework_api = self.framework_manager.create_framework_instance(
				status_reporter=self.main_thread_handler,
				execution_state=self.execution_state
			)
		
		# Set up execution state
		self.is_running = True
		self.thread_active = True
		self.start_time = time.time()
		
		# Reset counters
		self.completed_count = 0
		self.failed_count = 0
		self.completed_nodes.clear()
		self.failed_nodes.clear()
		
		# Update UI for start
		self._update_ui_for_start()
		
		# Start execution thread
		self.execution_thread = threading.Thread(
			target=self._execute_flow_thread,
			daemon=True,
			name="AutomationFlowExecution"
		)
		self.execution_thread.start()
		
		self.log_message("Started automation flow execution...", "success")

	def _execute_flow_thread(self):
		"""Execute the flow in a separate thread with proper error handling."""
		try:
			# Set API reference for all nodes
			if self.framework_api:
				self._set_api_for_all_nodes(self.root_node)
			
			# Initialize execution state
			if self.execution_state:
				self.execution_state.update_state(
					execution_active=True,
					current_experiment=None,
					current_iteration=0,
					total_iterations=0
				)
			
			# Execute the flow
			current_node = self.root_node
			node_count = 0
			
			while current_node is not None and node_count < 50 and self.is_running:
				node_count += 1
				
				# Check for cancellation BEFORE starting each node
				if self.execution_state and self.execution_state.is_cancelled():
					self.log_message(f"[CANCEL] Execution cancelled before node {node_count}")
					self._send_cancellation_status(current_node, node_count)
					break
				
				# Check for END command BEFORE starting each node
				if self.execution_state and self.execution_state.is_ended():
					self.log_message(f"[END] Execution ended before node {node_count}")
					self._send_end_status(current_node, node_count)
					break
				
				# Update current node
				#self.update_queue.put(('current_node', current_node))

				if self.main_thread_handler:
					self.main_thread_handler.queue_status_update({
						'type': 'current_node',
						'data': {
						'node_id': current_node.ID,
						'node_name': current_node.Name,
						'experiment': getattr(current_node, 'Experiment', {})
						}
					})                
				# Execute node
				start_time = time.time()
				try:
					current_node.run_experiment()
					execution_time = time.time() - start_time
					
					# Check for cancellation after node execution
					if self.execution_state and self.execution_state.is_cancelled():
						self.log_message(f"[CANCEL] Execution cancelled after node execution")
						self.update_queue.put(('node_cancelled', current_node))
						break
					
					# Check for END command after node execution
					if self.execution_state and self.execution_state.is_ended():
						self.log_message(f"[END] Execution ended after node execution")
						self.update_queue.put(('node_ended', current_node))
						break
					
					# Update node status based on results
					if 'FAIL' in current_node.runStatusHistory:
						self.update_queue.put(('node_failed', current_node))
					else:
						self.update_queue.put(('node_completed', current_node))
					
				except InterruptedError:
					self.log_message(f"[CANCEL] Node execution was cancelled")
					self.update_queue.put(('node_cancelled', current_node))
					break
				except Exception as e:
					self.log_message(f"[ERROR] Node execution failed: {str(e)}", "error")
					self.update_queue.put(('node_failed', current_node))
					
					# Check for commands after exception
					if self.execution_state and self.execution_state.is_cancelled():
						break
					if self.execution_state and self.execution_state.is_ended():
						break
				
				# Get next node
				next_node = current_node.get_next_node()
				current_node = next_node
				
				# Break if no more nodes or execution stopped
				if not self.is_running:
					break
			
			# Execution completed normally
			if node_count >= 50:
				self.update_queue.put(('flow_execution_error', "Flow execution stopped due to safety limit (50 nodes)"))
			else:
				self.update_queue.put(('flow_execution_complete', None))
			
		except Exception as e:
			self.log_message(f"[ERROR] Flow execution error: {e}", "error")
			self.update_queue.put(('execution_error', str(e)))
		finally:
			# Proper cleanup
			try:
				self.thread_active = False
				
				# Finalize framework execution
				if self.framework_manager:
					self.framework_manager.cleanup_current_instance("flow_execution_complete")
				
				# Queue completion
				if self.execution_state and self.execution_state.is_cancelled():
					self.update_queue.put(('execution_cancelled_complete', None))
				elif self.execution_state and self.execution_state.is_ended():
					self.update_queue.put(('execution_ended_complete', None))
				else:
					self.update_queue.put(('flow_execution_complete', None))
					
			except Exception as cleanup_error:
				self.log_message(f"[ERROR] Thread cleanup error: {cleanup_error}", "error")

	def _set_api_for_all_nodes(self, node, visited=None):
		"""Recursively set Framework API reference for all nodes in the flow."""
		if visited is None:
			visited = set()
		
		if node.ID in visited:
			return
		
		visited.add(node.ID)
		node.framework_api = self.framework_api
		
		# Recursively set for connected nodes
		for next_node in node.outputNodeMap.values():
			self._set_api_for_all_nodes(next_node, visited)

	def toggle_framework_hold(self):
		"""Toggle framework halt/continue functionality (matching ControlPanel)."""
		if not self.framework_api:
			self.log_message("No Framework API available", "warning")
			return

		state = self.framework_api.get_current_state()

		if not state.get('is_running'):
			self.log_message("No active execution to control", "warning")
			return

		# Check if currently paused
		if state.get('is_halted', False):
			# Continue execution
			result = self.framework_api.continue_execution()
			if result['success']:
				self.hold_button.configure(text="Hold", style="Hold.TButton")
				self.log_message(result['message'], "success")
				self.status_label.configure(text=" Resuming... ", bg="#BF0000", fg="white")
		else:
			# Halt execution
			result = self.framework_api.halt_execution()
			if result['success']:
				self.hold_button.configure(text="Continue", style="Continue.TButton")
				self.log_message(result['message'], "success")
				self.status_label.configure(text=" Halting... ", bg="orange", fg="black")

	def end_current_experiment(self):
		"""End current experiment through API (matching ControlPanel)."""
		if not self.framework_api:
			self.log_message("No Framework API available", "warning")
			return
		
		result = self.framework_api.end_experiment()
		if result['success']:
			self.log_message(result['message'], "success")
			self.end_button.configure(text="Ending...", state=tk.DISABLED, style="EndActive.TButton")
		else:
			self.log_message(result['message'], "warning")

	def cancel_execution(self):
		"""Cancel execution through API (matching ControlPanel)."""
		if not self.framework_api:
			self.log_message("No Framework API available", "warning")
			return
		
		result = self.framework_api.cancel_experiment()
		self.log_message(result['message'], "success")
		
		# Update UI immediately
		self.thread_active = False
		self.is_running = False
		self.cancel_button.configure(state=tk.DISABLED)
		self.end_button.configure(state=tk.DISABLED)
		
		# Schedule cleanup
		self.root.after(2000, self._cleanup_after_cancel)

	def _cleanup_after_cancel(self):
		"""Cleanup after cancellation (matching ControlPanel pattern)."""
		try:
			# Check if cancellation was processed or force cleanup after timeout
			if (not self.execution_state or not self.execution_state.has_command('CANCEL') or 
				not self.thread_active):
				self.log_message("Cancellation completed successfully", "success")
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
					self.log_message("Force cleanup after cancel timeout", "warning")
					self._reset_buttons_after_cancel()
					self._cancel_retry_count = 0
				
		except Exception as e:
			self.log_message(f"Error in cancel cleanup: {e}", "error")

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
			
			# Final status update
			self.root.after(2000, lambda: self.status_label.configure(text=" Ready ", bg="white", fg="black"))
			
			# Reset cancel retry
			if hasattr(self, '_cancel_retry_count'):
				self._cancel_retry_count = 0
				
		except Exception as e:
			self.log_message(f"Error resetting buttons: {e}", "error")

	def _update_ui_for_start(self):
		"""Update UI elements for execution start (matching ControlPanel)."""
		try:
			self.status_label.configure(text=" Running ", bg="#BF0000", fg="white")
			self.log_message("Starting flow execution", "success")
			
			# Reset node statuses
			for node_id in self.node_widgets.keys():
				self._update_node_status_safe(node_id, "Idle", self.node_colors['idle'], 'black')
			
			# Update button states
			self.start_button.configure(state=tk.DISABLED)
			self.cancel_button.configure(state=tk.NORMAL)
			self.end_button.configure(state=tk.NORMAL, text="End", style="End.TButton")
			self.hold_button.configure(state=tk.NORMAL, text="Hold", style="Hold.TButton")
			self.browse_button.configure(state=tk.DISABLED)
			
		except Exception as e:
			self.log_message(f"Error updating UI for start: {e}", "error")

	def _send_cancellation_status(self, node, node_count):
		"""Helper method to send cancellation status."""
		self.update_queue.put(('flow_execution_cancelled', {
			'node_name': node.Name if node else 'Unknown',
			'completed_nodes': node_count,
			'total_nodes': self.total_nodes,
			'reason': 'User cancellation'
		}))

	def _send_end_status(self, node, node_count):
		"""Helper method to send end command status."""
		self.update_queue.put(('flow_execution_ended', {
			'node_name': node.Name if node else 'Unknown',
			'completed_nodes': node_count,
			'total_nodes': self.total_nodes,
			'reason': 'END command - execution stopped gracefully'
		}))

	def _cleanup_node_statuses(self):
		"""Clean up node statuses when starting new execution."""
		try:
			for node_id in self.node_widgets.keys():
				self._update_node_status_safe(node_id, "Idle", self.node_colors['idle'], 'black')
		except Exception as e:
			self.log_message(f"[ERROR] Node status cleanup failed: {e}", "error")

	# ==================== UPDATE PROCESSING & UI COORDINATION ====================
	
	def process_updates(self):
		"""Process updates from the execution thread (matching ControlPanel pattern)."""
		try:
			while True:
				update_type, data = self.update_queue.get_nowait()
				
				if update_type == 'current_node':
					self.update_current_node(data)
				elif update_type == 'node_completed':
					self.update_node_completed(data)
				elif update_type == 'node_failed':
					self.update_node_failed(data)
				elif update_type == 'node_cancelled':
					self.update_node_cancelled(data)
				elif update_type == 'node_ended':
					self.update_node_ended(data)
				elif update_type == 'execution_complete':
					self.execution_completed()
				elif update_type == 'execution_cancelled':
					self.execution_cancelled(data)
				elif update_type == 'execution_ended':
					self.execution_ended(data)
				elif update_type == 'execution_error':
					self.execution_error(data)
				elif update_type == 'flow_execution_complete':
					self.flow_execution_complete()
				elif update_type == 'execution_cancelled_complete':
					self.execution_cancelled_complete()
				elif update_type == 'execution_ended_complete':
					self.execution_ended_complete()
					
		except queue.Empty:
			pass
		
		# Schedule next update
		if self.is_running or not self.update_queue.empty():
			self.root.after(100, self.process_updates)
		else:
			# Continue processing at slower rate when not running
			self.root.after(500, self.process_updates)
	
	def update_current_node(self, node):
		"""Update the current executing node with enhanced status tracking."""
		self.current_node = node
		
		# Update UI labels
		self.current_node_label.configure(text=f"Node: {node.Name} ({node.ID})")
		self.current_experiment_label.configure(text=f"Experiment: {node.Experiment.get('Test Name', 'Unknown')}")
		
		# Determine detailed status
		if self.is_experiment_running(node):
			status_text = "Status: Running Experiment"
			self.current_status_label.configure(text=status_text, foreground='red')
		else:
			status_text = "Status: Preparing"
			self.current_status_label.configure(text=status_text, foreground='blue')
		
		# Update node visual status
		self.redraw_node(node)
		
		# Update progress
		self.update_progress()
		
		self.log_message(f"Executing node: {node.Name} ({node.ID})")

	def update_node_completed(self, node):
		"""Update node as completed (Green)."""
		self.completed_nodes.add(node.ID)
		self.completed_count += 1
		
		# Update statistics
		self.completed_nodes_label.configure(text=f"✓ Completed: {self.completed_count}")
		
		# Update node visual status
		self.redraw_node(node)
		
		# Update progress
		self.update_progress()
		
		# Log results with details
		summary = node.get_execution_summary()
		self.log_message(f"Node completed: {node.Name} - {summary['pass_count']} pass, {summary['fail_count']} fail", "success")

	def update_node_failed(self, node):
		"""Update node as failed with proper color coding."""
		self.failed_nodes.add(node.ID)
		self.failed_count += 1
		
		# Update statistics
		self.failed_nodes_label.configure(text=f"✗ Failed: {self.failed_count}")
		
		# Update node visual status (will determine if yellow or red)
		self.redraw_node(node)
		
		# Update progress
		self.update_progress()
		
		# Log with appropriate level
		if self.is_execution_failure(node):
			self.log_message(f"Node execution failed: {node.Name}", "warning")  # Yellow failures
		else:
			self.log_message(f"Node test failed: {node.Name}", "error")  # Red failures

	def redraw_node(self, node):
		"""Redraw a specific node with updated status."""
		if node.ID not in self.node_widgets:
			return
		
		widget_info = self.node_widgets[node.ID]
		pos = widget_info['position']
		
		# Remove old node elements
		self.canvas.delete(f"node_{node.ID}")
		
		# Redraw with new status
		self.draw_single_node(node, pos)
		
	def draw_status_legend(self):
		"""Draw a status legend on the canvas."""
		legend_x = 20
		legend_y = 20
		
		legend_items = [
			('idle', '○ Waiting', '#CCCCCC'),
			('running', '● Running', '#FF5722'),    # Red
			('completed', '✓ Done', '#4CAF50'),     # Green  
			('execution_fail', '! Exec Fail', '#FFC107'),  # Yellow
			('failed', '✗ Failed', '#F44336')
		]
		
		# Legend background
		legend_bg = self.canvas.create_rectangle(
			legend_x - 5, legend_y - 5,
			legend_x + 120, legend_y + len(legend_items) * 25 + 5,
			fill='white', outline='black', width=1,
			tags="legend"
		)
		
		# Legend items
		for i, (status, label, color) in enumerate(legend_items):
			y_pos = legend_y + i * 25
			
			# Status indicator
			self.canvas.create_oval(
				legend_x, y_pos,
				legend_x + 15, y_pos + 15,
				fill=color, outline='black', width=1,
				tags="legend"
			)
			
			# Label
			self.canvas.create_text(
				legend_x + 20, y_pos + 7,
				text=label, fill='black',
				font=("Arial", 8), anchor='w',
				tags="legend"
			)

	def update_node_cancelled(self, node):
		"""Update node as cancelled."""
		self._update_node_status_safe(node.ID, "Cancelled", self.node_colors['cancelled'], 'white')
		self.log_message(f"Node cancelled: {node.Name}", "warning")

	def update_node_ended(self, node):
		"""Update node as ended."""
		# Determine final status based on results
		if 'FAIL' in node.runStatusHistory:
			self.update_node_failed(node)
		else:
			self.update_node_completed(node)
		
		self.log_message(f"Node ended: {node.Name}", "success")

	def update_progress(self):
		"""Update overall progress."""
		if self.total_nodes > 0:
			progress = ((self.completed_count + self.failed_count) / self.total_nodes) * 100
			self.progress_var.set(progress)
			self.progress_label.configure(text=f"{int(progress)}%")
			
			# Update shared status panel
			self.status_panel.update_overall_progress(
				self.completed_count + self.failed_count - 1,  # Current index
				self.total_nodes,
				1.0  # Current progress (completed)
			)
		
		# Update timing
		if self.start_time:
			elapsed = time.time() - self.start_time
			self.status_panel.elapsed_time_label.configure(text=f"Time: {self._format_time(elapsed)}")

	def execution_completed(self):
		"""Handle normal execution completion."""
		self.is_running = False
		
		# Update UI
		self._enable_ui_buttons_safe()
		self.current_status_label.configure(text="Status: Completed")
		
		total_time = time.time() - self.start_time if self.start_time else 0
		self.log_message(f"Flow execution completed in {self._format_time(total_time)}", "success")
		self.log_message(f"Results: {self.completed_count} completed, {self.failed_count} failed")
		
		self.status_label.configure(text=" Completed ", bg="#006400", fg="white")

	def execution_cancelled(self, data):
		"""Handle execution cancellation."""
		self.is_running = False
		
		self.current_status_label.configure(text="Status: Cancelled")
		self.log_message(f"Flow execution cancelled: {data.get('reason', 'Unknown reason')}", "warning")
		
		self.status_label.configure(text=" Cancelled ", bg="gray", fg="white")

	def execution_ended(self, data):
		"""Handle execution ended by END command."""
		self.is_running = False
		
		self.current_status_label.configure(text="Status: Ended")
		self.log_message(f"Flow execution ended: {data.get('reason', 'END command')}", "success")
		
		self.status_label.configure(text=" Ended ", bg="orange", fg="black")

	def execution_error(self, error_msg):
		"""Handle execution error."""
		self.is_running = False
		
		# Update UI
		self._enable_ui_buttons_safe()
		self.current_status_label.configure(text="Status: Error")
		self.log_message(f"Execution error: {error_msg}", "error")
		
		self.status_label.configure(text=" Error ", bg="red", fg="white")

	def flow_execution_complete(self):
		"""Handle flow execution completion."""
		self.execution_completed()

	def execution_cancelled_complete(self):
		"""Handle cancellation completion."""
		self._enable_ui_buttons_safe()

	def execution_ended_complete(self):
		"""Handle end command completion."""
		self._enable_ui_buttons_safe()

	def _enable_ui_buttons_safe(self):
		"""Safely enable UI buttons with error handling (matching ControlPanel)."""
		try:
			self.start_button.configure(state=tk.NORMAL)
			self.cancel_button.configure(state=tk.DISABLED)
			self.hold_button.configure(state=tk.DISABLED, text="Hold", style="Hold.TButton")
			self.end_button.configure(state=tk.DISABLED, text="End", style="End.TButton")
			self.browse_button.configure(state=tk.NORMAL)
		except Exception as e:
			self.log_message(f"Error enabling buttons: {e}", "error")

	def _update_node_status_safe(self, node_id: str, status: str, bg_color: str, fg_color: str):
		"""Safely update node status with error handling."""
		try:
			if node_id in self.node_widgets:
				# Update node visual representation
				# This would update the canvas representation of the node
				# Implementation depends on how nodes are drawn
				pass
		except Exception as e:
			self.log_message(f"[ERROR] Node status update failed for {node_id}: {e}", "error")

	def _format_time(self, seconds: float) -> str:
		"""Format seconds to MM:SS format."""
		minutes = int(seconds // 60)
		seconds = int(seconds % 60)
		return f"{minutes:02d}:{seconds:02d}"

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
		self.folder_entry.configure(state='normal')
		self.folder_entry.delete(0, tk.END)
		self.folder_entry.insert(0, folder_path)
		self.folder_entry.configure(state='readonly')
		
		self.log_message(f"Selected flow folder: {folder_path}")
		
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
				self.log_message(f"Found {filename}")
			else:
				# File not found
				missing_files.append(file_type)
				frame_info['status'].configure(foreground="red")
				frame_info['browse'].configure(state=tk.NORMAL)
				self.log_message(f"Missing {filename}", "warning")
		
		# Store found file paths
		self.structure_path = found_files.get('structure')
		self.flows_path = found_files.get('flows')
		self.ini_path = found_files.get('ini')
		
		if missing_files:
			# Show message about missing files
			missing_list = [self.default_files[ft] for ft in missing_files]
			message = f"Missing files:\n" + "\n".join(f"• {f}" for f in missing_list)
			message += "\n\nPlease use the Browse buttons to select these files individually."
			
			messagebox.showwarning("Missing Configuration Files", message)
			self.log_message("Some configuration files are missing. Please browse for them individually.", "warning")
		else:
			# All files found, try to load the flow
			self.log_message("All configuration files found. Loading flow...")
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
		elif file_type == 'flows':
			self.flows_path = file_path
		elif file_type == 'ini':
			self.ini_path = file_path
		
		# Update UI
		frame_info = self.file_labels[file_type]
		frame_info['status'].configure(foreground="green")
		frame_info['name'].configure(text=os.path.basename(file_path))
		frame_info['browse'].configure(state=tk.DISABLED)
		
		self.log_message(f"Selected {file_type} file: {os.path.basename(file_path)}")
		
		# Check if all files are now available
		if all([self.structure_path, self.flows_path, self.ini_path]):
			self.log_message("All configuration files selected. Loading flow...")
			self.load_flow_configuration()

	def load_flow_configuration(self):
		"""Load the flow configuration from selected files with enhanced validation."""
		try:
			# Create builder (using the existing FlowTestBuilder)
			self.builder = FlowTestBuilder(
				self.structure_path, 
				self.flows_path, 
				self.ini_path, 
				Framework=self.framework,
				logger=self.log_message
			)
			
			# Validate flow structure first
			is_valid, warnings, errors = self.validate_flow_structure()
			
			if errors:
				error_msg = "Flow validation failed:\n" + "\n".join(f"• {error}" for error in errors)
				raise ValueError(error_msg)
			
			# Show warnings if any
			if warnings:
				warning_msg = "Flow loaded with warnings:\n" + "\n".join(f"• {warning}" for warning in warnings)
				self.log_message(warning_msg, "warning")
				
				# Ask user if they want to continue
				if not messagebox.askyesno("Flow Warnings", 
										f"{warning_msg}\n\nDo you want to continue loading this flow?"):
					return
			
			# Find the start node dynamically
			start_node_id = self.find_start_node()
			
			if not start_node_id:
				raise ValueError("No start node found in flow configuration. Please ensure your flow has a StartNode or define a root node.")
			
			# Build the flow starting from the discovered start node
			self.root_node = self.builder._FlowTestBuilder__build_instance(start_node_id)
			
			# Create executor
			self.executor = FlowTestExecutor(root=self.root_node, framework=self.framework)
			
			# Update total nodes count
			self.total_nodes = len(self.builder.builtNodes)
			
			# Log flow summary
			self.log_flow_summary()
			
			# Draw the flow diagram
			self.draw_flow_diagram()
			
			# Enable start button
			self.start_button.configure(state=tk.NORMAL)
			
			self.log_message(f"Flow loaded successfully with {self.total_nodes} nodes", "success")
			self.log_message(f"Start node: {start_node_id} ({self.root_node.Name})")
			self.log_message("Ready to start execution")
			
			# Show validation results if there were warnings
			if warnings:
				self.show_flow_validation_results()
			
		except Exception as e:
			error_msg = f"Error loading flow configuration: {str(e)}"
			self.log_message(error_msg, "error")
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
		"""
		Draw the complete flow diagram with nodes and connections.
		Updated for vertical layout.
		"""
		if not self.builder:
			self.show_canvas_message("No flow configuration loaded")
			return
		
		self.canvas.delete("all")
		self.node_widgets.clear()
		self.connection_lines.clear()
		
		# Update total nodes label
		self.total_nodes_label.configure(text=f"Total: {self.total_nodes}")
		
		# Calculate layout
		positions = self.calculate_node_positions()
		
		if not positions:
			self.show_canvas_message("Unable to calculate node positions")
			return
		
		# Calculate required canvas size based on positions
		max_x = max(pos['x'] + pos['width'] for pos in positions.values()) + 50
		max_y = max(pos['y'] + pos['height'] for pos in positions.values()) + 50
		
		# Update canvas scroll region
		self.canvas.configure(scrollregion=(0, 0, max_x, max_y))
		
		# Draw connections first (so they appear behind nodes)
		self.draw_connections(positions)
		
		# Draw nodes
		self.draw_nodes(positions)
		
		# Add level labels on the left side
		self.draw_level_labels(positions)

	def draw_level_labels(self, positions):
		"""
		Draw level labels on the left side of the canvas.
		"""
		levels = {}
		for node_id, pos in positions.items():
			level = pos.get('level', 0)
			if level not in levels:
				levels[level] = pos['y'] + pos['height'] // 2
		
		for level, y_pos in levels.items():
			if level < 999:  # Don't show labels for unconnected nodes
				self.canvas.create_text(
					20, y_pos,
					text=f"Level {level}",
					fill="gray",
					font=("Arial", 8),
					anchor="w",
					tags="level_label"
				)
	
	def calculate_node_positions(self):
		"""
		Calculate optimal positions for all nodes using hierarchical top-to-bottom layout.
		Orders flows from start to finish with proper level-based positioning.
		"""
		if not self.builder:
			return {}
		
		positions = {}
		
		# Find the start node
		start_node_id = self.find_start_node()
		if not start_node_id:
			return self.calculate_simple_grid_positions()
		
		# Calculate hierarchical levels using breadth-first traversal
		node_levels = self.calculate_node_levels_bfs(start_node_id)
		
		# Group nodes by level and sort within levels
		levels = {}
		for node_id, level in node_levels.items():
			if level not in levels:
				levels[level] = []
			levels[level].append(node_id)
		
		# Sort nodes within each level for consistent ordering
		for level in levels:
			levels[level].sort(key=lambda x: self.get_node_sort_key(x))
		
		# Layout parameters
		node_width = 160
		node_height = 120
		horizontal_spacing = 220
		vertical_spacing = 180
		margin_x = 80
		margin_y = 60
		
		# Position nodes level by level (top to bottom)
		max_width = 0
		for level, nodes_in_level in sorted(levels.items()):
			y = margin_y + (level * vertical_spacing)
			
			# Calculate total width needed for this level
			total_width = len(nodes_in_level) * node_width + (len(nodes_in_level) - 1) * (horizontal_spacing - node_width)
			max_width = max(max_width, total_width)
			
			# Center the level horizontally
			canvas_width = max(1000, total_width + 2 * margin_x)
			start_x = (canvas_width - total_width) // 2
			
			# Position each node in the level
			for i, node_id in enumerate(nodes_in_level):
				x = start_x + i * horizontal_spacing
				
				positions[node_id] = {
					'x': x,
					'y': y,
					'width': node_width,
					'height': node_height,
					'center_x': x + node_width // 2,
					'center_y': y + node_height // 2,
					'level': level
				}
		
		return positions

	def calculate_node_levels_bfs(self, start_node_id):
		"""
		Calculate node levels using breadth-first search for proper top-to-bottom ordering.
		"""
		node_levels = {}
		queue = [(start_node_id, 0)]
		visited = set()
		
		while queue:
			node_id, level = queue.pop(0)
			
			if node_id in visited:
				continue
			
			visited.add(node_id)
			
			# Assign level (use minimum level if node was seen before)
			if node_id in node_levels:
				node_levels[node_id] = min(node_levels[node_id], level)
			else:
				node_levels[node_id] = level
			
			# Add connected nodes to queue
			node_config = self.builder.structureFile.get(node_id, {})
			output_map = node_config.get("outputNodeMap", {})
			
			for target_id in output_map.values():
				if target_id in self.builder.structureFile and target_id not in visited:
					queue.append((target_id, level + 1))
		
		# Handle any unconnected nodes
		for node_id in self.builder.structureFile.keys():
			if node_id not in node_levels:
				node_levels[node_id] = 999  # Place at bottom
		
		return node_levels

	def get_node_sort_key(self, node_id):
		"""
		Generate sort key for consistent node ordering within levels.
		"""
		node_config = self.builder.structureFile.get(node_id, {})
		node_name = node_config.get("name", "")
		instance_type = node_config.get("instanceType", "")
		
		# Priority order: StartNode, regular nodes, EndNode
		if instance_type == "StartNode":
			priority = 0
		elif instance_type == "EndNode":
			priority = 2
		else:
			priority = 1
		
		return (priority, node_name.lower(), node_id)

	def draw_single_node(self, node, pos):
		"""
		Draw a single node with enhanced status styling and better visual hierarchy.
		"""
		x, y = pos['x'], pos['y']
		width, height = pos['width'], pos['height']
		
		# Determine node status and colors
		status = self.get_node_status_color(node)
		bg_color = self.node_colors[status]
		text_color = self.node_text_colors[status]
		
		# Get node configuration for additional styling
		node_config = self.builder.structureFile.get(node.ID, {})
		instance_type = node_config.get("instanceType", "")
		
		# Add special styling for start/end nodes
		if instance_type == "StartNode":
			bg_color = self._blend_colors(bg_color, '#90EE90', 0.2)  # Green tint
			border_color = '#2E7D32'
			border_width = 3
		elif instance_type == "EndNode":
			bg_color = self._blend_colors(bg_color, '#FFB6C1', 0.2)  # Pink tint
			border_color = '#C62828'
			border_width = 3
		else:
			border_color = 'black'
			border_width = 2
		
		# Draw main node rectangle with enhanced styling
		node_rect = self.canvas.create_rectangle(
			x, y, x + width, y + height,
			fill=bg_color, outline=border_color, width=border_width,
			tags=f"node_{node.ID}"
		)
		
		# Add status indicator border for running experiments
		if status == 'running':
			# Animated border for running status
			self.canvas.create_rectangle(
				x-2, y-2, x + width + 2, y + height + 2,
				fill='', outline='#FF5722', width=4,
				tags=f"node_{node.ID}"
			)
		
		# Draw node content with better layout
		self.draw_node_content(node, pos, text_color, instance_type)
		
		# Draw status indicator
		self.draw_status_indicator(node, pos, status)
		
		# Store widget references
		self.node_widgets[node.ID] = {
			'rect': node_rect,
			'position': pos,
			'status': status
		}

	def draw_node_content(self, node, pos, text_color, instance_type):
		"""Draw the content inside a node with proper layout."""
		x, y = pos['x'], pos['y']
		width, height = pos['width'], pos['height']
		
		# Node name (larger, bold)
		name_text = self.canvas.create_text(
			x + width // 2, y + 18,
			text=node.Name, fill=text_color,
			font=("Arial", 10, "bold"),
			width=width - 10,
			tags=f"node_{node.ID}"
		)
		
		# Node ID
		id_text = self.canvas.create_text(
			x + width // 2, y + 38,
			text=f"ID: {node.ID}", fill=text_color,
			font=("Arial", 8),
			tags=f"node_{node.ID}"
		)
		
		# Instance type (cleaned up)
		type_display = instance_type.replace('FlowInstance', '').replace('Node', '')
		if not type_display:
			type_display = "Flow"
		
		type_text = self.canvas.create_text(
			x + width // 2, y + 55,
			text=type_display, fill=text_color,
			font=("Arial", 8, "italic"),
			tags=f"node_{node.ID}"
		)
		
		# Experiment info (if applicable)
		if instance_type not in ['StartNode', 'EndNode']:
			exp_name = node.Experiment.get('Test Name', 'No Experiment')
			if exp_name and len(exp_name) > 18:
				exp_name = exp_name[:15] + "..."
			
			exp_color = 'blue' if text_color == 'black' else 'lightblue'
			exp_text = self.canvas.create_text(
				x + width // 2, y + 75,
				text=exp_name, fill=exp_color,
				font=("Arial", 7), width=width - 10,
				tags=f"node_{node.ID}"
			)
		
		# Level indicator
		if 'level' in pos and pos['level'] < 999:
			level_text = self.canvas.create_text(
				x + width - 15, y + 12,
				text=f"L{pos['level']}", fill=text_color,
				font=("Arial", 6, "bold"),
				tags=f"node_{node.ID}"
			)

	def draw_status_indicator(self, node, pos, status):
		"""Draw enhanced status indicator with legend."""
		x, y = pos['x'], pos['y']
		
		# Status indicator (larger, more visible)
		indicator_size = 20
		indicator_x = x + 8
		indicator_y = y + 8
		
		# Status color mapping
		status_colors = {
			'idle': '#CCCCCC',
			'current': '#2196F3',
			'running': '#FF5722',      # Red - running
			'completed': '#4CAF50',    # Green - done
			'failed': '#F44336',
			'execution_fail': '#FFC107', # Yellow - execution fail
			'cancelled': '#9E9E9E'
		}
		
		indicator_color = status_colors.get(status, '#CCCCCC')
		
		# Draw indicator circle
		indicator = self.canvas.create_oval(
			indicator_x, indicator_y,
			indicator_x + indicator_size, indicator_y + indicator_size,
			fill=indicator_color, outline='black', width=2,
			tags=f"node_{node.ID}"
		)
		
		# Add status symbol
		symbol_map = {
			'idle': '○',
			'current': '▶',
			'running': '●',      # Red dot for running
			'completed': '✓',    # Green checkmark for done
			'failed': '✗',
			'execution_fail': '!', # Yellow exclamation for execution fail
			'cancelled': '◐'
		}
		
		symbol = symbol_map.get(status, '○')
		symbol_color = 'white' if status in ['running', 'completed', 'failed'] else 'black'
		
		symbol_text = self.canvas.create_text(
			indicator_x + indicator_size // 2,
			indicator_y + indicator_size // 2,
			text=symbol, fill=symbol_color,
			font=("Arial", 10, "bold"),
			tags=f"node_{node.ID}"
		)

	def draw_single_node(self, node, pos):
		"""
		Draw a single node with current status styling and level information.
		"""
		x, y = pos['x'], pos['y']
		width, height = pos['width'], pos['height']
		
		# Determine node color based on status
		if node.ID in self.failed_nodes:
			color = self.node_colors['failed']
			text_color = 'white'
		elif node.ID in self.completed_nodes:
			color = self.node_colors['completed']
			text_color = 'white'
		elif self.current_node and node.ID == self.current_node.ID:
			color = self.node_colors['current']
			text_color = 'white'
		else:
			color = self.node_colors['idle']
			text_color = 'black'
		
		# Add subtle gradient effect based on node type
		node_config = self.builder.structureFile.get(node.ID, {})
		instance_type = node_config.get("instanceType", "")
		
		if instance_type == "StartNode":
			# Add green tint for start nodes
			color = self._blend_colors(color, '#90EE90', 0.3)
		elif instance_type == "EndNode":
			# Add red tint for end nodes
			color = self._blend_colors(color, '#FFB6C1', 0.3)
		
		# Draw main node rectangle with rounded corners effect
		# Main rectangle
		node_rect = self.canvas.create_rectangle(
			x, y, x + width, y + height,
			fill=color, outline='black', width=2,
			tags=f"node_{node.ID}"
		)
		
		# Draw node name (larger font for better visibility)
		name_text = self.canvas.create_text(
			x + width // 2, y + 15,
			text=node.Name, fill=text_color,
			font=("Arial", 9, "bold"),
			width=width - 10,
			tags=f"node_{node.ID}"
		)
		
		# Draw node ID
		id_text = self.canvas.create_text(
			x + width // 2, y + 32,
			text=f"ID: {node.ID}", fill=text_color,
			font=("Arial", 7),
			tags=f"node_{node.ID}"
		)
		
		# Draw instance type
		type_text = self.canvas.create_text(
			x + width // 2, y + 48,
			text=instance_type.replace('FlowInstance', ''),
			fill=text_color, font=("Arial", 8),
			tags=f"node_{node.ID}"
		)
		
		# Draw experiment info (if applicable)
		if instance_type not in ['StartNode', 'EndNode']:
			exp_name = node.Experiment.get('Test Name', 'No Experiment')
			if exp_name and len(exp_name) > 15:
				exp_name = exp_name[:12] + "..."
			
			exp_text = self.canvas.create_text(
				x + width // 2, y + 65,
				text=exp_name, fill='blue' if text_color == 'black' else 'lightblue',
				font=("Arial", 7), width=width - 10,
				tags=f"node_{node.ID}"
			)
		
		# Draw level indicator (small number in corner)
		if 'level' in pos:
			level_text = self.canvas.create_text(
				x + width - 10, y + 10,
				text=f"L{pos['level']}", fill=text_color,
				font=("Arial", 6),
				tags=f"node_{node.ID}"
			)
		
		# Draw connection ports with better visibility
		self.draw_connection_ports_enhanced(node, pos, text_color)
		
		# Store widget references
		self.node_widgets[node.ID] = {
			'rect': node_rect,
			'name': name_text,
			'id': id_text,
			'type': type_text,
			'position': pos
		}

	def draw_connection_ports_enhanced(self, node, pos, text_color):
		"""
		Draw enhanced connection ports on a node.
		"""
		node_id = node.ID
		x, y = pos['x'], pos['y']
		width, height = pos['width'], pos['height']
		
		# Get node configuration
		node_config = self.builder.structureFile.get(node_id, {})
		output_map = node_config.get("outputNodeMap", {})
		
		# Output ports (bottom of node)
		if output_map:
			port_size = 10
			port_spacing = 25
			ports = sorted(output_map.keys())
			
			# Calculate starting position to center ports
			total_width = len(ports) * port_spacing
			start_x = x + (width - total_width) // 2 + port_spacing // 2
			port_y = y + height - port_size - 5
			
			for i, port in enumerate(ports):
				port_x = start_x + i * port_spacing
				port_color = self.connection_colors.get(int(port), '#666666')
				
				# Port rectangle
				port_rect = self.canvas.create_rectangle(
					port_x, port_y,
					port_x + port_size, port_y + port_size,
					fill=port_color, outline='black', width=1,
					tags=f"node_{node_id}"
				)
				
				# Port number
				port_text = self.canvas.create_text(
					port_x + port_size//2, port_y + port_size//2,
					text=str(port), fill='white',
					font=("Arial", 6, "bold"),
					tags=f"node_{node_id}"
				)
		
		# Input port (top of node) - only for non-start nodes
		instance_type = node_config.get("instanceType", "")
		if instance_type != "StartNode":
			input_port_size = 8
			input_port = self.canvas.create_rectangle(
				x + width//2 - input_port_size//2, y - 2,
				x + width//2 + input_port_size//2, y + input_port_size - 2,
				fill='gray', outline='black', width=1,
				tags=f"node_{node_id}"
			)

	def _blend_colors(self, color1, color2, ratio):
		"""
		Blend two colors together.
		
		Args:
			color1: Base color (hex string)
			color2: Blend color (hex string)  
			ratio: Blend ratio (0.0 to 1.0)
			
		Returns:
			str: Blended color as hex string
		"""
		try:
			# Convert hex to RGB
			def hex_to_rgb(hex_color):
				hex_color = hex_color.lstrip('#')
				return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
			
			def rgb_to_hex(rgb):
				return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
			
			rgb1 = hex_to_rgb(color1)
			rgb2 = hex_to_rgb(color2)
			
			# Blend the colors
			blended_rgb = tuple(
				int(rgb1[i] * (1 - ratio) + rgb2[i] * ratio)
				for i in range(3)
			)
			
			return rgb_to_hex(blended_rgb)
		except:
			return color1  # Return original color if blending fails

	def draw_connections(self, positions):
		"""Draw connections between nodes."""
		for node in self.builder.builtNodes.values():
			if not node.outputNodeMap:
				continue
				
			start_pos = positions[node.ID]
			start_x = start_pos['center_x']
			start_y = start_pos['y'] + start_pos['height']
			
			for port, next_node in node.outputNodeMap.items():
				end_pos = positions[next_node.ID]
				end_x = end_pos['center_x']
				end_y = end_pos['y']
				
				# Choose color based on port
				color = self.connection_colors.get(port, '#666666')
				
				# Draw connection line with arrow
				line = self.canvas.create_line(
					start_x, start_y, end_x, end_y,
					fill=color, width=3, arrow=tk.LAST,
					arrowshape=(10, 12, 3),
					tags=f"connection_{node.ID}_{next_node.ID}"
				)
				
				# Draw port label
				mid_x = (start_x + end_x) // 2
				mid_y = (start_y + end_y) // 2
				
				port_label = self.canvas.create_text(
					mid_x, mid_y,
					text=str(port), fill=color,
					font=("Arial", 8, "bold"),
					tags=f"connection_{node.ID}_{next_node.ID}"
				)
				
				self.connection_lines[f"{node.ID}_{next_node.ID}"] = {
					'line': line,
					'label': port_label,
					'port': port
				}

	def find_start_node(self):
		"""
		Dynamically find the start node from the flow configuration.
		Enhanced to handle the structure from the designer properly.
		
		Returns:
			str: The ID of the start node, or None if not found
		"""
		try:
			# Method 1: Look for nodes with instanceType "StartNode" (most reliable)
			start_nodes = []
			for node_id, node_config in self.builder.structureFile.items():
				if node_config.get("instanceType") == "StartNode":
					start_nodes.append(node_id)
					self.log_message(f"Found StartNode: {node_id} ({node_config.get('name', 'Unknown')})")
			
			if len(start_nodes) == 1:
				return start_nodes[0]
			elif len(start_nodes) > 1:
				self.log_message(f"Multiple StartNodes found: {start_nodes}. Using first one: {start_nodes[0]}", "warning")
				return start_nodes[0]
			
			# Method 2: Look for nodes that are not referenced as targets by other nodes
			# (i.e., nodes that have no incoming connections)
			all_node_ids = set(self.builder.structureFile.keys())
			referenced_nodes = set()
			
			# Collect all nodes that are referenced as targets
			for node_id, node_config in self.builder.structureFile.items():
				output_map = node_config.get("outputNodeMap", {})
				for target_id in output_map.values():
					referenced_nodes.add(target_id)
			
			# Find nodes that are not referenced (potential start nodes)
			unreferenced_nodes = all_node_ids - referenced_nodes
			
			if unreferenced_nodes:
				# If multiple unreferenced nodes, prefer certain patterns
				start_node_candidates = []
				
				for node_id in unreferenced_nodes:
					node_config = self.builder.structureFile[node_id]
					node_name = node_config.get("name", "").lower()
					instance_type = node_config.get("instanceType", "")
					
					# Prioritize StartNode types first
					if instance_type == "StartNode":
						start_node_candidates.insert(0, node_id)
					# Then prioritize nodes with start-like names
					elif any(keyword in node_name for keyword in ['start', 'begin', 'root', 'baseline', 'entry']):
						start_node_candidates.append(node_id)
					else:
						start_node_candidates.append(node_id)
				
				if start_node_candidates:
					selected_start = start_node_candidates[0]
					self.log_message(f"Found potential start node: {selected_start}")
					
					if len(start_node_candidates) > 1:
						self.log_message(f"Multiple start candidates found: {start_node_candidates}. Using: {selected_start}", "warning")
					
					return selected_start
			
			# Method 3: Look for specific naming patterns in node IDs or names
			start_patterns = ['START', 'BEGIN', 'ROOT', 'BASELINE', 'ENTRY', 'INIT']
			
			for pattern in start_patterns:
				for node_id, node_config in self.builder.structureFile.items():
					node_name = node_config.get("name", "")
					if pattern in node_id.upper() or pattern in node_name.upper():
						self.log_message(f"Found start node by pattern '{pattern}': {node_id}")
						return node_id
			
			# Method 4: If all else fails, let user choose
			if all_node_ids:
				return self.prompt_user_for_start_node(list(all_node_ids))
			
			return None
			
		except Exception as e:
			self.log_message(f"Error finding start node: {str(e)}", "error")
			return None

	def prompt_user_for_start_node(self, available_nodes):
		"""
		Prompt user to select start node when automatic detection fails.
		
		Args:
			available_nodes: List of available node IDs
			
		Returns:
			str: Selected node ID, or None if cancelled
		"""
		try:
			# Create selection dialog
			dialog = tk.Toplevel(self.root)
			dialog.title("Select Start Node")
			dialog.geometry("400x300")
			dialog.transient(self.root)
			dialog.grab_set()
			
			# Center dialog
			dialog.geometry("+%d+%d" % (
				self.root.winfo_rootx() + 50, 
				self.root.winfo_rooty() + 50
			))
			
			selected_node = None
			
			# Instructions
			instruction_frame = ttk.Frame(dialog)
			instruction_frame.pack(fill=tk.X, padx=10, pady=10)
			
			ttk.Label(instruction_frame, 
					text="Could not automatically detect start node.\nPlease select the node where execution should begin:",
					font=("Arial", 10)).pack()
			
			# Node list
			list_frame = ttk.Frame(dialog)
			list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
			
			# Listbox with node details
			listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
			scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
			listbox.configure(yscrollcommand=scrollbar.set)
			
			# Populate listbox with node info
			for node_id in available_nodes:
				node_config = self.builder.structureFile.get(node_id, {})
				node_name = node_config.get("name", "Unknown")
				node_type = node_config.get("instanceType", "Unknown")
				
				display_text = f"{node_id} - {node_name} ({node_type})"
				listbox.insert(tk.END, display_text)
			
			listbox.pack(side="left", fill="both", expand=True)
			scrollbar.pack(side="right", fill="y")
			
			# Select first item by default
			if available_nodes:
				listbox.selection_set(0)
			
			# Buttons
			button_frame = ttk.Frame(dialog)
			button_frame.pack(fill=tk.X, padx=10, pady=10)
			
			def on_select():
				nonlocal selected_node
				selection = listbox.curselection()
				if selection:
					selected_node = available_nodes[selection[0]]
					dialog.destroy()
			
			def on_cancel():
				dialog.destroy()
			
			ttk.Button(button_frame, text="Select", command=on_select).pack(side=tk.RIGHT, padx=5)
			ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)
			
			# Wait for dialog to close
			dialog.wait_window()
			
			if selected_node:
				self.log_message(f"User selected start node: {selected_node}")
			
			return selected_node
			
		except Exception as e:
			self.log_message(f"Error in start node selection dialog: {str(e)}", "error")
			return None

	def validate_flow_structure(self):
		"""
		Validate the loaded flow structure for common issues.
		
		Returns:
			tuple: (is_valid, warnings, errors)
		"""
		warnings = []
		errors = []
		
		try:
			if not self.builder or not self.builder.structureFile:
				errors.append("No flow structure loaded")
				return False, warnings, errors
			
			all_nodes = set(self.builder.structureFile.keys())
			
			# Check for start nodes
			start_nodes = []
			for node_id, node_config in self.builder.structureFile.items():
				if node_config.get("instanceType") == "StartNode":
					start_nodes.append(node_id)
			
			if not start_nodes:
				warnings.append("No explicit StartNode found - using automatic detection")
			elif len(start_nodes) > 1:
				warnings.append(f"Multiple StartNodes found: {start_nodes}")
			
			# Check for end nodes
			end_nodes = []
			for node_id, node_config in self.builder.structureFile.items():
				if node_config.get("instanceType") == "EndNode":
					end_nodes.append(node_id)
			
			if not end_nodes:
				warnings.append("No EndNode found - flow may run indefinitely")
			
			# Check for unreachable nodes
			if self.root_node:
				reachable_nodes = self.find_reachable_nodes(self.root_node.ID)
				unreachable = all_nodes - reachable_nodes
				
				if unreachable:
					warnings.append(f"Unreachable nodes: {list(unreachable)}")
			
			# Check for missing target references
			for node_id, node_config in self.builder.structureFile.items():
				output_map = node_config.get("outputNodeMap", {})
				for port, target_id in output_map.items():
					if target_id not in all_nodes:
						errors.append(f"Node {node_id} references non-existent target: {target_id}")
			
			# Check for circular references (basic check)
			if self.has_circular_references():
				warnings.append("Potential circular references detected")
			
			is_valid = len(errors) == 0
			return is_valid, warnings, errors
			
		except Exception as e:
			errors.append(f"Validation error: {str(e)}")
			return False, warnings, errors

	def find_reachable_nodes(self, start_node_id, visited=None):
		"""
		Find all nodes reachable from the start node.
		
		Args:
			start_node_id: ID of the starting node
			visited: Set of already visited nodes (for recursion)
			
		Returns:
			set: Set of reachable node IDs
		"""
		if visited is None:
			visited = set()
		
		if start_node_id in visited or start_node_id not in self.builder.structureFile:
			return visited
		
		visited.add(start_node_id)
		
		# Follow all connections
		node_config = self.builder.structureFile[start_node_id]
		output_map = node_config.get("outputNodeMap", {})
		
		for target_id in output_map.values():
			self.find_reachable_nodes(target_id, visited)
		
		return visited

	def has_circular_references(self):
		"""
		Check for circular references in the flow (basic implementation).
		
		Returns:
			bool: True if circular references are detected
		"""
		try:
			def visit_node(node_id, path):
				if node_id in path:
					return True  # Circular reference found
				
				if node_id not in self.builder.structureFile:
					return False
				
				node_config = self.builder.structureFile[node_id]
				output_map = node_config.get("outputNodeMap", {})
				
				new_path = path | {node_id}
				
				for target_id in output_map.values():
					if visit_node(target_id, new_path):
						return True
				
				return False
			
			# Check from each node
			for node_id in self.builder.structureFile.keys():
				if visit_node(node_id, set()):
					return True
			
			return False
			
		except Exception:
			return False  # Assume no circular references if check fails

	def show_flow_validation_results(self):
		"""Show flow validation results to user."""
		try:
			is_valid, warnings, errors = self.validate_flow_structure()
			
			if not warnings and not errors:
				self.log_message("Flow validation passed - no issues found", "success")
				return
			
			# Create validation results dialog
			dialog = tk.Toplevel(self.root)
			dialog.title("Flow Validation Results")
			dialog.geometry("500x400")
			dialog.transient(self.root)
			
			# Results text
			results_text = tk.Text(dialog, wrap=tk.WORD, font=("Consolas", 10))
			results_scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=results_text.yview)
			results_text.configure(yscrollcommand=results_scrollbar.set)
			
			results_text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
			results_scrollbar.pack(side="right", fill="y", pady=10)
			
			# Add results
			if errors:
				results_text.insert(tk.END, "ERRORS:\n", "error")
				for error in errors:
					results_text.insert(tk.END, f"  ✗ {error}\n", "error")
				results_text.insert(tk.END, "\n")
			
			if warnings:
				results_text.insert(tk.END, "WARNINGS:\n", "warning")
				for warning in warnings:
					results_text.insert(tk.END, f"  ⚠ {warning}\n", "warning")
			
			if is_valid:
				results_text.insert(tk.END, "\n✓ Flow structure is valid and can be executed.\n", "success")
			else:
				results_text.insert(tk.END, "\n✗ Flow has errors and cannot be executed safely.\n", "error")
			
			# Configure text colors
			results_text.tag_config("success", foreground="green", font=("Consolas", 10, "bold"))
			results_text.tag_config("error", foreground="red")
			results_text.tag_config("warning", foreground="orange")
			
			results_text.configure(state=tk.DISABLED)
			
			# Log summary
			if errors:
				self.log_message(f"Flow validation failed with {len(errors)} errors", "error")
			elif warnings:
				self.log_message(f"Flow validation passed with {len(warnings)} warnings", "warning")
			
		except Exception as e:
			self.log_message(f"Error during flow validation: {str(e)}", "error")
			
	# ==================== EVENT HANDLERS ====================
	
	def on_canvas_click(self, event):
		"""Handle canvas click events."""
		# Find clicked item
		item = self.canvas.find_closest(event.x, event.y)[0]
		tags = self.canvas.gettags(item)
		
		# Check if it's a node
		for tag in tags:
			if tag.startswith("node_"):
				node_id = tag.split("_", 1)[1]
				self.show_node_details(node_id)
				break

	def show_node_details(self, node_id):
		"""Show detailed information about a node."""
		node = self.builder.builtNodes.get(node_id)
		if not node:
			return
		
		# Create popup window with node details
		popup = tk.Toplevel(self.root)
		popup.title(f"Node Details: {node.Name}")
		popup.geometry("400x300")
		popup.transient(self.root)
		
		# Node information
		info_frame = ttk.LabelFrame(popup, text="Node Information", padding=10)
		info_frame.pack(fill=tk.X, padx=10, pady=5)
		
		ttk.Label(info_frame, text=f"ID: {node.ID}").pack(anchor="w")
		ttk.Label(info_frame, text=f"Name: {node.Name}").pack(anchor="w")
		ttk.Label(info_frame, text=f"Type: {type(node).__name__}").pack(anchor="w")
		
		# Experiment details
		exp_frame = ttk.LabelFrame(popup, text="Experiment Configuration", padding=10)
		exp_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
		
		exp_text = tk.Text(exp_frame, height=10, width=50)
		exp_scrollbar = ttk.Scrollbar(exp_frame, orient="vertical", command=exp_text.yview)
		exp_text.configure(yscrollcommand=exp_scrollbar.set)
		
		# Display experiment configuration
		for key, value in node.Experiment.items():
			exp_text.insert(tk.END, f"{key}: {value}\n")
		
		exp_text.pack(side="left", fill="both", expand=True)
		exp_scrollbar.pack(side="right", fill="y")

	def on_mousewheel(self, event):
		"""Handle mouse wheel scrolling on canvas."""
		self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

	def get_node_status_color(self, node):
		"""
		Determine node color based on current execution status.
		Implements the requested color scheme: Red=running, Green=done, Yellow=execution_fail
		"""
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
		"""
		Check if the experiment is currently running for this node.
		"""
		if not self.framework_api:
			return False
		
		try:
			state = self.framework_api.get_current_state()
			return (state.get('is_running', False) and 
					not state.get('waiting_for_command', False) and
					state.get('current_experiment') is not None)
		except:
			return False

	def is_execution_failure(self, node):
		"""
		Determine if the failure was due to execution issues (yellow) vs test failures (red).
		"""
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

	# ==================== HELP HANDLERS ====================

	def get_flow_summary(self):
		"""
		Get a summary of the loaded flow.
		
		Returns:
			dict: Flow summary information
		"""
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
			self.log_message(f"Error generating flow summary: {str(e)}", "error")
			return {}

	def log_flow_summary(self):
		"""Log a summary of the loaded flow."""
		summary = self.get_flow_summary()
		
		if not summary:
			return
		
		self.log_message("=== FLOW SUMMARY ===")
		self.log_message(f"Total Nodes: {summary['total_nodes']}")
		self.log_message(f"Start Node: {summary['start_node']} ({summary['start_node_name']})")
		self.log_message(f"Total Connections: {summary['total_connections']}")
		
		if summary['node_types']:
			self.log_message("Node Types:")
			for node_type, count in summary['node_types'].items():
				self.log_message(f"  {node_type}: {count}")
		
		if summary['experiments_used']:
			self.log_message(f"Experiments Used: {len(summary['experiments_used'])}")
			for exp in summary['experiments_used']:
				self.log_message(f"  - {exp}")
		
		self.log_message("==================")
	# ==================== CLEANUP & SHUTDOWN ====================
	
	def on_closing(self):
		"""Enhanced cleanup to prevent errors (matching ControlPanel)."""
		try:
			print("Starting automation interface cleanup...")
			self._cleanup_in_progress = True

			# CRITICAL: Stop the MainThreadHandler first
			if hasattr(self, 'main_thread_handler') and self.main_thread_handler:
				print("Cleaning up MainThreadHandler...")
				self.main_thread_handler.cleanup()
				time.sleep(0.1)
			
			# Cancel any running operations
			if hasattr(self, 'cancel_requested'):
				self.cancel_requested.set()

			# Stop execution
			self.thread_active = False
			self.is_running = False
			
			# Wait for thread to finish with timeout
			if self.execution_thread and self.execution_thread.is_alive():
				self.execution_thread.join(timeout=5.0)
				if self.execution_thread.is_alive():
					print("Warning: Execution thread did not stop gracefully")

			# Clear all queues
			self._clear_queue(self.command_queue)
			self._clear_queue(self.status_queue)
			self._clear_queue(self.update_queue)
			
			# Clean up Framework instance through manager
			if hasattr(self, 'framework_manager') and self.framework_manager:
				self.framework_manager.cleanup_current_instance("automation_interface_closing")
				self.framework_manager = None
			
			self.framework_api = None
			self.Framework_utils = None

			# Clean up flow components
			self.builder = None
			self.executor = None
			self.root_node = None
			
			# Schedule final cleanup
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
