"""
Test Runner Script for ControlPanel Offline Testing
Provides different test modes and configurations
"""

import sys
import os
import argparse
from TestControlPanel import TestControlPanelOffline, main

def run_quick_test():
    """Run a quick functionality test"""
    print("Running quick functionality test...")
    test_app = TestControlPanelOffline()
    
    # Auto-run a quick test sequence
    test_app.root.after(1000, test_app.simulate_success_run)
    test_app.root.after(15000, test_app.reset_all_tests)
    test_app.root.after(17000, lambda: test_app.control_panel.log_status("[TEST] Quick test completed"))
    
    test_app.run()

def run_animation_test():
    """Run animation-focused test"""
    print("Running animation test...")
    test_app = TestControlPanelOffline()
    
    # Auto-run animation tests
    test_app.root.after(1000, test_app.control_panel.verify_animations)
    
    test_app.run()

def run_stress_test():
    """Run stress test with multiple scenarios"""
    print("Running stress test...")
    test_app = TestControlPanelOffline()
    
    # Auto-run comprehensive test
    test_app.root.after(1000, test_app.run_comprehensive_test)
    
    test_app.run()

def main_with_args():
    """Main function with command line arguments"""
    
    parser = argparse.ArgumentParser(description='ControlPanel Offline Test Unit')
    parser.add_argument('--mode', choices=['interactive', 'quick', 'animation', 'stress'], 
                       default='interactive', help='Test mode to run')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Running in {args.mode} mode with verbose output")
    
    if args.mode == 'quick':
        run_quick_test()
    elif args.mode == 'animation':
        run_animation_test()
    elif args.mode == 'stress':
        run_stress_test()
    else:
        main()  # Interactive mode

if __name__ == "__main__":
    main_with_args()