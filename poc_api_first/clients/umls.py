"""
UMLS Metathesaurus API Client

Provides semantic type classification for biomedical terms.
135 semantic types available (T047=Disease, T061=Therapeutic Procedure, etc.)
"""

import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class UMLSClient:
    """Client for UMLS Terminology Services API."""
    
    BASE_URL = "https://uts-ws.nlm.nih.gov/rest"
    
    # Semantic type to category mapping
    CATEGORY_MAP = {
        # Conditions (diseases, symptoms, findings)
        'T047': 'CONDITION',  # Disease or Syndrome
        'T048': 'CONDITION',  # Mental or Behavioral Dysfunction
        'T184': 'CONDITION',  # Sign or Symptom
        'T046': 'CONDITION',  # Pathologic Function
        'T191': 'CONDITION',  # Neoplastic Process
        
        # Interventions (procedures, drugs, devices)
        'T061': 'INTERVENTION',  # Therapeutic or Preventive Procedure
        'T060': 'INTERVENTION',  # Diagnostic Procedure
        'T121': 'INTERVENTION',  # Pharmacologic Substance
        'T200': 'INTERVENTION',  # Clinical Drug
        'T074': 'INTERVENTION',  # Medical Device
        'T062': 'INTERVENTION',  # Research Activity (includes research interventions)
        
        # Outcomes (functions, findings, lab results)
        'T042': 'OUTCOME',  # Organ or Tissue Function
        'T039': 'OUTCOME',  # Physiologic Function
        'T033': 'OUTCOME',  # Finding
        'T034': 'OUTCOME',  # Laboratory or Test Result
        'T040': 'OUTCOME',  # Organism Function
        'T041': 'OUTCOME',  # Mental Process
        
        # Anatomy
        'T023': 'ANATOMY',  # Body Part, Organ, or Organ Component
        'T024': 'ANATOMY',  # Tissue
        'T025': 'ANATOMY',  # Cell
        'T029': 'ANATOMY',  # Body Location or Region
        'T030': 'ANATOMY',  # Body Space or Junction
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
        Classify a term into semantic categories.
        
        This is the main method for the POC - determines if a term
        is a CONDITION, INTERVENTION, OUTCOME, ANATOMY, or OTHER.
        
        Args:
            term: The term to classify (e.g., "neuromodulation")
            
        Returns:
            {
                'term': str,
                'cui': str or None,
                'name': str,  # Official UMLS name
                'semantic_types': List[str],  # Human-readable type names
                'tuis': List[str],  # Type unique identifiers
                'category': str,  # CONDITION, INTERVENTION, OUTCOME, ANATOMY, OTHER
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
                'category': 'UNKNOWN',
                'confidence': 0.0
            }
        
        # Take the best match (first result)
        concept = concepts[0]
        cui = concept.get('ui')
        name = concept.get('name', term)
        
        # Get semantic types
        sem_types = self.get_semantic_types(cui)
        
        # Extract TUIs and names
        tuis = []
        type_names = []
        for st in sem_types:
            uri = st.get('uri', '')
            tui = uri.split('/')[-1] if '/' in uri else ''
            tuis.append(tui)
            type_names.append(st.get('name', ''))
        
        # Determine category from first matching TUI
        category = 'OTHER'
        for tui in tuis:
            if tui in self.CATEGORY_MAP:
                category = self.CATEGORY_MAP[tui]
                break
        
        # Calculate confidence based on match quality
        # Higher confidence if exact match or if term appears in name
        confidence = 0.8 if term.lower() in name.lower() else 0.6
        
        return {
            'term': term,
            'cui': cui,
            'name': name,
            'semantic_types': type_names,
            'tuis': tuis,
            'category': category,
            'confidence': confidence
        }


# Quick test
if __name__ == "__main__":
    client = UMLSClient()
    
    # Test classification
    test_terms = ["multiple sclerosis", "neuromodulation", "motor function", "TMS"]
    
    print("UMLS Classification Test")
    print("=" * 60)
    
    for term in test_terms:
        result = client.classify_term(term)
        print(f"\nTerm: {term}")
        print(f"  CUI: {result['cui']}")
        print(f"  Name: {result['name']}")
        print(f"  Category: {result['category']}")
        print(f"  Semantic Types: {result['semantic_types']}")
        print(f"  Confidence: {result['confidence']:.2f}")
