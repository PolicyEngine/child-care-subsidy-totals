"""Classify each state's 2026 child care subsidy gap from five cc_gap.py runs.

Usage: python classify_states.py RUN_DIR SOURCES_DIR OUT.csv OUT.md

RUN_DIR holds cc_gap.py outputs for one commit: main-base.json, main-ft-billed.json,
main-ft-all.json, main-rate-billed.json and main-rate-all.json. SOURCES_DIR holds
ccdf_table3a_fy2024.csv and ccdf_table4a_fy2024.csv (ACF's FY 2024 CCDF
expenditures, Tables 3a and 4a) and ccdf_fy2024_table1_children_served.csv (ACF's
preliminary FY 2024 Table 1).

Each scenario changes one input the model reads, so moving from one run to the next
shows what limits a state's total:

- base: the dataset as shipped, with no care hours, days or provider type.
- ft_billed: every child under 13 in a unit with a reported bill gets a full-time
  schedule.
- rate_billed: ft_billed, and each of those units' bill rises to $1,000,000 a year,
  so the program's own rate sets the payment wherever it sits below the charge.
- ft_all and rate_all: the same for every unit with a child under 13.

The mechanism column follows from those runs alone:

- "pays from the file": the base run pays at least $10,000.
- "needs a care schedule": the base run pays nothing, and the full-time schedule
  makes it pay at least $1 million. The program prices care from hours or days,
  which the dataset doesn't carry.
- "capped by small bills": a schedule still leaves the total under $1 million, and
  the large bill lifts it to at least $1 million. The program pays the lesser of
  its rate and the family's bill, and the dataset's bills sit far below its rates.

"Per paid unit under a large bill" divides the rate_billed total by the units it
pays; a figure near $1,000,000 means the program pays the bill with no rate cap.

ACF's direct services count federal and state CCDF spending, including maintenance
of effort and one-time ARP Supplemental Discretionary funds; the last ACF column
removes those ARP funds (Table 4a) from the state's total expenditures.

Every model figure comes from one of the runs; nothing is scaled or interpolated.
"""

import csv
import json
import sys
from pathlib import Path

run_dir, sources, out_csv, out_md = (Path(a) for a in sys.argv[1:5])
SCENARIOS = ["base", "ft-billed", "ft-all", "rate-billed", "rate-all"]
NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}


def number(text):
    text = str(text).replace(",", "").replace("$", "").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


def table(name, key):
    with open(sources / name) as handle:
        return {row[key].strip().upper(): row for row in csv.DictReader(handle)}


runs = {s: json.load(open(run_dir / f"main-{s}.json")) for s in SCENARIOS}
commits = {s: runs[s]["commit"] for s in SCENARIOS}
assert len(set(commits.values())) == 1, commits
assert all(runs[s]["smoke_subsample"] in (None, 0, False) for s in SCENARIOS)
spending = table("ccdf_table3a_fy2024.csv", "State")
funds = table("ccdf_table4a_fy2024.csv", "State")
served = table("ccdf_fy2024_table1_children_served.csv", "state")

records = []
for code, name in NAMES.items():
    key = name.upper()
    rows = {s: runs[s]["rows"][code] for s in SCENARIOS}
    total = {s: rows[s]["subsidy"] / 1e6 for s in SCENARIOS}
    if total["base"] >= 0.01:
        mechanism = "pays from the file"
    elif total["ft-billed"] >= 1:
        mechanism = "needs a care schedule"
    elif total["rate-billed"] >= 1:
        mechanism = "capped by small bills"
    else:
        mechanism = "pays little even with a large bill"
    large = rows["rate-billed"]
    direct = number(spending[key]["Direct  Services"]) / 1e6
    arp = number(funds[key]["Discretionary ARP Supplemental 4/"]) / 1e6
    total_acf = number(spending[key]["Total Expenditures"]) / 1e6
    records.append(
        {
            "state": code,
            "mechanism": mechanism,
            "model_base_m": round(total["base"], 2),
            "model_ft_billed_m": round(total["ft-billed"], 2),
            "model_rate_billed_m": round(total["rate-billed"], 2),
            "model_rate_all_m": round(total["rate-all"], 2),
            "acf_direct_services_m": round(direct, 2),
            "acf_total_less_arp_supplemental_m": round(total_acf - arp, 2),
            "base_over_acf_direct": round(total["base"] / direct, 3) if direct else "",
            "paid_records_base": rows["base"]["records_paid"],
            "units_paid_base": round(rows["base"]["units_paid"]),
            "acf_families": number(served[key]["families"]),
            "bill_per_paid_unit_ft_billed": round(
                rows["ft-billed"]["bill_of_paid_units"]
                / max(rows["ft-billed"]["units_paid"], 1)
            ),
            "per_paid_unit_large_bill": round(
                large["subsidy"] / large["units_paid"] if large["units_paid"] else 0
            ),
        }
    )

with open(out_csv, "w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)

order = ["pays from the file", "needs a care schedule", "capped by small bills"]
national = {s: runs[s]["national"]["child_care_subsidies"] / 1e6 for s in SCENARIOS}
with open(out_md, "w") as handle:
    handle.write(
        f"Runs at commit `{commits['base'][:10]}`, year {runs['base']['year']}, "
        f"dataset `{runs['base']['dataset']}`.\n\n"
        "National totals ($M): "
        + ", ".join(f"{s} {national[s]:,.1f}" for s in SCENARIOS)
        + ".\n\n"
    )
    for mechanism in order + ["pays little even with a large bill"]:
        group = [r for r in records if r["mechanism"] == mechanism]
        if not group:
            continue
        handle.write(f"### {mechanism.capitalize()} ({len(group)})\n\n")
        handle.write(
            "| State | Model, file ($M) | Full-time schedule ($M) | Schedule and large bill ($M) "
            "| ACF direct services ($M) | ACF less ARP supplemental ($M) | Model ÷ ACF direct "
            "| Paid records | Bill per paid unit with a schedule ($) | Per paid unit under a large bill ($) |\n"
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        )
        for r in sorted(group, key=lambda r: -r["model_base_m"] - r["model_ft_billed_m"]):
            handle.write(
                f"| {r['state']} | {r['model_base_m']:,.2f} | {r['model_ft_billed_m']:,.2f} "
                f"| {r['model_rate_billed_m']:,.2f} | {r['acf_direct_services_m']:,.2f} "
                f"| {r['acf_total_less_arp_supplemental_m']:,.2f} | {r['base_over_acf_direct']} "
                f"| {r['paid_records_base']} | {r['bill_per_paid_unit_ft_billed']:,} "
                f"| {r['per_paid_unit_large_bill']:,} |\n"
            )
        handle.write("\n")
print(f"wrote {out_csv} and {out_md}")
