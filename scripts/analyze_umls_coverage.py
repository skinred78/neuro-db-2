#!/usr/bin/env python3
"""
UMLS Coverage Analysis - Investigate Low Definition Coverage

Analyzes intermediate UMLS data to understand why definition coverage is only 24.5%
instead of expected 80%+.

Investigation areas:
1. Sample random terms (with/without definitions)
2. Source vocabulary distribution
3. Coverage by semantic type
4. Term relevance assessment

Input: imports/umls/umls_concepts_intermediate.json
Output: imports/umls/coverage_analysis_report.md
"""

import json
import random
from pathlib import Path
from collections import defaultdict, Counter

# File paths
INTERMEDIATE_JSON = Path("imports/umls/umls_concepts_intermediate.json")
FILTER_STATS = Path("imports/umls/filter_statistics.json")
MRSTY_FILE = Path("downloads/umls/2025AB/2025AB/META/MRSTY.RRF")
OUTPUT_REPORT = Path("imports/umls/coverage_analysis_report.md")

# Sample sizes
SAMPLE_SIZE = 100
SAMPLE_WITH_DEFS = 50
SAMPLE_WITHOUT_DEFS = 50


def load_data():
    """Load intermediate concepts and filter statistics."""
    print(f"\n📥 Loading data...")

    with open(INTERMEDIATE_JSON, 'r', encoding='utf-8') as f:
        concepts = json.load(f)

    with open(FILTER_STATS, 'r', encoding='utf-8') as f:
        filter_stats = json.load(f)

    print(f"   ✅ Loaded {len(concepts):,} concepts")
    return concepts, filter_stats


def load_cui_semantic_types(concept_cuis):
    """Load semantic types for concepts (needed for coverage by type analysis)."""
    print(f"\n📖 Loading semantic types for {len(concept_cuis):,} concepts...")

    cui_types = defaultdict(set)

    with open(MRSTY_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            cols = line.strip().split('|')
            if len(cols) >= 4:
                cui = cols[0]
                if cui in concept_cuis:
                    semantic_type = cols[3]  # Semantic type name
                    cui_types[cui].add(semantic_type)

    print(f"   ✅ Loaded semantic types for {len(cui_types):,} concepts")
    return cui_types


def sample_terms(concepts):
    """Sample random terms for manual relevance assessment."""
    print(f"\n🎲 Sampling {SAMPLE_SIZE} random terms...")

    # Separate terms with/without definitions
    with_defs = [(cui, data) for cui, data in concepts.items() if data.get('definition')]
    without_defs = [(cui, data) for cui, data in concepts.items() if not data.get('definition')]

    print(f"   Terms with definitions: {len(with_defs):,}")
    print(f"   Terms without definitions: {len(without_defs):,}")

    # Sample
    sample_with = random.sample(with_defs, min(SAMPLE_WITH_DEFS, len(with_defs)))
    sample_without = random.sample(without_defs, min(SAMPLE_WITHOUT_DEFS, len(without_defs)))

    return sample_with, sample_without


def analyze_source_distribution(concepts):
    """Analyze which source vocabularies contributed most."""
    print(f"\n📊 Analyzing source vocabulary distribution...")

    # Count terms by source
    source_counts = Counter()
    source_with_defs = Counter()

    for cui, data in concepts.items():
        sources = data.get('sources', [])
        has_def = bool(data.get('definition'))

        for source in sources:
            source_counts[source] += 1
            if has_def:
                source_with_defs[source] += 1

    # Calculate coverage percentages
    source_coverage = {}
    for source in source_counts:
        total = source_counts[source]
        with_defs = source_with_defs.get(source, 0)
        pct = (with_defs / total * 100) if total > 0 else 0
        source_coverage[source] = {
            'total': total,
            'with_defs': with_defs,
            'coverage': pct
        }

    return source_coverage


def analyze_semantic_type_coverage(concepts, cui_semantic_types):
    """Analyze definition coverage by semantic type."""
    print(f"\n🔬 Analyzing coverage by semantic type...")

    type_counts = Counter()
    type_with_defs = Counter()

    for cui, data in concepts.items():
        semantic_types = cui_semantic_types.get(cui, set())
        has_def = bool(data.get('definition'))

        for sem_type in semantic_types:
            type_counts[sem_type] += 1
            if has_def:
                type_with_defs[sem_type] += 1

    # Calculate coverage percentages
    type_coverage = {}
    for sem_type in type_counts:
        total = type_counts[sem_type]
        with_defs = type_with_defs.get(sem_type, 0)
        pct = (with_defs / total * 100) if total > 0 else 0
        type_coverage[sem_type] = {
            'total': total,
            'with_defs': with_defs,
            'coverage': pct
        }

    return type_coverage


def generate_report(concepts, sample_with, sample_without, source_coverage, type_coverage):
    """Generate markdown report with analysis findings."""
    print(f"\n📝 Generating report...")

    report_lines = []

    # Header
    report_lines.append("# UMLS Coverage Analysis Report")
    report_lines.append("")
    report_lines.append("**Date**: 2025-11-20")
    report_lines.append("**Total Concepts**: {:,}".format(len(concepts)))

    # Overall coverage
    with_defs = sum(1 for c in concepts.values() if c.get('definition'))
    coverage_pct = (with_defs / len(concepts) * 100) if concepts else 0
    report_lines.append("**Overall Definition Coverage**: {:,} / {:,} ({:.1f}%)".format(
        with_defs, len(concepts), coverage_pct))
    report_lines.append("")
    report_lines.append("---")

    # 1. Random Sample - WITH Definitions
    report_lines.append("")
    report_lines.append("## 1. Sample Terms WITH Definitions (n={})".format(len(sample_with)))
    report_lines.append("")
    report_lines.append("| # | Term | Definition (first 80 chars) | Source(s) |")
    report_lines.append("|---|------|----------------------------|-----------|")

    for i, (cui, data) in enumerate(sample_with[:20], 1):  # Show first 20
        term = data.get('preferred_term', 'N/A')
        definition = data.get('definition', '')[:80]
        sources = ', '.join(sorted(data.get('sources', [])))
        def_source = data.get('definition_source', 'N/A')
        report_lines.append("| {} | {} | {} | {} (def: {}) |".format(
            i, term, definition, sources, def_source))

    if len(sample_with) > 20:
        report_lines.append("")
        report_lines.append("*({} additional terms sampled but not shown)*".format(len(sample_with) - 20))

    # 2. Random Sample - WITHOUT Definitions
    report_lines.append("")
    report_lines.append("## 2. Sample Terms WITHOUT Definitions (n={})".format(len(sample_without)))
    report_lines.append("")
    report_lines.append("| # | Term | Source(s) | Synonyms/Abbrev |")
    report_lines.append("|---|------|-----------|-----------------|")

    for i, (cui, data) in enumerate(sample_without[:20], 1):  # Show first 20
        term = data.get('preferred_term', 'N/A')
        sources = ', '.join(sorted(data.get('sources', [])))
        syns = len(data.get('synonyms', []))
        abbrs = len(data.get('abbreviations', []))
        report_lines.append("| {} | {} | {} | {} syn, {} abbr |".format(
            i, term, sources, syns, abbrs))

    if len(sample_without) > 20:
        report_lines.append("")
        report_lines.append("*({} additional terms sampled but not shown)*".format(len(sample_without) - 20))

    # 3. Source Vocabulary Distribution
    report_lines.append("")
    report_lines.append("## 3. Coverage by Source Vocabulary")
    report_lines.append("")
    report_lines.append("| Source | Total Terms | With Defs | Coverage % |")
    report_lines.append("|--------|-------------|-----------|------------|")

    # Sort by total count descending
    sorted_sources = sorted(source_coverage.items(), key=lambda x: x[1]['total'], reverse=True)
    for source, stats in sorted_sources[:20]:  # Top 20
        report_lines.append("| {} | {:,} | {:,} | {:.1f}% |".format(
            source, stats['total'], stats['with_defs'], stats['coverage']))

    if len(sorted_sources) > 20:
        report_lines.append("")
        report_lines.append("*({} additional sources not shown)*".format(len(sorted_sources) - 20))

    # 4. Coverage by Semantic Type
    report_lines.append("")
    report_lines.append("## 4. Coverage by Semantic Type")
    report_lines.append("")
    report_lines.append("| Semantic Type | Total Terms | With Defs | Coverage % |")
    report_lines.append("|---------------|-------------|-----------|------------|")

    # Sort by total count descending
    sorted_types = sorted(type_coverage.items(), key=lambda x: x[1]['total'], reverse=True)
    for sem_type, stats in sorted_types[:20]:  # Top 20
        report_lines.append("| {} | {:,} | {:,} | {:.1f}% |".format(
            sem_type, stats['total'], stats['with_defs'], stats['coverage']))

    if len(sorted_types) > 20:
        report_lines.append("")
        report_lines.append("*({} additional semantic types not shown)*".format(len(sorted_types) - 20))

    # 5. Key Findings
    report_lines.append("")
    report_lines.append("## 5. Key Findings")
    report_lines.append("")

    # Identify sources with lowest/highest coverage
    top_coverage_sources = sorted(source_coverage.items(), key=lambda x: x[1]['coverage'], reverse=True)[:5]
    low_coverage_sources = sorted(source_coverage.items(), key=lambda x: x[1]['coverage'])[:5]

    report_lines.append("### Highest Coverage Sources")
    for source, stats in top_coverage_sources:
        report_lines.append("- **{}**: {:.1f}% ({:,} of {:,})".format(
            source, stats['coverage'], stats['with_defs'], stats['total']))

    report_lines.append("")
    report_lines.append("### Lowest Coverage Sources")
    for source, stats in low_coverage_sources:
        if stats['total'] >= 100:  # Only show if significant presence
            report_lines.append("- **{}**: {:.1f}% ({:,} of {:,})".format(
                source, stats['coverage'], stats['with_defs'], stats['total']))

    # Identify types with lowest/highest coverage
    top_coverage_types = sorted(type_coverage.items(), key=lambda x: x[1]['coverage'], reverse=True)[:5]
    low_coverage_types = sorted(type_coverage.items(), key=lambda x: x[1]['coverage'])[:5]

    report_lines.append("")
    report_lines.append("### Highest Coverage Semantic Types")
    for sem_type, stats in top_coverage_types:
        report_lines.append("- **{}**: {:.1f}% ({:,} of {:,})".format(
            sem_type, stats['coverage'], stats['with_defs'], stats['total']))

    report_lines.append("")
    report_lines.append("### Lowest Coverage Semantic Types")
    for sem_type, stats in low_coverage_types:
        if stats['total'] >= 100:  # Only show if significant presence
            report_lines.append("- **{}**: {:.1f}% ({:,} of {:,})".format(
                sem_type, stats['coverage'], stats['with_defs'], stats['total']))

    # 6. Recommendations
    report_lines.append("")
    report_lines.append("## 6. Recommendations")
    report_lines.append("")
    report_lines.append("*To be added after manual review of sampled terms*")
    report_lines.append("")
    report_lines.append("**Next Steps**:")
    report_lines.append("1. Review sampled terms for neuroscience relevance")
    report_lines.append("2. Assess whether low-coverage sources should be excluded")
    report_lines.append("3. Consider prioritizing high-coverage sources (MSH, SNOMEDCT_US)")
    report_lines.append("4. Decide: proceed as-is, filter to definitions-only, or hybrid approach")

    # Write report
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"   ✅ Report saved to {OUTPUT_REPORT}")


def main():
    print("="*70)
    print("UMLS COVERAGE ANALYSIS")
    print("="*70)
    print("\nInvestigating why definition coverage is only 24.5% vs 80%+ expected")

    # Step 1: Load data
    concepts, filter_stats = load_data()

    # Step 2: Sample random terms
    sample_with, sample_without = sample_terms(concepts)

    # Step 3: Analyze source distribution
    source_coverage = analyze_source_distribution(concepts)

    # Step 4: Load semantic types for coverage analysis
    concept_cuis = set(concepts.keys())
    cui_semantic_types = load_cui_semantic_types(concept_cuis)

    # Step 5: Analyze coverage by semantic type
    type_coverage = analyze_semantic_type_coverage(concepts, cui_semantic_types)

    # Step 6: Generate report
    generate_report(concepts, sample_with, sample_without, source_coverage, type_coverage)

    # Summary
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\n✅ Analysis report: {OUTPUT_REPORT}")
    print(f"\n📊 Quick Summary:")

    # Top 5 sources by volume
    sorted_sources = sorted(source_coverage.items(), key=lambda x: x[1]['total'], reverse=True)
    print(f"\n   Top 5 Sources by Volume:")
    for i, (source, stats) in enumerate(sorted_sources[:5], 1):
        print(f"      {i}. {source}: {stats['total']:,} terms ({stats['coverage']:.1f}% with defs)")

    # Top 5 semantic types by volume
    sorted_types = sorted(type_coverage.items(), key=lambda x: x[1]['total'], reverse=True)
    print(f"\n   Top 5 Semantic Types by Volume:")
    for i, (sem_type, stats) in enumerate(sorted_types[:5], 1):
        print(f"      {i}. {sem_type}: {stats['total']:,} terms ({stats['coverage']:.1f}% with defs)")

    print(f"\n🎯 Next: Review {OUTPUT_REPORT} to inform coverage decision")


if __name__ == "__main__":
    main()
