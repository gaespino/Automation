import time
from typing import List
from typing import Optional, Dict, Any, List, Callable
from .base_strategy import TestStrategy
from ..configurations.test_configurations import TestResult, TestConfiguration
from ..execution.result_processor import TestResultProcessor
from ..execution.test_executor import TestExecutor
from ..utils.misc_utils import print_separator_box, print_custom_separator

class SweepTestStrategy(TestStrategy):
	"""Strategy for sweep tests"""
	
	def __init__(self, ttype: str, domain: str, start: float, end: float, step: float):
		self.ttype = ttype
		self.domain = domain
		self.values = self._generate_range(start, end, step)
	
	def _generate_range(self, start: float, end: float, step: float) -> List[float]:
		"""Generate test values range"""
		if self.ttype == 'frequency':
			return list(range(int(start), int(end) + int(step), int(step)))
		elif self.ttype == 'voltage':
			values = []
			current = start
			while current <= end + step/2:  # Add small tolerance for float comparison
				values.append(round(current, 5))
				current += step
			return values
		else:
			raise ValueError(f"Invalid sweep type: {self.ttype}")
	
	def execute(self, executor: TestExecutor, halt_controller=None) -> List[TestResult]:
		results = []
		total_tests = len(self.values)
			
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
			executor.config.strategy_type = 'Sweep'
		
		for i, value in enumerate(self.values):
			executor.config.tnumber = i + 1
			self._update_config_value(executor.config, value)

			# Check for END command before starting iteration
			if halt_controller and halt_controller._check_end_experiment_request():
				executor.gdflog.log(f"Experiment ended by END command before iteration {i + 1}", 2)
				break

			# Send progress update
			if halt_controller:
				halt_controller._send_status_update('strategy_progress', {
					'strategy_type': 'Sweep',
					'current_iteration': i + 1,
					'total_iterations': total_tests,
					'progress_percent': round((i + 1) / total_tests * 100, 1),
					'test_name': executor.config.name,
					'experiment_name': getattr(executor.config, 'experiment_name', executor.config.name),
					'current_value': f"{self.domain}={value}"
				})

			executor.gdflog.log(f'{print_separator_box(direction="down")}')	
			executor.gdflog.log(f'Running Sweep iteration: {i + 1}/{total_tests}, {self.domain}={value}')
			
			result = executor.execute_single_test()
			results.append(result)
			
			#if result.status == TestStatus.CANCELLED:
			#	break
			#elif result.status == TestStatus.EXECUTION_FAIL:
			#	break
			if result.status == "FAIL":
				executor.config.reset = True
			elif result.status == "PASS":
				executor.config.reset = executor.config.resetonpass
			else:
				break
			
			executor.gdflog.log(f'{print_separator_box(direction="up")}')

			# Check for END command after iteration completion (highest priority)
			if halt_controller and halt_controller._check_end_experiment_request():
				executor.gdflog.log(f"Experiment ended by END command after iteration {i + 1}", 2)
				halt_controller._send_status_update('experiment_ended_by_command', {
					'completed_iterations': i + 1,
					'total_iterations': total_tests,
					'reason': 'END command',
					'final_result': result.status,
					'experiment_name': getattr(executor.config, 'experiment_name', executor.config.name)
				})
				break

			# Only check for other controls if not the last iteration and END not requested
			if i < total_tests - 1:
				# Step-by-step check (if enabled)
				if halt_controller._step_mode_enabled:
					if not halt_controller._wait_for_step_command(i + 1, total_tests, result, logger=executor.gdflog):
						executor.gdflog.log("Loop execution ended by step command", 2)
						break
				
				# Regular halt check (existing functionality)
				if not halt_controller._wait_for_continue_or_cancel(i + 1, total_tests, logger=executor.gdflog):
					executor.gdflog.log("Sweep execution cancelled by user", 2)
					break

			time.sleep(10)

		# Update execution state
		if halt_controller:
			halt_controller._current_execution_state['is_running'] = False
			halt_controller._current_execution_state['waiting_for_command'] = False
				
			# Send final summary
			final_stats = halt_controller._calculate_current_stats(results)
			halt_controller._send_status_update('strategy_execution_complete', {
				'strategy_type': 'Sweep',
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
				'failure_patterns': TestResultProcessor._extract_failure_patterns(results)
			})
	
		return results
	
	def _update_config_value(self, config: TestConfiguration, value: float):
		"""Update configuration with new test value"""
		if self.ttype == 'frequency':
			if self.domain == 'ia':
				config.freq_ia = int(value)
			elif self.domain == 'cfc':
				config.freq_cfc = int(value)
		elif self.ttype == 'voltage':
			if self.domain == 'ia':
				config.volt_IA = value
			elif self.domain == 'cfc':
				config.volt_CFC = value

