# Roadmap Clarity: When Planning Replaces Panic

**Date**: 2025-12-04 09:00
**Severity**: Low (Strategic)
**Component**: Project Direction
**Status**: Documented

## What Happened

Spent morning writing two planning documents:
1. `251204-semantic-classification-implementation.md` - The HOW (5 weeks, 4 phases, 7 categories)
2. `251204-lexstream-query-roadmap.md` - The WHY (product vision, strategic pillars, metrics)

No code written. No tests run. Just markdown. And it feels like the most productive morning in two weeks.

## The Brutal Truth

We've been STUCK. Not technically blocked - the POC works, the APIs respond, the webapp deploys. But stuck in the "what do we build next?" paralysis.

The symptoms:
- Test framework with 20% pass rate (but is that bad?)
- Three database approaches (manual, UMLS, API-first) with unclear winner
- James's feedback about hierarchy (but MeSH import is 3 months of work)
- Beta pressure (need to ship something) vs foundation concerns (get the architecture right)

The planning session forced answering:
- **What's the goal?** Expert-grade PubMed queries for niche research monitoring
- **What's missing?** Semantic classification (system doesn't know MS is a disease)
- **What's the priority?** Classification BEFORE hierarchy (James: "Without knowing what a term IS, MeSH tree position is less useful")
- **What's deferred?** MeSH hierarchy trees, LLM phrase parsing, full UMLS enrichment

## Technical Details

**Seven semantic categories** (the breakthrough):
```
1. POPULATION_CONTEXT - Who/where (elderly, patients, rodents)
2. CONDITION_DISEASE - What's wrong (MS, Parkinson's, stroke)
3. INTERVENTION_EXPOSURE - What's done (TMS, DBS, drugs)
4. OUTCOME_MEASURE - What's measured (motor function, cognition)
5. ANATOMY_SYSTEM - Where in body (hippocampus, motor cortex)
6. MECHANISM_BIOLOGICAL - How it works (dopamine, neuroplasticity)
7. OBJECT_DEVICE - Physical things (electrode, implant)
```

**Why this matters**: Each category expands DIFFERENTLY.
- CONDITION: Synonyms + subtypes (NEVER mechanisms)
- INTERVENTION: Same modality only (NEVER outcomes or mechanisms)
- MECHANISM: ONLY direct synonyms (HIGH drift risk)

**The "MS + neuromodulation" example revisited**:
```
Without classification:
"MS" → expand to "multiple sclerosis, demyelination, autoimmune, inflammation..."
"neuromodulation" → expand to "neurostimulation, modulation, neural activity..."
Query: Drift into every neuroscience paper mentioning inflammation

With classification:
"MS" (CONDITION_DISEASE) → synonyms only, no mechanisms
"neuromodulation" (INTERVENTION_EXPOSURE) → same modality (TMS, DBS)
Query: Focused on disease + intervention intersection
```

**Implementation scope**:
- Phase 1 (weeks 1-2): 7-category taxonomy + UMLS TUI mapping
- Phase 2 (week 3): Category-specific expanders
- Phase 3 (weeks 4-5): Enriched database + hybrid flow
- DEFERRED: MeSH hierarchy, LLM parsing, full UMLS

## What We Tried

This IS what we're trying - the strategic pause to plan before building more.

Previous approach: Build → test → fail → debug → build more
Current approach: Plan → validate approach → prototype → iterate

The roadmap documents answer:
- **Product vision**: "Secret sauce is understanding hierarchy and nuance"
- **Current gaps**: Semantic drift (dopamine pollutes disease queries)
- **Desired state**: Category-aware expansion preventing drift
- **Success metrics**: 5-20 relevant papers (not 1, not 1,943)

## Root Cause Analysis

**Why we needed this**: Three weeks of execution without clear strategic direction. Each phase (manual curation, UMLS import, API-first) was reactive to previous phase's limitations, not proactive toward end goal.

**What changed**: James's feedback provided the "why" (hierarchy matters), but we still needed the "how" (what to build) and "when" (what to defer).

**The planning insight**: Semantic classification is the MVP. Everything else (MeSH trees, LLM parsing, full UMLS enrichment) can wait. Get the categories right first.

## Lessons Learned

1. **Strategic pause ≠ wasted time**: 4 hours planning > 2 weeks building the wrong thing
2. **Defer aggressively**: MeSH hierarchy is valuable but not blocking - defer it
3. **Prototype first**: 70-term prototype (all 7 categories) before enriching 569 terms
4. **Category framework is the unlock**: 7 categories + expansion rules solves semantic drift
5. **Document assumptions**: "MS is a disease" feels obvious, but system must encode it

## The Relief

The feeling stuck came from having three competing approaches (manual, UMLS, API) and no clear winner. The roadmap resolves it:

**Hybrid architecture** (Option C):
- Primary layer: 569 curated terms (gold standard with semantic types)
- Extended layer: ~3,500 MeSH neuroscience terms (deferred to phase 4)
- Fallback layer: UMLS 325K (unknown term lookup)

All three databases have value. Just different roles. Not "which is best?" but "which layer for what?"

## Next Steps

1. Review roadmap with James (does this align with vision?)
2. Approve Phase 1 implementation plan
3. Select 70 prototype terms (10 per category except MECHANISM=10)
4. Begin UMLS TUI → 7-category mapping
5. Build category-specific expanders

**Timeline**: 5 weeks to MVP (semantic classification working)
**Deferred**: MeSH hierarchy (3 months), LLM phrase parsing (phase 5+)

## Emotional Footnote

The satisfying part of planning isn't the documents themselves - it's the CLARITY. Three weeks of "what should we build?" anxiety condensed into:

> Build semantic classification (7 categories). Prototype with 70 terms. Defer MeSH hierarchy. Hybrid architecture (all three databases have roles).

That's a plan you can execute. That's a vision you can validate. That's a direction you can commit to.

And honestly? Writing down "MeSH hierarchy: DEFERRED" feels better than the ambiguous pressure of "we should probably add MeSH trees at some point maybe".

Defer with intention. Build with focus. Ship the MVP.

**Artifacts**:
- `plans/251204-lexstream-query-roadmap.md` (strategic)
- `plans/251204-semantic-classification-implementation.md` (tactical)
