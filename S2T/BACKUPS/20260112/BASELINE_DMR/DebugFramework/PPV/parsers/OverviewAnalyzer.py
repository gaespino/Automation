"""
OverviewAnalyzer - Creates a stakeholder-friendly unit overview presentation

This analyzer creates a comprehensive overview of the unit's debug status,
including reproduction analysis, voltage/frequency sensitivity, content analysis,
and top MCAs. Redesigned for executive presentation with clear, actionable insights.
"""

import pandas as pd
from collections import Counter
import re


class OverviewAnalyzer:
	"""Analyzes experiment data to create a stakeholder-friendly Overview sheet"""
	
	def __init__(self, test_df, summary_df, experiment_summary_df, fail_info_df=None):
		"""
		Initialize the analyzer with all necessary dataframes
		
		Args:
			test_df: FrameworkData (raw test data)
			summary_df: ExperimentReport (polished summary)
			experiment_summary_df: ExperimentSummary (comprehensive experiment analysis)
			fail_info_df: FrameworkFails (failure analysis with MCAs)
		"""
		self.test_df = test_df
		self.summary_df = summary_df
		self.experiment_summary_df = experiment_summary_df
		self.fail_info_df = fail_info_df if fail_info_df is not None else pd.DataFrame()
		
		# Content type mappings for categorization
		self.content_mappings = {
			'DBM': ['DBM', 'Dragon Bare Metal'],
			'Pseudo Mesh': ['Pseudo Mesh', 'SBFT', 'Dragon Pseudo SBFT'],
			'Pseudo Slice': ['Pseudo Slice', 'Dragon Pseudo Slice'],
			'Linux TSL': ['TSL', 'Test Seed Loader', 'Linux::TSL'],
			'Linux Sandstone': ['Sandstone', 'Linux::Sandstone'],
			'Linux iMunch': ['iMunch', 'Imunch', 'Linux::iMunch']
		}
	
	def create_overview(self):
		"""Create the Overview data structure with professional formatting"""
		sections = []
		
		# ======================== HEADER SECTION ========================
		sections.append(self._create_header_section())
		
		# ======================== UNIT INFORMATION ========================
		sections.append(self._create_unit_info_section())
		
		# ======================== REPRODUCTION STATUS ========================
		sections.append(self._create_reproduction_section())
		
		# ======================== CHARACTERIZATION RESULTS ========================
		sections.append(self._create_characterization_section())
		
		# ======================== FAILURE ANALYSIS ========================
		sections.append(self._create_failure_analysis_section())
		
		# ======================== CONTENT COVERAGE ========================
		sections.append(self._create_content_section())
		
		# Combine all sections
		all_data = []
		for section in sections:
			all_data.extend(section)
		
		return pd.DataFrame(all_data)
	
	def _create_header_section(self):
		"""Create header with title"""
		visual_id = self._get_visual_id()
		return [
			{'Section': 'HEADER', 'Category': '', 'Metric': f'DEBUG FRAMEWORK UNIT OVERVIEW - {visual_id}', 'Value': '', 'Status': '', 'Details': ''},
			{'Section': '', 'Category': '', 'Metric': '', 'Value': '', 'Status': '', 'Details': ''},
		]
	
	def _create_unit_info_section(self):
		"""Create unit information section"""
		visual_id = self._get_visual_id()
		first_exp, first_date = self._get_first_experiment()
		last_exp, last_date = self._get_last_experiment()
		
		# Count total experiments and failures
		total_experiments = len(self.experiment_summary_df) if not self.experiment_summary_df.empty else 0
		total_tests = len(self.test_df) if not self.test_df.empty else 0
		fail_count = len(self.test_df[self.test_df.get('Result', '') == 'FAIL']) if not self.test_df.empty and 'Result' in self.test_df.columns else 0
		
		return [
			{'Section': 'UNIT INFO', 'Category': 'Unit Information', 'Metric': '', 'Value': '', 'Status': '', 'Details': ''},
			{'Section': 'UNIT INFO', 'Category': '', 'Metric': 'Visual ID', 'Value': visual_id, 'Status': '', 'Details': ''},
			{'Section': 'UNIT INFO', 'Category': '', 'Metric': 'First Defeature', 'Value': first_date, 'Status': '', 'Details': first_exp},
			{'Section': 'UNIT INFO', 'Category': '', 'Metric': 'Last Defeature', 'Value': last_date, 'Status': '', 'Details': last_exp},
			{'Section': 'UNIT INFO', 'Category': '', 'Metric': 'Total Experiments', 'Value': str(total_experiments), 'Status': '', 'Details': f'{total_tests} total test runs'},
			{'Section': 'UNIT INFO', 'Category': '', 'Metric': 'Total Failures', 'Value': str(fail_count), 'Status': '', 'Details': f'{total_tests - fail_count} passes'},
			{'Section': '', 'Category': '', 'Metric': '', 'Value': '', 'Status': '', 'Details': ''},
		]
	
	def _create_reproduction_section(self):
		"""Create reproduction analysis section"""
		repro_status, repro_experiments = self._analyze_reproduction()
		repro_configs = self._get_repro_voltage_configs(repro_experiments)
		
		rows = [
			{'Section': 'REPRODUCTION', 'Category': 'Reproduction Analysis', 'Metric': '', 'Value': '', 'Status': '', 'Details': ''},
			{'Section': 'REPRODUCTION', 'Category': '', 'Metric': 'Reproducible', 'Value': repro_status, 'Status': repro_status, 'Details': f'{len(repro_experiments)} experiments with 100% fail rate'},
		]
		
		if repro_experiments:
			# Show repro experiments grouped by type
			baseline_repros = [e for e in repro_experiments if 'Baseline' in e or 'BaseRepro' in e]
			voltage_repros = [e for e in repro_experiments if 'Voltage' in e or 'vcfg' in e or 'vbump' in e]
			freq_repros = [e for e in repro_experiments if 'Frequency' in e or '_f' in e]
			other_repros = [e for e in repro_experiments if e not in baseline_repros + voltage_repros + freq_repros]
			
			if baseline_repros:
				rows.append({'Section': 'REPRODUCTION', 'Category': '', 'Metric': 'Baseline Repro', 'Value': 'YES', 'Status': 'YES', 'Details': ', '.join(baseline_repros)})
			else:
				rows.append({'Section': 'REPRODUCTION', 'Category': '', 'Metric': 'Baseline Repro', 'Value': 'NO', 'Status': 'NO', 'Details': 'No 100% reproducible baseline'})
			
			if voltage_repros:
				rows.append({'Section': 'REPRODUCTION', 'Category': '', 'Metric': 'Voltage Repro', 'Value': 'YES', 'Status': 'YES', 'Details': f'{len(voltage_repros)} voltage conditions reproduce'})
			
			if freq_repros:
				rows.append({'Section': 'REPRODUCTION', 'Category': '', 'Metric': 'Frequency Repro', 'Value': 'YES', 'Status': 'YES', 'Details': f'{len(freq_repros)} frequency conditions reproduce'})
			
			if other_repros:
				rows.append({'Section': 'REPRODUCTION', 'Category': '', 'Metric': 'Other Repro', 'Value': 'YES', 'Status': 'YES', 'Details': ', '.join(other_repros[:3])})
		
		# Add voltage conditions used for repro
		if repro_configs:
			rows.append({'Section': 'REPRODUCTION', 'Category': '', 'Metric': 'Repro Voltage Conditions', 'Value': '', 'Status': '', 'Details': ''})
			for config in repro_configs[:5]:  # Top 5 configs
				rows.append({'Section': 'REPRODUCTION', 'Category': '', 'Metric': '', 'Value': config, 'Status': '', 'Details': ''})
		
		rows.append({'Section': '', 'Category': '', 'Metric': '', 'Value': '', 'Status': '', 'Details': ''})
		return rows
	
	def _create_characterization_section(self):
		"""Create voltage/frequency characterization section"""
		voltage_analysis = self._analyze_voltage_ranges()
		freq_analysis = self._analyze_frequency_ranges()
		core_license_info = self._analyze_core_license_detailed()
		
		rows = [
			{'Section': 'CHARACTERIZATION', 'Category': 'Characterization Results', 'Metric': '', 'Value': '', 'Status': '', 'Details': ''},
		]
		
		# Voltage Analysis
		if voltage_analysis:
			rows.append({'Section': 'CHARACTERIZATION', 'Category': '', 'Metric': 'Voltage Sensitivity', 'Value': '', 'Status': '', 'Details': ''})
			for rail, data in voltage_analysis.items():
				status = 'FAIL' if data['fail_range'] != 'N/A' else 'PASS'
				rows.append({
					'Section': 'CHARACTERIZATION',
					'Category': '',
					'Metric': f'  {rail}',
					'Value': f"PASS: {data['pass_range']} | FAIL: {data['fail_range']}",
					'Status': status,
					'Details': data['content']
				})
		else:
			rows.append({'Section': 'CHARACTERIZATION', 'Category': '', 'Metric': 'Voltage Sensitivity', 'Value': 'Not Tested', 'Status': '', 'Details': ''})
		
		# Frequency Analysis
		if freq_analysis:
			rows.append({'Section': 'CHARACTERIZATION', 'Category': '', 'Metric': 'Frequency Sensitivity', 'Value': '', 'Status': '', 'Details': ''})
			for rail, data in freq_analysis.items():
				status = 'FAIL' if data['fail_range'] != 'N/A' else 'PASS'
				rows.append({
					'Section': 'CHARACTERIZATION',
					'Category': '',
					'Metric': f'  {rail}',
					'Value': f"PASS: {data['pass_range']} | FAIL: {data['fail_range']}",
					'Status': status,
					'Details': data['content']
				})
		else:
			rows.append({'Section': 'CHARACTERIZATION', 'Category': '', 'Metric': 'Frequency Sensitivity', 'Value': 'Not Tested', 'Status': '', 'Details': ''})
		
		# Core License
		if core_license_info:
			rows.append({'Section': 'CHARACTERIZATION', 'Category': '', 'Metric': 'Core License Analysis', 'Value': '', 'Status': '', 'Details': ''})
			for info in core_license_info:
				rows.append({
					'Section': 'CHARACTERIZATION',
					'Category': '',
					'Metric': f"  {info['core']}",
					'Value': info['status'],
					'Status': info['status'],
					'Details': info['details']
				})
		else:
			rows.append({'Section': 'CHARACTERIZATION', 'Category': '', 'Metric': 'Core License Analysis', 'Value': 'Not Tested', 'Status': '', 'Details': ''})
		
		rows.append({'Section': '', 'Category': '', 'Metric': '', 'Value': '', 'Status': '', 'Details': ''})
		return rows
	
	def _create_failure_analysis_section(self):
		"""Create failure analysis section with top MCAs"""
		top_mcas = self._get_top_mcas()
		
		rows = [
			{'Section': 'FAILURE', 'Category': 'Failure Analysis', 'Metric': '', 'Value': '', 'Status': '', 'Details': ''},
		]
		
		if top_mcas:
			rows.append({'Section': 'FAILURE', 'Category': '', 'Metric': 'Top 5 MCAs', 'Value': '', 'Status': '', 'Details': 'Most common failure signatures'})
			for i, (mca, count) in enumerate(top_mcas, 1):
				rows.append({
					'Section': 'FAILURE',
					'Category': '',
					'Metric': f'  #{i}',
					'Value': mca,
					'Status': '',
					'Details': f'Occurrences: {count}'
				})
		else:
			rows.append({'Section': 'FAILURE', 'Category': '', 'Metric': 'Top MCAs', 'Value': 'No MCA data', 'Status': '', 'Details': ''})
		
		rows.append({'Section': '', 'Category': '', 'Metric': '', 'Value': '', 'Status': '', 'Details': ''})
		return rows
	
	def _create_content_section(self):
		"""Create content coverage section"""
		content_coverage = self._analyze_content_coverage()
		
		rows = [
			{'Section': 'CONTENT', 'Category': 'Content Coverage', 'Metric': '', 'Value': '', 'Status': '', 'Details': ''},
		]
		
		for content_type, data in content_coverage.items():
			status = 'FAIL' if data['fail_count'] > 0 else ('PASS' if data['tested'] else 'NOT_RUN')
			rows.append({
				'Section': 'CONTENT',
				'Category': '',
				'Metric': content_type,
				'Value': f"PASS: {data['pass_count']} | FAIL: {data['fail_count']}",
				'Status': status,
				'Details': data['details']
			})
		
		return rows
	
	
	# ==================== HELPER METHODS ====================
	
	def _get_visual_id(self):
		"""Extract Visual ID from test data"""
		if 'VID' in self.test_df.columns:
			visual_ids = self.test_df['VID'].dropna().unique()
			if len(visual_ids) > 0:
				return str(visual_ids[0])
		if 'Visual_ID' in self.test_df.columns:
			visual_ids = self.test_df['Visual_ID'].dropna().unique()
			if len(visual_ids) > 0:
				return str(visual_ids[0])
		return 'N/A'
	
	def _get_first_experiment(self):
		"""Get first experiment name and date"""
		if self.test_df.empty:
			return 'N/A', 'N/A'
		
		# Sort by Folder (contains date)
		if 'Folder' in self.test_df.columns:
			sorted_df = self.test_df.sort_values('Folder')
			first_row = sorted_df.iloc[0]
			folder = first_row.get('Folder', '')
			# Extract date from folder (format: YYYYMMDD_HHMMSS_...)
			date_match = re.match(r'(\d{8})_(\d{6})', folder)
			if date_match:
				date_str = f"{date_match.group(1)}"
				exp_name = folder.split('_', 2)[2] if len(folder.split('_')) > 2 else folder
				return exp_name, date_str
		
		first_row = self.test_df.iloc[0]
		return first_row.get('Folder', 'N/A'), 'N/A'
	
	def _get_last_experiment(self):
		"""Get last experiment name and date"""
		if self.test_df.empty:
			return 'N/A', 'N/A'
		
		# Sort by Folder (contains date)
		if 'Folder' in self.test_df.columns:
			sorted_df = self.test_df.sort_values('Folder')
			last_row = sorted_df.iloc[-1]
			folder = last_row.get('Folder', '')
			# Extract date from folder (format: YYYYMMDD_HHMMSS_...)
			date_match = re.match(r'(\d{8})_(\d{6})', folder)
			if date_match:
				date_str = f"{date_match.group(1)}"
				exp_name = folder.split('_', 2)[2] if len(folder.split('_')) > 2 else folder
				return exp_name, date_str
		
		last_row = self.test_df.iloc[-1]
		return last_row.get('Folder', 'N/A'), 'N/A'
	
	def _analyze_reproduction(self):
		"""
		Analyze if unit failure was consistently reproduced
		Returns: (status, list of experiment names)
		"""
		if self.experiment_summary_df.empty:
			return 'N/A', []
		
		repro_experiments = []
		
		# Look for experiments with 100% fail rate (all FAIL, no mixed status)
		for _, row in self.experiment_summary_df.iterrows():
			status = str(row.get('Status', ''))
			exp_name = row.get('Experiment Name', 'Unknown')
			
			# Check for pure FAIL status (e.g., "FAIL 5" but not "PASS 2 | FAIL 3")
			if 'FAIL' in status and 'PASS' not in status and '|' not in status:
				repro_experiments.append(exp_name)
		
		if len(repro_experiments) > 0:
			return 'YES', repro_experiments
		elif len(self.experiment_summary_df) > 0:
			return 'FLAKY', []
		else:
			return 'NO', []
	
	def _get_repro_voltage_configs(self, repro_experiments):
		"""Extract voltage configurations used for reproducible experiments"""
		if not repro_experiments:
			return []
		
		configs = []
		for exp_name in repro_experiments:
			# Parse voltage info from experiment name
			# Examples: "vcfg_vbump_ia_v0_08", "CFC_Voltage_check_System_vcfg_vbump_cfc_v0"
			
			# IA voltage
			ia_match = re.search(r'ia[_]v(\d+)[_]?(\d*)', exp_name, re.IGNORECASE)
			if ia_match:
				voltage = f"{ia_match.group(1)}"
				if ia_match.group(2):
					voltage += f".{ia_match.group(2)}"
				configs.append(f"IA VBUMP: {voltage}V")
			
			# CFC voltage  
			cfc_match = re.search(r'cfc[_]v(\d+)[_]?(\d*)', exp_name, re.IGNORECASE)
			if cfc_match:
				voltage = f"{cfc_match.group(1)}"
				if cfc_match.group(2):
					voltage += f".{cfc_match.group(2)}"
				configs.append(f"CFC VBUMP: {voltage}V")
			
			# Frequency info
			freq_match = re.search(r'[_]f(\d+)', exp_name, re.IGNORECASE)
			if freq_match:
				freq = freq_match.group(1)
				# Determine which rail
				if 'ia' in exp_name.lower():
					configs.append(f"IA Frequency: {freq}x")
				elif 'cfc' in exp_name.lower():
					configs.append(f"CFC Frequency: {freq}x")
		
		return list(set(configs))  # Remove duplicates
	
	def _analyze_voltage_ranges(self):
		"""Analyze voltage pass/fail ranges by content type"""
		if self.experiment_summary_df.empty:
			return {}
		
		# Get voltage experiments
		voltage_exps = self.experiment_summary_df[
			self.experiment_summary_df['Type'] == 'Voltage'
		]
		
		if voltage_exps.empty:
			return {}
		
		voltage_data = {}
		
		# Process each voltage experiment
		for _, row in voltage_exps.iterrows():
			char = str(row.get('Characterization', ''))
			content = row.get('Used Content', 'Unknown')
			
			# Parse IA voltage
			ia_match = re.search(r'IA[^:]*:\s*FAIL\s*<=\s*([\d.]+)[^|]*\|\s*PASS\s*>=\s*([\d.]+)', char)
			if ia_match:
				fail_voltage = ia_match.group(1)
				pass_voltage = ia_match.group(2)
				if 'IA VBUMP' not in voltage_data:
					voltage_data['IA VBUMP'] = {'pass_range': f'>= {pass_voltage}V', 'fail_range': f'<= {fail_voltage}V', 'content': content}
			
			# Parse CFC voltage
			cfc_match = re.search(r'CFC[^:]*:\s*FAIL\s*<=\s*([\d.]+)[^|]*\|\s*PASS\s*>=\s*([\d.]+)', char)
			if cfc_match:
				fail_voltage = cfc_match.group(1)
				pass_voltage = cfc_match.group(2)
				if 'CFC VBUMP' not in voltage_data:
					voltage_data['CFC VBUMP'] = {'pass_range': f'>= {pass_voltage}V', 'fail_range': f'<= {fail_voltage}V', 'content': content}
		
		return voltage_data
	
	def _analyze_frequency_ranges(self):
		"""Analyze frequency pass/fail ranges by content type"""
		if self.experiment_summary_df.empty:
			return {}
		
		# Get frequency experiments
		freq_exps = self.experiment_summary_df[
			self.experiment_summary_df['Type'] == 'Frequency'
		]
		
		if freq_exps.empty:
			return {}
		
		freq_data = {}
		
		# Process each frequency experiment
		for _, row in freq_exps.iterrows():
			char = str(row.get('Characterization', ''))
			content = row.get('Used Content', 'Unknown')
			
			# Parse IA frequency
			ia_match = re.search(r'IA[^:]*:\s*FAIL\s*<=\s*(\d+)x[^|]*\|\s*PASS\s*>=\s*(\d+)x', char)
			if ia_match:
				fail_freq = ia_match.group(1)
				pass_freq = ia_match.group(2)
				if 'IA Ratio' not in freq_data:
					freq_data['IA Ratio'] = {'pass_range': f'>= {pass_freq}x', 'fail_range': f'<= {fail_freq}x', 'content': content}
			
			# Parse CFC frequency
			cfc_match = re.search(r'CFC[^:]*:\s*FAIL\s*<=\s*(\d+)x[^|]*\|\s*PASS\s*>=\s*(\d+)x', char)
			if cfc_match:
				fail_freq = cfc_match.group(1)
				pass_freq = cfc_match.group(2)
				if 'CFC Ratio' not in freq_data:
					freq_data['CFC Ratio'] = {'pass_range': f'>= {pass_freq}x', 'fail_range': f'<= {fail_freq}x', 'content': content}
		
		return freq_data
	
	def _analyze_core_license_detailed(self):
		"""Analyze Core License experiments with detailed information"""
		if self.experiment_summary_df.empty:
			return []
		
		core_license_info = []
		
		# Look for Core License experiments
		for _, row in self.experiment_summary_df.iterrows():
			exp_name = row.get('Experiment Name', '')
			
			# Check if this is a Core License experiment
			if 'Core' in exp_name and ('IA32' in exp_name or 'Core' in exp_name):
				status = str(row.get('Status', ''))
				content = row.get('Used Content', 'Unknown')
				
				# Extract core number
				core_match = re.search(r'Core(\d+)', exp_name)
				core_num = core_match.group(1) if core_match else 'Unknown'
				
				# Extract test type (LOOPS, SSE, AVX2, AVX3, etc.)
				test_type = 'Unknown'
				if 'LOOPS' in exp_name:
					test_type = 'LOOPS'
				elif 'SSE' in exp_name:
					test_type = 'SSE'
				elif 'AVX2' in exp_name:
					test_type = 'AVX2'
				elif 'AVX3' in exp_name:
					test_type = 'AVX3'
				
				# Extract frequency info
				freq_info = ''
				ia_freq = re.search(r'ia_f(\d+)', exp_name)
				cfc_freq = re.search(r'cfc_f(\d+)', exp_name)
				if ia_freq and cfc_freq:
					freq_info = f"IA: {ia_freq.group(1)}x, CFC: {cfc_freq.group(1)}x"
				
				# Determine PASS/FAIL status
				result_status = 'PASS' if 'PASS' in status and 'FAIL' not in status else 'FAIL'
				
				details = f"{test_type} | Content: {content}"
				if freq_info:
					details += f" | Freq: {freq_info}"
				
				core_license_info.append({
					'core': f"Core {core_num}",
					'status': result_status,
					'details': details
				})
		
		return core_license_info
	
	def _get_top_mcas(self):
		"""Get top 5 MCAs from FrameworkFails data"""
		if self.fail_info_df.empty or 'MCA' not in self.fail_info_df.columns:
			return []
		
		# Count MCA occurrences
		mca_counter = Counter()
		for mca in self.fail_info_df['MCA'].dropna():
			mca_str = str(mca).strip()
			if mca_str and mca_str.lower() not in ['none', 'nan', '', 'n/a']:
				mca_counter[mca_str] += 1
		
		# Return top 5
		return mca_counter.most_common(5)
	
	def _analyze_content_coverage(self):
		"""Analyze content coverage with pass/fail counts"""
		coverage = {}
		
		for content_type, keywords in self.content_mappings.items():
			# Find all tests for this content type
			content_tests = pd.DataFrame()
			
			if 'Used Content' in self.test_df.columns:
				for keyword in keywords:
					matching = self.test_df[
						self.test_df['Used Content'].str.contains(keyword, case=False, na=False)
					]
					content_tests = pd.concat([content_tests, matching])
			
			if content_tests.empty:
				coverage[content_type] = {
					'tested': False,
					'pass_count': 0,
					'fail_count': 0,
					'details': 'Not RUN'
				}
			else:
				# Count pass/fail
				if 'Result' in content_tests.columns:
					pass_count = len(content_tests[content_tests['Result'] == 'PASS'])
					fail_count = len(content_tests[content_tests['Result'] == 'FAIL'])
					total = len(content_tests)
					
					# Get unique failing seeds
					failing_seeds = []
					if fail_count > 0 and 'Failing_Content' in content_tests.columns:
						for fc in content_tests['Failing_Content'].dropna():
							failing_seeds.extend(str(fc).split(','))
					
					unique_fails = len(set([s.strip() for s in failing_seeds if s.strip()]))
					
					details = f"{unique_fails} unique failures" if fail_count > 0 else f"All {pass_count} tests passed"
					
					coverage[content_type] = {
						'tested': True,
						'pass_count': pass_count,
						'fail_count': fail_count,
						'details': details
					}
				else:
					coverage[content_type] = {
						'tested': True,
						'pass_count': 0,
						'fail_count': len(content_tests),
						'details': f'{len(content_tests)} tests run'
					}
		
		return coverage
