"""Vermont CCFAP families with two children, run on the model at a checkout.

Each case gives each child's weekly tuition (or one SPM-unit bill), the weekly
family share and, for each child, the provider type and weekly care hours. It
prints the model's weekly state payment, the family's remaining expense and the
subsidy counted in household benefits, with each child's state rate.

Run with PYTHONPATH set to a policyengine-us checkout:
    PYTHONPATH=<checkout> python vt_multi_child_cases.py
"""

import subprocess
import sys

from policyengine_us import Simulation

YEAR = 2026
WEEKS = 52

CASES = {
    # Two children at licensed centers, each with its own tuition.
    "S2": dict(
        share=200,
        children={
            "infant": dict(age=0, tuition=360, hours=35),
            "preschooler": dict(age=3, tuition=325, hours=35),
        },
    ),
    "S2b": dict(
        share=300,
        children={
            "infant": dict(age=0, tuition=600, hours=35),
            "preschooler": dict(age=3, tuition=200, hours=35),
        },
    ),
    # A 13-year-old is past the program's age limit.
    "S3": dict(
        share=50,
        children={
            "preschooler": dict(age=3, tuition=250, hours=35),
            "teen": dict(age=13, tuition=200, hours=35),
        },
    ),
    # One bill for the whole SPM unit, and only the 3-year-old in care.
    "S3b": dict(
        share=300,
        spm_bill=350,
        children={
            "preschooler": dict(age=3, hours=35),
            "school_age": dict(age=10, hours=0),
        },
    ),
}


def run(case):
    members = ["parent", *case["children"]]
    people = {"parent": {"age": {YEAR: 30}}}
    for name, child in case["children"].items():
        person = {
            "age": {YEAR: child["age"]},
            "is_tax_unit_dependent": {YEAR: True},
            "vt_ccfap_provider_type": {YEAR: "LICENSED_CENTER"},
            "childcare_days_per_week": {YEAR: 5 if child["hours"] else 0},
            "childcare_hours_per_day": {YEAR: child["hours"] / 5},
        }
        if "tuition" in child:
            person["pre_subsidy_childcare_expenses"] = {YEAR: child["tuition"] * WEEKS}
        people[name] = person
    spm_unit = {
        "members": members,
        "vt_ccfap_eligible": {YEAR: True},
        "vt_ccfap_family_share": {YEAR: case["share"] * WEEKS},
    }
    if "spm_bill" in case:
        spm_unit["spm_unit_pre_subsidy_childcare_expenses"] = {
            YEAR: case["spm_bill"] * WEEKS
        }
    situation = {
        "people": people,
        "tax_units": {"tax_unit": {"members": members}},
        "spm_units": {"spm_unit": spm_unit},
        "families": {"family": {"members": members}},
        "marital_units": {"marital_unit": {"members": ["parent"]}},
        "households": {"household": {"members": members, "state_name": {YEAR: "VT"}}},
    }
    simulation = Simulation(situation=situation)
    weekly = {
        name: float(simulation.calculate(name, YEAR)[0]) / WEEKS
        for name in (
            "child_care_subsidies",
            "childcare_expenses",
            "household_child_care_subsidies",
        )
    }
    month = f"{YEAR}-01"
    rates = simulation.calculate("vt_ccfap_state_rate", month)
    bills = simulation.calculate("pre_subsidy_childcare_expenses", YEAR) / WEEKS
    eligible = simulation.calculate("vt_ccfap_eligible_child", month)
    return weekly, list(zip(members, rates, bills, eligible))


if __name__ == "__main__":
    import policyengine_us

    root = policyengine_us.__file__.rsplit("/policyengine_us/", 1)[0]
    head = subprocess.run(
        ["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    print(f"policyengine_us at {head}")
    for label in sys.argv[1:] or CASES:
        weekly, people = run(CASES[label])
        print(
            f"{label}: state pays {weekly['child_care_subsidies']:.2f}, family owes "
            f"{weekly['childcare_expenses']:.2f}, counted "
            f"{weekly['household_child_care_subsidies']:.2f} a week"
        )
        for name, rate, bill, eligible in people:
            print(
                f"    {name}: state rate {rate:.2f}, weekly bill {bill:.2f}, "
                f"eligible child {bool(eligible)}"
            )
