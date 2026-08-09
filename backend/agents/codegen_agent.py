"""Code generation agent (SDD §3.2, step 3).

Phase 1 uses a mock implementation so the orchestrator flow can be exercised
without a Claude API key. The real Claude-backed agent lives in
backend/agents/claude_codegen_agent.py (SDD §12 step 3) — kept out of this file so
the mock path never needs the anthropic/pydantic packages installed.
"""

from __future__ import annotations

import re
from typing import Protocol

from backend.models.task import GeneratedFile, TaskStep


class CodeGenAgent(Protocol):
    def generate(
        self,
        step: TaskStep,
        user_prompt: str,
        existing_files: list[GeneratedFile],
    ) -> list[GeneratedFile]: ...


class MockCodeGenAgent:
    """Returns one small canned file per step, regardless of context."""

    def generate(
        self,
        step: TaskStep,
        user_prompt: str,
        existing_files: list[GeneratedFile],
    ) -> list[GeneratedFile]:
        slug = re.sub(r"[^a-z0-9]+", "_", step.description.lower()).strip("_")[:40]
        slug = slug or step.id
        content = f"# generated for: {step.description}\npass\n"
        return [GeneratedFile(path=f"generated/{slug}.py", content=content)]
