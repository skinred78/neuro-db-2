---
title: Validation Approach Options
date: 2025-11-19
status: pending-decision
decision-point: After import completion (Nov 23-24)
---

# Validation Approach Options for NeuroDB-2

## Decision Timeline

**When to decide**: After bulk import completes (Nov 23-24)
**Why defer**: Actual term count may differ from estimates; can assess quality needs based on import results

---

## Validation Components (Free vs Paid)

### Free Validation (Always Run - No Cost)

**1. Structural Validation** (Python/pandas)
- Column count verification (22 or 26 columns)
- Encoding checks (UTF-8)
- Duplicate detection
- Required field validation
- **Cost**: $0
- **Coverage**: 100% of terms
- **Time**: Minutes

**2. mesh-validator** (NIH MeSH API)
- Validates "Closest MeSH term" field against official NIH database
- Authoritative source for MeSH terms
- API-based, completely free
- **Cost**: $0
- **Coverage**: 100% of terms
- **Time**: 4-6 hours (parallelized API calls)

**Total Free Validation**: $0, catches ~80% of critical errors

---

### Paid Validation (neuro-reviewer using Gemini)

Validates remaining fields (definitions, synonyms, abbreviations, word forms, associated terms)

**Per-term cost**: ~$0.002 (Pro) or ~$0.00012 (Flash)

---

## Validation Option Matrix

| Option | neuro-reviewer Coverage | Cost | Quality Level | Time Required | When to Choose |
|--------|------------------------|------|---------------|---------------|----------------|
| **Minimal** | 50 terms (benchmarks only) | $0.10 | High for critical terms | 1 hour | Proof-of-concept only |
| **Strategic** | 1,000 terms (targeted) | $2 | High for key terms | 2-3 hours | Fast iteration needed |
| **Hybrid Flash/Pro** | 99K Flash + 1K Pro | $14-16 | Very high overall | 10-12 hours | **RECOMMENDED** |
| **Flash Complete** | 100K terms (Flash) | $12 | Good overall | 8-10 hours | Budget-conscious |
| **Pro Partial** | 50K terms (Pro) | $100 | Excellent for half | 1-2 days | High-stakes subset |
| **Pro Complete** | 100K terms (Pro) | $200 | Maximum quality | 2-3 days | Regulatory/medical |

---

## Detailed Option Descriptions

### Option 1: Minimal ($0.10)

**What gets validated**:
- Structural: 100% (free)
- mesh-validator: 100% (free)
- neuro-reviewer: Only benchmark terms (~50 terms)

**Use case**: Proof-of-concept, prototype testing

**Pros**:
- ✅ Extremely cheap ($0.10)
- ✅ Fast (few hours)
- ✅ Benchmarks fully validated

**Cons**:
- ❌ 99.95% of terms not neuro-reviewed
- ❌ High risk of issues in production
- ❌ Not recommended for real deployment

---

### Option 2: Strategic ($2)

**What gets validated**:
- Structural: 100% (free)
- mesh-validator: 100% (free)
- neuro-reviewer: 1,000 strategic terms
  - Benchmark terms (~50)
  - High-frequency terms (~500)
  - Conflict terms (UMLS ≠ Wikipedia) (~200)
  - Random sample (~250)

**Use case**: Deadline-driven development, need to ship quickly

**Pros**:
- ✅ Very cheap ($2)
- ✅ Fast (1 day)
- ✅ Critical terms validated
- ✅ Statistical sampling for confidence

**Cons**:
- ❌ Only 1% neuro-reviewed
- ❌ Potential edge cases missed
- ⚠️ Acceptable for Nov 25 demo, but recommend upgrading later

---

### Option 3: Hybrid Flash/Pro ($14-16) ⭐ RECOMMENDED

**What gets validated**:
- Structural: 100% (free)
- mesh-validator: 100% (free)
- neuro-reviewer Flash: 99,000 terms ($12)
- neuro-reviewer Pro: 1,000 critical terms ($2-4)

**Use case**: Production deployment, balanced quality/cost

**Pros**:
- ✅ 99% neuro-reviewed (Flash quality)
- ✅ 1% ultra-high quality (Pro for critical)
- ✅ Affordable ($14-16)
- ✅ Best cost-to-quality ratio
- ✅ Comprehensive error detection

**Cons**:
- ⚠️ Takes 10-12 hours (can run overnight)
- ⚠️ Flash slightly lower quality than Pro (but 95%+ accurate)

**Why recommended**:
- Sweet spot between cost and coverage
- 99% coverage catches virtually all issues
- Critical terms get Pro validation
- $14-16 is negligible for 100K database

---

### Option 4: Flash Complete ($12)

**What gets validated**:
- Structural: 100% (free)
- mesh-validator: 100% (free)
- neuro-reviewer Flash: 100,000 terms

**Use case**: Budget-conscious, need full coverage

**Pros**:
- ✅ 100% neuro-reviewed
- ✅ Very affordable ($12)
- ✅ Uniform validation quality
- ✅ Comprehensive coverage

**Cons**:
- ⚠️ Flash quality slightly lower than Pro
- ⚠️ Benchmark terms don't get Pro validation
- ⚠️ May miss subtle errors in critical terms

**When to choose**: If budget is tight but need full coverage

---

### Option 5: Pro Partial ($100)

**What gets validated**:
- Structural: 100% (free)
- mesh-validator: 100% (free)
- neuro-reviewer Pro: 50,000 terms
- (Optional) neuro-reviewer Flash: 50,000 terms ($6 additional)

**Use case**: High-stakes deployment, need very high confidence

**Pros**:
- ✅ 50% Pro validation (excellent quality)
- ✅ Can target most important 50K terms
- ✅ Very high confidence in validated subset

**Cons**:
- ❌ Expensive ($100)
- ❌ Only 50% coverage (if not using Flash for rest)
- ❌ Diminishing returns vs Hybrid ($100 vs $16 for <5% quality gain)

**When to choose**: Production medical application, regulatory requirements

---

### Option 6: Pro Complete ($200)

**What gets validated**:
- Structural: 100% (free)
- mesh-validator: 100% (free)
- neuro-reviewer Pro: 100,000 terms

**Use case**: Maximum quality, audit trail required

**Pros**:
- ✅ 100% Pro validation
- ✅ Maximum possible quality
- ✅ Full audit trail
- ✅ Regulatory-grade validation

**Cons**:
- ❌ Most expensive ($200)
- ❌ Takes 2-3 days
- ❌ Overkill for most use cases
- ❌ 12x cost of Hybrid for <2% quality improvement

**When to choose**: Regulatory compliance, medical research, legal liability

---

## Comparison Table

### Quality Metrics Comparison

| Option | MeSH Accuracy | neuro-reviewer Coverage | Overall Confidence | Best For |
|--------|---------------|------------------------|-------------------|----------|
| Minimal | 100% | 0.05% | Medium | Prototype |
| Strategic | 100% | 1% | Medium-High | Fast demo |
| **Hybrid** | **100%** | **99%** | **Very High** | **Production** |
| Flash Complete | 100% | 100% | High | Budget production |
| Pro Partial | 100% | 50% (Pro) | Very High | High stakes |
| Pro Complete | 100% | 100% (Pro) | Maximum | Regulatory |

### Cost-Benefit Analysis

| Option | Cost | Quality Gain vs Previous | Cost per Quality Point | Recommended? |
|--------|------|-------------------------|------------------------|--------------|
| Minimal | $0.10 | Baseline | - | ❌ Too risky |
| Strategic | $2 | +10% | $0.19 per % | ⚠️ If deadline critical |
| **Hybrid** | **$16** | **+90%** | **$0.16 per %** | **✅ YES** |
| Flash Complete | $12 | +1% vs Hybrid | $12 per % | ⚠️ Budget alternative |
| Pro Partial | $100 | +5% vs Hybrid | $17 per % | ❌ Diminishing returns |
| Pro Complete | $200 | +1% vs Pro Partial | $100 per % | ❌ Overkill |

**Sweet spot**: Hybrid at $16 (best quality per dollar)

---

## Decision Criteria Guide

**Choose Minimal ($0.10) if**:
- ❌ Not recommended for any production use

**Choose Strategic ($2) if**:
- Timeline extremely tight (<7 days total)
- Demo/prototype only
- Plan to do full validation later

**Choose Hybrid Flash/Pro ($14-16) if**: ⭐
- ✅ Production deployment
- ✅ Have 10-12 hours for validation
- ✅ Want comprehensive coverage
- ✅ Budget not a constraint (<$20)
- ✅ **RECOMMENDED FOR MOST USE CASES**

**Choose Flash Complete ($12) if**:
- Budget is tight
- Need 100% coverage
- Can accept Flash quality level
- Don't need Pro for critical terms

**Choose Pro Partial ($100) if**:
- High-stakes application
- Medical/research context
- Need audit trail
- Budget allows

**Choose Pro Complete ($200) if**:
- Regulatory requirements
- Legal liability concerns
- Need maximum possible quality
- Money not a concern

---

## Validation Timeline

**Regardless of option chosen, this is the sequence**:

### Phase 1: Structural Validation (Always First)
```bash
# Day after import completes
python scripts/validate_structure.py --input merged_database.csv
# Time: 5-10 minutes
# Cost: $0
# Fix any structural issues before proceeding
```

### Phase 2: mesh-validator (Always Second)
```bash
# Run on all terms
python scripts/validate_mesh_batch.py --input merged_database.csv --threads 10
# Time: 4-6 hours
# Cost: $0
# Fix MeSH errors before neuro-reviewer
```

### Phase 3: neuro-reviewer (Choose Option)
```bash
# OPTION: Strategic ($2)
python scripts/validate_neuro_pro.py --input critical_terms.csv

# OPTION: Hybrid ($16)
python scripts/validate_neuro_flash.py --input merged_database.csv --exclude critical_terms.txt
python scripts/validate_neuro_pro.py --input critical_terms.csv

# OPTION: Flash Complete ($12)
python scripts/validate_neuro_flash.py --input merged_database.csv

# OPTION: Pro Partial ($100)
python scripts/validate_neuro_pro.py --input merged_database.csv --sample 50000

# OPTION: Pro Complete ($200)
python scripts/validate_neuro_pro.py --input merged_database.csv
```

---

## Factors That Might Change Decision

**After import, reassess based on**:

1. **Actual term count**
   - If only 50K terms (not 100K): All options cheaper
   - If 150K terms: Costs scale proportionally

2. **Import quality**
   - If UMLS data very clean: Can use cheaper Flash
   - If many conflicts: Worth using Pro for conflicts

3. **Time available**
   - If extra time: Can afford Pro Complete
   - If rushing: Stick with Strategic

4. **James's feedback**
   - If early testing shows issues: Upgrade to higher tier
   - If quality looks good: Strategic might suffice

5. **Budget constraints**
   - If tight: Flash Complete ($12)
   - If flexible: Hybrid ($16)
   - If unlimited: Pro Complete ($200)

---

## Recommendation Summary

**Default recommendation**: **Hybrid Flash/Pro ($14-16)**

**Rationale**:
- Best cost-to-quality ratio
- 99% coverage sufficient for any practical use
- Critical terms get Pro validation
- Affordable for any budget
- Comprehensive error detection
- Production-ready quality

**When to upgrade**: Only if regulatory/legal requirements demand 100% Pro validation

**When to downgrade**: Only if demo/prototype (can upgrade later)

---

## Next Steps

**Now**: Continue with import implementation (no decision needed yet)

**Nov 23-24**: After import completes
1. Run free validation (structural + mesh-validator)
2. Assess actual term count and quality
3. Review this document
4. Choose validation option based on:
   - Actual data characteristics
   - Time available
   - Budget
   - Quality requirements

**Decision maker**: Sam (with input from implementation results)

---

## Questions to Answer at Decision Point

1. How many terms were actually imported? (affects cost)
2. How many conflicts between sources? (affects need for Pro)
3. How clean is the UMLS data? (affects Flash vs Pro choice)
4. What's the timeline pressure? (affects time available)
5. What's James's early feedback? (affects quality bar)

---

## Unresolved Questions

- Actual UMLS term count after neuroscience filtering (estimate: 100K-150K)
- Quality of UMLS definitions (may be very clean, may have issues)
- Benchmark performance with different validation levels
- James's quality expectations for production

---

**Document Status**: Ready for decision at validation phase (Nov 23-24)
**Default Choice**: Hybrid Flash/Pro ($14-16) unless factors change
