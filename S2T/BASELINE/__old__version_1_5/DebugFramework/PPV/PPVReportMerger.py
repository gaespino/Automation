import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import MCAparser as mca

tables = {'CHA':'cha_mc', 'CORE':'core_mc', 'PPV':'ppv', 'CHA_MCAS':'chadecode', 'LLC_MCAS':'llcdecode', 'CORE_MCAS':'coredecode'}
sheet_names = ['CHA', 'CORE', 'PPV', 'CHA_MCAS', 'LLC_MCAS', 'CORE_MCAS']

def merge_excel_files(input_folder, output_file, prefix = ''):
    # List to hold dataframes
    all_data = {}

    # Iterate over all Excel files in the input folder
    for file in os.listdir(input_folder):
        
        if prefix != None:
            keyword = prefix
            excelfile = (file.endswith(f'{keyword}.xlsx') or file.endswith(f'{keyword}.xls')) or (prefix in file and '.xls' in file)
        else:
            keyword = ''
            excelfile = (file.endswith(f'{keyword}.xlsx') or file.endswith(f'{keyword}.xls'))
       
        #print('ExcelFile',excelfile)
        if excelfile:
            file_path = os.path.join(input_folder, file)
            excel_data = pd.read_excel(file_path, sheet_name=None)
            
            for sheet_name, df in excel_data.items():
                if sheet_name not in all_data:
                    all_data[sheet_name] = []
                all_data[sheet_name].append(df)

    # Create a writer object to write the merged data to a new Excel file
    with pd.ExcelWriter(output_file) as writer:
        for sheet_name, df_list in all_data.items():
            merged_df = pd.concat(df_list, ignore_index=True)
            merged_df.to_excel(writer, sheet_name=sheet_name, index=False)
    


    print(f"Merged Excel file saved as {output_file}")

def merge_specific_tables(input_folder, output_file, sheet_names ):
    # Dictionary to hold dataframes for each table
    all_data = {table_name: [] for table_name in sheet_names}
    
    # Iterate over all Excel files in the input folder
    for file in os.listdir(input_folder):
        if file.endswith('.xlsx') or file.endswith('.xls'):
            file_path = os.path.join(input_folder, file)
            excel_data = pd.read_excel(file_path, sheet_name=None)
            
            for sheet_name, df in excel_data.items():
                if sheet_name in sheet_names:
                    all_data[sheet_name].append(df)

    # Create a writer object to write the merged data to a new Excel file
    with pd.ExcelWriter(output_file) as writer:
        for sheet, df_list in all_data.items():
            if df_list:  # Check if the list is not empty
                merged_df = pd.concat(df_list, ignore_index=True)
                merged_df.to_excel(writer, sheet_name=sheet, index=False)
    
    #merged_data = pd.read_excel(output_file, sheet_name=None)
    for sheet, df_list in all_data.items():
        merged_df = pd.concat(df_list, ignore_index=True)
        mca.addtable(df=merged_df, excel_file=output_file, sheet=sheet, table_name=tables[sheet])
    
    print(f"Merged Excel file saved as {output_file}")

def append_excel_tables(source_file, target_file, sheet_names):
    # Read the source Excel file
    source_data = pd.read_excel(source_file, sheet_name=None)
    
    # Read the target Excel file
    target_data = pd.read_excel(target_file, sheet_name=None)
    
    # Dictionary to hold the updated dataframes
    updated_data = {}

    # Iterate over the specified table names
    for sheet in sheet_names:
        if sheet in source_data:
            source_df = source_data[sheet]
            if sheet in target_data:
                target_df = target_data[sheet]
                # Append the source data to the target data
                updated_df = pd.concat([target_df, source_df], ignore_index=True)
            else:
                # If the table does not exist in the target file, use the source data
                updated_df = source_df
            updated_data[sheet] = updated_df
        else:
            # If the table does not exist in the source file, use the target data
            if sheet in target_data:
                updated_data[sheet] = target_data[sheet]

    # Create a writer object to write the updated data to the target Excel file
    with pd.ExcelWriter(target_file) as writer:
        for sheet, df in updated_data.items():
            df.to_excel(writer, sheet_name=sheet, index=False)
    
    # Rebuild object Tables
    for sheet, df in updated_data.items():
        #merged_df = pd.concat(df_list, ignore_index=True)
        mca.addtable(df=df, excel_file=target_file, sheet=sheet, table_name=tables[sheet])
    
    print(f"Data from {source_file} has been appended to {target_file}")

def test():
    # Example usage
    input_folder = rf'C:\ParsingFiles\MCAParser_Tests\MergeFiles'
    output_file = rf'C:\ParsingFiles\MCAParser_Tests\211_Merged_Test_018.xlsx'

    sheet_names = ['CHA', 'CORE', 'PPV', 'CHA_MCAS', 'LLC_MCAS', 'CORE_MCAS']


    source_file = rf'C:\ParsingFiles\MCAParser_Tests\AppendTest\GNR3_WW50_LLC_UNITS_TICKS_CLASS_PPV_Data.xlsx'
    target_file = rf'C:\ParsingFiles\MCAParser_Tests\AppendTest\GNR3_WW51_LLC_test001_PPV_Data.xlsx'
    # Example usage
    #input_folder = 'path_to_your_input_folder'
    #output_file = 'merged_output.xlsx'
    
    """ Tests """
    # Remove comment for any command below to test
    #merge_specific_tables(input_folder, output_file, sheet_names)
    #merge_excel_files(input_folder, output_file)
    #append_excel_tables(source_file, target_file, sheet_names)

if __name__ == "__main__":
    
	test()