# First Principles: Lex Stream Query Translation

## Core User Need

Neuroscientists want to find **5-20 highly relevant papers from the last 60 days** in their niche area of interest.

**Key insight**: Neuroscientists don't think in PubMed syntax. They think in **concepts**:
- Conditions (MS, Parkinson's, depression)
- Treatments/Interventions (neuromodulation, deep brain stimulation, SSRIs)
- Outcomes (cognitive improvement, symptom reduction)
- Brain regions/systems (basal ganglia, prefrontal cortex)
- Mechanisms (neuroplasticity, dopamine signaling)

**The translation problem:**
```
User's conceptual intent    →    Precise PubMed query    →    5-20 relevant papers
"MS + neuromodulation"           (what syntax?)               (niche, latest)
```

## What Does "MS + neuromodulation" Actually Mean?

When a neuroscientist types this, they likely mean:
> "Show me recent papers about using neuromodulation techniques to treat Multiple Sclerosis"

This has implicit structure:
- **Condition**: Multiple Sclerosis
- **Intervention**: Neuromodulation (as a treatment approach)
- **Relationship**: Treatment/therapeutic application

The current problem: Expanding both terms independently loses this semantic relationship.

## Success Criteria

A successful solution would:
1. Accept natural concept-based input from neuroscientists
2. Understand the semantic relationships between concepts
3. Generate precise PubMed queries that preserve intent
4. Return 5-20 highly relevant papers from the last 60 days
5. Allow saving as reusable "streams"

---

## Research Findings: Available APIs & Tools

### Key Insight #1: PubMed Already Does MeSH Expansion
- **Automatic Term Mapping (ATM)** - built-in query expansion
- **MeSH Explosion** - automatically includes narrower terms
- We shouldn't duplicate this; we should enhance it

### Key Insight #2: Hidden Gems for Concept Understanding

**PubTator 3.0** (HIGHLY RECOMMENDED)
- AI-powered concept extraction from text
- 9 entity types: gene, disease, chemical, species, variant, cell line, cell type, DNA, RNA
- 12 relation types: association, cause, treatment, inhibition, etc.
- **Semantic & relation search built-in**
- Free API, weekly updates
- 36M PubMed abstracts pre-annotated

**UMLS Metathesaurus API**
- 135 semantic types (e.g., "Disease or Syndrome", "Therapeutic Procedure")
- Concept relationships ("isa", "treats", etc.)
- This is EXACTLY what James wanted for classifying concepts
- Free with registration

**BERN2** (State-of-the-art NER)
- 9 entity types recognized
- Pre-computed: 33.4M PubMed articles
- Web API available
- Fast concept extraction

### Key Insight #3: Alternative Search Backends

**OpenAlex** - 98.6% coverage (better than PubMed's 93%)
- Open access, no restrictions
- Could be used as primary or backup

### Key Insight #4: No One Has Built This
> "No modern, production-ready 'concept → PubMed query' API exists. This is YOUR opportunity!"

---

## Fresh Start Architecture

```
User Input: "MS treatment with neuromodulation"
                    ↓
[1] CONCEPT EXTRACTION (PubTator 3.0 or BERN2)
    → "MS" (disease), "neuromodulation" (therapeutic)
                    ↓
[2] SEMANTIC CLASSIFICATION (UMLS API)
    → MS = Condition (CUI: C0026769)
    → neuromodulation = Intervention (CUI: C0520587)
                    ↓
[3] SMART EXPANSION (based on semantic type)
    → Conditions: expand to synonyms only
    → Interventions: expand to related techniques
    → (Use MeSH trees for hierarchy)
                    ↓
[4] QUERY CONSTRUCTION
    → ("Multiple Sclerosis"[MeSH] OR "MS"[tiab])
      AND ("Neuromodulation"[MeSH] OR "TMS"[tiab] OR ...)
    → Add: last 60 days filter
                    ↓
[5] SEARCH (PubMed E-utilities)
    → 5-20 relevant papers
```

---

## What This Means for NeuroDB-2

**Option A: NeuroDB-2 becomes supplementary**
- External APIs handle core concept extraction/classification
- NeuroDB-2 adds neuroscience-specific expansions not in UMLS/MeSH
- Much smaller, focused database

**Option B: NeuroDB-2 becomes unnecessary**
- If UMLS + MeSH + PubTator cover neuroscience well enough
- Our database might be redundant with better API usage

**Option C: NeuroDB-2 as caching/customization layer**
- Cache common UMLS/MeSH lookups
- Store user-specific preferences
- Handle neuroscience edge cases

---

---

## POC Plan: API-First Validation

**Goal**: Prove APIs can solve "MS + neuromodulation" problem (1 hit → 10+ hits)
**Effort**: 5-7 hours | **Cost**: $0 | **Timeline**: 1 week

### Prerequisites
1. Register for UMLS API key (free, instant): https://uts.nlm.nih.gov/uts/signup-login
2. Python 3.8+ with `requests`, `python-dotenv`

### Implementation Phases

**Phase 1: API Clients (2-3 hrs)**
```
poc-api-first/
├── clients/
│   ├── pubtator.py   # Concept extraction (9 entity types)
│   ├── umls.py       # Semantic types (135 types)
│   └── pubmed.py     # E-utilities search
```

**Phase 2: Semantic Pipeline (2-3 hrs)**
- Classify terms using UMLS semantic types
- Map to categories: CONDITION (T047), INTERVENTION (T061), OUTCOME (T042)
- Build query with appropriate expansion per category

**Phase 3: Testing (2-3 hrs)**

| Test Case | Expected Classification | Success Criteria |
|-----------|------------------------|------------------|
| "MS + neuromodulation" | MS=CONDITION, neuromodulation=INTERVENTION | 5-20 results |
| "MS motor function" | MS=CONDITION, motor function=OUTCOME | >0 results |
| Complex multi-term | Mixed categories | >0 results |

**Success Metrics**:
- API correctly classifies semantic types
- Query returns 5-20 relevant papers (not 1, not 1000s)
- ≥80% precision in top 10 results (manual review)
- Latency <2 seconds

### Decision Framework

**If POC succeeds**:
- Implement Hybrid (API semantic + local expansion)
- NeuroDB-2 becomes abbreviation layer only
- Stop manual synonym enrichment

**If POC fails**:
- Continue current path (UMLS local import)
- Document failure reasons
- Re-evaluate in 6-12 months

### Files to Create
```
/Users/sam/NeuroDB-2/poc-api-first/
├── .env                    # UMLS_API_KEY
├── clients/                # API clients
├── poc_pipeline.py         # Main pipeline
├── test_poc.py             # Test suite
├── comparison_report.md    # API vs NeuroDB-2
└── results/                # Test outputs
```

---

## Unresolved Questions

1. **Abbreviation handling**: APIs don't expand abbreviations. Keep NeuroDB-2 abbreviation layer?
2. **Multi-term disambiguation**: How to handle "MS" (multiple sclerosis vs mass spectrometry)?
3. **Caching strategy**: Redis? Local JSON? TTL?
4. **James validation**: Should neuroscientist review API-generated queries?
