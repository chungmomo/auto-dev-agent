"""Test execution (SDD §3.2 step 4 / §7).

Phase 1 runs tests as a local subprocess, not yet inside a Docker sandbox
(that isolation is SDD §12 step 4). A mock runner is also provided so the
CLI demo and unit tests can exercise both the pass and fail paths without
needing real test fixtures.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class TestResult:
    passed: bool
    errors: list[str] = field(default_factory=list)


class TestRunner(Protocol):
    def run(self) -> TestResult: ...


class MockTestRunner:
    """Always returns a fixed result, useful for demos and tests."""

    def __init__(self, passed: bool = True) -> None:
        self._passed = passed

    def run(self) -> TestResult:
        if self._passed:
            return TestResult(passed=True)
        return TestResult(passed=False, errors=["mock test failure"])


class SubprocessTestRunner:
    """Runs `pytest` against a target path as a plain local subprocess."""

    def __init__(self, target_path: str | Path, timeout: int = 120) -> None:
        self.target_path = Path(target_path)
        self.timeout = timeout

    def run(self) -> TestResult:
        try:
            result = subprocess.run(
                ["pytest", str(self.target_path), "-q"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return TestResult(passed=False, errors=[f"test run timed out after {self.timeout}s"])

        if result.returncode == 0:
            return TestResult(passed=True)

        failure_lines = [
            line
            for line in result.stdout.splitlines()
            if "FAILED" in line or "Error" in line
        ]
        errors = failure_lines or [result.stdout[-2000:] or result.stderr[-2000:]]
        return TestResult(passed=False, errors=errors)
