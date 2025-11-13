"""
Script to convert between Excel and JSON formats for s2tregdata.json
- Excel to JSON: Reads Excel with columns (lower_case, description, cr_offset, desired_value, ref_value)
- JSON to Excel: Reads JSON and creates Excel with tabs based on main keys
"""

import pandas as pd
import json
import sys
from pathlib import Path


def excel_to_json(excel_path, output_path=None):
    """
    Convert Excel file to JSON format
    
    Args:
        excel_path: Path to input Excel file
        output_path: Path to output JSON file (optional)
    """
    # Read Excel file
    df = pd.read_excel(excel_path)
    
    # Verify required columns exist
    required_columns = ['lower_case', 'description', 'cr_offset', 'desired_value', 'ref_value']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        print(f"Found columns: {list(df.columns)}")
        return
    
    # Build JSON structure
    result = {}
    
    for _, row in df.iterrows():
        lower_case = row['key']
        
        # Skip empty rows
        if pd.isna(lower_case) or str(lower_case).strip() == '':
            continue
        
        # Create the value dictionary with only non-empty values
        value_dict = {}
        
        if not pd.isna(row['description']):
            value_dict['description'] = str(row['description'])
        
        if not pd.isna(row['cr_offset']):
            value_dict['cr_offset'] = str(row['cr_offset'])
        
        if not pd.isna(row['desired_value']):
            value_dict['desired_value'] = str(row['desired_value'])
        
        if not pd.isna(row['ref_value']):
            value_dict['ref_value'] = str(row['ref_value'])
        
        # Add to result
        result[str(lower_case)] = value_dict
    
    # Determine output path
    if output_path is None:
        excel_file = Path(excel_path)
        output_path = excel_file.parent / f"{excel_file.stem}_output.json"
    
    s2t_reg = {'s2t_reg': result}
    # Write JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(s2t_reg, f, indent=4, ensure_ascii=False)
    
    print(f"Successfully converted {len(result)} entries")
    print(f"Output written to: {output_path}")
    
    # Print preview
    print("\nPreview (first 2 entries):")
    preview_count = 0
    for key, value in result.items():
        if preview_count >= 2:
            break
        print(f"\n  \"{key}\": {json.dumps(value, indent=4)}")
        preview_count += 1


def json_to_excel(json_path, output_path=None):
    """
    Convert JSON file to Excel format
    Creates Excel sheets based on main keys (e.g., 's2t_reg')
    
    Args:
        json_path: Path to input JSON file
        output_path: Path to output Excel file (optional)
    """
    # Read JSON file
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Determine output path
    if output_path is None:
        json_file = Path(json_path)
        output_path = json_file.parent / f"{json_file.stem}_output.xlsx"
    
    # Create Excel writer
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        
        # Process each main key (e.g., 's2t_reg')
        for main_key, registers in data.items():
            print(f"\nProcessing sheet: {main_key}")
            
            # Prepare data for DataFrame
            rows = []
            
            # Sort keys alphabetically
            sorted_keys = sorted(registers.keys())
            
            # Build rows with idx
            for idx, key in enumerate(sorted_keys):
                reg_info = registers[key]
                
                # Get desired_value and ref_value
                desired_value_str = reg_info.get('desired_value', '0x0')
                ref_value_str = reg_info.get('ref_value', '0x0')
                
                # Convert hex strings to integers for calculation
                try:
                    desired_value_int = int(desired_value_str, 16) if isinstance(desired_value_str, str) and desired_value_str.startswith('0x') else int(str(desired_value_str), 16)
                except (ValueError, TypeError):
                    desired_value_int = 0
                
                try:
                    ref_value_int = int(ref_value_str, 16) if isinstance(ref_value_str, str) and ref_value_str.startswith('0x') else int(str(ref_value_str), 16)
                except (ValueError, TypeError):
                    ref_value_int = 0
                
                # Calculate delta (XOR of desired and ref values)
                delta = desired_value_int ^ ref_value_int
                
                # Check if values are the same
                same = 'Yes' if delta == 0 else 'No'
                
                row = {
                    'idx': idx,
                    'key': key,
                    'description': reg_info.get('description', ''),
                    'cr_offset': reg_info.get('cr_offset', ''),
                    'numbits': reg_info.get('numbits', ''),
                    'desired_value': desired_value_str,
                    'ref_value': ref_value_str,
                    'delta': hex(delta) if delta != 0 else '0x0',
                    'same': same
                }
                rows.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(rows)
            
            # Write to Excel sheet (sheet name is the main key)
            # Excel sheet names have a 31 character limit
            sheet_name = main_key[:31] if len(main_key) > 31 else main_key
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"  Added {len(rows)} entries to sheet '{sheet_name}'")
    
    print(f"\nSuccessfully created Excel file: {output_path}")
    print(f"Total sheets: {len(data)}")
    
    # Print preview
    if data:
        first_key = list(data.keys())[0]
        first_registers = data[first_key]
        sorted_reg_keys = sorted(first_registers.keys())
        
        print(f"\nPreview from sheet '{first_key}' (first 3 entries):")
        for i, key in enumerate(sorted_reg_keys[:3]):
            reg_info = first_registers[key]
            print(f"  {i}. {key}")
            print(f"     description: {reg_info.get('description', '')}")
            print(f"     desired_value: {reg_info.get('desired_value', '')}")


if __name__ == "__main__":
    """
    Main execution block
    
    CONFIGURATION:
    -------------
    Set 'mode' to either:
    - 'excel_to_json': Convert Excel file to JSON format
    - 'json_to_excel': Convert JSON file to Excel format
    
    Excel to JSON:
      Input columns: lower_case, description, cr_offset, desired_value, ref_value
      Output: JSON with structure {"s2t_reg": {register_entries}}
    
    JSON to Excel:
      Input: JSON with main keys (e.g., "s2t_reg") containing register dictionaries
      Output: Excel file with:
        - Sheet name = main key (e.g., "s2t_reg")
        - Columns: idx, key, description, cr_offset, numbits, desired_value, ref_value
        - Keys sorted alphabetically
        - idx starting from 0
    """
    
    # ========== CONFIGURATION ==========
    # Change mode here: 'excel_to_json' or 'json_to_excel'
    mode = 'json_to_excel'
    # ===================================
    
    if mode == 'excel_to_json':
        # Excel to JSON conversion
        excel_file = r"C:\ParsingFiles\CWF\Registers\s2t_registers.xlsx"
        output_file = None  # Will auto-generate name if None
        
        print("=" * 80)
        print("EXCEL TO JSON CONVERSION")
        print("=" * 80)
        
        if not Path(excel_file).exists():
            print(f"Error: File not found: {excel_file}")
            sys.exit(1)
        
        excel_to_json(excel_file, output_file)
    
    elif mode == 'json_to_excel':
        # JSON to Excel conversion
        json_file = r"c:\Git\Automation\Automation\S2T\BASELINE\S2T\product_specific\cwf\RegFiles\s2tregdata.json"
        output_file = None  # Will auto-generate name if None
        
        print("=" * 80)
        print("JSON TO EXCEL CONVERSION")
        print("=" * 80)
        
        if not Path(json_file).exists():
            print(f"Error: File not found: {json_file}")
            sys.exit(1)
        
        json_to_excel(json_file, output_file)
    
    else:
        print(f"Error: Invalid mode '{mode}'")
        print("Valid modes: 'excel_to_json' or 'json_to_excel'")
        sys.exit(1)
