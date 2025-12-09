"""
Test the section distribution in field configs
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PPV.gui.ExperimentBuilder import ExperimentBuilderGUI

def main():
    app = ExperimentBuilderGUI()
    config = app.config_template
    
    # Count fields per section
    section_counts = {}
    for field_name, field_config in config['field_configs'].items():
        section = field_config.get('section', 'Unknown')
        section_counts[section] = section_counts.get(section, 0) + 1
    
    print("Field Distribution by Section:")
    print("=" * 60)
    for section in sorted(section_counts.keys()):
        print(f"{section:<30} {section_counts[section]:>3} fields")
    print("=" * 60)
    print(f"{'TOTAL':<30} {sum(section_counts.values()):>3} fields")
    
    app.root.destroy()

if __name__ == '__main__':
    main()
