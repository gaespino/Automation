"""
PPVMCAReportAPI.py — Portfolio REST API wrapper around ppv_report.

This module is Portfolio-specific.  The core logic lives in MCAparser.py,
which is kept identical between PPV (desktop) and Portfolio (web).  This
wrapper maps the REST form-parameters to ppv_report constructor args and
exposes run() / get_output_files() helpers consumed by api/routers/mca.py.
"""
from __future__ import annotations
import os

from .MCAparser import ppv_report


class PPVMCAReport:
	"""
	Web-API-friendly wrapper around ppv_report.

	Maps the REST parameters to ppv_report constructor args and provides
	run() / get_output_files() helpers used by api/routers/mca.py.

	Constructor kwargs
	------------------
	data_file     : path to the uploaded Bucketer / S2T Logger Excel file
	product       : 'GNR' | 'CWF' | 'DMR'
	work_week     : e.g. 'WW9'
	label         : optional run label
	mode          : 'Bucketer' (default) | 'Framework' | 'Data'
	output_dir    : directory to write output files into (tmpdir)
	mca_analysis  : whether to run the MCAAnalyzer post-processing step
	                (default True — generates a colour-coded Analysis sheet)

	run(options)
	------------
	options is a list of strings from the frontend checkboxes:
	  'REDUCED'   → reduced=True  (sets reduced data mode)
	  'DECODE'    → decode=True   (run MCA decode tab)
	  'OVERVIEW'  → overview=True (generate unit overview file)
	  'ANALYSIS'  → mca_analysis=True (MCAAnalyzer post-processing)

	get_output_files()
	------------------
	Returns list of (path, filename) tuples for files that were produced.
	"""

	def __init__(self, data_file, product='GNR', work_week='WW1', label='',
	             mode='Bucketer', output_dir=None, mca_analysis=True):
		self.data_file    = data_file
		self.product      = product.upper()
		self.work_week    = work_week
		self.label        = label
		self.mode         = mode
		self.output_dir   = output_dir or os.path.dirname(data_file)
		self.mca_analysis = mca_analysis
		self._report      = None  # ppv_report instance created in run()

	def run(self, options=None):
		if options is None:
			options = ['REDUCED', 'DECODE', 'OVERVIEW', 'ANALYSIS']
		opts = [o.upper() for o in options]

		reduced  = 'REDUCED'  in opts
		decode   = 'DECODE'   in opts
		overview = 'OVERVIEW' in opts
		analysis = 'ANALYSIS' in opts and self.mca_analysis

		run_opts = ['MESH', 'CORE']

		self._report = ppv_report(
			name         = self.product,
			week         = self.work_week,
			label        = self.label,
			source_file  = self.data_file,
			report       = self.output_dir,
			reduced      = reduced,
			mcdetail     = False,
			overview     = overview,
			decode       = decode,
			mode         = self.mode,
			product      = self.product,
			mca_analysis = analysis,
		)
		self._report.run(options=run_opts)

	def get_output_files(self):
		"""Return list of (path, filename) tuples for files that were produced."""
		if self._report is None:
			return []
		results = []
		for attr in ('data_file', 'mca_file', 'ovw_file'):
			path = getattr(self._report, attr, None)
			if path and os.path.isfile(path):
				results.append((path, os.path.basename(path)))
		return results


def rebuild_mca_tabs(data_file: str, product: str = 'GNR',
                     decode: bool = True, analysis: bool = True) -> None:
	"""
	Add MCA decoded tabs (CHA_MCAS, LLC_MCAS, CORE_MCAS, MEM_MCAS, IO_MCAS,
	UBOX) and an optional MCA Analysis sheet to an existing PPV data file that
	already has CHA and CORE tabs populated.

	This is the shared 'Redo MCA Analysis' path used by Framework Report (web)
	and can also be called from PPV desktop workflows when the data file already
	exists.  It skips the parse_data() step entirely — CHA/CORE rows are assumed
	to already be in the file.

	Parameters
	----------
	data_file : str
	    Absolute path to the Excel file (e.g. a MergedSummary.xlsx).
	    The file is modified in-place.
	product : str
	    Product name string (GNR, CWF, DMR).
	decode : bool
	    If True, run the MCA decoder to produce CHA_MCAS / LLC_MCAS /
	    CORE_MCAS / MEM_MCAS / IO_MCAS / UBOX sheets.
	analysis : bool
	    If True, run MCAAnalyzer to append the MCA_Analysis sheet.
	"""
	from .MCAparser import ppv_report

	output_dir = os.path.dirname(os.path.abspath(data_file)) or '.'

	# Construct a minimal ppv_report instance.
	# mode='Data' means __init__ skips the template filecopy so the
	# non-existent renamed data_file path never causes a FileNotFoundError.
	proc = ppv_report(
		name=product.upper(),
		week='WW0',
		label='rebuild',
		source_file=data_file,
		report=output_dir,
		mode='Data',
		product=product.upper(),
	)
	# Override the auto-renamed data_file to point at the actual file
	proc.data_file = data_file

	if decode:
		print(f' -- [Rebuild] Decoding CHA/LLC/MEM/IO MCAs from CHA tab...')
		proc.parse_mcas(data_file, 'CHA')
		print(f' -- [Rebuild] Decoding CORE MCAs from CORE tab...')
		proc.parse_CORE_mcas(data_file, 'CORE')

	if analysis:
		print(f' -- [Rebuild] Running MCA Analysis...')
		proc.gen_mca_analysis(data_file)
