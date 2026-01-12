from enum import Enum
from dataclasses import dataclass
import queue
import threading
import sys
import os
from typing import Dict, Any, Callable, Optional, List
import tkinter as tk
import time


current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

print(' -- Framework Control Panel Status Handler -- rev 1.7')

sys.path.append(parent_dir)
from DebugFramework.Interfaces.IFramework import IStatusReporter, IUIController, StatusType

debug = False

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
	ENDED = "ended"

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

		# Statistics tracking
		self.current_experiment_stats = {
			'experiment_name': None,
			'strategy_type': None,
			'total_iterations': 0,
			'current_iteration': 0,
			'iteration_results': [],
			'start_time': None,
			'is_active': False
		}
			
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
			'experiment_end_requested': self._handle_experiment_end_command,

			# Step-by-step mode handlers
			'step_mode_enabled': self._handle_step_mode_enabled,
			'step_mode_disabled': self._handle_step_mode_disabled,
			'step_iteration_complete': self._handle_step_iteration_complete,
			'step_continue_issued': self._handle_step_continue_issued,

			# Waiting Handlers
			'step_waiting': self._handle_step_waiting,
			'halt_waiting': self._handle_halt_waiting,			

			# Additional handlers for completeness
			#'all_experiments_complete': self._handle_all_complete,
			

			# ADD these handlers for ControlPanel
			'experiment_status_update': self._handle_experiment_status_update,
			'experiment_index_update': self._handle_experiment_index_update,
			'all_experiments_complete': self._handle_all_experiments_complete,
			'execution_ended_complete': self._handle_experiments_ended,

			# Handlers for AutomationPanel
			'flow_execution_setup': self._handle_flow_execution_setup,
			'flow_execution_complete': self._handle_flow_execution_complete,
			'flow_execution_ended_complete': self._handle_flow_execution_ended_complete,
			'flow_execution_cancelled': self._handle_flow_execution_cancelled,
			'flow_execution_error': self._handle_flow_execution_error,
			'current_node': self._handle_current_node,
			'node_running': self._handle_node_running,
			'node_completed': self._handle_node_completed,
			'node_failed': self._handle_node_failed,
			'node_execution_fail': self._handle_node_execution_fail,
			'node_error': self._handle_node_error,
			'flow_progress_update': self._handle_flow_progress_update,
			'status_update': self._handle_status_update,

			# FIXED: Add missing handlers that FlowTestExecutor is sending
			'log_message': self._handle_log_message,
			'node_start': self._handle_node_start,
			'node_complete': self._handle_node_complete,
			'hardware_failure_termination': self._handle_hardware_failure_termination,
			'unwired_port_termination': self._handle_unwired_port_termination,
			'flow_abort_requested': self._handle_flow_abort_requested,

		}

	def get_current_statistics(self) -> Dict[str, Any]:
		"""Get current experiment statistics"""
		results = self.current_experiment_stats['iteration_results']
		if not results:
			return {
				'total_completed': 0,
				'pass_rate': 0.0,
				'fail_rate': 0.0,
				'recent_trend': 'insufficient_data',
				'recommendation': 'continue',
				'sufficient_data': False,
				'current_iteration': self.current_experiment_stats['current_iteration'],
				'total_iterations': self.current_experiment_stats['total_iterations'],
				'experiment_name': self.current_experiment_stats['experiment_name']
			}
		
		# Calculate statistics
		total_completed = len(results)
		
		# Count different result types
		status_counts = {}
		for result in results:
			status = result['status'].upper()
			status_counts[status] = status_counts.get(status, 0) + 1
		
		# Calculate pass/fail counts
		pass_count = (status_counts.get('PASS', 0) + 
					 status_counts.get('SUCCESS', 0) + 
					 status_counts.get('*', 0))
		
		fail_count = status_counts.get('FAIL', 0) 
		
		cancelled_count = status_counts.get('CANCELLED', 0)
		execution_fail_count = (	status_counts.get('EXECUTIONFAIL', 0) + 
					 				status_counts.get('FAILED', 0)+ 
					 				status_counts.get('ERROR', 0))
		
		# Calculate valid tests (excluding cancelled and execution failures)
		valid_tests = total_completed - cancelled_count - execution_fail_count
		
		# Calculate rates
		if valid_tests > 0:
			pass_rate = (pass_count / valid_tests) * 100
			fail_rate = (fail_count / valid_tests) * 100
		else:
			pass_rate = 0.0
			fail_rate = 0.0
		
		return {
			'total_completed': total_completed,
			'pass_count': pass_count,
			'fail_count': fail_count,
			'cancelled_count': cancelled_count,
			'execution_fail_count': execution_fail_count,
			'pass_rate': round(pass_rate, 1),
			'fail_rate': round(fail_rate, 1),
			'valid_tests': valid_tests,
			'recent_trend': self._analyze_recent_trend(results, pass_rate, fail_rate, total_completed),
			'recommendation': self._get_recommendation(pass_rate, fail_rate, total_completed),
			'sufficient_data': self._has_sufficient_data(pass_rate, fail_rate, total_completed),
			'current_iteration': self.current_experiment_stats['current_iteration'],
			'total_iterations': self.current_experiment_stats['total_iterations'],
			'experiment_name': self.current_experiment_stats['experiment_name'],
			'strategy_type': self.current_experiment_stats['strategy_type'],
			'status_breakdown': status_counts,
			'latest_status': results[-1]['status'] if results else 'None',
			'latest_iteration': results[-1]['iteration'] if results else 0
		}
	
	def _analyze_recent_trend(self, results: List[Dict], pass_rate: float, fail_rate: float, total: int) -> str:
		"""Analyze recent trend in results"""
		
		if not self._has_sufficient_data(pass_rate,fail_rate, total):
			return "insufficient_data"
		
		recent_3 = results[-3:]
		fails = sum(1 for r in recent_3 if r['status'].upper() in ['FAIL'])
		passes = sum(1 for r in recent_3 if r['status'].upper() in ['PASS'])

		if fails == 3 and pass_rate < 5: # Trending to FAIL
			return "repro"
		elif passes == 3 and fail_rate < 5: # Trending to PASS
			return "no-repro"
		elif fails > 1 and passes > 1:
			return "flaky"
		elif fails == 0:
			return "no-repro"
		else:
			return "mixed"
	
	def _get_recommendation(self, pass_rate: float, fail_rate: float, total: int) -> str:
		"""Get recommendation based on current statistics"""
		if total < 3:
			return "continue"
		elif self._has_sufficient_data(pass_rate,fail_rate, total):
			if pass_rate >= 90:
				return "sufficient_data_good"
			elif fail_rate >= 90:
				return "sufficient_data_poor"
			else:
				return "continue"
		elif pass_rate >= 95:
			return "trending_excellent"
		elif fail_rate >= 95:
			return "trending_poor"
		else:
			return "continue"
	
	def _has_sufficient_data(self, pass_rate: float, fail_rate: float, total: int) -> bool:
		"""Determine if we have sufficient data for decision making"""
		if total >= 5:
			return True
		elif total >= 3:
			if pass_rate >= 95 or fail_rate >= 95:
				return True
		return False

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

		self.current_experiment_stats = {
			'experiment_name': data['experiment_name'],
			'strategy_type': data['strategy_type'],
			'total_iterations': data['total_iterations'],
			'current_iteration': 0,
			'iteration_results': [],
			'start_time': time.time(),
			'is_active': True
		}
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
			},
			# ADDED: Initialize experiment stats display
			'experiment_stats_update': {
				'iteration': 0,
				'total_iterations': data['total_iterations'],
				'pass_rate': 0.0,
				'fail_rate': 0.0,
				'recommendation': 'Starting - No data yet'
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

		if self.current_experiment_stats['is_active']:
			iteration_result = {
				'iteration': data['iteration'],
				'status': data['status'],
				'scratchpad': data.get('scratchpad', ''),
				'seed': data.get('seed', ''),
				'timestamp': time.time()
			}

			self.current_experiment_stats['iteration_results'].append(iteration_result)
			self.current_experiment_stats['current_iteration'] = data['iteration']
							
		# Build status message with details
		status_msg = f"[DONE] Completed Iteration {data['iteration']}: {data['status']}"
		if data.get('scratchpad'):
			status_msg += f" ({data['scratchpad']})"
		if data.get('seed'):
			status_msg += f" [Seed: {data['seed']}]"

		# ADDED: Get current statistics for UI update
		current_stats = self.get_current_statistics()
		
		return {
			'log_message': status_msg,
			'iteration_info': {
				'current': data['iteration'],
				'progress_weight': 1.0
			},
			'update_progress': True,
			'result_status': data['status'],
			'iteration_complete': True,
			'current_statistics': current_stats,
			# ADDED: Experiment statistics update
			'experiment_stats_update': {
				'iteration': current_stats['current_iteration'],
				'total_iterations': current_stats['total_iterations'],
				'pass_rate': current_stats['pass_rate'],
				'fail_rate': current_stats['fail_rate'],
				'recommendation': current_stats['recommendation'],
				'sufficient_data': current_stats['sufficient_data'],
				'recent_trend': current_stats['recent_trend']
			}
		}
	
	def _handle_iteration_failed(self, data) -> Dict[str, Any]:
		"""Handle iteration failure - UPDATED"""
		if self.current_experiment_stats['is_active']:
			iteration_result = {
				'iteration': data['iteration'],
				'status': data['status'],
				'scratchpad': data.get('error', ''),
				'seed': '',
				'timestamp': time.time()
			}
			
			self.current_experiment_stats['iteration_results'].append(iteration_result)
			self.current_experiment_stats['current_iteration'] = data['iteration']
		

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
			'progress_bar_style': "Iteration.Error.Horizontal.TProgressbar",  # Updated
			'reset_progress_bar_after': 2000,
			'current_statistics': self.get_current_statistics()
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
		current_iteration = data.get('current_iteration', 0)
		total_iterations = data.get('total_iterations', 0)

		# Update current experiment stats
		if self.current_experiment_stats['is_active']:
			self.current_experiment_stats['current_iteration'] = current_iteration
			self.current_experiment_stats['total_iterations'] = total_iterations
				
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

		# ADDED: Get current statistics
		current_stats = self.get_current_statistics()
		
		return {
			'log_message': status_msg,
			'strategy_progress': {
				'current_iteration': data['current_iteration'],
				'total_iterations': data['total_iterations'],
				'progress_percent': progress_percent
			},
			# ADDED: Experiment statistics update
			'experiment_stats_update': {
				'iteration': current_iteration,
				'total_iterations': total_iterations,
				'pass_rate': current_stats['pass_rate'],
				'fail_rate': current_stats['fail_rate'],
				'recommendation': current_stats['recommendation'],
				'sufficient_data': current_stats['sufficient_data'],
				'recent_trend': current_stats['recent_trend']
			}
		}
	
	def _handle_strategy_complete(self, data) -> Dict[str, Any]:
		"""Handle strategy completion with enhanced summary"""
		strategy_type = data.get('strategy_type', 'Unknown Strategy')
		self.current_experiment_stats['is_active'] = False
		
		final_stats = self.get_current_statistics()

		log_messages = [
			"=" * 50,
			f"[INFO] STRATEGY COMPLETE: {data.get('test_name', 'Unknown Test')}",
			"=" * 50,
			f"[INFO] Strategy Type: {strategy_type}",
			f"[INFO] Total Tests: {data.get('total_tests', 0)}",
			f"[INFO] Success Rate: {data.get('success_rate', 0)}%",
			f"[INFO] Final Recommendation: {final_stats['recommendation']}"
		]

		# Add detailed statistics
		if final_stats['total_completed'] > 0:
			log_messages.extend([
				f"[DATA] Pass: {final_stats['pass_count']}, Fail: {final_stats['fail_count']}",
				f"[DATA] Valid Tests: {final_stats['valid_tests']}, Cancelled: {final_stats['cancelled_count']}",
				f"[DATA] Recent Trend: {final_stats['recent_trend']}"
			])
					
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
			'status_update': "Strategy Complete",
			'final_statistics': self.get_current_statistics(),
			# ADDED: Reset experiment stats display
			'experiment_stats_update': {
				'iteration': final_stats['current_iteration'],
				'total_iterations': final_stats['total_iterations'],
				'pass_rate': final_stats['pass_rate'],
				'fail_rate': final_stats['fail_rate'],
				'recommendation': f"Complete - {final_stats['recommendation']}"
			}
		}
	
	def _handle_experiment_complete(self, data) -> Dict[str, Any]:
		"""Handle overall experiment completion"""
		test_folder = data.get('test_folder', '')
		summary_path = data.get('summary_path', '')
		
		return {
			'log_message': f"[SUCCESS] EXPERIMENT COMPLETED: '{data['test_name']}'",
			'log_message_2': f"[INFO] Test folder: {test_folder}",
			'log_message_3': f"[INFO] Summary: {summary_path}" if summary_path else "",
			'status_update': "Experiment Complete",
			'experiment_summary': {
				'test_folder': test_folder,
				'summary_path': summary_path,
				'experiment_name': data['test_name']
			}
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

	def _handle_experiments_ended(self, data) -> Dict[str, Any]:
		"""Handle experiments ended by command - FIXED with button states"""
		self.current_state = ExecutionState.ENDED
		framework_instance_id = data.get('framework_instance_id', 'unknown')

		return {
			'log_message': f"[INFO] Experiments ended by command, total executed: {data['total_executed']}",
			'status_label': {'text': ' Ended ', 'bg': 'orange', 'fg': 'black'},
			'button_update': {
				'run_button': {'state': 'normal', 'text': 'Run'},
				'cancel_button': {'state': 'disabled', 'text': 'Cancel'},
				'hold_button': {'state': 'disabled', 'text': 'Hold', 'style': 'Hold.TButton'},
				'end_button': {'state': 'disabled', 'text': 'End', 'style': 'End.TButton'},
				'power_control_button': {'state': 'normal'},
				'ipc_control_button': {'state': 'normal'}
			},
			'reset_thread_state': True,
			'finalize_execution': True,
			'framework_instance_id': framework_instance_id
		}

	def _handle_execution_cancelled(self, data) -> Dict[str, Any]:
		"""Handle execution cancellation - FIXED with button states"""
		self.current_state = ExecutionState.CANCELLED
		
		reason = data.get('reason', 'User requested')
		experiment_name = data.get('experiment_name', 'Unknown')
		
		log_messages = [
			f"[CANCEL] Execution CANCELLED: {reason}",
		]
		
		if 'completed_experiments' in data and 'total_experiments' in data:
			completed = data['completed_experiments']
			total = data['total_experiments']
			log_messages.append(f"[INFO] Progress: {completed}/{total} experiments completed before cancellation")
		
		if experiment_name != 'Unknown':
			log_messages.append(f"[INFO] Last experiment: {experiment_name}")
		
		return {
			'log_messages': log_messages,
			'status_label': {'text': ' Cancelled ', 'bg': 'gray', 'fg': 'white'},
			'button_update': {
				'run_button': {'state': 'normal', 'text': 'Run'},
				'cancel_button': {'state': 'disabled', 'text': 'Cancel'},
				'hold_button': {'state': 'disabled', 'text': 'Hold', 'style': 'Hold.TButton'},
				'end_button': {'state': 'disabled', 'text': 'End', 'style': 'End.TButton'},
				'power_control_button': {'state': 'normal'},
				'ipc_control_button': {'state': 'normal'}
			},
			'reset_thread_state': True,
			'progress_bar_style': "Iteration.Error.Horizontal.TProgressbar"
		}

	def _handle_execution_ended(self, data) -> Dict[str, Any]:
		"""Handle execution ended by END command"""
		self.current_state = ExecutionState.COMPLETED
		
		reason = data.get('reason', 'END command')
		experiment_name = data.get('experiment_name', 'Unknown')
		
		log_messages = [
			f"[INFO] Execution ENDED: {reason}",
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

	def _handle_experiment_ended_by_command(self, data) -> Dict[str, Any]:
		"""Handle experiment ended by END command"""
		completed = data['completed_iterations']
		total = data['total_iterations']
		reason = data['reason']
		
		return {
			'log_message': f"[END] Experiment ended by {reason} after {completed}/{total} iterations"
		}

	def _handle_experiment_end_command(self, data) -> Dict[str, Any]:
		"""Handle experiment ended by END command"""
		message = data['message']
		
		return {
			'log_message': f"{message}",
			'status_label': {'text': ' Ending ', 'bg': 'red', 'fg': 'white'},
			'status_update': "Ending - Waiting for current Iteration to finish",
		}

	def _handle_execution_halted(self, data) -> Dict[str, Any]:
		"""Handle execution halted - UPDATED"""
		self.current_state = ExecutionState.HALTED
		test_name = data.get('test_name', 'Unknown')
		iteration = data.get('current_iteration', 0)
		message = data.get('message', f'Execution halted at iteration {iteration}')
		
		return {
			'log_message': f"[HALT] EXECUTION HALTED: {message}",
			'status_label': {'text': ' Halted ', 'bg': 'orange', 'fg': 'black'},
			'status_update': "HALTED - Waiting for Continue",
			'progress_bar_style': "Iteration.Boot.Horizontal.TProgressbar",  # Updated
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

	def _handle_execution_setup(self, data) -> Dict[str, Any]:
		"""Handle execution setup notification"""
		total_experiments = data['total_experiments']
		experiment_names = data['experiment_names']
		framework_instance_id = data['framework_instance_id']
		return {
			'log_message': f"[START] Setup: {total_experiments} experiments queued",
			'log_message_2': f"[INFO] Experiments: {', '.join(experiment_names[:3])}{'...' if len(experiment_names) > 3 else ''}",
			'execution_setup': {
				'total_experiments': total_experiments,
				'experiment_names': experiment_names,
				'framework_instance_id': framework_instance_id
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

# ==================== MISSING FLOW EXECUTOR HANDLERS ====================

	def _handle_log_message(self, data) -> Dict[str, Any]:
		"""Handle log messages from FlowTestExecutor"""
		message = data if isinstance(data, str) else str(data)
		return {
			'log_message': f"[FLOW] {message}"
		}

	def _handle_node_start(self, data) -> Dict[str, Any]:
		"""Handle node start notification"""
		if isinstance(data, dict):
			node_id = data.get('node_id', 'Unknown')
			node_name = data.get('node_name', 'Unknown')
		else:
			node_id = getattr(data, 'ID', 'Unknown')
			node_name = getattr(data, 'Name', 'Unknown')
		
		return {
			'log_message': f"[NODE] Starting: {node_name} ({node_id})",
			'current_node_update': {
				'node_id': node_id,
				'node_name': node_name,
				'experiment_name': data.get('experiment_name', 'Unknown') if isinstance(data, dict) else f"Node: {node_name}"
			}
		}

	def _handle_node_complete(self, data) -> Dict[str, Any]:
		"""Handle node completion notification"""
		if isinstance(data, dict):
			node_id = data.get('node_id', 'Unknown')
			node_name = data.get('node_name', 'Unknown')
		else:
			node_id = getattr(data, 'ID', 'Unknown')
			node_name = getattr(data, 'Name', 'Unknown')
		
		return {
			'log_message': f"[NODE] Completed: {node_name} ({node_id})",
			# Note: This is different from 'node_completed' which updates the visual status
			# This just logs that the node finished executing
		}

	def _handle_hardware_failure_termination(self, data) -> Dict[str, Any]:
		"""Handle hardware failure termination"""
		failed_node = data.get('failed_node', 'Unknown') if isinstance(data, dict) else 'Unknown'
		reason = data.get('reason', 'Hardware failure') if isinstance(data, dict) else str(data)
		
		return {
			'log_message': f"[CRITICAL] Hardware failure termination: {reason}",
			'log_message_2': f"[CRITICAL] Failed node: {failed_node}",
			'status_label': {'text': ' HW Failure ', 'bg': 'red', 'fg': 'white'},
			'enable_buttons': True,
			'reset_thread_state': True
		}

	def _handle_unwired_port_termination(self, data) -> Dict[str, Any]:
		"""Handle unwired port termination"""
		node_name = data.get('node_name', 'Unknown') if isinstance(data, dict) else 'Unknown'
		termination_type = data.get('termination_type', 'unwired_port') if isinstance(data, dict) else 'unwired_port'
		reason = data.get('reason', 'Unwired port') if isinstance(data, dict) else str(data)
		
		return {
			'log_message': f"[FLOW] Unwired port termination: {reason}",
			'log_message_2': f"[FLOW] Terminating node: {node_name}",
			'status_label': {'text': ' Terminated ', 'bg': 'orange', 'fg': 'black'},
			'enable_buttons': True,
			'reset_thread_state': True
		}

	def _handle_flow_abort_requested(self, data) -> Dict[str, Any]:
		"""Handle flow abort request"""
		reason = data.get('reason', 'Flow aborted') if isinstance(data, dict) else str(data)
		failed_node = data.get('failed_node', 'Unknown') if isinstance(data, dict) else 'Unknown'
		
		return {
			'log_message': f"[ABORT] Flow abort requested: {reason}",
			'log_message_2': f"[ABORT] Node: {failed_node}",
			'status_label': {'text': ' Aborted ', 'bg': 'red', 'fg': 'white'},
			'enable_buttons': True,
			'reset_thread_state': True
		}

	# ==================== ADDITIONAL HANDLERS ====================

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
		framework_instance_id = data['framework_instance_id']
		return {
			'log_message': f"[RUN] Starting Experiment {current_index + 1}/{total_experiments}: {experiment_name}",
			'experiment_index_update': {
				'current_experiment_index': current_index,
				'total_experiments': total_experiments,
				'experiment_name': experiment_name,
				'framework_instance_id': framework_instance_id
			}
		}

	def _handle_all_experiments_complete(self, data) -> Dict[str, Any]:
		"""Handle all experiments completion - FIXED with button states"""
		self.current_state = ExecutionState.COMPLETED
		framework_instance_id = data.get('framework_instance_id', 'unknown')
		
		return {
			'log_message': f"[SUCCESS] All {data['total_executed']} experiments completed successfully",
			'status_label': {'text': ' Completed ', 'bg': '#006400', 'fg': 'white'},
			'button_update': {
				'run_button': {'state': 'normal', 'text': 'Run'},
				'cancel_button': {'state': 'disabled', 'text': 'Cancel'},
				'hold_button': {'state': 'disabled', 'text': 'Hold', 'style': 'Hold.TButton'},
				'end_button': {'state': 'disabled', 'text': 'End', 'style': 'End.TButton'},
				'power_control_button': {'state': 'normal'},
				'ipc_control_button': {'state': 'normal'}
			},
			'reset_thread_state': True,
			'finalize_execution': True,
			'framework_instance_id': framework_instance_id
		}

	# ==================== PHASE DETECTION HELPERS ====================

	def _is_boot_phase(self, status):
		"""Detect if this is a boot-related status"""
		boot_keywords = [
			'preparing environment', 'starting boot process', 'system boot in progress',
			'boot process complete', 'booting', 'initialization', 'hardware init', 'starting s2t flow', 'boot failed'
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
			'Boot Complete': 'Boot Complete',
			'Starting S2T Flow': 'Boot - S2T Flow',
			'Boot Failed - Retrying': 'Boot Failed - Retry'
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

	# ==================== AUTOMATION FLOW HANDLERS ====================

	def _handle_flow_execution_setup(self, data) -> Dict[str, Any]:
		"""Handle flow execution setup"""
		total_nodes = data.get('total_nodes', 0)
		framework_instance_id = data.get('framework_instance_id', 'unknown')
		
		return {
			'log_message': f"[FLOW] Setup: {total_nodes} nodes queued for execution",
			'log_message_2': f"[INFO] Framework Instance: {framework_instance_id}",
			'status_label': {'text': ' Preparing ', 'bg': '#4CAF50', 'fg': 'white'},
			'flow_setup': {
				'total_nodes': total_nodes,
				'framework_instance_id': framework_instance_id
			}
		}

	def _handle_current_node(self, data) -> Dict[str, Any]:
		"""Handle current node update"""
		if isinstance(data, dict):
			# Primitive data from thread
			node_id = data.get('node_id', 'Unknown')
			node_name = data.get('node_name', 'Unknown')
			experiment = data.get('experiment', {})
			exp_name = experiment.get('Test Name', 'No Experiment') if experiment else 'No Experiment'
		else:
			# Legacy node object
			node_id = getattr(data, 'ID', 'Unknown')
			node_name = getattr(data, 'Name', 'Unknown')
			exp_name = getattr(data, 'Experiment', {}).get('Test Name', 'No Experiment')
		
		return {
			'log_message': f"[NODE] Executing: {node_name} ({node_id})",
			'log_message_2': f"[INFO] Experiment: {exp_name}",
			'status_label': {'text': ' Running Node ', 'bg': '#2196F3', 'fg': 'white'},
			'current_node_update': {
				'node_id': node_id,
				'node_name': node_name,
				'experiment_name': exp_name
			}
		}

	def _handle_node_running(self, data) -> Dict[str, Any]:
		"""Handle node running status"""
		node_id = data.get('node_id', 'Unknown') if isinstance(data, dict) else getattr(data, 'ID', 'Unknown')
		
		return {
			'log_message': f"[RUN] Node {node_id} experiment started",
			'status_label': {'text': ' Running Exp ', 'bg': '#FF5722', 'fg': 'white'},
			'node_status_update': {
				'node_id': node_id,
				'status': 'running',
				'bg_color': '#FF5722',
				'fg_color': 'white'
			}
		}

	def _handle_node_completed(self, data) -> Dict[str, Any]:
		"""Handle node completion"""
		node_id = data.get('node_id', 'Unknown') if isinstance(data, dict) else getattr(data, 'ID', 'Unknown')
		
		return {
			'log_message': f"[DONE] Node {node_id} completed successfully",
			'node_status_update': {
				'node_id': node_id,
				'status': 'completed',
				'bg_color': '#4CAF50',
				'fg_color': 'white'
			},
			'flow_progress_update': True
		}

	def _handle_node_failed(self, data) -> Dict[str, Any]:
		"""Handle node test failure (red)"""
		node_id = data.get('node_id', 'Unknown') if isinstance(data, dict) else getattr(data, 'ID', 'Unknown')
		error = data.get('error', '') if isinstance(data, dict) else ''
		
		log_msg = f"[FAIL] Node {node_id} test failed"
		if error:
			log_msg += f": {error}"
		
		return {
			'log_message': log_msg,
			'node_status_update': {
				'node_id': node_id,
				'status': 'failed',
				'bg_color': '#F44336',
				'fg_color': 'white'
			},
			'flow_progress_update': True
		}

	def _handle_node_execution_fail(self, data) -> Dict[str, Any]:
		"""Handle node execution failure (yellow)"""
		node_id = data.get('node_id', 'Unknown') if isinstance(data, dict) else getattr(data, 'ID', 'Unknown')
		error = data.get('error', '') if isinstance(data, dict) else ''
		
		log_msg = f"[EXEC FAIL] Node {node_id} execution failed"
		if error:
			log_msg += f": {error}"
		
		return {
			'log_message': log_msg,
			'node_status_update': {
				'node_id': node_id,
				'status': 'execution_fail',
				'bg_color': '#FFC107',
				'fg_color': 'black'
			},
			'flow_progress_update': True
		}

	def _handle_node_error(self, node_data):
		"""Handle node error."""
		if isinstance(node_data, tuple) and len(node_data) >= 2:
			node, error = node_data[0], node_data[1]
			node_id = getattr(node, 'ID', 'Unknown')
		else:
			node_id = node_data.get('node_id', 'Unknown') if isinstance(node_data, dict) else 'Unknown'
			error = node_data.get('error', 'Unknown error') if isinstance(node_data, dict) else str(node_data)
		
		return {
			'log_message': f"[ERROR] Node {node_id} error: {error}",
			'node_status_update': {
				'node_id': node_id,
				'status': 'execution_fail',
				'bg_color': '#FFC107',
				'fg_color': 'black'
			}
		}

	def _handle_flow_execution_complete(self, data) -> Dict[str, Any]:
		"""Handle flow execution completion"""
		framework_instance_id = data.get('framework_instance_id', 'unknown')
		
		return {
			'log_message': "[FLOW] Flow execution completed successfully",
			'log_message_2': f"[INFO] Framework Instance: {framework_instance_id}",
			'status_label': {'text': ' Completed ', 'bg': '#006400', 'fg': 'white'},
			'enable_buttons': True,
			'finalize_execution': True
		}

	def _handle_flow_execution_ended_complete(self, data) -> Dict[str, Any]:
		"""Handle flow execution ended by command"""
		framework_instance_id = data.get('framework_instance_id', 'unknown')
		
		return {
			'log_message': "[FLOW] Flow execution ended by command",
			'log_message_2': f"[INFO] Framework Instance: {framework_instance_id}",
			'status_label': {'text': ' Ended ', 'bg': 'orange', 'fg': 'black'},
			'enable_buttons': True,
			'finalize_execution': True
		}

	def _handle_flow_execution_cancelled(self, data) -> Dict[str, Any]:
		"""Handle flow execution cancellation"""
		reason = data.get('reason', 'User requested') if isinstance(data, dict) else str(data)
		
		return {
			'log_message': f"[FLOW] Flow execution cancelled: {reason}",
			'status_label': {'text': ' Cancelled ', 'bg': 'gray', 'fg': 'white'},
			'enable_buttons': True,
			'reset_thread_state': True
		}

	def _handle_flow_execution_error(self, data) -> Dict[str, Any]:
		"""Handle flow execution error"""
		error_msg = data if isinstance(data, str) else data.get('error', 'Unknown error')
		
		return {
			'log_message': f"[ERROR] Flow execution error: {error_msg}",
			'status_label': {'text': ' Error ', 'bg': 'red', 'fg': 'white'},
			'enable_buttons': True,
			'reset_thread_state': True
		}

	def _handle_flow_progress_update(self, data) -> Dict[str, Any]:
		"""Handle flow progress updates"""
		return {
			'flow_progress_update': True,
			'status_update': "Flow Progress Updated"
		}
	
	def _handle_status_update(self, data) -> Dict[str, Any]:
		"""Handle generic status updates"""
		message = data.get('message', '') if isinstance(data, dict) else str(data)
		return {
			'log_message': f"[STATUS] {message}",
			'status_update': message
		}

# Used by Control Panel
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

		# Give time for any pending operations to complete
		time.sleep(0.1)

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

			# ADDED: Experiment statistics update
			self._safe_update_wrapper('experiment_stats_update', updates,
				lambda: self._handle_experiment_stats_update_safe(updates['experiment_stats_update']))
			
			# Wrap all updates in try-catch for individual error handling
			self._safe_update_wrapper('log_message', updates, 
				lambda: self.ui.log_status(updates['log_message']))
			
			self._safe_update_wrapper('log_messages', updates,
				lambda: [self.ui.log_status(msg) for msg in updates['log_messages']])
			
			self._safe_update_wrapper('log_message_2', updates,
				lambda: self.ui.log_status(updates['log_message_2']))
			
			self._safe_update_wrapper('status_label', updates,
				lambda: self.ui._coordinate_status_updates(updates['status_label']))
				
			# ENHANCED: Strategy progress handling for dual progress bars
			self._safe_update_wrapper('strategy_progress', updates,
				lambda: self.ui._coordinate_progress_updates('strategy_progress', updates['strategy_progress']))
				
			# ENHANCED: Experiment info updates
			self._safe_update_wrapper('experiment_info', updates,
				lambda: self._handle_experiment_info_dual_progress(updates['experiment_info']))
			
			# ENHANCED: Iteration info updates
			self._safe_update_wrapper('iteration_info', updates,
				lambda: self.ui._coordinate_progress_updates('iteration_progress', updates['iteration_info']))
			
			self._safe_update_wrapper('update_progress', updates,
				lambda: self._handle_progress_update_safe())
			
			self._safe_update_wrapper('result_status', updates,
				lambda: self.ui.update_progress_display(result_status=updates['result_status']))
			
			self._safe_update_wrapper('status_update', updates,
				lambda: self.ui.update_progress_display(status=updates['status_update']))
			
			self._safe_update_wrapper('progress_bar_style', updates,
				lambda: self._handle_progress_bar_style_safe(updates))
			
			self._safe_update_wrapper('button_update', updates,
				lambda: self._handle_button_update_safe(updates['button_update']))
			
			self._safe_update_wrapper('strategy_label_update', updates,
				lambda: self.ui.strategy_label.configure(**updates['strategy_label_update']))
			
			self._safe_update_wrapper('progress_reset', updates,
				lambda: self.ui.reset_progress_tracking())
			
			self._safe_update_wrapper('experiment_reset', updates,
				lambda: self._handle_experiment_reset_safe())
			
			self._safe_update_wrapper('boot_visual_feedback', updates,
				lambda: self._update_boot_visual_feedback(updates['boot_visual_feedback']))
			
			self._safe_update_wrapper('enable_buttons', updates,
				lambda: self.ui._coordinate_button_states('enable_after_completion'))

			self._safe_update_wrapper('reset_thread_state', updates,
				lambda: self._handle_thread_state_reset())
		
			self._safe_update_wrapper('experiment_status_update', updates,
				lambda: self._update_experiment_status_in_ui(updates['experiment_status_update']))

			self._safe_update_wrapper('finalize_execution', updates,
				lambda: self._finalize_execution_ui())
						
			self._safe_update_wrapper('execution_setup', updates,
				lambda: self._handle_execution_setup_safe(updates['execution_setup']))

			self._safe_update_wrapper('experiment_index_update', updates,
				lambda: self._handle_experiment_index_safe(updates['experiment_index_update']))

			# Automation Handlers -- Safe
			self._safe_update_wrapper('flow_setup', updates,
				lambda: self._handle_flow_setup_safe(updates['flow_setup']))

			self._safe_update_wrapper('current_node_update', updates,
				lambda: self._handle_current_node_update_safe(updates['current_node_update']))

			self._safe_update_wrapper('node_status_update', updates,
				lambda: self._handle_node_status_update_safe(updates['node_status_update']))

			self._safe_update_wrapper('flow_progress_update', updates,
				lambda: self._handle_flow_progress_update_safe())

		except Exception as e:
			print(f"UI update error: {e}")

	def _update_boot_visual_feedback(self, feedback_data):
		"""Update visual feedback during boot phases - FIXED for dual progress bars"""
		try:
			boot_stage = feedback_data['stage']
			progress_weight = feedback_data['progress_weight']
			
			if 'preparing' in boot_stage.lower():
				# Update iteration progress bar for boot phase
				if hasattr(self.ui, 'iteration_progress_bar'):
					self.ui.iteration_progress_bar.configure(style="Iteration.Boot.Horizontal.TProgressbar")
				if hasattr(self.ui, 'iteration_status_label'):
					self.ui.iteration_status_label.configure(text=f"Status: 🔧 {boot_stage}")
				if hasattr(self.ui, 'phase_label'):
					self.ui.phase_label.configure(text="[BOOT] Preparing", foreground="orange")
					
			elif 'initializing' in boot_stage.lower():
				if hasattr(self.ui, 'iteration_progress_bar'):
					self.ui.iteration_progress_bar.configure(style="Iteration.Boot.Horizontal.TProgressbar")
				if hasattr(self.ui, 'iteration_status_label'):
					self.ui.iteration_status_label.configure(text=f"Status: 🔄 {boot_stage}")
				if hasattr(self.ui, 'phase_label'):
					self.ui.phase_label.configure(text="[BOOT] Initializing", foreground="orange")
					
			elif 'boot' in boot_stage.lower() and 'complete' not in boot_stage.lower():
				if hasattr(self.ui, 'iteration_progress_bar'):
					self.ui.iteration_progress_bar.configure(style="Iteration.Running.Horizontal.TProgressbar")
				if hasattr(self.ui, 'iteration_status_label'):
					self.ui.iteration_status_label.configure(text=f"Status: ⚡ {boot_stage}")
				if hasattr(self.ui, 'phase_label'):
					self.ui.phase_label.configure(text="[BOOT] In Progress", foreground="blue")
					
			elif 'complete' in boot_stage.lower():
				if hasattr(self.ui, 'iteration_progress_bar'):
					self.ui.iteration_progress_bar.configure(style="Iteration.Horizontal.TProgressbar")
				if hasattr(self.ui, 'iteration_status_label'):
					self.ui.iteration_status_label.configure(text=f"Status: ✅ {boot_stage}")
				if hasattr(self.ui, 'phase_label'):
					self.ui.phase_label.configure(text="[BOOT] Complete", foreground="green")
					
		except Exception as e:
			print(f"Error updating boot visual feedback: {e}")

	def _enable_ui_buttons(self):
		"""Re-enable UI buttons after completion"""
		try:
			if hasattr(self.ui, 'run_button') and self.ui.run_button.winfo_exists():
				self.ui.run_button.configure(state='normal')
			if hasattr(self.ui, 'cancel_button') and self.ui.cancel_button.winfo_exists():
				self.ui.cancel_button.configure(state='disabled')
			if hasattr(self.ui, 'hold_button') and self.ui.hold_button.winfo_exists():
				self.ui.hold_button.configure(state='disabled')
			if hasattr(self.ui, 'end_button') and self.ui.end_button.winfo_exists():
				self.ui.end_button.configure(state='disabled')
		except Exception as e:
			print(f"Button enable error: {e}")

	def _update_experiment_status_in_ui(self, status_data):
		"""Update experiment status in UI safely with animations"""
		try:
			experiment_name = status_data['experiment_name']
			status = status_data['status']
			bg_color = status_data['bg_color']
			fg_color = status_data['fg_color']
			
			self.ui._update_experiment_status_safe(experiment_name, status, bg_color, fg_color)
			
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

	# ==================== SAFE UPDATE HANDLERS ====================

	def _handle_experiment_stats_update_safe(self, stats_data):
		"""Handle experiment statistics updates safely"""
		try:
			if hasattr(self.ui, 'status_panel') and self.ui.status_panel:
				self.ui.status_panel.update_experiment_stats(
					iteration=stats_data.get('iteration'),
					total_iterations=stats_data.get('total_iterations'),
					pass_rate=stats_data.get('pass_rate'),
					fail_rate=stats_data.get('fail_rate'),
					recommendation=stats_data.get('recommendation')
				)
				
			# Also update any direct UI elements if they exist
			if hasattr(self.ui, 'exp_iteration_label'):
				iteration = stats_data.get('iteration', 0)
				total_iterations = stats_data.get('total_iterations', 0)
				self.ui.exp_iteration_label.configure(text=f"Iteration: {iteration}/{total_iterations}")
				
			if hasattr(self.ui, 'exp_pass_rate_label'):
				pass_rate = stats_data.get('pass_rate', 0)
				self.ui.exp_pass_rate_label.configure(text=f"Pass Rate: {pass_rate:.1f}%")

			if hasattr(self.ui, 'exp_fail_rate_label'):
				pass_rate = stats_data.get('fail_rate', 0)
				self.ui.exp_fail_rate_label.configure(text=f"Fail Rate: {pass_rate:.1f}%")
												
			if hasattr(self.ui, 'exp_recommendation_label'):
				recommendation = stats_data.get('recommendation', '--')
				self.ui.exp_recommendation_label.configure(text=f"Recommendation: {recommendation}")
				
		except Exception as e:
			print(f"Experiment stats update error: {e}")
			
	def _handle_experiment_info_dual_progress(self, exp_info):
		"""Handle experiment info updates for dual progress system"""
		try:
			self.ui.current_experiment_name = exp_info['name']
			self.ui.total_iterations_in_experiment = exp_info['total_iterations']
			
			# Reset iteration progress for new experiment
			self.ui._coordinate_progress_updates('experiment_start', {})
			
			self.ui.update_progress_display(
				experiment_name=exp_info['name'],
				strategy_type=exp_info['strategy'],
				test_name=exp_info['test_name'],
				status="Starting Experiment"
			)
		except Exception as e:
			print(f"Dual progress experiment info update error: {e}")
	
	def _handle_progress_update_safe(self):
		"""Handle progress updates safely"""
		try:
			self.show_debug_messages(f"BEFORE Overall Progress Update:")
			
			# Only update if no strategy progress is active
			if not getattr(self.ui, '_strategy_progress_active', False):
				self.ui._coordinate_progress_updates('overall_calculation', {})
			
			self.show_debug_messages(f"AFTER Overall Progress Update:")
			
		except Exception as e:
			print(f"Progress update error: {e}")

	def _handle_progress_bar_style_safe(self, updates):
		"""Handle progress bar style updates safely - UPDATED for dual bars"""
		try:
			style_name = updates['progress_bar_style']
			duration = updates.get('reset_progress_bar_after')
			
			# Determine which progress bar to update based on style name
			if style_name.startswith('Overall.'):
				bar_type = 'overall'
			elif style_name.startswith('Iteration.'):
				bar_type = 'iteration'
			else:
				# Default to iteration bar for backward compatibility
				bar_type = 'iteration'
				# Convert generic styles to iteration-specific styles
				style_mapping = {
					"Custom.Horizontal.TProgressbar": "Iteration.Horizontal.TProgressbar",
					"Running.Horizontal.TProgressbar": "Iteration.Running.Horizontal.TProgressbar",
					"Warning.Horizontal.TProgressbar": "Iteration.Boot.Horizontal.TProgressbar",
					"Error.Horizontal.TProgressbar": "Iteration.Error.Horizontal.TProgressbar"
				}
				style_name = style_mapping.get(style_name, style_name)
			
			self.ui._coordinate_progress_bar_styles(style_name, duration, bar_type)
			
		except Exception as e:
			print(f"Progress bar style update error: {e}")

	def _handle_experiment_reset_safe(self):
		"""Handle experiment reset safely"""
		try:
			self.ui.current_experiment_name = None
			self.ui.update_progress_display(
				experiment_name="",
				strategy_type="Strategy Complete",
				test_name="",
				status="Strategy Complete"
			)
		except Exception as e:
			print(f"Experiment reset error: {e}")

	def _handle_execution_setup_safe(self, setup_data):
		"""Handle execution setup safely"""
		try:
			self.ui.total_experiments = setup_data['total_experiments']
			self.ui.current_experiment_index = 0
			self.ui.log_status(f"Loaded {setup_data['total_experiments']} experiments")
		except Exception as e:
			print(f"Execution setup error: {e}")

	def _handle_experiment_index_safe(self, index_data):
		"""Handle experiment index updates safely"""
		try:
			self.ui.current_experiment_index = index_data['current_experiment_index']
			self.ui.current_experiment_name = index_data['experiment_name']
		except Exception as e:
			print(f"Experiment index update error: {e}")

	def _safe_update_wrapper(self, key: str, updates: Dict[str, Any], update_func: callable):
		"""Safely execute UI update with error handling"""
		if key in updates:
			try:
				update_func()
			except tk.TclError:
				return  # Widget destroyed
			except Exception as e:
				print(f"Error in {key} update: {e}")

	def _handle_button_update_safe(self, button_updates):
		"""Handle button updates safely with comprehensive error checking"""
		try:
			for button_name, config in button_updates.items():
				if hasattr(self.ui, button_name):
					button = getattr(self.ui, button_name)
					if button and button.winfo_exists():
						try:
							button.configure(**config)
							if debug:
								print(f"Updated {button_name}: {config}")
						except Exception as e:
							print(f"Error updating {button_name}: {e}")
							
		except Exception as e:
			print(f"Button update error: {e}")

	def _handle_thread_state_reset(self):
		"""Handle thread state reset safely"""
		try:
			self.ui.thread_active = False
			if debug:
				print("Thread state reset to False")
		except Exception as e:
			print(f"Thread state reset error: {e}")

	# ==================== AUTOMATION FLOW UI HANDLERS ====================

	def _handle_flow_setup_safe(self, setup_data):
		"""Handle flow setup safely"""
		try:
			if hasattr(self.ui, 'total_nodes'):
				self.ui.total_nodes = setup_data['total_nodes']
			if hasattr(self.ui, 'flow_execution_state'):
				self.ui.flow_execution_state.total_nodes = setup_data['total_nodes']
			
			# Update total nodes label if it exists
			if hasattr(self.ui, 'total_nodes_label'):
				self.ui.total_nodes_label.configure(text=f"Total: {setup_data['total_nodes']}")
				
		except Exception as e:
			print(f"Flow setup update error: {e}")

	def _handle_current_node_update_safe(self, node_data):
		"""Handle current node update safely"""
		try:
			# Update current node labels
			if hasattr(self.ui, 'current_node_label'):
				self.ui.current_node_label.configure(
					text=f"Node: {node_data['node_name']} ({node_data['node_id']})"
				)
			
			if hasattr(self.ui, 'current_experiment_label'):
				self.ui.current_experiment_label.configure(
					text=f"Experiment: {node_data['experiment_name']}"
				)
			
			if hasattr(self.ui, 'current_status_label'):
				self.ui.current_status_label.configure(
					text="Status: Preparing", foreground='blue'
				)
			
			# Update current node reference
			if hasattr(self.ui, 'current_node'):
				# Find the actual node object if needed
				if hasattr(self.ui, 'builder') and self.ui.builder:
					actual_node = self.ui.builder.builtNodes.get(node_data['node_id'])
					if actual_node:
						self.ui.current_node = actual_node
						
		except Exception as e:
			print(f"Current node update error: {e}")

	def _handle_node_status_update_safe(self, status_data):
		"""Handle node status update safely"""
		try:
			node_id = status_data['node_id']
			status = status_data['status']
			bg_color = status_data['bg_color']
			fg_color = status_data['fg_color']
			
			# Update node visual status
			if hasattr(self.ui, 'node_drawer') and self.ui.node_drawer:
				# Find the node object
				if hasattr(self.ui, 'builder') and self.ui.builder:
					node = self.ui.builder.builtNodes.get(node_id)
					if node:
						self.ui.node_drawer.redraw_node(node, status)
			
			# Update current status label if this is the current node
			if (hasattr(self.ui, 'current_node') and self.ui.current_node and 
				self.ui.current_node.ID == node_id):
				
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
				
				if hasattr(self.ui, 'current_status_label'):
					self.ui.current_status_label.configure(
						text=status_text_map.get(status, f"Status: {status}"),
						foreground=status_color_map.get(status, 'black')
					)
					
		except Exception as e:
			print(f"Node status update error: {e}")

	def _handle_flow_progress_update_safe(self):
		"""Handle flow progress update safely"""
		try:
			# Update progress if we have the necessary components
			if hasattr(self.ui, 'update_progress'):
				self.ui.update_progress()
			
			# Update statistics
			if hasattr(self.ui, 'completed_count') and hasattr(self.ui, 'failed_count'):
				if hasattr(self.ui, 'completed_nodes_label'):
					self.ui.completed_nodes_label.configure(
						text=f"✓ Completed: {self.ui.completed_count}"
					)
				if hasattr(self.ui, 'failed_nodes_label'):
					self.ui.failed_nodes_label.configure(
						text=f"✗ Failed: {self.ui.failed_count}"
					)
					
		except Exception as e:
			print(f"Flow progress update error: {e}")

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
		cleared_count = 0 
		while not self._update_queue.empty():
			try:
				self._update_queue.get_nowait()
				cleared_count += 1
			except queue.Empty:
				break
		
		if cleared_count > 0:
			print(f"Cleared {cleared_count} pending status updates")

	# ==================== DEBUG INTERFACE ====================

	def show_debug_messages(self, msg):
		if debug:
			print(f"{msg}")
			self.ui.debug_progress_state()

# Used by AUtomation Panel
class SecondThreadHandler(IStatusReporter):
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
		"""Process single update through state machine AND UI handler"""
		if not self._callback_enabled:
			return
			
		# FIXED: Call the UI's specific handler first
		if hasattr(self.ui, 'handle_main_thread_update'):
			try:
				self.ui.handle_main_thread_update(update_data)
			except Exception as e:
				print(f"UI handler error: {e}")
		
		# Then process through state machine for logging and status
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

		# Give time for any pending operations to complete
		time.sleep(0.1)

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

			# ADDED: Experiment statistics update
			self._safe_update_wrapper('experiment_stats_update', updates,
				lambda: self._handle_experiment_stats_update_safe(updates['experiment_stats_update']))
			
			# Basic logging and status updates
			self._safe_update_wrapper('log_message', updates, 
				lambda: self.ui.log_status(updates['log_message']))
			
			self._safe_update_wrapper('log_messages', updates,
				lambda: [self.ui.log_status(msg) for msg in updates['log_messages']])
			
			self._safe_update_wrapper('log_message_2', updates,
				lambda: self.ui.log_status(updates['log_message_2']))
			
			self._safe_update_wrapper('status_label', updates,
				lambda: self.ui._coordinate_status_updates(updates['status_label']))
				
			# Progress updates - delegate to UI
			self._safe_update_wrapper('strategy_progress', updates,
				lambda: self.ui._coordinate_progress_updates('strategy_progress', updates['strategy_progress']))
				
			self._safe_update_wrapper('experiment_info', updates,
				lambda: self._handle_experiment_info_dual_progress(updates['experiment_info']))
			
			self._safe_update_wrapper('iteration_info', updates,
				lambda: self.ui._coordinate_progress_updates('iteration_progress', updates['iteration_info']))
			
			self._safe_update_wrapper('update_progress', updates,
				lambda: self._handle_progress_update_safe())
			
			self._safe_update_wrapper('result_status', updates,
				lambda: self.ui.update_progress_display(result_status=updates['result_status']))
			
			self._safe_update_wrapper('status_update', updates,
				lambda: self.ui.update_progress_display(status=updates['status_update']))
			
			self._safe_update_wrapper('progress_bar_style', updates,
				lambda: self._handle_progress_bar_style_safe(updates))
			
			# Button and UI state updates - delegate to UI
			self._safe_update_wrapper('button_update', updates,
				lambda: self.ui._coordinate_button_states('specific_button_update', updates['button_update']))
			
			self._safe_update_wrapper('enable_buttons', updates,
				lambda: self.ui._coordinate_button_states('enable_after_completion'))

			self._safe_update_wrapper('reset_thread_state', updates,
				lambda: self._handle_thread_state_reset())
		
			# Experiment status updates (ControlPanel specific)
			self._safe_update_wrapper('experiment_status_update', updates,
				lambda: self._update_experiment_status_in_ui(updates['experiment_status_update']))

			self._safe_update_wrapper('finalize_execution', updates,
				lambda: self._finalize_execution_ui())
						
			self._safe_update_wrapper('execution_setup', updates,
				lambda: self._handle_execution_setup_safe(updates['execution_setup']))

			self._safe_update_wrapper('experiment_index_update', updates,
				lambda: self._handle_experiment_index_safe(updates['experiment_index_update']))

			# Flow-specific updates - delegate to UI flow handler
			self._safe_update_wrapper('flow_setup', updates,
				lambda: self.ui._handle_flow_specific_updates('flow_setup', updates['flow_setup']))

			self._safe_update_wrapper('current_node_update', updates,
				lambda: self.ui._handle_flow_specific_updates('current_node_update', updates['current_node_update']))

			self._safe_update_wrapper('node_status_update', updates,
				lambda: self.ui._handle_flow_specific_updates('node_status_update', updates['node_status_update']))

			self._safe_update_wrapper('flow_progress_update', updates,
				lambda: self.ui._handle_flow_specific_updates('flow_progress_update', {}))

		except Exception as e:
			print(f"UI update error: {e}")

	def _update_experiment_status_in_ui(self, status_data):
		"""Update experiment status in UI safely with animations"""
		try:
			experiment_name = status_data['experiment_name']
			status = status_data['status']
			bg_color = status_data['bg_color']
			fg_color = status_data['fg_color']
			
			self.ui._update_experiment_status_safe(experiment_name, status, bg_color, fg_color)
			
		except Exception as e:
			print(f"Error updating experiment status: {e}")

		#"""Update experiment status in UI safely"""
		#try:
		#	experiment_name = status_data['experiment_name']
		#	for frame_data in self.ui.experiment_frames:
		#		if frame_data['experiment_name'] == experiment_name:
		#			frame_data['run_label'].configure(
		#				text=status_data['status'],
		#				bg=status_data['bg_color'],
		#				fg=status_data['fg_color']
		#			)
		#			break
		#except Exception as e:
		#	print(f"Error updating experiment status: {e}")

	def _finalize_execution_ui(self):
		"""Finalize UI after all experiments complete"""
		try:
			self.ui.run_button.configure(state='normal')
			self.ui.cancel_button.configure(state='disabled')
			self.ui.hold_button.configure(state='disabled', text=" Hold ")
			self.ui.end_button.configure(state='disabled', text="End")
		except Exception as e:
			print(f"Error finalizing UI: {e}")
		try:
			self.ui.power_control_button.configure(state='normal')
		except Exception as e:
			print(f"Warning UI does not have this button: {e}")
		try:
			self.ui.ipc_control_button.configure(state='normal')
		except Exception as e:
			print(f"Warning UI does not have this button: {e}")

	# ==================== SAFE UPDATE HANDLERS ====================


	def _handle_experiment_stats_update_safe(self, stats_data):
		"""Handle experiment statistics updates safely"""
		try:
			if hasattr(self.ui, 'status_panel') and self.ui.status_panel:
				self.ui.status_panel.update_experiment_stats(
					iteration=stats_data.get('iteration'),
					total_iterations=stats_data.get('total_iterations'),
					pass_rate=stats_data.get('pass_rate'),
					fail_rate=stats_data.get('fail_rate'),
					recommendation=stats_data.get('recommendation')
				)
		
			# Also update any direct UI elements if they exist
			if hasattr(self.ui, 'exp_iteration_label'):
				iteration = stats_data.get('iteration', 0)
				total_iterations = stats_data.get('total_iterations', 0)
				self.ui.exp_iteration_label.configure(text=f"Iteration: {iteration}/{total_iterations}")
				
			if hasattr(self.ui, 'exp_pass_rate_label'):
				pass_rate = stats_data.get('pass_rate', 0)
				self.ui.exp_pass_rate_label.configure(text=f"Pass Rate: {pass_rate:.1f}%")

			if hasattr(self.ui, 'exp_fail_rate_label'):
				pass_rate = stats_data.get('fail_rate', 0)
				self.ui.exp_fail_rate_label.configure(text=f"Fail Rate: {pass_rate:.1f}%")
								
			if hasattr(self.ui, 'exp_recommendation_label'):
				recommendation = stats_data.get('recommendation', '--')
				self.ui.exp_recommendation_label.configure(text=f"Recommendation: {recommendation}")
								
		except Exception as e:
			print(f"Experiment stats update error: {e}")
			
	def _handle_experiment_info_dual_progress(self, exp_info):
		"""Handle experiment info updates for dual progress system"""
		try:
			self.ui.current_experiment_name = exp_info['name']
			self.ui.total_iterations_in_experiment = exp_info['total_iterations']
			
			# Reset iteration progress for new experiment
			self.ui._coordinate_progress_updates('experiment_start', {})
			
			self.ui.update_progress_display(
				experiment_name=exp_info['name'],
				strategy_type=exp_info['strategy'],
				test_name=exp_info['test_name'],
				status="Starting Experiment"
			)
		except Exception as e:
			print(f"Dual progress experiment info update error: {e}")
			print(f"Iteration info update error: {e}")

	def _handle_progress_update_safe(self):
		"""Handle progress updates safely"""
		try:
			self.show_debug_messages(f"BEFORE Overall Progress Update:")
			
			# Only update if no strategy progress is active
			if not getattr(self.ui, '_strategy_progress_active', False):
				self.ui._coordinate_progress_updates('overall_calculation', {})
			
			self.show_debug_messages(f"AFTER Overall Progress Update:")
			
		except Exception as e:
			print(f"Progress update error: {e}")

	def _handle_progress_bar_style_safe(self, updates):
		"""Handle progress bar style updates safely - UPDATED for dual bars"""
		try:
			style_name = updates['progress_bar_style']
			duration = updates.get('reset_progress_bar_after')
			
			# Determine which progress bar to update based on style name
			if style_name.startswith('Overall.'):
				bar_type = 'overall'
			elif style_name.startswith('Iteration.'):
				bar_type = 'iteration'
			else:
				# Default to iteration bar for backward compatibility
				bar_type = 'iteration'
				# Convert generic styles to iteration-specific styles
				style_mapping = {
					"Custom.Horizontal.TProgressbar": "Iteration.Horizontal.TProgressbar",
					"Running.Horizontal.TProgressbar": "Iteration.Running.Horizontal.TProgressbar",
					"Warning.Horizontal.TProgressbar": "Iteration.Boot.Horizontal.TProgressbar",
					"Error.Horizontal.TProgressbar": "Iteration.Error.Horizontal.TProgressbar"
				}
				style_name = style_mapping.get(style_name, style_name)
			
			self.ui._coordinate_progress_bar_styles(style_name, duration, bar_type)
			
		except Exception as e:
			print(f"Progress bar style update error: {e}")

	def _handle_experiment_reset_safe(self):
		"""Handle experiment reset safely"""
		try:
			self.ui.current_experiment_name = None
			self.ui.update_progress_display(
				experiment_name="",
				strategy_type="Strategy Complete",
				test_name="",
				status="Strategy Complete"
			)
		except Exception as e:
			print(f"Experiment reset error: {e}")

	def _handle_execution_setup_safe(self, setup_data):
		"""Handle execution setup safely"""
		try:
			self.ui.total_experiments = setup_data['total_experiments']
			self.ui.current_experiment_index = 0
			self.ui.log_status(f"Loaded {setup_data['total_experiments']} experiments")
		except Exception as e:
			print(f"Execution setup error: {e}")

	def _handle_experiment_index_safe(self, index_data):
		"""Handle experiment index updates safely"""
		try:
			self.ui.current_experiment_index = index_data['current_experiment_index']
			self.ui.current_experiment_name = index_data['experiment_name']
		except Exception as e:
			print(f"Experiment index update error: {e}")

	def _safe_update_wrapper(self, key: str, updates: Dict[str, Any], update_func: callable):
		"""Safely execute UI update with error handling"""
		if key in updates:
			try:
				update_func()
			except tk.TclError:
				return  # Widget destroyed
			except Exception as e:
				print(f"Error in {key} update: {e}")

	def _handle_button_update_safe(self, button_updates):
		"""Handle button updates safely with comprehensive error checking"""
		try:
			for button_name, config in button_updates.items():
				if hasattr(self.ui, button_name):
					button = getattr(self.ui, button_name)
					if button and button.winfo_exists():
						try:
							button.configure(**config)
							if debug:
								print(f"Updated {button_name}: {config}")
						except Exception as e:
							print(f"Error updating {button_name}: {e}")
							
		except Exception as e:
			print(f"Button update error: {e}")

	def _handle_thread_state_reset(self):
		"""Handle thread state reset safely"""
		try:
			self.ui.thread_active = False
			if debug:
				print("Thread state reset to False")
		except Exception as e:
			print(f"Thread state reset error: {e}")

	# ==================== AUTOMATION FLOW UI HANDLERS ====================


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
		cleared_count = 0 
		while not self._update_queue.empty():
			try:
				self._update_queue.get_nowait()
				cleared_count += 1
			except queue.Empty:
				break
		
		if cleared_count > 0:
			print(f"Cleared {cleared_count} pending status updates")

	# ==================== DEBUG INTERFACE ====================

	def show_debug_messages(self, msg):
		if debug:
			print(f"{msg}")
			self.ui.debug_progress_state()
