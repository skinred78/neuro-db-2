#!/usr/bin/env python3
"""
Convert NeuroDB-2 CSV database to Lex Stream JSON format.

This script transforms the neuroscience terminology database from the
22-column CSV format to the Lex Stream application's expected JSON structure.

Usage:
    python convert_to_lexstream.py

Output:
    neuro_terms_wikipedia.json - Lex Stream compatible database
"""

import csv
import json
from pathlib import Path
from collections import defaultdict


def extract_synonyms(row):
    """Extract all synonym fields from CSV row."""
    synonyms = []
    for i in [1, 2, 3]:  # Synonym 1, 2, 3 columns
        syn = row.get(f'Synonym {i}', '') or ''
        syn = syn.strip()
        if syn:
            synonyms.append(syn)
    return synonyms


def extract_abbreviations(row):
    """Extract abbreviation from CSV row."""
    abbrev = row.get('Abbreviation', '') or ''
    abbrev = abbrev.strip()
    return [abbrev] if abbrev else []


def extract_word_forms(row):
    """Extract word forms from CSV row."""
    word_forms = {}

    # Basic word forms
    noun = row.get('Noun Form of Word', '') or ''
    if noun.strip():
        word_forms['noun'] = noun.strip()

    verb = row.get('Verb Form of Word', '') or ''
    if verb.strip():
        word_forms['verb'] = verb.strip()

    adj = row.get('Adjective Form of Word', '') or ''
    if adj.strip():
        word_forms['adjective'] = adj.strip()

    adv = row.get('Adverb Form of Word', '') or ''
    if adv.strip():
        word_forms['adverb'] = adv.strip()

    # Spelling variants
    uk = row.get('UK Spelling', '') or ''
    if uk.strip():
        word_forms['uk_spelling'] = uk.strip()

    us = row.get('US Spelling', '') or ''
    if us.strip():
        word_forms['us_spelling'] = us.strip()

    return word_forms


def extract_associated_terms(row):
    """Extract commonly associated terms from CSV row."""
    associated = []
    for i in range(1, 9):  # Associated Term 1-8
        term = row.get(f'Commonly Associated Term {i}', '') or ''
        term = term.strip()
        if term:
            associated.append(term)
    return associated


def check_mesh_status(row):
    """Check if term has valid MeSH mapping."""
    mesh_term = row.get('Closest MeSH term', '') or ''
    return bool(mesh_term.strip())


def convert_entry(row):
    """Convert a single CSV row to Lex Stream format."""
    primary_term = row.get('Term', '') or ''
    primary_term = primary_term.strip()

    if not primary_term:
        return None, None

    # Lowercase key for case-insensitive lookup
    key = primary_term.lower()

    definition = row.get('Definition', '') or ''
    definition = definition.strip()

    mesh_term = row.get('Closest MeSH term', '') or ''
    mesh_term = mesh_term.strip()

    term_two = row.get('Term Two', '') or ''
    term_two = term_two.strip() or primary_term

    # Build Lex Stream format
    converted = {
        "primary_term": primary_term,
        "definition": definition,
        "synonyms": extract_synonyms(row),
        "abbreviations": extract_abbreviations(row),
        "word_forms": extract_word_forms(row),
        "associated_terms": extract_associated_terms(row),
        "is_mesh_term": check_mesh_status(row),
        "mesh_term": mesh_term,
        "secondary_term": term_two
    }

    return key, converted


def build_abbreviations_map(terms_dict):
    """Build fast abbreviation lookup map."""
    abbrev_map = {}

    for key, term_data in terms_dict.items():
        for abbrev in term_data['abbreviations']:
            abbrev_key = abbrev.lower()
            if abbrev_key not in abbrev_map:
                abbrev_map[abbrev_key] = {
                    "expansion": term_data['primary_term'],
                    "definition": term_data['definition']
                }

    return abbrev_map


def build_mesh_map(terms_dict):
    """Build fast MeSH term lookup map."""
    mesh_map = {}

    for key, term_data in terms_dict.items():
        if term_data['is_mesh_term'] and term_data['mesh_term']:
            mesh_key = term_data['mesh_term'].lower()
            mesh_map[mesh_key] = term_data['mesh_term']

    return mesh_map


def convert_database(csv_path, output_path):
    """Convert entire CSV database to Lex Stream JSON format."""

    print("Reading CSV database...")
    terms_dict = {}
    skipped = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            key, converted = convert_entry(row)
            if key and converted:
                terms_dict[key] = converted
            else:
                skipped += 1
                print(f"  Skipped row {i}: missing term")

    print(f"Converted {len(terms_dict)} terms ({skipped} skipped)")

    print("Building abbreviations map...")
    abbreviations = build_abbreviations_map(terms_dict)
    print(f"  {len(abbreviations)} unique abbreviations")

    print("Building MeSH terms map...")
    mesh_terms = build_mesh_map(terms_dict)
    print(f"  {len(mesh_terms)} MeSH terms")

    # Build final structure
    database = {
        "terms": terms_dict,
        "abbreviations": abbreviations,
        "mesh_terms": mesh_terms,
        "metadata": {
            "total_terms": len(terms_dict),
            "total_abbreviations": len(abbreviations),
            "total_mesh_terms": len(mesh_terms),
            "source_file": "neuro_terms.csv",
            "source_name": "Wikipedia Glossary + NINDS Glossary",
            "version": "2.0",
            "date_created": "2025-11-12"
        }
    }

    print(f"Writing to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)

    file_size = Path(output_path).stat().st_size
    print(f"✓ Complete! File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

    return database


def print_sample_entries(database, count=3):
    """Print sample entries for verification."""
    print(f"\n{'=' * 60}")
    print(f"SAMPLE ENTRIES (first {count})")
    print('=' * 60)

    for i, (key, term) in enumerate(list(database['terms'].items())[:count]):
        print(f"\n{i+1}. Key: '{key}'")
        print(f"   Primary Term: {term['primary_term']}")
        print(f"   Definition: {term['definition'][:80]}...")
        print(f"   Synonyms: {term['synonyms']}")
        print(f"   Abbreviations: {term['abbreviations']}")
        print(f"   MeSH: {term['mesh_term']} (is_mesh: {term['is_mesh_term']})")
        print(f"   Associated: {term['associated_terms'][:3]}...")


def main():
    """Main conversion process."""
    csv_path = Path('neuro_terms.csv')

    # Read version from VERSION.txt
    version_file = Path('VERSION.txt')
    if version_file.exists():
        version = version_file.read_text().strip()
    else:
        version = "2.0.0"  # Default if VERSION.txt missing

    # Use versioned filename following naming convention
    output_path = Path(f'neuro_terms_v{version}_wikipedia-ninds.json')

    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        return 1

    print("=" * 60)
    print("NeuroDB-2 → Lex Stream Conversion")
    print("=" * 60)
    print()

    database = convert_database(csv_path, output_path)
    print_sample_entries(database)

    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Run validation: python validate_lexstream_db.py")
    print("2. Run tests: python test_lexstream_db.py")
    print("3. Review validation report")
    print("4. Copy to Lex Stream app directory")

    return 0


if __name__ == '__main__':
    exit(main())
