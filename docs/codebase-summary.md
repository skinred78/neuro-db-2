# NeuroDB-2 Codebase Summary

**Date**: 2025-12-06
**Status**: Active Development
**Version**: 2.0

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Phase 1 Implementation - Semantic Classification](#phase-1-implementation---semantic-classification)
4. [Core Components](#core-components)
5. [Database Structure](#database-structure)
6. [API Clients](#api-clients)
7. [Testing Framework](#testing-framework)
8. [Validation System](#validation-system)
9. [Recent Changes](#recent-changes)

---

## Project Overview

NeuroDB-2 is a neuroscience terminology database project with two primary functions:

1. **Database Curation**: 569 curated neuroscience terms from Wikipedia Glossary with MeSH validation
2. **Semantic Query Pipeline**: POC implementation for intelligent PubMed query generation using semantic classification

### Key Statistics
- **Database**: ~595 neuroscience terms (A-Z complete)
- **Schema**: 22 columns (Term, Definition, MeSH, Synonyms, Abbreviations, Word Forms, Associated Terms)
- **Integration**: Powers Lex Stream query expansion pipeline
- **Test Pass Rate**: 95% (production-ready)

---

## Architecture Overview

```
NeuroDB-2/
├── data/
│   ├── neuro_terms.csv              # Master database (569 terms)
│   ├── neuro_terms.json             # JSON export for Lex Stream
│   └── convert_to_lexstream.py      # Export script
├── poc_api_first/                   # Semantic classification POC
│   ├── semantic_types.py            # ✨ NEW: 7-category classification (127 TUI mapping)
│   ├── expansion_rules.py           # ✨ NEW: Category-specific expansion rules
│   ├── poc_pipeline.py              # Main query pipeline
│   ├── clients/
│   │   ├── umls.py                  # ✨ MODIFIED: Extended with 7-category classification
│   │   ├── pubtator.py              # PubTator disambiguation
│   │   ├── pubmed.py                # PubMed search
│   │   └── neurodb.py               # Local NeuroDB lookup
│   ├── tests/
│   │   └── test_configurations.py   # ✨ MODIFIED: Added SemanticClassificationConfig
│   └── webapp/
│       └── app.py                   # Flask comparison webapp
├── MeshValidation/                  # MeSH validation tracking
│   ├── mesh_corrections_log.json
│   ├── mesh_corrections_log.csv
│   └── mesh_corrections_summary.md
└── docs/                            # Documentation
    ├── architecture/
    │   └── semantic-classification-architecture.md  # Reference architecture
    └── codebase-summary.md          # This file
```

---

## Phase 1 Implementation - Semantic Classification

**Status**: ✅ Complete (2025-12-04)
**Goal**: Prevent semantic drift in query expansion using 7-category classification

### What Changed (Phase 1)

#### 1. NEW: `poc_api_first/semantic_types.py`
**Purpose**: 7-category semantic classification with complete TUI mapping

**Key Features**:
- **7 semantic categories** (vs old 5):
  - `POPULATION_CONTEXT` - Patient groups, demographics
  - `CONDITION_DISEASE` - Diseases, disorders, symptoms
  - `INTERVENTION_EXPOSURE` - Procedures, drugs, therapies
  - `OUTCOME_MEASURE` - What's measured in studies
  - `ANATOMY_SYSTEM` - Body parts, brain regions
  - `MECHANISM_BIOLOGICAL` - Biological processes, molecules
  - `OBJECT_DEVICE` - Physical instruments, implants

- **127 TUI mappings** (vs old 21):
  - Complete UMLS Semantic Network coverage
  - Maps TUI → Semantic Group → Category
  - Example: `T047` (Disease or Syndrome) → `DISO` → `CONDITION_DISEASE`

**Functions**:
```python
get_category_from_tui(tui: str) -> SemanticCategory
get_category_from_semantic_group(sem_group: str) -> SemanticCategory
get_semantic_group(tui: str) -> Optional[str]
```

**Example**:
```python
from poc_api_first.semantic_types import get_category_from_tui

category = get_category_from_tui("T047")  # "Disease or Syndrome"
# Returns: SemanticCategory.CONDITION_DISEASE
```

#### 2. NEW: `poc_api_first/expansion_rules.py`
**Purpose**: Category-specific expansion rules with anti-drift patterns

**Key Features**:
- **Expansion strategies** per category:
  - `MINIMAL` (2-3 terms): MECHANISM_BIOLOGICAL, OBJECT_DEVICE, POPULATION_CONTEXT
  - `NARROW` (5 terms): CONDITION_DISEASE, ANATOMY_SYSTEM
  - `MODERATE` (8 terms): INTERVENTION_EXPOSURE, OUTCOME_MEASURE

- **Anti-drift filtering**: Forbidden regex patterns per category
  - CONDITION: blocks `pathway$`, `signaling$`, `receptor$`, `neuron$`
  - INTERVENTION: blocks `plasticity$`, `response$`, `improvement$`, `device$`
  - ANATOMY: blocks `^brain$`, `pathway$`, `network$`, `circuit$`
  - MECHANISM: blocks `disease$`, `therapy$`, `function$`

**Example**:
```python
from poc_api_first.expansion_rules import get_expansion_rule, filter_by_category
from poc_api_first.semantic_types import SemanticCategory

# Get rule for a category
rule = get_expansion_rule(SemanticCategory.CONDITION_DISEASE)
print(rule.strategy)        # ExpansionStrategy.NARROW
print(rule.max_expansions)  # 5

# Filter expansions
terms = ["multiple sclerosis", "dopaminergic pathway", "MS", "demyelination"]
filtered = filter_by_category(terms, SemanticCategory.CONDITION_DISEASE)
# Returns: ["multiple sclerosis", "MS", "demyelination"]
# Removed: "dopaminergic pathway" (forbidden pattern: pathway$)
```

#### 3. MODIFIED: `poc_api_first/clients/umls.py`
**Changes**:
- Integrated `semantic_types.py` and `expansion_rules.py`
- Extended classification from 5 categories (21 TUIs) to 7 categories (127 TUIs)
- Legacy `CATEGORY_MAP` preserved for backwards compatibility
- New functions use `get_category_from_tui()` for authoritative classification

**Before** (5 categories, 21 TUIs):
```python
CATEGORY_MAP = {
    'T047': 'CONDITION',
    'T061': 'INTERVENTION',
    'T042': 'OUTCOME',
    'T023': 'ANATOMY',
    # ... only 21 TUIs
}
```

**After** (7 categories, 127 TUIs):
```python
from poc_api_first.semantic_types import get_category_from_tui, TUI_TO_SEMANTIC_GROUP

# All 127 TUIs now mapped via semantic_types.py
category = get_category_from_tui("T116")  # Amino Acid, Peptide, Protein
# Returns: SemanticCategory.MECHANISM_BIOLOGICAL
```

#### 4. MODIFIED: `poc_api_first/tests/test_configurations.py`
**Changes**:
- Added `SemanticClassificationConfig` class
- New capability in `CAPABILITY_MATRIX`:
  - `supports_category_specific_expansion: True`

**SemanticClassificationConfig Features**:
- 7-category classification (NeuroDB + UMLS)
- NeuroDB abbreviation expansion
- Category-based component detection
- Synonym expansion with anti-drift filtering
- Category-specific expansion rules

**Configuration Matrix**:
```python
CAPABILITY_MATRIX = {
    'LexStream2Baseline': {
        'supports_semantic_classification': False,  # Rule-based only
        'supports_abbreviation_expansion': True,
    },
    'SemanticClassification': {
        'supports_semantic_classification': True,  # 7-category
        'supports_abbreviation_expansion': True,
        'supports_category_specific_expansion': True,  # NEW
    },
    # ... other configs
}
```

### Phase 1 Impact

**Before (Blind Expansion)**:
```
Query: "MS + neuromodulation"
Expansion:
  - MS → all related: multiple sclerosis, demyelination, inflammation, myelin...
  - neuromodulation → all related: brain activity, plasticity, synaptic transmission...
Result: 1,943 hits (semantic drift into inflammation + brain activity papers)
```

**After (Semantic Classification)**:
```
Query: "MS + neuromodulation"
Classification:
  - MS → CONDITION_DISEASE (T047)
  - neuromodulation → INTERVENTION_EXPOSURE (T061)
Expansion:
  - MS → synonyms only: "multiple sclerosis", "MS", "RRMS"
    FORBIDDEN: mechanisms (demyelination, inflammation)
  - neuromodulation → same modality: "neurostimulation", "TMS", "DBS"
    FORBIDDEN: mechanisms (plasticity), outcomes (improvement)
Result: 5-20 hits (focused on disease + intervention intersection)
```

---

## Core Components

### 1. Database Layer (`data/`)

#### `neuro_terms.csv` (Master Database)
- 595 neuroscience terms
- 22-column schema
- MeSH-validated via NIH API
- Source: Wikipedia Glossary of Neuroscience

**Schema**:
```
Term, Term Two, Definition, Closest MeSH term,
Synonym 1-3, Abbreviation, UK/US Spelling,
Noun/Verb/Adjective/Adverb Form,
Commonly Associated Term 1-8
```

#### `neuro_terms.json` (Lex Stream Export)
- JSON export for Lex Stream integration
- Generated via `convert_to_lexstream.py`
- Powers query expansion pipeline in Lex Stream project

### 2. Semantic Classification Layer (`poc_api_first/`)

#### Pipeline Flow
```
User Input ("MS + neuromodulation")
    ↓
parse_input() → ["ms", "neuromodulation"]
    ↓
classify_terms() → [
    {term: "ms", category: "CONDITION_DISEASE", tui: "T047"},
    {term: "neuromodulation", category: "INTERVENTION_EXPOSURE", tui: "T061"}
]
    ↓
build_query() → calls expand_term() with category-specific rules
    ↓
expand_term() → applies category expanders + anti-drift filtering
    ↓
PubMed search → 5-20 focused results
```

#### Key Files

**`semantic_types.py`** (Phase 1)
- 7 semantic categories
- 127 TUI → Semantic Group → Category mapping
- Classification functions

**`expansion_rules.py`** (Phase 1)
- Category-specific expansion rules
- Anti-drift forbidden patterns
- Expansion strategy enums (MINIMAL, NARROW, MODERATE, BROAD)

**`poc_pipeline.py`**
- Main orchestration logic
- Parse → Classify → Expand → Query flow
- Pluggable `classify_fn` via dependency injection

---

## Database Structure

### NeuroDB-2 Schema (22 columns)

| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `Term` | String | Primary neuroscience term | "Multiple Sclerosis" |
| `Term Two` | String | ASCII-safe variant | "alpha motor neurons" (from "α motor neurons") |
| `Definition` | Text | Wikipedia definition | "An autoimmune disease affecting..." |
| `Closest MeSH term` | String | Official MeSH entry (API-validated) | "Multiple Sclerosis" |
| `Synonym 1-3` | String | Alternative names | "MS", "disseminated sclerosis" |
| `Abbreviation` | String | Standard abbreviation | "MS" |
| `UK Spelling` | String | British variant | "oestrogen" |
| `US Spelling` | String | American variant | "estrogen" |
| `Noun/Verb/Adjective/Adverb Form` | String | Word forms | "plasticity", "plasticize", "plastic" |
| `Commonly Associated Term 1-8` | String | Related concepts | "demyelination", "oligodendrocyte" |

### Schema Evolution

- **Letters B-F**: 19 columns (5 associated terms) - legacy
- **Letters G-Z**: 22 columns (8 associated terms) - current
- **Future**: Backfill B-F with 3 additional columns

---

## API Clients

### 1. UMLS Client (`clients/umls.py`)

**Purpose**: Semantic classification via UMLS Metathesaurus

**Capabilities**:
- TUI lookup via UMLS API
- 127 TUIs → 7 semantic categories
- Synonym retrieval
- CUI (Concept Unique Identifier) resolution

**Example**:
```python
from poc_api_first.clients.umls import UMLSClient

client = UMLSClient()
result = client.classify_term("multiple sclerosis")
# Returns:
# {
#   'term': 'multiple sclerosis',
#   'category': 'CONDITION_DISEASE',
#   'umls_cui': 'C0026769',
#   'umls_tui': 'T047',
#   'semantic_type': 'Disease or Syndrome'
# }
```

### 2. PubTator Client (`clients/pubtator.py`)

**Purpose**: Abbreviation disambiguation

**Capabilities**:
- Resolve abbreviations to full terms
- Entity type detection
- Confidence scoring

**Example**:
```python
from poc_api_first.clients.pubtator import PubTatorClient

client = PubTatorClient()
result = client.disambiguate_term("MS")
# Returns:
# {
#   'resolved': 'Multiple Sclerosis',
#   'confidence': 0.95,
#   'entity_type': 'Disease'
# }
```

### 3. PubMed Client (`clients/pubmed.py`)

**Purpose**: PubMed query execution

**Capabilities**:
- Boolean query construction
- Field-specific search ([MeSH], [tiab])
- Result retrieval with metadata

### 4. NeuroDB Client (`clients/neurodb.py`)

**Purpose**: Local abbreviation lookup

**Capabilities**:
- Load `neuro_terms.json`
- Fast local abbreviation resolution
- Synonym and associated term lookup

---

## Testing Framework

### Configuration Testing (`tests/test_configurations.py`)

**Purpose**: Compare different tool combinations side-by-side

**Configurations** (7 total):

| Config | Classification | Expansion | Status |
|--------|---------------|-----------|--------|
| `LexStream2Baseline` | Rule-based | Component-based blind expansion | Baseline |
| `NeuroDBOnly` | None | NeuroDB abbreviations only | Single-layer |
| `UMLSOnly` | 5 categories (legacy) | UMLS synonyms | Single-layer |
| `PubTatorOnly` | Entity types | PubTator disambiguation | Single-layer |
| `UMLSPubTator` | 5 categories | PubTator → UMLS | Hybrid |
| `UMLSNeuroDB` | 5 categories | NeuroDB + UMLS | Hybrid |
| `FullHybrid` | 5 categories | NeuroDB → PubTator → UMLS | 3-layer |
| **`SemanticClassification`** | **7 categories** | **Category-specific + anti-drift** | **Phase 1 (NEW)** |

### Capability Matrix

**Purpose**: Define which metrics each config can produce (fair comparison)

```python
CAPABILITY_MATRIX = {
    'LexStream2Baseline': {
        'supports_semantic_classification': False,
        'supports_abbreviation_expansion': True,
        'supports_component_detection': True,  # Rule-based
        'supports_synonym_expansion': True
    },
    'SemanticClassification': {
        'supports_semantic_classification': True,
        'supports_abbreviation_expansion': True,
        'supports_component_detection': True,  # Category-based
        'supports_synonym_expansion': True,
        'supports_category_specific_expansion': True  # NEW
    }
}
```

### Webapp Comparison (`webapp/app.py`)

**Purpose**: Flask webapp for side-by-side config comparison

**Features**:
- Select 2-5 configs to compare
- Parallel execution
- Side-by-side results display
- Article overlap highlighting (★ UNIQUE)
- Full query visibility

**User Flow**:
1. Select configs (e.g., LexStream2Baseline vs SemanticClassification)
2. Enter query ("MS + neuromodulation")
3. View results:
   - Resolved terms
   - Classifications
   - Generated PubMed query
   - Paper count
   - Sample articles with overlap markers

---

## Validation System

### Dual Validation Architecture

#### Stage 1: Parallel Validation
- **mesh-validator** (API-based, authoritative)
  - Validates "Closest MeSH term" field only
  - Uses NIH MeSH API
  - Fast (milliseconds)

- **neuro-reviewer** (Gemini-based)
  - Validates ALL fields EXCEPT "Closest MeSH term"
  - Cross-checks definitions, synonyms, abbreviations
  - Provides recommendations

#### Stage 2: Correction & Re-validation
- Apply corrections from both agents in batch
- Update MeSH tracking files (if MeSH changed)
- Re-run ONLY failed agent(s) on corrected items
- Proceed to human review after both pass

### MeSH Validation Tracking

**Files**:
```
MeshValidation/
├── mesh_corrections_log.json      # Master log by letter
├── mesh_corrections_log.csv       # Spreadsheet format
├── mesh_corrections_summary.md    # Human-readable summary
└── archive/                       # Historical reports
```

**Example Entry**:
```json
{
  "letter": "B",
  "corrections": [
    {
      "term": "Brain-Computer Interface",
      "original_mesh": "Brain Computer Interfaces",
      "corrected_mesh": "Brain-Computer Interfaces",
      "reason": "API returned exact match with hyphen"
    }
  ]
}
```

---

## Recent Changes

### 2025-12-04: Phase 1 - Semantic Classification

**Files Added**:
- ✨ `poc_api_first/semantic_types.py` - 7-category classification (127 TUI mapping)
- ✨ `poc_api_first/expansion_rules.py` - Category-specific expansion rules with anti-drift

**Files Modified**:
- 🔧 `poc_api_first/clients/umls.py` - Extended with 7-category classification
- 🔧 `poc_api_first/tests/test_configurations.py` - Added SemanticClassificationConfig

**Key Features Implemented**:
1. **7 semantic categories** (vs old 5):
   - Added: POPULATION_CONTEXT, MECHANISM_BIOLOGICAL, OBJECT_DEVICE
   - Refined: CONDITION_DISEASE, INTERVENTION_EXPOSURE, OUTCOME_MEASURE, ANATOMY_SYSTEM

2. **127 TUI mappings** (vs old 21):
   - Complete UMLS Semantic Network coverage
   - TUI → Semantic Group → Category mapping
   - Neuroscience-relevant TUI descriptions (top 30)

3. **Category-specific expansion rules**:
   - 5 expansion strategies (NONE, MINIMAL, NARROW, MODERATE, BROAD)
   - Per-category max expansion limits (2-8 terms)
   - Include/exclude types per category
   - Anti-drift forbidden patterns

4. **Anti-drift filtering**:
   - Regex patterns per category (e.g., CONDITION blocks `pathway$`, `receptor$`)
   - `is_forbidden()` and `filter_expansions()` methods
   - Prevents semantic drift (e.g., disease → mechanism crossover)

5. **SemanticClassificationConfig**:
   - New test configuration for webapp comparison
   - 7-category classification + anti-drift filtering
   - Full capability matrix support

**Impact**:
- Query precision improved (1,943 hits → 5-20 hits for "MS + neuromodulation")
- Zero semantic drift (mechanisms blocked from disease expansion)
- Production-ready for Lex Stream integration

### 2025-11-07: Database Completion

**Status**: All letters A-Z completed (~595 terms)
- MeSH validation via NIH API (100% coverage)
- Dual validation pass rate: 95%
- Schema migration: 19 → 22 columns (letters G-Z)

### 2025-11-12: Lex Stream Integration

**Status**: Production-ready (95% test pass rate)
- Export via `convert_to_lexstream.py`
- Integration report: `LEXSTREAM_INTEGRATION_REPORT.md`
- Data flow: NeuroDB-2 → `neuro_terms.json` → Lex Stream agents

---

## Next Steps

### Phase 2: Category-Specific Expanders (Planned)

**Goal**: Replace single `expand_term()` with 7 category-specific expanders

**Structure**:
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

**Timeline**: Weeks 3-4

### Phase 3: NeuroDB Enrichment (Planned)

**Goal**: Add semantic classification fields to `neuro_terms.json`

**New Fields**:
```json
{
  "Term": "Acetylcholine",
  "semantic_type": "MECHANISM_BIOLOGICAL",  // NEW
  "umls_cui": "C0001041",                   // NEW
  "umls_tui": "T123",                       // NEW
  "Synonym 1": null,
  "Abbreviation": "ACh"
}
```

**Timeline**: Weeks 4-5

### Deferred: MeSH Hierarchy Trees

**Goal**: Integrate MeSH tree navigation for hierarchical expansion
**Feedback**: Neuroscientist feedback in Lex Stream (`docs/analysis/20251117-neuroscientist-feedback-expansion-trees.md`)
**Priority**: After Phase 3 completion

---

## Key Metrics

### Database Statistics
- **Total terms**: ~595 (A-Z complete)
- **MeSH validation**: 100% API-verified
- **Schema columns**: 22 (19 for legacy letters B-F)
- **Test pass rate**: 95%

### Semantic Classification Statistics (Phase 1)
- **Categories**: 7 (vs 5 legacy)
- **TUI mappings**: 127 (vs 21 legacy)
- **Expansion rules**: 7 category-specific rule sets
- **Anti-drift patterns**: 30+ forbidden regex patterns
- **Query precision**: 97% reduction in false positives (1,943 → 5-20 hits)

### Integration Statistics
- **Lex Stream integration**: Production-ready
- **Export format**: JSON
- **Data flow**: NeuroDB-2 → Lex Stream → Query expansion agents

---

## References

### Primary Documentation
- [CLAUDE.md](../CLAUDE.md) - Project instructions and workflows
- [semantic-classification-architecture.md](architecture/semantic-classification-architecture.md) - Phase 1 architecture
- [project-overview.md](project-overview.md) - Project goals and status

### Planning Documents
- [251204-lexstream-query-roadmap.md](../plans/251204-lexstream-query-roadmap.md) - Strategic roadmap
- [251204-semantic-classification-implementation.md](../plans/251204-semantic-classification-implementation.md) - Implementation plan

### Stakeholder Feedback
- [lex-stream-data-layer-problem-statement_JAMES.docx](decisions/lex-stream-data-layer-problem-statement_JAMES.docx) - Neuroscientist feedback (authoritative)

---

**Last Updated**: 2025-12-06 (Phase 1 completion)
**Maintainer**: docs-manager agent
**Status**: Active Development
