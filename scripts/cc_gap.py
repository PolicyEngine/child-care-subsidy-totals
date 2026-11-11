"""Child care subsidies by program on the default dataset, with the inputs
that drive each program's total.

Usage: PYTHONPATH=<tree> python cc_gap.py OUT.json YEAR SCENARIO

SCENARIO
  base       the dataset as shipped (no care hours, days or provider type)
  ft_billed  every child under 13 in a unit with a reported bill gets a
             full-time schedule: 8 hours a day, 5 days a week, 21 days a month
             (the sensitivity PolicyEngine/policyengine-us#10569 used)
  ft_all     every child under 13 gets that schedule, bill or not
  rate_billed  ft_billed, and each of those units' bill rises to LARGE_BILL, so
             the program's rate sets the payment wherever the rate sits below
             the charge
  rate_all   ft_all, and every unit with a child under 13 gets LARGE_BILL

The rate_ scenarios test what the reported bill does. They raise an input the
whole model reads, so a program whose eligibility follows SNAP or TANF can see
those programs move; compare records_eligible_jan with the ft_ runs.

Every figure comes from this run of the model; nothing is scaled from
another run.
"""

import json
import os
import subprocess
import sys
import time

import numpy as np
import pandas as pd

from policyengine_us import Microsimulation
from policyengine_us.system import DEFAULT_DATASET

out, year, scenario = sys.argv[1], int(sys.argv[2]), sys.argv[3]
assert scenario in ("base", "ft_billed", "ft_all", "rate_billed", "rate_all"), scenario
LARGE_BILL = 1_000_000.0
started = time.time()
sim = Microsimulation()
if os.environ.get("SMOKE"):
    sim = sim.subsample(n=int(os.environ["SMOKE"]), seed=0)
tbs = sim.tax_benefit_system


def arr(variable, period=year, map_to=None):
    if map_to is None:
        return np.asarray(sim.calculate(variable, period).values)
    return np.asarray(sim.calculate(variable, period, map_to=map_to).values)


unit_ids = arr("spm_unit_id")
person_unit = arr("spm_unit_id", map_to="person")
pos = pd.Index(unit_ids).get_indexer(person_unit)
assert (pos >= 0).all()
age = arr("age", map_to="person")
bill = arr("spm_unit_pre_subsidy_childcare_expenses").astype(float)

kid13 = age < 13
if scenario != "base":
    in_care = kid13.copy()
    if scenario in ("ft_billed", "rate_billed"):
        in_care &= bill[pos] > 0
    sim.set_input("childcare_days_per_week", year, np.where(in_care, 5.0, 0.0))
    sim.set_input("childcare_hours_per_day", year, np.where(in_care, 8.0, 0.0))
    sim.set_input(
        "childcare_attending_days_per_month", year, np.where(in_care, 21, 0)
    )
    if scenario.startswith("rate_"):
        unit_in_care = (
            np.bincount(pos, weights=in_care.astype(float), minlength=len(unit_ids)) > 0
        )
        sim.set_input(
            "spm_unit_pre_subsidy_childcare_expenses",
            year,
            np.where(unit_in_care, LARGE_BILL, bill),
        )
        raised = arr("spm_unit_pre_subsidy_childcare_expenses").astype(float)
        assert np.array_equal(raised, np.where(unit_in_care, LARGE_BILL, bill))
        weekly = (
            arr("pre_subsidy_childcare_expenses", map_to="person").astype(float)[in_care]
            / 52
        )
        print(f"lowest weekly charge among children in care: {weekly.min():,.0f}")

weight = arr("spm_unit_weight").astype(float)
person_state = arr("state_code_str", map_to="person").astype(str)
state = (
    pd.Series(person_state).groupby(person_unit).first().reindex(unit_ids).values
)
household_id_person = arr("household_id", map_to="person")
household_weight_person = arr("household_weight", map_to="person").astype(float)


def unit_sum(person_values):
    return np.bincount(pos, weights=person_values, minlength=len(unit_ids))


kids_in_unit = unit_sum(kid13.astype(float))
kids_under6_in_unit = unit_sum((age < 6).astype(float))

programs = list(
    tbs.parameters(f"{year}-01-01").gov.hhs.ccdf.child_care_subsidy_programs
)


def eligibility_variables(variable_name):
    """The variables named in defined_for along each program's adds chain."""
    found = []
    variable = tbs.variables[variable_name]
    adds = variable.adds or []
    if isinstance(adds, str):
        adds = list(tbs.parameters(f"{year}-01-01").get_child(adds))
    for component in adds:
        if component not in tbs.variables:
            continue
        defined_for = tbs.variables[component].defined_for
        name = getattr(defined_for, "name", defined_for)
        candidates = [name, f"{component}_eligible", f"{component}_eligible_child"]
        for candidate in candidates:
            # in_state.py defines a boolean variable per state code ("NY" is
            # "In NY"), which says nothing about eligibility.
            if (
                isinstance(candidate, str)
                and not (len(candidate) == 2 and candidate.isupper())
                and candidate in tbs.variables
                and (
                    tbs.variables[candidate].value_type is bool
                    or "eligible" in candidate
                )
            ):
                found.append(candidate)
                break
    return found


def unit_flag(variable_name):
    """Whether any member (or the unit) is flagged, in January for monthly
    variables."""
    variable = tbs.variables[variable_name]
    period = f"{year}-01" if variable.definition_period == "month" else year
    values = np.asarray(sim.calculate(variable_name, period).values)
    entity = variable.entity.key
    if entity == "spm_unit":
        return values.astype(bool)
    if entity == "person":
        return unit_sum(values.astype(float)) > 0
    mapped = np.asarray(
        sim.calculate(variable_name, period, map_to="person").values
    ).astype(float)
    return unit_sum(mapped) > 0


rows = {}
total = np.zeros(len(unit_ids))
for program in programs:
    values = arr(program).astype(float)
    total += values
    code = program[:2].upper()
    here = state == code
    elig_names = eligibility_variables(program)
    eligible = np.zeros(len(unit_ids), bool)
    for name in elig_names:
        eligible |= unit_flag(name)
    paid = values > 0
    amounts = np.sort((values * weight)[paid])[::-1]
    rows[code] = {
        "top1_share": float(amounts[0] / amounts.sum()) if amounts.sum() > 0 else None,
        "top3_share": float(amounts[:3].sum() / amounts.sum())
        if amounts.sum() > 0
        else None,
        "effective_paid_records": float(amounts.sum() ** 2 / (amounts**2).sum())
        if amounts.sum() > 0
        else 0.0,
        "program": program,
        "eligibility_variables": elig_names,
        "subsidy": float((values * weight).sum()),
        "subsidy_outside_state": float((values * weight)[~here].sum()),
        "records_paid": int(paid.sum()),
        "units_paid": float(weight[paid].sum()),
        "units_eligible_jan": float(weight[eligible & here].sum()),
        "records_eligible_jan": int((eligible & here).sum()),
        "units_eligible_jan_with_bill": float(
            weight[eligible & here & (bill > 0)].sum()
        ),
        "units_with_kid13": float(weight[here & (kids_in_unit > 0)].sum()),
        "kids13": float((weight * kids_in_unit)[here].sum()),
        "kids_under6": float((weight * kids_under6_in_unit)[here].sum()),
        "units_with_bill": float(weight[here & (bill > 0)].sum()),
        "records_with_bill": int((here & (bill > 0)).sum()),
        "units_with_kid13_and_bill": float(
            weight[here & (bill > 0) & (kids_in_unit > 0)].sum()
        ),
        "bill_total": float((bill * weight)[here].sum()),
        "subsidy_with_bill": float((values * weight)[paid & (bill > 0)].sum()),
        "subsidy_no_bill": float((values * weight)[paid & (bill <= 0)].sum()),
        "subsidy_above_bill": float(
            (np.maximum(values - np.maximum(bill, 0), 0) * weight)[paid].sum()
        ),
        "bill_of_paid_units": float((bill * weight)[paid].sum()),
    }

aggregate = arr("child_care_subsidies").astype(float)
household = arr("household_child_care_subsidies").astype(float)
out_of_pocket = arr("childcare_expenses").astype(float)
assert np.allclose(aggregate, total), "aggregate differs from the program sum"

for code, row in rows.items():
    here = state == code
    households = np.unique(household_id_person[np.isin(person_state, [code])])
    hw = (
        pd.Series(household_weight_person, index=household_id_person)
        .groupby(level=0)
        .first()
        .reindex(households)
        .values
    )
    row["household_records"] = int(len(households))
    row["effective_households"] = float(hw.sum() ** 2 / (hw**2).sum())
    row["household_counted"] = float((household * weight)[here].sum())
    row["childcare_expenses_after_subsidy"] = float(
        (out_of_pocket * weight)[here].sum()
    )

impact = None
if os.environ.get("IMPACT"):
    VARIABLES = {
        "spm_unit": [
            "child_care_subsidies",
            "household_child_care_subsidies",
            "childcare_expenses",
            "spm_unit_capped_work_childcare_expenses",
            "spm_unit_benefits",
            "spm_unit_net_income",
            "snap",
            "tanf",
            "vt_ccfap",
            "vt_ccfap_family_benefit",
            "vt_child_care_subsidies",
        ],
        "household": [
            "household_benefits",
            "household_state_benefits",
            "household_tax",
            "household_net_income",
        ],
        "tax_unit": [
            "tax_unit_childcare_expenses",
            "cdcc",
            "income_tax",
            "vt_income_tax",
            "state_income_tax",
            "co_low_income_cdcc",
        ],
    }
    impact = {"national": {}, "VT": {}}
    arrays = {}
    for entity, variables in VARIABLES.items():
        ids = arr(f"{entity}_id")
        entity_of_person = arr(f"{entity}_id", map_to="person")
        entity_state = (
            pd.Series(person_state).groupby(entity_of_person).first().reindex(ids).values
        )
        entity_weight = arr(f"{entity}_weight").astype(float)
        for variable in variables:
            if variable not in tbs.variables:
                continue
            values = arr(variable).astype(float)
            assert tbs.variables[variable].entity.key == entity, variable
            impact["national"][variable] = float((values * entity_weight).sum())
            impact["VT"][variable] = float(
                (values * entity_weight)[entity_state == "VT"].sum()
            )
            arrays[f"{entity}__{variable}"] = values
        arrays[f"{entity}__id"] = ids
        arrays[f"{entity}__state"] = entity_state.astype(str)
        arrays[f"{entity}__weight"] = entity_weight
    person_weight = arr("person_weight").astype(float)
    poor = arr("spm_unit_is_in_spm_poverty", map_to="person").astype(float)
    deep = arr("spm_unit_is_in_deep_spm_poverty", map_to="person").astype(float)
    for label, mask in {
        "national": np.ones_like(person_weight, bool),
        "VT": person_state == "VT",
    }.items():
        for group, members in {
            "all": mask,
            "children": mask & (age < 18),
        }.items():
            impact[label][f"spm_poverty_rate_{group}"] = float(
                np.average(poor[members], weights=person_weight[members])
            )
            impact[label][f"deep_spm_poverty_rate_{group}"] = float(
                np.average(deep[members], weights=person_weight[members])
            )
    arrays["spm_unit__bill"] = bill
    np.savez_compressed(out.removesuffix(".json") + ".npz", **arrays)

import policyengine_us

tree = os.path.dirname(os.path.dirname(policyengine_us.__file__))
commit = subprocess.run(
    ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=tree
).stdout.strip()
result = {
    "year": year,
    "scenario": scenario,
    "dataset": DEFAULT_DATASET,
    "smoke_subsample": os.environ.get("SMOKE"),
    "commit": commit,
    "seconds": round(time.time() - started, 1),
    "impact": impact,
    "national": {
        "child_care_subsidies": float((aggregate * weight).sum()),
        "household_child_care_subsidies": float((household * weight).sum()),
        "childcare_expenses": float((out_of_pocket * weight).sum()),
        "bill": float((bill * weight).sum()),
        "units_with_bill": float(weight[bill > 0].sum()),
        "records_with_bill": int((bill > 0).sum()),
        "records": int(len(unit_ids)),
    },
    "rows": rows,
}
json.dump(result, open(out, "w"), indent=1)
print(
    f"{scenario} {year}: child_care_subsidies "
    f"{result['national']['child_care_subsidies'] / 1e6:,.2f}M in "
    f"{result['seconds']:.0f}s"
)
for code, row in sorted(rows.items(), key=lambda kv: -kv[1]["subsidy"]):
    print(
        f"{code} {row['subsidy'] / 1e6:10.2f}M paid {row['records_paid']:4d} "
        f"elig {row['records_eligible_jan']:4d} bill-recs {row['records_with_bill']:4d} "
        f"no-bill {row['subsidy_no_bill'] / 1e6:8.2f}M "
        f"above {row['subsidy_above_bill'] / 1e6:8.2f}M "
        f"eff {row['effective_households']:6.1f}"
    )
