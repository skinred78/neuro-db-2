#!/usr/bin/env python3
"""
Analyze synonym coverage in UMLS import to determine impact of 3-synonym limit.

This script analyzes how many synonyms we're losing by limiting to 3 per term
in the NeuroDB-2 schema.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

# File paths
BASE_DIR = Path(__file__).parent.parent
CUIS_FILE = BASE_DIR / "imports/umls/neuroscience_cuis.txt"
CONCEPTS_FILE = BASE_DIR / "imports/umls/umls_concepts_intermediate.json"
OUTPUT_FILE = BASE_DIR / "imports/umls/synonym_coverage_analysis.md"

def load_neuroscience_cuis():
    """Load the neuroscience CUI filter list."""
    print("Loading neuroscience CUI filter...")
    with open(CUIS_FILE, 'r') as f:
        cuis = {line.strip() for line in f if line.strip()}
    print(f"  Loaded {len(cuis):,} neuroscience CUIs")
    return cuis

def analyze_intermediate_concepts():
    """Analyze synonym counts from intermediate concepts JSON."""
    print("\nAnalyzing intermediate concepts JSON...")

    with open(CONCEPTS_FILE, 'r') as f:
        concepts = json.load(f)

    print(f"  Loaded {len(concepts):,} concepts")

    # Count synonyms per concept
    synonym_counts = []
    terms_with_synonyms = 0
    total_synonyms_available = 0
    total_synonyms_kept = 0

    for cui, data in concepts.items():
        synonyms = data.get('synonyms', [])
        syn_count = len(synonyms)
        synonym_counts.append(syn_count)

        if syn_count > 0:
            terms_with_synonyms += 1
            total_synonyms_available += syn_count
            total_synonyms_kept += min(syn_count, 3)

    # Distribution analysis
    distribution = Counter(synonym_counts)

    return {
        'total_concepts': len(concepts),
        'terms_with_synonyms': terms_with_synonyms,
        'total_synonyms_available': total_synonyms_available,
        'total_synonyms_kept': total_synonyms_kept,
        'total_synonyms_lost': total_synonyms_available - total_synonyms_kept,
        'distribution': distribution,
        'synonym_counts': synonym_counts
    }

def generate_report(stats):
    """Generate detailed analysis report."""

    dist = stats['distribution']
    total = stats['total_concepts']

    # Calculate percentages
    pct_with_synonyms = (stats['terms_with_synonyms'] / total) * 100
    pct_lost = (stats['total_synonyms_lost'] / stats['total_synonyms_available']) * 100 if stats['total_synonyms_available'] > 0 else 0

    # Find terms with >3 synonyms
    terms_exceeding_limit = sum(count for syn_count, count in dist.items() if syn_count > 3)
    pct_exceeding = (terms_exceeding_limit / total) * 100

    report = f"""# UMLS Synonym Coverage Analysis

**Analysis Date**: 2025-11-21
**Purpose**: Determine impact of 3-synonym limit in NeuroDB-2 schema

---

## Executive Summary

**Synonym Loss**: We're losing **{stats['total_synonyms_lost']:,} synonyms** ({pct_lost:.1f}%) by limiting to 3 per term.

**Key Findings**:
- {stats['terms_with_synonyms']:,} of {total:,} terms have synonyms ({pct_with_synonyms:.1f}%)
- {terms_exceeding_limit:,} terms have >3 synonyms ({pct_exceeding:.1f}%)
- Average synonyms per term (for terms with synonyms): {stats['total_synonyms_available'] / stats['terms_with_synonyms']:.1f}

**Recommendation**: See "Schema Expansion Options" below

---

## Detailed Statistics

### Overall Synonym Metrics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Concepts** | {total:,} | 100.0% |
| **Terms with Synonyms** | {stats['terms_with_synonyms']:,} | {pct_with_synonyms:.1f}% |
| **Terms without Synonyms** | {total - stats['terms_with_synonyms']:,} | {100 - pct_with_synonyms:.1f}% |
| | | |
| **Total Synonyms Available** | {stats['total_synonyms_available']:,} | 100.0% |
| **Synonyms Kept (3-limit)** | {stats['total_synonyms_kept']:,} | {100 - pct_lost:.1f}% |
| **Synonyms Lost (3-limit)** | {stats['total_synonyms_lost']:,} | {pct_lost:.1f}% |

### Impact of 3-Synonym Limit

| Synonym Count | Terms | % of Total | Cumulative % | Impact |
|---------------|-------|------------|--------------|--------|
"""

    # Build distribution table
    cumulative_terms = 0
    for syn_count in sorted(dist.keys()):
        count = dist[syn_count]
        pct = (count / total) * 100
        cumulative_terms += count
        cumulative_pct = (cumulative_terms / total) * 100

        # Impact assessment
        if syn_count == 0:
            impact = "No synonyms"
        elif syn_count <= 3:
            impact = "✅ All kept"
        elif syn_count <= 5:
            impact = f"⚠️ Lose {syn_count - 3}"
        else:
            impact = f"❌ Lose {syn_count - 3}"

        report += f"| {syn_count} | {count:,} | {pct:.2f}% | {cumulative_pct:.1f}% | {impact} |\n"

    # Terms exceeding limit breakdown
    report += f"""

### Terms Exceeding 3-Synonym Limit

| Category | Count | % of Total |
|----------|-------|------------|
| **Terms with 4 synonyms** | {dist.get(4, 0):,} | {(dist.get(4, 0) / total * 100):.2f}% |
| **Terms with 5 synonyms** | {dist.get(5, 0):,} | {(dist.get(5, 0) / total * 100):.2f}% |
| **Terms with 6-10 synonyms** | {sum(dist.get(i, 0) for i in range(6, 11)):,} | {(sum(dist.get(i, 0) for i in range(6, 11)) / total * 100):.2f}% |
| **Terms with 11-20 synonyms** | {sum(dist.get(i, 0) for i in range(11, 21)):,} | {(sum(dist.get(i, 0) for i in range(11, 21)) / total * 100):.2f}% |
| **Terms with 21+ synonyms** | {sum(dist.get(i, 0) for i in range(21, 100)):,} | {(sum(dist.get(i, 0) for i in range(21, 100)) / total * 100):.2f}% |
| **TOTAL exceeding limit** | {terms_exceeding_limit:,} | {pct_exceeding:.2f}% |

---

## Synonym Loss Analysis

### By Term Count

**Terms losing synonyms**: {terms_exceeding_limit:,} of {total:,} ({pct_exceeding:.1f}%)

**Synonym retention rate**: {100 - pct_lost:.1f}%

### Average Synonyms Lost Per Affected Term

For the {terms_exceeding_limit:,} terms with >3 synonyms:
- Average synonyms lost: {stats['total_synonyms_lost'] / terms_exceeding_limit if terms_exceeding_limit > 0 else 0:.1f} per term

---

## Schema Expansion Options

### Option A: Keep Current Limit (3 synonyms)
**Pros**:
- ✅ Simple schema (22 columns)
- ✅ Retains {100 - pct_lost:.1f}% of all synonyms
- ✅ Only {pct_exceeding:.1f}% of terms affected

**Cons**:
- ❌ Lose {stats['total_synonyms_lost']:,} synonyms ({pct_lost:.1f}%)
- ❌ {terms_exceeding_limit:,} terms don't get full synonym coverage

**Recommendation**: ✅ **Acceptable** if synonym loss <20% and affected terms <5%

---

### Option B: Expand to 5 Synonyms
"""

    # Calculate 5-synonym impact
    synonyms_kept_5 = sum(min(count, 5) * freq for count, freq in dist.items())
    synonyms_lost_5 = stats['total_synonyms_available'] - synonyms_kept_5
    pct_lost_5 = (synonyms_lost_5 / stats['total_synonyms_available']) * 100 if stats['total_synonyms_available'] > 0 else 0
    terms_exceeding_5 = sum(count for syn_count, count in dist.items() if syn_count > 5)
    pct_exceeding_5 = (terms_exceeding_5 / total) * 100

    report += f"""
**Impact**:
- Synonyms lost: {synonyms_lost_5:,} ({pct_lost_5:.1f}%) - down from {pct_lost:.1f}%
- Terms affected: {terms_exceeding_5:,} ({pct_exceeding_5:.2f}%) - down from {pct_exceeding:.1f}%

**Schema change**: Add 2 columns (Synonym 4, Synonym 5) = 24 total columns

**Pros**:
- ✅ Retain {100 - pct_lost_5:.1f}% of synonyms (vs {100 - pct_lost:.1f}% now)
- ✅ Only {pct_exceeding_5:.2f}% of terms affected (vs {pct_exceeding:.1f}% now)

**Cons**:
- ❌ Schema expansion (22 → 24 columns)
- ❌ Requires re-import of existing data

**Recommendation**: {"✅ **Recommended**" if pct_lost > 20 else "⚠️ **Optional**"} if synonym loss reduction is valuable

---

### Option C: Expand to 8 Synonyms
"""

    # Calculate 8-synonym impact
    synonyms_kept_8 = sum(min(count, 8) * freq for count, freq in dist.items())
    synonyms_lost_8 = stats['total_synonyms_available'] - synonyms_kept_8
    pct_lost_8 = (synonyms_lost_8 / stats['total_synonyms_available']) * 100 if stats['total_synonyms_available'] > 0 else 0
    terms_exceeding_8 = sum(count for syn_count, count in dist.items() if syn_count > 8)
    pct_exceeding_8 = (terms_exceeding_8 / total) * 100

    report += f"""
**Impact**:
- Synonyms lost: {synonyms_lost_8:,} ({pct_lost_8:.1f}%) - down from {pct_lost:.1f}%
- Terms affected: {terms_exceeding_8:,} ({pct_exceeding_8:.2f}%) - down from {pct_exceeding:.1f}%

**Schema change**: Add 5 columns (Synonym 4-8) = 27 total columns

**Pros**:
- ✅ Retain {100 - pct_lost_8:.1f}% of synonyms
- ✅ Minimal terms affected ({pct_exceeding_8:.2f}%)

**Cons**:
- ❌ Significant schema expansion (22 → 27 columns)
- ❌ Sparse data (most terms won't use all 8 slots)

**Recommendation**: {"✅ **Maximum coverage**" if pct_lost_8 < 5 else "⚠️ **Overkill**"} - consider if near-complete synonym retention is critical

---

## Lex Stream Impact Analysis

### Current Coverage (3 synonyms)
- **Synonym Finder agent**: Has access to {stats['total_synonyms_kept']:,} synonyms
- **Query expansion**: {100 - pct_lost:.1f}% of available synonym variations covered

### With 5 Synonyms
- **Synonym Finder agent**: Would have {synonyms_kept_5:,} synonyms (+{synonyms_kept_5 - stats['total_synonyms_kept']:,})
- **Query expansion**: {100 - pct_lost_5:.1f}% coverage (+{pct_lost - pct_lost_5:.1f}% improvement)

### With 8 Synonyms
- **Synonym Finder agent**: Would have {synonyms_kept_8:,} synonyms (+{synonyms_kept_8 - stats['total_synonyms_kept']:,})
- **Query expansion**: {100 - pct_lost_8:.1f}% coverage (+{pct_lost - pct_lost_8:.1f}% improvement)

---

## Recommendations

### If Synonym Loss < 20%
**Action**: ✅ Keep 3-synonym limit
- Schema remains simple
- Lex Stream coverage adequate
- Can always expand later if testing shows gaps

### If Synonym Loss 20-40%
**Action**: ⚠️ Consider expanding to 5 synonyms
- Moderate schema change (24 columns)
- Significant improvement in coverage
- Test with Lex Stream to validate impact

### If Synonym Loss > 40%
**Action**: ❌ Expand to 8 synonyms or use JSON field
- High synonym loss unacceptable
- Either expand schema or use JSON array for unlimited synonyms
- Alternative: Store synonyms in separate table

---

## Alternative Approaches

### Approach 1: JSON Array Field
Store all synonyms in single JSON field: `synonyms: ["syn1", "syn2", "syn3", ...]`

**Pros**:
- ✅ Unlimited synonyms
- ✅ No schema expansion

**Cons**:
- ❌ Harder to query in CSV format
- ❌ Requires JSON parsing

### Approach 2: Separate Synonym Table
Create `synonyms.csv` with columns: `Term, Synonym, Source`

**Pros**:
- ✅ Unlimited synonyms per term
- ✅ Preserves source attribution
- ✅ Normalized database design

**Cons**:
- ❌ Requires join operation
- ❌ More complex export to Lex Stream

### Approach 3: Priority Filtering
Keep 3-synonym limit but prioritize by source quality

**Current**: First 3 synonyms encountered
**Improved**: Best 3 synonyms (MSH > NCI > GO > others)

**Pros**:
- ✅ No schema change
- ✅ Higher quality synonyms retained

**Cons**:
- ❌ Still lose {stats['total_synonyms_lost']:,} synonyms
- ❌ Requires source-aware filtering logic

---

## Next Steps

1. **Review this analysis** to determine acceptable synonym loss threshold
2. **Test with Lex Stream** to see if 3-synonym limit impacts query quality
3. **Make schema decision**: Keep 3, expand to 5, expand to 8, or use alternative
4. **If expanding**: Update schema, re-import UMLS, update Lex Stream export
5. **If keeping 3**: Implement priority filtering to retain highest-quality synonyms

---

**Analysis Generated**: 2025-11-21
**Data Source**: `imports/umls/umls_concepts_intermediate.json`
**Total Concepts Analyzed**: {total:,}
**Script**: `scripts/analyze_synonym_coverage.py`
"""

    return report

def main():
    print("=" * 60)
    print("UMLS Synonym Coverage Analysis")
    print("=" * 60)

    # Analyze intermediate concepts
    stats = analyze_intermediate_concepts()

    # Generate report
    print("\nGenerating analysis report...")
    report = generate_report(stats)

    # Write report
    with open(OUTPUT_FILE, 'w') as f:
        f.write(report)

    print(f"\n✅ Analysis complete!")
    print(f"   Report saved to: {OUTPUT_FILE}")

    # Print summary
    print("\n" + "=" * 60)
    print("QUICK SUMMARY")
    print("=" * 60)
    print(f"Total concepts: {stats['total_concepts']:,}")
    print(f"Terms with synonyms: {stats['terms_with_synonyms']:,} ({stats['terms_with_synonyms']/stats['total_concepts']*100:.1f}%)")
    print(f"Total synonyms available: {stats['total_synonyms_available']:,}")
    print(f"Synonyms kept (3-limit): {stats['total_synonyms_kept']:,}")
    print(f"Synonyms LOST (3-limit): {stats['total_synonyms_lost']:,} ({stats['total_synonyms_lost']/stats['total_synonyms_available']*100:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    main()
