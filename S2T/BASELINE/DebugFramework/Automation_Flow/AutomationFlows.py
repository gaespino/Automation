"""
AutomationFlows.py
Handles orchestration of automation flows for test execution and reporting.
"""

import os
import sys
from abc import ABC, abstractmethod
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Tuple
import threading
import json

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

sys.path.append(parent_dir)


# Import FileHandler module for loading JSON files
import DebugFramework.FileHandler as fh  # Assuming FileHandler contains functions for loading JSON
from DebugFramework.ExecutionHandler.StatusManager import StatusEventType
from DebugFramework.Automation_Flow.AutomationTracker import ExperimentTracker
from DebugFramework.ExecutionHandler.Enums import TestStatus
import DebugFramework.ExecutionHandler.utils.ThreadsHandler as th
ExecutionCommand = th.ExecutionCommand

# Default configuration for System-to-Tester communication
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
	'BOOT_STOP_POSTCODE': 0x0,
	'BOOT_POSTCODE_WT': 30,
	'BOOT_POSTCODE_CHECK_COUNT': 1
}

# ==================== EXPERIMENT DATA & MANAGEMENT ====================

class SharedApiExperimentManager:
	"""Manages experiments using shared Framework API without cleanup conflicts."""
	
	def __init__(self, shared_framework_api, experiment_data, experiment_name=None, **kwargs):
		self.shared_framework_api = shared_framework_api
		self.experiment_data = experiment_data
		self.experiment_name = experiment_name
		self.kwargs = kwargs
		self.experiment_started = False
		self.start_result = None

	def start_experiment(self):
		"""Start experiment using shared API."""
		try:
			print(f"Starting experiment with shared API: {self.experiment_name}")
			
			self.start_result = self.shared_framework_api.start_experiment_step_by_step(
				experiment_data=self.experiment_data,
				experiment_name=self.experiment_name,
				**self.kwargs
			)
			
			if self.start_result['success']:
				self.experiment_started = True
				print(f"Experiment started successfully: {self.experiment_name}")
				return self.start_result
			else:
				raise RuntimeError(f"Failed to start experiment: {self.start_result.get('error')}")
				
		except Exception as e:
			self.experiment_started = False
			print(f"Experiment startup failed: {e}")
			raise

	def cleanup_experiment_only(self):
		"""Clean up current experiment state only (not the entire API)."""
		if self.experiment_started:
			try:
				print(f"Cleaning up experiment state: {self.experiment_name}")
				# Only clean up experiment state, not the entire API
				self.shared_framework_api.cleanup_step_experiment()
				print(f"Experiment cleanup completed: {self.experiment_name}")
			except Exception as e:
				print(f"Error during experiment cleanup for {self.experiment_name}: {e}")
		else:
			print(f"No experiment cleanup needed for {self.experiment_name}")

	def is_experiment_active(self):
		"""Check if experiment is currently active."""
		return self.experiment_started and self.shared_framework_api is not None

# ==================== FLOWS ====================

class FlowInstance(ABC):
	"""
	Enhanced base class representing a flow instance with Framework step-by-step integration.
	"""

	def __init__(self, ID, Name, Framework, framework_utils, Experiment, outputNodeMap, experiment_tracker = None, logger=None):
		self.ID = ID
		self.Name = Name
		self.Type = self.__class__.__name__.replace('FlowInstance', '')  # Node type from class name
		self.Framework = Framework
		self.Experiment = Experiment
		self.outputNodeMap = outputNodeMap
		self.outputPort = 0  # Default output port
		self.runStatusHistory = []  # History of run statuses
		self.execution_stats = {}  # Detailed execution statistics
		
		# Framework API will be set dynamically during execution
		self.framework_api = None  # Initially None
		self.framework_utils = framework_utils
		if not logger: 
			logger = print
		self.logger = logger

		# Initialize system-to-tester configuration
		self.S2T_CONFIG = framework_utils.system_2_tester_default() if framework_utils else S2T_CONFIGURATION

		# Initialize Experiment Tracker
		self.experiment_tracker = experiment_tracker
		self.config_snapshot = ()

	def run_experiment(self):
		"""Main experiment runner with shared Framework API."""
		self.logger(f"Running Experiment: {self.Name} (ID: {self.ID})")

		# Start experiment tracking
		if self.experiment_tracker:
			self.experiment_tracker.start_experiment_tracking(
				self.ID, self.Name, self.Experiment, node_instance=self
			)

			# Debug the tracker initialization
			if hasattr(self.experiment_tracker, 'debugger'):
				self.experiment_tracker.debugger.log(f"Flow experiment started: {self.Name}", "EXPERIMENT")
							
		if self.framework_api is not None:
			try:
				# Use shared Framework API (don't create new context)
				self._run_framework_experiment_with_shared_api()
			except Exception as e:
				self.logger(f"Framework experiment failed: {e}")
				self.runStatusHistory = ['FAILED']
		else:
			self.logger(f"WARNING: Node {self.ID} has no shared Framework API")
			self.runStatusHistory = ['FAILED']
			
		self.set_output_port()

		# Complete experiment tracking
		if self.experiment_tracker:
			test_folder = getattr(self.framework_api.framework.config, 'tfolder', None) if self.framework_api else None
			try:
				final_result = self._determine_final_result()
				self.experiment_tracker.complete_experiment(
					final_result=final_result,
					output_port=self.outputPort,
					test_folder=test_folder
				)
			except Exception as e:
				if hasattr(self.experiment_tracker, 'debugger'):
					self.experiment_tracker.debugger.log_error("Error completing experiment tracking", e)
					
	def _determine_final_result(self):
		"""
		Determine the final result of the experiment based on runStatusHistory.
		Returns a string representing the overall experiment outcome.
		"""
		if not self.runStatusHistory:
			return 'NO_DATA'
		
		# Count different result types
		pass_count = self.runStatusHistory.count('PASS')
		fail_count = self.runStatusHistory.count('FAIL')
		total_valid = pass_count + fail_count
		
		# Handle hardware failures and other statuses
		hardware_failures = sum(1 for status in self.runStatusHistory 
							if status in ['EXECUTION_FAIL', 'FAILED', 'PYTHON_FAIL', 'CANCELLED'])
		
		# If we have hardware failures exceeding threshold
		if total_valid > 0 and (hardware_failures / len(self.runStatusHistory)) > 0.40:
			return 'HARDWARE_FAILURE'
		
		# If no valid test results
		if total_valid == 0:
			return 'NO_VALID_RESULTS'
		
		# Calculate pass rate for valid results
		pass_rate = pass_count / total_valid if total_valid > 0 else 0
		
		# Determine final result based on pass rate
		if pass_rate >= 0.8:
			return 'STABLE'  # 80%+ pass rate
		elif pass_rate >= 0.5:
			return 'FLAKY'  # 50-79% pass rate
		elif pass_rate > 0:
			return 'MOSTLY_FAILING'  # Some passes but mostly fails
		else:
			return 'SOLID_REPRO'  # All fails
					
	def _run_framework_experiment_with_shared_api(self):
		"""Run experiment using shared Framework API with lightweight manager."""
		experiment_name = f"{self.Name}_{self.ID}"
		
		# Create experiment manager (not context manager)
		experiment_manager = SharedApiExperimentManager(
			shared_framework_api=self.framework_api,
			experiment_data=self.Experiment,
			experiment_name=experiment_name,
			S2T_BOOT_CONFIG=self.S2T_CONFIG
		)
		
		try:
			# Start experiment
			experiment_result = experiment_manager.start_experiment()
			
			self.logger(f"Experiment started: {experiment_result['message']}")
			self.logger(f"Thread: {experiment_result.get('thread_name', 'Unknown')}")
			
			# Monitor the experiment
			self._monitor_complete_experiment_lifecycle()
			
		except RuntimeError as e:
			self.logger(f"Failed to start experiment: {e}")
			self.runStatusHistory = [TestStatus.FAILED.value]
		except KeyboardInterrupt:
			self.logger("Experiment interrupted by user")
			self.runStatusHistory = [TestStatus.CANCELLED.value]
		except Exception as e:
			self.logger(f"Experiment execution error: {e}")
			self.runStatusHistory = [TestStatus.FAILED.value]
		finally:
			# Clean up experiment state only (not entire API)
			try:
				experiment_manager.cleanup_experiment_only()
			except Exception as e:
				self.logger(f"Error in experiment cleanup: {e}")

	def _monitor_complete_experiment_lifecycle(self):
		"""
		Monitor the complete experiment lifecycle until it's truly finished.
		Only return when experiment is complete, cancelled, or failed.
		"""
		iteration_count = 0
		max_iterations = self._get_max_iterations()
		collected_results = []
		experiment_active = True
		USE_TIMEOUT = False
		TIMEOUT_SECONDS = 600 if USE_TIMEOUT else None

		self.logger(f"Starting complete experiment lifecycle monitoring. Max iterations: {max_iterations}")
		self.logger(f"Timeout {'ENABLED' if USE_TIMEOUT else 'DISABLED'} - relying on PythonSV for failure detection")
			
		try:
			while experiment_active:
				# Wait for next event from the experiment thread
				if USE_TIMEOUT:
					event_result = self.framework_api.wait_for_next_iteration_event(timeout=TIMEOUT_SECONDS)
				else:
					# Wait indefinitely - let the framework/PythonSV handle failures
					event_result = self.framework_api.wait_for_next_iteration_event(timeout=None)
				
				if not event_result['success']:
					# Only handle timeout if timeout is enabled
					if event_result.get('timeout') and USE_TIMEOUT:
						self.logger("Timeout waiting for iteration event - experiment may be stuck")
						try:
							cancel_result = self.framework_api.cancel_experiment_with_ack(max_wait_time=5.0)
							self.logger(f"Cancel command sent and acknowledged: {cancel_result.get('acknowledged', False)}")
						except Exception as e:
							self.logger(f"Error sending cancel command: {e}")
						experiment_active = False
					
					elif event_result.get('cleanup_requested'):
						self.logger("Experiment cleanup was requested externally")
						experiment_active = False
					
					elif event_result.get('thread_died'):
						self.logger("Experiment thread died unexpectedly")
						experiment_active = False
					
					else:
						self.logger(f"Error waiting for iteration event: {event_result.get('error')}")
						# [DONE] Don't exit on non-timeout errors when timeout is disabled
						if USE_TIMEOUT:
							experiment_active = False
						else:
							self.logger("Continuing to wait (timeout disabled)...")
							continue
					
					if not collected_results and not experiment_active:
						self.runStatusHistory = [TestStatus.FAILED.value]
					break
				
				# [DONE] Rest of your event processing logic remains exactly the same
				event_data = event_result['event_data']
				event_type = event_data['event_type']
				
				self.logger(f"Received event: {event_type}")
				
				if event_type == StatusEventType.EXPERIMENT_COMPLETE.value:
					self.logger("Experiment completed successfully")
					final_results = event_data.get('final_results', [])
					self._process_final_results_from_events(collected_results, final_results)
					experiment_active = False
				
				elif event_type == StatusEventType.EXPERIMENT_FAILED.value:
					self.logger(f"Experiment failed: {event_data.get('error', 'Unknown error')}")
					if collected_results:
						self._process_final_results_from_events(collected_results, [])
					else:
						self.runStatusHistory = ['FAILED']
					experiment_active = False
				
				elif event_type in ['iteration_cancelled', 'iteration_failed']:
					self.logger(f"Iteration {event_type}: {event_data.get('reason', 'Unknown reason')}")
					if collected_results:
						self._process_final_results_from_events(collected_results, [])
					else:
						status = 'CANCELLED' if 'cancelled' in event_type else 'FAILED'
						self.runStatusHistory = [status]
					experiment_active = False
				
				elif event_type == StatusEventType.ITERATION_COMPLETE.value:
					iteration_count += 1
					
					# Extract iteration information
					iteration_num = event_data.get('iteration', iteration_count)
					status = event_data.get('status', 'Unknown')
					status_classification = event_data.get('status_classification', {})
					scratchpad = event_data.get('scratchpad', '')
					seed = event_data.get('seed', '')

					# [DONE] Check if this is the last iteration
					is_last_iteration = (iteration_count >= (max_iterations))
									
					# Get statistics from the status handler system
					statistics =  self.framework_api.get_iteration_statistics()#event_data.get('statistics', {})

					self.logger(f"Iteration {iteration_count} / {max_iterations} completed:")
					self.logger(f"  Status: {status}")
					self.logger(f"  Classification: {status_classification.get('category', 'unknown')}")
					self.logger(f"  Pass rate: {statistics.get('pass_rate', 0)}%")
					self.logger(f"  Total completed: {statistics.get('total_completed', 0)}")
					self.logger(f"  Recommendation: {statistics.get('recommendation', 'continue')}")
					
					# Store iteration result - check if we need this one here
					iteration_result = {
							'iteration': iteration_num,
							'status': status,
							'scratchpad': scratchpad,
							'seed': seed,
							'hardware_failure': False
						}

					self.execution_stats = statistics

					# Check for hardware failure
					if status_classification.get('should_abort_flow', False):
						self.logger(f"HARDWARE FAILURE detected in iteration {iteration_num}: {status}")
						collected_results.append({
							'iteration': iteration_num,
							'status': status,
							'scratchpad': scratchpad,
							'seed': seed,
							'hardware_failure': True
						})
						try:
							cancel_result = self.framework_api.cancel_experiment_with_ack()
							self.logger(f"Experiment cancelled due to hardware failure: {cancel_result.get('reason', 'unknown')}")
						except Exception as e:
							self.logger(f"Error cancelling experiment: {e}")
						experiment_active = False
						break
					
					# Store valid iteration result
					collected_results.append(iteration_result)
					
					# Store current statistics from status handler
					self.execution_stats = statistics

					# Track iteration if tracker available
					if self.experiment_tracker:
						config_snapshot = self._get_current_config_snapshot()
						self.experiment_tracker.track_iteration(
							iteration_num, status, scratchpad, seed, config_snapshot
						)
					
					execution_state = self.framework_api.get_current_state()
					waiting_step = execution_state.get('waiting_for_step', False)
					# Only make decisions for valid test results
					if status_classification.get('is_valid_test', False):
						
						if is_last_iteration:
							if waiting_step:
								self.logger("Last iteration completed - sending END command")
								
								# Use API method with acknowledgment
								end_result = self.framework_api.end_current_experiment_with_ack(max_wait_time=60.0)
								
								if end_result['acknowledged']:
									self.logger(f"End command confirmed in {end_result.get('wait_time', 0):.2f}s")
								else:
									self.logger(f"End command not confirmed: {end_result.get('reason', 'unknown')}")
							else:
								self.logger("Experiment will be ended by normal execution flow.")
								
						else:
							# Use statistics from status handler for decision making
							decision = self._make_iteration_decision(statistics, iteration_count, max_iterations)
							self.logger(f"Decision for iteration {iteration_num}: {decision}")
							print(f' - Flow Execution iteration: {iteration_num} -- Decision: {decision}')
					
							if decision == 'continue':
								print("Sending continue command for next iteration...")
								self.logger("Sending continue command for next iteration...")
								
								# Use API method with acknowledgment
								if waiting_step:
									continue_result = self.framework_api.continue_next_iteration_with_ack(max_wait_time=60.0)
									
									if continue_result['acknowledged']:
										self.logger(f"Continue command confirmed in {continue_result.get('wait_time', 0):.2f}s")
										print(f"Continue command processed successfully in {continue_result.get('wait_time', 0):.2f}s")
									else:
										self.logger(f"Continue command not confirmed: {continue_result.get('reason', 'timeout')}")
										print(f"Failed to confirm continue command: {continue_result.get('reason', 'timeout')}")
										
										# Check if we should continue anyway or abort
										if continue_result.get('reason') == 'timeout':
											self.logger("Continuing despite timeout - command might still be processed")
										else:
											self.logger("Aborting due to command confirmation failure")
											experiment_active = False
								else:
									self.logger("Execution not in waiting step mode... Continue")
										
							elif decision == 'end':
								self.logger("Early termination - sending END command")
								
								# Use API method with acknowledgment
								end_result = self.framework_api.end_current_experiment_with_ack(max_wait_time=60.0)
								
								if end_result['acknowledged']:
									self.logger(f"End command confirmed in {end_result.get('wait_time', 0):.2f}s")
								else:
									self.logger(f"End command not confirmed: {end_result.get('reason', 'unknown')}")
							
							else:  # cancel
								self.logger("Sending cancel command...")
								
								# Use API method with acknowledgment
								cancel_result = self.framework_api.cancel_experiment_with_ack(max_wait_time=10.0)
								
								if cancel_result['acknowledged']:
									self.logger(f"Cancel command confirmed in {cancel_result.get('wait_time', 0):.2f}s")
								else:
									self.logger(f"Cancel command not confirmed: {cancel_result.get('reason', 'unknown')}")
								
								time.sleep(2)
								experiment_active = False						
					
					else:
						self.logger(f"Non-test status received ({status}), continuing to monitor")
				
				else:
					self.logger(f"Unknown event type: {event_type} - continuing to monitor")
		
		except KeyboardInterrupt:
			self.logger("Monitoring interrupted by user")
			try:
				cancel_result = self.framework_api.cancel_experiment_with_ack(max_wait_time=5.0)
				self.logger(f"Experiment cancelled due to interruption - acknowledged: {cancel_result.get('acknowledged', False)}")
			except:
				pass
			experiment_active = False
		except Exception as e:
			self.logger(f"Error in experiment lifecycle monitoring: {e}")
			try:
				cancel_result = self.framework_api.cancel_experiment_with_ack(max_wait_time=5.0)
				self.logger(f"Experiment cancelled due to error - acknowledged: {cancel_result.get('acknowledged', False)}")
			except:
				pass
			experiment_active = False
		finally:
			if not hasattr(self, 'runStatusHistory') or not self.runStatusHistory:
				if collected_results:
					self._process_final_results_from_events(collected_results, [])
				else:
					self.runStatusHistory = ['FAILED']
			
			self.logger(f"Experiment lifecycle monitoring completed. Final status: {len(self.runStatusHistory)} results")

	def _process_final_results_from_events(self, collected_results: list, final_results: list):
		"""
		Process final results with proper TestStatus handling.
		"""
		try:
			self.runStatusHistory = []
			
			# Process collected iteration results first
			for result in collected_results:
				status = result['status']
				
				# Only include valid test results (PASS/FAIL) in flow history
				if status in [TestStatus.PASS.value, TestStatus.FAIL.value]:
					self.runStatusHistory.append(status)
				# Hardware failures are handled at the flow level, not included in node history
				elif status in [TestStatus.EXECUTION_FAIL.value, TestStatus.FAILED.value, TestStatus.PYTHON_FAIL.value]:
					self.logger(f"Hardware failure detected in iteration {result['iteration']}: {status}")
					# Don't add to runStatusHistory - let FlowTestExecutor handle flow abortion
				elif status == TestStatus.CANCELLED.value:
					self.logger(f"Iteration {result['iteration']} was cancelled")
					# Don't add to runStatusHistory - cancellation is handled at flow level
			
			# If we have final_results and no collected results, process them
			if not self.runStatusHistory and final_results:
				for result in final_results:
					if result in [TestStatus.PASS.value, TestStatus.FAIL.value]:
						self.runStatusHistory.append(result)
			
			# If no valid test results, this indicates a system issue
			if not self.runStatusHistory:
				self.logger("No valid test results found - marking as system failure")
				self.runStatusHistory = [TestStatus.FAILED.value]  # This will trigger flow abortion
			
			self.logger(f"Processed {len(collected_results)} iteration results into {len(self.runStatusHistory)} valid test results")
			
		except Exception as e:
			self.logger(f"Error processing final results: {e}")
			self.runStatusHistory = [TestStatus.FAILED.value]

	def _get_max_iterations(self):
		"""Get maximum iterations based on experiment type."""
		
		statistics =  self.framework_api.get_iteration_statistics()
		max_iterations = statistics['total_iterations']

		if max_iterations:
			return max_iterations
		
		test_type = self.Experiment.get('Test Type', 'Loops')
		
		if test_type == 'Loops':
			return self.Experiment.get('Loops', 10)
		elif test_type == 'Sweep':
			start = self.Experiment.get('Start', 0)
			end = self.Experiment.get('End', 10)
			step = self.Experiment.get('Steps', 1)
			return max(1, int((end - start) / step) + 1)
		elif test_type == 'Shmoo':
			return 50  # Default estimate for shmoo
		else:
			return 20  # Default maximum

	def _get_current_config_snapshot(self):
		"""Get current configuration snapshot for tracking"""
		if hasattr(self, 'framework_api') and self.framework_api:
			config = self.framework_api.framework.config
			return {
				'volt_IA': getattr(config, 'volt_IA', None),
				'volt_CFC': getattr(config, 'volt_CFC', None),
				'freq_ia': getattr(config, 'freq_ia', None),
				'freq_cfc': getattr(config, 'freq_cfc', None),
				'content': getattr(config, 'content', None),
				'mask': getattr(config, 'mask', None),
				'check_core': getattr(config, 'check_core', None)
			}
		return {}
	
	@abstractmethod
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""
		Abstract method for making decisions after each iteration.
		Must return 'continue', 'end', or 'cancel'.
		
		Parameters:
		- stats: Current execution statistics
		- iteration_count: Current iteration number
		- max_iterations: Maximum allowed iterations
		"""
		pass

	@abstractmethod
	def set_output_port(self):
		"""
		Abstract method for setting the output port based on the run status.
		Subclasses must implement this method to determine specific output behavior.
		"""
		pass
   
	def get_next_node(self):
		"""
		 ENHANCED: Handle unwired ports with automatic flow termination.
		
		Logic:
		- If port is wired: Follow the connection
		- If port is unwired: Terminate flow with appropriate error flag
		- Port 3 (hardware failure): Special handling with hardware error flag
		"""
		if not self.outputNodeMap:
			self.logger(f"No output node map defined for {self.Name} - terminating flow")
			return None
		
		try:
			if self.outputPort in self.outputNodeMap:
				# Port is wired - follow the connection
				nextNode = self.outputNodeMap[self.outputPort]
				
				if self.outputPort == 3:
					self.logger(f"HARDWARE FAILURE PORT (3) wired to: {nextNode.Name}")
					self.logger("Following hardware failure path instead of auto-termination")
				else:
					self.logger(f"Next node: {nextNode.Name} (Port: {self.outputPort})")
				
				return nextNode
			else:
				# Port is NOT wired - terminate flow with error flag
				self._handle_unwired_port_termination()
				return None
				
		except KeyError as e:
			self.logger(f"Output Port Error: No handler found for port {self.outputPort}. Exception: {e}")
			self._handle_unwired_port_termination()
			return None

	def _handle_unwired_port_termination(self):
		"""
		 NEW: Handle termination when a port is not wired.
		Sets appropriate error flags based on port type.
		"""
		port_descriptions = {
			0: "No Repro/Stable Content",
			1: "Solid Repro/Failures Found", 
			2: "Intermittent/Mixed Results",
			3: "Hardware Failure"
		}
		
		port_desc = port_descriptions.get(self.outputPort, f"Port {self.outputPort}")
		
		self.logger(f"UNWIRED PORT TERMINATION: Port {self.outputPort} ({port_desc}) is not wired")
		self.logger("Flow will terminate with appropriate error flag")
		
		# Set termination reason based on port type
		if self.outputPort == 3:
			self._set_termination_flag("hardware_failure", "Hardware failure detected but port 3 not wired")
		elif self.outputPort == 2:
			self._set_termination_flag("intermittent_results", "Intermittent results detected but port 2 not wired")
		elif self.outputPort == 1:
			self._set_termination_flag("repro_found", "Solid repro found but port 1 not wired")
		elif self.outputPort == 0:
			self._set_termination_flag("no_repro", "No repro found but port 0 not wired")
		else:
			self._set_termination_flag("unwired_port", f"Port {self.outputPort} not wired")

	def _set_termination_flag(self, termination_type: str, reason: str):
		"""
		NEW: Set termination flag and reason for flow executor to handle.
		"""
		# Store termination info in the node for executor to read
		self.termination_type = termination_type
		self.termination_reason = reason
		self.flow_should_terminate = True
		
		self.logger(f"Termination flag set: {termination_type} - {reason}")					
		
	def get_execution_summary(self):
		"""
		Get a summary of the execution results.
		"""
		return {
			'node_id': self.ID,
			'node_name': self.Name,
			'status_history': self.runStatusHistory,
			'execution_stats': self.execution_stats,
			'output_port': self.outputPort,
			'total_tests': len(self.runStatusHistory),
			'pass_count': self.runStatusHistory.count('PASS'),
			'fail_count': self.runStatusHistory.count('FAIL')
		}
 
	def _check_hardware_failure_threshold(self, stats) -> bool:
		"""
		Check if hardware failures exceed 40% threshold.
		Returns True if hardware failure threshold exceeded.
		"""
		total_completed = stats.get('total_completed', 0)
		execution_fail_count = stats.get('execution_fail_count', 0)
		cancelled_count = stats.get('cancelled_count', 0)
		
		if total_completed == 0:
			return False
		
		# Hardware failures include execution failures and cancellations
		hardware_failures = execution_fail_count + cancelled_count
		hardware_failure_rate = hardware_failures / total_completed
		
		self.logger(f"Hardware failure check: {hardware_failures}/{total_completed} = {hardware_failure_rate:.1%}")
		
		return hardware_failure_rate > 0.50  # 40% threshold

	def _get_failure_reproduction_pattern(self, stats) -> str:
		"""
		Analyze failure reproduction pattern using recent trend analysis.
		"""
		recent_trend = stats.get('recent_trend', 'insufficient_data')
		total_completed = stats.get('total_completed', 0)
		pass_rate = stats.get('pass_rate', 0.0)
		fail_rate = stats.get('fail_rate', 0.0)
		
		self.logger(f"Reproduction analysis - Trend: {recent_trend}, Pass: {pass_rate}%, Fail: {fail_rate}%")
		
		# Map trends to reproduction patterns
		if recent_trend == "repro":
			return "solid_repro"  # Consistent failures
		elif recent_trend == "no-repro":
			return "no_repro"     # Consistent passes
		elif recent_trend in ["flaky", "unstable", "mixed"]:
			return "intermittent" # Mixed results
		else:
			return "insufficient_data"

	def _make_base_iteration_decision(self, stats, iteration_count, max_iterations):
		"""
		Base decision logic with hardware failure detection.
		Subclasses should call this first, then add their specific logic.
		"""
		
		# Check hardware failure threshold first
		if self._check_hardware_failure_threshold(stats):
			self.logger("HARDWARE FAILURE THRESHOLD EXCEEDED - ending experiment")
			return 'end'
		
		# Check for sufficient data from status handler
		recommendation = stats.get('recommendation', 'continue')
		if recommendation in ['sufficient_data_good', 'sufficient_data_poor']:
			self.logger(f"Status handler indicates sufficient data: {recommendation}")
			return 'end'
		
		# Check iteration limits -- continue as we are waiting for step
		if iteration_count >= max_iterations:
			self.logger(f"Maximum iterations reached: {iteration_count}/{max_iterations}")
			return 'end'
		
		return None  # Let subclass decide

	def make_full_experiment_decision(self, stats, iteration_count, max_iterations):

		# Check base conditions first (hardware failures only)
		if self._check_hardware_failure_threshold(stats):
			self.logger("HARDWARE FAILURE THRESHOLD EXCEEDED - ending experiment")
			return 'end'
		
		# Check iteration limits
		if iteration_count >= max_iterations:
			self.logger(f"Maximum iterations reached: {iteration_count}/{max_iterations}")
			return 'end'
		
		return 'continue'
		
	def _set_base_output_ports(self):
		"""
		 ENHANCED: Base port setting with guaranteed hardware failure detection.
		Returns True if hardware failure port (3) was set, False otherwise.
		"""
		# Check if hardware failures exceed threshold in execution stats
		if hasattr(self, 'execution_stats') and self.execution_stats:
			if self._check_hardware_failure_threshold(self.execution_stats):
				self.outputPort = 3  # Hardware failure port
				self.logger("HARDWARE FAILURE THRESHOLD EXCEEDED - Setting port 3")
				self.logger("This will trigger immediate flow termination")
				return True
		
		# Check for hardware failure statuses in results
		hardware_statuses = [TestStatus.EXECUTION_FAIL.value, TestStatus.FAILED.value, 
						   TestStatus.PYTHON_FAIL.value, TestStatus.CANCELLED.value]
		
		hardware_failures = sum(1 for status in self.runStatusHistory if status in hardware_statuses)
		total_results = len(self.runStatusHistory)
		
		if total_results > 0 and (hardware_failures / total_results) > 0.40:
			self.outputPort = 3  # Hardware failure port
			self.logger("HARDWARE FAILURE IN RESULTS - Setting port 3")
			self.logger(f"Hardware failures: {hardware_failures}/{total_results} = {hardware_failures/total_results:.1%}")
			self.logger("This will trigger immediate flow termination")
			return True
		
		return False  # Let subclass set the port

class StartNodeFlowInstance(FlowInstance):
	"""
	Special flow instance for start nodes.
	Always succeeds and routes to port 1 by default.
	"""
	
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""
		Start nodes don't need iteration decisions - they just pass through.
		"""
		return 'end'  # Complete immediately

	def run_experiment(self):
		"""
		Start nodes don't run actual experiments - they just initialize the flow.
		"""
		self.logger(f"Starting flow execution from: {self.Name} (ID: {self.ID})")

		# Simulate a quick "experiment" that always passes
		self.runStatusHistory = ['PASS']
		
		# Set output port based on configuration or default logic
		self.set_output_port()

	def set_output_port(self):
		"""
		Start nodes can route to multiple paths based on initial conditions.
		For now, default to port 1 (success path) unless configured otherwise.
		"""
		# Check if there are multiple output connections
		if len(self.outputNodeMap) > 1:
			# For start nodes with multiple outputs, you might want to implement
			# some logic to choose the path. For now, default to port 1
			if 1 in self.outputNodeMap:
				self.outputPort = 1
			else:
				# Use the first available port
				self.outputPort = min(self.outputNodeMap.keys())
		elif len(self.outputNodeMap) == 1:
			# Only one output, use it
			self.outputPort = list(self.outputNodeMap.keys())[0]
		else:
			# No outputs (shouldn't happen for start nodes)
			self.outputPort = 0
		
		self.logger(f"Start node {self.Name} routing to port {self.outputPort}")

class EndNodeFlowInstance(FlowInstance):
	"""
	Special flow instance for end nodes.
	Terminates the flow execution.
	"""
	
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""
		End nodes don't need iteration decisions - they terminate the flow.
		"""
		print(' End Node reached, finishing Flow')
		return 'end'  # Complete immediately

	def run_experiment(self):
		"""
		End nodes don't run actual experiments - they just terminate the flow.
		"""
		self.logger(f"Flow execution completed at: {self.Name} (ID: {self.ID})")
		
		# Simulate a quick "experiment" that always passes
		self.runStatusHistory = ['PASS']
		
		# Set output port (should be none for end nodes)
		self.set_output_port()

	def set_output_port(self):
		"""
		End nodes have no output - they terminate the flow.
		"""
		self.outputPort = None  # No further routing
		self.logger(f"End node {self.Name} - flow execution terminated")

	def get_next_node(self):
		"""
		End nodes always return None to terminate the flow.
		"""
		self.logger(f"Flow terminated at end node: {self.Name}")
		return None

class SingleFailFlowInstance(FlowInstance):
	"""
	Debugging flow: Look for any failure occurrence.
	Port 0: No failures found (content doesn't cause failures)
	Port 1: Failures found (content can cause failures)
	Port 2: Intermittent failures (unreliable repro)
	Port 3: Hardware failures (>40% threshold)
	"""
	
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""
		Stop as soon as we detect any failure pattern.
		"""
		# Check base conditions first
		base_decision = self._make_base_iteration_decision(stats, iteration_count, max_iterations)
		if base_decision:
			return base_decision
		
		total_completed = stats.get('total_completed', 0)
		fail_rate = stats.get('fail_rate', 0.0)
		recent_trend = stats.get('recent_trend', 'insufficient_data')
		
		if total_completed >= 3:
			if recent_trend == "no-repro":
				self.logger("Consistent failures detected - ending")
				return 'end'
			elif fail_rate > 0 and total_completed >= 5:
				self.logger("Some failures detected - ending for analysis")
				return 'end'
			elif total_completed >= 5 and fail_rate == 0:
				self.logger("No failures after sufficient testing - ending")
				return 'end'
		
		return 'continue'

	def set_output_port(self):
		"""
		Route based on failure detection.
		"""
		# Check hardware failure port first
		if self._set_base_output_ports():
			return
		
		if hasattr(self, 'execution_stats') and self.execution_stats:
			pattern = self._get_failure_reproduction_pattern(self.execution_stats)
			fail_rate = self.execution_stats.get('fail_rate', 0.0)
			
			if pattern == "solid_repro":
				self.outputPort = 1  # Consistent failures found
			elif pattern == "no_repro":
				self.outputPort = 0  # No failures found
			else:  # intermittent patterns
				self.outputPort = 2  # Intermittent failures
		else:
			# Fallback analysis
			has_failures = 'FAIL' in self.runStatusHistory
			self.outputPort = 1 if has_failures else 0

		# [DONE] Validate port is wired (this will be checked in get_next_node())
		self.logger('='*50)
		self.logger(f' RunStatus: {self.runStatusHistory}')
		self.logger(f' SingleFail Node Complete - Port: {self.outputPort}')
		
		# [DONE] Check if port is wired and log accordingly
		if hasattr(self, 'outputNodeMap') and self.outputNodeMap:
			if self.outputPort in self.outputNodeMap:
				next_node = self.outputNodeMap[self.outputPort]
				self.logger(f' Port {self.outputPort} is wired to: {next_node.Name}')
			else:
				self.logger(f' WARNING: Port {self.outputPort} is NOT wired - flow will terminate')
		
		self.logger('='*50)		

class AllFailFlowInstance(FlowInstance):
	"""
	Debugging flow: Look for solid failure reproduction.
	Port 0: All passes (no repro found)
	Port 1: All fails (solid repro found) 
	Port 2: Mixed results (intermittent/flaky)
	Port 3: Hardware failures (>40% threshold)
	"""

	def run_experiment(self):
		"""Main experiment runner for AllFailFlowInstance with debugging"""
		print(f"[CONFIG] DEBUG: AllFailFlowInstance - Starting experiment: {self.Name} (Type: {type(self).__name__})")
		
		# Call parent run_experiment which handles experiment tracking
		super().run_experiment()
		
		print(f"[CONFIG] DEBUG: AllFailFlowInstance - Experiment complete. Final result: {getattr(self, 'runStatusHistory', 'Unknown')}")
		print(f"[CONFIG] DEBUG: AllFailFlowInstance - Output port: {getattr(self, 'outputPort', 'Unknown')}")
		
		# Debug: Check if experiment tracker received our data
		if self.experiment_tracker and hasattr(self.experiment_tracker, 'current_experiment_data'):
			current_data = self.experiment_tracker.current_experiment_data
			print(f"[CONFIG] DEBUG: AllFailFlowInstance - Tracker has our data: {current_data.get('node_name')} (Type: {current_data.get('node_type')})")
				
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""
		Continue until we can determine failure reproduction pattern.
		"""
		self.logger('='*50)
		self.logger(f' AllFail Decision Stats: {stats}')
		self.logger(f' Iterations count: {iteration_count}')
		self.logger(f' Iterations Max: {max_iterations}')

		# Check base conditions first (hardware failures, limits)
		base_decision = self._make_base_iteration_decision(stats, iteration_count, max_iterations)
		if base_decision:
			return base_decision
		
		total_completed = stats.get('total_completed', 0)
		pass_rate = stats.get('pass_rate', 0.0)
		fail_rate = stats.get('fail_rate', 0.0)
		recent_trend = stats.get('recent_trend', 'insufficient_data')
		
		# For debugging, we want to establish a clear pattern
		if total_completed >= 5:
			if recent_trend == "repro":
				self.logger("Solid failure reproduction detected - ending")
				return 'end'
			elif recent_trend == "no-repro":
				self.logger("No failure reproduction (all passes) - ending")
				return 'end'
			elif total_completed >= 10 and recent_trend in ["flaky", "unstable", "mixed"]:
				self.logger("Intermittent pattern established - ending")
				return 'end'
		
		# Need more data for clear pattern
		if total_completed >= 15:
			self.logger("Sufficient iterations for pattern analysis - ending")
			return 'end'
		
		self.logger("Continuing - need clearer reproduction pattern")
		return 'continue'
 
	def set_output_port(self):
		"""
		Route based on failure reproduction pattern with port validation.
		"""
		# Check hardware failure port first
		if self._set_base_output_ports():
			return
		
		# Analyze reproduction pattern
		if hasattr(self, 'execution_stats') and self.execution_stats:
			pattern = self._get_failure_reproduction_pattern(self.execution_stats)
			pass_rate = self.execution_stats.get('pass_rate', 0.0)
			fail_rate = self.execution_stats.get('fail_rate', 0.0)
			
			self.logger(f"Reproduction pattern: {pattern}, Pass: {pass_rate}%, Fail: {fail_rate}%")
			
			if pattern == "solid_repro":
				self.outputPort = 1  # Solid failure reproduction found
				self.logger("Port 1 - Solid failure reproduction detected")
			elif pattern == "no_repro":
				self.outputPort = 0  # No failures found (no repro)
				self.logger("Port 0 - No failure reproduction (all passes)")
			else:  # intermittent or insufficient_data
				self.outputPort = 2  # Mixed/intermittent results
			valid_results = [s for s in self.runStatusHistory if s in ['PASS', 'FAIL']]
			
			if not valid_results:
				self.outputPort = 3  # No valid results - hardware issue
			elif all(s == 'FAIL' for s in valid_results):
				self.outputPort = 1  # All fails - solid repro
			elif all(s == 'PASS' for s in valid_results):
				self.outputPort = 0  # All passes - no repro
			else:
				self.outputPort = 2  # Mixed results
		
		# Validate port is wired (this will be checked in get_next_node())
		self.logger('='*50)
		self.logger(f' RunStatus: {self.runStatusHistory}')
		self.logger(f' AllFail Node Complete - Port: {self.outputPort}')
		
		# Check if port is wired and log accordingly
		if hasattr(self, 'outputNodeMap') and self.outputNodeMap:
			if self.outputPort in self.outputNodeMap:
				next_node = self.outputNodeMap[self.outputPort]
				self.logger(f' Port {self.outputPort} is wired to: {next_node.Name}')
			else:
				self.logger(f' WARNING: Port {self.outputPort} is NOT wired - flow will terminate')
		
		self.logger('='*50)

class MajorityFailFlowInstance(FlowInstance):
	"""
	Debugging flow: Analyze failure rate patterns.
	Port 0: Low failure rate (<30% - content mostly stable)
	Port 1: High failure rate (>70% - content causes frequent failures)
	Port 2: Moderate failure rate (30-70% - intermittent issues)
	Port 3: Hardware failures (>40% threshold)
	"""
	
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""
		Continue until we have statistical confidence in failure patterns.
		"""
		# Check base conditions first
		base_decision = self._make_base_iteration_decision(stats, iteration_count, max_iterations)
		if base_decision:
			return base_decision

		total_completed = stats.get('total_completed', 0)
		fail_rate = stats.get('fail_rate', 0.0)
		recent_trend = stats.get('recent_trend', 'insufficient_data')
		
		# For statistical confidence in debugging
		if total_completed >= 10:
			if recent_trend in ["repro", "no-repro"]:
				self.logger(f"Clear pattern established: {recent_trend} - ending")
				return 'end'
			elif total_completed >= 15:
				self.logger("Sufficient data for failure rate analysis - ending")
				return 'end'
		
		return 'continue'

	def set_output_port(self):
		"""
		Route based on failure rate analysis for debugging.
		"""
		# Check hardware failure port first
		if self._set_base_output_ports():
			return
		
		if hasattr(self, 'execution_stats') and self.execution_stats:
			fail_rate = self.execution_stats.get('fail_rate', 0.0)
			pattern = self._get_failure_reproduction_pattern(self.execution_stats)
			
			self.logger(f"Failure rate analysis: {fail_rate}%, Pattern: {pattern}")
			
			if fail_rate >= 70:
				self.outputPort = 1  # High failure rate - content causes frequent failures
			elif fail_rate <= 30:
				self.outputPort = 0  # Low failure rate - content mostly stable
			else:
				self.outputPort = 2  # Moderate failure rate - intermittent issues
		else:
			# Fallback analysis
			fail_count = self.runStatusHistory.count('FAIL')
			total_count = len(self.runStatusHistory)
			fail_rate = (fail_count / total_count * 100) if total_count > 0 else 0
			
			if fail_rate >= 70:
				self.outputPort = 1
			elif fail_rate <= 30:
				self.outputPort = 0
			else:
				self.outputPort = 2

		# [DONE] Validate port is wired (this will be checked in get_next_node())
		self.logger('='*50)
		self.logger(f' RunStatus: {self.runStatusHistory}')
		self.logger(f' MajorityFail Node Complete - Port: {self.outputPort}')
		
		# [DONE] Check if port is wired and log accordingly
		if hasattr(self, 'outputNodeMap') and self.outputNodeMap:
			if self.outputPort in self.outputNodeMap:
				next_node = self.outputNodeMap[self.outputPort]
				self.logger(f' Port {self.outputPort} is wired to: {next_node.Name}')
			else:
				self.logger(f' WARNING: Port {self.outputPort} is NOT wired - flow will terminate')
		
		self.logger('='*50)

class AdaptiveFlowInstance(FlowInstance):
	"""
	Enhanced adaptive flow that analyzes previous AllFailFlowInstance results and generates optimized experiments.
	"""
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.analyzed_data = {}
		self.optimized_config = {}
	
	def run_experiment(self):
		"""Analyze previous data and generate optimized configuration - NO ACTUAL EXPERIMENT EXECUTION"""
		print("[CONFIG] DEBUG: AdaptiveFlowInstance - Starting configuration analysis (NO experiment execution)")
		self.logger(f"Starting Adaptive Analysis: {self.Name} (ID: {self.ID})")
		
		# DEBUG: Show original experiment config
		print("[CONFIG] DEBUG: AdaptiveFlowInstance - Original experiment config:")
		for key, value in self.Experiment.items():
			if value is not None:
				print(f"[CONFIG] DEBUG:   {key}: {value}")
		
		# Analyze previous experiment data (only AllFailFlowInstance)
		self._analyze_previous_experiments()
		
		# Generate optimized configuration
		self._generate_optimized_config()
		
		# Apply optimized configuration
		self._apply_optimized_config()
		
	   # DEBUG: Show final optimized config that will be passed to next node
		print("[CONFIG] DEBUG: AdaptiveFlowInstance - FINAL OPTIMIZED CONFIG to pass to next node:")
		for key, value in self.optimized_config.items():
			if value is not None:
				print(f"[CONFIG] DEBUG:   {key}: {value}")
		
		# Set successful completion WITHOUT running actual experiment
		self.runStatusHistory = ['PASS']
		self.set_output_port()
		
		# Complete experiment tracking (but mark as configuration-only)
		if self.experiment_tracker:
			test_folder = None  # No test folder since no experiment was run
			self.experiment_tracker.complete_experiment(
				final_result='CONFIG_PASSED',  # Special result for config-only nodes
				output_port=self.outputPort,
				test_folder=test_folder
			)
		
		print("[CONFIG] DEBUG: AdaptiveFlowInstance - Configuration analysis complete, ready to pass config to next node")

	def _analyze_previous_experiments(self):
		"""Analyze AllFailFlowInstance experiments for patterns"""
		print("[CONFIG] DEBUG: AdaptiveFlowInstance - Analyzing previous experiments...")
		
		if not self.experiment_tracker:
			print("[CONFIG] DEBUG: AdaptiveFlowInstance - No experiment tracker available")
			self.logger("No experiment tracker available for adaptive analysis")
			return
	
		# Debug: Show current experiment history
		self.experiment_tracker.debug_show_experiment_history()	

		# Get adaptive analysis data (only from AllFailFlowInstance)
		analysis_data = self.experiment_tracker.get_adaptive_analysis_data('AllFailFlowInstance')
		
		print(f"[CONFIG] DEBUG: AdaptiveFlowInstance - Analysis data status: {analysis_data.get('status')}")
		
		if analysis_data['status'] == 'no_data':
			print("[CONFIG] DEBUG: AdaptiveFlowInstance - No AllFailFlowInstance data available - using default configuration")
			self.logger("No AllFailFlowInstance data available - using default configuration")
			self.analyzed_data = {'use_default': True}
			return
		
		self.analyzed_data = analysis_data
		
		# DEBUG: Show what we found
		source_exp = analysis_data.get('source_experiment', {})
		print(f"[CONFIG] DEBUG: AdaptiveFlowInstance - Source experiment: {source_exp.get('node_name')} (Port: {source_exp.get('output_port')})")
		print(f"[CONFIG] DEBUG: AdaptiveFlowInstance - Recovery potential: {analysis_data.get('recovery_potential')}")
		print(f"[CONFIG] DEBUG: AdaptiveFlowInstance - Voltage type context: {analysis_data.get('voltage_type_context')}")
		
		# Show recommended config
		recommended = analysis_data.get('recommended_config', {})
		if recommended:
			print("[CONFIG] DEBUG: AdaptiveFlowInstance - Recommended config from analysis:")
			for key, value in recommended.items():
				if value is not None:
					print(f"[CONFIG] DEBUG:   {key}: {value}")
		
		# Log sweep insights if available
		sweep_insights = analysis_data.get('sweep_insights')
		if sweep_insights:
			print(f"[CONFIG] DEBUG: AdaptiveFlowInstance - Sweep insights: {sweep_insights['sweep_type']} {sweep_insights['sweep_domain']} - {sweep_insights['sensitivity_pattern']}")
			print(f"[CONFIG] DEBUG: AdaptiveFlowInstance - Sweep recommendation: {sweep_insights['recommendation']}")
	
	def _generate_optimized_config(self):
		"""Generate optimized configuration based on AllFailFlowInstance analysis - EXPERIMENT DATA ONLY"""
		# Start with current experiment configuration (keep node's own settings)
		self.optimized_config = {}
		
		if self.analyzed_data.get('use_default'):
			print("[CONFIG] DEBUG: AdaptiveFlowInstance - Using default configuration - no previous data available")
			self.logger("Using default configuration - no previous data available")
			return
		
		# Get ONLY experiment configuration from analysis (not metadata)
		recommended_config = self.analyzed_data.get('recommended_config', {})
		if recommended_config:
			# Filter to only include experiment parameters (not execution metadata)
			experiment_only_config = self._filter_to_experiment_parameters(recommended_config)
			self.optimized_config.update(experiment_only_config)
			print("[CONFIG] DEBUG: AdaptiveFlowInstance - Applied filtered experiment config from analysis")
		
		# Apply sweep-based optimizations
		sweep_insights = self.analyzed_data.get('sweep_insights')
		if sweep_insights:
			self._apply_sweep_optimizations(sweep_insights)
		
		# Apply voltage type optimizations
		voltage_type_context = self.analyzed_data.get('voltage_type_context', 'vbump')
		self._apply_voltage_type_optimizations(voltage_type_context)

	def _filter_to_experiment_parameters(self, config_dict):
		"""Filter configuration to only include experiment parameters (not execution metadata)"""
		experiment_parameters = {
			# Test content and configuration
			'Content',
			'Configuration (Mask)',
			'Check Core',
			
			# Voltage and frequency settings
			'Voltage IA',
			'Voltage CFC', 
			'Frequency IA',
			'Frequency CFC',
			'Voltage Type',

			# Mode Specific
			'Loops',
			'Type', 
			'Domain',
			'Start',
			'End',
			'Steps',
			'ShmooFile', 
			'ShmooLabel',

			# Test execution settings
			'Test Time',
			'Reset',
			'Reset on PASS',
			'FastBoot',
			
			# File paths and strings
			'TTL Folder',
			'Scripts File',
			'Bios File',
			'Fuse File',
			'Post Process',
			'Pass String',
			'Fail String',
			
			# Hardware settings
			'COM Port',
			'IP Address',
			'600W Unit',
			'Pseudo Config',
			'Boot Breakpoint',
			'Disable 2 Cores',
			'Core License',
			
			# All other experiment settings (Linux, Dragon, etc.)
			'Linux Pre Command', 'Linux Post Command', 'Startup Linux', 'Linux Path',
			'Linux Content Wait Time', 'Linux Content Line 0', 'Linux Content Line 1',
			'Linux Content Line 2', 'Linux Content Line 3', 'Linux Content Line 4',
			'Linux Content Line 5', 'Linux Content Line 6','Linux Content Line 7',
			'Linux Content Line 8','Linux Content Line 9','Linux Pass String', 'Linux Fail String',
			'Dragon Pre Command', 'Dragon Post Command', 'Startup Dragon', 'ULX Path',
			'ULX CPU', 'Product Chop', 'VVAR0', 'VVAR1', 'VVAR2', 'VVAR3', 'VVAR_EXTRA',
			'Dragon Content Path', 'Dragon Content Line', 'Stop on Fail',
			'Merlin Name', 'Merlin Drive', 'Merlin Path', 'Post Process',
			'Test Mode', 'Visual ID', 'Bucket', 'Experiment', 'Test Number'
		}
		
		filtered_config = {}
		for key, value in config_dict.items():
			if key in experiment_parameters and value is not None:
				filtered_config[key] = value
				print(f"[CONFIG] DEBUG: AdaptiveFlowInstance - Including experiment parameter: {key} = {value}")
		
		return filtered_config
	
	def _apply_sweep_optimizations(self, sweep_insights):
		"""Apply optimizations based on sweep insights"""
		sweep_type = sweep_insights['sweep_type']
		sweep_domain = sweep_insights['sweep_domain']
		pattern = sweep_insights['sensitivity_pattern']
		safe_values = sweep_insights.get('safe_values', [])
		voltage_type = sweep_insights.get('voltage_type_context', 'vbump')
		
		self.logger(f"Applying sweep optimizations: {sweep_type} {sweep_domain} - {pattern} ({voltage_type})")
		
		if safe_values and pattern in ['threshold_sensitivity', 'upper_threshold_sensitivity']:
			# Use safe values from sweep analysis
			if sweep_type == 'voltage':
				if sweep_domain == 'ia':
					safe_value = min(safe_values) if pattern == 'threshold_sensitivity' else max(safe_values)
					self.optimized_config['Voltage IA'] = safe_value
					self.logger(f"Set IA voltage to safe value: {safe_value}")
				elif sweep_domain == 'cfc':
					safe_value = min(safe_values) if pattern == 'threshold_sensitivity' else max(safe_values)
					self.optimized_config['Voltage CFC'] = safe_value
					self.logger(f"Set CFC voltage to safe value: {safe_value}")
				
				# Ensure voltage type is preserved
				self.optimized_config['Voltage Type'] = voltage_type
				
			elif sweep_type == 'frequency':
				if sweep_domain == 'ia':
					safe_value = min(safe_values) if pattern == 'threshold_sensitivity' else max(safe_values)
					self.optimized_config['Frequency IA'] = safe_value
					self.logger(f"Set IA frequency to safe value: {safe_value}")
				elif sweep_domain == 'cfc':
					safe_value = min(safe_values) if pattern == 'threshold_sensitivity' else max(safe_values)
					self.optimized_config['Frequency CFC'] = safe_value
					self.logger(f"Set CFC frequency to safe value: {safe_value}")
	
	def _apply_voltage_type_optimizations(self, voltage_type_context):
		"""Apply voltage type specific optimizations"""
		current_voltage_type = self.optimized_config.get('Voltage Type', 'vbump')
		
		# If previous experiment used PPVC and had good results, consider using it
		if voltage_type_context == 'PPVC':
			recovery_potential = self.analyzed_data.get('recovery_potential', 'unknown')
			if recovery_potential in ['high', 'medium']:
				self.optimized_config['Voltage Type'] = 'PPVC'
				self.logger(f"Applied PPVC voltage type based on previous success (recovery potential: {recovery_potential})")
				self.logger("Note: PPVC reduces voltage guardbands on all domains (IA and CFC)")
			else:
				self.logger(f"Keeping current voltage type ({current_voltage_type}) - previous PPVC had low recovery potential")
		else:
			# Keep the voltage type from previous successful experiment
			self.optimized_config['Voltage Type'] = voltage_type_context
			self.logger(f"Applied voltage type from previous experiment: {voltage_type_context}")
	
	def _merge_experiment_config(self, recommended_config):
		"""Merge recommended configuration into experiment config"""
		for key, value in recommended_config.items():
			if value is not None:
				self.optimized_config[key] = value
   
	def _apply_optimized_config(self):
		"""Apply optimized configuration to current experiment - keep node's Test Name"""
		print("[CONFIG] DEBUG: AdaptiveFlowInstance - Applying optimized configuration...")
		
		# Show before
		print("[CONFIG] DEBUG: AdaptiveFlowInstance - BEFORE applying optimized config:")
		key_params = ['Test Name', 'Voltage IA', 'Voltage CFC', 'Frequency IA', 'Frequency CFC', 'Voltage Type', 'Content', 'Configuration (Mask)']
		for key in key_params:
			current_value = self.Experiment.get(key)
			if current_value is not None:
				print(f"[CONFIG] DEBUG:   {key}: {current_value}")
		
		# Keep the node's original Test Name
		original_test_name = self.Experiment.get('Test Name', self.Name)
		
		# Apply optimized config
		self.Experiment.update(self.optimized_config)
		
		# Restore the node's Test Name
		self.Experiment['Test Name'] = original_test_name
		print(f"[CONFIG] DEBUG: AdaptiveFlowInstance - Kept original Test Name: {original_test_name}")
		
		self.logger("Applied optimized configuration")
		
		print("[CONFIG] DEBUG: AdaptiveFlowInstance - AFTER applying optimized config:")
		for key in key_params:
			new_value = self.Experiment.get(key)
			if new_value is not None:
				print(f"[CONFIG] DEBUG:   {key}: {new_value}")
				
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""Intelligent decision making based on analysis"""
		base_decision = self._make_base_iteration_decision(stats, iteration_count, max_iterations)
		if base_decision:
			return base_decision
		
		# Use adaptive logic based on previous data
		recovery_potential = self.analyzed_data.get('recovery_potential', 'unknown')
		
		if recovery_potential == 'high':
			# If we expect recovery, look for consistent passes
			if stats.get('recent_trend') == 'no-repro' and iteration_count >= 3:
				self.logger("High recovery potential confirmed - ending early")
				return 'end'
		elif recovery_potential == 'low':
			# If recovery is unlikely, look for solid repro quickly
			if stats.get('recent_trend') == 'repro' and iteration_count >= 5:
				self.logger("Low recovery potential - solid repro found")
				return 'end'
		
		return 'continue'
	
	def set_output_port(self):
		"""Set output port based on analysis results"""
		if self._set_base_output_ports():
			return
		
		# Always output optimized configuration through port 0
		self.outputPort = 0
		
		self.logger('='*50)
		self.logger(' Adaptive Analysis Complete')
		self.logger(f' Source: {self.analyzed_data.get("source_experiment", {}).get("node_name", "Default")}')
		self.logger(f' Recovery Potential: {self.analyzed_data.get("recovery_potential", "unknown")}')
		self.logger(f' Voltage Type Applied: {self.optimized_config.get("Voltage Type", "vbump")}')
		self.logger(f' AdaptiveFlow Node Complete - Port: {self.outputPort}')
		self.logger('='*50)
	
class CharacterizationFlowInstance(FlowInstance):
	"""
	Characterization flow for voltage/frequency sweeps using previous node configuration.
	"""
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.inherited_config = {}
		self.characterization_results = []
		self.previous_node_config = {}
		self.test_execution_config = {}

	def run_experiment(self):
		"""Run characterization with inherited configuration from previous connected node"""
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Starting characterization with inherited config")
		self.logger(f"Starting Unit Failure Characterization: {self.Name} (ID: {self.ID})")
		
		# DEBUG: Show original experiment config BEFORE inheritance
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - ORIGINAL experiment config (before inheritance):")
		for key, value in self.Experiment.items():
			if value is not None:
				print(f"[DEBUG] DEBUG:   {key}: {value}")
		
		# Extract test execution parameters from own configuration
		self._extract_test_execution_config()
		
		# DEBUG: Show extracted test execution config
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Extracted test execution config:")
		for key, value in self.test_execution_config.items():
			print(f"[DEBUG] DEBUG:   {key}: {value}")
		
		# Get configuration from previous connected node
		self._inherit_previous_node_configuration()
		
		# DEBUG: Show inherited config from previous node
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Inherited config from previous node:")
		for key, value in self.previous_node_config.items():
			if value is not None:
				print(f"[DEBUG] DEBUG:   {key}: {value}")
		
		# Merge previous node config with test execution config
		self._apply_inherited_configuration()
		
		# DEBUG: Show FINAL config that will be used for characterization
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - FINAL CONFIG for characterization experiment:")
		for key, value in self.Experiment.items():
			if value is not None:
				print(f"[DEBUG] DEBUG:   {key}: {value}")
		
		# DEBUG: Show key differences
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Key configuration inheritance summary:")
		key_params = ['Content', 'Voltage IA', 'Voltage CFC', 'Frequency IA', 'Frequency CFC', 'Voltage Type', 'Configuration (Mask)']
		for param in key_params:
			inherited_value = self.previous_node_config.get(param)
			final_value = self.Experiment.get(param)
			if inherited_value is not None:
				print(f"[DEBUG] DEBUG:   {param}: inherited '{inherited_value}' -> final '{final_value}'")
		
		# Now run the actual characterization experiment
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Starting ACTUAL experiment execution with inherited config")
		super().run_experiment()
		
		# Analyze characterization results for failure patterns
		self._analyze_characterization_results()
		
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Characterization experiment complete")

	def _extract_test_execution_config(self):
		"""Extract only test execution parameters from own experiment configuration"""
		# Test Type and associated parameters that control HOW the test runs
		test_type = self.Experiment.get('Test Type', 'Loops')
		volt_type = self.Experiment.get('Voltage Type', 'vbump')
		volt_ia = self.Experiment.get('Voltage IA', None)
		volt_cfc = self.Experiment.get('Voltage CFC', None)
		freq_ia = self.Experiment.get('Frequency IA', None)
		freq_cfc = self.Experiment.get('Frequency CFC', None)

		self.test_execution_config = {
			'Test Type': test_type,
			'Voltage Type':volt_type,
			'Voltage IA':volt_ia, 
			'Voltage CFC':volt_cfc, 
			'Frequency IA':freq_ia, 
			'Frequency CFC':freq_cfc
		}
		
		# Extract parameters based on test type
		if test_type == 'Sweep':
			sweep_params = ['Type', 'Domain', 'Start', 'End', 'Steps']
			for param in sweep_params:
				if param in self.Experiment:
					self.test_execution_config[param] = self.Experiment[param]
			
			self.logger(f"Extracted Sweep execution config: {self.test_execution_config}")
		
		elif test_type == 'Loops':
			if 'Loops' in self.Experiment:
				self.test_execution_config['Loops'] = self.Experiment['Loops']
			
			self.logger(f"Extracted Loops execution config: {self.test_execution_config}")
		
		elif test_type == 'Shmoo':
			shmoo_params = ['ShmooFile', 'ShmooLabel']
			for param in shmoo_params:
				if param in self.Experiment:
					self.test_execution_config[param] = self.Experiment[param]
			
			self.logger(f"Extracted Shmoo execution config: {self.test_execution_config}")
		
		else:
			self.logger(f"Unknown test type: {test_type} - using default execution config")

	def _inherit_previous_node_configuration(self):
		"""Inherit ONLY experiment configuration from the most recent connected node (filter out execution metadata)"""
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Inheriting EXPERIMENT CONFIG ONLY from previous node...")
		
		if not self.experiment_tracker:
			print("[DEBUG] DEBUG: CharacterizationFlowInstance - No experiment tracker available - cannot inherit config")
			self.logger("No experiment tracker available - cannot inherit previous node configuration")
			return
		
		previous_experiments = self.experiment_tracker.get_previous_experiment_data()
		
		if not previous_experiments:
			print("[DEBUG] DEBUG: CharacterizationFlowInstance - No previous experiments found")
			self.logger("No previous experiments found - using default configuration")
			return
		
		# Get the most recent experiment (last connected node)
		latest_experiment = previous_experiments[-1]
		
		print(f"[DEBUG] DEBUG: CharacterizationFlowInstance - Found previous experiment: {latest_experiment['node_name']} (Type: {latest_experiment['node_type']})")
		print(f"[DEBUG] DEBUG: CharacterizationFlowInstance - Previous node output port: {latest_experiment.get('output_port', 'unknown')}")
		
		self.logger(f"Inheriting configuration from previous node: {latest_experiment['node_name']}")
		self.logger(f"Previous node type: {latest_experiment['node_type']}")
		self.logger(f"Previous node output port: {latest_experiment.get('output_port', 'unknown')}")
		
		# Get ONLY the experiment configuration (not execution metadata)
		previous_experiment_config = latest_experiment.get('experiment_config', {})
		
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Raw previous experiment config:")
		for key, value in previous_experiment_config.items():
			if value is not None:
				print(f"[DEBUG] DEBUG:   {key}: {value}")
		
		# Filter to only include actual experiment parameters (not execution metadata)
		experiment_params_only = self._filter_experiment_parameters(previous_experiment_config)
		
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Filtered experiment parameters only:")
		for key, value in experiment_params_only.items():
			if value is not None:
				print(f"[DEBUG] DEBUG:   {key}: {value}")
		
		# Also get the runtime configuration from iterations if available (but filter it too)
		iterations = latest_experiment.get('iterations', [])
		runtime_config = {}
		
		# Don't Really need this
		if iterations:
			# Use the configuration from the first iteration as it contains the actual runtime values
			first_iteration = iterations[0]
			config_snapshot = first_iteration.get('config_snapshot', {})
			
			print("[DEBUG] DEBUG: CharacterizationFlowInstance - Raw runtime config from first iteration:")
			for key, value in config_snapshot.items():
				if value is not None:
					print(f"[DEBUG] DEBUG:   {key}: {value}")
			
			# Convert config snapshot to experiment format and filter
			#runtime_config_raw = self._convert_config_snapshot_to_experiment_format(config_snapshot)
			#runtime_config = self._filter_experiment_parameters(runtime_config_raw)
			
			print("[DEBUG] DEBUG: CharacterizationFlowInstance - Filtered runtime config:")
			for key, value in runtime_config.items():
				if value is not None:
					print(f"[DEBUG] DEBUG:   {key}: {value}")
			
			self.logger(f"Found runtime configuration from {len(iterations)} iterations")
		
		# Merge experiment config with runtime config (runtime takes precedence)
		# Both are already filtered to experiment parameters only
		self.previous_node_config = experiment_params_only.copy()
		#self.previous_node_config.update(runtime_config)
		
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - FINAL inherited experiment config (filtered):")
		for key, value in self.previous_node_config.items():
			if value is not None:
				print(f"[DEBUG] DEBUG:   {key}: {value}")
		
		# Log what we inherited
		self._log_inherited_configuration()
		self._log_inheritance_summary()

	def _filter_experiment_parameters(self, config_dict):
		"""Filter configuration to only include actual experiment parameters, excluding execution metadata and node-specific fields"""
		
		# Define fields that should NOT be inherited (keep node's own configuration)
		node_specific_fields = {
			'Test Name',  # Don't inherit Test Name - use node's own
			'Voltage Type',
			'Voltage IA', 
			'Voltage CFC',
			'Frequency IA',
			'Frequency CFC',
			'Loops',
			'Type',
			'Domain', 
			'Start',
			'End',
			'Steps',
			'ShmooFile',
			'ShmooLabel',
			'Test Type'  # Also keep the node's test type
		}
		
		# Define what we want to inherit (actual experiment configuration)
		experiment_parameters = {
			# Test content and configuration - THESE ARE THE MAIN THINGS TO INHERIT
			'Content',
			'Configuration (Mask)',
			'Check Core',
			
			# Test execution settings (but not voltage/frequency values)
			'Test Time',
			'Reset',
			'Reset on PASS',
			'FastBoot',
			
			# File paths and strings
			'TTL Folder',
			'Scripts File',
			'Bios File',
			'Fuse File',
			'Post Process',
			'Pass String',
			'Fail String',
			
			# Hardware settings
			'COM Port',
			'IP Address',
			'600W Unit',
			'Pseudo Config',
			'Boot Breakpoint',
			'Disable 2 Cores',
			'Core License',
			
			# Linux settings
			'Linux Pre Command',
			'Linux Post Command',
			'Startup Linux',
			'Linux Path',
			'Linux Content Wait Time',
			'Linux Content Line 0',
			'Linux Content Line 1',
			'Linux Content Line 2',
			'Linux Content Line 3',
			'Linux Content Line 4',
			'Linux Content Line 5',
			'Linux Content Line 6',
			'Linux Content Line 7',
			'Linux Content Line 8',
			'Linux Content Line 9',
			'Linux Pass String',
			'Linux Fail String',
			
			# Dragon settings
			'Dragon Pre Command',
			'Dragon Post Command',
			'Startup Dragon',
			'ULX Path',
			'ULX CPU',
			'Product Chop',
			'VVAR0',
			'VVAR1',
			'VVAR2',
			'VVAR3',
			'VVAR_EXTRA',
			'Dragon Content Path',
			'Dragon Content Line',
			'Stop on Fail',
			'Merlin Name',
			'Merlin Drive',
			'Merlin Path',
			
			# Test mode settings
			'Test Mode',
			'Visual ID',
			'Bucket',
			'Experiment',
			'Test Number'
		}
		
		# Define what we DON'T want to inherit (execution metadata and results)
		execution_metadata = {
			# Execution results and timing
			'executed',
			'execution_status',
			'execution_timestamp',
			'start_time',
			'end_time',
			'duration_seconds',
			'final_result',
			'output_port',
			
			# Statistics and counts
			'total_iterations',
			'pass_count',
			'fail_count',
			'other_count',
			'pass_rate_percent',
			'result_summary',
			
			# File paths from execution
			'test_folder',
			'summary_file',
			
			# Node metadata
			'node_id',
			'node_type',
			
			# Sweep results (not sweep configuration)
			'sweep_total_points',
			'sweep_failure_points', 
			'sweep_pass_points',
			'sweep_sensitivity_pattern',
			'sweep_sensitivity_description',
			'sweep_recommendation',
			
			# Failure analysis results
			'failure_patterns',
			'failure_patterns_count',
			'recovery_indicators',
			'recovery_indicators_count'
		}
		
		# Filter the configuration
		filtered_config = {}
		
		for key, value in config_dict.items():
			# Clean the key for comparison (remove config_ prefix if present)
			clean_key = key.replace('config_', '').replace('_', ' ').title()
			
			# Also check original key format
			original_key_check = key.lower().replace('_', '').replace(' ', '')
			
			# Check if this is a node-specific field that should NOT be inherited
			should_exclude_node_specific = False
			for node_field in node_specific_fields:
				node_field_check = node_field.lower().replace('_', '').replace(' ', '').replace('(', '').replace(')', '')
				if (node_field == key or 
					node_field == clean_key or 
					node_field_check == original_key_check or
					node_field.lower().replace(' ', '_') == key.lower()):
					should_exclude_node_specific = True
					print(f"[DEBUG] DEBUG: CharacterizationFlowInstance - EXCLUDING node-specific field: {key} (matches {node_field})")
					break
			
			if should_exclude_node_specific:
				continue
			
			# Check if this is an experiment parameter we want to keep
			should_include = False
			
			# Check against experiment parameters list
			for param in experiment_parameters:
				param_check = param.lower().replace('_', '').replace(' ', '').replace('(', '').replace(')', '')
				if (param == key or 
					param == clean_key or 
					param_check == original_key_check or
					param.lower().replace(' ', '_') == key.lower()):
					should_include = True
					break
			
			# Explicitly exclude execution metadata
			for metadata in execution_metadata:
				metadata_check = metadata.lower().replace('_', '').replace(' ', '')
				if (metadata == key.lower() or 
					metadata_check == original_key_check):
					should_include = False
					break
			
			if should_include and value is not None:
				# Use the original experiment format key name
				filtered_config[key] = value
				print(f"[DEBUG] DEBUG: CharacterizationFlowInstance - INCLUDING inherited field: {key} = {value}")
		
		return filtered_config

	def _convert_config_snapshot_to_experiment_format(self, config_snapshot):
		"""Convert config snapshot from iterations to experiment dictionary format"""
		experiment_format = {}
		
		# Map config snapshot keys to experiment dictionary keys
		config_mapping = {
			'voltage_ia': 'Voltage IA',
			'voltage_cfc': 'Voltage CFC',
			'frequency_ia': 'Frequency IA',
			'frequency_cfc': 'Frequency CFC',
			'content': 'Content',
			'mask': 'Configuration (Mask)',
			'check_core': 'Check Core',
			'voltage_type': 'Voltage Type'
		}
		
		for snapshot_key, exp_key in config_mapping.items():
			if config_snapshot.get(snapshot_key) is not None:
				experiment_format[exp_key] = config_snapshot[snapshot_key]
		
		return experiment_format

	def _log_inherited_configuration(self):
		"""Log the inherited configuration for debugging"""
		self.logger("Inherited configuration from previous node:")
		
		# Key parameters that are important for failure reproduction
		key_params = [
			'Content', 'Configuration (Mask)', 'Check Core', 'Voltage Type',
			'Voltage IA', 'Voltage CFC', 'Frequency IA', 'Frequency CFC',
			'Test Time', 'Reset', 'Reset on PASS', 'FastBoot',
			'TTL Folder', 'Pass String', 'Fail String'
		]
		
		inherited_count = 0
		for param in key_params:
			if param in self.previous_node_config and self.previous_node_config[param] is not None:
				self.logger(f"  {param}: {self.previous_node_config[param]}")
				inherited_count += 1
		
		self.logger(f"Total inherited parameters: {inherited_count}")
		
		# Also log any additional parameters not in the key list
		additional_params = [k for k in self.previous_node_config.keys() if k not in key_params and self.previous_node_config[k] is not None]
		if additional_params:
			self.logger(f"Additional inherited parameters: {len(additional_params)}")
			for param in additional_params[:5]:  # Log first 5 additional params
				self.logger(f"  {param}: {self.previous_node_config[param]}")
			if len(additional_params) > 5:
				self.logger(f"  ... and {len(additional_params) - 5} more")

	def _apply_inherited_configuration(self):
		"""Apply inherited configuration from previous node, override with test execution config"""
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Applying inherited configuration...")
		
		if not self.previous_node_config:
			print("[DEBUG] DEBUG: CharacterizationFlowInstance - No previous node configuration to inherit")
			self.logger("No previous node configuration to inherit - using current experiment config")
			return

		# Keep the node's original Test Name
		original_test_name = self.Experiment.get('Test Name', self.Name)
		
		# Show what we're starting with
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Current experiment config before merge:")
		for key, value in self.Experiment.items():
			if value is not None:
				print(f"[DEBUG] DEBUG:   {key}: {value}")
		
		# Start with the inherited configuration as base
		merged_config = self.previous_node_config.copy()
		
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Base inherited config:")
		for key, value in merged_config.items():
			if value is not None:
				print(f"[DEBUG] DEBUG:   {key}: {value}")
		
		# Override with test execution parameters (Test Type, Sweep params, etc.)
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Overriding with test execution config:")
		for key, value in self.test_execution_config.items():
			print(f"[DEBUG] DEBUG:   Override: {key} = {value}")
			merged_config[key] = value
		
		# Use the characterization node's name for Test Name (not inherited)
		merged_config['Test Name'] = self.Name  # Use node name directly
		print(f"[DEBUG] DEBUG: CharacterizationFlowInstance - Set Test Name to node name: {self.Name}")
		
		# Apply the merged configuration to the experiment
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Applying merged config to self.Experiment...")
		self.Experiment.update(merged_config)

		# Restore the node's own Test Name (don't inherit it)
		self.Experiment['Test Name'] = original_test_name
		print(f"[DEBUG] DEBUG: CharacterizationFlowInstance - Kept original Test Name: {original_test_name}")
		
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Final self.Experiment after merge:")
		for key, value in self.Experiment.items():
			if value is not None:
				print(f"[DEBUG] DEBUG:   {key}: {value}")
		
		self.logger("Applied inherited configuration with test execution overrides:")
		self.logger(f"  Test Name set to node name: {self.Name}")
		self.logger(f"  Test execution type: {self.test_execution_config.get('Test Type', 'Unknown')}")
		
		# Log the test execution overrides
		for key, value in self.test_execution_config.items():
			self.logger(f"  Override - {key}: {value}")
		
		# Validate the final configuration
		self._validate_characterization_config()
		self._debug_show_config_comparison()

	def _debug_show_config_comparison(self):
		"""Debug method to show configuration comparison (filtered experiment config only)"""
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - EXPERIMENT CONFIGURATION COMPARISON (Filtered):")
		print("=" * 100)
		
		# Only show experiment parameters, not execution metadata
		experiment_keys = set()
		
		# Collect all experiment-related keys
		for config_dict in [self.previous_node_config, self.test_execution_config, self.Experiment]:
			for key in config_dict.keys():
				# Filter out execution metadata keys
				if not any(metadata in key.lower() for metadata in [
					'executed', 'execution', 'start_time', 'end_time', 'duration', 
					'final_result', 'output_port', 'pass_count', 'fail_count', 
					'total_iterations', 'test_folder', 'summary_file', 'node_id', 
					'node_type', 'result_summary'
				]):
					experiment_keys.add(key)
		
		print(f"{'Parameter':<30} | {'Inherited':<20} | {'Override':<15} | {'Final':<20}")
		print("-" * 100)
		
		for key in sorted(experiment_keys):
			inherited = self.previous_node_config.get(key, 'NOT_SET')
			override = self.test_execution_config.get(key, 'NOT_SET')
			final = self.Experiment.get(key, 'NOT_SET')
			
			# Only show if at least one value is set
			if inherited != 'NOT_SET' or override != 'NOT_SET' or final != 'NOT_SET':
				print(f"{key:<30} | {str(inherited):<20} | {str(override):<15} | {str(final):<20}")
		
		print("=" * 100)
		print("[DEBUG] DEBUG: Note - Execution metadata (timing, results, counts) filtered out from inheritance")
		
	def _validate_characterization_config(self):
		"""Validate that the characterization configuration is suitable for failure reproduction"""
		validation_issues = []
		
		# Check that we have the essential failure reproduction parameters
		essential_params = ['Content', 'Pass String', 'Fail String']
		for param in essential_params:
			if not self.Experiment.get(param):
				validation_issues.append(f"Missing essential parameter: {param}")
		
		# Check test execution configuration
		test_type = self.Experiment.get('Test Type')
		if test_type == 'Sweep':
			sweep_params = ['Type', 'Domain', 'Start', 'End', 'Steps']
			missing_sweep_params = [p for p in sweep_params if p not in self.Experiment]
			if missing_sweep_params:
				validation_issues.append(f"Missing sweep parameters: {missing_sweep_params}")
		
		elif test_type == 'Shmoo':
			if not self.Experiment.get('ShmooFile'):
				validation_issues.append("Missing ShmooFile for Shmoo test type")
		
		elif test_type == 'Loops':
			if not self.Experiment.get('Loops'):
				validation_issues.append("Missing Loops parameter for Loops test type")
		
		# Log validation results
		if validation_issues:
			self.logger("Configuration validation issues found:")
			for issue in validation_issues:
				self.logger(f"  WARNING: {issue}")
		else:
			self.logger("Configuration validation passed - ready for characterization")
		
		# Log final configuration summary
		self._log_final_config_summary()
	
	def _log_final_config_summary(self):
		"""Log summary of final configuration for characterization"""
		self.logger("="*60)
		self.logger("CHARACTERIZATION CONFIGURATION SUMMARY")
		self.logger("="*60)
		
		# Test execution summary
		test_type = self.Experiment.get('Test Type', 'Unknown')
		self.logger(f"Test Type: {test_type}")
		
		if test_type == 'Sweep':
			sweep_type = self.Experiment.get('Type', 'Unknown')
			domain = self.Experiment.get('Domain', 'Unknown')
			start = self.Experiment.get('Start', 'Unknown')
			end = self.Experiment.get('End', 'Unknown')
			steps = self.Experiment.get('Steps', 'Unknown')
			self.logger(f"Sweep: {sweep_type} {domain} from {start} to {end} step {steps}")
		
		elif test_type == 'Loops':
			loops = self.Experiment.get('Loops', 'Unknown')
			self.logger(f"Loops: {loops}")
		
		elif test_type == 'Shmoo':
			shmoo_file = self.Experiment.get('ShmooFile', 'Unknown')
			shmoo_label = self.Experiment.get('ShmooLabel', 'Unknown')
			self.logger(f"Shmoo: {shmoo_file} ({shmoo_label})")
		
		# Failure reproduction conditions
		self.logger("Failure Reproduction Conditions:")
		repro_params = ['Content', 'Configuration (Mask)', 'Check Core', 'Voltage Type']
		for param in repro_params:
			value = self.Experiment.get(param, 'Not Set')
			self.logger(f"  {param}: {value}")
		
		# Voltage/Frequency settings
		vf_params = ['Voltage IA', 'Voltage CFC', 'Frequency IA', 'Frequency CFC']
		vf_set = [param for param in vf_params if self.Experiment.get(param) is not None]
		if vf_set:
			self.logger("Voltage/Frequency Settings:")
			for param in vf_set:
				self.logger(f"  {param}: {self.Experiment[param]}")
		
		self.logger("="*60)

	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""Continue until all characterization points are tested"""
		base_decision = self.make_full_experiment_decision(stats, iteration_count, max_iterations)
		if base_decision:
			return base_decision
		
		# For characterization, we want to complete all planned iterations
		return 'continue'

	def _analyze_characterization_results(self):
		"""Analyze characterization results focusing on failure reproduction patterns"""
		if not self.runStatusHistory:
			self.logger("No characterization results to analyze")
			return
		
		total_points = len(self.runStatusHistory)
		failing_points = []
		passing_points = []
		other_points = []
		
		# Analyze each result point
		for i, status in enumerate(self.runStatusHistory):
			config_snapshot = self._get_current_config_snapshot() if hasattr(self, '_get_current_config_snapshot') else {}
			
			point_data = {
				'iteration': i + 1,
				'status': status,
				'config': config_snapshot,
				'sweep_value': self._extract_sweep_value_for_iteration(i + 1, config_snapshot)
			}
			
			if status == 'FAIL':
				failing_points.append(point_data)
			elif status == 'PASS':
				passing_points.append(point_data)
			else:
				other_points.append(point_data)
		
		# Calculate rates
		fail_rate = len(failing_points) / total_points if total_points > 0 else 0
		pass_rate = len(passing_points) / total_points if total_points > 0 else 0
		other_rate = len(other_points) / total_points if total_points > 0 else 0
		
		# Assess failure reproduction quality
		reproduction_quality = self._assess_failure_reproduction_quality(fail_rate, total_points)
		
		self.characterization_results = {
			'total_points': total_points,
			'failing_points': failing_points,
			'passing_points': passing_points,
			'other_points': other_points,
			'fail_rate': fail_rate,
			'pass_rate': pass_rate,
			'other_rate': other_rate,
			'reproduction_quality': reproduction_quality,
			'failure_characterization': self._analyze_failure_characterization(failing_points),
			'inherited_from_node': self.previous_node_config.get('Test Name', 'Unknown'),
			'test_execution_type': self.test_execution_config.get('Test Type', 'Unknown')
		}
		
		# Store in experiment tracker
		if self.experiment_tracker:
			self.experiment_tracker.current_experiment_data['characterization_results'] = self.characterization_results
		
		self._log_characterization_analysis()

	def _assess_failure_reproduction_quality(self, fail_rate, total_points):
		"""Assess the quality of failure reproduction for characterization purposes"""
		if total_points == 0:
			return 'no_data'
		
		if fail_rate >= 0.8:
			return 'excellent_characterization'    # 80%+ failure rate - excellent for characterization
		elif fail_rate >= 0.5:
			return 'good_characterization'         # 50-79% failure rate - good characterization data
		elif fail_rate >= 0.2:
			return 'moderate_characterization'     # 20-49% failure rate - moderate characterization
		elif fail_rate > 0:
			return 'limited_characterization'      # 1-19% failure rate - limited characterization data
		else:
			return 'no_failure_reproduction'       # 0% failure rate - no failures reproduced
	
	def _extract_sweep_value_for_iteration(self, iteration_num, config_snapshot):
		"""Extract the sweep value for a specific iteration based on test type"""
		test_type = self.test_execution_config.get('Test Type')
		
		if test_type == 'Sweep':
			sweep_type = self.test_execution_config.get('Type')
			sweep_domain = self.test_execution_config.get('Domain')
			
			if sweep_type == 'voltage':
				if sweep_domain == 'ia':
					return config_snapshot.get('volt_IA')
				elif sweep_domain == 'cfc':
					return config_snapshot.get('volt_CFC')
			elif sweep_type == 'frequency':
				if sweep_domain == 'ia':
					return config_snapshot.get('freq_ia')
				elif sweep_domain == 'cfc':
					return config_snapshot.get('freq_cfc')
		
		# For non-sweep tests, return iteration number
		return iteration_num

	def _analyze_failure_characterization(self, failing_points):
		"""Analyze failure characterization patterns"""
		if not failing_points:
			return {'status': 'no_failures', 'message': 'No failures found for characterization'}
		
		# Extract sweep values from failing points
		failure_values = []
		for point in failing_points:
			sweep_value = point.get('sweep_value')
			if sweep_value is not None:
				failure_values.append(sweep_value)
		
		if not failure_values:
			return {
				'status': 'failures_no_sweep_data',
				'failure_count': len(failing_points),
				'message': 'Failures found but no sweep value data for characterization'
			}
		
		# Analyze failure distribution
		failure_range = [min(failure_values), max(failure_values)] if len(failure_values) > 1 else [failure_values[0], failure_values[0]]
		
		return {
			'status': 'characterized',
			'failure_count': len(failing_points),
			'failure_values': failure_values,
			'failure_range': failure_range,
			'failure_span': failure_range[1] - failure_range[0] if len(failure_values) > 1 else 0,
			'characterization_summary': self._generate_characterization_summary(failure_values, failure_range)
		}

	def _generate_characterization_summary(self, failure_values, failure_range):
		"""Generate characterization summary based on failure patterns"""
		test_type = self.test_execution_config.get('Test Type')
		
		if test_type == 'Sweep':
			sweep_type = self.test_execution_config.get('Type', 'unknown')
			sweep_domain = self.test_execution_config.get('Domain', 'unknown')
			
			if len(failure_values) == 1:
				return f"Unit fails at {sweep_type} {sweep_domain} = {failure_values[0]}"
			else:
				span = failure_range[1] - failure_range[0]
				return f"Unit fails across {sweep_type} {sweep_domain} range {failure_range[0]} to {failure_range[1]} (span: {span})"
		
		elif test_type == 'Loops':
			return f"Unit failed in {len(failure_values)} out of {self.test_execution_config.get('Loops', 'unknown')} loop iterations"
		
		elif test_type == 'Shmoo':
			return f"Unit failed at {len(failure_values)} points in shmoo characterization"
		
		else:
			return f"Unit failed at {len(failure_values)} characterization points"
	
	def _log_characterization_analysis(self):
		"""Log detailed characterization analysis"""
		results = self.characterization_results
		
		self.logger("="*70)
		self.logger("UNIT FAILURE CHARACTERIZATION ANALYSIS")
		self.logger("="*70)
		
		self.logger(f"Configuration inherited from: {results['inherited_from_node']}")
		self.logger(f"Test execution type: {results['test_execution_type']}")
		self.logger(f"Total characterization points: {results['total_points']}")
		self.logger(f"Failing points: {len(results['failing_points'])} ({results['fail_rate']:.1%})")
		self.logger(f"Passing points: {len(results['passing_points'])} ({results['pass_rate']:.1%})")
		
		if results['other_points']:
			self.logger(f"Other results: {len(results['other_points'])} ({results['other_rate']:.1%})")
		
		self.logger(f"Reproduction quality: {results['reproduction_quality']}")
		
		# Log failure characterization details
		failure_char = results['failure_characterization']
		if failure_char['status'] == 'characterized':
			self.logger(f"Failure characterization: {failure_char['characterization_summary']}")
			if failure_char.get('failure_range'):
				self.logger(f"Failure range: {failure_char['failure_range']}")
		elif failure_char['status'] == 'no_failures':
			self.logger("No failures reproduced - unit appears stable under inherited conditions")
		
		self.logger("="*70)

	def set_output_port(self):
		"""Set output port for characterization flow"""
		if self._set_base_output_ports():
			return
		
		# Characterization always exits through port 0 when complete
		self.outputPort = 0
		
		self.logger('='*50)
		self.logger(f' Characterization Results: {self.characterization_results}')
		self.logger(f' CharacterizationFlow Node Complete - Port: {self.outputPort}')
		self.logger('='*50)

	def _log_inheritance_summary(self):
		"""Log summary of what was inherited vs filtered out"""
		if not hasattr(self, 'previous_node_config'):
			return
		
		inherited_count = len([k for k, v in self.previous_node_config.items() if v is not None])
		
		print("[DEBUG] DEBUG: CharacterizationFlowInstance - Inheritance Summary:")
		print(f"[DEBUG] DEBUG:   Inherited experiment parameters: {inherited_count}")
		print("[DEBUG] DEBUG:   Filtered out execution metadata (timing, results, etc.)")
		
		# Show key inherited parameters
		key_inherited = ['Content', 'Voltage IA', 'Voltage CFC', 'Frequency IA', 'Frequency CFC', 'Voltage Type', 'Configuration (Mask)']
		inherited_key_params = {k: v for k, v in self.previous_node_config.items() if k in key_inherited and v is not None}
		
		if inherited_key_params:
			print("[DEBUG] DEBUG:   Key inherited parameters:")
			for key, value in inherited_key_params.items():
				print(f"[DEBUG] DEBUG:     {key}: {value}")
				
class DataCollectionFlowInstance(FlowInstance):
	"""
	Data collection flow that runs complete experiment without decision making.
	"""
	
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""Run all iterations without early termination"""
		base_decision = self.make_full_experiment_decision(stats, iteration_count, max_iterations)
		if base_decision:
			return base_decision
		
		# Continue until all iterations are complete
		return 'continue'
	
	def set_output_port(self):
		"""Set output port - always exit through port 0 unless hardware failure"""
		if self._set_base_output_ports():
			return
		
		# Data collection always completes through port 0
		self.outputPort = 0
		
		self.logger('='*50)
		self.logger(f' RunStatus: {self.runStatusHistory}')
		self.logger(f' DataCollection Node Complete - Port: {self.outputPort}')
		self.logger(f' Total Data Points Collected: {len(self.runStatusHistory)}')
		self.logger('='*50)

class AnalysisFlowInstance(FlowInstance):
	"""
	Enhanced analysis flow for comprehensive data analysis with smart experiment generation.
	"""
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.analysis_results = {}
		self.summary_report_path = None
		self.smart_experiment_proposal = None

	def run_experiment(self):
		"""Perform comprehensive analysis and generate smart experiment proposals - NO ACTUAL EXPERIMENT EXECUTION"""
		print("[DEBUG] DEBUG: AnalysisFlowInstance - Starting comprehensive analysis (NO experiment execution)")
		self.logger(f"Starting Comprehensive Analysis: {self.Name} (ID: {self.ID})")
		
		# DEBUG: Show original experiment config
		print("[DEBUG] DEBUG: AnalysisFlowInstance - Original experiment config:")
		for key, value in self.Experiment.items():
			if value is not None:
				print(f"[DEBUG] DEBUG:   {key}: {value}")
		
		# Perform comprehensive data analysis
		self._perform_comprehensive_analysis()
		
		# Generate smart experiment proposals
		self._generate_smart_experiment_proposals()
		
		# Generate summary report
		self._generate_summary_report()
		
		# Save analysis results
		self._save_analysis_results()
		
		# DEBUG: Show analysis results summary
		print("[DEBUG] DEBUG: AnalysisFlowInstance - Analysis results summary:")
		if self.analysis_results:
			flow_summary = self.analysis_results.get('flow_execution_summary', {})
			print(f"[DEBUG] DEBUG:   Total nodes executed: {flow_summary.get('total_nodes_executed', 0)}")
			print(f"[DEBUG] DEBUG:   Recovery conditions: {len(flow_summary.get('recovery_conditions', []))}")
			print(f"[DEBUG] DEBUG:   Failure conditions: {len(flow_summary.get('failure_conditions', []))}")
		
		# DEBUG: Show smart experiment proposals count
		if self.smart_experiment_proposal:
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Generated {self.smart_experiment_proposal.get('total_proposals', 0)} smart experiment proposals")
			
			# Show first few proposals
			proposals = self.smart_experiment_proposal.get('recommended_sequence', [])
			for i, item in enumerate(proposals[:3]):  # Show first 3
				proposal = item['proposal']
				print(f"[DEBUG] DEBUG:   Proposal {i+1}: {proposal['description']} (Priority: {proposal['priority']})")
		
		# Set successful completion WITHOUT running actual experiment
		# Print complete flow summary to console
		self._print_complete_flow_summary()

		self.runStatusHistory = ['PASS']
		self.set_output_port()
		
		# Complete experiment tracking (but mark as analysis-only)
		if self.experiment_tracker:
			test_folder = None  # No test folder since no experiment was run
			self.experiment_tracker.complete_experiment(
				final_result='ANALYSIS_COMPLETE',  # Special result for analysis-only nodes
				output_port=self.outputPort,
				test_folder=test_folder
			)
		
		print("[DEBUG] DEBUG: AnalysisFlowInstance - Analysis complete, ready to pass results to next node")
			
	def _perform_comprehensive_analysis(self):
		"""Perform comprehensive analysis of all collected data with content analysis"""
		if not self.experiment_tracker:
			self.logger("No experiment tracker available for analysis")
			self.analysis_results = {'error': 'No experiment tracker available'}
			return

		if hasattr(self.experiment_tracker, 'debug_sweep_detection'):
			self.experiment_tracker.debug_sweep_detection()
						
		try:
			comprehensive_data = self.experiment_tracker.get_comprehensive_analysis_data()
			
			# Validate comprehensive_data
			if comprehensive_data is None:
				self.logger("Comprehensive analysis returned None")
				self.analysis_results = {'error': 'Comprehensive analysis returned None'}
				return
			
			if 'error' in comprehensive_data:
				self.logger(f"Error in comprehensive analysis: {comprehensive_data['error']}")
				self.analysis_results = comprehensive_data
				return
			
			self.analysis_results = {
				'flow_execution_summary': comprehensive_data.get('flow_summary', {}),
				'voltage_frequency_analysis': comprehensive_data.get('voltage_frequency_analysis', {}),
				'unit_characterization': comprehensive_data.get('unit_characterization', {}),
				'recovery_analysis': comprehensive_data.get('recovery_analysis', {}),
				'failure_analysis': comprehensive_data.get('failure_analysis', {}),
				'sweep_summary': comprehensive_data.get('sweep_summary', {}),
				'content_analysis': comprehensive_data.get('content_analysis', {}),  # Add content analysis
				'unit_sensitivity_profile': self._create_unit_sensitivity_profile(comprehensive_data),
				'recommended_next_steps': comprehensive_data.get('recommendations', [])
			}
			
			self.logger(f"Analysis complete - processed {comprehensive_data.get('total_experiments', 0)} experiments")
			
		except Exception as e:
			error_msg = f"Error in comprehensive analysis: {str(e)}"
			self.logger(error_msg)
			self.analysis_results = {'error': error_msg}
				
	def _create_unit_sensitivity_profile(self, comprehensive_data):
		"""Create a comprehensive unit sensitivity profile"""
		vf_analysis = comprehensive_data['voltage_frequency_analysis']
		unit_char = comprehensive_data['unit_characterization']
		
		profile = {
			'overall_stability': unit_char['unit_stability'],
			'voltage_sensitivity': {
				'ia_voltage': self._extract_domain_sensitivity(vf_analysis, 'voltage', 'ia'),
				'cfc_voltage': self._extract_domain_sensitivity(vf_analysis, 'voltage', 'cfc'),
				'overall_conclusion': vf_analysis['voltage_sensitivity'].get('overall_voltage_conclusion', 'Unknown')
			},
			'frequency_sensitivity': {
				'ia_frequency': self._extract_domain_sensitivity(vf_analysis, 'frequency', 'ia'),
				'cfc_frequency': self._extract_domain_sensitivity(vf_analysis, 'frequency', 'cfc'),
				'overall_conclusion': vf_analysis['frequency_sensitivity'].get('overall_frequency_conclusion', 'Unknown')
			},
			'combined_sensitivity': vf_analysis['combined_analysis'],
			'dominant_failure_modes': unit_char['dominant_failure_patterns'],
			'recovery_success_rate': comprehensive_data['recovery_analysis'].get('recovery_success_rate', 0) if comprehensive_data['recovery_analysis'].get('status') == 'recovery_found' else 0
		}
		
		return profile
	
	def _extract_domain_sensitivity(self, vf_analysis, param_type, domain):
		"""Extract sensitivity information for a specific domain"""
		sensitivity_data = vf_analysis[f'{param_type}_sensitivity']
		domain_key = f'{domain}_{param_type}_sensitivity'
		
		if domain_key in sensitivity_data:
			domain_data = sensitivity_data[domain_key]
			return {
				'status': domain_data.get('status', 'no_data'),
				'pattern': domain_data.get('dominant_pattern', 'unknown'),
				'conclusion': domain_data.get('conclusion', 'No data available')
			}
		
		return {'status': 'no_data', 'pattern': 'unknown', 'conclusion': 'No data available'}
	
	def _generate_smart_experiment_proposals(self):
		"""Generate smart experiment proposals based on analysis"""
		proposals = []
		
		sensitivity_profile = self.analysis_results.get('unit_sensitivity_profile', {})
		recovery_analysis = self.analysis_results.get('recovery_analysis', {})
		
		# Voltage-based experiment proposals
		voltage_proposals = self._generate_voltage_experiment_proposals(sensitivity_profile)
		proposals.extend(voltage_proposals)
		
		# Frequency-based experiment proposals
		frequency_proposals = self._generate_frequency_experiment_proposals(sensitivity_profile)
		proposals.extend(frequency_proposals)
		
		# Recovery validation proposals
		recovery_proposals = self._generate_recovery_validation_proposals(recovery_analysis)
		proposals.extend(recovery_proposals)
		
		# Characterization proposals
		char_proposals = self._generate_characterization_proposals(sensitivity_profile)
		proposals.extend(char_proposals)
		
		self.smart_experiment_proposal = {
			'total_proposals': len(proposals),
			'proposals': proposals,
			'recommended_sequence': self._prioritize_experiment_proposals(proposals)
		}
		
		self.logger(f"Generated {len(proposals)} smart experiment proposals")
		
	def _generate_voltage_experiment_proposals(self, sensitivity_profile):
		"""Generate voltage-based experiment proposals in proper experiment format"""
		proposals = []
		voltage_sens = sensitivity_profile.get('voltage_sensitivity', {})
		
		# Base experiment template from current experiment
		base_template = self._create_base_experiment_template()
		
		# IA Voltage proposals
		ia_voltage = voltage_sens.get('ia_voltage', {})
		if ia_voltage['status'] == 'analyzed' and ia_voltage['pattern'] in ['threshold_sensitivity', 'upper_threshold_sensitivity']:
			ia_experiment = base_template.copy()
			ia_experiment.update({
				'Test Name': 'IA_Voltage_Characterization',
				'Test Type': 'Sweep',
				'Type': 'voltage',
				'Domain': 'ia',
				'Start': -0.05,
				'End': 0.08,
				'Steps': 0.01,
				'Voltage Type': 'vbump',  # Specific to IA domain
				'Loops': 1
			})
			
			proposals.append({
				'type': 'voltage_characterization',
				'domain': 'ia',
				'priority': 'high',
				'description': f"IA voltage characterization - {ia_voltage['conclusion']}",
				'experiment_config': ia_experiment,
				'rationale': f"Unit shows {ia_voltage['pattern']} for IA voltage"
			})
		
		# CFC Voltage proposals
		cfc_voltage = voltage_sens.get('cfc_voltage', {})
		if cfc_voltage['status'] == 'analyzed' and cfc_voltage['pattern'] in ['threshold_sensitivity', 'upper_threshold_sensitivity']:
			cfc_experiment = base_template.copy()
			cfc_experiment.update({
				'Test Name': 'CFC_Voltage_Characterization',
				'Test Type': 'Sweep',
				'Type': 'voltage',
				'Domain': 'cfc',
				'Start': -0.05,
				'End': 0.08,
				'Steps': 0.01,
				'Voltage Type': 'vbump',  # Specific to CFC domain
				'Loops': 1
			})
			
			proposals.append({
				'type': 'voltage_characterization',
				'domain': 'cfc',
				'priority': 'high',
				'description': f"CFC voltage characterization - {cfc_voltage['conclusion']}",
				'experiment_config': cfc_experiment,
				'rationale': f"Unit shows {cfc_voltage['pattern']} for CFC voltage"
			})
		
		# PPVC proposal if both domains show sensitivity
		if (ia_voltage.get('status') == 'analyzed' and cfc_voltage.get('status') == 'analyzed' and
			ia_voltage.get('pattern') in ['threshold_sensitivity', 'upper_threshold_sensitivity'] and
			cfc_voltage.get('pattern') in ['threshold_sensitivity', 'upper_threshold_sensitivity']):
			
			ppvc_experiment = base_template.copy()
			ppvc_experiment.update({
				'Test Name': 'PPVC_Voltage_Recovery',
				'Test Type': 'Loops',
				'Voltage Type': 'PPVC',  # Reduces guardbands on all domains
				'Loops': 15
			})
			
			proposals.append({
				'type': 'ppvc_recovery',
				'domain': 'all',
				'priority': 'critical',
				'description': 'PPVC voltage recovery test - reduces guardbands on all domains',
				'experiment_config': ppvc_experiment,
				'rationale': 'Both IA and CFC show voltage sensitivity - PPVC may provide recovery'
			})
		
		return proposals

	def _generate_frequency_experiment_proposals(self, sensitivity_profile):
		"""Generate frequency-based experiment proposals in proper experiment format"""
		proposals = []
		frequency_sens = sensitivity_profile.get('frequency_sensitivity', {})
		
		# Base experiment template
		base_template = self._create_base_experiment_template()
		
		# IA Frequency proposals - NO VOLTAGE TYPE since it's frequency only
		ia_frequency = frequency_sens.get('ia_frequency', {})
		if ia_frequency['status'] == 'analyzed' and ia_frequency['pattern'] in ['threshold_sensitivity', 'upper_threshold_sensitivity']:
			ia_freq_experiment = base_template.copy()
			ia_freq_experiment.update({
				'Test Name': 'IA_Frequency_Characterization',
				'Test Type': 'Sweep',
				'Type': 'frequency',
				'Domain': 'ia',
				'Start': 8,
				'End': 25,
				'Steps': 2,
				'Loops': 1
				# NOTE: No 'Voltage Type' here since this is frequency-only sweep
			})
			
			proposals.append({
				'type': 'frequency_characterization',
				'domain': 'ia',
				'priority': 'high',
				'description': f"IA frequency characterization - {ia_frequency['conclusion']}",
				'experiment_config': ia_freq_experiment,
				'rationale': f"Unit shows {ia_frequency['pattern']} for IA frequency"
			})
		
		# CFC Frequency proposals - NO VOLTAGE TYPE since it's frequency only
		cfc_frequency = frequency_sens.get('cfc_frequency', {})
		if cfc_frequency['status'] == 'analyzed' and cfc_frequency['pattern'] in ['threshold_sensitivity', 'upper_threshold_sensitivity']:
			cfc_freq_experiment = base_template.copy()
			cfc_freq_experiment.update({
				'Test Name': 'CFC_Frequency_Characterization',
				'Test Type': 'Sweep',
				'Type': 'frequency',
				'Domain': 'cfc',
				'Start': 8,
				'End': 22,
				'Steps': 2,
				'Loops': 1
				# NOTE: No 'Voltage Type' here since this is frequency-only sweep
			})
			
			proposals.append({
				'type': 'frequency_characterization',
				'domain': 'cfc',
				'priority': 'high',
				'description': f"CFC frequency characterization - {cfc_frequency['conclusion']}",
				'experiment_config': cfc_freq_experiment,
				'rationale': f"Unit shows {cfc_frequency['pattern']} for CFC frequency"
			})
		
		return proposals
	
	def _generate_recovery_validation_proposals(self, recovery_analysis):
		"""Generate recovery validation experiment proposals in proper experiment format"""
		proposals = []
		
		if recovery_analysis.get('status') == 'recovery_found':
			best_recovery = recovery_analysis.get('best_recovery_condition', {})
			if best_recovery:
				# Base experiment template
				recovery_experiment = self._create_base_experiment_template()
				
				# Apply recovery configuration
				recovery_config = best_recovery.get('config', {})
				recovery_experiment.update({
					'Test Name': 'Recovery_Validation',
					'Test Type': 'Loops',
					'Loops': 20
				})
				
				# Apply specific recovery settings
				if recovery_config.get('voltage_ia') is not None:
					recovery_experiment['Voltage IA'] = recovery_config['voltage_ia']
				if recovery_config.get('voltage_cfc') is not None:
					recovery_experiment['Voltage CFC'] = recovery_config['voltage_cfc']
				if recovery_config.get('frequency_ia') is not None:
					recovery_experiment['Frequency IA'] = recovery_config['frequency_ia']
				if recovery_config.get('frequency_cfc') is not None:
					recovery_experiment['Frequency CFC'] = recovery_config['frequency_cfc']
				if recovery_config.get('voltage_type') is not None:
					recovery_experiment['Voltage Type'] = recovery_config['voltage_type']
				if recovery_config.get('content') is not None:
					recovery_experiment['Content'] = recovery_config['content']
				if recovery_config.get('mask') is not None:
					recovery_experiment['Configuration (Mask)'] = recovery_config['mask']
				if recovery_config.get('check_core') is not None:
					recovery_experiment['Check Core'] = recovery_config['check_core']
				
				proposals.append({
					'type': 'recovery_validation',
					'priority': 'critical',
					'description': f"Validate best recovery condition ({best_recovery['pass_rate']:.1f}% success rate)",
					'experiment_config': recovery_experiment,
					'rationale': f"Validate recovery condition from {best_recovery.get('node_name', 'unknown node')}"
				})
		
		return proposals

	def _generate_characterization_proposals(self, sensitivity_profile):
		"""Generate characterization experiment proposals in proper experiment format"""
		proposals = []
		
		combined_sens = sensitivity_profile.get('combined_sensitivity', {})
		
		# If unit is sensitive to both voltage and frequency, propose 2D characterization
		if combined_sens.get('voltage_sensitive') and combined_sens.get('frequency_sensitive'):
			shmoo_experiment = self._create_base_experiment_template()
			shmoo_experiment.update({
				'Test Name': '2D_Voltage_Frequency_Characterization',
				'Test Type': 'Shmoo',
				'ShmooFile': 'C:\\SystemDebug\\Shmoos\\VoltageFrequencyShmoo.json',
				'ShmooLabel': 'VOLT_FREQ_CHAR'
			})
			
			proposals.append({
				'type': '2d_characterization',
				'priority': 'medium',
				'description': 'Combined voltage/frequency 2D characterization',
				'experiment_config': shmoo_experiment,
				'rationale': 'Unit shows sensitivity to both voltage and frequency'
			})
		
		return proposals

	def _create_base_experiment_template(self):
		"""Create base experiment template from current experiment"""
		# Use current experiment as template and preserve key settings
		base_template = {
			'Experiment': 'Enabled',
			'Test Mode': self.Experiment.get('Test Mode', 'Mesh'),
			'Visual ID': self.Experiment.get('Visual ID', 'TestUnitData'),
			'Bucket': self.Experiment.get('Bucket', 'ANALYSIS'),
			'COM Port': self.Experiment.get('COM Port', 11),
			'IP Address': self.Experiment.get('IP Address', '192.168.0.2'),
			'TTL Folder': self.Experiment.get('TTL Folder', 'R:\\Templates\\GNR\\version_2_0\\TTL_DragonMesh'),
			'Scripts File': self.Experiment.get('Scripts File'),
			'Bios File': self.Experiment.get('Bios File', None),
			'Fuse File': self.Experiment.get('Fuse File', None),
			'Pass String': self.Experiment.get('Pass String', 'Test Complete'),
			'Fail String': self.Experiment.get('Fail String', 'Test Failed'),
			'Content': self.Experiment.get('Content', 'Dragon'),
			'Test Number': self.Experiment.get('Test Number', 1),
			'Test Time': self.Experiment.get('Test Time', 30),
			'Reset': self.Experiment.get('Reset', True),
			'Reset on PASS': self.Experiment.get('Reset on PASS', True),
			'FastBoot': self.Experiment.get('FastBoot', True),
			'Core License': self.Experiment.get('Core License'),
			'600W Unit': self.Experiment.get('600W Unit', False),
			'Pseudo Config': self.Experiment.get('Pseudo Config', False),
			'Configuration (Mask)': self.Experiment.get('Configuration (Mask)'),
			'Boot Breakpoint': self.Experiment.get('Boot Breakpoint'),
			'Disable 2 Cores': self.Experiment.get('Disable 2 Cores'),
			'Check Core': self.Experiment.get('Check Core', 7),
			'Voltage Type': self.Experiment.get('Voltage Type', 'vbump'),
			'Voltage IA': self.Experiment.get('Voltage IA'),
			'Voltage CFC': self.Experiment.get('Voltage CFC'),
			'Frequency IA': self.Experiment.get('Frequency IA'),
			'Frequency CFC': self.Experiment.get('Frequency CFC'),
			'Linux Pre Command': self.Experiment.get('Linux Pre Command'),
			'Linux Post Command': self.Experiment.get('Linux Post Command'),
			'Startup Linux': self.Experiment.get('Startup Linux'),
			'Linux Path': self.Experiment.get('Linux Path'),
			'Linux Content Wait Time': self.Experiment.get('Linux Content Wait Time'),
			'Linux Content Line 0': self.Experiment.get('Linux Content Line 0'),
			'Linux Content Line 1': self.Experiment.get('Linux Content Line 1'),
			'Dragon Pre Command': self.Experiment.get('Dragon Pre Command'),
			'Dragon Post Command': self.Experiment.get('Dragon Post Command'),
			'Startup Dragon': self.Experiment.get('Startup Dragon', 'startup_efi.nsh'),
			'ULX Path': self.Experiment.get('ULX Path', 'FS1:\\EFI\\ulx'),
			'ULX CPU': self.Experiment.get('ULX CPU', 'GNR_B0'),
			'Product Chop': self.Experiment.get('Product Chop', 'GNR'),
			'VVAR0': self.Experiment.get('VVAR0', '0x4C4B40'),
			'VVAR1': self.Experiment.get('VVAR1', 80064000),
			'VVAR2': self.Experiment.get('VVAR2', '0x1000000'),
			'VVAR3': self.Experiment.get('VVAR3', '0x4000000'),
			'VVAR_EXTRA': self.Experiment.get('VVAR_EXTRA'),
			'Dragon Content Path': self.Experiment.get('Dragon Content Path', 'FS1:\\content\\Dragon\\7410_0x0E_PPV_MM\\GNR128C_H_1UP\\'),
			'Dragon Content Line': self.Experiment.get('Dragon Content Line', 'Sanity'),
			'Stop on Fail': self.Experiment.get('Stop on Fail', True),
			'Merlin Name': self.Experiment.get('Merlin Name', 'MerlinX.efi'),
			'Merlin Drive': self.Experiment.get('Merlin Drive', 'FS1:'),
			'Merlin Path': self.Experiment.get('Merlin Path', 'FS1:\\EFI\\Version8.15\\BinFiles\\Release'),
			'Post Process': self.Experiment.get('Post Process'),
			'Linux Pass String': self.Experiment.get('Linux Pass String'),
			'Linux Fail String': self.Experiment.get('Linux Fail String'),
			'Linux Content Line 2': self.Experiment.get('Linux Content Line 2'),
			'Linux Content Line 3': self.Experiment.get('Linux Content Line 3'),
			'Linux Content Line 4': self.Experiment.get('Linux Content Line 4'),
			'Linux Content Line 5': self.Experiment.get('Linux Content Line 5')
		}
		
		return base_template
	
	def _convert_config_to_experiment_format(self, config):
		"""Convert config snapshot to experiment format"""
		experiment_config = {}
		
		config_mapping = {
			'voltage_ia': 'Voltage IA',
			'voltage_cfc': 'Voltage CFC',
			'frequency_ia': 'Frequency IA',
			'frequency_cfc': 'Frequency CFC',
			'content': 'Content',
			'mask': 'Configuration (Mask)',
			'check_core': 'Check Core'
		}
		
		for config_key, exp_key in config_mapping.items():
			if config.get(config_key) is not None:
				experiment_config[exp_key] = config[config_key]
		
		return experiment_config
	
	def _prioritize_experiment_proposals(self, proposals):
		"""Prioritize experiment proposals by importance"""
		priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
		
		sorted_proposals = sorted(proposals, key=lambda x: priority_order.get(x['priority'], 4))
		
		return [
			{
				'sequence_number': i + 1,
				'proposal': proposal,
				'estimated_duration': self._estimate_experiment_duration(proposal['experiment_config'])
			}
			for i, proposal in enumerate(sorted_proposals)
		]
	
	def _estimate_experiment_duration(self, experiment_config):
		"""Estimate experiment duration in minutes"""
		test_type = experiment_config.get('Test Type', 'Loops')
		test_time = experiment_config.get('Test Time', 30)
		
		if test_type == 'Loops':
			loops = experiment_config.get('Loops', 10)
			return (loops * test_time) / 60  # Convert to minutes
		elif test_type == 'Sweep':
			start = experiment_config.get('Start', 0)
			end = experiment_config.get('End', 10)
			steps = experiment_config.get('Steps', 1)
			iterations = max(1, int((end - start) / steps) + 1)
			return (iterations * test_time) / 60
		elif test_type == 'Shmoo':
			return 30  # Estimate for shmoo
		else:
			return 10  # Default estimate
	
	def _generate_summary_report(self):
		"""Generate comprehensive summary report with experiment proposals"""
		if not self.experiment_tracker:
			return
			
		# Create comprehensive report
		report = {
			'analysis_timestamp': datetime.now().isoformat(),
			'flow_execution_summary': self.analysis_results['flow_execution_summary'],
			'unit_sensitivity_profile': self.analysis_results['unit_sensitivity_profile'],
			'comprehensive_analysis': self.analysis_results,
			'smart_experiment_proposals': self.smart_experiment_proposal,
			'detailed_experiment_history': self.experiment_tracker.experiments_history,
			'executive_summary': self._generate_executive_summary()
		}
		
		# Save report to file
		if hasattr(self, 'framework_api') and self.framework_api:
			test_folder = getattr(self.framework_api.framework.config, 'tfolder', None)
			if test_folder:
				report_path = os.path.join(test_folder, 'comprehensive_analysis_report.json')
				try:
					with open(report_path, 'w') as f:
						json.dump(report, f, indent=2, default=str)
					self.summary_report_path = report_path
					self.logger(f"Comprehensive analysis report saved to: {report_path}")
					
					# Also save experiment proposals as separate file for easy access
					proposals_path = os.path.join(test_folder, 'smart_experiment_proposals.json')
					with open(proposals_path, 'w') as f:
						json.dump(self.smart_experiment_proposal, f, indent=2, default=str)
					self.logger(f"Smart experiment proposals saved to: {proposals_path}")
					
				except Exception as e:
					self.logger(f"Error saving analysis report: {e}")
	
	def _generate_executive_summary(self):
		"""Generate executive summary of analysis"""
		sensitivity_profile = self.analysis_results.get('unit_sensitivity_profile', {})
		proposals = self.smart_experiment_proposal.get('proposals', []) if self.smart_experiment_proposal else []
		
		summary = {
			'unit_stability_assessment': sensitivity_profile.get('overall_stability', 'unknown'),
			'primary_sensitivities': [],
			'recovery_potential': sensitivity_profile.get('recovery_success_rate', 0),
			'recommended_immediate_actions': [],
			'total_experiment_proposals': len(proposals),
			'estimated_total_characterization_time': sum(
				self._estimate_experiment_duration(p['experiment_config']) 
				for p in proposals
			)
		}
		
		# Extract primary sensitivities
		voltage_sens = sensitivity_profile.get('voltage_sensitivity', {})
		frequency_sens = sensitivity_profile.get('frequency_sensitivity', {})
		
		if voltage_sens.get('overall_conclusion', '') != 'Unknown':
			summary['primary_sensitivities'].append(f"Voltage: {voltage_sens['overall_conclusion']}")
		
		if frequency_sens.get('overall_conclusion', '') != 'Unknown':
			summary['primary_sensitivities'].append(f"Frequency: {frequency_sens['overall_conclusion']}")
		
		# Extract immediate actions from high-priority proposals
		high_priority_proposals = [p for p in proposals if p['priority'] in ['critical', 'high']]
		summary['recommended_immediate_actions'] = [
			p['description'] for p in high_priority_proposals[:3]  # Top 3
		]
		
		return summary
	
	def _save_analysis_results(self):
		"""Save analysis results to experiment tracker"""
		if self.experiment_tracker:
			self.experiment_tracker.current_experiment_data['comprehensive_analysis'] = self.analysis_results
			self.experiment_tracker.current_experiment_data['smart_experiment_proposals'] = self.smart_experiment_proposal
			self.experiment_tracker.current_experiment_data['summary_report_path'] = self.summary_report_path
	
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""Analysis doesn't need iterations"""
		return 'end'
	
	def set_output_port(self):
		"""Analysis always completes through port 0 with experiment proposals"""
		self.outputPort = 0
		
		# Print experiment proposals to console and pass through port 0
		if self.smart_experiment_proposal:
			self._print_experiment_proposals()
		
		self.logger('='*50)
		self.logger(' Comprehensive Analysis Complete')
		self.logger(f' Summary Report: {self.summary_report_path}')
		self.logger(f' Smart Proposals Generated: {self.smart_experiment_proposal.get("total_proposals", 0) if self.smart_experiment_proposal else 0}')
		self.logger(f' AnalysisFlow Node Complete - Port: {self.outputPort}')
		self.logger('='*50)

	def _print_voltage_type_summary(self, proposals):
		"""Print summary of voltage type recommendations"""
		voltage_types_used = {}
		for item in proposals:
			exp_config = item['proposal']['experiment_config']
			voltage_type = exp_config.get('Voltage Type', 'vbump')
			if voltage_type not in voltage_types_used:
				voltage_types_used[voltage_type] = []
			voltage_types_used[voltage_type].append(item['proposal']['description'])
		
		if len(voltage_types_used) > 1:
			self.logger("\nVOLTAGE TYPE SUMMARY:")
			self.logger("-" * 40)
			for voltage_type, experiments in voltage_types_used.items():
				self.logger(f"{voltage_type}:")
				for exp in experiments:
					self.logger(f"  - {exp}")
				if voltage_type == 'PPVC':
					self.logger("    Note: PPVC reduces voltage guardbands on ALL domains (IA and CFC)")
				elif voltage_type == 'vbump':
					self.logger("    Note: vbump is domain-specific voltage adjustment")
			self.logger("-" * 40)

	def _print_experiment_proposals(self):
		"""Print experiment proposals to console in proper format"""
		proposals = self.smart_experiment_proposal.get('recommended_sequence', [])
		
		self.logger("\n" + "="*80)
		self.logger("SMART EXPERIMENT PROPOSALS")
		self.logger("="*80)
		
		for item in proposals:
			seq_num = item['sequence_number']
			proposal = item['proposal']
			duration = item['estimated_duration']
			
			self.logger(f"\n{seq_num}. {proposal['description']}")
			self.logger(f"   Type: {proposal['type']}")
			self.logger(f"   Priority: {proposal['priority'].upper()}")
			self.logger(f"   Estimated Duration: {duration:.1f} minutes")
			self.logger(f"   Rationale: {proposal['rationale']}")
			
			# Print key experiment configuration parameters
			exp_config = proposal['experiment_config']
			self.logger("   Key Configuration:")
			
			key_params = ['Test Name', 'Test Type', 'Type', 'Domain', 'Start', 'End', 'Steps', 
						 'Loops', 'Voltage Type', 'Voltage IA', 'Voltage CFC', 
						 'Frequency IA', 'Frequency CFC', 'Content', 'Configuration (Mask)']
			
			for param in key_params:
				if param in exp_config and exp_config[param] is not None:
					self.logger(f"     {param}: {exp_config[param]}")
		
		total_time = sum(item['estimated_duration'] for item in proposals)
		self.logger(f"\nTotal Estimated Time for All Proposals: {total_time:.1f} minutes ({total_time/60:.1f} hours)")
		self.logger("="*80)
		
		# Also print a summary of voltage type recommendations
		self._print_voltage_type_summary(proposals)

	def _print_complete_flow_summary(self):
		"""Print complete summary with enhanced tabular data and detailed experiment information"""
		print("\n" + "="*120)
		print("COMPLETE FLOW EXECUTION SUMMARY")
		print("="*120)
		
		if not self.experiment_tracker:
			print("No experiment tracker available for summary")
			return
		
		# Get comprehensive data
		comprehensive_data = self.analysis_results
		flow_summary = comprehensive_data.get('flow_execution_summary', {})
		vf_analysis = comprehensive_data.get('voltage_frequency_analysis', {})
		
		# Flow Overview
		print("\n[DEBUG] FLOW OVERVIEW:")
		print(f"   Total Nodes Executed: {flow_summary.get('total_nodes_executed', 0)}")
		print(f"   Total Experiments: {len(self.experiment_tracker.experiments_history)}")
		print(f"   Recovery Conditions Found: {len(flow_summary.get('recovery_conditions', []))}")
		print(f"   Failure Conditions Found: {len(flow_summary.get('failure_conditions', []))}")
		
		# Detailed Iteration-by-Iteration Results Table
		self._print_detailed_iteration_table()
		
		# Sweep Analysis Tables
		self._print_sweep_analysis_tables()
		
		# Enhanced Voltage/Frequency Analysis
		self._print_enhanced_vf_analysis(vf_analysis)
		
		# Recovery Analysis
		self._print_recovery_analysis(comprehensive_data.get('recovery_analysis', {}))
		
		# Content Analysis
		self._print_content_analysis()

		# Smart Experiment Proposals
		self._print_smart_proposals()
		
		# File Locations
		self._print_file_locations()
		
		print("="*120)
		print("FLOW EXECUTION COMPLETE")
		print("="*120 + "\n")

	def _print_content_analysis(self):
		"""Print detailed content analysis with Dragon and Linux specific details"""
		content_analysis = self.analysis_results.get('content_analysis', {})
		
		if content_analysis.get('status') != 'analyzed':
			print(f"\n[INFO] CONTENT ANALYSIS: {content_analysis.get('status', 'Unknown')} - {content_analysis.get('message', 'No data')}")
			return
		
		print("\n[INFO] CONTENT ANALYSIS:")
		print("="*80)
		
		content_types = content_analysis.get('content_types_found', [])
		print(f"   Content Types Found: {', '.join(content_types)}")
		print(f"   Total Content Experiments: {content_analysis.get('total_content_experiments', 0)}")
		
		# Best overall failure reproduction
		best_overall = content_analysis.get('best_failure_reproduction')
		if best_overall:
			print("\n   [RESULTS] BEST FAILURE REPRODUCTION:")
			print(f"     Content Type: {best_overall['content_type']}")
			print(f"     Failure Count: {best_overall['failure_count']}")
			print(f"     Experiments: {', '.join(best_overall['experiments'])}")
			print(f"     Unique Scratchpads: {len(best_overall['scratchpads'])}")
			print(f"     Unique Seeds: {len(best_overall['seeds'])}")
			
			if best_overall['scratchpads']:
				print(f"     Scratchpads: {', '.join(best_overall['scratchpads'][:3])}{'...' if len(best_overall['scratchpads']) > 3 else ''}")
			
			print("     Configuration:")
			config = best_overall['configuration']
			
			# Show base configuration
			base_fields = ['mask', 'check_core', 'voltage_type', 'voltage_ia', 'voltage_cfc', 'frequency_ia', 'frequency_cfc']
			for field in base_fields:
				if config.get(field) is not None:
					print(f"       {field}: {config[field]}")
			
			# Show content-specific configuration
			if best_overall['content_type'].lower() == 'dragon':
				dragon_fields = ['vvar0', 'vvar1', 'vvar2', 'vvar3', 'vvar_extra', 'dragon_content_path', 'dragon_content_line']
				dragon_config = {k: v for k, v in config.items() if k in dragon_fields and v is not None}
				if dragon_config:
					print("       Dragon-specific config:")
					for key, value in dragon_config.items():
						print(f"         {key}: {value}")
			
			elif best_overall['content_type'].lower() == 'linux':
				linux_fields = [k for k in config.keys() if k.startswith('linux_content_line_')]
				if linux_fields:
					print("       Linux Content Lines:")
					for field in sorted(linux_fields):
						line_num = field.split('_')[-1]
						print(f"         Line {line_num}: {config[field]}")
		
		# Individual content type analysis
		content_data = content_analysis.get('content_analysis', {})
		for content_type, analysis in content_data.items():
			print(f"\n   [INFO] {content_type.upper()} CONTENT DETAILED ANALYSIS:")
			print(f"     Experiments: {analysis['total_experiments']}")
			print(f"     Total Iterations: {analysis['total_iterations']}")
			print(f"     Failures: {analysis['total_failures']} ({analysis['failure_rate']:.1f}%)")
			print(f"     Unique Failure Configs: {len(analysis['configuration_failures'])}")
			
			# Show best config for this content type with detailed breakdown
			best_config = analysis.get('best_failure_config')
			if best_config:
				print(f"\n     [RESULTS] BEST {content_type.upper()} CONFIGURATION:")
				print(f"       Failure Count: {best_config['failure_count']}")
				print(f"       Experiments: {', '.join(best_config['experiments'])}")
				print(f"       Scratchpads: {', '.join(list(best_config['scratchpads'])[:3])}{'...' if len(best_config['scratchpads']) > 3 else ''}")
				print(f"       Seeds: {', '.join(list(best_config['seeds'])[:5])}{'...' if len(best_config['seeds']) > 5 else ''}")
				
				# Show configuration details
				config = best_config['config']
				print("       Configuration Details:")
				
				# Base configuration
				base_fields = ['mask', 'check_core', 'voltage_type', 'voltage_ia', 'voltage_cfc', 'frequency_ia', 'frequency_cfc']
				for field in base_fields:
					if config.get(field) is not None:
						print(f"         {field}: {config[field]}")
				
				# Content-specific configuration
				if content_type.lower() == 'dragon':
					dragon_fields = ['vvar0', 'vvar1', 'vvar2', 'vvar3', 'vvar_extra', 'dragon_content_path', 'dragon_content_line']
					for field in dragon_fields:
						if config.get(field) is not None:
							print(f"         {field}: {config[field]}")
				
				elif content_type.lower() == 'linux':
					linux_fields = [k for k in config.keys() if k.startswith('linux_content_line_')]
					if linux_fields:
						print("         Linux Content Lines:")
						for field in sorted(linux_fields):
							line_num = field.split('_')[-1]
							print(f"           Line {line_num}: {config[field]}")
			
			# Show insights
			insights = analysis.get('content_specific_insights', [])
			if insights:
				print(f"\n     [INFO] {content_type.upper()} INSIGHTS:")
				for insight in insights:
					print(f"       • {insight}")

	def _print_detailed_iteration_table(self):
		"""Print detailed iteration-by-iteration results in table format"""
		print("\n[INFO] DETAILED ITERATION RESULTS:")
		print("="*120)
		
		# Define columns - easily configurable
		columns = [
			('Exp#', 4),
			('Iter', 4),
			('Test Name', 20),
			('Test Mode', 10),
			('Test Type', 10),
			('Content', 12),
			('Result', 8),
			('V_CFC', 8),
			('F_CFC', 8),
			('V_IA', 8),
			('F_IA', 8),
			('V_Type', 8),
			('Mask', 15),
			('Core', 6),
			('Sweep Val', 10)
		]
		
		# Print header
		header = " | ".join(f"{col[0]:<{col[1]}}" for col in columns)
		print(header)
		print("-" * len(header))
		
		# Print data rows
		for exp_idx, exp in enumerate(self.experiment_tracker.experiments_history):
			if exp is None:
				continue
				
			# Get experiment info
			exp_config = exp.get('experiment_config', {})
			iterations = exp.get('iterations', [])
			
			# If no iterations, show experiment-level info
			if not iterations:
				row_data = self._format_table_row(exp_idx + 1, 0, exp, exp_config, None)
				print(" | ".join(f"{str(data):<{columns[i][1]}}" for i, data in enumerate(row_data)))
			else:
				# Show each iteration
				for iteration in iterations:
					iter_num = iteration.get('iteration', 0)
					config_snapshot = iteration.get('config_snapshot', {})
					sweep_value = iteration.get('sweep_value')
					
					row_data = self._format_table_row(exp_idx + 1, iter_num, exp, exp_config, iteration, config_snapshot, sweep_value)
					print(" | ".join(f"{str(data):<{columns[i][1]}}" for i, data in enumerate(row_data)))
		
		print("="*120)

	def _format_table_row(self, exp_num, iter_num, exp, exp_config, iteration=None, config_snapshot=None, sweep_value=None):
		"""Format a single table row with experiment/iteration data"""
		
		# Helper function to safely get and truncate values
		def safe_get(source, key, default='', max_len=None):
			value = source.get(key, default) if source else default
			if value is None:
				value = ''
			value_str = str(value)
			if max_len and len(value_str) > max_len:
				value_str = value_str[:max_len-2] + '..'
			return value_str
		
		# Get result from iteration or experiment
		if iteration:
			result = iteration.get('status', '')
		else:
			result = exp.get('final_result', '')
		
		# Get configuration values (prefer runtime config from iteration, fallback to experiment config)
		if config_snapshot:
			voltage_cfc = safe_get(config_snapshot, 'voltage_cfc', safe_get(exp_config, 'Voltage CFC'))
			frequency_cfc = safe_get(config_snapshot, 'frequency_cfc', safe_get(exp_config, 'Frequency CFC'))
			voltage_ia = safe_get(config_snapshot, 'voltage_ia', safe_get(exp_config, 'Voltage IA'))
			frequency_ia = safe_get(config_snapshot, 'frequency_ia', safe_get(exp_config, 'Frequency IA'))
			voltage_type = safe_get(config_snapshot, 'voltage_type', safe_get(exp_config, 'Voltage Type'))
			content = safe_get(config_snapshot, 'content', safe_get(exp_config, 'Content'))
			mask = safe_get(config_snapshot, 'mask', safe_get(exp_config, 'Configuration (Mask)'))
			check_core = safe_get(config_snapshot, 'check_core', safe_get(exp_config, 'Check Core'))
		else:
			voltage_cfc = safe_get(exp_config, 'Voltage CFC')
			frequency_cfc = safe_get(exp_config, 'Frequency CFC')
			voltage_ia = safe_get(exp_config, 'Voltage IA')
			frequency_ia = safe_get(exp_config, 'Frequency IA')
			voltage_type = safe_get(exp_config, 'Voltage Type')
			content = safe_get(exp_config, 'Content')
			mask = safe_get(exp_config, 'Configuration (Mask)')
			check_core = safe_get(exp_config, 'Check Core')
		
		return [
			exp_num,
			iter_num if iter_num > 0 else '',
			safe_get(exp_config, 'Test Name', max_len=18),
			safe_get(exp_config, 'Test Mode', max_len=8),
			safe_get(exp_config, 'Test Type', max_len=8),
			safe_get({'Content': content}, 'Content', max_len=10),
			result[:6] if result else '',
			voltage_cfc[:6] if voltage_cfc else '',
			frequency_cfc[:6] if frequency_cfc else '',
			voltage_ia[:6] if voltage_ia else '',
			frequency_ia[:6] if frequency_ia else '',
			voltage_type[:6] if voltage_type else '',
			mask[:13] if mask else '',
			check_core[:4] if check_core else '',
			str(sweep_value)[:8] if sweep_value is not None else ''
		]

	def _print_sweep_analysis_tables(self):
		"""Print detailed sweep analysis tables showing values and results"""
		print("\n[INFO] SWEEP ANALYSIS DETAILS:")
		print("="*80)
		
		sweep_experiments = [exp for exp in self.experiment_tracker.experiments_history 
							if exp and exp.get('sweep_data')]
		
		if not sweep_experiments:
			print("   No sweep experiments found")
			return
		
		for exp in sweep_experiments:
			self._print_single_sweep_table(exp)

	def _print_single_sweep_table(self, exp):
		"""Print detailed table for a single sweep experiment"""
		node_name = exp.get('node_name', 'Unknown')
		sweep_data = exp.get('sweep_data', {})
		sweep_analysis = exp.get('sweep_analysis', {})
		iterations = exp.get('iterations', [])
		
		sweep_type = sweep_data.get('sweep_type', 'Unknown')
		sweep_domain = sweep_data.get('sweep_domain', 'Unknown')
		voltage_type = sweep_data.get('voltage_type', 'Unknown')
		
		print(f"\n[DEBUG] {node_name} - {sweep_type.title()} {sweep_domain.upper()} Sweep ({voltage_type})")
		print("-" * 60)
		
		if not iterations:
			print("   No iteration data available")
			return
		
		# Create sweep results table
		print(f"{'Point':<6} {'Value':<10} {'Result':<8} {'V_IA':<8} {'V_CFC':<8} {'F_IA':<8} {'F_CFC':<8}")
		print("-" * 60)
		
		for i, iteration in enumerate(iterations):
			sweep_value = iteration.get('sweep_value', 'N/A')
			status = iteration.get('status', 'Unknown')
			config = iteration.get('config_snapshot', {})
			
			# Format values
			v_ia = f"{config.get('voltage_ia', ''):.3f}" if config.get('voltage_ia') is not None else ''
			v_cfc = f"{config.get('voltage_cfc', ''):.3f}" if config.get('voltage_cfc') is not None else ''
			f_ia = f"{config.get('frequency_ia', '')}" if config.get('frequency_ia') is not None else ''
			f_cfc = f"{config.get('frequency_cfc', '')}" if config.get('frequency_cfc') is not None else ''
			
			sweep_val_str = f"{sweep_value:.3f}" if isinstance(sweep_value, (int, float)) else str(sweep_value)
			
			print(f"{i+1:<6} {sweep_val_str:<10} {status:<8} {v_ia:<8} {v_cfc:<8} {f_ia:<8} {f_cfc:<8}")
		
		# Show sweep analysis summary
		if sweep_analysis:
			sensitivity = sweep_analysis.get('sensitivity_analysis', {})
			pattern = sensitivity.get('pattern', 'Unknown')
			description = sensitivity.get('description', 'No description')
			recommendation = sensitivity.get('recommendation', 'No recommendation')
			
			print("\n   Analysis:")
			print(f"     Pattern: {pattern}")
			print(f"     Description: {description}")
			print(f"     Recommendation: {recommendation}")
			
			# Show failure/pass ranges if available
			failure_range = sensitivity.get('failure_range')
			pass_range = sensitivity.get('pass_range')
			safe_values = sensitivity.get('safe_values', [])
			
			if failure_range:
				print(f"     Failure Range: {failure_range[0]} to {failure_range[1]}")
			if pass_range:
				print(f"     Pass Range: {pass_range[0]} to {pass_range[1]}")
			if safe_values:
				print(f"     Safe Values: {safe_values}")

	def _print_enhanced_vf_analysis(self, vf_analysis):
		"""Print enhanced voltage/frequency analysis with detailed statistics"""
		print("\n[INFO] VOLTAGE/FREQUENCY SENSITIVITY ANALYSIS:")
		print("="*80)
		
		voltage_sens = vf_analysis.get('voltage_sensitivity', {})
		frequency_sens = vf_analysis.get('frequency_sensitivity', {})
		combined = vf_analysis.get('combined_analysis', {})
		
		# Voltage Analysis
		if voltage_sens.get('status') == 'analyzed':
			debug_info = voltage_sens.get('debug_info', {})
			print("\n[DEBUG] VOLTAGE ANALYSIS:")
			print(f"   Total Voltage Experiments: {debug_info.get('total_voltage_experiments', 0)}")
			print(f"   Experiment Names: {', '.join(debug_info.get('voltage_experiment_names', []))}")
			
			# IA Voltage
			ia_voltage = voltage_sens.get('ia_voltage_sensitivity', {})
			if ia_voltage.get('status') == 'analyzed':
				self._print_domain_analysis('IA Voltage', ia_voltage)
			
			# CFC Voltage
			cfc_voltage = voltage_sens.get('cfc_voltage_sensitivity', {})
			if cfc_voltage.get('status') == 'analyzed':
				self._print_domain_analysis('CFC Voltage', cfc_voltage)
			
			print(f"   Overall Voltage Conclusion: {voltage_sens.get('overall_voltage_conclusion', 'Unknown')}")
		else:
			print(f"\n[DEBUG] VOLTAGE ANALYSIS: {voltage_sens.get('status', 'Unknown')} - {voltage_sens.get('conclusion', 'No data')}")
		
		# Frequency Analysis
		if frequency_sens.get('status') == 'analyzed':
			debug_info = frequency_sens.get('debug_info', {})
			print("\n[DEBUG] FREQUENCY ANALYSIS:")
			print(f"   Total Frequency Experiments: {debug_info.get('total_frequency_experiments', 0)}")
			print(f"   Experiment Names: {', '.join(debug_info.get('frequency_experiment_names', []))}")
			
			# IA Frequency
			ia_frequency = frequency_sens.get('ia_frequency_sensitivity', {})
			if ia_frequency.get('status') == 'analyzed':
				self._print_domain_analysis('IA Frequency', ia_frequency)
			
			# CFC Frequency
			cfc_frequency = frequency_sens.get('cfc_frequency_sensitivity', {})
			if cfc_frequency.get('status') == 'analyzed':
				self._print_domain_analysis('CFC Frequency', cfc_frequency)
			
			print(f"   Overall Frequency Conclusion: {frequency_sens.get('overall_frequency_conclusion', 'Unknown')}")
		else:
			print(f"\n[DEBUG] FREQUENCY ANALYSIS: {frequency_sens.get('status', 'Unknown')} - {frequency_sens.get('conclusion', 'No data')}")
		
		# Combined Analysis
		if combined.get('conclusion'):
			print("\n[DEBUG] COMBINED ANALYSIS:")
			print(f"   Voltage Sensitive: {combined.get('voltage_sensitive', False)}")
			print(f"   Frequency Sensitive: {combined.get('frequency_sensitive', False)}")
			print(f"   Conclusion: {combined['conclusion']}")

	def _print_domain_analysis(self, domain_name, domain_data):
		"""Print detailed analysis for a specific domain"""
		print(f"\n   {domain_name}:")
		print(f"     Experiments: {domain_data.get('experiments_count', 0)}")
		print(f"     Dominant Pattern: {domain_data.get('dominant_pattern', 'Unknown')}")
		print(f"     Recovery Experiments: {domain_data.get('recovery_experiments', 0)}/{domain_data.get('experiments_count', 0)}")
		print(f"     All Patterns: {domain_data.get('all_patterns', [])}")
		print(f"     Conclusion: {domain_data.get('conclusion', 'No conclusion')}")

	def _print_recovery_analysis(self, recovery_analysis):
		"""Print detailed recovery analysis"""
		print("\n[INFO] RECOVERY ANALYSIS:")
		print("="*50)
		
		if recovery_analysis.get('status') == 'recovery_found':
			print(f"   Recovery Conditions Found: {recovery_analysis.get('total_recovery_conditions', 0)}")
			print(f"   Recovery Success Rate: {recovery_analysis.get('recovery_success_rate', 0):.1%}")
			
			best_recovery = recovery_analysis.get('best_recovery_condition', {})
			if best_recovery:
				print("\n   Best Recovery Condition:")
				print(f"     Node: {best_recovery.get('node_name', 'Unknown')}")
				print(f"     Success Rate: {best_recovery.get('pass_rate', 0):.1%}")
				
				# Show recovery configuration
				config = best_recovery.get('config', {})
				if config:
					print("     Configuration:")
					for key, value in config.items():
						if value is not None:
							print(f"       {key}: {value}")
			
			# Show recovery patterns
			recovery_patterns = recovery_analysis.get('recovery_patterns', {})
			if recovery_patterns:
				print("\n   Recovery Patterns:")
				print(f"     Voltage-based: {recovery_patterns.get('voltage_based_recoveries', 0)}")
				print(f"     Frequency-based: {recovery_patterns.get('frequency_based_recoveries', 0)}")
				print(f"     Content-based: {recovery_patterns.get('content_based_recoveries', 0)}")
		else:
			print(f"   Status: {recovery_analysis.get('status', 'Unknown')}")

	def _print_smart_proposals(self):
		"""Print smart experiment proposals"""
		if hasattr(self, 'smart_experiment_proposal') and self.smart_experiment_proposal:
			proposals = self.smart_experiment_proposal.get('recommended_sequence', [])
			print("\n[DEBUG] SMART EXPERIMENT PROPOSALS:")
			print("="*60)
			print(f"   Total Proposals: {len(proposals)}")
			
			if proposals:
				print(f"\n{'#':<3} {'Priority':<10} {'Type':<20} {'Description':<40} {'Time':<8}")
				print("-" * 85)
				
				for i, item in enumerate(proposals):
					proposal = item['proposal']
					duration = item['estimated_duration']
					
					print(f"{i+1:<3} {proposal['priority'].upper():<10} {proposal['type']:<20} {proposal['description'][:38]:<40} {duration:.1f}m")
				
				total_time = sum(item['estimated_duration'] for item in proposals)
				print(f"\n   Total Estimated Time: {total_time:.1f} minutes ({total_time/60:.1f} hours)")

	def _print_file_locations(self):
		"""Print file locations and output paths"""
		print("\n[INFO]OUTPUT FILES:")
		print("="*40)
		
		if hasattr(self, 'summary_report_path') and self.summary_report_path:
			print(f"   Comprehensive Report: {self.summary_report_path}")
		
		# Show unique test folders
		test_folders = set()
		for exp in self.experiment_tracker.experiments_history:
			if exp and exp.get('test_folder'):
				test_folders.add(exp['test_folder'])
		
		if test_folders:
			print("   Test Folders:")
			for folder in sorted(test_folders):
				print(f"     {folder}")
		
		# Show INI file location
		if self.experiment_tracker.flow_config_path:
			print(f"   Flow Configuration: {self.experiment_tracker.flow_config_path}")
		
# ==================== EXPERIMENT BUILDER AND EXECUTOR ====================

class FlowTestExecutor:
	"""
	Enhanced executor with Framework API integration and comprehensive logging.
	"""

	def __init__(self, root, framework=None, execution_state = None, experiment_tracker = None):

		self.root = root
		self.framework = framework
		self.execution_state = execution_state
		self.experiment_tracker = experiment_tracker
		self.framework_api = None
		self.execution_log = []
		self.start_time = None
		self.execution_state = None
		self.status_callback = None
		
		# Cleanup tracking
		self._nodes_with_active_experiments = []
		self._cleanup_lock = threading.Lock()
	   
		self._reset_hardware_fails()
		# Hardware failure tracking
		#self._hardware_failure_detected = False
		#self._flow_abort_requested = False
		#self._abort_reason = None

		# Hardware Fail termination flag
		#self._hardware_failure_termination = False
		#self._unwired_port_termination = False
		#self._termination_type = None
		#self._termination_node = None
	
	def set_framework_api(self, framework_api):
		"""Set framework API dynamically during execution"""
		self.framework_api = framework_api
		print(f"FlowTestExecutor: Set framework_api: {framework_api}")

	def set_status_callback(self, callback):
		"""Set callback for status updates."""
		self.status_callback = callback
	
	# OLD METHOD -- Check and delete
	def _set_api_for_all_nodes(self, node, visited=None):
		"""
		Recursively set Framework API reference for all nodes in the flow.
		"""
		if visited is None:
			visited = set()
		
		if node.ID in visited:
			return
		
		visited.add(node.ID)
		node.framework_api = self.framework_api
		
		# Recursively set for connected nodes
		for next_node in node.outputNodeMap.values():
			self._set_api_for_all_nodes(next_node, visited)

	def execute(self):
		"""
		Execute the flow with comprehensive termination handling and ThreadsHandler integration.
		"""
		self._reset_hardware_fails()
		self.start_time = datetime.now()
		self.log_execution("Flow execution started")
		
		# Cleans data to Start Fresh
		if self.experiment_tracker.flow_summary['total_nodes_executed'] > 0:
			self.experiment_tracker.reset_data()
			self.experiment_tracker.flow_summary['start_time'] = datetime.now()
		try:
			current_node = self.root
			node_count = 0
			
			while current_node is not None and node_count < 50:
				# Check ThreadsHandler for termination conditions FIRST
				if self._should_terminate_flow():
					break
				
				# Check for cancellation/end commands using ThreadsHandler
				if self.execution_state:
					if self.execution_state.is_cancelled():
						self.log_execution("Flow execution cancelled by user")
						# Acknowledge the cancel command
						self.execution_state.acknowledge_command(ExecutionCommand.CANCEL, 
															   "Flow execution cancelled")
						break
					if self.execution_state.is_ended():
						self.log_execution("Flow execution ended by user")
						# Acknowledge the end command
						self.execution_state.acknowledge_command(ExecutionCommand.END_EXPERIMENT, 
															   "Flow execution ended")
						break
					
				node_count += 1

				if self.framework_api:
					current_node.framework_api = self.framework_api
									
				self.log_execution(f"Executing node: {current_node.Name} (ID: {current_node.ID})")

				# FIXED: Notify that node is starting (should turn blue)
				if self.status_callback:
					self.status_callback('current_node', {
						'node_id': current_node.ID,
						'node_name': current_node.Name,
						'experiment_name': self._get_experiment_name(current_node)
					})
					
				# Notify status callback
				#if self.status_callback:
				#	self.status_callback('node_start', current_node)                

				# Check for cancellation before execution
				if self.execution_state and (self.execution_state.is_cancelled() or self.execution_state.is_ended()):
					break
				
				# Execute the current node
				start_time = time.time()
				node_success = True
				
				try:
					# FIXED: Notify that node experiment is running (should turn red)
					if self.status_callback:
						self.status_callback('node_running', {
							'node_id': current_node.ID,
							'node_name': current_node.Name
						})
					current_node.run_experiment()
					
					# Check for hardware failures after node execution
					if self._detect_hardware_failure_in_node(current_node):
						self.log_execution(f"HARDWARE FAILURE detected in node: {current_node.Name}")
						self._trigger_hardware_failure_termination(current_node)
						node_success = False
						break
						
				except KeyboardInterrupt:
					self.log_execution(f"Node execution interrupted: {current_node.Name}")
					node_success = False
					break
				except Exception as e:
					self.log_execution(f"Node execution failed: {current_node.Name} - {e}")
					node_success = False
					# Check if this is a hardware-related exception
					if self._is_hardware_related_exception(e):
						self._trigger_hardware_failure_termination(current_node, str(e))
						break
				
				execution_time = time.time() - start_time

				# Check for cancellation after execution using ThreadsHandler
				if self.execution_state and (self.execution_state.is_cancelled() or self.execution_state.is_ended()):
					break
								
				# Log execution results
				if node_success:
					summary = current_node.get_execution_summary()
					self.log_execution(f"Node completed in {execution_time:.1f}s: {summary}")

					# FIXED: Determine if node passed or failed based on results
					
					if self.status_callback:
						self.status_callback('node_completed', {
							'node_id': current_node.ID,
							'node_name': current_node.Name
						})

				else:
					self.log_execution(f"Node failed in {execution_time:.1f}s: {current_node.Name}")
					if self.status_callback:
						self.status_callback('node_execution_fail', {
							'node_id': current_node.ID,
							'node_name': current_node.Name
						})
				# Notify status callback
				if self.status_callback:
					self.status_callback('node_complete', current_node)
								
				# Get next node with unwired port handling
				next_node = None
				if node_success:
					next_node = current_node.get_next_node()
					
					# Check if node requested termination due to unwired port
					if self._check_node_termination_request(current_node):
						break

				if next_node:
					self.log_execution(f"Moving to next node: {next_node.Name}")
				else:
					if node_success:
						if hasattr(current_node, 'flow_should_terminate') and current_node.flow_should_terminate:
							# Node requested termination due to unwired port
							self.log_execution("Flow terminated due to unwired port")
						else:
							# Normal flow completion
							self.log_execution("Flow execution completed - no more nodes")
					else:
						self.log_execution("Flow execution stopped due to node failure")
				
				current_node = next_node
			
			if node_count >= 50:
				self.log_execution("WARNING: Flow execution stopped due to safety limit (50 nodes)")
				
		except KeyboardInterrupt:
			self.log_execution("Flow execution interrupted by user")
			# Notify ThreadsHandler of interruption
			if self.execution_state:
				self.execution_state.cancel("Flow execution interrupted by user")
		except Exception as e:
			self.log_execution(f"ERROR: Flow execution failed: {e}")
			raise
		finally:
			# Log final status with termination details
			self._log_final_termination_status()
			
			total_time = (datetime.now() - self.start_time).total_seconds()
			self.log_execution(f"Flow execution finished. Total time: {total_time:.1f}s")

	def _get_experiment_name(self, node):
		"""Get experiment name for display."""
		if hasattr(node, 'Experiment') and node.Experiment:
			return node.Experiment.get('Test Name', f"Node: {node.Name}")
		return f"Node: {node.Name}"

	def _trigger_hardware_failure_termination(self, failed_node, reason=None):
		"""
		Trigger immediate hardware failure termination and notify ThreadsHandler.
		"""
		self._hardware_failure_termination = True
		self._hardware_failure_detected = True
		self._flow_abort_requested = True
		
		if reason:
			self._abort_reason = f"Hardware failure in node {failed_node.Name}: {reason}"
		else:
			self._abort_reason = f"Hardware failure detected in node {failed_node.Name}"
		
		termination_message = f"HARDWARE FAILURE TERMINATION TRIGGERED: {self._abort_reason}"
		self.log_execution(termination_message)
		
		# Notify ThreadsHandler of hardware failure
		if self.execution_state:
			self.execution_state.cancel(self._abort_reason)
		
		# Notify status callback about hardware failure termination
		if self.status_callback:
			self.status_callback('hardware_failure_termination', {
				'failed_node': failed_node.Name,
				'failed_node_id': failed_node.ID,
				'reason': self._abort_reason,
				'timestamp': datetime.now().isoformat(),
				'termination_type': 'hardware_failure'
			})
		
		# Try to cancel any running framework experiments immediately
		try:
			if self.framework_api:
				cancel_result = self.framework_api.cancel_experiment()
				self.log_execution(f"Framework experiment emergency cancellation: {cancel_result.get('success', False)}")
		except Exception as e:
			self.log_execution(f"Error cancelling framework experiment during termination: {e}")
					
	def _should_abort_flow(self) -> bool:
		"""Check if flow should be aborted due to hardware failures."""
		return self._flow_abort_requested or self._hardware_failure_detected

	def _detect_hardware_failure_in_node(self, node) -> bool:
		"""
		ENHANCED: Detect hardware failures with immediate termination logic.
		"""
		try:
			# Check the node's status history for hardware failure indicators
			if hasattr(node, 'runStatusHistory') and node.runStatusHistory:
				for status in node.runStatusHistory:
					if self._is_hardware_failure_status(status):
						self.log_execution(f"Hardware failure status detected: {status}")
						return True
			
			# Check execution stats for hardware failure patterns
			if hasattr(node, 'execution_stats') and node.execution_stats:
				stats = node.execution_stats
				
				# Check for high execution failure rate
				execution_fail_count = stats.get('execution_fail_count', 0)
				total_completed = stats.get('total_completed', 0)
				
				if total_completed > 0:
					execution_fail_rate = execution_fail_count / total_completed
					if execution_fail_rate > 0.4:  # 40% threshold
						self.log_execution(f"Hardware failure threshold exceeded: {execution_fail_rate:.1%}")
						return True
			
			# [DONE] Check if node set output port to 3 (hardware failure port)
			if hasattr(node, 'outputPort') and node.outputPort == 3:
				self.log_execution("Node routed to hardware failure port (3)")
				return True
			
			return False
			
		except Exception as e:
			self.log_execution(f"Error detecting hardware failure in node {node.Name}: {e}")
			return False

	def _is_hardware_failure_status(self, status: str) -> bool:
		"""
		Check if a status indicates a hardware failure.
		
		Args:
			status: Status string to check
			
		Returns:
			bool: True if status indicates hardware failure
		"""
		status_upper = status.upper()
		hardware_failure_statuses = [
			TestStatus.EXECUTION_FAIL.value,
			TestStatus.FAILED.value,
			TestStatus.PYTHON_FAIL.value
		]
		
		return status_upper in hardware_failure_statuses

	def _is_hardware_related_exception(self, exception: Exception) -> bool:
		"""
		Check if an exception is likely hardware-related.
		
		Args:
			exception: Exception to check
			
		Returns:
			bool: True if likely hardware-related
		"""
		exception_str = str(exception).lower()
		hardware_keywords = [
			'regaccfail',
			'rsp 10',
			'hardware',
			'device',
			'connection',
			'timeout',
			'communication',
			'ipc',
			'serial'
		]
		
		return any(keyword in exception_str for keyword in hardware_keywords)

	def _jump_to_end_node(self):
		"""
		NEW: Jump directly to the end node, bypassing all intermediate nodes.
		"""
		try:
			self.log_execution("Searching for end node to terminate flow...")
			
			# Find the end node in the flow
			end_node = self._find_end_node()
			
			if end_node:
				self.log_execution(f"Found end node: {end_node.Name} (ID: {end_node.ID})")
				
				# Set framework API for end node if needed
				if self.framework_api:
					end_node.framework_api = self.framework_api
				
				# Execute the end node
				self.log_execution(f"Executing end node: {end_node.Name}")
				
				if self.status_callback:
					self.status_callback('node_start', end_node)
				
				try:
					end_node.run_experiment()
					
					if self.status_callback:
						self.status_callback('node_complete', end_node)
					
					self.log_execution(f"End node executed successfully: {end_node.Name}")
					
				except Exception as e:
					self.log_execution(f"Error executing end node: {e}")
				
			else:
				self.log_execution("No end node found - flow will terminate without end node execution")
				
		except Exception as e:
			self.log_execution(f"Error jumping to end node: {e}")

	def _find_end_node(self):
		"""
		NEW: Find the end node in the built flow structure.
		
		Returns:
			EndNodeFlowInstance or None if not found
		"""
		try:
			# Search through all built nodes for an EndNode
			for node_id, node in self.builtNodes.items() if hasattr(self, 'builtNodes') else []:
				if isinstance(node, EndNodeFlowInstance):
					return node
			
			# If no built nodes available, search from root
			if hasattr(self, 'root') and self.root:
				return self._search_for_end_node_recursive(self.root, visited=set())
			
			return None
			
		except Exception as e:
			self.log_execution(f"Error finding end node: {e}")
			return None

	def _search_for_end_node_recursive(self, current_node, visited=None):
		"""
		NEW: Recursively search for end node in the flow structure.
		
		Args:
			current_node: Current node to search from
			visited: Set of visited node IDs to prevent cycles
			
		Returns:
			EndNodeFlowInstance or None if not found
		"""
		if visited is None:
			visited = set()
		
		if current_node.ID in visited:
			return None
		
		visited.add(current_node.ID)
		
		# Check if current node is an end node
		if isinstance(current_node, EndNodeFlowInstance):
			return current_node
		
		# Search through output nodes
		if hasattr(current_node, 'outputNodeMap') and current_node.outputNodeMap:
			for next_node in current_node.outputNodeMap.values():
				end_node = self._search_for_end_node_recursive(next_node, visited)
				if end_node:
					return end_node
		
		return None					
		
	def _request_flow_abort(self, reason: str, failed_node=None):
		"""
		Request flow abortion due to hardware failure.
		
		Args:
			reason: Reason for abortion
			failed_node: Node that caused the failure (optional)
		"""
		self._flow_abort_requested = True
		self._hardware_failure_detected = True
		self._abort_reason = reason
		
		abort_message = f"FLOW ABORTION REQUESTED: {reason}"
		if failed_node:
			abort_message += f" (Node: {failed_node.Name})"
		
		self.log_execution(abort_message)
		
		# Notify status callback about flow abortion
		if self.status_callback:
			self.status_callback('flow_abort_requested', {
				'reason': reason,
				'failed_node': failed_node.Name if failed_node else None,
				'timestamp': datetime.now().isoformat()
			})
		
		# Try to cancel any running framework experiments
		try:
			if self.framework_api:
				cancel_result = self.framework_api.cancel_experiment()
				self.log_execution(f"Framework experiment cancellation: {cancel_result.get('success', False)}")
		except Exception as e:
			self.log_execution(f"Error cancelling framework experiment during abort: {e}")
 
	def _should_terminate_flow(self) -> bool:
		"""
		ENHANCED: Check if flow should terminate for any reason using ThreadsHandler.
		"""
		# Check ThreadsHandler state
		if self.execution_state and self.execution_state.should_stop():
			return True
			
		return (self._hardware_failure_termination or 
				self._unwired_port_termination or 
				self._flow_abort_requested)

	def _check_node_termination_request(self, node) -> bool:
		"""
		Check if node requested flow termination due to unwired port.
		"""
		if hasattr(node, 'flow_should_terminate') and node.flow_should_terminate:
			termination_type = getattr(node, 'termination_type', 'unknown')
			termination_reason = getattr(node, 'termination_reason', 'Unknown reason')
			
			self._unwired_port_termination = True
			self._termination_type = termination_type
			self._termination_node = node
			self._abort_reason = termination_reason
			
			self.log_execution(f"UNWIRED PORT TERMINATION requested by node: {node.Name}")
			self.log_execution(f"Termination type: {termination_type}")
			self.log_execution(f"Reason: {termination_reason}")
			
			# Notify ThreadsHandler of unwired port termination
			if self.execution_state:
				self.execution_state.end_experiment(termination_reason)
			
			# Notify status callback
			if self.status_callback:
				self.status_callback('unwired_port_termination', {
					'node_name': node.Name,
					'node_id': node.ID,
					'termination_type': termination_type,
					'reason': termination_reason,
					'output_port': getattr(node, 'outputPort', 'unknown'),
					'timestamp': datetime.now().isoformat()
				})
			
			return True
		
		return False

	def get_flow_status(self) -> Dict:
		"""
		ENHANCED: Get comprehensive flow status including all termination types.
		"""
		return {
			'is_running': self.start_time is not None,
			'hardware_failure_detected': self._hardware_failure_detected,
			'hardware_failure_termination': self._hardware_failure_termination,
			'unwired_port_termination': self._unwired_port_termination,
			'flow_abort_requested': self._flow_abort_requested,
			'termination_type': self._termination_type,
			'terminating_node': self._termination_node.Name if self._termination_node else None,
			'abort_reason': self._abort_reason,
			'nodes_executed': len(self.execution_log),
			'active_experiments': len(self._nodes_with_active_experiments),
			'execution_time': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
		}

	def get_termination_report(self) -> Dict:
		"""
		NEW: Get detailed termination report for debugging and analysis.
		"""
		return {
			'termination_occurred': (self._hardware_failure_termination or 
								   self._unwired_port_termination or 
								   self._flow_abort_requested),
			'termination_details': {
				'hardware_failure': self._hardware_failure_termination,
				'unwired_port': self._unwired_port_termination,
				'user_abort': self._flow_abort_requested and not self._hardware_failure_termination and not self._unwired_port_termination,
				'termination_type': self._termination_type,
				'terminating_node': {
					'name': self._termination_node.Name if self._termination_node else None,
					'id': self._termination_node.ID if self._termination_node else None,
					'output_port': getattr(self._termination_node, 'outputPort', None) if self._termination_node else None
				},
				'reason': self._abort_reason,
				'timestamp': datetime.now().isoformat()
			},
			'execution_summary': {
				'total_time': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
				'nodes_executed': len(self.execution_log),
				'completed_normally': not (self._hardware_failure_termination or self._unwired_port_termination or self._flow_abort_requested)
			}
		}

	# Add reference to builtNodes from builder
	def set_built_nodes_reference(self, built_nodes):
		"""Set reference to built nodes for end node searching."""
		self.builtNodes = built_nodes
		
	def _cleanup_node_experiment(self, node):
		"""Clean up experiment resources for a specific node."""
		try:
			if hasattr(node, 'framework_api') and node.framework_api:
				self.log_execution(f"Cleaning up experiment for node: {node.Name}")
				node.framework_api.cleanup_step_experiment()
				
				# Remove from tracking
				with self._cleanup_lock:
					if node in self._nodes_with_active_experiments:
						self._nodes_with_active_experiments.remove(node)
						
		except Exception as e:
			self.log_execution(f"Error cleaning up node {node.Name}: {e}")

	def _cleanup_all_experiments(self):
		"""Clean up all remaining experiment resources."""
		self.log_execution("Performing comprehensive experiment cleanup")
		
		try:
			# Cleanup tracked nodes
			with self._cleanup_lock:
				nodes_to_cleanup = list(self._nodes_with_active_experiments)
				self._nodes_with_active_experiments.clear()
			
			for node in nodes_to_cleanup:
				self._cleanup_node_experiment(node)
			
			# Global framework API cleanup
			if self.framework_api:
				self.log_execution("Performing global framework API cleanup")
				self.framework_api.cleanup_step_experiment()
			
			self.log_execution("Comprehensive cleanup completed")
			
		except Exception as e:
			self.log_execution(f"Error during comprehensive cleanup: {e}")

	def _reset_hardware_fails(self):
		   
		# Hardware failure tracking
		self._hardware_failure_detected = False
		self._flow_abort_requested = False
		self._abort_reason = None

		# Hardware Fail termination flag
		self._hardware_failure_termination = False
		self._unwired_port_termination = False
		self._termination_type = None
		self._termination_node = None

	# Not used -- Check and delete
	def force_stop_all_experiments(self):
		"""Force stop all running experiments (emergency cleanup)."""
		self.log_execution("EMERGENCY: Force stopping all experiments")
		
		try:
			# Cancel all framework experiments
			if self.framework_api:
				self.framework_api.cancel_experiment()
			
			# Force cleanup all nodes
			self._cleanup_all_experiments()
			
			self.log_execution("Emergency stop completed")
			
		except Exception as e:
			self.log_execution(f"Error during emergency stop: {e}")

	def _log_final_termination_status(self):
		"""
		NEW: Log comprehensive final termination status.
		"""
		if self._hardware_failure_termination:
			self.log_execution("FINAL STATUS: HARDWARE FAILURE TERMINATION")
			self.log_execution(f"Reason: {self._abort_reason}")
		elif self._unwired_port_termination:
			self.log_execution("FINAL STATUS: UNWIRED PORT TERMINATION")
			self.log_execution(f"Termination Type: {self._termination_type}")
			self.log_execution(f"Terminating Node: {self._termination_node.Name if self._termination_node else 'Unknown'}")
			self.log_execution(f"Reason: {self._abort_reason}")
		elif self._flow_abort_requested:
			self.log_execution("FINAL STATUS: FLOW ABORTED")
			self.log_execution(f"Reason: {self._abort_reason}")
		else:
			self.log_execution("FINAL STATUS: NORMAL COMPLETION")

	def log_execution(self, message):
		"""Thread-safe logging that doesn't interfere with UI."""
		timestamp = datetime.now().strftime("%H:%M:%S")
		log_entry = f"[{timestamp}] {message}"
		self.execution_log.append(log_entry)
		
		# FIXED: Send 'status_update' instead of 'log_message' for general logging
		if self.status_callback:
			self.status_callback('status_update', {'message': message})

	def get_execution_report(self):
		"""Generate a comprehensive execution report."""
		return {
			'start_time': self.start_time,
			'execution_log': self.execution_log,
			'total_time': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
			'hardware_failure_detected': self._hardware_failure_detected,
			'flow_aborted': self._flow_abort_requested,
			'abort_reason': self._abort_reason
		}

	def __del__(self):
		"""Destructor to ensure cleanup."""
		try:
			self._cleanup_all_experiments()
		except Exception as e:
			print(f"Error in FlowTestExecutor destructor: {e}")

class FlowTestBuilder:
	"""
	Enhanced builder with Framework integration and better error handling.
	"""

	def __init__(self, structureFilePath: str, flowsFilePath: str, iniFilePath: str, Framework=None, framework_utils = None, logger=None):
		if not logger: 
			logger = print
		self.logger = logger

		self.structureFilePath = structureFilePath
		self.flowsFilePath = flowsFilePath
		self.iniFilePath = iniFilePath
		self.Framework = Framework
		self.framework_utils = framework_utils
		try:
			# Load configuration files
			self.structureFile = fh.load_json(structureFilePath)
			self.flowsFile = fh.load_json(flowsFilePath)
			self.initFile = fh.ini_to_dict_with_types(iniFilePath, convert_key_underscores=True)
			
			self.logger(f"Loaded structure file: {len(self.structureFile)} nodes")
			self.logger(f"Loaded flows file: {len(self.flowsFile)} flows")
			self.logger(f"Loaded ini file: {len(self.initFile)} configurations")
			
		except Exception as e:
			self.logger(f"Error loading configuration files: {e}")
			raise

		# Dictionary to store built nodes
		self.builtNodes = {}

		# UI configuration
		self.status_colors = {'default': 'gray', 'running': 'blue', 'success': 'green', 'failed': 'red'}
		self.connection_colors = ['orange', 'purple', 'yellow', 'brown']
		self.node_width, self.node_height = 70, 120
		self.square_size = 15

		# Initialize experiment tracker
		self.experiment_tracker = ExperimentTracker(iniFilePath)
		self.experiment_tracker.flow_summary['start_time'] = datetime.now()
	
	def build_flow(self, rootID, execution_state=None):
		"""
		Build and return an enhanced executor for the flow starting at rootID.
		[DONE] SINGLE PLACE where FlowTestExecutor is created.
		"""
		try:
			root = self.__build_instance(rootID)
			
			# ONLY PLACE: Create FlowTestExecutor
			executor = FlowTestExecutor(
				root=root, 
				framework=self.Framework,
				execution_state=execution_state,
				experiment_tracker = self.experiment_tracker  # Pass ThreadsHandler to executor
			)
			
			# [DONE] Pass built nodes reference to executor for end node searching
			executor.set_built_nodes_reference(self.builtNodes)
			
			self.logger(f"Flow built successfully with root: {rootID}")
			self.logger(f"Total nodes in flow: {len(self.builtNodes)}")
			
			return executor
			
		except Exception as e:
			self.logger(f"Error building flow: {e}")
			raise

	def __build_instance(self, flowKey):
		"""
		Enhanced instance building with better error handling.
		"""
		if flowKey in self.builtNodes:
			return self.builtNodes[flowKey]

		try:
			#nodeConfig = self.structureFile[flowKey]
			#ExperimentInfo = self.flowsFile[nodeConfig["flow"]]
			#ExperimentIni = self.initFile.get(nodeConfig["flow"], {})
			nodeConfig = self.structureFile[flowKey]
			instanceType = nodeConfig["instanceType"]
			flowName = nodeConfig.get("flow")
						
			self.logger(f"Building node: {flowKey} (Type: {instanceType}, Flow: {flowName})")
			
			# Handle special node types that don't need experiments
			if instanceType in ['StartNode', 'EndNode']:
				ExperimentInfo = self._create_dummy_experiment_for_special_nodes(instanceType, nodeConfig)
				ExperimentIni = {}
			else:
				# Handle regular flow nodes that need experiments
				if not flowName:
					raise ValueError(f"Node {flowKey} of type {instanceType} requires a flow assignment")
				
				if flowName not in self.flowsFile:
					raise ValueError(f"Flow '{flowName}' not found in flows file for node {flowKey}")
				
				ExperimentInfo = self.flowsFile[flowName]
				ExperimentIni = self.initFile.get(flowName, {})
						
			# Merge experiment configuration
			ExperimentInfo = {**ExperimentInfo, **ExperimentIni}
			
			# Get flow class - handle special node types
			if instanceType in ['StartNode', 'EndNode']:
				flowClass = self._get_special_node_class(instanceType)
			else:
				if instanceType not in globals():
					raise ValueError(f"Unknown instance type: {instanceType}")
				flowClass = globals()[instanceType]
			
			# Build output node mappings
			outputNodeMap = self.__build_following_nodes(nodeConfig.get("outputNodeMap", {}))
			
			# Create node instance
			node = flowClass(
				ID=flowKey,
				Name=nodeConfig["name"],
				Framework=self.Framework,
				framework_utils=self.framework_utils,
				Experiment=ExperimentInfo,
				outputNodeMap=outputNodeMap,
				experiment_tracker=self.experiment_tracker,
				logger=self.logger
			)
			
			self.builtNodes[flowKey] = node
			self.logger(f"Built node: {flowKey} ({nodeConfig['name']})")
			
			return node
			
		except Exception as e:
			self.logger(f"Error building instance {flowKey}: {e}")
			raise

	def __build_following_nodes(self, nodeMap: dict):
		"""
		Recursively builds and returns mappings for the output nodes.
		"""
		outputNodeMap = {}
		if nodeMap:
			for port, nodeKey in nodeMap.items():
				outputNodeMap[int(port)] = self.__build_instance(nodeKey)
		return outputNodeMap

	def _create_dummy_experiment_for_special_nodes(self, instanceType, nodeConfig):
		"""
		Create dummy experiment data for special nodes that don't run actual experiments.
		"""
		return {
			'Test Name': f"{instanceType} - {nodeConfig['name']}",
			'Test Type': 'Special',
			'Test Mode': 'Control',
			'Experiment': 'Enabled',
			'Description': f"Special node of type {instanceType}",
			'Loops': 1,
			'Start': 0,
			'End': 1,
			'Steps': 1
		}

	def _get_special_node_class(self, instanceType):
		"""
		Get the appropriate class for special node types.
		"""
		node_mapping = {
			'StartNode': StartNodeFlowInstance,
			'EndNode': EndNodeFlowInstance,
			'SingleFailFlowInstance': SingleFailFlowInstance,
			'AllFailFlowInstance': AllFailFlowInstance,
			'MajorityFailFlowInstance': MajorityFailFlowInstance,
			'AdaptiveFlowInstance': AdaptiveFlowInstance,
			'CharacterizationFlowInstance': CharacterizationFlowInstance,
			'DataCollectionFlowInstance': DataCollectionFlowInstance,
			'AnalysisFlowInstance': AnalysisFlowInstance
		}

		if instanceType in node_mapping:
			return node_mapping[instanceType]
		else:
			raise ValueError(f"Unknown node type: {instanceType}")
	
		#if instanceType == 'StartNode':
		#	return StartNodeFlowInstance
		#elif instanceType == 'EndNode':
		#	return EndNodeFlowInstance
		#else:
		#	raise ValueError(f"Unknown special node type: {instanceType}")

	def __build_following_nodes(self, nodeMap: dict):
		"""
		Recursively builds and returns mappings for the output nodes.
		"""
		outputNodeMap = {}
		if nodeMap:
			for port, nodeKey in nodeMap.items():
				outputNodeMap[int(port)] = self.__build_instance(nodeKey)
		return outputNodeMap
