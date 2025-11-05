import pandas as pd
import json

def load_json_data():
    # Load JSON data
    json_file_path = r'C:\Git\Automation\PPV\Decoder\cha_params.json'
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    dicts = ['TARGET_LOC_PORT_BY_VAL','MSCOD_BY_VAL','SAD_RESULT_BY_VAL','SAD_ATTR_BY_VAL','TOR_OPCODES_BY_VAL','CACHE_STATE_BY_VAL','TARGET_LOC_PORT_BY_VAL','ISMQ_FSM_BY_VAL',]
    # Write data to Excel
    excel_file_path = r'C:\Git\Automation\PPV\Decoder\cha_params.xlsx'
    with pd.ExcelWriter(excel_file_path) as writer:
        # Iterate over each dictionary in the JSON data
        for dict_name, dict_data in data.items():
            # Transform the dictionary into a DataFrame
            if dict_name not in dicts:
                continue
            df = pd.DataFrame(list(dict_data.items()), columns=[dict_name,'Description'])
            # Write the DataFrame to a sheet in the Excel file
            df.to_excel(writer, sheet_name=dict_name, index=False)


    print(f"Data successfully written to {excel_file_path}")

def convert_excel_2_json(excel_file_path = 'path_to_your_excel_file.xlsx', json_file_path = 'path_to_your_json_file.json', sheet='Port_ID_Map'):

    # Load the Excel file
    
    df = pd.read_excel(excel_file_path, sheet_name=sheet)

    # Group the data by 'DIE_TYPE' and 'DIE SEGMENT'
    grouped = df.groupby('bit0:10 ==> portID, bit11:15 ==> DieID')

    # Create a nested dictionary
    nested_dict = {}
    for key, group in grouped:
        
        nested_dict[key] = group.to_dict(orient='records')

    # Convert the nested dictionary to a JSON string with indentation
    json_str = json.dumps(nested_dict, indent=4)

    # Save the JSON string to a file
    
    with open(json_file_path, 'w') as json_file:
        json_file.write(json_str)

    print(f"Excel file has been successfully converted to JSON and saved to {json_file_path}")

convert_excel_2_json(excel_file_path=r'C:\Git\Automation\10nm_Wave4_PortID_HAS_0p8_WW05p2_2021 (version 1).xlsx', json_file_path=r'C:\Git\Automation\GNRPortIDs.json')