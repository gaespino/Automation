# DMR MCA Checker Templates

## Overview
This directory contains Excel template files for DMR (Diamond Rapids) MCA analysis and reporting.

## Required Template Files

The following template files need to be created for DMR:

1. **##Name##_##w##_##LABEL##_PPV_Data.xlsx**
   - Main data file with filtered MCA data
   - Contains sheets: CHA, CORE, PPV, raw_data
   - Tables: cha_mc, core_mc, ppv
   - Used for all reduced and non-reduced data modes

2. **##Name##_##w##_##LABEL##_PPV_MC_Checker.xlsm**
   - Macro-enabled MCA checker workbook
   - Contains VBA macros for highlighting and analysis
   - Copies data from Data.xlsx file
   - Optional - enabled via "MCA Checker" checkbox

3. **##Name##_##w##_##LABEL##_PPV_Unit_Overview.xlsx**
   - Unit overview summary file
   - Only used when "Overview" checkbox is selected
   - Requires "Reduced" mode to be enabled

4. **##Name##_##w##_##LABEL##_PPV_Next_Steps.xlsx**
   - Next steps tracking file (optional)
   - Not currently used by MCAparser

## DMR-Specific Considerations

### Register Naming Differences
- **CCF**: DMR uses I_CCF_ENV{0-3}__CBREGS_ALL{00-77} instead of CHA
- **SCA**: DMR uses SCF__SCA for LLC (Last Level Cache)
- **Core Banks**: Same as GNR (IFU_CR_MC0, DCU_CR_MC1, DTLB_CR_MC2, ML2_CR_MC3)

### MCA Decoding
DMR uses the DMR-specific decoder (`decoder_dmr.py`) which supports:
- CCF decoding (Bank 6) - 32 merged instances across 4 ENVs
- Core decoding (Banks 0-3) - BigCore (PNC) architecture
- SCA/LLC decoding (Bank 14) - 16 instances per IMH

### Template Structure
The templates should mirror GNR templates but with DMR-specific:
- Column headers for CCF/ENV/Instance instead of CHA
- SCA references instead of LLC
- CBB and IMH domain organization
- Port ID decoding for dual-domain architecture

## Setup Instructions

1. Copy GNR templates as starting point:
   ```
   copy ..\\GNR\\*.xlsx .\\
   copy ..\\GNR\\*.xlsm .\\
   ```

2. Modify templates for DMR:
   - Update sheet names and table references if needed
   - Adjust column headers for DMR register naming
   - Update VBA macros in .xlsm file if applicable

3. Test with DMR data:
   - Run PPVDataChecks.py with Product = "DMR"
   - Verify data parsing and MCA decoding
   - Validate Overview and MCA Checker outputs

## Notes
- Templates use placeholder syntax: ##Name##, ##w##, ##LABEL##
- MCAparser.py automatically replaces placeholders with user input
- DMR decoder is automatically invoked when Product = "DMR"
