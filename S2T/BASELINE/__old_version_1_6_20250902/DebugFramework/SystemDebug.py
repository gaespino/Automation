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
import colorama
from colorama import Fore, Style, Back
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
#try:
#	import users.gaespino.dev.DebugFramework.Storage_Handler.DBHandler as db
#	importlib.reload(db)
#	DATABASE_HANDLER_READY = True
#except Exception as e:
#	print(f' Unable to import Database Handler with Exception: {e}')
#	DATABASE_HANDLER_READY = False


## Folders
script_dir = os.path.dirname(os.path.abspath(__file__))
base_folder = 'C:\\SystemDebug'
ttl_source = os.path.join(script_dir, 'TTL')
shmoos_source = os.path.join(script_dir, 'Shmoos')
ttl_dest = os.path.join(base_folder, 'TTL')
shmoos_dest = os.path.join(base_folder, 'Shmoos')
logs_dest = os.path.join(base_folder, 'Logs')


PYTHONSV_CONSOLE_LOG = r"C:\Temp\PythonSVLog.log"

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
				 macro_folder: str = None,
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
				 failstring: str = 'Test Failed',
				 data_bin: str = None,
				 data_bin_desc: str = None,
				 program: str = None,):

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
		self.macro_folder = macro_folder
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

		# MIDAS Data -- Updated from Framework

		self.data_bin = data_bin
		self.data_bin_desc = data_bin_desc
		self.program = program

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
					'MacroFolder':self.macro_folder,
					'TestFolder':self.tfolder,
					'LogFile':self.log_file_path,
					'Mesh':self.Mesh,
					'Slice':self.Slice,
					'FastBoot':self.fastboot,
					'CoreLicense': self.corelic,
					'ExternalMask': self.extMask,
					'u600w': self.u600w,
					'data_bin':self.data_bin,
					'data_bin_desc':self.data_bin_desc,
					'program':self.program,
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
		self.pysvconsole_path = PYTHONSV_CONSOLE_LOG
		self.pythonlogger = 'script' # Will default this to embed for bootbreaks and pysvconsole
		self.log_file = Experiment.log_file
		self.script_file = Experiment.script_file
		self.scratchpad = ''
		self.host = Experiment.host
		self.com_port = Experiment.com_port
		self.running_iteration = 1
		self.running_test = None
		self.runStatus = None
		self.runStatusHistory=[]
		self.runName = None
		self.boot_postcode = False

		# Loggers Init
		self.pylog = None
		self.gdflog = None

		# Test Status Tracker  :: None is an init State :: False means failed :: True means success
		self.TestStatus = None
		self.Success = 'Success'
		self.Started = 'Started'
		self.Cancelled = 'Cancelled'
		self.Failed = 'Failed'

		#print(data)
		#print(experiment)
		#print(voltage)
		#print(frequency)
		# Initialize logging
		#self.gdflog = fh.printlog(self.log_file)
		self.updatevars()
		self.initlog()
		self.initPythonlog()

		self.system_to_tester_configuration()

	def system_to_tester_configuration(self):

		self.Debuglog(' >>> System to Tester Boot Parameters -- ')
		self.Debuglog(f'\tBootscript retries: {gcm.BOOTSCRIPT_RETRY_TIMES}')
		self.Debuglog(f'\tBootscript retry PC delay: {gcm.BOOTSCRIPT_RETRY_DELAY}')
		self.Debuglog(f'\tEFI Postcode: {gcm.EFI_POST}')
		self.Debuglog(f'\tEFI Postcode Waittime: {gcm.EFI_POSTCODE_WT}')
		self.Debuglog(f'\tEFI Postcode checks count: {gcm.EFI_POSTCODE_CHECK_COUNT}')
		self.Debuglog(f'\tOTHER Postcode: {gcm.LINUX_POST}')
		self.Debuglog(f'\tMRC Postcode: {gcm.AFTER_MRC_POST}')
		self.Debuglog(f'\tMRC Postcode Waittime: {gcm.MRC_POSTCODE_WT}')		
		self.Debuglog(f'\tMRC Postcode checks count: {gcm.MRC_POSTCODE_CHECK_COUNT}')	
		self.Debuglog(f'\tBoot Break Postcode: {gcm.BOOT_STOP_POSTCODE}')	
		self.Debuglog(f'\tBoot Break Waittimet: {gcm.BOOT_POSTCODE_WT}')	
		self.Debuglog(f'\tBoot Break checks count: {gcm.BOOT_POSTCODE_CHECK_COUNT}')	

	def initlog(self):
		self.gdflog = fh.FrameworkLogger(self.log_file, 'FrameworkLogger', console_output=True)

	def initPythonlog(self):
		self.pylog = fh.FrameworkLogger(self.pysvconsole_path, 'PythonSVLogger', pythonconsole=True)
		
		# This is basically to be sure all is reset back in some way
		self.stop_python_log()

	def start_python_log(self, file_mode = 'w'):
		if self.pythonlogger == 'embed':
			log(self.pysvconsole_path, 'w')
		else:
			if self.pylog:
				self.pylog.start_capture(file_mode)

	def stop_python_log(self):
		if self.pythonlogger == 'embed':
			nolog()
		else:
			if self.pylog:
				self.pylog.stop_capture()


	def Debuglog(self, message, event_type=1): #console_show= True, event_type=0):

		self.gdflog.log(message, event_type)
		
	def updatevars(self):

		## Collect Data from data dictionary
		self.visual = self.data.get('Visual')
		self.data_bin = self.data.get('data_bin')
		self.data_bin_desc = self.data.get('data_bin_desc')
		self.program = self.data.get('program')
		self.qdf = self.data.get('QDF')
		self.bucket = self.data.get('Bucket')
		self.macro_files =  self.data.get('MacroFile')
		self.macro_folder =  self.data.get('MacroFolder')
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
		
		# Initialize Color settings
		colorama.init()
		self.TestStatus = self.Started
		# Cancel Flag Check
		self.check_user_cancel()
		
		# Test Code Initialization
		self.TestBanner()
		ser.kill_process(process_name = 'ttermpro.exe', logger = self.Debuglog)
		boot_logging = False

		## Build variables for log and string data
		vbumps = True if self.voltIA != None or self.voltCFC != None else False
		
		if self.content == 'BootBreaks':
			self.boot_postcode = True
			boot_logging = True
			self.pythonlogger = 'embed'
		
		if self.content == 'PYSVConsole':
			self.pythonlogger = 'embed'

		vtstring = self.tnamestr('_vcfg_',self.bumps) if vbumps else ""
		iaF = self.tnamestr('_ia_f',self.freqIA)
		cfcF = self.tnamestr('_cfc_f',self.freqCFC)
		iavolt = self.tnamestr('_ia_v',self.voltIA if self.bumps != 'ppvc' else 'ppvc' ).replace(".","_")
		cfcvolt = self.tnamestr('_cfc_v',self.voltCFC if self.bumps != 'ppvc' else 'ppvc').replace(".","_")
		mask = self.tnamestr('',self.mask,"System")
		tname = self.tname.strip(' ')
		test = f'{tname}_{mask}{iaF}{cfcF}{vtstring}{iavolt}{cfcvolt}'
		coreslice = self.coreslice
		bootReady = False # This is to indicate a succesfull boot not used for now...
		validPYSVLog = False
		validTTLog = False

		## Setting Serial configuration
		exp_ttl_files_dict = self.ttl_copy() # Copy self.macro_files to the test location
		
		serial = ser.teraterm(visual=self.visual, qdf=self.qdf, bucket=self.bucket, log=self.log_file_path, cmds=exp_ttl_files_dict, tfolder=self.tfolder, test=test, ttime=self.ttime, tnum=self.tnum, DebugLog = self.Debuglog, chkcore = self.coreslice, content = self.content, host = self.host, PassString = self.passstring, FailString = self.failstring, cancel_flag = self.cancel_flag)
		if boot_logging: serial.boot_start()

		
		# Start Capturing PythonSV Console
		#log(self.pysvconsole_path)
		self.start_python_log('w')
		## Calls script for either mesh or slice
		if self.ismesh:

			try: 
				s2t.MeshQuickTest(core_freq = self.freqIA, mesh_freq = self.freqCFC, vbump_core = self.voltIA, vbump_mesh = self.voltCFC, Reset = self.Reset, Mask = self.mask, pseudo = self.htdis, dis_2CPM = self.dis2CPM, GUI = False, fastboot = self.fastboot, corelic = self.corelic, volttype=self.bumps, debug= False, boot_postcode = self.boot_postcode, extMask = self.extMask)
				self.check_user_cancel()
				bootReady = True
			except KeyboardInterrupt:
				self.Debuglog("Script interrupted by user. Exiting...",2)
				self.TestStatus = self.Cancelled
				return None			
			except InterruptedError:
				self.Debuglog("Script interrupted by user. Exiting...",2)
				self.TestStatus = self.Cancelled
				return None
			except SyntaxError as se:
				print(f"Syntax error occurred: {se}")
			except Exception as e: 				
				self.Debuglog(f' Boot Failed with Exception {e} --- Might be an issue with bootscript -- Retrying..... ',4)
				
				if 'RSP 10' in str(e) or 'regaccfail' in str(e):
					self.Debuglog(f' PowerCycling Unit -- RegAcc Fail during previuos Boot',4)
					self.powercycle(u600w = self.u600w, wait_postcode=False)
					time.sleep(120)
					Framework.reconnect_ipc()		
				else:
					self.Debuglog(f' PowerCycling Unit -- ',4)
					self.powercycle(u600w = self.u600w, wait_postcode=True)

				s2t.MeshQuickTest(core_freq = self.freqIA, mesh_freq = self.freqCFC, vbump_core = self.voltIA, vbump_mesh = self.voltCFC, Reset = self.Reset, Mask = self.mask, pseudo = self.htdis, dis_2CPM = self.dis2CPM, GUI = False, fastboot = self.fastboot, corelic = self.corelic, volttype=self.bumps, debug= False, boot_postcode = self.boot_postcode, extMask = self.extMask)
				#self.check_user_cancel()
				bootReady = True
			finally:
				if bootReady: 
					self.Debuglog(' Framework boot process completed.....',1)
					self.TestStatus = self.Success
					
				else: 
					self.Debuglog(' Framework was not able to properly configure the system. Check log for details.....',3)
					if self.TestStatus != self.Cancelled: self.TestStatus = self.Failed

		elif self.isslice:

			try:
				s2t.SliceQuickTest(Target_core = self.mask, core_freq = self.freqIA, mesh_freq = self.freqCFC, vbump_core = self.voltIA, vbump_mesh = self.voltCFC, Reset = self.Reset, pseudo = False, dis_2CPM = self.dis2CPM, GUI = False, fastboot = self.fastboot, corelic = self.corelic, volttype = self.bumps, debug= False, boot_postcode = self.boot_postcode)
				self.check_user_cancel()
				bootReady = True
			except KeyboardInterrupt:
				self.Debuglog("Script interrupted by user. Exiting...",2)
				self.TestStatus = self.Cancelled
				return None		
			except InterruptedError:
				self.Debuglog("Script interrupted by user. Exiting...",2)
				self.TestStatus = self.Cancelled
				return None	
			except SyntaxError as se:
				print(f"Syntax error occurred: {se}")
			except Exception as e: 
				self.Debuglog(f' Boot Failed with Exception {e} --- Might be an issue with bootscript -- Retrying..... ',4)

				if 'RSP 10' in str(e) or 'regaccfail' in str(e):
					self.powercycle(u600w = self.u600w, wait_postcode=False)
					time.sleep(120)
					Framework.reconnect_ipc()		
				else:
					self.powercycle(u600w = self.u600w, wait_postcode=True)

				s2t.SliceQuickTest(Target_core = self.mask, core_freq = self.freqIA, mesh_freq = self.freqCFC, vbump_core = self.voltIA, vbump_mesh = self.voltCFC, Reset = self.Reset, pseudo = False, dis_2CPM = self.dis2CPM, GUI = False, fastboot = self.fastboot, corelic = self.corelic, volttype = self.bumps, debug= False, boot_postcode = self.boot_postcode)
				#self.check_user_cancel()
				bootReady = True
			finally:
				if bootReady: 
					self.Debuglog(' Framework boot process completed.....',1)
					self.TestStatus = self.Success
				else: 
					
					self.Debuglog(' Framework was not able to properly configure the system. Check log for details.....',3)
					if self.TestStatus != self.Cancelled: self.TestStatus = self.Failed



		else:
			self.Debuglog(" --- Not valid type of test, select either mesh or slice",3)
			self.TestStatus = self.Failed

		if self.script_file != None:
			
			if self.content == 'BootBreaks': 	
				self.Debuglog(f" --- Executing Custom script at reached boot Breakpoint: {self.script_file}",1)

			elif self.content == 'PYSVConsole': 				
				self.Debuglog(f" --- Executing Custom script before test: {self.script_file}",1)

			fh.execute_file(file_path = self.script_file, logger = self.Debuglog)
			
			#if self.content == 'PYSVConsole' or self.content == 'BootBreaks': 
			
		# End Capturing PythonSV Console
		#nolog()
		self.stop_python_log()

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

		self.Debuglog(f' -- Test Start --- ')
		self.Debuglog(f' -- Debug Framework {self.tname} --- ')
		self.Debuglog(f' -- Performing test iteration {self.tnum} with the following parameters: ')

		## Get Running Content -- 
		self.running_content()

		## Print Test Summary keys --- 
		
		EMPTY_FIELDS = [None, 'None', '']
		Configured_Mask = self.mask if self.extMask == None else "Custom"
		self.Debuglog(f'\t > Unit VisualID: {self.visual}')
		self.Debuglog(f'\t > PPV Program: {self.program}')
		self.Debuglog(f'\t > PPV Bin: {self.data_bin}')
		self.Debuglog(f'\t > PPV Bin Desc: {self.data_bin_desc}')
		self.Debuglog(f'\t > Unit QDF: {self.qdf}')
		self.Debuglog(f'\t > Configuration: {Configured_Mask if Configured_Mask not in EMPTY_FIELDS else "System Mask"} ')
		if self.corelic: self.Debuglog(f'\t > Core License: {self.corelic} ')
		self.Debuglog(f'\t > Voltage set to: {self.bumps} ')
		self.Debuglog(f'\t > HT Disabled (BigCore): {self.htdis} ')
		self.Debuglog(f'\t > Dis 2 Cores (Atomcore): {self.dis2CPM} ')
		self.Debuglog(f'\t > Core Freq: {self.freqIA} ')
		self.Debuglog(f'\t > Core Voltage: {self.voltIA} ')
		self.Debuglog(f'\t > Mesh Freq: {self.freqCFC} ')
		self.Debuglog(f'\t > Mesh Voltage: {self.voltCFC} ')
		self.Debuglog(f'\t > Running Content: {self.content} ')
		self.Debuglog(f'\t > Pass String: {self.passstring} ')
		self.Debuglog(f'\t > Fail String: {self.failstring} ')

		if self.u600w: self.Debuglog(f'\t > Unit 600w Fuses Applied ')
		if self.extMask != None:
			printmasks = [["Type", "Value"]]
			printmasks.extend([k,v] for k, v in self.extMask.items())
			self.Debuglog(f'\t > Using External Custom Base Mask: ')
			self.Debuglog(f'{printmasks}\n'+ tabulate(printmasks, headers="firstrow", tablefmt="grid"))

	def running_content(self):
		
		if self.ismesh and self.Dragon:
			runtxt = f' -- Running Dragon {"Pseudo " if self.htdis else "Bare Metal"} content --- '
		elif self.isslice and self.Dragon:
			runtxt = f' -- Running Dragon Slice content --- '

		if self.Dragon: 
			self.Debuglog(f'{runtxt}')
			#self._running_content = 'EFI'
		elif self.Linux: 
			self.Debuglog(f' -- Running Linux Content ---') # Need to add more here, stil WIP, working only for Dragon
			#self._running_content = 'Linux'
		elif self.PYSVConsole: 
			#self._running_content = 'Python'
			self.Debuglog(f' -- PYSVConsole Custom Script Run ---')
		elif self.Bootbreaks: 
			#self._running_content = 'Boot'
			self.Debuglog(f' -- Boot Breakpoint Test ---')

	def tnamestr(self,prefix, value, default = ""):
		set_to_default = [None, '', 'None']
		tstr = f'{prefix}{value}' if value not in set_to_default else default
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

	def powercycle(self, u600w, wait_postcode = True):
		waittime = gcm.EFI_POSTCODE_WT

		Framework.reboot_unit(waittime=waittime, u600w=u600w, wait_postcode = wait_postcode)
		#if not u600w: 
		#	dpm.powercycle(ports=[1])
		#else:
		#	dpm.powercycle(ports=[1])
		#	time.sleep(60)
		#	dpm.reset_600w()
		#time.sleep(60)
		#gcm._wait_for_post(gcm.EFI_POST, sleeptime=60)
		#gcm.svStatus(refresh=True)				

	def ttl_copy(self):
		replace = 'Y'
		
		TTLPath = fh.create_path(folder=self.tfolder, file='TTL')
		fh.create_folder_if_not_exists(TTLPath)
		fh.copy_files(self.macro_folder, TTLPath, uinput=replace)
		
		return macros_path(TTLPath)

	## Test Types
	def Sweep(self, domain, ttype, start, end, step):
		self.initlog()
		self.Debuglog(print_custom_separator(f'Starting Sweep  -- {domain.upper()}:{ttype.upper()}'))

		## Reset Fail Status series to hold the current experiment results
		self.runStatusHistory=[]

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
			
			# Checks for current Test Status if something failed -- Exit the loop
			if self.TestStatus != self.Success:
				self.Debuglog(f' -- Sweep Test iteration {self.tnum} Cancelled.... ')
				return None
			
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

			#Save runStatus in series
			self.runStatusHistory.append(self.runStatus)

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

		## Reset Fail Status series to hold the current experiment results
		self.runStatusHistory=[]

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

			# Checks for current Test Status if something failed -- Exit the loop
			if self.TestStatus != self.Success:
				self.Debuglog(f' -- Loop Test iteration {self.tnum} Cancelled.... ')
				return None

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

			#Save runStatus in series
			self.runStatusHistory.append(self.runStatus)

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

		## Reset Fail Status series to hold the current experiment results
		self.runStatusHistory=[]

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

				# Checks for current Test Status if something failed -- Exit the loop
				if self.TestStatus != self.Success:
					self.Debuglog(f' -- Loop Test iteration {self.tnum} Cancelled.... ')
					return None

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

				#Save runStatus in series
				self.runStatusHistory.append(self.runStatus)
				
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
				self.stop_python_log()
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
					upload_to_database: bool = True
					):
		
		self.Experiment_Data = None
		self.Defeature = None
		self.current_iteration = 0
		self.current_test = None
		self.cancel_flag = None
		self.upload_to_database = upload_to_database
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
		self.unit_qdf = None # self.get_qdf()
		self.unit_data = None # self.get_unit_info()

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
								qdf = self.qdf,
								macro_cmds = self.ttl_macros,
								macro_folder = self.macro_files,
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
								failstring = self.failstring,
								data_bin=self.get_data_bin(),
								data_bin_desc=self.get_data_bin_desc(),
								program=self.get_program())
	
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
		WW = str(dpm.getWW())
		product = s2t.SELECTED_PRODUCT

		datahandler = fh.TestUpload(folder=self.Defeature.tfolder, vid=self.visual, name=self.name, bucket=self.bucket, WW=WW, product=product, logger = self.Defeature.Debuglog, from_Framework = True, upload_to_disk=True, upload_to_danta=self.upload_to_database)
		
		# Builds Unit Summary
		if self.summary:
			datahandler.generate_summary()

		# Prints Shmoo data
		self.Defeature.Debuglog(f'{self.Test_Type} Test Results --- \n')
		self.Defeature.Debuglog(shmoodata)
		self.Defeature.Debuglog('\nLegends:')
		self.Defeature.Debuglog(legends)

		datahandler.upload_data()

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
		
		if self.Defeature.TestStatus == self.Defeature.Success:
			# End Flow
			self.end_summary()
			return self.Defeature.runStatusHistory

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
		
		if self.Defeature.TestStatus == self.Defeature.Success:
			# End Flow
			self.end_summary()
			return self.Defeature.runStatusHistory

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
		
		if self.Defeature.TestStatus == self.Defeature.Success:
			# End Flow
			self.end_summary()
			return self.Defeature.runStatusHistory
		
	def get_visual(self):
		if self.unit_data:
			return self.unit_data['VISUAL_ID'][0]
		else:
			return None

	def get_data_bin(self):
		if self.unit_data:
			return self.unit_data['DATA_BIN'][0]
		else:
			return None

	def get_program(self):
		if self.unit_data:
			return self.unit_data['PROGRAM'][0]
		else:
			return None

	def get_qdf(self):
		qdf = dpm.qdf_str()
		self.FrameworkPrint(f" >>> Unit QDF: {qdf}")
		return qdf

	def get_data_bin_desc(self):
		if self.unit_data:
			return self.unit_data['data_bin_desc'][0]
		else:
			return None

	def check_unit_data(self):
		# Data from MIDAS
		visual_id = self.get_visual()
		qdf = self.unit_qdf

		if self.visual != visual_id and visual_id != None:
			self.FrameworkPrint(f" >>> Changing Visual ID to MIDAS collected data: ({self.visual} --> {visual_id})",1)
			self.visual = visual_id

		if self.qdf != qdf and qdf != None:
			self.FrameworkPrint(f" >>> Changing QDF to match fused data: ({self.qdf} --> {qdf})",1)
			self.qdf = qdf

	def update_unit_data(self):

		self.unit_qdf = self.get_qdf()
		self.unit_data = self.get_unit_info()

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

		#if self.qdf == '': self.qdf == dpm.qdf_str()

		self.bucket = data.get('Bucket', 'FRAMEWORK')
		self.ttime = data.get('Test Time', 30)
		self.reset = data.get('Reset', True)
		self.resetonpass = data.get('Reset on PASS', True)
		self.macro_files = data.get('TTL Folder', r'C:\SystemDebug\TTL')
		#self.ttl_version = data.get('TTL Version', '1.0')
		self.coreslice = data.get('Check Core', '')
		self.fastboot = data.get('FastBoot', False)
		self.target = data.get('Test Mode', '').lower()
		self.mask = data.get('Configuration (Mask)', '')
		self.pseudo = data.get('Pseudo Config', False)
		self.dis2CPM = int(data.get('Disable 2 Cores', None),16) if (data.get('Disable 2 Cores', None) != None) else None 
		self.corelic = int(data.get('Core License',None).split(":")[0]) if (data.get('Core License',None) != None) else None
		self.extMask = extmask if extmask != None else data.get('External Mask',None)
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

		# Updates System to Tester Configurations
		self.update_system_to_tester_config(S2T_BOOT_CONFIG)		 
		self.TTL_parse(self.macro_files)
		
		# Check Visual ID based on Midas data
		self.check_unit_data()
		self.FrameworkPrint(f" --- Starting Framework Execution for VID: {self.visual} :: QDF: {self.qdf}",1)

		runStatusHistory=None		
		
		if data['Test Type'] == 'Loops':				
			self.FrameworkPrint(f" >>>  Experiment will run a total of {data['Loops']} loops",1)

			runStatusHistory=self.Loops(	
							loops = data['Loops'], 
							volt_type= data['Voltage Type'].lower(), 
							volt_IA = data['Voltage IA'], 
							volt_CFC = data['Voltage CFC'],
							freq_ia= data['Frequency IA'], 
							freq_cfc = data['Frequency CFC'], 
						)
					
		elif data['Test Type'] == 'Sweep':	
			self.FrameworkPrint(f" >>>  Experiment will run a {data['Domain'].upper()}::{data['Type'].upper()} Sweep",1)

			runStatusHistory=self.Sweep(	
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
			self.FrameworkPrint(f" >>>  Experiment will run a Shmoo from file:{data['ShmooFile']} -- Label:{data['ShmooLabel']}",1)

			runStatusHistory=self.Shmoo(	
							file=data['ShmooFile'], 
							label=data['ShmooLabel'], 
							
							)

		# Returns Configuration to default values
		self.update_system_to_tester_config(self.system_2_tester_default())
		gcm.cancel_flag = None
		return runStatusHistory

	####################################################################################################################
	############################################	Framework Functions Below	########################################
	####################################################################################################################
	@staticmethod
	def FrameworkPrint(text, level = None):

		'''Levels
			Level 0 -> Debugging
			Level 1 -> Information
			Level 2 -> Error Critical '''	
		
		RESET_COLOR = Fore.WHITE

		if level == 0:
			COLOR = Fore.YELLOW
		elif level == 1:
			COLOR = Fore.GREEN
		elif level ==2:
			COLOR = Fore.RED
		else:
			COLOR = Fore.WHITE	

		print(COLOR + text + RESET_COLOR)

	@staticmethod
	def platform_check(com_port, ip_address):

		#com_port = self.com_port
		#ip_address = self.host
		TERATERM_PATH = ser.TERATERM_PATH
		TERATERM_RVP_PATH = ser.TERATERM_RVP_PATH
		TERATERM_INI_FILE = ser.TERATERM_INI_FILE

		fh.teraterm_check(com_port=com_port, ip_address=ip_address, teraterm_path = TERATERM_PATH, seteo_h_path = TERATERM_RVP_PATH, ini_file = TERATERM_INI_FILE, useparser=False, checkenv=True)

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
	def RecipeLoader(data, extmask = None, summary = True, skip = [], upload_to_database=True):
		
		data_from_sheets = data
		fprint = Framework.FrameworkPrint
		ExperimentFlow = Framework(upload_to_database=upload_to_database)
		ExperimentFlow.update_unit_data()

		# Print the extracted data
		for sheet_name, data in data_from_sheets.items():
			#print(f"Data from sheet: {sheet_name}")
			if sheet_name in skip:
				fprint(f' -- Skipping: {sheet_name}',0)
				continue
			
			if data['Experiment'] == 'Enabled':
				
				fprint(f'-- Executing {sheet_name} --',1)
				
				for field, value in data.items():
					fprint(f"{field} :: {value}",1)
				
				fprint("\n",1) 
				
				# Loading Class before the loop
				ExperimentFlow.RecipeExecutor(data=data, extmask=extmask, summary=summary)
			
	@staticmethod
	def Test_Macros_UI(root=None, data=None):
		
		ser.run_ttl(root, data)
	
	@staticmethod
	def TTL_Test(visual, cmds, bucket = 'Dummy', test = 'TTL Macro Validation', chkcore=None, ttime = 30, tnum = 1, content='Dragon', host = '192.168.0.2', PassString = 'Test Complete', FailString = 'Test Failed', cancel_flag=None):
		qdf = dpm.qdf_str()
		
		ser.start(visual=visual, qdf=qdf, bucket=bucket, content = content, chkcore=chkcore, host = host, cmds=cmds, test=test, ttime=ttime, tnum=tnum, PassString = PassString, FailString = FailString , cancel_flag= cancel_flag)

	@staticmethod
	def TTL_parse(folder): # 2.0 TTL parsing method
		config_file = fh.create_path(folder, 'config.ini')
		logger = Framework.FrameworkPrint
		converter = fh.FrameworkConfigConverter(config_file, logger=logger)
		if converter.read_ini():
			converter.create_current_flow_csv(folder)
			
			logger(' -- TTL Test Configuration -- ')
			config_data = converter.get_flow_config_data()
			table_data = [[key, value] for key, value in config_data.items()]
			#tabulated_df = fh.create_tabulated_format(converter.config)
			data_table = tabulate(table_data, headers=["Parameter", "Value"], tablefmt="grid")
			logger(data_table)

	@staticmethod
	def get_unit_info():
		
		return dpm.request_unit_info()

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
		fprint = Framework.FrameworkPrint
		if state == 'on':
			dpm.power_on(ports = [1])
		elif state == 'off':
			dpm.power_off(ports = [1])
		elif state == 'cycle':
			dpm.powercycle(stime = stime, ports = [1])
		else:
			fprint(' -- No valid power configuration selected use: on, off or cycle',2)

	@staticmethod
	def power_status():
		fprint = Framework.FrameworkPrint
		try:
			on_status = dpm.power_status()
		except:
			fprint('Not able to determine power status, setting it as off by default.',2)
			on_status = False
		
		return on_status

	@staticmethod
	def refresh_ipc():
		fprint = Framework.FrameworkPrint
		try:
			gcm.svStatus(refresh=True)
		except:
			fprint('!!! Unable to refresh SV and Unlock IPC. Issues with your system..',2)

	@staticmethod
	def reconnect_ipc():
		fprint = Framework.FrameworkPrint
		try:
			gcm.svStatus(checkipc = True, checksvcores = False, refresh = False, reconnect = True)
		except:
			fprint('!!! Unable to execute ipc reconnect operation, check your system ipc connection status...',2)

	@staticmethod
	def warm_reset(waittime=60, wait_postcode= False):
		fprint = Framework.FrameworkPrint
		try:
			dpm.warm_reset()

		except:
			fprint('Failed while performing a warm reset...',2)
		
		if wait_postcode:
			time.sleep(waittime)
			gcm._wait_for_post(gcm.EFI_POST, sleeptime=waittime)
			gcm.svStatus(refresh=True)

	@staticmethod
	def Masks(basemask=None, root = None, callback = None):
		NEW_MASK = DebugMask(basemask, root, callback)
		return NEW_MASK
	
	@staticmethod
	def read_current_mask():
		masks = dpm.fuses(rdFuses = True, sktnum =[0], printFuse=False)
		return masks

## Moved to FileHandler
#	@staticmethod
#	def manual_upload(tfolder  : str = None, visual : str = None, UPLOAD_TO_DISK  : bool = True, UPLOAD_DATA : bool = True, logger : function  = None):
#		console_logger = Framework.FrameworkPrint if logger == None else logger
#		Product = s2t.SELECTED_PRODUCT
#
#		fh.manual_upload(tfolder = tfolder, visual = visual, Product = Product, UPLOAD_TO_DISK = UPLOAD_TO_DISK, UPLOAD_DATA = UPLOAD_DATA, logger = console_logger)

#	@staticmethod
#	def generate_summary(visual : str = '', bucket : str = '', name : str = '', tfolder : str = '', logger : function = None):
#
#		logger == Framework.FrameworkPrint if logger == None else logger
#		WW = str(dpm.getWW())
#		Product = s2t.SELECTED_PRODUCT
#
#		fh.manual_summary(visual, bucket, name, WW, Product, tfolder, logger = None)
	
#	@staticmethod
#	def search_exp_name(tfolder, logname = 'DebugFrameworkLogger.log'):
#		file = fh.create_path(tfolder, logname)
#		return fh.find_name_regex(file, pattern=r"-- Debug Framework (\w+) ---")


#######################################################
########## 		Quick Access Framework Functions
#######################################################

def Sweep(name = 'Sweep', tnumber = 1, content = 'Dragon', ttype = 'frequency', domain = 'ia', visual = '-9999999', bucket = 'UNCORE',	coreslice = None, 
			fastboot = True, start = 16, end = 39, step= 4, volt_type= 'vbump', volt_IA = None,	volt_CFC = None, freq_ia = None, freq_cfc =None, mask='RowPass1', 
			target = 'mesh', pseudo=True, dis2CPM=True, corelic=None, ttime=30, reset= True, resetonpass=False,	extMask=None, u600w=False, summary = True,
			host = "10.250.0.2", com_port = '8', script_file = None, macro_files = None, upload_to_database=True):
	
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
					upload_to_database=upload_to_database
					)
	
	DebugFramework.Sweep(ttype=ttype, domain=domain, start=start, end=end, step=step, volt_type=volt_type, volt_IA=volt_IA, volt_CFC=volt_CFC,freq_ia=freq_ia, freq_cfc=freq_cfc)

def Loops(name = 'Loops', tnumber = 1, content = 'Dragon', loops = 5, visual = '-9999999', bucket = 'UNCORE', coreslice = None, fastboot = True, volt_type= 'bumps', 
			volt_IA = None, volt_CFC = None, freq_ia=None, freq_cfc=None, mask='RowPass1', target = 'mesh',	pseudo=True, dis2CPM=True, corelic=None, ttime=30,  
			reset= True, resetonpass=False,	extMask=None, u600w=False, summary = True, host = "10.250.0.2",	com_port = '8', script_file = None, macro_files = None,
			upload_to_database=True):


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
					upload_to_database=upload_to_database
					)
	
	DebugFramework.Loops(loops=loops, volt_type=volt_type, volt_IA=volt_IA, volt_CFC=volt_CFC,freq_ia=freq_ia, freq_cfc=freq_cfc)

def Shmoo(name = 'Shmoo', tnumber = 1, content = 'Dragon', visual = '-9999999', bucket = 'UNCORE', coreslice = None, fastboot = True, target = 'mesh', ttime = 30, 
			pseudo=False, dis2CPM=True, mask=None, file=r'C:\Temp\ShmooData.json', label='COREFIX', reset= True, resetonpass=False, corelic=None, extMask=None,
			u600w=False, summary = True, host = "10.250.0.2", com_port = '8', script_file = None, macro_files = None,upload_to_database=True):

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
					upload_to_database=upload_to_database
					)
	
	DebugFramework.Shmoo(file=file, label=label)

def Recipes(path=r'C:\Temp\DebugFrameworkTemplate.xlsx'):
	
	data_from_sheets = Framework.Recipes(path)

	return data_from_sheets

def RecipeLoader(data, extmask = None, summary = True, skip = [], upload_to_database=True):
	
	Framework.RecipeLoader(data, extmask, summary, skip, upload_to_database)

#######################################################
########## 		User Interface Calls
#######################################################

def ControlPanel():
	fcp.run(Framework)

def TTLMacroTest():
	Framework.Test_Macros_UI()

#######################################################
########## 		Masking Script 
#######################################################

def DebugMask(basemask=None, root=None, callback = None):

	#masks, array = gcm.CheckMasks(readfuse = True, extMasks=None)
	die = dpm.product_str()
	masks = dpm.fuses(rdFuses = True, sktnum =[0], printFuse=False) if basemask == None else basemask

	# Checks for all configurations, the dpm fuses will return None if that die is non existing on the system product

	compute0_core_hex = str(masks["ia_compute_0"]) if masks["ia_compute_0"] != None else None
	compute0_cha_hex = str(masks["llc_compute_0"]) if masks["llc_compute_0"] != None else None
	compute1_core_hex = str(masks["ia_compute_1"]) if masks["ia_compute_1"] != None else None
	compute1_cha_hex = str(masks["llc_compute_1"]) if masks["llc_compute_1"] != None else None
	compute2_core_hex = str(masks["ia_compute_2"]) if masks["ia_compute_2"] != None else None
	compute2_cha_hex = str(masks["llc_compute_2"]) if masks["llc_compute_2"] != None else None

	newmask = gme.Masking(root, compute0_core_hex, compute0_cha_hex, compute1_core_hex, compute1_cha_hex, compute2_core_hex, compute2_cha_hex, product = die.upper(), callback=callback)
	#editor = gme.SystemMaskEditor(compute0_core_hex, compute0_cha_hex, compute1_core_hex, compute1_cha_hex, compute2_core_hex, compute2_cha_hex, product = die.upper())
	#newmask = editor.start()

	return newmask

def currentTime():
	# Define the GMT-6 timezone
	gmt_minus_6 = pytz.timezone('Etc/GMT+6')

	# Get the current time in GMT-6
	current_time_gmt_minus_6 = datetime.now(gmt_minus_6)

	# Print the current time in GMT-6
	print("Current time in GMT-6:", current_time_gmt_minus_6.strftime('%Y-%m-%d %H:%M:%S'))

	return current_time_gmt_minus_6

#######################################################
########## 		Initialization
#######################################################

initscript()



