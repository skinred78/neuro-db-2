#!/usr/bin/env python3
"""
Coverage Comparison Script (Phase 2A)

Compares synonym/abbreviation coverage before and after Phase 2A TTY expansion.

Metrics Tracked:
- Synonym coverage (target: ≥50%)
- Abbreviation coverage (target: ≥20%)
- Definition/MeSH/Association retention (should remain stable)

Input:
- OLD CSV: imports/umls/umls_neuroscience_terms.csv.backup_TIMESTAMP
- NEW CSV: imports/umls/umls_neuroscience_terms.csv

Output:
- Terminal report with before/after metrics
- Success/failure assessment
"""

import csv
from pathlib import Path
from collections import Counter

# File paths
IMPORTS_DIR = Path("imports/umls")
OLD_CSV = None  # Will be detected from backup
NEW_CSV = IMPORTS_DIR / "umls_neuroscience_terms.csv"

# Success thresholds
SYNONYM_TARGET = 50.0  # 50% coverage
ABBREVIATION_TARGET = 20.0  # 20% coverage


def find_latest_backup():
    """Find the most recent backup file."""
    backups = list(IMPORTS_DIR.glob("umls_neuroscience_terms.csv.backup_*"))
    if not backups:
        print("❌ ERROR: No backup file found")
        return None

    # Sort by modification time, return latest
    latest = max(backups, key=lambda p: p.stat().st_mtime)
    return latest


def analyze_csv(csv_path):
    """Analyze coverage metrics for a CSV file."""
    print(f"📊 Analyzing {csv_path.name}...")

    total_terms = 0
    with_synonyms = 0
    with_abbreviations = 0
    with_definitions = 0
    with_mesh = 0
    with_associations = 0

    synonym_counts = []
    abbreviation_counts = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_terms += 1

            # Count synonyms (Synonym 1, Synonym 2, Synonym 3)
            syn_count = sum(1 for i in [1, 2, 3] if row.get(f'Synonym {i}', '').strip())
            if syn_count > 0:
                with_synonyms += 1
                synonym_counts.append(syn_count)

            # Count abbreviations
            if row.get('Abbreviation', '').strip():
                with_abbreviations += 1
                abbreviation_counts.append(1)

            # Count other enrichments
            if row.get('Definition', '').strip():
                with_definitions += 1

            if row.get('Closest MeSH term', '').strip():
                with_mesh += 1

            # Count associated terms (1-8)
            assoc_count = sum(1 for i in range(1, 9) if row.get(f'Commonly Associated Term {i}', '').strip())
            if assoc_count > 0:
                with_associations += 1

    # Calculate percentages
    pct_synonyms = (with_synonyms / total_terms * 100) if total_terms > 0 else 0
    pct_abbreviations = (with_abbreviations / total_terms * 100) if total_terms > 0 else 0
    pct_definitions = (with_definitions / total_terms * 100) if total_terms > 0 else 0
    pct_mesh = (with_mesh / total_terms * 100) if total_terms > 0 else 0
    pct_associations = (with_associations / total_terms * 100) if total_terms > 0 else 0

    return {
        'total_terms': total_terms,
        'with_synonyms': with_synonyms,
        'pct_synonyms': pct_synonyms,
        'with_abbreviations': with_abbreviations,
        'pct_abbreviations': pct_abbreviations,
        'with_definitions': with_definitions,
        'pct_definitions': pct_definitions,
        'with_mesh': with_mesh,
        'pct_mesh': pct_mesh,
        'with_associations': with_associations,
        'pct_associations': pct_associations,
        'synonym_counts': synonym_counts,
        'abbreviation_counts': abbreviation_counts
    }


def print_comparison(old_stats, new_stats):
    """Print formatted comparison report."""
    print("\n" + "="*70)
    print("COVERAGE COMPARISON REPORT (Phase 2A)")
    print("="*70)

    print(f"\n📈 Overall Metrics:")
    print(f"   Terms: {old_stats['total_terms']:,} → {new_stats['total_terms']:,}")

    print(f"\n🎯 Primary Targets (Phase 2A):")
    print(f"   {'Metric':<25} {'OLD':<15} {'NEW':<15} {'Change':<15} {'Status'}")
    print(f"   {'-'*25} {'-'*15} {'-'*15} {'-'*15} {'-'*10}")

    # Synonyms
    old_syn = old_stats['pct_synonyms']
    new_syn = new_stats['pct_synonyms']
    syn_change = new_syn - old_syn
    syn_status = "✅ PASS" if new_syn >= SYNONYM_TARGET else "❌ FAIL"
    print(f"   {'Synonym Coverage':<25} {old_syn:>6.1f}%{'':<8} {new_syn:>6.1f}%{'':<8} {syn_change:>+6.1f}%{'':<8} {syn_status}")

    # Abbreviations
    old_abb = old_stats['pct_abbreviations']
    new_abb = new_stats['pct_abbreviations']
    abb_change = new_abb - old_abb
    abb_status = "✅ PASS" if new_abb >= ABBREVIATION_TARGET else "❌ FAIL"
    print(f"   {'Abbreviation Coverage':<25} {old_abb:>6.1f}%{'':<8} {new_abb:>6.1f}%{'':<8} {abb_change:>+6.1f}%{'':<8} {abb_status}")

    print(f"\n📊 Enrichment Retention (should remain stable):")
    print(f"   {'Metric':<25} {'OLD':<15} {'NEW':<15} {'Change':<15} {'Status'}")
    print(f"   {'-'*25} {'-'*15} {'-'*15} {'-'*15} {'-'*10}")

    # Definitions
    old_def = old_stats['pct_definitions']
    new_def = new_stats['pct_definitions']
    def_change = new_def - old_def
    def_status = "✅ OK" if abs(def_change) < 5 else "⚠️  WARN"
    print(f"   {'Definition Coverage':<25} {old_def:>6.1f}%{'':<8} {new_def:>6.1f}%{'':<8} {def_change:>+6.1f}%{'':<8} {def_status}")

    # MeSH
    old_mesh = old_stats['pct_mesh']
    new_mesh = new_stats['pct_mesh']
    mesh_change = new_mesh - old_mesh
    mesh_status = "✅ OK" if abs(mesh_change) < 5 else "⚠️  WARN"
    print(f"   {'MeSH Coverage':<25} {old_mesh:>6.1f}%{'':<8} {new_mesh:>6.1f}%{'':<8} {mesh_change:>+6.1f}%{'':<8} {mesh_status}")

    # Associations
    old_assoc = old_stats['pct_associations']
    new_assoc = new_stats['pct_associations']
    assoc_change = new_assoc - old_assoc
    assoc_status = "✅ OK" if abs(assoc_change) < 5 else "⚠️  WARN"
    print(f"   {'Association Coverage':<25} {old_assoc:>6.1f}%{'':<8} {new_assoc:>6.1f}%{'':<8} {assoc_change:>+6.1f}%{'':<8} {assoc_status}")

    print(f"\n📈 Detailed Counts:")
    print(f"   Synonyms: {old_stats['with_synonyms']:,} → {new_stats['with_synonyms']:,} ({new_stats['with_synonyms'] - old_stats['with_synonyms']:+,})")
    print(f"   Abbreviations: {old_stats['with_abbreviations']:,} → {new_stats['with_abbreviations']:,} ({new_stats['with_abbreviations'] - old_stats['with_abbreviations']:+,})")

    # Overall success
    print(f"\n{'='*70}")
    success = new_syn >= SYNONYM_TARGET and new_abb >= ABBREVIATION_TARGET
    if success:
        print("✅ PHASE 2A SUCCESS")
        print(f"   Synonym coverage: {new_syn:.1f}% (target: ≥{SYNONYM_TARGET}%)")
        print(f"   Abbreviation coverage: {new_abb:.1f}% (target: ≥{ABBREVIATION_TARGET}%)")
    else:
        print("❌ PHASE 2A INCOMPLETE")
        if new_syn < SYNONYM_TARGET:
            print(f"   Synonym coverage: {new_syn:.1f}% < {SYNONYM_TARGET}% target")
        if new_abb < ABBREVIATION_TARGET:
            print(f"   Abbreviation coverage: {new_abb:.1f}% < {ABBREVIATION_TARGET}% target")
    print(f"{'='*70}")


def main():
    print("="*70)
    print("UMLS COVERAGE COMPARISON (Phase 2A)")
    print("="*70)

    # Step 1: Find backup
    global OLD_CSV
    OLD_CSV = find_latest_backup()
    if not OLD_CSV:
        print("\n⚠️  WARNING: Cannot find backup, skipping OLD metrics")
        return

    print(f"\n📂 Comparing:")
    print(f"   OLD: {OLD_CSV.name}")
    print(f"   NEW: {NEW_CSV.name}")

    if not NEW_CSV.exists():
        print(f"\n❌ ERROR: {NEW_CSV} not found")
        return

    # Step 2: Analyze both files
    old_stats = analyze_csv(OLD_CSV)
    new_stats = analyze_csv(NEW_CSV)

    # Step 3: Print comparison
    print_comparison(old_stats, new_stats)


if __name__ == "__main__":
    main()
