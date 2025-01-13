# #################################
#          ShmooReport
# #################################
# Version: 1.1
# Developer: Gabriel Espinoza Ballestero
# Date: 1/26/2024
#
# Description:
# Generates a report from a selected folder with tester Shmoo logs or ituff data, parsing the information
# into a more readable format with the option to generate a single xlsx report file with all the Shmoo data, 
# as well as image plots for each one of the Shmoos.
# 
# ShmooReport uses ShmooParser and ShmooPlotter to achieve the end result.
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
import shutil
site = "amr.corp.intel.com"
scriptpath = "ec\\proj\\mdl\\cr\\intel\\engineering\\dev\team_ftw\\gaespino\\scripts"
libsPath = f"\\\\{site}\\{scriptpath}"

sys.path.append(libsPath)

debug = True

# Arguments to be used from console

def argparser(debug):
	if not debug:
		parser = argparse.ArgumentParser()
		typehelp = ("Parse: Check raw log files from CLASS and clean them up in a new file, if there is any plot option selected will also create the files \n" 
		+	"Plot: Create a plot based on the files in the folder, folder files should only be processed Shmoo data, recommend using parse option only")

		# Add Argument list below
		parser.add_argument('-log', type=str, required= True,
							help = "Folder with all the logfiles taken from CLASS log with the raw Shmoo data")
		parser.add_argument('-filetype', choices=['parse', 'plot'], default= 'parse', type=str, required= False,
							help = typehelp)
		parser.add_argument('-filename', type=str, default='ShmooParsed_data',
							help = "Custom label to the new parsed txt file if not defined, default name ShmooParsed_data is used")
		parser.add_argument('-vid', type=str, default='', required= False,
							help = "Visual ID of the unit to be added at the end of the parsed file")
		parser.add_argument('-keystr', type=str, default='_', required= False,
							help = "Key string to be used to search for the vid in the log filename, by default uses '_'.")
		parser.add_argument('-plot', type=str, choices=['all', 'img', 'xls', ''], default='',
							help = "Plot type to be used, image (img): png file, excel file (xls) or all for both. Default is disabled")
		parser.add_argument('-color', type=str, choices=['Reds', 'Blues', 'Greens'], default='Reds', required= False,
							help = "Color palette to be used for the png file plot. Default is Blues")
		parser.add_argument('-source', type=str, choices=['tester', 'gnr', 'ituff_gnr','ituff'], default='gnr', required= False,
							help = "Source of the log file it can be tester or ituff. ")
		parser.add_argument('-axisfix', type=str, choices=['auto','none'], default='auto', required= False,
							help = "Auto option for fixing Axis order based on log data axis values of x / y ")
		args = parser.parse_args()
	
	# Default arguments for debug mode of the script
	else:
		class Args:
			#savefile = 'I:\\intel\\engineering\\dev\\team_ftw\\gaespino\\EMRMCC\\PEGA_SHMOOS_VF_NOVF\\ShmooParsed_Data.txt'
			log = r'C:\ParsingFiles\Shmoos_tests'
			filename = 'ShmooParsed_data'
			vid = ''
			keystr = ''
			plot = 'all'
			color = 'Blues'
			filetype = 'parse'
			source  = 'gnr'
			axisfix = 'auto'

		args = Args()
	
	return args

def plot(path, savefile, VID, plt_opt, filetype, useFolder = False, palette = 'Reds', axisfix = 'none', source = 'tester'):
	global libsPath
	from ShmooPlotter import plotter
	
	if useFolder:
		if filetype == 'plot':
			o_dir = path
		else:
			o_dir = savefile

	else:
		if filetype != 'plot':
			o_path = re.sub(r'\.txt$','',path)
			o_dir = o_path +'_Clean.txt'
		else:
			o_dir = path

	plotter(o_dir, plt_opt, VID, palette, axisfix, source, zipfolder = False)
	
def parse(path, savefile, VID, plt_opt, keystring, source):
	global libsPath
	from ShmooParser import parser
	VID = parser(path, savefile, VID, keystring, source)
	return VID
	
def main(path, savefile, VID, plt_opt, keystring, filetype,palette):
	if filetype == 'plot' and plt_opt == '':
		print ('Error: Plot option selected but no plot option used, select a valid plot from: img, xls or all')
		sys.exit(2)
	
	if filetype == 'parse' and plt_opt == '':
		print ('Warning: Parse selected, but there is no type of plot selected from: img, xls or all, no plot file will be created')
	
	if filetype != 'plot':
		parse(path, savefile, VID, plt_opt, keystring)

	if plt_opt != '' and filetype != 'parse':
		plot(path, savefile, VID, plt_opt, filetype, palette)

def folder_parse(path, savefile, VID, plt_opt, keystring, filetype, shmoofiles, parse_folder, filename, palette, source, axisfix = 'none'):
	useFolder = True
	if filetype == 'plot' and plt_opt == '':
		print ('MSG Error: Plot selected but no plot option used, please select a valid plot from: img, xls or all')
		sys.exit(2)
	
	if filetype == 'parse' and plt_opt == '':
		print ('MSG Warning: Parse selected, but there is no type of plot selected from: img, xls or all, no plot file will be created')
	
	savefile = os.path.join(parse_folder, filename + '.txt')
	
	# Check if file exists
	if os.path.isfile(savefile):
    	# If it does, delete it, this is mainly to avoid getting duplicate data inside the same file when plotting
		os.remove(savefile)
	print('PARSE MSG: Parsing using type:', filetype)
	#print(filetype)
	if source == 'tester' or source == 'gnr':
		for file in shmoofiles:

			shmoofile = os.path.join(path, file)
			if filetype != 'plot':
				parse(shmoofile, savefile, VID, plt_opt, keystring, source)
			if filetype == 'plot':
				plot(shmoofile, savefile, VID, plt_opt, filetype, useFolder, palette, axisfix, source)
	
	elif source == 'ituff' or source == 'ituff_gnr':
		shmoofile = os.path.join(path, shmoofiles)
		
		if filetype != 'plot':
			parse(shmoofile, savefile, VID, plt_opt, keystring, source)
		if filetype == 'plot':
			plot(shmoofile, savefile, VID, plt_opt, filetype, useFolder, palette, axisfix, source)

	if plt_opt != '' and filetype != 'plot':
		plot(path, savefile, VID, plt_opt, filetype, useFolder, palette, axisfix, source)

def folder_check(folder_path, folder_name = "Parsed", folder_file = True):
	
	# Verify if the provided path is a valid folder, if not exit the script
	if not os.path.isdir(folder_path):
		print(f'MSG Error: {folder_path} is not a valid folder. please check')
		sys.exit(1)
	
	if not folder_file:
		# Create a new directory for the Parsed results to be stored
		parse_folder = os.path.join(folder_path, folder_name)
		#plot_folder = os.path.join(parse_folder, "Plots")

		os.makedirs(parse_folder, exist_ok=True)
		
	# Build a list of text files in the folder
	shmoofiles = []
	folderpaths = []
	for file in os.listdir(folder_path):
		if file.endswith(".txt"):
			shmoofiles.append(file)
			
			if folder_file:
				folder_name = re.sub(r'\.txt$','',file)
			
				parse_folder = os.path.join(folder_path, folder_name)
				os.makedirs(parse_folder, exist_ok=True)

				file_src = os.path.join(folder_path, file)
				file_dst = os.path.join(parse_folder, file)
				#shutil.copy2(file_src, file_dst)
				#os.system(f'cp {file_src} {file_dst}')
				folderpaths.append(parse_folder)

		#shmoofiles.append(file)

	if not folder_file:
		folderpaths.append(parse_folder)

	return shmoofiles, folderpaths

def ituff_parse(folder_path):

	# Verify if the provided path is a valid folder, if not exit the script
	if not os.path.isdir(folder_path):
		print(f'MSG Error: {folder_path} is not a valid folder. please check')
		sys.exit(1)
	
	# Create a new directory for the Parsed results to be stored
	
	#plot_folder = os.path.join(parse_folder, "Plots")

	# Build a list of text files in the folder
	shmoofiles = []
	ituffpaths = []
	for file in os.listdir(folder_path):
		if file.endswith(".itf"):

			folder_name = re.sub(r'\.itf$','',file)
			
			parse_folder = os.path.join(folder_path, folder_name)
			os.makedirs(parse_folder, exist_ok=True)

			file_src = os.path.join(folder_path, file)
			file_dst = os.path.join(parse_folder, file)
			#shutil.copy2(file_src, file_dst)
			#os.system(f'cp {file_src} {file_dst}')
			shmoofiles.append(file)
			ituffpaths.append(parse_folder)
	
	return shmoofiles, ituffpaths

def ui_run(path, plt_opt, palette, filetype, filename, source, axisfix): 
	
	# This code only uses the folder portion, to treat individual files use the Parser and then the Plotter 
	use_folder = True
	savefile = ''

	#savefile = args.savefile
	keystring = ''
	VID = ''
	#if 'ituff' in source:

	print(f' {"#"*120}\n')
	print(f'\t{"-"*10} SHMOO PARSER {"-"*10}')
	print(f'\tRunning Shmoo parse for ituff VPOs, saving at: {path}\n')
	print(f'\tUsing Configuration:')
	#print(f'\tvpos:   \t{vpo}')		
	print(f'\tPlot:   \t{plt_opt}')	
	print(f'\tColors: \t{palette}')	
	print(f'\tType:   \t{filetype}')	
	print(f'\tReport: \t{filename}')	
	print(f'\tSource: \t{source}')
	print(f'\tAxis:   \t{axisfix}')
	print(f'\n{"#"*120}')
	print(f'{"#"*120}\n')
	print(f'\t{"-"*10} Processing data... Please wait.. {"-"*10} \n')
	
	if source == 'tester' or source == 'gnr':
		if use_folder:
			shmoofiles, folderpaths = folder_check(path)
			if len(folderpaths) > 1:
				for idx, folder in enumerate(folderpaths):
					shmoosf = [shmoofiles[idx]]
					folder_parse(path, savefile, VID, plt_opt, keystring, filetype, shmoosf, folder, filename, palette, source, axisfix)
			else:
				folder_parse(path, savefile, VID, plt_opt, keystring, filetype, shmoofiles, folderpaths[0], filename, palette, source, axisfix)

		else:
			main(path, savefile, VID, plt_opt, keystring, filetype, palette)
	elif source == 'ituff':
		shmoofiles, ituff_folder = ituff_parse(path)
		for idx, folder in enumerate(ituff_folder):
			folder_parse(path, savefile, VID, plt_opt, keystring, filetype, shmoofiles[idx], folder, filename, palette, source)
	elif source == 'ituff_gnr':
		print('Using Ituff file for GNR')
		shmoofiles, ituff_folder = ituff_parse(path)
		for idx, folder in enumerate(ituff_folder):
			folder_parse(path, savefile, VID, plt_opt, keystring, filetype, shmoofiles[idx], folder, filename, palette, source,axisfix)


	print(f'{"#"*120}\n')
	print(f'\tEND -- Process complete, check your files at folder{path}\n')

if __name__ == '__main__' : 
	
	# This code only uses the folder portion, to treat individual files use the Parser and then the Plotter 
	use_folder = True
	savefile = ''
	args = argparser(debug)

	# Move all the used arguments to its corresponding variable used in code

	path = args.log
	#savefile = args.savefile
	keystring = args.keystr
	VID = args.vid
	plt_opt = args.plot
	palette = args.color
	filetype = args.filetype
	filename = args.filename
	source = args.source
	axisfix = args.axisfix

	if source == 'tester' or source == 'gnr':
		if use_folder:
			shmoofiles, folderpaths = folder_check(path)
			if len(folderpaths) > 1:
				for idx, folder in enumerate(folderpaths):
					shmoosf = [shmoofiles[idx]]
					folder_parse(path, savefile, VID, plt_opt, keystring, filetype, shmoosf, folder, filename, palette, source, axisfix)
			else:
				folder_parse(path, savefile, VID, plt_opt, keystring, filetype, shmoofiles, folderpaths[0], filename, palette, source, axisfix)

		else:
			main(path, savefile, VID, plt_opt, keystring, filetype, palette)
	elif source == 'ituff':
		shmoofiles, ituff_folder = ituff_parse(path)
		for idx, folder in enumerate(ituff_folder):
			folder_parse(path, savefile, VID, plt_opt, keystring, filetype, shmoofiles[idx], folder, filename, palette, source)
	elif source == 'ituff_gnr':
		print('Using Ituff file for GNR')
		shmoofiles, ituff_folder = ituff_parse(path)
		for idx, folder in enumerate(ituff_folder):
			folder_parse(path, savefile, VID, plt_opt, keystring, filetype, shmoofiles[idx], folder, filename, palette, source,axisfix)
