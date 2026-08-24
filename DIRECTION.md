# Direction

## Objective
<!-- What are we trying to achieve? (e.g. Optimize cache lookup latency to <1ms, Fix payment retry bug) -->

## Signal
<!-- Command to verify correctness or measure performance. Must be frozen during experiment. -->
```bash
pytest tests/ -v
```

## Hard Gates (must pass: binary)
<!-- Deterministic constraints. Any failure → score = 0. -->
- Zero regression on existing test suite
- No external dependencies beyond Python standard library
- Maintain backward compatibility for public API contracts

## Soft Gates (should meet: proportional)
<!-- Continuous metrics. Regression scales score down, does not force immediate failure. -->
- <!-- e.g. p95 latency < 200ms -->
- <!-- e.g. Memory peak ≤ 15MB -->
- <!-- e.g. Diff LOC ≤ golden reference × 1.5 -->

## Resource Quotas
<!-- Proactive limits to prevent wasted cycles against exhausted services. -->
- <!-- e.g. API rate limit: 60 req/min (pause, don't retry) -->
- <!-- e.g. LLM token budget: 50k tokens per loop -->

## Budget
- Max iterations: 10
- Max diff size per step: 50 lines
