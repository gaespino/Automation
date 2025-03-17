## MCA Fail detection -- Algorithm to check for next steps and root cause analysis
## Gaespino - April -2025

#import sys
#import os
import json
import re
import pandas as pd
from pathlib import Path
import os

# Load the CSV file into a DataFrame
df = pd.read_csv('gnrtileconfig.csv')

ROWs = [1,2,3,4,5,6,7]
COLs = [0,1,2,3,4,5,7,8,9]
IPrange = [r for r in range(0,180)]
GNRtile = {}

for index, row in df.iterrows():
    die = row['DIE']
    core = row['CORE']
    row_val = row['Row']
    col_val = row['Col']
    
    if die not in GNRtile:
        GNRtile[die] = {}
    
    GNRtile[die][core] = {'row': row_val, 'col': col_val}

print(GNRtile)