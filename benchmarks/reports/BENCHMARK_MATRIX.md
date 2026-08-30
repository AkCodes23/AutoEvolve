# AutoEvolve SWE Benchmark: Quantified Evaluation Matrix

**Evaluation Date**: 2026-08-28T15:10:32Z
**Matrix Run**: 2026-08-28T15:09:52Z
**Data Source**: All figures below are computed from measured trial results in this matrix run.
**Verification Method**: Programmatic AST analysis, cryptographic SHA-256 test integrity checks, git cleanliness inspections, and sub-process test execution.

---

## 1. Multi-Condition Quantified SWE Matrix

| Metric Dimension | Measurement Method | Condition 0: Unguided Baseline LLM | Condition 1: Karpathy Guidelines | Condition 2: Ponytail 7-Rung Minimalism | Condition 3: AutoEvolve Mindset | Condition 5: AutoEvolve v3.0 (PRAXIST Evidence Inheritance) | Target / Threshold |
|:---|:---|:---: | :---: | :---: | :---: | :---:|:---:|
| **Functional Pass Rate** | Pytest exit codes across trials | 83.3% (5/6) | 100.0% (6/6) | 100.0% (6/6) | 100.0% (6/6) | 100.0% (6/6) | 100.0% |
| **Test Integrity** | SHA-256 hash matching on test files | Tampered | Intact | Intact | Intact | Intact | Intact (0% tamper) |
| **Avg Added LoC (S3)** | Executable statements (excl. blanks/docstrings) | 80 LoC | 53 LoC | 47 LoC | 47 LoC | 47 LoC | <= 45 LoC |
| **Caller Safety Rate (S1)** | Blast-radius audit on non-target modifications | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| **Peak Context Tokens (S4)** | Measured ingested test-runner output tokens | 24 tokens | 24 tokens | 24 tokens | 24 tokens | 24 tokens | <= 1,500 tokens |
| **Git Cleanliness (S5)** | Measured dirty/untracked state vs baseline commit | 1 dirty / 1 untracked | 0 dirty / 0 untracked | 0 dirty / 0 untracked | 0 dirty / 0 untracked | 0 dirty / 0 untracked | 0 dirty / 0 untracked |
| **AST Comment Noise Rate (S6)** | Narration, dead code, divider findings | 7 findings | 2 findings | 1 findings | 0 findings | 0 findings | 0 findings |
| **YAGNI Brevity Score** | AST complexity & stdlib purity ratio | 0.00 / 1.00 | 0.92 / 1.00 | 0.98 / 1.00 | 0.98 / 1.00 | 0.98 / 1.00 | >= 0.90 |
| **Composite SWE Readiness** | Weighted composite across all scenarios | **22.50%** | **92.80%** | **96.70%** | **99.70%** | **99.70%** | >= 95.0% |

---

## 2. Key Empirical Findings

1. **Top Performer**:
   Condition 3: AutoEvolve Mindset leads with a composite readiness score of 99.70%.
2. **Test Integrity Enforcement**:
   1 of 5 condition(s) showed test-file tampering under cryptographic SHA-256 verification.
3. **Context Ingestion Spread (S4)**:
   Peak measured context ingestion ranged from 24 tokens (Condition 3: AutoEvolve Mindset, policy: summary_tail) to 24 tokens (Condition 0: Unguided Baseline LLM, policy: full_stream).
