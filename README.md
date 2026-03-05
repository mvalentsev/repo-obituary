# 🪦 repo-obituary

> *A heartfelt farewell to your abandoned GitHub repository.*

Every repository deserves a proper goodbye.

```
                     🪦  R . I . P .  🪦

                      kennethreitz/legit
        Git for Humans, Inspired by GitHub for Mac(tm).

  ────────────────────────────────────────────────────────
  Born:   2011-06-25   Died:   2023-09-15  (2 years ago)
  Age:    12 years, 2 months
  Lang:   Python
  ────────────────────────────────────────────────────────
  5699 stars   215 forks   7 open issues
  ────────────────────────────────────────────────────────
  Cause of death:
    Died trying to fix one last bug

  Last words:
    "Merge pull request #275 from frostming/clint-182"

  ────────────────────────────────────────────────────────
  Epitaph:
    Stars acquired: 5,699. World changed: debatable.

```
*(real output includes colors)*

## Usage

```bash
# Basic usage
python obituary.py owner/repo

# With GitHub token (avoids rate limits)
GITHUB_TOKEN=your_token python obituary.py owner/repo

# Force obituary even for recently active repos
python obituary.py owner/repo --force
```

No dependencies. Pure Python 3.10+.

## How it works

1. Fetches repo metadata via GitHub API (stars, forks, language, dates, open issues)
2. Reads the last 10 commit messages to determine cause of death
3. Generates a randomized epitaph
4. Prints a tombstone with colors

## Cause of death detection

| Keyword in commits | Cause |
|---|---|
| `refactor` | died during an ambitious refactor that was 'almost done' |
| `rewrite` | perished mid-rewrite, half the old code gone, half the new unwritten |
| `wip` | abandoned mid-development, dreams still in the branch |
| `fix` | died trying to fix one last bug |
| `todo` | buried under an avalanche of TODOs |
| `merge` | lost in a merge conflict that nobody resolved |
| `revert` | reverted into oblivion |
| `initial commit` | never made it past the initial commit |
| `cleanup` | cleaned up so hard it no longer existed |
| `experiment` | remained an experiment until the very end |
| `test` | died writing tests that were never green |
| `draft` | marked as draft and never un-drafted |
| *(none matched)* | author got a real job / vibe shifted / replaced by a ChatGPT wrapper / … |

## Examples

```bash
python obituary.py kennethreitz/legit
python obituary.py nicowillis/pickledb
python obituary.py torvalds/uemacs
```

## Requirements

- Python 3.10+
- GitHub token recommended (optional, but avoids rate limiting)

Set `GITHUB_TOKEN` env var or pass `--token`.

---

*"Here lies a project that promised to change the world and settled for the stars it got."*

## Contributing

Found a better epitaph? A funnier cause of death? PRs welcome.
