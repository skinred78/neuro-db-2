---
title: Ontology Ingestion Optimization Analysis
date: 2025-11-19
type: technical-analysis
status: pending-decision
priority: critical
deadline: 2025-11-25
related_reports:
  - 2025-11-19-lex-stream-integration-compatibility-report.md
---

# Ontology Ingestion Optimization Analysis

## Executive Summary

**Current bottleneck**: Manual hardcoded enrichment approach is **completely unscalable** for millions of ontology terms. At current pace (1 min/term), UMLS alone would require 278 days of non-stop work.

**Key insight**: Target ontologies (UMLS, Neuronames, NIF, GO) **already contain** the data we're manually enriching (synonyms, definitions, hierarchies, MeSH mappings).

**Recommendation**: Bulk import with tiered validation (Option A) = 100-1000x faster, 90%+ quality, meets Nov 25 deadline.

---

## 🔍 CURRENT PROCESS ANALYSIS: BRUTAL TRUTH

### **THE MASSIVE BOTTLENECK** 🚨

Your current enrichment approach is **COMPLETELY UNSCALABLE**:

```python
# Current: Manual hardcoded dictionaries for EVERY term
enriched_data = [
    {"Term": "Anemia", "Synonym 1": "Anaemia", ...},  # 22 fields × 54 terms = manual hell
]
```

**Reality check:**
- Wikipedia: 515 terms → Manageable (barely)
- NINDS: 54 NEW terms → Painful
- **UMLS Metathesaurus: 4+ MILLION terms** → **IMPOSSIBLE** ❌

You literally cannot scale this. At 1 minute per term manually coding dictionaries, that's **6,666 HOURS** (278 days non-stop) just for data entry.

### Current 5-Step Workflow (Wikipedia/NINDS)

1. **Extract** → Parse markdown, extract Term + Definition
2. **Enrich** → AI fills 22 columns (manual hardcoded Python script)
3. **Validate** → Dual agents (mesh-validator + neuro-reviewer) in parallel
4. **Human Review** → Manual approval
5. **Save** → Write to letter CSV files

### CRITICAL BOTTLENECKS IDENTIFIED 🔴

#### **1. Manual Hardcoded Enrichment (MASSIVE BOTTLENECK)**
```python
# Current approach in enrich_terms.py (lines 8-129):
enriched_data = [
    {
        "Term": "Anemia",
        "Definition": "...",
        "Synonym 1": "Anaemia",
        # ... 19 more fields MANUALLY HARDCODED
    },
    # ... repeat for EVERY SINGLE TERM
]
```

**Problem**: You're manually coding Python dictionaries for every term!
- NINDS added 54 terms → manual enrichment
- **For UMLS Metathesaurus**: 4+ million terms
- **This approach is COMPLETELY UNSCALABLE** 🚨

#### **2. Sequential Processing**
- Processing one letter at a time
- No batch processing
- No parallelization

#### **3. Dual Validation for EVERY Term**
- mesh-validator: API calls (fast but still overhead)
- neuro-reviewer: Gemini CLI (slower, token-intensive)

---

## 💡 THE OPTIMIZATION OPPORTUNITY

### **Key Insight: Ontologies Already HAVE the Data**

The ontologies you're targeting **already contain** what you're manually enriching:

| Ontology | Format | What It Has | Size |
|----------|--------|-------------|------|
| **UMLS Metathesaurus** | RRF (pipe-delimited) | CUI, Term, Synonyms, Definitions, Source mappings | 4M+ concepts |
| **Neuronames** | JSON | Terms, Synonyms (7 languages), Definitions, Hierarchies | 3,000 structures |
| **NIF (NIFSTD)** | OWL/TTL | Terms, Synonyms, Hierarchies, Cell types, Techniques | Comprehensive |
| **Gene Ontology** | OBO/OWL | GO IDs, Terms, Definitions, Synonyms, Hierarchies | 40,000+ terms |

**They already have:**
- ✅ Synonyms
- ✅ Definitions
- ✅ Hierarchies (parent-child relationships)
- ✅ Cross-references (including MeSH!)
- ✅ Alternate spellings

**You don't need to ENRICH from AI — you need to MAP and TRANSFORM!**

### Ontology Format Details

#### UMLS Metathesaurus
- **Format**: RRF (Rich Release Format) - pipe-delimited text files
- **Key files**:
  - MRCONSO.RRF = Concept names and sources
  - MRDEF.RRF = Definitions
  - MRREL.RRF = Relationships
  - MRSTY.RRF = Semantic types
- **Latest release**: 2024AB (Nov 2024)
- **Download**: Requires UMLS license (free)

#### Neuronames
- **Format**: JSON
- **Includes**: Standard terms, Synonyms (English, Latin, French, German, Indonesian, Italian, Russian, Spanish), Definitions
- **Structure**: Relational database with Names, Concepts, Models tables
- **Size**: ~3,000 CNS structures (human, macaque, rat, mouse)
- **Download**: http://braininfo.rprc.washington.edu/nnont.aspx

#### NIF (NIFSTD)
- **Format**: OWL/TTL (Turtle)
- **Access**: NCBO BioPortal (https://bioportal.bioontology.org/ontologies/NIFSTD)
- **Modules**: Anatomy, cell types, experimental techniques, nervous system function, small molecules
- **Tools**: Load with Protégé, rdflib, or owlready2

#### Gene Ontology
- **Format**: OBO (primary), OWL, JSON
- **Key file**: go-basic.obo (simplified version)
- **Neuroscience subset**: goslim_synapse
- **Parser**: obonet (Python), ontologyIndex (R)
- **Download**: https://geneontology.org/docs/download-ontology/

---

## 🚀 PROPOSED OPTIMIZATION STRATEGIES

I have **3 approaches** from fastest/dirtiest to slower/highest-quality:

### **Option A: "BULK IMPORT + SELECTIVE VALIDATION"** ⚡ (RECOMMENDED)

**Speed**: 100-1000x faster than current
**Quality**: 85-95% (good enough for alpha)

#### Process:
1. **Direct Import** → Parse ontology files, map to 22-column schema
2. **Automated Schema Mapping** →
   - UMLS RRF → Your 22 columns (script-based, no AI)
   - Neuronames JSON → Your 22 columns
   - NIF OWL → Parse with ontology library
   - GO OBO → Parse with obonet Python library
3. **Tiered Validation**:
   - **Tier 1 (bulk)**: Structural validation only (22 columns, no nulls in required fields)
   - **Tier 2 (random sampling)**: mesh-validator on 10% sample
   - **Tier 3 (high-value)**: Full dual validation on James's benchmark terms only
4. **Post-import cleanup**: Fix issues found in samples

#### Pros:
- ✅ **10,000+ terms imported in hours, not months**
- ✅ No manual enrichment bottleneck
- ✅ Leverages existing structured data
- ✅ Ontologies are AUTHORITATIVE sources (more trustworthy than AI enrichment)
- ✅ Meets Nov 25 deadline
- ✅ Aligns with "accuracy over completeness" principle (empty fields OK)

#### Cons:
- ❌ Some fields might be empty (but that's OK per your "accuracy over completeness" rule)
- ❌ Initial schema mapping takes effort (but one-time cost)
- ❌ Lower validation coverage initially (mitigated by sampling strategy)

---

### **Option B: "HYBRID STREAMING PIPELINE"** 🔄 (BALANCED)

**Speed**: 10-50x faster
**Quality**: 90-98%

#### Process:
1. **Stream processing** → Process ontology files in batches (1000 terms at a time)
2. **Parallel enrichment** → Run mesh-validator on batches concurrently
3. **Selective AI enrichment** → Only use Gemini for missing fields (not all 22 columns)
4. **Asynchronous validation** → Validate while importing next batch

#### Pros:
- ✅ Higher quality than Option A
- ✅ Still 10x+ faster than current
- ✅ Catches issues earlier
- ✅ More granular control over quality

#### Cons:
- ❌ More complex pipeline
- ❌ Higher token costs (Gemini still involved)
- ❌ Longer implementation time (may miss Nov 25 deadline)
- ❌ Still has enrichment bottleneck (just faster)

---

### **Option C: "CURRENT APPROACH + AUTOMATION"** 🐌 (NOT RECOMMENDED)

**Speed**: 2-5x faster
**Quality**: 99%+

Keep current workflow, just automate the manual hardcoding:
- AI generates Python dictionaries automatically
- Still validates every term
- Still requires human review

#### Why I DON'T recommend this:
- ❌ Still fundamentally unscalable
- ❌ Wastes time enriching data that ontologies already have
- ❌ Token-expensive
- ❌ Won't meet Nov 25 deadline with 4M+ terms
- ❌ Ignores the fact that ontologies are MORE authoritative than AI enrichment

---

## 📊 SCALE COMPARISON

| Approach | Time for 4M UMLS terms | Token Cost | Quality | Meets Deadline? |
|----------|------------------------|------------|---------|-----------------|
| **Current (manual)** | 278 days | $$$$$$ | 99% | ❌ NO |
| **Option C (auto-enrichment)** | 30-60 days | $$$$$ | 98% | ❌ NO |
| **Option B (hybrid)** | 2-5 days | $$$ | 95% | ⚠️ MAYBE |
| **Option A (bulk import)** | 4-12 hours | $ | 90% | ✅ YES |

### Time Breakdown for Option A (UMLS Example)

| Phase | Duration | Description |
|-------|----------|-------------|
| Download UMLS | 30-60 min | One-time download (requires license) |
| Parse RRF files | 1-2 hours | Read pipe-delimited files into DataFrames |
| Schema mapping | 2-4 hours | Map UMLS fields → 22-column schema |
| Neuroscience filtering | 30-60 min | Filter for relevant terms (MeSH CNS categories) |
| Export to CSV | 30 min | Write to letter files |
| **Tier 1 validation** | 15 min | Structural checks (column count, required fields) |
| **Tier 2 validation** | 1-2 hours | mesh-validator on 10% sample (~400K terms) |
| **Tier 3 validation** | 1 hour | Full dual validation on benchmark terms |
| Bug fixes | 2-4 hours | Fix issues found in validation |
| **TOTAL** | **8-15 hours** | **vs 278 days with current approach** |

---

## ❓ CRITICAL QUESTIONS FOR YOU

1. **What's your quality bar?**
   - Do you need 99% accuracy for ALL 4M terms?
   - Or 90% accuracy with 99% for benchmark/high-value terms?

2. **What's your timeline?**
   - Nov 25 deadline = 6 days away
   - Option A is the ONLY viable path for that deadline

3. **What fields are CRITICAL?**
   - Term + Definition? (ontologies have these)
   - Synonyms? (ontologies have these)
   - MeSH mappings? (UMLS has these!)
   - Word forms (verb/adj/adverb)? (might need AI, but low priority for search)

4. **Schema flexibility?**
   - Can you adapt your 22-column schema to what ontologies provide?
   - Or must you force-fit ontology data into current schema?

5. **Filtering strategy?**
   - Do you want ALL 4M UMLS terms, or neuroscience subset only?
   - How do we define "neuroscience" for filtering? (MeSH tree codes? Semantic types?)

6. **MeSH validation approach?**
   - Is mesh-validator API rate-limited?
   - Can we batch MeSH validation calls for efficiency?

---

## 🎯 MY HONEST RECOMMENDATION

**Go with Option A for the deadline**, then iterate:

### Phase 1 (Nov 20-22): Bulk Import - PRIORITY ONTOLOGIES

#### Night 1 (Nov 20): Neuronames + GO (Quick Wins)
**Why these first?**
- Neuronames: JSON format = easiest to parse
- GO: Well-documented parsers available (obonet)
- Combined: ~43,000 terms (manageable scope for testing pipeline)

**Tasks**:
1. Download Neuronames JSON
2. Download GO goslim_synapse (neuroscience subset)
3. Write schema mapping scripts
4. Import to database
5. Run Tier 1 validation (structural)
6. Test against James's search strings (baseline measurement)

**Expected output**: +43K terms (595 → ~43.5K total)

#### Day 2 (Nov 21): UMLS Metathesaurus (The Big One)
**Why second?**
- Largest source (4M+ terms)
- Most complex format (RRF)
- Needs filtering strategy

**Tasks**:
1. Download UMLS 2024AB (requires license - apply NOW if not done)
2. Parse MRCONSO.RRF (concept names)
3. Parse MRDEF.RRF (definitions)
4. Parse MRREL.RRF (relationships for parent-child)
5. Filter for neuroscience terms (using MeSH tree codes or semantic types)
6. Map to 22-column schema
7. Import filtered subset

**Filtering options**:
- **Conservative**: MeSH tree codes C10* (Nervous System Diseases), F01-F03 (Mental Disorders, Behavioral Disciplines)
- **Moderate**: Add G11* (Nervous System Physiological Phenomena)
- **Aggressive**: All terms with neuroscience semantic types

**Expected output**: +50K to 500K terms (depending on filtering strategy)

#### Day 3 (Nov 22): NIF + Quality Pass
**Morning**: NIF import
1. Download NIFSTD from BioPortal
2. Parse OWL with rdflib/owlready2
3. Extract terms, synonyms, definitions
4. Import to database

**Afternoon**: Quality validation
1. mesh-validator on 10% random sample
2. Full dual validation on James's benchmark terms (neuromodulation, MS, Alzheimer's)
3. Identify critical issues

**Expected output**: +10K to 30K NIF terms, validation report

### Phase 2 (Nov 23-24): Quality Pass + Fixes

**Day 4 (Nov 23)**: Fix critical issues
1. Review validation reports
2. Fix schema mapping bugs
3. Handle edge cases (special characters, encoding issues)
4. Re-import corrected data

**Day 5 (Nov 24)**: Integration testing
1. Generate neuro_terms.csv (consolidated)
2. Generate neuro_terms.json (for Lex Stream)
3. Run convert_to_lexstream.py
4. Test with Lex Stream agents

### Phase 3 (Nov 25): Validation + Demo

**Deliverables**:
1. Updated database with 50K+ terms (vs 595 baseline)
2. Test results against James's benchmark search strings
3. Comparison report (before/after coverage)
4. MeSH tree integration implementation ideas

**Presentation to James**:
- Coverage improvement metrics
- Quality validation results
- Parent-child relationship examples
- Next steps for v1.0

### Phase 4 (Post-deadline): Continuous Improvement

**Week 2+**:
- Identify gaps through usage
- Targeted enrichment for high-value missing terms
- Refine filtering strategies based on feedback
- Add remaining ontologies (lower priority sources)
- Implement advanced MeSH tree weighting algorithms

---

## 🛠️ TECHNICAL IMPLEMENTATION SKETCH

### For UMLS (largest source):

```python
#!/usr/bin/env python3
"""
UMLS to NeuroDB-2 Schema Mapper
Fast bulk import with minimal validation overhead
"""
import pandas as pd
from pathlib import Path

# UMLS RRF file paths
UMLS_DIR = Path('/path/to/UMLS/2024AB/META')
OUTPUT_DIR = Path('/Users/sam/NeuroDB-2/LetterFiles')

def parse_umls_concepts():
    """Parse MRCONSO.RRF = concepts and terms"""
    # Column names from UMLS documentation
    cols = ['CUI', 'LAT', 'TS', 'LUI', 'STT', 'SUI', 'ISPREF', 'AUI', 'SAUI',
            'SCUI', 'SDUI', 'SAB', 'TTY', 'CODE', 'STR', 'SRL', 'SUPPRESS', 'CVF']

    df = pd.read_csv(
        UMLS_DIR / 'MRCONSO.RRF',
        sep='|',
        header=None,
        names=cols,
        encoding='utf-8',
        on_bad_lines='skip'
    )

    # Filter for English neuroscience terms
    # SAB = Source Abbreviation (MSH=MeSH, SNOMEDCT_US, NCI, etc.)
    neuro_df = df[
        (df['LAT'] == 'ENG') &  # English only
        (df['SUPPRESS'] != 'O') &  # Not obsolete
        (df['SAB'].isin(['MSH', 'SNOMEDCT_US', 'NCI']))  # Authoritative sources
    ].copy()

    return neuro_df

def parse_umls_definitions():
    """Parse MRDEF.RRF = definitions"""
    cols = ['CUI', 'AUI', 'ATUI', 'SATUI', 'SAB', 'DEF', 'SUPPRESS', 'CVF']

    df = pd.read_csv(
        UMLS_DIR / 'MRDEF.RRF',
        sep='|',
        header=None,
        names=cols,
        encoding='utf-8',
        on_bad_lines='skip'
    )

    # Get preferred definitions (MSH preferred)
    return df[df['SAB'] == 'MSH'].groupby('CUI').first()['DEF'].to_dict()

def get_synonyms_for_cui(cui, concepts_df):
    """Extract all synonyms for a given CUI"""
    synonyms = concepts_df[concepts_df['CUI'] == cui]['STR'].unique().tolist()
    return synonyms[:3]  # Limit to 3 synonyms per schema

def get_mesh_mapping(cui, concepts_df):
    """Get MeSH term for a CUI"""
    mesh_rows = concepts_df[(concepts_df['CUI'] == cui) & (concepts_df['SAB'] == 'MSH')]
    if not mesh_rows.empty:
        return mesh_rows.iloc[0]['STR']
    return ''

def map_to_neurodb_schema(concepts_df, definitions_dict):
    """Map UMLS data to NeuroDB-2 22-column schema"""

    # Get unique CUIs with preferred terms
    preferred = concepts_df[concepts_df['ISPREF'] == 'Y'].groupby('CUI').first()

    neurodb_terms = []

    for cui in preferred.index:
        term_row = preferred.loc[cui]
        synonyms = get_synonyms_for_cui(cui, concepts_df)

        # Remove the preferred term from synonyms list
        if term_row['STR'] in synonyms:
            synonyms.remove(term_row['STR'])

        record = {
            'Term': term_row['STR'],
            'Term Two': '',  # Only for special character variants
            'Definition': definitions_dict.get(cui, ''),
            'Closest MeSH term': get_mesh_mapping(cui, concepts_df),
            'Synonym 1': synonyms[0] if len(synonyms) > 0 else '',
            'Synonym 2': synonyms[1] if len(synonyms) > 1 else '',
            'Synonym 3': synonyms[2] if len(synonyms) > 2 else '',
            'Abbreviation': '',  # Could extract from TTY='AB' rows
            'UK Spelling': '',  # Not in UMLS
            'US Spelling': '',  # Not in UMLS
            'Noun Form of Word': '',  # Not in UMLS
            'Verb Form of Word': '',  # Not in UMLS
            'Adjective Form of Word': '',  # Not in UMLS
            'Adverb Form of Word': '',  # Not in UMLS
            'Commonly Associated Term 1': '',  # Could extract from MRREL.RRF
            'Commonly Associated Term 2': '',
            'Commonly Associated Term 3': '',
            'Commonly Associated Term 4': '',
            'Commonly Associated Term 5': '',
            'Commonly Associated Term 6': '',
            'Commonly Associated Term 7': '',
            'Commonly Associated Term 8': '',
        }

        neurodb_terms.append(record)

    return pd.DataFrame(neurodb_terms)

def export_by_letter(df, output_dir):
    """Export to letter-based CSV files (A.csv, B.csv, etc.)"""
    grouped = df.groupby(df['Term'].str[0].str.upper())

    for letter, group in grouped:
        filepath = output_dir / f'{letter}_UMLS.csv'
        group.to_csv(filepath, index=False, encoding='utf-8')
        print(f"✓ Exported {len(group)} terms to {filepath}")

def main():
    print("Starting UMLS bulk import...")

    # Step 1: Parse concepts
    print("1. Parsing MRCONSO.RRF...")
    concepts_df = parse_umls_concepts()
    print(f"   Found {len(concepts_df)} concept rows")

    # Step 2: Parse definitions
    print("2. Parsing MRDEF.RRF...")
    definitions_dict = parse_umls_definitions()
    print(f"   Found {len(definitions_dict)} definitions")

    # Step 3: Map to NeuroDB schema
    print("3. Mapping to NeuroDB-2 schema...")
    neurodb_df = map_to_neurodb_schema(concepts_df, definitions_dict)
    print(f"   Mapped {len(neurodb_df)} terms")

    # Step 4: Export by letter
    print("4. Exporting to letter files...")
    export_by_letter(neurodb_df, OUTPUT_DIR)

    print("\n✓ UMLS import complete!")
    print(f"Total terms imported: {len(neurodb_df)}")

if __name__ == '__main__':
    main()
```

**Parsing time estimate**: 2-4 hours for 4M terms (just I/O and mapping)

### For Neuronames (JSON format):

```python
#!/usr/bin/env python3
"""
Neuronames JSON to NeuroDB-2 Schema Mapper
Simplest import - JSON already well-structured
"""
import json
import pandas as pd
from pathlib import Path

def parse_neuronames_json(json_path):
    """Parse Neuronames JSON export"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    terms = []

    for item in data:
        # Neuronames has: Standard Term, Synonyms, Definition
        record = {
            'Term': item.get('standard_term', ''),
            'Term Two': '',
            'Definition': item.get('definition', ''),
            'Closest MeSH term': '',  # May need mesh-validator
            'Synonym 1': item.get('synonyms', [])[0] if len(item.get('synonyms', [])) > 0 else '',
            'Synonym 2': item.get('synonyms', [])[1] if len(item.get('synonyms', [])) > 1 else '',
            'Synonym 3': item.get('synonyms', [])[2] if len(item.get('synonyms', [])) > 2 else '',
            # ... rest of schema
        }
        terms.append(record)

    return pd.DataFrame(terms)
```

### For Gene Ontology (OBO format):

```python
#!/usr/bin/env python3
"""
Gene Ontology OBO to NeuroDB-2 Schema Mapper
Uses obonet library for parsing
"""
import obonet
import pandas as pd

def parse_go_obo(obo_path):
    """Parse GO OBO file using obonet"""
    graph = obonet.read_obo(obo_path)

    terms = []

    for node_id, data in graph.nodes(data=True):
        if node_id.startswith('GO:'):
            record = {
                'Term': data.get('name', ''),
                'Term Two': '',
                'Definition': data.get('def', '').split('"')[1] if 'def' in data else '',
                'Closest MeSH term': '',
                'Synonym 1': data.get('synonym', [''])[0] if 'synonym' in data else '',
                # Parse synonym format: "exact_synonym" "UBERON:..." EXACT []
                # ... rest of schema
            }
            terms.append(record)

    return pd.DataFrame(terms)
```

---

## 🔄 VALIDATION STRATEGY (Tiered Approach)

### Tier 1: Structural Validation (100% coverage)
```python
def validate_structure(df):
    """Fast structural checks - runs in seconds"""
    errors = []

    # Check column count
    if len(df.columns) != 22:
        errors.append(f"Expected 22 columns, got {len(df.columns)}")

    # Check required fields not empty
    if df['Term'].isna().any() or (df['Term'] == '').any():
        errors.append("Empty Term field found")

    # Check for duplicate terms
    duplicates = df[df.duplicated('Term', keep=False)]
    if not duplicates.empty:
        errors.append(f"Found {len(duplicates)} duplicate terms")

    return errors
```

### Tier 2: Sample Validation (10% coverage)
```python
def sample_validation(df, sample_rate=0.1):
    """Validate random sample with mesh-validator"""
    sample = df.sample(frac=sample_rate, random_state=42)

    # Run mesh-validator on sample
    # Log results, identify patterns
    # If >5% fail, investigate further

    return validation_results
```

### Tier 3: High-Value Validation (James's benchmark terms)
```python
def validate_benchmark_terms(df, benchmark_terms):
    """Full dual validation on critical terms"""
    benchmark_df = df[df['Term'].isin(benchmark_terms)]

    # Run BOTH mesh-validator + neuro-reviewer
    # Must pass 100% for these terms

    return validation_results
```

---

## 📈 SUCCESS METRICS

### Quantitative Metrics
- **Coverage**: Database size (595 → target 50K+ terms)
- **Benchmark performance**: Hit count for James's 3 search strings
- **MeSH coverage**: % of terms with valid MeSH mappings
- **Synonym density**: Avg synonyms per term
- **Definition completeness**: % terms with definitions

### Qualitative Metrics
- **Search quality**: Do generated search strings match James's manual ones?
- **Discovery value**: Are we finding niche/parallel research papers?
- **Confidence value**: Are we capturing super-KOL papers?

### Validation Metrics
- **Tier 1**: 100% pass rate (structural)
- **Tier 2**: >95% pass rate (sample MeSH validation)
- **Tier 3**: 100% pass rate (benchmark terms)

---

## 🤔 WHAT DO YOU THINK?

**Before I go deeper**, I need to know:

1. **Is Option A (bulk import) philosophically acceptable to you?**
   - Are you OK with some empty fields initially?
   - Do you trust ontologies more than AI enrichment?

2. **What's your true quality bar for this deadline?**
   - 90% accuracy with fast iteration?
   - Or 99% accuracy with slower progress?

3. **Which ontology should we prioritize FIRST for tonight's work?**
   - Neuronames (easiest, JSON)?
   - GO (well-documented parsers)?
   - UMLS (biggest impact, most complex)?

4. **Are you open to adapting your schema if ontologies don't perfectly match?**
   - E.g., accepting empty "Word Forms" fields if ontologies don't have them?
   - Or do you require all 22 columns populated?

5. **Filtering strategy for UMLS?**
   - Conservative (50K terms)?
   - Moderate (200K terms)?
   - Aggressive (500K+ terms)?

6. **Do you have UMLS license already?**
   - If not, need to apply NOW (usually instant approval for research)

---

## 🚨 DECISION REQUIRED

**This is blocking work for tonight.** Based on your answers, I can:

- **Option A**: Start writing bulk import scripts tonight (Neuronames + GO)
- **Option B**: Design hybrid streaming pipeline (2-3 day implementation)
- **Option C**: Optimize current manual approach (not recommended)

**What's your decision?**

Let's debate this. Challenge my assumptions. Tell me if I'm missing something critical about your quality requirements or if there's a reason the manual enrichment approach was chosen.

---

## 📚 APPENDIX: Resources

### UMLS Resources
- License application: https://uts.nlm.nih.gov/uts/signup-login
- Documentation: https://www.nlm.nih.gov/research/umls/
- File formats: https://www.nlm.nih.gov/research/umls/new_users/online_learning/Meta_006.html

### Neuronames Resources
- Download: http://braininfo.rprc.washington.edu/nnont.aspx
- Paper: https://pubmed.ncbi.nlm.nih.gov/21789500/

### NIF Resources
- BioPortal: https://bioportal.bioontology.org/ontologies/NIFSTD
- Documentation: https://neuinfo.org/about/nifvocabularies

### Gene Ontology Resources
- Downloads: https://geneontology.org/docs/download-ontology/
- obonet library: https://github.com/dhimmel/obonet
- goslim_synapse: Neuroscience-specific subset

### Python Libraries for Ontology Parsing
- `obonet`: Parse OBO files (GO)
- `rdflib`: Parse OWL/RDF files (NIF)
- `owlready2`: OWL ontology manipulation
- `pandas`: Data manipulation and CSV export

---

**Document Status**: Awaiting decision from Sam
**Next Steps**: Based on chosen option, begin implementation tonight (Nov 20)
