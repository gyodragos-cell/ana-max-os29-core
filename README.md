# OS29 Core

**Local evidence, memory and continuity for AI agents — not another AI model.**

OS29 is a Python library and MCP-compatible local service for storing evidence,
finding prior observations and handing work units between agent sessions. It
does not itself reason, host a language model or promise autonomous decisions.

OS28 is a **separate tool-infrastructure layer**. The public
integrations/os28 package is only a portable interface and a deterministic
offline mock. It does not contain the proprietary or private local OS28
implementation. Connecting an actual tool provider is optional.

## The problem

AI clients routinely lose context, repeat diagnostics and confuse observations
with verified results. OS29 supplies a local record of what was done, where the
evidence lives, what is still uncertain and the next safe action. The actual
agent decides what to do with it.

## What is included

- SQLite-backed traces, mission capsules, work units and evidence receipts.
- Checkpoints, handoff and resume by Work Unit ID using the same local store.
- SQLite FTS5/BM25 **lexical** search, not vector or semantic AI reasoning.
- Optional MCP STDIO provider, CLI and separately started HTTP gateway.
- Portable OS28 provider contract, offline mock, tests and privacy checks.
- No preloaded model, memory, database, real credentials or private logs.

## Architecture

    Operator-selected AI client / local model
                    |
             MCP STDIO / Python
                    |
             OS29 Core library
          evidence | Work Units | search
                    |
              local SQLite
                    |
       Optional OS28 provider interface
            (user-configured, mock by default)

## Quick start

Requires Python 3.11 or newer. The examples below call the virtual-environment
interpreter directly, so no PowerShell execution-policy or shell activation is needed.

Clone the published v0.1.0 tag:

    git clone --branch v0.1.0 https://github.com/gyodragos-cell/ana-max-os29-core.git
    cd ana-max-os29-core
    python -m venv .venv

Windows PowerShell:

    .\.venv\Scripts\python.exe -m pip install -e ".[test]"
    .\.venv\Scripts\python.exe -m compileall -q os29 integrations examples scripts tests
    .\.venv\Scripts\python.exe -m pytest -q
    .\.venv\Scripts\python.exe scripts/privacy_gate.py
    .\.venv\Scripts\python.exe scripts/offline_smoke.py

Linux / macOS:

    .venv/bin/python -m pip install -e ".[test]"
    .venv/bin/python -m compileall -q os29 integrations examples scripts tests
    .venv/bin/python -m pytest -q
    .venv/bin/python scripts/privacy_gate.py
    .venv/bin/python scripts/offline_smoke.py

For ongoing development, clone without --branch to use main. The v0.1.0 release
is immutable; newer demonstrations on main are intentionally not part of that tag.

These tests create isolated **temporary** SQLite databases and remove them.
The package needs no existing private memory store, laboratory computer,
gateway service or network connection for basic tests. Initial dependency
installation may require the package index.

## Conceptual workflow

1. Agent A creates a Work Unit with a project, objective and next action.
2. Agent A records evidence and a checkpoint in a user-selected local database.
3. Agent B opens that same database and resumes with only the Work Unit ID.
4. Agent B independently verifies evidence before marking a task completed.

The offline smoke proves persistence and resume across separate Store objects.
It does **not** imply that two actual AI models executed the workflow.

## Reproduce process handoff and crash recovery (current main)

The main development branch has an additional, public integration demonstration,
not part of the immutable v0.1.0 tag:

    git clone https://github.com/gyodragos-cell/ana-max-os29-core.git
    cd ana-max-os29-core
    python scripts/two_process_handoff_demo.py

This runs **three separate Python processes** over one disposable SQLite store:
Agent A hands off, Agent B persists a checkpoint before an intentional abrupt exit,
and restarted Agent B restores context, runs a real smoke command and completes.
Expected child exits are 0 / 23 / 0; the parent exits 0 on success. It is **not**
a simulation of two language-model reasoning systems or a test of private OS28.

The current main branch also tests the actual MCP STDIO JSON-RPC interface
from independent server subprocesses. See [reproducible handoff demo](docs/PROCESS_HANDOFF_DEMO.md).
The unit and integration test suite measures statement/branch coverage in CI
with an initial 60% minimum; this does not certify production readiness.

## Known limitations

- Work units are persisted context, not proof that a task is correct.
- FTS5 search is lexical and depends on the local SQLite build.
- Multi-machine replication and enterprise multi-user access are not shipped.
- Optional network tools require operator-provided configuration and review.
- No local AI inference engine, semantic embeddings, Frida or live OS28 gateway
  are included.
- This repository has a clean Git history, separate from the legacy portfolio repository.
- Documentation describes a developer preview, not a certified institution
  deployment or a measured performance advantage.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Independent process and MCP handoff demo](docs/PROCESS_HANDOFF_DEMO.md)
- [Offline quick start](docs/QUICK_START.md)
- [Security boundary](docs/SECURITY_BOUNDARY.md)
- [Roadmap](docs/ROADMAP.md)
- [Public release boundary](PUBLIC_RELEASE_BOUNDARY.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

MIT license: [LICENSE](LICENSE).
