# 🚀 JobHunt Autopilot

AI-driven cold-emailing automation that generates hyper-personalized job pitches and sends them on autopilot via GitHub Actions.

## How It Works

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Read CSV    │ →  │ AI Generates │ →  │ Send Email   │ →  │ Sync to      │
│  (1 lead)    │    │ Pitch        │    │ via Gmail    │    │ GitHub       │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

**Drip Mode**: Processes exactly **one unsent lead per run**. GitHub Actions triggers every 20 minutes, so your outreach stays natural and avoids spam filters.

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USER/JobPitch.git
cd JobPitch
pip install -r requirements.txt
```

### 2. Configure Secrets

Copy the example env file and fill in your details:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | Get one at [openrouter.ai](https://openrouter.ai) |
| `SMTP_EMAIL` | Your Gmail address |
| `SMTP_PASSWORD` | Gmail App Password ([guide](https://support.google.com/accounts/answer/185833)) |
| `GH_TOKEN` | GitHub Personal Access Token with `repo` scope |
| `GITHUB_REPO` | Format: `owner/repo` |
| `SENDER_NAME` | Your full name |
| `SENDER_PHONE` | Your phone number |
| `SENDER_LINKEDIN` | Your LinkedIn URL |
| `SENDER_PORTFOLIO` | Your portfolio URL |

### 3. Add Your Leads

Edit `jobs_database.csv`:

```csv
Company Name,Contact Email,Role,Context/JD,Why I Love Them,Sent Status,Sent Time
Acme Corp,hr@acme.com,ML Engineer,"Building recommendation systems...",I loved their new feature release,No,
```

> **Pro tip**: The "Why I Love Them" column is your secret weapon. Even one specific sentence like *"I used their app last week and loved the new UI"* makes the AI write an opening line that feels deeply researched.

### 4. Run Locally

```bash
python main.py
```

### 5. Enable Autopilot (GitHub Actions)

1. Push your repo to GitHub.
2. Go to **Settings → Secrets and variables → Actions**.
3. Add all secrets from the table above.
4. The workflow runs every 20 minutes automatically, or trigger it manually from the **Actions** tab.

## Project Structure

```
JobPitch/
├── main.py                 # CLI entry point
├── src/
│   ├── agent.py            # AI pitch generation (OpenRouter + 402 fallback)
│   ├── mailer.py           # Gmail SMTP sender with signature
│   ├── processor.py        # CSV lead management (drip mode)
│   └── git_util.py         # GitHub API sync
├── jobs_database.csv       # Your lead database
├── .env.example            # Secrets template
├── .github/workflows/
│   └── job_hunt.yml        # GitHub Actions cron workflow
├── requirements.txt
└── README.md
```

## Safety Features

- **402 Fallback**: If OpenRouter returns "Insufficient Credits", the agent automatically retries with a smaller token budget (up to 3 attempts).
- **Drip Mode**: Only one email per run — no accidental mass-sends.
- **Secret Verification**: The GitHub Actions workflow fails fast if any secret is missing.
- **Non-fatal GitHub sync**: If the GitHub push fails, the email is still sent and the CSV is still updated locally.

## License

MIT
