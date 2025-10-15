import sys
import os
from datetime import datetime
import shutil
import pandas as pd
import openpyxl
from tabulate import tabulate
import FileHandler as fh
#import SerialConnection as ser

def extract_data_from_named_table(sheet):
	# Iterate over all tables in the sheet
	for table in sheet.tables.values():
		# Get the table range
		table_range = sheet[table.ref]
		
		# Check if the first row contains 'Field' and 'Value'
		headers = [cell.value for cell in table_range[0]]
		if 'Field' in headers and 'Value' in headers:
			# Initialize a dictionary to store the values
			data = {}
			
			# Iterate over the rows starting from the second row
			for row in table_range[1:]:
				field = row[headers.index('Field')].value
				value = row[headers.index('Value')].value
				data[field] = value
			
			return data
	return None

def process_excel_file(file_path):
	# Load the Excel file
	workbook = openpyxl.load_workbook(file_path, data_only=True)
	
	# Dictionary to store data from all sheets
	all_data = {}
	
	# Iterate over each sheet
	for sheet_name in workbook.sheetnames:
		sheet = workbook[sheet_name]
		data = extract_data_from_named_table(sheet)
		
		if data:
			all_data[sheet_name] = data
	
	return all_data

def create_tabulated_format(data_from_sheets):
	# Get all unique fields from the data
	all_fields = set()
	for data in data_from_sheets.values():
		all_fields.update(data.keys())
	
	# Create a list to store DataFrame rows
	rows = []
	
	# Populate the rows list
	for field in all_fields:
		row_data = {'Fields': field}
		for sheet_name, data in data_from_sheets.items():
			row_data[sheet_name] = data.get(field, 'None')
		rows.append(row_data)
	
	# Create the DataFrame using pd.concat
	tabulated_df = pd.DataFrame(rows, columns=['Fields'] + list(data_from_sheets.keys()))
	
	return tabulated_df

#####################################################################################
##
##              Misc scripts
##
#####################################################################################

def copy_obj_files(src_dir, dest_dir, obj_files):

	for file in os.listdir(src_dir):
		for file_name in obj_files:
			if file_name in file:
				print(f'Copying File: {file_name} to {dest_dir}')
				src_file = os.path.join(src_dir, file)
				shutil.copy(src_file, dest_dir)

def print_custom_separator(text):
	total_length = 101
	text_length = len(text)
	side_length = (total_length - text_length) // 2
	separator_line = f'{"*" * side_length} {text} {"*" * side_length}'
	
	# Adjust if the total length is not exactly 101 due to integer division
	if len(separator_line) < total_length:
		separator_line += '*'
	
	return separator_line

def print_separator_box(direction='down'):
	arrow = '▼' if direction == 'down' else '▲'  # Box drawing arrows
	separator_line = f'{"─"*50}{arrow}{"─"*50}'
	print(separator_line)

def generate_strings(rows = 64, length=128, fill_char='0', custom_char='F', shift_range=(120, 128), shift_value='02'):
	# Initialize the base string with fill characters
	base_string = fill_char * length
	
	# Create a list to hold the generated strings
	strings = []
	
	# Iterate over the range to apply custom characters and shifting
	for i in range(rows):
		# Create a new string with the custom character in the specified range
		new_string = list(base_string)
		
		# Apply custom character in the specified range
		for j in range(shift_range[0], shift_range[1]):
			new_string[j] = custom_char
		
		# Insert the shift value at the beginning of the string
		shift_pos = i % (length - len(shift_value))
		new_string[shift_pos:shift_pos + len(shift_value)] = shift_value
		
		# Convert list back to string and add to the list
		strings.append(''.join(new_string))
	
	return strings

# Example usage

def generate_hex_string(length=128, fill_values=('F', '0'), specific_values=None):
	# Initialize the hex string with the first fill value
	hex_string = fill_values[0] * (length // 2) + fill_values[1] * (length // 2)
	
	# If specific values are provided, place them in the specified positions
	if specific_values:
		for position, value in specific_values.items():
			if 0 <= position < length:
				hex_string = hex_string[:position] + value + hex_string[position + 1:]
	
	return hex_string

def Recipes(path=r'\\crcv03a-cifs.cr.intel.com\mpe_spr_003\Gaespino\DebugFramework\CWF\ExperimentsTemplateCWF.xlsx'):
		
	data_from_sheets = fh.process_excel_file(path)
	# Create the tabulated format
	tabulated_df = fh.create_tabulated_format(data_from_sheets)
	#tabulated_df.sort_values(by=sort_by,inplace=True)
	data_table = tabulate(tabulated_df, headers='keys', tablefmt='grid', showindex=False)
	# Print the tabulated DataFrame
	print(data_table)

	return data_from_sheets
# Example usage:
# Generate a hex string with half 'F's and half '0's, with '2' at position 100
#hex_string = generate_hex_string(specific_values={100: '2'})
#print(hex_string)

# Generate a hex string with half '3's and half 'A's, with '5' at position 50
#hex_string = generate_hex_string(fill_values=('3', 'A'), specific_values={63: '5',127: '5'})
#print(hex_string)

#Recipes()

def get_last_line(logfile):
	with open(logfile, 'r') as file:
		lines = file.readlines()
	
	if lines:
		return lines[-1].strip(), lines
	return None, None

def search_in_file(lines, string = [], casesens = False, search_up_to_line = 10, reverse=True):
	
	if not lines:
		return None
	
	search_lines = list(reversed(lines)) if reverse else lines
	search_lines = search_lines[:search_up_to_line]
	#lines = lines.split('\n')
	for line in (search_lines):
		# Search for Pass String in lines
		for search_string in string:
			if (search_string in line) if casesens else (search_string.lower() in line.lower()):
				return True
		
	return False

if __name__ == "__main__":

	fh.teraterm_check(com_port = 15, teraterm_path = r"C:\teraterm", seteo_h_path = r"C:\SETEO_H", ini_file = "TERATERM.INI")
	
	#file = r'Q:\DPM_Debug\GNR\Logs\LLC\75MA888700252\RVPLoops\20250603_234218_T1_Loops_n3_Dragon_mesh\3_BaselineChecks_System_cfc_f22_vcfg_vbump_cfc_v-0_03.log'
	#lastline, lines = get_last_line(file)

	#found = search_in_file(lines, string = ['Image Handle'])
	#found_notrev = search_in_file(lines, string = ['Test Complete'], reverse=False)
	#print('Result', found, found_notrev)
	#server = r'\\Amr\ec\proj\mdl\cr'

# Example usage
	#source_folder = r'Q:\DPM_Debug\GNR\Logs\LLC\75857N7H00175\RVPLoops\20250618_084037_T1_Sweep_Dragon_mesh_voltage_cfc'
	#destination_folder = rf'{server}\intel\engineering\dev\user_links\gaespino\DebugFramework\GNR'
	#seed_folder = r'Q:\lvargasv\GNR\SM'
	
	#fh.copy_folder(source_folder, destination_folder)
	#data = fh.loops_fails(source_folder)
	#print(data)
#	lines = 64
#	shiftcount = 0
#	for i in range (lines):
#		# Generate a hex string with half '3's and half 'A's, with '5' at position 50
#		startchar = '5'
#		endchar = 'A'
#		start = 0 + shiftcount
#		end = start + 64
#		fill_values = ('0','5')
#		specific_values = {start:startchar, end:endchar}
#		hex_string = generate_hex_string(fill_values=fill_values, specific_values=specific_values)
#		print(f'normal,{i},{hex_string}')
#		#print(f'reverse,{i},{hex_string[::-1]}')
#		shiftcount += 1

	#generated_strings = generate_strings(64, 64, '0', '0', shift_range=(0, 64), shift_value='2')
	#for s in generated_strings:  # Display the first 5 strings for brevity
	#    print(s)
#    obj_list = ["DL32_1CayleyO_VI_0F100177",
#'DL32_Cayley_DBFN_0F100141',
#'DL32_Cayley_DIB_0F10013C',
#'DL32_Cayley_DIB_0F100144',
#'DL32_Cayley_DIB_0F100148',
#'DL32_Cayley_DIB_0F10015C',
#'DL32_Cayley_WI_0F10013B',
#'DL32_Cayley_WI_0F100163',
#'DL32_Ditto_GCAZ_0F100195',
#'DL32_Ditto_MAAZ_0F100181',
#'DL32_Ditto_OZAG_0F100184',
#'DL32_Ditto_OZAZ_0F100191',
#'DL32_DittoMT_CZ_0F10019D'
#]
#    drgslicepath = r'\\sccv69a-cifs.sc.intel.com\mpe_cmv_001\Dragon\OBJ\GNR\Tester\7425_0x0F_MO\GNR50C_L_MOSBFT_HToff_pseudoSBFT_Tester'
#    destination = r'I:\intel\engineering\dev\user_links\gaespino\GNR\ArchSim\Slice\Seeds'
#    #copy_obj_files(src_dir=drgslicepath, dest_dir=destination, obj_files=obj_list)
#    print_separator_box('down')
#    print_separator_box('up')
#    print(print_custom_separator('Test Results'))

	# Path to your Excel file
#    file_path = r'C:\Users\gaespino\OneDrive - Intel Corporation\Gaespino\GNR\System2Tester\DebugFrameworkTemplate.xlsx'  # Replace with your actual file path

	# Process the Excel file
#    data_from_sheets = process_excel_file(file_path)

	# Print the extracted data
#    for sheet_name, data in data_from_sheets.items():
#        print(f"Data from sheet: {sheet_name}")
#        for field, value in data.items():
#            print(f"{field}: {value}")
#        print("\n")

	# Create the tabulated format
#    tabulated_df = create_tabulated_format(data_from_sheets)
#    data_table = tabulate(tabulated_df, headers='keys', tablefmt='grid', showindex=False)
	# Print the tabulated DataFrame
#    print(data_table)
