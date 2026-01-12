import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import configparser
import json

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

sys.path.append(parent_dir)



class ExperimentDebugger:
	"""
	Experiment Tracker Debug Module
	Provides comprehensive debugging capabilities for ExperimentTracker functionality.
	Can be easily enabled/disabled and removed later.
	"""
	def __init__(self, enabled: bool = True, debug_folder: str = None, verbose: bool = True):
		self.enabled = enabled
		self.verbose = verbose
		self.debug_folder = debug_folder or "C:\\Temp"
		self.debug_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
		
		if self.enabled:
			self._ensure_debug_folder()
			self._init_debug_session()
	
	def _ensure_debug_folder(self):
		"""Create debug folder if it doesn't exist"""
		if not os.path.exists(self.debug_folder):
			os.makedirs(self.debug_folder)
	
	def _init_debug_session(self):
		"""Initialize debug session"""
		session_file = os.path.join(self.debug_folder, f"debug_session_{self.debug_session_id}.log")
		with open(session_file, 'w') as f:
			f.write(f"=== EXPERIMENT TRACKER DEBUG SESSION STARTED ===\n")
			f.write(f"Session ID: {self.debug_session_id}\n")
			f.write(f"Start Time: {datetime.now().isoformat()}\n")
			f.write("=" * 60 + "\n\n")
		
		if self.verbose:
			print(f"[TRACKER] ExperimentTracker Debug Session Started: {self.debug_session_id}")
			print(f"[TRACKER] Debug logs will be saved to: {self.debug_folder}")
	
	def log(self, message: str, category: str = "INFO", data: Any = None):
		"""Log debug message with optional data"""
		if not self.enabled:
			return
		
		timestamp = datetime.now().isoformat()
		log_entry = f"[{timestamp}] [{category}] {message}"
		
		# Console output
		if self.verbose:
			emoji_map = {
				"INFO": "[INFO]",
				"WARNING": "[WARN]",
				"ERROR": "[ERROR]",
				"SUCCESS": "[DONE]",
				"TRACKER": "[DEBUG]",
				"EXPERIMENT": "[DEBUG]",
				"ANALYSIS": "[ANALYSIS]",
				"CONFIG": "[CONFIG]"
			}
			emoji = emoji_map.get(category, "[TRACKER]")
			print(f"{emoji} {message}")
		
		# File output
		session_file = os.path.join(self.debug_folder, f"debug_session_{self.debug_session_id}.log")
		with open(session_file, 'a') as f:
			f.write(log_entry + "\n")
			if data is not None:
				f.write(f"    Data: {json.dumps(data, indent=2, default=str)}\n")
			f.write("\n")
	
	def log_experiment_start(self, node_id: str, node_name: str, experiment_config: Dict):
		"""Debug experiment start"""
		self.log(f"EXPERIMENT START - Node: {node_name} (ID: {node_id})", "EXPERIMENT")
		
		# Save detailed experiment config
		config_file = os.path.join(self.debug_folder, f"experiment_config_{node_id}_{self.debug_session_id}.json")
		with open(config_file, 'w') as f:
			json.dump({
				'node_id': node_id,
				'node_name': node_name,
				'experiment_config': experiment_config,
				'timestamp': datetime.now().isoformat()
			}, f, indent=2, default=str)
		
		self.log(f"Experiment config saved to: {config_file}", "CONFIG")
		
		# Log key configuration parameters
		key_params = ['Test Type', 'Content', 'Voltage IA', 'Voltage CFC', 'Frequency IA', 'Frequency CFC']
		config_summary = {k: experiment_config.get(k) for k in key_params if experiment_config.get(k) is not None}
		self.log(f"Key Config Parameters: {config_summary}", "CONFIG", config_summary)
	
	def log_iteration(self, iteration_num: int, status: str, config_snapshot: Dict, sweep_value: Any = None):
		"""Debug iteration tracking"""
		self.log(f"ITERATION {iteration_num} - Status: {status}", "TRACKER")
		
		if sweep_value is not None:
			self.log(f"  Sweep Value: {sweep_value}", "TRACKER")
		
		# Log key config changes
		key_config = {
			'voltage_ia': config_snapshot.get('volt_IA'),
			'voltage_cfc': config_snapshot.get('volt_CFC'),
			'frequency_ia': config_snapshot.get('freq_ia'),
			'frequency_cfc': config_snapshot.get('freq_cfc')
		}
		
		config_changes = {k: v for k, v in key_config.items() if v is not None}
		if config_changes:
			self.log(f"  Config: {config_changes}", "TRACKER")
	
	def log_experiment_complete(self, final_result: str, output_port: int, test_folder: str = None):
		"""Debug experiment completion"""
		self.log(f"EXPERIMENT COMPLETE - Result: {final_result}, Port: {output_port}", "SUCCESS")
		
		if test_folder:
			self.log(f"Test Folder: {test_folder}", "INFO")
	
	def log_sweep_analysis(self, sweep_analysis: Dict):
		"""Debug sweep analysis"""
		self.log("SWEEP ANALYSIS COMPLETE", "ANALYSIS")
		
		if sweep_analysis:
			summary = {
				'sweep_type': sweep_analysis.get('sweep_type'),
				'sweep_domain': sweep_analysis.get('sweep_domain'),
				'total_points': sweep_analysis.get('total_points'),
				'failure_points': sweep_analysis.get('failure_points'),
				'pattern': sweep_analysis.get('sensitivity_analysis', {}).get('pattern')
			}
			self.log(f"Sweep Summary: {summary}", "ANALYSIS", sweep_analysis)
	
	def log_adaptive_analysis(self, analysis_data: Dict):
		"""Debug adaptive analysis"""
		self.log("ADAPTIVE ANALYSIS", "ANALYSIS")
		
		if analysis_data.get('status') == 'data_available':
			source = analysis_data.get('source_experiment', {})
			self.log(f"Source: {source.get('node_name')} (Port: {source.get('output_port')})", "ANALYSIS")
			self.log(f"Recovery Potential: {analysis_data.get('recovery_potential')}", "ANALYSIS")
			
			# Log recommended config
			recommended = analysis_data.get('recommended_config', {})
			if recommended:
				self.log(f"Recommended Config: {recommended}", "ANALYSIS", recommended)
		else:
			self.log(f"No adaptive data available: {analysis_data.get('message')}", "WARNING")
		
	def log_comprehensive_analysis(self, comprehensive_data: Dict):
		"""Debug comprehensive analysis with proper null checking"""
		self.log("COMPREHENSIVE ANALYSIS COMPLETE", "ANALYSIS")
		
		try:
			# Safe extraction with null checking
			detailed_experiments = comprehensive_data.get('detailed_experiments', [])
			
			# Filter out None experiments and safely check sweep_data
			valid_experiments = [e for e in detailed_experiments if e is not None]
			
			voltage_experiments = len([
				e for e in valid_experiments 
				if e.get('sweep_data') is not None and 
				e.get('sweep_data', {}).get('sweep_type') == 'voltage'
			])
			
			frequency_experiments = len([
				e for e in valid_experiments 
				if e.get('sweep_data') is not None and 
				e.get('sweep_data', {}).get('sweep_type') == 'frequency'
			])
			
			flow_summary = comprehensive_data.get('flow_summary', {})
			recovery_conditions = flow_summary.get('recovery_conditions', []) if flow_summary else []
			failure_conditions = flow_summary.get('failure_conditions', []) if flow_summary else []
			
			summary = {
				'total_experiments': comprehensive_data.get('total_experiments', 0),
				'valid_experiments': len(valid_experiments),
				'voltage_experiments': voltage_experiments,
				'frequency_experiments': frequency_experiments,
				'recovery_conditions': len(recovery_conditions),
				'failure_conditions': len(failure_conditions)
			}
			
			self.log(f"Analysis Summary: {summary}", "ANALYSIS", summary)
			
			# Save comprehensive analysis to file with error handling
			try:
				analysis_file = os.path.join(self.debug_folder, f"comprehensive_analysis_{self.debug_session_id}.json")
				
				# Create a safe version of comprehensive_data for JSON serialization
				safe_comprehensive_data = self._make_json_safe(comprehensive_data)
				
				with open(analysis_file, 'w') as f:
					json.dump(safe_comprehensive_data, f, indent=2, default=str)
				
				self.log(f"Comprehensive analysis saved to: {analysis_file}", "INFO")
				
			except Exception as file_error:
				self.log(f"Error saving comprehensive analysis file: {file_error}", "ERROR")
			
		except Exception as e:
			self.log(f"Error in log_comprehensive_analysis: {e}", "ERROR")
			# Still try to log basic info
			self.log(f"Comprehensive data keys: {list(comprehensive_data.keys()) if comprehensive_data else 'None'}", "ERROR")

	def _make_json_safe(self, data):
		"""Make data safe for JSON serialization by handling None values and complex objects"""
		if data is None:
			return None
		elif isinstance(data, dict):
			return {k: self._make_json_safe(v) for k, v in data.items()}
		elif isinstance(data, list):
			return [self._make_json_safe(item) for item in data if item is not None]
		elif isinstance(data, datetime):
			return data.isoformat()
		elif hasattr(data, '__dict__'):
			# Handle custom objects
			return str(data)
		else:
			return data
	
	def log_tracker_state(self, tracker_instance):
		"""Debug current tracker state"""
		if not self.enabled:
			return
		
		self.log("TRACKER STATE SNAPSHOT", "TRACKER")
		
		state = {
			'experiments_count': len(tracker_instance.experiments_history),
			'current_experiment': {
				'node_name': tracker_instance.current_experiment_data.get('node_name'),
				'node_type': tracker_instance.current_experiment_data.get('node_type'),
				'iterations_count': len(tracker_instance.current_experiment_data.get('iterations', []))
			},
			'flow_summary': {
				'total_nodes': tracker_instance.flow_summary.get('total_nodes_executed'),
				'recovery_conditions': len(tracker_instance.flow_summary.get('recovery_conditions', [])),
				'failure_conditions': len(tracker_instance.flow_summary.get('failure_conditions', []))
			}
		}
		
		self.log(f"Tracker State: {state}", "TRACKER", state)
		
		# Save detailed state to file
		state_file = os.path.join(self.debug_folder, f"tracker_state_{self.debug_session_id}.json")
		with open(state_file, 'w') as f:
			json.dump({
				'timestamp': datetime.now().isoformat(),
				'experiments_history': tracker_instance.experiments_history,
				'current_experiment': tracker_instance.current_experiment_data,
				'flow_summary': tracker_instance.flow_summary
			}, f, indent=2, default=str)
	
	def log_error(self, error_message: str, exception: Exception = None):
		"""Log errors with full details"""
		self.log(f"ERROR: {error_message}", "ERROR")
		
		if exception:
			import traceback
			error_details = {
				'exception_type': type(exception).__name__,
				'exception_message': str(exception),
				'traceback': traceback.format_exc()
			}
			self.log(f"Exception Details: {error_details}", "ERROR", error_details)
	
	def create_debug_summary(self):
		"""Create debug session summary"""
		if not self.enabled:
			return
		
		summary_file = os.path.join(self.debug_folder, f"debug_summary_{self.debug_session_id}.txt")
		
		with open(summary_file, 'w') as f:
			f.write("=== EXPERIMENT TRACKER DEBUG SESSION SUMMARY ===\n")
			f.write(f"Session ID: {self.debug_session_id}\n")
			f.write(f"End Time: {datetime.now().isoformat()}\n")
			f.write("=" * 60 + "\n\n")
			
			# List all debug files created
			debug_files = [f for f in os.listdir(self.debug_folder) 
						  if self.debug_session_id in f]
			
			f.write("Debug Files Created:\n")
			for file in debug_files:
				f.write(f"  - {file}\n")
			
			f.write(f"\nTotal Debug Files: {len(debug_files)}\n")
		
		if self.verbose:
			print(f"[TRACKER] Debug session summary created: {summary_file}")

# Global debug instance - can be easily enabled/disabled
DEBUG_ENABLED = False  # Set to False to disable all debugging
#experiment_debugger = ExperimentDebugger(enabled=DEBUG_ENABLED, verbose=True)

class ExperimentTracker:
	"""Enhanced experiment tracking with comprehensive data collection"""
	
	def __init__(self, flow_config_path=None):
		self.flow_config_path = flow_config_path
		self.experiments_history = []
		self.current_experiment_data = {}

		# Initialize debugger
		self.debugger = ExperimentDebugger(enabled=DEBUG_ENABLED)
		
		self.reset_data()

		self.debugger.log("ExperimentTracker initialized", "TRACKER")

	def reset_data(self):

		self.flow_summary = {
			'start_time': None,
			'end_time': None,
			'total_nodes_executed': 0,
			'recovery_conditions': [],
			'failure_conditions': [],
			'characterization_data': [],
			'test_folders': [],
			'unit_configurations': [],
			'sweep_analysis': {
				'voltage_sweeps': [],
				'frequency_sweeps': [],
				'sensitivity_patterns': {}
			}
		}

	def start_experiment_tracking(self, node_id, node_name, experiment_config, node_instance=None):
		"""Start tracking a new experiment with enhanced sweep detection and proper node type detection"""
		
		# Get the actual node type from the instance if provided
		if node_instance:
			node_type = type(node_instance).__name__
			print(f"[CONFIG] DEBUG: ExperimentTracker - Node type from instance: {node_type}")
		else:
			node_type = self._get_node_type_from_name(node_name)
			print(f"[CONFIG] DEBUG: ExperimentTracker - Node type from name: {node_type}")
		
		self.debugger.log_experiment_start(node_id, node_name, experiment_config)
		
		self.current_experiment_data = {
			'node_id': node_id,
			'node_name': node_name,
			'node_type': node_type,  # Now properly set from actual instance
			'experiment_config': experiment_config.copy(),
			'start_time': datetime.now(),
			'end_time': None,
			'iterations': [],
			'final_result': None,
			'output_port': None,
			'test_folder': None,
			'summary_file_path': None,
			'unit_state': {},
			'failure_patterns': [],
			'recovery_indicators': [],
			'sweep_data': self._extract_sweep_configuration(experiment_config),
			'voltage_frequency_analysis': {
				'voltage_dependency': None,
				'frequency_dependency': None,
				'combined_sensitivity': None,
				'voltage_type_used': experiment_config.get('Voltage Type', 'vbump')
			}
		}
		
		print(f"[CONFIG] DEBUG: ExperimentTracker - Experiment tracking started for {node_type}: {node_name}")
			
	def _get_node_type_from_name(self, node_name):
		"""Extract node type from node name with enhanced detection"""
		node_name_lower = node_name.lower()
		
		print(f"[CONFIG] DEBUG: ExperimentTracker - Detecting node type from name: '{node_name}'")
		
		# More comprehensive node type detection
		if 'allfail' in node_name_lower or 'all_fail' in node_name_lower:
			detected_type = 'AllFailFlowInstance'
		elif 'singlefail' in node_name_lower or 'single_fail' in node_name_lower:
			detected_type = 'SingleFailFlowInstance'
		elif 'majorityfail' in node_name_lower or 'majority_fail' in node_name_lower:
			detected_type = 'MajorityFailFlowInstance'
		elif 'adaptive' in node_name_lower:
			detected_type = 'AdaptiveFlowInstance'
		elif 'characterization' in node_name_lower or 'char' in node_name_lower:
			detected_type = 'CharacterizationFlowInstance'
		elif 'datacollection' in node_name_lower or 'data_collection' in node_name_lower:
			detected_type = 'DataCollectionFlowInstance'
		elif 'analysis' in node_name_lower:
			detected_type = 'AnalysisFlowInstance'
		elif 'start' in node_name_lower:
			detected_type = 'StartNodeFlowInstance'
		elif 'end' in node_name_lower:
			detected_type = 'EndNodeFlowInstance'
		else:
			detected_type = 'FlowInstance'
		
		print(f"[CONFIG] DEBUG: ExperimentTracker - Detected node type: {detected_type}")
		return detected_type

	def _extract_sweep_configuration(self, experiment_config):
		"""Extract sweep configuration details with case normalization"""
		test_type = experiment_config.get('Test Type', '')
		
		if test_type != 'Sweep':
			return None
			
		# Normalize case for consistency
		sweep_type = experiment_config.get('Type', '').lower()  # voltage or frequency
		sweep_domain = experiment_config.get('Domain', '').lower()  # ia or cfc
		
		return {
			'sweep_type': sweep_type,
			'sweep_domain': sweep_domain,
			'start_value': experiment_config.get('Start', 0),
			'end_value': experiment_config.get('End', 0),
			'step_value': experiment_config.get('Steps', 1),
			'voltage_type': experiment_config.get('Voltage Type', 'vbump'),
			'sweep_values': self._calculate_sweep_values(experiment_config)
		}

	def _calculate_sweep_values(self, experiment_config):
		"""Calculate actual sweep values that will be tested"""
		sweep_type = experiment_config.get('Type', '')
		start = experiment_config.get('Start', 0)
		end = experiment_config.get('End', 0)
		step = experiment_config.get('Steps', 1)
		
		if sweep_type == 'frequency':
			return list(range(int(start), int(end) + int(step), int(step)))
		elif sweep_type == 'voltage':
			values = []
			current = start
			while current <= end + step/2:
				values.append(round(current, 5))
				current += step
			return values
		else:
			return []

	def track_iteration(self, iteration_num, status, scratchpad, seed, config_snapshot):
		"""Track individual iteration results with enhanced sweep value tracking"""
		# Get the actual sweep value used for this iteration
		sweep_value = self._get_sweep_value_for_iteration(iteration_num, config_snapshot)
		
		# Debug iteration
		self.debugger.log_iteration(iteration_num, status, config_snapshot, sweep_value)
				
		iteration_data = {
			'iteration': iteration_num,
			'status': status,
			'scratchpad': scratchpad,
			'seed': seed,
			'timestamp': datetime.now(),
			'config_snapshot': {
				'voltage_ia': config_snapshot.get('volt_IA'),
				'voltage_cfc': config_snapshot.get('volt_CFC'),
				'frequency_ia': config_snapshot.get('freq_ia'),
				'frequency_cfc': config_snapshot.get('freq_cfc'),
				'content': config_snapshot.get('content'),
				'mask': config_snapshot.get('mask'),
				'check_core': config_snapshot.get('check_core'),
				'voltage_type': config_snapshot.get('voltage_type', 'vbump')  # Track voltage type
			},
			'sweep_value': sweep_value,
			'sweep_point_analysis': self._analyze_sweep_point(iteration_num, status, sweep_value)
		}
		
		if hasattr(self, 'current_experiment_data'):
			self.current_experiment_data['iterations'].append(iteration_data)

	def _get_sweep_value_for_iteration(self, iteration_num, config_snapshot):
		"""Extract the actual sweep value used for this iteration"""
		sweep_data = self.current_experiment_data.get('sweep_data')
		if not sweep_data:
			return None
			
		sweep_type = sweep_data.get('sweep_type')
		sweep_domain = sweep_data.get('sweep_domain')
		
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
		
		return None

	def _analyze_sweep_point(self, iteration_num, status, sweep_value):
		"""Analyze individual sweep point for patterns"""
		return {
			'iteration': iteration_num,
			'sweep_value': sweep_value,
			'result': status,
			'is_failure': status == 'FAIL',
			'is_pass': status == 'PASS'
		}
	
	def complete_experiment(self, final_result, output_port, test_folder, summary_path=None):
		"""Complete experiment tracking with enhanced analysis"""
		try:
			if not hasattr(self, 'current_experiment_data'):
				return
			
			self.debugger.log_experiment_complete(final_result, output_port, test_folder)
						
			# Get test folder and summary file from framework if not provided
			if not test_folder and hasattr(self, '_framework_api'):
				test_folder = self._extract_test_folder_from_framework()
				summary_path = self._extract_summary_path_from_framework(test_folder)
				
			self.current_experiment_data.update({
				'end_time': datetime.now(),
				'final_result': final_result,
				'output_port': output_port,
				'test_folder': test_folder,
				'summary_file_path': summary_path
			})
			
			# Enhanced analysis for sweeps
			if self.current_experiment_data.get('sweep_data'):
				self._analyze_sweep_results()
				if self.current_experiment_data.get('sweep_analysis'):
					self.debugger.log_sweep_analysis(self.current_experiment_data['sweep_analysis'])
			
			# Analyze results for patterns
			self._analyze_experiment_patterns()
			
			# Add to history
			self.experiments_history.append(self.current_experiment_data.copy())
			
			# Update flow summary
			self._update_flow_summary()
			
			# Persist to INI file
			self._persist_to_ini()
				
			# Final tracker state
			self.debugger.log_tracker_state(self)
		
		except Exception as e:
			self.debugger.log_error(f"Error completing experiment tracking", e)	
	
	def _extract_test_folder_from_framework(self):
		"""Extract test folder from framework's _generate_summary section"""
		try:
			if hasattr(self, '_framework_api') and self._framework_api:
				framework = self._framework_api.framework
				if hasattr(framework.config, 'tfolder'):
					return framework.config.tfolder
		except Exception as e:
			print(f"Error extracting test folder from framework: {e}")
		return None

	def _extract_summary_path_from_framework(self, test_folder):
		"""Extract summary file path from framework"""
		if not test_folder:
			return None
			
		try:
			# Look for summary files in the test folder
			summary_files = []
			if os.path.exists(test_folder):
				for file in os.listdir(test_folder):
					if file.startswith('Summary_') and file.endswith('.xlsx'):
						summary_files.append(os.path.join(test_folder, file))
			
			return summary_files[0] if summary_files else None
		except Exception as e:
			print(f"Error extracting summary path: {e}")
			return None

	def _analyze_sweep_results(self):
		"""Analyze sweep results for voltage/frequency sensitivity patterns with voltage type awareness"""
		sweep_data = self.current_experiment_data.get('sweep_data')
		iterations = self.current_experiment_data.get('iterations', [])
		
		if not sweep_data or not iterations:
			return
		
		sweep_type = sweep_data.get('sweep_type')
		sweep_domain = sweep_data.get('sweep_domain')
		voltage_type = sweep_data.get('voltage_type', 'vbump')
		
		# Analyze failure points
		failure_points = [it for it in iterations if it['status'] == 'FAIL']
		pass_points = [it for it in iterations if it['status'] == 'PASS']
		
		analysis = {
			'sweep_type': sweep_type,
			'sweep_domain': sweep_domain,
			'voltage_type': voltage_type,  # Include voltage type in analysis
			'total_points': len(iterations),
			'failure_points': len(failure_points),
			'pass_points': len(pass_points),
			'failure_values': [it['sweep_value'] for it in failure_points if it['sweep_value'] is not None],
			'pass_values': [it['sweep_value'] for it in pass_points if it['sweep_value'] is not None],
			'sensitivity_analysis': self._determine_sensitivity_pattern(failure_points, pass_points, sweep_data)
		}
		
		self.current_experiment_data['sweep_analysis'] = analysis
		
		# Update flow-level sweep tracking
		self._update_flow_sweep_analysis(analysis)

	def _determine_sensitivity_pattern(self, failure_points, pass_points, sweep_data):
		"""Determine sensitivity patterns with proper 'no sensitivity' detection"""
		voltage_type = sweep_data.get('voltage_type', 'vbump')
		sweep_type = sweep_data.get('sweep_type', 'unknown')
		sweep_domain = sweep_data.get('sweep_domain', 'unknown')
		
		total_points = len(failure_points) + len(pass_points)
		
		print(f"[DEBUG] DEBUG: Sensitivity Analysis - {sweep_type} {sweep_domain} ({voltage_type})")
		print(f"[DEBUG] DEBUG: Total points: {total_points}, Failures: {len(failure_points)}, Passes: {len(pass_points)}")
		
		if not failure_points:
			return {
				'pattern': 'no_sensitivity',
				'description': f'Unit not sensitive to {sweep_type} {sweep_domain} ({voltage_type}) - all points pass',
				'recommendation': 'Unit appears stable across tested range',
				'voltage_type_context': voltage_type
			}
		
		if not pass_points:
			# ALL POINTS FAIL = NO SENSITIVITY (no recovery condition found)
			return {
				'pattern': 'no_sensitivity',
				'description': f'Unit not sensitive to {sweep_type} {sweep_domain} ({voltage_type}) - fails across entire range (no recovery condition)',
				'recommendation': f'Unit fails across entire tested {sweep_type} range - no sensitivity threshold found',
				'voltage_type_context': voltage_type,
				'failure_mode': 'complete_failure_no_recovery'
			}
		
		# We have both failures and passes - analyze the pattern
		failure_values = [fp['sweep_value'] for fp in failure_points if fp['sweep_value'] is not None]
		pass_values = [pp['sweep_value'] for pp in pass_points if pp['sweep_value'] is not None]
		
		if failure_values and pass_values:
			min_fail = min(failure_values)
			max_fail = max(failure_values)
			min_pass = min(pass_values)
			max_pass = max(pass_values)
			
			print(f"[DEBUG] DEBUG: Failure range: {min_fail} to {max_fail}")
			print(f"[DEBUG] DEBUG: Pass range: {min_pass} to {max_pass}")
			
			# Determine pattern based on value distribution
			if max_fail < min_pass:
				# Failures are at lower values, passes at higher values
				pattern = 'threshold_sensitivity'
				description = f'Unit sensitive below {min_pass} {sweep_type} ({voltage_type}) - recovers at higher values'
				recommendation = f'Use values >= {min_pass} for recovery'
			elif min_fail > max_pass:
				# Failures are at higher values, passes at lower values  
				pattern = 'upper_threshold_sensitivity'
				description = f'Unit sensitive above {max_pass} {sweep_type} ({voltage_type}) - recovers at lower values'
				recommendation = f'Use values <= {max_pass} for recovery'
			else:
				# Mixed pattern - failures and passes are interleaved
				pattern = 'mixed_sensitivity'
				description = f'Unit has mixed sensitivity pattern for {sweep_type} {sweep_domain} ({voltage_type})'
				recommendation = f'Use passing values: {sorted(pass_values)} for recovery'
			
			return {
				'pattern': pattern,
				'description': description,
				'failure_range': [min_fail, max_fail],
				'pass_range': [min_pass, max_pass],
				'safe_values': sorted(pass_values),
				'voltage_type_context': voltage_type,
				'recommendation': self._generate_sensitivity_recommendation(pattern, failure_values, pass_values, voltage_type)
			}
		
		return {
			'pattern': 'unknown',
			'description': 'Unable to determine sensitivity pattern',
			'recommendation': 'More data needed for analysis',
			'voltage_type_context': voltage_type
		}

	def _generate_sensitivity_recommendation(self, pattern, failure_values, pass_values, voltage_type):
		"""Generate recommendations based on sensitivity pattern and voltage type"""
		base_recommendation = ""
		
		if pattern == 'threshold_sensitivity':
			safe_value = min(pass_values) if pass_values else None
			base_recommendation = f'Use values >= {safe_value} for recovery' if safe_value else 'Use higher values for recovery'
		elif pattern == 'upper_threshold_sensitivity':
			safe_value = max(pass_values) if pass_values else None
			base_recommendation = f'Use values <= {safe_value} for recovery' if safe_value else 'Use lower values for recovery'
		else:
			base_recommendation = 'Avoid failure values, use passing values for recovery'
		
		# Add voltage type specific context
		if voltage_type == 'PPVC':
			base_recommendation += ' (Consider PPVC reduces guardbands on all domains)'
		elif voltage_type == 'vbump':
			base_recommendation += ' (vbump specific to tested domain)'
		
		return base_recommendation

	def _generate_content_recommendations(self, content_analysis):
		"""Generate content-specific recommendations"""
		recommendations = []
		
		if content_analysis.get('status') != 'analyzed':
			return recommendations
		
		best_overall = content_analysis.get('best_failure_reproduction')
		if best_overall:
			content_type = best_overall['content_type']
			config = best_overall['configuration']
			
			if content_type.lower() == 'dragon':
				rec = {
					'type': 'dragon_failure_reproduction',
					'priority': 'high',
					'description': f'Use Dragon configuration that reproduced {best_overall["failure_count"]} failures',
					'details': {
						'dragon_content_line': config.get('dragon_content_line'),
						'dragon_content_path': config.get('dragon_content_path'),
						'vvar_settings': {
							'vvar0': config.get('vvar0'),
							'vvar1': config.get('vvar1'),
							'vvar2': config.get('vvar2'),
							'vvar3': config.get('vvar3'),
							'vvar_extra': config.get('vvar_extra')
						}
					}
				}
				recommendations.append(rec)
				
			elif content_type.lower() == 'linux':
				linux_lines = {k: v for k, v in config.items() if k.startswith('linux_content_line_')}
				rec = {
					'type': 'linux_failure_reproduction',
					'priority': 'high',
					'description': f'Use Linux configuration that reproduced {best_overall["failure_count"]} failures',
					'details': {
						'linux_content_lines': linux_lines
					}
				}
				recommendations.append(rec)
		
		print("[DEBUG] DEBUG: AnalysisFlowInstance - Content Recommendations Complete")

		return recommendations

	def _generate_content_analysis(self):
		"""Generate detailed content-based failure analysis"""
		try:
			print("[DEBUG] DEBUG: AnalysisFlowInstance - Starting content analysis...")
			
			# Group experiments by content type
			content_groups = {}
			
			for exp in self.experiments_history:
				if exp is None:
					continue
					
				exp_config = exp.get('experiment_config', {})
				content = exp_config.get('Content', 'Unknown')
				
				if content not in content_groups:
					content_groups[content] = []
				content_groups[content].append(exp)
			
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Found content types: {list(content_groups.keys())}")
			
			content_analysis = {}
			
			for content_type, experiments in content_groups.items():
				print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Analyzing {content_type} content ({len(experiments)} experiments)")
				content_analysis[content_type] = self._analyze_content_type(content_type, experiments)
			
			return {
				'status': 'analyzed',
				'content_types_found': list(content_groups.keys()),
				'total_content_experiments': sum(len(exps) for exps in content_groups.values()),
				'content_analysis': content_analysis,
				'best_failure_reproduction': self._find_best_failure_reproduction_across_content(content_analysis)
			}
			
		except Exception as e:
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Error in content analysis: {e}")
			return {
				'status': 'error',
				'message': str(e)
			}

	def _analyze_content_type(self, content_type, experiments):
		"""Analyze experiments for a specific content type"""
		
		# Collect all iterations from all experiments of this content type
		all_iterations = []
		all_failures = []
		all_passes = []
		configuration_failures = {}
		
		for exp in experiments:
			iterations = exp.get('iterations', [])
			exp_config = exp.get('experiment_config', {})
			node_name = exp.get('node_name', 'Unknown')
			
			for iteration in iterations:
				iteration_data = {
					'experiment_name': node_name,
					'iteration_num': iteration.get('iteration', 0),
					'status': iteration.get('status', 'Unknown'),
					'scratchpad': iteration.get('scratchpad', ''),
					'seed': iteration.get('seed', ''),
					'config_snapshot': iteration.get('config_snapshot', {}),
					'experiment_config': exp_config,
					'sweep_value': iteration.get('sweep_value')
				}
				
				all_iterations.append(iteration_data)
				
				if iteration_data['status'] == 'FAIL':
					all_failures.append(iteration_data)
					
					# Track configuration that caused this failure
					config_key = self._create_config_signature(iteration_data, content_type)
					if config_key not in configuration_failures:
						configuration_failures[config_key] = {
							'config': self._extract_relevant_config(iteration_data, content_type),
							'failures': [],
							'failure_count': 0,
							'scratchpads': set(),
							'seeds': set(),
							'experiments': set()
						}
					
					configuration_failures[config_key]['failures'].append(iteration_data)
					configuration_failures[config_key]['failure_count'] += 1
					configuration_failures[config_key]['scratchpads'].add(iteration_data['scratchpad'])
					configuration_failures[config_key]['seeds'].add(iteration_data['seed'])
					configuration_failures[config_key]['experiments'].add(iteration_data['experiment_name'])
					
				elif iteration_data['status'] == 'PASS':
					all_passes.append(iteration_data)
		
		# Calculate statistics
		total_iterations = len(all_iterations)
		total_failures = len(all_failures)
		total_passes = len(all_passes)
		failure_rate = (total_failures / total_iterations * 100) if total_iterations > 0 else 0
		
		# Find best failure reproduction configuration
		best_config = None
		if configuration_failures:
			best_config = max(configuration_failures.values(), key=lambda x: x['failure_count'])
			
			# Convert sets to lists for JSON serialization
			for config_data in configuration_failures.values():
				config_data['scratchpads'] = list(config_data['scratchpads'])
				config_data['seeds'] = list(config_data['seeds'])
				config_data['experiments'] = list(config_data['experiments'])
		
		return {
			'content_type': content_type,
			'total_experiments': len(experiments),
			'total_iterations': total_iterations,
			'total_failures': total_failures,
			'total_passes': total_passes,
			'failure_rate': failure_rate,
			'configuration_failures': configuration_failures,
			'best_failure_config': best_config,
			'failure_reproduction_summary': self._generate_content_failure_summary(content_type, best_config, total_failures),
			'content_specific_insights': self._generate_content_specific_insights(content_type, configuration_failures, all_failures)
		}

	def _create_config_signature(self, iteration_data, content_type):
		"""Create a unique signature for configuration based on content type"""
		config_snapshot = iteration_data['config_snapshot']
		exp_config = iteration_data['experiment_config']
		
		if content_type.lower() == 'dragon':
			# For Dragon content, focus on Dragon-specific configuration
			signature_parts = [
				f"mask_{config_snapshot.get('mask', exp_config.get('Configuration (Mask)', 'none'))}",
				f"core_{config_snapshot.get('check_core', exp_config.get('Check Core', 'none'))}",
				f"vtype_{config_snapshot.get('voltage_type', exp_config.get('Voltage Type', 'vbump'))}",
				f"via_{config_snapshot.get('voltage_ia', exp_config.get('Voltage IA', 'none'))}",
				f"vcfc_{config_snapshot.get('voltage_cfc', exp_config.get('Voltage CFC', 'none'))}",
				f"fia_{config_snapshot.get('frequency_ia', exp_config.get('Frequency IA', 'none'))}",
				f"fcfc_{config_snapshot.get('frequency_cfc', exp_config.get('Frequency CFC', 'none'))}",
				f"vvar0_{exp_config.get('VVAR0', 'none')}",
				f"vvar1_{exp_config.get('VVAR1', 'none')}",
				f"vvar2_{exp_config.get('VVAR2', 'none')}",
				f"vvar3_{exp_config.get('VVAR3', 'none')}",
				f"vvar_extra_{exp_config.get('VVAR_EXTRA', 'none')}",
				f"dragon_path_{exp_config.get('Dragon Content Path', 'none')}",
				f"dragon_line_{exp_config.get('Dragon Content Line', 'none')}"
			]
		elif content_type.lower() == 'linux':
			# For Linux content, focus on Linux-specific configuration
			signature_parts = [
				f"mask_{config_snapshot.get('mask', exp_config.get('Configuration (Mask)', 'none'))}",
				f"core_{config_snapshot.get('check_core', exp_config.get('Check Core', 'none'))}",
				f"vtype_{config_snapshot.get('voltage_type', exp_config.get('Voltage Type', 'vbump'))}",
				f"via_{config_snapshot.get('voltage_ia', exp_config.get('Voltage IA', 'none'))}",
				f"vcfc_{config_snapshot.get('voltage_cfc', exp_config.get('Voltage CFC', 'none'))}",
				f"fia_{config_snapshot.get('frequency_ia', exp_config.get('Frequency IA', 'none'))}",
				f"fcfc_{config_snapshot.get('frequency_cfc', exp_config.get('Frequency CFC', 'none'))}",
			]
			linux_parts = []
			for i in range(10):
				line_key = f'Linux Content Line {i}'
				line_value = exp_config.get(line_key, 'none')
				linux_parts.append(f"linux_line{i}_{line_value}")
			
			signature_parts = signature_parts + linux_parts

		else:
			# Generic configuration signature
			signature_parts = [
				f"mask_{config_snapshot.get('mask', exp_config.get('Configuration (Mask)', 'none'))}",
				f"core_{config_snapshot.get('check_core', exp_config.get('Check Core', 'none'))}",
				f"vtype_{config_snapshot.get('voltage_type', exp_config.get('Voltage Type', 'vbump'))}",
				f"via_{config_snapshot.get('voltage_ia', exp_config.get('Voltage IA', 'none'))}",
				f"vcfc_{config_snapshot.get('voltage_cfc', exp_config.get('Voltage CFC', 'none'))}",
				f"fia_{config_snapshot.get('frequency_ia', exp_config.get('Frequency IA', 'none'))}",
				f"fcfc_{config_snapshot.get('frequency_cfc', exp_config.get('Frequency CFC', 'none'))}"
			]
		
		return "_".join(signature_parts)

	def _extract_relevant_config(self, iteration_data, content_type):
		"""Extract relevant configuration based on content type"""
		config_snapshot = iteration_data['config_snapshot']
		exp_config = iteration_data['experiment_config']
		
		base_config = {
			'mask': config_snapshot.get('mask', exp_config.get('Configuration (Mask)')),
			'check_core': config_snapshot.get('check_core', exp_config.get('Check Core')),
			'voltage_type': config_snapshot.get('voltage_type', exp_config.get('Voltage Type')),
			'voltage_ia': config_snapshot.get('voltage_ia', exp_config.get('Voltage IA')),
			'voltage_cfc': config_snapshot.get('voltage_cfc', exp_config.get('Voltage CFC')),
			'frequency_ia': config_snapshot.get('frequency_ia', exp_config.get('Frequency IA')),
			'frequency_cfc': config_snapshot.get('frequency_cfc', exp_config.get('Frequency CFC'))
		}
		
		if content_type.lower() == 'dragon':
			base_config.update({
				'vvar0': exp_config.get('VVAR0'),
				'vvar1': exp_config.get('VVAR1'),
				'vvar2': exp_config.get('VVAR2'),
				'vvar3': exp_config.get('VVAR3'),
				'vvar_extra': exp_config.get('VVAR_EXTRA'),
				'dragon_content_path': exp_config.get('Dragon Content Path'),
				'dragon_content_line': exp_config.get('Dragon Content Line')
			})
		elif content_type.lower() == 'linux':
			# Linux-specific configuration
			linux_config = {}
			# Extract all Linux Content Lines 0-9
			for i in range(10):
				line_key = f'Linux Content Line {i}'
				line_value = exp_config.get(line_key)
				if line_value is not None:
					linux_config[f'linux_content_line_{i}'] = line_value
			
			base_config.update(linux_config)
		
		# Remove None values
		return {k: v for k, v in base_config.items() if v is not None}

	def _generate_content_failure_summary(self, content_type, best_config, total_failures):
		"""Generate summary of failure reproduction for content type"""
		if not best_config or total_failures == 0:
			return f"No failures found for {content_type} content"
		
		failure_count = best_config['failure_count']
		failure_percentage = (failure_count / total_failures * 100) if total_failures > 0 else 0
		
		return f"{content_type} content: Best configuration reproduced {failure_count} failures ({failure_percentage:.1f}% of all {content_type} failures)"

	def _generate_content_specific_insights(self, content_type, configuration_failures, all_failures):
		"""Generate content-specific insights"""
		insights = []
		
		if not configuration_failures:
			return [f"No failure patterns found for {content_type} content"]
		
		# Sort configurations by failure count
		sorted_configs = sorted(configuration_failures.values(), key=lambda x: x['failure_count'], reverse=True)
		
		# Top failure configuration
		top_config = sorted_configs[0]
		insights.append(f"Most effective failure configuration reproduced {top_config['failure_count']} failures")
		
		# Scratchpad analysis
		all_scratchpads = set()
		for failure in all_failures:
			if failure['scratchpad']:
				all_scratchpads.add(failure['scratchpad'])
		
		if all_scratchpads:
			insights.append(f"Found {len(all_scratchpads)} unique failure scratchpads")
			most_common_scratchpad = max(all_scratchpads, key=lambda sp: sum(1 for f in all_failures if f['scratchpad'] == sp))
			scratchpad_count = sum(1 for f in all_failures if f['scratchpad'] == most_common_scratchpad)
			insights.append(f"Most common scratchpad: '{most_common_scratchpad}' ({scratchpad_count} occurrences)")
		
		# Configuration diversity
		insights.append(f"Found {len(configuration_failures)} unique failure-causing configurations")
	
		# Content-specific insights
		if content_type.lower() == 'dragon':
			# Analyze Dragon-specific fields
			dragon_lines = set()
			dragon_paths = set()
			vvar_combinations = set()
			
			for config_data in configuration_failures.values():
				config = config_data['config']
				
				# Dragon Content Line analysis
				dragon_line = config.get('dragon_content_line')
				if dragon_line:
					dragon_lines.add(dragon_line)
				
				# Dragon Content Path analysis
				dragon_path = config.get('dragon_content_path')
				if dragon_path:
					dragon_paths.add(dragon_path)
				
				# VVAR combination analysis
				vvar_combo = (
					config.get('vvar0'),
					config.get('vvar1'),
					config.get('vvar2'),
					config.get('vvar3'),
					config.get('vvar_extra')
				)
				if any(v is not None for v in vvar_combo):
					vvar_combinations.add(vvar_combo)
			
			if dragon_lines:
				insights.append(f"Dragon content lines that caused failures: {sorted(dragon_lines)}")
			
			if dragon_paths:
				insights.append(f"Dragon content paths that caused failures: {len(dragon_paths)} unique paths")
				# Show most common path
				most_common_path = max(dragon_paths, key=lambda path: sum(1 for cd in configuration_failures.values() if cd['config'].get('dragon_content_path') == path))
				path_count = sum(1 for cd in configuration_failures.values() if cd['config'].get('dragon_content_path') == most_common_path)
				insights.append(f"Most failure-prone Dragon path: '{most_common_path}' ({path_count} failure configs)")
			
			if vvar_combinations:
				insights.append(f"Found {len(vvar_combinations)} unique VVAR combinations causing failures")
				# Analyze individual VVAR values
				vvar0_values = set(config.get('vvar0') for config in [cd['config'] for cd in configuration_failures.values()] if config.get('vvar0'))
				vvar1_values = set(config.get('vvar1') for config in [cd['config'] for cd in configuration_failures.values()] if config.get('vvar1'))
				
				if vvar0_values:
					insights.append(f"VVAR0 values in failures: {sorted(vvar0_values)}")
				if vvar1_values:
					insights.append(f"VVAR1 values in failures: {sorted(vvar1_values)}")
		
		elif content_type.lower() == 'linux':
			# Analyze Linux-specific fields
			linux_lines_used = {}
			
			for config_data in configuration_failures.values():
				config = config_data['config']
				failure_count = config_data['failure_count']
				
				# Check which Linux Content Lines are being used
				for i in range(10):
					line_key = f'linux_content_line_{i}'
					line_value = config.get(line_key)
					if line_value is not None:
						if i not in linux_lines_used:
							linux_lines_used[i] = {'values': set(), 'failure_count': 0}
						linux_lines_used[i]['values'].add(line_value)
						linux_lines_used[i]['failure_count'] += failure_count
			
			if linux_lines_used:
				insights.append(f"Linux content lines used in failures: {sorted(linux_lines_used.keys())}")
				
				# Find most failure-prone line
				most_failure_prone_line = max(linux_lines_used.keys(), key=lambda line: linux_lines_used[line]['failure_count'])
				line_data = linux_lines_used[most_failure_prone_line]
				insights.append(f"Most failure-prone Linux line: Line {most_failure_prone_line} ({line_data['failure_count']} total failures)")
				insights.append(f"Linux Line {most_failure_prone_line} values: {sorted(line_data['values'])}")
				
				# Show all lines with their values
				for line_num in sorted(linux_lines_used.keys()):
					line_data = linux_lines_used[line_num]
					if len(line_data['values']) > 1:
						insights.append(f"Linux Line {line_num} has {len(line_data['values'])} different values causing failures")
		
		return insights

	def _find_best_failure_reproduction_across_content(self, content_analysis):
		"""Find the best failure reproduction configuration across all content types"""
		best_overall = None
		best_failure_count = 0
		
		for content_type, analysis in content_analysis.items():
			best_config = analysis.get('best_failure_config')
			if best_config and best_config['failure_count'] > best_failure_count:
				best_failure_count = best_config['failure_count']
				best_overall = {
					'content_type': content_type,
					'configuration': best_config['config'],
					'failure_count': best_config['failure_count'],
					'scratchpads': best_config['scratchpads'],
					'seeds': best_config['seeds'],
					'experiments': best_config['experiments'],
					'summary': f"{content_type} content with {best_failure_count} failures reproduced"
				}
		
		return best_overall
	
	def _update_flow_sweep_analysis(self, sweep_analysis):
		"""Update flow-level sweep analysis"""
		sweep_type = sweep_analysis['sweep_type']
		sweep_domain = sweep_analysis['sweep_domain']
		
		sweep_key = f"{sweep_type}_{sweep_domain}"
		
		if sweep_key not in self.flow_summary['sweep_analysis']['sensitivity_patterns']:
			self.flow_summary['sweep_analysis']['sensitivity_patterns'][sweep_key] = []
		
		self.flow_summary['sweep_analysis']['sensitivity_patterns'][sweep_key].append({
			'node_name': self.current_experiment_data['node_name'],
			'analysis': sweep_analysis,
			'timestamp': datetime.now()
		})

	def get_adaptive_analysis_data(self, target_node_type='AllFailFlowInstance'):
		"""Get analysis data specifically for AdaptiveFlowInstance with enhanced prioritization"""
		self.debugger.log(f"Getting adaptive analysis data for: {target_node_type}", "ANALYSIS")
		
		print(f"[CONFIG] DEBUG: ExperimentTracker - Looking for experiments with node_type: {target_node_type}")
		print(f"[CONFIG] DEBUG: ExperimentTracker - Total experiments in history: {len(self.experiments_history)}")
		
		# Debug: Show all experiment types in history
		for i, exp in enumerate(self.experiments_history):
			if exp:
				print(f"[CONFIG] DEBUG: ExperimentTracker - Experiment {i}: {exp.get('node_name', 'Unknown')} (Type: {exp.get('node_type', 'Unknown')}) - Result: {exp.get('final_result', 'Unknown')}")
			else:
				print(f"[CONFIG] DEBUG: ExperimentTracker - Experiment {i}: None")
		
		try:
			# Only include data from AllFailFlowInstance nodes for adaptive analysis
			relevant_experiments = [
				exp for exp in self.experiments_history 
				if exp is not None and exp.get('node_type') == target_node_type
			]
			
			print(f"[CONFIG] DEBUG: ExperimentTracker - Found {len(relevant_experiments)} relevant experiments")
			
			if not relevant_experiments:
				print(f"[CONFIG] DEBUG: ExperimentTracker - No {target_node_type} experiments found")
				return {
					'status': 'no_data',
					'message': f'No {target_node_type} data available for adaptive analysis',
					'default_config': self._get_default_config(),
					'debug_info': {
						'total_experiments': len(self.experiments_history),
						'target_node_type': target_node_type,
						'available_node_types': list(set(exp.get('node_type', 'Unknown') for exp in self.experiments_history if exp))
					}
				}
			
			# Prioritize experiments: solid repro first, then highest fail rate
			best_experiment = self._select_best_experiment_for_adaptive(relevant_experiments)
			
			print(f"[CONFIG] DEBUG: ExperimentTracker - Selected best experiment: {best_experiment.get('node_name')} (Result: {best_experiment.get('final_result')}, Port: {best_experiment.get('output_port')})")
			
			analysis = {
				'status': 'data_available',
				'source_experiment': {
					'node_name': best_experiment['node_name'],
					'output_port': best_experiment['output_port'],
					'final_result': best_experiment['final_result']
				},
				'recommended_config': self._extract_adaptive_config(best_experiment),
				'sweep_insights': self._get_sweep_insights_for_adaptive(best_experiment),
				'failure_patterns': best_experiment.get('failure_patterns', {}),
				'recovery_potential': self._assess_recovery_potential(best_experiment),
				'voltage_type_context': self._extract_voltage_type_context(best_experiment),
				'selection_reason': self._get_selection_reason(best_experiment, relevant_experiments)
			}
			
			self.debugger.log_adaptive_analysis(analysis)
			return analysis
			
		except Exception as e:
			self.debugger.log_error(f"Error in adaptive analysis", e)
			return {'status': 'error', 'message': str(e)}

	def _select_best_experiment_for_adaptive(self, experiments):
		"""Select the best experiment for adaptive analysis with prioritization"""
		print("[CONFIG] DEBUG: ExperimentTracker - Selecting best experiment for adaptive analysis...")
		
		# Categorize experiments
		solid_repro_experiments = []
		flaky_experiments = []
		
		for exp in experiments:
			final_result = exp.get('final_result', '')
			output_port = exp.get('output_port', '')
			iterations = exp.get('iterations', [])
			
			# Calculate fail statistics
			fail_count = len([it for it in iterations if it['status'] == 'FAIL'])
			pass_count = len([it for it in iterations if it['status'] == 'PASS'])
			total_count = len(iterations)
			fail_rate = fail_count / total_count if total_count > 0 else 0
			
			exp_stats = {
				'experiment': exp,
				'fail_count': fail_count,
				'pass_count': pass_count,
				'total_count': total_count,
				'fail_rate': fail_rate
			}
			
			print(f"[CONFIG] DEBUG: ExperimentTracker - {exp.get('node_name')}: Result={final_result}, Port={output_port}, Fails={fail_count}/{total_count} ({fail_rate:.1%})")
			
			# Prioritize solid repro (all fails or SOLID_REPRO result)
			if (final_result == 'SOLID_REPRO' or 
				output_port == 1 or  # Port 1 typically means solid repro found
				(fail_rate >= 0.9 and total_count >= 3)):  # 90%+ fail rate with sufficient data
				solid_repro_experiments.append(exp_stats)
				print(f"[CONFIG] DEBUG: ExperimentTracker - Classified as SOLID REPRO: {exp.get('node_name')}")
			else:
				flaky_experiments.append(exp_stats)
				print(f"[CONFIG] DEBUG: ExperimentTracker - Classified as FLAKY/UNSTABLE: {exp.get('node_name')}")
		
		# Selection logic: prioritize solid repro, then highest fail rate
		if solid_repro_experiments:
			print("[CONFIG] DEBUG: ExperimentTracker - Found solid repro experiments, selecting best one...")
			# Among solid repro experiments, select the one with most failures (most data)
			best_solid = max(solid_repro_experiments, key=lambda x: x['fail_count'])
			selected = best_solid['experiment']
			print(f"[CONFIG] DEBUG: ExperimentTracker - Selected solid repro: {selected.get('node_name')} ({best_solid['fail_count']} failures)")
			return selected
		
		elif flaky_experiments:
			print("[CONFIG] DEBUG: ExperimentTracker - No solid repro found, selecting highest fail rate from flaky experiments...")
			# Among flaky experiments, select the one with highest fail rate, then most failures
			best_flaky = max(flaky_experiments, key=lambda x: (x['fail_rate'], x['fail_count']))
			selected = best_flaky['experiment']
			print(f"[CONFIG] DEBUG: ExperimentTracker - Selected flaky with highest fail rate: {selected.get('node_name')} ({best_flaky['fail_rate']:.1%} fail rate)")
			return selected
		
		else:
			print("[CONFIG] DEBUG: ExperimentTracker - No suitable experiments found, using most recent...")
			# Fallback to most recent
			return experiments[-1]

	def _get_selection_reason(self, selected_experiment, all_experiments):
		"""Get the reason why this experiment was selected"""
		final_result = selected_experiment.get('final_result', '')
		output_port = selected_experiment.get('output_port', '')
		iterations = selected_experiment.get('iterations', [])
		
		fail_count = len([it for it in iterations if it['status'] == 'FAIL'])
		total_count = len(iterations)
		fail_rate = fail_count / total_count if total_count > 0 else 0
		
		if final_result == 'SOLID_REPRO' or output_port == 1 or fail_rate >= 0.9:
			return f"Selected for solid repro condition ({fail_count}/{total_count} failures, {fail_rate:.1%} fail rate)"
		else:
			return f"Selected for highest fail rate among flaky experiments ({fail_count}/{total_count} failures, {fail_rate:.1%} fail rate)"

	def _extract_voltage_type_context(self, experiment):
		"""Extract voltage type context from experiment"""
		voltage_freq_analysis = experiment.get('voltage_frequency_analysis', {})
		return voltage_freq_analysis.get('voltage_type_used', 'vbump')

	def _extract_adaptive_config(self, experiment):
		"""Extract configuration for adaptive flow with ALL fields from selected experiment"""
		iterations = experiment.get('iterations', [])
		if not iterations:
			return self._get_default_config()
		
		print("[CONFIG] DEBUG: ExperimentTracker - Extracting adaptive config from selected experiment...")
		
		# Get the experiment configuration (base config)
		base_experiment_config = experiment.get('experiment_config', {})
		
		# Get runtime configuration from iterations (actual values used)
		runtime_config = {}
		if iterations:
			# Use the first iteration's config snapshot for runtime values
			first_iteration = iterations[0]
			config_snapshot = first_iteration.get('config_snapshot', {})
			runtime_config = self._convert_config_to_experiment_format(config_snapshot)
		
		# Merge base config with runtime config (runtime takes precedence)
		adaptive_config = base_experiment_config.copy()
		adaptive_config.update(runtime_config)
		
		print("[CONFIG] DEBUG: ExperimentTracker - Base experiment config:")
		for key, value in base_experiment_config.items():
			if value is not None:
				print(f"[CONFIG] DEBUG:   {key}: {value}")
		
		print("[CONFIG] DEBUG: ExperimentTracker - Runtime config from iterations:")
		for key, value in runtime_config.items():
			if value is not None:
				print(f"[CONFIG] DEBUG:   {key}: {value}")
		
		print("[CONFIG] DEBUG: ExperimentTracker - FINAL adaptive config (ALL fields):")
		for key, value in adaptive_config.items():
			if value is not None:
				print(f"[CONFIG] DEBUG:   {key}: {value}")
		
		return adaptive_config

	def _convert_config_to_experiment_format(self, config_snapshot):
		"""Convert config snapshot to proper experiment dictionary format"""
		experiment_config = {}
		
		# Map configuration values to experiment dictionary keys
		if config_snapshot.get('voltage_ia') is not None:
			experiment_config['Voltage IA'] = config_snapshot['voltage_ia']
		
		if config_snapshot.get('voltage_cfc') is not None:
			experiment_config['Voltage CFC'] = config_snapshot['voltage_cfc']
		
		if config_snapshot.get('frequency_ia') is not None:
			experiment_config['Frequency IA'] = config_snapshot['frequency_ia']
		
		if config_snapshot.get('frequency_cfc') is not None:
			experiment_config['Frequency CFC'] = config_snapshot['frequency_cfc']
		
		if config_snapshot.get('content') is not None:
			experiment_config['Content'] = config_snapshot['content']
		
		if config_snapshot.get('mask') is not None:
			experiment_config['Configuration (Mask)'] = config_snapshot['mask']
		
		if config_snapshot.get('check_core') is not None:
			experiment_config['Check Core'] = config_snapshot['check_core']
		
		if config_snapshot.get('voltage_type') is not None:
			experiment_config['Voltage Type'] = config_snapshot['voltage_type']
		
		return experiment_config
		
	def _apply_sweep_recovery_logic(self, base_config, sweep_analysis):
		"""Apply sweep-based recovery logic to configuration"""
		sensitivity = sweep_analysis.get('sensitivity_analysis', {})
		pattern = sensitivity.get('pattern')
		
		if pattern == 'threshold_sensitivity':
			# Use safe values above threshold
			pass_range = sensitivity.get('pass_range', [])
			if pass_range:
				safe_value = min(pass_range)
				sweep_type = sweep_analysis['sweep_type']
				sweep_domain = sweep_analysis['sweep_domain']
				
				if sweep_type == 'voltage':
					if sweep_domain == 'ia':
						base_config['voltage_ia'] = safe_value
					elif sweep_domain == 'cfc':
						base_config['voltage_cfc'] = safe_value
				elif sweep_type == 'frequency':
					if sweep_domain == 'ia':
						base_config['frequency_ia'] = safe_value
					elif sweep_domain == 'cfc':
						base_config['frequency_cfc'] = safe_value
		
		return base_config


	def _get_sweep_insights_for_adaptive(self, experiment):
		"""Get sweep insights for adaptive configuration"""
		sweep_analysis = experiment.get('sweep_analysis')
		if not sweep_analysis:
			return None
		
		return {
			'sweep_type': sweep_analysis['sweep_type'],
			'sweep_domain': sweep_analysis['sweep_domain'],
			'sensitivity_pattern': sweep_analysis['sensitivity_analysis']['pattern'],
			'recommendation': sweep_analysis['sensitivity_analysis']['recommendation'],
			'safe_values': sweep_analysis['sensitivity_analysis'].get('pass_range', [])
		}
	
	def _assess_recovery_potential(self, experiment):
		"""Assess recovery potential based on experiment results"""
		iterations = experiment.get('iterations', [])
		if not iterations:
			return 'unknown'
		
		pass_count = len([it for it in iterations if it['status'] == 'PASS'])
		total_count = len(iterations)
		pass_rate = pass_count / total_count if total_count > 0 else 0
		
		if pass_rate >= 0.5:
			return 'high'
		elif pass_rate >= 0.2:
			return 'medium'
		else:
			return 'low'

		
	def get_comprehensive_analysis_data(self):
		"""Get comprehensive analysis data for AnalysisFlowInstance with content analysis"""
		self.debugger.log("Starting comprehensive analysis", "ANALYSIS")
		
		try:
			# Filter out None experiments
			valid_experiments = [exp for exp in self.experiments_history if exp is not None]
			content_analysis = self._generate_content_analysis()
			comprehensive_data = {
				'flow_summary': self.flow_summary,
				'total_experiments': len(valid_experiments),
				'detailed_experiments': valid_experiments,
				'voltage_frequency_analysis': self._generate_comprehensive_vf_analysis(),
				'unit_characterization': self._generate_unit_characterization(),
				'recovery_analysis': self._generate_recovery_analysis(),
				'failure_analysis': self._generate_failure_analysis(),
				'sweep_summary': self._generate_sweep_summary(),
				'content_analysis': content_analysis,  # Add content analysis
				'recommendations': self._generate_comprehensive_recommendations() + self._generate_content_recommendations(content_analysis)
			}
			
			self.debugger.log_comprehensive_analysis(comprehensive_data)
			return comprehensive_data
			
		except Exception as e:
			self.debugger.log_error(f"Error in comprehensive analysis", e)
			
			# Return safe fallback data
			return {
				'flow_summary': self.flow_summary or {},
				'total_experiments': len([exp for exp in self.experiments_history if exp is not None]),
				'detailed_experiments': [exp for exp in self.experiments_history if exp is not None],
				'voltage_frequency_analysis': {'status': 'error', 'message': str(e)},
				'unit_characterization': {'status': 'error', 'message': str(e)},
				'recovery_analysis': {'status': 'error', 'message': str(e)},
				'failure_analysis': {'status': 'error', 'message': str(e)},
				'sweep_summary': {'status': 'error', 'message': str(e)},
				'content_analysis': {'status': 'error', 'message': str(e)},
				'recommendations': [],
				'error': str(e)
			}
	
	def _safe_get_experiments_by_sweep_type(self, sweep_type):
		"""Safely get experiments by sweep type with null checking"""
		valid_experiments = []
		
		for exp in self.experiments_history:
			if exp is None:
				continue
				
			sweep_data = exp.get('sweep_data')
			if sweep_data is None:
				continue
				
			if sweep_data.get('sweep_type') == sweep_type:
				valid_experiments.append(exp)
		
		return valid_experiments

	def _generate_comprehensive_vf_analysis(self):
		"""Generate comprehensive voltage/frequency analysis with case-insensitive detection"""
		try:
			print("[DEBUG] DEBUG: AnalysisFlowInstance - Starting VF analysis...")
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Total experiments to analyze: {len(self.experiments_history)}")
			
			voltage_experiments = []
			frequency_experiments = []
			
			for i, exp in enumerate(self.experiments_history):
				if exp is None:
					print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Experiment {i}: None")
					continue
					
				node_name = exp.get('node_name', 'Unknown')
				sweep_data = exp.get('sweep_data')
				
				print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Experiment {i}: {node_name}")
				print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Sweep data: {sweep_data}")
				
				if sweep_data is not None:
					sweep_type = sweep_data.get('sweep_type', '').lower()  # Convert to lowercase
					print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Sweep type (normalized): {sweep_type}")
					
					if sweep_type == 'voltage':
						voltage_experiments.append(exp)
						print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Added to voltage experiments")
					elif sweep_type == 'frequency':
						frequency_experiments.append(exp)
						print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Added to frequency experiments")
					else:
						print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Unknown sweep type: {sweep_type}")
				else:
					print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   No sweep data")
			
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Found {len(voltage_experiments)} voltage experiments")
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Found {len(frequency_experiments)} frequency experiments")
			
			# Rest of the method remains the same...
			analysis = {
				'voltage_sensitivity': self._analyze_voltage_sensitivity(voltage_experiments),
				'frequency_sensitivity': self._analyze_frequency_sensitivity(frequency_experiments),
				'combined_analysis': self._analyze_combined_sensitivity(voltage_experiments, frequency_experiments),
				'debug_info': {
					'total_experiments_checked': len(self.experiments_history),
					'voltage_experiments_found': len(voltage_experiments),
					'frequency_experiments_found': len(frequency_experiments),
					'voltage_experiment_names': [exp.get('node_name') for exp in voltage_experiments],
					'frequency_experiment_names': [exp.get('node_name') for exp in frequency_experiments]
				}
			}
			
			print("[DEBUG] DEBUG: AnalysisFlowInstance - VF analysis complete")
			return analysis
			
		except Exception as e:
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Error in VF analysis: {e}")
			self.debugger.log_error(f"Error in VF analysis", e)
			return {
				'voltage_sensitivity': {'status': 'error', 'message': str(e)},
				'frequency_sensitivity': {'status': 'error', 'message': str(e)},
				'combined_analysis': {'status': 'error', 'message': str(e)}
			}

	def _analyze_voltage_sensitivity(self, voltage_experiments):
		"""Analyze voltage sensitivity with enhanced debugging"""
		print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Analyzing {len(voltage_experiments)} voltage experiments")
		
		if not voltage_experiments:
			print("[DEBUG] DEBUG: AnalysisFlowInstance - No voltage experiments to analyze")
			return {'status': 'no_data', 'conclusion': 'No voltage sweep data available'}
		
		try:
			ia_sensitivity = []
			cfc_sensitivity = []
			
			for exp in voltage_experiments:
				if exp is None:
					continue
					
				node_name = exp.get('node_name', 'Unknown')
				sweep_analysis = exp.get('sweep_analysis')
				sweep_data = exp.get('sweep_data')
				
				print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Processing voltage experiment: {node_name}")
				print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Sweep data: {sweep_data}")
				print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Sweep analysis: {sweep_analysis is not None}")
				
				if sweep_data is None:
					print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   No sweep data, skipping")
					continue
					
				sweep_domain = sweep_data.get('sweep_domain')  # Check sweep_data first
				if not sweep_domain and sweep_analysis:
					sweep_domain = sweep_analysis.get('sweep_domain')  # Fallback to sweep_analysis
				
				print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Sweep domain: {sweep_domain}")
				
				if sweep_domain == 'ia':
					if sweep_analysis:
						ia_sensitivity.append(sweep_analysis)
						print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Added to IA voltage sensitivity")
					else:
						print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   No sweep analysis for IA experiment")
				elif sweep_domain == 'cfc':
					if sweep_analysis:
						cfc_sensitivity.append(sweep_analysis)
						print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Added to CFC voltage sensitivity")
					else:
						print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   No sweep analysis for CFC experiment")
				else:
					print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Unknown or missing sweep domain: {sweep_domain}")
			
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - IA voltage sensitivity data: {len(ia_sensitivity)} experiments")
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - CFC voltage sensitivity data: {len(cfc_sensitivity)} experiments")
			
			return {
				'status': 'analyzed',
				'ia_voltage_sensitivity': self._summarize_domain_sensitivity(ia_sensitivity),
				'cfc_voltage_sensitivity': self._summarize_domain_sensitivity(cfc_sensitivity),
				'overall_voltage_conclusion': self._determine_overall_voltage_sensitivity(ia_sensitivity, cfc_sensitivity),
				'debug_info': {
					'total_voltage_experiments': len(voltage_experiments),
					'ia_experiments': len(ia_sensitivity),
					'cfc_experiments': len(cfc_sensitivity)
				}
			}
			
		except Exception as e:
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Error in voltage sensitivity analysis: {e}")
			return {'status': 'error', 'conclusion': f'Error analyzing voltage sensitivity: {str(e)}'}

	def _analyze_frequency_sensitivity(self, frequency_experiments):
		"""Analyze frequency sensitivity with enhanced debugging"""
		print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Analyzing {len(frequency_experiments)} frequency experiments")
		
		if not frequency_experiments:
			print("[DEBUG] DEBUG: AnalysisFlowInstance - No frequency experiments to analyze")
			return {'status': 'no_data', 'conclusion': 'No frequency sweep data available'}
		
		try:
			ia_sensitivity = []
			cfc_sensitivity = []
			
			for exp in frequency_experiments:
				if exp is None:
					continue
					
				node_name = exp.get('node_name', 'Unknown')
				sweep_analysis = exp.get('sweep_analysis')
				sweep_data = exp.get('sweep_data')
				
				print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Processing frequency experiment: {node_name}")
				print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Sweep data: {sweep_data}")
				print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Sweep analysis: {sweep_analysis is not None}")
				
				if sweep_data is None:
					print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   No sweep data, skipping")
					continue
					
				sweep_domain = sweep_data.get('sweep_domain')  # Check sweep_data first
				if not sweep_domain and sweep_analysis:
					sweep_domain = sweep_analysis.get('sweep_domain')  # Fallback to sweep_analysis
				
				print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Sweep domain: {sweep_domain}")
				
				if sweep_domain == 'ia':
					if sweep_analysis:
						ia_sensitivity.append(sweep_analysis)
						print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Added to IA frequency sensitivity")
					else:
						print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   No sweep analysis for IA experiment")
				elif sweep_domain == 'cfc':
					if sweep_analysis:
						cfc_sensitivity.append(sweep_analysis)
						print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Added to CFC frequency sensitivity")
					else:
						print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   No sweep analysis for CFC experiment")
				else:
					print(f"[DEBUG] DEBUG: AnalysisFlowInstance -   Unknown or missing sweep domain: {sweep_domain}")
			
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - IA frequency sensitivity data: {len(ia_sensitivity)} experiments")
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - CFC frequency sensitivity data: {len(cfc_sensitivity)} experiments")
			
			return {
				'status': 'analyzed',
				'ia_frequency_sensitivity': self._summarize_domain_sensitivity(ia_sensitivity),
				'cfc_frequency_sensitivity': self._summarize_domain_sensitivity(cfc_sensitivity),
				'overall_frequency_conclusion': self._determine_overall_frequency_sensitivity(ia_sensitivity, cfc_sensitivity),
				'debug_info': {
					'total_frequency_experiments': len(frequency_experiments),
					'ia_experiments': len(ia_sensitivity),
					'cfc_experiments': len(cfc_sensitivity)
				}
			}
			
		except Exception as e:
			print(f"[DEBUG] DEBUG: AnalysisFlowInstance - Error in frequency sensitivity analysis: {e}")
			return {'status': 'error', 'conclusion': f'Error analyzing frequency sensitivity: {str(e)}'}

	def _summarize_domain_sensitivity(self, sensitivity_data):
		"""Summarize sensitivity for a specific domain with enhanced pattern analysis"""
		if not sensitivity_data:
			return {'status': 'no_data'}
		
		try:
			# Filter out None entries and extract patterns safely
			valid_data = [s for s in sensitivity_data if s is not None]
			patterns = []
			recovery_found = []
			
			for s in valid_data:
				sensitivity_analysis = s.get('sensitivity_analysis')
				if sensitivity_analysis is not None:
					pattern = sensitivity_analysis.get('pattern')
					if pattern is not None:
						patterns.append(pattern)
						
						# Check if recovery conditions were found
						safe_values = sensitivity_analysis.get('safe_values', [])
						has_recovery = len(safe_values) > 0 or pattern in ['threshold_sensitivity', 'upper_threshold_sensitivity', 'mixed_sensitivity']
						recovery_found.append(has_recovery)
			
			if not patterns:
				return {'status': 'no_pattern_data'}
			
			most_common_pattern = max(set(patterns), key=patterns.count)
			recovery_experiments = sum(recovery_found)
			
			# Enhanced conclusion based on recovery potential
			base_conclusion = self._interpret_sensitivity_pattern(most_common_pattern)
			if most_common_pattern == 'no_sensitivity':
				no_recovery_count = patterns.count('no_sensitivity')
				if no_recovery_count == len(patterns):
					enhanced_conclusion = f"{base_conclusion} - No recovery conditions found in any experiment"
				else:
					enhanced_conclusion = f"{base_conclusion} - Mixed results with some recovery potential"
			else:
				enhanced_conclusion = f"{base_conclusion} - Recovery conditions found in {recovery_experiments}/{len(valid_data)} experiments"
			
			return {
				'status': 'analyzed',
				'experiments_count': len(valid_data),
				'dominant_pattern': most_common_pattern,
				'all_patterns': patterns,
				'recovery_experiments': recovery_experiments,
				'conclusion': enhanced_conclusion
			}
			
		except Exception as e:
			return {'status': 'error', 'message': str(e)}
		
	def _interpret_sensitivity_pattern(self, pattern):
		"""Interpret sensitivity pattern into human-readable conclusion"""
		interpretations = {
			'no_sensitivity': 'Unit shows no sensitivity - either stable across range or fails completely with no recovery',
			'threshold_sensitivity': 'Unit has a clear sensitivity threshold - recovers above threshold',
			'upper_threshold_sensitivity': 'Unit is sensitive at higher values - recovers below threshold', 
			'complete_sensitivity': 'Unit is highly sensitive across entire range',
			'mixed_sensitivity': 'Unit shows inconsistent sensitivity pattern with some recovery points'
		}
		return interpretations.get(pattern, 'Unknown sensitivity pattern')
	
	def _determine_overall_voltage_sensitivity(self, ia_data, cfc_data):
		"""Determine overall voltage sensitivity conclusion"""
		if not ia_data and not cfc_data:
			return 'No voltage sensitivity data available'
		
		conclusions = []
		if ia_data:
			ia_summary = self._summarize_domain_sensitivity(ia_data)
			conclusions.append(f"IA voltage: {ia_summary['conclusion']}")
		
		if cfc_data:
			cfc_summary = self._summarize_domain_sensitivity(cfc_data)
			conclusions.append(f"CFC voltage: {cfc_summary['conclusion']}")
		
		return '; '.join(conclusions)
	
	def _determine_overall_frequency_sensitivity(self, ia_data, cfc_data):
		"""Determine overall frequency sensitivity conclusion"""
		if not ia_data and not cfc_data:
			return 'No frequency sensitivity data available'
		
		conclusions = []
		if ia_data:
			ia_summary = self._summarize_domain_sensitivity(ia_data)
			conclusions.append(f"IA frequency: {ia_summary['conclusion']}")
		
		if cfc_data:
			cfc_summary = self._summarize_domain_sensitivity(cfc_data)
			conclusions.append(f"CFC frequency: {cfc_summary['conclusion']}")
		
		return '; '.join(conclusions)
	
	def _analyze_combined_sensitivity(self, voltage_experiments, frequency_experiments):
		"""Analyze combined voltage and frequency sensitivity"""
		has_voltage_sensitivity = any(
			exp.get('sweep_analysis', {}).get('failure_points', 0) > 0 
			for exp in voltage_experiments
		)
		
		has_frequency_sensitivity = any(
			exp.get('sweep_analysis', {}).get('failure_points', 0) > 0 
			for exp in frequency_experiments
		)
		
		if has_voltage_sensitivity and has_frequency_sensitivity:
			conclusion = 'Unit is sensitive to both voltage and frequency'
		elif has_voltage_sensitivity:
			conclusion = 'Unit is primarily voltage sensitive'
		elif has_frequency_sensitivity:
			conclusion = 'Unit is primarily frequency sensitive'
		else:
			conclusion = 'Unit shows minimal voltage/frequency sensitivity'
		
		return {
			'voltage_sensitive': has_voltage_sensitivity,
			'frequency_sensitive': has_frequency_sensitivity,
			'conclusion': conclusion
		}
	
	def _generate_unit_characterization(self):
		"""Generate overall unit characterization"""
		total_experiments = len(self.experiments_history)
		recovery_experiments = len(self.flow_summary['recovery_conditions'])
		failure_experiments = len(self.flow_summary['failure_conditions'])
		
		characterization = {
			'total_experiments_run': total_experiments,
			'recovery_conditions_found': recovery_experiments,
			'failure_conditions_found': failure_experiments,
			'unit_stability': self._assess_unit_stability(),
			'dominant_failure_patterns': self._get_dominant_failure_patterns(),
			'recommended_operating_conditions': self._get_recommended_operating_conditions()
		}
		
		print("[DEBUG] DEBUG: AnalysisFlowInstance - Unit Characterization Complete")
		return characterization
	
	def _assess_unit_stability(self):
		"""Assess overall unit stability"""
		recovery_rate = len(self.flow_summary['recovery_conditions']) / len(self.experiments_history) if self.experiments_history else 0
		
		if recovery_rate >= 0.7:
			return 'stable'
		elif recovery_rate >= 0.4:
			return 'moderately_stable'
		else:
			return 'unstable'
	
	def _get_dominant_failure_patterns(self):
		"""Get dominant failure patterns across all experiments"""
		all_patterns = {}
		
		for exp in self.experiments_history:
			patterns = exp.get('failure_patterns', {})
			for pattern_key, pattern_data in patterns.items():
				if pattern_key not in all_patterns:
					all_patterns[pattern_key] = 0
				all_patterns[pattern_key] += pattern_data['count']
		
		# Sort by frequency and return top 3
		sorted_patterns = sorted(all_patterns.items(), key=lambda x: x[1], reverse=True)
		return sorted_patterns[:3]
	
	def _get_recommended_operating_conditions(self):
		"""Get recommended operating conditions based on all data"""
		recommendations = {}
		
		# Analyze recovery conditions for best settings
		recovery_conditions = self.flow_summary['recovery_conditions']
		if recovery_conditions:
			best_recovery = max(recovery_conditions, key=lambda x: x['pass_rate'])
			recommendations = best_recovery['config'].copy()
		
		return recommendations
	
	def _generate_recovery_analysis(self):
		"""Generate detailed recovery analysis"""
		recovery_conditions = self.flow_summary['recovery_conditions']
		
		if not recovery_conditions:
			return {'status': 'no_recovery_found'}
		
		result = {
			'status': 'recovery_found',
			'total_recovery_conditions': len(recovery_conditions),
			'best_recovery_condition': max(recovery_conditions, key=lambda x: x['pass_rate']),
			'recovery_success_rate': sum(rc['pass_rate'] for rc in recovery_conditions) / len(recovery_conditions),
			'recovery_patterns': self._analyze_recovery_patterns(recovery_conditions)
		}

		print("[DEBUG] DEBUG: AnalysisFlowInstance - Recommend Operating Conditions Complete")
		return result
	
	def _analyze_recovery_patterns(self, recovery_conditions):
		"""Analyze patterns in recovery conditions"""
		voltage_recoveries = []
		frequency_recoveries = []
		content_recoveries = []
		
		for condition in recovery_conditions:
			config = condition['config']
			if config.get('voltage_ia') or config.get('voltage_cfc'):
				voltage_recoveries.append(condition)
			if config.get('frequency_ia') or config.get('frequency_cfc'):
				frequency_recoveries.append(condition)
			if config.get('content'):
				content_recoveries.append(condition)
		
		return {
			'voltage_based_recoveries': len(voltage_recoveries),
			'frequency_based_recoveries': len(frequency_recoveries),
			'content_based_recoveries': len(content_recoveries)
		}
	
	def _generate_failure_analysis(self):
		"""Generate detailed failure analysis"""
		failure_conditions = self.flow_summary['failure_conditions']
		
		if not failure_conditions:
			return {'status': 'no_failures_found'}
		
		result = {
			'status': 'failures_analyzed',
			'total_failure_conditions': len(failure_conditions),
			'failure_distribution': self._analyze_failure_distribution(failure_conditions),
			'common_failure_patterns': self._get_common_failure_patterns(failure_conditions)
		}
		print("[DEBUG] DEBUG: AnalysisFlowInstance - Failure Analysis Complete")

		return result
	
	def _analyze_failure_distribution(self, failure_conditions):
		"""Analyze distribution of failure conditions"""
		node_types = {}
		for condition in failure_conditions:
			node_name = condition['node_name']
			if node_name not in node_types:
				node_types[node_name] = 0
			node_types[node_name] += 1
		
		return node_types
	
	def _get_common_failure_patterns(self, failure_conditions):
		"""Get common failure patterns across all failure conditions"""
		all_patterns = {}
		
		for condition in failure_conditions:
			patterns = condition.get('failure_patterns', {})
			for pattern_key, pattern_data in patterns.items():
				if pattern_key not in all_patterns:
					all_patterns[pattern_key] = 0
				all_patterns[pattern_key] += pattern_data['count']
		
		# Return top 5 patterns
		sorted_patterns = sorted(all_patterns.items(), key=lambda x: x[1], reverse=True)
		return sorted_patterns[:5]
	
	def _generate_sweep_summary(self):
		"""Generate summary of all sweep experiments"""
		sweep_experiments = [exp for exp in self.experiments_history if exp.get('sweep_data')]
		
		if not sweep_experiments:
			return {'status': 'no_sweep_data'}
		
		voltage_sweeps = [exp for exp in sweep_experiments if exp['sweep_data']['sweep_type'] == 'voltage']
		frequency_sweeps = [exp for exp in sweep_experiments if exp['sweep_data']['sweep_type'] == 'frequency']
		
		result = {
			'status': 'sweep_data_available',
			'total_sweep_experiments': len(sweep_experiments),
			'voltage_sweeps': len(voltage_sweeps),
			'frequency_sweeps': len(frequency_sweeps),
			'sweep_insights': self._generate_sweep_insights(sweep_experiments)
		}

		print("[DEBUG] DEBUG: AnalysisFlowInstance - Sweep Summary Complete")

		return result
	
	def _generate_sweep_insights(self, sweep_experiments):
		"""Generate insights from sweep experiments"""
		insights = []
		
		for exp in sweep_experiments:
			sweep_analysis = exp.get('sweep_analysis', {})
			if sweep_analysis:
				insight = {
					'node_name': exp['node_name'],
					'sweep_type': sweep_analysis['sweep_type'],
					'sweep_domain': sweep_analysis['sweep_domain'],
					'sensitivity_pattern': sweep_analysis['sensitivity_analysis']['pattern'],
					'recommendation': sweep_analysis['sensitivity_analysis']['recommendation']
				}
				insights.append(insight)
		
		return insights
	
	def _generate_comprehensive_recommendations(self):
		"""Generate comprehensive recommendations for next steps"""
		recommendations = []
		
		# Recovery-based recommendations
		recovery_analysis = self._generate_recovery_analysis()
		if recovery_analysis.get('status') == 'recovery_found':
			best_recovery = recovery_analysis['best_recovery_condition']
			recommendations.append({
				'type': 'recovery_validation',
				'priority': 'high',
				'description': f"Validate recovery condition from {best_recovery['node_name']} with {best_recovery['pass_rate']:.1f}% pass rate",
				'suggested_config': best_recovery['config']
			})
		
		# Sweep-based recommendations
		vf_analysis = self._generate_comprehensive_vf_analysis()
		if vf_analysis['voltage_sensitivity']['status'] == 'analyzed':
			recommendations.append({
				'type': 'voltage_characterization',
				'priority': 'medium',
				'description': f"Voltage analysis: {vf_analysis['combined_analysis']['conclusion']}",
				'details': vf_analysis['voltage_sensitivity']
			})
		
		if vf_analysis['frequency_sensitivity']['status'] == 'analyzed':
			recommendations.append({
				'type': 'frequency_characterization',
				'priority': 'medium',
				'description': f"Frequency analysis: {vf_analysis['combined_analysis']['conclusion']}",
				'details': vf_analysis['frequency_sensitivity']
			})
		
		print("[DEBUG] DEBUG: AnalysisFlowInstance - Comprehensive recommendations complete")
		return recommendations

	def _get_default_config(self):
		"""Get default configuration when no data is available in experiment format"""
		return {
			'Voltage IA': None,
			'Voltage CFC': None,
			'Frequency IA': None,
			'Frequency CFC': None,
			'Content': None,
			'Configuration (Mask)': None,
			'Check Core': None,
			'Voltage Type': 'vbump'
		}
	
	def set_framework_api_reference(self, framework_api):
		"""Set framework API reference for extracting test folder and summary info"""
		self._framework_api = framework_api
								
	def _analyze_experiment_patterns(self):
		"""Analyze experiment for failure/recovery patterns"""
		iterations = self.current_experiment_data.get('iterations', [])
		if not iterations:
			return
			
		# Analyze failure patterns
		failures = [it for it in iterations if it['status'] == 'FAIL']
		passes = [it for it in iterations if it['status'] == 'PASS']
		
		# Extract failure patterns
		failure_patterns = {}
		for failure in failures:
			pattern_key = f"{failure['scratchpad']}_{failure['seed']}"
			if pattern_key not in failure_patterns:
				failure_patterns[pattern_key] = {
					'count': 0,
					'config': failure['config_snapshot'],
					'iterations': []
				}
			failure_patterns[pattern_key]['count'] += 1
			failure_patterns[pattern_key]['iterations'].append(failure['iteration'])
		
		self.current_experiment_data['failure_patterns'] = failure_patterns
		
		# Determine if this was a recovery condition
		pass_rate = len(passes) / len(iterations) if iterations else 0
		if pass_rate >= 0.8:  # 80% or higher pass rate
			self.current_experiment_data['recovery_indicators'].append({
				'type': 'high_pass_rate',
				'value': pass_rate,
				'config': iterations[0]['config_snapshot'] if iterations else {}
			})

	def _update_flow_summary(self):
		"""Update overall flow summary"""
		exp = self.current_experiment_data
		
		self.flow_summary['total_nodes_executed'] += 1
		self.flow_summary['test_folders'].append(exp.get('test_folder'))
		
		# Track recovery conditions (high pass rate experiments)
		if exp.get('recovery_indicators'):
			self.flow_summary['recovery_conditions'].append({
				'node_name': exp['node_name'],
				'config': exp['iterations'][0]['config_snapshot'] if exp['iterations'] else {},
				'pass_rate': len([it for it in exp['iterations'] if it['status'] == 'PASS']) / len(exp['iterations']) if exp['iterations'] else 0
			})
		
		# Track failure conditions (experiments that found solid repro)
		if exp.get('output_port') == 1 and exp['node_type'] in ['AllFailFlowInstance', 'SingleFailFlowInstance']:
			self.flow_summary['failure_conditions'].append({
				'node_name': exp['node_name'],
				'config': exp['iterations'][0]['config_snapshot'] if exp['iterations'] else {},
				'failure_patterns': exp.get('failure_patterns', {})
			})
				
	def _persist_to_ini(self):
		"""Persist experiment data to INI file using Test Name as section keys"""
		if not self.flow_config_path:
			return
			
		try:
			config = configparser.ConfigParser()
			
			if os.path.exists(self.flow_config_path):
				config.read(self.flow_config_path)
			
			def safe_str(value):
				if value is None:
					return ''
				elif isinstance(value, datetime):
					return value.isoformat()
				elif isinstance(value, bool):
					return 'True' if value else 'False'
				elif isinstance(value, (list, dict)):
					return json.dumps(value, default=str, separators=(',', ':'))
				elif isinstance(value, float):
					return f"{value:.6f}"
				else:
					return str(value)
			
			# Get the Test Name to use as section key (fallback to node name if no Test Name)
			experiment_config = self.current_experiment_data.get('experiment_config', {})
			test_name = experiment_config.get('Test Name') or self.current_experiment_data.get('node_name', 'Unknown_Test')
			
			print(f"[CONFIG] DEBUG: ExperimentTracker - Using Test Name as INI section: {test_name}")
			
			# Ensure the section exists
			if test_name not in config:
				config.add_section(test_name)
				if hasattr(self, 'debugger') and self.debugger.enabled:
					self.debugger.log(f"Created new section for test: {test_name}", "INFO")
			
			# Calculate statistics
			iterations = self.current_experiment_data.get('iterations', [])
			pass_count = len([it for it in iterations if it['status'] == 'PASS'])
			fail_count = len([it for it in iterations if it['status'] == 'FAIL'])
			other_count = len(iterations) - pass_count - fail_count
			
			# Determine execution status
			execution_status = self._determine_execution_status()
			
			# Add experiment data to the test's section
			config[test_name].update({
				# Execution Status
				'executed': 'True',
				'execution_status': execution_status,
				'node_name': safe_str(self.current_experiment_data.get('node_name', '')),  # Keep node name for reference
				'node_type': safe_str(self.current_experiment_data.get('node_type', '')),
				'node_id': safe_str(self.current_experiment_data.get('node_id', '')),
				'execution_timestamp': safe_str(datetime.now()),
				
				# Timing
				'start_time': safe_str(self.current_experiment_data.get('start_time')),
				'end_time': safe_str(self.current_experiment_data.get('end_time')),
				'duration_seconds': safe_str(self._calculate_experiment_duration()),
				
				# Results
				'final_result': safe_str(self.current_experiment_data.get('final_result', '')),
				'output_port': safe_str(self.current_experiment_data.get('output_port', '')),
				
				# Statistics
				'total_iterations': safe_str(len(iterations)),
				'pass_count': safe_str(pass_count),
				'fail_count': safe_str(fail_count),
				'other_count': safe_str(other_count),
				'pass_rate_percent': safe_str(round(pass_count / len(iterations) * 100, 2) if iterations else 0),
				
				# File Paths
				'test_folder': safe_str(self.current_experiment_data.get('test_folder', '')),
				'summary_file': safe_str(self.current_experiment_data.get('summary_file_path', '')),
			})
			
			# Add key experiment configuration
			key_config_params = [
				'Test Type', 'Content', 'Voltage IA', 'Voltage CFC', 'Frequency IA', 'Frequency CFC',
				'Voltage Type', 'Configuration (Mask)', 'Check Core', 'Type', 'Domain', 'Start', 'End', 'Steps', 'Loops'
			]
			
			for param in key_config_params:
				if param in experiment_config and experiment_config[param] is not None:
					clean_key = f"config_{param.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_').lower()}"
					config[test_name][clean_key] = safe_str(experiment_config[param])
			
			# Add sweep data if available
			sweep_data = self.current_experiment_data.get('sweep_data')
			if sweep_data:
				config[test_name].update({
					'sweep_type': safe_str(sweep_data.get('sweep_type', '')),
					'sweep_domain': safe_str(sweep_data.get('sweep_domain', '')),
					'sweep_start_value': safe_str(sweep_data.get('start_value', '')),
					'sweep_end_value': safe_str(sweep_data.get('end_value', '')),
					'sweep_step_value': safe_str(sweep_data.get('step_value', '')),
					'sweep_voltage_type': safe_str(sweep_data.get('voltage_type', '')),
				})
				
				# Add sweep analysis if available
				sweep_analysis = self.current_experiment_data.get('sweep_analysis')
				if sweep_analysis:
					sensitivity = sweep_analysis.get('sensitivity_analysis', {})
					config[test_name].update({
						'sweep_total_points': safe_str(sweep_analysis.get('total_points', 0)),
						'sweep_failure_points': safe_str(sweep_analysis.get('failure_points', 0)),
						'sweep_pass_points': safe_str(sweep_analysis.get('pass_points', 0)),
						'sweep_sensitivity_pattern': safe_str(sensitivity.get('pattern', '')),
						'sweep_sensitivity_description': safe_str(sensitivity.get('description', '')),
						'sweep_recommendation': safe_str(sensitivity.get('recommendation', ''))
					})
			
			# Add summary information
			if pass_count > 0 and fail_count > 0:
				config[test_name]['result_summary'] = f"Mixed results: {pass_count} passes, {fail_count} fails"
			elif pass_count > 0:
				config[test_name]['result_summary'] = f"Stable: {pass_count} passes, no failures"
			elif fail_count > 0:
				config[test_name]['result_summary'] = f"Failing: {fail_count} failures, no passes"
			else:
				config[test_name]['result_summary'] = "No valid test results"
			
			# Update FLOW_SUMMARY section
			self._update_flow_summary_section(config)
			
			# Save to file
			with open(self.flow_config_path, 'w') as f:
				config.write(f)
				
			# Debug logging
			if hasattr(self, 'debugger') and self.debugger.enabled:
				self.debugger.log(f"Experiment data persisted to test section: {test_name}", "INFO")
				self.debugger.log(f"Node name: {self.current_experiment_data.get('node_name')}", "INFO")
				
		except Exception as e:
			error_msg = f"Error persisting experiment data: {e}"
			print(error_msg)
			
			if hasattr(self, 'debugger') and self.debugger.enabled:
				self.debugger.log_error(error_msg, e)

	def _determine_execution_status(self):
		"""Determine the execution status based on results"""
		final_result = self.current_experiment_data.get('final_result', '')
		output_port = self.current_experiment_data.get('output_port', '')
		
		if final_result == 'HARDWARE_FAILURE':
			return 'HARDWARE_FAILURE'
		elif final_result == 'STABLE':
			return 'COMPLETED_STABLE'
		elif final_result == 'SOLID_REPRO':
			return 'COMPLETED_REPRO_FOUND'
		elif final_result == 'INTERMITTENT':
			return 'COMPLETED_INTERMITTENT'
		elif output_port == '3':
			return 'HARDWARE_FAILURE'
		elif output_port in ['0', '1', '2']:
			return 'COMPLETED_SUCCESS'
		else:
			return 'COMPLETED_UNKNOWN'

	def _update_flow_summary_section(self, config):
		"""Update the FLOW_SUMMARY section"""
		if "FLOW_SUMMARY" not in config:
			config.add_section("FLOW_SUMMARY")
		
		# Count executed nodes
		executed_nodes = []
		for section_name in config.sections():
			if section_name != "FLOW_SUMMARY" and config.has_option(section_name, 'executed'):
				if config.get(section_name, 'executed') == 'True':
					executed_nodes.append(section_name)
		
		config["FLOW_SUMMARY"].update({
			'total_experiments': str(len(self.experiments_history)),
			'executed_nodes': str(len(executed_nodes)),
			'executed_node_list': ', '.join(executed_nodes),
			'total_nodes_executed': str(self.flow_summary.get('total_nodes_executed', 0)),
			'recovery_conditions_count': str(len(self.flow_summary.get('recovery_conditions', []))),
			'failure_conditions_count': str(len(self.flow_summary.get('failure_conditions', []))),
			'last_updated': datetime.now().isoformat(),
			'flow_start_time': str(self.flow_summary.get('start_time', '')),
		})

	def _calculate_experiment_duration(self):
		"""Calculate experiment duration in seconds"""
		try:
			start_time = self.current_experiment_data.get('start_time')
			end_time = self.current_experiment_data.get('end_time')
			
			if start_time and end_time:
				duration = end_time - start_time
				return int(duration.total_seconds())
			return 0
		except Exception:
			return 0
	 
	def get_previous_experiment_data(self, node_type=None):
		"""Get data from previous experiments for adaptive flows"""
		if node_type:
			return [exp for exp in self.experiments_history if exp['node_type'] == node_type]
		return self.experiments_history
	
	def generate_flow_summary_report(self):
		"""Generate comprehensive flow summary report"""
		return {
			'flow_summary': self.flow_summary,
			'experiments_executed': len(self.experiments_history),
			'recovery_conditions_found': len(self.flow_summary['recovery_conditions']),
			'failure_conditions_found': len(self.flow_summary['failure_conditions']),
			'test_folders': list(set(self.flow_summary['test_folders'])),
			'detailed_experiments': self.experiments_history
		}

	def debug_show_experiment_history(self):
		"""Debug method to show current experiment history"""
		print("[CONFIG] DEBUG: ExperimentTracker - EXPERIMENT HISTORY:")
		print("=" * 60)
		for i, exp in enumerate(self.experiments_history):
			if exp:
				print(f"  {i}: {exp.get('node_name', 'Unknown')} (Type: {exp.get('node_type', 'Unknown')}) - Port: {exp.get('output_port', 'Unknown')}")
			else:
				print(f"  {i}: None")
		print("=" * 60)	

	def debug_sweep_detection(self):
		"""Debug method to show sweep detection issues"""
		print("[INFO] DEBUG: Sweep Detection Analysis")
		print("=" * 60)
		
		for i, exp in enumerate(self.experiments_history):
			if exp is None:
				print(f"Experiment {i}: None")
				continue
				
			node_name = exp.get('node_name', 'Unknown')
			node_type = exp.get('node_type', 'Unknown')
			
			print(f"\nExperiment {i}: {node_name} ({node_type})")
			
			# Check experiment config
			exp_config = exp.get('experiment_config', {})
			test_type = exp_config.get('Test Type')
			sweep_type = exp_config.get('Type')
			domain = exp_config.get('Domain')
			
			print(f"  Experiment Config:")
			print(f"    Test Type: {test_type}")
			print(f"    Type: {sweep_type}")
			print(f"    Domain: {domain}")
			
			# Check sweep data
			sweep_data = exp.get('sweep_data')
			print(f"  Sweep Data: {sweep_data}")
			
			# Check sweep analysis
			sweep_analysis = exp.get('sweep_analysis')
			print(f"  Sweep Analysis: {sweep_analysis is not None}")
			
			if sweep_analysis:
				print(f"    Analysis Type: {sweep_analysis.get('sweep_type')}")
				print(f"    Analysis Domain: {sweep_analysis.get('sweep_domain')}")
		
		print("=" * 60)

