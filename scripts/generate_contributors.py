#!/usr/bin/env python3

import json
import os
import sys
import urllib.request


API_ROOT = "https://api.github.com"


def request_json(url, token=None):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
            "User-Agent": "GoClub-Contributors-Generator",
        },
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_all_merged_prs(repo, token=None):
    page = 1
    merged = []

    while True:
        url = f"{API_ROOT}/repos/{repo}/pulls?state=closed&per_page=100&page={page}"
        items = request_json(url, token=token)
        if not items:
            break

        for item in items:
            if item.get("merged_at") and item.get("user"):
                merged.append(item)

        if len(items) < 100:
            break

        page += 1

    return merged


def build_contributors(prs):
    grouped = {}

    for pr in prs:
        user = pr["user"]
        login = user["login"]
        current = grouped.setdefault(
            login,
            {
                "login": login,
                "html_url": user["html_url"],
                "avatar_url": user["avatar_url"],
                "name": None,
                "merged_prs": 0,
            },
        )
        current["merged_prs"] += 1

    return sorted(grouped.values(), key=lambda item: (-item["merged_prs"], item["login"].lower()))


def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip() or None
    output = os.environ.get("CONTRIBUTORS_OUTPUT", "data/contributors.json")

    if not repo:
        print("Missing GITHUB_REPOSITORY", file=sys.stderr)
        sys.exit(1)

    prs = fetch_all_merged_prs(repo, token=token)
    contributors = build_contributors(prs)

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(contributors, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote {len(contributors)} contributors to {output}")


if __name__ == "__main__":
    main()
