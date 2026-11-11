"""Compare qualified_exempt.yaml with every county plan parsed into parsed_rates.json.

Usage: python -I check_exempt.py PARSED.json QUALIFIED_EXEMPT.yaml
"""
import json
import sys
from datetime import date
from decimal import Decimal

import yaml

parsed_path, yaml_path = sys.argv[1], sys.argv[2]
parsed = json.load(open(parsed_path))
table = {k: v for k, v in yaml.safe_load(open(yaml_path)).items() if k.endswith("_CO")}


def in_force(values, day):
    starts = sorted(values)
    latest = [s for s in starts if s <= day]
    return Decimal(str(values[latest[-1] if latest else starts[0]]))


mismatches = 0
checked = 0
for county, plans in parsed["exempt"].items():
    for start, cells in plans.items():
        day = date.fromisoformat(start)
        for band in ("UNDER_5", "AGE_5_AND_OVER"):
            want = Decimal(cells[band])
            got = in_force(table[county][band], day)
            checked += 1
            if want != got:
                mismatches += 1
                print("MISMATCH", county, start, band, "plan", want, "yaml", got, cells.get("file"))
print("checked", checked, "mismatches", mismatches)
print("counties in yaml", len(table), "counties parsed", len(parsed["exempt"]))
