#!/usr/bin/env python3
"""
PPV Tools - Python Dependency Installer
Cross-platform installation script for required packages
"""

import sys
import subprocess
import platform

# Required packages with versions
REQUIRED_PACKAGES = {
    'pandas': '>=1.3.0',
    'numpy': '>=1.20.0',
    'openpyxl': '>=3.0.0',
    'xlwings': '>=0.24.0',
    'colorama': '>=0.4.4',
    'tabulate': '>=0.8.9'
}

# Standard library packages (no installation needed)
STDLIB_PACKAGES = [
    'tkinter', 'json', 'os', 'sys', 're', 'zipfile', 'datetime', 
    'shutil', 'subprocess', 'http.client', 'getpass', 'collections',
    'string', 'pathlib', 'typing', 'uuid', 'argparse', 'csv', 
    'statistics', 'turtle'
]

def print_header(text):
    """Print a formatted header"""
    print('\n' + '='*70)
    print(f'  {text}')
    print('='*70 + '\n')

def check_python_version():
    """Check if Python version is 3.7 or higher"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"ERROR: Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def upgrade_pip():
    """Upgrade pip to latest version"""
    print("\nUpgrading pip to latest version...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        print("✓ pip upgraded successfully")
        return True
    except subprocess.CalledProcessError:
        print("⚠ Warning: Failed to upgrade pip, continuing with current version")
        return True

def install_package(package_name, version_spec):
    """Install a single package"""
    package_spec = f"{package_name}{version_spec}"
    print(f"\nInstalling {package_name}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_spec])
        print(f"✓ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ ERROR: Failed to install {package_name}")
        return False

def verify_installation(package_name):
    """Verify that a package is installed and get its version"""
    try:
        if package_name == 'tkinter':
            import tkinter
            return True, "bundled"
        else:
            module = __import__(package_name)
            version = getattr(module, '__version__', 'unknown')
            return True, version
    except ImportError:
        return False, None

def main():
    """Main installation process"""
    print_header("PPV TOOLS - DEPENDENCY INSTALLER")
    
    print("This script will install all required Python packages for PPV Tools.\n")
    print(f"Platform: {platform.system()} {platform.release()}")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Upgrade pip
    print_header("UPGRADING PIP")
    if not upgrade_pip():
        sys.exit(1)
    
    # Install required packages
    print_header("INSTALLING DEPENDENCIES")
    
    failed_packages = []
    for i, (package, version_spec) in enumerate(REQUIRED_PACKAGES.items(), 1):
        print(f"\n[{i}/{len(REQUIRED_PACKAGES)}] {package}...")
        if not install_package(package, version_spec):
            failed_packages.append(package)
    
    # Verify installations
    print_header("VERIFYING INSTALLATION")
    
    print("\nInstalled Packages:")
    all_success = True
    
    for package in REQUIRED_PACKAGES.keys():
        success, version = verify_installation(package)
        if success:
            print(f"  ✓ {package:15} {version}")
        else:
            print(f"  ✗ {package:15} FAILED")
            all_success = False
    
    # Check standard library packages
    print("\nStandard Library (included with Python):")
    for package in ['tkinter', 'json', 'sys', 're', 'datetime']:
        success, version = verify_installation(package)
        status = "✓" if success else "✗"
        print(f"  {status} {package}")
    
    # Final report
    print_header("INSTALLATION COMPLETE" if all_success else "INSTALLATION COMPLETED WITH ERRORS")
    
    if all_success:
        print("✓ All required packages have been successfully installed!\n")
        print("You can now run PPV Tools:")
        print("  • PPV Tools Hub:      python run.py")
        print("  • Experiment Builder: python run_experiment_builder.py")
        print("  • Run Tests:          python test_experiment_builder.py")
        print("\nFor more information, see README.md\n")
    else:
        print("⚠ Some packages failed to install:")
        for package in failed_packages:
            print(f"  - {package}")
        print("\nPlease install these packages manually:")
        for package in failed_packages:
            print(f"  pip install {package}{REQUIRED_PACKAGES[package]}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
