"""Comprehensive tests for markdown parser — edge cases, boundaries, negatives."""
from __future__ import annotations

import pytest

from benchmarks.scenarios.s13_test_quality.src.markdown_parser import (
    Header,
    Link,
    parse_emphasis,
    parse_headers,
    parse_links,
)


class TestParseHeaders:
    def test_h1(self):
        assert parse_headers("# Hello") == [Header("Hello", 1)]

    def test_h2_through_h6(self):
        for level in range(2, 7):
            hashes = "#" * level
            result = parse_headers(f"{hashes} Level {level}")
            assert result == [Header(f"Level {level}", level)]

    def test_multiple_headers(self):
        md = "# First\n## Second\n### Third"
        result = parse_headers(md)
        assert len(result) == 3

    def test_empty_input(self):
        assert parse_headers("") == []

    def test_no_space_after_hash_is_not_header(self):
        assert parse_headers("#NotAHeader") == []

    def test_unicode_header(self):
        result = parse_headers("# こんにちは")
        assert result == [Header("こんにちは", 1)]

    def test_header_with_inline_code(self):
        result = parse_headers("## The `main` function")
        assert result[0].text == "The `main` function"

    def test_seven_hashes_not_header(self):
        assert parse_headers("####### Not valid") == []


class TestParseLinks:
    def test_simple_link(self):
        result = parse_links("[Google](https://google.com)")
        assert result == [Link("Google", "https://google.com")]

    def test_multiple_links(self):
        md = "[A](http://a.com) and [B](http://b.com)"
        assert len(parse_links(md)) == 2

    def test_empty_text_link(self):
        result = parse_links("[](http://empty.com)")
        assert result == [Link("", "http://empty.com")]

    def test_empty_url_link(self):
        result = parse_links("[text]()")
        assert result == [Link("text", "")]

    def test_no_links(self):
        assert parse_links("No links here") == []

    def test_link_with_spaces_in_text(self):
        result = parse_links("[click here please](http://x.com)")
        assert result[0].text == "click here please"

    def test_empty_input(self):
        assert parse_links("") == []


class TestParseEmphasis:
    def test_single_emphasis(self):
        result = parse_emphasis("This is *important*")
        assert "important" in result

    def test_bold_emphasis(self):
        result = parse_emphasis("This is **very bold**")
        assert "very bold" in result

    def test_no_emphasis(self):
        assert parse_emphasis("plain text") == []

    def test_empty_input(self):
        assert parse_emphasis("") == []

    def test_multiple_emphasis(self):
        result = parse_emphasis("*one* and *two*")
        assert len(result) >= 2


class TestNegativeCases:
    def test_malformed_link_no_paren(self):
        assert parse_links("[broken link") == []

    def test_malformed_header_only_hashes(self):
        assert parse_headers("###") == []

    def test_emphasis_unclosed(self):
        result = parse_emphasis("*unclosed emphasis")
        assert len(result) == 0 or "unclosed emphasis" not in result
