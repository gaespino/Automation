"""
AutomationBuilder.py
Contains all the core classes for automation flow building and execution.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from abc import ABC, abstractmethod
import threading
import time
from datetime import datetime
import queue
import json
from typing import Dict, List, Any, Optional, Callable

# Add parent directory to path for imports (if needed)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

# Import your existing flow classes (adjust paths as needed)
try:
	# These imports depend on your existing code structure
	from Automation_Flow.AutomationFlows import FlowTestBuilder
	from Automation_Flow.AutomationFlows import FlowTestExecutor
	# Import your flow instance classes
	from Automation_Flow.AutomationFlows import (
		FlowInstance, StartNodeFlowInstance, EndNodeFlowInstance,
		SingleFailFlowInstance, AllFailFlowInstance, MajorityFailFlowInstance,
		AdaptiveFlowInstance
	)
except ImportError as e:
	print(f"Warning: Could not import flow classes: {e}")
	# You might want to define dummy classes or handle this differently

# Import FileHandler if it exists
try:
	import FileHandler as fh
except ImportError:
	print("Warning: FileHandler not found. File operations may not work.")
	fh = None

import ExecutionHandler.utils.ThreadsHandler as th
ExecutionCommand = th.ExecutionCommand
execution_state = th.execution_state

# ==================== CORE DATA & STATE MANAGEMENT ====================

class FlowExecutionState:
	"""Manages the overall execution state and statistics."""
	
	def __init__(self, execution_state):
		self.is_running = False
		self.thread_active = False
		self.start_time = None
		self.current_node = None
		self.completed_nodes = set()
		self.failed_nodes = set()
		self.cancelled_nodes = set()
		self.total_nodes = 0
		self.completed_count = 0
		self.failed_count = 0
		# FIXED: Track experiments (nodes), not iterations
		self.total_experiments = 0  # Total number of nodes/experiments
		self.completed_experiments = 0  # Completed nodes
		self.failed_experiments = 0  # Failed nodes
		self.current_experiment_index = 0  # Current node index
		
		# Current node's iteration tracking
		self.current_node_iterations = 0
		self.current_node_total_iterations = 0
		self.execution_thread = None
		self.execution_state = execution_state
		# Threading and command handling
		self.cancel_requested = threading.Event()
		self.exception_queue = queue.Queue()
		
	def reset_for_new_execution(self):
		self.completed_nodes.clear()
		self.failed_nodes.clear()
		self.cancelled_nodes.clear()
		self.completed_experiments = 0
		self.failed_experiments = 0
		self.current_experiment_index = 0
		self.current_node = None
		self.current_node_iterations = 0
		self.current_node_total_iterations = 0
		self.start_time = time.time()
		self.cancel_requested.clear()
		
		# Prepare execution state for new run
		self.execution_state.prepare_for_execution()
		self.execution_state.update_state(
			execution_active=True,
			current_experiment=None,
			current_iteration=0,  # This will be iterations within current node
			total_iterations=0    # This will be set per node
		)
		
					
	def update_node_status(self, node_id, status):
		"""Update node status and counters."""
		if status == 'completed':
			self.completed_nodes.add(node_id)
			self.completed_experiments += 1
		elif status == 'failed':
			self.failed_nodes.add(node_id)
			self.failed_experiments += 1
		elif status == 'cancelled':
			self.cancelled_nodes.add(node_id)
		
		# Update current experiment index
		self.current_experiment_index = self.completed_experiments + self.failed_experiments
		
		# Update execution state with EXPERIMENT progress (not iteration)
		self.execution_state.update_state(
			current_experiment=f"Experiment {self.current_experiment_index}/{self.total_experiments}",
			# Keep iteration tracking for current node's internal iterations
			current_iteration=self.current_node_iterations,
			total_iterations=self.current_node_total_iterations
		)

	def set_current_node_iterations(self, current, total):
		"""Set iteration info for current node's experiment."""
		self.current_node_iterations = current
		self.current_node_total_iterations = total
		
		# Update execution state with node's iteration info
		self.execution_state.update_state(
			current_iteration=current,
			total_iterations=total
		)
			
	def get_progress_percentage(self):
		"""Get current progress as percentage of EXPERIMENTS (nodes)."""
		if self.total_experiments == 0:
			return 0
		return ((self.completed_experiments + self.failed_experiments) / self.total_experiments) * 100

	# ==================== COMMAND DELEGATION METHODS ====================
	
	def is_cancelled(self):
		"""Check if execution is cancelled - delegate to execution_state."""
		return self.execution_state.is_cancelled()
	
	def is_ended(self):
		"""Check if execution is ended - delegate to execution_state."""
		return self.execution_state.is_ended()
	
	def should_stop(self):
		"""Check if execution should stop - delegate to execution_state."""
		return self.execution_state.should_stop()
	
	def is_paused(self):
		"""Check if execution is paused - delegate to execution_state."""
		return self.execution_state.is_paused()
	
	def clear_all_commands(self):
		"""Clear all commands - delegate to execution_state."""
		self.execution_state.clear_all_commands()
		self.cancel_requested.clear()
	
	def cancel(self, reason="User requested"):
		"""Cancel execution - delegate to execution_state."""
		success = self.execution_state.cancel(reason)
		if success:
			self.cancel_requested.set()  # Set local flag for compatibility
		return success
	
	def end_experiment(self, reason="User requested"):
		"""End experiment - delegate to execution_state."""
		return self.execution_state.end_experiment(reason)
	
	def pause(self, reason="User requested"):
		"""Pause execution - delegate to execution_state."""
		return self.execution_state.pause(reason)
	
	def resume(self, reason="User requested"):
		"""Resume execution - delegate to execution_state."""
		return self.execution_state.resume(reason)
	
	# ==================== COMMAND ACKNOWLEDGMENT METHODS ====================
	
	def acknowledge_cancel(self, response=None):
		"""Acknowledge cancel command processing."""
		return self.execution_state.acknowledge_command(ExecutionCommand.CANCEL, response)
	
	def acknowledge_end(self, response=None):
		"""Acknowledge end command processing."""
		return self.execution_state.acknowledge_command(ExecutionCommand.END_EXPERIMENT, response)
	
	def acknowledge_pause(self, response=None):
		"""Acknowledge pause command processing."""
		return self.execution_state.acknowledge_command(ExecutionCommand.PAUSE, response)
	
	def acknowledge_resume(self, response=None):
		"""Acknowledge resume command processing."""
		return self.execution_state.acknowledge_command(ExecutionCommand.RESUME, response)
	
	# ==================== STATE MANAGEMENT METHODS ====================
	
	def update_state(self, **kwargs):
		"""Update execution state."""
		# Update local state
		for key, value in kwargs.items():
			if hasattr(self, key):
				setattr(self, key, value)
		
		# Update global execution state
		self.execution_state.update_state(**kwargs)
	
	def get_state(self, key, default=None):
		"""Get state value from execution_state."""
		return self.execution_state.get_state(key, default)
	
	def set_state(self, key, value):
		"""Set state value in execution_state."""
		self.execution_state.set_state(key, value)
	
	# ==================== COMPATIBILITY METHODS ====================
	
	def finalize_execution(self, reason="completed"):
		"""Finalize execution."""
		self.is_running = False
		self.thread_active = False
		self.execution_state.finalize_execution(reason)

class FlowConfiguration:
	"""Manages flow configuration and file handling."""
	
	def __init__(self, framework_api=None, framework_utils= None):
		self.builder = None
		self.executor = None
		self.root_node = None
		self.flow_folder = None
		self.structure_path = None
		self.flows_path = None
		self.ini_path = None
		self.default_files = {
			'structure': 'FrameworkAutomationStructure.json',
			'flows': 'FrameworkAutomationFlows.json',
			'ini': 'FrameworkAutomationInit.ini'
		}
		self.framework_api = framework_api
		self.framework_utils = framework_utils

	def load_configuration(self, structure_path, flows_path, ini_path, framework=None, logger=None):
		"""Load flow configuration from files."""
		try:
			if not FlowTestBuilder:
				raise ImportError("FlowTestBuilder not available")
				
			self.builder = FlowTestBuilder(
				structure_path, flows_path, ini_path, 
				Framework=framework, framework_utils=self.framework_utils, logger=logger
			)
			
			start_node_id = self.find_start_node()
			if not start_node_id:
				raise ValueError("No start node found in flow configuration")
				
			self.root_node = self.builder._FlowTestBuilder__build_instance(start_node_id)
			
			if FlowTestExecutor:
				self.executor = FlowTestExecutor(root=self.root_node, framework=framework)
			
			return True, None
		except Exception as e:
			return False, str(e)
	
	def find_start_node(self):
		"""Find the start node in the configuration."""
		try:
			# Method 1: Look for nodes with instanceType "StartNode"
			start_nodes = []
			for node_id, node_config in self.builder.structureFile.items():
				if node_config.get("instanceType") == "StartNode":
					start_nodes.append(node_id)
			
			if len(start_nodes) == 1:
				return start_nodes[0]
			elif len(start_nodes) > 1:
				return start_nodes[0]  # Use first one
			
			# Method 2: Look for nodes not referenced as targets
			all_node_ids = set(self.builder.structureFile.keys())
			referenced_nodes = set()
			
			for node_id, node_config in self.builder.structureFile.items():
				output_map = node_config.get("outputNodeMap", {})
				for target_id in output_map.values():
					referenced_nodes.add(target_id)
			
			unreferenced_nodes = all_node_ids - referenced_nodes
			
			if unreferenced_nodes:
				# Prioritize certain patterns
				for node_id in unreferenced_nodes:
					node_config = self.builder.structureFile[node_id]
					node_name = node_config.get("name", "").lower()
					if any(keyword in node_name for keyword in ['start', 'begin', 'root', 'baseline']):
						return node_id
				return list(unreferenced_nodes)[0]
			
			# Method 3: Look for naming patterns
			start_patterns = ['START', 'BEGIN', 'ROOT', 'BASELINE', 'ENTRY']
			for pattern in start_patterns:
				for node_id, node_config in self.builder.structureFile.items():
					node_name = node_config.get("name", "")
					if pattern in node_id.upper() or pattern in node_name.upper():
						return node_id
			
			# Fallback to first node
			if all_node_ids:
				return list(all_node_ids)[0]
				
			return None
			
		except Exception as e:
			print(f"Error finding start node: {e}")
			return None
	
	def validate_flow_structure(self):
		"""Validate the loaded flow structure."""
		warnings = []
		errors = []
		
		try:
			if not self.builder or not self.builder.structureFile:
				errors.append("No flow structure loaded")
				return False, warnings, errors
			
			all_nodes = set(self.builder.structureFile.keys())
			
			# Check for start nodes
			start_nodes = []
			for node_id, node_config in self.builder.structureFile.items():
				if node_config.get("instanceType") == "StartNode":
					start_nodes.append(node_id)
			
			if not start_nodes:
				warnings.append("No explicit StartNode found - using automatic detection")
			elif len(start_nodes) > 1:
				warnings.append(f"Multiple StartNodes found: {start_nodes}")
			
			# Check for missing target references
			for node_id, node_config in self.builder.structureFile.items():
				output_map = node_config.get("outputNodeMap", {})
				for port, target_id in output_map.items():
					if target_id not in all_nodes:
						errors.append(f"Node {node_id} references non-existent target: {target_id}")
			
			is_valid = len(errors) == 0
			return is_valid, warnings, errors
			
		except Exception as e:
			errors.append(f"Validation error: {str(e)}")
			return False, warnings, errors

# ==================== VISUAL COMPONENTS ====================
class NodeDrawer:
	"""Handles all node drawing and visual representation."""
	
	def __init__(self, canvas, node_colors, connection_colors):
		self.canvas = canvas
		self.node_colors = node_colors
		self.connection_colors = connection_colors
		self.node_widgets = {}
		
		# Text colors for better contrast
		self.node_text_colors = {
			'idle': 'black',
			'current': 'white',
			'running': 'white',
			'completed': 'white',
			'failed': 'white',
			'execution_fail': 'black',
			'skipped': 'white',
			'cancelled': 'white'
		}
		
	def draw_single_node(self, node, pos, status='idle'):
		"""Draw a single node with status styling."""
		x, y = pos['x'], pos['y']
		width, height = pos['width'], pos['height']
		
		# Determine colors based on status
		bg_color = self.node_colors.get(status, self.node_colors['idle'])
		text_color = self.node_text_colors.get(status, 'black')
		
		# Get node configuration for additional styling
		node_config = getattr(node, '_node_config', {})
		if hasattr(node, 'builder') and hasattr(node.builder, 'structureFile'):
			node_config = node.builder.structureFile.get(node.ID, {})
		
		instance_type = node_config.get("instanceType", type(node).__name__)
		
		# Add special styling for start/end nodes
		border_color = 'black'
		border_width = 2
		
		if instance_type == "StartNode":
			bg_color = self._blend_colors(bg_color, '#90EE90', 0.2)  # Green tint
			border_color = '#2E7D32'
			border_width = 3
		elif instance_type == "EndNode":
			bg_color = self._blend_colors(bg_color, '#FFB6C1', 0.2)  # Pink tint
			border_color = '#C62828'
			border_width = 3
		
		# Store all created elements for this node
		node_elements = []
		
		# Draw main node rectangle
		node_rect = self.canvas.create_rectangle(
			x, y, x + width, y + height,
			fill=bg_color, outline=border_color, width=border_width,
			tags=f"node_{node.ID}"
		)
		node_elements.append(node_rect)
		
		# Add status indicator border for running experiments
		if status == 'running':
			running_border = self.canvas.create_rectangle(
				x-2, y-2, x + width + 2, y + height + 2,
				fill='', outline='#FF5722', width=4,
				tags=f"node_{node.ID}"
			)
			node_elements.append(running_border)
		
		# Draw node content
		content_elements = self._draw_node_content(node, pos, text_color, instance_type)
		node_elements.extend(content_elements)
		
		# Draw status indicator
		status_elements = self._draw_status_indicator(node, pos, status)
		node_elements.extend(status_elements)
		
		# Draw connection ports
		port_elements = self._draw_connection_ports(node, pos, text_color)
		node_elements.extend(port_elements)
		
		# Store widget references with all elements
		self.node_widgets[node.ID] = {
			'rect': node_rect,
			'position': pos,
			'status': status,
			'elements': node_elements  # Store all canvas elements for complete cleanup
		}
	
	def redraw_node(self, node, new_status=None):
		"""Redraw a node with updated status - with complete cleanup."""
		if node.ID not in self.node_widgets:
			return
		
		# Get current position and status
		widget_info = self.node_widgets[node.ID]
		pos = widget_info['position']
		status = new_status or widget_info['status']
		
		# COMPLETE CLEANUP: Remove ALL elements associated with this node
		self._complete_node_cleanup(node.ID)
		
		# Redraw with new status
		self.draw_single_node(node, pos, status)
	
	def _complete_node_cleanup(self, node_id):
		"""Completely remove all visual elements for a node."""
		if node_id not in self.node_widgets:
			return
		
		widget_info = self.node_widgets[node_id]
		
		# Method 1: Delete by stored element IDs (most reliable)
		if 'elements' in widget_info:
			for element_id in widget_info['elements']:
				try:
					self.canvas.delete(element_id)
				except:
					pass  # Element might already be deleted
		
		# Method 2: Delete by tag (backup cleanup)
		self.canvas.delete(f"node_{node_id}")
		
		# Method 3: Additional cleanup for any missed elements
		# Find and delete any remaining elements that might have the node tag
		all_items = self.canvas.find_all()
		for item in all_items:
			tags = self.canvas.gettags(item)
			if f"node_{node_id}" in tags:
				try:
					self.canvas.delete(item)
				except:
					pass
	
	def _draw_node_content(self, node, pos, text_color, instance_type):
		"""Draw the content inside a node and return list of created elements."""
		x, y = pos['x'], pos['y']
		width, height = pos['width'], pos['height']
		
		elements = []
		
		# Node name (larger, bold)
		name_text = self.canvas.create_text(
			x + width // 2, y + 18,
			text=node.Name, fill=text_color,
			font=("Arial", 10, "bold"),
			width=width - 10,
			tags=f"node_{node.ID}"
		)
		elements.append(name_text)
		
		# Node ID
		id_text = self.canvas.create_text(
			x + width // 2, y + 38,
			text=f"ID: {node.ID}", fill=text_color,
			font=("Arial", 8),
			tags=f"node_{node.ID}"
		)
		elements.append(id_text)
		
		# Instance type (cleaned up)
		type_display = instance_type.replace('FlowInstance', '').replace('Node', '')
		if not type_display:
			type_display = "Flow"
		
		type_text = self.canvas.create_text(
			x + width // 2, y + 55,
			text=type_display, fill=text_color,
			font=("Arial", 8, "italic"),
			tags=f"node_{node.ID}"
		)
		elements.append(type_text)
		
		# Experiment info (if applicable)
		if instance_type not in ['StartNode', 'EndNode']:
			exp_name = getattr(node, 'Experiment', {}).get('Test Name', 'No Experiment')
			if exp_name and len(exp_name) > 18:
				exp_name = exp_name[:15] + "..."
			
			exp_color = 'blue' if text_color == 'black' else 'lightblue'
			exp_text = self.canvas.create_text(
				x + width // 2, y + 75,
				text=exp_name, fill=exp_color,
				font=("Arial", 7), width=width - 10,
				tags=f"node_{node.ID}"
			)
			elements.append(exp_text)
		
		# Level indicator
		if 'level' in pos and pos['level'] < 999:
			level_text = self.canvas.create_text(
				x + width - 15, y + 12,
				text=f"L{pos['level']}", fill=text_color,
				font=("Arial", 6, "bold"),
				tags=f"node_{node.ID}"
			)
			elements.append(level_text)
		
		return elements
	
	def _draw_status_indicator(self, node, pos, status):
		"""Draw status indicator on node and return list of created elements."""
		x, y = pos['x'], pos['y']
		
		elements = []
		
		# Status indicator (larger, more visible)
		indicator_size = 20
		indicator_x = x + 8
		indicator_y = y + 8
		
		# Status color mapping
		status_colors = {
			'idle': '#CCCCCC',
			'current': '#2196F3',
			'running': '#FF5722',      # Red - running
			'completed': '#4CAF50',    # Green - done
			'failed': '#F44336',
			'execution_fail': '#FFC107', # Yellow - execution fail
			'cancelled': '#9E9E9E'
		}
		
		indicator_color = status_colors.get(status, '#CCCCCC')
		
		# Draw indicator circle
		indicator = self.canvas.create_oval(
			indicator_x, indicator_y,
			indicator_x + indicator_size, indicator_y + indicator_size,
			fill=indicator_color, outline='black', width=2,
			tags=f"node_{node.ID}"
		)
		elements.append(indicator)
		
		# Add status symbol
		symbol_map = {
			'idle': '○',
			'current': '▶',
			'running': '●',      # Red dot for running
			'completed': '✓',    # Green checkmark for done
			'failed': '✗',
			'execution_fail': '!', # Yellow exclamation for execution fail
			'cancelled': '◐'
		}
		
		symbol = symbol_map.get(status, '○')
		symbol_color = 'white' if status in ['running', 'completed', 'failed'] else 'black'
		
		symbol_text = self.canvas.create_text(
			indicator_x + indicator_size // 2,
			indicator_y + indicator_size // 2,
			text=symbol, fill=symbol_color,
			font=("Arial", 10, "bold"),
			tags=f"node_{node.ID}"
		)
		elements.append(symbol_text)
		
		return elements
	
	def _draw_connection_ports(self, node, pos, text_color):
		"""Draw connection ports on a node and return list of created elements."""
		x, y = pos['x'], pos['y']
		width, height = pos['width'], pos['height']
		
		elements = []
		
		# Get output connections
		output_map = getattr(node, 'outputNodeMap', {})
		
		# Output ports (bottom of node)
		if output_map:
			port_size = 10
			port_spacing = 25
			ports = sorted(output_map.keys())
			
			# Calculate starting position to center ports
			total_width = len(ports) * port_spacing
			start_x = x + (width - total_width) // 2 + port_spacing // 2
			port_y = y + height - port_size - 5
			
			for i, port in enumerate(ports):
				port_x = start_x + i * port_spacing
				port_color = self.connection_colors.get(int(port), '#666666')
				
				# Port rectangle
				port_rect = self.canvas.create_rectangle(
					port_x, port_y,
					port_x + port_size, port_y + port_size,
					fill=port_color, outline='black', width=1,
					tags=f"node_{node.ID}"
				)
				elements.append(port_rect)
				
				# Port number
				port_text = self.canvas.create_text(
					port_x + port_size//2, port_y + port_size//2,
					text=str(port), fill='white',
					font=("Arial", 6, "bold"),
					tags=f"node_{node.ID}"
				)
				elements.append(port_text)
		
		# Input port (top of node) - only for non-start nodes
		instance_type = type(node).__name__
		if instance_type != "StartNodeFlowInstance":
			input_port_size = 8
			input_port = self.canvas.create_rectangle(
				x + width//2 - input_port_size//2, y - 2,
				x + width//2 + input_port_size//2, y + input_port_size - 2,
				fill='gray', outline='black', width=1,
				tags=f"node_{node.ID}"
			)
			elements.append(input_port)
		
		return elements
	
	def _blend_colors(self, color1, color2, ratio):
		"""Blend two colors together."""
		try:
			def hex_to_rgb(hex_color):
				hex_color = hex_color.lstrip('#')
				return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
			
			def rgb_to_hex(rgb):
				return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
			
			rgb1 = hex_to_rgb(color1)
			rgb2 = hex_to_rgb(color2)
			
			blended_rgb = tuple(
				int(rgb1[i] * (1 - ratio) + rgb2[i] * ratio)
				for i in range(3)
			)
			
			return rgb_to_hex(blended_rgb)
		except:
			return color1

class ConnectionDrawer:
	"""Handles drawing connections between nodes."""
	
	def __init__(self, canvas, connection_colors):
		self.canvas = canvas
		self.connection_colors = connection_colors
		self.connection_lines = {}
	
	def draw_connections(self, nodes, positions):
		"""Draw all connections between nodes."""
		# Clear all existing connections first
		self.clear_all_connections()
		
		for node in nodes:
			if not hasattr(node, 'outputNodeMap') or not node.outputNodeMap:
				continue
			self._draw_connections_for_node(node, positions)
	
	def clear_all_connections(self):
		"""Clear all connection lines from canvas and internal tracking."""
		# Delete all tracked connections
		for connection_key, connection_info in self.connection_lines.items():
			try:
				self.canvas.delete(connection_info['line'])
				self.canvas.delete(connection_info['label'])
				if 'label_bg' in connection_info:
					self.canvas.delete(connection_info['label_bg'])
			except:
				pass  # Element might already be deleted
		
		# Clear tracking dictionary
		self.connection_lines.clear()
		
		# Also delete by tag as backup
		self.canvas.delete("connection")
		self.canvas.delete("connection_line")
		self.canvas.delete("connection_label")
	
	def _draw_connections_for_node(self, node, positions):
		"""Draw connections for a single node."""
		if node.ID not in positions:
			return
			
		start_pos = positions[node.ID]
		start_x = start_pos['center_x']
		start_y = start_pos['y'] + start_pos['height']
		
		# Sort connections by port number for consistent visual ordering
		sorted_connections = sorted(node.outputNodeMap.items())
		
		for i, (port, next_node) in enumerate(sorted_connections):
			if next_node.ID not in positions:
				continue
				
			end_pos = positions[next_node.ID]
			end_x = end_pos['center_x']
			end_y = end_pos['y']
			
			# Choose color based on port
			color = self.connection_colors.get(port, '#666666')
			
			# Adjust start point if multiple connections from same node
			if len(sorted_connections) > 1:
				offset_x = (i - (len(sorted_connections) - 1) / 2) * 30
				actual_start_x = start_x + offset_x
			else:
				actual_start_x = start_x
			
			# Draw connection with routing
			self.draw_connection_with_routing(
				actual_start_x, start_y, end_x, end_y,
				color, port, node.ID, next_node.ID
			)
	
	def draw_connection_with_routing(self, start_x, start_y, end_x, end_y, 
								   color, port, from_node_id, to_node_id):
		"""Draw a connection with smart routing."""
		# Calculate if we need curved routing
		vertical_distance = end_y - start_y
		horizontal_distance = abs(end_x - start_x)
		
		# Create unique tags for this connection
		connection_tag = f"connection_{from_node_id}_{to_node_id}"
		line_tag = f"connection_line_{from_node_id}_{to_node_id}"
		label_tag = f"connection_label_{from_node_id}_{to_node_id}"
		
		if vertical_distance > 50 and horizontal_distance < 50:
			# Simple straight line for direct vertical connections
			line = self.canvas.create_line(
				start_x, start_y, end_x, end_y,
				fill=color, width=3, arrow=tk.LAST,
				arrowshape=(10, 12, 3),
				tags=("connection", "connection_line", line_tag, connection_tag)
			)
		else:
			# Use curved routing for complex connections
			mid_y = start_y + vertical_distance * 0.6
			
			points = [
				start_x, start_y,
				start_x, mid_y,
				end_x, mid_y,
				end_x, end_y
			]
			
			line = self.canvas.create_line(
				points,
				fill=color, width=3, arrow=tk.LAST,
				arrowshape=(10, 12, 3),
				smooth=True,
				tags=("connection", "connection_line", line_tag, connection_tag)
			)
		
		# Port label positioning
		if abs(end_x - start_x) > 100:
			label_x = (start_x + end_x) // 2
			label_y = start_y + vertical_distance * 0.6
		else:
			label_x = (start_x + end_x) // 2
			label_y = (start_y + end_y) // 2
		
		# Port label with background
		label_bg = self.canvas.create_oval(
			label_x - 12, label_y - 12,
			label_x + 12, label_y + 12,
			fill='white', outline=color, width=2,
			tags=("connection", "connection_label", label_tag, connection_tag)
		)
		
		port_label = self.canvas.create_text(
			label_x, label_y,
			text=str(port), fill=color,
			font=("Arial", 8, "bold"),
			tags=("connection", "connection_label", label_tag, connection_tag)
		)
		
		# Store connection info with all elements
		connection_key = f"{from_node_id}_{to_node_id}"
		self.connection_lines[connection_key] = {
			'line': line,
			'label': port_label,
			'label_bg': label_bg,
			'port': port,
			'from_node': from_node_id,
			'to_node': to_node_id,
			'elements': [line, label_bg, port_label]  # Track all elements
		}
	
	def redraw_connections_for_node(self, node_id, nodes, positions):
		"""Redraw connections for a specific node - with complete cleanup."""
		# Find all connections that involve this node (both incoming and outgoing)
		connections_to_remove = []
		
		for connection_key, connection_info in self.connection_lines.items():
			if (connection_info['from_node'] == node_id or 
				connection_info['to_node'] == node_id):
				connections_to_remove.append(connection_key)
		
		# Remove old connections completely
		for connection_key in connections_to_remove:
			self._remove_connection_completely(connection_key)
		
		# Force canvas update
		self.canvas.update_idletasks()
		
		# Redraw all connections that involve this node
		nodes_to_redraw = set()
		
		# Find all nodes that connect TO this node
		for node in nodes:
			if hasattr(node, 'outputNodeMap') and node.outputNodeMap:
				for target_node in node.outputNodeMap.values():
					if target_node.ID == node_id:
						nodes_to_redraw.add(node.ID)
		
		# Add the node itself (for outgoing connections)
		nodes_to_redraw.add(node_id)
		
		# Redraw connections for all affected nodes
		for redraw_node_id in nodes_to_redraw:
			for node in nodes:
				if node.ID == redraw_node_id:
					self._draw_connections_for_node(node, positions)
					break
	
	def _remove_connection_completely(self, connection_key):
		"""Completely remove a connection and all its visual elements."""
		if connection_key not in self.connection_lines:
			return
		
		connection_info = self.connection_lines[connection_key]
		
		# Method 1: Delete by stored element IDs
		if 'elements' in connection_info:
			for element_id in connection_info['elements']:
				try:
					self.canvas.delete(element_id)
				except:
					pass
		
		# Method 2: Delete individual elements
		try:
			self.canvas.delete(connection_info['line'])
			self.canvas.delete(connection_info['label'])
			if 'label_bg' in connection_info:
				self.canvas.delete(connection_info['label_bg'])
		except:
			pass
		
		# Method 3: Delete by specific tags
		from_node = connection_info.get('from_node', '')
		to_node = connection_info.get('to_node', '')
		if from_node and to_node:
			connection_tag = f"connection_{from_node}_{to_node}"
			line_tag = f"connection_line_{from_node}_{to_node}"
			label_tag = f"connection_label_{from_node}_{to_node}"
			
			self.canvas.delete(connection_tag)
			self.canvas.delete(line_tag)
			self.canvas.delete(label_tag)
		
		# Remove from tracking
		del self.connection_lines[connection_key]
	
	def cleanup_all_connections(self):
		"""Emergency cleanup of all connection-related canvas items."""
		# Delete all items with connection tags
		self.canvas.delete("connection")
		self.canvas.delete("connection_line")
		self.canvas.delete("connection_label")
		
		# Clear tracking
		self.connection_lines.clear()
		
		# Force update
		self.canvas.update_idletasks()
		
class LayoutManager:
	"""Manages node positioning and layout algorithms."""
	
	def __init__(self):
		self.custom_positions = {}
		self.position_modified = False
		
	def calculate_hierarchical_layout(self, builder):
		"""Calculate hierarchical top-to-bottom layout."""
		if not builder or not builder.structureFile:
			return {}
		
		# Find start node
		start_node_id = self._find_start_node(builder)
		if not start_node_id:
			return self._calculate_grid_layout(builder)
		
		# Calculate node levels using BFS
		node_levels = self._calculate_node_levels_bfs(start_node_id, builder)
		
		# Position nodes by level
		return self._position_nodes_by_level(node_levels, builder)
	
	def _find_start_node(self, builder):
		"""Find start node in builder."""
		for node_id, node_config in builder.structureFile.items():
			if node_config.get("instanceType") == "StartNode":
				return node_id
		
		# Fallback: find node not referenced by others
		all_nodes = set(builder.structureFile.keys())
		referenced = set()
		
		for node_config in builder.structureFile.values():
			output_map = node_config.get("outputNodeMap", {})
			referenced.update(output_map.values())
		
		unreferenced = all_nodes - referenced
		return list(unreferenced)[0] if unreferenced else list(all_nodes)[0] if all_nodes else None
	
	def _calculate_node_levels_bfs(self, start_node_id, builder):
		"""Calculate node levels using breadth-first search."""
		node_levels = {}
		queue = [(start_node_id, 0)]
		visited = set()
		
		while queue:
			node_id, level = queue.pop(0)
			
			if node_id in visited:
				continue
			
			visited.add(node_id)
			
			# Assign level (use minimum level if node was seen before)
			if node_id in node_levels:
				node_levels[node_id] = min(node_levels[node_id], level)
			else:
				node_levels[node_id] = level
			
			# Add connected nodes to queue
			node_config = builder.structureFile.get(node_id, {})
			output_map = node_config.get("outputNodeMap", {})
			
			for target_id in output_map.values():
				if target_id in builder.structureFile and target_id not in visited:
					queue.append((target_id, level + 1))
		
		# Handle unconnected nodes
		for node_id in builder.structureFile.keys():
			if node_id not in node_levels:
				node_levels[node_id] = 999
		
		return node_levels
	
	def _position_nodes_by_level(self, node_levels, builder):
		"""Position nodes based on their hierarchical levels."""
		# Group nodes by level
		levels = {}
		for node_id, level in node_levels.items():
			if level not in levels:
				levels[level] = []
			levels[level].append(node_id)
		
		# Sort nodes within each level
		for level in levels:
			levels[level].sort(key=lambda x: self._get_node_sort_key(x, builder))
		
		# Layout parameters
		node_width = 160
		node_height = 120
		horizontal_spacing = 220
		vertical_spacing = 180
		margin_x = 80
		margin_y = 60
		
		positions = {}
		
		# Position nodes level by level (top to bottom)
		for level, nodes_in_level in sorted(levels.items()):
			y = margin_y + (level * vertical_spacing)
			
			# Calculate total width needed for this level
			total_width = len(nodes_in_level) * node_width + (len(nodes_in_level) - 1) * (horizontal_spacing - node_width)
			
			# Center the level horizontally
			canvas_width = max(1000, total_width + 2 * margin_x)
			start_x = (canvas_width - total_width) // 2
			
			# Position each node in the level
			for i, node_id in enumerate(nodes_in_level):
				x = start_x + i * horizontal_spacing
				
				positions[node_id] = {
					'x': x,
					'y': y,
					'width': node_width,
					'height': node_height,
					'center_x': x + node_width // 2,
					'center_y': y + node_height // 2,
					'level': level
				}
		
		return positions
	
	def _get_node_sort_key(self, node_id, builder):
		"""Generate sort key for consistent node ordering within levels."""
		node_config = builder.structureFile.get(node_id, {})
		node_name = node_config.get("name", "")
		instance_type = node_config.get("instanceType", "")
		
		# Priority order: StartNode, regular nodes, EndNode
		if instance_type == "StartNode":
			priority = 0
		elif instance_type == "EndNode":
			priority = 2
		else:
			priority = 1
		
		return (priority, node_name.lower(), node_id)
	
	def _calculate_grid_layout(self, builder):
		"""Fallback grid layout."""
		positions = {}
		
		nodes_per_row = 3
		node_width = 160
		node_height = 120
		spacing_x = 220
		spacing_y = 180
		margin = 80
		
		row = 0
		col = 0
		
		for node_id in builder.structureFile.keys():
			x = margin + (col * spacing_x)
			y = margin + (row * spacing_y)
			
			positions[node_id] = {
				'x': x, 'y': y,
				'width': node_width, 'height': node_height,
				'center_x': x + node_width // 2,
				'center_y': y + node_height // 2,
				'level': row
			}
			
			col += 1
			if col >= nodes_per_row:
				col = 0
				row += 1
		
		return positions
	
	def get_node_position(self, node_id, calculated_positions):
		"""Get node position (custom or calculated)."""
		if node_id in self.custom_positions:
			return self.custom_positions[node_id]
		return calculated_positions.get(node_id)
	
	def set_custom_position(self, node_id, position):
		"""Set custom position for a node."""
		self.custom_positions[node_id] = position
		self.position_modified = True
	
	def reset_positions(self):
		"""Reset all custom positions."""
		self.custom_positions.clear()
		self.position_modified = False
	
	def reset_single_position(self, node_id):
		"""Reset single node position."""
		if node_id in self.custom_positions:
			del self.custom_positions[node_id]

# ==================== INTERACTION & DRAGGING ====================

class NodeDragHandler:
	"""Handles node dragging functionality."""
	
	def __init__(self, canvas, layout_manager, node_drawer, connection_drawer):
		self.canvas = canvas
		self.layout_manager = layout_manager
		self.node_drawer = node_drawer
		self.connection_drawer = connection_drawer
		
		self.dragging_enabled = True
		self.dragging_node = None
		self.drag_start_x = 0
		self.drag_start_y = 0
		self.drag_offset_x = 0
		self.drag_offset_y = 0
		self.snap_to_grid = True
		self.grid_size = 20
		self.drag_ghost = None
		self.connection_preview = []
		
		# Store references for redrawing
		self.current_nodes = []
		self.current_positions = {}
		
	def set_nodes_and_positions(self, nodes, positions):
		"""Set current nodes and positions for redrawing."""
		self.current_nodes = nodes
		self.current_positions = positions
		
	def enable_dragging(self, enabled=True):
		"""Enable or disable dragging."""
		self.dragging_enabled = enabled
		cursor = "hand2" if enabled else ""
		self.canvas.configure(cursor=cursor)
	
	def on_drag_start(self, event):
		"""Handle start of dragging."""
		if not self.dragging_enabled:
			return
		
		canvas_x = self.canvas.canvasx(event.x)
		canvas_y = self.canvas.canvasy(event.y)
		
		node_id = self._find_node_at_position(canvas_x, canvas_y)
		if node_id:
			self._start_dragging_node(node_id, canvas_x, canvas_y)
	
	def on_drag_motion(self, event):
		"""Handle dragging motion."""
		if not self.dragging_node:
			return
		
		canvas_x = self.canvas.canvasx(event.x)
		canvas_y = self.canvas.canvasy(event.y)
		
		if self.snap_to_grid:
			canvas_x = round(canvas_x / self.grid_size) * self.grid_size
			canvas_y = round(canvas_y / self.grid_size) * self.grid_size
		
		self._update_drag_ghost(canvas_x, canvas_y)
		self._update_connection_preview(canvas_x, canvas_y)
	
	def on_drag_end(self, event):
		"""Handle end of dragging."""
		if not self.dragging_node:
			return
		
		canvas_x = self.canvas.canvasx(event.x)
		canvas_y = self.canvas.canvasy(event.y)
		
		if self.snap_to_grid:
			canvas_x = round(canvas_x / self.grid_size) * self.grid_size
			canvas_y = round(canvas_y / self.grid_size) * self.grid_size
		
		self._finish_dragging(canvas_x, canvas_y)
	
	def _find_node_at_position(self, x, y):
		"""Find node at given canvas position."""
		item = self.canvas.find_closest(x, y)[0]
		tags = self.canvas.gettags(item)
		
		for tag in tags:
			if tag.startswith("node_"):
				return tag.split("_", 1)[1]
		return None
	
	def _start_dragging_node(self, node_id, x, y):
		"""Start dragging a specific node."""
		self.dragging_node = node_id
		self.drag_start_x = x
		self.drag_start_y = y
		
		# Calculate offset from node center
		if node_id in self.node_drawer.node_widgets:
			node_pos = self.node_drawer.node_widgets[node_id]['position']
			self.drag_offset_x = x - node_pos['center_x']
			self.drag_offset_y = y - node_pos['center_y']
		
		# Change cursor
		self.canvas.configure(cursor="fleur")
		
		# Create drag ghost
		self._create_drag_ghost(node_id, x, y)
		
		# Highlight connections
		self._highlight_node_connections(node_id, True)
	
	def _update_drag_ghost(self, x, y):
		"""Update ghost position during drag."""
		if self.drag_ghost:
			self.canvas.coords(
				self.drag_ghost,
				x - 75, y - 50,
				x + 75, y + 50
			)
	
	def _finish_dragging(self, x, y):
		"""Finish dragging and update node position."""
		# Calculate new position
		new_x = x - self.drag_offset_x - 80  # Adjust for node width/2
		new_y = y - self.drag_offset_y - 60  # Adjust for node height/2
		
		# Ensure node stays within canvas bounds
		new_x = max(20, new_x)
		new_y = max(20, new_y)
		
		# Update node position
		self._update_node_position(self.dragging_node, new_x, new_y)
		
		# Clean up drag state
		self._cleanup_drag_state()
	
	def _create_drag_ghost(self, node_id, x, y):
		"""Create a semi-transparent ghost of the node being dragged."""
		# Find the node to get its name
		node_name = node_id
		for node in self.current_nodes:
			if node.ID == node_id:
				node_name = node.Name
				break
		
		# Create ghost rectangle
		self.drag_ghost = self.canvas.create_rectangle(
			x - 75, y - 50,
			x + 75, y + 50,
			fill='lightblue', outline='blue', width=2,
			stipple='gray50',
			tags="drag_ghost"
		)
		
		# Add ghost text
		ghost_text = self.canvas.create_text(
			x, y, text=node_name,
			fill='blue', font=("Arial", 9, "bold"),
			tags="drag_ghost"
		)
	
	def _highlight_node_connections(self, node_id, highlight):
		"""Highlight connections for the specified node."""
		# Find connections involving this node
		for connection_key, connection_info in self.connection_drawer.connection_lines.items():
			if node_id in connection_key:
				if highlight:
					self.canvas.itemconfig(connection_info['line'], width=5, fill='orange')
				else:
					port = connection_info['port']
					original_color = self.connection_drawer.connection_colors.get(port, '#666666')
					self.canvas.itemconfig(connection_info['line'], width=3, fill=original_color)
	
	def _update_connection_preview(self, x, y):
		"""Update connection preview lines during dragging."""
		# Clear existing preview
		for item in self.connection_preview:
			self.canvas.delete(item)
		self.connection_preview.clear()
		
		if not self.dragging_node:
			return
		
		# Find the dragging node
		dragging_node = None
		for node in self.current_nodes:
			if node.ID == self.dragging_node:
				dragging_node = node
				break
		
		if not dragging_node or not hasattr(dragging_node, 'outputNodeMap'):
			return
		
		# Draw preview connections
		for target_node in dragging_node.outputNodeMap.values():
			if target_node.ID in self.node_drawer.node_widgets:
				target_pos = self.node_drawer.node_widgets[target_node.ID]['position']
				target_x = target_pos['center_x']
				target_y = target_pos['center_y']
				
				# Create preview line
				preview_line = self.canvas.create_line(
					x, y, target_x, target_y,
					fill='orange', width=2, dash=(5, 5),
					tags="connection_preview"
				)
				self.connection_preview.append(preview_line)
		
	def _update_node_position(self, node_id, new_x, new_y):
		"""Update a node's position and redraw it with complete cleanup."""
		if node_id not in self.node_drawer.node_widgets:
			return
		
		# Update position data
		old_pos = self.node_drawer.node_widgets[node_id]['position']
		new_pos = {
			'x': new_x,
			'y': new_y,
			'width': old_pos['width'],
			'height': old_pos['height'],
			'center_x': new_x + old_pos['width'] // 2,
			'center_y': new_y + old_pos['height'] // 2,
			'level': old_pos.get('level', 0)
		}
		
		# Store custom position
		self.layout_manager.set_custom_position(node_id, new_pos)
		
		# Update current positions
		self.current_positions[node_id] = new_pos
		
		# Find the node object
		node_obj = None
		for node in self.current_nodes:
			if node.ID == node_id:
				node_obj = node
				break
		
		if node_obj:
			# Get current status before cleanup
			current_status = self.node_drawer.node_widgets[node_id].get('status', 'idle')
			
			# STEP 1: Clean up ALL connections first (before touching the node)
			self.connection_drawer.redraw_connections_for_node(
				node_id, self.current_nodes, self.current_positions
			)
			
			# STEP 2: Clean up the node
			self.node_drawer._complete_node_cleanup(node_id)
			
			# STEP 3: Force canvas update
			self.canvas.update_idletasks()
			
			# STEP 4: Redraw node at new position
			self.node_drawer.draw_single_node(node_obj, new_pos, current_status)
			
			# STEP 5: Redraw connections again after node is in place
			self.canvas.after_idle(lambda: self.connection_drawer.redraw_connections_for_node(
				node_id, self.current_nodes, self.current_positions
			))
	def _cleanup_drag_state(self):
		"""Clean up dragging state and visual elements."""
		# Remove drag ghost
		if self.drag_ghost:
			self.canvas.delete(self.drag_ghost)
			self.drag_ghost = None
		
		# Remove connection preview
		for item in self.connection_preview:
			self.canvas.delete(item)
		self.connection_preview.clear()
		
		# Remove any remaining drag-related tags
		self.canvas.delete("drag_ghost")
		self.canvas.delete("connection_preview")
		
		# Unhighlight connections
		if self.dragging_node:
			self._highlight_node_connections(self.dragging_node, False)
		
		# Reset cursor
		if self.dragging_enabled:
			self.canvas.configure(cursor="hand2")
		else:
			self.canvas.configure(cursor="")
		
		# Force canvas update to ensure all cleanup is processed
		self.canvas.update_idletasks()
		
		# Clear dragging state
		self.dragging_node = None
		self.drag_start_x = 0
		self.drag_start_y = 0

class CanvasInteractionHandler:
	"""Handles canvas interactions like clicks, context menus, etc."""
	
	def __init__(self, canvas, flow_config, execution_state, drag_handler):
		self.canvas = canvas
		self.flow_config = flow_config
		self.execution_state = execution_state
		self.drag_handler = drag_handler
		
	def setup_bindings(self):
		"""Setup canvas event bindings."""
		# Note: We don't bind click events here since they're handled in the main interface
		# to coordinate with dragging
		pass
	
	def on_canvas_click(self, event):
		"""Handle canvas click events - only show details if not dragging."""
		# Check if we're in drag mode or currently dragging
		if (hasattr(self.drag_handler, 'dragging_node') and 
			self.drag_handler.dragging_node is not None):
			return  # Don't show details during dragging
		
		if not self.drag_handler.dragging_enabled:
			# If dragging is disabled, always show details
			self._show_node_details_for_click(event)
		else:
			# If dragging is enabled, we need to be more careful
			# Only show details if this was a simple click (not a drag operation)
			canvas_x = self.canvas.canvasx(event.x)
			canvas_y = self.canvas.canvasy(event.y)
		
			# Check if we clicked on a node
			node_id = self._find_node_at_position(canvas_x, canvas_y)
			if node_id:
				# Schedule details to show after a brief delay to see if dragging starts
				self.canvas.after(150, lambda: self._delayed_show_details(node_id, event.x, event.y))
				
	def _delayed_show_details(self, node_id, original_x, original_y):
		"""Show node details after a delay, but only if we're not dragging."""
		# Check if dragging started
		if (hasattr(self.drag_handler, 'dragging_node') and 
			self.drag_handler.dragging_node is not None):
			return  # Dragging started, don't show details
		
		# Check if mouse is still roughly in the same position (not dragging)
		try:
			current_x = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx()
			current_y = self.canvas.winfo_pointery() - self.canvas.winfo_rooty()
			
			# If mouse moved significantly, it was probably a drag attempt
			if abs(current_x - original_x) > 5 or abs(current_y - original_y) > 5:
				return
		except:
			pass  # If we can't get mouse position, proceed anyway
		
		# Show details
		self.show_node_details(node_id)
	
	def _show_node_details_for_click(self, event):
		"""Show node details for a click event when dragging is disabled."""
		canvas_x = self.canvas.canvasx(event.x)
		canvas_y = self.canvas.canvasy(event.y)
		
		node_id = self._find_node_at_position(canvas_x, canvas_y)
		if node_id:
			self.show_node_details(node_id)
	
	def _find_node_at_position(self, x, y):
		"""Find node at given canvas position."""
		item = self.canvas.find_closest(x, y)[0]
		tags = self.canvas.gettags(item)
		
		for tag in tags:
			if tag.startswith("node_"):
				return tag.split("_", 1)[1]
		return None
	
	def on_right_click(self, event):
		"""Handle right-click context menu."""
		if not self.drag_handler.dragging_enabled or self.execution_state.is_running:
			return
		
		canvas_x = self.canvas.canvasx(event.x)
		canvas_y = self.canvas.canvasy(event.y)
		
		# Find node under cursor
		item = self.canvas.find_closest(canvas_x, canvas_y)[0]
		tags = self.canvas.gettags(item)
		
		node_id = None
		for tag in tags:
			if tag.startswith("node_"):
				node_id = tag.split("_", 1)[1]
				break
		
		if node_id:
			self.show_context_menu(event, node_id)
	
	def show_node_details(self, node_id):
		"""Show detailed node information in a popup window."""
		if not self.flow_config.builder:
			return
			
		node = self.flow_config.builder.builtNodes.get(node_id)
		if not node:
			return
		
		# Create popup window with node details
		popup = tk.Toplevel()
		popup.title(f"Node Details: {node.Name}")
		popup.geometry("500x400")
		popup.transient(self.canvas.winfo_toplevel())
		popup.grab_set()  # Make it modal
		
		# Center the popup on the main window
		popup.update_idletasks()
		main_window = self.canvas.winfo_toplevel()
		x = main_window.winfo_x() + (main_window.winfo_width() // 2) - (popup.winfo_width() // 2)
		y = main_window.winfo_y() + (main_window.winfo_height() // 2) - (popup.winfo_height() // 2)
		popup.geometry(f"+{x}+{y}")
		
		# Create notebook for tabbed interface
		notebook = ttk.Notebook(popup)
		notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
		
		# Tab 1: Node Information
		info_frame = ttk.Frame(notebook)
		notebook.add(info_frame, text="Node Info")
		
		# Node basic information
		basic_info_frame = ttk.LabelFrame(info_frame, text="Basic Information", padding=10)
		basic_info_frame.pack(fill=tk.X, padx=5, pady=5)
		
		ttk.Label(basic_info_frame, text=f"ID: {node.ID}", font=("Arial", 10, "bold")).pack(anchor="w")
		ttk.Label(basic_info_frame, text=f"Name: {node.Name}").pack(anchor="w")
		ttk.Label(basic_info_frame, text=f"Type: {type(node).__name__}").pack(anchor="w")
		
		# Get node configuration
		node_config = {}
		if hasattr(self.flow_config.builder, 'structureFile'):
			node_config = self.flow_config.builder.structureFile.get(node_id, {})
		
		instance_type = node_config.get("instanceType", "Unknown")
		ttk.Label(basic_info_frame, text=f"Instance Type: {instance_type}").pack(anchor="w")
		
		# Connection information
		conn_info_frame = ttk.LabelFrame(info_frame, text="Connections", padding=10)
		conn_info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
		
		# Output connections
		if hasattr(node, 'outputNodeMap') and node.outputNodeMap:
			ttk.Label(conn_info_frame, text="Output Connections:", font=("Arial", 9, "bold")).pack(anchor="w")
			for port, target_node in node.outputNodeMap.items():
				conn_text = f"  Port {port} → {target_node.Name} ({target_node.ID})"
				ttk.Label(conn_info_frame, text=conn_text, font=("Arial", 8)).pack(anchor="w")
		else:
			ttk.Label(conn_info_frame, text="No output connections", font=("Arial", 8, "italic")).pack(anchor="w")
		
		# Tab 2: Experiment Configuration
		exp_frame = ttk.Frame(notebook)
		notebook.add(exp_frame, text="Experiment Config")
		
		# Experiment details with scrollable text
		exp_detail_frame = ttk.LabelFrame(exp_frame, text="Experiment Configuration", padding=10)
		exp_detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
		
		# Create text widget with scrollbar
		text_frame = ttk.Frame(exp_detail_frame)
		text_frame.pack(fill=tk.BOTH, expand=True)
		
		exp_text = tk.Text(text_frame, height=15, width=60, wrap=tk.WORD, font=("Consolas", 9))
		exp_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=exp_text.yview)
		exp_text.configure(yscrollcommand=exp_scrollbar.set)
		
		exp_text.pack(side="left", fill="both", expand=True)
		exp_scrollbar.pack(side="right", fill="y")
		
		# Display experiment configuration
		if hasattr(node, 'Experiment') and node.Experiment:
			for key, value in node.Experiment.items():
				exp_text.insert(tk.END, f"{key}:\n")
				if isinstance(value, (dict, list)):
					# Pretty print complex values
					import json
					try:
						formatted_value = json.dumps(value, indent=2)
						exp_text.insert(tk.END, f"{formatted_value}\n\n")
					except:
						exp_text.insert(tk.END, f"{str(value)}\n\n")
				else:
					exp_text.insert(tk.END, f"  {value}\n\n")
		else:
			exp_text.insert(tk.END, "No experiment configuration available.")
		
		exp_text.configure(state=tk.DISABLED)  # Make read-only
		
		# Tab 3: Execution Status (if available)
		if hasattr(node, 'runStatusHistory') or hasattr(node, 'execution_stats'):
			status_frame = ttk.Frame(notebook)
			notebook.add(status_frame, text="Execution Status")
			
			status_detail_frame = ttk.LabelFrame(status_frame, text="Execution Information", padding=10)
			status_detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
			
			# Execution status
			if hasattr(node, 'runStatusHistory') and node.runStatusHistory:
				ttk.Label(status_detail_frame, text="Run Status History:", font=("Arial", 9, "bold")).pack(anchor="w")
				for i, status in enumerate(node.runStatusHistory):
					status_text = f"  {i+1}. {status}"
					ttk.Label(status_detail_frame, text=status_text, font=("Arial", 8)).pack(anchor="w")
			
			# Execution statistics
			if hasattr(node, 'execution_stats') and node.execution_stats:
				ttk.Label(status_detail_frame, text="\nExecution Statistics:", font=("Arial", 9, "bold")).pack(anchor="w")
				for key, value in node.execution_stats.items():
					stat_text = f"  {key}: {value}"
					ttk.Label(status_detail_frame, text=stat_text, font=("Arial", 8)).pack(anchor="w")
		
		# Button frame
		button_frame = ttk.Frame(popup)
		button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
		
		# Close button
		close_button = ttk.Button(button_frame, text="Close", command=popup.destroy)
		close_button.pack(side=tk.RIGHT)
		
		# Copy to clipboard button (for experiment config)
		def copy_to_clipboard():
			if hasattr(node, 'Experiment') and node.Experiment:
				import json
				try:
					clipboard_text = json.dumps(node.Experiment, indent=2)
					popup.clipboard_clear()
					popup.clipboard_append(clipboard_text)
					# Show brief confirmation
					copy_button.configure(text="Copied!")
					popup.after(1000, lambda: copy_button.configure(text="Copy Config"))
				except Exception as e:
					copy_button.configure(text="Copy Failed")
					popup.after(1000, lambda: copy_button.configure(text="Copy Config"))
		
		copy_button = ttk.Button(button_frame, text="Copy Config", command=copy_to_clipboard)
		copy_button.pack(side=tk.RIGHT, padx=(0, 5))
		
		# Focus on the popup
		popup.focus_set()
		
		# Bind Escape key to close
		popup.bind('<Escape>', lambda e: popup.destroy())
	
	def show_context_menu(self, event, node_id):
		"""Show context menu for node operations."""
		context_menu = tk.Menu(self.canvas.winfo_toplevel(), tearoff=0)
		
		context_menu.add_command(
			label=f"Node Details: {node_id}",
			command=lambda: self.show_node_details(node_id)
		)
		
		context_menu.add_separator()
		
		context_menu.add_command(
			label=f"Reset Position: {node_id}",
			command=lambda: self._reset_single_node_position(node_id)
		)
		
		try:
			context_menu.tk_popup(event.x_root, event.y_root)
		finally:
			context_menu.grab_release()
	
	def _reset_single_node_position(self, node_id):
		"""Reset a single node to its calculated position."""
		if hasattr(self.drag_handler, 'layout_manager'):
			self.drag_handler.layout_manager.reset_single_position(node_id)
			print(f"Reset position for node: {node_id}")

# ==================== EXECUTION MANAGEMENT ====================

class FlowExecutionManager:
	"""Manages flow execution and Framework integration."""
	
	def __init__(self, flow_config, flow_execution_state, framework_manager):
		self.flow_config = flow_config
		self.flow_execution_state = flow_execution_state
		self.framework_api = None
		self.framework_manager = framework_manager
		self.update_queue = queue.Queue()

		# Thread management (matching ControlPanel)
		self.thread_active = False
		self.execution_thread = None
		self.current_framework_instance_id = None
		
		# FlowTestExecutor integration
		self.executor = None
		self.main_thread_handler = None  # Will be set externally

	def set_main_thread_handler(self, handler):
		"""Set main thread handler for UI updates."""
		self.main_thread_handler = handler
					
	def start_execution(self, executor):
		"""Start flow execution."""
		print('Execution Started 2')
		if self.thread_active:
			return False, "Execution already running"
		
		if not self.flow_config.root_node:
			return False, "No flow loaded"
		
		self.executor = executor
		print('Execution Started 3')
		# Prepare for execution
		self.flow_execution_state.reset_for_new_execution()
		self.flow_execution_state.is_running = True
		self.flow_execution_state.thread_active = True
		print('Execution Started 4')
		# Clear any previous commands (matching ControlPanel)
		self.flow_execution_state.clear_all_commands()
		print('Execution Started 5')
		# Create fresh Framework instance with ID tracking (matching ControlPanel)
		framework_instance_id = f"flow_framework_{int(time.time() * 1000)}"
		print('Execution Started 6')
		print(self.framework_manager)
		if self.framework_manager:
			print('Execution Started 7')
			print(self.framework_manager)
			self.framework_api = self.framework_manager.create_framework_instance(
				status_reporter=self.main_thread_handler,
				execution_state=self.flow_execution_state.execution_state
			)
			self.current_framework_instance_id = framework_instance_id
			print(f"Created fresh framework instance: {framework_instance_id}")

			if self.executor:
				self.executor.set_framework_api(self.framework_api)
				print(f"Set framework_api on executor: {self.framework_api}")			
		
		
		# Prepare primitive data for thread (matching ControlPanel pattern)
		flow_data = self._create_primitive_flow_data()
		framework_api = self.framework_api

		# Set thread management flags
		self.thread_active = True		
		print('Execution Started')
		# Start execution thread with primitive data only
		self.execution_thread = threading.Thread(
			target=self._execute_flow_thread,
			args=(flow_data, framework_api, framework_instance_id),
			daemon=True,
			name=f"FlowExecution_{framework_instance_id}"
		)
		self.execution_thread.start()
		
		return True, "Execution started"

	def _create_primitive_flow_data(self):
		"""Create primitive data for thread execution (matching ControlPanel pattern)."""
		try:
			flow_data = {
				'total_nodes': len(self.flow_config.builder.builtNodes) if self.flow_config.builder else 0,
				'start_node_id': self.flow_config.root_node.ID if self.flow_config.root_node else None,
				'structure_data': dict(self.flow_config.builder.structureFile) if self.flow_config.builder else {},
				'flows_data': dict(self.flow_config.builder.flowsFile) if self.flow_config.builder else {},
				'init_data': dict(self.flow_config.builder.initFile) if self.flow_config.builder else {}
			}
			return flow_data
		except Exception as e:
			self.update_queue.put(('execution_error', f"Failed to create flow data: {str(e)}"))
			return {}
			
	def cancel_execution(self):
		"""Cancel current execution using FlowExecutionState."""
		if not self.flow_execution_state.is_running:
			return False, "No execution running"
		
		# Use FlowExecutionState which delegates to execution_state
		success = self.flow_execution_state.cancel("User requested cancellation")
		
		if success and self.framework_api:
			try:
				result = self.framework_api.cancel_experiment()
				return result['success'], result['message']
			except Exception as e:
				return False, f"Framework cancel failed: {str(e)}"
		
		return success, "Cancellation requested" if success else "Failed to request cancellation"

	def _execute_flow_thread(self, flow_data, framework_api, framework_instance_id):
		"""Execute flow in separate thread with proper command checking."""
		try:
			current_node = self.flow_config.root_node
			node_count = 0

			# Verify framework instance at start
			if framework_instance_id != self.current_framework_instance_id:
				self.update_queue.put(('flow_execution_error', "Framework instance mismatch - aborting thread"))
				return

			# Send setup notification
			if self.main_thread_handler:
				self.main_thread_handler.queue_status_update({
					'type': 'flow_execution_setup',
					'data': {
						'total_nodes': flow_data['total_nodes'],
						'framework_instance_id': framework_instance_id
					}
				})

			# Execute flow using enhanced executor with monitoring
			self._execute_with_monitoring(flow_data, framework_api, framework_instance_id)			

			# Execution completed normally
			if not self.flow_execution_state.should_stop():
				self.main_thread_handler.queue_status_update({
					'type': 'flow_execution_complete',
					'data': {'framework_instance_id': framework_instance_id}
				})
			
		except InterruptedError:
			self.update_queue.put(('flow_execution_cancelled', 'Flow execution was cancelled'))
		except Exception as e:
			self.update_queue.put(('flow_execution_error', str(e)))
		finally:
			# Proper cleanup using FlowExecutionState
			self._cleanup_execution_thread(flow_data, framework_instance_id)
			
	def _execute_with_monitoring(self, flow_data, framework_api, framework_instance_id):
		"""Execute flow with node-by-node monitoring and command checking."""
		current_node = self.executor.root
		node_count = 0
		
		while (current_node is not None and 
			node_count < 50 and 
			not self.flow_execution_state.should_stop()):
			
			# Verify framework instance during execution
			if framework_instance_id != self.current_framework_instance_id:
				self.update_queue.put(('flow_execution_error', "Framework instance changed during execution"))
				break
			
			node_count += 1
			
			# Check for END command BEFORE starting each node
			if self.flow_execution_state.is_ended():
				self.flow_execution_state.acknowledge_end(f'END command received - stopping before node {node_count}')
				# FIXED: Use flow-specific handler
				if self.main_thread_handler:
					self.main_thread_handler.queue_status_update({
						'type': 'flow_execution_ended_complete',
						'data': {'reason': f'END command received - stopping before node {node_count}'}
					})
				break
			
			# Check for cancellation BEFORE starting each node
			if self.flow_execution_state.is_cancelled():
				self.flow_execution_state.acknowledge_cancel(f'Execution cancelled before node {node_count}')
				# FIXED: Use flow-specific handler
				if self.main_thread_handler:
					self.main_thread_handler.queue_status_update({
						'type': 'flow_execution_cancelled',
						'data': {'reason': f'Execution cancelled before node {node_count}'}
					})
				break
			
			# Update current node with primitive data
			if self.main_thread_handler:
				self.main_thread_handler.queue_status_update({
					'type': 'current_node',
					'data': {
						'node_id': current_node.ID,
						'node_name': current_node.Name,
						'experiment': getattr(current_node, 'Experiment', {})
					}
				})
			
			# Update status to running
			if self.main_thread_handler:
				self.main_thread_handler.queue_status_update({
					'type': 'node_running',
					'data': {'node_id': current_node.ID}
				})
			
			# Execute single node with monitoring
			success = self._execute_single_node_monitored(current_node, framework_instance_id)
			
			# Check for commands after node execution
			if self.flow_execution_state.is_ended():
				self.flow_execution_state.acknowledge_end(f'END command received after node execution')
				if self.main_thread_handler:
					self.main_thread_handler.queue_status_update({
						'type': 'flow_execution_ended_complete',
						'data': {'reason': 'END command received after node execution'}
					})
				break
			
			if self.flow_execution_state.is_cancelled():
				self.flow_execution_state.acknowledge_cancel(f'Execution cancelled after node execution')
				if self.main_thread_handler:
					self.main_thread_handler.queue_status_update({
						'type': 'flow_execution_cancelled',
						'data': {'reason': 'Execution cancelled after node execution'}
					})
				break
			
			# Update node completion status
			self._update_node_completion_status(current_node, success)
			
			# Get next node
			current_node = current_node.get_next_node()
			
			# Small delay to allow command processing
			time.sleep(0.1)
	
	def _execute_single_node_monitored(self, node, framework_instance_id):
		"""Execute a single node with Framework API integration and monitoring."""
		try:
			if self.framework_api:
				node.framework_api = self.framework_api
				print(f"Set framework_api on node {node.ID}: {self.framework_api}")
			else:
				print(f"WARNING: No framework_api available for node {node.ID}")
				
			# Framework instance verification
			if framework_instance_id and framework_instance_id != self.current_framework_instance_id:
				return False
			
			# Check global execution state before starting
			if self.flow_execution_state.should_stop():
				return False
			
			# Send node running status through MainThreadHandler
			if self.main_thread_handler:
				self.main_thread_handler.queue_status_update({
					'type': 'node_running',
					'data': {'node_id': node.ID}
				})

			# Set current experiment info in execution state
			experiment_name = f"Node: {node.Name}"
			if hasattr(node, 'Experiment') and node.Experiment:
				test_name = node.Experiment.get('Test Name', 'Unknown')
				experiment_name = f"{node.Name} - {test_name}"
					
				# Get expected iterations for this node
				total_iterations = self._get_node_expected_iterations(node)
				self.flow_execution_state.set_current_node_iterations(0, total_iterations)
			
			# Execute the node (this calls the node's run_experiment method)
			start_time = time.time()
			
			node.run_experiment()
			execution_time = time.time() - start_time

			# Check for cancellation after execution
			if self.flow_execution_state.should_stop():
				return False
			
			# Check Framework API state if available
			if self.framework_api:
				state = self.framework_api.get_current_state()
				if state.get('end_requested') or state.get('cancelled'):
					return False

			# FIXED: Check for system-level failures that should cancel entire flow
			system_failure = self._check_for_system_failures(node)
			if system_failure:
				# System failure - cancel entire flow execution
				self.flow_execution_state.cancel(f"System failure in node {node.ID}: {system_failure}")
				
				if self.main_thread_handler:
					self.main_thread_handler.queue_status_update({
						'type': 'flow_execution_cancelled',
						'data': {'reason': f'System failure: {system_failure}', 'node_id': node.ID}
					})
				
				return False
						
			# Determine success based on node's execution results
			success = self._determine_node_success(node)
				
			# Send completion status through MainThreadHandler
			if self.main_thread_handler:
				if success:
					self.main_thread_handler.queue_status_update({
						'type': 'node_completed',
						'data': {'node_id': node.ID}
					})
				else:
					# This is a test failure (FAIL result), not system failure
					self.main_thread_handler.queue_status_update({
						'type': 'node_failed',
						'data': {'node_id': node.ID}
					})
			
			return success
			
		except InterruptedError:
			# Propagate cancellation to execution state
			self.flow_execution_state.cancel("Node execution interrupted")
			return False
		except Exception as e:
			# Send error through MainThreadHandler
			if self.main_thread_handler:
				self.main_thread_handler.queue_status_update({
					'type': 'node_error',
					'data': {'node_id': node.ID, 'error': str(e)}
				})
			return False

	def _determine_node_success(self, node):
		"""Determine if node execution was successful (PASS/FAIL only, not system failures)."""
		if not hasattr(node, 'runStatusHistory') or not node.runStatusHistory:
			return True  # No status history, assume success
		
		# Only consider PASS/FAIL for flow routing decisions
		# System failures (FAILED, CANCELLED, etc.) are handled separately
		test_result_statuses = ['PASS', 'FAIL']
		
		# Filter to only test results, ignore system status
		test_results = [status for status in node.runStatusHistory if status in test_result_statuses]
		
		if not test_results:
			# No test results found, check if we have system failures
			system_failure = self._check_for_system_failures(node)
			if system_failure:
				# System failure already handled in _check_for_system_failures
				return False
			else:
				# No test results and no system failure, assume success
				return True
		
		# Determine success based on test results only
		fail_count = test_results.count('FAIL')
		return fail_count == 0  # Success if no FAIL results

	def _check_for_system_failures(self, node):
		"""Check for system-level failures that should cancel entire flow execution."""
		if not hasattr(node, 'runStatusHistory') or not node.runStatusHistory:
			return None
		
		# System failure indicators that should cancel entire flow
		system_failure_statuses = [
			'Failed',           # Framework execution failure
			'ExecutionFAIL', # User cancelled during execution
			'CANCELLED',        # General cancellation
			'TIMEOUT',          # System timeout
			'PythonFail',   # Hardware failure
			'FRAMEWORK_ERROR'   # Framework system error
		]

		for status in node.runStatusHistory:
			if status in system_failure_statuses:
				return status
		
		# Check for execution statistics indicating system failure
		if hasattr(node, 'execution_stats') and node.execution_stats:
			stats_str = str(node.execution_stats).lower()
			if any(keyword in stats_str for keyword in ['execution_error', 'timeout', 'framework_error', 'hardware_error']):
				return "System execution error detected"
		
		return None		

	def _get_node_expected_iterations(self, node):
		"""Get expected number of iterations for a node based on its experiment configuration."""
		if not hasattr(node, 'Experiment') or not node.Experiment:
			return 1
		
		experiment = node.Experiment
		test_type = experiment.get('Test Type', 'Loops')
		
		if test_type == 'Loops':
			return experiment.get('Loops', 1)
		elif test_type == 'Sweep':
			start = experiment.get('Start', 0)
			end = experiment.get('End', 10)
			step = experiment.get('Steps', 1)
			return max(1, int((end - start) / step) + 1)
		elif test_type == 'Shmoo':
			# Estimate based on shmoo configuration
			return experiment.get('EstimatedIterations', 50)
		else:
			return 1

	def _update_node_completion_status(self, node, success):
		"""Update node completion status based on execution result."""
		if success:
			# FIXED: Use MainThreadHandler instead of update_queue
			if self.main_thread_handler:
				self.main_thread_handler.queue_status_update({
					'type': 'node_completed',
					'data': {'node_id': node.ID}
				})
		else:
			# Check if it was a system failure (already handled) or test failure
			system_failure = self._check_for_system_failures(node)
			if not system_failure:
				# This is a test failure (FAIL result)
				if self.main_thread_handler:
					self.main_thread_handler.queue_status_update({
						'type': 'node_failed',
						'data': {'node_id': node.ID}
					})
	
	def _is_execution_failure(self, node):
		"""Determine if failure was execution-related (yellow) vs test failure (red)."""
		# Check node type
		instance_type = type(node).__name__
		if 'Start' in instance_type or 'End' in instance_type:
			return True  # Start/End node failures are usually execution issues
		
		# Check for execution error patterns
		if hasattr(node, 'runStatusHistory') and node.runStatusHistory:
			if 'FAILED' in node.runStatusHistory:  # Framework execution failure
				return True
			if len(node.runStatusHistory) == 1 and 'FAIL' in node.runStatusHistory:
				return True  # Single failure might be execution issue
		
		# Check for execution statistics
		if hasattr(node, 'execution_stats') and node.execution_stats:
			stats_str = str(node.execution_stats).lower()
			if any(keyword in stats_str for keyword in ['execution_error', 'timeout', 'framework_error']):
				return True
		
		return False  # Regular test failure

	def _cleanup_execution_thread(self, flow_data, framework_instance_id):
		"""Cleanup execution thread resources."""
		try:
			self.thread_active = False
			
			# Finalize execution state
			self.flow_execution_state.finalize_execution("flow_execution_complete")
			
			# Clear primitive data
			flow_data.clear()
			
			# Clear executor reference
			self.executor = None
			
			# Queue completion
			if self.main_thread_handler:
				if self.flow_execution_state.is_ended():
					self.main_thread_handler.queue_status_update({
						'type': 'flow_execution_ended_complete',
						'data': {'framework_instance_id': framework_instance_id}
					})
				else:
					self.main_thread_handler.queue_status_update({
						'type': 'flow_execution_complete',
						'data': {'framework_instance_id': framework_instance_id}
					})
					
		except Exception as cleanup_error:
			print(f"Flow thread cleanup error: {cleanup_error}")

class FrameworkIntegrationManager:
	"""Manages Framework API integration and commands."""
	
	def __init__(self, framework_manager=None, main_thread_handler=None, execution_state_obj=None):
		self.framework_manager = framework_manager
		self.main_thread_handler = main_thread_handler
		self.execution_state_obj = execution_state_obj
		self.framework_api = None
		
	def initialize_framework(self):
		"""Initialize Framework API."""
		if self.framework_manager:
			try:
				self.framework_api = self.framework_manager.create_framework_instance(
					status_reporter=self.main_thread_handler,
					execution_state=self.execution_state_obj
				)
				return True
			except Exception as e:
				print(f"Framework initialization failed: {e}")
				return False
		return False
	
	def toggle_framework_hold(self):
		"""Toggle Framework halt/continue."""
		if not self.framework_api:
			return False, "No Framework API available"
		
		try:
			state = self.framework_api.get_current_state()
			
			if state.get('is_halted', False):
				result = self.framework_api.continue_execution()
			else:
				result = self.framework_api.halt_execution()
			
			return result['success'], result['message']
		except Exception as e:
			return False, f"Framework operation failed: {str(e)}"
	
	def end_current_experiment(self):
		"""End current experiment."""
		if not self.framework_api:
			return False, "No Framework API available"
		
		try:
			result = self.framework_api.end_experiment()
			return result['success'], result['message']
		except Exception as e:
			return False, f"End experiment failed: {str(e)}"
	
	def is_experiment_running(self):
		"""Check if experiment is currently running."""
		if not self.framework_api:
			return False
		
		try:
			state = self.framework_api.get_current_state()
			return (state.get('is_running', False) and 
					not state.get('waiting_for_command', False) and
					state.get('current_experiment') is not None)
		except:
			return False

# ==================== UI COMPONENTS ====================

class FlowControlPanel:
	"""Manages the control buttons and execution controls."""
	
	def __init__(self, parent_frame, execution_manager, drag_handler, framework_integration=None):
		self.parent_frame = parent_frame
		self.execution_manager = execution_manager
		self.drag_handler = drag_handler
		self.framework_integration = framework_integration
		self.create_controls()
		
	def create_controls(self):
		"""Create control buttons."""
		# Title and controls frame
		title_frame = ttk.Frame(self.parent_frame)
		title_frame.pack(fill=tk.X, padx=10, pady=5)
		
		ttk.Label(title_frame, text="Automation Flow Execution", 
				 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
		
		# Status label
		self.status_label = tk.Label(title_frame, padx=5, width=15, text=" Ready ", 
								   bg="white", fg="black", font=("Arial", 12), 
								   relief=tk.GROOVE, borderwidth=2)
		self.status_label.pack(side=tk.RIGHT)
		
		# Control buttons frame
		controls_frame = ttk.Frame(title_frame)
		controls_frame.pack(side=tk.RIGHT, padx=5)
		
		# Execution controls
		self.start_button = ttk.Button(
			controls_frame, text="Start Flow",
			command=self.start_execution, state=tk.DISABLED
		)
		self.start_button.pack(side=tk.RIGHT, padx=2)
		
		self.hold_button = ttk.Button(
			controls_frame, text="Hold",
			command=self.toggle_framework_hold, 
			state=tk.DISABLED
		)
		self.hold_button.pack(side=tk.RIGHT, padx=2)
		
		self.end_button = ttk.Button(
			controls_frame, text="End",
			command=self.end_current_experiment, 
			state=tk.DISABLED
		)
		self.end_button.pack(side=tk.RIGHT, padx=2)
		
		self.cancel_button = ttk.Button(
			controls_frame, text="Cancel",
			command=self.cancel_execution, state=tk.DISABLED
		)
		self.cancel_button.pack(side=tk.RIGHT, padx=2)
		
		# Dragging controls
		drag_controls_frame = ttk.Frame(controls_frame)
		drag_controls_frame.pack(side=tk.RIGHT, padx=(20, 5))
		
		self.drag_enabled_var = tk.BooleanVar(value=True)
		self.drag_checkbox = ttk.Checkbutton(
			drag_controls_frame, text="Enable Dragging",
			variable=self.drag_enabled_var,
			command=self.toggle_dragging
		)
		self.drag_checkbox.pack(side=tk.RIGHT, padx=2)
		
		self.snap_grid_var = tk.BooleanVar(value=True)
		self.snap_checkbox = ttk.Checkbutton(
			drag_controls_frame, text="Snap to Grid",
			variable=self.snap_grid_var,
			command=self.toggle_grid_snap
		)
		self.snap_checkbox.pack(side=tk.RIGHT, padx=2)
		
		self.reset_positions_button = ttk.Button(
			drag_controls_frame, text="Reset Layout",
			command=self.reset_node_positions
		)
		self.reset_positions_button.pack(side=tk.RIGHT, padx=2)
	
	def start_execution(self):
		"""Start execution and update UI."""
		success, message = self.execution_manager.start_execution()
		if success:
			self.lock_controls_for_execution()
			self.status_label.configure(text=" Running ", bg="#BF0000", fg="white")
		return success, message
	
	def cancel_execution(self):
		"""Cancel execution and update UI."""
		success, message = self.execution_manager.cancel_execution()
		if success:
			self.status_label.configure(text=" Cancelling ", bg="orange", fg="black")
		return success, message
	
	def toggle_framework_hold(self):
		"""Toggle Framework hold/continue."""
		if self.framework_integration:
			success, message = self.framework_integration.toggle_framework_hold()
			if success:
				# Update button text based on current state
				if "continue" in message.lower():
					self.hold_button.configure(text="Continue")
				else:
					self.hold_button.configure(text="Hold")
	
	def end_current_experiment(self):
		"""End current experiment."""
		if self.framework_integration:
			success, message = self.framework_integration.end_current_experiment()
			if success:
				self.end_button.configure(text="Ending...", state=tk.DISABLED)
	
	def toggle_dragging(self):
		"""Toggle dragging capability."""
		enabled = self.drag_enabled_var.get()
		self.drag_handler.enable_dragging(enabled)
	
	def toggle_grid_snap(self):
		"""Toggle grid snapping."""
		self.drag_handler.snap_to_grid = self.snap_grid_var.get()
	
	def reset_node_positions(self):
		"""Reset node positions."""
		if self.drag_handler.layout_manager.position_modified:
			if messagebox.askyesno("Reset Positions", 
								 "This will reset all manually positioned nodes. Continue?"):
				self.drag_handler.layout_manager.reset_positions()
				return True
		return False
	
	def lock_controls_for_execution(self):
		"""Lock controls during execution."""
		self.start_button.configure(state=tk.DISABLED)
		self.cancel_button.configure(state=tk.NORMAL)
		self.hold_button.configure(state=tk.NORMAL)
		self.end_button.configure(state=tk.NORMAL)
		self.drag_checkbox.configure(state=tk.DISABLED)
		self.snap_checkbox.configure(state=tk.DISABLED)
		self.reset_positions_button.configure(state=tk.DISABLED)
		self.drag_handler.enable_dragging(False)
	
	def unlock_controls_after_execution(self):
		"""Unlock controls after execution."""
		self.start_button.configure(state=tk.NORMAL)
		self.cancel_button.configure(state=tk.DISABLED)
		self.hold_button.configure(state=tk.DISABLED, text="Hold")
		self.end_button.configure(state=tk.DISABLED, text="End")
		self.drag_checkbox.configure(state=tk.NORMAL)
		self.snap_checkbox.configure(state=tk.NORMAL)
		self.reset_positions_button.configure(state=tk.NORMAL)
		self.drag_handler.enable_dragging(self.drag_enabled_var.get())
		
		self.status_label.configure(text=" Ready ", bg="white", fg="black")

class FileManagementPanel:
	"""Manages file selection and loading."""
	
	def __init__(self, parent_frame, flow_config, on_flow_loaded_callback, logger_callback=None):
		self.parent_frame = parent_frame
		self.flow_config = flow_config
		self.on_flow_loaded_callback = on_flow_loaded_callback
		self.logger_callback = logger_callback or print
		self.file_labels = {}
		self.create_file_controls()
	
	def create_file_controls(self):
		"""Create file selection controls."""
		# File selection frame
		file_frame = ttk.Frame(self.parent_frame)
		file_frame.pack(fill=tk.X, padx=10, pady=5)
		
		ttk.Label(file_frame, text="Flow Folder:", width=12).pack(side=tk.LEFT)
		
		self.folder_entry = ttk.Entry(file_frame, state='readonly')
		self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
		
		self.browse_button = ttk.Button(
			file_frame, text="Browse",
			command=self.browse_flow_folder
		)
		self.browse_button.pack(side=tk.RIGHT)
		
		# File status frame
		self.file_status_frame = ttk.Frame(self.parent_frame)
		self.file_status_frame.pack(fill=tk.X, padx=10, pady=5)
		
		self.create_file_status_widgets()
	
	def create_file_status_widgets(self):
		"""Create file status indicators."""
		for file_type, filename in self.flow_config.default_files.items():
			frame = ttk.Frame(self.file_status_frame)
			
			# Status indicator
			status_label = ttk.Label(frame, text="●", foreground="red", font=("Arial", 12))
			status_label.pack(side=tk.LEFT)
			
			# File name
			name_label = ttk.Label(frame, text=filename, width=35)
			name_label.pack(side=tk.LEFT, padx=(5, 0))
			
			# Browse individual file button
			browse_btn = ttk.Button(frame, text="Browse", 
								  command=lambda ft=file_type: self.browse_individual_file(ft),
								  state=tk.DISABLED)
			browse_btn.pack(side=tk.RIGHT)
			
			self.file_labels[file_type] = {
				'frame': frame,
				'status': status_label,
				'name': name_label,
				'browse': browse_btn
			}
	
	def browse_flow_folder(self):
		"""Browse for flow folder."""
		folder_path = filedialog.askdirectory(title="Select Flow Configuration Folder")
		
		if not folder_path:
			return
		
		self.flow_config.flow_folder = folder_path
		self.folder_entry.configure(state='normal')
		self.folder_entry.delete(0, tk.END)
		self.folder_entry.insert(0, folder_path)
		self.folder_entry.configure(state='readonly')
		
		self.logger_callback(f"Selected flow folder: {folder_path}")
		
		# Check for default files
		self.check_default_files()
	
	def check_default_files(self):
		"""Check for default configuration files in the selected folder."""
		if not self.flow_config.flow_folder:
			return
		
		found_files = {}
		missing_files = []
		
		# Show file status frame
		self.file_status_frame.pack(fill=tk.X, padx=10, pady=5)
		
		for file_type, filename in self.flow_config.default_files.items():
			file_path = os.path.join(self.flow_config.flow_folder, filename)
			frame_info = self.file_labels[file_type]
			
			# Show the frame
			frame_info['frame'].pack(fill=tk.X, pady=2)
			
			if os.path.exists(file_path):
				# File found
				found_files[file_type] = file_path
				frame_info['status'].configure(foreground="green")
				frame_info['browse'].configure(state=tk.DISABLED)
				self.logger_callback(f"Found {filename}")
			else:
				# File not found
				missing_files.append(file_type)
				frame_info['status'].configure(foreground="red")
				frame_info['browse'].configure(state=tk.NORMAL)
				self.logger_callback(f"Missing {filename}")
		
		# Store found file paths
		self.flow_config.structure_path = found_files.get('structure')
		self.flow_config.flows_path = found_files.get('flows')
		self.flow_config.ini_path = found_files.get('ini')
		
		if missing_files:
			missing_list = [self.flow_config.default_files[ft] for ft in missing_files]
			message = f"Missing files:\n" + "\n".join(f"• {f}" for f in missing_list)
			message += "\n\nPlease use the Browse buttons to select these files individually."
			
			messagebox.showwarning("Missing Configuration Files", message)
		else:
			# All files found, try to load the flow
			self.load_flow_configuration()
	
	def browse_individual_file(self, file_type):
		"""Browse for individual configuration file."""
		filename = self.flow_config.default_files[file_type]
		
		# Determine file type for dialog
		if file_type in ['structure', 'flows']:
			filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
		else:  # ini
			filetypes = [("INI files", "*.ini"), ("All files", "*.*")]
		
		file_path = filedialog.askopenfilename(
			title=f"Select {filename}",
			filetypes=filetypes
		)
		
		if not file_path:
			return
		
		# Update the corresponding path
		if file_type == 'structure':
			self.flow_config.structure_path = file_path
		elif file_type == 'flows':
			self.flow_config.flows_path = file_path
		elif file_type == 'ini':
			self.flow_config.ini_path = file_path
		
		# Update UI
		frame_info = self.file_labels[file_type]
		frame_info['status'].configure(foreground="green")
		frame_info['name'].configure(text=os.path.basename(file_path))
		frame_info['browse'].configure(state=tk.DISABLED)
		
		self.logger_callback(f"Selected {file_type} file: {os.path.basename(file_path)}")
		
		# Check if all files are now available
		if all([self.flow_config.structure_path, self.flow_config.flows_path, self.flow_config.ini_path]):
			self.load_flow_configuration()
	
	def load_flow_configuration(self):
		"""Load flow configuration."""
		try:
			success, error = self.flow_config.load_configuration(
				self.flow_config.structure_path,
				self.flow_config.flows_path,
				self.flow_config.ini_path,
				framework=None,  # Set by main interface
				logger=self.logger_callback
			)
			
			if success:
				self.logger_callback("Flow loaded successfully")
				self.on_flow_loaded_callback()
			else:
				self.logger_callback(f"Failed to load flow: {error}")
				messagebox.showerror("Configuration Error", f"Error loading flow: {error}")
				
		except Exception as e:
			error_msg = f"Error loading flow configuration: {str(e)}"
			self.logger_callback(error_msg)
			messagebox.showerror("Configuration Error", error_msg)

class StatusDisplayPanel:
	"""Manages status display and statistics."""
	
	def __init__(self, parent_frame, execution_state):
		self.parent_frame = parent_frame
		self.execution_state = execution_state
		self.create_status_display()
	
	def create_status_display(self):
		"""Create status display widgets."""
		# Current status section
		status_frame = ttk.LabelFrame(self.parent_frame, text="Current Status", padding=10)
		status_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
		
		self.current_node_label = ttk.Label(status_frame, text="Node: Ready to start")
		self.current_node_label.pack(anchor="w")
		
		self.current_experiment_label = ttk.Label(status_frame, text="Experiment: None")
		self.current_experiment_label.pack(anchor="w")
		
		self.current_status_label = ttk.Label(status_frame, text="Status: Idle")
		self.current_status_label.pack(anchor="w")
		
		# Statistics section
		stats_frame = ttk.LabelFrame(self.parent_frame, text="Flow Statistics", padding=10)
		stats_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
		
		counters_frame = ttk.Frame(stats_frame)
		counters_frame.pack(fill=tk.X)
		
		self.completed_nodes_label = ttk.Label(counters_frame, text="✓ Completed: 0", foreground="green")
		self.completed_nodes_label.pack(side=tk.LEFT)
		
		self.failed_nodes_label = ttk.Label(counters_frame, text="✗ Failed: 0", foreground="red")
		self.failed_nodes_label.pack(side=tk.LEFT, padx=(10, 0))
		
		self.total_nodes_label = ttk.Label(counters_frame, text="Total: 0")
		self.total_nodes_label.pack(side=tk.RIGHT)
		
		# Progress bar
		progress_frame = ttk.Frame(stats_frame)
		progress_frame.pack(fill=tk.X, pady=(5, 0))
		
		ttk.Label(progress_frame, text="Progress:").pack(side=tk.LEFT)
		
		self.progress_var = tk.DoubleVar()
		self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
										  maximum=100, length=200)
		self.progress_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
		
		self.progress_label = ttk.Label(progress_frame, text="0%")
		self.progress_label.pack(side=tk.RIGHT)
		
		# Timing info
		timing_frame = ttk.Frame(stats_frame)
		timing_frame.pack(fill=tk.X, pady=(5, 0))
		
		self.elapsed_time_label = ttk.Label(timing_frame, text="Elapsed: 00:00")
		self.elapsed_time_label.pack(side=tk.LEFT)
	
	def update_current_node(self, node):
		"""Update current node display."""
		self.current_node_label.configure(text=f"Node: {node.Name} ({node.ID})")
		
		exp_name = "None"
		if hasattr(node, 'Experiment') and node.Experiment:
			exp_name = node.Experiment.get('Test Name', 'Unknown')
		
		self.current_experiment_label.configure(text=f"Experiment: {exp_name}")
	
	def update_status(self, status_text, color=None):
		"""Update current status display."""
		self.current_status_label.configure(text=f"Status: {status_text}")
		if color:
			self.current_status_label.configure(foreground=color)
	
	def update_statistics(self):
		"""Update statistics display."""
		self.completed_nodes_label.configure(text=f"✓ Completed: {self.execution_state.completed_count}")
		self.failed_nodes_label.configure(text=f"✗ Failed: {self.execution_state.failed_count}")
		self.total_nodes_label.configure(text=f"Total: {self.execution_state.total_nodes}")
		
		# Update progress
		progress = self.execution_state.get_progress_percentage()
		self.progress_var.set(progress)
		self.progress_label.configure(text=f"{int(progress)}%")
		
		# Update timing
		if self.execution_state.start_time:
			elapsed = time.time() - self.execution_state.start_time
			elapsed_str = self._format_time(elapsed)
			self.elapsed_time_label.configure(text=f"Elapsed: {elapsed_str}")
	
	def _format_time(self, seconds):
		"""Format seconds to MM:SS format."""
		minutes = int(seconds // 60)
		seconds = int(seconds % 60)
		return f"{minutes:02d}:{seconds:02d}"

# Export all classes for import
__all__ = [
	'FlowExecutionState',
	'FlowConfiguration', 
	'NodeDrawer',
	'ConnectionDrawer',
	'LayoutManager',
	'NodeDragHandler',
	'CanvasInteractionHandler',
	'FlowExecutionManager',
	'FrameworkIntegrationManager',
	'FlowControlPanel',
	'FileManagementPanel',
	'StatusDisplayPanel'
]