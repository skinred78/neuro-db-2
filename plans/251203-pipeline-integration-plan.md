# Pipeline Integration Plan: SemanticQueryPipeline + MVP Test Framework

**Date**: 2025-12-03
**Status**: Planning (REVISED v3 - FINAL)
**Objective**: Replace mock execution in test_runner.py with actual SemanticQueryPipeline calls
**Revision**: Addresses ALL CRITICAL (2) and HIGH (2) issues from Codex review:
- CRITICAL #1: classify_fn contract with pipeline normalizer (Section 1.5, Step 1)
- CRITICAL #2: Schema consistency in _classify_terms_batch (Section 1.5, Step 2)
- HIGH #1: API call counting handles both metadata formats (Section 1.5, Step 3)
- HIGH #2: Path centralization via Config.NEURODB_DATA_PATH (Section 1.5, Step 5)

---

## 1. Executive Summary

### Current State
- **SemanticQueryPipeline** (`poc_pipeline.py`): Self-contained, creates own clients in `__init__()`
- **Test Configurations** (`test_configurations.py`): Create their own clients, have `classify_term()` methods
- **Test Runner** (`test_runner.py`): Uses `_mock_pipeline_execution()` placeholder
- **Client Duplication**: Pipeline and configs both instantiate UMLS/PubTator/PubMed clients

### Architectural Decision: **Adapter Pattern** (NOT Refactor)

**Rationale**:
1. SemanticQueryPipeline proven stable (5 hits vs 1 for "MS + neuromodulation")
2. Configs need different classification logic (UMLSPubTator 2-layer, FullHybrid 3-layer)
3. Adapter layer keeps pipeline intact, minimal risk
4. Configs delegate to pipeline for query building + search, customize classification only

### Key Integration Points
1. Config-based client injection into pipeline
2. NeuroDB-2 disambiguation layer for FullHybrid
3. Classification method override mechanism
4. Error handling for missing API keys / network failures

---

## 1.5 CRITICAL Issue Fixes (from Codex Review)

### CRITICAL #1: Classification Schema Contract

**Problem**: Custom `classify_fn` callback bypasses pipeline post-processing. Missing required keys (`original_term`, `term`, `expansion_strategy`) will break `build_query()` and `expand_term()`.

**Solution**: Define explicit schema contract + pipeline normalizes callback outputs.

**Required Classification Record Schema**:
```python
CLASSIFICATION_SCHEMA = {
    # Required fields (pipeline depends on these)
    'term': str,              # Classified term (may be expanded)
    'original_term': str,     # Original input term (before expansion)
    'category': str,          # CONDITION, INTERVENTION, OUTCOME, ANATOMY, OTHER, UNKNOWN
    'expansion_strategy': str, # narrow, moderate, broad

    # Optional fields (UMLS enrichment)
    'cui': str | None,        # UMLS Concept Unique Identifier
    'name': str | None,       # UMLS preferred name
    'semantic_types': list,   # UMLS semantic type codes

    # Disambiguation metadata
    'disambiguation_source': str,  # NeuroDB_term, NeuroDB_abbrev, PubTator, UMLS_direct
    'disambiguation_used': bool,   # True if term was expanded/disambiguated
    'confidence': float,           # 0.0-1.0 confidence in disambiguation
}
```

**Pipeline Normalizer** (in `poc_pipeline.py`):
```python
def _normalize_classification(self, raw: Dict, original_term: str) -> Dict:
    """
    Normalize classification output to ensure all required keys present.
    Pipeline calls this AFTER custom classify_fn returns.
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
```

---

### CRITICAL #2: Schema Consistency Across Configs

**Problem**: `_classify_terms_batch` returns raw `classify_term()` outputs. Different configs return different keys, breaking downstream pipeline processing.

**Solution**: Each config's `_classify_terms_batch` returns normalized records.

**Updated Config Pattern**:
```python
class UMLSPubTatorConfig:
    def _classify_terms_batch(self, terms: List[str]) -> List[Dict]:
        """
        Batch classification returning normalized records.

        IMPORTANT: Returns records matching CLASSIFICATION_SCHEMA.
        Pipeline trusts these keys exist; normalizer adds missing defaults.
        """
        results = []
        for term in terms:
            raw = self.classify_term(term)

            # Ensure required keys present
            normalized = {
                'term': raw.get('term', term),
                'original_term': term,  # ALWAYS set original
                'category': raw.get('category', 'UNKNOWN'),
                'cui': raw.get('cui'),
                'name': raw.get('name'),
                'semantic_types': raw.get('semantic_types', []),
                'disambiguation_source': raw.get('disambiguation_source', 'UMLS_direct'),
                'disambiguation_used': raw.get('disambiguation_source', '') == 'PubTator',
                'confidence': raw.get('confidence', 0.5),
            }
            results.append(normalized)

        return results
```

---

### HIGH #1: API Call Counting Consistency

**Problem**: `_extract_api_calls` checks `disambiguation_used` but FullHybrid sets `disambiguation_source`.

**Solution**: Check both keys consistently.

**Updated `_extract_api_calls`**:
```python
def _extract_api_calls(self, result: Dict) -> Dict[str, int]:
    """
    Extract API call counts from pipeline result.

    Handles both disambiguation_used (bool) and disambiguation_source (str).
    """
    classifications = result.get('classifications', [])

    pubtator_count = 0
    for c in classifications:
        # Check both metadata formats
        if c.get('disambiguation_used', False):
            pubtator_count += 1
        elif c.get('disambiguation_source', '') == 'PubTator':
            pubtator_count += 1

    return {
        'pubmed': 1,
        'umls': len(classifications),
        'pubtator': pubtator_count
    }
```

---

### HIGH #2: Path Centralization

**Problem**: NeuroDB path uses `Path(__file__)` instead of `Config.NEURODB_DATA_PATH`.

**Solution**: Use centralized config.

**Updated FullHybridConfig.__init__**:
```python
from poc_api_first.config import Config

def __init__(self):
    # ... client initialization ...

    # Use centralized config path
    neurodb_path = Config.NEURODB_DATA_PATH

    if not neurodb_path.exists():
        raise FileNotFoundError(
            f"NeuroDB-2 data file not found: {neurodb_path}\n"
            "Set NEURODB_DATA_PATH in config or ensure data/neuro_terms.json exists."
        )
```

**Add to Config class** (if not present):
```python
# In poc_api_first/config.py
NEURODB_DATA_PATH = Path(__file__).parent.parent / 'data' / 'neuro_terms.json'
```

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Test Runner (test_runner.py)                               │
│  - Loads test cases from benchmark_queries.json            │
│  - Measures latency externally (AUTHORITATIVE)             │
│  - Calls config.run() for each test                        │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ Configuration Classes (test_configurations.py)              │
│  - UMLSPubTatorConfig: 2-layer (PubTator → UMLS)           │
│  - FullHybridConfig:   3-layer (NeuroDB → PubTator → UMLS) │
│  - Each config:                                             │
│    • Creates clients in __init__()                          │
│    • Has classify_term() method (custom logic)             │
│    • NEW: Has run() method (delegates to pipeline)         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ Semantic Query Pipeline (poc_pipeline.py)                  │
│  - NEW: Accepts optional clients in __init__()             │
│  - NEW: Accepts optional classify_fn callback              │
│  - Existing: parse_input(), build_query(), run()           │
│  - Default: Creates own clients if not provided            │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Implementation Steps

### Step 1: Modify SemanticQueryPipeline (Backward Compatible)

**File**: `poc_api_first/poc_pipeline.py`

**Changes**:
```python
class SemanticQueryPipeline:
    def __init__(
        self,
        umls_client=None,
        pubmed_client=None,
        pubtator_client=None,
        classify_fn=None  # NEW: Callback for term classification
    ):
        """
        Initialize pipeline with optional client injection.

        Args:
            umls_client: UMLSClient instance (creates default if None)
            pubmed_client: PubMedClient instance (creates default if None)
            pubtator_client: PubTatorClient instance (creates default if None)
            classify_fn: Custom classification function (uses self.classify_terms if None)
                         Signature: classify_fn(terms: List[str]) -> List[Dict]
                         MUST return records matching CLASSIFICATION_SCHEMA (see Section 1.5)
        """
        self.umls = umls_client or UMLSClient()
        self.pubmed = pubmed_client or PubMedClient()
        self.pubtator = pubtator_client or PubTatorClient()
        self._custom_classify_fn = classify_fn

    def _normalize_classification(self, raw: Dict, original_term: str) -> Dict:
        """
        Normalize classification output to ensure all required keys present.

        CRITICAL FIX: Pipeline calls this AFTER custom classify_fn returns
        to guarantee build_query() and expand_term() have required keys.
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

    def classify_terms(self, terms: List[str]) -> List[Dict]:
        """
        Classify terms using custom function if provided, otherwise use default.

        NOTE: Always normalizes output to ensure schema compliance.
        """
        if self._custom_classify_fn:
            # Custom classification (from configs)
            raw_results = self._custom_classify_fn(terms)

            # CRITICAL: Normalize to ensure required keys for build_query/expand_term
            return [
                self._normalize_classification(raw, term)
                for raw, term in zip(raw_results, terms)
            ]

        # Original POC implementation (2-layer: PubTator → UMLS)
        classifications = []
        for term in terms:
            # [EXISTING CODE - unchanged, already returns correct schema]
            ...
        return classifications
```

**Risk**: Low - backward compatible (all params optional, normalizer preserves existing behavior)

---

### Step 2: Add `run()` Method to Configurations

**File**: `poc_api_first/tests/test_configurations.py`

> **CRITICAL FIX (Section 1.5 #2)**: `_classify_terms_batch` MUST return normalized records per CLASSIFICATION_SCHEMA. Pipeline normalizer adds missing defaults, but configs should provide required keys.

**Add to UMLSPubTatorConfig**:
```python
class UMLSPubTatorConfig:
    # [Existing __init__, classify_term methods - unchanged]

    def run(self, user_input: str, days=60, max_results=20, verbose=False):
        """
        Execute pipeline with 2-layer disambiguation (PubTator → UMLS).

        Returns same structure as SemanticQueryPipeline.run()
        """
        from poc_api_first.poc_pipeline import SemanticQueryPipeline

        pipeline = SemanticQueryPipeline(
            umls_client=self.umls_client,
            pubtator_client=self.pubtator_client,
            classify_fn=self._classify_terms_batch  # Custom classification
        )

        return pipeline.run(user_input, days, max_results, verbose)

    def _classify_terms_batch(self, terms: List[str]) -> List[Dict]:
        """
        Batch classification returning normalized records.

        CRITICAL: Returns records matching CLASSIFICATION_SCHEMA (Section 1.5).
        Pipeline normalizer adds missing defaults, but we provide required keys.

        Applies 2-layer logic: PubTator → UMLS
        """
        results = []
        for term in terms:
            raw = self.classify_term(term)

            # Normalize to CLASSIFICATION_SCHEMA
            normalized = {
                'term': raw.get('term', term),
                'original_term': term,  # ALWAYS set original
                'category': raw.get('category', 'UNKNOWN'),
                'cui': raw.get('cui'),
                'name': raw.get('name'),
                'semantic_types': raw.get('semantic_types', []),
                'disambiguation_source': raw.get('disambiguation_source', 'UMLS_direct'),
                'disambiguation_used': raw.get('disambiguation_source', '') == 'PubTator',
                'confidence': raw.get('confidence', 0.5),
            }
            results.append(normalized)

        return results
```

**Add to FullHybridConfig**:
```python
class FullHybridConfig:
    # [Existing __init__, classify_term methods - unchanged]

    def run(self, user_input: str, days=60, max_results=20, verbose=False):
        """
        Execute pipeline with 3-layer disambiguation (NeuroDB → PubTator → UMLS).

        Returns same structure as SemanticQueryPipeline.run()
        """
        from poc_api_first.poc_pipeline import SemanticQueryPipeline

        pipeline = SemanticQueryPipeline(
            umls_client=self.umls_client,
            pubtator_client=self.pubtator_client,
            classify_fn=self._classify_terms_batch  # Custom 3-layer classification
        )

        return pipeline.run(user_input, days, max_results, verbose)

    def _classify_terms_batch(self, terms: List[str]) -> List[Dict]:
        """
        Batch classification returning normalized records.

        CRITICAL: Returns records matching CLASSIFICATION_SCHEMA (Section 1.5).
        Pipeline normalizer adds missing defaults, but we provide required keys.

        Applies 3-layer logic: NeuroDB → PubTator → UMLS
        """
        results = []
        for term in terms:
            raw = self.classify_term(term)

            # Normalize to CLASSIFICATION_SCHEMA
            normalized = {
                'term': raw.get('term', term),
                'original_term': term,  # ALWAYS set original
                'category': raw.get('category', 'UNKNOWN'),
                'cui': raw.get('cui'),
                'name': raw.get('name'),
                'semantic_types': raw.get('semantic_types', []),
                'disambiguation_source': raw.get('disambiguation_source', 'UMLS_direct'),
                'disambiguation_used': raw.get('disambiguation_source', '') not in ['UMLS_direct', 'unknown', ''],
                'confidence': raw.get('confidence', 0.5),
            }
            results.append(normalized)

        return results
```

**Risk**: Low - encapsulated within config classes

---

### Step 3: Replace Mock Execution in Test Runner

**File**: `poc_api_first/tests/test_runner.py`

**Replace `run_single_test()` method**:
```python
def run_single_test(self, config, test_case: Dict) -> Dict[str, Any]:
    """
    Execute single test case and collect metrics.

    Args:
        config: Configuration object
        test_case: Test case dictionary

    Returns:
        Test result with evaluation metrics
    """
    start_time = time.time()

    try:
        # ACTUAL PIPELINE EXECUTION (replaces mock)
        result = config.run(
            user_input=test_case['input'],
            days=60,
            max_results=20,
            verbose=False  # Suppress verbose output during tests
        )

        latency_seconds = time.time() - start_time

        # Validate result structure
        if result.get('status') != 'success':
            raise ValueError(f"Pipeline returned error: {result.get('error')}")

        # Evaluate result
        evaluation = self.evaluate_result(test_case, result, latency_seconds)

        # NOTE: Runner measures latency externally (AUTHORITATIVE)
        return {
            'test_id': test_case['test_id'],
            'input': test_case['input'],
            'config': config.name,
            'result_count': result['result_count'],
            'latency_seconds': latency_seconds,  # AUTHORITATIVE measurement
            'api_calls': self._extract_api_calls(result),
            'classifications': result.get('classifications', []),
            'query': result.get('query', ''),
            'evaluation': evaluation,
            'status': 'PASS' if evaluation.get('quantitative', {}).get('passed') else 'FAIL',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'test_id': test_case['test_id'],
            'input': test_case['input'],
            'config': config.name,
            'status': 'ERROR',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def _extract_api_calls(self, result: Dict) -> Dict[str, int]:
    """
    Extract API call counts from pipeline result.

    HIGH FIX (Section 1.5 #1): Handles both disambiguation_used (bool)
    and disambiguation_source (str) for consistent counting.

    Pipeline doesn't track this explicitly yet, so we infer:
    - 1 PubMed search
    - N UMLS calls (1 per term)
    - N PubTator calls (1 per abbreviation that used PubTator)
    """
    classifications = result.get('classifications', [])

    pubtator_count = 0
    for c in classifications:
        # Check both metadata formats for consistency
        if c.get('disambiguation_used', False):
            pubtator_count += 1
        elif c.get('disambiguation_source', '') == 'PubTator':
            pubtator_count += 1

    return {
        'pubmed': 1,  # One search per query
        'umls': len(classifications),  # One UMLS call per term
        'pubtator': pubtator_count  # Counted via unified metadata check
    }
```

**Remove** `_mock_pipeline_execution()` method entirely.

**Risk**: Medium - core test execution logic, but simple replacement

---

### Step 4: Error Handling & Validation

**Add API Key Validation to Config Init**:
```python
class UMLSPubTatorConfig:
    def __init__(self):
        """Initialize UMLS + PubTator clients."""
        from poc_api_first.clients.umls import UMLSClient
        from poc_api_first.clients.pubtator import PubTatorClient

        api_key = os.getenv("UMLS_API_KEY")
        if not api_key:
            raise ValueError(
                "UMLS_API_KEY environment variable not set.\n"
                "UMLSPubTator configuration requires UMLS API access.\n"
                "Set UMLS_API_KEY in .env file or environment."
            )

        try:
            self.umls_client = UMLSClient(api_key)
            self.pubtator_client = PubTatorClient()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize clients: {e}")
```

**Add Network Error Handling to Pipeline**:
```python
def run(self, user_input: str, days=60, max_results=20, verbose=True) -> Dict:
    """
    Run the full semantic query pipeline.

    [EXISTING DOCSTRING]
    """
    start_time = time.time()

    try:
        # [EXISTING CODE]
        ...

    except requests.exceptions.RequestException as e:
        # Network errors (API down, timeout, rate limit)
        latency = time.time() - start_time
        return {
            'input': user_input,
            'error': f"Network error: {str(e)}",
            'error_type': 'network',
            'latency_seconds': latency,
            'status': 'error'
        }

    except ValueError as e:
        # Validation errors (bad API key, malformed response)
        latency = time.time() - start_time
        return {
            'input': user_input,
            'error': f"Validation error: {str(e)}",
            'error_type': 'validation',
            'latency_seconds': latency,
            'status': 'error'
        }

    except Exception as e:
        # Catch-all for unexpected errors
        latency = time.time() - start_time
        return {
            'input': user_input,
            'error': str(e),
            'error_type': 'unknown',
            'latency_seconds': latency,
            'status': 'error'
        }
```

**Risk**: Low - defensive programming, no breaking changes

---

### Step 5: NeuroDB-2 Integration for FullHybrid

**Current State**: FullHybrid loads `neuro_terms.json` but only checks abbreviations

**Enhancement**: Support full NeuroDB-2 structure

**Expected NeuroDB-2 Structure** (from `data/neuro_terms.json`):
```json
[
  {
    "Term": "alpha motor neurons",
    "Abbreviation": "α-MN",
    "Synonym 1": "alpha motoneurons",
    "Closest MeSH term": "Motor Neurons",
    ...
  }
]
```

**Updated FullHybridConfig.__init__()**:
```python
from poc_api_first.config import Config

def __init__(self):
    # [Existing client initialization - unchanged]

    # HIGH FIX (Section 1.5 #2): Use centralized config path
    neurodb_path = Config.NEURODB_DATA_PATH

    if not neurodb_path.exists():
        raise FileNotFoundError(
            f"NeuroDB-2 data file not found: {neurodb_path}\n"
            "Set NEURODB_DATA_PATH in config.py or ensure data/neuro_terms.json exists."
        )

    with open(neurodb_path) as f:
        neurodb_list = json.load(f)

    # Build lookup indices for O(1) access
    self.neurodb_by_term = {}  # term → full record
    self.neurodb_by_abbrev = {}  # abbreviation → full record

    for record in neurodb_list:
        term = record.get('Term', '').lower()
        abbrev = record.get('Abbreviation', '').lower()

        if term:
            self.neurodb_by_term[term] = record
        if abbrev:
            self.neurodb_by_abbrev[abbrev] = record
```

**Updated FullHybridConfig.classify_term()**:
```python
def classify_term(self, term: str):
    """
    Three-layer disambiguation with confidence-based selection:
    - NeuroDB-2 (confidence: 1.0) - neuroscience-specific curation
    - PubTator (confidence: 0.5-0.9) - biomedical general
    - UMLS direct (confidence: 0.5) - fallback

    Selects highest-confidence expansion for UMLS classification.
    """
    term_lower = term.lower()

    # Layer 1: NeuroDB-2 exact term match
    if term_lower in self.neurodb_by_term:
        record = self.neurodb_by_term[term_lower]
        resolved = record.get('Term')  # Use official term for UMLS
        result = self.umls_client.classify_term(resolved)
        result['disambiguation_source'] = 'NeuroDB_term'
        result['confidence'] = 1.0
        result['neurodb_record'] = record
        return result

    # Layer 1b: NeuroDB-2 abbreviation match
    if term_lower in self.neurodb_by_abbrev:
        record = self.neurodb_by_abbrev[term_lower]
        resolved = record.get('Term')  # Expand abbreviation
        result = self.umls_client.classify_term(resolved)
        result['disambiguation_source'] = 'NeuroDB_abbrev'
        result['confidence'] = 1.0
        result['neurodb_record'] = record
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
```

**Risk**: Low - isolated to FullHybrid config

---

## 4. Testing Strategy

### Unit Tests (New File: `poc_api_first/tests/test_integration.py`)

```python
"""Integration tests for pipeline + config integration."""

import pytest
from poc_api_first.tests.test_configurations import UMLSPubTatorConfig, FullHybridConfig
from poc_api_first.poc_pipeline import SemanticQueryPipeline

class TestPipelineIntegration:
    """Test pipeline integration with configurations."""

    @pytest.fixture
    def umls_pubtator_config(self):
        """Skip if UMLS_API_KEY not set."""
        try:
            return UMLSPubTatorConfig()
        except ValueError as e:
            pytest.skip(f"UMLS_API_KEY not available: {e}")

    @pytest.fixture
    def full_hybrid_config(self):
        """Skip if UMLS_API_KEY not set or NeuroDB missing."""
        try:
            return FullHybridConfig()
        except (ValueError, FileNotFoundError) as e:
            pytest.skip(f"Full hybrid config unavailable: {e}")

    def test_umls_pubtator_run(self, umls_pubtator_config):
        """Test UMLSPubTator config.run() executes successfully."""
        result = umls_pubtator_config.run("MS + neuromodulation", verbose=False)

        assert result['status'] == 'success'
        assert 'result_count' in result
        assert 'query' in result
        assert 'classifications' in result
        assert len(result['classifications']) >= 2  # MS, neuromodulation

    def test_full_hybrid_run(self, full_hybrid_config):
        """Test FullHybrid config.run() executes successfully."""
        result = full_hybrid_config.run("TMS stroke", verbose=False)

        assert result['status'] == 'success'
        assert 'result_count' in result
        assert 'classifications' in result

    def test_pipeline_client_injection(self):
        """Test pipeline accepts client injection."""
        from poc_api_first.clients.umls import UMLSClient
        from poc_api_first.clients.pubmed import PubMedClient

        try:
            umls = UMLSClient()
            pubmed = PubMedClient()

            pipeline = SemanticQueryPipeline(
                umls_client=umls,
                pubmed_client=pubmed
            )

            assert pipeline.umls is umls
            assert pipeline.pubmed is pubmed
        except ValueError:
            pytest.skip("UMLS_API_KEY not available")

    def test_custom_classify_fn(self):
        """Test pipeline accepts custom classification function."""
        def mock_classify(terms):
            return [{'term': t, 'category': 'TEST'} for t in terms]

        pipeline = SemanticQueryPipeline(classify_fn=mock_classify)
        result = pipeline.classify_terms(['test'])

        assert result[0]['category'] == 'TEST'
```

### Integration Test (Run Actual Test Suite)

```bash
# Run test suite with actual pipeline (not mocks)
cd /Users/sam/NeuroDB-2
python -m poc_api_first.tests.test_runner

# Should output:
# MVP Test Runner - Semantic Pipeline Evaluation
# Configurations: 2 (UMLSPubTator, FullHybrid)
# Test Suites: ['benchmark']
# Running benchmark suite (5 cases)...
# ...
# TEST SUMMARY
# UMLSPubTator:
#   Tests: 5
#   Passed: 4 (80.0%)
#   Avg Results: 8.2
#   Avg Latency: 1.8s
# FullHybrid:
#   Tests: 5
#   Passed: 5 (100%)
#   Avg Results: 12.4
#   Avg Latency: 1.9s
```

**Success Criteria**:
- All 5 benchmark queries execute without errors
- BM-002 ("MS + neuromodulation") returns ≥5 hits for UMLSPubTator
- FullHybrid shows better result counts than UMLSPubTator
- Latency < 2.0s per query
- No API errors or rate limit issues

---

## 5. Risk Assessment

### High Risk
**None**

### Medium Risk
1. **API Rate Limits** (UMLS: 20 req/s, PubTator: 10 req/s)
   - **Mitigation**: Sequential test execution (no parallel), add `time.sleep(0.1)` in classify_terms
   - **Contingency**: Implement rate limiter in `poc_api_first/utils/rate_limiter.py`

2. **Missing UMLS_API_KEY in CI/CD**
   - **Mitigation**: Graceful config initialization failure + skip tests
   - **Contingency**: Mock configs for environments without API keys

### Low Risk
1. **NeuroDB-2 file format changes**
   - **Mitigation**: Validate JSON structure on load
   - **Contingency**: Fallback to PubTator if NeuroDB missing

2. **Network timeouts**
   - **Mitigation**: Requests timeout=30s, retry logic in clients
   - **Contingency**: Test runner catches exceptions, marks as ERROR

---

## 6. Files to Modify/Create

### Modify
1. **`poc_api_first/poc_pipeline.py`** (Lines 41-44)
   - Add optional client parameters to `__init__()`
   - Add `classify_fn` callback parameter
   - Update `classify_terms()` to check callback first

2. **`poc_api_first/tests/test_configurations.py`** (Lines 109-154, 156-231)
   - Add `run()` method to UMLSPubTatorConfig
   - Add `run()` method to FullHybridConfig
   - Add `_classify_terms_batch()` to both configs
   - Enhance FullHybrid NeuroDB-2 loading (structured indices)
   - Update FullHybrid `classify_term()` for term + abbrev lookup

3. **`poc_api_first/tests/test_runner.py`** (Lines 164-220)
   - Replace `run_single_test()` with actual pipeline execution
   - Add `_extract_api_calls()` helper method
   - Remove `_mock_pipeline_execution()` method (line 221)

### Create
4. **`poc_api_first/tests/test_integration.py`** (New)
   - Unit tests for pipeline + config integration
   - Client injection tests
   - Custom classify_fn tests
   - Config run() method tests

### No Changes
- `poc_api_first/clients/umls.py` (stable)
- `poc_api_first/clients/pubtator.py` (stable)
- `poc_api_first/clients/pubmed.py` (stable)
- `poc_api_first/evaluators/quantitative_metrics.py` (stable)
- `poc_api_first/tests/test_data/benchmark_queries.json` (stable)

---

## 7. Implementation Order

### Phase 1: Foundation (1-2 hours)
1. Modify `SemanticQueryPipeline.__init__()` (client injection + classify_fn callback)
2. Add unit tests in `test_integration.py` for client injection
3. Verify backward compatibility (existing `poc_pipeline.py` main block still works)

### Phase 2: Configuration Integration (1-2 hours)
4. Add `run()` + `_classify_terms_batch()` to UMLSPubTatorConfig
5. Test UMLSPubTator with "MS + neuromodulation" (should get 5+ hits)
6. Add `run()` + `_classify_terms_batch()` to FullHybridConfig
7. Enhance FullHybrid NeuroDB-2 loading (term + abbrev indices)

### Phase 3: Test Runner Integration (1 hour)
8. Replace `run_single_test()` mock with `config.run()` call
9. Add `_extract_api_calls()` helper
10. Remove `_mock_pipeline_execution()`

### Phase 4: Validation (1 hour)
11. Run full test suite: `python -m poc_api_first.tests.test_runner`
12. Verify all 5 benchmark queries execute
13. Check BM-002 gets ≥5 hits (proven POC case)
14. Validate FullHybrid > UMLSPubTator for result counts

**Total Estimate**: 4-6 hours

---

## 8. Open Questions

### Resolved
- ✅ Should we refactor pipeline or use adapter? → **Adapter pattern**
- ✅ How to handle config-specific classification? → **Callback function**
- ✅ Where to inject NeuroDB-2? → **FullHybrid.classify_term()**

### Unresolved
1. **API Call Tracking**: Pipeline doesn't currently track API calls internally
   - **Recommendation**: Add simple counter dict to pipeline, return in result
   - **Alternative**: Keep inference in test runner (current approach)

2. **Rate Limiting**: No rate limiter implemented yet
   - **Recommendation**: Sequential execution + sleep(0.1) for now
   - **Future**: Implement `utils/rate_limiter.py` with token bucket

3. **Caching**: No caching for UMLS/PubTator responses
   - **Recommendation**: Defer to post-MVP (utils/cache_manager.py exists)
   - **Impact**: Higher latency during testing (acceptable for MVP)

4. **Test Data Expansion**: Only 5 benchmark queries
   - **Recommendation**: Start with 5, expand after MVP validation
   - **Future**: Add edge cases (long queries, special chars, unknown terms)

---

## 9. Success Metrics

### Must Have (MVP)
- ✅ All 5 benchmark queries execute without errors
- ✅ BM-002 returns ≥5 hits for UMLSPubTator (proven POC metric)
- ✅ FullHybrid leverages NeuroDB-2 successfully
- ✅ Latency < 2.0s per query average
- ✅ Test runner generates valid JSON results file

### Should Have
- ✅ FullHybrid shows 20-30% improvement over UMLSPubTator
- ✅ Classification metadata includes disambiguation source
- ✅ Error handling catches network/API failures gracefully
- ✅ Unit test coverage for integration points

### Nice to Have
- Rate limiter implementation (defer to post-MVP)
- Redis caching for UMLS responses (defer to post-MVP)
- Parallel test execution (defer to post-MVP - sequential safer)

---

## 10. Rollback Plan

### If Integration Fails
1. **Git revert** to pre-integration state
2. **Restore mock execution**: Uncomment `_mock_pipeline_execution()`
3. **Framework still usable**: Test runner works with mocks for demonstrations

### Partial Rollback
- If FullHybrid fails: Disable in `MVP_CONFIGURATIONS`, keep UMLSPubTator
- If UMLSPubTator fails: Test with pipeline standalone (bypass configs)

### Data Integrity
- No database changes (read-only NeuroDB-2)
- No external state mutations
- Safe to rollback anytime

---

**END OF PLAN**
