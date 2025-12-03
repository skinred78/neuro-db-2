"""
Quantitative Metrics Evaluator

Evaluates automated quantitative metrics from test runner records:
- Result count (number of papers returned)
- Latency (query execution time)
- API call counts (UMLS, PubTator, PubMed)
"""

from typing import Dict, Any


class QuantitativeMetrics:
    """
    Evaluates quantitative metrics from test runner records.

    NOTE: `result` parameter is the runner's output record (not raw pipeline output).
    The runner embeds authoritative measurements like latency_seconds.
    """

    def __init__(self, target_range=(5, 20), latency_threshold=2.0):
        """
        Initialize metrics evaluator with thresholds.

        Args:
            target_range: Tuple of (min, max) acceptable result counts
            latency_threshold: Maximum acceptable latency in seconds
        """
        self.min_results, self.max_results = target_range
        self.latency_threshold = latency_threshold

    def evaluate(self, test_case: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate quantitative metrics for a single test result.

        Args:
            test_case: Test case definition with expected results
            result: Test runner output record with embedded metrics

        Returns:
            Dictionary with quantitative metric evaluations
        """
        metrics = {
            'result_count': result.get('result_count', 0),
            'in_target_range': self._check_result_range(result, test_case),
            'latency_seconds': result.get('latency_seconds', 0),  # From runner, not pipeline
            'latency_acceptable': self._check_latency(result),
            'api_calls': result.get('api_calls', {}),
            'total_api_calls': self._count_total_api_calls(result)
        }

        # Add pass/fail status
        metrics['passed'] = (
            metrics['in_target_range'] and
            metrics['latency_acceptable']
        )

        return metrics

    def _check_result_range(self, result: Dict[str, Any], test_case: Dict[str, Any]) -> bool:
        """
        Check if result count is in acceptable range.

        Uses test case-specific range if provided, otherwise uses default range.
        """
        result_count = result.get('result_count', 0)

        # Use test case-specific range if provided
        expected = test_case.get('expected_results', {})
        min_count = expected.get('min_count', self.min_results)
        max_count = expected.get('max_count', self.max_results)

        return min_count <= result_count <= max_count

    def _check_latency(self, result: Dict[str, Any]) -> bool:
        """
        Check if latency is within acceptable threshold.

        NOTE: Uses latency_seconds from runner (AUTHORITATIVE measurement).
        Pipeline's internal timing is NOT used.
        """
        latency = result.get('latency_seconds', float('inf'))
        return latency < self.latency_threshold

    def _count_total_api_calls(self, result: Dict[str, Any]) -> int:
        """
        Count total API calls made during query processing.

        Returns:
            Total number of API calls across all services
        """
        api_calls = result.get('api_calls', {})
        return sum(api_calls.values())

    def aggregate_metrics(self, results: list) -> Dict[str, Any]:
        """
        Aggregate metrics across multiple test results.

        Args:
            results: List of test results with evaluated metrics

        Returns:
            Aggregated statistics
        """
        if not results:
            return {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'pass_rate': 0.0
            }

        evaluations = [r.get('evaluation', {}).get('quantitative', {}) for r in results]
        evaluations = [e for e in evaluations if e]  # Filter empty

        if not evaluations:
            return {
                'total_tests': len(results),
                'passed': 0,
                'failed': len(results),
                'pass_rate': 0.0
            }

        passed = sum(1 for e in evaluations if e.get('passed', False))
        failed = len(evaluations) - passed

        # Aggregate result counts
        result_counts = [e['result_count'] for e in evaluations]
        avg_results = sum(result_counts) / len(result_counts) if result_counts else 0

        # Aggregate latencies
        latencies = [e['latency_seconds'] for e in evaluations]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0
        min_latency = min(latencies) if latencies else 0

        # Aggregate API calls
        total_api_calls = [e['total_api_calls'] for e in evaluations]
        avg_api_calls = sum(total_api_calls) / len(total_api_calls) if total_api_calls else 0

        return {
            'total_tests': len(evaluations),
            'passed': passed,
            'failed': failed,
            'pass_rate': (passed / len(evaluations)) * 100 if evaluations else 0,

            'result_counts': {
                'average': round(avg_results, 2),
                'min': min(result_counts) if result_counts else 0,
                'max': max(result_counts) if result_counts else 0,
                'in_range_count': sum(1 for e in evaluations if e.get('in_target_range', False))
            },

            'latency': {
                'average_seconds': round(avg_latency, 3),
                'min_seconds': round(min_latency, 3),
                'max_seconds': round(max_latency, 3),
                'acceptable_count': sum(1 for e in evaluations if e.get('latency_acceptable', False))
            },

            'api_calls': {
                'average_total': round(avg_api_calls, 2)
            }
        }
