#!/usr/bin/env python3
"""
UMLS to NeuroDB-2 Schema Mapper

Maps extracted UMLS data to NeuroDB-2 26-column CSV schema:
- 22 standard columns (Term, Definition, Synonyms, etc.)
- 4 metadata columns (source, source_priority, sources_contributing, date_added)

Input:
- imports/umls/umls_concepts_intermediate.json (325K concepts)
- imports/umls/umls_associations.json (294K with associations)

Output:
- imports/umls/umls_neuroscience_terms.csv (26 columns)
"""

import json
import csv
from pathlib import Path
from datetime import date

# File paths
CONCEPTS_FILE = Path("imports/umls/umls_concepts_intermediate.json")
ASSOCIATIONS_FILE = Path("imports/umls/umls_associations.json")
OUTPUT_CSV = Path("imports/umls/umls_neuroscience_terms.csv")

# NeuroDB-2 26-column schema (22 standard + 4 metadata)
SCHEMA_COLUMNS = [
    # Standard columns (22)
    'Term',
    'Term Two',
    'Definition',
    'Closest MeSH term',
    'Synonym 1',
    'Synonym 2',
    'Synonym 3',
    'Abbreviation',
    'UK Spelling',
    'US Spelling',
    'Noun Form of Word',
    'Verb Form of Word',
    'Adjective Form of Word',
    'Adverb Form of Word',
    'Commonly Associated Term 1',
    'Commonly Associated Term 2',
    'Commonly Associated Term 3',
    'Commonly Associated Term 4',
    'Commonly Associated Term 5',
    'Commonly Associated Term 6',
    'Commonly Associated Term 7',
    'Commonly Associated Term 8',
    # Metadata columns (4)
    'Source',
    'Source Priority',
    'Sources Contributing',
    'Date Added',
]


def load_data():
    """Load concepts and associations."""
    print(f"\n📥 Loading data...")

    with open(CONCEPTS_FILE, 'r', encoding='utf-8') as f:
        concepts = json.load(f)

    with open(ASSOCIATIONS_FILE, 'r', encoding='utf-8') as f:
        associations = json.load(f)

    print(f"   ✅ Loaded {len(concepts):,} concepts")
    print(f"   ✅ Loaded {len(associations):,} association sets")

    return concepts, associations


def map_concept_to_row(cui, concept_data, associations):
    """
    Map a single UMLS concept to NeuroDB-2 26-column row.

    Args:
        cui: UMLS CUI
        concept_data: Concept metadata from intermediate JSON
        associations: Association data for this CUI

    Returns:
        dict: Row data with 26 columns
    """
    row = {}

    # Column 1: Term
    row['Term'] = concept_data.get('preferred_term', '')

    # Column 2: Term Two (alternate representation)
    # Leave empty - UMLS doesn't distinguish ASCII-safe versions
    row['Term Two'] = ''

    # Column 3: Definition
    definition = concept_data.get('definition', '')
    if not definition or not definition.strip():
        definition = '(pending enrichment)'  # Mark for future backfill
    row['Definition'] = definition

    # Column 4: Closest MeSH term
    row['Closest MeSH term'] = concept_data.get('mesh_code', '')

    # Columns 5-7: Synonym 1-3
    synonyms = concept_data.get('synonyms', [])
    row['Synonym 1'] = synonyms[0] if len(synonyms) > 0 else ''
    row['Synonym 2'] = synonyms[1] if len(synonyms) > 1 else ''
    row['Synonym 3'] = synonyms[2] if len(synonyms) > 2 else ''

    # Column 8: Abbreviation
    abbreviations = concept_data.get('abbreviations', [])
    row['Abbreviation'] = abbreviations[0] if abbreviations else ''

    # Columns 9-10: UK/US Spelling
    # UMLS doesn't distinguish spelling variants
    row['UK Spelling'] = ''
    row['US Spelling'] = ''

    # Columns 11-14: Word Forms
    # UMLS doesn't provide word form variations
    row['Noun Form of Word'] = ''
    row['Verb Form of Word'] = ''
    row['Adjective Form of Word'] = ''
    row['Adverb Form of Word'] = ''

    # Columns 15-22: Commonly Associated Term 1-8
    assoc_data = associations.get(cui, {})
    associated_terms = assoc_data.get('associated_terms', [])

    for i in range(8):
        col_name = f'Commonly Associated Term {i+1}'
        row[col_name] = associated_terms[i] if i < len(associated_terms) else ''

    # Metadata Column 23: Source
    row['Source'] = 'UMLS'

    # Metadata Column 24: Source Priority
    row['Source Priority'] = 'High'  # UMLS is authoritative medical terminology

    # Metadata Column 25: Sources Contributing
    sources = concept_data.get('sources', [])
    row['Sources Contributing'] = ';'.join(sorted(sources)) if sources else ''

    # Metadata Column 26: Date Added
    row['Date Added'] = date.today().isoformat()

    return row


def map_all_concepts(concepts, associations):
    """Map all concepts to NeuroDB-2 rows."""
    print(f"\n🗺️  Mapping {len(concepts):,} concepts to NeuroDB-2 schema...")

    rows = []
    stats = {
        'total': 0,
        'with_definitions': 0,
        'with_mesh': 0,
        'with_synonyms': 0,
        'with_abbreviations': 0,
        'with_associations': 0,
    }

    for cui, concept_data in concepts.items():
        row = map_concept_to_row(cui, concept_data, associations)
        rows.append(row)

        # Track statistics
        stats['total'] += 1
        if row['Definition'] and row['Definition'] != '(pending enrichment)':
            stats['with_definitions'] += 1
        if row['Closest MeSH term']:
            stats['with_mesh'] += 1
        if row['Synonym 1'] or row['Synonym 2'] or row['Synonym 3']:
            stats['with_synonyms'] += 1
        if row['Abbreviation']:
            stats['with_abbreviations'] += 1
        if any(row[f'Commonly Associated Term {i}'] for i in range(1, 9)):
            stats['with_associations'] += 1

    print(f"   ✅ Mapped {len(rows):,} rows")
    return rows, stats


def write_csv(rows):
    """Write rows to CSV file."""
    print(f"\n💾 Writing {len(rows):,} rows to {OUTPUT_CSV}...")

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"   ✅ Wrote {OUTPUT_CSV}")


def print_statistics(stats):
    """Print coverage statistics."""
    print(f"\n📊 Coverage Statistics:")
    print(f"")
    print(f"   Total terms: {stats['total']:,}")
    print(f"")
    print(f"   Field Coverage:")
    print(f"   - Definitions: {stats['with_definitions']:,} ({stats['with_definitions']/stats['total']*100:.1f}%)")
    print(f"   - MeSH codes: {stats['with_mesh']:,} ({stats['with_mesh']/stats['total']*100:.1f}%)")
    print(f"   - Synonyms: {stats['with_synonyms']:,} ({stats['with_synonyms']/stats['total']*100:.1f}%)")
    print(f"   - Abbreviations: {stats['with_abbreviations']:,} ({stats['with_abbreviations']/stats['total']*100:.1f}%)")
    print(f"   - Associated Terms: {stats['with_associations']:,} ({stats['with_associations']/stats['total']*100:.1f}%)")


def main():
    print("="*70)
    print("UMLS TO NEURODB-2 SCHEMA MAPPER")
    print("="*70)

    # Step 1: Load data
    concepts, associations = load_data()

    # Step 2: Map to schema
    rows, stats = map_all_concepts(concepts, associations)

    # Step 3: Write CSV
    write_csv(rows)

    # Step 4: Print statistics
    print_statistics(stats)

    # Summary
    print("\n" + "="*70)
    print("SCHEMA MAPPING COMPLETE")
    print("="*70)

    print(f"\n✅ Output: {OUTPUT_CSV}")
    print(f"✅ Format: 26-column CSV (22 standard + 4 metadata)")
    print(f"✅ Rows: {len(rows):,}")

    print(f"\n🎯 Next Steps:")
    print(f"   1. Run structural validation: lib/validators.py")
    print(f"   2. Profile data quality")
    print(f"   3. Update ontology-import-tracker.md")


if __name__ == "__main__":
    main()
