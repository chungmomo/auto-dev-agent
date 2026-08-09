"""Offline tests for the real Claude-backed agents.

The transport (client.messages.parse) is mocked, so these never hit the network and
never need an API key — they only verify the JSON-schema <-> dataclass plumbing.
"""

from unittest.mock import MagicMock

import pytest

pytest.importorskip("anthropic")

from backend.agents.claude_codegen_agent import (  # noqa: E402
    ClaudeCodeGenAgent,
    CodeGenSpec,
    FileSpec,
)
from backend.agents.claude_planning_agent import (  # noqa: E402
    ClaudePlanningAgent,
    PlanSpec,
    PlanStepSpec,
)
from backend.models.task import GeneratedFile, TaskStep  # noqa: E402


def _fake_response(parsed_output):
    response = MagicMock()
    response.parsed_output = parsed_output
    return response


def test_claude_planning_agent_maps_plan_spec_to_task_steps():
    client = MagicMock()
    client.messages.parse.return_value = _fake_response(
        PlanSpec(
            steps=[
                PlanStepSpec(description="Set up Flask app"),
                PlanStepSpec(description="Add lesson pages"),
            ]
        )
    )
    agent = ClaudePlanningAgent(client=client)

    steps = agent.plan("Web học tiếng Việt cho bé 7 tuổi")

    assert [s.description for s in steps] == [
        "Set up Flask app",
        "Add lesson pages",
    ]
    client.messages.parse.assert_called_once()
    _, kwargs = client.messages.parse.call_args
    assert kwargs["output_format"] is PlanSpec


def test_claude_codegen_agent_maps_code_gen_spec_to_generated_files():
    client = MagicMock()
    client.messages.parse.return_value = _fake_response(
        CodeGenSpec(files=[FileSpec(path="app.py", content="print('hi')")])
    )
    agent = ClaudeCodeGenAgent(client=client)
    step = TaskStep(description="Set up Flask app")

    files = agent.generate(step, "Web học tiếng Việt cho bé 7 tuổi", [])

    assert files == [GeneratedFile(path="app.py", content="print('hi')")]
    client.messages.parse.assert_called_once()


def test_claude_codegen_agent_includes_existing_files_as_context():
    client = MagicMock()
    client.messages.parse.return_value = _fake_response(
        CodeGenSpec(
            files=[FileSpec(path="tests/test_app.py", content="def test_ok(): pass")]
        )
    )
    agent = ClaudeCodeGenAgent(client=client)
    step = TaskStep(description="Write tests")
    existing = [GeneratedFile(path="app.py", content="print('hi')")]

    agent.generate(step, "demo", existing)

    _, kwargs = client.messages.parse.call_args
    user_message = kwargs["messages"][0]["content"]
    assert "app.py" in user_message
    assert "print('hi')" in user_message
