# Lex Stream Data Layer: Semantic Classification Implementation Plan

**Date**: 2025-12-04
**Status**: DRAFT - Awaiting approval
**Estimated Timeline**: 5 weeks to MVP

---

## Executive Summary

Implement semantic classification to fix the core problem: **Lex Stream doesn't know that "MS" is a disease and "neuromodulation" is an intervention**. Without this understanding, expansion rules fail.

**Key decisions from James (neuroscientist):**
1. Seven semantic categories (not 5)
2. Semantic classification FIRST, MeSH hierarchy SECOND
3. Hybrid approach: Database + LLM for classification
4. Prototype with 50-100 terms before committing

---

## The Seven Categories

| Category | UMLS Semantic Groups | Expansion Strategy |
|----------|---------------------|-------------------|
| POPULATION_CONTEXT | Living beings, Geographic, Activities, Events, Orgs, Occupations | Rarely expand (synonyms only) |
| CONDITION_DISEASE | Disorders | Synonyms, subtypes, hierarchical (NO mechanisms) |
| INTERVENTION_EXPOSURE | Procedures, Chemicals/Drugs | Synonyms, same modality (NO mechanisms/devices/outcomes) |
| OUTCOME_MEASURE | Physiology, Phenomena | Synonyms, scale variants, measurement labels |
| ANATOMY_SYSTEM | Anatomy | Hierarchical children, subregions (avoid overly broad) |
| MECHANISM_BIOLOGICAL | Genes/mol sequences, Concepts | ONLY direct synonyms (HIGH drift risk) |
| OBJECT_DEVICE | Objects | LIMITED expansion (physical things) |

---

## Project Structure

**Decision: STAY in NeuroDB-2**

Keep:
- `poc_api_first/` - Working comparison framework
- `poc_api_first/clients/` - UMLS, PubTator, PubMed APIs
- `poc_api_first/webapp/` - Comparison UI (deployed)
- `data/neuro_terms.json` - 569 curated terms (extend with semantic_type)

Deprecate:
- `convert_to_lexstream.py` - Old flat export
- `convert_umls_to_lexstream.py` - UMLS 325K becomes fallback only

---

## Implementation Phases

### Phase 1: Semantic Classification Infrastructure (Week 1-2)

**Tasks:**
1. Create `poc_api_first/semantic_types.py`
   - Define 7 categories as enum
   - Map all 127 UMLS TUIs to 7 categories
   - Define expansion rules per category

2. Extend `poc_api_first/clients/umls.py`
   - Current: 21 TUIs mapped to 5 categories
   - New: 127 TUIs mapped to 7 categories
   - Add `get_semantic_group()` method

3. Create `poc_api_first/expansion_rules.py`
   - Category-specific include/exclude rules
   - Max expansion limits per category
   - Anti-drift patterns (e.g., CONDITION excludes "pathway", "receptor")

**Data Schema Change** (add to each term):
```json
{
  "semantic_type": "CONDITION_DISEASE",
  "umls_cui": "C0026769",
  "umls_tui": "T047",
  "expansion_rules": {
    "include": ["synonyms", "subtypes"],
    "exclude": ["mechanisms"]
  }
}
```

---

### Phase 2: Prototype Testing (Week 2-3)

**70-term prototype set:**
- CONDITION_DISEASE (15): MS, Parkinson's, stroke, Alzheimer's, depression, epilepsy, ALS, TBI, autism, ADHD, migraine, neuropathy, dystonia, schizophrenia, dementia
- INTERVENTION_EXPOSURE (15): TMS, DBS, tDCS, fMRI, EEG, MEG, PET, neuromodulation, neurostimulation, optogenetics, rTMS, VNS, SCS, ECT, rehabilitation
- OUTCOME_MEASURE (10): motor function, cognition, memory, attention, gait, speech, pain, quality of life, disability, tremor
- ANATOMY_SYSTEM (10): motor cortex, hippocampus, basal ganglia, prefrontal cortex, cerebellum, thalamus, brainstem, spinal cord, corpus callosum, amygdala
- MECHANISM_BIOLOGICAL (10): neuroplasticity, long-term potentiation, dopamine, serotonin, glutamate, GABA, synaptic transmission, neuroinflammation, oxidative stress, apoptosis
- OBJECT_DEVICE (5): electrode, coil, implant, probe, sensor
- POPULATION_CONTEXT (5): elderly, pediatric, stroke survivors, healthy controls, patients

**Hypothesis Testing Template:**
```markdown
## HYP-XXX: [Name]

### Statement
[Expected behavior]

### Test Query
Input: "[query]"

### Expected Classification
| Term | Category | Expansion |
|------|----------|-----------|

### Success Criteria
- [ ] Classification accuracy
- [ ] Result count: 5-20 papers
- [ ] No semantic drift
- [ ] Latency: < 20s

### Results
[After test]

### Actions
[Changes needed]
```

---

### Phase 3: Category-Specific Expansion (Week 3-4)

**Create expander modules:**
```
poc_api_first/expanders/
├── base_expander.py
├── condition_expander.py      # Synonyms, subtypes (NO mechanisms)
├── intervention_expander.py   # Synonyms, same modality (NO mechanisms/devices)
├── outcome_expander.py        # Synonyms, scale variants
├── anatomy_expander.py        # Hierarchical children (avoid overly broad)
├── mechanism_expander.py      # ONLY direct synonyms (conservative)
├── object_expander.py         # LIMITED expansion
└── population_expander.py     # Rarely expand
```

**Anti-drift filtering example:**
```python
class ConditionExpander(BaseExpander):
    FORBIDDEN_PATTERNS = [
        r"pathway$",     # mechanisms
        r"signaling$",   # mechanisms
        r"receptor$",    # mechanisms
        r"neuron$",      # anatomy/mechanism
    ]
```

---

### Phase 4: Production Integration (Week 4-5)

**Database Enrichment Workflow:**
1. Export 569 terms for UMLS enrichment
2. Batch UMLS API to get CUI, TUI for each term
3. Map TUI to 7 categories
4. Manual review by James
5. Import enriched data

**Hybrid Classification Flow:**
```
User: "MS + neuromodulation"
  ↓
Step 1: Parse → ["ms", "neuromodulation"]
  ↓
Step 2: NeuroDB lookup (569 curated)
  "ms" → CONDITION_DISEASE
  "neuromodulation" → INTERVENTION_EXPOSURE
  ↓ (if not found)
Step 3: UMLS API fallback → Get TUI → Map to category
  ↓
Step 4: Category-specific expansion
  CONDITION: synonyms (no mechanisms)
  INTERVENTION: same modality (no mechanisms)
  ↓
Step 5: Query assembly
  ("Multiple Sclerosis"[MeSH] OR "MS"[tiab])
  AND
  ("neuromodulation"[tiab] OR "neurostimulation"[tiab])
  ↓
Step 6: PubMed search → 5 relevant papers
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `poc_api_first/semantic_types.py` | 7 categories, TUI mapping |
| `poc_api_first/expansion_rules.py` | Category-specific rules |
| `poc_api_first/expanders/*.py` | 7 category expanders |
| `scripts/enrich_semantic_types.py` | UMLS batch enrichment |
| `docs/testing/hypothesis_template.md` | Test template |
| `docs/testing/prototype_terms.md` | 70-term list |

## Files to Modify

| File | Changes |
|------|---------|
| `poc_api_first/clients/umls.py` | Expand TUI mapping (21→127) |
| `poc_api_first/poc_pipeline.py` | 7-category classification |
| `poc_api_first/tests/test_configurations.py` | Add SemanticClassificationConfig |
| `data/neuro_terms.json` | Add semantic_type, CUI, TUI fields |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Classification accuracy | 95%+ on prototype set |
| Query quality | 5-20 papers per query |
| Semantic drift | 0 cases (no tetramethylsilane for TMS) |
| Latency | < 20s prototype, < 5s production (with cache) |

---

## Deferred to Later

- **MeSH hierarchy trees** - After MVP validation (James: classification first)
- **LLM phrase parsing** - Phase 5+ (multi-word phrases like "older adults with PD")
- **Full UMLS 325K enrichment** - Use as fallback only, not primary

---

## Open Questions

1. **Timeline**: 5 weeks acceptable for beta pressure?
2. **Prototype terms**: Should James review/approve the 70-term selection?
3. **MeSH deferral**: OK to defer hierarchy to after MVP?
4. **Starting point**: Phase 1 infrastructure or jump to prototype testing?

---

## Source Documents

- James's feedback: `docs/decisions/lex-stream-data-layer-problem-statement_JAMES.docx`
- Research findings: `docs/analysis/2025-11-28_1400_lexstream-comprehensive-research.md`
- MeSH hierarchy scope: (Lex-stream-2) `docs/analysis/20251118-mesh-hierarchy-scope-and-staging.md`
