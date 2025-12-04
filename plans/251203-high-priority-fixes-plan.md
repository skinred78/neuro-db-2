# HIGH Priority Fixes Implementation Plan

**Date**: 2025-12-03
**Project**: NeuroDB-2 POC API-First
**Purpose**: Address 10 HIGH priority issues from Codex technical review
**Context**: Main plan at `plans/251203-semantic-pipeline-test-suite-design.md`
**Review**: `plans/codex-technical-review-20251203-1007.md`

---

## EXECUTIVE SUMMARY

**Status**: 5 CRITICAL issues fixed, 10 HIGH priority issues remaining
**Goal**: Make test framework production-ready
**Total Effort**: ~7.5 hours (see breakdown below)
**Priority**: Implement in order (issues 1-3 block execution, 4-10 affect validity)

**Fixed CRITICAL Issues**:
1. ✅ Capability matrix added (Section 2.2.1)
2. ✅ Latency standardization (Section 2.3, runner embeds authoritative `latency_seconds`)
3. ✅ Undefined attributes documented (config schema clarified)
4. ✅ Baseline definition clarified (blind semantic, rule-based components)
5. ✅ Hardcoded paths → repo-relative (with note to fix in code)

**Remaining HIGH Issues**: Addressed below in priority order

---

## ISSUE 1: CONCURRENCY VS RATE LIMITING

**Source**: Section 2.3, Line 499
**Problem**: `ThreadPoolExecutor(max_workers=5)` without API throttling coordination
**Risk**: PubTator/UMLS rate-limit errors (UMLS: 20 req/s, 5000 req/hr), noisy latency measurements
**Severity**: HIGH (blocks reliable execution)

### Root Cause
Parallel test execution → burst of API calls → rate limits → errors/retries → unpredictable latency

### Solution: API Request Queue with Rate Limiting

**Affected Files**:
- `poc-api-first/tests/test_runner.py` (Section 2.3)
- NEW: `poc-api-first/utils/rate_limiter.py`

**Implementation**:

```python
# poc-api-first/utils/rate_limiter.py
import time
import threading
from collections import deque
from typing import Callable, Any

class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    Thread-safe, coordinates across parallel test executions.
    """
    def __init__(self, requests_per_second: int, requests_per_hour: int):
        self.req_per_sec = requests_per_second
        self.req_per_hour = requests_per_hour

        # Token buckets
        self.sec_tokens = requests_per_second
        self.hour_tokens = requests_per_hour

        # Locks
        self.sec_lock = threading.Lock()
        self.hour_lock = threading.Lock()

        # Refill tracking
        self.last_sec_refill = time.time()
        self.last_hour_refill = time.time()
        self.hour_window = deque(maxlen=requests_per_hour)

    def acquire(self):
        """Block until token available from both buckets."""
        while True:
            with self.sec_lock:
                self._refill_sec()
                if self.sec_tokens > 0:
                    self.sec_tokens -= 1
                    sec_ok = True
                else:
                    sec_ok = False

            with self.hour_lock:
                self._refill_hour()
                if self.hour_tokens > 0:
                    self.hour_tokens -= 1
                    self.hour_window.append(time.time())
                    hour_ok = True
                else:
                    hour_ok = False

            if sec_ok and hour_ok:
                return
            else:
                time.sleep(0.05)  # 50ms backoff

    def _refill_sec(self):
        """Refill per-second bucket."""
        now = time.time()
        elapsed = now - self.last_sec_refill
        if elapsed >= 1.0:
            self.sec_tokens = self.req_per_sec
            self.last_sec_refill = now

    def _refill_hour(self):
        """Refill per-hour bucket (sliding window)."""
        now = time.time()
        # Remove tokens older than 1 hour
        while self.hour_window and (now - self.hour_window[0]) > 3600:
            self.hour_window.popleft()
            self.hour_tokens = min(self.hour_tokens + 1, self.req_per_hour)

# Global rate limiters (shared across threads)
UMLS_LIMITER = RateLimiter(requests_per_second=20, requests_per_hour=5000)
PUBTATOR_LIMITER = RateLimiter(requests_per_second=10, requests_per_hour=1000)  # Conservative

def rate_limited_call(limiter: RateLimiter, func: Callable, *args, **kwargs) -> Any:
    """Execute function after acquiring rate limit token."""
    limiter.acquire()
    return func(*args, **kwargs)
```

**Update Clients**:

```python
# poc-api-first/clients/umls.py
from utils.rate_limiter import UMLS_LIMITER, rate_limited_call

class UMLSClient:
    def classify_term(self, term):
        return rate_limited_call(UMLS_LIMITER, self._classify_term_impl, term)

    def _classify_term_impl(self, term):
        # Original implementation (API call)
        pass

# poc-api-first/clients/pubtator.py
from utils.rate_limiter import PUBTATOR_LIMITER, rate_limited_call

class PubTatorClient:
    def disambiguate_term(self, term):
        return rate_limited_call(PUBTATOR_LIMITER, self._disambiguate_impl, term)

    def _disambiguate_impl(self, term):
        # Original implementation (API call)
        pass
```

**Update Main Plan**:

Add to Section 2.3 after line 499:

```markdown
### 2.3.1 Rate Limiting & Concurrency Control

**Problem**: Parallel execution without API throttling → rate limit errors

**Solution**: Token bucket rate limiter (thread-safe)
- UMLS: 20 req/s, 5000 req/hr (NIH limits)
- PubTator: 10 req/s, 1000 req/hr (conservative)
- Clients wrap API calls with `rate_limited_call()`
- Runner proceeds with `ThreadPoolExecutor(max_workers=5)` safely

**Latency Impact**: Minimal (<50ms backoff) when within limits

**Implementation**: See `poc-api-first/utils/rate_limiter.py`
```

**Effort**: 1 hour (implement + test)

---

## ISSUE 2: FULLHYBRID SHORT-CIRCUITING

**Source**: Section 2.2, Lines 386-400
**Problem**: `FullHybridConfig.classify_term()` returns immediately after NeuroDB match, never consulting PubTator
**Risk**: Missed disambiguation evidence, suboptimal confidence
**Severity**: HIGH (affects accuracy)

### Root Cause
First-match-wins logic → NeuroDB overrides PubTator even when PubTator has higher confidence

### Solution: Confidence-Based Arbitration

**Affected Files**:
- Plan Section 2.2, Config 4 (FullHybrid)
- `poc-api-first/tests/test_configurations.py`

**Implementation**:

```python
class FullHybridConfig:
    """Full hybrid with confidence arbitration (NOT first-match wins)."""

    def classify_term(self, term):
        """
        Multi-source disambiguation with confidence scoring:
        1. Collect all candidate expansions from NeuroDB, PubTator
        2. Score by confidence (source priority + context signals)
        3. Use highest-confidence expansion for UMLS classification

        Scoring:
        - NeuroDB exact match: 1.0 (neuroscience-specific, curated)
        - PubTator high confidence (>0.8): 0.9
        - PubTator medium confidence (0.5-0.8): 0.7
        - Direct UMLS lookup: 0.5 (no expansion)
        """
        candidates = []

        # Layer 1: NeuroDB (neuroscience-specific)
        if term.lower() in self.neurodb.get('abbreviations', {}):
            neurodb_expansion = self.neurodb['abbreviations'][term.lower()]['expansion']
            candidates.append({
                'source': 'NeuroDB',
                'expansion': neurodb_expansion,
                'confidence': 1.0  # Curated neuroscience data
            })

        # Layer 2: PubTator (biomedical general)
        if self.is_abbreviation(term):
            pt_result = self.pubtator_client.disambiguate_term(term)
            if pt_result['confidence'] > 0.5:
                candidates.append({
                    'source': 'PubTator',
                    'expansion': pt_result['resolved'],
                    'confidence': pt_result['confidence'] * 0.9  # Scale down vs NeuroDB
                })

        # Layer 3: Direct UMLS (no expansion)
        candidates.append({
            'source': 'UMLS',
            'expansion': term,  # Literal
            'confidence': 0.5
        })

        # Select highest confidence candidate
        best = max(candidates, key=lambda c: c['confidence'])

        # UMLS classification with metadata
        result = self.umls_client.classify_term(best['expansion'])
        result['disambiguation'] = {
            'original_term': term,
            'resolved_term': best['expansion'],
            'source': best['source'],
            'confidence': best['confidence'],
            'all_candidates': candidates
        }

        return result
```

**Update Main Plan**:

Replace Section 2.2 Config 4 (lines 359-401) with:

```markdown
**Config 4: UMLS + PubTator + NeuroDB-2 (Full Hybrid with Arbitration)**
```python
class FullHybridConfig:
    name = "FullHybrid"
    use_pubtator = True
    use_neurodb = True

    def classify_term(self, term):
        """
        Multi-source confidence arbitration (NOT first-match wins):
        - Collect expansions from NeuroDB (conf=1.0) and PubTator (conf=0.5-0.9)
        - Select highest confidence candidate
        - Return UMLS classification with disambiguation metadata

        Rationale: Avoids short-circuiting, allows evidence combination
        """
        # [Implementation as shown above]
```
```

**Testing**:
- Test case: "MS" (in NeuroDB) vs "PET" (PubTator stronger)
- Expected: NeuroDB wins for "MS" (conf=1.0), PubTator for "PET" if neurodb absent

**Effort**: 30 minutes (refactor + test)

---

## ISSUE 3: RESULT COUNT IN-RANGE AS GATING

**Source**: Sections 2.4 (line 608), 4.1 (line 913)
**Problem**: 5-20 result range used as pass/fail criterion, penalizes valid query variability
**Risk**: False negatives (rare terms rejected), biased comparison
**Severity**: HIGH (affects fairness)

### Root Cause
Treating result count as quality signal when it's actually query specificity

### Solution: Make Result Count Informational, Not Gating

**Affected Sections**:
- Section 2.4 (QuantitativeMetrics)
- Section 4.1 (Success Criteria)

**Plan Updates**:

**1. Update Section 2.4** (replace lines 605-618):

```markdown
**Quantitative Metrics** (automated):
```python
class QuantitativeMetrics:
    """
    NOTE: Runner embeds authoritative `latency_seconds` in record.
    """
    def evaluate(self, test_case, result):
        return {
            'result_count': result['result_count'],
            'in_target_range': 5 <= result['result_count'] <= 20,  # INFORMATIONAL ONLY
            'latency_seconds': result['latency_seconds'],
            'latency_acceptable': result['latency_seconds'] < 2.0,
            'api_calls': {
                'pubtator': self.count_pubtator_calls(result),
                'umls': self.count_umls_calls(result),
                'pubmed': 1
            },
            'total_api_calls': self.count_total_api_calls(result)
        }

    def passes_criteria(self, evaluation):
        """
        Pass criteria: Latency acceptable AND no errors.
        Result count is INFORMATIONAL - not gating.

        Rationale: Rare terms naturally return <5 results;
                   broad interventions naturally return >20.
                   Penalizing either biases comparison unfairly.
        """
        return (
            evaluation['latency_acceptable'] and
            evaluation.get('error') is None
        )
```
```

**2. Update Section 4.1** (replace lines 909-917):

```markdown
### 4.1 Per-Configuration Thresholds

**Pass Criteria** (must meet ALL):
- ✅ Semantic accuracy: ≥90% for known terms
- ✅ Latency (warm): <2s for 95% of queries
- ✅ Precision@10: ≥80% (manual validation) - STAGED (informative early, gating later)
- ✅ No critical errors (API failures, crashes)

**Informational Metrics** (NOT gating):
- Result count in range (5-20): Report %, but do NOT fail tests outside range
  - Rationale: Rare terms (<5), broad interventions (>20) are valid
  - Use: Track distribution, identify outliers for review
- Abbreviation disambiguation: ≥85%
- Coverage of rare terms: ≥60%
- Cache hit rate: ≥80%

**Category-Specific Adjustments**:
- Rare terms (RARE-*): Exclude from result-count expectations
- Complex queries (CPX-*): Allow wider latency tolerance (+500ms)
```
```

**3. Update Section 2.5** (ComparisonAnalyzer):

Replace scoring logic (line 786) to remove `in_range_rate`:

```python
# OLD (line 781-786):
in_range_rate = sum(
    1 for r in config_results
    if 5 <= r.get('result_count', 0) <= 20
) / len(config_results)

score = (pass_rate * 0.5) + (avg_accuracy * 0.3) + (in_range_rate * 0.2)

# NEW:
score = (pass_rate * 0.6) + (avg_accuracy * 0.4)
# Removed in_range_rate (no longer gating)
# Rebalanced: pass_rate 50%→60%, accuracy 30%→40%
```

**Effort**: 15 minutes (text changes only)

---

## ISSUE 4: HEURISTIC RELEVANCE ISSUES

**Source**: Section 2.4, Lines 658-696
**Problem**: String-inclusion of raw tokens in title/abstract (no stemming/synonyms)
**Risk**: Mis-estimated relevance, invalid comparison scoring
**Severity**: HIGH (affects validity)

### Root Cause
Naive string matching → false negatives (synonyms missed) + false positives (substring matches)

### Solution: Downgrade to Placeholder, Require Manual Labels

**Affected Files**:
- Plan Section 2.4 (RelevanceScorer)
- Plan Section 5.2 (Manual validation)

**Plan Updates**:

**1. Update Section 2.4** (replace lines 658-696):

```markdown
**Relevance Scoring** (manual validation required):
```python
class RelevanceScorer:
    """
    Heuristic relevance is PLACEHOLDER ONLY - not used in pass/fail.

    CRITICAL: Do NOT use heuristic scores for comparison/gating until:
    1. Manual labels available (neuroscientist review)
    2. Validated proxy implemented (e.g., MeSH overlap, citation analysis)

    Current heuristic (token inclusion) has known limitations:
    - Misses synonyms (TMS != "transcranial magnetic stimulation")
    - Misses stemming (memory != memories)
    - False positives on substring matches (MS in "amsler")
    """

    def estimate_relevance_placeholder(self, test_case, result):
        """
        PLACEHOLDER heuristic - DO NOT USE for comparison scoring.
        Reports token inclusion for debugging only.
        """
        articles = result['articles']
        query_terms = test_case['input'].lower().split()

        relevance_scores = []
        for article in articles[:10]:
            title = article.get('title', '').lower()
            abstract = article.get('abstract', '').lower()
            content = f"{title} {abstract}"

            matches = sum(1 for term in query_terms if term in content)
            score = matches / len(query_terms) if query_terms else 0

            relevance_scores.append({
                'pmid': article['pmid'],
                'title': article['title'][:80],
                'heuristic_score': score,  # NOT validated
                'matches': matches
            })

        return {
            'placeholder_warning': 'Heuristic scores NOT valid for comparison',
            'requires_manual_review': True,  # ALWAYS requires manual review
            'heuristic_avg': sum(r['heuristic_score'] for r in relevance_scores) / 10,
            'top_10_scores': relevance_scores
        }

    def evaluate_with_manual_labels(self, test_case, result, gold_standard):
        """
        Precision@10 from manual labels (neuroscientist review).

        Args:
            gold_standard: dict with 'relevant_pmids' and 'irrelevant_pmids'

        Returns:
            Precision@10 (0.0-1.0), using manual relevance judgments
        """
        top_10_pmids = [a['pmid'] for a in result['articles'][:10]]
        relevant = gold_standard.get('relevant_pmids', set())

        relevant_retrieved = sum(1 for pmid in top_10_pmids if pmid in relevant)
        precision = relevant_retrieved / 10.0

        return {
            'precision_at_10': precision,
            'relevant_retrieved': relevant_retrieved,
            'relevant_missed': len(relevant - set(top_10_pmids)),
            'irrelevant_retrieved': 10 - relevant_retrieved
        }
```
```

**2. Update Section 4.1** (Success Criteria):

Add clarification after line 916:

```markdown
**NOTE: Precision@10 Staging**:
- **Phase 1 (automated)**: Heuristic placeholder only, NOT used for pass/fail
- **Phase 2 (manual labels)**: Neuroscientist review → precision@10 calculated
- **Phase 3 (validation)**: Precision@10 ≥80% becomes GATING for deployment
```

**3. Update Section 5.2** (Manual Validation):

Add after line 997:

```markdown
**CRITICAL: Manual Labels Required for Comparison**

Heuristic relevance (token matching) is PLACEHOLDER - do NOT use for:
- Configuration comparison scoring
- Pass/fail decisions
- Winner determination

Valid comparison requires:
1. Neuroscientist labels (5 benchmarks × 4 configs = 200 papers)
2. OR validated proxy (MeSH term overlap, citation-based relevance)

Timeline: Phase 2 Week 2 (manual review session with James)
```

**Effort**: 30 minutes (documentation + warning comments)

---

## ISSUE 5: CACHE CONTROL

**Source**: Sections 6.1 (line 1047), Phase 3 (line 867)
**Problem**: "Clear cache between configurations" noted but no identical warm-up procedure
**Risk**: Cache-skewed latency comparisons (Config A benefits from Config B's cache)
**Severity**: HIGH (affects fairness)

### Root Cause
Cache state inconsistent across configurations → non-comparable warm latencies

### Solution: Standardized Cache Warm-Up Protocol

**Affected Sections**:
- Section 6.1 (Fairness Criteria)
- Section 3, Phase 3 (Performance Benchmarking)

**Plan Updates**:

**1. Update Section 6.1** (replace line 1047):

```markdown
### 6.1 Fairness Criteria

**Ensure fair comparison**:
- ✅ Same test cases for all configurations
- ✅ Same UMLS API version
- ✅ Same PubMed database state (run tests within 24 hours)
- ✅ Same date filter (last 60 days)
- ✅ Same max results limit (20)
- ✅ Identical evaluation metrics
- ✅ **Identical cache warm-up procedure (see 6.1.1)**

**Cache Control Protocol** (Section 6.1.1):

#### 6.1.1 Cache Warm-Up and Clearing

**Problem**: Inconsistent cache state → unfair latency comparison

**Solution**: Standardized 3-phase cache protocol per configuration

**Phase A: Cold Start (Cache Clear)**
```python
# Before each configuration test run
redis_client.flushdb()  # Clear ALL cache
# OR if shared cache: namespace by config
redis_client.delete(f"cache:{config_name}:*")
```

**Phase B: Warm-Up (Identical for All Configs)**
```python
# Warm-up set: Fixed 10 queries (not in test suite)
WARMUP_QUERIES = [
    "fMRI motor cortex",
    "Parkinson disease",
    "TMS depression",
    "EEG epilepsy",
    "DBS tremor",
    "stroke rehabilitation",
    "Alzheimer memory",
    "MEG visual cortex",
    "DTI white matter",
    "PET glucose metabolism"
]

def warm_cache(config):
    """Execute warm-up queries in fixed order."""
    for query in WARMUP_QUERIES:
        pipeline = SemanticQueryPipeline(config)
        pipeline.run(query, days=60, max_results=20)
        # Discard results, cache now populated
```

**Phase C: Measurement**
```python
# Run actual test suite (cache warm)
# Latencies now comparable across configs
```

**Execution Order**:
```
For each configuration:
  1. Cache clear (Phase A)
  2. Warm-up (Phase B) - SAME queries, SAME order
  3. Run test suite (Phase C) - measure latencies
  4. Repeat for next configuration
```

**Rationale**: Each config starts with identical cache state → fair warm latency comparison
```

**2. Update Section 3, Phase 3** (replace lines 867-878):

```markdown
### Phase 3: Performance Benchmarking (Week 2)

**Scope**: Latency, API call count, caching impact

**Metrics**:
- Cold start latency (cache cleared)
- Warm latency (after standardized warm-up)
- API calls per query
- Cache hit rate

**Test Procedure**:
1. **For each configuration**:
   - Run cold start: Clear cache → run test suite 1× → record p50/p95/p99
   - Run warm-up: Execute 10 fixed warm-up queries (Section 6.1.1)
   - Run warm test: Run test suite 10× → record p50/p95/p99
   - Record cache hit rate (from cache stats)

2. **Cache Control**:
   - Use Section 6.1.1 protocol (clear → warm-up → measure)
   - Ensure identical warm-up for all configs

**Target**:
- Cold start: <5s acceptable (p95)
- Warm: <2s required (p95)
- Cache hit rate: >80%

**Deliverable**: Performance comparison table with cold/warm latencies per config
```

**Effort**: 30 minutes (documentation + procedure)

---

## ISSUE 6: STATISTICAL METHODS NOT INTEGRATED

**Source**: Section 6.2 (lines 1053-1061)
**Problem**: t-tests and CIs proposed but not wired into evaluators/reports
**Risk**: Non-actionable "significance" claims, unreliable comparison
**Severity**: HIGH (affects validity)

### Root Cause
Statistical methods documented but not implemented in analyzer code

### Solution: Implement Statistical Analysis in ComparisonAnalyzer

**Affected Files**:
- Plan Section 6.2
- Plan Section 2.5 (ComparisonAnalyzer code)
- NEW: `poc-api-first/tests/evaluators/statistical_analyzer.py`

**Implementation**:

```python
# poc-api-first/tests/evaluators/statistical_analyzer.py
import statistics
from scipy import stats
import numpy as np

class StatisticalAnalyzer:
    """
    Statistical significance testing for latency and accuracy comparisons.

    Minimum sample sizes:
    - Latency: n≥10 per config per test case (for t-test)
    - Accuracy: n≥30 per config (for CI estimation)
    """

    @staticmethod
    def compare_latencies(config_a_latencies, config_b_latencies, alpha=0.05):
        """
        Two-sample t-test for latency difference.

        Args:
            config_a_latencies: List[float] (≥10 samples)
            config_b_latencies: List[float] (≥10 samples)
            alpha: Significance level (default 0.05)

        Returns:
            {
                'mean_a': float,
                'mean_b': float,
                'difference': float,
                't_statistic': float,
                'p_value': float,
                'significant': bool,
                'interpretation': str
            }
        """
        if len(config_a_latencies) < 10 or len(config_b_latencies) < 10:
            return {'error': 'Insufficient samples (need ≥10 per config)'}

        mean_a = statistics.mean(config_a_latencies)
        mean_b = statistics.mean(config_b_latencies)

        t_stat, p_value = stats.ttest_ind(config_a_latencies, config_b_latencies)
        significant = p_value < alpha

        interpretation = (
            f"Config A {'faster' if mean_a < mean_b else 'slower'} by "
            f"{abs(mean_a - mean_b):.3f}s "
            f"({'significant' if significant else 'not significant'} at α={alpha})"
        )

        return {
            'mean_a': mean_a,
            'mean_b': mean_b,
            'difference': mean_b - mean_a,
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': significant,
            'interpretation': interpretation
        }

    @staticmethod
    def accuracy_confidence_interval(accuracy_list, confidence=0.95):
        """
        95% confidence interval for accuracy metric.

        Args:
            accuracy_list: List[float] (0.0-1.0) (≥30 samples)
            confidence: Confidence level (default 0.95)

        Returns:
            {
                'mean': float,
                'ci_lower': float,
                'ci_upper': float,
                'margin_of_error': float,
                'formatted': str  # e.g., "85% ± 3%"
            }
        """
        if len(accuracy_list) < 30:
            return {'error': 'Insufficient samples (need ≥30 for CI)'}

        mean = statistics.mean(accuracy_list)
        stdev = statistics.stdev(accuracy_list)
        n = len(accuracy_list)

        # t-distribution for CI (more conservative than normal)
        t_critical = stats.t.ppf((1 + confidence) / 2, n - 1)
        margin = t_critical * (stdev / np.sqrt(n))

        return {
            'mean': mean,
            'ci_lower': mean - margin,
            'ci_upper': mean + margin,
            'margin_of_error': margin,
            'formatted': f"{mean*100:.1f}% ± {margin*100:.1f}%"
        }

    @staticmethod
    def minimum_sample_sizes():
        """Return minimum sample sizes for statistical tests."""
        return {
            'latency_comparison': 10,  # Per config per test case
            'accuracy_ci': 30,         # Per config total
            'precision_validation': 5   # Benchmark queries minimum
        }
```

**Update ComparisonAnalyzer** (Section 2.5):

Add after line 750:

```python
class ComparisonAnalyzer:
    def __init__(self):
        self.stats = StatisticalAnalyzer()

    def compare_by_config(self, results):
        """Aggregate metrics per configuration WITH statistical tests."""
        configs = {}  # ... existing code ...

        # NEW: Statistical comparisons
        config_names = list(configs.keys())
        for i, config_a in enumerate(config_names):
            for config_b in config_names[i+1:]:
                # Latency comparison
                latencies_a = configs[config_a]['latency_samples']
                latencies_b = configs[config_b]['latency_samples']

                stat_result = self.stats.compare_latencies(latencies_a, latencies_b)

                # Store in comparison metadata
                key = f"{config_a}_vs_{config_b}"
                configs[key] = {
                    'type': 'statistical_comparison',
                    'metric': 'latency',
                    'result': stat_result
                }

        # NEW: Accuracy confidence intervals
        for config_name, config_data in configs.items():
            if isinstance(config_data, dict) and 'accuracy_samples' in config_data:
                ci = self.stats.accuracy_confidence_interval(
                    config_data['accuracy_samples']
                )
                config_data['accuracy_ci'] = ci

        return configs
```

**Update Main Plan**:

Replace Section 6.2 (lines 1053-1061):

```markdown
### 6.2 Statistical Significance

**Implementation**: `poc-api-first/tests/evaluators/statistical_analyzer.py`

**Minimum Sample Sizes**:
- Latency comparison: n≥10 per config per test case (two-sample t-test)
- Accuracy CI: n≥30 per config total (95% confidence interval)
- Precision validation: n≥5 benchmark queries (manual review)

**For latency comparisons**:
```python
# Example: Compare UMLS+PubTator vs Full Hybrid
stat_result = StatisticalAnalyzer.compare_latencies(
    config_a_latencies=[1.2, 1.3, 1.1, ...],  # 10+ samples
    config_b_latencies=[1.5, 1.6, 1.4, ...],  # 10+ samples
    alpha=0.05
)
# Returns: {
#   'mean_a': 1.2, 'mean_b': 1.5,
#   'p_value': 0.003, 'significant': True,
#   'interpretation': "Config A faster by 0.3s (significant at α=0.05)"
# }
```

**For accuracy comparisons**:
```python
# Example: Accuracy CI for semantic classification
ci = StatisticalAnalyzer.accuracy_confidence_interval(
    accuracy_list=[0.85, 0.87, 0.83, ...],  # 30+ samples
    confidence=0.95
)
# Returns: {
#   'formatted': "85% ± 3%",
#   'ci_lower': 0.82, 'ci_upper': 0.88
# }
```

**Integration**:
- ComparisonAnalyzer calls statistical methods automatically
- Report includes p-values, CIs in comparison tables
- Winner determination requires statistical significance (p<0.05)

**Report Format**:
| Metric | Config A | Config B | Difference | p-value | Significant? |
|--------|----------|----------|------------|---------|--------------|
| Latency | 1.2s ± 0.1 | 1.5s ± 0.2 | 0.3s | 0.003 | ✅ Yes |
| Accuracy | 85% ± 3% | 90% ± 2% | 5% | 0.012 | ✅ Yes |
```

**Effort**: 1 hour (implement + integrate)

---

## ISSUE 7: LATENCY TARGETS AGGRESSIVE

**Source**: Sections 4.1 (line 914), Phase 3 (line 874)
**Problem**: <2s p95 warm may be aggressive without robust caching/batching
**Risk**: Unrealistic targets → all configs fail → invalid comparison
**Severity**: HIGH (affects realism)

### Root Cause
Target set without validation against Phase 3 infrastructure and API latencies

### Solution: Calibrate Targets, Add Tiered Thresholds

**Affected Sections**:
- Section 4.1 (Success Criteria)
- Section 3, Phase 3 (Performance Benchmarking)

**Plan Updates**:

**1. Update Section 4.1** (replace line 914):

```markdown
### 4.1 Per-Configuration Thresholds

**Pass Criteria** (must meet ALL):
- ✅ Semantic accuracy: ≥90% for known terms
- ✅ Latency (warm, p95): **See tiered targets below**
- ✅ Precision@10: ≥80% (manual validation) - STAGED
- ✅ No critical errors

**Latency Targets (Tiered by Phase)**:

**Phase 1 (Initial - No Caching)**:
- p95 <5s acceptable (baseline measurement)
- p50 <3s target

**Phase 2 (Redis Cache Enabled)**:
- p95 <3s acceptable
- p50 <2s target

**Phase 3 (Production-Ready - Optimized)**:
- p95 <2s **GOAL** (requires validation in Phase 2)
- p50 <1.5s target

**Calibration Protocol**:
1. Run Phase 1 tests → establish baseline p95/p50
2. Enable caching (Phase 2) → measure improvement
3. If Phase 2 p95 <2.5s → Phase 3 target of <2s is realistic
4. If Phase 2 p95 >3s → adjust Phase 3 target OR optimize infra

**Rationale**: Targets must align with infrastructure capability
- External API latencies (UMLS ~500ms, PubTator ~300ms, PubMed ~200ms)
- Multi-term queries: 3 terms × 500ms = 1.5s minimum (no parallelization)
- Cache hit rate 80% → 20% cold calls still add latency
```

**2. Update Section 3, Phase 3** (after line 878):

```markdown
**Latency Target Calibration**:

**Step 1: Measure Baseline (Cold)**
- Run test suite 1× per config, cache cleared
- Record p50/p95/p99 cold latencies
- **Expected**: p95 ~4-6s (multiple API calls, no cache)

**Step 2: Measure with Cache (Warm)**
- Enable Redis cache, run warm-up protocol (Section 6.1.1)
- Run test suite 10× per config
- Record p50/p95/p99 warm latencies
- **Expected**: p95 ~2-3s (80% cache hits)

**Step 3: Validate Target Feasibility**
- If p95 warm <2.5s → **<2s target is realistic** (proceed to Phase 3)
- If p95 warm >3s → **Adjust target OR investigate**:
  - Check cache hit rate (should be >80%)
  - Profile API call parallelization
  - Consider batching UMLS requests

**Step 4: Set Production Target**
- Use Phase 2 p95 - 0.5s as Phase 3 goal
- Example: Phase 2 p95 = 2.3s → Phase 3 goal = 1.8s
```

**Effort**: 15 minutes (documentation update)

---

## ISSUE 8: PRECISION@10 STAGING

**Source**: Sections 4.1 (line 916), 5.2 (line 986)
**Problem**: ≥80% is blocking but manual review may be delayed
**Risk**: Tests blocked waiting for manual labels
**Severity**: HIGH (affects timeline)

### Root Cause
Precision@10 defined as hard requirement before manual labels available

### Solution: Stage Precision@10 (Informative → Gating)

**Affected Sections**:
- Section 4.1 (Success Criteria)
- Section 5.2 (Manual Validation)

**Plan Updates**:

**1. Update Section 4.1** (after line 916):

```markdown
**Precision@10 Staging Protocol**:

**Stage 1: Automated Testing (Phase 1, Week 1)**
- Status: **INFORMATIONAL ONLY**
- Metric: Heuristic placeholder (token inclusion)
- Use: Identify obvious failures (0 results, errors)
- NOT GATING: Proceed to Phase 2 regardless

**Stage 2: Manual Validation (Phase 2, Week 2)**
- Status: **MEASUREMENT**
- Metric: Manual labels from neuroscientist (James)
- Use: Calculate actual Precision@10 per config
- NOT GATING: Accept any score, document for analysis

**Stage 3: Deployment Decision (Phase 4, Week 3)**
- Status: **GATING**
- Metric: Precision@10 from manual labels
- Threshold: ≥80% required for production deployment
- Gating: If <80%, config NOT recommended for deployment

**Rationale**:
- Phase 1: Fast automated testing, no manual bottleneck
- Phase 2: Collect ground truth, measure actual performance
- Phase 3: Use validated scores for deployment decision

**Timeline Implications**:
- Week 1: Automated tests complete (Stage 1)
- Week 2: Manual review scheduled (Stage 2)
- Week 3: Deployment decision with validated scores (Stage 3)
```

**2. Update Section 5.2** (after line 998):

```markdown
### 5.2 Neuroscientist Review Protocol

**Review Timing**: **Week 2, Day 3** (after automated tests complete)

**Scope**: 5 benchmark queries × 4 configurations = 20 result sets

**Pre-Review Preparation** (Week 2, Day 1-2):
1. Extract top 10 results from Phase 1 automated tests
2. Format for review (PDF or web form)
3. Schedule 2-hour review session with James
4. **Do NOT block Phase 1 completion on review scheduling**

**Review Process**:
[Existing review form content]

**Stage 2 Deliverable**:
- Precision@10 scores per configuration (MEASURED, not gating yet)
- Qualitative feedback for error analysis
- Documented in `results/manual_review_<timestamp>.json`

**Stage 3 Usage**:
- Precision@10 scores feed into deployment decision (Week 3)
- Threshold ≥80% applied ONLY for final recommendation
```

**Effort**: 15 minutes (documentation update)

---

## ISSUE 9: GROUND TRUTH SUBJECTIVITY

**Source**: Section 9 (Risks)
**Problem**: Missing inter-rater agreement (Cohen's kappa), dual-review protocol, tie-break rules
**Risk**: Unreliable ground truth → invalid validation
**Severity**: HIGH (affects validity)

### Root Cause
Single-reviewer manual validation without reliability checks

### Solution: Add Dual-Review Protocol with Inter-Rater Agreement

**Affected Sections**:
- NEW: Section 5.2.1 (Dual-Review Protocol)
- Section 5.1 (Gold Standard Creation)

**Plan Updates**:

**1. Add NEW Section 5.2.1** (after Section 5.2, line 998):

```markdown
### 5.2.1 Dual-Review Protocol for Ground Truth Reliability

**Problem**: Single reviewer → subjective judgments, no reliability check

**Solution**: Dual-review with inter-rater agreement (Cohen's kappa)

**Protocol**:

**Step 1: Initial Review (Reviewer 1)**
- Neuroscientist A (James): Review all 200 papers (20 result sets)
- Score each paper 0-5 (irrelevant → highly relevant)
- Time: ~2 hours

**Step 2: Sample Dual-Review (Reviewer 2)**
- Neuroscientist B (independent): Review 20% random sample (40 papers)
- Same 0-5 scale, blinded to Reviewer 1 scores
- Time: ~30 minutes

**Step 3: Inter-Rater Agreement Analysis**
```python
from sklearn.metrics import cohen_kappa_score

# Binary classification: relevant (≥3) vs irrelevant (<3)
reviewer_1_binary = [1 if score >= 3 else 0 for score in reviewer_1_scores]
reviewer_2_binary = [1 if score >= 3 else 0 for score in reviewer_2_scores]

kappa = cohen_kappa_score(reviewer_1_binary, reviewer_2_binary)

# Interpretation:
# kappa > 0.8: Excellent agreement → proceed
# kappa 0.6-0.8: Good agreement → acceptable
# kappa < 0.6: Poor agreement → reconcile disagreements
```

**Step 4: Disagreement Reconciliation**
- If kappa < 0.6: Schedule joint review session
- Review disagreements (|score_1 - score_2| ≥ 2)
- Discuss until consensus reached
- Document rationale for tie-breaks

**Tie-Break Rules** (if consensus impossible):
1. Defer to domain expert with stronger neuroscience background
2. If equal expertise: Mark as "uncertain" (exclude from precision calculation)
3. If >10% uncertain: Expand review to Reviewer 3

**Deliverable**:
- Inter-rater kappa score (target: >0.6)
- Reconciled labels for full dataset
- Documented disagreements and resolutions

**Timeline Impact**: +2 hours (sample dual-review + reconciliation)
```

**2. Update Section 5.1** (add after line 980):

```markdown
**Ground Truth Validation**:

**Quality Assurance**:
- Dual-review 20% sample (Section 5.2.1)
- Inter-rater agreement (Cohen's kappa >0.6)
- Disagreement reconciliation protocol

**Documentation**:
- Store in `tests/fixtures/gold_standard.json`
- Include metadata:
  ```json
  {
    "metadata": {
      "creation_date": "2025-12-XX",
      "reviewers": ["James (Reviewer 1)", "Reviewer 2 Name"],
      "inter_rater_kappa": 0.72,
      "disagreements_reconciled": 8,
      "uncertain_labels": 2
    },
    "BM-001": { ... }
  }
  ```
```

**Effort**: 30 minutes (protocol documentation)

---

## ISSUE 10: ENVIRONMENT/PORTABILITY

**Source**: Section 9 (Risks), Appendix C (line 1400)
**Problem**: Missing .env for UMLS key, config loader for CI/local runs
**Risk**: Setup failures, broken CI, non-reproducible tests
**Severity**: HIGH (blocks execution)

### Root Cause
No documented environment setup, secrets in code, paths hardcoded

### Solution: Add Environment Setup Documentation + Config Loader

**Affected Sections**:
- NEW: Section 1.1 (Environment Setup)
- Section 9 (Risks)
- NEW: Implementation files

**Plan Updates**:

**1. Add NEW Section 1.1** (before Section 1, as introduction):

```markdown
## 1.1 ENVIRONMENT SETUP

**Prerequisites**:
- Python 3.10+
- Redis (for caching)
- UMLS API key (from NIH UTS)

**Setup Steps**:

**Step 1: Clone Repository**
```bash
cd /path/to/NeuroDB-2
```

**Step 2: Install Dependencies**
```bash
pip install -r poc-api-first/requirements.txt
# scipy>=1.11.0 (for stats)
# redis>=5.0.0 (for cache)
# requests>=2.31.0 (for APIs)
```

**Step 3: Configure Environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

**.env.example** (create in project root):
```bash
# UMLS API Key (required)
# Get from: https://uts.nlm.nih.gov/uts/signup-login
UMLS_API_KEY=your_umls_api_key_here

# Redis Configuration (optional, defaults shown)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Test Configuration
TEST_PARALLEL=true
TEST_WORKERS=5
TEST_OUTPUT_DIR=poc-api-first/results

# API Rate Limits (adjust if different)
UMLS_RATE_LIMIT_PER_SEC=20
UMLS_RATE_LIMIT_PER_HOUR=5000
PUBTATOR_RATE_LIMIT_PER_SEC=10
PUBTATOR_RATE_LIMIT_PER_HOUR=1000
```

**Step 4: Verify Setup**
```bash
python poc-api-first/tests/test_runner.py --verify-setup
# Checks: UMLS key, Redis connection, NeuroDB-2 data
```

**Step 5: Run Tests**
```bash
# Dry run (mock APIs)
python poc-api-first/tests/test_runner.py --dry-run

# Full test suite (live APIs)
python poc-api-first/tests/test_runner.py --parallel --output results/run_$(date +%s).json
```

**CI/CD Configuration** (.github/workflows/test.yml):
```yaml
name: Semantic Pipeline Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r poc-api-first/requirements.txt
      - run: |
          # Use mock APIs in CI (no secrets needed)
          python poc-api-first/tests/test_runner.py --dry-run --output results/ci_run.json
      - uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: poc-api-first/results/
```
```

**2. Create Config Loader** (NEW file):

```python
# poc-api-first/config/loader.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / '.env')

class Config:
    """Centralized configuration from environment variables."""

    # API Keys
    UMLS_API_KEY = os.getenv('UMLS_API_KEY')

    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))

    # Test Configuration
    TEST_PARALLEL = os.getenv('TEST_PARALLEL', 'true').lower() == 'true'
    TEST_WORKERS = int(os.getenv('TEST_WORKERS', 5))
    TEST_OUTPUT_DIR = os.getenv('TEST_OUTPUT_DIR', 'poc-api-first/results')

    # API Rate Limits
    UMLS_RATE_PER_SEC = int(os.getenv('UMLS_RATE_LIMIT_PER_SEC', 20))
    UMLS_RATE_PER_HOUR = int(os.getenv('UMLS_RATE_LIMIT_PER_HOUR', 5000))
    PUBTATOR_RATE_PER_SEC = int(os.getenv('PUBTATOR_RATE_LIMIT_PER_SEC', 10))
    PUBTATOR_RATE_PER_HOUR = int(os.getenv('PUBTATOR_RATE_LIMIT_PER_HOUR', 1000))

    # Data Paths (repo-relative)
    NEURODB_DATA_PATH = PROJECT_ROOT / 'data' / 'neuro_terms.json'

    @classmethod
    def verify(cls):
        """Verify required configuration."""
        errors = []

        if not cls.UMLS_API_KEY:
            errors.append("UMLS_API_KEY not set in .env")

        if not cls.NEURODB_DATA_PATH.exists():
            errors.append(f"NeuroDB-2 data not found: {cls.NEURODB_DATA_PATH}")

        if errors:
            raise EnvironmentError("\n".join(errors))

        return True
```

**3. Update test_runner.py** to use Config:

```python
# poc-api-first/tests/test_runner.py
from config.loader import Config

class SemanticPipelineTestRunner:
    def __init__(self, test_suite_path: str):
        # Verify environment before proceeding
        Config.verify()

        # Use config values
        self.parallel = Config.TEST_PARALLEL
        self.max_workers = Config.TEST_WORKERS
        # ...
```

**4. Update Section 9** (add after line 1261):

```markdown
### Risk 6: Environment Setup Failures
**Impact**: Tests fail due to missing credentials, paths
**Mitigation**:
- .env.example template provided (Section 1.1)
- Config loader validates setup before tests run
- CI uses mock APIs (no secrets needed)
- Verify-setup command checks all prerequisites
```

**Effort**: 1 hour (create files + documentation)

---

## PRIORITY & SEQUENCING

**Phase 1: Execution Blockers** (Must fix before running tests):
1. ✅ Issue 1: Rate limiting (1 hour) - CRITICAL for execution
2. ✅ Issue 10: Environment setup (1 hour) - CRITICAL for execution
3. ✅ Issue 7: Latency target calibration (15 min) - Define realistic targets

**Phase 2: Fairness & Validity** (Must fix before comparison):
4. ✅ Issue 2: FullHybrid arbitration (30 min) - Affects accuracy
5. ✅ Issue 3: Result count non-gating (15 min) - Affects fairness
6. ✅ Issue 5: Cache control (30 min) - Affects fairness
7. ✅ Issue 6: Statistical methods (1 hour) - Required for valid comparison

**Phase 3: Quality Improvements** (Before manual validation):
8. ✅ Issue 4: Heuristic relevance warning (30 min) - Documentation
9. ✅ Issue 8: Precision@10 staging (15 min) - Timeline clarity
10. ✅ Issue 9: Dual-review protocol (30 min) - Reliability

**Total Sequential Effort**: ~7.5 hours
**Parallelizable**: Issues 1-3 can be done concurrently (3 developers → 1 hour)

---

## IMPLEMENTATION CHECKLIST

**Phase 1** (2 hours):
- [ ] Implement rate limiter (`utils/rate_limiter.py`)
- [ ] Update UMLS/PubTator clients with rate limiting
- [ ] Create `.env.example` and config loader
- [ ] Update test_runner.py to use Config
- [ ] Document environment setup (Section 1.1)
- [ ] Update latency targets (Section 4.1, Phase 3)

**Phase 2** (3 hours):
- [ ] Refactor FullHybrid config with arbitration (Section 2.2)
- [ ] Update QuantitativeMetrics to make result count non-gating (Section 2.4)
- [ ] Document cache control protocol (Section 6.1.1)
- [ ] Implement StatisticalAnalyzer (`evaluators/statistical_analyzer.py`)
- [ ] Integrate statistics into ComparisonAnalyzer (Section 2.5)
- [ ] Update Section 6.2 with implementation details

**Phase 3** (2.5 hours):
- [ ] Add heuristic relevance warnings (Section 2.4)
- [ ] Document Precision@10 staging (Section 4.1)
- [ ] Add dual-review protocol (Section 5.2.1)
- [ ] Update gold standard schema with metadata (Section 5.1)
- [ ] Update Risk 9 with ground truth protocols

**Validation**:
- [ ] Test rate limiter with burst requests
- [ ] Verify FullHybrid arbitration logic with test cases
- [ ] Run statistical tests with sample data (verify p-values, CIs)
- [ ] Verify Config.verify() catches missing env vars
- [ ] Dry-run test suite with mock APIs

---

## UNRESOLVED QUESTIONS

1. **Inter-rater agreement threshold**: Is kappa >0.6 sufficient, or require >0.7?
   - Recommendation: Start with >0.6 (good agreement), adjust if issues

2. **Reviewer 2 availability**: Who is Reviewer 2 (independent neuroscientist)?
   - Action: Identify before Phase 2, Week 2

3. **Statistical power**: Are 10 samples per config sufficient for latency t-test?
   - Recommendation: Yes for exploratory, but 30+ preferred for publication

4. **Cache implementation**: Redis vs in-memory cache?
   - Recommendation: Redis (persistent, configurable, CI-friendly)

5. **CI runtime**: Will dry-run (mock APIs) cover all test cases adequately?
   - Recommendation: Yes for structure validation, but weekly live API tests needed

---

## SUMMARY

**Issues Addressed**: 10 HIGH priority
**Total Effort**: ~7.5 hours
**Critical Path**: Issues 1, 10 (execution blockers)
**Validation Required**: Rate limiter, statistical tests, config loader
**Timeline Impact**: None (all fits within Week 1 framework setup)

**Next Steps**:
1. Review this plan with technical lead
2. Assign issues to developers (parallelizable)
3. Implement Phase 1 (execution blockers) first
4. Validate with dry-run before Phase 2
5. Update main plan document with all changes
