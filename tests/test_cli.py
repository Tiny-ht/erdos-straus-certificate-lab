import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from erdos_straus import Exhausted, NoX, dumps_certificate


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.env = dict(os.environ)
        source = Path(__file__).resolve().parents[1] / "src"
        self.env["PYTHONPATH"] = str(source)

    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, "-m", "erdos_straus", *map(str, arguments)],
            cwd=self.directory, env=self.env, capture_output=True, text=True,
            timeout=15,
        )

    def test_branch_stdout_and_scope_verification(self):
        produced = self.run_cli("branch", 5, 3)
        self.assertEqual(produced.returncode, 0, produced.stderr)
        data = json.loads(produced.stdout)
        self.assertEqual(data["kind"], "no_x")
        self.assertEqual(data["remainders"], [[3, 3], [4, 8]])
        path = self.directory / "branch.json"
        path.write_text(produced.stdout, encoding="utf-8")
        checked = self.run_cli("verify", path, "--n", 5, "--x", 3)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertEqual(json.loads(checked.stdout), {
            "accepted": True, "kind": "no_x", "scope": {"n": 5, "x": 3},
        })
        wrong_scope = self.run_cli("verify", path, "--n", 5, "--x", 2)
        self.assertEqual(wrong_scope.returncode, 1)
        self.assertFalse(json.loads(wrong_scope.stdout)["accepted"])

    def test_output_file_and_positive_witness(self):
        path = self.directory / "witness.json"
        produced = self.run_cli("branch", 5, 2, "--output", path)
        self.assertEqual(produced.returncode, 0, produced.stderr)
        self.assertEqual(produced.stdout, "")
        self.assertEqual(json.loads(path.read_text())["z"], 20)
        checked = self.run_cli("verify", path, "--n", 5, "--x", 2)
        self.assertEqual(checked.returncode, 0)
        self.assertTrue(json.loads(checked.stdout)["accepted"])
        wrong_n = self.run_cli("verify", path, "--n", 6, "--x", 2)
        self.assertEqual(wrong_n.returncode, 1)

    def test_search_found_and_budget_unknown_are_distinct(self):
        found = self.run_cli("search", 5)
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertEqual(json.loads(found.stdout)["kind"], "witness")
        stopped = self.run_cli("search", 5, "--max-checks", 0)
        self.assertEqual(stopped.returncode, 3, stopped.stderr)
        progress = json.loads(stopped.stdout)
        self.assertEqual(progress["status"], "unknown")
        self.assertEqual(progress["checks_done"], 0)
        self.assertEqual(progress["closed_x"], [])
        self.assertNotIn("schema", progress)
        self.assertNotIn("kind", progress)
        path = self.directory / "unknown.json"
        path.write_text(stopped.stdout, encoding="utf-8")
        rejected = self.run_cli("verify", path, "--n", 5, "--x", 2)
        self.assertEqual(rejected.returncode, 2)
        self.assertNotIn("Traceback", rejected.stderr)

    def test_unknown_can_be_written_without_becoming_a_certificate(self):
        path = self.directory / "progress.json"
        result = self.run_cli("search", 5, "--max-checks", 0, "--output", path)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertEqual(json.loads(path.read_text())["status"], "unknown")

    def test_mathematically_invalid_certificate_is_rejected(self):
        path = self.directory / "bad-remainder.json"
        path.write_text(dumps_certificate(NoX(5, 3, ((3, 3), (4, 9)))), encoding="utf-8")
        result = self.run_cli("verify", path, "--n", 5, "--x", 3)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["accepted"])
        self.assertEqual(result.stderr, "")

    def test_verify_requires_scope_appropriate_to_certificate(self):
        branch = self.directory / "branch.json"
        branch.write_text(dumps_certificate(NoX(5, 3, ((3, 3), (4, 8)))), encoding="utf-8")
        missing_x = self.run_cli("verify", branch, "--n", 5)
        self.assertEqual(missing_x.returncode, 2)
        self.assertIn("--x is required", missing_x.stderr)
        root = self.directory / "root.json"
        root.write_text(dumps_certificate(Exhausted(5, ())), encoding="utf-8")
        extra_x = self.run_cli("verify", root, "--n", 5, "--x", 3)
        self.assertEqual(extra_x.returncode, 2)
        self.assertIn("--x is not allowed", extra_x.stderr)
        incomplete = self.run_cli("verify", root, "--n", 5)
        self.assertEqual(incomplete.returncode, 1)
        self.assertEqual(json.loads(incomplete.stdout)["scope"], {"n": 5})

    def test_normal_input_errors_have_exit_two_without_traceback(self):
        malformed = self.directory / "malformed.json"
        malformed.write_text('{"unexpected": true}', encoding="utf-8")
        invalid_utf8 = self.directory / "invalid-utf8.json"
        invalid_utf8.write_bytes(b"\xff")
        cases = [
            ("branch", "true", 3), ("branch", "5.0", 3), ("branch", 1, 1),
            ("search", 5, "--max-checks", -1), ("search", 5, "--max-checks", "1.5"),
            ("branch", 5, 3, "--out", self.directory / "bad-abbreviation.json"),
            ("verify", malformed, "--n", 5, "--x", 3),
            ("verify", invalid_utf8, "--n", 5, "--x", 3),
            ("verify", self.directory / "missing.json", "--n", 5, "--x", 3),
            ("branch", 5, 3, "--output", self.directory / "missing" / "file.json"),
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                result = self.run_cli(*arguments)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
