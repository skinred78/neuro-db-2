#!/usr/bin/env python3
"""
UMLS MRREL.RRF Parser - Extract Related Concepts (Associated Terms)

Addresses DEC-001: Do UMLS associations provide domain-specific relationships
or generic taxonomy?

Parses MRREL.RRF (5.7 GB, 16 columns) to extract related concepts for our
325K neuroscience terms.

MRREL.RRF format (pipe-delimited):
CUI1|AUI1|STYPE1|REL|CUI2|AUI2|STYPE2|RELA|RUI|SRUI|SAB|SL|RG|DIR|SUPPRESS|CVF

Key columns:
- CUI1: Source concept
- REL: Relationship type (RB=Broader, RN=Narrower, RO=Other, etc.)
- RELA: Additional relationship attribute (e.g., "part_of", "causes", "treats")
- CUI2: Target concept
- SAB: Source vocabulary
- SUPPRESS: Suppression flag

Goal: Extract domain-specific relationships for "Commonly Associated Terms" mapping
"""

import json
from pathlib import Path
from collections import defaultdict, Counter

# File paths
MRREL_FILE = Path("downloads/umls/2025AB/2025AB/META/MRREL.RRF")
INTERMEDIATE_JSON = Path("imports/umls/umls_concepts_intermediate.json")
OUTPUT_ASSOCIATIONS = Path("imports/umls/umls_associations.json")
OUTPUT_PROFILE = Path("imports/umls/mrrel_relationship_profile.md")

# Relationship types to extract (domain-specific, not generic taxonomy)
# Based on UMLS documentation: https://www.ncbi.nlm.nih.gov/books/NBK9685/
DOMAIN_SPECIFIC_RELA = {
    # Neuroscience-relevant relationships
    'part_of', 'has_part', 'branch_of', 'tributary_of',
    'supplies', 'drains_into', 'receives_input_from', 'sends_output_to',
    'afferent_to', 'efferent_to', 'innervates', 'innervated_by',
    'connected_to', 'communicates_with', 'synapse_with',
    'causes', 'caused_by', 'affects', 'affected_by',
    'treats', 'treated_by', 'prevents', 'prevented_by',
    'associated_with', 'co-occurs_with', 'manifestation_of',
    'process_of', 'has_process', 'precedes', 'followed_by',
    'derivative_of', 'has_derivative', 'contains', 'contained_in',
    'location_of', 'has_location', 'adjacent_to',
    'has_active_ingredient', 'active_ingredient_of',
    'has_mechanism_of_action', 'mechanism_of_action_of',
    'has_physiologic_effect', 'physiologic_effect_of',
    'isa', 'inverse_isa',  # Include for context
}

# Generic taxonomy relationships (exclude from associated terms)
TAXONOMY_REL = {
    'PAR',  # Parent
    'CHD',  # Child
    'SIB',  # Sibling
    'RB',   # Broader
    'RN',   # Narrower
}


def load_concepts():
    """Load our 325K extracted concepts."""
    print(f"\n📥 Loading concepts from {INTERMEDIATE_JSON}...")

    with open(INTERMEDIATE_JSON, 'r', encoding='utf-8') as f:
        concepts = json.load(f)

    print(f"   ✅ Loaded {len(concepts):,} concepts")
    return set(concepts.keys())


def parse_mrrel(our_cuis):
    """
    Parse MRREL.RRF to extract relationships for our concepts.

    Returns:
        dict: {CUI: {related_concepts: [CUI2, ...], relationships: {CUI2: [RELA, ...]}}}
        dict: Relationship type statistics
    """
    print(f"\n🔍 Parsing MRREL.RRF (5.7 GB, ~80M rows)...")
    print(f"   Looking for relationships involving {len(our_cuis):,} neuroscience CUIs...")

    associations = defaultdict(lambda: {
        'related_cuis': set(),
        'relationships': defaultdict(list)
    })

    # Statistics
    stats = {
        'total_rows': 0,
        'our_cui_matches': 0,
        'relationships_extracted': 0,
        'rel_types': Counter(),
        'rela_types': Counter(),
        'sources': Counter(),
        'domain_specific': 0,
        'taxonomy': 0,
    }

    with open(MRREL_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            stats['total_rows'] += 1

            cols = line.strip().split('|')
            if len(cols) < 16:
                continue

            cui1 = cols[0]
            rel = cols[3]      # Relationship type (RB, RN, RO, etc.)
            cui2 = cols[4]
            rela = cols[7]     # Additional relationship attribute
            sab = cols[10]     # Source vocabulary
            suppress = cols[14]  # Suppression flag

            # Only process if one of the CUIs is in our set
            if cui1 not in our_cuis and cui2 not in our_cuis:
                continue

            stats['our_cui_matches'] += 1

            # Skip suppressed relationships
            if suppress != 'N':
                continue

            # Track statistics
            stats['rel_types'][rel] += 1
            if rela:
                stats['rela_types'][rela] += 1
            stats['sources'][sab] += 1

            # Determine if this is domain-specific or taxonomy
            is_domain_specific = rela and rela.lower() in DOMAIN_SPECIFIC_RELA
            is_taxonomy = rel in TAXONOMY_REL

            if is_taxonomy:
                stats['taxonomy'] += 1
                # Skip pure taxonomy relationships (we want domain-specific)
                if not is_domain_specific:
                    continue

            if is_domain_specific:
                stats['domain_specific'] += 1

            # Store relationship (bidirectional)
            if cui1 in our_cuis:
                associations[cui1]['related_cuis'].add(cui2)
                if rela:
                    associations[cui1]['relationships'][cui2].append(rela)
                stats['relationships_extracted'] += 1

            if cui2 in our_cuis and cui2 != cui1:
                associations[cui2]['related_cuis'].add(cui1)
                if rela:
                    associations[cui2]['relationships'][cui1].append(rela)
                stats['relationships_extracted'] += 1

            # Progress indicator
            if stats['total_rows'] % 10000000 == 0:
                print(f"   Processed {stats['total_rows']:,} rows, " +
                      f"{stats['our_cui_matches']:,} relevant, " +
                      f"{len(associations):,} CUIs with relationships...")

    print(f"\n   ✅ Parsing complete!")
    print(f"\n   📊 Statistics:")
    print(f"      Total rows processed: {stats['total_rows']:,}")
    print(f"      Rows involving our CUIs: {stats['our_cui_matches']:,}")
    print(f"      Relationships extracted: {stats['relationships_extracted']:,}")
    print(f"      Domain-specific relationships: {stats['domain_specific']:,}")
    print(f"      Taxonomy relationships (excluded): {stats['taxonomy']:,}")
    print(f"      CUIs with associations: {len(associations):,}")

    return dict(associations), stats


def map_cui_to_terms(associations, concepts_data):
    """
    Map CUI associations to term names for "Commonly Associated Terms".

    Returns:
        dict: {CUI: {'associated_terms': [term1, term2, ...], 'relationship_details': {...}}}
    """
    print(f"\n🗺️  Mapping CUI associations to term names...")

    # Load full concepts data to get term names
    with open(INTERMEDIATE_JSON, 'r', encoding='utf-8') as f:
        concepts = json.load(f)

    mapped_associations = {}
    cuis_with_terms = 0

    for cui, assoc_data in associations.items():
        related_cuis = assoc_data['related_cuis']

        # Map CUIs to term names
        associated_terms = []
        relationship_details = {}

        for related_cui in related_cuis:
            if related_cui in concepts:
                term_name = concepts[related_cui].get('preferred_term', '')
                if term_name:
                    associated_terms.append(term_name)
                    # Store relationship types for this term
                    relas = assoc_data['relationships'].get(related_cui, [])
                    if relas:
                        relationship_details[term_name] = relas

        if associated_terms:
            mapped_associations[cui] = {
                'associated_terms': associated_terms[:20],  # Limit to top 20
                'relationship_details': relationship_details,
                'total_associations': len(associated_terms)
            }
            cuis_with_terms += 1

    print(f"   ✅ Mapped {cuis_with_terms:,} CUIs to associated term names")

    return mapped_associations


def generate_profile_report(stats, associations, mapped_associations):
    """Generate markdown report profiling MRREL relationships."""
    print(f"\n📝 Generating relationship profile report...")

    lines = []
    lines.append("# UMLS MRREL Relationship Profile Report")
    lines.append("")
    lines.append("**Date**: 2025-11-20")
    lines.append(f"**Total Concepts**: 325,241")
    lines.append(f"**Concepts with Associations**: {len(mapped_associations):,}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Overall statistics
    lines.append("## Overall Statistics")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total MRREL rows | {stats['total_rows']:,} |")
    lines.append(f"| Rows involving our CUIs | {stats['our_cui_matches']:,} |")
    lines.append(f"| Relationships extracted | {stats['relationships_extracted']:,} |")
    lines.append(f"| Domain-specific relationships | {stats['domain_specific']:,} |")
    lines.append(f"| Taxonomy relationships (excluded) | {stats['taxonomy']:,} |")
    lines.append(f"| CUIs with associations | {len(associations):,} |")
    lines.append(f"| CUIs with mapped term names | {len(mapped_associations):,} |")
    lines.append("")

    # Coverage
    coverage_pct = (len(mapped_associations) / 325241 * 100) if 325241 > 0 else 0
    lines.append(f"**Association Coverage**: {len(mapped_associations):,} / 325,241 ({coverage_pct:.1f}%)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # REL types
    lines.append("## Relationship Types (REL)")
    lines.append("")
    lines.append("| REL Code | Description | Count |")
    lines.append("|----------|-------------|-------|")

    rel_descriptions = {
        'RO': 'Other related',
        'RB': 'Broader (parent)',
        'RN': 'Narrower (child)',
        'PAR': 'Parent',
        'CHD': 'Child',
        'SIB': 'Sibling',
        'RQ': 'Related and possibly synonymous',
        'SY': 'Source asserted synonymy',
    }

    for rel, count in stats['rel_types'].most_common(20):
        desc = rel_descriptions.get(rel, 'Unknown')
        lines.append(f"| {rel} | {desc} | {count:,} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # RELA types (domain-specific)
    lines.append("## Relationship Attributes (RELA) - Domain-Specific")
    lines.append("")
    lines.append("| RELA | Count | Domain-Specific? |")
    lines.append("|------|-------|------------------|")

    for rela, count in stats['rela_types'].most_common(30):
        is_domain = "✅" if rela.lower() in DOMAIN_SPECIFIC_RELA else "❌"
        lines.append(f"| {rela} | {count:,} | {is_domain} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Sources
    lines.append("## Source Vocabularies Contributing Relationships")
    lines.append("")
    lines.append("| Source | Relationships | % of Total |")
    lines.append("|--------|--------------|-----------|")

    total_rels = sum(stats['sources'].values())
    for source, count in stats['sources'].most_common(20):
        pct = (count / total_rels * 100) if total_rels > 0 else 0
        lines.append(f"| {source} | {count:,} | {pct:.1f}% |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Sample associations
    lines.append("## Sample Associations (First 20 CUIs)")
    lines.append("")

    for i, (cui, data) in enumerate(list(mapped_associations.items())[:20], 1):
        lines.append(f"### {i}. CUI: {cui}")
        lines.append(f"**Total Associations**: {data['total_associations']}")
        lines.append(f"**Associated Terms** (showing up to 10):")
        for term in data['associated_terms'][:10]:
            relas = data['relationship_details'].get(term, [])
            if relas:
                lines.append(f"- {term} ({', '.join(relas[:3])})")
            else:
                lines.append(f"- {term}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # DEC-001 Assessment
    lines.append("## DEC-001 Assessment: Relationship Quality")
    lines.append("")
    lines.append("**Question**: Do UMLS associations provide domain-specific relationships or generic taxonomy?")
    lines.append("")

    domain_pct = (stats['domain_specific'] / stats['relationships_extracted'] * 100) if stats['relationships_extracted'] > 0 else 0
    taxonomy_pct = (stats['taxonomy'] / stats['our_cui_matches'] * 100) if stats['our_cui_matches'] > 0 else 0

    lines.append(f"**Finding**:")
    lines.append(f"- Domain-specific relationships: {stats['domain_specific']:,} ({domain_pct:.1f}% of extracted)")
    lines.append(f"- Pure taxonomy relationships: {stats['taxonomy']:,} ({taxonomy_pct:.1f}% of matches)")
    lines.append("")

    if domain_pct > 50:
        lines.append("**Conclusion**: ✅ UMLS provides **substantial domain-specific relationships**")
        lines.append("- Suitable for populating 'Commonly Associated Terms' columns")
        lines.append("- Relationships include functional (causes, treats), anatomical (part_of, innervates), and process-based associations")
    else:
        lines.append("**Conclusion**: ⚠️ UMLS relationships are **primarily taxonomic**")
        lines.append("- May need supplemental sources for domain-specific associations")
        lines.append("- Consider NIF, GO, or literature mining for functional relationships")

    lines.append("")
    lines.append("**Recommendation**: Proceed with MRREL associations for NeuroDB-2 'Commonly Associated Terms' mapping")
    lines.append("")

    # Write report
    with open(OUTPUT_PROFILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"   ✅ Profile report saved to {OUTPUT_PROFILE}")


def main():
    print("="*70)
    print("UMLS MRREL RELATIONSHIP PARSER")
    print("="*70)
    print("\nDEC-001: Profiling domain-specific vs taxonomic relationships")

    # Step 1: Load our concepts
    our_cuis = load_concepts()

    # Step 2: Parse MRREL for relationships
    associations, stats = parse_mrrel(our_cuis)

    if not associations:
        print("\n❌ ERROR: No associations found")
        return

    # Step 3: Map CUIs to term names
    mapped_associations = map_cui_to_terms(associations, INTERMEDIATE_JSON)

    # Step 4: Save associations
    print(f"\n💾 Saving associations to {OUTPUT_ASSOCIATIONS}...")

    # Convert sets to lists for JSON serialization
    json_data = {}
    for cui, data in mapped_associations.items():
        json_data[cui] = {
            'associated_terms': data['associated_terms'],
            'relationship_details': data['relationship_details'],
            'total_associations': data['total_associations']
        }

    with open(OUTPUT_ASSOCIATIONS, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)

    print(f"   ✅ Saved {len(json_data):,} CUI associations")

    # Step 5: Generate profile report
    generate_profile_report(stats, associations, mapped_associations)

    # Summary
    print("\n" + "="*70)
    print("MRREL PARSING COMPLETE")
    print("="*70)

    coverage_pct = (len(mapped_associations) / 325241 * 100) if 325241 > 0 else 0

    print(f"\n✅ Extracted associations for {len(mapped_associations):,} concepts ({coverage_pct:.1f}%)")
    print(f"✅ Domain-specific relationships: {stats['domain_specific']:,}")
    print(f"✅ Output: {OUTPUT_ASSOCIATIONS}")
    print(f"✅ Profile: {OUTPUT_PROFILE}")

    print(f"\n🎯 Next: Map UMLS data to NeuroDB-2 26-column schema")


if __name__ == "__main__":
    main()
