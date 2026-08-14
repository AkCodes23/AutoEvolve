# Direction

## Objective
<!-- What are we trying to achieve? (e.g. Optimize cache lookup latency to <1ms, Fix payment retry bug) -->

## Signal
<!-- Command to verify correctness or measure performance. Must be frozen during experiment. -->
```bash
pytest tests/ -v
```

## Guardrails
<!-- Invariants that must NEVER be violated -->
- Zero regression on existing test suite
- No external dependencies beyond Python standard library
- Maintain backward compatibility for public API contracts

## Budget
- Max iterations: 10
- Max diff size per step: 50 lines
