# Decision: NIF Associated Terms Handling

**Date**: 2025-11-19
**Status**: ✅ DECIDED - Option A Implemented
**Decision Date**: 2025-11-19
**Decision Maker**: Sam

---

## Problem Statement

NIF-GrossAnatomy.ttl provides hierarchical taxonomy relationships (parent/child classes) extracted from RDF ontology structure. The importer currently populates "Commonly Associated Term" columns with these hierarchy relationships.

**Current State**:
- 1,609 associated term entries across 1,636 terms
- Top entry: "Regional part of brain" (593 occurrences - 36% of all terms)
- Other common entries: "Anatomical entity", "Brodmann partition scheme region", "Nucleus of CNS"

**Issue**: These are **ontology metadata** (class hierarchy), not **domain associations** needed for query expansion.

**Expected for Lex Stream**:
- Hippocampus → memory, learning, Alzheimer's disease, temporal lobe
- Dopamine → reward, Parkinson's disease, substantia nigra, motivation

**Actual from NIF**:
- Hippocampus → Regional part of brain
- Thalamus → Regional part of brain
- Amygdala → Regional part of brain

---

## Options Analysis

### Option A: Update NIF Importer NOW (Skip Associated Terms)

**Approach**: Modify `import_nif_neuroanatomy.py` to not populate associated term columns from RDF hierarchy relationships.

#### Pros
✅ **Cleaner data immediately** - No misleading generic taxonomy terms
✅ **Prevents query pollution** - Lex Stream won't expand searches with "Regional part of brain"
✅ **Establishes quality principle** - Only populate fields with appropriate data types
✅ **Better testing baseline** - Can test Lex Stream with NIF data without false positives
✅ **Clear role separation** - NIF = structure names/synonyms, UMLS = associations
✅ **Easier to validate** - Empty fields clearly indicate "needs UMLS enrichment"

#### Cons
❌ **Time investment** - Need to update importer, re-run, re-validate (~30 minutes)
❌ **Potential data loss** - Some specific parents might be useful (e.g., "Nucleus of CNS", "Cranial nerve")
❌ **Premature decision** - Don't know if hierarchy relationships useful for MeSH trees (James's Nov 25 requirement)
❌ **Risk of rework** - If UMLS has same issue, will need different strategy
❌ **Incomplete data sooner** - NIF export will have fewer populated fields

#### Implementation Effort
- Modify lines 222-224 in `import_nif_neuroanatomy.py`
- Re-run importer (~2 minutes)
- Update validation report (~5 minutes)
- Re-commit and document (~10 minutes)
- **Total**: ~30 minutes

---

### Option B: Wait for UMLS, Then Decide

**Approach**: Keep current NIF import as-is. Evaluate UMLS "related concepts" quality. Make decision during merge phase (Day 4).

#### Pros
✅ **Evidence-based decision** - See what UMLS provides before choosing strategy
✅ **Preserve hierarchy data** - Might be useful for MeSH tree implementation
✅ **Avoid rework** - If UMLS also has generic terms, need unified filtering strategy anyway
✅ **More context** - Can compare NIF hierarchy vs UMLS associations vs existing Wikipedia data
✅ **Flexible filtering** - Can implement smart filtering during merge (e.g., keep specific terms, remove generic)
✅ **No time cost now** - Continue with Day 2 (Gene Ontology) immediately

#### Cons
❌ **Misleading current data** - Associated term fields contain wrong data type
❌ **Bad precedent** - Signals "populate fields even if semantically incorrect"
❌ **Testing complications** - If we test Lex Stream before UMLS, results skewed by generic terms
❌ **Harder merge logic** - Filtering 100K UMLS + 1.6K NIF terms more complex than re-running NIF
❌ **Documentation burden** - Need to clearly document "these aren't real associations"

#### Implementation Effort
- Update documentation to note limitation (~10 minutes)
- Implement filtering logic during merge phase (~2 hours on Day 4)
- **Total**: ~2 hours (deferred to Day 4)

---

## Data Analysis

### Specificity Distribution

| Term Frequency | Count | Specificity Level | Example | Useful? |
|----------------|-------|-------------------|---------|---------|
| 200+ | 1 | Ultra-generic | "Regional part of brain" (593) | ❌ No |
| 50-199 | 1 | Very generic | "Brodmann partition scheme region" (50) | ⚠️ Maybe |
| 20-49 | 3 | Generic | "Superficial feature part of frontal lobe" (30) | ⚠️ Maybe |
| 10-19 | 7 | Moderately specific | "Nucleus of CNS" (22), "Cranial nerve" (13) | ✅ Possibly |
| 5-9 | 12 | Specific | "Lobe of cerebral cortex" (9) | ✅ Likely |
| 1-4 | 247 | Very specific | Individual structure names | ✅ Yes |

**Observation**: ~92% of associated terms (250 of 271 unique) appear ≤9 times, suggesting they might be specific enough to be useful.

**Problem**: The top 4 generic terms account for 701 of 1,609 entries (44%).

---

## Hybrid Option: Filtered Associated Terms

### Option C: Smart Filtering (Keep Specific, Remove Generic)

**Approach**: Modify importer to filter associated terms by frequency threshold.

**Logic**:
```python
# Only include associated terms that appear ≤ threshold times
# Rationale: Rare terms = specific, common terms = generic taxonomy

SPECIFICITY_THRESHOLD = 20  # Appears in max 20 terms (~1% of dataset)

if associated_term_frequency <= SPECIFICITY_THRESHOLD:
    row['Commonly Associated Term 1'] = term
else:
    # Too generic, skip
    pass
```

**Result**:
- Removes: "Regional part of brain" (593), "Brodmann partition scheme region" (50), generic parent classes
- Keeps: "Nucleus of CNS" (22), "Cranial nerve" (13), specific structural relationships

#### Pros
✅ **Best of both worlds** - Preserve specific relationships, remove generic noise
✅ **Data-driven** - Use frequency as proxy for specificity
✅ **Useful hierarchy info** - Keep parent terms that are actually informative
✅ **Scalable** - Can apply same logic to UMLS, Gene Ontology

#### Cons
❌ **Complex implementation** - Need two-pass processing (count frequencies, then filter)
❌ **Arbitrary threshold** - "20 occurrences" is heuristic, might need tuning
❌ **False positives** - Some common terms might actually be useful
❌ **Most work** - Requires significant code changes (~1-2 hours)

---

## Recommendation

### Short-term (Before Day 2): **Option A - Skip Associated Terms**

**Rationale**:
1. **NIF's strength is structure names, not associations** - Focus on what it does well
2. **UMLS will fill this gap** - Wait for semantic relationships from comprehensive source
3. **Clean data principle** - Don't populate fields with semantically incorrect data
4. **Low cost** - 30 minutes vs 2 hours (Option B merge complexity)
5. **Reversible** - If we discover hierarchy useful for MeSH trees, can add back

**Exception**:
If hierarchy relationships turn out to be critical for MeSH tree implementation (James's requirement), revisit on Day 4 during merge phase.

### Long-term (Day 4 Merge): Evaluate UMLS quality, then choose between:
- **If UMLS has good associations**: Use UMLS for associated terms, NIF for structure names
- **If UMLS also generic**: Implement Option C (smart filtering) across all sources
- **If MeSH trees need hierarchy**: Add separate "parent_structure" field, keep associated terms for domain concepts

---

## Questions to Answer with UMLS Data

1. Does UMLS have domain-specific "related concepts" or also generic taxonomy?
2. How many UMLS neuroscience terms have associated concepts?
3. What's the overlap between NIF hierarchy and UMLS associations?
4. Are NIF parent structures useful for MeSH tree navigation?

---

## Decision Criteria

**Choose Option A (skip now) if**:
- ✅ Primary goal is query expansion (not MeSH trees)
- ✅ Want clean data for testing
- ✅ Confident UMLS will provide associations
- ✅ Time-constrained for Day 2

**Choose Option B (wait) if**:
- ✅ MeSH tree implementation is immediate priority
- ✅ Need to preserve all source data for analysis
- ✅ Uncertain about UMLS quality
- ✅ Can document limitations clearly

**Choose Option C (filter) if**:
- ✅ Need both hierarchy AND associations from NIF
- ✅ Have time for complex implementation
- ✅ Want maximum data preservation with quality

---

## Impact Assessment

### On Lex Stream Query Expansion
- **Current (with generic terms)**: Searches for "hippocampus" would expand to include "regional part of brain" (adds noise)
- **After Option A**: Searches wait for UMLS associations (cleaner but incomplete)
- **After UMLS merge**: Searches use domain-specific associations (optimal)

### On MeSH Tree Implementation
- **Current**: Have parent-child structure relationships available
- **After Option A**: Lose parent-child for Day 2-3, can restore during merge if needed
- **After merge**: Can implement MeSH trees with proper semantic relationships

---

## Next Steps

1. **Decide by**: End of Day 1 review (today)
2. **If Option A**: Update importer, re-run, commit before Day 2
3. **If Option B**: Document limitation, continue to Day 2 (Gene Ontology)
4. **If Option C**: Defer to Day 4, implement during merge phase

---

## Decision Made

**Chosen Option**: **A - Skip Associated Terms**

**Rationale**:
- NIF's core strength is neuroanatomy structure names, not semantic associations
- Generic taxonomy terms ("Regional part of brain") don't help query expansion
- UMLS will provide domain-specific associated terms
- Lower implementation cost (30 min vs 2 hours during merge)
- Produces cleaner data for Lex Stream testing
- Reversible if MeSH tree implementation needs hierarchy data

**Implementation**:
- Modified `scripts/import_nif_neuroanatomy.py` lines 221-225
- Removed associated term extraction from RDF relationships
- Added decision reference comment in code
- Re-ran import pipeline
- Validated output: 0 of 1,636 terms have associated terms

**Results**:
- ✅ All 1,636 terms now have empty associated term fields
- ✅ Structural validation passes
- ✅ Ready for UMLS merge to populate associated terms
- ✅ Clean baseline for Lex Stream testing

**Next Steps**:
1. During UMLS import (Day 3+), evaluate UMLS "related concepts" quality
2. During merge (Day 4), populate associated terms from UMLS
3. If MeSH tree implementation needs hierarchy, can add separate field or restore NIF relationships

**Trade-offs Accepted**:
- ⚠️ NIF parent-child structure relationships not preserved in associated terms
- ⚠️ If needed for MeSH trees, will require additional implementation work
- ✅ Risk mitigated by: Can restore from source TTL if needed, UMLS likely provides better associations
