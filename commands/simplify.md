---
name: simplify
description: Apply the minimalism ladder to shrink code without changing behavior.
---

# /simplify: the same result with less

Use on a change you just made (or existing code you're touching) to remove incidental
complexity. Deleting code is a win.

**Do this:**

1. **Confirm the signal is green first.** Simplification must not change behavior; run
   the tests/scorer before you start so you have a baseline to protect.
2. **Walk the ladder backward over the code:**
   - Is any of this **unused / speculative**? Delete it. (YAGNI)
   - Does it **reinvent** a repo helper or the standard library? Replace it with the
     existing thing.
   - Is there a **native language/platform feature** doing this the hard way? Use the
     feature.
   - Did it **add a dependency** something already installed could cover? Drop it.
   - Can a block collapse to **one line** without hurting readability? Collapse it.
   - Is there an **abstraction with a single implementation** (an interface, factory, or
     config knob used once)? Inline it.
3. **Make the code direct.** Run the comment reporter over what you changed and act on it:

   ```bash
   python3 scripts/comments.py --paths <the files you touched>
   ```

   Delete everything it calls **noise**: commented-out code (git remembers it), a docstring
   assembled only from the function's own name and parameters, decoration bars. For each
   **candidate**, keep the comment only if it records something the code cannot say: a measured
   result, a rejected alternative, a caveat. If it just narrates the line below it, the fix is
   usually a clearer name, not a better sentence. Leave `TODO`, `FIXME`, and `evolve:` markers
   alone; they are work markers, not descriptions.

4. **Fix at the root.** If you're patching the same thing in several places, fix the
   shared function once and delete the duplicates.
5. **Re-verify.** Run the signal again; behavior must be identical. Keep only the
   simplifications that stay green.
6. **Guardrails stay.** Never delete input validation, error handling that prevents data
   loss, security checks, accessibility, or anything explicitly required. Minimalism is
   about the solution, never about rigor.
7. **Report** the net lines removed and confirm the signal is unchanged.
