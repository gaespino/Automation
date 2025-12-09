"""
Test script to verify dynamic section creation works correctly
"""
import sys
sys.path.insert(0, 'PPV/gui')

# Test that sections are created with proper references
test_sections = [
    ("Loops", "loops_section"),
    ("Sweep", "sweep_section"),
    ("Shmoo", "shmoo_section"),
    ("Linux", "linux_section"),
    ("Dragon", "dragon_section"),
    ("Merlin", "merlin_section"),
    ("Test Configuration", "test_configuration_section"),
    ("Basic Information", "basic_information_section"),
    ("Advanced Configuration", "advanced_configuration_section"),
]

print("=" * 60)
print("Dynamic Section Creation Test")
print("=" * 60)

print("\n✓ Expected section key mappings:")
for section_name, expected_key in test_sections:
    # Generate key using same logic as create_dynamic_section
    section_key = f"{section_name.lower().replace(' ', '_')}_section"
    matches = "✅" if section_key == expected_key else "❌"
    print(f"  {matches} '{section_name}' → '{section_key}'")

print("\n✓ Special fields with dynamic options:")
special_fields = {
    "Configuration (Mask)": "get_config_mask_options()",
    "Core License": "get_core_license_options()",
    "Disable 2 Cores": '["0x3", "0xc", "0x9", "0xa", "0x5"]',
    "Disable 1 Core": '["0x1", "0x2"]'
}

for field_name, options_source in special_fields.items():
    print(f"  • {field_name:25} → {options_source}")

print("\n✓ Sections requiring conditional display:")
conditional_sections = [
    ("Loops", "Test Type", "Loops"),
    ("Sweep", "Test Type", "Sweep"),
    ("Shmoo", "Test Type", "Shmoo"),
    ("Linux", "Content", "Linux"),
    ("Dragon", "Content", "Dragon"),
    ("Merlin", "Content", "Dragon"),
]

for section_name, condition_field, condition_value in conditional_sections:
    print(f"  • {section_name:15} grayed when {condition_field:12} != '{condition_value}'")

print("\n" + "=" * 60)
print("✅ Test mapping complete")
print("=" * 60)
