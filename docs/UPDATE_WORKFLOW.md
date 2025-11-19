# Database Update Workflow & Frequency Guide

**Last Updated**: 2025-11-18
**Context**: Lex Stream neuroscience terminology database maintenance

---

## Update Frequency Overview

### Current Phase: Development (Now - Next 2-3 Months)

**Frequency**: **Frequent, ad-hoc updates** (multiple times per week)

**Why**:
- Implementing MeSH hierarchy trees (neuroscientist feedback priority)
- Integrating UMLS Metathesaurus (license approved)
- Rapid iteration on data enrichment quality
- Testing hierarchy-aware query expansion
- Expanding term coverage (569 → target: 2000+ terms)

**Characteristics**:
- No fixed schedule (as needed for development)
- Immediate export after validation passes
- Quick validation cycles (minutes, not hours)
- Frequent Lex Stream integration testing
- Incremental improvements

**Impact**: This requires **lightweight automation** that supports manual triggering, not scheduled cron jobs.

---

### Future Phase: Production (3+ Months from Now)

**Frequency**: **Monthly or less** (scheduled releases)

**Why**:
- Stable feature set (hierarchy trees implemented)
- UMLS integrated and validated
- Mature quality assurance processes
- Predictable release cycles for Lex Stream

**Characteristics**:
- Scheduled release dates (1st of month, quarterly, etc.)
- Comprehensive validation (days, not minutes)
- Batch updates from multiple sources
- Coordinated deployment with Lex Stream updates
- Semantic versioning (MAJOR.MINOR.PATCH)

**Impact**: This will need **scheduled automation** (cron jobs, CI/CD pipelines, release management).

---

## Workflow Recommendations by Phase

### Development Phase Workflow

**Update Trigger**: When implementing features or fixing issues

**Process**:
```bash
# 1. Make changes to data (add terms, enrich hierarchy metadata)
cd /Users/sam/NeuroDB-2
vim neuro_terms.csv   # or use scripts to enrich

# 2. Convert to JSON
python3 convert_to_lexstream.py

# 3. Validate & export (automated script)
./scripts/export_to_lexstream.sh

# 4. Test in Lex Stream
cd /Users/sam/Lex-stream-2
python3 app.py
# Manual testing: Open browser, test queries

# 5. If tests pass, commit both repos
cd /Users/sam/NeuroDB-2
git add . && git commit -m "feat: add hierarchy tree metadata for neurodegeneration terms"
cd /Users/sam/Lex-stream-2
git add neuro_terms.json DB_VERSION.txt
git commit -m "chore: update terminology database to v2.1.0"
```

**Validation Level**: **Fast validation** (< 5 minutes)
- Structure validation (required sections, key formats)
- Basic functional tests (abbreviation expansion, MeSH detection)
- Skip comprehensive integration tests

**Automation**: Manual trigger (`./scripts/export_to_lexstream.sh`)

---

### Production Phase Workflow

**Update Trigger**: Scheduled release date (e.g., 1st of month)

**Process**:
```bash
# 1. Batch updates from sources (UMLS, Wikipedia, NINDS)
cd /Users/sam/NeuroDB-2
./scripts/update_from_sources.sh   # Future script

# 2. Comprehensive validation
python3 validate_lexstream_db.py
python3 test_lexstream_db.py

# 3. Create release candidate
./scripts/create_release.sh v2.5.0   # Future script
# - Updates VERSION.txt
# - Updates CHANGELOG.md
# - Exports to Lex Stream staging

# 4. Integration testing (Lex Stream staging)
cd /Users/sam/Lex-stream-2
python3 -m pytest tests/ --full
npm run test:e2e

# 5. If all tests pass, promote to production
cd /Users/sam/NeuroDB-2
git tag v2.5.0
git push origin v2.5.0

# 6. Deploy to Lex Stream production
cd /Users/sam/Lex-stream-2
./deploy.sh production   # Future script
```

**Validation Level**: **Comprehensive validation** (hours to days)
- Full test suite (unit, integration, E2E)
- Manual quality review by neuroscientist
- Performance benchmarks
- Regression testing

**Automation**: Scheduled CI/CD pipeline (GitHub Actions, cron)

---

## What "No Set Schedule" Means for Implementation

### 1. **Automation Design**

**Development Phase** (now):
- ✅ Manual trigger scripts (like `export_to_lexstream.sh`)
- ✅ Quick validation (< 5 min)
- ✅ Lightweight logs (timestamped files in `scripts/output/`)
- ❌ No scheduled cron jobs
- ❌ No complex CI/CD pipelines

**Production Phase** (later):
- ✅ Scheduled automation (monthly cron, GitHub Actions)
- ✅ Comprehensive validation (full test suite)
- ✅ Release management (tags, changelogs, deployment)
- ✅ Slack/email notifications on completion

**Implication**: Build simple manual scripts now, add scheduling later.

---

### 2. **Testing Strategy**

**Development Phase**:
- **Fast feedback loop**: Validate structure + basic function tests only
- **Manual testing**: Query a few terms in Lex Stream UI
- **Acceptable failure rate**: Can export with warnings (review later)

**Production Phase**:
- **Zero-defect requirement**: All tests must pass
- **Automated regression tests**: Compare query expansion quality before/after
- **Performance benchmarks**: Query generation time, synonym coverage
- **Breaking change detection**: Schema compatibility checks

**Implication**: Don't build comprehensive test suite yet. Focus on fast validation now, expand tests as you approach production.

---

### 3. **Version Control**

**Development Phase**:
- **Frequent minor bumps**: v2.0.0 → v2.1.0 → v2.2.0 (weekly)
- **No strict semver**: Can break schema during active development
- **Changelog**: Simple bullets in CHANGELOG.md

**Production Phase**:
- **Semantic versioning**: MAJOR.MINOR.PATCH (strict)
- **Git tags**: Every release gets a tag (v2.5.0)
- **Changelog**: Structured (Added, Changed, Fixed, Breaking Changes)
- **Release notes**: User-facing documentation

**Implication**: Use simple version bumps now (increment VERSION.txt). Implement strict semver before production release.

---

### 4. **Coordination with Lex Stream**

**Development Phase**:
- **Loose coupling**: NeuroDB-2 updates don't require Lex Stream deployment
- **Immediate integration**: Export → test locally → commit both repos
- **No staging environment**: Test on localhost

**Production Phase**:
- **Tight coordination**: Scheduled releases align with Lex Stream sprints
- **Staging environment**: Test in staging before production
- **Rollback plan**: Database versioning allows reverting to previous version

**Implication**: Simple local testing now. Set up staging/production environments before monthly releases.

---

### 5. **Data Source Updates**

**Development Phase** (hierarchy trees, UMLS):
- **Manual ingestion**: Run scripts to import new sources
- **Incremental addition**: Add 50-100 terms at a time
- **Quality over quantity**: Validate deeply, expand slowly

**Production Phase** (mature database):
- **Automated ingestion**: Scheduled pulls from UMLS API, Wikipedia updates
- **Batch processing**: Add 500-1000 terms per release
- **Automated quality checks**: Flag low-quality terms for review

**Implication**: Build manual ingestion scripts now (already have Wikipedia, NINDS). Add UMLS automation after integration.

---

## Recommended Immediate Actions

### 1. ✅ **Export Automation** (DONE)
Created `scripts/export_to_lexstream.sh`:
- Validates database structure
- Runs functional tests
- Copies to Lex Stream
- Updates version tracking
- Creates export log

**Usage**:
```bash
cd /Users/sam/NeuroDB-2
./scripts/export_to_lexstream.sh          # Full validation + tests
./scripts/export_to_lexstream.sh --skip-tests  # Fast export (dev only)
```

### 2. ⏳ **Quick Validation Script** (Future)
Create `scripts/quick_validate.sh`:
- Structure checks only (< 30 seconds)
- Skip comprehensive tests
- Use during rapid iteration

**When**: Create when you're updating multiple times per day

### 3. ⏳ **UMLS Ingestion Script** (Priority: After license approval)
Create `scripts/import_umls.sh`:
- Pull terms from UMLS Metathesaurus
- Map to NeuroDB-2 schema
- Merge with existing database
- Flag duplicates for review

**When**: After UMLS license arrives

### 4. ⏳ **Hierarchy Tree Enrichment** (Priority: Immediate)
Create `scripts/enrich_mesh_hierarchy.sh`:
- Query NIH MeSH API for tree numbers
- Add parent/child relationships
- Augment `neuro_terms.json` with hierarchy metadata
- See neuroscientist feedback: `docs/analysis/20251117-neuroscientist-feedback-expansion-trees.md` (Lex Stream)

**When**: Start now (neuroscientist's #1 priority)

---

## Transition to Production Checklist

When update frequency stabilizes (monthly), implement:

### Automation
- [ ] GitHub Actions workflow for scheduled releases
- [ ] Automated changelog generation
- [ ] Slack/email notifications
- [ ] Rollback automation

### Testing
- [ ] Comprehensive test suite (100+ tests)
- [ ] Performance benchmarks
- [ ] Regression test comparison
- [ ] E2E tests with Lex Stream

### Release Management
- [ ] Strict semantic versioning
- [ ] Git tags for all releases
- [ ] Release notes template
- [ ] Staging environment setup

### Documentation
- [ ] User-facing changelog
- [ ] Data provenance tracking
- [ ] Quality metrics dashboard
- [ ] Update schedule published

---

## Summary

**Current Priority**: **Fast iteration, not scheduled releases**

**Key Insight**: "No set schedule but frequent updates" means:
1. Build **manual trigger automation** (not cron jobs)
2. **Quick validation** (< 5 min), skip comprehensive tests
3. **Immediate export** after changes (same day, not batched)
4. **Local testing** (no staging environment yet)
5. **Simple versioning** (increment VERSION.txt, no strict semver)

**Next Phase**: When updates slow to monthly, add:
1. **Scheduled automation** (GitHub Actions, cron)
2. **Comprehensive testing** (full suite, benchmarks)
3. **Release management** (tags, changelogs, staging)
4. **Strict versioning** (semantic versioning)

**Focus Now**: Implement MeSH hierarchy trees (neuroscientist priority) using current lightweight workflow.

---

## Decisions Made (2025-11-18)

### 1. **UMLS License**: ✅ **Available next day (imminent)**

**Timeline**: License approved, expect access within 24 hours

**Action**: Prepare UMLS ingestion script for neuroscience subset filtering (see decision #2)

---

### 2. **Hierarchy Tree Scope**: ✅ **Neuroscience subset (~3,500 descriptors)**

**Decision**: Full C10/F02/F03 branches + related terms, NOT manually curated

**Scope**:
- C10: Nervous System Diseases (all ~1,800 terms)
- F02: Psychological Phenomena (all ~600 terms)
- F03: Mental Disorders (all ~400 terms)
- Related: G11, D27, E01, E02 subsets (~700 terms)
- **Total**: ~3,500 descriptors

**Rationale**: Faster implementation, complete coverage, manageable performance (10-20x faster than full 28K tree)

---

### 3. **Production Release Target**: ✅ **3 months (when app goes live)**

**Timeline**: Switch from frequent → monthly updates when production app launches

**Current Phase** (now - 3 months):
- Frequent, ad-hoc updates (multiple/week)
- UMLS integration
- MeSH hierarchy tree implementation
- Rapid iteration on data quality

**Future Phase** (3+ months):
- Monthly scheduled releases
- Stable feature set
- Mature QA processes

---

### 4. **Staging Environment**: ✅ **Backend staging implemented**

**Decision**: Staging backend for safe database testing before production

**Status**: **Implemented** (Lex Stream repo)
- GitHub Actions workflows created (staging + production)
- Frontend routing: Preview channels → Staging backend
- Backend CORS: Supports Firebase preview URLs
- Setup guide: `docs/STAGING_SETUP.md`

**User Action Required**: Deploy GCP Cloud Run staging service (~1 hour, see Lex Stream `docs/STAGING_SETUP.md`)

---

## Next Immediate Actions

### 1. **UMLS Ingestion Script** (Priority: Immediate)

Create `scripts/import_umls.sh`:
- Filter UMLS to neuroscience semantic types
- Merge with existing NeuroDB-2 database
- Map to 22-column schema
- Flag duplicates for review

**Semantic Types to Include**:
- T046: Pathologic Function (diseases)
- T047: Disease or Syndrome
- T048: Mental or Behavioral Dysfunction
- T061: Therapeutic or Preventive Procedure
- T074: Medical Device (neuroimaging, neurostimulation)
- T116/T126: Neurotransmitters, signaling molecules

### 2. **MeSH Hierarchy Enrichment** (Priority: Immediate)

Create `scripts/enrich_mesh_hierarchy.sh`:
- Query NIH MeSH API for C10, F02, F03 branches
- Extract tree numbers, parent/child relationships
- Augment `neuro_terms.json` with hierarchy metadata
- See Lex Stream analysis: `docs/analysis/20251118-mesh-hierarchy-scope-and-staging.md`

### 3. **Test in Lex Stream Staging** (After deployment)

- Export database with hierarchy metadata
- Deploy to Lex Stream staging
- Test query expansion quality
- Share preview URL with neuroscientist stakeholders

---

## Unresolved Questions

None - all questions resolved with user input.
