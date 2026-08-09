from pathlib import Path

from backend.sandbox.test_runner import SubprocessTestRunner

FIXTURES = Path(__file__).parent / "fixtures" / "sample_target"


def test_subprocess_runner_reports_pass():
    result = SubprocessTestRunner(FIXTURES / "sample_pass.py").run()
    assert result.passed
    assert result.errors == []


def test_subprocess_runner_reports_fail_with_errors():
    result = SubprocessTestRunner(FIXTURES / "sample_fail.py").run()
    assert not result.passed
    assert result.errors
