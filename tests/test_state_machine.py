import pytest

from backend.models.task import Task, TaskStatus
from backend.orchestrator.state_machine import InvalidTransitionError, TaskStateMachine

HAPPY_PATH = [
    TaskStatus.PLANNING,
    TaskStatus.CODING,
    TaskStatus.TESTING,
    TaskStatus.COMMITTING,
    TaskStatus.PR_CREATED,
    TaskStatus.CI_RUNNING,
    TaskStatus.DONE,
]


def test_happy_path_transitions_are_allowed():
    task = Task(user_prompt="demo")
    for target in HAPPY_PATH:
        TaskStateMachine.transition(task, target)
    assert task.status == TaskStatus.DONE


def test_failed_goes_to_needs_attention_not_back_to_coding():
    task = Task(user_prompt="demo")
    for target in [TaskStatus.PLANNING, TaskStatus.CODING, TaskStatus.TESTING]:
        TaskStateMachine.transition(task, target)

    TaskStateMachine.transition(task, TaskStatus.FAILED)
    assert not TaskStateMachine.can_transition(TaskStatus.FAILED, TaskStatus.CODING)
    TaskStateMachine.transition(task, TaskStatus.NEEDS_ATTENTION)
    assert task.status == TaskStatus.NEEDS_ATTENTION


def test_ci_running_can_fail_to_needs_attention():
    assert TaskStateMachine.can_transition(
        TaskStatus.CI_RUNNING, TaskStatus.NEEDS_ATTENTION
    )


@pytest.mark.parametrize(
    "current,target",
    [
        (TaskStatus.CREATED, TaskStatus.CODING),
        (TaskStatus.DONE, TaskStatus.PLANNING),
        (TaskStatus.NEEDS_ATTENTION, TaskStatus.CODING),
    ],
)
def test_invalid_transitions_are_rejected(current, target):
    task = Task(user_prompt="demo")
    task.status = current
    with pytest.raises(InvalidTransitionError):
        TaskStateMachine.transition(task, target)
