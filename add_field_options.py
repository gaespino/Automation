"""
Add options to special fields in all product config files
"""
import json
from pathlib import Path

def update_config_with_options(file_path, product_name):
    """Update a single config file with field options"""
    print(f"\nProcessing: {file_path.name} ({product_name})")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    field_configs = config.get('field_configs', {})
    changes_made = 0
    
    # Configuration (Mask) options - same for all products
    if "Configuration (Mask)" in field_configs:
        if 'options' not in field_configs["Configuration (Mask)"]:
            field_configs["Configuration (Mask)"]['options'] = [
                "RowPass1", "RowPass2", "RowPass3", 
                "FirstPass", "SecondPass", "ThirdPass"
            ]
            print(f"  ✓ Added options to 'Configuration (Mask)'")
            changes_made += 1
    
    # Core License options - GNR and DMR only
    if "Core License" in field_configs:
        if product_name in ["GNR", "DMR"]:
            if 'options' not in field_configs["Core License"]:
                field_configs["Core License"]['options'] = [
                    "1: SSE/128",
                    "2: AVX2/256 Light",
                    "3: AVX2/256 Heavy",
                    "4: AVX3/512 Light",
                    "5: AVX3/512 Heavy",
                    "6: TMUL Light",
                    "7: TMUL Heavy"
                ]
                print(f"  ✓ Added options to 'Core License'")
                changes_made += 1
        elif 'options' in field_configs["Core License"]:
            # Remove options for CWF
            del field_configs["Core License"]['options']
            print(f"  ✓ Removed options from 'Core License' (not applicable for {product_name})")
            changes_made += 1
    
    # Disable 2 Cores options - CWF specific, but add to all
    if "Disable 2 Cores" in field_configs:
        if 'options' not in field_configs["Disable 2 Cores"]:
            field_configs["Disable 2 Cores"]['options'] = [
                "0x3", "0xc", "0x9", "0xa", "0x5"
            ]
            print(f"  ✓ Added options to 'Disable 2 Cores'")
            changes_made += 1
    
    # Disable 1 Core options - DMR specific, but add to all
    if "Disable 1 Core" in field_configs:
        if 'options' not in field_configs["Disable 1 Core"]:
            field_configs["Disable 1 Core"]['options'] = [
                "0x1", "0x2"
            ]
            print(f"  ✓ Added options to 'Disable 1 Core'")
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
    configs = [
        (config_dir / 'GNRControlPanelConfig.json', 'GNR'),
        (config_dir / 'CWFControlPanelConfig.json', 'CWF'),
        (config_dir / 'DMRControlPanelConfig.json', 'DMR')
    ]
    
    total_changes = 0
    
    print("=" * 60)
    print("Adding Field Options to Configuration Files")
    print("=" * 60)
    
    for config_file, product_name in configs:
        if config_file.exists():
            changes = update_config_with_options(config_file, product_name)
            total_changes += changes
        else:
            print(f"\n❌ File not found: {config_file}")
    
    print("\n" + "=" * 60)
    print(f"✅ Complete! Total changes made: {total_changes}")
    print("=" * 60)

if __name__ == "__main__":
    main()
