# #################################
#          ShmooPlotter
# #################################
# Version: 1.1
# Developer: Gabriel Espinoza Ballestero
# Date: 1/26/2024
#
# Description:
# Plots from the Parsed data file, all the Shmoos into an xlsx or image files, whis script uses as input the result of, 
# ShmooParser.
#
# Debug:
# There is a debug flag inside the code, if debug is required set this flag to True, and set the appropiate arguments manually in the debug section of the argpaser.
#
# Developer Notes: 
#	- Updated with arguments, color pallete is limited to 3 options, it can be further increased, just check the cmap color options for seaborn if needed
#	- Excel file does not print any color in the file, it does include the legend and the tabs if vid is found will be added to its name, in other cases the
#		tab name will be a sequence of number in the format of plot##.
#	- Format used for the plot images is jpg, and uses seaborn and panda dataframes, if your system does not have those libraries, use a virtual environment and install.
#	- Code can be called from console using the following : ShmooPlotter.py [-h] -log LOG [-plot {all,img,xls}] [-vid VID] [-color {Reds,Blues,Greens}]
#
# Intel 2024


import os
import sys
import re
import getpass 
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
#import collections
import argparse
from matplotlib.patches import Patch
from matplotlib.colors import rgb2hex, colorConverter
from matplotlib.collections import QuadMesh
from openpyxl import load_workbook
import shutil


# Optional variables, printfile is only used to display a message once, debug by default False, if True configure manually the args values inside the argparser debug section.
debug = False
excel_printfile = None
filelist = []

# Arguments definition, use -h in console for detailed info.
def argparser(debug):
	if not debug:
		parser = argparse.ArgumentParser()

		# Add Argument list below
		parser.add_argument('-log', type=str, required= True,
							help = "Shmoo processed logfile to be used for plotting")
		parser.add_argument('-plot', type=str, choices=['all', 'img', 'xls'], default='xls',
							help = "Plot type to be used, image (img): jpg file, excel file (xls) or all for both. Default is xls")
		parser.add_argument('-vid', type=str, default='', required= False,
							help = "Visual ID of the unit to be displayed on image title and excel tabnames")
		parser.add_argument('-color', type=str, choices=['Reds', 'Blues', 'Greens'], default='Reds', required= False,
							help = "Color palette to be used for the image file plot. Default is Blues")
		parser.add_argument('-color', type=str, choices=['Reds', 'Blues', 'Greens'], default='Reds', required= False,
							help = "Color palette to be used for the image file plot. Default is Blues")
		parser.add_argument('-axis', choices=['none', 'auto'], default= 'none', type=str, required= False,
							help = 'Checks for min/max values of x and y axis, and accomodates data to plot automatically if auto is selected')

		args = parser.parse_args()
	
	# Default arguments for debug mode of the script
	else:
		class Args:
			plot = 'all'
			log = r'C:\\ParsingFiles\\VPO_J412026RV_ItuffData\\J412026RV_5261_chk_1_20240320005130_QAHOT\\ShmooParsed_data.txt'
			vid = ''
			color = 'Blues'
			axis = 'none'
		args = Args()
	
	return args

# plot_data: Creates all the necessary arrays to be used for the plots, such as Data, axis and legends
def axis_build(map_line):
	xaxis = 'XAXIS:'
	yaxis = 'YAXIS:'
	yfound = xfound = False
	
	for line in map_line:
		if xaxis in line:
			axis = line.split(' ')
			index = axis.index('by')
			
			x_axis = {
			'name':axis[index - 4],
			'start':float(axis[index - 3]), 
			'end':float(axis[index - 1]),
			'step':float(axis[index + 1]),  
			}
			xfound = True
		elif yaxis in line:
			axis = line.split(' ')
			index = axis.index('by')
			
			y_axis = {
			'name':axis[index - 4],
			'start':float(axis[index - 3]), 
			'end':float(axis[index - 1]),
			'step':float(axis[index + 1]),  
			}
			yfound = True
		
		elif yfound and xfound:
			break
		
		else:
			continue
		
	return (x_axis, y_axis)
	
def plot_data(file, VID = '', axisfix = 'none', source = 'tester'):
	FileN = ''
	PLISTN = ''
	INSTANCEN = ''
	data = {
		'X':[],
		'Y':[],
		'legend':[],
		'Data':[],
		'Data_list':[],
		'VID':[],
		'Filename':[],
		'Plist':[],
		'Instance':[],
		'Axis':[],
		'Type':'Shmoo'
		}
	patterns = [
		r'\|[A-Za-z\*]',  # Pattern 1
		r'\+[A-Za-z\*]',  # Pattern 2
	]
	data_list = []
	data_array = []
	legend = ['* = All patterns passed the test']

	map_lines = file.split('\n')
	
	# index word - this line contains the required index data, might have to revisit in case of more complicated shmoos - deprecated
	word = '0_tname'
	
	# Search for the index word - deprecated
	index = next((i for i, elem in enumerate(map_lines) if word in elem), -1)
	
	x_axis, y_axis = axis_build(map_lines)
	
	## Old code for axis location
	# Builds the axis data for the plot
	#axis = map_lines[index].split('^')
	#x_axis = {
	#	'name':axis[1],
	#	'start':float(axis[2]), 
	#	'end':float(axis[3]),
	#	'step':float(axis[4]),  
	#	}
	#y_axis = {
	#	'name':axis[5],
	#	'start':float(axis[6]), 
	#	'end':float(axis[7]),
	#	'step':float(axis[8]),  
	#	}
	for line in map_lines:
		if re.search(r'REPEAT_N', line):
			data['Type'] = 'Repeat'	
			#Change Patterns
			patterns = [
			r'\|[0-9A-Za-z\*]',  # Pattern 1
			r'\+[0-9A-Za-z\*]',  # Pattern 2
			]
			break
	
	skipwords = [
		'FUSE_CONFIG_CALLBACKS',  		# Pattern 1
		"DIE_RECOVERY",        	# Pattern 2
		"FILE:"		# Pattern 3
		"2_tname_HWALARM"		# Pattern 3
	]

	# Builds the array for Shmoo data, remove any non needed character
	for line in map_lines:
		skipword = False
		# Look for key values such as plist, pattern, legends,...
		if source == 'ituff_gnr' or source =='gnr':
			if re.search(r'\= .*:g', line) or  re.search(r'\= .*:d', line):
				_legend = line.replace(" ","").split(':')
				_pattern = f'{_legend[0]}:{_legend[1]}'
				_plist = _legend[0]
				_vector= _legend[2]
				_misc= _legend[3]
				legend.append(_pattern)
				continue
		else:
			if re.search(r'\= g', line) or  re.search(r'\= d', line):
				_legend = line.replace(" ","").split(':')
				_pattern = _legend[0]
				_plist = _legend[1]
				_vector= _legend[2]
				legend.append(_pattern)
				continue
			if re.search(r'Alarm Type', line):
				alrm = f'** = {line}'
				legend.append(alrm)
				continue
		# Important, string searched below is based on what the Parser prints at the end of every shmoo data array
		if re.search(r'Unit VID = ', line) and VID == '':
			VID = line.replace('Unit VID = ',"")
			continue
		#else:
		#	VID = ''
		if re.search(r'FILE:', line):
			FileN = line.replace('FILE:',"").split('\\')[-1]
			continue
		if re.search(r'PLIST:', line):
			PLISTN = line.replace('PLIST:',"").split('\\')[-1]
			continue
		if re.search(r'INSTANCE:', line):
			INSTANCEN = line.replace('INSTANCE:',"").split('\\')[-1]
			continue

		# Checks for any word to skip
		for skipw in skipwords:
			if skipw in line:
				skipword = True
				break
		if skipword:
			continue	
		
		# Remove the spaces in case we are using a Repeat N Shmoo
		for pattern in patterns:
			if data['Type'] == 'Repeat':
				nline = line.replace(" ","")
			else:
				nline = line
			

			if re.search(pattern, nline):
				if not re.search(r'\+\-\-', nline):
					#_data = line.split('+')
					#_data = _data[-1]
					_data = re.sub(r'.*[\+\|]', "", nline)
					_data = re.sub(r'\[.*', "", _data)
					_data = _data.replace(" ","")
					data_list.append(_data)
					_data_array = [char for char in _data]
					data_array.append(_data_array)

		


		#else:
		#	FileN = ''
			
	# Data structuring, also checing if x/y axis are inverted to either increment/decrement based on step size
	if data_list: 
		column_labels = len(data_list[0])
		row_labels = len(data_list)
		axisfix_x = False
		axisfix_y = False
		axisfix_y_order = False

		if x_axis['start'] > x_axis['end']:
			x_values = [format_number(number = (x_axis['start'] - i * x_axis['step'])) for i in range(column_labels)]
			if 'auto' in axisfix: axisfix_x = True

		else:
			x_values = [format_number(number = (x_axis['start'] + i * x_axis['step'])) for i in range(column_labels)]


		if y_axis['start'] > y_axis['end']:
			y_values = [format_number(number = (y_axis['start'] - i * y_axis['step'])) for i in range(row_labels)]
			if 'auto' in axisfix: axisfix_y = True		
			
		else:
			y_values = [format_number(number = (y_axis['start'] + i * y_axis['step'])) for i in range(row_labels)]
			if 'auto' in axisfix: axisfix_y_order = True	
					
		if 'auto' in axisfix:
			if axisfix_x:
				x_values.reverse()
				reversed_data = [sublist[::-1] for sublist in data_array]
				data_array = reversed_data

			if axisfix_y:
				y_values.reverse()
				data_array.reverse()
				data_list.reverse()
			
			if axisfix_y_order:
				y_values.reverse()
				
		# Based on how data is being generated needed to reverse this by default		
		#if source == 'ituff' or source == 'ituff_gnr': y_values.reverse()

		data['X'] = x_values
		data['Y'] = y_values #.reverse()
		
		data['Axis'] = [x_axis["name"], y_axis["name"]]
		data['Data'] = data_array
		
		data['Data_list'] = data_list
		data['legend'] = legend
		data['VID'] = VID
		data['Filename'] = FileN
		data['Plist'] = PLISTN
		data['Instance'] = INSTANCEN
	else:
		data = []
	return (data)

def format_number(number):
    # Define the threshold below which numbers should be displayed in scientific notation
    threshold = 1e-3
    
    # Check if the absolute value of the number is below the threshold
    if abs(number) < threshold:
        # Format the number in scientific notation
        return f"{number:.2E}"
    else:
        # Format the number normally
        return str(round(number,2))
	
# excel plot: Code to create the report file in an excel file, if file exists it replaces it and if is not it creates it, if multiple plots are used (pltnum > 1), 
# 	only first plot is overwriten the following will append and add a nrw tab for each plot.
def excel_plot(data, o_dir, pltnum):	
	filename = os.path.basename(o_dir)
	o_path = re.sub(filename,'',o_dir)
	filename = re.sub(r'\.txt$','',filename)
	filename = re.sub(r'_Clean','',filename)
	global excel_printfile
	
	# Excel file appends the ShmooReport text at the end of the used logfile, not much here.
	output_file = f'{o_path}{filename}_ShmooReport.xlsx'

	# Naming sheet of excel file based on VID data, if there is any
	if pltnum == '':
		pltnum = 0

	if len(data['VID'] ) == 0:
		sht_name = f"plot{pltnum:02d}"
	else:	
		sht_name = f"plot{pltnum:02d}_{data['VID']}"

	# Reassigning dict data to individual variables, mostly for easy of use in code.

	data_list = data['Data_list']
	xlslegend = data['legend'].copy()
	
	x_values = data['X']
	y_values = data['Y']
	file_n = data['Filename']
	plist_n = data['Plist']
	inst_n = data['Instance']
	Axis_n = data['Axis']
	data_array = data['Data'] 
	xdata = f'XAXIS: {Axis_n[0]}'
	xlslegend.append(xdata)
	ydata = f'YAXIS: {Axis_n[1]}'
	xlslegend.append(ydata)
	fdata = f'FILE: {file_n}'
	xlslegend.append(fdata)
	idata = f'INSTANCE: {inst_n}'
	xlslegend.append(idata)
	pdata = f'PLIST: {plist_n}'
	xlslegend.append(pdata)
	# Building pandas dataframes to be usde in excel,
	legend_df = pd.DataFrame({'Legend': xlslegend})
	df = pd.DataFrame(data_array, index=y_values, columns=x_values)

	# Just wanted to print one message, excel file does not change, might be implemented on a better way, probably changing this.
	lastprint = f'PLOT MSG: Editing Excel file: {output_file}'
	if excel_printfile != lastprint: 
		print (lastprint)
		excel_printfile = lastprint
	
	print (f'PLOT MSG: Creating new sheet for shmoo report: {sht_name}')
	
	# Write Excel file with the data
	if pltnum == 1 or pltnum == 0: 
		with pd.ExcelWriter(output_file, engine='openpyxl', mode='w') as writer:
			
			legend_df.index += len(df) + 2
			legend_df.to_excel(writer, sheet_name=sht_name, startrow=len(df) + 2, index=False, header=False)
			df.to_excel(writer, sheet_name=sht_name,startrow=0, index=True, header=True)
	else:
		with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists = 'overlay') as writer:
			
			legend_df.index += len(df) + 2
			legend_df.to_excel(writer, sheet_name=sht_name, startrow=len(df) + 2, index=False, header=False)
			df.to_excel(writer, sheet_name=sht_name,startrow=0, index=True, header=True)

# image plot: Code allowing to build the output plot image file.
def image_plot(data, o_dir, pltnum, palette = 'Reds'):
	filename = os.path.basename(o_dir)
	o_path = re.sub(filename,'',o_dir)
	filename = re.sub(r'\.txt$','',filename)
	filename = re.sub(r'_Clean','',filename)
	img_type = 'jpg'
	# Create a new directory for the image results to be stored
	o_path = os.path.join(o_path, 'Plots')
	#plot_folder = os.path.join(parse_folder, "Plots")

	os.makedirs(o_path, exist_ok=True)
	
	# Developer option, default to highligt max color and * to green, option 1 makes it behave as a heatmap
	devopt = 0
	if type(pltnum) == str: pltnum = 1
	# Name the output file use consecutive numbering if we have multiple plots in the same file
	if data['VID'] != '':
		if re.search(rf"{data['VID']}", filename):
			output_file = f'{o_path}/{filename}_plot{pltnum:02d}.{img_type}'
		else:
			output_file = f'{o_path}/{filename}_plot{pltnum:02d}_{data["VID"]}.{img_type}'
	else:
		output_file = f'{o_path}/{filename}_plot{pltnum:02d}.{img_type}'
	
		
	data_list = data['Data_list']
	legend = data['legend']
	x_values = data['X']
	y_values = data['Y']
	file_n = data['Filename']
	plist_n = data['Plist']
	inst_n = data['Instance']
	Axis_n = data['Axis']
	data_array = data['Data'] 
	
	# Set the title if there is any VID variable found in text or argument input
	Title = f'{Axis_n[0]} vs {Axis_n[1]} Shmoo:'

	if len(data['VID'] ) > 0:
		Title = f"{Axis_n[0]} vs {Axis_n[1]} Shmoo: {data['VID']}"
	
	if file_n != '':
		Title = f"FILE: {file_n} \n" + Title

	# Checks for devopt color configuration by default reds - This might be deleted in the future, devopt 1 uses a value for each letter and assings a value to each, 
	# 	this implementation was replaced with the count of each letter to assign the value, allowing a better visualization.
	if devopt ==1: 
		array = np.array([list(map(lambda x: 0 if x == "*" else ord(x) - ord('A') + 1, line)) for line in data_list])
		cmap = 'Reds'
		
	else: 
		array, cmap, legend_colors = plot_colors(data_list, legend, palette)
	
	# Create plot Dataframe	
	df0 = pd.DataFrame(array, index=y_values, columns=x_values)

	# Create a heatmap
	fig, ax = plt.subplots(figsize=(8, 6))
	sns.heatmap(df0, cmap=cmap, annot=False, fmt='', linewidths=0.5, cbar=False)

	# Set legends to show the failing patterns based on the file data
	legend_elements = []
	for _legend in legend:
		x = _legend[0]
		if devopt == 1: 
			legnd_color = 'white'
		else: 
			try:
				legnd_color = legend_colors[x]
			except KeyError:
				legnd_color = cmap[0]	
		lgnd =  re.sub(r'.*[\=]', "", _legend)
		value = ord(x) - ord('A') + 1
		legend_elements.append(Patch(facecolor=legnd_color, edgecolor='black', label=f'{x} = {lgnd}'))
	
	if plist_n == '':
		axtitle = f'PLIST Failing patterns'
	else:
		axtitle = f'INSTANCE : {inst_n} \nPLIST : {plist_n}'

	ax.legend(handles=legend_elements, loc='upper center', title = axtitle, bbox_to_anchor=(0.5, -0.15), fontsize=10, framealpha=1, ncol=1)

	# Find the correct child artist that represents the heatmap plot
	heatmap_artist = None
	for artist in ax.get_children():
		if isinstance(artist, QuadMesh):
			heatmap_artist = artist
			break

	# Display the original alphanumeric value on each cell
	for i in range(len(data_array)):
		for j in range(len(data_array[i])):
			
			cell_color =heatmap_artist.get_facecolor()[i * len(data_array[i]) + j]
			cell_brightness = sum(colorConverter.to_rgb(cell_color))/ 3
			if cell_brightness < 0.5:
				letter_color = '#FFFFFF'  # White
			else:
				letter_color = '#000000'  # Black
			ax.text(j + 0.5, i + 0.5, data_array[i][j], ha='center', va='center', color=letter_color)

	# Add plot title
	plt.title(Title)
	

	# Save plot to an image file
	print (f'PLOT MSG: Creating Shmoo plot file - {output_file}')
	plt.savefig(output_file, format=img_type, bbox_inches='tight', pad_inches=0.05)
	plt.close(fig)

# plot colors: Flats the shmoo data to check for failing counts, based on the values obtained assigns the colors, "*" is set to the lowest value of the selected color
#	palette, here we also assign the same color palette to the legend boxes, and build the numerical array to be used by the seaborn heatmap library.
def plot_colors(data, legend_colors, palette):
	
	flat_data = [cell for row in data for cell in row]
	unique_letters, counts = np.unique(flat_data, return_counts=True)
	if '*' in unique_letters:
		asterisk_index = np.where(unique_letters == '*')[0][0]
		counts[asterisk_index] = 0

	letter_count = dict(zip(unique_letters, counts))
	array = np.array([list(map(lambda x: letter_count[x], line))for line in data]) 

	# Flatten the data array
	flat_data = [cell for row in data for cell in row]

	# Create a colormap based on the frequency
	cmap = sns.color_palette(palette, max(counts) + 1)

	legend_colors = {letter: '' for letter in unique_letters}
	
	for key in legend_colors:
		legnd_cnt = letter_count[key] 
		legend_colors[key] = cmap[legnd_cnt]
		

	return array, cmap, legend_colors

## DevNotes: Below is a placeholder for future updates, need to figure how to dynamically change Excel cell colors, havent found a nice way yet
def highlight_data(val):
	if '*' in val:
		return 'background-color: green'
	elif any(char.isalpha() for char in val):
		# Generate a different color for each letter A to Z
		char_color = ord(val[0].upper()) - ord('A')
		rgb_color = f'rgb({char_color * 10}, {char_color * 10}, {char_color * 10})'
		return f'background-color: {rgb_color}'
	else:
		return ''

# filed check: Section to check for keyword inside the Shmoo parsed file, this will allow for multiple parsed files to be used, creating an array for each of them.
def file_check(log, source):
	#split_word = '-log option passed with' # Word not used atm, it wont work with old version of shmooparse
	if source == 'ituff' or source == 'ituff_gnr' or source == 'gnr': 
		split_word = "Saving="
		second_word = None
	else: 
		split_word = "-log option"
		second_word = "XAXIS:"
	log_array = []

	try:
		with open(log, 'r') as file:
			log_content = file.read()
		
		
		if second_word != None:
			#for text in split_text:
			split_text = log_content.split(second_word)
			split_text = [second_word + split.strip() for split in split_text[1:]]
		else:
			split_text = log_content.split(split_word)
		## further split
		if len(split_text) == 2:
			log_array.append(split_text[1])
		else:
			log_array = [split_word + '\n'+ split.strip() for split in split_text[1:]]
	except:
		log_array = None #empty

	return log_array

# plotter: Main part of the code, calls the rest of modules to generate the plot files, based on the plot selection.
def plotter(o_dir, plt_opt,  VID = '',palette = 'Reds', axisfix = 'none', source = 'tester', zipfolder = True):

	
	log_array = file_check(o_dir, source)	
	
	if log_array:


		if len(log_array) > 1: pltnum = 1
		
		else: pltnum = ''
		
		for log_data in log_array:

			_data = plot_data(log_data, VID, axisfix,source)
			if not _data:
				continue
			if plt_opt == 'img':
				image_plot(_data, o_dir, pltnum, palette)
			elif plt_opt == 'xls':
				excel_plot(_data, o_dir, pltnum)
			elif plt_opt == 'all':
				excel_plot(_data, o_dir, pltnum)
				image_plot(_data, o_dir, pltnum, palette)

			if type(pltnum) == int: pltnum += 1
		
		if zipfolder:
			filename = os.path.basename(o_dir)
			o_path = re.sub(filename,'',o_dir)
			zip_to =  os.path.join(o_path, 'ImagePlots')
			zip_from = os.path.join(o_path, 'Plots')

			#print(zip_path)
			print(zip_from)
			print(zip_to)
			#zip_path = os.path.join(o_path, 'PlotImageFiles')
			shutil.make_archive(zip_to, 'zip', zip_from)
			shutil.rmtree(zip_from)
	else:
		print(f'PLOT MSG: There was no data to be used for plot in dir {o_dir}, moving to next folder, if there is any.')
# Main: Used to call the code from console, if needs to be called from another script, use plotter module.
def main(path, plt_opt, VID, palette, axisfix,source):
	scriptHome = os.path.dirname(os.path.realpath(__file__))
	current_user = getpass.getuser()
	o_path = re.sub(r'\.txt$','',path)
	filename = os.path.basename(path)
	Miscdata = {'scripthome':scriptHome,
			 'logfile':path,
			 'user': current_user
			 }

	if plt_opt in ['all', 'xls', 'img']:
		plotter(path, plt_opt, VID, palette, axisfix,source)
	else:
		print ('No valid plot selection use -plot all, xls or img')

if __name__ == '__main__' : 
	
	# Build the args values, debug option configured inside module, by default disabled.
	args = argparser(debug)

	# Move all the used arguments to its corresponding variables used in code

	path = args.log
	plt_opt = args.plot
	palette = args.color
	VID = args.vid
	axisfix = args.axis
	source = 'ituff_gnr'
	main(path, plt_opt, VID, palette, axisfix, source)