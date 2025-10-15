"""
Product specific functions

REV 0.1 --
Code migration to product specific features

"""

import colorama
from colorama import Fore, Style, Back
from dataclasses import dataclass

CONFIG_PRODUCT = 'GNR'

print (f"Loading Functions for {CONFIG_PRODUCT} || REV 0.1")

@dataclass
class functions:
	
	@staticmethod
	def pseudo_masking(ClassMask: dict, ClassMask_sys: dict, syscomputes: int):

		for key in ClassMask.keys():
		
			ClassMask_fix = ClassMask[key][::-1]
			#print(f'\nComputes Mask = {key}',ClassMask[key])
			#print(f'\nComputes Mask = {key}',ClassMask_fix)
			computes = {'compute0':ClassMask_fix[0:44][::-1],'compute1':ClassMask_fix[44:88][::-1],'compute2':ClassMask_fix[88:][::-1]}
			#print('\nComputes Mask = ',computes)
			for compute in syscomputes:
				bitcount = 0
				bitarray = []
				for bit in computes[compute]:
					addbits = bitcount % 5
					if addbits == 0 and bitcount != 0:
						bitarray.append('11')
					bitarray.append(bit)
					bitcount += 1
				bitstring = ''.join(bitarray)
				ClassMask_sys[key][compute] = bitstring

		return ClassMask_sys

	@staticmethod
	def core_apic_id(core, compute_index, sv, id0, id1):
		threads = sv.socket0.get_by_path(f'compute{compute_index}').cpu.get_by_path(f'core{core}').threads
		ht_enabled = len(threads) == 2

		#corefix = core - 60*compute_index
		#core_index = sv.socket._core_phy2log_matrixes['socket0'][compute_index].cha_list[corefix].local_logical
		id0 = threads[0].ml3_cr_pic_extended_local_apic_id
		if ht_enabled: id1 = threads[-1].ml3_cr_pic_extended_local_apic_id
		if id1 == None: print (Fore.RED + "\nHT is disabled on the unit, please check your configuration if this is not intended\n" + Fore.RESET )
		
		return id0, id1
	
	@staticmethod
	def read_dr_registers(sv, ipc, logger, mcadata, table):

		## Registers pre thread -- Testing a different register, will check if differences shows up.
		## APIC reg --> ml3_cr_pic_piclet_state.ext_apic_id.get_value()
		## DRs reg --> .core_cr_dr0.get_value()
		sv.sockets.cpu.cores.setaccess('crb')
		with ipc.device_locker():
			threads = sv.socket0.computes.cpu.cores.threads
			drs = [['CORE','THREAD','APIC IDs', 'DR0','DR1','DR2','DR3']]
			
			for thread in threads:
				_CORE = thread.parent.name.upper()
				_THREAD = thread.name.upper()
				_APIC_ID = thread.ml3_cr_pic_extended_local_apic_id.get_value()
				_DR0 = thread.core_cr_dr0.get_value()
				_DR1 = thread.core_cr_dr1.get_value()
				_DR2 = thread.core_cr_dr2.get_value()
				_DR3 = thread.core_cr_dr3.get_value()
			
				if mcadata:
					mcadata['TestName'].append("%s" % thread.ml3_cr_pic_extended_local_apic_id.path)
					mcadata['TestValue'].append("0x%x" % _APIC_ID)
					mcadata['TestName'].append("%s" % thread.core_cr_dr0.path)
					mcadata['TestValue'].append("0x%x" % _DR0)
					mcadata['TestName'].append("%s" % thread.core_cr_dr1.path)
					mcadata['TestValue'].append("0x%x" % _DR1)
					mcadata['TestName'].append("%s" % thread.core_cr_dr2.path)
					mcadata['TestValue'].append("0x%x" % _DR2)
					mcadata['TestName'].append("%s" % thread.core_cr_dr3.path)
					mcadata['TestValue'].append("0x%x" % _DR3)
				
				if not table: logger(f'dr_data_{_CORE}_{_THREAD}_APIC_{_APIC_ID}_DR0_{_DR0:#x}_DR1_{_DR1:#x}_DR2_{_DR2:#x}_DR3_{_DR3:#x}')
				
				drs.append([_CORE, _THREAD, hex(_APIC_ID), hex(_DR0), hex(_DR1), hex(_DR2), hex(_DR3)])
		sv.sockets.cpu.cores.setaccess('default')

		return drs, mcadata

	@staticmethod
	def display_banner(revision, date, engineer):
    	# Create the banner text
		banner_text = rf'''

==========================================================================================================
   _______   ______     ______  _____________________  ___   ___      _________________________________ 
  / ____/ | / / __ \   / ___| \/ / ___/_  __/ ____/  |/  /  |__ \    /_  __/ ____/ ___/_  __/ ____/ __ \
 / / __/  |/ / /_/ /   \__ \ \  /\__ \ / / / __/ / /|_/ /   __/ /     / / / __/  \__ \ / / / __/ / /_/ /
/ /_/ / /|  / _, _/   ___/ / / /___/ // / / /___/ /  / /   / __/     / / / /___ ___/ // / / /___/ _, _/ 
\____/_/ |_/_/ |_|   /____/ /_//____//_/ /_____/_/  /_/   /____/    /_/ /_____//____//_/ /_____/_/ |_|  
																																																		  
===========================================================================================================

-- System 2 Tester GNR version {revision}
-- Release: {date}
-- For any issues please contact: {engineer}

===========================================================================================================
	'''
	
		# Print the banner
		print(banner_text)
