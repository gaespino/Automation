import threading
import queue
from typing import Callable, Dict, Any, Optional
from datetime import datetime

class MainThreadHandler:
	"""
	Handles all main thread operations and status updates
	Designed to be reusable across different UI implementations
	"""
	
	def __init__(self, root, ui_controller):
		self.root = root
		self.ui = ui_controller  # Generic reference to UI (Control Panel or other UI)
		
		# Thread safety
		self._update_queue = queue.Queue()
		self._callback_enabled = True
		self._processing_critical = False
		
		# Handler registry - ALL handlers are here
		self._status_handlers = {}
		self._register_all_handlers()
		
		# Start the main thread processor
		self._start_processor()
		
	def _register_all_handlers(self):
		"""Register ALL status update handlers"""
		self._status_handlers = {
			# Core execution handlers
			'experiment_start': self._handle_experiment_start,
			'iteration_start': self._handle_iteration_start,
			'iteration_progress': self._handle_iteration_progress,
			'iteration_complete': self._handle_iteration_complete,
			'iteration_failed': self._handle_iteration_failed,
			'iteration_cancelled': self._handle_iteration_cancelled,
			'strategy_progress': self._handle_strategy_progress,
			'strategy_execution_complete': self._handle_strategy_complete,
			'strategy_complete': self._handle_strategy_complete,
			'experiment_complete': self._handle_experiment_complete,
			'experiment_failed': self._handle_experiment_failed,
			
			# Control command handlers
			'experiment_ended_by_command': self._handle_experiment_ended_by_command,
			'execution_halted': self._handle_execution_halted,
			'execution_resumed': self._handle_execution_resumed,
			'execution_cancelled': self._handle_execution_cancelled,
			
			# Step-by-step mode handlers
			'step_mode_enabled': self._handle_step_mode_enabled,
			'step_mode_disabled': self._handle_step_mode_disabled,
			'step_iteration_complete': self._handle_step_iteration_complete,
			'step_continue_issued': self._handle_step_continue_issued,
		}
	
	def _start_processor(self):
		"""Start the main thread update processor"""
		self._process_updates()
	
	def _process_updates(self):
		"""Process queued updates in the main thread"""
		try:
			# Process all queued updates
			while not self._update_queue.empty():
				try:
					update_data = self._update_queue.get_nowait()
					self._process_single_update(update_data)
				except queue.Empty:
					break
				except Exception as e:
					print(f"Error processing update: {e}")
		except Exception as e:
			print(f"Error in update processor: {e}")
		finally:
			# Schedule next processing cycle
			self.root.after(50, self._process_updates)  # Process every 50ms
	
	def _process_single_update(self, update_data):
		"""Process a single update safely"""
		if not self._callback_enabled:
			return
			
		status_type = update_data.get('type')
		data = update_data.get('data', {})
		
		# Get handler
		handler = self._status_handlers.get(status_type)
		if handler:
			try:
				handler(data)
			except Exception as e:
				print(f"Error in handler {status_type}: {e}")
				self.ui.log_status(f"Handler error for {status_type}: {e}")
		else:
			self.ui.log_status(f"Unknown status type: {status_type}")
	
	def queue_status_update(self, status_data: Dict[str, Any]):
		"""Queue a status update for main thread processing"""
		try:
			if not self._callback_enabled or self._processing_critical:
				return
				
			# Add timestamp if not present
			if 'timestamp' not in status_data:
				status_data['timestamp'] = datetime.now().isoformat()
			
			self._update_queue.put(status_data)
			
		except Exception as e:
			print(f"Error queuing status update: {e}")
	
	def disable_callbacks_temporarily(self, duration_ms: int = 2000):
		"""Temporarily disable callbacks during critical operations"""
		self._processing_critical = True
		self.root.after(duration_ms, self._re_enable_callbacks)
	
	def _re_enable_callbacks(self):
		"""Re-enable callbacks after critical operation"""
		self._processing_critical = False
	
	def enable_callbacks(self):
		"""Enable callback processing"""
		self._callback_enabled = True
	
	def disable_callbacks(self):
		"""Disable callback processing"""
		self._callback_enabled = False
	
	def clear_queue(self):
		"""Clear all pending updates"""
		while not self._update_queue.empty():
			try:
				self._update_queue.get_nowait()
			except queue.Empty:
				break
	
	# ==================== ALL STATUS HANDLERS ====================
	
	def _handle_experiment_start(self, data):
		"""Handle experiment start status"""
		self.ui.current_experiment_name = data['experiment_name']
		self.ui.total_iterations_in_experiment = data['total_iterations']
		self.ui.current_iteration = 0
		self.ui.current_iteration_progress = 0.0
		
		self.ui.log_status(f"🚀 Started Experiment: {data['experiment_name']}")
		self.ui.log_status(f"📋 Strategy: {data['strategy_type']} with {data['total_iterations']} iterations")
		
		self.ui.update_progress_display(
			experiment_name=data['experiment_name'],
			strategy_type=data['strategy_type'],
			test_name=data['test_name'],
			status="Starting Experiment"
		)
	
	def _handle_iteration_start(self, data):
		"""Handle iteration start"""
		self.ui.current_iteration = data['iteration']
		self.ui.current_iteration_progress = data.get('progress_weight', 0.0)
		
		self.ui.log_status(f"▶️ Starting Iteration {data['iteration']}: {data['status']}")
		self.ui._update_overall_progress()
	
	def _handle_iteration_progress(self, data):
		"""Handle iteration progress updates with enhanced boot detection"""
		self.ui.current_iteration = data['iteration']
		self.ui.current_iteration_progress = data.get('progress_weight', 0.0)
		
		status = data['status']
		
		# Detect and handle different phases
		if self._is_boot_phase(status):
			self._handle_boot_phase_progress(data)
		elif self._is_test_content_phase(status):
			self._handle_test_content_progress(data)
		else:
			# Generic progress handling
			self.ui.log_status(f"⚙️ Iteration {data['iteration']}: {status}")
		
		# Always update progress regardless of phase
		self.ui._update_overall_progress()
		self.ui.update_progress_display(
			experiment_name=data.get('experiment_name', ''),
			strategy_type=data.get('strategy_type', ''),
			test_name=data.get('test_name', ''),
			status=status
		)
	
	def _handle_iteration_complete(self, data):
		"""Handle iteration completion"""
		self.ui.current_iteration = data['iteration']
		self.ui.current_iteration_progress = 1.0
		
		# Log with result details
		status_msg = f"✅ Completed Iteration {data['iteration']}: {data['status']}"
		if data.get('scratchpad'):
			status_msg += f" ({data['scratchpad']})"
		if data.get('seed'):
			status_msg += f" [Seed: {data['seed']}]"
		
		self.ui.log_status(status_msg)
		
		# Update progress and statistics
		self.ui._update_overall_progress()
		self.ui.update_progress_display(result_status=data['status'])
	
	def _handle_iteration_failed(self, data):
		"""Handle iteration failure"""
		self.ui.current_iteration = data['iteration']
		self.ui.current_iteration_progress = 1.0
		
		error_msg = f"❌ FAILED Iteration {data['iteration']}: {data['status']}"
		if data.get('error'):
			error_msg += f" - {data['error']}"
		
		self.ui.log_status(error_msg)
		
		# Update progress bar to show failure
		self.ui._update_overall_progress()
		self.ui.update_progress_display(result_status=data['status'])
		
		# Change progress bar color to indicate failure
		try:
			self.ui.progress_bar.configure(style="Error.Horizontal.TProgressbar")
			# Reset to normal after 2 seconds
			self.root.after(2000, lambda: self.ui.progress_bar.configure(style="Custom.Horizontal.TProgressbar"))
		except:
			pass
	
	def _handle_iteration_cancelled(self, data):
		"""Handle iteration cancellation"""
		self.ui.current_iteration = data['iteration']
		self.ui.current_iteration_progress = 1.0
		
		self.ui.log_status(f"🚫 CANCELLED Iteration {data['iteration']}: {data['status']}")
		
		# Update progress and mark as cancelled
		self.ui._update_overall_progress()
		self.ui.update_progress_display(result_status="CANCELLED")
		
	def _handle_strategy_progress(self, data):
		"""Handle strategy progress updates with enhanced Shmoo support"""
		self.ui.current_iteration = data['current_iteration']
		total_iterations = data['total_iterations']
		progress_percent = data.get('progress_percent', 0)
		
		# Update progress bar safely
		try:
			self.ui.progress_var.set(min(100, max(0, progress_percent)))
			self.ui.progress_percentage_label.configure(text=f"{int(progress_percent)}%")
			
			# Update iteration info
			iteration_text = f"Iter {self.ui.current_iteration}/{total_iterations}"
			self.ui.progress_iteration_label.configure(text=iteration_text)
			
			# Enhanced logging based on strategy type
			strategy_type = data.get('strategy_type', 'Unknown')
			
			if strategy_type == 'Shmoo':
				# Special handling for Shmoo progress
				status_msg = f"📊 Shmoo Progress: {progress_percent:.1f}% - {data['test_name']}"
				if data.get('current_point'):
					status_msg += f" - Point: {data['current_point']}"
				if data.get('x_axis') and data.get('y_axis'):
					status_msg += f" ({data['x_axis']}, {data['y_axis']})"
			elif strategy_type == 'Sweep':
				# Special handling for Sweep progress
				status_msg = f"📊 Sweep Progress: {progress_percent:.1f}% - {data['test_name']}"
				if data.get('current_value'):
					status_msg += f" - {data['current_value']}"
			else:
				# Default handling for Loops and others
				status_msg = f"📊 Progress: {progress_percent:.1f}% - {data['test_name']}"
				if data.get('current_value'):
					status_msg += f" - {data['current_value']}"
				elif data.get('current_point'):
					status_msg += f" - {data['current_point']}"
			
			self.ui.log_status(status_msg)
			
		except Exception as e:
			print(f"Error updating progress: {e}")
			
		except Exception as e:
			print(f"Error updating progress: {e}")
		
	def _handle_strategy_complete(self, data):
		"""Handle strategy completion with enhanced Shmoo summary"""
		self.ui.log_status("=" * 50)
		self.ui.log_status(f"🏁 STRATEGY COMPLETE: {data.get('test_name', 'Unknown Test')}")
		self.ui.log_status("=" * 50)
		
		strategy_type = data.get('strategy_type', 'Unknown Strategy')
		self.ui.log_status(f"📋 Strategy Type: {strategy_type}")
		self.ui.log_status(f"📊 Total Tests: {data.get('total_tests', 0)}")
		self.ui.log_status(f"✅ Success Rate: {data.get('success_rate', 0)}%")
		
		# Shmoo-specific information
		if strategy_type == 'Shmoo':
			if data.get('shmoo_dimensions'):
				self.ui.log_status(f"📐 Shmoo Dimensions: {data['shmoo_dimensions']}")
			if data.get('x_axis_config'):
				x_config = data['x_axis_config']
				self.ui.log_status(f"📈 X-Axis: {x_config.get('Type', 'Unknown')} - {x_config.get('Domain', 'Unknown')}")
			if data.get('y_axis_config'):
				y_config = data['y_axis_config']
				self.ui.log_status(f"📈 Y-Axis: {y_config.get('Type', 'Unknown')} - {y_config.get('Domain', 'Unknown')}")
		
		# Log status breakdown
		if 'status_counts' in data and data['status_counts']:
			self.ui.log_status("📈 Results Summary:")
			for status, count in data['status_counts'].items():
				total_tests = data.get('total_tests', 1)
				percentage = (count / total_tests * 100) if total_tests > 0 else 0
				self.ui.log_status(f"  {status}: {count} ({percentage:.1f}%)")
		
		# Log top failure patterns if any
		if data.get('failure_patterns'):
			self.ui.log_status("🔍 Top Failure Patterns:")
			for pattern, count in list(data['failure_patterns'].items())[:3]:
				self.ui.log_status(f"  {pattern}: {count} occurrences")
		
		self.ui.log_status("=" * 50)
		
		# Reset progress for next experiment
		self.ui.current_experiment_name = None
		self.ui.update_progress_display(
			experiment_name="",
			strategy_type="Strategy Complete",
			test_name=data.get('test_name', ''),
			status="Strategy Complete"
		)
	
	def _handle_experiment_complete(self, data):
		"""Handle overall experiment completion"""
		self.ui.log_status(f"🎉 EXPERIMENT COMPLETED: '{data['test_name']}'")
		
		# Update status display
		self.ui.update_progress_display(
			experiment_name=data.get('experiment_name', ''),
			status="Experiment Complete"
		)
	
	def _handle_experiment_failed(self, data):
		"""Handle experiment failure"""
		self.ui.log_status(f"💥 EXPERIMENT FAILED: '{data['experiment_name']}' - {data['reason']}")
		
		# Update progress bar to show failure
		try:
			self.ui.progress_bar.configure(style="Error.Horizontal.TProgressbar")
		except:
			pass
		
		self.ui.update_progress_display(
			experiment_name=data.get('experiment_name', ''),
			status=f"Failed: {data['reason']}"
		)
	
	# Boot phase detection and handling
	def _is_boot_phase(self, status):
		"""Detect if this is a boot-related status"""
		boot_keywords = [
			'preparing environment', 'starting boot process', 'system boot in progress',
			'boot complete', 'booting', 'initialization', 'hardware init'
		]
		return any(keyword in status.lower() for keyword in boot_keywords)
	
	def _is_test_content_phase(self, status):
		"""Detect if this is test content execution"""
		content_keywords = [
			'running test content', 'test content complete', 'processing results',
			'analyzing results', 'executing', 'dragon', 'linux', 'custom'
		]
		return any(keyword in status.lower() for keyword in content_keywords)
	
	def _handle_boot_phase_progress(self, data):
		"""Handle boot-specific progress with enhanced logging and UI"""
		status = data['status']
		progress_weight = data.get('progress_weight', 0.0)
		iteration = data['iteration']
		
		boot_stage = self._extract_boot_stage(status)
		progress_percent = int(progress_weight * 100)
		
		self.ui.log_status(f"🔄 Boot Progress [{progress_percent}%]: {boot_stage}")
		self._update_boot_visual_feedback(boot_stage, progress_weight)
	
	def _handle_test_content_progress(self, data):
		"""Handle test content execution progress"""
		status = data['status']
		progress_weight = data.get('progress_weight', 0.0)
		iteration = data['iteration']
		
		content_stage = self._extract_content_stage(status)
		progress_percent = int(progress_weight * 100)
		
		self.ui.log_status(f"🧪 Test Content [{progress_percent}%]: {content_stage}")
	
	def _extract_boot_stage(self, status):
		"""Extract meaningful boot stage from status"""
		stage_mapping = {
			'preparing environment': 'Preparing Environment',
			'starting boot process': 'Initializing Boot',
			'system boot in progress': 'System Boot',
			'boot complete': 'Boot Complete'
		}
		
		status_lower = status.lower()
		for key, friendly_name in stage_mapping.items():
			if key in status_lower:
				return friendly_name
		return status
	
	def _extract_content_stage(self, status):
		"""Extract meaningful test content stage from status"""
		stage_mapping = {
			'running test content': 'Executing Tests',
			'test content complete': 'Tests Complete',
			'processing results': 'Processing Results',
			'analyzing results': 'Analyzing Results'
		}
		
		status_lower = status.lower()
		for key, friendly_name in stage_mapping.items():
			if key in status_lower:
				return friendly_name
		return status
	
	def _update_boot_visual_feedback(self, boot_stage, progress_weight):
		"""Update visual feedback during boot phases"""
		try:
			if 'preparing' in boot_stage.lower():
				self.ui.progress_bar.configure(style="Running.Horizontal.TProgressbar")
				self.ui.iteration_status_label.configure(text=f"Status: 🔧 {boot_stage}")
			elif 'initializing' in boot_stage.lower():
				self.ui.progress_bar.configure(style="Running.Horizontal.TProgressbar")
				self.ui.iteration_status_label.configure(text=f"Status: 🔄 {boot_stage}")
			elif 'boot' in boot_stage.lower() and 'complete' not in boot_stage.lower():
				self.ui.progress_bar.configure(style="Custom.Horizontal.TProgressbar")
				self.ui.iteration_status_label.configure(text=f"Status: ⚡ {boot_stage}")
			elif 'complete' in boot_stage.lower():
				self.ui.iteration_status_label.configure(text=f"Status: ✅ {boot_stage}")
		except Exception as e:
			print(f"Error updating boot visual feedback: {e}")
	
	# Step-by-step handlers
	def _handle_step_mode_enabled(self, data):
		"""Handle step-by-step mode enabled"""
		self.ui.log_status("🔄 Step-by-step execution mode enabled")
		try:
			self.ui.strategy_label.configure(text="Mode: Step-by-Step", foreground="orange")
		except:
			pass
	
	def _handle_step_mode_disabled(self, data):
		"""Handle step-by-step mode disabled"""
		self.ui.log_status("▶️ Step-by-step mode disabled - continuous execution")
		try:
			self.ui.strategy_label.configure(foreground="black")
		except:
			pass
	
	def _handle_step_iteration_complete(self, data):
		"""Handle step iteration completion (waiting for command)"""
		iteration = data['current_iteration']
		total = data['total_iterations']
		stats = data.get('current_stats', {})
		
		self.ui.log_status(f"⏸️ STEP MODE: Iteration {iteration}/{total} COMPLETE")
		self.ui.log_status(f"📊 Current Stats - Pass: {stats.get('pass_count', 0)}, Fail: {stats.get('fail_count', 0)}")
		self.ui.log_status("⏳ Waiting for command...")
		
		self.ui.update_progress_display(status="Step: Waiting for Command")
		
		try:
			self.ui.progress_bar.configure(style="Warning.Horizontal.TProgressbar")
		except:
			pass
	
	def _handle_step_continue_issued(self, data):
		"""Handle step continue command issued"""
		iteration = data['current_iteration']
		total = data['total_iterations']
		
		self.ui.log_status(f"▶️ CONTINUE command - proceeding to iteration {iteration + 1}/{total}")
		self.ui.update_progress_display(status="Step: Continuing")
		
		try:
			self.ui.progress_bar.configure(style="Custom.Horizontal.TProgressbar")
		except:
			pass
	
	# Control handlers
	def _handle_execution_halted(self, data):
		"""Handle execution halted"""
		test_name = data.get('test_name', 'Unknown')
		iteration = data.get('current_iteration', 0)
		
		self.ui.log_status(f"⏸️ Execution HALTED at iteration {iteration} of {test_name}")
		self.ui.update_progress_display(status="HALTED - Waiting for Continue")
		
		try:
			self.ui.hold_button.configure(text="Continue", style="Continue.TButton")
		except:
			pass
	
	def _handle_execution_resumed(self, data):
		"""Handle execution resumed"""
		test_name = data.get('test_name', 'Unknown')
		iteration = data.get('current_iteration', 0)
		
		self.ui.log_status(f"▶️ Execution RESUMED at iteration {iteration} of {test_name}")
		self.ui.update_progress_display(status="Resumed")
		
		try:
			self.ui.hold_button.configure(text="Hold", style="Hold.TButton")
		except:
			pass
	
	def _handle_experiment_ended_by_command(self, data):
		"""Handle experiment ended by END command"""
		completed = data['completed_iterations']
		total = data['total_iterations']
		reason = data['reason']
		
		self.ui.log_status(f"🛑 Experiment ended by {reason} after {completed}/{total} iterations")
	
	def _handle_execution_cancelled(self, data):
		"""Handle execution cancellation"""
		self.ui.log_status("🚫 Execution cancelled by user")