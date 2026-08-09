"""CLI entrypoint (SDD §10 Phase 1: "chưa có UI, dùng CLI").

Usage:
    python -m backend.main "Thêm API đăng nhập bằng JWT"
    python -m backend.main "Thêm API đăng nhập bằng JWT" --fail-test

    # Real Claude API + Docker sandbox (SDD §12 steps 3-4). Requires
    # ANTHROPIC_API_KEY set and Docker installed/running:
    python -m backend.main "Trang web học tiếng Việt cho bé gái 7 tuổi" --engine claude
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.models.task import Task
from backend.orchestrator.task_runner import TaskRunner


def main(argv: list[str] | None = None) -> Task:
    parser = argparse.ArgumentParser(description="Auto Coding Bot CLI")
    parser.add_argument("prompt", help="Natural language feature request")
    parser.add_argument(
        "--engine",
        choices=["mock", "claude"],
        default="mock",
        help="mock: canned agents, no dependencies/network (default). "
        "claude: real Claude API + Docker sandbox, needs ANTHROPIC_API_KEY and Docker.",
    )
    parser.add_argument(
        "--workspace",
        default="workspace",
        help="Directory generated task files are written under (default: workspace/)",
    )
    parser.add_argument(
        "--fail-test",
        action="store_true",
        help="mock engine only: force the mock test run to fail, to demo the "
        "NEEDS_ATTENTION path",
    )
    args = parser.parse_args(argv)

    if args.engine == "claude":
        from backend.agents.claude_codegen_agent import ClaudeCodeGenAgent
        from backend.agents.claude_planning_agent import ClaudePlanningAgent
        from backend.sandbox.docker_executor import DockerSandboxTestRunner

        planning_agent = ClaudePlanningAgent()
        codegen_agent = ClaudeCodeGenAgent()
        test_runner_factory = lambda ws: DockerSandboxTestRunner(ws)  # noqa: E731
    else:
        from backend.agents.codegen_agent import MockCodeGenAgent
        from backend.agents.planning_agent import MockPlanningAgent
        from backend.sandbox.test_runner import MockTestRunner

        planning_agent = MockPlanningAgent()
        codegen_agent = MockCodeGenAgent()
        test_runner_factory = lambda ws: MockTestRunner(  # noqa: E731
            passed=not args.fail_test
        )

    task = Task(user_prompt=args.prompt)
    runner = TaskRunner(
        planning_agent=planning_agent,
        codegen_agent=codegen_agent,
        test_runner_factory=test_runner_factory,
        on_event=lambda evt: print(json.dumps(evt.to_dict(), ensure_ascii=False)),
        workspace_root=Path(args.workspace),
    )
    runner.run(task)
    print(f"Final status: {task.status.value}", file=sys.stderr)
    print(f"Workspace: {task.workspace_dir}", file=sys.stderr)
    return task


if __name__ == "__main__":
    main()
