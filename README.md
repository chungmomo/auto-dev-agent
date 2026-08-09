# auto-dev-agent

Auto Coding Bot — takes a natural-language feature request and automatically
plans, generates code, tests, and (in later phases) commits/PRs/deploys it.
Full design: [docs/SDD.md](docs/SDD.md).

## Status: Phase 1 (MVP) + Docker sandbox

Orchestrator + state machine, using mock Planning/CodeGen agents, driven from a CLI.
No web UI, no real Claude API calls, no Git/GitHub integration yet — see the roadmap in
[docs/SDD.md](docs/SDD.md#10-l%E1%BB%99-tr%C3%ACnh-tri%E1%BB%83n-khai-roadmap-%C4%91%E1%BB%81-xu%E1%BA%A5t).

A Docker-based sandbox test runner ([backend/sandbox/docker_executor.py](backend/sandbox/docker_executor.py))
is available as a drop-in replacement for the local `SubprocessTestRunner` — it runs
`pytest` inside an isolated, network-disabled, resource-limited container instead of
directly on the host (SDD §6). It isn't wired into the CLI demo yet (that happens once
the Planning/CodeGen agents call the real Claude API and start generating code that
actually needs sandboxing).

**Requires Docker installed and the daemon running.** The sandbox image
(`docker/sandbox.Dockerfile`) is built automatically on first use and cached.

```bash
pytest tests/test_docker_executor.py -q -v
```

### Run the demo

```bash
pip install -r requirements.txt
python -m backend.main "Thêm API đăng nhập bằng JWT"
```

Add `--fail-test` to see the failure path (state ends at `NEEDS_ATTENTION`
instead of `DONE`):

```bash
python -m backend.main "Thêm API đăng nhập bằng JWT" --fail-test
```

### Run the tests

```bash
pytest tests/ -q
```

