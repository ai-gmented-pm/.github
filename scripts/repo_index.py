#!/usr/bin/env python3
"""Generate the repository index shown on the organisation profile.

Reads every repository of the given owners through the GitHub CLI (`gh`),
renders one Markdown table (one row per repository: name, description, owner,
visibility, access of the account that generated the index, date of the last push) and writes it to
the output file. Archived repositories go to a collapsed section at the end.

The output is generated: never edit it by hand, run this script instead.

    python3 scripts/repo_index.py --out profile/README.md
    python3 scripts/repo_index.py --include-private --out ../.github-private/profile/README.md

Authentication comes from `gh` (local login, or GH_TOKEN in a workflow). A
fine-grained token reaches one owner only, so an owner can have a token of its
own in REPO_INDEX_TOKEN_<OWNER> (upper case, `-` and `.` as `_`), used for
that owner instead of GH_TOKEN. The "Access" column is the permission of the
account behind the token on each repository; it is empty when unknown.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

DEFAULT_OWNERS = ("ai-gmented-pm", "romain-nicod")
FIELDS = (
    "name,nameWithOwner,description,visibility,isArchived,isFork,isTemplate,"
    "url,viewerPermission,pushedAt"
)
SCRIPT_URL = "https://github.com/ai-gmented-pm/.github/blob/main/scripts/repo_index.py"

ICONS = {"PUBLIC": "🌐", "PRIVATE": "🔒", "INTERNAL": "🏢"}
ACCESS = {
    "ADMIN": "Admin",
    "MAINTAIN": "Maintain",
    "WRITE": "Write",
    "TRIAGE": "Triage",
    "READ": "Read",
}


def fetch(owner: str) -> list[dict]:
    """Return the repositories of `owner` as `gh repo list --json` gives them."""
    cmd = ["gh", "repo", "list", owner, "--limit", "500", "--json", FIELDS]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True, env=owner_env(owner)).stdout
    return json.loads(out)


def owner_env(owner: str) -> dict[str, str]:
    """Environment for `gh`: the owner's own token when one is set, else unchanged."""
    env = dict(os.environ)
    token = env.get("REPO_INDEX_TOKEN_" + re.sub(r"[^A-Za-z0-9]", "_", owner).upper())
    if token:
        env["GH_TOKEN"] = token
    return env


def select(repos: list[dict], include_private: bool) -> list[dict]:
    if include_private:
        return list(repos)
    return [r for r in repos if r["visibility"] == "PUBLIC"]


def cell(text: str | None) -> str:
    """Escape a value for a Markdown table cell."""
    return (text or "—").replace("|", "\\|").replace("\n", " ").strip()


def row(repo: dict) -> str:
    icon = ICONS.get(repo["visibility"], "📦")
    name = f"{icon} [{repo['name']}]({repo['url']})"
    tags = []
    if repo.get("isTemplate"):
        tags.append("template")
    if repo.get("isFork"):
        tags.append("fork")
    if tags:
        name += " · " + ", ".join(tags)
    owner = repo["nameWithOwner"].split("/")[0]
    visibility = repo["visibility"].capitalize()
    access = ACCESS.get(repo.get("viewerPermission") or "", "—")
    updated = (repo.get("pushedAt") or "")[:10] or "—"
    return f"| {name} | {cell(repo.get('description'))} | {owner} | {visibility} | {access} | {updated} |"


def table(repos: list[dict]) -> str:
    head = "| Repository | What it is | Owner | Visibility | Access | Updated |\n|---|---|---|---|---|---|"
    return "\n".join([head] + [row(r) for r in repos])


def sort_key(repo: dict):
    owner = repo["nameWithOwner"].split("/")[0]
    return (DEFAULT_OWNERS.index(owner) if owner in DEFAULT_OWNERS else 99, repo["name"].lower())


def render(repos: list[dict], *, today: dt.date, include_private: bool) -> str:
    live = sorted((r for r in repos if not r["isArchived"]), key=sort_key)
    archived = sorted((r for r in repos if r["isArchived"]), key=sort_key)
    public = sum(1 for r in repos if r["visibility"] == "PUBLIC")
    private = len(repos) - public
    scope = "every repository" if include_private else "every public repository"
    counts = f"{len(repos)} repositories: {public} public, {private} private, {len(archived)} archived"
    if not include_private:
        counts = f"{len(repos)} public repositories, {len(archived)} of them archived"
    lines = [
        "## Repositories",
        "",
        f"_{scope.capitalize()} behind AI-GMENTED PM, on this organisation and on the personal "
        f"account [romain-nicod](https://github.com/romain-nicod). {counts}. "
        f"Generated on {today.isoformat()} by [`repo_index.py`]({SCRIPT_URL}); "
        "edits by hand are overwritten. Access is the permission of the account that generated the index, "
        "Updated the date of the last push._",
        "",
        table(live),
    ]
    if archived:
        lines += [
            "",
            "<details>",
            f"<summary>Archived ({len(archived)})</summary>",
            "",
            table(archived),
            "",
            "</details>",
        ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--owner", action="append", help="owner to index (repeatable)")
    parser.add_argument("--include-private", action="store_true", help="list private repositories too")
    parser.add_argument("--out", required=True, help="Markdown file to write")
    args = parser.parse_args(argv)
    owners = args.owner or list(DEFAULT_OWNERS)

    repos: list[dict] = []
    for owner in owners:
        repos += fetch(owner)
    chosen = select(repos, args.include_private)
    missing = sorted(r["nameWithOwner"] for r in chosen if not r.get("description"))
    if missing:
        print("without a description (fix it on GitHub):", ", ".join(missing), file=sys.stderr)

    text = render(chosen, today=dt.date.today(), include_private=args.include_private)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"{args.out}: {len(chosen)} repositories from {', '.join(owners)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
