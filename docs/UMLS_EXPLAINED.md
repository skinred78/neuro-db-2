# UMLS Metathesaurus Explained

**Purpose**: Reference guide for understanding UMLS structure, input files, and source vocabularies used in the NeuroDB-2 UMLS import.

**Created**: 2025-11-21
**Related**: `imports/umls/umls_import_quality_profile.md`

---

## What is UMLS?

**UMLS** = **Unified Medical Language System**

The UMLS Metathesaurus is a **multi-source biomedical terminology database** maintained by the National Library of Medicine (NLM). It integrates over 200 medical vocabularies into a unified framework, allowing terminology from different systems to be mapped and cross-referenced.

**Key Concept**: UMLS doesn't create new terminology—it **aggregates and links** existing terminologies from authoritative sources.

---

## The 4 Input Files (RRF Format)

The UMLS Metathesaurus is distributed as a collection of pipe-delimited text files (`.RRF` = Rich Release Format). For the NeuroDB-2 import, we use **4 core files**:

### 1. **MRCONSO.RRF** - Concept Names and Synonyms
**Size**: 2.1 GB (17.4 million rows)
**Purpose**: The main file containing all concept names, synonyms, and alternative terms

**What it contains**:
- **CUI** (Concept Unique Identifier): UMLS's internal ID for each concept
- **LAT** (Language): Language code (we filter for ENG = English)
- **TTY** (Term Type): What kind of term this is (PT=Preferred Term, SY=Synonym, AB=Abbreviation, etc.)
- **STR** (String): The actual term text (e.g., "hippocampus", "brain stem", "Alzheimer disease")
- **SAB** (Source Abbreviation): Which vocabulary this term came from (MSH, SNOMEDCT_US, NCI, etc.)
- **SUPPRESS** (Suppression flag): Whether this term should be suppressed (we exclude suppressed terms)

**Example row**:
```
C0019564|ENG|PT|Hippocampus|MSH|N
```
Translation: CUI C0019564, English, Preferred Term, "Hippocampus", from MeSH, not suppressed

**Our usage**:
- Filter for neuroscience CUIs (1.02M out of 3.5M total)
- Extract preferred terms, synonyms (max 3), and abbreviations
- Result: 325,241 unique terms

---

### 2. **MRDEF.RRF** - Definitions
**Size**: 131 MB
**Purpose**: Textual definitions for concepts

**What it contains**:
- **CUI**: Concept identifier
- **DEF**: Definition text
- **SAB**: Source that provided the definition

**Example row**:
```
C0019564|A curved gray matter structure in the temporal lobe...|MSH
```

**Our usage**:
- Match definitions to our 325K neuroscience CUIs
- Prioritize high-quality sources (MSH, NCI, GO)
- Result: 79,617 definitions (24.5% coverage)

**Why low coverage?**
Many anatomical vocabularies (FMA, UWDA) are structural taxonomies—they define relationships between structures but don't provide encyclopedic definitions.

---

### 3. **MRREL.RRF** - Relationships Between Concepts
**Size**: 5.7 GB (63.5 million rows)
**Purpose**: Describes how concepts relate to each other

**What it contains**:
- **CUI1**: First concept
- **REL**: Relationship type (RB=Broader, RN=Narrower, PAR=Parent, etc.)
- **RELA**: More specific relationship (part_of, treats, causes, innervates, etc.)
- **CUI2**: Second concept
- **SAB**: Source vocabulary

**Relationship types we extract** (domain-specific):
- **Anatomical**: `part_of`, `has_part`, `innervates`, `finding_site_of`
- **Pharmacological**: `treats`, `has_mechanism_of_action`, `has_physiologic_effect`
- **Pathological**: `causes`, `manifestation_of`, `has_pathological_process`

**Relationship types we exclude** (generic taxonomy):
- `PAR` (Parent), `CHD` (Child), `SIB` (Sibling), `RB` (Broader), `RN` (Narrower)

**Example row**:
```
C0019564|part_of|C0025065|FMA
```
Translation: Hippocampus (C0019564) is part_of Brain (C0025065), from FMA vocabulary

**Our usage**:
- Extract 1.8M domain-specific relationships
- Map to "Commonly Associated Terms" field
- Result: 294,008 terms (90.4%) have associations

---

### 4. **MRSTY.RRF** - Semantic Types
**Size**: 201 MB
**Purpose**: Categorizes each CUI by semantic type (what kind of thing it is)

**What it contains**:
- **CUI**: Concept identifier
- **TUI**: Type Unique Identifier
- **STY**: Semantic Type Name

**UMLS Semantic Network** has 127 semantic types organized in hierarchy:
- **Anatomical**: Body Part, Cell, Tissue, Cell Component
- **Physiological**: Organ Function, Mental Process, Organism Function
- **Pathological**: Disease/Syndrome, Mental Dysfunction, Pathologic Function
- **Chemical**: Pharmacologic Substance, Amino Acid, Neuroreactive Substance

**Example row**:
```
C0019564|T023|Body Part, Organ, or Organ Component
```

**Our usage**:
- Filter UMLS's 3.5M CUIs down to neuroscience-relevant ones
- Selected 27 semantic types (anatomical, physiological, pathological, chemical)
- Result: 1,015,068 neuroscience CUIs (29% of UMLS)

---

## Source Vocabularies in UMLS

Yes, the **UMLS Metathesaurus has integrated data from all these sources**. Each source is an independent medical terminology system that UMLS links together.

### Major Sources in NeuroDB-2 UMLS Import

| Source Code | Full Name | Type | Terms | Def Coverage |
|-------------|-----------|------|-------|--------------|
| **FMA** | Foundational Model of Anatomy | Anatomy | 99,074 (30%) | 5.1% |
| **SNOMEDCT_US** | SNOMED Clinical Terms (US) | Clinical | 67,590 (21%) | 15.5% |
| **UWDA** | University of Washington Digital Anatomist | Anatomy | 60,201 (18%) | 5.4% |
| **GO** | Gene Ontology | Molecular | 54,118 (17%) | 69.5% ✅ |
| **MEDCIN** | MEDCIN Clinical Terminology | Clinical | 39,773 (12%) | 12.8% |
| **MTH** | UMLS Metathesaurus | Meta | 39,063 (12%) | 40.5% |
| **NCI** | National Cancer Institute Thesaurus | Cancer/Bio | 35,800 (11%) | 89.1% ✅ |
| **MSH** | Medical Subject Headings (MeSH) | Index | 13,739 (4%) | 54.1% ✅ |

**Note**: Percentages show how many of our 325K imported terms came from each source.

### Understanding the Sources

**Anatomical Sources** (FMA, UWDA):
- Focus: Structural hierarchies (brain → cerebrum → frontal lobe)
- Strength: Comprehensive anatomical relationships
- Weakness: Few textual definitions (they're taxonomies, not encyclopedias)
- Volume: 30-18% of our terms
- Definition coverage: 5-6%

**Clinical Sources** (SNOMEDCT_US, MEDCIN):
- Focus: Clinical terminology for medical records
- Strength: Standardized clinical language
- Weakness: Mixed neuroscience relevance
- Volume: 21-12% of our terms
- Definition coverage: 13-16%

**Biomedical Sources** (NCI, GO, MSH):
- Focus: Research terminology, molecular biology, literature indexing
- Strength: Excellent definitions, curated content
- Weakness: Lower volume in neuroscience domain
- Volume: 4-17% of our terms
- Definition coverage: 54-89% ✅

**Metathesaurus (MTH)**:
- Focus: UMLS-created concepts to bridge vocabularies
- Volume: 12% of our terms
- Definition coverage: 40.5%

### How UMLS Integrates Sources

1. **Each source maintains independence**: FMA has its own term IDs, MeSH has its own, etc.

2. **UMLS creates CUIs to link them**: When FMA's "Hippocampus" and MeSH's "Hippocampus" refer to the same concept, UMLS assigns them the same CUI (e.g., C0019564)

3. **MRCONSO shows all variants**: One CUI might have:
   - Preferred term from MSH: "Hippocampus"
   - Synonym from FMA: "Hippocampal formation"
   - Synonym from SNOMEDCT: "Hippocampus proper"

4. **Source priority for conflicts**: When sources disagree, we prioritize:
   - Definitions: MSH > NCI > GO > SNOMEDCT
   - Terms: MSH > SNOMEDCT > NCI > FMA

---

## Why Different Sources Have Different Definition Coverage

**High Coverage (69-89%)**:
- **NCI (89.1%)**: Cancer research focus = every term needs clear definition
- **GO (69.5%)**: Gene/protein ontology = scientific rigor requires definitions
- **MSH (54.1%)**: Literature indexing = definitions needed for cataloging

**Low Coverage (5-16%)**:
- **FMA (5.1%)**: Anatomy atlas, not encyclopedia ("left frontal lobe" needs position, not definition)
- **UWDA (5.4%)**: Digital anatomy model, structural relationships only
- **SNOMEDCT (15.5%)**: Clinical codes, not educational resource

**Key Insight**: Volume ≠ Quality
- FMA contributes 99K terms (30%) but only 5K definitions
- NCI contributes 36K terms (11%) but 32K definitions (89%)

---

## UMLS Import Pipeline Simplified

```
Step 1: Build Neuroscience Filter (MRSTY)
  Input: 3.5M CUIs (all UMLS concepts)
  Filter: 27 neuroscience semantic types
  Output: 1.02M neuroscience CUIs

Step 2: Extract Terms (MRCONSO)
  Input: 17.4M rows (all UMLS terms)
  Filter: Match neuroscience CUIs, English, not suppressed, preferred terms
  Output: 325,241 unique terms

Step 3: Add Definitions (MRDEF)
  Input: MRDEF definition file
  Match: CUIs from Step 2
  Output: 79,617 definitions (24.5%)

Step 4: Add Relationships (MRREL)
  Input: 63.5M relationship rows
  Filter: Domain-specific relationships (exclude taxonomy)
  Extract: 1.8M relationships → map to term names
  Output: 294,008 terms with associations (90.4%)

Step 5: Map to NeuroDB Schema
  Map UMLS data → NeuroDB-2 26-column format
  Add metadata: source='umls', priority=1
  Output: umls_neuroscience_terms.csv (325,241 rows)
```

---

## Quick Reference: File Formats

**RRF Format** (Rich Release Format):
- Pipe-delimited text files: `field1|field2|field3`
- UTF-8 encoding
- One row per relationship/concept/definition
- Designed for streaming (too large to load into memory)

**Why streaming matters**:
- MRREL.RRF = 5.7 GB
- Loading into memory = crashes
- Streaming = process line-by-line, <4GB RAM

---

## Glossary

- **CUI**: Concept Unique Identifier (UMLS's internal ID, e.g., C0019564)
- **SAB**: Source Abbreviation (which vocabulary: MSH, NCI, FMA, etc.)
- **TTY**: Term Type (PT=Preferred, SY=Synonym, AB=Abbreviation)
- **RELA**: Relationship Attribute (part_of, treats, causes, etc.)
- **Semantic Type**: What category a concept belongs to (anatomical, pathological, etc.)
- **Metathesaurus**: UMLS's integrated multi-source database
- **Source Vocabulary**: Original terminology system (MeSH, SNOMED, FMA, etc.)

---

## Common Questions

**Q: Why don't all terms have definitions?**
A: Anatomical sources (FMA, UWDA) are structural taxonomies—they define spatial relationships, not concepts. "Left frontal lobe" needs a position in hierarchy, not a definition.

**Q: Why is MeSH coverage only 4.2%?**
A: Most neuroscience terms come from specialized vocabularies (FMA anatomy, GO molecular biology, NCI cancer biology). MeSH is a literature indexing system—it's authoritative but selective.

**Q: Why accept 24.5% definition coverage?**
A: Lex Stream core agents (spell check, abbreviation, synonym, MeSH detection) don't use definitions. Only Component Detector (optional PICO feature) needs them. Maximum term coverage matters more than definition coverage.

**Q: What's the difference between synonyms and associated terms?**
A:
- **Synonyms**: Different names for the SAME concept (hippocampus = hippocampal formation)
- **Associated terms**: Related but DIFFERENT concepts (hippocampus → memory, temporal lobe, Alzheimer's)

**Q: How do you prevent generic taxonomy pollution?**
A: We exclude pure taxonomy relationships (PAR=Parent, CHD=Child, RB=Broader, RN=Narrower) and only keep domain-specific relationships (part_of, treats, causes, innervates).

---

## For More Information

- **UMLS Documentation**: https://www.nlm.nih.gov/research/umls/
- **Import Quality Profile**: `imports/umls/umls_import_quality_profile.md`
- **Decision Documents**: `docs/decisions/2025-11-20-umls-*.md`
- **Ontology Tracker**: `docs/decisions/ontology-import-tracker.md`

---

**Document Status**: Living reference - update as understanding deepens
**Maintained by**: NeuroDB-2 team
**Last Updated**: 2025-11-21
