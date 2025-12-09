"""
Verify that field options are properly configured in all config files
"""
import json
from pathlib import Path

def verify_field_options(file_path, product_name):
    """Verify field options in a config file"""
    print(f"\n{'=' * 60}")
    print(f"Verifying: {file_path.name} ({product_name})")
    print('=' * 60)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    field_configs = config.get('field_configs', {})
    
    # Fields that should have options
    fields_to_check = {
        "Configuration (Mask)": {
            "should_have_options": True,
            "expected_count": 6,
            "all_products": True
        },
        "Core License": {
            "should_have_options": product_name in ["GNR", "DMR"],
            "expected_count": 7,
            "all_products": False
        },
        "Disable 2 Cores": {
            "should_have_options": True,
            "expected_count": 5,
            "all_products": True
        },
        "Disable 1 Core": {
            "should_have_options": True,
            "expected_count": 2,
            "all_products": True
        }
    }
    
    all_valid = True
    
    for field_name, expectations in fields_to_check.items():
        if field_name not in field_configs:
            print(f"  ❌ Field '{field_name}' not found in config")
            all_valid = False
            continue
        
        field_config = field_configs[field_name]
        has_options = 'options' in field_config
        
        if expectations['should_have_options']:
            if has_options:
                option_count = len(field_config['options'])
                if option_count == expectations['expected_count']:
                    print(f"  ✅ {field_name:25} - {option_count} options")
                    # Show options
                    for opt in field_config['options']:
                        print(f"     • {opt}")
                else:
                    print(f"  ⚠️  {field_name:25} - {option_count} options (expected {expectations['expected_count']})")
                    all_valid = False
            else:
                print(f"  ❌ {field_name:25} - Missing options")
                all_valid = False
        else:
            if has_options:
                print(f"  ⚠️  {field_name:25} - Has options but shouldn't (product: {product_name})")
            else:
                print(f"  ✅ {field_name:25} - No options (correct for {product_name})")
    
    return all_valid

def main():
    """Verify all product config files"""
    config_dir = Path('PPV/configs')
    configs = [
        (config_dir / 'GNRControlPanelConfig.json', 'GNR'),
        (config_dir / 'CWFControlPanelConfig.json', 'CWF'),
        (config_dir / 'DMRControlPanelConfig.json', 'DMR')
    ]
    
    print("=" * 60)
    print("Field Options Configuration Verification")
    print("=" * 60)
    
    all_valid = True
    
    for config_file, product_name in configs:
        if config_file.exists():
            valid = verify_field_options(config_file, product_name)
            all_valid = all_valid and valid
        else:
            print(f"\n❌ File not found: {config_file}")
            all_valid = False
    
    print("\n" + "=" * 60)
    if all_valid:
        print("✅ All field options verified successfully!")
    else:
        print("❌ Some field options have issues")
    print("=" * 60)

if __name__ == "__main__":
    main()
