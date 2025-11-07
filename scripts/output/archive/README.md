# Archive: Intermediate Workflow Files

**Purpose**: This directory contains intermediate files from the enrichment and validation workflow. These files show the step-by-step progression but are not needed for final integration.

## Letter A Pilot Files

### A_NINDS_enriched_neuro.csv
- **Created by**: neuro-reviewer agent
- **Contains**: AI-enriched fields (synonyms, abbreviations, word forms, associated terms)
- **Missing**: MeSH terms (not yet added)
- **Status**: Intermediate - superseded by enriched_final.csv

### A_NINDS_enriched_final.csv
- **Created by**: Merging neuro-reviewer + mesh-validator results
- **Contains**: Complete enrichment (AI fields + MeSH terms)
- **Validation**: Had 7 errors found during first validation
- **Status**: Intermediate - superseded by corrected.csv

### A_NINDS_corrected.csv
- **Created by**: Applying first batch of corrections (7 errors fixed)
- **Validation**: Re-validation found 2 additional errors
- **Status**: Intermediate - superseded by final.csv

## Final File Location

The final validated data is in the parent directory:
- **`../A_NINDS_final.csv`** ✓ - Ready for integration (all validations passed)

## Why Archive These?

These intermediate files provide an audit trail showing:
1. How enrichment evolved through the workflow
2. What corrections were applied at each stage
3. Complete validation history

They are kept for reference but are not needed for database integration.

---

**Date Archived**: 2025-11-07
