"""Real Claude-backed Planning Agent (SDD §12 step 3).

Kept in its own module so the mock CLI path (backend/agents/planning_agent.py) never
needs the anthropic/pydantic packages installed. Only imported when the CLI is run
with --engine claude.
"""

from __future__ import annotations

import anthropic
from pydantic import BaseModel

from backend.models.task import TaskStep

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """\
You are the Planning Agent of an automated software development pipeline (SDD §3.2).
Given a natural-language feature request, break it down into a small, ordered list of
concrete implementation steps for a Python project (this pipeline only supports
Python projects for now — SDD §1.2). Each step should be self-contained enough that a
separate Code Generation step can implement it as one or more files, building on the
files earlier steps produced. Prefer 2 to 6 steps. Do not include deployment,
infrastructure, or non-Python steps."""


class PlanStepSpec(BaseModel):
    description: str


class PlanSpec(BaseModel):
    steps: list[PlanStepSpec]


class ClaudePlanningAgent:
    """Calls the real Claude API to produce a task breakdown."""

    def __init__(self, client: anthropic.Anthropic | None = None) -> None:
        self.client = client or anthropic.Anthropic()

    def plan(self, user_prompt: str) -> list[TaskStep]:
        try:
            response = self.client.messages.parse(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
                output_format=PlanSpec,
            )
        except anthropic.AuthenticationError as exc:
            raise RuntimeError(
                "Claude API authentication failed during planning — check "
                "ANTHROPIC_API_KEY."
            ) from exc
        except anthropic.RateLimitError as exc:
            raise RuntimeError("Claude API rate limited during planning.") from exc
        except anthropic.APIConnectionError as exc:
            raise RuntimeError(
                "Could not reach the Claude API during planning."
            ) from exc
        except anthropic.APIStatusError as exc:
            raise RuntimeError(f"Claude API error during planning: {exc}") from exc

        spec = response.parsed_output
        return [TaskStep(description=step.description) for step in spec.steps]
