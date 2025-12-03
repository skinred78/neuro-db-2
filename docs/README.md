# NeuroDB-2 Documentation Guide

**Purpose**: Navigation guide for project documentation
**Last Updated**: 2025-12-03

---

## Quick Start

### What is NeuroDB-2?
Neuroscience terminology database powering [Lex Stream](../Lex-stream-2) query expansion pipeline. Evolved from manual Wikipedia curation (649 terms) to hybrid API-first architecture (PubTator + UMLS + local database).

### Current Status (Dec 2025)
**Phase 6**: Hybrid Approach (POC validated)
- **API Layer**: PubTator (abbreviations) + UMLS (semantics)
- **Local Database**: 649 high-quality terms (synonyms, abbreviations)
- **POC Results**: 5 relevant papers (vs 1-14 with blind expansion)

**Next**: Production implementation (Redis caching, <2s latency target)

---

## Documentation Structure

```
docs/
├── timeline/
│   └── PROJECT_TIMELINE.md          # Complete project chronology (Phase 1-6)
├── decisions/
│   ├── ontology-import-tracker.md   # UMLS/NIF import tracker (DEC-001 to DEC-004)
│   ├── 2025-11-19-nif-associated-terms-decision.md
│   ├── 2025-11-20-umls-cui-filter-count-decision.md
│   ├── 2025-11-20-umls-coverage-strategy-decision.md
│   └── lex-stream-data-layer-problem-statement.docx
├── plans/
│   ├── api-first-poc-detailed.md    # POC implementation plan
│   └── api-first-poc-summary.md     # POC executive summary
├── analysis/
│   ├── 2025-11-28_1400_lexstream-comprehensive-research.md
│   ├── 2025-11-19-lex-stream-integration-compatibility-report.md
│   └── 2025-11-19-ontology-ingestion-optimization-analysis.md
├── archive/
│   ├── LEXSTREAM_INTEGRATION_REPORT.md  # Phase 1 integration (v2.0.0)
│   ├── CHANGELOG.md                     # Historical changelog
│   ├── VERSIONING_SUMMARY.md            # Version history
│   ├── SCHEMA_MIGRATION.md              # Schema evolution
│   ├── mesh_final_report.md             # MeSH validation
│   └── mesh_validation_results.json     # Validation data
├── feedback/
│   └── (neuroscientist feedback)
├── DATABASE_CREATION_GUIDE.md       # Original manual workflow
├── UMLS_EXPLAINED.md                # UMLS integration guide
├── UMLS_LEXSTREAM_INTEGRATION_SUMMARY.md  # Phase 2 summary
├── UPDATE_WORKFLOW.md               # Maintenance procedures
├── VERSIONING_CONVENTIONS.md        # Version control standards
├── agent-orchestration.md           # ClaudeKit agent patterns
├── data-quality-standards.md        # Quality metrics
├── mesh-validation-guide.md         # MeSH validation process
└── project-overview.md              # Original project overview

poc-api-first/
└── POC_RESULTS.md                   # Phase 5 POC results (Dec 2025)

plans/ (root)
├── 2025-11-19-scalable-ontology-ingestion-with-source-control.md
├── 2025-11-20-umls-importer-implementation-plan.md
├── 251121-umls-phase2a-synonym-abbreviation-expansion.md
└── research/
    └── 251128-umls-semantic-types-pico-classification.md
```

---

## Key Documents by Use Case

### Understanding Project Evolution
📖 **Start here**: `timeline/PROJECT_TIMELINE.md`
- Complete chronology (Phase 1-6)
- Decision log (DEC-001 to DEC-005)
- Metrics comparison across phases
- Lessons learned

### Understanding Current Architecture (Hybrid Approach)
🏗️ **Phase 5 POC**: `../poc-api-first/POC_RESULTS.md`
- API-first validation (PubTator + UMLS)
- "MS + neuromodulation" case study
- 5-layer pipeline architecture
- Performance metrics (15s latency, 100% accuracy)

🏗️ **Phase 6 Plan**: `timeline/PROJECT_TIMELINE.md#phase-6`
- Hybrid architecture (API + local database)
- NeuroDB-2 value proposition
- Production roadmap (Weeks 1-4)

### UMLS Integration (Phase 2)
📊 **Import Tracker**: `decisions/ontology-import-tracker.md`
- NIF import (1,636 terms)
- UMLS import (325,241 terms)
- Phase 2A synonym expansion (DEC-004)
- Data quality characteristics
- Decision log (DEC-001 to DEC-004)

📊 **Coverage Summary**: `UMLS_LEXSTREAM_INTEGRATION_SUMMARY.md`
- Phase 2A results (10% synonyms, 0.5% abbreviations)
- Trade-offs analysis (UMLS strengths vs limitations)
- Export to Lex Stream (v3.0.0)

📊 **Implementation Plans**:
- `../plans/2025-11-19-scalable-ontology-ingestion-with-source-control.md` (NIF)
- `../plans/2025-11-20-umls-importer-implementation-plan.md` (UMLS)
- `../plans/251121-umls-phase2a-synonym-abbreviation-expansion.md` (Phase 2A)

### Lex Stream Integration
🔗 **Comprehensive Research**: `analysis/2025-11-28_1400_lexstream-comprehensive-research.md`
- Lex Stream architecture (5-agent pipeline)
- Database requirements (primary_term, synonyms, abbreviations, mesh_term)
- Integration points (SpellChecker, AbbreviationExpander, SynonymFinder, MeSH Detector)
- Success metrics (coverage targets)

🔗 **Phase 1 Integration**: `archive/LEXSTREAM_INTEGRATION_REPORT.md`
- v2.0.0 validation (649 terms)
- Test results (95% pass rate)
- Coverage stats (42.7% synonyms, 22.2% abbreviations)

🔗 **Phase 2 Integration**: `UMLS_LEXSTREAM_INTEGRATION_SUMMARY.md`
- v3.0.0 UMLS database (325K terms)
- Testing results (24/24 tests passed)
- Performance (1.38s load time, 189 MB)

### Decision History
📋 **All Decisions**: `timeline/PROJECT_TIMELINE.md#key-decisions-log`

**Critical Decisions**:
- **DEC-001** (Nov 19): Skip NIF taxonomy associations
- **DEC-002** (Nov 20): Proceed with 1M CUIs + multi-stage filtering
- **DEC-003** (Nov 20): Import all 325K UMLS terms (24.5% definitions)
- **DEC-004** (Nov 21): Accept UMLS synonym limitation (10% coverage)
- **DEC-005** (Dec 2): GO - API-first POC validated, implement hybrid

**Decision Documents**:
- `decisions/2025-11-19-nif-associated-terms-decision.md` (DEC-001)
- `decisions/2025-11-20-umls-cui-filter-count-decision.md` (DEC-002)
- `decisions/2025-11-20-umls-coverage-strategy-decision.md` (DEC-003)
- `decisions/ontology-import-tracker.md` (DEC-004)
- `../poc-api-first/POC_RESULTS.md` (DEC-005)

### Neuroscientist Feedback
💬 **James's Feedback** (Nov 17 & 28):
- `analysis/2025-11-28_1400_lexstream-comprehensive-research.md#phase-3`
- Key insight: "Secret sauce comes from understanding hierarchy of terms"
- MeSH hierarchy trees example (Parkinson's Disease)
- Requirements: 3,500-4,000 terms, 70-80% synonym coverage

### Data Quality & Standards
📐 **Standards**: `data-quality-standards.md`
- Coverage targets by field
- Validation requirements
- Quality metrics

📐 **MeSH Validation**: `mesh-validation-guide.md`
- mesh-validator agent workflow
- NIH MeSH API integration
- Correction tracking

📐 **Validation Results**: `archive/mesh_final_report.md`
- Phase 1 MeSH validation (595 terms)
- Correction logs

### Maintenance & Operations
🔧 **Update Workflow**: `UPDATE_WORKFLOW.md`
- Adding new terms
- Validation procedures
- Export to Lex Stream

🔧 **Versioning**: `VERSIONING_CONVENTIONS.md`
- Semantic versioning (v2.0.0, v3.0.0)
- Database changelog
- Migration procedures

🔧 **Database Creation**: `DATABASE_CREATION_GUIDE.md`
- Original manual workflow (Phase 1)
- 5-step process (ingest, enrich, validate, review, save)
- Letter-by-letter processing

### Agent Orchestration
🤖 **ClaudeKit Agents**: `agent-orchestration.md`
- mesh-validator (MeSH API validation)
- neuro-reviewer (Gemini-based validation)
- planner, researcher, tester, debugger
- Parallel vs sequential execution

---

## Historical Context (Archive)

### Phase 1: Manual Database (Nov 7-12, 2025)
**Artifacts**:
- `archive/LEXSTREAM_INTEGRATION_REPORT.md` - v2.0.0 validation
- `archive/CHANGELOG.md` - Historical changes
- `archive/VERSIONING_SUMMARY.md` - Version history
- `archive/SCHEMA_MIGRATION.md` - Schema evolution (19→22 columns)
- `archive/mesh_final_report.md` - MeSH validation

**Data**:
- `../data/LetterFiles/[A-Z].csv` - Individual letter databases
- `../data/neuro_terms.csv` - Master database (595 terms)
- `../data/neuro_terms_v2.0.0_wikipedia-ninds.json` - Lex Stream export

### Phase 2: UMLS Integration (Nov 19-21, 2025)
**Artifacts**:
- `decisions/ontology-import-tracker.md` - Import tracker
- `UMLS_EXPLAINED.md` - UMLS primer
- `UMLS_LEXSTREAM_INTEGRATION_SUMMARY.md` - Integration summary

**Data**:
- `../imports/nif/` - NIF import (1,636 terms)
- `../imports/umls/` - UMLS import (325K terms)
- `../data/neuro_terms_v3.0.0_umls.json` - UMLS export (189 MB)

### Phase 5: API-First POC (Dec 2-3, 2025)
**Artifacts**:
- `plans/api-first-poc-detailed.md` - Detailed plan
- `plans/api-first-poc-summary.md` - Executive summary
- `../poc-api-first/POC_RESULTS.md` - Results

**Code**:
- `../poc-api-first/poc_pipeline.py` - 5-layer pipeline
- `../poc-api-first/clients/` - PubTator, UMLS, PubMed clients

---

## Data Files Location

### Production Data
**Location**: `../data/`

**Term Databases**:
- `neuro_terms.csv` - Phase 1 master (595 terms)
- `neuro_terms.json` - Lex Stream export (current)
- `neuro_terms_v2.0.0_wikipedia-ninds.json` - Phase 1 versioned (649 terms)
- `neuro_terms_v3.0.0_umls.json` - Phase 2 UMLS (325K terms, 189 MB)
- `neuro_terms_original_515.csv` - Pre-expansion backup

**Letter Files**:
- `LetterFiles/[A-Z].csv` - Phase 1 letter-by-letter processing
- `LetterFiles_original_515/` - Original 515-term backup

**Source Glossaries**:
- `sources/Wikipedia-Glossary-of-Neuroscience.md` - Wikipedia source (595 terms)
- `sources/ninds-glossary-of-neurological-terms.md` - NINDS source (54 terms)

### Import Data
**Location**: `../imports/`

- `nif/` - NIF neuroanatomy (1,636 terms)
- `umls/` - UMLS Metathesaurus (325K terms)
  - `umls_neuroscience_terms.csv` (88 MB)
  - Phase 2A logs (import, mapping, merge, coverage)

### Validation Data
**Location**: `../validation/MeshValidation/`

- `mesh_corrections_log.json` - Master correction log
- `mesh_corrections_log.csv` - CSV format
- `mesh_corrections_summary.md` - Human-readable summary
- `archive/` - Historical validation reports

---

## POC Code Location

### API-First POC (Phase 5)
**Location**: `../poc-api-first/`

**Pipeline**:
- `poc_pipeline.py` - Main 5-layer pipeline
- `clients/pubtator.py` - PubTator 3.0 Autocomplete API
- `clients/umls.py` - UMLS Metathesaurus API
- `clients/pubmed.py` - PubMed E-utilities API
- `.env` - UMLS API key (not in git)

**Results**:
- `POC_RESULTS.md` - Comprehensive results
- `results/test_ms_neuromodulation.json` - Test case output

---

## Scripts Location

### Import Scripts
**Location**: `../scripts/`

**NIF**:
- `import_nif_neuroanatomy.py` - NIF TTL parser

**UMLS**:
- `import_umls_metathesaurus.py` - UMLS RRF parser
- `merge_umls_enrichments.py` - Phase 2A merge
- `compare_coverage.py` - Coverage analysis

**Export**:
- `convert_to_lexstream.py` - CSV → Lex Stream JSON (Phase 1)
- `convert_umls_to_lexstream.py` - UMLS CSV → Lex Stream JSON (Phase 2)

---

## Plans Location

### Root Plans
**Location**: `../plans/`

**Ontology Ingestion**:
- `2025-11-19-scalable-ontology-ingestion-with-source-control.md` - NIF plan
- `2025-11-20-umls-importer-implementation-plan.md` - UMLS plan
- `251121-umls-phase2a-synonym-abbreviation-expansion.md` - Phase 2A plan

**Implementation**:
- `implementation/` - Implementation artifacts
- `reports/` - Agent handoff reports
- `templates/` - Plan templates
- `diagrams/` - Architecture diagrams

### Docs Plans
**Location**: `docs/plans/`

**API-First POC**:
- `api-first-poc-detailed.md` - Detailed implementation plan
- `api-first-poc-summary.md` - Executive summary

### Research
**Location**: `../plans/research/`

**UMLS Research**:
- `251128-umls-semantic-types-pico-classification.md` - Semantic types analysis

---

## Quick Reference

### Understanding Current State (Dec 2025)
1. Read: `timeline/PROJECT_TIMELINE.md#phase-6`
2. Read: `../poc-api-first/POC_RESULTS.md`
3. Review: Hybrid architecture diagram (in timeline)

### Adding New Terms (Manual Workflow - Historical)
1. Read: `DATABASE_CREATION_GUIDE.md`
2. Read: `UPDATE_WORKFLOW.md`
3. Review: `mesh-validation-guide.md`

### Understanding UMLS Integration
1. Read: `UMLS_EXPLAINED.md` (primer)
2. Read: `decisions/ontology-import-tracker.md` (tracker)
3. Read: `UMLS_LEXSTREAM_INTEGRATION_SUMMARY.md` (summary)

### Understanding API-First Approach
1. Read: `../poc-api-first/POC_RESULTS.md` (results)
2. Read: `plans/api-first-poc-detailed.md` (implementation)
3. Review: PubTator/UMLS API docs (in POC code)

### Understanding Decisions
1. Read: `timeline/PROJECT_TIMELINE.md#key-decisions-log`
2. Deep dive: `decisions/` individual decision docs
3. Context: `decisions/ontology-import-tracker.md` (all DEC-001 to DEC-004)

---

## Frequently Asked Questions

### What's the current database version?
**Phase 1** (production): v2.0.0 - 649 terms, 42.7% synonyms, 22.2% abbreviations
**Phase 2** (experimental): v3.0.0 - 325K terms, 10% synonyms, 0.5% abbreviations
**Phase 6** (planned): Hybrid - Local + API (PubTator + UMLS)

### Why did we switch to API-first?
UMLS local database had low synonym/abbreviation coverage (10%/0.5% vs 42.7%/22.2% manual). PubTator API solves abbreviation disambiguation ("MS" → "Multiple Sclerosis"). UMLS API provides semantic classification (CONDITION, INTERVENTION). Hybrid approach combines local quality + API breadth.

### What happened to the 325K UMLS terms?
Still available in `data/neuro_terms_v3.0.0_umls.json` (189 MB). Used for spell checking and associations (90.4% coverage). Low synonym/abbreviation quality led to hybrid approach (API + selective local enrichment).

### What's the role of NeuroDB-2 in hybrid architecture?
**Layer 1**: Neuroscience-specific abbreviations (TMS, DBS, fMRI) not in PubTator
**Caching**: Common UMLS lookups (performance optimization)
**Quality**: High-quality synonyms (42.7% for 649 terms) for top terms

### Where are the validation logs?
`validation/MeshValidation/` - MeSH corrections (mesh-validator agent)
`archive/mesh_final_report.md` - Phase 1 final report
Dual validation: mesh-validator (NIH API) + neuro-reviewer (Gemini)

### How do I switch between database versions?
See Lex Stream: `DATABASE_TESTING.md` (symlink method)
v2.0.0: `neuro_terms_production.json` (649 terms)
v3.0.0: `neuro_terms_v3.0.0_umls.json` (325K terms)

---

## Contributing

### Updating Documentation
1. Update relevant docs in `docs/`
2. Update `timeline/PROJECT_TIMELINE.md` if major phase/decision
3. Follow existing structure (see templates in `../plans/templates/`)
4. Use git for version control (professional commits)

### Adding Decisions
1. Create `decisions/YYYY-MM-DD-decision-name.md`
2. Add to `decisions/ontology-import-tracker.md` (if ontology-related)
3. Add to `timeline/PROJECT_TIMELINE.md#key-decisions-log`
4. Use decision template (see existing DEC-001 to DEC-005)

### Creating Plans
1. Use templates in `../plans/templates/`
2. Save to `../plans/` (ontology) or `docs/plans/` (general)
3. Link from relevant docs (timeline, decisions, analysis)
4. Include: Objective, Approach, Outcomes, Files Created, Decision Docs

---

## Document Status
✅ **COMPLETE**
**Last Major Update**: Dec 3, 2025 (Phase 6 reorganization)
**Maintained By**: Engineering Team
**Review Frequency**: After each major phase/pivot

---

## Related Projects

### Lex Stream 2
**Location**: `../Lex-stream-2/`
**Docs**: `CLAUDE.md`, `README.md`, `DATABASE_TESTING.md`
**Purpose**: Neuroscience literature search (PubMed query expansion)
**Status**: Production deployed (Firebase + GCP Cloud Run)

### Integration
NeuroDB-2 → `convert_to_lexstream.py` → `neuro_terms.json` → Lex Stream agents
