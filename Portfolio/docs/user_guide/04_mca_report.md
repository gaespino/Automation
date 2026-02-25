# PPV MCA Report

URL: `/thr-tools/mca-report`

## Purpose
Generate MCA failure analysis reports from Bucketer or S2T Logger Excel files.

## Usage
1. Choose analysis sections: MESH, CORE, IO, SA (default: MESH + CORE)
2. Upload the Bucketer/S2T Excel workbook
3. Click **Generate Report**
4. The report is appended as a new sheet; the modified workbook downloads automatically

## Backend
`THRTools/parsers/MCAparser.py` — `ppv_report` class, `.run(options=[...])`
