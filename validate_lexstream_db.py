#!/usr/bin/env python3
"""
Validate Lex Stream database structure and data quality.

This script performs comprehensive validation of the generated
neuro_terms_wikipedia.json file to ensure it meets Lex Stream requirements.

Usage:
    python validate_lexstream_db.py
"""

import json
from pathlib import Path
from collections import Counter


def validate_structure(db):
    """Validate required top-level structure."""
    print("\n1. STRUCTURE VALIDATION")
    print("-" * 60)

    required_sections = ['terms', 'abbreviations', 'mesh_terms', 'metadata']
    errors = []

    for section in required_sections:
        if section in db:
            print(f"   ✓ {section}: present ({len(db[section])} entries)")
        else:
            print(f"   ✗ {section}: MISSING")
            errors.append(f"Missing required section: {section}")

    return errors


def validate_keys(db):
    """Validate all keys are lowercase."""
    print("\n2. KEY VALIDATION (lowercase requirement)")
    print("-" * 60)

    errors = []

    # Check terms keys
    non_lowercase_terms = [k for k in db['terms'].keys() if k != k.lower()]
    if non_lowercase_terms:
        print(f"   ✗ Found {len(non_lowercase_terms)} non-lowercase term keys")
        for key in non_lowercase_terms[:5]:
            print(f"      - '{key}'")
            errors.append(f"Non-lowercase term key: {key}")
    else:
        print(f"   ✓ All {len(db['terms'])} term keys are lowercase")

    # Check abbreviation keys
    non_lowercase_abbrev = [k for k in db['abbreviations'].keys() if k != k.lower()]
    if non_lowercase_abbrev:
        print(f"   ✗ Found {len(non_lowercase_abbrev)} non-lowercase abbreviation keys")
        errors.extend([f"Non-lowercase abbrev key: {k}" for k in non_lowercase_abbrev])
    else:
        print(f"   ✓ All {len(db['abbreviations'])} abbreviation keys are lowercase")

    # Check mesh keys
    non_lowercase_mesh = [k for k in db['mesh_terms'].keys() if k != k.lower()]
    if non_lowercase_mesh:
        print(f"   ✗ Found {len(non_lowercase_mesh)} non-lowercase MeSH keys")
        errors.extend([f"Non-lowercase mesh key: {k}" for k in non_lowercase_mesh])
    else:
        print(f"   ✓ All {len(db['mesh_terms'])} MeSH keys are lowercase")

    return errors


def validate_term_entries(db):
    """Validate individual term entries."""
    print("\n3. TERM ENTRY VALIDATION")
    print("-" * 60)

    errors = []
    terms = db['terms']

    # Required fields
    missing_primary = [k for k, v in terms.items() if not v.get('primary_term')]
    if missing_primary:
        print(f"   ✗ {len(missing_primary)} entries missing primary_term")
        errors.extend([f"Missing primary_term: {k}" for k in missing_primary[:10]])
    else:
        print(f"   ✓ All entries have primary_term")

    # Check definitions
    missing_def = [k for k, v in terms.items() if not v.get('definition')]
    short_def = [k for k, v in terms.items() if v.get('definition') and len(v['definition']) < 10]

    if missing_def:
        print(f"   ⚠ {len(missing_def)} entries missing definition")
    else:
        print(f"   ✓ All entries have definitions")

    if short_def:
        print(f"   ⚠ {len(short_def)} entries have short definitions (<10 chars)")
        for k in short_def[:3]:
            print(f"      - {k}: '{terms[k]['definition']}'")

    # Check required field structure
    required_fields = ['primary_term', 'definition', 'synonyms', 'abbreviations',
                      'word_forms', 'associated_terms', 'is_mesh_term',
                      'mesh_term', 'secondary_term']

    missing_fields = {}
    for key, term in list(terms.items())[:100]:  # Sample first 100
        for field in required_fields:
            if field not in term:
                missing_fields.setdefault(field, []).append(key)

    if missing_fields:
        print(f"   ✗ Found missing fields:")
        for field, keys in missing_fields.items():
            print(f"      - {field}: {len(keys)} entries")
            errors.append(f"Missing field '{field}' in {len(keys)} entries")
    else:
        print(f"   ✓ All sampled entries have required fields")

    return errors


def validate_data_quality(db):
    """Validate data quality metrics."""
    print("\n4. DATA QUALITY METRICS")
    print("-" * 60)

    terms = db['terms']

    # Synonym coverage
    with_synonyms = sum(1 for v in terms.values() if v.get('synonyms'))
    print(f"   Synonyms: {with_synonyms}/{len(terms)} terms ({with_synonyms/len(terms)*100:.1f}%)")

    # Abbreviation coverage
    with_abbrev = sum(1 for v in terms.values() if v.get('abbreviations'))
    print(f"   Abbreviations: {with_abbrev}/{len(terms)} terms ({with_abbrev/len(terms)*100:.1f}%)")

    # MeSH coverage
    with_mesh = sum(1 for v in terms.values() if v.get('is_mesh_term'))
    print(f"   MeSH terms: {with_mesh}/{len(terms)} terms ({with_mesh/len(terms)*100:.1f}%)")

    # Associated terms coverage
    with_associated = sum(1 for v in terms.values() if v.get('associated_terms'))
    print(f"   Associated terms: {with_associated}/{len(terms)} terms ({with_associated/len(terms)*100:.1f}%)")

    # Word forms coverage
    with_word_forms = sum(1 for v in terms.values() if v.get('word_forms'))
    print(f"   Word forms: {with_word_forms}/{len(terms)} terms ({with_word_forms/len(terms)*100:.1f}%)")

    # Definition length analysis
    def_lengths = [len(v.get('definition', '')) for v in terms.values()]
    avg_def_length = sum(def_lengths) / len(def_lengths) if def_lengths else 0
    print(f"   Avg definition length: {avg_def_length:.0f} characters")

    return []


def validate_metadata(db):
    """Validate metadata accuracy."""
    print("\n5. METADATA VALIDATION")
    print("-" * 60)

    errors = []
    metadata = db['metadata']

    # Check counts match
    actual_terms = len(db['terms'])
    stated_terms = metadata.get('total_terms', 0)
    if actual_terms == stated_terms:
        print(f"   ✓ Term count matches: {actual_terms}")
    else:
        print(f"   ✗ Term count mismatch: stated {stated_terms}, actual {actual_terms}")
        errors.append(f"Metadata term count mismatch")

    actual_abbrev = len(db['abbreviations'])
    stated_abbrev = metadata.get('total_abbreviations', 0)
    if actual_abbrev == stated_abbrev:
        print(f"   ✓ Abbreviation count matches: {actual_abbrev}")
    else:
        print(f"   ✗ Abbreviation count mismatch: stated {stated_abbrev}, actual {actual_abbrev}")
        errors.append(f"Metadata abbreviation count mismatch")

    actual_mesh = len(db['mesh_terms'])
    stated_mesh = metadata.get('total_mesh_terms', 0)
    if actual_mesh == stated_mesh:
        print(f"   ✓ MeSH count matches: {actual_mesh}")
    else:
        print(f"   ✗ MeSH count mismatch: stated {stated_mesh}, actual {actual_mesh}")
        errors.append(f"Metadata MeSH count mismatch")

    # Check metadata fields
    required_meta = ['source_file', 'source_name']
    for field in required_meta:
        if metadata.get(field):
            print(f"   ✓ {field}: {metadata[field]}")
        else:
            print(f"   ⚠ {field}: missing")

    return errors


def check_duplicates(db):
    """Check for duplicate entries."""
    print("\n6. DUPLICATE DETECTION")
    print("-" * 60)

    # Check for duplicate abbreviation expansions
    abbrev_expansions = [v['expansion'] for v in db['abbreviations'].values()]
    expansion_counts = Counter(abbrev_expansions)
    duplicates = {k: v for k, v in expansion_counts.items() if v > 1}

    if duplicates:
        print(f"   ⚠ Found {len(duplicates)} abbreviations with same expansion:")
        for expansion, count in list(duplicates.items())[:5]:
            print(f"      - '{expansion}': {count} abbreviations")
            # Find which abbreviations
            abbrevs = [k for k, v in db['abbreviations'].items() if v['expansion'] == expansion]
            print(f"        Abbrevs: {', '.join(abbrevs[:3])}")
    else:
        print(f"   ✓ No duplicate abbreviation expansions")

    return []


def main():
    """Main validation process."""
    # Check for versioned filename first, fallback to generic
    version_file = Path('VERSION.txt')
    if version_file.exists():
        version = version_file.read_text().strip()
        db_path = Path(f'neuro_terms_v{version}_wikipedia-ninds.json')
    else:
        db_path = Path('neuro_terms_wikipedia.json')

    if not db_path.exists():
        # Try finding any versioned file
        import glob
        versioned_files = glob.glob('neuro_terms_v*.json')
        if versioned_files:
            db_path = Path(versioned_files[0])
        else:
            db_path = Path('neuro_terms_wikipedia.json')

    if not db_path.exists():
        print(f"Error: {db_path} not found")
        print("Run convert_to_lexstream.py first")
        return 1

    print("=" * 60)
    print("LEX STREAM DATABASE VALIDATION")
    print("=" * 60)

    # Load database
    print("\nLoading database...")
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)

    file_size = db_path.stat().st_size
    print(f"  File: {db_path}")
    print(f"  Size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

    # Run validations
    all_errors = []
    all_errors.extend(validate_structure(db))
    all_errors.extend(validate_keys(db))
    all_errors.extend(validate_term_entries(db))
    all_errors.extend(validate_data_quality(db))
    all_errors.extend(validate_metadata(db))
    all_errors.extend(check_duplicates(db))

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    if all_errors:
        print(f"\n❌ FAILED: {len(all_errors)} errors found")
        print("\nFirst 10 errors:")
        for i, error in enumerate(all_errors[:10], 1):
            print(f"  {i}. {error}")
        return 1
    else:
        print("\n✅ PASSED: All validations successful")
        print("\nDatabase is ready for Lex Stream integration!")
        return 0


if __name__ == '__main__':
    exit(main())
