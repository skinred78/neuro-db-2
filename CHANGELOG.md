# Changelog

All notable changes to the NeuroDB-2 Neuroscience Terminology Database will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2025-11-12

### Added
- 54 NINDS Glossary terms (32 unique, 22 enriched existing entries)
- Dual validation system: mesh-validator (NIH API) + neuro-reviewer (Gemini)
- Lex Stream JSON export format converter
- Comprehensive validation and testing suite
- MeSH correction tracking system (JSON, CSV, Markdown formats)
- ClaudeKit agent orchestration framework
- 25+ specialized skills (document handling, debugging, problem-solving)
- Complete project documentation suite

### Changed
- Unified schema to 22 columns across all letters (previously mixed 19-22)
- Enhanced MeSH coverage from ~85% to 88.4% (503/569 terms)
- Associated terms coverage increased to 94.7% (539/569 terms)
- Migrated MeSH validator from broken id.nlm.nih.gov to NCBI E-utilities API
- Improved data quality standards with stricter validation rules
- Enhanced abbreviation enrichment (126 unique abbreviations)

### Fixed
- MeSH validator API endpoint (NCBI E-utilities migration)
- Column count inconsistencies in letter files
- 32 MeSH term corrections (10 Phase 1, 22 Phase 2)
- 5 CSV rows with misaligned columns (documented, not critical)
- Null handling in CSV-to-JSON conversion process

### Database Statistics
- **Total Terms**: 569 (515 Wikipedia + 54 NINDS)
- **MeSH Terms**: 503 (88.4% coverage, API-validated)
- **Abbreviations**: 126 unique
- **Synonyms**: 243 terms (42.7% coverage)
- **Associated Terms**: 539 terms (94.7% coverage)
- **Word Forms**: 291 terms (51.1% coverage)
- **Avg Definition Length**: 153 characters

### Technical
- Export Format: Lex Stream-compatible JSON (428 KB)
- Schema: 22 columns unified
- Validation: Dual-agent (mesh-validator + neuro-reviewer)
- Backups: Created neuro_terms_original_515.csv, LetterFiles_original_515/

---

## [1.0.0] - 2025-10-27

### Added
- Initial database creation from Wikipedia Glossary of Neuroscience
- 515 neuroscience terms across letters A-Z
- MeSH validation system with NIH API integration
- 22-column schema with comprehensive field structure
- Individual letter files for data organization
- CSV and JSON export formats
- Basic project documentation (CLAUDE.md, SCHEMA_MIGRATION.md)

### Database Statistics
- **Total Terms**: 515 (Wikipedia only)
- **MeSH Terms**: ~435 (est. 85% coverage)
- **Schema**: 19-22 columns (mixed during creation process)
- **Coverage**: All letters A-Z complete

### Technical
- Source: Wikipedia Glossary of Neuroscience
- Validation: Single-agent MeSH validation
- Export Formats: CSV, JSON
- Schema Evolution: Letters B-F (19 cols), G-Z (22 cols)

---

## Version History Summary

| Version | Date | Terms | Sources | MeSH % | Notes |
|---------|------|-------|---------|--------|-------|
| 2.0.0 | 2025-11-12 | 569 | Wikipedia + NINDS | 88.4% | Dual validation, unified schema |
| 1.0.0 | 2025-10-27 | 515 | Wikipedia | ~85% | Initial release |

---

## Upcoming Changes

### Planned for v2.1.0
- Backfill letters B-F with additional associated terms (columns 6-8)
- Enrich high-traffic terms with additional synonyms
- Add full expansion for GABA abbreviation
- Cross-reference with existing Lex Stream database

### Considered for v3.0.0
- Third major data source (NCBI, UMLS, or similar)
- Relationship/ontology structure
- Citation tracking for definitions
- Multi-language support
- API endpoint for programmatic access

---

## Breaking Changes

None in v2.0.0. The release is backward compatible with v1.x for Lex Stream integration.

Future breaking changes will be clearly marked with **BREAKING CHANGE:** prefix.

---

## Migration Guides

### v1.0.0 → v2.0.0

**For Lex Stream Users**:
- ✅ No migration required (backward compatible)
- ✅ All v1 fields present in v2
- ✅ Additional fields enhance functionality but aren't required
- ℹ️ Update database path to `neuro_terms_v2.0.0_wikipedia-ninds.json`

**For Database Maintainers**:
- Schema now unified to 22 columns
- Dual validation required for new entries
- MeSH corrections must be tracked in MeshValidation/
- Follow new versioning conventions (see docs/VERSIONING_CONVENTIONS.md)

---

## Links

- [Versioning Conventions](docs/VERSIONING_CONVENTIONS.md)
- [Project Overview](docs/project-overview.md)
- [MeSH Validation Guide](docs/mesh-validation-guide.md)
- [Data Quality Standards](docs/data-quality-standards.md)
- [Lex Stream Integration Report](LEXSTREAM_INTEGRATION_REPORT.md)

---

**Maintained By**: NeuroDB-2 Project Team
**Last Updated**: 2025-11-12
