# UMLS Synonym Coverage Analysis

**Analysis Date**: 2025-11-21
**Purpose**: Determine impact of 3-synonym limit in NeuroDB-2 schema

---

## Executive Summary

**Synonym Loss**: We're losing **6,561 synonyms** (12.6%) by limiting to 3 per term.

**Key Findings**:
- 29,306 of 325,241 terms have synonyms (9.0%)
- 2,481 terms have >3 synonyms (0.8%)
- Average synonyms per term (for terms with synonyms): 1.8

**Recommendation**: See "Schema Expansion Options" below

---

## Detailed Statistics

### Overall Synonym Metrics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Concepts** | 325,241 | 100.0% |
| **Terms with Synonyms** | 29,306 | 9.0% |
| **Terms without Synonyms** | 295,935 | 91.0% |
| | | |
| **Total Synonyms Available** | 52,008 | 100.0% |
| **Synonyms Kept (3-limit)** | 45,447 | 87.4% |
| **Synonyms Lost (3-limit)** | 6,561 | 12.6% |

### Impact of 3-Synonym Limit

| Synonym Count | Terms | % of Total | Cumulative % | Impact |
|---------------|-------|------------|--------------|--------|
| 0 | 295,935 | 90.99% | 91.0% | No synonyms |
| 1 | 17,760 | 5.46% | 96.5% | ✅ All kept |
| 2 | 6,951 | 2.14% | 98.6% | ✅ All kept |
| 3 | 2,114 | 0.65% | 99.2% | ✅ All kept |
| 4 | 1,033 | 0.32% | 99.6% | ⚠️ Lose 1 |
| 5 | 586 | 0.18% | 99.7% | ⚠️ Lose 2 |
| 6 | 308 | 0.09% | 99.8% | ❌ Lose 3 |
| 7 | 207 | 0.06% | 99.9% | ❌ Lose 4 |
| 8 | 134 | 0.04% | 99.9% | ❌ Lose 5 |
| 9 | 62 | 0.02% | 100.0% | ❌ Lose 6 |
| 10 | 33 | 0.01% | 100.0% | ❌ Lose 7 |
| 11 | 36 | 0.01% | 100.0% | ❌ Lose 8 |
| 12 | 23 | 0.01% | 100.0% | ❌ Lose 9 |
| 13 | 11 | 0.00% | 100.0% | ❌ Lose 10 |
| 14 | 13 | 0.00% | 100.0% | ❌ Lose 11 |
| 15 | 7 | 0.00% | 100.0% | ❌ Lose 12 |
| 16 | 4 | 0.00% | 100.0% | ❌ Lose 13 |
| 17 | 7 | 0.00% | 100.0% | ❌ Lose 14 |
| 18 | 2 | 0.00% | 100.0% | ❌ Lose 15 |
| 19 | 1 | 0.00% | 100.0% | ❌ Lose 16 |
| 20 | 4 | 0.00% | 100.0% | ❌ Lose 17 |
| 21 | 2 | 0.00% | 100.0% | ❌ Lose 18 |
| 22 | 2 | 0.00% | 100.0% | ❌ Lose 19 |
| 25 | 1 | 0.00% | 100.0% | ❌ Lose 22 |
| 27 | 1 | 0.00% | 100.0% | ❌ Lose 24 |
| 29 | 2 | 0.00% | 100.0% | ❌ Lose 26 |
| 32 | 1 | 0.00% | 100.0% | ❌ Lose 29 |
| 37 | 1 | 0.00% | 100.0% | ❌ Lose 34 |


### Terms Exceeding 3-Synonym Limit

| Category | Count | % of Total |
|----------|-------|------------|
| **Terms with 4 synonyms** | 1,033 | 0.32% |
| **Terms with 5 synonyms** | 586 | 0.18% |
| **Terms with 6-10 synonyms** | 744 | 0.23% |
| **Terms with 11-20 synonyms** | 108 | 0.03% |
| **Terms with 21+ synonyms** | 10 | 0.00% |
| **TOTAL exceeding limit** | 2,481 | 0.76% |

---

## Synonym Loss Analysis

### By Term Count

**Terms losing synonyms**: 2,481 of 325,241 (0.8%)

**Synonym retention rate**: 87.4%

### Average Synonyms Lost Per Affected Term

For the 2,481 terms with >3 synonyms:
- Average synonyms lost: 2.6 per term

---

## Schema Expansion Options

### Option A: Keep Current Limit (3 synonyms)
**Pros**:
- ✅ Simple schema (22 columns)
- ✅ Retains 87.4% of all synonyms
- ✅ Only 0.8% of terms affected

**Cons**:
- ❌ Lose 6,561 synonyms (12.6%)
- ❌ 2,481 terms don't get full synonym coverage

**Recommendation**: ✅ **Acceptable** if synonym loss <20% and affected terms <5%

---

### Option B: Expand to 5 Synonyms

**Impact**:
- Synonyms lost: 2,632 (5.1%) - down from 12.6%
- Terms affected: 862 (0.27%) - down from 0.8%

**Schema change**: Add 2 columns (Synonym 4, Synonym 5) = 24 total columns

**Pros**:
- ✅ Retain 94.9% of synonyms (vs 87.4% now)
- ✅ Only 0.27% of terms affected (vs 0.8% now)

**Cons**:
- ❌ Schema expansion (22 → 24 columns)
- ❌ Requires re-import of existing data

**Recommendation**: ⚠️ **Optional** if synonym loss reduction is valuable

---

### Option C: Expand to 8 Synonyms

**Impact**:
- Synonyms lost: 869 (1.7%) - down from 12.6%
- Terms affected: 213 (0.07%) - down from 0.8%

**Schema change**: Add 5 columns (Synonym 4-8) = 27 total columns

**Pros**:
- ✅ Retain 98.3% of synonyms
- ✅ Minimal terms affected (0.07%)

**Cons**:
- ❌ Significant schema expansion (22 → 27 columns)
- ❌ Sparse data (most terms won't use all 8 slots)

**Recommendation**: ✅ **Maximum coverage** - consider if near-complete synonym retention is critical

---

## Lex Stream Impact Analysis

### Current Coverage (3 synonyms)
- **Synonym Finder agent**: Has access to 45,447 synonyms
- **Query expansion**: 87.4% of available synonym variations covered

### With 5 Synonyms
- **Synonym Finder agent**: Would have 49,376 synonyms (+3,929)
- **Query expansion**: 94.9% coverage (+7.6% improvement)

### With 8 Synonyms
- **Synonym Finder agent**: Would have 51,139 synonyms (+5,692)
- **Query expansion**: 98.3% coverage (+10.9% improvement)

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
- ❌ Still lose 6,561 synonyms
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
**Total Concepts Analyzed**: 325,241
**Script**: `scripts/analyze_synonym_coverage.py`
