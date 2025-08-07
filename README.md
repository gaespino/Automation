# Automation

 Libraries required:
 
    - Xlwings - Used to edit Excel files with array formulas
        ○ pip install pandas xlwings --proxy http://proxy-dmz.intel.com:911/
    - Pandas - Data handling
        ○ pip install pandas --proxy http://proxy-dmz.intel.com:911/
    - Openpyxl - General Excel data manipulation
        ○ pip install openpyxl --proxy http://proxy-dmz.intel.com:911/
    - Colorama - Console warnings
        ○ pip install colorama --proxy http://proxy-dmz.intel.com:911/
 

# Tools for PPV / RVP / PTC Log manipulation

 Use PPVTools.py as the main menu for all the tools.

Scripts that can be used from the menu:

 PPV MCA Parser
 PTC Loops Parser
 DPMB
 FIle Handler

MCA Parser uses DPMB report format as base, decodes the MCA data into a more readable and usable format, as well as an Overview file that can works as a dashboard for DPM Purposes.
PTC Loop Parser, outputs a file in the format of DPMB report, so it can be consumed by the MCA Parser.
DPMB connects to the Bucketer API to generate the PPV units reports based on VIDs lists and WW selected.
File Handler, is a miscellaneous script used to Merge previous Excel reports into one, for data consolidation purposes

# Shmoo Parser

Use GNRShmoo.py to open the UI, this tool can generate a graphical Shmoo based on Tester logs, ituff data or VPO numbers.
