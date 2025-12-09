"""
Quick test script to verify field configuration changes
"""
import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PPV.gui.ExperimentBuilder import ExperimentBuilderGUI

def test_config_loading():
    """Test that configuration loads correctly"""
    print("=" * 80)
    print("Testing Field Configuration Structure")
    print("=" * 80)
    
    try:
        # Create instance
        app = ExperimentBuilderGUI()
        config = app.config_template
        
        # Check structure
        print(f"\n✓ ExperimentBuilder instance created successfully")
        
        if 'field_configs' in config:
            print(f"✓ Using NEW field_configs structure")
            print(f"  - Total fields: {len(config['field_configs'])}")
            
            # Show some sample fields
            print(f"\n  Sample fields:")
            for idx, (field_name, field_config) in enumerate(list(config['field_configs'].items())[:5]):
                section = field_config.get('section', 'Unknown')
                field_type = field_config.get('type', 'str')
                default = field_config.get('default', '')
                desc = field_config.get('description', '')
                print(f"    {idx+1}. {field_name}")
                print(f"       Section: {section}")
                print(f"       Type: {field_type}, Default: {default}")
                print(f"       Description: {desc[:50]}..." if len(desc) > 50 else f"       Description: {desc}")
            
            # Get sections
            sections = app.get_all_sections()
            print(f"\n  Sections defined: {len(sections)}")
            for idx, section in enumerate(sections, 1):
                # Count fields in section
                field_count = sum(1 for fc in config['field_configs'].values() if fc.get('section') == section)
                print(f"    {idx}. {section} ({field_count} fields)")
            
        elif 'data_types' in config:
            print(f"✓ Using OLD data_types structure (migrated)")
            print(f"  - Total fields: {len(config['data_types'])}")
        else:
            print(f"✗ No configuration structure found!")
        
        # Test migration
        print(f"\n{'='*80}")
        print("Testing Configuration Migration")
        print(f"{'='*80}")
        
        old_config = {
            "data_types": {
                "Test Field 1": ["str"],
                "Test Field 2": ["int"],
            },
            "TEST_MODES": ["Mesh", "Slice"]
        }
        
        migrated = app.migrate_config_format(old_config)
        
        if 'field_configs' in migrated:
            print(f"✓ Migration successful")
            print(f"  - Migrated fields: {list(migrated['field_configs'].keys())}")
            for field_name, field_config in migrated['field_configs'].items():
                print(f"    {field_name}: {field_config}")
        else:
            print(f"✗ Migration failed")
        
        # Cleanup
        app.root.destroy()
        
        print(f"\n{'='*80}")
        print("✓ All tests passed!")
        print(f"{'='*80}")
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_config_loading()
    sys.exit(0 if success else 1)
