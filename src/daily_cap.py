"""
daily_cap.py — Daily Email Cap Tracker
Tracks how many emails have been sent today using CSV timestamps.
Auto-resets when the UTC date changes.
"""

import csv
from datetime import datetime, timezone


def get_sent_today(csv_path: str) -> int:
    """
    Count how many emails were sent today (UTC) by checking Sent Time
    in the CSV.  This works across ephemeral GitHub Actions runners
    because it relies on the committed CSV, not local state.
    """
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    count = 0

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sent_time = row.get("Sent Time", "").strip()
            if sent_time.startswith(today_str):
                count += 1

    return count


def remaining_today(csv_path: str, daily_limit: int = 450) -> int:
    """Return how many more emails can be sent today."""
    sent = get_sent_today(csv_path)
    return max(0, daily_limit - sent)
