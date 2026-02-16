#!/usr/bin/env python3
"""
main.py — JobHunt Autopilot
Processes one unsent lead per run: generates an AI pitch, sends it,
updates the CSV, and syncs to GitHub.
"""

import os
import sys
from dotenv import load_dotenv

from src.agent import Agent
from src.mailer import send_email
from src.processor import get_next_lead, mark_as_sent
from src.git_util import sync_csv_to_github


CSV_PATH = os.path.join(os.path.dirname(__file__), "jobs_database.csv")


def main():
    load_dotenv()

    print("=" * 60)
    print("  🚀 JobHunt Autopilot — Drip Mode")
    print("=" * 60)

    # ── Step 1: Find the next unsent lead ────────────────────
    print("\n📋 Step 1: Scanning for next unsent lead...")
    lead = get_next_lead(CSV_PATH)

    if lead is None:
        print("  ℹ️  No unsent leads remaining. Nothing to do.")
        sys.exit(0)

    company = lead["Company Name"]
    email = lead["Contact Email"]
    role = lead["Role"]
    jd = lead.get("Context/JD", "")
    why = lead.get("Why I Love Them", "")
    row_idx = lead["_row_index"]

    print(f"  🎯 Target: {company} — {role}")
    print(f"  📬 Contact: {email}")

    # ── Step 2: Generate the AI pitch ────────────────────────
    print("\n🤖 Step 2: Generating AI pitch...")

    value_add = os.getenv(
        "MY_VALUE_ADD",
        "I bring strong skills in AI/ML, data science, and full-stack "
        "development with a passion for building impactful products."
    )

    agent = Agent(
        company_name=company,
        role=role,
        jd_snippet=jd,
        value_add=value_add,
        why_i_love_them=why,
    )

    pitch = agent.generate_pitch()
    print(f"  ✅ Pitch Generated!")
    print(f"  📌 Subject: {pitch['subject']}")

    # ── Step 3: Send the email ───────────────────────────────
    print("\n📧 Step 3: Sending email...")
    send_email(to=email, subject=pitch["subject"], body=pitch["body"])
    print(f"  ✅ Email Sent!")

    # ── Step 4: Update the CSV ───────────────────────────────
    print("\n📝 Step 4: Updating CSV...")
    mark_as_sent(CSV_PATH, row_idx)
    print(f"  ✅ CSV Updated!")

    # ── Step 5: Sync to GitHub ───────────────────────────────
    print("\n🔄 Step 5: Syncing CSV to GitHub...")
    try:
        sync_csv_to_github(CSV_PATH)
        print(f"  ✅ GitHub Synced!")
    except Exception as e:
        print(f"  ⚠️  GitHub sync failed (non-fatal): {e}")
        print(f"     The email was still sent and CSV updated locally.")

    # ── Done ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  🎉 Done! Pitched {company} for {role}.")
    print("=" * 60)


if __name__ == "__main__":
    main()
