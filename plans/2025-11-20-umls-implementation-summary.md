# UMLS Importer Implementation - Executive Summary

**Plan File**: `/Users/sam/NeuroDB-2/plans/2025-11-20-umls-importer-implementation-plan.md`
**Status**: Ready for implementation (awaiting UMLS file location)
**Estimated Duration**: 4-5 hours
**Priority**: P1 (Critical)

---

## Objectives

Extract 100K-150K neuroscience terms from UMLS Metathesaurus (4M concepts) to:
1. Fill NIF gaps (87% lacked definitions)
2. Provide MeSH mappings (60%+ coverage expected)
3. Add domain-specific associations (if DEC-001 profiling shows quality)
4. Expand synonym coverage

---

## Implementation Phases

### Phase 1: Setup (30 min)
- Verify UMLS files: MRCONSO.RRF (6GB), MRDEF.RRF (600MB), MRREL.RRF (2GB), MRSTY.RRF (40MB)
- Create directory structure: `imports/umls/`, `downloads/umls/2024AB/META/`

### Phase 2: Build Neuroscience Filter (45 min)
**Script**: `build_umls_filter_index.py`
- Parse MRSTY.RRF for semantic types
- **Hybrid filtering**: Semantic types + source vocabularies (MSH, SNOMEDCT_US, NCI) + neuro keywords
- Output: `neuroscience_cuis.txt` (100K-150K CUIs)

**Neuroscience Semantic Types**:
- Anatomical: Body Part/Organ, Cell Component, Tissue
- Physiological: Mental Process, Organ Function, Neural Activity
- Pathological: Disease/Syndrome, Mental Dysfunction
- Chemical: Pharmacologic Substance, Neurotransmitters, Receptors

### Phase 3: Extract Terms (60 min)
**Script**: `import_umls_neuroscience.py` (Part 1)
- Stream MRCONSO.RRF line-by-line (6GB - DO NOT load into memory)
- Filter: CUI in neuroscience set, LAT=ENG, SUPPRESS=N
- Extract: Preferred terms, synonyms (max 3), abbreviations, MeSH codes
- Deduplicate: Source priority MSH > SNOMEDCT_US > NCI

### Phase 4: Extract Definitions (30 min)
**Script**: `import_umls_neuroscience.py` (Part 2)
- Stream MRDEF.RRF (600MB)
- Prioritize: MSH > SNOMEDCT_US > NCI definitions
- Target: 80%+ coverage (vs NIF's 13%)

### Phase 5: Extract & Profile Relationships ⚠️ CRITICAL (90 min)
**Script**: `import_umls_neuroscience.py` (Part 3) + `umls_profilers.py`
- Stream MRREL.RRF (2GB)
- Extract related concepts (max 8 per term)
- **DEC-001 Profiling**: Sample 1000 relationships, classify:
  - Domain-specific: hippocampus → memory, Alzheimer's (GOOD for query expansion)
  - Generic taxonomy: hippocampus → Body Part (BAD - same issue as NIF)
- Generate profiling report with filtering recommendations

**DEC-001 Decision Tree**:
- If >60% domain-specific → Use relationships directly
- If >60% generic taxonomy → Filter by RELA whitelist (may_treat, associated_with, affects)
- If mixed → Smart filtering with relationship type priority

### Phase 6: Map to Schema (45 min)
**Script**: `import_umls_neuroscience.py` (Part 4)
- Reuse `lib/schema_mapper.map_umls_to_schema()`
- Apply DEC-001 filtering if needed
- Add source metadata: source='umls', priority=1

### Phase 7: Validate (30 min)
**Script**: `import_umls_neuroscience.py` (Part 5)
- Write CSV: `imports/umls/umls_neuroscience_imported.csv`
- Run `lib/validators.py`: 26 columns, UTF-8, no duplicates, required fields

### Phase 8: Data Quality Profiling (30 min)
**Script**: `umls_profilers.py`
- Definition coverage (target: >80%)
- MeSH coverage (target: >60%)
- Avg synonyms per term
- Top 20 associated terms (identify any generic terms)

### Phase 9: Documentation (30 min)
- `imports/umls/UMLS_IMPORT_SUMMARY.md`
- `docs/decisions/2025-11-20-umls-associated-terms-quality.md` (DEC-001 findings)
- Update `docs/decisions/ontology-import-tracker.md`

---

## Key Technical Details

### Memory Efficiency (Critical)
- **Stream RRF files line-by-line** - Never load 6GB into memory
- **Early filtering** - Apply CUI whitelist before building data structures
- **Peak RAM**: <4GB (tested with NIF importer pattern)

### Filtering Strategy (Hybrid)
```python
Include CUI if:
  - Has Priority 1 semantic type (anatomy, physiology, pathology), OR
  - Has Priority 2 semantic type AND (from MSH/SNOMEDCT/NCI OR contains neuro keyword), OR
  - Has Priority 3 semantic type AND from MSH AND contains neuro keyword
```

### Deduplication Priority
Same term from multiple sources → Keep MSH > SNOMEDCT_US > NCI > other

### Relationship Quality Profiling (DEC-001)
```python
# Classify RELA values
Domain-specific: may_treat, may_diagnose, associated_with, affects, causes
Generic taxonomy: isa, part_of, has_part, component_of

# Sample 1000 relationships, report distribution
# Decide filtering strategy: USE_DIRECTLY | FILTER_BY_RELA | SMART_FILTER
```

---

## Scripts to Create

1. **`scripts/lib/umls_parsers.py`** (~150 lines)
   - RRF file streaming utilities
   - Pipe-delimited parsing with UTF-8 support

2. **`scripts/lib/umls_profilers.py`** (~200 lines)
   - Relationship quality analysis (DEC-001)
   - Data coverage metrics

3. **`scripts/build_umls_filter_index.py`** (~250 lines)
   - Semantic type filtering
   - Output: neuroscience_cuis.txt

4. **`scripts/import_umls_neuroscience.py`** (~400 lines)
   - Main pipeline: parse → profile → map → validate

---

## Success Criteria

**Minimum Viable**:
- 80K+ terms, 70%+ definitions, 50%+ MeSH, DEC-001 profiling complete

**Target**:
- 100K-150K terms, 80%+ definitions, 60%+ MeSH, 2+ avg synonyms

**Stretch**:
- 150K+ terms, 90%+ definitions, 70%+ MeSH, domain-specific associations

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Memory overflow (6GB file) | Script crash | Line-by-line streaming, early filtering |
| Generic relationships (DEC-001) | Query pollution | Profiling phase, RELA filtering |
| Low term count (<80K) | Incomplete coverage | Expand semantic types, adjust filters |
| Duplicate terms | Data inconsistency | Source priority deduplication |

---

## Comparison to NIF Import

| Metric | NIF | UMLS (Expected) |
|--------|-----|-----------------|
| Total terms | 1,636 | 100K-150K |
| Definition coverage | 13% | 80%+ |
| Avg synonyms | 0.9 | 2+ |
| Avg associated terms | 0 | 2-4 (if domain-specific) |
| MeSH coverage | 0% | 60%+ |

---

## Next Steps

1. **Ask user**: Where are UMLS 2024AB files located?
2. **Verify files**: Check sizes match expected ranges
3. **Start Phase 2**: Build neuroscience CUI filter
4. **Profile sample**: Test first 1K concepts before full import
5. **Implement full pipeline**: Only after sample validation

---

## Unresolved Questions

1. UMLS file location? (Ask user)
2. If DEC-001 shows mixed quality, what threshold for domain-specific %? (Decide after profiling)
3. If term count is 80K or 200K, adjust filters? (Validate after Phase 2)
4. If MeSH coverage <60%, run mesh-validator agent? (Decide after data profiling)

---

## Blockers

**Immediate**: Need UMLS file location from user
**Downstream**: Day 4 merge algorithm depends on DEC-001 profiling results

---

**Prepared by**: Planner agent
**Date**: 2025-11-20
**Full Plan**: `/Users/sam/NeuroDB-2/plans/2025-11-20-umls-importer-implementation-plan.md` (56KB, 900+ lines)
