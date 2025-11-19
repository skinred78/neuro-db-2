# Versioning System - Quick Reference

**Current Version**: 2.0.0
**Current Database**: `neuro_terms_v2.0.0_wikipedia-ninds.json`
**Last Updated**: 2025-11-12

---

## Key Files

| File | Purpose |
|------|---------|
| `VERSION.txt` | Current version number (2.0.0) |
| `CHANGELOG.md` | Complete version history with all changes |
| `docs/VERSIONING_CONVENTIONS.md` | Full versioning standards and guidelines |
| `neuro_terms_v2.0.0_wikipedia-ninds.json` | Production database (versioned filename) |

---

## File Naming Convention

### Pattern
```
neuro_terms_v[MAJOR].[MINOR].[PATCH]_[source-tag].[ext]
```

### Examples
```
neuro_terms_v1.0.0_wikipedia.json          # v1: Wikipedia only (515 terms)
neuro_terms_v2.0.0_wikipedia-ninds.json    # v2: Wikipedia + NINDS (569 terms)
neuro_terms_v2.1.0_wikipedia-ninds.json    # v2.1: Future additions
```

---

## Semantic Versioning

**MAJOR** (x.0.0) - Breaking changes:
- Adding new major data source
- Schema restructuring
- Breaking API changes

**MINOR** (2.x.0) - New features:
- Adding terms within existing sources
- New fields/columns (backward compatible)
- Enrichment of existing terms

**PATCH** (2.0.x) - Bug fixes:
- Typo corrections
- Definition improvements
- Metadata updates

---

## Quick Commands

### Check Current Version
```bash
cat VERSION.txt
# Output: 2.0.0
```

### View Recent Changes
```bash
head -50 CHANGELOG.md
```

### Run Conversion (auto-versioned output)
```bash
python3 convert_to_lexstream.py
# Output: neuro_terms_v2.0.0_wikipedia-ninds.json
```

### Validate Database
```bash
python3 validate_lexstream_db.py
# Auto-finds versioned file from VERSION.txt
```

### Test Database
```bash
python3 test_lexstream_db.py
# Auto-finds versioned file from VERSION.txt
```

---

## Version History

| Version | Date | Terms | Sources | Key Changes |
|---------|------|-------|---------|-------------|
| 2.0.0 | 2025-11-12 | 569 | Wikipedia + NINDS | Added NINDS, dual validation, unified schema |
| 1.0.0 | 2025-10-27 | 515 | Wikipedia | Initial release |

---

## For Lex Stream Integration

### Current Production File
```
neuro_terms_v2.0.0_wikipedia-ninds.json
```

### Update Lex Stream Config
```python
# In services/terms_loader.py
DATABASE_PATH = "neuro_terms_v2.0.0_wikipedia-ninds.json"
```

### Symlink Strategy (Optional)
```bash
# Create symlink for easy version updates
ln -s neuro_terms_v2.0.0_wikipedia-ninds.json neuro_terms.json

# In Lex Stream config
DATABASE_PATH = "neuro_terms.json"  # Points to symlink

# When updating to v2.1.0, just update symlink:
ln -sf neuro_terms_v2.1.0_wikipedia-ninds.json neuro_terms.json
```

---

## Creating a New Version

### 1. Update Version Files
```bash
echo "2.1.0" > VERSION.txt
# Add entry to CHANGELOG.md
```

### 2. Generate Export
```bash
python3 convert_to_lexstream.py
# Automatically creates: neuro_terms_v2.1.0_wikipedia-ninds.json
```

### 3. Git Tag
```bash
git add VERSION.txt CHANGELOG.md neuro_terms_v2.1.0_wikipedia-ninds.json
git commit -m "Release v2.1.0: [description]"
git tag -a v2.1.0 -m "Release v2.1.0"
git push origin main --tags
```

---

## Documentation

- **Full Versioning Guide**: `docs/VERSIONING_CONVENTIONS.md`
- **Complete Changelog**: `CHANGELOG.md`
- **Integration Guide**: `LEXSTREAM_INTEGRATION_REPORT.md`
- **Project Overview**: `docs/project-overview.md`

---

## Best Practices

✅ **DO**:
- Always update VERSION.txt and CHANGELOG.md together
- Use versioned filenames for all exports
- Document breaking changes prominently
- Create backups before major updates
- Tag releases in git

❌ **DON'T**:
- Change version numbers without updating CHANGELOG
- Skip version numbers (e.g., 2.0.0 → 2.2.0)
- Use generic filenames for production exports
- Forget to update documentation

---

**For Questions**: See `docs/VERSIONING_CONVENTIONS.md` for complete details.
