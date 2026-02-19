"""
agent.py — Dynamic Pitch Agent
Generates hyper-personalized job pitches using Google Gemini API (free tier).
Free tier: 15 RPM, 1500 requests/day — more than enough for batch mode.
"""

import os
import time
import requests


class Agent:
    """AI Agent that generates personalized cold-email pitches."""

    GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    MAX_RETRIES = 5

    def __init__(self, company_name: str, role: str, jd_snippet: str,
                 value_add: str, why_i_love_them: str = ""):
        self.company_name = company_name
        self.role = role
        self.jd_snippet = jd_snippet
        self.value_add = value_add
        self.why_i_love_them = why_i_love_them
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.sender_name = os.getenv("SENDER_NAME", "Mohammad Hussain")

    def _build_prompt(self) -> str:
        system_rules = (
            f"You are a professional career coach writing cold emails on behalf of {self.sender_name}. "
            "Rules you MUST follow:\n"
            "1. Output ONLY plain text — absolutely NO markdown, no bold, no bullet points, no asterisks.\n"
            "2. The first line must be the subject line in the format: Subject: <subject text>\n"
            "3. Then leave one blank line and write the email body.\n"
            "4. NEVER use placeholders like [Your Name], [Company Name], [Role], etc. "
            "Use the actual values provided.\n"
            "5. Keep the tone professional yet warm — like a real human wrote it.\n"
            "6. The email must be concise (under 200 words for the body).\n"
            "7. Do NOT include a signature block — it will be appended separately.\n"
            "8. End the body with a brief, confident call to action.\n"
        )

        task = f"\nWrite a cold email to {self.company_name} for the role of {self.role}."
        task += f"\nJob description snippet: {self.jd_snippet}"
        task += f"\nMy unique value add: {self.value_add}"

        if self.why_i_love_them:
            task += (
                f"\nPersonal connection / why I love them: {self.why_i_love_them} "
                "(Weave this naturally into the opening line to show genuine interest.)"
            )

        task += f"\nThe sender's name is {self.sender_name}. Use it in the sign-off."

        return system_rules + task

    def generate_pitch(self) -> dict:
        """
        Call Google Gemini to generate a pitch email.
        Returns {"subject": str, "body": str}.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        url = f"{self.GEMINI_URL}?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": self._build_prompt()}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 600,
            },
        }

        for attempt in range(1, self.MAX_RETRIES + 1):
            print(f"  🤖 Attempt {attempt}/{self.MAX_RETRIES} (Gemini Flash)...")

            try:
                response = requests.post(url, json=payload, timeout=60)
            except requests.exceptions.Timeout:
                print(f"  ⏰ Timed out, retrying...")
                continue

            if response.status_code == 429:
                wait = 15 * attempt
                print(f"  ⏳ Rate limited — waiting {wait}s...")
                time.sleep(wait)
                continue

            if response.status_code >= 400:
                print(f"  ⚠️  HTTP {response.status_code}: {response.text[:200]}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(10)
                    continue
                response.raise_for_status()

            data = response.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"  ✅ Pitch generated (Gemini Flash)")
            return self._parse_pitch(raw_text)

        raise RuntimeError(
            f"Failed to generate pitch after {self.MAX_RETRIES} retries."
        )

    @staticmethod
    def _parse_pitch(raw_text: str) -> dict:
        """Split the raw AI output into subject and body."""
        lines = raw_text.split("\n", 1)
        subject = ""
        body = raw_text

        if lines[0].lower().startswith("subject:"):
            subject = lines[0].split(":", 1)[1].strip()
            body = lines[1].strip() if len(lines) > 1 else ""

        # Safety: strip any residual markdown artifacts
        body = body.replace("**", "").replace("*", "").replace("#", "")

        return {"subject": subject, "body": body}
