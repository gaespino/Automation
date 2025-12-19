"""Test the product selector"""
import sys
sys.path.insert(0, 'PPV')

from gui.ProductSelector import show_product_selector

print("Opening product selector...")
selected = show_product_selector()
print(f"Selected product: {selected}")
