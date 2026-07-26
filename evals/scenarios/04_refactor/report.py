def format_report(data):
    """Format a summary report for a list of items: [{'category': str, 'value': float}]."""
    total = sum(d["value"] for d in data)
    avg = total / len(data)
    categories = set(d["category"] for d in data)
    max_item = max(data, key=lambda x: x["value"])

    lines = ["# Summary Report"]
    lines.append(f"Total Items: {len(data)}")
    lines.append(f"Total Value: {total:.2f}")
    lines.append(f"Average Value: {avg:.2f}")
    lines.append(f"Categories: {', '.join(sorted(categories))}")
    lines.append(f"Top Performer: {max_item['category']} ({max_item['value']:.2f})")
    return "\n".join(lines)


def get_summary(data):
    """Return report text; callers rely on format_report."""
    return format_report(data)
