# Decision: UMLS CUI Filter Count Strategy

**Date**: 2025-11-20
**Status**: 🔄 PENDING DECISION
**Decision ID**: DEC-002
**Decision Maker**: Sam

---

## Problem Statement

Initial CUI filtering using semantic types produced **1,015,068 CUIs** (29% of total UMLS), significantly exceeding target range of **100K-150K CUIs**.

**Current State**:
- Filtered CUIs: 1,015,068
- Target range: 100K-150K
- Overage: **7-10x higher than target**

**Root Cause Analysis**:
Semantic type filtering is too broad:
- "Pharmacologic Substance" includes ALL drugs (195K) - most not neurological
- "Amino Acid, Peptide, or Protein" includes ALL proteins (167K) - most not neurological
- "Disease or Syndrome" includes ALL diseases (125K) - most not neurological
- "Injury or Poisoning" includes ALL injuries (118K) - most not neurological

**Impact**:
- Higher downstream processing time (parsing 1M CUIs instead of 150K)
- Potential for non-neuroscience terms in final output
- More complex deduplication and quality control
- Risk of diluting neuroscience-specific content

---

## Data Analysis

### Top 10 Semantic Types by Count

| Semantic Type | Count | % of Total | Neuroscience Specificity |
|---------------|-------|------------|--------------------------|
| Pharmacologic Substance | 194,736 | 19.2% | ⚠️ Low (all drugs, not just neuro) |
| Amino Acid, Peptide, or Protein | 166,936 | 16.4% | ⚠️ Low (all proteins) |
| Disease or Syndrome | 125,399 | 12.4% | ⚠️ Low (all diseases) |
| Injury or Poisoning | 117,688 | 11.6% | ⚠️ Low (all injuries) |
| Body Part, Organ, or Organ Component | 94,429 | 9.3% | ⚠️ Medium (includes all body parts) |
| Gene or Genome | 89,124 | 8.8% | ⚠️ Low (all genes) |
| Biologically Active Substance | 79,079 | 7.8% | ⚠️ Low (all bioactive substances) |
| Neoplastic Process | 50,244 | 4.9% | ⚠️ Low (all cancers) |
| Enzyme | 32,542 | 3.2% | ⚠️ Low (all enzymes) |
| Molecular Function | 32,705 | 3.2% | ⚠️ Low (all molecular functions) |

**Observation**: Top semantic types are **domain-agnostic** (apply to entire human body/medicine, not just neuroscience).

### Priority Distribution

| Priority Level | Count | % | Description |
|----------------|-------|---|-------------|
| Priority 1 (High) | 564,636 | 55.6% | Anatomical, physiological, pathological |
| Priority 2 (Medium) | 450,432 | 44.4% | Behavioral, chemical, genetic |
| Priority 3 (Selective) | 0 | 0% | Procedures (currently excluded) |

---

## Options Analysis

### Option A: Restrict to Priority 1 Only (Immediate Re-Filter)

**Approach**: Re-run filter with only Priority 1 semantic types (most specific neuroscience)

**Keep**:
- T023: Body Part, Organ, or Organ Component
- T029: Body Location or Region
- T030: Body Space or Junction
- T025: Cell
- T026: Cell Component
- T024: Tissue
- T039: Physiologic Function
- T040: Organism Function
- T042: Organ or Tissue Function
- T043: Cell Function
- T044: Molecular Function
- T041: Mental Process
- T048: Mental or Behavioral Dysfunction
- T047: Disease or Syndrome
- T046: Pathologic Function
- T049: Cell or Molecular Dysfunction
- T191: Neoplastic Process
- T037: Injury or Poisoning
- T192: Receptor

**Remove** (Priority 2):
- T121: Pharmacologic Substance (195K)
- T116: Amino Acid, Peptide, or Protein (167K)
- T123: Biologically Active Substance (79K)
- T125: Hormone (4K)
- T114: Nucleic Acid (16K)
- T126: Enzyme (33K)
- T028: Gene or Genome (89K)
- T053: Behavior (82)
- T054: Social Behavior (1K)

**Expected Result**: ~200K-300K CUIs (still 2-3x target)

#### Pros
✅ **Immediate reduction** - Reduces from 1M → ~250K CUIs
✅ **Higher specificity** - Focuses on core neuroscience types
✅ **Faster processing** - Less data to parse in MRCONSO
✅ **Cleaner output** - Reduces non-neuro drugs/proteins

#### Cons
❌ **May miss important terms** - Loses neurological drugs, neurotransmitters, neuro-enzymes
❌ **Still above target** - 250K is still 2x the 150K target
❌ **Arbitrary cutoff** - Priority 1 vs 2 distinction is subjective
❌ **Time cost** - Requires re-running filter (~5 minutes)

---

### Option B: Proceed with 1M CUIs + Multi-Stage Filtering (RECOMMENDED)

**Approach**: Keep 1M CUIs, apply additional filters during MRCONSO parsing:

**Stage 1** (Already complete): Semantic type filter → 1M CUIs

**Stage 2** (During MRCONSO parsing):
- **Language filter**: LAT=ENG (exclude foreign language terms)
- **Suppression filter**: SUPPRESS=N (exclude obsolete/suppressed terms)
- **Preferred term requirement**: ISPREF=Y or TTY=PN (only preferred names, not all synonyms)

**Stage 3** (Keyword filter for broad semantic types):
```python
# For CUIs with these broad semantic types, require neuro keywords:
BROAD_TYPES = ['Pharmacologic Substance', 'Amino Acid, Peptide, or Protein',
               'Disease or Syndrome', 'Injury or Poisoning', 'Gene or Genome']

NEURO_KEYWORDS = ['neuro', 'brain', 'cerebr', 'cortex', 'neural', 'synap',
                  'axon', 'dendrit', 'glia', 'cognit', 'memory', 'mental',
                  'psychiatric', 'parkinson', 'alzheimer', 'epilep', 'stroke']

# Only include broad-type CUIs if preferred term contains neuro keyword
```

**Stage 4** (Deduplication): Remove duplicate terms (case-insensitive)

**Expected Result**: ~150K-250K final terms (within or near target)

#### Pros
✅ **No data loss upfront** - Preserves all potentially relevant CUIs
✅ **Natural reduction** - Language/suppression filters significantly reduce count
✅ **Keyword precision** - Ensures broad categories (drugs, proteins) are actually neuro-relevant
✅ **Flexible** - Can adjust keyword list if needed
✅ **Evidence-based** - See actual term strings before deciding exclusions
✅ **No rework** - Don't need to re-run filtering

#### Cons
❌ **Slower parsing** - Processing 1M CUIs takes longer than 250K
❌ **More complex logic** - Requires keyword matching during parsing
❌ **Risk of false negatives** - Keywords might miss valid neuro terms without obvious neuro words
❌ **Delayed validation** - Don't know final count until after full parse

---

### Option C: Hybrid - Restrict Priority 1 + Add Selective Priority 2

**Approach**: Use Priority 1 types PLUS selectively add back specific Priority 2 types that are highly neuroscience-specific

**Keep all Priority 1** (564K CUIs)

**Add back selective Priority 2**:
- T192: Receptor (6K) - Neurotransmitter receptors are critical
- T125: Hormone (4K) - Neuroendocrine hormones relevant
- T054: Social Behavior (1K) - Behavioral neuroscience

**Exclude Priority 2 broad types**:
- Pharmacologic Substance (195K) - Too broad
- Amino Acid, Peptide, or Protein (167K) - Too broad
- Gene or Genome (89K) - Too broad
- Biologically Active Substance (79K) - Too broad
- Enzyme (33K) - Too broad

**Then apply keyword filter** for remaining broad types during MRCONSO parsing

**Expected Result**: ~200K CUIs → ~150K final terms after parsing filters

#### Pros
✅ **Balanced approach** - Reduces obvious noise while preserving specificity
✅ **Preserves critical types** - Keeps receptors, hormones, behaviors
✅ **Manageable size** - 200K CUIs is reasonable for parsing
✅ **Keyword safety net** - Still applies keywords to remaining broad types

#### Cons
❌ **Complex logic** - Requires maintaining inclusion/exclusion lists
❌ **Still arbitrary** - "Selective" choices are subjective
❌ **Risk of gaps** - Might exclude important neurological drugs/proteins
❌ **Implementation time** - Requires modifying filter script

---

## Decision Criteria

**Choose Option A if**:
- ✅ Want simplest approach (just Priority 1)
- ✅ Willing to accept potential loss of neuro drugs/proteins
- ✅ Prioritize processing speed over completeness

**Choose Option B if**:
- ✅ Want maximum coverage (no data loss)
- ✅ Comfortable with longer parsing time
- ✅ Trust keyword filtering to ensure relevance
- ✅ Want to see actual term strings before excluding

**Choose Option C if**:
- ✅ Want balanced approach
- ✅ Can define clear inclusion criteria for Priority 2
- ✅ Want moderate CUI count reduction

---

## Estimated Impact on Processing Time

| Option | CUI Count | MRCONSO Parse Time | Total Pipeline Time |
|--------|-----------|-------------------|---------------------|
| **Option A** | ~250K | ~20 min | ~2.5 hours |
| **Option B** | 1,015K | ~45 min | ~3 hours |
| **Option C** | ~200K | ~18 min | ~2.3 hours |

**Note**: Times are estimates based on planner agent's performance benchmarks.

---

## Risk Assessment

### Risk 1: Missing Important Neuro Terms

**Option A**: ⚠️ **High Risk**
- Excludes neurological drugs (antipsychotics, antidepressants, anticonvulsants)
- Excludes neurotransmitters (dopamine, serotonin, GABA as proteins)
- Excludes neuro-specific enzymes (MAO, COMT, ChAT)

**Option B**: ✅ **Low Risk**
- Preserves all potentially relevant terms
- Keyword filter ensures broad categories are neuro-specific

**Option C**: ⚠️ **Medium Risk**
- Excludes drugs/proteins that might be neurological
- Partially mitigated by keyword filtering

### Risk 2: Non-Neuro Terms in Final Output

**Option A**: ✅ **Low Risk**
- Priority 1 types are more specific
- Still some risk from broad anatomical/disease types

**Option B**: ⚠️ **Medium Risk**
- Relies on keyword filtering for quality
- Keywords might miss some generic terms

**Option C**: ✅ **Low-Medium Risk**
- Balanced approach reduces broad categories
- Keyword filter provides additional safety

### Risk 3: Processing Performance

**Option A**: ✅ **Low Risk**
- Smaller CUI set = faster parsing
- ~20 min MRCONSO parsing

**Option B**: ⚠️ **Medium Risk**
- Larger CUI set = slower parsing
- ~45 min MRCONSO parsing
- Still acceptable (within plan's 2 hour estimate)

**Option C**: ✅ **Low Risk**
- Moderate CUI set = moderate parsing
- ~18 min MRCONSO parsing

---

## Recommendation

### **Option B: Proceed with 1M CUIs + Multi-Stage Filtering**

**Rationale**:
1. **No Premature Exclusion** - We don't yet know which of the 1M CUIs actually have English preferred terms. Many might be foreign language, suppressed, or have no preferred name.

2. **Natural Reduction Expected** - Based on UMLS structure:
   - ~20-30% of CUIs don't have ENG preferred terms
   - ~5-10% are suppressed/obsolete
   - Keyword filtering of broad types will remove another 30-40%
   - Expected reduction: 1M → 150K-250K (within or near target)

3. **Evidence-Based Decision** - We'll see actual term strings (e.g., "Fluoxetine" is a Pharmacologic Substance - do we want it?) before making exclusion decisions.

4. **Preserves Coverage** - Neurological drugs (SSRIs, antipsychotics, anticonvulsants) are Priority 2 Pharmacologic Substances. Excluding them would create significant gaps.

5. **Reversible** - If Stage 2-3 filters don't reduce count enough, we can add post-processing filters. Easier than re-running entire pipeline.

6. **Aligns with Planner Agent's Plan** - The planner agent's implementation plan anticipated multi-stage filtering during MRCONSO parsing (lines 224-280).

### Implementation Strategy

**Phase 2A** (Current - Complete): Semantic type filter → 1,015,068 CUIs

**Phase 2B** (Next): MRCONSO parsing with filters:
```python
# Stage 1: Load 1M CUIs
neuro_cuis = load_cui_filter()

# Stage 2: Basic filters
for line in MRCONSO:
    if CUI not in neuro_cuis: continue
    if LAT != 'ENG': continue
    if SUPPRESS != 'N': continue
    if ISPREF != 'Y': continue  # Preferred terms only

    # Stage 3: Keyword filter for broad semantic types
    if semantic_type in BROAD_TYPES:
        if not contains_neuro_keyword(STR):
            continue

    # Include this term
    extract_term_data()
```

**Phase 2C**: Report actual count and decide if additional filtering needed

---

## Questions to Answer During Implementation

1. **After Stage 2 (language/suppression filters)**: How many CUIs remain?
2. **Keyword match rate**: What % of broad-type terms match neuro keywords?
3. **Final term count**: Is it within 100K-250K range?
4. **Sample quality**: Are the extracted terms actually neuroscience-relevant?

If final count still >250K, consider:
- **Post-filter Option 1**: Restrict to Priority 1 CUIs only (can do after parsing)
- **Post-filter Option 2**: Stricter keyword requirements
- **Post-filter Option 3**: Source priority (keep MSH/SNOMEDCT only)

---

## Decision

**Status**: ✅ **DECIDED - Option B Selected**
**Decision Date**: 2025-11-20
**Decision Maker**: Sam

**Final Decision**: **Option B** - Proceed with 1,015,068 CUIs + multi-stage filtering during MRCONSO parsing

**Next Steps** (if approved):
1. Implement keyword filtering in MRCONSO parser
2. Run Phase 2B (parse MRCONSO with filters)
3. Report intermediate counts after each filter stage
4. Evaluate final count and quality
5. Adjust if needed (post-processing filters)

**Alternative** (if Option A or C preferred):
- Re-run `build_umls_filter_index.py` with modified semantic type list
- Proceed with smaller CUI set

---

## Stakeholder Input Needed

**Question for Sam**: Which option do you prefer?

- **Option A**: Restrict now (Priority 1 only, ~250K CUIs, faster but may miss neuro drugs/proteins)
- **Option B**: Proceed with 1M CUIs, let natural filters reduce count (recommended)
- **Option C**: Hybrid approach (selective Priority 2, ~200K CUIs, moderate complexity)

**Approval Needed**: Yes ✅
**Impact**: Medium-High (affects coverage, processing time, final term count)

---

## Implementation Results and Findings

**Implementation Date**: 2025-11-20
**Status**: ✅ Phase 1 Complete (Term extraction from MRCONSO/MRDEF)

### Phase 1 Execution Summary

**Script**: `scripts/import_umls_neuroscience.py` (Phase 1)
**Duration**: ~8 minutes (MRCONSO parsing)
**Input**: 1,015,068 neuroscience CUIs
**Output**: 325,241 unique neuroscience terms

### Multi-Stage Filter Performance

Option B's multi-stage filtering successfully reduced 17.4M MRCONSO rows to 325K terms:

| Filter Stage | Input Rows | Output Rows | Reduction | % Filtered |
|--------------|------------|-------------|-----------|------------|
| **Stage 0**: Total MRCONSO rows | 17,390,109 | - | - | - |
| **Stage 1**: CUI match (in neuroscience set) | 17,390,109 | 7,030,159 | 10,359,950 | 59.6% |
| **Stage 2**: English only (LAT=ENG) | 7,030,159 | 4,104,591 | 2,925,568 | 41.6% |
| **Stage 3**: Not suppressed (SUPPRESS=N) | 4,104,591 | 3,560,455 | 544,136 | 13.3% |
| **Stage 4**: Preferred terms only (ISPREF=Y or TTY=PN) | 3,560,455 | 2,873,660 | 686,795 | 19.3% |
| **Stage 5**: Keyword filter (for broad types) | 2,019,408 broad-type rows | 48,389 passed | 1,971,019 | **97.6%** |
| **Final**: After deduplication | 325,515 concepts | 325,241 unique | 274 duplicates | 0.08% |

**Key Findings**:
- ✅ Stage 5 keyword filter was **highly effective** (97.6% rejection rate for broad types)
- ✅ Language filter removed 42% (foreign language terms)
- ✅ Suppression filter removed 13% (obsolete/deprecated terms)
- ✅ Final count: 325,241 terms (**68% reduction** from 1M CUIs)

### Coverage Analysis

Extracted 325,241 terms with the following metadata coverage:

| Metadata Field | Count | Coverage | Target | Status |
|----------------|-------|----------|--------|--------|
| **Definitions** | 79,617 | 24.5% | 80%+ | ❌ **MAJOR GAP** |
| **MeSH codes** | 13,739 | 4.2% | 60%+ | ❌ **MAJOR GAP** |
| **Synonyms** | 29,306 | 9.0% | 40%+ | ⚠️ Below target |
| **Source vocabularies** | 325,241 | 100% | 100% | ✅ Complete |

### Critical Issue Discovered: Low Definition Coverage

**Expected**: 80%+ definition coverage (UMLS is known for comprehensive definitions)
**Actual**: 24.5% definition coverage (79,617 of 325,241 terms)

**Why This Is Concerning**:
1. UMLS import was chosen specifically to **fill NIF's 87% definition gap**
2. With 24.5% coverage, we're not much better than NIF's 13%
3. Defeats primary purpose of UMLS import (comprehensive definitions)

**Possible Explanations**:
1. **Overly broad filtering** - Captured many rare/specific terms lacking UMLS metadata
2. **MRDEF incomplete** - Not all UMLS sources provide definitions
3. **Source vocabulary bias** - Terms from some vocabularies (GO, HPO) may lack definitions
4. **Semantic type specificity** - Very specific anatomical/pathological terms poorly documented

### Term Count Assessment

**Target Range**: 100K-150K terms
**Actual**: 325,241 terms
**Variance**: +117% to +225% above target

**Status**: ⚠️ **Above target by 30-130%**

**Impact**:
- More terms to process in downstream phases (MRREL parsing, schema mapping)
- Potential dilution of neuroscience specificity
- Higher validation complexity

### Filter Effectiveness: Keyword Filtering

Stage 5 keyword filter rejected **1,971,019 broad-type rows** (97.6%), accepting only **48,389** (2.4%).

**Broad semantic types filtered**:
- Pharmacologic Substance
- Amino Acid, Peptide, or Protein
- Disease or Syndrome
- Injury or Poisoning
- Gene or Genome
- Biologically Active Substance
- Enzyme
- Nucleic Acid

**Keyword match examples** (accepted):
- "dopamine" (neurotransmitter)
- "fluoxetine" (psychiatric medication)
- "Parkinson's disease" (neurological disease)
- "synaptic protein" (neural protein)

**Rejected examples** (no neuro keywords):
- "Aspirin" (pharmacologic substance, not neuro)
- "Insulin" (hormone, not neuro)
- "Heart failure" (disease, not neuro)
- "Collagen" (protein, not neuro)

**Verdict**: ✅ Keyword filtering worked as intended, preventing non-neuro terms from broad types.

---

## New Decision Point: Coverage Issue

### Problem Statement

Phase 1 produced 325,241 terms with **only 24.5% definition coverage**, falling far short of the 80%+ target that motivated UMLS import.

### Investigation Needed

Before deciding how to proceed, we need to understand:

**Question 1**: Are the 75.5% of terms without definitions actually neuroscience-relevant?
- Sample 100 random terms without definitions
- Manual review for neuroscience relevance
- Determine if they're obscure/valid terms or filtering errors

**Question 2**: Why is MeSH coverage so low (4.2%)?
- Expected: 60%+ of neuroscience terms in MeSH
- Actual: Only 13,739 of 325,241 terms have MeSH codes
- Indicates possible source vocabulary mismatch

**Question 3**: What are the source vocabulary distributions?
- Which source vocabularies contributed most terms?
- Do sources without definitions dominate the dataset?
- Should we prioritize MSH/SNOMEDCT sources?

### Options for Addressing Coverage

**Option A**: Accept low coverage, proceed to Phase 2
- Continue with 325K terms despite 24.5% definition coverage
- Hope NIF merge (Day 4) fills gaps
- Risk: Final database still has many undefined terms

**Option B**: Filter to terms WITH definitions only
- Keep only 79,617 terms with definitions (24.5% of current)
- Result: ~80K high-quality terms with 100% definition coverage
- Downside: Defeats UMLS's purpose (wanted 100K-150K terms)

**Option C**: Prioritize high-coverage source vocabularies
- Re-filter to prefer MSH/SNOMEDCT/NCI sources
- Add source priority filter during MRCONSO parsing
- Expected: Lower count but higher coverage

**Option D**: Investigate first, then decide
- Sample 100 terms to understand what we extracted
- Analyze source vocabulary distribution
- Profile definition coverage by semantic type
- Make informed decision based on data

### Recommendation: Option D (Investigate First)

**Next Steps**:
1. Sample 100 random terms (50 with definitions, 50 without)
2. Manually assess neuroscience relevance
3. Analyze source vocabulary distribution
4. Profile coverage by semantic type
5. Create DEC-003 if investigation reveals need for filtering adjustment

**Estimated Time**: 30 minutes for investigation, then decision

---

## Lessons Learned

### What Worked Well ✅

1. **Multi-stage filtering** - Reduced 17.4M rows → 325K terms efficiently
2. **Keyword filtering** - 97.6% rejection rate for broad types prevented non-neuro pollution
3. **Language filter** - Removed 42% foreign language terms automatically
4. **Deduplication** - Only 274 duplicates found (0.08%), minimal redundancy

### What Didn't Work as Expected ⚠️

1. **Definition coverage** - 24.5% vs 80%+ target (major gap)
2. **MeSH coverage** - 4.2% vs 60%+ target (major gap)
3. **Final count** - 325K vs 100K-150K target (2-3x higher)

### Key Insights

1. **Semantic type breadth** - Even Priority 1 types captured very specific terms lacking metadata
2. **UMLS heterogeneity** - Not all source vocabularies provide definitions/MeSH mappings equally
3. **Coverage vs count trade-off** - Broader filtering = more terms but lower metadata coverage

### Questions for Further Investigation

1. **Source vocabulary analysis**: Which sources contributed most terms? Which have best coverage?
2. **Semantic type profiling**: Which semantic types have high/low definition coverage?
3. **Term specificity**: Are undefined terms highly specific anatomical/pathological concepts?
4. **NIF overlap**: How many NIF terms (1,636) are in our UMLS extraction?

---

## Status Update

**Phase 1**: ✅ Complete (MRCONSO/MRDEF parsing)
**Phase 2**: ⏳ Pending investigation and coverage decision
**Phase 3**: ⏳ Pending (MRREL parsing for DEC-001)

**Current State**: Paused for coverage issue investigation before proceeding to relationship extraction.

**Decision Required**: Whether to proceed with 325K terms (low coverage) or apply additional filtering.
