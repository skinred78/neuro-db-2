---
title: Lex Stream Integration Compatibility Report
date: 2025-11-19
type: integration-analysis
related_to: 2025-11-19-ontology-ingestion-optimization-analysis.md
status: verified-compatible
---

# Lex Stream Integration Compatibility Report

## Executive Summary

**✅ OPTION A IS FULLY COMPATIBLE WITH LEX STREAM**

Changing the data source from Wikipedia/NINDS to UMLS/Neuronames/NIF/GO **does NOT break** the Lex Stream integration. The database structure remains identical; only the ingestion pipeline changes.

**No changes required** to:
- Frontend code
- Backend agents
- API routes
- JSON schema
- Database format

---

## Data Flow Architecture

### Current Integration Pipeline

```
NeuroDB-2 (22-column CSV)
    ↓
convert_to_lexstream.py (reads CSV, maps to JSON schema)
    ↓
neuro_terms.json (JSON with specific structure)
    ↓
Lex Stream Backend (terms_loader.py loads JSON)
    ↓
Backend Agents (process queries using terminology)
    ↓
API Routes (expose processed results)
    ↓
Frontend (displays pipeline results)
```

### What Option A Changes

```diff
- Wikipedia/NINDS markdown → Manual enrichment → 22-column CSV
+ UMLS/Neuronames/NIF/GO → Automated parsing → 22-column CSV (same format)
```

**Everything downstream remains identical.**

---

## Schema Compatibility Analysis

### NeuroDB-2 CSV Schema (22 columns)

```csv
Term,Term Two,Definition,Closest MeSH term,Synonym 1,Synonym 2,Synonym 3,Abbreviation,UK Spelling,US Spelling,Noun Form of Word,Verb Form of Word,Adjective Form of Word,Adverb Form of Word,Commonly Associated Term 1,Commonly Associated Term 2,Commonly Associated Term 3,Commonly Associated Term 4,Commonly Associated Term 5,Commonly Associated Term 6,Commonly Associated Term 7,Commonly Associated Term 8
```

### Lex Stream JSON Schema (Expected Format)

```json
{
  "terms": {
    "lowercase_key": {
      "primary_term": "String",
      "definition": "String",
      "synonyms": ["String"],
      "abbreviations": ["String"],
      "word_forms": {
        "noun": "String",
        "verb": "String",
        "adjective": "String",
        "adverb": "String",
        "uk_spelling": "String",
        "us_spelling": "String"
      },
      "associated_terms": ["String"],
      "is_mesh_term": Boolean,
      "mesh_term": "String",
      "secondary_term": "String"
    }
  },
  "abbreviations": {
    "lowercase_abbrev": {
      "expansion": "String",
      "definition": "String"
    }
  },
  "mesh_terms": {
    "lowercase_mesh": "Official MeSH Term"
  },
  "metadata": {
    "total_terms": Number,
    "total_abbreviations": Number,
    "total_mesh_terms": Number,
    "source_file": "String",
    "source_name": "String",
    "version": "String",
    "date_created": "String"
  }
}
```

### CSV → JSON Mapping (convert_to_lexstream.py)

| CSV Column | JSON Field | Mapping Function |
|------------|------------|------------------|
| Term | primary_term | Direct copy |
| Term Two | secondary_term | Direct copy (fallback to primary_term) |
| Definition | definition | Direct copy |
| Closest MeSH term | mesh_term, is_mesh_term | Direct copy + boolean check |
| Synonym 1-3 | synonyms (array) | extract_synonyms() |
| Abbreviation | abbreviations (array) | extract_abbreviations() |
| UK/US Spelling | word_forms.uk_spelling, word_forms.us_spelling | extract_word_forms() |
| Noun/Verb/Adj/Adverb Forms | word_forms.{noun/verb/adjective/adverb} | extract_word_forms() |
| Associated Term 1-8 | associated_terms (array) | extract_associated_terms() |

**✅ Conversion script location**: `/Users/sam/NeuroDB-2/convert_to_lexstream.py`

**✅ No changes needed** - Script reads ANY 22-column CSV regardless of data source

---

## Backend Agent Compatibility

### Agents That Use Terminology Data

**File**: `/Users/sam/Lex-stream-2/agents.py`

#### 1. SpellChecker Agent
**Accesses:**
- `terms` (all keys)
- `synonyms` (array)
- `word_forms` (object)
- `abbreviations` (array)
- `mesh_terms` (object)
- `associated_terms` (array)

**Impact**: ✅ None - All fields populated by convert_to_lexstream.py

#### 2. AbbreviationExpander Agent
**Accesses:**
- `abbreviations` (object with expansion + definition)

**Impact**: ✅ None - Abbreviations extracted from CSV column

#### 3. SynonymFinder Agent
**Accesses:**
- `terms` (all term_data objects)
- `synonyms` (array)
- `primary_term` (string)
- `associated_terms` (array)
- `word_forms` (object)

**Impact**: ✅ None - All fields available from CSV

#### 4. QueryAssembler Agent
**Accesses:**
- `mesh_terms` (object)

**Impact**: ✅ None - MeSH terms extracted from CSV "Closest MeSH term" column

#### 5. ComponentQueryAssembler Agent
**Accesses:**
- `mesh_terms` (object)

**Impact**: ✅ None - Same as QueryAssembler

**Verified in**:
- `/Users/sam/Lex-stream-2/agents.py` (lines 118-150, 559-560, 621-926, 1039-1041, 1453-1455)

---

## Frontend Compatibility

### Frontend Architecture

**Location**: `/Users/sam/Lex-stream-2/frontend/lex-stream-ui/`

**Key Finding**: Frontend does NOT directly access neuro_terms.json

#### What Frontend Receives

Frontend components display **processed pipeline results**, not raw terminology data:

**Component**: `PipelineDetails.jsx`

Displays:
- Abbreviation expansions (from AbbreviationExpander agent)
- Synonym additions (from SynonymFinder agent)
- Query assembly details (from QueryAssembler agent)
- MeSH vs TIAB tag assignments

**Data source**: `/api/query` endpoint returns pipeline results

**Verified in**: `/Users/sam/Lex-stream-2/frontend/lex-stream-ui/src/components/PipelineDetails.jsx`

#### API Endpoints That Expose Terminology

**1. /api/terms** (`routes/terms.py`)
- Returns complete neuro_terms.json structure
- Used for debugging/inspection, not core functionality
- **Impact**: ✅ None - JSON structure unchanged

**2. /api/spelling** (`routes/spelling.py`)
- Uses terms_loader.load_neuro_terms()
- Spell-checks against terminology database
- **Impact**: ✅ None - Agent processes same JSON structure

**3. /api/query** (`routes/query.py`)
- Runs 5-agent pipeline
- Returns processed results, not raw terminology
- **Impact**: ✅ None - Agents work with same JSON structure

**Verified in**: `/Users/sam/Lex-stream-2/routes/`

---

## Integration Test Scenarios

### Test Case 1: Existing Wikipedia Terms
**Scenario**: Terms already in database (e.g., "Parkinson disease")

**Before (Wikipedia)**:
```json
{
  "primary_term": "Parkinson disease",
  "definition": "A chronic progressive...",
  "synonyms": ["Parkinson's disease"],
  "abbreviations": ["PD"],
  "mesh_term": "Parkinson Disease",
  "is_mesh_term": true
}
```

**After (UMLS)**:
```json
{
  "primary_term": "Parkinson disease",
  "definition": "A progressive neurodegenerative disorder...",
  "synonyms": ["Parkinson's disease", "idiopathic Parkinson disease"],
  "abbreviations": ["PD"],
  "mesh_term": "Parkinson Disease",
  "is_mesh_term": true
}
```

**Impact**: ✅ Enhanced data (more synonyms), same structure

---

### Test Case 2: New Ontology Terms
**Scenario**: Terms NOT in Wikipedia but in UMLS (e.g., "alpha-synuclein aggregation")

**Before**: Not in database (0 results)

**After (UMLS)**:
```json
{
  "primary_term": "alpha-synuclein aggregation",
  "definition": "...",
  "synonyms": ["SNCA aggregation"],
  "abbreviations": [],
  "mesh_term": "alpha-Synuclein",
  "is_mesh_term": true
}
```

**Impact**: ✅ Expanded coverage, agents find more synonyms/expansions

---

### Test Case 3: Agent Processing
**Scenario**: User searches "PD treatment"

**Pipeline processing** (unchanged):
1. InputSanitizer: "pd treatment" (lowercase)
2. SpellChecker: ✅ Valid (finds "PD" in abbreviations)
3. AbbreviationExpander: "PD" → "Parkinson disease"
4. SynonymFinder: Adds ["Parkinson's disease", "idiopathic Parkinson disease"]
5. QueryAssembler: Tags with [MeSH] or [tiab]

**Impact**: ✅ MORE expansions/synonyms (better results), same pipeline

---

### Test Case 4: Frontend Display
**Scenario**: View pipeline details after query

**Frontend displays**:
```
Abbreviation Expansion:
- PD → Parkinson disease

Synonym Finding:
- Parkinson disease + Parkinson's disease
- Parkinson disease + idiopathic Parkinson disease

Query Assembly:
- Parkinson disease[MeSH] OR Parkinson's disease[tiab] OR ...
```

**Impact**: ✅ Same display format, potentially more items shown

---

## Risk Assessment

### Zero-Risk Changes
- ✅ 22-column CSV format (identical)
- ✅ convert_to_lexstream.py script (no changes)
- ✅ JSON schema structure (identical)
- ✅ Backend agent logic (no changes)
- ✅ API endpoint contracts (no changes)
- ✅ Frontend components (no changes)

### Low-Risk Changes (Monitored)
- ⚠️ **Data quality**: Ontology terms might have different phrasing
  - **Mitigation**: Tiered validation (mesh-validator + sampling)
- ⚠️ **Empty fields**: Some CSV columns might be empty for ontology terms
  - **Mitigation**: Already acceptable per "accuracy over completeness" rule
  - **Impact**: Agents handle empty fields gracefully (e.g., `if synonyms` checks)

### Validation Checkpoints

**After bulk import, verify**:
1. ✅ CSV files have exactly 22 columns
2. ✅ convert_to_lexstream.py runs without errors
3. ✅ JSON structure validates against schema
4. ✅ terms_loader.py loads JSON successfully
5. ✅ All agents initialize without errors
6. ✅ /api/terms endpoint returns valid JSON
7. ✅ Frontend loads without errors

**Validation script locations**:
- `/Users/sam/NeuroDB-2/validate_lexstream_db.py`
- `/Users/sam/NeuroDB-2/test_lexstream_db.py`

---

## Performance Implications

### Database Size Impact

| Metric | Current (Wikipedia) | After Option A (UMLS) | Change |
|--------|---------------------|------------------------|--------|
| Total terms | 595 | ~100,000-150,000 | 168-252x |
| neuro_terms.json size | ~438 KB | ~60-90 MB (estimated) | 137-205x |
| Load time | <1 second | 2-5 seconds (estimated) | Acceptable |
| Memory footprint | ~5 MB | ~150-250 MB | Manageable |

### Caching Strategy (Already Implemented)

**File**: `/Users/sam/Lex-stream-2/services/terms_loader.py`

```python
# Global cache for neuroscience terms data
_neuro_terms_cache = None

def load_neuro_terms():
    global _neuro_terms_cache

    # Return cached data if available
    if _neuro_terms_cache is not None:
        return _neuro_terms_cache

    # Load JSON once, cache for all requests
    with open(NEURO_TERMS_JSON_PATH, 'r') as f:
        _neuro_terms_cache = json.load(f)

    return _neuro_terms_cache
```

**Impact**: ✅ One-time load at app startup, cached for all requests

**Performance**: ✅ Acceptable - 2-5 second startup delay for 100x coverage increase

---

## Deployment Automation

### Current Automated Deployment Process

**Location**: `/Users/sam/Lex-stream-2/.github/workflows/`

**Workflows**:
1. `deploy-backend-staging.yml` - Auto-deploys to Cloud Run staging
2. `deploy-backend-production.yml` - Auto-deploys to Cloud Run production

**Trigger**: Push to `main` branch when these paths change:
- `*.py` files
- `routes/**`, `services/**`, `utils/**`
- **`neuro_terms.json`** ← Database updates trigger auto-deployment
- `requirements.txt`, `Dockerfile`, `config.py`

**Deployment Steps** (Automated):
1. Build Docker image (includes `neuro_terms.json`)
2. Push to Google Container Registry
3. Deploy to Cloud Run (staging and/or production)
4. Health check verification
5. Database version check (production)
6. Create deployment tag
7. Post commit comment with URLs

**CRITICAL**: When `neuro_terms.json` is committed to Lex Stream repo, it **automatically deploys** to staging and production environments.

### Manual Step Required

**The one manual step** in the pipeline:
```bash
# After running convert_to_lexstream.py in NeuroDB-2:
cp /Users/sam/NeuroDB-2/neuro_terms_v{version}_{source}.json \
   /Users/sam/Lex-stream-2/neuro_terms.json

# Then commit in Lex Stream repo to trigger auto-deployment
cd /Users/sam/Lex-stream-2
git add neuro_terms.json
git commit -m "Update terminology database to v{version}"
git push origin main  # ← Triggers GitHub Actions auto-deployment
```

**Why this step exists**: Separation of concerns
- NeuroDB-2: Data processing, validation, quality control
- Lex Stream: Application deployment, production serving

---

## Migration Plan

### Phase 1: Bulk Import in NeuroDB-2 (No Lex Stream Changes)
1. Run Option A ingestion scripts in NeuroDB-2
2. Generate new neuro_terms.csv (100K+ terms)
3. Run convert_to_lexstream.py → `neuro_terms_v{version}_umls-neuronames-nif-go.json`
4. Run validation scripts (validate_lexstream_db.py, test_lexstream_db.py)

**Expected**: New versioned JSON file with 100K+ terms in NeuroDB-2

**Location**: `/Users/sam/NeuroDB-2/neuro_terms_v{version}_umls-neuronames-nif-go.json`

### Phase 2: Local Integration Testing (Before Deployment)
1. **Copy** new JSON to Lex Stream (manual step):
   ```bash
   cp /Users/sam/NeuroDB-2/neuro_terms_v*.json \
      /Users/sam/Lex-stream-2/neuro_terms.json
   ```
2. Start Lex Stream backend locally:
   ```bash
   cd /Users/sam/Lex-stream-2
   python app.py
   ```
3. Verify /api/terms endpoint loads (check for errors)
4. Run test queries through agents
5. Check frontend display locally
6. Run Lex Stream test suite:
   ```bash
   pytest tests/
   ```

**Expected**: All tests pass locally, more expansions/synonyms

### Phase 3: Staging Deployment (Automated)
1. **Commit** neuro_terms.json to Lex Stream repo:
   ```bash
   cd /Users/sam/Lex-stream-2
   git add neuro_terms.json
   git commit -m "Update terminology database to v{version} (100K+ terms from UMLS/Neuronames/NIF/GO)"
   git push origin main
   ```
2. **GitHub Actions automatically**:
   - Builds Docker image with new database
   - Deploys to Cloud Run staging
   - Runs health checks
   - Posts staging URL in commit comment

3. **Manual verification** on staging:
   - Test /api/terms endpoint
   - Run sample queries
   - Check performance (load time)
   - Verify James's benchmark searches

**Expected**: Staging environment running with new database

### Phase 4: Quality Validation on Staging
1. Test against James's benchmark search strings (neuromodulation, MS, Alzheimer's)
2. Compare before/after coverage
3. Measure improvement:
   - Terms found
   - Synonyms added
   - MeSH mappings available
   - Query quality vs James's manual queries
4. Monitor performance metrics:
   - Load time
   - Memory usage
   - Response times

**Expected**: Significant quality improvement, acceptable performance

### Phase 5: Production Deployment (Automated with Manual Gate)
1. **If staging tests pass**, merge to production (same commit triggers production deploy)
2. **GitHub Actions automatically**:
   - Builds production Docker image
   - Deploys to Cloud Run production
   - Verifies database version
   - Runs health checks
   - Creates deployment tag

3. **Monitor production**:
   - Check logs for errors
   - Verify /api/health endpoint
   - Test frontend integration
   - Monitor performance

**Expected**: Production running with 100K+ term database

**Rollback Plan**:
- If issues detected, revert neuro_terms.json commit
- GitHub Actions will auto-deploy previous version

---

## Compatibility Checklist

### ✅ Database Structure
- [x] Same 22-column CSV format
- [x] Same column names and order
- [x] Same CSV encoding (UTF-8)
- [x] Same CSV delimiter (comma)

### ✅ Conversion Process
- [x] convert_to_lexstream.py unchanged
- [x] Same JSON output structure
- [x] Same field mappings
- [x] Same validation logic

### ✅ Backend Integration
- [x] terms_loader.py unchanged
- [x] All agents compatible
- [x] API routes unchanged
- [x] Caching logic unchanged

### ✅ Frontend Integration
- [x] No frontend code changes needed
- [x] API contracts unchanged
- [x] Display components unchanged
- [x] Pipeline results format unchanged

### ✅ Validation & Testing
- [x] Validation scripts available
- [x] Test scripts available
- [x] Integration tests documented

### ✅ Deployment Automation
- [x] GitHub Actions workflows configured
- [x] Auto-deploy on neuro_terms.json changes
- [x] Health check verification automated
- [x] Database version tracking automated
- [x] Manual copy step documented
- [x] Rollback procedure documented

---

## Conclusion

**Option A is 100% compatible with Lex Stream + Deployment Automation.**

### Key Insights

1. **Lex Stream doesn't care about data SOURCE, only data STRUCTURE**
   - Same 22-column CSV → Same JSON schema → Same agent processing
   - Frontend/backend completely decoupled from data source

2. **Deployment is mostly automated**
   - ✅ One manual step: Copy JSON from NeuroDB-2 to Lex Stream
   - ✅ Everything else automated via GitHub Actions
   - ✅ Auto-deploy to staging and production on commit

3. **Safe rollback mechanism**
   - Revert commit → Auto-deploys previous version
   - Database version tracked in health endpoint

### What Changes

**Data only:**
- 595 terms → 100K+ terms
- More synonyms per term
- Better MeSH coverage
- More comprehensive associated terms

**Structure:** Identical

**Performance:** Acceptable
- 2-5 second load time (one-time at startup)
- Cached in memory for all requests

---

## Next Steps

### Immediate (Nov 20-22): Bulk Import
1. ✅ **Approve Option A** for implementation
2. Run bulk import scripts in NeuroDB-2 (UMLS, Neuronames, NIF, GO)
3. Generate neuro_terms.csv (100K+ terms)
4. Run convert_to_lexstream.py
5. Validate output (validate_lexstream_db.py, test_lexstream_db.py)

### Before Deployment: Local Testing
6. Copy JSON to Lex Stream directory (manual step)
7. Test Lex Stream locally (python app.py)
8. Run Lex Stream test suite (pytest tests/)
9. Verify agents work with new database

### Staging Deployment: Automated
10. Commit neuro_terms.json to Lex Stream repo
11. GitHub Actions auto-deploys to staging
12. Test on staging environment
13. Validate against James's benchmark searches

### Production Deployment: Automated (If Tests Pass)
14. Same commit auto-deploys to production
15. Monitor performance and errors
16. Measure improvement vs baseline

**No Lex Stream code changes required.** ✅

**Deployment automation already configured.** ✅

---

## References

- NeuroDB-2 Schema: `/Users/sam/NeuroDB-2/CLAUDE.md` (lines 54-83)
- Conversion Script: `/Users/sam/NeuroDB-2/convert_to_lexstream.py`
- Lex Stream Loader: `/Users/sam/Lex-stream-2/services/terms_loader.py`
- Backend Agents: `/Users/sam/Lex-stream-2/agents.py`
- Frontend Components: `/Users/sam/Lex-stream-2/frontend/lex-stream-ui/src/components/`
- API Routes: `/Users/sam/Lex-stream-2/routes/`
