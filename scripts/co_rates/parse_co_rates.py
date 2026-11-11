"""Parse Colorado CCCAP rate sources and cross-check them.

Sources (under SRC_DIR, as scripts/co_rates/download_co_rates.sh leaves them):
- raw/rates_eff_2024-10-01.txt, raw/rates_eff_2025-10-01.txt: CDEC's
  State-Established Daily Licensed Provider Reimbursement Rates (pdftotext
  -layout of the PDFs linked from cdec.colorado.gov).
- county_plans/*.txt and county_plans/hist/*.txt: each county's CHATS County
  Rate Plan (pdftotext -layout), from CDEC's "View County CCCAP Policies and
  Rate Plan" Drive folder and its "Historical County Rate Plans" subfolders.

Usage: python -I parse_co_rates.py SRC_DIR OUT.json

Checks (each raises on failure):
1. Each state table has 64 counties x 21 rows, one value per cell.
2. In every county plan, the licensed Regular full-time rates equal the state
   table in force on the plan's effective date (10/1/2024 table before
   10/1/2025, 10/1/2025 table after), sub-bands inside one state band agree,
   Tier 1 equals Tier 2 and Tier 4 equals Tier 5.
3. In every plan, each Regular row's part-time rate is 55% of full time,
   FT/PT is 155% and FT/FT is 200%, rounded half up to the cent.
"""

import json
import re
import sys
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

STATE_TABLES = {
    "2024-10-01": "raw/rates_eff_2024-10-01.txt",
    "2025-10-01": "raw/rates_eff_2025-10-01.txt",
}

AGE_KEYS = {
    ("CENTER", "0-18 months"): "MONTHS_0_TO_18",
    ("CENTER", "18-36 months"): "MONTHS_18_TO_36",
    ("CENTER", "36 months to 6 years"): "MONTHS_36_TO_YEARS_6",
    ("CENTER", "School Age"): "SCHOOL_AGE",
    ("HOME", "0-24 months"): "MONTHS_0_TO_24",
    ("HOME", "24 months to 6 years"): "MONTHS_24_TO_YEARS_6",
    ("HOME", "School Age"): "SCHOOL_AGE",
}
TIER_KEYS = {
    "Tier 1 & Tier 2": "TIER_1_2",
    "Tier 3": "TIER_3",
    "Tier 4 & Tier 5": "TIER_4_5",
}
# A county plan's CHATS sub-bands, mapped to the state table's bands.
PLAN_BANDS = {
    "CENTER": {
        "0-6 Months": "MONTHS_0_TO_18",
        "06-12 Months": "MONTHS_0_TO_18",
        "12-18 Months": "MONTHS_0_TO_18",
        "18-24 Months": "MONTHS_18_TO_36",
        "24-30 Months": "MONTHS_18_TO_36",
        "30-36 Months": "MONTHS_18_TO_36",
        "36 - School Age": "MONTHS_36_TO_YEARS_6",
        "School Age": "SCHOOL_AGE",
    },
    "HOME": {
        "0-6 Months": "MONTHS_0_TO_24",
        "06-12 Months": "MONTHS_0_TO_24",
        "12-18 Months": "MONTHS_0_TO_24",
        "18-24 Months": "MONTHS_0_TO_24",
        "24-30 Months": "MONTHS_24_TO_YEARS_6",
        "30-36 Months": "MONTHS_24_TO_YEARS_6",
        "36 - School Age": "MONTHS_24_TO_YEARS_6",
        "School Age": "SCHOOL_AGE",
    },
}
PLAN_TIER = {1: "TIER_1_2", 2: "TIER_1_2", 3: "TIER_3", 4: "TIER_4_5", 5: "TIER_4_5"}

CENT = Decimal("0.01")


def round_cents(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def county_key(name: str) -> str:
    return re.sub(r"[^A-Z]+", "_", name.strip().upper()).strip("_") + "_COUNTY_CO"


STATE_ROW = re.compile(
    r"^\s*(?P<county>[A-Za-z][A-Za-z .]*?)\s+(?P<ptype>CENTER|HOME)\s+"
    r"(?P<age>0-18 months|18-36 months|36 months to 6 years|School Age|"
    r"0-24 months|24 months to 6 years)\s+"
    r"(?P<tier>Tier 1 & Tier 2|Tier 3|Tier 4 & Tier 5)\s+\$\s*(?P<amt>[\d,]+\.\d{2})\s*$"
)


def parse_state_table(path: Path) -> dict:
    table = {}
    for line in path.read_text().splitlines():
        m = STATE_ROW.match(line)
        if not m:
            continue
        key = (
            county_key(m["county"]),
            m["ptype"],
            AGE_KEYS[(m["ptype"], m["age"])],
            TIER_KEYS[m["tier"]],
        )
        assert key not in table, f"duplicate {key} in {path.name}"
        table[key] = Decimal(m["amt"].replace(",", ""))
    counties = {k[0] for k in table}
    assert len(counties) == 64, (path.name, len(counties))
    assert len(table) == 64 * 21, (path.name, len(table))
    return table


PAIR = r"(FT|FTFT|FTPT|PT)\s+([\d,]+\.\d{2})"
PLAN_ROW = re.compile(r"^(?P<label>.*?)\s*(?P<pairs>(?:(?:FT|FTFT|FTPT|PT)\s+[\d,]+\.\d{2}\s*){5})$")
EXEMPT_ROW = re.compile(
    r"^\s*(?P<rate>[A-Za-z][A-Za-z ]*?)\s+(?P<age>[<>]5 Years)\s+"
    r"(?P<pt>[\d,]+\.\d{2})\s+(?P<ft>[\d,]+\.\d{2})\s+(?P<ftpt>[\d,]+\.\d{2})\s+(?P<ftft>[\d,]+\.\d{2})\s*$"
)
SECTION = re.compile(r"County Ceiling Rates: Provider Type \((Exempt|Home|Center)\)")


def parse_plan(path: Path) -> dict:
    text = path.read_text()
    m = re.search(r"County Rate Plan - (.+?)\s*\n", text)
    county = county_key(m.group(1))
    m = re.search(r"Effective Begin Date\s*:\s*(\d{1,2})/(\d{1,2})/(\d{4})", text)
    effective = f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    sections = defaultdict(list)
    current = None
    for line in text.splitlines():
        s = SECTION.search(line)
        if s:
            current = s.group(1)
            continue
        if current:
            sections[current].append(line)
    exempt = {}
    for line in sections["Exempt"]:
        e = EXEMPT_ROW.match(line)
        if e:
            exempt[(e["rate"].strip(), e["age"])] = {
                k: Decimal(e[k].replace(",", "")) for k in ("pt", "ft", "ftpt", "ftft")
            }
    licensed = {}
    for ptype, name in (("HOME", "Home"), ("CENTER", "Center")):
        blocks = []
        block = None
        for line in sections[name]:
            r = PLAN_ROW.match(line)
            if r:
                pairs = re.findall(PAIR, r["pairs"])
                units = {u for u, _ in pairs}
                assert len(units) == 1, (path.name, line)
                unit = pairs[0][0]
                amounts = [Decimal(a.replace(",", "")) for _, a in pairs]
                if unit == "FT":
                    block = {"label": [], "FT": amounts}
                    blocks.append(block)
                else:
                    block[unit] = amounts
                if r["label"].strip():
                    block["label"].append(r["label"].strip())
            elif block is not None and line.strip() and not re.search(
                r"Page \d+ of \d+|Rate Type|Tier 1|Care Unit|Age Group|^\s*Group\s*$", line
            ):
                block["label"].append(line.strip())
        for b in blocks:
            label = " ".join(b["label"])
            label = re.sub(r"\s+", " ", label)
            licensed[(ptype, label)] = b
    return {"county": county, "effective": effective, "exempt": exempt, "licensed": licensed, "file": str(path)}


def check_units(plan: dict, problems: list):
    for (ptype, label), b in plan["licensed"].items():
        if not label.startswith("Regular"):
            continue
        for i, ft in enumerate(b["FT"]):
            want = {
                "PT": round_cents(ft * Decimal("0.55")),
                "FTPT": round_cents(ft * Decimal("1.55")),
                "FTFT": ft * 2,
            }
            for unit, value in want.items():
                if b.get(unit) is None or b[unit][i] != value:
                    problems.append(
                        f"{Path(plan['file']).name} {ptype} {label} tier {i+1} {unit}: {b.get(unit, [None]*5)[i]} != {value}"
                    )
    for (rate, age), v in plan["exempt"].items():
        if rate != "Regular":
            continue
        want = {
            "pt": round_cents(v["ft"] * Decimal("0.55")),
            "ftpt": round_cents(v["ft"] * Decimal("1.55")),
            "ftft": v["ft"] * 2,
        }
        for unit, value in want.items():
            if v[unit] != value:
                problems.append(f"{Path(plan['file']).name} EXEMPT {age} {unit}: {v[unit]} != {value}")


def regular_ft(plan: dict) -> dict:
    """The plan's licensed Regular full-time rates, keyed like the state table."""
    out = {}
    for (ptype, label), b in plan["licensed"].items():
        if not label.startswith("Regular "):
            continue
        band = label[len("Regular "):]
        state_band = PLAN_BANDS[ptype].get(band)
        assert state_band, (plan["file"], ptype, label)
        for tier_number, value in enumerate(b["FT"], start=1):
            key = (plan["county"], ptype, state_band, PLAN_TIER[tier_number])
            out.setdefault(key, set()).add(value)
    return out


def main(src_dir: str, out_path: str):
    base = Path(src_dir)
    tables = {date: parse_state_table(base / path) for date, path in STATE_TABLES.items()}
    plan_files = sorted((base / "county_plans").glob("*.txt")) + sorted(
        (base / "county_plans/hist").glob("*.txt")
    )
    plans = [parse_plan(p) for p in plan_files]
    problems = []
    checked = 0
    for plan in plans:
        check_units(plan, problems)
        if plan["effective"] < "2024-10-01":
            continue
        table = tables["2025-10-01" if plan["effective"] >= "2025-10-01" else "2024-10-01"]
        ft = regular_ft(plan)
        keys = {k for k in table if k[0] == plan["county"]}
        if set(ft) != keys:
            problems.append(f"{Path(plan['file']).name}: plan keys differ from the state table")
        for key in keys:
            values = ft.get(key, set())
            if values != {table[key]}:
                problems.append(f"{Path(plan['file']).name} {key}: plan {sorted(values)} vs state {table[key]}")
            checked += 1
    # Qualified exempt Regular full-time rates by county and effective date.
    exempt = defaultdict(dict)
    for plan in plans:
        reg = {age: v["ft"] for (rate, age), v in plan["exempt"].items() if rate == "Regular"}
        if set(reg) != {"<5 Years", ">5 Years"}:
            problems.append(f"{Path(plan['file']).name}: exempt Regular rows {sorted(reg)}")
            continue
        prior = exempt[plan["county"]].get(plan["effective"])
        entry = {"UNDER_5": str(reg["<5 Years"]), "AGE_5_AND_OVER": str(reg[">5 Years"]), "file": Path(plan["file"]).name}
        if prior and (prior["UNDER_5"], prior["AGE_5_AND_OVER"]) != (entry["UNDER_5"], entry["AGE_5_AND_OVER"]):
            problems.append(f"{plan['county']} {plan['effective']}: two plans disagree on exempt rates: {prior} vs {entry}")
        exempt[plan["county"]][plan["effective"]] = entry
    result = {
        "state": {
            date: {"|".join(k): str(v) for k, v in sorted(t.items())} for date, t in tables.items()
        },
        "exempt": {c: dict(sorted(v.items())) for c, v in sorted(exempt.items())},
        "plans_checked": len(plans),
        "licensed_cells_checked": checked,
        "problems": problems,
    }
    Path(out_path).write_text(json.dumps(result, indent=1))
    print(f"plans parsed: {len(plans)}; licensed cells checked against the state tables: {checked}")
    print(f"problems: {len(problems)}")
    for p in problems[:60]:
        print("  ", p)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
