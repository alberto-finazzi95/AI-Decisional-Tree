"""Run unittest discovery and publish a Markdown summary in GitHub Actions."""

import os
import sys
import unittest
from pathlib import Path
from typing import TextIO


class SummaryTestResult(unittest.TextTestResult):
    """Collect individual test and subtest results for the GitHub job summary."""

    def __init__(self, stream: TextIO, descriptions: bool, verbosity: int):
        super().__init__(stream, descriptions, verbosity)
        self.test_results: list[tuple[str, str, str]] = []

    def addSuccess(self, test: unittest.case.TestCase) -> None:
        self.test_results.append((test.id(), "Passed", ""))
        super().addSuccess(test)

    def addFailure(self, test: unittest.case.TestCase, err: tuple) -> None:
        self.test_results.append((test.id(), "Failed", self._exc_info_to_string(err, test)))
        super().addFailure(test, err)

    def addError(self, test: unittest.case.TestCase, err: tuple) -> None:
        self.test_results.append((test.id(), "Error", self._exc_info_to_string(err, test)))
        super().addError(test, err)

    def addSkip(self, test: unittest.case.TestCase, reason: str) -> None:
        self.test_results.append((test.id(), "Skipped", reason))
        super().addSkip(test, reason)

    def addSubTest(self, test: unittest.case.TestCase, subtest: unittest.case.TestCase, err: tuple | None) -> None:
        description = subtest._subDescription()
        if err is None:
            self.test_results.append((f"{test.id()} - {description}", "Passed", ""))
        else:
            self.test_results.append((f"{test.id()} - {description}", "Failed", self._exc_info_to_string(err, test)))
        super().addSubTest(test, subtest, err)


def _write_github_summary(result: SummaryTestResult) -> None:
    """Append test counts and individual outcomes to the GitHub Actions job summary."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    passed = sum(status == "Passed" for _, status, _ in result.test_results)
    failed = sum(status == "Failed" for _, status, _ in result.test_results)
    errors = sum(status == "Error" for _, status, _ in result.test_results)
    skipped = sum(status == "Skipped" for _, status, _ in result.test_results)

    with Path(summary_path).open("a", encoding="utf-8") as summary:
        summary.write("## Unit test results\n\n")
        summary.write(
            f"**{len(result.test_results)} cases** — {passed} passed, "
            f"{failed} failed, {errors} errors, {skipped} skipped "
            f"({result.testsRun} test methods).\n\n"
        )
        summary.write("| Test | Result |\n| --- | --- |\n")
        for name, status, details in result.test_results:
            summary.write(f"| `{name.replace('|', '\\|')}` | {status} |\n")
            if details:
                summary.write(
                    f"\n<details><summary>{status} details</summary>\n\n```text\n{details}\n```\n</details>\n\n"
                )


def main() -> int:
    """Discover and run all test modules, then write a GitHub Actions summary."""
    test_dir = Path(__file__).parent
    sys.path.insert(0, str(test_dir.parent))
    suite = unittest.defaultTestLoader.discover(str(test_dir), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2, resultclass=SummaryTestResult)
    result = runner.run(suite)
    _write_github_summary(result)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
