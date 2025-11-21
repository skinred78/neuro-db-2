# UMLS Coverage Investigation Findings

**Date**: 2025-11-20
**Investigation**: Why definition coverage is only 24.5% instead of 80%+

---

## Root Cause Identified

The low coverage is driven by **anatomical ontologies** that focus on hierarchical structure rather than textual definitions.

### Primary Culprits

1. **FMA (Foundational Model of Anatomy)**
   - Volume: 99,074 terms (30% of all extracted terms)
   - Coverage: 5.1% (5,057 terms with definitions)
   - Nature: Ultra-granular anatomical hierarchy
   - Example: "Cartilage of right inferior surface of posterolateral part of body of second thoracic vertebra"

2. **UWDA (University of Washington Digital Anatomica)**
   - Volume: 60,201 terms (18% of all extracted terms)
   - Coverage: 5.4% (3,254 terms with definitions)
   - Nature: Anatomical hierarchy without textual definitions
   - Example: "Right first superficial digital artery"

3. **SNOMEDCT_US (SNOMED Clinical Terms)**
   - Volume: 67,590 terms (21% of all extracted terms)
   - Coverage: 15.5% (10,502 terms with definitions)
   - Nature: Clinical terminology, includes anatomical structures
   - Example: "Structure of lateral meniscus of left knee joint"

**Combined Impact**: These 3 sources account for 69% of extracted terms (226,865 of 325,241) but only 8.2% have definitions.

---

## High-Quality Sources (Lower Volume)

| Source | Terms | Coverage | Quality |
|--------|-------|----------|---------|
| **NCI** | 35,800 | 89.1% | Excellent neuroscience content |
| **CSP** | 3,376 | 81.6% | High-quality medical definitions |
| **GO** | 54,118 | 69.5% | Gene Ontology - excellent molecular/cellular |
| **CHV** | 9,117 | 64.6% | Consumer health vocabulary |
| **AOD** | 3,564 | 56.5% | Alcohol/drug abuse terms |
| **MSH** | 13,739 | 54.1% | MeSH - authoritative but only 13K terms |
| **OMIM** | 5,211 | 45.1% | Genetic disorders |
| **MTH** | 39,063 | 40.5% | Metathesaurus-created terms |

---

## Coverage by Semantic Type

**Low-Coverage Types** (Priority 1 Anatomical):
- Body Part, Organ, or Organ Component: 93,585 terms (5.9% coverage)
- Body Location or Region: 26,866 terms (5.6% coverage)
- Body Space or Junction: 10,176 terms (6.1% coverage)
- Pathologic Function: 28,772 terms (6.0% coverage)

**High-Coverage Types** (Priority 1 Functional):
- Cell or Molecular Dysfunction: 5,472 terms (75.7% coverage)
- Cell Component: 7,955 terms (67.3% coverage)
- Molecular Function: 27,103 terms (65.5% coverage)
- Cell Function: 17,166 terms (65.4% coverage)

---

## Sample Term Assessment

### Terms WITH Definitions (High Quality)
- "locus ceruleus formation" (GO) - developmental biology
- "vascular endothelial growth factor signaling pathway" (GO) - molecular signaling
- "Neuroeffector Junction" (MSH) - neuroscience anatomy
- "Receptor Down-Regulation" (MSH) - physiology
- "Giant Cell Tumors" (MSH, NCI) - pathology
- "neurodegeneration with brain iron accumulation 4 protein" (NCI) - neurogenetics

**Assessment**: High neuroscience relevance, textbook-quality definitions.

### Terms WITHOUT Definitions (Ultra-Granular Anatomy)
- "Cartilage of right inferior surface of posterolateral part of body of second thoracic vertebra" (FMA)
- "Space of posterior part of superior mediastinum" (FMA)
- "Entire lower segmental branch of renal artery" (SNOMEDCT_US)
- "Structure of interosseous crural nerve" (FMA)
- "Cementum of first upper molar tooth" (FMA)
- "composite Hodgkin's and non-Hodgkin's lymphoma of pleura" (MEDCIN)
- "Natrol Cognium Memory Extra Strength" (MMSL) - commercial drug brand

**Assessment**: Mix of ultra-granular anatomical terms, clinical codes, and brand names. Low neuroscience research value.

---

## Why This Happened

Our filtering strategy correctly captured neuroscience-relevant **semantic types**, but didn't distinguish between:

1. **Research-level neuroscience terms** (processes, pathways, disorders) - typically have definitions
2. **Ultra-granular anatomical structures** (specific nerve branches, tissue layers) - rarely have textual definitions in UMLS

FMA and UWDA are Priority 1 types ("Body Part, Organ, or Organ Component") so they passed through filtering, but they're structured hierarchies, not encyclopedic resources.

---

## Research Agent Assessment

**Question**: Would a research agent help investigate this?

**Answer**: **No, research agent NOT needed.**

The investigation is complete. The coverage pattern is now fully understood:

1. **Root Cause**: Anatomical ontologies (FMA, UWDA) lack textual definitions by design
2. **Evidence**: 30% of terms from FMA, 18% from UWDA, both <6% coverage
3. **Semantic Types**: Anatomical types dominate volume but have low coverage
4. **Sample Assessment**: Low-coverage terms are ultra-granular anatomy, not core neuroscience

A research agent would confirm what we already know: FMA/UWDA are structural ontologies, not definition sources. The 80%+ expectation was based on core medical terms, not granular anatomical hierarchies.

**What we need**: A **decision** on how to proceed, not more research.

---

## Decision Options

### Option A: Proceed As-Is (325K terms, 24.5% coverage)
- **Pros**: Maximum coverage of anatomical structures
- **Cons**: 75% of terms lack definitions (defeats UMLS import goal)
- **Use Case**: If NeuroDB-2 needs comprehensive anatomical granularity

### Option B: Filter to Definitions-Only (~80K terms, 100% coverage)
- **Pros**: Every term has a quality definition
- **Cons**: Lose 245K terms (mostly anatomical), drops below 100K-150K target
- **Use Case**: If definitions are mandatory (for Lex Stream query expansion)

### Option C: Hybrid - Prioritize High-Coverage Sources (~100-150K terms, 60-80% coverage)
- **Strategy**: Keep ALL terms from high-coverage sources (NCI, GO, MSH, CSP, OMIM), then add best FMA/SNOMEDCT terms (those WITH definitions)
- **Pros**: Balances volume and quality, stays in target range
- **Cons**: Requires source-based filtering logic

### Option D: Multi-Tier Import
- **Tier 1**: Terms with definitions (80K) - import to NeuroDB-2
- **Tier 2**: Anatomical terms without definitions (245K) - separate file for reference/linking
- **Pros**: Keep all data, distinguish quality levels
- **Cons**: More complex data management

### Option E: Combine with NIF Definitions
- **Strategy**: Import UMLS with 24.5% coverage, use NIF definitions to backfill
- **Requires**: Cross-reference UMLS terms with NIF database (from Day 1)
- **Pros**: Leverage existing NIF definition coverage
- **Cons**: Integration complexity

---

## Recommendation

**Recommended**: **Option C - Hybrid Source Prioritization**

**Rationale**:
1. **Maintains Target Range**: 100K-150K terms (vs 325K bloat)
2. **Maximizes Definition Coverage**: 60-80% (vs 24.5%)
3. **Preserves Quality**: Keeps all NCI, GO, MSH terms (89%, 69%, 54% coverage)
4. **Includes Best Anatomy**: FMA/SNOMEDCT terms that DO have definitions
5. **Aligns with DEC-001 Goal**: UMLS should provide definitions (not just term lists)

**Next Steps**:
1. Create DEC-003: UMLS Coverage Strategy Decision
2. Implement hybrid filtering if Option C approved
3. Validate output quality (sample 100 terms from filtered set)
4. Proceed to MRREL.RRF parsing (DEC-001 profiling)

---

## Files Generated

- `imports/umls/coverage_analysis_report.md` - Full statistical report
- `imports/umls/coverage_investigation_findings.md` - This summary (decision-ready)
