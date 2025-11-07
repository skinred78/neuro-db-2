#!/usr/bin/env python3
"""
Extract NEW terms from NINDS Glossary for integration into NeuroDB-2.

This script:
1. Parses the NINDS glossary markdown file
2. Extracts term names and definitions
3. Compares with existing database to find NEW terms
4. Groups NEW terms by letter
5. Outputs structured data for enrichment
"""

import csv
import json
import glob
from pathlib import Path
from collections import defaultdict

# Configuration
NINDS_GLOSSARY = '/Users/sam/NeuroDB-2/ninds-glossary-of-neurological-terms.md'
LETTER_FILES_DIR = '/Users/sam/NeuroDB-2/LetterFiles'
OUTPUT_DIR = '/Users/sam/NeuroDB-2/scripts/output'

def parse_ninds_glossary(file_path):
    """Parse NINDS glossary and extract terms + definitions."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    terms = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines, headers, source info
        if not line or line.startswith('-') or line.startswith('Original') or line.startswith('This page'):
            i += 1
            continue

        # Check if line is a term (starts with uppercase letter)
        if line and line[0].isupper():
            # Check if next line exists and is likely a definition
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                # Definition should not start with a dash (section header)
                if next_line and not next_line.startswith('-'):
                    terms.append({
                        'term': line,
                        'definition': next_line
                    })
                    i += 2  # Skip term and definition
                    continue

        i += 1

    return terms

def load_existing_terms(letter_files_dir):
    """Load all terms from existing letter CSV files."""
    existing_terms = set()

    csv_files = glob.glob(f"{letter_files_dir}/*.csv")

    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'Term' in row and row['Term']:
                        existing_terms.add(row['Term'].lower().strip())
        except Exception as e:
            print(f"Warning: Could not read {csv_file}: {e}")

    return existing_terms

def identify_new_terms(ninds_terms, existing_terms):
    """Identify terms that are in NINDS but not in existing database."""
    new_terms = []
    overlapping_terms = []

    for term_data in ninds_terms:
        term_lower = term_data['term'].lower().strip()

        if term_lower in existing_terms:
            overlapping_terms.append(term_data)
        else:
            new_terms.append(term_data)

    return new_terms, overlapping_terms

def group_by_letter(terms):
    """Group terms by their first letter."""
    grouped = defaultdict(list)

    for term_data in terms:
        first_letter = term_data['term'][0].upper()
        grouped[first_letter].append(term_data)

    # Sort terms within each letter
    for letter in grouped:
        grouped[letter].sort(key=lambda x: x['term'].lower())

    return dict(grouped)

def generate_csv_template(terms_by_letter, output_dir):
    """Generate CSV template files for enrichment (22-column schema)."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # CSV columns (22-column schema)
    columns = [
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
        'Commonly Associated Term 8'
    ]

    files_created = []

    for letter, terms in sorted(terms_by_letter.items()):
        filename = f"{output_dir}/{letter}_NINDS_template.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            for term_data in terms:
                row = {col: '' for col in columns}  # Initialize all columns as empty
                row['Term'] = term_data['term']
                row['Definition'] = term_data['definition']
                # All other fields empty, ready for enrichment
                writer.writerow(row)

        files_created.append(filename)
        print(f"✓ Created {filename} ({len(terms)} terms)")

    return files_created

def generate_summary_report(ninds_terms, existing_terms, new_terms, overlapping_terms, terms_by_letter):
    """Generate summary report of extraction."""
    report = []
    report.append("=" * 60)
    report.append("NINDS TERMS EXTRACTION REPORT")
    report.append("=" * 60)
    report.append("")

    report.append(f"NINDS Glossary: {len(ninds_terms)} terms total")
    report.append(f"Existing Database: {len(existing_terms)} terms")
    report.append(f"Overlapping Terms: {len(overlapping_terms)} terms")
    report.append(f"NEW Terms: {len(new_terms)} terms")
    report.append("")

    report.append("NEW TERMS BY LETTER:")
    report.append("-" * 60)

    for letter in sorted(terms_by_letter.keys()):
        terms = terms_by_letter[letter]
        report.append(f"  {letter}: {len(terms)} terms")
        for term_data in terms:
            report.append(f"     - {term_data['term']}")

    report.append("")
    report.append("=" * 60)
    report.append(f"CSV templates created in: {OUTPUT_DIR}")
    report.append("=" * 60)

    return "\n".join(report)

def main():
    print("Starting NINDS terms extraction...")
    print()

    # Step 1: Parse NINDS glossary
    print("1. Parsing NINDS glossary...")
    ninds_terms = parse_ninds_glossary(NINDS_GLOSSARY)
    print(f"   Found {len(ninds_terms)} terms in NINDS glossary")

    # Step 2: Load existing database terms
    print("2. Loading existing database terms...")
    existing_terms = load_existing_terms(LETTER_FILES_DIR)
    print(f"   Found {len(existing_terms)} terms in existing database")

    # Step 3: Identify NEW terms
    print("3. Identifying NEW terms...")
    new_terms, overlapping_terms = identify_new_terms(ninds_terms, existing_terms)
    print(f"   Found {len(new_terms)} NEW terms")
    print(f"   Found {len(overlapping_terms)} overlapping terms (skipped)")

    # Step 4: Group by letter
    print("4. Grouping NEW terms by letter...")
    terms_by_letter = group_by_letter(new_terms)
    print(f"   Grouped into {len(terms_by_letter)} letters")

    # Step 5: Generate CSV templates
    print("5. Generating CSV templates for enrichment...")
    files_created = generate_csv_template(terms_by_letter, OUTPUT_DIR)

    # Step 6: Generate summary report
    print()
    report = generate_summary_report(ninds_terms, existing_terms, new_terms, overlapping_terms, terms_by_letter)
    print(report)

    # Save report to file
    report_file = f"{OUTPUT_DIR}/extraction_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print()
    print(f"Report saved to: {report_file}")

    # Save detailed JSON for reference
    json_file = f"{OUTPUT_DIR}/ninds_new_terms.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_ninds_terms': len(ninds_terms),
                'existing_database_terms': len(existing_terms),
                'new_terms': len(new_terms),
                'overlapping_terms': len(overlapping_terms)
            },
            'new_terms_by_letter': terms_by_letter
        }, f, indent=2, ensure_ascii=False)
    print(f"Detailed data saved to: {json_file}")

    print()
    print("✓ Extraction complete!")
    print()
    print("NEXT STEPS:")
    print("1. Review CSV templates in scripts/output/")
    print("2. Run enrichment workflow (AI + mesh-validator)")
    print("3. Validate enriched data (dual validation)")
    print("4. Integrate into letter files")

if __name__ == '__main__':
    main()
