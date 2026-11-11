#!/usr/bin/env bash
# Fetch CDEC's two state-established rate tables and the 158 county rate plans
# that data/co_rates/sources.tsv lists, from CDEC's Google Drive folders, into
# DEST. The script checks each PDF against its SHA-256 hash and writes a
# `pdftotext -layout` copy beside it, which parse_co_rates.py reads.
#
# Usage: scripts/co_rates/download_co_rates.sh DEST   (needs curl and pdftotext)
set -euo pipefail

dest=${1:?usage: download_co_rates.sh DEST}
manifest="$(cd "$(dirname "$0")/../.." && pwd)/data/co_rates/sources.tsv"
mkdir -p "$dest"

tail -n +2 "$manifest" | while IFS=$'\t' read -r path id sha title; do
  out="$dest/$path"
  mkdir -p "$(dirname "$out")"
  if [ ! -s "$out" ] || [ "$(shasum -a 256 "$out" | cut -c1-64)" != "$sha" ]; then
    # Drive answers bursts of downloads with 503s, so pace them and retry.
    sleep 1
    curl -fsSL --retry 8 --retry-delay 15 --retry-all-errors -o "$out" "https://drive.google.com/uc?export=download&id=$id" || rm -f "$out"
  fi
  if [ ! -s "$out" ] || [ "$(shasum -a 256 "$out" | cut -c1-64)" != "$sha" ]; then
    echo "Save https://drive.google.com/file/d/$id/view ($title) as $out, then rerun this script." >&2
    exit 1
  fi
  pdftotext -layout "$out" "${out%.pdf}.txt"
done
echo "verified $(($(wc -l < "$manifest") - 1)) PDFs under $dest"
