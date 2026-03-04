"""
MCAAnalyzer - Replicates MCA Analysis Excel functionality in Python

Replicates the Analysis, REV_Units, RevCHACount, RevCoreCount, RevLLCCount
and OtherErrors Excel sheet logic using the decoded MCA data and product
IP translation / layout configuration files.

Algorithm for identifying the failing instance (CORE / CHA / LLC / Other):
  1. Count ML2/MCA register occurrences per instance (same as Excel Rev*Count arrays).
  2. If a single instance dominates → that is the hint.
  3. If there is a TIE in the count → fall back to the UBOX FirstError count array:
       the UBOX MCERRLOGGINGREG / IERRLOGGINGREG records which portid fired first
       in each run.  The most-frequent FirstError portid (after physical→logical
       instance conversion via the device offset) breaks the tie.
  4. Non-CORE/CHA/LLC first errors (PUNIT, UPI, …) become "Other Errors".

Physical → Logical conversion (device offset):
  Some IP types have a per-compute-tile offset in their portid numbering.
  For GNR cpucore (offset=4):
    logical = physical - (physical // block_size) * offset
  where block_size = (items_per_compute) + offset  (e.g. 60+4=64 for GNR cores).

Supports: GNR, CWF (same layout as GNR), DMR (placeholder)

Per-product configuration is stored in PPV/analysis/{product}/:
  ip_translation.json – consolidated IP translation config with three sections:
    "firsterror_ip"     : {ip_key → translate}
    "firsterror_device" : {device_key → {"translate": str, "offset": int}}
    "failing_ips"       : {ip_translate → register_type}
  layout.json         – Compute/Row/Col position for each logical instance id
  scoring_config.json – score_compute / score_row / score_col weights used
                        when ranking candidate failing locations

Translation fallback:
  When an ip_key or device_key is not found in ip_translation.json:
  - The raw key value is used as-is (uppercase)
  - A WARNING is printed once per unknown key so the entry can be added to the JSON
"""

import json
import re
import pandas as pd
from collections import Counter
from pathlib import Path


# Products using the same CHA/Core layout structure
_GNR_LAYOUT_PRODUCTS = {'GNR', 'CWF'}
# DMR placeholder flag
_DMR_PRODUCTS = {'DMR'}

# ip_translation "firsterror_ip" values that map to CORE / CHA / LLC
_CORE_TRANSLATE = {'CORE'}
_CHA_TRANSLATE  = {'CHA', 'SCF'}
_LLC_TRANSLATE  = {'LLC', 'SCF_LLC'}

# NCEVENT substrings used to select IERR vs MCERR rows in the UBOX DataFrame
_IERR_LABEL  = 'IERRLOGGINGREG'
_MCERR_LABEL = 'MCERRLOGGINGREG'


def _load_json(path):
	"""Load a JSON file; return empty dict on failure."""
	try:
		with open(path, 'r') as f:
			return json.load(f)
	except Exception:
		return {}


def _load_ip_translation(path):
	"""
	Load ip_translation.json.  Returns a dict with keys:
	  'firsterror_ip'     : {ip_key: translate_str}
	  'firsterror_device' : {device_key: {'translate': str, 'offset': int}}
	  'failing_ips'       : {ip_translate: register_type_str}
	Returns empty sub-dicts on failure.
	"""
	data = _load_json(path)
	return {
		'firsterror_ip'    : data.get('firsterror_ip',     {}),
		'firsterror_device': data.get('firsterror_device', {}),
		'failing_ips'      : data.get('failing_ips',       {}),
	}


def _compute_location(instance_id, layout, mode='core'):
	"""
	Map a logical CORE/CHA/LLC numeric id to a human-readable location.

	For GNR/CWF entries (no 'cbb' key):
	  mode='core' → "Compute{X} : Row{R} : Col{C}"
	  mode='cha'  → "Compute{X} : Row{R} : Col{C}"  (same as core)

	For DMR entries (with 'cbb' key):
	  mode='core' → "CBB{cbb} : Compute{compute} : Row{row} : Col{col}"
	  mode='cha'  → "CBB{cbb} : ENV{env} : Instance{cbo} : Row{row} : Col{col}"

	Returns "" when not found.
	"""
	entry = layout.get(str(instance_id))
	if not entry:
		return ''
	if 'cbb' in entry:
		# DMR layout entry
		cbb     = entry.get('cbb', '')
		compute = entry.get('compute', '')
		row     = entry.get('row', '')
		col     = entry.get('col', '')
		env     = entry.get('env', '')
		cbo     = entry.get('cbo', '')
		if mode == 'cha':
			return f"CBB{cbb} : ENV{env} : Instance{cbo} : Row{row} : Col{col}"
		return f"CBB{cbb} : Compute{compute} : Row{row} : Col{col}"
	# GNR/CWF layout entry
	compute_name = entry.get('compute', '')
	row = entry.get('row', '')
	col = entry.get('col', '')
	compute_num = re.sub(r'[^0-9]', '', compute_name)
	return f"Compute{compute_num} : Row{row} : Col{col}"


class MCAAnalyzer:
	"""
	Replicates the MCA Analysis Excel workbook logic in Python.

	Usage
	-----
	analyzer = MCAAnalyzer(product='GNR')
	result   = analyzer.analyze(
	    cha_df=cha_decoded_df,
	    llc_df=llc_decoded_df,
	    core_df=core_decoded_df,
	    firsterr_df=firsterr_decoded_df,   # UBOX portids() output
	    ppv_df=ppv_data_df,                # optional, for Lot/WW lookups from PPV tab
	    debug=True,                        # optional verbose trace
	)
	result['analysis']  → per-unit Analysis DataFrame
	result['rev_units'] → intermediate REV_Units DataFrame
	"""

	def __init__(self, product='GNR', layout_file=None, config_file=None):
		self.product  = product.upper()
		base_dir      = Path(__file__).parent.parent / 'analysis'
		product_dir   = base_dir / self.product

		# Load per-product scoring config (score weights for Compute/Row/Col selection)
		_cfg_path = config_file or product_dir / 'scoring_config.json'
		_cfg = _load_json(_cfg_path)
		self.score_compute = _cfg.get('score_compute', 1)
		self.score_row     = _cfg.get('score_row',     2)
		self.score_col     = _cfg.get('score_col',     4)

		# Layout: prefer product subfolder layout.json, fall back to root GNR files
		if layout_file:
			self.layout = _load_json(layout_file)
		elif (product_dir / 'layout.json').exists():
			self.layout = _load_json(product_dir / 'layout.json')
		elif self.product in _GNR_LAYOUT_PRODUCTS:
			self.layout = _load_json(base_dir / 'GNR_layout.json')
		elif self.product in _DMR_PRODUCTS:
			self.layout = {}
		else:
			self.layout = _load_json(base_dir / 'GNR_layout.json')

		# Pre-compute block_size cache (for physical→logical conversion)
		self._block_size_cache = {}

		# Load consolidated IP translation config from ip_translation.json
		_trans = _load_ip_translation(product_dir / 'ip_translation.json')
		self.firsterror_ip_map     = _trans['firsterror_ip']
		self.firsterror_device_map = _trans['firsterror_device']
		self.failing_ips_map       = _trans['failing_ips']

		# Track keys that were not found in the translation config so the caller
		# can extend ip_translation.json with missing entries.
		self._translation_misses: set = set()

		# Load root-cause / debug-hints priority rules
		_rules_path = product_dir / 'priority_rules.json'
		_rules_data = _load_json(_rules_path)
		self._default_rc_order  = _rules_data.get('default_root_cause_order',  ['other', 'cha', 'llc', 'core'])
		self._default_dh_order  = _rules_data.get('default_debug_hints_order', ['other', 'cha', 'llc', 'core'])
		self._priority_rules    = _rules_data.get('rules', [])

	# =========================================================================
	# Public API
	# =========================================================================

	def analyze(self, cha_df=None, llc_df=None, core_df=None,
				firsterr_df=None, ppv_df=None,
				io_df=None, mem_df=None,
				debug=False):
		"""
		Run the full MCA analysis pipeline.

		Parameters
		----------
		cha_df      : DataFrame from decoder.cha()
		llc_df      : DataFrame from decoder.llc()
		core_df     : DataFrame from decoder.core()
		firsterr_df : DataFrame from decoder.portids()  (UBOX FirstError)
		ppv_df      : DataFrame with Lot/WW columns from the PPV tab (optional)
		io_df       : DataFrame from decoder.io()  (optional; IO_MCAS sheet)
		mem_df      : DataFrame from decoder.mem() (optional; MEM_MCAS sheet)
		debug       : When True, print per-VID trace to stdout

		Returns
		-------
		dict with keys 'analysis' and 'rev_units'
		"""
		cha_df      = cha_df      if cha_df      is not None else pd.DataFrame()
		llc_df      = llc_df      if llc_df      is not None else pd.DataFrame()
		core_df     = core_df     if core_df     is not None else pd.DataFrame()
		firsterr_df = firsterr_df if firsterr_df is not None else pd.DataFrame()
		io_df       = io_df       if io_df       is not None else pd.DataFrame()
		mem_df      = mem_df      if mem_df      is not None else pd.DataFrame()

		if debug:
			print(f"\n{'='*60}")
			print(f"MCAAnalyzer.analyze()  product={self.product}")
			print(f"  core_df rows   : {len(core_df)}")
			print(f"  cha_df rows    : {len(cha_df)}")
			print(f"  llc_df rows    : {len(llc_df)}")
			print(f"  firsterr rows  : {len(firsterr_df)}")
			print(f"  io_df rows     : {len(io_df)}")
			print(f"  mem_df rows    : {len(mem_df)}")
			print(f"{'='*60}")

		rev_cha  = self._build_rev_cha_count(cha_df,   firsterr_df, debug)
		rev_llc  = self._build_rev_llc_count(llc_df,   firsterr_df, debug)
		rev_core = self._build_rev_core_count(core_df, firsterr_df, debug)
		other_errors = self._build_other_errors(firsterr_df, debug)
		rev_io   = self._build_rev_io_count(io_df,   debug)
		rev_mem  = self._build_rev_mem_count(mem_df,  debug)

		rev_units = self._build_rev_units(
			cha_df, llc_df, core_df,
			rev_cha, rev_llc, rev_core, other_errors,
			rev_io=rev_io, rev_mem=rev_mem,
		)

		analysis = self._build_analysis(rev_units, ppv_df)

		if debug:
			self._print_debug_summary(analysis)

		return {'analysis': analysis, 'rev_units': rev_units}

	# =========================================================================
	# Physical → Logical instance conversion helpers
	# =========================================================================

	def _block_size_for_offset(self, offset):
		"""
		Return block_size = items_per_compute + offset, derived from the layout.
		When offset is 0 (or layout is absent) returns 1 (conversion is identity).
		"""
		if offset == 0 or not self.layout:
			return 1

		# Derive items-per-compute from the layout (works for CORE; same formula
		# applies to CHA/LLC when a layout is present).
		computes = Counter(v.get('compute', '') for v in self.layout.values() if v)
		n_computes = len([c for c in computes if c])
		if n_computes > 0:
			return len(self.layout) // n_computes + offset
		return 64  # GNR fallback

	def _physical_to_logical_by_offset(self, physical_str, offset):
		"""
		Convert a physical portid instance number to logical using an explicit
		offset value (from ip_translation.json firsterror_device section).
		"""
		try:
			physical = int(physical_str)
		except (ValueError, TypeError):
			return 0
		if offset == 0:
			return physical
		block_size  = self._block_size_for_offset(offset)
		compute_idx = physical // block_size
		return physical - compute_idx * offset

	def _parse_firsterr_location(self, loc_str):
		"""
		Parse a 'FirstError - Location' string into a structured dict using the
		ip_translation.json lookup tables.

		If an ip_key or device_key is not found the raw value is used as-is and
		a WARNING is emitted once per unknown key so the entry can be added to
		ip_translation.json.

		Examples
		--------
		'core_coregp.0.cpucore.148'          → ip_translate='CORE',  logical=140, display='CORE140'
		'scf_cha.0.cpuscf.38'                → ip_translate='CHA',   logical=34,  display='CHA34'
		'punit_ptpcioregs_0.0.eprpunit.1'    → ip_translate='PUNIT', logical=1,   display='PUNIT:EPRPUNIT1'

		Returns None on parse failure.
		"""
		if not loc_str or not isinstance(loc_str, str):
			return None
		parts = loc_str.split('.')
		if len(parts) < 4:
			return None

		ip_key     = parts[0]
		device_key = parts[2]
		instance_s = parts[-1]

		# --- IP translation (ip_translation.json → firsterror_ip) ---
		if ip_key in self.firsterror_ip_map:
			ip_translate = self.firsterror_ip_map[ip_key]
		else:
			ip_translate = ip_key.upper()
			miss_key = f"firsterror_ip:{ip_key}"
			if miss_key not in self._translation_misses:
				self._translation_misses.add(miss_key)
				print(f"WARNING [MCAAnalyzer] Unknown FirstError IP key '{ip_key}'"
				      " – using raw value. Add to ip_translation.json.")

		# --- Device translation (ip_translation.json → firsterror_device) ---
		device_info = self.firsterror_device_map.get(device_key)
		if device_info:
			device_translate = device_info['translate']
			offset           = device_info['offset']
		else:
			device_translate = device_key.upper()
			offset           = 0
			miss_key = f"firsterror_device:{device_key}"
			if miss_key not in self._translation_misses:
				self._translation_misses.add(miss_key)
				print(f"WARNING [MCAAnalyzer] Unknown FirstError Device key '{device_key}'"
				      " – using raw value, offset=0. Add to ip_translation.json.")

		# --- Physical → Logical (device-based offset) ---
		logical = self._physical_to_logical_by_offset(instance_s, offset)

		is_core = ip_translate.upper() in _CORE_TRANSLATE
		is_cha  = ip_translate.upper() in _CHA_TRANSLATE
		is_llc  = ip_translate.upper() in _LLC_TRANSLATE

		if is_core or is_cha or is_llc or offset > 0:
			display = f"{ip_translate}{logical}"
		else:
			display = f"{ip_translate}:{device_translate}{instance_s}"

		return {
			'ip_key'      : ip_key,
			'ip_translate': ip_translate,
			'logical'     : logical,
			'display'     : display,
			'is_core'     : is_core,
			'is_cha'      : is_cha,
			'is_llc'      : is_llc,
		}

	# =========================================================================
	# FirstError count helpers (UBOX portids DataFrame)
	# =========================================================================

	def _firsterr_counts(self, firsterr_df, vid, ncevent_type, ip_filter_fn):
		"""
		Build a Counter of logical instance names from the UBOX FirstError data
		for one VisualID, filtered to a specific NCEVENT type (IERR / MCERR)
		and ip_translate category.

		Parameters
		----------
		ncevent_type : 'IERRLOGGINGREG', 'MCERRLOGGINGREG', or None.
		              When None, all rows are scanned (both IERR and MCERR).
		ip_filter_fn : callable(parsed_dict) → bool – selects CORE/CHA/LLC rows

		Returns
		-------
		Counter  {display_name: count}  e.g. {'CORE140': 3}
		"""
		if firsterr_df.empty:
			return Counter()

		vid_col = 'VisualID' if 'VisualID' in firsterr_df.columns else 'VisualId'
		loc_col = 'FirstError - Location'
		nce_col = 'NCEVENT'

		if loc_col not in firsterr_df.columns:
			return Counter()

		sub = firsterr_df[firsterr_df[vid_col] == vid]
		if ncevent_type and nce_col in sub.columns:
			sub = sub[sub[nce_col].str.contains(ncevent_type, na=False)]

		counts = Counter()
		for loc in sub[loc_col].dropna():
			parsed = self._parse_firsterr_location(loc)
			if parsed and ip_filter_fn(parsed):
				counts[parsed['display']] += 1
		return counts

	# =========================================================================
	# Generic helpers
	# =========================================================================

	def _get_visual_ids(self, *dfs):
		ids = set()
		for df in dfs:
			if df is not None and not df.empty:
				col = 'VisualID' if 'VisualID' in df.columns else 'VisualId'
				if col in df.columns:
					ids.update(df[col].dropna().unique())
		return sorted(ids)

	def _argmax_unique(self, counter):
		"""
		Return (winner, is_unique).
		is_unique=True iff exactly one key has the maximum count.
		"""
		if not counter:
			return ('NotFound', False)
		max_count = max(counter.values())
		winners   = [k for k, v in counter.items() if v == max_count]
		if len(winners) == 1:
			return (winners[0], True)
		return ('NotFound', False)

	def _resolve_hint_with_firsterr(self, ml2_counts, firsterr_df, vid,
									ncevent_type, ip_filter_fn, debug,
									label=''):
		"""
		Determine the failing instance hint using ML2 count + FirstError fallback.

		Algorithm
		---------
		1. If ML2 counts have a unique winner → return it.
		2. If ML2 counts are tied (or empty) → use FirstError count from UBOX.
		3. If FirstError also tied → return 'NotFound'.

		Returns
		-------
		(hint_str, source_str)
		  hint_str   : 'CORE140', 'CHA9', 'NotFound', …
		  source_str : 'ML2'|'FirstError'|'NotFound' (for debug)
		"""
		winner, unique = self._argmax_unique(ml2_counts)

		if debug:
			print(f"  [{label}] ML2 counts  : {dict(ml2_counts)}")

		if unique and winner != 'NotFound':
			if debug:
				print(f"  [{label}] → winner from ML2: {winner}")
			return winner, 'ML2'

		# ---- tie-break via FirstError counts ----
		fe_counts = self._firsterr_counts(
			firsterr_df, vid, ncevent_type, ip_filter_fn)
		if debug:
			print(f"  [{label}] ML2 tied/empty → FirstError ({ncevent_type}) counts: {dict(fe_counts)}")

		fe_winner, fe_unique = self._argmax_unique(fe_counts)
		if fe_unique and fe_winner != 'NotFound':
			if debug:
				print(f"  [{label}] → winner from FirstError: {fe_winner}")
			return fe_winner, 'FirstError'

		if debug:
			print(f"  [{label}] → NotFound (tie in both ML2 and FirstError)")
		return 'NotFound', 'NotFound'

	# =========================================================================
	# Per-product per-VID hint helpers (called by _build_rev_*_count)
	# =========================================================================

	def _cha_hint_gnr_cwf(self, subset, cha_col, firsterr_df, vid, debug):
		"""
		GNR/CWF: resolve CHA Hint and CHA Fail Area for one VID.

		Returns (cha_hint, cha_area)
		"""
		cha_hint = 'NotFound'
		cha_area = ''
		cha_filter = lambda p: p['is_cha']
		if cha_col and not subset[cha_col].dropna().empty:
			ml2_counts = Counter(subset[cha_col].dropna())
			cha_hint, _ = self._resolve_hint_with_firsterr(
				ml2_counts, firsterr_df, vid,
				_MCERR_LABEL, cha_filter, debug, label='CHA')
			if cha_hint != 'NotFound':
				cha_num  = re.sub(r'[^0-9]', '', str(cha_hint))
				cha_area = _compute_location(cha_num, self.layout)
		return cha_hint, cha_area

	def _cha_hint_dmr(self, subset, env_col, inst_col, vid, debug):
		"""
		DMR: resolve CHA Hint and CHA Fail Area for one VID using synthetic
		ENV+CBO keys from the CCF DataFrame.

		Returns (cha_hint, cha_area)
		"""
		cha_hint = 'NotFound'
		cha_area = ''
		if not (env_col and inst_col):
			return cha_hint, cha_area

		def _make_key(row):
			env_val  = str(row[env_col]).strip()  if pd.notna(row[env_col])  else ''
			inst_val = str(row[inst_col]).strip() if pd.notna(row[inst_col]) else ''
			return f"ENV{env_val}_CBO{inst_val}"

		keys = subset.apply(_make_key, axis=1).dropna()
		keys = keys[keys != 'ENV_CBO']
		if keys.empty:
			return cha_hint, cha_area

		ml2_counts = Counter(keys)
		winner, unique = self._argmax_unique(ml2_counts)
		if debug:
			print(f"  [CHA-DMR] ML2 counts: {dict(ml2_counts)}")
		if unique and winner != 'NotFound':
			m = re.search(r'_CBO(.+)$', winner)
			cbo_val  = m.group(1) if m else winner
			cha_hint = f"CBO{cbo_val}"
			env_m = re.match(r'ENV(\d+)_', winner)
			if env_m:
				env_num = env_m.group(1)
				for mod_id, entry in self.layout.items():
					if (str(entry.get('env', '')) == str(env_num) and
							str(entry.get('cbo', '')) == str(cbo_val)):
						cha_area = _compute_location(mod_id, self.layout, mode='cha')
						break
			if debug:
				print(f"  [CHA-DMR] → hint={cha_hint!r}  area={cha_area!r}")
		return cha_hint, cha_area

	def _llc_hint_gnr_cwf(self, subset, llc_col, firsterr_df, vid, debug):
		"""
		GNR/CWF: resolve LLC Hint and LLC Fail Area for one VID.

		Returns (llc_hint, llc_area)
		"""
		llc_hint = 'NotFound'
		llc_area = ''
		llc_filter = lambda p: p['is_llc']
		if llc_col and not subset[llc_col].dropna().empty:
			ml2_counts = Counter(subset[llc_col].dropna())
			llc_hint, _ = self._resolve_hint_with_firsterr(
				ml2_counts, firsterr_df, vid,
				_MCERR_LABEL, llc_filter, debug, label='LLC')
			if llc_hint != 'NotFound':
				llc_num  = re.sub(r'[^0-9]', '', str(llc_hint))
				llc_area = _compute_location(llc_num, self.layout)
		return llc_hint, llc_area

	def _core_hint_gnr_cwf(self, subset, core_col, err_col,
						   firsterr_df, vid, core_filter, debug):
		"""
		GNR/CWF: resolve Core Hint, Core Fail Area, and Core MCAs for one VID.
		Applies the IERR root-cause gate and MCERR FirstError tie-break.

		Returns (core_hint, core_area, core_mcas)
		"""
		core_hint = 'NotFound'
		core_area = ''
		core_mcas = ''

		# Step 1 — IERR gate
		ierr_non_core = False
		if not firsterr_df.empty:
			ierr_counts = self._firsterr_counts(
				firsterr_df, vid, _IERR_LABEL, lambda p: True)
			if ierr_counts:
				ierr_winner, _ = self._argmax_unique(ierr_counts)
				if ierr_winner and ierr_winner != 'NotFound':
					parsed = None
					_vc  = 'VisualID' if 'VisualID' in firsterr_df.columns else 'VisualId'
					_nce = 'NCEVENT'
					_lc  = 'FirstError - Location'
					fe_sub = firsterr_df[firsterr_df[_vc] == vid]
					if _nce in fe_sub.columns:
						fe_sub = fe_sub[fe_sub[_nce].str.contains(_IERR_LABEL, na=False)]
					for loc in fe_sub[_lc].dropna():
						p = self._parse_firsterr_location(loc)
						if p and p['display'] == ierr_winner:
							parsed = p
							break
					if parsed and not parsed['is_core']:
						ierr_non_core = True
						if debug:
							print("  [CORE] IERR first error is non-CORE: "
								  f"{ierr_winner} → Core Hint = NotFound")
						mcerr_core_counts = self._firsterr_counts(
							firsterr_df, vid, _MCERR_LABEL, core_filter)
						if mcerr_core_counts:
							mcerr_winner, _ = self._argmax_unique(mcerr_core_counts)
							if mcerr_winner and mcerr_winner != 'NotFound':
								core_num = re.sub(r'[^0-9]', '', str(mcerr_winner))
								loc_full = _compute_location(core_num, self.layout)
								m = re.match(r'(Compute\d+)', loc_full)
								if m:
									core_area = m.group(1)
								else:
									core_area = loc_full
									if debug:
										print("  [CORE] WARNING: unexpected location "
											  f"format {loc_full!r}; using full string")
								if debug:
									print("  [CORE] Core Fail Area from MCERR: "
										  f"{mcerr_winner} → {core_area!r}")

		# Step 2 — ML2 + MCERR tie-break
		if not ierr_non_core and core_col and not subset[core_col].dropna().empty:
			ml2_counts = Counter(subset[core_col].dropna())
			core_hint, _ = self._resolve_hint_with_firsterr(
				ml2_counts, firsterr_df, vid,
				None, core_filter, debug, label='CORE')
			if core_hint != 'NotFound':
				core_num  = re.sub(r'[^0-9]', '', str(core_hint))
				core_area = _compute_location(core_num, self.layout, mode='core')
				if err_col:
					winning_rows = subset[subset[core_col] == core_hint]
					unique_errs  = winning_rows[err_col].dropna().unique().tolist()
					if not unique_errs:
						all_errs = subset[err_col].dropna()
						if not all_errs.empty:
							top_err, _ = self._argmax_unique(Counter(all_errs))
							if top_err and top_err != 'NotFound':
								unique_errs = [top_err]
					core_mcas = ', '.join(str(e) for e in unique_errs if e)
				if debug:
					print(f"  [CORE] area={core_area!r}  mcas={core_mcas!r}")

		# Fallback — populate core_mcas even when hint is NotFound
		if not core_mcas and err_col and core_col and not subset[core_col].dropna().empty:
			all_errs = subset[err_col].dropna()
			if not all_errs.empty:
				top_err, _ = self._argmax_unique(Counter(all_errs))
				if top_err and top_err != 'NotFound':
					core_mcas = top_err
			if debug and core_mcas:
				print(f"  [CORE] core_mcas from all rows (fallback): {core_mcas!r}")

		return core_hint, core_area, core_mcas

	def _core_hint_dmr(self, subset, core_col, err_col, vid, debug):
		"""
		DMR: resolve Core Hint, Core Fail Area, and Core MCAs for one VID.
		Uses ML2 counts alone (no IERR gate, no FirstError tie-break).

		Returns (core_hint, core_area, core_mcas)
		"""
		core_hint = 'NotFound'
		core_area = ''
		core_mcas = ''

		if core_col and not subset[core_col].dropna().empty:
			ml2_counts = Counter(subset[core_col].dropna())
			core_hint, _ = self._argmax_unique(ml2_counts)
			if debug:
				print(f"  [CORE-DMR] ML2 counts: {dict(ml2_counts)}")
			if core_hint != 'NotFound':
				core_num  = re.sub(r'[^0-9]', '', str(core_hint))
				core_area = _compute_location(core_num, self.layout, mode='core')
				if err_col:
					winning_rows = subset[subset[core_col] == core_hint]
					unique_errs  = winning_rows[err_col].dropna().unique().tolist()
					if not unique_errs:
						all_errs = subset[err_col].dropna()
						if not all_errs.empty:
							top_err, _ = self._argmax_unique(Counter(all_errs))
							if top_err and top_err != 'NotFound':
								unique_errs = [top_err]
					core_mcas = ', '.join(str(e) for e in unique_errs if e)
				if debug:
					print(f"  [CORE-DMR] area={core_area!r}  mcas={core_mcas!r}")

		if not core_mcas and err_col and core_col and not subset[core_col].dropna().empty:
			all_errs = subset[err_col].dropna()
			if not all_errs.empty:
				top_err, _ = self._argmax_unique(Counter(all_errs))
				if top_err and top_err != 'NotFound':
					core_mcas = top_err
			if debug and core_mcas:
				print(f"  [CORE-DMR] core_mcas from all rows (fallback): {core_mcas!r}")

		return core_hint, core_area, core_mcas

	def _io_hint_per_vid(self, subset, grp_col, inst_col, dec_col, vid, debug):
		"""
		Product-neutral: resolve IO Hint, IO Details, and IO MCAs for one VID.
		The caller resolves the group column (IO for GNR/CWF, IMH_CBB for DMR).

		Returns (io_hint, io_details, io_mcas)
		"""
		io_hint    = 'NotFound'
		io_details = ''
		io_mcas    = 0

		if not (inst_col and not subset[inst_col].dropna().empty):
			return io_hint, io_details, io_mcas

		def _io_key(row):
			grp  = str(row[grp_col]).strip()  if grp_col  and pd.notna(row[grp_col])  else ''
			inst = str(row[inst_col]).strip() if pd.notna(row[inst_col]) else ''
			dec  = str(row[dec_col]).strip()  if dec_col  and pd.notna(row[dec_col])  else ''
			return f"{grp}:{inst}:{dec}"

		keys = subset.apply(_io_key, axis=1).dropna()
		keys = keys[keys != '::']
		if not keys.empty:
			cnt = Counter(keys)
			winner, unique = self._argmax_unique(cnt)
			io_mcas = len(subset)
			if unique and winner != 'NotFound':
				parts    = winner.split(':')
				grp_val  = parts[0] if len(parts) > 0 else ''
				inst_val = parts[1] if len(parts) > 1 else ''
				dec_val  = parts[2] if len(parts) > 2 else ''
				io_hint    = f"{grp_val}:{inst_val}" if grp_val else inst_val
				io_details = f"{dec_val} ({cnt[winner]} occurrences)"
				if debug:
					print(f"\n[RevIO] VID={vid}: hint={io_hint!r}  "
						  f"details={io_details!r}")
		return io_hint, io_details, io_mcas

	def _mem_hint_per_vid(self, subset, inst_col, dec_col, vid, debug):
		"""
		Product-neutral: resolve MEM Hint, MEM Details, and MEM MCAs for one VID.

		Returns (mem_hint, mem_details, mem_mcas)
		"""
		mem_hint    = 'NotFound'
		mem_details = ''
		mem_mcas    = 0

		if not (inst_col and not subset[inst_col].dropna().empty):
			return mem_hint, mem_details, mem_mcas

		def _mem_key(row):
			inst = str(row[inst_col]).strip() if pd.notna(row[inst_col]) else ''
			dec  = str(row[dec_col]).strip()  if dec_col and pd.notna(row[dec_col]) else ''
			return f"{inst}:{dec}"

		keys = subset.apply(_mem_key, axis=1).dropna()
		keys = keys[keys != ':']
		if not keys.empty:
			cnt = Counter(keys)
			winner, unique = self._argmax_unique(cnt)
			mem_mcas = len(subset)
			if unique and winner != 'NotFound':
				parts    = winner.split(':')
				inst_val = parts[0] if len(parts) > 0 else ''
				dec_val  = parts[1] if len(parts) > 1 else ''
				mem_hint    = inst_val
				mem_details = f"{dec_val} ({cnt[winner]} occurrences)"
				if debug:
					print(f"\n[RevMEM] VID={vid}: hint={mem_hint!r}  "
						  f"details={mem_details!r}")
		return mem_hint, mem_details, mem_mcas

	# =========================================================================
	# RevCHACount equivalent
	# =========================================================================

	def _build_rev_cha_count(self, cha_df, firsterr_df, debug=False):
		"""
		Per-VisualID CHA hint dispatcher.

		Routes per-VID computation to the product-specific helper:
		  - GNR/CWF → _cha_hint_gnr_cwf()  (ML2 + MCERR FirstError tie-break)
		  - DMR     → _cha_hint_dmr()       (synthetic ENV+CBO key, ML2 only)

		Returns DataFrame: VisualID, CHA Hint, CHA Fail Area, SrcID Hint
		"""
		rows = []
		if cha_df.empty:
			return pd.DataFrame(columns=['VisualID', 'CHA Hint', 'CHA Fail Area', 'SrcID Hint'])

		vid_col = 'VisualID' if 'VisualID' in cha_df.columns else 'VisualId'
		is_dmr  = self.product in _DMR_PRODUCTS

		if is_dmr:
			env_col  = 'ENV'      if 'ENV'      in cha_df.columns else None
			inst_col = 'Instance' if 'Instance' in cha_df.columns else None
			src_col  = ('ModuleID' if 'ModuleID' in cha_df.columns else
						('SrcID'   if 'SrcID'    in cha_df.columns else None))
		else:
			cha_col = 'CHA'   if 'CHA'   in cha_df.columns else None
			src_col = 'SrcID' if 'SrcID' in cha_df.columns else None

		for vid in cha_df[vid_col].dropna().unique():
			if debug:
				label = 'RevCHA-DMR' if is_dmr else 'RevCHA'
				print(f"\n[{label}] VID={vid}")

			subset = cha_df[cha_df[vid_col] == vid]

			if is_dmr:
				cha_hint, cha_area = self._cha_hint_dmr(
					subset, env_col, inst_col, vid, debug)
			else:
				cha_hint, cha_area = self._cha_hint_gnr_cwf(
					subset, cha_col, firsterr_df, vid, debug)

			srcid_hint = 'NotFound'
			if src_col and not subset[src_col].dropna().empty:
				srcid_counts = Counter(subset[src_col].dropna())
				src_winner, src_unique = self._argmax_unique(srcid_counts)
				if src_unique and src_winner != 'NotFound':
					srcid_hint = src_winner

			rows.append({
				'VisualID'     : vid,
				'CHA Hint'     : cha_hint,
				'CHA Fail Area': cha_area,
				'SrcID Hint'   : srcid_hint,
			})

		return pd.DataFrame(rows)

	# =========================================================================
	# RevLLCCount equivalent
	# =========================================================================

	def _build_rev_llc_count(self, llc_df, firsterr_df, debug=False):
		"""
		Per-VisualID LLC hint dispatcher.

		Routes per-VID computation to the product-specific helper:
		  - GNR/CWF → _llc_hint_gnr_cwf()  (ML2 + MCERR FirstError tie-break)
		  - DMR     → early-return (CCF combined block; LLC is always empty)

		Returns DataFrame: VisualID, LLC Hint, LLC Fail Area
		"""
		rows = []
		if llc_df.empty or self.product in _DMR_PRODUCTS:
			return pd.DataFrame(columns=['VisualID', 'LLC Hint', 'LLC Fail Area'])

		vid_col = 'VisualID' if 'VisualID' in llc_df.columns else 'VisualId'
		llc_col = 'LLC' if 'LLC' in llc_df.columns else None

		for vid in llc_df[vid_col].dropna().unique():
			if debug:
				print(f"\n[RevLLC] VID={vid}")

			subset = llc_df[llc_df[vid_col] == vid]
			llc_hint, llc_area = self._llc_hint_gnr_cwf(
				subset, llc_col, firsterr_df, vid, debug)

			rows.append({
				'VisualID'     : vid,
				'LLC Hint'     : llc_hint,
				'LLC Fail Area': llc_area,
			})

		return pd.DataFrame(rows)

	# =========================================================================
	# RevCoreCount equivalent
	# =========================================================================

	def _build_rev_core_count(self, core_df, firsterr_df, debug=False):
		"""
		Per-VisualID Core hint dispatcher.

		Routes per-VID computation to the product-specific helper:
		  - GNR/CWF → _core_hint_gnr_cwf()  (IERR gate + ML2 + MCERR tie-break)
		  - DMR     → _core_hint_dmr()       (ML2 counts only; no IERR/FirstError)

		Returns DataFrame: VisualID, Core Hint, Core Fail Area, Core MCAs
		"""
		rows = []
		if core_df.empty:
			return pd.DataFrame(
				columns=['VisualID', 'Core Hint', 'Core Fail Area', 'Core MCAs'])

		vid_col   = 'VisualID' if 'VisualID' in core_df.columns else 'VisualId'
		_core_key = 'MODULE' if self.product != 'GNR' else 'CORE'
		_err_key  = 'MC DECODE' if self.product != 'GNR' else 'MCACOD (ErrDecode)'
		core_col  = _core_key if _core_key in core_df.columns else None
		err_col   = (_err_key if _err_key in core_df.columns else
					('ErrorType' if 'ErrorType' in core_df.columns else None))

		is_dmr       = self.product in _DMR_PRODUCTS
		core_filter  = lambda p: p['is_core']

		for vid in core_df[vid_col].dropna().unique():
			if debug:
				print(f"\n[RevCore] VID={vid}")

			subset = core_df[core_df[vid_col] == vid]

			if is_dmr:
				core_hint, core_area, core_mcas = self._core_hint_dmr(
					subset, core_col, err_col, vid, debug)
			else:
				core_hint, core_area, core_mcas = self._core_hint_gnr_cwf(
					subset, core_col, err_col, firsterr_df, vid, core_filter, debug)

			rows.append({
				'VisualID'      : vid,
				'Core Hint'     : core_hint,
				'Core Fail Area': core_area,
				'Core MCAs'     : core_mcas,
			})

		return pd.DataFrame(rows)

	# =========================================================================
	# Other Errors  (non-CORE/CHA/LLC IERR first errors)
	# =========================================================================

	def _build_other_errors(self, firsterr_df, debug=False):
		"""
		Build per-VisualID "Other Errors" string.

		Source: UBOX FirstError - Location rows (both MCERRLOGGINGREG and
		IERRLOGGINGREG) whose ip_translate is NOT CORE / CHA / LLC.
		Examples: PUNIT, B2CMI, MSE, CMS, SBO, UBOX, …

		PUNIT/UBOX appear in IERR rows; B2CMI/MSE/CMS/SBO appear in MCERR rows.
		Both register types are scanned so no IP class is missed.

		Returns dict {visual_id: "PUNIT:EPRPUNIT1, B2CMI:DDRFMB6, …"}
		"""
		other = {}
		if firsterr_df.empty:
			return other

		vid_col = 'VisualID' if 'VisualID' in firsterr_df.columns else 'VisualId'
		loc_col = 'FirstError - Location'

		if loc_col not in firsterr_df.columns:
			return other

		for vid in firsterr_df[vid_col].dropna().unique():
			sub = firsterr_df[firsterr_df[vid_col] == vid]
			# Scan ALL rows (both IERR and MCERR): each IP class appears in
			# exactly one register type per ip_translation.json failing_ips.

			seen      = {}     # display → count
			for loc in sub[loc_col].dropna():
				parsed = self._parse_firsterr_location(loc)
				if not parsed:
					continue
				if parsed['is_core'] or parsed['is_cha'] or parsed['is_llc']:
					continue   # handled by Rev*Count
				disp = parsed['display']
				if disp:
					seen[disp] = seen.get(disp, 0) + 1

			# Report only the most-frequent (dominant) other-error(s)
			if seen:
				max_cnt   = max(seen.values())
				dominant  = [d for d, c in seen.items() if c == max_cnt]
				other_str = ', '.join(dominant)
			else:
				other_str = ''

			other[vid] = other_str

			if debug and other_str:
				print(f"\n[OtherErr] VID={vid}: {other_str}"
					  f"  (counts: {seen})")

		return other

	# =========================================================================
	# IO/MEM Commonality Analyzers (Phase 3)
	# =========================================================================

	def _build_rev_io_count(self, io_df, debug=False):
		"""
		Per-VisualID IO hint dispatcher.

		Resolves the product-specific group column (IO for GNR/CWF, IMH_CBB for
		DMR) and delegates per-VID computation to _io_hint_per_vid().

		Returns DataFrame: VisualID, IO Hint, IO Details, IO MCAs
		"""
		rows = []
		if io_df is None or io_df.empty:
			return pd.DataFrame(columns=['VisualID', 'IO Hint', 'IO Details', 'IO MCAs'])

		vid_col  = 'VisualID' if 'VisualID' in io_df.columns else 'VisualId'
		inst_col = 'Instance'  if 'Instance'  in io_df.columns else None
		dec_col  = 'MC_DECODE' if 'MC_DECODE' in io_df.columns else None

		# Group column differs by product
		if self.product in _DMR_PRODUCTS:
			grp_col = 'IMH_CBB' if 'IMH_CBB' in io_df.columns else None
		else:
			grp_col = 'IO' if 'IO' in io_df.columns else None

		for vid in io_df[vid_col].dropna().unique():
			subset = io_df[io_df[vid_col] == vid]
			io_hint, io_details, io_mcas = self._io_hint_per_vid(
				subset, grp_col, inst_col, dec_col, vid, debug)
			rows.append({
				'VisualID'  : vid,
				'IO Hint'   : io_hint,
				'IO Details': io_details,
				'IO MCAs'   : io_mcas,
			})

		return pd.DataFrame(rows)

	def _build_rev_mem_count(self, mem_df, debug=False):
		"""
		Per-VisualID MEM hint dispatcher.

		Delegates per-VID computation to the product-neutral _mem_hint_per_vid().

		Returns DataFrame: VisualID, MEM Hint, MEM Details, MEM MCAs
		"""
		rows = []
		if mem_df is None or mem_df.empty:
			return pd.DataFrame(columns=['VisualID', 'MEM Hint', 'MEM Details', 'MEM MCAs'])

		vid_col  = 'VisualID' if 'VisualID' in mem_df.columns else 'VisualId'
		inst_col = 'Instance'  if 'Instance'  in mem_df.columns else None
		dec_col  = 'MC_DECODE' if 'MC_DECODE' in mem_df.columns else None

		for vid in mem_df[vid_col].dropna().unique():
			subset = mem_df[mem_df[vid_col] == vid]
			mem_hint, mem_details, mem_mcas = self._mem_hint_per_vid(
				subset, inst_col, dec_col, vid, debug)
			rows.append({
				'VisualID'   : vid,
				'MEM Hint'   : mem_hint,
				'MEM Details': mem_details,
				'MEM MCAs'   : mem_mcas,
			})

		return pd.DataFrame(rows)

	# =========================================================================
	# REV_Units equivalent
	# =========================================================================

	def _build_rev_units(self, cha_df, llc_df, core_df,
						 rev_cha, rev_llc, rev_core, other_errors,
						 rev_io=None, rev_mem=None):
		"""
		Build the REV_Units per-unit summary DataFrame.

		Columns:
		  VisualID, # Runs, Core Hint, Core Fail Area, CHA Hint, CHA Fail Area,
		  LLC Hint, LLC Fail Area, SrcIDs, Other, Top OrigReq, Top OpCode,
		  Top ISMQ, Top SAD, Top SAD LocPort, SAD Targets, Core MCAs,
		  IO Hint, IO Details, IO MCAs, MEM Hint, MEM Details, MEM MCAs
		"""
		_empty_io  = pd.DataFrame(columns=['VisualID', 'IO Hint',  'IO Details',  'IO MCAs'])
		_empty_mem = pd.DataFrame(columns=['VisualID', 'MEM Hint', 'MEM Details', 'MEM MCAs'])
		if rev_io  is None: rev_io  = _empty_io
		if rev_mem is None: rev_mem = _empty_mem

		all_vids = self._get_visual_ids(cha_df, llc_df, core_df)

		def _lookup(df_ref, vid, field, default='NotFound'):
			if df_ref.empty or 'VisualID' not in df_ref.columns:
				return default
			row = df_ref[df_ref['VisualID'] == vid]
			if row.empty:
				return default
			val = row.iloc[0].get(field, default)
			return val if pd.notna(val) and val != '' else default

		def _count_runs(df, vid):
			if df.empty:
				return 0
			vc = 'VisualID' if 'VisualID' in df.columns else 'VisualId'
			rc = 'Run' if 'Run' in df.columns else None
			if not rc or vc not in df.columns:
				return 0
			return df[df[vc] == vid]['Run'].dropna().nunique()

		def _top_field(df, vid, field):
			if df.empty or field not in df.columns:
				return ''
			vc = 'VisualID' if 'VisualID' in df.columns else 'VisualId'
			vals = df[df[vc] == vid][field].dropna()
			vals = vals[vals.astype(str).str.strip() != '']
			if vals.empty:
				return ''
			# Always return a value; append '*' when multiple values tie for top count
			cnt = Counter(vals)
			top_count = cnt.most_common(1)[0][1]
			top_vals = [v for v, c in cnt.most_common() if c == top_count]
			winner = str(top_vals[0])
			return f"{winner}*" if len(top_vals) > 1 else winner

		rows = []
		for vid in all_vids:
			runs = max(_count_runs(cha_df, vid),
					   _count_runs(llc_df, vid),
					   _count_runs(core_df, vid))

			core_hint = _lookup(rev_core, vid, 'Core Hint')
			core_area = _lookup(rev_core, vid, 'Core Fail Area', default='')
			core_mcas = _lookup(rev_core, vid, 'Core MCAs', default='')

			cha_hint  = _lookup(rev_cha, vid, 'CHA Hint')
			cha_area  = _lookup(rev_cha, vid, 'CHA Fail Area', default='')
			srcids    = _lookup(rev_cha, vid, 'SrcID Hint')

			llc_hint  = _lookup(rev_llc, vid, 'LLC Hint')
			llc_area  = _lookup(rev_llc, vid, 'LLC Fail Area', default='')

			other = other_errors.get(vid, '')

			top_origreq  = _top_field(cha_df, vid, 'Orig Req')
			top_opcode   = _top_field(cha_df, vid, 'Opcode')
			top_ismq     = _top_field(cha_df, vid, 'ISMQ')
			top_sad      = _top_field(cha_df, vid, 'Result')
			top_locport  = _top_field(cha_df, vid, 'Local Port')

			sad_targets = ''
			if not cha_df.empty and 'Local Port' in cha_df.columns:
				vc = 'VisualID' if 'VisualID' in cha_df.columns else 'VisualId'
				unique_ports = [
					str(p) for p in cha_df[cha_df[vc] == vid]['Local Port'].dropna().unique()
					if str(p) not in ('', 'nan')
				]
				sad_targets = ', '.join(unique_ports)

			io_hint    = _lookup(rev_io,  vid, 'IO Hint')
			io_details = _lookup(rev_io,  vid, 'IO Details',  default='')
			io_mcas    = _lookup(rev_io,  vid, 'IO MCAs',     default=0)

			mem_hint    = _lookup(rev_mem, vid, 'MEM Hint')
			mem_details = _lookup(rev_mem, vid, 'MEM Details', default='')
			mem_mcas    = _lookup(rev_mem, vid, 'MEM MCAs',    default=0)

			rows.append({
				'VisualID'      : vid,
				'# Runs'        : runs,
				'Core Hint'     : core_hint,
				'Core Fail Area': core_area,
				'CHA Hint'      : cha_hint,
				'CHA Fail Area' : cha_area,
				'LLC Hint'      : llc_hint,
				'LLC Fail Area' : llc_area,
				'SrcIDs'        : srcids,
				'Other'         : other,
				'Top OrigReq'   : top_origreq,
				'Top OpCode'    : top_opcode,
				'Top ISMQ'      : top_ismq,
				'Top SAD'       : top_sad,
				'Top SAD LocPort': top_locport,
				'SAD Targets'   : sad_targets,
				'Core MCAs'     : core_mcas,
				'IO Hint'       : io_hint,
				'IO Details'    : io_details,
				'IO MCAs'       : io_mcas,
				'MEM Hint'      : mem_hint,
				'MEM Details'   : mem_details,
				'MEM MCAs'      : mem_mcas,
			})

		return pd.DataFrame(rows)

	# =========================================================================
	# Analysis / Summary DataFrame
	# =========================================================================

	def _resolve_priority_order(self, context):
		"""
		Evaluate priority_rules.json rules against the per-row context dict and
		return (rc_order, dh_order) — the ordered lists of IP-category tokens
		('other', 'cha', 'llc', 'core') to use for Root Cause and Debug Hints.

		Rules are evaluated in declaration order; the first matching rule wins.
		If no rule matches, the default orders from the config are returned.

		Condition operators (JSON key patterns)
		---------------------------------------
		All conditions in a rule must be satisfied for the rule to match
		(implicit AND).  Three operator suffixes are supported for string
		context fields, plus direct boolean equality for flag fields:

		  {field}_equals  <str>   – exact case-sensitive match
		  {field}_in      [list]  – membership in a list of strings
		  {field}_contains <str>  – substring present anywhere in the value

		  {flag}          <bool>  – direct equality for boolean context keys

		String context fields available in conditions
		----------------------------------------------
		  top_origreq   – value of 'Top OrigReq'    (e.g. "PortIn", "Read")
		  top_opcode    – value of 'Top OpCode'      (e.g. "RdCur", "WrPush")
		  top_ismq      – value of 'Top ISMQ'
		  top_sad       – value of 'Top SAD'
		  top_locport   – value of 'Top SAD LocPort'
		  core_mcas     – value of 'Core Mcas'

		Boolean context flags available in conditions
		----------------------------------------------
		  cha_hint_present   – True when CHA Hint != 'NotFound'
		  llc_hint_present   – True when LLC Hint != 'NotFound'
		  core_hint_present  – True when Core Hint != 'NotFound'
		  srcid_present      – True when SrcIDs != 'NotFound'
		  other_present      – True when Other is non-empty
		  io_hint_present    – True when IO Hint  != 'NotFound'
		  mem_hint_present   – True when MEM Hint != 'NotFound'

		Examples
		--------
		  # Exact match on a single string field
		  "condition": { "top_origreq_equals": "PortIn" }

		  # Membership in a list
		  "condition": { "top_origreq_in": ["PortIn", "PortOut"] }

		  # Substring (e.g. core bank error)
		  "condition": { "core_mcas_contains": "bank" }

		  # Boolean flag combined with string match
		  "condition": {
		    "top_origreq_equals": "PortIn",
		    "cha_hint_present"  : true,
		    "srcid_present"     : true
		  }
		"""
		for rule in self._priority_rules:
			cond = rule.get('condition', {})
			# An empty/absent condition dict is a catch-all: it matches every row.
			# This is intentional and can be used to set a product-wide default
			# override at the end of the rules list (last resort).
			match = True

			for cond_key, cond_val in cond.items():
				if cond_key.endswith('_equals'):
					ctx_key = cond_key[:-len('_equals')]
					# String fields are always str (initialized with '' fallback)
					if context.get(ctx_key, '') != cond_val:
						match = False
						break
				elif cond_key.endswith('_in'):
					ctx_key = cond_key[:-len('_in')]
					if context.get(ctx_key, '') not in cond_val:
						match = False
						break
				elif cond_key.endswith('_contains'):
					ctx_key = cond_key[:-len('_contains')]
					# str() is safe: string context fields are always str ('');
					# this guard also handles any unexpected non-string values.
					if cond_val not in str(context.get(ctx_key, '')):
						match = False
						break
				else:
					# Direct boolean / value equality (for presence flags)
					if context.get(cond_key) != cond_val:
						match = False
						break

			if match:
				rc_order = rule.get('override_root_cause_order',  self._default_rc_order)
				dh_order = rule.get('override_debug_hints_order', self._default_dh_order)
				return rc_order, dh_order

		return self._default_rc_order, self._default_dh_order

	def _build_analysis(self, rev_units, ppv_df=None):
		"""
		Build the final Analysis/Summary DataFrame that replicates the
		Excel 'Analysis' (summ) table.

		Columns (matching Excel column order):
		  VisualIDs, Lot, WW, # Runs, Core Hint, Core Fail Area,
		  CHA Hint, CHA Fail Area, LLC Hint, LLC Fail Area, SrcIDs,
		  Other, Top OrigReq, Top OpCode, Top ISMQ, Top SAD,
		  Top SAD LocPort, Core Mcas, Root Cause,
		  Core Next Steps, CHA Next Steps, LLC Next Steps,
		  Other Next Steps, Debug Hints, Failing Area

		Root Cause and Debug Hints are determined by evaluating the rules
		defined in priority_rules.json for the product. The first matching
		rule's priority order is used; if no rule matches, the configured
		default order is applied.
		"""
		if rev_units.empty:
			return pd.DataFrame()

		ppv_lot = {}
		ppv_ww  = {}
		if ppv_df is not None and not ppv_df.empty:
			vc = next(
				(c for c in ('VisualId', 'VisualID', 'Data.Visual_ID')
				 if c in ppv_df.columns), None)
			if vc:
				for vid, grp in ppv_df.groupby(vc):
					if 'Lot' in ppv_df.columns:
						raw_lots = grp['Lot'].dropna().astype(str)
						unique_lots = dict.fromkeys(
							v.strip()
							for cell in raw_lots
							for v in cell.split(',')
							if v.strip()
						)
						ppv_lot[vid] = ', '.join(unique_lots)
					if 'DecimaWW' in ppv_df.columns:
						wws = grp['DecimaWW'].dropna().astype(str).unique()
						ppv_ww[vid] = ', '.join(wws)

		rows = []
		for _, ru in rev_units.iterrows():
			vid       = ru['VisualID']
			lot       = ppv_lot.get(vid, '')
			ww        = ppv_ww.get(vid, '')
			num_runs  = ru.get('# Runs', 0)

			core_hint  = ru.get('Core Hint',      'NotFound')
			core_area  = ru.get('Core Fail Area', '')
			cha_hint   = ru.get('CHA Hint',       'NotFound')
			cha_area   = ru.get('CHA Fail Area',  '')
			llc_hint   = ru.get('LLC Hint',       'NotFound')
			llc_area   = ru.get('LLC Fail Area',  '')
			srcids     = ru.get('SrcIDs',         'NotFound')
			other      = ru.get('Other',          '')
			top_origreq  = ru.get('Top OrigReq',    '')
			top_opcode   = ru.get('Top OpCode',     '')
			top_ismq     = ru.get('Top ISMQ',       '')
			top_sad      = ru.get('Top SAD',        '')
			top_locport  = ru.get('Top SAD LocPort','')
			core_mcas    = ru.get('Core MCAs',      '')

			io_hint     = ru.get('IO Hint',     'NotFound')
			io_details  = ru.get('IO Details',  '')
			io_mcas     = ru.get('IO MCAs',     0)
			mem_hint    = ru.get('MEM Hint',    'NotFound')
			mem_details = ru.get('MEM Details', '')
			mem_mcas    = ru.get('MEM MCAs',    0)

			# Resolve priority orders via configurable rules
			_ctx = {
				# String fields – support _equals, _in, _contains operators
				# Strip trailing '*' (tie indicator) for rule matching
				'top_origreq'  : top_origreq.rstrip('*'),
				'top_opcode'   : top_opcode.rstrip('*'),
				'top_ismq'     : top_ismq.rstrip('*'),
				'top_sad'      : top_sad.rstrip('*'),
				'top_locport'  : top_locport.rstrip('*'),
				'core_mcas'    : core_mcas,
				'io_mcas'      : str(io_mcas),
				'mem_mcas'     : str(mem_mcas),
				# Boolean presence flags – direct equality match
				'cha_hint_present' : cha_hint  != 'NotFound',
				'llc_hint_present' : llc_hint  != 'NotFound',
				'core_hint_present': core_hint != 'NotFound',
				'srcid_present'    : srcids    != 'NotFound',
				'other_present'    : bool(other),
				'io_hint_present'  : io_hint   != 'NotFound',
				'mem_hint_present' : mem_hint  != 'NotFound',
			}
			rc_order, dh_order = self._resolve_priority_order(_ctx)

			# Map category token → (value, is_present)
			_rc_map = {
				'other': (other,     bool(other)),
				'cha'  : (cha_hint,  cha_hint  != 'NotFound'),
				'llc'  : (llc_hint,  llc_hint  != 'NotFound'),
				'core' : (core_hint, core_hint != 'NotFound'),
				'io'   : (io_hint,   io_hint   != 'NotFound'),
				'mem'  : (mem_hint,  mem_hint  != 'NotFound'),
			}

			# Root Cause – first present entry in the resolved priority order
			root_cause = ''
			for token in rc_order:
				val, present = _rc_map.get(token, ('', False))
				if present:
					root_cause = val
					break

			# Next Steps
			core_next = (f"Disable CORE: {core_hint} - MCAs: {core_mcas}"
						 if core_hint != 'NotFound' else '')

			if cha_hint != 'NotFound':
				sig      = ' - '.join(filter(None, [top_origreq, top_ismq]))
				cha_next = f"Disable CHA: {cha_hint} - Signature: {sig} : {top_locport}".rstrip(' :')
			elif srcids != 'NotFound':
				sig      = ' - '.join(filter(None, [top_origreq, top_ismq]))
				cha_next = f"Disable SrcID: {srcids} - Signature: {sig} : {top_locport}".rstrip(' :')
			else:
				cha_next = ''

			llc_next   = (f"Disable LLC: {llc_hint}" if llc_hint != 'NotFound' else '')
			other_next = (f"Defeature: {other}  -- Check CORE or CHA MCAs for more data."
						  if other else '')
			io_next    = (f"Check IO: {io_hint} - {io_details}" if io_hint != 'NotFound' else '')
			mem_next   = (f"Check MEM: {mem_hint} - {mem_details}" if mem_hint != 'NotFound' else '')

			# Map category token → next-step string
			_dh_map = {
				'other': other_next,
				'cha'  : cha_next,
				'llc'  : llc_next,
				'core' : core_next,
				'io'   : io_next,
				'mem'  : mem_next,
			}

			# Debug Hints – first non-empty next-step in the resolved priority order
			debug_hints = ''
			for token in dh_order:
				val = _dh_map.get(token, '')
				if val:
					debug_hints = val
					break

			fail_parts = []
			if core_area:
				fail_parts.append(f"CORE: {core_area}")
			if cha_area:
				fail_parts.append(f"CHA: {cha_area}")
			if llc_area:
				fail_parts.append(f"LLC: {llc_area}")
			failing_area = ' - '.join(fail_parts)

			rows.append({
				'VisualIDs'        : vid,
				'Lot'              : lot,
				'WW'               : ww,
				'# Runs'           : num_runs,
				'Core Hint'        : core_hint,
				'Core Fail Area'   : core_area,
				'CHA Hint'         : cha_hint,
				'CHA Fail Area'    : cha_area,
				'LLC Hint'         : llc_hint,
				'LLC Fail Area'    : llc_area,
				'SrcIDs'           : srcids,
				'Other'            : other,
				'Top OrigReq'      : top_origreq,
				'Top OpCode'       : top_opcode,
				'Top ISMQ'         : top_ismq,
				'Top SAD'          : top_sad,
				'Top SAD LocPort'  : top_locport,
				'Core Mcas'        : core_mcas,
				'IO Hint'          : io_hint,
				'IO Details'       : io_details,
				'MEM Hint'         : mem_hint,
				'MEM Details'      : mem_details,
				'Root Cause'       : root_cause,
				'Core Next Steps'  : core_next,
				'CHA Next Steps'   : cha_next,
				'LLC Next Steps'   : llc_next,
				'Other Next Steps' : other_next,
				'IO IPs Next Steps': io_next,
				'MEM IPs Next Steps': mem_next,
				'Debug Hints'      : debug_hints,
				'Failing Area'     : failing_area,
			})

		return pd.DataFrame(rows)

	# =========================================================================
	# Debug helpers
	# =========================================================================

	def _print_debug_summary(self, analysis):
		"""Print a compact comparison table of all VID results."""
		if analysis.empty:
			print("[DEBUG] Analysis DataFrame is empty.")
			return
		print(f"\n{'─'*110}")
		print(f"{'VID':<20} {'Core Hint':<12} {'Root Cause':<22} {'Debug Hints':<50}")
		print(f"{'─'*110}")
		for _, r in analysis.iterrows():
			print(f"{str(r['VisualIDs']):<20} "
				  f"{str(r['Core Hint']):<12} "
				  f"{str(r.get('Root Cause','')):<22} "
				  f"{str(r.get('Debug Hints',''))[:50]}")
		print(f"{'─'*110}\n")
