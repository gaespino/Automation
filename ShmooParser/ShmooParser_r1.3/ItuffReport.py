# #################################
#          ItuffReport
# #################################
# Version: 1.1
# Developer: Gabriel Espinoza Ballestero
# Date: 1/26/2024
#
# Description:
# This script is designed to collect data from DEDC VPOs accesing directly to hdmxdata path at intels CR site,
# lookups for the VPO number, parses all the data into a more readable txt file, and can plot the same into an xlsx, or an image file.
#
# This script uses ShmooReport, ShmooParser and ShmooPlotter, for parsing and plotting the data, 
# ShmooReport is the one responsible for calling the corresponding plotter and parsing scripts.
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
import gzip
import glob

site = "amr.corp.intel.com"
scriptpath = "ec\\proj\\mdl\\cr\\intel\\engineering\\dev\team_ftw\\gaespino\\scripts"
libsPath = f"\\\\{site}\\{scriptpath}"

sys.path.append(libsPath)

from ShmooReport import ituff_parse
from ShmooReport import folder_parse

# Variable used only to check script errors/issues, used to skip arguments and be run from VSCode
debug = True

# Arguments to be used from console

def argparser(debug):
	if not debug:
		parser = argparse.ArgumentParser()
		typehelp = ("Parse: Check raw log files from CLASS and clean them up in a new file, if there is any plot option selected will also create the files \n" 
		+	"Plot: Create a plot based on the files in the folder, folder files should only be processed Shmoo data, recommend using parse option only")

		# Add Argument list below
		parser.add_argument('-dest', type=str, required= True,
							help = "Destination path to save parsed results")
		parser.add_argument('--vpo', nargs='+', required= True,
							help = "List of VPOS to be used to extract data from ituff. format: [J#######, ]")
		parser.add_argument('-filetype', choices=['parse', 'plot'], default= 'parse', type=str, required= False,
							help = "Type of postprocessing to be used, either parse or plot, if only parse is selected it won't plot any file just make the .txt with the data")
		parser.add_argument('-filename', type=str, default='ShmooParsed_data',
							help = "Custom label to the new parsed txt file if not defined, default name ShmooParsed_data is used")
		parser.add_argument('-source', type=str, choices=['ituff', 'ituff_gnr'], default='ituff', required= False,
							help = "Source of the log file it can be tester or ituff. ")
		parser.add_argument('-plot', type=str, choices=['all', 'img', 'xls', ''], default='',
							help = "Plot type to be used, image (img): png file, excel file (xls) or all for both. Default is disabled")
		parser.add_argument('-color', type=str, choices=['Reds', 'Blues', 'Greens'], default='Reds', required= False,
							help = "Color palette to be used for the png file plot. Default is Blues")
		parser.add_argument('-axis', choices=['none', 'auto'], default= 'auto', type=str, required= False,
							help = 'Checks for min/max values of x and y axis, and accomodates data to plot automatically if auto is selected')
		
		args = parser.parse_args()
	
	# Default arguments for debug mode of the script
	else:
		class Args:
			#savefile = 'I:\\intel\\engineering\\dev\\team_ftw\\gaespino\\EMRMCC\\PEGA_SHMOOS_VF_NOVF\\ShmooParsed_Data.txt'
			dest = r'C:\ParsingFiles\GNR_IA_Screen_Low'
			filename = 'IA_Low_Screen'
			plot = 'all'
			color = 'viridis'
			filetype = 'parse'
			vpo = ['J442084RV'] #J404018RV #J404020RV #J403123MV #J404006MV #J404019RV
			axis = ['auto']
			source = 'ituff_gnr'

		args = Args()
	
	return args

# Starts the lookup for VPO data in hdmxdata\prod folder
def VPO (path, Lot):
	site = "amr.corp.intel.com"
	ituffpath = "ec\\proj\\mdl\\cr\\intel\\hdmxdata\\prod"
	
	ituff_dir = f"\\\\{site}\\{ituffpath}"
	datafiles = []
	#ituff_dir = r"I:\hdmxdata\prod"
	
	Lot_dirs = dirFinder(ituff_dir, Lot)
	if not Lot_dirs:
		print(f'VPO {Lot} was not found in ituff directory: {ituff_dir}')
		sys.exit()
	gzipFs = fileFinder(Lot_dirs)
	
	print(f'PARSE MSG: VPO {Lot} found in ituff directory: {ituff_dir}')

	unzip_path = os.path.join(path, f'VPO_{Lot}_ItuffData')
	#plot_folder = os.path.join(parse_folder, "Plots")
	print(f'PARSE MSG: Unziping VPO Ituff Data in path: {unzip_path}.')
	os.makedirs(unzip_path, exist_ok=True)
	
	for gzipF in gzipFs:
		gzfile = os.path.basename(gzipF)[:-3]
		datafile = os.path.join(unzip_path, gzfile)
		unzip_data(gzipF, datafile)
		datafiles.append(datafile)
	
	return unzip_path

# Unzip the gzip ituff file
def unzip_data(gzipF, datafile):

	with gzip.open(gzipF, 'rb') as gz_in:
		with open(datafile, 'wb') as gz_out:
			shutil.copyfileobj(gz_in, gz_out)

# Search inside the network folder, changes the folder depending if we are using Unix or windows
def dirFinder(ituff_dir, Lot):
	
	Lot_dirs = []
	

	# Change the dir in case running in CR environment
	if not os.path.exists(str(ituff_dir)):
		Unix_path = r'/nfs/site/disks/mdo_labs_001/hdmxdata/prod'

		ituff_dir = Unix_path
	#	#ituff_dir = ituff_dir[0:2]+"\\prod"+ dir_path[2:]
	#print(f'Searching for the following VPO: {Lot} in hdmxdata path: {ituff_dir}, for ituff data: ')
	with os.scandir(ituff_dir) as entries:
		for entry in entries:
			if entry.is_dir() and Lot in entry.name:
				Lot_dirs.append(entry.path)
	
	if Lot_dirs: return Lot_dirs
	else: return None

# Search for all files inside the folders based on VPO name criteria
def fileFinder(Lot_dirs):
	gzipFs = []

	for Lot_dir in Lot_dirs:
		# Utiliza glob.glob para encontrar archivos .gz en la ruta actual
		gzipF = glob.glob(os.path.join(Lot_dir, '*.gz'))

		# Extiende la lista de rutas_archivos_gz con las rutas encontradas
		gzipFs.extend(gzipF)

	# Retorna la lista de rutas absolutas de archivos .gz encontrados
	return gzipFs


def ui_run(dest, vpo, plt_opt, palette, filetype, filename, source, axisfix):
		
	# This code only uses the folder portion, to treat individual files use the Parser and then the Plotter 
	use_folder = True
	savefile = ''

	#savefile = args.savefile
	keystring = ''
	VID = ''
	print(f' {"#"*120}\n')
	print(f'\t{"-"*10} ITUFF PARSER {"-"*10}')
	print(f'\tRunning Shmoo parse for ituff VPOs, saving at: {dest}\n')
	print(f'\tUsing Configuration:')
	print(f'\tvpos:   \t{vpo}')		
	print(f'\tPlot:   \t{plt_opt}')	
	print(f'\tColors: \t{palette}')	
	print(f'\tType:   \t{filetype}')	
	print(f'\tReport: \t{filename}')	
	print(f'\tSource: \t{source}')
	print(f'\tAxis:   \t{axisfix}')
	print(f'\n{"#"*120}')
	print(f'{"#"*120}\n')
	print(f'\t{"-"*10} Processing data... Please wait.. {"-"*10} \n')
	
	for lot in vpo:
		
		unzip_path = VPO (dest, lot)

		path = unzip_path
		shmoofiles, ituff_folder = ituff_parse(path)
		
		for idx, folder in enumerate(ituff_folder):
			folder_parse(path=path, savefile=savefile, VID=VID, plt_opt=plt_opt, keystring=keystring, filetype=filetype, shmoofiles=shmoofiles[idx], parse_folder=folder, filename=filename, palette=palette, source=source, axisfix=axisfix)


	print(f'{"#"*120}\n')
	print(f'\tEND -- Process complete, check your files at folder{dest}\n')

if __name__ == '__main__' : 
	
	# This code only uses the folder portion, to treat individual files use the Parser and then the Plotter 
	use_folder = True
	savefile = ''
	args = argparser(debug)

	# Move all the used arguments to its corresponding variable used in code

	dest = args.dest
	vpo = args.vpo
	#savefile = args.savefile
	keystring = ''
	VID = ''
	plt_opt = args.plot
	palette = args.color
	filetype = args.filetype
	filename = args.filename
	source = args.source #'ituff_gnr'
	axisfix = args.axis

	print(f' {"#"*120}\n')
	print(f'\t{"-"*10} ITUFF PARSER {"-"*10}')
	print(f'\tRunning Shmoo parse for ituff VPOs, saving at: {dest}\n')
	print(f'\tUsing Configuration:')
	print(f'\tvpos:   \t{vpo}')		
	print(f'\tPlot:   \t{plt_opt}')	
	print(f'\tColors: \t{palette}')	
	print(f'\tType:   \t{filetype}')	
	print(f'\tReport: \t{filename}')	
	print(f'\tSource: \t{source}')
	print(f'\tAxis:   \t{axisfix}')
	print(f'\n{"#"*120}')
	print(f'{"#"*120}\n')
	print(f'\t{"-"*10} Processing data... Please wait.. {"-"*10} \n')

	for lot in vpo:
		
		unzip_path = VPO (dest, lot)

		path = unzip_path
		shmoofiles, ituff_folder = ituff_parse(path)
		
		for idx, folder in enumerate(ituff_folder):
			folder_parse(path, savefile, VID, plt_opt, keystring, filetype, shmoofiles[idx], folder, filename, palette, source, axisfix)
	
	print(f'{"#"*120}\n')
	print(f'\tEND -- Process complete, check your files in folder{dest}\n')
