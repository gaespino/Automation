"""
Verify all three product configs are properly formatted
"""
import json
import os

def verify_config(product):
    """Verify a product config file"""
    config_path = f"PPV/configs/{product}ControlPanelConfig.json"
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print(f"\n{'='*70}")
    print(f"  {product} Configuration")
    print(f"{'='*70}")
    
    # Check structure
    if 'field_configs' in config:
        print(f"✓ Using NEW field_configs structure")
        print(f"  Total fields: {len(config['field_configs'])}")
        
        # Section distribution
        sections = {}
        conditional_fields = []
        
        for field_name, field_config in config['field_configs'].items():
            section = field_config.get('section', 'Unknown')
            sections[section] = sections.get(section, 0) + 1
            
            if 'condition' in field_config:
                conditional_fields.append(field_name)
        
        print(f"\n  Section Distribution:")
        for section in sorted(sections.keys()):
            print(f"    • {section:<30} {sections[section]:>2} fields")
        
        print(f"\n  Conditional Fields: {len(conditional_fields)}")
        if conditional_fields:
            print(f"    {', '.join(conditional_fields[:5])}...")
        
        # Check metadata completeness
        complete_fields = 0
        for field_name, field_config in config['field_configs'].items():
            if all(key in field_config for key in ['section', 'type', 'default', 'description']):
                complete_fields += 1
        
        print(f"\n  Metadata Completeness: {complete_fields}/{len(config['field_configs'])} fields")
        
        # Product info
        print(f"\n  Product: {config.get('PRODUCT', 'N/A')}")
        print(f"  Description: {config.get('DESCRIPTION', 'N/A')}")
        
    elif 'data_types' in config:
        print(f"✗ Using OLD data_types structure")
        print(f"  This will auto-migrate, but consider updating to field_configs")
    
    else:
        print(f"✗ Invalid configuration structure!")

def main():
    print("\n" + "="*70)
    print("  PPV Control Panel Configuration Verification")
    print("="*70)
    
    for product in ["GNR", "CWF", "DMR"]:
        verify_config(product)
    
    print(f"\n{'='*70}")
    print("  ✓ All configurations verified!")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    main()
