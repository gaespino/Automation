"""
Test to verify section marker filtering works correctly
"""

# Test data simulating widgets dictionary with various entries
test_widgets = {
    'Test Name': {'var': 'var_obj', 'type': 'str', 'widget': 'widget_obj'},
    'Test Mode': {'var': 'var_obj', 'type': 'str', 'widget': 'widget_obj'},
    'loops_section': 'section_frame_obj',
    'sweep_section': 'section_frame_obj',
    'shmoo_section': 'section_frame_obj',
    'linux_section': 'section_frame_obj',
    'dragon_section': 'section_frame_obj',
    'merlin_section': 'section_frame_obj',
    'test_configuration_section': 'section_frame_obj',
    'basic_information_section': 'section_frame_obj',
    'advanced_configuration_section': 'section_frame_obj',
    'unit_data_section': 'section_frame_obj',
    'Loops': {'var': 'var_obj', 'type': 'int', 'widget': 'widget_obj'},
    'Voltage Type': {'var': 'var_obj', 'type': 'str', 'widget': 'widget_obj'},
}

print("=" * 60)
print("Section Marker Filtering Test")
print("=" * 60)

print("\n✓ Testing endswith('_section') filter:\n")

field_count = 0
section_count = 0

for field_name, field_info in test_widgets.items():
    if field_name.endswith('_section'):
        section_count += 1
        print(f"  [SKIP] {field_name:35} (section marker)")
    else:
        field_count += 1
        print(f"  [KEEP] {field_name:35} (field)")

print("\n" + "=" * 60)
print(f"✅ Results:")
print(f"   Fields kept:    {field_count}")
print(f"   Sections skipped: {section_count}")
print("=" * 60)

# Verify counts
expected_fields = 4
expected_sections = 10

if field_count == expected_fields and section_count == expected_sections:
    print("\n✅ Test PASSED - All section markers properly filtered!")
else:
    print(f"\n❌ Test FAILED - Expected {expected_fields} fields and {expected_sections} sections")
    print(f"   Got {field_count} fields and {section_count} sections")
