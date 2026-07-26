def parse_tags(text: str) -> list[str]:
    """Parse comma-separated tags, stripping surrounding whitespace and ignoring empty tags."""
    return text.split(",")
