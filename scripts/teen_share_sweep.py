"""Which state child care programs pay toward a teenager's share of the bill?

For each state program in gov.hhs.ccdf.child_care_subsidy_programs, build pairs
of SPM units that differ only in a 15-year-old's child care charge: a parent
earning $20,000 for 40 hours a week, a 3-year-old with a $36,000 annual charge,
and a 15-year-old with no special need whose charge is $0 in one unit and
$12,000 in the other. The unit's bill equals the sum of the two charges in each.
Family size, income and the young child's inputs stay the same, so a program
that pays only for children within CCDF's age limit (45 CFR 98.20(a)(1)) pays
the same in both. Two schedules: the 3-year-old in full-time care (8 hours a
day, 5 days a week, 21 days a month), and no care schedule at all.

Usage: PYTHONPATH=<policyengine-us tree> python teen_share_sweep.py OUT.json YEAR
"""

import json
import sys

from policyengine_us import Simulation
from policyengine_us.system import system

out_path, year = sys.argv[1], int(sys.argv[2])
programs = system.parameters(f"{year}-01-01").gov.hhs.ccdf.child_care_subsidy_programs
states = sorted({name.split("_")[0].upper() for name in programs})

SCHEDULES = {
    "full_time": dict(
        childcare_hours_per_week=40,
        childcare_hours_per_day=8,
        childcare_days_per_week=5,
        childcare_attending_days_per_month=21,
    ),
    "no_schedule": {},
}
TEEN_CHARGES = (0, 12_000)
YOUNG_CHARGE = 36_000

people, tax_units, spm_units, families, marital_units, households = {}, {}, {}, {}, {}, {}
keys = []
for state in states:
    for schedule, care in SCHEDULES.items():
        for teen_charge in TEEN_CHARGES:
            key = f"{state}_{schedule}_{teen_charge}"
            keys.append((state, schedule, teen_charge, key))
            parent, young, teen = f"{key}_parent", f"{key}_young", f"{key}_teen"
            members = [parent, young, teen]
            people[parent] = {
                "age": {year: 30},
                "employment_income": {year: 20_000},
                "weekly_hours_worked": {year: 40},
            }
            people[young] = {
                "age": {year: 3},
                "is_tax_unit_dependent": {year: True},
                "pre_subsidy_childcare_expenses": {year: YOUNG_CHARGE},
                **{name: {year: value} for name, value in care.items()},
            }
            people[teen] = {
                "age": {year: 15},
                "is_tax_unit_dependent": {year: True},
                "pre_subsidy_childcare_expenses": {year: teen_charge},
            }
            tax_units[key] = {"members": members}
            spm_units[key] = {
                "members": members,
                "spm_unit_pre_subsidy_childcare_expenses": {
                    year: YOUNG_CHARGE + teen_charge
                },
            }
            families[key] = {"members": members}
            marital_units[key] = {"members": [parent]}
            households[key] = {"members": members, "state_name": {year: state}}

situation = dict(
    people=people,
    tax_units=tax_units,
    spm_units=spm_units,
    families=families,
    marital_units=marital_units,
    households=households,
)
simulation = Simulation(situation=situation)
unit_index = {key: i for i, key in enumerate(spm_units)}

values = {}
for name in programs:
    state = name.split("_")[0].upper()
    try:
        result = simulation.calculate(name, year)
    except Exception as error:  # report, don't hide, a program that fails
        values[state] = {"error": f"{type(error).__name__}: {error}"[:300]}
        continue
    values[state] = {"variable": name}
    for s, schedule, teen_charge, key in keys:
        if s == state:
            values[state][f"{schedule}_{teen_charge}"] = round(
                float(result[unit_index[key]]), 2
            )

rows = []
for state in states:
    v = values.get(state, {})
    if "error" in v:
        rows.append(dict(state=state, error=v["error"]))
        continue
    row = dict(state=state, variable=v.get("variable"))
    for schedule in SCHEDULES:
        without, with_teen = v.get(f"{schedule}_0"), v.get(f"{schedule}_12000")
        row[f"{schedule}_without_teen_charge"] = without
        row[f"{schedule}_with_teen_charge"] = with_teen
        row[f"{schedule}_difference"] = (
            None if without is None or with_teen is None else round(with_teen - without, 2)
        )
    rows.append(row)

json.dump(dict(year=year, rows=rows), open(out_path, "w"), indent=1)
print(f"{'state':5} {'full-time: without':>18} {'with':>10} {'diff':>9}   {'no schedule: without':>20} {'with':>10} {'diff':>9}")
for r in rows:
    if "error" in r:
        print(f"{r['state']:5} ERROR {r['error'][:100]}")
        continue
    print(
        f"{r['state']:5} {r['full_time_without_teen_charge']:>18,.0f} {r['full_time_with_teen_charge']:>10,.0f} {r['full_time_difference']:>9,.0f}   "
        f"{r['no_schedule_without_teen_charge']:>20,.0f} {r['no_schedule_with_teen_charge']:>10,.0f} {r['no_schedule_difference']:>9,.0f}"
    )
flagged = [r["state"] for r in rows if "error" not in r and (abs(r["full_time_difference"]) > 1 or abs(r["no_schedule_difference"]) > 1)]
print("states whose payment moves with the teenager's charge:", ", ".join(flagged) or "none")
