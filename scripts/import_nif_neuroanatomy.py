#!/usr/bin/env python3
"""
NIF Neuroanatomy (NeuroNames) Importer for NeuroDB-2

Imports neuroanatomy terms from the NIF-GrossAnatomy.ttl file which contains
NeuroNames data integrated into the Neuroscience Information Framework Standard (NIFSTD).

Source: https://github.com/SciCrunch/NIF-Ontology
License: Creative Commons Attribution 4.0 International License

Data flow:
1. Download NIF-GrossAnatomy.ttl from GitHub
2. Parse TTL (Turtle/RDF format) using rdflib
3. Extract terms with properties (label, definition, synonyms)
4. Map to NeuroDB-2 extended 26-column schema
5. Add source metadata (source='nif', priority=2)
6. Validate structure and export to CSV

Expected output: ~3,000 neuroanatomy terms
"""

import sys
import csv
import requests
from pathlib import Path
from datetime import datetime

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.schema_mapper import NEURODB_SCHEMA, create_empty_row
from lib.source_tagger import add_source_metadata
from lib.validators import generate_validation_report, print_validation_report

# Try to import rdflib
try:
    from rdflib import Graph, URIRef, Namespace
    from rdflib.namespace import RDFS, OWL, SKOS
except ImportError:
    print("ERROR: rdflib not installed. Install with: pip install rdflib")
    sys.exit(1)


# Configuration
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/SciCrunch/NIF-Ontology/master/ttl"
NIF_GROSS_ANATOMY_URL = f"{GITHUB_RAW_BASE}/NIF-GrossAnatomy.ttl"
OUTPUT_DIR = Path("imports/nif")
OUTPUT_FILE = OUTPUT_DIR / "nif_neuroanatomy_imported.csv"
TEMP_TTL_FILE = OUTPUT_DIR / "NIF-GrossAnatomy.ttl"

# RDF namespaces (will be refined based on actual TTL structure)
NIFSTD = Namespace("http://uri.neuinfo.org/nif/nifstd/")
OBOREL = Namespace("http://purl.obolibrary.org/obo/")


def download_nif_data():
    """
    Downloads NIF-GrossAnatomy.ttl from GitHub.

    Returns:
        Path: Path to downloaded TTL file
    """
    print(f"\n📥 Downloading NIF-GrossAnatomy.ttl from GitHub...")
    print(f"   URL: {NIF_GROSS_ANATOMY_URL}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(NIF_GROSS_ANATOMY_URL, timeout=30)
        response.raise_for_status()

        with open(TEMP_TTL_FILE, 'wb') as f:
            f.write(response.content)

        file_size_mb = TEMP_TTL_FILE.stat().st_size / (1024 * 1024)
        print(f"   ✅ Downloaded: {file_size_mb:.2f} MB")
        print(f"   Saved to: {TEMP_TTL_FILE}")

        return TEMP_TTL_FILE

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Download failed: {str(e)}")
        print(f"\n   Manual download instructions:")
        print(f"   1. Visit: {NIF_GROSS_ANATOMY_URL}")
        print(f"   2. Save file to: {TEMP_TTL_FILE}")
        print(f"   3. Re-run this script")
        sys.exit(1)


def parse_nif_ttl(ttl_path):
    """
    Parses NIF-GrossAnatomy.ttl file using rdflib.

    Args:
        ttl_path (Path): Path to TTL file

    Returns:
        list: List of term dictionaries with extracted properties
    """
    print(f"\n🔍 Parsing NIF-GrossAnatomy.ttl...")

    graph = Graph()
    graph.parse(ttl_path, format='turtle')

    print(f"   Loaded {len(graph)} triples")

    terms = []
    processed_count = 0

    # Query all classes (neuroanatomy terms are typically OWL classes)
    for subject in graph.subjects(predicate=None, object=OWL.Class):
        processed_count += 1

        # Extract properties
        term_data = {
            'uri': str(subject),
            'label': None,
            'definition': None,
            'synonyms': [],
            'abbreviations': [],
            'related_terms': []
        }

        # Get label (rdfs:label or skos:prefLabel)
        for label in graph.objects(subject, RDFS.label):
            term_data['label'] = str(label)
            break

        # Get definition (multiple possible predicates)
        for pred in [SKOS.definition, URIRef("http://purl.obolibrary.org/obo/IAO_0000115")]:
            for definition in graph.objects(subject, pred):
                term_data['definition'] = str(definition)
                break
            if term_data['definition']:
                break

        # Get synonyms (exactSynonym, related synonym, etc.)
        for syn_pred in [
            URIRef("http://www.geneontology.org/formats/oboInOwl#hasExactSynonym"),
            URIRef("http://www.geneontology.org/formats/oboInOwl#hasRelatedSynonym"),
            URIRef("http://www.geneontology.org/formats/oboInOwl#hasBroadSynonym"),
            URIRef("http://www.geneontology.org/formats/oboInOwl#hasNarrowSynonym")
        ]:
            for synonym in graph.objects(subject, syn_pred):
                syn_text = str(synonym)
                if syn_text and syn_text not in term_data['synonyms']:
                    term_data['synonyms'].append(syn_text)

        # Get related terms (broader/narrower concepts)
        for related_pred in [
            URIRef("http://www.w3.org/2004/02/skos/core#broader"),
            URIRef("http://www.w3.org/2004/02/skos/core#narrower"),
            URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf")
        ]:
            for related in graph.objects(subject, related_pred):
                # Get label of related term
                for related_label in graph.objects(related, RDFS.label):
                    related_text = str(related_label)
                    if related_text and related_text not in term_data['related_terms']:
                        term_data['related_terms'].append(related_text)

        # Only keep terms with at least a label
        if term_data['label']:
            terms.append(term_data)

        # Progress indicator
        if processed_count % 1000 == 0:
            print(f"   Processed {processed_count} classes, extracted {len(terms)} terms...")

    print(f"   ✅ Extracted {len(terms)} neuroanatomy terms")
    return terms


def map_nif_to_neurodb_schema(nif_terms):
    """
    Maps NIF term data to NeuroDB-2 extended 26-column schema.

    Args:
        nif_terms (list): List of term dictionaries from parse_nif_ttl()

    Returns:
        list: List of row dictionaries conforming to NEURODB_SCHEMA
    """
    print(f"\n🗺️  Mapping {len(nif_terms)} terms to NeuroDB-2 schema...")

    rows = []
    seen_terms = set()  # Track duplicates
    empty_def_count = 0

    for term in nif_terms:
        # Skip duplicates (keep first occurrence)
        term_key = term['label'].lower().strip()
        if term_key in seen_terms:
            continue
        seen_terms.add(term_key)

        row = create_empty_row()

        # Core fields
        row['Term'] = term['label']
        definition = (term.get('definition') or '').strip()

        # Use placeholder if no definition available
        # Note: NIF-GrossAnatomy is primarily taxonomic, ~87% lack definitions
        if not definition:
            definition = f"Neuroanatomical structure (definition not available in NIF source)"
            empty_def_count += 1

        row['Definition'] = definition

        # Synonyms (max 3)
        for i, syn in enumerate(term['synonyms'][:3]):
            row[f'Synonym {i+1}'] = syn

        # Abbreviations (extract from synonyms if they look like abbreviations)
        # Simple heuristic: all caps, 2-6 characters
        abbrevs = [s for s in term['synonyms'] if s.isupper() and 2 <= len(s) <= 6]
        if abbrevs:
            row['Abbreviation'] = abbrevs[0]

        # Associated terms (max 8)
        for i, related in enumerate(term['related_terms'][:8]):
            row[f'Commonly Associated Term {i+1}'] = related

        # Add source metadata
        add_source_metadata(row, 'nif')

        rows.append(row)

    print(f"   ✅ Mapped {len(rows)} rows ({empty_def_count} with placeholder definitions)")
    return rows


def write_csv(rows, output_path):
    """
    Writes rows to CSV with proper quoting and UTF-8 encoding.

    Args:
        rows (list): List of row dictionaries
        output_path (Path): Output CSV path
    """
    print(f"\n💾 Writing CSV to {output_path}...")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=NEURODB_SCHEMA, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    print(f"   ✅ Wrote {len(rows)} rows")


def import_nif_neuroanatomy():
    """
    Main import pipeline for NIF neuroanatomy data.
    """
    print("="*70)
    print("NIF NEUROANATOMY (NEURONAMES) IMPORTER")
    print("="*70)

    # Step 1: Download data
    if TEMP_TTL_FILE.exists():
        print(f"\n✓ Using existing TTL file: {TEMP_TTL_FILE}")
        ttl_file = TEMP_TTL_FILE
    else:
        ttl_file = download_nif_data()

    # Step 2: Parse TTL
    nif_terms = parse_nif_ttl(ttl_file)

    if not nif_terms:
        print("\n❌ ERROR: No terms extracted from TTL file")
        sys.exit(1)

    # Step 3: Map to schema
    rows = map_nif_to_neurodb_schema(nif_terms)

    # Step 4: Write CSV
    write_csv(rows, OUTPUT_FILE)

    # Step 5: Validate
    print(f"\n🔍 Running structural validation...")
    report = generate_validation_report(OUTPUT_FILE)
    print_validation_report(report)

    # Step 6: Summary
    print("\n" + "="*70)
    print("IMPORT COMPLETE")
    print("="*70)
    print(f"\nOutput file: {OUTPUT_FILE}")
    print(f"Total terms: {len(rows)}")
    print(f"Validation: {report['summary']}")
    print(f"Source: nif (priority 2)")
    print(f"Date added: {datetime.now().strftime('%Y-%m-%d')}")

    if report['overall_valid']:
        print("\n✅ SUCCESS - Ready for merging with other sources")
    else:
        print("\n❌ FAILED - Fix validation errors before proceeding")
        sys.exit(1)


if __name__ == "__main__":
    import_nif_neuroanatomy()
