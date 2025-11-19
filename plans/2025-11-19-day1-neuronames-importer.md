# Day 1 Implementation: Neuronames Importer

## Objective

Build Neuronames importer with source tagging infrastructure to process ~3,000 neuroanatomy terms.

## Deliverables

1. **Core Infrastructure** (`scripts/lib/`)
   - `schema_mapper.py` - Maps ontology fields → NeuroDB-2 26-column schema
   - `source_tagger.py` - Adds source metadata (source, priority, date)
   - `validators.py` - Structural validation (column count, encoding, duplicates)

2. **Neuronames Importer** (`scripts/import_neuronames.py`)
   - Downloads JSON from http://braininfo.rprc.washington.edu/nnont.aspx
   - Parses neuroanatomy structure data
   - Maps to extended 26-column schema
   - Outputs: `imports/neuronames/neuronames_imported.csv`

3. **Test Output**
   - ~3,000 terms with source tags
   - Validated structure (26 columns)
   - Ready for future merging

## Extended Schema (26 columns)

**Standard 22 columns** (unchanged):
- Term, Term Two, Definition, Closest MeSH term
- Synonym 1-3, Abbreviation
- UK/US Spelling
- Word Forms (Noun, Verb, Adjective, Adverb)
- Associated Terms 1-8

**New 4 metadata columns**:
- `source` - Single primary source (e.g., "neuronames")
- `source_priority` - Integer 1-3 (1=highest)
- `sources_contributing` - Comma-separated if merged (e.g., "neuronames,umls")
- `date_added` - ISO 8601 format (YYYY-MM-DD)

## Implementation Steps

### Step 1: Create Core Infrastructure

**File: `scripts/lib/schema_mapper.py`**
```python
NEURODB_SCHEMA = [
    'Term', 'Term Two', 'Definition', 'Closest MeSH term',
    'Synonym 1', 'Synonym 2', 'Synonym 3', 'Abbreviation',
    'UK Spelling', 'US Spelling',
    'Noun Form of Word', 'Verb Form of Word',
    'Adjective Form of Word', 'Adverb Form of Word',
    'Commonly Associated Term 1', 'Commonly Associated Term 2',
    'Commonly Associated Term 3', 'Commonly Associated Term 4',
    'Commonly Associated Term 5', 'Commonly Associated Term 6',
    'Commonly Associated Term 7', 'Commonly Associated Term 8',
    'source', 'source_priority', 'sources_contributing', 'date_added'
]

def create_empty_row():
    """Returns dict with all 26 columns initialized to empty strings."""

def map_neuronames_to_schema(neuronames_entry):
    """Maps Neuronames JSON fields to NeuroDB-2 schema."""
```

**File: `scripts/lib/source_tagger.py`**
```python
SOURCE_PRIORITIES = {
    'umls': 1,
    'neuronames': 2,
    'nif': 2,
    'gene_ontology': 2,
    'wikipedia': 3,
    'ninds': 3
}

def add_source_metadata(row, source_name):
    """Adds source, priority, and date to row."""

def merge_sources(existing_row, new_row):
    """Handles multi-source conflicts and merging."""
```

**File: `scripts/lib/validators.py`**
```python
def validate_structure(csv_path):
    """Validates column count (26), encoding (UTF-8), duplicates."""

def validate_required_fields(csv_path):
    """Checks Term and Definition are non-empty."""

def generate_validation_report(csv_path):
    """Returns dict with validation results."""
```

### Step 2: Create Neuronames Importer

**File: `scripts/import_neuronames.py`**
```python
import json, csv, requests
from datetime import datetime
from pathlib import Path
from lib.schema_mapper import NEURODB_SCHEMA, create_empty_row, map_neuronames_to_schema
from lib.source_tagger import add_source_metadata
from lib.validators import validate_structure, generate_validation_report

NEURONAMES_URL = "http://braininfo.rprc.washington.edu/nnont.aspx"
OUTPUT_DIR = Path("imports/neuronames")
OUTPUT_FILE = OUTPUT_DIR / "neuronames_imported.csv"

def download_neuronames():
    """Downloads JSON from Neuronames API."""

def parse_neuronames(json_data):
    """Extracts term entries from JSON structure."""

def import_neuronames():
    """Main import pipeline."""
    # 1. Download JSON
    # 2. Parse entries
    # 3. Map to schema
    # 4. Add source metadata
    # 5. Write CSV
    # 6. Validate structure
    # 7. Report summary

if __name__ == "__main__":
    import_neuronames()
```

### Step 3: Test Pipeline

```bash
# Run importer
python scripts/import_neuronames.py

# Expected output:
# - imports/neuronames/neuronames_imported.csv
# - ~3,000 rows
# - 26 columns per row
# - Validation report (PASS)

# Manual spot check:
head -n 5 imports/neuronames/neuronames_imported.csv
wc -l imports/neuronames/neuronames_imported.csv
```

## Success Criteria

- ✅ All 3 infrastructure libraries created
- ✅ Neuronames importer script functional
- ✅ Output CSV has exactly 26 columns
- ✅ ~3,000 terms imported
- ✅ Structural validation passes
- ✅ Source metadata correctly populated:
  - `source` = "neuronames"
  - `source_priority` = 2
  - `sources_contributing` = "neuronames"
  - `date_added` = today's date

## Notes

- **NO neuro-reviewer validation yet** (defer to Day 5)
- **NO mesh-validator yet** (run during Day 4 merge)
- Focus on infrastructure + data extraction only
- Neuronames likely has clean data (curated neuroanatomy database)

## Next Steps (Day 2+)

- Day 2: NIF + Gene Ontology importers (reuse infrastructure)
- Day 3: UMLS importer (when license arrives)
- Day 4: Merge algorithm + free validation
- Day 5: Choose validation approach, run neuro-reviewer
