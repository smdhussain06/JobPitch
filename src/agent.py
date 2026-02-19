"""
agent.py — Dynamic Pitch Agent
Generates hyper-personalized job pitches using OpenRouter AI.
Uses openrouter/auto so OpenRouter picks the best available model.
"""

import os
import json
import time
import requests


class Agent:
    """AI Agent that generates personalized cold-email pitches."""

    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "openrouter/auto"   # Let OpenRouter pick the best available model
    DEFAULT_MAX_TOKENS = 600
    MAX_RETRIES = 5
    TOKEN_REDUCTION_FACTOR = 0.75

    def __init__(self, company_name: str, role: str, jd_snippet: str,
                 value_add: str, why_i_love_them: str = ""):
        self.company_name = company_name
        self.role = role
        self.jd_snippet = jd_snippet
        self.value_add = value_add
        self.why_i_love_them = why_i_love_them
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.sender_name = os.getenv("SENDER_NAME", "Mohammad Hussain")

    def _build_system_prompt(self) -> str:
        return (
            "You are a professional career coach writing cold emails on behalf of "
            f"{self.sender_name}. "
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

    def _build_user_prompt(self) -> str:
        parts = [
            f"Write a cold email to {self.company_name} for the role of {self.role}.",
            f"Job description snippet: {self.jd_snippet}",
            f"My unique value add: {self.value_add}",
        ]
        if self.why_i_love_them:
            parts.append(
                f"Personal connection / why I love them: {self.why_i_love_them} "
                "(Weave this naturally into the opening line to show genuine interest.)"
            )
        parts.append(
            f"The sender's name is {self.sender_name}. Use it in the sign-off."
        )
        return "\n".join(parts)

    def generate_pitch(self) -> dict:
        """
        Call OpenRouter to generate a pitch email.
        Returns {"subject": str, "body": str}.
        Uses openrouter/auto — OpenRouter picks the best available model.
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not set.")

        max_tokens = self.DEFAULT_MAX_TOKENS

        for attempt in range(1, self.MAX_RETRIES + 1):
            print(f"  🤖 Attempt {attempt}/{self.MAX_RETRIES} "
                  f"(model=auto, max_tokens={int(max_tokens)})...")

            payload = {
                "model": self.MODEL,
                "messages": [
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": self._build_user_prompt()},
                ],
                "max_tokens": int(max_tokens),
                "temperature": 0.7,
                "provider": {
                    "data_collection": "allow",
                },
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/JobHuntAutopilot",
                "X-Title": "JobHunt Autopilot",
            }

            try:
                response = requests.post(
                    self.OPENROUTER_URL, headers=headers, json=payload, timeout=60
                )
            except requests.exceptions.Timeout:
                print(f"  ⏰ Request timed out, retrying...")
                continue

            if response.status_code == 402:
                print(f"  ⚠️  402 Insufficient Credits — reducing token budget...")
                max_tokens = int(max_tokens * self.TOKEN_REDUCTION_FACTOR)
                if max_tokens < 100:
                    raise RuntimeError(
                        "Cannot generate pitch: credits exhausted even at "
                        "minimum token count."
                    )
                continue

            if response.status_code == 429:
                wait = 10 * (2 ** (attempt - 1))  # 10s, 20s, 40s...
                print(f"  ⏳ 429 Rate Limited — waiting {wait}s before retry...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json()

            model_used = data.get("model", "unknown")
            raw_text = data["choices"][0]["message"]["content"].strip()
            print(f"  ✅ Pitch generated (routed to: {model_used})")
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
