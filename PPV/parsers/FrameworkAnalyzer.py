"""
FrameworkAnalyzer - Comprehensive Experiment Summary Analysis
Analyzes data from all parsed Framework Report tabs to provide experiment-level insights
"""

import pandas as pd
import numpy as np
from collections import Counter
import re


class ExperimentSummaryAnalyzer:
	"""
	Generates comprehensive experiment-level summary by analyzing data from:
	- FrameworkData (test_df) - Raw experiment data with detailed test iterations
	- ExperimentReport (summary_df) - Polished report with key data for internal reporting
	- DragonData (vvar_df) - VVAR analysis data
	- CoreData (core_data_df) - Core voltage/ratio/VVAR data
	- FrameworkFails (fail_info_df) - Detailed failing content information
	- UniqueFails - Unique failing patterns
	- MCA data (mca_df) - Machine Check Architecture errors
	
	No additional file parsing required - uses existing dataframes.
	"""
	
	def __init__(self, test_df, summary_df=None, fail_info_df=None, vvar_df=None, 
				 mca_df=None, core_data_df=None, dragon_data_df=None):
		"""
		Initialize analyzer with all available dataframes.
		
		Args:
			test_df: FrameworkData dataframe (required) - raw experiment iteration data
			summary_df: ExperimentReport dataframe (required) - polished summary with key data
			fail_info_df: FrameworkFails dataframe (optional) - detailed failing content
			vvar_df: DragonData/VVAR dataframe (optional) - VVAR analysis
			mca_df: MCA data (optional) - Machine Check Architecture errors
			core_data_df: CoreData dataframe (optional) - core voltage/ratio data
			dragon_data_df: DragonData dataframe (optional) - alternative VVAR source
		"""
		self.test_df = test_df if test_df is not None else pd.DataFrame()
		self.summary_df = summary_df if summary_df is not None else pd.DataFrame()
		self.fail_info_df = fail_info_df if fail_info_df is not None else pd.DataFrame()
		self.vvar_df = vvar_df if vvar_df is not None else pd.DataFrame()
		self.mca_df = mca_df if mca_df is not None else pd.DataFrame()
		self.core_data_df = core_data_df if core_data_df is not None else pd.DataFrame()
		self.dragon_data_df = dragon_data_df if dragon_data_df is not None else pd.DataFrame()
		
		# Dragon content types (from PPVFrameworkReport.py)
		self.dragon_content = ['DBM', 'Pseudo Slice', 'Pseudo Mesh']
		self.exclude_vvars = ['0x0', '0x600D600D', '0x600d600d']
		
		# Linux content types (for FailingContent column naming and VVAR exclusion)
		self.linux_content_types = ['TSL', 'Sandstone', 'Linux']
	
	def analyze_all_experiments(self):
		"""
		Generate comprehensive summary for all experiments.
		Returns DataFrame with one row per experiment.
		"""
		if self.test_df.empty:
			return pd.DataFrame()
		
		# Check if required column exists
		if 'Folder' not in self.test_df.columns:
			print(f"Warning: 'Folder' column not found in test_df. Available columns: {list(self.test_df.columns)}")
			return pd.DataFrame()
		
		# Group by experiment (use Folder as unique identifier)
		experiments = self.test_df['Folder'].unique()
		
		summary_rows = []
		for experiment_folder in experiments:
			exp_data = self._analyze_single_experiment(experiment_folder)
			if exp_data:
				summary_rows.append(exp_data)
		
		if not summary_rows:
			return pd.DataFrame()
		
		# Create DataFrame (allow dynamic columns based on content type)
		df = pd.DataFrame(summary_rows)
		
		# Define desired column order (with Experiment Name, Status, and flexible failing column)
		base_columns = [
			'#', 'Date', 'Experiment Name', 'Type', 'PostCodes', 'Configuration', 'Used Content',
			'Results', 'Status', 'Fail Rate', 'Characterization', 'CoreData - PhyCore',
			'CoreData - Voltages', 'CoreData - Ratios', 'VVARs'
		]
		
		# Add FailingContent or Failing Seed column (whichever exists)
		if 'FailingContent' in df.columns:
			base_columns.append('FailingContent')
		else:
			base_columns.append('Failing Seed')
		
		# Ensure all base columns exist (add missing ones with empty strings)
		for col in base_columns:
			if col not in df.columns:
				df[col] = ''
		
		return df[base_columns]
	
	def _analyze_single_experiment(self, experiment_folder):
		"""Analyze a single experiment and return summary dict"""
		# Get all rows for this experiment
		if 'Folder' not in self.test_df.columns:
			return None
		
		# For voltage/frequency sweeps, experiment names change per iteration
		# So we need to match by experiment number (#) to get ALL iterations
		if '#' in self.test_df.columns:
			# First get the experiment number from the first matching folder
			temp_rows = self.test_df[self.test_df['Folder'] == experiment_folder]
			if temp_rows.empty:
				return None
			exp_num = temp_rows.iloc[0].get('#', None)
			
			# Now get ALL rows with this experiment number
			if exp_num:
				exp_rows = self.test_df[self.test_df['#'] == exp_num]
			else:
				exp_rows = temp_rows
		else:
			# Fallback to folder matching if # column doesn't exist
			exp_rows = self.test_df[self.test_df['Folder'] == experiment_folder]
		
		if exp_rows.empty:
			return None
		
		# Get first row for experiment-level data
		first_row = exp_rows.iloc[0]
		
		# Extract basic info with safe .get() calls
		exp_num = first_row.get('#', '')
		date = first_row.get('Date_Formatted', first_row.get('Date', ''))
		exp_type = first_row.get('Type', '')
		experiment_name = first_row.get('Experiment', experiment_folder)
		
		# Skip Invalid experiments
		if exp_type == 'Invalid':
			return None
		
		# Get unique postcodes
		postcodes = self._get_unique_postcodes(exp_rows)
		
		# Get configuration (Mask | Defeature)
		configuration = self._build_configuration(exp_rows)
		
		# Get used content
		used_content = self._get_used_content(first_row)
		
		# Determine if this is Linux content (check if any Linux type in content string)
		is_linux = any(linux_type in used_content for linux_type in self.linux_content_types)
		
		# Get results (MCAs and VVARs indicators) - pass is_linux flag and exp_num
		results = self._analyze_results(exp_num, exp_rows, experiment_folder, experiment_name, used_content, is_linux)
		
		# Calculate fail rate
		fail_rate = self._calculate_fail_rate(exp_rows)
		
		# Analyze characterization (voltage/frequency changes)
		characterization = self._analyze_characterization(exp_rows)
		
		# Get CoreData information (use exp_num and experiment_name for exact matching)
		phy_core, voltages, ratios = self._get_core_data_info(exp_num, experiment_name)
		
		# Get VVARs (N/A for Linux content)
		vvars = 'N/A' if is_linux else self._get_vvars(exp_num, experiment_name)
		
		# Get failing seed/content (use exp_num for exact matching)
		failing_content = self._get_failing_seed(exp_num, experiment_folder, experiment_name, used_content)
		
		# Get status from experiment results (PASS/FAIL/Mixed)
		status = self._get_experiment_status(exp_rows)
		
		# Always use 'FailingContent' as the column name (consistent across all content types)
		# The column will be renamed later if needed based on overall content mix
		result_dict = {
			'#': exp_num,
			'Date': date,
			'Experiment Name': experiment_name,  # Use experiment name from test_df
			'Type': exp_type,
			'PostCodes': postcodes,
			'Configuration': configuration,
			'Used Content': used_content,
			'Results': results,
			'Status': status,  # NEW: Status column
			'Fail Rate': fail_rate,
			'Characterization': characterization,
			'CoreData - PhyCore': phy_core,
			'CoreData - Voltages': voltages,
			'CoreData - Ratios': ratios,
			'VVARs': vvars,
			'FailingContent': failing_content,  # Always use this key
			'is_linux': is_linux  # Track for potential column renaming
		}
		
		return result_dict
	
	def _get_unique_postcodes(self, exp_rows):
		"""Extract unique postcodes from experiment rows"""
		if 'PostCode' not in exp_rows.columns:
			return ''
		
		postcodes = exp_rows['PostCode'].dropna().unique()
		# Filter out empty strings and 'None'
		postcodes = [str(pc) for pc in postcodes if pc and str(pc) not in ['None', 'nan', '']]
		return ', '.join(sorted(postcodes))
	
	def _extract_experiment_name(self, folder_name):
		"""
		Extract clean experiment name from folder (remove date/time prefix).
		Folder format: YYYYMMDD_HHMMSS_ExperimentName
		Returns: ExperimentName
		"""
		parts = folder_name.split('_')
		if len(parts) >= 3:
			# Remove first two parts (date and time)
			return '_'.join(parts[2:])
		return folder_name
	
	def _build_configuration(self, exp_rows):
		"""Build configuration string: Mask | Defeature (only stable values)"""
		# Get mask (should be consistent across experiment)
		mask = exp_rows['Configuration'].iloc[0] if 'Configuration' in exp_rows.columns else ''
		
		# For defeature, only include values that stay constant
		# Extract defeature components that don't change
		defeature_stable = self._extract_stable_defeature(exp_rows)
		
		if mask and defeature_stable:
			return f"{mask} | {defeature_stable}"
		elif mask:
			return mask
		elif defeature_stable:
			return defeature_stable
		else:
			return ''
	
	def _extract_stable_defeature(self, exp_rows):
		"""
		Extract only the defeature components that remain constant.
		Changing components (voltage/frequency) go into Characterization.
		"""
		# Parse defeature strings to find stable components
		defeature_components = {}
		
		for _, row in exp_rows.iterrows():
			# Get defeature from various possible column names
			defeature = ''
			for col in ['Defeature', 'DefeatureString']:
				if col in row and pd.notna(row[col]):
					defeature = str(row[col])
					break
			
			if not defeature:
				continue
			
			# Parse defeature (format: "Component1::Value1 | Component2::Value2")
			parts = defeature.split(' | ')
			for part in parts:
				if '::' in part:
					key, value = part.split('::', 1)
					if key not in defeature_components:
						defeature_components[key] = set()
					defeature_components[key].add(value)
		
		# Keep only components with single unique value
		stable_parts = []
		for key in sorted(defeature_components.keys()):
			values = defeature_components[key]
			if len(values) == 1:
				stable_parts.append(f"{key}::{list(values)[0]}")
		
		return ' | '.join(stable_parts)
	
	def _get_used_content(self, row):
		"""Get used content from row"""
		if 'Used Content' in row and pd.notna(row['Used Content']):
			return str(row['Used Content'])
		
		# Fallback: construct from Running Content and Content Detail
		running = row.get('Running Content', '')
		detail = row.get('Content Detail', '')
		
		if running and detail and running != detail:
			return f"{running}::{detail}"
		elif running:
			return running
		else:
			return detail
	
	def _analyze_results(self, exp_num, exp_rows, experiment_folder, experiment_name, used_content, is_linux):
		"""
		Analyze results: MCAs (YES/NO) | VVARs (YES/NO if not 0x0/0x600d600d) or N/A for Linux
		
		Args:
			exp_num: Experiment number (#)
			exp_rows: DataFrame rows for this experiment
			experiment_folder: Folder name
			experiment_name: Clean experiment name
			used_content: Content type
			is_linux: Boolean indicating if content is Linux type
		"""
		results_parts = []
		
		# Check MCAs
		has_mca = self._check_mca_presence(exp_rows, experiment_folder)
		mca_indicator = "YES" if has_mca else "NO"
		results_parts.append(f"MCAs: {mca_indicator}")
		
		# Check VVARs
		if is_linux:
			# For Linux content, show N/A
			results_parts.append("VVARs: N/A")
		else:
			# For non-Linux content, check if Dragon content type
			is_dragon = any(dragon_type in used_content for dragon_type in self.dragon_content)
			
			if is_dragon:
				# Use exp_num and experiment_name for precise matching
				has_vvar = self._check_vvar_presence(exp_num, experiment_name)
				vvar_indicator = "YES" if has_vvar else "NO"
				results_parts.append(f"VVARs: {vvar_indicator}")
		
		return ' | '.join(results_parts)
	
	def _check_mca_presence(self, exp_rows, experiment_folder):
		"""Check if experiment has MCAs"""
		# First check MCA Status column in test_df
		if 'MCA Status' in exp_rows.columns:
			mca_status = exp_rows['MCA Status'].dropna()
			if not mca_status.empty and any('YES' in str(status).upper() for status in mca_status):
				return True
		
		# Check mca_df if available
		if not self.mca_df.empty and 'Folder' in self.mca_df.columns:
			exp_mcas = self.mca_df[self.mca_df['Folder'] == experiment_folder]
			return not exp_mcas.empty
		
		return False
	
	def _check_vvar_presence(self, exp_num, experiment_name):
		"""
		Check if experiment has VVARs (excluding 0x0 and 0x600d600d).
		Matches by both # and Experiment name to avoid duplicate experiment collisions.
		"""
		if self.vvar_df.empty or 'Experiment' not in self.vvar_df.columns:
			return False
		
		# Filter VVARs for this experiment (match by both # and name if available)
		if '#' in self.vvar_df.columns and exp_num:
			exp_vvars = self.vvar_df[
				(self.vvar_df['#'] == exp_num) & 
				(self.vvar_df['Experiment'] == experiment_name)
			]
		else:
			# Fallback to name only
			exp_vvars = self.vvar_df[self.vvar_df['Experiment'] == experiment_name]
		
		if exp_vvars.empty:
			return False
		
		# Check for non-excluded VVAR values
		if 'VVAR' not in exp_vvars.columns:
			return False
			
		for _, row in exp_vvars.iterrows():
			vvar_val = str(row.get('VVAR', '')).strip()
			if vvar_val and vvar_val not in self.exclude_vvars:
				return True
		
		return False
	
	def _calculate_fail_rate(self, exp_rows):
		"""Calculate fail rate as percentage"""
		total = len(exp_rows)
		if total == 0:
			return '0%'
		
		# Count failures (Result/Status column)
		fail_count = 0
		for _, row in exp_rows.iterrows():
			result = str(row.get('Result', '')).upper()
			status = str(row.get('Status', '')).upper()
			
			if 'FAIL' in result or 'FAIL' in status:
				fail_count += 1
		
		fail_percentage = (fail_count / total) * 100
		return f"{fail_percentage:.1f}%"
	
	def _get_experiment_status(self, exp_rows):
		"""
		Get overall experiment status with counts:
		- All PASS -> "PASS 3" (if 3 iterations)
		- All FAIL -> "FAIL 3" (if 3 iterations)
		- Mixed -> "P15 | F3" (e.g., 15 pass, 3 fail)
		"""
		total = len(exp_rows)
		if total == 0:
			return ''
		
		pass_count = 0
		fail_count = 0
		
		for _, row in exp_rows.iterrows():
			result = str(row.get('Result', '')).upper()
			status = str(row.get('Status', '')).upper()
			
			if 'FAIL' in result or 'FAIL' in status:
				fail_count += 1
			else:
				pass_count += 1
		
		# Always include counts
		if fail_count == 0:
			return f'PASS {pass_count}'
		elif pass_count == 0:
			return f'FAIL {fail_count}'
		else:
			return f'P{pass_count} | F{fail_count}'
	
	def _analyze_characterization(self, exp_rows):
		"""
		Analyze characterization: voltage/frequency changes across iterations.
		Handles: Voltage sweeps, Frequency sweeps, Shmoo (2-axis)
		
		Returns formatted string describing the characterization.
		"""
		# Extract voltage and frequency data
		voltage_data = self._extract_voltage_frequency_data(exp_rows)
		
		if not voltage_data:
			return ''
		
		characterization_parts = []
		
		# Analyze voltage changes
		voltage_char = self._analyze_voltage_characterization(voltage_data)
		if voltage_char:
			characterization_parts.append(voltage_char)
		
		# Analyze frequency changes
		frequency_char = self._analyze_frequency_characterization(voltage_data)
		if frequency_char:
			characterization_parts.append(frequency_char)
		
		# Detect shmoo (2-axis) experiments
		if self._is_shmoo_experiment(voltage_data):
			shmoo_char = self._analyze_shmoo_characterization(voltage_data)
			if shmoo_char:
				characterization_parts.append(shmoo_char)
		
		return ' | '.join(characterization_parts)
	
	def _extract_voltage_frequency_data(self, exp_rows):
		"""
		Extract voltage and frequency data for each iteration.
		Returns dict with component types and their values over iterations.
		"""
		data = {
			'IA_Voltage': [],
			'IA_Frequency': [],
			'CFC_Voltage': [],
			'CFC_Frequency': [],
			'VBump': [],
			'Results': []
		}
		
		for _, row in exp_rows.iterrows():
			# Extract voltage and frequency values
			core_voltage = row.get('Core Voltage', None)
			core_freq = row.get('Core Freq', None)
			mesh_voltage = row.get('Mesh Voltage', None)
			mesh_freq = row.get('Mesh Freq', None)
			vbump = row.get('Voltage set to', None)
			result = str(row.get('Result', 'PASS')).upper()
			
			# Store with result
			data['IA_Voltage'].append((core_voltage, result))
			data['IA_Frequency'].append((core_freq, result))
			data['CFC_Voltage'].append((mesh_voltage, result))
			data['CFC_Frequency'].append((mesh_freq, result))
			data['VBump'].append((vbump, result))
			data['Results'].append(result)
		
		# Remove empty data
		data = {k: v for k, v in data.items() if v and any(val[0] is not None for val in v)}
		
		return data
	
	def _analyze_voltage_characterization(self, voltage_data):
		"""Analyze voltage sweep characterization"""
		char_parts = []
		
		# Check IA (Core) voltage
		if 'IA_Voltage' in voltage_data:
			ia_char = self._characterize_sweep(voltage_data['IA_Voltage'], 'IA', 'VBUMP')
			if ia_char:
				char_parts.append(ia_char)
		
		# Check CFC (Mesh) voltage
		if 'CFC_Voltage' in voltage_data:
			cfc_char = self._characterize_sweep(voltage_data['CFC_Voltage'], 'CFC', 'VBUMP')
			if cfc_char:
				char_parts.append(cfc_char)
		
		return ' | '.join(char_parts) if char_parts else ''
	
	def _analyze_frequency_characterization(self, voltage_data):
		"""Analyze frequency sweep characterization"""
		char_parts = []
		
		# Check IA (Core) frequency
		if 'IA_Frequency' in voltage_data:
			ia_char = self._characterize_sweep(voltage_data['IA_Frequency'], 'IA', 'FLAT Ratio')
			if ia_char:
				char_parts.append(ia_char)
		
		# Check CFC (Mesh) frequency
		if 'CFC_Frequency' in voltage_data:
			cfc_char = self._characterize_sweep(voltage_data['CFC_Frequency'], 'CFC', 'FLAT Ratio')
			if cfc_char:
				char_parts.append(cfc_char)
		
		return ' | '.join(char_parts) if char_parts else ''
	
	def _characterize_sweep(self, value_result_pairs, component, sweep_type):
		"""
		Characterize a voltage or frequency sweep.
		
		Args:
			value_result_pairs: List of (value, result) tuples
			component: 'IA' or 'CFC'
			sweep_type: 'VBUMP' or 'FLAT Ratio'
		
		Returns:
			Formatted characterization string or empty string
		
		Examples:
			Voltage: "CFC VBUMP: FAIL <= 0.04 | PASS >= 0.06"
			Frequency: "CFC FLAT Ratio: FAIL = 22 | PASS <= 20"
		"""
		# Filter out None values and extract unique values
		valid_pairs = [(v, r) for v, r in value_result_pairs if v is not None]
		
		if len(valid_pairs) < 2:
			return ''  # No sweep detected
		
		# Check if values are actually changing
		unique_values = set(v for v, r in valid_pairs)
		if len(unique_values) < 2:
			return ''  # No variation
		
		# Separate pass and fail values
		fail_values = [float(v) for v, r in valid_pairs if 'FAIL' in r]
		pass_values = [float(v) for v, r in valid_pairs if 'FAIL' not in r]
		
		if not fail_values and not pass_values:
			return ''
		
		# Determine step size (from first two unique sorted values)
		sorted_unique = sorted([float(v) for v in unique_values])
		if len(sorted_unique) >= 2:
			step = abs(sorted_unique[1] - sorted_unique[0])
		else:
			step = 0
		
		# Format results based on sweep type
		if sweep_type == 'VBUMP':
			# Voltage sweep: "CFC VBUMP: FAIL <= 0.04 | PASS >= 0.06"
			if fail_values and pass_values:
				fail_threshold = max(fail_values)
				pass_threshold = min(pass_values)
				return f"{component} {sweep_type}: FAIL <= {fail_threshold} | PASS >= {pass_threshold}"
			elif fail_values:
				fail_max = max(fail_values)
				return f"{component} {sweep_type}: FAIL <= {fail_max}"
			else:
				pass_min = min(pass_values)
				return f"{component} {sweep_type}: PASS >= {pass_min}"
		else:
			# Frequency sweep: "CFC FLAT Ratio: FAIL = 22 | PASS <= 20"
			if fail_values and pass_values:
				# Get the highest failing frequency
				fail_max_val = max(fail_values)
				# Get the highest passing frequency
				pass_max_val = max(pass_values)
				return f"{component} {sweep_type}: FAIL = {fail_max_val} | PASS <= {pass_max_val}"
			elif fail_values:
				fail_vals_str = ', '.join(map(str, sorted(set(fail_values))))
				return f"{component} {sweep_type}: FAIL = {fail_vals_str}"
			else:
				pass_max = max(pass_values)
				return f"{component} {sweep_type}: PASS <= {pass_max}"
	
	def _is_shmoo_experiment(self, voltage_data):
		"""Detect if experiment is a shmoo (2-axis) experiment"""
		# Shmoo has changes in at least 2 dimensions
		changing_dimensions = 0
		
		for key in ['IA_Voltage', 'IA_Frequency', 'CFC_Voltage', 'CFC_Frequency']:
			if key in voltage_data:
				values = [v for v, r in voltage_data[key] if v is not None]
				if len(set(values)) > 1:
					changing_dimensions += 1
		
		return changing_dimensions >= 2
	
	def _analyze_shmoo_characterization(self, voltage_data):
		"""Analyze shmoo (2-axis) characterization"""
		# Identify which axes are changing
		changing_axes = []
		
		if 'IA_Voltage' in voltage_data:
			ia_v_values = [v for v, r in voltage_data['IA_Voltage'] if v is not None]
			if len(set(ia_v_values)) > 1:
				changing_axes.append('IA Voltage')
		
		if 'IA_Frequency' in voltage_data:
			ia_f_values = [v for v, r in voltage_data['IA_Frequency'] if v is not None]
			if len(set(ia_f_values)) > 1:
				changing_axes.append('IA Frequency')
		
		if 'CFC_Voltage' in voltage_data:
			cfc_v_values = [v for v, r in voltage_data['CFC_Voltage'] if v is not None]
			if len(set(cfc_v_values)) > 1:
				changing_axes.append('CFC Voltage')
		
		if 'CFC_Frequency' in voltage_data:
			cfc_f_values = [v for v, r in voltage_data['CFC_Frequency'] if v is not None]
			if len(set(cfc_f_values)) > 1:
				changing_axes.append('CFC Frequency')
		
		if len(changing_axes) >= 2:
			return f"Shmoo: {' vs '.join(changing_axes[:2])}"
		
		return ''
	
	def _get_core_data_info(self, exp_num, experiment_name):
		"""
		Get CoreData information: PhyCore, Voltages, Ratios
		Returns: (phy_core, voltages, ratios)
		
		CoreData columns: Core_Module, HI_Ratio, Lo_Ratio, HI_Volt, Lo_Volt, #, Experiment
		Matches by both # (experiment number) and Experiment name to avoid duplicates
		"""
		if self.core_data_df.empty:
			return '', '', ''
		
		# Filter CoreData for this experiment (match by BOTH # and Experiment to avoid duplicates)
		if 'Experiment' not in self.core_data_df.columns:
			return '', '', ''
		
		# Match by experiment number if available (most specific)
		if '#' in self.core_data_df.columns and exp_num:
			exp_core_data = self.core_data_df[
				(self.core_data_df['#'] == exp_num) & 
				(self.core_data_df['Experiment'] == experiment_name)
			]
		else:
			# Fallback to name only (less safe but needed if # missing)
			exp_core_data = self.core_data_df[self.core_data_df['Experiment'] == experiment_name]
		
		if exp_core_data.empty:
			return '', '', ''
		
		# Get physical core (Core_Module column)
		if 'Core_Module' in exp_core_data.columns:
			phy_cores = exp_core_data['Core_Module'].dropna().unique()
			phy_core = ', '.join(sorted(set(str(pc) for pc in phy_cores)))
		else:
			phy_core = ''
		
		# Get voltage range (HI_Volt and Lo_Volt)
		voltages = ''
		if 'HI_Volt' in exp_core_data.columns and 'Lo_Volt' in exp_core_data.columns:
			hi_volts = exp_core_data['HI_Volt'].dropna()
			lo_volts = exp_core_data['Lo_Volt'].dropna()
			
			if not hi_volts.empty and not lo_volts.empty:
				# Convert to float if stored as strings
				try:
					hi_vals = [float(str(v).strip()) if str(v).strip() else 0 for v in hi_volts]
					lo_vals = [float(str(v).strip()) if str(v).strip() else 0 for v in lo_volts]
					hi_max = max(hi_vals)
					lo_min = min(lo_vals)
					voltages = f"HI: {hi_max:.6f} | LO: {lo_min:.6f}"
				except (ValueError, TypeError):
					voltages = ''
		
		# Get ratio range (HI_Ratio and Lo_Ratio)
		ratios = ''
		if 'HI_Ratio' in exp_core_data.columns and 'Lo_Ratio' in exp_core_data.columns:
			hi_ratios = exp_core_data['HI_Ratio'].dropna()
			lo_ratios = exp_core_data['Lo_Ratio'].dropna()
			
			if not hi_ratios.empty and not lo_ratios.empty:
				# Ratios might be hex strings like '0x16' - need to parse
				try:
					hi_ratio_vals = []
					lo_ratio_vals = []
					
					for hr in hi_ratios:
						hr_str = str(hr).strip()
						if hr_str.startswith('0x') or hr_str.startswith('0X'):
							hi_ratio_vals.append(int(hr_str, 16))
						else:
							hi_ratio_vals.append(int(float(hr_str)))
					
					for lr in lo_ratios:
						lr_str = str(lr).strip()
						if lr_str.startswith('0x') or lr_str.startswith('0X'):
							lo_ratio_vals.append(int(lr_str, 16))
						else:
							lo_ratio_vals.append(int(float(lr_str)))
					
					hi_max = max(hi_ratio_vals)
					lo_min = min(lo_ratio_vals)
					ratios = f"HI: 0x{hi_max:X} | LO: 0x{lo_min:X}"
				except (ValueError, TypeError):
					ratios = ''
		
		return phy_core, voltages, ratios
	
	def _get_vvars(self, exp_num, experiment_name):
		"""
		Get unique VVARs for experiment (excluding 0x0 and 0x600d600d).
		Only applicable for Dragon content.
		Matches by both # and Experiment name to avoid duplicate experiment collisions.
		"""
		if self.vvar_df.empty:
			return ''
		
		# Filter VVARs for this experiment (match by both # and name if available)
		if '#' in self.vvar_df.columns and exp_num:
			exp_vvars = self.vvar_df[
				(self.vvar_df['#'] == exp_num) & 
				(self.vvar_df['Experiment'] == experiment_name)
			]
		else:
			# Fallback to name only
			exp_vvars = self.vvar_df[self.vvar_df['Experiment'] == experiment_name]
		
		if exp_vvars.empty:
			return ''
		
		# Collect unique VVAR values
		vvar_values = []
		for _, row in exp_vvars.iterrows():
			vvar_val = str(row.get('VVAR', '')).strip()
			if vvar_val and vvar_val not in self.exclude_vvars:
				vvar_values.append(vvar_val)
		
		# Return unique sorted VVARs
		unique_vvars = sorted(set(vvar_values))
		return ', '.join(unique_vvars)
	
	def _get_failing_seed(self, exp_num, experiment_folder, experiment_name, used_content):
		"""
		Get failing seed/content with count prefix:
		- Priority 1: If CoreData available, use Failing_Content from CoreData (most reliable)
		- Priority 2: If DragonData available, use Failing_Seed from DragonData
		- Priority 3: Use Content Status from ExperimentReport (test_df) - fallback only
		
		Returns format: "x3_ContentA, x1_ContentB, x5_ContentC"
		where x# indicates number of times that content failed
		
		Matches by # (experiment number) to get ALL iterations for voltage/frequency sweeps.
		"""
		# Priority 1: Check CoreData FIRST (most reliable source)
		if not self.core_data_df.empty:
			# Filter CoreData for this experiment (match by BOTH # and Experiment to avoid duplicates)
			if 'Experiment' in self.core_data_df.columns and 'Failing_Content' in self.core_data_df.columns:
				# Match by experiment number if available (most specific)
				# For voltage/frequency sweeps, experiment names change per iteration,
				# so we MUST match by # to get ALL iterations
				if '#' in self.core_data_df.columns and exp_num:
					exp_core = self.core_data_df[self.core_data_df['#'] == exp_num]
				else:
					# Fallback to name only (less safe but needed if # missing)
					exp_core = self.core_data_df[self.core_data_df['Experiment'] == experiment_name]
				
				if not exp_core.empty:
					# Get Failing_Content from CoreData
					failing_content = exp_core['Failing_Content'].dropna()
					
					if len(failing_content) > 0:
						# Filter out invalid values (including 'PASS' which isn't actually a failure)
						valid_content = [str(fc) for fc in failing_content if fc and str(fc).lower() not in ['none', 'nan', '', 'pass']]
						if valid_content:
							# Count occurrences and format with x# prefix
							from collections import Counter
							content_counts = Counter(valid_content)
							formatted_content = [f"x{count}_{content}" for content, count in sorted(content_counts.items())]
							return ', '.join(formatted_content)
		
		# Priority 2: Check DragonData (vvar_df or dragon_data_df) if CoreData empty
		if not self.vvar_df.empty or (hasattr(self, 'dragon_data_df') and not self.dragon_data_df.empty):
			# Try to get from dragon_data_df first
			if hasattr(self, 'dragon_data_df') and not self.dragon_data_df.empty:
				dragon_df = self.dragon_data_df
			else:
				dragon_df = self.vvar_df
			
			# Filter for this experiment
			# For voltage/frequency sweeps, experiment names change per iteration,
			# so we MUST match by # to get ALL iterations
			if '#' in dragon_df.columns and exp_num:
				exp_dragon = dragon_df[dragon_df['#'] == exp_num]
			else:
				exp_dragon = dragon_df[dragon_df['Experiment'] == experiment_name]
			
			if not exp_dragon.empty:
				# Get failing seed from DragonData
				if 'Failing_Seed' in exp_dragon.columns:
					failing_seeds = exp_dragon['Failing_Seed'].dropna()
					if len(failing_seeds) > 0:
						# Filter out invalid values (including 'PASS' which isn't actually a failure)
						valid_seeds = [str(fs) for fs in failing_seeds if fs and str(fs).lower() not in ['none', 'nan', '', 'pass']]
						if valid_seeds:
							# Count occurrences and format with x# prefix
							from collections import Counter
							seed_counts = Counter(valid_seeds)
							formatted_seeds = [f"x{count}_{seed}" for seed, count in sorted(seed_counts.items())]
							return ', '.join(formatted_seeds)
		
		# Priority 3: Fallback to Content Status from test_df (use exp_num for matching)
		# For voltage/frequency sweeps, experiment names change per iteration (e.g., _ia_v0_01, _ia_v0_02)
		# So we match by experiment number (#) to get ALL iterations of the same experiment
		if '#' in self.test_df.columns and exp_num:
			# Match by experiment number - this catches all iterations even with changing names
			exp_rows = self.test_df[self.test_df['#'] == exp_num]
		else:
			# Fallback if # column is missing (shouldn't happen with current implementation)
			exp_rows = self.test_df[self.test_df['Folder'] == experiment_folder]
		
		if not exp_rows.empty and 'Content Status' in exp_rows.columns:
			# Get all content status values - DON'T use dropna() as we want to see all rows
			content_status_list = exp_rows['Content Status']
			
			if len(content_status_list) > 0:
				# Split by comma if multiple failures per row, then flatten
				all_failures = []
				for cs in content_status_list:
					# Handle NaN, None, and other invalid values
					if pd.isna(cs):
						continue  # Skip NaN values
					
					cs_str = str(cs).strip()  # Strip the entire value first
					if cs_str.lower() not in ['none', 'nan', '', 'pass']:
						# Split by comma and clean up each item
						failures = [f.strip() for f in cs_str.split(',')]
						all_failures.extend(failures)
				
				if all_failures:
					# Count occurrences and format with x# prefix
					from collections import Counter
					failure_counts = Counter(all_failures)
					formatted_failures = [f"x{count}_{failure}" for failure, count in sorted(failure_counts.items())]
					return ', '.join(formatted_failures)
		
		return ''


# Helper function to integrate with existing framework
def create_experiment_summary(test_df, summary_df=None, fail_info_df=None, vvar_df=None, 
							   mca_df=None, core_data_df=None, dragon_data_df=None):
	"""
	Convenience function to create ExperimentSummary dataframe.
	
	Args:
		test_df: FrameworkData dataframe (required) - raw experiment iteration data
		summary_df: ExperimentReport dataframe (required) - polished summary with key data
		fail_info_df: FrameworkFails dataframe (optional) - detailed failing content
		vvar_df: DragonData/VVAR dataframe (optional) - VVAR analysis
		mca_df: MCA data (optional) - Machine Check Architecture errors
		core_data_df: CoreData dataframe (optional) - core voltage/ratio data
		dragon_data_df: DragonData dataframe (optional) - alternative VVAR source
	
	Returns:
		DataFrame with comprehensive experiment summary
	"""
	analyzer = ExperimentSummaryAnalyzer(
		test_df=test_df,
		summary_df=summary_df,
		fail_info_df=fail_info_df,
		vvar_df=vvar_df,
		mca_df=mca_df,
		core_data_df=core_data_df,
		dragon_data_df=dragon_data_df
	)
	
	return analyzer.analyze_all_experiments()
