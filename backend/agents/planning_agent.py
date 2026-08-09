"""Planning agent: turns a user prompt into a task breakdown (SDD §3.2, step 2).

Phase 1 uses a mock implementation so the orchestrator flow can be exercised
without a Claude API key. The real Claude-backed agent is SDD §12 step 3.
"""

from __future__ import annotations

from typing import Protocol

from backend.models.task import TaskStep


class PlanningAgent(Protocol):
    def plan(self, user_prompt: str) -> list[TaskStep]: ...


class MockPlanningAgent:
    """Returns a small, deterministic plan regardless of the prompt."""

    def plan(self, user_prompt: str) -> list[TaskStep]:
        return [
            TaskStep(description=f"Analyze requirement: {user_prompt}"),
            TaskStep(description="Implement core logic"),
            TaskStep(description="Write unit tests"),
        ]
