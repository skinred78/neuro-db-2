"""
Semantic Pipeline Test Runner (MVP)

Orchestrates test execution across tool configurations, collects metrics,
and generates comparison reports.

MVP Note: This framework is ready for integration with the semantic query pipeline.
Currently uses mock execution to demonstrate framework structure.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor

from poc_api_first.tests.test_configurations import (
    MVP_CONFIGURATIONS,
    CAPABILITY_MATRIX
)
from poc_api_first.evaluators.quantitative_metrics import QuantitativeMetrics
from poc_api_first.config import Config


class SemanticPipelineTestRunner:
    """
    MVP Test Runner for semantic query pipeline evaluation.

    Orchestrates test execution, metric collection, and comparison generation
    across multiple tool configurations.
    """

    def __init__(self, test_data_path: str = None):
        """
        Initialize test runner.

        Args:
            test_data_path: Path to test data directory (defaults to tests/test_data/)
        """
        if test_data_path is None:
            test_data_path = Path(__file__).parent / 'test_data'
        else:
            test_data_path = Path(test_data_path)

        self.test_data_path = test_data_path
        self.test_suites = self.load_test_suites()
        self.configurations = self._init_configurations()
        self.results = []

        # Initialize evaluators
        # NOTE: 30s threshold allows for multi-API round trips with timeouts
        # (UMLS ~2-5s + PubTator ~1-3s + expansion ~3-5s) × N terms + PubMed ~3-5s
        # Increased from 25s due to external API variability
        self.quantitative_evaluator = QuantitativeMetrics(
            target_range=(5, 50),  # Raised max from 20 to 50 for broader queries
            latency_threshold=30.0,  # Raised from 25s to account for API variability
            strict_range_check=False  # Only enforce minimum (max is informational)
        )

    def _init_configurations(self) -> List:
        """Initialize test configurations (MVP: UMLSPubTator, FullHybrid)."""
        configs = []
        for ConfigClass in MVP_CONFIGURATIONS:
            try:
                config = ConfigClass()
                configs.append(config)
            except Exception as e:
                print(f"Warning: Could not initialize {ConfigClass.__name__}: {e}")
                print(f"  Skipping this configuration for testing.")
        return configs

    def load_test_suites(self) -> Dict[str, List[Dict]]:
        """
        Load test data from JSON files.

        Returns:
            Dictionary mapping suite names to test case lists
        """
        suites = {}

        # Load benchmark queries (MVP focus)
        benchmark_file = self.test_data_path / 'benchmark_queries.json'
        if benchmark_file.exists():
            with open(benchmark_file) as f:
                suites['benchmark'] = json.load(f)

        return suites

    def run_all_tests(self, parallel: bool = False) -> Dict[str, Any]:
        """
        Execute all test cases across all configurations.

        Args:
            parallel: Whether to run tests in parallel (MVP: sequential recommended)

        Returns:
            Complete test results with comparisons
        """
        print(f"\n{'='*60}")
        print(f"MVP Test Runner - Semantic Pipeline Evaluation")
        print(f"{'='*60}\n")
        print(f"Configurations: {len(self.configurations)}")
        print(f"Test Suites: {list(self.test_suites.keys())}")
        print(f"Parallel Execution: {parallel}\n")

        for config in self.configurations:
            print(f"\n--- Testing Configuration: {config.name} ---\n")

            for suite_name, test_cases in self.test_suites.items():
                print(f"Running {suite_name} suite ({len(test_cases)} cases)...")

                suite_results = self.run_test_suite(
                    config, suite_name, test_cases, parallel
                )
                self.results.append(suite_results)

        # Generate comparison report
        comparison = self.generate_comparison_report()

        return {
            'configurations': [c.name for c in self.configurations],
            'total_tests': sum(r['summary']['total'] for r in self.results),
            'results': self.results,
            'comparison': comparison,
            'timestamp': datetime.now().isoformat()
        }

    def run_test_suite(
        self,
        config,
        suite_name: str,
        test_cases: List[Dict],
        parallel: bool
    ) -> Dict[str, Any]:
        """
        Run single test suite with specific configuration.

        Args:
            config: Configuration object
            suite_name: Name of test suite
            test_cases: List of test case dictionaries
            parallel: Whether to run in parallel

        Returns:
            Suite results with summary
        """
        if parallel:
            with ThreadPoolExecutor(max_workers=Config.TEST_WORKERS) as executor:
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
            # Use config's run() method if available (integrated pipeline)
            # Otherwise fall back to mock execution for demo purposes
            if hasattr(config, 'run'):
                result = config.run(
                    user_input=test_case['input'],
                    days=60,
                    max_results=20,
                    verbose=False
                )
            else:
                # Fallback: Mock result for configs without run() method
                result = self._mock_pipeline_execution(config, test_case)

            latency_seconds = time.time() - start_time

            # Evaluate result
            evaluation = self.evaluate_result(test_case, result, latency_seconds)

            # NOTE: Runner measures latency externally and embeds it in result record.
            # This is the AUTHORITATIVE latency field that evaluators should use.
            return {
                'test_id': test_case['test_id'],
                'input': test_case['input'],
                'config': config.name,
                'result_count': result['result_count'],
                'latency_seconds': latency_seconds,  # AUTHORITATIVE measurement
                'api_calls': result.get('api_calls', {}),
                'classifications': result.get('classifications', {}),
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

    def _mock_pipeline_execution(self, config, test_case: Dict) -> Dict[str, Any]:
        """
        Mock pipeline execution for MVP demonstration.

        TODO: Remove when actual pipeline is integrated.

        Returns:
            Mock result simulating pipeline output
        """
        # Simulate different performance for different configs
        if config.name == 'UMLSPubTator':
            result_count = 7  # Moderate results
        elif config.name == 'FullHybrid':
            result_count = 12  # Better results with NeuroDB-2
        else:
            result_count = 3  # Baseline

        return {
            'result_count': result_count,
            'api_calls': {
                'pubmed': 1,
                'umls': 3,
                'pubtator': 1 if config.use_pubtator else 0
            },
            'classifications': {},
            'query': f"mock_query_{test_case['test_id']}"
        }

    def evaluate_result(
        self,
        test_case: Dict,
        result: Dict,
        latency_seconds: float
    ) -> Dict[str, Any]:
        """
        Evaluate test result using available evaluators.

        Args:
            test_case: Test case definition
            result: Pipeline result
            latency_seconds: Measured latency

        Returns:
            Dictionary with all evaluation metrics
        """
        # Prepare result record for evaluators
        result_record = {
            **result,
            'latency_seconds': latency_seconds  # Embed authoritative latency
        }

        evaluation = {}

        # Quantitative metrics (always evaluated)
        evaluation['quantitative'] = self.quantitative_evaluator.evaluate(
            test_case, result_record
        )

        # TODO: Add semantic accuracy evaluator when pipeline ready
        # config_name = result_record.get('config', 'unknown')
        # if CAPABILITY_MATRIX.get(config_name, {}).get('supports_semantic_classification'):
        #     evaluation['semantic'] = self.semantic_evaluator.evaluate(
        #         test_case, result_record
        #     )

        return evaluation

    def summarize_results(self, results: List[Dict]) -> Dict[str, Any]:
        """
        Summarize test suite results.

        Args:
            results: List of test results

        Returns:
            Summary statistics
        """
        total = len(results)
        passed = sum(1 for r in results if r.get('status') == 'PASS')
        failed = sum(1 for r in results if r.get('status') == 'FAIL')
        errors = sum(1 for r in results if r.get('status') == 'ERROR')

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'pass_rate': (passed / total * 100) if total > 0 else 0
        }

    def generate_comparison_report(self) -> Dict[str, Any]:
        """
        Generate cross-configuration comparison.

        Returns:
            Comparison analysis across all configurations
        """
        if not self.results:
            return {'error': 'No results available for comparison'}

        # Group results by configuration
        by_config = {}
        for suite_result in self.results:
            config_name = suite_result['config']
            if config_name not in by_config:
                by_config[config_name] = []
            by_config[config_name].extend(suite_result['results'])

        # Aggregate metrics per configuration
        comparison = {}
        for config_name, results in by_config.items():
            comparison[config_name] = {
                'summary': {
                    'total_tests': len(results),
                    'passed': sum(1 for r in results if r.get('status') == 'PASS'),
                    'failed': sum(1 for r in results if r.get('status') == 'FAIL'),
                    'errors': sum(1 for r in results if r.get('status') == 'ERROR')
                },
                'quantitative': self.quantitative_evaluator.aggregate_metrics(results)
            }

        return comparison

    def save_results(self, output_path: str = None):
        """
        Save test results to JSON file.

        Args:
            output_path: Path to save results (defaults to results/ directory)
        """
        if output_path is None:
            output_dir = Path(__file__).parent.parent / 'results'
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f'test_results_{timestamp}.json'

        results_data = self.run_all_tests(parallel=False)

        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"\n✅ Results saved to: {output_path}")
        return output_path


def main():
    """Run MVP test suite."""
    print("MVP Semantic Pipeline Test Runner\n")

    # Check for required environment variables
    if not Config.UMLS_API_KEY:
        print("⚠️  Warning: UMLS_API_KEY not set in environment")
        print("   Some configurations may not initialize properly\n")

    runner = SemanticPipelineTestRunner()

    # Run tests
    results = runner.run_all_tests(parallel=False)

    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}\n")

    for config_name, metrics in results['comparison'].items():
        summary = metrics['summary']
        quant = metrics.get('quantitative', {})

        print(f"{config_name}:")
        print(f"  Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']} ({quant.get('pass_rate', 0):.1f}%)")
        if 'result_counts' in quant:
            print(f"  Avg Results: {quant['result_counts']['average']}")
        if 'latency' in quant:
            print(f"  Avg Latency: {quant['latency']['average_seconds']}s")
        if summary.get('errors', 0) > 0:
            print(f"  Errors: {summary['errors']}")
        print()

    # Save results
    output_file = runner.save_results()

    return results


if __name__ == '__main__':
    main()
