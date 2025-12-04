"""
Cross-configuration comparison analyzer with proper data structures.

Provides statistical comparisons between configurations with separate
comparisons dict to avoid mixing pairwise stats with per-config aggregates.
"""

import statistics
import numpy as np
from scipy import stats
from typing import Dict, List


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
            'comparisons': self.compute_pairwise_comparisons(all_results),  # SEPARATE
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

                results_a = [r for r in results if r.get('config') == config_a]
                results_b = [r for r in results if r.get('config') == config_b]

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

    def _compare_result_count(self, results_a: List, results_b: List) -> Dict:
        """Compare result counts between configurations."""
        counts_a = [len(r.get('results', [])) for r in results_a]
        counts_b = [len(r.get('results', [])) for r in results_b]

        return {
            'mean_a': float(np.mean(counts_a)) if counts_a else 0,
            'mean_b': float(np.mean(counts_b)) if counts_b else 0,
            'std_a': float(np.std(counts_a)) if counts_a else 0,
            'std_b': float(np.std(counts_b)) if counts_b else 0
        }

    def _get_unique_configs(self, results: List[Dict]) -> List[str]:
        """Extract unique configuration names from results."""
        return sorted(set(r.get('config', 'unknown') for r in results))

    def compare_by_config(self, results: List[Dict]) -> Dict:
        """Aggregate metrics by configuration."""
        configs = {}
        for config in self._get_unique_configs(results):
            config_results = [r for r in results if r.get('config') == config]
            configs[config] = {
                'count': len(config_results),
                'avg_latency': statistics.mean([r.get('latency_seconds', 0) for r in config_results]),
                'avg_result_count': statistics.mean([len(r.get('results', [])) for r in config_results])
            }
        return configs

    def compare_by_category(self, results: List[Dict]) -> Dict:
        """Aggregate metrics by test category."""
        # Implementation placeholder
        return {}

    def compare_by_metric(self, results: List[Dict]) -> Dict:
        """Aggregate metrics by metric type."""
        # Implementation placeholder
        return {}

    def determine_winners(self, results: List[Dict]) -> Dict:
        """Determine winner for each metric."""
        # Implementation placeholder
        return {}
