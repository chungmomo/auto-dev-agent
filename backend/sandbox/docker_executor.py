"""Docker-based sandbox test runner (SDD §6 / §12 step 4).

Runs pytest against a target directory inside an isolated, resource-limited,
network-disabled container instead of directly on the host. Implements the same
TestRunner protocol as SubprocessTestRunner (backend/sandbox/test_runner.py), so it's
a drop-in replacement wherever a TestRunner is expected — used once real (Claude-API
backed) Code Gen Agents start writing files that need to be executed to be tested.
"""

from __future__ import annotations

from pathlib import Path

import docker
from docker.errors import ImageNotFound

from backend.sandbox.test_runner import TestResult

SANDBOX_DOCKERFILE_DIR = Path(__file__).resolve().parents[2] / "docker"
DEFAULT_IMAGE = "auto-dev-agent-sandbox:latest"


class DockerSandboxTestRunner:
    """Runs `pytest` inside an isolated Docker container.

    Security properties (SDD §6): no network access, read-only workspace mount,
    memory/CPU limits, a hard wall-clock timeout, and the container is always
    removed afterward regardless of outcome.
    """

    def __init__(
        self,
        target_path: str | Path,
        image: str = DEFAULT_IMAGE,
        timeout: int = 120,
        mem_limit: str = "512m",
        nano_cpus: int = 1_000_000_000,  # 1 CPU
    ) -> None:
        self.target_path = Path(target_path).resolve()
        self.image = image
        self.timeout = timeout
        self.mem_limit = mem_limit
        self.nano_cpus = nano_cpus

    def run(self) -> TestResult:
        client = docker.from_env()
        self._ensure_image(client)

        container = client.containers.run(
            self.image,
            command=["pytest", "/workspace/target", "-q"],
            detach=True,
            volumes={str(self.target_path): {"bind": "/workspace/target", "mode": "ro"}},
            network_disabled=True,
            mem_limit=self.mem_limit,
            nano_cpus=self.nano_cpus,
            environment={"PYTHONDONTWRITEBYTECODE": "1"},
        )

        try:
            try:
                result = container.wait(timeout=self.timeout)
            except Exception:
                container.kill()
                return TestResult(
                    passed=False,
                    errors=[f"sandbox timed out after {self.timeout}s"],
                )

            exit_code = result.get("StatusCode", 1)
            logs = container.logs().decode("utf-8", errors="replace")
        finally:
            container.remove(force=True)

        if exit_code == 0:
            return TestResult(passed=True)

        failure_lines = [
            line for line in logs.splitlines() if "FAILED" in line or "Error" in line
        ]
        errors = failure_lines or [logs[-2000:]]
        return TestResult(passed=False, errors=errors)

    def _ensure_image(self, client) -> None:
        try:
            client.images.get(self.image)
        except ImageNotFound:
            client.images.build(
                path=str(SANDBOX_DOCKERFILE_DIR),
                dockerfile="sandbox.Dockerfile",
                tag=self.image,
                rm=True,
            )
