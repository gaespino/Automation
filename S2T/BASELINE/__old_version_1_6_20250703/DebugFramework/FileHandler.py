import sys
import os
from datetime import datetime
import shutil
import pandas as pd
import openpyxl
import logging
import socket
import zipfile
import json

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import PPV.MCAparser as parser
import PPV.PPVReportMerger as merger

import importlib

importlib.reload(parser)
importlib.reload(merger)

#####################################################################################
##
##              DebugFramework Logger
##
#####################################################################################

class printlog():
	
	def __init__(self, log_file):
		self.log_file = log_file
		#self.event_type = event_type

	def initlog(self):
		# Initialize log file
		if self.log_file:
			with open(self.log_file, 'w', encoding='utf-8') as f:
				f.write('- SystemDebugFramework Logging')  # Create or override the log file

	def Debuglog(self, message, console_show= True,event_type =0 ):
		if console_show: print(message)
		if self.log_file: self.savetofile(message)

	def savetofile(self, message):
		with open(self.log_file, 'a', encoding='utf-8') as f:
			if isinstance(message, pd.DataFrame):
				message = message.to_string()
			elif isinstance(message, list):
				message = '\n'.join(map(str, message))  # Convert list to string
		
			f.write(message + '\n')

class FrameworkLogger:
	def __init__(self, log_file='app.log', logger_name = 'FrameworkLogger', console_output=False, reset_handlers=True):
		self.log_file = log_file
		self.console_output = console_output
		self.logger = logging.getLogger(logger_name)
		self.logger.setLevel(logging.DEBUG)
		# Reset handlers if reset_handlers is True
		if reset_handlers:
			self.logger.handlers = []		
		# Create file handler
		file_handler = logging.FileHandler(self.log_file, mode='w')
		file_handler.setLevel(logging.DEBUG)
		
		# Define log format
		formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
		file_handler.setFormatter(formatter)
		
		# Add file handler to logger if not already added
		self.logger.addHandler(file_handler)

		# Create console handler
		if self.console_output:
			console_handler = logging.StreamHandler()
			console_handler.setLevel(logging.DEBUG)
			#console_handler.setFormatter(formatter)
			
		#	# Add console handler to logger if not already added
		#	if not any(isinstance(handler, logging.StreamHandler) for handler in self.logger.handlers):
			self.logger.addHandler(console_handler)

	def log(self, message, event_type=1):
		event_types = {
			0: logging.DEBUG,
			1: logging.INFO,
			2: logging.WARNING,
			3: logging.ERROR,
			4: logging.CRITICAL
		}
			
		if event_type in event_types:
			self.logger.log(event_types[event_type], message)
			#if event_type <= 1 and self.console_output: print(message)
		else:
			self.logger.error("Invalid event type: %s", event_type)

#####################################################################################
##
##              Functions for file Handling and Script initilization
##
#####################################################################################

# Functions to load recipes file
def extract_data_from_named_table(sheet):
	"""
	Extracts data from a named table within an Excel sheet.
	
	param: sheet = An openpyxl worksheet object from which data is to be extracted.
	return: A dictionary containing 'Field' and 'Value' pairs if the table is found, otherwise None.
	"""    
	
	# Iterate over all tables in the sheet
	for table in sheet.tables.values():
		# Get the table range
		table_range = sheet[table.ref]
		
		# Check if the first row contains 'Field' and 'Value'
		headers = [cell.value for cell in table_range[0]]
		if 'Field' in headers and 'Value' in headers:
			# Initialize a dictionary to store the values
			data = {}
			
			# Iterate over the rows starting from the second row
			for row in table_range[1:]:
				field = row[headers.index('Field')].value
				value = row[headers.index('Value')].value
				data[field] = value
			
			return data
	return None

def process_excel_file(file_path):
	"""
	Processes an Excel file to extract data from named tables in each sheet.
	
	param: file_path = Path to the Excel file to be processed.
	return: A dictionary containing data from all sheets, with sheet names as keys.
	"""
	# Load the Excel file
	workbook = openpyxl.load_workbook(file_path, data_only=True)
	
	# Dictionary to store data from all sheets
	all_data = {}
	
	# Iterate over each sheet
	for sheet_name in workbook.sheetnames:
		sheet = workbook[sheet_name]
		data = extract_data_from_named_table(sheet)
		
		if data:
			all_data[sheet_name] = data
	
	return all_data

def create_tabulated_format(data_from_sheets):
	"""
	Creates a tabulated DataFrame from extracted data across multiple sheets.
	
	param: data_from_sheets = A dictionary containing data from multiple sheets.
	return: A pandas DataFrame with fields as rows and sheet names as columns.
	"""
	# Get all unique fields from the data
	all_fields = []#set()
	for data in data_from_sheets.values():
		all_fields = data.keys()  #.update(data.keys())
		break
	# Create a list to store DataFrame rows
	rows = []
	
	# Populate the rows list
	for field in all_fields:
		row_data = {'Fields': field}
		for sheet_name, data in data_from_sheets.items():
			row_data[sheet_name] = data.get(field, 'None')
		rows.append(row_data)
	
	# Create the DataFrame using pd.concat
	tabulated_df = pd.DataFrame(rows, columns=['Fields'] + list(data_from_sheets.keys()))
	
	return tabulated_df

# Function to create logs folder
def create_log_folder(logs_dest, description =None):
	"""
	Creates a log folder with a timestamp and optional description.
	
	:param logs_dest: Destination path where the log folder will be created.
	:param description: Optional description to append to the folder name.
	:return log_folder_path: The path to the created log folder.
	"""

	current_datetime = datetime.now().strftime('%Y%m%d_%H%M%S')
	add_name = f'_{description}' if description != None else ''
	log_folder_path = os.path.join(logs_dest, f'{current_datetime}{add_name}')
	create_folder_if_not_exists(log_folder_path)
	return log_folder_path

# Function to create folder if it does not exist
def create_folder_if_not_exists(folder):
	"""
	Creates a folder if it does not already exist.
	
	:param folder: Path to the folder to be created.
	:return folderisthere: Boolean indicating whether the folder already existed.
	"""

	if not os.path.exists(folder):
		os.makedirs(folder)
		print(f' --- Created folder: {folder}')
		folderisthere = False
	else:
		print(f' --- Folder already exists: {folder}')
		folderisthere = True
	return folderisthere

def create_path(folder, file):
	"""
	Creates a file path by joining a folder and file name.
	
	:param folder: Path to the folder.
	:param file: Name of the file.
	:return filepath: The full file path.
	"""

	filepath = os.path.join(folder, file)
	return filepath

# Function to copy files from source to destination
def copy_files(src, dest, uinput = ""):
	"""
	Copies files from a source directory to a destination directory, with user confirmation.
	
	:param src: Source directory path.
	:param dest: Destination directory path.
	:param uinput: User input for file override confirmation ('Y' or 'N').
	"""
	user_input = uinput
	while "N" not in user_input and "Y" not in user_input:
		user_input = input(f"Do you want to override files from {src} to {dest}? (Y/N) [N]: ").strip().upper() or 'N'

	for filename in os.listdir(src):
		full_file_name = os.path.join(src, filename)
		if os.path.isfile(full_file_name):
			if os.path.exists(dest):

				if user_input == 'Y':
					shutil.copy(full_file_name, dest)
					print(f'Copied {filename} to {dest}')
				else:
					print(f'Skipping file replace {dest}')

def merge_mca_files(input_folder: str, output_file: str):
	"""
	Merges MCA Excel files from an input folder into a single output file.
	
	:param input_folder: Path to the folder containing MCA Excel files.
	:param output_file: Path to the output Excel file.
	"""	
	merger.merge_excel_files(input_folder=input_folder, output_file=output_file, prefix = 'MCA_Report')

def decode_mcas(name:str, week:str, source_file:str, label:str, path:str, product:str):
	"""
	Decode MCAs from a Raw Data Debug Framework Summary File
	
	:param name: Name to be used on the PPV Report.
	:param week: WW to be used in the PPV Report.
	:param source_file: Path to the MCA Log file in xlsx format to be used to generate the report
	:param label: Custom Label to add on the file name of the report
	:param path: Path where the report will be saved
	:param product: Product flavour for ex. GNR, CWF, SPR,...

	"""
	
	PPVMCAs = parser.ppv_report(name=name, week=week, label=label, source_file=source_file, report = path, reduced = True, overview = False, decode = True, mcdetail= False, product = product)
	PPVMCAs.run(options = ['MESH', 'CORE'])

# Looks for failing seed
def extract_fail_seed(log_file_path: str, 
					  PassString: list = ["Test Complete"], 
					  FailString: list = ["Test Failed"], 
					  HangString: list = ["running MerlinX.efi"], 
					  CheckString: list = [r"CHANGING BACK TO DIR: FS1:\EFI"], casesens=False):
	"""
	Extracts the failing seed from a log file.
	
	:param log_file_path: Path to log file.
	:param PassString: Search Strings to declare a PASS condition.
	:param FailString: Search Strings to declare a FAIL condition.
	:param HangString: Search Strings to declare a HANG condition.
	:param CheckString: Search Strings to declare a CHECK condition.
	:return obj_file: The failing seed or None if not found.
	"""
	
	if not casesens:
		PassString = [p.lower() for p in PassString]
		FailString = [f.lower() for f in FailString]
		HangString = [h.lower() for h in HangString]
		CheckString = [c.lower() for c in CheckString]

	def extract_obj_file(log_file_path):
		obj_file = None
		
		# Search from top to bottom for "Test Failed"
		with open(log_file_path, 'r') as file:
			lines = file.readlines()
			for line in lines:
				for search_string in FailString:
					if (search_string in line) if casesens else (search_string.lower() in line.lower()):
						obj_file = extract_obj_from_line(line)
						obj_file = obj_file.replace('.obj','') + '_FAIL' if obj_file != None else None
						return obj_file

			# If not found, search from bottom to top for "running MerlinX.efi"
			if not obj_file:
				for line in reversed(lines):
					
					# Search for Pass String in lines
					for search_string in PassString:
						if (search_string in line) if casesens else (search_string.lower() in line.lower()):
							obj_file = "PASS"   
							return obj_file			

					# Search for CHECK String String in lines					
					for search_string in CheckString:
						if (search_string in line) if casesens else (search_string.lower() in line.lower()):
							obj_file = "_CHECK_MCA"
							return obj_file                        

					# Search for Hang String in lines					
					for search_string in HangString:
						if (search_string in line) if casesens else (search_string.lower() in line.lower()):
							obj_file = extract_obj_from_line(line)
							obj_file = obj_file.replace('.obj','') + '_HANG' if obj_file != None else None
							return obj_file

		return obj_file

	def extract_obj_from_line(line):
		start = line.rfind('\\') + 1
		end = line.rfind('.obj')
		if start != -1 and end != -1:
			return line[start:end + 4]
		return None

	# Usage example
	#log_file_path = 'path_to_log_file.log'
	result = extract_obj_file(log_file_path)
	if result:
		#print(f'Found .obj file: {result}')
		return result
	else:
		#print('No .obj file found.')
		return None

def loops_fails(path: str):
	"""
	Iterates over log files in a directory to extract failing seeds.
	
	:param path: Path for seed files.
	:return seeds: A dictionary with filenames and their corresponding failing seeds.
	"""

	seeds = {'file':[], 'seed':[]}
	for file in os.listdir(path):
		if file.endswith('.log'):
			file_path = os.path.join(path, file)
			seed = extract_fail_seed(file_path)
			seeds['file'].append(file)
			seeds['seed'].append(seed)
			print(file,seed)
	return seeds

def save_excel_to_json(file_path, experiments):
	try:
		# Serialize the experiments data to JSON
		with open(file_path, 'w') as json_file:
			json.dump(experiments, json_file, indent=4)
		print("Save Config", "Configuration saved successfully.")
	except Exception as e:
		print("Save Config", f"Failed to save configuration: {e}")

def load_json_file(file_path):
	with open(file_path, 'r') as json_file:
		experiments = json.load(json_file)
	return experiments

#####################################################################################
##
##              Custom script loader -- Reads a file and execute each line
##
#####################################################################################

def execute_file(file_path: str, logger = None):
	"""
	Executes Python code lines from a .txt file.
	
	:param file_path: Path to the .txt file containing Python code lines to be executed.
	:param logger: Logging instance if not used will use print
	"""

	if logger == None: logger = print
	print('-- Starting file execution ---')
	try:
		with open(file_path, 'r') as file:
			lines = file.readlines()
		
		for line in lines:
			stripped_line = line.strip()
			if stripped_line:
				try:
					logger(f'> Executing: {stripped_line}')
					exec(stripped_line)
				except Exception as e:
					logger(f"Error executing line: {stripped_line}\nException: {e}")
	except FileNotFoundError:
		logger(f"File not found: {file_path}")
	except Exception as e:
		logger(f"An error occurred: {e}")
	print(' -- Ending file execution ---')
	# Example usage
	#execute_file('path/to/your/file.txt')

#####################################################################################
##
##              Database Handling Scripts
##
#####################################################################################

def copy_folder(src, dest, visual = "unknown", zipdata=True , logger = None):
	"""
	Copies a folder content into another location, it can be a complete folder copy or a zip file of it.

	:param src: Source Folder
	:param dest: Destination Folder
	:param visual: Unit Visual ID to be included in name
	:param zip_filter: Files to not be included in zip file
	:param zipdata: Option to use a zipfile instead of the folder
	:param logger: Logging instance if not used will use print
	"""

	# Zip File Filter options, Search for words and copy the files instead of including inside zipfile
	LoggerFileSearch = "FrameworkLogger.log"
	DataFileSearch = "Data.xlsx"
	zip_filter = True

	def zip_folder_contents(zip_file_name, dest_path):
		r"""
		Creates a zip file from a folder

		:param src: Path to the folder to be compressed into a zip file.
		:param zip_file_name: Full path of the zip file, include the extension (\path\file.zip)
		:param zip_filter: Filters out of zip and copy files ending with FrameworkLogger.log and Data.xlsx files
		"""
			
		# Create a zip file with the folder name
		with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
			# Iterate through all files in the folder
			for root, _, files in os.walk(src):
				for file in files:
					file_path = os.path.join(root, file)
					# Add file to the zip, using relative path
					if zip_filter and (file.endswith(LoggerFileSearch) or file.endswith(DataFileSearch)):
						shutil.copy(file_path, dest_path)
						continue
					zipf.write(file_path, os.path.relpath(file_path, src))

	# Check if destination path exists
	if logger == None: logger = print 
	if not os.path.exists(dest):
		raise Exception(f"Destination folder ({dest}) does not exist, files are not being copied.")

	# Get hostname and current date
	hostname = socket.gethostname()
	current_date = datetime.now().strftime("%Y%m%d")
	src_folder_name = os.path.basename(src.rstrip('/\\'))

	# Create destination path with hostname and current date (includes source folder name)
	
	dest_path = os.path.join(dest, visual, hostname.lower(), current_date, src_folder_name)

	if zipdata:
		# Create zipfile with source folder name
		#dest_path = os.path.join(dest, hostname.lower(), current_date, visual)

		zip_file_name = f'ExperimentData.zip'
		zip_file_path = os.path.join(dest_path, zip_file_name)
		os.makedirs(dest_path, exist_ok=True)

		zip_folder_contents(zip_file_path, dest_path)
		logger(f'Data operation Succesfull !!! --> Check file: {zip_file_path}')
	else:
		# Create destination path with hostname and current date (includes source folder name)
		#dest_path = os.path.join(dest, hostname.lower(), current_date, visual, src_folder_name)
		os.makedirs(dest_path, exist_ok=True)

		# Copy contents from source to destination
		try:
			shutil.copytree(src, dest_path, dirs_exist_ok=True)
			logger(f'Data operation Succesfull !!! --> Check Folder: {dest_path}')
		except Exception as e:
			logger(f"An error occurred: {e}")
	return dest_path


#####################################################################################
##
##              TTL Files Changes -- Usage for SERIAL and SSH files (WIP)
##
#####################################################################################

def validate_com_port(com_port):
	"""
	Validates if the COM port number is a valid integer.
	
	param: com_port = COM port number as a string.
	raise: ValueError if the COM port number is not a valid integer.
	"""

	if not com_port.isdigit():
		raise ValueError(f"Invalid COM PORT number: {com_port}. It must be a valid integer.")

def process_ttl_file(base_file_path=r'C:\SystemDebug\TTL', experiment_number =1, new_com_port = 8, new_runregression_line = 'runregression %MM%', new_dbmvvars_string= 'dbmvvars.nsh', slice = False, vvarnsh = 'apic_cdie0'):
	"""
	Processes a TTL file to update specific lines based on parameters.
	
	param: base_file_path = Base path where TTL files are located.
	param: experiment_number = Number to identify the experiment.
	param: new_com_port = New COM port number to be set.
	param: new_runregression_line = New runregression line to be set.
	param: new_dbmvvars_string = New dbmvvars string to be set.
	param: slice = Boolean indicating whether to process slice-specific lines.
	param: vvarnsh = Variable name for slice-specific processing.
	return: Path to the processed TTL file.
	"""

	if new_com_port != None: validate_com_port(new_com_port)
	
	if slice:
		cmdsfile = 'Commands_slice.ttl'
		dbmstring = 'dbmvvars'
	else:
		cmdsfile = 'Commands.ttl'
		dbmstring = 'slicevars'
	expfile = f"Experiment{experiment_number}.ttl"

	base_cmd_file =  os.path.join(base_file_path, cmdsfile)
	output_file_path = os.path.join(base_file_path, expfile)
	
	try:
		with open(base_cmd_file, 'r') as base_file:
			lines = base_file.readlines()

		line_found = {
			"com_port": False,
			"run_regression": False,
			"dbmvvars": False
		}

		with open(output_file_path, 'w') as output_file:
			for line in lines:
				if line.startswith("connect '/C=") and "/BAUD=" in line:
					parts = line.split('/C=')
					parts[1] = new_com_port + '/' + parts[1].split('/', 1)[1]
					line = '/C='.join(parts)
					line_found["com_port"] = True

				if line.startswith("sendln 'runregression"):
					line = f"sendln '{new_runregression_line}" + '\n'
					line_found["run_regression"] = True

				if f"{dbmstring}.nsh" in line:
					line = line.replace(f"{dbmstring}.nsh", new_dbmvvars_string)
					line_found["dbmvvars"] = True
				
			   
				if slice:
					if line.startswith("sendln 'apic_cdie"):
						line = f"sendln '{vvarnsh}" + '\n'
						#output_file.write(vvaroverride)
					

				output_file.write(line)
		
		for key, value in line_found.items():
			if not value:
				raise RuntimeError(f"Error: Specified line for {key} not found in the base file.")

	except FileNotFoundError:
		sys.exit(f"Error: Base file '{base_file_path}' not found.")
	except Exception as e:
		sys.exit(f"Error: {str(e)}")

	return output_file_path


if __name__ == "__main__":
	#path = r'Q:\DPM_Debug\GNR\Logs\IDI\74TQ507400300\RVP\Loops\Shmoo_Core_V_vs_F_25DegC_AVX3_Slice84\17_CORE Shmoo Hi_IA__84__ia_f36__cfc_f22__vcfg_fixed__ia_v0_95.log'

	path = r'Q:\DPM_Debug\GNR\Logs\IDI\74NM737000278\RVP\Loops\1_Shmoo_slice_156_F4_F5_F7'

	#extract_fail_seed(path)

	seeds = loops_fails(path)

	for k,v in seeds.items():
		print(f'{k} : {v}')
### Not used
#if __name__ == "__main__":
#    if len(sys.argv) != 6:
#        sys.exit("Usage: python script.py <base_file_path> <experiment_number> <new_com_port> <new_runregression_line> <new_dbmvvars_string>")
#    
#    base_file_path = sys.argv[1]
#    experiment_number = sys.argv[2]
#    new_com_port = sys.argv[3]
#    new_runregression_line = sys.argv[4]
#    new_dbmvvars_string = sys.argv[5]
#
#    process_ttl_file(base_file_path, experiment_number, new_com_port, new_runregression_line, new_dbmvvars_string)