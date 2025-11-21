# Phase 2A: Schema Mapping Log

**Date**: 2025-11-21
**Script**: `scripts/map_umls_to_schema.py`
**Input**: `imports/umls/umls_concepts_intermediate.json` + `imports/umls/umls_associations.json`
**Output**: `imports/umls/umls_neuroscience_imported.csv`

---

## Execution Steps

### Step 1: Load Intermediate Data
✅ Loaded **325,241** concepts from `umls_concepts_intermediate.json`
✅ Loaded **294,008** association sets from `umls_associations.json`

### Step 2: Map to NeuroDB-2 Schema
🗺️ Mapping **325,241** concepts to 26-column format...

**Schema Mapping**:
- `Term` ← preferred_term
- `Definition` ← definition
- `Closest MeSH term` ← mesh_code
- `Synonym 1-3` ← synonyms (first 3)
- `Abbreviation` ← abbreviations (comma-separated)
- `Commonly Associated Term 1-8` ← related_concepts (first 8)
- `Source CUI` ← cui (metadata)
- `Source SAB` ← sources (metadata)

✅ Mapped **325,241** rows

### Step 3: Write CSV Output
💾 Writing **325,241** rows to `umls_neuroscience_imported.csv`...
✅ Wrote CSV with 26 columns

---

## Coverage Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total terms** | 325,241 | 100.0% |
| **Definitions** | 79,617 | 24.5% |
| **MeSH codes** | 13,739 | 4.2% |
| **Synonyms** | 32,477 | **10.0%** ⬆️ |
| **Abbreviations** | 1,541 | **0.5%** ⬆️ |
| **Associated terms** | 294,008 | 90.4% |

**Key Improvement**: Phase 2A expanded synonym/abbreviation coverage through TTY type expansion.

---

## Schema Details

**Format**: 26-column CSV
**Standard columns**: 22 (Term, Definition, MeSH, Synonyms, Abbreviations, Word Forms, Associated Terms, etc.)
**Metadata columns**: 4 (Source CUI, Source SAB, Data Source, Import Date)

**Validation**: Ready for merge with OLD enriched data

---

**Processing Time**: ~5 seconds
**Status**: ✅ **SUCCESS**
