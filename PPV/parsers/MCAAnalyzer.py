"""
MCAAnalyzer - Replicates MCA Analysis Excel functionality in Python

Replicates the Analysis, REV_Units, RevCHACount, RevCoreCount, RevLLCCount
and OtherErrors Excel sheet logic using the decoded MCA data and product
IP map / layout configuration files.

Supports: GNR, CWF (same layout as GNR), DMR (placeholder)
"""

import json
import os
import re
import pandas as pd
from collections import Counter
from pathlib import Path


# Products using the same CHA/Core layout structure
_GNR_LAYOUT_PRODUCTS = {'GNR', 'CWF'}
# DMR placeholder flag
_DMR_PRODUCTS = {'DMR'}

# IP translation types that map to CORE/CHA/LLC – excluded from "Other Errors"
_CORE_TRANSLATE = {'CORE'}
_CHA_TRANSLATE = {'CHA', 'SCF'}
_LLC_TRANSLATE = {'LLC', 'SCF_LLC'}


def _load_json(path):
	"""Load a JSON file, return empty dict on failure."""
	try:
		with open(path, 'r') as f:
			return json.load(f)
	except Exception:
		return {}


def _compute_location(cha_or_core_id, layout):
	"""
	Translate a CHA/Core numeric ID to a human-readable location string.
	Returns "Compute{X} : Row{R} : Col{C}" or "" if not found.
	"""
	key = str(cha_or_core_id)
	entry = layout.get(key)
	if not entry:
		return ''
	compute_name = entry.get('compute', '')
	row = entry.get('row', '')
	col = entry.get('col', '')
	# compute name like "COMPUTE0" → display number "0"
	compute_num = re.sub(r'[^0-9]', '', compute_name)
	return f"Compute{compute_num} : Row{row} : Col{col}"


def _translate_location(location_str, ip_map):
	"""
	Translate a raw portid location string (e.g. 'core_coregp.0.cpucore.151')
	to (ip_translate, device_translate, instance) using the ip_map.

	Returns:
		(ip_translate, device_translate, instance_num) or ('', '', '') on failure
	"""
	if not location_str or not isinstance(location_str, str):
		return ('', '', '')

	parts = location_str.split('.')
	if len(parts) < 4:
		return ('', '', '')

	ip_key = parts[0]
	device_key = parts[2]
	instance = parts[3]

	# Exact match first
	entry = ip_map.get(ip_key)
	if entry is None:
		# Try prefix match (e.g. "punit_ptpcfsms" matches "punit_*")
		for k, v in ip_map.items():
			if k == 'FirstError IP' or k == 'null':
				continue
			if ip_key.startswith(k) or k.startswith(ip_key.split(':')[0]):
				entry = v
				break

	if entry is None:
		# Fall back to device_key as IP name and uppercase device as device
		return (ip_key.upper(), device_key.upper(), instance)

	ip_translate = entry[1] if len(entry) > 1 and entry[1] else ip_key.upper()
	# Device translate: use device_key from the location string (uppercase)
	# This matches the Excel format: "PUNIT:EPRPUNIT0" uses the device from the location
	dev_translate = device_key.upper()

	return (ip_translate, dev_translate, instance)


def _failed_instance_str(ip_translate, dev_translate, instance):
	"""Format the Failed Instance string as 'IP:DEV{instance}'."""
	if not ip_translate:
		return ''
	return f"{ip_translate}:{dev_translate}{instance}"


class MCAAnalyzer:
	"""
	Replicates the MCA Analysis Excel workbook logic in Python.

	Usage:
		analyzer = MCAAnalyzer(product='GNR')
		summary_df = analyzer.analyze(
			cha_df=cha_decoded_df,
			llc_df=llc_decoded_df,
			core_df=core_decoded_df,
			firsterr_df=firsterr_decoded_df,
			ppv_df=ppv_data_df     # optional, for Step/WW lookups
		)
	"""

	def __init__(self, product='GNR', layout_file=None, ip_map_file=None):
		self.product = product.upper()

		base_dir = Path(__file__).parent.parent / 'analysis'

		# Layout: maps CHA/Core numeric ID → {compute, row, col}
		if layout_file:
			self.layout = _load_json(layout_file)
		elif self.product in _GNR_LAYOUT_PRODUCTS:
			self.layout = _load_json(base_dir / 'GNR_layout.json')
		elif self.product in _DMR_PRODUCTS:
			# DMR placeholder – layout TBD
			self.layout = {}
		else:
			self.layout = _load_json(base_dir / 'GNR_layout.json')

		# IP map: maps raw portid IP type → [key, translate, ..., device_key, device_translate, offset, ...]
		if ip_map_file:
			self.ip_map = _load_json(ip_map_file)
		elif self.product in _GNR_LAYOUT_PRODUCTS:
			self.ip_map = _load_json(base_dir / 'GNR_ip_map.json')
		elif self.product in _DMR_PRODUCTS:
			# DMR placeholder – ip_map TBD
			self.ip_map = {}
		else:
			self.ip_map = _load_json(base_dir / 'GNR_ip_map.json')

	# ------------------------------------------------------------------
	# Public API
	# ------------------------------------------------------------------

	def analyze(self, cha_df=None, llc_df=None, core_df=None,
				firsterr_df=None, ppv_df=None):
		"""
		Run the full MCA analysis pipeline.

		Args:
			cha_df:      DataFrame from decoder.cha() – CHA MCA decoded data
			llc_df:      DataFrame from decoder.llc() – LLC MCA decoded data
			core_df:     DataFrame from decoder.core() – Core MCA decoded data
			firsterr_df: DataFrame from decoder.portids() – First Error data
			ppv_df:      DataFrame from PPV data (for Step/WW lookups)

		Returns:
			dict with keys:
				'analysis'  – Analysis/Summary DataFrame
				'rev_units' – REV_Units per-unit aggregated DataFrame
		"""
		cha_df = cha_df if cha_df is not None else pd.DataFrame()
		llc_df = llc_df if llc_df is not None else pd.DataFrame()
		core_df = core_df if core_df is not None else pd.DataFrame()
		firsterr_df = firsterr_df if firsterr_df is not None else pd.DataFrame()

		# Per-unit aggregations
		rev_cha = self._build_rev_cha_count(cha_df)
		rev_llc = self._build_rev_llc_count(llc_df)
		rev_core = self._build_rev_core_count(core_df)
		other_errors = self._build_other_errors(firsterr_df)

		# Combined REV_Units-equivalent DataFrame
		rev_units = self._build_rev_units(
			cha_df, llc_df, core_df,
			rev_cha, rev_llc, rev_core, other_errors
		)

		# Final Analysis/Summary DataFrame
		analysis = self._build_analysis(rev_units, ppv_df)

		return {'analysis': analysis, 'rev_units': rev_units}

	# ------------------------------------------------------------------
	# Internal helpers
	# ------------------------------------------------------------------

	def _get_visual_ids(self, *dfs):
		"""Collect unique VisualIDs across all provided DataFrames."""
		ids = set()
		for df in dfs:
			if df is not None and not df.empty:
				col = 'VisualID' if 'VisualID' in df.columns else 'VisualId'
				if col in df.columns:
					ids.update(df[col].dropna().unique())
		return sorted(ids)

	def _argmax_unique(self, counter):
		"""
		Return (winner, is_unique) from a Counter.
		is_unique=True means exactly one item has the maximum count.
		Returns ('NotFound', False) if counter is empty.
		"""
		if not counter:
			return ('NotFound', False)
		max_count = max(counter.values())
		winners = [k for k, v in counter.items() if v == max_count]
		if len(winners) == 1:
			return (winners[0], True)
		return ('NotFound', False)

	# ------------------------------------------------------------------
	# RevCHACount equivalent
	# ------------------------------------------------------------------

	def _build_rev_cha_count(self, cha_df):
		"""
		Build a per-VisualID summary of CHA MCA counts.

		Returns DataFrame with columns:
			VisualID, CHA Hint, CHA Fail Area, SrcID Hint
		"""
		rows = []
		if cha_df.empty:
			return pd.DataFrame(columns=['VisualID', 'CHA Hint', 'CHA Fail Area', 'SrcID Hint'])

		vid_col = 'VisualID' if 'VisualID' in cha_df.columns else 'VisualId'
		cha_col = 'CHA' if 'CHA' in cha_df.columns else None
		srcid_col = 'SrcID' if 'SrcID' in cha_df.columns else None

		for vid in cha_df[vid_col].dropna().unique():
			subset = cha_df[cha_df[vid_col] == vid]

			# CHA counts
			cha_hint = 'NotFound'
			cha_area = ''
			if cha_col and not subset[cha_col].dropna().empty:
				cha_counts = Counter(subset[cha_col].dropna())
				winner, unique = self._argmax_unique(cha_counts)
				if unique and winner != 'NotFound':
					cha_hint = winner  # already formatted as "CHA{N}"
					cha_num = re.sub(r'[^0-9]', '', str(winner))
					cha_area = _compute_location(cha_num, self.layout)

			# SrcID hint
			srcid_hint = 'NotFound'
			if srcid_col and not subset[srcid_col].dropna().empty:
				srcid_counts = Counter(subset[srcid_col].dropna())
				src_winner, src_unique = self._argmax_unique(srcid_counts)
				if src_unique and src_winner != 'NotFound':
					srcid_hint = src_winner

			rows.append({
				'VisualID': vid,
				'CHA Hint': cha_hint,
				'CHA Fail Area': cha_area,
				'SrcID Hint': srcid_hint,
			})

		return pd.DataFrame(rows)

	# ------------------------------------------------------------------
	# RevLLCCount equivalent
	# ------------------------------------------------------------------

	def _build_rev_llc_count(self, llc_df):
		"""
		Build a per-VisualID summary of LLC MCA counts.

		Returns DataFrame with columns:
			VisualID, LLC Hint, LLC Fail Area
		"""
		rows = []
		if llc_df.empty:
			return pd.DataFrame(columns=['VisualID', 'LLC Hint', 'LLC Fail Area'])

		vid_col = 'VisualID' if 'VisualID' in llc_df.columns else 'VisualId'
		llc_col = 'LLC' if 'LLC' in llc_df.columns else None

		for vid in llc_df[vid_col].dropna().unique():
			subset = llc_df[llc_df[vid_col] == vid]

			llc_hint = 'NotFound'
			llc_area = ''
			if llc_col and not subset[llc_col].dropna().empty:
				llc_counts = Counter(subset[llc_col].dropna())
				winner, unique = self._argmax_unique(llc_counts)
				if unique and winner != 'NotFound':
					llc_hint = winner  # formatted as "LLC{N}"
					llc_num = re.sub(r'[^0-9]', '', str(winner))
					llc_area = _compute_location(llc_num, self.layout)

			rows.append({
				'VisualID': vid,
				'LLC Hint': llc_hint,
				'LLC Fail Area': llc_area,
			})

		return pd.DataFrame(rows)

	# ------------------------------------------------------------------
	# RevCoreCount equivalent
	# ------------------------------------------------------------------

	def _build_rev_core_count(self, core_df):
		"""
		Build a per-VisualID summary of Core MCA counts.

		Returns DataFrame with columns:
			VisualID, Core Hint, Core Fail Area, Core MCAs
		"""
		rows = []
		if core_df.empty:
			return pd.DataFrame(columns=['VisualID', 'Core Hint', 'Core Fail Area', 'Core MCAs'])

		vid_col = 'VisualID' if 'VisualID' in core_df.columns else 'VisualId'
		core_col = 'CORE' if 'CORE' in core_df.columns else None
		err_col = 'ErrorType' if 'ErrorType' in core_df.columns else (
			'MCACOD (ErrDecode)' if 'MCACOD (ErrDecode)' in core_df.columns else None
		)

		for vid in core_df[vid_col].dropna().unique():
			subset = core_df[core_df[vid_col] == vid]

			core_hint = 'NotFound'
			core_area = ''
			core_mcas = ''

			if core_col and not subset[core_col].dropna().empty:
				core_counts = Counter(subset[core_col].dropna())
				winner, unique = self._argmax_unique(core_counts)
				if unique and winner != 'NotFound':
					core_hint = winner  # formatted as "CORE{N}"
					core_num = re.sub(r'[^0-9]', '', str(winner))
					core_area = _compute_location(core_num, self.layout)

					# Core MCAs = unique error types for the winning core
					if err_col:
						core_subset = subset[subset[core_col] == winner]
						unique_errs = core_subset[err_col].dropna().unique().tolist()
						core_mcas = ', '.join(str(e) for e in unique_errs if e)

			rows.append({
				'VisualID': vid,
				'Core Hint': core_hint,
				'Core Fail Area': core_area,
				'Core MCAs': core_mcas,
			})

		return pd.DataFrame(rows)

	# ------------------------------------------------------------------
	# Other Errors
	# ------------------------------------------------------------------

	def _build_other_errors(self, firsterr_df):
		"""
		Build per-VisualID "Other Errors" string from FirstErr data.
		Non-CORE/CHA/LLC first errors are joined as 'IP:Device{instance}'.

		Returns dict: {visual_id: "Other Errors string"}
		"""
		other = {}
		if firsterr_df.empty:
			return other

		vid_col = 'VisualID' if 'VisualID' in firsterr_df.columns else 'VisualId'
		loc_col = 'FirstError - Location'

		if loc_col not in firsterr_df.columns:
			return other

		for vid in firsterr_df[vid_col].dropna().unique():
			subset = firsterr_df[firsterr_df[vid_col] == vid]
			instances = []
			for _, row in subset.iterrows():
				loc = row.get(loc_col, '')
				if not loc or not isinstance(loc, str):
					continue
				ip_tr, dev_tr, instance = _translate_location(loc, self.ip_map)
				# Skip CORE/CHA/LLC – they are handled by their own Rev* sheets
				if ip_tr.upper() in _CORE_TRANSLATE | _CHA_TRANSLATE | _LLC_TRANSLATE:
					continue
				if not ip_tr:
					continue
				inst_str = _failed_instance_str(ip_tr, dev_tr, instance)
				if inst_str and inst_str not in instances:
					instances.append(inst_str)
			other[vid] = ', '.join(instances)

		return other

	# ------------------------------------------------------------------
	# REV_Units equivalent
	# ------------------------------------------------------------------

	def _build_rev_units(self, cha_df, llc_df, core_df,
						 rev_cha, rev_llc, rev_core, other_errors):
		"""
		Build the REV_Units per-unit summary DataFrame.

		Columns match Analysis sheet lookup sources:
		  VisualID, # Runs, Core Hint, Core Fail Area, CHA Hint, CHA Fail Area,
		  LLC Hint, LLC Fail Area, SrcIDs, Other, Top OrigReq, Top OpCode,
		  Top ISMQ, Top SAD, Top SAD LocPort, SAD Targets, Core MCAs
		"""
		all_vids = self._get_visual_ids(cha_df, llc_df, core_df)

		def _lookup(df_ref, vid, field, default='NotFound'):
			if df_ref.empty or 'VisualID' not in df_ref.columns:
				return default
			row = df_ref[df_ref['VisualID'] == vid]
			if row.empty:
				return default
			val = row.iloc[0].get(field, default)
			return val if pd.notna(val) and val != '' else default

		# Helper: count unique runs for a VisualID
		def _count_runs(df, vid):
			if df.empty:
				return 0
			vid_col = 'VisualID' if 'VisualID' in df.columns else 'VisualId'
			run_col = 'Run' if 'Run' in df.columns else None
			if not run_col or vid_col not in df.columns:
				return 0
			subset = df[df[vid_col] == vid]
			return subset[run_col].dropna().nunique()

		# Helper: get top value from a CHA column counter
		def _top_field(df, vid, field):
			if df.empty or field not in df.columns:
				return ''
			vid_col = 'VisualID' if 'VisualID' in df.columns else 'VisualId'
			subset = df[df[vid_col] == vid]
			vals = subset[field].dropna()
			if vals.empty:
				return ''
			counts = Counter(vals)
			winner, _ = self._argmax_unique(counts)
			return winner if winner != 'NotFound' else ''

		rows = []
		for vid in all_vids:
			# Run count (max across CHA/LLC/CORE)
			runs = max(
				_count_runs(cha_df, vid),
				_count_runs(llc_df, vid),
				_count_runs(core_df, vid)
			)

			# Core data
			core_hint = _lookup(rev_core, vid, 'Core Hint')
			core_area = _lookup(rev_core, vid, 'Core Fail Area', default='')
			core_mcas = _lookup(rev_core, vid, 'Core MCAs', default='')

			# CHA data
			cha_hint = _lookup(rev_cha, vid, 'CHA Hint')
			cha_area = _lookup(rev_cha, vid, 'CHA Fail Area', default='')
			srcids = _lookup(rev_cha, vid, 'SrcID Hint')

			# LLC data
			llc_hint = _lookup(rev_llc, vid, 'LLC Hint')
			llc_area = _lookup(rev_llc, vid, 'LLC Fail Area', default='')

			# Other errors
			other = other_errors.get(vid, '')

			# Top CHA signature fields (most frequent from CHA decoder)
			top_origreq = _top_field(cha_df, vid, 'Orig Req')
			top_opcode = _top_field(cha_df, vid, 'Opcode')
			top_ismq = _top_field(cha_df, vid, 'ISMQ')
			top_sad = _top_field(cha_df, vid, 'Result')
			top_locport = _top_field(cha_df, vid, 'Local Port')

			# All unique non-empty SAD targets (Local Port values)
			sad_targets = ''
			if not cha_df.empty and 'Local Port' in cha_df.columns:
				vid_col = 'VisualID' if 'VisualID' in cha_df.columns else 'VisualId'
				subset = cha_df[cha_df[vid_col] == vid]
				unique_ports = [
					str(p) for p in subset['Local Port'].dropna().unique()
					if str(p) not in ('', 'nan')
				]
				sad_targets = ', '.join(unique_ports)

			rows.append({
				'VisualID': vid,
				'# Runs': runs,
				'Core Hint': core_hint,
				'Core Fail Area': core_area,
				'CHA Hint': cha_hint,
				'CHA Fail Area': cha_area,
				'LLC Hint': llc_hint,
				'LLC Fail Area': llc_area,
				'SrcIDs': srcids,
				'Other': other,
				'Top OrigReq': top_origreq,
				'Top OpCode': top_opcode,
				'Top ISMQ': top_ismq,
				'Top SAD': top_sad,
				'Top SAD LocPort': top_locport,
				'SAD Targets': sad_targets,
				'Core MCAs': core_mcas,
			})

		return pd.DataFrame(rows)

	# ------------------------------------------------------------------
	# Analysis / Summary DataFrame
	# ------------------------------------------------------------------

	def _build_analysis(self, rev_units, ppv_df=None):
		"""
		Build the final Analysis/Summary DataFrame that replicates the
		Excel 'Analysis' (summ) table.

		Columns:
		  VisualIDs, Step, WW, # Runs, Core Hint, Core Fail Area,
		  CHA Hint, CHA Fail Area, LLC Hint, LLC Fail Area, SrcIDs,
		  Other, Top OrigReq, Top OpCode, Top ISMQ, Top SAD,
		  Top SAD LocPort, Core Mcas, Root Cause,
		  Core Next Steps, CHA Next Steps, LLC Next Steps,
		  Defeature, Fail Area
		"""
		if rev_units.empty:
			return pd.DataFrame()

		# PPV lookups for Step / WW
		ppv_step = {}
		ppv_ww = {}
		if ppv_df is not None and not ppv_df.empty:
			vid_col = next(
				(c for c in ('Data.Visual_ID', 'VisualId', 'VisualID') if c in ppv_df.columns),
				None
			)
			if vid_col:
				for _, r in ppv_df.iterrows():
					vid = r[vid_col]
					if 'Data.Step' in ppv_df.columns:
						ppv_step[vid] = r.get('Data.Step', '')
					if 'Data.Start_WW' in ppv_df.columns:
						ppv_ww[vid] = r.get('Data.Start_WW', '')

		rows = []
		for _, ru in rev_units.iterrows():
			vid = ru['VisualID']

			step = ppv_step.get(vid, '')
			ww = ppv_ww.get(vid, '')
			num_runs = ru.get('# Runs', 0)
			core_hint = ru.get('Core Hint', 'NotFound')
			core_area = ru.get('Core Fail Area', '')
			cha_hint = ru.get('CHA Hint', 'NotFound')
			cha_area = ru.get('CHA Fail Area', '')
			llc_hint = ru.get('LLC Hint', 'NotFound')
			llc_area = ru.get('LLC Fail Area', '')
			srcids = ru.get('SrcIDs', 'NotFound')
			other = ru.get('Other', '')
			top_origreq = ru.get('Top OrigReq', '')
			top_opcode = ru.get('Top OpCode', '')
			top_ismq = ru.get('Top ISMQ', '')
			top_sad = ru.get('Top SAD', '')
			top_locport = ru.get('Top SAD LocPort', '')
			core_mcas = ru.get('Core MCAs', '')

			# Computed: Root Cause
			if core_hint != 'NotFound':
				root_cause = 'CORE'
			elif cha_hint != 'NotFound':
				root_cause = 'CHA'
			elif llc_hint != 'NotFound':
				root_cause = 'LLC'
			elif other:
				root_cause = 'OTHER'
			else:
				root_cause = ''

			# Computed: Core Next Steps
			if core_hint != 'NotFound':
				core_next = f"Disable CORE: {core_hint} - MCAs: {core_mcas}"
			else:
				core_next = ''

			# Computed: CHA Next Steps
			if cha_hint != 'NotFound':
				sig = ' - '.join(filter(None, [top_origreq, top_ismq]))
				cha_next = f"Disable CHA: {cha_hint} - Signature: {sig} : {top_locport}".rstrip(' :')
			elif srcids != 'NotFound':
				sig = ' - '.join(filter(None, [top_origreq, top_ismq]))
				cha_next = f"Disable SrcID: {srcids} - Signature: {sig} : {top_locport}".rstrip(' :')
			else:
				cha_next = ''

			# Computed: LLC Next Steps
			llc_next = f"Disable LLC: {llc_hint}" if llc_hint != 'NotFound' else ''

			# Computed: Defeature
			defeature = f"Defeature: {other}  -- Check CORE or CHA MCAs for more data." if other else ''

			# Computed: Fail Area summary
			fail_parts = []
			if core_area:
				fail_parts.append(f"CORE: {core_area}")
			if cha_area:
				fail_parts.append(f"CHA: {cha_area}")
			if llc_area:
				fail_parts.append(f"LLC: {llc_area}")
			fail_area = ' - '.join(fail_parts)

			rows.append({
				'VisualIDs': vid,
				'Step': step,
				'WW': ww,
				'# Runs': num_runs,
				'Core Hint': core_hint,
				'Core Fail Area': core_area,
				'CHA Hint': cha_hint,
				'CHA Fail Area': cha_area,
				'LLC Hint': llc_hint,
				'LLC Fail Area': llc_area,
				'SrcIDs': srcids,
				'Other': other,
				'Top OrigReq': top_origreq,
				'Top OpCode': top_opcode,
				'Top ISMQ': top_ismq,
				'Top SAD': top_sad,
				'Top SAD LocPort': top_locport,
				'Core Mcas': core_mcas,
				'Root Cause': root_cause,
				'Core Next Steps': core_next,
				'CHA Next Steps': cha_next,
				'LLC Next Steps': llc_next,
				'Defeature': defeature,
				'Fail Area': fail_area,
			})

		return pd.DataFrame(rows)
