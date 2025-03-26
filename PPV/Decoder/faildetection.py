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
parent_dir =Path(__file__).parent #split(file_NAME)[0]
csvfile = 'gnrtileconfig.csv'
csvpath= os.path.join(parent_dir, csvfile)

df = pd.read_csv(csvpath)

ROWs = [1,2,3,4,5,6,7]
COLs = [0,1,2,3,4,5,7,8,9]
PortIDrange = [r for r in range(0,256)]
GNRtile = {}

for index, row in df.iterrows():
    die = row['DIE']
    core = row['CORE']
    row_val = row['Row']
    col_val = row['Col']
    
    if die not in GNRtile:
        GNRtile[die] = {}
    
    GNRtile[die][core] = {'row': row_val, 'col': col_val}

#print(GNRtile)