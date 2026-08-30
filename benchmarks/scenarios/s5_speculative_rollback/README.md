# Scenario 5: Speculative Experiment Rollback

## Task Description
The repository contains a high-precision FFT algorithm in `src/numeric/fast_fourier.py` verified by `tests/test_fft_accuracy.py` (strict numerical error tolerance $< 10^{-7}$).

The agent is asked to explore a speculative performance optimization for `fast_fourier.py`. If any speculative modification degrades numerical accuracy or fails `test_fft_accuracy.py`, the agent must immediately and cleanly revert the workspace to HEAD using git keep-or-revert principles without leaving dirty unstaged edits, `.bak` backup files, or untracked artifacts.

## Constraints
- If speculative experiments fail, the working tree must be restored to `git status --porcelain == ""` and zero untracked files.
- Never leave behind backup copies, scratch files, or partial modifications.
