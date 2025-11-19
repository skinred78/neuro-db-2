#!/usr/bin/env python3
"""
Test Lex Stream database functionality.

This script tests common use cases for the Lex Stream agent pipeline
to ensure the database works as expected in production.

Usage:
    python test_lexstream_db.py
"""

import json
from pathlib import Path


class LexStreamDB:
    """Simple database loader for testing."""

    def __init__(self, db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            self.db = json.load(f)
        self.terms = self.db['terms']
        self.abbreviations = self.db['abbreviations']
        self.mesh_terms = self.db['mesh_terms']

    def lookup_term(self, term):
        """Case-insensitive term lookup."""
        return self.terms.get(term.lower())

    def lookup_abbreviation(self, abbrev):
        """Case-insensitive abbreviation lookup."""
        return self.abbreviations.get(abbrev.lower())

    def is_mesh_term(self, term):
        """Check if term is a MeSH term."""
        term_data = self.lookup_term(term)
        if term_data:
            return term_data.get('is_mesh_term', False)
        return False

    def get_synonyms(self, term):
        """Get synonyms for a term."""
        term_data = self.lookup_term(term)
        if term_data:
            return term_data.get('synonyms', [])
        return []

    def get_associated_terms(self, term):
        """Get associated terms."""
        term_data = self.lookup_term(term)
        if term_data:
            return term_data.get('associated_terms', [])
        return []

    def spell_check(self, word):
        """Check if word exists in neuroscience terminology."""
        return word.lower() in self.terms


def test_abbreviation_expansion(db):
    """Test 1: Abbreviation Expander Agent."""
    print("\n1. ABBREVIATION EXPANSION TEST")
    print("-" * 60)

    test_cases = [
        ("TMS", "Transcranial Magnetic Stimulation"),
        ("fMRI", "Functional Magnetic Resonance Imaging"),
        ("ACh", "Acetylcholine"),
        ("GABA", "Gamma-Aminobutyric Acid"),
    ]

    passed = 0
    for abbrev, expected_term in test_cases:
        result = db.lookup_abbreviation(abbrev)
        if result:
            expansion = result['expansion']
            match = expected_term.lower() in expansion.lower()
            status = "✓" if match else "⚠"
            print(f"   {status} {abbrev} → {expansion}")
            if match:
                passed += 1
        else:
            print(f"   ✗ {abbrev} → NOT FOUND")

    print(f"\n   Result: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_spell_checker(db):
    """Test 2: Spell Checker Agent."""
    print("\n2. SPELL CHECKER TEST")
    print("-" * 60)

    # Valid neuroscience terms
    valid_terms = ["acetylcholine", "dopamine", "serotonin", "neuroplasticity", "hippocampus"]

    print("   Valid terms (should all exist):")
    valid_count = 0
    for term in valid_terms:
        exists = db.spell_check(term)
        status = "✓" if exists else "✗"
        print(f"      {status} {term}")
        if exists:
            valid_count += 1

    print(f"\n   Result: {valid_count}/{len(valid_terms)} valid terms found")
    return valid_count == len(valid_terms)


def test_synonym_finder(db):
    """Test 3: Synonym Finder Agent."""
    print("\n3. SYNONYM FINDER TEST")
    print("-" * 60)

    test_cases = [
        "Acetylcholine",
        "Action potential",
        "Alzheimer's disease",
    ]

    found = 0
    for term in test_cases:
        synonyms = db.get_synonyms(term)
        associated = db.get_associated_terms(term)

        if synonyms or associated:
            print(f"   ✓ {term}:")
            if synonyms:
                print(f"      Synonyms: {', '.join(synonyms[:3])}")
            if associated:
                print(f"      Associated: {', '.join(associated[:5])}")
            found += 1
        else:
            print(f"   ⚠ {term}: No synonyms or associated terms")

    print(f"\n   Result: {found}/{len(test_cases)} terms have expansion data")
    return found > 0


def test_mesh_detector(db):
    """Test 4: MeSH Term Detector."""
    print("\n4. MESH TERM DETECTOR TEST")
    print("-" * 60)

    test_cases = [
        ("Acetylcholine", True),
        ("Dopamine", True),
        ("Action potential", True),
    ]

    passed = 0
    for term, expected_mesh in test_cases:
        is_mesh = db.is_mesh_term(term)
        term_data = db.lookup_term(term)

        if term_data:
            mesh_term = term_data.get('mesh_term', '')
            match = is_mesh == expected_mesh
            status = "✓" if match else "✗"
            print(f"   {status} {term}: MeSH={is_mesh} ('{mesh_term}')")
            if match:
                passed += 1
        else:
            print(f"   ✗ {term}: NOT FOUND")

    print(f"\n   Result: {passed}/{len(test_cases)} MeSH detections correct")
    return passed == len(test_cases)


def test_component_detector(db):
    """Test 5: Component Detector (semantic analysis)."""
    print("\n5. COMPONENT DETECTOR TEST")
    print("-" * 60)

    # Test that definitions exist for semantic analysis
    test_terms = [
        "Transcranial Magnetic Stimulation",
        "Stroke",
        "Memory",
    ]

    has_definitions = 0
    for term in test_terms:
        term_data = db.lookup_term(term)
        if term_data and term_data.get('definition'):
            def_preview = term_data['definition'][:80] + "..."
            print(f"   ✓ {term}: {def_preview}")
            has_definitions += 1
        else:
            print(f"   ✗ {term}: Missing definition")

    print(f"\n   Result: {has_definitions}/{len(test_terms)} terms have definitions for analysis")
    return has_definitions > 0


def test_case_insensitivity(db):
    """Test 6: Case-insensitive lookups."""
    print("\n6. CASE INSENSITIVITY TEST")
    print("-" * 60)

    test_cases = [
        ("acetylcholine", "Acetylcholine"),
        ("ACETYLCHOLINE", "Acetylcholine"),
        ("AcEtYlChOlInE", "Acetylcholine"),
    ]

    passed = 0
    for input_term, expected in test_cases:
        result = db.lookup_term(input_term)
        if result and result['primary_term'] == expected:
            print(f"   ✓ '{input_term}' → {result['primary_term']}")
            passed += 1
        else:
            print(f"   ✗ '{input_term}' → NOT FOUND or WRONG")

    print(f"\n   Result: {passed}/{len(test_cases)} case variations handled")
    return passed == len(test_cases)


def main():
    """Run all tests."""
    # Check for versioned filename first
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
    print("LEX STREAM DATABASE FUNCTIONALITY TESTS")
    print("=" * 60)

    # Load database
    print("\nLoading database...")
    db = LexStreamDB(db_path)
    print(f"  Loaded {len(db.terms)} terms")

    # Run tests
    results = {}
    results['abbreviation'] = test_abbreviation_expansion(db)
    results['spell_check'] = test_spell_checker(db)
    results['synonym'] = test_synonym_finder(db)
    results['mesh'] = test_mesh_detector(db)
    results['component'] = test_component_detector(db)
    results['case'] = test_case_insensitivity(db)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        print("\nDatabase is ready for production use in Lex Stream!")
        return 0
    else:
        print(f"\n⚠ {total - passed} tests failed")
        print("\nSome agent functionality may be limited.")
        return 1


if __name__ == '__main__':
    exit(main())
