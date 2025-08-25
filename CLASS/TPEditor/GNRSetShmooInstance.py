
import os
import argparse
import sys

debug = False
# Content Instances used

def fungroup(selection = 'UNCORE', product= 'UCCAP'):

	prod = {'UCCAP': {'patmods':'FUN_UCC', 'fuse':'FUN_UCCAP'}}
	
	funSelection = {'UNCORE': 
				 		{	'path': 'Modules/FUN_UNCORE_COMP/InputFiles',
							'shmoo': 'UncoreFC_shmoo_config.json',
							'fctracking': '.InitialDefeatureTracking.json',
							'patmods': f"{prod[product]['patmods']}.patmod.json",
							'setpoints': 'FUN_UTP_setpoints.json',
							'fuseconfig': f"{prod[product]['fuse']}.fuseconfig.json",
							'ConfigFile':"~HDMT_TPL_DIR/Modules/FUN_UNCORE_COMP/InputFiles/"
	   					}
					}
	return funSelection[selection]

def class_instances(F):
	
	uncore_instances = {f'DRG_{F}_CD0':			f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHDRGCD0',
						f'DRG_{F}_CD1':			f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHDRGCD1',
						f'DRG_{F}_CD2':			f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHDRGCD2',
						f'UUFC_{F}_PARALLEL':	f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHTWPARALLEL',
						f'UUFC_{F}_CFC_MESHTW':	f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHTW',
						f'UUFC_{F}_HDC_MESHTW':	f'FUN_UNCORE_COMP::UNCORE_HDC_VMIN_K_CHKCFCHDC{F}_STF_HDC_VMIN_{F}_MESHTW',
						f'MPM_{F}_CD0':			f'FUN_UNCORE_COMP::UNCORE_DDR_VMIN_K_CHKDDRD{F}_STF_DDRD_VMIN_{F}_DDRMPMCD1',
						f'MPM_{F}_CD1':			f'FUN_UNCORE_COMP::UNCORE_DDR_VMIN_K_CHKDDRD{F}_STF_DDRD_VMIN_{F}_DDRMPMCD2',
						f'MPM_{F}_CD2':			f'FUN_UNCORE_COMP::UNCORE_DDR_VMIN_K_CHKDDRD{F}_STF_DDRD_VMIN_{F}_DDRMPMCD3',
						f'FCTRACKINGA_{F}':		f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGA',
						f'FCTRACKINGB_{F}':		f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGB',
						f'FCTRACKINGC_{F}':		f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGC',	
						f'FCTRACKINGD_{F}':		f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGD',		
					}

	return uncore_instances

def jsonfinder(directory):
	"""
	Lists all the JSON files in the specified directory.

	Args:
	directory (str): The path to the directory to search for JSON files.

	Returns:
	list: A list of filenames (str) that end with '.json'
	"""
	# Initialize an empty list to store the names of JSON files
	json_files = { }

	# Check if the directory exists
	if not os.path.exists(directory):
		print("The specified directory does not exist.")
		return json_files

	# Loop through each file in the directory
	for filename in os.listdir(directory):
		# Check if the file is a JSON file
		parts = filename.split('.')
		file_end = parts[-1]
		name = parts[0]
		func = None
		if file_end == "json":
			# Append the full path of the file to the list
			#parts = filename.split('.')
	
			if len(parts) > 2:
				func = parts[1]
			elif 'setpoints' in name:
				func = 'setpoints'
			elif 'shmoo' in name:
				func = 'shmoo'
				
			
			## If Function is found add it to the dictionary
			if func != None:
				# Create the key with an empty array if it doesnts exists
				if func not in json_files:
					json_files[func] = []
				
				json_files[func] += [name]
	
	return json_files

def argparser(debug):
	if not debug:
		parser = argparse.ArgumentParser()
		typehelp = ("Shmoo configuration for GNR Tester")

		# Add Argument list below
		parser.add_argument('-content', choices=['mpm', 'drg', 'uufc','fctracking', 'other'],type=str, required= True,
							help = "Content Shmoos to be enabled")
		parser.add_argument('-plist', default=None, type=str, required= False,
							help = "Content Shmoos to be enabled")
		parser.add_argument('-frequency', choices=['F1','F2','F3','F4'],type=str, required= True,
							help = "Content Shmoos to be enabled")
		parser.add_argument('-enable',  choices=['True','False',None],type=str, default=None, required= False,
							help = "Enable / Disable option for shmoo config ")
		parser.add_argument('-Shmoo', type=str, default=None, required= False,
							help = "Name of the shmoo to be used from UNCORE SHMOO FILE")
		parser.add_argument('-Mask', type=str, default=None, required= False,
							help = "Masking file to change FCTRACKING A, B, C or D")
		parser.add_argument('-MaskName', type=str, default=None, required= False,
							help = "Name of the FCTRACKING to be used")

		args = parser.parse_args()
	
	# Default arguments for debug mode of the script
	else:
		class Args:
			#savefile = 'I:\\intel\\engineering\\dev\\team_ftw\\gaespino\\EMRMCC\\PEGA_SHMOOS_VF_NOVF\\ShmooParsed_Data.txt'
			content = 'drg'
			plist = "fun_uncore_vcccfc_F1_CHKCFCF1_siso_DRAGON_MATCHMODE_new_list"
			frequency = 'F1'
			Shmoo = 'LLC_SHMOO'
			Mask = 'A'
			MaskName = 'GNRX3FCR0'
			enable = 'False'
		args = Args()
	
	return args

# Will move the parameters to be read from a dict later
set_instance = '%HDMTTOS%\Runtime\Release\SingleScriptCmd.exe setInstanceParam '
verify = '%HDMTTOS%\Runtime\Release\SingleScriptCmd.exe verifyTestInstance '
ShmooEnabled = 'ShmooEnable'
LogEnabled = 'LogLevel'
MaskConfigFile = 'ConfigFile'
setShmoo = True
Patlist = 'Patlist'
ShmooConfigurationFile = 'ShmooConfigurationFile'

plist_drg = {	'CFCvmin':"fun_uncore_vcccfc_F1_CHKCFCF1_siso_Pseudo_CFCvmin_list",
				'CFCvminAll':"fun_uncore_vcccfc_F1_CHKCFCF1_siso_Pseudo_CFCvminALL_list",
				'NewMatchmode':"fun_uncore_vcccfc_F1_CHKCFCF1_siso_DRAGON_MATCHMODE_new_list",
				'MATCHMODE':"fun_uncore_vcccfc_F1_CHKCFCF1_siso_DRAGON_MATCHMODE_list",
				}


class TPEdit():
	def __init__(self, selection, product, verif):
		self.selection = selection
		self.product = product
		self.verif = verif
		self.configs = fungroup(selection, product)
		
		# Required Strings for TOS call
		self.set_instance = '%HDMTTOS%\Runtime\Release\SingleScriptCmd.exe setInstanceParam '
		self.verify = '%HDMTTOS%\Runtime\Release\SingleScriptCmd.exe verifyTestInstance '
		self.ShmooEnabled = 'ShmooEnable'
		self.LogEnabled = 'LogLevel'
		self.MaskConfigFile = 'ConfigFile'
		self.preinstances = 'TestPointPreinstance'
		self.FreqVolt = {
									'VoltageTargets':None,
									'StartVoltages':None,
									'EndVoltageLimits': None,
									'StartVoltegesForRetry': None,
									'ForwardingIdentifier': None,
									'OffsetValue': None,
									'StartOffset': None,
									'TestPointPreinstance' : None
									}
		#setShmoo = True
		self.Patlist = 'Patlist'
		self.ShmooConfigurationFile = 'ShmooConfigurationFile'
		

	def ShmooSet(self, instances):
		
		for instance in instances:

			##Set Bypass

			print(f'\n\nSetting {instance}')
			print('Setting parameters ---> LogLevel = "Enabled" && ShmooEnable = "ENABLED_ALWAYS"')
			os.system(self.set_instance + f'{instance} {self.LogEnabled} "Enabled"')
			os.system(self.set_instance + f'{instance} {self.ShmooEnabled} "ENABLED_ALWAYS"')

	def ShmooUnSet(self, instances):

	
		for instance in instances:

			##Set Bypass

			print(f'\n\nSetting {instance}')
			print('Setting parameters ---> LogLevel = "Disabled" && ShmooEnable = "DISABLED"')
			os.system(self.set_instance + f'{instance} {self.LogEnabled} "Disabled"')
			os.system(self.set_instance + f'{instance} {self.ShmooEnabled} "DISABLED"')

	def FCTrackingChange(self, MaskFile, instances):
		config = self.configs

		ConfigFile = config['ConfigFile'] #"~HDMT_TPL_DIR/Modules/FUN_UNCORE_COMP/InputFiles/"
		fctracking = config['fctracking']
		File = f"{ConfigFile}{MaskFile}{fctracking}"
		for instance in instances:
			print(f'\n\nSetting {instance}')
			print(f'Setting parameters ---> ConfigFile = "{File}"')
			os.system(self.set_instance + f'{instance} {self.MaskConfigFile} "{File}"')
			#os.system(set_instance + f'{instance} {ShmooEnabled} "DISABLED"')
			if self.verif:
				print(f'Verifying Instance --->  "{instance}"')
				os.system(self.verify + f'{instance}')

	def ContentChange(self, plist, instances):

		PLIST = plist
		for instance in instances:
			print(f'\n\nSetting {instance}')
			print(f'Setting parameters ---> Patlist = "{PLIST}"')
			os.system(self.set_instance + f'{instance} {self.Patlist} "{PLIST}"')
			#os.system(set_instance + f'{instance} {ShmooEnabled} "DISABLED"')

	def VFChange(self, preinstance, voltages, instances):

		for key in self.FreqVolt.keys():
			if key == self.preinstances:
				self.FreqVolt[key] = preinstance
			else:	
				self.FreqVolt[key] = voltages[key]
		
		for instance in instances:
			
			for n, v in self.FreqVolt.items():
				if v:
					print(f'\n\nSetting {instance}')
					print(f'Setting parameters ---> {n} = "{v}"')
					os.system(self.set_instance + f'{instance} {n} "{v}"')
					#os.system(set_instance + f'{instance} {ShmooEnabled} "DISABLED"')


	def ShmooChange(self, shmoo, instances):
		configs = self.configs
		shmoopath = configs['path']
		shmoofile = configs['shmoo']

		ShmooConfigFile = f"./{shmoopath}/{shmoofile}!{shmoo}"
		for instance in instances:
			print(f'\n\nSetting {instance}')
			print(f'Setting parameters ---> ShmooConfigurationFile = "{ShmooConfigFile}"')
			os.system(self.set_instance + f'{instance} {self.ShmooConfigurationFile} "{ShmooConfigFile}"')
			#os.system('%HDMTTOS%\Runtime\Release\SingleScriptCmd.exe verifyTestInstance ' 'TPI_DFF::DFFX_X_UBE_K_START_X_X_X_X')
			if self.verif:
				print(f'Verifying Instance --->  "{instance}"')
				os.system(self.verify + f'{instance}')
				#os.system(set_instance + f'{instance} {ShmooEnabled} "DISABLED"')


if __name__ == '__main__' : 
	args = argparser(debug)
	content = args.content
	plist = args.plist
	frequency = args.frequency
	Mask = args.Mask
	MaskName = args.MaskName
	setShmoo = args.enable
	Shmoo = args.Shmoo
	inst_dict = class_instances(frequency)
	
	#print(setShmoo)
	if content == 'drg':
		instances = [inst_dict[f'DRG_{frequency}_CD0'],inst_dict[f'DRG_{frequency}_CD1'],inst_dict[f'DRG_{frequency}_CD2']]
		
	elif content == 'mpm':
		instances = [inst_dict[f'MPM_{frequency}_CD0'],inst_dict[f'MPM_{frequency}_CD1'],inst_dict[f'MPM_{frequency}_CD2']]
	elif content == 'uufc':
		instances = [inst_dict[f'UUFC_{frequency}_PARALLEL']]
	elif content == 'fctracking':
		## Will bring data from an external file
		instances = [inst_dict[f'FCTRACING{Mask}_{frequency}']]
	else:
		print ('No valid instance selected')
		sys.exit()
	tp = TPEdit(selection='UNCORE', product='UCCAP', verif=True)
	if plist != None:
		tp.ContentChange(plist, instances)
	if Shmoo != None:
		tp.ShmooChange(Shmoo, instances)
	if Mask != None and MaskName != None:
		tp.FCTrackingChange(MaskName, instances)
	
	if setShmoo != None:
		if setShmoo == 'True' and (content != 'fctracking'):
			print('\n\tSetting SHMOOS Configuration in selected instances...\n')
			tp.ShmooSet(instances)
		else:

			print('\n\tRemoving SHMOOS Configuration in selected instances...\n')
			tp.ShmooUnSet(instances)