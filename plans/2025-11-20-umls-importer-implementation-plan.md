# UMLS Metathesaurus Importer - Implementation Plan

**Date**: 2025-11-20
**Status**: Ready for Implementation
**Priority**: P1 (Critical - Provides 100K-150K neuroscience terms)
**Estimated Duration**: 4-5 hours

---

## Overview

Implement UMLS Metathesaurus importer to extract 100K-150K neuroscience-relevant terms from 4M+ UMLS concepts, mapping to NeuroDB-2 extended 26-column schema. This source will provide comprehensive definitions (addressing NIF's 87% placeholder rate), extensive synonyms, MeSH mappings, and domain-specific associated terms.

### Critical Success Criteria

- Filter 4M+ UMLS concepts → 100K-150K neuroscience terms using hybrid semantic type + source vocabulary strategy
- Extract data from 4 RRF files: MRCONSO (concepts), MRDEF (definitions), MRREL (relationships), MRSTY (semantic types)
- Profile "related concepts" quality to answer DEC-001 (domain-specific vs generic taxonomy)
- Pass structural validation (26 columns, UTF-8, no duplicates)
- Achieve 80%+ definition coverage (vs NIF's 13%)
- Document relationship quality findings for merge phase

---

## Requirements

### Functional Requirements

1. **Filtering Accuracy**: Extract neuroscience-relevant concepts with 90%+ precision
2. **Data Completeness**: Populate all applicable schema fields (terms, definitions, synonyms, abbreviations, MeSH, associations)
3. **Source Priority**: Handle multi-source duplicates (MSH > SNOMEDCT_US > NCI > other)
4. **Memory Efficiency**: Stream multi-GB files line-by-line without loading full datasets
5. **Relationship Profiling**: Sample and classify 100+ relationship types to answer DEC-001

### Non-Functional Requirements

1. **Performance**: Process 4M concepts in <2 hours on standard hardware
2. **Memory Usage**: <4GB RAM peak during processing
3. **Scalability**: Support future UMLS releases with minimal code changes
4. **Maintainability**: Reuse existing infrastructure (schema_mapper, source_tagger, validators)
5. **Documentation**: Generate detailed profiling report for merge phase decisions

---

## Architecture

### Data Flow

```
UMLS Files (downloads/)
    ↓
[Phase 1] MRSTY.RRF → Build neuroscience CUI filter
    ↓
    neuroscience_cuis.txt (100K-150K CUIs)
    ↓
[Phase 2] MRCONSO.RRF → Extract terms/synonyms/abbreviations (stream, filter by CUI)
    ↓
[Phase 3] MRDEF.RRF → Extract definitions (stream, filter by CUI)
    ↓
[Phase 4] MRREL.RRF → Extract related concepts + PROFILE QUALITY (DEC-001)
    ↓
    umls_data_dict (CUI → {term, definition, synonyms, related, ...})
    ↓
[Phase 5] Map to NeuroDB-2 schema → Handle duplicates → Add source metadata
    ↓
    imports/umls/umls_neuroscience_imported.csv
    ↓
[Phase 6] Structural validation + Data profiling + Documentation
    ↓
    ✅ READY FOR MERGE
```

### Component Interactions

**Reused Infrastructure**:
- `lib/schema_mapper.py` - `map_umls_to_schema()`, `create_empty_row()`, `validate_row()`
- `lib/source_tagger.py` - `add_source_metadata(row, 'umls')`
- `lib/validators.py` - `generate_validation_report()`, `print_validation_report()`

**New Components**:
- `scripts/build_umls_filter_index.py` - Semantic type filtering
- `scripts/import_umls_neuroscience.py` - Main import pipeline
- `scripts/lib/umls_parsers.py` - RRF file streaming utilities
- `scripts/lib/umls_profilers.py` - Relationship quality analysis (DEC-001)

---

## Implementation Steps

### Phase 1: Environment Setup & Download (30 min)

**Goal**: Prepare UMLS files and verify structure

**Steps**:
1. Create directory structure:
   ```bash
   mkdir -p imports/umls
   mkdir -p downloads/umls/2024AB/META
   ```

2. **Ask user for UMLS file location**:
   - Option A: Already downloaded → verify files exist
   - Option B: Need to download → provide instructions with license login

3. Verify required files present:
   ```bash
   downloads/umls/2024AB/META/MRCONSO.RRF  # ~6GB, 16M rows
   downloads/umls/2024AB/META/MRDEF.RRF   # ~600MB, 1.2M rows
   downloads/umls/2024AB/META/MRREL.RRF   # ~2GB, 60M rows
   downloads/umls/2024AB/META/MRSTY.RRF   # ~40MB, 2M rows
   ```

4. Create profiling script structure:
   ```bash
   touch scripts/lib/umls_parsers.py
   touch scripts/lib/umls_profilers.py
   touch scripts/build_umls_filter_index.py
   touch scripts/import_umls_neuroscience.py
   ```

**Validation**: All 4 RRF files readable, file sizes match expected ranges

---

### Phase 2: Build Neuroscience CUI Filter (45 min)

**Script**: `scripts/build_umls_filter_index.py`

**Goal**: Create filtered list of 100K-150K neuroscience-relevant CUIs

**Algorithm** (Hybrid Approach):

```python
# Neuroscience Semantic Types (from UMLS TUI codes)
NEURO_SEMANTIC_TYPES = {
    # Anatomical (Priority 1)
    'T023': 'Body Part, Organ, or Organ Component',
    'T029': 'Body Location or Region',
    'T030': 'Body Space or Junction',
    'T025': 'Cell',
    'T026': 'Cell Component',
    'T024': 'Tissue',

    # Physiological (Priority 1)
    'T039': 'Physiologic Function',
    'T040': 'Organism Function',
    'T042': 'Organ or Tissue Function',
    'T043': 'Cell Function',
    'T044': 'Molecular Function',
    'T041': 'Mental Process',

    # Behavioral (Priority 2)
    'T053': 'Behavior',
    'T054': 'Social Behavior',
    'T048': 'Mental or Behavioral Dysfunction',

    # Pathological (Priority 1)
    'T047': 'Disease or Syndrome',
    'T046': 'Pathologic Function',
    'T049': 'Cell or Molecular Dysfunction',
    'T191': 'Neoplastic Process',
    'T037': 'Injury or Poisoning',

    # Chemical (Priority 2)
    'T121': 'Pharmacologic Substance',
    'T116': 'Amino Acid, Peptide, or Protein',
    'T123': 'Biologically Active Substance',
    'T125': 'Hormone',
    'T192': 'Receptor',
    'T114': 'Nucleic Acid, Nucleoside, or Nucleotide',

    # Procedures (Priority 3 - selective)
    'T060': 'Diagnostic Procedure',
    'T061': 'Therapeutic or Preventive Procedure',
}

# Priority Source Vocabularies
PRIORITY_SOURCES = ['MSH', 'SNOMEDCT_US', 'NCI', 'NDFRT', 'GO', 'HPO', 'OMIM']

# Neuroscience Keywords (for supplemental filtering)
NEURO_KEYWORDS = [
    'neuro', 'brain', 'cerebr', 'cortex', 'neural', 'synap',
    'axon', 'dendrit', 'glia', 'astrocyt', 'cognit', 'memory',
    'psychiatric', 'mental', 'behavior'
]
```

**Processing Logic**:
1. Parse MRSTY.RRF (pipe-delimited: `CUI|TUI|STN|STY|ATUI|CVF`)
2. For each CUI, collect semantic type codes (TUI)
3. Include CUI if:
   - Has any Priority 1 semantic type, OR
   - Has Priority 2 semantic type AND (from priority source OR contains neuro keyword), OR
   - Has Priority 3 semantic type AND from priority source AND contains neuro keyword

**Output**:
- `imports/umls/neuroscience_cuis.txt` - One CUI per line
- `imports/umls/filter_statistics.json` - Counts by semantic type, source, keyword

**Expected Result**: 100K-150K CUIs (validate range before continuing)

---

### Phase 3: Extract Terms and Synonyms (60 min)

**Script**: `scripts/import_umls_neuroscience.py` (Part 1)

**Goal**: Parse MRCONSO.RRF to extract terms, synonyms, abbreviations for filtered CUIs

**MRCONSO.RRF Structure** (18 columns, pipe-delimited):
```
CUI|LAT|TS|LUI|STT|SUI|ISPREF|AUI|SAUI|SCUI|SDUI|SAB|TTY|CODE|STR|SRL|SUPPRESS|CVF
```

**Key Columns**:
- `CUI` (col 0): Concept identifier
- `LAT` (col 1): Language (filter: ENG)
- `SAB` (col 11): Source vocabulary (MSH, SNOMEDCT_US, etc.)
- `TTY` (col 12): Term type (PN=Preferred Name, SY=Synonym, AB=Abbreviation)
- `STR` (col 14): The actual term string
- `SUPPRESS` (col 16): Suppression flag (filter: N = not suppressed)
- `ISPREF` (col 6): Preferred term flag (Y/N)

**Streaming Algorithm**:
```python
import csv
from collections import defaultdict

# Load filtered CUIs
with open('imports/umls/neuroscience_cuis.txt') as f:
    neuro_cuis = set(line.strip() for line in f)

# Stream MRCONSO.RRF (6GB file - DO NOT load into memory)
concepts = defaultdict(lambda: {
    'preferred_term': None,
    'synonyms': [],
    'abbreviations': [],
    'sources': set(),
    'mesh_code': None
})

with open('downloads/umls/2024AB/META/MRCONSO.RRF', encoding='utf-8') as f:
    for line in f:
        cols = line.strip().split('|')
        cui = cols[0]

        # Early filter (critical for performance)
        if cui not in neuro_cuis:
            continue
        if cols[1] != 'ENG':  # Language filter
            continue
        if cols[16] != 'N':  # Skip suppressed
            continue

        sab = cols[11]  # Source
        tty = cols[12]  # Term type
        term_str = cols[14]
        ispref = cols[6]

        # Track source vocabularies
        concepts[cui]['sources'].add(sab)

        # Extract preferred term
        if ispref == 'Y' or tty == 'PN':
            if not concepts[cui]['preferred_term']:
                concepts[cui]['preferred_term'] = term_str

        # Extract synonyms
        elif tty in ['SY', 'FN', 'MTH_FN']:
            if term_str not in concepts[cui]['synonyms']:
                concepts[cui]['synonyms'].append(term_str)

        # Extract abbreviations
        elif tty in ['AB', 'ACR']:
            if term_str not in concepts[cui]['abbreviations']:
                concepts[cui]['abbreviations'].append(term_str)

        # Extract MeSH code (if SAB=MSH)
        if sab == 'MSH' and not concepts[cui]['mesh_code']:
            concepts[cui]['mesh_code'] = cols[13]  # CODE column

# Deduplicate by preferred term (case-insensitive)
# Priority: MSH > SNOMEDCT_US > NCI > other
unique_terms = {}
for cui, data in concepts.items():
    term = data['preferred_term']
    if not term:
        continue

    term_key = term.lower().strip()

    if term_key not in unique_terms:
        unique_terms[term_key] = (cui, data)
    else:
        # Compare source priorities
        existing_sources = unique_terms[term_key][1]['sources']
        new_sources = data['sources']

        if 'MSH' in new_sources and 'MSH' not in existing_sources:
            unique_terms[term_key] = (cui, data)
        elif 'SNOMEDCT_US' in new_sources and 'MSH' not in existing_sources:
            unique_terms[term_key] = (cui, data)

print(f"Extracted {len(unique_terms)} unique neuroscience terms")
```

**Output**: `concepts` dict with terms/synonyms/abbreviations/MeSH codes

**Validation**: 100K-150K unique terms, 90%+ have preferred term populated

---

### Phase 4: Extract Definitions (30 min)

**Script**: `scripts/import_umls_neuroscience.py` (Part 2)

**Goal**: Parse MRDEF.RRF to add definitions to concepts

**MRDEF.RRF Structure** (8 columns):
```
CUI|AUI|ATUI|SATUI|SAB|DEF|SUPPRESS|CVF
```

**Streaming Algorithm**:
```python
# Stream MRDEF.RRF (~600MB)
with open('downloads/umls/2024AB/META/MRDEF.RRF', encoding='utf-8') as f:
    for line in f:
        cols = line.strip().split('|')
        cui = cols[0]

        # Early filter
        if cui not in concepts:
            continue
        if cols[6] != 'N':  # Skip suppressed
            continue

        sab = cols[4]
        definition = cols[5]

        # Prioritize definition sources: MSH > SNOMEDCT_US > NCI > other
        existing_def = concepts[cui].get('definition')
        existing_source = concepts[cui].get('definition_source', '')

        # Update if better source or no existing definition
        if not existing_def or \
           (sab == 'MSH') or \
           (sab == 'SNOMEDCT_US' and existing_source != 'MSH') or \
           (sab == 'NCI' and existing_source not in ['MSH', 'SNOMEDCT_US']):
            concepts[cui]['definition'] = definition
            concepts[cui]['definition_source'] = sab
```

**Validation**: Check definition coverage (target: 80%+)

---

### Phase 5: Extract and Profile Related Concepts (90 min) ⚠️ CRITICAL for DEC-001

**Script**: `scripts/import_umls_neuroscience.py` (Part 3) + `scripts/lib/umls_profilers.py`

**Goal**: Extract related concepts AND profile quality to answer DEC-001

**MRREL.RRF Structure** (16 columns):
```
CUI1|AUI1|STYPE1|REL|CUI2|AUI2|STYPE2|RELA|RUI|SRUI|SAB|SL|RG|DIR|SUPPRESS|CVF
```

**Key Columns**:
- `CUI1`, `CUI2` (cols 0, 4): Related concepts
- `REL` (col 3): Relationship type (RB=Broader, RN=Narrower, RO=Other, RL=Like)
- `RELA` (col 7): Specific relationship (may_treat, may_diagnose, associated_with, etc.)
- `SAB` (col 10): Source of relationship

**Extraction Algorithm**:
```python
from collections import Counter

# Track relationship types for profiling
relationship_types = Counter()
sample_relationships = []  # For manual inspection

with open('downloads/umls/2024AB/META/MRREL.RRF', encoding='utf-8') as f:
    for line in f:
        cols = line.strip().split('|')
        cui1, cui2 = cols[0], cols[4]

        # Include if either CUI is neuroscience-relevant
        if cui1 not in concepts and cui2 not in concepts:
            continue
        if cols[15] != 'N':  # Skip suppressed
            continue

        rel = cols[3]
        rela = cols[7]
        sab = cols[10]

        # Track for profiling
        relationship_types[(rel, rela, sab)] += 1

        # Sample first 1000 for manual review
        if len(sample_relationships) < 1000:
            # Get term strings for CUIs
            term1 = concepts[cui1]['preferred_term'] if cui1 in concepts else cui1
            term2 = concepts[cui2]['preferred_term'] if cui2 in concepts else cui2
            sample_relationships.append({
                'term1': term1,
                'term2': term2,
                'rel': rel,
                'rela': rela,
                'source': sab
            })

        # Add to related_concepts (filter by relationship quality later)
        if cui1 in concepts:
            related_term = concepts[cui2]['preferred_term'] if cui2 in concepts else None
            if related_term and related_term not in concepts[cui1].get('related_concepts', []):
                if 'related_concepts' not in concepts[cui1]:
                    concepts[cui1]['related_concepts'] = []
                concepts[cui1]['related_concepts'].append({
                    'term': related_term,
                    'rel': rel,
                    'rela': rela,
                    'source': sab
                })
```

**DEC-001 Profiling Analysis**:

Create `scripts/lib/umls_profilers.py`:

```python
def profile_relationship_quality(sample_relationships, concepts):
    """
    Analyzes relationship quality to answer DEC-001.

    Classifies relationships as:
    - Domain-specific: hippocampus → memory, learning, Alzheimer's
    - Generic taxonomy: hippocampus → Body Part, Regional part of brain
    - Mixed: Some useful, some generic

    Returns profiling report with recommendations.
    """

    # Classify RELA types
    domain_specific_rela = {
        'may_treat', 'may_diagnose', 'may_prevent', 'may_cause',
        'associated_with', 'co-occurs_with', 'interacts_with',
        'affects', 'disrupts', 'stimulates', 'inhibits'
    }

    generic_taxonomy_rela = {
        'isa', 'inverse_isa', 'part_of', 'has_part',
        'component_of', 'has_component'
    }

    # Analyze sample
    domain_count = 0
    generic_count = 0
    mixed_count = 0

    for rel in sample_relationships[:100]:  # Analyze first 100
        rela = rel['rela']

        if rela in domain_specific_rela:
            domain_count += 1
        elif rela in generic_taxonomy_rela:
            generic_count += 1
        else:
            mixed_count += 1

    # Generate report
    total = domain_count + generic_count + mixed_count
    report = {
        'total_sampled': total,
        'domain_specific': domain_count,
        'domain_specific_pct': (domain_count / total * 100) if total > 0 else 0,
        'generic_taxonomy': generic_count,
        'generic_taxonomy_pct': (generic_count / total * 100) if total > 0 else 0,
        'mixed': mixed_count,
        'recommendation': None,
        'top_relationship_types': None
    }

    # Determine recommendation
    if report['domain_specific_pct'] > 60:
        report['recommendation'] = 'USE_DIRECTLY'
        report['rationale'] = 'Majority are domain-specific associations'
    elif report['generic_taxonomy_pct'] > 60:
        report['recommendation'] = 'FILTER_BY_RELA'
        report['rationale'] = 'Majority are generic taxonomy, need filtering'
    else:
        report['recommendation'] = 'SMART_FILTER'
        report['rationale'] = 'Mixed quality, filter by RELA whitelist'

    return report
```

**Outputs**:
1. `imports/umls/relationship_profiling_report.json` - DEC-001 analysis
2. `imports/umls/relationship_samples.csv` - 1000 sample relationships for review
3. Updated `concepts` dict with related_concepts

**Validation**:
- Review profiling report
- Manually inspect 20 random samples
- Decide filtering strategy before final mapping

---

### Phase 6: Map to NeuroDB-2 Schema (45 min)

**Script**: `scripts/import_umls_neuroscience.py` (Part 4)

**Goal**: Convert concepts dict to CSV rows conforming to 26-column schema

**Mapping Logic** (reuse `lib/schema_mapper.map_umls_to_schema`):

```python
from lib.schema_mapper import create_empty_row
from lib.source_tagger import add_source_metadata

rows = []
for cui, data in concepts.items():
    row = create_empty_row()

    # Core fields
    row['Term'] = data.get('preferred_term', '')
    row['Definition'] = data.get('definition', '')

    # Closest MeSH term
    row['Closest MeSH term'] = data.get('mesh_code', '')

    # Synonyms (max 3)
    for i, syn in enumerate(data.get('synonyms', [])[:3]):
        row[f'Synonym {i+1}'] = syn

    # Abbreviation (first one)
    abbrevs = data.get('abbreviations', [])
    if abbrevs:
        row['Abbreviation'] = abbrevs[0]

    # Associated terms (max 8)
    # Apply DEC-001 filtering if recommendation = 'FILTER_BY_RELA'
    related = data.get('related_concepts', [])

    # Filter by RELA if needed (based on profiling)
    if profiling_report['recommendation'] == 'FILTER_BY_RELA':
        domain_specific_rela = {
            'may_treat', 'may_diagnose', 'associated_with',
            'co-occurs_with', 'affects', 'causes'
        }
        related = [r for r in related if r['rela'] in domain_specific_rela]

    # Populate associated term columns
    for i, rel in enumerate(related[:8]):
        row[f'Commonly Associated Term {i+1}'] = rel['term']

    # Source metadata
    add_source_metadata(row, 'umls')
    row['sources_contributing'] = ','.join(sorted(data.get('sources', [])))

    rows.append(row)
```

**Deduplication Check**:
- Already deduplicated in Phase 3 by term key
- Verify no duplicates before writing

**Validation**: All rows have Term + Definition populated, 26 columns each

---

### Phase 7: Write CSV and Validate (30 min)

**Script**: `scripts/import_umls_neuroscience.py` (Part 5)

**Goal**: Write final CSV and run validation suite

```python
import csv
from lib.validators import generate_validation_report, print_validation_report

# Write CSV
output_path = 'imports/umls/umls_neuroscience_imported.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=NEURODB_SCHEMA, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {output_path}")

# Validate
report = generate_validation_report(output_path)
print_validation_report(report)

if not report['overall_valid']:
    print("❌ VALIDATION FAILED - Fix errors before proceeding")
    sys.exit(1)
```

**Validation Checks** (from `lib/validators.py`):
- ✅ Exactly 26 columns per row
- ✅ UTF-8 encoding
- ✅ No duplicate terms (case-insensitive)
- ✅ Required fields populated (Term, Definition, source, source_priority, date_added)

**Expected Output**:
- `imports/umls/umls_neuroscience_imported.csv` - 100K-150K rows
- Validation: ✅ PASS

---

### Phase 8: Data Quality Profiling (30 min)

**Script**: `scripts/lib/umls_profilers.py` (additional function)

**Goal**: Generate comprehensive data quality report

```python
def generate_data_quality_report(csv_path):
    """
    Analyzes UMLS import data quality.

    Reports:
    - Definition coverage (% non-empty)
    - Synonym coverage (avg per term)
    - Abbreviation coverage (%)
    - MeSH mapping coverage (%)
    - Associated term coverage (avg per term)
    - Source vocabulary distribution
    - Top 20 most common associated terms
    """

    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)

    # Coverage metrics
    def_coverage = sum(1 for r in rows if r['Definition'].strip()) / total * 100
    mesh_coverage = sum(1 for r in rows if r['Closest MeSH term'].strip()) / total * 100
    abbrev_coverage = sum(1 for r in rows if r['Abbreviation'].strip()) / total * 100

    # Average synonyms
    syn_counts = []
    for r in rows:
        count = sum(1 for i in [1,2,3] if r[f'Synonym {i}'].strip())
        syn_counts.append(count)
    avg_synonyms = sum(syn_counts) / total

    # Average associated terms
    assoc_counts = []
    for r in rows:
        count = sum(1 for i in range(1,9) if r[f'Commonly Associated Term {i}'].strip())
        assoc_counts.append(count)
    avg_assoc = sum(assoc_counts) / total

    # Top associated terms
    assoc_terms = []
    for r in rows:
        for i in range(1, 9):
            term = r[f'Commonly Associated Term {i}'].strip()
            if term:
                assoc_terms.append(term)

    from collections import Counter
    top_assoc = Counter(assoc_terms).most_common(20)

    report = {
        'total_terms': total,
        'definition_coverage_pct': def_coverage,
        'mesh_coverage_pct': mesh_coverage,
        'abbreviation_coverage_pct': abbrev_coverage,
        'avg_synonyms_per_term': avg_synonyms,
        'avg_associated_terms_per_term': avg_assoc,
        'top_20_associated_terms': top_assoc
    }

    return report
```

**Output**: `imports/umls/data_quality_report.json`

**Thresholds**:
- Definition coverage: >80% (vs NIF's 13%)
- MeSH coverage: >60%
- Avg associated terms: >2 (if DEC-001 = domain-specific)

---

### Phase 9: Documentation (30 min)

**Goal**: Document import results and DEC-001 findings

**Files to Create/Update**:

1. **`imports/umls/UMLS_IMPORT_SUMMARY.md`**:
   ```markdown
   # UMLS Neuroscience Import Summary

   **Date**: 2025-11-20
   **Source**: UMLS Metathesaurus 2024AB
   **Total Terms**: [X]

   ## Filtering Strategy
   - Semantic types: [list]
   - Source vocabularies: MSH, SNOMEDCT_US, NCI, ...
   - Keyword matching: neuro*, brain*, ...

   ## Data Quality
   - Definition coverage: X%
   - MeSH mapping coverage: X%
   - Avg synonyms per term: X
   - Avg associated terms: X

   ## DEC-001: Relationship Quality Analysis
   - Recommendation: [USE_DIRECTLY | FILTER_BY_RELA | SMART_FILTER]
   - Domain-specific: X%
   - Generic taxonomy: X%
   - Rationale: [findings]

   ## Top 20 Associated Terms
   [list with frequencies]

   ## Comparison to NIF
   | Metric | NIF | UMLS |
   |--------|-----|------|
   | Definition coverage | 13% | X% |
   | Avg synonyms | 0.9 | X |
   | Avg associated terms | 0 | X |
   ```

2. **`docs/decisions/2025-11-20-umls-associated-terms-quality.md`**:
   - DEC-001 profiling results
   - Sample relationship analysis
   - Filtering strategy decision
   - Impact on merge phase

3. **Update `docs/decisions/ontology-import-tracker.md`**:
   - Mark UMLS as complete
   - Add data quality metrics
   - Link to summary and profiling reports

---

## Files to Create/Modify

### New Files

1. **`scripts/lib/umls_parsers.py`** (~150 lines)
   - `stream_mrsty()` - Parse semantic types
   - `stream_mrconso()` - Parse concept names
   - `stream_mrdef()` - Parse definitions
   - `stream_mrrel()` - Parse relationships

2. **`scripts/lib/umls_profilers.py`** (~200 lines)
   - `profile_relationship_quality()` - DEC-001 analysis
   - `generate_data_quality_report()` - Coverage metrics
   - `classify_relationship_type()` - Domain vs taxonomy

3. **`scripts/build_umls_filter_index.py`** (~250 lines)
   - Main: Build neuroscience CUI filter
   - Output: neuroscience_cuis.txt, filter_statistics.json

4. **`scripts/import_umls_neuroscience.py`** (~400 lines)
   - Main import pipeline (Phases 3-7)
   - Orchestrates parsing, profiling, mapping, validation

### Modified Files

5. **`scripts/lib/schema_mapper.py`**
   - Update `map_umls_to_schema()` to handle relationship filtering based on profiling

---

## Testing Strategy

### Unit Tests

1. **RRF Parsing**:
   - Test pipe-delimited parsing with edge cases (empty fields, special chars)
   - Verify UTF-8 encoding handling
   - Test streaming with large files (mock with first 10K lines)

2. **Filtering Logic**:
   - Test semantic type inclusion/exclusion
   - Test source priority deduplication
   - Test keyword matching

3. **Schema Mapping**:
   - Test all 26 columns populated correctly
   - Test synonym/abbreviation truncation (max 3, max 1)
   - Test associated term filtering

### Integration Tests

1. **End-to-End Pipeline**:
   - Run on sample dataset (1,000 CUIs)
   - Verify output CSV structure
   - Check validation passes

2. **Performance Tests**:
   - Profile memory usage during streaming
   - Verify <4GB RAM peak
   - Verify <2 hour runtime on full dataset

### Validation Tests

1. **Structural Validation**:
   - Run `lib/validators.py` suite
   - Verify 26 columns, UTF-8, no duplicates

2. **Data Quality Validation**:
   - Check definition coverage >80%
   - Check MeSH coverage >60%
   - Manually review 50 random terms

---

## Performance Considerations

### Memory Optimization

- **Stream RRF files line-by-line** - Never load full file into memory
- **Early filtering** - Apply CUI filter before building data structures
- **Lazy evaluation** - Use generators where possible
- **Batch processing** - Write intermediate results every 10K concepts

### Disk I/O Optimization

- **Cache filtered CUI set** - Load once, reuse across all RRF parsers
- **Sequential reads** - RRF files are large, avoid random seeks
- **Compression** - Consider compressing intermediate outputs if disk-limited

### Processing Time Estimates

| Phase | File Size | Rows | Est. Time |
|-------|-----------|------|-----------|
| MRSTY parsing | 40MB | 2M | 5 min |
| MRCONSO parsing | 6GB | 16M | 45 min |
| MRDEF parsing | 600MB | 1.2M | 10 min |
| MRREL parsing | 2GB | 60M | 30 min |
| Mapping + validation | - | 150K | 15 min |
| **Total** | **8.6GB** | **79M** | **~2 hours** |

---

## Security Considerations

### Data Handling

- UMLS requires license agreement - verify user has valid license
- Do not commit downloaded UMLS files to git (add to .gitignore)
- Processed CSV can be shared (derived work, educational use)

### Input Validation

- Validate RRF file structure before processing
- Sanitize pipe-delimited fields (handle escaped pipes)
- Verify UTF-8 encoding (reject malformed data)

---

## Risks & Mitigations

### Risk 1: File Size Exceeds Memory
**Impact**: Script crashes with OOM error
**Probability**: Medium (MRCONSO is 6GB)
**Mitigation**: Line-by-line streaming, early filtering, batch processing
**Fallback**: Process in chunks, write intermediate files

### Risk 2: Generic Taxonomy Relationships (DEC-001)
**Impact**: Associated terms pollute query expansion
**Probability**: Medium (NIF had this issue)
**Mitigation**: Profiling phase before full import, RELA filtering
**Fallback**: Can post-process CSV to remove generic terms

### Risk 3: Lower Than Expected Term Count
**Impact**: <80K terms extracted instead of 100K-150K
**Probability**: Low (conservative filtering)
**Mitigation**: Adjust semantic type list, add more keywords
**Fallback**: Expand to Priority 3 semantic types

### Risk 4: Duplicate Terms Across Sources
**Impact**: Same term from MSH, SNOMEDCT, NCI creates duplicates
**Probability**: High (expected behavior)
**Mitigation**: Source priority deduplication (MSH > SNOMEDCT > NCI)
**Fallback**: Post-process to merge duplicates with multi-source tracking

### Risk 5: UMLS Download Issues
**Impact**: Cannot access files due to license/download problems
**Probability**: Low (user confirmed license approved)
**Mitigation**: Verify files exist before starting
**Fallback**: Use MetamorphoSys to create subset, or defer to Day 3

---

## Success Criteria

### Minimum Viable

- ✅ 80K+ neuroscience terms extracted
- ✅ 70%+ have definitions
- ✅ 50%+ have MeSH mappings
- ✅ Structural validation passes
- ✅ DEC-001 profiling completed

### Target

- ✅ 100K-150K neuroscience terms
- ✅ 80%+ definition coverage
- ✅ 60%+ MeSH coverage
- ✅ 50%+ have associated terms (if domain-specific)
- ✅ Avg 2+ synonyms per term

### Stretch

- ✅ 150K+ terms
- ✅ 90%+ definition coverage
- ✅ 70%+ MeSH coverage
- ✅ Domain-specific associations requiring minimal filtering

---

## Next Steps After Completion

1. **Immediate** (same day):
   - Review DEC-001 profiling report
   - Decide if UMLS can proceed to merge or needs filtering
   - Update ontology import tracker

2. **Day 3** (parallel):
   - Gene Ontology import can proceed independently
   - UMLS data available for early testing in Lex Stream

3. **Day 4** (merge phase):
   - Merge UMLS + NIF using source priority
   - Populate NIF empty fields with UMLS data
   - Implement DEC-001 filtering if needed
   - Create unified neuroscience ontology

---

## Unresolved Questions

1. **UMLS File Location**: Where has user downloaded UMLS 2024AB? (Ask before starting)

2. **Relationship Filtering Threshold**: If DEC-001 shows mixed quality, what % domain-specific is acceptable? (Decide after profiling)

3. **Term Count Range**: If extraction yields 80K or 200K, should we adjust? (Validate after Phase 2)

4. **MeSH Mapping Strategy**: If UMLS MeSH coverage <60%, should we run mesh-validator agent? (Decide after data quality profiling)

5. **Associated Term Source Priority**: If term has relationships from MSH and SNOMEDCT, which to prefer? (Default: MSH, but validate during profiling)

---

## Summary

**Implementation**: 5 phases, 9 steps, 4-5 hours total
**Output**: `imports/umls/umls_neuroscience_imported.csv` (100K-150K rows)
**Critical Milestone**: DEC-001 relationship profiling determines merge strategy
**Dependencies**: User provides UMLS file location
**Blocks**: Day 4 merge algorithm
**Infrastructure**: Reuses NIF importer patterns (schema_mapper, source_tagger, validators)

**Key Innovation**: Hybrid filtering (semantic types + sources + keywords) for precision, relationship profiling for merge quality assurance.
