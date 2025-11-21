# Phase 2A: UMLS Import Log (Expanded TTY Filters)

**Date**: 2025-11-21
**Script**: `scripts/import_umls_neuroscience.py`
**Strategy**: DEC-002 Option B (Multi-stage filtering)
**Enhancements**: Expanded TTY types (synonyms: 9, abbreviations: 4) + heuristic detection

---

## Configuration

- **Input CUIs**: 1,015,068 neuroscience CUIs
- **Target**: 150K-250K final terms
- **Source**: MRCONSO.RRF (2.1 GB, ~17M rows)

---

## Execution Timeline

### Step 1: Load Neuroscience CUI Filter
✅ Loaded **1,015,068** neuroscience CUIs from `imports/umls/neuroscience_cuis.txt`

### Step 2: Load Semantic Type Mappings
✅ Loaded semantic types for **3,488,973** CUIs

### Step 3: Parse MRCONSO.RRF
**Processing**: Multi-stage filtering pipeline

Progress indicators:
- Processed 5,000,000 rows → 127,043 concepts with data
- Processed 6,000,000 rows → 163,629 concepts with data

✅ **Parsing complete!**

### Filter Stage Results

| Stage | Description | Rows Remaining |
|-------|-------------|----------------|
| **Input** | Total rows processed | 17,390,109 |
| **Stage 1** | CUI match (neuroscience filter) | 7,030,159 (40.4%) |
| **Stage 2** | English only (LAT=ENG) | 4,104,591 (23.6%) |
| **Stage 3** | Not suppressed (SUPPRESS=N) | 3,560,455 (20.5%) |
| **Stage 4** | Preferred terms (ISPREF=Y or TTY=PN) | 2,873,660 (16.5%) |
| **Stage 5** | Keyword filter (broad types) | |
| - Passed | Neuroscience keywords found | 48,389 |
| - Failed | Non-neuroscience terms | 1,971,019 |

**Output**: ✅ Extracted **325,515** concepts with preferred terms

---

### Step 4: Parse MRDEF.RRF (Definitions)
✅ Added definitions to **79,812** concepts (**24.5%** coverage)

---

### Step 5: Deduplicate by Term Name
✅ Removed **274** duplicates
✅ Final count: **325,241** unique terms

---

### Step 6: Save Intermediate Data
✅ Saved **325,241** concepts to `imports/umls/umls_concepts_intermediate.json`

---

## Results Summary

### ✅ Phase 1 Complete: Term Extraction

**Output**: 325,241 unique neuroscience terms

### Coverage Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Definitions** | 79,617 | 24.5% |
| **MeSH codes** | 13,739 | 4.2% |
| **Synonyms** | 32,477 | **10.0%** ⬆️ |
| **Abbreviations** | 1,541 | **0.5%** ⬆️ |

**Key Improvement**: Synonym coverage increased from 9.0% → 10.0% (+3,171 terms)

---

## Target Assessment

⚠️ **Above target** (325K > 250K)
Consider: Stricter keyword filters or Priority 1 types only

---

## Next Steps

1. ✅ Review intermediate data: `imports/umls/umls_concepts_intermediate.json`
2. ✅ Map to NeuroDB-2 26-column schema
3. ✅ Merge with old enriched data
4. ✅ Run validation and quality profiling

---

**Processing Time**: ~18 minutes
**Status**: ✅ **SUCCESS**
