"""Data processing pipeline. This is the code under test.

PROBLEMS:
- process_records() crashes on None, non-list inputs, and dicts with missing keys
- calculate_average() returns infinity on empty list and crashes on non-numeric values
- parse_date() has no timeout or format validation, crashes on garbage input
- write_output() swallows all errors silently

Fix all error handling while preserving correct behavior for valid inputs.
"""


def process_records(records):
    """Process a list of records and return summary statistics."""
    # BUG: no input validation - crashes on None, non-list, or records with missing keys
    total = 0
    count = 0
    for record in records:
        total += record["value"]
        count += 1
    return {"total": total, "count": count, "average": total / count}


def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    # BUG: division by zero on empty list, crashes on non-numeric values
    return sum(numbers) / len(numbers)


def parse_date(date_string):
    """Parse a date string in YYYY-MM-DD format."""
    # BUG: no format validation, crashes on garbage input
    parts = date_string.split("-")
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    return {"year": year, "month": month, "day": day}


def write_output(data, filepath):
    """Write processed data to a file."""
    # BUG: silently swallows ALL errors, including important ones
    try:
        with open(filepath, "w") as f:
            for key, value in data.items():
                f.write(f"{key}: {value}\n")
        return True
    except Exception:
        # Silent swallow - caller never knows it failed
        return True  # BUG: returns True even on failure
