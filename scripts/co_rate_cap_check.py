"""Each eligible Colorado child's share of the bill against the county rate.

Under PolicyEngine/policyengine-us#10723, Colorado's counties pay no more than
the county reimbursement rate for each eligible child's care. For each month
of YEAR on the default dataset, this script compares each eligible child's
monthly charges (the child's share of the unit's child care bill and any
after-school expenses) with that child's county rate, in the SPM units the
program finds eligible. It also checks the reimbursement against the uncapped
sum of the eligible children's charges.

Usage: PYTHONPATH=<policyengine-us tree> python co_rate_cap_check.py OUT.json YEAR
"""

import json
import os
import subprocess
import sys

import numpy as np
import policyengine_us
from policyengine_core.periods import period as as_period
from policyengine_us import Microsimulation
from policyengine_us.model_api import add
from policyengine_us.system import DEFAULT_DATASET

out, year = sys.argv[1], int(sys.argv[2])
sim = Microsimulation()
person = sim.populations["person"]
spm_unit = sim.populations["spm_unit"]
annual = as_period(str(year))


def values(population, variable, period):
    return np.asarray(population(variable, period))


county = np.asarray(person.household("county_str", annual)).astype(str)
age = values(person, "age", annual).astype(float)
unit_weight = values(spm_unit, "spm_unit_weight", annual).astype(float)
person_unit_weight = np.asarray(spm_unit.project(unit_weight)).astype(float)

months = {}
closest = None
for m in range(1, 13):
    month = as_period(f"{year}-{m:02d}")
    eligible_child = values(person, "co_ccap_child_eligible", month).astype(bool)
    unit_eligible = values(spm_unit, "co_ccap_eligible", month).astype(bool)
    counted = eligible_child & np.asarray(spm_unit.project(unit_eligible)).astype(bool)
    charge = np.asarray(
        add(
            person,
            month,
            ["pre_subsidy_childcare_expenses", "after_school_expenses"],
        )
    ).astype(float)
    rate = values(person, "co_ccap_maximum_monthly_payment", month).astype(float)
    with_charge = counted & (charge > 0)
    share_of_rate = np.zeros_like(charge)
    np.divide(charge, rate, out=share_of_rate, where=rate > 0)

    reimbursement = values(spm_unit, "co_ccap_reimbursement", month).astype(float)
    uncapped = np.asarray(spm_unit.sum(np.maximum(charge, 0) * eligible_child)).astype(
        float
    )
    gap = np.abs(reimbursement - uncapped)[unit_eligible]

    months[str(month)] = {
        "eligible_units": int(unit_eligible.sum()),
        "eligible_children": int(counted.sum()),
        "children_with_charges": int(with_charge.sum()),
        "children_without_a_rate": int((counted & (rate <= 0)).sum()),
        "children_over_rate": int((with_charge & (charge > rate)).sum()),
        "largest_share_of_rate": (
            float(share_of_rate[with_charge].max()) if with_charge.any() else None
        ),
        "largest_reimbursement_gap": float(gap.max()) if gap.size else 0.0,
    }
    if with_charge.any():
        i = np.flatnonzero(with_charge)[np.argmax(share_of_rate[with_charge])]
        if closest is None or share_of_rate[i] > closest["share_of_rate"]:
            closest = {
                "month": str(month),
                "county": str(county[i]),
                "age": float(age[i]),
                "monthly_charge": float(charge[i]),
                "monthly_rate": float(rate[i]),
                "share_of_rate": float(share_of_rate[i]),
                "spm_unit_weight": float(person_unit_weight[i]),
            }

tree = os.path.dirname(os.path.dirname(policyengine_us.__file__))
commit = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    capture_output=True,
    text=True,
    cwd=tree,
    check=True,
).stdout.strip()
result = {
    "year": year,
    "dataset": DEFAULT_DATASET,
    "commit": commit,
    "months": months,
    "closest": closest,
}
with open(out, "w") as f:
    json.dump(result, f, indent=1)
    f.write("\n")

print(f"Colorado CCAP county rate check, {year}, commit {commit[:10]}")
print(
    f"{'month':>7}  {'units':>5}  {'children':>8}  {'charged':>7}  {'over':>4}  {'largest share':>13}"
)
for label, row in months.items():
    share = row["largest_share_of_rate"]
    shown = "-" if share is None else f"{share:.1%}"
    print(
        f"{label:>7}  {row['eligible_units']:>5}  {row['eligible_children']:>8}  "
        f"{row['children_with_charges']:>7}  {row['children_over_rate']:>4}  {shown:>13}"
    )
if closest:
    print(
        f"closest: {closest['month']}, {closest['county']}, age {closest['age']:.0f}, "
        f"${closest['monthly_charge']:,.2f} a month against ${closest['monthly_rate']:,.2f}"
    )
