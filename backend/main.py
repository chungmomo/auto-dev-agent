"""CLI entrypoint for the Phase 1 demo (SDD §10 Phase 1: "chưa có UI, dùng CLI").

Usage:
    python -m backend.main "Thêm API đăng nhập bằng JWT"
    python -m backend.main "Thêm API đăng nhập bằng JWT" --fail-test
"""

from __future__ import annotations

import argparse
import json
import sys

from backend.agents.codegen_agent import MockCodeGenAgent
from backend.agents.planning_agent import MockPlanningAgent
from backend.models.task import Task
from backend.orchestrator.task_runner import TaskRunner
from backend.sandbox.test_runner import MockTestRunner


def main(argv: list[str] | None = None) -> Task:
    parser = argparse.ArgumentParser(description="Auto Coding Bot - Phase 1 CLI demo")
    parser.add_argument("prompt", help="Natural language feature request")
    parser.add_argument(
        "--fail-test",
        action="store_true",
        help="Force the mock test run to fail, to demo the NEEDS_ATTENTION path",
    )
    args = parser.parse_args(argv)

    task = Task(user_prompt=args.prompt)
    runner = TaskRunner(
        planning_agent=MockPlanningAgent(),
        codegen_agent=MockCodeGenAgent(),
        test_runner=MockTestRunner(passed=not args.fail_test),
        on_event=lambda evt: print(json.dumps(evt.to_dict(), ensure_ascii=False)),
    )
    runner.run(task)
    print(f"Final status: {task.status.value}", file=sys.stderr)
    return task


if __name__ == "__main__":
    main()
