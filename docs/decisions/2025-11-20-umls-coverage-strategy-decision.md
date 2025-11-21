# DEC-003: UMLS Coverage Strategy Decision

**Date**: 2025-11-20
**Status**: 🟡 Pending Decision
**Blocks**: Phase 2 UMLS import (schema mapping, validation)
**Related**: DEC-002 (CUI filter count), DEC-001 (associated concepts profiling)

---

## Context

**Phase 1 Results**: Extracted 325,241 terms from UMLS with multi-stage filtering (DEC-002 Option B).

**Critical Issue Discovered**: Only 24.5% definition coverage (79,617 of 325,241) vs 80%+ expected.

**Root Cause** (from coverage investigation):
- Anatomical ontologies (FMA, UWDA) dominate volume (30% + 18% = 48% of terms)
- These sources provide hierarchical structure, not textual definitions
- Coverage: FMA 5.1%, UWDA 5.4%, SNOMEDCT_US 15.5%
- Combined: 226,865 terms (69% of total), only 8.2% with definitions

---

## Investigation Summary

### Coverage by Source (Top 10 by Volume)

| Source | Terms | With Defs | Coverage % | Nature |
|--------|-------|-----------|------------|--------|
| **FMA** | 99,074 | 5,057 | 5.1% | Anatomical hierarchy |
| **SNOMEDCT_US** | 67,590 | 10,502 | 15.5% | Clinical terminology |
| **UWDA** | 60,201 | 3,254 | 5.4% | Anatomical hierarchy |
| **GO** | 54,118 | 37,635 | **69.5%** | Gene Ontology ✅ |
| **MEDCIN** | 39,773 | 5,081 | 12.8% | Clinical terms |
| **MTH** | 39,063 | 15,817 | 40.5% | Metathesaurus |
| **NCI** | 35,800 | 31,883 | **89.1%** | Cancer/neuro terms ✅ |
| **SNMI** | 20,079 | 6,381 | 31.8% | Systematized nomenclature |
| **RCD** | 17,346 | 5,034 | 29.0% | Read codes |
| **MSH** | 13,739 | 7,435 | **54.1%** | MeSH terms ✅ |

### High-Quality Sources (Lower Volume)

| Source | Terms | Coverage % | Assessment |
|--------|-------|------------|------------|
| **NCI** | 35,800 | 89.1% | Excellent neuroscience content |
| **CSP** | 3,376 | 81.6% | High-quality medical definitions |
| **GO** | 54,118 | 69.5% | Gene Ontology - molecular/cellular |
| **CHV** | 9,117 | 64.6% | Consumer health vocabulary |
| **AOD** | 3,564 | 56.5% | Alcohol/drug abuse |
| **MSH** | 13,739 | 54.1% | MeSH - authoritative |
| **OMIM** | 5,211 | 45.1% | Genetic disorders |

### Coverage by Semantic Type

**Low-Coverage Types** (Anatomical - Priority 1):
- Body Part, Organ, or Organ Component: 93,585 terms (5.9% coverage)
- Body Location or Region: 26,866 terms (5.6% coverage)
- Pathologic Function: 28,772 terms (6.0% coverage)

**High-Coverage Types** (Functional - Priority 1):
- Cell or Molecular Dysfunction: 5,472 terms (75.7% coverage)
- Cell Component: 7,955 terms (67.3% coverage)
- Molecular Function: 27,103 terms (65.5% coverage)
- Cell Function: 17,166 terms (65.4% coverage)

---

## Problem Statement

**Goal**: Import UMLS to provide 100K-150K neuroscience terms with quality definitions.

**Current State**: 325,241 terms extracted but 75% lack definitions.

**Why This Matters**:
1. **Lex Stream Integration**: Query expansion requires definitions (spell check, abbreviation expansion, synonym detection)
2. **DEC-001 Goal**: UMLS meant to provide definitions, not just term lists
3. **Semantic Mapping**: Need definitions to map terms correctly to NeuroDB-2 schema
4. **User Value**: Definitions enable understanding, not just recognition

**Trade-off**: Volume vs Quality
- Keep all 325K terms → 24.5% coverage (defeats purpose)
- Filter to definitions only → ~80K terms (below target, loses anatomy)
- Hybrid approach → balance volume and quality

---

## Options

### Option A: Proceed As-Is (325K terms, 24.5% coverage)

**Strategy**: Import all 325,241 extracted terms regardless of definition coverage.

**Pros**:
- Maximum coverage of anatomical structures
- Comprehensive hierarchical relationships
- No data loss from filtering
- Stays well above 100K target

**Cons**:
- **75% of terms lack definitions** (defeats UMLS import goal)
- Ultra-granular anatomy (e.g., "Cartilage of right inferior surface...") - low research value
- Bloated database (2x target volume)
- Poor Lex Stream integration (can't expand without definitions)

**Assessment**: ❌ Not recommended - contradicts DEC-001 goal (UMLS for definitions)

---

### Option B: Filter to Definitions-Only (~80K terms, 100% coverage)

**Strategy**: Keep ONLY terms with definitions (79,617 terms).

**Pros**:
- **100% definition coverage** by definition
- High-quality, research-relevant terms
- Clean Lex Stream integration
- Focused dataset (no anatomical bloat)

**Cons**:
- **Below target range** (80K vs 100K-150K)
- Loses 245K terms (mostly anatomical)
- Reduced anatomical granularity
- May miss some relevant structures

**SQL Filter**:
```python
concepts_with_defs = {
    cui: data for cui, data in concepts.items()
    if data.get('definition')
}
```

**Assessment**: ⚠️ Viable but below target - consider if definition quality is paramount

---

### Option C: Hybrid - Prioritize High-Coverage Sources (~100-150K terms, 60-80% coverage)

**Strategy**: Source-based filtering with quality tiers.

**Tier 1 (Keep ALL terms)**: High-coverage sources
- NCI (35,800 terms, 89% coverage)
- CSP (3,376 terms, 82% coverage)
- GO (54,118 terms, 70% coverage)
- CHV (9,117 terms, 65% coverage)
- AOD (3,564 terms, 57% coverage)
- MSH (13,739 terms, 54% coverage)
- OMIM (5,211 terms, 45% coverage)
- **Subtotal**: ~125K terms, ~65% coverage

**Tier 2 (Definitions-only)**: Low-coverage sources
- FMA (5,057 with defs)
- SNOMEDCT_US (10,502 with defs)
- UWDA (3,254 with defs)
- Others (remaining with defs)
- **Subtotal**: ~20K terms, 100% coverage

**Combined**: ~145K terms, 70-75% coverage

**Pros**:
- **Hits target range** (145K ≈ 100K-150K)
- **High definition coverage** (70-75% vs 24.5%)
- Keeps all high-quality sources (NCI, GO, MSH)
- Includes best anatomical terms (those with definitions)
- Balances volume and quality

**Cons**:
- Requires source-based filtering logic
- Some low-coverage sources lose terms without definitions
- More complex than binary filter

**Implementation**:
```python
HIGH_COVERAGE_SOURCES = {'NCI', 'CSP', 'GO', 'CHV', 'AOD', 'MSH', 'OMIM'}

filtered_concepts = {}
for cui, data in concepts.items():
    sources = data.get('sources', [])
    has_def = bool(data.get('definition'))

    # Tier 1: Keep all terms from high-coverage sources
    if any(s in HIGH_COVERAGE_SOURCES for s in sources):
        filtered_concepts[cui] = data
    # Tier 2: Keep terms with definitions from other sources
    elif has_def:
        filtered_concepts[cui] = data
```

**Assessment**: ✅ **Recommended** - balances volume, quality, and coverage goals

---

### Option D: Multi-Tier Import (Separate Files)

**Strategy**: Import multiple quality tiers as separate datasets.

**Tier 1 File** (`umls_tier1_definitions.csv`): 79,617 terms with definitions (100% coverage)

**Tier 2 File** (`umls_tier2_anatomical.csv`): 245,624 terms without definitions (anatomical reference)

**Pros**:
- Keep all extracted data
- Distinguish quality levels
- Flexible use cases (tier 1 for Lex Stream, tier 2 for reference)
- No data loss

**Cons**:
- More complex data management
- Two separate files to track
- Unclear which to prioritize
- May confuse integration

**Assessment**: ⚠️ Viable if need both quality definitions AND comprehensive anatomy

---

### Option E: Combine with NIF Definitions (Cross-Reference)

**Strategy**: Import UMLS with 24.5% coverage, backfill with NIF definitions (Day 1 import: 1,636 terms).

**Process**:
1. Import all 325K UMLS terms
2. Cross-reference with NIF database (term name matching)
3. Use NIF definitions to fill gaps where UMLS lacks definitions

**Pros**:
- Leverages existing NIF work (Day 1)
- Potentially increases coverage
- Combines strengths of both sources

**Cons**:
- Integration complexity (term matching challenges)
- NIF only has 1,636 terms (limited backfill potential)
- May introduce definition inconsistencies
- Engineering overhead

**Assessment**: ⚠️ High effort, uncertain benefit (NIF too small to significantly impact 245K gap)

---

## Decision Matrix

| Option | Terms | Coverage | Target Hit | Complexity | Quality | Lex Stream |
|--------|-------|----------|------------|------------|---------|------------|
| **A: As-is** | 325K | 24.5% | ✅ (2x) | Low | ❌ Low | ❌ Poor |
| **B: Defs-only** | 80K | 100% | ❌ (0.5x) | Low | ✅ High | ✅ Excellent |
| **C: Hybrid** | 145K | 70-75% | ✅ (1x) | Medium | ✅ High | ✅ Good |
| **D: Multi-tier** | 80K + 245K | 100% + 0% | ✅ / ❌ | High | ✅ / ❌ | ✅ / ❌ |
| **E: NIF merge** | 325K | ~27%? | ✅ (2x) | Very High | ⚠️ Mixed | ⚠️ Fair |

---

## Recommendation

**Selected Option**: **C - Hybrid Source Prioritization**

**Rationale**:
1. **Hits Target Range**: 145K terms (within 100K-150K)
2. **High Definition Coverage**: 70-75% (3x improvement over 24.5%)
3. **Preserves Quality Sources**: All NCI, GO, MSH terms (highest research value)
4. **Includes Best Anatomy**: FMA/SNOMEDCT terms that DO have definitions
5. **Lex Stream Compatible**: 70%+ coverage enables effective query expansion
6. **Aligns with DEC-001**: UMLS provides definitions, not just term lists
7. **Balanced Complexity**: Moderate implementation effort, clear logic

**Expected Outcome**:
- **Volume**: ~145K terms (target range)
- **Coverage**: 70-75% definitions (~105K with defs, ~40K without)
- **Quality**: High (prioritizes NCI 89%, GO 69%, MSH 54%)
- **Anatomy**: Best anatomical terms retained (those with definitions)

---

## Implementation Plan

### Phase 2A: Implement Hybrid Filtering

**Script**: `scripts/filter_umls_by_source_quality.py`

**Logic**:
1. Load `imports/umls/umls_concepts_intermediate.json` (325K terms)
2. Define high-coverage sources: {NCI, CSP, GO, CHV, AOD, MSH, OMIM}
3. Filter:
   - **Tier 1**: Keep ALL terms from high-coverage sources
   - **Tier 2**: Keep terms with definitions from other sources
4. Output: `imports/umls/umls_filtered_hybrid.json` (~145K terms)

**Validation**:
- Count terms by source
- Calculate new coverage percentage
- Sample 100 terms (50 tier 1, 50 tier 2)
- Verify coverage target (70-75%)

### Phase 2B: Map to NeuroDB-2 Schema

**Script**: Use existing `lib/schema_mapper.py` (from Day 1 NIF import)

**Mapping**:
- `Term` ← `preferred_term`
- `Definition` ← `definition`
- `Closest MeSH term` ← `mesh_code` (populate where available)
- `Synonym 1-3` ← `synonyms[0:3]`
- `Abbreviation` ← `abbreviations[0]`
- `Commonly Associated Term 1-8` ← Parse from MRREL.RRF (DEC-001 profiling)
- `Source` ← `sources` (join with `;`)
- `Source Priority` ← `UMLS`
- `Date Added` ← `2025-11-20`

### Phase 2C: Structural Validation

**Script**: Use existing `lib/validators.py`

**Checks**:
- 26-column schema compliance
- Required fields populated (Term, Definition for tier 1)
- CSV quoting/escaping correct
- No duplicate terms

### Phase 2D: Quality Profiling

**Metrics**:
- Definition coverage by source
- Synonym/abbreviation coverage
- MeSH code coverage
- Associated concepts coverage (after MRREL parsing)

---

## Success Criteria

✅ **Volume**: 100K-150K terms (target: ~145K)
✅ **Coverage**: 60-80% definitions (target: ~70-75%)
✅ **Quality**: High-coverage sources prioritized (NCI, GO, MSH)
✅ **Lex Stream**: 70%+ coverage enables query expansion
✅ **Schema**: 26-column NeuroDB-2 compliance
✅ **Validation**: Structural and quality checks pass

---

## Next Steps

1. ✅ **Decision Required**: User approves Option C (or selects alternative)
2. Implement hybrid filtering (`scripts/filter_umls_by_source_quality.py`)
3. Parse MRREL.RRF for associated concepts (DEC-001 profiling)
4. Map filtered data to NeuroDB-2 26-column schema
5. Run structural validation
6. Generate quality profile report
7. Update `docs/ontology-import-tracker.md`

---

## Alternative Decision Paths

If **Option B** selected (definitions-only):
- Skip hybrid filtering
- Proceed directly to schema mapping with 80K terms
- Accept below-target volume for maximum quality

If **Option A** selected (as-is):
- Skip all filtering
- Proceed to schema mapping with 325K terms
- Accept low coverage (24.5%)

If **Option D** selected (multi-tier):
- Create two output files (tier1_definitions.csv, tier2_anatomical.csv)
- Document usage guidelines for each tier
- More complex tracking/validation

---

---

## CRITICAL INVESTIGATION: Definition Field Usage in Lex Stream

**Date**: 2025-11-20 (Post-initial decision analysis)
**Trigger**: User question: "What's the function of the definitions in our database?"
**Method**: Agent-based codebase analysis of `/Users/sam/Lex-stream-2`

### Investigation Objective

**Key Questions**:
1. Is the "Definition" field mandatory for Lex Stream functionality?
2. Which agents actually USE the definition field vs just store it?
3. Would terms without definitions work for query expansion?

**Why This Matters**: Initial recommendation (Option C) assumed definitions were critical. If definitions are optional, Option A (all 325K terms) becomes viable.

---

### Findings: Definitions Are OPTIONAL

**Agent Analysis Results** (Explore agent, thorough mode):

#### Core Agents Do NOT Use Definitions

**1. Spell Checker Agent** (`agents.py:112-150`)
- **Accesses**: term names, synonyms, word_forms, abbreviations, MeSH terms, associated_terms
- **Does NOT access**: definition field ❌
- **Conclusion**: Validates against term names only

**2. Abbreviation Expander Agent** (`agents.py:602-609`)
- **Accesses**: abbreviation → expansion mappings
- **Does NOT access**: definition field ❌
- **Note**: Definitions stored in metadata (`convert_new_database.py:132`) but never read
- **Conclusion**: Expands abbreviations without definitions

**3. Synonym Finder Agent** (`agents.py:862-915`)
- **Accesses**: synonyms, associated_terms, word_forms, primary_term
- **Does NOT access**: definition field ❌
- **Conclusion**: Finds synonyms using synonym lists, not definitions

**4. MeSH Detector / Query Assembler** (`agents.py:1346-1352`)
- **Accesses**: mesh_terms mapping only
- **Does NOT access**: definition field ❌
- **Conclusion**: MeSH tagging uses code mappings, not definitions

#### Optional Feature Uses Definitions

**Component Detector Agent** (`services/component_detector.py`)
- **Uses**: associated_terms + definition for PICO categorization
- **Impact**: Optional feature for component-based queries (not default mode)
- **Fallback**: Works with term names alone if definitions missing
- **Conclusion**: Enhancement, not requirement

---

### Test Results: Missing Definitions Handled Gracefully

**Test Script Created**: `imports/umls/test_missing_definitions.py`

**Results**:
```bash
✅ SpellChecker initialized successfully
✅ AbbreviationExpander initialized successfully
✅ SynonymFinder initialized successfully
✅ QueryAssembler initialized successfully
✅ SpellChecker.process() works with empty definitions
✅ AbbreviationExpander.process() works with empty definitions
✅ SynonymFinder.process() works with empty definitions
✅ QueryAssembler.process() works with empty definitions
```

**Conclusion**: All core agents handle missing definitions without errors.

---

### Schema Validation Analysis

**Finding**: Definition field NOT enforced

**Evidence**: `services/terms_loader.py:47-50`
```python
# Validates only top-level keys:
required_keys = ['terms', 'abbreviations', 'mesh_terms', 'metadata']
# No validation for 'definition' field presence in term entries
```

**Current Dataset**: 569 terms, 100% definition coverage (quality achievement, not technical requirement)

---

### Documentation Discrepancy

**NEUROSCIENCE_LEXICON.md** (Quality Standard):
```markdown
| `definition` | string | ✅ | Scientific definition (50-200 words) |
```

**DATABASE_CREATION_GUIDE.md** (Functional Requirement):
```markdown
| `definition` | "string (recommended)" | // Helps component detection
```

**Interpretation**:
- Quality docs describe aspiration (100% coverage ideal)
- Creation guide describes reality (recommended, not required)
- Current 100% coverage is quality achievement, not technical necessity

---

### What Lex Stream Actually Needs

**Required Fields** (for core functionality):
- ✅ `primary_term` - Term name
- ✅ `synonyms` - Synonym list
- ✅ `abbreviations` - Abbreviation mappings
- ✅ `mesh_code` - MeSH term mapping
- ✅ `associated_terms` - Related concepts
- ✅ `word_forms` - Noun/verb/adjective variants

**Optional Fields** (enhance features):
- ⚠️ `definition` - Used by Component Detector only (optional feature)

**Not Used**:
- ❌ Definition for spell checking
- ❌ Definition for abbreviation expansion
- ❌ Definition for synonym finding
- ❌ Definition for MeSH detection

---

## REVISED RECOMMENDATION

### **NEW: Option A - Import All 325K Terms**

**Previous Assessment**: ❌ "Poor quality, defeats purpose"
**Revised Assessment**: ✅ **RECOMMENDED** - Maximizes coverage for actual requirements

**Why Recommendation Changed**:
1. **Definitions not required** for 4 core agents (spell check, abbreviation, synonym, MeSH)
2. **Component Detector optional** - users generate effective queries without PICO categorization
3. **Coverage > Quality** for search - more terms = better synonym/abbreviation expansion
4. **Graceful degradation** - system handles missing definitions without errors
5. **Future-proof** - can backfill definitions later via Wikipedia/AI generation

**Updated Decision Matrix**:

| Option | Terms | Def Coverage | Target Hit | Complexity | **Core Agents** | **Component Det** |
|--------|-------|--------------|------------|------------|-----------------|-------------------|
| **A: As-is** ✅ | 325K | 24.5% | ✅ (2x) | Low | ✅ **Excellent** | ⚠️ 24.5% |
| **B: Defs-only** | 80K | 100% | ❌ (0.5x) | Low | ⚠️ Reduced | ✅ 100% |
| **C: Hybrid** | 145K | 70-75% | ✅ (1x) | Medium | ✅ Good | ✅ 70% |

**Key Insight**: Original matrix rated Lex Stream compatibility based on **definition coverage**. Actual code analysis shows compatibility depends on **term coverage**, not definition coverage.

---

## Revised Implementation Plan

### Phase 2: Import All 325K Terms

**Strategy**: Maximum coverage, mark terms needing definition enrichment

**Steps**:
1. Import all 325,241 UMLS terms (skip hybrid filtering)
2. Mark terms lacking definitions:
   ```python
   if not term_data.get('definition', '').strip():
       term_data['definition'] = "(pending enrichment)"
       term_data['needs_definition'] = True
   ```
3. Map to NeuroDB-2 26-column schema
4. Validate structural compliance
5. Profile data quality (coverage by field type)

**Quality Improvement Roadmap** (Future):
- **Phase 2A**: Backfill top 10K most-queried terms (Wikipedia/NINDS)
- **Phase 2B**: AI-assisted definition generation (GPT-4 with verification)
- **Phase 2C**: Community contribution workflow for domain experts

---

## Updated Success Criteria

✅ **Volume**: 300K+ terms (target exceeded)
✅ **Core Agent Coverage**: 100% (all terms usable)
✅ **Component Detector**: 24.5% (optional feature, acceptable degradation)
✅ **Spell Check**: Maximum dictionary size
✅ **Abbreviation Expansion**: Maximum acronym coverage
✅ **Synonym Finding**: Maximum synonym relationships
✅ **MeSH Detection**: 13,739 terms with codes (4.2% coverage)

❌ ~~**Definition Coverage**: 60-80%~~ (not required for core functionality)

---

## Status Tracking

**Current Status**: ✅ **APPROVED & IMPLEMENTED - Option A**

**Original Recommendation** (Pre-Investigation): Option C (145K terms, 70% coverage)
**Revised Recommendation** (Post-Investigation): Option A (325K terms, 24.5% coverage)

**Change Rationale**: Lex Stream codebase analysis revealed definitions are optional, not required. Maximum term coverage more valuable than definition coverage for primary use case (query expansion).

**Files Generated**:
- `imports/umls/coverage_analysis_report.md` - Statistical analysis
- `imports/umls/coverage_investigation_findings.md` - Investigation summary
- `docs/decisions/2025-11-20-umls-coverage-strategy-decision.md` - This document
- **NEW**: Lex Stream codebase analysis (via Explore agent)

**Blocks**:
- Phase 2 implementation (schema mapping, validation)
- MRREL.RRF parsing (DEC-001)
- UMLS import completion

**Decision Status**: ✅ **APPROVED - Option A** (User confirmed 2025-11-20)

---

## References

- **DEC-001**: Associated Concepts Profiling Strategy (pending MRREL parsing)
- **DEC-002**: UMLS CUI Filter Count Decision (Option B selected)
- **Phase 1 Results**: 325,241 terms extracted, 24.5% coverage
- **Investigation Report**: `imports/umls/coverage_investigation_findings.md`
- **Lex Stream Codebase**: `/Users/sam/Lex-stream-2` (analyzed via Explore agent)
- **Lex Stream Integration Status**: 95% test pass rate (production-ready)
