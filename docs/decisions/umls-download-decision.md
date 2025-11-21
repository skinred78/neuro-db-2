# UMLS Download Decision

**Date**: 2025-11-20
**Decision**: Which UMLS file(s) to download for NeuroDB-2 import

---

## Files Required for Our Implementation

According to both plans (mine and planner agent's), we need these 4 RRF files:

1. **MRCONSO.RRF** - Concept names, synonyms, abbreviations, source codes
2. **MRDEF.RRF** - Definitions
3. **MRREL.RRF** - Related concepts (CRITICAL for DEC-001 profiling)
4. **MRSTY.RRF** - Semantic types (for filtering 4M → 100K-150K concepts)

---

## Available Download Options

### Option 1: MRCONSO.RRF Only ❌ INSUFFICIENT
- **Size**: 472 MB compressed → 2.1 GB uncompressed
- **URL**: https://download.nlm.nih.gov/umls/kss/2025AB/umls-2025AB-mrconso.zip
- **Contains**: Only MRCONSO.RRF
- **Missing**: MRDEF, MRREL, MRSTY
- **Verdict**: ❌ Not enough - missing 3 critical files

### Option 2: UMLS Metathesaurus Level 0 Subset ⚠️ LIMITED
- **Size**: 1.8 GB compressed → 10.3 GB uncompressed
- **URL**: https://download.nlm.nih.gov/umls/kss/2025AB/umls-2025AB-metathesaurus-level-0.zip
- **Contains**: All META/ RRF files, but only Level 0 source vocabularies
- **Level 0 Sources**: Vocabularies with no additional restrictions (subset of all sources)
- **Missing**: Terms from restricted sources (may miss some neuroscience content)
- **Verdict**: ⚠️ Usable but may have lower term count than expected

### Option 3: UMLS Metathesaurus Full Subset ✅ RECOMMENDED
- **Size**: 5.2 GB compressed → 35.8 GB uncompressed
- **URL**: https://download.nlm.nih.gov/umls/kss/2025AB/umls-2025AB-metathesaurus-full.zip
- **Contains**: Complete Metathesaurus with all RRF files (MRCONSO, MRDEF, MRREL, MRSTY, etc.)
- **Includes**: All source vocabularies (MSH, SNOMEDCT_US, NCI, GO, HPO, OMIM, etc.)
- **Missing**: MetamorphoSys (not needed), Semantic Network files (not needed), Specialist Lexicon (not needed)
- **Verdict**: ✅ **PERFECT for our needs**

### Option 4: Full Release ⚠️ OVERKILL
- **Size**: 5.2 GB compressed → 37.8 GB uncompressed
- **URL**: https://download.nlm.nih.gov/umls/kss/2025AB/umls-2025AB-full.zip
- **Contains**: Everything in Option 3 PLUS MetamorphoSys, Semantic Network, Specialist Lexicon
- **Extra**: MetamorphoSys (requires 40 GB disk, 2-10 hours to run)
- **Verdict**: ⚠️ Same Metathesaurus content as Option 3, but with unnecessary extras

---

## Recommendation: Option 3 (Full Subset)

**Download**: `umls-2025AB-metathesaurus-full.zip`

### Why This Option?

✅ **Has all 4 required files**: MRCONSO, MRDEF, MRREL, MRSTY
✅ **Complete source coverage**: All vocabularies including MSH, SNOMEDCT_US, NCI
✅ **No installation needed**: Direct RRF file access
✅ **Reasonable size**: 5.2 GB compressed (vs 37.8 GB for full release)
✅ **No bloat**: Excludes MetamorphoSys, Semantic Network (not needed)

### What We'll Get

**Expected file structure after extraction**:
```
umls-2025AB-metathesaurus-full/
├── META/
│   ├── MRCONSO.RRF    (~16M rows, 2.1 GB)
│   ├── MRDEF.RRF      (~1.2M rows, 600 MB)
│   ├── MRREL.RRF      (~60M rows, 2 GB)
│   ├── MRSTY.RRF      (~2M rows, 40 MB)
│   ├── MRSAB.RRF      (source info)
│   ├── MRSAT.RRF      (attributes)
│   └── ... (other files we don't need)
└── README.txt
```

### Disk Space Requirements

- **Download**: 5.2 GB (compressed)
- **Extraction**: 35.8 GB (uncompressed)
- **Working space**: ~10 GB (intermediate files during import)
- **Total needed**: ~51 GB free disk space

---

## Alternative: Level 0 Subset (If Disk-Limited)

If 51 GB is too much, Option 2 (Level 0 Subset) is acceptable:

**Pros**:
- Smaller: 1.8 GB compressed → 10.3 GB uncompressed
- Still has all 4 required files
- Faster download and extraction

**Cons**:
- Missing some restricted source vocabularies
- May result in 70K-100K terms instead of 100K-150K
- Could miss some rare neuroscience concepts

**When to use**:
- Disk space < 50 GB available
- Fast prototyping / testing
- Can upgrade to Full Subset later if needed

---

## Files We DON'T Need

❌ **MetamorphoSys** (excluded in Option 3) - GUI tool for subsetting, we're writing custom Python filters
❌ **Semantic Network** (SN, SRDEF, SRSTR files) - We only need MRSTY for filtering
❌ **Specialist Lexicon** - Linguistic tools, not needed for term extraction
❌ **History files** - Only needed for change tracking across versions

---

## Download Command

```bash
# Create directory
mkdir -p downloads/umls/2025AB

# Download (requires UMLS license login)
cd downloads/umls/2025AB
curl -O https://download.nlm.nih.gov/umls/kss/2025AB/umls-2025AB-metathesaurus-full.zip

# Verify checksum
echo "494e5ab4a9b0cb5c60f40fea999abef4  umls-2025AB-metathesaurus-full.zip" | md5sum -c

# Extract
unzip umls-2025AB-metathesaurus-full.zip

# Verify files exist
ls -lh META/MRCONSO.RRF
ls -lh META/MRDEF.RRF
ls -lh META/MRREL.RRF
ls -lh META/MRSTY.RRF
```

---

## Decision

**File to Download**: `umls-2025AB-metathesaurus-full.zip` (Option 3)

**URL**: https://download.nlm.nih.gov/umls/kss/2025AB/umls-2025AB-metathesaurus-full.zip

**Size**: 5.2 GB compressed → 35.8 GB uncompressed

**Rationale**:
- Contains all 4 required RRF files
- Complete source vocabulary coverage
- No unnecessary extras (MetamorphoSys, etc.)
- Reasonable disk space (51 GB total with working space)

**Fallback**: If disk-limited, use Level 0 Subset (Option 2)

---

## Next Steps

1. **Confirm disk space**: Verify 51+ GB available
2. **Download**: Use curl or browser (requires UMLS license authentication)
3. **Verify checksum**: MD5 `494e5ab4a9b0cb5c60f40fea999abef4`
4. **Extract**: Unzip to `downloads/umls/2025AB/`
5. **Verify files**: Check all 4 RRF files present and readable
6. **Proceed to Phase 2**: Build filtering index with `scripts/build_umls_filter_index.py`
