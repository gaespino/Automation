# Create EnhancedThreadSafeState.py

import threading
import time
from datetime import datetime
from enum import Enum, auto
from typing import List, Dict, Any, Optional, Set, Callable
from dataclasses import dataclass, field

''' Framework Threads Handler -- rev 1.7'''

debug_enabled = False

class ExecutionCommand(Enum):
	"""Enumeration of all possible execution commands"""
	# Core execution commands
	CANCEL = auto()
	END_EXPERIMENT = auto()
	PAUSE = auto()
	RESUME = auto()
	
	# Step-by-step commands
	STEP_CONTINUE = auto()
	ENABLE_STEP_MODE = auto()
	DISABLE_STEP_MODE = auto()
	
	# Advanced commands
	SKIP_CURRENT_TEST = auto()
	RETRY_CURRENT_TEST = auto()
	CHANGE_LOG_LEVEL = auto()
	EMERGENCY_STOP = auto()
	
	# Status commands
	REQUEST_STATUS = auto()
	HEARTBEAT = auto()

@dataclass
class CommandData:
	"""Data structure for command with metadata"""
	command: ExecutionCommand
	timestamp: float = field(default_factory=time.time)
	data: Optional[Dict[str, Any]] = None
	processed: bool = False
	response: Optional[Any] = None  # For command responses
	acknowledged: bool = False  # NEW: Track if acknowledged
	processing_started: bool = False  # NEW: Track if processing started

	def __post_init__(self):
		if self.data is None:
			self.data = {}

class EnhancedThreadSafeState:
	"""Enhanced thread-safe state manager with command system"""
	
	def __init__(self):
		self._lock = threading.RLock()
		self.debug_enabled = debug_enabled
		# Core execution state
		self._state: Dict[str, Any] = {
			'execution_active': False,
			'current_experiment': None,
			'current_iteration': 0,
			'total_iterations': 0,
			'step_mode_enabled': False,
			'log_level': 'INFO',
			'waiting_for_step': False,
			'framework_ready': True
		}
		
		# Command tracking
		self._active_commands: Set[ExecutionCommand] = set()
		self._command_history: list[CommandData] = []
		self._max_history = 100
		
		# Command data storage
		self._command_data: Dict[ExecutionCommand, Any] = {}
		
		# Status tracking
		self._last_heartbeat = time.time()
		
		# Command response callbacks
		self._response_callbacks: Dict[ExecutionCommand, Callable] = {}

		# DEBUG: Command lifecycle tracking
		self._command_lifecycle: Dict[ExecutionCommand, Dict[str, float]] = {}

	# ==================== DEBUG MANAGEMENT ====================

	def _debug_log(self, message: str, level: str = "INFO"):
		"""Debug logging with thread info"""
		if self.debug_enabled:
			try:
				thread_name = threading.current_thread().name
				timestamp = time.strftime("%H:%M:%S")
				print(f"[{timestamp}][{thread_name}][{level}] THREAD_HANDLER: {message}")
			except Exception as e:
				print(f'Error with debug:{e}')

	def _debug_breakpoint(self, breakpoint_name: str, command: ExecutionCommand = None, extra_data: Dict = None):
		"""Debug breakpoint with detailed state information"""
		if not self.debug_enabled:
			return

		try:    
			thread_name = threading.current_thread().name
			timestamp = time.strftime("%H:%M:%S")
			
			print(f"\n{'='*60}")
			print(f" DEBUG BREAKPOINT: {breakpoint_name}")
			print(f" Time: {timestamp}")
			print(f" Thread: {thread_name}")
			
			if command:
				print(f" Command: {command.name}")
				
				# Command lifecycle info
				if command in self._command_lifecycle:
					lifecycle = self._command_lifecycle[command]
					print(f" Command Lifecycle:")
					for event, event_time in lifecycle.items():
						event_timestamp = time.strftime("%H:%M:%S")
						print(f"   {event}: {event_timestamp}")
			
			with self._lock:
				print(f" Active Commands: {[cmd.name for cmd in self._active_commands]}")
				print(f" Execution Active: {self._state.get('execution_active', False)}")
				print(f" Current Experiment: {self._state.get('current_experiment', 'None')}")
				print(f" Current Iteration: {self._state.get('current_iteration', 0)}")
				
				# Recent command history
				recent_commands = self._command_history[-3:] if self._command_history else []
				print(f" Recent Commands:")
				for cmd_data in recent_commands:
					status = " Acked" if cmd_data.acknowledged else (" Processing" if cmd_data.processing_started else " Pending")
					print(f"   {cmd_data.command.name}: {status}")
			
			if extra_data:
				print(f" Extra Data: {extra_data}")
				
			print(f"{'='*60}\n")
		except Exception as e:
			print(f'Error with debug:{e}')

	# ==================== INIT MANAGEMENT ====================

	def prepare_for_execution(self) -> bool:
		"""Prepare state for new execution"""
		self._debug_breakpoint("PREPARE_FOR_EXECUTION_START")
		try:
			with self._lock:
				# Clear all commands except persistent ones
				#persistent_commands = {ExecutionCommand.ENABLE_STEP_MODE, ExecutionCommand.DISABLE_STEP_MODE}
				#commands_to_clear = self._active_commands - persistent_commands
				self._debug_log(f"Before clearing - Active commands: {[cmd.name for cmd in self._active_commands]}")
				self._debug_log(f"Before clearing - Command data keys: {list(self._command_data.keys())}")

				commands_to_clear = self._active_commands.copy()
				self._debug_log(f"Clearing {len(commands_to_clear)} commands: {[cmd.name for cmd in commands_to_clear]}")
				
				#for cmd in commands_to_clear:
				#    self._active_commands.discard(cmd)
				#    self._command_data.pop(cmd, None)

				# Clear commands but preserve execution state if already set
				preserve_execution_state = self._state.get('execution_active', False)
				current_experiment = self._state.get('current_experiment')
				total_iterations = self._state.get('total_iterations', 0)
				
				# Clear active commands completely
				self._active_commands.clear()
				
				# Clear all command data
				self._command_data.clear()
				
				# Clear response callbacks
				self._response_callbacks.clear()
				
				# Mark all unprocessed commands in history as processed/cancelled
				for cmd_data in self._command_history:
					if not cmd_data.processed:
						cmd_data.processed = True
						cmd_data.response = "Cleared during preparation"
						cmd_data.acknowledged = True

				# [ DONE ] Only reset execution state if not already active
				if not preserve_execution_state:
					self._state.update({
						'execution_active': False,
						'current_experiment': None,
						'current_iteration': 0,
						'total_iterations': 0,
						'waiting_for_step': False,
						'framework_ready': True
					})
				else:
					# Preserve active execution state
					self._state.update({
						'execution_active': True,
						'current_experiment': current_experiment,
						'total_iterations': total_iterations,
						'waiting_for_step': False,
						'framework_ready': True
					})
				
				# Update heartbeat
				self._last_heartbeat = time.time()
				self._debug_breakpoint("PREPARE_FOR_EXECUTION_COMPLETE")
				return True
				
		except Exception as e:
			print(f"Error preparing for execution: {e}")
			return False
	
	def finalize_execution(self, reason: str = "completed"):
		"""Finalize execution and cleanup"""
		try:
			with self._lock:
				# Mark as inactive
				self._state['execution_active'] = False
				self._state['framework_ready'] = True
				
				# Clear execution-specific commands
				execution_commands = {
					ExecutionCommand.CANCEL,
					ExecutionCommand.END_EXPERIMENT,
					ExecutionCommand.PAUSE,
					ExecutionCommand.RESUME,
					ExecutionCommand.STEP_CONTINUE,
					ExecutionCommand.EMERGENCY_STOP
				}
				
				for cmd in execution_commands:
					self._active_commands.discard(cmd)
					self._command_data.pop(cmd, None)
				
				# Add finalization to history
				self._command_history.append(CommandData(
					command=ExecutionCommand.REQUEST_STATUS,  # Use as generic status command
					data={"action": "finalize", "reason": reason},
					processed=True
				))
				
				self._trim_history()
				
		except Exception as e:
			print(f"Error finalizing execution: {e}")
	
	def is_ready_for_execution(self) -> bool:
		"""Check if state is ready for new execution"""
		with self._lock:
			return (self._state.get('framework_ready', True) and 
					not self._state.get('execution_active', False) and
					not self.has_command(ExecutionCommand.EMERGENCY_STOP))

	# ==================== COMMAND MANAGEMENT ====================
	
	def issue_command(self, command: ExecutionCommand, data: Optional[Dict[str, Any]] = None, 
					 callback: Optional[Callable] = None) -> bool:
		"""Issue a command (called from main thread)"""
		
		self._debug_breakpoint("COMMAND_ISSUE_START", command, {"data": data})
		try:
			with self._lock:
				# Initialize command lifecycle tracking
				self._command_lifecycle[command] = {
					'issued': time.time()
				}

				# Prevent duplicate commands for certain types
				if command in [ExecutionCommand.CANCEL, ExecutionCommand.END_EXPERIMENT, ExecutionCommand.EMERGENCY_STOP]:
					if command in self._active_commands:
						return True  # Already active
				
				command_data = CommandData(command=command, data=data or {})
				
				# Add to active commands
				self._active_commands.add(command)
				
				# Store command data if provided
				if data:
					self._command_data[command] = data
				
				# Store callback if provided
				if callback:
					self._response_callbacks[command] = callback
				
				# Add to history
				self._command_history.append(command_data)
				self._trim_history()
				
				# Handle immediate state changes for certain commands
				self._process_immediate_commands(command, data or {})

				self._debug_breakpoint("COMMAND_ISSUE_COMPLETE", command, {
					"active_commands_count": len(self._active_commands),
					"command_in_active": command in self._active_commands
				})

				return True
				
		except Exception as e:
			print(f"Error issuing command {command}: {e}")
			return False

	def has_command(self, command: ExecutionCommand) -> bool:
		"""Check if a specific command is active"""
		with self._lock:
			has_cmd = command in self._active_commands
			
			# Find command data for more info
			cmd_data = None
			for cmd in reversed(self._command_history):
				if cmd.command == command:
					cmd_data = cmd
					break
			
			self._debug_log(f"Command check {command.name}: {'ACTIVE' if has_cmd else 'INACTIVE'}" + 
						  (f" (Acked: {cmd_data.acknowledged}, Processing: {cmd_data.processing_started})" if cmd_data else ""))
			
			return has_cmd

	def start_processing_command(self, command: ExecutionCommand) -> bool:
		"""Mark command as processing started (called when background thread starts handling it)"""
		self._debug_breakpoint("COMMAND_PROCESSING_START", command)
		
		try:
			with self._lock:
				if command not in self._active_commands:
					self._debug_log(f"Cannot start processing {command.name} - not in active commands", "ERROR")
					return False
				
				# Update lifecycle
				if command in self._command_lifecycle:
					self._command_lifecycle[command]['processing_started'] = time.time()
				
				# Mark in history
				for cmd_data in reversed(self._command_history):
					if cmd_data.command == command and not cmd_data.processing_started:
						cmd_data.processing_started = True
						break
				
				self._debug_log(f"Started processing command {command.name}")
				return True
				
		except Exception as e:
			self._debug_log(f"Error starting processing for {command}: {e}", "ERROR")
			return False

	def get_active_commands(self) -> Set[ExecutionCommand]:
		"""Get all active commands"""
		
		with self._lock:
			return self._active_commands.copy()
	
	def acknowledge_command(self, command: ExecutionCommand, response: Any = None) -> bool:
		"""Acknowledge that a command has been processed (called from background thread)"""

		self._debug_breakpoint("COMMAND_ACKNOWLEDGE_START", command, {"response": response})
		
		try:
			with self._lock:

				if command not in self._active_commands:
					self._debug_log(f"Cannot acknowledge {command.name} - not in active commands", "WARN")
					return False
				
				if command in self._command_lifecycle:
					self._command_lifecycle[command]['acknowledged'] = time.time()
				
				self._active_commands.remove(command)
					
				# Mark as processed in history
				for cmd_data in reversed(self._command_history):
					if cmd_data.command == command and not cmd_data.processed:
						cmd_data.processed = True
						cmd_data.response = response
						break
					
				# Execute callback if exists
				callback = self._response_callbacks.pop(command, None)
				if callback:
					try:
						callback(response)
					except Exception as e:
						print(f"Callback error for {command}: {e}")
					
				# Clean up command data
				self._command_data.pop(command, None)
					
				return True
			
				
		except Exception as e:
			self._debug_log(f"Error acknowledging command {command}: {e}", "ERROR")
			print(f"Error acknowledging command {command}: {e}")
			return False
	
	def get_command_data(self, command: ExecutionCommand) -> Optional[Dict[str, Any]]:
		"""Get data associated with a command"""
		with self._lock:
			return self._command_data.get(command, {}).copy()
	
	def clear_all_commands(self):
		"""Clear all active commands"""
		with self._lock:
			self._active_commands.clear()
			self._command_data.clear()
	
	# ==================== CONVENIENCE COMMAND METHODS ====================
	
	def cancel(self, reason: str = "User requested", callback: Optional[Callable] = None) -> bool:
		"""Issue cancel command"""
		#return self.issue_command(ExecutionCommand.CANCEL, {"reason": reason}, callback)
		"""Issue cancel command with debug"""
		self._debug_log(f"Issuing CANCEL command: {reason}")
		return self.issue_command(ExecutionCommand.CANCEL, {"reason": reason}, callback)
		
	def end_experiment(self, reason: str = "User requested", callback: Optional[Callable] = None) -> bool:
		"""Issue end experiment command"""
		#return self.issue_command(ExecutionCommand.END_EXPERIMENT, {"reason": reason}, callback)
		"""Issue end experiment command with debug"""
		self._debug_log(f"Issuing END_EXPERIMENT command: {reason}")
		return self.issue_command(ExecutionCommand.END_EXPERIMENT, {"reason": reason}, callback)

	def pause(self, reason: str = "User requested", callback: Optional[Callable] = None) -> bool:
		"""Issue pause command"""
		return self.issue_command(ExecutionCommand.PAUSE, {"reason": reason}, callback)
	
	def resume(self, reason: str = "User requested", callback: Optional[Callable] = None) -> bool:
		"""Issue resume command"""
		return self.issue_command(ExecutionCommand.RESUME, {"reason": reason}, callback)
	
	def step_continue(self, callback: Optional[Callable] = None) -> bool:

		self._debug_log(f"Step continue requested")
		
		# Get current state for debugging
		with self._lock:
			exec_active = self._state.get('execution_active', False)
			step_mode = self._state.get('step_mode_enabled', False)
			waiting = self._state.get('waiting_for_step', False)
			
			self._debug_log(f"Step continue requested:")
			self._debug_log(f"  execution_active: {exec_active}")
			self._debug_log(f"  step_mode_enabled: {step_mode}")
			self._debug_log(f"  waiting_for_step: {waiting}")			
			self._debug_log(f"State check - Active: {exec_active}, Step Mode: {step_mode}, Waiting: {waiting}")
		
	  	# [ DONE ] Validate state before issuing command
		if not self._state.get('execution_active', False):
			print("WARNING: Attempting step continue when execution not active")
			#return False
		
		if not self._state.get('step_mode_enabled', False):
			print("WARNING: Attempting step continue when step mode not enabled")
			#return False
		
		if not self._state.get('waiting_for_step', False):
			print("WARNING: Attempting step continue when not waiting for step")
			#return False

		# [ DONE ] ALWAYS issue the command (no validation)
		self._debug_log(f"Issuing STEP_CONTINUE command (validation DISABLED)")
		success = self.issue_command(ExecutionCommand.STEP_CONTINUE, {}, callback)
		
		if success:
			self._debug_log(f"STEP_CONTINUE command issued successfully")
		else:
			self._debug_log(f"STEP_CONTINUE command FAILED to issue")
					
		"""Issue step continue command"""
		return success#self.issue_command(ExecutionCommand.STEP_CONTINUE, {}, callback)
	
	def enable_step_mode(self) -> bool:
		"""Enable step-by-step mode"""
		return self.issue_command(ExecutionCommand.ENABLE_STEP_MODE)
	
	def disable_step_mode(self) -> bool:
		"""Disable step-by-step mode"""
		return self.issue_command(ExecutionCommand.DISABLE_STEP_MODE)
	
	def emergency_stop(self, reason: str = "Emergency stop requested") -> bool:
		"""Issue emergency stop command"""
		return self.issue_command(ExecutionCommand.EMERGENCY_STOP, {"reason": reason})
	
	def skip_current_test(self, reason: str = "User requested skip") -> bool:
		"""Skip current test"""
		return self.issue_command(ExecutionCommand.SKIP_CURRENT_TEST, {"reason": reason})
	
	def change_log_level(self, level: str) -> bool:
		"""Change logging level"""
		return self.issue_command(ExecutionCommand.CHANGE_LOG_LEVEL, {"level": level})
	
	# ==================== STATE CHECKING METHODS ====================
	
	def is_cancelled(self) -> bool:
		"""Check if cancellation was requested"""
		#return self.has_command(ExecutionCommand.CANCEL) or self.has_command(ExecutionCommand.EMERGENCY_STOP)
		"""Check if cancellation was requested with debug info"""
		with self._lock:
			cancel_active = ExecutionCommand.CANCEL in self._active_commands
			emergency_active = ExecutionCommand.EMERGENCY_STOP in self._active_commands
			result = cancel_active or emergency_active
			
			if result:
				self._debug_log(f"Cancellation check: TRUE (Cancel: {cancel_active}, Emergency: {emergency_active})")
			
			return result
		   
	def is_ended(self) -> bool:
		"""Check if end was requested"""
		#return self.has_command(ExecutionCommand.END_EXPERIMENT)
		"""Check if end was requested with debug info"""
		with self._lock:
			result = ExecutionCommand.END_EXPERIMENT in self._active_commands
			
			if result:
				self._debug_log(f"End check: TRUE")
			
			return result
		   
	def is_paused(self) -> bool:
		"""Check if pause was requested"""
		#return self.has_command(ExecutionCommand.PAUSE) and not self.has_command(ExecutionCommand.RESUME)
		"""Check if pause was requested with debug info"""
		with self._lock:
			pause_active = ExecutionCommand.PAUSE in self._active_commands
			resume_active = ExecutionCommand.RESUME in self._active_commands
			result = pause_active and not resume_active
			
			if pause_active or resume_active:
				self._debug_log(f"Pause check: {result} (Pause: {pause_active}, Resume: {resume_active})")
			
			return result
		   
	def should_stop(self) -> bool:
		"""Check if execution should stop completely"""
		#return (self.has_command(ExecutionCommand.CANCEL) or 
		#        self.has_command(ExecutionCommand.END_EXPERIMENT) or
		#        self.has_command(ExecutionCommand.EMERGENCY_STOP))
		"""Check if execution should stop completely with debug info"""
		with self._lock:
			cancel = ExecutionCommand.CANCEL in self._active_commands
			end = ExecutionCommand.END_EXPERIMENT in self._active_commands
			emergency = ExecutionCommand.EMERGENCY_STOP in self._active_commands
			result = cancel or end or emergency
			
			if result:
				self._debug_log(f"Should stop: TRUE (Cancel: {cancel}, End: {end}, Emergency: {emergency})")
				self._debug_log(f"Active commands: {[cmd.name for cmd in self._active_commands]}")
			return result
			
	def should_step_continue(self) -> bool:
		"""Check if step continue was requested"""
		return self.has_command(ExecutionCommand.STEP_CONTINUE)
	
	def is_step_mode_enabled(self) -> bool:
		"""Check if step mode is enabled"""
		with self._lock:
			return self._state.get('step_mode_enabled', False)
	
	# ==================== STATE MANAGEMENT ====================
	
	def set_state(self, key: str, value: Any):
		"""Set a state value"""
		with self._lock:
			old_value = self._state.get(key)
			
			if key == 'execution_active':
				import traceback
				thread_name = threading.current_thread().name
				timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
				
				if old_value != value:
					self._debug_log(f"[ FIRE ] EXECUTION_ACTIVE CHANGE: {old_value} -> {value} (Thread: {thread_name}) at {timestamp}")
					
					# Print detailed stack trace
					stack = traceback.format_stack()
					self._debug_log("Stack trace for execution_active change:")
					for i, line in enumerate(stack[-8:]):  # Show more frames
						self._debug_log(f"  [{i}] {line.strip()}")
					
					if value == False:
						self._debug_log("[ DEBUG ]  CRITICAL: execution_active set to FALSE - this will break step mode!")
				else:
					# Even if value is the same, log it for debugging
					self._debug_log(f"execution_active set to same value: {value} (Thread: {thread_name})")
			
									
			self._state[key] = value
	
	def get_state(self, key: str, default: Any = None) -> Any:
		"""Get a state value"""
		with self._lock:
			return self._state.get(key, default)
	
	def update_state(self, **kwargs):
		"""Update multiple state values with race condition debugging"""
		with self._lock:
			if 'execution_active' in kwargs:
				old_value = self._state.get('execution_active')
				new_value = kwargs['execution_active']
				
				import traceback
				import datetime
				thread_name = threading.current_thread().name
				timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
				
				self._debug_log(f"[ FIRE ] EXECUTION_ACTIVE UPDATE START: {old_value} -> {new_value} (Thread: {thread_name}) at {timestamp}")
				
				# [ DONE ] Actually update the state
				self._state.update(kwargs)
				
				# [ DONE ] Immediately verify the update worked
				actual_value = self._state.get('execution_active')
				if actual_value != new_value:
					self._debug_log(f"[ CHECK ] CRITICAL BUG: State update failed! Expected {new_value}, got {actual_value}")
				else:
					self._debug_log(f"[ DONE ] State update successful: execution_active = {actual_value}")
				
				if old_value != new_value:
					stack = traceback.format_stack()
					self._debug_log("Stack trace for execution_active update:")
					for i, line in enumerate(stack[-6:]):
						self._debug_log(f"  [{i}] {line.strip()}")
					
					if new_value == False:
						self._debug_log("[ DEBUG ]  CRITICAL: execution_active updated to FALSE!")
			else:
				# [ DONE ] Normal update for non-execution_active keys
				self._state.update(kwargs)

	def get_full_state(self) -> Dict[str, Any]:
		"""Get complete state snapshot"""
		with self._lock:
			return {
				'state': self._state.copy(),
				'active_commands': list(self._active_commands),
				'last_heartbeat': self._last_heartbeat,
				'command_count': len(self._command_history)
			}
	
	def reset(self):
		"""Reset all state and commands"""
		with self._lock:
			self._state = {
				'execution_active': False,
				'current_experiment': None,
				'current_iteration': 0,
				'total_iterations': 0,
				'step_mode_enabled': False,
				'log_level': 'INFO'
			}
			self._active_commands.clear()
			self._command_data.clear()
			self._command_history.clear()
			self._last_heartbeat = time.time()
	
	# ==================== INTERNAL METHODS ====================
	
	def _process_immediate_commands(self, command: ExecutionCommand, data: Dict[str, Any]):
		"""Process commands that need immediate state changes"""
		if command == ExecutionCommand.ENABLE_STEP_MODE:
			self._state['step_mode_enabled'] = True
		elif command == ExecutionCommand.DISABLE_STEP_MODE:
			self._state['step_mode_enabled'] = False
		elif command == ExecutionCommand.CHANGE_LOG_LEVEL:
			self._state['log_level'] = data.get('level', 'INFO')
		elif command == ExecutionCommand.RESUME:
			# Remove pause command when resume is issued
			self._active_commands.discard(ExecutionCommand.PAUSE)
	
	def _trim_history(self):
		"""Keep command history within limits"""
		if len(self._command_history) > self._max_history:
			self._command_history = self._command_history[-self._max_history:]
	
	def heartbeat(self):
		"""Update heartbeat timestamp"""
		with self._lock:
			self._last_heartbeat = time.time()
	
	def get_command_history(self, limit: int = 10) -> List[CommandData]:
		"""Get recent command history"""
		with self._lock:
			return self._command_history[-limit:].copy()
	
	# ==================== DEBUG AND ANALYSIS METHODS ====================
	
	def get_command_lifecycle_info(self, command: ExecutionCommand) -> Dict[str, Any]:
		"""Get detailed lifecycle information for a command"""
		with self._lock:
			if command not in self._command_lifecycle:
				return {}
			
			lifecycle = self._command_lifecycle[command].copy()
			
			# Calculate durations
			if 'issued' in lifecycle and 'processing_started' in lifecycle:
				lifecycle['time_to_processing'] = lifecycle['processing_started'] - lifecycle['issued']
			
			if 'processing_started' in lifecycle and 'acknowledged' in lifecycle:
				lifecycle['processing_duration'] = lifecycle['acknowledged'] - lifecycle['processing_started']
			
			if 'issued' in lifecycle and 'acknowledged' in lifecycle:
				lifecycle['total_duration'] = lifecycle['acknowledged'] - lifecycle['issued']
			
			return lifecycle

	def debug_command_flow(self, command: ExecutionCommand):
		"""Print detailed command flow analysis"""
		if not self.debug_enabled:
			return
			
		print(f"\n COMMAND FLOW ANALYSIS: {command.name}")
		print("="*50)
		
		lifecycle = self.get_command_lifecycle_info(command)
		if lifecycle:
			print(" Lifecycle Events:")
			for event, timestamp in lifecycle.items():
				if isinstance(timestamp, float):
					formatted_time = time.strftime("%H:%M:%S")
					print(f"   {event}: {formatted_time}")
				else:
					print(f"   {event}: {timestamp}")
		
		# Find command in history
		with self._lock:
			cmd_data = None
			for cmd in reversed(self._command_history):
				if cmd.command == command:
					cmd_data = cmd
					break
			
			if cmd_data:
				print(f" Command Status:")
				print(f"   Processing Started: {cmd_data.processing_started}")
				print(f"   Processed: {cmd_data.processed}")
				print(f"   Acknowledged: {cmd_data.acknowledged}")
				print(f"   Response: {cmd_data.response}")
			
			print(f" Currently Active: {command in self._active_commands}")
		
		print("="*50)

	def enable_debug(self):
		"""Enable debug logging"""
		self.debug_enabled = True
		self._debug_log("Debug logging enabled")

	def disable_debug(self):
		"""Disable debug logging"""
		self._debug_log("Debug logging disabled")
		self.debug_enabled = False

	# ==================== DEBUGGING METHODS ====================
	
	def debug_info(self) -> str:
		"""Get debug information"""
		with self._lock:
			active_cmds = [cmd.name for cmd in self._active_commands]
			recent_cmds = [f"{cmd.command.name}({cmd.processed})" for cmd in self._command_history[-5:]]
			
			return f"""
=== Enhanced Thread Safe State Debug ===
Active Commands: {active_cmds}
Recent Commands: {recent_cmds}
Current State: {self._state}
Last Heartbeat: {time.time() - self._last_heartbeat:.1f}s ago
==========================================
"""


# Global instance
execution_state = EnhancedThreadSafeState()