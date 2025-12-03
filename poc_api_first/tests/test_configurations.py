"""
Test configurations for semantic query pipeline evaluation.

Defines capability matrix and configuration classes for comparing tool combinations.
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
    'UMLSOnly': {
        'supports_semantic_classification': True,
        'supports_abbreviation_expansion': False,
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
        # Step 1: PubTator disambiguation
        if self.is_abbreviation(term):
            disambiguation = self.pubtator_client.disambiguate_term(term)
            if disambiguation['confidence'] > 0.5:
                term = disambiguation['resolved']

        # Step 2: UMLS classification
        return self.umls_client.classify_term(term)


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
            self.neurodb = json.load(f)

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
        # Layer 1: NeuroDB-2 (neuroscience-specific - highest priority)
        if term.lower() in self.neurodb.get('abbreviations', {}):
            resolved = self.neurodb['abbreviations'][term.lower()]['expansion']
            result = self.umls_client.classify_term(resolved)
            result['disambiguation_source'] = 'NeuroDB'
            result['confidence'] = 1.0
            return result

        # Layer 2: PubTator (biomedical general)
        if self.is_abbreviation(term):
            disambiguation = self.pubtator_client.disambiguate_term(term)
            if disambiguation['confidence'] > 0.5:
                resolved = disambiguation['resolved']
                result = self.umls_client.classify_term(resolved)
                result['disambiguation_source'] = 'PubTator'
                result['confidence'] = disambiguation['confidence'] * 0.9
                return result

        # Layer 3: UMLS direct lookup (fallback)
        result = self.umls_client.classify_term(term)
        result['disambiguation_source'] = 'UMLS_direct'
        result['confidence'] = 0.5
        return result


# MVP Configuration Set (3 configs for initial testing)
MVP_CONFIGURATIONS = [
    # LexStream2BaselineConfig,  # Reference only - requires Lex Stream 2 implementation
    UMLSPubTatorConfig,           # Proven POC
    FullHybridConfig              # Full hybrid with NeuroDB-2
]

# Full Configuration Set (for comprehensive testing when all implementations ready)
ALL_CONFIGURATIONS = [
    LexStream2BaselineConfig,
    UMLSPubTatorConfig,
    FullHybridConfig
]
