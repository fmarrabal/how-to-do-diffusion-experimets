"""Small independent identity/transition regressions; no production freeze."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_doctoral_identity_v131 as D
import build_research_release_v13 as B


class DoctoralIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="academy-identity-fixture-")
        self.root = Path(self.temp.name)
        self.original = {
            "version": "1.2.0", "includedInLLMTraining": False,
            "application": "fixture", "activities": ["sync"], "guidedSteps": 93,
            "objectiveTasks": 79, "documentaryTasksRequiringHumanReview": 14,
            "numericSubchecks": 16, "scope": "fixture", "modelBoundaries": {},
            "publicDataset": {"rawFilesRetained": True},
            "releaseStatus": "reviewed-teaching-software",
            "qa": [{"path": "historical-only.json", "sha256": "1" * 64}],
            "files": [{"path": "web/doctoral-physics.js", "sha256": "2" * 64}],
        }
        for name in set(D.EXTRA_FILES) | {"web/doctoral-physics.js"}:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(("small fixture: " + name).encode())
        self.write_original()

    def tearDown(self):
        self.temp.cleanup()

    def write_original(self):
        self.old_bytes = json.dumps(self.original, separators=(",", ":")).encode()
        (self.root / D.ORIGINAL_FILE).write_bytes(self.old_bytes)
        self.old_hash = hashlib.sha256(self.old_bytes).hexdigest()

    def build(self):
        return D.build_manifest(self.root, original_sha256=self.old_hash)

    def test_stable_current_hashes_and_original_history_are_separate(self):
        first = self.build()
        self.assertEqual(first, self.build())
        self.assertEqual((self.root / D.ORIGINAL_FILE).read_bytes(), self.old_bytes)
        self.assertEqual(first["historicalQualification"]["qa"], self.original["qa"])
        self.assertEqual(first["releaseStatus"], "identity-only")
        self.assertNotIn("rootReview", first)
        self.assertFalse(first["newTrainingPerformed"])
        self.assertFalse(first["pilotOutcomesClaimed"])
        self.assertFalse(first["auditPatch"]["currentQAApprovalAsserted"])
        before = next(r for r in first["files"] if r["path"] == "web/doctoral-physics.js")
        (self.root / "web/doctoral-physics.js").write_bytes(b"a different current engine")
        after = next(r for r in self.build()["files"] if r["path"] == before["path"])
        self.assertNotEqual(before["sha256"], after["sha256"])
        self.assertEqual(self.build()["historicalQualification"], first["historicalQualification"])

    def test_original_mutation_fails_instead_of_requalifying_history(self):
        (self.root / D.ORIGINAL_FILE).write_bytes(self.old_bytes + b" ")
        with self.assertRaisesRegex(ValueError, "history has changed"):
            self.build()

    def test_generator_is_bound_but_generated_outputs_are_not(self):
        rows = {r["path"]: r for r in self.build()["files"]}
        name = "tools/build_doctoral_identity_v131.py"
        self.assertEqual(rows[name]["sha256"], D.sha(self.root / name))
        self.assertFalse(set(rows) & D.FORBIDDEN_CIRCULAR)
        self.original["files"].append({"path": "web/bundle-manifest.json"})
        self.write_original()
        with self.assertRaisesRegex(ValueError, "cannot hash themselves"):
            self.build()

    def test_original_path_cannot_escape_workspace(self):
        self.original["files"].append({"path": "../private.txt"})
        self.write_original()
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            self.build()


class VersionedFreezeFixtureTests(unittest.TestCase):
    def test_both_version_targets_roots_and_repeat_preservation(self):
        # Only three tiny synthetic public files per version. The root review is
        # a fixture, not an approval; production constants and sources are untouched.
        for version in ("1.3.0", "1.3.1"):
            with self.subTest(version=version), tempfile.TemporaryDirectory(prefix="academy-version-fixture-") as raw:
                work = Path(raw)
                academy = work / "desktop/academy"
                web = academy / "web"
                (web / "content").mkdir(parents=True)
                (web / "content/research-manifest.json").write_bytes(b'{"fixture":true}')
                (web / "content/doctoral-manifest.json").write_bytes(b'{"identityOnly":true}')
                research_sha = B.sha(web / "content/research-manifest.json")
                review = {"sha256": "3" * 64, "passed": True, "path": "fixture-review.json"}
                def prepare():
                    bundle = {"version": version, "releaseStatus": "pending-root-review",
                              "researchContentSha256": research_sha,
                              "doctoralContentSha256": B.sha(web / "content/doctoral-manifest.json"),
                              "doctoralReleaseStatus": "pending-root-review"}
                    (web / "bundle-manifest.json").write_bytes(B.encoded(bundle))
                    return {"researchContentSha256": research_sha}
                def files():
                    return {p.relative_to(web).as_posix(): p for p in web.rglob("*") if p.is_file()}
                output = work / "website" / ("v" + version)
                with patch.multiple(B, VERSION=version, WORKSPACE=work, ACADEMY=academy, WEB=web, DEFAULT_RELEASE=output), \
                     patch.object(B, "check_review", return_value=review), \
                     patch.object(B, "prepare", side_effect=prepare), \
                     patch.object(B, "public_files", side_effect=files):
                    result = B.freeze(academy / "unused-fixture-review.json", "3" * 64)
                    self.assertTrue(result["frozen"])
                    manifest = B.verify_frozen(output)
                    self.assertEqual(manifest["publicRoot"], "https://diffatonce.com/assets/academy/v" + version + "/")
                    if version == "1.3.1":
                        self.assertEqual(manifest["doctoralReleaseStatus"], "reviewed-teaching-software")
                    before = B.sha(output / "WEB_RELEASE_SHA256.json")
                    repeat = B.freeze(academy / "unused-fixture-review.json", "3" * 64, output)
                    self.assertTrue(repeat["alreadyPresent"])
                    self.assertEqual(B.sha(output / "WEB_RELEASE_SHA256.json"), before)
                    wrong = work / "website" / ("v1.3.1" if version == "1.3.0" else "v1.3.0")
                    with self.assertRaisesRegex(ValueError, "versioned public folder"):
                        B.freeze(academy / "unused-fixture-review.json", "3" * 64, wrong)


if __name__ == "__main__":
    unittest.main()
