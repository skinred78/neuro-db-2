# Ontology Import Tracker

**Purpose**: Track decisions, findings, data quality characteristics, and trade-offs for each ontology source.

**Last Updated**: 2025-11-19

---

## Import Status Dashboard

| Source | Status | Terms | Definitions | Synonyms | Abbreviations | Associated Terms | Priority | Issues | Decision Docs |
|--------|--------|-------|-------------|----------|---------------|------------------|----------|--------|---------------|
| **Wikipedia** | ✅ Complete | 595 | 100% | High | Medium | High quality | 3 | None | N/A (manual) |
| **NINDS** | ✅ Complete | 54 | 100% | Medium | Low | Low | 3 | None | N/A (manual) |
| **NIF** | ✅ Complete | 1,636 | 13% real, 87% placeholder | Low | Very low | Empty (awaiting UMLS) | 2 | ✅ [Resolved](#nif-associated-terms) | [Link](./2025-11-19-nif-associated-terms-decision.md) |
| **Gene Ontology** | 🔄 Pending (Day 2) | ~2,000 est. | TBD | TBD | TBD | TBD | 2 | TBD | TBD |
| **UMLS** | ⏳ Blocked (license) | 100K-150K est. | TBD | TBD | TBD | TBD | 1 | License pending | TBD |

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

### UMLS Metathesaurus (Blocked - License Pending)

**Status**: License applied, waiting 2-3 days
**Expected Import**: 2025-11-21 or later (Day 3+)
**Source File**: MRCONSO.RRF + MRDEF.RRF (neuroscience filtered)
**Terms Expected**: 100K-150K (filtered from 4M total)

#### Anticipated Characteristics
- Focus: Comprehensive medical/neuroscience terminology
- Definitions: Expected to be extensive
- Synonyms: Expected to be comprehensive (multiple source vocabularies)
- MeSH Terms: Expected to have direct MeSH mappings
- Associated Terms: Expected to have semantic relationships

#### Critical Questions
1. Are UMLS "related concepts" domain-specific or also generic taxonomy?
2. How complete are UMLS definitions for neuroscience terms?
3. What percentage have MeSH mappings?
4. How many conflicts with existing Wikipedia/NINDS/NIF data?

#### Risks
- UMLS might also have generic taxonomy in associated terms
- Filtering 4M → 100K might miss important terms
- Definition quality might vary by source vocabulary

---

## Cross-Source Comparison Matrix

| Feature | Wikipedia/NINDS | NIF | Gene Ontology (est.) | UMLS (est.) |
|---------|----------------|-----|----------------------|-------------|
| **Term Count** | 649 | 1,636 | ~2,000 | 100K-150K |
| **Definition Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐ (13%) | ⭐⭐⭐⭐ (expected) | ⭐⭐⭐⭐⭐ (expected) |
| **Synonym Coverage** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ (expected) | ⭐⭐⭐⭐⭐ (expected) |
| **Domain Focus** | General neuro | Neuroanatomy | Synaptic/molecular | Comprehensive |
| **Associated Terms** | ✅ Domain-specific | ❌ Generic taxonomy | TBD | TBD |
| **Import Effort** | Manual (1 min/term) | Automated (2 min) | Automated (est. 5 min) | Automated (est. 30-60 min) |
| **Validation** | Dual (mesh + neuro) | Structural only | TBD | TBD |

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

### DEC-002: Validation Approach
**Date**: 2025-11-19
**Status**: Deferred to Nov 23-24
**Options**: 6 tiers (Minimal $0.10 → Pro Complete $200)
**Recommendation**: Hybrid Flash/Pro ($14-16)
**Decision Maker**: Sam
**Impact**: High (quality assurance, cost)
**Doc**: [validation-approach-options.md](./validation-approach-options.md)

### DEC-003: UMLS Filtering Strategy
**Date**: TBD (Nov 21+)
**Status**: Not yet decided
**Options**: Conservative (50K-80K), Moderate (100K-150K), Aggressive (200K-300K)
**Recommendation**: Start Moderate, can expand
**Decision Maker**: Sam
**Impact**: High (database size, performance, coverage)
**Doc**: TBD

---

## Lessons Learned

### Ontology-Specific Insights

1. **NIF/Taxonomic Sources**: Focus on structure names, not semantic relationships
2. **RDF/OWL Formats**: "Broader/narrower" relationships ≠ domain associations
3. **Definition Coverage**: Taxonomic ontologies prioritize classification over descriptions
4. **Deduplication**: Always check for case-insensitive duplicates in ontology imports

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

1. **Immediate (Day 1)**: Decide on NIF associated terms (DEC-001)
2. **Day 2**: Profile Gene Ontology sample data before full import
3. **Day 3+**: Profile UMLS sample data, create UMLS-specific decision doc
4. **Day 4**: Merge strategy decisions (how to handle conflicts, priority rules)
5. **Day 5**: Validation approach decision (DEC-002)

---

**Maintained by**: Engineering team
**Review frequency**: After each ontology import
**Document Status**: Living document - update continuously
