# POC Plan: API-First Neuroscience Literature Search

**Date**: 2025-12-01
**Type**: Proof-of-Concept / Validation Experiment
**Goal**: Validate if NIH APIs can replace NeuroDB-2 for semantic-aware literature search
**Timeline**: 1 week (minimal but conclusive)

---

## Executive Summary

Test if PubTator 3.0 + UMLS APIs can solve "MS + neuromodulation" problem where blind expansion fails. Goal: prove APIs understand semantic relationships (condition vs intervention) BEFORE deciding NeuroDB-2 fate.

**Success Criteria**:
- API correctly classifies "MS" as disease, "neuromodulation" as intervention
- Generated PubMed query returns 5-20 relevant papers from last 60 days
- Latency <2 seconds per query

**Rollback Plan**: If APIs fail, continue NeuroDB-2 + UMLS hybrid approach (current path)

---

## Problem Context

### Current Pain Point

**User Input**: "MS + neuromodulation" (or "MS treatment with neuromodulation")

**Current Behavior** (NeuroDB-2 blind expansion):
```
MS → [multiple sclerosis, demyelinating disease, CNS disease, etc.]
neuromodulation → [TMS, DBS, electrical stimulation, etc.]
```
**Query**: `(MS OR multiple sclerosis OR ...) AND (neuromodulation OR TMS OR ...)`
**Result**: 1 hit (terrible recall)

**Root Cause**: System doesn't understand MS=CONDITION, neuromodulation=INTERVENTION. Expands both equally, creating overly restrictive query.

### Desired Behavior

**Semantic Understanding**:
- "MS" → DISEASE (narrow expansion: official names only)
- "neuromodulation" → INTERVENTION (broad expansion: all techniques)

**Smart Query**:
```
(multiple sclerosis[MeSH]) AND (neuromodulation[tiab] OR TMS[tiab] OR DBS[tiab] OR ...)
```
**Expected Result**: 5-20 relevant papers

---

## API Capabilities Assessment

### 1. PubTator 3.0

**URL**: https://www.ncbi.nlm.nih.gov/research/pubtator3/api

**Capabilities**:
- AI-powered concept extraction from text
- 9 entity types: gene, disease, chemical, species, variant, cell line, cell type, DNA, RNA
- 12 relation types: association, cause, treatment, inhibition, comparison, etc.
- 36M PubMed abstracts pre-annotated
- Free API, no auth required

**Relevant Endpoints**:

1. **Concept Recognition**: `/api/entity/recognizer`
   - Input: Raw text ("MS treatment with neuromodulation")
   - Output: Detected entities with types
   - Example response:
   ```json
   {
     "entities": [
       {"text": "MS", "type": "Disease", "start": 0, "end": 2, "id": "MESH:D009103"},
       {"text": "neuromodulation", "type": "Chemical", "start": 19, "end": 34}
     ]
   }
   ```

2. **Relation Extraction**: `/api/relation/recognizer`
   - Input: Text
   - Output: Relationships (e.g., "neuromodulation TREATS MS")
   - Example response:
   ```json
   {
     "relations": [
       {"type": "treatment", "arg1": "neuromodulation", "arg2": "MS"}
     ]
   }
   ```

**Limitations**:
- Only 9 entity types (no "intervention/procedure" category)
- May classify "neuromodulation" as "Chemical" (close enough?)
- Limited to biomedical entities (no study design detection)

### 2. UMLS Metathesaurus API

**URL**: https://uts-ws.nlm.nih.gov/

**Capabilities**:
- 135 semantic types (T047=Disease, T061=Therapeutic Procedure, etc.)
- Concept relationships (isa, treats, associated_with, etc.)
- Free with registration (API key required)

**Relevant Endpoints**:

1. **Search Concepts**: `GET /rest/search/current`
   - Input: Term string ("neuromodulation")
   - Output: UMLS CUI + semantic types
   - Example request:
   ```
   GET https://uts-ws.nlm.nih.gov/rest/search/current?string=neuromodulation&apiKey={KEY}
   ```
   - Example response:
   ```json
   {
     "result": {
       "results": [
         {
           "ui": "C0394674",
           "name": "Neuromodulation",
           "rootSource": "SNOMEDCT_US",
           "semanticTypes": [
             {"name": "Therapeutic or Preventive Procedure", "uri": "...T061"}
           ]
         }
       ]
     }
   }
   ```

2. **Get Concept Details**: `GET /rest/content/current/CUI/{cui}`
   - Input: CUI (C0026769 for MS)
   - Output: Full concept metadata, semantic types, definitions
   - Example response:
   ```json
   {
     "result": {
       "ui": "C0026769",
       "name": "Multiple Sclerosis",
       "semanticTypes": [
         {"name": "Disease or Syndrome", "uri": "...T047"}
       ],
       "atoms": "...",
       "relations": "..."
     }
   }
   ```

3. **Get Related Concepts**: `GET /rest/content/current/CUI/{cui}/relations`
   - Input: CUI
   - Output: Related concepts (synonyms, broader, narrower terms)
   - Useful for expansion

**Strengths**:
- 135 semantic types (vs PubTator's 9) → better categorization
- Official NIH authority
- Hierarchical relationships (tree structure)

**Limitations**:
- Rate limits (20 requests/second, 5000/hour)
- Requires free API key (registration ~5 min)
- Text search can be ambiguous (multiple CUIs for "MS")

### 3. PubMed E-utilities

**URL**: https://eutils.ncbi.nlm.nih.gov/

**Already in Use**: Lex Stream currently uses E-utilities for PubMed search

**Automatic Term Mapping (ATM)**:
- PubMed auto-expands MeSH terms
- Example: "multiple sclerosis"[MeSH] → includes MeSH tree children
- No API call needed - happens server-side

**Advantage**: Free MeSH explosion without extra work

---

## Test Case Definition

### Input Examples

1. **Simple**: "MS + neuromodulation"
2. **Natural Language**: "MS treatment with neuromodulation"
3. **Complex**: "multiple sclerosis neuromodulation therapy outcomes"
4. **Ambiguous**: "MS motor function" (MS=disease, motor function=outcome)

### Expected Classification

| Term | Semantic Type | Category | Expansion Strategy |
|------|--------------|----------|-------------------|
| MS / multiple sclerosis | T047 (Disease) | CONDITION | Narrow (official names only) |
| neuromodulation | T061 (Therapeutic Procedure) | INTERVENTION | Broad (all techniques: TMS, DBS, VNS, etc.) |
| motor function | T042 (Organ Function) | OUTCOME | Moderate (motor control, motor performance) |

### Expected Query Structure

**Input**: "MS treatment with neuromodulation"

**Desired Output**:
```
(multiple sclerosis[MeSH])
AND
(neuromodulation[tiab] OR transcranial magnetic stimulation[tiab] OR TMS[tiab] OR deep brain stimulation[tiab] OR DBS[tiab] OR vagus nerve stimulation[tiab] OR VNS[tiab])
AND
("last 60 days"[PDat])
```

**Logic**:
- CONDITION (MS): MeSH tag for precision
- INTERVENTION (neuromodulation): tiab tag + broad expansion for recall
- Date filter: Last 60 days

### Success Metrics

**Primary**:
- ✅ API correctly identifies semantic types (disease vs intervention)
- ✅ Generated query returns 5-20 results (not 0, not 1000s)
- ✅ Results are relevant (manual review of top 10)

**Secondary**:
- ⏱️ Latency <2 seconds (total API calls + PubMed query)
- 💰 Cost: $0 (all APIs free)
- 🔄 Reliability: 3/3 test runs succeed

**Failure Criteria**:
- ❌ API misclassifies terms (MS as intervention, neuromodulation as disease)
- ❌ Query returns 0 results or >100 results
- ❌ Latency >5 seconds
- ❌ API errors/rate limiting in normal use

---

## Implementation Plan

### Phase 1: Environment Setup (30 min)

**Prerequisites**:
- Python 3.8+
- requests library
- UMLS API key (free registration)

**Setup Steps**:

1. Register for UMLS API key
   - URL: https://uts.nlm.nih.gov/uts/signup-login
   - Form: Name, email, institution
   - Approval: Instant (automated)

2. Create project directory
   ```bash
   mkdir /Users/sam/NeuroDB-2/poc-api-first
   cd /Users/sam/NeuroDB-2/poc-api-first
   ```

3. Create `.env` file
   ```bash
   UMLS_API_KEY=your_key_here
   ```

4. Install dependencies
   ```bash
   pip install requests python-dotenv
   ```

**Deliverable**: Working environment with API credentials

### Phase 2: API Integration (2-3 hours)

**Goal**: Create modular API clients for each service

**File Structure**:
```
poc-api-first/
├── .env (API keys)
├── clients/
│   ├── __init__.py
│   ├── pubtator.py (PubTator 3.0 client)
│   ├── umls.py (UMLS API client)
│   └── pubmed.py (E-utilities client)
├── test_apis.py (API testing script)
└── poc_pipeline.py (Full POC pipeline)
```

#### 2.1: PubTator Client

**File**: `clients/pubtator.py`

**Functions**:

1. `recognize_entities(text: str) -> List[Entity]`
   - Endpoint: POST https://www.ncbi.nlm.nih.gov/research/pubtator3/api/entity/recognizer
   - Input: Raw text
   - Output: List of entities with type, text, position, ID

2. `extract_relations(text: str) -> List[Relation]`
   - Endpoint: POST https://www.ncbi.nlm.nih.gov/research/pubtator3/api/relation/recognizer
   - Input: Raw text
   - Output: Relationships between entities

**Implementation**:
```python
import requests
from typing import List, Dict

class PubTatorClient:
    BASE_URL = "https://www.ncbi.nlm.nih.gov/research/pubtator3/api"

    def recognize_entities(self, text: str) -> List[Dict]:
        """Extract biomedical entities from text."""
        endpoint = f"{self.BASE_URL}/entity/recognizer"
        response = requests.post(endpoint, json={"text": text})
        response.raise_for_status()
        return response.json().get("entities", [])

    def extract_relations(self, text: str) -> List[Dict]:
        """Extract relationships between entities."""
        endpoint = f"{self.BASE_URL}/relation/recognizer"
        response = requests.post(endpoint, json={"text": text})
        response.raise_for_status()
        return response.json().get("relations", [])
```

**Test Cases**:
```python
client = PubTatorClient()

# Test 1: Simple entity recognition
entities = client.recognize_entities("MS treatment with neuromodulation")
assert any(e['type'] == 'Disease' for e in entities)

# Test 2: Relation extraction
relations = client.extract_relations("TMS improves motor function in MS patients")
assert any(r['type'] == 'treatment' for r in relations)
```

#### 2.2: UMLS Client

**File**: `clients/umls.py`

**Functions**:

1. `search_concept(term: str) -> List[Concept]`
   - Endpoint: GET /rest/search/current
   - Input: Term string
   - Output: List of matching CUIs with semantic types

2. `get_semantic_types(cui: str) -> List[SemanticType]`
   - Endpoint: GET /rest/content/current/CUI/{cui}
   - Input: CUI
   - Output: Semantic types (T047, T061, etc.)

3. `get_related_terms(cui: str, relation_type: str = 'synonym') -> List[str]`
   - Endpoint: GET /rest/content/current/CUI/{cui}/relations
   - Input: CUI, relation type
   - Output: Related concept names

**Implementation**:
```python
import os
import requests
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class UMLSClient:
    BASE_URL = "https://uts-ws.nlm.nih.gov/rest"

    def __init__(self):
        self.api_key = os.getenv("UMLS_API_KEY")
        if not self.api_key:
            raise ValueError("UMLS_API_KEY not found in .env")

    def search_concept(self, term: str) -> List[Dict]:
        """Search for UMLS concepts by term string."""
        endpoint = f"{self.BASE_URL}/search/current"
        params = {
            "string": term,
            "apiKey": self.api_key,
            "returnIdType": "concept",
            "pageSize": 10
        }
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()['result']['results']

    def get_semantic_types(self, cui: str) -> List[Dict]:
        """Get semantic types for a CUI."""
        endpoint = f"{self.BASE_URL}/content/current/CUI/{cui}"
        params = {"apiKey": self.api_key}
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()['result']['semanticTypes']

    def get_synonyms(self, cui: str) -> List[str]:
        """Get synonyms/related terms for a CUI."""
        endpoint = f"{self.BASE_URL}/content/current/CUI/{cui}/atoms"
        params = {"apiKey": self.api_key, "pageSize": 25}
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        atoms = response.json()['result']
        return [atom['name'] for atom in atoms]
```

**Test Cases**:
```python
client = UMLSClient()

# Test 1: Search for MS
results = client.search_concept("multiple sclerosis")
assert len(results) > 0
assert results[0]['ui'] == 'C0026769'  # Official MS CUI

# Test 2: Get semantic type
stys = client.get_semantic_types("C0026769")
assert any(s['name'] == 'Disease or Syndrome' for s in stys)

# Test 3: Get synonyms
synonyms = client.get_synonyms("C0026769")
assert "MS" in synonyms
```

#### 2.3: PubMed Client

**File**: `clients/pubmed.py`

**Functions**:

1. `search(query: str, retmax: int = 20, date_filter: str = '60') -> Dict`
   - Endpoint: GET /entrez/eutils/esearch.fcgi
   - Input: PubMed query, result limit, date range
   - Output: PMIDs and count

2. `fetch_abstracts(pmids: List[str]) -> List[Article]`
   - Endpoint: GET /entrez/eutils/efetch.fcgi
   - Input: PMIDs
   - Output: Article titles, abstracts, authors

**Implementation**:
```python
import requests
from typing import List, Dict
from datetime import datetime, timedelta

class PubMedClient:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def search(self, query: str, retmax: int = 20, days: int = 60) -> Dict:
        """Search PubMed with date filter."""
        endpoint = f"{self.BASE_URL}/esearch.fcgi"

        # Date filter: last N days
        date_to = datetime.now().strftime("%Y/%m/%d")
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")

        params = {
            "db": "pubmed",
            "term": query,
            "retmax": retmax,
            "retmode": "json",
            "datetype": "pdat",
            "mindate": date_from,
            "maxdate": date_to
        }

        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()['esearchresult']

    def fetch_abstracts(self, pmids: List[str]) -> List[Dict]:
        """Fetch article details for PMIDs."""
        endpoint = f"{self.BASE_URL}/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        # Parse XML (simplified for POC)
        return {"xml": response.text}
```

**Test Cases**:
```python
client = PubMedClient()

# Test 1: Simple search
results = client.search("multiple sclerosis[MeSH]", retmax=5, days=60)
assert results['count'] != '0'
assert len(results['idlist']) <= 5

# Test 2: Fetch abstracts
pmids = results['idlist'][:3]
abstracts = client.fetch_abstracts(pmids)
assert abstracts is not None
```

**Deliverable**: 3 working API clients with unit tests

### Phase 3: Semantic Classification Pipeline (2-3 hours)

**Goal**: Build pipeline to classify user input into semantic categories

**File**: `poc_pipeline.py`

**Pipeline Steps**:

1. **Input Parsing**: Extract individual terms from user query
2. **API Classification**: Call PubTator + UMLS to classify each term
3. **Category Mapping**: Map semantic types to Lex Stream categories
4. **Expansion Strategy**: Determine narrow/moderate/broad expansion per category
5. **Query Assembly**: Build PubMed query with proper tags ([MeSH] vs [tiab])
6. **PubMed Search**: Execute query and return results
7. **Evaluation**: Assess result quality (count, relevance)

**Category Mapping** (from research):

| Semantic Type (UMLS) | TUI | Lex Stream Category | Expansion Strategy |
|---------------------|-----|--------------------|--------------------|
| Disease or Syndrome | T047 | CONDITION | Narrow (MeSH only) |
| Sign or Symptom | T184 | CONDITION | Narrow |
| Therapeutic Procedure | T061 | INTERVENTION | Broad (all techniques) |
| Pharmacologic Substance | T121 | INTERVENTION | Moderate (drug class) |
| Organ Function | T042 | OUTCOME | Moderate (related measures) |
| Finding | T033 | OUTCOME | Moderate |

**Implementation**:

```python
from clients.pubtator import PubTatorClient
from clients.umls import UMLSClient
from clients.pubmed import PubMedClient
from typing import Dict, List
import time

class SemanticQueryPipeline:
    """POC pipeline for API-first semantic query expansion."""

    # Semantic type to category mapping
    CATEGORY_MAP = {
        'T047': 'CONDITION',  # Disease or Syndrome
        'T184': 'CONDITION',  # Sign or Symptom
        'T061': 'INTERVENTION',  # Therapeutic Procedure
        'T121': 'INTERVENTION',  # Pharmacologic Substance
        'T074': 'INTERVENTION',  # Medical Device
        'T042': 'OUTCOME',  # Organ Function
        'T033': 'OUTCOME',  # Finding
        'T034': 'OUTCOME',  # Lab Result
    }

    def __init__(self):
        self.pubtator = PubTatorClient()
        self.umls = UMLSClient()
        self.pubmed = PubMedClient()

    def classify_term(self, term: str) -> Dict:
        """
        Classify single term using UMLS API.

        Returns:
            {
                'term': str,
                'cui': str,
                'semantic_types': List[str],
                'category': str,
                'expansion_strategy': str
            }
        """
        # Search UMLS
        concepts = self.umls.search_concept(term)
        if not concepts:
            return {
                'term': term,
                'cui': None,
                'semantic_types': [],
                'category': 'UNKNOWN',
                'expansion_strategy': 'narrow'
            }

        # Take first (best match)
        concept = concepts[0]
        cui = concept['ui']

        # Get semantic types
        sem_types = self.umls.get_semantic_types(cui)
        tuis = [st['uri'].split('/')[-1] for st in sem_types]  # Extract TUI

        # Map to category
        category = None
        for tui in tuis:
            if tui in self.CATEGORY_MAP:
                category = self.CATEGORY_MAP[tui]
                break

        if not category:
            category = 'OTHER'

        # Determine expansion strategy
        expansion_strategy = {
            'CONDITION': 'narrow',
            'INTERVENTION': 'broad',
            'OUTCOME': 'moderate',
            'OTHER': 'narrow'
        }.get(category, 'narrow')

        return {
            'term': term,
            'cui': cui,
            'semantic_types': [st['name'] for st in sem_types],
            'category': category,
            'expansion_strategy': expansion_strategy
        }

    def expand_term(self, classification: Dict) -> List[str]:
        """
        Expand term based on strategy.

        narrow: Original term + official synonyms only
        moderate: + related terms
        broad: + all techniques/subtypes
        """
        cui = classification['cui']
        strategy = classification['expansion_strategy']

        if not cui:
            return [classification['term']]

        # Get synonyms
        synonyms = self.umls.get_synonyms(cui)

        if strategy == 'narrow':
            # Top 3 synonyms
            return synonyms[:3]
        elif strategy == 'moderate':
            # Top 10 synonyms
            return synonyms[:10]
        elif strategy == 'broad':
            # All synonyms (up to 25)
            return synonyms[:25]
        else:
            return [classification['term']]

    def build_query(self, classifications: List[Dict]) -> str:
        """
        Build PubMed query from classified terms.

        Logic:
        - CONDITION terms: [MeSH] tag (narrow, precise)
        - INTERVENTION terms: [tiab] tag (broad, recall)
        - OUTCOME terms: [tiab] tag
        - OR within category, AND between categories
        """
        conditions = []
        interventions = []
        outcomes = []

        for cls in classifications:
            category = cls['category']
            expansions = self.expand_term(cls)

            if category == 'CONDITION':
                # Use MeSH tag for precision
                terms = [f"{exp}[MeSH]" for exp in expansions]
                conditions.extend(terms)
            elif category == 'INTERVENTION':
                # Use tiab tag for recall
                terms = [f"{exp}[tiab]" for exp in expansions]
                interventions.extend(terms)
            elif category == 'OUTCOME':
                # Use tiab tag
                terms = [f"{exp}[tiab]" for exp in expansions]
                outcomes.extend(terms)

        # Build query
        query_parts = []

        if conditions:
            query_parts.append(f"({' OR '.join(conditions)})")
        if interventions:
            query_parts.append(f"({' OR '.join(interventions)})")
        if outcomes:
            query_parts.append(f"({' OR '.join(outcomes)})")

        # AND between categories
        query = " AND ".join(query_parts)
        return query

    def run(self, user_input: str, days: int = 60) -> Dict:
        """
        Full POC pipeline.

        Args:
            user_input: User query (e.g., "MS treatment with neuromodulation")
            days: Date range (default 60 days)

        Returns:
            {
                'input': str,
                'classifications': List[Dict],
                'query': str,
                'results': Dict (PubMed results),
                'latency': float (seconds),
                'status': 'success' | 'error'
            }
        """
        start_time = time.time()

        try:
            # 1. Parse input (simple whitespace tokenization for POC)
            terms = [t.strip() for t in user_input.lower().split()
                     if t.strip() not in ['with', 'and', 'or', 'treatment', 'therapy']]

            # 2. Classify each term
            classifications = []
            for term in terms:
                cls = self.classify_term(term)
                classifications.append(cls)
                print(f"Classified '{term}': {cls['category']} ({cls['semantic_types']})")

            # 3. Build query
            query = self.build_query(classifications)
            print(f"\nGenerated query: {query}")

            # 4. Search PubMed
            results = self.pubmed.search(query, retmax=20, days=days)

            # 5. Calculate latency
            latency = time.time() - start_time

            return {
                'input': user_input,
                'classifications': classifications,
                'query': query,
                'result_count': int(results['count']),
                'pmids': results['idlist'],
                'latency': latency,
                'status': 'success'
            }

        except Exception as e:
            return {
                'input': user_input,
                'error': str(e),
                'latency': time.time() - start_time,
                'status': 'error'
            }
```

**Deliverable**: Working semantic classification pipeline

### Phase 4: Testing & Validation (2-3 hours)

**Goal**: Run test cases and evaluate API performance

**File**: `test_poc.py`

**Test Cases**:

```python
from poc_pipeline import SemanticQueryPipeline
import json

def test_ms_neuromodulation():
    """Test Case 1: MS + neuromodulation (primary use case)"""
    pipeline = SemanticQueryPipeline()

    result = pipeline.run("MS treatment with neuromodulation")

    print("\n=== Test 1: MS + neuromodulation ===")
    print(json.dumps(result, indent=2))

    # Assertions
    assert result['status'] == 'success', "Pipeline failed"

    # Check classification
    classifications = {c['term']: c['category'] for c in result['classifications']}
    assert 'ms' in classifications, "MS not classified"
    assert 'neuromodulation' in classifications, "neuromodulation not classified"

    # Semantic validation
    ms_category = classifications['ms']
    neuro_category = classifications['neuromodulation']
    assert ms_category == 'CONDITION', f"MS wrongly classified as {ms_category}"
    assert neuro_category == 'INTERVENTION', f"neuromodulation wrongly classified as {neuro_category}"

    # Result count validation
    count = result['result_count']
    assert 5 <= count <= 100, f"Result count {count} outside expected range (5-100)"

    # Latency validation
    assert result['latency'] < 2.0, f"Latency {result['latency']}s exceeds 2s threshold"

    print(f"✅ Test 1 PASSED: {count} results in {result['latency']:.2f}s")
    return result

def test_ms_motor_function():
    """Test Case 2: MS + motor function (disease + outcome)"""
    pipeline = SemanticQueryPipeline()

    result = pipeline.run("MS motor function")

    print("\n=== Test 2: MS + motor function ===")
    print(json.dumps(result, indent=2))

    # Semantic validation
    classifications = {c['term']: c['category'] for c in result['classifications']}
    assert classifications.get('ms') == 'CONDITION', "MS not a condition"
    # motor/function might be separate terms

    count = result['result_count']
    assert count > 0, "No results found"

    print(f"✅ Test 2 PASSED: {count} results in {result['latency']:.2f}s")
    return result

def test_complex_query():
    """Test Case 3: Multiple terms with mixed categories"""
    pipeline = SemanticQueryPipeline()

    result = pipeline.run("multiple sclerosis neuromodulation therapy outcomes")

    print("\n=== Test 3: Complex query ===")
    print(json.dumps(result, indent=2))

    assert result['status'] == 'success'
    count = result['result_count']
    assert count > 0, "No results found"

    print(f"✅ Test 3 PASSED: {count} results in {result['latency']:.2f}s")
    return result

def run_all_tests():
    """Run all test cases and generate report"""
    results = []

    try:
        results.append(("MS + neuromodulation", test_ms_neuromodulation()))
    except AssertionError as e:
        print(f"❌ Test 1 FAILED: {e}")
        results.append(("MS + neuromodulation", {"status": "failed", "error": str(e)}))

    try:
        results.append(("MS + motor function", test_ms_motor_function()))
    except AssertionError as e:
        print(f"❌ Test 2 FAILED: {e}")
        results.append(("MS + motor function", {"status": "failed", "error": str(e)}))

    try:
        results.append(("Complex query", test_complex_query()))
    except AssertionError as e:
        print(f"❌ Test 3 FAILED: {e}")
        results.append(("Complex query", {"status": "failed", "error": str(e)}))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, r in results if r.get('status') == 'success')
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result.get('status') == 'success' else "❌ FAIL"
        count = result.get('result_count', 'N/A')
        latency = result.get('latency', 'N/A')
        print(f"{status} | {name:30s} | Results: {count:>4} | Latency: {latency}")

    print(f"\nOverall: {passed}/{total} tests passed")

    return results

if __name__ == "__main__":
    run_all_tests()
```

**Manual Validation**:

1. Review top 10 PMIDs from Test 1 (MS + neuromodulation)
2. Open abstracts in PubMed
3. Check relevance:
   - Is paper about MS? (Yes/No)
   - Is paper about neuromodulation? (Yes/No)
   - Is paper from last 60 days? (Yes/No)
4. Calculate precision: % of relevant papers in top 10
5. Target: ≥80% precision

**Deliverable**: Test results + manual relevance assessment

### Phase 5: Comparative Analysis (1-2 hours)

**Goal**: Compare API-first vs NeuroDB-2 approaches

**File**: `comparison_report.md`

**Comparison Dimensions**:

| Dimension | API-First (POC) | NeuroDB-2 Current | Winner |
|-----------|----------------|-------------------|--------|
| **Semantic Understanding** | ✅ UMLS 135 types | ❌ None (blind expansion) | API |
| **Vocabulary Size** | ♾️ Full UMLS (3M+ concepts) | 595 terms (or 325K UMLS import) | API |
| **Maintenance Burden** | ✅ Zero (NIH maintains) | ❌ High (manual curation) | API |
| **Latency** | ⏱️ TBD (test) | ✅ <100ms (local JSON) | TBD |
| **Cost** | ✅ Free | ✅ Free | Tie |
| **Offline Support** | ❌ Requires internet | ✅ Works offline | NeuroDB |
| **Customization** | ❌ Limited | ✅ Full control | NeuroDB |
| **MeSH Hierarchy** | ✅ Built-in (UMLS) | ❌ Not implemented | API |
| **Synonym Coverage** | ✅ UMLS 100% | ⚠️ 10% (UMLS import) or 42% (Wikipedia) | API |
| **Abbreviations** | ⚠️ TBD | ✅ 22% (126 abbreviations) | TBD |

**Qualitative Assessment**:

1. **API Strengths**:
   - Semantic understanding (solves "MS + neuromodulation" problem)
   - No maintenance (NIH updates)
   - Full UMLS vocabulary
   - MeSH hierarchy built-in

2. **API Weaknesses**:
   - Network dependency (latency, availability)
   - Rate limits (20 req/s, 5000/hr)
   - Less control over expansion logic
   - No abbreviation expansion (needs separate handling)

3. **NeuroDB-2 Strengths**:
   - Fast (local JSON lookup)
   - Offline capability
   - Custom neuroscience abbreviations
   - Full control over expansion rules

4. **NeuroDB-2 Weaknesses**:
   - No semantic understanding (blind expansion)
   - High maintenance burden
   - Small vocabulary (595 terms) or low synonym coverage (10% UMLS)
   - MeSH hierarchy not implemented

**Hybrid Approach Recommendation**:

Based on POC results, recommend one of:

1. **Full API Replacement**: If latency <1s, use APIs for all classification + expansion
2. **Hybrid Layer 1 (API semantic classification + local expansion)**:
   - API: Classify terms (CONDITION, INTERVENTION, OUTCOME)
   - Local DB: Expand terms based on classification
3. **Hybrid Layer 2 (Local DB + API fallback)**:
   - Local DB: Primary (fast)
   - API: Fallback for unknown terms + semantic validation
4. **Keep NeuroDB-2**: If API fails tests, continue current path (UMLS import + manual enrichment)

**Deliverable**: Comparison report with recommendation

---

## Evaluation Criteria

### Success Metrics

**API Functionality** (Must Pass All):
- [ ] UMLS API correctly classifies "MS" as T047 (Disease)
- [ ] UMLS API correctly classifies "neuromodulation" as T061 (Therapeutic Procedure)
- [ ] Pipeline generates semantically-structured query
- [ ] PubMed search returns 5-20 results for "MS + neuromodulation"
- [ ] Manual review: ≥80% precision in top 10 results

**Performance** (Must Pass 2/3):
- [ ] Total latency <2 seconds (UMLS + PubMed API calls)
- [ ] API reliability: 3/3 test runs succeed without errors
- [ ] Rate limits not hit during normal testing (20 req/s)

**Comparative Advantage** (Must Pass 1/2):
- [ ] API-first returns MORE relevant results than blind expansion (qualitative)
- [ ] API-first solves semantic ambiguity problem (e.g., MS + neuromodulation)

### Failure Scenarios

**Critical Failures** (POC fails if any occur):
- ❌ API consistently misclassifies terms (e.g., MS as intervention)
- ❌ Generated queries return 0 results for valid neuroscience queries
- ❌ Latency >5 seconds (unusable for interactive app)
- ❌ API errors/downtime in >50% of test runs

**Minor Failures** (Can work around):
- ⚠️ Some terms not found in UMLS (fallback to local DB)
- ⚠️ Latency 2-5 seconds (acceptable, needs caching)
- ⚠️ Abbreviations not expanded (add local abbreviation layer)

---

## Decision Framework

### If POC Succeeds (All Success Metrics Pass)

**Recommendation**: Implement Hybrid Layer 1 (API semantic + local expansion)

**Next Steps**:
1. Design production architecture (caching, fallback, error handling)
2. Implement API client with retry logic + rate limiting
3. Add local abbreviation expansion layer (NeuroDB-2 abbreviations.json)
4. Performance optimization (Redis cache for API responses)
5. Integration with Lex Stream agents
6. Timeline: 2-3 weeks

**NeuroDB-2 Fate**:
- Keep as **abbreviation database** (126 abbreviations)
- Keep as **fallback** for offline/API failure scenarios
- **Stop** manual synonym enrichment (rely on UMLS API)
- **Stop** UMLS local import (325K terms not needed)

### If POC Partially Succeeds (Some Failures)

**Scenario 1: Latency 2-5s**
- Recommendation: Implement aggressive caching (Redis)
- Cache UMLS responses for common terms (90% hit rate expected)
- Precompute classifications for top 1K neuroscience terms
- Re-test with cache

**Scenario 2: Some Terms Not Found**
- Recommendation: Hybrid fallback
- API first, NeuroDB-2 second
- Log missing terms for manual enrichment

**Scenario 3: Rate Limiting Issues**
- Recommendation: Request higher limits from NIH (free for research)
- Implement request queuing
- Cache aggressively

### If POC Fails (Critical Failures)

**Recommendation**: Continue current path (NeuroDB-2 + UMLS local import)

**Next Steps**:
1. Complete UMLS import semantic type enrichment (from research report)
2. Add CUI + semantic types to CSV schema
3. Implement local semantic classification (UMLS TUI → category)
4. Manual synonym enrichment for top 5K terms
5. Timeline: 2-3 months (per current plan)

**Lessons Learned**:
- Document why API approach failed
- Consider alternative APIs (PubTator 3.0 limitations?)
- Re-evaluate in 6-12 months (APIs improve over time)

---

## Implementation Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1. Environment Setup | 30 min | API credentials, project structure |
| 2. API Integration | 2-3 hours | PubTator, UMLS, PubMed clients |
| 3. Pipeline Development | 2-3 hours | Semantic classification pipeline |
| 4. Testing | 2-3 hours | Automated tests + manual validation |
| 5. Analysis | 1-2 hours | Comparison report + recommendation |
| **Total** | **1 day** | **Go/No-Go decision on API-first** |

---

## Files to Create

```
/Users/sam/NeuroDB-2/poc-api-first/
├── .env (API keys)
├── .gitignore (.env)
├── README.md (POC overview)
├── requirements.txt (requests, python-dotenv)
├── clients/
│   ├── __init__.py
│   ├── pubtator.py (PubTator 3.0 client)
│   ├── umls.py (UMLS API client)
│   └── pubmed.py (E-utilities client)
├── poc_pipeline.py (Full semantic classification pipeline)
├── test_poc.py (Automated test suite)
├── comparison_report.md (API vs NeuroDB-2 analysis)
└── results/
    ├── test_1_ms_neuromodulation.json (Test results)
    ├── test_2_ms_motor_function.json
    ├── test_3_complex_query.json
    └── manual_validation.csv (Relevance assessment)
```

---

## Risks & Mitigations

### Risk 1: API Downtime

**Impact**: POC cannot complete
**Probability**: Low (NIH APIs are stable)
**Mitigation**:
- Test during off-peak hours (avoid Mon 9am EST)
- Retry logic with exponential backoff
- Fallback: Use cached responses from previous test runs

### Risk 2: Rate Limiting

**Impact**: Cannot complete all tests
**Probability**: Medium (5000 req/hr limit)
**Mitigation**:
- Implement request throttling (max 10 req/s)
- Cache API responses during development
- Run tests sequentially (not parallel)

### Risk 3: UMLS Registration Delay

**Impact**: Cannot start POC
**Probability**: Low (usually instant approval)
**Mitigation**:
- Register ASAP (before starting implementation)
- Have backup account ready
- Use existing UMLS account if available

### Risk 4: Semantic Type Ambiguity

**Impact**: Misclassification of terms
**Probability**: Medium (some terms have multiple types)
**Mitigation**:
- Use primary semantic type (first in list)
- Context-based disambiguation (future enhancement)
- Manual override for critical terms

### Risk 5: Poor Query Quality

**Impact**: 0 results or 1000+ results
**Probability**: Medium (expansion logic untested)
**Mitigation**:
- Iterative refinement of expansion strategies
- A/B test different expansion levels
- Manual query review before PubMed search

---

## Unresolved Questions

1. **PubTator vs UMLS**: Which API is more accurate for neuroscience term classification? Test both?

2. **Multi-Term Disambiguation**: How to handle "MS" (multiple sclerosis vs mass spectrometry) in context of "MS motor function"? Need syntactic parsing?

3. **Abbreviation Handling**: APIs don't expand abbreviations. Keep NeuroDB-2 abbreviation layer? Integrate with API pipeline?

4. **Caching Strategy**: Where to cache API responses? Redis? Local JSON? How long (TTL)?

5. **Error Recovery**: If UMLS API fails for one term, continue with others or abort? Partial results acceptable?

6. **Production Architecture**: If POC succeeds, how to integrate with existing Lex Stream agents? Replace agents or add new "Semantic Classifier" agent?

7. **Neuroscientist Validation**: James (neuroscientist) should review API-generated queries. Schedule feedback session?

---

## Success Definition

**Primary Goal**: Prove APIs can solve "MS + neuromodulation" semantic problem (1 hit → 10+ hits)

**Secondary Goals**:
- Validate UMLS semantic types work for neuroscience domain
- Measure API latency vs local DB
- Identify gaps in API coverage (abbreviations, neuroscience-specific terms)

**Decision Point**: Go/No-Go on API-first architecture for Lex Stream

**Timeline**: 1 week (5-7 hours actual work)

**Budget**: $0 (all APIs free)

---

## Next Actions (After Plan Approval)

1. Register for UMLS API key (5 min)
2. Create project directory structure (10 min)
3. Implement API clients (2-3 hours)
4. Build pipeline (2-3 hours)
5. Run tests (2-3 hours)
6. Write comparison report (1-2 hours)
7. **Decision meeting**: Review results, decide next steps

---

**Plan Status**: ✅ COMPLETE
**File Path**: `/Users/sam/.claude/plans/happy-imagining-sundae-agent-f1f41365.md`
**Date**: 2025-12-01
**Next Action**: Review plan → Approve → Execute Phase 1
