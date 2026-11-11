"""Write Colorado CCCAP rate parameters from parse_co_rates.py's output.

Usage: python -I gen_co_rate_params.py PARSED.json PE_TREE

Writes, under PE_TREE/policyengine_us/parameters/gov/states/co/ccap/rates/:
- licensed_center.yaml and licensed_home.yaml: the state-established Regular
  full-time daily rates, by county, age band and quality tier, from the tables
  effective October 1, 2024 and October 1, 2025.
- qualified_exempt.yaml: each county's Regular full-time daily rate for
  qualified exempt providers, by age band, from its county rate plans,
  starting October 1, 2024 and listing a date only when a plan changed it.
"""

import json
import sys
from decimal import Decimal
from pathlib import Path

SOS = "https://www.sos.state.co.us/CCR/GenerateRulePdf.do?ruleVersionId=12658&fileName=8%20CCR%201403-1"
TABLE_2024 = "https://drive.google.com/file/d/1j9wqebwdFbZqNIpwuLcYEXgKqKvXagUf/view"
TABLE_2025 = "https://drive.google.com/file/d/1wK5dCjkW_uqj06tTd0af9-fC6gAfGu5v/view"
MEMO_2024 = "https://drive.google.com/file/d/1uTkDYcRXuCX3dIbnzfyC5vtomzCNkWbR/view"
PLANS = "https://drive.google.com/drive/folders/1YSLL5Sn32NyKbp8Z0063ldFbAhQwfHW_"

CENTER_BANDS = ["MONTHS_0_TO_18", "MONTHS_18_TO_36", "MONTHS_36_TO_YEARS_6", "SCHOOL_AGE"]
HOME_BANDS = ["MONTHS_0_TO_24", "MONTHS_24_TO_YEARS_6", "SCHOOL_AGE"]
TIERS = ["TIER_1_2", "TIER_3", "TIER_4_5"]


def num(value: str) -> str:
    return f"{Decimal(value):.2f}".rstrip("0").rstrip(".")


def licensed(parsed: dict, ptype: str, bands: list, kind: str) -> str:
    noun = {"CENTER": "child care centers", "HOME": "family child care homes"}[ptype]
    label = {"CENTER": "licensed center", "HOME": "licensed family child care home"}[ptype]
    band_variable = {"CENTER": "co_ccap_center_age_band", "HOME": "co_ccap_home_age_band"}[ptype]
    lines = [
        f"description: Colorado pays licensed {noun} up to these full-time daily rates under the Child Care Assistance Program, by county, age band and quality tier.",
        "metadata:",
        "  propagate_metadata_to_children: true",
        "  unit: currency-USD",
        "  period: day",
        f"  label: Colorado CCCAP {label} full-time daily rates",
        "  breakdown:",
        "    - county",
        f"    - {band_variable}",
        "    - co_ccap_quality_tier",
        "  breakdown_labels:",
        "    - County",
        "    - Age band",
        "    - Colorado Shines quality tier",
        "  reference:",
        # PolicyEngine US cites each source once, so the title names both pages.
        '    - title: "8 CCR 1403-1 3.125(FFF) and 3.130, the county pays the lesser of the private pay rate and the county reimbursement rate, and the state-established licensed provider base and tiered rates #page 101,118"',
        f"      href: {SOS}#page=101",
        "    - title: CDEC, State-Established Daily Licensed Provider Reimbursement Rates effective October 1, 2024",
        f"      href: {TABLE_2024}",
        "    - title: CDEC, State-Established Daily Licensed Provider Reimbursement Rates effective October 1, 2025",
        f"      href: {TABLE_2025}",
        "    - title: CDEC Operational Memo OM-CCCAP-2024-0002, State-Established Regular Rates",
        f"      href: {MEMO_2024}",
        "",
    ]
    t24 = parsed["state"]["2024-10-01"]
    t25 = parsed["state"]["2025-10-01"]
    counties = sorted({k.split("|")[0] for k in t24})
    for county in counties:
        lines.append(f"{county}:")
        for band in bands:
            lines.append(f"  {band}:")
            for tier in TIERS:
                key = f"{county}|{ptype}|{band}|{tier}"
                lines.append(f"    {tier}:")
                lines.append(f"      2024-10-01: {num(t24[key])}")
                lines.append(f"      2025-10-01: {num(t25[key])}")
    return "\n".join(lines) + "\n"


def exempt(parsed: dict) -> str:
    lines = [
        "description: Colorado pays qualified exempt child care providers up to these full-time daily rates under the Child Care Assistance Program, by county and age band.",
        "metadata:",
        "  propagate_metadata_to_children: true",
        "  unit: currency-USD",
        "  period: day",
        "  label: Colorado CCCAP qualified exempt provider full-time daily rates",
        "  breakdown:",
        "    - county",
        "    - co_ccap_qualified_exempt_age_band",
        "  breakdown_labels:",
        "    - County",
        "    - Age band",
        "  reference:",
        '    - title: "8 CCR 1403-1 3.125(FFF) and 3.130(B) and (D), the county pays the lesser of the private pay rate and the county reimbursement rate, rate types by provider type, and qualified exempt rates set by counties #page 101,119"',
        f"      href: {SOS}#page=101",
        "    - title: CDEC, County CCCAP Policies and Rate Plans (County Ceiling Rates, Provider Type Exempt, Regular rate type)",
        f"      href: {PLANS}",
        "",
    ]
    for county, plans in sorted(parsed["exempt"].items()):
        dated = sorted((date, entry) for date, entry in plans.items() if date >= "2024-10-01")
        assert dated and dated[0][0] == "2024-10-01", (county, dated[:1])
        lines.append(f"{county}:")
        for band, field in (("UNDER_5", "UNDER_5"), ("AGE_5_AND_OVER", "AGE_5_AND_OVER")):
            lines.append(f"  {band}:")
            previous = None
            for date, entry in dated:
                value = num(entry[field])
                if value != previous:
                    lines.append(f"    {date}: {value}")
                    previous = value
    return "\n".join(lines) + "\n"


def main(parsed_path: str, tree: str):
    parsed = json.loads(Path(parsed_path).read_text())
    assert not parsed["problems"], parsed["problems"][:5]
    out = Path(tree) / "policyengine_us/parameters/gov/states/co/ccap/rates"
    out.mkdir(parents=True, exist_ok=True)
    (out / "licensed_center.yaml").write_text(licensed(parsed, "CENTER", CENTER_BANDS, "center"))
    (out / "licensed_home.yaml").write_text(licensed(parsed, "HOME", HOME_BANDS, "home"))
    (out / "qualified_exempt.yaml").write_text(exempt(parsed))
    for name in ("licensed_center.yaml", "licensed_home.yaml", "qualified_exempt.yaml"):
        print(name, sum(1 for _ in (out / name).open()), "lines")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
