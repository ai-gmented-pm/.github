import datetime as dt
import os
import unittest
from unittest import mock

import repo_index

FIXTURE = [
    {"name": "zeta", "nameWithOwner": "romain-nicod/zeta", "description": "A | pipe", "visibility": "PRIVATE",
     "isArchived": False, "isFork": False, "isTemplate": False, "url": "https://github.com/romain-nicod/zeta",
     "viewerPermission": "ADMIN", "pushedAt": "2026-11-01T00:00:00Z"},
    {"name": "alpha", "nameWithOwner": "romain-nicod/alpha", "description": None, "visibility": "PUBLIC",
     "isArchived": False, "isFork": False, "isTemplate": True, "url": "https://github.com/romain-nicod/alpha",
     "viewerPermission": None, "pushedAt": "2026-11-01T00:00:00Z"},
    {"name": "old", "nameWithOwner": "ai-gmented-pm/old", "description": "Archived", "visibility": "PRIVATE",
     "isArchived": True, "isFork": True, "isTemplate": False, "url": "https://github.com/ai-gmented-pm/old",
     "viewerPermission": "READ", "pushedAt": "2026-01-01T00:00:00Z"},
]
TODAY = dt.date(2026, 11, 2)


class SelectTests(unittest.TestCase):
    def test_public_only_by_default(self):
        self.assertEqual([r["name"] for r in repo_index.select(FIXTURE, False)], ["alpha"])

    def test_private_included_on_request(self):
        self.assertEqual(len(repo_index.select(FIXTURE, True)), 3)


class RenderTests(unittest.TestCase):
    def test_rows_sorted_org_first_then_name_and_archived_collapsed(self):
        text = repo_index.render(FIXTURE, today=TODAY, include_private=True)
        body = text.split("<details>")[0]
        self.assertLess(body.index("[alpha]"), body.index("[zeta]"))
        self.assertIn("<summary>Archived (1)</summary>", text)
        self.assertIn("🔒 [old](https://github.com/ai-gmented-pm/old) · fork", text.split("<details>")[1])

    def test_cells_escaped_and_defaults(self):
        text = repo_index.render(FIXTURE, today=TODAY, include_private=True)
        self.assertIn("| A \\| pipe |", text)
        self.assertIn("🌐 [alpha](https://github.com/romain-nicod/alpha) · template | — | romain-nicod | Public | — |", text)
        self.assertIn("| romain-nicod | Private | Admin | 2026-11-01 |", text)
        self.assertIn("| Repository | What it is | Owner | Visibility | Access | Updated |", text)

    def test_missing_push_date_is_a_dash(self):
        repo = dict(FIXTURE[0], pushedAt=None)
        self.assertTrue(repo_index.row(repo).endswith("| Admin | — |"))

    def test_counts_and_date(self):
        text = repo_index.render(FIXTURE, today=TODAY, include_private=True)
        self.assertIn("3 repositories: 1 public, 2 private, 1 archived", text)
        self.assertIn("Generated on 2026-11-02", text)
        public = repo_index.render(repo_index.select(FIXTURE, False), today=TODAY, include_private=False)
        self.assertIn("1 public repositories, 0 of them archived", public)
        self.assertNotIn("<details>", public)


class OwnerTokenTests(unittest.TestCase):
    def test_owner_token_replaces_gh_token(self):
        with mock.patch.dict(os.environ, {"GH_TOKEN": "default", "REPO_INDEX_TOKEN_AI_GMENTED_PM": "org"}, clear=True):
            self.assertEqual(repo_index.owner_env("ai-gmented-pm")["GH_TOKEN"], "org")
            self.assertEqual(repo_index.owner_env("romain-nicod")["GH_TOKEN"], "default")

    def test_empty_owner_token_is_ignored(self):
        with mock.patch.dict(os.environ, {"GH_TOKEN": "default", "REPO_INDEX_TOKEN_AI_GMENTED_PM": ""}, clear=True):
            self.assertEqual(repo_index.owner_env("ai-gmented-pm")["GH_TOKEN"], "default")


if __name__ == "__main__":
    unittest.main()
