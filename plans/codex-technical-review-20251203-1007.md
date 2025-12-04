# Technical Review — Semantic Pipeline Test Suite Design

Date: 2025-12-03 10:07
Reviewed file: plans/251203-semantic-pipeline-test-suite-design.md

Scope covered:
- Section 2: Test framework architecture (soundness)
- Section 2.2: Tool configurations (implementation validity)
- Section 2.4/related: Evaluation metrics definitions (appropriateness)
- Section 6: Comparison methodology (fairness)
- Section 4.1: Success criteria (realism)
- Section 9: Risks (completeness)

Note on numbering mismatch: The plan places evaluation metric definitions in Section 2.4 and comparison methodology in Section 6; the review request referenced Sections 3 and 4 respectively. This review evaluates the intended topics regardless of numbering.

---

## Findings by Area

### 2. Test Framework Architecture

- [CRITICAL] Metric applicability mismatch across configurations (2.3, 2.4): Baseline configuration does not emit semantic classifications, yet downstream evaluators (semantic accuracy) expect them. This penalizes the baseline unfairly or yields division-by-zero/empty denominators.
- [HIGH] Concurrency vs rate limiting (2.3): `ThreadPoolExecutor(max_workers=5)` without coordination to API throttling risks PubTator/UMLS rate-limit errors and noisy latency measurements.
- [HIGH] Undefined attributes/methods (2.2, 2.3): `config.name`, `self.umls_client`, `self.pubtator_client`, `self.is_abbreviation`, `self.load_neurodb`, and `count_api_calls` are referenced but not defined/injected, risking runtime errors.
- [MEDIUM] Directory/comments mismatch (2.1): Comments say “4 tool combination configs,” but runner executes 5 (including baseline). Minor clarity issue.
- [MEDIUM] Error handling surface (2.3): Runner catches broad `Exception` but there’s no structured error type mapping to the error analysis taxonomy.

### 2.2 Tool Configurations

- [CRITICAL] Baseline definition contradiction: “blind expansion” vs “component detection” (2.2). If truly blind with no semantic typing, “component detection” should not be asserted. Ambiguity affects fairness and expectations.
- [CRITICAL] Non-portable hardcoded paths (2.2, Appendix C): `neurodb_path = "/Users/sam/NeuroDB-2/data/neuro_terms.json"` and absolute paths in Appendix C will break CI and teammate environments. Use repo-relative paths and env vars.
- [HIGH] FullHybrid short-circuiting (2.2): Returning immediately after NeuroDB match avoids consulting PubTator when both could provide evidence. Prefer ensembling or confidence arbitration rather than first-match wins.
- [MEDIUM] UMLS-only lacks explicit abbreviation policy (2.2): Intentional, but document that literals will be classified without expansion and ensure tests expect that.
- [MEDIUM] Missing retry/backoff and circuit breakers for API clients in config flows.

### 2.4 Evaluation Metrics Definitions

- [CRITICAL] Latency source inconsistency (2.3 vs 2.4): Runner measures `latency` externally; `QuantitativeMetrics` expects `result['latency_seconds']`. If pipeline doesn’t embed latency, the metric fails. Use a single authoritative latency field on the runner record passed to evaluators.
- [HIGH] Result count “in-range” (5–20) as a pass driver (2.4, 4.1): This incentivizes pruning rather than retrieval quality and penalizes valid query variability. Treat as informational, not gating.
- [HIGH] Heuristic relevance (2.4): String-inclusion of raw tokens in title/abstract will mis-estimate relevance (no stemming/synonyms) and should not feed comparison scoring until replaced by manual labels or a validated proxy.
- [MEDIUM] API call counting unspecified (2.4): Counting functions are referenced but not defined, risking under/over-counting and unfair cost comparisons.

### 6. Comparison Methodology (Fairness)

- [CRITICAL] Capability-normalized metrics missing (6.1): Apply only the metrics a configuration can produce (e.g., exclude semantic accuracy for the baseline or provide an adapter that maps components). Otherwise, comparisons are biased.
- [HIGH] Cache control (6.1, Phase 3): “Clear cache between configurations” is noted, but cold/warm comparisons need identical procedures per config (same warm-up set, same order) to avoid cache-skewed outcomes.
- [HIGH] Statistical methods not integrated (6.2): t-tests and CIs are proposed but not wired into evaluators/reports; risk of non-actionable “significance” claims.

### 4.1 Success Criteria (Realism)

- [HIGH] Latency targets (4.1, Phase 3): <2s p95 warm across external APIs may be aggressive without robust caching/batching. Ensure targets align with Phase 3 cold/warm definitions and infra capability.
- [HIGH] Precision@10 ≥80% (4.1, 5.2): Reasonable for mature systems, but it becomes a blocker if manual review is delayed. Should be staged: informative in early runs, gating later.
- [MEDIUM] Result-count in-range for ≥75% (4.1): Valid for many queries but not niche ones (rare terms). Make category-specific or exclude rare/niche from this gate.

### 9. Risks & Mitigations (Completeness)

- [HIGH] Missing: Ground truth subjectivity and adjudication (9). Add inter-rater agreement (e.g., Cohen’s kappa), dual-review protocol, and tie-break rules.
- [HIGH] Missing: Environment/portability (9). Hardcoded paths and secrets handling (UMLS key) can break CI/local runs. Add .env + config loader and repo-relative paths.
- [MEDIUM] Missing: CI with no network (9). Ensure mocks cover clients end-to-end and validate parity against recorded cassettes.
- [MEDIUM] Missing: Dataset/version pinning (9). Explicitly pin UMLS release, PubTator model/version, and PubMed query parameters for reproducibility; store run metadata.
- [LOW] Missing: Cost/availability posture for third-party APIs (SLA, quotas, outage playbook).

---

## Cross-Cutting Inconsistencies and Gaps

- Numbering vs scope confusion in the document could lead to mis-implementation if teams key off section numbers. Align titles and references.
- Benchmarks count mismatch: 1.8 lists 5 benchmarks; 5.1 “Gold Standard Creation” mentions 10; reconcile before planning manual workload.
- Appendix example tables show illustrative numbers; ensure they are clearly labeled as examples in reports to avoid misinterpretation.

---

## Recommendations

1) Normalize metrics per capability and fix evaluator IO contract
- Add a configuration capability matrix; only compute metrics a config can produce (e.g., disable semantic accuracy for baseline).
- Standardize runner output schema and pass that to metrics (include authoritative `latency_seconds` on runner record).

2) Remove hardcoded paths and enforce environment portability
- Use repo-relative paths, `.env` for secrets, and a config loader usable in CI and local dev.
- Update Appendix C to reflect relative paths and document environment variables.

3) Refine comparison and thresholds to avoid bias
- Make result-count range non-gating, category-aware, or report-only.
- Stage Precision@10 as non-gating until gold standard/manual labels are available.
- Integrate caching policy and warm-up protocols identically per configuration.

4) Strengthen tool configurations and ensemble logic
- In FullHybrid, combine NeuroDB and PubTator signals with confidence arbitration rather than short-circuiting.
- Add retries/backoff for API calls; surface structured errors for the error analysis framework.

5) Operationalize statistical rigor
- Implement the t-tests/CI computations in the analyzer; define minimum sample sizes per category and per configuration before claiming significance.

---

## Severity Totals

- CRITICAL: 5
- HIGH: 10
- MEDIUM: 8
- LOW: 3

---

## Overall Assessment

APPROVED_WITH_CHANGES — Architecture and methodology are directionally sound, but there are blocking issues around metric fairness, non-portable paths, and evaluator/runner inconsistencies that must be addressed before reliable execution and comparison.

