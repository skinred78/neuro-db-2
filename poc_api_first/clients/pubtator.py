"""
PubTator 3.0 API Client

AI-powered biomedical concept extraction.
9 entity types: gene, disease, chemical, species, variant, cell line, cell type, DNA, RNA
12 relation types: association, cause, treatment, inhibition, etc.
"""

import requests
from typing import List, Dict, Optional


class PubTatorClient:
    """Client for PubTator 3.0 API (NCBI)."""
    
    BASE_URL = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api"
    
    # Entity type to Lex Stream category mapping
    ENTITY_CATEGORY_MAP = {
        'Disease': 'CONDITION',
        'Chemical': 'INTERVENTION',  # Often drugs/compounds
        'Gene': 'OTHER',  # Could be target or biomarker
        'Species': 'OTHER',
        'Variant': 'OTHER',
        'CellLine': 'OTHER',
        'CellType': 'ANATOMY',
        'DNA': 'OTHER',
        'RNA': 'OTHER',
    }
    
    def __init__(self):
        """Initialize PubTator client (no API key required)."""
        pass

    def autocomplete(
        self,
        query: str,
        concept: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find entity matches using autocomplete.

        This is KEY for abbreviation disambiguation!
        E.g., "MS" with concept="disease" → "Multiple Sclerosis"

        Args:
            query: Search term (can be abbreviation like "MS")
            concept: Filter by type: disease, chemical, gene, variant, species, cellline
            limit: Max results to return

        Returns:
            List of matching entities with name, type, and ID
        """
        endpoint = f"{self.BASE_URL}/entity/autocomplete/"

        params = {
            "query": query,
            "limit": limit
        }
        if concept:
            params["concept"] = concept

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"PubTator autocomplete error: {e}")
            return []

    def disambiguate_term(self, term: str) -> Dict:
        """
        Attempt to disambiguate an abbreviation or ambiguous term.

        Tries disease first, then chemical, then general search.
        Returns the best match with its type.

        Args:
            term: Term to disambiguate (e.g., "MS", "TMS")

        Returns:
            {
                'original': str,
                'resolved': str,  # Full name if found
                'type': str,  # disease, chemical, gene, etc.
                'confidence': float
            }
        """
        # Try disease first (most common in neuroscience)
        disease_matches = self.autocomplete(term, concept="disease", limit=3)
        if disease_matches:
            best = disease_matches[0]
            return {
                'original': term,
                'resolved': best.get('name', term),
                'type': 'disease',
                'confidence': 0.9 if term.upper() in best.get('name', '').upper() else 0.7
            }

        # Try chemical (drugs, compounds)
        chemical_matches = self.autocomplete(term, concept="chemical", limit=3)
        if chemical_matches:
            best = chemical_matches[0]
            return {
                'original': term,
                'resolved': best.get('name', term),
                'type': 'chemical',
                'confidence': 0.8
            }

        # Try general search
        general_matches = self.autocomplete(term, limit=3)
        if general_matches:
            best = general_matches[0]
            return {
                'original': term,
                'resolved': best.get('name', term),
                'type': best.get('type', 'unknown'),
                'confidence': 0.6
            }

        # No match found
        return {
            'original': term,
            'resolved': term,
            'type': 'unknown',
            'confidence': 0.0
        }

    def recognize_entities(self, text: str) -> List[Dict]:
        """
        Extract biomedical entities from free text.
        
        Args:
            text: Free text to analyze (e.g., "MS treatment with neuromodulation")
            
        Returns:
            List of entities:
            [
                {
                    'text': str,  # Matched text
                    'type': str,  # Disease, Chemical, Gene, etc.
                    'start': int,  # Character offset
                    'end': int,
                    'id': str  # Database ID (e.g., MESH:D009103)
                }
            ]
        """
        endpoint = f"{self.BASE_URL}/annotations/annotate/submit/text"
        
        # PubTator expects specific format
        payload = {
            "text": text,
            "return_type": "json"
        }
        
        try:
            response = requests.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract entities from response
            entities = []
            for passage in data.get('passages', []):
                for annotation in passage.get('annotations', []):
                    entities.append({
                        'text': annotation.get('text', ''),
                        'type': annotation.get('infons', {}).get('type', 'Unknown'),
                        'start': annotation.get('locations', [{}])[0].get('offset', 0),
                        'end': annotation.get('locations', [{}])[0].get('offset', 0) + 
                               annotation.get('locations', [{}])[0].get('length', 0),
                        'id': annotation.get('infons', {}).get('identifier', '')
                    })
            
            return entities
            
        except requests.exceptions.RequestException as e:
            print(f"PubTator API error: {e}")
            return []
    
    def annotate_pmids(self, pmids: List[str], concepts: Optional[List[str]] = None) -> Dict:
        """
        Get annotations for specific PubMed articles.
        
        Args:
            pmids: List of PubMed IDs
            concepts: Optional filter for concept types (e.g., ['gene', 'disease'])
            
        Returns:
            Dictionary mapping PMID to list of entities
        """
        endpoint = f"{self.BASE_URL}/publications/export/biocjson"
        
        params = {
            "pmids": ",".join(pmids)
        }
        
        if concepts:
            params["concepts"] = ",".join(concepts)
        
        try:
            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse results by PMID
            results = {}
            for pub in data.get('PubTator3', []):
                pmid = pub.get('pmid', '')
                entities = []
                
                for passage in pub.get('passages', []):
                    for annotation in passage.get('annotations', []):
                        entities.append({
                            'text': annotation.get('text', ''),
                            'type': annotation.get('infons', {}).get('type', 'Unknown'),
                            'id': annotation.get('infons', {}).get('identifier', '')
                        })
                
                results[pmid] = entities
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"PubTator API error: {e}")
            return {}
    
    def search_relations(
        self, 
        entity1: str, 
        entity2: Optional[str] = None,
        relation_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for relations between entities in PubMed literature.
        
        Args:
            entity1: First entity (required)
            entity2: Second entity (optional, for specific pairs)
            relation_type: Filter by relation type (e.g., "treatment", "association")
            
        Returns:
            List of relation records with PMIDs and entity pairs
        """
        endpoint = f"{self.BASE_URL}/search/"
        
        # Build query
        query = entity1
        if entity2:
            query = f"{entity1} {entity2}"
        
        params = {
            "text": query,
            "type": "relation" if relation_type else "entity"
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json().get('results', [])
            
        except requests.exceptions.RequestException as e:
            print(f"PubTator API error: {e}")
            return []
    
    def classify_entities(self, text: str) -> List[Dict]:
        """
        Extract and classify entities from text into Lex Stream categories.
        
        Args:
            text: Free text to analyze
            
        Returns:
            List of classified entities:
            [
                {
                    'text': str,
                    'type': str,  # PubTator type
                    'category': str,  # CONDITION, INTERVENTION, etc.
                    'id': str
                }
            ]
        """
        entities = self.recognize_entities(text)
        
        classified = []
        for entity in entities:
            entity_type = entity.get('type', 'Unknown')
            category = self.ENTITY_CATEGORY_MAP.get(entity_type, 'OTHER')
            
            classified.append({
                'text': entity['text'],
                'type': entity_type,
                'category': category,
                'id': entity.get('id', '')
            })
        
        return classified


# Quick test
if __name__ == "__main__":
    client = PubTatorClient()
    
    print("PubTator Entity Recognition Test")
    print("=" * 60)
    
    # Test entity extraction
    test_texts = [
        "MS treatment with neuromodulation",
        "Multiple sclerosis patients receiving transcranial magnetic stimulation",
        "TMS improves motor function in Parkinson's disease"
    ]
    
    for text in test_texts:
        print(f"\nText: {text}")
        entities = client.classify_entities(text)
        
        if entities:
            for e in entities:
                print(f"  - {e['text']}: {e['type']} ({e['category']})")
        else:
            print("  No entities detected (API may need longer text)")
