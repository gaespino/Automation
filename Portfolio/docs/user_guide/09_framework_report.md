# Framework Report Builder

URL: `/thr-tools/framework-report`

## Purpose
Build multi-sheet experiment summary reports from DebugFramework DataFrames.

## Usage
1. Upload 7 DataFrame files: Test, Summary, Fail Info, VVAR, MCA, Core, Dragon
2. Set output report filename
3. Click **Build Report**

Missing DataFrames are replaced with empty frames with a warning.

## Backend
`THRTools/parsers/FrameworkAnalyzer.py`  `ExperimentSummaryAnalyzer` class
