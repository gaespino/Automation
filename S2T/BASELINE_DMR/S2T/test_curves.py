"""
Quick test script for dump_core_curves and dump_uncore_curves functions
"""
import sys
import os

# Add the current directory to path
MAIN_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(MAIN_PATH)

import GetTesterCurves as gtc

def test_dump_functions():
	"""Test the dump_core_curves and dump_uncore_curves functions"""

	# Example visual ID - replace with actual visual ID for testing
	visual_id = input("Enter Visual ID (e.g., 'your_visual_id'): ").strip()

	if not visual_id:
		print("No visual ID provided, using example values for demonstration")
		visual_id = "EXAMPLE_VID"

	# Select product and config
	print("\nAvailable products: GNR, DMR, CWF")
	product = input("Enter product name (default: GNR): ").strip().upper() or "GNR"
	config = input("Enter config (default: XCC): ").strip().upper() or "XCC"

	# Initialize the module with product settings
	print(f"\n{'='*60}")
	print(f"Initializing GetTesterCurves for {product} - {config}")
	print(f"{'='*60}")
	try:
		gtc.set_variables(product, config)
	except Exception as e:
		print(f"Error initializing variables: {e}")
		print("Continuing with default values...")

	# Test parameters
	test_hot = input("\nUse HOT temperature? (y/n, default: y): ").strip().lower() != 'n'

	print(f"\n{'='*60}")
	print("TEST 1: dump_core_curves()")
	print(f"{'='*60}")
	try:
		# Test with a single core (core 0)
		core_num = int(input("Enter core number to test (default: 0): ").strip() or "0")
		ate_freq = input("Enter ATE frequency (default: F1): ").strip() or "F1"

		print(f"\nTesting dump_core_curves with core={core_num}, hot={test_hot}")
		data = gtc.get_voltages_core(visual_id, core=core_num, ate_freq=ate_freq, hot=test_hot)
		print(f"\nReturned {len(data)} data points for core curves")
		print("\nSample data keys:")
		for i, key in enumerate(list(data.keys())[:5]):
			print(f"  {key}: {data[key]}")
			if i >= 4:
				break
	except Exception as e:
		print(f"Error in dump_core_curves: {e}")
		import traceback
		traceback.print_exc()

	print(f"\n{'='*60}")
	print("TEST 2: dump_uncore_curves()")
	print(f"{'='*60}")
	try:
		ate_freq_uncore = input("Enter ATE frequency for uncore (default: F1): ").strip() or "F1"

		print(f"\nTesting dump_uncore_curves with hot={test_hot}")
		data = gtc.get_voltages_uncore(visual_id, ate_freq=ate_freq_uncore, hot=test_hot)
		print(f"\nReturned {len(data)} data points for uncore curves")
		print("\nSample data keys:")
		for i, key in enumerate(list(data.keys())[:5]):
			print(f"  {key}: {data[key]}")
			if i >= 4:
				break
	except Exception as e:
		print(f"Error in dump_uncore_curves: {e}")
		import traceback
		traceback.print_exc()

	print(f"\n{'='*60}")
	print("TEST 3: Direct dump_core_curves call (visual display)")
	print(f"{'='*60}")
	try:
		core_range = input("Enter core range (default: 0-4) as 'start-end': ").strip() or "0-4"
		start, end = map(int, core_range.split('-'))

		print(f"\nDumping core curves for cores {start} to {end}")
		gtc.dump_core_curves(visual_id, core=[start, end], hot=test_hot)
	except Exception as e:
		print(f"Error in direct dump_core_curves: {e}")
		import traceback
		traceback.print_exc()

	print(f"\n{'='*60}")
	print("TEST 4: Direct dump_uncore_curves call (visual display)")
	print(f"{'='*60}")
	try:
		check_domain = input("Enter domain to check (CFC/IO/MEM/all, default: all): ").strip() or "all"

		print(f"\nDumping uncore curves for domain: {check_domain}")
		gtc.dump_uncore_curves(visual_id, check=check_domain, hot=test_hot)
	except Exception as e:
		print(f"Error in direct dump_uncore_curves: {e}")
		import traceback
		traceback.print_exc()

	print(f"\n{'='*60}")
	print("Testing complete!")
	print(f"{'='*60}")

if __name__ == "__main__":
	print("="*60)
	print("GetTesterCurves Test Script")
	print("="*60)
	print("\nThis script tests the dump_core_curves and dump_uncore_curves functions")
	print("You'll need a valid Visual ID to retrieve actual DFF data")
	print()


	product = "DMR"
	config = "DMR_CLTAP"
	visual_id = "D58M6D7200035"
	cores = [0, 128]
	gtc.set_variables(product, config)
	#gtc.save_gv_array(visual_id, corner='corner', hot=True)
	gtc.dump_core_curves(visual_id, core=cores, hot=True)
	#gtc.dump_uncore_curves(visual_id, check='all', hot=True)
	#CORE, MESH, IO = gtc.get_ratios_core(1)
	#CORE, MESH, IO = gtc.get_ratios_uncore(4)
	#print('CORE: ' ,CORE)
	#print('MESH: ', MESH)
	#print('IO: ', IO)

	LICENSE = 'AMX'
	CORE = 106
	ATE_FREQ = 'F4'
	IP = 'CFC'
	DIE = 'CBO10'
	print_cfc = False
	print_core = True

	if print_core:
		DATA = gtc.get_voltages_core(visual_id, core = CORE, ate_freq=ATE_FREQ,  hot=True, force=False)
		DATA_MLC = gtc.get_voltages_mlc(visual_id, core = CORE, ate_freq=ATE_FREQ,  hot=True, force=False)
		Value = gtc.filter_core_voltage(DATA, LICENSE, CORE, ATE_FREQ)
		Value_MLC = gtc.filter_uncore_voltage(DATA_MLC, 'MLC', 'CBB0', ATE_FREQ)
		print(f'Voltage for {LICENSE} core {CORE} at {ATE_FREQ}: {Value} V')
		print(f'Voltage for MLC {CORE} at {ATE_FREQ}: {Value_MLC} V')

	if print_cfc:
		DATA = gtc.get_voltages_uncore(visual_id, ate_freq=ATE_FREQ, hot=True, force=False)
		Value = gtc.filter_uncore_voltage(DATA, IP, DIE, ATE_FREQ)
		#print(f'Voltage for {LICENSE} core {CORE} at {ATE_FREQ}: {Value} V')
		print(f'Voltage for {IP} {DIE} at {ATE_FREQ}: {Value} V')

	#test_dump_functions()
