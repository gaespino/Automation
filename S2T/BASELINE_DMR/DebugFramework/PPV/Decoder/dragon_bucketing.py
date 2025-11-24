#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A module for decoding Dragon error statuses into buckets and
other related functions.
"""
# This .py file can used in one of two ways.
#
# First would be to include it as part of a larger Python package and
# import as a module.  Example Python code:
#
# >>> import dragon_bucketing
# >>> dragon_bucketing.bucket('C001420D', 'ICL', 'DR04-Yakko-WsZ-AA000011.obj')
# Bucket(main='PM_Flow', sub='General PM flow', retest=True, algo='Yakko', meta='Fully Parsed')
# >>> dragon_bucketing.get_main_labels()
# ['Data_Miscompare', 'x86_Fault', 'DRNG', ...]
# >>> dragon_bucketing.get_algo('DR04-Yakko-WsZ-AA000011.obj')
# 'Yakko'
#
# Each of the above methods are documented at length further below.
#
# The `Bucket` class is a six-element tuple:
# -     main: Label for the main bucket
# -      sub: Label for the sub-bucket
# -     algo: Name of the Dragon algorithm parsed from seed name
# -   retest: True if the error suggests that re-testing is *recommended*,
#             False if re-testing is NOT recommended, or None if can't determine
# - priority: A *recommended* priority to use for DPM accounting,
#             where 1 is the highest priority, 2 is next highest, etc.
# -     meta: Metadata about how the input values were parsed.
# Note that this script will assume vvar information is a hex number, and
# all returned strings are single line ASCII with no control characters.
#
# All the possible values for `Bucket.main` and `Bucket.meta` exist as constants
# (module attributes using ALL_UPPERCASE_WITH_UNDERSCORES):
#
# >>> import dragon_bucketing
# >>> dragon_bucketing.DATA_MISCOMPARE
# 'Data_Miscompare'
#
# The other way to use this .py file is directly from the command line.
# Examples:
#
# > python .\dragon_bucketing.py --help
# More complete help information.
# > python .\dragon_bucketing.py bucket "C001420D" "ICL" "DR04-Yakko-WsZ-AA000011.obj"
# Calls the `bucket` method from the module.
# > python .\dragon_bucketing.py get_algo "DR04-Yakko-WsZ-AA000011.obj"
# Calls the `get_algo` method from the module.
# > python .\dragon_bucketing.py get_main_labels
# Calls the `get_main_labels` method from the module.

import collections
import re
import string
import sys


Bucket = collections.namedtuple('Bucket',
    ['main', 'sub', 'algo', 'retest', 'priority', 'meta'])
Bucket.__new__.__defaults__ = (None, False, 0, None)


def bucket(vvar, product=None, seed_name=None, is_os=False):
    """Decodes a Dragon error status into a bucket.

    Args:
        vvar: Value from Thread Status VVAR
        product: Product Acronym (e.g. ICX, SPR)
        seed_name: Name of the seed
        is_os: 'True' if this is a DoL/TSL seed

    Returns:
        `Bucket` tuple containing information of the bucket.
    """
    seed = None
    meta = FULLY_PARSED
    # if statements are set up so "higher precedence" meta cases are checked
    # after "lower precedence" ones
    if not product:
        meta = MISSING_PRODUCT
    if not seed_name:
        meta = MISSING_SEED_NAME
    if product:
        product = _fix_product(product)
        if product not in _mce_banks:
            meta = BAD_PRODUCT
    if seed_name:
        seed = _fix_seed_name(seed_name)
        if not seed:
            meta = BAD_SEED_NAME
    algo = seed.tmpl.family_name if seed is not None else None

    try:
        vvar = _fix_vvar(vvar)
        bckt = _bucket_top(vvar, product, seed, is_os)
        return Bucket(
            bckt.main, bckt.sub,
            retest=_get_retest(bckt.main), priority=_get_priority(bckt.main),
            algo=algo, meta=(bckt.meta or meta))
    except:
        return Bucket(
            UNKNOWN, UNKNOWN,
            retest=_get_retest(UNKNOWN), priority=_get_priority(UNKNOWN),
            algo=algo, meta=BAD_ERRORCODE)


def get_main_labels():
    """Gets all the main bucket labels in priority order."""
    mod = sys.modules[__name__]
    bckts = []
    for glbl in dir(mod):
        bkct_main = getattr(mod, glbl)
        priority = _get_priority(bkct_main)
        if priority <= 0:
            continue
        if len(bckts) < priority:
            bckts += [None] * (priority - len(bckts))
        bckts[priority - 1] = bkct_main
    return bckts


def get_algo(seed_name):
    """Parses the Dragon algorithm name from a seed name.

    Args:
        seed_name: Name of the seed

    Returns:
        String containing the algorithm name, or `None` if it can't be parsed.
    """
    seed = _fix_seed_name(seed_name)
    return seed.tmpl.family_name if seed is not None else None


# Names for all main buckets
CONFIG_MISMATCH = "Config_Mismatch"
DATA_MISCOMPARE = "Data_Miscompare"
DRNG = "DRNG"
EARLY_TERMINATION = "Early_Termination"
FORCE_FAIL = "Force_Fail"
MCE_HARD = "MCE_Hard"
MCE_SOFT = "MCE_Soft"
PASS = "Pass"
PM_FLOW = "PM_Flow"
TEST_BUG = "Test_Bug"
TIMEOUT = "Timeout"
UNKNOWN = "Unknown"
X86_FAULT = "x86_Fault"

# Values for bucket meta information
BAD_ERRORCODE = "Failed to Parse Errorcode"
BAD_SEED_NAME = "Failed to Parse Seed Name"
BAD_PRODUCT = "Failed to Parse Product or Product Not Yet Supported"
MISSING_SEED_NAME = "Missing Seed Name"
MISSING_PRODUCT = "Missing Product"
FULLY_PARSED = "Fully Parsed"

# Everything below are private helper methods or classes

_mode_chars = 'MSQLHER'
_sep_chars = '_-'


def _get_priority(bckt_main):
    """Returns a recommended priority for DPM accounting."""
    if bckt_main == DATA_MISCOMPARE: return 1
    elif bckt_main == X86_FAULT: return 2
    elif bckt_main == DRNG: return 3
    elif bckt_main == MCE_HARD: return 4
    elif bckt_main == MCE_SOFT: return 5
    elif bckt_main == CONFIG_MISMATCH: return 6
    elif bckt_main == PM_FLOW: return 7
    elif bckt_main == TEST_BUG: return 8
    elif bckt_main == EARLY_TERMINATION: return 9
    elif bckt_main == UNKNOWN: return 10
    elif bckt_main == TIMEOUT: return 11
    elif bckt_main == FORCE_FAIL: return 12
    elif bckt_main == PASS: return 13
    # reaching the else is a bug but added for completeness
    else: return 0


def _get_retest(bckt_main):
    """Returns a Boolean for whether the error warrants re-testing."""
    if bckt_main in (FORCE_FAIL, PASS):
        # except for these as that's kinda ambiguous
        return None
    return _get_priority(bckt_main) >= 6


def _valid_prefix(prefix):
    """Of a seed name, returns True or False"""
    state = 0
    for c in prefix:
        if state == -1:
            if c in _sep_chars:
                state = 0
        elif state == 0:
            state = 1 if c.lower() == 'd' else -1
        elif state == 1:
            state = 2 if c.lower() in _mode_chars.lower() else -1
        elif state == 2:
            state = 3 if c in string.hexdigits else -1
        elif state == 3:
            if c in string.hexdigits: return True
            state = -1
    return False


def _check_suffix(suffix):
    """Checks the suffix of a seed name.
    Returns:
        A tuple (suffix, seednum) where
        suffix: The given suffix arg with seed number (and beyond) stripped.
        seednum: The seed number part of the suffix.
        If the suffix arg is not valid both tuple items are empty.
    """
    end, hexstart, hexcount = -1, -1, 0
    for idx, c in enumerate(suffix):
        if c in _sep_chars:
            end, hexstart, hexcount = idx, -1, 0
        elif not c.isalnum():
            break
        elif c in string.hexdigits:
            if hexstart < 0:
                hexstart = idx
            hexcount += 1
            if hexcount >= 8: # if 8 hex digits in a row
                return (suffix[:end], suffix[hexstart:hexstart+8])
        else:
            end, hexstart, hexcount = idx + 1, -1, 0
    return ('', '')


_SeedParts = collections.namedtuple('_SeedParts', ['tmpl', 'release', 'config'])


class _Template(object):
    def __init__(self, template_def, variant_chars):
        self.full_name = template_def.full_name
        self.family_name = template_def.family_name
        self.variant_chars = (variant_chars
            .strip(_sep_chars)
            .replace(_sep_chars[0], _sep_chars[-1])
            .upper())

    def __eq__(self, other):
        if isinstance(other, _Template):
            return (
                other.full_name == self.full_name and
                other.variant_chars == self.variant_chars)
        elif isinstance(other, _TemplateDef):
            return other.full_name == self.full_name
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class _TemplateDef(object):
    def __init__(self, *args):
        args_iter = iter(args)
        self.full_name = next(args_iter)
        self.family_name = self.full_name
        self.trunc_name = self.full_name
        self.short_name = None
        self.short_name_suffices = dict()
        try:
            while True:
                arg = next(args_iter)
                if isinstance(arg, dict):
                    self.short_name_suffices = arg
                if isinstance(arg, str):
                    if len(arg) > 2:
                        self.trunc_name = arg
                    else:
                        self.short_name = arg
        except StopIteration:
            pass
        if len(self.short_name_suffices) > 0 or self.trunc_name != self.full_name:
            self.family_name = self.full_name + ' family'

    def os_names(self):
        """Returns iterable of (name, template suffix)
        Examples:  ('EE', ''), ('FC', 'C'), ('CO', 'O')
        """
        if self.short_name:
            yield self.short_name, ''
            for name, suffix in self.short_name_suffices.items():
                yield name, suffix


_TemplateDef.Aes = _TemplateDef('Aes', 'AS')
_TemplateDef.Aught = _TemplateDef('Aught', 'AT')
_TemplateDef.Blender = _TemplateDef('Blender', 'BR')
_TemplateDef.Boom = _TemplateDef('Boom')
_TemplateDef.Cayley = _TemplateDef('Cayley', 'CY', {'CC': 'C', 'CO': 'O'}) # "Cayley" matches CayleyV/CayleyW as well (no ext)
_TemplateDef.Charyb = _TemplateDef('Charyb')
_TemplateDef.Demo = _TemplateDef('Demo', 'DO')
_TemplateDef.Ditto = _TemplateDef('Ditto', 'DT', {'DC': 'C'})
_TemplateDef.DittoMT = _TemplateDef('DittoMT', 'DM')
_TemplateDef.Eclipse = _TemplateDef('Eclipse')
_TemplateDef.EveGoogle = _TemplateDef('EveGoogle', 'EE')
_TemplateDef.Fireworx = _TemplateDef('Fireworx', 'Fire', 'FX', {'FI': 'C'})
_TemplateDef.Fissure = _TemplateDef('Fissure', 'FE')
_TemplateDef.Flipper = _TemplateDef('Flipper', 'FL')
_TemplateDef.Frenzy = _TemplateDef('Frenzy', 'FY', {'FZ': 'C'})
_TemplateDef.FRM = _TemplateDef('FRM', 'FM', {'FC': 'C'})
_TemplateDef.Fuso = _TemplateDef('Fuso', 'FO')
_TemplateDef.Geode = _TemplateDef('Geode', 'GE')
_TemplateDef.Kawachi = _TemplateDef('Kawachi', 'KI')
_TemplateDef.LeekSpin = _TemplateDef('LeekSpin', 'Leek', 'LN', {'LC': 'C'})
_TemplateDef.Loki = _TemplateDef('Loki')
_TemplateDef.Millet = _TemplateDef('Millet', 'MI')
_TemplateDef.Oakley = _TemplateDef('Oakley', 'OY')
_TemplateDef.Padlock = _TemplateDef('Padlock')
_TemplateDef.PlusOne = _TemplateDef('PlusOne', 'PE')
_TemplateDef.QSpam = _TemplateDef('QSpam', 'QM')
_TemplateDef.ReadDRNG = _TemplateDef('ReadDRNG')
_TemplateDef.ReportApic = _TemplateDef('ReportApic', 'RA')
_TemplateDef.ReportLoop = _TemplateDef('ReportLoop', 'RL')
_TemplateDef.Sanity = _TemplateDef('Sanity')
_TemplateDef.SanityPR = _TemplateDef('SanityPR')
_TemplateDef.Satsuma = _TemplateDef('Satsuma', 'SA')
_TemplateDef.Scylla = _TemplateDef('Scylla')
_TemplateDef.Skipper = _TemplateDef('Skipper', 'SR')
_TemplateDef.Twiddle = _TemplateDef('Twiddle', 'TE')
_TemplateDef.Yakko = _TemplateDef('Yakko', 'YO')

def _get_all_template_defs():
    attrs = (a for a in dir(_TemplateDef) if not a.startswith('_'))
    values = map(lambda a: getattr(_TemplateDef, a), attrs)
    return (v for v in values if isinstance(v, _TemplateDef))


_mce_banks = dict()
_product_alias = dict()

_mce_banks['hsx'] = ["IFU", "DCU", "TLB", "MLC", "PCU", "QPI", "IIO/Ubox", "CHA/CBO/LLC", "CHA/CBO/LLC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "QPI", "QPI"]

_product_alias['aml'] = 'skl'
_product_alias['whl'] = 'skl'
_product_alias['cfl'] = 'skl'
_product_alias['cml'] = 'skl'
_product_alias['kbl'] = 'skl'
_mce_banks['skl'] = ["IFU", "DCU", "TLB", "MLC", "PCU", "MEE", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC"]

_product_alias['cpx'] = 'skx'
_product_alias['acf'] = 'skx'
_product_alias['clx'] = 'skx'
_mce_banks['skx'] = ["IFU", "DCU", "TLB", "MLC", "PCU", "UPI", "IIO/Ubox", "M2M", "M2M", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "UPI", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "UPI"]

_product_alias['hwl'] = 'bdx'
_product_alias['bdxml'] = 'bdx'
_product_alias['bdxde'] = 'bdx'
_mce_banks['bdx'] = ["IFU", "DCU", "TLB", "MLC", "PCU", "QPI", "IIO/Ubox", "CHA/CBO/LLC", "CHA/CBO/LLC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "QPI", "QPI"]

_product_alias['sph'] = 'icl'
_product_alias['rkl'] = 'icl'
_product_alias['tgl'] = 'icl'
_mce_banks['icl'] = ["IFU", "DCU", "TLB", "MLC", "MEE", "PCU", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "EDRAM", "EDRAM", "2LM", "2LM", "2LM", "2LM"]

_mce_banks['lkf'] = ["Atom BUS / BigCore IFU", "Atom MLC / BigCore DCU", "Atom FEC / BigCore TLB", "Atom MEC / BigCore MLC", "MEE", "MEE", "PCU", "CHA/CBO/LLC", "CHA/CBO/LLC"]

_product_alias['jsl'] = 'ehl'
_mce_banks['ehl'] = ["BUS", "MLC", "FEC", "MEC", "MEE", "MEE", "PCU", "CHA/CBO/LLC", "CHA/CBO/LLC"]

_mce_banks['snr'] = ["BUS", "MLC", "FEC", "MEC", "Bunit", "PCU", "IOMCA", None, None, "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "M2M", "iMC", "iMC", "iMC"]

_product_alias['icxsp'] = 'icx'
_product_alias['icxd'] = 'icx'
_mce_banks['icx'] = ["IFU", "DCU", "TLB", "MLC", "PCU", "UPI", "IIO/Ubox", "UPI", "UPI", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "M2M", "iMC", "iMC", "iMC", "M2M", "iMC", "iMC", "iMC", "M2M", "iMC", "iMC", "iMC", "M2M", "iMC", "iMC", "iMC"]

_product_alias['emr'] = 'spr'
_mce_banks['spr'] = ["IFU", "DCU", "TLB", "MLC", "PCU", "UPI", "IIO/Ubox", "MDF", "MDF", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "M2M", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", None, None, None, None, None, None, None, None, "M2M", "HBM MC", "HBM MC"]

_product_alias['gnrap'] = 'gnr'
_product_alias['gnrsp'] = 'gnr'
_product_alias['gnrd'] = 'gnr'
_mce_banks['gnr'] = ["IFU", "DCU", "TLB", "MLC", "IIO/Ubox", "UPI", "PCU", "CHA/CBO/LLC", None, "CHA/CBO/LLC", None, "MSE", "M2M", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC"]

_product_alias['srfap'] = 'srf'
_product_alias['srfsp'] = 'srf'
_mce_banks['srf'] = ["BUS", "MLC", "FEC", "MEC", "IIO/Ubox", "UPI", "PCU", "CHA/CBO/LLC", None, "CHA/CBO/LLC", None, "MSE", "M2M", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC"]

_mce_banks['grr'] = ["BUS", "MLC", "FEC", "MEC", "IIO/Ubox", None, "PCU", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "MSE", "M2M", "iMC", "iMC"] #GRR shouldn't use banks 8 and 10 per standard, but one doc had a different instance list (0-3, 4-6; vs 0-6, none) so incl for paranoia

_product_alias['cwfap'] = 'cwf'
_product_alias['cwfsp'] = 'cwf'
_mce_banks['cwf'] = ["IFU", "DCU", "TLB", "MLC", "IIO/Ubox", "UPI", "PCU", "CHA/CBO/LLC", None, "CHA/CBO/LLC", None, "MSE", "M2M", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC"]

_product_alias['dmrap'] = 'dmr'
_product_alias['dmrsp'] = 'dmr'
_product_alias['dmrd'] = 'dmr'
_product_alias['dmredge'] = 'dmr'
_mce_banks['dmr'] = ["IFU", "DCU", "TLB", "MLC", "PCU", "NCU", "CHA/CBO/LLC", "D2D", None, None, "RASIP", "PCU", "HA", "HSF", "SCA", "D2D", "MSE", "IOCache", "UXI", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC"]

_mce_banks['pmr'] = ["BUS", "MLC", "FEC", "MEC", "PCU", "NCU", "CHA/CBO/LLC", "D2D", None, None, "RASIP", "PCU", "HA", "HSF", "SCA", "D2D", "MSE", "IOCache", None, "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC", "iMC"]

_product_alias['rpl'] = 'adl'
_mce_banks['adl'] = ["Atom BUS / BigCore FEC", "Atom MLC / BigCore DCU", "Atom FEC / BigCore TLB", "Atom MEC / BigCore MLC", "MEE", "MEE", "PCU", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC"]

_mce_banks['mtl'] = ["Atom BUS / BigCore FEC", "Atom MLC / BigCore DCU", "Atom FEC / BigCore TLB", "Atom MEC / BigCore MLC", "PCU", "MEE", "MEE", "IOC", "CHA/CBO/LLC", "CHA/CBO/LLC", None, None, None, None, "DMU", None, "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC"]
_mce_banks['arl'] = ["Atom BUS / BigCore FEC", "Atom MLC / BigCore DCU", "Atom FEC / BigCore TLB", "Atom MEC / BigCore MLC", "PCU", "MEE", "MEE", "IOC", "CHA/CBO/LLC", "CHA/CBO/LLC", None, None, None, None, "DMU", None, "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC"]

_mce_banks['lnl'] = ["Atom BUS / BigCore FEC", "Atom MLC / BigCore DCU", "Atom FEC / BigCore TLB", "Atom MEC / BigCore MLC", "PCU", "sNCU", "ICELAND", None, "HBO", "HBO", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC"]
_product_alias['wcl'] = 'ptl'
_mce_banks['ptl'] = ["Atom BUS / BigCore FEC", "Atom MLC / BigCore DCU", "Atom FEC / BigCore TLB", "Atom MEC / BigCore MLC", "PCU", "sNCU", "ICELAND", None, "HBO", "HBO", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC", "CHA/CBO/LLC"]

_mce_banks['nvl'] = ["Atom BUS / BigCore FEC", "Atom MLC / BigCore DCU", "Atom FEC / BigCore TLB", "Atom MEC / BigCore MLC", None, None, "CHA/CBO/LLC", None, None, "PCU", "sNCU", "DMU", "HBO"]

def _fix_vvar(vvar):
    try:
        types = (int, long) # long type for Python 2.x compat, Python 3.x falls to the "except" case with just int; so ignore any Python 3.x warnings about "long is not defined"
    except NameError:
        types = int
    return vvar if isinstance(vvar, types) else int(str(vvar), 16)


def _fix_product(product):
    if product is None: return None
    fixed = ''.join(c for c in str(product) if c.isalnum()).lower()
    if fixed in _product_alias:
        fixed = _product_alias[fixed]
    return fixed


def _fix_seed_name(seed_name):
    if seed_name is None: return None
    def get_candidates():
        # Search for full name, going from longest to shortest
        key = lambda d: len(d.trunc_name)
        for d in sorted(_get_all_template_defs(), key=key, reverse=True):
            parts = re.split(d.trunc_name, seed_name, maxsplit=1, flags=re.I)
            if len(parts) > 1:
                # check "extra" stuff and remove it
                # e.g. 'DR02-Fireworx-00000000' => ['DR02-', 'worx-00000000']
                #      need to remove 'worx'
                extra = d.full_name[len(d.trunc_name):]
                if extra and re.match(extra, parts[1], flags=re.I):
                    parts[1] = parts[1][len(extra):]
                yield (parts[0], d, parts[1])
        # Didn't find full name, look for external/OS names
        for d in _get_all_template_defs():
            for name, suffix in d.os_names():
                pattern = '[%s]%s[%s]' % (_sep_chars, name, _sep_chars)
                parts = re.split(pattern, seed_name, maxsplit=1, flags=re.I)
                if len(parts) > 1:
                    # if a suffix is defined for this os name, add it back in
                    # e.g. 'DR02-LC-00000000' => ['DR02', '00000000']
                    #      change to 'C-00000000'
                    if suffix:
                        parts[1] = suffix + _sep_chars[0] + parts[1]
                    yield (parts[0], d, parts[1])

    for prefix, d, suffix in get_candidates():
        if not _valid_prefix(prefix): continue
        suffix, seednum = _check_suffix(suffix)
        if not seednum: continue
        return _SeedParts(_Template(d, suffix),
            int(seednum[:2], 16), int(seednum[2], 16))
    return None


def _bucket_top(vvar, product, seed, is_os):
    if vvar < 0 or vvar > 0xFFFFFFFF or (
        vvar < 0x10000000 and vvar not in (0, 0x1040, 0xaced)):
        return Bucket(UNKNOWN, "malformed errorcode", meta=BAD_ERRORCODE)

    bckt = _bucket_test_bug(vvar, product, seed, is_os)
    if bckt:
        return bckt
    if is_os:
        bckt = _bucket_dol(vvar)
        if bckt:
            return bckt
    if (vvar >> 28) == 0xF:
        bckt = _bucket_test_specific_mismatch(vvar, seed)
        if bckt:
            return bckt
    if (vvar >> 28) in (0xC, 0xD):
        bckt = _bucket_special_interrupt(vvar, seed, is_os)
        if bckt:
            return bckt
        bckt = _bucket_normal_interrupt(vvar, is_os)
        if bckt:
            return bckt
    if (vvar >> 28) in (0xA, 0xB):
        bckt = _bucket_mce(vvar, product, is_os)
        if bckt:
            return bckt
    if not is_os:
        bckt = _bucket_bare_metal(vvar)
        if bckt:
            return bckt
    return Bucket(UNKNOWN, UNKNOWN)


def _bucket_test_bug(vvar, product, seed, is_os):
    if product is None or seed is None: return None
    def false_0x199_mismatch(): return Bucket(TEST_BUG, "Dragon PM Turbo bug: false 0x199 mismatch")

    def r4523_r6001_turbo_wrapper_up_on_dp4mp_or_dp_on_4mp():
        if is_os: return None
        if (vvar & 0xF0FFFFFF) == 0xC000000E:
            return Bucket(TEST_BUG, "Dragon PM Turbo bug: false #PF")
        if (vvar & 0xF0FFFFFF) == 0xC002020D:
            return false_0x199_mismatch()
        if vvar == 0xF0000199:
            if seed.tmpl == _TemplateDef.Sanity and seed.tmpl.variant_chars == 'MSR':
                return false_0x199_mismatch()
        return None

    # Product names are after _product_alias translation
    if product == 'skx':
        if seed.release in (0x64, 0x5F, 0x40, 0x3A, 0x24, 0x17, 0x14, 0xC7):
            return r4523_r6001_turbo_wrapper_up_on_dp4mp_or_dp_on_4mp()
    if product == 'bdx':
        if seed.release in (0x30, 0x2F, 0x26, 0x0A, 0x02, 0xBB, 0xA4):
            return r4523_r6001_turbo_wrapper_up_on_dp4mp_or_dp_on_4mp()
    if product == 'hsx':
        if seed.release in (0x22, 0x15, 0x0D):
            return r4523_r6001_turbo_wrapper_up_on_dp4mp_or_dp_on_4mp()
    return None


def _bucket_test_specific_mismatch(vvar, seed):
    if seed is None:
        return Bucket(DATA_MISCOMPARE, "Data Miscompare")
    def pm_unexpected_config(): return Bucket(PM_FLOW, "PM: Unexpected config")
    def pm_cstate_general_flow(): return Bucket(PM_FLOW, "PM: C-State general flow")
    def pm_core_enumerative_ratio_grant_failed(): return Bucket(PM_FLOW, "PM: Core enumerative ratio grant failed")
    def unexpected_number_of_threads(): return Bucket(CONFIG_MISMATCH, "unexpected number of threads")
    def unexpected_vmx_config(): return Bucket(CONFIG_MISMATCH, "Unexpected VMX config")

    if seed.tmpl == _TemplateDef.Sanity:
        if seed.tmpl.variant_chars == 'CST':
            if vvar == 0xFA07FA07: return pm_unexpected_config()
            if (vvar & 0x0FFFFFFF) in (1, 2, 4): return pm_cstate_general_flow()
            return Bucket(PM_FLOW, "PM: C-State not granted")
        elif seed.tmpl.variant_chars == 'MUC':
            return Bucket(CONFIG_MISMATCH, "Overly slow data access: check memory setup")
        elif seed.tmpl.variant_chars == 'MSR':
            return Bucket(CONFIG_MISMATCH, "MSR setup mismatch across threads")
        elif seed.tmpl.variant_chars == 'P23':
            return Bucket(CONFIG_MISMATCH, "patch2/3 DR access issue")
        elif seed.tmpl.variant_chars == 'PST':
            if (vvar & 0xFFFFFFFE) == 0xFFFFFFFE: return pm_unexpected_config()
            return pm_core_enumerative_ratio_grant_failed()
        elif seed.tmpl.variant_chars == 'TF':
            if vvar == 0xF7EBF7EB: return pm_unexpected_config()
            if (vvar & 0xFF00) == 0: return pm_unexpected_config()
            return pm_core_enumerative_ratio_grant_failed()
        elif seed.tmpl.variant_chars == 'TPU':
            return unexpected_number_of_threads()
        elif seed.tmpl.variant_chars == 'TRB':
            if vvar == 0xF7EBF7EB: return pm_unexpected_config()
            return pm_core_enumerative_ratio_grant_failed()
        elif seed.tmpl.variant_chars == 'TSC':
            return Bucket(CONFIG_MISMATCH, "TSC/ACNT not incrementing as expected")
        elif seed.tmpl.variant_chars == 'UFS':
            if vvar == 0xFFFFFFFF: return pm_unexpected_config()
            return Bucket(PM_FLOW, "PM: Uncore enumerative ratio grant failed")
        elif seed.tmpl.variant_chars == 'VMX':
            return unexpected_vmx_config()
    elif seed.tmpl == _TemplateDef.SanityPR:
        if seed.tmpl.variant_chars == 'V':
            return unexpected_vmx_config()

    elif seed.tmpl == _TemplateDef.DittoMT:
        if vvar == 0xF3A00000: return unexpected_number_of_threads()
    elif seed.tmpl in (
        _TemplateDef.ReportApic, _TemplateDef.ReportLoop, _TemplateDef.ReadDRNG):
        return Bucket(FORCE_FAIL, "Force fail: return info in place of fail code")
    elif seed.tmpl == _TemplateDef.Boom:
        return Bucket(FORCE_FAIL, "Force fail: integration check")

    return Bucket(DATA_MISCOMPARE, "Data Miscompare: " + seed.tmpl.family_name)


def _bucket_special_interrupt(vvar, seed, is_os):
    def pm_unexpected_config(): return Bucket(PM_FLOW, "PM: Unexpected config")
    def pm_general_flow(): return Bucket(PM_FLOW, "PM: General flow")
    def pm_cstate_general_flow(): return Bucket(PM_FLOW, "PM: C-State general flow")
    def pm_fact_general_flow(): return Bucket(PM_FLOW, "PM: FACT/SST-TF general flow")
    def pm_pstate_general_flow(): return Bucket(PM_FLOW, "PM: P-State general flow")
    def pm_turbo_general_flow(): return Bucket(PM_FLOW, "PM: Turbo general flow")
    def pm_ufs_flow_verify_failure(): return Bucket(PM_FLOW, "PM: UFS flow/verify failure")
    def pm_fail_to_restore_verify_ratio(): return Bucket(PM_FLOW, "PM: Fail to restore/verify ratio")
    low = vvar & 0xFFFFFF
    if (vvar >> 28) == 0xC:
        if low == 0x00000D: return Bucket(X86_FAULT, "#GP: plain General Protection Fault")
        if low == 0x01120D: return Bucket(DRNG, "DRNG: BIST failed")
        if low == 0x01220D: return Bucket(DATA_MISCOMPARE, "unexpected RTM abort or failure to abort")
        if low == 0x01320D:
            if seed is None:
                return Bucket(DATA_MISCOMPARE, "Data Miscompare")
            return Bucket(DATA_MISCOMPARE, "Data Miscompare: " + seed.tmpl.family_name)
        if low == 0x01620D: return Bucket(DRNG, "DRNG: did not receive a number")
        if low == 0x01720D: return Bucket(DRNG, "DRNG: 2 consecutive numbers matched")
        if not is_os:
            if low == 0x01420D: return pm_general_flow()
            if low == 0x01520D: return Bucket(X86_FAULT, "unexpected VM Exit")
            if low == 0x01820D: return pm_general_flow()
            if low == 0x01920D: return pm_general_flow()
            if low == 0x01A20D: return pm_fail_to_restore_verify_ratio()
            if low == 0x01B20D: return pm_general_flow()
            if low == 0x01C20D: return pm_unexpected_config()
            if low == 0x01E20D: return pm_unexpected_config()
            if low == 0x01F20D: return pm_unexpected_config()
            if low == 0x02020D: return pm_unexpected_config()
            if low == 0x02120D: return pm_unexpected_config()
            if low == 0x02220D: return Bucket(DATA_MISCOMPARE, "PKRU/PKRS read did not match write")
            if low == 0x02320D: return pm_unexpected_config()
            if low == 0x02420D: return pm_unexpected_config()
            if low == 0x02520D: return Bucket(CONFIG_MISMATCH, "PCI Segment: Unexpected config")
            if low == 0x02620D: return Bucket(CONFIG_MISMATCH, "PM: HPM/TPMI general flow, HPM table access out of bounds")
            if (low & 0xFFF) == 0x20D: return Bucket(UNKNOWN, "unrecognized special fake #GP")
    if (vvar >> 28) == 0xD:
        if not is_os:
            if low == 0x001017: return pm_cstate_general_flow()
            if low == 0x001117: return pm_cstate_general_flow()
            if low == 0x001217: return pm_cstate_general_flow()
            if low == 0x001317: return pm_fail_to_restore_verify_ratio()
            if low == 0x002017: return pm_pstate_general_flow()
            if low == 0x002117: return pm_pstate_general_flow()
            if low == 0x002217: return pm_fail_to_restore_verify_ratio()
            if low == 0x003017: return Bucket(TIMEOUT, "wbinvd started but not completed")
            if low == 0x004017: return pm_turbo_general_flow()
            if low == 0x004117: return pm_turbo_general_flow()
            if low == 0x004217: return pm_fail_to_restore_verify_ratio()
            if low == 0x004317: return pm_turbo_general_flow()
            if low == 0x004417: return pm_turbo_general_flow()
            if low == 0x004517: return pm_fail_to_restore_verify_ratio()
            if low == 0x004617: return pm_turbo_general_flow()
            # Created but never used: UfsStart=0x50
            if low == 0x005117: return pm_ufs_flow_verify_failure()
            if low == 0x005217: return pm_ufs_flow_verify_failure()
            if low == 0x005317: return pm_ufs_flow_verify_failure()
            if low == 0x006217: return pm_fail_to_restore_verify_ratio()
            if (low & 0xFFF0FF) == 0x0006017:
                return pm_fact_general_flow()
            if low == 0x007217: return pm_unexpected_config()
            if low == 0x007817: return pm_fail_to_restore_verify_ratio()
            if low == 0x007B17: return pm_unexpected_config()
            if (low & 0xFFF0FF) == 0x0007017:
                return pm_fact_general_flow()
    return None


def _bucket_normal_interrupt(vvar, is_os):
    def pm_unknown_unhandled_errors(): return Bucket(PM_FLOW, "PM: Unknown/unhandled errors")
    low = vvar & 0xFF
    if (vvar >> 28) == 0xC:
        if low == 0: return Bucket(X86_FAULT, "#DE: Divide Error")
        if low == 1: return Bucket(X86_FAULT, "#DB: Debug Exception")
        if low == 2:
            if is_os: return Bucket(X86_FAULT, "#NMI: Non Maskable Interrupt")
            else: return pm_unknown_unhandled_errors()
        if low == 3: return Bucket(X86_FAULT, "#BP: Breakpoint")
        if low == 4: return Bucket(X86_FAULT, "#OF: Overflow ")
        if low == 5: return Bucket(X86_FAULT, "#BR: BOUND Range Exceeded")
        if low == 6: return Bucket(X86_FAULT, "#UD: Invalid Opcode")
        if low == 7: return Bucket(X86_FAULT, "#NM: Device Not Available")
        if low == 8: return Bucket(X86_FAULT, "#DF: Double Fault")
        if low == 9: return Bucket(X86_FAULT, "RSVD: Was 287/387 Coprocessor Segment Overrun")
        if low == 0xA: return Bucket(X86_FAULT, "#TS: Invalid TSS")
        if low == 0xB: return Bucket(X86_FAULT, "#NP: Segment Not Present")
        if low == 0xC: return Bucket(X86_FAULT, "#SS: Stack-Segment Fault")
        if low == 0xD: return Bucket(X86_FAULT, "#GP: complex General Protection Fault")
        if low == 0xE: return Bucket(X86_FAULT, "#PF: Page Fault")
        if low == 0xF: return Bucket(X86_FAULT, "RSVD: Reserved x86 Fault vector")
    if (vvar >> 28) == 0xD:
        if low == 0x10: return Bucket(X86_FAULT, "#MF: x87 FPU Floating-Point Error")
        if low == 0x11: return Bucket(X86_FAULT, "#AC: Alignment Check")
        if low == 0x12: return Bucket(MCE_HARD, "#MC: Machine Check")
        if low == 0x13: return Bucket(X86_FAULT, "#XM: SIMD Floating Point Exception")
        if low == 0x14: return Bucket(X86_FAULT, "#VE: Virtualization Exception")
        if low == 0x15: return Bucket(X86_FAULT, "#CP: Control Protection Exception")
        if not is_os:
            if low == 0x16: return pm_unknown_unhandled_errors()
            if low == 0x17: return pm_unknown_unhandled_errors()
            if low == 0x18: return Bucket(MCE_SOFT, "Dragon CMCI Soft MCE Handler")
    return None


def _bucket_mce(vvar, product, is_os):
    if is_os:
        return None
    if (vvar >> 26) & 1 == 1:
        main = MCE_HARD
        sub = " hard MCE"
    else:
        main = MCE_SOFT
        sub = " soft MCE"

    if (vvar & 0xFFFFFF) == 0: # msr + bank is all 0
        return Bucket(main, "Sympathetic MCE")
    bank = vvar & 0xFF
    try:
        pltfm_info = _mce_banks[product]
        bank_name = pltfm_info[bank]
    except:
        bank_name = None
    if not bank_name:
        bank_name = "bank " + str(bank)
    return Bucket(main, bank_name + sub)


def _bucket_dol(vvar):
    """DoL/TSL specific errors that clash with other functions"""
    def unhandled_corruption(): return Bucket(EARLY_TERMINATION, "unhandled corruption")
    def test_kernel_did_not_start(): return Bucket(EARLY_TERMINATION, "test kernel did not start")
    if vvar == 0x00000000: return Bucket(PASS, PASS)
    if vvar == 0xDEADFADE: return unhandled_corruption() # TSL >= 3.7
    if vvar == 0xDEADDEAD: return Bucket(TIMEOUT, TIMEOUT)
    if vvar == 0xDEADBEEF: return Bucket(TIMEOUT, "Timeout and priority starved")
    if vvar == 0xDEAD0B0B: return Bucket(TIMEOUT, "Timeout and thermal throttling")
    if vvar == 0xDEADBEA7: return unhandled_corruption()
    if vvar == 0xDEADBAB4: return Bucket(CONFIG_MISMATCH, "thread disabled")
    if vvar == 0xDEADB005: return Bucket(UNKNOWN, "SigBus code=0, possible MCE") # TSL >= v3.12.3
    if vvar == 0xDEADABBA: return Bucket(TIMEOUT, "Seed sync Timeout") # TSL >= v3.12.3
    if vvar == 0xDEADAB04: return unhandled_corruption()
    if vvar == 0xC0FFC0FF: return test_kernel_did_not_start()
    if vvar == 0x48232323: return Bucket(UNKNOWN, UNKNOWN) # collision with _bucket_bare_metal
    if (vvar >> 28) == 0x4:
        return Bucket(CONFIG_MISMATCH, "missing ISA")
    if (0x27 >= (vvar >> 24) >= 0x22) and (vvar & 0xFFF) == 0:
        return test_kernel_did_not_start()
    return None


def _bucket_bare_metal(vvar):
    def unexpected_number_of_threads(): return Bucket(CONFIG_MISMATCH, "unexpected number of threads")
    def incorrect_vvar_inputs(): return Bucket(CONFIG_MISMATCH, "incorrect vvar inputs")
    def patch23_not_enabled(): return Bucket(CONFIG_MISMATCH, "patch2/3 not enabled")
    if vvar == 0x00000000: return Bucket(TIMEOUT, TIMEOUT)
    if vvar == 0x00001040: return Bucket(TIMEOUT, TIMEOUT)
    if vvar == 0x0000ACED: return Bucket(PASS, PASS)
    if vvar == 0x10000001: return unexpected_number_of_threads()
    if vvar == 0x10000002: return incorrect_vvar_inputs()
    if vvar == 0x10000003: return unexpected_number_of_threads()
    if vvar == 0x10000004: return incorrect_vvar_inputs()
    if vvar == 0x10000005: return incorrect_vvar_inputs()
    if vvar == 0x10000006: return incorrect_vvar_inputs()
    if vvar == 0x10000007: return incorrect_vvar_inputs()
    if vvar == 0x10000008: return incorrect_vvar_inputs()
    if vvar == 0x10000009: return unexpected_number_of_threads()
    if vvar == 0x1000000A: return unexpected_number_of_threads()
    if vvar == 0x1000000B: return incorrect_vvar_inputs()
    if vvar == 0x1000000C: return unexpected_number_of_threads()
    if vvar == 0x1000000D: return unexpected_number_of_threads()
    if vvar == 0x1000000E: return incorrect_vvar_inputs()
    if vvar == 0x1000000F: return Bucket(CONFIG_MISMATCH, "TSC/ACNT not incrementing as expected")
    if vvar == 0x10000010: return unexpected_number_of_threads()
    if vvar == 0x10000011: return incorrect_vvar_inputs()
    if vvar == 0x10000012: return incorrect_vvar_inputs()
    if vvar == 0x10000013: return incorrect_vvar_inputs()
    if vvar == 0x10000014: return incorrect_vvar_inputs()
    if vvar == 0x10000015: return incorrect_vvar_inputs()
    if vvar == 0x10000016: return incorrect_vvar_inputs()
    if vvar == 0x10000017: return incorrect_vvar_inputs()
    if vvar == 0x10000018: return incorrect_vvar_inputs()
    if vvar == 0x10000019: return incorrect_vvar_inputs()
    if vvar == 0x1000001A: return incorrect_vvar_inputs()
    if vvar == 0x1000001B: return incorrect_vvar_inputs()
    if vvar == 0x1000001C: return incorrect_vvar_inputs()
    if vvar == 0x20000001: return Bucket(EARLY_TERMINATION, "test kernel did not start")
    if vvar == 0x203B154D: return Bucket(TIMEOUT, "wbinvd started but not completed")
    if (vvar >> 24) == 0x20:
        if ((vvar & 0xFFF0) >> 4) == 0x020:
            return Bucket(EARLY_TERMINATION, "shutdown occurred")
    if vvar == 0x48232323: return patch23_not_enabled()
    if vvar == 0x53232323: return patch23_not_enabled()
    if vvar == 0x5B232323: return patch23_not_enabled()
    if (vvar >> 28) in (0x4, 0x5):
        return Bucket(CONFIG_MISMATCH, "missing ISA")
    if vvar == 0x600D600D: return Bucket(PASS, PASS)
    if vvar == 0x7FFFFFFF: return Bucket(EARLY_TERMINATION, "unhandled corruption")
    if (vvar >> 16) == 0x7000:
        return unexpected_number_of_threads()
    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Performs functions regarding Dragon error statuses.")
    subparsers = parser.add_subparsers(dest='subcommand')
    # bucket
    bucket_parser = subparsers.add_parser('bucket',
        help="Decodes a Dragon error status into a bucket.")
    bucket_parser.add_argument('vvar',
        help="Value from Thread Status VVAR")
    bucket_parser.add_argument('product',
        help="Product Acronym (e.g. ICX, SPR)",
        nargs='?', default=None)
    bucket_parser.add_argument('seed_name',
        help="Name of the seed",
        nargs='?', default=None)
    bucket_parser.add_argument('--is_os',
        help="Use if this is a DoL/TSL seed",
        action='store_true', default=False)
    # main labels
    main_labels_parser = subparsers.add_parser('get_main_labels',
        help="Prints all main bucket labels, in priority order.")
    # algo
    algo_parser = subparsers.add_parser('get_algo',
        help="Parses the Dragon algo name from a seed name.")
    algo_parser.add_argument('seed_name',
        help="Name of the seed",
        nargs='?', default=None)

    args = parser.parse_args()
    if args.subcommand == 'bucket':
        bckt = bucket(args.vvar, args.product, args.seed_name, args.is_os)
        print(bckt)
    elif args.subcommand == 'get_main_labels':
        print(get_main_labels())
    elif args.subcommand == 'get_algo':
        print(get_algo(args.seed_name))
