# Semantic Classification Architecture

**Date**: 2025-12-04
**Status**: Reference Documentation
**Related Plans**:
- [251204-lexstream-query-roadmap.md](../../plans/251204-lexstream-query-roadmap.md)
- [251204-semantic-classification-implementation.md](../../plans/251204-semantic-classification-implementation.md)

---

## Table of Contents

1. [The Core Problem](#the-core-problem)
2. [Key Decisions from Stakeholder Feedback](#key-decisions-from-stakeholder-feedback)
3. [What "Expand Appropriately" Means](#what-expand-appropriately-means)
4. [When Expansion Happens](#when-expansion-happens)
5. [Data Sources](#data-sources)
6. [The Comparison Webapp](#the-comparison-webapp)
7. [Config System & Extensibility](#config-system--extensibility)
8. [Where Semantic Classification Fits In](#where-semantic-classification-fits-in)

---

## The Core Problem

The system doesn't know that "MS" is a disease and "neuromodulation" is an intervention. Without this understanding, expansion rules fail and queries drift into irrelevant results.

**Example**: Query "MS + neuromodulation"

| Approach | Result | Problem |
|----------|--------|---------|
| No expansion | 1 hit | Too restrictive |
| Blind expansion | 1,943 hits | Semantic drift (inflammation, brain activity) |
| Smart expansion | 5-20 hits | Focused on disease + intervention intersection |

---

## Key Decisions from Stakeholder Feedback

> **Source Document**: [lex-stream-data-layer-problem-statement_JAMES.docx](../decisions/lex-stream-data-layer-problem-statement_JAMES.docx)
>
> James (neuroscientist) provided critical feedback that shaped this architecture. All design decisions should align with these principles.

### The Root Cause (James's Analysis)

> "The core failure we saw in MS + neuromodulation search was not about hierarchy - it was that the system didn't know MS is a disease and neuromodulation is an intervention, so it applied the wrong expansion patterns. Without knowing what a term IS, MeSH tree position is less useful."

### Decision 1: Seven Categories (Not Five)

James mapped UMLS's 15 semantic groups to 7 categories relevant for neuroscience:

| UMLS Semantic Group | Maps To |
|---------------------|---------|
| Living beings, Geographic areas, Activities, Events, Orgs, Occupations | POPULATION_CONTEXT |
| Disorders | CONDITION_DISEASE |
| Procedures, Chemicals & Drugs | INTERVENTION_EXPOSURE |
| Physiology, Phenomena | OUTCOME_MEASURE |
| Anatomy | ANATOMY_SYSTEM |
| Genes & molecular sequences, Concepts & ideas | MECHANISM_BIOLOGICAL |
| Objects | OBJECT_DEVICE |

### Decision 2: Classification First, Hierarchy Second

> "For the secret sauce, semantic classification comes first, MeSH hierarchy second... The tree only really helps once you know if X is a disease node or X is an anatomical structure."

**Implication**: Build 7-category classification before investing in MeSH tree integration.

### Decision 3: Category-Specific Expansion Rules

James provided detailed expansion rules per category:

| Category | Expand To | Never Expand To |
|----------|-----------|-----------------|
| **POPULATION_CONTEXT** | Rarely expand. Synonyms only (e.g., "older adults" → "aged", "elderly"). Hierarchical for rodents (mice/rats). | — |
| **CONDITION_DISEASE** | Exact synonyms, acronyms, clinical subtypes, hierarchical variants (early/late stage). | Mechanisms, non-clinical terms |
| **INTERVENTION_EXPOSURE** | Common synonyms, same modality/procedure. | Mechanisms, objects/devices, outcomes |
| **OUTCOME_MEASURE** | Synonyms, acronyms, measurement labels, scale variants. | — |
| **ANATOMY_SYSTEM** | Well-defined hierarchical children, known subregions. | Overly broad regions (e.g., "whole brain") |
| **MECHANISM_BIOLOGICAL** | Direct synonyms or direct canonical alternatives ONLY. | High drift risk — be conservative |
| **OBJECT_DEVICE** | Limited expansion — physical things, not conceptual. | — |

### Decision 4: Hybrid Classification Approach

> "Lex Stream will need a stable ontology but also flexibility given users may not be as coherent as we like. Hybrid approach seems like the only practical option here."

**What this means**:
- **Database-driven**: Pre-classify known terms with stable semantic_type
- **LLM fallback**: Parse multi-word phrases like "older adults with PD" → POPULATION_CONTEXT + CONDITION_DISEASE
- **Classification type is stable** (PD is always a disease), but **expansion behavior is context-aware**

### Decision 5: Option C (Hybrid Database Strategy)

> "Focused vocabulary but with the UMLS as a fallback for unexpected user inputs."

| Layer | Source | Purpose |
|-------|--------|---------|
| Primary | 569 curated terms | Gold standard with semantic types |
| Extended | ~3,500 MeSH neuroscience | Hierarchical relationships |
| Fallback | UMLS 325K | Unknown term lookup |

### Decision 6: Prototype First

> "Yes, we should prototype on a small, high-value subset of terms before committing."

**Action**: Test with 70 terms (10 per category) before enriching all 569 terms.

---

## What "Expand Appropriately" Means

**Core definition**: Different semantic categories get expanded using **different rules** to prevent semantic drift.

### The 7 Expansion Rule Sets

| Category | EXPAND TO | NEVER EXPAND TO |
|----------|-----------|-----------------|
| **CONDITION_DISEASE** | Synonyms, subtypes, hierarchical children | Mechanisms (dopamine, pathway), non-clinical terms |
| **INTERVENTION_EXPOSURE** | Synonyms, same modality (neurostimulation) | Mechanisms, devices, outcomes |
| **OUTCOME_MEASURE** | Synonyms, scale variants, measurement labels | — |
| **ANATOMY_SYSTEM** | Hierarchical children, subregions | Overly broad regions |
| **MECHANISM_BIOLOGICAL** | **ONLY direct synonyms** | Anything else (HIGH drift risk) |
| **OBJECT_DEVICE** | Direct synonyms only | Conceptual expansions |
| **POPULATION_CONTEXT** | Rarely expand (synonyms only) | — |

### Concrete Example

**Without appropriate expansion** (current behavior):
```
"MS" → expand to ALL related terms:
  multiple sclerosis, demyelination, autoimmune, inflammation,
  myelin, oligodendrocyte, T-cell, cytokine...

"neuromodulation" → expand to ALL related terms:
  neurostimulation, neural activity, brain activity,
  excitability, plasticity, synaptic transmission...

Result: 1,943 papers (drift into every paper mentioning inflammation + brain activity)
```

**With appropriate expansion** (planned behavior):
```
"MS" (classified as CONDITION_DISEASE)
  → ONLY synonyms + subtypes:
    "multiple sclerosis", "MS", "relapsing-remitting MS", "RRMS"
  → FORBIDDEN: mechanisms (demyelination, inflammation, cytokine)

"neuromodulation" (classified as INTERVENTION_EXPOSURE)
  → ONLY synonyms + same modality:
    "neurostimulation", "TMS", "DBS", "tDCS"
  → FORBIDDEN: mechanisms (plasticity, excitability), outcomes (improvement)

Result: 5-20 papers (focused on disease + intervention intersection)
```

### Anti-Drift Filtering (Implementation)

Each category expander has forbidden patterns:

```python
class ConditionExpander(BaseExpander):
    FORBIDDEN_PATTERNS = [
        r"pathway$",     # blocks "dopaminergic pathway"
        r"signaling$",   # blocks "cell signaling"
        r"receptor$",    # blocks "dopamine receptor"
        r"neuron$",      # blocks anatomy/mechanism crossover
    ]
```

---

## When Expansion Happens

Looking at the current pipeline (`poc_api_first/poc_pipeline.py`), the flow is:

```
run()
  │
  ├── 1. parse_input()        → ["ms", "neuromodulation"]
  │
  ├── 2. classify_terms()     → [{term: "ms", category: "CONDITION"}, ...]
  │
  ├── 3. build_query()        → calls expand_term() INSIDE build_query
  │                              ↑ EXPANSION HAPPENS HERE
  │
  └── 4. pubmed.search()      → execute query
```

### Current `expand_term()` Logic

```python
def expand_term(self, classification: Dict) -> List[str]:
    strategy = classification.get('expansion_strategy', 'narrow')

    synonyms = self.umls.get_synonyms(cui)  # Gets synonyms from UMLS API

    if strategy == 'narrow':
        return synonyms[:3]      # Top 3 synonyms
    elif strategy == 'moderate':
        return synonyms[:8]      # Top 8 synonyms
    elif strategy == 'broad':
        return synonyms[:15]     # Up to 15 synonyms
```

### Current Strategy Mapping

```python
EXPANSION_STRATEGY = {
    'CONDITION': 'narrow',     # Just synonyms
    'INTERVENTION': 'broad',   # Include related techniques
    'OUTCOME': 'moderate',     # Some related measures
    'ANATOMY': 'narrow',       # Specific terms only
    'OTHER': 'narrow',
    'UNKNOWN': 'narrow'
}
```

### The Problem

Current expansion is **quantity-based** (how many synonyms), not **type-based** (what KIND of synonyms).

**Example**: "dopamine" (MECHANISM) with `narrow` strategy gets 3 synonyms from UMLS, but those might include "dopaminergic pathway", "dopamine receptor" — no filtering based on what makes sense for mechanisms.

### Planned Fix

Replace single `expand_term()` with **7 category-specific expanders**:

```
poc_api_first/expanders/
├── base_expander.py
├── condition_expander.py      # Synonyms, subtypes (NO mechanisms)
├── intervention_expander.py   # Same modality only
├── outcome_expander.py        # Synonyms, scale variants
├── anatomy_expander.py        # Hierarchical children
├── mechanism_expander.py      # ONLY direct synonyms (conservative)
├── object_expander.py         # LIMITED expansion
└── population_expander.py     # Rarely expand
```

---

## Data Sources

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INPUT                                      │
│                      "MS + neuromodulation"                              │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ parse
                               ▼
                      ["ms", "neuromodulation"]
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  SOURCE 1       │   │  SOURCE 2       │   │  SOURCE 3       │
│  NeuroDB-2      │   │  UMLS API       │   │  PubTator API   │
│  (569 terms)    │   │  (325K terms)   │   │  (disambiguation)│
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│ Has today:      │   │ Has today:      │   │ Has today:      │
│ • Term          │   │ • CUI           │   │ • Resolved term │
│ • Definition    │   │ • TUI (127)     │   │ • Entity type   │
│ • MeSH term     │   │ • Synonyms      │   │ • Confidence    │
│ • Synonyms 1-3  │   │ • Semantic type │   │                 │
│ • Abbreviation  │   │                 │   │                 │
│ • Associated 1-8│   │                 │   │                 │
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│ MISSING:        │   │ CURRENT:        │   │ Role:           │
│ ❌ semantic_type│   │ 21 TUIs mapped  │   │ Resolve "MS" →  │
│ ❌ CUI          │   │ to 5 categories │   │ "Multiple       │
│ ❌ TUI          │   │ (need 127 → 7)  │   │  Sclerosis"     │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   CLASSIFICATION     │
                    │   (7 categories)     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   EXPANSION          │
                    │   (category-aware)   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   PubMed Query       │
                    └──────────────────────┘
```

### What Each Source Provides

| Source | Classification | Expansion | Current Status |
|--------|---------------|-----------|----------------|
| **NeuroDB-2** (569 terms) | ❌ No semantic_type field | ✅ Synonyms 1-3, Associated 1-8 | Missing CUI/TUI |
| **UMLS API** | ✅ TUI → 5 categories (need 7) | ✅ Unlimited synonyms via API | 21 TUIs mapped |
| **PubTator API** | ⚠️ Entity types only | ❌ No synonyms | Disambiguation only |

### The Gap: NeuroDB-2

NeuroDB-2 has great curated synonyms/associations but **no semantic classification**:

```json
// Current neuro_terms.json
{
  "Term": "Acetylcholine",
  "Synonym 1": null,
  "Abbreviation": "ACh",
  "Commonly Associated Term 1": "neurotransmitter",
  // ❌ NO semantic_type
  // ❌ NO CUI
  // ❌ NO TUI
}
```

### The Gap: UMLS Client

UMLS API has classification (TUI) but only 21 TUIs mapped to 5 categories:

```python
# Current umls.py
CATEGORY_MAP = {
    'T047': 'CONDITION',    # Disease or Syndrome
    'T061': 'INTERVENTION', # Therapeutic Procedure
    'T042': 'OUTCOME',      # Organ Function
    'T023': 'ANATOMY',      # Body Part
    # ... only 21 TUIs mapped
    # ❌ Missing: POPULATION_CONTEXT, MECHANISM_BIOLOGICAL, OBJECT_DEVICE
}
```

### The Plan: Connect Them

**Step 1**: Enrich NeuroDB-2 with UMLS data

```json
// PLANNED neuro_terms.json
{
  "Term": "Acetylcholine",
  "semantic_type": "MECHANISM_BIOLOGICAL",  // ← NEW
  "umls_cui": "C0001041",                   // ← NEW
  "umls_tui": "T123",                       // ← NEW
  "Synonym 1": null,
  "Commonly Associated Term 1": "neurotransmitter",
}
```

**Step 2**: Expand UMLS TUI mapping (21 → 127 TUIs → 7 categories)

```python
# PLANNED umls.py
CATEGORY_MAP = {
    # CONDITION_DISEASE (existing + more)
    'T047': 'CONDITION_DISEASE',
    'T048': 'CONDITION_DISEASE',

    # MECHANISM_BIOLOGICAL (NEW)
    'T116': 'MECHANISM_BIOLOGICAL',  # Amino Acid, Peptide, Protein
    'T123': 'MECHANISM_BIOLOGICAL',  # Biologically Active Substance

    # POPULATION_CONTEXT (NEW)
    'T100': 'POPULATION_CONTEXT',    # Age Group
    'T101': 'POPULATION_CONTEXT',    # Patient or Disabled Group
    # ... all 127 TUIs mapped
}
```

### Hybrid Lookup Flow (Planned)

```
User: "acetylcholine dysfunction"
         │
         ▼
Step 1: NeuroDB-2 lookup
        "acetylcholine" → FOUND
        semantic_type: MECHANISM_BIOLOGICAL
        synonyms: ["ACh", "cholinergic"]
         │
         ▼
Step 2: Category-specific expansion
        MECHANISM_BIOLOGICAL → conservative (synonyms only)
        Expand to: ["acetylcholine", "ACh"]
        FORBIDDEN: "cholinergic pathway", "receptor"
         │
         ▼
Step 3: Unknown term fallback
        "dysfunction" → NOT in NeuroDB-2
        → UMLS API lookup → T046 → CONDITION_DISEASE
```

---

## The Comparison Webapp

The webapp (`poc_api_first/webapp/app.py`) is a **configuration testing framework** that lets you compare different tool combinations side-by-side.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WEBAPP (Flask)                                   │
│                    poc_api_first/webapp/app.py                          │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONFIG_METADATA (5 configs)                          │
├─────────────────────────────────────────────────────────────────────────┤
│ neurodb_only  │ umls_only │ pubtator_only │ umls_pubtator │ full_hybrid │
└───────┬───────┴─────┬─────┴───────┬───────┴───────┬───────┴──────┬──────┘
        │             │             │               │              │
        ▼             ▼             ▼               ▼              ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                   test_configurations.py (Config Classes)                  │
├───────────────┬───────────────┬───────────────┬───────────────┬───────────┤
│NeuroDBOnly    │ UMLSOnly      │ PubTatorOnly  │ UMLSPubTator  │FullHybrid │
│               │               │               │               │           │
│• NeuroDB only │• UMLS API     │• PubTator API │• PubTator →   │• NeuroDB →│
│• No external  │• No disambig  │• No classify  │   UMLS        │  PubTator │
│  APIs         │               │               │               │   → UMLS  │
└───────────────┴───────────────┴───────────────┴───────────────┴───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  SemanticQueryPipeline│
                    │  (poc_pipeline.py)    │
                    │                       │
                    │  1. parse_input()     │
                    │  2. classify_terms()  │ ← Each config provides its own
                    │  3. build_query()     │   classify_fn to the pipeline
                    │  4. pubmed.search()   │
                    └──────────────────────┘
```

### How Configs Differ

| Config | Classification Source | Expansion Source |
|--------|----------------------|------------------|
| **NeuroDBOnly** | None (returns UNKNOWN) | NeuroDB abbreviations only |
| **UMLSOnly** | UMLS API (TUI → 5 categories) | UMLS synonyms |
| **PubTatorOnly** | None (entity type only) | PubTator disambiguation |
| **UMLSPubTator** | UMLS API | PubTator + UMLS synonyms |
| **FullHybrid** | UMLS API | NeuroDB → PubTator → UMLS |

### The Key: Custom `classify_fn`

Each config injects its own classification function into the pipeline:

```python
class NeuroDBOnlyConfig:
    def run(self, keywords, ...):
        pipeline = SemanticQueryPipeline(
            classify_fn=self._classify_all  # ← Custom classify_fn
        )
        return pipeline.run(keywords, ...)

    def _classify_all(self, terms):
        return [self.classify_term(t) for t in terms]

    def classify_term(self, term):
        # Only looks up in NeuroDB
        # Returns category: 'UNKNOWN' (no semantic classification)
```

### Webapp User Flow

1. User opens webapp
2. Selects 2-5 configs to compare
3. Enters keywords (e.g., "MS + neuromodulation")
4. Webapp runs all selected configs **in parallel**
5. Results displayed side-by-side:
   - Resolved terms
   - Classifications
   - Generated query
   - Paper count
   - Sample articles (with overlap highlighting)

---

## Config System & Extensibility

The comparison framework is designed for easy experimentation. Add new APIs, remove unused ones, or create new combinations with minimal code changes.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           EXTENSIBLE CONFIG SYSTEM                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐      ┌──────────────────┐      ┌────────────────┐ │
│  │  API Clients     │      │  Config Classes  │      │  Webapp        │ │
│  │  (clients/*.py)  │ ──── │  (test_config.py)│ ──── │  (app.py)      │ │
│  └──────────────────┘      └──────────────────┘      └────────────────┘ │
│                                                                          │
│  Add new client ────────── Create config class ────── Register in       │
│                            with classify_fn           CONFIG_METADATA   │
└─────────────────────────────────────────────────────────────────────────┘
```

### The Key Design Pattern: Dependency Injection

Each config controls its own classification logic via `classify_fn`:

```python
class AnyConfig:
    def run(self, user_input, ...):
        pipeline = SemanticQueryPipeline(
            classify_fn=self._classify_terms_batch  # ← Injected
        )
        return pipeline.run(user_input, ...)
```

The pipeline doesn't care HOW classification happens—it just calls the injected function.

### How to Add a New API

**3 steps to add any new API:**

| Step | File | Action |
|------|------|--------|
| 1 | `poc_api_first/clients/new_api.py` | Create API client class |
| 2 | `poc_api_first/tests/test_configurations.py` | Create config class |
| 3 | `poc_api_first/webapp/app.py` | Add to `CONFIG_METADATA` dict |

**Example: Adding a hypothetical BioPortal API**

```python
# Step 1: poc_api_first/clients/bioportal.py
class BioPortalClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://data.bioontology.org"

    def classify_term(self, term):
        # API call logic
        return {'term': term, 'category': 'CONDITION_DISEASE', ...}

# Step 2: Add to test_configurations.py
class BioPortalOnlyConfig:
    name = "BioPortalOnly"

    def __init__(self):
        self.client = BioPortalClient(os.getenv("BIOPORTAL_API_KEY"))

    def classify_term(self, term):
        return self.client.classify_term(term)

    def _classify_terms_batch(self, terms):
        return [self.classify_term(t) for t in terms]

    def run(self, user_input, days=60, max_results=20, verbose=False):
        from poc_api_first.poc_pipeline import SemanticQueryPipeline
        pipeline = SemanticQueryPipeline(classify_fn=self._classify_terms_batch)
        return pipeline.run(user_input=user_input, days=days, max_results=max_results)

# Step 3: Add to CONFIG_METADATA in webapp/app.py
'bioportal_only': {
    'name': 'BioPortal Only',
    'description': 'BioPortal ontology lookup',
    'class': BioPortalOnlyConfig
}
```

**Effort**: ~50-100 lines of code, ~30 minutes.

### How to Remove an API

**Example: Removing PubTator**

| Step | File | Action |
|------|------|--------|
| 1 | `test_configurations.py` | Delete `PubTatorOnlyConfig` class |
| 2 | `test_configurations.py` | Delete `UMLSPubTatorConfig` class |
| 3 | `test_configurations.py` | Remove PubTator layer from `FullHybridConfig.classify_term()` |
| 4 | `webapp/app.py` | Remove entries from `CONFIG_METADATA` |
| 5 | `clients/pubtator.py` | Delete file (optional) |

**Before** (FullHybrid with 3 layers):
```python
def classify_term(self, term):
    # Layer 1: NeuroDB
    if term.lower() in self.abbreviations:
        return ...

    # Layer 2: PubTator  ← DELETE THIS BLOCK
    if self.is_abbreviation(term):
        disambiguation = self.pubtator_client.disambiguate_term(term)
        ...

    # Layer 3: UMLS fallback
    return self.umls_client.classify_term(term)
```

**After** (2 layers):
```python
def classify_term(self, term):
    # Layer 1: NeuroDB
    if term.lower() in self.abbreviations:
        return ...

    # Layer 2: UMLS fallback
    return self.umls_client.classify_term(term)
```

**Why it's easy**: No shared state, no inheritance, pipeline doesn't know which APIs you use.

### API Combination Strategies

When combining multiple APIs in `classify_term()`, choose a strategy:

| Strategy | Pattern | Use Case |
|----------|---------|----------|
| **Sequential** | A → B (A feeds B) | Disambiguate → then classify |
| **Priority Cascade** | A → B → C (first match wins) | Best source first, fallbacks |
| **Conditional** | if X then A else B | Different APIs for different term types |
| **Parallel + Merge** | A + B → combine by confidence | Multiple opinions, pick best |

**Sequential Example** (UMLSPubTator):
```python
def classify_term(self, term):
    # Step 1: PubTator disambiguates
    if self.is_abbreviation(term):
        result = self.pubtator_client.disambiguate_term(term)
        if result['confidence'] > 0.5:
            term = result['resolved']  # "MS" → "Multiple Sclerosis"

    # Step 2: UMLS classifies the resolved term
    return self.umls_client.classify_term(term)
```

**Priority Cascade Example** (FullHybrid):
```python
def classify_term(self, term):
    # Layer 1: NeuroDB (highest priority, curated)
    if term.lower() in self.abbreviations:
        resolved = self.abbreviations[term.lower()]
        result = self.umls_client.classify_term(resolved)
        result['confidence'] = 1.0
        return result  # ← EARLY RETURN

    # Layer 2: PubTator (biomedical general)
    if self.is_abbreviation(term):
        disambiguation = self.pubtator_client.disambiguate_term(term)
        if disambiguation['confidence'] > 0.5:
            result = self.umls_client.classify_term(disambiguation['resolved'])
            result['confidence'] = 0.9
            return result  # ← EARLY RETURN

    # Layer 3: UMLS direct (fallback)
    result = self.umls_client.classify_term(term)
    result['confidence'] = 0.5
    return result
```

### Current API Comparison Matrix

| Config | NeuroDB | PubTator | UMLS | Strategy |
|--------|:-------:|:--------:|:----:|----------|
| NeuroDBOnly | ✓ | | | Single layer |
| PubTatorOnly | | ✓ | | Single layer |
| UMLSOnly | | | ✓ | Single layer |
| UMLSPubTator | | ✓ | ✓ | Sequential |
| FullHybrid | ✓ | ✓ | ✓ | Priority cascade |

### Possible New Combinations

| Config | Layers | Test Hypothesis |
|--------|--------|-----------------|
| NeuroDBUMLS | NeuroDB → UMLS | Is PubTator needed if we have NeuroDB? |
| UMLSBioPortal | UMLS + BioPortal | Do ontology sources complement UMLS? |
| AllSources | NeuroDB → PubTator → UMLS → BioPortal | More layers = better? |

### What the Webapp Shows

When you run a comparison, each config displays:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Config: FullHybrid                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Resolved Terms:                                                         │
│    "MS" → "Multiple Sclerosis" (NeuroDB, confidence: 1.0)               │
│    "neuromodulation" → "neuromodulation" (UMLS, confidence: 0.5)        │
│                                                                          │
│  Classifications:                                                        │
│    Multiple Sclerosis → CONDITION (T047)                                │
│    neuromodulation → INTERVENTION (T061)                                │
│                                                                          │
│  Generated Query:                                                        │
│    ("Multiple Sclerosis"[MeSH] OR "MS"[tiab])                           │
│    AND ("neuromodulation"[tiab] OR "neurostimulation"[tiab])            │
│                                                                          │
│  Results: 5 papers                                                       │
│                                                                          │
│  Articles:                                                               │
│    1. "TMS effects on MS patients..." (PMID: 12345) ★ UNIQUE            │
│    2. "Neuromodulation in multiple sclerosis..." (PMID: 23456)          │
│    ...                                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Features**:
- Side-by-side comparison (select 2-5 configs)
- Parallel execution (all configs run simultaneously)
- Article overlap highlighting (★ UNIQUE = only found by this config)
- Full query visibility (see exactly what was sent to PubMed)

### Adding a New Config to Webapp

After creating a config class, register it in `webapp/app.py`:

```python
CONFIG_METADATA = {
    # ... existing configs ...

    'my_new_config': {
        'name': 'My New Config',
        'description': 'Description shown in UI',
        'class': MyNewConfigClass
    }
}
```

The webapp automatically:
- Shows checkbox for new config
- Runs it in parallel with others
- Displays results in same format
- Computes article overlaps

---

## Where Semantic Classification Fits In

### Current State

Only `UMLSOnly`, `UMLSPubTator`, and `FullHybrid` do classification (via UMLS API with 5 categories).

### Planned: New Config

Add `SemanticClassificationConfig` for 7-category classification with category-specific expansion:

```python
# PLANNED: New config in test_configurations.py
class SemanticClassificationConfig:
    """
    7-category semantic classification with category-specific expansion.
    """
    name = "SemanticClassification"

    def __init__(self):
        # Load enriched NeuroDB with semantic_type
        self.neurodb = load_enriched_neurodb()
        self.umls = UMLSClient()  # Fallback
        self.expanders = {
            'CONDITION_DISEASE': ConditionExpander(),
            'INTERVENTION_EXPOSURE': InterventionExpander(),
            'OUTCOME_MEASURE': OutcomeExpander(),
            'ANATOMY_SYSTEM': AnatomyExpander(),
            'MECHANISM_BIOLOGICAL': MechanismExpander(),
            'OBJECT_DEVICE': ObjectExpander(),
            'POPULATION_CONTEXT': PopulationExpander(),
        }

    def classify_term(self, term):
        # 1. Try NeuroDB (enriched with semantic_type)
        if term in self.neurodb:
            return {
                'term': term,
                'category': self.neurodb[term]['semantic_type'],  # ← 7 categories
            }

        # 2. Fallback to UMLS API (127 TUI → 7 categories)
        result = self.umls.classify_term(term)
        return self._map_to_7_categories(result)

    def expand_term(self, classification):
        category = classification['category']
        expander = self.expanders[category]  # ← Category-specific
        return expander.expand(classification)
```

### Webapp Flow After Implementation

```
User selects: "SemanticClassification" config
User enters: "MS + neuromodulation"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ SemanticClassificationConfig.run()                                       │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Parse → ["ms", "neuromodulation"]                                     │
│                                                                          │
│ 2. Classify (7-category):                                                │
│    "ms" → NeuroDB lookup → semantic_type: CONDITION_DISEASE              │
│    "neuromodulation" → NeuroDB lookup → semantic_type: INTERVENTION      │
│                                                                          │
│ 3. Expand (category-specific):                                           │
│    CONDITION_DISEASE → ConditionExpander                                 │
│        → synonyms only: ["multiple sclerosis", "MS"]                     │
│        → FORBIDDEN: mechanisms                                           │
│    INTERVENTION → InterventionExpander                                   │
│        → same modality: ["neurostimulation", "TMS", "DBS"]               │
│        → FORBIDDEN: mechanisms, outcomes                                 │
│                                                                          │
│ 4. Build query with category-aware formatting                            │
│ 5. PubMed search → 5-20 relevant papers                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Summary: Before vs After

| Component | Current | After Plan |
|-----------|---------|------------|
| **Webapp** | Compares 5 configs | Add SemanticClassificationConfig |
| **Classification** | 5 categories (UMLS only) | 7 categories (NeuroDB + UMLS) |
| **Expansion** | Count-based (narrow/moderate/broad) | Category-specific rules + forbidden patterns |
| **NeuroDB-2** | No semantic_type | Enriched with CUI/TUI/semantic_type |
| **UMLS mapping** | 21 TUIs → 5 categories | 127 TUIs → 7 categories |
| **Testing** | Manual comparison | Hypothesis-driven with clear success criteria |

---

## Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1 | Weeks 1-2 | 7-category taxonomy, TUI mapping, expansion rules |
| Phase 2 | Week 3 | 70-term prototype testing |
| Phase 3 | Weeks 3-4 | Category-specific expanders |
| Phase 4 | Weeks 4-5 | NeuroDB enrichment, production integration |
| **DEFERRED** | — | MeSH hierarchy trees, LLM phrase parsing |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Query relevance | 1 hit (MS+neuro) | 5-20 hits |
| Semantic drift | High | Zero |
| Classification accuracy | N/A | 95%+ |
| Latency | 27s | < 5s (with cache) |

---

## Related Files

### Stakeholder Feedback (Authoritative)

| File | Purpose |
|------|---------|
| `docs/decisions/lex-stream-data-layer-problem-statement_JAMES.docx` | **Primary source** — James's neuroscientist feedback defining 7 categories, expansion rules, and architectural decisions. All design should align with this. |

### Planning Documents

| File | Purpose |
|------|---------|
| `plans/251204-lexstream-query-roadmap.md` | Strategic roadmap (the WHY) |
| `plans/251204-semantic-classification-implementation.md` | Implementation plan (the HOW) |

### Code Files

| File | Purpose |
|------|---------|
| `poc_api_first/poc_pipeline.py` | Core pipeline (parse → classify → expand → query) |
| `poc_api_first/clients/umls.py` | UMLS API client (TUI mapping here) |
| `poc_api_first/tests/test_configurations.py` | Config classes for webapp |
| `poc_api_first/webapp/app.py` | Flask webapp |
| `data/neuro_terms.json` | NeuroDB-2 (569 curated terms) |

---

## Glossary

### Core Concepts

| Term | Definition |
|------|------------|
| **Semantic Classification** | Categorizing terms by what they represent (disease, intervention, anatomy, etc.) rather than treating all terms equally. Enables category-specific expansion rules. |
| **Semantic Drift** | When query expansion adds terms that are technically related but contextually wrong. Example: expanding "MS" (disease) to include "demyelination" (mechanism) pollutes results with basic science papers instead of clinical trials. |
| **Query Expansion** | Adding synonyms, related terms, or hierarchical relatives to a search term to improve recall. The challenge is expanding enough to catch relevant papers without drifting into irrelevant ones. |
| **Category-Specific Expansion** | Applying different expansion rules based on term category. Diseases expand to synonyms only; interventions expand to same-modality techniques; mechanisms barely expand at all. |

### UMLS Terminology

| Term | Definition |
|------|------------|
| **UMLS** | Unified Medical Language System. NIH's comprehensive biomedical vocabulary database containing millions of concepts from 200+ source vocabularies. |
| **CUI** | Concept Unique Identifier. A stable identifier for a concept across all UMLS source vocabularies. Example: `C0026769` = Multiple Sclerosis. |
| **TUI** | Type Unique Identifier. Identifies the semantic type of a concept. Example: `T047` = Disease or Syndrome. There are 127 TUIs organized into 15 semantic groups. |
| **Semantic Type** | A category assigned to UMLS concepts describing what kind of thing it is. Examples: Disease or Syndrome (T047), Therapeutic Procedure (T061), Body Part (T023). |
| **Atom** | A specific name string from a specific source vocabulary. A concept (CUI) has many atoms (synonyms) from different sources. |

### MeSH Terminology

| Term | Definition |
|------|------------|
| **MeSH** | Medical Subject Headings. NLM's controlled vocabulary for indexing PubMed articles. Hierarchically organized into trees. |
| **MeSH Descriptor** | An official MeSH term used for indexing. Example: "Multiple Sclerosis" is a descriptor; "MS" is not. |
| **MeSH Tree** | Hierarchical organization of MeSH terms. A term can appear in multiple trees. Example: Parkinson's Disease appears under Basal Ganglia Diseases, Movement Disorders, AND Synucleinopathies. |
| **[MeSH] tag** | PubMed search field that matches against MeSH indexing. More precise than title/abstract search but requires exact MeSH terms. |
| **[tiab] tag** | PubMed search field for Title and Abstract. Broader than [MeSH] but may include irrelevant matches. |

### Project-Specific Terms

| Term | Definition |
|------|------------|
| **NeuroDB-2** | This project's curated database of 569 neuroscience terms with definitions, synonyms, abbreviations, and associated terms. Currently lacks semantic classification (CUI/TUI). |
| **Lex Stream** | The downstream query generation system that consumes NeuroDB-2 data. Generates PubMed queries for researchers monitoring niche topics. |
| **PubTator** | NCBI's biomedical text mining tool. Used for disambiguation (resolving "MS" → "Multiple Sclerosis") based on biomedical context. |
| **Config** | A specific combination of tools/APIs used for query generation. The webapp compares multiple configs side-by-side. Example: "FullHybrid" = NeuroDB + PubTator + UMLS. |
| **Expander** | A module that takes a classified term and returns expanded terms based on category-specific rules. Planned: 7 expanders, one per semantic category. |

### The 7 Semantic Categories

| Category | What It Represents | Expansion Behavior |
|----------|-------------------|-------------------|
| **CONDITION_DISEASE** | Diseases, disorders, symptoms | Synonyms + subtypes only. Never mechanisms. |
| **INTERVENTION_EXPOSURE** | Procedures, drugs, therapies | Same modality only. Never outcomes. |
| **OUTCOME_MEASURE** | What's measured in studies | Synonyms + scale variants. |
| **ANATOMY_SYSTEM** | Body parts, brain regions | Hierarchical children. Avoid broad regions. |
| **MECHANISM_BIOLOGICAL** | Biological processes, molecules | ONLY direct synonyms. High drift risk. |
| **OBJECT_DEVICE** | Physical instruments, implants | Direct synonyms only. |
| **POPULATION_CONTEXT** | Patient groups, demographics | Rarely expand. |
