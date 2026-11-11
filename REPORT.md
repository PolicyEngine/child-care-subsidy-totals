# Child care subsidies in PolicyEngine US, 2026

We estimate that PolicyEngine US pays $1.79 billion in state child care subsidies in 2026 on its default dataset, Populace US 2024. The Administration for Children and Families (ACF) reports that the 50 states and DC spent $29.25 billion of federal and state Child Care and Development Fund (CCDF) money in fiscal year 2024. They spent $20.62 billion of it on direct services, and $18.56 billion in all without the one-time supplemental funds of the American Rescue Plan Act (ARP). Our estimate falls short of direct services by $18.84 billion, or 91%.

Three features of the dataset hold the estimate down:

- It records no hours or days of care, so 28 programs pay nothing.
- Several programs pay no more than the family's child care bill, and the bills it records run below those programs' rates.
- Microcosm draws the dataset's child care spending from the CPS ASEC, where 57.6% of households with a CCDF subsidy reported no paid care in 2010 to 2014.

In Connecticut, Colorado and Vermont, our estimate exceeds ACF's direct services instead, because the model pays more units than those states served.

## Three groups of programs

PolicyEngine US models a child care subsidy program in each of the 50 states and DC. We ran the default dataset for 2026 as shipped and with two changes to its inputs. The first gives every child under 13 in a unit that reports a bill a full-time schedule of 8 hours a day, 5 days a week and 21 days a month. The second also raises each of those units' annual bill to $1 million, so each program's own rates set what it pays. How a state's total responds places its program in one of three groups.

| Group | Programs | As shipped ($M) | Full-time schedule ($M) | Schedule and $1 million bill ($M) | ACF direct services ($M) | ACF total less ARP supplemental ($M) |
|---|---:|---:|---:|---:|---:|---:|
| Pays from the file | 17 | 1,786.3 | 2,232.3 | 40,110.2 | 5,571.8 | 4,670.8 |
| Needs a care schedule | 28 | 0.0 | 7,028.7 | 36,700.4 | 13,963.9 | 13,158.4 |
| Capped by small bills | 6 | 0.0 | 0.4 | 1,823.6 | 1,087.0 | 733.5 |
| All | 51 | 1,786.3 | 9,261.3 | 78,634.2 | 20,622.8 | 18,562.7 |

Seventeen programs pay from the file, $1.79 billion in all, and every dollar goes to a unit that reports a bill. Twenty-eight pay nothing until a child has hours or days of care, and $7.03 billion once children have the full-time schedule. Six pay $524 in all on the dataset as shipped and less than $1 million with the schedule. The units they pay report average bills of $26 to $997 a year, state by state, and the $1 million bill lifts those six to $1.82 billion.

[`results/state_mechanisms.md`](results/state_mechanisms.md) gives every state's figures. [`results/scenarios/`](results/scenarios/) also holds runs that give the schedule to every child under 13, and then the $1 million bill to every unit with one.

## Why most programs pay little

### Care schedules

The dataset records no hours of care, days of care or provider type for any child, and the model's inputs for hours and days default to zero. [PolicyEngine/microcosm#916](https://github.com/PolicyEngine/microcosm/pull/916), a draft pull request, adds days and hours of care for children aged 0 to 12 to Microcosm's build, from the 2024 National Survey of Early Care and Education.

### Reported bills

Microcosm carries each SPM unit's child care spending from the CPS ASEC (`SPM_CHILDCAREXPNS`), and the model reads it as the bill before any subsidy. The CPS ASEC asks what families paid for child care while they worked. The Census Bureau matched CCDF administrative records to the 2010 to 2014 surveys ([SEHSD Working Paper 2019-11](https://www.census.gov/library/working-papers/2019/demo/SEHSD-WP2019-11.html)). Of the households receiving a subsidy, 57.6% reported no paid child care and 36.8% reported paid care. On average, those households reported $952 a year of child care spending, against $625 a year of copayments in the administrative records.

A program that pays the lesser of its rate and the family's bill pays a family no more than its reported spending, and nothing to a family that reports none. For example, the model's Connecticut formula pays the lesser of the approved cost of care and the bill, less the family fee. We estimate that Connecticut's total rises from $405.6 million on the dataset as shipped to $857.2 million with the full-time schedule, and to $1.39 billion with the $1 million bill.

## Three states where our estimate exceeds ACF's

Our estimate exceeds ACF's direct services in Connecticut by 86%, in Colorado by 61% and in Vermont by 48%. In each, the model pays more units than the state served in an average month of fiscal year 2024.

| State | Our estimate ($M) | ACF direct services ($M) | Units the model pays | Families served in an average month |
|---|---:|---:|---:|---:|
| Connecticut | 405.6 | 217.8 | 80,759 | 10,600 |
| Colorado | 270.7 | 167.7 | 31,425 | 11,600 |
| Vermont | 45.9 | 31.1 | 5,124 | 2,200 |

In 12 of the 17 programs that pay from the file, Connecticut's and Colorado's among them, the model pays every unit that is eligible in January and reports a bill. We estimate an average of $5,022 a unit in Connecticut, while ACF's figures come to $20,550 of direct services per family served.

Colorado's Department of Early Childhood requires a family's adult caretakers to take part in an eligible activity, such as work or school, before the state pays for child care ([8 CCR 1403-1](https://www.sos.state.co.us/CCR/GenerateRulePdf.do?ruleVersionId=12658&fileName=8%20CCR%201403-1#page=31)). The model's Colorado formula has no such test. [PolicyEngine/policyengine-us#10690](https://github.com/PolicyEngine/policyengine-us/pull/10690) adds it, and we estimate that Colorado's subsidies then fall from $270.7 million to $0.5 million. Eight of the 19 paid records lose their payment, and they carry 29,426 of the 31,425 units.

On the dataset as shipped, the model also charges Colorado families no parent fee. Its formula scales each child's part of the fee by that child's hours of care a day, so a child with no recorded hours adds nothing. For example, a parent earning $40,000 with a 3-year-old and a $1,000 monthly bill owes a $232.23 fee at 8 hours a day and nothing with no hours ([`results/colorado/parent_fee_hours_097b3c7f8a.txt`](results/colorado/parent_fee_hours_097b3c7f8a.txt)). Hours enter Colorado's formula through the fee and nowhere else, and with the full-time schedule, we estimate that Colorado's subsidies fall from $270.7 million to $163.0 million. Colorado's counties assess one fee for each household, adding $15 for each child after the first when income exceeds the poverty guideline ([8 CCR 1403-1, 3.124](https://www.sos.state.co.us/CCR/GenerateRulePdf.do?ruleVersionId=12658&fileName=8%20CCR%201403-1#page=79)). The model charges that whole fee for each eligible child. [PolicyEngine/policyengine-us#10721](https://github.com/PolicyEngine/policyengine-us/pull/10721) charges each household one fee and treats a child with no recorded hours as in full-time care, and we estimate that Colorado's subsidies then fall from $270.7 million to $203.9 million.

Since December 17, 2023, Vermont has paid providers its state rate whatever they charge ([Understanding Payments, question 3](https://outside.vermont.gov/dept/DCF/Shared%20Documents/CDD/CCFAP/CCFAP-Understanding-Payments.pdf#page=1)). In the model, $16.2 million of Vermont's $45.9 million exceeds what the paid units report spending, and household benefits count the other $29.8 million.

A few records carry each of these totals: the largest paid record carries 74% of Colorado's payment, 53% of Vermont's and 42% of Connecticut's.

## Changes to the model

Each pull request cites the law it follows. For each formula change, an Axiom issue tracks the encoding of the same rule.

| Pull request | Change | Our estimate for 2026 | Axiom |
|---|---|---|---|
| [policyengine-us#10690](https://github.com/PolicyEngine/policyengine-us/pull/10690) | Colorado requires an eligible activity, such as work or school | Colorado's subsidies fall from $270.7 million to $0.5 million | [rulespec-us#2067](https://github.com/TheAxiomFoundation/rulespec-us/issues/2067) |
| [policyengine-us#10699](https://github.com/PolicyEngine/policyengine-us/pull/10699) | Colorado pays only for children within its age limits | Colorado's fall from $270.7 million to $269.3 million | [rulespec-us#2073](https://github.com/TheAxiomFoundation/rulespec-us/issues/2073) |
| [policyengine-us#10721](https://github.com/PolicyEngine/policyengine-us/pull/10721) | Colorado charges each household one parent fee, and the model treats a child with no recorded hours as in full-time care | Colorado's fall from $270.7 million to $203.9 million | [rulespec-us#2136](https://github.com/TheAxiomFoundation/rulespec-us/issues/2136) |
| [policyengine-us#10723](https://github.com/PolicyEngine/policyengine-us/pull/10723) | Colorado's counties pay no more than the county reimbursement rate for each child's care | Colorado's stay at $269.3 million, as under policyengine-us#10699 | [rulespec-us#2135](https://github.com/TheAxiomFoundation/rulespec-us/issues/2135) |
| [policyengine-us#10691](https://github.com/PolicyEngine/policyengine-us/pull/10691) | North Carolina requires a need for care | North Carolina's fall from $127.1 million to $2.0 million | [rulespec-us#2068](https://github.com/TheAxiomFoundation/rulespec-us/issues/2068), [axiom-corpus#985](https://github.com/TheAxiomFoundation/axiom-corpus/issues/985) |
| [policyengine-us#10679](https://github.com/PolicyEngine/policyengine-us/pull/10679) | New Hampshire divides monthly income by 4.33 weeks in the family's cost share | New Hampshire's fall by $1.66 a year | [rulespec-us#2056](https://github.com/TheAxiomFoundation/rulespec-us/issues/2056) |
| [policyengine-us#10698](https://github.com/PolicyEngine/policyengine-us/pull/10698) | Nebraska pays only for children within its age limit who use an approved provider | Nebraska's fall from $498 to $250 | [rulespec-us#2072](https://github.com/TheAxiomFoundation/rulespec-us/issues/2072) |
| [policyengine-us#10678](https://github.com/PolicyEngine/policyengine-us/pull/10678) | Tests Vermont's family balance against the department's sample invoices | No formula change | |
| [policyengine-us#10694](https://github.com/PolicyEngine/policyengine-us/pull/10694) | Vermont pays nothing for a child with no care hours once a sibling has them | The dataset records no care hours, so the formula still reads the bill as attendance | [rulespec-us#1984](https://github.com/TheAxiomFoundation/rulespec-us/issues/1984) |

In the run of policyengine-us#10721, families pay $66.8 million more of their bills, and we estimate that they claim $6.1 million more in the child and dependent care credit. With $0.8 million more in SNAP, household net income falls by $59.9 million, and national SPM poverty rates don't change.

In the run of policyengine-us#10723, which builds on policyengine-us#10699, no eligible child's share of the unit's reported spending reaches the county rate. The largest, $922 a month for an 8-year-old in Eagle County, comes to 64% of the child's $1,450 monthly rate ([`results/colorado/rate_cap_78d5e022ce.json`](results/colorado/rate_cap_78d5e022ce.json)).

In the runs of policyengine-us#10690 and policyengine-us#10691, families who lose the subsidy pay more of their bills. We estimate that they receive $18.2 million more in SNAP in Colorado and $37.4 million more in North Carolina, and national SPM poverty rates don't change in either run.

## Open questions

### Take-up

We estimate 347,519 paid units in 2026 across the 17 programs that pay from the file, while those states served an average of 228,300 families a month in fiscal year 2024.

### What the reported spending measures

The model can read the copayment a subsidized family reports as that family's whole bill, and then pay a subsidy against it.

### Which children the bill covers

The model splits each unit's reported spending evenly across its members under 18. Under that split, we estimate that children aged 13 to 17 get $12.6 billion of the $79.1 billion that units with children report. Federal rules cover children under 13, and older children at a state's option when they can't care for themselves or a court supervises them ([45 CFR 98.20](https://www.ecfr.gov/current/title-45/part-98/section-98.20)).

### How SPM net income counts subsidies

The model's SPM net income counts Colorado's, Washington's and West Virginia's child care subsidies and leaves out the other 48 programs. Under policyengine-us#10691, we estimate that North Carolina's subsidies fall by $125.1 million while national SPM net income rises by $37.4 million, the SNAP that families gain.

## Payments toward a teenager's share of the bill

For each state's program, we built pairs of otherwise identical SPM units, each with a parent earning $20,000 and a 3-year-old with a $36,000 charge. A 15-year-old's annual child care charge comes to $0 in one unit of each pair and $12,000 in the other. The 15-year-old has no special need, and federal rules leave out a child of that age unless the child can't provide self-care or a court supervises the child ([45 CFR 98.20](https://www.ecfr.gov/current/title-45/part-98/section-98.20)). A program that follows them pays the same in both units. At `main` commit `0296cdbd13`, 49 programs paid the same in both units, and Colorado's and Nebraska's payments rose by the teenager's whole $12,000, with the full-time schedule and with none ([`results/teen_share_sweep_0296cdbd13.txt`](results/teen_share_sweep_0296cdbd13.txt)).

Colorado's formula sums the child care and after-school charges of every member of the unit. Nebraska's pays a member's whole share of the bill whenever its rates price nothing for that member, as they do for a child the formula counts as ineligible. For example, take a parent earning $20,000 with a 3-year-old in 21 days of care a month, a 15-year-old and a $24,000 annual bill. The model pays $1,819 a month, $819 for the 3-year-old's care and the 15-year-old's whole $1,000 share of the bill.

[PolicyEngine/policyengine-us#10699](https://github.com/PolicyEngine/policyengine-us/pull/10699) limits Colorado's payment to children within its age limits, and we estimate that Colorado's subsidies then fall from $270.7 million to $269.3 million. [PolicyEngine/policyengine-us#10698](https://github.com/PolicyEngine/policyengine-us/pull/10698) limits Nebraska's to children within its age limit who use an approved provider. On the dataset as shipped, we estimate that Nebraska's program then pays $250 instead of $498, so the fix matters little until the dataset records care schedules.

[`README.md`](README.md) gives the commands that reproduce every figure here, and [`sources.md`](sources.md) lists each source with its hash.
