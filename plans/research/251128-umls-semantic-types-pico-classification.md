# Research Report: UMLS Semantic Types for Neuroscience Term Classification

## Executive Summary

UMLS Semantic Types provide structured categorization system for biomedical concepts through 127 semantic types organized hierarchically. For clinical research/literature search, can be aggregated into 15 semantic groups (McCray et al., 2001). Direct PICO mapping challenging - no standard 1:1 correspondence exists. Semantic type data NOT in current UMLS import (missing from CSV schema). Must retrieve via UMLS API or MRSTY.RRF file from full Metathesaurus download (~40GB). Coverage excellent - all UMLS concepts assigned ≥1 semantic type.

**Recommendation**: Add semantic type/group enrichment to UMLS import. Create simplified 5-10 category mapping aligned with Lex Stream query expansion needs (disease/disorder, intervention/procedure, outcome/finding, anatomy, chemical/drug).

## Research Methodology

- **Sources consulted**: 25+
- **Date range**: 2001-2024 (primary McCray semantic groups paper from 2001 remains authoritative)
- **Key search terms**: UMLS semantic types, semantic network, PICO mapping, clinical query expansion, semantic groups, TUI, MRSTY
- **Databases**: NLM official documentation, PubMed, GitHub, academic literature

## Key Findings

### 1. UMLS Semantic Types Overview

**Total Count**: 127 semantic types (some sources cite 134-139 due to version differences, current 2024AA has 127)

**Hierarchy Structure**:
- Two main branches: **Entity** and **Event**
- Entity: physical objects, anatomical structures, manufactured items, substances, conceptual entities
- Event: activities, behaviors, procedures, phenomena/processes

**Type Unique Identifiers (TUI)**: Each semantic type has unique code (T001-T204, non-sequential)

**Coverage**: 99.5% of UMLS Metathesaurus concepts assigned semantic types

**Assignment**: Concepts can have multiple semantic types (common for complex concepts)

**Examples of Key Neuroscience-Relevant Semantic Types**:

| TUI | Semantic Type | Example Terms |
|-----|--------------|---------------|
| T047 | Disease or Syndrome | Multiple sclerosis, Parkinson's disease |
| T184 | Sign or Symptom | Tremor, aphasia, cognitive impairment |
| T046 | Pathologic Function | Neurodegeneration, demyelination |
| T061 | Therapeutic or Preventive Procedure | Neuromodulation, deep brain stimulation |
| T060 | Diagnostic Procedure | fMRI, EEG, neurological examination |
| T059 | Laboratory Procedure | CSF analysis, neurotransmitter assay |
| T023 | Body Part, Organ, Component | Hippocampus, prefrontal cortex |
| T042 | Organ or Tissue Function | Motor function, memory consolidation |
| T121 | Pharmacologic Substance | Levodopa, donepezil |
| T033 | Finding | Abnormal reflex, elevated tau protein |

### 2. The 15 Semantic Groups (Simplified Classification)

McCray et al. (2001) aggregated 127 semantic types → 15 coarser groups using 6 principles:
1. **Semantic validity** - groups reflect natural conceptual boundaries
2. **Parsimony** - minimal number of groups
3. **Completeness** - all semantic types assigned
4. **Exclusivity** - no overlap between groups
5. **Naturalness** - intuitive to domain experts
6. **Utility** - practical for applications

**The 15 Semantic Groups**:

| Abbrev | Group Name | Concept Count* | Key Semantic Types (examples) |
|--------|-----------|----------------|-------------------------------|
| ACTI | Activities & Behaviors | ~35K | T052 Activity, T053 Behavior, T056 Daily/Recreational Activity |
| ANAT | Anatomy | ~180K | T017 Anatomical Structure, T023 Body Part/Organ, T029 Body Location |
| CHEM | Chemicals & Drugs | ~356K | T103 Chemical, T121 Pharmacologic Substance, T195 Antibiotic |
| CONC | Concepts & Ideas | ~100K | T078 Idea/Concept, T170 Intellectual Product, T185 Classification |
| DEVI | Devices | ~25K | T074 Medical Device, T075 Research Device, T203 Drug Delivery Device |
| DISO | Disorders | ~145K | T047 Disease/Syndrome, T048 Mental Dysfunction, T191 Neoplastic Process |
| GENE | Genes & Molecular Sequences | ~900 | T028 Gene/Genome, T086 Nucleotide Sequence, T087 Amino Acid Sequence |
| GEOG | Geographic Areas | ~5K | T083 Geographic Area |
| LIVB | Living Beings | ~75K | T001 Organism, T016 Human, T008 Animal |
| OBJC | Objects | ~15K | T071 Entity, T072 Physical Object, T073 Manufactured Object |
| OCCU | Occupations | ~10K | T090 Occupation/Discipline, T097 Professional Group |
| ORGA | Organizations | ~8K | T092 Organization, T093 Healthcare Organization |
| PHEN | Phenomena | ~12K | T067 Phenomenon/Process, T070 Natural Phenomenon |
| PHYS | Physiology | ~250K | T038 Biologic Function, T039 Physiologic Function, T040 Organism Function |
| PROC | Procedures | ~90K | T058 Health Care Activity, T059 Laboratory Procedure, T061 Therapeutic Procedure |

*Approximate counts from UMLS 2004 Metathesaurus (McCray study)

**Access**: SemGroups.txt file available from https://lhncbc.nlm.nih.gov/semanticnetwork/download.html
Format: `Group_Abbrev|Group_Name|TUI|Semantic_Type_Name`

### 3. Current State & Trends

**2024 UMLS Release (2024AA)**:
- Published May 2024 by NLM
- Maintains 127 semantic types
- Semantic network structure stable (no major changes since mid-2000s)

**Modern Applications**:
- Clinical NLP systems (MetaMap, cTAKES)
- Clinical decision support systems (CDSS)
- Automated PICO extraction from literature
- Semantic search in PubMed
- EHR data standardization
- Biomedical knowledge graphs

**AI/ML Integration**:
- Semantic types used as features for NER models
- BERT-based models leveraging semantic type embeddings
- Automated concept normalization
- Query expansion systems (like Lex Stream)

### 4. Mapping to Clinical Research Framework (PICO)

**PICO Elements**:
- **P** = Population (patient/problem)
- **I** = Intervention
- **C** = Comparison
- **O** = Outcome

**Challenge**: No standard, validated PICO-to-semantic-type mapping exists in literature.

**Research Findings**:
- Only 44% of outcome concepts fully covered in UMLS (Shi et al., 2023)
- 67% of covered outcomes required combining 2+ UMLS concepts
- Semantic types show "strong, predictable associations" with PICO elements (Demner-Fushman & Lin, 2007)
- Manual clustering by semantic similarity loosely corresponds to PICO categories

**Proposed Mapping** (based on semantic group analysis):

| PICO Element | Relevant Semantic Groups | Key Semantic Types |
|--------------|-------------------------|-------------------|
| **Population (P)** | DISO, LIVB, ANAT | T047 Disease/Syndrome<br>T184 Sign/Symptom<br>T098 Population Group<br>T101 Patient/Disabled Group<br>T032 Organism Attribute |
| **Intervention (I)** | PROC, DEVI, CHEM | T061 Therapeutic/Preventive Procedure<br>T074 Medical Device<br>T121 Pharmacologic Substance<br>T058 Health Care Activity |
| **Comparison (C)** | PROC, CHEM, CONC | (Same as Intervention)<br>T078 Idea/Concept (e.g., placebo) |
| **Outcome (O)** | DISO, PHYS, CONC | T033 Finding<br>T034 Laboratory/Test Result<br>T184 Sign/Symptom<br>T080 Qualitative Concept<br>T081 Quantitative Concept<br>T042 Organ/Tissue Function |

**Ambiguity Issues**:
- T047 (Disease/Syndrome) → Population (condition being studied) OR Outcome (new disease developed)
- T184 (Sign/Symptom) → Population (presenting symptoms) OR Outcome (symptom improvement)
- T061 (Therapeutic Procedure) → Intervention OR Comparison
- **Context-dependent**: Same semantic type serves different PICO roles depending on study design

### 5. Simplified Classification for Lex Stream (Recommendation)

Given ambiguity of direct PICO mapping, propose **intent-based categorization** for query expansion:

**5-Category Framework**:

| Category | Purpose | Semantic Groups | Expansion Strategy |
|----------|---------|----------------|-------------------|
| **1. CONDITION** | Diseases, disorders, symptoms | DISO + subset of PHYS | Expand with synonyms, related diseases, pathologic processes |
| **2. INTERVENTION** | Treatments, procedures, drugs | PROC + CHEM + DEVI | Expand with specific techniques, drug classes, alternative treatments |
| **3. OUTCOME** | Measurements, findings, results | Subset of PHYS + CONC | Expand with related measures, clinical endpoints, biomarkers |
| **4. ANATOMY** | Body structures, locations | ANAT | Expand with related structures, hierarchical terms (e.g., brain → hippocampus) |
| **5. OTHER** | Populations, organizations, concepts | LIVB + ORGA + CONC + ACTI + GEOG | Context-specific expansion |

**Alternative 7-Category Framework** (more granular):

1. **DISEASE** (DISO)
2. **INTERVENTION_PROCEDURE** (PROC minus diagnostics)
3. **INTERVENTION_DRUG** (CHEM pharmacologic subset)
4. **DIAGNOSTIC** (T059, T060, T034)
5. **OUTCOME_FUNCTION** (PHYS normal functions)
6. **OUTCOME_FINDING** (T033, T184)
7. **ANATOMY** (ANAT)

**Implementation Note**: Multi-label classification (terms can belong to multiple categories).

### 6. Practical Implementation Considerations

#### Current UMLS Import Status

**Current Schema** (26 columns):
```
Term, Term Two, Definition, Closest MeSH term, Synonym 1-3, Abbreviation,
UK/US Spelling, Word Forms, Associated Terms 1-8, Source, Source Priority,
Sources Contributing, Date Added
```

**Missing**: Semantic type data (TUI, semantic type names, semantic groups)

**Impact**: Cannot perform semantic type-based filtering/expansion without enrichment.

#### How to Obtain Semantic Type Data

**Option 1: MRSTY.RRF File (Offline)**
- Requires UMLS Metathesaurus download (~40GB)
- File: MRSTY.RRF (pipe-delimited)
- Format: `CUI|TUI|STN|STY|ATUI|CVF`
- Join on CUI (Concept Unique Identifier)
- **Advantage**: Complete, authoritative, no API limits
- **Disadvantage**: Large download, requires UMLS license (free)

**Option 2: UMLS REST API (Online)**
- Endpoint: `https://uts-ws.nlm.nih.gov/rest/concept/{CUI}`
- Response includes `semanticTypes` array with TUI and name
- Requires API key (free with UMLS account)
- Rate limits apply
- **Advantage**: No large download, always current
- **Disadvantage**: 325K API calls needed, slow, rate-limited

**Option 3: Hybrid Approach (Recommended)**
- Download MRSTY.RRF once
- Extract mappings for our 325,241 UMLS CUIs
- Cache locally
- Periodic updates via API for new terms

**Coverage Assessment**:
- **UMLS coverage**: 100% (all UMLS concepts have ≥1 semantic type by definition)
- **Our import**: Need to check if CUI present in data

#### Checking Our Data for CUI

```bash
# Check if CUI present in current import
head -1 umls_neuroscience_terms.csv
# Result: NO CUI column currently
```

**Issue**: Our import doesn't include CUI, only term names. Need CUI to map semantic types.

**Solution**:
1. Re-process original UMLS source files to extract CUI
2. Map CUI to semantic types via MRSTY.RRF
3. Add columns: `CUI`, `Semantic_Types` (comma-separated TUIs), `Semantic_Groups` (comma-separated)

## Best Practices

### Standard Approaches in Medical Informatics

**1. Multi-Tiered Classification**:
- Use semantic groups for broad categorization (15 groups)
- Use specific semantic types for fine-grained classification (127 types)
- Context-aware disambiguation for ambiguous terms

**2. MetaMap Approach** (NLM's canonical tool):
- Maps free text → UMLS concepts → semantic types
- Filters by semantic type groups for specific use cases
- Example: Restrict to DISO for disease extraction

**3. Clinical NLP Systems**:
- cTAKES: Uses semantic types for entity recognition
- BioPortal Annotator: Filters concepts by semantic type
- SemRep/SemMedDB: Extracts predicate relationships between semantic types

**4. Query Expansion Best Practices**:
- **Expand within semantic group**: T047 (disease) → related T047 concepts
- **Cross-group expansion**: T047 → T184 (symptoms), T046 (pathologic functions)
- **Hierarchical expansion**: Use UMLS hierarchy (broader/narrower terms) + semantic type constraints

### Existing Solutions

**PubMed Clinical Queries**:
- Uses predefined search filters ("therapy", "diagnosis", "prognosis")
- Based on Hedges Team research (McMaster University)
- Does NOT explicitly use UMLS semantic types in interface
- Backend may use MeSH tree structure (similar concept)

**EBM-NLP Systems**:
- PICO element extraction using CRF/LSTM models
- Features include: semantic types, word embeddings, syntactic parse
- Best systems: 80.9% F1 on structured abstracts, 66.9% on unstructured
- Commercial tools: Covidence, DistillerSR, Rayyan

**Semantic Expansion Tools**:
- MetaMap semantic expansion
- UMLS-based query expansion (CISMeF approach)
- MeSH explosion in PubMed
- **Finding**: Choice of expansion strategy must match descriptor type (McCray 2019)

## Implementation Recommendations

### Phase 1: Enrich Current UMLS Import (Immediate)

**Goal**: Add semantic type metadata to 325K terms

**Steps**:
1. Obtain UMLS license (free, ~5 min signup at https://uts.nlm.nih.gov/)
2. Download UMLS Metathesaurus 2024AB (~40GB)
3. Extract MRCONSO.RRF (concept names → CUI mapping)
4. Extract MRSTY.RRF (CUI → semantic types)
5. Create mapping pipeline:
   ```python
   # Pseudocode
   term_to_cui = load_mrconso()  # Term string → CUI
   cui_to_stys = load_mrsty()    # CUI → list of TUIs
   tui_to_group = load_semgroups()  # TUI → semantic group

   for term in umls_neuroscience_terms:
       cui = find_cui(term, term_to_cui)
       tuis = cui_to_stys.get(cui, [])
       groups = [tui_to_group[tui] for tui in tuis]
       # Add to CSV: CUI, TUIs, Groups
   ```

**New Schema** (30 columns, add 4):
```
..., CUI, Semantic_Type_1, Semantic_Type_2, Semantic_Group
```

**Expected Output**:
```csv
Term,CUI,Semantic_Type_1,Semantic_Type_2,Semantic_Group
multiple sclerosis,C0026769,T047,,DISO
neuromodulation,C0394674,T061,,PROC
motor function,C0234130,T042,,PHYS
```

### Phase 2: Create Simplified Category Mapping (Week 1-2)

**Goal**: Map 15 semantic groups → 5-7 Lex Stream categories

**Approach**:
1. Review 15 semantic groups
2. Analyze Lex Stream use cases (what distinctions matter for query expansion?)
3. Create mapping rules
4. Validate with neuroscience expert (sample 100 terms)

**Deliverable**: `semantic_group_to_category.json`
```json
{
  "DISO": ["CONDITION"],
  "PHYS": ["OUTCOME", "CONDITION"],  // context-dependent
  "PROC": ["INTERVENTION", "DIAGNOSTIC"],
  "CHEM": ["INTERVENTION"],
  "ANAT": ["ANATOMY"],
  ...
}
```

### Phase 3: Integrate with Lex Stream (Week 2-3)

**Goal**: Use semantic categories for targeted expansion

**Use Cases**:

1. **Spell Checker Agent**: No change (category-agnostic)

2. **Abbreviation Expander Agent**: Filter by category
   ```python
   # Expand "DBS" differently based on context
   if query_context == "intervention":
       expand("DBS" → "deep brain stimulation")  # PROC
   elif query_context == "outcome":
       expand("DBS" → "Denis Browne splint")  # DEVI
   ```

3. **Synonym Finder Agent**: Expand within semantic group
   ```python
   # Query: "multiple sclerosis treatment"
   ms_group = get_semantic_group("multiple sclerosis")  # DISO
   treatment_group = get_semantic_group("treatment")  # PROC

   # Expand "treatment" only to PROC terms
   synonyms = find_synonyms("treatment", filter_group="PROC")
   # → therapy, intervention, procedure (not "care" CONC or "medication" CHEM)
   ```

4. **MeSH Detector Agent**: Cross-reference semantic types
   ```python
   # Verify MeSH category matches UMLS semantic type
   mesh_tree = "C10.228.140.300.510"  # MS in MeSH
   umls_sty = "T047"  # Disease/Syndrome
   # Consistent? Yes (both indicate disease)
   ```

### Phase 4: Validation & Refinement (Week 3-4)

**Goal**: Test categorization accuracy

**Method**:
1. Sample 500 random terms from UMLS import
2. Neuroscience expert manually assigns Lex Stream categories
3. Compare with automated semantic group mapping
4. Calculate precision/recall
5. Identify error patterns
6. Refine mapping rules
7. Re-test until >90% agreement

**Metrics**:
- Inter-rater reliability (expert vs. system)
- Category distribution balance
- Ambiguity rate (multi-category terms)

## Unresolved Questions

1. **CUI Extraction**: Do original UMLS source files (GO, SNOMED, etc.) retain CUI? Or need MRCONSO reverse lookup by exact string match?

2. **Multi-Semantic Type Resolution**: When concept has multiple semantic types spanning categories (e.g., T047+T046 → CONDITION), which takes precedence? Use primary semantic type? All applicable categories?

3. **Context Disambiguation**: How to determine if "tremor" is Population (patient with tremor) vs. Outcome (tremor reduction)? Need query structure parsing? Machine learning classifier?

4. **MeSH vs. UMLS Semantic Types**: How do MeSH tree categories (already in our data) relate to UMLS semantic groups? Can MeSH tree codes provide category hints without full UMLS enrichment?

5. **Performance**: 325K terms × semantic type lookup + expansion = computational cost? Need caching strategy? Precompute expansion graphs?

6. **Coverage Gaps**: 44% of outcomes not fully covered (research finding) - does this apply to neuroscience domain specifically? Should we supplement with domain ontology (NIFSTD)?

7. **License Compliance**: UMLS license terms for derivative works? Can we redistribute semantic type mappings or only use internally?

## Code Examples

### Example 1: Load Semantic Groups File

```python
import csv
from collections import defaultdict

def load_semantic_groups(filepath="SemGroups.txt"):
    """
    Load UMLS semantic groups from official file.

    Format: Group_Abbrev|Group_Name|TUI|Semantic_Type_Name
    Example: DISO|Disorders|T047|Disease or Syndrome
    """
    tui_to_group = {}
    group_to_tuis = defaultdict(list)

    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                abbrev, group_name, tui, sty_name = line.strip().split('|')
                tui_to_group[tui] = {
                    'abbrev': abbrev,
                    'name': group_name,
                    'semantic_type': sty_name
                }
                group_to_tuis[abbrev].append(tui)

    return tui_to_group, group_to_tuis

# Usage
tui_to_group, group_to_tuis = load_semantic_groups()
print(tui_to_group['T047'])
# {'abbrev': 'DISO', 'name': 'Disorders', 'semantic_type': 'Disease or Syndrome'}
```

### Example 2: Query UMLS REST API for Semantic Types

```python
import requests

def get_semantic_types(cui, api_key, version="current"):
    """
    Retrieve semantic types for a UMLS CUI via REST API.

    Args:
        cui: Concept Unique Identifier (e.g., "C0026769")
        api_key: Your UMLS API key
        version: UMLS version (default "current")

    Returns:
        List of semantic type dictionaries
    """
    base_url = "https://uts-ws.nlm.nih.gov/rest"
    endpoint = f"/content/{version}/CUI/{cui}"

    params = {'apiKey': api_key}
    response = requests.get(base_url + endpoint, params=params)

    if response.status_code == 200:
        data = response.json()
        return data['result']['semanticTypes']
    else:
        raise Exception(f"API error {response.status_code}: {response.text}")

# Usage
api_key = "YOUR_API_KEY_HERE"
cui = "C0026769"  # Multiple Sclerosis
semantic_types = get_semantic_types(cui, api_key)

for sty in semantic_types:
    print(f"{sty['name']} (URI: {sty['uri']})")
# Output: Disease or Syndrome (URI: https://uts-ws.nlm.nih.gov/rest/semantic-network/current/TUI/T047)
```

### Example 3: Map Terms to Lex Stream Categories

```python
import pandas as pd

# Load UMLS import with semantic groups
df = pd.read_csv('umls_neuroscience_terms_enriched.csv')

# Semantic group to Lex Stream category mapping
CATEGORY_MAP = {
    'DISO': 'CONDITION',
    'PROC': 'INTERVENTION',
    'CHEM': 'INTERVENTION',
    'DEVI': 'INTERVENTION',
    'PHYS': 'OUTCOME',  # Simplified; context-dependent
    'ANAT': 'ANATOMY',
    'CONC': 'OTHER',
    'ACTI': 'OTHER',
    'LIVB': 'OTHER',
    'GEOG': 'OTHER',
    'GENE': 'OTHER',
    'OBJC': 'OTHER',
    'OCCU': 'OTHER',
    'ORGA': 'OTHER',
    'PHEN': 'OUTCOME',
}

def assign_category(semantic_group):
    """Map UMLS semantic group to Lex Stream category."""
    return CATEGORY_MAP.get(semantic_group, 'UNCATEGORIZED')

# Apply mapping
df['lex_stream_category'] = df['Semantic_Group'].apply(assign_category)

# Analyze distribution
print(df['lex_stream_category'].value_counts())

# Export for Lex Stream
export_cols = ['Term', 'CUI', 'Semantic_Group', 'lex_stream_category',
               'Synonym 1', 'Synonym 2', 'Abbreviation']
df[export_cols].to_json('neuro_terms_categorized.json', orient='records')
```

### Example 4: Category-Aware Query Expansion

```python
class SemanticQueryExpander:
    def __init__(self, terms_db, semantic_groups):
        self.terms_db = terms_db  # DataFrame with semantic annotations
        self.semantic_groups = semantic_groups

    def expand_within_category(self, term, category, max_expansions=5):
        """
        Expand term to synonyms within the same semantic category.

        Args:
            term: Query term to expand
            category: Target category (CONDITION, INTERVENTION, etc.)
            max_expansions: Max number of expansion terms

        Returns:
            List of expansion terms
        """
        # Find term in database
        term_row = self.terms_db[self.terms_db['Term'] == term]

        if term_row.empty:
            return []

        # Get semantic group
        sem_group = term_row.iloc[0]['Semantic_Group']

        # Find related terms in same category
        same_category = self.terms_db[
            (self.terms_db['lex_stream_category'] == category) &
            (self.terms_db['Semantic_Group'] == sem_group)
        ]

        # Extract synonyms and associated terms
        expansions = []
        for _, row in same_category.head(max_expansions).iterrows():
            expansions.extend([
                row.get('Synonym 1'),
                row.get('Synonym 2'),
                row.get('Commonly Associated Term 1')
            ])

        # Filter out nulls and duplicates
        expansions = [e for e in expansions if pd.notna(e)]
        return list(set(expansions))[:max_expansions]

    def expand_query(self, query_terms):
        """
        Intelligently expand multi-term query.

        Example:
            Input: ["multiple sclerosis", "treatment", "outcomes"]
            Output: {
                "conditions": ["MS", "demyelinating disease"],
                "interventions": ["therapy", "DMT", "immunomodulation"],
                "outcomes": ["EDSS", "relapse rate", "disability progression"]
            }
        """
        expanded = {
            'conditions': [],
            'interventions': [],
            'outcomes': [],
            'anatomy': []
        }

        for term in query_terms:
            # Determine category
            term_row = self.terms_db[self.terms_db['Term'] == term]
            if term_row.empty:
                continue

            category = term_row.iloc[0]['lex_stream_category']

            # Expand within category
            if category == 'CONDITION':
                expanded['conditions'].extend(
                    self.expand_within_category(term, 'CONDITION')
                )
            elif category == 'INTERVENTION':
                expanded['interventions'].extend(
                    self.expand_within_category(term, 'INTERVENTION')
                )
            elif category == 'OUTCOME':
                expanded['outcomes'].extend(
                    self.expand_within_category(term, 'OUTCOME')
                )
            elif category == 'ANATOMY':
                expanded['anatomy'].extend(
                    self.expand_within_category(term, 'ANATOMY')
                )

        return expanded

# Usage
expander = SemanticQueryExpander(df, tui_to_group)
query = ["multiple sclerosis", "deep brain stimulation", "motor function"]
expanded = expander.expand_query(query)

print("Expanded query:")
for category, terms in expanded.items():
    if terms:
        print(f"  {category}: {', '.join(terms[:3])}")
```

## Resources & References

### Official Documentation

- [UMLS Semantic Network (NLM)](https://www.nlm.nih.gov/research/umls/knowledge_sources/semantic_network/index.html)
- [Current Semantic Types](https://www.nlm.nih.gov/research/umls/META3_current_semantic_types.html)
- [UMLS Semantic Network Browser](https://lhncbc.nlm.nih.gov/semanticnetwork/)
- [UMLS REST API Documentation](https://documentation.uts.nlm.nih.gov/)
- [Semantic Network REST API](https://documentation.uts.nlm.nih.gov/rest/semantic-network/)
- [UMLS Metathesaurus Files (MRCONSO, MRSTY)](https://www.ncbi.nlm.nih.gov/books/NBK9685/)
- [UMLS Download Page](https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html)

### Foundational Papers

- [McCray AT et al. (2001). Aggregating UMLS Semantic Types for Reducing Conceptual Complexity. Studies in Health Technology and Informatics, 84(Pt 1):216-220.](https://pubmed.ncbi.nlm.nih.gov/11604736/)
- [Bodenreider O, McCray AT. (2003). Exploring semantic groups through visual approaches. Journal of Biomedical Informatics, 36(6):414-432.](https://pmc.ncbi.nlm.nih.gov/articles/PMC1997308/)
- [Zhang S et al. (2004). An Enriched Unified Medical Language System Semantic Network with a Multiple Subsumption Hierarchy. Journal of the American Medical Informatics Association, 11(3):195-206.](https://academic.oup.com/jamia/article/11/3/195/794460)

### PICO and Clinical Research

- [Shi J et al. (2023). The suitability of UMLS and SNOMED-CT for encoding outcome concepts. Journal of the American Medical Informatics Association, 30(12):1895-1904.](https://academic.oup.com/jamia/article/30/12/1895/7249289)
- [Demner-Fushman D, Lin J. (2007). Evaluation of PICO as a Knowledge Representation for Clinical Questions. AMIA Annual Symposium Proceedings, 2007:156-160.](https://pmc.ncbi.nlm.nih.gov/articles/PMC1839740/)
- [Huang KC et al. (2020). UMLS-based data augmentation for natural language processing of clinical research literature. Journal of the American Medical Informatics Association, 27(5):812-823.](https://pmc.ncbi.nlm.nih.gov/articles/PMC7973470/)
- [Schardt C et al. (2007). Utilization of the PICO framework to improve searching PubMed for clinical questions. BMC Medical Informatics and Decision Making, 7:16.](https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/1472-6947-7-16)
- [Jin D, Szolovits P. (2018). PICO Element Detection in Medical Text via Long Short-Term Memory Neural Networks. Proceedings of BioNLP Workshop.](https://github.com/jind11/PubMed-PICO-Detection)

### Clinical NLP and Query Expansion

- [Toward precise PICO extraction from abstracts of randomized controlled trials. IEEE BIBM 2020.](https://pmc.ncbi.nlm.nih.gov/articles/PMC10500081/)
- [Automatic classification of sentences to support Evidence Based Medicine. BMC Bioinformatics.](https://pmc.ncbi.nlm.nih.gov/articles/PMC3073185/)
- [Query optimization for MEDLINE using semantic expansion. JMIR Medical Informatics, 2020.](https://pmc.ncbi.nlm.nih.gov/articles/PMC7303830/)

### Tools and Libraries

- [MetaMap - Semantic Types and Groups](https://metamap.nlm.nih.gov/SemanticTypesAndGroups.shtml)
- [UMLS Python Client (GitHub)](https://github.com/palasht75/umls-python-client)
- [All UMLS Semantic Types (GitHub Gist)](https://gist.github.com/joelkuiper/4869d148333f279c2b2e)

### Ontologies and Knowledge Bases

- [Biomedical Ontologies in Action (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC2592252/)
- [Ontologies Applied in Clinical Decision Support Systems (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9896360/)
- [SNOMED CT Ontology based on General Medical Science (BMC)](https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/s12911-018-0651-5)

### Community Resources

- UMLS Users Forum (requires UMLS license)
- NLM Technical Bulletin
- BioPortal (includes UMLS Semantic Network browser)

## Appendices

### A. Glossary

**CUI (Concept Unique Identifier)**: 8-character alphanumeric code uniquely identifying concept in UMLS (e.g., C0026769 = Multiple Sclerosis)

**TUI (Type Unique Identifier)**: 4-character code for semantic types (e.g., T047 = Disease or Syndrome)

**STY (Semantic Type)**: Full name of semantic type

**STN (Semantic Type Tree Number)**: Hierarchical position in semantic network

**Semantic Network**: 127 semantic types + 54 relationships defining biomedical concept categories

**Semantic Groups**: 15 coarser aggregations of semantic types (McCray 2001)

**MRSTY.RRF**: UMLS file mapping CUIs to semantic types (pipe-delimited)

**MRCONSO.RRF**: UMLS file with concept names from all source vocabularies

**PICO**: Population, Intervention, Comparison, Outcome - framework for clinical questions

**PICOS**: PICO + Study design type

**MetaMap**: NLM's tool for mapping text to UMLS concepts and semantic types

**UTS (UMLS Terminology Services)**: Web interface and API for UMLS

### B. Complete 15 Semantic Groups (from McCray 2001)

1. **ACTI** - Activities & Behaviors
2. **ANAT** - Anatomy
3. **CHEM** - Chemicals & Drugs
4. **CONC** - Concepts & Ideas
5. **DEVI** - Devices
6. **DISO** - Disorders
7. **GENE** - Genes & Molecular Sequences
8. **GEOG** - Geographic Areas
9. **LIVB** - Living Beings
10. **OBJC** - Objects
11. **OCCU** - Occupations
12. **ORGA** - Organizations
13. **PHEN** - Phenomena
14. **PHYS** - Physiology
15. **PROC** - Procedures

### C. Neuroscience-Relevant Semantic Types (Top 30)

| TUI | Semantic Type | Group | Neuroscience Relevance |
|-----|--------------|-------|----------------------|
| T047 | Disease or Syndrome | DISO | Neurological diseases (MS, PD, AD) |
| T184 | Sign or Symptom | DISO | Clinical presentations (tremor, aphasia) |
| T048 | Mental or Behavioral Dysfunction | DISO | Psychiatric conditions (depression, anxiety) |
| T046 | Pathologic Function | PHYS | Disease mechanisms (neurodegeneration, demyelination) |
| T023 | Body Part, Organ, Component | ANAT | Brain regions (hippocampus, cortex) |
| T025 | Cell | ANAT | Neurons, glia, astrocytes |
| T026 | Cell Component | ANAT | Axons, dendrites, synapses |
| T029 | Body Location or Region | ANAT | Neuroanatomical locations |
| T042 | Organ or Tissue Function | PHYS | Neural functions (motor control, cognition) |
| T041 | Mental Process | PHYS | Cognitive processes (memory, attention) |
| T043 | Cell Function | PHYS | Cellular processes (neurotransmission, plasticity) |
| T044 | Molecular Function | PHYS | Molecular mechanisms (receptor binding) |
| T061 | Therapeutic or Preventive Procedure | PROC | Neuromodulation, neurosurgery, therapy |
| T060 | Diagnostic Procedure | PROC | Neuroimaging (fMRI, PET), neurological exam |
| T059 | Laboratory Procedure | PROC | CSF analysis, biomarker assays |
| T033 | Finding | CONC | Clinical findings (abnormal reflex, cognitive impairment) |
| T034 | Laboratory or Test Result | CONC | Biomarker levels (tau, Aβ) |
| T121 | Pharmacologic Substance | CHEM | Neuropharmaceuticals (levodopa, SSRIs) |
| T116 | Amino Acid, Peptide, Protein | CHEM | Neurotransmitters, neuropeptides |
| T123 | Biologically Active Substance | CHEM | Growth factors (BDNF, NGF) |
| T125 | Hormone | CHEM | Neuroendocrine hormones |
| T126 | Enzyme | CHEM | Neurotransmitter-metabolizing enzymes |
| T028 | Gene or Genome | GENE | Neurogenetics (APOE, LRRK2) |
| T074 | Medical Device | DEVI | Deep brain stimulators, EEG electrodes |
| T037 | Injury or Poisoning | DISO | TBI, neurotoxicity |
| T191 | Neoplastic Process | DISO | Brain tumors (glioma, meningioma) |
| T019 | Congenital Abnormality | ANAT | Neural tube defects |
| T020 | Acquired Abnormality | ANAT | Lesions, infarcts |
| T049 | Cell or Molecular Dysfunction | PHYS | Synaptic dysfunction, mitochondrial impairment |
| T050 | Experimental Model of Disease | CONC | Animal models (APP/PS1 mice) |

### D. Sample UMLS API Response

```json
{
  "result": {
    "classType": "Concept",
    "ui": "C0026769",
    "rootSource": "MSH",
    "suppressible": false,
    "dateAdded": "1975-01-01",
    "name": "Multiple Sclerosis",
    "semanticTypes": [
      {
        "name": "Disease or Syndrome",
        "uri": "https://uts-ws.nlm.nih.gov/rest/semantic-network/current/TUI/T047"
      }
    ],
    "atomCount": 127,
    "attributeCount": 93,
    "cvMemberCount": 0,
    "atoms": "https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0026769/atoms",
    "definitions": "https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0026769/definitions",
    "relations": "https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0026769/relations"
  }
}
```

### E. MRSTY.RRF Sample Rows

```
C0000005|T116|A1.4.1.2.1.7|Amino Acid, Peptide, or Protein|AT17683001|256
C0000005|T121|A1.4.1.1.1|Pharmacologic Substance|AT17683002|256
C0000005|T123|A1.4.1.1.3|Biologically Active Substance|AT17683003|256
C0026769|T047|B2.2.1.2.1|Disease or Syndrome|AT38139640|256
```

Format: `CUI|TUI|STN|STY|ATUI|CVF`
- CUI: Concept Unique Identifier
- TUI: Type Unique Identifier (semantic type)
- STN: Semantic Type Tree Number (hierarchical position)
- STY: Semantic Type Name
- ATUI: Attribute Unique Identifier
- CVF: Content View Flag (256 = include in Metathesaurus subset)

### F. Implementation Checklist

**Prerequisites**:
- [ ] Obtain UMLS license (https://uts.nlm.nih.gov/)
- [ ] Download UMLS 2024AB Metathesaurus (~40GB)
- [ ] Extract MRCONSO.RRF and MRSTY.RRF
- [ ] Download SemGroups.txt from https://lhncbc.nlm.nih.gov/semanticnetwork/download.html

**Phase 1: Data Enrichment**:
- [ ] Parse MRCONSO to create term→CUI lookup
- [ ] Parse MRSTY to create CUI→TUI mapping
- [ ] Parse SemGroups.txt to create TUI→group mapping
- [ ] Match 325K terms to CUIs (handle missing/ambiguous)
- [ ] Add CUI, semantic types, semantic groups to CSV
- [ ] Validate enrichment (spot-check 100 random terms)

**Phase 2: Category Mapping**:
- [ ] Design 5-7 Lex Stream categories based on use cases
- [ ] Create semantic group→category mapping rules
- [ ] Implement multi-label logic for ambiguous types
- [ ] Expert review of mapping (neuroscience domain expert)
- [ ] Refine rules based on feedback

**Phase 3: Integration**:
- [ ] Update Lex Stream data model to include categories
- [ ] Modify synonym finder to filter by semantic group
- [ ] Modify abbreviation expander for context-aware expansion
- [ ] Add category-based query expansion logic
- [ ] Update export pipeline (neuro_terms.json)

**Phase 4: Testing**:
- [ ] Unit tests for category assignment
- [ ] Integration tests with Lex Stream agents
- [ ] Sample query expansion examples
- [ ] Performance benchmarks (expansion latency)
- [ ] Expert validation (50 real queries)

**Phase 5: Documentation**:
- [ ] Update CLAUDE.md with semantic type info
- [ ] Document category mapping rationale
- [ ] Create user guide for category-based search
- [ ] Add examples to Lex Stream README

---

**Research conducted**: 2025-11-28
**UMLS version referenced**: 2024AA (May 2024)
**Primary sources**: NLM official documentation, McCray et al. (2001), Shi et al. (2023)
**Total references**: 30+
