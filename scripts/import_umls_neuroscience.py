#!/usr/bin/env python3
"""
UMLS Neuroscience Term Importer

Extracts neuroscience terms from UMLS Metathesaurus using multi-stage filtering.

Pipeline:
1. Load 1M neuroscience CUIs from filter index
2. Parse MRCONSO.RRF: Extract preferred terms, synonyms, abbreviations
3. Parse MRDEF.RRF: Extract definitions
4. Parse MRREL.RRF: Extract related concepts (DEC-001 profiling)
5. Map to NeuroDB-2 26-column schema
6. Validate and profile data quality

Filtering stages (DEC-002 Option B):
- Stage 1: CUI in neuroscience filter (1M CUIs)
- Stage 2: Language filter (LAT=ENG)
- Stage 3: Suppression filter (SUPPRESS=N)
- Stage 4: Preferred term filter (ISPREF=Y or TTY=PN)
- Stage 5: Keyword filter (for broad semantic types)

Expected output: 150K-250K neuroscience terms
"""

import sys
import csv
import json
from pathlib import Path
from collections import defaultdict, Counter

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

# File paths
UMLS_META_DIR = Path("downloads/umls/2025AB/2025AB/META")
IMPORTS_DIR = Path("imports/umls")

# Input files
NEUROSCIENCE_CUIS_FILE = IMPORTS_DIR / "neuroscience_cuis.txt"
FILTER_STATS_FILE = IMPORTS_DIR / "filter_statistics.json"
MRCONSO_FILE = UMLS_META_DIR / "MRCONSO.RRF"
MRDEF_FILE = UMLS_META_DIR / "MRDEF.RRF"
MRREL_FILE = UMLS_META_DIR / "MRREL.RRF"

# Output files
OUTPUT_CSV = IMPORTS_DIR / "umls_neuroscience_imported.csv"
INTERMEDIATE_JSON = IMPORTS_DIR / "umls_concepts_intermediate.json"

# Broad semantic types requiring keyword filter (DEC-002)
BROAD_SEMANTIC_TYPES = {
    'Pharmacologic Substance',
    'Amino Acid, Peptide, or Protein',
    'Disease or Syndrome',
    'Injury or Poisoning',
    'Gene or Genome',
    'Biologically Active Substance',
    'Enzyme',
    'Nucleic Acid, Nucleoside, or Nucleotide'
}

# Neuroscience keywords for broad type filtering
NEURO_KEYWORDS = [
    'neuro', 'brain', 'cerebr', 'cortex', 'cortical', 'neural',
    'synap', 'axon', 'dendrit', 'glia', 'astrocyt', 'oligodendro',
    'cognit', 'memory', 'psychiatric', 'mental', 'psycho', 'behavior',
    'parkinson', 'alzheimer', 'epilep', 'schizo', 'depress', 'anxiet',
    'autism', 'dementia', 'stroke', 'migraine', 'huntington',
    'dopamin', 'serotonin', 'gaba', 'glutamat', 'acetylcholin',
    'hippocampus', 'amygdala', 'thalamus', 'hypothalamus', 'cerebellum'
]

def load_neuroscience_cuis():
    """Load pre-filtered neuroscience CUIs."""
    print(f"\n📥 Loading neuroscience CUIs from {NEUROSCIENCE_CUIS_FILE}...")

    if not NEUROSCIENCE_CUIS_FILE.exists():
        print(f"❌ ERROR: {NEUROSCIENCE_CUIS_FILE} not found")
        print(f"   Run scripts/build_umls_filter_index.py first")
        sys.exit(1)

    cuis = set()
    with open(NEUROSCIENCE_CUIS_FILE, 'r') as f:
        for line in f:
            cui = line.strip()
            if cui:
                cuis.add(cui)

    print(f"   ✅ Loaded {len(cuis):,} neuroscience CUIs")
    return cuis


def load_cui_semantic_types():
    """Load semantic type mapping to identify broad types needing keyword filter."""
    print(f"\n📥 Loading CUI semantic type mappings...")

    # Parse MRSTY.RRF to build CUI → semantic types mapping
    mrsty_file = UMLS_META_DIR / "MRSTY.RRF"
    cui_types = defaultdict(set)

    with open(mrsty_file, 'r', encoding='utf-8') as f:
        for line in f:
            cols = line.strip().split('|')
            if len(cols) >= 4:
                cui = cols[0]
                semantic_type = cols[3]  # Semantic type name
                cui_types[cui].add(semantic_type)

    print(f"   ✅ Loaded semantic types for {len(cui_types):,} CUIs")
    return cui_types


def contains_neuro_keyword(term_string):
    """Check if term contains any neuroscience keyword."""
    term_lower = term_string.lower()
    return any(keyword in term_lower for keyword in NEURO_KEYWORDS)


def parse_mrconso(neuro_cuis, cui_semantic_types):
    """
    Parse MRCONSO.RRF to extract terms, synonyms, abbreviations.

    MRCONSO.RRF format (18 columns, pipe-delimited):
    CUI|LAT|TS|LUI|STT|SUI|ISPREF|AUI|SAUI|SCUI|SDUI|SAB|TTY|CODE|STR|SRL|SUPPRESS|CVF

    Returns:
        dict: {CUI: {preferred_term, synonyms[], abbreviations[], mesh_code, sources[]}}
    """
    print(f"\n🔍 Parsing MRCONSO.RRF (2.1 GB, ~16M rows)...")
    print(f"   Applying multi-stage filters (DEC-002 Option B)...")

    concepts = defaultdict(lambda: {
        'preferred_term': None,
        'synonyms': [],
        'abbreviations': [],
        'mesh_code': None,
        'sources': set()
    })

    # Filter stage counters
    stage_counts = {
        'total_rows': 0,
        'stage1_cui_match': 0,
        'stage2_english': 0,
        'stage3_not_suppressed': 0,
        'stage4_preferred': 0,
        'stage5_keyword_pass': 0,
        'stage5_keyword_fail': 0
    }

    with open(MRCONSO_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            stage_counts['total_rows'] += 1

            cols = line.strip().split('|')
            if len(cols) < 18:
                continue

            cui = cols[0]
            lat = cols[1]  # Language
            ispref = cols[6]  # Preferred flag
            sab = cols[11]  # Source abbreviation
            tty = cols[12]  # Term type
            code = cols[13]  # Source code
            term_str = cols[14]  # The actual term string
            suppress = cols[16]  # Suppression flag

            # Stage 1: CUI filter (1M neuroscience CUIs)
            if cui not in neuro_cuis:
                continue
            stage_counts['stage1_cui_match'] += 1

            # Stage 2: Language filter (English only)
            if lat != 'ENG':
                continue
            stage_counts['stage2_english'] += 1

            # Stage 3: Suppression filter (not suppressed/obsolete)
            if suppress != 'N':
                continue
            stage_counts['stage3_not_suppressed'] += 1

            # Track source vocabularies
            concepts[cui]['sources'].add(sab)

            # Extract MeSH code if from MeSH source
            if sab == 'MSH' and not concepts[cui]['mesh_code']:
                concepts[cui]['mesh_code'] = code

            # Stage 4: Preferred term extraction
            if ispref == 'Y' or tty == 'PN':
                stage_counts['stage4_preferred'] += 1

                # Stage 5: Keyword filter for broad semantic types
                cui_types = cui_semantic_types.get(cui, set())
                needs_keyword_filter = bool(BROAD_SEMANTIC_TYPES & cui_types)

                if needs_keyword_filter:
                    if not contains_neuro_keyword(term_str):
                        stage_counts['stage5_keyword_fail'] += 1
                        continue  # Skip non-neuro terms from broad types
                    stage_counts['stage5_keyword_pass'] += 1

                # Store preferred term (only if not already set)
                if not concepts[cui]['preferred_term']:
                    concepts[cui]['preferred_term'] = term_str

            # Extract synonyms
            elif tty in ['SY', 'FN', 'MTH_FN']:
                if term_str and term_str not in concepts[cui]['synonyms']:
                    concepts[cui]['synonyms'].append(term_str)

            # Extract abbreviations
            elif tty in ['AB', 'ACR']:
                if term_str and term_str not in concepts[cui]['abbreviations']:
                    concepts[cui]['abbreviations'].append(term_str)

            # Progress indicator
            if stage_counts['total_rows'] % 1000000 == 0:
                print(f"   Processed {stage_counts['total_rows']:,} rows, " +
                      f"{len(concepts):,} concepts with data...")

    print(f"\n   ✅ Parsing complete!")
    print(f"\n   📊 Filter Stage Results:")
    print(f"      Total rows processed: {stage_counts['total_rows']:,}")
    print(f"      Stage 1 (CUI match): {stage_counts['stage1_cui_match']:,}")
    print(f"      Stage 2 (English): {stage_counts['stage2_english']:,}")
    print(f"      Stage 3 (Not suppressed): {stage_counts['stage3_not_suppressed']:,}")
    print(f"      Stage 4 (Preferred terms): {stage_counts['stage4_preferred']:,}")
    print(f"      Stage 5 (Keyword filter):")
    print(f"         Passed: {stage_counts['stage5_keyword_pass']:,}")
    print(f"         Failed: {stage_counts['stage5_keyword_fail']:,}")

    # Filter to concepts with preferred terms
    concepts_with_terms = {
        cui: data for cui, data in concepts.items()
        if data['preferred_term']
    }

    print(f"\n   ✅ Extracted {len(concepts_with_terms):,} concepts with preferred terms")
    return dict(concepts_with_terms)


def parse_mrdef(concepts):
    """
    Parse MRDEF.RRF to add definitions.

    MRDEF.RRF format (8 columns):
    CUI|AUI|ATUI|SATUI|SAB|DEF|SUPPRESS|CVF
    """
    print(f"\n📖 Parsing MRDEF.RRF for definitions...")

    # Priority order for definition sources
    SOURCE_PRIORITY = ['MSH', 'SNOMEDCT_US', 'NCI', 'NCBI', 'HPO', 'OMIM']

    def_counts = 0

    with open(MRDEF_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            cols = line.strip().split('|')
            if len(cols) < 8:
                continue

            cui = cols[0]
            sab = cols[4]  # Source
            definition = cols[5]
            suppress = cols[6]

            # Only process CUIs we have
            if cui not in concepts:
                continue

            # Skip suppressed
            if suppress != 'N':
                continue

            # Check if we should update definition
            existing_def = concepts[cui].get('definition')
            existing_source = concepts[cui].get('definition_source', '')

            # Update if no definition, or better source
            should_update = False
            if not existing_def:
                should_update = True
            elif sab in SOURCE_PRIORITY:
                if existing_source not in SOURCE_PRIORITY:
                    should_update = True
                elif SOURCE_PRIORITY.index(sab) < SOURCE_PRIORITY.index(existing_source):
                    should_update = True

            if should_update:
                concepts[cui]['definition'] = definition
                concepts[cui]['definition_source'] = sab
                def_counts += 1

    # Count concepts with definitions
    with_defs = sum(1 for c in concepts.values() if c.get('definition'))
    coverage = (with_defs / len(concepts) * 100) if concepts else 0

    print(f"   ✅ Added definitions to {with_defs:,} concepts ({coverage:.1f}% coverage)")
    return concepts


def deduplicate_by_term(concepts):
    """
    Deduplicate concepts by preferred term (case-insensitive).
    Keep first occurrence, prioritize MSH source.
    """
    print(f"\n🔄 Deduplicating by term name...")

    unique_terms = {}
    duplicates_removed = 0

    for cui, data in concepts.items():
        term = data.get('preferred_term', '')
        if not term:
            continue

        term_key = term.lower().strip()

        if term_key not in unique_terms:
            unique_terms[term_key] = (cui, data)
        else:
            # Duplicate found - keep one with MSH source if possible
            existing_cui, existing_data = unique_terms[term_key]
            existing_sources = existing_data.get('sources', set())
            new_sources = data.get('sources', set())

            if 'MSH' in new_sources and 'MSH' not in existing_sources:
                unique_terms[term_key] = (cui, data)
            elif 'SNOMEDCT_US' in new_sources and not ('MSH' in existing_sources or 'SNOMEDCT_US' in existing_sources):
                unique_terms[term_key] = (cui, data)

            duplicates_removed += 1

    # Convert back to dict format
    deduplicated = {cui: data for cui, data in unique_terms.values()}

    print(f"   ✅ Removed {duplicates_removed:,} duplicates")
    print(f"   ✅ Final count: {len(deduplicated):,} unique terms")

    return deduplicated


def save_intermediate(concepts):
    """Save intermediate JSON for debugging/inspection."""
    print(f"\n💾 Saving intermediate data to {INTERMEDIATE_JSON}...")

    # Convert sets to lists for JSON serialization
    json_data = {}
    for cui, data in concepts.items():
        json_data[cui] = {
            'preferred_term': data.get('preferred_term'),
            'definition': data.get('definition', ''),
            'definition_source': data.get('definition_source', ''),
            'synonyms': data.get('synonyms', []),
            'abbreviations': data.get('abbreviations', []),
            'mesh_code': data.get('mesh_code', ''),
            'sources': list(data.get('sources', []))
        }

    with open(INTERMEDIATE_JSON, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)

    print(f"   ✅ Saved {len(concepts):,} concepts to {INTERMEDIATE_JSON}")


def main():
    print("="*70)
    print("UMLS NEUROSCIENCE TERM IMPORTER")
    print("="*70)
    print(f"\nStrategy: DEC-002 Option B (Multi-stage filtering)")
    print(f"Input: 1,015,068 neuroscience CUIs")
    print(f"Target: 150K-250K final terms")

    # Step 1: Load neuroscience CUI filter
    neuro_cuis = load_neuroscience_cuis()

    # Step 2: Load semantic type mappings (for keyword filtering)
    cui_semantic_types = load_cui_semantic_types()

    # Step 3: Parse MRCONSO (terms, synonyms, abbreviations)
    concepts = parse_mrconso(neuro_cuis, cui_semantic_types)

    if not concepts:
        print("\n❌ ERROR: No concepts extracted from MRCONSO")
        sys.exit(1)

    # Step 4: Parse MRDEF (definitions)
    concepts = parse_mrdef(concepts)

    # Step 5: Deduplicate by term name
    concepts = deduplicate_by_term(concepts)

    # Step 6: Save intermediate results
    save_intermediate(concepts)

    # Summary
    print("\n" + "="*70)
    print("PHASE 1 COMPLETE: TERM EXTRACTION")
    print("="*70)
    print(f"\n✅ Extracted {len(concepts):,} unique neuroscience terms")
    print(f"✅ Intermediate data: {INTERMEDIATE_JSON}")

    # Coverage statistics
    with_defs = sum(1 for c in concepts.values() if c.get('definition'))
    with_mesh = sum(1 for c in concepts.values() if c.get('mesh_code'))
    with_syns = sum(1 for c in concepts.values() if c.get('synonyms'))

    print(f"\n📊 Coverage Statistics:")
    print(f"   Definitions: {with_defs:,} ({with_defs/len(concepts)*100:.1f}%)")
    print(f"   MeSH codes: {with_mesh:,} ({with_mesh/len(concepts)*100:.1f}%)")
    print(f"   Synonyms: {with_syns:,} ({with_syns/len(concepts)*100:.1f}%)")

    print(f"\n🎯 Target Assessment:")
    if 150000 <= len(concepts) <= 250000:
        print(f"   ✅ Within target range (150K-250K)")
    elif len(concepts) < 150000:
        print(f"   ⚠️  Below target (< 150K)")
        print(f"   Consider: Relaxing keyword filters or adding Priority 3 types")
    else:
        print(f"   ⚠️  Above target (> 250K)")
        print(f"   Consider: Stricter keyword filters or Priority 1 only")

    print(f"\n🚀 Next Steps:")
    print(f"   1. Review intermediate data: {INTERMEDIATE_JSON}")
    print(f"   2. Parse MRREL.RRF for related concepts (DEC-001 profiling)")
    print(f"   3. Map to NeuroDB-2 26-column schema")
    print(f"   4. Run validation and quality profiling")


if __name__ == "__main__":
    main()
