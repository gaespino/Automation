
import os
import json

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

class TPEdit():

	def __init__(self, selection, product, verif, test=False):
		self.selection = selection
		self.product = product
		self.verif = verif
		self.configs = fungroup(selection, product)
		self.test = test
		
		# Required Strings for TOS call
		self.set_instance = r'%HDMTTOS%\Runtime\Release\SingleScriptCmd.exe setInstanceParam '
		self.verify = r'%HDMTTOS%\Runtime\Release\SingleScriptCmd.exe verifyTestInstance '
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

	def change_instance(self, instance, entry, value, verify=True):

		self.modify_instance(instance, entry, value)
		if verify: self.verify_instance(instance)

	def modify_instance(self, instance, entry, value):

		#print(f'\n\nSetting {instance}')
		print(f'Setting parameters ---> {entry} = "{value}"')
		if not self.test: os.system(self.set_instance + f'{instance} {entry} "{value}"')

	def verify_instance(self, instance):
		print(f'Verifying Instance ---> {instance}')
		if not self.test: os.system(self.verify + f'{instance}')

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

def load_json(file_path):
	with open(file_path, 'r') as file:
		return json.load(file)

def compare_and_apply_changes(original_config, edited_config, tpedit):
	changed_instance = []

	for instance, original_entries in original_config.items():
		if instance in edited_config:
			edited_entries = edited_config[instance]

			# Check for MultiTrial
			bin_matrix = edited_entries.get('Bin_Matrix',False)
			if bin_matrix:
				print('Cannot Change MultTrial Instances :( Moving to Next one.')
				continue
				# Handle instances with Bin_Matrix
				#for bin_value in bin_matrix:
				#	instance_name_with_bin = f"{instance}_{bin_value}"
				#	for entry, original_value in original_entries.items():
				#		edited_value = edited_entries.get(entry)
				#		if edited_value is not None and edited_value != original_value:
				#			print(f'Change detected for {instance_name_with_bin}: {entry} from "{original_value}" to "{edited_value}"')
				#			tpedit.modify_instance(instance_name_with_bin, entry, edited_value)
				#			if instance_name_with_bin not in changed_instance: changed_instance.append(instance_name_with_bin)
			else:
				# Handle regular instances
				for entry, original_value in original_entries.items():
					edited_value = edited_entries.get(entry)
					if edited_value is not None and edited_value != original_value:
						print(f'Change detected for {instance}: {entry} from "{original_value}" to "{edited_value}"')
						tpedit.modify_instance(instance, entry, edited_value)
						if instance not in changed_instance: changed_instance.append(instance)

	if changed_instance:
		for mod_inst in changed_instance:
			tpedit.verify_instance(mod_inst)


def main(Debug):
	# Load the original and edited JSON configurations
	original_config_path = r"I:\intel\engineering\dev\user_links\ddcanale\TP\TP_WW22P4_Short\MTPLs\ConfigFiles\FUN_UNCORE_COMP.json"
	edited_config_path = r"I:\intel\engineering\dev\user_links\ddcanale\TP\TP_WW22P4_Short\MTPLs\ConfigFiles\IDI_Configuration_File.json"
	
	original_config = load_json(original_config_path)
	edited_config = load_json(edited_config_path)

	# Initialize the TPEdit class
	tpedit = TPEdit(selection='UNCORE', product='UCCAP', verif=True, test=Debug)

	# Compare and apply changes
	compare_and_apply_changes(original_config, edited_config, tpedit)

if __name__ == '__main__':
	main(Debug=True)