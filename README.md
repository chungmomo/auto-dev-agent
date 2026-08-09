# auto-dev-agent

Auto Coding Bot — takes a natural-language feature request and automatically
plans, generates code, tests, and (in later phases) commits/PRs/deploys it.
Full design: [docs/SDD.md](docs/SDD.md).

## Status: Phase 1 (MVP) + Docker sandbox + real Claude API agents

Orchestrator + state machine, Planning/CodeGen agents, and a Docker sandbox to run
generated code in. No web UI, no Git/GitHub integration yet — see the roadmap in
[docs/SDD.md](docs/SDD.md#10-l%E1%BB%99-tr%C3%ACnh-tri%E1%BB%83n-khai-roadmap-%C4%91%E1%BB%81-xu%E1%BA%A5t).

### Run the demo (mock — no dependencies, no network, no API key)

```bash
pip install -r requirements.txt
python -m backend.main "Thêm API đăng nhập bằng JWT"
```

Add `--fail-test` to see the failure path (state ends at `NEEDS_ATTENTION`
instead of `DONE`):

```bash
python -m backend.main "Thêm API đăng nhập bằng JWT" --fail-test
```

### Run for real (`--engine claude`)

Uses the real Claude API to plan and write actual files under `workspace/<task_id>/`,
then tests them inside the Docker sandbox
([backend/sandbox/docker_executor.py](backend/sandbox/docker_executor.py)) instead of
on the host (SDD §6) — no network access, read-only mount, resource-limited,
always removed after the run.

**Requires:** `ANTHROPIC_API_KEY` set (or `ant auth login`), and Docker installed with
the daemon running. The sandbox image (`docker/sandbox.Dockerfile`) is built
automatically on first use and cached.

```bash
python -m backend.main "Trang web học tiếng Việt cho bé gái 7 tuổi" --engine claude
```

No retry loop yet (SDD roadmap Phase 2) and no Git/GitHub integration yet (SDD §12
step 5) — a failed test run ends at `NEEDS_ATTENTION`, and a passing run stops at a
stub `PR_CREATED`/`CI_RUNNING` rather than actually pushing anywhere.

### Run the tests

```bash
pytest tests/ -q
```

