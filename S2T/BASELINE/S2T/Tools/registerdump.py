import os
import sys
import pandas as pd
import re
import importlib
from datetime import datetime
from collections import defaultdict

# Append the Main Scripts Path
FILE_PATH = os.path.abspath(os.path.dirname(__file__))
MAIN_PATH = os.path.join(FILE_PATH, '..')
class RegisterDump():

	def __init__(self, sv, ipc, fuse_base, dump_file):
		self.sv = sv
		self.ipc = ipc
		self.fuse_base = fuse_base
		self.dump_file = dump_file
		self.dump_data = []
		self.dump_time = None
		self._register_dump_file = None
		self._regs_df = None
		self._check_defaults()
		self._check_dump_file()

	def _check_defaults(self):
		self.logregisters_path = r'C:\Temp\RegisterDumpLogs'

		if not os.path.exists(self.logregisters_path):
			os.makedirs(self.logregisters_path)

	def _check_dump_file(self):
		# Check if provided dump file format is correct
		# Considering output will be a .csv file
		# Also checks if path for the provded file exists

		if self.dump_file is not None:
			if not self.dump_file.endswith('.csv'):
				print("Provided dump file format is not supported. Please provide a .csv file.")
				sys.exit(1)
			if not os.path.exists(os.path.dirname(self.dump_file)):
				print("Provided dump file path does not exist. Please provide a valid path.")
				sys.exit(1)

	def logregisters(self):
		print("Parsing register dump...")

		self.dump_time = datetime.now().strftime("%Y-%m-%d %H_%M_%S")
		self._register_dump_file = os.path.join(self.logregisters_path, f"{self.dump_time}_registerlist.log")

		# Generate the register dump using the provided parameters
		# This uses the PythonSV object passed to generate no need to declare SV nor IPC
		print('Generating register dump, this may take a few moments...')
		print(f"Dump will be saved to: {self._register_dump_file}")
		self.fuse_base.logregisters(self._register_dump_file)

		print("Register dump generated successfully.")

	def _process_dump(self):
		dump_file = self._register_dump_file
		if dump_file is None:
			print("No register dump file available.")
			return

		# This function will parse the dump file and convert it into a structured list
		# Raw data is in the format --> cha_cms_scf_gnr_maxi_coretile_c4_r5.repair_memory_repair_word_3=0x0
		# Will be converted to a list of dictionaries with keys: 'register', 'value', and 'timestamp'

		with open(dump_file, 'r') as f:
			lines = f.readlines()

		for line in lines:
			line = line.strip()
			if '=' in line:
				register, value = line.split('=', 1)
				register = register.strip()
				value = value.strip()
				# Store the register and value in a structured format (e.g., a list of dictionaries)
				# For demonstration, we'll just print them out
				print(f"Register: {register}, Value: {value}, Timestamp: {self.dump_time}")
				self.dump_data.append({'register': register, 'value': value, 'timestamp': self.dump_time})

	def _get_registers_info(self):
		# This function is used to get pythonsv data from the dump data
		# Checking the info on each register and getting the corresponding data from pythonsv
		# Data is in the format:

		'''{'original_name': 'scf_gnr_maxi_coretile_c9_r2/FIVR_PCBCBB_config2_tdp_dcm',
			'IOSFSBEP': 2,
			'IOSFSBHierarchicalPortID': 1,
			'Instance': 'FIVR_PCBCBB_config2_tdp_dcm',
			'IOSFSBPortID': 194,
			'RamAddr': 9317,
			'PRamAddr': 9317,
			'CatLockoutID': 0,
			'FuseMapOrder': 1,
			'VF_Name': 'scf_gnr_maxi_coretile_c9_r2/FIVR_PCBCBB_config2_tdp_dcm_DF',
			'FUSE_WIDTH': 4,
			'RcvrAddr': 17706,
			'StartBit': 4,
			'default': 0,
			'IPResetType': 'prim_rst_b',
			'Group': 'DF',
			'Category': 'IntelHVM',
			'RequestType': 'HighDensity',
			'LLDD': False,
			'GroupNumber': 0,
			'Shared': True,
			'SharedTag': 'fivrhip_4p_Group_core.PCBCBB_config2_tdp_dcm',
			'SharedTagPivot': 'Master',
			'PullOnce': False,
			'BlkOnDbg': False,
			'VFOverrideDisable': False,
			'JTagRD': True,
			'JTagWR': True,
			'CSRRD': True,
			'CSRWR': True,
			'RD4Err': True,
			'LockoutValidIDTag': None,
			'IPOwner': 'sghosh4',
			'RTLSignalPath': 'soc_tb.soc.scf_gnr_maxi_coretile_c9_r2.cv_top.xi_fivr.fivrtop.fivrzooggen[0].fivr_parzoog.dig_right.fivrhip_zoog_right_regs_wrapper_i.fivrhip_zoog_right_regs.PCBCBB_config2.tdp_dcm',
			'EncodingValues': 'HWRESET,0',
			'EncodingValueType': 'KeyValuePairs',
			'Units': None,
			'Class': 'Parametric',
			'SubClass': 'PowerDelivery',
			'Consumer': 'IPHardware',
			'ExternalCustomerVisible': False,
			'description': 'PWM dead time settings for P in DCM ;',
			'Puller': None,
			'CRIID': None,
			'ip_name': 'scf_gnr_maxi_coretile_c9_r2',
			'aliases_original_path': 'fuses.scf_gnr_maxi_coretile_c0_r1.fivr_pcbcbb_config2_tdp_dcm',
			'numbits': 4}'''

		if self.dump_data is None:
			print("No dump data available to get register info.")
			return
		svregisters_info = []

		for entry in self.dump_data:
			register = entry['register']
			value = entry['value']
			timestamp = entry['timestamp']

			svregisters_info.append(self.fuse_base.getbypath(register).info)

		# Convert info dictionary data to a dataframe to later pass it to excel
		self._regs_df = pd.DataFrame(svregisters_info)

	def _generate_dump_report(self):
		# This function will generate a report based on the dump data and the register info obtained from pythonsv
		# The report will be saved in an Excel file with the following format:
		# | Register | Value | Timestamp | IPOwner | Description | ... |
		# The columns will be based on the keys of the info dictionary obtained from pythonsv

		if self._regs_df is None:
			print("No register info available to generate report.")
			return

		# Combine the dump data with the register info
		dump_report_df = self._regs_df.copy()

		# Save the report to an Excel file
		if self.dump_file is None:
			report_file = os.path.join(self.logregisters_path, f"{self.dump_time}_register_report.csv")
			# Set to default folder and default naming for Report if no provided
		else:
			report_file = self.dump_file
		dump_report_df.to_csv(report_file, index=False)
		print(f"Register dump report generated successfully: {report_file}")

	def dump_registers(self):
		self.logregisters()
		self._process_dump()
		self._get_registers_info()
		self._generate_dump_report()


class FuseFileGenerator():
	"""
	Generate fuse configuration files from register arrays.
	
	This class takes an array of fully-qualified register assignments and converts them
	into a fuse file format compatible with fusefilegen.py.
	Supports multiple products (GNR, DMR, CWF) by dynamically loading validation patterns.
	
	Example input:
		['sv.socket0.compute0.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point0= 0xaa',
		 'sv.socket0.compute1.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point0= 0xaa']
	
	Example output (.fuse file):
		[sv.socket0.compute0.fuses]
		pcu.pcode_ddrd_ddr_vf_voltage_point0 = 0xaa
		
		[sv.socket0.compute1.fuses]
		pcu.pcode_ddrd_ddr_vf_voltage_point0 = 0xaa
	"""
	
	def __init__(self, fusemodule, register_array, product='gnr', output_file=None):
		"""
		Initialize the FuseFileGenerator.
		
		Args:
			register_array: List of register assignments in format 'full.path.to.register=value'
			product: Product name ('gnr', 'dmr', 'cwf') - determines validation patterns
			output_file: Path to output fuse file. If None, auto-generates in default directory.
		"""
		self.fusemodule = fusemodule
		self.register_array = register_array
		self.product = product.lower()
		self.output_file = output_file
		self.parsed_data = defaultdict(dict)
		self.errors = []
		self.warnings = []
		self.fuse_file_path = None
		self.VALID_SECTION_PATTERNS = []
		self._load_product_patterns()
		self._check_defaults()
	
	def _load_product_patterns(self):
		"""
		Load validation patterns from the provided fusefilegen module.
		
		The fusemodule parameter should be the product-specific fusefilegen module
		(e.g., S2T.product_specific.gnr.fusefilegen) passed during initialization.
		"""
		try:
			# Get the FuseFileParser class and extract VALID_SECTION_PATTERNS
			parser_class = self.fusemodule.FuseFileParser
			self.VALID_SECTION_PATTERNS = parser_class.VALID_SECTION_PATTERNS
			
			print(f"Loaded validation patterns for product: {self.product.upper()}")
			
		except AttributeError as e:
			self.errors.append(
				f"FuseFileParser class or VALID_SECTION_PATTERNS not found in provided fusemodule. "
				f"Error: {e}"
			)
			print(f"ERROR: {self.errors[-1]}")
		except Exception as e:
			self.errors.append(f"Error loading product patterns from fusemodule: {e}")
			print(f"ERROR: {self.errors[-1]}")
	
	def _check_defaults(self):
		"""Set up default paths, reusing logic from RegisterDump"""
		self.fusefile_path = r'C:\Temp\RegisterDumpLogs'
		
		if not os.path.exists(self.fusefile_path):
			os.makedirs(self.fusefile_path)
	
	def _parse_register_entry(self, entry):
		"""
		Parse a single register entry into section, register, and value.
		
		Args:
			entry: String like 'sv.socket0.compute0.fuses.pcu.register_name= 0xaa'
		
		Returns:
			Tuple of (section, register, value) or None if invalid
		"""
		# Remove whitespace and split by '='
		entry = entry.strip()
		if '=' not in entry:
			self.errors.append(f"Invalid entry format (no '='): {entry}")
			return None
		
		path, value = entry.split('=', 1)
		path = path.strip()
		value = value.strip()
		
		# Find the section (everything up to and including .fuses)
		# Try to match against all valid patterns to extract the section
		section = None
		for pattern in self.VALID_SECTION_PATTERNS:
			# Convert validation pattern to extraction pattern
			# Remove ^ and $ anchors, capture the entire pattern
			extraction_pattern = pattern.replace('^', '').replace('$', '')
			extraction_pattern = f'({extraction_pattern})'
			
			match = re.search(extraction_pattern, path)
			if match:
				section = match.group(1)
				break
		
		if not section:
			self.errors.append(
				f"Could not extract valid fuse section from: {entry}. "
				f"Product: {self.product.upper()}"
			)
			return None
		
		# Everything after the section is the register name
		register = path[len(section):].lstrip('.')
		
		if not register:
			self.errors.append(f"Empty register name in: {entry}")
			return None
		
		return section, register, value
	
	def parse_array(self):
		"""Parse the register array into structured data grouped by section"""
		print(f"Parsing {len(self.register_array)} register entries...")
		
		for entry in self.register_array:
			result = self._parse_register_entry(entry)
			if result:
				section, register, value = result
				
				# Check for duplicates
				if register in self.parsed_data[section]:
					self.warnings.append(
						f"Duplicate register '{register}' in section '{section}'. "
						f"Overwriting {self.parsed_data[section][register]} with {value}"
					)
				
				self.parsed_data[section][register] = value
		
		if self.errors:
			print(f"Parsing completed with {len(self.errors)} error(s)")
			for error in self.errors:
				print(f"  ERROR: {error}")
			return False
		
		if self.warnings:
			print(f"Parsing completed with {len(self.warnings)} warning(s)")
			for warning in self.warnings:
				print(f"  WARNING: {warning}")
		
		print(f"Successfully parsed {len(self.parsed_data)} section(s)")
		return True
	
	def generate_fuse_file(self):
		"""Generate the fuse file from parsed data"""
		if not self.parsed_data:
			print("No data to generate. Did you run parse_array()?")
			return False
		
		# Generate output filename if not provided
		if self.output_file is None:
			timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
			self.fuse_file_path = os.path.join(self.fusefile_path, f"{timestamp}_generated.fuse")
		else:
			self.fuse_file_path = self.output_file
			# Create directory if it doesn't exist
			os.makedirs(os.path.dirname(self.fuse_file_path), exist_ok=True)
		
		# Write the fuse file
		try:
			with open(self.fuse_file_path, 'w', encoding='utf-8') as f:
				# Write header comment
				f.write(f"# Fuse file generated from register array\n")
				f.write(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
				f.write(f"# Total sections: {len(self.parsed_data)}\n")
				f.write(f"# Total registers: {sum(len(regs) for regs in self.parsed_data.values())}\n")
				f.write("\n")
				
				# Write each section
				for section in sorted(self.parsed_data.keys()):
					f.write(f"[{section}]\n")
					
					# Write registers for this section, sorted alphabetically
					for register in sorted(self.parsed_data[section].keys()):
						value = self.parsed_data[section][register]
						f.write(f"{register} = {value}\n")
					
					f.write("\n")  # Blank line between sections
			
			print(f"Fuse file generated successfully: {self.fuse_file_path}")
			return True
			
		except Exception as e:
			self.errors.append(f"Error writing fuse file: {e}")
			print(f"ERROR: {e}")
			return False
	
	def create_fuse_file(self):
		"""
		Main method to create fuse file from register array.
		Combines parsing and generation steps.
		"""
		if self.parse_array():
			return self.generate_fuse_file()
		return False
	
	def get_report(self):
		"""Get a report of the generation results"""
		total_registers = sum(len(regs) for regs in self.parsed_data.values())
		return {
			'sections': list(self.parsed_data.keys()),
			'section_count': len(self.parsed_data),
			'register_count': total_registers,
			'errors': self.errors,
			'warnings': self.warnings,
			'output_file': self.fuse_file_path
		}
