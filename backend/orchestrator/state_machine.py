"""Task state machine, encoding the transition diagram from SDD §3.1.

Phase 1 has no retry loop (per the roadmap in SDD §10), so FAILED goes straight
to NEEDS_ATTENTION rather than back to CODING. Phase 2 will add the retry edge.
"""

from __future__ import annotations

from backend.models.task import Task, TaskStatus

TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.CREATED: frozenset({TaskStatus.PLANNING}),
    TaskStatus.PLANNING: frozenset({TaskStatus.CODING}),
    TaskStatus.CODING: frozenset({TaskStatus.TESTING}),
    TaskStatus.TESTING: frozenset({TaskStatus.FAILED, TaskStatus.COMMITTING}),
    TaskStatus.FAILED: frozenset({TaskStatus.NEEDS_ATTENTION}),
    TaskStatus.COMMITTING: frozenset({TaskStatus.PR_CREATED}),
    TaskStatus.PR_CREATED: frozenset({TaskStatus.CI_RUNNING}),
    TaskStatus.CI_RUNNING: frozenset({TaskStatus.DONE, TaskStatus.NEEDS_ATTENTION}),
    TaskStatus.DONE: frozenset(),
    TaskStatus.NEEDS_ATTENTION: frozenset(),
}


class InvalidTransitionError(Exception):
    def __init__(self, current: TaskStatus, target: TaskStatus) -> None:
        super().__init__(f"Cannot transition from {current} to {target}")
        self.current = current
        self.target = target


class TaskStateMachine:
    """Validates and applies state transitions for a Task."""

    @staticmethod
    def can_transition(current: TaskStatus, target: TaskStatus) -> bool:
        return target in TRANSITIONS[current]

    @classmethod
    def transition(cls, task: Task, target: TaskStatus) -> None:
        if not cls.can_transition(task.status, target):
            raise InvalidTransitionError(task.status, target)
        task.status = target
