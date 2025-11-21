# UMLS Phase 2A: Synonym & Abbreviation Expansion Plan

**Date:** 2025-11-21
**Priority:** HIGH
**Estimated Time:** 2-3 hours
**Target:** Synonym coverage 9% → 50-70%, Abbreviation coverage 0.4% → 20-30%

---

## Overview

Expand TTY type filtering in MRCONSO parsing to capture 6x-15x more synonyms and 5x-10x more abbreviations. Current extraction limited to 3 synonym types (SY, FN, MTH_FN) and 2 abbreviation types (AB, ACR). Expansion adds 6 synonym types and 2 abbreviation types plus heuristic detection.

**Critical Constraint:** Must preserve existing enriched data (definitions, associated terms, MeSH codes from prior processing).

---

## Current State Analysis

**File:** `scripts/import_umls_neuroscience.py` (432 lines)
**Database:** `imports/umls/umls_neuroscience_terms.csv` (325,241 rows, 26 columns)
**Source Data:** `downloads/umls/2025AB/2025AB/META/MRCONSO.RRF` (2.1 GB, ~17M rows)
**Reusable Filter:** `imports/umls/neuroscience_cuis.txt` (1,015,068 CUIs)

**Current TTY Extraction (Lines 207-215):**
```python
# Extract synonyms
elif tty in ['SY', 'FN', 'MTH_FN']:
    if term_str and term_str not in concepts[cui]['synonyms']:
        concepts[cui]['synonyms'].append(term_str)

# Extract abbreviations
elif tty in ['AB', 'ACR']:
    if term_str and term_str not in concepts[cui]['abbreviations']:
        concepts[cui]['abbreviations'].append(term_str)
```

**Current Coverage:**
- Synonyms: 29,306 terms (9.0%)
- Abbreviations: 1,208 terms (0.4%)

---

## Requirements

### Functional Requirements
1. Expand synonym TTY types: add SYN, ET, ETCF, ETCLIN, XM, XQ
2. Expand abbreviation TTY types: add AA, SYGB
3. Add heuristic abbreviation detection (all-caps, 2-10 chars, not common words)
4. Preserve existing data from `umls_neuroscience_terms.csv` (columns: Definition, Associated Terms 1-8, MeSH code)
5. Maintain 26-column schema compliance
6. Pass structural validation (0 errors)

### Non-Functional Requirements
1. Avoid re-parsing MRDEF/MRREL (reuse existing definitions/associations)
2. Runtime < 30 minutes for MRCONSO re-parsing
3. Zero data loss on merge
4. Rollback capability if issues detected

---

## Architecture

### Data Flow

```
Stage 1: MRCONSO Re-parsing (Modified TTY Filters)
    ↓
neuroscience_cuis.txt (reuse) → parse_mrconso() → NEW synonym/abbreviation extracts
    ↓
Stage 2: CSV Merge Strategy
    ↓
OLD umls_neuroscience_terms.csv + NEW synonyms/abbreviations → MERGED output
    ↓
Stage 3: Validation
    ↓
Structural validation → Coverage metrics → Integration test with Lex Stream
```

### File Operations

**Inputs:**
- `imports/umls/neuroscience_cuis.txt` (reuse existing filter)
- `downloads/umls/2025AB/2025AB/META/MRCONSO.RRF` (re-parse with new TTY filters)
- `imports/umls/umls_neuroscience_terms.csv` (existing enriched data)

**Outputs:**
- `imports/umls/umls_neuroscience_terms_NEW.csv` (expanded synonyms/abbreviations)
- `imports/umls/umls_neuroscience_terms.csv.backup_20251121` (timestamped backup)

---

## Implementation Steps

### Step 1: Backup Existing Data
**Time:** 1 minute

```bash
# Create timestamped backup
cp imports/umls/umls_neuroscience_terms.csv \
   imports/umls/umls_neuroscience_terms.csv.backup_20251121
```

**Validation:**
- Verify backup file exists
- Confirm row count matches original (325,241 rows)

---

### Step 2: Modify TTY Extraction Logic
**Time:** 15 minutes
**File:** `scripts/import_umls_neuroscience.py`

#### Code Change 1: Expand Synonym TTY Types (Lines 207-210)

**BEFORE:**
```python
# Extract synonyms
elif tty in ['SY', 'FN', 'MTH_FN']:
    if term_str and term_str not in concepts[cui]['synonyms']:
        concepts[cui]['synonyms'].append(term_str)
```

**AFTER:**
```python
# Extract synonyms (expanded from 3 to 9 TTY types)
elif tty in ['SY', 'FN', 'MTH_FN', 'SYN', 'ET', 'ETCF', 'ETCLIN', 'XM', 'XQ']:
    if term_str and term_str not in concepts[cui]['synonyms']:
        concepts[cui]['synonyms'].append(term_str)
```

**Rationale:**
- SYN: Designated synonym (UMLS official)
- ET: Entry term (MeSH vocabulary)
- ETCF: Entry term, consumer-friendly (MeSH)
- ETCLIN: Entry term, clinician-preferred (MeSH)
- XM: Cross-mapping term
- XQ: Alternate name (query expansion)

---

#### Code Change 2: Expand Abbreviation TTY Types + Heuristics (Lines 212-215)

**BEFORE:**
```python
# Extract abbreviations
elif tty in ['AB', 'ACR']:
    if term_str and term_str not in concepts[cui]['abbreviations']:
        concepts[cui]['abbreviations'].append(term_str)
```

**AFTER:**
```python
# Extract abbreviations (expanded from 2 to 4 TTY types + heuristic)
elif tty in ['AB', 'ACR', 'AA', 'SYGB']:
    if term_str and term_str not in concepts[cui]['abbreviations']:
        concepts[cui]['abbreviations'].append(term_str)

# Heuristic abbreviation detection (all-caps, 2-10 chars, not common words)
elif is_potential_abbreviation(term_str):
    if term_str not in concepts[cui]['abbreviations']:
        concepts[cui]['abbreviations'].append(term_str)
```

**Rationale:**
- AA: Attribute name abbreviation
- SYGB: Gene symbol synonym

---

#### Code Change 3: Add Abbreviation Heuristic Function (After Line 116)

**INSERT AFTER `contains_neuro_keyword()` function:**

```python
# Common words to exclude from abbreviation detection
COMMON_WORDS = {
    'A', 'AN', 'THE', 'IS', 'ARE', 'WAS', 'WERE', 'BE', 'BEEN', 'BEING',
    'HAVE', 'HAS', 'HAD', 'DO', 'DOES', 'DID', 'WILL', 'WOULD', 'COULD',
    'SHOULD', 'MAY', 'MIGHT', 'CAN', 'OF', 'IN', 'TO', 'FOR', 'WITH',
    'ON', 'AT', 'BY', 'FROM', 'UP', 'OUT', 'IF', 'NO', 'NOT', 'AS', 'OR'
}

def is_potential_abbreviation(term_str):
    """
    Heuristic detection for abbreviations:
    - All uppercase letters (allows numbers, hyphens)
    - Length 2-10 characters
    - Not a common English word
    - Not purely numeric
    """
    if not term_str:
        return False

    # Check length
    if len(term_str) < 2 or len(term_str) > 10:
        return False

    # Check if all-caps (allows numbers, hyphens, underscores)
    clean_term = term_str.replace('-', '').replace('_', '').replace(' ', '')
    if not clean_term.isupper():
        return False

    # Check if purely alphabetic portion exists
    alpha_chars = ''.join(c for c in clean_term if c.isalpha())
    if not alpha_chars:
        return False  # Purely numeric

    # Exclude common words
    if alpha_chars in COMMON_WORDS:
        return False

    return True
```

**Location:** Insert after line 116 (`contains_neuro_keyword()` function)

---

### Step 3: Re-parse MRCONSO with New Filters
**Time:** 20-30 minutes (depends on system performance)

**Command:**
```bash
cd /Users/sam/NeuroDB-2
python3 scripts/import_umls_neuroscience.py
```

**Expected Output:**
- Intermediate file: `imports/umls/umls_concepts_intermediate.json` (updated)
- Processing time: ~20-30 minutes for 17M MRCONSO rows
- Console output: Filter stage statistics

**Note:** This re-runs entire pipeline (Stages 1-5) but reuses existing `neuroscience_cuis.txt` filter.

---

### Step 4: Create Merge Script
**Time:** 20 minutes
**File:** `scripts/merge_umls_enrichments.py` (NEW FILE, ~120 lines)

**Purpose:** Merge NEW synonym/abbreviation data with EXISTING enriched data.

**Logic:**
1. Load OLD CSV (325,241 rows with definitions, associations, MeSH codes)
2. Load NEW intermediate JSON (325K+ concepts with expanded synonyms/abbreviations)
3. For each term in OLD CSV:
   - Preserve: Definition, Associated Terms 1-8, MeSH code, Date Added, Source metadata
   - Replace: Synonym 1-3, Abbreviation (from NEW data)
4. Write merged CSV to `umls_neuroscience_terms_NEW.csv`

**Merge Strategy (Column Mapping):**

| Column | Strategy | Source |
|--------|----------|--------|
| Term, Term Two | Preserve | OLD CSV |
| Definition | Preserve | OLD CSV |
| Closest MeSH term | Preserve | OLD CSV |
| Synonym 1-3 | Replace | NEW JSON (expanded) |
| Abbreviation | Replace | NEW JSON (expanded) |
| UK/US Spelling | Preserve | OLD CSV |
| Word Forms (Noun/Verb/Adj/Adv) | Preserve | OLD CSV |
| Associated Terms 1-8 | Preserve | OLD CSV |
| Source metadata | Preserve | OLD CSV |

**Script Skeleton:**

```python
#!/usr/bin/env python3
"""
Merge UMLS Synonym/Abbreviation Enrichments

Combines NEW synonym/abbreviation extracts with EXISTING enriched data.
Preserves definitions, associated terms, MeSH codes.
"""

import csv
import json
from pathlib import Path

OLD_CSV = Path("imports/umls/umls_neuroscience_terms.csv")
NEW_JSON = Path("imports/umls/umls_concepts_intermediate.json")
OUTPUT_CSV = Path("imports/umls/umls_neuroscience_terms_NEW.csv")

def load_old_data():
    """Load existing enriched data."""
    old_data = {}
    with open(OLD_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            term = row['Term']
            old_data[term] = row
    print(f"Loaded {len(old_data):,} rows from OLD CSV")
    return old_data

def load_new_synonyms_abbreviations():
    """Load NEW synonym/abbreviation data."""
    with open(NEW_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    new_data = {}
    for cui, concept in data.items():
        term = concept.get('preferred_term', '')
        if term:
            new_data[term] = {
                'synonyms': concept.get('synonyms', [])[:3],  # Take first 3
                'abbreviation': concept.get('abbreviations', [None])[0]  # Take first
            }
    print(f"Loaded {len(new_data):,} concepts from NEW JSON")
    return new_data

def merge_data(old_data, new_data):
    """Merge NEW synonyms/abbreviations with OLD enriched data."""
    merged = []
    match_count = 0
    synonym_updates = 0
    abbr_updates = 0

    for term, old_row in old_data.items():
        new_row = old_row.copy()  # Start with OLD data

        # Check if NEW data available
        if term in new_data:
            match_count += 1
            new_syns = new_data[term]['synonyms']
            new_abbr = new_data[term]['abbreviation']

            # Update synonyms (up to 3)
            for i, syn in enumerate(new_syns, 1):
                if syn:
                    new_row[f'Synonym {i}'] = syn
                    synonym_updates += 1

            # Update abbreviation
            if new_abbr:
                new_row['Abbreviation'] = new_abbr
                abbr_updates += 1

        merged.append(new_row)

    print(f"\nMerge Statistics:")
    print(f"  Matched terms: {match_count:,}")
    print(f"  Synonym updates: {synonym_updates:,}")
    print(f"  Abbreviation updates: {abbr_updates:,}")

    return merged

def write_merged_csv(merged_data, fieldnames):
    """Write merged CSV."""
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_data)
    print(f"\n✅ Wrote {len(merged_data):,} rows to {OUTPUT_CSV}")

def main():
    print("="*70)
    print("UMLS SYNONYM/ABBREVIATION MERGE")
    print("="*70)

    # Load data
    old_data = load_old_data()
    new_data = load_new_synonyms_abbreviations()

    # Merge
    merged = merge_data(old_data, new_data)

    # Write output
    fieldnames = [
        'Term', 'Term Two', 'Definition', 'Closest MeSH term',
        'Synonym 1', 'Synonym 2', 'Synonym 3', 'Abbreviation',
        'UK Spelling', 'US Spelling', 'Noun Form of Word', 'Verb Form of Word',
        'Adjective Form of Word', 'Adverb Form of Word',
        'Commonly Associated Term 1', 'Commonly Associated Term 2',
        'Commonly Associated Term 3', 'Commonly Associated Term 4',
        'Commonly Associated Term 5', 'Commonly Associated Term 6',
        'Commonly Associated Term 7', 'Commonly Associated Term 8',
        'Source', 'Source Priority', 'Sources Contributing', 'Date Added'
    ]
    write_merged_csv(merged, fieldnames)

if __name__ == "__main__":
    main()
```

**Execution:**
```bash
python3 scripts/merge_umls_enrichments.py
```

---

### Step 5: Structural Validation
**Time:** 5 minutes

**Validation Script:** `scripts/validate_umls_structure.py` (existing)

```bash
python3 scripts/validate_umls_structure.py imports/umls/umls_neuroscience_terms_NEW.csv
```

**Expected Output:**
```
✅ All rows have 26 columns
✅ No structural errors detected
✅ Total terms: 325,241
```

**Criteria:**
- 0 structural errors
- All rows have exactly 26 columns
- No data corruption (row count matches)

---

### Step 6: Coverage Comparison
**Time:** 5 minutes

**Comparison Script:** Create `scripts/compare_coverage.py` (~50 lines)

```python
#!/usr/bin/env python3
"""Compare synonym/abbreviation coverage before/after enrichment."""

import csv
import sys

def analyze_coverage(csv_path):
    """Calculate synonym and abbreviation coverage."""
    total = 0
    with_syn = 0
    with_abbr = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            if row.get('Synonym 1', '').strip():
                with_syn += 1
            if row.get('Abbreviation', '').strip():
                with_abbr += 1

    return {
        'total': total,
        'synonyms': with_syn,
        'abbreviations': with_abbr,
        'syn_pct': (with_syn / total * 100) if total > 0 else 0,
        'abbr_pct': (with_abbr / total * 100) if total > 0 else 0
    }

def main():
    old_path = "imports/umls/umls_neuroscience_terms.csv.backup_20251121"
    new_path = "imports/umls/umls_neuroscience_terms_NEW.csv"

    print("Coverage Comparison Report")
    print("="*70)

    old_stats = analyze_coverage(old_path)
    new_stats = analyze_coverage(new_path)

    print(f"\nOLD Data ({old_path}):")
    print(f"  Synonyms: {old_stats['synonyms']:,} ({old_stats['syn_pct']:.1f}%)")
    print(f"  Abbreviations: {old_stats['abbreviations']:,} ({old_stats['abbr_pct']:.1f}%)")

    print(f"\nNEW Data ({new_path}):")
    print(f"  Synonyms: {new_stats['synonyms']:,} ({new_stats['syn_pct']:.1f}%)")
    print(f"  Abbreviations: {new_stats['abbreviations']:,} ({new_stats['abbr_pct']:.1f}%)")

    syn_improvement = new_stats['synonyms'] - old_stats['synonyms']
    abbr_improvement = new_stats['abbreviations'] - old_stats['abbreviations']

    print(f"\n📊 Improvement:")
    print(f"  Synonyms: +{syn_improvement:,} ({new_stats['syn_pct'] - old_stats['syn_pct']:.1f}% increase)")
    print(f"  Abbreviations: +{abbr_improvement:,} ({new_stats['abbr_pct'] - old_stats['abbr_pct']:.1f}% increase)")

    # Success criteria
    success = (
        new_stats['syn_pct'] >= 50.0 and
        new_stats['abbr_pct'] >= 20.0
    )

    if success:
        print(f"\n✅ SUCCESS: Target coverage achieved")
    else:
        print(f"\n⚠️  WARNING: Below target coverage")
        if new_stats['syn_pct'] < 50.0:
            print(f"     Synonyms: {new_stats['syn_pct']:.1f}% (target: 50%+)")
        if new_stats['abbr_pct'] < 20.0:
            print(f"     Abbreviations: {new_stats['abbr_pct']:.1f}% (target: 20%+)")

if __name__ == "__main__":
    main()
```

**Execution:**
```bash
python3 scripts/compare_coverage.py
```

**Success Criteria:**
- Synonym coverage ≥ 50%
- Abbreviation coverage ≥ 20%
- Zero data loss (row count unchanged)

---

### Step 7: Integration Test with Lex Stream
**Time:** 10 minutes

**Test Procedure:**
1. Copy NEW CSV to Lex Stream project:
   ```bash
   cp imports/umls/umls_neuroscience_terms_NEW.csv \
      ../Lex-stream-2/data/neuro_terms.json
   ```

2. Run Lex Stream synonym expansion test:
   ```bash
   cd ../Lex-stream-2
   python3 -m pytest tests/test_synonym_expansion.py -v
   ```

3. Expected results:
   - Query expansion rate increases (more synonyms detected)
   - No schema validation errors
   - Test pass rate ≥ 95%

**Validation:**
- Lex Stream ingests CSV without errors
- Synonym expansion agent detects more variants
- No degradation in other agent performance

---

### Step 8: Replace Production CSV
**Time:** 2 minutes

**Only proceed if all validations pass:**

```bash
# Verify backup exists
ls -lh imports/umls/umls_neuroscience_terms.csv.backup_20251121

# Replace production file
mv imports/umls/umls_neuroscience_terms_NEW.csv \
   imports/umls/umls_neuroscience_terms.csv
```

**Validation:**
```bash
wc -l imports/umls/umls_neuroscience_terms.csv  # Should be 325,242 (header + 325,241 rows)
head -1 imports/umls/umls_neuroscience_terms.csv  # Verify 26-column header
```

---

### Step 9: Git Commit
**Time:** 3 minutes

```bash
git add imports/umls/umls_neuroscience_terms.csv
git add scripts/import_umls_neuroscience.py
git add scripts/merge_umls_enrichments.py
git add scripts/compare_coverage.py

git commit -m "$(cat <<'EOF'
feat(umls): expand synonym and abbreviation extraction

- Expand synonym TTY types: SY, FN, MTH_FN → +6 types (SYN, ET, ETCF, ETCLIN, XM, XQ)
- Expand abbreviation TTY types: AB, ACR → +2 types (AA, SYGB)
- Add heuristic abbreviation detection (all-caps, 2-10 chars)
- Synonym coverage: 9.0% → [ACTUAL]% (+[DELTA] terms)
- Abbreviation coverage: 0.4% → [ACTUAL]% (+[DELTA] terms)
- Preserve existing definitions, associated terms, MeSH codes
- All 325,241 terms maintain 26-column schema compliance
EOF
)"
```

**Note:** Replace `[ACTUAL]` and `[DELTA]` with actual metrics from Step 6.

---

## Validation Strategy

### Pre-Merge Validation Checkpoints
1. **Backup Verification:**
   - Backup file exists
   - Row count matches original (325,241 rows)
   - File size > 0 bytes

2. **Code Modification Verification:**
   - TTY type lists expanded correctly
   - Heuristic function added at correct location
   - No syntax errors (`python3 -m py_compile scripts/import_umls_neuroscience.py`)

3. **MRCONSO Re-parsing Validation:**
   - Script completes without errors
   - Intermediate JSON generated
   - Console output shows increased synonym/abbreviation extraction

### Post-Merge Validation Checkpoints
4. **Structural Validation:**
   - All rows have 26 columns
   - No CSV parsing errors
   - Total row count unchanged (325,241 data rows)

5. **Data Integrity Validation:**
   - Definition fields preserved (79,617 definitions remain)
   - Associated Terms preserved (294,008 terms with associations)
   - MeSH codes preserved (13,739 MeSH codes remain)
   - Source metadata preserved

6. **Coverage Validation:**
   - Synonym coverage ≥ 50%
   - Abbreviation coverage ≥ 20%
   - Coverage improvement documented

7. **Integration Validation:**
   - Lex Stream ingests CSV without errors
   - No schema validation failures
   - Test pass rate ≥ 95%

---

## Rollback Procedures

### Rollback Scenario 1: Code Modification Errors
**Trigger:** Syntax errors, script crashes during re-parsing

**Action:**
```bash
# Revert code changes
git checkout scripts/import_umls_neuroscience.py

# Verify original script works
python3 -m py_compile scripts/import_umls_neuroscience.py
```

---

### Rollback Scenario 2: Merge Script Errors
**Trigger:** Data loss, column misalignment, CSV corruption

**Action:**
```bash
# Delete corrupted output
rm imports/umls/umls_neuroscience_terms_NEW.csv

# Verify backup integrity
wc -l imports/umls/umls_neuroscience_terms.csv.backup_20251121
head -1 imports/umls/umls_neuroscience_terms.csv.backup_20251121

# Production file remains unchanged (no action needed)
```

---

### Rollback Scenario 3: Post-Replacement Issues
**Trigger:** Lex Stream integration failures, schema validation errors

**Action:**
```bash
# Restore from backup
cp imports/umls/umls_neuroscience_terms.csv.backup_20251121 \
   imports/umls/umls_neuroscience_terms.csv

# Verify restoration
wc -l imports/umls/umls_neuroscience_terms.csv
python3 scripts/validate_umls_structure.py imports/umls/umls_neuroscience_terms.csv

# Revert git changes if committed
git revert HEAD
```

---

### Rollback Scenario 4: Lex Stream Integration Degradation
**Trigger:** Synonym expansion causes false positives, query expansion errors

**Action:**
```bash
# In Lex-stream-2 project
cd ../Lex-stream-2

# Restore previous neuro_terms.json
git checkout data/neuro_terms.json

# Verify Lex Stream tests pass
python3 -m pytest tests/test_synonym_expansion.py -v
```

---

## Success Metrics

### Quantitative Targets
- **Synonym Coverage:** ≥ 50% (target: 50-70%)
- **Abbreviation Coverage:** ≥ 20% (target: 20-30%)
- **Structural Validation:** 0 errors
- **Data Preservation:** 100% (all 325,241 rows intact)
- **Lex Stream Test Pass Rate:** ≥ 95%

### Qualitative Thresholds
- Zero data loss on merge
- Existing enrichments preserved (definitions, associations, MeSH codes)
- 26-column schema compliance maintained
- Git history clean (no AI attribution, conventional commit format)

### Performance Benchmarks
- MRCONSO re-parsing: < 30 minutes
- Merge script execution: < 5 minutes
- Total pipeline runtime: < 60 minutes

---

## Files to Modify/Create/Delete

### Modified Files
1. `scripts/import_umls_neuroscience.py`
   - Lines 207-210: Expand synonym TTY types (3 → 9 types)
   - Lines 212-215: Expand abbreviation TTY types (2 → 4 types) + heuristic
   - After line 116: Add `is_potential_abbreviation()` function (~30 lines)
   - After line 116: Add `COMMON_WORDS` constant (~5 lines)

### Created Files
2. `scripts/merge_umls_enrichments.py` (~120 lines)
   - NEW: Merges NEW synonym/abbreviation data with OLD enriched data

3. `scripts/compare_coverage.py` (~50 lines)
   - NEW: Compares coverage before/after enrichment

4. `imports/umls/umls_neuroscience_terms.csv.backup_20251121`
   - Timestamped backup of production CSV

5. `imports/umls/umls_neuroscience_terms_NEW.csv` (TEMPORARY)
   - Merged output (deleted after replacing production file)

6. `imports/umls/umls_concepts_intermediate.json` (REGENERATED)
   - Intermediate JSON with expanded synonyms/abbreviations

### Deleted Files (After Merge)
7. `imports/umls/umls_neuroscience_terms_NEW.csv`
   - Temporary merged file (replaced production file)

---

## Risks & Mitigations

### Risk 1: TTY Type Explosion (Low-Quality Synonyms)
**Likelihood:** Medium
**Impact:** High (false positives in Lex Stream query expansion)

**Mitigation:**
- Post-merge: Sample 100 random terms, manually verify synonym quality
- If quality < 80%: Reduce TTY types (remove XM, XQ as lowest priority)
- Iterate TTY selection based on quality feedback

---

### Risk 2: Heuristic Abbreviation False Positives
**Likelihood:** Medium
**Impact:** Medium (common words detected as abbreviations)

**Mitigation:**
- `COMMON_WORDS` blacklist (40+ common English words)
- Length constraint (2-10 chars) filters out long phrases
- Post-merge: Manually review top 50 heuristic-detected abbreviations
- If FP rate > 10%: Expand `COMMON_WORDS` blacklist

---

### Risk 3: Merge Script Data Loss
**Likelihood:** Low
**Impact:** Critical (lose definitions, associations, MeSH codes)

**Mitigation:**
- Timestamped backup before merge (`umls_neuroscience_terms.csv.backup_20251121`)
- Merge script writes to NEW file (no overwrite until validated)
- Validation step confirms row count unchanged
- Rollback procedure tested before execution

---

### Risk 4: MRCONSO Re-parsing Performance
**Likelihood:** Low
**Impact:** Medium (exceeds 30-minute target)

**Mitigation:**
- Use existing `neuroscience_cuis.txt` filter (reduces rows by 95%)
- Python multiprocessing if runtime > 30 minutes (parallelize CUI filtering)
- Monitor progress indicators (console output every 1M rows)

---

### Risk 5: Lex Stream Integration Degradation
**Likelihood:** Low
**Impact:** High (query expansion errors, false positives)

**Mitigation:**
- Integration test BEFORE replacing production file (Step 7)
- Rollback procedure if test pass rate < 95%
- A/B comparison: OLD vs NEW synonym expansion behavior
- Deploy to Lex Stream staging environment first (if available)

---

## Testing Strategy

### Unit Tests (Not Required)
- No new complex logic added (TTY list expansion only)
- Heuristic function simple (blacklist + regex)
- Manual verification sufficient

### Integration Tests (REQUIRED)
1. **Structural Validation** (Step 5)
   - Verify 26-column schema compliance
   - Verify row count unchanged

2. **Coverage Comparison** (Step 6)
   - Verify synonym coverage ≥ 50%
   - Verify abbreviation coverage ≥ 20%

3. **Lex Stream Integration Test** (Step 7)
   - Verify CSV ingestion without errors
   - Verify synonym expansion agent behavior
   - Verify test pass rate ≥ 95%

### Manual Verification (Recommended)
4. **Synonym Quality Sampling:**
   - Sample 100 random terms
   - Manually verify synonym relevance
   - Target quality: ≥ 80% relevant synonyms

5. **Abbreviation Quality Sampling:**
   - Sample 50 heuristic-detected abbreviations
   - Manually verify abbreviation validity
   - Target FP rate: < 10%

---

## Performance Considerations

### MRCONSO Re-parsing Optimization
- **Current Performance:** ~17M rows parsed in 20-30 minutes
- **Bottleneck:** Disk I/O (2.1 GB file read)
- **Optimization:** Reuse existing `neuroscience_cuis.txt` filter (reduces processing by 95%)
- **No Further Optimization Needed:** Performance acceptable

### Merge Script Optimization
- **Expected Performance:** < 5 minutes for 325K rows
- **Bottleneck:** In-memory dict lookups (O(1) average)
- **No Optimization Needed:** CSV processing adequate for dataset size

### Validation Script Optimization
- **Expected Performance:** < 1 minute per script
- **No Optimization Needed:** Single-pass CSV iteration sufficient

---

## Security Considerations

### Data Integrity
- **Backup Strategy:** Timestamped backups prevent accidental overwrites
- **Merge Strategy:** Write to NEW file, validate before replacing production
- **Validation Strategy:** Multi-checkpoint verification before committing

### Access Control
- **No Changes Required:** File permissions unchanged
- **Git History:** Professional commits (no AI attribution)

### Sensitive Data
- **No PII/PHI:** UMLS data is medical terminology (no patient data)
- **No Credentials:** No API keys or secrets in code

---

## Unresolved Questions

1. **TTY Type Priority:** Should XM and XQ synonyms be weighted lower in Lex Stream query expansion? (May require Lex Stream schema update to support synonym quality scores)

2. **Heuristic Abbreviation Threshold:** Is 2-10 char length optimal? (May need adjustment after manual QA sampling)

3. **Merge Conflict Resolution:** If a term exists in OLD CSV but not in NEW JSON (unlikely), should it be preserved or flagged for review?

4. **Performance Profiling:** Should we add timing instrumentation to `parse_mrconso()` to identify bottlenecks for future optimizations?

5. **Phase 2B Dependencies:** Does Phase 2A completion unblock Phase 2B (MeSH enrichment), or can they run in parallel?

---

## Next Steps After Phase 2A

**Immediate (After Validation):**
1. Run coverage comparison metrics
2. Update CLAUDE.md with new coverage statistics
3. Notify Lex Stream team of enriched data availability

**Short-Term (Phase 2B):**
1. Create `scripts/enrich_mesh_codes.py` for MeSH API enrichment
2. Target MeSH coverage: 4.2% → 30-40%
3. Integrate mesh-validator agent for verification

**Long-Term (Phase 2C):**
1. Analyze Lex Stream query logs to identify top 10K most-queried terms
2. Backfill definitions using Wikipedia, NINDS, PubMed
3. Target definition coverage: 24.5% → 40-50%

---

**END OF PLAN**
