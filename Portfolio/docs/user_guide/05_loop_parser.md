# PTC Loop Parser

URL: `/thr-tools/loop-parser`

## Purpose
Parse PTC experiment log files and produce a structured Excel output.

## Usage
1. Fill in **Bucket**, **Lots Seq Key**, **Start WW**, and **Output Name`n2. Toggle ZIP input / DPMB format output as needed
3. Upload log files
4. Click **Parse Logs**
5. Output Excel downloads automatically

## Backend
`THRTools/parsers/PPVLoopsParser.py`  `LogsPTC` class
