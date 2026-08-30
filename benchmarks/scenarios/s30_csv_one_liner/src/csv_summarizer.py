"""Ultra-minimal stdlib CSV column summarizer in 4 lines."""
import csv
import io


def summarize_csv_column(csv_text: str, column_index: int) -> float:
    """Calculate mean of a column using pure stdlib csv in 4 lines."""
    reader = csv.reader(io.StringIO(csv_text.strip()))
    vals = [float(row[column_index]) for row in reader if row and len(row) > column_index]
    return sum(vals) / len(vals) if vals else 0.0
