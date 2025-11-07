# NINDS Glossary Integration Plan

**Created**: 2025-11-07
**Updated**: 2025-11-07 (Revised enrichment approach)
**Source**: NINDS Glossary of Neurological Terms
**URL**: https://www.ninds.nih.gov/health-information/disorders/glossary-neurological-terms
**Status**: Ready for Implementation (Revised Approach)

---

## Executive Summary

**Goal**: Integrate 54 NEW neuroscience terms from NINDS Glossary into NeuroDB-2 database

**Current State**:
- Existing database: 515 terms (Wikipedia Glossary, letters A-Z)
- NINDS Glossary: 76 terms total
- Overlap: 22 terms (both databases have them)
- NEW terms: 54 terms (only in NINDS)

**Approach**: Add NEW terms to existing letter files, enriching database coverage

**Expected Outcome**: Expanded database with 569 total terms (515 + 54)

---

## Analysis: NINDS vs Wikipedia Glossary

### Source Comparison

| Aspect | Wikipedia Glossary | NINDS Glossary |
|--------|-------------------|----------------|
| **Purpose** | Academic reference | Patient education |
| **Language** | Technical/scientific | Plain language |
| **Definitions** | Detailed, technical | Simplified, accessible |
| **Coverage** | Broad neuroscience | Clinical/medical focus |
| **Terms Count** | 515 terms | 76 terms |
| **Authority** | Community-curated | NIH/Government |

### Data Quality Assessment

**NINDS Strengths**:
- ✅ Authoritative source (NIH)
- ✅ Plain language definitions (good for accessibility)
- ✅ Clinical/medical focus (complements Wikipedia's academic focus)
- ✅ Patient-centric terminology

**NINDS Limitations**:
- ⚠️ Limited coverage (76 terms vs Wikipedia's 515)
- ⚠️ No MeSH terms provided (need to enrich)
- ⚠️ No synonyms provided (need to enrich)
- ⚠️ No abbreviations provided (need to enrich)
- ⚠️ Simplified definitions (may lack technical precision)

### Integration Strategy

**Decision**: ADD new terms, KEEP existing Wikipedia definitions for overlaps

**Rationale**:
- Wikipedia definitions are more technical/comprehensive
- NINDS definitions can be added as supplementary data later
- Avoid overwriting validated data
- Maintain consistency with existing database standards

---

## NEW Terms from NINDS (54 total)

### Complete List by Letter

**A (4 terms)**
- Anemia
- Apraxia
- Atrial Fibrillation
- Atrophy

**B (2 terms)**
- Biomarkers
- Blood-brain barrier

**C (8 terms)**
- Cephalocele
- Cerebral
- Cerebral Atrophy
- Cerebral Hypoxia
- Chorea
- Clonus
- Coma
- Contracture

**D (5 terms)**
- Dendrites
- Dysautonomia
- Dysgraphia
- Dysphagia
- Dystonia

**E (3 terms)**
- Encephalitis
- Encephalopathy
- Enzymes

**F (2 terms)**
- Fasciculations
- Fibromuscular dysplasia (FMD)

**H (4 terms)**
- Hydromyelia
- Hypersomnia
- Hypertonia
- Hypotonia

**I (3 terms)**
- Immunoglobulins
- Inflammation
- Intravenous immunoglobulin

**L (4 terms)**
- Learning Disabilities
- Lipidoses
- Lipids
- (Note: Lesion is overlap, not new)

**M (5 terms)**
- Metabolism
- Multi-infarct Dementia
- Myelin Sheath
- Myelitis
- Myotonia

**N (3 terms)**
- Neuropathy
- Neurosarcoidosis
- Neurotoxicity

**O (1 term)**
- Orthostatic Hypotension

**P (7 terms)**
- Paralysis
- Paresthesia
- Peripheral Nervous System
- Pinched Nerve
- Plasmapheresis
- Platelets
- Prosopagnosia

**R (1 term)**
- Rigidity

**S (3 terms)**
- Spasticity
- Syncope
- (Note: Synapse is overlap, not new)

**T (2 terms)**
- Tardive Dyskinesia
- Transcutaneous Electrical Nerve Stimulation

**W (2 terms)**
- Whiplash
- White Matter

---

## Integration Workflow

### Key Approach: Division of Labor

**Critical Design Decision**: mesh-validator discovers MeSH terms, AI enriches everything else

**Why This Matters**:
1. **Single Source of Truth for MeSH**: NIH API is authoritative, AI guesses are not
2. **Efficiency**: mesh-validator searches + validates in one step (not two)
3. **Accuracy**: Direct API queries more reliable than AI suggestions
4. **Simplicity**: Clear separation of responsibilities

**Agent Responsibilities**:
- **mesh-validator**: Search NIH MeSH API for term, add if found, document if not found
- **AI (neuro-reviewer)**: Enrich synonyms, abbreviations, word forms, associated terms
- **Both validate in parallel**: mesh-validator checks MeSH consistency, neuro-reviewer validates AI-enriched fields

### Phase 1: Data Extraction & Enrichment

**Step 1: Extract NINDS Terms**
- Parse `ninds-glossary-of-neurological-terms.md`
- Extract term name + definition for 54 NEW terms
- Group by letter for organization

**Step 2: Enrich with Missing Fields**

For each NEW term, populate:

| Field | Data Source | Method |
|-------|-------------|--------|
| `Term` | NINDS (direct) | ✅ Available |
| `Term Two` | Manual | Generate ASCII-safe version if needed |
| `Definition` | NINDS (direct) | ✅ Available |
| `Closest MeSH term` | **mesh-validator API search** | **Discover + validate in one step** |
| `Synonym 1-3` | AI enrichment | neuro-reviewer + research |
| `Abbreviation` | AI enrichment | Check if standard abbreviation exists |
| `UK/US Spelling` | Dictionary/AI | Check for variants |
| `Word Forms` | Dictionary/AI | Extract noun/verb/adjective/adverb |
| `Associated Terms 1-8` | AI enrichment | Related neuroscience concepts |

**Enrichment Approach (Revised)**:
- **AI enriches everything EXCEPT MeSH terms**: Synonyms, abbreviations, word forms, associated terms
- **mesh-validator discovers MeSH terms via NIH API search**: Searches API, adds term if found, leaves empty if not found
- **neuro-reviewer validates AI-enriched fields**: Cross-validates synonyms, abbreviations, word forms, associated terms
- Leave fields empty if no reliable data (accuracy over completeness)

### Phase 2: Validation

**Step 3: Run Dual Validation**

For each enriched term (run agents in parallel):
- **mesh-validator**: MeSH terms already discovered/added in Step 2, verify consistency and document empty fields
- **neuro-reviewer**: Validate AI-enriched fields (synonyms, abbreviations, word forms, associated terms)
- Both agents must PASS before proceeding

**Step 4: Apply Corrections**
- Batch apply all corrections from validation reports
- Update MeSH tracking files if corrections made
- Targeted re-validation on corrected items

### Phase 3: Integration

**Step 5: Add to Letter Files**

Options:

**Option A: Separate NINDS Letter Files (Recommended for Testing)**
- Create new files: `A_NINDS.csv`, `B_NINDS.csv`, etc.
- Keeps NINDS data separate for quality comparison
- Easy to merge or discard later

**Option B: Merge into Existing Letter Files**
- Append NINDS terms to existing `A.csv`, `B.csv`, etc.
- Single unified database
- Requires more careful tracking

**Recommendation**: Option A initially, then Option B after validation passes

**Step 6: Update Consolidated Database**
- Re-run Workflow 2 (Merge Letter Files)
- Consolidate all letters → `neuro_terms.csv`
- Verify term count: 515 + 54 = 569 terms
- Generate JSON export → `neuro_terms.json`

### Phase 4: Export to Lex Stream Format

**Step 7: Convert to Lex Stream JSON**
- Run conversion script: `convert_neurodb_to_lexstream.py`
- Output: `neuro_terms.json` (Lex Stream format)
- Validate structure against DATABASE_CREATION_GUIDE.md requirements
- Test with Lex Stream pipeline

---

## Implementation Steps (Detailed)

### Step 1: Create Extraction Script

**File**: `scripts/extract_ninds_terms.py`

```python
#!/usr/bin/env python3
"""Extract NEW terms from NINDS glossary for integration."""
import csv

# Read NINDS glossary
with open('ninds-glossary-of-neurological-terms.md', 'r') as f:
    lines = f.readlines()

# Parse terms + definitions
ninds_data = []
i = 0
while i < len(lines):
    line = lines[i].strip()
    if not line or line.startswith('-') or line.startswith('Original'):
        i += 1
        continue
    if line and line[0].isupper():
        if i + 1 < len(lines):
            definition = lines[i + 1].strip()
            if definition and not definition.startswith('-'):
                ninds_data.append({
                    'term': line,
                    'definition': definition
                })
                i += 2
                continue
    i += 1

# Filter for NEW terms only (not in existing database)
# ... comparison logic ...

# Output by letter
# ... grouping and export logic ...
```

### Step 2: Create Enrichment Script

**File**: `scripts/enrich_ninds_terms.py`

```python
#!/usr/bin/env python3
"""Enrich NINDS terms with missing fields using AI."""
# Use Gemini CLI or similar to:
# 1. Suggest MeSH terms
# 2. Identify synonyms
# 3. Extract abbreviations
# 4. Find associated terms
# 5. Determine word forms
```

### Step 3: Run Validation Workflow

**Use existing validation agents**:
```bash
# For each letter with new NINDS terms
# Launch both agents in parallel (use single message with 2 Task calls)
Task: mesh-validator validates MeSH terms
Task: neuro-reviewer validates all other fields
```

### Step 4: Integration Command Sequence

```bash
# Extract NINDS terms
python scripts/extract_ninds_terms.py

# Enrich with missing fields
python scripts/enrich_ninds_terms.py

# Validate (use Claude Code agents in parallel)
# Apply corrections
# Re-validate

# Add to letter files (Option A: separate files)
# A_NINDS.csv, B_NINDS.csv, etc.

# Merge all letters (including NINDS)
# Workflow 2: Merge Letter Files

# Generate final exports
# Workflow 5: Generate JSON
# Workflow 5b: Convert to Lex Stream format
```

---

## Data Quality Standards

### NINDS-Specific Considerations

**Definition Handling**:
- NINDS definitions are plain language (patient-focused)
- May lack technical precision
- Consider adding as "Plain Language Definition" supplementary field (future enhancement)
- For now: Use NINDS definition as primary `Definition` field

**MeSH Term Discovery**:
- NINDS doesn't provide MeSH terms
- mesh-validator searches NIH API directly for each term
- If exact/close match found → add MeSH term
- If no match found → leave empty, document rationale (e.g., "informal term, no official MeSH")
- More reliable than AI suggestions (single source of truth: NIH API)

**Synonym Enrichment**:
- NINDS provides minimal synonym information
- Requires external research (PubMed, medical dictionaries)
- Lower confidence than Wikipedia-sourced synonyms
- Mark enriched fields for future review

### Validation Thresholds

**Acceptable Completion Rates for NINDS Terms**:
- `Term`: 100% (required)
- `Definition`: 100% (from NINDS)
- `Closest MeSH term`: 80%+ (some terms may lack MeSH)
- `Synonym 1`: 50%+ (enrichment-dependent)
- `Abbreviation`: 30%+ (not all terms have abbreviations)
- `Associated Terms`: 60%+ (clinical terms often have strong associations)

---

## Risk Assessment

### Potential Issues

**1. MeSH Discovery Challenges**
- **Risk**: Some NINDS terms may not have official MeSH equivalents (informal/colloquial terms)
- **Example**: "Pinched Nerve" (NINDS) → no direct MeSH equivalent
- **Mitigation**: mesh-validator searches API, leaves empty if no match, documents rationale (acceptable outcome)

**2. Definition Quality Disparity**
- **Risk**: NINDS definitions less technical than Wikipedia
- **Impact**: Database consistency affected
- **Mitigation**: Accept as-is, consider future field for "Technical Definition"

**3. Enrichment Data Quality**
- **Risk**: AI-generated synonyms/abbreviations/associated terms may be less reliable than Wikipedia-sourced data
- **Impact**: Lower confidence in some enriched fields for NINDS-sourced terms
- **Mitigation**: neuro-reviewer validates all AI-enriched fields, mark enriched fields for future review, document confidence levels
- **Note**: MeSH terms are NOT AI-generated (API-discovered), so higher reliability

**4. Overlap Conflicts**
- **Risk**: 22 overlapping terms have different definitions
- **Decision**: Keep Wikipedia definitions (higher technical quality)
- **Future**: Consider adding NINDS definitions as supplementary

### Mitigation Strategies

1. **Separate NINDS Letter Files**: Easy rollback if quality issues
2. **Enhanced Validation**: Extra scrutiny on AI-enriched fields
3. **Documentation**: Track NINDS provenance in metadata
4. **Phased Integration**: Test on subset (letters A-E) before full integration
5. **Quality Metrics**: Compare NINDS vs Wikipedia term performance in Lex Stream

---

## Timeline Estimate

### Phase 1: Data Extraction & Enrichment (4-6 hours)
- Extract 54 terms: 1 hour
- Enrich with missing fields: 2-3 hours
- Format for validation: 1-2 hours

### Phase 2: Validation (2-3 hours)
- Run dual validation: 1 hour
- Review reports: 30 min
- Apply corrections: 30 min
- Re-validation: 1 hour

### Phase 3: Integration (1-2 hours)
- Create NINDS letter files: 30 min
- Merge with existing database: 30 min
- Generate exports: 30 min
- Quality checks: 30 min

### Phase 4: Lex Stream Conversion (1-2 hours)
- Create conversion script: 1 hour
- Validate output: 30 min
- Test with Lex Stream: 30 min

**Total Estimated Time**: 8-13 hours

---

## Success Criteria

### Quantitative Metrics
- [ ] All 54 NEW terms extracted from NINDS
- [ ] 100% of terms have definitions
- [ ] 80%+ of terms have validated MeSH mappings
- [ ] 100% dual validation pass rate (after corrections)
- [ ] Consolidated database has 569 terms (515 + 54)
- [ ] Lex Stream JSON validates successfully
- [ ] No data loss from existing 515 terms

### Qualitative Metrics
- [ ] NINDS terms integrate seamlessly with existing database
- [ ] Data quality standards maintained
- [ ] MeSH corrections tracked properly
- [ ] Audit trail complete
- [ ] Documentation updated

---

## Next Actions

**Immediate**:
1. Review this plan for accuracy and completeness
2. Decide on integration approach (Option A vs B)
3. Create extraction script (`scripts/extract_ninds_terms.py`)
4. Test extraction on 5-10 sample terms

**Short-term**:
1. Develop enrichment strategy (manual vs AI-assisted)
2. Create enrichment script or workflow
3. Run pilot on Letter A NINDS terms (4 terms)
4. Validate pilot results

**Long-term**:
1. Process all 54 NINDS terms
2. Integrate into master database
3. Convert to Lex Stream format
4. Test with Lex Stream pipeline
5. Gather performance metrics
6. Document lessons learned

---

## Questions for Discussion

1. **Integration Approach**: Separate NINDS files (Option A) or merge immediately (Option B)?
2. **Definition Preference**: Keep Wikipedia (technical) or use NINDS (plain language)?
3. **Enrichment Method**: Fully automated (AI) or human-guided enrichment?
4. **Validation Threshold**: What % of empty fields is acceptable for NINDS terms?
5. **Timeline**: Rush integration or phased/careful approach?

---

## Appendix: Sample NINDS Terms

### Example 1: Apraxia (NEW term)
**NINDS Definition**: "Apraxia is the loss of the ability to perform skilled movements and gestures. For example, a person may no longer be able to wink, lick their lips, or complete the steps required to bathe or dress themselves."

**Enrichment Needs**:
- MeSH term: "Apraxia" (to be validated)
- Synonyms: "dyspraxia" (developmental form)
- Associated terms: "motor planning", "motor skills", "neurological disorder"

### Example 2: Biomarkers (NEW term)
**NINDS Definition**: "Biomarker is a term used to refer to biological signs of disease found in blood, body fluids, and tissues. Biomarkers can help indicate risk of a disease, aid in diagnosis, and track progression."

**Enrichment Needs**:
- MeSH term: "Biomarkers" (to be validated)
- Synonyms: "biological markers", "molecular markers"
- Associated terms: "diagnosis", "prognosis", "disease progression", "clinical trial"

### Example 3: Dendrites (NEW term)
**NINDS Definition**: "Dendrites are the part of the neuron that receive signals from other nerve cells."

**Enrichment Needs**:
- MeSH term: "Dendrites" (to be validated)
- Associated terms: "neuron", "synapse", "axon", "signal transmission", "neurotransmitter"

---

**End of Integration Plan**
