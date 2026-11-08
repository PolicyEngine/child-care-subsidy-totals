"""How do care hours change Colorado's Child Care Assistance Program parent fee?

Builds Colorado SPM units with a parent earning $40,000 a year and one or two
children under 13, each with a $1,000 monthly share of the child care bill, and
prints the parent fee and subsidy for January 2026 with no hours of care
recorded, with 3 hours a day and with 8 hours a day for every child.

Usage: PYTHONPATH=<policyengine-us tree> python co_parent_fee_hours.py
"""

from policyengine_us import Simulation

MONTH = "2026-01"
INCOME = 40_000
VARIABLES = [
    "co_ccap_base_parent_fee",
    "co_ccap_add_on_parent_fee",
    "co_ccap_parent_fee",
    "co_ccap_subsidy",
]


def run(n_children, hours):
    people = {"parent": {"age": {"2026": 30}, "employment_income": {"2026": INCOME}}}
    for i in range(n_children):
        child = {"age": {"2026": 3 + 2 * i}}
        if hours is not None:
            child["childcare_hours_per_day"] = {"2026": hours}
        people[f"child{i}"] = child
    members = list(people)
    situation = {
        "people": people,
        "spm_units": {
            "spm": {
                "members": members,
                "spm_unit_pre_subsidy_childcare_expenses": {"2026": 12_000 * n_children},
            }
        },
        "tax_units": {"tu": {"members": members}},
        "families": {"f": {"members": members}},
        "households": {"h": {"members": members, "state_code": {"2026": "CO"}}},
    }
    sim = Simulation(situation=situation)
    return [float(sim.calculate(v, MONTH)[0]) for v in VARIABLES]


print(f"Colorado CCAP, {MONTH}: parent earning ${INCOME:,} a year, $1,000 a month of the bill for each child")
print(f"{'children':>8}  {'hours a day':>11}  {'base fee':>9}  {'add-on':>7}  {'parent fee':>10}  {'subsidy':>9}")
for n_children in (1, 2):
    for hours in (None, 3, 8):
        base, add_on, fee, subsidy = run(n_children, hours)
        label = "none" if hours is None else str(hours)
        print(f"{n_children:>8}  {label:>11}  {base:>9,.2f}  {add_on:>7,.2f}  {fee:>10,.2f}  {subsidy:>9,.2f}")
