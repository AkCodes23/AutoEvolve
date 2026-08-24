# Direction

## Objective
<!-- What are we trying to achieve? (e.g. Optimize cache lookup latency to <1ms, Fix payment retry bug) -->

## Signal
<!-- Command to verify correctness or measure performance. Must be frozen during experiment. -->
```bash
pytest tests/ -v
```

## Hard Gates (must pass: binary)
<!-- Canonical deterministic constraints. Any failure -> abort or revert step. -->
- Zero regression on existing test suite
- No external dependencies beyond Python standard library
- Maintain backward compatibility for public API contracts

## Soft Gates (should meet: proportional)
<!-- Continuous performance and quality targets. Regressions scale score down without immediate failure. -->
- <!-- Latency target: e.g. p95 latency <= 200ms -->
- <!-- Memory ceiling: e.g. peak memory <= 15MB -->
- <!-- Diff budget: e.g. modified LOC <= reference * 1.5 -->

## Resource Quotas
<!-- Proactive exhaustion limits. Pause or route around rather than burning retry loops. -->
- <!-- Rate limit: e.g. max 60 req/min (pause until window reset) -->
- <!-- Token ceiling: e.g. max 50k tokens per loop -->

## Budget
- Max iterations: 10
- Max diff size per step: 50 lines
