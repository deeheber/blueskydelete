"""Offline quality-script checks; uv and its tools are replaced locally."""

import json
import shutil
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "code-quality.sh"
BASH = shutil.which("bash")
EXPECTED_COMMANDS = [
    ["run", "--locked", "ruff", "check", "--fix", "."],
    ["run", "--locked", "ruff", "format", "."],
    ["run", "--locked", "mypy", "."],
]


@unittest.skipUnless(BASH, "requires Bash to run the quality script")
class CodeQualityScriptTests(unittest.TestCase):
    """Exercise shell control flow without running or installing tools."""

    def setUp(self) -> None:
        self.temporary = TemporaryDirectory(prefix="code quality ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        self.bin = self.root / "bin with spaces"
        self.bin.mkdir()
        self.log = self.root / "calls.jsonl"
        self.uv = self.bin / "uv"
        self.uv.write_text(
            f"#!{sys.executable}\n"
            + textwrap.dedent(
                """\
                import json
                import os
                import sys
                from pathlib import Path

                log = Path(os.environ["QUALITY_TEST_LOG"])
                with log.open("a") as stream:
                    stream.write(json.dumps({
                        "args": sys.argv[1:],
                        "cwd": os.getcwd(),
                    }) + "\\n")
                step = len(log.read_text().splitlines())
                print(f"tool output {step}")
                if step == int(os.environ["QUALITY_TEST_FAIL_STEP"]):
                    print(f"tool failure {step}", file=sys.stderr)
                    sys.exit(int(os.environ["QUALITY_TEST_EXIT_CODE"]))
                """
            ),
            encoding="utf-8",
        )
        self.uv.chmod(0o755)

    def run_script(
        self, fail_step: int = 0, exit_code: int = 0
    ) -> subprocess.CompletedProcess[str]:
        """Run with an isolated PATH and a configurable tool failure.

        Args:
            fail_step: One-based invocation to fail, or zero for success.
            exit_code: Exit status for the failing invocation.

        Returns:
            Captured script output and exit status.
        """
        self.log.unlink(missing_ok=True)
        assert BASH is not None
        return subprocess.run(
            [BASH, str(SCRIPT)],
            cwd=self.project,
            env={
                "PATH": str(self.bin),
                "LC_ALL": "C",
                "QUALITY_TEST_LOG": str(self.log),
                "QUALITY_TEST_FAIL_STEP": str(fail_step),
                "QUALITY_TEST_EXIT_CODE": str(exit_code),
            },
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

    def assert_commands(self, expected: list[list[str]]) -> None:
        """Check exact arguments, ordering, and working directories.

        Args:
            expected: Argument lists in expected invocation order.
        """
        calls = [
            json.loads(line) for line in self.log.read_text().splitlines()
        ]
        self.assertEqual(
            calls,
            [
                {"args": command, "cwd": str(self.project)}
                for command in expected
            ],
        )

    def test_runs_locked_lint_format_and_type_checks_across_project(
        self,
    ) -> None:
        (self.project / "main.py").touch()
        nested = self.project / "nested directory"
        nested.mkdir()
        (nested / "another file.py").touch()

        result = self.run_script()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_commands(EXPECTED_COMMANDS)
        self.assertEqual(
            result.stdout, "tool output 1\ntool output 2\ntool output 3\n"
        )
        self.assertEqual(result.stderr, "")

    def test_empty_project_is_delegated_to_tools(self) -> None:
        result = self.run_script()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_commands(EXPECTED_COMMANDS)

    def test_each_tool_failure_stops_script_and_preserves_status(self) -> None:
        for fail_step in range(1, len(EXPECTED_COMMANDS) + 1):
            for exit_code in (1, 2, 42):
                with self.subTest(fail_step=fail_step, exit_code=exit_code):
                    result = self.run_script(fail_step, exit_code)

                    self.assertEqual(result.returncode, exit_code)
                    self.assert_commands(EXPECTED_COMMANDS[:fail_step])
                    self.assertEqual(
                        result.stdout,
                        "".join(
                            f"tool output {step}\n"
                            for step in range(1, fail_step + 1)
                        ),
                    )
                    self.assertEqual(
                        result.stderr, f"tool failure {fail_step}\n"
                    )

    def test_missing_uv_fails_without_using_host_tools(self) -> None:
        self.uv.unlink()

        result = self.run_script()

        self.assertEqual(result.returncode, 127)
        self.assertIn("uv: command not found", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
