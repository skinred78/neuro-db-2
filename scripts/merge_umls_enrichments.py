#!/usr/bin/env python3
"""
Merge UMLS Enrichments Script

Merges OLD enriched CSV (definitions, MeSH codes, associations) with
NEW enriched CSV (expanded synonyms/abbreviations from Phase 2A).

Merge Strategy (per unresolved question #3):
- For matching terms: Take definition/MeSH/associations from OLD, synonyms/abbreviations from NEW
- For terms in OLD but not NEW: Keep entire OLD row (preserve enrichments)
- For terms in NEW but not OLD: Add NEW row (new discoveries)

Input:
- OLD CSV: imports/umls/umls_neuroscience_terms.csv.backup_TIMESTAMP
- NEW CSV: imports/umls/umls_neuroscience_imported.csv

Output:
- Merged CSV: imports/umls/umls_neuroscience_terms.csv
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict

# File paths
IMPORTS_DIR = Path("imports/umls")
OLD_CSV = None  # Will be detected from backup
NEW_CSV = IMPORTS_DIR / "umls_neuroscience_imported.csv"
OUTPUT_CSV = IMPORTS_DIR / "umls_neuroscience_terms.csv"

def find_latest_backup():
    """Find the most recent backup file."""
    backups = list(IMPORTS_DIR.glob("umls_neuroscience_terms.csv.backup_*"))
    if not backups:
        print("❌ ERROR: No backup file found")
        print(f"   Expected: {IMPORTS_DIR}/umls_neuroscience_terms.csv.backup_TIMESTAMP")
        sys.exit(1)

    # Sort by modification time, return latest
    latest = max(backups, key=lambda p: p.stat().st_mtime)
    return latest


def load_csv_by_term(csv_path):
    """Load CSV into dict keyed by term name (case-insensitive)."""
    print(f"📥 Loading {csv_path.name}...")

    terms = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        for row in reader:
            term_key = row['Term'].lower().strip()
            terms[term_key] = row

    print(f"   ✅ Loaded {len(terms):,} terms ({len(headers)} columns)")
    return terms, headers


def merge_enrichments(old_terms, new_terms):
    """
    Merge OLD and NEW term dictionaries.

    Strategy:
    - OLD wins: Definition, MeSH code, Associated Terms, UK/US Spelling, Word Forms
    - NEW wins: Synonyms, Abbreviations
    - Preserve: Terms in OLD but not NEW (keep all enrichments)
    - Add: Terms in NEW but not OLD (new discoveries)
    """
    print(f"\n🔄 Merging enrichments...")

    merged = {}
    stats = {
        'matched': 0,
        'old_only': 0,
        'new_only': 0
    }

    # Process OLD terms
    for term_key, old_row in old_terms.items():
        if term_key in new_terms:
            # MATCH: Merge columns
            new_row = new_terms[term_key]
            merged_row = old_row.copy()

            # NEW wins for synonyms/abbreviations
            merged_row['Synonym 1'] = new_row.get('Synonym 1', '')
            merged_row['Synonym 2'] = new_row.get('Synonym 2', '')
            merged_row['Synonym 3'] = new_row.get('Synonym 3', '')
            merged_row['Abbreviation'] = new_row.get('Abbreviation', '')

            # OLD retains all other enrichments (definitions, MeSH, associations, etc.)

            merged[term_key] = merged_row
            stats['matched'] += 1
        else:
            # OLD ONLY: Keep entire row (preserve enrichments)
            merged[term_key] = old_row
            stats['old_only'] += 1

    # Process NEW-only terms
    for term_key, new_row in new_terms.items():
        if term_key not in old_terms:
            # NEW ONLY: Add to merged
            merged[term_key] = new_row
            stats['new_only'] += 1

    print(f"   ✅ Merge complete:")
    print(f"      Matched (merged): {stats['matched']:,}")
    print(f"      OLD only (preserved): {stats['old_only']:,}")
    print(f"      NEW only (added): {stats['new_only']:,}")
    print(f"      Total merged: {len(merged):,}")

    return merged, stats


def write_merged_csv(merged_terms, headers):
    """Write merged terms to output CSV."""
    print(f"\n💾 Writing merged CSV to {OUTPUT_CSV}...")

    # Sort by term name for consistent output
    sorted_terms = sorted(merged_terms.items(), key=lambda x: x[0])

    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for _, row in sorted_terms:
            writer.writerow(row)

    print(f"   ✅ Wrote {len(sorted_terms):,} terms")


def validate_merge(merged_count, old_count, new_count, stats):
    """Validate merge results."""
    print(f"\n✅ Validation:")

    # Check: merged count should be >= max(old, new)
    expected_min = max(old_count, new_count)
    if merged_count >= expected_min:
        print(f"   ✅ Merged count ({merged_count:,}) >= max(OLD, NEW) ({expected_min:,})")
    else:
        print(f"   ❌ ERROR: Merged count ({merged_count:,}) < max(OLD, NEW) ({expected_min:,})")
        return False

    # Check: matched + old_only should equal old_count
    if stats['matched'] + stats['old_only'] == old_count:
        print(f"   ✅ All OLD terms accounted for")
    else:
        print(f"   ❌ ERROR: OLD terms mismatch")
        return False

    # Check: matched + new_only should equal new_count
    if stats['matched'] + stats['new_only'] == new_count:
        print(f"   ✅ All NEW terms accounted for")
    else:
        print(f"   ❌ ERROR: NEW terms mismatch")
        return False

    return True


def main():
    print("="*70)
    print("UMLS ENRICHMENT MERGER (Phase 2A)")
    print("="*70)

    # Step 1: Find latest backup
    global OLD_CSV
    OLD_CSV = find_latest_backup()
    print(f"\n📂 Input Files:")
    print(f"   OLD (enriched): {OLD_CSV.name}")
    print(f"   NEW (expanded synonyms/abbreviations): {NEW_CSV.name}")

    if not NEW_CSV.exists():
        print(f"\n❌ ERROR: {NEW_CSV} not found")
        print(f"   Run scripts/import_umls_neuroscience.py first")
        sys.exit(1)

    # Step 2: Load both CSVs
    old_terms, old_headers = load_csv_by_term(OLD_CSV)
    new_terms, new_headers = load_csv_by_term(NEW_CSV)

    # Use OLD headers (more complete schema)
    headers = old_headers

    # Step 3: Merge enrichments
    merged_terms, stats = merge_enrichments(old_terms, new_terms)

    # Step 4: Validate merge
    if not validate_merge(len(merged_terms), len(old_terms), len(new_terms), stats):
        print("\n❌ Merge validation FAILED")
        sys.exit(1)

    # Step 5: Write merged CSV
    write_merged_csv(merged_terms, headers)

    print("\n" + "="*70)
    print("MERGE COMPLETE")
    print("="*70)
    print(f"\n✅ Output: {OUTPUT_CSV}")
    print(f"✅ Total terms: {len(merged_terms):,}")
    print(f"\n📊 Merge Statistics:")
    print(f"   Matched (merged columns): {stats['matched']:,}")
    print(f"   OLD only (preserved): {stats['old_only']:,}")
    print(f"   NEW only (added): {stats['new_only']:,}")


if __name__ == "__main__":
    main()
