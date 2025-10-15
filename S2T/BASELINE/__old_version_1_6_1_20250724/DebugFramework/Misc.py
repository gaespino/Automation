import sys
import os
from datetime import datetime
import shutil
import pandas as pd
import openpyxl
from tabulate import tabulate

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

if __name__ == "__main__":
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
    file_path = r'C:\Users\gaespino\OneDrive - Intel Corporation\Gaespino\GNR\System2Tester\DebugFrameworkTemplate.xlsx'  # Replace with your actual file path

    # Process the Excel file
    data_from_sheets = process_excel_file(file_path)

    # Print the extracted data
    for sheet_name, data in data_from_sheets.items():
        print(f"Data from sheet: {sheet_name}")
        for field, value in data.items():
            print(f"{field}: {value}")
        print("\n")

    # Create the tabulated format
    tabulated_df = create_tabulated_format(data_from_sheets)
    data_table = tabulate(tabulated_df, headers='keys', tablefmt='grid', showindex=False)
    # Print the tabulated DataFrame
    print(data_table)
