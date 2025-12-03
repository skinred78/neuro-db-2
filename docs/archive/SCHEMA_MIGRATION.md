# Schema Migration: 19 to 22 Columns

## Overview
On 2025-10-22, the schema was expanded from 19 to 22 columns to accommodate more commonly associated terms.

## Changes
- **Old schema**: 5 associated term columns (columns 15-19)
- **New schema**: 8 associated term columns (columns 15-22)
- **Added columns**: 
  - Commonly Associated Term 6
  - Commonly Associated Term 7
  - Commonly Associated Term 8

## File Status

### 19-Column Files (Legacy - Need Backfill)
- B.csv (22 terms)
- C.csv (26 terms)
- D.csv (22 terms)
- E.csv (23 terms)
- F.csv (15 terms)
- **Total**: 108 terms

### 22-Column Files (Current Schema)
- G.csv onwards will use new schema
- **Status**: Starting with letter G

## Migration Plan

### Phase 1: Complete G-Z (In Progress)
Continue processing letters G through Z with the new 22-column schema.

### Phase 2: Backfill B-F (After Z Complete)
1. Read each B-F file
2. Add 3 empty columns at the end
3. Optionally enrich with additional associated terms
4. Save updated files

### Phase 3: Merge & Export
1. Verify all files have 22 columns
2. Merge into neuro_terms.csv
3. Generate neuro_terms.json

## Rationale
Analysis showed 75.5% of terms (83/110) were using all 5 associated term slots, indicating the limit was too restrictive. Expanding to 8 slots will accommodate ~95% of terms without constraint while maintaining reasonable data density.

## Commands
To backfill after completing Z:
```
# User command
backfill B-F

# Or
add columns to B-F
```
