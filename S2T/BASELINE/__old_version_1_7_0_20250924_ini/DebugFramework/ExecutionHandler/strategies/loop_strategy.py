import time
from typing import List
from typing import Optional, Dict, Any, List, Callable
from .base_strategy import TestStrategy
from ..configurations.test_configurations import TestResult, TestConfiguration
from ..execution.result_processor import TestResultProcessor
from ..execution.test_executor import TestExecutor
from ..utils.misc_utils import print_separator_box, print_custom_separator

class LoopTestStrategy(TestStrategy):
	"""Strategy for loop tests"""
	
	def __init__(self, loops: int):
		self.loops = loops
	
	def execute(self, executor: TestExecutor, halt_controller=None) -> List[TestResult]:
		results = []
		fail_count = 0

		# Set up callback for executor
		if halt_controller and hasattr(halt_controller, '_send_status_update'):
			executor._framework_callback = halt_controller._send_status_update
			
		# Initialize execution state
		if halt_controller:
			halt_controller._current_execution_state.update({
				'is_running': True,
				'total_iterations': self.loops,
				'iteration_results': [],
				'experiment_name': executor.config.name,
				'end_requested': False
			})

			# Store strategy type in config for status updates
			executor.config.strategy_type = 'Loops'		

		for i in range(self.loops):
			executor.config.tnumber = i + 1

			# Check for END command before starting iteration
			if halt_controller and halt_controller._check_end_experiment_request():
				executor.gdflog.log(f"Experiment ended by END command before iteration {i + 1}", 2)
				break

			# Send progress update
			if halt_controller:
				halt_controller._send_status_update('strategy_progress', {
					'strategy_type': 'Loops',
					'current_iteration': i + 1,
					'total_iterations': self.loops,
					'progress_percent': round((i + 1) / self.loops * 100, 1),
					'test_name': executor.config.name,
					'experiment_name': getattr(executor.config, 'experiment_name', executor.config.name)
				})

			executor.gdflog.log(f'{print_separator_box(direction="down")}')	
			executor.gdflog.log(print_custom_separator(f'Running Loop iteration: {i + 1}/{self.loops}'))

			result = executor.execute_single_test()
			results.append(result)
			
			if result.status == "CANCELLED":
				break
			elif result.status == "ExecutionFAIL":
				break
			elif result.status == "FAIL":
				fail_count += 1
				executor.config.reset = True
			else:
				executor.config.reset = executor.config.resetonpass
			
			executor.gdflog.log(f'{print_separator_box(direction="up")}')

			# Check for END command after iteration completion (highest priority)
			if halt_controller and halt_controller._check_end_experiment_request():
				executor.gdflog.log(f"Experiment ended by END command after iteration {i + 1}", 2)
				halt_controller._send_status_update('experiment_ended_by_command', {
					'completed_iterations': i + 1,
					'total_iterations': self.loops,
					'reason': 'END command',
					'final_result': result.status,
					'experiment_name': getattr(executor.config, 'experiment_name', executor.config.name)
				})
				break

			# Only check for other controls if not the last iteration and END not requested
			if i < self.loops - 1:
				# Step-by-step check (if enabled)
				if halt_controller._step_mode_enabled:
					if not halt_controller._wait_for_step_command(i + 1, self.loops, result, logger=executor.gdflog):
						executor.gdflog.log("Loop execution ended by step command", 2)
						break
				
				# Regular halt check (existing functionality)
				if not halt_controller._wait_for_continue_or_cancel(i + 1, self.loops, logger=executor.gdflog):
					executor.gdflog.log("Loop execution cancelled by user", 2)
					break
			
			time.sleep(10)  # Brief pause between iterations

		# Update execution state
		if halt_controller:
			halt_controller._current_execution_state['is_running'] = False
			halt_controller._current_execution_state['waiting_for_command'] = False
			
			# Send final summary
			final_stats = halt_controller._calculate_current_stats(results)
			halt_controller._send_status_update('strategy_execution_complete', {
				'strategy_type': 'Loops',
				'test_name': executor.config.name,
				'experiment_name': getattr(executor.config, 'experiment_name', executor.config.name),
				'total_executed': len(results),
				'total_tests': len(results),
				'planned_iterations': self.loops,
				'completed_normally': len(results) == self.loops and not halt_controller._check_end_experiment_request(),
				'ended_by_command': halt_controller._check_end_experiment_request(),
				'final_stats': final_stats,
				'success_rate': final_stats.get('pass_rate', 0),
				'status_counts': TestResultProcessor._calculate_status_counts(results),
				'failure_patterns': TestResultProcessor._extract_failure_patterns(results)
			})
					
		return results
