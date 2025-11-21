# Day 2 Implementation Plan: UMLS Metathesaurus Importer

**Date**: 2025-11-20
**Status**: Planning Phase
**Priority**: 1 (Highest - will provide 100K-150K neuroscience terms)

---

## Objectives

Create UMLS importer to extract 100K-150K neuroscience terms from UMLS Metathesaurus, filling critical gaps from NIF import (definitions, synonyms, MeSH mappings, domain-specific associated terms).

### Success Criteria
- [ ] Filter 4M+ UMLS concepts → 100K-150K neuroscience-relevant terms
- [ ] Extract comprehensive definitions (address NIF's 87% placeholder rate)
- [ ] Extract synonyms from multiple source vocabularies
- [ ] Extract MeSH mappings for all terms
- [ ] **CRITICAL**: Profile "related concepts" quality (answer DEC-001 question)
- [ ] Map to NeuroDB-2 26-column schema with source metadata
- [ ] Pass structural validation (26 columns, UTF-8, no duplicates)

---

## UMLS File Structure (Research Summary)

### Files Required

#### 1. MRCONSO.RRF (Concept Names and Sources)
**Size**: ~4M concepts, 16.4M unique concept names (2024AB release)
**Format**: Pipe-delimited (|), UTF-8
**Columns** (18 total):
```
CUI|LAT|TS|LUI|STT|SUI|ISPREF|AUI|SAUI|SCUI|SDUI|SAB|TTY|CODE|STR|SRL|SUPPRESS|CVF
```

**Key Fields for NeuroDB-2**:
- `CUI`: Concept Unique Identifier (for linking to MRDEF, MRREL)
- `SAB`: Source Abbreviation (filter: MSH=MeSH, SNOMEDCT_US, NCI, etc.)
- `TTY`: Term Type (PN=Preferred Name, SY=Synonym, AB=Abbreviation)
- `STR`: String (the actual term text)
- `SUPPRESS`: Filter out suppressed terms (keep only N)
- `LAT`: Language (filter: ENG)

#### 2. MRDEF.RRF (Definitions)
**Format**: Pipe-delimited (|), UTF-8
**Columns** (8 total):
```
CUI|AUI|ATUI|SATUI|SAB|DEF|SUPPRESS|CVF
```

**Key Fields**:
- `CUI`: Links to MRCONSO
- `DEF`: Definition text (up to 2,656 chars)
- `SAB`: Source of definition (prioritize MSH, SNOMEDCT_US, NCI)

#### 3. MRREL.RRF (Related Concepts) - **CRITICAL for DEC-001**
**Format**: Pipe-delimited (|), UTF-8
**Columns** (16 total):
```
CUI1|AUI1|STYPE1|REL|CUI2|AUI2|STYPE2|RELA|RUI|SRUI|SAB|SL|RG|DIR|SUPPRESS|CVF
```

**Key Fields**:
- `CUI1`, `CUI2`: Linked concepts
- `REL`: Relationship type (RB=Broader, RN=Narrower, RO=Other related)
- `RELA`: Specific relationship (may_treat, may_diagnose, etc.)
- `SAB`: Source of relationship

**DEC-001 Question**: Do UMLS `RELA` values provide domain-specific associations (hippocampus → memory, learning) or generic taxonomy (hippocampus → Regional part of brain)?

---

## Neuroscience Filtering Strategy

### Option A: Semantic Type Filtering (RECOMMENDED)
**File**: MRSTY.RRF (Semantic Types)
**Approach**: Filter by semantic type assignments

**Neuroscience-Relevant Semantic Types**:

**Anatomical Structures** (High priority):
- Body Part, Organ, or Organ Component (brain, nervous system)
- Cell or Molecular Dysfunction (neuronal pathology)
- Cell Component (synapses, dendrites)
- Tissue (neural tissue)

**Physiological Functions**:
- Physiologic Function (neural processing)
- Organ or Tissue Function (brain function)
- Cell Function (neuronal activity)
- Molecular Function (neurotransmitter release)
- Mental Process (cognition, memory)

**Behavioral**:
- Individual Behavior
- Social Behavior
- Mental or Behavioral Dysfunction (psychiatric disorders)

**Pathological**:
- Disease or Syndrome (neurological diseases)
- Neoplastic Process (brain tumors)
- Injury or Poisoning (traumatic brain injury)

**Chemical/Pharmacological**:
- Pharmacologic Substance (neurological drugs)
- Neuroreactive Substance or Biogenic Amine (neurotransmitters)
- Receptor (neurotransmitter receptors)

**Estimated Coverage**: 100K-200K concepts

### Option B: Source Vocabulary Filtering (SAB)
**Approach**: Filter by high-quality neuroscience sources

**Priority Sources**:
1. **MSH** (MeSH) - Medical Subject Headings (NLM's controlled vocabulary)
2. **SNOMEDCT_US** - SNOMED Clinical Terms
3. **NCI** - NCI Thesaurus (cancer + neuro-oncology)
4. **NDFRT** - National Drug File - Reference Terminology
5. **GO** - Gene Ontology (synaptic terms)
6. **HPO** - Human Phenotype Ontology
7. **OMIM** - Online Mendelian Inheritance in Man
8. **NCBI** - NCBI Taxonomy

**Estimated Coverage**: 150K-300K concepts (includes non-neuroscience)

### Option C: Hybrid Approach (RECOMMENDED)
**Combine** semantic types + SAB filtering + keyword matching

**Algorithm**:
```python
Include concept if ANY of:
1. Has neuroscience semantic type (Option A list)
2. From priority SAB (MSH, SNOMEDCT_US, NCI) AND contains neuro* keywords
3. From GO with synaptic/neural terms
```

**Estimated Coverage**: 100K-150K highly relevant concepts (target range)

**Trade-off**: More conservative (may miss rare terms) but higher precision

---

## Implementation Approach

### Phase 1: Download and Prepare (15 min)
1. Download UMLS 2024AB Full Release from https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html
2. Extract META directory (contains RRF files)
3. Locate: MRCONSO.RRF, MRDEF.RRF, MRREL.RRF, MRSTY.RRF
4. Cache locally in `imports/umls/`

### Phase 2: Build Filtering Index (30 min)
**Script**: `scripts/build_umls_filter_index.py`

1. Parse MRSTY.RRF → Build CUI → Semantic Types mapping
2. Filter concepts by semantic types (Option A)
3. Save filtered CUI list to `imports/umls/neuroscience_cuis.txt`
4. Report statistics (CUI count by semantic type)

**Output**: ~100K-200K CUIs

### Phase 3: Extract Neuroscience Terms (45 min)
**Script**: `scripts/import_umls_neuroscience.py`

1. **Load filtered CUIs** from Phase 2
2. **Parse MRCONSO.RRF** (line-by-line, memory-efficient):
   - Filter: CUI in neuroscience_cuis AND LAT=ENG AND SUPPRESS=N
   - Extract preferred terms (ISPREF=Y or TTY=PN)
   - Extract synonyms (TTY=SY, FN, etc.)
   - Extract abbreviations (TTY=AB)
   - Group by CUI
3. **Parse MRDEF.RRF**:
   - Filter: CUI in neuroscience_cuis
   - Prioritize definitions: MSH > SNOMEDCT_US > NCI > other
   - Extract best definition per CUI
4. **Parse MRREL.RRF** (**CRITICAL for DEC-001**):
   - Filter: CUI1 or CUI2 in neuroscience_cuis
   - Extract relationships: RO (other related), may_treat, may_diagnose, etc.
   - **Profile relationship types** to answer DEC-001 question
   - Limit to top 8 most specific associations per concept

**Deduplication**:
- Keep first occurrence of each unique term (case-insensitive)
- Prefer MeSH (SAB=MSH) if duplicate from multiple sources

**Output**: Dictionaries keyed by CUI:
```python
{
  'C0000000': {
    'preferred_term': str,
    'synonyms': [str, str, str],
    'abbreviations': [str],
    'definition': str,
    'definition_source': str,
    'related_concepts': [str, str, ...],
    'mesh_code': str,  # If SAB=MSH
    'sources': [str, str, ...]
  }
}
```

### Phase 4: Map to NeuroDB-2 Schema (30 min)
Reuse `lib/schema_mapper.py` from NIF importer

**Mapping**:
- `Term` ← preferred_term
- `Definition` ← definition (no placeholders!)
- `Closest MeSH term` ← mesh_code (if available)
- `Synonym 1-3` ← first 3 synonyms
- `Abbreviation` ← first abbreviation
- `Commonly Associated Term 1-8` ← related_concepts (max 8)
- `source` ← "umls"
- `source_priority` ← 1
- `sources_contributing` ← comma-separated SAB list
- `date_added` ← today

**Expected Result**: 100K-150K rows

### Phase 5: Validate and Profile (30 min)
1. **Structural validation** (reuse `lib/validators.py`)
2. **Data quality profiling**:
   - Definition coverage: % with non-empty definitions
   - Synonym coverage: avg synonyms per term
   - Abbreviation coverage: % with abbreviations
   - MeSH mapping coverage: % with MeSH codes
   - **Associated term profiling** (DEC-001):
     - Count relationships by type (RO, may_treat, etc.)
     - Sample 100 random associated terms
     - Classify: domain-specific vs. generic taxonomy
     - Report top 20 most common associated terms

### Phase 6: Write Output and Document (30 min)
1. Write CSV: `imports/umls/umls_neuroscience_imported.csv`
2. Update `docs/decisions/ontology-import-tracker.md`:
   - UMLS data quality characteristics
   - Associated term profiling results (DEC-001 answer)
   - Strengths and limitations
3. Create completion summary: `plans/2025-11-20-day2-umls-completion-summary.md`

**Total Estimated Time**: ~3 hours

---

## Critical Questions to Answer

### 1. DEC-001: UMLS Associated Concepts Quality
**Question**: Do UMLS MRREL relationships provide domain-specific associations or generic taxonomy?

**Test**: Sample 100 random concepts, inspect `RELA` values and related concept strings

**Possible Outcomes**:
- ✅ **Domain-specific** (e.g., hippocampus → memory, Alzheimer's disease, learning) → Use directly
- ❌ **Generic taxonomy** (e.g., hippocampus → Body Part, Organ Component) → Apply DEC-001 Option C filtering
- ⚠️ **Mixed quality** → Implement smart filtering by relationship type

### 2. Definition Coverage
**Question**: What % of neuroscience concepts have definitions in UMLS?

**Hypothesis**: 80-90% (much better than NIF's 13%)

**Impact**: If <70%, may need to keep NIF placeholder definitions

### 3. MeSH Mapping Coverage
**Question**: What % of terms have MeSH codes?

**Hypothesis**: 60-80% (MeSH is major UMLS source)

**Impact**: If low, may need mesh-validator agent during merge phase

### 4. Term Count Accuracy
**Question**: Will filtering yield 100K-150K or different range?

**Impact on Plan**: If <80K, expand semantic types; if >200K, add stricter filtering

---

## Risk Mitigation

### Risk 1: File Size (MRCONSO.RRF ~6GB uncompressed)
**Mitigation**: Line-by-line streaming, filter early, don't load entire file

### Risk 2: Memory Usage (4M concepts)
**Mitigation**: Process in batches, write intermediate results, use generators

### Risk 3: Generic Taxonomy (DEC-001 repeat)
**Mitigation**: Profile first 1,000 concepts before full import, implement filtering if needed

### Risk 4: Duplicate Terms Across Sources
**Mitigation**: Deduplication with source priority (MSH > SNOMEDCT_US > NCI > other)

### Risk 5: Download/License Issues
**Mitigation**: User confirmed license approval; fallback to MetamorphoSys subset if full download fails

---

## Next Steps

1. **Confirm download access**: Ask user where UMLS files are located or if download needed
2. **Choose filtering strategy**: Recommend Option C (Hybrid) for precision
3. **Build index script**: Start with Phase 2 (filter CUIs by semantic types)
4. **Profile sample data**: Test on 1,000 concepts before full import
5. **Implement full importer**: Only after sample profiling confirms approach

---

## Dependencies

**Blocked By**: None (license approved)
**Blocks**:
- Day 3: Gene Ontology import (could proceed in parallel)
- Day 4: Merge algorithm (needs UMLS baseline)

**Infrastructure Reuse**:
- ✅ `lib/schema_mapper.py` (NeuroDB-2 schema)
- ✅ `lib/source_tagger.py` (source metadata)
- ✅ `lib/validators.py` (structural validation)

---

**Status**: Ready to implement after user confirms UMLS file location
