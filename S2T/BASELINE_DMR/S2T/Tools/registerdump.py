import os
import sys
import pandas as pd
from datetime import datetime

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
