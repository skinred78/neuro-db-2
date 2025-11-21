---
title: Scalable Ontology Ingestion with Selective Source Control
date: 2025-11-19
type: implementation-plan
priority: critical
deadline: 2025-11-25
status: ready-for-implementation
related_docs:
  - docs/analysis/2025-11-19-ontology-ingestion-optimization-analysis.md
  - docs/analysis/2025-11-19-lex-stream-integration-compatibility-report.md
---

## Executive Summary

**Goal**: Scale NeuroDB-2 from 595 to 100K+ terms using automated bulk import from 4 ontologies, add source tagging for quality optimization, enable runtime filtering in Lex Stream.

**Timeline**: Nov 20-25 (6 days)

**Approach**: Prioritize UMLS + Neuronames first (80% value, 20% effort), add source control system, validate against James's benchmarks, deploy via automated GitHub Actions pipeline.

**Key Constraint**: Maintain 22-column CSV → JSON schema (Lex Stream compatibility).

**Success Metrics**:

- Database size: 595 → 100K+ terms
- Lex Stream deployment: automated (zero downtime)
- Quality: 90%+ pass rate on tiered validation
- Benchmark performance: measurable improvement vs baseline

---

## Architecture Overview

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ONTOLOGY SOURCES                          │
├─────────────────────────────────────────────────────────────┤
│ UMLS          Neuronames       NIF/NIFSTD      Gene Ontology│
│ (RRF)         (JSON)           (OWL/TTL)       (OBO)        │
│ 4M+ terms     3K structures    ~30K terms      40K terms    │
└────┬──────────────┬────────────────┬───────────────┬────────┘
     │              │                │               │
     ▼              ▼                ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                  BULK IMPORT PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│  Importer 1     Importer 2      Importer 3     Importer 4   │
│  umls_import    neuronames_     nif_import     go_import    │
│  .py            import.py       .py            .py           │
│                                                              │
│  ▸ Parse native format (RRF/JSON/OWL/OBO)                   │
│  ▸ Map to 22-column schema                                  │
│  ▸ Tag with source metadata (umls/neuronames/nif/go)        │
│  ▸ Export to [A-Z]_SOURCE.csv files                         │
└────┬──────────────┬────────────────┬───────────────┬────────┘
     │              │                │               │
     └──────────────┴────────────────┴───────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  SOURCE MERGING & CONFLICT RESOLUTION        │
├─────────────────────────────────────────────────────────────┤
│  merge_sources.py                                            │
│                                                              │
│  ▸ Priority ranking: UMLS (1) > Neuronames (2) > Wiki (3)   │
│  ▸ Merge overlapping terms intelligently                    │
│  ▸ Deduplicate synonyms across sources                      │
│  ▸ Track all contributing sources per term                  │
│  ▸ Output: neuro_terms.csv (consolidated, source-tagged)    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  TIERED VALIDATION                           │
├─────────────────────────────────────────────────────────────┤
│  Tier 1: Structural (100% coverage)                          │
│    ▸ Column count, required fields, encoding                │
│                                                              │
│  Tier 2: Sample-based (10% random sample)                   │
│    ▸ mesh-validator on random 10K terms                     │
│                                                              │
│  Tier 3: High-value (benchmark terms)                       │
│    ▸ Full dual validation (mesh-validator + neuro-reviewer) │
│    ▸ James's benchmark: neuromodulation, MS, Alzheimer's    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  CONVERSION & EXPORT                         │
├─────────────────────────────────────────────────────────────┤
│  convert_to_lexstream.py (MODIFIED)                          │
│                                                              │
│  ▸ Add source metadata to JSON output                       │
│  ▸ Generate neuro_terms_v{version}_{sources}.json           │
│  ▸ Maintain backward compatibility                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  LEX STREAM INTEGRATION                      │
├─────────────────────────────────────────────────────────────┤
│  terms_loader.py (MODIFIED)                                  │
│  config.py (NEW SETTINGS)                                    │
│                                                              │
│  ▸ Source filtering configuration (env vars)                │
│  ▸ Runtime term filtering based on enabled sources          │
│  ▸ Rebuild abbreviations/mesh_terms maps dynamically        │
│  ▸ Backward compatible (default = all sources enabled)      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  TESTING & BENCHMARKING                      │
├─────────────────────────────────────────────────────────────┤
│  test_source_combinations.py (NEW)                           │
│                                                              │
│  Test configurations:                                        │
│    ▸ Baseline (Wikipedia/NINDS only - 595 terms)            │
│    ▸ UMLS-only (~100K terms)                                │
│    ▸ UMLS + Neuronames (~103K terms)                        │
│    ▸ All sources (100K+ terms)                              │
│                                                              │
│  Benchmark queries:                                          │
│    ▸ Neuromodulation for MS                                 │
│    ▸ Alzheimer's disease treatment                          │
│    ▸ Stroke rehabilitation                                  │
│                                                              │
│  Metrics:                                                    │
│    ▸ Synonyms added, query complexity, quality score        │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Core Infrastructure (Nov 20, 4 hours)

### 1.1 Source Tagging Schema

**File**: `schemas/source_metadata.py` (NEW)

```python
"""
Source metadata schema for tracking ontology provenance.
"""

SOURCE_PRIORITY = {
    'umls': 1,          # Highest priority (authoritative medical ontology)
    'neuronames': 2,    # Neuroanatomy specialist
    'wikipedia': 3,     # Current baseline
    'ninds': 3,         # Current baseline (same priority as Wikipedia)
    'nif': 4,           # Comprehensive but less structured
    'go': 5,            # Gene-focused (lower priority for clinical terms)
}

SOURCE_NAMES = {
    'umls': 'UMLS Metathesaurus 2024AB',
    'neuronames': 'Neuronames Brain Hierarchy',
    'wikipedia': 'Wikipedia Glossary of Neuroscience',
    'ninds': 'NINDS Glossary',
    'nif': 'Neuroscience Information Framework (NIFSTD)',
    'go': 'Gene Ontology (goslim_synapse)',
}

def get_source_tag(source_abbrev):
    """Get source metadata for a given abbreviation."""
    return {
        'source': source_abbrev,
        'source_name': SOURCE_NAMES.get(source_abbrev, 'Unknown'),
        'priority': SOURCE_PRIORITY.get(source_abbrev, 99)
    }
```

### 1.2 Extended CSV Schema (22 columns + source metadata)

**Approach**: Add source metadata as ADDITIONAL columns (beyond 22-column schema).

**Rationale**: Maintains Lex Stream compatibility while enabling source tracking.

**New columns** (appended after column 22):

- `Source` - Primary source identifier (umls/neuronames/nif/go/wikipedia/ninds)
- `Source Priority` - Integer ranking (1=highest)
- `Contributing Sources` - Comma-separated list of all sources that provided data for this term
- `Date Added` - ISO timestamp

**File format example**:

```csv
Term,Term Two,Definition,...,Commonly Associated Term 8,Source,Source Priority,Contributing Sources,Date Added
Parkinson disease,,A chronic progressive...,treatment,umls,1,"umls,wikipedia",2025-11-20T10:30:00Z
```

### 1.3 Merge Strategy

**File**: `scripts/merge_sources.py` (NEW)

**Algorithm**:

1. Group terms by lowercase key (case-insensitive matching)
2. For overlapping terms:

   - Use HIGHEST priority source for `Definition` field
   - Merge ALL `Synonyms` from all sources (deduplicate)
   - Use HIGHEST priority source for `MeSH term`
   - Combine `Associated Terms` (deduplicate, limit to 8 best)
   - Track all contributing sources
3. For unique terms: preserve as-is with single source tag

**Conflict resolution**:

- Definition conflicts → Use highest priority source
- MeSH conflicts → Use highest priority source (UMLS > others)
- Synonym conflicts → Merge all, deduplicate exact matches
- Empty fields → Fill from lower priority sources if available

---

## Phase 2: UMLS + Neuronames Import (Nov 20-21, 16 hours)

**Priority**: These two sources provide 80% of value.

### 2.1 UMLS Metathesaurus Importer

**File**: `importers/umls_import.py` (NEW)

**Input**: UMLS 2024AB RRF files (downloaded separately)

**UMLS Files Required**:

- `MRCONSO.RRF` - Concept names and sources (~15M rows)
- `MRDEF.RRF` - Definitions
- `MRREL.RRF` - Relationships (for associated terms)
- `MRSTY.RRF` - Semantic types (for neuroscience filtering)

**Neuroscience Filtering Strategy**:

Option A: **MeSH Tree Code Filtering** (Conservative)

```python
# MeSH tree codes for neuroscience
NEURO_MESH_TREES = [
    'C10',      # Nervous System Diseases
    'C23.888',  # Signs and Symptoms, Nervous System
    'F01',      # Behavior and Behavior Mechanisms
    'F02',      # Psychological Phenomena
    'F03',      # Mental Disorders
    'G11',      # Nervous System Physiological Phenomena
]
```

Expected output: ~50K-100K terms

Option B: **Semantic Type Filtering** (Aggressive)

```python
# UMLS semantic types for neuroscience
NEURO_SEMANTIC_TYPES = [
    'T047',  # Disease or Syndrome
    'T048',  # Mental or Behavioral Dysfunction
    'T184',  # Sign or Symptom
    'T023',  # Body Part, Organ, or Organ Component (nervous system)
    'T061',  # Therapeutic or Preventive Procedure
    # ... more
]
```

Expected output: ~200K-500K terms

**Recommendation**: Start with Option A (conservative), expand to Option B if coverage insufficient.

**Implementation**:

```python
#!/usr/bin/env python3
"""
UMLS Metathesaurus to NeuroDB-2 bulk importer.
Filters for neuroscience terms using MeSH tree codes.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from schemas.source_metadata import get_source_tag

# Configuration
UMLS_DIR = Path('/path/to/UMLS/2024AB/META')
OUTPUT_DIR = Path('/Users/sam/NeuroDB-2/LetterFiles')
SOURCE_TAG = 'umls'

# MeSH tree code prefixes for neuroscience
NEURO_MESH_PREFIXES = ['C10', 'C23.888', 'F01', 'F02', 'F03', 'G11']

def parse_mrconso():
    """Parse MRCONSO.RRF for concept names."""
    cols = ['CUI', 'LAT', 'TS', 'LUI', 'STT', 'SUI', 'ISPREF', 'AUI',
            'SAUI', 'SCUI', 'SDUI', 'SAB', 'TTY', 'CODE', 'STR',
            'SRL', 'SUPPRESS', 'CVF']

    print("Parsing MRCONSO.RRF (this may take 5-10 minutes)...")
    df = pd.read_csv(
        UMLS_DIR / 'MRCONSO.RRF',
        sep='|',
        header=None,
        names=cols,
        encoding='utf-8',
        dtype=str,
        on_bad_lines='skip'
    )

    # Filter for English, non-obsolete terms
    df = df[
        (df['LAT'] == 'ENG') &
        (df['SUPPRESS'].isna() | (df['SUPPRESS'] != 'O'))
    ].copy()

    print(f"  Loaded {len(df):,} English concepts")
    return df

def filter_neuroscience_terms(concepts_df):
    """Filter for neuroscience-relevant terms using MeSH tree codes."""
    # TODO: Parse MRSTY.RRF for semantic types
    # TODO: Join with MeSH tree codes
    # For now, use source-based filtering

    neuro_df = concepts_df[
        concepts_df['SAB'].isin(['MSH', 'SNOMEDCT_US', 'NCI', 'NDFRT'])
    ].copy()

    print(f"  Filtered to {len(neuro_df):,} neuroscience terms")
    return neuro_df

def parse_mrdef():
    """Parse MRDEF.RRF for definitions."""
    cols = ['CUI', 'AUI', 'ATUI', 'SATUI', 'SAB', 'DEF', 'SUPPRESS', 'CVF']

    print("Parsing MRDEF.RRF...")
    df = pd.read_csv(
        UMLS_DIR / 'MRDEF.RRF',
        sep='|',
        header=None,
        names=cols,
        encoding='utf-8',
        dtype=str,
        on_bad_lines='skip'
    )

    # Prefer MSH definitions, fall back to others
    priority_sources = ['MSH', 'NCI', 'SNOMEDCT_US']
    for source in priority_sources:
        source_defs = df[df['SAB'] == source].groupby('CUI').first()['DEF']
        if len(source_defs) > 0:
            return source_defs.to_dict()

    return df.groupby('CUI').first()['DEF'].to_dict()

def extract_synonyms_for_cui(cui, concepts_df, max_syns=3):
    """Extract unique synonyms for a CUI."""
    syns = concepts_df[concepts_df['CUI'] == cui]['STR'].unique().tolist()
    return syns[:max_syns]

def get_mesh_term_for_cui(cui, concepts_df):
    """Get MeSH term for a CUI."""
    mesh_rows = concepts_df[
        (concepts_df['CUI'] == cui) &
        (concepts_df['SAB'] == 'MSH')
    ]
    if not mesh_rows.empty:
        return mesh_rows.iloc[0]['STR']
    return ''

def map_to_neurodb_schema(concepts_df, definitions_dict):
    """Map UMLS data to NeuroDB-2 22+4 column schema."""

    preferred = concepts_df[concepts_df['ISPREF'] == 'Y'].groupby('CUI').first()

    records = []
    timestamp = datetime.utcnow().isoformat() + 'Z'
    source_meta = get_source_tag(SOURCE_TAG)

    for cui in preferred.index:
        term_row = preferred.loc[cui]
        primary_term = term_row['STR']
        synonyms = extract_synonyms_for_cui(cui, concepts_df)

        # Remove primary term from synonyms
        if primary_term in synonyms:
            synonyms.remove(primary_term)

        record = {
            # 22-column schema (Lex Stream compatible)
            'Term': primary_term,
            'Term Two': '',
            'Definition': definitions_dict.get(cui, ''),
            'Closest MeSH term': get_mesh_term_for_cui(cui, concepts_df),
            'Synonym 1': synonyms[0] if len(synonyms) > 0 else '',
            'Synonym 2': synonyms[1] if len(synonyms) > 1 else '',
            'Synonym 3': synonyms[2] if len(synonyms) > 2 else '',
            'Abbreviation': '',  # Could extract from TTY='AB' rows
            'UK Spelling': '',
            'US Spelling': '',
            'Noun Form of Word': '',
            'Verb Form of Word': '',
            'Adjective Form of Word': '',
            'Adverb Form of Word': '',
            'Commonly Associated Term 1': '',
            'Commonly Associated Term 2': '',
            'Commonly Associated Term 3': '',
            'Commonly Associated Term 4': '',
            'Commonly Associated Term 5': '',
            'Commonly Associated Term 6': '',
            'Commonly Associated Term 7': '',
            'Commonly Associated Term 8': '',

            # Source metadata (additional 4 columns)
            'Source': SOURCE_TAG,
            'Source Priority': source_meta['priority'],
            'Contributing Sources': SOURCE_TAG,
            'Date Added': timestamp,
        }

        records.append(record)

    return pd.DataFrame(records)

def export_by_letter(df, output_dir):
    """Export to letter-based CSV files."""
    grouped = df.groupby(df['Term'].str[0].str.upper())

    for letter, group in grouped:
        filepath = output_dir / f'{letter}_UMLS.csv'
        group.to_csv(filepath, index=False, encoding='utf-8')
        print(f"  ✓ {letter}: {len(group):,} terms → {filepath.name}")

def main():
    print("=" * 60)
    print("UMLS Metathesaurus Bulk Import")
    print("=" * 60)

    # Step 1: Parse concepts
    concepts_df = parse_mrconso()

    # Step 2: Filter for neuroscience
    neuro_df = filter_neuroscience_terms(concepts_df)

    # Step 3: Parse definitions
    definitions_dict = parse_mrdef()

    # Step 4: Map to NeuroDB schema
    print("Mapping to NeuroDB-2 schema...")
    neurodb_df = map_to_neurodb_schema(neuro_df, definitions_dict)
    print(f"  Mapped {len(neurodb_df):,} terms")

    # Step 5: Export by letter
    print("Exporting to letter files...")
    export_by_letter(neurodb_df, OUTPUT_DIR)

    print("\n✓ UMLS import complete!")
    print(f"Total terms imported: {len(neurodb_df):,}")

if __name__ == '__main__':
    main()
```

**Estimated runtime**: 2-4 hours (parsing 15M rows, filtering, exporting)

### 2.2 Neuronames Importer

**File**: `importers/neuronames_import.py` (NEW)

**Input**: Neuronames JSON export (download from http://braininfo.rprc.washington.edu/)

**Implementation**:

```python
#!/usr/bin/env python3
"""
Neuronames neuroanatomy ontology to NeuroDB-2 bulk importer.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from schemas.source_metadata import get_source_tag

# Configuration
NEURONAMES_JSON = Path('/path/to/neuronames_export.json')
OUTPUT_DIR = Path('/Users/sam/NeuroDB-2/LetterFiles')
SOURCE_TAG = 'neuronames'

def parse_neuronames_json(json_path):
    """Parse Neuronames JSON export."""

    print("Loading Neuronames JSON...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"  Loaded {len(data):,} neuroanatomical structures")

    records = []
    timestamp = datetime.utcnow().isoformat() + 'Z'
    source_meta = get_source_tag(SOURCE_TAG)

    for item in data:
        # Neuronames structure (varies by export format)
        primary_term = item.get('standard_term') or item.get('name', '')
        if not primary_term:
            continue

        # Extract synonyms (multiple languages)
        synonyms = []
        for lang_field in ['english_synonym', 'latin_synonym', 'abbreviation']:
            syn = item.get(lang_field, '')
            if syn and syn != primary_term:
                synonyms.append(syn)

        record = {
            # 22-column schema
            'Term': primary_term,
            'Term Two': '',
            'Definition': item.get('definition', ''),
            'Closest MeSH term': item.get('mesh_term', ''),
            'Synonym 1': synonyms[0] if len(synonyms) > 0 else '',
            'Synonym 2': synonyms[1] if len(synonyms) > 1 else '',
            'Synonym 3': synonyms[2] if len(synonyms) > 2 else '',
            'Abbreviation': item.get('abbreviation', ''),
            'UK Spelling': '',
            'US Spelling': '',
            'Noun Form of Word': '',
            'Verb Form of Word': '',
            'Adjective Form of Word': '',
            'Adverb Form of Word': '',
            'Commonly Associated Term 1': '',
            'Commonly Associated Term 2': '',
            'Commonly Associated Term 3': '',
            'Commonly Associated Term 4': '',
            'Commonly Associated Term 5': '',
            'Commonly Associated Term 6': '',
            'Commonly Associated Term 7': '',
            'Commonly Associated Term 8': '',

            # Source metadata
            'Source': SOURCE_TAG,
            'Source Priority': source_meta['priority'],
            'Contributing Sources': SOURCE_TAG,
            'Date Added': timestamp,
        }

        records.append(record)

    return pd.DataFrame(records)

def export_by_letter(df, output_dir):
    """Export to letter-based CSV files."""
    grouped = df.groupby(df['Term'].str[0].str.upper())

    for letter, group in grouped:
        filepath = output_dir / f'{letter}_NEURONAMES.csv'
        group.to_csv(filepath, index=False, encoding='utf-8')
        print(f"  ✓ {letter}: {len(group):,} terms → {filepath.name}")

def main():
    print("=" * 60)
    print("Neuronames Neuroanatomy Import")
    print("=" * 60)

    df = parse_neuronames_json(NEURONAMES_JSON)
    print(f"\nProcessed {len(df):,} terms")

    print("\nExporting to letter files...")
    export_by_letter(df, OUTPUT_DIR)

    print("\n✓ Neuronames import complete!")

if __name__ == '__main__':
    main()
```

**Estimated runtime**: 5-10 minutes (small JSON file)

---

## Phase 3: NIF + GO Import (Nov 22, 8 hours)

### 3.1 NIF/NIFSTD Importer

**File**: `importers/nif_import.py` (NEW)

**Input**: NIFSTD OWL file (download from NCBO BioPortal)

**Dependencies**: `pip install rdflib owlready2`

**Implementation sketch**:

```python
#!/usr/bin/env python3
"""
NIF/NIFSTD ontology to NeuroDB-2 bulk importer.
Uses rdflib to parse OWL/TTL format.
"""

from rdflib import Graph, Namespace, RDF, RDFS
import pandas as pd
from pathlib import Path
from datetime import datetime
from schemas.source_metadata import get_source_tag

# Configuration
NIF_OWL = Path('/path/to/NIFSTD.owl')
OUTPUT_DIR = Path('/Users/sam/NeuroDB-2/LetterFiles')
SOURCE_TAG = 'nif'

# OWL namespaces
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
OBO = Namespace("http://purl.obolibrary.org/obo/")

def parse_nif_owl(owl_path):
    """Parse NIF OWL file using rdflib."""

    print("Loading NIF OWL ontology (this may take 5-10 minutes)...")
    g = Graph()
    g.parse(owl_path, format='xml')

    print(f"  Loaded {len(g):,} RDF triples")

    records = []
    timestamp = datetime.utcnow().isoformat() + 'Z'
    source_meta = get_source_tag(SOURCE_TAG)

    # Query for OWL classes (terms)
    for subject in g.subjects(RDF.type, None):
        if not str(subject).startswith('http://'):
            continue

        # Get label (preferred term)
        labels = list(g.objects(subject, RDFS.label))
        if not labels:
            continue
        primary_term = str(labels[0])

        # Get definition
        definitions = list(g.objects(subject, SKOS.definition))
        definition = str(definitions[0]) if definitions else ''

        # Get synonyms
        synonyms = [str(s) for s in g.objects(subject, SKOS.altLabel)][:3]

        record = {
            'Term': primary_term,
            'Term Two': '',
            'Definition': definition,
            'Closest MeSH term': '',  # May need mesh-validator
            'Synonym 1': synonyms[0] if len(synonyms) > 0 else '',
            'Synonym 2': synonyms[1] if len(synonyms) > 1 else '',
            'Synonym 3': synonyms[2] if len(synonyms) > 2 else '',
            'Abbreviation': '',
            'UK Spelling': '',
            'US Spelling': '',
            'Noun Form of Word': '',
            'Verb Form of Word': '',
            'Adjective Form of Word': '',
            'Adverb Form of Word': '',
            'Commonly Associated Term 1': '',
            'Commonly Associated Term 2': '',
            'Commonly Associated Term 3': '',
            'Commonly Associated Term 4': '',
            'Commonly Associated Term 5': '',
            'Commonly Associated Term 6': '',
            'Commonly Associated Term 7': '',
            'Commonly Associated Term 8': '',
            'Source': SOURCE_TAG,
            'Source Priority': source_meta['priority'],
            'Contributing Sources': SOURCE_TAG,
            'Date Added': timestamp,
        }

        records.append(record)

    return pd.DataFrame(records)

def main():
    print("=" * 60)
    print("NIF/NIFSTD Ontology Import")
    print("=" * 60)

    df = parse_nif_owl(NIF_OWL)
    print(f"\nProcessed {len(df):,} terms")

    # Export logic same as above

    print("\n✓ NIF import complete!")

if __name__ == '__main__':
    main()
```

**Estimated runtime**: 1-2 hours

### 3.2 Gene Ontology Importer

**File**: `importers/go_import.py` (NEW)

**Input**: goslim_synapse.obo (download from geneontology.org)

**Dependencies**: `pip install obonet networkx`

**Implementation sketch**:

```python
#!/usr/bin/env python3
"""
Gene Ontology (goslim_synapse) to NeuroDB-2 bulk importer.
Uses obonet library to parse OBO format.
"""

import obonet
import pandas as pd
from pathlib import Path
from datetime import datetime
from schemas.source_metadata import get_source_tag

# Configuration
GO_OBO = Path('/path/to/goslim_synapse.obo')
OUTPUT_DIR = Path('/Users/sam/NeuroDB-2/LetterFiles')
SOURCE_TAG = 'go'

def parse_go_obo(obo_path):
    """Parse GO OBO file using obonet."""

    print("Loading GO OBO file...")
    graph = obonet.read_obo(obo_path)

    print(f"  Loaded {len(graph.nodes):,} GO terms")

    records = []
    timestamp = datetime.utcnow().isoformat() + 'Z'
    source_meta = get_source_tag(SOURCE_TAG)

    for node_id, data in graph.nodes(data=True):
        if not node_id.startswith('GO:'):
            continue

        primary_term = data.get('name', '')
        if not primary_term:
            continue

        # Parse definition (format: "text" [citations])
        def_raw = data.get('def', '')
        definition = def_raw.split('"')[1] if '"' in def_raw else ''

        # Parse synonyms
        synonyms = []
        for syn_data in data.get('synonym', []):
            # Format: "synonym text" EXACT []
            syn_text = syn_data.split('"')[1] if '"' in syn_data else ''
            if syn_text and syn_text != primary_term:
                synonyms.append(syn_text)

        record = {
            'Term': primary_term,
            'Term Two': '',
            'Definition': definition,
            'Closest MeSH term': '',
            'Synonym 1': synonyms[0] if len(synonyms) > 0 else '',
            'Synonym 2': synonyms[1] if len(synonyms) > 1 else '',
            'Synonym 3': synonyms[2] if len(synonyms) > 2 else '',
            'Abbreviation': '',
            'UK Spelling': '',
            'US Spelling': '',
            'Noun Form of Word': '',
            'Verb Form of Word': '',
            'Adjective Form of Word': '',
            'Adverb Form of Word': '',
            'Commonly Associated Term 1': '',
            'Commonly Associated Term 2': '',
            'Commonly Associated Term 3': '',
            'Commonly Associated Term 4': '',
            'Commonly Associated Term 5': '',
            'Commonly Associated Term 6': '',
            'Commonly Associated Term 7': '',
            'Commonly Associated Term 8': '',
            'Source': SOURCE_TAG,
            'Source Priority': source_meta['priority'],
            'Contributing Sources': SOURCE_TAG,
            'Date Added': timestamp,
        }

        records.append(record)

    return pd.DataFrame(records)

def main():
    print("=" * 60)
    print("Gene Ontology (goslim_synapse) Import")
    print("=" * 60)

    df = parse_go_obo(GO_OBO)
    print(f"\nProcessed {len(df):,} terms")

    # Export logic same as above

    print("\n✓ GO import complete!")

if __name__ == '__main__':
    main()
```

**Estimated runtime**: 15-30 minutes

---

## Phase 4: Source Merging & Conflict Resolution (Nov 22, 4 hours)

### 4.1 Merge Algorithm

**File**: `scripts/merge_sources.py` (NEW)

**Input**: All `[A-Z]_SOURCE.csv` files from `LetterFiles/`

**Output**: Consolidated `neuro_terms.csv` with merged data

**Algorithm**:

```python
#!/usr/bin/env python3
"""
Merge multiple ontology source CSV files into single consolidated database.
Handles overlapping terms with intelligent conflict resolution.
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict
from schemas.source_metadata import SOURCE_PRIORITY

# Configuration
INPUT_DIR = Path('/Users/sam/NeuroDB-2/LetterFiles')
OUTPUT_CSV = Path('/Users/sam/NeuroDB-2/neuro_terms.csv')

def load_all_source_files():
    """Load all letter files from all sources."""

    all_dfs = []

    # Pattern: A_UMLS.csv, A_NEURONAMES.csv, A.csv (Wikipedia/NINDS)
    for csv_file in sorted(INPUT_DIR.glob('*.csv')):
        print(f"Loading {csv_file.name}...")
        df = pd.read_csv(csv_file, encoding='utf-8', dtype=str)
        all_dfs.append(df)

    combined = pd.concat(all_dfs, ignore_index=True)
    print(f"\nTotal rows loaded: {len(combined):,}")

    return combined

def merge_terms_by_key(df):
    """Merge terms with same lowercase key."""

    # Add lowercase key for grouping
    df['_key'] = df['Term'].str.lower().str.strip()

    merged_records = []

    for key, group in df.groupby('_key'):
        if len(group) == 1:
            # No conflict - single source
            merged_records.append(group.iloc[0].to_dict())
        else:
            # Multiple sources - merge intelligently
            merged = merge_conflicting_terms(group)
            merged_records.append(merged)

    return pd.DataFrame(merged_records)

def merge_conflicting_terms(group_df):
    """Merge multiple rows for same term."""

    # Sort by source priority (lowest number = highest priority)
    group_df = group_df.copy()
    group_df['Source Priority'] = pd.to_numeric(group_df['Source Priority'])
    group_df = group_df.sort_values('Source Priority')

    # Use highest priority row as base
    base_row = group_df.iloc[0].to_dict()

    # Merge fields intelligently
    merged = base_row.copy()

    # Definition: Use highest priority non-empty definition
    for _, row in group_df.iterrows():
        if pd.notna(row['Definition']) and row['Definition'].strip():
            merged['Definition'] = row['Definition']
            break

    # MeSH term: Use highest priority non-empty MeSH
    for _, row in group_df.iterrows():
        if pd.notna(row['Closest MeSH term']) and row['Closest MeSH term'].strip():
            merged['Closest MeSH term'] = row['Closest MeSH term']
            break

    # Synonyms: Merge from all sources, deduplicate
    all_synonyms = set()
    for _, row in group_df.iterrows():
        for i in [1, 2, 3]:
            syn = row.get(f'Synonym {i}', '')
            if pd.notna(syn) and syn.strip():
                all_synonyms.add(syn.strip())

    # Remove primary term from synonyms
    primary_term = merged['Term']
    all_synonyms.discard(primary_term)

    # Assign back to merged record (limit to 3)
    synonym_list = sorted(list(all_synonyms))[:3]
    for i in range(3):
        merged[f'Synonym {i+1}'] = synonym_list[i] if i < len(synonym_list) else ''

    # Associated terms: Merge from all sources (limit to 8 best)
    all_associated = set()
    for _, row in group_df.iterrows():
        for i in range(1, 9):
            term = row.get(f'Commonly Associated Term {i}', '')
            if pd.notna(term) and term.strip():
                all_associated.add(term.strip())

    associated_list = sorted(list(all_associated))[:8]
    for i in range(8):
        merged[f'Commonly Associated Term {i+1}'] = associated_list[i] if i < len(associated_list) else ''

    # Contributing sources: Combine all
    all_sources = set()
    for _, row in group_df.iterrows():
        sources = str(row.get('Contributing Sources', '')).split(',')
        all_sources.update([s.strip() for s in sources if s.strip()])

    merged['Contributing Sources'] = ','.join(sorted(all_sources))

    return merged

def main():
    print("=" * 60)
    print("Source Merging & Conflict Resolution")
    print("=" * 60)

    # Step 1: Load all source files
    combined_df = load_all_source_files()

    # Step 2: Merge terms by key
    print("\nMerging terms by lowercase key...")
    merged_df = merge_terms_by_key(combined_df)
    print(f"  {len(combined_df):,} rows → {len(merged_df):,} unique terms")

    # Step 3: Remove temporary key column
    if '_key' in merged_df.columns:
        merged_df = merged_df.drop(columns=['_key'])

    # Step 4: Sort by Term
    merged_df = merged_df.sort_values('Term')

    # Step 5: Export
    print(f"\nExporting to {OUTPUT_CSV}...")
    merged_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')

    print("\n✓ Merge complete!")
    print(f"Total unique terms: {len(merged_df):,}")

    # Statistics
    print("\nSource Statistics:")
    for source in merged_df['Source'].unique():
        count = len(merged_df[merged_df['Source'] == source])
        print(f"  {source}: {count:,} terms")

if __name__ == '__main__':
    main()
```

**Estimated runtime**: 30 minutes - 1 hour

---

## Phase 5: Tiered Validation (Nov 22-23, 6 hours)

### 5.1 Tier 1: Structural Validation (100% coverage)

**File**: `scripts/validate_structure.py` (MODIFIED from existing)

**Checks**:

- Exactly 26 columns (22 schema + 4 source metadata)
- `Term` field non-empty
- No duplicate terms
- Valid UTF-8 encoding
- Source priority is integer 1-5

**Implementation**:

```python
#!/usr/bin/env python3
"""
Tier 1: Structural validation for merged database.
Fast checks (runs in seconds).
"""

import pandas as pd
from pathlib import Path

def validate_structure(csv_path):
    """Run structural validation checks."""

    errors = []

    # Load CSV
    df = pd.read_csv(csv_path, encoding='utf-8', dtype=str)

    # Check column count
    expected_cols = 26  # 22 schema + 4 source metadata
    if len(df.columns) != expected_cols:
        errors.append(f"Expected {expected_cols} columns, got {len(df.columns)}")

    # Check Term field
    if df['Term'].isna().any() or (df['Term'] == '').any():
        errors.append("Empty Term field found")

    # Check duplicates
    duplicates = df[df.duplicated('Term', keep=False)]
    if not duplicates.empty:
        errors.append(f"Found {len(duplicates)} duplicate terms")

    # Check source priority
    try:
        priorities = pd.to_numeric(df['Source Priority'])
        if (priorities < 1).any() or (priorities > 5).any():
            errors.append("Invalid source priority (must be 1-5)")
    except:
        errors.append("Source Priority must be numeric")

    return errors

def main():
    csv_path = Path('/Users/sam/NeuroDB-2/neuro_terms.csv')

    print("Running Tier 1 structural validation...")
    errors = validate_structure(csv_path)

    if errors:
        print("\n❌ VALIDATION FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1
    else:
        print("\n✓ Tier 1 PASSED")
        return 0

if __name__ == '__main__':
    exit(main())
```

**Estimated runtime**: 10-30 seconds

### 5.2 Tier 2: Sample-Based MeSH Validation (10% coverage)

**File**: `scripts/validate_sample_mesh.py` (NEW)

**Process**:

1. Random sample 10% of terms (~10K terms)
2. Run mesh-validator agent on sample
3. Calculate pass rate
4. If <95% pass, investigate patterns

**Implementation**:

```python
#!/usr/bin/env python3
"""
Tier 2: Sample-based MeSH validation.
Validates 10% random sample using mesh-validator agent.
"""

import pandas as pd
from pathlib import Path
import subprocess
import json

def sample_terms(csv_path, sample_rate=0.1):
    """Random sample of terms for validation."""
    df = pd.read_csv(csv_path, encoding='utf-8', dtype=str)
    sample = df.sample(frac=sample_rate, random_state=42)
    return sample

def validate_mesh_sample(sample_df):
    """Run mesh-validator on sample."""

    # Write sample to temp CSV
    temp_csv = Path('/tmp/mesh_sample.csv')
    sample_df.to_csv(temp_csv, index=False)

    # Call mesh-validator agent
    # TODO: Implement mesh-validator invocation
    # result = subprocess.run(['opencode', 'run', 'mesh-validator', str(temp_csv)])

    pass  # Placeholder

def main():
    csv_path = Path('/Users/sam/NeuroDB-2/neuro_terms.csv')

    print("Running Tier 2 sample validation (10%)...")
    sample = sample_terms(csv_path)
    print(f"  Sampled {len(sample):,} terms")

    # TODO: Implement validation
    print("\n⚠️  Tier 2 validation not yet implemented")
    return 0

if __name__ == '__main__':
    exit(main())
```

**Estimated runtime**: 1-2 hours

### 5.3 Tier 3: Benchmark Term Validation (High-value terms)

**File**: `scripts/validate_benchmark_terms.py` (NEW)

**Benchmark terms** (from James's feedback):

- Neuromodulation-related: TMS, DBS, tDCS, VNS
- MS-related: multiple sclerosis, relapsing-remitting MS, EDSS
- Alzheimer's-related: Alzheimer's disease, amyloid beta, tau protein

**Process**: Full dual validation (mesh-validator + neuro-reviewer) on these critical terms.

**Estimated runtime**: 30 minutes - 1 hour

---

## Phase 6: Lex Stream Integration (Nov 23-24, 8 hours)

### 6.1 Enhanced Conversion Script

**File**: `convert_to_lexstream.py` (MODIFIED)

**Changes**:

1. Add source metadata to JSON output
2. Handle new 26-column CSV format
3. Generate versioned output filename

**Modifications**:

```python
# Add to convert_entry function (line 89):

def convert_entry(row):
    """Convert a single CSV row to Lex Stream format."""
    # ... existing code ...

    # NEW: Add source metadata
    converted['source_metadata'] = {
        'source': row.get('Source', 'unknown'),
        'source_priority': int(row.get('Source Priority', 99)),
        'contributing_sources': row.get('Contributing Sources', '').split(','),
        'date_added': row.get('Date Added', '')
    }

    return key, converted

# Modify metadata section (line 181):

"metadata": {
    "total_terms": len(terms_dict),
    "total_abbreviations": len(abbreviations),
    "total_mesh_terms": len(mesh_terms),
    "source_file": "neuro_terms.csv",
    "source_name": "UMLS + Neuronames + Wikipedia + NINDS",  # Updated
    "version": version,  # From VERSION.txt
    "date_created": datetime.utcnow().isoformat() + 'Z',
    "sources_included": list(set(df['Source'].unique())),  # NEW
}
```

### 6.2 Lex Stream Runtime Filtering

**File**: `/Users/sam/Lex-stream-2/config.py` (MODIFIED)

**Add configuration**:

```python
# Source filtering configuration
ENABLED_SOURCES = os.getenv('ENABLED_SOURCES', 'all')  # 'all' or 'umls,neuronames,wikipedia'
SOURCE_FILTER_MODE = os.getenv('SOURCE_FILTER_MODE', 'inclusive')  # 'inclusive' or 'exclusive'

def get_enabled_sources():
    """Parse enabled sources from config."""
    if ENABLED_SOURCES == 'all':
        return None  # No filtering
    return [s.strip() for s in ENABLED_SOURCES.split(',')]
```

**File**: `/Users/sam/Lex-stream-2/services/terms_loader.py` (MODIFIED)

**Add filtering logic**:

```python
def load_neuro_terms():
    """
    Load neuroscience terms with optional source filtering.
    """
    global _neuro_terms_cache

    if _neuro_terms_cache is not None:
        return _neuro_terms_cache

    # Load full database
    with open(NEURO_TERMS_JSON_PATH, 'r', encoding='utf-8') as file:
        full_data = json.load(file)

    # Apply source filtering if configured
    enabled_sources = get_enabled_sources()
    if enabled_sources:
        filtered_terms = filter_by_source(full_data['terms'], enabled_sources)

        # Rebuild abbreviations and mesh_terms maps
        abbrev_map = build_abbreviations_map(filtered_terms)
        mesh_map = build_mesh_map(filtered_terms)

        _neuro_terms_cache = {
            'terms': filtered_terms,
            'abbreviations': abbrev_map,
            'mesh_terms': mesh_map,
            'metadata': full_data['metadata']
        }
    else:
        _neuro_terms_cache = full_data

    return _neuro_terms_cache

def filter_by_source(terms_dict, enabled_sources):
    """Filter terms by source."""
    filtered = {}
    for key, term_data in terms_dict.items():
        source = term_data.get('source_metadata', {}).get('source', 'unknown')
        if source in enabled_sources:
            filtered[key] = term_data
    return filtered

def build_abbreviations_map(terms_dict):
    """Rebuild abbreviations map for filtered terms."""
    # Same logic as convert_to_lexstream.py
    pass

def build_mesh_map(terms_dict):
    """Rebuild MeSH map for filtered terms."""
    # Same logic as convert_to_lexstream.py
    pass
```

**Backward compatibility**: Default `ENABLED_SOURCES='all'` means no filtering (all sources used).

---

## Phase 7: Testing & Benchmarking (Nov 24, 6 hours)

### 7.1 Test Configurations

**File**: `tests/test_source_combinations.py` (NEW)

**Configurations to test**:

| Config          | Sources                                | Expected Terms | Purpose                     |
| --------------- | -------------------------------------- | -------------- | --------------------------- |
| baseline        | wikipedia,ninds                        | 595            | Current production baseline |
| umls-only       | umls                                   | ~100K          | Test UMLS quality alone     |
| umls-neuronames | umls,neuronames                        | ~103K          | Primary deployment target   |
| all-sources     | umls,neuronames,nif,go,wikipedia,ninds | ~130K+         | Maximum coverage            |

**Benchmark queries** (from James):

1. **Neuromodulation for MS**:

   - Include: neuromodulation, multiple sclerosis
   - Exclude: animal studies
1. **Alzheimer's treatment**:

   - Include: Alzheimer's disease, treatment, clinical trial
   - Exclude: review articles
1. **Stroke rehabilitation**:

   - Include: stroke, rehabilitation, motor recovery
   - Exclude: case reports

**Metrics to track**:

- Synonyms added per query
- MeSH terms detected
- Query complexity (number of terms in final query)
- Quality score vs baseline

**Implementation**:

```python
#!/usr/bin/env python3
"""
Test different source combinations against benchmark queries.
"""

import os
import json
import pandas as pd
from pathlib import Path

BENCHMARK_QUERIES = [
    {
        'name': 'Neuromodulation for MS',
        'include': 'neuromodulation, multiple sclerosis',
        'exclude': 'animal studies'
    },
    {
        'name': 'Alzheimer treatment',
        'include': "Alzheimer's disease, treatment, clinical trial",
        'exclude': 'review articles'
    },
    {
        'name': 'Stroke rehabilitation',
        'include': 'stroke, rehabilitation, motor recovery',
        'exclude': 'case reports'
    }
]

CONFIGS = [
    {'name': 'baseline', 'sources': 'wikipedia,ninds'},
    {'name': 'umls-only', 'sources': 'umls'},
    {'name': 'umls-neuronames', 'sources': 'umls,neuronames'},
    {'name': 'all-sources', 'sources': 'all'},
]

def test_configuration(config, query):
    """Test a specific source configuration against a benchmark query."""

    # Set environment variable
    os.environ['ENABLED_SOURCES'] = config['sources']

    # TODO: Call Lex Stream API to generate query
    # result = requests.post('http://localhost:5000/api/generate-query', ...)

    # Track metrics
    metrics = {
        'config': config['name'],
        'query': query['name'],
        'synonyms_added': 0,  # TODO: Extract from API response
        'mesh_terms_detected': 0,
        'query_complexity': 0,
    }

    return metrics

def main():
    results = []

    for config in CONFIGS:
        print(f"\nTesting configuration: {config['name']}")
        for query in BENCHMARK_QUERIES:
            print(f"  Query: {query['name']}")
            metrics = test_configuration(config, query)
            results.append(metrics)

    # Save results
    df = pd.DataFrame(results)
    df.to_csv('test_results.csv', index=False)

    print("\n✓ Benchmarking complete!")

if __name__ == '__main__':
    main()
```

**Estimated runtime**: 2-3 hours

### 7.2 Quality Comparison Report

**File**: `tests/generate_comparison_report.py` (NEW)

**Output**: Markdown report comparing baseline vs new configurations

**Metrics**:

- Database size (terms, abbreviations, MeSH coverage)
- Synonyms per term (avg, median, max)
- Definition completeness (% with definitions)
- MeSH coverage (% with valid MeSH terms)
- Benchmark query improvements (before/after)

---

## Phase 8: Deployment (Nov 25, 4 hours)

### 8.1 Deployment Workflow

**Process** (already automated via GitHub Actions):

1. **Local validation** (NeuroDB-2):

   ```bash
   cd /Users/sam/NeuroDB-2

   # Run tiered validation
   python scripts/validate_structure.py
   python scripts/validate_sample_mesh.py
   python scripts/validate_benchmark_terms.py

   # Generate Lex Stream JSON
   python convert_to_lexstream.py
   # Output: neuro_terms_v3.0.0_umls-neuronames-wikipedia-ninds.json

   # Test locally
   python validate_lexstream_db.py
   python test_lexstream_db.py
   ```
1. **Copy to Lex Stream** (manual step):

   ```bash
   cp /Users/sam/NeuroDB-2/neuro_terms_v3.0.0_*.json \
      /Users/sam/Lex-stream-2/neuro_terms.json
   ```
1. **Local Lex Stream testing**:

   ```bash
   cd /Users/sam/Lex-stream-2

   # Test locally
   python app.py
   # Verify /api/terms endpoint
   # Test benchmark queries
   ```
1. **Staging deployment** (automated):

   ```bash
   cd /Users/sam/Lex-stream-2

   git add neuro_terms.json
   git commit -m "Update terminology database to v3.0.0 (100K+ terms from UMLS/Neuronames/Wikipedia/NINDS)"
   git push origin main

   # GitHub Actions automatically:
   # - Builds Docker image
   # - Deploys to Cloud Run staging
   # - Runs health checks
   ```
1. **Staging verification**:

   - Test /api/terms endpoint (check metadata)
   - Run benchmark queries
   - Verify performance (load time < 5s)
   - Check logs for errors
1. **Production deployment** (automated, same commit):

   - GitHub Actions auto-deploys to production
   - Monitor logs
   - Verify health endpoint
1. **Rollback plan** (if issues):

   ```bash
   git revert HEAD
   git push origin main
   # Auto-deploys previous version
   ```

### 8.2 Performance Considerations

**Large JSON file handling** (~60-90 MB estimated):

**Backend optimization** (already implemented):

- Global cache in `terms_loader.py` (loads once at startup)
- Expected load time: 2-5 seconds (one-time cost)
- Memory footprint: ~150-250 MB (acceptable)

**Monitoring**:

- Check Cloud Run memory usage
- Monitor startup time
- Verify cache hit rates (Redis)

---

## File Structure

```
/Users/sam/NeuroDB-2/
├── schemas/
│   └── source_metadata.py          # NEW - Source priority and metadata
├── importers/
│   ├── umls_import.py              # NEW - UMLS RRF parser
│   ├── neuronames_import.py        # NEW - Neuronames JSON parser
│   ├── nif_import.py               # NEW - NIF OWL parser
│   └── go_import.py                # NEW - GO OBO parser
├── scripts/
│   ├── merge_sources.py            # NEW - Conflict resolution
│   ├── validate_structure.py      # MODIFIED - 26-column validation
│   ├── validate_sample_mesh.py    # NEW - Tier 2 validation
│   └── validate_benchmark_terms.py # NEW - Tier 3 validation
├── tests/
│   ├── test_source_combinations.py # NEW - Benchmark testing
│   └── generate_comparison_report.py # NEW - Quality report
├── LetterFiles/
│   ├── A.csv                       # Existing - Wikipedia/NINDS
│   ├── A_UMLS.csv                  # NEW - UMLS terms starting with A
│   ├── A_NEURONAMES.csv            # NEW - Neuronames terms starting with A
│   └── ...
├── convert_to_lexstream.py         # MODIFIED - Add source metadata
├── neuro_terms.csv                 # MODIFIED - 26 columns (22 + 4 source)
├── neuro_terms_v3.0.0_umls-neuronames-wikipedia-ninds.json  # NEW
├── VERSION.txt                     # UPDATE to 3.0.0
└── CHANGELOG.md                    # UPDATE with v3.0.0 changes

/Users/sam/Lex-stream-2/
├── config.py                       # MODIFIED - Add source filtering
├── services/
│   └── terms_loader.py             # MODIFIED - Runtime filtering
└── tests/
    └── test_source_filtering.py    # NEW - Test filtering logic
```

---

## Implementation Timeline (Nov 20-25)

### Day 1 (Nov 20): Infrastructure + Neuronames

**Hours: 8**

| Time        | Task                              | Duration | Output                |
| ----------- | --------------------------------- | -------- | --------------------- |
| 09:00-10:00 | Create schemas/source_metadata.py | 1h       | Source tagging system |
| 10:00-12:00 | Implement neuronames_import.py    | 2h       | Neuronames importer   |
| 12:00-13:00 | Lunch                             | 1h       | -                     |
| 13:00-14:00 | Run Neuronames import             | 1h       | ~3K terms added       |
| 14:00-17:00 | Implement merge_sources.py        | 3h       | Merge algorithm       |

**Deliverable**: Neuronames data imported, merge system ready

### Day 2 (Nov 21): UMLS Import

**Hours: 10**

| Time        | Task                               | Duration | Output            |
| ----------- | ---------------------------------- | -------- | ----------------- |
| 09:00-12:00 | Implement umls_import.py           | 3h       | UMLS parser       |
| 12:00-13:00 | Lunch                              | 1h       | -                 |
| 13:00-15:00 | Download UMLS 2024AB (if not done) | 2h       | UMLS RRF files    |
| 15:00-19:00 | Run UMLS import                    | 4h       | ~100K terms added |

**Deliverable**: UMLS data imported (~100K terms)

### Day 3 (Nov 22): NIF + GO + Merge + Validation

**Hours: 10**

| Time        | Task                           | Duration | Output                       |
| ----------- | ------------------------------ | -------- | ---------------------------- |
| 09:00-11:00 | Implement nif_import.py        | 2h       | NIF parser                   |
| 11:00-12:00 | Run NIF import                 | 1h       | ~30K terms added             |
| 12:00-13:00 | Lunch                          | 1h       | -                            |
| 13:00-14:30 | Implement go_import.py         | 1.5h     | GO parser                    |
| 14:30-15:00 | Run GO import                  | 0.5h     | ~2K terms added              |
| 15:00-17:00 | Run merge_sources.py           | 2h       | Consolidated neuro_terms.csv |
| 17:00-19:00 | Run Tier 1 + Tier 2 validation | 2h       | Validation reports           |

**Deliverable**: All sources merged, initial validation passed

### Day 4 (Nov 23): Lex Stream Integration

**Hours: 8**

| Time        | Task                                           | Duration | Output                    |
| ----------- | ---------------------------------------------- | -------- | ------------------------- |
| 09:00-11:00 | Modify convert_to_lexstream.py                 | 2h       | Enhanced converter        |
| 11:00-12:00 | Run conversion                                 | 1h       | neuro_terms_v3.0.0_*.json |
| 12:00-13:00 | Lunch                                          | 1h       | -                         |
| 13:00-15:00 | Modify Lex Stream (config.py, terms_loader.py) | 2h       | Source filtering          |
| 15:00-17:00 | Local testing (Lex Stream)                     | 2h       | Verified locally          |

**Deliverable**: Lex Stream compatible JSON, local testing passed

### Day 5 (Nov 24): Testing + Benchmarking

**Hours: 8**

| Time        | Task                                  | Duration | Output             |
| ----------- | ------------------------------------- | -------- | ------------------ |
| 09:00-12:00 | Implement test_source_combinations.py | 3h       | Testing framework  |
| 12:00-13:00 | Lunch                                 | 1h       | -                  |
| 13:00-16:00 | Run benchmark tests                   | 3h       | Comparison metrics |
| 16:00-17:00 | Generate comparison report            | 1h       | Quality report     |

**Deliverable**: Benchmark results, quality metrics

### Day 6 (Nov 25): Deployment + Demo

**Hours: 6**

| Time        | Task                      | Duration | Output                    |
| ----------- | ------------------------- | -------- | ------------------------- |
| 09:00-10:00 | Final validation (Tier 3) | 1h       | Benchmark terms validated |
| 10:00-11:00 | Deploy to staging         | 1h       | Staging environment live  |
| 11:00-12:00 | Staging verification      | 1h       | Verified                  |
| 12:00-13:00 | Lunch                     | 1h       | -                         |
| 13:00-14:00 | Deploy to production      | 1h       | Production live           |
| 14:00-15:00 | Prepare demo materials    | 1h       | Demo ready                |

**Deliverable**: Production deployment, demo materials

---

## Testing Strategy

### Validation Tiers

**Tier 1: Structural (100% coverage)**

- Column count (26 columns)
- Required fields (Term, Source)
- Encoding (UTF-8)
- Duplicates check
- **Pass criteria**: Zero errors

**Tier 2: Sample (10% coverage)**

- Random sample: ~10K terms
- MeSH validation via mesh-validator
- **Pass criteria**: ≥95% pass rate

**Tier 3: High-value (Benchmark terms)**

- Full dual validation on critical terms
- James's benchmark queries
- **Pass criteria**: 100% pass rate

### Performance Testing

**Metrics to track**:

- JSON load time (target: <5s)
- Memory usage (target: <300 MB)
- API response time (no degradation vs baseline)
- Cache hit rate (Redis)

### Quality Metrics

**Database quality**:

- Definition completeness: % terms with definitions
- MeSH coverage: % terms with MeSH mappings
- Synonym density: avg synonyms per term
- Source distribution: terms per source

**Query quality** (vs baseline):

- Synonyms added per query
- MeSH terms detected
- Query complexity (term count)
- Result relevance (subjective)

---

## Risk Mitigation

### Risk 1: UMLS License Delays

**Probability**: Low

**Impact**: High

**Mitigation**: Apply for UMLS license immediately (usually instant approval). If delayed, prioritize Neuronames + NIF + GO first.

### Risk 2: Memory Issues (Large JSON)

**Probability**: Medium

**Impact**: Medium

**Mitigation**:

- Implement pagination if needed
- Monitor Cloud Run memory usage
- Consider JSON streaming if >100 MB

### Risk 3: Empty Fields

**Probability**: High

**Impact**: Low

**Mitigation**:

- Empty fields acceptable per "accuracy over completeness" rule
- Agents handle empty fields gracefully
- Fill from lower priority sources when merging

### Risk 4: MeSH Validation Failures

**Probability**: Medium

**Impact**: Medium

**Mitigation**:

- Use tiered validation (not 100% coverage)
- Sample-based approach (10% random)
- Focus validation on benchmark terms

### Risk 5: Performance Degradation

**Probability**: Low

**Impact**: High

**Mitigation**:

- Load testing before deployment
- Redis caching already implemented
- Rollback procedure ready

### Risk 6: Source Conflicts

**Probability**: High

**Impact**: Low

**Mitigation**:

- Clear priority ranking (UMLS > Neuronames > Wikipedia)
- Merge algorithm tested on sample data
- Manual review of conflicts if needed

---

## Success Criteria

### Quantitative Metrics

**Database size**:

- ✅ Target: 100K+ terms (vs 595 baseline)
- ✅ MeSH coverage: ≥80%
- ✅ Definition completeness: ≥70%

**Performance**:

- ✅ JSON load time: <5s
- ✅ Memory usage: <500 MB
- ✅ API response time: no degradation

**Validation**:

- ✅ Tier 1: 100% pass rate
- ✅ Tier 2: ≥95% pass rate
- ✅ Tier 3: 100% pass rate (benchmark terms)

### Qualitative Metrics

**Lex Stream integration**:

- ✅ Zero breaking changes to frontend/backend
- ✅ Automated deployment successful
- ✅ No production errors

**Query quality**:

- ✅ More synonyms added per query
- ✅ Better MeSH coverage
- ✅ Benchmark queries perform better than baseline

**Usability**:

- ✅ Source filtering works as expected
- ✅ Documentation updated
- ✅ Team can test different source combinations

---

## Rollback Plan

**If deployment fails**:

1. **Identify issue** (logs, error messages)
2. **Revert commit** in Lex Stream repo:

   ```bash
   git revert HEAD
   git push origin main
   ```
3. **Auto-deploy previous version** (GitHub Actions)
4. **Verify production** is back to baseline
5. **Debug issue locally**
6. **Re-deploy when fixed**

**If performance issues**:

1. **Disable source filtering** (set `ENABLED_SOURCES='wikipedia,ninds'`)
2. **Redeploy with baseline configuration**
3. **Investigate memory/performance bottleneck**
4. **Optimize and retry**

---

## Documentation Updates

### Files to Update

**NeuroDB-2**:

- `CLAUDE.md` - Update workflows, add source control section
- `README.md` - Add bulk import instructions
- `CHANGELOG.md` - v3.0.0 release notes
- `VERSION.txt` - Update to 3.0.0
- `docs/codebase-summary.md` - Update architecture

**Lex Stream**:

- `CLAUDE.md` - Document source filtering feature
- `README.md` - Update database version
- `config.py` - Add comments for new env vars
- `docs/DEPLOYMENT.md` - Update deployment steps

---

## Unresolved Questions

1. **UMLS License**: Do you have UMLS account credentials already? If not, apply immediately at https://uts.nlm.nih.gov/uts/signup-login
1. **Neuroscience Filtering Strategy**: For UMLS, which filtering approach?

   - Option A: Conservative (MeSH tree codes C10, F01-F03, G11) → ~50K-100K terms
   - Option B: Aggressive (semantic types) → ~200K-500K terms
   - Recommendation: Start with Option A
1. **Source Priority Adjustments**: Are the proposed rankings correct?

   - UMLS (1) > Neuronames (2) > Wikipedia/NINDS (3) > NIF (4) > GO (5)
   - Or should Neuronames be higher priority for neuroanatomy terms?
1. **Performance Threshold**: What is acceptable JSON load time?

   - Current plan assumes 2-5s is acceptable for 100K terms
   - If stricter requirement, may need pagination or lazy loading
1. **Quality Bar**: Is 90%+ pass rate on tiered validation acceptable for Nov 25 deadline?

   - Or do you require 95%+ before deployment?
1. **Testing Scope**: Which source combinations should be prioritized for testing?

   - Baseline vs UMLS-only vs UMLS+Neuronames vs All-sources?
   - Or focus only on UMLS+Neuronames (recommended deployment)?
1. **Benchmark Queries**: Are the 3 proposed benchmark queries sufficient?

   - Neuromodulation for MS
   - Alzheimer's treatment
   - Stroke rehabilitation
   - Or do you have specific queries from James?
1. **Deployment Timing**: What time on Nov 25 is the demo/deadline?

   - Need to ensure deployment completes with buffer time for verification

---

**Document Status**: Ready for implementation

**Next Steps**:

1. Answer unresolved questions
2. Apply for UMLS license (if not done)
3. Begin Phase 1 implementation (Nov 20)

**Estimated Total Time**: 48-54 hours over 6 days (Nov 20-25)