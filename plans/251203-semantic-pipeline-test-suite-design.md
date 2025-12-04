# Semantic Query Pipeline Test Suite Design

**Date**: 2025-12-03
**Project**: NeuroDB-2 POC API-First
**Purpose**: Comprehensive evaluation of tool combinations for semantic query expansion
**Analyst**: Planning Agent

---

## EXECUTIVE SUMMARY

**Objective**: Design test suite evaluating 5 tool combinations for semantic query pipeline:
1. **Lex Stream 2 Current** (blind expansion with neuro_terms.json v2.0) - **BASELINE**
2. UMLS-only (semantic classification without abbreviation)
3. UMLS + PubTator (current POC - PROVEN)
4. UMLS + NeuroDB-2 (semantic classification + local enrichment)
5. UMLS + PubTator + NeuroDB-2 (full hybrid)

**Current State**:
- **Baseline (Lex Stream 2)**: "MS + neuromodulation" → **1 hit** (James's feedback)
- **POC (UMLS + PubTator)**: "MS + neuromodulation" → **5 hits** (proven improvement)

**Validation Status**: ⚠️ **UNVALIDATED** - This plan created by AI planner without external human/expert review. Requires validation before implementation.

**Success Criteria**:
- 5-20 highly relevant papers (last 60 days)
- Precision ≥80% in top 10 results
- Correct semantic classification (CONDITION, INTERVENTION, OUTCOME, ANATOMY)
- Abbreviation disambiguation accuracy
- <2s latency (production target)

---

## 1. TEST CASE CATALOG

### 1.1 Abbreviation Disambiguation (Priority: HIGH)

**Category Goal**: Validate PubTator + NeuroDB-2 abbreviation resolution

| Test ID | Input | Expected Expansion | Semantic Type | Ambiguity Level |
|---------|-------|-------------------|---------------|-----------------|
| ABB-001 | MS | Multiple Sclerosis | CONDITION | HIGH (vs Mass Spectrometry) |
| ABB-002 | TMS | Transcranial Magnetic Stimulation | INTERVENTION | MEDIUM |
| ABB-003 | DBS | Deep Brain Stimulation | INTERVENTION | LOW |
| ABB-004 | fMRI | Functional Magnetic Resonance Imaging | INTERVENTION | LOW |
| ABB-005 | EEG | Electroencephalography | INTERVENTION | LOW |
| ABB-006 | BOLD | Blood-Oxygen-Level-Dependent | OUTCOME | MEDIUM |
| ABB-007 | PET | Positron Emission Tomography | INTERVENTION | HIGH (vs animal) |
| ABB-008 | DTI | Diffusion Tensor Imaging | INTERVENTION | MEDIUM |
| ABB-009 | MEG | Magnetoencephalography | INTERVENTION | MEDIUM |
| ABB-010 | LTP | Long-Term Potentiation | OUTCOME | MEDIUM |

**Expected Tool Performance**:
- **PubTator**: MS (✅), PET (⚠️ needs context), TMS (✅)
- **NeuroDB-2**: fMRI (✅), DTI (✅), BOLD (✅), MEG (✅) - neuroscience-specific
- **UMLS alone**: Fails on all abbreviations - returns literal terms

---

### 1.2 Multi-Term Queries (Priority: HIGH)

**Category Goal**: Test semantic classification + query building logic

| Test ID | Input | Expected Components | Target Results |
|---------|-------|-------------------|----------------|
| MTQ-001 | MS + neuromodulation | CONDITION + INTERVENTION | 5-15 papers |
| MTQ-002 | Parkinson's + DBS | CONDITION + INTERVENTION | 10-20 papers |
| MTQ-003 | depression + TMS | CONDITION + INTERVENTION | 10-20 papers |
| MTQ-004 | stroke + motor function | CONDITION + OUTCOME | 10-20 papers |
| MTQ-005 | Alzheimer's + memory + fMRI | CONDITION + OUTCOME + INTERVENTION | 5-15 papers |
| MTQ-006 | epilepsy + neuromodulation + seizure reduction | CONDITION + INTERVENTION + OUTCOME | 5-15 papers |
| MTQ-007 | TBI + cognitive performance | CONDITION + OUTCOME | 10-20 papers |

**Expected Query Structure**:
```
(CONDITION terms with [MeSH]) AND (INTERVENTION terms with [tiab]) AND (OUTCOME terms with [tiab])
```

---

### 1.3 Semantic Ambiguity (Priority: HIGH)

**Category Goal**: Test context-aware disambiguation

| Test ID | Input | Ambiguity | Expected Resolution | Notes |
|---------|-------|-----------|---------------------|-------|
| AMB-001 | MS treatment | MS = disease vs honorific | Multiple Sclerosis | PubTator should detect "treatment" context |
| AMB-002 | PET scan brain | PET = imaging vs animal | Positron Emission Tomography | Context: "scan", "brain" |
| AMB-003 | MEG study | MEG = imaging vs name | Magnetoencephalography | Context: "study" |
| AMB-004 | LTP memory | LTP = outcome vs other | Long-Term Potentiation | Context: "memory" |
| AMB-005 | DBS effectiveness | DBS = intervention | Deep Brain Stimulation | Clear neuroscience context |

**Metrics**:
- Disambiguation accuracy: % correctly resolved
- Context utilization score: Did algorithm use surrounding terms?

---

### 1.4 Complex Queries (Priority: MEDIUM)

**Category Goal**: Stress-test pipeline with realistic neuroscience queries

| Test ID | Input | Expected Behavior | Challenge |
|---------|-------|-------------------|-----------|
| CPX-001 | TMS + depression + treatment response + fMRI | 4 components, mixed types | Multi-component classification |
| CPX-002 | Parkinson's + DBS + motor improvement + quality of life | 4 terms, outcome measures | Multiple outcome metrics |
| CPX-003 | stroke rehabilitation + motor cortex + neuroplasticity | Anatomy + outcome + intervention | Anatomical precision |
| CPX-004 | ADHD + neurofeedback + cognitive training + attention | 2 interventions + condition + outcome | Dual interventions |
| CPX-005 | migraine + transcranial direct current stimulation + pain reduction | Full names vs abbreviations | Mixed format handling |

**Expected Result Range**: 5-20 papers (avoid 0 or 1000+)

---

### 1.5 Edge Cases (Priority: MEDIUM)

**Category Goal**: Test robustness and error handling

| Test ID | Input | Expected Behavior | Edge Type |
|---------|-------|-------------------|-----------|
| EDG-001 | hippocampal memory | UK spelling: hippocampal vs hippocampus | Spelling variant |
| EDG-002 | neurones firing | UK spelling: neurones vs neurons | UK/US difference |
| EDG-003 | anti-depressant | Hyphenation: anti-depressant vs antidepressant | Hyphen handling |
| EDG-004 | dopaminergic neuron | Word form: dopamine → dopaminergic | Adjective form |
| EDG-005 | TMS  (extra spaces) | Whitespace normalization | Input sanitization |
| EDG-006 | tms (lowercase) | Case normalization | Case handling |
| EDG-007 | transcranial magnetic stimulation | Full name instead of abbreviation | Expansion reverse |
| EDG-008 | XYZABC (nonsense) | Graceful failure, no results | Invalid term |
| EDG-009 | Multiple Sclerosis (caps) | Case handling on full terms | Case sensitivity |
| EDG-010 | TMS; DBS | Semicolon separator | Separator handling |

---

### 1.6 Rare/Niche Terms (Priority: LOW)

**Category Goal**: Test coverage of specialized neuroscience terminology

| Test ID | Input | Expected Source | Expected CUI/Classification |
|---------|-------|-----------------|----------------------------|
| RARE-001 | optogenetics | UMLS or NeuroDB-2 | INTERVENTION |
| RARE-002 | chemogenetics | UMLS or NeuroDB-2 | INTERVENTION |
| RARE-003 | grid cells | NeuroDB-2 preferred | ANATOMY |
| RARE-004 | default mode network | UMLS or NeuroDB-2 | ANATOMY |
| RARE-005 | theta oscillations | NeuroDB-2 preferred | OUTCOME |
| RARE-006 | sharp wave ripples | Likely missing | OUTCOME |
| RARE-007 | entorhinal cortex | UMLS + NeuroDB-2 | ANATOMY |
| RARE-008 | spike-timing-dependent plasticity | Likely missing | OUTCOME |

**Metrics**:
- Coverage rate: % terms found in UMLS, PubTator, NeuroDB-2
- Fallback behavior: How does pipeline handle missing terms?

---

### 1.7 Outcome Measures (Priority: MEDIUM)

**Category Goal**: Validate outcome classification and expansion

| Test ID | Input | Expected Classification | Expansion Terms |
|---------|-------|------------------------|-----------------|
| OUT-001 | motor function | OUTCOME | motor performance, motor control, movement |
| OUT-002 | cognitive performance | OUTCOME | cognition, cognitive function, mental performance |
| OUT-003 | symptom reduction | OUTCOME | symptom relief, symptom improvement, clinical improvement |
| OUT-004 | pain relief | OUTCOME | analgesia, pain reduction, pain management |
| OUT-005 | functional connectivity | OUTCOME | brain connectivity, neural connectivity |
| OUT-006 | quality of life | OUTCOME | QOL, life quality, functional status |
| OUT-007 | reaction time | OUTCOME | response time, RT, latency |

**Expected Query Tag**: [tiab] (title/abstract, not MeSH - outcomes are descriptive)

---

### 1.8 Benchmark Queries (Priority: HIGH)

**Category Goal**: Real-world queries from neuroscientist feedback (James)

| Test ID | Input | Source | Expected Results | Validation |
|---------|-------|--------|------------------|------------|
| BM-001 | TMS, stroke, memory | Lex Stream example | 10-20 papers | James review |
| BM-002 | MS + neuromodulation | POC test case | 5-15 papers | Current baseline: 5 |
| BM-003 | Parkinson's DBS motor | Common clinical query | 10-20 papers | High clinical relevance |
| BM-004 | fMRI motor cortex | Neuroimaging research | 10-20 papers | Research-focused |
| BM-005 | depression neuromodulation RCT | Evidence-based query | 5-10 papers | Study design filter |

**Validation Method**: Manual review by James (neuroscientist) - precision scoring top 10 results

---

## 2. TEST FRAMEWORK ARCHITECTURE

### 2.1 Directory Structure

```
poc-api-first/
├── tests/
│   ├── __init__.py
│   ├── test_data/
│   │   ├── abbreviations.json         # ABB-001 to ABB-010
│   │   ├── multi_term_queries.json    # MTQ-001 to MTQ-007
│   │   ├── semantic_ambiguity.json    # AMB-001 to AMB-005
│   │   ├── complex_queries.json       # CPX-001 to CPX-005
│   │   ├── edge_cases.json            # EDG-001 to EDG-010
│   │   ├── rare_terms.json            # RARE-001 to RARE-008
│   │   ├── outcome_measures.json      # OUT-001 to OUT-007
│   │   └── benchmark_queries.json     # BM-001 to BM-005
│   ├── test_runner.py                 # Main test orchestrator
│   ├── test_configurations.py         # 4 tool combination configs
│   ├── evaluators/
│   │   ├── quantitative_metrics.py    # Count, latency, API calls
│   │   ├── semantic_accuracy.py       # Classification correctness
│   │   ├── relevance_scorer.py        # Precision/recall estimation
│   │   └── comparison_analyzer.py     # Cross-tool comparison
│   ├── fixtures/
│   │   ├── mock_apis.py               # Mock responses for CI/CD
│   │   └── gold_standard.json         # Expected results for validation
│   └── reports/
│       ├── template_report.md         # Report structure
│       └── <timestamp>_results.json   # Test run outputs
├── results/
│   └── comparisons/                   # Tool combination comparisons
└── docs/
    └── testing_guide.md               # How to run tests
```

---

### 2.2 Tool Configurations

**Config 0: Lex Stream 2 Current (BASELINE)**
```python
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
    """
    name = "LexStream2Baseline"  # Config identifier
    use_pubtator = False
    use_neurodb = True  # neuro_terms.json v2.0 (569 terms, 126 abbreviations)
    use_umls = False    # No UMLS semantic classification

    def __init__(self):
        """Initialize baseline with NeuroDB-2 local database."""
        import os
        import json
        neurodb_path = os.path.join(os.path.dirname(__file__), '../../../data/neuro_terms.json')
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
        """
        pass
```
**Expected Performance**: 40-50% (baseline to beat)

**Config 1: UMLS-only**
```python
class UMLSOnlyConfig:
    name = "UMLSOnly"  # Config identifier
    use_pubtator = False
    use_neurodb = False

    def __init__(self):
        """Initialize UMLS client."""
        import os
        from clients.umls import UMLSClient
        api_key = os.getenv("UMLS_API_KEY")
        self.umls_client = UMLSClient(api_key)

    def classify_term(self, term):
        return self.umls_client.classify_term(term)
```

**Config 2: UMLS + PubTator (POC - PROVEN 5 hits)**
```python
class UMLSPubTatorConfig:
    name = "UMLSPubTator"  # Config identifier
    use_pubtator = True
    use_neurodb = False

    def __init__(self):
        """Initialize UMLS + PubTator clients."""
        import os
        from clients.umls import UMLSClient
        from clients.pubtator import PubTatorClient
        api_key = os.getenv("UMLS_API_KEY")
        self.umls_client = UMLSClient(api_key)
        self.pubtator_client = PubTatorClient()

    @staticmethod
    def is_abbreviation(term):
        """Check if term is likely an abbreviation."""
        return len(term) <= 5 or term.isupper() or (len(term.split()) == 1 and len(term) <= 10)

    def classify_term(self, term):
        # Step 1: PubTator disambiguation
        if self.is_abbreviation(term):
            disambiguation = self.pubtator_client.disambiguate_term(term)
            if disambiguation['confidence'] > 0.5:
                term = disambiguation['resolved']

        # Step 2: UMLS classification
        return self.umls_client.classify_term(term)
```

**Config 3: UMLS + NeuroDB-2 (Local Enrichment)**
```python
class UMLSNeuroDBConfig:
    name = "UMLSNeuroDB"  # Config identifier
    use_pubtator = False
    use_neurodb = True

    def __init__(self):
        """Initialize UMLS client and load NeuroDB-2."""
        import os
        import json
        from clients.umls import UMLSClient
        api_key = os.getenv("UMLS_API_KEY")
        self.umls_client = UMLSClient(api_key)

        # Load NeuroDB-2 with relative path
        neurodb_path = os.path.join(os.path.dirname(__file__), '../../../data/neuro_terms.json')
        with open(neurodb_path) as f:
            self.neurodb = json.load(f)

    def classify_term(self, term):
        # Step 1: NeuroDB-2 abbreviation lookup
        if term.lower() in self.neurodb.get('abbreviations', {}):
            term = self.neurodb['abbreviations'][term.lower()]['expansion']

        # Step 2: UMLS classification
        return self.umls_client.classify_term(term)
```

**Config 4: UMLS + PubTator + NeuroDB-2 (Full Hybrid)**
```python
class FullHybridConfig:
    name = "FullHybrid"  # Config identifier
    use_pubtator = True
    use_neurodb = True

    def __init__(self):
        """Initialize all clients: UMLS, PubTator, and NeuroDB-2."""
        import os
        import json
        from clients.umls import UMLSClient
        from clients.pubtator import PubTatorClient
        api_key = os.getenv("UMLS_API_KEY")
        self.umls_client = UMLSClient(api_key)
        self.pubtator_client = PubTatorClient()

        # Load NeuroDB-2 with relative path
        neurodb_path = os.path.join(os.path.dirname(__file__), '../../../data/neuro_terms.json')
        with open(neurodb_path) as f:
            self.neurodb = json.load(f)

    @staticmethod
    def is_abbreviation(term):
        """Check if term is likely an abbreviation."""
        return len(term) <= 5 or term.isupper() or (len(term.split()) == 1 and len(term) <= 10)

    def classify_term(self, term):
        # Layer 1: NeuroDB-2 (neuroscience-specific)
        if term.lower() in self.neurodb.get('abbreviations', {}):
            resolved = self.neurodb['abbreviations'][term.lower()]['expansion']
            return self.umls_client.classify_term(resolved)

        # Layer 2: PubTator (biomedical general)
        if self.is_abbreviation(term):
            disambiguation = self.pubtator_client.disambiguate_term(term)
            if disambiguation['confidence'] > 0.5:
                resolved = disambiguation['resolved']
                return self.umls_client.classify_term(resolved)

        # Layer 3: UMLS direct lookup
        return self.umls_client.classify_term(term)
```

---

### 2.2.1 Configuration Capability Matrix

**Purpose**: Defines which metrics each configuration can produce to ensure fair comparison.

| Capability | Baseline | UMLS-only | UMLS+PubTator | UMLS+NeuroDB-2 | Full Hybrid |
|------------|----------|-----------|---------------|----------------|-------------|
| **Abbreviation Expansion** | ✅ (via neuro_terms.json) | ❌ | ✅ (PubTator) | ✅ (NeuroDB-2) | ✅ (both) |
| **Semantic Classification** | ❌ (blind expansion) | ✅ (UMLS) | ✅ (UMLS) | ✅ (UMLS) | ✅ (UMLS) |
| **Component Detection** | ✅ (rule-based) | ❌ | ❌ | ❌ | ❌ |
| **Synonym Expansion** | ✅ (neuro_terms.json) | ❌ | ❌ | ✅ (NeuroDB-2) | ✅ (NeuroDB-2) |

**Metric Applicability**:
```python
CAPABILITY_MATRIX = {
    'LexStream2Baseline': {
        'supports_semantic_classification': False,  # Skip semantic_accuracy metric
        'supports_abbreviation_expansion': True,
        'supports_component_detection': True,
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
```

**Usage in Evaluators**:
```python
# evaluators/semantic_accuracy.py
def evaluate(self, results, config_name):
    if not CAPABILITY_MATRIX[config_name]['supports_semantic_classification']:
        return {'skipped': True, 'reason': 'Configuration does not support semantic classification'}
    # ... normal evaluation
```

---

### 2.3 Test Runner Architecture

```python
# tests/test_runner.py

class SemanticPipelineTestRunner:
    """
    Orchestrates test execution across all 5 tool configurations (including Lex Stream 2 baseline).
    Supports parallel execution, result collection, comparison generation.
    """

    def __init__(self, test_suite_path: str):
        self.test_suites = self.load_test_suites(test_suite_path)
        self.configurations = [
            LexStream2BaselineConfig(),  # BASELINE - current production
            UMLSOnlyConfig(),
            UMLSPubTatorConfig(),
            UMLSNeuroDBConfig(),
            FullHybridConfig()
        ]
        self.results = []

    def run_all_tests(self, parallel: bool = True):
        """Execute all test cases across all configurations."""
        for config in self.configurations:
            for suite_name, test_cases in self.test_suites.items():
                suite_results = self.run_test_suite(
                    config, suite_name, test_cases, parallel
                )
                self.results.append(suite_results)

        return self.generate_comparison_report()

    def run_test_suite(self, config, suite_name, test_cases, parallel):
        """Run single test suite with specific configuration."""
        if parallel:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(self.run_single_test, config, tc)
                    for tc in test_cases
                ]
                results = [f.result() for f in futures]
        else:
            results = [
                self.run_single_test(config, tc)
                for tc in test_cases
            ]

        return {
            'config': config.name,
            'suite': suite_name,
            'results': results,
            'summary': self.summarize_results(results)
        }

    def run_single_test(self, config, test_case):
        """Execute single test case and collect metrics."""
        start_time = time.time()

        try:
            # Build pipeline with configuration
            pipeline = SemanticQueryPipeline(config)

            # Run query
            result = pipeline.run(
                user_input=test_case['input'],
                days=60,
                max_results=20,
                verbose=False
            )

            latency_seconds = time.time() - start_time

            # Evaluate result
            evaluation = self.evaluate_result(test_case, result)

            # NOTE: Runner measures latency externally and embeds it in result record.
            # This is the AUTHORITATIVE latency field that evaluators should use.
            # Pipeline's internal timing is NOT used to ensure consistent measurement.
            return {
                'test_id': test_case['test_id'],
                'input': test_case['input'],
                'config': config.name,
                'result_count': result['result_count'],
                'latency_seconds': latency_seconds,  # AUTHORITATIVE latency measurement
                'api_calls': self.count_api_calls(config, result),
                'classifications': result['classifications'],
                'query': result['query'],
                'evaluation': evaluation,
                'status': 'PASS' if evaluation['pass'] else 'FAIL',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'test_id': test_case['test_id'],
                'config': config.name,
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def count_api_calls(self, config, result):
        """
        Count API calls made during query processing.

        Args:
            config: Configuration object indicating which APIs are enabled
            result: Pipeline result containing query metadata

        Returns:
            dict: API call counts by service
        """
        api_calls = {'pubmed': 1}  # Always 1 PubMed search

        # Count UMLS calls (one per term if semantic classification enabled)
        if hasattr(config, 'umls_client') and config.umls_client:
            terms = result.get('terms', [])
            api_calls['umls'] = len(terms)

        # Count PubTator calls (one per abbreviation detected)
        if config.use_pubtator:
            abbreviations = [t for t in result.get('terms', [])
                           if config.is_abbreviation(t)]
            api_calls['pubtator'] = len(abbreviations)

        return api_calls
```

---

### 2.4 Evaluation Metrics

**Quantitative Metrics** (automated):
```python
class QuantitativeMetrics:
    """
    Evaluates quantitative metrics from test runner records.

    NOTE: `result` parameter is the runner's output record (not raw pipeline output).
    The runner embeds authoritative measurements like latency_seconds.
    """
    def evaluate(self, test_case, result):
        return {
            'result_count': result['result_count'],
            'in_target_range': 5 <= result['result_count'] <= 20,
            'latency_seconds': result['latency_seconds'],  # From runner, not pipeline
            'latency_acceptable': result['latency_seconds'] < 2.0,
            'api_calls': {
                'pubtator': self.count_pubtator_calls(result),
                'umls': self.count_umls_calls(result),
                'pubmed': 1  # Always 1 for search
            },
            'total_api_calls': self.count_total_api_calls(result)
        }
```

**Semantic Accuracy Metrics** (automated):
```python
class SemanticAccuracyMetrics:
    def evaluate(self, test_case, result):
        expected = test_case.get('expected_classifications', {})
        actual = result['classifications']

        accuracy = {
            'total_terms': len(actual),
            'correct_classifications': 0,
            'incorrect_classifications': 0,
            'details': []
        }

        for i, cls in enumerate(actual):
            expected_category = expected.get(cls['term'], {}).get('category')

            if expected_category:
                is_correct = cls['category'] == expected_category
                accuracy['correct_classifications' if is_correct else 'incorrect_classifications'] += 1

                accuracy['details'].append({
                    'term': cls['term'],
                    'expected': expected_category,
                    'actual': cls['category'],
                    'correct': is_correct
                })

        accuracy['accuracy_rate'] = (
            accuracy['correct_classifications'] / accuracy['total_terms']
            if accuracy['total_terms'] > 0 else 0
        )

        return accuracy
```

**Relevance Scoring** (manual validation):
```python
class RelevanceScorer:
    """
    Manual scoring of result relevance by neuroscientist.
    For automated testing, use heuristic relevance estimation.
    """

    def estimate_relevance(self, test_case, result):
        """
        Heuristic estimation until manual review available.
        Checks if query terms appear in returned article titles/abstracts.
        """
        articles = result['articles']
        query_terms = test_case['input'].lower().split()

        relevance_scores = []
        for article in articles[:10]:  # Top 10 only
            title = article.get('title', '').lower()
            abstract = article.get('abstract', '').lower()
            content = f"{title} {abstract}"

            # Count query term appearances
            matches = sum(1 for term in query_terms if term in content)
            score = matches / len(query_terms) if query_terms else 0

            relevance_scores.append({
                'pmid': article['pmid'],
                'title': article['title'][:80],
                'score': score,
                'matches': matches
            })

        avg_score = sum(r['score'] for r in relevance_scores) / len(relevance_scores) if relevance_scores else 0

        return {
            'estimated_precision': avg_score,
            'top_10_scores': relevance_scores,
            'requires_manual_review': avg_score < 0.6  # Low confidence
        }
```

---

### 2.5 Comparison Analyzer

```python
class ComparisonAnalyzer:
    """
    Cross-configuration comparison generator.
    Identifies which tool combinations perform best for each test category.
    """

    def generate_comparison(self, all_results):
        comparison = {
            'by_configuration': self.compare_by_config(all_results),
            'by_test_category': self.compare_by_category(all_results),
            'by_metric': self.compare_by_metric(all_results),
            'winner_analysis': self.determine_winners(all_results)
        }

        return comparison

    def compare_by_config(self, results):
        """Aggregate metrics per configuration."""
        configs = {}
        for r in results:
            config = r['config']
            if config not in configs:
                configs[config] = {
                    'total_tests': 0,
                    'passed': 0,
                    'failed': 0,
                    'avg_latency': [],
                    'avg_result_count': [],
                    'avg_accuracy': []
                }

            configs[config]['total_tests'] += 1
            configs[config]['passed' if r['status'] == 'PASS' else 'failed'] += 1
            configs[config]['avg_latency'].append(r.get('latency_seconds', 0))
            configs[config]['avg_result_count'].append(r.get('result_count', 0))

            if 'evaluation' in r and 'accuracy' in r['evaluation']:
                configs[config]['avg_accuracy'].append(
                    r['evaluation']['accuracy']['accuracy_rate']
                )

        # Calculate averages
        for config in configs.values():
            config['avg_latency'] = statistics.mean(config['avg_latency'])
            config['avg_result_count'] = statistics.mean(config['avg_result_count'])
            config['avg_accuracy'] = statistics.mean(config['avg_accuracy']) if config['avg_accuracy'] else 0
            config['pass_rate'] = config['passed'] / config['total_tests']

        return configs

    def determine_winners(self, results):
        """Identify best configuration per category."""
        categories = ['abbreviations', 'multi_term', 'semantic_ambiguity',
                      'complex_queries', 'edge_cases', 'rare_terms',
                      'outcome_measures', 'benchmarks']

        winners = {}
        for category in categories:
            category_results = [r for r in results if category in r['test_id'].lower()]

            if not category_results:
                continue

            # Score by: pass rate (50%) + accuracy (30%) + result count (20%)
            scores = {}
            for config in ['UMLS-only', 'UMLS+PubTator', 'UMLS+NeuroDB', 'Full Hybrid']:
                config_results = [r for r in category_results if r['config'] == config]

                if not config_results:
                    continue

                pass_rate = sum(1 for r in config_results if r['status'] == 'PASS') / len(config_results)
                avg_accuracy = statistics.mean([
                    r['evaluation']['accuracy']['accuracy_rate']
                    for r in config_results
                    if 'evaluation' in r and 'accuracy' in r['evaluation']
                ]) if config_results else 0

                in_range_rate = sum(
                    1 for r in config_results
                    if 5 <= r.get('result_count', 0) <= 20
                ) / len(config_results)

                score = (pass_rate * 0.5) + (avg_accuracy * 0.3) + (in_range_rate * 0.2)
                scores[config] = score

            winners[category] = {
                'best_config': max(scores, key=scores.get),
                'score': max(scores.values()),
                'all_scores': scores
            }

        return winners
```

---

## 3. TEST EXECUTION PHASES

### Phase 1: Automated Testing (Week 1)

**Scope**: All test categories except manual validation

**Steps**:
1. Load test data from JSON files
2. Execute tests in parallel (5 concurrent threads)
3. Collect quantitative metrics
4. Generate automated comparison report

**Command**:
```bash
python tests/test_runner.py --parallel --output results/comparisons/run_<timestamp>.json
```

**Deliverables**:
- JSON results file with all metrics
- Markdown comparison report
- Pass/fail summary by configuration

---

### Phase 2: Manual Validation (Week 2)

**Scope**: Benchmark queries (BM-001 to BM-005)

**Steps**:
1. Extract top 10 results for each benchmark query
2. Present to James (neuroscientist) for relevance scoring
3. Manual scoring: 0 (irrelevant) to 5 (highly relevant)
4. Calculate precision@10 for each configuration

**Validation Form**:
```
Test: BM-001 (TMS, stroke, memory)
Configuration: UMLS + PubTator

Paper 1: [Title]
PMID: 12345678
Relevance: ☐ 0  ☐ 1  ☐ 2  ☐ 3  ☐ 4  ☐ 5
Notes: _______________________

[Repeat for papers 2-10]

Overall Query Quality: ☐ Poor  ☐ Fair  ☐ Good  ☐ Excellent
```

**Precision Calculation**:
```
Precision@10 = (Count of papers scored ≥3) / 10
Target: ≥0.80 (80%)
```

---

### Phase 3: Performance Benchmarking (Week 2)

**Scope**: Latency, API call count, caching impact

**Metrics**:
- Cold start latency (no cache)
- Warm latency (with cache)
- API calls per query
- Cache hit rate

**Test Procedure**:
1. Run each test 10 times (cold start)
2. Record latency distribution (p50, p95, p99)
3. Enable Redis cache
4. Run each test 10 more times (warm)
5. Compare cold vs warm performance

**Target**:
- Cold start: <5s acceptable
- Warm: <2s required
- Cache hit rate: >80%

---

### Phase 4: Comparison Analysis (Week 3)

**Scope**: Cross-configuration decision matrix

**Analysis**:
1. Aggregate all quantitative + qualitative metrics
2. Generate comparison matrix
3. Identify winner by test category
4. Cost-benefit analysis (API calls vs accuracy)
5. Recommendation report

**Decision Matrix Example**:

| Metric | UMLS-only | UMLS+PubTator | UMLS+NeuroDB | Full Hybrid |
|--------|-----------|---------------|--------------|-------------|
| Abbreviation Accuracy | 20% | 85% | 90% | 95% |
| Semantic Accuracy | 95% | 95% | 95% | 95% |
| Avg Latency (cold) | 3.5s | 4.2s | 3.8s | 4.5s |
| Avg Latency (warm) | 1.2s | 1.5s | 1.3s | 1.6s |
| API Calls/Query | 5 | 8 | 7 | 10 |
| Result Range 5-20 | 60% | 85% | 80% | 90% |
| Precision@10 | 70% | 82% | 78% | 85% |
| **Overall Score** | 65% | **88%** | 83% | **90%** |

---

## 4. SUCCESS CRITERIA

### 4.1 Per-Configuration Thresholds

**Pass Criteria** (must meet ALL):
- ✅ Semantic accuracy: ≥90% for known terms
- ✅ Result count in range (5-20): ≥75% of queries
- ✅ Latency (warm): <2s for 95% of queries
- ✅ Precision@10: ≥80% (manual validation)
- ✅ No critical errors (API failures, crashes)

**Optional Quality Metrics**:
- Abbreviation disambiguation: ≥85%
- Coverage of rare terms: ≥60%
- Cache hit rate: ≥80%

---

### 4.2 Overall Test Suite Success

**Deployment-Ready Criteria**:
- At least 1 configuration meets all pass criteria
- Clear winner identified for each test category
- Cost-benefit analysis documented
- Neuroscientist (James) approval on benchmark queries

---

## 5. VALIDATION APPROACH

### 5.1 Gold Standard Creation

**Method**: Manual curation of expected results for 10 benchmark queries

**Process**:
1. Execute each benchmark query manually in PubMed
2. Review top 20 results
3. Classify by relevance (highly relevant, relevant, marginal, irrelevant)
4. Document expected semantic classifications
5. Store in `tests/fixtures/gold_standard.json`

**Gold Standard Schema**:
```json
{
  "BM-001": {
    "input": "TMS, stroke, memory",
    "expected_classifications": {
      "TMS": {
        "category": "INTERVENTION",
        "cui": "C0436548",
        "name": "Transcranial Magnetic Stimulation"
      },
      "stroke": {
        "category": "CONDITION",
        "cui": "C0038454",
        "name": "Cerebrovascular accident"
      },
      "memory": {
        "category": "OUTCOME",
        "cui": "C0025260",
        "name": "Memory"
      }
    },
    "expected_result_count": {
      "min": 10,
      "max": 20
    },
    "highly_relevant_pmids": [12345678, 87654321],
    "irrelevant_pmids": [11111111],
    "notes": "Should find TMS trials in stroke patients measuring memory outcomes"
  }
}
```

---

### 5.2 Neuroscientist Review Protocol

**Reviewer**: James (neuroscientist, Lex Stream stakeholder)

**Review Scope**: 5 benchmark queries × 4 configurations = 20 result sets

**Review Form**:
1. **Query Understanding**: Did the system interpret the query correctly? (Yes/No)
2. **Top 10 Relevance**: Score each paper 0-5
3. **Missing Papers**: Were obvious papers missed? (List PMIDs)
4. **False Positives**: Were irrelevant papers included? (List PMIDs)
5. **Overall Quality**: Poor / Fair / Good / Excellent
6. **Comments**: Free text feedback

**Deliverable**: Completed review forms → aggregated precision scores per configuration

---

### 5.3 Error Analysis Framework

**Goal**: Understand failure modes and improvement opportunities

**Categories**:
1. **Disambiguation Failures**: Abbreviation resolved incorrectly
2. **Classification Errors**: Semantic type wrong (e.g., INTERVENTION → CONDITION)
3. **Coverage Gaps**: Term not found in any source
4. **Query Building Issues**: Poor query structure, wrong tags
5. **API Errors**: Timeout, rate limit, service unavailable

**Process**:
1. Collect all failed tests
2. Categorize by error type
3. Identify patterns (e.g., "All rare terms fail", "UK spellings mishandled")
4. Document in error log with suggested fixes

**Error Log Schema**:
```json
{
  "test_id": "RARE-006",
  "error_type": "coverage_gap",
  "description": "Term 'sharp wave ripples' not found in UMLS, PubTator, or NeuroDB-2",
  "impact": "Query failed to execute, returned 0 results",
  "suggested_fix": "Add term to NeuroDB-2 with definition and MeSH mapping",
  "priority": "medium"
}
```

---

## 6. COMPARISON METHODOLOGY

### 6.1 Fairness Criteria

**Ensure fair comparison**:
- ✅ Same test cases for all configurations
- ✅ Same UMLS API version
- ✅ Same PubMed database state (run tests within 24 hours)
- ✅ Same date filter (last 60 days)
- ✅ Same max results limit (20)
- ✅ Identical evaluation metrics

**Control Variables**:
- Network latency: Run tests from same machine
- Cache state: Clear cache between configurations
- API rate limits: Use delays to avoid throttling

---

### 6.2 Statistical Significance

**For latency comparisons**:
- Run each test 10 times
- Calculate mean + standard deviation
- Use t-test to determine if latency differences are significant (p<0.05)

**For accuracy comparisons**:
- Calculate 95% confidence intervals
- Report accuracy as: mean ± CI (e.g., 85% ± 3%)

---

### 6.3 Cost-Benefit Analysis

**Metrics**:
- **Cost**: API calls per query, latency, maintenance overhead
- **Benefit**: Accuracy, coverage, user satisfaction

**Example Analysis**:

| Configuration | API Calls | Latency | Accuracy | Coverage | **Score** |
|---------------|-----------|---------|----------|----------|-----------|
| UMLS-only | 5 | 1.2s | 75% | 60% | 60 |
| UMLS+PubTator | 8 | 1.5s | 88% | 85% | **82** |
| UMLS+NeuroDB | 7 | 1.3s | 85% | 90% | 80 |
| Full Hybrid | 10 | 1.6s | 90% | 95% | **85** |

**Score Formula**:
```
Score = (Accuracy × 0.4) + (Coverage × 0.3) + ((1 - normalized_latency) × 0.2) + ((1 - normalized_API_calls) × 0.1)
```

**Decision Rule**:
- If Full Hybrid score > 85 AND latency <2s → **RECOMMEND Full Hybrid**
- Else if UMLS+PubTator score > 80 → **RECOMMEND UMLS+PubTator** (current proven)
- Else → **INVESTIGATE ISSUES**

---

## 7. IMPLEMENTATION ROADMAP

### Week 1: Framework Setup + Automated Tests

**Day 1-2**: Test infrastructure
- [ ] Create directory structure
- [ ] Implement test configurations (4 classes)
- [ ] Implement test runner
- [ ] Implement evaluators (quantitative, semantic, relevance)

**Day 3-4**: Test data creation
- [ ] Create all test case JSON files (60+ test cases)
- [ ] Implement test data loader
- [ ] Validate test data schema

**Day 5**: Automated execution
- [ ] Run all automated tests (parallel)
- [ ] Generate comparison report (JSON + Markdown)
- [ ] Fix any infrastructure bugs

**Deliverables**:
- ✅ Working test framework
- ✅ Initial automated results
- ✅ Comparison matrix (automated metrics only)

---

### Week 2: Manual Validation + Performance

**Day 1-2**: Benchmark preparation
- [ ] Extract top 10 results for 5 benchmarks × 4 configs = 20 sets
- [ ] Format for James review (PDF or web form)
- [ ] Schedule review session with James

**Day 3**: Manual review
- [ ] James reviews results
- [ ] Calculate precision@10 per configuration
- [ ] Document feedback

**Day 4-5**: Performance benchmarking
- [ ] Run latency tests (10× per test case)
- [ ] Test with/without cache
- [ ] Measure API call counts
- [ ] Generate performance report

**Deliverables**:
- ✅ Manual validation results
- ✅ Performance benchmarks
- ✅ Updated comparison matrix (with precision scores)

---

### Week 3: Analysis + Recommendations

**Day 1-2**: Error analysis
- [ ] Categorize all failures
- [ ] Identify patterns
- [ ] Document error log

**Day 3**: Comparison analysis
- [ ] Aggregate all metrics (quantitative + qualitative + performance)
- [ ] Generate decision matrix
- [ ] Run cost-benefit analysis
- [ ] Determine winners by category

**Day 4-5**: Final report
- [ ] Write executive summary
- [ ] Document recommendations
- [ ] Create implementation plan for chosen configuration
- [ ] Present to stakeholders

**Deliverables**:
- ✅ Comprehensive comparison report
- ✅ Winner identification by category
- ✅ Recommendation: Which hybrid approach to adopt
- ✅ Next steps for production deployment

---

## 8. EXPECTED OUTCOMES

### 8.1 Predicted Results

**Based on POC findings**:

**UMLS-only**:
- ❌ Fails on abbreviations (20% accuracy)
- ✅ Good semantic classification (95%)
- ✅ Fast latency (1.2s)
- ❌ Poor result quality (many 0 or 1000+ results)

**UMLS + PubTator** (current proven):
- ✅ **Excellent abbreviation handling (85%)**
- ✅ **Good semantic classification (95%)**
- ⚠️ Moderate latency (1.5s)
- ✅ **Balanced results (85% in 5-20 range)**

**UMLS + NeuroDB-2**:
- ✅ **Excellent neuroscience abbreviations (90%)**
- ✅ Good semantic classification (95%)
- ✅ Fast latency (1.3s)
- ✅ Good results for neuroscience queries (80% in range)
- ⚠️ Limited biomedical coverage (fails on non-neuro terms)

**Full Hybrid**:
- ✅ **Best abbreviation handling (95%)**
- ✅ **Best semantic classification (95%)**
- ⚠️ Slowest latency (1.6s)
- ✅ **Best result quality (90% in range)**
- ⚠️ Most complex (maintenance overhead)

---

### 8.2 Anticipated Winner

**Primary Recommendation**: **UMLS + PubTator + NeuroDB-2 (Full Hybrid)**

**Rationale**:
- Addresses neuroscientist feedback (James) on term coverage
- Leverages NeuroDB-2's 595 curated terms (22% abbreviation coverage)
- PubTator handles biomedical terms outside neuroscience
- UMLS provides semantic backbone
- Proven POC baseline (UMLS+PubTator) as foundation

**Trade-offs**:
- Slightly higher latency (acceptable with caching)
- More complex architecture (justified by accuracy gains)
- Requires NeuroDB-2 maintenance (already in place)

**Fallback**: If latency >2s unacceptable → **UMLS + PubTator** (proven, simpler)

---

## 9. RISKS & MITIGATIONS

### Risk 1: API Rate Limits
**Impact**: Tests fail due to UMLS throttling (20 req/s, 5000 req/hr)
**Mitigation**:
- Implement request queuing with delays
- Use mock APIs for CI/CD testing
- Run live API tests in batches

### Risk 2: NeuroDB-2 Coverage Gaps
**Impact**: Rare term tests fail
**Mitigation**:
- Document coverage gaps as expected failures
- Prioritize top 1K-5K terms for enrichment
- Use UMLS as fallback

### Risk 3: Manual Review Availability
**Impact**: James unavailable for validation
**Mitigation**:
- Use heuristic relevance estimation as proxy
- Schedule review session in advance
- Accept delayed validation if needed

### Risk 4: Result Instability
**Impact**: PubMed results change day-to-day (new publications)
**Mitigation**:
- Run all configurations within 24 hours
- Accept ±2 result count variance as normal
- Focus on relative comparison, not absolute numbers

### Risk 5: Test Framework Bugs
**Impact**: Invalid results due to implementation errors
**Mitigation**:
- Unit test each evaluator component
- Manual spot-check 10% of results
- Version control all test data

---

## 9.5 PLAN VALIDATION CHECKLIST

⚠️ **THIS PLAN IS CURRENTLY UNVALIDATED** - Created by AI planner without external review.

### Required Validation Steps Before Implementation:

**1. Domain Expert Review (Neuroscientist)**
- [ ] Review test cases with James or equivalent neuroscientist
- [ ] Validate that test queries represent real-world use cases
- [ ] Confirm success metrics (5-20 papers, 80% precision) are appropriate
- [ ] Identify missing edge cases or neuroscience-specific scenarios

**2. Technical Review (Independent Engineer)**
- [ ] Review architecture and tool configurations for correctness
- [ ] Validate metric definitions and thresholds
- [ ] Check test framework design for completeness
- [ ] Identify implementation risks and dependencies

**3. Stakeholder Alignment**
- [ ] Confirm Lex Stream 2 baseline is correctly characterized
- [ ] Validate that comparison is fair and addresses business goals
- [ ] Ensure timeline (3 weeks) aligns with project priorities
- [ ] Get buy-in on expected scores and success criteria

**4. Cross-Validation with Existing Data**
- [ ] Compare predicted scores against POC results ("MS + neuromodulation" = 5 hits)
- [ ] Validate expected tool performance against known capabilities
- [ ] Check test case catalog against known abbreviation/synonym lists

**5. Plan Refinement**
- [ ] Address all unresolved questions (Section 10)
- [ ] Adjust scope based on validation feedback
- [ ] Finalize success criteria with stakeholder input
- [ ] Create implementation-ready version after validation

### Validation Sign-off:
- [ ] Domain Expert: _________________ Date: _______
- [ ] Technical Reviewer: _____________ Date: _______
- [ ] Product Owner: _________________ Date: _______

**Status**: ❌ NOT VALIDATED - Do not proceed to implementation until checklist complete

---

## 10. UNRESOLVED QUESTIONS

1. **NeuroDB-2 Integration Depth**: Should NeuroDB-2 provide full synonym expansion OR only abbreviation disambiguation?

2. **UMLS Caching Strategy**: Cache all 325K UMLS terms OR only top 5K neuroscience terms?

3. **Context-Aware Disambiguation**: Should "MS treatment" use surrounding words to disambiguate OR rely on PubTator's first match?

4. **MeSH Hierarchy Integration**: Wait for MeSH tree implementation (3-month timeline) OR proceed with flat semantic types?

5. **Production Latency Target**: Is 2s hard requirement OR acceptable if accuracy significantly higher?

6. **Test Suite Maintenance**: Who updates test cases as PubMed database evolves?

7. **Benchmark Expansion**: 5 benchmarks sufficient OR need 20+ for statistical confidence?

8. **Fallback Strategy**: If all tools fail (term not found), return 0 results OR fallback to blind expansion?

9. **Multi-Language Support**: Test only English OR include UK spelling variants as separate test category?

10. **Continuous Testing**: Run test suite weekly (CI/CD) OR only on major changes?

---

## 11. APPENDICES

### Appendix A: Test Data Schema

**abbreviations.json**:
```json
[
  {
    "test_id": "ABB-001",
    "category": "abbreviation",
    "input": "MS",
    "expected_expansion": "Multiple Sclerosis",
    "expected_classifications": {
      "MS": {
        "category": "CONDITION",
        "semantic_type": "Disease or Syndrome",
        "cui": "C0026769"
      }
    },
    "ambiguity_level": "HIGH",
    "notes": "Also: Mass Spectrometry (chemical analysis)"
  }
]
```

---

### Appendix B: Report Template

**Comparison Report Structure**:
```markdown
# Semantic Pipeline Test Results - <Timestamp>

## Executive Summary
- Total tests: 60
- Configurations tested: 4
- Pass rate: 85%
- Winner: Full Hybrid (90% score)

## Results by Configuration
### UMLS-only
- Pass rate: 65%
- Avg latency: 1.2s
- Precision@10: 70%

[Repeat for all configs]

## Results by Test Category
### Abbreviations
- Winner: Full Hybrid (95% accuracy)
- UMLS-only: 20% (FAIL)
- UMLS+PubTator: 85% (PASS)
- UMLS+NeuroDB: 90% (PASS)

[Repeat for all categories]

## Recommendations
1. Deploy Full Hybrid configuration
2. Implement Redis cache (target: <2s latency)
3. Enrich NeuroDB-2 with top 1K rare terms

## Next Steps
[Action items]
```

---

### Appendix C: File Paths

**Test Framework** (relative to project root):
- `poc-api-first/tests/test_runner.py`
- `poc-api-first/tests/test_configurations.py`
- `poc-api-first/tests/test_data/*.json`

**Existing Code**:
- `poc-api-first/poc_pipeline.py`
- `poc-api-first/clients/umls.py`
- `poc-api-first/clients/pubtator.py`
- `poc-api-first/clients/pubmed.py`

**Data Sources**:
- `data/neuro_terms.json` (595 terms, 126 abbreviations)
- UMLS API: `https://uts-ws.nlm.nih.gov/rest`
- PubTator API: `https://www.ncbi.nlm.nih.gov/research/pubtator3-api`

---

**Plan Status**: ✅ COMPLETE
**Next Action**: Review plan → Begin Week 1 implementation
**Estimated Timeline**: 3 weeks (setup → validation → analysis)
**Expected Outcome**: Recommendation report identifying optimal hybrid configuration
