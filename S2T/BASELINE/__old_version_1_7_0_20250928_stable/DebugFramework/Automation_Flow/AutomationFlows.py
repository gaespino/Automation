import os
import sys
from abc import ABC, abstractmethod
import time
from datetime import datetime


current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

sys.path.append(parent_dir)


# Import FileHandler module for loading JSON files
import FileHandler as fh  # Assuming FileHandler contains functions for loading JSON

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
		self.framework_api = None  # Will be set by FlowTestExecutor

		# Framework API will be set dynamically during execution
		self.framework_api = None  # Initially None
		self.framework_utils = framework_utils
		if not logger: 
			logger = print
		self.logger = logger

		# Initialize system-to-tester configuration
		self.S2T_CONFIG = framework_utils.system_2_tester_default() if framework_utils else S2T_CONFIGURATION

	def run_experiment(self):
		"""Executes the experiment using Framework's step-by-step mode with real-time decision making."""
		self.logger(f"Running Experiment: {self.Name} (ID: {self.ID})")
		print(f"Framework: {self.Framework } (API: {self.framework_api})")
		if self.framework_api is not None:
			print(f"Node {self.ID}: Using Framework API: {self.framework_api}")
			try:
				self._run_framework_experiment()
			except Exception as e:
				self.logger(f"Framework experiment failed: {e}")
				self.runStatusHistory = ['FAILED']
		elif self.Framework is not None:
			# Fallback: Framework available but no API (shouldn't happen in normal flow)
			self.logger(f"WARNING: Node {self.ID} has Framework but no framework_api")
			self.runStatusHistory = ['FAILED']
		else:
			# Fallback to test mode
			self.runStatusHistory = test_runStatusHistory(self.ID)
			self.logger(f"Test mode result: {self.runStatusHistory}")
			
		self.set_output_port()

	def _run_framework_experiment(self):
		"""
		Run experiment using Framework's step-by-step mode with intelligent decision making.
		"""
		try:
			# Start experiment in step-by-step mode
			experiment_name = f"{self.Name}_{self.ID}"
			result = self.framework_api.start_experiment_step_by_step(
				self.Experiment, 
				experiment_name=experiment_name,
				S2T_BOOT_CONFIG=self.S2T_CONFIG
			)
			
			if not result['success']:
				self.logger(f"Failed to start experiment: {result.get('error', 'Unknown error')}")
				self.runStatusHistory = ['FAILED']
				return

			self.logger(f"Experiment started successfully in step-by-step mode")
			
			# Monitor and control experiment execution
			self._monitor_step_by_step_execution()
			
		except Exception as e:
			self.logger(f"Error running Framework experiment: {e}")
			self.runStatusHistory = ['FAILED']

	def _monitor_step_by_step_execution(self):
		"""
		Monitor step-by-step execution and make decisions based on results.
		"""
		iteration_count = 0
		max_iterations = self._get_max_iterations()
		
		while True:
			state = self.framework_api.get_current_state()
			
			if not state['is_running']:
				self.logger(f"Experiment completed. Final state: {state}")
				break
			
			if state['waiting_for_command']:
				iteration_count += 1
				stats = self.framework_api.get_iteration_statistics()
				
				self.logger(f"Iteration {state['current_iteration']} completed:")
				self.logger(f"  Pass rate: {stats['pass_rate']}%")
				self.logger(f"  Total completed: {stats['total_completed']}")
				self.logger(f"  Recommendation: {stats['recommendation']}")
				
				# Store current statistics
				self.execution_stats = stats
				
				# Make decision based on node-specific logic
				decision = self._make_iteration_decision(stats, iteration_count, max_iterations)
				
				if decision == 'continue':
					self.logger(f"Decision: Continue to next iteration")
					continue_result = self.framework_api.continue_next_iteration()
					if not continue_result['success']:
						self.logger(f"Failed to continue: {continue_result['message']}")
						break
				elif decision == 'end':
					self.logger(f"Decision: End experiment early")
					end_result = self.framework_api.end_current_experiment()
					if end_result['success']:
						self.logger(f"Experiment ended successfully")
					break
				else:
					self.logger(f"Decision: Cancel experiment")
					self.framework_api.cancel_experiment()
					break
			
			time.sleep(2)  # Check every 2 seconds
		
		# Extract final results
		self._extract_final_results()

	def _get_max_iterations(self):
		"""
		Get maximum iterations based on experiment type.
		Override in subclasses for specific limits.
		"""
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

	def _extract_final_results(self):
		"""Extract final results from the completed experiment."""
		try:
			final_state = self.framework_api.get_current_state()
			final_stats = self.framework_api.get_iteration_statistics()
			
			# Update execution state with iteration progress
			if hasattr(self, '_flow_execution_state'):
				total_completed = final_stats.get('total_completed', 0)
				self._flow_execution_state.set_current_node_iterations(total_completed, total_completed)
			
			# Build status history based on final statistics
			total_completed = final_stats.get('total_completed', 0)
			pass_count = int(total_completed * final_stats.get('pass_rate', 0) / 100)
			fail_count = total_completed - pass_count
			
			# Create status history with PASS/FAIL only (no system statuses)
			self.runStatusHistory = (['PASS'] * pass_count) + (['FAIL'] * fail_count)
			
			# Store detailed stats
			self.execution_stats = final_stats
			
			self.logger(f"Final Results - Total: {total_completed}, Pass: {pass_count}, Fail: {fail_count}")
			
		except Exception as e:
			self.logger(f"Error extracting final results: {e}")
			# System error - use FAILED status to trigger flow cancellation
			self.runStatusHistory = ['FAILED']

	@abstractmethod
	def set_output_port(self):
		"""
		Abstract method for setting the output port based on the run status.
		Subclasses must implement this method to determine specific output behavior.
		"""
		pass

	def get_next_node(self):
		"""
		Returns the next node to execute based on the output port determined in `set_output_port`.
		"""
		if self.outputNodeMap: 
			try:
				nextNode = self.outputNodeMap[self.outputPort]
				self.logger(f"Next node: {nextNode.Name} (Port: {self.outputPort})")
				return nextNode
			except KeyError as e:
				self.logger(f"Output Port Error: No handler found for port {self.outputPort}. Exception: {e}")
		return None

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
	Flow instance that stops on first failure and routes based on any failure occurrence.
	"""
	
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""
		Stop immediately if any failure is detected.
		"""
		if stats['total_completed'] >= 1:
			if stats['fail_rate'] > 0:
				return 'end'  # Stop on first failure
			elif stats['total_completed'] >= 5 and stats['pass_rate'] == 100:
				return 'end'  # Stop early if we have good confidence
		
		if iteration_count >= max_iterations:
			return 'end'
		
		return 'continue'

	def set_output_port(self):
		"""
		Returns 0 if any failure found, otherwise 1.
		"""
		self.outputPort = 0 if 'FAIL' in self.runStatusHistory else 1

class AllFailFlowInstance(FlowInstance):
	"""
	Flow instance that requires all tests to fail for failure path.
	"""
	
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""
		Continue until we have enough data to determine if all tests fail.
		"""
		if stats['total_completed'] >= 3:
			if stats['pass_rate'] > 0:
				return 'end'  # We have passes, so not all fail
			elif stats['total_completed'] >= 10:
				return 'end'  # Enough failures to be confident
		
		if iteration_count >= max_iterations:
			return 'end'
		
		return 'continue'

	def set_output_port(self):
		"""
		Returns 0 if all tests failed, otherwise 1.
		"""
		has_failures = 'FAIL' in self.runStatusHistory
		all_failed = len(set(self.runStatusHistory)) <= 1 and has_failures
		self.outputPort = 0 if all_failed else 1

class MajorityFailFlowInstance(FlowInstance):
	"""
	Flow instance that routes based on majority failure rate.
	"""
	
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""
		Continue until we have statistical confidence in the failure rate.
		"""
		if stats['total_completed'] >= 10:
			# We have enough data for statistical confidence
			if abs(stats['fail_rate'] - 50) > 20:  # Clear majority either way
				return 'end'
		elif stats['total_completed'] >= 20:
			return 'end'  # Maximum for statistical analysis
		
		if iteration_count >= max_iterations:
			return 'end'
		
		return 'continue'

	def set_output_port(self):
		"""
		Returns 0 if majority of tests failed (>=50%), otherwise 1.
		"""
		fail_rate = self.runStatusHistory.count('FAIL') / len(self.runStatusHistory) if self.runStatusHistory else 0
		self.outputPort = 0 if fail_rate >= 0.5 else 1

class AdaptiveFlowInstance(FlowInstance):
	"""
	Advanced flow instance that adapts based on trends and confidence levels.
	"""
	
	def _make_iteration_decision(self, stats, iteration_count, max_iterations):
		"""
		Make intelligent decisions based on trends and confidence.
		"""
		total = stats['total_completed']
		
		# Early stopping conditions
		if total >= 5:
			if stats['pass_rate'] >= 95:
				return 'end'  # Very high pass rate, confident in success
			elif stats['pass_rate'] <= 5:
				return 'end'  # Very high fail rate, confident in failure
		
		# Medium confidence stopping
		if total >= 15:
			if stats['pass_rate'] >= 80 or stats['pass_rate'] <= 20:
				return 'end'  # Clear trend established
		
		# Maximum iterations reached
		if iteration_count >= max_iterations:
			return 'end'
		
		# Check for sufficient data based on recommendation
		if stats['recommendation'] in ['sufficient_data_good', 'sufficient_data_poor']:
			return 'end'
		
		return 'continue'

	def set_output_port(self):
		"""
		Intelligent routing based on execution statistics and trends.
		"""
		if not self.execution_stats:
			# Fallback to simple majority
			fail_rate = self.runStatusHistory.count('FAIL') / len(self.runStatusHistory) if self.runStatusHistory else 0
			self.outputPort = 0 if fail_rate >= 0.5 else 1
			return
		
		pass_rate = self.execution_stats.get('pass_rate', 0)
		total_tests = self.execution_stats.get('total_completed', 0)
		
		# Route based on confidence and results
		if total_tests >= 10:
			if pass_rate >= 70:
				self.outputPort = 1  # Success path
			else:
				self.outputPort = 0  # Failure path
		else:
			# Not enough data, use simple majority
			self.outputPort = 0 if pass_rate < 50 else 1

class FlowTestExecutor:
	"""
	Enhanced executor with Framework API integration and comprehensive logging.
	"""

	def __init__(self, root, framework=None):
		self.root = root
		self.framework = framework
		self.framework_api = None
		self.execution_log = []
		self.start_time = None
		self.framework_api = None
		# Initialize Framework API if available
		#if framework_api:
			#self.framework_api = framework_api(framework)
			
			# Set API reference for all nodes
		#	self._set_api_for_all_nodes(root)

	def set_framework_api(self, framework_api):
		"""Set framework API dynamically during execution"""
		self.framework_api = framework_api
		print(f"FlowTestExecutor: Set framework_api: {framework_api}")
	
	
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

	def set_execution_state(self, execution_state):
		"""Set execution state for command checking."""
		self.execution_state = execution_state
		
	def set_status_callback(self, callback):
		"""Set callback for status updates."""
		self.status_callback = callback

	def execute(self):
		"""
		Execute the flow with comprehensive logging and error handling.
		"""
		self.start_time = datetime.now()
		self.log_execution("Flow execution started")
		
		try:
			current_node = self.root
			node_count = 0
			
			while current_node is not None and node_count < 50:  # Safety limit
				# Check for cancellation/end commands
				if self.execution_state:
					if self.execution_state.is_cancelled():
						self.log_execution("Flow execution cancelled by user")
						break
					if self.execution_state.is_ended():
						self.log_execution("Flow execution ended by user")
						break
					
				node_count += 1

				if self.framework_api:
					current_node.framework_api = self.framework_api
					print(f"Set framework_api on node {current_node.ID}")
									
				self.log_execution(f"Executing node: {current_node.Name} (ID: {current_node.ID})")

				# Notify status callback if available
				if self.status_callback:
					self.status_callback('node_start', current_node)				

				# Check for cancellation before execution
				if self.execution_state and (self.execution_state.is_cancelled() or self.execution_state.is_ended()):
					break
				
				# Execute the current node
				start_time = time.time()
				current_node.run_experiment()
				execution_time = time.time() - start_time

				# Check for cancellation after execution
				if self.execution_state and (self.execution_state.is_cancelled() or self.execution_state.is_ended()):
					break
								
				# Log execution results
				summary = current_node.get_execution_summary()
				self.log_execution(f"Node completed in {execution_time:.1f}s: {summary}")

				# Notify status callback if available
				if self.status_callback:
					self.status_callback('node_complete', current_node)
								
				# Get next node
				next_node = current_node.get_next_node()
				
				if next_node:
					self.log_execution(f"Moving to next node: {next_node.Name}")
				else:
					self.log_execution("Flow execution completed - no more nodes")
				
				current_node = next_node
			
			if node_count >= 50:
				self.log_execution("WARNING: Flow execution stopped due to safety limit (50 nodes)")
				
		except Exception as e:
			self.log_execution(f"ERROR: Flow execution failed: {e}")
			raise
		finally:
			total_time = (datetime.now() - self.start_time).total_seconds()
			self.log_execution(f"Flow execution finished. Total time: {total_time:.1f}s")

	def log_execution_old(self, message):
		"""
		Log execution messages with timestamps.
		"""
		timestamp = datetime.now().strftime("%H:%M:%S")
		log_entry = f"[{timestamp}] {message}"
		self.execution_log.append(log_entry)
		print(log_entry)

	# **ADD** new method for thread-safe logging:
	def log_execution(self, message):
		"""Thread-safe logging that doesn't interfere with UI."""
		timestamp = datetime.now().strftime("%H:%M:%S")
		log_entry = f"[{timestamp}] {message}"
		self.execution_log.append(log_entry)
		# Don't print directly in thread - use callback instead
		if self.status_callback:
			self.status_callback('log_message', log_entry)
			
	def get_execution_report(self):
		"""
		Generate a comprehensive execution report.
		"""
		return {
			'start_time': self.start_time,
			'execution_log': self.execution_log,
			'total_time': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
		}

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

	def build_flow(self, rootID):
		"""
		Build and return an enhanced executor for the flow starting at rootID.
		"""
		try:
			root = self.__build_instance(rootID)
			executor = FlowTestExecutor(root=root, framework=self.Framework)
			
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
