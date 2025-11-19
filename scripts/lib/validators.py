"""
Validation utilities for NeuroDB-2 CSV data.

Performs structural validation (Tier 1) - column count, encoding, duplicates, required fields.
Does NOT perform semantic validation (mesh-validator, neuro-reviewer).
"""

import csv
from pathlib import Path
from collections import Counter


def validate_structure(csv_path, expected_columns=26):
    """
    Validates CSV file structure.

    Checks:
    - File exists and is readable
    - UTF-8 encoding
    - Exactly expected_columns columns in every row
    - No malformed CSV (proper quoting)

    Args:
        csv_path (str|Path): Path to CSV file
        expected_columns (int): Expected column count (26 for extended schema)

    Returns:
        dict: {
            'valid': bool,
            'errors': list of error messages,
            'warnings': list of warning messages
        }
    """
    csv_path = Path(csv_path)
    result = {'valid': True, 'errors': [], 'warnings': []}

    # Check file exists
    if not csv_path.exists():
        result['valid'] = False
        result['errors'].append(f"File not found: {csv_path}")
        return result

    # Check file is readable
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
    except UnicodeDecodeError:
        result['valid'] = False
        result['errors'].append("File is not UTF-8 encoded")
        return result
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Error reading file: {str(e)}")
        return result

    # Check has data
    if len(rows) < 2:  # Header + at least 1 data row
        result['valid'] = False
        result['errors'].append("File has no data rows (only header or empty)")
        return result

    # Check column count consistency
    header_cols = len(rows[0])
    if header_cols != expected_columns:
        result['valid'] = False
        result['errors'].append(
            f"Header has {header_cols} columns, expected {expected_columns}"
        )

    for i, row in enumerate(rows[1:], start=2):  # Start at row 2 (skip header)
        if len(row) != expected_columns:
            result['valid'] = False
            result['errors'].append(
                f"Row {i} has {len(row)} columns, expected {expected_columns}"
            )
            # Only report first 5 column count errors
            if len([e for e in result['errors'] if 'columns' in e]) >= 5:
                result['errors'].append("...and more column count errors")
                break

    return result


def validate_required_fields(csv_path):
    """
    Validates that required fields are non-empty.

    Required fields:
    - Term
    - Definition
    - source
    - source_priority
    - date_added

    Args:
        csv_path (str|Path): Path to CSV file

    Returns:
        dict: {
            'valid': bool,
            'errors': list of error messages (row numbers with empty required fields)
        }
    """
    csv_path = Path(csv_path)
    result = {'valid': True, 'errors': []}

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=2):  # Start at row 2 (skip header)
                # Check Term
                if not row.get('Term', '').strip():
                    result['valid'] = False
                    result['errors'].append(f"Row {i}: Term is empty")

                # Check Definition
                if not row.get('Definition', '').strip():
                    result['valid'] = False
                    result['errors'].append(f"Row {i}: Definition is empty")

                # Check source metadata
                if not row.get('source', '').strip():
                    result['valid'] = False
                    result['errors'].append(f"Row {i}: source is empty")

                if not row.get('source_priority', '').strip():
                    result['valid'] = False
                    result['errors'].append(f"Row {i}: source_priority is empty")

                if not row.get('date_added', '').strip():
                    result['valid'] = False
                    result['errors'].append(f"Row {i}: date_added is empty")

                # Stop after 10 errors to avoid overwhelming output
                if len(result['errors']) >= 10:
                    result['errors'].append("...and more required field errors")
                    break

    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Error reading file: {str(e)}")

    return result


def validate_duplicates(csv_path):
    """
    Checks for duplicate terms.

    Args:
        csv_path (str|Path): Path to CSV file

    Returns:
        dict: {
            'valid': bool,
            'duplicates': list of (term, count) tuples for duplicates,
            'warnings': list of warning messages
        }
    """
    csv_path = Path(csv_path)
    result = {'valid': True, 'duplicates': [], 'warnings': []}

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            terms = [row.get('Term', '').strip().lower() for row in reader]

        # Count term occurrences
        term_counts = Counter(terms)
        duplicates = [(term, count) for term, count in term_counts.items()
                      if count > 1 and term]  # Exclude empty terms

        if duplicates:
            result['valid'] = False
            result['duplicates'] = sorted(duplicates, key=lambda x: x[1], reverse=True)
            result['warnings'].append(
                f"Found {len(duplicates)} duplicate terms (case-insensitive)"
            )

    except Exception as e:
        result['valid'] = False
        result['warnings'].append(f"Error checking duplicates: {str(e)}")

    return result


def validate_encoding(csv_path):
    """
    Validates UTF-8 encoding and checks for encoding issues.

    Args:
        csv_path (str|Path): Path to CSV file

    Returns:
        dict: {
            'valid': bool,
            'encoding': str (detected encoding),
            'errors': list of error messages
        }
    """
    csv_path = Path(csv_path)
    result = {'valid': True, 'encoding': 'UTF-8', 'errors': []}

    # Try UTF-8
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            f.read()
        return result
    except UnicodeDecodeError as e:
        result['valid'] = False
        result['errors'].append(f"UTF-8 decoding failed: {str(e)}")

    # Try other common encodings
    for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
        try:
            with open(csv_path, 'r', encoding=encoding) as f:
                f.read()
            result['encoding'] = encoding
            result['errors'].append(
                f"File uses {encoding} encoding, should be UTF-8"
            )
            return result
        except UnicodeDecodeError:
            continue

    result['errors'].append("Could not detect file encoding")
    return result


def generate_validation_report(csv_path):
    """
    Runs all structural validations and generates comprehensive report.

    Args:
        csv_path (str|Path): Path to CSV file

    Returns:
        dict: {
            'overall_valid': bool,
            'file_path': str,
            'row_count': int,
            'structure': {...},
            'required_fields': {...},
            'duplicates': {...},
            'encoding': {...},
            'summary': str (human-readable summary)
        }
    """
    csv_path = Path(csv_path)

    # Run all validations
    structure = validate_structure(csv_path)
    required = validate_required_fields(csv_path)
    duplicates = validate_duplicates(csv_path)
    encoding = validate_encoding(csv_path)

    # Count rows
    row_count = 0
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            row_count = sum(1 for _ in csv.reader(f)) - 1  # Subtract header
    except:
        pass

    # Aggregate results
    overall_valid = all([
        structure['valid'],
        required['valid'],
        duplicates['valid'],
        encoding['valid']
    ])

    report = {
        'overall_valid': overall_valid,
        'file_path': str(csv_path),
        'row_count': row_count,
        'structure': structure,
        'required_fields': required,
        'duplicates': duplicates,
        'encoding': encoding
    }

    # Generate summary
    if overall_valid:
        summary = f"✅ PASS - All validations passed ({row_count} terms)"
    else:
        error_count = (
            len(structure.get('errors', [])) +
            len(required.get('errors', [])) +
            len(duplicates.get('warnings', [])) +
            len(encoding.get('errors', []))
        )
        summary = f"❌ FAIL - {error_count} validation errors found"

    report['summary'] = summary

    return report


def print_validation_report(report):
    """
    Pretty-prints validation report to console.

    Args:
        report (dict): Report from generate_validation_report()
    """
    print("\n" + "="*70)
    print(f"VALIDATION REPORT: {report['file_path']}")
    print("="*70)

    print(f"\nOverall Status: {report['summary']}")
    print(f"Total Rows: {report['row_count']}")

    # Structure validation
    print("\n--- Structure Validation ---")
    if report['structure']['valid']:
        print("✅ PASS - Column count consistent (26 columns)")
    else:
        print("❌ FAIL - Structure issues:")
        for error in report['structure']['errors']:
            print(f"  - {error}")

    # Required fields validation
    print("\n--- Required Fields Validation ---")
    if report['required_fields']['valid']:
        print("✅ PASS - All required fields populated")
    else:
        print("❌ FAIL - Missing required fields:")
        for error in report['required_fields']['errors']:
            print(f"  - {error}")

    # Duplicate check
    print("\n--- Duplicate Check ---")
    if report['duplicates']['valid']:
        print("✅ PASS - No duplicate terms found")
    else:
        print("❌ FAIL - Duplicate terms detected:")
        for term, count in report['duplicates']['duplicates'][:10]:
            print(f"  - '{term}': {count} occurrences")
        if len(report['duplicates']['duplicates']) > 10:
            print(f"  - ...and {len(report['duplicates']['duplicates']) - 10} more")

    # Encoding check
    print("\n--- Encoding Validation ---")
    if report['encoding']['valid']:
        print("✅ PASS - UTF-8 encoding")
    else:
        print("❌ FAIL - Encoding issues:")
        for error in report['encoding']['errors']:
            print(f"  - {error}")

    print("\n" + "="*70 + "\n")
