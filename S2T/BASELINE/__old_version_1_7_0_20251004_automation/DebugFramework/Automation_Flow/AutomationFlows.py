import os
import sys
from abc import ABC, abstractmethod
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Tuple
import threading

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

sys.path.append(parent_dir)


# Import FileHandler module for loading JSON files
import FileHandler as fh  # Assuming FileHandler contains functions for loading JSON
from ExecutionHandler.StatusManager import StatusEventType
from ExecutionHandler.Enums import TestStatus
import ExecutionHandler.utils.ThreadsHandler as th
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

class FlowInstance(ABC):
	"""
	Enhanced base class representing a flow instance with Framework step-by-step integration.
	"""

	def __init__(self, ID, Name, Framework, framework_utils, Experiment, outputNodeMap, logger=None):
		self.ID = ID
		self.Name = Name
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

	def run_experiment(self):
		"""Main experiment runner with shared Framework API."""
		self.logger(f"Running Experiment: {self.Name} (ID: {self.ID})")
		
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
			self.logger(f"Experiment interrupted by user")
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
						self.logger(f"Timeout waiting for iteration event - experiment may be stuck")
						try:
							cancel_result = self.framework_api.cancel_experiment()
							self.logger(f"Cancel command sent due to timeout: {cancel_result.get('success', False)}")
						except Exception as e:
							self.logger(f"Error sending cancel command: {e}")
						experiment_active = False
					
					elif event_result.get('cleanup_requested'):
						self.logger(f"Experiment cleanup was requested externally")
						experiment_active = False
					
					elif event_result.get('thread_died'):
						self.logger(f"Experiment thread died unexpectedly")
						experiment_active = False
					
					else:
						self.logger(f"Error waiting for iteration event: {event_result.get('error')}")
						# ✅ Don't exit on non-timeout errors when timeout is disabled
						if USE_TIMEOUT:
							experiment_active = False
						else:
							self.logger(f"Continuing to wait (timeout disabled)...")
							continue
					
					if not collected_results and not experiment_active:
						self.runStatusHistory = [TestStatus.FAILED.value]
					break
				
				# ✅ Rest of your event processing logic remains exactly the same
				event_data = event_result['event_data']
				event_type = event_data['event_type']
				
				self.logger(f"Received event: {event_type}")
				
				if event_type == StatusEventType.ITERATION_COMPLETE.value:
					iteration_count += 1
					
					# Extract iteration information
					iteration_num = event_data.get('iteration', iteration_count)
					status = event_data.get('status', 'Unknown')
					status_classification = event_data.get('status_classification', {})
					scratchpad = event_data.get('scratchpad', '')
					seed = event_data.get('seed', '')

					# ✅ Check if this is the last iteration
					is_last_iteration = (iteration_count >= (max_iterations))
									
					# Get statistics from the status handler system
					statistics =  self.framework_api.get_iteration_statistics()#event_data.get('statistics', {})

					# Check if we have statistics, if nor take it from API
					#if not statistics and self.framework_api:
					#		try:
					#			api_stats = self.framework_api.get_iteration_statistics()
					#			statistics = api_stats if api_stats else {}
					#		except Exception as e:
					#			self.logger(f"Error getting statistics from API: {e}")
					#			statistics = {}

					self.logger(f"Iteration {iteration_num} completed:")
					self.logger(f"  Status: {status}")
					self.logger(f"  Classification: {status_classification.get('category', 'unknown')}")
					self.logger(f"  Pass rate: {statistics.get('pass_rate', 0)}%")
					self.logger(f"  Total completed: {statistics.get('total_completed', 0)}")
					self.logger(f"  Recommendation: {statistics.get('recommendation', 'continue')}")

					# Store iteration result - check if we need this one here
					collected_results.append({
							'iteration': iteration_num,
							'status': status,
							'scratchpad': scratchpad,
							'seed': seed,
							'hardware_failure': False
						})

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
							cancel_result = self.framework_api.cancel_experiment()
							self.logger(f"Experiment cancelled due to hardware failure: {cancel_result.get('success', False)}")
						except Exception as e:
							self.logger(f"Error cancelling experiment: {e}")
						experiment_active = False
						break
					
					# Store valid iteration result
					collected_results.append({
						'iteration': iteration_num,
						'status': status,
						'scratchpad': scratchpad,
						'seed': seed,
						'hardware_failure': False
					})
					
					# Store current statistics from status handler
					self.execution_stats = statistics
					
					# Only make decisions for valid test results
					if status_classification.get('is_valid_test', False):

						if is_last_iteration:
							self.logger(f"Last iteration completed - sending END command")
							end_result = self.framework_api.end_current_experiment()
							if end_result['success']:
								self.logger(f"End command sent successfully - waiting for experiment completion")
							else:
								self.logger(f"Failed to send end command: {end_result['message']}")
							# Don't set experiment_active = False here, wait for completion event
						else:
							# Use statistics from status handler for decision making
							decision = self._make_iteration_decision(statistics, iteration_count, max_iterations)
							self.logger(f"Decision for iteration {iteration_num}: {decision}")
						
							if decision == 'continue':
								self.logger(f"Sending continue command for next iteration...")
								continue_result = self.framework_api.continue_next_iteration()
								if not continue_result['success']:
									self.logger(f"Failed to send continue command: {continue_result['message']}")
									time.sleep(5)
									experiment_active = False
								else:
									self.logger(f"Continue command sent successfully - waiting for next iteration")
								
							elif decision == 'end':
								self.logger(f"Early termination - sending END command")
								end_result = self.framework_api.end_current_experiment()
								if end_result['success']:
									self.logger(f"End command sent successfully - waiting for experiment completion")
								else:
									self.logger(f"Failed to send end command: {end_result['message']}")
							
							else:  # cancel
								self.logger(f"Sending cancel command...")
								cancel_result = self.framework_api.cancel_experiment()
								self.logger(f"Cancel command sent: {cancel_result['success']}")
								time.sleep(5)
								experiment_active = False
					else:
						self.logger(f"Non-test status received ({status}), continuing to monitor")
				
				elif event_type == StatusEventType.EXPERIMENT_COMPLETE.value:
					self.logger(f"Experiment completed successfully")
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
				
				else:
					self.logger(f"Unknown event type: {event_type} - continuing to monitor")
		
		except KeyboardInterrupt:
			self.logger(f"Monitoring interrupted by user")
			try:
				cancel_result = self.framework_api.cancel_experiment()
				self.logger(f"Experiment cancelled due to interruption: {cancel_result.get('success', False)}")
			except:
				pass
			experiment_active = False
		except Exception as e:
			self.logger(f"Error in experiment lifecycle monitoring: {e}")
			try:
				cancel_result = self.framework_api.cancel_experiment()
				self.logger(f"Experiment cancelled due to error: {cancel_result.get('success', False)}")
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
				self.logger(f"No valid test results found - marking as system failure")
				self.runStatusHistory = [TestStatus.FAILED.value]  # This will trigger flow abortion
			
			self.logger(f"Processed {len(collected_results)} iteration results into {len(self.runStatusHistory)} valid test results")
			
		except Exception as e:
			self.logger(f"Error processing final results: {e}")
			self.runStatusHistory = [TestStatus.FAILED.value]

	def _get_max_iterations(self):
		"""Get maximum iterations based on experiment type."""
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
					self.logger(f"Following hardware failure path instead of auto-termination")
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
		self.logger(f"Flow will terminate with appropriate error flag")
		
		# Set termination reason based on port type
		if self.outputPort == 3:
			self._set_termination_flag("hardware_failure", f"Hardware failure detected but port 3 not wired")
		elif self.outputPort == 2:
			self._set_termination_flag("intermittent_results", f"Intermittent results detected but port 2 not wired")
		elif self.outputPort == 1:
			self._set_termination_flag("repro_found", f"Solid repro found but port 1 not wired")
		elif self.outputPort == 0:
			self._set_termination_flag("no_repro", f"No repro found but port 0 not wired")
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
		
		return hardware_failure_rate > 0.40  # 40% threshold

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
			self.logger(f"HARDWARE FAILURE THRESHOLD EXCEEDED - ending experiment")
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
  
	def _set_base_output_ports(self):
		"""
		 ENHANCED: Base port setting with guaranteed hardware failure detection.
		Returns True if hardware failure port (3) was set, False otherwise.
		"""
		# Check if hardware failures exceed threshold in execution stats
		if hasattr(self, 'execution_stats') and self.execution_stats:
			if self._check_hardware_failure_threshold(self.execution_stats):
				self.outputPort = 3  # Hardware failure port
				self.logger(f"HARDWARE FAILURE THRESHOLD EXCEEDED - Setting port 3")
				self.logger(f"This will trigger immediate flow termination")
				return True
		
		# Check for hardware failure statuses in results
		hardware_statuses = [TestStatus.EXECUTION_FAIL.value, TestStatus.FAILED.value, 
						   TestStatus.PYTHON_FAIL.value, TestStatus.CANCELLED.value]
		
		hardware_failures = sum(1 for status in self.runStatusHistory if status in hardware_statuses)
		total_results = len(self.runStatusHistory)
		
		if total_results > 0 and (hardware_failures / total_results) > 0.40:
			self.outputPort = 3  # Hardware failure port
			self.logger(f"HARDWARE FAILURE IN RESULTS - Setting port 3")
			self.logger(f"Hardware failures: {hardware_failures}/{total_results} = {hardware_failures/total_results:.1%}")
			self.logger(f"This will trigger immediate flow termination")
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
			if recent_trend == "repro":
				self.logger(f"Consistent failures detected - ending")
				return 'end'
			elif fail_rate > 0 and total_completed >= 5:
				self.logger(f"Some failures detected - ending for analysis")
				return 'end'
			elif total_completed >= 8 and fail_rate == 0:
				self.logger(f"No failures after sufficient testing - ending")
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

		# ✅ Validate port is wired (this will be checked in get_next_node())
		self.logger('='*50)
		self.logger(f' RunStatus: {self.runStatusHistory}')
		self.logger(f' SingleFail Node Complete - Port: {self.outputPort}')
		
		# ✅ Check if port is wired and log accordingly
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
				self.logger(f"Solid failure reproduction detected - ending")
				return 'end'
			elif recent_trend == "no-repro":
				self.logger(f"No failure reproduction (all passes) - ending")
				return 'end'
			elif total_completed >= 10 and recent_trend in ["flaky", "unstable", "mixed"]:
				self.logger(f"Intermittent pattern established - ending")
				return 'end'
		
		# Need more data for clear pattern
		if total_completed >= 15:
			self.logger(f"Sufficient iterations for pattern analysis - ending")
			return 'end'
		
		self.logger(f"Continuing - need clearer reproduction pattern")
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
				self.logger(f"Port 1 - Solid failure reproduction detected")
			elif pattern == "no_repro":
				self.outputPort = 0  # No failures found (no repro)
				self.logger(f"Port 0 - No failure reproduction (all passes)")
			else:  # intermittent or insufficient_data
				self.outputPort = 2  # Mixed/intermittent results
				self.logger(f"Port 2 - Intermittent or mixed results")
		else:
			# Fallback analysis using runStatusHistory
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
				self.logger(f"Sufficient data for failure rate analysis - ending")
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

		# ✅ Validate port is wired (this will be checked in get_next_node())
		self.logger('='*50)
		self.logger(f' RunStatus: {self.runStatusHistory}')
		self.logger(f' MajorityFail Node Complete - Port: {self.outputPort}')
		
		# ✅ Check if port is wired and log accordingly
		if hasattr(self, 'outputNodeMap') and self.outputNodeMap:
			if self.outputPort in self.outputNodeMap:
				next_node = self.outputNodeMap[self.outputPort]
				self.logger(f' Port {self.outputPort} is wired to: {next_node.Name}')
			else:
				self.logger(f' WARNING: Port {self.outputPort} is NOT wired - flow will terminate')
		
		self.logger('='*50)

class AdaptiveFlowInstance(FlowInstance):
	"""
	Advanced debugging flow with intelligent pattern recognition.
	Port 0: Stable content (no significant failures)
	Port 1: Reproducible failures (good for debugging)
	Port 2: Complex patterns (needs further analysis)
	Port 3: Hardware failures (>40% threshold)
	"""
	
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""
		Intelligent decision making for debugging workflows.
		"""
		# Check base conditions first
		base_decision = self._make_base_iteration_decision(stats, iteration_count, max_iterations)
		if base_decision:
			return base_decision

		total_completed = stats.get('total_completed', 0)
		recommendation = stats.get('recommendation', 'continue')
		recent_trend = stats.get('recent_trend', 'insufficient_data')
		pass_rate = stats.get('pass_rate', 0.0)
		
		self.logger(f"Adaptive decision - Total: {total_completed}, Recommendation: {recommendation}, Trend: {recent_trend}")
		
		# Use status handler intelligence for debugging
		if recommendation == 'sufficient_data_good' and recent_trend == "no-repro":
			self.logger(f"Confirmed stable content - ending")
			return 'end'
		elif recommendation == 'sufficient_data_poor' and recent_trend == "repro":
			self.logger(f"Confirmed reproducible failures - ending")
			return 'end'
		elif total_completed >= 12 and recent_trend in ["flaky", "unstable"]:
			self.logger(f"Complex failure pattern identified - ending")
			return 'end'
		
		return 'continue'

	def set_output_port(self):
		"""
		Intelligent routing for debugging based on comprehensive analysis.
		"""
		# Check hardware failure port first
		if self._set_base_output_ports():
			return
		
		if hasattr(self, 'execution_stats') and self.execution_stats:
			pattern = self._get_failure_reproduction_pattern(self.execution_stats)
			pass_rate = self.execution_stats.get('pass_rate', 0.0)
			fail_rate = self.execution_stats.get('fail_rate', 0.0)
			recent_trend = self.execution_stats.get('recent_trend', 'insufficient_data')
			
			self.logger(f"Adaptive routing - Pattern: {pattern}, Trend: {recent_trend}, "
					   f"Pass: {pass_rate}%, Fail: {fail_rate}%")
			
			if pattern == "solid_repro" and fail_rate >= 60:
				self.outputPort = 1  # Excellent for debugging - reproducible failures
			elif pattern == "no_repro" and pass_rate >= 80:
				self.outputPort = 0  # Stable content - no debugging needed
			else:
				self.outputPort = 2  # Complex patterns - needs further analysis
		else:
			# Fallback to simple analysis
			fail_rate = (self.runStatusHistory.count('FAIL') / len(self.runStatusHistory) * 100) if self.runStatusHistory else 0
			self.outputPort = 1 if fail_rate >= 60 else (0 if fail_rate <= 20 else 2)

			valid_results = [s for s in self.runStatusHistory if s in ['PASS', 'FAIL']]
			
			if not valid_results:
				self.outputPort = 3  # No valid results - hardware issue	

		# ✅ Validate port is wired (this will be checked in get_next_node())
		self.logger('='*50)
		self.logger(f' RunStatus: {self.runStatusHistory}')
		self.logger(f' AdaptiveFlow Node Complete - Port: {self.outputPort}')
		
		# ✅ Check if port is wired and log accordingly
		if hasattr(self, 'outputNodeMap') and self.outputNodeMap:
			if self.outputPort in self.outputNodeMap:
				next_node = self.outputNodeMap[self.outputPort]
				self.logger(f' Port {self.outputPort} is wired to: {next_node.Name}')
			else:
				self.logger(f' WARNING: Port {self.outputPort} is NOT wired - flow will terminate')
		
		self.logger('='*50)

class FlowTestExecutor:
	"""
	Enhanced executor with Framework API integration and comprehensive logging.
	"""

	def __init__(self, root, framework=None, execution_state = None):

		self.root = root
		self.framework = framework
		self.execution_state = execution_state
		self.framework_api = None
		self.execution_log = []
		self.start_time = None
		self.execution_state = None
		self.status_callback = None
		
		# Cleanup tracking
		self._nodes_with_active_experiments = []
		self._cleanup_lock = threading.Lock()
	   
		# Hardware failure tracking
		self._hardware_failure_detected = False
		self._flow_abort_requested = False
		self._abort_reason = None

		# Hardware Fail termination flag
		self._hardware_failure_termination = False
		self._unwired_port_termination = False
		self._termination_type = None
		self._termination_node = None
	
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
		self.start_time = datetime.now()
		self.log_execution("Flow execution started")
		
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
			
			# ✅ Check if node set output port to 3 (hardware failure port)
			if hasattr(node, 'outputPort') and node.outputPort == 3:
				self.log_execution(f"Node routed to hardware failure port (3)")
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
			self.log_execution(f"FINAL STATUS: HARDWARE FAILURE TERMINATION")
			self.log_execution(f"Reason: {self._abort_reason}")
		elif self._unwired_port_termination:
			self.log_execution(f"FINAL STATUS: UNWIRED PORT TERMINATION")
			self.log_execution(f"Termination Type: {self._termination_type}")
			self.log_execution(f"Terminating Node: {self._termination_node.Name if self._termination_node else 'Unknown'}")
			self.log_execution(f"Reason: {self._abort_reason}")
		elif self._flow_abort_requested:
			self.log_execution(f"FINAL STATUS: FLOW ABORTED")
			self.log_execution(f"Reason: {self._abort_reason}")
		else:
			self.log_execution(f"FINAL STATUS: NORMAL COMPLETION")

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

	def build_flow(self, rootID, execution_state=None):
		"""
		Build and return an enhanced executor for the flow starting at rootID.
		✅ SINGLE PLACE where FlowTestExecutor is created.
		"""
		try:
			root = self.__build_instance(rootID)
			
			# ONLY PLACE: Create FlowTestExecutor
			executor = FlowTestExecutor(
				root=root, 
				framework=self.Framework,
				execution_state=execution_state  # Pass ThreadsHandler to executor
			)
			
			# ✅ Pass built nodes reference to executor for end node searching
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
		if instanceType == 'StartNode':
			return StartNodeFlowInstance
		elif instanceType == 'EndNode':
			return EndNodeFlowInstance
		else:
			raise ValueError(f"Unknown special node type: {instanceType}")

	def __build_following_nodes(self, nodeMap: dict):
		"""
		Recursively builds and returns mappings for the output nodes.
		"""
		outputNodeMap = {}
		if nodeMap:
			for port, nodeKey in nodeMap.items():
				outputNodeMap[int(port)] = self.__build_instance(nodeKey)
		return outputNodeMap

# Test Variables
def test_runStatusHistory(ID):
	if '1' in ID:
		FAIL = True
	elif '2' in ID:
		FAIL = False    
	elif '3' in ID:
		FAIL = True
	else:
		FAIL = False    
	return ['FAIL' if FAIL else 'PASS']
