# UMLS Importer Quick Reference

**Full Plan**: `plans/2025-11-20-umls-importer-implementation-plan.md`
**Summary**: `plans/2025-11-20-umls-implementation-summary.md`
**Data Flow**: `plans/diagrams/umls-data-flow.md`

---

## Prerequisites Checklist

- [ ] UMLS 2024AB license approved (user confirmed)
- [ ] UMLS files downloaded and extracted
- [ ] Verify files exist:
  - `downloads/umls/2024AB/META/MRCONSO.RRF` (~6GB)
  - `downloads/umls/2024AB/META/MRDEF.RRF` (~600MB)
  - `downloads/umls/2024AB/META/MRREL.RRF` (~2GB)
  - `downloads/umls/2024AB/META/MRSTY.RRF` (~40MB)

---

## Script Execution Order

```bash
# Phase 2: Build neuroscience CUI filter (45 min)
python3 scripts/build_umls_filter_index.py
# Output: imports/umls/neuroscience_cuis.txt (100K-150K CUIs)

# Phase 3-7: Main import pipeline (3 hours)
python3 scripts/import_umls_neuroscience.py
# Output: imports/umls/umls_neuroscience_imported.csv

# Expected completion: 4-5 hours total
```

---

## Key Configuration Values

### Neuroscience Semantic Type Codes (MRSTY.RRF)

**Priority 1** (Always include):
- `T023` - Body Part, Organ, or Organ Component
- `T025` - Cell
- `T026` - Cell Component
- `T029` - Body Location or Region
- `T039` - Physiologic Function
- `T041` - Mental Process
- `T047` - Disease or Syndrome
- `T046` - Pathologic Function
- `T121` - Pharmacologic Substance

**Priority 2** (Include if MSH/SNOMEDCT/NCI OR neuro keyword):
- `T048` - Mental or Behavioral Dysfunction
- `T053` - Behavior
- `T123` - Biologically Active Substance
- `T192` - Receptor

**Priority 3** (Include if MSH AND neuro keyword):
- `T060` - Diagnostic Procedure
- `T061` - Therapeutic Procedure

### Source Priority (for deduplication)

1. MSH (MeSH) - Highest
2. SNOMEDCT_US
3. NCI
4. Other sources

### Relationship Types (DEC-001)

**Domain-Specific** (KEEP):
- `may_treat`, `may_diagnose`, `may_prevent`, `may_cause`
- `associated_with`, `co-occurs_with`, `affects`
- `interacts_with`, `stimulates`, `inhibits`

**Generic Taxonomy** (FILTER OUT):
- `isa`, `inverse_isa`
- `part_of`, `has_part`
- `component_of`, `has_component`

---

## Critical Thresholds

| Metric | Minimum | Target | Stretch |
|--------|---------|--------|---------|
| Total terms | 80K | 100K-150K | 150K+ |
| Definition coverage | 70% | 80% | 90% |
| MeSH coverage | 50% | 60% | 70% |
| Avg synonyms | 1.5 | 2+ | 3+ |
| Domain-specific % (DEC-001) | 50% | 60% | 80% |

**Red Flags**:
- Total terms <80K → Expand semantic types
- Definition coverage <70% → Keep NIF placeholders
- Domain-specific <50% → Apply RELA filtering
- Generic taxonomy >60% → Same issue as NIF, need smart filtering

---

## File Formats (RRF)

### MRCONSO.RRF (18 columns, pipe-delimited)
```
CUI|LAT|TS|LUI|STT|SUI|ISPREF|AUI|SAUI|SCUI|SDUI|SAB|TTY|CODE|STR|SRL|SUPPRESS|CVF
```
**Key**: CUI (0), LAT (1), SAB (11), TTY (12), STR (14), SUPPRESS (16)

### MRDEF.RRF (8 columns)
```
CUI|AUI|ATUI|SATUI|SAB|DEF|SUPPRESS|CVF
```
**Key**: CUI (0), SAB (4), DEF (5), SUPPRESS (6)

### MRREL.RRF (16 columns)
```
CUI1|AUI1|STYPE1|REL|CUI2|AUI2|STYPE2|RELA|RUI|SRUI|SAB|SL|RG|DIR|SUPPRESS|CVF
```
**Key**: CUI1 (0), REL (3), CUI2 (4), RELA (7), SAB (10), SUPPRESS (14)

### MRSTY.RRF (6 columns)
```
CUI|TUI|STN|STY|ATUI|CVF
```
**Key**: CUI (0), TUI (1)

---

## Common Pitfalls

### Memory Issues
❌ **DON'T**: Load entire RRF file into memory
```python
with open('MRCONSO.RRF') as f:
    rows = f.readlines()  # ❌ 6GB into RAM
```

✅ **DO**: Stream line-by-line
```python
with open('MRCONSO.RRF') as f:
    for line in f:  # ✅ Stream
        process(line)
```

### Early Filtering
❌ **DON'T**: Filter after parsing
```python
all_concepts = parse_all()  # ❌ 16M concepts
filtered = [c for c in all_concepts if c.cui in neuro_cuis]
```

✅ **DO**: Filter during parsing
```python
for line in f:
    cui = line.split('|')[0]
    if cui not in neuro_cuis:  # ✅ Early exit
        continue
    process(line)
```

### Duplicate Handling
❌ **DON'T**: Keep all duplicates
```python
concepts[cui] = data  # ❌ Overwrites
```

✅ **DO**: Compare source priority
```python
if cui not in concepts or has_higher_priority(data):
    concepts[cui] = data  # ✅ Keep best
```

---

## DEC-001 Decision Tree

```
Sample 1000 relationships from MRREL.RRF
    ↓
Classify by RELA type
    ↓
Calculate % domain-specific vs % generic taxonomy
    ↓
    ├─ >60% domain-specific
    │   → Recommendation: USE_DIRECTLY
    │   → No filtering needed
    │
    ├─ >60% generic taxonomy
    │   → Recommendation: FILTER_BY_RELA
    │   → Whitelist: may_treat, associated_with, affects, etc.
    │
    └─ Mixed (40-60% each)
        → Recommendation: SMART_FILTER
        → Priority: Domain-specific RELA > REL=RO > Other
```

---

## Validation Checklist

### Structural (lib/validators.py)
- [ ] Exactly 26 columns per row
- [ ] UTF-8 encoding (no decoding errors)
- [ ] No duplicate terms (case-insensitive)
- [ ] Required fields populated: Term, Definition, source, source_priority, date_added

### Data Quality (lib/umls_profilers.py)
- [ ] Definition coverage >80%
- [ ] MeSH coverage >60%
- [ ] Avg synonyms >2
- [ ] Top 20 associated terms reviewed (no "Regional part of brain" type generics)

### DEC-001 Profiling
- [ ] Relationship profiling report generated
- [ ] 1000 sample relationships classified
- [ ] Recommendation documented
- [ ] Filtering strategy applied if needed

---

## Output Files

### Primary Output
- `imports/umls/umls_neuroscience_imported.csv` (100K-150K rows, 26 columns)

### Intermediate Files
- `imports/umls/neuroscience_cuis.txt` (CUI filter)
- `imports/umls/filter_statistics.json` (filtering metrics)

### Profiling Reports
- `imports/umls/relationship_profiling_report.json` (DEC-001 analysis)
- `imports/umls/relationship_samples.csv` (1000 samples for review)
- `imports/umls/data_quality_report.json` (coverage metrics)

### Documentation
- `imports/umls/UMLS_IMPORT_SUMMARY.md` (human-readable summary)
- `docs/decisions/2025-11-20-umls-associated-terms-quality.md` (DEC-001 findings)

---

## Troubleshooting

### Problem: Term count <80K
**Cause**: Filtering too aggressive
**Solution**: Expand Priority 2/3 semantic types, add more keywords

### Problem: Term count >200K
**Cause**: Filtering too loose
**Solution**: Stricter semantic type priorities, require MSH for Priority 3

### Problem: Definition coverage <70%
**Cause**: Many concepts lack definitions in UMLS
**Solution**: Keep NIF placeholders for merge phase

### Problem: High generic taxonomy % (DEC-001)
**Cause**: Same issue as NIF (RDF hierarchy vs domain associations)
**Solution**: Apply RELA whitelist filtering

### Problem: Memory overflow
**Cause**: Not streaming properly
**Solution**: Check for `readlines()`, use generators, write batches

---

## Quick Commands

```bash
# Check file sizes
ls -lh downloads/umls/2024AB/META/*.RRF

# Count lines in RRF files
wc -l downloads/umls/2024AB/META/MRCONSO.RRF

# Preview first 5 rows
head -5 downloads/umls/2024AB/META/MRCONSO.RRF

# Count filtered CUIs
wc -l imports/umls/neuroscience_cuis.txt

# Check CSV structure
head -2 imports/umls/umls_neuroscience_imported.csv | python3 -c "import sys; print(len(sys.stdin.readline().split(',')))"

# Validate UTF-8
file imports/umls/umls_neuroscience_imported.csv

# Check for duplicates
cut -d',' -f1 imports/umls/umls_neuroscience_imported.csv | sort | uniq -d
```

---

## Time Estimates by Phase

| Phase | Task | Est. Time |
|-------|------|-----------|
| 1 | Setup & verify files | 30 min |
| 2 | Build CUI filter (MRSTY) | 45 min |
| 3 | Extract terms (MRCONSO) | 60 min |
| 4 | Extract definitions (MRDEF) | 30 min |
| 5 | Extract & profile relationships (MRREL) | 90 min |
| 6 | Map to schema | 45 min |
| 7 | Write & validate CSV | 30 min |
| 8 | Data quality profiling | 30 min |
| 9 | Documentation | 30 min |
| **Total** | | **~5 hours** |

**Note**: First run may take longer (learning curve), subsequent runs faster

---

## Success Indicators

✅ **Ready for merge if**:
- CSV validates (26 columns, UTF-8, no duplicates)
- 100K-150K terms extracted
- 80%+ have definitions
- 60%+ have MeSH mappings
- DEC-001 profiling complete with recommendation
- Top 20 associated terms look domain-specific (not "Body Part", "Regional part of brain")

⚠️ **Needs review if**:
- Term count outside 80K-200K range
- Definition coverage <70%
- MeSH coverage <50%
- DEC-001 shows >60% generic taxonomy (apply filtering)

❌ **Blocker if**:
- Validation fails (structural errors)
- Files not readable (encoding issues)
- Memory overflow (streaming not working)
- Term count <50K (filtering broken)

---

**Last Updated**: 2025-11-20
**Author**: Planner agent
**Status**: Ready for implementation
