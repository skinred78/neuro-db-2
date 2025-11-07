# NeuroDB-2: Neuroscience Terminology Database

**Version**: 2.0
**Status**: Active Development (Letters G-Z in progress)
**Last Updated**: 2025-11-07

## Executive Summary

NeuroDB-2 is a comprehensive neuroscience terminology database project that creates a validated, structured repository of neuroscience terms with their definitions, synonyms, abbreviations, word forms, and MeSH (Medical Subject Headings) classifications. The database serves as an authoritative reference for neuroscience research, education, and clinical applications.

## Project Goals

### Primary Objectives
1. Create comprehensive database of neuroscience terminology (A-Z)
2. Validate all MeSH terms against official NIH API
3. Enrich terminology with accurate synonyms, abbreviations, and word forms
4. Maintain high data quality through dual AI-powered validation
5. Provide structured export formats (CSV, JSON) for research applications

### Success Metrics
- Complete coverage of Wikipedia Glossary of Neuroscience terms (A-Z)
- 100% MeSH validation accuracy via NIH API
- Zero fabricated data (accuracy over completeness)
- Dual validation pass rate for all letter files
- Comprehensive validation logging and audit trails

## Data Sources

### Primary Source
**Wikipedia Glossary of Neuroscience**
- File: `Wikipedia-Glossary-of-Neuroscience.md`
- Content: Term names and definitions
- Source: Community-curated neuroscience glossary
- Status: Complete reference data for letters A-Z

### Validation Sources
**NIH MeSH Database**
- API: https://id.nlm.nih.gov/mesh/
- Purpose: Authoritative MeSH term verification
- Usage: Validates "Closest MeSH term" field via mesh-validator agent

**Google Gemini CLI**
- Purpose: Cross-validation of definitions, synonyms, word forms
- Usage: Validates all fields except MeSH terms via neuro-reviewer agent

## Database Schema

### Core Structure
22 columns per term (expanded from original 19 columns):

**Identity Fields**
- `Term` - Primary neuroscience term
- `Term Two` - ASCII-safe alternate representation (special characters removed)

**Definition**
- `Definition` - Complete definition from Wikipedia

**MeSH Classification**
- `Closest MeSH term` - Exact official MeSH database entry (API-validated)

**Synonyms & Abbreviations**
- `Synonym 1`, `Synonym 2`, `Synonym 3` - Alternative names (NOT abbreviations)
- `Abbreviation` - Standard abbreviated forms (e.g., BBB, BDNF, BCI)

**Spelling Variants**
- `UK Spelling` - British English variant
- `US Spelling` - American English variant

**Word Forms**
- `Noun Form of Word`
- `Verb Form of Word`
- `Adjective Form of Word`
- `Adverb Form of Word`

**Related Terms**
- `Commonly Associated Term 1` through `Commonly Associated Term 8`
- 1-8 related neuroscience concepts (as appropriate, not mandatory to fill all)

### Schema Evolution
- **Letters B-F**: 19 columns (5 associated terms)
- **Letters G-Z**: 22 columns (8 associated terms)
- **Backfill Plan**: Add 3 columns to B-F after completing G-Z

## Validation System

### Dual Validation Architecture

**Stage 1: Parallel Validation**
- **mesh-validator** - API-based MeSH validation (authoritative)
  - Validates only "Closest MeSH term" field
  - Uses official NIH MeSH API
  - Fast execution (API responses in milliseconds)
  - Final authority on MeSH terms

- **neuro-reviewer** - Gemini-based validation
  - Validates ALL fields EXCEPT "Closest MeSH term"
  - Cross-checks definitions, synonyms, abbreviations, word forms
  - Identifies misclassifications and errors
  - Provides recommendations

**Stage 2: Correction & Re-validation**
- Apply corrections from both agents in single batch
- Update MeSH correction tracking files (if MeSH changes made)
- Re-run ONLY failed agent(s) on corrected items (targeted validation)
- Proceed to human review only after both agents pass

### Validation Artifacts

**MeSH Correction Tracking**
```
MeshValidation/
├── mesh_corrections_log.json      # Master log by letter
├── mesh_corrections_log.csv       # Spreadsheet format
├── mesh_corrections_summary.md    # Human-readable summary
└── archive/                       # Historical validation reports
```

## Development Progress

### Completed (Letters A-X)
- **Letter A**: 32 terms (placeholder/example data)
- **Letters B-X**: ~500 validated terms across 23 letter files
- All completed letters validated via dual validation
- MeSH corrections tracked and applied

### In Progress (Letters Y-Z)
- Remaining letters to complete database
- Using full 22-column schema
- Dual validation workflow established

### Backfill Phase (Planned)
- Add 3 columns to letters B-F (19 → 22 columns)
- Optional enrichment with additional associated terms

### Final Consolidation
- Merge all letter files → `neuro_terms.csv`
- Export to JSON → `neuro_terms.json`
- Quality assurance report

## File Organization

```
NeuroDB-2/
├── Wikipedia-Glossary-of-Neuroscience.md   # Source data
├── LetterFiles/                            # Individual letter CSVs
│   ├── A.csv, B.csv, ... X.csv            # Validated terms by letter
│   └── [Y.csv, Z.csv]                     # In progress
├── MeshValidation/                         # Validation tracking
│   ├── mesh_corrections_log.json
│   ├── mesh_corrections_log.csv
│   ├── mesh_corrections_summary.md
│   └── archive/                           # Historical reports
├── neuro_terms.csv                         # Master database (consolidated)
├── neuro_terms.json                        # JSON export
├── CLAUDE.md                               # Project instructions
├── SCHEMA_MIGRATION.md                     # Schema evolution notes
└── docs/                                   # Project documentation
    ├── project-overview.md                # This file
    ├── mesh-validation-guide.md           # MeSH validation details
    ├── data-quality-standards.md          # Data quality guidelines
    └── agent-orchestration.md             # Dual validation workflow
```

## Technology Stack

### Core Tools
- **Python CSV module** - CSV file generation with proper quoting
- **Bash scripting** - Automation and file operations
- **NIH MeSH API** - MeSH term validation
- **Google Gemini CLI** - Cross-validation via AI

### AI Agent Framework (ClaudeKit)
- **mesh-validator** - Domain-specific MeSH validation agent
- **neuro-reviewer** - Domain-specific neuroscience data review agent
- **General agents** - Planner, researcher, tester, code-reviewer, etc.
- **Orchestration** - Parallel execution for independent validations

## Data Quality Principles

### Accuracy Over Completeness
- NEVER fabricate or guess information
- Leave fields empty if no reliable data available
- Verify all MeSH terms via API (no exceptions)
- Cross-validate definitions and synonyms

### Validation Requirements
- Both agents (mesh-validator + neuro-reviewer) must pass
- MeSH terms must match official NIH database exactly
- Definitions must be accurate per source material
- Synonyms must be true alternatives (not abbreviations)
- Associated terms must be relevant to neuroscience domain

### Audit Trail
- All MeSH corrections logged in 3 formats (JSON, CSV, Markdown)
- Validation reports archived for historical reference
- Human review required before final approval of each letter

## Use Cases

### Research Applications
- Term standardization across neuroscience papers
- Automated term extraction and classification
- Cross-referencing with MeSH-indexed literature
- Building neuroscience knowledge graphs

### Educational Applications
- Neuroscience terminology reference
- Study aids with definitions and related terms
- Synonym and abbreviation lookup
- Word form variations for writing

### Clinical Applications
- Medical terminology standardization
- EHR (Electronic Health Record) integration
- Clinical decision support systems
- Medical coding and billing

## Future Enhancements

### Potential Additions
- Additional associated terms for letters B-F (backfill)
- Cross-references between related terms
- Citations for definitions
- Multi-language support (translations)
- API endpoint for programmatic access
- Web interface for browsing and searching

### Integration Opportunities
- Link to PubMed literature via MeSH terms
- Connect to neuroscience ontologies (e.g., NeuroLex)
- Integration with neuroscience research databases
- Export to RDF/OWL for semantic web applications

## Contributing Guidelines

### Adding New Terms
1. Extract term and definition from source (Wikipedia Glossary)
2. Enrich with verifiable data (synonyms, MeSH, word forms)
3. Run dual validation (mesh-validator + neuro-reviewer in parallel)
4. Apply corrections from validation reports
5. Re-validate targeted corrections (not full re-review)
6. Submit for human review
7. Save approved data to letter file

### Modifying Existing Terms
1. Document reason for modification
2. Update relevant fields with verified information
3. Re-run dual validation
4. Update MeSH correction logs if MeSH term changed
5. Human review of modifications

## License & Attribution

- **Source Data**: Wikipedia Glossary of Neuroscience (CC BY-SA license)
- **MeSH Terms**: NIH National Library of Medicine (public domain)
- **Database Compilation**: Original work for research and educational purposes

## Project Status

**Current Phase**: Data Collection (Letters G-Z)
**Completion**: ~87% (23 of 26 letters complete)
**Next Milestone**: Complete letters Y-Z
**Final Goal**: Consolidated validated database with JSON export

---

For detailed implementation instructions, see `CLAUDE.md` in the project root.
