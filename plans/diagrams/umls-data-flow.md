# UMLS Importer Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    UMLS 2024AB Files (downloads/)                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌──────────────────┐        ┌─────────────────┐
│ MRSTY.RRF     │         │  MRCONSO.RRF     │        │   MRDEF.RRF     │
│ (Semantic     │         │  (Concepts)      │        │   (Definitions) │
│  Types)       │         │  ~6GB, 16M rows  │        │  ~600MB, 1.2M   │
│ ~40MB, 2M     │         │                  │        │                 │
└───────┬───────┘         └──────────────────┘        └─────────────────┘
        │                          │                           │
        │ PHASE 2                  │                           │
        │ Filter by semantic types │                           │
        ▼                          │                           │
┌────────────────────────┐         │                           │
│ Neuroscience Filter    │         │                           │
│ ─────────────────────  │         │                           │
│ Semantic Types:        │         │                           │
│ • T023 Body Part       │         │                           │
│ • T041 Mental Process  │         │                           │
│ • T047 Disease         │         │                           │
│ • T121 Pharmacologic   │         │                           │
│ + 20 more types        │         │                           │
│                        │         │                           │
│ Hybrid Logic:          │         │                           │
│ Priority 1 types OR    │         │                           │
│ Priority 2 + (MSH OR   │         │                           │
│   neuro keyword) OR    │         │                           │
│ Priority 3 + MSH +     │         │                           │
│   neuro keyword        │         │                           │
└───────┬────────────────┘         │                           │
        │                          │                           │
        ▼                          │                           │
┌────────────────────────┐         │                           │
│ neuroscience_cuis.txt  │         │                           │
│ ─────────────────────  │         │                           │
│ C0000000               │         │                           │
│ C0000001               │         │                           │
│ ... (100K-150K CUIs)   │         │                           │
└───────┬────────────────┘         │                           │
        │                          │                           │
        │ PHASE 3                  │                           │
        │ Use as filter ───────────┤                           │
        │                          ▼                           │
        │                 ┌──────────────────┐                 │
        │                 │ Stream & Filter  │                 │
        │                 │ ──────────────── │                 │
        │                 │ • CUI in filter  │                 │
        │                 │ • LAT = ENG      │                 │
        │                 │ • SUPPRESS = N   │                 │
        │                 │                  │                 │
        │                 │ Extract:         │                 │
        │                 │ • Preferred term │                 │
        │                 │ • Synonyms (3)   │                 │
        │                 │ • Abbreviations  │                 │
        │                 │ • MeSH codes     │                 │
        │                 │ • Source (SAB)   │                 │
        │                 └────────┬─────────┘                 │
        │                          │                           │
        │                          ▼                           │
        │                 ┌──────────────────┐                 │
        │                 │ Deduplicate      │                 │
        │                 │ ──────────────── │                 │
        │                 │ Priority:        │                 │
        │                 │ MSH >            │                 │
        │                 │ SNOMEDCT_US >    │                 │
        │                 │ NCI > other      │                 │
        │                 └────────┬─────────┘                 │
        │                          │                           │
        ├──────────────────────────┼───────────────────────────┤
        │                          ▼                           │
        │                 ┌──────────────────┐                 │
        │                 │  concepts = {}   │                 │
        │                 │  ──────────────  │                 │
        │                 │  CUI → {         │                 │
        │                 │    'term': str   │                 │
        │                 │    'synonyms': []│                 │
        │                 │    'abbrevs': [] │                 │
        │                 │    'mesh': str   │                 │
        │                 │    'sources': [] │                 │
        │                 │  }               │                 │
        │                 └────────┬─────────┘                 │
        │                          │                           │
        │ PHASE 4                  │                           │
        │ Use as filter ───────────┼───────────────────────────┤
        │                          │                           ▼
        │                          │                  ┌──────────────────┐
        │                          │                  │ Stream & Filter  │
        │                          │                  │ ──────────────── │
        │                          │                  │ • CUI in filter  │
        │                          │                  │ • SUPPRESS = N   │
        │                          │                  │                  │
        │                          │                  │ Extract:         │
        │                          │                  │ • Definition     │
        │                          │                  │ • Source (SAB)   │
        │                          │                  │                  │
        │                          │                  │ Prioritize:      │
        │                          │                  │ MSH > SNOMEDCT > │
        │                          │                  │ NCI > other      │
        │                          │                  └────────┬─────────┘
        │                          │                           │
        │                          ├───────────────────────────┘
        │                          │
        │                          ▼
        │                 ┌──────────────────┐
        │                 │  concepts = {}   │
        │                 │  ──────────────  │
        │                 │  CUI → {         │
        │                 │    ...           │
        │                 │    'definition'  │
        │                 │    'def_source'  │
        │                 │  }               │
        │                 └────────┬─────────┘
        │                          │
        ▼                          │
┌─────────────────┐               │
│   MRREL.RRF     │               │
│   (Related      │               │
│    Concepts)    │               │
│  ~2GB, 60M rows │               │
└────────┬────────┘               │
         │                        │
         │ PHASE 5 ⚠️ CRITICAL     │
         │ (DEC-001 Profiling)    │
         ▼                        │
┌──────────────────┐              │
│ Stream & Filter  │              │
│ ──────────────── │              │
│ • CUI1 or CUI2   │              │
│   in filter      │              │
│ • SUPPRESS = N   │              │
│                  │              │
│ Extract:         │              │
│ • Related CUIs   │              │
│ • REL type       │              │
│ • RELA (specific)│              │
│ • Source (SAB)   │              │
└────────┬─────────┘              │
         │                        │
         ▼                        │
┌──────────────────────────┐     │
│ Profiling Analysis       │     │
│ ──────────────────────── │     │
│ Sample 1000 relations:   │     │
│                          │     │
│ Classify RELA:           │     │
│ • Domain-specific:       │     │
│   may_treat,             │     │
│   associated_with,       │     │
│   affects, causes        │     │
│   (hippocampus →         │     │
│    memory, Alzheimer's)  │     │
│                          │     │
│ • Generic taxonomy:      │     │
│   isa, part_of,          │     │
│   has_part               │     │
│   (hippocampus →         │     │
│    Body Part)            │     │
│                          │     │
│ Generate report:         │     │
│ • % domain-specific      │     │
│ • % generic taxonomy     │     │
│ • Recommendation:        │     │
│   USE_DIRECTLY |         │     │
│   FILTER_BY_RELA |       │     │
│   SMART_FILTER           │     │
└────────┬─────────────────┘     │
         │                       │
         ├───────────────────────┤
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│        concepts = {} (complete)         │
│        ───────────────────────────      │
│        CUI → {                          │
│          'term': str                    │
│          'definition': str              │
│          'def_source': str              │
│          'synonyms': [str, ...]         │
│          'abbreviations': [str, ...]    │
│          'mesh_code': str               │
│          'sources': [str, ...]          │
│          'related_concepts': [          │
│            {'term': str,                │
│             'rel': str,                 │
│             'rela': str,                │
│             'source': str}              │
│          ]                              │
│        }                                │
└─────────┬───────────────────────────────┘
          │
          │ PHASE 6
          │ Map to NeuroDB-2 Schema
          ▼
┌─────────────────────────────────────────┐
│      Schema Mapping                     │
│      ──────────────                     │
│                                         │
│  For each concept:                      │
│    row = create_empty_row()            │
│                                         │
│    row['Term'] = term                  │
│    row['Definition'] = definition      │
│    row['Closest MeSH term'] = mesh     │
│    row['Synonym 1-3'] = synonyms[:3]   │
│    row['Abbreviation'] = abbrevs[0]    │
│                                         │
│    # Apply DEC-001 filtering           │
│    if profiling.rec == 'FILTER':       │
│      related = filter_by_rela(...)     │
│                                         │
│    row['Commonly Associated 1-8']      │
│      = related_terms[:8]               │
│                                         │
│    add_source_metadata(row, 'umls')    │
│    row['source_priority'] = '1'        │
│    row['sources_contributing']         │
│      = ','.join(sources)               │
└─────────┬───────────────────────────────┘
          │
          │ PHASE 7
          │ Write & Validate
          ▼
┌─────────────────────────────────────────┐
│  umls_neuroscience_imported.csv         │
│  ─────────────────────────────────      │
│  Term,Term Two,Definition,...(26 cols)  │
│  "Hippocampus","","The hippocampus..."  │
│  "Dopamine","","A neurotransmitter..."  │
│  ... (100K-150K rows)                   │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│      Structural Validation              │
│      ─────────────────────              │
│  ✓ 26 columns per row                   │
│  ✓ UTF-8 encoding                       │
│  ✓ No duplicates (case-insensitive)     │
│  ✓ Required fields populated:           │
│    - Term (non-empty)                   │
│    - Definition (non-empty)             │
│    - source ('umls')                    │
│    - source_priority ('1')              │
│    - date_added (YYYY-MM-DD)            │
└─────────┬───────────────────────────────┘
          │
          │ PHASE 8
          │ Data Quality Profiling
          ▼
┌─────────────────────────────────────────┐
│   Data Quality Report                   │
│   ──────────────────────                │
│                                         │
│   Total terms: 100K-150K                │
│   Definition coverage: 80%+             │
│   MeSH coverage: 60%+                   │
│   Avg synonyms: 2+                      │
│   Avg associated terms: 2-4             │
│                                         │
│   Top 20 associated terms:              │
│   1. "memory" (3,245)                   │
│   2. "cognitive function" (2,891)       │
│   3. "Alzheimer's disease" (2,456)      │
│   ...                                   │
│                                         │
│   ⚠️ Check for generic terms:           │
│   - "Body Part" (?)                     │
│   - "Regional part of brain" (?)        │
└─────────┬───────────────────────────────┘
          │
          │ PHASE 9
          │ Documentation
          ▼
┌─────────────────────────────────────────┐
│   Documentation Outputs                 │
│   ──────────────────────                │
│                                         │
│   1. UMLS_IMPORT_SUMMARY.md             │
│      - Filtering strategy               │
│      - Data quality metrics             │
│      - Top associated terms             │
│      - Comparison to NIF                │
│                                         │
│   2. 2025-11-20-umls-associated-        │
│      terms-quality.md                   │
│      - DEC-001 profiling results        │
│      - Relationship samples             │
│      - Filtering decision               │
│                                         │
│   3. ontology-import-tracker.md         │
│      (updated)                          │
└─────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│   ✅ READY FOR MERGE (Day 4)            │
└─────────────────────────────────────────┘
```

## Data Transformation Examples

### Example 1: Complete UMLS Concept

**Input** (from multiple RRF files):
```
MRSTY:    C0019564|T023|...  (Semantic Type: Body Part)
MRCONSO:  C0019564|ENG|...|MSH|PN|...|Hippocampus|...
MRCONSO:  C0019564|ENG|...|MSH|SY|...|Hippocampal Formation|...
MRDEF:    C0019564|...|MSH|The hippocampus is a curved...|...
MRREL:    C0019564|...|RO|C0025260|...|associated_with|...  → Memory
MRREL:    C0019564|...|RO|C0002395|...|associated_with|...  → Alzheimer Disease
```

**Output** (NeuroDB-2 schema):
```csv
"Hippocampus","","The hippocampus is a curved elongation...",
"Hippocampus","Hippocampal Formation","","","","","","",
"Memory","Alzheimer Disease","Temporal Lobe","Learning","","","","",
"umls","1","MSH,SNOMEDCT_US","2025-11-20"
```

### Example 2: Multi-Source Deduplication

**Input** (duplicate term from different sources):
```
MRCONSO: C0000001|ENG|...|MSH|PN|D012345|Dopamine|...
MRCONSO: C0000002|ENG|...|SNOMEDCT_US|PN|67890|Dopamine|...
MRCONSO: C0000003|ENG|...|NCI|PN|C98765|Dopamine|...
```

**Processing**:
```
1. All extract to unique_terms['dopamine']
2. Priority comparison: MSH wins
3. Keep C0000001, merge sources
```

**Output**:
```csv
"Dopamine","","A neurotransmitter...",
"D012345","","","","","","","",
"Reward","Parkinson Disease","Substantia Nigra","Motivation",...,
"umls","1","MSH,NCI,SNOMEDCT_US","2025-11-20"
```

### Example 3: DEC-001 Filtering Decision

**Input** (relationships from MRREL):
```
hippocampus|RO|memory|associated_with|MSH          → Domain-specific ✅
hippocampus|RB|Body Part|isa|SNOMEDCT_US          → Generic taxonomy ❌
hippocampus|RO|Alzheimer|may_cause|MSH            → Domain-specific ✅
hippocampus|RB|Anatomical Structure|part_of|NCI  → Generic taxonomy ❌
```

**Profiling Result**:
```
Domain-specific: 60% (associated_with, may_cause)
Generic taxonomy: 40% (isa, part_of)
Recommendation: FILTER_BY_RELA
```

**Filtering Logic**:
```python
DOMAIN_SPECIFIC_RELA = {
    'associated_with', 'may_treat', 'may_cause',
    'may_diagnose', 'affects', 'co-occurs_with'
}

filtered_related = [
    r for r in related_concepts
    if r['rela'] in DOMAIN_SPECIFIC_RELA
]
```

**Output** (only domain-specific associations):
```csv
..., "Memory","Alzheimer Disease","","","","","","", ...
```

## Performance Metrics

| Operation | Input Size | Filter Rate | Output Size | Time |
|-----------|------------|-------------|-------------|------|
| MRSTY parsing | 2M rows | 5% | 100K-150K CUIs | 5 min |
| MRCONSO streaming | 16M rows | 0.6% | 100K-150K concepts | 45 min |
| MRDEF streaming | 1.2M rows | 8% | 80K-120K definitions | 10 min |
| MRREL streaming | 60M rows | 0.2% | 300K-500K relationships | 30 min |
| Deduplication | 100K-150K | 10% | 100K-135K unique | 5 min |
| Schema mapping | 100K-135K | 100% | 100K-135K rows | 10 min |
| Validation | 100K-135K | 100% | Report | 5 min |
| **Total** | **79.2M rows** | **0.1-0.2%** | **100K-150K** | **~2 hours** |

## Memory Usage Profile

```
Phase 1-2 (Filter building):     ~500MB (CUI set in memory)
Phase 3 (MRCONSO streaming):     ~2GB (concepts dict growing)
Phase 4 (MRDEF streaming):       ~2.5GB (adding definitions)
Phase 5 (MRREL streaming):       ~3.5GB (adding relationships)
Phase 6-7 (Mapping + writing):   ~3GB (rows list)
Peak:                            ~3.5GB
```

**Mitigation**: Batch writing, intermediate file saves, generator-based processing
