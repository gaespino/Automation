"""
PPV Tools - Main Entry Point

This is the main launcher for the PPV Tools Hub application.
Run this file to start the PPV Tools interface.

Usage:
    python run_ppv_tools.py
"""

import sys
import os

# Add the current directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk

# Import after adding to path
from gui.PPVTools import Tools, display_banner
from gui.ProductSelector import show_product_selector

def main():
    """Main entry point for PPV Tools application"""
    # Display the banner in console
    display_banner()
    
    # Show product selector first
    selected_product = show_product_selector()
    
    # Exit if user cancelled
    if not selected_product:
        print("Product selection cancelled. Exiting...")
        return
    
    print(f"\nSelected Product: {selected_product}")
    print("Launching PPV Tools Hub...\n")
    
    # Create the main window with selected product
    root = tk.Tk()
    app = Tools(root, default_product=selected_product)
    root.mainloop()

if __name__ == "__main__":
    main()
