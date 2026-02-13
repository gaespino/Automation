import time
import os
import subprocess
import threading


try:
	import users.gaespino.dev.S2T.Logger.ErrorReport as ereport
	import users.gaespino.dev.S2T.dpmChecks as dpm
	import users.gaespino.dev.DebugFramework.UI.Serial as ttl
except:
	print('Failed to import important libraries')

try:
	import users.THR.PythonScripts.thr.CWFCoreDebugUtils as gcd
except:
	#print('Not able to import important libraries')
	#import users.THR.PythonScripts.thr.GNRCoreDebugUtils as gcd
	import users.THR.dmr_debug_utilities.DMRCoreDebugUtils as gcd


# TEST MODE
USE_TEST_MODE_S2T = True

# Run Tera Term macros
macrospath = r'C:\PythonSV\graniterapids\users\gaespino\DebugFramework\TTL'
macro_files = {
	'Disconnect': rf'{macrospath}\disconnect.ttl',
	'Connect': rf'{macrospath}\connect.ttl',
	'StartCapture':  rf'{macrospath}\Boot.ttl',
	'StartTest': rf'{macrospath}\Commands.ttl',
	'StopCapture':  rf'{macrospath}\stop_capture.ttl'
}

log_file_path = r'C:\Temp\capture.log'
tfolder = r'C:\Temp'

TERATERM_PATH = r'C:\teraterm'
TERATERM_MACRO_PATH = os.path.join(TERATERM_PATH, 'ttermpro.exe')
TERATERM_RVP_PATH =  r"C:\SETEO H"
TERATERM_INI_FILE = "TERATERM.INI"


class teraterm():

	def __init__(self, visual, qdf, bucket, log, cmds, tfolder, test, ttime, tnum, DebugLog, chkcore=None, content='Dragon', host = None, PassString = 'Test Complete', FailString = 'Test Failed', cancel_flag = None, execution_state = None):

		self.logfile = log
		#self.ttpath = ttpath
		self.cmds = cmds
		#print(cmds)
		self.ttendw = [s.strip() for s in PassString.split(",")] #PassString ## Test Succes Word
		self.ttendfail = [s.strip() for s in FailString.split(",")] #FailString ## Test FAIL Word
		self.test = test # This will change the variable to be used
		self.testtime = ttime
		self.tnum = tnum
		self.vid = visual
		self.qdf = qdf
		self.bucket = bucket
		self.tfolder = tfolder
		self.Ttlwinname = r'FRAMEWORK - Tera Term VT'
		self.testresult = None
		self.terminate = threading.Event()
		self.terminate_boot_log = threading.Event()
		self.chkcore = chkcore
		self.scratchpad = ''
		self.DebugLog = DebugLog
		self.content = content
		self.host = host
		self.product = dpm.SELECTED_PRODUCT
		self.cancel_flag = cancel_flag
		self.execution_state = execution_state

		# DR Data being collected by default
		self.dr_dump = True

	def get_last_line(self):
		with open(self.logfile, 'r') as file:
			lines = file.readlines()
			if lines:
				return lines[-1].strip(), lines
			return None, None

	def search_in_file(self, lines, string = [], casesens = False, search_up_to_line = 10, reverse=True):

		if not lines:
			return None

		search_lines = list(reversed(lines)) if reverse else lines
		search_lines = search_lines[:search_up_to_line]
		for line in (search_lines[:search_up_to_line]):
			# Search for Pass String in lines
			for search_string in string:
				if (search_string in line) if casesens else (search_string.lower() in line.lower()):
					return True

		return False

	def selfcheck(self):
		# Check log file init vars
		last_line = None
		unchanged_checks = 0
		endcount = 0
		tstPass = False
		time.sleep(30)

		if self.content == 'Dragon': tstPass = self.eficheck(last_line, unchanged_checks, endcount)
		elif self.content == 'Linux': tstPass = self.linuxcheck(last_line, unchanged_checks, endcount)
		elif self.content == 'PYSVConsole': tstPass = self.pysvcheck()
		elif self.content == 'BootBreaks': tstPass = self.pysvcheck()
		else: self.DebugLog("No valid content option selected... ")

		return tstPass

	def pysvcheck(self):
		self.DebugLog("Starting PythonSV Self Check Process ....")
		mce = self.mca_checker()
		return not mce

	def eficheck(self, last_line = None, unchanged_checks = 0, endcount = 0):
		self.DebugLog("Starting EFI Self Check Process ....")
		prevlines = 0
		## Check Loop increase ttime based on your current content time
		while True:
			self.check_user_cancel()
			try:
				current_last_line, total_lines = self.get_last_line()
			except:
				self.DebugLog("Failed reading Teraterm data log")
				return False
			if total_lines == None:
				self.DebugLog("Failed reading Teraterm data log")
				return False

			numlines = len(total_lines)# if total_lines != None else 0

			# Function to collect Core Data if configured
			self.get_core_data()

			if current_last_line == last_line and prevlines == numlines:
				unchanged_checks += 1

			else:
				unchanged_checks = 0
				last_line = current_last_line

			if unchanged_checks >= 10:
				self.DebugLog("Console FAIL")
				return False
				#break

			if unchanged_checks >= 5:
				mce = self.mca_checker()
				if mce:
					return False
				if self.search_in_file(lines=total_lines, string=self.ttendfail, casesens=False, search_up_to_line=10, reverse=True):
					return False

			if r'fs1:\efi\>' in current_last_line.lower() and numlines >= 2:
				previousline = total_lines[numlines-2]
				self.DebugLog(f'Last line {-1} --times:{endcount} --> {previousline}', 1)
				endcount += 1
				mce = False

				if any(pass_str.lower() in previousline.lower() for pass_str in self.ttendw) and endcount > 5:
					self.DebugLog("Test Finished Succesfully")
					return True

				if any(fail_str.lower() in previousline.lower() for fail_str in self.ttendfail):
					self.DebugLog("Test Failed -- Errors detected")
					return False

				if endcount > 5:
					mce = self.mca_checker()

				if mce:
					self.DebugLog("MCE Founds -- Ending Test")
					return False

				if self.search_in_file(lines=total_lines, string=self.ttendfail, casesens=False, search_up_to_line=10, reverse=True):
					self.DebugLog("Test Failed -- Errors detected")
					return False

				if self.search_in_file(lines=total_lines, string=self.ttendw, casesens=False, search_up_to_line=10, reverse=True):
					self.DebugLog("Test Finished Succesfully")
					return True

			else:
				endcount = 0

			if any(fail_str.lower() in current_last_line.lower() for fail_str in self.ttendfail):
				self.DebugLog("Test Failed -- Errors detected")
				return False
				#break

			if any(pass_str.lower() in current_last_line.lower() for pass_str in self.ttendw):
				# Last MCE Check before passing test
				mce = self.mca_checker()
				if mce:
					self.DebugLog("MCE Founds at the end of Test")
					return False

				self.DebugLog("Test Finished Succesfully")
				return True

			prevlines = numlines
			time.sleep(self.testtime)

	def linuxcheck(self, last_line = None, unchanged_checks = 0, endcount = 0):
		self.DebugLog("Starting Linux OS Self Check Process ....")
		prevlines = 0
		## Check Loop increase ttime based on your current content time
		while True:
			self.check_user_cancel()
			try:
				current_last_line, total_lines = self.get_last_line()
			except:
				self.DebugLog("Failed reading Teraterm data log")
				return False
			if total_lines == None:
				self.DebugLog("Failed reading Teraterm data log")
				return False

			numlines = len(total_lines)# if total_lines != None else 0

			# Function to collect Core Data if configured
			self.get_core_data()

			# Ping Host to ensure connection is alive
			wdtimer = self.ping_host(host=self.host, retries=10, interval=self.testtime)


			if current_last_line == last_line and prevlines == numlines:
				self.DebugLog(f'Log Last line not moving -- {last_line} -- Count:{unchanged_checks}')
				unchanged_checks += 1

			else:
				unchanged_checks = 0
				last_line = current_last_line

			if not wdtimer:
				self.DebugLog("Console FAIL")
				return False
				#break

			if unchanged_checks >= 10:
				mce = self.mca_checker()
				if mce:
					return False
				if self.search_in_file(lines=total_lines, string=self.ttendfail, casesens=False, search_up_to_line=10, reverse=True):
					return False
				if unchanged_checks >= 20:
					print(f'Console looks stuck -- ignore if running TSL -- No Changes Count: {unchanged_checks}')#return False


			if 'root@' in current_last_line and numlines >= 2:
				previousline = total_lines[numlines-2]
				self.DebugLog(f'Last line {-1} --times:{endcount} --> {previousline}', 1)
				endcount += 1
				mce = False

				if any(pass_str.lower() in previousline.lower() for pass_str in self.ttendw) and endcount > 5:
					self.DebugLog("Test Finished Succesfully")
					return True

				# Check MCE at count 5
				if endcount > 5:
					mce = self.mca_checker()

				if mce:
					self.DebugLog("MCE Founds -- Ending Test")
					return False

				if self.search_in_file(lines=total_lines, string=self.ttendfail, casesens=False, search_up_to_line=10, reverse=True):
					self.DebugLog("Test Failed -- Errors detected")
					return False

				if self.search_in_file(lines=total_lines, string=self.ttendw, casesens=False, search_up_to_line=10, reverse=True):
					self.DebugLog("Test Finished Succesfully")
					return True

				if endcount >=20:
					self.DebugLog("Console looks stuck -- Ending Test")
					return False

			else:
				endcount = 0

			if any(fail_str.lower() in current_last_line.lower() for fail_str in self.ttendfail):
				self.DebugLog("Test Failed -- Errors detected")
				return False
				#break

			if any(pass_str.lower() in current_last_line.lower() for pass_str in self.ttendw):
				# Last MCE Check before passing test
				mce = self.mca_checker()
				if mce:
					self.DebugLog("MCE Founds at the end of Test")
					return False

				self.DebugLog("Test Finished Succesfully")
				return True
				#break
			prevlines = numlines
			time.sleep(self.testtime)

	def ping_host(self, host, retries=5, interval=20):
		retry_count = 0
		while retry_count < retries:
			try:
				# Ping the host
				response = subprocess.run(['ping', '-n', '1', host], capture_output=True, text=True)
				if "Reply from" in response.stdout:
					self.DebugLog(f"Host {host} is up.")
					return True
				else:
					self.DebugLog(f"No response from {host}. Retrying...")
					retry_count += 1
					time.sleep(interval)
			except Exception as e:
				self.DebugLog(f"Error pinging {host}: {e}")
				retry_count += 1
				time.sleep(interval)

		self.DebugLog(f"Failed to connect to {host} after {retries} retries.")

	def get_core_data(self):

		if self.chkcore != None:

			core = self.chkcore
			socket = 0

			try:

				if self.product == 'GNR':
					compute=gcd.get_compute(core)
					iaR = gcd.read_current_core_ratio(core, compute, socket)
					iaV = gcd.read_current_core_voltage(core, compute, socket)
					iaL = gcd.read_current_license(core, compute, socket)
					dcf_ratio = gcd.dcf_read_ratio(core, False)
					#print( "core = %s, IA Ratio = %s, IA Volt = %f,  IALicense= %s" % (core, iaR, iaV, iaL))

					self.DebugLog("phys_core = %s, IA Ratio = %s, IA Volt = %f, IALicense= %s, current_dcf_ratio = %d" % (core, iaR, iaV, iaL, dcf_ratio))
				elif self.product == 'CWF':
					phys_mod = core
					compute=gcd.get_compute(core)
					moduleLog = gcd.get_moduleLog(core, compute, socket)
					iaR = gcd.read_current_core_ratio(moduleLog, compute, socket)
					iaV = gcd.read_current_core_voltage(moduleLog, compute, socket)
					self.DebugLog( "PHYmodule = %s, LLmodule = %s, IA Ratio = %d, IA Volt = %f" % (phys_mod, moduleLog, iaR, iaV))
				elif self.product == 'DMR':
					phys_core = core
					iaR = gcd.read_current_core_ratio(phys_core, socket)
					iaV = gcd.read_current_core_voltage(phys_core, socket)
					iaL = gcd.read_current_license(phys_core, socket)

					self.DebugLog("phys_core = %s, IA Ratio = %s, IA Volt = %f, IALicense= %s" % (phys_core, iaR, iaV, iaL))

			except Exception as e:
				self.DebugLog( f" Failed collecting data for --> Core / Module:{core} -- {e}")
				self.DebugLog(f" Disabling Check Core/Module routine for CORE/MOD: {core}")
				self.DebugLog(" Check if your Module/Core is disabled or PythonSV is having issues")
				self.chkcore = None

	def run_tera_term_macro(self):
		macro_path = self.macro
		teraterm_exe = TERATERM_MACRO_PATH #r'C:\teraterm\ttermpro.exe'
		#os.system(f'"{teraterm_exe}" /M={macro_path}')
		self.DebugLog(f"Teraterm data:{macro_path}")
		process = subprocess.Popen([teraterm_exe, '/M='+ macro_path])

		# Wait for the terminate flag to be set
		while not self.terminate.is_set():
			self.check_user_cancel()
			time.sleep(1)
		process.terminate()
		process.wait()
		self.DebugLog(' Test Ended -- Closing Teraterm ....')
		#bring_tera_term_to_foreground()
		#time.sleep(2)
		#send_to_tera_term(macro_path)
		#return process

	def run(self, macro=None, check=True):
		#macro = self.cmds['StartCapture']
		#self.run_tera_term_macro(macro)
		self.check_user_cancel()

		if macro == None: self.macro = self.cmds['StartTest']
		else: macro = self.macro

		teraterm_thread = threading.Thread(target=self.run_tera_term_macro).start()
		if check: self.checker()

	def boot_start(self, macro=None):
		#macro = self.cmds['StartCapture']
		#self.run_tera_term_macro(macro)
		self.check_user_cancel()
		if macro == None: self.macro = self.cmds['StartCapture']
		else: macro = self.macro
		print (self.macro, self.cmds)
		bootlogging_thread = threading.Thread(target=self.boot_loggin).start()

	def boot_loggin(self):
		macro = self.macro
		try:
			teraterm_exe = r'C:\teraterm\ttermpro.exe'
			#os.system(f'"{teraterm_exe}" /M={macro_path}')
			self.DebugLog(f" Teraterm Macro used during Boot:{macro}")
			self.boot_process = subprocess.Popen([teraterm_exe, '/M='+ macro])
			time.sleep(10)
			# Wait for the terminate flag to be set
			self.DebugLog(' Logging Boot Data --')
			while not self.terminate_boot_log.is_set():
				self.check_user_cancel()

				time.sleep(1)
		except Exception as e:
			self.DebugLog(f"Failed during boot logging: {e} ")
			self.boot_process.terminate()
			self.boot_process.wait()

		self.boot_process.terminate()
		self.boot_process.wait()

	def boot_end(self, check = True):
		self.terminate_boot_log.set()
		#self.boot_process.wait()
		self.DebugLog('Closing Teraterm Boot Logging window')
		time.sleep(10)
		self.terminate_boot_log.clear()
		if check: self.checker()

	def PYSVconsole(self, check = True):

		self.DebugLog(' PYSConsole Test Ended ....')
		#self.selfcheck()
		if check: self.checker()

	def checker(self):
		time.sleep(30)
		tstPass = self.selfcheck()

		if tstPass:
			self.DebugLog('SERIAL: Test Completed Succesfully')
			tname = f'{self.test}_PASS'
			self.testresult = f'PASS::{self.test}'

		else:
			self.DebugLog('SERIAL: Test Failed')
			tname = f'{self.test}_FAILED'
			self.testresult = f'FAIL::{self.test}'
		#self.process.terminate()

		dpm.logger(visual = self.vid, qdf = self.qdf, TestName=tname, Testnumber = self.tnum, dr_dump = self.dr_dump, folder=self.tfolder, Bucket = self.bucket, UI=False, logging = self.DebugLog)
		self.scratchpad = ereport.readscratchpad()
		self.terminate.set()

	def mca_checker(self):
		if self.product == 'GNR': mcadata, pysvdecode = ereport.mca_dump_gnr(verbose=False)
		elif self.product == 'CWF': mcadata, pysvdecode = ereport.mca_dump_cwf(verbose=False)
		elif self.product == 'DMR': mcadata, pysvdecode = ereport.mca_dump_dmr(verbose=False)
		else: self.DebugLog(f"Check Configuration product is no available for MCE Capture. Product:{self.product}")

		for k,v in pysvdecode.items():
			if v == True:
				self.DebugLog(f"MCE Found Unit Failed @ {k.upper()}")
				return True
			mcvalue = v

		return mcvalue

	def check_user_cancel(self):

		cancel_check = self.cancel_flag #!= None

		if self.execution_state is not None:
			if self.execution_state.is_cancelled():
				self.DebugLog("Execution stopped by command", 2)
				raise InterruptedError("SERIAL: Execution stopped")

		# Fallback Method -- Used by TTL Test
		elif cancel_check:
			#print('Checking Cancel Status', cancel_check, self.cancel_flag.is_set())
			if self.cancel_flag.is_set():
				self.DebugLog("SERIAL: Framework Execution interrupted by user. Exiting...",2)
				raise InterruptedError('SERIAL: Execution Interrupted by User')

		else:
			pass

# Testing Purpose
def ping_host(host: str, retries: int = 10, interval: int = 20):

	"""
	Pings a remote Host with specific retries and Intervals

	:param host: IP address of the host(e.g., '192.168.0.2').
	:param retries: Number of connection retries.
	:param interval: Interval of time in seconds between each retry.

	"""

	retry_count = 0
	while retry_count < retries:
		try:
			# Ping the host
			response = subprocess.run(['ping', '-n', '1', host], capture_output=True, text=True)
			if "Reply from" in response.stdout:
				print(f"Host {host} is up.")
				return True
			else:
				print(f"No response from {host}. Retrying...")
				retry_count += 1
				time.sleep(interval)
		except Exception as e:
			print(f"Error pinging {host}: {e}")
			retry_count += 1
			time.sleep(interval)

	print(f"Failed to connect to {host} after {retries} retries.")
	return False

def start(visual='-999999999', qdf='Test', bucket='UNCORE', content = 'Dragon', host = '192.168.0.2', chkcore=None, log=log_file_path, cmds=macrospath, tfolder=tfolder, test='Dummy', ttime=30, tnum=1, PassString = 'Test Complete', FailString = 'Test Failed', cancel_flag = None):
	macro_files = {
	'Disconnect': rf'{cmds}\disconnect.ttl',
	'Connect': rf'{cmds}\connect.ttl',
	'StartCapture':  rf'{cmds}\start_capture.ttl',
	'StartTest': rf'{cmds}\Commands.ttl',
	'StopCapture':  rf'{cmds}\stop_capture.ttl'
	}

	kill_process()
	DebugLog = print
	#tst = teraterm(visual, bucket, qdf, log, macro_files, tfolder, test, ttime, tnum, DebugLog)
	tst = teraterm(visual=visual, qdf=qdf, bucket=bucket, log=log, cmds=macro_files, tfolder=tfolder, test=test, ttime=ttime, tnum=tnum, DebugLog=DebugLog, chkcore=chkcore, content=content, host = host, PassString = PassString, FailString = FailString, cancel_flag= cancel_flag)
	tst.run()

def run_ttl(root, data=None):
	ttl.call(root, data, teraterm)

# Kills a Process Window if open -- Run Before starting any console check to avoid previous open windows issues such a COM Port being taken by
def kill_process(process_name: str = 'ttermpro.exe', logger = None):
	"""
	Terminates a process by its name.

	:param process_name: Name of the process to terminate (e.g., 'ttermpro.exe').
	:param logger: External Logger
	"""

	if logger == None: logger = print
	try:
		# Use tasklist to check if the process is running
		result = subprocess.run(['tasklist'], stdout=subprocess.PIPE, text=True)

		# Check if the process is in the list of running processes
		if process_name in result.stdout:
			logger(f"{process_name} is running. Terminating...")

			# Use taskkill to terminate the process
			subprocess.run(['taskkill', '/F', '/IM', process_name], stdout=subprocess.PIPE, text=True)
			logger(f"{process_name} has been terminated.")
		else:
			logger(f"{process_name} is not running.")
	except Exception as e:
		logger(f"An error occurred: {e}")

#for macro in macro_files:
#    run_tera_term_macro(macro)
#    time.sleep(5)  # Wait for a few seconds between running macros



