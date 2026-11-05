# .github — the organisation profile of AI-GMENTED PM

This repository holds what GitHub shows on the organisation page
[github.com/ai-gmented-pm](https://github.com/ai-gmented-pm): `profile/README.md`,
an index of every repository behind the practice, on this organisation and on
the personal account [romain-nicod](https://github.com/romain-nicod).

## The index is generated, never edited

`profile/README.md` is written by `scripts/repo_index.py`, which reads the
repositories through the GitHub CLI and renders one table: name, description,
owner, visibility, and the access of the account that generated the index.
Archived repositories sit in a collapsed section at the end.

The workflow `.github/workflows/repo-index.yml` runs it every Monday, on
demand, and when the generator changes, then commits the result when it
differs. It lists public repositories only, so it runs without any secret, on
the token of the workflow. With the repository secret `REPO_INDEX_TOKEN` (a
fine-grained token of `romain-nicod`, *Metadata: read* on all repositories) the
Access column shows that account's permission instead of the workflow's.

The full index, private repositories included, is shown to members of the
organisation only: it lives in `ai-gmented-pm/.github-private`, whose workflow
fetches this generator and runs it with `--include-private`. A fine-grained
token reaches one owner, so that workflow takes two: `REPO_INDEX_TOKEN` for
`romain-nicod` and `REPO_INDEX_TOKEN_ORG` for `ai-gmented-pm` (passed to the
script as `REPO_INDEX_TOKEN_AI_GMENTED_PM`). It never regenerates with a
partial view: when a token is missing it leaves the index as it is.

Run it by hand, logged in with `gh`:

```bash
python3 scripts/repo_index.py --out profile/README.md
```

Tests: `python3 -m unittest discover -s scripts`.

## Licence

MIT, see `LICENSE`. The profile text is © Romain Nicod.
