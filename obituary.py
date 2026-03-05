#!/usr/bin/env python3
"""
repo-obituary: A heartfelt farewell to your abandoned GitHub repository.
"""

import sys
import re
import json
import urllib.request
import urllib.error
import os
import random
from datetime import datetime, timezone

# ── Cause-of-death heuristics (matched against last commit messages) ──────────
COMMIT_CAUSES = {
    "refactor":       "died during an ambitious refactor that was 'almost done'",
    "rewrite":        "perished mid-rewrite, half the old code gone, half the new unwritten",
    "wip":            "abandoned mid-development, dreams still in the branch",
    "fix":            "died trying to fix one last bug",
    "todo":           "buried under an avalanche of TODOs",
    "update dep":     "dependency-updated into incompatibility",
    "bump":           "versioned itself into irrelevance",
    "merge":          "lost in a merge conflict that nobody resolved",
    "revert":         "reverted into oblivion",
    "initial commit": "never made it past the initial commit",
    "cleanup":        "cleaned up so hard it no longer existed",
    "experiment":     "remained an experiment until the very end",
    "test":           "died writing tests that were never green",
    "draft":          "marked as draft and never un-drafted",
}

FALLBACK_CAUSES = [
    "author got a real job",
    "died of feature creep",
    "replaced by a ChatGPT wrapper",
    "overwhelmed by scope",
    "maintainer discovered touch grass",
    "the README was never finished",
    "vibe shifted",
    "pivoted to blockchain, then pivoted away",
    "open issues outnumbered the stars",
    "motivation left the building",
    "suffered a fatal case of 'I'll finish it later'",
]

EPITAPHS = [
    "Here lies a project that promised to change the world\nand settled for {stars} stars.",
    "It compiled once. It was beautiful.",
    "Gone too soon. Or maybe right on time.\nWe'll never know.",
    "Stars acquired: {stars}. World changed: debatable.",
    "The last commit message said '{last_msg}'.\nNobody came after.",
    "Survived by {open_issues} open issues\nand the eternal question: 'is this still maintained?'",
    "It had potential. We all said so.",
    "The README was always 'work in progress'.",
    "A brave soul, felled by real life.",
    "In loving memory. PRs no longer accepted.",
]

# ── ANSI colours ──────────────────────────────────────────────────────────────
GRAY   = "\033[90m"
WHITE  = "\033[97m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RED    = "\033[91m"
DIM    = "\033[2m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)


def center_ansi(s: str, width: int) -> str:
    """Center a string that may contain ANSI codes, based on visible length."""
    visible = len(strip_ansi(s))
    pad = max(width - visible, 0)
    left = pad // 2
    right = pad - left
    return " " * left + s + " " * right


def gh_api(path: str, token: str | None) -> dict | list:
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        print(f"{RED}GitHub API error {e.code}: {body.get('message', '?')}{RESET}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"{RED}Network error: {e.reason}{RESET}", file=sys.stderr)
        sys.exit(1)


def age_string(created: str, died: str) -> str:
    """Return human-readable project lifespan (birth to last commit)."""
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    birth = datetime.strptime(created, fmt).replace(tzinfo=timezone.utc)
    death = datetime.strptime(died, fmt).replace(tzinfo=timezone.utc)
    delta = death - birth
    years  = delta.days // 365
    months = (delta.days % 365) // 30
    days   = delta.days
    if years > 0:
        return f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''}"
    if months > 0:
        return f"{months} month{'s' if months != 1 else ''}"
    return f"{days} day{'s' if days != 1 else ''}"


def since_death(died: str) -> str:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    death = datetime.strptime(died, fmt).replace(tzinfo=timezone.utc)
    now   = datetime.now(timezone.utc)
    years = (now - death).days // 365
    months = ((now - death).days % 365) // 30
    days  = (now - death).days
    if years > 0:
        return f"{years} year{'s' if years != 1 else ''} ago"
    if months > 0:
        return f"{months} month{'s' if months != 1 else ''} ago"
    return f"{days} day{'s' if days != 1 else ''} ago"


def is_dead(last_commit: str, threshold_days: int = 365) -> bool:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    death = datetime.strptime(last_commit, fmt).replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - death).days >= threshold_days


def pick_cause(commits: list) -> str:
    messages = " ".join(c["commit"]["message"].lower() for c in commits[:10])
    for keyword, cause in COMMIT_CAUSES.items():
        if keyword in messages:
            return cause
    return random.choice(FALLBACK_CAUSES)


def truncate(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[:max_len - 1] + "…"


def print_obituary(repo: str, token: str | None, force: bool = False):
    print(f"{DIM}Fetching data for {repo}...{RESET}", file=sys.stderr)

    data    = gh_api(f"/repos/{repo}", token)
    commits = gh_api(f"/repos/{repo}/commits?per_page=10", token)

    name        = data["full_name"]
    stars       = data["stargazers_count"]
    forks       = data["forks_count"]
    language    = data.get("language") or "unknown language"
    created     = data["created_at"]
    open_issues = data["open_issues_count"]  # from repo metadata, no extra API call
    description = data.get("description") or ""

    if not commits:
        print(f"{RED}No commits found.{RESET}", file=sys.stderr)
        sys.exit(1)

    last_commit  = commits[0]["commit"]["author"]["date"]
    last_msg_raw = commits[0]["commit"]["message"].split("\n")[0]
    last_msg     = truncate(last_msg_raw, 60)

    if not force and not is_dead(last_commit):
        print(f"{YELLOW}⚠  This repo had activity in the last year. Use --force to generate anyway.{RESET}")
        sys.exit(0)

    cause = pick_cause(commits)
    age   = age_string(created, last_commit)
    gone  = since_death(last_commit)
    born  = created[:10]
    died  = last_commit[:10]

    epitaph = (
        random.choice(EPITAPHS)
        .replace("{stars}", f"{stars:,}")
        .replace("{last_msg}", last_msg)
        .replace("{open_issues}", str(open_issues))
    )

    W = 60
    SEP = GRAY + "─" * W + RESET

    def row(label: str, value: str) -> str:
        return f"  {GRAY}{label}{RESET}  {value}"

    lines = [
        "",
        center_ansi(f"{BOLD}{WHITE}🪦  R . I . P .  🪦{RESET}", W),
        "",
        center_ansi(f"{BOLD}{CYAN}{name}{RESET}", W),
    ]
    if description:
        lines.append(center_ansi(f"{DIM}{truncate(description, W)}{RESET}", W))
    lines += [
        "",
        SEP,
        row("Born:  ", f"{born}   {GRAY}Died:{RESET}  {died}  {DIM}({gone}){RESET}"),
        row("Age:   ", age),
        row("Lang:  ", language),
        SEP,
        f"  {YELLOW}⭐ {stars:,} stars{RESET}   {GRAY}🍴 {forks:,} forks{RESET}   {RED}🐛 {open_issues} open issues{RESET}",
        SEP,
        f"  {BOLD}Cause of death:{RESET}",
        f"  {RED}  {cause.capitalize()}{RESET}",
        "",
        f"  {BOLD}Last words:{RESET}",
        f"  {DIM}  \"{last_msg}\"{RESET}",
        "",
        SEP,
        f"  {DIM}{BOLD}Epitaph:{RESET}",
        *[f"  {DIM}  {line.strip()}{RESET}" for line in epitaph.split("\n")],
        "",
    ]

    print()
    for line in lines:
        print(line)
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate a heartfelt obituary for your abandoned GitHub repository.",
        epilog="Example: obituary.py torvalds/uemacs",
    )
    parser.add_argument("repo", help="owner/repo")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token (or set GITHUB_TOKEN)")
    parser.add_argument("--force", action="store_true", help="Generate even for active repos")
    args = parser.parse_args()

    if "/" not in args.repo:
        print(f"{RED}Error: repo must be in owner/repo format{RESET}", file=sys.stderr)
        sys.exit(1)

    print_obituary(args.repo, args.token, args.force)


if __name__ == "__main__":
    main()
