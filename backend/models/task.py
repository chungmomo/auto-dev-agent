"""In-memory data model for a task, simplified from SDD §5 (no DB yet in Phase 1)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """States from SDD §3.1."""

    CREATED = "CREATED"
    PLANNING = "PLANNING"
    CODING = "CODING"
    TESTING = "TESTING"
    FAILED = "FAILED"
    COMMITTING = "COMMITTING"
    PR_CREATED = "PR_CREATED"
    CI_RUNNING = "CI_RUNNING"
    DONE = "DONE"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"


@dataclass
class TaskStep:
    """A single planned unit of work, from SDD §5.2."""

    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: StepStatus = StepStatus.PENDING
    attempt_count: int = 0
    generated_code: str | None = None


@dataclass
class TaskEvent:
    """Realtime event, shaped after the sample in SDD §4.3."""

    event: str
    task_id: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    step: str | None = None
    attempt: int | None = None
    passed: bool | None = None
    errors: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "event": self.event,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
        }
        if self.step is not None:
            data["step"] = self.step
        if self.attempt is not None:
            data["attempt"] = self.attempt
        if self.passed is not None:
            data["passed"] = self.passed
        if self.errors:
            data["errors"] = self.errors
        data.update(self.extra)
        return data


@dataclass
class Task:
    """A feature request being carried through the lifecycle, from SDD §5.1."""

    user_prompt: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.CREATED
    repo_url: str | None = None
    branch_name: str | None = None
    pr_url: str | None = None
    steps: list[TaskStep] = field(default_factory=list)
    events: list[TaskEvent] = field(default_factory=list)
