"""
Verify Unit Data configuration is correct across all product configs
"""
import json
from pathlib import Path

def verify_config(file_path):
    """Verify a single config file"""
    print(f"\n{'=' * 60}")
    print(f"Verifying: {file_path.name}")
    print('=' * 60)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    field_configs = config.get('field_configs', {})
    
    # Expected Unit Data fields
    expected_unit_data_fields = ['Product', 'Visual ID', 'Bucket', 'COM Port', 'IP Address']
    
    # Find all Unit Data fields
    unit_data_fields = [
        field_name for field_name, field_config in field_configs.items()
        if field_config.get('section') == 'Unit Data'
    ]
    
    print(f"\n✓ Found {len(unit_data_fields)} Unit Data fields:")
    for field_name in unit_data_fields:
        field_config = field_configs[field_name]
        print(f"  - {field_name:15} ({field_config.get('type'):5}) : {field_config.get('description')}")
    
    # Check for expected fields
    print(f"\n✓ Verification:")
    all_found = True
    for expected_field in expected_unit_data_fields:
        if expected_field in unit_data_fields:
            print(f"  ✅ {expected_field}")
        else:
            print(f"  ❌ {expected_field} - MISSING!")
            all_found = False
    
    # Check that Unit Data fields are NOT in Basic Information or Advanced Configuration
    print(f"\n✓ Checking fields moved from other sections:")
    issues = []
    for field_name in ['Visual ID', 'Bucket']:
        field_config = field_configs.get(field_name, {})
        section = field_config.get('section')
        if section == 'Basic Information':
            issues.append(f"  ❌ '{field_name}' still in Basic Information")
    
    for field_name in ['COM Port', 'IP Address']:
        field_config = field_configs.get(field_name, {})
        section = field_config.get('section')
        if section == 'Advanced Configuration':
            issues.append(f"  ❌ '{field_name}' still in Advanced Configuration")
    
    if issues:
        for issue in issues:
            print(issue)
        all_found = False
    else:
        print("  ✅ All Unit Data fields properly moved")
    
    # Count fields per section
    section_counts = {}
    for field_config in field_configs.values():
        section = field_config.get('section', 'Unknown')
        section_counts[section] = section_counts.get(section, 0) + 1
    
    print(f"\n✓ Field distribution across sections:")
    for section, count in sorted(section_counts.items()):
        marker = "📋" if section == "Unit Data" else "  "
        print(f"  {marker} {section:25} : {count:2} fields")
    
    return all_found

def main():
    """Verify all product config files"""
    config_dir = Path('PPV/configs')
    config_files = [
        config_dir / 'GNRControlPanelConfig.json',
        config_dir / 'CWFControlPanelConfig.json',
        config_dir / 'DMRControlPanelConfig.json'
    ]
    
    print("=" * 60)
    print("Unit Data Configuration Verification")
    print("=" * 60)
    
    all_valid = True
    
    for config_file in config_files:
        if config_file.exists():
            valid = verify_config(config_file)
            all_valid = all_valid and valid
        else:
            print(f"\n❌ File not found: {config_file}")
            all_valid = False
    
    print("\n" + "=" * 60)
    if all_valid:
        print("✅ All configurations verified successfully!")
    else:
        print("❌ Some configurations have issues")
    print("=" * 60)

if __name__ == "__main__":
    main()
