
# Code Snippet taken from /pythonsv/graniterapids/ras/ras_master/portid2ip
'''
Code used to translate PortID Data into Current System IP Information

The main call for this script will be made by dpm script

'''

import namednodes
#import graniterapids.ras.ras_master.pysv_shortcut as psv
import csv
#from graniterapids.ras.ras_master.ieh_test_master import test_master
sv = namednodes.sv

global ret_csv
ret_csv = [['PORT ID','IP','PYTHONSV PATH']]

def search_from_target_info(target_info,portid):
	for key, value in target_info.items():
		if key == 'portid':
			return value == int(portid)
		elif isinstance(value, dict):
			if search_from_target_info(value, int(portid)):
				return True
	return False

def search_from_target_info_db_gen(target_info):
	val = False
	for key, value in target_info.items():
		if key == 'portid':
			return value
		elif isinstance(value, dict):
			val = search_from_target_info_db_gen(value)
			if val!=False:return val
	return False

def finder(target,portid):
	found_ip = False
	ret = None
	attributes = find_subcomponent(target)
	#attributes_and_methods = target.sub_components
	#attributes_and_methods = [x for x in attributes_and_methods.keys()]# if not x.startswith('_')]
	#attributes = [x for x in attributes_and_methods if 'target_info' in dir(target.getbypath(x))]
	#print(attributes_and_methods)
	#print(attributes)
	for ip in attributes:
		#if 'scf_cms' in ip: print(ip, 'Finder')
		target_info = target.getbypath(ip).target_info
		try:
			found_ip = search_from_target_info(target_info,portid)
		except:
			#print('Failed in Finder')
			pass
		if found_ip:
			print('The PortID :',hex(portid), ' corresponds to : ',ip, ', path : ',target.getbypath(ip).path)
			ret = [hex(portid),ip,target.getbypath(ip).path]
			return ret
	return ret

def db_gen(target):
	portid = False
	attributes_and_methods = target.sub_components
	attributes_and_methods = [x for x in attributes_and_methods.keys()]# if not x.startswith('_')]
	attributes = []
	for x in attributes_and_methods:
		try:
			if 'target_info' in dir(target.getbypath(x)):
				attributes.append(x)
		except: pass
	for ip in attributes:
		target_info = target.getbypath(ip).target_info
		try:
			portid = search_from_target_info_db_gen(target_info)
		except:pass
		if portid != False:
			if type(target.getbypath(ip).path)!=namednodes.comp.ComponentGroup:
				ret_csv.append([hex(portid),ip,target.getbypath(ip).path])
				print('The PortID :',hex(portid), ' corresponds to : ',ip, ', path : ',target.getbypath(ip).path)

def find_ip(portid, db = False):
	#sockets = psv.get_sockets()
	sockets = sv.sockets
	computes = sv.sockets.computes
	ios = sv.sockets.ios
	#cpus = sv.sockets.cpus
   
	for skt in sockets:
		#computes = psv.get_cdies()
		for io in ios:#range(2):

			### IO DIE
			#die = psv.get_iodie(int(skt.name.split('socket')[1]),io)
			#print(die.name)
			### IO -> UNCORE
			ret = find_component(io, portid, component='uncore', db=False)
			if ret !=None: return ret
			#ret = finder(die.uncore,portid)
			#if ret != None: return ret
			
			#attributes_and_methods = die.uncore.sub_components
			#attributes_and_methods = [x for x in attributes_and_methods.keys()]# if not x.startswith('_')]
			#attributes = [x for x in attributes_and_methods if 'target_info' in dir(die.uncore.getbypath(x))]
			#for ip in attributes:
			#	try:
			#		ret = finder(die.uncore.getbypath(ip),portid)
			#		if ret != None: return ret
			#	except:pass
			#if ret != None: return ret
			
			### IO -> FUSES
			ret = find_component(io, portid, component='fuses', db=False)
			if ret !=None: return ret
			#ret = finder(die.fuses,portid)
			#if ret != None: return ret
			
			#attributes_and_methods = die.fuses.sub_components
			#attributes_and_methods = [x for x in attributes_and_methods.keys()]# if not x.startswith('_')]
			#attributes = [x for x in attributes_and_methods if 'target_info' in dir(die.fuses.getbypath(x))]
			#for ip in attributes:
			#	try:
			#		ret = finder(die.fuses.getbypath(ip),portid)
			#		if ret != None: return ret
			#	except:pass
			#if ret != None: return ret
			
		for die in computes:
			ret = find_component(die, portid, component='uncore', db=False)
			if ret !=None: return ret
			### COMPUTE -> UNCORE
			#ret = finder(die.uncore,portid)
			#if ret != None: return ret
			
			#attributes_and_methods = dir(die.uncore)
			#attributes_and_methods = [x for x in attributes_and_methods.keys()]# if not x.startswith('_')]
			#attributes = [x for x in attributes_and_methods if 'target_info' in dir(die.uncore.getbypath(x))]
			#for ip in attributes:
			#	try:
			#		ret = finder(die.uncore.getbypath(ip),portid)
			#		if ret != None: return ret
			#	except:pass
			#if ret != None: return ret
			
			### COMPUTE -> CPU
			ret = find_component(die, portid, component='cpu', db=False)
			if ret !=None: return ret
			#ret = finder(die.cpu,portid)
			#if ret != None: return ret
			
			#attributes_and_methods = dir(die.cpu)
			#attributes_and_methods = [x for x in attributes_and_methods.keys()]# if not x.startswith('_')]
			#attributes = [x for x in attributes_and_methods if 'target_info' in dir(die.cpu.getbypath(x))]
			#for ip in attributes:
			#	try:
			#		ret = finder(die.cpu.getbypath(ip),portid)
			#		if ret != None: return ret
			#	except:pass
			#if ret != None: return ret
			
			### COMPUTE -> FUSES
			ret = find_component(die, portid, component='fuses', db=False)
			if ret !=None: return ret
			#ret = finder(die.fuses,portid)
			#if ret != None: return ret
			
			#attributes_and_methods = dir(die.fuses)
			#attributes_and_methods = [x for x in attributes_and_methods.keys()]# if not x.startswith('_')]
			#attributes = [x for x in attributes_and_methods if 'target_info' in dir(die.fuses.getbypath(x))]
			#for ip in attributes:
			#	try:
			#		ret = finder(die.fuses.getbypath(ip),portid)
			#		if ret != None: return ret
			#	except:pass
			#if ret != None: return ret
	return None

def find_component(die, portid, component = 'uncore', db = False):
	ret = None
	ip = die.getbypath(component) #psv.get_iodie(int(skt.name.split('socket')[1]),io)
	print(f'--> Looking PortID info in {die.name} : {ip.name}')
	### IO -> UNCORE
	if db: db_gen(ip)
	else:ret = finder(ip,portid)
	
	if ret != None: return ret
	attributes = find_subcomponent(ip)	
	#attributes_and_methods = ip.sub_components
	#attributes_and_methods = [x for x in attributes_and_methods.keys()]# if not x.startswith('_')]
	#attributes = [x for x in attributes_and_methods if 'target_info' in dir(ip.getbypath(x))]
	#print(attributes)
	for sub in attributes:
		try:
			#if 'scf_cms' in sub: print(sub)
			if db: 
				db_gen(ip.getbypath(sub))
			else: 
				ret = finder(ip.getbypath(sub),portid)
			
			if ret != None: 
				return ret
			
			# Search in a lower layer
			attributes_l2 = find_subcomponent(ip.getbypath(sub))
			for sub_l2 in attributes_l2:

				if db: 
					db_gen(ip.getbypath(sub).getbypath(sub_l2))
				else: 
					ret = finder(ip.getbypath(sub).getbypath(sub_l2),portid)
				if ret != None: 
					return ret		
		
		except:
			#print('Failed in Find Component')
			pass
	if ret != None: return ret
	return ret

def find_subcomponent(ip):
	attributes_and_methods = ip.sub_components
	attributes_and_methods = [x for x in attributes_and_methods.keys()]# if not x.startswith('_')]
	attributes = [x for x in attributes_and_methods if 'target_info' in dir(ip.getbypath(x))]

	return attributes

def database_generator(filename = 'C:/pythonsv/graniterapids/ras/ras_master/10nm_Wave4_PortID_HAS_1p0_WW28p3_2021.xlsx'):
	sockets = sv.sockets
	computes = sv.sockets.computes
	ios = sv.sockets.ios	
	
	#sockets = psv.get_sockets()
	for skt in sockets:
			#computes = psv.get_cdies()
			for io in ios:#range(2):
				### IO DIE
				find_component(io, portid=None, component='uncore', db=True)
				find_component(io, portid=None, component='fuses', db=True)

				#die = psv.get_iodie(int(skt.name.split('socket')[1]),io)
				
				### IO -> UNCORE
				#print('IO:UNCORE')
				#ret = db_gen(die.uncore)
				
				#attributes_and_methods = die.uncore.sub_components
				#attributes_and_methods = [x for x in attributes_and_methods.keys()]# if not x.startswith('_')]
				#attributes = [x for x in attributes_and_methods if 'target_info' in dir(die.uncore.getbypath(x))]
				#for ip in attributes:
				#	try:ret = db_gen(die.uncore.getbypath(ip))
				#	except:pass
				
				### IO -> FUSES
				#print("IO:FUSES")
				#ret = db_gen(die.fuses)
				
				#attributes_and_methods = dir(die.fuses)
				#attributes_and_methods = [x for x in attributes_and_methods if not x.startswith('_')]
				#attributes = [x for x in attributes_and_methods if 'target_info' in dir(die.fuses.getbypath(x))]
				#for ip in attributes:
				#	try:ret = db_gen(die.uncore.getbypath(ip))
				#	except:pass
			
			for die in computes:
				### COMPUTE -> UNCORE
				find_component(die, portid=None, component='uncore', db=True)
				find_component(die, portid=None, component='cpu', db=True)
				find_component(die, portid=None, component='fuses', db=True)
				#print("COMPUTES:UNCORE")
				#ret = db_gen(die.uncore)
				
				#attributes_and_methods = dir(die.uncore)
				#attributes_and_methods = [x for x in attributes_and_methods if not x.startswith('_')]
				#attributes = [x for x in attributes_and_methods if 'target_info' in dir(die.uncore.getbypath(x))]
				#for ip in attributes:
				#	try:ret = db_gen(die.uncore.getbypath(ip))
				#	except:pass

	f = open(r"C:\Temp\portid_to_path.csv", 'w', newline='')
	writer = csv.writer(f)
	for item in sorted(ret_csv, key=lambda x: x[1:]): writer.writerows([item])
	print(r"portid_to_path.csv is saved at C:\Temp\portid_to_path.csv")
	
	try:
		import pandas as pd
		import numpy as np
		df = pd.read_excel('{}'.format(filename))
		for index, row in df.iterrows():
			if not np.isnan(row[9]):
				if hex(int(row[9])) in [x[0] for x in ret_csv]:
					path = [x[2] for x in ret_csv if x[0] == hex(int(row[9]))][0]
					df.at[index, 'Path'] = path
		df.to_excel('{}'.format(filename), index=False)
		print("Added paths to the excel sheet : {}".format(filename))
	except:pass
	return True