# Sources

Each file's SHA-256 hash identifies the copy we read. `scripts/download_sources.sh` checks the two ACF workbooks against these hashes before it extracts their tables.

## Spending and caseloads

- **CCDF Expenditures for FY 2024 (all appropriation years)**, Administration for Children and Families, Office of Child Care. Tables 3a and 4a give each state's federal and state spending and its spending of ARP supplemental funds.
  - Page: https://acf.gov/occ/data/fy-2024-ccdf-state-expenditure-data
  - File: https://acf.gov/sites/default/files/documents/occ/CCDF_Expenditures_for_FY_2024_all_appropriation_years.xlsx
  - Retrieved November 4, 2026
  - SHA-256: `a3ee490cbce4a54067f3f2da98ec622b0ad986422b7580b394a317004cc34b04`
  - Extracts: `data/acf/ccdf_table3a_fy2024.csv`, `data/acf/ccdf_table4a_fy2024.csv`
- **FY 2024 CCDF Data Tables (Preliminary)**, Administration for Children and Families, Office of Child Care. Table 1 gives the average monthly adjusted number of families and children each state served.
  - Page: https://acf.gov/occ/data/fy-2024-ccdf-data-tables-preliminary
  - File: https://acf.gov/sites/default/files/documents/occ/FY2024-ccdf-data-tables-preliminary.xlsx
  - Retrieved November 4, 2026
  - SHA-256: `951479601b6ee67066352f06a0cc380e3200b4cb6700f6c207690e8174d2ac3f`
  - Extract: `data/acf/ccdf_fy2024_table1_children_served.csv`

## Reported child care spending

- **Kathryn Shantz, "Using Administrative Records to Evaluate Child Care Expense Reporting among Child Care Subsidy Recipients"**, SEHSD Working Paper 2019-11, U.S. Census Bureau, presented at the Population Association of America's 2019 meeting. It matches CCDF administrative records to the 2010 to 2014 CPS ASEC.
  - Page: https://www.census.gov/library/working-papers/2019/demo/SEHSD-WP2019-11.html
  - File: https://www.census.gov/content/dam/Census/library/working-papers/2019/demo/sehsd-wp2019-11.pdf
  - Retrieved November 6, 2026
  - SHA-256: `224e41956bc09aff2d9d4be5eb98484ea9dc8d01ad67cab7adf9994077228dd3`
- **Microcosm's child care input**, which carries each SPM unit's child care spending from the CPS ASEC's `SPM_CHILDCAREXPNS`: https://github.com/PolicyEngine/microcosm/blob/main/packages/microcosm-build/src/microcosm/build/us_runtime/childcare.py

## Law and guidance

- **45 CFR 98.20**, a child's eligibility for CCDF services, as in force on November 1, 2026: https://www.ecfr.gov/current/title-45/part-98/section-98.20
- **Vermont Child Care Financial Assistance Program, "Understanding Payments"**, question 3, on paying the state rate whatever a provider charges.
  - File: https://outside.vermont.gov/dept/DCF/Shared%20Documents/CDD/CCFAP/CCFAP-Understanding-Payments.pdf#page=1
  - Retrieved November 4, 2026
  - SHA-256: `deffc72afe0f5cba1567504b231e0f5c4eeb02e5d155b526924db7197773dded`
- **Colorado, 8 CCR 1403-1, section 3.111**, the Child Care Assistance Program's activity requirement: https://www.sos.state.co.us/CCR/GenerateRulePdf.do?ruleVersionId=12658&fileName=8%20CCR%201403-1#page=31
- **Colorado, 8 CCR 1403-1, section 3.124**, the Child Care Assistance Program's parent fees: https://www.sos.state.co.us/CCR/GenerateRulePdf.do?ruleVersionId=12658&fileName=8%20CCR%201403-1#page=79

The pull requests in `REPORT.md` cite the state law behind each change.

## Model and data

- **PolicyEngine US** (https://github.com/PolicyEngine/policyengine-us), at these commits:
  - `e53b426082cd8953b30d8ede8b944f2d5f7246be`: `main`, for the five scenario runs in `results/scenarios/`
  - `040fe5686c956dfce960f7c55fa263687a5bf669`: `main`, the base of the fix runs in `results/fixes/`
  - `0296cdbd13be978f864969724bd8d91abcb2c3a4`: `main`, for `results/teen_share_sweep_0296cdbd13.json` and `.txt`
  - `097b3c7f8a1a99f06867cba0d2dbfc41b3caf8ca`: `main`, for `results/colorado/parent_fee_hours_097b3c7f8a.txt`; its Colorado child care code matches `e53b426082`'s
  - `6e93ee2a214b108c4a01cdee3a195410b566b343`: PolicyEngine/policyengine-us#10690, Colorado
  - `9cd97f594a9c92b27fe6e62202323212042c93ac`: PolicyEngine/policyengine-us#10691, North Carolina
  - `caec9d8a8078e60bff5903bd68352d7e953719fd`: PolicyEngine/policyengine-us#10679, New Hampshire
  - `378827969c5146731eb7f60e75e9e8f293e33460`: PolicyEngine/policyengine-us#10678, Vermont, for `results/bill_split_by_age.json` and the first Vermont case file
  - `de507aa74c0989a1c894591170b20bb821ad0de5`: PolicyEngine/policyengine-us#10694, Vermont, for the second Vermont case file
  - `0304cc8b70a646f59fd473f856d880aa197aa197`: PolicyEngine/policyengine-us#10694, Vermont, for `results/fixes/vt-att-0304cc8b70.json` and the third Vermont case file, whose cases match the second's
  - `391422a907c0220845603c4d8a9a9c21fed318ac`, tree `b9a86257269ad564a404eb855fb171426b87a3f7`: PolicyEngine/policyengine-us#10699, Colorado, its commit `2eeea71ed3` cherry-picked onto `040fe5686c`
  - `366c0b6dae5b15640ff0eb6cb2e42e396b76f00d`, tree `4d851608428346512745f8f7b1312d30345ad9d3`: PolicyEngine/policyengine-us#10721, Colorado, `040fe5686c` with Colorado's child care variables and parameters from merge commit `14de5b316a`
  - `0b0aea6c9503325d29dbd2d8df8080606c7a09e1`, tree `09bb0ff8aba6a19d7851af59a9cf3bbb443e5f47`: PolicyEngine/policyengine-us#10698, Nebraska, its commits `6e75fcf479` and `b060143520` cherry-picked onto `040fe5686c`
- **Populace US 2024**, the default dataset at those commits: `hf://datasets/policyengine/populace-us/populace_us_2024.h5@populace-us-2024-spm-20260909`
  - Revision: `9a814a3b3b53c0ecd6e1737b6ec862c31300ef6f`
  - Size: 826,917,837 bytes
  - SHA-256: `6496cc4393d4d3c6574f76eca231de5898c803b9067645591fd5c4d3e65aee84`
