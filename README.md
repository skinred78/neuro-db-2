# NeuroDB-2: Neuroscience Terminology Database Pipeline

Data processing and validation pipeline for neuroscience terminology sources, powering the **[Lex Stream](../Lex-stream-2)** query expansion system.

## Overview

NeuroDB-2 ingests, enriches, validates, and exports neuroscience terminology from authoritative sources (Wikipedia, NINDS, UMLS Metathesaurus) into a structured JSON database consumed by Lex Stream's agentic workflow pipeline.

## Current Database

**Version**: v2.0.0
**File**: `neuro_terms_v2.0.0_wikipedia-ninds.json` (427.7 KB)

### Statistics
- **Total Terms**: 569
- **Abbreviations**: 126
- **MeSH Terms**: 412 (88.4% coverage)
- **Synonyms**: 243 terms (42.7%)
- **Associated Terms**: 539 terms (94.7%)

### Sources
- ✅ Wikipedia Glossary of Neuroscience (515 terms)
- ✅ NINDS Glossary (54 terms)
- ⏳ UMLS Metathesaurus (license applied, pending integration)

## Integration with Lex Stream

**Purpose**: This database powers Lex Stream's query expansion features:
- Abbreviation expansion (TMS → Transcranial magnetic stimulation)
- Synonym finding (memory → recall, recognition)
- MeSH term detection (Acetylcholine → [MeSH] tag)
- Spell checking (alzhimers → Alzheimer's)
- Component categorization (TMS → Intervention)

**Integration Status**: ✅ Production-ready (95% test pass rate)
**Integration Report**: [LEXSTREAM_INTEGRATION_REPORT.md](LEXSTREAM_INTEGRATION_REPORT.md)

## Data Processing Pipeline

```
1. Source Ingestion
   └─> Wikipedia-Glossary-of-Neuroscience.md
   └─> ninds-glossary-of-neurological-terms.md
   └─> (future: UMLS Metathesaurus)
         ↓
2. AI Enrichment
   └─> Synonyms, abbreviations, word forms, associated terms
         ↓
3. Dual Validation
   ├─> mesh-validator (NIH MeSH API)
   └─> neuro-reviewer (Gemini CLI)
         ↓
4. Export to Lex Stream
   └─> neuro_terms.json
```

## Key Files

- **Master Database**: `neuro_terms.csv` (consolidated CSV format)
- **Lex Stream Export**: `neuro_terms_v2.0.0_wikipedia-ninds.json` (JSON format)
- **Letter Files**: `A.csv`, `B.csv`, ..., `Z.csv` (working files during term collection)
- **Validation Reports**: `MeshValidation/` (MeSH corrections, validation logs)
- **Conversion Script**: `convert_to_lexstream.py` (CSV → JSON export)
- **Test Scripts**: `validate_lexstream_db.py`, `test_lexstream_db.py`

## Data Schema

**CSV Format** (22 columns):
- Term, Term Two (ASCII-safe variant)
- Definition
- Closest MeSH term
- Synonym 1-3
- Abbreviation
- UK/US Spelling
- Word Forms (noun, verb, adjective, adverb)
- Commonly Associated Term 1-8

**JSON Format** (Lex Stream):
```json
{
  "terms": { "term_key": { /* term data */ } },
  "abbreviations": { "abbr_key": { /* expansion */ } },
  "mesh_terms": { "mesh_key": "MeSH Term" },
  "metadata": { /* version, counts, sources */ }
}
```

## Workflows

### 1. Adding New Terms (Letters B-Z)
```bash
# See CLAUDE.md for complete 5-step workflow
# 1. Extract from Wikipedia source
# 2. AI enrichment
# 3. Dual validation (mesh-validator + neuro-reviewer)
# 4. Human review
# 5. Save to letter file (e.g., F.csv)
```

### 2. Merging Letter Files
```bash
# Consolidate all letter CSV files into master database
# See CLAUDE.md Workflow 2
```

### 3. Generating JSON Export
```bash
# Convert master CSV to Lex Stream JSON format
python convert_to_lexstream.py

# Validate output
python validate_lexstream_db.py

# Test against Lex Stream agents
python test_lexstream_db.py
```

### 4. Exporting to Lex Stream
```bash
# Use automated pipeline script
./scripts/export_to_lexstream.sh

# Manual copy (development)
cp neuro_terms_v2.0.0_wikipedia-ninds.json ../Lex-stream-2/neuro_terms.json
```

## Update Frequency

**Current Phase** (Development):
- Frequent updates as needed (implementing MeSH hierarchy trees)
- Manual testing after each update
- Rapid iteration on data enrichment

**Future Phase** (Production):
- Monthly or less frequent updates
- Scheduled release cycles
- Automated testing/validation
- Semantic versioning

## Validation

All terms undergo dual validation:

1. **mesh-validator** (NIH MeSH API):
   - Validates "Closest MeSH term" field
   - API-authoritative verification
   - Tracks corrections in `MeshValidation/`

2. **neuro-reviewer** (Gemini CLI):
   - Validates all other fields
   - Cross-checks definitions, synonyms, associated terms
   - Reports errors and recommendations

**MeSH Corrections**: All MeSH corrections logged in:
- `MeshValidation/mesh_corrections_log.json`
- `MeshValidation/mesh_corrections_log.csv`
- `MeshValidation/mesh_corrections_summary.md`

## Version Control

**Semantic Versioning**: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking schema changes, source migrations
- **MINOR**: New sources added (NINDS, UMLS)
- **PATCH**: Term corrections, enrichments

**Current Version**: 2.0.0
**Version File**: `VERSION.txt`
**Changelog**: `CHANGELOG.md`
**Versioning Guide**: `docs/VERSIONING_CONVENTIONS.md`

## ClaudeKit Integration

This project uses ClaudeKit framework with specialized agents:

**Domain-Specific Agents**:
- **mesh-validator**: Validates MeSH terms against NIH API
- **neuro-reviewer**: Reviews neuroscience terminology data via Gemini CLI

**General Development Agents**:
- planner, researcher, tester, debugger, code-reviewer, docs-manager, git-manager, project-manager

See `CLAUDE.md` for complete agent orchestration protocols.

## Next Steps

### Current Priority: MeSH Hierarchy Trees
Based on neuroscientist feedback, implementing hierarchical term relationships:
- MeSH tree numbers (e.g., C10.228.140.079.862.500)
- Parent/child relationships
- Sibling terms
- Semantic context for component detection

See: `docs/analysis/20251117-neuroscientist-feedback-expansion-trees.md` (Lex Stream repo)

### Future Enhancements
- ⏳ UMLS Metathesaurus integration (license pending)
- ⏳ MeSH hierarchy tree implementation
- ⏳ Automated export pipeline
- ⏳ Expanded synonym coverage
- ⏳ Word form enrichment

## Documentation

- **Project Constitution**: `CLAUDE.md`
- **Integration Report**: `LEXSTREAM_INTEGRATION_REPORT.md`
- **Versioning Guide**: `docs/VERSIONING_CONVENTIONS.md`
- **Schema Migration**: `SCHEMA_MIGRATION.md`
- **MeSH Validation**: `MeshValidation/` directory

## Contributing

See `CLAUDE.md` for:
- Development principles (YANGI, KISS, DRY)
- Data quality standards
- Git workflow
- Agent orchestration patterns

## License

[Add license information]

## Support

For questions or issues:
1. Review `CLAUDE.md` for project background
2. Check `LEXSTREAM_INTEGRATION_REPORT.md` for integration status
3. Review validation logs in `MeshValidation/`
4. Open issue on GitHub

---

**Powering Lex Stream's intelligent query expansion for neuroscience literature search.**
