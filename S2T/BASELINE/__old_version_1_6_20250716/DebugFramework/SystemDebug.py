import time
import os, sys
import ipccli
import namednodes
import pandas as pd
import time
import shutil
from tabulate import tabulate
from datetime import datetime
import pytz
from ipccli.stdiolog import log
from ipccli.stdiolog import nolog

import users.gaespino.dev.S2T.CoreManipulation as gcm
import users.gaespino.dev.S2T.dpmChecks as dpm
import users.gaespino.dev.S2T.SetTesterRegs as s2t

import users.gaespino.dev.DebugFramework.SerialConnection as ser
import users.gaespino.dev.DebugFramework.MaskEditor as gme
import users.gaespino.dev.DebugFramework.FileHandler as fh
import users.gaespino.dev.DebugFramework.UI.ControlPanel as fcp


import importlib

importlib.reload(ser)
importlib.reload(gme)
importlib.reload(fh)
importlib.reload(fcp)


## DB Connection library
try:
	import users.gaespino.dev.DebugFramework.Storage_Handler.DBHandler as db
	importlib.reload(db)
	DATABASE_HANDLER_READY = True
except Exception as e:
	print(f' Unable to import Database Handler with Exception: {e}')
	DATABASE_HANDLER_READY = False

## Folders
script_dir = os.path.dirname(os.path.abspath(__file__))
base_folder = 'C:\\SystemDebug'
ttl_source = os.path.join(script_dir, 'TTL')
shmoos_source = os.path.join(script_dir, 'Shmoos')
ttl_dest = os.path.join(base_folder, 'TTL')
shmoos_dest = os.path.join(base_folder, 'Shmoos')
logs_dest = os.path.join(base_folder, 'Logs')

# Run Tera Term macros
def macros_path(ttl_path):
	macrospath = rf'{ttl_path}'
	macro_cmds = {
		'Disconnect': rf'{macrospath}\disconnect.ttl',
		'Connect': rf'{macrospath}\connect.ttl',
		'StartCapture':  rf'{macrospath}\Boot.ttl',
		'StartTest': rf'{macrospath}\Commands.ttl',
		'StopCapture':  rf'{macrospath}\stop_capture.ttl'
	}
	return macro_cmds
# Default Macros Path
macro_cmds = macros_path(ttl_dest)

# Separator Lines

def print_separator_box(direction='down'):
	arrow = 'v' if direction == 'down' else '+'  # Box drawing arrows
	separator_line = f'{"-"*50}{arrow}{"-"*50}'
	return separator_line
	#print(separator_line)

def print_custom_separator(text):
	total_length = 101
	text_length = len(text)
	side_length = (total_length - text_length) // 2
	separator_line = f'{"*" * side_length} {text} {"*" * side_length}'
	
	# Adjust if the total length is not exactly 101 due to integer division
	if len(separator_line) < total_length:
		separator_line += '*'
	
	return separator_line

def initscript():
	# Create base folder if it does not exist
	fh.create_folder_if_not_exists(base_folder)

	# Create TTL and Shmoos folders if they do not exist
	ttlf = fh.create_folder_if_not_exists(ttl_dest)
	shmf = fh.create_folder_if_not_exists(shmoos_dest)
	logsf = fh.create_folder_if_not_exists(logs_dest)

	if not ttlf: replace_files(ttl=True, shmoo=False, replace = True)
	if not shmf: replace_files(ttl=False, shmoo=True, replace = True)

	print('Operation completed.')

def replace_files(ttl, shmoo, replace = False):
	if replace: user_input = "Y"
	else: ""
	# Copy files to TTL and Shmoos folders
	if ttl:fh.copy_files(ttl_source, ttl_dest, uinput=user_input)
	if shmoo:fh.copy_files(shmoos_source, shmoos_dest, uinput=user_input)

## Defeature tools Objects

class Experiment():
	def __init__(self,
			  	 name: str = 'Experiment',
				 tnumber: int = 1,
				 content: str = 'Dragon',
				 visual: str = '-9999999',
				 qdf: str = '',
				 bucket: str = 'UNCORE',
				 macro_cmds: dict = None,
				 coreslice: int = None,
				 fastboot: bool = True,
				 postcode_break: int = None,
				 target: str = 'mesh',
				 mask: str = None,
				 volt_type= 'vbump', 
				 volt_IA: float = None, 
				 volt_CFC: float = None,
				 freq_ia: int = None, 
				 freq_cfc: int = None, 
				 pseudo: bool = True,
				 dis2CPM: int = None, 
				 corelic: int = None, 
				 ttime: int =30,  
				 reset: bool = True, 
				 resetonpass: bool = False, 
				 extMask: dict = None, 
				 u600w: bool = False, 
				 summary: bool = True,
				 host: str = "10.250.0.2",
				 com_port: str = '8',
				 script_file: str = None,
				 passstring: str = 'Test Complete',
				 failstring: str = 'Test Failed',):

		self.name = name
		self.tnumber = tnumber
		self.content = content
		self.visual = visual
		self.qdf = qdf
		self.bucket = bucket
		self.coreslice = coreslice
		self.fastboot = fastboot
		self.postcode_break = postcode_break
		self.target = target
		self.mask = mask
		self.pseudo = pseudo
		self.dis2CPM = dis2CPM
		self.corelic = corelic
		self.ttime = ttime
		self.reset = reset
		self.resetonpass = resetonpass
		self.extMask = extMask
		self.u600w = u600w
		self.summary = summary
		self.host = host
		self.script_file = script_file
		self.com_port = com_port
		self.passstring = passstring
		self.failstring = failstring
		# TTL Macros paths
		self.macro_files = macro_cmds
		self.log_file_path = ser.log_file_path
		
		# Test Folder -- Will be updated once called by the function
		self.tfolder = None

		#  Log File -- Will be updated once called by the function
		self.log_file = None
				
		# Experiment Type -- Will be updated once called by the function
		self.etype = None
		
		# Loop Variables -- Will be updated once called by the function
		self.loops = 5

		# Sweep Variables -- Will be updated once called by the function
		self.ttype = 'frequency'
		self.domain = 'ia'
		self.domains = ['ia' ,'cfc']

		# Voltage Variables -- Will be updated once called by the function
		self.volt_IA = volt_IA
		self.volt_CFC = volt_CFC
		self.volt_type = volt_type
		

		#Freq Variables -- Will be updated once called by the function
		self.freq_ia = freq_ia
		self.freq_cfc = freq_cfc

		# Content initialization and checks
		self.content_selection()
		self.target_validation()
		#self.datadict()
		#self.experimentdict()
		#self.fusesdict()

	def datadict(self):
		
		self.data = {
					'Visual':self.visual,
					'QDF': self.qdf,
					'Bucket':self.bucket,
					'MacroFile':self.macro_files,
					'TestFolder':self.tfolder,
					'LogFile':self.log_file_path,
					'Mesh':self.Mesh,
					'Slice':self.Slice,
					'FastBoot':self.fastboot,
					'CoreLicense': self.corelic,
					'ExternalMask': self.extMask,
					'u600w': self.u600w,
					}

	def experimentdict(self):

		self.experiment = {
					'Type': self.etype,
					'Name': self.name,
					'Number':self.tnumber,
					'Time':self.ttime,
					'Mask':self.mask,
					'Pseudo':self.pseudo,
					'2CPM':self.dis2CPM,
					'Dragon':self.runDragon,
					'Linux':self.runLinux,
					'PYSVConsole':self.runPYSVConsole,
					'Bootbreaks':self.runBootBreaks,
					'Core': self.coreslice,
					'Pass String': self.passstring,
					'Fail String': self.failstring,
					}

	def fusesdict(self):

		self.voltage = {
					'Type': self.volt_type,
					'IA': self.volt_IA,
					'CFC': self.volt_CFC,
					}

		self.frequency = {
					'IA': self.freq_ia,
					'CFC':self.freq_cfc,
					}

	def content_selection(self):

		self.runLinux = False
		self.runDragon = False
		self.runPYSVConsole = False
		
		# Checking if PYSVConsole will apply any breaks --
		self.runBootBreaks = True if self.postcode_break != None else False

		# BootBreaks is enabled when using PYSVConsole with a EFI Postcode Break != 0x0
		if self.content == 'Dragon': 
			self.runDragon = True
		elif self.content == 'Linux': 
			self.runLinux = True
		elif self.content == 'PYSVConsole' and not self.runBootBreaks: 
			self.runPYSVConsole = True
		elif self.content == 'PYSVConsole' and self.runBootBreaks: 
			self.runBootBreaks = True
		else:
			raise ValueError(f' --- Invalid selectd content -> {self.content} -- Content options are: Dragon | Linux | PYSVConsole')

	def target_validation(self):
		self.Slice = False
		self.Mesh = False
		# Checks for current Target
		if self.target == 'mesh':
			self.Mesh = True
			self.chkcore = self.coreslice
		elif self.target == 'slice':
			self.Slice = True
			self.chkcore = self.mask
		else:
			raise ValueError(f' --- Invalid selectd target -> {self.target} -- target should slice or mesh.')
			
	def configLoops(self, loops = 5):
		# Checks for current content

		self.description = f'T{self.tnumber}_{self.name}_Loops'#_n{loops}_{self.content}_{self.target}'
		self.update_dicts()

	def configSweep(self, ttype = 'frequency', domain = 'ia'):

		if domain not in self.domains: 
			raise ValueError(f' -- Invalid domain selection use: {self.domains}')
		
		# Required files -- TTL Macros, and paths
		self.description = f'T{self.tnumber}_{self.name}_Sweep'#_{self.content}_{self.target}_{ttype}_{domain}'
		self.update_dicts()

	def configShmoo(self, label='COREFIX'):
	
		# Required files -- TTL Macros, and paths
		self.description = f'T{self.tnumber}_{self.name}_Shmoo'#_{self.content}_{self.target}_{label}'
		self.update_dicts()

	def update_dicts(self):
		self.tfolder = fh.create_log_folder(logs_dest, self.description)#ser.tfolder
		self.log_file = os.path.join(self.tfolder, 'DebugFrameworkLogger.log')

		self.datadict()
		self.experimentdict()
		self.fusesdict()

class defeature():

	def __init__(self, Experiment, cancel_flag = None):
				# data: dict,
				# experiment: dict = None,
				# voltage: dict  = None,
				# frequency: dict = None,
				# log_file: str = None,
				# host: str = "10.250.0.2",
				# com_port: str = '8',
				# script_file: str = None):
		#super().__init__(data, experiment, voltage, frequency, log_file, host, com_port, script_file)
		self.cancel_flag = cancel_flag
		self.data = Experiment.data
		self.experiment = Experiment.experiment
		self.voltage = Experiment.voltage
		self.frequency = Experiment.frequency
		self.Reset = Experiment.reset # Resets Unit on each iteration by default True
		self.resetonpass = Experiment.resetonpass
		self.s2t_config_path = r"C:\Temp\System2TesterRun.json"
		self.pysvconsole_path = r"C:\Temp\PythonSVLog.log"
		self.log_file = Experiment.log_file
		self.script_file = Experiment.script_file
		self.scratchpad = ''
		self.host = Experiment.host
		self.com_port = Experiment.com_port
		self.running_iteration = 1
		self.running_test = None
		self.runStatus = None
		self.runName = None
		self.boot_postcode = False
		#print(data)
		#print(experiment)
		#print(voltage)
		#print(frequency)
		# Initialize logging
		#self.gdflog = fh.printlog(self.log_file)
		self.updatevars()
		self.initlog()
		self.system_to_tester_configuration()

	def system_to_tester_configuration(self):

		self.Debuglog(' System to Tester Boot Parameters -- ')
		self.Debuglog(f'Bootscript retries: {gcm.BOOTSCRIPT_RETRY_TIMES}')
		self.Debuglog(f'Bootscript retry PC delay: {gcm.BOOTSCRIPT_RETRY_DELAY}')
		self.Debuglog(f'EFI Postcode: {gcm.EFI_POST}')
		self.Debuglog(f'EFI Postcode Waittime: {gcm.EFI_POSTCODE_WT}')
		self.Debuglog(f'EFI Postcode checks count: {gcm.EFI_POSTCODE_CHECK_COUNT}')
		self.Debuglog(f'OTHER Postcode: {gcm.LINUX_POST}')
		self.Debuglog(f'MRC Postcode: {gcm.AFTER_MRC_POST}')
		self.Debuglog(f'MRC Postcode Waittime: {gcm.MRC_POSTCODE_WT}')		
		self.Debuglog(f'MRC Postcode checks count: {gcm.MRC_POSTCODE_CHECK_COUNT}')	
		self.Debuglog(f'Boot Break Postcode: {gcm.BOOT_STOP_POSTCODE}')	
		self.Debuglog(f'Boot Break Waittimet: {gcm.BOOT_POSTCODE_WT}')	
		self.Debuglog(f'Boot Break checks count: {gcm.BOOT_POSTCODE_CHECK_COUNT}')	

	def initlog(self):
		self.gdflog = fh.FrameworkLogger(self.log_file, 'FrameworkLogger', True, True)
		# Initialize log file
		#if self.log_file:
		#	with open(self.log_file, 'w', encoding='utf-8') as f:
		#		f.write('')  # Create or override the log file

	def Debuglog(self, message, event_type=1): #console_show= True, event_type=0):
		#self.gdflog.log(message, console_show, event_type)
		self.gdflog.log(message, event_type)
		#if console_show: print(message)
		#if self.log_file:
		#	with open(self.log_file, 'a', encoding='utf-8') as f:
		#		if isinstance(message, pd.DataFrame):
		#			message = message.to_string()
		#		elif isinstance(message, list):
		#			message = '\n'.join(map(str, message))  # Convert list to string
		#	
		#		f.write(message + '\n')
			
	def updatevars(self):

		## Collect Data from data dictionary
		self.visual = self.data.get('Visual')
		self.qdf = self.data.get('QDF')
		self.bucket = self.data.get('Bucket')
		self.macro_files =  self.data.get('MacroFile')
		self.tfolder =  self.data.get('TestFolder')
		self.log_file_path =  self.data.get('LogFile')
		self.ismesh =  self.data.get('Mesh')
		self.isslice =  self.data.get('Slice')
		self.fastboot = self.data.get('FastBoot')
		self.corelic = self.data.get('CoreLicense')
		self.extMask = self.data.get('ExternalMask')
		self.u600w = self.data.get('u600w')
		## Collect Experiment Information --
		self.etype = self.experiment.get('Type')
		self.tname = self.experiment.get('Name')
		self.tnum = self.experiment.get('Number',1)
		if type(self.tnum) != int:
			print('Test Number needs to be an integer -- Changing it to default of 1')
			self.tnum = 1
		
		self.ttime = self.experiment.get('Time')
		self.mask = self.experiment.get('Mask')

		self.htdis = self.experiment.get('Pseudo')
		self.dis2CPM = self.experiment.get('2CPM')
		self.Dragon = self.experiment.get('Dragon')
		self.Linux = self.experiment.get('Linux')
		self.PYSVConsole = self.experiment.get('PYSVConsole', False)
		self.Bootbreaks = self.experiment.get('Bootbreaks', False)
		self.coreslice = self.experiment.get('Core')
		self.passstring = self.experiment.get('Pass String','Test Complete')
		self.failstring = self.experiment.get('Fail String', 'Test Failed')

		if self.Dragon: self.content = 'Dragon'
		elif  self.Linux: self.content = 'Linux'
		elif  self.PYSVConsole: self.content = 'PYSVConsole'
		elif  self.Bootbreaks: self.content = 'BootBreaks'
		else: self.content = None

		## Voltage variables
		self.bumps = self.voltage.get('Type')
		self.voltIA = self.voltage.get('IA')
		self.voltCFC = self.voltage.get('CFC')

		## Frequency variables
		self.freqIA = self.frequency.get('IA')
		self.freqCFC = self.frequency.get('CFC')

		self.shmoodata = pd.DataFrame()
		self.legends = pd.DataFrame()

	def Test(self):
		## Print Test Banner
		#self.Debuglog(f'\n{print_separator_box(direction="down")}\n')
		self.check_user_cancel()
		self.TestBanner()
		ser.kill_process(process_name = 'ttermpro.exe', logger = self.Debuglog)
		boot_logging = False

		## Build variables for log and string data
		vbumps = True if self.voltIA != None or self.voltCFC != None else False
		
		if self.content == 'BootBreaks':
			self.boot_postcode = True
			boot_logging = True
		
		vtstring = self.tnamestr('_vcfg_',self.bumps) if vbumps else ""
		iaF = self.tnamestr('_ia_f',self.freqIA)
		cfcF = self.tnamestr('_cfc_f',self.freqCFC)
		iavolt = self.tnamestr('_ia_v',self.voltIA).replace(".","_")
		cfcvolt = self.tnamestr('_cfc_v',self.voltCFC).replace(".","_")
		mask = self.tnamestr('',self.mask,"System")
		tname = self.tname.strip(' ')
		test = f'{tname}_{mask}{iaF}{cfcF}{vtstring}{iavolt}{cfcvolt}'
		coreslice = self.coreslice
		bootReady = False # This is to indicate a succesfull boot not used for now...
		validPYSVLog = False
		validTTLog = False

		## Setting Serial configuration
		serial = ser.teraterm(visual=self.visual, qdf=self.qdf, bucket=self.bucket, log=self.log_file_path, cmds=self.macro_files, tfolder=self.tfolder, test=test, ttime=self.ttime, tnum=self.tnum, DebugLog = self.Debuglog, chkcore = self.coreslice, content = self.content, host = self.host, PassString = self.passstring, FailString = self.failstring, cancel_flag = self.cancel_flag)
		if boot_logging: serial.boot_start()

		
		# Start Capturing PythonSV Console
		log(self.pysvconsole_path)

		## Calls script for either mesh or slice
		if self.ismesh:

			try: 
				s2t.MeshQuickTest(core_freq = self.freqIA, mesh_freq = self.freqCFC, vbump_core = self.voltIA, vbump_mesh = self.voltCFC, Reset = self.Reset, Mask = self.mask, pseudo = self.htdis, dis_2CPM = self.dis2CPM, GUI = False, fastboot = self.fastboot, corelic = self.corelic, volttype=self.bumps, debug= False, boot_postcode = self.boot_postcode, extMask = self.extMask)
				self.check_user_cancel()
				bootReady = True
			except KeyboardInterrupt:
				self.Debuglog("Script interrupted by user. Exiting...",2)
				return None			
			except InterruptedError:
				self.Debuglog("Script interrupted by user. Exiting...",2)
				return None	
			except Exception as e: 				
				self.Debuglog(f' Boot Failed with Exception {e} --- Might be an issue with bootscript -- Retrying..... ',4)
				self.powercycle(u600w = self.u600w)
				s2t.MeshQuickTest(core_freq = self.freqIA, mesh_freq = self.freqCFC, vbump_core = self.voltIA, vbump_mesh = self.voltCFC, Reset = self.Reset, Mask = self.mask, pseudo = self.htdis, dis_2CPM = self.dis2CPM, GUI = False, fastboot = self.fastboot, corelic = self.corelic, volttype=self.bumps, debug= False, boot_postcode = self.boot_postcode, extMask = self.extMask)
				#self.check_user_cancel()
				bootReady = True
			finally:
				if bootReady: 
					self.Debuglog(' Framework boot process completed.....',1)
				else: 
					
					self.Debuglog(' Framework was not able to properly configure the system. Check log for details.....',3)

		elif self.isslice:

			try:
				s2t.SliceQuickTest(Target_core = coreslice, core_freq = self.freqIA, mesh_freq = self.freqCFC, vbump_core = self.voltIA, vbump_mesh = self.voltCFC, Reset = self.Reset, pseudo = False, dis_2CPM = self.dis2CPM, GUI = False, fastboot = self.fastboot, corelic = self.corelic, volttype = self.bumps, debug= False, boot_postcode = self.boot_postcode)
				self.check_user_cancel()
				bootReady = True
			except KeyboardInterrupt:
				self.Debuglog("Script interrupted by user. Exiting...",2)
				return None		
			except InterruptedError:
				self.Debuglog("Script interrupted by user. Exiting...",2)
				return None	
			except Exception as e: 
				self.Debuglog(f' Boot Failed with Exception {e} --- Might be an issue with bootscript -- Retrying..... ',4)
				self.powercycle(u600w = self.u600w)
				#dpm.powercycle(ports=[1])
				#time.sleep(60)
				#gcm._wait_for_post(gcm.EFI_POST, sleeptime=60)
				#gcm.svStatus(refresh=True)		
				s2t.SliceQuickTest(Target_core = coreslice, core_freq = self.freqIA, mesh_freq = self.freqCFC, vbump_core = self.voltIA, vbump_mesh = self.voltCFC, Reset = self.Reset, pseudo = False, dis_2CPM = self.dis2CPM, GUI = False, fastboot = self.fastboot, corelic = self.corelic, volttype = self.bumps, debug= False, boot_postcode = self.boot_postcode)
				#self.check_user_cancel()
				bootReady = True
			finally:
				if bootReady: 
					self.Debuglog(' Framework boot process completed.....',1)
				else: 
					
					self.Debuglog(' Framework was not able to properly configure the system. Check log for details.....',3)

		else:
			self.Debuglog(" --- Not valid type of test, select either mesh or slice",3)
			sys.exit()

		if self.script_file != None:
			
			if self.content == 'BootBreaks': 	
				self.Debuglog(f" --- Executing Custom script at reached boot Breakpoint: {self.script_file}",1)

			elif self.content == 'PYSVConsole': 				
				self.Debuglog(f" --- Executing Custom script before test: {self.script_file}",1)

			fh.execute_file(file_path = self.script_file, logger = self.Debuglog)
			
			#if self.content == 'PYSVConsole' or self.content == 'BootBreaks': 
			
		# End Capturing PythonSV Console
		nolog()

		# Start SelfChecks -- 
		if self.content == 'PYSVConsole': serial.PYSVconsole()
		elif self.content == 'BootBreaks': serial.boot_end()
		else: serial.run()

		## Take data from current run PASS / FAIL and testname
		result = serial.testresult.split("::") if serial.testresult != None else ['NA','NA']
		
		self.runStatus = result[0]
		self.runName = result[-1]
		
		pysvlog_new_path = os.path.join(self.tfolder, f'{self.tnum}_{test}_pysv.log')
		#if self.script_file != None:
		if os.path.exists(self.pysvconsole_path):
			shutil.copy(self.pysvconsole_path, pysvlog_new_path)
			validPYSVLog = True
		else:
			validPYSVLog = False

		## Moves the log a another file to avoid overwrite in loops
		log_new_path = os.path.join(self.tfolder, f'{self.tnum}_{test}.log')

		if os.path.exists(self.log_file_path):
			shutil.copy(self.log_file_path, log_new_path)
			validTTLog = True
		else:
			validTTLog = False
		
		## Saves current configuration into selected new path
		s2t_config_path = os.path.join(self.tfolder, f'{self.tnum}_{test}.json')
		if os.path.exists(self.s2t_config_path):
			shutil.copy(self.s2t_config_path, s2t_config_path)

		self.check_user_cancel()		
		self.seed = fh.extract_fail_seed(log_new_path)
		self.scratchpad = serial.scratchpad
		self.Iteration_end(log_new_path, s2t_config_path, pysvlog_new_path, validTTLog,validPYSVLog)


		#self.Debuglog(f'tdata_{self.tnum}::{self.runName}::{self.runStatus}::{self.scratchpad}::{self.seed}')
		#self.Debuglog(print_custom_separator(f'Test iteration summary'))
		#self.Debuglog(f' -- Test Name: {self.runName} --- ')
		#self.Debuglog(f' -- Test Result: {self.runStatus} --- ')
		#self.Debuglog(f' -- Dragon Seeds Status: {self.seed} --- ')
		#self.Debuglog(f' -- Current Unit Scratchpad: {self.scratchpad} --- ')
		#self.Debuglog(f' -- SerialConsoleLog: {log_new_path} --- ')
		#self.Debuglog(f' -- System2TesterConfig: {s2t_config_path} --- ')
		#self.Debuglog(f' -- Test End --- ')

	def Iteration_end(self, log_new_path, s2t_config_path, pysvlog_new_path, validTTLog,validPYSVLog):

		self.Debuglog(f'tdata_{self.tnum}::{self.runName}::{self.runStatus}::{self.scratchpad}::{self.seed}')
		self.Debuglog(print_custom_separator(f'Test iteration summary'))
		self.Debuglog(f' -- Test Name: {self.runName} --- ')
		self.Debuglog(f' -- Test Result: {self.runStatus} --- ')
		if self.content == 'Dragon': self.Debuglog(f' -- Dragon Seeds Status: {self.seed} --- ')
		self.Debuglog(f' -- Current Unit Scratchpad: {self.scratchpad} --- ')
		if validTTLog: self.Debuglog(f' -- SerialConsoleLog: {log_new_path} --- ')
		if validPYSVLog: self.Debuglog(f' -- SerialConsoleLog: {pysvlog_new_path} --- ')
		self.Debuglog(f' -- System2TesterConfig: {s2t_config_path} --- ')
		self.Debuglog(f' -- Test End --- ')

	def TestBanner(self):
		
		if self.ismesh and self.Dragon:
			runtxt = f' -- Running Dragon {"Pseudo " if self.htdis else "Bare Metal"} content --- '
		elif self.isslice and self.Dragon:
			runtxt = f' -- Running Dragon Slice content --- '
		self.Debuglog(f' -- Test Start --- ')
		self.Debuglog(f' -- Debug Framework {self.tname} --- ')
		self.Debuglog(f' -- Performing test iteration {self.tnum} with the following parameters: ')
		if self.Dragon: self.Debuglog(f'{runtxt}')
		if self.Linux: self.Debuglog(f' -- Running Linux Content ---') # Need to add more here, stil WIP, working only for Dragon
		if self.PYSVConsole: self.Debuglog(f' -- PYSVConsole Custom Script Run ---')
		if self.Bootbreaks: self.Debuglog(f' -- Boot Breakpoint Test ---')
		self.Debuglog(f'\t > Unit VisualID: {self.visual}')
		self.Debuglog(f'\t > Unit QDF: {self.qdf}')
		self.Debuglog(f'\t > Configuration: {self.mask if self.mask != None else "System Mask"} ')
		if self.corelic: self.Debuglog(f'\t > Core License: {self.corelic} ')
		self.Debuglog(f'\t > Voltage set to: {self.bumps} ')
		self.Debuglog(f'\t > HT Disabled (BigCore): {self.htdis} ')
		self.Debuglog(f'\t > Dis 2 Cores (Atomcore): {self.dis2CPM} ')
		self.Debuglog(f'\t > Core Freq: {self.freqIA} ')
		self.Debuglog(f'\t > Core Voltage: {self.voltIA} ')
		self.Debuglog(f'\t > Mesh Freq: {self.freqCFC} ')
		self.Debuglog(f'\t > Mesh Voltage: {self.voltCFC} ')
		if self.u600w: self.Debuglog(f'\t > Unit 600w Fuses Applied ')
		if self.extMask != None:
			printmasks = [["Type", "Value"]]
			printmasks.append([[k,v] for k, v in self.extMask.items()])
			self.Debuglog(f'\t > Using External Base Mask: {printmasks} \n')
			self.Debuglog(tabulate(printmasks, headers="firstrow", tablefmt="grid"))

	def tnamestr(self,prefix, value, default = ""):
		tstr = f'{prefix}{value}' if value != None or value != None else default
		return tstr

	def tarray(self, ttype, start, end, step):
		
		if start > end:
			_start = start
			_end = end
			invert = True
		else:
			_start = start
			_end = end
			invert = False
		
		# Depending on type will build the new array
		if ttype == 'frequency':

			rng = list(range(_start, _end+step, step))
			if rng[-1] > end: rng[-1] = _end

		elif ttype == 'voltage':
			rng = []
			current = _start
			# Round to 5 decimals max
			while current < (_end+step):
				current = round(current,5)
				rng.append(current)
				current += step
				#print(current,end,step)
			if rng[-1] > _end: rng[-1] = _end

		else:
			self.Debuglog(' --- Invalid type selected for a Sweep test: options are [frequency, voltage]',3)
			sys.exit()
		if invert: 
			self.Debuglog(' --- Reversed range used for Sweep Experiment.')
			rng = rng[::-1]
		return rng

	def tupdate(self, ttype, domain, value):
		# Update frequency  /voltage value
		if ttype == 'frequency':
			if domain == 'ia': self.freqIA = value
			if domain == 'cfc': self.freqCFC = value

		if ttype == 'voltage':
			if domain == 'ia': self.voltIA = value
			if domain == 'cfc': self.voltCFC = value

	def powercycle(self, u600w):

		if not u600w: 
			dpm.powercycle(ports=[1])
		else:
			dpm.powercycle(ports=[1])
			time.sleep(60)
			dpm.reset_600w()
		time.sleep(60)
		gcm._wait_for_post(gcm.EFI_POST, sleeptime=60)
		gcm.svStatus(refresh=True)				

	## Test Types
	def Sweep(self, domain, ttype, start, end, step):
		self.initlog()
		self.Debuglog(print_custom_separator(f'Starting Sweep  -- {domain.upper()}:{ttype.upper()}'))
		## Condition if start > end??

		rng = self.tarray(ttype, start, end, step)
		failnum = 0
		## Loop
		shmooy = []
		legends = []
		for r in rng:
			self.check_user_cancel()
			self.Debuglog(f'{print_separator_box(direction="down")}')
			self.Debuglog(print_custom_separator(f'Running Sweep iteration:{self.tnum}'))
				
			# Update frequency  /voltage value
			self.tupdate(ttype=ttype, domain=domain, value=r)

			## Run the test
			self.Test()
			self.Debuglog(f' -- Test iteration {self.tnum} Completed.... ')
			self.Debuglog(f'Test Result:: {self.runStatus} -- {self.runName}')
			if self.runStatus == 'FAIL':
				fail_letter = chr(65+failnum)
				legends.append(f'{fail_letter} - {self.tnum}:{self.scratchpad}:{self.seed}')
				shmooy.append([fail_letter])
				failnum += 1
				self.Reset = True
			else:
				shmooy.append(["*"])
				if self.resetonpass == True: self.Reset = True
				else: self.Reset = False


			# Update test Number for next Iteartion
			self.tnum += 1
			self.Debuglog(f'{print_separator_box(direction="up")}')
			time.sleep(10)
		self.legends =  pd.DataFrame(legends,columns=["Legends"])
		self.shmoodata = pd.DataFrame(shmooy, columns=[ttype], index=rng)
		#self.shmoo = shmooy

	def Loop(self, loops):
		self.initlog()
		self.Debuglog(print_custom_separator(f'Starting Loop'))

		## Loop
		shmooy = []
		legends = []
		failnum = 0
		for l in range(loops):
			self.check_user_cancel()
			self.Debuglog(f'{print_separator_box(direction="down")}')
			self.Debuglog(print_custom_separator(f'Running Loop iteration:{self.tnum}'))
				
			# Update frequency  /voltage value

			## Run the test
			self.Test()
			self.Debuglog(f' -- Test iteration {self.tnum} Completed.... ')
			self.Debuglog(f'Test Result:: {self.runStatus} -- {self.runName}')
			if self.runStatus == 'FAIL':
				fail_letter = chr(65+failnum)
				
				legends.append(f'{fail_letter} - {self.tnum}:{self.scratchpad}:{self.seed}')
				shmooy.append([fail_letter])
				failnum += 1
				self.Reset = True
			else:
				shmooy.append(["*"])
				if self.resetonpass == True: self.Reset = True
				else: self.Reset = False


			# Update test Number for next Iteartion
			self.tnum += 1
			self.Debuglog(f'{print_separator_box(direction="up")}')
			time.sleep(10)
		self.legends =  pd.DataFrame(legends,columns=["Legends"])
		self.shmoodata = pd.DataFrame(shmooy, columns=["Loops"])
		#self.shmoo = shmooy

	def Shmoo(self, xvalues, yvalues):
		self.initlog()
		self.Debuglog(print_custom_separator(f'Starting Shmoo'))
		## Condition if start > end??
		ttypex = xvalues.get('Type')
		domainx = xvalues.get('Domain')
		startx = xvalues.get('Start')
		endx = xvalues.get('End')
		stepx = xvalues.get('Step')

		## Condition if start > end??
		ttypey = yvalues.get('Type')
		domainy = xvalues.get('Domain')
		starty = yvalues.get('Start')
		endy = yvalues.get('End')
		stepy = yvalues.get('Step')

		rngx = self.tarray(ttypex, startx, endx, stepx)
		rngy = self.tarray(ttypey, starty, endy, stepy)
		## Loop
		failnum= 0
		shmooy = []
		legends = []
		#print(rngx)
		#print(rngy)
		#time.sleep(60)
		for ry in rngy:
			
			self.tupdate(ttype=ttypey, domain=domainy, value=ry)
			shmoox = []
			for rx in rngx:
				self.check_user_cancel()
				self.Debuglog(f'{print_separator_box(direction="down")}')
				self.Debuglog(print_custom_separator(f'Running shmoo iteration:{self.tnum}'))
				self.tupdate(ttype=ttypex, domain=domainx, value=rx)
				## Run the test

				self.Test()

				self.Debuglog(f' -- Test iteration {self.tnum} Completed.... ')
				self.Debuglog(f'Test Result:: {self.runStatus} -- {self.runName}')

				if self.runStatus == 'FAIL':
					fail_letter = chr(65+failnum)
					legends.append(f'{fail_letter} - {self.tnum}:{self.scratchpad}:{self.seed}')
					shmoox.append(fail_letter)
					failnum += 1
					self.Reset = True
				else:
					shmoox.append("*")
					if self.resetonpass == True: self.Reset = True
					else: self.Reset = False
				# Update test Number for next Iteartion
				self.tnum += 1
				self.Debuglog(f'{print_separator_box(direction="up")}')
				time.sleep(10)
			self.Debuglog(shmoox)
			self.Debuglog(legends)
			shmooy.append(shmoox)
			self.Debuglog(shmooy)
		self.legends = pd.DataFrame(legends,columns=["Legends"])
		self.shmoodata = pd.DataFrame(shmooy, columns=rngx, index=rngy) #shmooy

	def check_user_cancel(self):
		cancel_check = self.cancel_flag != None
		if cancel_check:
			#print('Checking Cancel Status', cancel_check, self.cancel_flag.is_set())	
			if self.cancel_flag.is_set():
				self.Debuglog("Framework Execution interrupted by user. Exiting...",2)
				raise InterruptedError('Execution Interrupted by User')

## Framework Automation functions Object
class Framework():
	
	def __init__(	self,
			  		name: str = 'Experiment',
				 	tnumber: int = 1,
				 	content: str = 'Dragon',
				 	visual: str = '-9999999',
				 	qdf: str = '',
				 	bucket: str = 'FRAMEWORK',
				 	macro_files: str = None,
				 	coreslice: int = None,
				 	fastboot: bool = True,
					postcode_break: int = None,
				 	target: str = 'mesh',
				 	mask: str = None,
				 	pseudo: bool = True,
				 	dis2CPM: int = None, 
				 	corelic: int = None, 
				 	ttime: int =30,  
				 	reset: bool = True, 
				 	resetonpass: bool = False, 
				 	extMask: dict = None, 
				 	u600w: bool = False, 
				 	summary: bool = True,
				 	host: str = "10.250.0.2",
				 	com_port: str = '8',
				 	script_file: str = None,
					passstring: str = 'Test Complete',
					failstring: str = 'Test Failed',
					):
		
		self.Experiment_Data = None
		self.Defeature = None
		self.current_iteration = 0
		self.current_test = None
		self.cancel_flag = None
		
		# Experiment Data
		self.name = name
		self.tnumber = tnumber
		self.content = content
		self.visual = visual
		self.qdf = qdf
		self.bucket = bucket
		self.ttime = ttime
		self.reset = reset
		self.resetonpass = resetonpass
		self.macro_files = macro_files
		self.coreslice = coreslice
		self.fastboot = fastboot
		self.postcode_break = postcode_break
		self.target = target
		self.mask = mask
		self.pseudo = pseudo
		self.dis2CPM = dis2CPM
		self.corelic = corelic
		self.extMask = extMask
		self.u600w = u600w
		self.summary = summary
		self.host = host
		self.com_port = com_port
		self.script_file = script_file
		self.passstring = passstring
		self.failstring = failstring

	def update_system_to_tester_config(self, data):		

		gcm.AFTER_MRC_POST = data['AFTER_MRC_POST']
		gcm.EFI_POST = data['EFI_POST']
		gcm.LINUX_POST = data['LINUX_POST']
		gcm.BOOTSCRIPT_RETRY_TIMES = data['BOOTSCRIPT_RETRY_TIMES']
		gcm.BOOTSCRIPT_RETRY_DELAY = data['BOOTSCRIPT_RETRY_DELAY']
		gcm.MRC_POSTCODE_WT = data['MRC_POSTCODE_WT']
		gcm.EFI_POSTCODE_WT = data['EFI_POSTCODE_WT']
		gcm.MRC_POSTCODE_CHECK_COUNT = data['MRC_POSTCODE_CHECK_COUNT']
		gcm.EFI_POSTCODE_CHECK_COUNT = data['EFI_POSTCODE_CHECK_COUNT']
		gcm.BOOT_STOP_POSTCODE = data['BOOT_STOP_POSTCODE']
		gcm.BOOT_POSTCODE_WT = data['BOOT_POSTCODE_WT']	
		gcm.BOOT_POSTCODE_CHECK_COUNT = data['BOOT_POSTCODE_CHECK_COUNT']		

	def update_voltage_config(self, volt_type, volt_IA, volt_CFC):
			
		self.volt_type= volt_type
		self.volt_IA = volt_IA
		self.volt_CFC = volt_CFC

	def update_misc_configs(self, summary):
		
		self.summary = summary
	
	def update_frequency_config(self, freq_ia, freq_cfc):

		self.freq_ia = freq_ia
		self.freq_cfc =freq_cfc

	def update_platform_setup(self, u600w, host, com_port):
		self.u600w = u600w
		self.host = host
		self.com_port = com_port

	def update_test_required_files(self, script_file, macro_files):

		self.script_file = script_file
		self.macro_files = macro_files    		

	def update_experiment_data(self):
			
		self.Experiment_Data = Experiment(	name =  self.name,
								tnumber = self.tnumber,
								content = self.content,
								visual = self.visual,
								bucket =self.bucket,
								qdf=self.qdf,
								macro_cmds = self.ttl_macros,
								coreslice = self.coreslice,
								fastboot = self.fastboot,
								postcode_break = self.postcode_break,
								target = self.target,
								mask = self.mask,
								volt_type= self.volt_type, 
								volt_IA = self.volt_IA, 
								volt_CFC = self.volt_CFC,
								freq_ia = self.freq_ia, 
								freq_cfc = self.freq_cfc, 
								pseudo = self.pseudo,
								dis2CPM = self.dis2CPM, 
								corelic = self.corelic, 
								ttime = self.ttime,  
								reset = self.reset, 
								resetonpass = self.resetonpass, 
								extMask = self.extMask, 
								u600w = self.u600w, 
								summary = self.summary,
								host = self.host,
								com_port = self.com_port,
								script_file = self.script_file,
								passstring = self.passstring, 
								failstring = self.failstring)
	
	def set_defeature_config(self):	
		self.Defeature = defeature(Experiment = self.Experiment_Data, cancel_flag=self.cancel_flag)

	def check_ttl_macro(self):
		
		## Defaults to TTL files in C:\SystemDebug\TTL
		if self.macro_files == None: 
			self.ttl_macros = macro_cmds 
		else:
			self.ttl_macros = macros_path(self.macro_files)
		
		print(f'Using TTL Files: {self.ttl_macros}')

	def check_reset_on_pass_condition(self):
		# Passing reset variables
		if self.volt_type == 'vbump':
			self.Defeature.resetonpass = True
			self.Defeature.Debuglog('Units will reset on pass when using vbumps  --- \n')

	def end_summary(self):

		shmoodata = self.Defeature.shmoodata
		legends = self.Defeature.legends

		# Builds Unit Summary
		if self.summary:
			self.show_summary()

		# Prints Shmoo data
		self.Defeature.Debuglog(f'{self.Test_Type} Test Results --- \n')
		self.Defeature.Debuglog(shmoodata)
		self.Defeature.Debuglog('\nLegends:')
		self.Defeature.Debuglog(legends)

		self.upload_data()

	def show_summary(self):
		logger = self.Defeature.Debuglog
		bucket = self.bucket
		tfolder = self.Defeature.tfolder
		visual = self.visual
		name = self.name

		SummaryName = f'Summary_{visual}_{name}'
		SummaryFile = fh.create_path(tfolder, f'{SummaryName}.xlsx')
		WW = str(dpm.getWW())
		Product = s2t.SELECTED_PRODUCT

		logger('Generating Summary files --- \n')

		fh.merge_mca_files(input_folder=tfolder, output_file=SummaryFile)
		fh.decode_mcas(name=SummaryName, week=WW, source_file=SummaryFile, label=bucket, path=tfolder, product = Product)

	def upload_data(self):
		logger = self.Defeature.Debuglog
		tfolder = self.Defeature.tfolder
		visual = self.visual
		Product = s2t.SELECTED_PRODUCT

		## Temporary DATA Destination -- Saving it into I Drive for now
		DATA_SERVER = r'\\Amr\ec\proj\mdl\cr'
		DATA_DESTINATION = rf'{DATA_SERVER}\intel\engineering\dev\user_links\gaespino\DebugFramework\{Product}'

		logger('Copying Data to Server --- \n')
		dest_folder=fh.copy_folder(src=tfolder, dest=DATA_DESTINATION, visual=visual, zipdata=True , logger = logger)
		
		if DATABASE_HANDLER_READY:
			try:
				db.upload_summary_report(storage_dir=dest_folder)
			except Exception as e:
				logger(f' Failed updloading data to DantaDB -- Exception {e}',2)
			
	def Sweep(self, 
				ttype = 'frequency', 
				domain = 'ia', 
				start = 16, 
				end = 39, 
				step= 4, 
				volt_type= 'vbump', 
				volt_IA = None,	
				volt_CFC = None, 
				freq_ia = None, 
				freq_cfc =None,):
		
		# Variable Initialization
		self.Test_Type = 'Sweep'
		self.update_voltage_config(volt_type, volt_IA, volt_CFC)
		self.update_frequency_config(freq_ia, freq_cfc)

		self.check_ttl_macro()
		
		# Update Experiment and Defeature Objects
		self.update_experiment_data()
		
		# Setup Selected TestType Configuration
		self.Experiment_Data.configSweep(ttype=ttype, domain=domain)
		
		# Setup for the defeature config using experiment data
		self.set_defeature_config()

		# Checks Reset on Pass condition based on voltaje selection
		self.check_reset_on_pass_condition()

		# Starts the test
		self.Defeature.Sweep(domain=domain, ttype=ttype, start=start, end=end, step=step)
		
		# End Flow
		self.end_summary()

	def Shmoo(self,
				file=r'C:\Temp\ShmooData.json', 
				label='COREFIX',):

		# Collect data from Json file
		shmoojs = dpm.dev_dict(file, False)
		shmoojson = shmoojs[label]

		volt_type = shmoojson['VoltageSettings']['Type']
		volt_IA = shmoojson['VoltageSettings']['core']
		volt_CFC = shmoojson['VoltageSettings']['cfc']

		freq_ia = shmoojson['FrequencySettings']['core']
		freq_cfc = shmoojson['FrequencySettings']['cfc']

		xvalues = shmoojson['Xaxis']
		yvalues = shmoojson['Yaxis']

		
		# Variable Initialization
		self.Test_Type = 'Shmoo'
		self.update_voltage_config(volt_type, volt_IA, volt_CFC)
		self.update_frequency_config(freq_ia, freq_cfc)

		self.check_ttl_macro()
		
		# Update Experiment and Defeature Objects
		self.update_experiment_data()
		
		# Setup Selected TestType Configuration
		self.Experiment_Data.configShmoo(label=label)
		
		# Setup for the defeature config using experiment data
		self.set_defeature_config()

		# Checks Reset on Pass condition based on voltaje selection
		self.check_reset_on_pass_condition()

		# Starts the test
		self.Defeature.Shmoo(xvalues=xvalues, yvalues=yvalues)
		
		# End Flow
		self.end_summary()

	def Loops(self, 
				loops = 5, 
				volt_type= 'bumps', 
				volt_IA = None, 
				volt_CFC = None, 
				freq_ia=None, 
				freq_cfc=None,):

		
		# Variable Initialization
		self.Test_Type = 'Loops'

		self.update_voltage_config(volt_type, volt_IA, volt_CFC)
		self.update_frequency_config(freq_ia, freq_cfc)

		self.check_ttl_macro()
		
		# Update Experiment and Defeature Objects
		self.update_experiment_data()

		# Setup Selected TestType Configuration		
		self.Experiment_Data.configLoops(loops=loops)

		# Setup for the defeature config using experiment data
		self.set_defeature_config()

		# Checks Reset on Pass condition based on voltaje selection
		self.check_reset_on_pass_condition()

		# Starts the test
		self.Defeature.Loop(loops=loops)
		
		# End Flow
		self.end_summary()

	def RecipeExecutor(self, data, S2T_BOOT_CONFIG = None, extmask = None, summary=True, cancel_flag = None):
		self.cancel_check = cancel_flag != None
		self.cancel_flag = cancel_flag
		if self.cancel_check: gcm.cancel_flag = self.cancel_flag
		
		if S2T_BOOT_CONFIG == None: 
			S2T_BOOT_CONFIG = self.system_2_tester_default()

		# Updating Experiment with newest data
		self.name = data.get('Test Name','')
		self.tnumber = data.get('Test Number', 1)
		self.content = data.get('Content', 'Dragon')
		self.visual = data.get('Visual ID', '-9999999')

		if self.qdf == '': self.qdf == dpm.qdf_str()

		self.bucket = data.get('Bucket', 'FRAMEWORK')
		self.ttime = data.get('Test Time', 30)
		self.reset = data.get('Reset', True)
		self.resetonpass = data.get('Reset on PASS', True)
		self.macro_files = data.get('TTL Folder', '')
		self.coreslice = data.get('Check Core', '')
		self.fastboot = data.get('FastBoot', False)
		self.target = data.get('Test Mode', '').lower()
		self.mask = data.get('Configuration (Mask)', '')
		self.pseudo = data.get('Pseudo Config', False)
		self.dis2CPM = int(data.get('Disable 2 Cores', None),16) if (data.get('Disable 2 Cores', None) != None) else None 
		self.corelic = int(data.get('Core License',None).split(":")[0]) if (data.get('Core License',None) != None) else None
		self.extMask = extmask
		self.u600w = data.get('600W Unit', False)
		self.summary = summary
		self.host = data.get('IP Address', '192.168.0.2')
		self.com_port = data.get('COM Port', '8')
		self.script_file = data.get('Scripts File', None)
		self.postcode_break = data.get('Boot Breakpoint', None)
		## Lookup Strings for Pass/Fail Conditions
		self.passstring = data.get('Pass String', 'Test Complete')
		self.failstring = data.get('Fail String', 'Test Failed')

		S2T_BOOT_CONFIG['BOOT_STOP_POSTCODE'] = int(self.postcode_break,16) if self.postcode_break != None else 0x0
		self.update_system_to_tester_config(S2T_BOOT_CONFIG)		 

		if data['Test Type'] == 'Loops':				
					self.Loops(	
							loops = data['Loops'], 
							volt_type= data['Voltage Type'].lower(), 
							volt_IA = data['Voltage IA'], 
							volt_CFC = data['Voltage CFC'],
							freq_ia= data['Frequency IA'], 
							freq_cfc = data['Frequency CFC'], 
						)
					
		elif data['Test Type'] == 'Sweep':	
					self.Sweep(	
							ttype = data['Type'].lower(), 
							domain = data['Domain'].lower(), 
							start = data['Start'], 
							end = data['End'], 
							step= data['Steps'], 
							volt_type= data['Voltage Type'].lower(), 
							volt_IA = data['Voltage IA'], 
							volt_CFC = data['Voltage CFC'], 
							freq_ia=data['Frequency IA'], 
							freq_cfc=data['Frequency CFC'], 
							)			

		elif data['Test Type'] == 'Shmoo':	
					self.Shmoo(	
							file=data['ShmooFile'], 
							label=data['ShmooLabel'], 
							
							)

		# Returns Configuration to default values
		self.update_system_to_tester_config(self.system_2_tester_default())
		gcm.cancel_flag = None
		
	def check_user_cancel(self):
		if self.cancel_check:
			
			if self.cancel_flag.is_set():
				self.Debuglog("Framework Execution interrupted by user. Exiting...",2)
				raise InterruptedError('Execution Interrupted by User')

	@staticmethod
	def system_2_tester_default():

		S2T_CONFIGURATION = {	'AFTER_MRC_POST' : 0xbf000000,
								'EFI_POST' : 0xef0000ff,
								'LINUX_POST' : 0x58000000,
								'BOOTSCRIPT_RETRY_TIMES' : 3,
								'BOOTSCRIPT_RETRY_DELAY' : 60,
								'MRC_POSTCODE_WT' : 30,
								'EFI_POSTCODE_WT' : 60,
								'MRC_POSTCODE_CHECK_COUNT' : 5,
								'EFI_POSTCODE_CHECK_COUNT' : 10,
								'BOOT_STOP_POSTCODE' : 0x0,
								'BOOT_POSTCODE_WT' : 30,
								'BOOT_POSTCODE_CHECK_COUNT' : 10}
		
		return S2T_CONFIGURATION

	@staticmethod
	def Recipes(path=r'C:\Temp\DebugFrameworkTemplate.xlsx'):
		if path.endswith('.json'):
			data_from_sheets = fh.load_json_file(path)
			#tabulated_df = data_from_sheets
		elif path.endswith('.xlsx'):
			data_from_sheets = fh.process_excel_file(path)
			# Create the tabulated format
		else:
			return None
		tabulated_df = fh.create_tabulated_format(data_from_sheets)
		data_table = tabulate(tabulated_df, headers='keys', tablefmt='grid', showindex=False)
		# Print the tabulated DataFrame
		print(data_table)

		return data_from_sheets

	@staticmethod
	def RecipeLoader(data, extmask = None, summary = True, skip = []):
		
		data_from_sheets = data
		
		# Print the extracted data
		for sheet_name, data in data_from_sheets.items():
			#print(f"Data from sheet: {sheet_name}")
			if sheet_name in skip:
				print(f' -- Skipping: {sheet_name}')
				continue
			
			if data['Experiment'] == 'Enabled':
				
				print(f'-- Executing {sheet_name} --')
				
				for field, value in data.items():
					print(f"{field}: {value}")
				
				print("\n") 

				Framework.RecipeExecutor(data=data, extmask=extmask, summary=summary)
			
	@staticmethod
	def Test_Macros_UI(root=None, data=None):
		
		ser.run_ttl(root, data)
	
	@staticmethod
	def TTL_Test(visual, cmds, bucket = 'Dummy', test = 'TTL Macro Validation', chkcore=None, ttime = 30, tnum = 1, content='Dragon', host = '192.168.0.2', PassString = 'Test Complete', FailString = 'Test Failed', cancel_flag=None):
		qdf = dpm.qdf_str()
		ser.start(visual=visual, qdf=qdf, bucket=bucket, content = content, chkcore=chkcore, host = host, cmds=cmds, test=test, ttime=ttime, tnum=tnum, PassString = PassString, FailString = FailString , cancel_flag= cancel_flag)

	@staticmethod
	def reboot_unit(waittime=60, u600w=False, wait_postcode= False):
		
		if not u600w: 
			dpm.powercycle(ports=[1])
		else:
			dpm.powercycle(ports=[1])
			time.sleep(waittime)
			dpm.reset_600w()
		
		if wait_postcode:
			time.sleep(waittime)
			gcm._wait_for_post(gcm.EFI_POST, sleeptime=waittime)
			gcm.svStatus(refresh=True)			

	@staticmethod
	def power_control(state = 'on', stime = 10):
		
		if state == 'on':
			dpm.power_on(ports = [1])
		elif state == 'off':
			dpm.power_off(ports = [1])
		elif state == 'cycle':
			dpm.powercycle(stime = stime, ports = [1])
		else:
			print(' -- No valid power configuration selected use: on, off or cycle')

	@staticmethod
	def power_status():
		try:
			on_status = dpm.power_status()
		except:
			print('Not able to determine power status, setting it as off by default.')
			on_status = False
		
		return on_status

	@staticmethod
	def refresh_ipc():
		try:
			gcm.svStatus(refresh=True)
		except:
			print('Not able refresh SV and Unlock IPC. Issues with your system..')

	@staticmethod
	def warm_reset(waittime=60, wait_postcode= False):
		try:
			dpm.warm_reset()

		except:
			print('Failed while performing a warm reset...')
		
		if wait_postcode:
			time.sleep(waittime)
			gcm._wait_for_post(gcm.EFI_POST, sleeptime=waittime)
			gcm.svStatus(refresh=True)

def Sweep(name = 'Sweep', tnumber = 1, content = 'Dragon', ttype = 'frequency', domain = 'ia', visual = '-9999999', bucket = 'UNCORE',	coreslice = None, 
			fastboot = True, start = 16, end = 39, step= 4, volt_type= 'vbump', volt_IA = None,	volt_CFC = None, freq_ia = None, freq_cfc =None, mask='RowPass1', 
			target = 'mesh', pseudo=True, dis2CPM=True, corelic=None, ttime=30, reset= True, resetonpass=False,	extMask=None, u600w=False, summary = True,
			host = "10.250.0.2", com_port = '8', script_file = None, macro_files = None):
	
	DebugFramework = Framework(
					name = name,
				 	tnumber = tnumber,
				 	content= content,
				 	visual = visual,
				 	qdf = dpm.qdf_str(),
				 	bucket = bucket,
				 	macro_files = macro_files,
				 	coreslice = coreslice,
				 	fastboot = fastboot,
					postcode_break = None,
				 	target = target,
				 	mask = mask,
				 	pseudo = pseudo,
				 	dis2CPM = dis2CPM, 
				 	corelic = corelic, 
				 	ttime = ttime,  
				 	reset = reset, 
				 	resetonpass= resetonpass, 
				 	extMask = extMask, 
				 	u600w = u600w, 
				 	summary = summary,
				 	host = host,
				 	com_port = com_port,
				 	script_file = script_file,
					passstring = 'Test Complete',
					failstring = 'Test Failed',
					)
	
	DebugFramework.Sweep(ttype=ttype, domain=domain, start=start, end=end, step=step, volt_type=volt_type, volt_IA=volt_IA, volt_CFC=volt_CFC,freq_ia=freq_ia, freq_cfc=freq_cfc)

def Loops(name = 'Loops', tnumber = 1, content = 'Dragon', loops = 5, visual = '-9999999', bucket = 'UNCORE', coreslice = None, fastboot = True, volt_type= 'bumps', 
			volt_IA = None, volt_CFC = None, freq_ia=None, freq_cfc=None, mask='RowPass1', target = 'mesh',	pseudo=True, dis2CPM=True, corelic=None, ttime=30,  
			reset= True, resetonpass=False,	extMask=None, u600w=False, summary = True, host = "10.250.0.2",	com_port = '8', script_file = None, macro_files = None):


	DebugFramework = Framework(
					name = name,
				 	tnumber = tnumber,
				 	content= content,
				 	visual = visual,
				 	qdf = dpm.qdf_str(),
				 	bucket = bucket,
				 	macro_files = macro_files,
				 	coreslice = coreslice,
				 	fastboot = fastboot,
					postcode_break = None,
				 	target = target,
				 	mask = mask,
				 	pseudo = pseudo,
				 	dis2CPM = dis2CPM, 
				 	corelic = corelic, 
				 	ttime = ttime,  
				 	reset = reset, 
				 	resetonpass= resetonpass, 
				 	extMask = extMask, 
				 	u600w = u600w, 
				 	summary = summary,
				 	host = host,
				 	com_port = com_port,
				 	script_file = script_file,
					passstring = 'Test Complete',
					failstring = 'Test Failed',
					)
	
	DebugFramework.Loops(loops=loops, volt_type=volt_type, volt_IA=volt_IA, volt_CFC=volt_CFC,freq_ia=freq_ia, freq_cfc=freq_cfc)

def Shmoo(name = 'Shmoo', tnumber = 1, content = 'Dragon', visual = '-9999999', bucket = 'UNCORE', coreslice = None, fastboot = True, target = 'mesh', ttime = 30, 
			pseudo=False, dis2CPM=True, mask=None, file=r'C:\Temp\ShmooData.json', label='COREFIX', reset= True, resetonpass=False, corelic=None, extMask=None,
			u600w=False, summary = True, host = "10.250.0.2", com_port = '8', script_file = None, macro_files = None):

	DebugFramework = Framework(
					name = name,
				 	tnumber = tnumber,
				 	content= content,
				 	visual = visual,
				 	qdf = dpm.qdf_str(),
				 	bucket = bucket,
				 	macro_files = macro_files,
				 	coreslice = coreslice,
				 	fastboot = fastboot,
					postcode_break = None,
				 	target = target,
				 	mask = mask,
				 	pseudo = pseudo,
				 	dis2CPM = dis2CPM, 
				 	corelic = corelic, 
				 	ttime = ttime,  
				 	reset = reset, 
				 	resetonpass= resetonpass, 
				 	extMask = extMask, 
				 	u600w = u600w, 
				 	summary = summary,
				 	host = host,
				 	com_port = com_port,
				 	script_file = script_file,
					passstring = 'Test Complete',
					failstring = 'Test Failed',
					)
	
	DebugFramework.Shmoo(file=file, label=label)

def Recipes(path=r'C:\Temp\DebugFrameworkTemplate.xlsx'):
	
	data_from_sheets = Framework.Recipes(path)

	return data_from_sheets

def RecipeLoader(data, extmask = None, summary = True, skip = []):
	
	Framework.RecipeLoader(data, extmask, summary, skip)

def ControlPanel():
	fcp.run(Framework)

def TTLMacroTest():
	Framework.Test_Macros_UI()

def DebugMask():
	#masks, array = gcm.CheckMasks(readfuse = True, extMasks=None)
	die = dpm.product_str()
	masks = dpm.fuses(rdFuses = True, sktnum =[0], printFuse=False)

	# Checks for all configurations, the dpm fuses will return None if that die is non existing on the system product

	compute0_core_hex = str(masks["ia_compute_0"]) if masks["ia_compute_0"] != None else None
	compute0_cha_hex = str(masks["llc_compute_0"]) if masks["llc_compute_0"] != None else None
	compute1_core_hex = str(masks["ia_compute_1"]) if masks["ia_compute_1"] != None else None
	compute1_cha_hex = str(masks["llc_compute_1"]) if masks["llc_compute_1"] != None else None
	compute2_core_hex = str(masks["ia_compute_2"]) if masks["ia_compute_2"] != None else None
	compute2_cha_hex = str(masks["llc_compute_2"]) if masks["llc_compute_2"] != None else None

	editor = gme.SystemMaskEditor(compute0_core_hex, compute0_cha_hex, compute1_core_hex, compute1_cha_hex, compute2_core_hex, compute2_cha_hex, product = die.upper())
	newmask = editor.start()
	return newmask

def currentTime():
	# Define the GMT-6 timezone
	gmt_minus_6 = pytz.timezone('Etc/GMT+6')

	# Get the current time in GMT-6
	current_time_gmt_minus_6 = datetime.now(gmt_minus_6)

	# Print the current time in GMT-6
	print("Current time in GMT-6:", current_time_gmt_minus_6.strftime('%Y-%m-%d %H:%M:%S'))

	return current_time_gmt_minus_6

## Init conditions, creates required folder and files
initscript()



