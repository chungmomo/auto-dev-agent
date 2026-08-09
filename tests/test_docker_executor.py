from pathlib import Path

import pytest

docker = pytest.importorskip("docker")

from backend.sandbox.docker_executor import DockerSandboxTestRunner  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "sample_target"


def _docker_daemon_available() -> bool:
    try:
        docker.from_env().ping()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _docker_daemon_available(), reason="Docker daemon not available"
)


def test_docker_sandbox_reports_pass():
    result = DockerSandboxTestRunner(FIXTURES / "sample_pass.py").run()
    assert result.passed
    assert result.errors == []


def test_docker_sandbox_reports_fail_with_errors():
    result = DockerSandboxTestRunner(FIXTURES / "sample_fail.py").run()
    assert not result.passed
    assert result.errors
