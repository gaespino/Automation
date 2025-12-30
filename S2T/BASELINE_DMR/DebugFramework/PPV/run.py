"""
THR Debug Tools - Main Entry Point

This is the main launcher for the THR Debug Tools Hub application.
(Test Hole Resolution Debug Tools)

This suite comprehends all the required tools for a proper unit characterization
and debug flow, starting from offline analysis with data collected from unit
factory testing, which is further parsed with the MCA Parser tool. The analyzed
data is used to properly select the most ROI bucket or issue, which is then
tested using Framework experiments that can be created using the Experiment Builder
or Automation Flows, generating unit reproduction and characterization data to
properly root cause and isolate issues, resulting in a more robust DPM process
with the objective of reducing DPM and increasing test effectivity in early
stages of factory testing.

Usage:
    python run.py
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
    """Main entry point for THR Debug Tools application"""
    # Display the banner in console
    display_banner()
    
    # Show product selector first
    selected_product = show_product_selector()
    
    # Exit if user cancelled
    if not selected_product:
        print("Product selection cancelled. Exiting...")
        return
    
    print(f"\nSelected Product: {selected_product}")
    print("Launching THR Debug Tools Hub...\n")
    
    # Create the main window with selected product
    root = tk.Tk()
    app = Tools(root, default_product=selected_product)
    root.mainloop()

if __name__ == "__main__":
    main()
