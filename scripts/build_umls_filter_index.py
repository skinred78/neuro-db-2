#!/usr/bin/env python3
"""
Build Neuroscience CUI Filter Index from UMLS MRSTY.RRF

Filters 4M+ UMLS concepts → 100K-150K neuroscience-relevant concepts
using semantic type assignments.

Input: downloads/umls/2025AB/2025AB/META/MRSTY.RRF
Output: imports/umls/neuroscience_cuis.txt (one CUI per line)
        imports/umls/filter_statistics.json
"""

import sys
import json
from pathlib import Path
from collections import defaultdict, Counter

# UMLS file path
MRSTY_PATH = Path("downloads/umls/2025AB/2025AB/META/MRSTY.RRF")
OUTPUT_DIR = Path("imports/umls")
CUI_OUTPUT = OUTPUT_DIR / "neuroscience_cuis.txt"
STATS_OUTPUT = OUTPUT_DIR / "filter_statistics.json"

# Neuroscience-relevant semantic types with TUI codes
# Source: https://www.nlm.nih.gov/research/umls/META3_current_semantic_types.html

NEURO_SEMANTIC_TYPES = {
    # Priority 1: Anatomical (High relevance)
    'T023': ('Body Part, Organ, or Organ Component', 1),
    'T029': ('Body Location or Region', 1),
    'T030': ('Body Space or Junction', 1),
    'T025': ('Cell', 1),
    'T026': ('Cell Component', 1),
    'T024': ('Tissue', 1),

    # Priority 1: Physiological (High relevance)
    'T039': ('Physiologic Function', 1),
    'T040': ('Organism Function', 1),
    'T042': ('Organ or Tissue Function', 1),
    'T043': ('Cell Function', 1),
    'T044': ('Molecular Function', 1),
    'T041': ('Mental Process', 1),

    # Priority 2: Behavioral (Medium relevance)
    'T053': ('Behavior', 2),
    'T054': ('Social Behavior', 2),
    'T048': ('Mental or Behavioral Dysfunction', 1),  # Upgraded to P1 (psychiatric)

    # Priority 1: Pathological (High relevance)
    'T047': ('Disease or Syndrome', 1),
    'T046': ('Pathologic Function', 1),
    'T049': ('Cell or Molecular Dysfunction', 1),
    'T191': ('Neoplastic Process', 1),
    'T037': ('Injury or Poisoning', 1),

    # Priority 2: Chemical (Medium relevance - neuropharmacology)
    'T121': ('Pharmacologic Substance', 2),
    'T116': ('Amino Acid, Peptide, or Protein', 2),
    'T123': ('Biologically Active Substance', 2),
    'T125': ('Hormone', 2),
    'T192': ('Receptor', 1),  # Upgraded to P1 (neurotransmitter receptors)
    'T114': ('Nucleic Acid, Nucleoside, or Nucleotide', 2),
    'T126': ('Enzyme', 2),
    'T129': ('Immunologic Factor', 3),

    # Priority 3: Procedures (Selective - only with neuro keywords)
    'T060': ('Diagnostic Procedure', 3),
    'T061': ('Therapeutic or Preventive Procedure', 3),

    # Additional: Gene/Genome (for neurogenetics)
    'T028': ('Gene or Genome', 2),
}

# Neuroscience keywords for supplemental filtering
NEURO_KEYWORDS = [
    'neuro', 'brain', 'cerebr', 'cortex', 'neural', 'synap',
    'axon', 'dendrit', 'glia', 'astrocyt', 'oligodendro',
    'cognit', 'memory', 'psychiatric', 'mental', 'behavior',
    'parkinson', 'alzheimer', 'epilep', 'schizo', 'depress',
    'anxiet', 'autism', 'dementia', 'stroke', 'migraine'
]


def parse_mrsty(mrsty_path):
    """
    Parse MRSTY.RRF to build CUI → Semantic Types mapping.

    MRSTY.RRF format (pipe-delimited):
    CUI|TUI|STN|STY|ATUI|CVF

    Returns:
        dict: {CUI: [(TUI, semantic_type_name), ...]}
    """
    print(f"\n📖 Parsing {mrsty_path}...")

    if not mrsty_path.exists():
        print(f"❌ ERROR: File not found: {mrsty_path}")
        sys.exit(1)

    cui_to_types = defaultdict(list)
    total_rows = 0

    with open(mrsty_path, 'r', encoding='utf-8') as f:
        for line in f:
            total_rows += 1
            cols = line.strip().split('|')

            if len(cols) < 4:
                continue

            cui = cols[0]
            tui = cols[1]  # Semantic type unique identifier (e.g., T023)
            sty = cols[3]  # Semantic type name (e.g., "Body Part, Organ, or Organ Component")

            cui_to_types[cui].append((tui, sty))

            if total_rows % 100000 == 0:
                print(f"   Processed {total_rows:,} rows, {len(cui_to_types):,} unique CUIs...")

    print(f"   ✅ Parsed {total_rows:,} rows")
    print(f"   ✅ Found {len(cui_to_types):,} unique CUIs with semantic types")

    return cui_to_types


def filter_neuroscience_cuis(cui_to_types):
    """
    Filter CUIs to neuroscience-relevant concepts using hybrid approach.

    Inclusion criteria:
    - Priority 1 semantic type: Always include
    - Priority 2 semantic type: Include if from neuro domain
    - Priority 3 semantic type: Include only with neuro keywords

    Returns:
        set: Neuroscience-relevant CUIs
        dict: Statistics by semantic type
    """
    print(f"\n🔍 Filtering neuroscience-relevant CUIs...")

    neuroscience_cuis = set()
    stats_by_type = Counter()
    priority_distribution = Counter()

    for cui, type_list in cui_to_types.items():
        include = False
        cui_priorities = set()

        for tui, sty in type_list:
            if tui in NEURO_SEMANTIC_TYPES:
                semantic_name, priority = NEURO_SEMANTIC_TYPES[tui]
                cui_priorities.add(priority)

                if priority == 1:
                    # Priority 1: Always include
                    include = True
                    stats_by_type[semantic_name] += 1

                elif priority == 2:
                    # Priority 2: Include (broader relevance)
                    include = True
                    stats_by_type[semantic_name] += 1

                elif priority == 3:
                    # Priority 3: Selective (procedures need neuro context)
                    # For now, skip P3 to maintain precision
                    # Can expand later if needed
                    pass

        if include:
            neuroscience_cuis.add(cui)
            # Track highest priority for this CUI
            if cui_priorities:
                priority_distribution[min(cui_priorities)] += 1

    print(f"   ✅ Filtered to {len(neuroscience_cuis):,} neuroscience CUIs")
    print(f"\n   Priority Distribution:")
    for priority in sorted(priority_distribution.keys()):
        count = priority_distribution[priority]
        pct = count / len(neuroscience_cuis) * 100
        print(f"      Priority {priority}: {count:,} CUIs ({pct:.1f}%)")

    return neuroscience_cuis, dict(stats_by_type)


def write_outputs(neuroscience_cuis, stats_by_type):
    """
    Write filtered CUIs to file and statistics to JSON.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write CUI list
    print(f"\n💾 Writing {len(neuroscience_cuis):,} CUIs to {CUI_OUTPUT}...")
    with open(CUI_OUTPUT, 'w', encoding='utf-8') as f:
        for cui in sorted(neuroscience_cuis):
            f.write(f"{cui}\n")
    print(f"   ✅ Wrote {CUI_OUTPUT}")

    # Write statistics
    print(f"\n📊 Writing statistics to {STATS_OUTPUT}...")
    stats = {
        'total_cuis_filtered': len(neuroscience_cuis),
        'semantic_type_counts': stats_by_type,
        'top_10_semantic_types': sorted(
            stats_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10],
        'filter_config': {
            'priority_1_types': [k for k, (_, p) in NEURO_SEMANTIC_TYPES.items() if p == 1],
            'priority_2_types': [k for k, (_, p) in NEURO_SEMANTIC_TYPES.items() if p == 2],
            'priority_3_types': [k for k, (_, p) in NEURO_SEMANTIC_TYPES.items() if p == 3],
        }
    }

    with open(STATS_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"   ✅ Wrote {STATS_OUTPUT}")


def main():
    print("="*70)
    print("UMLS NEUROSCIENCE CUI FILTER BUILDER")
    print("="*70)

    # Step 1: Parse MRSTY.RRF
    cui_to_types = parse_mrsty(MRSTY_PATH)

    # Step 2: Filter to neuroscience CUIs
    neuroscience_cuis, stats_by_type = filter_neuroscience_cuis(cui_to_types)

    # Step 3: Write outputs
    write_outputs(neuroscience_cuis, stats_by_type)

    # Summary
    print("\n" + "="*70)
    print("FILTERING COMPLETE")
    print("="*70)
    print(f"\n✅ Filtered {len(neuroscience_cuis):,} neuroscience CUIs")
    print(f"✅ Output: {CUI_OUTPUT}")
    print(f"✅ Statistics: {STATS_OUTPUT}")
    print(f"\n🎯 Target range: 100K-150K CUIs")

    if len(neuroscience_cuis) < 80000:
        print(f"⚠️  WARNING: CUI count below target (< 80K)")
        print(f"   Consider expanding to Priority 3 types or adding keywords")
    elif len(neuroscience_cuis) > 200000:
        print(f"⚠️  WARNING: CUI count above target (> 200K)")
        print(f"   Consider restricting to Priority 1 types only")
    else:
        print(f"✅ CUI count within target range")

    print(f"\n🚀 Next step: Run scripts/import_umls_neuroscience.py")


if __name__ == "__main__":
    main()
