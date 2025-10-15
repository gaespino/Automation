from enum import Enum
from dataclasses import dataclass
import queue
import threading
import sys
import os
from typing import Dict, Any, Callable, Optional, List
import tkinter as tk

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(parent_dir)
sys.path.append(parent_dir)

from Interfaces.IFramework import IStatusReporter, IUIController, StatusType

debug = True

class ExecutionState(Enum):
	IDLE = "idle"
	EXPERIMENT_RUNNING = "experiment_running"
	ITERATION_RUNNING = "iteration_running"
	BOOT_PHASE = "boot_phase"
	TEST_PHASE = "test_phase"
	HALTED = "halted"
	STEP_WAITING = "step_waiting"
	COMPLETED = "completed"
	FAILED = "failed"
	CANCELLED = "cancelled"

@dataclass
class ExecutionEvent:
	type: str
	data: Dict[str, Any]
	timestamp: str

class ExecutionStateMachine:
	"""Complete state machine with all handlers"""
	
	def __init__(self, ui_updater: Callable[[Dict[str, Any]], None]):
		self.current_state = ExecutionState.IDLE
		self.ui_updater = ui_updater
		
		# Complete handler registry - ALL original handlers
		self.handlers = {
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
			'execution_ended': self._handle_execution_ended,	

			# Control command handlers
			'experiment_ended_by_command': self._handle_experiment_ended_by_command,
			'execution_setup': self._handle_execution_setup,
			'execution_halted': self._handle_execution_halted,
			'execution_resumed': self._handle_execution_resumed,
			'execution_cancelled': self._handle_execution_cancelled,
			'execution_finalized': self._handle_execution_finalized,
			'execution_prepared': self._handle_execution_prepared,
			
			# Step-by-step mode handlers
			'step_mode_enabled': self._handle_step_mode_enabled,
			'step_mode_disabled': self._handle_step_mode_disabled,
			'step_iteration_complete': self._handle_step_iteration_complete,
			'step_continue_issued': self._handle_step_continue_issued,

			# Waiting Handlers
			'step_waiting': self._handle_step_waiting,
			'halt_waiting': self._handle_halt_waiting,			

			# Additional handlers for completeness
			'all_experiments_complete': self._handle_all_complete,

			# ADD these handlers for ControlPanel
			'experiment_status_update': self._handle_experiment_status_update,
			'experiment_index_update': self._handle_experiment_index_update,
			'all_experiments_complete': self._handle_all_experiments_complete,
		}
	
	def process_event(self, event: ExecutionEvent):
		"""Process event and return UI updates"""
		handler = self.handlers.get(event.type)
		if handler:
			try:
				ui_updates = handler(event.data)
				if ui_updates:
					self.ui_updater(ui_updates)
			except Exception as e:
				print(f"Handler error for {event.type}: {e}")
		else:
			print(f"Unknown event type: {event.type}")
	
	# ==================== CORE EXECUTION HANDLERS ====================
	
	def _handle_experiment_start(self, data) -> Dict[str, Any]:
		"""Handle experiment start status"""
		self.current_state = ExecutionState.EXPERIMENT_RUNNING
		return {
			'log_message': f"[START] Started Experiment: {data['experiment_name']}",
			'log_message_2': f"[INFO] Strategy: {data['strategy_type']} with {data['total_iterations']} iterations",
			'status_label': {'text': ' Running ', 'bg': '#BF0000', 'fg': 'white'},
			#'progress_reset': True, # ADD if we want to reset every run
			'experiment_info': {
				'name': data['experiment_name'],
				'strategy': data['strategy_type'],
				'test_name': data['test_name'],
				'total_iterations': data['total_iterations']
			}
		}
	
	def _handle_iteration_start(self, data) -> Dict[str, Any]:
		"""Handle iteration start"""
		self.current_state = ExecutionState.ITERATION_RUNNING
		return {
			'log_message': f"[RUN] Starting Iteration {data['iteration']}: {data['status']}",
			'iteration_info': {
				'current': data['iteration'],
				'progress_weight': data.get('progress_weight', 0.0)
			},
			'update_progress': True
		}
	
	def _handle_iteration_progress(self, data) -> Dict[str, Any]:
		"""Handle iteration progress updates with enhanced boot detection"""
		status = data['status']
		
		# Detect phase and set appropriate state
		if self._is_boot_phase(status):
			self.current_state = ExecutionState.BOOT_PHASE
			return self._handle_boot_phase_progress(data)
		elif self._is_test_content_phase(status):
			self.current_state = ExecutionState.TEST_PHASE
			return self._handle_test_content_progress(data)
		else:
			# Generic progress handling
			return {
				'log_message': f"[PROGRESS] Iteration {data['iteration']}: {status}",
				'iteration_info': {
					'current': data['iteration'],
					'progress_weight': data.get('progress_weight', 0.0)
				},
				'update_progress': True,
				'status_update': status
			}
	
	def _handle_iteration_complete(self, data) -> Dict[str, Any]:
		"""Handle iteration completion"""
		self.current_state = ExecutionState.EXPERIMENT_RUNNING
		
		# Build status message with details
		status_msg = f"[DONE] Completed Iteration {data['iteration']}: {data['status']}"
		if data.get('scratchpad'):
			status_msg += f" ({data['scratchpad']})"
		if data.get('seed'):
			status_msg += f" [Seed: {data['seed']}]"
		
		return {
			'log_message': status_msg,
			'iteration_info': {
				'current': data['iteration'],
				'progress_weight': 1.0
			},
			'update_progress': True,
			'result_status': data['status'],
			'iteration_complete': True
		}
	
	def _handle_iteration_failed(self, data) -> Dict[str, Any]:
		"""Handle iteration failure"""
		error_msg = f"[FAIL] FAILED Iteration {data['iteration']}: {data['status']}"
		if data.get('error'):
			error_msg += f" - {data['error']}"
		
		return {
			'log_message': error_msg,
			'iteration_info': {
				'current': data['iteration'],
				'progress_weight': 1.0
			},
			'update_progress': True,
			'result_status': data['status'],
			'progress_bar_style': "Error.Horizontal.TProgressbar",
			'reset_progress_bar_after': 2000  # Reset after 2 seconds
		}
	
	def _handle_iteration_cancelled(self, data) -> Dict[str, Any]:
		"""Handle iteration cancellation"""
		self.current_state = ExecutionState.CANCELLED
		return {
			'log_message': f"[CANCEL] CANCELLED Iteration {data['iteration']}: {data['status']}",
			'iteration_info': {
				'current': data['iteration'],
				'progress_weight': 1.0
			},
			'update_progress': True,
			'result_status': "CANCELLED"
		}
	
	def _handle_strategy_progress(self, data) -> Dict[str, Any]:
		"""Handle strategy progress updates with enhanced Shmoo support"""
		progress_percent = data.get('progress_percent', 0)
		strategy_type = data.get('strategy_type', 'Unknown')
		
		# Build status message based on strategy type
		if strategy_type == 'Shmoo':
			status_msg = f"[SHMOO] Progress: {progress_percent:.1f}% - {data['test_name']}"
			if data.get('current_point'):
				status_msg += f" - Point: {data['current_point']}"
			if data.get('x_axis') and data.get('y_axis'):
				status_msg += f" ({data['x_axis']}, {data['y_axis']})"
		elif strategy_type == 'Sweep':
			status_msg = f"[SWEEP] Progress: {progress_percent:.1f}% - {data['test_name']}"
			if data.get('current_value'):
				status_msg += f" - {data['current_value']}"
		else:
			status_msg = f"[LOOPS] Progress: {progress_percent:.1f}% - {data['test_name']}"
			if data.get('current_value'):
				status_msg += f" - {data['current_value']}"
			elif data.get('current_point'):
				status_msg += f" - {data['current_point']}"
		
		return {
			'log_message': status_msg,
			'strategy_progress': {
				'current_iteration': data['current_iteration'],
				'total_iterations': data['total_iterations'],
				'progress_percent': progress_percent
			}
		}
	
	def _handle_strategy_complete(self, data) -> Dict[str, Any]:
		"""Handle strategy completion with enhanced summary"""
		strategy_type = data.get('strategy_type', 'Unknown Strategy')
		
		log_messages = [
			"=" * 50,
			f"[INFO] STRATEGY COMPLETE: {data.get('test_name', 'Unknown Test')}",
			"=" * 50,
			f"[INFO] Strategy Type: {strategy_type}",
			f"[INFO] Total Tests: {data.get('total_tests', 0)}",
			f"[INFO] Success Rate: {data.get('success_rate', 0)}%"
		]
		
		# Add Shmoo-specific information
		if strategy_type == 'Shmoo':
			if data.get('shmoo_dimensions'):
				log_messages.append(f"[INFO] Shmoo Dimensions: {data['shmoo_dimensions']}")
			if data.get('x_axis_config'):
				x_config = data['x_axis_config']
				log_messages.append(f"[INFO] X-Axis: {x_config.get('Type', 'Unknown')} - {x_config.get('Domain', 'Unknown')}")
			if data.get('y_axis_config'):
				y_config = data['y_axis_config']
				log_messages.append(f"[INFO] Y-Axis: {y_config.get('Type', 'Unknown')} - {y_config.get('Domain', 'Unknown')}")
		
		# Add status breakdown
		if 'status_counts' in data and data['status_counts']:
			log_messages.append("[DATA] Results Summary:")
			for status, count in data['status_counts'].items():
				total_tests = data.get('total_tests', 1)
				percentage = (count / total_tests * 100) if total_tests > 0 else 0
				log_messages.append(f"  {status}: {count} ({percentage:.1f}%)")
		
		# Add failure patterns
		if data.get('failure_patterns'):
			log_messages.append("[DATA] Top Failure Patterns:")
			for pattern, count in list(data['failure_patterns'].items())[:3]:
				log_messages.append(f"  {pattern}: {count} occurrences")
		
		log_messages.append("=" * 50)
		
		return {
			'log_messages': log_messages,
			'experiment_reset': True,
			'status_update': "Strategy Complete"
		}
	
	def _handle_experiment_complete(self, data) -> Dict[str, Any]:
		"""Handle overall experiment completion"""
		return {
			'log_message': f"[SUCCESS] EXPERIMENT COMPLETED: '{data['test_name']}'",
			'status_update': "Experiment Complete"
		}
	
	def _handle_experiment_failed(self, data) -> Dict[str, Any]:
		"""Handle experiment failure"""
		self.current_state = ExecutionState.FAILED
		return {
			'log_message': f"[FAIL] EXPERIMENT FAILED: '{data['experiment_name']}' - {data['reason']}",
			'status_label': {'text': ' Failed ', 'bg': 'red', 'fg': 'white'},
			'progress_bar_style': "Error.Horizontal.TProgressbar",
			'status_update': f"Failed: {data['reason']}"
		}

	# ==================== CONTROL COMMAND HANDLERS ====================

	def _handle_experiment_ended_by_command(self, data) -> Dict[str, Any]:
		"""Handle experiment ended by END command"""
		completed = data['completed_iterations']
		total = data['total_iterations']
		reason = data['reason']
		
		return {
			'log_message': f"[END] Experiment ended by {reason} after {completed}/{total} iterations"
		}

	def _handle_execution_halted(self, data) -> Dict[str, Any]:
		"""Handle execution halted - ENHANCED"""
		self.current_state = ExecutionState.HALTED
		test_name = data.get('test_name', 'Unknown')
		iteration = data.get('current_iteration', 0)
		message = data.get('message', f'Execution halted at iteration {iteration}')
		
		return {
			'log_message': f"[HALT] EXECUTION HALTED: {message}",
			'status_label': {'text': ' Halted ', 'bg': 'orange', 'fg': 'black'},
			'status_update': "HALTED - Waiting for Continue",
			'progress_bar_style': "Warning.Horizontal.TProgressbar",
			'button_update': {
				'hold_button': {'text': 'Continue', 'style': 'Continue.TButton', 'state': 'normal'},
				'end_button': {'state': 'normal', 'text': 'End'},
				'cancel_button': {'state': 'normal', 'text': 'Cancel'}
			}
		}

	def _handle_execution_resumed(self, data) -> Dict[str, Any]:
		"""Handle execution resumed - ENHANCED"""
		self.current_state = ExecutionState.EXPERIMENT_RUNNING
		test_name = data.get('test_name', 'Unknown')
		iteration = data.get('current_iteration', 0)
		message = data.get('message', f'Execution resumed from iteration {iteration}')
		
		return {
			'log_message': f"[RUN] EXECUTION RESUMED: {message}",
			'status_label': {'text': ' Running ', 'bg': '#BF0000', 'fg': 'white'},
			'status_update': "Resumed",
			'progress_bar_style': "Custom.Horizontal.TProgressbar",
			'button_update': {
				'hold_button': {'text': 'Hold', 'style': 'Hold.TButton', 'state': 'normal'},
				'end_button': {'state': 'normal', 'text': 'End'},
				'cancel_button': {'state': 'normal', 'text': 'Cancel'}
			}
		}

	def _handle_execution_cancelled(self, data) -> Dict[str, Any]:
		"""Handle execution cancellation"""
		self.current_state = ExecutionState.CANCELLED
		
		reason = data.get('reason', 'User requested')
		experiment_name = data.get('experiment_name', 'Unknown')
		
		log_messages = [
			f"[CANCEL] Execution CANCELLED: {reason}",
		]
		
		# Add progress info if available
		if 'completed_experiments' in data and 'total_experiments' in data:
			completed = data['completed_experiments']
			total = data['total_experiments']
			log_messages.append(f"[INFO] Progress: {completed}/{total} experiments completed before cancellation")
		
		# Add current experiment info if available
		if experiment_name != 'Unknown':
			log_messages.append(f"[INFO] Last experiment: {experiment_name}")
		
		return {
			'log_messages': log_messages,
			'status_label': {'text': ' Cancelled ', 'bg': 'gray', 'fg': 'white'},
			'enable_buttons': True,
			'reset_thread_state': True,
			'progress_bar_style': "Error.Horizontal.TProgressbar"
		}

	def _handle_execution_setup(self, data) -> Dict[str, Any]:
		"""Handle execution setup notification"""
		total_experiments = data['total_experiments']
		experiment_names = data['experiment_names']
		
		return {
			'log_message': f"[START] Setup: {total_experiments} experiments queued",
			'log_message_2': f"[INFO] Experiments: {', '.join(experiment_names[:3])}{'...' if len(experiment_names) > 3 else ''}",
			'execution_setup': {
				'total_experiments': total_experiments,
				'experiment_names': experiment_names
			}
		}

	def _handle_execution_prepared(self, data) -> Dict[str, Any]:
		"""Handle execution preparation"""
		return {
			'log_message': "[READY] Framework prepared for execution",
			'status_update': "Ready"
		}

	def _handle_execution_finalized(self, data) -> Dict[str, Any]:
		"""Handle execution finalization"""
		reason = data.get('reason', 'completed')
		return {
			'log_message': f"[DONE] Execution finalized: {reason}",
			'status_update': f"Finalized ({reason})",
			'enable_buttons': True
		}

	# ==================== STEP-BY-STEP MODE HANDLERS ====================

	def _handle_step_mode_enabled(self, data) -> Dict[str, Any]:
		"""Handle step-by-step mode enabled"""
		return {
			'log_message': "[INFO] Step-by-step execution mode enabled",
			'strategy_label_update': {'text': 'Mode: Step-by-Step', 'foreground': 'orange'}
		}

	def _handle_step_mode_disabled(self, data) -> Dict[str, Any]:
		"""Handle step-by-step mode disabled"""
		return {
			'log_message': "[INFO] Step-by-step mode disabled - continuous execution",
			'strategy_label_update': {'foreground': 'black'}
		}

	def _handle_step_iteration_complete(self, data) -> Dict[str, Any]:
		"""Handle step iteration completion (waiting for command)"""
		self.current_state = ExecutionState.STEP_WAITING
		iteration = data['current_iteration']
		total = data['total_iterations']
		stats = data.get('current_stats', {})
		
		log_messages = [
			f"[INFO] STEP MODE: Iteration {iteration}/{total} COMPLETE",
			f"[DATA] Current Stats - Pass: {stats.get('pass_count', 0)}, Fail: {stats.get('fail_count', 0)}",
			"[INFO] Waiting for command..."
		]
		
		return {
			'log_messages': log_messages,
			'status_update': "Step: Waiting for Command",
			'progress_bar_style': "Warning.Horizontal.TProgressbar"
		}

	def _handle_step_continue_issued(self, data) -> Dict[str, Any]:
		"""Handle step continue command issued - ENHANCED"""
		self.current_state = ExecutionState.ITERATION_RUNNING
		
		current_iteration = data.get('current_iteration', 0)
		total_iterations = data.get('total_iterations', 0)
		next_iteration = data.get('next_iteration', current_iteration + 1)
		message = data.get('message', 'Step continue processed')
		
		return {
			'log_message': f"[RUN] STEP CONTINUE: {message} - proceeding to iteration {next_iteration}/{total_iterations}",
			'status_update': "Step: Continuing to Next Iteration",
			'status_label': {'text': ' Running ', 'bg': '#BF0000', 'fg': 'white'},
			'progress_bar_style': "Custom.Horizontal.TProgressbar",
			'button_update': {
				'step_continue_button': {'state': 'disabled'},
				'hold_button': {'state': 'normal', 'text': 'Hold'},
				'end_button': {'state': 'normal', 'text': 'End'},
				'cancel_button': {'state': 'normal', 'text': 'Cancel'}
			}
		}

	def _handle_step_waiting(self, data) -> Dict[str, Any]:
		"""Handle step mode waiting for command state"""
		self.current_state = ExecutionState.STEP_WAITING
		
		current_iteration = data.get('current_iteration', 0)
		total_iterations = data.get('total_iterations', 0)
		available_commands = data.get('available_commands', [])
		next_iteration = data.get('next_iteration', current_iteration + 1)
		
		log_messages = [
			f"[INFO] STEP MODE: Waiting for command after iteration {current_iteration}/{total_iterations}",
			f"[INFO] Next iteration will be: {next_iteration}/{total_iterations}",
			"[INFO] Available commands:"
		]
		
		# Add available commands to log
		command_descriptions = {
			'step_continue': '  • step_continue() - Continue to next iteration',
			'end_experiment': '  • end_experiment() - End after current iteration', 
			'cancel_execution': '  • cancel_execution() - Cancel immediately'
		}
		
		for cmd in available_commands:
			if cmd in command_descriptions:
				log_messages.append(command_descriptions[cmd])
		
		return {
			'log_messages': log_messages,
			'status_label': {'text': ' Step Wait ', 'bg': 'orange', 'fg': 'black'},
			'status_update': f"Step: Waiting for Command (Iter {current_iteration})",
			'progress_bar_style': "Warning.Horizontal.TProgressbar",
			'button_update': {
				'step_continue_button': {'state': 'normal', 'text': 'Continue Step'},
				'end_button': {'state': 'normal', 'text': 'End Experiment'},
				'cancel_button': {'state': 'normal', 'text': 'Cancel'}
			},
			'waiting_state': {
				'type': 'step_waiting',
				'current_iteration': current_iteration,
				'total_iterations': total_iterations,
				'next_iteration': next_iteration
			}
		}

	def _handle_halt_waiting(self, data) -> Dict[str, Any]:
		"""Handle halt mode waiting for command state"""
		self.current_state = ExecutionState.HALTED
		
		current_iteration = data.get('current_iteration', 0)
		total_iterations = data.get('total_iterations', 0)
		available_commands = data.get('available_commands', [])
		message = data.get('message', 'Execution halted')
		
		log_messages = [
			f"[INFO] HALT MODE: {message}",
			f"[INFO] Will resume from iteration {current_iteration + 1}/{total_iterations}",
			"[INFO] Available commands:"
		]
		
		# Add available commands to log
		command_descriptions = {
			'continue_execution': '  • continue_execution() - Resume execution',
			'cancel_execution': '  • cancel_execution() - Cancel execution',
			'end_experiment': '  • end_experiment() - End experiment'
		}
		
		for cmd in available_commands:
			if cmd in command_descriptions:
				log_messages.append(command_descriptions[cmd])
		
		return {
			'log_messages': log_messages,
			'status_label': {'text': ' Halted ', 'bg': 'orange', 'fg': 'black'},
			'status_update': f"Halted: Waiting for Command (Iter {current_iteration})",
			'progress_bar_style': "Warning.Horizontal.TProgressbar",
			'button_update': {
				'hold_button': {'state': 'normal', 'text': 'Continue', 'style': 'Continue.TButton'},
				'end_button': {'state': 'normal', 'text': 'End Experiment'},
				'cancel_button': {'state': 'normal', 'text': 'Cancel'}
			},
			'waiting_state': {
				'type': 'halt_waiting',
				'current_iteration': current_iteration,
				'total_iterations': total_iterations,
				'resume_iteration': current_iteration + 1
			}
		}

	# ==================== ADDITIONAL HANDLERS ====================

	def _handle_all_complete(self, data) -> Dict[str, Any]:
		"""Handle all experiments completion"""
		self.current_state = ExecutionState.COMPLETED
		return {
			'log_message': "[DONE] All experiments completed",
			'status_label': {'text': ' Completed ', 'bg': '#006400', 'fg': 'white'},
			'enable_buttons': True
		}

	def _handle_experiment_status_update(self, data) -> Dict[str, Any]:
		"""Handle experiment status updates from ControlPanel"""
		return {
			'experiment_status_update': {
				'experiment_name': data['experiment_name'],
				'status': data['status'],
				'bg_color': data['bg_color'],
				'fg_color': data['fg_color']
			}
		}

	def _handle_experiment_index_update(self, data) -> Dict[str, Any]:
		"""Handle experiment index updates"""
		current_index = data['current_experiment_index']
		total_experiments = data['total_experiments']
		experiment_name = data['experiment_name']
		
		return {
			'log_message': f"[RUN] Starting Experiment {current_index + 1}/{total_experiments}: {experiment_name}",
			'experiment_index_update': {
				'current_experiment_index': current_index,
				'total_experiments': total_experiments,
				'experiment_name': experiment_name
			}
		}

	def _handle_all_experiments_complete(self, data) -> Dict[str, Any]:
		"""Handle all experiments completion"""
		self.current_state = ExecutionState.COMPLETED
		return {
			'log_message': f"[INFO] All {data['total_executed']} experiments completed",
			'status_label': {'text': ' Completed ', 'bg': '#006400', 'fg': 'white'},
			'enable_buttons': True,
			'finalize_execution': True
		}

	def _handle_execution_ended(self, data) -> Dict[str, Any]:
		"""Handle execution ended by END command"""
		self.current_state = ExecutionState.COMPLETED
		
		reason = data.get('reason', 'END command')
		experiment_name = data.get('experiment_name', 'Unknown')
		
		log_messages = [
			f"[] Execution ENDED: {reason}",
		]
		
		# Add progress info if available
		if 'completed_experiments' in data and 'total_experiments' in data:
			completed = data['completed_experiments']
			total = data['total_experiments']
			log_messages.append(f"[DONE] Progress: {completed}/{total} experiments completed before ending")
		
		# Add current experiment info if available
		if experiment_name != 'Unknown':
			log_messages.append(f"[DONE] Last experiment: {experiment_name}")
		
		return {
			'log_messages': log_messages,
			'status_label': {'text': ' Ended ', 'bg': 'orange', 'fg': 'black'},
			'enable_buttons': True,
			'reset_thread_state': True,
			'finalize_execution': True
		}

	# ==================== PHASE DETECTION HELPERS ====================

	def _is_boot_phase(self, status):
		"""Detect if this is a boot-related status"""
		boot_keywords = [
			'preparing environment', 'starting boot process', 'system boot in progress',
			'boot complete', 'booting', 'initialization', 'hardware init', 's2t flow'
		]
		return any(keyword in status.lower() for keyword in boot_keywords)

	def _is_test_content_phase(self, status):
		"""Detect if this is test content execution"""
		content_keywords = [
			'running test content', 'test content complete', 'processing results',
			'analyzing results', 'executing', 'dragon', 'linux', 'custom'
		]
		return any(keyword in status.lower() for keyword in content_keywords)

	def _handle_boot_phase_progress(self, data) -> Dict[str, Any]:
		"""Handle boot-specific progress with enhanced logging and UI"""
		status = data['status']
		progress_weight = data.get('progress_weight', 0.0)
		iteration = data['iteration']
		
		boot_stage = self._extract_boot_stage(status)
		progress_percent = int(progress_weight * 100)
		
		return {
			'log_message': f"[INFO] Boot Progress [{progress_percent}%]: {boot_stage}",
			'iteration_info': {
				'current': iteration,
				'progress_weight': progress_weight
			},
			'update_progress': True,
			'boot_visual_feedback': {
				'stage': boot_stage,
				'progress_weight': progress_weight
			}
		}

	def _handle_test_content_progress(self, data) -> Dict[str, Any]:
		"""Handle test content execution progress"""
		status = data['status']
		progress_weight = data.get('progress_weight', 0.0)
		iteration = data['iteration']
		
		content_stage = self._extract_content_stage(status)
		progress_percent = int(progress_weight * 100)
		
		return {
			'log_message': f"[INFO] Test Content [{progress_percent}%]: {content_stage}",
			'iteration_info': {
				'current': iteration,
				'progress_weight': progress_weight
			},
			'update_progress': True
		}

	def _extract_boot_stage(self, status):
		"""Extract meaningful boot stage from status"""
		stage_mapping = {
			'preparing environment': 'Preparing Environment',
			'starting boot process': 'Initializing Boot',
			'system boot in progress': 'System Boot',
			'boot complete': 'Boot Complete',
			's2t flow': 'S2T Flow'
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

class MainThreadHandler(IStatusReporter):
	"""Complete main thread handler with all original functionality"""

	def __init__(self, root, ui_controller):
		self.root = root
		self.ui = ui_controller
		self._update_queue = queue.Queue()
		self._callback_enabled = True
		self._after_id = None  # Track the after callback ID
		self._is_destroyed = False  # Track if we've been destroyed
			
		# Replace complex handlers with complete state machine
		self.state_machine = ExecutionStateMachine(self._apply_ui_updates)
		
		# Start processor
		self._start_processor()

	def report_status(self, status_data: Dict[str, Any]) -> None:
		"""IStatusReporter interface implementation"""
		self.queue_status_update(status_data)

	def _start_processor(self):
		"""Start the update processor"""
		self._process_updates()

	def _process_updates(self):
		# Check if we've been destroyed
		if self._is_destroyed or not self._callback_enabled:
			return
		
		"""Process updates in main thread"""
		try:
			# Check if root still exists
			if not self.root or not self.root.winfo_exists():
				self._is_destroyed = True
				return
	
			while not self._update_queue.empty():
				try:
					update_data = self._update_queue.get_nowait()
					self._process_single_update(update_data)
				except queue.Empty:
					break
		except tk.TclError:
			# Widget has been destroyed
			self._is_destroyed = True
			return
		except Exception as e:
			print(f"Update processor error: {e}")
		finally:
			# Schedule next update only if not destroyed
			if not self._is_destroyed and self._callback_enabled:
				try:
					self._after_id = self.root.after(50, self._process_updates)
				except tk.TclError:
					# Root has been destroyed
					self._is_destroyed = True

	def _process_single_update(self, update_data):
		"""Process single update through state machine"""
		if not self._callback_enabled:
			return
			
		event = ExecutionEvent(
			type=update_data.get('type'),
			data=update_data.get('data', {}),
			timestamp=update_data.get('timestamp', '')
		)
		
		self.state_machine.process_event(event)

	def cleanup(self):
		"""Proper cleanup method"""
		self._is_destroyed = True
		self._callback_enabled = False
		
		# Cancel any pending after callbacks
		if self._after_id and self.root:
			try:
				self.root.after_cancel(self._after_id)
				self._after_id = None
			except tk.TclError:
				pass  # Root already destroyed
		
		# Clear the queue
		self.clear_queue()

	def disable_callbacks(self):
		"""Disable callback processing and cleanup"""
		self._callback_enabled = False
		self.cleanup()	

	def _apply_ui_updates(self, updates: Dict[str, Any]):
		"""Apply comprehensive UI updates safely in main thread"""
		try:
			# Check if UI still exists before any updates
			if not hasattr(self, 'ui') or not self.ui or not hasattr(self.ui, 'root'):
				return

			# Check if root window still exists
			try:
				if not self.ui.root.winfo_exists():
					return
			except tk.TclError:
				return

			# Handle single log message
			if 'log_message' in updates:
				try:
					self.ui.log_status(updates['log_message'])
				except tk.TclError:
					return  # Widget destroyed

			# Handle multiple log messages
			if 'log_messages' in updates:
				for message in updates['log_messages']:
					try:
						self.ui.log_status(message)
					except tk.TclError:
						return  # Widget destroyed
			
			# Handle multiple log messages
			if 'log_messages' in updates:
				for message in updates['log_messages']:
					try:
						self.ui.log_status(message)
					except tk.TclError:
						return  # Widget destroyed
			
			# Handle status label updates with existence check
			if 'status_label' in updates:
				try:
					if hasattr(self.ui, 'status_label') and self.ui.status_label.winfo_exists():
						label_config = updates['status_label']
						self.ui.status_label.configure(**label_config)
				except tk.TclError:
					return  # Widget destroyed	
																	
			# Handle single log message
			#if 'log_message' in updates:
			#	self.ui.log_status(updates['log_message'])
			
			# Handle multiple log messages
			#if 'log_messages' in updates:
			#	for message in updates['log_messages']:
			#		self.ui.log_status(message)
			
			# Handle additional log message (for experiment start)
			#if 'log_message_2' in updates:
			#	self.ui.log_status(updates['log_message_2'])
			
			# Handle status label updates
			#if 'status_label' in updates:
			#	label_config = updates['status_label']
			#	self.ui.status_label.configure(**label_config)
			
			# Handle strategy progress updates - FIX THIS SECTION

			if 'strategy_progress' in updates:
				progress_data = updates['strategy_progress']
				progress_percent = progress_data['progress_percent']

				# DEBUG: Before update
				self.show_debug_messages(f"BEFORE Strategy Progress Update:")		
				
				# Update UI tracking variables
				self.ui.current_iteration = progress_data['current_iteration']
				self.ui.total_iterations_in_experiment = progress_data['total_iterations']
				
				# Calculate iteration progress weight (0.0 to 1.0)
				if progress_data['total_iterations'] > 0:
					self.ui.current_iteration_progress = (progress_data['current_iteration'] - 1) / progress_data['total_iterations']
				
				# Update progress bar directly AND through overall calculation
				self.ui.progress_var.set(min(100, max(0, progress_percent)))
				self.ui.progress_percentage_label.configure(text=f"{int(progress_percent)}%")
				
				iteration_text = f"Iter {progress_data['current_iteration']}/{progress_data['total_iterations']}"
				self.ui.progress_iteration_label.configure(text=iteration_text)
				
				# Also update overall progress for consistency
				self.ui._update_overall_progress()

				# DEBUG: After update
				self.show_debug_messages(f"AFTER Strategy Progress Update:")
					
			# Handle experiment info updates
			if 'experiment_info' in updates:
				exp_info = updates['experiment_info']
				self.ui.current_experiment_name = exp_info['name']
				self.ui.total_iterations_in_experiment = exp_info['total_iterations']
				#self.ui.current_iteration = 0
				#self.ui.current_iteration_progress = 0.0
				
				self.ui.update_progress_display(
					experiment_name=exp_info['name'],
					strategy_type=exp_info['strategy'],
					test_name=exp_info['test_name'],
					status="Starting Experiment"
				)
				
			# Handle iteration info updates - ENHANCE THIS
			if 'iteration_info' in updates:
				iter_info = updates['iteration_info']

				# DEBUG: Before iteration update
				self.show_debug_messages(f"BEFORE Iteration Info Update:")
		
				self.ui.current_iteration = iter_info['current']
				self.ui.current_iteration_progress = iter_info.get('progress_weight', 0.0)
				
				# Force progress update
				self.ui._update_overall_progress()

				# DEBUG: After iteration update
				self.show_debug_messages(f"AFTER Iteration Info Update:")
			
			# Handle progress updates
			if 'update_progress' in updates:
				print()

				self.show_debug_messages(f"BEFORE Overall Progress Update:")
				
				self.ui._update_overall_progress()
				
				self.show_debug_messages(f"AFTER Overall Progress Update:")
			
			# Handle result status updates
			if 'result_status' in updates:
				self.ui.update_progress_display(result_status=updates['result_status'])
			
			# Handle status updates
			if 'status_update' in updates:
				self.ui.update_progress_display(status=updates['status_update'])
			
			# Handle progress bar style changes
			if 'progress_bar_style' in updates:
				self.ui.progress_bar.configure(style=updates['progress_bar_style'])
				
				# Handle automatic reset
				if 'reset_progress_bar_after' in updates:
					delay = updates['reset_progress_bar_after']
					self.root.after(delay, lambda: self.ui.progress_bar.configure(style="Custom.Horizontal.TProgressbar"))
			
			# Handle button updates
			if 'button_update' in updates:
				button_updates = updates['button_update']
				for button_name, config in button_updates.items():
					if hasattr(self.ui, button_name):
						getattr(self.ui, button_name).configure(**config)
			
			# Handle strategy label updates
			if 'strategy_label_update' in updates:
				self.ui.strategy_label.configure(**updates['strategy_label_update'])
			
			# Handle progress reset
			if 'progress_reset' in updates:
				self.ui.reset_progress_tracking()
			
			# Handle experiment reset
			if 'experiment_reset' in updates:
				self.ui.current_experiment_name = None
				self.ui.update_progress_display(
					experiment_name="",
					strategy_type="Strategy Complete",
					test_name="",
					status="Strategy Complete"
				)
			
			# Handle boot visual feedback
			if 'boot_visual_feedback' in updates:
				self._update_boot_visual_feedback(updates['boot_visual_feedback'])
			
			# Handle button enabling
			if 'enable_buttons' in updates:
				self._enable_ui_buttons()

			if 'reset_thread_state' in updates:
				self.ui.thread_active = False
				
			# ADD experiment status updates
			if 'experiment_status_update' in updates:
				status_data = updates['experiment_status_update']
				self._update_experiment_status_in_ui(status_data)

			# ADD finalization handling
			if 'finalize_execution' in updates:
				self._finalize_execution_ui()
						
			# Handle execution setup
			if 'execution_setup' in updates:
				setup_data = updates['execution_setup']
				self.ui.total_experiments = setup_data['total_experiments']
				self.ui.current_experiment_index = 0
				self.ui.log_status(f"Loaded {setup_data['total_experiments']} experiments")

			# Handle experiment index updates  
			if 'experiment_index_update' in updates:
				index_data = updates['experiment_index_update']
				self.ui.current_experiment_index = index_data['current_experiment_index']
				self.ui.current_experiment_name = index_data['experiment_name']
								
		except Exception as e:
			print(f"UI update error: {e}")

	def _update_boot_visual_feedback(self, feedback_data):
		"""Update visual feedback during boot phases"""
		try:
			boot_stage = feedback_data['stage']
			progress_weight = feedback_data['progress_weight']
			
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

	def _enable_ui_buttons(self):
		"""Re-enable UI buttons after completion"""
		try:
			self.ui.run_button.configure(state='normal')
			self.ui.cancel_button.configure(state='disabled')
			self.ui.hold_button.configure(state='disabled')
			self.ui.end_button.configure(state='disabled')
		except Exception as e:
			print(f"Button enable error: {e}")

	def _update_experiment_status_in_ui(self, status_data):
		"""Update experiment status in UI safely"""
		try:
			experiment_name = status_data['experiment_name']
			for frame_data in self.ui.experiment_frames:
				if frame_data['experiment_name'] == experiment_name:
					frame_data['run_label'].configure(
						text=status_data['status'],
						bg=status_data['bg_color'],
						fg=status_data['fg_color']
					)
					break
		except Exception as e:
			print(f"Error updating experiment status: {e}")

	def _finalize_execution_ui(self):
		"""Finalize UI after all experiments complete"""
		try:
			self.ui.run_button.configure(state='normal')
			self.ui.cancel_button.configure(state='disabled')
			self.ui.hold_button.configure(state='disabled', text=" Hold ")
			self.ui.end_button.configure(state='disabled', text="End")
			self.ui.power_control_button.configure(state='normal')
			self.ui.ipc_control_button.configure(state='normal')
		except Exception as e:
			print(f"Error finalizing UI: {e}")

	# ==================== PUBLIC INTERFACE ====================

	def queue_status_update(self, status_data: Dict[str, Any]):
		"""Queue status update for processing"""
		try:
			if self._callback_enabled:
				self._update_queue.put_nowait(status_data)
		except Exception as e:
			print(f"Queue error: {e}")

	def disable_callbacks_temporarily(self, duration_ms: int = 2000):
		"""Temporarily disable callbacks during critical operations"""
		self._callback_enabled = False
		self.root.after(duration_ms, self._re_enable_callbacks)

	def _re_enable_callbacks(self):
		"""Re-enable callbacks after critical operation"""
		self._callback_enabled = True

	def enable_callbacks(self):
		"""Enable callback processing"""
		self._callback_enabled = True

	def disable_callbacks(self):
		"""Disable callback processing"""
		self._callback_enabled = False

	def clear_queue(self):
		"""Clear pending updates"""
		while not self._update_queue.empty():
			try:
				self._update_queue.get_nowait()
			except queue.Empty:
				break

	# ==================== DEBUG INTERFACE ====================

	def show_debug_messages(self, msg):
		if debug:
			print(f"{msg}")
			self.ui.debug_progress_state()

