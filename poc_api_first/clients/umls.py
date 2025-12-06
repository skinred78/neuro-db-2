"""
UMLS Metathesaurus API Client

Provides semantic type classification for biomedical terms.
127 semantic types mapped to 7 neuroscience-relevant categories.

Reference: poc_api_first/semantic_types.py for full TUI mapping
"""

import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

from poc_api_first.semantic_types import (
    SemanticCategory,
    get_category_from_tui,
    get_semantic_group,
    TUI_TO_SEMANTIC_GROUP,
    CATEGORY_DISPLAY_NAMES,
)
from poc_api_first.expansion_rules import (
    get_expansion_rule,
    get_max_expansions,
    filter_by_category,
    ExpansionStrategy,
)

load_dotenv()


class UMLSClient:
    """Client for UMLS Terminology Services API with 7-category classification."""

    BASE_URL = "https://uts-ws.nlm.nih.gov/rest"

    # Legacy mapping for backwards compatibility (deprecated)
    # Use get_category_from_tui() from semantic_types.py instead
    CATEGORY_MAP = {
        # CONDITION_DISEASE
        'T047': 'CONDITION_DISEASE',
        'T048': 'CONDITION_DISEASE',
        'T184': 'CONDITION_DISEASE',
        'T046': 'CONDITION_DISEASE',
        'T191': 'CONDITION_DISEASE',
        'T037': 'CONDITION_DISEASE',
        'T049': 'CONDITION_DISEASE',
        'T050': 'CONDITION_DISEASE',
        'T190': 'CONDITION_DISEASE',

        # INTERVENTION_EXPOSURE (procedures + drugs)
        'T061': 'INTERVENTION_EXPOSURE',
        'T060': 'INTERVENTION_EXPOSURE',
        'T058': 'INTERVENTION_EXPOSURE',
        'T059': 'INTERVENTION_EXPOSURE',
        'T062': 'INTERVENTION_EXPOSURE',
        'T063': 'INTERVENTION_EXPOSURE',
        'T121': 'INTERVENTION_EXPOSURE',
        'T200': 'INTERVENTION_EXPOSURE',
        'T195': 'INTERVENTION_EXPOSURE',

        # OUTCOME_MEASURE (physiology + phenomena)
        'T042': 'OUTCOME_MEASURE',
        'T039': 'OUTCOME_MEASURE',
        'T033': 'OUTCOME_MEASURE',
        'T034': 'OUTCOME_MEASURE',
        'T040': 'OUTCOME_MEASURE',
        'T041': 'OUTCOME_MEASURE',
        'T032': 'OUTCOME_MEASURE',
        'T043': 'OUTCOME_MEASURE',
        'T044': 'OUTCOME_MEASURE',
        'T045': 'OUTCOME_MEASURE',

        # ANATOMY_SYSTEM
        'T017': 'ANATOMY_SYSTEM',
        'T018': 'ANATOMY_SYSTEM',
        'T021': 'ANATOMY_SYSTEM',
        'T022': 'ANATOMY_SYSTEM',
        'T023': 'ANATOMY_SYSTEM',
        'T024': 'ANATOMY_SYSTEM',
        'T025': 'ANATOMY_SYSTEM',
        'T026': 'ANATOMY_SYSTEM',
        'T029': 'ANATOMY_SYSTEM',
        'T030': 'ANATOMY_SYSTEM',
        'T031': 'ANATOMY_SYSTEM',

        # MECHANISM_BIOLOGICAL (genes + concepts)
        'T028': 'MECHANISM_BIOLOGICAL',
        'T085': 'MECHANISM_BIOLOGICAL',
        'T086': 'MECHANISM_BIOLOGICAL',
        'T087': 'MECHANISM_BIOLOGICAL',
        'T088': 'MECHANISM_BIOLOGICAL',
        'T116': 'MECHANISM_BIOLOGICAL',
        'T123': 'MECHANISM_BIOLOGICAL',
        'T124': 'MECHANISM_BIOLOGICAL',
        'T125': 'MECHANISM_BIOLOGICAL',
        'T126': 'MECHANISM_BIOLOGICAL',

        # OBJECT_DEVICE
        'T074': 'OBJECT_DEVICE',
        'T075': 'OBJECT_DEVICE',
        'T071': 'OBJECT_DEVICE',
        'T072': 'OBJECT_DEVICE',
        'T073': 'OBJECT_DEVICE',

        # POPULATION_CONTEXT (living beings + activities)
        'T016': 'POPULATION_CONTEXT',
        'T096': 'POPULATION_CONTEXT',
        'T097': 'POPULATION_CONTEXT',
        'T098': 'POPULATION_CONTEXT',
        'T099': 'POPULATION_CONTEXT',
        'T100': 'POPULATION_CONTEXT',
        'T101': 'POPULATION_CONTEXT',
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("UMLS_API_KEY")
        if not self.api_key:
            raise ValueError("UMLS_API_KEY not found. Set it in .env or pass directly.")
    
    def search_concept(self, term: str, page_size: int = 10) -> List[Dict]:
        """
        Search for UMLS concepts by term string.
        
        Args:
            term: The term to search for (e.g., "multiple sclerosis")
            page_size: Number of results to return
            
        Returns:
            List of concept matches with CUI, name, and semantic types
        """
        endpoint = f"{self.BASE_URL}/search/current"
        params = {
            "string": term,
            "apiKey": self.api_key,
            "returnIdType": "concept",
            "pageSize": page_size,
            "inputType": "atom",
            "searchType": "words"
        }
        
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get('result', {}).get('results', [])
    
    def get_concept_details(self, cui: str) -> Dict:
        """
        Get full details for a concept by CUI.
        
        Args:
            cui: Concept Unique Identifier (e.g., "C0026769")
            
        Returns:
            Concept details including name, semantic types, definitions
        """
        endpoint = f"{self.BASE_URL}/content/current/CUI/{cui}"
        params = {"apiKey": self.api_key}
        
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        
        return response.json().get('result', {})
    
    def get_semantic_types(self, cui: str) -> List[Dict]:
        """
        Get semantic types for a concept.
        
        Args:
            cui: Concept Unique Identifier
            
        Returns:
            List of semantic types (e.g., [{"name": "Disease or Syndrome", "uri": "...T047"}])
        """
        details = self.get_concept_details(cui)
        return details.get('semanticTypes', [])
    
    def get_atoms(self, cui: str, page_size: int = 25) -> List[Dict]:
        """
        Get atoms (synonyms/alternative names) for a concept.
        
        Args:
            cui: Concept Unique Identifier
            page_size: Number of atoms to return
            
        Returns:
            List of atoms with name, source vocabulary, etc.
        """
        endpoint = f"{self.BASE_URL}/content/current/CUI/{cui}/atoms"
        params = {
            "apiKey": self.api_key,
            "pageSize": page_size
        }
        
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        
        return response.json().get('result', [])
    
    def get_synonyms(self, cui: str, max_synonyms: int = 25) -> List[str]:
        """
        Get unique synonym names for a concept.
        
        Args:
            cui: Concept Unique Identifier
            max_synonyms: Maximum number of synonyms to return
            
        Returns:
            List of unique synonym strings
        """
        atoms = self.get_atoms(cui, page_size=max_synonyms)
        
        # Extract unique names
        synonyms = []
        seen = set()
        for atom in atoms:
            name = atom.get('name', '')
            name_lower = name.lower()
            if name_lower not in seen:
                synonyms.append(name)
                seen.add(name_lower)
        
        return synonyms[:max_synonyms]
    
    def classify_term(self, term: str) -> Dict:
        """
        Classify a term into 7 semantic categories.

        Uses the full 127 TUI mapping via semantic_types.py.

        Args:
            term: The term to classify (e.g., "neuromodulation")

        Returns:
            {
                'term': str,
                'cui': str or None,
                'name': str,  # Official UMLS name
                'semantic_types': List[str],  # Human-readable type names
                'tuis': List[str],  # Type unique identifiers
                'semantic_groups': List[str],  # UMLS semantic group codes
                'category': str,  # One of 7 categories or UNKNOWN
                'category_enum': SemanticCategory,  # Enum value
                'expansion_strategy': str,  # narrow/moderate/broad
                'max_expansions': int,  # Max synonyms to use
                'confidence': float  # 0-1 confidence score
            }
        """
        # Search for the term
        concepts = self.search_concept(term)

        if not concepts:
            return {
                'term': term,
                'cui': None,
                'name': term,
                'semantic_types': [],
                'tuis': [],
                'semantic_groups': [],
                'category': 'UNKNOWN',
                'category_enum': SemanticCategory.UNKNOWN,
                'expansion_strategy': 'minimal',
                'max_expansions': 2,
                'confidence': 0.0
            }

        # Take the best match (first result)
        concept = concepts[0]
        cui = concept.get('ui')
        name = concept.get('name', term)

        # Get semantic types
        sem_types = self.get_semantic_types(cui)

        # Extract TUIs, names, and semantic groups
        tuis = []
        type_names = []
        sem_groups = []
        for st in sem_types:
            uri = st.get('uri', '')
            tui = uri.split('/')[-1] if '/' in uri else ''
            tuis.append(tui)
            type_names.append(st.get('name', ''))
            # Get semantic group for this TUI
            sg = get_semantic_group(tui)
            if sg and sg not in sem_groups:
                sem_groups.append(sg)

        # Determine category from first matching TUI using new 7-category system
        category_enum = SemanticCategory.UNKNOWN
        for tui in tuis:
            cat = get_category_from_tui(tui)
            if cat != SemanticCategory.UNKNOWN:
                category_enum = cat
                break

        # Get expansion rules for this category
        expansion_rule = get_expansion_rule(category_enum)

        # Calculate confidence based on match quality
        confidence = 0.8 if term.lower() in name.lower() else 0.6

        return {
            'term': term,
            'cui': cui,
            'name': name,
            'semantic_types': type_names,
            'tuis': tuis,
            'semantic_groups': sem_groups,
            'category': category_enum.value,
            'category_enum': category_enum,
            'expansion_strategy': expansion_rule.strategy.value,
            'max_expansions': expansion_rule.max_expansions,
            'confidence': confidence
        }

    def classify_term_with_filtered_synonyms(self, term: str) -> Dict:
        """
        Classify term and get filtered synonyms based on category rules.

        Combines classification with category-aware synonym filtering.

        Args:
            term: The term to classify

        Returns:
            Classification dict + 'filtered_synonyms' list
        """
        classification = self.classify_term(term)

        if classification['cui']:
            # Get raw synonyms from UMLS
            raw_synonyms = self.get_synonyms(
                classification['cui'],
                max_synonyms=classification['max_expansions'] * 2
            )
            # Filter using category-specific anti-drift patterns
            filtered = filter_by_category(raw_synonyms, classification['category_enum'])
            # Limit to max for this category
            classification['filtered_synonyms'] = filtered[:classification['max_expansions']]
        else:
            classification['filtered_synonyms'] = []

        return classification


# Quick test
if __name__ == "__main__":
    client = UMLSClient()

    # Test 7-category classification
    test_terms = [
        "multiple sclerosis",   # CONDITION_DISEASE
        "neuromodulation",      # INTERVENTION_EXPOSURE
        "motor function",       # OUTCOME_MEASURE
        "hippocampus",          # ANATOMY_SYSTEM
        "dopamine",             # MECHANISM_BIOLOGICAL
        "electrode",            # OBJECT_DEVICE
        "elderly",              # POPULATION_CONTEXT
    ]

    print("UMLS 7-Category Classification Test")
    print("=" * 70)

    for term in test_terms:
        result = client.classify_term(term)
        print(f"\nTerm: {term}")
        print(f"  CUI: {result['cui']}")
        print(f"  Name: {result['name']}")
        print(f"  Category: {result['category']}")
        print(f"  Semantic Groups: {result['semantic_groups']}")
        print(f"  Expansion: {result['expansion_strategy']} (max: {result['max_expansions']})")
        print(f"  Confidence: {result['confidence']:.2f}")
