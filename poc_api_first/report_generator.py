"""
Markdown Report Generator for Semantic Pipeline Test Results

Converts JSON test results into human-readable markdown reports.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def generate_report(results_path: str, output_path: str = None) -> str:
    """
    Generate markdown report from JSON test results.

    Args:
        results_path: Path to JSON test results file
        output_path: Optional path for output markdown (auto-generates if None)

    Returns:
        Path to generated markdown report
    """
    with open(results_path) as f:
        data = json.load(f)

    # Extract timestamp from filename or use current time
    results_file = Path(results_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    # Build report
    lines = []
    lines.append("# Semantic Pipeline Test Report")
    lines.append("")
    lines.append(f"**Generated**: {timestamp}")
    lines.append(f"**Source**: `{results_file.name}`")
    lines.append("")

    # Summary section
    lines.append("---")
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    # Build summary table
    lines.append("| Config | Passed | Failed | Pass Rate | Avg Latency |")
    lines.append("|--------|--------|--------|-----------|-------------|")

    total_passed = 0
    total_failed = 0

    for config_result in data.get('results', []):
        config_name = config_result.get('config', 'Unknown')
        results = config_result.get('results', [])

        passed = sum(1 for r in results if r.get('status') == 'PASS')
        failed = len(results) - passed
        total_passed += passed
        total_failed += failed

        pass_rate = (passed / len(results) * 100) if results else 0

        latencies = [r.get('latency_seconds', 0) for r in results]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        lines.append(f"| {config_name} | {passed}/{len(results)} | {failed}/{len(results)} | {pass_rate:.0f}% | {avg_latency:.1f}s |")

    # Overall stats
    total_tests = total_passed + total_failed
    overall_rate = (total_passed / total_tests * 100) if total_tests else 0
    lines.append("")
    lines.append(f"**Overall**: {total_passed}/{total_tests} tests passing ({overall_rate:.0f}%)")
    lines.append("")

    # Detailed results per config
    lines.append("---")
    lines.append("")
    lines.append("## Test Details")
    lines.append("")

    for config_result in data.get('results', []):
        config_name = config_result.get('config', 'Unknown')
        results = config_result.get('results', [])

        lines.append(f"### {config_name}")
        lines.append("")

        for result in results:
            test_id = result.get('test_id', 'Unknown')
            input_query = result.get('input', '')
            status = result.get('status', 'UNKNOWN')
            result_count = result.get('result_count', 0)
            latency = result.get('latency_seconds', 0)

            # Status emoji
            status_icon = "✅" if status == "PASS" else "❌"

            lines.append(f"#### {status_icon} {test_id}: {input_query}")
            lines.append("")

            # Basic metrics
            lines.append(f"- **Results**: {result_count} papers (target: 5-20)")
            lines.append(f"- **Latency**: {latency:.1f}s")
            lines.append(f"- **Status**: {status}")
            lines.append("")

            # Classifications
            classifications = result.get('classifications', [])
            if classifications:
                lines.append("**Term Classifications**:")
                lines.append("")
                lines.append("| Original | Resolved | Category | Source | Confidence |")
                lines.append("|----------|----------|----------|--------|------------|")

                for c in classifications:
                    orig = c.get('original_term', '')
                    resolved = c.get('term', c.get('name', ''))
                    category = c.get('category', 'UNKNOWN')
                    source = c.get('disambiguation_source', 'UMLS_direct')
                    confidence = c.get('confidence', 0.5)

                    # Truncate long terms
                    if len(resolved) > 30:
                        resolved = resolved[:27] + "..."

                    lines.append(f"| {orig} | {resolved} | {category} | {source} | {confidence:.1f} |")

                lines.append("")

            # Query (collapsed for readability)
            query = result.get('query', '')
            if query:
                lines.append("<details>")
                lines.append("<summary>Generated PubMed Query</summary>")
                lines.append("")
                lines.append("```")
                # Word wrap long queries
                if len(query) > 80:
                    lines.append(_wrap_query(query))
                else:
                    lines.append(query)
                lines.append("```")
                lines.append("</details>")
                lines.append("")

            lines.append("---")
            lines.append("")

    # Issues summary (for failed tests)
    lines.append("## Issues Summary")
    lines.append("")

    issues = _extract_issues(data)
    if issues:
        for issue_type, issue_list in issues.items():
            lines.append(f"### {issue_type}")
            lines.append("")
            for issue in issue_list:
                lines.append(f"- {issue}")
            lines.append("")
    else:
        lines.append("No issues detected - all tests passing!")
        lines.append("")

    # Write report
    report_content = "\n".join(lines)

    if output_path is None:
        output_dir = Path(results_path).parent
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"report_{timestamp_str}.md"

    with open(output_path, 'w') as f:
        f.write(report_content)

    return str(output_path)


def _wrap_query(query: str, width: int = 80) -> str:
    """Wrap long query strings for readability."""
    words = query.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > width:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + 1

    if current_line:
        lines.append(" ".join(current_line))

    return "\n".join(lines)


def _extract_issues(data: Dict) -> Dict[str, List[str]]:
    """Extract common issues from failed tests."""
    issues = {
        "Disambiguation Errors": [],
        "Result Count Issues": [],
        "Other Issues": []
    }

    seen_disambiguation = set()

    for config_result in data.get('results', []):
        for result in config_result.get('results', []):
            if result.get('status') != 'PASS':
                result_count = result.get('result_count', 0)

                # Check for disambiguation issues
                for c in result.get('classifications', []):
                    orig = c.get('original_term', '')
                    resolved = c.get('term', '')
                    source = c.get('disambiguation_source', '')

                    # Flag likely wrong disambiguations
                    if source == 'PubTator' and orig.lower() != resolved.lower():
                        key = f"{orig} → {resolved}"
                        if key not in seen_disambiguation:
                            seen_disambiguation.add(key)
                            issues["Disambiguation Errors"].append(
                                f"`{orig}` → `{resolved}` (via {source})"
                            )

                # Check result counts
                if result_count == 0:
                    issues["Result Count Issues"].append(
                        f"{result.get('test_id')}: 0 results (query may be too narrow)"
                    )
                elif result_count > 100:
                    issues["Result Count Issues"].append(
                        f"{result.get('test_id')}: {result_count} results (query too broad)"
                    )

    # Remove empty categories
    return {k: v for k, v in issues.items() if v}


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        # Find most recent results file
        results_dir = Path(__file__).parent / "results"
        json_files = sorted(results_dir.glob("test_results_*.json"), reverse=True)

        if not json_files:
            print("Usage: python report_generator.py <results.json>")
            print("No test results found in results/ directory")
            sys.exit(1)

        results_path = json_files[0]
        print(f"Using most recent: {results_path.name}")
    else:
        results_path = sys.argv[1]

    output_path = generate_report(results_path)
    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    main()
