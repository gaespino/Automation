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
