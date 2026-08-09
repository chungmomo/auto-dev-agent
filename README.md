# auto-dev-agent

Auto Coding Bot — takes a natural-language feature request and automatically
plans, generates code, tests, and (in later phases) commits/PRs/deploys it.
Full design: [docs/SDD.md](docs/SDD.md).

## Status: Phase 1 (MVP)

Orchestrator + state machine only, using mock Planning/CodeGen agents and a
local (non-Docker) test runner, driven from a CLI. No web UI, no real
Claude API calls, no Git/GitHub integration yet — see the roadmap in
[docs/SDD.md](docs/SDD.md#10-l%E1%BB%99-tr%C3%ACnh-tri%E1%BB%83n-khai-roadmap-%C4%91%E1%BB%81-xu%E1%BA%A5t).

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

