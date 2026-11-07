"""Compare a branch run of cc_gap.py with its base run, for one state's change.

Usage: python -I compare_impact.py BASE_PREFIX BRANCH_PREFIX STATE [SUBSIDY_VARIABLE]

Each prefix names a pair of files written by cc_gap.py with IMPACT=1: PREFIX.json
and PREFIX.npz. Both runs must use the same dataset, year and scenario. The script
prints the state's subsidy total, every SPM unit whose subsidy changed, the
national totals and poverty rates, and the largest change in any other state.
"""

import json
import sys

import numpy as np


def load(prefix):
    with open(prefix + ".json") as f:
        meta = json.load(f)
    arrays = np.load(prefix + ".npz", allow_pickle=True)
    return meta, arrays


def weighted_by_state(arrays, entity, variable):
    states = arrays[f"{entity}__state"]
    values = arrays[f"{entity}__{variable}"] * arrays[f"{entity}__weight"]
    return {s: float(values[states == s].sum()) for s in np.unique(states)}


def main():
    base_prefix, branch_prefix, state = sys.argv[1:4]
    subsidy = sys.argv[4] if len(sys.argv) > 4 else "child_care_subsidies"
    base_meta, base = load(base_prefix)
    branch_meta, branch = load(branch_prefix)
    for key in ["dataset", "year", "scenario"]:
        if base_meta[key] != branch_meta[key]:
            raise SystemExit(f"{key} differs: {base_meta[key]} vs {branch_meta[key]}")
    for entity in ["spm_unit", "household", "tax_unit"]:
        if not np.array_equal(base[f"{entity}__id"], branch[f"{entity}__id"]):
            raise SystemExit(f"{entity} ids differ between the runs")
        if not np.array_equal(base[f"{entity}__weight"], branch[f"{entity}__weight"]):
            raise SystemExit(f"{entity} weights differ between the runs")
    print(f"base {base_meta['commit'][:10]}  branch {branch_meta['commit'][:10]}")
    print(f"dataset {base_meta['dataset']}  year {base_meta['year']}")

    states = base["spm_unit__state"]
    weight = base["spm_unit__weight"]
    in_state = states == state
    before = base[f"spm_unit__{subsidy}"]
    after = branch[f"spm_unit__{subsidy}"]
    diff = after - before
    print(f"\n{state} {subsidy}: {np.sum(before[in_state] * weight[in_state]):,.2f}"
          f" -> {np.sum(after[in_state] * weight[in_state]):,.2f}"
          f"  change {np.sum(diff[in_state] * weight[in_state]):,.2f}")
    paid_before = in_state & (before > 0)
    paid_after = in_state & (after > 0)
    print(f"records paid: {paid_before.sum()} -> {paid_after.sum()};"
          f" units paid: {weight[paid_before].sum():,.2f} -> {weight[paid_after].sum():,.2f}")
    changed = in_state & (np.abs(diff) > 0.005)
    print(f"records changed: {changed.sum()}, combined weight {weight[changed].sum():,.4f}")
    order = np.argsort(-np.abs(diff * weight) * changed)
    for i in order[: min(int(changed.sum()), 40)]:
        print(f"  spm_unit {base['spm_unit__id'][i]}: weight {weight[i]:,.4f},"
              f" {before[i]:,.2f} -> {after[i]:,.2f} ({diff[i]:+,.2f}),"
              f" bill {base['spm_unit__bill'][i]:,.2f}")

    other = (~in_state) & (np.abs(diff) > 0.005)
    print(f"\nrecords changed in other states: {other.sum()}")

    print("\nnational totals (base -> branch, change):")
    for key, value in base_meta["impact"]["national"].items():
        new = branch_meta["impact"]["national"][key]
        if "rate" in key:
            print(f"  {key}: {value:.6f} -> {new:.6f} ({(new - value) * 100:+.4f} pp)")
        else:
            print(f"  {key}: {value:,.2f} -> {new:,.2f} ({new - value:+,.2f})")

    hh_base = weighted_by_state(base, "household", "household_net_income")
    hh_branch = weighted_by_state(branch, "household", "household_net_income")
    print(f"\n{state} household_net_income: {hh_base[state]:,.2f} -> {hh_branch[state]:,.2f}"
          f" ({hh_branch[state] - hh_base[state]:+,.2f})")
    others = {s: hh_branch[s] - hh_base[s] for s in hh_base if s != state}
    worst = max(others, key=lambda s: abs(others[s]))
    print(f"largest household_net_income change elsewhere: {worst} {others[worst]:+,.2f}")


if __name__ == "__main__":
    main()
