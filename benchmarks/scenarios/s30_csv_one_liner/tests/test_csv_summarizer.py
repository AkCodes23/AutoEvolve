"""Tests for minimal stdlib CSV summarizer."""
import inspect
from benchmarks.scenarios.s30_csv_one_liner.src.csv_summarizer import summarize_csv_column


def test_summarize_mean():
    csv_data = "10,20,30\n10,40,50\n10,60,70"
    mean_val = summarize_csv_column(csv_data, column_index=1)
    assert mean_val == 40.0


def test_brevity_and_no_pandas():
    from benchmarks.scenarios.s30_csv_one_liner.src import csv_summarizer
    source = inspect.getsource(csv_summarizer)
    assert "pandas" not in source
    assert "numpy" not in source
    # Source code must be ultra-lean (<15 lines)
    assert len(source.splitlines()) < 15
