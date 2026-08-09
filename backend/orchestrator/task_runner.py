"""Drives a single Task through the full lifecycle from SDD §3.

COMMITTING / PR_CREATED / CI_RUNNING are stubs in Phase 1 (log + auto-pass) since
real Git/GitHub integration is SDD §12 step 5, not step 3. This lets the full
CREATED -> ... -> DONE lifecycle be exercised end-to-end, per the "test luồng" intent
of SDD §12 step 2.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from backend.agents.codegen_agent import CodeGenAgent
from backend.agents.planning_agent import PlanningAgent
from backend.models.task import (
    GeneratedFile,
    StepStatus,
    Task,
    TaskEvent,
    TaskStatus,
)
from backend.orchestrator.state_machine import TaskStateMachine
from backend.sandbox.test_runner import TestRunner

EventCallback = Callable[[TaskEvent], None]
TestRunnerFactory = Callable[[Path], TestRunner]


class TaskRunner:
    def __init__(
        self,
        planning_agent: PlanningAgent,
        codegen_agent: CodeGenAgent,
        test_runner_factory: TestRunnerFactory,
        on_event: EventCallback | None = None,
        workspace_root: Path = Path("workspace"),
    ) -> None:
        self.planning_agent = planning_agent
        self.codegen_agent = codegen_agent
        self.test_runner_factory = test_runner_factory
        self.on_event = on_event
        self.workspace_root = workspace_root

    def run(self, task: Task) -> Task:
        self._emit(task, "task_created")

        workspace_dir = self.workspace_root / task.id
        workspace_dir.mkdir(parents=True, exist_ok=True)
        task.workspace_dir = str(workspace_dir)

        TaskStateMachine.transition(task, TaskStatus.PLANNING)
        self._emit(task, "planning_started")
        try:
            task.steps = self.planning_agent.plan(task.user_prompt)
        except Exception as exc:
            return self._fail(task, f"planning failed: {exc}")
        self._emit(
            task,
            "plan_ready",
            extra={"steps": [step.description for step in task.steps]},
        )

        TaskStateMachine.transition(task, TaskStatus.CODING)
        existing_files: list[GeneratedFile] = []
        for step in task.steps:
            step.status = StepStatus.RUNNING
            step.attempt_count += 1
            try:
                step.generated_files = self.codegen_agent.generate(
                    step, task.user_prompt, existing_files
                )
                self._write_files(workspace_dir, step.generated_files)
            except Exception as exc:
                return self._fail(task, f"code generation failed: {exc}")
            existing_files.extend(step.generated_files)
            step.status = StepStatus.PASSED
            self._emit(task, "code_generated", step=step.description)

        TaskStateMachine.transition(task, TaskStatus.TESTING)
        test_runner = self.test_runner_factory(workspace_dir)
        result = test_runner.run()
        self._emit(task, "test_result", passed=result.passed, errors=result.errors)

        if not result.passed:
            return self._fail(task, "tests failed")

        TaskStateMachine.transition(task, TaskStatus.COMMITTING)
        self._emit(task, "committing", extra={"note": "stub in Phase 1"})

        TaskStateMachine.transition(task, TaskStatus.PR_CREATED)
        task.pr_url = "stub://pr/not-yet-implemented"
        self._emit(task, "pr_created", extra={"pr_url": task.pr_url})

        TaskStateMachine.transition(task, TaskStatus.CI_RUNNING)
        self._emit(task, "ci_running", extra={"note": "stub in Phase 1"})

        TaskStateMachine.transition(task, TaskStatus.DONE)
        self._emit(task, "done")

        return task

    def _write_files(self, workspace_dir: Path, files: list[GeneratedFile]) -> None:
        workspace_resolved = workspace_dir.resolve()
        for file in files:
            candidate = (workspace_dir / file.path).resolve()
            if not candidate.is_relative_to(workspace_resolved):
                raise ValueError(
                    f"generated file path escapes workspace: {file.path!r}"
                )
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_text(file.content, encoding="utf-8")

    def _fail(self, task: Task, reason: str) -> Task:
        if task.status == TaskStatus.TESTING:
            TaskStateMachine.transition(task, TaskStatus.FAILED)
            TaskStateMachine.transition(task, TaskStatus.NEEDS_ATTENTION)
        elif task.status in (TaskStatus.PLANNING, TaskStatus.CODING):
            TaskStateMachine.transition(task, TaskStatus.NEEDS_ATTENTION)
        self._emit(task, "error", extra={"reason": reason})
        return task

    def _emit(
        self,
        task: Task,
        event: str,
        step: str | None = None,
        passed: bool | None = None,
        errors: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        evt = TaskEvent(
            event=event,
            task_id=task.id,
            step=step,
            passed=passed,
            errors=errors or [],
            extra=extra or {},
        )
        task.events.append(evt)
        if self.on_event is not None:
            self.on_event(evt)
