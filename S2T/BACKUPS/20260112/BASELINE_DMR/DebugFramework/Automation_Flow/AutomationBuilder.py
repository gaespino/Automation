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

class FlowConfiguration:
	"""Manages flow configuration and file handling."""

	def __init__(self, framework_api=None, framework_utils= None, execution_state = None):
		self.builder = None
		self.executor = None
		self.root_node = None
		self.flow_folder = None
		self.structure_path = None
		self.flows_path = None
		self.ini_path = None
		self.saved_positions = {}  # Store loaded positions
		self.default_files = {
			'structure': 'FrameworkAutomationStructure.json',
			'flows': 'FrameworkAutomationFlows.json',
			'ini': 'FrameworkAutomationInit.ini',
			'positions': 'FrameworkAutomationPositions.json'
		}
		self.framework_api = framework_api
		self.framework_utils = framework_utils
		self.execution_state = execution_state

	def load_configuration(self, structure_path, flows_path, ini_path, framework=None, logger=None, execution_state=None):
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

			# SINGLE PLACE: Create executor through builder with execution_state
			self.executor = self.builder.build_flow(start_node_id, execution_state=execution_state)

			# Load saved positions if available
			self._load_positions(logger)

			return True, None
		except Exception as e:
			return False, str(e)

	def _load_positions(self, logger=None):
		"""Load saved node positions from FrameworkAutomationPositions.json."""

		self.saved_positions = {}

		if not self.flow_folder:
			# Try to get folder from structure_path
			if self.structure_path:
				self.flow_folder = os.path.dirname(self.structure_path)

		if not self.flow_folder:
			return

		positions_file = os.path.join(self.flow_folder, self.default_files['positions'])

		if os.path.exists(positions_file):
			try:
				with open(positions_file, 'r') as f:
					positions_data = json.load(f)

				# Enhance positions with width, height, center_x, center_y
				node_width = 160
				node_height = 120

				for node_id, pos in positions_data.items():
					if 'x' in pos and 'y' in pos:
						x = pos['x']
						y = pos['y']

						# Create complete position dict with all required fields
						self.saved_positions[node_id] = {
							'x': x,
							'y': y,
							'width': pos.get('width', node_width),
							'height': pos.get('height', node_height),
							'center_x': x + pos.get('width', node_width) // 2,
							'center_y': y + pos.get('height', node_height) // 2,
							'level': pos.get('level', 0)
						}

				if logger:
					logger(f"Loaded saved positions for {len(self.saved_positions)} nodes", "success")
				else:
					print(f"[FlowConfig] Loaded {len(self.saved_positions)} node positions")

			except Exception as e:
				if logger:
					logger(f"Could not load positions: {str(e)}", "warning")
				else:
					print(f"[FlowConfig] Could not load positions: {e}")

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
			print(f"[DEBUG] Node {node.ID} not found in node_widgets")
			return

		# Get current position and status
		widget_info = self.node_widgets[node.ID]
		pos = widget_info['position']
		status = new_status or widget_info['status']

		print(f"[DEBUG] Redrawing node {node.ID} with status: {status}")

		# COMPLETE CLEANUP: Remove ALL elements associated with this node
		self._complete_node_cleanup(node.ID)

		# Redraw with new status
		self.draw_single_node(node, pos, status)

		print(f"[DEBUG] Node {node.ID} redrawn successfully")

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
		"""Handle all canvas click events with proper execution state awareness."""
		canvas_x = self.canvas.canvasx(event.x)
		canvas_y = self.canvas.canvasy(event.y)

		# First, always check if we clicked on a node
		node_id = self._find_node_at_position(canvas_x, canvas_y)
		if node_id:
			# ALWAYS show node details when clicking on a node, regardless of execution state
			self.show_node_details(node_id)
			return

		# For non-node clicks, check execution state
		is_running = self._is_execution_running()

		if is_running:
			# During execution, only node details are allowed (already handled above)
			return

		# When not running, handle dragging interactions
		if self._is_dragging_enabled():
			# Check if we're in the middle of a drag operation
			if (hasattr(self.drag_handler, 'dragging_node') and
				self.drag_handler.dragging_node):
				return  # Don't process clicks during dragging

			# This is a regular click on empty canvas - could be start of drag or just click
			# Let the drag handler decide
			pass  # No additional action needed for empty canvas clicks

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
		try:
			item = self.canvas.find_closest(x, y)
			if item:
				tags = self.canvas.gettags(item[0])
				for tag in tags:
					if tag.startswith("node_"):
						return tag.split("_", 1)[1]
			return None
		except Exception:
			return None

	def _is_execution_running(self):
		"""Check if execution is currently running."""
		try:
			if hasattr(self, 'execution_state') and self.execution_state:
				return self.execution_state.get_state('execution_active', False)
			return False
		except Exception:
			return False

	def _is_dragging_enabled(self):
		"""Check if dragging is currently enabled."""
		try:
			if hasattr(self.drag_handler, 'dragging_enabled'):
				return self.drag_handler.dragging_enabled
			return False
		except Exception:
			return False

	def on_right_click(self, event):
		"""Handle right-click context menu."""
		# Only show context menu if not running and dragging is enabled
		if self._is_execution_running():
			return

		if not self._is_dragging_enabled():
			return

		canvas_x = self.canvas.canvasx(event.x)
		canvas_y = self.canvas.canvasy(event.y)

		# Find node under cursor
		node_id = self._find_node_at_position(canvas_x, canvas_y)

		if node_id:
			self.show_context_menu(event, node_id)

	def show_node_details(self, node_id):
		"""Show detailed information about a node - always accessible."""
		# FIXED: Safe builder checking after cleanup
		if not hasattr(self, 'flow_config') or not self.flow_config:
			return
		if not hasattr(self.flow_config, 'builder') or not self.flow_config.builder:
			return

		node = self.flow_config.builder.builtNodes.get(node_id)
		if not node:
			return

		# Check execution state for display purposes
		is_running = self._is_execution_running()
		current_node_id = self._get_current_executing_node_id()

		# Create popup window with node details
		popup = tk.Toplevel()
		popup.title(f"Node Details: {node.Name}")
		popup.geometry("500x400")
		popup.transient(self.canvas.winfo_toplevel())
		popup.grab_set()  # Make it modal

		# Center the popup on the main window
		try:
			popup.update_idletasks()
			main_window = self.canvas.winfo_toplevel()
			x = main_window.winfo_x() + (main_window.winfo_width() // 2) - (popup.winfo_width() // 2)
			y = main_window.winfo_y() + (main_window.winfo_height() // 2) - (popup.winfo_height() // 2)
			popup.geometry(f"+{x}+{y}")
		except Exception:
			pass  # Use default positioning if calculation fails

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

		# Show current execution status if running
		if is_running:
			current_status = "Idle"
			status_color = "black"

			if current_node_id == node_id:
				current_status = "Currently Executing"
				status_color = "red"
			elif self._is_node_completed(node_id):
				current_status = "Completed"
				status_color = "green"
			elif self._is_node_failed(node_id):
				current_status = "Failed"
				status_color = "red"

			status_label = ttk.Label(basic_info_frame, text=f"Execution Status: {current_status}",
								font=("Arial", 9, "bold"), foreground=status_color)
			status_label.pack(anchor="w")

		# Get node configuration safely
		node_config = {}
		try:
			if (hasattr(self.flow_config, 'builder') and
				hasattr(self.flow_config.builder, 'structureFile')):
				node_config = self.flow_config.builder.structureFile.get(node_id, {})
		except Exception:
			pass

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

	def _get_current_executing_node_id(self):
		"""Get the ID of the currently executing node."""
		try:
			if hasattr(self, 'execution_state') and self.execution_state:
				current_exp = self.execution_state.get_state('current_experiment', '')
				# Try to extract node ID from current experiment string
				# This depends on how you format the current_experiment in your flow
				return None  # You'll need to implement this based on your flow's current_node tracking
			return None
		except Exception:
			return None

	def _is_node_completed(self, node_id):
		"""Check if a node has completed execution."""
		# You'll need to access the completed_nodes from FlowProgressInterface
		# This might require passing a reference or callback
		return False

	def _is_node_failed(self, node_id):
		"""Check if a node has failed execution."""
		# You'll need to access the failed_nodes from FlowProgressInterface
		# This might require passing a reference or callback
		return False

	def _reset_single_node_position(self, node_id):
		"""Reset a single node to its calculated position."""
		if hasattr(self.drag_handler, 'layout_manager'):
			self.drag_handler.layout_manager.reset_single_position(node_id)
			print(f"Reset position for node: {node_id}")

# ==================== UI COMPONENTS ====================

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
		completed_count = getattr(self.execution_state, 'completed_count', 0)
		failed_count = getattr(self.execution_state, 'failed_count', 0)
		total_nodes = getattr(self.execution_state, 'total_nodes', 0)

		self.completed_nodes_label.configure(text=f"✓ Completed: {completed_count}")
		self.failed_nodes_label.configure(text=f"✗ Failed: {failed_count}")
		self.total_nodes_label.configure(text=f"Total: {total_nodes}")

		# Update progress
		if total_nodes > 0:
			progress = ((completed_count + failed_count) / total_nodes) * 100
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
	'FlowConfiguration',
	'NodeDrawer',
	'ConnectionDrawer',
	'LayoutManager',
	'NodeDragHandler',
	'CanvasInteractionHandler',
	'FlowControlPanel',
	'FileManagementPanel',
	'StatusDisplayPanel'
]
