# Versioning & File Naming Conventions

**Project**: NeuroDB-2 Neuroscience Terminology Database
**Last Updated**: 2025-11-12

---

## Overview

This document defines how we version and name all database files, exports, and deliverables in the NeuroDB-2 project. Consistent versioning ensures clear provenance, enables rollback, and facilitates comparison between database versions.

---

## Semantic Versioning for Database Content

We use **semantic versioning** adapted for data/content projects:

```
v[MAJOR].[MINOR].[PATCH]
```

### Version Components

**MAJOR** - Incremented when:
- Adding a major new data source (e.g., Wikipedia → Wikipedia + NINDS)
- Significant schema changes (e.g., 19 columns → 22 columns)
- Breaking changes to data structure
- Fundamental changes in validation methodology

**MINOR** - Incremented when:
- Adding terms within existing sources
- Enriching existing terms (synonyms, associated terms, etc.)
- Schema additions that don't break compatibility
- MeSH term corrections or updates

**PATCH** - Incremented when:
- Bug fixes (typos, formatting errors)
- Data quality improvements (definition refinements)
- Metadata updates
- Non-breaking corrections

---

## File Naming Convention

### Export Files (JSON/CSV for Applications)

**Format**: `neuro_terms_v[MAJOR].[MINOR].[PATCH]_[SOURCE-TAG].[ext]`

**Examples**:
```
neuro_terms_v1.0.0_wikipedia.json      # Original Wikipedia only
neuro_terms_v2.0.0_wikipedia-ninds.json # Wikipedia + NINDS
neuro_terms_v2.1.0_wikipedia-ninds.json # Added more terms
neuro_terms_v2.0.1_wikipedia-ninds.json # Bug fix release
```

**Source Tags**:
- `wikipedia` - Wikipedia Glossary of Neuroscience only
- `ninds` - NINDS Glossary only
- `wikipedia-ninds` - Combined Wikipedia + NINDS
- `wikipedia-ninds-ncbi` - Future: if adding NCBI source
- `combined` - Multiple sources, if tag gets too long

### Working Files (Letter Files)

**Format**: `[LETTER].csv`

**Location**: `LetterFiles/`

**Examples**:
```
LetterFiles/A.csv
LetterFiles/B.csv
LetterFiles/Z.csv
```

**Versioning**: Working files don't have version numbers. Version is tracked through:
1. Git commits
2. Master database consolidation
3. Dated backups when needed

### Master Database Files

**Format**: `neuro_terms.csv` (always latest consolidated version)

**Version Tracking**:
- Current version tracked in `VERSION.txt`
- Git history provides version trail
- Dated backups created before major updates

### Backup Files

**Format**: `neuro_terms_[DESCRIPTION]_[YYYY-MM-DD].csv`

**Examples**:
```
neuro_terms_original_515.csv              # Pre-NINDS baseline
neuro_terms_backup_2025-11-12.csv         # Dated backup
neuro_terms_pre-merge_2025-11-12.csv      # Before merge operation
LetterFiles/A.csv.backup_20251112         # Letter file backup
```

### Validation Reports

**Format**: `[LETTER]_[SOURCE]_[TYPE]_report_[DATE].md`

**Examples**:
```
MeshValidation/A_NINDS_mesh_validation_report.md
MeshValidation/batch1_mesh_validation_report.md
```

### Script Output Files

**Format**: `[LETTER]_[SOURCE]_[STAGE].csv`

**Examples**:
```
scripts/output/A_NINDS_final.csv
scripts/output/B_NINDS_enriched.csv
scripts/archive/A_NINDS_enriched_final_20251112.csv
```

---

## Version History

### v2.0.0 (2025-11-12)
**Tag**: `wikipedia-ninds`
**Terms**: 569
**Sources**: Wikipedia Glossary + NINDS Glossary
**Changes**:
- Added 54 NINDS terms (32 unique, 22 enriched existing)
- Enhanced validation (dual agent system)
- MeSH coverage: 88.4% (503/569 terms)
- Schema: 22 columns

### v1.0.0 (2025-10-27)
**Tag**: `wikipedia`
**Terms**: 515
**Sources**: Wikipedia Glossary of Neuroscience
**Changes**:
- Initial database creation
- Letters A-Z complete
- MeSH validation system established
- Schema: 19-22 columns (mixed during creation)

---

## Version Tracking Files

### VERSION.txt

Location: Project root

```
2.0.0
```

Simple text file containing current semantic version.

### CHANGELOG.md

Location: Project root

Detailed changelog following [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

All notable changes to the NeuroDB-2 database will be documented in this file.

## [2.0.0] - 2025-11-12

### Added
- 54 NINDS Glossary terms
- Dual validation system (mesh-validator + neuro-reviewer)
- Enhanced MeSH coverage (88.4%)

### Changed
- Unified schema to 22 columns across all letters
- Improved associated terms coverage (94.7%)

### Fixed
- MeSH validator API endpoint (migrated to NCBI E-utilities)
```

---

## Git Tagging Convention

**Format**: `v[MAJOR].[MINOR].[PATCH]`

**Examples**:
```bash
git tag v1.0.0 685fbca  # Initial Wikipedia release
git tag v2.0.0 476e9a0  # Wikipedia + NINDS release
git push origin v2.0.0
```

**Tag Message Format**:
```bash
git tag -a v2.0.0 -m "Release v2.0.0: Wikipedia + NINDS (569 terms)

- Added 54 NINDS terms
- MeSH coverage: 88.4%
- Schema: 22 columns unified
- Dual validation system"
```

---

## Release Process

When creating a new version:

### 1. Update Version Files
```bash
# Update VERSION.txt
echo "2.0.0" > VERSION.txt

# Update CHANGELOG.md
# Add new version section with changes
```

### 2. Create Versioned Export
```bash
# Generate export with version in filename
python convert_to_lexstream.py  # outputs to versioned filename
mv neuro_terms_wikipedia.json neuro_terms_v2.0.0_wikipedia-ninds.json
```

### 3. Commit and Tag
```bash
git add VERSION.txt CHANGELOG.md neuro_terms_v2.0.0_wikipedia-ninds.json
git commit -m "Release v2.0.0: Wikipedia + NINDS (569 terms)"
git tag -a v2.0.0 -m "Release v2.0.0"
git push origin main --tags
```

### 4. Create Backup
```bash
# Backup master CSV before next work begins
cp neuro_terms.csv "neuro_terms_backup_$(date +%Y-%m-%d).csv"
```

---

## Version Compatibility

### Schema Compatibility

| Version | Columns | Compatible With |
|---------|---------|-----------------|
| v1.x | 19-22 (mixed) | Lex Stream v1.x |
| v2.x | 22 (unified) | Lex Stream v2.x |

### Breaking Changes

**v1.x → v2.x**:
- ✅ Non-breaking for Lex Stream (all v1 fields present)
- ✅ Backward compatible (can read v1 format)
- ⚠ Letters B-F backfill needed for full 22-column consistency

**Future v2.x → v3.x**:
- Would need migration guide if schema changes
- Document in CHANGELOG.md under "BREAKING CHANGES"

---

## Quick Reference

### Current Version
```
v2.0.0 (wikipedia-ninds, 569 terms, 22 columns)
```

### Current Export Filename
```
neuro_terms_v2.0.0_wikipedia-ninds.json
```

### Current Master Database
```
neuro_terms.csv (no version in filename, tracks latest)
```

### How to Check Version
```bash
cat VERSION.txt
# or
head -n 1 CHANGELOG.md | grep -oE '[0-9]+\.[0-9]+\.[0-9]+'
# or
git describe --tags
```

---

## Best Practices

1. **Always update VERSION.txt and CHANGELOG.md together**
2. **Create dated backups before major changes**
3. **Use descriptive git commit messages with version context**
4. **Tag all releases in git**
5. **Include version in export filenames for Lex Stream integration**
6. **Document breaking changes prominently**
7. **Keep version trail clear for rollback capability**

---

## Future Considerations

### Potential Version 3.0 Triggers

- Adding third major data source (NCBI, UMLS, etc.)
- Major schema redesign
- Multi-language support
- Relationship/ontology structure additions
- API endpoint integration

### Date-Based Snapshots

For long-term archival, consider date-based snapshots:
```
archives/neuro_terms_2025-11-12_v2.0.0_wikipedia-ninds.json
```

---

## Questions & Updates

When version conventions need updating:
1. Propose changes in this document
2. Discuss with team/maintainers
3. Update examples and references
4. Document in CHANGELOG.md
5. Communicate to Lex Stream integration team

---

**Last Updated**: 2025-11-12
**Document Version**: 1.0
**Maintained By**: NeuroDB-2 Project Team
