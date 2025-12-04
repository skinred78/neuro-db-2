# LexStream Query Generation Roadmap

**Date**: 2025-12-04
**Status**: DRAFT - Strategic alignment document
**Owner**: NeuroDB-2 / LexStream

---

## The Goal

**Product Vision**: LexStream enables neuroscience researchers to generate expert-grade PubMed queries that monitor niche research areas with a continuous stream of relevant new papers.

**The "Secret Sauce"**: Understanding the hierarchy and nuance behind search terms - not just synonyms, but knowing what type of concept each term represents and how to expand it appropriately.

---

## Current State

### What We Have
| Component | Status | Description |
|-----------|--------|-------------|
| NeuroDB-2 (569 terms) | Stable | Curated neuroscience glossary with synonyms, abbreviations, MeSH terms |
| UMLS import (325K terms) | Testing | Massive vocabulary but sparse synonyms (10%), no semantic types |
| poc_api_first | Working | Comparison framework with 5 configs (UMLS, PubTator, PubMed APIs) |
| Webapp | Deployed | Side-by-side query comparison tool (Firebase + Cloud Run) |

### What's Missing
| Gap | Impact | Evidence |
|-----|--------|----------|
| Semantic classification | Critical | "MS + neuromodulation" → 1 hit (system doesn't know MS is disease, neuromodulation is intervention) |
| Category-specific expansion | Critical | All terms expanded the same way → semantic drift (dopamine, synaptic transmission pollute disease queries) |
| MeSH hierarchy | Important | Can't do intelligent broader/narrower term expansion |
| Hypothesis-driven testing | Process | Built POC without clear hypotheses about what each API would do |

---

## Desired State

**Expert Query Generation Flow**:
```
User Input: "MS, neuromodulation, motor outcomes"
                    ↓
        [Semantic Classification]
        MS → CONDITION_DISEASE
        neuromodulation → INTERVENTION_EXPOSURE
        motor outcomes → OUTCOME_MEASURE
                    ↓
        [Category-Specific Expansion]
        MS → Multiple Sclerosis (synonyms only, NO mechanisms)
        neuromodulation → neurostimulation, TMS, DBS (related procedures)
        motor outcomes → motor function, mobility (measurement terms)
                    ↓
        [Smart Query Assembly]
        ("Multiple Sclerosis"[MeSH] OR "MS"[tiab])
        AND
        ("neuromodulation"[tiab] OR "neurostimulation"[tiab] OR ...)
        AND
        ("motor function"[tiab] OR "mobility"[tiab])
                    ↓
        5-20 highly relevant papers
```

---

## Strategic Pillars

### Pillar 1: Semantic Understanding
**Goal**: Know what type of concept each term is before expanding it.

James's insight: "The core failure was not about hierarchy - it was that the system didn't know MS is a disease and neuromodulation is an intervention, so it applied the wrong expansion patterns."

**Seven Categories** (mapped from UMLS semantic groups):
1. POPULATION_CONTEXT - Who/where (elderly, patients, rodents)
2. CONDITION_DISEASE - What's wrong (MS, Parkinson's, stroke)
3. INTERVENTION_EXPOSURE - What's done (TMS, DBS, drugs)
4. OUTCOME_MEASURE - What's measured (motor function, cognition)
5. ANATOMY_SYSTEM - Where in body (hippocampus, motor cortex)
6. MECHANISM_BIOLOGICAL - How it works (dopamine, neuroplasticity)
7. OBJECT_DEVICE - Physical things (electrode, implant)

### Pillar 2: Category-Specific Expansion
**Goal**: Each category expands differently to avoid semantic drift.

| Category | Expand To | Never Expand To |
|----------|-----------|-----------------|
| CONDITION_DISEASE | Synonyms, subtypes | Mechanisms, non-clinical terms |
| INTERVENTION_EXPOSURE | Synonyms, same modality | Mechanisms, devices, outcomes |
| OUTCOME_MEASURE | Synonyms, acronyms, scale variants | - |
| ANATOMY_SYSTEM | Hierarchical children | Overly broad regions |
| MECHANISM_BIOLOGICAL | Direct synonyms ONLY | (High drift risk) |
| OBJECT_DEVICE | Direct synonyms | Conceptual expansions |
| POPULATION_CONTEXT | Rarely expand | - |

### Pillar 3: Hierarchical Relationships (Future)
**Goal**: Use MeSH tree structure for intelligent broader/narrower expansion.

Example: Parkinson's disease exists in 3 MeSH branches:
- Basal Ganglia Diseases
- Movement Disorders
- Synucleinopathies

A hierarchical system would recognize all paths and use them for contextual expansion.

**Priority**: After semantic classification is working (James: "Without knowing what a term IS, MeSH tree position is less useful")

### Pillar 4: Agile Testing Framework
**Goal**: Hypothesis-driven process for testing new APIs and methods.

Before adding any new capability:
1. State the hypothesis (what will this do to query quality?)
2. Define success criteria (result count, precision, no drift)
3. Test with prototype terms
4. Measure and document results
5. Iterate or discard

---

## Roadmap Phases

### Phase 0: Foundation (Current)
**Status**: Complete
- [x] NeuroDB-2 curated glossary (569 terms)
- [x] UMLS import (325K terms)
- [x] API integrations (UMLS, PubTator, PubMed)
- [x] Comparison webapp deployed
- [x] James feedback documented

### Phase 1: Semantic Classification
**Status**: Planning
**Goal**: Classify every term into one of 7 categories

Deliverables:
- [ ] 7-category taxonomy with UMLS TUI mapping
- [ ] Category-specific expansion rules
- [ ] Prototype with 50-100 high-value terms
- [ ] SemanticClassificationConfig for comparison testing

Success Criteria:
- 95%+ classification accuracy on prototype set
- "MS + neuromodulation" returns 5-20 papers (not 1)
- Zero semantic drift (no tetramethylsilane for TMS)

### Phase 2: Category-Specific Expansion
**Status**: Not started
**Goal**: Each category expands using its own rules

Deliverables:
- [ ] 7 category-specific expanders
- [ ] Anti-drift filters (forbidden patterns per category)
- [ ] Query assembly that respects categories

Success Criteria:
- CONDITION terms don't expand to mechanisms
- INTERVENTION terms stay within same modality
- MECHANISM terms expand conservatively (high drift risk)

### Phase 3: Production Integration
**Status**: Not started
**Goal**: Enriched database + hybrid classification flow

Deliverables:
- [ ] 569 curated terms enriched with semantic_type, CUI, TUI
- [ ] Hybrid flow: NeuroDB → UMLS fallback → LLM phrase parsing
- [ ] Caching for < 5s latency

Success Criteria:
- < 5s latency (with caching)
- Seamless fallback for unknown terms
- James validation of query quality

### Phase 4: MeSH Hierarchy (Future)
**Status**: Deferred
**Goal**: Use tree structure for broader/narrower expansion

Scope: ~3,500 neuroscience MeSH descriptors (C10, F02, F03 branches)

Deliverables:
- [ ] MeSH tree data for neuroscience subset
- [ ] Parent/child relationship navigation
- [ ] Intelligent broader/narrower suggestions

### Phase 5: LLM Context Awareness (Future)
**Status**: Deferred
**Goal**: Parse multi-word phrases and handle ambiguous terms

Example: "older adults with PD" → POPULATION_CONTEXT + CONDITION_DISEASE

---

## Database Strategy

**Decision: Option C (Hybrid)**

| Layer | Source | Size | Purpose |
|-------|--------|------|---------|
| Primary | 569 curated terms | Small | Gold standard with semantic types |
| Extended | ~3,500 MeSH neuroscience | Medium | Hierarchical relationships |
| Fallback | UMLS 325K | Large | Unknown term lookup |

---

## Testing Philosophy

**Hypothesis-Driven Process**:

1. **Before testing any new method**:
   - What specific problem does this solve?
   - What's the expected impact on query quality?
   - How will we measure success?

2. **Prototype first**:
   - 50-100 high-value terms covering all 7 categories
   - Include known problematic cases (TMS, MS, fMRI)
   - Get James feedback before scaling

3. **Compare methods**:
   - Use webapp for side-by-side comparison
   - Document results in markdown
   - Keep what works, discard what doesn't

---

## Success Metrics (Overall)

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Query relevance | Low (1 hit for MS+neuro) | High (5-20 hits) | PubMed result count |
| Semantic drift | High (wrong expansions) | Zero | Manual review of expansions |
| Classification accuracy | N/A | 95%+ | Compare to James's expected categories |
| Latency | 27s | < 5s | With caching |
| Expert validation | Partial | Full | James approval of benchmark queries |

---

## Open Questions

1. **Phase 1 scope**: Full 127 TUI mapping or start with common neuroscience TUIs only?
2. **Prototype term selection**: Should James approve the 50-100 term list?
3. **Timeline**: What's the target date for beta readiness?
4. **Resource allocation**: How much time can be dedicated per week?

---

## Next Steps

1. **Review this roadmap** - Does it align with the overall vision?
2. **Answer open questions** - Especially timeline and scope
3. **Approve Phase 1** - Semantic classification implementation plan
4. **Begin prototype** - 50-100 terms with semantic types

---

## Related Documents

- James's feedback: `docs/decisions/lex-stream-data-layer-problem-statement_JAMES.docx`
- Implementation plan: `plans/251204-semantic-classification-implementation.md`
- Research findings: `docs/analysis/2025-11-28_1400_lexstream-comprehensive-research.md`
