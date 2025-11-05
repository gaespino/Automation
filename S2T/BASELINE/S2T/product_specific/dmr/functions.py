"""
Product specific functions

REV 0.1 --
Code migration to product specific features

"""

import colorama
from colorama import Fore, Style, Back
from dataclasses import dataclass

CONFIG_PRODUCT = 'DMR'

print (f"Loading Functions for {CONFIG_PRODUCT} || REV 0.1")

@dataclass
class functions:
	
	@staticmethod
	def pseudo_masking(ClassMask: dict, ClassMask_sys: dict, syscomputes: int):

		for key in ClassMask.keys():

			ClassMask_fix = ClassMask[key][::-1]
			computes = {'compute0':ClassMask_fix[0:24][::-1],'compute1':ClassMask_fix[24:48][::-1],'compute2':ClassMask_fix[48:72][::-1]}
			
			for compute in syscomputes:
				bitcount = 0
				bitarray = []
				for bit in computes[compute]:
					addbits = bitcount % 3 # there are 5 disabled after a set of 3 cores
					# if addbits == 0 and bitcount != 0:
					if bitcount == 0:
						bitarray.append('11') # 5 cores are disabled starting at the core 0
					elif addbits == 0:
						bitarray.append('1111') 
					bitarray.append(bit)
					bitcount += 1
				bitarray.append('111111')
				bitstring = ''.join(bitarray)
				ClassMask_sys[key][compute] = bitstring
		
		return ClassMask_sys

	@staticmethod
	def core_apic_id(phys_module, cbb_index, compute_index, sv, id0, id1):

		cores = sv.socket0.get_by_path(f'cbb{cbb_index}').get_by_path(f'compute{compute_index}').get_by_path(f'module{phys_module}').cores
		morethan_1_cpm = len(cores) >= 2

		#core = physical2ClassLogical[core % MAXLOGICAL] + (compute_index)*MAXLOGICAL
		id0 = cores[0].thread0.ml3_cr_pic_extended_local_apic_id
		if morethan_1_cpm: id1 =  cores[-1].thread0.ml3_cr_pic_extended_local_apic_id
		if id1 == None: print (Fore.RED + "\nLess than 2 Cores per module check on the unit, please check your configuration if this is not intended\n" + Fore.RESET )
		
		return id0, id1
	
	@staticmethod
	def read_dr_registers(sv, ipc, logger, mcadata, table):

		## Registers pre thread -- CWF Requires a halt to read -- Testing a different register, will check if differences shows up.
		## APIC reg --> bus_cr_pic_piclet_state.ext_apic_id.get_value()
		## DRs reg --> .x86_cr_dr0.get_value()
		sv.sockets.computes.cpu.modules.setaccess('crb')
		with ipc.device_locker():
			threads = sv.socket0.cbbs.computes.modules.cores
			drs = [['MODULE','THREAD','APIC IDs', 'DR0','DR1','DR2','DR3']]
			
			for thread in threads:
				_CORE = thread.parent.name.upper()
				_THREAD = thread.name.upper()
				_APIC_ID = thread.thread0.ml3_cr_pic_extended_local_apic_id.get_value()
				_DR0 = thread.thread0.x86_cr_dr0.get_value()
				_DR1 = thread.thread0.x86_cr_dr1.get_value()
				_DR2 = thread.thread0.x86_cr_dr2.get_value()
				_DR3 = thread.thread0.x86_cr_dr3.get_value()
			
				if mcadata:
					mcadata['TestName'].append("%s" % thread.thread0.ml3_cr_pic_extended_local_apic_id.path)
					mcadata['TestValue'].append("0x%x" % _APIC_ID)
					mcadata['TestName'].append("%s" % thread.thread0.x86_cr_dr0.path)
					mcadata['TestValue'].append("0x%x" % _DR0)
					mcadata['TestName'].append("%s" % thread.thread0.x86_cr_dr1.path)
					mcadata['TestValue'].append("0x%x" % _DR1)
					mcadata['TestName'].append("%s" % thread.thread0.x86_cr_dr2.path)
					mcadata['TestValue'].append("0x%x" % _DR2)
					mcadata['TestName'].append("%s" % thread.thread0.x86_cr_dr3.path)
					mcadata['TestValue'].append("0x%x" % _DR3)

				if not table: logger(f'dr_data_{_CORE}_{_THREAD}_APIC_{_APIC_ID:#x}_DR0_{_DR0:#x}_DR1_{_DR1:#x}_DR2_{_DR2:#x}_DR3_{_DR3:#x}')
											
				drs.append([_CORE, _THREAD, hex(_APIC_ID), _DR0, _DR1, _DR2, _DR3])
			sv.sockets.computes.cpu.modules.setaccess('default')
			return drs, mcadata    	


	@staticmethod
	def display_banner(revision, date, engineer):
			# Create the banner text
		banner_text = rf'''

==========================================================================================================
    ____  __  _______     _______  ____________  ___   ___     _________________________________ 
   / __ \/  |/  / __ \   / ___/\ \/ / ___/_  __/ ____/  |/  /  |__ \   /_  __/ ____/ ___/_  __/ ____/ __ \
  / / / / /|_/ / /_/ /   \__ \  \  /\__ \ / / / __/ / /|_/ /   __/ /    / / / __/  \__ \ / / / __/ / /_/ /
 / /_/ / /  / / _, _/   ___/ /  / /___/ // / / /___/ /  / /   / __/    / / / /___ ___/ // / / /___/ _, _/ 
/_____/_/  /_/_/ |_|   /____/  /_//____//_/ /_____/_/  /_/   /____/   /_/ /_____//____//_/ /_____/_/ |_|  
																																																			
===========================================================================================================

-- System 2 Tester DMR version {revision}
-- Release: {date}
-- For any issues please contact: {engineer}

===========================================================================================================
	'''
		
		# Print the banner
		print(banner_text)
