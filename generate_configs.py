"""
Generate updated config files with enhanced field_configs structure
"""
import json
import os

# Enhanced field_configs template with proper section assignments
FIELD_CONFIGS = {
    "Experiment": {"section": "Basic Information", "type": "str", "default": "", "description": "Experiment name/identifier", "required": True},
    "Test Name": {"section": "Basic Information", "type": "str", "default": "", "description": "Unique test identifier", "required": True},
    "Test Mode": {"section": "Basic Information", "type": "str", "default": "Mesh", "description": "Test execution mode", "required": True, "options": ["Mesh", "Slice"]},
    "Test Type": {"section": "Basic Information", "type": "str", "default": "Loops", "description": "Type of test to run", "required": True, "options": ["Loops", "Sweep", "Shmoo"]},
    "Visual ID": {"section": "Basic Information", "type": "str", "default": "", "description": "Visual identifier for UI display", "required": False},
    "Bucket": {"section": "Basic Information", "type": "str", "default": "", "description": "Test bucket/category classification", "required": False},
    
    "COM Port": {"section": "Advanced Configuration", "type": "int", "default": 1, "description": "Serial COM port number for communication", "required": False},
    "IP Address": {"section": "Advanced Configuration", "type": "str", "default": "", "description": "Target device IP address", "required": False},
    "TTL Folder": {"section": "Advanced Configuration", "type": "str", "default": "", "description": "TTL scripts folder path", "required": False},
    "Scripts File": {"section": "Advanced Configuration", "type": "str", "default": "", "description": "Test scripts file path", "required": False},
    "Pass String": {"section": "Advanced Configuration", "type": "str", "default": "", "description": "String pattern indicating test pass", "required": False},
    "Fail String": {"section": "Advanced Configuration", "type": "str", "default": "", "description": "String pattern indicating test failure", "required": False},
    "Stop on Fail": {"section": "Advanced Configuration", "type": "bool", "default": False, "description": "Stop test execution on first failure", "required": False},
    
    "Content": {"section": "Test Configuration", "type": "str", "default": "Linux", "description": "Content type to execute", "required": False, "options": ["Linux", "Dragon", "PYSVConsole"]},
    "Test Number": {"section": "Test Configuration", "type": "int", "default": 0, "description": "Test sequence number", "required": False},
    "Test Time": {"section": "Test Configuration", "type": "int", "default": 0, "description": "Test timeout in seconds", "required": False},
    "Reset": {"section": "Test Configuration", "type": "bool", "default": False, "description": "Reset system before test", "required": False},
    "Reset on PASS": {"section": "Test Configuration", "type": "bool", "default": False, "description": "Reset system after successful test", "required": False},
    "FastBoot": {"section": "Test Configuration", "type": "bool", "default": False, "description": "Enable fast boot mode", "required": False},
    "Core License": {"section": "Test Configuration", "type": "str", "default": "", "description": "Core license key", "required": False},
    "600W Unit": {"section": "Test Configuration", "type": "bool", "default": False, "description": "Use 600W power supply unit", "required": False},
    "Pseudo Config": {"section": "Test Configuration", "type": "bool", "default": False, "description": "Enable pseudo configuration mode", "required": False},
    "Post Process": {"section": "Test Configuration", "type": "str", "default": "", "description": "Post-processing script to execute", "required": False},
    "Configuration (Mask)": {"section": "Test Configuration", "type": "str", "default": "", "description": "Configuration mask value", "required": False},
    "Boot Breakpoint": {"section": "Test Configuration", "type": "str", "default": "", "description": "Boot breakpoint location", "required": False},
    "Disable 2 Cores": {"section": "Test Configuration", "type": "str", "default": "", "description": "Cores to disable (2-core configuration)", "required": False},
    "Disable 1 Core": {"section": "Test Configuration", "type": "str", "default": "", "description": "Core to disable (1-core configuration)", "required": False},
    "Check Core": {"section": "Test Configuration", "type": "int", "default": 0, "description": "Specific core to check/monitor", "required": False},
    
    "Voltage Type": {"section": "Voltage & Frequency", "type": "str", "default": "vbump", "description": "Voltage control type", "required": False, "options": ["vbump", "fixed", "ppvc"]},
    "Voltage IA": {"section": "Voltage & Frequency", "type": "float", "default": 0.0, "description": "IA domain voltage level (V)", "required": False},
    "Voltage CFC": {"section": "Voltage & Frequency", "type": "float", "default": 0.0, "description": "CFC domain voltage level (V)", "required": False},
    "Frequency IA": {"section": "Voltage & Frequency", "type": "int", "default": 0, "description": "IA domain frequency (MHz)", "required": False},
    "Frequency CFC": {"section": "Voltage & Frequency", "type": "int", "default": 0, "description": "CFC domain frequency (MHz)", "required": False},
    
    "Loops": {"section": "Loops", "type": "int", "default": 1, "description": "Number of test iterations to execute", "required": False, "condition": {"field": "Test Type", "value": "Loops"}},
    
    "Type": {"section": "Sweep", "type": "str", "default": "Voltage", "description": "Parameter type to sweep", "required": False, "options": ["Voltage", "Frequency"], "condition": {"field": "Test Type", "value": "Sweep"}},
    "Domain": {"section": "Sweep", "type": "str", "default": "IA", "description": "Domain to sweep", "required": False, "options": ["CFC", "IA"], "condition": {"field": "Test Type", "value": "Sweep"}},
    "Start": {"section": "Sweep", "type": "float", "default": 0.0, "description": "Sweep start value", "required": False, "condition": {"field": "Test Type", "value": "Sweep"}},
    "End": {"section": "Sweep", "type": "float", "default": 0.0, "description": "Sweep end value", "required": False, "condition": {"field": "Test Type", "value": "Sweep"}},
    "Steps": {"section": "Sweep", "type": "float", "default": 1.0, "description": "Sweep step size/increment", "required": False, "condition": {"field": "Test Type", "value": "Sweep"}},
    
    "ShmooFile": {"section": "Shmoo", "type": "str", "default": "", "description": "Shmoo configuration file path", "required": False, "condition": {"field": "Test Type", "value": "Shmoo"}},
    "ShmooLabel": {"section": "Shmoo", "type": "str", "default": "", "description": "Shmoo label/identifier", "required": False, "condition": {"field": "Test Type", "value": "Shmoo"}},
    
    "Linux Path": {"section": "Linux", "type": "str", "default": "", "description": "Linux binary/script path", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Pre Command": {"section": "Linux", "type": "str", "default": "", "description": "Command to execute before Linux test", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Post Command": {"section": "Linux", "type": "str", "default": "", "description": "Command to execute after Linux test", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Pass String": {"section": "Linux", "type": "str", "default": "", "description": "String pattern indicating Linux test pass", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Fail String": {"section": "Linux", "type": "str", "default": "", "description": "String pattern indicating Linux test failure", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Content Wait Time": {"section": "Linux", "type": "int", "default": 0, "description": "Wait time in seconds before checking Linux content", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Startup Linux": {"section": "Linux", "type": "str", "default": "", "description": "Linux startup script/command", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Content Line 0": {"section": "Linux", "type": "str", "default": "", "description": "Linux content command line 0", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Content Line 1": {"section": "Linux", "type": "str", "default": "", "description": "Linux content command line 1", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Content Line 2": {"section": "Linux", "type": "str", "default": "", "description": "Linux content command line 2", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Content Line 3": {"section": "Linux", "type": "str", "default": "", "description": "Linux content command line 3", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Content Line 4": {"section": "Linux", "type": "str", "default": "", "description": "Linux content command line 4", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Content Line 5": {"section": "Linux", "type": "str", "default": "", "description": "Linux content command line 5", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Content Line 6": {"section": "Linux", "type": "str", "default": "", "description": "Linux content command line 6", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Content Line 7": {"section": "Linux", "type": "str", "default": "", "description": "Linux content command line 7", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Content Line 8": {"section": "Linux", "type": "str", "default": "", "description": "Linux content command line 8", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    "Linux Content Line 9": {"section": "Linux", "type": "str", "default": "", "description": "Linux content command line 9", "required": False, "condition": {"field": "Content", "value": "Linux"}},
    
    "Dragon Pre Command": {"section": "Dragon", "type": "str", "default": "", "description": "Command to execute before Dragon test", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    "Dragon Post Command": {"section": "Dragon", "type": "str", "default": "", "description": "Command to execute after Dragon test", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    "Startup Dragon": {"section": "Dragon", "type": "str", "default": "", "description": "Dragon startup script/command", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    "ULX Path": {"section": "Dragon", "type": "str", "default": "", "description": "ULX file path for Dragon", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    "ULX CPU": {"section": "Dragon", "type": "str", "default": "", "description": "ULX CPU identifier/configuration", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    "Product Chop": {"section": "Dragon", "type": "str", "default": "", "description": "Product chop identifier", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    "VVAR0": {"section": "Dragon", "type": "str", "default": "", "description": "Dragon variable 0", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    "VVAR1": {"section": "Dragon", "type": "str", "default": "", "description": "Dragon variable 1", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    "VVAR2": {"section": "Dragon", "type": "str", "default": "", "description": "Dragon variable 2", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    "VVAR3": {"section": "Dragon", "type": "str", "default": "", "description": "Dragon variable 3", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    "VVAR_EXTRA": {"section": "Dragon", "type": "str", "default": "", "description": "Dragon extra variables", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    "Dragon Content Path": {"section": "Dragon", "type": "str", "default": "", "description": "Dragon content file path", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    "Dragon Content Line": {"section": "Dragon", "type": "str", "default": "", "description": "Dragon content command line", "required": False, "condition": {"field": "Content", "value": "Dragon"}},
    
    "Merlin Name": {"section": "Merlin", "type": "str", "default": "", "description": "Merlin configuration name", "required": False},
    "Merlin Drive": {"section": "Merlin", "type": "str", "default": "", "description": "Merlin drive letter/path", "required": False},
    "Merlin Path": {"section": "Merlin", "type": "str", "default": "", "description": "Merlin executable path", "required": False},
    "Fuse File": {"section": "Merlin", "type": "str", "default": "", "description": "Fuse configuration file path", "required": False},
    "Bios File": {"section": "Merlin", "type": "str", "default": "", "description": "BIOS file path", "required": False},
}

PRODUCTS = {
    "GNR": {
        "name": "GNR",
        "description": "GNR (Granite Rapids) Control Panel Configuration"
    },
    "CWF": {
        "name": "CWF",
        "description": "CWF (Clearwater Forest) Control Panel Configuration"
    },
    "DMR": {
        "name": "DMR",
        "description": "DMR (Diamond Rapids) Control Panel Configuration"
    }
}

def generate_config(product_code):
    """Generate enhanced config for a product"""
    product = PRODUCTS[product_code]
    
    config = {
        "field_configs": FIELD_CONFIGS,
        "TEST_MODES": ["Mesh", "Slice"],
        "TEST_TYPES": ["Loops", "Sweep", "Shmoo"],
        "CONTENT_OPTIONS": ["Linux", "Dragon", "PYSVConsole"],
        "VOLTAGE_TYPES": ["vbump", "fixed", "ppvc"],
        "TYPES": ["Voltage", "Frequency"],
        "DOMAINS": ["CFC", "IA"],
        "PRODUCT": product["name"],
        "DESCRIPTION": product["description"],
        "field_enable_config": {
            "Pseudo Config": ["GNR"],
            "Disable 2 Cores": ["CWF"],
            "Disable 1 Core": ["DMR"],
            "Core License": ["GNR", "DMR"]
        }
    }
    
    return config

def main():
    """Generate all config files"""
    configs_dir = os.path.join(os.path.dirname(__file__), 'PPV', 'configs')
    
    for product_code in ["GNR", "CWF", "DMR"]:
        config = generate_config(product_code)
        output_file = os.path.join(configs_dir, f"{product_code}ControlPanelConfig.json")
        
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"✓ Generated {product_code}ControlPanelConfig.json")
        print(f"  - {len(config['field_configs'])} fields configured")
        
        # Count fields per section
        sections = {}
        for field_config in config['field_configs'].values():
            section = field_config['section']
            sections[section] = sections.get(section, 0) + 1
        
        print(f"  - {len(sections)} sections:")
        for section, count in sorted(sections.items()):
            print(f"      • {section}: {count} fields")
        print()
    
    print("=" * 60)
    print("✓ All configuration files generated successfully!")
    print("=" * 60)

if __name__ == '__main__':
    main()
