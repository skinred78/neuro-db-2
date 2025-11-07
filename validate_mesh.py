#!/usr/bin/env python3
"""
MeSH Term Validator using NCBI E-utilities API
Searches and validates MeSH terms from the official NCBI MeSH database
"""

import requests
import json
import time
from urllib.parse import quote

# Terms to validate
TERMS = [
    "Anemia",
    "Apraxia",
    "Atrial Fibrillation",
    "Atrophy",
    "Autosomal Recessive Disorders"
]

def search_mesh(term):
    """Search MeSH database for a term and return top results"""
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=mesh&term={quote(term)}&retmode=json&retmax=5"
    response = requests.get(url)
    data = response.json()
    return data['esearchresult'].get('idlist', [])

def get_mesh_details(mesh_id):
    """Get details for a specific MeSH ID"""
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=mesh&id={mesh_id}&retmode=json"
    response = requests.get(url)
    data = response.json()

    if mesh_id in data['result']:
        result = data['result'][mesh_id]
        return {
            'id': mesh_id,
            'terms': result.get('ds_meshterms', []),
            'scope': result.get('ds_scopenote', ''),
            'year': result.get('ds_yearintroduced', '')
        }
    return None

def validate_term(search_term):
    """Validate a search term against MeSH database"""
    print(f"\n{'='*80}")
    print(f"VALIDATING: {search_term}")
    print(f"{'='*80}")

    # Search for the term
    ids = search_mesh(search_term)

    if not ids:
        print(f"API Result: NO MATCHES FOUND")
        print(f"MeSH Term: (empty)")
        print(f"Rationale: Term not found in official MeSH database")
        print(f"Status: EMPTY (acceptable)")
        return None

    # Get details for top results
    print(f"API Result: Found {len(ids)} potential matches")
    print(f"\nTop 3 MeSH matches:\n")

    results = []
    for i, mesh_id in enumerate(ids[:3], 1):
        details = get_mesh_details(mesh_id)
        if details and details['terms']:
            official_term = details['terms'][0]  # First term is the official descriptor
            results.append({
                'rank': i,
                'id': mesh_id,
                'official_term': official_term,
                'all_terms': details['terms'],
                'scope': details['scope'][:200] + '...' if len(details['scope']) > 200 else details['scope']
            })

            print(f"{i}. {official_term}")
            print(f"   MeSH ID: {mesh_id}")
            print(f"   Synonyms: {', '.join(details['terms'][1:4]) if len(details['terms']) > 1 else 'None'}")
            print(f"   Scope: {results[-1]['scope']}")
            print()

        time.sleep(0.1)  # Rate limiting

    # Determine exact vs close match
    if results:
        top_result = results[0]
        is_exact = search_term.lower() in [t.lower() for t in top_result['all_terms']]

        print(f"RECOMMENDATION:")
        print(f"  MeSH Term: {top_result['official_term']}")
        print(f"  Match Type: {'EXACT MATCH' if is_exact else 'CLOSE MATCH - HUMAN REVIEW NEEDED'}")
        print(f"  Confidence: {'HIGH' if is_exact else 'MEDIUM'}")
        print(f"  Status: {'CONFIRMED' if is_exact else 'REVIEW REQUIRED'}")

        return {
            'search_term': search_term,
            'mesh_term': top_result['official_term'],
            'match_type': 'exact' if is_exact else 'close',
            'confidence': 'HIGH' if is_exact else 'MEDIUM',
            'status': 'CONFIRMED' if is_exact else 'REVIEW_REQUIRED',
            'mesh_id': top_result['id'],
            'alternatives': [r['official_term'] for r in results[1:]] if len(results) > 1 else []
        }

    return None

def main():
    """Main validation function"""
    print("="*80)
    print("MESH TERM VALIDATION REPORT")
    print("Using NCBI E-utilities API")
    print("="*80)

    results = []
    for term in TERMS:
        result = validate_term(term)
        results.append(result)
        time.sleep(0.3)  # Rate limiting between requests

    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")

    confirmed = [r for r in results if r and r['status'] == 'CONFIRMED']
    review_needed = [r for r in results if r and r['status'] == 'REVIEW_REQUIRED']
    not_found = [r for r in results if r is None]

    print(f"Total terms validated: {len(TERMS)}")
    print(f"  Exact matches (CONFIRMED): {len(confirmed)}")
    print(f"  Close matches (REVIEW NEEDED): {len(review_needed)}")
    print(f"  Not found in MeSH: {len(not_found)}")

    print(f"\n{'='*80}")
    print("DETAILED RESULTS FOR CSV IMPORT")
    print(f"{'='*80}\n")

    for i, (term, result) in enumerate(zip(TERMS, results), 1):
        if result:
            print(f"{i}. {term} → {result['mesh_term']} [{result['status']}]")
        else:
            print(f"{i}. {term} → (empty) [NOT_FOUND]")

    # Save results to JSON
    with open('/Users/sam/NeuroDB-2/mesh_validation_results.json', 'w') as f:
        json.dump({
            'terms_validated': TERMS,
            'results': results,
            'summary': {
                'total': len(TERMS),
                'confirmed': len(confirmed),
                'review_needed': len(review_needed),
                'not_found': len(not_found)
            }
        }, f, indent=2)

    print(f"\nResults saved to: /Users/sam/NeuroDB-2/mesh_validation_results.json")

if __name__ == '__main__':
    main()
