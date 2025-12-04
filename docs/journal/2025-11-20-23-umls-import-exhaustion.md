# UMLS Import Exhaustion: Processing 17.4M Rows of Medical Ontology

**Date**: 2025-11-20 23:00
**Severity**: Medium
**Component**: UMLS Metathesaurus Import
**Status**: Complete (but at what cost?)

## What Happened

Spent two days importing UMLS Metathesaurus. Downloaded 12 GB of data files. Processed MRCONSO.RRF (2.1 GB, 17.4M rows), MRDEF.RRF (131 MB), MRREL.RRF (5.7 GB). Multi-stage filtering reduced 1.02M CUIs → 325,241 terms. Generated 88 MB CSV file. Export to JSON: 189 MB.

Result: Went from 649 curated terms to 325,241 UMLS terms. 500× increase in vocabulary size.

And somehow this feels like a Pyrrhic victory.

## The Brutal Truth

The numbers look impressive:
- ✅ 325,241 neuroscience terms (vs 649 manual)
- ✅ 90.4% association coverage (294K terms have related concepts)
- ✅ 24.5% definition coverage (79K terms have definitions)

But the quality metrics tell a different story:
- ❌ 10.0% synonym coverage (vs 42.7% manual curation)
- ❌ 0.5% abbreviation coverage (vs 22.2% manual)
- ❌ 1.38s load time (vs 0.05s for 649 terms)

We traded QUALITY for QUANTITY. And I'm not sure it was worth it.

## Technical Details

**UMLS data structure**:
- MRCONSO.RRF: Concept names and term types (17.4M rows)
- MRDEF.RRF: Definitions (900K rows)
- MRREL.RRF: Relationships between concepts (91M rows)

**Filtering pipeline**:
```
17.4M total rows
  → 27 neuroscience semantic types (T023, T025, T026, etc.)
  → 1.02M CUIs match semantic filter
  → Group by CUI, aggregate preferred terms
  → Keep only if has >=1 related concept
  → 325,241 final terms
```

**What we kept**:
- Preferred term (PT) as primary
- Synonyms from 9 TTY types (SY, MTH_SY, etc.)
- Abbreviations from 4 TTY types (AB, MTH_AB, etc.)
- Related concepts via "RL" relationship type
- Definitions (when available)

**What we lost**:
- Hierarchy relationships (skipped RDF parsing)
- Semantic type classifications (data exists, not extracted)
- Source attributions (which ontology provided each term)
- Confidence scores (UMLS doesn't really have these)

## What We Tried

**Attempt 1: Strict CUI filter (target 100K terms)**
- Used narrowest semantic types only
- Result: Missed too many valid neuroscience terms
- Rejected

**Attempt 2: Broad CUI filter (got 1.02M CUIs)**
- All 27 neuroscience semantic types
- Natural filtering via relationship requirements
- Result: 325K final terms (68% reduction from filtering)
- ✅ Accepted

**Attempt 3: Synonym enrichment (Phase 2A)**
- Expanded TTY types from 3→9 for synonyms
- Expanded TTY types from 2→4 for abbreviations
- Added heuristic detection for abbreviations
- Result: 10% synonym coverage (vs target 50%)
- Conclusion: UMLS limitation, not implementation issue

## Root Cause Analysis

**Why synonym coverage is so low**: UMLS is federated - it aggregates 200+ source vocabularies but doesn't normalize synonym representation. Some sources provide rich synonyms (MeSH), others don't (NCI Thesaurus). The aggregation creates vocabulary breadth but synonym sparsity.

**Why this took 2 days**:
- Day 1: NIF neuroanatomy import (1,636 terms) revealed RDF hierarchy complexity
- Day 2: UMLS Metathesaurus (325K terms) hit filtering complexity
- Day 3: Phase 2A synonym expansion hit data quality limits

**The architectural trap**: Assumed more data = better results. Reality: more data = more noise unless you also import the semantic structure (hierarchies, classifications, relationships).

## The Exhausting Part

Processing 17.4M rows is intellectually interesting but emotionally draining:
- Waiting for 15-minute import scripts to finish
- Debugging why relationship filtering drops 700K terms
- Investigating why abbreviation coverage is 0.5% (spoiler: UMLS doesn't encode many)
- Writing decision docs for every major filtering choice (DEC-001, DEC-002, DEC-003)
- Defending why we're keeping 1.02M CUIs when initial target was 100K

And at the end: **James says the glossary approach is too simplistic**.

The 325K terms don't solve the core problem (semantic classification). They just give us more terms to classify incorrectly.

## Lessons Learned

1. **Vocabulary size ≠ query quality**: 325K terms with 10% synonyms < 649 terms with 42.7% synonyms
2. **Federated data has gaps**: UMLS aggregates but doesn't harmonize - synonym quality varies wildly by source
3. **Import ≠ integration**: Having 325K terms loaded doesn't mean the query pipeline uses them well
4. **Decision docs are essential**: DEC-001 through DEC-004 preserve rationale when questioned later
5. **Prototype before scaling**: Should have tested 100 terms first, not jumped to 325K

## The Meta-Realization

Three days after finishing UMLS import, we pivoted to API-first architecture.

All that import code? Not deleted, but... not used in production either. The 325K terms sit in `imports/umls/` as a fallback layer, not the primary engine.

The real value of the UMLS import wasn't the 325K terms. It was learning WHY APIs are better:
- UMLS API returns semantic types (T047 = Disease)
- UMLS API is always current (our CSV freezes at download date)
- UMLS API doesn't require 88 MB local storage
- UMLS API does the classification we need

## Next Steps

**At the time (Nov 20)**:
- ✅ Complete Phase 2A synonym expansion
- ✅ Export to neuro_terms_v3.0.0_umls.json
- ✅ Document coverage gaps (DEC-004)

**In retrospect (Dec 4)**:
- The 325K terms became fallback layer
- Primary pipeline uses UMLS API, not local CSV
- The import code is preserved but not critical path

## Emotional Footnote

There's something demoralizing about spending 2 days processing 17.4M rows, generating an 88 MB CSV, and having someone say "the glossary approach is too simplistic" three days later.

The work wasn't wasted - we learned database scale isn't the solution. But it's hard not to feel like we optimized the wrong thing.

**Lines of code written**: ~800 (import scripts + merge logic)
**Rows processed**: 17,400,000
**Final terms**: 325,241
**Production usage**: Fallback layer only

The git commits from Nov 19-21 represent excellent execution of database import. But the architecture pivot on Nov 28 revealed that vocabulary size wasn't the bottleneck - semantic understanding was.

**Commits**:
- `bcd92e1` - NIF import (1,636 terms)
- `07426e9` - UMLS import (325K terms)
- `efc1786` - Phase 2A expansion
