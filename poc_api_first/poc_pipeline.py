"""
Semantic Query Pipeline - POC

Combines UMLS, PubTator, and PubMed APIs to:
1. Parse user input into terms
2. Classify each term semantically (CONDITION, INTERVENTION, OUTCOME)
3. Build smart PubMed query based on categories
4. Execute search and return results

This is the core of the API-first approach test.
"""

import re
import time
import json
from typing import List, Dict, Tuple, Callable, Optional
from poc_api_first.clients.umls import UMLSClient
from poc_api_first.clients.pubmed import PubMedClient
from poc_api_first.clients.pubtator import PubTatorClient


class SemanticQueryPipeline:
    """POC pipeline for API-first semantic query expansion.

    Supports optional client injection and custom classification callbacks
    for integration with different tool configurations.
    """

    # Stop words to filter from input
    STOP_WORDS = {
        'with', 'and', 'or', 'the', 'a', 'an', 'in', 'on', 'for',
        'to', 'of', 'treatment', 'therapy', 'using', 'by'
    }

    # Expansion strategies by category
    EXPANSION_STRATEGY = {
        'CONDITION': 'narrow',     # Just synonyms, MeSH term
        'INTERVENTION': 'broad',   # Include related techniques
        'OUTCOME': 'moderate',     # Some related measures
        'ANATOMY': 'narrow',       # Specific terms only
        'OTHER': 'narrow',
        'UNKNOWN': 'narrow'
    }

    def __init__(
        self,
        umls_client: Optional[UMLSClient] = None,
        pubmed_client: Optional[PubMedClient] = None,
        pubtator_client: Optional[PubTatorClient] = None,
        classify_fn: Optional[Callable[[List[str]], List[Dict]]] = None
    ):
        """
        Initialize pipeline with optional client injection.

        Args:
            umls_client: UMLSClient instance (creates default if None AND no classify_fn)
            pubmed_client: PubMedClient instance (creates default if None)
            pubtator_client: PubTatorClient instance (creates default if None AND no classify_fn)
            classify_fn: Custom classification function (uses self.classify_terms if None)
                         Signature: classify_fn(terms: List[str]) -> List[Dict]
                         MUST return records matching CLASSIFICATION_SCHEMA
                         When provided, UMLS/PubTator clients are optional.
        """
        self._custom_classify_fn = classify_fn

        # Only create default UMLS/PubTator clients if no custom classify_fn
        # Custom classify_fn may not need these APIs (e.g., NeuroDBOnlyConfig)
        if classify_fn is None:
            self.umls = umls_client if umls_client is not None else UMLSClient()
            self.pubtator = pubtator_client if pubtator_client is not None else PubTatorClient()
        else:
            self.umls = umls_client  # May be None - custom classify_fn handles classification
            self.pubtator = pubtator_client  # May be None

        # PubMed client always needed for search
        self.pubmed = pubmed_client if pubmed_client is not None else PubMedClient()

        # API call tracking for cost/usage analysis
        self.api_call_counts = {'umls': 0, 'pubtator': 0, 'pubmed': 0}

    def _normalize_classification(self, raw: Dict, original_term: str) -> Dict:
        """
        Normalize classification output to ensure all required keys present.

        CRITICAL FIX: Pipeline calls this AFTER custom classify_fn returns
        to guarantee build_query() and expand_term() have required keys.

        Args:
            raw: Raw classification dict from custom classify_fn
            original_term: The original input term

        Returns:
            Normalized dict with all required keys
        """
        return {
            # Required - with defaults
            'term': raw.get('term', original_term),
            'original_term': raw.get('original_term', original_term),
            'category': raw.get('category', 'UNKNOWN'),
            'expansion_strategy': self.EXPANSION_STRATEGY.get(
                raw.get('category', 'UNKNOWN'), 'narrow'
            ),

            # Optional - pass through
            'cui': raw.get('cui'),
            'name': raw.get('name', raw.get('term', original_term)),
            'semantic_types': raw.get('semantic_types', []),

            # Disambiguation metadata - unified keys
            'disambiguation_source': raw.get('disambiguation_source', 'unknown'),
            'disambiguation_used': raw.get('disambiguation_used',
                raw.get('disambiguation_source', '') not in ['UMLS_direct', 'unknown', '']),
            'confidence': raw.get('confidence', 0.5),
        }
    
    def parse_input(self, user_input: str) -> List[str]:
        """
        Parse user input into individual terms.

        Handles:
        - "MS + neuromodulation" -> ["ms", "neuromodulation"]
        - "TMS, stroke, memory" -> ["tms", "stroke", "memory"]
        - "fMRI motor cortex" -> ["fmri", "motor cortex"]  # PRESERVES phrase!
        - "Parkinson's DBS motor" -> ["parkinson's", "dbs", "motor"]

        Strategy:
        1. Split on explicit delimiters (+, comma, and) - DON'T lowercase yet
        2. For each phrase, identify abbreviations BEFORE lowercasing
        3. Group contiguous non-abbreviations as multi-word terms
        4. Filter stop words

        Args:
            user_input: Raw user query

        Returns:
            List of terms to classify
        """
        text = user_input.strip()  # DON'T lowercase yet - need case for abbreviation detection!

        # Step 1: Normalize explicit delimiters to pipe
        text = re.sub(r'\s*\+\s*', ' | ', text)      # "+" separator
        text = re.sub(r'\s*,\s*', ' | ', text)       # "," separator
        text = re.sub(r'\s+and\s+', ' | ', text, flags=re.IGNORECASE)  # "and" separator

        # Step 2: Split into candidate phrases
        parts = [p.strip() for p in text.split('|') if p.strip()]

        # Step 3: Process each phrase - split around abbreviations, keep others together
        expanded_parts = []
        for part in parts:
            words = part.split()

            # For single or two-word phrases without abbreviations, keep as-is
            if len(words) <= 2 and not any(self._is_abbreviation(w) for w in words):
                expanded_parts.append(part.lower())
                continue

            # For phrases with abbreviations, split around them
            # Group contiguous non-abbreviations together
            current_group = []
            for word in words:
                if self._is_abbreviation(word):
                    # Flush current group first
                    if current_group:
                        expanded_parts.append(' '.join(current_group).lower())
                        current_group = []
                    # Add abbreviation as separate term
                    expanded_parts.append(word.lower())
                else:
                    current_group.append(word)

            # Flush remaining group
            if current_group:
                expanded_parts.append(' '.join(current_group).lower())

        # Step 4: Filter stop words
        terms = []
        for part in expanded_parts:
            words = part.split()
            filtered = [w for w in words if w not in self.STOP_WORDS]
            if filtered:
                term = ' '.join(filtered)
                terms.append(term)

        return terms

    def _is_abbreviation(self, word: str) -> bool:
        """
        Check if word is likely an abbreviation.

        MUST be called BEFORE lowercasing to detect uppercase patterns.

        Heuristics:
        - All uppercase and <= 6 chars (TMS, DBS, RCT, MS, EEG)
        - Mixed case with uppercase after first char (fMRI, rTMS)

        Args:
            word: Word to check (original case)

        Returns:
            True if likely abbreviation
        """
        # All caps (TMS, DBS, RCT, MS, EEG)
        if word.isupper() and len(word) <= 6:
            return True

        # Mixed case with uppercase after first char (fMRI, rTMS, MEG)
        if len(word) >= 2 and any(c.isupper() for c in word[1:]):
            return True

        return False
    
    def classify_terms(self, terms: List[str]) -> List[Dict]:
        """
        Classify each term using PubTator + UMLS APIs.

        If custom classify_fn was provided at init, uses that instead and
        normalizes the output to ensure all required keys are present.

        NEW: Attempts PubTator disambiguation for abbreviations first!
        E.g., "MS" → "Multiple Sclerosis" → UMLS classification

        Args:
            terms: List of terms to classify

        Returns:
            List of classification results (normalized to CLASSIFICATION_SCHEMA)
        """
        # Use custom classification if provided
        if self._custom_classify_fn is not None:
            raw_results = self._custom_classify_fn(terms)
            # CRITICAL: Normalize to ensure required keys for build_query/expand_term
            return [
                self._normalize_classification(raw, term)
                for raw, term in zip(raw_results, terms)
            ]

        # Original POC implementation (2-layer: PubTator → UMLS)
        classifications = []

        for term in terms:
            # Step 1: Check if term might be an abbreviation (short, all caps, etc.)
            is_likely_abbreviation = (
                len(term) <= 5 or  # Short terms
                term.isupper() or  # All caps like "MS", "TMS"
                (len(term.split()) == 1 and len(term) <= 10)  # Single short word
            )

            resolved_term = term
            disambiguation_used = False

            # Step 2: If likely abbreviation, try PubTator disambiguation
            if is_likely_abbreviation:
                disambiguation = self.pubtator.disambiguate_term(term)
                self.api_call_counts['pubtator'] += 1  # Track PubTator API call
                if disambiguation['confidence'] > 0.5:
                    resolved_term = disambiguation['resolved']
                    disambiguation_used = True
                    print(f"   [PubTator] Resolved '{term}' → '{resolved_term}' ({disambiguation['type']}, conf={disambiguation['confidence']:.2f})")

            # Step 3: Classify with UMLS (using resolved term)
            result = self.umls.classify_term(resolved_term)
            self.api_call_counts['umls'] += 1  # Track UMLS classify API call

            # Step 4: Add disambiguation metadata
            result['original_term'] = term
            result['disambiguation_used'] = disambiguation_used
            if disambiguation_used:
                result['pubtator_type'] = disambiguation['type']
                result['pubtator_confidence'] = disambiguation['confidence']

            # Step 5: Add expansion strategy based on category
            result['expansion_strategy'] = self.EXPANSION_STRATEGY.get(
                result['category'], 'narrow'
            )

            classifications.append(result)

            # Rate limiting (UMLS allows 20 req/s)
            time.sleep(0.1)

        return classifications
    
    def expand_term(self, classification: Dict) -> List[str]:
        """
        Expand a term based on its category and strategy.
        
        Args:
            classification: Classification result from classify_terms
            
        Returns:
            List of expanded terms (synonyms, related terms)
        """
        cui = classification.get('cui')
        strategy = classification.get('expansion_strategy', 'narrow')
        original_term = classification.get('term', '')
        
        if not cui:
            return [original_term]
        
        try:
            synonyms = self.umls.get_synonyms(cui)
            self.api_call_counts['umls'] += 1  # Track UMLS get_synonyms API call

            if strategy == 'narrow':
                # Top 3 synonyms only
                return synonyms[:3] if synonyms else [original_term]
            elif strategy == 'moderate':
                # Top 8 synonyms
                return synonyms[:8] if synonyms else [original_term]
            elif strategy == 'broad':
                # Up to 15 synonyms
                return synonyms[:15] if synonyms else [original_term]
            else:
                return [original_term]
                
        except Exception as e:
            print(f"Error expanding {original_term}: {e}")
            return [original_term]
    
    def build_query(self, classifications: List[Dict]) -> str:
        """
        Build PubMed query from classified and expanded terms.
        
        Logic:
        - CONDITION: Use [MeSH] tag for precision
        - INTERVENTION: Use [tiab] tag with broad expansion
        - OUTCOME: Use [tiab] tag
        - Combine with AND between categories, OR within
        
        Args:
            classifications: List of term classifications
            
        Returns:
            PubMed query string
        """
        # Group by category
        category_terms = {
            'CONDITION': [],
            'INTERVENTION': [],
            'OUTCOME': [],
            'ANATOMY': [],
            'OTHER': []
        }
        
        for cls in classifications:
            category = cls.get('category', 'OTHER')
            if category == 'UNKNOWN':
                category = 'OTHER'
            
            # Expand term
            expansions = self.expand_term(cls)
            
            # Format based on category
            if category == 'CONDITION':
                # Use MeSH for conditions (more precise)
                official_name = cls.get('name', cls['term'])
                formatted = [f'"{official_name}"[MeSH]']
                # Also add title/abstract for abbreviations
                formatted.append(f'"{cls["term"]}"[tiab]')
            elif category == 'INTERVENTION':
                # Use tiab for interventions (broader recall)
                formatted = [f'"{exp}"[tiab]' for exp in expansions[:5]]
            elif category == 'OUTCOME':
                # Use tiab for outcomes
                formatted = [f'"{exp}"[tiab]' for exp in expansions[:3]]
            elif category == 'ANATOMY':
                # Use MeSH for anatomy
                formatted = [f'"{exp}"[MeSH]' for exp in expansions[:2]]
            else:
                # Default to tiab
                formatted = [f'"{cls["term"]}"[tiab]']
            
            category_terms[category].extend(formatted)
        
        # Build query parts
        query_parts = []
        
        for category in ['CONDITION', 'INTERVENTION', 'OUTCOME', 'ANATOMY', 'OTHER']:
            terms = category_terms[category]
            if terms:
                # OR within category
                part = ' OR '.join(terms)
                query_parts.append(f"({part})")
        
        # AND between categories
        query = ' AND '.join(query_parts)
        
        return query
    
    def run(
        self, 
        user_input: str, 
        days: int = 60, 
        max_results: int = 20,
        verbose: bool = True
    ) -> Dict:
        """
        Run the full semantic query pipeline.
        
        Args:
            user_input: User's query (e.g., "MS + neuromodulation")
            days: Filter to last N days
            max_results: Maximum results to return
            verbose: Print progress
            
        Returns:
            {
                'input': str,
                'terms': List[str],
                'classifications': List[Dict],
                'query': str,
                'result_count': int,
                'articles': List[Dict],
                'latency_seconds': float,
                'status': str
            }
        """
        start_time = time.time()

        # Reset API call counts for this run
        self.api_call_counts = {'umls': 0, 'pubtator': 0, 'pubmed': 0}

        try:
            # Step 1: Parse input
            if verbose:
                print(f"\n{'='*60}")
                print(f"Input: {user_input}")
                print(f"{'='*60}")
            
            terms = self.parse_input(user_input)
            if verbose:
                print(f"\n1. Parsed terms: {terms}")
            
            # Step 2: Classify terms
            if verbose:
                print(f"\n2. Classifying terms with UMLS...")
            
            classifications = self.classify_terms(terms)
            
            if verbose:
                for cls in classifications:
                    print(f"   - '{cls['term']}' -> {cls['category']}")
                    print(f"     CUI: {cls['cui']}, Name: {cls['name']}")
                    print(f"     Semantic types: {cls['semantic_types']}")
            
            # Step 3: Build query
            query = self.build_query(classifications)
            if verbose:
                print(f"\n3. Generated PubMed query:")
                print(f"   {query}")
            
            # Step 4: Search PubMed
            if verbose:
                print(f"\n4. Searching PubMed (last {days} days)...")
            
            result = self.pubmed.search_and_fetch(query, retmax=max_results, days=days)
            self.api_call_counts['pubmed'] += 1  # Track PubMed API call

            latency = time.time() - start_time
            
            if verbose:
                print(f"\n5. Results:")
                print(f"   Total hits: {result['count']}")
                print(f"   Returned: {len(result['articles'])} articles")
                print(f"   Latency: {latency:.2f}s")
                
                if result['articles']:
                    print(f"\n   Sample articles:")
                    for art in result['articles'][:3]:
                        title = art['title'][:70] + '...' if len(art['title']) > 70 else art['title']
                        print(f"   - {title}")
                        print(f"     PMID: {art['pmid']}")
            
            return {
                'input': user_input,
                'terms': terms,
                'classifications': classifications,
                'query': query,
                'query_translation': result.get('query_translation', ''),
                'result_count': result['count'],
                'articles': result['articles'],
                'api_calls': self.api_call_counts.copy(),  # API usage tracking
                'latency_seconds': latency,
                'status': 'success'
            }
            
        except Exception as e:
            latency = time.time() - start_time

            return {
                'input': user_input,
                'error': str(e),
                'api_calls': self.api_call_counts.copy(),  # Include partial API tracking on error
                'latency_seconds': latency,
                'status': 'error'
            }
    
    def compare_with_blind_expansion(
        self, 
        user_input: str, 
        days: int = 60
    ) -> Dict:
        """
        Compare semantic expansion vs blind expansion.
        
        This demonstrates the problem we're trying to solve.
        
        Args:
            user_input: User's query
            days: Date filter
            
        Returns:
            Comparison results
        """
        print("\n" + "="*70)
        print("COMPARISON: Semantic vs Blind Expansion")
        print("="*70)
        
        # 1. Semantic expansion (our approach)
        print("\n--- SEMANTIC EXPANSION (API-First) ---")
        semantic_result = self.run(user_input, days=days, verbose=True)
        
        # 2. Blind expansion (current Lex Stream approach)
        print("\n--- BLIND EXPANSION (Current Approach) ---")
        terms = self.parse_input(user_input)
        
        # Just OR all terms together (simulating blind expansion)
        blind_query = ' AND '.join([f'"{t}"[tiab]' for t in terms])
        print(f"Query: {blind_query}")
        
        blind_result = self.pubmed.search(blind_query, retmax=20, days=days)
        print(f"Results: {blind_result['count']} hits")
        
        # 3. Comparison
        print("\n--- COMPARISON SUMMARY ---")
        print(f"Semantic expansion: {semantic_result.get('result_count', 0)} hits")
        print(f"Blind expansion: {blind_result['count']} hits")
        
        semantic_count = semantic_result.get('result_count', 0)
        blind_count = blind_result['count']
        
        if semantic_count > blind_count:
            improvement = ((semantic_count - blind_count) / max(blind_count, 1)) * 100
            print(f"Improvement: +{improvement:.0f}% more results with semantic expansion")
        elif semantic_count < blind_count:
            print(f"Note: Blind expansion found more results (may include noise)")
        else:
            print("Same number of results")
        
        return {
            'semantic': semantic_result,
            'blind': {
                'query': blind_query,
                'count': blind_result['count']
            }
        }


# Main execution
if __name__ == "__main__":
    pipeline = SemanticQueryPipeline()
    
    # Test the primary use case
    print("\n" + "#"*70)
    print("# POC TEST: API-First Semantic Query Expansion")
    print("#"*70)
    
    # Test case 1: MS + neuromodulation (the problematic case)
    result = pipeline.compare_with_blind_expansion("MS + neuromodulation")
    
    # Save results
    with open('results/test_ms_neuromodulation.json', 'w') as f:
        json.dump({
            'test_case': 'MS + neuromodulation',
            'semantic_result_count': result['semantic'].get('result_count', 0),
            'blind_result_count': result['blind']['count'],
            'semantic_query': result['semantic'].get('query', ''),
            'blind_query': result['blind']['query'],
            'classifications': result['semantic'].get('classifications', []),
            'status': result['semantic'].get('status', 'unknown')
        }, f, indent=2, default=str)
    
    print("\n\nResults saved to results/test_ms_neuromodulation.json")
