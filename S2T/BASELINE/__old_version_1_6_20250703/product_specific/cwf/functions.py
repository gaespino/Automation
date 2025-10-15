"""
Product specific functions

REV 0.1 --
Code migration to product specific features

"""

import colorama
from colorama import Fore, Style, Back
from dataclasses import dataclass

CONFIG_PRODUCT = 'CWF'

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
	def core_apic_id(core, compute_index, sv, id0, id1):
		cores = sv.socket0.get_by_path(f'compute{compute_index}').cpu.get_by_path(f'module{core}').cores
		morethan_2_cpm = len(cores) >= 2

		#core = physical2ClassLogical[core % MAXLOGICAL] + (compute_index)*MAXLOGICAL
		id0 = cores[0].thread0.pic_cr_pic_extended_local_apic_id
		if morethan_2_cpm: id1 =  cores[-1].thread0.pic_cr_pic_extended_local_apic_id
		if id1 == None: print (Fore.RED + "\nLess than 2 Cores per module check on the unit, please check your configuration if this is not intended\n" + Fore.RESET )
		
		return id0, id1

	@staticmethod
	def read_dr_registers(sv, ipc, logger, mcadata, table):

		## Registers pre thread -- CWF Requires a halt to read -- Testing a different register, will check if differences shows up.
		## APIC reg --> bus_cr_pic_piclet_state.ext_apic_id.get_value()
		## DRs reg --> .x86_cr_dr0.get_value()
		sv.sockets.computes.cpu.modules.setaccess('crb')
		with ipc.device_locker():
			threads = sv.socket0.computes.cpu.modules.cores
			drs = [['MODULE','THREAD','APIC IDs', 'DR0','DR1','DR2','DR3']]
			
			for thread in threads:
				_CORE = thread.parent.name.upper()
				_THREAD = thread.name.upper()
				_APIC_ID = thread.pic_cr_pic_extended_local_apic_id.get_value()
				_DR0 = thread.x86_cr_dr0.get_value()
				_DR1 = thread.x86_cr_dr1.get_value()
				_DR2 = thread.x86_cr_dr2.get_value()
				_DR3 = thread.x86_cr_dr3.get_value()
			
				if mcadata:
					mcadata['TestName'].append("%s" % thread.pic_cr_pic_extended_local_apic_id.path)
					mcadata['TestValue'].append("0x%x" % _APIC_ID)
					mcadata['TestName'].append("%s" % thread.x86_cr_dr0.path)
					mcadata['TestValue'].append("0x%x" % _DR0)
					mcadata['TestName'].append("%s" % thread.x86_cr_dr1.path)
					mcadata['TestValue'].append("0x%x" % _DR1)
					mcadata['TestName'].append("%s" % thread.x86_cr_dr2.path)
					mcadata['TestValue'].append("0x%x" % _DR2)
					mcadata['TestName'].append("%s" % thread.x86_cr_dr3.path)
					mcadata['TestValue'].append("0x%x" % _DR3)

				if not table: logger(f'dr_data_{_CORE}_th{_THREAD}_APIC{_APIC_ID}_DR0{_DR0}_DR1{_DR1}_DR2{_DR2}_DR3{_DR3}')
											
				drs.append([_CORE, _THREAD, hex(_APIC_ID), _DR0, _DR1, _DR2, _DR3])
			sv.sockets.computes.cpu.modules.setaccess('default')
			return drs    	


	@staticmethod
	def display_banner(revision, date, engineer):
			# Create the banner text
		banner_text = rf'''

==========================================================================================================
    _______      _______   ______  _____________________  ___   ___     _________________________________ 
   / ___/ / __  / / ___/  / ___| \/ / ___/_  __/ ____/  |/  /  |__ \   /_  __/ ____/ ___/_  __/ ____/ __ \
  / /  / /_/ /_/ / /__    \__ \ \  /\__ \ / / / __/ / /|_/ /   __/ /    / / / __/  \__ \ / / / __/ / /_/ /
 / /__/   __    / ___/   ___/ / / /___/ // / / /___/ /  / /   / __/    / / / /___ ___/ // / / /___/ _, _/ 
/____/___/ /___/_/      /____/ /_//____//_/ /_____/_/  /_/   /____/   /_/ /_____//____//_/ /_____/_/ |_|  
																																																			
===========================================================================================================

-- System 2 Tester CWF version {revision}
-- Release: {date}
-- For any issues please contact: {engineer}

===========================================================================================================
	'''
		
		# Print the banner
		print(banner_text)
