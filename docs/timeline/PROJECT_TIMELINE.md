# NeuroDB-2 Project Timeline

**Purpose**: Comprehensive chronology of project evolution, decisions, and pivots
**Last Updated**: 2025-12-03

---

## Overview

NeuroDB-2 evolved through six distinct phases, transitioning from a manual Wikipedia-based glossary to a hybrid API-first + local database architecture optimized for neuroscience literature search.

**Current Status**: Phase 6 - Hybrid Approach (POC validated Dec 2025)

---

## Phase 1: Original Database Approach (Nov 2025)

### Timeline
**Nov 7-12, 2025**

### Objective
Build comprehensive neuroscience terminology database via manual curation from authoritative glossaries

### Approach
- Source data from Wikipedia Glossary of Neuroscience + NINDS glossary
- Manual enrichment of 22-column schema (synonyms, abbreviations, definitions, MeSH terms)
- Dual validation (mesh-validator + neuro-reviewer agents)
- Letter-by-letter processing (A-Z.csv files)

### Outcomes
✅ **595 terms** from Wikipedia (all letters A-Z complete)
✅ **54 terms** from NINDS
✅ **Total: 649 terms** with high-quality data
✅ **Dual validation**: 95% test pass rate in Lex Stream integration
✅ **Coverage stats**:
- 88.4% MeSH coverage
- 42.7% synonym coverage
- 22.2% abbreviation coverage
- 94.7% associated terms coverage

### Key Files Created
- `LetterFiles/[A-Z].csv` - Individual letter databases
- `neuro_terms.csv` - Master consolidated database
- `neuro_terms.json` / `neuro_terms_v2.0.0_wikipedia-ninds.json` - Lex Stream export
- `MeshValidation/` - Validation logs and correction tracking
- `LEXSTREAM_INTEGRATION_REPORT.md` - Integration test results

### Decision Documents
- None (manual workflow, no major decisions required)

### Limitations Discovered
❌ Only 649 terms insufficient for quality literature searches
❌ Manual enrichment bottleneck (1 min/term)
❌ Cannot scale to 10K+ terms needed by Lex Stream users
⚠️ James's feedback: "569 terms really short of what we will need"

---

## Phase 2: UMLS Integration (Nov 19-21, 2025)

### Timeline
**Nov 19-21, 2025** (3 days)

### Objective
Scale database from 649 → 325,241 terms using UMLS Metathesaurus (20+ ontology sources)

### Approach
**Day 1 (Nov 19)**: NIF Neuroanatomy Import
- Source: NIF-GrossAnatomy.ttl (1.41 MB, 29,742 RDF triples)
- Result: 1,636 neuroanatomy structure names
- Issue: Generic taxonomy in associated terms → DEC-001 skip decision

**Day 2 (Nov 20)**: UMLS Metathesaurus Import
- Sources: MRCONSO.RRF (2.1 GB), MRDEF.RRF (131 MB), MRREL.RRF (5.7 GB)
- Semantic type filtering: 27 neuroscience types → 1.02M CUIs
- Multi-stage filtering: 17.4M rows → 325,241 unique terms
- Issues:
  - CUI filter too broad (1M vs 100K target) → DEC-002
  - Low definition coverage (24.5%) → DEC-003
  - Domain vs taxonomy relationships → DEC-001 analysis

**Day 3 (Nov 21)**: Phase 2A Synonym/Abbreviation Expansion
- Expanded TTY types: Synonyms (3→9), Abbreviations (2→4)
- Heuristic detection for abbreviations
- Results: 10% synonym coverage, 0.5% abbreviation coverage
- Root cause: UMLS data limitation (not implementation) → DEC-004

### Outcomes
✅ **325,241 terms** (580x increase from Phase 1)
✅ **90.4% association coverage** (294,008 terms)
✅ **24.5% definition coverage** (79,617 terms)
✅ **Lex Stream export**: `neuro_terms_v3.0.0_umls.json` (189 MB)
⚠️ **Low synonym/abbreviation coverage** (10%/0.5% vs 42.7%/22.2% in Phase 1)

### Key Files Created
- `imports/nif/` - NIF neuroanatomy importer
- `imports/umls/` - UMLS importer suite
- `imports/umls/umls_neuroscience_terms.csv` (88 MB, 325K terms)
- `scripts/import_nif_neuroanatomy.py`
- `scripts/import_umls_metathesaurus.py`
- `scripts/merge_umls_enrichments.py`
- `convert_umls_to_lexstream.py`

### Decision Documents
- `docs/decisions/2025-11-19-nif-associated-terms-decision.md` (DEC-001)
- `docs/decisions/2025-11-20-umls-cui-filter-count-decision.md` (DEC-002)
- `docs/decisions/2025-11-20-umls-coverage-strategy-decision.md` (DEC-003)
- `docs/decisions/ontology-import-tracker.md` (DEC-004 Phase 2A findings)

### Plan Documents
- `plans/2025-11-19-scalable-ontology-ingestion-with-source-control.md`
- `plans/2025-11-20-umls-importer-implementation-plan.md`
- `plans/251121-umls-phase2a-synonym-abbreviation-expansion.md`

### Trade-Offs
✅ Massive vocabulary increase (325K terms)
✅ Excellent associations (90.4%)
❌ Lower synonym quality (10% vs 42.7%)
❌ Lower abbreviation quality (0.5% vs 22.2%)
❌ 1.38s load time (vs 0.05s Phase 1)

---

## Phase 3: James's Feedback - Semantic Understanding (Nov 17 & 28, 2025)

### Timeline
**Nov 17 & 28, 2025**

### Key Feedback
**Quote (Nov 17)**: *"569 terms is really short of what we will need. We def need more for synonym mapping and proper query expansion. Also, the glossary approach is too simplistic - the secret sauce comes from being able to understand the hierarchy of terms."*

### Critical Insight: MeSH Hierarchy Trees
James provided Parkinson's Disease example showing **three different hierarchy branches**:

1. **Movement Disorder Path**:
   - Nervous System Diseases → Central Nervous System Diseases → Movement Disorders → Parkinsonian Disorders → Parkinson Disease

2. **Brain Disease Path**:
   - Nervous System Diseases → Central Nervous System Diseases → Brain Diseases → Basal Ganglia Diseases → Parkinsonian Disorders → Parkinson Disease

3. **Neurodegenerative Path**:
   - Nervous System Diseases → Neurodegenerative Diseases → Synucleinopathies → Lewy Body Disease → Parkinson Disease

### Impact on Query Expansion
- Hierarchy enables semantic understanding
- Related terms from parent/sibling nodes
- Context-aware synonym expansion
- Component detection improvements

### Stakeholder Requirements
1. Expand vocabulary: 569 → 3,500-4,000+ neuroscience terms
2. Add MeSH hierarchy trees (tree numbers, parent/child relationships)
3. Improve synonym coverage: 42.7% → 70-80%
4. Integrate UMLS Metathesaurus

### Analysis Documents
- `docs/analysis/2025-11-28_1400_lexstream-comprehensive-research.md` - Comprehensive Lex Stream research
- `docs/feedback/20251117-neuroscientist-feedback-expansion-trees.md` (in Lex Stream)

### Status
⏳ **MeSH hierarchy implementation**: Deferred (3-month timeline)
✅ **UMLS integration**: Complete (325K terms)
⚠️ **Synonym coverage**: Still gap (10% UMLS vs 70-80% target)

---

## Phase 4: Problem Statement & Research (Nov 28, 2025)

### Timeline
**Nov 28, 2025**

### Objective
Formalize the core problem: "MS + neuromodulation" query returns wrong results

### Problem Analysis
**User Input**: "MS + neuromodulation"

**Current Behavior (UMLS-only)**:
- "MS" → "Ms. - Title" (generic honorific)
- Classification: OTHER
- Query returns 14 papers (mostly irrelevant)

**Desired Behavior**:
- "MS" → "Multiple Sclerosis" (disease)
- Classification: CONDITION
- Query returns 5-10 relevant papers

### Root Cause
UMLS cannot disambiguate abbreviations without context. "MS" in UMLS matches:
- "Ms." (title/honorific) - first alphabetical match
- "Multiple Sclerosis" (disease)
- "Mass Spectrometry" (lab technique)
- etc.

### Research Conducted
Gemini-powered comprehensive Lex Stream analysis:
- Analyzed 5-agent pipeline (SpellChecker, AbbreviationExpander, SynonymFinder, MeSH Detector, ComponentDetector)
- Identified which agents use definitions (ComponentDetector only)
- Profiled database requirements (primary_term, synonyms, abbreviations, mesh_term)
- Documented integration points

### Key Documents
- `docs/decisions/lex-stream-data-layer-problem-statement.docx` - Formal problem statement
- `docs/analysis/2025-11-28_1400_lexstream-comprehensive-research.md` - Comprehensive research

### Insight
Need **abbreviation disambiguation layer** before UMLS semantic classification

---

## Phase 5: API-First POC (Dec 2-3, 2025)

### Timeline
**Dec 2-3, 2025**

### Objective
Validate if PubTator + UMLS APIs can solve semantic classification without local database

### Hypothesis
```
PubTator (abbreviation disambiguation) → UMLS (semantic classification) → Smart Query
```

### POC Architecture
**5-Layer Pipeline**:
1. **PubTator Autocomplete**: Abbreviation disambiguation
   - "MS" → "Multiple Sclerosis" (disease, confidence: 0.70)
2. **UMLS API**: Semantic classification
   - "Multiple Sclerosis" → T047 (Disease or Syndrome) → CONDITION
   - "neuromodulation" → T061 (Therapeutic Procedure) → INTERVENTION
3. **Smart Query Building**: PICO-structured query
   - (condition) AND (intervention)
4. **PubMed E-utilities**: Literature search
5. **Results**: 5 papers (vs 1-14 with blind expansion)

### POC Results
✅ **SUCCEEDED** - Semantic classification problem solved

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Correct semantic classification | 100% | 100% | ✅ PASS |
| Result count (5-20 papers) | 5-20 | 5 | ✅ PASS |
| Latency (<20s acceptable for POC) | <20s | 15.16s | ✅ PASS |
| Abbreviation handling | Yes | Yes | ✅ PASS |

### API Performance
**PubTator 3.0 Autocomplete**:
- Correctly resolved "MS" → "Multiple Sclerosis" (first match)
- Latency: ~200ms per query
- Cost: Free (no auth required)

**UMLS Metathesaurus API**:
- Accuracy: 100% for full terms
- Latency: ~500ms per query
- Cost: Free (registration required)
- Rate limits: 20 req/s, 5000 req/hr

### Key Files Created
- `poc-api-first/poc_pipeline.py` - Main pipeline
- `poc-api-first/clients/pubtator.py` - PubTator client
- `poc-api-first/clients/umls.py` - UMLS client
- `poc-api-first/clients/pubmed.py` - PubMed client
- `poc-api-first/POC_RESULTS.md` - Results summary
- `docs/plans/api-first-poc-detailed.md` - Detailed plan
- `docs/plans/api-first-poc-summary.md` - Executive summary

### Gaps Identified
1. **Latency**: 15s acceptable for POC, needs <2s for production → Redis cache
2. **PubTator coverage**: Not all neuroscience abbreviations (e.g., fMRI, DTI) → NeuroDB-2 fallback
3. **Context ambiguity**: "MS" could be Multiple Sclerosis OR Mass Spectrometry → needs disambiguation
4. **Rate limits**: UMLS 20 req/s → aggressive caching needed

---

## Phase 6: Hybrid Approach (Dec 3, 2025)

### Timeline
**Dec 3, 2025** (Current)

### Objective
Combine API-first + NeuroDB-2 for optimal performance

### Recommended Architecture
```
User Input
  ↓
[Layer 1] NeuroDB-2 - Neuroscience-specific abbreviations (TMS, DBS, fMRI, etc.)
  ↓
[Layer 2] PubTator - General biomedical abbreviations (MS, COPD, etc.)
  ↓
[Layer 3] UMLS API - Semantic classification
  ↓
[Layer 4] Smart query building (PICO structure)
  ↓
[Layer 5] PubMed search
```

### NeuroDB-2 Value Proposition
**Strengths retained**:
- ✅ Neuroscience-specific jargon not in PubTator
- ✅ Caching layer for common UMLS lookups (performance)
- ✅ User-specific customizations
- ✅ 126 abbreviations already curated
- ✅ High-quality synonyms (42.7% for top terms)

**API strengths**:
- ✅ Abbreviation disambiguation (PubTator)
- ✅ Semantic classification (UMLS API)
- ✅ No local database bloat
- ✅ Always up-to-date (live APIs)

### Production Architecture Plan (Weeks 2-4)
```python
def enhanced_pipeline(user_input):
    terms = parse_input(user_input)

    for term in terms:
        # Layer 1: NeuroDB-2 (neuroscience-specific)
        if term in neurodb_abbreviations:
            resolved = neurodb_abbreviations[term]

        # Layer 2: PubTator (biomedical general)
        elif is_abbreviation(term):
            resolved = pubtator.disambiguate(term)

        # Layer 3: UMLS API (semantic classification)
        classification = umls.classify(resolved)

        # Layer 4: Smart query building
        query_part = build_query(classification)

    # Layer 5: PubMed search
    return pubmed.search(query)
```

### Next Steps
**Week 1**:
1. Add Redis caching layer (15s → <2s latency)
2. Integrate NeuroDB-2 abbreviations (126 terms)
3. Test additional cases (Parkinson's+DBS, fMRI+motor cortex)

**Weeks 2-4**:
1. Production deployment with caching
2. Hybrid database (NeuroDB-2 + UMLS API)
3. Performance benchmarking (<2s target)

### Status
✅ **POC validated** (Dec 2-3)
⏳ **Production implementation** (pending)

---

## Artifacts By Phase

### Phase 1: Original Database
**Data Files**:
- `LetterFiles/[A-Z].csv` (595 terms)
- `neuro_terms.csv` (master database)
- `neuro_terms.json` (Lex Stream export)
- `neuro_terms_v2.0.0_wikipedia-ninds.json` (versioned export)

**Documentation**:
- `LEXSTREAM_INTEGRATION_REPORT.md`
- `SCHEMA_MIGRATION.md`
- `VERSIONING_SUMMARY.md`
- `Wikipedia-Glossary-of-Neuroscience.md` (source)
- `ninds-glossary-of-neurological-terms.md` (source)

**Validation**:
- `MeshValidation/mesh_corrections_log.json`
- `MeshValidation/mesh_corrections_log.csv`
- `MeshValidation/mesh_corrections_summary.md`
- `mesh_final_report.md`
- `mesh_validation_results.json`

### Phase 2: UMLS Integration
**Data Files**:
- `imports/nif/` - NIF import data
- `imports/umls/` - UMLS import data
- `imports/umls/umls_neuroscience_terms.csv` (325K terms)
- `neuro_terms_v3.0.0_umls.json` (Lex Stream export)

**Scripts**:
- `scripts/import_nif_neuroanatomy.py`
- `scripts/import_umls_metathesaurus.py`
- `scripts/merge_umls_enrichments.py`
- `convert_umls_to_lexstream.py`

**Documentation**:
- `docs/decisions/2025-11-19-nif-associated-terms-decision.md`
- `docs/decisions/2025-11-20-umls-cui-filter-count-decision.md`
- `docs/decisions/2025-11-20-umls-coverage-strategy-decision.md`
- `docs/decisions/ontology-import-tracker.md`
- `docs/UMLS_EXPLAINED.md`
- `docs/UMLS_LEXSTREAM_INTEGRATION_SUMMARY.md`

**Plans**:
- `plans/2025-11-19-scalable-ontology-ingestion-with-source-control.md`
- `plans/2025-11-20-umls-importer-implementation-plan.md`
- `plans/251121-umls-phase2a-synonym-abbreviation-expansion.md`

### Phase 3: James's Feedback
**Analysis**:
- `docs/analysis/2025-11-28_1400_lexstream-comprehensive-research.md`
- Lex Stream: `docs/feedback/20251117-neuroscientist-feedback-expansion-trees.md`

### Phase 4: Problem Statement
**Decision Docs**:
- `docs/decisions/lex-stream-data-layer-problem-statement.docx`

**Research**:
- `plans/research/251128-umls-semantic-types-pico-classification.md`

### Phase 5: API-First POC
**POC Code**:
- `poc-api-first/poc_pipeline.py`
- `poc-api-first/clients/pubtator.py`
- `poc-api-first/clients/umls.py`
- `poc-api-first/clients/pubmed.py`
- `poc-api-first/POC_RESULTS.md`

**Plans**:
- `docs/plans/api-first-poc-detailed.md`
- `docs/plans/api-first-poc-summary.md`

### Phase 6: Hybrid Approach
**Status**: Documentation in progress (this timeline)

---

## Key Decisions Log

### DEC-001: NIF Associated Terms Handling
**Date**: 2025-11-19
**Decision**: Skip RDF hierarchy, let UMLS populate associations
**Rationale**: Taxonomic relationships ≠ domain associations
**Impact**: Cleaner data, UMLS dependency for associations
**Doc**: `docs/decisions/2025-11-19-nif-associated-terms-decision.md`

### DEC-002: UMLS CUI Filter Count Strategy
**Date**: 2025-11-20
**Decision**: Proceed with 1M CUIs + multi-stage filtering
**Rationale**: Natural filtering more effective than strict upfront filters
**Impact**: 1.02M CUIs → 325,241 terms (68% reduction)
**Doc**: `docs/decisions/2025-11-20-umls-cui-filter-count-decision.md`

### DEC-003: UMLS Coverage Strategy (Definitions)
**Date**: 2025-11-20
**Decision**: Import all 325K terms (24.5% definition coverage)
**Rationale**: Maximum coverage > definition coverage; core agents work without definitions
**Impact**: 325K terms imported, ComponentDetector degraded but functional
**Doc**: `docs/decisions/2025-11-20-umls-coverage-strategy-decision.md`

### DEC-004: Phase 2A Synonym/Abbreviation Expansion
**Date**: 2025-11-21
**Decision**: Accept UMLS data limitation (10%/0.5% coverage)
**Rationale**: Extracted 100% of available UMLS data; need alternative sources
**Impact**: Targets (50%/20%) unrealistic; recommend Wikipedia/LLM enrichment
**Doc**: `docs/decisions/ontology-import-tracker.md` (Phase 2A findings)

### DEC-005: API-First POC Go/No-Go
**Date**: 2025-12-02
**Decision**: GO - Implement hybrid architecture
**Rationale**: PubTator + UMLS API solve semantic classification; NeuroDB-2 valuable as supplement
**Impact**: 5-layer architecture validated; proceed to caching + integration
**Doc**: `poc-api-first/POC_RESULTS.md`

---

## Metrics Comparison

| Metric | Phase 1 (Manual) | Phase 2 (UMLS) | Phase 5 (API) | Phase 6 (Hybrid) |
|--------|------------------|----------------|---------------|------------------|
| **Term Count** | 649 | 325,241 | N/A (API) | 649 + API |
| **Synonym Coverage** | 42.7% | 10.0% | N/A | 42.7% (local) |
| **Abbreviation Coverage** | 22.2% | 0.5% | N/A | 22.2% (local) |
| **Definition Coverage** | 100% | 24.5% | N/A | 100% (local) |
| **Association Coverage** | 94.7% | 90.4% | N/A | 90%+ |
| **MeSH Coverage** | 88.4% | 4.2% | 100% (API) | 88.4% + API |
| **Load Time** | 0.05s | 1.38s | ~0.7s (API) | <2s (cached) |
| **Latency** | Instant | Instant | 15s (POC) | <2s (target) |
| **Semantic Classification** | Manual | None | ✅ Automatic | ✅ Automatic |
| **Abbreviation Disambiguation** | Manual | None | ✅ PubTator | ✅ PubTator |

---

## Lessons Learned

### Technical
1. **UMLS strengths**: Vocabulary breadth, associations (90.4%), authoritative sources
2. **UMLS limitations**: Synonym/abbreviation sparsity (10%/0.5%), definition gaps (24.5%)
3. **API advantages**: Always up-to-date, semantic classification, no database bloat
4. **API challenges**: Latency (15s), rate limits (20 req/s), caching required
5. **Hybrid value**: Combines local quality + API breadth

### Process
1. **User feedback critical**: James's hierarchy insight shaped Phase 3-6
2. **POC before commitment**: API-first POC validated architecture before full implementation
3. **Incremental testing**: Small samples (100 terms) before full import saved rework
4. **Decision documentation**: DEC-001 through DEC-005 preserved rationale
5. **Version control**: Separate databases (v2.0.0, v3.0.0) enabled A/B testing

### Data Quality
1. **Coverage ≠ Quality**: 325K terms (UMLS) lower quality than 649 (manual)
2. **Source matters**: Wikipedia/NINDS 42.7% synonyms vs UMLS 10%
3. **Definitions optional**: Lex Stream core agents work without definitions
4. **Associations critical**: 90.4% coverage key for query expansion
5. **Curation needed**: Top 1K-10K terms require manual synonym enrichment

---

## Unresolved Questions

1. **MeSH Hierarchy**: When to implement tree numbers? (3-month timeline)
2. **Synonym Enrichment**: Wikipedia scraping vs LLM generation vs manual?
3. **Caching Strategy**: Redis vs local JSON vs hybrid?
4. **Database Merge**: Keep v2.0.0 + v3.0.0 separate or merge?
5. **Gene Ontology**: Still valuable after API-first pivot?

---

## Next Actions

### Immediate (Week 1)
- [ ] Implement Redis caching (target: 15s → <2s latency)
- [ ] Integrate NeuroDB-2 abbreviations (126 terms) into POC
- [ ] Test additional cases (Parkinson's+DBS, fMRI+motor cortex)
- [ ] Benchmark UMLS API vs local database performance

### Short-Term (Weeks 2-4)
- [ ] Production deployment (caching + NeuroDB-2 integration)
- [ ] Performance optimization (<2s total latency)
- [ ] Hybrid database strategy (local + API)
- [ ] Comprehensive testing (100 neuroscience queries)

### Medium-Term (Months 2-3)
- [ ] MeSH hierarchy implementation (tree numbers, parent/child)
- [ ] Synonym enrichment (top 5K terms, target 70% coverage)
- [ ] Definition backfill (Wikipedia/NINDS for top 10K terms)
- [ ] Production monitoring (latency, cache hit rate, API costs)

---

**Document Status**: ✅ COMPLETE
**Maintained By**: Engineering Team
**Review Frequency**: After each major phase/pivot
