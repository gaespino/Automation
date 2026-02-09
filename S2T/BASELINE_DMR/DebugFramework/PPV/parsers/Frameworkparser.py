import zipfile
import os
import pandas as pd
import colorama
from tabulate import tabulate
from colorama import Fore, Style, Back
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo
import re
import sys

# Import ExcelReportBuilder for flexible Excel generation
try:
	from ..utils.ExcelReportBuilder import ExcelReportBuilder, SheetConfig
except ImportError:
	from utils.ExcelReportBuilder import ExcelReportBuilder, SheetConfig

# Import dragon_bucketing module for VVAR decoding
decoder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Decoder')
sys.path.append(decoder_path)
try:
	import dragon_bucketing
except ImportError:
	print("Warning: dragon_bucketing module not found. VVAR decoding will be skipped.")
	dragon_bucketing = None

# Import FrameworkAnalyzer for ExperimentSummary generation
try:
	from .FrameworkAnalyzer import ExperimentSummaryAnalyzer, create_experiment_summary
except ImportError:
	try:
		from FrameworkAnalyzer import ExperimentSummaryAnalyzer, create_experiment_summary
	except ImportError:
		print("Warning: FrameworkAnalyzer module not found. ExperimentSummary generation will be skipped.")
		ExperimentSummaryAnalyzer = None
		create_experiment_summary = None


class LogFileParser:

	def __init__(self, zip_file_path, content_type, exclusion_string='pysv', casesens=False):
		self.zip_file_path = zip_file_path
		self.content_type = content_type.lower()  # Ensure content type is case-insensitive
		self.exclusion_string = exclusion_string
		self.casesens = casesens
		self.pass_strings = ["Test Complete"]
		self.fail_strings = ["exit: fail", "not ok"]
		self.hang_strings = ["running MerlinX.efi"]
		self.check_strings = [r"CHANGING BACK TO DIR: FS1:\EFI"]
		self.skip_strings = []

	def set_zip_file_path(self, zip_path):
		self.zip_file_path = zip_path

	def set_pass_strings(self, pass_strings):
		self.pass_strings = [p.lower() for p in pass_strings] if not self.casesens else pass_strings

	def set_fail_strings(self, fail_strings):
		self.fail_strings = [f.lower() for f in fail_strings] if not self.casesens else fail_strings

	def set_hang_strings(self, hang_strings):
		self.hang_strings = [h.lower() for h in hang_strings] if not self.casesens else hang_strings

	def set_check_strings(self, check_strings):
		self.check_strings = [c.lower() for c in check_strings] if not self.casesens else check_strings

	def set_skip_strings(self, skip_strings):
		self.skip_strings = [s.lower() for s in skip_strings] if not self.casesens else skip_strings

	def parse_log_files_in_zip(self):
		zipped_log_data = {}
		with zipfile.ZipFile(self.zip_file_path, 'r') as zip_ref:
			for log_file in zip_ref.namelist():
				if log_file.endswith('.log') and self.exclusion_string not in log_file:
					with zip_ref.open(log_file) as log_file_ref:
						# Try UTF-8 first, then fall back to latin-1 (which accepts all byte values)
						try:
							log_content = log_file_ref.read().decode('utf-8')
						except UnicodeDecodeError:
							try:
								log_content = log_file_ref.read().decode('latin-1')
							except:
								# If all else fails, use UTF-8 with error replacement
								log_file_ref.seek(0)  # Reset file pointer
								log_content = log_file_ref.read().decode('utf-8', errors='replace')
						# Use the content type to determine which parsing method to call
						if self.content_type == 'efi':
							result = self.parse_efi_log(log_content)
						elif self.content_type == 'linux':
							result = self.parse_linux_log(log_content)
						elif self.content_type == 'sandstone':
							result = self.parse_sandstone_log(log_content)
						elif self.content_type == 'imunch':
							result = self.parse_linux_log(log_content)
						elif self.content_type == 'tsl':
							result = self.parse_tsl_log(log_content)
						elif self.content_type == 'python':
							result = self.parse_python_log(log_content)
						elif self.content_type == 'other':
							result = self.parse_efi_log(log_content)
						else:
							result = []
						print(f"Result for {log_file}: {result}")
						zipped_log_data[log_file] = result #','.join(result)

		return zipped_log_data

	def parse_efi_log(self, log_content):
		lines = log_content.splitlines()
		fail_results = set()

		for line in lines:
			if any((skip_string in line) if self.casesens else (skip_string.lower() in line.lower()) for skip_string in self.skip_strings):
				continue

			for search_string in self.fail_strings:
				if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
					obj_file = self.extract_obj_from_line(line)
					fail_results.add(obj_file.replace('.obj', '') + '_FAIL' if obj_file else "FAIL")

		if not fail_results:
			for line in reversed(lines):
				if any((skip_string in line) if self.casesens else (skip_string.lower() in line.lower()) for skip_string in self.skip_strings):
					continue

				for search_string in self.pass_strings:
					if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
						fail_results.add("PASS")
						break
				else:
					for search_string in self.check_strings:
						if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
							fail_results.add("_CHECK_MCA")
							break
					else:
						for search_string in self.hang_strings:
							if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
								obj_file = self.extract_obj_from_line(line)
								fail_results.add(obj_file.replace('.obj', '') + '_HANG' if obj_file else "HANG")
								break

				if "PASS" in fail_results or "_CHECK_MCA" in fail_results or any(obj.endswith('_HANG') for obj in fail_results):
					break

		return list(fail_results)

	def extract_obj_from_line(self, line):
		start = line.rfind('\\') + 1
		end = line.rfind('.obj')
		if start != -1 and end != -1:
			return line[start:end + 4]
		return None

	def parse_sandstone_log(self, log_content):
		lines = log_content.splitlines()
		fail_results = set()

		# Check for fail conditions
		for line in lines:
			if any((skip_string in line) if self.casesens else (skip_string.lower() in line.lower()) for skip_string in self.skip_strings):
				continue

			for search_string in self.fail_strings:
				if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
					# Extract the failing test information
					parts = line.strip(search_string).split(" ")
					if len(parts) >= 2:
						fail_results.add(f"{parts[1]}")
					else:
						fail_results.add("FAIL")

		# If no fail conditions are found, check for pass conditions
		if not fail_results:
			for line in lines:
				if any((skip_string in line) if self.casesens else (skip_string.lower() in line.lower()) for skip_string in self.skip_strings):
					continue

				for search_string in self.pass_strings:
					if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
						fail_results.add("PASS")
						break

		# If neither pass nor fail conditions are found, default to "HANG"
		if not fail_results:
			fail_results.add("HANG")

		return list(fail_results)

	def parse_linux_log(self, log_content):
		lines = log_content.splitlines()
		fail_results = set()

		# Check for fail conditions
		for line in lines:
			if any((skip_string in line) if self.casesens else (skip_string.lower() in line.lower()) for skip_string in self.skip_strings):
				continue

			for search_string in self.fail_strings:
				if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
					# Extract the failing test information
					parts = line.strip(search_string)
					if len(parts) > 2:
						fail_results.add(f"{parts}")
					else:
						fail_results.add("FAIL")

		# If no fail conditions are found, check for pass conditions
		if not fail_results:
			for line in lines:
				if any((skip_string in line) if self.casesens else (skip_string.lower() in line.lower()) for skip_string in self.skip_strings):
					continue

				for search_string in self.pass_strings:
					if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
						fail_results.add("PASS")
						break

		# If neither pass nor fail conditions are found, default to "HANG"
		if not fail_results:
			fail_results.add("HANG")

		return list(fail_results)

	def parse_tsl_log(self, log_content):
		lines = log_content.splitlines()
		fail_results = set()

		# Check for fail conditions
		for line in lines:
			if any((skip_string in line) if self.casesens else (skip_string.lower() in line.lower()) for skip_string in self.skip_strings):
				continue

			for search_string in self.fail_strings:
				if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
					# Extract the failing test information
					parts = line.strip(search_string)
					if len(parts) > 2:
						fail_results.add(f"{parts}")
					else:
						fail_results.add("FAIL")

		# If no fail conditions are found, check for pass conditions
		if not fail_results:
			for line in reversed(lines):
				if any((skip_string in line) if self.casesens else (skip_string.lower() in line.lower()) for skip_string in self.skip_strings):
					continue

				for search_string in self.pass_strings:
					if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
						fail_results.add("PASS")
						break

				else:
					for search_string in self.check_strings: # empty for TSL
						if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
							fail_results.add("_CHECK_MCA")
							break
					else:
						for search_string in self.hang_strings:
							if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
								obj_file = self.extract_obj_from_line(line)
								fail_results.add(obj_file.replace('.obj', '') + '_HANG' if obj_file else "HANG")
								break

				if "PASS" in fail_results or "_CHECK_MCA" in fail_results or any(obj.endswith('_HANG') for obj in fail_results):
					break

		return list(fail_results)

	def parse_python_log(self, log_content):
		lines = log_content.splitlines()
		fail_results = set()

		for line in lines:
			if any((skip_string in line) if self.casesens else (skip_string.lower() in line.lower()) for skip_string in self.skip_strings):
				continue

			for search_string in self.fail_strings:
				if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
					fail_results.add("FAIL")

		if not fail_results:
			for line in reversed(lines):
				if any((skip_string in line) if self.casesens else (skip_string.lower() in line.lower()) for skip_string in self.skip_strings):
					continue

				for search_string in self.pass_strings:
					if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
						fail_results.add("PASS")
						break
				else:
					for search_string in self.hang_strings:
						if (search_string in line) if self.casesens else (search_string.lower() in line.lower()):
							fail_results.add("HANG")
							break

		return list(fail_results)

class LogSummaryParser:

	def __init__(self, excel_path_dict, test_df, product = 'GNR'):
		self.excel_path_dict = excel_path_dict
		self.test_df = test_df
		self.product = product
		self.search_word = 'CORE' if product == 'GNR' else 'MODULE'

	def parse_mca_tabs_from_files(self):
		# Initialize a dictionary to store results
		report_data = []
		excel_path_dict = self.excel_path_dict
		# Initialize a list to store MCA data

		# Define the tabs to parse
		tabs_to_parse = ['CHA_MCAS', 'LLC_MCAS', 'CORE_MCAS', 'UBOX']

		# Iterate over each Excel file in the path dictionary
		for experiment_name, info in excel_path_dict.items():
			excel_file_path = info['path']
			# Load the Excel file
			print(excel_file_path)
			excel_data = pd.read_excel(excel_file_path, sheet_name=None, engine='openpyxl')

			# Iterate over each tab
			for tab in tabs_to_parse:
				if tab in excel_data:
					df = excel_data[tab]
					for _, row in df.iterrows():
						# Extract the run value from the 'Run' column
						run_value = str(row['Run']).split('-')[0]

						# Extract MCA data based on the tab
						if tab == 'CHA_MCAS':
							report_data.append(self._check_mesh_data(row, experiment_name, run_value))
						elif tab == 'LLC_MCAS':
							report_data.append(self._check_llc_data( row, experiment_name, run_value))
						elif tab == 'CORE_MCAS':
							report_data.append(self._check_core_data(row, experiment_name, run_value))
						elif tab == 'UBOX':
							result = self._check_ubox_data( row, experiment_name, run_value)
							if result:  # Only append if valid UBOX entry
								report_data.append(result)

		# Convert the MCA data to a DataFrame
		mca_df = pd.DataFrame(report_data)

		# Check if mca_df is empty and initialize with default columns if necessary
		if mca_df.empty:
			mca_df = pd.DataFrame(columns=['Failed MCA', 'Content', 'Experiment', 'Run Value'])
			unique_mcas_df = pd.DataFrame(columns=['Failed MCA', 'Content', 'Fail_Count'])

		else:
			# Generate unique MCA values and their counts

			unique_mcas_df = mca_df.groupby('Failed MCA').agg(
				Content=('Content', lambda x: ', '.join(set(x))),
				Fail_Count=('Failed MCA', 'size')
			).reset_index()

		return unique_mcas_df, mca_df

	def get_experiment_name(self, experiment_number):
		# Filter the DataFrame directly, ensuring 'Test File' column does not contain NaN values
		matching_row = self.test_df[self.test_df['Test File'].notna() & self.test_df['Test File'].str.startswith(f"{experiment_number}_")]

		if not matching_row.empty:
			return matching_row.iloc[0]['Experiment']
		return f"Experiment {experiment_number}"

	# Product-specific MCA format configuration
	# Makes it easy to add new products in the future - just add a new entry here
	@staticmethod
	def _get_product_config():
		"""Returns product-specific configuration for MCA parsing.

		To add a new product:
		1. Add product key to the dictionary
		2. Specify 'domain_prefix' (e.g., 'CDIE' or 'CBB')
		3. Specify 'domain_field' (column name for domain, e.g., 'Compute' or 'CBB')
		4. Specify 'core_field' (column name for core/module)
		5. Add any product-specific fields in 'extra_cha_fields' if needed
		"""
		return {
			'GNR': {
				'domain_prefix': 'CDIE',
				'domain_field': 'Compute',
				'core_field': 'CORE',
				'extra_cha_fields': ['CHA']  # No extra fields for GNR
			},
			'CWF': {
				'domain_prefix': 'CDIE',
				'domain_field': 'Compute',
				'core_field': 'MODULE',
				'extra_cha_fields': ['CHA']  # No extra fields for CWF
			},
			'DMR': {
				'domain_prefix': 'CBB',
				'domain_field': 'CBB',
				'core_field': 'MODULE',
				'extra_cha_fields': ['ENV', 'instance']  # DMR-specific CHA fields
			}
		}

	@staticmethod
	def _get_ubox_config():
		"""Returns UBOX-specific configuration.

		UBOX format is consistent across all products:
		- Extracts event name from NCEVENT field (last part after '__')
		- Includes FirstError - Location field
		- Filters out invalid locations ('0x0' or NaN)
		"""
		return {
			'event_field': 'NCEVENT',
			'location_field': 'FirstError - Location',
			'invalid_locations': ['0x0', '0', None],
			'event_separator': '__'  # Separator for parsing NCEVENT
		}

	@staticmethod
	def _build_mca_string(config, row, unit_fields, mca_type, tab_name):
		"""Build MCA string with error handling.

		Args:
			config: Product configuration dictionary
			row: DataFrame row with MCA data
			unit_fields: List of field names to include in MCA string
			mca_type: Type of MCA (for error messages)
			tab_name: Name of the tab being processed

		Returns:
			Formatted MCA string or None if error
		"""
		try:
			parts = [f"{config['domain_prefix']}{row[config['domain_field']]}"]

			for field in unit_fields:
				if field not in row:
					print(f"Warning: Field '{field}' not found in {tab_name} row for {mca_type}")
					return None
				parts.append(str(row[field]))

			# Add MC DECODE at the end
			if 'MC DECODE' in row:
				parts.append(str(row['MC DECODE']))
			else:
				print(f"Warning: 'MC DECODE' field not found in {tab_name} row")
				return None

			return ':'.join(parts)

		except KeyError as e:
			print(f"Error building {mca_type} string for {tab_name}: Missing key {e}")
			return None
		except Exception as e:
			print(f"Unexpected error building {mca_type} string for {tab_name}: {e}")
			return None

	def _check_mesh_data(self, row, experiment_name, run_value):
		"""Parse CHA_MCAS tab data with product-specific format."""
		try:
			configs = LogSummaryParser._get_product_config()
			product = self.product

			if product not in configs:
				print(f"Error: Unknown product '{product}' in CHA_MCAS parsing. Supported: {list(configs.keys())}")
				return {'Failed MCA': 'UNKNOWN_PRODUCT', 'Content': 'CHA_MCAs', 'Experiment': experiment_name, 'Run Value': run_value}

			config = configs[product]
			print(f"Processing CHA_MCAS for product: {product}, experiment: {experiment_name}")

			# Build unit fields list (CHA + any extra product-specific fields)
			unit_fields = config.get('extra_cha_fields', [])

			mca_string = LogSummaryParser._build_mca_string(config, row, unit_fields, 'CHA_MCA', 'CHA_MCAS')

			if mca_string is None:
				print(f"Failed to build CHA MCA string for {product}")
				mca_string = 'PARSE_ERROR'

			return {
				'Failed MCA': mca_string,
				'Content': 'CHA_MCAs',
				'Experiment': experiment_name,
				'Run Value': run_value
			}

		except Exception as e:
			print(f"Exception in _check_mesh_data for {product}: {e}")
			return {'Failed MCA': 'EXCEPTION', 'Content': 'CHA_MCAs', 'Experiment': experiment_name, 'Run Value': run_value}

	def _check_llc_data(self, row, experiment_name, run_value):
		"""Parse LLC_MCAS tab data with product-specific format."""
		try:
			configs = LogSummaryParser._get_product_config()
			product = self.product
			if product not in configs:
				print(f"Error: Unknown product '{product}' in LLC_MCAS parsing. Supported: {list(configs.keys())}")
				return {'Failed MCA': 'UNKNOWN_PRODUCT', 'Content': 'LLC_MCAs', 'Experiment': experiment_name, 'Run Value': run_value}

			config = configs[product]
			print(f"Processing LLC_MCAS for product: {product}, experiment: {experiment_name}")

			# LLC format: domain::LLC::MC_DECODE
			unit_fields = ['LLC']

			mca_string = LogSummaryParser._build_mca_string(config, row, unit_fields, 'LLC_MCA', 'LLC_MCAS')

			if mca_string is None:
				print(f"Failed to build LLC MCA string for {product}")
				mca_string = 'PARSE_ERROR'

			return {
				'Failed MCA': mca_string,
				'Content': 'LLC_MCAs',
				'Experiment': experiment_name,
				'Run Value': run_value
			}

		except Exception as e:
			print(f"Exception in _check_llc_data for {product}: {e}")
			return {'Failed MCA': 'EXCEPTION', 'Content': 'LLC_MCAs', 'Experiment': experiment_name, 'Run Value': run_value}

	def _check_core_data(self, row, experiment_name, run_value):
		"""Parse CORE_MCAS tab data with product-specific format."""
		try:
			configs = LogSummaryParser._get_product_config()
			product = self.product
			if product not in configs:
				print(f"Error: Unknown product '{product}' in CORE_MCAS parsing. Supported: {list(configs.keys())}")
				return {'Failed MCA': 'UNKNOWN_PRODUCT', 'Content': 'CORE_MCAs', 'Experiment': experiment_name, 'Run Value': run_value}

			config = configs[product]
			print(f"Processing CORE_MCAS for product: {product}, experiment: {experiment_name}")

			# CORE format: domain::CORE/MODULE::ErrorType::MCACOD (note: doesn't use MC DECODE)
			try:
				parts = [
					f"{config['domain_prefix']}{row[config['domain_field']]}",
					str(row[config['core_field']]),
					str(row['ErrorType']),
					str(row['MCACOD (ErrDecode)'])
				]
				mca_string = '::'.join(parts)

			except KeyError as e:
				print(f"Error: Missing required field {e} in CORE_MCAS for {product}")
				mca_string = 'PARSE_ERROR'

			return {
				'Failed MCA': mca_string,
				'Content': 'CORE_MCAs',
				'Experiment': experiment_name,
				'Run Value': run_value
			}

		except Exception as e:
			print(f"Exception in _check_core_data for {product}: {e}")
			return {'Failed MCA': 'EXCEPTION', 'Content': 'CORE_MCAs', 'Experiment': experiment_name, 'Run Value': run_value}

	def _check_ubox_data(self, row, experiment_name, run_value):
		"""Parse UBOX tab data with error handling and validation.

		UBOX format: EventName::Location
		Filters out invalid or zero locations.
		"""
		try:
			config = LogSummaryParser._get_ubox_config()
			product = self.product

			print(f"Processing UBOX for product: {product}, experiment: {experiment_name}")

			# Validate required fields exist
			if config['event_field'] not in row:
				print(f"Error: '{config['event_field']}' field not found in UBOX row")
				return None

			if config['location_field'] not in row:
				print(f"Error: '{config['location_field']}' field not found in UBOX row")
				return None

			# Get location value
			location = row[config['location_field']]

			# Check if location is valid (not NaN and not in invalid list)
			if pd.isna(location):
				print(f"Skipping UBOX entry: Location is NaN")
				return None

			location_str = str(location).strip()
			if location_str in config['invalid_locations'] or location_str == '':
				print(f"Skipping UBOX entry: Invalid location '{location_str}'")
				return None

			# Extract event name from NCEVENT
			try:
				ncevent = str(row[config['event_field']])
				# Split by separator and take the last part
				event_parts = ncevent.split(config['event_separator'])
				event_name = event_parts[-1] if event_parts else ncevent

				if not event_name or event_name == 'nan':
					print(f"Error: Invalid event name extracted from NCEVENT: '{ncevent}'")
					return None

			except Exception as e:
				print(f"Error parsing NCEVENT field: {e}")
				return None

			# Build UBOX MCA string
			mca_string = f"{event_name}::{location_str}"
			print(f"  UBOX MCA: {mca_string}")

			return {
				'Failed MCA': mca_string,
				'Content': 'UBOX',
				'Experiment': experiment_name,
				'Run Value': run_value
			}

		except Exception as e:
			print(f"Exception in _check_ubox_data for {product}: {e}")
			return None  # Return None for UBOX errors to skip invalid entries

######################################################################################################################
###########################     Framework Report Scripts Below
######################################################################################################################

def framework_merge(file_dict, output_file, prefix = '', skip=[]):
	# List to hold dataframes
	all_data = {}

	# Iterate over all Excel files in the input folder
	for k, v in file_dict.items():
		file = file_dict[k]['path']
		testype = file_dict[k]['test_type']
		if testype in skip:
			formatted_print(f' >>> {testype.upper()} <<< {file}', Fore.MAGENTA, Back.LIGHTYELLOW_EX)
			continue

		if prefix != None:
			keyword = prefix
			excelfile = (file.endswith(f'{keyword}.xlsx') or file.endswith(f'{keyword}.xls')) or (prefix in file and '.xls' in file)
		else:
			keyword = ''
			excelfile = (file.endswith(f'{keyword}.xlsx') or file.endswith(f'{keyword}.xls'))


		if excelfile:
			file_path = file
			excel_data = pd.read_excel(file_path, sheet_name=None)

			for sheet_name, df in excel_data.items():
				if sheet_name not in all_data:
					all_data[sheet_name] = []
				all_data[sheet_name].append(df)

		formatted_print(f' >>> DONE <<< {file}', Fore.BLACK, Back.LIGHTGREEN_EX)

	# Create a writer object to write the merged data to a new Excel file
	with pd.ExcelWriter(output_file) as writer:
		for sheet_name, df_list in all_data.items():
			merged_df = pd.concat(df_list, ignore_index=True)
			merged_df.to_excel(writer, sheet_name=sheet_name, index=False)

	print(f"Framework Data Merged Excel file saved as {output_file}")

def parse_log_files(log_dict):
	# List to store test data
	test_data = []

	# Keywords to look for in the log files
	keywords = [
		"Unit QDF:",
		"Configuration:",
		"Voltage set to:",
		"HT Disabled (BigCore):",
		"Dis 2 Cores (Atomcore):",
		"Core License:",
		"Core Freq:",
		"Core Voltage:",
		"Mesh Freq:",
		"Mesh Voltage:",
		"Unit 600w Fuses Applied",
		"Running Content:",
		"Pass String:",
		"Fail String:"
	]

	# Process each log file
	for filename, info in log_dict.items():
		log_path = info['path']
		test_type = info['test_type']
		content_info = info['content']
		comments = info['comments']

		with open(log_path, 'r') as file:
			content = file.read()

		# Split the content based on the test start string
		tests = content.split("-- Test Start ---")

		# Extract path information
		#logfile_path = log_path.split(os.sep)
		path_parts = os.path.normpath(log_path).split(os.sep)
		if len(path_parts) >= 6:
			vid = path_parts[-5]
			platform = path_parts[-4]
			date = path_parts[-3]
			folder = path_parts[-2]

		# Process each test section
		for test in tests[1:]:  # Skip the first split part as it is before the first test start
			test_info = {
				'VID': vid,
				'Platform': platform,
				'Date': date,
				'Folder': folder,
				'Type': test_type
			}

			# Extract tdata information
			tdata_start = test.find("tdata_")
			if tdata_start != -1:
				tdata_end = test.find('\n', tdata_start)
				tdata_line = test[tdata_start:tdata_end].strip()
				tdata_parts = tdata_line.split("::")
				if len(tdata_parts) >= 5:
					test_info['Test Number'] = tdata_parts[0]
					test_info['Experiment'] = tdata_parts[1]
					test_info['PostCode'] = tdata_parts[3]
					test_info['Result'] = tdata_parts[2]
					test_info['Content Status'] = tdata_parts[4].strip()  # Strip whitespace/tabs
					test_info['Test File'] = f'{tdata_parts[0].strip("tdata_")}_{tdata_parts[1]}.log'


			# Extract keyword values
			for keyword in keywords:
				start = test.find(keyword)
				if start != -1:
					end = test.find('\n', start)
					value = test[start + len(keyword):end].strip()
					test_info[keyword.strip(':')] = value
				else:
					test_info[keyword.strip(':')] = None

			# Check for 600W Fuses Applied
			test_info['Unit 600w Fuses Applied'] = 'True' if "Unit 600w Fuses Applied" in test else 'False'
			test_info['Content Detail'] = content_info
			test_info['Comments'] = comments
			# Append the test information to the list
			test_data.append(test_info)

	# Create a DataFrame from the test data list
	test_df = pd.DataFrame(test_data)

	return test_df

def check_zip_data(zip_path_dict, skip_array, test_df):
	zip_results = []
	pass_array = []
	fail_array = []

	# Group by 'Folder' to aggregate pass and fail strings
	grouped_df = test_df.groupby('Folder').agg({
		'Pass String': lambda x: ','.join(x.dropna()),
		'Fail String': lambda x: ','.join(x.dropna())
	}).reset_index()

	for experiment, zip_files in zip_path_dict.items():
		zip_path = zip_files['path']
		test_type = zip_files['test_type']
		content_info = zip_files['content']
		comments = zip_files['comments']
		exp_df = test_df[(test_df['Folder'] == experiment)]

		if not exp_df.empty:
			pass_string = exp_df.iloc[0]['Pass String']
			fail_string = exp_df.iloc[0]['Fail String']

			# Split the concatenated strings and convert to sets to ensure uniqueness, then back to lists
			try:
				pass_array = list(set(pass_string.split(",")))
			except:
				pass_array = []

			try:
				fail_array = list(set(fail_string.split(",")))
			except:
				fail_array = []
		#fail_info_df[(fail_info_df['Log File'] == test_file) & (fail_info_df['Experiment'] == folder)]
		#for zip_file in zip_files:

		results = parse_zip_files(zip_file_path=zip_path, content=content_info, pass_array = pass_array, fail_array = fail_array, skip_array = skip_array, exclusion_string='pysv', casesens=False)

		for filename, data in results.items():
			zip_results.append({'Experiment': experiment, 'Content': content_info, 'Log File': filename, 'Log Fails': ', '.join(data)})

	return pd.DataFrame(zip_results)

def parse_zip_files(zip_file_path, content, pass_array = [], fail_array = [], skip_array = [], exclusion_string='pysv', casesens=False):

	linux_rules = {	'pass': ['exit: pass', "test_result: passed" , "Passed", "Result=SUCCESS"],
		  		'fail': ['exit: fail', "test_result: failed", "failed", "Result=FAILED"], 'hang': [], 'check': []}

	tsl_rules = {	'pass': ['exit: pass'],
		  		'fail': ['exit: fail', "not ok"], 'hang': ['.obj'], 'check': []}

	sandstone_rules = {	'pass': ['exit: pass'],
		  		'fail': ['exit: fail', "not ok"], 'hang': [], 'check': []}

	imunch_rules = {	'pass': ['exit: pass'],
		  		'fail': ['exit: fail', "not ok"], 'hang': [], 'check': []}

	efi_rules = {	'pass': ['Test Complete'],
		  		'fail': ['Test Failed'], 'hang': [], 'check': []}

	dragon_rules = {	'pass': ['Test Complete'],
		  		'fail': ['Test Failed'], 'hang': ["running MerlinX.efi", "MerlinX.efi"], 'check':[r"CHANGING BACK TO DIR: FS1:\EFI"]}

	python_rules = {	'pass': ['Test Complete'],
		  		'fail': ['Test Failed'], 'hang': [], 'check': []}

	other_rules = {	'pass': ['Test Complete'],
		  		'fail': ['Test Failed'], 'hang': [], 'check': []}

	## Content division for Failing Checks
	efi_content = ["EFI"]
	dragon_content = ["DBM", "Pseudo Slice", "Pseudo Mesh"]
	linux_content = [ "Linux"]
	tsl_content = [ "TSL"]
	sandstone_content = ["Sandstone"]
	imunch_content = ["Imunch"]
	python_content = ["Python"]
	other_content = ["Other"]

	if content in efi_content:
		content_selection = "EFI"
		content_type = "efi"
	elif content in dragon_content:
		content_selection = "Dragon"
		content_type = "efi"
	elif content in linux_content:
		content_selection = "Linux"
		content_type = "linux"
	elif content in sandstone_content:
		content_selection = "Sandstone"
		content_type = "sandstone"
	elif content in imunch_content:
		content_selection = "Imunch"
		content_type = "imunch"
	elif content in tsl_content:
		content_selection = "TSL"
		content_type = "tsl"
	elif content in python_content:
		content_selection = "Python"
		content_type = "python"
	elif content in other_content:
		content_selection = "Other"
		content_type = "efi"
	else:
		print(' -- No valid content selected..')
		return {}

	content_strings = {		"EFI": efi_rules,
							"Dragon": dragon_rules,
							"Linux": linux_rules,
							"Sandstone": sandstone_rules,
							"Imunch": imunch_rules,
							"TSL": tsl_rules,
							"Python": python_rules,
							"Other": other_rules} # will use same as EFI rules for now Placeholder

	zip_parser = LogFileParser(zip_file_path, content_type=content_type, exclusion_string=exclusion_string, casesens=casesens)

	# Set Strings into parser
	zip_parser.set_pass_strings(array_merge(content_strings[content_selection]['pass'], pass_array))
	zip_parser.set_fail_strings(array_merge(content_strings[content_selection]['fail'], fail_array))
	zip_parser.set_hang_strings(content_strings[content_selection]['hang'])
	zip_parser.set_check_strings(content_strings[content_selection]['check'])
	zip_parser.set_skip_strings(skip_array)

	# Execute Parser
	zipped_log_data = zip_parser.parse_log_files_in_zip()

	return zipped_log_data

def find_files(base_folder, excel_keyword='Summary', zip_keyword='ExperimentData', log_keyword='DebugFrameworkLogger.log'):
	# Lists to store results
	data = []

	# Walk through the directory tree
	for root, dirs, files in os.walk(base_folder):
		# Initialize variables to store file paths
		excel_path = None
		zip_path = None
		log_path = None

		# Check for Excel files
		for file in files:
			if file.endswith('.xlsx'):
				if excel_keyword is None or excel_keyword in file:
					excel_path = os.path.join(root, file)

					# Extract information from the path
					path_parts = os.path.normpath(excel_path).split(os.sep)
					if len(path_parts) >= 6:
						product = path_parts[-6]
						vid = path_parts[-5]
						platform = path_parts[-4]
						date = path_parts[-3]
						experiment = path_parts[-2]
						summary_file = path_parts[-1]

						# Append to data list
						data.append({
							'Product': product,
							'VID': vid,
							'Platform': platform,
							'Date': date,
							'Experiment': experiment,
							'Summary File': summary_file,
							'Excel': excel_path,
							'ZIP': None,  # Placeholder for ZIP path
							'Log': None   # Placeholder for log path
						})

		# If an Excel file was found, check for ZIP and log files
		if excel_path:
			for file in files:
				# Check for ZIP files
				if file.endswith('.zip'):
					if zip_keyword is None or zip_keyword in file:
						zip_path = os.path.join(root, file)

				# Check for log files
				if file == log_keyword:
					log_path = os.path.join(root, file)

			# Update the last entry in the data list with ZIP and log paths
			if data:
				data[-1]['ZIP'] = zip_path
				data[-1]['Log'] = log_path

	# Create a DataFrame from the data list
	df = pd.DataFrame(data)

	return df

def create_file_dict(df, file_type, test_types=None, content_types=None, comments_types=None):
	file_dict = {}
	for _, row in df.iterrows():
		file_path = row[f'{file_type}']
		if pd.notna(file_path) and not os.path.basename(file_path).startswith('~$'):
			folder_name = os.path.basename(os.path.dirname(file_path))
			file_dict[folder_name] = {
				'path': file_path,
				'test_type': test_types.get(row['Experiment'], 'Base') if test_types else None,
				'content': content_types.get(row['Experiment'], '') if content_types else None,
				'comments': comments_types.get(row['Experiment'], '') if comments_types else None
			}

	return file_dict

def extract_date_time_from_folder(folder_name):
	"""
	Extract date and time from folder name pattern: YYYYMMDD_HHMMSS_Tx_ExperimentName
	Example: 20250821_163602_T1_BaseRepro_Loops
	Returns: tuple (date_str, time_str) formatted as ('YYYY-MM-DD', 'HH:MM:SS')
	"""
	import re
	# Pattern to extract date and time from folder name
	pattern = r'^(\d{8})_(\d{6})_'
	match = re.match(pattern, folder_name)

	if match:
		date_part = match.group(1)  # YYYYMMDD
		time_part = match.group(2)  # HHMMSS

		# Format date as YYYY-MM-DD
		date_formatted = f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]}"

		# Format time as HH:MM:SS
		time_formatted = f"{time_part[0:2]}:{time_part[2:4]}:{time_part[4:6]}"

		return date_formatted, time_formatted

	return '', ''

def create_summary_df(test_df):
	summary_data = []

	# Sort test_df by Date and Folder to get consistent ordering
	# This ensures experiments are numbered in chronological order
	test_df_sorted = test_df.sort_values(by=['Date', 'Folder'], ignore_index=True)

	# Build experiment_index_map based on sorted date order
	experiment_index_map = {}  # Map to store index values for each experiment
	folder_date_map = {}  # Map folders to their dates for sorting

	# First pass: collect unique folders with their dates in sorted order
	for _, row in test_df_sorted.iterrows():
		folder = row['Folder']
		date = row.get('Date', '')
		if folder not in folder_date_map:
			folder_date_map[folder] = date

	# Sort folders by date and assign consistent indices
	sorted_folders = sorted(folder_date_map.keys(), key=lambda f: (folder_date_map[f], f))
	for idx, folder in enumerate(sorted_folders, start=1):
		experiment_index_map[folder] = idx

	for _, row in test_df_sorted.iterrows():
		# Extract values from the current row
		# If line experiment is Invalid skip it
		exptype = row['Type']
		if exptype == 'Invalid':
			continue
		running_content = row['Running Content']
		content_detail = row['Content Detail']
		comments = row['Comments']
		folder =  row['Folder']
		experiment = row['Experiment']
		exptype = row['Type']
		voltage_set_to = row['Voltage set to']
		postcode = row['PostCode']
		ht_disabled = row['HT Disabled (BigCore)']
		dis_cores = row['Dis 2 Cores (Atomcore)']
		core_freq = row['Core Freq']
		core_voltage = row['Core Voltage']
		mesh_freq = row['Mesh Freq']
		mesh_voltage = row['Mesh Voltage']
		fuses_applied = row['Unit 600w Fuses Applied']
		mask = row['Configuration']
		status = row['Result']
		log_file = row['Test File']
		content_results = row['Content Status']
		mca_status = row.get('MCA Status', '')  # Get MCA Status from test_df

		# Use the pre-assigned index from date-sorted map
		exp_index = experiment_index_map[folder]

		# Extract Date and Time from folder name
		date_formatted, time_formatted = extract_date_time_from_folder(folder)

		# Construct Defeature String
		Exclude_array = ['None', 'False', None, False]

		run_content_framework = running_content if running_content not in Exclude_array else ''
		run_content_detail = content_detail if content_detail not in Exclude_array else ''

		used_content = f'{run_content_framework}::{run_content_detail}' if run_content_detail != run_content_framework else run_content_framework

		# Build defeature parts list
		defeature_parts = []

		# Core License
		core_license = row['Core License']
		if core_license not in Exclude_array:
			defeature_parts.append(f'CoreLicense::{core_license}')

		# Check if PPVC mode
		is_ppvc = voltage_set_to not in Exclude_array and str(voltage_set_to).upper() == 'PPVC'

		# Voltage set to (vbump) - only add if not default values (Vnom, VBUMP) or if PPVC
		if voltage_set_to not in Exclude_array:
			voltage_upper = str(voltage_set_to).upper()
			if voltage_upper not in ['VNOM', 'NOM', 'VBUMP']:
				defeature_parts.append(f'VBump::{voltage_upper}')

		# IA (Core) settings - skip voltage if PPVC mode
		ia_parts = []
		if core_freq not in Exclude_array:
			ia_parts.append(f'F{core_freq}')
		if not is_ppvc and core_voltage not in Exclude_array:
			float_voltage = float(core_voltage)
			formatted_voltage = f'({core_voltage})' if float_voltage < 0 else core_voltage
			ia_parts.append(f'V{formatted_voltage}')
		if ia_parts:
			defeature_parts.append(f'IA::{",".join(ia_parts)}')

		# CFC (Mesh) settings - skip voltage if PPVC mode
		cfc_parts = []
		if mesh_freq not in Exclude_array:
			cfc_parts.append(f'F{mesh_freq}')
		if not is_ppvc and mesh_voltage not in Exclude_array:
			float_voltage = float(mesh_voltage)
			formatted_voltage = f'({mesh_voltage})' if float_voltage < 0 else mesh_voltage
			cfc_parts.append(f'V{formatted_voltage}')
		if cfc_parts:
			defeature_parts.append(f'CFC::{",".join(cfc_parts)}')

		# HT Disabled
		if ht_disabled not in Exclude_array:
			defeature_parts.append(f'HTDIS::{ht_disabled.upper()}')

		# Disabled Modules/Cores
		if dis_cores not in Exclude_array:
			defeature_parts.append(f'DISMOD::{dis_cores.upper()}')

		# 600W Fuses
		if fuses_applied not in Exclude_array:
			defeature_parts.append(f'600W::{fuses_applied.upper()}')

		# Join all parts with " | " separator
		DefeatureString = ' | '.join(defeature_parts)

		# Append the row data to the summary list
		summary_data.append({
			'#': exp_index,  # Use the date-sorted index
			'Date': date_formatted,  # Formatted date from folder name
			'Time': time_formatted,  # Formatted time from folder name
			'Experiment': experiment,
			'Type': exptype,
			'PostCode': postcode,
			'Defeature': DefeatureString,
			'Mask': mask,
			'Status': status,
			'Used Content': used_content,
			'Content Results': content_results,
			'MCAs': mca_status,  # Add MCA presence
			'Comments': comments
		})

	summary_df = pd.DataFrame(summary_data)

	# Also add experiment numbers, Date/Time, and Used Content to test_df_sorted for consistency
	test_df_sorted['#'] = test_df_sorted['Folder'].map(experiment_index_map)

	# Extract Date and Time from folder names and add to test_df_sorted
	date_time_data = test_df_sorted['Folder'].apply(lambda f: pd.Series(extract_date_time_from_folder(f), index=['Date_Formatted', 'Time_Formatted']))
	test_df_sorted['Date_Formatted'] = date_time_data['Date_Formatted']
	test_df_sorted['Time_Formatted'] = date_time_data['Time_Formatted']

	# Calculate and add Used Content to test_df_sorted (same logic as summary)
	def calculate_used_content(row):
		Exclude_array = ['None', 'False', None, False]
		running_content = row.get('Running Content', '')
		content_detail = row.get('Content Detail', '')
		run_content_framework = running_content if running_content not in Exclude_array else ''
		run_content_detail = content_detail if content_detail not in Exclude_array else ''
		return f'{run_content_framework}::{run_content_detail}' if run_content_detail != run_content_framework else run_content_framework

	test_df_sorted['Used Content'] = test_df_sorted.apply(calculate_used_content, axis=1)

	# Return the summary_df, the updated test_df with # and Used Content columns, and the experiment_index_map
	return summary_df, test_df_sorted, experiment_index_map

def format_voltage(value, volt_type, exclude_array):

	if value not in exclude_array:
		float_value = float(value)
		formatted_value = f'({value})' if float_value < 0 else value
		return_value = f'::{volt_type} {formatted_value}'
	else:
		return_value = ''

	return return_value

def format_frequency(value, exclude_array):

	if value not in exclude_array:
		return_value = f'::F{value}'
	else:
		return_value = ''

	return return_value

def save_to_excel(initial_df, test_df, summary_df, fail_info_df=None, unique_fails_df=None, unique_mcas_df=None,
                  vvar_df=None, core_data_df=None, experiment_summary_df=None, overview_df=None, filename='output.xlsx'):
	"""
	Save DataFrames to Excel with formatting.
	Now uses ExcelReportBuilder class for better maintainability.

	For custom sheet order or styling, use ExcelReportBuilder directly:
		from ExcelReportBuilder import ExcelReportBuilder, SheetConfig

		# Define custom configuration
		configs = [
			SheetConfig('MySheet', 'my_df', 'MyTable', 'TableStyleLight1'),
			# ... more configs
		]

		builder = ExcelReportBuilder(sheet_configs=configs)
		builder.build({'my_df': my_dataframe}, 'output.xlsx')
	"""

	# Use ExcelReportBuilder (overview_df passed directly from caller)
	try:
		from ..utils.ExcelReportBuilder import save_to_excel as excel_save
	except ImportError:
		from utils.ExcelReportBuilder import save_to_excel as excel_save
	excel_save(initial_df, test_df, summary_df, fail_info_df, unique_fails_df, unique_mcas_df,
	           vvar_df, core_data_df, experiment_summary_df, overview_df, filename=filename)

def add_framework_fails_tab(save_path, zip_results):
	with pd.ExcelWriter(save_path, mode='a', engine='openpyxl') as writer:
		df = pd.DataFrame([
			{'#': idx + 1, 'Experiment': result['Experiment'], 'Fail Data': ', '.join(result['Data'])}
			for idx, result in enumerate(zip_results.values())
		])
		df.to_excel(writer, sheet_name='FrameworkFails', index=False)

def formatted_print(text, fore = Fore.RESET, back = Back.RESET):

	pretty_text = back + fore + text + Fore.RESET + Back.RESET

	print(pretty_text)

def generate_unique_fails(fail_info_df):

	# Split the fail data by commas and explode the DataFrame
	fail_info_df['Log Fails'] = fail_info_df['Log Fails'].apply(lambda x: x.split(','))
	exploded_df = fail_info_df.explode('Log Fails')

	# Filter out "PASS" entries
	#exploded_df = exploded_df[exploded_df['Fails'] != "PASS"]

	#unique_fails = fail_info_df.explode('Log Fails')
	unique_fails = exploded_df.groupby('Log Fails').agg(
		Content=('Content', lambda x: ', '.join(set(x))),
		Fail_Count=('Log Fails', 'size')
	).reset_index().rename(columns={'Log Fails': 'Failed Content'})

	# Return it to the previous format
	fail_info_df['Log Fails'] = fail_info_df['Log Fails'].apply(lambda x: ','.join(x))

	print(unique_fails)
	return unique_fails

def update_content_results(base_df, fail_info_df):
	for idx, row in base_df.iterrows():
		test_file = row['Test File']
		folder = row['Folder']
		fail_data = fail_info_df[(fail_info_df['Log File'] == test_file) & (fail_info_df['Experiment'] == folder)]
		if not fail_data.empty:
			fails = fail_data['Log Fails'].tolist()
			fails_list = [f.strip() for f in fails[0].split(",")]  # Strip each failure item
			base_df.at[idx, 'Content Status'] = (', '.join(fails_list[:2]) + '...') if len(fails_list) > 2 else ', '.join(fails_list)
	return base_df

def update_mca_results(test_df, fail_info_df, mca_df):
	# Call check_mca_presence to get MCA presence for each log file
	mca_presence = check_mca_presence(fail_info_df, mca_df)

	# Iterate over each row in test_df and update MCA Status
	for idx, row in test_df.iterrows():
		log_file = row['Test File']
		test_df.at[idx, 'MCA Status'] = mca_presence.get(log_file, 'NO')

	return test_df

def check_mca_presence(fail_info_df, mca_df):
	# Initialize a dictionary to store MCA presence for each log file
	mca_presence = {}

	# Iterate over each row in fail_info_df
	for _, row in fail_info_df.iterrows():
		experiment_name = row['Experiment']
		log_file = row['Log File']
		run_value = log_file.split('_')[0]

		# Check if there is any MCA data for the experiment and run_value
		mca_exists = not mca_df[(mca_df['Experiment'] == experiment_name) & (mca_df['Run Value'] == run_value)].empty

		# Set MCA presence to 'YES' or 'NO'
		mca_presence[log_file] = 'YES' if mca_exists else 'NO'

	return mca_presence

def array_merge(array1, array2, unique = True):
	new_array = list(set(array1 + array2)) if unique else array1 + array2
	return new_array


# ============================================================================
# DEBUGFRAMEWORKLOGGER PARSER CLASS - Handles DR, Voltage, and Metadata parsing
# ============================================================================

class DebugFrameworkLoggerParser:
	"""
	Parses DebugFrameworkLogger.log files to extract DR data, Voltage data, and Metadata.
	"""

	def __init__(self, log_dict, product='GNR'):
		self.log_dict = log_dict
		self.product = product
		self._dr_df = None
		self._voltage_df = None
		self._metadata_df = None
		self._parsed = False

	def _parse_if_needed(self):
		"""Parse all data if not already parsed - Direct parser without external dependencies"""
		if self._parsed:
			return

		all_dr = []
		all_voltage = []
		all_metadata = []

		for experiment, log_info in self.log_dict.items():
			log_path = log_info['path']

			# Find DebugFrameworkLogger.log in the same directory
			log_dir = os.path.dirname(log_path)
			debug_log_path = os.path.join(log_dir, 'DebugFrameworkLogger.log')

			if not os.path.exists(debug_log_path):
				continue

			try:
				with open(debug_log_path, 'r', encoding='utf-8', errors='ignore') as f:
					current_iteration = None

					for line in f:
						# Parse iteration number from multiple sources
						# Priority 1: "Running Loop iteration: X/Y" marker (appears before voltage data)
						if 'Running Loop iteration:' in line:
							match = re.search(r'Running Loop iteration:\s*(\d+)/\d+', line)
							if match:
								current_iteration = int(match.group(1))

						# Priority 2: "Performing test iteration X with" marker (also appears before voltage data)
						elif 'Performing test iteration' in line:
							match = re.search(r'Performing test iteration (\d+) with', line)
							if match:
								current_iteration = int(match.group(1))

						# Priority 3: tdata lines (appears after test completes)
						# Format: tdata_1::MeshAVX2_Twiddle_FirstPass_ia_f32_cfc_f18::FAIL::0xef0000ff::DL32-Twiddle-3Y-0F100385_HANG
						if 'tdata_' in line:
							match = re.search(r'tdata_(\d+)', line)
							if match:
								tdata_iteration = int(match.group(1))
								# Only update if we haven't set it from Loop/Performing marker
								# or if tdata number matches current_iteration
								if current_iteration is None or tdata_iteration == current_iteration:
									current_iteration = tdata_iteration

								# Extract failing seed from tdata line (5th field after ::)
								# Format: tdata_1::TestName::STATUS::Scratchpad::FailingSeed
								tdata_match = re.search(r'tdata_\d+::[^:]+::[^:]+::[^:]+::(.+?)(?:_FAIL|_HANG|_PASS|$)', line)
								if tdata_match:
									failing_seed = tdata_match.group(1).strip()
									# Remove common suffixes
									failing_seed = failing_seed.replace('_FAIL', '').replace('_HANG', '').replace('_PASS', '')

									# Store metadata
									all_metadata.append({
										'Experiment': experiment,
										'Iteration': tdata_iteration,
										'Failing_Seed': failing_seed,
										'Log_File': f"{tdata_iteration}_{experiment}.log"
									})

						# Parse DR data
						# Format: dr_data_CORE141_THREAD1_APIC_[32b] 0x00000101_DR0_0x600d600d_DR1_0x40d_DR2_0x0_DR3_0xcddc
						if 'dr_data_CORE' in line:
							match = re.search(
								r'dr_data_CORE(\d+)_THREAD(\d+)_APIC_\[32b\]\s+(0x[0-9a-fA-F]+)_DR0_(0x[0-9a-fA-F]+)_DR1_(0x[0-9a-fA-F]+)_DR2_(0x[0-9a-fA-F]+)_DR3_(0x[0-9a-fA-F]+)',
								line
							)
							if match:
								core = int(match.group(1))
								thread = int(match.group(2))
								apic_id = match.group(3)
								dr0 = match.group(4).upper()  # Normalize to uppercase
								dr1 = match.group(5).upper()  # Normalize to uppercase
								dr2 = match.group(6).upper()  # Normalize to uppercase
								dr3 = match.group(7).upper()  # Normalize to uppercase

								all_dr.append({
									'Experiment': experiment,
									'Iteration': current_iteration,
									'Core_Module': core,
									'Thread': thread,
									'APIC_ID': apic_id,
									'DR0': dr0,
									'DR1': dr1,
									'DR2': dr2,
									'DR3': dr3
								})

						# Parse voltage data - Handle both GNR and CWF formats
						# GNR Format: phys_core = 141, IA Ratio = 0x16, IA Volt = 0.682500, IALicense= 0x1, current_dcf_ratio = 0
						# CWF Format: PHYmodule = 141, LLmodule = 123, IA Ratio = 22, IA Volt = 0.682500

						if ('phys_core' in line or 'PHYmodule' in line) and 'IA Ratio' in line and 'IA Volt' in line:
							core = None
							ratio = None
							voltage = None
							license_val = None

							# Try GNR format first (phys_core with hex ratio and license)
							match_gnr = re.search(
								r'phys_core\s*=\s*(\d+),\s*IA Ratio\s*=\s*(0x[0-9a-fA-F]+),\s*IA Volt\s*=\s*([\d.]+)(?:,\s*IALicense\s*=\s*(0x[0-9a-fA-F]+))?',
								line
							)
							if match_gnr:
								core = int(match_gnr.group(1))
								ratio_hex = match_gnr.group(2)
								voltage = float(match_gnr.group(3))
								ratio = int(ratio_hex, 16)  # Convert hex to decimal
								if match_gnr.group(4):
									license_val = match_gnr.group(4)  # Keep as hex string
							else:
								# Try CWF format (PHYmodule with decimal ratio)
								match_cwf = re.search(
									r'PHYmodule\s*=\s*(\d+),\s*LLmodule\s*=\s*(\d+),\s*IA Ratio\s*=\s*(\d+),\s*IA Volt\s*=\s*([\d.]+)',
									line
								)
								if match_cwf:
									core = int(match_cwf.group(1))  # Use physical module
									ratio = int(match_cwf.group(3))  # Already decimal
									voltage = float(match_cwf.group(4))

							# Add to results if we successfully parsed
							if core is not None and ratio is not None and voltage is not None:
								all_voltage.append({
									'Experiment': experiment,
									'Iteration': current_iteration,
									'Core_Module': core,
									'Voltage': voltage,
									'Ratio': ratio,
									'License': license_val if license_val else ''
								})

			except Exception as e:
				print(f"Warning: Could not parse DebugFrameworkLogger for {experiment}: {e}")
				continue

		self._dr_df = pd.DataFrame(all_dr) if all_dr else pd.DataFrame()
		self._voltage_df = pd.DataFrame(all_voltage) if all_voltage else pd.DataFrame()
		self._metadata_df = pd.DataFrame(all_metadata) if all_metadata else pd.DataFrame()
		self._parsed = True

	def parse_dr_data(self):
		"""Parse and return DR data DataFrame"""
		self._parse_if_needed()
		return self._dr_df

	def parse_core_voltage_data(self):
		"""Parse and return voltage data DataFrame"""
		self._parse_if_needed()
		return self._voltage_df

	def parse_experiment_metadata(self):
		"""Parse and return metadata DataFrame"""
		self._parse_if_needed()
		return self._metadata_df

	def parse_all(self):
		"""Parse all DebugFrameworkLogger files and return DR, voltage, and metadata DataFrames"""
		self._parse_if_needed()
		return self._dr_df, self._voltage_df, self._metadata_df


# ============================================================================
# VVAR PARSER CLASS - Handles all VVAR parsing with clean architecture
# ============================================================================

class VVARParser:
	"""
	Handles VVAR parsing from ZIP files and DebugFrameworkLogger DR data.
	Uses composition to avoid deep nesting and improve maintainability.
	"""

	def __init__(self, product='GNR', vvar_filter=None, skip_array=None):
		self.product = product
		self.vvar_filter = vvar_filter or ['0x600D600D']
		self.skip_array = skip_array or []
		self.dragon_bucketing = dragon_bucketing

	def parse_from_zip(self, zip_path_dict, test_df, dr_df=None, metadata_df=None, experiment_index_map=None):
		"""Main entry point for parsing VVARs from ZIP files

		Args:
			zip_path_dict: Dictionary of ZIP file paths
			test_df: Test DataFrame with experiment information (must include # column)
			dr_df: DR data DataFrame
			metadata_df: Metadata DataFrame
			experiment_index_map: Map of folder names to experiment numbers (for consistent numbering)
		"""
		all_results = []

		for experiment, zip_info in zip_path_dict.items():
			log_results = self._parse_experiment_logs(
				experiment, zip_info, test_df, dr_df, experiment_index_map
			)
			all_results.extend(log_results)

		# Add DR data enhancement (pass zip_path_dict to extract failing seeds)
		dr_results = self._enhance_with_dr_data(test_df, dr_df, metadata_df, all_results, experiment_index_map, zip_path_dict)
		all_results.extend(dr_results)

		return self._create_dataframe(all_results)

	def _parse_experiment_logs(self, experiment, zip_info, test_df, dr_df, experiment_index_map):
		"""Parse VVAR data from log files in a ZIP"""
		results = []
		zip_path = zip_info['path']
		content_info = zip_info['content']

		# Get experiment # and clean name from test_df
		exp_tests = test_df[test_df['Folder'] == experiment]
		if exp_tests.empty:
			return results

		# Use first test row to get experiment info
		first_test = exp_tests.iloc[0]
		exp_num = first_test.get('#', 1)
		exp_name = first_test.get('Experiment', experiment)

		# Create global APIC-to-VVAR mappings for all iterations in this experiment
		apic_mappings_cache = {}
		if dr_df is not None and not dr_df.empty:
			for test_num in exp_tests['Test Number'].unique():
				iteration = self._extract_iteration_from_test_number(test_num, 0)
				if iteration is not None:
					apic_mappings_cache[iteration] = self._create_global_apic_vvar_mapping(dr_df, experiment, iteration)

		with zipfile.ZipFile(zip_path, 'r') as zip_ref:
			for log_file in zip_ref.namelist():
				if not log_file.endswith('.log') or 'pysv' in log_file:
					continue

				log_content = zip_ref.open(log_file).read().decode('utf-8', errors='ignore')
				vvar_data = self._extract_vvars_from_log(log_content)

				if not vvar_data or self._should_skip_seed(vvar_data['failing_seed']):
					continue

			# Get test iteration number from log filename
			test_num = self._extract_test_number_from_filename(log_file)
			iteration = self._extract_iteration_from_test_number(test_num, 0) if test_num else None

			# Get "Used Content" from test_df for this specific iteration
			# Build the proper test number format (e.g., 'tdata_2')
			test_num_str = f'tdata_{test_num}' if test_num else None
			test_row = exp_tests[exp_tests['Test Number'] == test_num_str] if test_num_str else exp_tests.head(1)
			if not test_row.empty:
				used_content = test_row.iloc[0].get('Used Content', content_info)
			else:
				used_content = content_info				# Get global APIC mapping for this iteration
				apic_to_vvar_map = apic_mappings_cache.get(iteration, None) if iteration is not None else None

				# Deduplicate VVARs by value within this log file (iteration)
				# Multiple cores may have the same VVAR value - we want only ONE row per unique VVAR
				# Use case-insensitive comparison (0xA4000000 == 0xa4000000)
				unique_vvars = {}
				for vvar in vvar_data['vvars']:
					vvar_value = vvar['Value']
					vvar_value_upper = vvar_value.upper()  # Normalize to uppercase for comparison
					if vvar_value_upper not in unique_vvars:
						# Store first occurrence with original case
						unique_vvars[vvar_value_upper] = vvar

				# Process each unique VVAR value (one row per unique VVAR per iteration)
				for vvar in unique_vvars.values():
					row_data = self._create_vvar_row(
						experiment, exp_name, used_content, log_file,
						vvar_data['failing_seed'], vvar, exp_num,
						test_df, dr_df, test_num, apic_to_vvar_map
					)
					results.append(row_data)

		return results

	def _extract_vvars_from_log(self, log_content):
		"""Extract VVAR values and failing seed from log content"""
		lines = log_content.splitlines()
		vvar_list = []
		failing_seed = None
		in_vvar_section = False

		seed_pattern = r'Running\s+FS\d+:\\.*\\([\w-]+\.obj)'
		vvar_pattern = r'<Vvar\s+Number="(0x[0-9A-Fa-f]+)"\s+Value="(0x[0-9A-Fa-f]+)"\s*/>'

		for line in lines:
			seed_match = re.search(seed_pattern, line)
			if seed_match:
				failing_seed = seed_match.group(1).replace('.obj', '')

			if '<Vvars>' in line:
				in_vvar_section = True
				continue
			if '</Vvars>' in line:
				in_vvar_section = False
				continue

			if in_vvar_section:
				vvar_match = re.search(vvar_pattern, line)
				if vvar_match:
					vvar_num = vvar_match.group(1)
					vvar_val = vvar_match.group(2)

					# Convert VVAR number to int for range check
					vvar_num_int = int(vvar_num, 16)

					# Only include VVARs in the core range (0xC to 0x32B)
					# Skip configuration VVARs (0x0-0xB) and any VVARs above 0x32B
					if vvar_num_int < 0xC or vvar_num_int > 0x32B:
						continue

					# Skip filtered VVAR values (e.g., 0x600D600D)
					if vvar_val.upper() not in [v.upper() for v in self.vvar_filter]:
						vvar_list.append({'Number': vvar_num, 'Value': vvar_val})

		return {'failing_seed': failing_seed, 'vvars': vvar_list}

	def _extract_test_number_from_filename(self, filename):
		"""Extract iteration number from log filename (e.g., '11_FirstPass_...' -> 11)"""
		match = re.match(r'(\d+)_', filename)
		return int(match.group(1)) if match else None

	def _should_skip_seed(self, failing_seed):
		"""Check if seed should be skipped based on skip_array"""
		if not failing_seed:
			return True
		return any(skip_str and skip_str.strip() in failing_seed for skip_str in self.skip_array)

	def _decode_vvar(self, vvar_value, seed_name=''):
		"""Decode VVAR using dragon_bucketing"""
		if not self.dragon_bucketing:
			return "Decode unavailable"

		try:
			bucket = self.dragon_bucketing.bucket(
				vvar=vvar_value,
				product=self.product,
				seed_name=seed_name,
				is_os=False
			)
			return f"{bucket.main} | {bucket.sub}"
		except Exception as e:
			return f"Decode Error: {str(e)}"

	def _create_vvar_row(self, folder, exp_name, content, log_file, failing_seed,
	                     vvar, exp_num, test_df, dr_df, test_num, apic_to_vvar_map=None):
		"""Create a row of VVAR data with core columns

		Args:
			folder: Folder name (e.g., '20251103_090627_T1_MeshAVX2_Twiddle')
			exp_name: Clean experiment name (e.g., 'MeshAVX2_Twiddle_FirstPass_ia_f32_cfc_f18')
			content: Content type
			log_file: Log file name
			failing_seed: Failing seed
			vvar: VVAR dictionary with 'Number' and 'Value'
			exp_num: Experiment number from test_df
			test_df: Test DataFrame
			dr_df: DR DataFrame
			test_num: Test iteration number
			apic_to_vvar_map: Global APIC-to-VVAR mapping (optional)
		"""
		vvar_value = vvar['Value']
		vvar_number = vvar.get('Number', None)  # Extract VVAR number if available

		# Normalize VVAR value to uppercase for consistency (0xa4000000 -> 0xA4000000)
		vvar_value_normalized = vvar_value.upper() if isinstance(vvar_value, str) else vvar_value

		decode_result = self._decode_vvar(vvar_value, failing_seed)

		# Extract Date and Time from folder name
		date_formatted, time_formatted = extract_date_time_from_folder(folder)

		# Build notes documenting data source
		notes = 'Data from individual log file'

		row_data = {
			'#': exp_num,
			'Date': date_formatted,
			'Time': time_formatted,
			'Experiment': exp_name,
			'Content': content,
			'Log_File': os.path.basename(log_file),
			'Data_Origin': 'VVAR_Log',
			'Failing_Seed': failing_seed,
			'VVAR': vvar_value_normalized,  # Use normalized uppercase version
			'Decode': decode_result,
			'Notes': notes
		}

		# Add core columns if DR data available (pass global mapping)
		if dr_df is not None and not dr_df.empty and test_num is not None:
			# Always calculate VVAR numbers based on global APIC ordering
			core_columns, core_list = self._build_core_columns(
				dr_df, folder, test_num, vvar_value, vvar_number=None, apic_to_vvar_map=apic_to_vvar_map
			)
			row_data.update(core_columns)
			row_data['CoreList'] = core_list
		else:
			row_data['CoreList'] = ''

		return row_data

	def _build_core_columns(self, dr_df, experiment, iteration, vvar_value, vvar_number=None, apic_to_vvar_map=None):
		"""Build per-core VVAR columns from DR data with VVAR number calculated by APIC ordering

		VVAR number assignment logic:
		1. If apic_to_vvar_map is provided (global mapping), use it directly
		2. Otherwise, collect APIC IDs only for this VVAR value and create local mapping

		Global mapping (preferred):
		- Created once per experiment/iteration across ALL VVAR values
		- Ensures sequential numbering across all compute dies (0xC, 0xD, 0xE...)
		- APIC 0x0 (Compute0) -> 0xC, APIC 0x80 (Compute1) -> 0x5C (continues sequentially)

		Local mapping (fallback):
		- Created per VVAR value (old behavior)
		- Only used if apic_to_vvar_map is not provided

		This handles APIC ID offsets across compute dies:
		- Compute0 (cores 0-59): APIC starts at 0x0
		- Compute1 (cores 60-119): APIC starts at 0x80 (GNR) or 0x100 (CWF)
		- Compute2 (cores 120-179): APIC starts at 0x100 (GNR) or 0x200 (CWF)
		"""
		# Normalize VVAR value to uppercase for case-insensitive comparison
		vvar_value_upper = vvar_value.upper() if isinstance(vvar_value, str) else vvar_value

		# Filter DR data for this specific experiment and iteration
		# Use case-insensitive VVAR comparison
		exp_dr_data = dr_df[
			(dr_df['Experiment'] == experiment) &
			(dr_df['Iteration'] == iteration) &
			(dr_df['DR0'].str.upper() == vvar_value_upper)
		].copy()

		if exp_dr_data.empty:
			return {}, ''

		# If no global mapping provided, create local mapping (fallback to old behavior)
		if apic_to_vvar_map is None:
			# Step 1: Collect all unique APIC IDs and sort them
			# This handles compute die offsets automatically
			all_apic_ids = []
			for _, row in exp_dr_data.iterrows():
				apic_id = row['APIC_ID']
				apic_int = apic_id if isinstance(apic_id, int) else int(str(apic_id), 16 if '0x' in str(apic_id) else 10)
				if apic_int not in all_apic_ids:
					all_apic_ids.append(apic_int)

			# Sort APIC IDs from lowest to highest
			all_apic_ids.sort()

			# Step 2: Create APIC ID to VVAR number mapping
			# VVAR numbers start at 0xC and increment sequentially
			apic_to_vvar_map = {}
			for idx, apic_id in enumerate(all_apic_ids):
				vvar_num = 0xC + idx  # Start at 0xC (12 decimal), increment by sorted position
				apic_to_vvar_map[apic_id] = vvar_num

		# Step 3: Build core columns with proper VVAR numbers
		core_columns = {}
		cores_with_vvar = []

		# Group by core
		for core_num in sorted(exp_dr_data['Core_Module'].unique()):
			core_dr = exp_dr_data[exp_dr_data['Core_Module'] == core_num]

			# Deduplicate by (APIC_ID, Thread)
			seen_threads = set()
			threads = []

			for _, dr_row in core_dr.iterrows():
				apic_id = dr_row['APIC_ID']
				thread_num = dr_row.get('Thread', 0)

				# Convert APIC ID to integer
				apic_int = apic_id if isinstance(apic_id, int) else int(str(apic_id), 16 if '0x' in str(apic_id) else 10)
				key = (apic_int, thread_num)

				if key not in seen_threads:
					seen_threads.add(key)
					apic_hex = f"0x{apic_int:X}"

					# Determine VVAR number: use from log if available, otherwise use calculated mapping
					if vvar_number:
						# Use VVAR number from log file
						vvar_num_hex = vvar_number
					else:
						# Use VVAR number from APIC ordering mapping
						vvar_num = apic_to_vvar_map.get(apic_int, 0xC)
						vvar_num_hex = f"0x{vvar_num:X}"

					threads.append(f"TH:{thread_num}_APIC:{apic_hex}_VVAR_N:{vvar_num_hex}")

			if threads:
				core_columns[f'CORE{core_num}'] = " | ".join(threads) if len(threads) > 1 else threads[0]
				cores_with_vvar.append(core_num)

		core_list = ', '.join(map(str, sorted(cores_with_vvar)))
		return core_columns, core_list

	def _create_global_apic_vvar_mapping(self, dr_df, experiment, iteration):
		"""Create global APIC-to-VVAR mapping for entire experiment/iteration

		This creates a single mapping across ALL VVAR values in an experiment/iteration,
		ensuring VVAR numbers are assigned sequentially across all compute dies.

		Example:
		- APIC 0x0 (Compute0) -> VVAR 0xC
		- APIC 0x2 (Compute0) -> VVAR 0xD
		- ...
		- APIC 0x4E (Compute0, CORE57) -> VVAR 0x5A
		- APIC 0x4F (Compute0, CORE57) -> VVAR 0x5B
		- APIC 0x80 (Compute1, CORE62) -> VVAR 0x5C (continues sequentially, NOT 0x8C)
		- APIC 0x81 (Compute1, CORE62) -> VVAR 0x5D

		Args:
			dr_df: DR DataFrame
			experiment: Experiment folder name
			iteration: Iteration number

		Returns:
			dict: Mapping from APIC ID (int) to VVAR number (int)
		"""
		# Filter DR data for this experiment and iteration (all VVAR values)
		exp_dr_data = dr_df[
			(dr_df['Experiment'] == experiment) &
			(dr_df['Iteration'] == iteration)
		].copy()

		if exp_dr_data.empty:
			return {}

		# Collect all unique APIC IDs across ALL VVAR values
		all_apic_ids = set()
		for _, row in exp_dr_data.iterrows():
			apic_id = row['APIC_ID']
			apic_int = apic_id if isinstance(apic_id, int) else int(str(apic_id), 16 if '0x' in str(apic_id) else 10)
			all_apic_ids.add(apic_int)

		# Sort APIC IDs globally (handles compute die offsets)
		sorted_apic_ids = sorted(all_apic_ids)

		# Create global mapping: VVAR numbers start at 0xC and increment sequentially
		apic_to_vvar_map = {}
		for idx, apic_id in enumerate(sorted_apic_ids):
			vvar_num = 0xC + idx  # Start at 0xC, increment globally across all compute dies
			apic_to_vvar_map[apic_id] = vvar_num

		return apic_to_vvar_map

	def _enhance_with_dr_data(self, test_df, dr_df, metadata_df, existing_results, experiment_index_map, zip_path_dict):
		"""Add VVAR entries from DebugFrameworkLogger DR data with deduplication

		This method creates one row per unique VVAR value, comparing with log file data
		and documenting the data source and any conflicts.

		Args:
			test_df: Test DataFrame
			dr_df: DR DataFrame
			metadata_df: Metadata DataFrame
			existing_results: Already parsed VVAR results from log files
			experiment_index_map: Map of folder names to experiment numbers
			zip_path_dict: Dictionary of ZIP file paths for extracting failing seeds
		"""
		if dr_df is None or dr_df.empty or test_df.empty:
			return []

		# Build a map of existing VVAR data from log files for comparison
		# Key: (experiment_name, iteration, vvar_value) -> log_result_dict
		log_vvar_map = {}
		for row in existing_results:
			exp_name = row.get('Experiment', '')
			# Extract iteration from log_file (e.g., "1_ExperimentName.log" -> 1)
			log_file = row.get('Log_File', '')
			if log_file and '_' in log_file:
				try:
					iteration = int(log_file.split('_')[0])
				except (ValueError, IndexError):
					iteration = None
			else:
				iteration = None

			vvar_value = row.get('VVAR', '')
			if exp_name and vvar_value and iteration is not None:
				# Normalize to uppercase for case-insensitive comparison
				vvar_value_key = vvar_value.upper() if isinstance(vvar_value, str) else vvar_value
				log_vvar_map[(exp_name, iteration, vvar_value_key)] = row

		dr_results = []

		# Track which experiment/iteration combinations we've processed to create global mappings
		apic_mappings_cache = {}

		for test_idx, test_row in test_df.iterrows():
			folder = test_row.get('Folder', '')
			exp_name = test_row.get('Experiment', folder)
			exp_num = test_row.get('#', test_idx + 1)
			content = test_row.get('Used Content', test_row.get('Running Content', ''))

			# Extract numeric iteration from Test Number
			iteration = self._extract_iteration_from_test_number(test_row.get('Test Number', ''), test_idx)

			# Get DR data for this iteration
			exp_dr = dr_df[
				(dr_df['Experiment'] == folder) &
				(dr_df['Iteration'] == iteration) &
				(dr_df['DR0'] != '0x0')
			]

			if exp_dr.empty:
				continue

			# Create global APIC-to-VVAR mapping once per experiment/iteration
			mapping_key = (folder, iteration)
			if mapping_key not in apic_mappings_cache:
				apic_mappings_cache[mapping_key] = self._create_global_apic_vvar_mapping(dr_df, folder, iteration)
			apic_to_vvar_map = apic_mappings_cache[mapping_key]

			# Get failing seed from metadata (DebugFrameworkLogger tdata) or ZIP log file
			# Try metadata first (tdata lines), then fall back to ZIP log file
			log_file_from_meta, failing_seed = self._get_metadata_for_iteration(metadata_df, folder, iteration)
			if not failing_seed:
				# Fallback to extracting from ZIP log file
				failing_seed = self._get_failing_seed_from_dr(folder, iteration, zip_path_dict)

			# Use log_file from metadata, or construct it
			if log_file_from_meta and log_file_from_meta != 'Unknown':
				log_file = log_file_from_meta
			else:
				log_file = f"{iteration}_{exp_name}.log" if iteration is not None else 'Unknown'

			# DEDUPLICATION: Group by unique DR0 (VVAR) values
			# For each unique VVAR value, create ONE row with all core data
			for dr0_value, dr0_group in exp_dr.groupby('DR0'):
				# Normalize DR0 value for case-insensitive comparison
				dr0_value_normalized = dr0_value.upper() if isinstance(dr0_value, str) else dr0_value

				# Check if this VVAR already exists in log file data
				log_key = (exp_name, iteration, dr0_value_normalized)

				if log_key in log_vvar_map:
					# VVAR exists in log file - skip creating DR_Data row since log data takes priority
					# The log file already has this VVAR with potentially more accurate data
					continue

				# Create DR_Data row for this unique VVAR value
				row_data = self._create_dr_row(
					exp_num, exp_name, content, log_file, failing_seed,
					dr0_value, dr0_group, iteration, folder, apic_to_vvar_map
				)
				dr_results.append(row_data)

		return dr_results

	def _get_failing_seed_from_dr(self, folder, iteration, zip_path_dict):
		"""Get failing seed from log file in ZIP for specific iteration

		Args:
			folder: Experiment folder name (e.g., '20251103_090627_T1_MeshAVX2_Twiddle')
			iteration: Iteration number to find failing seed for
			zip_path_dict: Dictionary of ZIP file paths

		Returns:
			Failing seed string or empty string if not found
		"""
		# Get the ZIP file for this experiment
		if folder not in zip_path_dict:
			return ''

		zip_path = zip_path_dict[folder]['path']

		if not os.path.exists(zip_path):
			return ''

		# Construct the expected log file name based on iteration
		# Log files are typically named like: "1_ExperimentName.log", "2_ExperimentName.log", etc.
		log_filename_pattern = f"{iteration}_"

		try:
			with zipfile.ZipFile(zip_path, 'r') as zip_file:
				# Find the log file for this iteration
				log_files = [f for f in zip_file.namelist() if f.endswith('.log') and log_filename_pattern in f]

				if not log_files:
					return ''

				# Read the first matching log file
				log_file = log_files[0]
				with zip_file.open(log_file) as f:
					log_content = f.read().decode('utf-8', errors='ignore')

					# Extract failing seed using the same pattern as _parse_vvar_data
					seed_pattern = r'Running\s+FS\d+:\\.*\\([\w-]+\.obj)'
					seed_match = re.search(seed_pattern, log_content)

					if seed_match:
						failing_seed = seed_match.group(1).replace('.obj', '')
						return failing_seed

		except Exception as e:
			# Silently handle errors (ZIP might be corrupted, file might not exist, etc.)
			pass

		return ''

	def _extract_iteration_from_test_number(self, test_num_raw, fallback_idx):
		"""Extract numeric iteration from Test Number (e.g., 'tdata_1' -> 1)"""
		if isinstance(test_num_raw, str) and 'tdata_' in test_num_raw:
			try:
				return int(test_num_raw.split('_')[1])
			except (IndexError, ValueError):
				return fallback_idx + 1
		elif isinstance(test_num_raw, int):
			return test_num_raw
		return fallback_idx + 1

	def _get_metadata_for_iteration(self, metadata_df, experiment, iteration):
		"""Get log file and failing seed from metadata"""
		if metadata_df is None or metadata_df.empty:
			return 'Unknown', ''

		iter_metadata = metadata_df[
			(metadata_df['Experiment'] == experiment) &
			(metadata_df['Iteration'] == iteration)
		]

		if iter_metadata.empty:
			return 'Unknown', ''

		log_file = iter_metadata.iloc[0].get('Log_File', 'Unknown')
		failing_seed_raw = iter_metadata.iloc[0].get('Failing_Seed', '')

		# Clean failing seed: remove _FAIL, _HANG suffixes
		failing_seed = failing_seed_raw
		if isinstance(failing_seed_raw, str):
			failing_seed = failing_seed_raw.replace('_FAIL', '').replace('_HANG', '')

		return log_file, failing_seed

	def _create_dr_row(self, exp_num, exp_name, content, log_file, failing_seed, dr0_value, dr0_group, iteration, folder, apic_to_vvar_map=None):
		"""Create a row from DR data

		Args:
			exp_num: Experiment number
			exp_name: Clean experiment name
			content: Content type
			log_file: Log file name
			failing_seed: Failing seed
			dr0_value: DR0 value (VVAR value)
			dr0_group: Group of DR rows for this DR0 value
			iteration: Iteration number
			folder: Folder name for Date/Time extraction
			apic_to_vvar_map: Global APIC-to-VVAR mapping (optional)
		"""
		decode_result = self._decode_vvar(dr0_value)

		# Normalize VVAR value to uppercase for consistency
		dr0_value_normalized = dr0_value.upper() if isinstance(dr0_value, str) else dr0_value

		# Extract Date and Time from folder name
		date_formatted, time_formatted = extract_date_time_from_folder(folder)

		# Build notes documenting data source
		notes = 'Data from DebugFrameworkLogger (no log file VVAR found)'

		row_data = {
			'#': exp_num,
			'Date': date_formatted,
			'Time': time_formatted,
			'Experiment': exp_name,
			'Content': content,
			'Log_File': log_file,
			'Data_Origin': 'DR_Data',
			'Failing_Seed': failing_seed,
			'VVAR': dr0_value_normalized,  # Use normalized uppercase version
			'Decode': decode_result,
			'Notes': notes
		}

		# Add core columns (pass global mapping for correct VVAR numbering)
		core_columns, core_list = self._build_dr_core_columns(dr0_value, dr0_group, apic_to_vvar_map)
		row_data.update(core_columns)
		row_data['CoreList'] = core_list

		return row_data

	def _build_dr_core_columns(self, dr0_value, dr0_group, apic_to_vvar_map=None):
		"""Build core columns from DR data group - Use global VVAR number mapping

		Args:
			dr0_value: DR0 value (VVAR value)
			dr0_group: Group of DR rows for this DR0 value
			apic_to_vvar_map: Global APIC-to-VVAR mapping (if None, uses old local calculation)
		"""
		core_columns = {}
		cores_with_vvar = []

		for core_num in sorted(dr0_group['Core_Module'].unique()):
			core_dr = dr0_group[dr0_group['Core_Module'] == core_num]

			# Deduplicate threads
			seen_threads = set()
			threads = []

			for _, dr_row in core_dr.iterrows():
				apic_id = dr_row['APIC_ID']
				thread_num = dr_row.get('Thread', 0)
				key = (apic_id, thread_num)

				if key not in seen_threads:
					seen_threads.add(key)
					apic_hex = f"0x{apic_id:X}" if isinstance(apic_id, int) else str(apic_id)

					# Ensure apic_id is an integer
					apic_int = apic_id if isinstance(apic_id, int) else int(str(apic_id), 16 if '0x' in str(apic_id) else 10)

					# Use global mapping if provided, otherwise fall back to old calculation
					if apic_to_vvar_map and apic_int in apic_to_vvar_map:
						# Use global VVAR number (correct: sequential across all compute dies)
						calculated_vvar_num = apic_to_vvar_map[apic_int]
					else:
						# Fall back to old calculation: VVAR number = 0xC + APIC ID (INCORRECT for multi-die)
						calculated_vvar_num = 0xC + apic_int

					vvar_num_hex = f"0x{calculated_vvar_num:X}"

					threads.append(f"TH:{thread_num}_APIC:{apic_hex}_VVAR_N:{vvar_num_hex}")

			if threads:
				core_columns[f'CORE{core_num}'] = " | ".join(threads) if len(threads) > 1 else threads[0]
				cores_with_vvar.append(core_num)

		core_list = ', '.join(map(str, sorted(cores_with_vvar)))
		return core_columns, core_list

	def _create_dataframe(self, results):
		"""Convert results list to DataFrame with proper column ordering"""
		if not results:
			return pd.DataFrame()

		df = pd.DataFrame(results)

		# Define column order (including Date, Time, and Notes)
		base_cols = ['#', 'Date', 'Time', 'Experiment', 'Content', 'Log_File', 'Data_Origin',
		             'Failing_Seed', 'VVAR', 'Decode', 'Notes', 'CoreList']

		# Find all CORE columns
		core_cols = sorted([col for col in df.columns if col.startswith('CORE')],
		                   key=lambda x: int(x.replace('CORE', '')))

		# Reorder columns
		ordered_cols = base_cols + core_cols
		final_cols = [col for col in ordered_cols if col in df.columns]

		return df[final_cols]


# ============================================================================
# CORE DATA REPORT CLASS - Handles CoreData report generation
# ============================================================================

class CoreDataReportGenerator:
	"""
	Generates CoreData report combining voltage, DR, VVAR, and MCA data.
	Uses iteration-aware matching to properly separate test iterations.
	"""

	def __init__(self, product='GNR'):
		self.product = product
		self.dragon_bucketing = dragon_bucketing

	def generate(self, voltage_df, dr_df, vvar_df, mca_df, test_df, metadata_df=None):
		"""Main entry point for generating CoreData report"""
		if test_df.empty:
			return pd.DataFrame()

		results = []

		for test_idx, test_row in test_df.iterrows():
			test_results = self._process_test_iteration(
				test_row, test_idx, voltage_df, dr_df, vvar_df, mca_df, metadata_df
			)
			results.extend(test_results)

		if not results:
			return pd.DataFrame()

		return pd.DataFrame(results)

	def _process_test_iteration(self, test_row, test_idx, voltage_df, dr_df, vvar_df, mca_df, metadata_df):
		"""Process a single test iteration"""
		folder = test_row.get('Folder', '')  # Folder name with timestamp
		experiment = test_row.get('Experiment', folder)  # Clean experiment name
		iteration = self._extract_iteration(test_row.get('Test Number', ''), test_idx)
		exp_type = test_row.get('Type', '')
		content = test_row.get('Used Content', test_row.get('Running Content', ''))
		row_num = test_row.get('#', test_idx + 1)  # Experiment number from test_df

		# Extract Date and Time from folder name
		date_formatted, time_formatted = extract_date_time_from_folder(folder)

		# Construct log_file name using iteration and clean experiment name
		log_file = f"{iteration}_{experiment}.log" if iteration is not None else f"{experiment}.log"

		# Get failing_content from test_df for Linux, otherwise from metadata
		content_detail = test_row.get('Content Detail', '')
		is_linux = 'linux' in content.lower() or 'linux' in content_detail.lower()

		if is_linux:
			# For Linux content, get from ExperimentReport (test_df)
			failing_content = test_row.get('Content Status', '')
		else:
			# For non-Linux content, get failing_seed from metadata
			_, failing_content = self._get_metadata(metadata_df, folder, iteration)

		# Get iteration-specific data (use folder for matching against raw data)
		iter_voltage = self._filter_by_iteration(voltage_df, folder, iteration)
		iter_dr = self._filter_by_iteration(dr_df, folder, iteration)
		iter_vvar = self._filter_by_experiment(vvar_df, experiment)  # vvar_df has clean experiment name
		iter_mca = self._filter_by_experiment(mca_df, folder)  # mca_df has folder name (from excel_path_dict keys)


		# Build defeature string
		defeature = self._build_defeature_string(test_row)

		# Collect results
		results = []

		# If we have voltage data, create rows for each core
		if not iter_voltage.empty:
			results.extend(self._create_voltage_rows(
				row_num, experiment, content, log_file, exp_type, defeature,
				iter_voltage, iter_dr, iter_vvar, iter_mca, failing_content,
				date_formatted, time_formatted
			))
		# Else if we have DR/VVAR/MCA data, create rows for those
		elif not iter_dr.empty or not iter_vvar.empty or not iter_mca.empty:
			results.append(self._create_summary_row(
				row_num, experiment, content, log_file, exp_type, defeature,
				iter_dr, iter_vvar, iter_mca, failing_content,
				date_formatted, time_formatted
			))

		return results

	def _extract_iteration(self, test_num_raw, fallback_idx):
		"""Extract numeric iteration from Test Number"""
		if isinstance(test_num_raw, str) and 'tdata_' in test_num_raw:
			try:
				return int(test_num_raw.split('_')[1])
			except (IndexError, ValueError):
				return fallback_idx + 1
		elif isinstance(test_num_raw, int):
			return test_num_raw
		return fallback_idx + 1

	def _get_metadata(self, metadata_df, experiment, iteration):
		"""Get metadata for iteration"""
		if metadata_df is None or metadata_df.empty:
			return '', ''

		iter_metadata = metadata_df[
			(metadata_df['Experiment'] == experiment) &
			(metadata_df['Iteration'] == iteration)
		]

		if iter_metadata.empty:
			return '', ''

		log_file = iter_metadata.iloc[0].get('Log_File', '')
		failing_seed = iter_metadata.iloc[0].get('Failing_Seed', '')

		return log_file, failing_seed

	def _filter_by_iteration(self, df, experiment, iteration):
		"""Filter DataFrame by experiment and iteration"""
		if df is None or df.empty:
			return pd.DataFrame()
		return df[(df['Experiment'] == experiment) & (df['Iteration'] == iteration)].copy()

	def _filter_by_experiment(self, df, experiment):
		"""Filter DataFrame by experiment only"""
		if df is None or df.empty:
			return pd.DataFrame()
		return df[df['Experiment'] == experiment].copy()

	def _build_defeature_string(self, test_row):
		"""Build defeature string from test row"""
		parts = []
		exclude = ['None', 'False', None, False, '', 'nan']

		# Core License
		core_license = test_row.get('Core License', '')
		if core_license not in exclude and str(core_license).lower() != 'nan':
			parts.append(f'CoreLicense::{core_license}')

		# Check if PPVC mode
		voltage_set = test_row.get('Voltage set to', '')
		is_ppvc = (voltage_set not in exclude and
		           str(voltage_set).lower() != 'nan' and
		           str(voltage_set).upper() == 'PPVC')

		# Voltage set to (vbump) - only add if not default values (Vnom, VBUMP) or if PPVC
		if voltage_set not in exclude and str(voltage_set).lower() != 'nan':
			voltage_upper = str(voltage_set).upper()
			if voltage_upper not in ['VNOM', 'NOM', 'VBUMP']:
				parts.append(f'VBump::{voltage_upper}')

		# IA (Core) settings - skip voltage if PPVC mode
		ia_parts = []
		core_freq = test_row.get('Core Freq', '')
		if core_freq not in exclude and str(core_freq).lower() != 'nan':
			ia_parts.append(f'F{core_freq}')

		if not is_ppvc:
			core_voltage = test_row.get('Core Voltage', '')
			if core_voltage not in exclude and str(core_voltage).lower() != 'nan':
				try:
					float_voltage = float(core_voltage)
					formatted_voltage = f'({core_voltage})' if float_voltage < 0 else core_voltage
					ia_parts.append(f'V{formatted_voltage}')
				except (ValueError, TypeError):
					ia_parts.append(f'V{core_voltage}')

		if ia_parts:
			parts.append(f'IA::{",".join(ia_parts)}')

		# CFC (Mesh) settings - skip voltage if PPVC mode
		cfc_parts = []
		mesh_freq = test_row.get('Mesh Freq', '')
		if mesh_freq not in exclude and str(mesh_freq).lower() != 'nan':
			cfc_parts.append(f'F{mesh_freq}')

		if not is_ppvc:
			mesh_voltage = test_row.get('Mesh Voltage', '')
			if mesh_voltage not in exclude and str(mesh_voltage).lower() != 'nan':
				try:
					float_voltage = float(mesh_voltage)
					formatted_voltage = f'({mesh_voltage})' if float_voltage < 0 else mesh_voltage
					cfc_parts.append(f'V{formatted_voltage}')
				except (ValueError, TypeError):
					cfc_parts.append(f'V{mesh_voltage}')

		if cfc_parts:
			parts.append(f'CFC::{",".join(cfc_parts)}')

		# HT Disabled
		ht_disabled = test_row.get('HT Disabled (BigCore)', '')
		if ht_disabled not in exclude and str(ht_disabled).lower() != 'nan':
			parts.append(f'HTDIS::{ht_disabled.upper()}')

		# Disabled Modules/Cores
		dis_cores = test_row.get('Dis 2 Cores (Atomcore)', '')
		if dis_cores not in exclude and str(dis_cores).lower() != 'nan':
			parts.append(f'DISMOD::{dis_cores.upper()}')

		# 600W Fuses
		fuses_applied = test_row.get('Unit 600w Fuses Applied', '')
		if fuses_applied not in exclude and str(fuses_applied).lower() != 'nan':
			parts.append(f'600W::{fuses_applied.upper()}')

		return ' | '.join(parts) if parts else ''

	def _create_voltage_rows(self, row_num, experiment, content, log_file, exp_type, defeature,
	                         voltage_df, dr_df, vvar_df, mca_df, failing_content,
	                         date_formatted, time_formatted):
		"""Create rows for each core with voltage data"""
		results = []

		# Extract unique license values from voltage data
		license_values = self._get_license_from_voltage(voltage_df)

		# Group voltage data by core
		for core_num in sorted(voltage_df['Core_Module'].unique()):
			core_voltage = voltage_df[voltage_df['Core_Module'] == core_num]

			# Get voltage statistics
			hi_volt = core_voltage['Voltage'].max()
			lo_volt = core_voltage['Voltage'].min()
			hi_ratio = core_voltage['Ratio'].max()
			lo_ratio = core_voltage['Ratio'].min()

			# Get unique VVAR values for this core
			vvar_values = self._get_unique_vvars_for_core(vvar_df, core_num)
			decode = self._decode_vvar(vvar_values) if vvar_values else ''

			# Get MCA for this core
			mca = self._get_mca_for_core(mca_df, core_num)

			# Build notes
			notes = ''
			if not vvar_values:
				notes = 'No VVAR data found for this core'

			results.append({
				'#': row_num,
				'Date': date_formatted,
				'Time': time_formatted,
				'Experiment': experiment,
				'Content': content,
				'Log_File': log_file,
				'Failing_Content': failing_content,
				'Defeature': defeature,
				'Core_Module': f'CORE{core_num}' if self.product == 'GNR' else f'MODULE{core_num}',
				'HI_Ratio': f'0x{int(hi_ratio):X}' if pd.notna(hi_ratio) else '',
				'Lo_Ratio': f'0x{int(lo_ratio):X}' if pd.notna(lo_ratio) else '',
				'HI_Volt': f'{hi_volt:.6f}' if pd.notna(hi_volt) else '',
				'Lo_Volt': f'{lo_volt:.6f}' if pd.notna(lo_volt) else '',
				'License': license_values,
				'VVAR': vvar_values,  # Add VVAR column with unique values
				'MCA': mca,
				'Notes': notes
			})

		return results

	def _create_summary_row(self, row_num, experiment, content, log_file, exp_type, defeature,
	                        dr_df, vvar_df, mca_df, failing_content,
	                        date_formatted, time_formatted):
		"""Create summary row when no voltage data available"""
		# Get first available VVAR
		vvar_info = vvar_df.iloc[0]['VVAR'] if not vvar_df.empty and 'VVAR' in vvar_df.columns else ''
		decode = self._decode_vvar(vvar_info) if vvar_info else ''

		# Get first available MCA - use correct column name
		mca = mca_df.iloc[0]['Failed MCA'] if not mca_df.empty and 'Failed MCA' in mca_df.columns else ''

		notes = 'No voltage/ratio data available for this iteration'

		return {
			'#': row_num,
			'Date': date_formatted,
			'Time': time_formatted,
			'Experiment': experiment,
			'Content': content,
			'Log_File': log_file,
			'Failing_Content': failing_content,
			'Defeature': defeature,
			'Core_Module': 'No Core Data',
			'HI_Ratio': '',
			'Lo_Ratio': '',
			'HI_Volt': '',
			'Lo_Volt': '',
			'License': '',
			'VVAR': vvar_info,  # Add VVAR column
			'MCA': mca,
			'Notes': notes
		}

	def _get_license_from_voltage(self, voltage_df):
		"""Extract unique license values from voltage data"""
		if voltage_df.empty or 'License' not in voltage_df.columns:
			return ''

		# Get unique non-empty license values
		licenses = voltage_df['License'].dropna().unique()
		licenses = [lic for lic in licenses if lic and lic != '']

		if not licenses:
			return ''

		# Return comma-separated list of unique licenses
		return ', '.join(sorted(set(licenses)))

	def _get_unique_vvars_for_core(self, vvar_df, core_num):
		"""Get unique VVAR VALUES (not numbers) for specific core

		VVAR VALUE is the actual register value (DR0) like 0x600D600D, 0xA4000000
		VVAR NUMBER is the index 0xC, 0xD, etc. (stored in CORE column metadata)

		For CoreData report, we need VVAR VALUES from the main VVAR column.
		"""
		if vvar_df.empty:
			return ''

		unique_vvars = set()
		core_col = f'CORE{core_num}'

		# Get VVAR VALUES from main VVAR column for this core
		if 'VVAR' in vvar_df.columns and core_col in vvar_df.columns:
			for _, row in vvar_df.iterrows():
				# Check if this core has data in the CORE column
				core_data = row.get(core_col, '')
				if pd.isna(core_data) or core_data == '':
					continue

				# Get the VVAR VALUE from the main VVAR column (this is DR0 or log file VVAR)
				vvar_val = row.get('VVAR', '')
				if vvar_val and pd.notna(vvar_val) and vvar_val != '':
					unique_vvars.add(str(vvar_val).upper())  # Normalize to uppercase

		if not unique_vvars:
			return ''

		# Return comma-separated unique values (sorted for consistency)
		return ', '.join(sorted(unique_vvars))

	def _get_vvar_for_core(self, vvar_df, core_num):
		"""Get VVAR value for specific core"""
		if vvar_df.empty:
			return ''

		core_col = f'CORE{core_num}'
		if core_col in vvar_df.columns:
			core_vvars = vvar_df[vvar_df[core_col].notna()][core_col].tolist()
			if core_vvars:
				return core_vvars[0] if len(core_vvars) == 1 else '; '.join(core_vvars)

		# Fallback to VVAR column
		if 'VVAR' in vvar_df.columns:
			return vvar_df.iloc[0]['VVAR']

		return ''

	def _get_mca_for_core(self, mca_df, core_num):
		"""Get MCA data for specific core with uniqueness"""
		if mca_df.empty or 'Failed MCA' not in mca_df.columns:
			return ''

		core_mcas = []
		search_word = 'CORE' if self.product == 'GNR' else 'MODULE'

		for _, mca_row in mca_df.iterrows():
			failed_mca = mca_row['Failed MCA']
			if pd.isna(failed_mca) or failed_mca == '':
				continue

			# Check if this MCA is for this core
			# MCA format: "CDIE{compute}::CORE{num}::ErrorType::MCACOD" (GNR)
			# MCA format: "CDIE{compute}::MODULE{num}::ErrorType::MCACOD" (CWF)
			# Check for exact pattern first: ::{search_word}{core_num}::
			if f'::{search_word}{core_num}::' in str(failed_mca).upper():
				# Add only if not already in list (ensure uniqueness)
				if failed_mca not in core_mcas:
					core_mcas.append(failed_mca)
			# Fallback: check for CORE{num} or MODULE{num} anywhere in string
			elif f'{search_word}{core_num}' in str(failed_mca).upper():
				if failed_mca not in core_mcas:
					core_mcas.append(failed_mca)

		return '; '.join(core_mcas) if core_mcas else ''

	def _decode_vvar(self, vvar_value):
		"""Decode VVAR using dragon_bucketing"""
		if not vvar_value or not self.dragon_bucketing:
			return ''

		try:
			bucket = self.dragon_bucketing.bucket(
				vvar=vvar_value,
				product=self.product,
				seed_name='',
				is_os=False
			)
			return f"{bucket.main} | {bucket.sub}"
		except Exception:
			return ''


# ============================================================================
# PUBLIC API FUNCTIONS - Maintain backward compatibility
# ============================================================================

def parse_vvars_from_zip(zip_path_dict, test_df, product='GNR', vvar_filter=None,
                          skip_array=None, dr_df=None, metadata_df=None, experiment_index_map=None):
	"""
	Parse VVAR data from ZIP files and DebugFrameworkLogger DR data.

	Args:
		zip_path_dict: Dictionary of ZIP file paths
		test_df: Test DataFrame with experiment information (must have # and Experiment columns)
		product: Product name for dragon_bucketing (default: 'GNR')
		vvar_filter: List of VVAR values to ignore
		skip_array: List of strings to skip
		dr_df: DataFrame with DR data
		metadata_df: Experiment metadata with Iteration, Log_File and Failing_Seed
		experiment_index_map: Map of folder names to experiment numbers (optional)

	Returns:
		DataFrame with VVAR data
	"""
	parser = VVARParser(product=product, vvar_filter=vvar_filter, skip_array=skip_array)
	return parser.parse_from_zip(zip_path_dict, test_df, dr_df, metadata_df, experiment_index_map)


def create_core_data_report(voltage_df, dr_df, vvar_df, mca_df, test_df, metadata_df=None, product='GNR'):
	"""
	Create CoreData report combining voltage, DR, VVAR, and MCA data.

	Args:
		voltage_df: Voltage data with Iteration column
		dr_df: DR data with Iteration column
		vvar_df: VVAR data from zip files
		mca_df: MCA data
		test_df: Test configuration data
		metadata_df: Experiment metadata
		product: Product type (GNR or CWF)

	Returns:
		DataFrame with CoreData report
	"""
	generator = CoreDataReportGenerator(product=product)
	return generator.generate(voltage_df, dr_df, vvar_df, mca_df, test_df, metadata_df)


def test():

	#zip_file_path = r'R:/DebugFramework/GNR/754F39Y300403/cr03tppv0007en/20250707/20250707_192129_T0_BaselineChecks-VoltageSweeps_Sweep/ExperimentData.zip'
	#zip_file_path = r'R:/DebugFramework/GNR/754F39Y300403/cr03tppv0162en/20250728/20250728_112725_T8_Pseudo_HTDIS_Loops\ExperimentData.zip'
	zip_file_path = r'R:/DebugFramework/GNR/74698UA600040\cr03tppv0165en\20250725\20250724_154318_T1_Shmoo_Core_Volt_vs_Freq_Shmoo\ExperimentData.zip'

	content_type = 'Sandstone'  # Set the content type here
	pass_array = []#["exit: pass"]
	fail_array = []#["exit: fail", "not ok"]
	skip_array = ["0Sanity"]

	data = parse_zip_files(zip_file_path=zip_file_path, content=content_type, pass_array = pass_array, fail_array = fail_array, skip_array = skip_array , exclusion_string='pysv', casesens=False)

	print(data)

def test_log_file_parser():
	path = r'R:\DebugFramework\GNR\75VP061900080'
	Excel_kw = 'Summary'
	zip_kw = 'ExperimentData'
	output_file = r'C:\ParsingFiles\DebugFramework\Framework_Report.xlsx'

	data = find_files(base_folder=path, excel_keyword=Excel_kw, zip_keyword=zip_kw)

	log_path_dict = create_file_dict(data, 'Log')
	excel_path_dict = create_file_dict(data, 'Excel')
	zip_path_dict = create_file_dict(data, 'ZIP')

	print('Excel Files', excel_path_dict , '\n')
	print('Zip Files', zip_path_dict , '\n')
	print('Log Files', log_path_dict , '\n')
	print('Data Files', data , '\n')

	# Parse log files and create test data DataFrame
	test_df = parse_log_files(log_path_dict)

	# Example usage:

	#excel_files = [info['path'] for info in excel_path_dict.values()]
	print('file:', excel_path_dict)
	log_summary = LogSummaryParser(excel_path_dict=excel_path_dict, test_df=test_df)
	report_df, mca_df = log_summary.parse_mca_tabs_from_files()
	print(report_df)
	print("")
	print(mca_df)

	# Output results using tabulate
	#print("\nTest Data DataFrame:")
	#print(tabulate(test_df, headers='keys', tablefmt='grid'))

	# Save DataFrames to Excel
	# save_to_excel(data, test_df, filename=output_file)

if __name__ == "__main__":
	test_log_file_parser()
