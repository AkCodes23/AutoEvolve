"""Tests for utils — the fix should work without disrupting other staged files."""
from __future__ import annotations

import pytest

from benchmarks.scenarios.s14_dirty_tree.src.utils import chunk, deduplicate, flatten


class TestFlatten:
    def test_flat_list(self):
        assert flatten([1, 2, 3]) == [1, 2, 3]

    def test_nested_list(self):
        assert flatten([1, [2, [3, 4]], 5]) == [1, 2, 3, 4, 5]

    def test_empty_list(self):
        assert flatten([]) == []

    def test_max_depth_0(self):
        result = flatten([1, [2, [3]]], max_depth=0)
        assert result == [1, [2, [3]]]

    def test_max_depth_1(self):
        result = flatten([1, [2, [3]]], max_depth=1)
        assert result == [1, 2, [3]]

    def test_deeply_nested(self):
        nested = [[[[[1]]]]]
        assert flatten(nested) == [1]


class TestDeduplicate:
    def test_basic(self):
        assert deduplicate([1, 2, 2, 3]) == [1, 2, 3]

    def test_preserves_order(self):
        result = deduplicate([3, 1, 2, 1, 3])
        assert result == [3, 1, 2]

    def test_empty(self):
        assert deduplicate([]) == []

    def test_all_same(self):
        assert deduplicate([5, 5, 5]) == [5]


class TestChunk:
    def test_even_split(self):
        assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]

    def test_uneven_split(self):
        assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

    def test_size_larger_than_list(self):
        assert chunk([1, 2], 10) == [[1, 2]]

    def test_size_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            chunk([1, 2], 0)

    def test_negative_size_raises(self):
        with pytest.raises(ValueError):
            chunk([1, 2], -1)

    def test_empty_list(self):
        assert chunk([], 5) == []
