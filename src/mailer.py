"""
mailer.py — SMTP Email Sender
Sends plain-text emails via Gmail SMTP with App Passwords.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def _build_signature() -> str:
    """Build a professional plain-text signature from env vars."""
    name = os.getenv("SENDER_NAME", "Mohammad Hussain")
    phone = os.getenv("SENDER_PHONE", "")
    linkedin = os.getenv("SENDER_LINKEDIN", "")
    portfolio = os.getenv("SENDER_PORTFOLIO", "")

    sig_lines = [
        "",
        "---",
        name,
    ]
    if phone:
        sig_lines.append(f"Phone: {phone}")
    if linkedin:
        sig_lines.append(f"LinkedIn: {linkedin}")
    if portfolio:
        sig_lines.append(f"Portfolio: {portfolio}")

    return "\n".join(sig_lines)


def send_email(to: str, subject: str, body: str) -> None:
    """
    Send a plain-text email via Gmail SMTP.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body (plain text, no markdown).
    """
    smtp_email = os.getenv("SMTP_EMAIL", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")

    if not smtp_email or not smtp_password:
        raise ValueError(
            "SMTP_EMAIL and SMTP_PASSWORD must be set in environment."
        )

    # Append the professional signature
    full_body = body + "\n" + _build_signature()

    msg = MIMEMultipart()
    msg["From"] = smtp_email
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(full_body, "plain"))

    print(f"  📧 Connecting to Gmail SMTP...")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, to, msg.as_string())

    print(f"  ✅ Email sent successfully to {to}")
