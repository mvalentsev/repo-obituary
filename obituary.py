#!/usr/bin/env python3
"""
repo-obituary: A heartfelt farewell to your abandoned GitHub repository.
"""

import sys
import json
import urllib.request
import urllib.error
import os
import random
from datetime import datetime, timezone

# ── Cause-of-death heuristics (matched against last commit messages) ──────────
COMMIT_CAUSES = {
    "refactor":  "died during an ambitious refactor that was 'almost done'",
    "rewrite":   "perished mid-rewrite, half the old code gone, half the new unwritten",
    "wip":        "abandoned mid-development, dreams still in the branch",
    "fix":        "died trying to fix one last bug",
    "todo":       "buried under an avalanche of TODOs",
    "update dep": "dependency-updated into incompatibility",
    "bump":       "versioned itself into irrelevance",
    "merge":      "lost in a merge conflict that nobody resolved",
    "revert":     "reverted into oblivion",
    "initial commit": "never made it past the initial commit",
    "cleanup":    "cleaned up so hard it no longer existed",
    "experiment": "remained an experiment until the very end",
    "test":       "died writing tests that were never green",
    "draft":      "marked as draft and never un-drafted",
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
    "The last commit message said '{last_msg}'.\n    Nobody came after.",
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


def gh_api(path: str, token: str | None) -> dict:
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


def age_string(created: str, died: str) -> str:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    birth = datetime.strptime(created, fmt)
    death = datetime.strptime(died, fmt)
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


def pick_cause(commits: list) -> str:
    messages = " ".join(c["commit"]["message"].lower() for c in commits[:10])
    for keyword, cause in COMMIT_CAUSES.items():
        if keyword in messages:
            return cause
    return random.choice(FALLBACK_CAUSES)


def is_dead(last_commit: str, threshold_days: int = 365) -> bool:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    death = datetime.strptime(last_commit, fmt).replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - death).days >= threshold_days


def box(lines: list[str], width: int = 60) -> str:
    top    = "╔" + "═" * (width - 2) + "╗"
    bottom = "╚" + "═" * (width - 2) + "╝"
    middle = []
    for line in lines:
        # strip ANSI for length calc
        import re
        plain = re.sub(r"\033\[[0-9;]*m", "", line)
        pad = width - 2 - len(plain)
        middle.append("║ " + line + " " * max(pad - 1, 0) + "║")
    return "\n".join([top] + middle + [bottom])


def print_obituary(repo: str, token: str | None, force: bool = False):
    print(f"{DIM}Fetching data for {repo}...{RESET}", file=sys.stderr)

    data    = gh_api(f"/repos/{repo}", token)
    commits = gh_api(f"/repos/{repo}/commits?per_page=10", token)
    issues  = gh_api(f"/repos/{repo}/issues?state=open&per_page=1", token)

    name         = data["full_name"]
    stars        = data["stargazers_count"]
    forks        = data["forks_count"]
    language     = data.get("language") or "unknown language"
    created      = data["created_at"]
    open_issues  = data["open_issues_count"]
    contributors_url = data.get("contributors_url", "")
    description  = data.get("description") or ""

    if not commits:
        print(f"{RED}No commits found.{RESET}", file=sys.stderr)
        sys.exit(1)

    last_commit     = commits[0]["commit"]["author"]["date"]
    last_msg        = commits[0]["commit"]["message"].split("\n")[0][:60]
    last_msg_full   = commits[0]["commit"]["message"].split("\n")[0]

    if not force and not is_dead(last_commit):
        print(f"{YELLOW}⚠  This repo had activity in the last year. Use --force to generate anyway.{RESET}")
        sys.exit(0)

    cause   = pick_cause(commits)
    age     = age_string(created, last_commit)
    gone    = since_death(last_commit)
    born    = created[:10]
    died    = last_commit[:10]

    # pick epitaph
    epitaph = random.choice(EPITAPHS).format(
        stars=f"{stars:,}",
        last_msg=last_msg,
        open_issues=open_issues,
    )

    W = 62
    SEP = GRAY + "─" * (W - 2) + RESET

    lines = []
    lines.append("")
    lines.append(f"{BOLD}{WHITE}{'🪦  R . I . P .  🪦':^{W}}{RESET}")
    lines.append("")
    lines.append(f"{BOLD}{CYAN}{name:^{W}}{RESET}")
    if description:
        lines.append(f"{DIM}{description[:W]:^{W}}{RESET}")
    lines.append("")
    lines.append(SEP)
    lines.append(f"  {GRAY}Born:{RESET}   {born}     {GRAY}Died:{RESET}   {died}  ({gone})")
    lines.append(f"  {GRAY}Age:{RESET}    {age}")
    lines.append(f"  {GRAY}Lang:{RESET}   {language}")
    lines.append(SEP)
    lines.append(f"  {YELLOW}⭐ {stars:,} stars{RESET}   {GRAY}🍴 {forks:,} forks{RESET}   {RED}🐛 {open_issues} open issues{RESET}")
    lines.append(SEP)
    lines.append(f"  {BOLD}Cause of death:{RESET}")
    lines.append(f"  {RED}  {cause.capitalize()}{RESET}")
    lines.append("")
    lines.append(f"  {BOLD}Last words:{RESET}")
    lines.append(f"  {DIM}  \"{last_msg_full}\"{RESET}")
    lines.append("")
    lines.append(SEP)
    lines.append(f"  {DIM}{BOLD}Epitaph:{RESET}")
    for epi_line in epitaph.split("\n"):
        lines.append(f"  {DIM}{epi_line.strip()}{RESET}")
    lines.append("")

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
