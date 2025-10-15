from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Tuple
from enum import Enum

print(' -- Debug Framework Status Manager -- rev 1.7')

#########################################################
######		Status Manager
#########################################################

class StatusEventType(Enum):
	# Experiment Level
	EXPERIMENT_START = "experiment_start"
	EXPERIMENT_END = "experiment_end"
	EXPERIMENT_FAILED = "experiment_failed"
	EXPERIMENT_CANCELLED = "experiment_cancelled"
	EXPERIMENT_PREPARED = "execution_prepared"
	EXPERIMENT_FINALIZED = "execution_finalized"
	EXPERIMENT_END_REQUESTED = "experiment_end_requested"
	EXPERIMENT_ENDED_BY_COMMAND = "experiment_ended_by_command"
	
	# Strategy Level
	STRATEGY_PROGRESS = "strategy_progress"
	STRATEGY_COMPLETE = "strategy_complete"
	STRATEGY_EXECUTION_COMPLETE = "strategy_execution_complete"
	
	# Iteration Level
	ITERATION_START = "iteration_start"
	ITERATION_PROGRESS = "iteration_progress"
	ITERATION_COMPLETE = "iteration_complete"
	ITERATION_FAILED = "iteration_failed"
	ITERATION_CANCELLED = "iteration_cancelled"
	
	# Command Level
	EXECUTION_HALTED = "execution_halted"
	EXECUTION_RESUMED = "execution_resumed"
	HALT_WAITING = "halt_waiting"

	# Step Mode
	STEP_MODE_ENABLED = "step_mode_enabled"
	STEP_MODE_DISABLED = "step_mode_disabled"
	STEP_ITERATION_COMPLETE = "step_iteration_complete"
	STEP_CONTINUE_ISSUED = "step_continue_issued"
	STEP_WAITING = "step_waiting"

@dataclass
class StatusContext:
	"""Context information for status updates"""
	experiment_name: Optional[str] = None
	strategy_type: Optional[str] = None
	test_name: Optional[str] = None
	current_iteration: int = 0
	total_iterations: int = 0
	additional_data: Dict[str, Any] = field(default_factory=dict)

class StatusUpdateManager:
	"""Lightweight status update manager that integrates with MainThreadHandler"""
	
	def __init__(self, status_reporter, logger=None):
		self.status_reporter = status_reporter  # Your MainThreadHandler instance
		self.logger = logger or print
		self.enabled = True
		self.context = StatusContext()
	
	def update_context(self, **kwargs):
		"""Update the current context"""
		for key, value in kwargs.items():
			if hasattr(self.context, key):
				setattr(self.context, key, value)
			else:
				self.context.additional_data[key] = value
	
	def send_update(self, event_type: StatusEventType, **additional_data):
		"""Send status update through your existing MainThreadHandler"""
		if not self.enabled:
			return
		
		try:
			# Build status data compatible with your MainThreadHandler
			status_data = {
				'type': event_type.value,
				'timestamp': datetime.now().isoformat(),
				'data': {
					# Core context
					'experiment_name': self.context.experiment_name,
					'strategy_type': self.context.strategy_type,
					'test_name': self.context.test_name,
					'iteration': self.context.current_iteration,
					'current_iteration': self.context.current_iteration,
					'total_iterations': self.context.total_iterations,
					
					# Additional context data
					**self.context.additional_data,
					
					# Event-specific data
					**additional_data
				}
			}
			
			# Apply event-specific transformations to match your handler expectations
			self._apply_event_transformations(status_data, event_type, additional_data)
			
			# Send through your existing status reporter
			if self.status_reporter:
				self.status_reporter.report_status(status_data)
				
			# Debug logging for progress updates
			if 'progress' in event_type.value:
				progress = additional_data.get('progress_percent', 0)
				if 'progress_weight' in additional_data:
					progress = additional_data['progress_weight'] * 100
				self.logger(f"DEBUG Framework Status: {event_type.value} - {progress:.1f}%")
				
		except Exception as e:
			self.logger(f"Status update error: {e}")
	
	def _apply_event_transformations(self, status_data: Dict, event_type: StatusEventType, additional_data: Dict):
		"""Apply transformations to match your MainThreadHandler expectations"""
		data = status_data['data']
		
		# Handle progress weight to progress percent conversion
		if 'progress_weight' in additional_data:
			data['progress_percent'] = additional_data['progress_weight'] * 100
		
		# Handle strategy progress specific formatting
		if event_type == StatusEventType.STRATEGY_PROGRESS:
			if 'progress_percent' not in additional_data and self.context.total_iterations > 0:
				data['progress_percent'] = (self.context.current_iteration / self.context.total_iterations) * 100
		
		# Handle iteration complete specific data
		if event_type == StatusEventType.ITERATION_COMPLETE:
			if 'scratchpad' in additional_data:
				data['scratchpad'] = additional_data['scratchpad']
			if 'seed' in additional_data:
				data['seed'] = additional_data['seed']
		
		# Handle strategy execution complete data
		if event_type == StatusEventType.STRATEGY_EXECUTION_COMPLETE:
			required_fields = [
				'total_executed', 'total_tests', 'planned_iterations', 
				'completed_normally', 'ended_by_command', 'final_stats',
				'success_rate', 'status_counts', 'failure_patterns'
			]
			for field in required_fields:
				if field in additional_data:
					data[field] = additional_data[field]
		
		# Handle step iteration complete data
		if event_type == StatusEventType.STEP_ITERATION_COMPLETE:
			if 'latest_result' in additional_data:
				data['latest_result'] = additional_data['latest_result']
			if 'current_stats' in additional_data:
				data['current_stats'] = additional_data['current_stats']
			if 'waiting_for_command' in additional_data:
				data['waiting_for_command'] = additional_data['waiting_for_command']
	
	def disable(self):
		"""Disable status updates"""
		self.enabled = False
	
	def enable(self):
		"""Enable status updates"""
		self.enabled = True
	
	def reset_context(self):
		"""Reset context for new execution"""
		self.context = StatusContext()
