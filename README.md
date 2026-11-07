# Child care subsidy totals

We compare PolicyEngine US's 2026 state child care subsidy totals with what each state spent from the Child Care and Development Fund (CCDF) in fiscal year 2024. [`REPORT.md`](REPORT.md) gives the findings and the pull requests that follow from them.

## Contents

| Path | What it holds |
|---|---|
| `REPORT.md` | The comparison, state by state, and what drives each gap |
| `results/state_mechanisms.csv` and `.md` | One row per state, with the model's totals under each scenario, ACF's spending and caseloads, and the records and units the model pays |
| `results/scenarios/` | National and state outputs of the five scenario runs on `main` |
| `results/fixes/` | Runs of the Colorado, North Carolina and New Hampshire pull requests and of the `main` commit they branch from |
| `results/bill_split_by_age.json` | Where the dataset's child care spending lands by child age |
| `results/vermont/` | Two-child Vermont cases before and after PolicyEngine/policyengine-us#10694 |
| `data/acf/` | The three ACF tables the comparison reads |
| `scripts/` | The scripts that produce every file above |
| `sources.md` | Each source's address, retrieval date and SHA-256 hash, and the model commits and dataset revision |

## Reproduce

Each scenario run loads the default dataset, Populace US 2024, from Hugging Face and takes about nine minutes. Check out PolicyEngine US at the commit a result file names, then point `PYTHONPATH` at that checkout:

```bash
git clone https://github.com/PolicyEngine/policyengine-us ../policyengine-us
git -C ../policyengine-us checkout e53b426082cd8953b30d8ede8b944f2d5f7246be
uv venv ../policyengine-us/.venv
uv pip install --python ../policyengine-us/.venv/bin/python -e ../policyengine-us openpyxl
```

Run the five scenarios and classify the states:

```bash
for s in base ft_billed ft_all rate_billed rate_all; do
  PYTHONPATH=../policyengine-us ../policyengine-us/.venv/bin/python scripts/cc_gap.py "results/scenarios/main-${s//_/-}.json" 2026 "$s"
done
../policyengine-us/.venv/bin/python -I scripts/classify_states.py results/scenarios data/acf results/state_mechanisms.csv results/state_mechanisms.md
```

For a pull request's impact, fetch its head with `git -C ../policyengine-us fetch origin pull/<number>/head`, and run the base commit and the head with `IMPACT=1`, which also writes record-level `.npz` files beside the JSON:

```bash
git -C ../policyengine-us checkout 040fe5686c956dfce960f7c55fa263687a5bf669
IMPACT=1 PYTHONPATH=../policyengine-us ../policyengine-us/.venv/bin/python scripts/cc_gap.py results/fixes/base-040fe5686c.json 2026 base
git -C ../policyengine-us fetch origin pull/10690/head
git -C ../policyengine-us checkout 6e93ee2a214b108c4a01cdee3a195410b566b343
IMPACT=1 PYTHONPATH=../policyengine-us ../policyengine-us/.venv/bin/python scripts/cc_gap.py results/fixes/co-6e93ee2a21.json 2026 base
../policyengine-us/.venv/bin/python -I scripts/compare_impact.py results/fixes/base-040fe5686c results/fixes/co-6e93ee2a21 CO
```

At commit `378827969c5146731eb7f60e75e9e8f293e33460`, from PolicyEngine/policyengine-us#10678, `scripts/bill_split_by_age.py results/bill_split_by_age.json` writes the split by age, and `scripts/vt_multi_child_cases.py` prints the Vermont cases. Run both with the same `PYTHONPATH`.

`scripts/download_sources.sh` fetches ACF's two workbooks, checks their hashes and rebuilds `data/acf/`.
