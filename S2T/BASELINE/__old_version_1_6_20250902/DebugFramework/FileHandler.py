import sys
import os
import io
import re
from datetime import datetime
import shutil
import pandas as pd
import openpyxl
import logging
import socket
import zipfile
import json
import configparser
from pathlib import Path
from colorama import Fore, Style, Back
import importlib


sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
	#from ..DebugFramework.Storage_Handler import DBHandler as db
	#from ..DebugFramework.Storage_Handler import DBUserInterface as dbui
	import Storage_Handler.DBHandler as db
	import Storage_Handler.DBUserInterface as dbui
	importlib.reload(db)
	DATABASE_HANDLER_READY = True
except Exception as e:
	print(f' Unable to import Database Handler with Exception: {e}')
	DATABASE_HANDLER_READY = False


#from PPV import MCAparser as parser
#from PPV import PPVReportMerger as merger
import PPV.MCAparser as parser
import PPV.PPVReportMerger as merger

importlib.reload(parser)
importlib.reload(merger)


ORIGINAL_STDIN = sys.stdin
ORIGINAL_STDOUT = sys.stdout
ORIGINAL_STDERR = sys.stderr

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

	def __init__(self, log_file='app.log', logger_name = 'FrameworkLogger', console_output=False, pythonconsole = False, reset_handlers=True):
		self.log_file = log_file
		self.console_output = console_output
		self.pythonconsole = pythonconsole
		self.logger = logging.getLogger(logger_name)
		self.logger.setLevel(logging.DEBUG)
		# Reset handlers if reset_handlers is True
		if reset_handlers:
			self.reset_all_handlers()	

		# Define log format
		# Python Console Logs Format
		
		self.pysvfomatter = logging.Formatter('%(message)s')
		
		# Framework Format
		self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

		# Create file handler
		file_handler = logging.FileHandler(self.log_file, mode='w')
		file_handler.setLevel(logging.DEBUG)
		file_handler.setFormatter(self.formatter)
		self.logger.addHandler(file_handler)
	
		# Create console handler
		if self.console_output:
			console_handler = logging.StreamHandler()
			console_handler.setLevel(logging.DEBUG)

		#	# Add console handler to logger if not already added
		#	if not any(isinstance(handler, logging.StreamHandler) for handler in self.logger.handlers):
			self.logger.addHandler(console_handler)

		self.original_stdin = ORIGINAL_STDIN
		self.original_stdout = ORIGINAL_STDOUT
		self.original_stderr = ORIGINAL_STDERR
		self.capture_active = False
	
	def reset_all_handlers(self):
		self.logger.handlers = []

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

	def start_capture(self, file_mode='w'):
		if self.pythonconsole and not self.capture_active:
			# Create file handler with specified mode
			self.reset_all_handlers()
			file_handler = logging.FileHandler(self.log_file, mode=file_mode)
			file_handler.setLevel(logging.DEBUG)
			file_handler.setFormatter(self.pysvfomatter)
			self.logger.addHandler(file_handler)

			# Redirect stdout and stderr to custom TeeStream
			sys.stdin = self._create_tee_stream(self.original_stdin, logging.DEBUG)
			sys.stdout = self._create_tee_stream(self.original_stdout, logging.INFO)
			sys.stderr = self._create_tee_stream(self.original_stderr, logging.ERROR)

			sys.settrace(self._trace_calls)
			self.capture_active = True

	def stop_capture(self):
		if self.pythonconsole:
			# Restore original stdout and stderr
			sys.stdin = self.original_stdin
			sys.stdout = self.original_stdout
			sys.stderr = self.original_stderr

			sys.settrace(None)
			self.capture_active = False

	def _create_tee_stream(self, stream, level):
		class TeeStream(io.StringIO):
			def __init__(self, stream, logger, level):
				super().__init__()
				self.stream = stream
				self.logger = logger
				self.level = level

			def write(self, message):
				self.stream.write(message)
				self.logger.log(self.level, message.strip())

			def readline(self):
				input_line = self.stream.readline()
				self.logger.log(self.level, f"Input: {input_line.strip()}")
				return input_line

			def flush(self):
				self.stream.flush()

		return TeeStream(stream, self.logger, level)

	def _trace_calls(self, frame, event, arg):
		if event == 'call':
			code = frame.f_code
			if code.co_name == '<module>':
				self.logger.log(logging.INFO, f"Input: {code.co_filename}:{frame.f_lineno} - {code.co_name}")
		return self._trace_calls


#####################################################################################
##
##              Database and files Upload
##
#####################################################################################

class TestUpload:

	def __init__(self, folder, vid, name, bucket, WW, product, logger = None, from_Framework = False, upload_to_disk=True, upload_to_danta=True):
		self.folder = folder
		self.vid = vid
		self.name = name
		self.bucket = bucket
		self.print = logger
		self.temporal = r'C:\Temp'
		self.TemporalFolder = f'ManualTest_{name}' ## This is an option to manually upload data when using the dpmlogger
		self.upload_to_danta = upload_to_danta
		self.upload_to_disk = upload_to_disk
		self.from_Framework = from_Framework
		self.WW = WW
		self.product = product

	def generate_temporal(self):
		folder = f'ManualTest_{self.name}'
		# Creates a temporal folder to store the data
		self.TemporalFolder = create_path(self.temporal, folder)
		create_folder_if_not_exists(self.TemporalFolder)
		
	def remove_temporal(self):

		remove_folder_if_exists(self.TemporalFolder)

	def copy_to_temporal(self, files):
		
		dest = self.TemporalFolder

		# Provide full filename
		for file in files:
			copy_single_file(file, dest)

	def copy_to_log_to_temporal(self, file):
		
		destination_dir = self.TemporalFolder
		# Get the file name and extension
		file_name, file_extension = os.path.splitext(file)

		# Determine the new file name
		if file_extension.lower() != '.log':
			new_file_name = file_name + '.log'
		else:
			new_file_name = os.path.basename(file)
			
		# Define the full path for the new file
		destination_file = os.path.join(destination_dir, new_file_name)

		# Copy the file to the destination
		shutil.copy(file, destination_file)	

	def generate_summary(self):
		
		#visual = self.vid
		#name = self.name
		#bucket = self.bucket
		tfolder = self.folder if self.from_Framework else self.TemporalFolder
		self.manual_summary(visual=self.vid, bucket=self.bucket, name=self.name, WW=self.WW, product=self.product, tfolder=tfolder, logger = self.print)
		#SummaryName = f'Summary_{self.vid}_{self.name}'
		#SummaryFile = create_path(tfolder, f'{SummaryName}.xlsx')

		#self.print('Generating Summary files --- \n')

		#merge_mca_files(input_folder=tfolder, output_file=SummaryFile)
		#decode_mcas(name=SummaryName, week=self.WW, source_file=SummaryFile, label=self.bucket, path=tfolder, product = self.product)

	def upload_data(self):

		tfolder = self.folder if self.from_Framework else self.TemporalFolder

		self.manual_upload(tfolder = tfolder, visual = self.vid, Product = self.product, UPLOAD_TO_DISK = self.upload_to_disk, UPLOAD_DATA = self.upload_to_danta, logger = self.print )

	# This function will move the console print to a logger to save required data into a file
	def initlog(self):
		
		self.log_file = os.path.join(self.TemporalFolder, 'DebugFrameworkLogger.log')
		self.print = FrameworkLogger(self.log_file, 'FrameworkLogger', console_output=True)

	def TestBanner(self, qdf, tnum, mask, corelic, bumps, htdis, dis2CPM, freqIA, voltIA, freqCFC, voltCFC, content, passstring, failstring):

		self.print(f' -- Test Start --- ')
		self.print(f' -- Debug Framework {self.name} --- ')
		self.print(f' -- Performing test iteration {tnum} with the following parameters: ')

		## Get Running Content -- Not used
		#self.running_content()

		## Print Test Summary keys --- 
		
		EMPTY_FIELDS = [None, 'None', '']
		u600w = ['RVF5']
		self.print(f'\t > Unit VisualID: {self.vid}')
		self.print(f'\t > Unit QDF: {qdf}')
		self.print(f'\t > Configuration: {mask if mask not in EMPTY_FIELDS else "System Mask"} ')
		if corelic: self.print(f'\t > Core License: {corelic} ')
		self.print(f'\t > Voltage set to: {bumps} ')
		self.print(f'\t > HT Disabled (BigCore): {htdis} ')
		self.print(f'\t > Dis 2 Cores (Atomcore): {dis2CPM} ')
		self.print(f'\t > Core Freq: {freqIA} ')
		self.print(f'\t > Core Voltage: {voltIA} ')
		self.print(f'\t > Mesh Freq: {freqCFC} ')
		self.print(f'\t > Mesh Voltage: {voltCFC} ')
		self.print(f'\t > Running Content: {content} ')
		self.print(f'\t > Pass String: {passstring} ')
		self.print(f'\t > Fail String: {failstring} ')

		if qdf in u600w: self.print(f'\t > Unit 600w Fuses Applied ')
		#if self.extMask != None:
		#	printmasks = [["Type", "Value"]]
		#	printmasks.append([[k,v] for k, v in self.extMask.items()])
		#	self.print(f'\t > Using External Base Mask: {printmasks} \n')
		#	self.print(tabulate(printmasks, headers="firstrow", tablefmt="grid"))	

	def Iteration_end(self, tnum, runName, runStatus, scratchpad, seed):

		self.print(f'tdata_{tnum}::{runName}::{runStatus}::{scratchpad}::{seed}')
		self.print(f' -- Test End --- ')

	@staticmethod
	def manual_upload(tfolder, visual, Product, UPLOAD_TO_DISK = True, UPLOAD_DATA = True, logger = None, ):
		"""Allows the manual update of data into Framework NAS and Danta DB, based on a folder location.

		Args:
			tfolder (str, optional): Test Folder. Defaults to None.
			visual (str, optional): Visual ID of the Unit. Defaults to None.
			Product (str, optional): Product Name. Defaults to None.
			UPLOAD_TO_DISK (bool, optional): Enables Copy of data to Framework NAS. Defaults to None.
			UPLOAD_DATA (bool, optional): Enables Data upload to Danta DB. Defaults to True.
			logger (func, optional): Function to be called for console printing / logging. Defaults to None.
		"""
		logger = print if logger == None else logger

		## Debug Framework Disk
		DATA_SERVER = r'\\crcv03a-cifs.cr.intel.com\mfg_tlo_001'
		DATA_DESTINATION = rf'{DATA_SERVER}\DebugFramework\{Product}'

		if UPLOAD_TO_DISK: 
			logger('Copying Data to Framework disk --- \n')
			dest_folder=copy_folder(src=tfolder, dest=DATA_DESTINATION, visual=visual, zipdata=True , logger = logger)
		
		if DATABASE_HANDLER_READY and UPLOAD_DATA:
			try:
				logger('Uploading Data to Danta Server --- \n')
				db.upload_summary_report(storage_dir=dest_folder)
			except Exception as e:
				logger(f' Failed updloading data to DantaDB -- Exception {e}',2)

	@staticmethod
	def manual_summary(visual, bucket, name, WW, product, tfolder, logger = None):

		logger = print if logger == None else logger

		SummaryName = f'Summary_{visual}_{name}'
		SummaryFile = create_path(tfolder, f'{SummaryName}.xlsx')

		logger('Generating Summary files --- \n')

		merge_mca_files(input_folder=tfolder, output_file=SummaryFile)
		decode_mcas(name=SummaryName, week=WW, source_file=SummaryFile, label=bucket, path=tfolder, product = product)

	@staticmethod
	def search_exp_name(tfolder, logname = 'DebugFrameworkLogger.log'):
		file = create_path(tfolder, logname)
		return find_name_regex(file, pattern=r"-- Debug Framework (\w+) ---")

def find_name_regex(file_path, pattern=r"-- Debug Framework (\w+) ---"):
	"""
	Searches for a line using regex pattern and extracts the core name.
	
	Args:
		file_path (str): Path to the file to search
		pattern (str): Regex pattern to match (default captures word between the fixed parts)
	
	Returns:
		str: The extracted core name or None if not found
	"""
	try:
		with open(file_path, 'r', encoding='utf-8') as file:
			for line in file:
				match = re.search(pattern, line.strip())
				if match:
					return match.group(1)  # Return the first captured group
					
	except FileNotFoundError:
		print(f"Error: File '{file_path}' not found.")
		return None
	except Exception as e:
		print(f"Error reading file: {e}")
		return None
	
	return None

def manual_upload():
	dbui.main(datahandler=TestUpload)

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

def remove_folder_if_exists(folder_path):
	"""
	Removes the specified folder if it exists.

	Parameters:
	folder_path (str): The path to the folder to be removed.
	"""
	if os.path.exists(folder_path) and os.path.isdir(folder_path):
		shutil.rmtree(folder_path)
		print(f"Folder '{folder_path}' has been removed.")
	else:
		print(f"Folder '{folder_path}' does not exist.")

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
					copy_single_file(full_file_name, dest)
					print(f'Copied {filename} to {dest}')
				else:
					print(f'Skipping file replace {dest}')

def copy_single_file(full_file_name, dest):
	shutil.copy(full_file_name, dest)	

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

def teraterm_check(com_port, ip_address='192.168.0.2', teraterm_path = r"C:\teraterm", seteo_h_path = r"C:\SETEO_H", ini_file = "TERATERM.INI", useparser=False, checkenv=True):
	
	def use_configparser():
		
		for k, v in init_check_variables.items():
			print(f'Checking Teraterm Configuration :: {k} :: {config["Tera Term"][k]} --> {v}')
			if config['Tera Term'][k] != v:
				print(f'Updating Teraterm Configuration :: {k} :: {config["Tera Term"][k]} --> {v}')
				config['Tera Term'][k]= v

		# Write the updated content back to the TERATERM.INI file
		with open(ini_file_path, 'w') as configfile:
			config.write(configfile)

	def use_lineread():
			
		# Read the TERATERM.INI file
		with open(ini_file_path, 'r') as file:
			lines = file.readlines()

		# Update the configuration settings
		with open(ini_file_path, 'w') as file:
			for line in lines:
				gotonext = False
				for k, v in init_check_variables.items():
					if line.startswith(f'{k}='):
						file.write(f'{k}={v}\n')
						oldv = line.split("=")[1].split("\n")[0]
						print(f'Checking Teraterm Configuration :: {k} :: {oldv} --> {v}')
						gotonext = True
				if gotonext:
					continue
				else:
					file.write(line)

	ini_file_path = os.path.join(teraterm_path, ini_file)

	# Check if TERATERM.INI exists in C:\teraterm
	if not os.path.exists(ini_file_path):
		# Copy the entire teraterm folder from C:\SETEO_O to C:\
		source_folder = os.path.join(seteo_h_path, "teraterm")
		print(f"Searching for a copy of teraterm at folder: {seteo_h_path} :: {source_folder}")
		if os.path.exists(source_folder):
			shutil.copytree(source_folder, teraterm_path)
			print("teraterm folder copied from C:\\SETEO_H to C:\\.")
		else:
			#print("")
			raise ValueError ("teraterm folder not found in C:\\SETEO_H.")

	# Read the TERATERM.INI file
	config = configparser.ConfigParser()
	config.read(ini_file_path)

	# Update the configuration settings
	init_check_variables = {
							'ComPort':str(com_port),
							'BaudRate':'115200', 
							'Parity':'none', 
							'DataBit':'8', 
							'StopBit':'1', 
							'FlowCtrl':'none', 
							'DelayPerChar':'100', 
							'DelayPerLine':'100', 
							}
	# Pass and User set to None as we only check variable exists not eh value itself
	host_variables = { 'FrameworkSerial': f'{com_port}',
							'FrameworkIPAdress':f'{ip_address}',
							'FrameworkDefaultPass':None,
							'FrameworkDefaultUser':None,}

	# Parse will modify the file comments, not using it for now
	if useparser:
		use_configparser()
	else:
		use_lineread()

	print("TERATERM.INI updated successfully.")
	if checkenv:
		print('Checking ENV Variables for COM and IP Configuration')
		check_env_variables(host_variables)

def ini_to_dict_with_types(file_path, convert_section_underscores=False, convert_key_underscores=False):
	"""
	Reads an INI file and returns it as a nested dictionary with automatic type conversion.
	Attempts to convert values to int, float, or boolean when possible.
	
	Args:
		file_path (str): Path to the .ini file
		convert_section_underscores (bool): If True, converts underscores to spaces in section names
		convert_key_underscores (bool): If True, converts underscores to spaces in key names
		
	Returns:
		dict: Dictionary with sections as keys and their key-value pairs as nested dictionaries.
			  Values are automatically converted to appropriate Python types.
			  
	Raises:
		FileNotFoundError: If the file doesn't exist
		configparser.Error: If there's an error parsing the INI file
	"""
	if not Path(file_path).exists():
		raise FileNotFoundError(f"File not found: {file_path}")
	
	config = configparser.ConfigParser()
	config.read(file_path)

	def convert_name(name, do_convert):
		"""Convert underscores to spaces if do_convert is True."""
		return name.replace('_', ' ') if do_convert else name

	def convert_value(value):
		"""Convert string values to bool, int, float, or keep as string."""
		if value.lower() in ('true', 'yes', '1', 'on'):
			return True
		elif value.lower() in ('false', 'no', '0', 'off'):
			return False
		try:
			return int(value)
		except ValueError:
			pass
		try:
			return float(value)
		except ValueError:
			pass
		return value
	
	result = {}
	for section_name in config.sections():
		converted_section_name = convert_name(section_name, convert_section_underscores)
		result[converted_section_name] = {
			convert_name(key, convert_key_underscores): convert_value(value) 
			for key, value in config[section_name].items()
		}
	
	return result

def check_env_variables(variables):
	for var_name, desired_value in variables.items():
		current_value = os.getenv(var_name, None)
		
		if current_value is None:
			# Environment variable does not exist, create it
			#os.environ[var_name] = desired_value
			#print(f"Created environment variable '{var_name}' with value '{desired_value}'.")
			raise ValueError(f'System is not properly set env variable {var_name} is not configured...')
		
		elif current_value != desired_value and not (var_name == 'FrameworkDefaultPass' or var_name == 'FrameworkDefaultUser'):
			# Environment variable exists but has a different value, update it
			os.environ[var_name] = desired_value
			#raise ValueError(f'Differences found in System configuration "{var_name}" value: System {current_value} -- Experiment {desired_value}  -- Check!')
			print(f"Changing variable '{var_name}' -- System:'{current_value}' -- Experiment:'{desired_value}'.")
		else:
			# Environment variable exists and has the correct value
			print(f"System is Properly set for the experiment -- Environment variable '{var_name}' already exists with the correct value '{current_value}'.")

def load_json(filepath):
	with open(filepath,"r") as f:
		return json.load(f)

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

	try:
		os.makedirs(dest_path, exist_ok=True)
	except Exception as e:
		logger(f"Error creating dir at location {dest_path}: {e}")
		return dest_path

	if zipdata:
		# Create zipfile with source folder name
		#dest_path = os.path.join(dest, hostname.lower(), current_date, visual)

		zip_file_name = f'ExperimentData.zip'
		zip_file_path = os.path.join(dest_path, zip_file_name)
		

		zip_folder_contents(zip_file_path, dest_path)
		logger(f'Data operation Succesfull !!! --> Check file: {zip_file_path}')
	else:
		# Create destination path with hostname and current date (includes source folder name)
		#dest_path = os.path.join(dest, hostname.lower(), current_date, visual, src_folder_name)
		#os.makedirs(dest_path, exist_ok=True)

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

class FrameworkConfigConverter:
	def __init__(self, ini_file_path="framework_config.ini", logger=None):
		"""
		Initialize the converter with INI file path
		
		Args:
			ini_file_path (str): Path to the INI configuration file
		"""
		self.print = print if logger == None else logger
		self.ini_file_path = ini_file_path
		self.config = None
		self.csv_filename = "flow_params.csv"
		self._values = None
		self._cached_config_data = {}  # Cache for config data
	
	def get_values(self):
		return self._values
	
	def update_values(self, values):
		self._values = values

	def read_ini(self):
		"""Read and parse the INI configuration file"""
		try:
			if not os.path.exists(self.ini_file_path):
				self.print(f"INI file not found, check if yout TTL configuration is 1.0: {self.ini_file_path}",1)
				return False
			
			self.config = configparser.ConfigParser()
			self.config.read(self.ini_file_path)
			self.print(f"INI file loaded successfully: {self.ini_file_path}",1)
			# Clear cache when config is reloaded
			self._cached_config_data = {}
			return True
			
		except Exception as e:
			self.print(f"Error reading INI file: {e}",2)
			return False

	# ========== FLOW DEFINITIONS - SINGLE SOURCE OF TRUTH ==========
	
	def _get_linux_flow_definition(self):
		"""Define Linux flow configuration structure"""
		return [
			# (field_name, section, key, default_value)
			("STARTUP_LINUX", "LINUX_INIT", "STARTUP_LINUX", "startup_linux.nsh"),
			("WAIT_STRING1", "LINUX_INIT", "WAIT_STRING1", "Press any key to continue..."),
			("WAIT_STRING2", "LINUX_INIT", "WAIT_STRING2", "GRUB version"),
			("WAIT_STRING3", "LINUX_INIT", "WAIT_STRING3", "Loading Linux"),
			("WAIT_STRING4", "LINUX_INIT", "WAIT_STRING4", "--MORE--"),
			("LINUX_PATH", "LINUX_CONTENT", "LINUX_PATH", "cd /root/content/LOS/TSL/bin"),
			("LINUX_CONTENT_WAIT", "LINUX_CONTENT", "LINUX_CONTENT_WAIT", "20"),
			("LINUX_PASS_STRING", "LINUX_CONTENT", "LINUX_PASS_STRING", "Test Completed"),
			("LINUX_FAIL_STRING", "LINUX_CONTENT", "LINUX_FAIL_STRING", "Test_Failed"),
			("LINUX_CONTENT_LINE_0", "LINUX_CONTENT", "LINUX_CONTENT_LINE_0", ""),
			("LINUX_CONTENT_LINE_1", "LINUX_CONTENT", "LINUX_CONTENT_LINE_1", ""),
			("LINUX_CONTENT_LINE_2", "LINUX_CONTENT", "LINUX_CONTENT_LINE_2", ""),
			("LINUX_CONTENT_LINE_3", "LINUX_CONTENT", "LINUX_CONTENT_LINE_3", ""),
			("LINUX_CONTENT_LINE_4", "LINUX_CONTENT", "LINUX_CONTENT_LINE_4", ""),
			("LINUX_CONTENT_LINE_5", "LINUX_CONTENT", "LINUX_CONTENT_LINE_5", ""),
			("LINUX_CONTENT_LINE_6", "LINUX_CONTENT", "LINUX_CONTENT_LINE_6", ""),
			("LINUX_CONTENT_LINE_7", "LINUX_CONTENT", "LINUX_CONTENT_LINE_7", ""),
			("LINUX_CONTENT_LINE_8", "LINUX_CONTENT", "LINUX_CONTENT_LINE_8", ""),
			("LINUX_CONTENT_LINE_9", "LINUX_CONTENT", "LINUX_CONTENT_LINE_9", ""),
			("LNX_PRE_EXEC_CMD", "LINUX_CMDS", "LNX_PRE_EXEC_CMD", ""),
			("LNX_POST_EXEC_CMD", "LINUX_CMDS", "LNX_POST_EXEC_CMD", ""),
			("COMMAND_TIMEOUT", "EXECUTION_CONTROL", "command_timeout", "30")
		]
	
	def _get_slice_flow_definition(self):
		"""Define Slice flow configuration structure"""
		return [
			("STARTUP_EFI", "DRG_INIT", "STARTUP_EFI", "startup_efi.nsh"),
			("ULX_PATH", "DRG_INIT", "ULX_PATH", "FS1:\\EFI\\ulx"),
			("ULX_CPU", "DRG_INIT", "ULX_CPU", "GNR_B0"),
			("PRODUCT_CHOP", "DRG_INIT", "PRODUCT_CHOP", "GNR"),
			("VVAR0", "VVAR_SETUP", "VVAR0", "0x4C4B40"),
			("VVAR1", "VVAR_SETUP", "VVAR1", "80064000"),
			("VVAR2", "VVAR_SETUP", "VVAR2", "0x1000000"),
			("VVAR3", "VVAR_SETUP", "VVAR3", "0x10000"),
			("VVAR_EXTRA", "VVAR_SETUP", "VVAR_EXTRA", " "),
			("SLICE_CONTENT", "SETUP_SLICE", "CONTENT", "FS1:\\content\\Dragon\\GNR1C_Q_Slice_2M_pseudoSBFT_System"),
			("APIC_CDIE", "SETUP_SLICE", "APIC_CDIE", "0"),
			("DRAGON_CONTENT_LINE", "DRAGON_CONTENT", "DRAGON_CONTENT_LINE", "Ditto Blender Yakko"),
			("MERLIN", "MERLIN_SETUP", "MERLIN", "MerlinX"),
			("MERLIN_DRIVE", "MERLIN_SETUP", "MERLIN_DRIVE", "FS1:"),
			("MERLIN_DIR", "MERLIN_SETUP", "MERLIN_DIR", "FS1:\\EFI\\Version8.15\\BinFiles\\Release"),
			("STOP_ON_FAIL", "SETUP_REGRESSION", "STOP_ON_FAIL", "0"),
			("EFI_PRE_EXEC_CMD", "EFI_CMDS", "EFI_PRE_EXEC_CMD", ""),
			("EFI_POST_EXEC_CMD", "EFI_CMDS", "EFI_POST_EXEC_CMD", ""),
			("COMMAND_TIMEOUT", "EXECUTION_CONTROL", "command_timeout", "30")
		]
	
	def _get_mesh_flow_definition(self):
		"""Define Mesh flow configuration structure"""
		return [
			("STARTUP_EFI", "DRG_INIT", "STARTUP_EFI", "startup_efi.nsh"),
			("ULX_PATH", "DRG_INIT", "ULX_PATH", "FS1:\\EFI\\ulx"),
			("ULX_CPU", "DRG_INIT", "ULX_CPU", "GNR_B0"),
			("PRODUCT_CHOP", "DRG_INIT", "PRODUCT_CHOP", "GNR"),
			("VVAR0", "VVAR_SETUP", "VVAR0", "0x4C4B40"),
			("VVAR1", "VVAR_SETUP", "VVAR1", "80064000"),
			("VVAR2", "VVAR_SETUP", "VVAR2", "0x1000000"),
			("VVAR3", "VVAR_SETUP", "VVAR3", "0x10000"),
			("VVAR_EXTRA", "VVAR_SETUP", "VVAR_EXTRA", " "),
			("MESH_CONTENT", "SETUP_MESH", "MESH_CONTENT", "FS1:\\content\\Dragon\\7410_0x0E_PPV_MegaMem\\GNR128C_H_1UP\\"),
			("DRAGON_CONTENT_LINE", "DRAGON_CONTENT", "DRAGON_CONTENT_LINE", "Ditto Blender Yakko"),
			("MERLIN", "MERLIN_SETUP", "MERLIN", "MerlinX"),
			("MERLIN_DRIVE", "MERLIN_SETUP", "MERLIN_DRIVE", "FS1:"),
			("MERLIN_DIR", "MERLIN_SETUP", "MERLIN_DIR", "FS1:\\EFI\\Version8.15\\BinFiles\\Release"),
			("STOP_ON_FAIL", "SETUP_REGRESSION", "STOP_ON_FAIL", "0"),
			("EFI_PRE_EXEC_CMD", "EFI_CMDS", "EFI_PRE_EXEC_CMD", ""),
			("EFI_POST_EXEC_CMD", "EFI_CMDS", "EFI_POST_EXEC_CMD", ""),
			("COMMAND_TIMEOUT", "EXECUTION_CONTROL", "command_timeout", "30")
		]
	
	def _get_custom_flow_definition(self):
		"""Define Custom flow configuration structure"""
		return [
			("CUSTOM_PATH", "CUSTOM", "CUSTOM_PATH", "FS1:\\CUSTOM"),
			("CMD_LINE_0", "CUSTOM", "CMD_LINE_0", "custom.nsh"),
			("EFI_PRE_EXEC_CMD", "EFI_CMDS", "EFI_PRE_EXEC_CMD", ""),
			("EFI_POST_EXEC_CMD", "EFI_CMDS", "EFI_POST_EXEC_CMD", ""),
			("COMMAND_TIMEOUT", "EXECUTION_CONTROL", "command_timeout", "30")
		]

	# ========== CORE METHOD - SINGLE SOURCE OF TRUTH ==========
	
	def get_flow_config_data(self, flow_type=None, include_empty=True, use_cache=True):
		"""
		Get flow configuration data as a dictionary - THE MAIN METHOD
		
		Args:
			flow_type (str): Flow type - 'LINUX', 'SLICE', 'MESH', or 'CUSTOM'. 
							If None, uses current flow type from config
			include_empty (bool): Whether to include empty values in the result
			use_cache (bool): Whether to use cached data if available
							
		Returns:
			dict: Configuration data with parameter names as keys and values as values
				  Returns None if error occurs
		"""
		# Determine flow type
		if flow_type is None:
			flow_type = self.get_current_flow_type()
		
		flow_type = flow_type.upper() if flow_type else None
		
		# Check cache first
		cache_key = f"{flow_type}_{include_empty}"
		#self.print(f'Configured:{cache_key}' )
		if use_cache and cache_key in self._cached_config_data:
			#self.print(f'Returning:{cache_key}')
			return self._cached_config_data[cache_key]
		
		# Flow type mapping
		flow_definitions = {
			'LINUX': self._get_linux_flow_definition,
			'SLICE': self._get_slice_flow_definition,
			'MESH': self._get_mesh_flow_definition,
			'CUSTOM': self._get_custom_flow_definition
		}
		
		if flow_type not in flow_definitions:
			self.print(f"Error: Unknown or missing flow type '{flow_type}'", 2)
			return None
		
		if self.config is None:
			self.print("Error: Configuration not loaded. Call read_ini() first.", 2)
			return None
		
		# Get flow definition and extract values
		definition = flow_definitions[flow_type]()
		config_dict = {}
		
		try:
			for field_name, section, key, default_value in definition:
				if section in self.config:
					value = self.config[section].get(key, default_value)
				else:
					value = default_value
				
				# Include based on include_empty flag
				if include_empty or value:
					config_dict[field_name] = value
			
			# Cache the result
			self._cached_config_data[cache_key] = config_dict
			return config_dict
			
		except Exception as e:
			self.print(f"Error extracting {flow_type} flow configuration: {e}", 2)
			return None

	# ========== LEGACY METHODS (NOW USE get_flow_config_data) ==========
	
	def get_linux_flow_values(self):
		"""Extract Linux flow configuration values - LEGACY METHOD"""
		config_data = self.get_flow_config_data('LINUX', include_empty=True)
		if config_data is None:
			self.update_values(values=None)
			return None
		
		values = list(config_data.values())
		self.update_values(values=values)
		return values
	
	def get_slice_flow_values(self):
		"""Extract Slice flow configuration values - LEGACY METHOD"""
		config_data = self.get_flow_config_data('SLICE', include_empty=True)
		if config_data is None:
			self.update_values(values=None)
			return None
		
		values = list(config_data.values())
		self.update_values(values=values)
		return values
	
	def get_mesh_flow_values(self):
		"""Extract Mesh flow configuration values - LEGACY METHOD"""
		config_data = self.get_flow_config_data('MESH', include_empty=True)
		if config_data is None:
			self.update_values(values=None)
			return None
		
		values = list(config_data.values())
		self.update_values(values=values)
		return values
	
	def get_custom_flow_values(self):
		"""Extract Custom flow configuration values - LEGACY METHOD"""
		config_data = self.get_flow_config_data('CUSTOM', include_empty=True)
		if config_data is None:
			self.update_values(values=None)
			return None
		
		values = list(config_data.values())
		self.update_values(values=values)
		return values

	# ========== CSV CREATION ==========
	
	def create_flow_csv(self, flow_type, ttl_folder_path):
		"""
		Create CSV file for specified flow type using config data as source
		
		Args:
			flow_type (str): Flow type - 'LINUX', 'SLICE', 'MESH', or 'CUSTOM'
			ttl_folder_path (str): Path to folder where CSV will be created
			
		Returns:
			str: Path to created CSV file, or None if failed
		"""
		try:
					   
			Path(ttl_folder_path).mkdir(parents=True, exist_ok=True)
			
			# Get config data (include empty values for CSV to maintain order)
			config_data = self.get_flow_config_data(flow_type, include_empty=True)
			
			if config_data is None:
				return None
			
			# Define filename
			flow_type_lower = flow_type.lower()
			csv_filename = f"{flow_type_lower}_flow_params.csv"
			csv_file_path = os.path.join(ttl_folder_path, csv_filename)
			
			# Create CSV file from config data values
			values = list(config_data.values())
			with open(csv_file_path, 'w') as f:
				f.write(','.join(values))
			
			self.print(f"{flow_type} flow CSV file created: {csv_file_path}", 1)
			return csv_file_path
			
		except Exception as e:
			self.print(f"Error creating {flow_type} flow CSV file: {e}", 2)
			return None
	
	def create_current_flow_csv(self, ttl_folder_path):
		"""Create CSV for the flow type specified in EXECUTION_CONTROL"""
		flow_type = self.get_current_flow_type()
		return self.create_flow_csv(flow_type, ttl_folder_path)
	
	def get_current_flow_type(self):
		"""Get the current flow type from EXECUTION_CONTROL section"""
		if self.config is None:
			return None
		
		if 'EXECUTION_CONTROL' in self.config:
			return self.config['EXECUTION_CONTROL'].get('flow_type', 'SLICE')
		
		return 'SLICE'  # Default

	# ========== UTILITY METHODS ==========
	
	def clear_cache(self):
		"""Clear the configuration data cache"""
		self._cached_config_data = {}
		self.print("Configuration cache cleared", 1)
	
	def get_available_flow_types(self):
		"""Get list of available flow types"""
		return ['LINUX', 'SLICE', 'MESH', 'CUSTOM']
	
	def validate_flow_type(self, flow_type):
		"""Validate if flow type is supported"""
		return flow_type.upper() in self.get_available_flow_types()

def create_default_framework_config(filename="framework_config.ini"):
	"""Create a default framework configuration INI file with all flows"""
	
	config = configparser.ConfigParser()
	
	# Linux Configuration Section
	config['LINUX_INIT'] = {
		'STARTUP_LINUX': 'startup_linux.nsh',
		'WAIT_STRING1': 'Press any key to continue...',
		'WAIT_STRING2': 'GRUB version',
		'WAIT_STRING3': 'Loading Linux',
		'WAIT_STRING4': '--MORE--'
	}
	
	config['LINUX_CONTENT'] = {
		'LINUX_PATH': 'cd /root/content/LOS/TSL/bin',
		'LINUX_CONTENT_WAIT': '20',
		'LINUX_PASS_STRING': 'Test Completed',
		'LINUX_FAIL_STRING': 'Test_Failed',
		'LINUX_CONTENT_LINE_0': '/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/Mlc_data_n3.xml --write_log_file_to_stdout=on --ituff=off',
		'LINUX_CONTENT_LINE_1': '/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/Mlc_data_n3.xml --write_log_file_to_stdout=on --ituff=off',
		'LINUX_CONTENT_LINE_2': '/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/Mlc_data_n3.xml --write_log_file_to_stdout=on --ituff=off',
		'LINUX_CONTENT_LINE_3': '/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/Mlc_data_n3.xml --write_log_file_to_stdout=on --ituff=off',
		'LINUX_CONTENT_LINE_4': '/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/Mlc_data_n3.xml --write_log_file_to_stdout=on --ituff=off',
		'LINUX_CONTENT_LINE_5': '',
		'LINUX_CONTENT_LINE_6': '',
		'LINUX_CONTENT_LINE_7': '',
		'LINUX_CONTENT_LINE_8': '',
		'LINUX_CONTENT_LINE_9': ''
	}
	
	# Dragon Configuration Section
	config['DRG_INIT'] = {
		'STARTUP_EFI': 'startup_efi.nsh',
		'ULX_PATH': r'FS1:\EFI\ulx',
		'ULX_CPU': 'GNR_B0',
		'PRODUCT_CHOP': 'GNR'
	}
	
	config['VVAR_SETUP'] = {
		'VVAR0': '0x4C4B40',
		'VVAR1': '80064000',
		'VVAR2': '0x1000000',
		'VVAR3': '0x10000',
		'VVAR_EXTRA': ' '
	}
	
	config['SETUP_SLICE'] = {
		'CONTENT': r'FS1:\content\Dragon\GNR1C_Q_Slice_2M_pseudoSBFT_System',
		'APIC_CDIE': '0'
	}
	
	config['SETUP_MESH'] = {
		'MESH_CONTENT': r'FS1:\content\Dragon\7410_0x0E_PPV_MegaMem\GNR128C_H_1UP\\'
	}
	
	config['DRAGON_CONTENT'] = {
		'DRAGON_CONTENT_LINE': 'Ditto Blender Yakko'
	}
	
	config['MERLIN_SETUP'] = {
		'MERLIN': 'MerlinX',
		'MERLIN_DRIVE': 'FS1:',
		'MERLIN_DIR': r'FS1:\EFI\Version8.15\BinFiles\Release'
	}
	
	config['SETUP_REGRESSION'] = {
		'STOP_ON_FAIL': '0'
	}
	
	config['CUSTOM'] = {
		'CUSTOM_PATH': r'FS1:\CUSTOM',
		'CMD_LINE_0': 'custom.nsh'
	}
	
	config['EFI_CMDS'] = {
		'EFI_PRE_EXEC_CMD': '',
		'EFI_POST_EXEC_CMD': ''
	}
	
	config['LINUX_CMDS'] = {
		'LNX_PRE_EXEC_CMD': '',
		'LNX_POST_EXEC_CMD': ''
	}
	
	config['EXECUTION_CONTROL'] = {
		'flow_type': 'SLICE',
		'command_timeout': '30'
	}
	
	# Write to file with comments
	with open(filename, 'w') as configfile:
		configfile.write("# Framework Configuration File\n")
		configfile.write("# This file contains all parameters for different test flows\n\n")
		config.write(configfile)
	
	print(f"Default framework configuration created: {filename}")
	return filename

if __name__ == "__main__":
	
	config_file = r'R:\Templates\GNR\version_2_0\TTL_Linux\config.ini'
	print("Creating default framework configuration files...")
	
	# Create the main default config
	#create_default_framework_config(config_file)
	
	# Initialize converter
	converter = FrameworkConfigConverter(config_file)
	flow_type = 'MESH'
	ttl_folder = r"R:\Templates\GNR\version_2_0\TTL_Linux"
	if converter.read_ini():

		
		# Create CSV for current flow type (from INI)
		converter.create_current_flow_csv(ttl_folder)
		
		# Or create specific flow CSVs
		#converter.create_flow_csv('LINUX', ttl_folder)
		#converter.create_flow_csv('SLICE', ttl_folder)
		#converter.create_flow_csv(flow_type, ttl_folder)
		#converter.create_flow_csv('CUSTOM', ttl_folder)

	
	#manual_upload()
	#path = r'Q:\DPM_Debug\GNR\Logs\IDI\74TQ507400300\RVP\Loops\Shmoo_Core_V_vs_F_25DegC_AVX3_Slice84\17_CORE Shmoo Hi_IA__84__ia_f36__cfc_f22__vcfg_fixed__ia_v0_95.log'

	#path = r'Q:\DPM_Debug\GNR\Logs\IDI\74NM737000278\RVP\Loops\1_Shmoo_slice_156_F4_F5_F7'

	#extract_fail_seed(path)

	#seeds = loops_fails(path)

	#for k,v in seeds.items():
	#	print(f'{k} : {v}')
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