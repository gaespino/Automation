"""
Product specific functions

REV 0.1 --
Code migration to product specific features

"""

import colorama
import time
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
				_APIC_ID = thread.thread0.pic_cr_pic_extended_local_apic_id.get_value()
				_DR0 = thread.thread0.x86_cr_dr0.get_value()
				_DR1 = thread.thread0.x86_cr_dr1.get_value()
				_DR2 = thread.thread0.x86_cr_dr2.get_value()
				_DR3 = thread.thread0.x86_cr_dr3.get_value()
			
				if mcadata:
					mcadata['TestName'].append("%s" % thread.thread0.pic_cr_pic_extended_local_apic_id.path)
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
	def _set_crs(sv, num_crs, crarray, cr_array_start, cr_array_end, skip_index_array, _s2t_dict, func_wr_ipc):
		
		def check_value(value,n,label='TAP'):
			
			if int(value) == int(desired_value):
				print(Fore.LIGHTGREEN_EX +"{} -- | {}:{} Already at desired value :{}:{} ".format(label, index, n, hex(desired_value), hex(value)) + Fore.RESET)
				return True
			return False

		def validate_change(n):
			check_string = Fore.RED + "NOT OK" + Fore.RESET
			n_value = sv.sockets[0].cpu.modules[0].cores[0].get_by_path(n).get_value()
			if int(n_value) == int(desired_value):
				check_string = Fore.GREEN + "OK" + Fore.RESET
			
			return check_string

		print ("\nSetting %d CRs " % num_crs)
		index = 0

		for n in sorted(crarray):
		# for n in (crarray):
			desired_value = crarray[n]
			
			# HardCoded Flag -- we will use TAP for registers located at thread level
			use_TAP = True
			
			if (index not in skip_index_array) and (index >= cr_array_start) and (index<=cr_array_end):
				value = sv.sockets[0].cpu.modules[0].cores[0].get_by_path(n).get_value()
				if check_value(value, n, label='CRS'):
					index +=1
					continue
				
				if 'thread' in n and use_TAP:

					# This does not apply to CWF but leaving for reference
					threads = len(sv.sockets.cpu.modules[0].cores.threads)
					if threads == 1 and 'thread1' in n:
						print ("%d: !!!! skipping %s, single thread is configured" % (index, n)  )
						continue

					sv.socket0.computes.cpu.modules.cores.get_by_path(n).write(crarray[n])
					
					check_str = validate_change(n)

					print("TAP -- | {}:{} Changed from :{}: -> :{}: | ".format(index, n, hex(value), hex(crarray[n])) + check_str)
				else:
					func_wr_ipc(index, n, crarray) ## Calls write IPC function on S2T Main
					check_str = validate_change(n)
					print("IPC -- | {}:{}({}) Changed from :{}: -> :{}: | ".format(index, n,hex(_s2t_dict[n]['cr_offset']),hex(value),hex(crarray[n])) + check_str)
			else:
				print (Fore.YELLOW +"%d: !!!! skipping %s" % (index, n) + Fore.RESET)
			index +=1

	@staticmethod
	def _set_crs_tap(sv, num_crs, crarray, cr_array_start, cr_array_end, skip_index_array):
		print ("Setting %d CRs " % num_crs)
		index = 0		
		
		for n in sorted(crarray):
		# for n in (crarray):
			
			if (index not in skip_index_array) and (index >= cr_array_start) and (index<=cr_array_end):
				# print ("%d:%s: itp.crb64(0x%x, 0x%x)" % (index, n, _s2t_dict[n], crarray[n]))
				
				
				threads = len(sv.sockets.cpu.modules[0].cores)
				
				# This does not apply to CWF but leaving for reference
				if threads == 1 and 'thread1' in n:
					print ("%d: !!!! skipping %s, single thread is configured" % (index, n)  )
					continue
				
				value = sv.socket0.compute0.cpu.modules[0].get_by_path(n)
				sv.socket0.computes.cpu.modules.get_by_path(n).write(crarray[n])
				
				time.sleep(0.5)	
				
				mcchk = sv.socket0.compute0.cpu.modules[0].bus_cr_mci_status # Need to confirm will check BUS for now
			
				if mcchk != 0:
					print(f'sv.socket0.cpu.core0.ml2_cr_mc3_status = {mcchk}')
					print(f"{index}: {n} - Failing the unit add to skip --")
					break
				print("{}:{} Changed from :{}: -> :{}: ".format(index, n, value, hex(crarray[n])))

			else:
				print ("%d: !!!! skipping %s" % (index, n)  )
			index +=1

	@staticmethod
	def _cr_reg_dump(_seldict, seldict, sv, core, regsname, _crd):

		for key in _seldict[seldict].keys():
			regfound = sv.socket0.cpu.get_by_path(f'module{core}').core0.thread0.search(key)
			#threaded = True if 'thread0' in regfound else False
			try:
				if key in regfound:
					data = sv.socket0.cpu.get_by_path(f'module{core}').core0.thread0.get_by_path(key).info
					value = sv.socket0.cpu.get_by_path(f'module{core}').core0.thread0.get_by_path(key).read()
					register = f'thread0.{key}'
				else:
					data = sv.socket0.cpu.get_by_path(f'module{core}').core0.get_by_path(key).info
					value = sv.socket0.cpu.get_by_path(f'module{core}').core0.get_by_path(key).read()
					register = key
				
				description = data['description'] if 'description' in data.keys() else data['original_name']
				cr_offset = data['cr_offset']
				numbits = data['numbits']
				
				_crd[regsname[seldict]][register] = {'description':description,
												'cr_offset':cr_offset, 
												'numbits':numbits,
												'desired_value':hex(_seldict[seldict][key]),
												'ref_value':hex(int(value)),} 
				
				print(f"{register} : cr_offset = {data['cr_offset']}, numbits = {data['numbits']}, desired_value = {_seldict[seldict][key]} -- {value}")
			
			except Exception as e:

				print (f"Exception reading {key} on core{core} : {e}")
				_crd[regsname[seldict]][key] = {'description':'N/A',
												'cr_offset':'N/A', 
												'numbits':'N/A',
												'desired_value':hex(_seldict[seldict][key]),
												'ref_value':'N/A',} 

		return _crd
	
	@staticmethod
	def _cr_reg_check(sv, _seldict, seldict, core):
		
		for key in _seldict[seldict].keys():
			#thread_search = True if 'thread' in key else False
			try:
				value = sv.socket0.cpu.get_by_path(f'module{core}').core0.get_by_path(key).get_value()

				desired_value = _seldict[seldict][key]
				
				string_check = (Fore.RED + "DIFFERENT" + Fore.RESET) if int(value) != int(desired_value) else (Fore.GREEN + "SAME" + Fore.RESET) 

				print(f"{key} : TESTER = {hex(desired_value)} :: System = {hex(value)} | "+ string_check)
			except Exception as e:
				print (Fore.RED + f"Exception reading {key} on module{core} : {e}" + Fore.RESET)

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
