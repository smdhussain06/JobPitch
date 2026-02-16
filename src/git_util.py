"""
git_util.py — GitHub API Sync
Pushes the updated CSV back to the GitHub repo so you can track
application status from your phone.
"""

import os
import base64
import requests


def sync_csv_to_github(
    csv_path: str,
    repo: str = "",
    branch: str = "main",
    commit_msg: str = "chore: update jobs_database.csv — lead sent",
) -> None:
    """
    Upload the CSV to GitHub using the REST API (Contents endpoint).

    Args:
        csv_path: Local path to the CSV file.
        repo: GitHub repo in 'owner/repo' format. Falls back to GITHUB_REPO env.
        branch: Target branch (default: main).
        commit_msg: Commit message.
    """
    token = os.getenv("GH_TOKEN", "")
    repo = repo or os.getenv("GITHUB_REPO", "")

    if not token:
        raise ValueError("GH_TOKEN is not set.")
    if not repo:
        raise ValueError("GITHUB_REPO is not set (expected format: owner/repo).")

    file_name = os.path.basename(csv_path)
    api_url = f"https://api.github.com/repos/{repo}/contents/{file_name}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Step 1: Get the current file SHA (required for updates)
    print(f"  🔍 Fetching current SHA for {file_name}...")
    get_resp = requests.get(api_url, headers=headers, params={"ref": branch}, timeout=30)

    sha = None
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")
    elif get_resp.status_code != 404:
        get_resp.raise_for_status()

    # Step 2: Read and encode the local file
    with open(csv_path, "r", encoding="utf-8") as f:
        content_b64 = base64.b64encode(f.read().encode("utf-8")).decode("utf-8")

    # Step 3: Push the update
    payload = {
        "message": commit_msg,
        "content": content_b64,
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    print(f"  🚀 Pushing {file_name} to {repo}@{branch}...")
    put_resp = requests.put(api_url, headers=headers, json=payload, timeout=30)
    put_resp.raise_for_status()

    print(f"  ✅ GitHub synced — {file_name} updated on {repo}@{branch}")
