"""Write the three ACF tables the comparison reads as CSV files.

Usage:
    python extract_acf_tables.py EXPENDITURES.xlsx DATA_TABLES.xlsx OUT_DIR

EXPENDITURES.xlsx is ACF's "CCDF Expenditures for FY 2024 (all appropriation
years)" workbook, and DATA_TABLES.xlsx is its "FY 2024 CCDF Data Tables
(Preliminary)" workbook; scripts/download_sources.sh fetches both. The script
writes:

- ccdf_table3a_fy2024.csv: Table 3a, all expenditures by state, detailed summary
  (state and federal expenditures, including maintenance of effort);
- ccdf_table4a_fy2024.csv: Table 4a, all expenditures by state, categorical
  summary, which separates the ARP Supplemental Discretionary funds;
- ccdf_fy2024_table1_children_served.csv: Table 1, the average monthly adjusted
  number of families and children served.

Each output keeps the workbook's data rows below the header, in order, and drops
footnotes; line breaks in headers and state names become spaces.
"""

import csv
import sys
from pathlib import Path

import openpyxl

expenditures, data_tables, out_dir = (Path(a) for a in sys.argv[1:4])
out_dir.mkdir(parents=True, exist_ok=True)


def rows_below_header(sheet, first_header):
    rows = list(sheet.iter_rows(values_only=True))
    start = next(
        i for i, row in enumerate(rows) if row and str(row[0]).strip() == first_header
    )
    header = [str(c).replace("\n", " ").strip() if c is not None else "" for c in rows[start]]
    width = max(i for i, c in enumerate(header) if c) + 1
    body = []
    for row in rows[start + 1 :]:
        cells = list(row[:width]) + [None] * (width - len(row[:width]))
        # Data rows carry a number, or "-" where a state reported nothing;
        # footnote rows carry text alone.
        if cells[0] is None or not any(
            isinstance(c, (int, float)) or c == "-" for c in cells[1:]
        ):
            continue
        body.append(cells)
    return header[:width], body


def write(path, header, body):
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in body:
            writer.writerow(
                [str(row[0]).replace("\n", " ").strip()] + list(row[1:])
            )


book = openpyxl.load_workbook(expenditures, read_only=True, data_only=True)
for sheet, name in [("Table 3a", "ccdf_table3a_fy2024.csv"), ("Table 4a", "ccdf_table4a_fy2024.csv")]:
    header, body = rows_below_header(book[sheet], "State")
    write(out_dir / name, header, body)

book = openpyxl.load_workbook(data_tables, read_only=True, data_only=True)
header, body = rows_below_header(book["1. Children Served"], "State/Territory")
write(out_dir / "ccdf_fy2024_table1_children_served.csv", ["state", "families", "children"], body)
print(f"wrote three tables to {out_dir}")
