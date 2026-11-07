"""Where the default dataset's child care spending lands by child age in 2026.

pre_subsidy_childcare_expenses splits each SPM unit's reported spending
(spm_unit_pre_subsidy_childcare_expenses) evenly across members under 18. This
script runs that formula on the default dataset and reports, weighted:

- reported spending in units with and without a member under 18;
- the spending the split assigns to children aged 0-5, 6-12 and 13-17;
- units with spending and a child aged 13-17, and children of that age with a share.

Run with PYTHONPATH set to a policyengine-us checkout:
    PYTHONPATH=<checkout> python bill_split_by_age.py OUT.json
"""

import json
import subprocess
import sys

import numpy as np

import policyengine_us
from policyengine_us import Microsimulation
from policyengine_us.system import DEFAULT_DATASET

YEAR = 2026
out_path = sys.argv[1]

sim = Microsimulation()
age = sim.calculate("age", YEAR).values
person_weight = sim.calculate("person_weight", YEAR).values
share = sim.calculate("pre_subsidy_childcare_expenses", YEAR).values
unit_bill = sim.calculate("spm_unit_pre_subsidy_childcare_expenses", YEAR).values
unit_weight = sim.calculate("spm_unit_weight", YEAR).values
under_18 = age < 18
unit_has_child = sim.map_result(under_18.astype(float), "person", "spm_unit", how="sum") > 0
unit_has_teen = (
    sim.map_result(((age >= 13) & (age < 18)).astype(float), "person", "spm_unit", how="sum")
    > 0
)

bands = {"0-5": age < 6, "6-12": (age >= 6) & (age < 13), "13-17": (age >= 13) & (age < 18)}
billed = unit_bill > 0
result = {
    "year": YEAR,
    "dataset": DEFAULT_DATASET,
    "commit": subprocess.run(
        ["git", "-C", policyengine_us.__path__[0], "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    ).stdout.strip(),
    "reported_spending_total": float((unit_bill * unit_weight).sum()),
    "reported_spending_units_with_child": float(
        (unit_bill * unit_weight * unit_has_child).sum()
    ),
    "reported_spending_units_without_child": float(
        (unit_bill * unit_weight * ~unit_has_child).sum()
    ),
    "units_with_spending": float((unit_weight * billed).sum()),
    "units_with_spending_and_teen": float((unit_weight * billed * unit_has_teen).sum()),
    "records_with_spending_and_teen": int((billed & unit_has_teen).sum()),
    "assigned_by_age": {
        name: float((share * person_weight * mask).sum()) for name, mask in bands.items()
    },
    "children_with_share_by_age": {
        name: float((person_weight * mask * (share > 0)).sum())
        for name, mask in bands.items()
    },
}
json.dump(result, open(out_path, "w"), indent=1)
print(json.dumps(result, indent=1))
