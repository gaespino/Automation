# #################################
#          ShmooParser
# #################################
# Version: 1.1
# Developer: Gabriel Espinoza Ballestero
# Date: 1/26/2024
#
# Description:
# Checks tester or ituff logged data to clean and show a more clear Shmoo information.
# The resulting Shmoo can be used to easily interpret and analyze units performance on a test.
#
# Debug:
# There is a debug flag inside the code, if debug is required set this flag to True, and set the appropiate arguments manually in the debug section of the argpaser.
#
# Intel 2024


import os
import sys
import re
import getpass 
import argparse


debug = False
path = ''
savefile =''
plt_opt = ''
VID = ''
keystring = ''

debug = False
parse_file = None


# Arguments definition, use -h in console for detailed info.
def argparser(debug):
	if not debug:
		parser = argparse.ArgumentParser()

		# Add Argument list below
		parser.add_argument('-log', type=str, required= True,
							help = "Log file taken from CLASS log with the raw Shmoo data")
		parser.add_argument('-savefile', type=str, default='',
							help = "Name or location of the file to save the parsed data of the Shmoo log from CLASS, if file exists script will append data at the end, if not it will create the file")
		parser.add_argument('-vid', type=str, default='', required= False,
							help = "Visual ID of the unit to be added at the end of the parsed file")
		parser.add_argument('-keystr', type=str, default='_', required= False,
							help = "Key string to be used to search for the vid in the log filename, by default uses '_'.")
		parser.add_argument('-source', type=str, choices=['tester', 'ituff', 'gnr', 'ituff_gnr'], default='tester', required= False,
							help = "Source of the log file it can be tester or ituff. ")

		args = parser.parse_args()
	
	# Default arguments for debug mode of the script
	else:
		class Args:
			savefile = r'C:\ParsingFiles\GNR_Shmoo\Tests\Parsed_data.txt'
			log = r'C:\ParsingFiles\GNR_Shmoo\Tests\Shmoo_Unit_0098_lock_content_enabled.txt'
			#log = 'C:\\Users\\gaespino\\OneDrive - Intel Corporation\\Gaespino\\GNR\\J347045RV_5261_chk_1_20231122003207_QAHOT.itf'
			vid = ''
			keystr = '_'
			source = 'ituff_gnr'
		args = Args()
	
	return args

def format_number(number):
    # Define the threshold below which numbers should be displayed in scientific notation
    threshold = 1e-3
    
    # Check if the absolute value of the number is below the threshold
    if abs(number) < threshold:
        # Format the number in scientific notation
        return f"{number:.5E}"
    else:
        # Format the number normally
        return f"{number:.5f}"
	
def ituff_filter(log, VID):
	# Read the content of the log file into a string
	with open(log, 'r') as file:
		log_content = file.read()

	# Define a list of regular expressions to search for
	patterns = {
		'Shmoo_start': r'0_comnt_DEDC_EDCM_0',  # Pattern 1
		'VID_split': r'2_visualid_',        # Pattern 2
		'Shmoo_end': r'0_comnt_DEDC_EDCR_[A-Za-z0-9]+_TPI_DEDC::CTRL_X_SHMOO*?',     # Pattern 3
	}

	VIDpattern = r'(?<=2_visualid_).*?\n'
	
	ituffshmoo = []
	# Spli file in visual IDS

	vid_splits = log_content.split(patterns['VID_split'])
	vid_array = [patterns['VID_split'] + split.strip() for split in vid_splits[1:]]

	for vid_split in vid_array:
		
		vidname = re.search(VIDpattern, vid_split)
		VID = vidname.group().strip() if vidname else ""
		
		shmoo_split = vid_split.split(patterns['Shmoo_start'])
		shmoo_array = [patterns['Shmoo_start'] + split.strip() for split in shmoo_split[1:]]
		for shmoo in shmoo_array:
			start = shmoo.find(patterns['Shmoo_start'])
			if start == -1: continue
			end = shmoo.find(patterns['Shmoo_end'])
			shmoo_content = shmoo[start:end]
			shmoo_contents = ituff_params(shmoo_content, VID)
			ituffshmoo.append(shmoo_contents)

	return ituffshmoo

def ituff_filter_gnr(log, VID):
	# Read the content of the log file into a string
	with open(log, 'r') as file:
		log_content = file.read()

	# Define a list of regular expressions to search for
	patterns = {
		'Shmoo_start': r"_SSTP",#r'0_strgval_0_0_0',  # Pattern 1
		'VID_split': r'2_visualid_',        # Pattern 2
		'Shmoo_end': r"_Profile_Thermal",     # Pattern 3
	}

	VIDpattern = r'(?<=2_visualid_).*?\n'
	
	ituffshmoo = []
	# Spli file in visual IDS

	vid_splits = log_content.split(patterns['VID_split'])
	vid_array = [patterns['VID_split'] + split.strip() for split in vid_splits[1:]]

	print (f'PARSE MSG: Found a total of {len(vid_array)} based on vids findings for the ituff file. Data processing started...')

	for vid_split in vid_array:
		
		vidname = re.search(VIDpattern, vid_split)
		startstring = re.search(r"(?<=0_tname_)(.*?)_SSTP",vid_split)
		startstring = startstring.group().strip() if startstring else ""
		VID = vidname.group().strip() if vidname else ""
		
		shmoo_split = vid_split.split(patterns['Shmoo_start'])
		shmoo_array = [f'{startstring}\n' + split.strip() for split in shmoo_split[1:]]
		print (f'PARSE MSG: VID: {VID} -- Found a total of {len(shmoo_array)} shmoos. Processing... ')
		for shmoo in shmoo_array:
			shmooWord = shmoo.find(patterns['Shmoo_start'])
			if shmooWord == -1: continue
			end = shmoo.find(patterns['Shmoo_end'])
			shmoo_content = shmoo[shmooWord:end]
			shmoo_contents = ituff_params_gnr(shmoo_content, VID)
			ituffshmoo.append(shmoo_contents)
		
		print (f'PARSE MSG: VID: {VID}. Shmoo Parse completed moving to the next...')
	print (f'PARSE MSG: Ituff file Processing completed moving to the next if any...')

	return ituffshmoo

def GNR_filter(log, VID):

	# Read the content of the log file into a string
	with open(log, 'r') as file:
		log_content = file.read()

	# Define a list of regular expressions to search for
	patterns = {
		'Shmoo_start': r'Plist=',  # Pattern 1
		'VID_split': r'Functional Test settings',        # Pattern 2
		'Shmoo_end': r'_Profile_Thermal',     # Pattern 3
	}

	VIDpattern = r'(?<=2_visualid_).*?\n'
	
	gnrshmoo = []
	# Spli file in visual IDS

	vid_splits = log_content.split(patterns['VID_split'])
	vid_array = [patterns['VID_split'] + split.strip() for split in vid_splits[1:]]

	if not vid_splits:
		vid_array = [log_content]

	for vid_split in vid_array:
		if not re.search(r'Printing Shmoo', vid_split):
			continue
		vidname = re.search(VIDpattern, vid_split)
		VID = vidname.group().strip() if vidname else ""
		
		shmoo_split = vid_split.split(patterns['Shmoo_start'])
		shmoo_array = [patterns['Shmoo_start'] + split.strip() for split in shmoo_split[1:]]
		for shmoo in shmoo_array:
			
			# Look for key string in shmoo array
			shmoo_string = shmoo.find('Printing Shmoo')
			if shmoo_string == -1: continue
			
			start = shmoo.find(patterns['Shmoo_start'])
			if start == -1: continue
			end = shmoo.find(patterns['Shmoo_end'])
			shmoo_content = shmoo[start:end]
			shmoo_contents = GNR_params(shmoo_content, VID)
			gnrshmoo.append(shmoo_contents)

	return gnrshmoo

def GNR_params(data, VID):
	patterns = [
#		r'0_strgval_name:patlist.*?:',  # Pattern 1
#		r'0_strgval_name:timings.*?:',  # Pattern 2
#		r'0_strgval_name:xaxis_max.*?:',     # Pattern 3
#		r'0_strgval_name:xaxis_min.*?',     # Pattern 4
#		r'0_strgval_name:xaxis_parameter.*?',     # Pattern 5
#		r'0_strgval_name:xaxis_resolution.*?',    # Pattern 6
#		r'0_strgval_name:yaxis_max.*?',     # Pattern 7
#		r'0_strgval_name:yaxis_min.*?', # Pattern 8
#		r'0_strgval_name:yaxis_parameter.*?',     # Pattern 9
#		r'0_strgval_name:yaxis_resolution.*?',     # Pattern 10
		r'0_comnt_Plot3End_.*?',     # Pattern 11
		r'0_comnt_P3Legend_.*?',     # Pattern 11
		r'0_comnt_P3Data_.*?',     # Pattern 12
		r'0_comnt_PLOT_.*?',     # Pattern 12
		r'0_comnt_Plot3Start_.*?',     # Pattern 12
#		r'.*?LEGEND.*?',     # Pattern 12
	]

	rules = {
		'Plot3Start_': '',  # Pattern 1
		'timings': '',  # Pattern 2
		'PXStop,': '',     # Pattern 3
		'PXStart,':'',     # Pattern 4
		'PXName,':'',     # Pattern 5
		'PXStep,':'',    # Pattern 6
		'PYStop,':'',     # Pattern 7
		'PYStart,':'', # Pattern 8
		'PYName,':'',     # Pattern 9
		'PYStep,':'',     # Pattern 10

	}
	datarules = {
		'shmoo_data':[],     # Pattern 11
		'legends':[],     # Pattern 12
		'instance':'',     # Pattern 13
		'visualID':VID,     # Pattern 13
	}


	matches= []
	lines = data.split('\n')
	for idx, line in enumerate(lines):
		#for pattern in patterns:
		## Check for key line to get instance name
		if re.search(r'Printed to Ituff:',line):
			continue

		line = re.sub(r".*11]", "", line)
		if re.search(r'.*?X_.*?_Y_.*?', line):
			#log_filtered = f"{line.split('^')[1]} {line.split('^')[2]}"
			instance_data = lines.index(line)
			log_filtered = re.sub(r"0_tname_", "", lines[instance_data+2])
			matches.append(log_filtered)
		
		if re.search(r'Plist=.*', line):
    			#log_filtered = re.sub(pattern, "", line)
			if "Printing Shmoo" in lines[idx+1]:
				log_filtered = line #re.sub(r"Plist=", "", line).split(",")[0]
			#log_filtered = log_filtered.split(':')
			#if line == '': continue
				matches.append(log_filtered)
				continue
		
		if re.search(r'0_strgval_.*?', line):
			#log_filtered = re.sub(pattern, "", line)
			log_filtered = re.sub(r"0_strgval_", "", line)
			#log_filtered = log_filtered.split(':')
			#if line == '': continue
			matches.append(log_filtered)
			continue
		elif re.search(r'.*?LEGEND.*?', line):
			#log_filtered = f"{line.split('^')[1]} {line.split('^')[2]}"
			log_filtered = f"{line.split('^')[2]}"
			matches.append(log_filtered)
			continue

		else:
			continue
	
	filtered_lines = GNR_patterns(matches, rules, datarules)

#		if re.search(r'0_tname', line):
	return filtered_lines

def GNR_patterns(lines, rules, datarules):
	#index = 0
	#name_pattern = r"(?<=Plot3Start_)[^^]+"
	#value_pattern = r"(?<=PLOT_)[^^]+"
	#luString = r"P3Legend.*?"
	#inst_pattern = r"(?<=Plot3Start_)[^^]+"
	lb = 0
	if "Plist" in lines[0]:
		rules["Plot3Start_"] = re.sub(r"Plist=", "", lines[0]).split(",")[0]
		lb = 1
	datarules['instance'] = lines[lb]
	datarules['shmoo_data'] = lines[lb+2].split("_")[::-1]
	
	# Build Axis data
	axisdata = lines[lb+1]
	axisdata = axisdata.split('^')
	rules['PXName,'] = axisdata[1]
	rules['timings'] = axisdata[0]
	rules['PXStart,'] = axisdata[2]
	rules['PXStop,'] = axisdata[3]
	rules['PXStep,'] = axisdata[4].split('_')[0]
	rules['PYName,'] = axisdata[5]
	rules['PYStart,'] = axisdata[6]
	rules['PYStop,'] = axisdata[7]
	rules['PYStep,'] = axisdata[8]
	
	## Legends 
	lgnbase = lb+3
	legendcount = int((len(lines) - (lgnbase))/2)
	counts = 0
	for counts in range(legendcount):
		newcnt = counts*2
		legnds = f'{lines[lgnbase+newcnt]} = {lines[newcnt + lgnbase + 1]}'
		datarules['legends'].append(legnds)


	datarules['legends'] = sorted(datarules['legends'])
			

	#for idx, line in enumerate(lines):
	#	if re.search(r'.*?X_.*?_Y_.*?', line):
	#		axisdata = line.split('^')
	#		rules['PXName'] = axisdata[0]
	#		rules['timings'] = axisdata[1]
	#		rules['PXStart'] = axisdata[2]
	#		rules['PXStop'] = axisdata[3]
	#		rules['PXStep'] = axisdata[4].split('_')[0]
	#		rules['PYName'] = axisdata[5]
	#		rules['PYStart'] = axisdata[6]
	#		rules['PYStop'] = axisdata[7]
	#		rules['PYStep'] = axisdata[8]
			

		#if re.search(inst_pattern, line):
		#	instname = re.search(inst_pattern, line)
		#	inst = instname.group().strip() if instname else ""
		#	datarules['instance'] = inst

		#if re.match(luString, line):
		#	index = idx
		
		#for key in rules:
		#	if key in line:
		#		#keyname = re.search(name_pattern, line)
		#		if re.search(value_pattern, line):
		#			keyvalue = re.sub(r'PLOT_', "", line)
		#			value = re.sub(key, "", keyvalue)
		#			#name = keyname.group().strip() if keyname else ""
		#			#value = keyvalue.group().strip() if keyvalue else ""
		#		
		#			rules[key] = value
		
		#if re.search(r"P3Data_.*?", line):
		#	_shmoodata = re.sub(r"P3Data_", "", line)
		#	datarules['shmoo_data'].append(_shmoodata)
		
	#	if re.search(r"P3Legend_.*?", line):
	#		_legend = re.sub(r"P3Legend_", "", line)
	#		datarules['legends'].append(_legend)
	#try:
	#	legendcnt = int((len(lines) - (index + 1))/2)
	#	
	#	shmoo_data = lines[index+1]
	#except:
	#	legendcnt = 0
	#	shmoo_data = ''
	#shmoo_data = shmoo_data.split("_")
	#
	#Reverse the Array data 
	#shmoo_data = shmoo_data[::-1]
	#
	#datarules['shmoo_data'] = shmoo_data


	#counts = 0
	#for counts in range(legendcnt):
	#	newcnt = counts * 2
	#	if re.search(r'[A-Z]',lines[index + newcnt + 2]):
	#		try:
	#			legnds = f'{lines[index + newcnt + 2]} = {lines[index + newcnt + 3]}'
	#			datarules['legends'].append(legnds)
	#		except:
	#			break

	#datarules['legends'] = sorted(datarules['legends'])

	filtered_lines = GNR_formats(rules, datarules)
	
	return (filtered_lines)

def GNR_formats(rules, datarules):
	
	logdata = []

	saving = f'Saving= Shmoo with data gathered from ituff - timing: {rules["timings"]}'
	logdata.append(saving)
	xmax = float(rules["PXStop,"])
	xmin = float(rules["PXStart,"])
	ymax = float(rules["PYStop,"])
	ymin = float(rules["PYStart,"])

	logdata.append(f'Unit VID = {datarules["visualID"]}')
	#x_steps =  #float(rules["PXStep,"])
	#y_steps =  #float(rules["PYStep,"])
	_xresol = float(rules["PXStep,"])#abs(xmax-xmin) / x_steps
	_yresol = float(rules["PYStep,"])#abs(ymax-ymin) / y_steps
	x_resol = float(format_number(_xresol))
	x_steps =  abs(xmax-xmin) / _xresol
	y_steps =  abs(ymax-ymin) / _yresol #float(rules["PYStep,"])


	XAXIS = f'  XAXIS:  {rules["PXName,"]} {format_number(xmin)} - {format_number(xmax)} by {format_number(x_resol)} ({format_number(x_steps)} steps)'
	logdata.append(XAXIS)
	
	y_resol = float(format_number(_yresol))
	#y_steps =  int(abs((ymax - ymin) / y_resol))
	YAXIS = f'  YAXIS:  {rules["PYName,"]} {format_number(ymin)} - {format_number(ymax)} by {format_number(y_resol)} ({format_number(y_steps)} steps)'
	logdata.append(YAXIS)

	INSTANCE = 	f'  INSTANCE: {datarules["instance"]} '
	PLIST = 	f'  PLIST: {rules["Plot3Start_"]} '
	logdata.append(INSTANCE)
	logdata.append(PLIST)

	
	if ymax >= ymin:
		rowmax = int(max(ymax, 6))
	else:
		rowmax = int(max(ymin, 6))

	ylenmax = len(str(ymax))
	ylenmin = len(str(ymin))
	rowlen = len(datarules["shmoo_data"][0])

	#datarules['shmoo_data'][0] = f'{rules["yaxis_max"]}+'.ljust(rowmax)+ {datarules["shmoo_data"][0]}
	#datarules['shmoo_data'][-1] = f'{rules["yaxis_max"]}+{datarules["shmoo_data"][-1]}'
	yval = ymax
	
	
	for shidx, shmoo in enumerate(datarules['shmoo_data']):
		base = ymax - ymin
		if shidx == 0:
			shmoodat = f'{ymax}+{shmoo}'.rjust(rowmax + rowlen)
		elif shidx == (len(datarules['shmoo_data'])-1):
			shmoodat = f'{ymin}+{shmoo}'.rjust(rowmax + rowlen)
		else:
			if base > 0:
				yval = yval -_yresol
			else:
				yval = yval +_yresol
			shmoodat = f'{round(yval,2)}|{shmoo}'.rjust(rowmax + rowlen)	
		logdata.append(shmoodat)

	for legnd in datarules['legends']:
		legnddat = f'    {legnd}'
		logdata.append(legnddat)

	return (logdata)

def ituff_params(data, VID):
	patterns = [
#		r'0_strgval_name:patlist.*?:',  # Pattern 1
#		r'0_strgval_name:timings.*?:',  # Pattern 2
#		r'0_strgval_name:xaxis_max.*?:',     # Pattern 3
#		r'0_strgval_name:xaxis_min.*?',     # Pattern 4
#		r'0_strgval_name:xaxis_parameter.*?',     # Pattern 5
#		r'0_strgval_name:xaxis_resolution.*?',    # Pattern 6
#		r'0_strgval_name:yaxis_max.*?',     # Pattern 7
#		r'0_strgval_name:yaxis_min.*?', # Pattern 8
#		r'0_strgval_name:yaxis_parameter.*?',     # Pattern 9
#		r'0_strgval_name:yaxis_resolution.*?',     # Pattern 10
#		r'0_strgval_X.*?',     # Pattern 11
#		r'0_strgval_[0-9A-Za-z\*]+',     # Pattern 11
#		r'0_strgval_g.*?',     # Pattern 12
#		r'0_strgval_d.*?',     # Pattern 12
		r'0_strgval_.*?',     # Pattern 12
		r'.*?LEGEND.*?',     # Pattern 12
	]

	rules = {
		'patlist': '',  # Pattern 1
		'timings': '',  # Pattern 2
		'xaxis_max': '',     # Pattern 3
		'xaxis_min':'',     # Pattern 4
		'xaxis_parameter':'',     # Pattern 5
		'xaxis_resolution':'',    # Pattern 6
		'yaxis_max':'',     # Pattern 7
		'yaxis_min':'', # Pattern 8
		'yaxis_parameter':'',     # Pattern 9
		'yaxis_resolution':'',     # Pattern 10

	}
	datarules = {
		'shmoo_data':[],     # Pattern 11
		'legends':[],     # Pattern 12
		'instance':'',     # Pattern 13
		'visualID':VID,     # Pattern 13
	}


	matches= []
	lines = data.split('\n')
	for line in lines:
		#for pattern in patterns:
		## Check for key line to get instance name
		if re.search(r'.*?X_.*?_Y_.*?', line):
			#log_filtered = f"{line.split('^')[1]} {line.split('^')[2]}"
			instance_data = lines.index(line)
			log_filtered = re.sub(r"0_tname", "", lines[instance_data+1])
			matches.append(log_filtered)

		if re.search(r'0_strgval_.*?', line):
			#log_filtered = re.sub(pattern, "", line)
			log_filtered = re.sub(r"0_strgval_", "", line)
			#log_filtered = log_filtered.split(':')
			#if line == '': continue
			matches.append(log_filtered)
			continue
		elif re.search(r'.*?LEGEND.*?', line):
			#log_filtered = f"{line.split('^')[1]} {line.split('^')[2]}"
			log_filtered = f"{line.split('^')[2]}"
			matches.append(log_filtered)
			continue

		else:
			continue
	
	filtered_lines = ituff_patterns(matches, rules, datarules)

#		if re.search(r'0_tname', line):
	return filtered_lines

def ituff_params_gnr(data, VID):
	patterns = [
#		r'0_strgval_name:patlist.*?:',  # Pattern 1
#		r'0_strgval_name:timings.*?:',  # Pattern 2
#		r'0_strgval_name:xaxis_max.*?:',     # Pattern 3
#		r'0_strgval_name:xaxis_min.*?',     # Pattern 4
#		r'0_strgval_name:xaxis_parameter.*?',     # Pattern 5
#		r'0_strgval_name:xaxis_resolution.*?',    # Pattern 6
#		r'0_strgval_name:yaxis_max.*?',     # Pattern 7
#		r'0_strgval_name:yaxis_min.*?', # Pattern 8
#		r'0_strgval_name:yaxis_parameter.*?',     # Pattern 9
#		r'0_strgval_name:yaxis_resolution.*?',     # Pattern 10
#		r'0_strgval_X.*?',     # Pattern 11
#		r'0_strgval_[0-9A-Za-z\*]+',     # Pattern 11
#		r'0_strgval_g.*?',     # Pattern 12
#		r'0_strgval_d.*?',     # Pattern 12
		r'0_strgval_0_0_0',     # Pattern 12
		r'.*?LEGEND.*?',     # Pattern 12
	]

	rules = {
		'patlist': '',  # Pattern 1
		'timings': '',  # Pattern 2
		'xaxis_max': '',     # Pattern 3
		'xaxis_min':'',     # Pattern 4
		'xaxis_parameter':'',     # Pattern 5
		'xaxis_resolution':'',    # Pattern 6
		'yaxis_max':'',     # Pattern 7
		'yaxis_min':'', # Pattern 8
		'yaxis_parameter':'',     # Pattern 9
		'yaxis_resolution':'',     # Pattern 10

	}
	datarules = {
		'shmoo_data':[],     # Pattern 11
		'legends':[],     # Pattern 12
		'instance':'',     # Pattern 13
		'visualID':VID,     # Pattern 13
	}


	matches= []
	lines = data.split('\n')
	for line in lines:
		#for pattern in patterns:
		## Check for key line to get instance name
		if re.search(r'.*?X_.*?_Y_.*?', line):
			#log_filtered = f"{line.split('^')[1]} {line.split('^')[2]}"
			instance_data = lines.index(line)
			#log_filtered = re.sub(r"0_strgval_", "", line)
			log_filtered = re.sub(r"0_tname", "", lines[instance_data+1])
			matches.append(log_filtered)
			

		if re.search(r'0_strgval_.*?', line):
			#log_filtered = re.sub(pattern, "", line)
			log_filtered = re.sub(r"0_strgval_", "", line)
			#log_filtered = log_filtered.split(':')
			#if line == '': continue
			matches.append(log_filtered)
			continue
		elif re.search(r'.*?LEGEND.*?', line):
			#log_filtered = f"{line.split('^')[1]} {line.split('^')[2]}"
			log_filtered = f"{line.split('^')[1]}_{line.split('^')[2]}"
			matches.append(log_filtered)
			continue

		else:
			continue
	
	filtered_lines = ituff_patterns_gnr(matches, rules, datarules)

#		if re.search(r'0_tname', line):
	return filtered_lines

def ituff_patterns_gnr(lines, rules, datarules):
	#index = 0
	name_pattern = r"(?<=name:)[^^]+"
	value_pattern = r"(?<=value:)[^^]+"
	luString = r"X_.*?_Y_.*?"
	inst_pattern = r"::(.*?)_SHMOO"
	legend_lut = r".*LEGEND.*"
	for idx, line in enumerate(lines):
		if re.search(inst_pattern, line):
			instname = re.search(inst_pattern, line)
			inst = instname.group().strip() if instname else ""
			datarules['instance'] = inst

		if re.match(luString, line):
			index = idx
			axis_split = line.split("^")
			rules['xaxis_max'] = axis_split[3]
			rules['xaxis_min'] = axis_split[2]
			rules['xaxis_parameter'] = axis_split[1]
			rules['xaxis_resolution'] = axis_split[4].split("_")[0]

			rules['yaxis_max'] = axis_split[7]
			rules['yaxis_min'] = axis_split[6]
			rules['yaxis_parameter'] = axis_split[5]
			rules['yaxis_resolution'] = axis_split[8]
		
		#if re.match(legend_lut, line):



		
#		for key in rules:
#			if key in line:
#				keyname = re.search(name_pattern, line)
#				keyvalue = re.search(value_pattern, line)
#				
#				name = keyname.group().strip() if keyname else ""
#				value = keyvalue.group().strip() if keyvalue else ""
#				
#				rules[key] = value

	try:
		legendcnt = int((len(lines) - (index + 1)))
		#legendcnt = int((len(lines) - 3)/2)
		shmoo_data = lines[index+1]
		
	except:
		legendcnt = 0
		shmoo_data = ''
	shmoo_data = shmoo_data.split("_")

	#Reverse the Array data 
	shmoo_data = shmoo_data[::-1]

	datarules['shmoo_data'] = shmoo_data


	counts = 0
	for counts in range(legendcnt):
		newcnt = counts * 2
		if re.search(legend_lut,lines[index + counts]):
		
		#if re.search(r'[A-Z]',lines[index + newcnt + 2]):
			try:
				legnds = f'{lines[index + counts].split("_")[1]} = {lines[index + counts + 1]}'
				datarules['legends'].append(legnds)
			except:
				break

	datarules['legends'] = sorted(datarules['legends'])

	filtered_lines = ituff_formats(rules, datarules)
	
	return (filtered_lines)

def ituff_patterns(lines, rules, datarules):
	#index = 0
	name_pattern = r"(?<=name:)[^^]+"
	value_pattern = r"(?<=value:)[^^]+"
	luString = r"X_.*?_Y_.*?"
	inst_pattern = r"(?<=TPI_DEDC::)[^^]+"
	for idx, line in enumerate(lines):
		if re.search(inst_pattern, line):
			instname = re.search(inst_pattern, line)
			inst = instname.group().strip() if instname else ""
			datarules['instance'] = inst

		if re.match(luString, line):
			index = idx
		
		for key in rules:
			if key in line:
				keyname = re.search(name_pattern, line)
				keyvalue = re.search(value_pattern, line)
				
				name = keyname.group().strip() if keyname else ""
				value = keyvalue.group().strip() if keyvalue else ""
				
				rules[key] = value

	try:
		legendcnt = int((len(lines) - (index + 1))/2)
		
		shmoo_data = lines[index+1]
	except:
		legendcnt = 0
		shmoo_data = ''
	shmoo_data = shmoo_data.split("_")

	#Reverse the Array data 
	shmoo_data = shmoo_data[::-1]

	datarules['shmoo_data'] = shmoo_data


	counts = 0
	for counts in range(legendcnt):
		newcnt = counts * 2
		if re.search(r'[A-Z]',lines[index + newcnt + 2]):
			try:
				legnds = f'{lines[index + newcnt + 2]} = {lines[index + newcnt + 3]}'
				datarules['legends'].append(legnds)
			except:
				break

	datarules['legends'] = sorted(datarules['legends'])

	filtered_lines = ituff_formats(rules, datarules)
	
	return (filtered_lines)

def ituff_formats(rules, datarules):
	
	logdata = []

	saving = f'Saving= Shmoo with data gathered from ituff - timing: {rules["timings"]}'
	logdata.append(saving)
	xmax = float(format_number(float(rules["xaxis_max"])))
	xmin = float(format_number(float(rules["xaxis_min"])))
	ymax = float(format_number(float(rules["yaxis_max"])))
	ymin = float(format_number(float(rules["yaxis_min"])))

	logdata.append(f'Unit VID = {datarules["visualID"]}')

	x_resol = float(format_number(float(rules["xaxis_resolution"])))
	x_steps =  float(format_number(abs((xmax - xmin) / x_resol)))
	XAXIS = f'  XAXIS:  {rules["xaxis_parameter"]} {xmin} - {xmax} by {x_resol} ({x_steps} steps)'
	logdata.append(XAXIS)
	
	y_resol = float(format_number(float(rules["yaxis_resolution"])))
	y_steps =  float(format_number(abs((ymax - ymin) / y_resol)))
	YAXIS = f'  YAXIS:  {rules["yaxis_parameter"]} {ymin} - {ymax} by {y_resol} ({y_steps} steps)'
	logdata.append(YAXIS)

	PLIST = f'  PLIST:  {datarules["instance"]} :: {rules["patlist"]} '
	logdata.append(PLIST)


	
	if ymax >= ymin:
		rowmax = max(ymax, 6)
	else:
		rowmax = max(ymin, 6)

	ylenmax = len(str(ymax))
	ylenmin = len(str(ymin))
	rowlen = len(datarules["shmoo_data"][0])

	#datarules['shmoo_data'][0] = f'{rules["yaxis_max"]}+'.ljust(rowmax)+ {datarules["shmoo_data"][0]}
	#datarules['shmoo_data'][-1] = f'{rules["yaxis_max"]}+{datarules["shmoo_data"][-1]}'

	for shidx, shmoo in enumerate(datarules['shmoo_data']):
		
		if shidx == 0:
			shmoodat = f'{ymax}+{shmoo}'.rjust(int(rowmax) + rowlen)
		elif shidx == (len(datarules['shmoo_data'])-1):
			shmoodat = f'{ymin}+{shmoo}'.rjust(int(rowmax) + rowlen)
		else:
			shmoodat = f'|{shmoo}'.rjust(int(rowmax) + rowlen)	
		logdata.append(shmoodat)

	for legnd in datarules['legends']:
		legnddat = f'    {legnd}'
		logdata.append(legnddat)

	return (logdata)

def Shmoo_filter(log, VID):
	# Read the content of the log file into a string
	with open(log, 'r') as file:
		log_content = file.read()

	# Define a list of regular expressions to search for
	patterns = [
		r'DUT.* \|',  # Pattern 1
		r'\+',        # Pattern 2
		r'\= g',     # Pattern 3
		r'\= d',     # Pattern 4
		r'Clamp',     # Pattern 5
		r'PLIST:',    # Pattern 6
		r'VDAC_',     # Pattern 7
		r'tap_param', # Pattern 8
#		r'Custom',     # Pattern 9
		r'XAXIS:',     # Pattern 10
		r'YAXIS:',     # Pattern 11
		r'REPEAT_N ',     # Pattern 12
	]

	skipwords = [
		'2_strgval',  		# Pattern 1
		"API_CALL",        	# Pattern 2
		"SLOPE: RES",		# Pattern 3
		"2_tname_HWALARM"		# Pattern 3
	]
	# Search for the patterns in the log content
	matches = []

	# Split file in lines
	log_lines = log_content.split('\n')
	

	# Search for patterns inside file and return a filtered array of lines
	for line in log_lines:
		# Check if there is any skip word in the line
		skipword = False
		for skipw in skipwords:
			if skipw in line:	
				skipword = True
				break
		if skipword:
			continue
		else:
			# Continue code
			for pattern in patterns:
				if re.search(pattern, line):

						#log_filtered = re.sub(pattern, "", line)
						log_filtered = re.sub(r".*11]", "", line)
						#if line == '': continue
						matches.append(log_filtered)
						break
				else:
					continue
#		if re.search(r'0_tname', line):

	if VID != '': matches.append(f'Unit VID = {VID}')
	
	

	filtered_lines = matches

	return(filtered_lines)

def write_new(Miscdata, filtered_lines, cleanfile, use_append):
	global parse_file
	#Clear file using the write option
	if use_append == False:
		Clean_shmoo = open(cleanfile, 'w')
		Clean_shmoo.close()
	
	#Open file with the append option
	Clean_shmoo = open(cleanfile, 'a')

	# Write data in txt file
	Clean_shmoo.write(f'- Firstline of new parsed file -' + '\n')
	Clean_shmoo.write(f'-log option passed with {Miscdata["logfile"]}' + '\n')
	#Clean_shmoo.write(f'Saving= Shmoo with data gathered from tester')
	Clean_shmoo.write(f'Hi {Miscdata["user"]}, parsing log of all_pin mode Shmoo Instance for you' + '\n')
	for line in filtered_lines:
		Clean_shmoo.write(line + '\n')
	Clean_shmoo.write(f'FILE: {Miscdata["logfile"]}' + '\n')
	#Clean_shmoo.write(f'USER: {Miscdata["logfile"]}' + '\n')
	
	if parse_file != cleanfile: 
		parse_file = cleanfile
		if use_append:
			print (f'PARSE MSG: Shmoo parsed file created in the following location: {cleanfile}')
		else:
			print (f'PARSE MSG: Shmoo data will be added at the end of the following file {cleanfile}')
	
	Clean_shmoo.close()

def VID_check(filename, keystring):
	if re.search(r'(?i)vid(.*)', filename):
		VID = re.search(r'(?i)vid(.*)', filename).group(0)
		VID = VID.split('_')
		VID = VID[0]
	
	elif re.search(keystring, filename):
		
		vidpat = re.compile(rf'{keystring}(\d+[A-Za-z].+)')
		try:
			VID = re.search(vidpat, filename).group(1)
			VID = re.sub(r'\.(.*)','',VID)
			VID = VID.rstrip('_').rstrip('.')
			#VID = ''
		except AttributeError:
			VID = ''
	else:
		VID = ''

	return VID

def parser(path, savefile, VID, keystring, source = 'tester'):
	scriptHome = os.path.dirname(os.path.realpath(__file__))
	current_user = getpass.getuser()
	o_path = re.sub(r'\.txt$','',path)
	filename = os.path.basename(path)
	Miscdata = {'scripthome':scriptHome,
			 'logfile':path,
			 'user': current_user
			 }
	#inputFile = open(path, 'r')
	
	if VID == '': VID = VID_check(filename, keystring)

	use_append = False
	if savefile != '':
		o_dir = savefile
		try:
			open(o_dir, 'r')
			use_append = True
			#print (f'Shmoo data will be added at the end of the following file {savefile}')
		except FileNotFoundError: 
			use_append = False
			print (f'PARSE MSG: Creating new shmoo datafile {savefile}')
	else:	
		
		o_dir = o_path +'_Clean.txt'

	if source == 'tester':
		filtered_lines = Shmoo_filter(path, VID)
		write_new(Miscdata, filtered_lines, o_dir, use_append)

	elif source == 'ituff':
		ituff_lines = ituff_filter(path, VID)
		for filtered_lines in ituff_lines:
			write_new(Miscdata, filtered_lines, o_dir, use_append)
			use_append = True
	elif source == 'ituff_gnr':
		ituff_lines = ituff_filter_gnr(path, VID)
		for filtered_lines in ituff_lines:
			write_new(Miscdata, filtered_lines, o_dir, use_append)
			use_append = True

	elif source == 'gnr':
		gnr_lines = GNR_filter(path, VID)
		count = 0
		if len(gnr_lines) > 1: use_append = True
		for filtered_lines in gnr_lines:
			write_new(Miscdata, filtered_lines, o_dir, use_append)
if __name__ == '__main__' : 
	
	args = argparser(debug)

	# Move all the used arguments to its corresponding variable used in code

	path = args.log
	savefile = args.savefile
	keystring = args.keystr
	VID = args.vid
	source = args.source
	
	parser(path, savefile, VID, keystring, source)