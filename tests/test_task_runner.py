from pathlib import Path

from backend.agents.codegen_agent import MockCodeGenAgent
from backend.agents.planning_agent import MockPlanningAgent
from backend.models.task import Task, TaskStatus
from backend.orchestrator.task_runner import TaskRunner
from backend.sandbox.test_runner import MockTestRunner


def make_runner(passed: bool, workspace_root: Path) -> TaskRunner:
    return TaskRunner(
        planning_agent=MockPlanningAgent(),
        codegen_agent=MockCodeGenAgent(),
        test_runner_factory=lambda ws: MockTestRunner(passed=passed),
        workspace_root=workspace_root,
    )


def test_full_run_reaches_done_on_passing_tests(tmp_path):
    task = Task(user_prompt="Add JWT login API")
    runner = make_runner(passed=True, workspace_root=tmp_path)

    result = runner.run(task)

    assert result.status == TaskStatus.DONE
    assert result.pr_url is not None
    assert len(result.steps) == 3
    event_names = [e.event for e in result.events]
    assert event_names == [
        "task_created",
        "planning_started",
        "plan_ready",
        "code_generated",
        "code_generated",
        "code_generated",
        "test_result",
        "committing",
        "pr_created",
        "ci_running",
        "done",
    ]

    assert result.workspace_dir == str(tmp_path / result.id)
    written_files = list(Path(result.workspace_dir).rglob("*.py"))
    assert len(written_files) == 3


def test_run_stops_at_needs_attention_when_tests_fail(tmp_path):
    task = Task(user_prompt="Add JWT login API")
    runner = make_runner(passed=False, workspace_root=tmp_path)

    result = runner.run(task)

    assert result.status == TaskStatus.NEEDS_ATTENTION
    assert result.pr_url is None
    last_events = [e.event for e in result.events[-2:]]
    assert last_events == ["test_result", "error"]

    test_result_event = next(e for e in result.events if e.event == "test_result")
    assert test_result_event.passed is False
    assert test_result_event.errors == ["mock test failure"]


def test_events_carry_task_id(tmp_path):
    task = Task(user_prompt="demo")
    runner = make_runner(passed=True, workspace_root=tmp_path)
    result = runner.run(task)
    assert all(e.task_id == task.id for e in result.events)
