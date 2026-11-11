"""Compare licensed_center.yaml and licensed_home.yaml with the parsed state-established tables.

Usage: python -I check_licensed.py PARSED.json LICENSED_CENTER.yaml LICENSED_HOME.yaml
"""
import json
import sys
from datetime import date
from decimal import Decimal

import yaml

parsed_path, center_path, home_path = sys.argv[1:4]
parsed = json.load(open(parsed_path))
tables = {
    "CENTER": {k: v for k, v in yaml.safe_load(open(center_path)).items() if k.endswith("_CO")},
    "HOME": {k: v for k, v in yaml.safe_load(open(home_path)).items() if k.endswith("_CO")},
}
checked = mismatches = 0
kinds = set()
for start, cells in parsed["state"].items():
    day = date.fromisoformat(start)
    for key, value in cells.items():
        county, kind, band, tier = key.split("|")
        kinds.add(kind)
        values = tables[kind][county][band][tier]
        starts = sorted(values)
        latest = [s for s in starts if s <= day]
        got = Decimal(str(values[latest[-1] if latest else starts[0]]))
        checked += 1
        if got != Decimal(value):
            mismatches += 1
            print("MISMATCH", start, key, "pdf", value, "yaml", got)
# Every yaml cell should come from a parsed cell on one of the two dates.
extra = 0
for kind, table in tables.items():
    for county, bands in table.items():
        for band, tiers in bands.items():
            for tier, values in tiers.items():
                for start in values:
                    key = f"{county}|{kind}|{band}|{tier}"
                    if key not in parsed["state"].get(start.isoformat(), {}):
                        extra += 1
                        print("YAML-ONLY", start, key)
print("dates", sorted(parsed["state"]), "kinds", sorted(kinds))
print("checked", checked, "mismatches", mismatches, "yaml-only", extra)
