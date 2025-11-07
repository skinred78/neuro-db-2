# NINDS Terms Enrichment Instructions

## Overview

You now have 54 NEW NINDS terms extracted into CSV template files in `scripts/output/`.
These files have Term + Definition populated, but all other fields are empty.

**Next Step**: Enrich these terms with missing fields using dual approach:
1. **AI (neuro-reviewer)** enriches: Synonyms, Abbreviations, Word Forms, Associated Terms
2. **mesh-validator** discovers: MeSH terms via NIH API search

---

## Pilot Approach (Recommended)

Start with Letter A only (5 terms) to validate the workflow before processing all 54 terms.

### Pilot File
- **File**: `scripts/output/A_NINDS_template.csv`
- **Terms**: 5 terms (Anemia, Apraxia, Atrial Fibrillation, Atrophy, Autosomal Recessive Disorders)

---

## Enrichment Workflow

### Step 1: Prepare for Enrichment

**Input File**: `scripts/output/A_NINDS_template.csv`

Review the 5 terms that need enrichment:
```
1. Anemia
2. Apraxia
3. Atrial Fibrillation
4. Atrophy
5. Autosomal Recessive Disorders
```

### Step 2: Launch Dual Enrichment (Parallel)

**IMPORTANT**: Run both agents in parallel using single message with 2 Task tool calls

#### Agent 1: neuro-reviewer (AI Enrichment)

**Prompt Template**:
```
I need you to enrich neuroscience terms from the NINDS Glossary with missing fields.

**Input File**: scripts/output/A_NINDS_template.csv

**Your Task**: For each of the 5 terms, enrich the following fields:
- Synonym 1-3: True alternative names (NOT abbreviations)
- Abbreviation: Standard abbreviated form (if exists)
- UK Spelling / US Spelling: Regional variants (if different)
- Word Forms: Noun, Verb, Adjective, Adverb (only if specific to this term)
- Commonly Associated Terms 1-8: Related neuroscience concepts (1-8 as appropriate)

**Critical Rules**:
- Do NOT suggest MeSH terms (mesh-validator will handle that)
- Leave fields empty if no reliable data
- Accuracy over completeness
- Abbreviations go in Abbreviation field, NOT synonyms

**Output**: Updated CSV with enriched fields
```

#### Agent 2: mesh-validator (MeSH Discovery)

**Prompt Template**:
```
I need you to discover MeSH terms for NINDS Glossary terms.

**Input File**: scripts/output/A_NINDS_template.csv

**Your Task**: For each of the 5 terms:
1. Search NIH MeSH API for the term
2. If exact/close match found: Add MeSH term to "Closest MeSH term" column
3. If no match found: Leave empty, document rationale

**Terms to Search**:
1. Anemia
2. Apraxia
3. Atrial Fibrillation
4. Atrophy
5. Autosomal Recessive Disorders

**Critical Rules**:
- Use NIH MeSH API as single source of truth
- Leaving empty is acceptable (not all terms have MeSH)
- Document rationale for empty fields

**Output**: Updated CSV with MeSH terms discovered
```

### Step 3: Merge Results

After both agents complete:
1. Take AI-enriched CSV (synonyms, abbreviations, word forms, associated terms)
2. Add MeSH terms from mesh-validator results
3. Create single enriched CSV: `scripts/output/A_NINDS_enriched.csv`

### Step 4: Run Dual Validation (Parallel)

**IMPORTANT**: Run both validators in parallel

#### Validator 1: mesh-validator

**Prompt**:
```
Validate MeSH terms in scripts/output/A_NINDS_enriched.csv

Verify:
- All MeSH terms are valid via NIH API
- Empty MeSH fields have documented rationale
- Format matches MeSH standards

Report: PASS/FAIL with details
```

#### Validator 2: neuro-reviewer

**Prompt**:
```
Validate AI-enriched fields in scripts/output/A_NINDS_enriched.csv

Verify:
- Synonyms are accurate (not abbreviations)
- Abbreviations are standard usage
- Word forms are appropriate
- Associated terms are relevant
- Definitions are accurate

Report: PASS/FAIL with details
```

### Step 5: Apply Corrections (If Needed)

If either validator returns FAIL:
1. Review correction suggestions from both reports
2. Apply ALL corrections in single batch
3. Update MeSH tracking files (if MeSH corrections made)
4. Run targeted re-validation (only corrected items)

### Step 6: Human Review

Once both validators PASS:
1. Review enriched CSV for quality
2. Check for obvious errors or omissions
3. Approve for integration or request adjustments

---

## Scaling to All Terms

After pilot succeeds with Letter A:

### Batch Processing Options

**Option 1: Process All Letters at Once**
- Run enrichment on all 17 letter files
- Parallel agent invocations for each letter
- Faster but requires more coordination

**Option 2: Process Letter by Letter**
- Complete A, then B, then C, etc.
- More controlled, easier to track progress
- Recommended for safety

**Option 3: Process by Batch Size**
- Group letters by term count:
  - Small batch (1-2 terms): O, R, S, W
  - Medium batch (3-5 terms): A, B, D, E, F, H, I, L, M, N, P, T
  - Large batch (8 terms): C

---

## Quality Metrics

Track these metrics for pilot (Letter A):

- **Enrichment Coverage**:
  - % terms with at least 1 synonym
  - % terms with abbreviation
  - % terms with MeSH term
  - % terms with 3+ associated terms

- **Validation**:
  - First-pass validation rate
  - Number of corrections needed
  - Re-validation pass rate

- **Time**:
  - Enrichment time per term
  - Validation time per term
  - Total time for 5 terms

**Expected Results**:
- 80%+ should have MeSH terms (Anemia, Apraxia, Atrial Fibrillation likely have them)
- 60%+ should have at least 1 synonym
- 40%+ should have abbreviations
- 100% should have associated terms

---

## Pilot Success Criteria

Letter A pilot is successful if:
- [ ] All 5 terms enriched with no empty mandatory fields (Term, Definition)
- [ ] 80%+ have validated MeSH terms
- [ ] 100% pass dual validation (after corrections if needed)
- [ ] Enriched CSV is well-formatted (22 columns, proper quoting)
- [ ] Process completed in < 2 hours
- [ ] Workflow is repeatable for other letters

---

## Troubleshooting

### Issue: mesh-validator finds no MeSH terms

**Possible Causes**:
- Terms are informal/colloquial (e.g., "Pinched Nerve")
- Terms are too specific or too general
- Terms are not in medical domain

**Solution**:
- Document rationale for empty MeSH field
- Proceed with integration (empty is acceptable)

### Issue: neuro-reviewer suggests poor quality enrichments

**Possible Causes**:
- AI lacks domain knowledge for rare terms
- Term has minimal literature coverage

**Solution**:
- Manually research term
- Leave fields empty rather than use low-confidence data
- Mark for future review

### Issue: Validators disagree on corrections

**Resolution**:
- mesh-validator has final authority on MeSH terms
- neuro-reviewer has final authority on other fields
- Human review resolves conflicts

---

## Next Steps After Pilot

If pilot succeeds:
1. Document lessons learned
2. Adjust enrichment prompts if needed
3. Scale to remaining 49 terms (Letters B-W)
4. Track cumulative metrics
5. Prepare for integration into master database

If pilot fails:
1. Identify root cause
2. Adjust approach
3. Retry pilot with improvements
4. Reassess integration plan if needed

---

## Files Generated

During pilot, you will create:
- `scripts/output/A_NINDS_template.csv` - ✓ Already created (extraction)
- `scripts/output/A_NINDS_enriched.csv` - Created after enrichment
- `scripts/output/A_NINDS_validation_mesh.md` - mesh-validator report
- `scripts/output/A_NINDS_validation_neuro.md` - neuro-reviewer report
- `scripts/output/A_NINDS_final.csv` - After validation passes

---

**Ready to start pilot enrichment for Letter A (5 terms)?**
