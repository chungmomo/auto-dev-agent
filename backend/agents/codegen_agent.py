"""Code generation agent (SDD §3.2, step 3).

Phase 1 uses a mock implementation so the orchestrator flow can be exercised
without a Claude API key. The real Claude-backed agent is SDD §12 step 3.
"""

from __future__ import annotations

from typing import Protocol

from backend.models.task import TaskStep


class CodeGenAgent(Protocol):
    def generate(self, step: TaskStep) -> str: ...


class MockCodeGenAgent:
    """Returns a small canned code snippet for any step."""

    def generate(self, step: TaskStep) -> str:
        return f"# generated for: {step.description}\npass\n"
