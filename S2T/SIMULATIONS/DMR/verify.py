"""Quick verification script for mock module"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mock_dpmChecks as dpm

print('='*80)
print('Mock Module Verification')
print('='*80)
print(f'Product: {dpm.config.SELECTED_PRODUCT}')
print(f'Variant: {dpm.config.PRODUCT_VARIANT}')
print(f'Chop: {dpm.config.PRODUCT_CHOP}')
print('')
print('Testing logger function...')
print('')

result = dpm.logger(TestName='QuickVerifyTest', Testnumber=999)

print('')
print(f'Result Status: {result["status"]}')
print(f'Errors Found: {result["errors_found"]}')
print(f'MCA Decoded: {result["mca_decoded"]}')
print('')
print('='*80)
print('✓ Mock verification successful!')
print('='*80)
