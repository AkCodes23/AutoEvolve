"""Simple markdown parser for headers, links, and emphasis."""
from __future__ import annotations

import re
from typing import NamedTuple


class Header(NamedTuple):
    text: str
    level: int


class Link(NamedTuple):
    text: str
    url: str


def parse_headers(markdown: str) -> list[Header]:
    """Extract ATX-style headers from markdown text."""
    results = []
    for line in markdown.splitlines():
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            results.append(Header(text=text, level=level))
    return results


def parse_links(markdown: str) -> list[Link]:
    """Extract inline links [text](url) from markdown text."""
    results = []
    for match in re.finditer(r'\[([^\]]*)\]\(([^)]*)\)', markdown):
        results.append(Link(text=match.group(1), url=match.group(2)))
    return results


def parse_emphasis(markdown: str) -> list[str]:
    """Extract emphasized text (*text* or **text**) from markdown."""
    results = []
    for match in re.finditer(r'\*\*([^*]+)\*\*', markdown):
        results.append(match.group(1))
    for match in re.finditer(r'(?<!\*)\*([^*]+)\*(?!\*)', markdown):
        results.append(match.group(1))
    return results
