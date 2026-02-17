"""
processor.py — Smart Lead Processor
Reads and manages the jobs_database.csv in drip mode (one lead per run).
"""

import csv
from datetime import datetime, timezone
from typing import Optional


FIELDNAMES = [
    "Company Name",
    "Contact Email",
    "Role",
    "Context/JD",
    "Why I Love Them",
    "Sent Status",
    "Sent Time",
]


def get_next_lead(csv_path: str) -> Optional[dict]:
    """
    Return the first unsent lead from the CSV, or None if all are sent.
    A lead is considered unsent if 'Sent Status' is empty or 'No'.
    """
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            status = row.get("Sent Status", "").strip().lower()
            if status in ("", "no"):
                row["_row_index"] = idx
                return row
    return None


def get_next_batch(csv_path: str, batch_size: int = 15) -> list[dict]:
    """
    Return up to `batch_size` unsent leads from the CSV.
    Each lead dict includes '_row_index' for marking as sent later.
    """
    batch = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            status = row.get("Sent Status", "").strip().lower()
            if status in ("", "no"):
                row["_row_index"] = idx
                batch.append(row)
                if len(batch) >= batch_size:
                    break
    return batch


def mark_as_sent(csv_path: str, row_index: int) -> None:
    """
    Update the given row in the CSV: set 'Sent Status' to 'Yes'
    and 'Sent Time' to the current UTC timestamp.
    """
    rows = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    if row_index < 0 or row_index >= len(rows):
        raise IndexError(f"Row index {row_index} out of range (total: {len(rows)})")

    rows[row_index]["Sent Status"] = "Yes"
    rows[row_index]["Sent Time"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  📝 CSV updated — row {row_index} marked as sent.")
