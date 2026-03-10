# Generate DMR log_portid.json from SbPortIdProvider.csv
# Source: c:\\pythonsv\\diamondrapids\\ubox\\preSi\\SbPortIdProvider.csv
# Output: c:\\Git\\Automation\\PPV\\Decoder\\DMR\\log_portid.json

import csv
import json
import ast
import re
from pathlib import Path

INPUT_CSV  = r"c:\pythonsv\diamondrapids\ubox\preSi\SbPortIdProvider.csv"
OUTPUT_JSON = r"c:\Git\Automation\PPV\Decoder\DMR\log_portid.json"

portid_map = {}

with open(INPUT_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        alias     = row.get('Alias_Name', '').strip()
        interface = row.get('Sideband Interface', '').strip()
        sb_type   = row.get('GPSB or PMSB', '').strip()
        portid_str = row.get('SB Port ID', '').strip()

        if not portid_str:
            continue

        # Normalize the portid string so ast.literal_eval can parse it
        # e.g.  {6: 'ch0', 47: 'ch1'}  or  {9: None}  or  {252:None}
        try:
            portid_dict = ast.literal_eval(portid_str)
        except Exception:
            # Try fixing common issues like missing spaces
            try:
                portid_dict = ast.literal_eval(portid_str.replace(':None', ': None'))
            except Exception:
                print(f"  [SKIP] Could not parse portid: {portid_str!r}  (row: {alias})")
                continue

        # Build the display name
        # Format:  ALIAS.interface  (e.g. "S3M.iosf_sbb_s2s_0")
        # If alias is empty, fall back to interface
        if alias:
            base_name = f"{alias}.{interface}" if interface else alias
        else:
            base_name = interface if interface else "unknown"

        for pid, sub in portid_dict.items():
            pid_str = str(pid)
            if sub is not None:
                display = f"{base_name}.{sub}"
            else:
                display = base_name

            # If a portid is already mapped (multiple interfaces share it),
            # append the new name to avoid silent overwrite
            if pid_str in portid_map:
                existing = portid_map[pid_str]
                if isinstance(existing, list):
                    existing.append(display)
                else:
                    portid_map[pid_str] = [existing, display]
            else:
                portid_map[pid_str] = display

# Flatten lists to a single string joined by " / " for readability
flat_map = {}
for pid, val in portid_map.items():
    if isinstance(val, list):
        flat_map[pid] = " / ".join(val)
    else:
        flat_map[pid] = val

# Sort numerically
sorted_map = {str(k): flat_map[str(k)]
              for k in sorted(flat_map.keys(), key=lambda x: int(x))}

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(sorted_map, f, indent=4)

print(f"Generated {len(sorted_map)} port ID entries -> {OUTPUT_JSON}")
