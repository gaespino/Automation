import time
from typing import List
from typing import Optional, Dict, Any, List, Callable
from .base_strategy import TestStrategy
from ..configurations.test_configurations import TestResult, TestConfiguration
from ..execution.result_processor import TestResultProcessor
from ..execution.test_executor import TestExecutor
from ..utils.misc_utils import print_separator_box, print_custom_separator

class ShmooTestStrategy(TestStrategy):
	"""Strategy for shmoo tests"""
	
	def __init__(self, x_config: Dict, y_config: Dict):
		self.x_config = x_config
		self.y_config = y_config
		self.x_values = self._generate_range(x_config)
		self.y_values = self._generate_range(y_config)

	def get_axis_values(self) -> tuple[List[float], List[float]]:
		"""Return the X and Y axis values for 2D shmoo plotting"""
		return self.x_values, self.y_values
	
	def _generate_range(self, config: Dict) -> List[float]:
		"""Generate range based on configuration"""
		ttype = config['Type']
		start = config['Start']
		end = config['End']
		step = config['Step']
		
		if ttype == 'frequency':
			return list(range(int(start), int(end) + int(step), int(step)))
		elif ttype == 'voltage':
			values = []
			current = start
			while current <= end + step/2:
				values.append(round(current, 5))
				current += step
			return values
	
	def execute(self, executor: TestExecutor, halt_controller=None) -> List[TestResult]:
		results = []
		iteration = 1
		total_tests = len(self.x_values) * len(self.y_values)
	
		# Set up callback for executor
		if halt_controller and hasattr(halt_controller, '_send_status_update'):
			executor._framework_callback = halt_controller._send_status_update
			
		# Initialize execution state
		if halt_controller:
			halt_controller._current_execution_state.update({
				'is_running': True,
				'total_iterations': total_tests,
				'iteration_results': [],
				'experiment_name': executor.config.name,
				'end_requested': False
			})
			
			# Store strategy type in config for status updates
			executor.config.strategy_type = 'Shmoo'
				
		for y_value in self.y_values:
			self._update_config_value(executor.config, self.y_config, y_value)

			for x_value in self.x_values:
				executor.config.tnumber = iteration
				self._update_config_value(executor.config, self.x_config, x_value)

				# Check for END command before starting iteration
				if halt_controller and halt_controller._check_end_experiment_request():
					executor.gdflog.log(f"Experiment ended by END command before iteration {i + 1}", 2)
					break

				# Send progress update
				if halt_controller:
					halt_controller._send_status_update('strategy_progress', {
						'strategy_type': 'Shmoo',
						'current_iteration': iteration,
						'total_iterations': total_tests,
						'progress_percent': round(iteration / total_tests * 100, 1),
						'test_name': executor.config.name,
						'experiment_name': getattr(executor.config, 'experiment_name', executor.config.name),
						'current_point': f"X={x_value}, Y={y_value}",
						'x_axis': f"{self.x_config['Domain']}={x_value}",
						'y_axis': f"{self.y_config['Domain']}={y_value}"
					})

				executor.gdflog.log(f'{print_separator_box(direction="down")}')	
				executor.gdflog.log(f'Running Shmoo iteration: {iteration}/{total_tests}')
				
				result = executor.execute_single_test()
				results.append(result)
				
				if result.status == "CANCELLED":
					return results
				elif result.status == "ExecutionFAIL":
					break
				elif result.status == "FAIL":
					executor.config.reset = True
				else:
					executor.config.reset = executor.config.resetonpass
			
				iteration += 1
				executor.gdflog.log(f'{print_separator_box(direction="up")}')


				# Check for END command after iteration completion (highest priority)
				if halt_controller and halt_controller._check_end_experiment_request():
					executor.gdflog.log(f"Experiment ended by END command after iteration {i + 1}", 2)
					halt_controller._send_status_update('experiment_ended_by_command', {
						'completed_iterations': iteration - 1,
						'total_iterations': total_tests,
						'reason': 'END command',
						'final_result': result.status,
						'experiment_name': getattr(executor.config, 'experiment_name', executor.config.name)
					})
					break

				# Only check for other controls if not the last iteration and END not requested
				if iteration < total_tests:
					# Step-by-step check (if enabled)
					if halt_controller._step_mode_enabled:
						if not halt_controller._wait_for_step_command(iteration, total_tests, result, logger=executor.gdflog):
							executor.gdflog.log("Loop execution ended by step command", 2)
							break
					
					# Regular halt check (existing functionality)
					if not halt_controller._wait_for_continue_or_cancel(iteration, total_tests, logger=executor.gdflog):
						executor.gdflog.log("Shmoo execution cancelled by user", 2)
						break

				time.sleep(10)

		# Update execution state
		if halt_controller:
			halt_controller._current_execution_state['is_running'] = False
			halt_controller._current_execution_state['waiting_for_command'] = False
			
			# Send final summary
			final_stats = halt_controller._calculate_current_stats(results)
			halt_controller._send_status_update('strategy_execution_complete', {
				'strategy_type': 'Shmoo',
				'test_name': executor.config.name,
				'experiment_name': getattr(executor.config, 'experiment_name', executor.config.name),
				'total_executed': len(results),
				'total_tests': len(results),
				'planned_iterations': total_tests,
				'completed_normally': len(results) == total_tests and not halt_controller._check_end_experiment_request(),
				'ended_by_command': halt_controller._check_end_experiment_request(),
				'final_stats': final_stats,
				'success_rate': final_stats.get('pass_rate', 0),
				'status_counts': TestResultProcessor._calculate_status_counts(results),
				'failure_patterns': TestResultProcessor._extract_failure_patterns(results),
				'shmoo_dimensions': f"{len(self.x_values)}x{len(self.y_values)}",
				'x_axis_config': self.x_config,
				'y_axis_config': self.y_config
			})
	
		return results
	
	def _update_config_value(self, config: TestConfiguration, axis_config: Dict, value: float):
		"""Update configuration with new test value"""
		ttype = axis_config['Type']
		domain = axis_config['Domain']
		
		if ttype == 'frequency':
			if domain == 'ia':
				config.freq_ia = int(value)
			elif domain == 'cfc':
				config.freq_cfc = int(value)
		elif ttype == 'voltage':
			if domain == 'ia':
				config.volt_IA = value
			elif domain == 'cfc':
				config.volt_CFC = value
