"""
Category-Specific Expansion Rules for Semantic Classification

Defines expansion strategies and anti-drift patterns for each of the
7 semantic categories. Based on James's stakeholder feedback.

Reference: docs/architecture/semantic-classification-architecture.md
"""

import re
from dataclasses import dataclass, field
from typing import List, Set, Pattern, Optional
from enum import Enum

from poc_api_first.semantic_types import SemanticCategory


class ExpansionStrategy(Enum):
    """Expansion strategy levels."""
    NONE = "none"           # No expansion (term only)
    MINIMAL = "minimal"     # Only direct synonyms (1-2)
    NARROW = "narrow"       # Synonyms only (3-5)
    MODERATE = "moderate"   # Synonyms + related (5-8)
    BROAD = "broad"         # Extensive expansion (8-15)


@dataclass
class ExpansionRule:
    """
    Expansion rule for a semantic category.

    Attributes:
        category: The semantic category this rule applies to
        strategy: Default expansion strategy
        max_expansions: Maximum number of expansion terms
        include_types: What to include in expansion
        exclude_types: What to NEVER include (high priority)
        forbidden_patterns: Regex patterns to filter out (anti-drift)
        notes: Human-readable notes about the rule
    """
    category: SemanticCategory
    strategy: ExpansionStrategy
    max_expansions: int
    include_types: List[str] = field(default_factory=list)
    exclude_types: List[str] = field(default_factory=list)
    forbidden_patterns: List[str] = field(default_factory=list)
    notes: str = ""

    def get_compiled_patterns(self) -> List[Pattern]:
        """Compile forbidden patterns for efficient matching."""
        return [re.compile(p, re.IGNORECASE) for p in self.forbidden_patterns]

    def is_forbidden(self, term: str) -> bool:
        """Check if a term matches any forbidden pattern."""
        for pattern in self.get_compiled_patterns():
            if pattern.search(term):
                return True
        return False

    def filter_expansions(self, terms: List[str]) -> List[str]:
        """Filter out forbidden terms from expansion list."""
        return [t for t in terms if not self.is_forbidden(t)]


# ============================================================================
# EXPANSION RULES BY CATEGORY (James's decisions)
# ============================================================================

EXPANSION_RULES = {
    # -------------------------------------------------------------------------
    # POPULATION_CONTEXT: Rarely expand, synonyms only
    # Examples: elderly, pediatric, stroke survivors, healthy controls
    # -------------------------------------------------------------------------
    SemanticCategory.POPULATION_CONTEXT: ExpansionRule(
        category=SemanticCategory.POPULATION_CONTEXT,
        strategy=ExpansionStrategy.MINIMAL,
        max_expansions=3,
        include_types=["synonyms"],
        exclude_types=["hierarchical", "related"],
        forbidden_patterns=[],
        notes="Rarely expand. Synonyms only (e.g., 'older adults' → 'aged', 'elderly'). "
              "Hierarchical OK for rodents (mice/rats)."
    ),

    # -------------------------------------------------------------------------
    # CONDITION_DISEASE: Synonyms, acronyms, subtypes
    # Examples: MS, Parkinson's, stroke, Alzheimer's, depression
    # NEVER: mechanisms, non-clinical terms
    # -------------------------------------------------------------------------
    SemanticCategory.CONDITION_DISEASE: ExpansionRule(
        category=SemanticCategory.CONDITION_DISEASE,
        strategy=ExpansionStrategy.NARROW,
        max_expansions=5,
        include_types=["synonyms", "acronyms", "subtypes", "hierarchical_children"],
        exclude_types=["mechanisms", "non_clinical"],
        forbidden_patterns=[
            r"pathway$",      # blocks "dopaminergic pathway"
            r"signaling$",    # blocks "cell signaling"
            r"receptor$",     # blocks "dopamine receptor"
            r"neuron$",       # blocks anatomy/mechanism crossover
            r"cascade$",      # blocks "signaling cascade"
            r"transduction$", # blocks "signal transduction"
            r"expression$",   # blocks "gene expression"
            r"activation$",   # blocks "receptor activation"
            r"inhibition$",   # blocks mechanism terms
            r"modulation$",   # blocks mechanism terms
        ],
        notes="Expand to exact synonyms, acronyms, clinical subtypes. "
              "NEVER mechanisms (dopamine, pathway), non-clinical terms."
    ),

    # -------------------------------------------------------------------------
    # INTERVENTION_EXPOSURE: Synonyms, same modality/procedure
    # Examples: TMS, DBS, tDCS, neuromodulation, neurostimulation
    # NEVER: mechanisms, objects/devices, outcomes
    # -------------------------------------------------------------------------
    SemanticCategory.INTERVENTION_EXPOSURE: ExpansionRule(
        category=SemanticCategory.INTERVENTION_EXPOSURE,
        strategy=ExpansionStrategy.MODERATE,
        max_expansions=8,
        include_types=["synonyms", "same_modality", "related_procedures"],
        exclude_types=["mechanisms", "devices", "outcomes"],
        forbidden_patterns=[
            r"plasticity$",    # blocks mechanism
            r"excitability$",  # blocks mechanism
            r"response$",      # blocks outcome
            r"improvement$",   # blocks outcome
            r"recovery$",      # blocks outcome
            r"device$",        # blocks object
            r"electrode$",     # blocks object (unless context)
            r"coil$",          # blocks object (unless context)
        ],
        notes="Common synonyms, same modality/procedure. "
              "NEVER mechanisms, objects/devices, outcomes."
    ),

    # -------------------------------------------------------------------------
    # OUTCOME_MEASURE: Synonyms, acronyms, scale variants
    # Examples: motor function, cognition, memory, gait, tremor
    # -------------------------------------------------------------------------
    SemanticCategory.OUTCOME_MEASURE: ExpansionRule(
        category=SemanticCategory.OUTCOME_MEASURE,
        strategy=ExpansionStrategy.MODERATE,
        max_expansions=8,
        include_types=["synonyms", "acronyms", "scale_variants", "measurement_labels"],
        exclude_types=[],
        forbidden_patterns=[
            r"treatment$",     # blocks intervention
            r"therapy$",       # blocks intervention
            r"stimulation$",   # blocks intervention
        ],
        notes="Synonyms, acronyms, measurement labels, scale variants. "
              "Example: UPDRS, EDSS score variants."
    ),

    # -------------------------------------------------------------------------
    # ANATOMY_SYSTEM: Hierarchical children, subregions
    # Examples: motor cortex, hippocampus, basal ganglia, cerebellum
    # AVOID: overly broad regions (e.g., "whole brain")
    # -------------------------------------------------------------------------
    SemanticCategory.ANATOMY_SYSTEM: ExpansionRule(
        category=SemanticCategory.ANATOMY_SYSTEM,
        strategy=ExpansionStrategy.NARROW,
        max_expansions=5,
        include_types=["synonyms", "hierarchical_children", "subregions"],
        exclude_types=["overly_broad"],
        forbidden_patterns=[
            r"^brain$",        # too broad
            r"^nervous system$",  # too broad
            r"^central nervous system$",  # too broad
            r"^cns$",          # too broad
            r"pathway$",       # mechanism overlap
            r"network$",       # mechanism overlap (unless specific)
            r"circuit$",       # mechanism overlap (unless specific)
        ],
        notes="Well-defined hierarchical children, known subregions. "
              "AVOID overly broad regions like 'whole brain'."
    ),

    # -------------------------------------------------------------------------
    # MECHANISM_BIOLOGICAL: ONLY direct synonyms (HIGH DRIFT RISK)
    # Examples: neuroplasticity, dopamine, serotonin, LTP, GABA
    # -------------------------------------------------------------------------
    SemanticCategory.MECHANISM_BIOLOGICAL: ExpansionRule(
        category=SemanticCategory.MECHANISM_BIOLOGICAL,
        strategy=ExpansionStrategy.MINIMAL,
        max_expansions=2,
        include_types=["direct_synonyms", "canonical_alternatives"],
        exclude_types=["related", "hierarchical", "pathways"],
        forbidden_patterns=[
            r"disease$",       # blocks condition terms
            r"disorder$",      # blocks condition terms
            r"syndrome$",      # blocks condition terms
            r"therapy$",       # blocks intervention
            r"treatment$",     # blocks intervention
            r"function$",      # blocks outcome
            r"measure$",       # blocks outcome
        ],
        notes="ONLY direct synonyms or canonical alternatives. "
              "HIGH DRIFT RISK - be extremely conservative."
    ),

    # -------------------------------------------------------------------------
    # OBJECT_DEVICE: Limited expansion, physical things only
    # Examples: electrode, coil, implant, probe, sensor
    # -------------------------------------------------------------------------
    SemanticCategory.OBJECT_DEVICE: ExpansionRule(
        category=SemanticCategory.OBJECT_DEVICE,
        strategy=ExpansionStrategy.MINIMAL,
        max_expansions=3,
        include_types=["direct_synonyms"],
        exclude_types=["conceptual", "procedures"],
        forbidden_patterns=[
            r"stimulation$",   # blocks intervention
            r"therapy$",       # blocks intervention
            r"function$",      # blocks outcome
        ],
        notes="LIMITED expansion - physical things, not conceptual. "
              "Direct synonyms only."
    ),

    # -------------------------------------------------------------------------
    # UNKNOWN: Conservative fallback
    # -------------------------------------------------------------------------
    SemanticCategory.UNKNOWN: ExpansionRule(
        category=SemanticCategory.UNKNOWN,
        strategy=ExpansionStrategy.MINIMAL,
        max_expansions=2,
        include_types=["synonyms"],
        exclude_types=[],
        forbidden_patterns=[],
        notes="Fallback for unclassified terms. Very conservative."
    ),
}


def get_expansion_rule(category: SemanticCategory) -> ExpansionRule:
    """
    Get expansion rule for a semantic category.

    Args:
        category: SemanticCategory enum value

    Returns:
        ExpansionRule for the category
    """
    return EXPANSION_RULES.get(category, EXPANSION_RULES[SemanticCategory.UNKNOWN])


def get_max_expansions(category: SemanticCategory) -> int:
    """Get maximum expansion count for a category."""
    return get_expansion_rule(category).max_expansions


def filter_by_category(
    terms: List[str],
    category: SemanticCategory
) -> List[str]:
    """
    Filter expansion terms based on category-specific forbidden patterns.

    Args:
        terms: List of candidate expansion terms
        category: SemanticCategory of the source term

    Returns:
        Filtered list with forbidden terms removed
    """
    rule = get_expansion_rule(category)
    return rule.filter_expansions(terms)


def should_expand(category: SemanticCategory) -> bool:
    """Check if a category should be expanded at all."""
    rule = get_expansion_rule(category)
    return rule.strategy != ExpansionStrategy.NONE


def get_expansion_strategy(category: SemanticCategory) -> ExpansionStrategy:
    """Get expansion strategy for a category."""
    return get_expansion_rule(category).strategy


# ============================================================================
# EXPANSION STRATEGY SUMMARY (for documentation)
# ============================================================================

EXPANSION_SUMMARY = """
SEMANTIC CATEGORY EXPANSION RULES
=================================

| Category              | Strategy | Max | Expand To                        | Never Expand To              |
|-----------------------|----------|-----|----------------------------------|------------------------------|
| POPULATION_CONTEXT    | Minimal  | 3   | Synonyms only                    | Hierarchical                 |
| CONDITION_DISEASE     | Narrow   | 5   | Synonyms, acronyms, subtypes     | Mechanisms, non-clinical     |
| INTERVENTION_EXPOSURE | Moderate | 8   | Synonyms, same modality          | Mechanisms, devices, outcomes|
| OUTCOME_MEASURE       | Moderate | 8   | Synonyms, acronyms, scales       | Interventions                |
| ANATOMY_SYSTEM        | Narrow   | 5   | Synonyms, subregions             | Overly broad regions         |
| MECHANISM_BIOLOGICAL  | Minimal  | 2   | ONLY direct synonyms             | Everything else (HIGH RISK)  |
| OBJECT_DEVICE         | Minimal  | 3   | Direct synonyms only             | Conceptual, procedures       |
| UNKNOWN               | Minimal  | 2   | Synonyms only                    | —                            |

Anti-Drift Patterns:
- CONDITION: pathway$, signaling$, receptor$, neuron$
- INTERVENTION: plasticity$, response$, improvement$, device$
- ANATOMY: ^brain$, pathway$, network$, circuit$
- MECHANISM: disease$, therapy$, treatment$, function$
"""


if __name__ == "__main__":
    # Test expansion rules
    print("Expansion Rules Test")
    print("=" * 60)

    # Test filtering
    test_terms = [
        "multiple sclerosis",
        "dopaminergic pathway",  # Should be filtered for CONDITION
        "MS",
        "demyelination",
        "signal transduction",   # Should be filtered
    ]

    rule = get_expansion_rule(SemanticCategory.CONDITION_DISEASE)
    filtered = rule.filter_expansions(test_terms)

    print(f"\nCONDITION_DISEASE filtering:")
    print(f"  Input: {test_terms}")
    print(f"  Output: {filtered}")
    print(f"  Removed: {set(test_terms) - set(filtered)}")

    # Show all rules
    print("\n" + EXPANSION_SUMMARY)
