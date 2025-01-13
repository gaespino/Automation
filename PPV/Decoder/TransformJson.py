import pandas as pd
import json

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