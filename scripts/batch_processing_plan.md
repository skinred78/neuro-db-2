# Batch Processing Plan: Letters B-W

**Goal**: Process remaining 49 NINDS terms efficiently using parallel batch processing
**Strategy**: Group letters by term count, process batches in parallel

---

## Remaining Terms Breakdown

**Total**: 16 letters, 49 terms

### Small Letters (1-2 terms) - 7 letters, 10 terms
- O: 1 term (Orthostatic Hypotension)
- R: 1 term (Rigidity)
- S: 1 term (Syncope)
- W: 1 term (Whiplash)
- B: 2 terms (Biomarkers, Blood-brain barrier)
- F: 2 terms (Fasciculations, Fibromuscular dysplasia)
- T: 2 terms (Transcutaneous Electrical Nerve Stimulation, Tremor)

### Medium Letters (3-5 terms) - 8 letters, 31 terms
- E: 3 terms (Encephalitis, Encephalopathy, Enzymes)
- I: 3 terms (Immunoglobulins, Inflammation, Intravenous immunoglobulin)
- L: 3 terms (Learning Disabilities, Lipidoses, Lipids)
- H: 4 terms (Hydromyelia, Hypersomnia, Hypertonia, Hypotonia)
- N: 4 terms (Nervous System, Neuropathy, Neurosarcoidosis, Neurotoxicity)
- P: 4 terms (Paresthesia, Pinched Nerve, Plasmapheresis, Platelets)
- D: 5 terms (Dendrites, Dysautonomia, Dysgraphia, Dysphagia, Dystonia)
- M: 5 terms (Metabolism, Multi-infarct Dementia, Myelin Sheath, Myelitis, Myotonia)

### Large Letter (8 terms) - 1 letter, 8 terms
- C: 8 terms (Cephalocele, Cerebral, Cerebral Atrophy, Cerebral Hypoxia, Chorea, Clonus, Coma, Contracture)

---

## Batch Processing Strategy

### Approach: 4 Batches with Parallel Execution

**Batch 1: SMALL LETTERS** (7 letters, 10 terms)
- Letters: O, R, S, W, B, F, T
- Processing time: ~15-20 minutes
- Strategy: All small letters in single batch

**Batch 2: MEDIUM BATCH A** (4 letters, 13 terms)
- Letters: E, I, L, H
- Processing time: ~20-25 minutes
- Strategy: First half of medium letters

**Batch 3: MEDIUM BATCH B** (4 letters, 18 terms)
- Letters: N, P, D, M
- Processing time: ~25-30 minutes
- Strategy: Second half of medium letters

**Batch 4: LARGE LETTER** (1 letter, 8 terms)
- Letters: C
- Processing time: ~15-20 minutes
- Strategy: Process separately (most terms in single letter)

**Total estimated time**: 75-95 minutes for all 4 batches

---

## Parallel Processing Per Batch

For EACH batch, we'll launch dual enrichment in parallel:

```
Batch X Processing:
├── neuro-reviewer agent (enriches synonyms, abbreviations, word forms, associated terms)
└── mesh-validator agent (discovers MeSH terms via NIH API)
     │
     ▼
   Merge results → Validate → Correct → Final
```

---

## Workflow Per Batch

### Step 1: Launch Dual Enrichment (Parallel)
- neuro-reviewer: Enriches all non-MeSH fields for all letters in batch
- mesh-validator: Discovers MeSH terms for all letters in batch
- Both run in parallel (single message, 2 Task calls)

### Step 2: Merge Results
- Combine neuro-reviewer + mesh-validator outputs
- Create single enriched CSV per letter

### Step 3: Dual Validation (Parallel)
- mesh-validator: Verify MeSH terms
- neuro-reviewer: Verify enriched fields
- Both run in parallel

### Step 4: Apply Corrections
- Batch apply all corrections from both validators
- Update MeSH tracking files if needed
- Targeted re-validation on corrected items only

### Step 5: Final Output
- Each letter gets final validated CSV
- Ready for integration into master database

---

## Batch Execution Order

### Option A: Sequential Batches (Conservative)
Process one batch at a time, validate, correct, then move to next batch.
- **Pro**: Easier to manage, can adjust based on results
- **Con**: Takes full 75-95 minutes
- **Recommended**: If you want to monitor progress

### Option B: Parallel Batches (Aggressive)
Launch all 4 batches simultaneously, handle all corrections at end.
- **Pro**: Could complete in 30-40 minutes (fastest batch determines total time)
- **Con**: More complex to manage, harder to track issues
- **Recommended**: If you want maximum speed

### Option C: Staggered Batches (Balanced) ✓ RECOMMENDED
Launch batches in pairs: (Batch 1 + 2) together, then (Batch 3 + 4) together.
- **Pro**: Balance of speed and manageability
- **Con**: Moderate complexity
- **Recommended**: Best balance of efficiency and control

---

## Success Criteria Per Batch

Each batch must achieve:
- [ ] All terms enriched (no missing data in mandatory fields)
- [ ] 75%+ MeSH term coverage (some terms may not have MeSH)
- [ ] 100% validation pass rate (after corrections)
- [ ] All corrections documented
- [ ] Final CSV files generated

---

## Risk Mitigation

### Potential Issues

**Issue 1: Agent Overload**
- Risk: Processing too many terms at once overwhelms agents
- Mitigation: Batch size limited to 18 terms max
- Fallback: Split large batches if issues occur

**Issue 2: Validation Failures**
- Risk: High correction rate slows process
- Mitigation: Learn from Letter A pilot (common error patterns)
- Fallback: More specific enrichment prompts

**Issue 3: MeSH API Rate Limiting**
- Risk: Too many API calls in short time
- Mitigation: mesh-validator has built-in rate limiting
- Fallback: Stagger batch launches by 5 minutes

---

## Files Generated (49 total)

### Per Letter (16 letters × 3 files each = 48 files):
- `[X]_NINDS_template.csv` - Already exists (extraction output)
- `[X]_NINDS_enriched.csv` - After dual enrichment (intermediate, will archive)
- `[X]_NINDS_final.csv` - After validation and corrections (KEEP)

### Summary Reports:
- `batch_1_summary.md` - Batch 1 results
- `batch_2_summary.md` - Batch 2 results
- `batch_3_summary.md` - Batch 3 results
- `batch_4_summary.md` - Batch 4 results
- `all_batches_final_report.md` - Overall summary

---

## Next Steps After Batch Processing

Once all 4 batches complete:
1. Review all 16 final CSV files (49 terms total)
2. Integrate into LetterFiles/ directory
3. Merge with existing database (515 + 49 = 564 terms)
4. Update MeSH tracking logs
5. Generate consolidated neuro_terms.csv
6. Export to Lex Stream JSON format

---

**Ready to Start Batch Processing**

Recommended approach: **Option C (Staggered Batches)**
- Launch Batches 1 & 2 together (~35-45 min)
- Validate and correct
- Launch Batches 3 & 4 together (~40-50 min)
- Validate and correct
- Total time: ~75-95 minutes
