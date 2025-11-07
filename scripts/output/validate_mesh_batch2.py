#!/usr/bin/env python3
"""
MeSH Validation for BATCH 2 (Medium Letters A) - 13 terms from NINDS Glossary
Uses NCBI E-utilities API to validate MeSH terms
"""

import requests
import json
import time
from typing import Dict, Optional

# Terms to validate
TERMS = [
    "Encephalitis",
    "Encephalopathy",
    "Enzymes",
    "Immunoglobulins",
    "Inflammation",
    "Intravenous immunoglobulin",
    "Learning Disabilities",
    "Lipidoses",
    "Lipids",
    "Hydromyelia",
    "Hypersomnia",
    "Hypertonia",
    "Hypotonia"
]

def search_mesh_term(term: str) -> Optional[Dict]:
    """Search for a MeSH term using NCBI E-utilities"""
    # Step 1: Search for exact MeSH descriptor match
    # Use [MeSH Terms] field to search only in MeSH descriptors/headings
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=mesh&term={term}[MeSH Terms]&retmode=json"

    try:
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()

        # Check if we found any results
        id_list = data.get('esearchresult', {}).get('idlist', [])
        if not id_list:
            return None

        # Step 2: Get detailed information for all results to find exact match
        time.sleep(0.2)  # Rate limiting

        # Check up to first 5 results for exact match
        for mesh_id in id_list[:5]:
            summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=mesh&id={mesh_id}&retmode=json"

            response = requests.get(summary_url)
            response.raise_for_status()
            summary_data = response.json()

            # Extract the MeSH term details
            result = summary_data.get('result', {}).get(mesh_id, {})

            if result:
                mesh_terms = result.get('ds_meshterms', [])
                mesh_ui = result.get('ds_meshui', '')
                scope_note = result.get('ds_scopenote', '')
                primary_term = mesh_terms[0] if mesh_terms else None

                # Check if any of the MeSH terms match our search term exactly (case-insensitive)
                for mesh_variant in mesh_terms:
                    if mesh_variant.lower() == term.lower():
                        return {
                            'mesh_id': mesh_id,
                            'mesh_ui': mesh_ui,
                            'primary_term': primary_term,
                            'matched_term': mesh_variant,
                            'all_terms': mesh_terms,
                            'scope_note': scope_note,
                            'record_type': result.get('ds_recordtype', '')
                        }

                # If no exact match, wait before next check
                time.sleep(0.15)

        # No exact match found, return first result as close match
        mesh_id = id_list[0]
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=mesh&id={mesh_id}&retmode=json"

        response = requests.get(summary_url)
        response.raise_for_status()
        summary_data = response.json()

        result = summary_data.get('result', {}).get(mesh_id, {})
        if result:
            mesh_terms = result.get('ds_meshterms', [])
            mesh_ui = result.get('ds_meshui', '')
            scope_note = result.get('ds_scopenote', '')

            return {
                'mesh_id': mesh_id,
                'mesh_ui': mesh_ui,
                'primary_term': mesh_terms[0] if mesh_terms else None,
                'matched_term': None,
                'all_terms': mesh_terms,
                'scope_note': scope_note,
                'record_type': result.get('ds_recordtype', '')
            }

        return None

    except Exception as e:
        print(f"Error searching for '{term}': {e}")
        return None

def validate_all_terms():
    """Validate all terms and generate report"""
    results = []

    print("MESH VALIDATION - BATCH 2 (NINDS Glossary)")
    print("=" * 70)
    print(f"\nValidating {len(TERMS)} terms using NCBI E-utilities API...\n")

    for i, term in enumerate(TERMS, 1):
        print(f"[{i}/{len(TERMS)}] Searching: {term}...", end=" ")

        result = search_mesh_term(term)

        if result:
            primary_term = result['primary_term']
            matched_term = result.get('matched_term')
            exact_match = (matched_term is not None)

            results.append({
                'search_term': term,
                'found': True,
                'exact_match': exact_match,
                'mesh_term': primary_term,
                'matched_term': matched_term if matched_term else primary_term,
                'mesh_ui': result['mesh_ui'],
                'all_terms': result['all_terms'],
                'scope_note': result['scope_note'][:100] + '...' if len(result['scope_note']) > 100 else result['scope_note']
            })

            if exact_match:
                print(f"✓ EXACT MATCH: {matched_term}")
            else:
                print(f"⚠ CLOSE MATCH: {primary_term}")
        else:
            results.append({
                'search_term': term,
                'found': False,
                'exact_match': False,
                'mesh_term': None,
                'mesh_ui': None,
                'all_terms': [],
                'scope_note': ''
            })
            print("✗ NOT FOUND")

        time.sleep(0.15)  # Rate limiting

    return results

def generate_report(results):
    """Generate detailed validation report"""

    exact_matches = [r for r in results if r['found'] and r['exact_match']]
    close_matches = [r for r in results if r['found'] and not r['exact_match']]
    not_found = [r for r in results if not r['found']]

    print("\n" + "=" * 70)
    print("VALIDATION REPORT")
    print("=" * 70)

    print(f"\nSUMMARY:")
    print(f"- Total terms validated: {len(results)}")
    print(f"- Exact matches: {len(exact_matches)} ({len(exact_matches)/len(results)*100:.1f}%)")
    print(f"- Close matches: {len(close_matches)} ({len(close_matches)/len(results)*100:.1f}%)")
    print(f"- Not found: {len(not_found)} ({len(not_found)/len(results)*100:.1f}%)")

    if exact_matches:
        print(f"\n✓ EXACT MATCHES ({len(exact_matches)} terms):")
        for r in exact_matches:
            print(f"  • {r['search_term']} → {r['mesh_term']} ({r['mesh_ui']})")

    if close_matches:
        print(f"\n⚠ CLOSE MATCHES ({len(close_matches)} terms):")
        for r in close_matches:
            print(f"  • Search: '{r['search_term']}'")
            print(f"    MeSH: '{r['mesh_term']}' ({r['mesh_ui']})")
            print(f"    All terms: {', '.join(r['all_terms'][:3])}")

    if not_found:
        print(f"\n✗ NOT FOUND ({len(not_found)} terms):")
        for r in not_found:
            print(f"  • {r['search_term']}")
            print(f"    Rationale: No MeSH descriptor found via NCBI E-utilities")

    # CSV output format
    print("\n" + "=" * 70)
    print("CSV FORMAT OUTPUT")
    print("=" * 70)
    print("\nTerm|MeSH Term|MeSH UI|Status|Confidence")
    print("-" * 70)

    for r in results:
        if r['found']:
            status = "EXACT" if r['exact_match'] else "CLOSE"
            confidence = "HIGH" if r['exact_match'] else "MEDIUM"
            print(f"{r['search_term']}|{r['mesh_term']}|{r['mesh_ui']}|{status}|{confidence}")
        else:
            print(f"{r['search_term']}|||NOT_FOUND|N/A")

    # Save JSON results
    output_file = "/Users/sam/NeuroDB-2/scripts/output/mesh_validation_batch2_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Full results saved to: {output_file}")

if __name__ == "__main__":
    results = validate_all_terms()
    generate_report(results)
