"""
Update all product config files to move Unit Data fields to their own section
"""
import json
from pathlib import Path

def update_config_file(file_path):
    """Update a single config file"""
    print(f"\nProcessing: {file_path.name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    field_configs = config.get('field_configs', {})
    
    # Unit Data fields to move
    unit_data_fields = ['Product', 'Visual ID', 'Bucket', 'COM Port', 'IP Address']
    
    changes_made = 0
    
    # Add Product field if it doesn't exist
    if 'Product' not in field_configs:
        field_configs['Product'] = {
            "section": "Unit Data",
            "type": "str",
            "default": "GNR",
            "description": "Product type",
            "required": True,
            "options": ["GNR", "CWF", "DMR"]
        }
        print(f"  + Added 'Product' field")
        changes_made += 1
    
    # Update sections for Unit Data fields
    for field_name in unit_data_fields:
        if field_name in field_configs:
            old_section = field_configs[field_name].get('section', 'Unknown')
            if old_section != 'Unit Data':
                field_configs[field_name]['section'] = 'Unit Data'
                print(f"  ✓ Moved '{field_name}' from '{old_section}' to 'Unit Data'")
                changes_made += 1
            else:
                print(f"  - '{field_name}' already in 'Unit Data'")
        else:
            print(f"  ! Warning: '{field_name}' not found in config")
    
    # Update the section order to include Unit Data
    if 'section_order' in field_configs.get('Experiment', {}):
        section_order = field_configs['Experiment']['section_order']
        if 'Unit Data' not in section_order:
            # Insert Unit Data after Basic Information
            if 'Basic Information' in section_order:
                idx = section_order.index('Basic Information') + 1
                section_order.insert(idx, 'Unit Data')
                print(f"  ✓ Added 'Unit Data' to section_order")
                changes_made += 1
    
    if changes_made > 0:
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print(f"  ✅ Saved {changes_made} changes to {file_path.name}")
    else:
        print(f"  ℹ No changes needed for {file_path.name}")
    
    return changes_made

def main():
    """Update all product config files"""
    config_dir = Path('PPV/configs')
    config_files = [
        config_dir / 'GNRControlPanelConfig.json',
        config_dir / 'CWFControlPanelConfig.json',
        config_dir / 'DMRControlPanelConfig.json'
    ]
    
    total_changes = 0
    
    print("=" * 60)
    print("Updating Product Configuration Files")
    print("=" * 60)
    
    for config_file in config_files:
        if config_file.exists():
            changes = update_config_file(config_file)
            total_changes += changes
        else:
            print(f"\n❌ File not found: {config_file}")
    
    print("\n" + "=" * 60)
    print(f"✅ Complete! Total changes made: {total_changes}")
    print("=" * 60)

if __name__ == "__main__":
    main()
