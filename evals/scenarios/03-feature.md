# Scenario 03: add pagination

**Task to give the agent:** "Add a `?page=` parameter to the `list_items` endpoint.
Existing callers that pass no page must behave exactly as before."

**Setup:** a `list_items` handler that returns all items, plus a test or two for the
current behavior.

**The signal:** an acceptance check (no single number). Two things must hold: `?page=2`
returns the right slice, and a request with no `page` returns what it always did.

**What the mindset should change (treatment vs control):**
- Writes the acceptance checks down first (the two conditions), then implements toward them.
- Makes the smallest change that satisfies both; does not refactor the handler wholesale.
- Treats the guardrail as non-negotiable: **validates** `page` (rejects negative or
  non-integer input) rather than trusting it.
- Verifies both conditions by running them, keeps the change, journals it.

**Failure modes a weak run shows:** breaks the no-page default, skips input validation, or
builds a general filtering framework when one parameter was asked for.
