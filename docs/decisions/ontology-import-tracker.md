# Ontology Import Tracker

**Purpose**: Track decisions, findings, data quality characteristics, and trade-offs for each ontology source.

**Last Updated**: 2025-11-20

---

## Import Status Dashboard

| Source | Status | Terms | Definitions | Synonyms | Abbreviations | Associated Terms | Priority | Issues | Decision Docs |
|--------|--------|-------|-------------|----------|---------------|------------------|----------|--------|---------------|
| **Wikipedia** | ✅ Complete | 595 | 100% | High | Medium | High quality | 3 | None | N/A (manual) |
| **NINDS** | ✅ Complete | 54 | 100% | Medium | Low | Low | 3 | None | N/A (manual) |
| **NIF** | ✅ Complete | 1,636 | 13% real, 87% placeholder | Low | Very low | Empty (awaiting UMLS) | 2 | ✅ [Resolved](#nif-associated-terms) | [Link](./2025-11-19-nif-associated-terms-decision.md) |
| **UMLS** | ✅ Complete | 325,241 | 24.5% | 9.0% | 0.4% | 90.4% ✅ | 1 | ✅ [3 resolved](#umls-metathesaurus) | [DEC-002](./2025-11-20-umls-cui-filter-count-decision.md), [DEC-003](./2025-11-20-umls-coverage-strategy-decision.md) |
| **Gene Ontology** | 🔄 Pending (Day 3) | ~2,000 est. | TBD | TBD | TBD | TBD | 2 | TBD | TBD |

**Legend**:
- ✅ Complete and validated
- 🔄 In progress
- ⏳ Blocked/waiting
- ❌ Issue identified

---

## Source-Specific Findings

### NIF (Neuroscience Information Framework)

**Import Date**: 2025-11-19
**Source File**: NIF-GrossAnatomy.ttl (1.41 MB, 29,742 RDF triples)
**Terms Imported**: 1,636
**Source Priority**: 2

#### Data Quality Characteristics

| Characteristic | Rating | Notes |
|----------------|--------|-------|
| **Structure Names** | ⭐⭐⭐⭐⭐ Excellent | High-quality neuroanatomy structure names |
| **Definitions** | ⭐⭐ Poor | Only 13% have definitions (taxonomic source) |
| **Synonyms** | ⭐⭐ Poor | Limited synonym coverage |
| **Abbreviations** | ⭐ Very Poor | Minimal abbreviation data |
| **Associated Terms** | ⭐ Very Poor | Generic taxonomy only (see issue below) |
| **Hierarchy/Relationships** | ⭐⭐⭐⭐⭐ Excellent | Strong parent-child structural relationships |
| **Coverage** | ⭐⭐⭐⭐ Good | Comprehensive brain structure taxonomy |

#### Strengths
- ✅ Authoritative neuroanatomy structure names (Fornix, Hippocampus, Thalamus, etc.)
- ✅ Comprehensive hierarchical relationships (parent/child structures)
- ✅ Multi-species coverage (human, macaque, rat, mouse)
- ✅ Clean, validated data (no duplicates after processing)
- ✅ Strong foundation for MeSH tree implementation

#### Limitations
- ❌ 87% placeholder definitions (inherent to source being taxonomic)
- ❌ Associated terms are generic taxonomy ("Regional part of brain" = 36% of entries)
- ❌ Limited synonym coverage
- ❌ Minimal abbreviation data
- ⚠️ Lower term count than expected (1,636 vs 3,000 estimated)

#### Issues Discovered

##### Issue #1: Associated Terms Are Generic Taxonomy
**Severity**: Medium
**Impact**: Pollutes "commonly associated terms" field with ontology metadata
**Status**: ✅ Resolved (Option A - Skip associated terms)
**Resolution Date**: 2025-11-19
**Decision Doc**: [2025-11-19-nif-associated-terms-decision.md](./2025-11-19-nif-associated-terms-decision.md)

**Details**:
- RDF hierarchy relationships (broader/narrower) populated associated terms
- Top entry: "Regional part of brain" (593 occurrences, 36%)
- These are class hierarchy, not domain associations
- Not useful for Lex Stream query expansion

**Options Considered**:
- A: Skip associated terms in NIF import (30 min fix) ✅ CHOSEN
- B: Wait for UMLS, decide during merge (2 hour merge complexity)
- C: Smart filtering by frequency threshold (1-2 hour implementation)

**Resolution Implemented**:
- Modified `scripts/import_nif_neuroanatomy.py` to skip RDF hierarchy extraction
- Re-ran import: All 1,636 terms now have empty associated term fields
- UMLS will populate associated terms during merge (Day 4)
- NIF focuses on structure names only (its core strength)
- Decision reversible if MeSH tree implementation needs hierarchy

##### Issue #2: Lower Term Count Than Expected
**Severity**: Low
**Impact**: None (UMLS will provide 100K-150K terms)
**Status**: Documented

**Details**:
- Expected ~3,000 terms based on NeuroNames documentation
- Actual: 1,636 after deduplication
- Likely reasons:
  - NIF-GrossAnatomy is subset of full NeuroNames database
  - Duplicates removed (12 found)
  - Stricter TTL parsing filters

**Resolution**: Acceptable. NIF valuable for structure names even with lower count.

#### Dependencies
- **Definitions**: Requires UMLS merge for comprehensive definitions
- **Synonyms**: Requires UMLS merge for extensive synonyms
- **Associated Terms**: Requires UMLS merge for domain associations

#### Merge Strategy
- **Use NIF for**: Structure names, hierarchical relationships
- **Supplement with UMLS**: Definitions, synonyms, domain associations
- **Priority**: NIF priority=2 overridden by UMLS priority=1 for conflicting definitions

---

### UMLS Metathesaurus

**Import Date**: 2025-11-20
**Source Files**: MRCONSO.RRF (2.1 GB), MRDEF.RRF (131 MB), MRREL.RRF (5.7 GB), MRSTY.RRF (201 MB)
**Terms Imported**: 325,241
**Source Priority**: 1 (Highest - authoritative medical terminology)

#### Data Quality Characteristics

| Characteristic | Rating | Notes |
|----------------|--------|-------|
| **Term Coverage** | ⭐⭐⭐⭐⭐ Excellent | 325K terms (2x target volume) |
| **Definitions** | ⭐⭐ Poor | Only 24.5% have definitions (anatomical ontology issue) |
| **Synonyms** | ⭐⭐ Poor | 9.0% coverage (TTY filtering may be strict) |
| **Abbreviations** | ⭐ Very Poor | 0.4% coverage (1,208 abbreviations) |
| **Associated Terms** | ⭐⭐⭐⭐⭐ Excellent | 90.4% coverage (294K terms with associations) |
| **MeSH Codes** | ⭐ Very Poor | 4.2% coverage (13,739 terms) |
| **Source Quality** | ⭐⭐⭐⭐ Good | Multiple authoritative sources (NCI, GO, MSH) |
| **Structural Validity** | ⭐⭐⭐⭐⭐ Perfect | 0 errors, 26-column schema compliance |

#### Strengths
- ✅ Massive term coverage (325,241 terms - 2x target)
- ✅ Excellent association coverage (90.4% - critical for Lex Stream)
- ✅ Domain-specific relationships extracted (1.8M relationships)
- ✅ Multi-source compilation (NCI, GO, MSH, FMA, SNOMEDCT, etc.)
- ✅ Authoritative medical terminology (UMLS gold standard)
- ✅ Comprehensive semantic type filtering (27 types, 1M CUIs)

#### Limitations
- ❌ Low definition coverage (24.5%) - anatomical ontologies lack textual definitions
- ❌ Very low MeSH coverage (4.2%) - most terms from non-MeSH sources
- ❌ Low synonym coverage (9.0%) - TTY filtering may need expansion
- ❌ Very low abbreviation coverage (0.4%) - only 1,208 abbreviations
- ⚠️ Definitions not required for Lex Stream core agents (DEC-003 finding)

#### Issues Discovered

##### Issue #1: CUI Filter Count Too High (1M vs 100K-150K target)
**Severity**: Medium
**Impact**: Potential database bloat, processing overhead
**Status**: ✅ Resolved (DEC-002 - Option B)
**Resolution Date**: 2025-11-20
**Decision Doc**: [2025-11-20-umls-cui-filter-count-decision.md](./2025-11-20-umls-cui-filter-count-decision.md)

**Details**:
- Initial semantic type filtering produced 1,015,068 CUIs (7-10x target)
- Semantic types too broad (captured ALL drugs, ALL proteins, ALL diseases)
- Risk of importing non-neuroscience terms

**Options Considered**:
- A: Restrict to Priority 1 types only (~250K CUIs)
- B: Proceed with 1M CUIs + multi-stage filtering (CHOSEN) ✅
- C: Hybrid selective approach (~200K CUIs)

**Resolution Implemented**:
- Accepted 1M CUIs as input to multi-stage MRCONSO parser
- Stage 1: CUI match (17.4M → 7.0M rows)
- Stage 2: English only (7.0M → 4.1M rows)
- Stage 3: Not suppressed (4.1M → 3.6M rows)
- Stage 4: Preferred terms (3.6M → 2.9M rows)
- Stage 5: Keyword filter for broad types (2.9M → 48K passed, 1.97M rejected)
- **Final output**: 325,241 terms (68% reduction, natural filtering worked)

##### Issue #2: Low Definition Coverage (24.5% vs 80%+ expected)
**Severity**: High (initially), Low (after investigation)
**Impact**: Defeats UMLS import goal (initially thought)
**Status**: ✅ Resolved (DEC-003 - Option A)
**Resolution Date**: 2025-11-20
**Decision Doc**: [2025-11-20-umls-coverage-strategy-decision.md](./2025-11-20-umls-coverage-strategy-decision.md)

**Details**:
- Only 79,617 of 325,241 terms (24.5%) have definitions
- Root cause: Anatomical ontologies (FMA, UWDA) dominate volume (48% of terms)
- FMA/UWDA are structural hierarchies, not encyclopedic sources
- Initial assumption: definitions required for Lex Stream

**Investigation**:
- Analyzed Lex Stream codebase (`/Users/sam/Lex-stream-2`) via Explore agent
- Found: Core agents (spell check, abbreviation, synonym, MeSH) do NOT use definitions
- Definitions only used by Component Detector (optional PICO feature)
- Test Results: All agents handle missing definitions gracefully

**Options Considered**:
- A: Import all 325K terms (24.5% coverage) (CHOSEN) ✅
- B: Filter to definitions-only (~80K terms, 100% coverage)
- C: Hybrid source prioritization (~145K terms, 70% coverage)
- D: Multi-tier import (separate files)
- E: Combine with NIF definitions

**Resolution Implemented**:
- Accepted Option A: Import all 325K terms
- Rationale: Maximum coverage more valuable than definition coverage for query expansion
- Core agents (90% of use cases) work without definitions
- Component Detector degraded but functional (24.5% can use definitions)
- Future: Can backfill definitions via Wikipedia/AI generation

##### Issue #3: UMLS Relationships - Domain-Specific vs Taxonomy (DEC-001)
**Severity**: Medium
**Impact**: Quality of "commonly associated terms" field
**Status**: ✅ Resolved (Proceed with MRREL)
**Resolution Date**: 2025-11-20
**Decision Doc**: Profiled in DEC-001 assessment

**Details**:
- Question: Do UMLS associations provide domain-specific relationships or generic taxonomy?
- Parsed MRREL.RRF: 5.7 GB, 63.5M rows
- Found 14.6M rows involving our 325K CUIs
- Extracted 13.0M relationships
- **Domain-specific**: 1.8M (13.8% of extracted)
- **Pure taxonomy (excluded)**: 3.1M (21.0% of matches)

**Finding**: UMLS relationships are **primarily taxonomic** but provide substantial domain-specific relationships

**Domain-Specific Relationship Types Extracted**:
- Anatomical: `part_of`, `has_part`, `innervates`, `finding_site_of`
- Pharmacological: `treats`, `has_mechanism_of_action`, `has_physiologic_effect`
- Pathological: `causes`, `manifestation_of`, `has_pathological_process`

**Resolution**:
- Proceed with MRREL associations
- Result: **90.4% association coverage** (294,008 of 325,241 terms)
- Even at 13.8% domain-specific, provides excellent coverage
- Filtered out pure taxonomy (PAR, CHD, SIB, RB, RN)

#### Source Breakdown by Volume

| Source | Terms | Definition Coverage | Quality |
|--------|-------|---------------------|---------|
| **FMA** | 99,074 (30%) | 5.1% | Anatomical hierarchy |
| **SNOMEDCT_US** | 67,590 (21%) | 15.5% | Clinical terminology |
| **UWDA** | 60,201 (18%) | 5.4% | Anatomical hierarchy |
| **GO** | 54,118 (17%) | 69.5% | ✅ Excellent |
| **MEDCIN** | 39,773 (12%) | 12.8% | Clinical terms |
| **MTH** | 39,063 (12%) | 40.5% | Metathesaurus |
| **NCI** | 35,800 (11%) | 89.1% | ✅ Excellent |
| **MSH** | 13,739 (4%) | 54.1% | ✅ Good |

**Pattern**: High-quality sources (NCI, GO, MSH) have lower volume but excellent definitions. Anatomical sources (FMA, UWDA) have high volume but low definitions.

#### Pipeline Summary

**Phase 1: Filtering & Extraction**
1. Build neuroscience CUI filter (MRSTY → 1.02M CUIs)
2. Parse MRCONSO with multi-stage filtering (17.4M → 325K terms)
3. Parse MRDEF for definitions (79,617 definitions, 24.5%)
4. Deduplicate by term name (325,241 unique)

**Phase 2: Enrichment & Mapping**
1. Parse MRREL for related concepts (1.8M domain-specific relationships)
2. Map CUI associations to term names (294,008 with associations)
3. Map to NeuroDB-2 26-column schema
4. Structural validation (✅ 0 errors)

**Total Processing Time**: ~45 minutes (automated)

#### Dependencies
- **Definitions**: Can backfill later via Wikipedia/NINDS/AI generation
- **MeSH Codes**: Can enrich via NIH MeSH API mapping
- **Synonyms**: Can expand with additional TTY types from MRCONSO
- **Abbreviations**: Can expand with relaxed TTY filters

#### Future Improvements (Priority Order)

1. **Definition Backfill** (Priority: High)
   - Target: Top 10K most-queried terms
   - Sources: Wikipedia, NINDS, PubMed abstracts
   - Goal: Increase to 40-50% coverage

2. **MeSH Code Enrichment** (Priority: Medium)
   - Method: NIH MeSH API mapping
   - Target: Terms from MSH source without mesh_code
   - Goal: Increase to 20-30% coverage

3. **Synonym Expansion** (Priority: Medium)
   - Re-parse MRCONSO with additional TTY types (SYN, ET, ETCF)
   - Goal: Increase to 30-40% coverage

4. **Abbreviation Expansion** (Priority: Low)
   - Re-parse with relaxed TTY filters
   - Cross-reference with NIF abbreviations
   - Goal: Increase to 5-10% coverage

#### Merge Strategy
- **Primary Use**: Comprehensive term coverage, associated terms
- **Priority**: UMLS priority=1 overrides NIF priority=2 for definitions
- **NIF Complement**: NIF provides structure names, UMLS provides associations
- **Result**: NIF's empty associated terms fields populated by UMLS relationships

#### Validation Results
- **Structural**: ✅ 0 errors, 0 warnings
- **Schema**: ✅ 26 columns (22 standard + 4 metadata)
- **Required Fields**: ✅ All populated (Term, Definition or placeholder)
- **CSV Format**: ✅ Proper quoting/escaping

#### Integration Status
- **Lex Stream**: ✅ Ready for integration
- **Spell Checker**: ✅ Excellent (325K term dictionary)
- **Abbreviation Expander**: ⚠️ Limited (1.2K abbreviations)
- **Synonym Finder**: ⚠️ Limited (29K terms with synonyms)
- **MeSH Detector**: ⚠️ Limited (13.7K terms with codes)
- **Component Detector**: ⚠️ Fair (24.5% can use definitions)

---

### Wikipedia + NINDS (Existing Data)

**Import Date**: 2025-11-12 (completed before ontology expansion)
**Terms Imported**: 595 (Wikipedia) + 54 (NINDS) = 649 total
**Source Priority**: 3

#### Data Quality Characteristics

| Characteristic | Rating | Notes |
|----------------|--------|-------|
| **Definitions** | ⭐⭐⭐⭐⭐ Excellent | Well-written, comprehensive |
| **Synonyms** | ⭐⭐⭐⭐ Good | Multiple synonyms per term |
| **Abbreviations** | ⭐⭐⭐ Fair | Standard abbreviations included |
| **Associated Terms** | ⭐⭐⭐⭐ Good | Domain-relevant associations |
| **Coverage** | ⭐⭐ Poor | Only 649 terms (insufficient for quality queries) |

#### Strengths
- ✅ High-quality human-curated definitions
- ✅ Domain-appropriate associated terms
- ✅ Validated through dual review (mesh-validator + neuro-reviewer)
- ✅ Strong foundation for benchmark testing

#### Limitations
- ❌ Low term count (595 + 54 = 649)
- ❌ Manual enrichment bottleneck (1 min/term)
- ⚠️ Lex Stream testing shows insufficient coverage for quality searches

---

### Gene Ontology (Pending - Day 2)

**Status**: Not yet implemented
**Expected Import**: 2025-11-20 (Day 2)
**Source File**: goslim_synapse.obo
**Terms Expected**: ~2,000

#### Anticipated Characteristics
- Focus: Synaptic function, gene/protein roles
- Format: OBO (simpler than TTL)
- Definitions: Expected to be comprehensive (GO is well-documented)
- Synonyms: Expected to have exact/broad/narrow/related
- Associated Terms: Likely domain-specific (molecular functions, biological processes)

#### Questions to Answer
1. Are GO definitions neuroscience-appropriate or too molecular?
2. Do GO associated terms help PubMed query expansion?
3. What's the overlap with NIF structure names?
4. How many abbreviations in GO terms?

---

## Cross-Source Comparison Matrix

| Feature | Wikipedia/NINDS | NIF | UMLS | Gene Ontology (est.) |
|---------|----------------|-----|------|----------------------|
| **Term Count** | 649 | 1,636 | 325,241 ✅ | ~2,000 |
| **Definition Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐ (13%) | ⭐⭐ (24.5%) | ⭐⭐⭐⭐ (expected) |
| **Synonym Coverage** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ (9%) | ⭐⭐⭐⭐ (expected) |
| **Domain Focus** | General neuro | Neuroanatomy | Comprehensive | Synaptic/molecular |
| **Associated Terms** | ✅ Domain-specific | ❌ Generic taxonomy | ✅ 90.4% coverage | TBD |
| **Import Effort** | Manual (1 min/term) | Automated (2 min) | Automated (45 min) | Automated (est. 5 min) |
| **Validation** | Dual (mesh + neuro) | Structural only | Structural (0 errors) | TBD |
| **Lex Stream Ready** | ✅ Yes | ✅ Yes | ✅ Yes | TBD |

---

## Decision Log

### DEC-001: NIF Associated Terms Handling
**Date**: 2025-11-19
**Status**: ✅ RESOLVED - Option A Implemented
**Decision Date**: 2025-11-19
**Options**: Skip (A), Wait (B), Filter (C)
**Chosen**: Option A - Skip associated terms
**Decision Maker**: Sam
**Impact**: Medium (cleaner data, UMLS dependency for associations)
**Result**: All 1,636 NIF terms have empty associated fields
**Doc**: [2025-11-19-nif-associated-terms-decision.md](./2025-11-19-nif-associated-terms-decision.md)

### DEC-002: UMLS CUI Filter Count Strategy
**Date**: 2025-11-20
**Status**: ✅ RESOLVED - Option B Implemented
**Decision Date**: 2025-11-20
**Options**: Restrict Priority 1 (A), Proceed with 1M + multi-stage (B), Hybrid (C)
**Chosen**: Option B - Proceed with 1M CUIs + multi-stage filtering
**Decision Maker**: Sam
**Impact**: High (determines term volume, filtering complexity)
**Result**: 1.02M CUIs → 325,241 terms (68% reduction via natural filtering)
**Doc**: [2025-11-20-umls-cui-filter-count-decision.md](./2025-11-20-umls-cui-filter-count-decision.md)

### DEC-003: UMLS Coverage Strategy (Definition Field)
**Date**: 2025-11-20
**Status**: ✅ RESOLVED - Option A Implemented
**Decision Date**: 2025-11-20
**Options**: Import all (A), Definitions-only (B), Hybrid sources (C), Multi-tier (D), NIF merge (E)
**Chosen**: Option A - Import all 325K terms (24.5% definition coverage)
**Decision Maker**: Sam
**Impact**: Critical (determines import strategy, Lex Stream compatibility)
**Result**: 325K terms imported. Lex Stream codebase analysis showed definitions optional for core agents.
**Doc**: [2025-11-20-umls-coverage-strategy-decision.md](./2025-11-20-umls-coverage-strategy-decision.md)

### Validation Approach Decision
**Date**: 2025-11-19
**Status**: Deferred to Nov 23-24
**Options**: 6 tiers (Minimal $0.10 → Pro Complete $200)
**Recommendation**: Hybrid Flash/Pro ($14-16)
**Decision Maker**: Sam
**Impact**: High (quality assurance, cost)
**Doc**: [validation-approach-options.md](./validation-approach-options.md)

---

## Lessons Learned

### Ontology-Specific Insights

1. **NIF/Taxonomic Sources**: Focus on structure names, not semantic relationships
2. **RDF/OWL Formats**: "Broader/narrower" relationships ≠ domain associations
3. **Definition Coverage**: Taxonomic ontologies prioritize classification over descriptions
4. **Deduplication**: Always check for case-insensitive duplicates in ontology imports
5. **UMLS Filtering**: Multi-stage filtering (1M CUIs → 325K) more effective than strict upfront filters
6. **UMLS Source Quality**: Volume ≠ quality (FMA/UWDA high volume, NCI/GO lower volume but better definitions)
7. **Definition Requirements**: Validate actual code usage before assuming fields are required
8. **MRREL Relationships**: Domain-specific relationships exist (13.8%) but need filtering (exclude pure taxonomy)

### Process Improvements

1. **Decision Tracking**: Document trade-offs BEFORE implementing, not after
2. **Data Profiling**: Analyze sample data before full import (saves rework)
3. **Incremental Testing**: Test small samples (100 terms) before full import
4. **Source Expectations**: Research ontology purpose/focus to set realistic expectations

---

## Templates

### New Ontology Import Checklist

- [ ] Research ontology purpose and focus area
- [ ] Identify data format (TTL, OBO, RRF, JSON, XML)
- [ ] Download sample data (100-1000 terms)
- [ ] Profile data characteristics (definitions %, synonyms %, etc.)
- [ ] Identify potential issues (generic terms, missing fields, duplicates)
- [ ] Document findings in this tracker
- [ ] Create decision document if trade-offs exist
- [ ] Implement importer using infrastructure libraries
- [ ] Run structural validation
- [ ] Update this tracker with results
- [ ] Commit with comprehensive commit message

### Issue Template

```markdown
##### Issue #N: [Brief Description]
**Severity**: Low | Medium | High | Critical
**Impact**: [What's affected]
**Status**: Discovered | Pending Decision | Resolved
**Decision Doc**: [Link if applicable]

**Details**: [What's the problem]

**Options**: [If applicable]
- A: [Option description] (cost/benefit)
- B: [Option description] (cost/benefit)

**Recommendation**: [If applicable]

**Resolution**: [How was it resolved, or pending decision]
```

---

## Next Actions

1. ✅ **Day 1** (2025-11-19): NIF import complete, DEC-001 resolved
2. ✅ **Day 2** (2025-11-20): UMLS import complete, DEC-002 & DEC-003 resolved
3. **Day 3** (2025-11-21): Gene Ontology import
   - Profile sample data before full import
   - Focus on synaptic/molecular terms
   - Assess definition quality and domain specificity
4. **Day 4+**: Merge & Integration
   - Merge UMLS + NIF + Wikipedia/NINDS (+ GO if complete)
   - Resolve conflicts using source priority rules (UMLS=1, NIF=2, Wiki/NINDS=3)
   - Export to Lex Stream JSON format
   - Integration testing with Lex Stream agents
5. **Day 5+**: Quality Improvements
   - Definition backfill for top 10K terms (Wikipedia, NINDS)
   - MeSH code enrichment via NIH API
   - Synonym/abbreviation expansion
   - Validation approach decision (if deferred from Nov 19)

---

**Maintained by**: Engineering team
**Review frequency**: After each ontology import
**Document Status**: Living document - update continuously
