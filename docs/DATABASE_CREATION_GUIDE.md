# Neuroscience Terminology Database Creation Guide

## What is Lex Stream?

Lex Stream is a web application designed to help neuroscientists search PubMed literature more effectively. It bridges the gap between simple keyword searches and expert-level query construction.

**Core Problem**: Neuroscientists need to search PubMed but:
- Simple keyword searches return too few (0 hits) or too many (1000s of hits) results
- Professional PubMed queries require complex Boolean logic and MeSH term expertise
- Users don't know neuroscience synonyms, abbreviations, or MeSH mappings

**Lex Stream Solution**: Accepts simple inclusion/exclusion concepts → generates expert-level PubMed queries → fetches and displays results

**Example Transformation**:
```
User Input:
  Include: "TMS, stroke, motor recovery"
  Exclude: "case reports"

Generated Query:
  (TMS[tiab] OR "transcranial magnetic stimulation"[tiab] OR
   "repetitive TMS"[tiab]) AND (stroke[MeSH] OR "cerebrovascular accident"[tiab])
   AND ("motor recovery"[tiab] OR "motor function"[tiab] OR rehabilitation[MeSH])
   NOT case reports[Publication Type]
```

## How Neuroscience Terminology Databases Are Used

The neuroscience terminology database (`neuro_terms.json`) is the **intelligence layer** that powers Lex Stream's 5-6 agent pipeline:

### Pipeline Architecture

```
User Input → Input Sanitizer → Spell Checker → Abbreviation Expander
→ Synonym Finder → [Component Detector] → Query Assembler → PubMed API
```

### Database Usage by Agent

#### 1. **Spell Checker Agent**
- **Uses**: `terms` + `synonyms` as high-confidence neuroscience dictionary
- **Purpose**: Detect misspellings in neuroscience terminology
- **Example**: "alzhiemers" → suggests "Alzheimer's" (from database)
- **Confidence**: Database matches = high confidence, general dictionary = medium

#### 2. **Abbreviation Expander Agent**
- **Uses**: `abbreviations` lookup map
- **Purpose**: Expand neuroscience abbreviations to full terms
- **Example**: "TMS" → "transcranial magnetic stimulation"
- **Logic**: Checks if user input matches abbreviations map, expands if found

#### 3. **Synonym Finder Agent**
- **Uses**: `synonyms` + `associated_terms` + `word_forms`
- **Purpose**: Broaden search coverage with related terminology
- **Example**: "memory" → adds "recall", "recognition", "mnemonic"
- **Conflict Detection**: Checks exclusions against inclusion terms/synonyms

#### 4. **MeSH Term Detector**
- **Uses**: `is_mesh_term` + `mesh_term` fields
- **Purpose**: Determine proper query field tags
- **Example**: "Acetylcholine" → gets `[MeSH]` tag instead of `[tiab]`
- **Impact**: MeSH terms search controlled vocabulary, broader coverage

#### 5. **Component Detector Agent** (Component-Based Mode)
- **Uses**: `associated_terms` + `definition` for semantic analysis
- **Purpose**: Categorize terms into Intervention, Condition, Outcome, Study Design
- **Example**: "TMS" → Intervention, "stroke" → Condition, "memory" → Outcome
- **Query Structure**: OR within components, AND between components

#### 6. **Query Assembler Agent**
- **Uses**: All database fields to construct final query
- **Purpose**: Apply proper field tags based on term type
- **Publication Types**: Exclusions like "case reports" get `[Publication Type]` tag
- **Example**: Combines all expanded/tagged terms into valid PubMed query syntax

### Database Structure

```json
{
  "terms": {
    "acetylcholine": {                    // Key: lowercase for case-insensitive lookup
      "primary_term": "Acetylcholine",    // Display name
      "definition": "A neurotransmitter...", // Helps component detection
      "synonyms": [                       // Alternative names
        "ACh neurotransmitter"
      ],
      "abbreviations": ["ACh"],           // Short forms
      "word_forms": {                     // Linguistic variations
        "noun": "acetylcholine",
        "adjective": "cholinergic",
        "uk_spelling": "Acetylcholine",
        "us_spelling": "Acetylcholine"
      },
      "associated_terms": [               // Related concepts
        "neurotransmitter",
        "nicotinic receptor",
        "muscarinic receptor"
      ],
      "is_mesh_term": true,               // MeSH status flag
      "mesh_term": "Acetylcholine",       // Official MeSH heading
      "secondary_term": "Acetylcholine"   // Alternative primary term
    }
  },
  "abbreviations": {                      // Fast abbreviation lookup
    "ach": {
      "expansion": "Acetylcholine",
      "definition": "A neurotransmitter..."
    }
  },
  "mesh_terms": {                         // Fast MeSH lookup
    "acetylcholine": "Acetylcholine"
  },
  "metadata": {
    "total_terms": 2847,
    "total_abbreviations": 1234,
    "total_mesh_terms": 1567,
    "source_file": "neuro_terms.xlsx"
  }
}
```

### Critical Implementation Details

1. **Case-Insensitive Lookups**: All dictionary keys are lowercase
2. **In-Memory Caching**: Database loaded once at startup (`services/terms_loader.py`)
3. **Required Fields**: terms, abbreviations, mesh_terms, metadata sections must exist
4. **File Size**: Current database ~500KB, loads in <100ms
5. **Validation**: Backend validates structure on startup, exits if invalid

---

## Instructions for Creating a New Database

### Context

You are creating a **new neuroscience terminology database** from a different source. This database will either:
- **Option A**: Be tested separately against the existing database
- **Option B**: Be merged with the existing database after validation

### Requirements

#### 1. Database Schema

**Required Structure**:
```json
{
  "terms": {},
  "abbreviations": {},
  "mesh_terms": {},
  "metadata": {}
}
```

**Term Entry Schema**:
```json
{
  "primary_term": "string (required)",      // Official term name
  "definition": "string (recommended)",     // Helps component detection
  "synonyms": ["string"],                   // Alternative names
  "abbreviations": ["string"],              // Short forms (e.g., "TMS")
  "word_forms": {                           // Linguistic variations
    "noun": "string",
    "verb": "string",
    "adjective": "string",
    "adverb": "string",
    "uk_spelling": "string",
    "us_spelling": "string"
  },
  "associated_terms": ["string"],           // Related concepts
  "is_mesh_term": boolean,                  // MeSH term flag
  "mesh_term": "string",                    // Official MeSH heading if applicable
  "secondary_term": "string"                // Alternative primary term
}
```

**Abbreviation Entry Schema**:
```json
{
  "expansion": "string (required)",         // Full term
  "definition": "string (recommended)"      // Definition
}
```

**Metadata Schema**:
```json
{
  "total_terms": int,
  "total_abbreviations": int,
  "total_mesh_terms": int,
  "source_file": "string",
  "source_name": "string"                   // NEW - track provenance
}
```

#### 2. Data Quality Standards

**Required**:
- All `terms` dictionary keys must be lowercase
- All `abbreviations` dictionary keys must be lowercase
- All `mesh_terms` dictionary keys must be lowercase
- No null or empty `primary_term` values
- All entries must have at least `primary_term` and `definition`

**Recommended**:
- Verify MeSH terms against NLM MeSH database
- Include comprehensive synonyms for common neuroscience concepts
- Populate `associated_terms` for component detection accuracy
- Include UK/US spelling variations where applicable
- Provide detailed definitions for semantic analysis

**Data Enrichment**:
- **Synonyms**: Include scientific and colloquial terms
- **Abbreviations**: All common neuroscience abbreviations
- **Associated Terms**: Include:
  - Broader concepts (e.g., "dopamine" → "neurotransmitter")
  - Related techniques (e.g., "TMS" → "neuromodulation")
  - Common co-occurring terms
  - Measurement outcomes
  - Clinical applications

#### 3. Conversion Process

**Step 1: Create Conversion Script**

Use `convert_new_database.py` as a template:

```python
#!/usr/bin/env python3
"""
Convert [SOURCE_NAME] database to Lex Stream format.
"""
import json
from pathlib import Path

def convert_entry(source_entry):
    """Convert a single entry from source format to Lex Stream format."""

    # Extract primary term
    primary_term = source_entry.get("term_field").strip()
    if not primary_term:
        return None, None

    # Lowercase key for case-insensitive lookup
    key = primary_term.lower()

    # Build Lex Stream format
    converted = {
        "primary_term": primary_term,
        "definition": source_entry.get("definition", ""),
        "synonyms": extract_synonyms(source_entry),
        "abbreviations": extract_abbreviations(source_entry),
        "word_forms": extract_word_forms(source_entry),
        "associated_terms": extract_associated_terms(source_entry),
        "is_mesh_term": check_mesh_status(source_entry),
        "mesh_term": source_entry.get("mesh", ""),
        "secondary_term": source_entry.get("alt_term", primary_term)
    }

    return key, converted

# Implement conversion logic...
```

**Step 2: Generate Output File**

```bash
python convert_[source_name]_database.py input.json neuro_terms_[source].json
```

**Recommended Filename Format**: `neuro_terms_[source_name].json`
- Example: `neuro_terms_ncbi.json`
- Example: `neuro_terms_umls.json`

#### 4. Validation Checklist

Before submitting the database:

- [ ] **Structure Validation**
  - [ ] Has all 4 required sections: terms, abbreviations, mesh_terms, metadata
  - [ ] All dictionary keys are lowercase
  - [ ] No duplicate keys in any section
  - [ ] Metadata counts match actual entries

- [ ] **Data Quality**
  - [ ] All entries have primary_term
  - [ ] Definitions are informative (>10 words)
  - [ ] Synonyms are accurate and comprehensive
  - [ ] Abbreviations are standard neuroscience usage
  - [ ] MeSH terms verified (if possible)

- [ ] **Technical Validation**
  - [ ] Valid JSON syntax (use `json.load()` to verify)
  - [ ] UTF-8 encoding
  - [ ] No trailing commas
  - [ ] File size reasonable (<5MB)

- [ ] **Functional Testing**
  - [ ] Loads successfully with `services/terms_loader.py`
  - [ ] Sample spell check queries work
  - [ ] Sample abbreviation expansions work
  - [ ] Sample MeSH lookups work

#### 5. Testing Procedure

**Create Test Script** (`test_new_database.py`):

```python
#!/usr/bin/env python3
"""Test new neuroscience database."""
import json

# Load database
with open('neuro_terms_[source].json', 'r') as f:
    db = json.load(f)

# Test structure
assert 'terms' in db
assert 'abbreviations' in db
assert 'mesh_terms' in db
assert 'metadata' in db

# Test sample lookups
assert 'acetylcholine' in db['terms']
assert 'ach' in db['abbreviations']

# Test data quality
for key, term in list(db['terms'].items())[:10]:
    assert key == key.lower(), f"Key not lowercase: {key}"
    assert term['primary_term'], f"Missing primary_term: {key}"
    assert len(term['definition']) > 10, f"Short definition: {key}"

print("✓ All tests passed")
```

**Run Tests**:
```bash
python test_new_database.py
```

#### 6. Integration Options

**Option A: Separate Database (Recommended for Testing)**

1. Save as `neuro_terms_[source].json`
2. Create comparison script to measure quality differences
3. Test pipeline accuracy with both databases
4. Compare metrics:
   - Spell check accuracy
   - Abbreviation expansion coverage
   - MeSH detection rate
   - Component categorization quality
   - Query result quality

**Option B: Merge with Existing Database**

Only after Option A validation passes:

1. Identify conflicts (duplicate terms/abbreviations)
2. Resolve conflicts:
   - Compare definition quality
   - Merge synonyms and abbreviations
   - Prefer MeSH-verified entries
   - Document source priority decisions
3. Update metadata to track multi-source origin
4. Validate merged database
5. Run full test suite

### Deliverables

1. **Conversion Script**: `convert_[source]_database.py`
2. **Output Database**: `neuro_terms_[source].json`
3. **Validation Report**: Document showing:
   - Total entries created
   - Data quality metrics
   - Sample entries (5-10)
   - Comparison with existing database (if applicable)
   - Known issues or limitations
4. **Test Results**: Output from validation tests

### Questions to Answer

When submitting the database, provide answers to:

1. **Source**: Where did this data come from?
2. **Coverage**: What neuroscience domains are covered?
3. **Quality**: How were terms/definitions validated?
4. **MeSH Status**: How were MeSH terms verified?
5. **Conflicts**: Any duplicate/conflicting entries with existing database?
6. **Limitations**: What neuroscience areas are missing?
7. **Recommendations**: Should this replace, merge with, or complement existing database?

---

## Reference Files

- **Current Database**: `/Users/sam/Lex-stream-2/neuro_terms.json`
- **Conversion Example**: `/Users/sam/Lex-stream-2/convert_new_database.py`
- **Loader Service**: `/Users/sam/Lex-stream-2/services/terms_loader.py`
- **Project Constitution**: `/Users/sam/Lex-stream-2/CLAUDE.md`

## Support

For questions about database structure or integration, refer to:
- This guide
- Existing conversion scripts in the repository
- Pipeline agent implementations in `agents.py`
