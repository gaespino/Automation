## GNR DFF Data Collector
#
# Update: 3/6/2025
# Version: 1.5
# Last Update notes: Added the following features:
# - Code Modularity to include BASELINE of multiproducts
#
## Revision: 1.3
## Date: 20/01/2025
## Edit: gabriel.espinoza.ballestero@intel.com
## update: Added a new interface located in the UI folder, this will replace the previous args option.
## 
## 
## Revision: 1.2
## Date: 20/06/2024
## Edit: gabriel.espinoza.ballestero@intel.com
## update: Added offline mode for the DFF data collector as well as the core option. Script can be used from platform or from the Q drive:
## Use command prompt line: python Q:\Gaespino\scripts\s2t\GNRDffDataCollector.py -vid {UnitVID} -option {core / uncore}
## EXample: python Q:\Gaespino\scripts\s2t\GNRDffDataCollector.py -vid 74GC556700043 -option core
##
## Revision: 1.1
## Date: 16/04/2024
## Edit: gabriel.espinoza.ballestero@intel.com
##
## Script used to save DFF data from units, DFF data needs to be at site for the script to pull the required data.

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import os
from dataclasses import dataclass

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import GNRGetTesterCurves as gtc
import UI.GNRDffDataUI as dff

classLogical2Physical = gtc.classLogical2Physical#{0:0, 1:1, 2:2, 3:3, 4:6, 5:7, 6:8, 7:9, 8:10, 9:13, 10:14, 11:15, 12:16, 13:17, 14:20, 15:21, 16:22, 17:23, 18:24, 19:27, 20:28, 21:29, 22:30, 23:31, 24:34, 25:35, 26:36, 27:37, 28:38, 29:41, 30:42, 31:43, 32:44, 33:45, 34:48, 35:49, 36:50, 37:51, 38:52, 39:55, 40:56, 41:57, 42:58, 43:59}
physical2ClassLogical = gtc.physical2ClassLogical#{v:k for k, v in log2Phys10x5.items()}
CORESTRING = gtc.CORESTRING
MAXLOGICAL = gtc.MAXLOGICAL
MAXPHYSICAL = gtc.MAXPHYSICAL
SELECTED_PRODUCT = gtc.SELECTED_PRODUCT
PRODUCT_CONFIG = gtc.PRODUCT_CONFIG

options = ['core','uncore']
debug = False

class datacollector:
	def __init__(self):
		self.classLogical2Physical = classLogical2Physical
		self.physical2ClassLogical = physical2ClassLogical
		self.CORESTRING = CORESTRING
		self.MAXLOGICAL = MAXLOGICAL
		self.MAXPHYSICAL = MAXPHYSICAL
		self.SELECTED_PRODUCT = SELECTED_PRODUCT
		self.PRODUCT_CONFIG = PRODUCT_CONFIG

	def max_difference(self, a, b, c):
		# Create a list of the three values
		if type(a) == str:
			a = float(a)
		if type(b) == str:
			b = float(b)
		if type(c) == str:
			c = float(c)

		values = [a, b, c]
		
		if a==b==c:
			max_diff = 0
		else:
			# Calculate the maximum difference
			max_diff = max([abs(i - j) for i in values for j in values if i != j])
		
		return max_diff

	def uncore_collect(self, vidfile, outputfile ='C:\\Temp\\uncore_vmin_dump.xlsx' , flow = ['hot', 'cold']):
		print(f'Starting data collection for {self.SELECTED_PRODUCT}')
		_isfile = self.checkfile(vidfile)

		if _isfile: 
			with open(vidfile , 'r') as file:
				vids = [line.strip() for line in file]
				file.close()
		else:
			vids = [vidfile]

		data = {}

		visualIDs = vids
		
		Savedata = {'VisualID': [], 
					'COMPUTE':[],
					'IP':[],
					'Freq':[],
					'Flow':[],
					'Voltage':[],
					'Compare':[],
					'IPCompare':[]
					}
		for flw in flow:
			for vid in visualIDs:
				print(f'Collecting data for {vid} - {flw.upper()}')
				if flw == 'hot': 
					hotf = True
					temp = "HSTC_V"
					custom = False
				elif flw == 'custom':
					hotf = True
					custom = True
					temp = temp = "FAST_STC_V"
				else: 
					hotf = False
					temp = "CSTC_V"
					custom = False
				data = gtc.dump_uncore_curves(visual= vid, hot = hotf, usedata = True, custom=custom, temp=temp)
				Frequencies = {'HDC':[], 'CFC':[],'IO':[]}

				for key, value in data.items():
					key_string = key.split('-')
					freq = key_string[2]
					compute = key_string[0]
					ip = key_string[1]
					fvalue = float(value)

					Savedata['VisualID'].append(vid)
					Savedata['COMPUTE'].append(compute)
					Savedata['IP'].append(ip)
					if 'hot' == flw.lower(): 
						Savedata['Flow'].append('HOT')
					elif 'cold' == flw.lower():
						Savedata['Flow'].append('COLD')
					elif 'custom' == flw.lower():
						Savedata['Flow'].append(temp)
					Savedata['Freq'].append(freq)
					Savedata['Voltage'].append(fvalue)
					if 'COMPUTE' in compute:
						Savedata['Compare'].append(self.max_difference(data[f'COMPUTE0-{ip}-{freq}-Voltage'],data[f'COMPUTE1-{ip}-{freq}-Voltage'],data[f'COMPUTE2-{ip}-{freq}-Voltage']))
					else:
						Savedata['Compare'].append(abs(float(data[f'IO0-{ip}-{freq}-Voltage'])-float(data[f'IO1-{ip}-{freq}-Voltage'])))
					if (ip == 'CFC' or ip == 'HDC') and 'COMPUTE' in compute and self.SELECTED_PRODUCT != 'CWF':
						Savedata['IPCompare'].append(abs(float(data[f'{compute}-CFC-{freq}-Voltage'])-float(data[f'{compute}-HDC-{freq}-Voltage'])))
					else:
						Savedata['IPCompare'].append(0)


		# Create a DataFrame from the dictionary
		df = pd.DataFrame(Savedata)

		# Write the DataFrame to Excel
		df.to_excel(outputfile, index=False)

	def core_collect(self, vidfile, outputfile ='C:\\Temp\\core_vmin_dump.xlsx',coremin=0, coremax=132,  flow = ['hot', 'cold'], skipfused = True):
		print(f'Starting data collection for {self.SELECTED_PRODUCT}')
		_isfile = self.checkfile(vidfile)

		if _isfile: 
			with open(vidfile , 'r') as file:
				vids = [line.strip() for line in file]
				file.close()
		else:
			vids = [vidfile]
			

		data = {}
		cores = [coremin,coremax]
		visualIDs = vids
		
		Savedata = {'VisualID': [], 
					'COMPUTE':[],
					f'{self.CORESTRING}LOG':[],
					f'{self.CORESTRING}PHY':[],
					'LIC':[],
					'Freq':[],
					'Flow':[],
					'Voltage':[],
	#                'Compare':[],
	#                'IPCompare':[]
					}
		for flw in flow:
			for vid in visualIDs:
				print(f'Collecting data for {vid} - {flw.upper()}')
				if flw == 'hot': 
					hotf = True
					temp = "HSTC_V"
					custom = False
				elif flw == 'custom':
					hotf = True
					custom = True
					temp = temp = "FAST_STC_V"
				else: 
					hotf = False
					temp = "CSTC_V"
					custom = False
	#           for c in range(cores):
				data = gtc.dump_core_curves(visual= vid, core= cores, product= self.PRODUCT_CONFIG, hot = hotf, usedata=True, custom=custom, temp=temp)
	#			Frequencies = {'HDC':[], 'CFC':[],'IO':[]}

				for key, value in data.items():
					key_string = key.split('-')
					freq = key_string[2]
					core = key_string[0]
					ip = key_string[1]
					fvalue = float(value)
					if fvalue < 0 and skipfused:
						continue				
					Savedata['VisualID'].append(vid)
					corelognum = int(core.replace(f'{self.CORESTRING}',""))
					Savedata[f'{self.CORESTRING}LOG'].append(corelognum)
					compute = (int(corelognum/self.MAXLOGICAL))
					corephy = self.classLogical2Physical[(corelognum%self.MAXLOGICAL)]+(compute*self.MAXPHYSICAL)
					Savedata[f'{self.CORESTRING}PHY'].append(corephy)
					Savedata['COMPUTE'].append(compute)
					Savedata['LIC'].append(ip)
					if 'hot' == flw.lower(): 
						Savedata['Flow'].append('HOT')
					elif 'cold' == flw.lower():
						Savedata['Flow'].append('COLD')
					elif 'custom' == flw.lower():
						Savedata['Flow'].append(temp)
					Savedata['Freq'].append(freq)
					Savedata['Voltage'].append(fvalue)


		# Create a DataFrame from the dictionary
		df = pd.DataFrame(Savedata)

		# Write the DataFrame to Excel
		df.to_excel(outputfile, index=False)

	def checkfile(self, file_path):
		if os.path.exists(file_path):
			return True
		else:
			return False

	def run(self, flow, option, vid, output, skipfused = True):
		
		if flow == 'all':
			flows = ['hot','cold']	
		else:
			flows = [flow.lower()]
		print(f'Starting data collection for {option}, please wait until operation is complete')
		if option.lower() == 'uncore':
			
			self.uncore_collect(vidfile=vid, outputfile = output , flow = flows)
		elif option.lower() == 'core':
			self.core_collect(vidfile = vid, outputfile = output, coremin=0, coremax=132,  flow = flows, skipfused = skipfused)
		else:
			print('Option not availabled use core or uncore for file dump')

		print(f'Data collection file saved at: {output}')    	
	
	def update_product(self, product, config):

		gtc.set_variables(product, config)
		self.classLogical2Physical = gtc.classLogical2Physical#{0:0, 1:1, 2:2, 3:3, 4:6, 5:7, 6:8, 7:9, 8:10, 9:13, 10:14, 11:15, 12:16, 13:17, 14:20, 15:21, 16:22, 17:23, 18:24, 19:27, 20:28, 21:29, 22:30, 23:31, 24:34, 25:35, 26:36, 27:37, 28:38, 29:41, 30:42, 31:43, 32:44, 33:45, 34:48, 35:49, 36:50, 37:51, 38:52, 39:55, 40:56, 41:57, 42:58, 43:59}
		self.physical2ClassLogical = gtc.physical2ClassLogical#{v:k for k, v in log2Phys10x5.items()}
		self.CORESTRING = gtc.CORESTRING
		self.MAXLOGICAL = gtc.MAXLOGICAL
		self.MAXPHYSICAL = gtc.MAXPHYSICAL
		self.SELECTED_PRODUCT = gtc.SELECTED_PRODUCT
		self.PRODUCT_CONFIG = gtc.PRODUCT_CONFIG
		print(self.SELECTED_PRODUCT , self.MAXLOGICAL,self.MAXPHYSICAL)

## Interface
def UI():
	collector = datacollector()
	dff.callUI(collector)


if __name__ == "__main__":
	UI()
	