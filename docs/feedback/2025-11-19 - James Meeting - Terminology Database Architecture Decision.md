---
title: James Meeting - Terminology Database Architecture Decision
date: 2025-11-19
note_type: meeting
attendees:
  - James
  - Sam
projects:
  - project-academiq
tags:
  - type-meeting
  - project-academiq
  - lex-stream
---

## Executive Summary

Terminology database architecture decision resolved ahead of Nov 25 deadline: simplified parent-child tree structure (not full branch-twig-leaf) due to time constraints. Priority ontology sources identified (UMLS Metathesaurus, Neuronames, NIF, Gene/Protein GO) for immediate ingestion starting tonight. Validation approach established using James's existing search strings as quality benchmarks. Key insight: MeSH-only searches too restrictive—need balanced MeSH terms + text words approach.

## Key Discussion Points

- **Priority Ontology Sources Identified** (Immediate ingestion):

  1. **UMLS Metathesaurus** (mandatory)
  2. **Neuronames** (#6 - mandatory)
  3. **NIF** (#7 - mandatory)
  4. **Gene/Protein Ontology (GO)** (very useful, include now)



- **MeSH Tree Structure Integration** (Simplified approach):
    - **Decision**: "Ontology light" version—parent + child only (not full tree structure)
    - **Rationale**: Time constraints given Tom's urgency; full branch-twig-leaf structure too complex/time-consuming for alpha
    - **Example**: Parkinson's disease has multiple parent branches (synucleinopathies, basal ganglia diseases, movement disorders) and multiple child branches; simplified version captures one parent + one child relationship
    - **Implementation**: Tree relationships translate into OR operators within components ("Parkinson's disease OR synucleinopathies OR basal ganglia diseases")
    - **Next step**: Sam to develop ideas on implementation by Friday
- **Search String Architecture Clarified**:
    - **Components**: Queries divided into logical components (disease, methodology, patient population, study design)
    - **Within-component logic**: OR operators connect related terms from tree structure
    - **Between-component logic**: AND operators connect different concept components
    - **"Secret sauce"**: Algorithm to weight terms based on tree relationships—determines when to include broader parent terms vs narrower child terms
    - **Human element**: Understanding when user wants "Parkinson's disease" specifically vs broader "movement disorders" category—this expertise is "gold dust"
- **MeSH Terms vs Text Words Balance**:
    - **MeSH-only limitation**: Relies on PubMed indexing; papers must have all specified MeSH terms; indexing quality varies
    - **Text word advantage**: Searches title/abstract/full text/references; captures papers regardless of indexing
    - **Text word risk**: Too broad (word in single reference) vs too narrow (title/abstract only)
    - **Best practice**: Combine MeSH terms + text words within each component for comprehensive coverage
    - **Typical ratio**: Not specified numerically, but both types essential in every component
- **Validation Methodology Established**:
    - **Benchmark search strings**: James's existing queries (neuromodulation, multiple sclerosis, Alzheimer's disease)
    - **Characteristics**: Specific/niche within broad categories; <25 hits to maintain focus (not 300+ hits)
    - **Goal**: Replicate human-generated quality; 100% replication unlikely initially
    - **Gap analysis**: Differences attributed to glossary size—insufficient synonyms, related terms, variants
    - **Testing owner**: Sam continues testing against these benchmarks
- **Query Refinement Process** (UX implications):
    - **Systematic literature reviews**: Search string fixed in protocol; changes must be transparent/justified in publication
    - **Manuscript development**: Frequent iterations—adding keywords, updating for new publications (continuous refinement throughout writing process)
    - **Typical modifications**: Adding keywords/concepts to increase specificity
    - **Risk**: Single additional AND keyword can over-narrow (50 hits → 2 hits indicates "overstepped the mark")
    - **UX requirement**: Agile editing capability—modify search string components, remove unwanted terms, regenerate (vs current "reset and start over")
    - **Advanced option**: Let users edit Lex-generated search string directly; basic option: trust system's curated list
- **Product Positioning Insight**:
    - **Framing**: "Curated list" of best matches, not comprehensive search
    - **Dual value proposition**: (1) Capture obvious KOL publications for confidence, (2) Uncover niche/parallel research for discovery
    - **Discovery value**: Methods from different research fields; unexpected relevant approaches; "wildcard" matches with high potential interest
    - **User confidence**: Must show super-KOL papers to validate tool reliability while providing discovery value

## Decisions Made

1. **Simplified tree structure approach**: Parent-child only (not full tree) for alpha due to time constraints; positions architecture well for future versions
1. **Priority ontology ingestion order**: UMLS Metathesaurus, Neuronames, NIF, Gene/Protein GO starting immediately (tonight)
1. **Validation benchmarks**: James's three existing search strings (neuromodulation, MS, Alzheimer's) as quality targets
1. **Version roadmap**: v0.5/v1 focus on core algorithm; UX refinements (agile editing, user customization) deferred to later versions

## Action Items

**For You**:

1. Start ingesting priority ontologies (UMLS, Neuronames, NIF, GO) tonight using automated process (By: Nov 20)
2. Develop MeSH tree structure integration ideas and present to James (By: Nov 22 - Friday)
3. Continue testing against James's benchmark search strings to track quality improvement (Ongoing)
4. Follow up with James on progress Thursday/Friday (By: Nov 21-22)

## Strategic Notes

- **Architecture decision unblocked ahead of Nov 25 deadline**: Simplified parent-child approach balances time constraints with quality improvement pathway; avoids over-engineering while maintaining scalability
- **MeSH integration complexity acknowledged**: Weighting algorithm for tree relationships represents significant technical challenge; versioned approach (v0.5, v1) realistic given trial-and-error requirements
- **Quality bar calibrated**: Not expecting 100% replication of expert search strings initially; gaps attributed to glossary size (solvable through ontology expansion) rather than architectural limitations
- **User experience philosophy established**: "Curated list" framing reduces pressure for comprehensive coverage; focuses value proposition on discovery + confidence rather than exhaustive search
- **Agile editing capability critical for future versions**: Researchers iterate frequently (especially manuscript development); current "reset and start over" approach incompatible with real usage patterns
- **Meeting linked to prep document**: [[2025-11-19 - James Meeting Prep - Terminology Database Questions]] successfully addressed all 8 question areas