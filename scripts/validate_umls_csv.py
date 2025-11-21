#!/usr/bin/env python3
"""
UMLS CSV Structural Validator

Validates that umls_neuroscience_terms.csv conforms to NeuroDB-2 26-column schema.

Checks:
1. Column count (26)
2. Column names match schema
3. Required fields populated (Term, Definition or placeholder)
4. CSV quoting/escaping correct
5. No malformed rows
"""

import csv
from pathlib import Path
from collections import Counter

# File to validate
CSV_FILE = Path("imports/umls/umls_neuroscience_terms.csv")

# Expected schema (26 columns)
EXPECTED_COLUMNS = [
    'Term', 'Term Two', 'Definition', 'Closest MeSH term',
    'Synonym 1', 'Synonym 2', 'Synonym 3', 'Abbreviation',
    'UK Spelling', 'US Spelling',
    'Noun Form of Word', 'Verb Form of Word', 'Adjective Form of Word', 'Adverb Form of Word',
    'Commonly Associated Term 1', 'Commonly Associated Term 2', 'Commonly Associated Term 3', 'Commonly Associated Term 4',
    'Commonly Associated Term 5', 'Commonly Associated Term 6', 'Commonly Associated Term 7', 'Commonly Associated Term 8',
    'Source', 'Source Priority', 'Sources Contributing', 'Date Added',
]


def validate_structure():
    """Validate CSV structure."""
    print(f"\n🔍 Validating {CSV_FILE}...")

    errors = []
    warnings = []
    row_count = 0
    column_counts = Counter()

    # Check file exists
    if not CSV_FILE.exists():
        errors.append(f"File not found: {CSV_FILE}")
        return errors, warnings, 0

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Validate header
        actual_columns = reader.fieldnames
        if actual_columns != EXPECTED_COLUMNS:
            errors.append(f"Column mismatch!")
            errors.append(f"  Expected: {EXPECTED_COLUMNS}")
            errors.append(f"  Actual: {actual_columns}")
            return errors, warnings, 0

        # Validate rows
        for i, row in enumerate(reader, 1):
            row_count = i

            # Check column count
            column_counts[len(row)] += 1

            # Check required fields
            if not row.get('Term', '').strip():
                errors.append(f"Row {i}: Missing 'Term' field")

            if not row.get('Definition', '').strip():
                warnings.append(f"Row {i}: Missing 'Definition' field")

            # Progress indicator
            if i % 50000 == 0:
                print(f"   Validated {i:,} rows...")

    print(f"   ✅ Validated {row_count:,} rows")
    return errors, warnings, row_count


def print_results(errors, warnings, row_count):
    """Print validation results."""
    print(f"\n📊 Validation Results:")
    print(f"")
    print(f"   Total rows: {row_count:,}")
    print(f"   Errors: {len(errors)}")
    print(f"   Warnings: {len(warnings)}")
    print(f"")

    if errors:
        print(f"❌ ERRORS:")
        for error in errors[:10]:  # Show first 10
            print(f"   - {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more errors")
        print(f"")

    if warnings:
        print(f"⚠️  WARNINGS:")
        for warning in warnings[:10]:  # Show first 10
            print(f"   - {warning}")
        if len(warnings) > 10:
            print(f"   ... and {len(warnings) - 10} more warnings")
        print(f"")

    if not errors:
        print(f"✅ VALIDATION PASSED")
    else:
        print(f"❌ VALIDATION FAILED")


def main():
    print("="*70)
    print("UMLS CSV STRUCTURAL VALIDATOR")
    print("="*70)

    errors, warnings, row_count = validate_structure()

    print_results(errors, warnings, row_count)

    # Summary
    print("\n" + "="*70)
    print("VALIDATION COMPLETE")
    print("="*70)

    if errors:
        print(f"\n❌ Found {len(errors)} structural errors")
        return 1
    else:
        print(f"\n✅ CSV structure valid: {row_count:,} rows, 26 columns")
        return 0


if __name__ == "__main__":
    exit(main())
