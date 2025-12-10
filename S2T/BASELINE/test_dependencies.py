"""
BASELINE Dependencies Test Script
==================================
Tests all external package imports to verify environment setup.

Usage:
    python test_dependencies.py
"""

def test_external_imports():
    """Test all external package imports"""
    errors = []
    warnings = []
    
    print("=" * 60)
    print("BASELINE Dependencies Test")
    print("=" * 60)
    print("\n📦 Testing External Packages (pip/conda):\n")
    
    # External packages
    try:
        import pandas
        print(f"✓ pandas {pandas.__version__}")
    except ImportError as e:
        errors.append(f"✗ pandas: {e}")
        print(f"✗ pandas - NOT FOUND")
    
    try:
        import numpy
        print(f"✓ numpy {numpy.__version__}")
    except ImportError as e:
        errors.append(f"✗ numpy: {e}")
        print(f"✗ numpy - NOT FOUND")
    
    try:
        import openpyxl
        print(f"✓ openpyxl {openpyxl.__version__}")
    except ImportError as e:
        errors.append(f"✗ openpyxl: {e}")
        print(f"✗ openpyxl - NOT FOUND")
    
    try:
        import xlwings
        print(f"✓ xlwings {xlwings.__version__}")
    except ImportError as e:
        errors.append(f"✗ xlwings: {e}")
        print(f"✗ xlwings - NOT FOUND")
    
    try:
        import pymongo
        print(f"✓ pymongo {pymongo.__version__}")
    except ImportError as e:
        errors.append(f"✗ pymongo: {e}")
        print(f"✗ pymongo - NOT FOUND")
    
    try:
        import colorama
        print(f"✓ colorama {colorama.__version__}")
    except ImportError as e:
        errors.append(f"✗ colorama: {e}")
        print(f"✗ colorama - NOT FOUND")
    
    try:
        import tabulate
        print(f"✓ tabulate {tabulate.__version__}")
    except ImportError as e:
        errors.append(f"✗ tabulate: {e}")
        print(f"✗ tabulate - NOT FOUND")
    
    try:
        import pytz
        print(f"✓ pytz {pytz.__version__}")
    except ImportError as e:
        errors.append(f"✗ pytz: {e}")
        print(f"✗ pytz - NOT FOUND")
    
    try:
        import psutil
        print(f"✓ psutil {psutil.__version__}")
    except ImportError as e:
        errors.append(f"✗ psutil: {e}")
        print(f"✗ psutil - NOT FOUND")
    
    try:
        import lxml
        print(f"✓ lxml {lxml.__version__}")
    except ImportError as e:
        errors.append(f"✗ lxml: {e}")
        print(f"✗ lxml - NOT FOUND")
    
    # Intel-specific tools
    print("\n🏢 Testing Intel-Specific Tools:\n")
    
    try:
        import ipccli
        print(f"✓ ipccli")
    except ImportError as e:
        warnings.append(f"⚠ ipccli: {e}")
        print(f"⚠ ipccli - NOT FOUND (Intel tool)")
    
    try:
        import namednodes
        print(f"✓ namednodes")
    except ImportError as e:
        warnings.append(f"⚠ namednodes: {e}")
        print(f"⚠ namednodes - NOT FOUND (Intel tool)")
    
    try:
        import svtools
        print(f"✓ svtools")
    except ImportError as e:
        warnings.append(f"⚠ svtools: {e}")
        print(f"⚠ svtools - NOT FOUND (Intel tool)")
    
    try:
        import toolext
        print(f"✓ toolext")
    except ImportError as e:
        warnings.append(f"⚠ toolext: {e}")
        print(f"⚠ toolext - NOT FOUND (Intel tool)")
    
    # Standard library (should always work)
    print("\n📚 Testing Standard Library Modules:\n")
    
    std_modules = [
        'sys', 'os', 'json', 'time', 'datetime', 'threading',
        'multiprocessing', 'queue', 're', 'pathlib', 'shutil',
        'subprocess', 'socket', 'uuid', 'tempfile', 'logging'
    ]
    
    std_ok = 0
    for mod_name in std_modules:
        try:
            __import__(mod_name)
            std_ok += 1
        except ImportError:
            errors.append(f"✗ {mod_name} (standard library)")
    
    print(f"✓ Standard library: {std_ok}/{len(std_modules)} modules OK")
    
    # Results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ {len(errors)} CRITICAL ERRORS (missing required packages):")
        for error in errors:
            print(f"  {error}")
        print("\n💡 Install missing packages with:")
        print("   pip install -r requirements.txt")
    else:
        print("\n✅ All required external packages are installed!")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} WARNINGS (Intel-specific tools):")
        for warning in warnings:
            print(f"  {warning}")
        print("\n💡 Intel tools are only available on Intel development systems.")
        print("   Some features may not work without these tools.")
    else:
        print("\n✅ All Intel-specific tools are available!")
    
    print("\n" + "=" * 60)
    
    if not errors:
        print("✅ Environment is ready for BASELINE framework!")
        return True
    else:
        print("❌ Please install missing packages before running BASELINE.")
        return False


if __name__ == "__main__":
    import sys
    success = test_external_imports()
    sys.exit(0 if success else 1)
