#!/usr/bin/env bash
# Fetch ACF's two FY 2024 CCDF workbooks into data/raw/, check each against the
# SHA-256 hash in sources.md, and extract the three tables the comparison reads
# into data/acf/.
#
# acf.gov sometimes refuses scripted downloads. When a download fails or its hash
# differs, the script names the file to save by hand from a browser, and a rerun
# picks it up.
#
# Usage: scripts/download_sources.sh   (needs Python with openpyxl; set PYTHON to choose one)
set -euo pipefail

cd "$(dirname "$0")/.."
raw=data/raw
mkdir -p "$raw"
python=${PYTHON:-python3}

fetch() {
  local url=$1 name=$2 sha=$3
  local path="$raw/$name"
  if [ ! -s "$path" ]; then
    curl -fsSL --retry 3 -o "$path" "$url" || rm -f "$path"
  fi
  if [ ! -s "$path" ] || [ "$(shasum -a 256 "$path" | cut -c1-64)" != "$sha" ]; then
    echo "Save $url as $path (replacing any file there), then rerun this script." >&2
    exit 1
  fi
  echo "verified $path"
}

fetch https://acf.gov/sites/default/files/documents/occ/CCDF_Expenditures_for_FY_2024_all_appropriation_years.xlsx \
  CCDF_Expenditures_for_FY_2024_all_appropriation_years.xlsx \
  a3ee490cbce4a54067f3f2da98ec622b0ad986422b7580b394a317004cc34b04
fetch https://acf.gov/sites/default/files/documents/occ/FY2024-ccdf-data-tables-preliminary.xlsx \
  FY2024-ccdf-data-tables-preliminary.xlsx \
  951479601b6ee67066352f06a0cc380e3200b4cb6700f6c207690e8174d2ac3f

"$python" -I scripts/extract_acf_tables.py \
  "$raw/CCDF_Expenditures_for_FY_2024_all_appropriation_years.xlsx" \
  "$raw/FY2024-ccdf-data-tables-preliminary.xlsx" \
  data/acf
