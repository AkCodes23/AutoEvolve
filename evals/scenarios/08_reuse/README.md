# 08_reuse

## The task

`reuse.py` is a small product catalog module. `find_product(catalog, raw_sku)` and
`remove_product(catalog, raw_sku)` only match a product code spelled exactly the way it is
stored, so `"ab 12"` does not find the product registered as `"AB-12"`. The task is to make
both resolve any spelling of the same code.

Task text for `evals/profile.py` `TASKS` and `evals/manifest.json`:

> In reuse.py, find_product(catalog, raw_sku) and remove_product(catalog, raw_sku) only match
> a product code spelled exactly the way it is stored, so "ab 12" does not find the product
> that was registered as "AB-12". Fix both so that any spelling of the same code resolves to
> the same catalog entry: surrounding whitespace is ignored, letter case is ignored, and a
> space, an underscore and a hyphen are interchangeable separators. find_product must return
> the stored product record or None when nothing matches; remove_product must delete the entry
> and return True when it matched, and return False and leave the catalog unchanged when it did
> not. Leave the rest of the module working as it does today.

## The signal

The module already contains `normalize_sku()`, a documented helper whose docstring states that
it is "the module's single definition of the same product code", and three existing functions
(`register_product`, `rename_product`, `total_value`) already route through it. The whole
requirement of the two new lookups is "canonicalise the code, then use the dict".

So the literal task can be satisfied two ways:

- **reimplement**: transcribe the rule inline at the call site (or into a fresh private helper).
  Functionally correct, and a second copy of the rule.
- **reuse**: call the helper that is already there.

The discipline under test is the second one:

- ponytail, ladder rung 2: "Already in this codebase? A helper, util, type, or pattern that
  already lives here -> reuse it. Look before you write."
- AutoEvolve, minimalism ladder rung 2: "Reuse: Use existing helper/pattern in this codebase."
- karpathy: does not ask for reuse anywhere. This scenario is therefore expected to favour
  ponytail and AutoEvolve over karpathy and control, and that asymmetry is the reason it exists.
  Read a karpathy result here as "the ruleset does not cover this", not as a defect.

Checks 1 to 5 are ordinary correctness and gate the score. Checks 6 to 8 measure reuse, from
three angles (`find_product`, `remove_product`, and whether the two stay consistent with the
rest of the module when the canonical rule changes). A reader who wants to discount the
reuse discipline should discount all three of those together.

Reuse is detected by BEHAVIOUR, never by reading source text: the module's `normalize_sku` is
replaced with a stub and the new functions are called. Module-level aliases and captured
default arguments are patched too, so `_norm = normalize_sku` and
`def find_product(c, s, _norm=normalize_sku)` count as reuse. Closure capture and a
module-level `functools.partial` are known blind spots and are stated as such in `grade.py`.

## What a good run looks like

Measured with the shipped grader (`python evals/run.py 08_reuse`, and the same grader driven
through the `profile.py` scorer in an isolated interpreter):

| submission | score | notes |
|---|---|---|
| shipped starter (exact-key matching) | 3/8 | fails 1, 3, 6, 7, 8 |
| naive: rule transcribed inline, functionally correct | 5/8 | fails 6, 7, 8 |
| naive variant: same rule written as a regex | 5/8 | fails 6, 7, 8 |
| naive variant: rule moved into a new private helper | 5/8 | fails 6, 7, 8 |
| guided: calls `normalize_sku` | 8/8 | |
| guided variants: module alias, default-arg capture, thin wrapper, both-sides scan | 8/8 | aliasing forms are accepted as reuse |
| reuses the helper but returns the wrong shape | 4/8 | correctness gates: it scores below the correct naive answer |
| file that does not import, or is missing `find_product` | 0/8 | full set of checks reported failed, no harness error |

So the three-way separation is 37.5 percent (starter) / 62.5 percent (naive) / 100 percent
(guided). A condition that moves the graded-checks mean from roughly 62 toward 100 on this
scenario is changing whether the model looks at the file before writing, which is the only
thing this scenario is built to measure.

One deliberate grader design note: the stubs are idempotent, so a defensive solution that
canonicalises both sides of a comparison is not punished. And no correctness input contains a
repeated separator (`"AB  12"`), because the documented rule and a regex spelling of it
disagree there and that difference is not what is being measured.
