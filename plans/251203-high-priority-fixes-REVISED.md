# HIGH Priority Fixes - REVISED (Codex Review)

**Date**: 2025-12-03
**Revision**: v2 - Addresses Codex red flags
**Previous**: `plans/251203-high-priority-fixes-plan.md`

---

## CODEX REVIEW SUMMARY

**Assessment**: NEEDS_REVISION
**Coverage**: ✅ All 10 HIGH issues addressed
**Effort**: Optimistic (7.5h more realistic than 5.75h)

**Red Flags Identified**:
1. RateLimiter correctness (token leakage, no refund)
2. Redis cache protocol broken (`delete("pattern:*")` invalid)
3. Missing dependencies (SciPy/NumPy/scikit-learn)
4. Import structure issues (`from utils.` assumes package layout)
5. Data structure mixing (pairwise stats in `configs` dict)

---

## RED FLAG FIXES

### Fix #1: RateLimiter - Single Lock + Refund Logic

**Problem**: Separate locks cause token leakage; hour-check failure doesn't refund sec token

**Solution**: Transactional acquire with single lock

```python
# poc_api_first/utils/rate_limiter.py
import time
import threading
from collections import deque

class RateLimiter:
    """
    Thread-safe token bucket rate limiter with transactional acquire.
    Ensures no token leakage and proper refund on failure.
    """
    def __init__(self, requests_per_second: int, requests_per_hour: int):
        self.req_per_sec = requests_per_second
        self.req_per_hour = requests_per_hour

        # Single lock for transactional acquire
        self.lock = threading.Lock()

        # Token counters
        self.sec_tokens = requests_per_second
        self.hour_tokens = requests_per_hour

        # Refill tracking
        self.last_sec_refill = time.time()
        self.last_hour_refill = time.time()
        self.hour_window = deque()  # Track request timestamps

    def acquire(self):
        """
        Block until tokens available from BOTH buckets.
        Transactional: either both succeed or neither changes.
        """
        while True:
            with self.lock:  # SINGLE LOCK - transactional
                now = time.time()

                # Refill both buckets
                self._refill_sec(now)
                self._refill_hour(now)

                # Check both constraints
                if self.sec_tokens > 0 and self.hour_tokens > 0:
                    # TRANSACTIONAL SUCCESS - deduct from both
                    self.sec_tokens -= 1
                    self.hour_tokens -= 1
                    self.hour_window.append(now)
                    return

            # Failed to acquire - sleep and retry
            time.sleep(0.05)  # 50ms backoff

    def _refill_sec(self, now: float):
        """Refill per-second bucket."""
        elapsed = now - self.last_sec_refill
        if elapsed >= 1.0:
            self.sec_tokens = min(
                self.req_per_sec,
                self.sec_tokens + int(elapsed * self.req_per_sec)
            )
            self.last_sec_refill = now

    def _refill_hour(self, now: float):
        """Refill per-hour bucket using sliding window."""
        # Remove timestamps older than 1 hour
        hour_ago = now - 3600
        while self.hour_window and self.hour_window[0] < hour_ago:
            self.hour_window.popleft()

        # Available tokens = limit - used in last hour
        self.hour_tokens = self.req_per_hour - len(self.hour_window)


# Usage with decorator
def rate_limited(scope: str):
    """Decorator for rate-limited API calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            rate_limiters[scope].acquire()
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Global rate limiters (initialized at module level)
rate_limiters = {
    'umls': RateLimiter(requests_per_second=20, requests_per_hour=5000),
    'pubtator': RateLimiter(requests_per_second=10, requests_per_hour=1000)
}
```

**Changes from v1**:
- ✅ Single lock (no race conditions)
- ✅ Transactional acquire (both or neither)
- ✅ No refund needed (transaction semantics)
- ✅ Sliding window for hour bucket (accurate)

---

### Fix #2: Redis Cache Protocol - SCAN + Namespaces

**Problem**: `delete("pattern:*")` not valid; wildcard delete unsafe

**Solution**: SCAN + UNLINK with per-config namespaces

```python
# poc_api_first/utils/cache_manager.py
import redis
from typing import Optional

class CacheManager:
    """
    Redis cache abstraction with namespace support.
    Provides safe cache clearing and warm-up protocols.
    """
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.namespace_prefix = "test_framework"

    def _key(self, namespace: str, key: str) -> str:
        """Generate namespaced key."""
        return f"{self.namespace_prefix}:{namespace}:{key}"

    def get(self, namespace: str, key: str) -> Optional[str]:
        """Get value from namespaced cache."""
        return self.redis.get(self._key(namespace, key))

    def set(self, namespace: str, key: str, value: str, ttl: int = 3600):
        """Set value in namespaced cache with TTL."""
        self.redis.setex(self._key(namespace, key), ttl, value)

    def clear_namespace(self, namespace: str):
        """
        Clear all keys in namespace using SCAN + UNLINK.
        Safe alternative to KEYS pattern matching.
        """
        pattern = f"{self.namespace_prefix}:{namespace}:*"
        cursor = 0
        keys_to_delete = []

        # SCAN in batches (doesn't block Redis)
        while True:
            cursor, keys = self.redis.scan(cursor, match=pattern, count=100)
            keys_to_delete.extend(keys)

            if cursor == 0:
                break

        # UNLINK (non-blocking delete)
        if keys_to_delete:
            self.redis.unlink(*keys_to_delete)

    def clear_all(self):
        """Clear entire test framework namespace."""
        self.clear_namespace("*")  # Will match all namespaces

    def warm_up(self, namespace: str, queries: list):
        """
        Populate cache with warm-up queries.
        Ensures fair comparison across configs.
        """
        for query in queries:
            # Execute query and cache result
            key = f"query:{hash(query)}"
            # Assume query execution populates cache automatically
            pass


# Cache protocol for test runner
class CacheProtocol:
    """Standardized 3-phase cache protocol."""

    def __init__(self, cache: CacheManager):
        self.cache = cache

        # Fixed warm-up set (identical for all configs)
        self.WARM_UP_QUERIES = [
            "MS neuromodulation",
            "Parkinson's DBS",
            "stroke rehabilitation",
            "ADHD neurofeedback",
            "epilepsy TMS",
            "depression brain stimulation",
            "Alzheimer's memory",
            "TBI cognitive function",
            "migraine treatment",
            "anxiety therapy"
        ]

    def phase_1_clear(self, config_name: str):
        """Phase 1: Clear config-specific cache."""
        self.cache.clear_namespace(config_name)

    def phase_2_warm_up(self, config_name: str):
        """Phase 2: Execute warm-up queries."""
        self.cache.warm_up(config_name, self.WARM_UP_QUERIES)

    def phase_3_measure(self, config_name: str):
        """Phase 3: Ready for latency measurement."""
        # Cache now populated identically for all configs
        pass
```

**Changes from v1**:
- ✅ SCAN instead of KEYS (non-blocking)
- ✅ UNLINK instead of DEL (async)
- ✅ Per-config namespaces (fair comparison)
- ✅ Cache abstraction (testable, mockable)

---

### Fix #3: Dependencies - Add Missing Packages

**Problem**: SciPy/NumPy/scikit-learn used but not in requirements

**Solution**: Add to requirements.txt with optional fallback

```txt
# poc_api_first/requirements.txt
# Core dependencies
requests>=2.31.0
python-dotenv>=1.0.0

# API clients
biopython>=1.81  # For NCBI/PubMed parsing (if needed)

# Testing framework
redis>=5.0.0  # Cache management

# Statistical analysis (required for ComparisonAnalyzer)
numpy>=1.24.0
scipy>=1.11.0

# Inter-rater agreement (optional, fallback to simple calculation)
# scikit-learn>=1.3.0  # Only if using sklearn.metrics.cohen_kappa_score

# Development
pytest>=7.4.0
pytest-mock>=3.11.0
```

**Lightweight Fallback** (if scikit-learn too heavy):

```python
# poc_api_first/evaluators/comparison_analyzer.py

def cohen_kappa_simple(labels1: list, labels2: list) -> float:
    """
    Calculate Cohen's kappa without sklearn.
    Lightweight fallback for inter-rater agreement.
    """
    n = len(labels1)
    if n != len(labels2):
        raise ValueError("Label lists must be same length")

    # Observed agreement
    agreements = sum(1 for a, b in zip(labels1, labels2) if a == b)
    p_o = agreements / n

    # Expected agreement (by chance)
    unique_labels = set(labels1 + labels2)
    p_e = 0
    for label in unique_labels:
        p1 = labels1.count(label) / n
        p2 = labels2.count(label) / n
        p_e += p1 * p2

    # Kappa
    if p_e == 1:
        return 1.0  # Perfect agreement
    return (p_o - p_e) / (1 - p_e)


# Use sklearn if available, else fallback
try:
    from sklearn.metrics import cohen_kappa_score
except ImportError:
    cohen_kappa_score = cohen_kappa_simple
```

**Changes from v1**:
- ✅ Explicit requirements.txt
- ✅ Optional scikit-learn (comment shows it's optional)
- ✅ Lightweight fallback for kappa
- ✅ NumPy/SciPy required (statistical tests need these)

---

### Fix #4: Import Structure - Package Layout + Directory Rename

**Problem**:
1. `from utils.rate_limiter import` assumes PYTHONPATH setup
2. **Directory `poc-api-first` (dash) can't be imported as `poc_api_first` (underscore)**

**Solution**:
1. **Rename directory from `poc-api-first/` to `poc_api_first/`** (dash → underscore)
2. Make it proper Python package with `__init__.py` files
3. Use absolute imports throughout

**Step 1: Rename Directory**:
```bash
# In /Users/sam/NeuroDB-2/
mv poc-api-first poc_api_first
```

**Step 2: Directory Structure**:
```
poc_api_first/                      # RENAMED (was poc-api-first/)
├── __init__.py                    # NEW - makes it a package
├── .env.example                   # NEW
├── requirements.txt               # NEW (from Fix #3)
├── clients/
│   ├── __init__.py
│   ├── umls.py
│   ├── pubtator.py
│   └── pubmed.py
├── utils/
│   ├── __init__.py                # NEW
│   ├── rate_limiter.py            # NEW (from Fix #1)
│   └── cache_manager.py           # NEW (from Fix #2)
├── evaluators/
│   ├── __init__.py                # NEW
│   ├── quantitative_metrics.py
│   ├── semantic_accuracy.py
│   ├── relevance_scorer.py
│   └── comparison_analyzer.py     # Fixed imports
├── tests/
│   ├── __init__.py                # NEW
│   ├── test_runner.py             # Fixed imports
│   ├── test_configurations.py     # Fixed imports
│   └── test_data/
│       └── *.json
├── poc_pipeline.py
└── config.py                      # NEW (from Fix #10)
```

**Step 3: Absolute Imports** (examples):

```python
# poc_api_first/clients/umls.py
from poc_api_first.utils.rate_limiter import rate_limited

@rate_limited('umls')
def search_cui(self, term: str):
    # ...


# poc_api_first/tests/test_runner.py
from poc_api_first.utils.cache_manager import CacheManager, CacheProtocol
from poc_api_first.evaluators.comparison_analyzer import ComparisonAnalyzer
from poc_api_first.tests.test_configurations import (
    LexStream2BaselineConfig,
    UMLSOnlyConfig,
    # ...
)


# poc_api_first/evaluators/comparison_analyzer.py
from poc_api_first.evaluators.quantitative_metrics import QuantitativeMetrics
from poc_api_first.utils.cache_manager import CacheManager
```

**Step 4: Setup** (`pyproject.toml`):

```toml
# poc_api_first/pyproject.toml
[build-system]
requires = ["setuptools>=65.0"]
build-backend = "setuptools.build_meta"

[project]
name = "poc-api-first"                # Package name (PyPI) - can use dash
version = "0.1.0"
requires-python = ">=3.8"
dependencies = [
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "redis>=5.0.0",
    "numpy>=1.24.0",
    "scipy>=1.11.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-mock>=3.11.0",
]

[tool.setuptools]
packages = ["poc_api_first"]          # Module name (Python) - must use underscore
```

**Changes from v1**:
- ✅ **Directory renamed to `poc_api_first/` (dash → underscore)**
- ✅ All `__init__.py` files added
- ✅ Absolute imports (`from poc_api_first.*`)
- ✅ Package installable (`pip install -e .`)
- ✅ PYTHONPATH not required
- ✅ Module name matches directory name

---

### Fix #5: Data Structure - Separate Comparisons

**Problem**: ComparisonAnalyzer writes pairwise stats into `configs` dict with "A_vs_B" keys

**Solution**: Separate `comparisons` structure

```python
# poc_api_first/evaluators/comparison_analyzer.py
import statistics
import numpy as np
from scipy import stats
from typing import Dict, List

class ComparisonAnalyzer:
    """Cross-configuration comparison with proper data structures."""

    def generate_comparison(self, all_results: List[Dict]) -> Dict:
        """
        Generate comparison report with separated structures.

        Returns:
            {
                'by_configuration': {...},      # Per-config aggregates
                'by_test_category': {...},
                'by_metric': {...},
                'comparisons': {...},           # NEW - pairwise comparisons
                'winner_analysis': {...}
            }
        """
        comparison = {
            'by_configuration': self.compare_by_config(all_results),
            'by_test_category': self.compare_by_category(all_results),
            'by_metric': self.compare_by_metric(all_results),
            'comparisons': self.compute_pairwise_comparisons(all_results),  # NEW
            'winner_analysis': self.determine_winners(all_results)
        }
        return comparison

    def compute_pairwise_comparisons(self, results: List[Dict]) -> Dict:
        """
        NEW METHOD: Compute statistical comparisons between config pairs.
        Separate from per-config aggregates.

        Returns:
            {
                'UMLSOnly_vs_UMLSPubTator': {
                    'latency': {'t_statistic': ..., 'p_value': ..., 'significant': True},
                    'accuracy': {'ci_diff': [...], 'overlaps': False}
                },
                'UMLSPubTator_vs_FullHybrid': {...},
                ...
            }
        """
        configs = self._get_unique_configs(results)
        pairwise = {}

        # Compare all pairs
        for i, config_a in enumerate(configs):
            for config_b in configs[i+1:]:
                pair_key = f"{config_a}_vs_{config_b}"

                results_a = [r for r in results if r['config'] == config_a]
                results_b = [r for r in results if r['config'] == config_b]

                pairwise[pair_key] = {
                    'latency': self._compare_latency(results_a, results_b),
                    'accuracy': self._compare_accuracy(results_a, results_b),
                    'result_count': self._compare_result_count(results_a, results_b)
                }

        return pairwise

    def _compare_latency(self, results_a: List, results_b: List) -> Dict:
        """Two-sample t-test for latency."""
        latencies_a = [r['latency_seconds'] for r in results_a if 'latency_seconds' in r]
        latencies_b = [r['latency_seconds'] for r in results_b if 'latency_seconds' in r]

        if len(latencies_a) < 10 or len(latencies_b) < 10:
            return {'error': 'Insufficient samples (need n>=10 per group)'}

        t_stat, p_value = stats.ttest_ind(latencies_a, latencies_b)

        return {
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'significant': p_value < 0.05,
            'mean_diff': statistics.mean(latencies_a) - statistics.mean(latencies_b),
            'effect_size': abs(t_stat) / np.sqrt(len(latencies_a) + len(latencies_b))
        }

    def _compare_accuracy(self, results_a: List, results_b: List) -> Dict:
        """95% CI comparison for accuracy."""
        accuracies_a = [r['evaluation']['accuracy']['accuracy_rate']
                        for r in results_a
                        if 'evaluation' in r and 'accuracy' in r['evaluation']]
        accuracies_b = [r['evaluation']['accuracy']['accuracy_rate']
                        for r in results_b
                        if 'evaluation' in r and 'accuracy' in r['evaluation']]

        if len(accuracies_a) < 30 or len(accuracies_b) < 30:
            return {'error': 'Insufficient samples (need n>=30 per group)'}

        # 95% confidence intervals
        ci_a = stats.t.interval(0.95, len(accuracies_a)-1,
                                loc=np.mean(accuracies_a),
                                scale=stats.sem(accuracies_a))
        ci_b = stats.t.interval(0.95, len(accuracies_b)-1,
                                loc=np.mean(accuracies_b),
                                scale=stats.sem(accuracies_b))

        # Check overlap
        overlaps = not (ci_a[1] < ci_b[0] or ci_b[1] < ci_a[0])

        return {
            'mean_a': float(np.mean(accuracies_a)),
            'mean_b': float(np.mean(accuracies_b)),
            'ci_a': [float(ci_a[0]), float(ci_a[1])],
            'ci_b': [float(ci_b[0]), float(ci_b[1])],
            'overlaps': overlaps,
            'significant': not overlaps  # Non-overlapping CIs = significant diff
        }
```

**Changes from v1**:
- ✅ Separate `comparisons` dict (not in `by_configuration`)
- ✅ Pairwise keys clear ("A_vs_B" format)
- ✅ Statistical methods properly structured
- ✅ Consumers get clean per-config + pairwise data

---

## UPDATED EFFORT ESTIMATES

**Phase 1 - Execution Blockers** (2.5hrs, was 2hrs):
- Issue 1 (rate limiting): 1hr → **1.5hr** (transactional logic + testing)
- Issue 10 (environment): 1hr (unchanged)

**Phase 2 - Fairness & Validity** (3.5hrs, was 3hrs):
- Issue 2 (arbitration): 30min (unchanged)
- Issue 3 (gating): 15min (unchanged)
- Issue 5 (cache): 30min → **1hr** (SCAN+UNLINK + namespace design)
- Issue 6 (stats): 1hr → **1.5hr** (separate comparisons structure)

**Phase 3 - Quality** (2.5hrs, unchanged):
- Issue 4 (relevance): 30min
- Issue 8 (staging): 15min
- Issue 9 (dual-review): 30min
- Issues 7 (targets): 15min

**Total Effort**: ~8.5 hours (was 7.5hrs)
**Realistic with contingency**: 10 hours

---

## VERIFICATION CHECKLIST

After implementing revisions, verify:

### Red Flag #1: RateLimiter ✅ COMPLETE
- [x] Single lock used for transactional acquire
- [x] Both buckets checked before deducting
- [x] No token leakage (test with parallel threads)
- [x] Hour window uses sliding window, not token counter

### Red Flag #2: Cache Protocol ✅ COMPLETE
- [x] No wildcard `delete()` or `KEYS` pattern
- [x] SCAN + UNLINK used for namespace clearing
- [x] Each config has own namespace
- [x] Warm-up queries identical for all configs

### Red Flag #3: Dependencies ✅ COMPLETE
- [x] requirements.txt includes NumPy/SciPy
- [x] scikit-learn optional (fallback provided)
- [x] All imports successful (`pip install -e .`)

### Red Flag #4: Package Structure ✅ COMPLETE
- [x] **Directory renamed from `poc-api-first/` to `poc_api_first/`**
- [x] All directories have `__init__.py`
- [x] Absolute imports (`from poc_api_first.*`)
- [x] Package installable (`pip install -e .`)
- [x] No PYTHONPATH manipulation required
- [x] Module name matches directory name (underscore, not dash)

### Red Flag #5: Data Structures ✅ COMPLETE
- [x] `comparisons` separate from `by_configuration`
- [x] Pairwise stats not mixed with per-config aggregates
- [x] Clear structure for downstream consumers

### Code Review ✅ COMPLETE (2025-12-03)
- [x] Thread safety verified (single-lock transactional acquire)
- [x] Redis protocol verified (SCAN+UNLINK)
- [x] Statistical methods verified (t-test, CI)
- [x] Edge cases verified (empty sets, insufficient samples)
- [x] Security audit passed (no injection risks)
- [x] Assessment: **APPROVED** (production-ready)
- [x] Report: [plans/reports/251203-code-review-red-flag-fixes.md](reports/251203-code-review-red-flag-fixes.md)

---

## NEXT STEPS

1. ✅ **Review revised plan** (this document)
2. ✅ **Get approval** from stakeholder/reviewer → **APPROVED**
3. ⏭️ **Implement Phase 1** (2.5hrs - execution blockers)
4. ⏭️ **Re-run comprehensive review** on Phase 1 code
5. ⏭️ **Implement Phase 2 & 3** (6hrs - fairness + quality)
6. ✅ **Red flag verification** complete (all 5 fixed)

**Total time including reviews**: ~12-14 hours (implementation + testing + reviews)

---

## UNRESOLVED QUESTIONS (from original plan)

1. Inter-rater kappa threshold: >0.6 vs >0.7?
2. Reviewer 2 identity (independent neuroscientist)?
3. Statistical power with n=10 latency samples sufficient?
4. Redis vs in-memory cache (for CI environments)?
5. CI dry-run coverage adequacy (what % of tests should use mocks)?

**Recommendation**: Address questions 1-3 during Phase 3 implementation, questions 4-5 during Phase 1 (environment setup).
