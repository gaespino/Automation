#import sapphirerapids.execution.USBPowerSplitter as usbps
#import sapphirerapids.toolext.bootscript.boot as b
#import sapphirerapids.users.kwadams.debug.utils as u

#import svtools.common.baseaccess as _baseaccess

#from pysvtools.server_ip_debug.cha import cha
#from pysvtools.server_ip_debug.mdf import mdf

#from asyncore import read
import datetime
#import ipccli
#itp = ipccli.baseaccess()
#import namednodes

import os
import shutil
import subprocess
import sys
import time
import pandas as pd
import getpass
#import traceback

#import win32gui
#import win32con
#import win32api
#import winreg

import re
import csv

from os.path import exists
from turtle import end_fill
import statistics

product = 'gnr'
path = r'C:\ParsingFiles\GNR\Masks_GNR\MaskingFile_001.csv'

#path = 'Q:\\Gaespino\\GNR\\EMR_fuse_check.csv'#EMR_fuse_check

try:
	#my try
	verbose = False
	i = 0
	for item in sys.argv:
		if item == "-v" or item == "-verbose" or item== "--verbose":
			verbose = True
		if item == "-dat" or item == "-datafile" or item == "-s" or item == "--datafile":
			path = sys.argv[i+1]
		if item == "-prod" or item == "-product" or item == "-p" or item == "--product":
			product = sys.argv[i+2]
		i += 1
#	main(path)
#
except IndexError:
  print("Error: Invalid format\n")
  print("Valid format: \n \n spr_data_processing.py -dat <Path to Datafile> -v (Verbose: Optional)\n \n ")
  sys.exit(2)



# Here starts new code

def read(path):
	with open(path,'r', newline= '\n') as csvinput:

		scriptHome = os.path.dirname(os.path.realpath(__file__))
		inputFile = open(path)
		o_path = re.sub(r'\.csv$','',path)
		o_dir = o_path+'_processed.csv'
		headers = []
		columns = []
		datafile = csv.reader(csvinput)
		#header = (datafile[0])
		#headers = (headers).split(',')
	   # rows = next(datafile)

		for row in datafile:
			if not columns:
				columns = [[] for _ in row]
			for i, value in enumerate(row):
				columns[i].append(value)

		data = {i[0]: i for i in columns}

	return data

def qdf_parse(path):
	## Read aque reported data
	data = read(path)

	split_pat= [
				'^', #qdfsplit = '^'
				'~' ,#fusesplit = '|'
				'|' #fusesplit old = '|'
				]


	patterns = {
			'VID': r'VISUAL_ID',	#Bucket QDF
			'QDF_B': r'.*BUCKET_QDFS.*',	#Bucket QDF
			'QDF_P': r'.*PASSING_QDFS.*',	#Passing QDF
			'LLC_C1': r'.*FUSECDIEA.*HWRS_TOP_RAM_IP_DISABLE_FUSES_DWORD2_LLC_DISABLE.*',	#cOMPUTE 1 LLC MAKS
			'LLC_C2': r'.*FUSECDIEB.*HWRS_TOP_RAM_IP_DISABLE_FUSES_DWORD2_LLC_DISABLE.*',	#cOMPUTE 2 LLC MAKS
			'LLC_C3': r'.*FUSECDIEC.*HWRS_TOP_RAM_IP_DISABLE_FUSES_DWORD2_LLC_DISABLE.*',	#cOMPUTE 3 LLC MAKS
			'CORE_C1': r'.*FUSECDIEA.*HWRS_TOP_RAM_IP_DISABLE_FUSES_DWORD6_CORE_DISABLE.*',	#cOMPUTE 1 LLC MAKS
			'CORE_C2': r'.*FUSECDIEB.*HWRS_TOP_RAM_IP_DISABLE_FUSES_DWORD6_CORE_DISABLE.*',	#cOMPUTE 2 LLC MAKS
			'CORE_C3': r'.*FUSECDIEC.*HWRS_TOP_RAM_IP_DISABLE_FUSES_DWORD6_CORE_DISABLE.*',	#cOMPUTE 3 LLC MAKS
	}

	patdata = {}

	VID = next(iter(data.keys()))

	for key in data.keys():
		#for pattern in patterns:
		content = data[key]
		for patkey in patterns.keys():
			if (re.search(patterns[patkey], key)) :
				patdata[patkey] = patfinder(content, split_pat)

	index = 0
	xlsdata = {
		'VISUAL_ID': [],
		'BUCKET_QDF': [],
		'FUSES::CORE::COMPUTE1': [],
		'FUSES::LLC::COMPUTE1': [],
		'FUSES::CORE::COMPUTE2': [],
		'FUSES::LLC::COMPUTE2': [],
		'FUSES::CORE::COMPUTE3': [],
		'FUSES::LLC::COMPUTE3': [],
	}

	for vid in patdata['VID']:
		vididx = patdata['VID'].index(vid)
		for qdfb in patdata['QDF_B'][vididx]:
			xlsdata['VISUAL_ID'].append(vid[0])
			xlsdata['BUCKET_QDF'].append(qdfb)
			index = patdata['QDF_B'][vididx].index(qdfb)
			#if qdfb == '':
			#	continue
			# Look for data based on QDF index and append to new dict
			# Cpmpute 1 Fuse Data for QDF
			xlsdata['FUSES::CORE::COMPUTE1'].append(patdata['CORE_C1'][vididx][index] if qdfb != '' else '')
			xlsdata['FUSES::LLC::COMPUTE1'].append(patdata['LLC_C1'][vididx][index] if qdfb != '' else '')
			# Cpmpute 2 Fuse Data for QDF
			xlsdata['FUSES::CORE::COMPUTE2'].append(patdata['CORE_C2'][vididx][index] if qdfb != '' else '')
			xlsdata['FUSES::LLC::COMPUTE2'].append(patdata['LLC_C2'][vididx][index] if qdfb != '' else '')
			# Cpmpute 3 Fuse Data for QDF
			xlsdata['FUSES::CORE::COMPUTE3'].append(patdata['CORE_C3'][vididx][index] if qdfb != '' else '')
			xlsdata['FUSES::LLC::COMPUTE3'].append(patdata['LLC_C3'][vididx][index] if qdfb != '' else '')

	xlswrite(path,xlsdata)

def legacy_qdf_parse(path):
	## Read aque reported data
	data = read(path)

	split_pat= [
				'^', #qdfsplit = '^'
				'~' #fusesplit = '~'
				]


	patterns = {
			'VID': r'VISUAL_ID',	#Bucket QDF
			'QDF_B': r'.*BUCKET-QDFS.*',	#Bucket QDF
			'QDF_P': r'.*PASSING-QDFS.*',	#Passing QDF
			'LLC_C1': r'.*_LLC_SLICE_DISABLE.*',	#LLC MASKS
#			'LLC_C2': r'.*U4HWRS_TOP_RAM_IP_DISABLE_FUSES_DWORD2_LLC_DISABLE.*',	#cOMPUTE 2 LLC MAKS
#			'LLC_C3': r'.*U5HWRS_TOP_RAM_IP_DISABLE_FUSES_DWORD2_LLC_DISABLE.*',	#cOMPUTE 3 LLC MAKS
			'CORE_C1': r'.*_IA_CORE_DISABLE.*',	#CORES MASK
#			'CORE_C2': r'.*U4HWRS_TOP_RAM_IP_DISABLE_FUSES_DWORD6_CORE_DISABLE.*',	#cOMPUTE 2 LLC MAKS
#			'CORE_C3': r'.*U5HWRS_TOP_RAM_IP_DISABLE_FUSES_DWORD6_CORE_DISABLE.*',	#cOMPUTE 3 LLC MAKS
			'HCX': r'.*_DISABLE_HCX.*',	#HCX MASK
			'MC': r'.*_DISABLE_MC.*',	#MC MASK
			'PI5': r'.*_DISABLE_PI5.*',	#PI5 MASK
			'SCF_IO': r'.*_DISABLE_SCF_IO.*',	#SCF_IO MASK
			'UPI': r'.*_DISABLE_UPI.*',	#UPI MASK
	}

	patdata = {}

	VID = next(iter(data.keys()))

	for key in data.keys():
		#for pattern in patterns:
		content = data[key]
		for patkey in patterns.keys():
			if (re.search(patterns[patkey], key)) :
				patdata[patkey] = patfinder(content, split_pat)

	index = 0
	xlsdata = {
		'VISUAL_ID': [],
		'BUCKET_QDF': [],
		'FUSES::CORE::COMPUTE': [],
		'FUSES::LLC::COMPUTE': [],
		'FUSES::HCX::IO': [],
		'FUSES::MC::IO': [],
		'FUSES::PI5::IO': [],
		'FUSES::SCF_IO::IO': [],
		'FUSES::UPI::IO': [],
	}

	for vid in patdata['VID']:
		vididx = patdata['VID'].index(vid)
		for qdfb in patdata['QDF_B'][vididx]:
			xlsdata['VISUAL_ID'].append(vid[0])
			xlsdata['BUCKET_QDF'].append(qdfb)
			index = patdata['QDF_B'][vididx].index(qdfb)

			# Look for data based on QDF index and append to new dict
			# Cpmpute 1 Fuse Data for QDF
			xlsdata['FUSES::CORE::COMPUTE'].append(patdata['CORE_C1'][vididx][index])
			xlsdata['FUSES::LLC::COMPUTE'].append(patdata['LLC_C1'][vididx][index])
			# Cpmpute 2 Fuse Data for QDF
			xlsdata['FUSES::HCX::IO'].append(patdata['HCX'][vididx][index])
			xlsdata['FUSES::MC::IO'].append(patdata['MC'][vididx][index])
			# Cpmpute 3 Fuse Data for QDF
			xlsdata['FUSES::PI5::IO'].append(patdata['PI5'][vididx][index])
			xlsdata['FUSES::SCF_IO::IO'].append(patdata['SCF_IO'][vididx][index])
			xlsdata['FUSES::UPI::IO'].append(patdata['UPI'][vididx][index])

	xlswrite(path,xlsdata)

def xlswrite(path, data):

	scriptHome = os.path.dirname(os.path.realpath(__file__))
	current_user = getpass.getuser()
	o_path = re.sub(r'\.csv$','',path)
	#filename = os.path.basename(path)
	xlsfile = o_path + '_filtered.xlsx'
	# Create a DataFrame from the dictionary
	df = pd.DataFrame(data)

	# Write the DataFrame to Excel
	df.to_excel(xlsfile, index=False)

def patfinder(content, split_pat):
	dataline = []
	if re.search('QDFS', content[0]) :
		_splitpat = split_pat[0]
	else:
		_splitpat = split_pat[1]

	for cont in content[1:]:
		if _splitpat == '~':
			_dataline = [s for s in cont.split(_splitpat) if s]
		else:
			_dataline = cont.split(_splitpat)

		dataline.append(_dataline)

	return dataline

if __name__ == '__main__' :
	if product == 'emr':
		legacy_qdf_parse(path)
	elif product == 'spr':
		legacy_qdf_parse(path)
	elif product == 'gnr':
		qdf_parse(path)
