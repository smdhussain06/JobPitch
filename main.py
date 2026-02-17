#!/usr/bin/env python3
"""
main.py — JobHunt Autopilot (Batch Mode)
Processes up to 15 unsent leads per run with a 2-min drip delay,
enforces a 450/day cap, then syncs the CSV to GitHub once.
"""

import os
import sys
import time
from dotenv import load_dotenv

from src.agent import Agent
from src.mailer import send_email
from src.processor import get_next_batch, mark_as_sent
from src.daily_cap import remaining_today
from src.git_util import sync_csv_to_github


CSV_PATH = os.path.join(os.path.dirname(__file__), "jobs_database.csv")

# ── Configuration ─────────────────────────────────────────
BATCH_SIZE = 15          # emails per run
DAILY_CAP = 450          # auto-resets next UTC day
DRIP_DELAY = 120         # seconds between emails (2 min)


def main():
    load_dotenv()

    print("=" * 60)
    print("  🚀 JobHunt Autopilot — Batch Mode")
    print("=" * 60)
    print(f"  ⚙️  Batch Size : {BATCH_SIZE}")
    print(f"  ⚙️  Daily Cap  : {DAILY_CAP}")
    print(f"  ⚙️  Drip Delay : {DRIP_DELAY}s ({DRIP_DELAY // 60} min)")

    # ── Step 1: Check daily cap ──────────────────────────────
    print("\n📊 Step 1: Checking daily cap...")
    cap_remaining = remaining_today(CSV_PATH, DAILY_CAP)
    print(f"  📈 Emails remaining today: {cap_remaining}")

    if cap_remaining <= 0:
        print("  🛑 Daily cap reached (450). Stopping — will auto-reset tomorrow.")
        sys.exit(0)

    # ── Step 2: Fetch batch of unsent leads ──────────────────
    print(f"\n📋 Step 2: Fetching next batch (up to {BATCH_SIZE})...")
    batch = get_next_batch(CSV_PATH, batch_size=BATCH_SIZE)

    if not batch:
        print("  ℹ️  No unsent leads remaining. Nothing to do.")
        sys.exit(0)

    # Clamp to daily cap
    if len(batch) > cap_remaining:
        print(f"  ⚠️  Clamping batch from {len(batch)} → {cap_remaining} (daily cap)")
        batch = batch[:cap_remaining]

    print(f"  🎯 Processing {len(batch)} leads this run")

    # ── Step 3: Drip-send the batch ──────────────────────────
    print(f"\n📧 Step 3: Sending emails (2-min drip delay between each)...")
    sent_count = 0

    value_add = os.getenv(
        "MY_VALUE_ADD",
        "I bring strong skills in AI/ML, data science, and full-stack "
        "development with a passion for building impactful products."
    )

    for i, lead in enumerate(batch):
        company = lead["Company Name"]
        email = lead["Contact Email"]
        role = lead["Role"]
        jd = lead.get("Context/JD", "")
        why = lead.get("Why I Love Them", "")
        row_idx = lead["_row_index"]

        print(f"\n  ── [{i + 1}/{len(batch)}] {company} — {role} ──")
        print(f"     📬 To: {email}")

        try:
            # Generate AI pitch
            print(f"     🤖 Generating pitch...")
            agent = Agent(
                company_name=company,
                role=role,
                jd_snippet=jd,
                value_add=value_add,
                why_i_love_them=why,
            )
            pitch = agent.generate_pitch()
            print(f"     📌 Subject: {pitch['subject']}")

            # Send email
            print(f"     📧 Sending...")
            send_email(to=email, subject=pitch["subject"], body=pitch["body"])
            print(f"     ✅ Sent!")

            # Mark as sent in CSV
            mark_as_sent(CSV_PATH, row_idx)
            sent_count += 1

        except Exception as e:
            print(f"     ❌ Failed: {e}")
            print(f"     ⏭️  Skipping to next lead...")
            continue

        # Drip delay (skip after the last email)
        if i < len(batch) - 1:
            print(f"     ⏳ Waiting {DRIP_DELAY}s before next email...")
            time.sleep(DRIP_DELAY)

    # ── Step 4: Sync to GitHub (once) ────────────────────────
    if sent_count > 0:
        print(f"\n🔄 Step 4: Syncing CSV to GitHub...")
        try:
            sync_csv_to_github(
                CSV_PATH,
                commit_msg=f"chore: batch update — {sent_count} emails sent",
            )
            print(f"  ✅ GitHub Synced!")
        except Exception as e:
            print(f"  ⚠️  GitHub sync failed (non-fatal): {e}")
            print(f"     Emails were still sent and CSV updated locally.")
    else:
        print("\n⚠️  No emails were sent this run — skipping GitHub sync.")

    # ── Done ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  🎉 Batch complete! Sent {sent_count}/{len(batch)} emails.")
    print(f"  📊 Daily remaining: ~{cap_remaining - sent_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
