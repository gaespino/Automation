"""
Test script to verify Experiment Builder can be imported and initialized
without launching the full GUI (for automated testing)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import():
    """Test that the module can be imported"""
    try:
        from gui.ExperimentBuilder import ExperimentBuilderGUI
        print("✓ ExperimentBuilder module imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import ExperimentBuilder: {e}")
        return False

def test_template_loading():
    """Test that the config template can be loaded"""
    try:
        from gui.ExperimentBuilder import ExperimentBuilderGUI
        
        # Create a mock class to test template loading without GUI
        class MockBuilder:
            def get_default_template(self):
                return ExperimentBuilderGUI.get_default_template(self)
        
        mock = MockBuilder()
        template = mock.get_default_template()
        
        if 'data_types' in template:
            print(f"✓ Config template loaded successfully ({len(template['data_types'])} fields)")
            return True
        else:
            print("✗ Config template missing 'data_types'")
            return False
    except Exception as e:
        print(f"✗ Failed to load template: {e}")
        return False

def test_default_experiment():
    """Test that default experiment data can be created"""
    try:
        from gui.ExperimentBuilder import ExperimentBuilderGUI
        
        class MockBuilder:
            def __init__(self):
                self.config_template = self.get_default_template()
            
            def get_default_template(self):
                return ExperimentBuilderGUI.get_default_template(self)
            
            def create_default_experiment_data(self):
                return ExperimentBuilderGUI.create_default_experiment_data(self)
        
        mock = MockBuilder()
        exp_data = mock.create_default_experiment_data()
        
        if exp_data and 'Test Name' in exp_data:
            print(f"✓ Default experiment created successfully ({len(exp_data)} fields)")
            return True
        else:
            print("✗ Default experiment creation failed")
            return False
    except Exception as e:
        print(f"✗ Failed to create default experiment: {e}")
        return False

def test_excel_template_exists():
    """Test that the Excel template was created"""
    template_path = os.path.join(os.path.dirname(__file__), 'gui', 'Experiment_Template_Sample.xlsx')
    if os.path.exists(template_path):
        print(f"✓ Excel template exists: {os.path.basename(template_path)}")
        return True
    else:
        print(f"✗ Excel template not found at: {template_path}")
        return False

def test_documentation_exists():
    """Test that documentation files exist"""
    docs = [
        'gui/EXPERIMENT_BUILDER_README.md',
        'gui/QUICK_START.md',
        'gui/IMPLEMENTATION_SUMMARY.md'
    ]
    
    all_exist = True
    for doc in docs:
        doc_path = os.path.join(os.path.dirname(__file__), doc)
        if os.path.exists(doc_path):
            print(f"✓ Documentation exists: {os.path.basename(doc)}")
        else:
            print(f"✗ Documentation missing: {doc}")
            all_exist = False
    
    return all_exist

def run_all_tests():
    """Run all tests"""
    print("="*70)
    print("PPV Experiment Builder - Verification Tests")
    print("="*70)
    print()
    
    tests = [
        ("Import Test", test_import),
        ("Template Loading Test", test_template_loading),
        ("Default Experiment Test", test_default_experiment),
        ("Excel Template Test", test_excel_template_exists),
        ("Documentation Test", test_documentation_exists)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "="*70)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*70)
    
    if all(results):
        print("\n🎉 All tests passed! Experiment Builder is ready to use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
