"""
Search Methodology Comparison Framework - Configuration Definitions.

PURPOSE: Define multiple search tool configurations for side-by-side comparison.
This allows researchers to evaluate which tool combination works best for their
specific query types and domains.

CONFIGURATIONS:
- LexStream2Baseline: Original Lex Stream pipeline (rule-based)
- NeuroDBOnly: Local abbreviation lookup (neuroscience-specific)
- UMLSOnly: UMLS semantic classification (no disambiguation)
- PubTatorOnly: PubTator biomedical disambiguation (no classification)
- UMLSPubTator: 2-layer hybrid (disambiguation → classification)
- UMLSNeuroDB: NeuroDB abbreviations + UMLS classification
- FullHybrid: 3-layer (NeuroDB → PubTator → UMLS)

CAPABILITY_MATRIX: Defines which metrics each config can produce, ensuring
fair comparison (e.g., don't penalize PubTator-only for lacking semantic classification).
"""

import os
import json
from pathlib import Path


# Capability Matrix: defines which metrics each configuration can produce
CAPABILITY_MATRIX = {
    'LexStream2Baseline': {
        'supports_semantic_classification': False,  # Skip semantic_accuracy metric
        'supports_abbreviation_expansion': True,
        'supports_component_detection': True,  # Rule-based, not UMLS-based
        'supports_synonym_expansion': True
    },
    'NeuroDBOnly': {
        'supports_semantic_classification': False,  # No UMLS classification
        'supports_abbreviation_expansion': True,   # NeuroDB abbreviation lookup
        'supports_component_detection': False,
        'supports_synonym_expansion': False
    },
    'UMLSOnly': {
        'supports_semantic_classification': True,
        'supports_abbreviation_expansion': False,  # No abbreviation expansion
        'supports_component_detection': False,
        'supports_synonym_expansion': False
    },
    'PubTatorOnly': {
        'supports_semantic_classification': False,  # No UMLS classification
        'supports_abbreviation_expansion': True,    # PubTator disambiguation
        'supports_component_detection': False,
        'supports_synonym_expansion': False
    },
    'UMLSPubTator': {
        'supports_semantic_classification': True,
        'supports_abbreviation_expansion': True,
        'supports_component_detection': False,
        'supports_synonym_expansion': False
    },
    'UMLSNeuroDB': {
        'supports_semantic_classification': True,
        'supports_abbreviation_expansion': True,
        'supports_component_detection': False,
        'supports_synonym_expansion': True
    },
    'FullHybrid': {
        'supports_semantic_classification': True,
        'supports_abbreviation_expansion': True,
        'supports_component_detection': False,
        'supports_synonym_expansion': True
    },
    'SemanticClassification': {
        'supports_semantic_classification': True,  # 7-category classification
        'supports_abbreviation_expansion': True,   # NeuroDB abbreviations
        'supports_component_detection': True,      # Category-based detection
        'supports_synonym_expansion': True,        # With anti-drift filtering
        'supports_category_specific_expansion': True  # NEW: Phase 1 feature
    }
}


class LexStream2BaselineConfig:
    """
    Lex Stream 2's current implementation: "component-based blind expansion"

    CLARIFICATION:
    - "Blind" = No UMLS semantic classification (doesn't know T047=Disease vs T061=Therapeutic)
    - "Component-based" = DOES have rule-based categorization (pattern matching to detect
      Intervention/Condition/Outcome from term structure and database hints)

    Example: "MS + neuromodulation"
    - "MS" → expanded to "multiple sclerosis" (abbreviation lookup)
    - Both categorized via RULE-BASED patterns (NOT semantic classification)
    - Query: (MS OR multiple sclerosis) AND (neuromodulation)
    - Result: 1 hit (too restrictive due to missing semantic understanding)

    vs. Semantic Classification (UMLS):
    - "MS" → C0026769 (T047: Disease or Syndrome) → CONDITION
    - "neuromodulation" → C0520587 (T061: Therapeutic Procedure) → INTERVENTION
    - Query uses [MeSH] for CONDITION, [tiab] with synonyms for INTERVENTION
    - Result: 5 hits (better precision)

    NOTE: This is a REFERENCE configuration for comparison. Actual Lex Stream 2
    pipeline implementation would be required for live testing.
    """
    name = "LexStream2Baseline"
    use_pubtator = False
    use_neurodb = True  # neuro_terms.json v2.0
    use_umls = False    # No UMLS semantic classification

    def __init__(self):
        """Initialize baseline with NeuroDB-2 local database."""
        # Use relative path from project root
        neurodb_path = Path(__file__).parent.parent.parent / 'data' / 'neuro_terms.json'

        if not neurodb_path.exists():
            raise FileNotFoundError(
                f"NeuroDB-2 data file not found: {neurodb_path}\n"
                "Please ensure data/neuro_terms.json exists in project root."
            )

        with open(neurodb_path) as f:
            self.neurodb = json.load(f)

    def process_query(self, terms):
        """
        Lex Stream 2's query processing pipeline:
        1. Abbreviation expansion from neuro_terms.json (local lookup)
        2. Synonym finding from neuro_terms.json (local lookup)
        3. RULE-BASED component detection (pattern matching, NOT semantic classification)
        4. Query assembly: OR within components, AND between components

        Key limitation: No UMLS semantic types → can't distinguish Disease (use [MeSH])
        from Therapeutic Procedure (use [tiab] with broad synonyms)

        NOTE: Requires actual Lex Stream 2 pipeline implementation.
        """
        raise NotImplementedError(
            "LexStream2Baseline is a reference configuration. "
            "Actual Lex Stream 2 pipeline implementation required for testing."
        )


class NeuroDBOnlyConfig:
    """
    Single-layer: Only NeuroDB abbreviation lookup (no UMLS classification, no PubTator)

    Flow:
    - Abbreviation detected → NeuroDB lookup
    - Match found → use expanded term directly (no UMLS classification)
    - No match → use original term as-is

    Fallback: Original term (UNKNOWN category, no classification)

    Purpose: Baseline to measure value of NeuroDB neuroscience-specific abbreviations
    without any external API calls.
    """
    name = "NeuroDBOnly"
    use_neurodb = True
    use_umls = False
    use_pubtator = False

    def __init__(self):
        """Initialize with NeuroDB-2 local database only."""
        neurodb_path = Path(__file__).parent.parent.parent / 'data' / 'neuro_terms.json'

        if not neurodb_path.exists():
            raise FileNotFoundError(
                f"NeuroDB-2 data file not found: {neurodb_path}\n"
                "Please ensure data/neuro_terms.json exists in project root."
            )

        with open(neurodb_path) as f:
            raw_data = json.load(f)

        # Build abbreviation lookup from list format
        self.abbreviations = {}
        for entry in raw_data:
            abbrev = entry.get('Abbreviation')
            term_name = entry.get('Term')
            if abbrev and term_name:
                self.abbreviations[abbrev.lower()] = term_name

    @staticmethod
    def is_abbreviation(term):
        """Check if term is likely an abbreviation."""
        return len(term) <= 5 or term.isupper() or (len(term.split()) == 1 and len(term) <= 10)

    def classify_term(self, term):
        """
        Single-layer: NeuroDB abbreviation lookup only.

        No UMLS classification - returns UNKNOWN category.
        Confidence 0.9 for NeuroDB matches, 0.3 for fallback.
        """
        original_term = term

        # NeuroDB abbreviation lookup
        if term.lower() in self.abbreviations:
            resolved = self.abbreviations[term.lower()]
            return {
                'term': resolved,
                'original_term': original_term,
                'category': 'UNKNOWN',  # No UMLS classification
                'disambiguation_source': 'NeuroDB',
                'confidence': 0.9  # High confidence for curated match
            }

        # Fallback: use original term
        return {
            'term': term,
            'original_term': original_term,
            'category': 'UNKNOWN',
            'disambiguation_source': 'none',
            'confidence': 0.3  # Low confidence, no disambiguation
        }

    def _classify_terms_batch(self, terms):
        """Batch classification - wraps classify_term for pipeline callback."""
        return [self.classify_term(t) for t in terms]

    def run(self, user_input, days=60, max_results=20, verbose=False):
        """
        Execute pipeline with NeuroDB-only classification.

        No external API calls for classification - only PubMed search.
        """
        from poc_api_first.poc_pipeline import SemanticQueryPipeline

        pipeline = SemanticQueryPipeline(
            umls_client=None,      # No UMLS
            pubmed_client=None,    # Use default
            pubtator_client=None,  # No PubTator
            classify_fn=self._classify_terms_batch
        )
        return pipeline.run(
            user_input=user_input,
            days=days,
            max_results=max_results,
            verbose=verbose
        )


class UMLSOnlyConfig:
    """
    Single-layer: Only UMLS semantic classification (no abbreviation expansion)

    Flow:
    - All terms → UMLS direct lookup
    - No PubTator disambiguation
    - No NeuroDB expansion

    Limitation: Abbreviations may fail UMLS lookup (e.g., "MS" → no CUI found)

    Purpose: Baseline to show value of disambiguation layers (PubTator, NeuroDB)
    """
    name = "UMLSOnly"
    use_neurodb = False
    use_umls = True
    use_pubtator = False

    def __init__(self):
        """Initialize UMLS client only."""
        from poc_api_first.clients.umls import UMLSClient

        api_key = os.getenv("UMLS_API_KEY")
        if not api_key:
            raise ValueError("UMLS_API_KEY environment variable not set")

        self.umls_client = UMLSClient(api_key)

    def classify_term(self, term):
        """
        Single-layer: UMLS direct lookup only.

        No abbreviation expansion - abbreviations sent directly to UMLS.
        """
        result = self.umls_client.classify_term(term)
        result['original_term'] = term
        result['disambiguation_source'] = 'UMLS_direct'
        result['confidence'] = 0.7 if result.get('cui') else 0.3
        return result

    def _classify_terms_batch(self, terms):
        """Batch classification - wraps classify_term for pipeline callback."""
        return [self.classify_term(t) for t in terms]

    def run(self, user_input, days=60, max_results=20, verbose=False):
        """
        Execute pipeline with UMLS-only classification.

        No abbreviation expansion - relies on UMLS to understand abbreviations.
        """
        from poc_api_first.poc_pipeline import SemanticQueryPipeline

        pipeline = SemanticQueryPipeline(
            umls_client=self.umls_client,
            pubmed_client=None,    # Use default
            pubtator_client=None,  # No PubTator
            classify_fn=self._classify_terms_batch
        )
        return pipeline.run(
            user_input=user_input,
            days=days,
            max_results=max_results,
            verbose=verbose
        )


class PubTatorOnlyConfig:
    """
    Single-layer: Only PubTator disambiguation (no UMLS classification)

    Flow:
    - Abbreviation detected → PubTator autocomplete
    - Match found → use expanded term (no UMLS classification)
    - No match → use original term as-is

    Fallback: Original term (UNKNOWN category)

    Purpose: Measure PubTator disambiguation quality without UMLS.
    """
    name = "PubTatorOnly"
    use_neurodb = False
    use_umls = False
    use_pubtator = True

    def __init__(self):
        """Initialize PubTator client only."""
        from poc_api_first.clients.pubtator import PubTatorClient
        self.pubtator_client = PubTatorClient()

    @staticmethod
    def is_abbreviation(term):
        """Check if term is likely an abbreviation."""
        return len(term) <= 5 or term.isupper() or (len(term.split()) == 1 and len(term) <= 10)

    def classify_term(self, term):
        """
        Single-layer: PubTator disambiguation only.

        No UMLS classification - returns UNKNOWN category.
        """
        original_term = term

        # PubTator disambiguation
        if self.is_abbreviation(term):
            disambiguation = self.pubtator_client.disambiguate_term(term)
            if disambiguation['confidence'] > 0.5:
                return {
                    'term': disambiguation['resolved'],
                    'original_term': original_term,
                    'category': 'UNKNOWN',  # No UMLS classification
                    'disambiguation_source': 'PubTator',
                    'confidence': disambiguation['confidence']
                }

        # Fallback: use original term
        return {
            'term': term,
            'original_term': original_term,
            'category': 'UNKNOWN',
            'disambiguation_source': 'none',
            'confidence': 0.3
        }

    def _classify_terms_batch(self, terms):
        """Batch classification - wraps classify_term for pipeline callback."""
        return [self.classify_term(t) for t in terms]

    def run(self, user_input, days=60, max_results=20, verbose=False):
        """
        Execute pipeline with PubTator-only disambiguation.

        No semantic classification - only abbreviation expansion.
        """
        from poc_api_first.poc_pipeline import SemanticQueryPipeline

        pipeline = SemanticQueryPipeline(
            umls_client=None,      # No UMLS
            pubmed_client=None,    # Use default
            pubtator_client=self.pubtator_client,
            classify_fn=self._classify_terms_batch
        )
        return pipeline.run(
            user_input=user_input,
            days=days,
            max_results=max_results,
            verbose=verbose
        )


class UMLSPubTatorConfig:
    """
    UMLS + PubTator (POC - PROVEN 5 hits)

    Proven configuration from POC testing:
    - "MS + neuromodulation" → 5 hits (vs 1 hit for baseline)
    - PubTator handles abbreviation disambiguation
    - UMLS provides semantic classification
    """
    name = "UMLSPubTator"
    use_pubtator = True
    use_neurodb = False

    def __init__(self):
        """Initialize UMLS + PubTator clients."""
        # Import here to avoid circular dependencies
        from poc_api_first.clients.umls import UMLSClient
        from poc_api_first.clients.pubtator import PubTatorClient

        api_key = os.getenv("UMLS_API_KEY")
        if not api_key:
            raise ValueError("UMLS_API_KEY environment variable not set")

        self.umls_client = UMLSClient(api_key)
        self.pubtator_client = PubTatorClient()

    @staticmethod
    def is_abbreviation(term):
        """Check if term is likely an abbreviation."""
        return len(term) <= 5 or term.isupper() or (len(term.split()) == 1 and len(term) <= 10)

    def classify_term(self, term):
        """
        Two-layer disambiguation and classification:
        1. PubTator abbreviation expansion (if abbreviation detected)
        2. UMLS semantic classification
        """
        original_term = term
        disambiguation_source = 'UMLS_direct'
        confidence = 0.5

        # Step 1: PubTator disambiguation
        if self.is_abbreviation(term):
            disambiguation = self.pubtator_client.disambiguate_term(term)
            if disambiguation['confidence'] > 0.5:
                term = disambiguation['resolved']
                disambiguation_source = 'PubTator'
                confidence = disambiguation['confidence']

        # Step 2: UMLS classification
        result = self.umls_client.classify_term(term)
        result['original_term'] = original_term
        result['disambiguation_source'] = disambiguation_source
        result['confidence'] = confidence
        return result

    def _classify_terms_batch(self, terms):
        """Batch classification - wraps classify_term for pipeline callback."""
        return [self.classify_term(t) for t in terms]

    def run(self, user_input, days=60, max_results=20, verbose=False):
        """
        Execute semantic pipeline with this config's classification.

        Creates SemanticQueryPipeline with injected clients and classify_fn.
        """
        from poc_api_first.poc_pipeline import SemanticQueryPipeline

        pipeline = SemanticQueryPipeline(
            umls_client=self.umls_client,
            pubmed_client=None,  # Use default
            pubtator_client=self.pubtator_client,
            classify_fn=self._classify_terms_batch
        )
        return pipeline.run(
            user_input=user_input,
            days=days,
            max_results=max_results,
            verbose=verbose
        )


class FullHybridConfig:
    """
    UMLS + PubTator + NeuroDB-2 (Full Hybrid)

    Three-layer disambiguation with confidence-based arbitration:
    - Layer 1: NeuroDB-2 (neuroscience-specific, highest confidence)
    - Layer 2: PubTator (biomedical general)
    - Layer 3: UMLS direct lookup (fallback)
    """
    name = "FullHybrid"
    use_pubtator = True
    use_neurodb = True

    def __init__(self):
        """Initialize all clients: UMLS, PubTator, and NeuroDB-2."""
        # Import here to avoid circular dependencies
        from poc_api_first.clients.umls import UMLSClient
        from poc_api_first.clients.pubtator import PubTatorClient

        api_key = os.getenv("UMLS_API_KEY")
        if not api_key:
            raise ValueError("UMLS_API_KEY environment variable not set")

        self.umls_client = UMLSClient(api_key)
        self.pubtator_client = PubTatorClient()

        # Load NeuroDB-2 with relative path
        neurodb_path = Path(__file__).parent.parent.parent / 'data' / 'neuro_terms.json'

        if not neurodb_path.exists():
            raise FileNotFoundError(
                f"NeuroDB-2 data file not found: {neurodb_path}\n"
                "Please ensure data/neuro_terms.json exists in project root."
            )

        with open(neurodb_path) as f:
            raw_data = json.load(f)

        # Build abbreviation lookup from list format
        # neuro_terms.json is a list of dicts with 'Abbreviation' and 'Term' fields
        self.abbreviations = {}
        for entry in raw_data:
            abbrev = entry.get('Abbreviation')
            term_name = entry.get('Term')
            if abbrev and term_name:
                self.abbreviations[abbrev.lower()] = term_name

    @staticmethod
    def is_abbreviation(term):
        """Check if term is likely an abbreviation."""
        return len(term) <= 5 or term.isupper() or (len(term.split()) == 1 and len(term) <= 10)

    def classify_term(self, term):
        """
        Three-layer disambiguation with confidence-based selection:
        - NeuroDB-2 (confidence: 1.0) - neuroscience-specific curation
        - PubTator (confidence: 0.5-0.9) - biomedical general
        - UMLS direct (confidence: 0.5) - fallback

        Selects highest-confidence expansion for UMLS classification.
        """
        original_term = term

        # Layer 1: NeuroDB-2 (neuroscience-specific - highest priority)
        if term.lower() in self.abbreviations:
            resolved = self.abbreviations[term.lower()]
            result = self.umls_client.classify_term(resolved)
            result['original_term'] = original_term
            result['disambiguation_source'] = 'NeuroDB'
            result['confidence'] = 1.0
            return result

        # Layer 2: PubTator (biomedical general)
        if self.is_abbreviation(term):
            disambiguation = self.pubtator_client.disambiguate_term(term)
            if disambiguation['confidence'] > 0.5:
                resolved = disambiguation['resolved']
                result = self.umls_client.classify_term(resolved)
                result['original_term'] = original_term
                result['disambiguation_source'] = 'PubTator'
                result['confidence'] = disambiguation['confidence'] * 0.9
                return result

        # Layer 3: UMLS direct lookup (fallback)
        result = self.umls_client.classify_term(term)
        result['original_term'] = original_term
        result['disambiguation_source'] = 'UMLS_direct'
        result['confidence'] = 0.5
        return result

    def _classify_terms_batch(self, terms):
        """Batch classification - wraps classify_term for pipeline callback."""
        return [self.classify_term(t) for t in terms]

    def run(self, user_input, days=60, max_results=20, verbose=False):
        """
        Execute semantic pipeline with this config's 3-layer classification.

        Creates SemanticQueryPipeline with injected clients and classify_fn.
        NeuroDB-2 provides highest-priority neuroscience abbreviation expansion.
        """
        from poc_api_first.poc_pipeline import SemanticQueryPipeline

        pipeline = SemanticQueryPipeline(
            umls_client=self.umls_client,
            pubmed_client=None,  # Use default
            pubtator_client=self.pubtator_client,
            classify_fn=self._classify_terms_batch
        )
        return pipeline.run(
            user_input=user_input,
            days=days,
            max_results=max_results,
            verbose=verbose
        )


class SemanticClassificationConfig:
    """
    7-Category Semantic Classification with Category-Specific Expansion.

    NEW: Phase 1 implementation of semantic classification architecture.

    Key features:
    - 7 semantic categories (vs old 5): POPULATION_CONTEXT, CONDITION_DISEASE,
      INTERVENTION_EXPOSURE, OUTCOME_MEASURE, ANATOMY_SYSTEM, MECHANISM_BIOLOGICAL,
      OBJECT_DEVICE
    - Category-specific expansion rules (anti-drift filtering)
    - Full 127 TUI mapping (vs old 21)
    - Hybrid lookup: NeuroDB → UMLS fallback

    Flow:
    1. NeuroDB lookup (highest priority, 569 curated terms)
    2. UMLS API fallback (127 TUIs → 7 categories)
    3. Category-specific expansion with anti-drift filtering

    Reference: docs/architecture/semantic-classification-architecture.md
    """
    name = "SemanticClassification"
    use_neurodb = True
    use_umls = True
    use_pubtator = False  # Simplified flow for Phase 1

    def __init__(self):
        """Initialize with NeuroDB + UMLS (7-category) classification."""
        from poc_api_first.clients.umls import UMLSClient
        from poc_api_first.semantic_types import SemanticCategory, get_category_from_tui
        from poc_api_first.expansion_rules import (
            get_expansion_rule,
            filter_by_category,
            ExpansionStrategy,
        )

        api_key = os.getenv("UMLS_API_KEY")
        if not api_key:
            raise ValueError("UMLS_API_KEY environment variable not set")

        self.umls_client = UMLSClient(api_key)

        # Store imports for later use
        self._SemanticCategory = SemanticCategory
        self._get_category_from_tui = get_category_from_tui
        self._get_expansion_rule = get_expansion_rule
        self._filter_by_category = filter_by_category
        self._ExpansionStrategy = ExpansionStrategy

        # Load NeuroDB-2 with relative path
        neurodb_path = Path(__file__).parent.parent.parent / 'data' / 'neuro_terms.json'

        if not neurodb_path.exists():
            raise FileNotFoundError(
                f"NeuroDB-2 data file not found: {neurodb_path}\n"
                "Please ensure data/neuro_terms.json exists in project root."
            )

        with open(neurodb_path) as f:
            raw_data = json.load(f)

        # Build lookup dictionaries from NeuroDB
        self.abbreviations = {}
        self.term_lookup = {}
        for entry in raw_data:
            term_name = entry.get('Term', '').lower()
            abbrev = entry.get('Abbreviation')

            # Store full entry for term lookup
            if term_name:
                self.term_lookup[term_name] = entry

            # Store abbreviation mapping
            if abbrev and term_name:
                self.abbreviations[abbrev.lower()] = entry.get('Term')

    def classify_term(self, term):
        """
        7-category semantic classification with hybrid lookup.

        1. Check NeuroDB for abbreviation expansion
        2. UMLS API for full 127 TUI → 7 category classification
        3. Apply category-specific expansion rules
        """
        original_term = term
        disambiguation_source = 'UMLS_direct'

        # Layer 1: NeuroDB abbreviation expansion
        if term.lower() in self.abbreviations:
            term = self.abbreviations[term.lower()]
            disambiguation_source = 'NeuroDB'

        # Layer 2: UMLS 7-category classification
        result = self.umls_client.classify_term(term)

        # Get category-specific expansion rule
        category_enum = result.get('category_enum', self._SemanticCategory.UNKNOWN)
        expansion_rule = self._get_expansion_rule(category_enum)

        # Enhance result with expansion metadata
        result['original_term'] = original_term
        result['disambiguation_source'] = disambiguation_source
        result['expansion_rule'] = {
            'strategy': expansion_rule.strategy.value,
            'max_expansions': expansion_rule.max_expansions,
            'include_types': expansion_rule.include_types,
            'exclude_types': expansion_rule.exclude_types,
        }

        # Apply confidence based on source
        if disambiguation_source == 'NeuroDB':
            result['confidence'] = 0.95
        elif result.get('cui'):
            result['confidence'] = 0.8
        else:
            result['confidence'] = 0.3

        return result

    def get_filtered_synonyms(self, classification):
        """
        Get synonyms filtered by category-specific anti-drift rules.

        Args:
            classification: Result from classify_term()

        Returns:
            List of filtered synonyms (respects max_expansions)
        """
        if not classification.get('cui'):
            return []

        category_enum = classification.get('category_enum', self._SemanticCategory.UNKNOWN)
        max_syns = classification.get('expansion_rule', {}).get('max_expansions', 5)

        # Get raw synonyms from UMLS
        raw_synonyms = self.umls_client.get_synonyms(
            classification['cui'],
            max_synonyms=max_syns * 2  # Get extra for filtering
        )

        # Filter using category-specific anti-drift patterns
        filtered = self._filter_by_category(raw_synonyms, category_enum)

        return filtered[:max_syns]

    def _classify_terms_batch(self, terms):
        """Batch classification - wraps classify_term for pipeline callback."""
        return [self.classify_term(t) for t in terms]

    def run(self, user_input, days=60, max_results=20, verbose=False):
        """
        Execute semantic pipeline with 7-category classification.

        Uses category-aware expansion rules to prevent semantic drift.
        """
        from poc_api_first.poc_pipeline import SemanticQueryPipeline

        pipeline = SemanticQueryPipeline(
            umls_client=self.umls_client,
            pubmed_client=None,    # Use default
            pubtator_client=None,  # Not used in Phase 1
            classify_fn=self._classify_terms_batch
        )
        return pipeline.run(
            user_input=user_input,
            days=days,
            max_results=max_results,
            verbose=verbose
        )


# MVP Configuration Set (6 configs for comparison testing)
MVP_CONFIGURATIONS = [
    # LexStream2BaselineConfig,  # Reference only - requires Lex Stream 2 implementation
    NeuroDBOnlyConfig,            # Single-layer: NeuroDB abbreviation expansion only
    UMLSOnlyConfig,               # Single-layer: UMLS semantic classification only
    PubTatorOnlyConfig,           # Single-layer: PubTator disambiguation only
    UMLSPubTatorConfig,           # Two-layer: UMLS + PubTator (proven POC)
    FullHybridConfig,             # Three-layer: NeuroDB + PubTator + UMLS
    SemanticClassificationConfig  # NEW: 7-category with anti-drift (Phase 1)
]

# Full Configuration Set (for comprehensive testing when all implementations ready)
ALL_CONFIGURATIONS = [
    LexStream2BaselineConfig,
    NeuroDBOnlyConfig,
    UMLSOnlyConfig,
    PubTatorOnlyConfig,
    UMLSPubTatorConfig,
    FullHybridConfig,
    SemanticClassificationConfig  # NEW: 7-category with anti-drift (Phase 1)
]
